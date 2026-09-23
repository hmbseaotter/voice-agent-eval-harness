"""The report for two audiences, its labels, its escaping and its snapshots (P4).

Several of these exist because the specification's own criteria did not
distinguish the design from its inversion until D130 added the halves they were
missing -- the two-audience deliverable carried no criterion at all, and the
escaping criterion was satisfied by a renderer that deleted the characters.
"""

from __future__ import annotations

import functools
import inspect
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Final, NoReturn

import pytest
import yaml

from harness.checks import build_registry
from harness.cli import _judged_rollup_lines, main
from harness.core.artifact import build_payload, content_hash
from harness.core.context import build_context
from harness.core.engine import roll_up, run
from harness.core.findings import Finding, load_findings
from harness.core.registry import ResultBuilder
from harness.core.result import Provenance
from harness.core.rubric import CheckTier, Rubric, load_rubric
from harness.corpus.policies import load_policies
from harness.corpus.text_adapter import parse_call
from harness.judge.engine import JudgedOutcome
from harness.judge.rollup import JudgedEntryRollup, roll_up_judged
from harness.report import (
    AUDIENCES,
    NON_DETERMINISM_CAVEAT,
    _judged_distributions,
    _judged_table,
    audience_entries,
    escape_cell,
    render_tier_a,
    unescape_cell,
)

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
SNAPSHOT: Final[Path] = REPO_ROOT / "snapshots" / "report.md"
WORKFLOW: Final[Path] = REPO_ROOT / ".github" / "workflows" / "checks.yml"


def _findings() -> dict[str, Finding]:
    return {
        finding.id: finding for finding in load_findings(REPO_ROOT / "corpus" / "findings.yaml")
    }


def _rubric() -> Rubric:
    return load_rubric(REPO_ROOT / "rubric.yaml", build_registry().keys())


def _report_text() -> str:
    """The committed snapshot, or a skip saying how to make one.

    Skipped rather than failed while it is absent, for the reason
    `test_a_reference_log_is_committed` gives about the run log: the artifact is
    produced by a command, and a suite that fails for want of it would fail on
    a fresh clone before anything had been run. The half that fails is
    `test_a_report_snapshot_is_committed`.

    **Read only by the tests whose subject is the artifact** -- the snapshot's
    existence, and its byte-identity against a fresh render. Everything that
    asserts a *property of the report* reads `_rendered_report()` instead, and
    D151 is why.
    """
    if not SNAPSHOT.exists():
        pytest.skip("no committed report snapshot; write one with `harness report --out`")
    return SNAPSHOT.read_text(encoding="utf-8")


