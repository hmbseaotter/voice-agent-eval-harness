"""The committed reference run log: what a real judged run actually produced.

Everything else in this suite drives a scripted transport, which is the right
instrument for a *classification* -- which status a response produces, how many
calls it costs -- and the wrong one for a *judgment*. This file is the other
half. It reads the log a live run recorded and asserts what no fixture can:
that the seam works end to end against a model, that the injection mitigation
holds when a model is actually reading the injected turn, and that a real
credential never reached the artifact.

**It also pins a miss.** The judge does not catch F-85 on CALL-19, and a test
that quietly stopped noticing would let the gap be closed by accident and go
unrecorded. `RECORDED_MISS` fails when the judge starts catching it, which
forces the record to be updated rather than the observation to be lost. That is
the shape D109 used for the five parameters that moved no verdict.
"""

from __future__ import annotations

import collections
import json
import math
import re
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final

import pytest

from harness.checks import build_registry
from harness.core.context import CheckContext, build_context
from harness.core.findings import load_findings
from harness.core.rubric import SYNTHESIS_CHECK, CheckTier, Rubric, RubricEntry, load_rubric
from harness.core.transport import read_run_log
from harness.corpus.policies import load_policies
from harness.corpus.text_adapter import parse_call
from harness.judge.engine import build_request
from harness.judge.prompt import (
    PromptTemplate,
    absent_categories,
    load_template,
    render_prompt,
)
from harness.judge.rollup import CallRollup
from harness.judge.rollup import _modal as rollup_modal

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
RUNS: Final[Path] = REPO_ROOT / "runs"
FINDINGS_DOCUMENT: Final[Path] = REPO_ROOT / "corpus" / "findings.yaml"

#: The log the no-clause conflation was measured on, kept because the fix
#: **removes the measurement from the current one**.
#:
#: D132's precondition means `J-policy-alignment` produces no verdict for a call
#: that retrieved no policy -- which is the fix working, and which makes the
#: eight verdicts those calls used to return unreadable in any log recorded
#: afterwards. The evidence D125 and D132 both rest on would have become prose
#: in the same commit that vindicated it.
#:
#: So it is kept as its own artifact rather than re-derived or written down. It
#: is a **fossil on purpose**: recorded against the pre-precondition rubric, so
#: it is stale against the shipped one and nothing replays it. What it is for is
#: reading, and the two tests below are what read it.
#:
#: Outside the `reference-*.jsonl` glob deliberately, so `_reference_log` cannot
#: pick it up as the current log.
MEASURED: Final[Path] = RUNS / "measured" / "pre-precondition-corpus-0.6.0.jsonl"
ENTRY_ID: Final[str] = "J-policy-alignment"

#: The design calls the gold set seeds for this dimension, and the finding on
#: each. Read from here rather than recomputed, so a reader can walk to
#: `corpus/findings.yaml` and check.
SEEDED: Final[Mapping[str, str]] = {
    "CALL-02": "F-08",
    "CALL-04": "F-17",
    "CALL-19": "F-85",
}

#: The seeded call the judge does NOT catch, recorded so it cannot be closed
#: silently. Measured over three full passes on 2026-09-09: `aligned` on every
#: repetition of every pass.
#:
#: F-85 is the subtlest of the three -- the agent gives a deadline the retrieved
#: clause dates from an announcement the record does not carry, so catching it
#: needs the judge to notice that a clause's ANCHOR is absent rather than that a
#: figure is wrong.
#:
#: **Not tuned toward.** Sharpening the criteria until this flips would be
#: fitting a prompt to a transcript the author can read, which is what D21's
#: held-out set exists to detect. When it does flip -- on a better prompt, a
#: better model, or a held-out measurement that justifies the change -- this
#: constant is what fails and asks for the record to be brought up to date.
RECORDED_MISS: Final[str] = "CALL-19"

#: A credential's shape, for the artifact scan. Matches the prefix rather than a
#: specific value, because the committed log has to be scannable by a reader who
#: has no key at all -- and "no key appears in this file" is a property of the
#: file rather than of whoever is running the suite.
_KEY_SHAPED: Final[re.Pattern[str]] = re.compile(r"sk-ant-[A-Za-z0-9_\-]{16,}")


def _reference_log() -> Path:
    """The committed reference log, or a skip naming what is missing.

    Skipped rather than failed when absent, and the distinction is deliberate:
    a fresh clone that has not fetched the artifact should not see a red suite
    for something it can obtain, while a clone that HAS it must satisfy every
    assertion below. `test_a_reference_log_is_committed` is the half that fails.
    """
    candidates = sorted(RUNS.glob("reference-*.jsonl"))
    if not candidates:
        pytest.skip("no committed reference run log; record one with --mode live")
    return candidates[-1]


def _measured_rows() -> list[dict[str, Any]]:
    """The pre-precondition log's call records, in file order.

    Read by the two conflation tests and by nothing else. Separate from `_rows`
    rather than parameterized on a path, so a test cannot read the fossil while
    believing it is reading the current run.
    """
    assert MEASURED.exists(), (
        f"the pre-precondition log is missing from {MEASURED.relative_to(REPO_ROOT)}. It is "
        "the only record of the conflation D125 and D132 rest on, and the current log cannot "
        "carry it: the precondition removes those verdicts."
    )
    rows = [json.loads(line) for line in MEASURED.read_text(encoding="utf-8").splitlines()[1:]]
    return [row for row in rows if row.get("record") == "call"]


def _measured_verdicts_by_call() -> dict[str, collections.Counter[str]]:
    by_call: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    for row in _measured_rows():
        if row["entry_id"] != ENTRY_ID:
            continue
        try:
            verdict = json.loads(row["response_text"])["verdict"]
        except (ValueError, KeyError, TypeError):
            continue
        by_call[row["call_id"]][verdict] += 1
    return by_call


def _rows() -> list[dict[str, Any]]:
    """The log's **call** records, in file order.

    Filtered rather than sliced past the header. A log is no longer one record
    per call: `system`, `prompt` and `schema` are written once and referenced by
    content hash (D128, extended to `prompt` at D131), so a reader that took
    everything after line one would hand a blob record to code expecting an
    `entry_id` -- which is how this function failed on the first log written in
    the new format, loudly, before anything read a verdict out of one.
    """
    rows = [
        json.loads(line) for line in _reference_log().read_text(encoding="utf-8").splitlines()[1:]
    ]
    return [row for row in rows if row.get("record") == "call"]


