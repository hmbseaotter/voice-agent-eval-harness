"""The CLI, and the transport spy that proves the tier issues no model call.

A spy needs something to spy on. There is no model transport at this phase, so
asserting "the transport was not called" would be asserting about an object
that does not exist -- which is why the spy here is at the **socket** layer: a
model call of any kind, through any client, has to open one. The whole run
executes with `socket.socket`, `socket.create_connection` and
`ssl.SSLContext.wrap_socket` replaced by functions that raise, and it completes.

That is a stronger assertion than a mock on a seam, and it keeps working at P3
when the seam exists: a live call under this spy raises rather than passing
because somebody remembered to patch the right module.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import socket
import ssl
import subprocess
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final

import pytest
import yaml

from harness import cli
from harness.agreement import RUBRIC_FROZEN_V1
from harness.checks import build_registry
from harness.cli import main
from harness.core.artifact import build_payload, content_hash
from harness.core.context import build_context
from harness.core.findings import dump_findings, load_findings
from harness.core.result import Provenance
from harness.core.rubric import CheckTier, load_rubric, rubric_hash
from harness.core.severity import BAND_ORDER
from harness.core.transport import (
    _DOTENV_CACHE,
    CREDENTIAL_VARIABLES,
    DEFAULT_CALL_CEILING,
    JudgeRequest,
    JudgeResponse,
    RecordingTransport,
    RunLogHeader,
    RunLogWriter,
    estimate_cost_usd,
    read_run_log,
)
from harness.corpus.policies import load_policies
from harness.corpus.text_adapter import parse_call
from harness.judge.engine import INFORMED_RETRY_BUDGET, run_judged
from harness.judge.prompt import absent_categories, load_template

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]

#: Modules that would be imported by any HTTP client the judged tier could use.
#: Asserted absent after a deterministic run, so an accidental import at module
#: scope is caught even though nothing calls it.
_TRANSPORT_MODULES: Final[tuple[str, ...]] = (
    "anthropic",
    "httpx",
    "requests",
    "urllib3",
    "http.client",
)


@pytest.fixture
def no_credential_in_reach(monkeypatch: pytest.MonkeyPatch) -> None:
    """Both credential routes closed, on a machine that may have a key.

    The environment half is `delenv`. The file half cannot be: the CLI resolves
    `.env` from the repository root, and the machine a live run is issued from
    has one there. The parse cache is seeded with an empty result for that path
    instead -- which is the shipped reader returning nothing, rather than a
    patched function pretending to. A test whose verdict depends on whether the
    operator has a key is not a test.
    """
    for name in CREDENTIAL_VARIABLES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setitem(_DOTENV_CACHE, (REPO_ROOT / ".env").resolve(), MappingProxyType({}))


class TransportOpened(AssertionError):
    """Raised by the spy when anything tries to open a connection."""


@pytest.fixture
def transport_spy(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Every route to a network connection, replaced by a refusal."""
    opened: list[str] = []

    def refuse(name: str) -> Any:
        def _refuse(*args: object, **kwargs: object) -> Any:
            del args, kwargs
            opened.append(name)
            raise TransportOpened(f"the deterministic tier opened {name}")

        return _refuse

    monkeypatch.setattr(socket, "socket", refuse("socket.socket"))
    monkeypatch.setattr(socket, "create_connection", refuse("socket.create_connection"))
    monkeypatch.setattr(ssl.SSLContext, "wrap_socket", refuse("ssl wrap_socket"))
    return opened