@functools.lru_cache(maxsize=1)
def _rendered_report() -> str:
    """The report as the shipped renderer produces it now.

    **The shape tests read the committed snapshot until D151, and that made
    their controls blind.** A mutation to `src/harness/report.py` cannot change
    a file on disk, so restoring a real defect -- moving the non-determinism
    caveat into a footer, collapsing the orthogonal label axes -- left every
    test that asserted those properties green. The sweep reported both controls
    as measuring nothing and was right.

    The defect was not escaping the suite. The byte-identity test regenerates
    the report and compares it against the snapshot, so it went red. That is
    the failure mode this project names *a criterion ticked against its
    neighbor* -- the control is registered against one test and the defect is
    caught by another, so the named test's evidence is somebody else's.

    Rendered once per session and cached: the command is a subprocess over the
    whole corpus in replay mode, and six tests asking for it separately would
    pay for it six times.
    """
    produced = subprocess.run(
        [sys.executable, "-m", "harness.cli", "report"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert produced.returncode == 0, (
        "the report command failed, so no property of its output can be asserted:\n"
        + produced.stderr[-2000:]
    )
    return produced.stdout


# --------------------------------------------------------------------------
# Escaping: the model's text survives the table it is rendered into
# --------------------------------------------------------------------------


def test_a_pipe_and_a_newline_render_without_corrupting_the_table() -> None:
    """The criterion as the specification words it.

    A Markdown table row is delimited by pipes and terminated by a newline, so
    model-authored text containing either would silently split one row into two
    or one cell into three -- with the verdict landing under the wrong heading
    and nothing saying so.
    """
    rendered = escape_cell("the agent said | then\nstopped")
    assert "|" not in rendered.replace("\\|", "")
    assert "\n" not in rendered


def test_the_escaped_text_still_carries_what_it_escaped() -> None:
    """The half D130 added, and the one the criterion above cannot buy.

    A renderer that deleted every pipe and newline satisfies "renders without
    corrupting the report table" and destroys the rationale a reader is being
    shown. The requirement's verb is *escape*, and escape means recoverable --
    so the round trip is asserted rather than the absence of a character.
    """
    for original in (
        "the agent said | then\nstopped",
        "a backslash \\ and a pipe |",
        "\\| already escaped-looking",
        "trailing backslash \\",
        "carriage\r\nreturn",
    ):
        assert unescape_cell(escape_cell(original)) == original.replace("\r\n", "\n"), original


def test_escaping_is_injective_so_two_rationales_cannot_render_the_same() -> None:
    """The property that makes the round trip possible rather than lucky.

    A scheme mapping both `|` and `\\|` onto `\\|` would round-trip one of them
    and corrupt the other, and the corruption would be invisible: the table
    still renders. Backslash is escaped first for exactly this reason.
    """
    originals = ["a|b", "a\\|b", "a\\\\|b", "a\nb", "a\\nb"]
    assert len({escape_cell(text) for text in originals}) == len(originals)


# --------------------------------------------------------------------------
# Two audiences, routed by owner
# --------------------------------------------------------------------------


def test_every_entry_is_routed_to_an_audience_by_the_owner_of_what_it_traces() -> None:
    """The deliverable that carried no criterion until D130.

    Asserted on **which entries land in which section**, not on the sections
    existing: a report emitting two headings and putting every entry under the
    first satisfies "the report has two audiences" and routes nothing.
    """
    rubric = _rubric()
    findings = _findings()
    routed = {
        title: {entry.id for entry in audience_entries(rubric, findings, owners)}
        for title, _, owners in AUDIENCES
    }
    assert all(routed.values()), f"an audience holds no entry at all: {routed}"

    covered = set().union(*routed.values())
    declared = {entry.id for entry in rubric.entries}
    assert covered == declared, (
        "entries in no audience section, so a reader of either would not see them: "
        f"{sorted(declared - covered)}"
    )


def test_an_entry_tracing_findings_on_two_desks_appears_in_both_sections() -> None:
    """D43's whole argument, made checkable.

    "A row bundling a platform defect with an agent defect is actionable by
    nobody" -- and an entry tracing one of each is actionable by both. Routing
    it to a single section by majority would hand half of it to the wrong desk,
    silently, and the shipped rubric contains two such entries.
    """
    rubric = _rubric()
    findings = _findings()
    routed = [
        {entry.id for entry in audience_entries(rubric, findings, owners)}
        for _, _, owners in AUDIENCES
    ]
    both = set.intersection(*routed)
    assert both, (
        "no entry appears in both audience sections, so this asserts nothing about "
        "membership routing. The shipped rubric has entries tracing an agent finding and a "
        "platform finding; if that stopped being true, say so here."
    )


# --------------------------------------------------------------------------
# The rendered report: labels, the caveat, and the judged numbers
# --------------------------------------------------------------------------


def test_the_report_carries_both_audience_sections_with_their_entries() -> None:
    text = _rendered_report()
    for title, _, owners in AUDIENCES:
        assert f"## {title}" in text, f"the report has no {title!r} section"
        entries = audience_entries(_rubric(), _findings(), owners)
        assert entries
        section = text.split(f"## {title}", 1)[1].split("\n## ", 1)[0]
        present = [entry.id for entry in entries if f"`{entry.id}`" in section]
        assert present, f"the {title!r} section names none of the entries routed to it"


def test_a_call_that_failed_in_more_than_one_way_carries_orthogonal_labels() -> None:
    """Taxonomy 34, applied to this report rather than only to a system under test.

    "One value cannot express an interaction that failed in several independent
    ways", and the disposition is explicit that the recommendation is one the
    harness's own report must follow. So the call table's row is three
    independent axes -- what was found, what was not evaluated, which owners
    must act -- and a call with entries in more than one of them is what proves
    they are independent rather than three renderings of one label.
    """
    text = _rendered_report()
    section = text.split("## Calls", 1)[1].split("\n## ", 1)[0]
    rows = [line for line in section.splitlines() if line.startswith("| CALL-")]
    assert rows, "the report has no per-call rows"

    def cells(row: str) -> list[str]:
        return [cell.strip() for cell in row.strip().strip("|").split("|")]

    assert all(len(cells(row)) == 4 for row in rows), "a call row is not four columns"
    multi = [
        row
        for row in rows
        if cells(row)[1] not in {"nothing", ""} and cells(row)[2] not in {"everything applied", ""}
    ]
    assert multi, (
        "no call has both a finding and something that could not be evaluated, so the two "
        "axes are never observed to be independent"
    )
    two_desks = [row for row in rows if "," in cells(row)[3]]
    assert two_desks, "no call names more than one owner, so the third axis asserts nothing"


def test_the_non_determinism_caveat_is_inline_above_the_numbers_it_qualifies() -> None:
    """Asserted on **position**, not on presence.

    A caveat a reader meets after the number it qualifies has already failed,
    and one in a footer is a caveat about numbers the reader has already
    believed. So this compares offsets: the caveat has to come before the
    judged table and after the judged heading.
    """
    text = _rendered_report()
    caveat = text.index(NON_DETERMINISM_CAVEAT[:60])
    heading = text.index("## Judged tier")
    table = text.index("| entry | model | gate |")
    assert heading < caveat < table, (
        "the non-determinism caveat is not between the judged heading and the judged table"
    )


def test_every_rate_gated_judged_dimension_reports_its_four_other_counts() -> None:
    """The criterion, scoped to the tier D130 said it had to be.

    The deterministic breakdown has printed all five counts since P2, so a
    criterion that does not name the tier goes green off a tier that was
    already there. This reads the **judged** table.
    """
    text = _rendered_report()
    section = text.split("## Judged tier", 1)[1].split("\n## ", 1)[0]
    header = next(line for line in section.splitlines() if line.startswith("| entry | model |"))
    for column in ("rate", "applicable", "n/a", "unevaluable", "errored", "refused"):
        assert f"| {column} " in header or f" {column} |" in header, (
            f"the judged table has no {column!r} column: {header}"
        )
    # **The section holds two tables and this criterion is about the first.**
    # Selecting on `| \`J-` caught both: the summary carries one row per entry
    # with nine columns, and the per-call table below it carries 112 rows of
    # four. The filter matched all 119 and the width assertion failed on the
    # wrong population -- visible only once a snapshot existed for this test to
    # run against at all, which is the half of D130's split that had never
    # executed.
    lines = section.splitlines()
    start = lines.index(header) + 2  # the header, then its separator row
    rows: list[str] = []
    for line in lines[start:]:
        if not line.startswith("| `J-"):
            break
        rows.append(line)
    assert rows, "the judged summary table has no entry rows"
    assert all(len(row.strip().strip("|").split("|")) == 9 for row in rows), (
        "a judged row does not carry the rate and its four accompanying counts"
    )


def test_a_judged_dimension_is_reported_as_a_distribution_in_the_report() -> None:
    text = _rendered_report()
    section = text.split("### Verdict distributions", 1)[1].split("\n## ", 1)[0]
    assert re.search(r"\| \w+ x\d+", section), (
        "no per-call row carries a count against a verdict, so the report shows verdicts "
        "rather than distributions"
    )


# --------------------------------------------------------------------------
# What the phase-4 audit found these tests could not see (D158)
# --------------------------------------------------------------------------


def _mixed_call() -> JudgedEntryRollup:
    """One call on which nine repetitions returned the negative pole and the tenth errored.

    The shape D154's first recording produced -- one truncation among ten -- rolled
    up through the shipped roll-up rather than written as a row by hand.
    """
    entry = _rubric().by_id("J-concerns-addressed")
    builder = ResultBuilder(
        entry=entry, call_id="CALL-08", provenance=Provenance("1", "0.6.0", "a" * 64)
    )
    outcomes = [
        JudgedOutcome(
            result=builder.applicable(entry.negative, ("[T1] caller: something", "rationale")),
            repetition=repetition,
            request_hash="h",
            stop_reason="end_turn",
            informed_retries=0,
        )
        for repetition in range(1, 10)
    ]
    outcomes.append(
        JudgedOutcome(
            result=builder.errored("the answer stopped at max_tokens"),
            repetition=10,
            request_hash="h",
            stop_reason="max_tokens",
            informed_retries=0,
        )
    )
    return roll_up_judged(outcomes, [entry])[0]


def _cells(row: str) -> list[str]:
    return [cell.strip() for cell in row.strip().strip("|").split("|")]


def test_the_judged_tables_would_notice_an_errored_repetition_among_verdicts() -> None:
    """P4-1. The call has a modal verdict, so it is applicable and in the rate -- and
    its errored repetition is still a result that could not be obtained. The status
    columns counted calls whose repetitions were all of one status, so they counted
    it nowhere, and nothing read their values: the committed log records no errored
    result, so a table printing 0 in that column passed this whole module, the
    snapshot included (D158).

    Asserted on the values both renderers print, not on the column names.
    """
    rollup = _mixed_call()
    assert rollup.applicable == 1
    header, _, row = _judged_table([rollup])
    printed = dict(zip(_cells(header), _cells(row), strict=True))
    assert printed["applicable (calls)"] == "1", printed
    assert printed["errored (results)"] == "1", printed

    entry_row = next(
        line for line in _judged_rollup_lines([rollup]) if line.startswith(rollup.entry.id)
    )
    # entry, gate, rate, app, n/a, unev, err, ref, result
    assert entry_row.split()[6] == "1", entry_row


def test_a_call_row_would_notice_its_errored_repetition_dropped_beside_its_verdicts() -> None:
    """P4-1's other half. Both renderers printed a call's statuses only when it had
    no verdict at all, each from its own copy of that rule, so the call's row showed
    nine verdicts and hid the tenth result. They print one function's text now (D158).
    """
    rollup = _mixed_call()
    distribution = _judged_distributions([rollup])[2]
    assert f"{rollup.entry.negative} x9" in distribution, distribution
    assert "errored x1" in distribution, distribution

    call_line = next(line for line in _judged_rollup_lines([rollup]) if "CALL-08" in line)
    assert "errored x1" in call_line, call_line


def test_the_audience_sections_would_notice_an_entry_rendered_on_the_wrong_desk() -> None:
    """P4-2. Routing was asserted on the routing function, and the rendered sections
    only for naming *at least one* routed entry -- so a renderer that put every entry
    in both sections passed all three tests the criterion named, and only the
    snapshot saw it: D151's shape, one criterion over.

    Asserted on the rendered report, in both directions: a section names every entry
    routed to it and none that is not.
    """
    text = _rendered_report()
    rubric = _rubric()
    findings = _findings()
    for title, _, owners in AUDIENCES:
        section = text.split(f"## {title}", 1)[1].split("\n## ", 1)[0]
        rendered = set(re.findall(r"`([AJ]-[A-Za-z0-9-]+)`", section))
        routed = {entry.id for entry in audience_entries(rubric, findings, owners)}
        assert rendered == routed, (
            f"the {title!r} section renders {sorted(rendered - routed)} it was not routed "
            f"and omits {sorted(routed - rendered)} it was"
        )


def test_the_calls_table_would_notice_a_judged_entry_found_on_a_minority_of_repetitions() -> None:
    """P4-8. The Calls table counted a judged entry as found when any repetition
    returned the negative pole, while the gate and both judged tables read the modal
    verdict, so the snapshot listed `J-call-synthesis` as found on CALL-07 above a
    distribution row giving the opposite verdict (D158).

    Read in both directions over the rendered report: a judged entry is under a
    call's "what was found" exactly when its modal verdict there is one the entry
    counts against its gate -- the negative pole, or a verdict it declares beside the
    pole (D160). It read the pole alone until D160, which turned it red on the first
    entry to declare more while the report itself was right: the rule restated
    beside the check, caught by the suite.
    """
    text = _rendered_report()
    violating = {entry.id: entry.violating for entry in _rubric().entries}

    calls = text.split("## Calls", 1)[1].split("\n## ", 1)[0]
    found: set[tuple[str, str]] = set()
    for line in calls.splitlines():
        if line.startswith("| CALL-"):
            call_id, found_cell, _, _ = _cells(line)
            found |= {
                (item.strip(), call_id)
                for item in found_cell.split(",")
                if item.strip().startswith("J-")
            }

    distributions = text.split("### Verdict distributions", 1)[1].split("\n## ", 1)[0]
    rows = re.findall(
        r"^\| `(J-[A-Za-z0-9-]+)` \| (CALL-\d+) \| ([a-z_]+|--) \|",
        distributions,
        re.MULTILINE,
    )
    assert rows, "no judged distribution row parsed, so this compares nothing"
    fired = {
        (entry_id, call_id) for entry_id, call_id, verdict in rows if verdict in violating[entry_id]
    }
    assert found == fired, (
        f"found without a violating modal verdict: {sorted(found - fired)}; a violating modal "
        f"verdict not found: {sorted(fired - found)}"
    )


# --------------------------------------------------------------------------
# The snapshot, and what makes it a regression rather than a determinism check
# --------------------------------------------------------------------------


def test_a_report_snapshot_is_committed() -> None:
    """The half that fails when the artifact is missing.

    Split from the tests that read it for the reason the reference log's pair
    is split: a suite that failed everywhere for want of a generated artifact
    would say nothing about which one it wanted.
    """
    assert SNAPSHOT.exists(), (
        f"no committed report snapshot at {SNAPSHOT.relative_to(REPO_ROOT)}. Generate it with "
        "`uv run harness report --out snapshots/report.md`."
    )


def test_the_report_matches_the_committed_snapshot_byte_for_byte() -> None:
    """The golden-report regression, against something older than this run.

    **This is the criterion D130 added**, and the difference from the one it
    sits beside is the whole point. "Byte-identical across two consecutive
    replay runs" is a *determinism* assertion: it compares a run against
    itself, and passes on a build whose report changed completely. D8 chose
    replay mode in order to have a **regression** signal -- and its stated
    hazard is somebody running live, seeing a snapshot failure, and
    regenerating the snapshot to make CI green. A self-comparison cannot see
    that, having nothing older than this run to disagree with.
    """
    expected = _report_text()
    produced = subprocess.run(
        [sys.executable, "-m", "harness.cli", "report"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert produced.returncode == 0, produced.stderr[-2000:]
    assert produced.stdout == expected, (
        "the report no longer matches the committed snapshot. If the change is intended, "
        "regenerate it in the same commit and say what moved; if it is not, this is the "
        "regression the snapshot exists to catch."
    )


def test_two_consecutive_replay_reports_are_byte_identical() -> None:
    """The determinism half, which the regression above does not buy.

    A build could produce the same wrong bytes twice. It could also produce
    different bytes twice while matching a snapshot that was regenerated from
    one of them. Neither assertion implies the other.
    """
    runs = [
        subprocess.run(
            [sys.executable, "-m", "harness.cli", "report"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            check=False,
        )
        for _ in range(2)
    ]
    assert all(run.returncode == 0 for run in runs), runs[0].stderr[-2000:]
    assert runs[0].stdout == runs[1].stdout, "two replay reports of one build differ"


def test_the_golden_report_regression_runs_in_ci() -> None:
    """The capability D8 chose replay mode in order to have.

    A guard nothing runs is a guard that holds on the days somebody remembers,
    which is this project's own argument for the CI workflow existing at all.
    """
    document = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    commands = "\n".join(str(step.get("run", "")) for step in document["jobs"]["checks"]["steps"])
    assert "harness report" in commands, "CI does not run the report command"
    assert "snapshots/report.md" in commands, (
        "CI runs the report and does not compare it against the committed snapshot, so the "
        "step proves the command exits zero and nothing about what it produced"
    )


def test_the_report_is_produced_on_a_clone_with_no_credential_in_reach() -> None:
    """The criterion, run the way a reader would meet it.

    Replay is the default mode so behavior never depends on whether a key
    happens to be in the environment (D8), and this is the assertion that turns
    that from a design statement into a fact: both declared credential
    variables are removed from the subprocess environment.

    **The empty directory it runs from does not put `.env` out of reach**, which
    this docstring used to claim (P4-12). The command resolves its root with
    `_repo_root()`, which is this checkout, and would read a `.env` there
    whatever the working directory. The assertion holds because the report path
    reads no credential at all, which
    `test_the_report_would_notice_its_path_reading_a_credential` pins (OB-29).
    The suite passing on a machine with a key says nothing on its own, which is
    the hazard that made a phase-3 test pass locally and fail on CI.
    """
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in {"ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"}
    }
    with tempfile.TemporaryDirectory(prefix="report-no-credential-") as scratch:
        produced = subprocess.run(
            [
                sys.executable,
                "-m",
                "harness.cli",
                "report",
                "--rubric",
                str(REPO_ROOT / "rubric.yaml"),
                "--transcripts",
                str(REPO_ROOT / "corpus" / "transcripts"),
                "--policies",
                str(REPO_ROOT / "corpus" / "policies"),
                "--corpus-version-file",
                str(REPO_ROOT / "corpus" / "CORPUS_VERSION"),
                "--findings",
                str(REPO_ROOT / "corpus" / "findings.yaml"),
                "--template",
                str(REPO_ROOT / "prompts" / "judge-dimension.v1.md"),
                "--run-log",
                str(REPO_ROOT / "runs" / "reference-corpus-0.6.0.jsonl"),
            ],
            capture_output=True,
            text=True,
            cwd=scratch,
            env={**environment, "PYTHONPATH": str(REPO_ROOT / "src")},
            check=False,
        )
    assert produced.returncode == 0, produced.stderr[-2000:]
    assert produced.stdout.startswith("# Evaluation report")
    for title, _, _ in AUDIENCES:
        assert f"## {title}" in produced.stdout


def test_the_report_would_notice_its_path_reading_a_credential(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """P4-12. The reason the report needs no credential, pinned rather than stated.

    The subprocess test above said running from a directory holding no `.env` put
    that file out of reach. It did not: the command resolves its root with
    `_repo_root()`, which is this checkout, and reads `.env` there whatever the
    working directory. That test holds because the report path reads no credential
    at all, and this makes that the assertion: both functions the CLI imports and
    `read_dotenv`, the one reader of `.env` they share, raise if called, and the
    report is still produced in full (OB-29).
    """

    def refuse(name: str) -> Callable[..., NoReturn]:
        def refused(*_args: object, **_kwargs: object) -> NoReturn:
            raise AssertionError(f"the report path called {name}, so it reads a credential")

        return refused

    monkeypatch.setattr("harness.cli.resolve_credential", refuse("resolve_credential"))
    monkeypatch.setattr("harness.cli.credential_values", refuse("credential_values"))
    monkeypatch.setattr("harness.core.transport.read_dotenv", refuse("read_dotenv"))
    exit_code = main(
        [
            "report",
            "--rubric",
            str(REPO_ROOT / "rubric.yaml"),
            "--transcripts",
            str(REPO_ROOT / "corpus" / "transcripts"),
            "--policies",
            str(REPO_ROOT / "corpus" / "policies"),
            "--corpus-version-file",
            str(REPO_ROOT / "corpus" / "CORPUS_VERSION"),
            "--findings",
            str(REPO_ROOT / "corpus" / "findings.yaml"),
            "--template",
            str(REPO_ROOT / "prompts" / "judge-dimension.v1.md"),
            "--run-log",
            str(REPO_ROOT / "runs" / "reference-corpus-0.6.0.jsonl"),
        ]
    )
    output = capsys.readouterr().out
    assert exit_code == 0
    assert output.startswith("# Evaluation report")
    for title, _, _ in AUDIENCES:
        assert f"## {title}" in output


def test_the_tier_a_section_is_byte_identical_across_runs_and_across_modes() -> None:
    """The unconditional half of D8's reproducibility split.

    Tier A makes no model call, so its bytes cannot depend on the mode -- and
    that is what makes the *other* half's restriction meaningful. Conflating
    the two is D8's stated hazard: somebody runs live, sees a snapshot failure,
    regenerates it to make CI green, and the regression signal goes with it.

    Asserted by rendering the section directly under both mode labels, because
    a live run is not something a suite may issue.
    """
    rubric = _rubric()
    registry = build_registry()
    corpus_version = (REPO_ROOT / "corpus" / "CORPUS_VERSION").read_text(encoding="utf-8").strip()
    policies = load_policies(REPO_ROOT / "corpus" / "policies")
    contexts = [
        build_context(parse_call(path), policies, policy_tool="fetch_policy")
        for path in sorted((REPO_ROOT / "corpus" / "transcripts").glob("*.txt"))
    ]
    calls = tuple(
        parse_call(path) for path in sorted((REPO_ROOT / "corpus" / "transcripts").glob("*.txt"))
    )
    digest = content_hash(build_payload(calls, corpus_version, REPO_ROOT))
    provenance = Provenance(rubric.version, corpus_version, digest)

    rendered = []
    for _ in range(2):
        report = run(rubric, contexts, provenance, registry, tier=CheckTier.ASSERT)
        rendered.append(render_tier_a(roll_up(report, rubric), report))
    assert rendered[0] == rendered[1], "two deterministic runs render different Tier A sections"
    # **The section takes no mode and cannot.** That is a stronger claim than
    # rendering it twice under two labels: a renderer given a mode could use it
    # tomorrow, and a test that passed both labels today would keep passing
    # while the property it names quietly became conditional.
    assert set(inspect.signature(render_tier_a).parameters) == {"rollups", "report"}, (
        "render_tier_a takes something other than the deterministic results, so its bytes "
        "could depend on the mode after all"
    )