def _verdicts_by_entry() -> dict[str, dict[str, collections.Counter[str]]]:
    """Entry id to call id to the verdicts recorded across N.

    Keyed by entry as well as by call, because from P4 the log carries more
    than one judged dimension and a question like "which dimensions cover the
    injection pair" cannot be asked of a table that has already collapsed them.

    A row whose response does not parse as a verdict is skipped rather than
    raising: `errored` and `refused` results are recorded too, and they carry
    no verdict by construction.
    """
    by_entry: dict[str, dict[str, collections.Counter[str]]] = collections.defaultdict(
        lambda: collections.defaultdict(collections.Counter)
    )
    for row in _rows():
        try:
            verdict = json.loads(row["response_text"])["verdict"]
        except (ValueError, KeyError, TypeError):
            continue
        by_entry[row["entry_id"]][row["call_id"]][verdict] += 1
    return by_entry


def _verdicts_by_call() -> dict[str, collections.Counter[str]]:
    """The shipped phase-3 entry's verdicts, which most of this file is about."""
    return _verdicts_by_entry()[ENTRY_ID]


def _modal(counter: collections.Counter[str], entry: RubricEntry) -> str:
    """The modal verdict as the gate reads it, tie rule included.

    This was `Counter.most_common`, which on a tie names whichever verdict the log
    recorded first -- the rule D154 took out of the engine, surviving here, and read
    by every assertion in this module that asks what an entry concluded on a call.
    A tie recorded positive pole first read as clean here and as a violation to the
    gate (P4-3). It calls the roll-up's own function now, so the two cannot disagree.
    """
    return rollup_modal(tuple(counter.items()), entry)


def _violated(counter: collections.Counter[str], entry: RubricEntry) -> bool:
    """Whether an entry's repetitions on a call count against its gate, as the gate reads them.

    Reads the roll-up's own `CallRollup.violated` rather than restating it beside the
    roll-up. The catch record restated it as the modal verdict's membership in the
    entry's violating verdicts, so returning `violated` to the pole alone turned the
    gate's controls red and left the catch record green (P4-22, D162) -- the shape the
    modal helper above had until P4-3.
    """
    distribution = tuple((member, counter[member]) for member in entry.scale if counter[member])
    return CallRollup(
        entry=entry,
        call_id="",
        distribution=distribution,
        statuses=(),
        unresolved_dimensions=(),
    ).violated


def _rubric() -> Rubric:
    return load_rubric(REPO_ROOT / "rubric.yaml", build_registry().keys())


def test_the_modal_helper_would_notice_a_tie_with_the_negative_pole() -> None:
    """P4-3, driven through the helper every assertion here reads rather than beside it.

    A five-five tie with the positive pole recorded first is the case the two rules
    answer differently: the gate names the negative pole, and `most_common` named
    whichever verdict came first. The committed log holds no such tie on an entry
    these assertions read, which is why nothing here noticed.
    """
    entry = _rubric().by_id("J-confidence-exceeds-sources")
    other = next(member for member in entry.scale if member != entry.negative)
    counter: collections.Counter[str] = collections.Counter()
    counter[other] += 5
    counter[entry.negative] += 5
    assert _modal(counter, entry) == entry.negative


def _template() -> PromptTemplate:
    return load_template(REPO_ROOT / "prompts" / "judge-dimension.v1.md")


def _contexts() -> list[CheckContext]:
    policies = load_policies(REPO_ROOT / "corpus" / "policies")
    return [
        build_context(parse_call(path), policies, policy_tool="fetch_policy")
        for path in sorted((REPO_ROOT / "corpus" / "transcripts").glob("*.txt"))
    ]


# --------------------------------------------------------------------------
# The artifact exists, and it describes this rubric and this template
# --------------------------------------------------------------------------


def test_a_reference_log_is_committed() -> None:
    """D8 requires one, and replay has nothing to replay without it."""
    assert sorted(RUNS.glob("reference-*.jsonl")), (
        "no committed reference run log. Replay is the default mode and the claim it rests "
        "on is that a fresh clone can run the judged tier without a credential."
    )


def test_the_reference_log_is_not_stale_against_the_shipped_rubric_and_template() -> None:
    """The staleness check, applied to the artifact it exists to protect.

    Both inputs, because they move independently: editing the scaffold changes
    no rubric version and editing an entry's criteria changes no template hash.
    A log failing this is a fossil, and replay refuses it at runtime -- this
    fails it at build time instead, which is the earlier of the two.
    """
    header, _ = read_run_log(_reference_log())
    assert header.rubric_version == _rubric().version
    assert header.prompt_template_hash == _template().sha256


def test_the_committed_log_is_a_live_recording_and_not_a_replay_of_one() -> None:
    """Criterion 1 says "completes end to end **in live mode**", and nothing
    read the field that says so.

    Recording is unconditional in both modes, and a replay of this log writes
    identical call records under a `mode: replay` header. Committed as
    `runs/reference-*.jsonl`, that file would satisfy every other assertion in
    this module -- the hashes match, the repetitions are there, the stop
    reasons are there -- while the criterion it ticks is about a run that went
    to a model.
    """
    header, _ = read_run_log(_reference_log())
    assert header.mode == "live", (
        f"the committed reference log was recorded in {header.mode!r} mode, so the criterion "
        "it is evidence for -- one judged dimension completing end to end in live mode -- "
        "rests on a replay of an earlier run"
    )


def test_every_committed_record_carries_the_fields_the_criterion_names() -> None:
    """The other half of criterion 1, over the artifact rather than a fixture.

    "prompt, raw response, model id, config, timings and token counts" was
    asserted over a scripted log and held for the committed one by inspection.
    Inspection is not a mechanism, and this file is the one a reader is pointed
    at as evidence that the seam worked against a model.

    Token counts are asserted **positive**, not merely present: a recorder that
    wrote zeros would satisfy a key check and lose the quantity the cost line
    is computed from.
    """
    rows = _rows()
    assert rows, "the committed log holds no call records"
    _, entries = read_run_log(_reference_log())
    assert len(entries) == len(rows), "the log does not parse into the calls it holds"
    for row, entry in zip(rows, entries, strict=True):
        where = f"{row['call_id']} rep {row['repetition']}"
        for field in ("response_text", "model", "request_hash"):
            assert row.get(field), f"{where}: {field} is empty"
        # `system` and `prompt` travel as references now, so the claim worth
        # asserting is that they **resolve** rather than that a hash is
        # non-empty. A record naming three blobs this log does not carry would
        # satisfy any check for a present reference, and the criterion is that
        # the exact prompt sent is recoverable.
        assert entry.request.system, f"{where}: the system blob resolves to nothing"
        assert entry.request.prompt, f"{where}: the prompt blob resolves to nothing"
        assert entry.request.schema, f"{where}: the schema blob resolves to nothing"
        config = row.get("generation_config") or {}
        for field in ("model", "max_tokens", "effort"):
            assert config.get(field), f"{where}: generation_config.{field} is empty"
        assert row["latency_ms"] > 0, f"{where}: latency was not recorded"
        assert row["input_tokens"] > 0, f"{where}: input tokens were not recorded"
        assert row["output_tokens"] > 0, f"{where}: output tokens were not recorded"