def test_the_assert_tier_completes_with_every_route_to_a_socket_refused(
    transport_spy: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    """The criterion, asserted by a spy rather than by inspection."""
    exit_code = main(["run", "--tier", "assert"])
    assert transport_spy == [], f"the run opened {transport_spy}"
    assert exit_code == 1, "the design set is seeded with defects, so a gate must fail (D105)"

    output = capsys.readouterr().out
    assert "tier: assert" in output
    assert "GATES FAILED" in output


def test_the_spy_would_notice_a_connection(transport_spy: list[str]) -> None:
    """The control. The assertion above is that a list stayed empty, and a spy
    that patched nothing would also leave it empty."""
    with pytest.raises(TransportOpened):
        socket.create_connection(("example.invalid", 443))
    assert transport_spy == ["socket.create_connection"]


def test_no_transport_module_is_imported_by_a_deterministic_run() -> None:
    """A client imported at module scope makes no call and is still a seam the
    tier is not supposed to have yet."""
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; from harness.cli import main; "
            "code = main(['run','--tier','assert']); "
            "print('IMPORTED:' + ','.join(m for m in "
            f"{_TRANSPORT_MODULES!r} if m in sys.modules)); "
            "sys.exit(code)",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 1, completed.stderr[-800:]
    assert "IMPORTED:" in completed.stdout
    imported = completed.stdout.rsplit("IMPORTED:", 1)[1].strip()
    assert imported == "", f"a deterministic run imported {imported}"


# --------------------------------------------------------------------------
# The per-check breakdown, and what the exit code means
# --------------------------------------------------------------------------


def test_the_run_prints_a_line_for_every_entry_of_the_tier(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """ "prints a per-check breakdown" is a criterion, so the breakdown is
    checked against the rubric rather than eyeballed."""
    from harness.checks import build_registry
    from harness.core.rubric import CheckTier, load_rubric

    main(["run", "--tier", "assert"])
    output = capsys.readouterr().out
    rubric = load_rubric(REPO_ROOT / "rubric.yaml", build_registry().keys())
    for entry in rubric.for_tier(CheckTier.ASSERT):
        assert entry.id in output, f"{entry.id} is missing from the breakdown"
    for column in ("app", "n/a", "unev", "err", "ref"):
        assert column in output, f"the breakdown omits the {column} count"


def test_every_status_is_printed_beside_the_rate_and_not_folded_into_it(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """W21 is a tier where `threshold` was consumed by no logic and no rate was
    computed anywhere; printing the counts is what lets a reader tell a
    dimension that failed from one that never applied."""
    from harness.core.result import Status

    main(["run", "--tier", "assert"])
    output = capsys.readouterr().out
    for status in Status:
        assert f"{status.value}:" in output, f"{status.value} is not reported"


def test_no_result_is_missing_a_provenance_value(capsys: pytest.CaptureFixture[str]) -> None:
    """The criterion's own wording: the count of results missing any of the
    three is zero, and the run prints that count."""
    main(["run", "--tier", "assert"])
    output = capsys.readouterr().out
    assert "missing a provenance value: 0" in output


def test_an_absolute_gate_negative_fails_the_run_on_the_process_exit_code() -> None:
    """Asserted on a real process, because the criterion says so.

    Calling `main` in-process reads a return value; the criterion is about the
    exit code a shell sees, and those are different things until something
    checks.
    """
    completed = subprocess.run(
        [sys.executable, "-m", "harness.cli", "run", "--tier", "assert"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 1, completed.stderr[-500:]
    assert "absolute" in completed.stdout
    assert "GATES FAILED" in completed.stdout


def test_a_run_whose_gates_all_hold_exits_zero(tmp_path: Path) -> None:
    """The control for the exit code, which is otherwise only ever seen as 1.

    Something has to exit zero, or the non-zero above proves nothing about
    gates and only that this command always fails.

    **What makes it zero is the threshold, not silence.** This docstring said
    "one entry whose check is silent on every design call", and the check is
    not silent: `lifecycle_event_missing` finds F-47 on CALL-12, so the rate is
    0.94 rather than 1.00. A `threshold: 0.0` rate gate holds anyway, which
    makes this the better control of the two -- it shows a gate reading a rate
    rather than a run finding nothing to read. The assertion on the rate keeps
    the two apart: were the check to go genuinely silent the rate would read
    1.00, and this test would then fail rather than pass for a reason nobody
    had stated.
    """
    rubric = tmp_path / "quiet.yaml"
    rubric.write_text(
        "version: '1'\n"
        "entries:\n"
        "  - id: A-quiet\n"
        "    tier: assert\n"
        "    check: lifecycle_event_missing\n"
        "    gate: rate\n"
        "    threshold: 0.0\n"
        "    scale: [emitted, missing]\n"
        "    negative: missing\n"
        "    traces_to: [F-47]\n"
        "    negative_instance: CALL-01\n"
        "    params:\n"
        "      required_system_events: [call.ended]\n",
        encoding="utf-8",
    )
    completed = subprocess.run(
        [sys.executable, "-m", "harness.cli", "run", "--tier", "assert", "--rubric", str(rubric)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout[-800:] + completed.stderr[-400:]
    assert "every gate held" in completed.stdout
    rate = next(
        line.split()[2] for line in completed.stdout.splitlines() if line.startswith("A-quiet")
    )
    assert rate == "0.94", (
        f"the entry's pass rate is {rate}, not the 0.94 that makes this a gate holding over a "
        "check that fired. At 1.00 the check found nothing, and this then asserts only that a "
        "run with no violations exits zero -- a weaker claim than the name makes"
    )


# --------------------------------------------------------------------------
# Refusals
# --------------------------------------------------------------------------


def test_the_judged_tier_in_replay_mode_needs_a_log_to_replay(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Through P2 this asserted `--tier judge` was refused by name, because the
    seam did not exist and running zero entries would have printed a clean
    table that looked like success.

    From P3 the tier runs, and the refusal that remains is a different one:
    replay has to be told which log to replay. There is no default, because a
    default would make the run depend on which file happened to be newest in
    the log directory.
    """
    assert main(["run", "--tier", "judge"]) == 2
    assert "needs a run log" in capsys.readouterr().err


def test_a_judged_replay_run_completes_over_a_log_it_recorded(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The end-to-end replay path, over the shipped rubric and corpus.

    The log is produced by a first pass through a scripted transport and then
    replayed by the CLI, so this asserts the two halves agree about what a
    request hash is -- which no unit test of either half can.
    """
    log = _record_reference_log(tmp_path)
    code = main(
        [
            "run",
            "--tier",
            "judge",
            "--mode",
            "replay",
            "--run-log",
            str(log),
            "--run-log-dir",
            str(tmp_path / "out"),
        ]
    )
    out = capsys.readouterr().out
    assert code == 0, out
    assert "tier: judge   mode: replay" in out
    assert "J-policy-alignment" in out
    # The gate the judged tier did not have at P3 and does now (OB-8). Its
    # absence used to be printed in the output, deliberately, so a reader could
    # not mistake exit 0 for a claim about the agent -- and that sentence is
    # what this asserted. The claim it makes now is the opposite one.
    assert "every gate held" in out
    # The distribution, not a modal verdict: the requirement's words are
    # "report the verdict distribution across those repetitions rather than a
    # single verdict", and a per-call line carrying one verdict would read as a
    # report and satisfy nothing.
    assert " x10" in out, "the per-call rows do not carry a distribution across repetitions"


def test_a_judged_replay_run_records_its_own_log(tmp_path: Path) -> None:
    """Recording is unconditional and applies to replay too. "Every run-log
    entry carries a stop_reason; the count missing one is zero" has to be
    asserted over a log this run produced."""
    log = _record_reference_log(tmp_path)
    out_dir = tmp_path / "out"
    main(
        [
            "run",
            "--tier",
            "judge",
            "--mode",
            "replay",
            "--run-log",
            str(log),
            "--run-log-dir",
            str(out_dir),
        ]
    )
    written = sorted(out_dir.glob("*.jsonl"))
    assert len(written) == 1
    _, entries = read_run_log(written[0])
    assert entries
    assert all(entry.response.stop_reason for entry in entries)


def test_a_stale_log_is_refused_and_the_flag_lets_it_through(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Both halves of the criterion. A refusal with no override is a wall; the
    flag is the deliberate decision that the difference does not matter."""
    log = _record_reference_log(tmp_path, template_hash="c" * 64)
    args = [
        "run",
        "--tier",
        "judge",
        "--mode",
        "replay",
        "--run-log",
        str(log),
        "--run-log-dir",
        str(tmp_path / "out"),
    ]
    assert main(args) == 2
    assert "prompt-template hash" in capsys.readouterr().err

    # And succeeds with the flag, which is the criterion's second half. The log
    # here was recorded through the real template and stamped with a header
    # claiming otherwise, so every request still hash-matches: the flag lifts
    # the staleness REFUSAL and changes nothing about the lookup. A log whose
    # prompts genuinely differed would still miss, entry by entry, which is the
    # refusal arriving one layer down rather than being waived.
    assert main([*args, "--allow-stale-replay"]) == 0


def test_live_mode_prints_an_estimate_and_issues_nothing_without_confirmation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The requirement's second and third parts: a live run prints an estimated
    call count and cost, and issues no call until confirmed. The first part --
    that it requires a credential -- is
    `test_live_mode_requires_a_credential_before_it_prints_an_estimate`.

    Confirmation is declined here, so no transport is ever constructed -- which
    is the strongest available form of "issued no call": there is nothing for a
    fallback to reach.

    **The fake credential is what makes this a test rather than a machine
    property.** The credential check runs before the estimate now, which is the
    order the requirement states, so a run with no key reachable is refused
    before it prints anything. This test passed on the machine that wrote it,
    where `.env` holds a real key, and would have gone red on CI and on every
    clone -- found by running the suite in a worktree rather than in the
    checkout. Setting the variable makes the precondition the test's own.
    """
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake-0123456789")
    monkeypatch.setattr(cli, "confirm_spend", lambda _prompt: False)
    code = main(
        [
            "run",
            "--tier",
            "judge",
            "--mode",
            "live",
            "--run-log-dir",
            str(tmp_path / "out"),
        ]
    )
    captured = capsys.readouterr()
    assert code == 2
    assert "estimated $" in captured.out
    assert "judged call(s)" in captured.out
    assert "call ceiling:" in captured.out
    assert "expected: about $" in captured.out, (
        "the pre-flight prints only the ceiling, a figure far above what a run spends (OB-17)"
    )
    assert "the retries recorded there:" in captured.out, (
        "the expected figure does not say how it counted informed retries (OB-33)"
    )
    assert "was recorded under another rubric or template" not in captured.out, (
        "the committed log, recorded under the shipped rubric and template, was flagged stale"
    )
    assert "no confirmation given" in captured.err
    assert not list((tmp_path / "out").glob("*.jsonl")), (
        "a log was written for a run that never ran"
    )


@pytest.mark.usefixtures("no_credential_in_reach")
def test_live_mode_requires_a_credential_before_it_prints_an_estimate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    transport_spy: list[str],
) -> None:
    """The requirement's first clause, in the requirement's own order.

    "SHALL require a credential, SHALL print an estimated call count and cost,
    and SHALL require confirmation." The credential was checked last, inside the
    transport constructor, which the CLI reaches only after confirmation -- so
    an operator with no key approved spend they could not make and was then
    refused. Nothing in the suite drove that refusal at all: removing it left
    159 judged-tier tests green.

    Confirmation is answered YES here, which is what makes this a test of the
    order rather than of the confirmation. The socket spy is the guard on that
    choice: with the refusal removed, the run reaches a transport, and the spy
    turns a network call into a failure instead of a charge.
    """
    monkeypatch.setattr(cli, "confirm_spend", lambda _prompt: True)
    code = main(
        ["run", "--tier", "judge", "--mode", "live", "--run-log-dir", str(tmp_path / "out")]
    )
    captured = capsys.readouterr()
    assert code == 2, captured.out[-500:]
    assert "credential" in captured.err
    assert "estimated $" not in captured.out, (
        "the estimate was printed before the credential was checked, so an operator with no "
        "key is asked to approve spend they cannot make"
    )
    assert transport_spy == [], f"the run opened {transport_spy}"
    assert not list((tmp_path / "out").glob("*.jsonl")), (
        "a run log was written for a run that was refused"
    )


def test_a_judged_run_whose_results_errored_reports_the_tier_incomplete(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """D114's exit 3, for the judged tier.

    A log recorded from a judge that cites an identifier nobody offered replays
    to `errored` on every repetition: the informed retry fires, the retry cites
    the same fabrication, and the budget is spent. That is the tier failing to
    produce results rather than the agent failing a gate, so it is 3 and not 1.

    Nothing asserted this. `if broken or unevaluable:` replaced with
    `if False:` left the judged-tier suite green, so a run that errored on
    every call and exited 0 would have been noticed by nothing.
    """
    expected = _judged_results_over_the_design_set()
    log = _record_reference_log(tmp_path, citations=("T999",))
    code = main(
        [
            "run",
            "--tier",
            "judge",
            "--mode",
            "replay",
            "--run-log",
            str(log),
            "--run-log-dir",
            str(tmp_path / "out"),
            # Every repetition spends two calls here, not one: the fabricated
            # citation buys the informed retry. A ceiling below that halts the
            # run -- correctly, and it would make this test assert exit 3 for
            # the wrong reason, which is what it did when the tier grew from
            # one entry to seven against a literal `400`. Derived now, with a
            # margin, so it moves with the rubric.
            "--max-calls",
            str(expected * (1 + INFORMED_RETRY_BUDGET) + 10),
        ]
    )
    out = capsys.readouterr().out
    assert code == 3, out[-800:]
    assert "TIER INCOMPLETE" in out
    assert f"errored: {expected}" in out, (
        "the count of errored results is not reported beside the verdict"
    )


def test_a_judged_run_the_transport_aborts_exits_three_and_says_what_it_obtained(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The other route to 3, and the one that carries partial results.

    A log one repetition short replays until the missing hash, which aborts the
    run. The requirement is that results already obtained are persisted before
    any subsequent abort, so the count reported and the count in the log this
    run wrote have to agree -- a run reporting fewer results than its own log
    would be disagreeing with the artifact the requirement is written about.
    """
    log = _record_reference_log(tmp_path)
    lines = log.read_text(encoding="utf-8").splitlines()
    log.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")

    out_dir = tmp_path / "out"
    code = main(
        [
            "run",
            "--tier",
            "judge",
            "--mode",
            "replay",
            "--run-log",
            str(log),
            "--run-log-dir",
            str(out_dir),
        ]
    )
    captured = capsys.readouterr()
    assert code == 3, captured.out[-800:]
    assert "RUN ABORTED" in captured.err
    assert "result(s) were obtained before it stopped" in captured.err

    written = sorted(out_dir.glob("*.jsonl"))
    assert len(written) == 1
    _, entries = read_run_log(written[0])
    assert entries, "the run aborted without persisting anything it had already obtained"
    # **The comparison is against the results that cost a call**, which is what
    # the log is a record of. It was `results:` against `len(entries)` until
    # D125's precondition, when a dimension that does not apply to a call
    # started producing a result and no run-log entry -- so the totals stopped
    # being the same number for a reason that is not a defect. Comparing them
    # anyway would have made the fix look like one.
    assert f"of which issued a call: {len(entries)}" in captured.out, (
        "the run reports a count of issued calls its own log does not carry"
    )


def test_the_estimate_is_the_product_of_calls_dimensions_and_n() -> None:
    """The number nobody holds in their head, and the reason the requirement
    asks for it to be printed."""
    rubric = load_rubric(REPO_ROOT / "rubric.yaml", build_registry().keys())
    template = load_template(REPO_ROOT / "prompts" / "judge-dimension.v1.md")
    policies = load_policies(REPO_ROOT / "corpus" / "policies")
    contexts = [
        build_context(parse_call(path), policies, policy_tool="fetch_policy")
        for path in sorted((REPO_ROOT / "corpus" / "transcripts").glob("*.txt"))
    ]
    calls, cost = cli.judged_call_estimate(rubric, contexts, template)
    expected = 0
    for entry in rubric.for_tier(CheckTier.JUDGE):
        assert entry.judge is not None
        applicable = sum(
            1
            for context in contexts
            if not absent_categories(
                context, entry.judge.applies_when_facts_present, entry_id=entry.id
            )
        )
        expected += applicable * entry.judge.repetitions
    assert calls == expected
    assert cost > 0

    # The precondition has to be visible in the figure, not merely applied. A
    # count of calls-times-entries-times-N is what the estimate printed before
    # D132, and it names a spend on requests the run will never issue.
    assert calls < len(contexts) * len(rubric.for_tier(CheckTier.JUDGE)) * 10, (
        "the estimate counts every call for every entry, so an entry whose precondition "
        "excludes half the corpus is quoted at twice what it will cost"
    )


def test_the_estimate_is_measured_from_the_prompts_rather_than_a_constant() -> None:
    """A number a human is asked to agree to should not be a guess when the
    thing it describes is sitting in memory.

    The first draft used constants -- 6,000 input tokens and 500 output per
    call -- and they were wrong by about three and a half times against the
    shipped corpus, in the direction that makes a reader approve more spending
    than they were told. This drives the estimate over two different corpora
    and requires the figure to move with them.
    """
    rubric = load_rubric(REPO_ROOT / "rubric.yaml", build_registry().keys())
    template = load_template(REPO_ROOT / "prompts" / "judge-dimension.v1.md")
    policies = load_policies(REPO_ROOT / "corpus" / "policies")
    paths = sorted((REPO_ROOT / "corpus" / "transcripts").glob("*.txt"))
    contexts = [
        build_context(parse_call(path), policies, policy_tool="fetch_policy") for path in paths
    ]

    # CALL-04 renders the largest prompt in the design set and CALL-07 the
    # smallest, so a per-call estimate that read a constant would report the
    # same input size for both.
    big = [c for c in contexts if c.call_id == "CALL-04"]
    small = [c for c in contexts if c.call_id == "CALL-07"]
    assert big and small
    _, big_cost = cli.judged_call_estimate(rubric, big, template)
    _, small_cost = cli.judged_call_estimate(rubric, small, template)
    assert big_cost > small_cost, (
        "the estimate does not move with the prompt it describes, so it is a constant "
        "wearing a function's name"
    )


def test_an_entry_nothing_recorded_is_priced_at_its_ceiling_and_named() -> None:
    """The expected figure's one fallback, stated rather than absorbed (D152).

    An entry the recorded run never exercised has no answer length to price, and
    guessing one would be the constant the estimate's first draft was. It is
    priced at its ceiling, so the figure stays safe, and returned by name, so the
    printed line can say which part of the figure is a bound.
    """
    recorded = cli.JudgedEntryEstimate("J-recorded", "claude-sonnet-5", 10, 2000, 8192)
    unrecorded = cli.JudgedEntryEstimate("J-new", "claude-sonnet-5", 10, 2000, 8192)
    cost, missing = cli.expected_cost_usd([recorded, unrecorded], {"J-recorded": 500})
    assert missing == ("J-new",)
    assert cost == pytest.approx(
        estimate_cost_usd(
            model="claude-sonnet-5", calls=10, input_tokens_each=2000, output_tokens_each=500
        )
        + unrecorded.ceiling_usd()
    )


def test_the_expected_figure_would_notice_recorded_retries_left_out() -> None:
    """P4-16. Each entry's calls are priced at the retry share its log recorded (OB-33, D170).

    The synthesis spends informed retries in every recording, and a figure pricing
    first attempts alone left them to the input side's over-estimate. An entry the
    log shows retrying a quarter of its calls is priced at a quarter more calls, one
    it shows never retrying at none, and one with no share given at none.
    """
    retried = cli.JudgedEntryEstimate("J-retried", "claude-sonnet-5", 10, 2000, 8192)
    steady = cli.JudgedEntryEstimate("J-steady", "claude-sonnet-5", 10, 2000, 8192)
    unshared = cli.JudgedEntryEstimate("J-unshared", "claude-sonnet-5", 10, 2000, 8192)
    each = estimate_cost_usd(
        model="claude-sonnet-5", calls=10, input_tokens_each=2000, output_tokens_each=500
    )
    cost, missing = cli.expected_cost_usd(
        [retried, steady, unshared],
        {"J-retried": 500, "J-steady": 500, "J-unshared": 500},
        {"J-retried": 1.25, "J-steady": 1.0},
    )
    assert missing == ()
    assert cost == pytest.approx(each * 1.25 + each + each)


def test_the_expected_figure_says_why_it_is_absent_when_nothing_was_recorded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """With no recorded run to read, the second line says so rather than vanishing.

    A figure that silently disappears reads the same as one nobody built, and an
    operator approving the ceiling would not know which of the two they had.
    """
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake-0123456789")
    monkeypatch.setattr(cli, "confirm_spend", lambda _prompt: False)
    monkeypatch.setattr(cli, "_DEFAULT_REFERENCE_LOG", str(tmp_path / "never-recorded.jsonl"))
    code = main(
        ["run", "--tier", "judge", "--mode", "live", "--run-log-dir", str(tmp_path / "out")]
    )
    out = capsys.readouterr().out
    assert code == 2
    assert "estimated $" in out
    assert "expected: not computed" in out
    assert "expected: about $" not in out


def test_the_expected_figure_would_notice_a_stale_log_left_unflagged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """P4-16. A log recorded under another rubric version is named beside the figure.

    The figure still prints, since a stale log's lengths are the only ones there are,
    and the line names what differs the way replay names it, so an operator approving
    spend sees that the prediction rests on a rubric this run does not use (OB-33, D170).
    """
    stale = _record_reference_log(tmp_path, name="stale.jsonl", mode="live", rubric_version="0")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake-0123456789")
    monkeypatch.setattr(cli, "confirm_spend", lambda _prompt: False)
    monkeypatch.setattr(cli, "_DEFAULT_REFERENCE_LOG", str(stale))
    code = main(
        ["run", "--tier", "judge", "--mode", "live", "--run-log-dir", str(tmp_path / "out")]
    )
    out = capsys.readouterr().out
    assert code == 2
    assert "expected: about $" in out, out[-1200:]
    assert "stale.jsonl was recorded under another rubric or template" in out, out[-1200:]
    assert "rubric version: log '0', current '1'" in out, out[-1200:]


def test_a_declared_default_ceiling_applies_when_max_calls_is_absent() -> None:
    """ "WHERE `--max-calls N` is absent, the system SHALL apply a declared
    default ceiling rather than running uncapped." Asserted on the parsed
    arguments, because "uncapped" is what an absent default looks like."""
    parser_args = _parse(["run", "--tier", "judge"])
    assert parser_args.max_calls == DEFAULT_CALL_CEILING
    assert _parse(["run", "--tier", "judge", "--max-calls", "7"]).max_calls == 7


def test_replay_is_the_default_mode() -> None:
    """So behavior never depends on whether a credential happens to be present
    in the environment, and money is never spent by accident (D8)."""
    assert _parse(["run", "--tier", "judge"]).mode == "replay"


def test_confirmation_reads_a_non_interactive_stdin_as_no(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A live run started by a script that cannot answer should not spend
    money."""

    def _raises(_prompt: str) -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", _raises)
    assert cli.confirm_spend("Issue these calls? [y/N] ") is False


@pytest.mark.parametrize(
    ("answer", "expected"), [("y", True), ("yes", True), ("Y", True), ("n", False), ("", False)]
)
def test_confirmation_accepts_only_an_affirmative(
    answer: str, expected: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt: answer)
    assert cli.confirm_spend("prompt") is expected


def test_an_unknown_tier_is_refused_naming_the_declared_ones(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["run", "--tier", "human"]) == 2
    error = capsys.readouterr().err
    assert "human" in error and "assert" in error and "judge" in error


def test_a_rubric_that_does_not_load_aborts_with_its_reason(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    broken = tmp_path / "broken.yaml"
    broken.write_text("version: '1'\nentries: []\n", encoding="utf-8")
    assert main(["run", "--tier", "assert", "--rubric", str(broken)]) == 2
    assert "rubric refused" in capsys.readouterr().err


def test_a_missing_corpus_aborts_rather_than_reporting_an_empty_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    empty = tmp_path / "no-transcripts"
    empty.mkdir()
    assert main(["run", "--tier", "assert", "--transcripts", str(empty)]) == 2
    assert "corpus refused" in capsys.readouterr().err


def test_the_policy_tool_name_is_a_flag_and_not_a_constant(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A corpus entity name, so it is configurable at the boundary too.

    Under a different name no document is retrieved, so the policy entries stop
    finding anything to check and their counts move.
    """
    main(["run", "--tier", "assert"])
    with_default = capsys.readouterr().out
    main(["run", "--tier", "assert", "--policy-tool", "get_policy"])
    with_other = capsys.readouterr().out
    assert with_default != with_other, (
        "changing the retrieval tool name changed nothing, so the name is not reaching "
        "the seam from the command line"
    )


def test_a_run_whose_checks_all_error_does_not_report_that_every_gate_held(
    tmp_path: Path,
) -> None:
    """P2-1. A check that threw on every call produced fifteen `errored` rows,
    no failed gate, "every gate held", and **exit 0**.

    The status channel separates the five states and the exit code collapsed
    four of them into "held" -- W11's shape one level up, in the line a CI job
    reads. A rubric that breaks every check reported success.
    """
    rubric_path = REPO_ROOT / "rubric.yaml"
    document = yaml.safe_load(rubric_path.read_text(encoding="utf-8"))
    entry = next(e for e in document["entries"] if e["id"] == "A-completion-claim-unsupported")
    entry["params"]["topics"] = "oops"
    document["entries"] = [entry]
    broken = tmp_path / "rubric.yaml"
    broken.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")

    exit_code = main(["run", "--tier", "assert", "--rubric", str(broken)])
    assert exit_code == 3, "a tier that errored on every call did not report itself incomplete"


def test_a_run_with_no_verdict_to_compare_also_reports_the_tier_incomplete(
    tmp_path: Path,
) -> None:
    """D114's second half, which shared a branch with the first and no test.

    `errored` is a broken check and `unevaluable` is a check that could not
    reach a verdict; both exit 3 from one condition, and only the errored half
    was asserted. A guard proven on one of the two states it covers is a guard
    proven on half of itself.

    Forced through the rubric rather than through a fixture check, because that
    is how it would actually arrive: `governing_clause_not_applied` returns
    `unevaluable` when the entry names a clause the retrieved document does not
    contain, which is a finding against the rubric rather than against the
    call. The gate is a rate gate at 0.0 so nothing fails on the gates, which
    is what makes the exit code the only thing distinguishing this run from a
    clean one.
    """
    document = yaml.safe_load((REPO_ROOT / "rubric.yaml").read_text(encoding="utf-8"))
    entry = next(e for e in document["entries"] if e["check"] == "governing_clause_not_applied")
    for topic in entry["params"]["topics"].values():
        topic["governing_clauses"] = ["99.9"]
    entry["gate"] = "rate"
    entry["threshold"] = 0.0
    document["entries"] = [entry]
    rubric = tmp_path / "rubric.yaml"
    rubric.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")

    exit_code = main(["run", "--tier", "assert", "--rubric", str(rubric)])
    assert exit_code == 3, (
        "a tier whose only results carried no verdict reported itself complete. No gate "
        "failed, which is not the same as every gate holding"
    )


def test_a_failed_gate_outranks_an_incomplete_tier(tmp_path: Path) -> None:
    """The precedence, which D114 records as a choice rather than an accident.

    A run with both a failed gate and an errored result exits **1**, not 3: the
    gate branch is tested first. A failed gate is evidence that was actually
    computed and is actionable now, and that branch prints the errored count
    beside it, so the reader is told about both and gets the code for the one
    carrying findings.

    Untested, this reads as an ordering nobody chose. The shipped rubric over
    the design set is exactly this case -- gates fail and nothing errors -- so
    the mixed case needs building.
    """
    document = yaml.safe_load((REPO_ROOT / "rubric.yaml").read_text(encoding="utf-8"))
    broken = next(e for e in document["entries"] if e["id"] == "A-completion-claim-unsupported")
    broken["params"]["topics"] = "oops"
    failing = next(e for e in document["entries"] if e["id"] == "A-lifecycle-event-missing")
    document["entries"] = [broken, failing]
    rubric = tmp_path / "rubric.yaml"
    rubric.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")

    exit_code = main(["run", "--tier", "assert", "--rubric", str(rubric)])
    assert exit_code == 1, (
        "a run with a failed gate and an errored check did not exit 1, so the precedence "
        "D114 records is not the precedence the code applies"
    )


def test_an_empty_corpus_version_is_refused_by_name(tmp_path: Path) -> None:
    """P2-8. `Provenance("", "", "")` constructed, so a `CORPUS_VERSION` holding
    only a newline stamped every result blank, printed
    `missing a provenance value: 555`, and continued.

    The exit 1 that followed came from a gate; a quieter rubric would have
    exited 0 with a report nothing could be recomputed from.
    """
    blank = tmp_path / "CORPUS_VERSION"
    blank.write_text("\n", encoding="utf-8")

    exit_code = main(["run", "--tier", "assert", "--corpus-version-file", str(blank)])
    assert exit_code == 2, "an empty corpus version did not refuse the run"


def test_provenance_refuses_each_blank_field_by_name() -> None:
    """The type-level half, so the CLI test above is not the only thing holding
    it. `test_every_result_carries_all_three_provenance_values` asserts the
    fields have no defaults, which is the neighbor of this: a dataclass with no
    default still constructs from three empty strings."""
    for blank in ("rubric_version", "corpus_version", "artifact_hash"):
        values = {"rubric_version": "r", "corpus_version": "c", "artifact_hash": "h"}
        values[blank] = "   "
        with pytest.raises(ValueError) as caught:
            Provenance(**values)
        assert blank in str(caught.value)

    assert Provenance("r", "c", "h").corpus_version == "c"


def test_the_parser_refuses_a_command_that_is_not_run() -> None:
    """The behavior that replaced an unreachable guard.

    `main` carried `if args.command != "run": parser.error(...)`, and
    `add_subparsers(required=True)` refuses an unknown command and a missing
    one before `parse_args` returns -- so the guard could not execute and read,
    to anyone scanning the file, as a tested path. Deleting dead code is only
    half of it: the behavior it appeared to provide has to be asserted
    somewhere, and it now is, in the place that keeps working when a second
    subcommand arrives.
    """
    for argv in (["bogus"], [], ["--tier", "assert"]):
        with pytest.raises(SystemExit) as exited:
            main(argv)
        assert exited.value.code == 2, f"argparse did not refuse {argv!r}"


def test_the_default_paths_come_from_the_working_directory_when_not_in_a_checkout() -> None:
    """`parents[2]` is the repository root only for an editable install.

    `src/harness/cli.py` walks up through `src/harness` and `src` to the root,
    which is right here and wrong in a wheel: `site-packages/harness/cli.py`
    gives the directory *above* `site-packages`, so every default path points
    outside any checkout and the run fails naming a path the reader has never
    seen. An adopter installing `harness` and running it against their own
    corpus is the case that reaches this, and it is the case nothing here could
    reproduce -- so `_repo_root` takes the file, and this drives it.
    """
    from harness.cli import _repo_root

    assert _repo_root() == REPO_ROOT, "the editable-install answer moved"

    installed = Path("C:/nowhere/lib/site-packages/harness/cli.py")
    assert _repo_root(installed) == Path.cwd(), (
        "an installed package still resolves its defaults against a directory two levels "
        "above itself, which is not a corpus and not a checkout"
    )

    shallow = Path("/cli.py")
    assert _repo_root(shallow) == Path.cwd(), (
        "a path with no grandparent raised instead of falling back"
    )


def _parse(argv: list[str]) -> argparse.Namespace:
    """The parsed arguments `main` would act on, without acting on them.

    Uses the shipped `build_parser` rather than rebuilding one. A test that
    declared its own flags would be asserting its own defaults, which is the
    shape D121 found in six controls.
    """
    return cli.build_parser().parse_args(argv)


def _judged_results_over_the_design_set() -> int:
    """How many judged results the shipped rubric produces over the design set.

    Computed rather than written down. It was `160` -- sixteen calls times ten
    repetitions -- while the rubric held one judged entry, and became wrong
    twice in one phase: D125's precondition stopped one dimension applying to
    the calls that retrieved no policy, and P4 took the tier from one entry to
    seven. A count derived from the corpus and the rubric moves when either
    does, which is the difference between a number that is checked and one that
    is remembered.
    """
    rubric = load_rubric(REPO_ROOT / "rubric.yaml", build_registry().keys())
    policies = load_policies(REPO_ROOT / "corpus" / "policies")
    contexts = [
        build_context(parse_call(path), policies, policy_tool="fetch_policy")
        for path in sorted((REPO_ROOT / "corpus" / "transcripts").glob("*.txt"))
    ]
    total = 0
    for entry in rubric.for_tier(CheckTier.JUDGE):
        assert entry.judge is not None
        applies = sum(
            1
            for context in contexts
            if not absent_categories(
                context, entry.judge.applies_when_facts_present, entry_id=entry.id
            )
        )
        total += applies * entry.judge.repetitions
    return total


def test_a_judged_run_with_only_some_results_errored_still_reports_the_tier_incomplete(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The half of D114's exit 3 that nothing could see.

    **Two guards return 3 from this function**, and the test beside this one
    trips both. `if judged_errored or judged_unevaluable:` counts results;
    `if silent:` asks whether any dimension produced no verdict at all (D134).
    A run where every result errored satisfies both, so the control that
    restored the first -- `if False:` -- left the suite green and reported that
    the guard was measuring nothing. It was: not because the guard is wrong, but
    because no test asked it anything its neighbor could not answer.

    Fabricating a citation on **one call** separates them. Every dimension keeps
    its verdicts from the other fifteen, so none is `measured_nothing` and the
    second guard stays quiet; the errored count is non-zero, so the first fires.
    The assertion that the second guard did not fire is what keeps this test
    honest if the roll-up ever widens.
    """
    log = _record_reference_log(tmp_path, citations=("T999",), fabricate_only=("CALL-01",))
    expected = _judged_results_over_the_design_set()
    code = main(
        [
            "run",
            "--tier",
            "judge",
            "--mode",
            "replay",
            "--run-log",
            str(log),
            "--run-log-dir",
            str(tmp_path / "out"),
            "--max-calls",
            str(expected * (1 + INFORMED_RETRY_BUDGET) + 10),
        ]
    )
    out = capsys.readouterr().out
    assert code == 3, out[-800:]
    assert "TIER INCOMPLETE" in out
    assert "produced no verdict at all" not in out, (
        "the measured-nothing guard fired, so this run cannot distinguish the two exit-3 "
        "paths and the control over the count-based one is blind again:\n" + out[-800:]
    )


def _record_reference_log(
    tmp_path: Path,
    *,
    template_hash: str | None = None,
    citations: tuple[str, ...] = ("T1",),
    fabricate_only: tuple[str, ...] = (),
    name: str = "reference.jsonl",
    mode: str = "replay",
    rubric_version: str | None = None,
    labels_manifest: str = "",
) -> Path:
    """Record a log the CLI can replay, from a scripted transport.

    Built by running the real judged engine over the real corpus with canned
    answers, rather than by writing JSON by hand: a hand-written log would
    agree with whatever the test author believed a request hash was, and that
    belief is exactly what this needs to test.

    `citations` is what the canned answer cites. A fabricated identifier makes
    the engine spend its one informed retry and record BOTH requests, so a log
    recorded this way replays to `errored` rather than to a cache miss -- the
    retry carries a different user message and therefore a different request
    hash, so a log holding only the first attempt could not replay the second.

    `fabricate_only` narrows that to named calls, and exists because a run where
    EVERY result errored cannot tell two exit-3 guards apart: every dimension is
    also `measured_nothing`, so both fire and removing either changes nothing
    (D143). Naming one call leaves every dimension holding verdicts from the
    other fifteen, which is the only shape the count-based guard catches alone.

    `mode` is what the header declares. A resume refuses a log that says `replay`,
    so the resume tests record one that says `live` (D153). `rubric_version` is
    what it declares for the rubric, so a resume can be handed a log recorded
    under another one (D161). `labels_manifest` is the manifest it names, so a
    replay or a resume can be handed a log sealed against other labels (D173).
    """
    template = load_template(REPO_ROOT / "prompts" / "judge-dimension.v1.md")
    rubric = load_rubric(REPO_ROOT / "rubric.yaml", build_registry().keys())
    entry = rubric.by_id("J-policy-alignment")
    assert entry.judge is not None

    policies = load_policies(REPO_ROOT / "corpus" / "policies")
    contexts = [
        build_context(parse_call(path), policies, policy_tool="fetch_policy")
        for path in sorted((REPO_ROOT / "corpus" / "transcripts").glob("*.txt"))
    ]

    corpus_version = (REPO_ROOT / "corpus" / "CORPUS_VERSION").read_text(encoding="utf-8").strip()
    calls = tuple(
        parse_call(p) for p in sorted((REPO_ROOT / "corpus" / "transcripts").glob("*.txt"))
    )
    digest = content_hash(build_payload(calls, corpus_version, REPO_ROOT))

    header = RunLogHeader(
        rubric_version=rubric_version or rubric.version,
        prompt_template_hash=template_hash or template.sha256,
        corpus_version=corpus_version,
        artifact_hash=digest,
        mode=mode,
        started_at="2026-09-09T00:00:00Z",
        labels_manifest=labels_manifest,
        # A held-out run writes the rubric it judged under beside the manifest
        # (D183), so a log recorded for one here carries it too; without it every
        # held-out replay would be refused for naming a rubric its log does not.
        rubric_hash=rubric_hash(REPO_ROOT / "rubric.yaml") if labels_manifest else "",
    )
    path = tmp_path / name

    class _Canned:
        """A canned answer **shaped by the entry that was asked**.

        One literal verdict for every request was enough while the rubric held
        one judged entry. It holds seven with five different scales now, so a
        fixture answering `aligned` to all of them is refused by
        `validate_result` on six -- correctly, and for a reason about the
        fixture. The verdict is read off the declared schema's own enum, so a
        scale renamed in the rubric moves this with it.
        """

        def send(self, request: JudgeRequest) -> JudgeResponse:
            properties = request.schema["properties"]
            assert isinstance(properties, dict)
            cited = (
                citations if not fabricate_only or request.call_id in fabricate_only else ("T1",)
            )
            payload: dict[str, Any] = {
                "verdict": properties["verdict"]["enum"][0],
                "rationale": "canned",
                "citations": list(cited),
            }
            if "rests_on" in properties:
                listed = re.findall(r"^([A-Z]-[a-z-]+): ", request.prompt, re.MULTILINE)
                payload["rests_on"] = listed or ["J-policy-alignment"]
            return JudgeResponse(
                text=json.dumps(payload),
                stop_reason="end_turn",
                stop_category=None,
                stop_explanation=None,
                input_tokens=10,
                output_tokens=5,
                model="claude-sonnet-5",
                latency_ms=1,
            )

    transport = RecordingTransport(_Canned(), RunLogWriter(path, header))
    run_judged(
        rubric,
        contexts,
        Provenance(rubric.version, corpus_version, digest),
        template=template,
        transport=transport,
    )
    return path


def test_the_default_ceiling_covers_the_shipped_judged_run() -> None:
    """The number, compared against the configuration it was written for.

    `DEFAULT_CALL_CEILING` was 200 through P3, and its comment said why: "200
    covers one full pass of the shipped judged entry over the design set with
    room for retries". The rubric held one judged entry when that was written
    and holds seven now, so the default became a value that **refused the run
    it existed to permit** -- a judged replay over the shipped rubric halted at
    the ceiling and exited 3, which is a finding about the harness rather than
    about the agent.

    Nothing noticed, because the justification was prose sitting beside the
    number. This is that prose turned into a comparison: the ceiling has to
    cover every judged call the shipped configuration issues, plus one informed
    retry for each, because the ceiling counts logical sends and the retry is
    one of them.

    **Not an equality.** A ceiling exactly the size of the run is a run that
    fails on its first transient re-send, and this is a net rather than a
    budget -- the estimate-and-confirm prompt is what an operator agrees to.
    """
    rubric = load_rubric(REPO_ROOT / "rubric.yaml", build_registry().keys())
    policies = load_policies(REPO_ROOT / "corpus" / "policies")
    contexts = [
        build_context(parse_call(path), policies, policy_tool="fetch_policy")
        for path in sorted((REPO_ROOT / "corpus" / "transcripts").glob("*.txt"))
    ]

    expected = 0
    for entry in rubric.for_tier(CheckTier.JUDGE):
        assert entry.judge is not None
        applies = sum(
            1
            for context in contexts
            if not absent_categories(
                context, entry.judge.applies_when_facts_present, entry_id=entry.id
            )
        )
        expected += applies * entry.judge.repetitions

    assert expected, "the shipped rubric issues no judged call, so this compares nothing"
    needed = expected * (1 + INFORMED_RETRY_BUDGET)
    assert needed <= DEFAULT_CALL_CEILING, (
        f"the default ceiling is {DEFAULT_CALL_CEILING} and the shipped judged tier issues "
        f"{expected} calls, needing {needed} with an informed retry on each. A run with no "
        "--max-calls would halt part-way and exit 3."
    )


def test_a_resumed_run_issues_only_the_calls_its_log_lacks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """OB-20: an aborted live run's log is resumed rather than paid for again (D153).

    A live log is recorded and cut in half, which is what an abort leaves: every
    line up to the last complete call. The resumed run is given a stand-in for the
    API that answers as the full run did and counts every call it is sent, and a
    ceiling of exactly the calls the half log lacks. Five things follow.

    It issues those calls and no others -- a served answer is not a call. It
    completes under that ceiling, which it cannot if the ceiling counts served
    answers. It exits as a replay of the full log does, because every answer is
    the full run's. It says so when it ends, counting every answer the half log
    holds as served and the calls it lacks as issued (OB-24). And the log it
    writes is complete and says what it is:
    `mode: live`, since every call in it went to the API, with `resumed_from`
    naming the session the first half came from.
    """
    full = _record_reference_log(tmp_path, name="full.jsonl", mode="live")
    _, full_entries = read_run_log(full)
    answers = {
        (entry.request.request_hash, entry.request.repetition): entry.response
        for entry in full_entries
    }

    lines = full.read_text(encoding="utf-8").splitlines()
    partial = tmp_path / "partial.jsonl"
    partial.write_bytes(("\n".join(lines[: len(lines) // 2]) + "\n").encode("utf-8"))
    _, partial_entries = read_run_log(partial)
    missing = len(full_entries) - len(partial_entries)
    assert 0 < missing < len(full_entries), "the half log is not a partial run"

    replayed = main(
        [
            "run",
            "--tier",
            "judge",
            "--mode",
            "replay",
            "--run-log",
            str(full),
            "--run-log-dir",
            str(tmp_path / "replayed"),
        ]
    )
    capsys.readouterr()

    issued: list[str] = []

    class _AnswersAsTheFullRunDid:
        """Stands in for `LiveTransport`, and counts every call it is sent."""

        def __init__(self, *, root: Path) -> None:
            del root

        def send(self, request: JudgeRequest) -> JudgeResponse:
            issued.append(request.request_hash)
            return answers[(request.request_hash, request.repetition)]

    monkeypatch.setattr("harness.core.transport.LiveTransport", _AnswersAsTheFullRunDid)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake-0123456789")
    monkeypatch.setattr(cli, "confirm_spend", lambda _prompt: True)
    out_dir = tmp_path / "out"
    code = main(
        [
            "run",
            "--tier",
            "judge",
            "--mode",
            "live",
            "--resume",
            str(partial),
            "--run-log-dir",
            str(out_dir),
            "--max-calls",
            str(missing),
        ]
    )
    captured = capsys.readouterr()
    assert code == replayed, captured.err[-800:]
    assert len(issued) == missing, f"issued {len(issued)} calls to finish a log {missing} short"
    assert "resume:" in captured.out
    assert (
        f"resume: {len(partial_entries)} answer(s) served from {partial} and "
        f"{missing} call(s) issued" in captured.out
    ), captured.out[-1200:]

    written = sorted(out_dir.glob("*.jsonl"))
    assert len(written) == 1
    header, entries = read_run_log(written[0])
    assert header.mode == "live"
    assert header.resumed_from == ("2026-09-09T00:00:00Z",), (
        "the resumed log does not name the session its first half came from"
    )
    assert {(entry.request.request_hash, entry.request.repetition) for entry in entries} == set(
        answers
    )


def test_resume_needs_live_mode(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Resuming issues the calls a log lacks, and replay issues none (D153)."""
    log = _record_reference_log(tmp_path, mode="live")
    code = main(
        [
            "run",
            "--tier",
            "judge",
            "--mode",
            "replay",
            "--run-log",
            str(log),
            "--resume",
            str(log),
            "--run-log-dir",
            str(tmp_path / "out"),
        ]
    )
    assert code == 2
    assert "--resume" in capsys.readouterr().err


def test_a_torn_run_log_is_refused_by_name_rather_than_as_a_traceback(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """P4-11. Replay over a log cut off mid-line exits 2, naming the file and the line.

    The parser's own error escaped every command that reads a log, so replay exited
    1 -- the code for a gate that failed, a finding about the agent -- with a
    traceback. A damaged log is a run that could not be made (OB-28, D167).
    """
    log = _record_reference_log(tmp_path, mode="live")
    lines = log.read_text(encoding="utf-8").splitlines()
    torn = tmp_path / "torn.jsonl"
    torn.write_bytes("\n".join([*lines[:-1], lines[-1][: len(lines[-1]) // 2]]).encode("utf-8"))

    code = main(
        [
            "run",
            "--tier",
            "judge",
            "--mode",
            "replay",
            "--run-log",
            str(torn),
            "--run-log-dir",
            str(tmp_path / "out"),
        ]
    )
    err = capsys.readouterr().err
    assert code == 2, err[-800:]
    assert "torn.jsonl" in err, err[-800:]
    assert f"line {len(lines)}" in err, err[-800:]


def test_a_resume_reads_a_torn_log_to_its_last_complete_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """OB-28. A resume finishes a log whose last line was cut off mid-write, and says so.

    A run that stops mid-write leaves its last line incomplete. The resume drops that
    line rather than refusing the log it exists to finish, issues exactly the calls
    the complete records lack -- the torn line's among them -- and prints that it
    dropped one (D167).
    """
    full = _record_reference_log(tmp_path, name="full.jsonl", mode="live")
    _, full_entries = read_run_log(full)
    answers = {
        (entry.request.request_hash, entry.request.repetition): entry.response
        for entry in full_entries
    }
    lines = full.read_text(encoding="utf-8").splitlines()
    half = len(lines) // 2
    complete = tmp_path / "complete-half.jsonl"
    complete.write_bytes(("\n".join(lines[:half]) + "\n").encode("utf-8"))
    _, kept = read_run_log(complete)
    torn = tmp_path / "torn-half.jsonl"
    torn.write_bytes(
        ("\n".join(lines[:half]) + "\n" + lines[half][: len(lines[half]) // 2]).encode("utf-8")
    )
    missing = len(full_entries) - len(kept)
    assert 0 < missing < len(full_entries), "the torn log is not a partial run"

    issued: list[str] = []

    class _AnswersAsTheFullRunDid:
        """Stands in for `LiveTransport`, and counts every call it is sent."""

        def __init__(self, *, root: Path) -> None:
            del root

        def send(self, request: JudgeRequest) -> JudgeResponse:
            issued.append(request.request_hash)
            return answers[(request.request_hash, request.repetition)]

    monkeypatch.setattr("harness.core.transport.LiveTransport", _AnswersAsTheFullRunDid)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake-0123456789")
    monkeypatch.setattr(cli, "confirm_spend", lambda _prompt: True)
    code = main(
        [
            "run",
            "--tier",
            "judge",
            "--mode",
            "live",
            "--resume",
            str(torn),
            "--run-log-dir",
            str(tmp_path / "out"),
            "--max-calls",
            str(missing),
        ]
    )
    captured = capsys.readouterr()
    assert code not in (2, 3), captured.err[-800:]
    assert len(issued) == missing, f"issued {len(issued)} calls to finish a log {missing} short"
    assert "cut off mid-write" in captured.out


def _rubric_with_edited_questions(tmp_path: Path, *, only: str | None) -> Path:
    """The shipped rubric with judged questions edited and its version string kept.

    The edit P4-4 describes: one the staleness check does not see, because the
    rubric's version is its author's to change and nobody changed it. `only` names
    the one entry to edit; `None` edits every judged entry.
    """
    document = yaml.safe_load((REPO_ROOT / "rubric.yaml").read_text(encoding="utf-8"))
    for raw in document["entries"]:
        if raw.get("tier") == "judge" and (only is None or raw["id"] == only):
            raw["question"] = f"{raw['question']} (edited)"
    path = tmp_path / ("rubric-edited.yaml" if only is None else f"rubric-edited-{only}.yaml")
    path.write_text(yaml.safe_dump(document, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return path


def test_a_resume_would_notice_a_log_answering_no_dimension_request_run_anyway(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """P4-4. A resume that can serve nothing is refused before spend is approved (OB-24).

    An edit that leaves the rubric version unchanged passes the staleness check, so a
    resume under it missed on every request and ran anyway, issuing every call under a
    header naming a session that served nothing. Every dimension's request is known
    before anything is sent, so a log answering none of them is refused there, with no
    confirmation asked and no log written (D168).
    """
    log = _record_reference_log(tmp_path, name="recorded.jsonl", mode="live")
    edited = _rubric_with_edited_questions(tmp_path, only=None)
    asked: list[str] = []

    def _decline(prompt: str) -> bool:
        asked.append(prompt)
        return False

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake-0123456789")
    monkeypatch.setattr(cli, "confirm_spend", _decline)
    out_dir = tmp_path / "out"
    code = main(
        [
            "run",
            "--tier",
            "judge",
            "--mode",
            "live",
            "--resume",
            str(log),
            "--rubric",
            str(edited),
            "--run-log-dir",
            str(out_dir),
        ]
    )
    err = capsys.readouterr().err
    assert code == 2, err[-800:]
    assert "holds an answer to none of the" in err, err[-800:]
    assert asked == [], "a resume that could serve nothing reached the confirmation"
    assert not list(out_dir.glob("*.jsonl")), "a refused resume wrote a log"


def test_a_resume_under_an_edited_entry_would_notice_its_counts_misprinted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """P4-4's case, run: one entry's question edited under an unchanged rubric version.

    The staleness check passes and the log still answers the other dimensions, so the
    resume goes ahead: the edited entry's requests miss and are issued, what is unchanged
    is served, and the run's end says how many of each -- which went unsaid when a resume
    served nothing at all (OB-24, D168).
    """
    log = _record_reference_log(tmp_path, name="recorded.jsonl", mode="live")
    _, recorded_entries = read_run_log(log)
    recorded_keys = {
        (entry.request.request_hash, entry.request.repetition) for entry in recorded_entries
    }
    edited = _rubric_with_edited_questions(tmp_path, only="J-policy-alignment")
    issued: list[str] = []

    class _AnswersFromTheSchema:
        """Stands in for `LiveTransport`: counts every call and answers as its schema allows."""

        def __init__(self, *, root: Path) -> None:
            del root

        def send(self, request: JudgeRequest) -> JudgeResponse:
            issued.append(request.request_hash)
            properties = request.schema["properties"]
            payload: dict[str, Any] = {
                "verdict": properties["verdict"]["enum"][0],
                "rationale": "canned",
                "citations": ["T1"],
            }
            if "rests_on" in properties:
                listed = re.findall(r"^([A-Z]-[a-z-]+): ", request.prompt, re.MULTILINE)
                payload["rests_on"] = listed or ["J-policy-alignment"]
            return JudgeResponse(
                text=json.dumps(payload),
                stop_reason="end_turn",
                stop_category=None,
                stop_explanation=None,
                input_tokens=10,
                output_tokens=5,
                model="claude-sonnet-5",
                latency_ms=1,
            )

    monkeypatch.setattr("harness.core.transport.LiveTransport", _AnswersFromTheSchema)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake-0123456789")
    monkeypatch.setattr(cli, "confirm_spend", lambda _prompt: True)
    out_dir = tmp_path / "out"
    code = main(
        [
            "run",
            "--tier",
            "judge",
            "--mode",
            "live",
            "--resume",
            str(log),
            "--rubric",
            str(edited),
            "--run-log-dir",
            str(out_dir),
        ]
    )
    captured = capsys.readouterr()
    assert code not in (2, 3), captured.err[-800:]
    assert issued, "the edited entry's requests were all served, so the edit went unseen"
    (written,) = sorted(out_dir.glob("*.jsonl"))
    _, written_entries = read_run_log(written)
    served = sum(
        1
        for entry in written_entries
        if (entry.request.request_hash, entry.request.repetition) in recorded_keys
    )
    assert served, "nothing unchanged was served"
    dimension_entries = [
        entry
        for entry in recorded_entries
        if entry.request.entry_id != "J-call-synthesis" and entry.request.retry_index == 0
    ]
    answered = sum(
        1 for entry in dimension_entries if entry.request.entry_id != "J-policy-alignment"
    )
    assert 0 < answered < len(dimension_entries), "the edit left no dimension request missing"
    assert (
        f"resume: {answered} of the {len(dimension_entries)} dimension request(s) this run sends "
        "are answered in that log" in captured.out
    ), captured.out[-1600:]
    assert (
        f"resume: {served} answer(s) served from {log} and {len(issued)} call(s) issued"
        in captured.out
    ), captured.out[-1200:]


def test_a_resume_log_is_refused_before_anyone_is_asked_to_approve_spend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Every refusal a resume log can earn, and none reaches the confirmation (D153).

    A log recorded in replay mode holds answers no session issued, and a log
    recorded against a different rubric version or template would describe two
    states under one header. Each is refused with its reason, after the credential
    and before the estimate -- the order the phase-3 audit put the credential check
    in, for the same reason: an operator should not approve spend on a run that
    will be refused. The rubric version went unasserted through a resume until
    D161 (P4-19): the comparison refusing it is replay's, and only replay drove it.
    """
    asked: list[str] = []

    def _decline(prompt: str) -> bool:
        asked.append(prompt)
        return False

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake-0123456789")
    monkeypatch.setattr(cli, "confirm_spend", _decline)
    never_live = _record_reference_log(tmp_path, name="replayed.jsonl")
    stale = _record_reference_log(tmp_path, name="stale.jsonl", mode="live", template_hash="0" * 64)
    other_rubric = _record_reference_log(
        tmp_path, name="other-rubric.jsonl", mode="live", rubric_version="0"
    )
    for log, reason in (
        (never_live, "'replay' mode"),
        (stale, "prompt-template hash"),
        (other_rubric, "rubric version"),
    ):
        code = main(
            [
                "run",
                "--tier",
                "judge",
                "--mode",
                "live",
                "--resume",
                str(log),
                "--run-log-dir",
                str(tmp_path / "out"),
            ]
        )
        err = capsys.readouterr().err
        assert code == 2, err
        assert reason in err, err
        assert "--allow-stale-replay" not in err, "a resume refusal offered replay's override"
    assert asked == [], "a resume log was refused only after spend had been approved"


#: Two labels manifests, both invented. No test below reads, writes or names a
#: held-out transcript, run log or label: a run is made held out by declaring design
#: calls in a HELDOUT_SET of the test's own (D173).
_MANIFEST: Final[str] = "0123456789abcdef" * 2 + "01234567"
_OTHER_MANIFEST: Final[str] = "fedcba9876543210" * 2 + "fedcba98"


def _declare_held_out(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, only: str | None = None
) -> None:
    """Point the run at a HELDOUT_SET of the test's own, declaring design calls.

    Every design call by default, so the design corpus reads as a held-out run;
    `only` declares that one call, so the corpus reads as a run mixing the two sets.
    """
    design = (REPO_ROOT / "corpus" / "DESIGN_SET").read_text(encoding="utf-8").split()
    declared = tmp_path / "HELDOUT_SET"
    declared.write_text(
        "# invented for a test\n" + "\n".join([only] if only else design) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    monkeypatch.setattr(cli, "_HELDOUT_SET", str(declared))
    # A held-out run is refused transcripts inside the checkout (D174), so the design
    # transcripts are copied out and made the default a run reads.
    transcripts = tmp_path / "transcripts"
    shutil.copytree(REPO_ROOT / "corpus" / "transcripts", transcripts)
    monkeypatch.setattr(cli, "_DEFAULT_TRANSCRIPTS", str(transcripts))
    # And its corpus version file, refused inside the checkout for the same reason
    # (D182): the default holds the design corpus's version, which a held-out run
    # would stamp into a header describing a corpus it never read.
    version = tmp_path / "CORPUS_VERSION"
    shutil.copy(REPO_ROOT / "corpus" / "CORPUS_VERSION", version)
    monkeypatch.setattr(cli, "_DEFAULT_CORPUS_VERSION", str(version))


def _judged_replay(log: Path, out_dir: Path, *extra: str) -> int:
    return main(
        [
            "run",
            "--tier",
            "judge",
            "--mode",
            "replay",
            "--run-log",
            str(log),
            "--run-log-dir",
            str(out_dir),
            *extra,
        ]
    )


def test_a_held_out_replay_writes_its_labels_manifest_into_the_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A held-out run's log names the labels manifest it was given (D173).

    The key the held-out repository's gate reads: a replay over calls HELDOUT_SET
    declares, handed the manifest its log was sealed against, completes and writes
    a log whose header names it.
    """
    _declare_held_out(tmp_path, monkeypatch)
    log = _record_reference_log(tmp_path, labels_manifest=_MANIFEST)
    out_dir = tmp_path / "out"
    code = _judged_replay(log, out_dir, "--labels-manifest", _MANIFEST)
    assert code == 0, capsys.readouterr().err[-800:]
    written = sorted(out_dir.glob("*.jsonl"))
    assert len(written) == 1
    header, _ = read_run_log(written[0])
    assert header.labels_manifest == _MANIFEST, "the run left its labels manifest out of its log"


def test_a_held_out_replay_writes_the_rubric_it_judged_under(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A held-out run's log names the rubric it judged under (D183).

    The hash is recomputed here from the rubric on disk rather than read off the
    run, so a run writing a constant would fail this. A design run writes no such
    key, which `test_a_header_carries_the_rubric_a_held_out_run_judged_under` holds
    in the writer.
    """
    _declare_held_out(tmp_path, monkeypatch)
    log = _record_reference_log(tmp_path, labels_manifest=_MANIFEST)
    out_dir = tmp_path / "out"
    code = _judged_replay(log, out_dir, "--labels-manifest", _MANIFEST)
    assert code == 0, capsys.readouterr().err[-800:]
    written = sorted(out_dir.glob("*.jsonl"))
    assert len(written) == 1, written
    header, _ = read_run_log(written[0])
    assert header.rubric_hash == rubric_hash(REPO_ROOT / "rubric.yaml"), (
        "the run left the rubric it judged under out of its log"
    )


def test_a_held_out_replay_would_notice_a_log_judged_under_another_rubric(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A held-out replay is refused a log recorded under another rubric (D183).

    The recorded log names a rubric hash this run does not, with the same rubric
    version and prompt-template hash throughout -- which is the case neither of
    those two values can see. Refused before anything is served, and with no log
    written.
    """
    _declare_held_out(tmp_path, monkeypatch)
    log = _record_reference_log(tmp_path, labels_manifest=_MANIFEST)
    recorded = log.read_text(encoding="utf-8").splitlines()
    header = json.loads(recorded[0])
    header["rubric_hash"] = "3c" * 32
    recorded[0] = json.dumps(header, sort_keys=True)
    log.write_text("\n".join(recorded) + "\n", encoding="utf-8", newline="\n")
    out_dir = tmp_path / "out"
    code = _judged_replay(log, out_dir, "--labels-manifest", _MANIFEST)
    err = capsys.readouterr().err
    assert code == 2, err[-800:]
    assert "rubric hash" in err, err[-800:]
    assert not list(out_dir.glob("*.jsonl")), "a refused replay wrote a log"


def test_a_held_out_run_would_notice_its_labels_manifest_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A judged run over calls HELDOUT_SET declares is refused without the flag (D173).

    Refused naming the flag it needs, before the log it replays is read, and with no
    log written.
    """
    _declare_held_out(tmp_path, monkeypatch)
    log = _record_reference_log(tmp_path)
    out_dir = tmp_path / "out"
    code = _judged_replay(log, out_dir)
    err = capsys.readouterr().err
    assert code == 2, err[-800:]
    assert "so it needs --labels-manifest" in err, err[-800:]
    assert not list(out_dir.glob("*.jsonl")), "a held-out run with no manifest wrote a log"


def test_a_run_mixing_held_out_and_design_calls_would_be_noticed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A run reading calls HELDOUT_SET declares beside calls it does not is refused (D173).

    Refused with a well-formed manifest given, so what refuses it is the mix: a
    held-out run log holds held-out calls alone.
    """
    _declare_held_out(tmp_path, monkeypatch, only="CALL-01")
    log = _record_reference_log(tmp_path, labels_manifest=_MANIFEST)
    out_dir = tmp_path / "out"
    code = _judged_replay(log, out_dir, "--labels-manifest", _MANIFEST)
    err = capsys.readouterr().err
    assert code == 2, err[-800:]
    assert "run the two sets apart" in err, err[-800:]
    assert not list(out_dir.glob("*.jsonl")), "a run mixing the two sets wrote a log"


def test_a_design_run_would_notice_a_labels_manifest_it_has_no_use_for(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A run over no call HELDOUT_SET declares is refused the flag (D173).

    Only a held-out run takes it, so a manifest in a header marks a held-out log and
    nothing else. Run against this repository's own HELDOUT_SET, which declares no
    design call.
    """
    log = _record_reference_log(tmp_path, labels_manifest=_MANIFEST)
    out_dir = tmp_path / "out"
    code = _judged_replay(log, out_dir, "--labels-manifest", _MANIFEST)
    err = capsys.readouterr().err
    assert code == 2, err[-800:]
    assert "no call this run reads is declared in HELDOUT_SET" in err, err[-800:]
    assert not list(out_dir.glob("*.jsonl")), "a design run given a manifest wrote a log"


def test_a_malformed_labels_manifest_would_be_noticed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The flag is checked for a full commit SHA's shape, and for nothing more (D173).

    Uppercase, shortened and overlong values are refused by name. Which commit it
    names is the held-out repository's gate to check.
    """
    _declare_held_out(tmp_path, monkeypatch)
    log = _record_reference_log(tmp_path)
    out_dir = tmp_path / "out"
    for malformed in (_MANIFEST.upper(), _MANIFEST[:12], _MANIFEST + "0"):
        code = _judged_replay(log, out_dir, "--labels-manifest", malformed)
        err = capsys.readouterr().err
        assert code == 2, err[-800:]
        assert f"--labels-manifest {malformed!r} is not a full commit SHA" in err, err[-800:]
    assert not list(out_dir.glob("*.jsonl")), "a malformed manifest wrote a log"


def test_a_judged_run_would_notice_its_held_out_set_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """With no HELDOUT_SET where the run reads it, every judged run is refused (D173).

    A run that cannot tell whether its calls are held out cannot tell whether it
    needs a labels manifest, so the missing file is refused rather than read as
    declaring nothing. A design run is enough to show it.
    """
    monkeypatch.setattr(cli, "_HELDOUT_SET", str(tmp_path / "absent" / "HELDOUT_SET"))
    log = _record_reference_log(tmp_path)
    out_dir = tmp_path / "out"
    code = _judged_replay(log, out_dir)
    err = capsys.readouterr().err
    assert code == 2, err[-800:]
    assert "reads HELDOUT_SET to tell whether its calls are held out" in err, err[-800:]
    assert not list(out_dir.glob("*.jsonl")), "a run with no HELDOUT_SET wrote a log"


def test_a_held_out_replay_would_notice_a_log_naming_other_labels(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A held-out replay is refused a log sealed against another manifest (D173).

    Refused before anything is served, with no log written: the log it wrote would
    name one set of held-out labels over answers recorded under another.
    """
    _declare_held_out(tmp_path, monkeypatch)
    log = _record_reference_log(tmp_path, labels_manifest=_OTHER_MANIFEST)
    out_dir = tmp_path / "out"
    code = _judged_replay(log, out_dir, "--labels-manifest", _MANIFEST)
    err = capsys.readouterr().err
    assert code == 2, err[-800:]
    assert f"recorded under labels manifest {_OTHER_MANIFEST}" in err, err[-800:]
    assert not list(out_dir.glob("*.jsonl")), "a replay of a log naming other labels wrote a log"


def test_a_held_out_resume_would_notice_a_log_naming_other_labels(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A held-out resume is refused a log sealed against other labels, before approval (D173).

    A log naming another manifest and a log naming none are each refused with the
    manifest it names, no confirmation asked and no log written.
    """
    asked: list[str] = []

    def _decline(prompt: str) -> bool:
        asked.append(prompt)
        return False

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake-0123456789")
    monkeypatch.setattr(cli, "confirm_spend", _decline)
    _declare_held_out(tmp_path, monkeypatch)
    out_dir = tmp_path / "out"
    for name, sealed in (("other.jsonl", _OTHER_MANIFEST), ("unsealed.jsonl", "")):
        log = _record_reference_log(tmp_path, name=name, mode="live", labels_manifest=sealed)
        code = main(
            [
                "run",
                "--tier",
                "judge",
                "--mode",
                "live",
                "--resume",
                str(log),
                "--labels-manifest",
                _MANIFEST,
                "--run-log-dir",
                str(out_dir),
            ]
        )
        err = capsys.readouterr().err
        assert code == 2, err[-800:]
        assert f"recorded under labels manifest {sealed or 'none'}" in err, err[-800:]
    assert asked == [], "a resume of a log naming other labels reached the confirmation"
    assert not list(out_dir.glob("*.jsonl")), "a refused resume wrote a log"


def test_a_held_out_run_would_notice_a_path_inside_the_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A held-out replay is refused its transcripts, its log directory, the log it
    replays or its corpus version file when that path resolves inside this checkout,
    and writes nothing (D174, D182).

    One path at a time, every other path outside, each refusal naming its flag. The
    paths inside are this repository's own design files, and the log directory is
    `runs/`, the default; anything a regression writes there is removed again. The
    corpus version file joined them at D182: its default holds the design corpus's
    version, which a held-out run would otherwise stamp into a header describing a
    corpus it never read.
    """
    _declare_held_out(tmp_path, monkeypatch)
    log = _record_reference_log(tmp_path, labels_manifest=_MANIFEST)
    out_dir = tmp_path / "out"
    runs = REPO_ROOT / "runs"
    before = set(runs.iterdir())
    try:
        for flag, value in (
            ("--transcripts", "corpus/transcripts"),
            ("--run-log-dir", "runs"),
            ("--run-log", "runs/reference-corpus-0.6.0.jsonl"),
            ("--corpus-version-file", "corpus/CORPUS_VERSION"),
        ):
            code = _judged_replay(log, out_dir, "--labels-manifest", _MANIFEST, flag, value)
            err = capsys.readouterr().err
            assert code == 2, err[-800:]
            assert "a held-out run keeps its transcripts and run logs outside" in err, err[-800:]
            assert f"{flag} {value} would put it inside" in err, err[-800:]
    finally:
        for stray in set(runs.iterdir()) - before:
            stray.unlink()
    assert not list(out_dir.glob("*.jsonl")), "a held-out run refused its paths wrote a log"


def test_a_held_out_runs_log_is_named_for_the_gate_that_admits_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A held-out run's log is written under the `heldout-` prefix the held-out
    repository's gate admits, and a design run's log is not (D184).

    Both runs are replays of a recorded log, so neither spends anything, and each
    name is read off the file the run wrote rather than from the code that builds it.
    What this replaces is a rename performed by hand after the run was paid for.
    """
    _declare_held_out(tmp_path, monkeypatch)
    held_out_log = _record_reference_log(tmp_path, labels_manifest=_MANIFEST)
    held_out_dir = tmp_path / "held-out"
    code = _judged_replay(held_out_log, held_out_dir, "--labels-manifest", _MANIFEST)
    assert code == 0, capsys.readouterr().err[-800:]
    written = sorted(held_out_dir.glob("*.jsonl"))
    assert len(written) == 1, written
    assert written[0].name.startswith("heldout-"), written[0].name
    assert written[0].name.endswith("-replay.jsonl"), written[0].name

    # A design run keeps the name it had: the prefix follows the header's labels
    # manifest, which only a held-out run carries. Declared here by a HELDOUT_SET of
    # the test's own that names nothing, so the same corpus reads as the design set
    # without copying it out a second time.
    declares_nothing = tmp_path / "EMPTY_HELDOUT_SET"
    declares_nothing.write_text("# declares nothing\n", encoding="utf-8", newline="\n")
    monkeypatch.setattr(cli, "_HELDOUT_SET", str(declares_nothing))
    design_log = _record_reference_log(tmp_path, name="design-log.jsonl")
    design_dir = tmp_path / "design"
    assert _judged_replay(design_log, design_dir) == 0, capsys.readouterr().err[-800:]
    written = sorted(design_dir.glob("*.jsonl"))
    assert len(written) == 1, written
    assert not written[0].name.startswith("heldout-"), written[0].name


def test_a_report_over_held_out_calls_would_notice_an_out_path_inside_the_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A report over calls `HELDOUT_SET` declares is refused `--out` inside this
    checkout, and is produced to a path outside it and on stdout (D185).

    The calls are this repository's own design calls, declared held out by a
    `HELDOUT_SET` of the test's own, so nothing held out is read. The refused path
    sits under `build/`, the project's own output directory, which is where a report
    would plausibly be written and which the absence check deliberately scans.
    """
    _declare_held_out(tmp_path, monkeypatch)
    # Removed either side of the refusal, not just asserted absent: the control
    # gate mutates one copy of the tree in place, so the run under a mutation that
    # lets this report through leaves the file behind for the next control's
    # unmutated run to trip over. `runs/` is kept clear the same way above.
    inside = REPO_ROOT / "build" / "held-out-report.md"
    inside.unlink(missing_ok=True)
    try:
        code = main(["report", "--out", "build/held-out-report.md"])
        err = capsys.readouterr().err
        assert code == 2, err[-800:]
        assert "carries the judge's verdicts on them" in err, err[-800:]
        assert "--out build/held-out-report.md would write it inside" in err, err[-800:]
        assert not inside.exists(), "a refused report wrote its file anyway"
    finally:
        inside.unlink(missing_ok=True)

    outside = tmp_path / "held-out-report.md"
    assert main(["report", "--out", str(outside)]) == 0, capsys.readouterr().err[-800:]
    assert outside.read_text(encoding="utf-8").startswith("# Evaluation report")

    capsys.readouterr()
    code = main(["report"])
    printed = capsys.readouterr()
    assert code == 0, printed.err[-800:]
    assert printed.out.startswith("# Evaluation report")


def test_a_design_report_is_still_written_where_it_is_asked_for(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The false-positive half of the refusal above: a report over design calls is
    written inside this checkout, which is how the snapshot is produced (D185).

    Written under `build/`, and removed again, so the check that reads this tree for
    held-out output is not handed a file by its own test suite.
    """
    destination = REPO_ROOT / "build" / "design-report-for-a-test.md"
    try:
        assert main(["report", "--out", str(destination)]) == 0, capsys.readouterr().err[-800:]
        assert destination.read_text(encoding="utf-8").startswith("# Evaluation report")
    finally:
        destination.unlink(missing_ok=True)


def test_a_held_out_resume_would_notice_its_log_inside_the_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A held-out resume is refused a log inside this checkout before any confirmation
    is asked for, and before the log is read (D174).

    The log named is the committed reference log, a design file, so nothing held out
    is read either way.
    """
    asked: list[str] = []

    def _decline(prompt: str) -> bool:
        asked.append(prompt)
        return False

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake-0123456789")
    monkeypatch.setattr(cli, "confirm_spend", _decline)
    _declare_held_out(tmp_path, monkeypatch)
    out_dir = tmp_path / "out"
    code = main(
        [
            "run",
            "--tier",
            "judge",
            "--mode",
            "live",
            "--resume",
            "runs/reference-corpus-0.6.0.jsonl",
            "--labels-manifest",
            _MANIFEST,
            "--run-log-dir",
            str(out_dir),
        ]
    )
    err = capsys.readouterr().err
    assert code == 2, err[-800:]
    assert "--resume runs/reference-corpus-0.6.0.jsonl would put it inside" in err, err[-800:]
    assert asked == [], "a resume of a log inside the checkout reached the confirmation"
    assert not list(out_dir.glob("*.jsonl")), "a refused resume wrote a log"


#: The held-out half of a split design corpus: eight design calls, CALL-08 among
#: them, because `A-record-fields-disagree` fires on CALL-08 alone over the corpus.
_HELD_OUT_HALF: Final[tuple[str, ...]] = tuple(f"CALL-{number:02d}" for number in range(1, 9))


def _split_corpus(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, held_out_calls: tuple[str, ...]
) -> tuple[Path, Path, Path]:
    """The design corpus split in two outside the checkout (D175).

    The calls named are declared held out in a HELDOUT_SET of the test's own and
    copied to one directory, the rest to another. Returns the design transcripts, the
    held-out transcripts and a held-out corpus version file. Every call is a design
    call, so nothing held out is read.
    """
    declared = tmp_path / "HELDOUT_SET"
    declared.write_text("\n".join(held_out_calls) + "\n", encoding="utf-8", newline="\n")
    monkeypatch.setattr(cli, "_HELDOUT_SET", str(declared))
    design, held_out = tmp_path / "design-transcripts", tmp_path / "held-out-transcripts"
    design.mkdir()
    held_out.mkdir()
    for transcript in sorted((REPO_ROOT / "corpus" / "transcripts").glob("*.txt")):
        shutil.copy(transcript, (held_out if transcript.stem in held_out_calls else design))
    version = tmp_path / "held-out-CORPUS_VERSION"
    shutil.copy(REPO_ROOT / "corpus" / "CORPUS_VERSION", version)
    return design, held_out, version


def _invented_labels(tmp_path: Path, calls: tuple[str, ...], **overrides: Any) -> tuple[Path, Path]:
    """Invented held-out labels over `calls`: HF-01 on CALL-08, traced to
    `A-record-fields-disagree`, and HF-02 on CALL-02, uncovered. Every other field of
    both is borrowed from a design finding; `overrides` replaces keys of the traces."""
    borrowed = load_findings(REPO_ROOT / "corpus" / "findings.yaml")[0]
    findings_file = tmp_path / "held-out-findings.yaml"
    findings_file.write_text(
        dump_findings(
            (
                replace(borrowed, id="HF-01", call_ref="CALL-08"),
                replace(borrowed, id="HF-02", call_ref="CALL-02"),
            )
        ),
        encoding="utf-8",
        newline="\n",
    )
    rubric = load_rubric(REPO_ROOT / "rubric.yaml", build_registry().keys())
    traces = {
        "rubric-frozen-v1": RUBRIC_FROZEN_V1,
        "traces": {
            entry.id: (["HF-01"] if entry.id == "A-record-fields-disagree" else [])
            for entry in rubric.entries
        },
        "uncovered": ["HF-02"],
        "calls_without_findings": [call for call in calls if call not in {"CALL-08", "CALL-02"}],
        **overrides,
    }
    traces_file = tmp_path / "held-out-traces.yaml"
    traces_file.write_text(yaml.safe_dump(traces), encoding="utf-8", newline="\n")
    return findings_file, traces_file


def _held_out_args(
    transcripts: Path, version: Path, log: Path, findings: Path, traces: Path
) -> list[str]:
    return [
        "--held-out-transcripts",
        str(transcripts),
        "--held-out-corpus-version-file",
        str(version),
        "--held-out-run-log",
        str(log),
        "--held-out-findings",
        str(findings),
        "--held-out-traces",
        str(traces),
    ]


def _agreement_row(out: str, section: str, entry_id: str) -> list[int]:
    """The five counts and the call count one section printed for one entry."""
    start = out.index(section)
    for line in out[start:].splitlines():
        if line.startswith(entry_id + " "):
            return [int(token) for token in line.split()[2:8]]
    raise AssertionError(f"{entry_id} has no row under {section!r}:\n{out[start:][:2000]}")


def test_agreement_would_notice_its_design_section_miscounted(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The design section over the committed reference log, and the held-out section
    left uncomputed while no held-out labels are given (D175).

    `A-record-fields-disagree` fires on CALL-08 alone and traces the finding there, so
    its row is one hit, no miss and no false alarm, over the sixteen design calls.
    """
    code = main(["agreement"])
    captured = capsys.readouterr()
    assert code == 0, captured.err[-800:]
    assert "design set: 16 calls" in captured.out
    assert "held-out set: not computed" in captured.out
    hit, miss, false_alarm, _, _, calls = _agreement_row(
        captured.out, "design set:", "A-record-fields-disagree"
    )
    assert (hit, miss, false_alarm, calls) == (1, 0, 0, 16), captured.out[:3000]


def test_agreement_would_notice_its_held_out_section_left_out(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """With all five held-out inputs, a held-out section beside the design one, each
    over its own calls (D175).

    The labels are invented over design calls: HF-01 sits on CALL-08 and is traced to
    `A-record-fields-disagree`, which fires there alone, so that row is one hit over
    the held-out half's eight calls.
    """
    design, held_out, version = _split_corpus(tmp_path, monkeypatch, _HELD_OUT_HALF)
    log = _record_reference_log(tmp_path, name="held-out.jsonl", labels_manifest=_MANIFEST)
    findings, traces = _invented_labels(tmp_path, _HELD_OUT_HALF)
    code = main(
        [
            "agreement",
            "--transcripts",
            str(design),
            *_held_out_args(held_out, version, log, findings, traces),
        ]
    )
    captured = capsys.readouterr()
    assert code == 0, captured.err[-800:]
    assert "design set: 8 calls" in captured.out
    assert "held-out set: 8 calls" in captured.out
    hit, miss, false_alarm, _, _, calls = _agreement_row(
        captured.out, "held-out set:", "A-record-fields-disagree"
    )
    assert (hit, miss, false_alarm, calls) == (1, 0, 0, 8), captured.out[-3000:]


def test_agreement_would_notice_held_out_inputs_given_in_part(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Some of the five held-out inputs and not all are refused, naming the missing
    ones, before anything is read (D175)."""
    code = main(
        [
            "agreement",
            "--held-out-findings",
            str(tmp_path / "findings.yaml"),
            "--held-out-traces",
            str(tmp_path / "traces.yaml"),
        ]
    )
    err = capsys.readouterr().err
    assert code == 2, err
    missing = "--held-out-transcripts, --held-out-corpus-version-file, --held-out-run-log"
    assert f"{missing} are missing" in err, err


def test_agreement_would_notice_a_held_out_input_inside_the_checkout(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A held-out input resolving inside this checkout is refused before anything is
    read (D174, D175). The one inside is this repository's own findings file."""
    args = _held_out_args(
        tmp_path / "transcripts",
        tmp_path / "CORPUS_VERSION",
        tmp_path / "held-out.jsonl",
        Path("corpus/findings.yaml"),
        tmp_path / "traces.yaml",
    )
    code = main(["agreement", *args])
    err = capsys.readouterr().err
    assert code == 2, err
    assert "--held-out-findings corpus" in err, err
    assert "would read them from inside" in err, err


def test_agreement_would_notice_design_calls_declared_held_out(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A design corpus holding a call HELDOUT_SET declares is refused, so the design
    section never scores a held-out call (D175)."""
    declared = tmp_path / "HELDOUT_SET"
    declared.write_text("CALL-01\n", encoding="utf-8", newline="\n")
    monkeypatch.setattr(cli, "_HELDOUT_SET", str(declared))
    code = main(["agreement"])
    err = capsys.readouterr().err
    assert code == 2, err
    assert "so the design section would score held-out calls" in err, err


def test_agreement_would_notice_a_held_out_set_holding_an_undeclared_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Held-out transcripts holding a call HELDOUT_SET does not declare are refused as
    not the held-out set (D173, D175)."""
    design, held_out, version = _split_corpus(tmp_path, monkeypatch, _HELD_OUT_HALF)
    shutil.copy(REPO_ROOT / "corpus" / "transcripts" / "CALL-09.txt", held_out)
    log = _record_reference_log(tmp_path, name="held-out.jsonl", labels_manifest=_MANIFEST)
    findings, traces = _invented_labels(tmp_path, _HELD_OUT_HALF)
    code = main(
        [
            "agreement",
            "--transcripts",
            str(design),
            *_held_out_args(held_out, version, log, findings, traces),
        ]
    )
    err = capsys.readouterr().err
    assert code == 2, err
    assert "are not declared in HELDOUT_SET, so they are not the held-out set" in err, err


def test_agreement_would_notice_a_held_out_log_naming_no_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A held-out run log whose header names no labels manifest is refused: every
    held-out run's log names one (D173, D175)."""
    design, held_out, version = _split_corpus(tmp_path, monkeypatch, _HELD_OUT_HALF)
    log = _record_reference_log(tmp_path, name="held-out.jsonl")
    findings, traces = _invented_labels(tmp_path, _HELD_OUT_HALF)
    code = main(
        [
            "agreement",
            "--transcripts",
            str(design),
            *_held_out_args(held_out, version, log, findings, traces),
        ]
    )
    err = capsys.readouterr().err
    assert code == 2, err
    assert "names no labels manifest" in err, err


def test_agreement_would_notice_held_out_labels_breaking_an_invariant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Held-out labels whose traces name another frozen commit are refused by the
    command, not only by the function it calls (D175)."""
    design, held_out, version = _split_corpus(tmp_path, monkeypatch, _HELD_OUT_HALF)
    log = _record_reference_log(tmp_path, name="held-out.jsonl", labels_manifest=_MANIFEST)
    findings, traces = _invented_labels(tmp_path, _HELD_OUT_HALF, **{"rubric-frozen-v1": "0" * 40})
    code = main(
        [
            "agreement",
            "--transcripts",
            str(design),
            *_held_out_args(held_out, version, log, findings, traces),
        ]
    )
    err = capsys.readouterr().err
    assert code == 2, err
    assert "names rubric-frozen-v1" in err, err


def test_agreement_would_notice_a_replay_that_stopped_part_way(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A design log cut in half is refused as a replay that stopped part-way, rather
    than scored over the calls it still answers (D175).

    Cut at a line boundary, so the log reads cleanly and the replay misses on the
    requests its missing half held, which the judged engine records as an abort.
    """
    log = _record_reference_log(tmp_path)
    lines = log.read_text(encoding="utf-8").splitlines(keepends=True)
    cut = tmp_path / "cut.jsonl"
    cut.write_text("".join(lines[: len(lines) // 2]), encoding="utf-8", newline="")
    code = main(["agreement", "--run-log", str(cut)])
    err = capsys.readouterr().err
    assert code == 2, err
    assert "stopped part-way" in err, err


#: How far each design call's id moves when it is copied out as an invented held-out
#: call: far enough that no copy takes a design call's id or one HELDOUT_SET declares.
_RENAMED_BY: Final[int] = 80


@dataclass(frozen=True)
class _RenamedSet:
    """Every design call copied out under a new id, as an invented held-out set (D188)."""

    transcripts: Path
    version: Path
    log: Path
    declared: Path
    renamed: dict[str, str]
    """Design call id to the id its copy carries."""


class _AsRecorded:
    """Answers a copied call as the committed reference log answered the call it was
    copied from, repetition for repetition and retry for retry.

    The copies cannot replay from that log directly: the synthesis resamples the
    dimensions' answers by call id (D154), so a renamed call's synthesis prompt is a
    request the log never saw. Recording through this gives the copies a log of their
    own that holds the same answers, so their coverage is the design set's.
    """

    def __init__(self, renamed: dict[str, str]) -> None:
        _, entries = read_run_log(REPO_ROOT / "runs" / "reference-corpus-0.6.0.jsonl")
        self._answers = {
            (e.request.call_id, e.request.entry_id, e.request.repetition, e.request.retry_index): (
                e.response
            )
            for e in entries
        }
        self._original = {copy: design for design, copy in renamed.items()}

    def send(self, request: JudgeRequest) -> JudgeResponse:
        key = (request.entry_id, request.repetition, request.retry_index)
        return self._answers[(self._original[request.call_id], *key)]


@pytest.fixture(scope="session")
def renamed_held_out(tmp_path_factory: pytest.TempPathFactory) -> _RenamedSet:
    """An invented held-out set: the design calls under new ids, a corpus version file,
    a HELDOUT_SET declaring the new ids, and a log naming a labels manifest (D188).

    Recorded once per session, since recording runs the judged engine over sixteen
    calls. Every file sits outside the checkout, and every call is a design call, so
    nothing held out is read.
    """
    directory = tmp_path_factory.mktemp("renamed-held-out")
    transcripts = directory / "transcripts"
    transcripts.mkdir()
    renamed: dict[str, str] = {}
    for path in sorted((REPO_ROOT / "corpus" / "transcripts").glob("*.txt")):
        copy = f"CALL-{int(path.stem.removeprefix('CALL-')) + _RENAMED_BY}"
        renamed[path.stem] = copy
        text = path.read_bytes().decode("utf-8")
        assert text.count(f"call_id: {path.stem}\n") == 1, path
        (transcripts / f"{copy}.txt").write_bytes(
            text.replace(f"call_id: {path.stem}\n", f"call_id: {copy}\n").encode("utf-8")
        )
    declared = directory / "HELDOUT_SET"
    declared.write_text("\n".join(renamed.values()) + "\n", encoding="utf-8", newline="\n")
    version = directory / "CORPUS_VERSION"
    shutil.copy(REPO_ROOT / "corpus" / "CORPUS_VERSION", version)

    template = load_template(REPO_ROOT / "prompts" / "judge-dimension.v1.md")
    rubric = load_rubric(REPO_ROOT / "rubric.yaml", build_registry().keys())
    policies = load_policies(REPO_ROOT / "corpus" / "policies")
    calls = tuple(parse_call(path) for path in sorted(transcripts.glob("*.txt")))
    corpus_version = version.read_text(encoding="utf-8").strip()
    digest = content_hash(build_payload(calls, corpus_version, REPO_ROOT))
    header = RunLogHeader(
        rubric_version=rubric.version,
        prompt_template_hash=template.sha256,
        corpus_version=corpus_version,
        artifact_hash=digest,
        mode="replay",
        started_at="2026-09-18T00:00:00Z",
        labels_manifest=_MANIFEST,
        rubric_hash=rubric_hash(REPO_ROOT / "rubric.yaml"),
    )
    log = directory / "heldout-renamed.jsonl"
    run_judged(
        rubric,
        [build_context(call, policies, policy_tool="fetch_policy") for call in calls],
        Provenance(rubric.version, corpus_version, digest),
        template=template,
        transport=RecordingTransport(_AsRecorded(renamed), RunLogWriter(log, header)),
    )
    return _RenamedSet(transcripts, version, log, declared, renamed)


def _renamed_labels(
    directory: Path, renamed: dict[str, str], *, untraced: str = "F-04", **overrides: Any
) -> tuple[Path, Path, Path]:
    """The design findings as invented held-out labels on the copied calls (D188).

    `F-NN` becomes `HF-NN` on the copy of its call, the traces are the rubric's with
    `untraced` left out of them, and the severity export is the design export with
    every id moved the same way, so its bands still agree with its cuts. Leaving one
    finding untraced is what makes the held-out section differ from the design one
    where it should. `overrides` replaces keys of the traces. Returns the findings,
    the traces and the severity export.
    """

    def held(finding_id: str) -> str:
        return "H" + finding_id

    design = load_findings(REPO_ROOT / "corpus" / "findings.yaml")
    findings_file = directory / "held-out-findings.yaml"
    findings_file.write_text(
        dump_findings(
            tuple(replace(f, id=held(f.id), call_ref=renamed[f.call_ref]) for f in design)
        ),
        encoding="utf-8",
        newline="\n",
    )
    rubric = load_rubric(REPO_ROOT / "rubric.yaml", build_registry().keys())
    traces = {
        entry.id: [held(f) for f in entry.traces_to if f != untraced] for entry in rubric.entries
    }
    traced = {finding for ids in traces.values() for finding in ids}
    document = {
        "rubric-frozen-v1": RUBRIC_FROZEN_V1,
        "traces": traces,
        "uncovered": sorted(held(f.id) for f in design if held(f.id) not in traced),
        "calls_without_findings": sorted(
            set(renamed.values()) - {renamed[f.call_ref] for f in design}
        ),
        **overrides,
    }
    traces_file = directory / "held-out-traces.yaml"
    traces_file.write_text(yaml.safe_dump(document), encoding="utf-8", newline="\n")

    export = json.loads((REPO_ROOT / "corpus" / "findings.severity.json").read_text("utf-8"))
    for row in export["severities"]:
        row["id"] = held(row["id"])
    for cut in export["cuts"]:
        cut["above_id"], cut["below_id"] = held(cut["above_id"]), held(cut["below_id"])
        cut["between"] = [held(finding) for finding in cut["between"]]
    export["unplaced"] = [held(finding) for finding in export["unplaced"]]
    severity_file = directory / "held-out-severity.json"
    severity_file.write_text(json.dumps(export, indent=2), encoding="utf-8", newline="\n")
    return findings_file, traces_file, severity_file


def _coverage_args(
    held_out: _RenamedSet, findings: Path, traces: Path, severity: Path, *, log: Path | None = None
) -> list[str]:
    return [
        "coverage",
        *_held_out_args(
            held_out.transcripts, held_out.version, log or held_out.log, findings, traces
        ),
        "--held-out-severity",
        str(severity),
    ]


def _coverage_table(out: str, section: str) -> dict[tuple[str, str], tuple[int, int, int]]:
    """Holds, traced and retired per row of one section's table: a band's own row
    keyed `(band, "")`, and each detection type beneath it `(band, type)` (D192)."""
    lines = out[out.index(f"{section}: coverage by severity") :].splitlines()
    start = lines.index("-" * 34) + 1
    rows: dict[tuple[str, str], tuple[int, int, int]] = {}
    band = ""
    for line in lines[start:]:
        if not line:
            break
        label, holds, traced, retired = line.split()
        if not line.startswith(" "):
            band = label
        rows[(band, "" if label == band else label)] = (int(holds), int(traced), int(retired))
    return rows


def _coverage_rows(out: str, section: str) -> dict[str, tuple[int, int, int]]:
    """Each band's holds, traced and retired, as one section printed them."""
    return {band: row for (band, kind), row in _coverage_table(out, section).items() if not kind}


def _section(out: str, section: str) -> str:
    """One section, from its heading to the next section's or the end of the output."""
    heading = f"{section}: coverage by severity"
    start = out.index(heading)
    following = out.find("set: coverage by severity", start + len(heading))
    return out[start : following if following >= 0 else len(out)]


def test_coverage_would_notice_its_design_section_miscounted(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The design section over the committed reference log and severity export, per
    band, with the uncovered, the missed and the unbanded named (D157, D187, D188).

    F-76 is the critical finding no entry is traced to; F-85 is the judged miss
    `RECORDED_MISS` pins; F-54 is question-tier and retired all the same.
    """
    code = main(["coverage"])
    captured = capsys.readouterr()
    assert code == 0, captured.err[-800:]
    assert _coverage_rows(captured.out, "design set") == {
        "critical": (4, 3, 3),
        "high": (14, 14, 14),
        "medium": (28, 27, 27),
        "low": (37, 33, 32),
    }, captured.out[:3000]
    section = _section(captured.out, "design set")
    uncovered = section[section.index("uncovered -- ") : section.index("missed -- ")]
    assert "critical   F-76\n" in uncovered, uncovered
    assert "medium     F-90\n" in uncovered, uncovered
    assert "low        F-60, F-55, F-89, F-42\n" in uncovered, uncovered
    assert "low        F-85 (J-policy-alignment: silent)" in section, section
    assert "no band: 7 finding(s) question-tier" in section, section
    assert "  retired    F-54\n" in section, section
    assert "no band: 0 finding(s) unplaced" in section, section
    assert "held-out set: not computed" in captured.out
    # Split by who could detect each finding (D192): every assert-type finding the
    # rubric aims at is retired, and the uncovered and the missed are judge-type.
    table = _coverage_table(captured.out, "design set")
    assert table[("critical", "assert")] == (3, 3, 3), table
    assert table[("critical", "judge")] == (1, 0, 0), table
    assert table[("low", "judge")] == (18, 14, 13), table
    assert all(table[(band, "human")] == (0, 0, 0) for band in BAND_ORDER), table


def test_coverage_would_notice_its_held_out_section_left_out(
    renamed_held_out: _RenamedSet,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """With all six held-out inputs, a held-out section beside the design one, banded by
    its own severity export and read against its own traces, and never pooled (D177,
    D188).

    The invented held-out set is the design set under new ids with F-04 left untraced,
    so its figures are the design set's except that one critical finding moves from
    retired to uncovered, and no design id appears in it.
    """
    monkeypatch.setattr(cli, "_HELDOUT_SET", str(renamed_held_out.declared))
    findings, traces, severity = _renamed_labels(tmp_path, renamed_held_out.renamed)
    code = main(_coverage_args(renamed_held_out, findings, traces, severity))
    captured = capsys.readouterr()
    assert code == 0, captured.err[-800:]
    assert _coverage_rows(captured.out, "design set")["critical"] == (4, 3, 3)
    assert _coverage_rows(captured.out, "held-out set") == {
        "critical": (4, 2, 2),
        "high": (14, 14, 14),
        "medium": (28, 27, 27),
        "low": (37, 33, 32),
    }, captured.out[-4000:]
    section = _section(captured.out, "held-out set")
    uncovered = section[section.index("uncovered -- ") : section.index("missed -- ")]
    assert "HF-04" in uncovered and "HF-76" in uncovered, uncovered
    assert "HF-85 (J-policy-alignment: silent)" in section, section
    assert not re.search(r"(?<!H)F-\d", section), "a design id is in the held-out section"
    # HF-04 is assert-type, so the finding left untraced moves out of the critical
    # band's assert part and leaves its judge part as the design set's (D192).
    table = _coverage_table(captured.out, "held-out set")
    assert table[("critical", "assert")] == (3, 2, 2), table
    assert table[("critical", "judge")] == (1, 0, 0), table


def test_coverage_would_notice_held_out_inputs_given_in_part(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Five of the six held-out inputs, the severity export left out, are refused naming
    it before anything is read (D175, D188)."""
    args = _held_out_args(
        tmp_path / "transcripts",
        tmp_path / "CORPUS_VERSION",
        tmp_path / "held-out.jsonl",
        tmp_path / "findings.yaml",
        tmp_path / "traces.yaml",
    )
    code = main(["coverage", *args])
    err = capsys.readouterr().err
    assert code == 2, err
    assert "--held-out-severity is missing" in err, err


def test_coverage_would_notice_a_held_out_input_inside_the_checkout(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A held-out severity export inside this checkout is refused before anything is read
    (D174, D188). The one inside is this repository's own design export."""
    args = _held_out_args(
        tmp_path / "transcripts",
        tmp_path / "CORPUS_VERSION",
        tmp_path / "held-out.jsonl",
        tmp_path / "findings.yaml",
        tmp_path / "traces.yaml",
    )
    code = main(["coverage", *args, "--held-out-severity", "corpus/findings.severity.json"])
    err = capsys.readouterr().err
    assert code == 2, err
    assert "--held-out-severity corpus" in err, err
    assert "would read them from inside" in err, err


def test_coverage_would_notice_a_severity_file_its_join_refuses(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A severity export that no longer names a defect-tier finding is refused by the
    join rather than covered with that finding left out of every band (D188).

    F-44 anchors no cut and sits between none, so dropping its row leaves a file the
    loader accepts, and only the join can see what is missing.
    """
    export = json.loads((REPO_ROOT / "corpus" / "findings.severity.json").read_text("utf-8"))
    export["severities"] = [row for row in export["severities"] if row["id"] != "F-44"]
    severity = tmp_path / "severity.json"
    severity.write_text(json.dumps(export), encoding="utf-8", newline="\n")
    code = main(["coverage", "--severity", str(severity)])
    err = capsys.readouterr().err
    assert code == 2, err
    assert "appear in neither 'severities' nor 'unplaced': F-44" in err, err


def test_coverage_would_notice_a_findings_file_edited_after_scoring(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A findings file whose finding was edited after its band was placed is refused by
    the command, naming the finding, rather than covered under a band on text nobody
    compared (D140, D189)."""
    edited = tuple(
        replace(finding, consequence=finding.consequence + " Edited after scoring.")
        if finding.id == "F-76"
        else finding
        for finding in load_findings(REPO_ROOT / "corpus" / "findings.yaml")
    )
    findings = tmp_path / "findings.yaml"
    findings.write_text(dump_findings(edited), encoding="utf-8", newline="\n")
    code = main(["coverage", "--findings", str(findings)])
    err = capsys.readouterr().err
    assert code == 2, err
    assert "placed on text that has changed since it was scored: F-76" in err, err


def test_coverage_would_notice_a_finding_on_a_call_its_set_does_not_read(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Design transcripts missing a call the findings sit on are refused, rather than
    covered with that call's findings counted as never caught (D188)."""
    transcripts = tmp_path / "transcripts"
    shutil.copytree(REPO_ROOT / "corpus" / "transcripts", transcripts)
    (transcripts / "CALL-18.txt").unlink()
    code = main(["coverage", "--transcripts", str(transcripts)])
    err = capsys.readouterr().err
    assert code == 2, err
    assert "findings sit on call(s) this set does not read: CALL-18" in err, err


def test_coverage_would_notice_each_refusal_it_shares_with_agreement(
    renamed_held_out: _RenamedSet,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Coverage reads the replays and the labels agreement reads, so it refuses what
    agreement refuses of them (D175, D188): design calls HELDOUT_SET declares, held-out
    transcripts holding a call it does not, a held-out log naming no manifest, labels
    naming another frozen commit, and a replay that stopped part-way."""
    findings, traces, severity = _renamed_labels(tmp_path, renamed_held_out.renamed)

    def refused(args: list[str], expected: str) -> None:
        code = main(args)
        err = capsys.readouterr().err
        assert code == 2, err[-800:]
        assert expected in err, err[-800:]

    declares_a_design_call = tmp_path / "DESIGN_CALL_HELDOUT_SET"
    declares_a_design_call.write_text("CALL-01\n", encoding="utf-8", newline="\n")
    monkeypatch.setattr(cli, "_HELDOUT_SET", str(declares_a_design_call))
    refused(["coverage"], "so the design section would score held-out calls")

    monkeypatch.setattr(cli, "_HELDOUT_SET", str(renamed_held_out.declared))
    mixed = tmp_path / "mixed"
    shutil.copytree(renamed_held_out.transcripts, mixed)
    shutil.copy(REPO_ROOT / "corpus" / "transcripts" / "CALL-09.txt", mixed)
    args = _coverage_args(renamed_held_out, findings, traces, severity)
    refused(
        [*args, "--held-out-transcripts", str(mixed)],
        "are not declared in HELDOUT_SET, so they are not the held-out set",
    )

    lines = renamed_held_out.log.read_text(encoding="utf-8").splitlines(keepends=True)
    header = json.loads(lines[0])
    del header["labels_manifest"]
    unsealed = tmp_path / "unsealed.jsonl"
    unsealed.write_text(json.dumps(header) + "\n" + "".join(lines[1:]), "utf-8", newline="")
    refused(
        _coverage_args(renamed_held_out, findings, traces, severity, log=unsealed),
        "names no labels manifest",
    )

    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    findings, traces, severity = _renamed_labels(
        elsewhere, renamed_held_out.renamed, **{"rubric-frozen-v1": "0" * 40}
    )
    refused(_coverage_args(renamed_held_out, findings, traces, severity), "names rubric-frozen-v1")

    reference = (REPO_ROOT / "runs" / "reference-corpus-0.6.0.jsonl").read_text("utf-8")
    cut = tmp_path / "cut.jsonl"
    halves = reference.splitlines(keepends=True)
    cut.write_text("".join(halves[: len(halves) // 2]), encoding="utf-8", newline="")
    refused(["coverage", "--run-log", str(cut)], "stopped part-way")


def test_coverage_would_notice_an_out_flag_that_writes_a_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Stdout only, as agreement's held-out section is (D175, D188): the parser refuses
    `--out`, and nothing is written where it pointed."""
    destination = tmp_path / "coverage.txt"
    with pytest.raises(SystemExit) as refused:
        main(["coverage", "--out", str(destination)])
    assert refused.value.code == 2
    assert "unrecognized arguments: --out" in capsys.readouterr().err
    assert not destination.exists()


def test_agreement_and_coverage_refuse_a_held_out_log_judged_under_another_rubric(
    renamed_held_out: _RenamedSet,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The rubric hash is what says a log's answers and a set's labels belong together
    (D186), and the two commands that score the labels were the two that never compared
    it: `check_rubric_hash` runs on `harness run`'s replay and on a resume, and neither
    of these replays through either (the phase-5 audit's P5-5, D197).

    Refused with no override, as D186 chose, and both halves are driven: a log naming
    another rubric's hash and one naming none. The log as recorded still computes.
    """
    monkeypatch.setattr(cli, "_HELDOUT_SET", str(renamed_held_out.declared))
    findings, traces, severity = _renamed_labels(tmp_path, renamed_held_out.renamed)
    lines = renamed_held_out.log.read_text(encoding="utf-8").splitlines(keepends=True)

    def re_headed(name: str, hashed: str | None) -> Path:
        header = json.loads(lines[0])
        if hashed is None:
            header.pop("rubric_hash", None)
        else:
            header["rubric_hash"] = hashed
        path = tmp_path / name
        path.write_text(json.dumps(header) + "\n" + "".join(lines[1:]), "utf-8", newline="")
        return path

    for log, expected in (
        (re_headed("another.jsonl", "0" * 64), "judged under rubric hash 0000000000000000"),
        (re_headed("none.jsonl", None), "judged under rubric hash none"),
    ):
        for args in (
            [
                "agreement",
                *_held_out_args(
                    renamed_held_out.transcripts, renamed_held_out.version, log, findings, traces
                ),
            ],
            _coverage_args(renamed_held_out, findings, traces, severity, log=log),
        ):
            code = main(args)
            err = capsys.readouterr().err
            assert code == 2, err[-800:]
            assert expected in err, err[-800:]
            assert "scored against answers given under another rubric" in err, err[-800:]

    assert main(_coverage_args(renamed_held_out, findings, traces, severity)) == 0
    assert "held-out set: coverage by severity" in capsys.readouterr().out


def test_the_log_reading_commands_refuse_a_damaged_header_and_offer_no_flag_they_lack(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Two halves of the phase-5 audit's P5-16, over the committed reference log.

    A header missing a field left `harness agreement`, `harness coverage` and `harness
    report` ending in a traceback and exit 1, which is the code for a failed gate; each
    now refuses by name with exit 2. And replay's staleness refusal ends by offering
    `--allow-stale-replay`, which the two measurement commands do not take -- passing it
    to them is an argument error -- so they say what a reader can actually do, as D168
    had the resume say.
    """
    lines = (
        (REPO_ROOT / "runs" / "reference-corpus-0.6.0.jsonl")
        .read_text(encoding="utf-8")
        .splitlines(keepends=True)
    )

    def re_headed(name: str, **changes: object) -> Path:
        header = json.loads(lines[0])
        for key, value in changes.items():
            if value is None:
                del header[key]
            else:
                header[key] = value
        path = tmp_path / name
        path.write_text(json.dumps(header) + "\n" + "".join(lines[1:]), "utf-8", newline="")
        return path

    damaged = re_headed("damaged.jsonl", artifact_hash=None)
    for command in ("agreement", "coverage", "report"):
        code = main([command, "--run-log", str(damaged)])
        err = capsys.readouterr().err
        assert code == 2, err[-400:]
        assert "carries no artifact_hash" in err, err[-400:]

    stale = re_headed("stale.jsonl", rubric_version="99")
    for command in ("agreement", "coverage"):
        code = main([command, "--run-log", str(stale)])
        err = capsys.readouterr().err
        assert code == 2, err[-400:]
        assert "--allow-stale-replay" not in err, err[-400:]
        assert "point --run-log at a log recorded under this state" in err, err[-400:]


def test_agreement_and_coverage_read_the_held_out_policies_they_are_given(
    renamed_held_out: _RenamedSet,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--held-out-policies` is the one held-out input with a default -- the design
    set's policies, which the present held-out calls read -- and no test passed it on
    either command until the phase-5 audit's P5-6, so the flag could have stopped being
    read with nothing red.

    Driven both ways: the design policies given explicitly compute the same section the
    default does, and a directory holding none is refused.
    """
    monkeypatch.setattr(cli, "_HELDOUT_SET", str(renamed_held_out.declared))
    findings, traces, severity = _renamed_labels(tmp_path, renamed_held_out.renamed)
    design_policies = str(REPO_ROOT / "corpus" / "policies")
    empty = tmp_path / "no-policies"
    empty.mkdir()

    for args in (
        [
            "agreement",
            *_held_out_args(
                renamed_held_out.transcripts,
                renamed_held_out.version,
                renamed_held_out.log,
                findings,
                traces,
            ),
        ],
        _coverage_args(renamed_held_out, findings, traces, severity),
    ):
        assert main([*args, "--held-out-policies", design_policies]) == 0
        assert "held-out set" in capsys.readouterr().out

        code = main([*args, "--held-out-policies", str(empty)])
        err = capsys.readouterr().err
        assert code == 2, err[-400:]
        assert "polic" in err, err[-400:]