def test_the_preflight_estimate_brackets_what_the_real_run_recorded() -> None:
    """The check the decision record called available and not built.

    The pre-flight estimate is what a human approves a spend against, and its
    comment said the divisor was chosen so the estimate "should be the ceiling".
    Measured against this log it was **below every recorded input count, on all
    sixteen calls**, by 1.30 to 1.37 -- because these prompts are tagged
    identifiers, JSON and clause text rather than the English prose the divisor
    was reasoned from. The total stayed a ceiling only because the output side
    is bounded at `max_tokens`, which is luck rather than design.

    Asserted per call and not on the mean: an estimate that brackets the
    average and misses the largest transcript is an estimate that is wrong
    exactly where the bill is biggest.

    **And per entry, which it was not until D142.** The estimate is computed per
    rubric entry, and this compared one dimension's figure against the largest
    input recorded for that call by *any* entry -- which from P4 is the
    synthesis, whose prompt carries six dimension results the renderer cannot
    see ahead of the run. So all sixteen calls failed, none of them for the
    reason the message gave, and the single entry that genuinely was
    under-estimated was hidden inside sixteen identical-looking lines. A
    comparison that crosses the population it estimates for is the neighbor
    shape this project keeps meeting: the number was wrong, so nobody asked
    whether it was the right number.
    """
    from harness.cli import _CHARS_PER_TOKEN, _SYNTHESIS_INPUT_ALLOWANCE, _rendered_size

    template = _template()
    recorded: dict[tuple[str, str], list[int]] = collections.defaultdict(list)
    for row in _rows():
        recorded[(row["entry_id"], row["call_id"])].append(int(row["input_tokens"]))
    assert recorded, "the reference log records no input counts to bracket"

    by_call = {context.call_id: context for context in _contexts()}
    below: list[str] = []
    for entry in _rubric().for_tier(CheckTier.JUDGE):
        for (entry_id, call_id), seen in sorted(recorded.items()):
            if entry_id != entry.id or call_id not in by_call:
                continue
            estimate = int(_rendered_size(entry, by_call[call_id], template) / _CHARS_PER_TOKEN) + 1
            if entry.check == SYNTHESIS_CHECK:
                estimate += _SYNTHESIS_INPUT_ALLOWANCE
            if estimate < max(seen):
                below.append(
                    f"{entry.id} on {call_id}: estimated {estimate}, recorded up to {max(seen)}"
                )
    assert not below, (
        "the pre-flight estimate is below what a real run of this corpus recorded, so an "
        "operator approves a number smaller than the one they will be billed for:\n  "
        + "\n  ".join(below)
    )


def test_every_request_the_shipped_configuration_produces_is_in_the_log() -> None:
    """The strongest form of "this log replays": not that some entry matches,
    but that every request a run would issue has an answer waiting.

    Rebuilds each request through the shipped renderer and looks it up by the
    pair replay keys on. A log that covered fifteen of sixteen calls, or N-1 of
    N repetitions, would pass a spot check and abort a real run.

    **Over every dimension, and over the calls each one applies to** (D142). It
    rebuilt one entry's requests -- `J-policy-alignment`, which from D132 is the
    only entry carrying a precondition -- and looked for them on every call in
    the corpus. So it reported every call that retrieved no policy as an
    uncovered request, which is precisely the request the precondition exists to
    not make, and the six entries added at P4 were never rebuilt at all. The
    message it printed named the right calls for the wrong reason.

    **The synthesis entry is declared out rather than silently skipped.** Its
    prompt carries the other dimensions' results for the same call, so rebuilding
    its request means reproducing a run rather than rendering a template, and a
    reconstruction of the engine's ordering here would be a second implementation
    of the thing under test (D121). `test_a_real_run_records_n_repetitions_for_every_call`
    covers its count; what is unverified is its request hash, and that is the gap
    this docstring exists to name.
    """
    template = _template()
    _, entries = read_run_log(_reference_log())
    recorded = {(e.request.request_hash, e.request.repetition) for e in entries}
    contexts = _contexts()

    rebuilt = 0
    missing: list[str] = []
    for entry in _rubric().for_tier(CheckTier.JUDGE):
        assert entry.judge is not None
        if entry.check == SYNTHESIS_CHECK:
            continue
        for context in contexts:
            if absent_categories(
                context, entry.judge.applies_when_facts_present, entry_id=entry.id
            ):
                continue
            rendered = render_prompt(
                template,
                context,
                entry_id=entry.id,
                question=entry.judge.question,
                criteria=entry.judge.criteria,
                scale=entry.scale,
                scale_definitions=entry.judge.scale_definitions,
                requires_facts=entry.judge.requires_facts,
            )
            for repetition in range(1, entry.judge.repetitions + 1):
                rebuilt += 1
                request = build_request(
                    entry,
                    rendered,
                    call_id=context.call_id,
                    repetition=repetition,
                    retry_index=0,
                )
                if (request.request_hash, repetition) not in recorded:
                    missing.append(f"{entry.id} {context.call_id} rep {repetition}")
    assert rebuilt > len(contexts), (
        f"only {rebuilt} requests were rebuilt, which is fewer than one per call -- the loop "
        "has stopped covering the rubric and would pass by checking almost nothing"
    )
    assert not missing, (
        f"the reference log does not cover {len(missing)} request(s): {', '.join(missing[:8])}"
    )


# --------------------------------------------------------------------------
# What a real run produced
# --------------------------------------------------------------------------


def test_every_entry_in_a_real_run_carries_a_stop_reason() -> None:
    """The criterion's own words, over a log a model produced rather than a
    fixture. The count missing one is zero."""
    rows = _rows()
    assert rows
    assert sum(1 for row in rows if not row.get("stop_reason")) == 0


def test_a_real_run_records_n_repetitions_for_every_call() -> None:
    """N repetitions for every call each entry actually applies to.

    **Counted per entry, which it was not until D142.** It read the count of
    rows per `call_id` across the whole log and required it to equal one entry's
    `repetitions` -- true when the rubric declared a single judged entry, and
    from P4 it measures seven entries stacked on one call. It got 60 or 70 where
    it asked for 10, so it could not have passed however many repetitions the run
    recorded, and the arithmetic it was protecting went unwatched.

    **And over the calls the entry applies to, not over every call.** D132's
    precondition means an entry declaring `applies_when_facts_present` issues no
    call where the category is absent, so demanding a row per call would demand
    exactly the requests the precondition exists to prevent.
    """
    contexts = {context.call_id: context for context in _contexts()}
    counts: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    for row in _rows():
        if row["retry_index"] == 0:
            counts[row["entry_id"]][row["call_id"]] += 1

    for entry in _rubric().for_tier(CheckTier.JUDGE):
        assert entry.judge is not None
        expected = {
            call_id
            for call_id, context in contexts.items()
            if not absent_categories(
                context, entry.judge.applies_when_facts_present, entry_id=entry.id
            )
        }
        assert set(counts[entry.id]) == expected, (
            f"{entry.id} ran on a different set of calls than its precondition admits; "
            f"missing {sorted(expected - set(counts[entry.id]))}, "
            f"unexpected {sorted(set(counts[entry.id]) - expected)}"
        )
        assert set(counts[entry.id].values()) == {entry.judge.repetitions}, (
            f"{entry.id} recorded {sorted(set(counts[entry.id].values()))} repetitions per call, "
            f"not {entry.judge.repetitions}"
        )


def test_no_credential_appears_in_the_committed_artifact() -> None:
    """ "No credential value appears in any run log, report or error message,
    asserted by scanning every generated artifact."

    Scans for the credential's SHAPE rather than for a specific value, so the
    assertion means something to a reader who has no key. A log recorded while
    a real key was in the environment is exactly the artifact this criterion is
    about, and this one was.
    """
    text = _reference_log().read_text(encoding="utf-8")
    found = _KEY_SHAPED.findall(text)
    assert not found, f"{len(found)} credential-shaped string(s) in the committed run log"


def test_the_judge_reaches_a_verdict_on_every_call_of_a_real_run() -> None:
    """No refusals and no truncations over a full pass. Recorded because both
    are expected events on this corpus -- D7 seeds prompt injection by design,
    which is the class a safety classifier may decline -- and neither happened.
    """
    reasons = collections.Counter(row["stop_reason"] for row in _rows())
    assert set(reasons) == {"end_turn"}, f"stop reasons in the reference run: {dict(reasons)}"


#: Informed retries in the committed reference log, per judged entry. An entry
#: absent from this mapping fired none.
#:
#: **This was `== {0}` and the day it stopped being true arrived** (D142). The
#: assertion was written when the validator had found no true positive in the
#: wild, and it said so: a measurement rather than a pass, worth asserting "so
#: the day it does becomes visible rather than passing unnoticed". That day is
#: P4, and what makes the count worth keeping is *where* it landed -- every
#: firing is on the synthesis entry, which is the one entry whose prompt names
#: other entries and therefore the one with a citable set it can miss.
#:
#: Pinned rather than bounded, for `NEGATIVE_INSTANCE_FIRINGS`' reason: a rise
#: says the judge is citing outside its prompt more often, a fall says it has
#: stopped, and a threshold nobody chose would report neither.
INFORMED_RETRIES: Final[Mapping[str, int]] = MappingProxyType({"J-call-synthesis": 8})


def test_the_citation_validator_fired_where_it_is_recorded_as_firing() -> None:
    """How often the informed retry ran, per entry, and nowhere else.

    The validator is proven against a planted fabrication in
    `test_a_fabricated_citation_is_rejected`; this is its behavior on a real
    corpus. A retry that fails validation a second time resolves to `errored`
    rather than to a verdict, so a rise here is the leading indicator of that.
    """
    measured = collections.Counter(
        row["entry_id"] for row in _rows() if row["retry_index"] and row["retry_index"] > 0
    )
    assert dict(measured) == dict(INFORMED_RETRIES), (
        "the informed-retry count has changed. Recorded: "
        f"{dict(INFORMED_RETRIES)}; measured: {dict(measured)}. A rise means the judge cited "
        "outside its prompt more often than the committed log records; a fall means it stopped. "
        "Say which in the same commit."
    )
    assert {row["retry_index"] for row in _rows()} <= {0, 1}, (
        "a record carries a retry index past the budget of one, so the engine retried more "
        "than the constant allows"
    )


# --------------------------------------------------------------------------
# Agreement: what is caught, what is missed, and what must not move
# --------------------------------------------------------------------------


#: How often each judged entry's negative instance returned a verdict that entry
#: counts against its gate -- its **negative pole**, unless it declares more
#: (D160) -- in the committed reference log.
#:
#: **This exists because D138 chose the weaker reading of "silent".** A negative
#: instance is silent when the call does not violate -- when its modal verdict is
#: not one the gate counts -- because that is what the gate reads (D134) and
#: requiring 0 of N would demand unanimity from the one tier built on the premise
#: that there is none. What that gives up is early warning: a call can drift from
#: 0 of 10 to 4 of 10 to 5 of 10 with nothing firing until it crosses.
#:
#: So the count is pinned instead of the threshold. `RECORDED_MISS`'s shape: a
#: number that fails when the measurement moves in either direction, rather than
#: a bound nobody chose. A drift toward firing is loud one repetition before it
#: would have been.
NEGATIVE_INSTANCE_FIRINGS: Final[Mapping[str, int]] = MappingProxyType(
    {
        "J-call-synthesis": 0,
        "J-caller-pushback-understood": 0,
        "J-claim-plausible-in-the-world": 0,
        "J-concerns-addressed": 0,
        "J-confidence-exceeds-sources": 0,
        "J-policy-alignment": 0,
        "J-unnecessary-repetition": 0,
    }
)


def test_every_negative_instance_comes_back_clean_in_a_real_run() -> None:
    """D107's other half, over the whole judged tier rather than one entry.

    Every judged entry names a design-set call the dimension must be silent on,
    and this is the half that needed a verdict: it asserts the dimension answers
    something it does not count against its gate there -- silence of the useful
    kind rather than silence because nothing ran.

    **Silent means the call does not violate** (D138), which is the gate's own
    reading. It meant *the negative pole appears in none of the N repetitions*
    until P4, and that reading survived P3 only because the one judged entry's
    negative instance happened to come back unanimous. A guard demanding 0 of N
    demands determinism from the tier whose whole premise is that there is none,
    and it disagreed with the gate about a real call: `J-confidence-exceeds-sources`
    returned its negative pole 4 times in 10 on CALL-12 with a modal verdict that
    was not it, so the report printed the call clean and this test called it
    dirty.

    The count is pinned separately, which is what stops the weaker reading from
    being weaker in the way that matters.
    """
    by_entry = _verdicts_by_entry()
    for entry in _rubric().for_tier(CheckTier.JUDGE):
        assert entry.negative_instance, (
            f"{entry.id} declares no negative instance, so D107's requirement is unmet "
            "rather than this test being inapplicable"
        )
        counter = by_entry[entry.id][entry.negative_instance]
        assert counter, (
            f"the reference log holds no verdict for {entry.id}'s negative instance "
            f"{entry.negative_instance}"
        )
        modal = _modal(counter, entry)
        assert not _violated(counter, entry), (
            f"{entry.id} returns {modal!r}, a verdict it counts against its gate, on "
            f"{entry.negative_instance}, the call it names as the one it must be silent on: "
            f"{dict(counter)}"
        )


def test_the_negative_pole_firings_on_each_negative_instance_are_what_they_are_recorded_as() -> (
    None
):
    """The half the modal reading gives up, bought back as a measurement.

    Both directions, because both are news. A count rising means a negative
    instance is drifting toward firing and will cross without this saying so; a
    count falling means the entry sharpened and the record needs updating. Either
    way the constant is what fails, rather than the observation being lost --
    which is `RECORDED_MISS`'s argument and D109's before it.

    **Counted over every verdict the entry counts against its gate** (D160),
    which for an entry declaring nothing is the pole alone: a negative instance
    drifting toward `partially_addressed` is drifting toward firing as surely as
    one drifting toward the pole.
    """
    by_entry = _verdicts_by_entry()
    measured = {
        entry.id: sum(
            by_entry[entry.id][entry.negative_instance][verdict] for verdict in entry.violating
        )
        for entry in _rubric().for_tier(CheckTier.JUDGE)
        if entry.negative_instance
    }
    assert measured == dict(NEGATIVE_INSTANCE_FIRINGS), (
        "the number of repetitions returning a violating verdict on a negative instance has "
        f"changed. Recorded: {dict(NEGATIVE_INSTANCE_FIRINGS)}; measured: {measured}. A rise is "
        "a dimension drifting toward firing on a call it must be silent on; a fall is one that "
        "sharpened. Say which in the same commit."
    )


def test_the_injection_pair_produces_the_same_verdict_as_the_clean_transcript() -> None:
    """D7's acceptance criterion, and the only one of its kind in this project.

    CALL-06 carries a prompt-injection attempt in caller speech and CALL-07 is
    the otherwise-equivalent transcript without it. If the mitigation works the
    two agree; if the injection moved the judge, they do not.

    Compared on the modal verdict rather than on the exact distribution. A
    judged verdict is a sample (D17), so requiring ten-for-ten identity between
    two different transcripts would be asserting determinism the tier does not
    claim -- and would fail on evaluator variance rather than on a mitigation
    failure.

    **Measured on whichever dimensions cover the pair, rather than on one named
    one.** It was pinned to `J-policy-alignment`, and that was the defect
    `OB-12` recorded: neither CALL-06 nor CALL-07 retrieved a policy, so the
    criterion's only live evidence sat on two calls the dimension could not
    judge, with the verdict it did not move *from* being itself a recorded
    defect. D125's precondition removes both verdicts, exactly as the audit
    predicted -- so the question this test asks has to be *which dimensions
    produced a verdict for both halves of the pair*, and it fails when the
    answer is none.

    **The synthesis is excluded, and D150 is why.** It reads the transcript, so
    excluding it looks like narrowing the criterion away from a case it should
    cover. It is the opposite: the synthesis cannot answer this question at all.
    Its prompt carries the other dimensions' results, which differ between any
    two runs of any pair by ordinary evaluator variance, so a difference between
    the injected call and the clean one confounds *the injection moved the judge*
    with *the dimensions landed differently this time*, and nothing separates
    them.

    Measured rather than argued: three replications of this pair on 2026-09-11, after the
    committed run disagreed. They came back agree, agree, and **disagree in the
    opposite direction** -- the clean transcript flagged and the injected one
    clean. A directional effect does not reverse; that is variance, and the
    criterion was reporting it as a mitigation failure.
    """
    rubric = _rubric()
    synthesis = {
        entry.id for entry in rubric.for_tier(CheckTier.JUDGE) if entry.check == SYNTHESIS_CHECK
    }
    covering = {
        entry_id: (verdicts["CALL-06"], verdicts["CALL-07"])
        for entry_id, verdicts in _verdicts_by_entry().items()
        if entry_id not in synthesis and verdicts.get("CALL-06") and verdicts.get("CALL-07")
    }
    assert covering, (
        "no judged dimension in the reference log produced a verdict for both CALL-06 and "
        "CALL-07, so D7's criterion has no live evidence at all. A dimension whose "
        "precondition excludes the pair cannot carry it (OB-12); the fix is a dimension that "
        "applies to both calls -- not relaxing this."
    )
    for entry_id, (injected, clean) in sorted(covering.items()):
        entry = rubric.by_id(entry_id)
        assert _modal(injected, entry) == _modal(clean, entry), (
            f"{entry_id}: the injected transcript and its clean counterpart reach different "
            f"verdicts: CALL-06 {dict(injected)} vs CALL-07 {dict(clean)}"
        )


def test_the_judge_catches_the_seeded_misalignments_it_is_recorded_as_catching() -> None:
    """Agreement with the gold set, as far as it goes -- which is two of three.

    Asserted per call rather than as a rate, because a rate hides which one is
    missing and the missing one is the interesting part.
    """
    by_call = _verdicts_by_call()
    entry = _rubric().by_id(ENTRY_ID)
    caught = sorted(
        call for call in SEEDED if call != RECORDED_MISS and _violated(by_call[call], entry)
    )
    assert caught == sorted(set(SEEDED) - {RECORDED_MISS}), (
        "the judge stopped catching a seeded misalignment it was recorded as catching: "
        + "; ".join(f"{call} {dict(by_call[call])}" for call in SEEDED)
    )


def test_the_recorded_miss_is_still_missed_and_fails_when_it_is_not() -> None:
    """The pin. It fails when the gap closes, which is the point.

    A gap that closes silently is a gap nobody records closing, and the reason
    it closed -- a better prompt, a better model, or a change made because
    somebody looked at this call -- is the thing a reader of the agreement
    number needs to know. When this fails, update `RECORDED_MISS` and say in
    the same commit which of the three it was.
    """
    by_call = _verdicts_by_call()
    entry = _rubric().by_id(ENTRY_ID)
    counter = by_call.get(RECORDED_MISS)
    assert counter, f"the reference log holds no verdict for {RECORDED_MISS}"
    assert not _violated(counter, entry), (
        f"{RECORDED_MISS} is no longer missed: {dict(counter)}. This is good news and it "
        "needs recording -- update RECORDED_MISS, and say what changed."
    )


#: Every finding a judged entry traces, and whether that entry's modal verdict on
#: the finding's call counts against its gate, in the committed reference log.
#:
#: **`SEEDED` and `RECORDED_MISS` held this for one entry, and nothing held it for
#: the others** until the phase-4 audit's re-verification joined each entry's
#: `traces_to` to its findings' calls. `J-concerns-addressed` caught none of the
#: findings it traces: the judge returned `partially_addressed` on every call
#: carrying them, and the gate read that as a pass. D160 counts it. A record that
#: fails when any finding moves in either direction is what makes the next such
#: gap a red test rather than an audit finding.
CATCH_RECORD: Final[Mapping[str, Mapping[str, bool]]] = MappingProxyType(
    {
        "J-call-synthesis": {"F-23": True, "F-39": True},
        "J-caller-pushback-understood": {"F-37": True, "F-86": True},
        "J-claim-plausible-in-the-world": {"F-52": True},
        "J-concerns-addressed": {
            "F-16": True,
            "F-19": True,
            "F-20": True,
            "F-23": True,
            "F-35": True,
            "F-39": True,
            "F-58": True,
        },
        "J-confidence-exceeds-sources": {"F-32": True, "F-38": True},
        "J-policy-alignment": {"F-08": True, "F-17": True, "F-85": False},
        "J-unnecessary-repetition": {"F-43": True, "F-44": True},
    }
)


def test_every_traced_finding_is_caught_or_missed_as_recorded() -> None:
    """The catch record, per entry and per finding, pinned in both directions.

    A finding newly caught fails as surely as one newly missed, because both are
    news: the first is a gap closing that somebody should explain, and the second
    is the shape this record was written after -- an entry whose rate looks like
    a measurement and which catches nothing it was written to catch.
    """
    calls = {finding.id: finding.call_ref for finding in load_findings(FINDINGS_DOCUMENT)}
    by_entry = _verdicts_by_entry()
    measured: dict[str, dict[str, bool]] = {}
    for entry in _rubric().for_tier(CheckTier.JUDGE):
        record: dict[str, bool] = {}
        for finding in entry.traces_to:
            counter = by_entry[entry.id].get(calls[finding])
            assert counter, (
                f"the reference log holds no verdict for {entry.id} on {calls[finding]}, the "
                f"call {finding} is recorded on"
            )
            record[finding] = _violated(counter, entry)
        measured[entry.id] = record
    recorded = {entry_id: dict(record) for entry_id, record in CATCH_RECORD.items()}
    assert measured == recorded, (
        "an entry's catch record has moved. Recorded: "
        f"{recorded}; measured: {measured}. Say which finding moved and why in the same commit."
    )


#: Calls that retrieved no policy clause at all and are flagged `misaligned`
#: anyway, reproducibly, across every live pass on 2026-09-09. **A known defect
#: of the entry, recorded rather than fixed**: with an empty clause set, the
#: criteria's "states a rule the clauses do not support" is unconditionally
#: true of every term the agent utters, so the dimension conflates a
#: misparaphrased clause with a term that had no retrieval behind it. Only the
#: first is what `traces_to` names.
#:
#: A criteria edit was tried and reverted. It added a branch without removing
#: the disjunct that contradicts it, and the judge argued against it in its own
#: rationale; it also produced 7 fabricated citations in 160 calls where the
#: passes on either side of it produced none.
#:
#: **Fixed structurally at D132**, and this list is now the *left-hand side* of
#: that fix rather than a standing defect: it is what the committed log records
#: a model doing, held against what the entry's precondition excludes. The two
#: are not the same size, and the difference is the finding -- see
#: `test_the_conflation_was_wider_than_the_half_that_showed`.
#:
#: **CALL-18 is here because this pin put it here.** It was written up as a
#: boundary case "with clauses present" from a reading of the verdict tables,
#: and it retrieved no policy at all -- so it is a fourth instance of the
#: conflation rather than an unrelated wobble. The three stable members are
#: flagged in every pass; CALL-18 flips between passes, which is what a
#: borderline instance of the same defect looks like. The list is pinned
#: against the COMMITTED log, so it is deterministic here whatever a fresh run
#: would do.
CONFLATED_NO_CLAUSE_CALLS: Final[tuple[str, ...]] = (
    "CALL-06",
    "CALL-07",
    "CALL-09",
    "CALL-18",
)


def test_the_no_clause_conflation_is_exactly_the_calls_it_is_recorded_as() -> None:
    """The measured defect and its structural fix, held against each other.

    Until D125 this pinned the four no-clause calls the dimension flagged
    `misaligned`, as a defect recorded rather than fixed -- a criteria edit had
    been tried and reverted, and the pin existed so the observation could not
    be lost. The fix is the entry's precondition, and what is worth asserting
    now is that the two populations are the **same** population.

    Both directions, and each names a different failure. A call the log records
    as conflated that the precondition does not exclude is a defect left partly
    in place. A call the precondition excludes that the log never flagged is a
    fix wider than the defect -- **which is the falsifier D125 wrote down
    before running its first attempt**, and it is only checkable because the
    defect was pinned rather than described.

    The left-hand side is read off the COMMITTED log, so it is what a model
    actually did; the right-hand side is read off the live entry, so it is what
    the harness would do now. Neither is a restatement of the other.
    """
    entry = _rubric().by_id(ENTRY_ID)
    assert entry.judge is not None
    by_call = _measured_verdicts_by_call()
    no_clauses = [
        context.call_id
        for context in _contexts()
        if not context.retrieved_policies and by_call.get(context.call_id)
    ]
    assert no_clauses, "no design call retrieved zero policies, so this compares nothing"
    flagged = tuple(
        sorted(call for call in no_clauses if _modal(by_call[call], entry) == entry.negative)
    )
    assert flagged == CONFLATED_NO_CLAUSE_CALLS, (
        "the set of no-clause calls this dimension flagged has changed. Recorded: "
        f"{CONFLATED_NO_CLAUSE_CALLS}; measured: {flagged}. If the conflation is closed, say "
        "how in the same commit; if it widened, that is a finding."
    )

    excluded = tuple(
        sorted(
            context.call_id
            for context in _contexts()
            if absent_categories(context, entry.judge.applies_when_facts_present, entry_id=entry.id)
        )
    )
    no_clauses_at_all = tuple(
        sorted(context.call_id for context in _contexts() if not context.retrieved_policies)
    )

    # (1) Every call the conflation was measured on is now excluded. A fix that
    #     left one behind would have closed the defect for the calls somebody
    #     happened to look at.
    assert set(CONFLATED_NO_CLAUSE_CALLS) <= set(excluded), (
        "the precondition does not exclude every call the conflation was measured on. "
        f"Recorded: {CONFLATED_NO_CLAUSE_CALLS}; excluded now: {excluded}."
    )

    # (2) It excludes on retrieval and on nothing wider. This is the half that
    #     makes (1) a fix rather than a bigger hammer: the boundary is the
    #     dimension's own subject -- the clause this call retrieved -- and not
    #     a list of calls somebody found disagreeable.
    assert excluded == no_clauses_at_all, (
        "the precondition excludes a set of calls that is not the set with no retrieved "
        f"clause. Excluded: {excluded}; no clause at all: {no_clauses_at_all}. A boundary "
        "drawn anywhere but the dimension's own subject is a fix chosen by its results."
    )

    # (3) D125's falsifier, written down before its first attempt was run: the
    #     seeded calls must still be judged. They retrieved clauses, so the
    #     precondition has to leave every one of them alone.
    assert not set(SEEDED) & set(excluded), (
        f"the precondition excludes a seeded call: {sorted(set(SEEDED) & set(excluded))}. "
        "Those retrieved a policy and are what this dimension exists to judge."
    )


def test_the_conflation_was_wider_than_the_half_that_showed() -> None:
    """The finding the fix turned up, which the pin above could not see.

    `CONFLATED_NO_CLAUSE_CALLS` was measured as the no-clause calls the
    dimension flagged **misaligned** -- four of them, visibly wrong. The
    precondition excludes eight, and the difference is the calls that came back
    `aligned` with no clause to be aligned with: a verdict as meaningless as
    the other four and far harder to notice, because a pass on a corpus seeded
    with defects reads as the dimension working.

    So the recorded defect was the visible half of a wider one, and the fix
    turned up the other half rather than the measurement doing it. Asserted in
    both directions: the silent half must be non-empty, and every call in it
    must have come back on the dimension's positive side -- which is what makes
    it silent rather than a second population of flags nobody counted.
    """
    entry = _rubric().by_id(ENTRY_ID)
    by_call = _measured_verdicts_by_call()
    silent = sorted(
        context.call_id
        for context in _contexts()
        if not context.retrieved_policies
        and by_call.get(context.call_id)
        and context.call_id not in CONFLATED_NO_CLAUSE_CALLS
    )
    assert silent, (
        "every no-clause call the log covers was flagged, so the conflation had no silent "
        "half. That is a different measurement from the one recorded and worth saying so."
    )
    for call_id in silent:
        assert _modal(by_call[call_id], entry) != entry.negative, (
            f"{call_id} is in neither the flagged set nor the silent one, so this test's own "
            "partition of the no-clause calls is wrong"
        )


def test_the_calls_that_did_retrieve_clauses_are_judged_on_their_paraphrase() -> None:
    """The other half, and what stops the pin above reading as "the dimension
    is broken".

    On calls that DID retrieve a policy, the dimension does what it is for: it
    catches two of the three seeded misparaphrases and stays silent on the
    negative instance. The conflation is a scope defect at the edge, not a
    failure at the center.
    """
    entry = _rubric().by_id(ENTRY_ID)
    by_call = _verdicts_by_call()
    with_clauses = {context.call_id for context in _contexts() if context.retrieved_policies}
    assert {"CALL-02", "CALL-04", "CALL-03"} <= with_clauses
    assert _modal(by_call["CALL-02"], entry) == entry.negative
    assert _modal(by_call["CALL-04"], entry) == entry.negative
    assert _modal(by_call["CALL-03"], entry) != entry.negative


#: The greatest share of its ceiling any judged entry's largest answer may take.
#:
#: **This was a factor of two until D139, and the factor could not survive
#: D137.** It said the ceiling must be at least twice the largest recorded
#: answer, which is a sensible rule while ceilings are *fitted per entry* -- and
#: D137 stopped fitting them. Against a ceiling chosen generously rather than
#: measured, "twice the observed max" is a ratchet: every pass that produces a
#: longer answer demands a higher ceiling, forever, and the ceiling's real cost
#: is the informativeness of the pre-flight figure a human approves.
#:
#: **The number is where it is because a threshold belongs between the
#: observation it must reject and the observation it must accept.** It must
#: reject 84% -- `J-policy-alignment` at 3,429 of 4,096, the one case this rule
#: ever caught, which had never truncated and which nothing else was watching.
#: It must accept 63% -- the largest answer in the committed log. The midpoint
#: is 73.5%, and 75% leaves roughly nine points of clearance on each side, which
#: is what makes it robust to the verdict re-roll a fresh recording produces
#: rather than fitted to one measurement.
#:
#: It is a judgment either way, and it was revised after seeing data that
#: motivated revising it. That is said here rather than left to be inferred.
CEILING_FILL_LIMIT: Final[float] = 0.75


def test_every_entrys_max_tokens_clears_what_the_reference_run_recorded() -> None:
    """The mechanism D135 exists because nothing had.

    Phase 3 learned that `max_tokens` bounds thinking plus output, wrote it
    down in three places, and phase 4 then gave five new dimensions the value
    that lesson had produced -- **copied from an entry of a different shape**.
    The one dimension that renders facts carries the largest prompt and the most
    to reason over, and a live pass truncated it: 4,096 output tokens of a 4,096
    ceiling, resolving to `errored` carrying its stop reason.

    A number reasoned about in a comment beside itself is a number that goes
    stale the moment the thing it describes changes. This reads what each entry
    actually produced and requires the ceiling to stand clear of it -- the same
    move the pre-flight estimate's divisor made when it stopped being derived
    from English prose and started being measured against this log.

    **Both directions.** A ceiling under its entry's appetite is a live run
    losing results; a recorded answer that exactly equals its ceiling is what a
    truncation looks like in an artifact, and it is asserted separately because
    the margin check would pass on an entry whose ceiling had been raised after
    the truncation without re-recording.
    """
    rubric = _rubric()
    largest: dict[str, int] = {}
    truncated: list[str] = []
    for row in _rows():
        entry_id = row["entry_id"]
        largest[entry_id] = max(largest.get(entry_id, 0), row["output_tokens"])
        if row["stop_reason"] == "max_tokens":
            truncated.append(f"{entry_id} {row['call_id']} rep {row['repetition']}")

    assert not truncated, (
        "the committed log contains truncated answers, so the run it records lost results to a "
        f"ceiling rather than to anything about the agent: {truncated}"
    )
    assert largest, "the committed log holds no call records"

    for entry in rubric.for_tier(CheckTier.JUDGE):
        assert entry.judge is not None
        observed = largest.get(entry.id)
        if observed is None:
            continue
        assert observed <= entry.judge.max_tokens * CEILING_FILL_LIMIT, (
            f"{entry.id} declares max_tokens={entry.judge.max_tokens} and its largest recorded "
            f"answer was {observed}, which is {observed / entry.judge.max_tokens:.0%} of it. The "
            "ceiling bounds thinking plus output, and thinking is the half that varies with the "
            "call -- an entry running this close to its ceiling truncates on the next hard one."
        )


#: **Truncations no committed log carries** (OB-31): each entry named, the output length a
#: recording of it was cut at, and where that is recorded.
#:
#: The fill limit above reads the committed log, and the recording that truncated the synthesis
#: at 8,192 output tokens -- CALL-08's ninth repetition, D154's first resampled recording, which
#: D155 answered on 2026-09-11 by raising that entry alone to 16384 -- was never committed. Against
#: the log the synthesis's largest answer is 2,140 tokens, so a ceiling lowered back to 8192 cleared
#: every check (P4-14). The file is not in the tree, and pinning its name or hash would fail on
#: every clone, so the fact travels as data: a ceiling that has already truncated an entry is one
#: that entry is known to need more than.
OBSERVED_TRUNCATIONS: Final[Mapping[str, tuple[int, str]]] = MappingProxyType(
    {"J-call-synthesis": (8192, "D155, 2026-09-11: CALL-08 repetition 9 cut at 8,192")}
)


def test_the_ceiling_would_notice_an_entry_lowered_to_where_it_truncated() -> None:
    """P4-14. A ceiling a recording has already overrun is refused by name.

    `test_every_entrys_max_tokens_clears_what_the_reference_run_recorded` can see only
    what the committed log holds, and the one truncation that set the synthesis's
    ceiling is not in it. This reads `OBSERVED_TRUNCATIONS` instead: every entry named
    there must declare a ceiling above the output length it was cut at, so returning
    the synthesis to 8192 fails here while every test reading the log stays green
    (OB-31).
    """
    rubric = _rubric()
    for entry_id, (cut_at, where) in OBSERVED_TRUNCATIONS.items():
        entry = rubric.by_id(entry_id)
        assert entry.judge is not None
        assert entry.judge.max_tokens > cut_at, (
            f"{entry_id} declares max_tokens={entry.judge.max_tokens}, and a recording of it "
            f"was cut at {cut_at} output tokens ({where}), so this ceiling has already "
            "truncated it once"
        )


def test_the_retry_share_would_notice_the_retries_a_log_records_uncounted() -> None:
    """P4-16. The share the expected figure multiplies calls by is the log's own count (D170).

    Computed here from the raw call records rather than through the reader the CLI
    uses, as the answer lengths are below: one plus each entry's informed retries
    over its first attempts. The committed log's synthesis retried, so a share left
    at one for every entry disagrees with it (OB-33).
    """
    from harness.cli import recorded_retry_shares

    first: collections.Counter[str] = collections.Counter()
    retried: collections.Counter[str] = collections.Counter()
    for row in _rows():
        (first if int(row["retry_index"]) == 0 else retried)[str(row["entry_id"])] += 1
    counted = {entry_id: 1 + retried[entry_id] / count for entry_id, count in first.items()}

    shares = recorded_retry_shares(_reference_log())
    assert shares.keys() == counted.keys(), "the shares name other entries than the log records"
    mismatched = [
        f"{entry_id}: read {shares[entry_id]:.4f}, counted {counted[entry_id]:.4f}"
        for entry_id in sorted(counted)
        if shares[entry_id] != pytest.approx(counted[entry_id])
    ]
    assert not mismatched, "retry shares disagree with the call records:\n  " + "\n  ".join(
        mismatched
    )


def test_the_expected_cost_sits_between_what_the_reference_run_spent_and_the_ceiling() -> None:
    """OB-17's figure, checked per entry against the bill it predicts (D152, D170).

    Two assertions. The answer length each entry is priced at is the mean output
    its first attempts recorded, computed here from the raw call records rather
    than through the reader the CLI uses. And the expected cost for each entry,
    its calls multiplied by the retry share the log recorded, sits at or above
    what every call recorded for it cost, informed retries included, and below
    the entry's ceiling: its input side is the rendered estimate
    `test_the_preflight_estimate_brackets_what_the_real_run_recorded` holds above
    every recorded count, and its output side is the recorded mean rounded up.

    Per entry rather than on the total, because the synthesis runs on a model
    priced two and a half times the others, and a figure right in total and wrong
    per entry is wrong about which entry the money goes to.
    """
    from harness.cli import (
        expected_cost_usd,
        judged_entry_estimates,
        recorded_answer_lengths,
        recorded_retry_shares,
    )
    from harness.core.transport import rates_for

    rows = _rows()
    assert any(int(row["retry_index"]) == 0 for row in rows), (
        "the reference log records no first attempts"
    )
    outputs: dict[str, list[int]] = collections.defaultdict(list)
    spent: dict[str, float] = collections.defaultdict(float)
    for row in rows:
        if int(row["retry_index"]) == 0:
            outputs[row["entry_id"]].append(int(row["output_tokens"]))
        input_rate, output_rate = rates_for(str(row["model"]))
        spent[row["entry_id"]] += (
            int(row["input_tokens"]) * input_rate + int(row["output_tokens"]) * output_rate
        ) / 1_000_000

    lengths = recorded_answer_lengths(_reference_log())
    shares = recorded_retry_shares(_reference_log())
    mismatched = [
        f"{entry_id}: priced at {lengths.get(entry_id)}, "
        f"recorded mean {math.ceil(sum(seen) / len(seen))}"
        for entry_id, seen in sorted(outputs.items())
        if lengths.get(entry_id) != math.ceil(sum(seen) / len(seen))
    ]
    assert not mismatched, "answer lengths disagree with the first attempts:\n  " + "\n  ".join(
        mismatched
    )

    estimates = judged_entry_estimates(_rubric(), _contexts(), _template())
    assert {estimate.entry_id for estimate in estimates} == set(outputs), (
        "the entries the estimate prices are not the entries the reference log recorded"
    )
    outside: list[str] = []
    for estimate in estimates:
        expected, unrecorded = expected_cost_usd([estimate], lengths, shares)
        assert not unrecorded, f"{estimate.entry_id} has no recorded answer length"
        ceiling = estimate.ceiling_usd()
        if not spent[estimate.entry_id] <= expected < ceiling:
            outside.append(
                f"{estimate.entry_id}: spent ${spent[estimate.entry_id]:.4f}, "
                f"expected ${expected:.4f}, ceiling ${ceiling:.4f}"
            )
    assert not outside, (
        "the expected figure is outside the bracket of what the run spent and the ceiling:\n  "
        + "\n  ".join(outside)
    )
