"""Rolling N repetitions into a rate, a gate and a distribution (P4).

Phase 3 built none of this on purpose (D124), because **first**, **modal** and
**worst** are three different claims about what N means. These are the
assertions that make the choice a decision rather than a helper -- and several
of them exist because the specification's own criteria did not distinguish the
design from its inversion until D130 added the halves they were missing.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Final

import pytest

from harness.checks import build_registry
from harness.core.registry import ResultBuilder
from harness.core.result import Provenance, Result, Status
from harness.core.rubric import RubricEntry, load_rubric
from harness.judge.engine import JudgedOutcome
from harness.judge.rollup import JudgedEntryRollup, _modal, roll_up_judged

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
PROVENANCE: Final[Provenance] = Provenance("1", "0.6.0", "a" * 64)
ENTRY_ID: Final[str] = "J-concerns-addressed"


def _entry(entry_id: str = ENTRY_ID) -> RubricEntry:
    """A shipped entry. A fixture entry here would make these tests assertions
    about a fixture, and the tie rule reads `scale` and `negative` off the
    rubric."""
    return load_rubric(REPO_ROOT / "rubric.yaml", build_registry().keys()).by_id(entry_id)


def _verdicts(entry: RubricEntry, call_id: str, **counts: int) -> list[JudgedOutcome]:
    builder = ResultBuilder(entry=entry, call_id=call_id, provenance=PROVENANCE)
    outcomes: list[JudgedOutcome] = []
    repetition = 0
    for verdict, count in counts.items():
        for _ in range(count):
            repetition += 1
            outcomes.append(
                JudgedOutcome(
                    result=builder.applicable(verdict, ("[T1] caller: something", "rationale")),
                    repetition=repetition,
                    request_hash="h",
                    stop_reason="end_turn",
                    informed_retries=0,
                )
            )
    return outcomes


def _status(entry: RubricEntry, call_id: str, status: Status, count: int) -> list[JudgedOutcome]:
    builder = ResultBuilder(entry=entry, call_id=call_id, provenance=PROVENANCE)
    make: dict[Status, Callable[[], Result]] = {
        Status.REFUSED: lambda: builder.refused("the model declined"),
        Status.ERRORED: lambda: builder.errored("the retry budget is exhausted"),
        Status.NOT_APPLICABLE: lambda: builder.not_applicable("this dimension does not apply"),
        Status.UNEVALUABLE: lambda: builder.unevaluable("corpus:missing", "no ground truth"),
    }
    build = make[status]
    return [
        JudgedOutcome(
            result=build(),
            repetition=0 if status is Status.NOT_APPLICABLE else index,
            request_hash="",
            stop_reason="",
            informed_retries=0,
        )
        for index in range(1, count + 1)
    ]


def _only(outcomes: Sequence[JudgedOutcome], entry: RubricEntry) -> JudgedEntryRollup:
    return roll_up_judged(outcomes, [entry])[0]


# --------------------------------------------------------------------------
# The distribution is the report, and the modal verdict is the gate's
# --------------------------------------------------------------------------


def test_a_dimension_whose_repetitions_disagree_is_reported_as_a_distribution() -> None:
    """The criterion D130 added, and the half the original could not buy.

    "A judged dimension evaluated at N>1 is reported as a verdict distribution,
    not a single verdict" is satisfied on a **unanimous** fixture by a renderer
    that prints `{the first verdict: N}` and never reads repetitions 2 to N.
    The distribution's whole purpose is the case where they disagree, so the
    fixture disagrees.
    """
    entry = _entry()
    rollup = _only(_verdicts(entry, "CALL-04", addressed=6, unaddressed=4), entry)
    call = rollup.calls[0]
    assert dict(call.distribution) == {"addressed": 6, "unaddressed": 4}
    assert call.applicable == 10


def test_the_distribution_is_in_scale_order_rather_than_count_order() -> None:
    """So two calls are comparable at a glance.

    A distribution that reordered itself with the data would put the same
    verdict in a different column on every row, which is the property a reader
    scanning a table relies on without knowing they rely on it.
    """
    entry = _entry()
    rollup = _only(_verdicts(entry, "CALL-04", unaddressed=9, addressed=1), entry)
    assert [name for name, _ in rollup.calls[0].distribution] == ["addressed", "unaddressed"]


def test_the_modal_verdict_is_what_the_gate_reads() -> None:
    """Modal rather than first or worst, and the difference is not cosmetic.

    **first** discards nine samples and makes N decorative. **worst** makes one
    flip in ten fail the call, so raising N would make a dimension strictly
    more likely to fail -- the measurement moving the verdict, which is the one
    thing an evaluator must not do.
    """
    entry = _entry()
    rollup = _only(_verdicts(entry, "CALL-04", addressed=6, unaddressed=4), entry)
    assert rollup.calls[0].verdict == "addressed"
    assert not rollup.calls[0].violated
    assert rollup.violations == 0


def test_a_tie_resolves_toward_the_negative_pole_and_says_that_it_was_a_tie() -> None:
    """Five for and five against is an evaluator that could not decide.

    The two readings are "record that nothing went wrong" and "record that
    something did", and recording nothing is the fail-open: it turns an
    unresolved measurement into a pass, on a tier whose thesis is that failure
    modes must not be reported as one thing.

    **And the tie is reported**, which is the half a modal verdict destroys. A
    reader looking at `unaddressed` has no way to see it was reached over a
    split unless the roll-up says so.
    """
    entry = _entry()
    rollup = _only(_verdicts(entry, "CALL-04", addressed=5, unaddressed=5), entry)
    call = rollup.calls[0]
    assert call.verdict == entry.negative
    assert call.tied
    assert rollup.tied == ("CALL-04",)


def test_a_tie_that_does_not_involve_the_negative_pole_follows_scale_order() -> None:
    """Deterministic, and it cannot change the gate.

    The alternative is a verdict that depends on which repetition came back
    first, which would make a report of a replayed run differ from a report of
    the same run recorded in a different order.

    **On an entry that violates on its pole alone.** This used
    `J-concerns-addressed` until D160 counted that entry's middle value against
    its gate, which turns a split between `addressed` and `partially_addressed`
    into a tie with a violating verdict -- asserted below, with the other answer.
    """
    entry = _entry("J-confidence-exceeds-sources")
    rollup = _only(_verdicts(entry, "CALL-04", borderline=5, within_sources=5), entry)
    assert rollup.calls[0].verdict == "within_sources"
    assert rollup.calls[0].tied


def test_the_tie_rule_is_the_function_the_rollup_calls() -> None:
    """The control's target, driven directly rather than re-implemented.

    Six controls in this tree asserted a rule beside the check instead of
    calling it, and every one was measuring nothing (D121). `_modal` is the
    named function, so a control can plant a defect in the rule itself.
    """
    entry = _entry()
    assert _modal((("addressed", 5), ("unaddressed", 5)), entry) == entry.negative
    assert _modal((("addressed", 6), ("unaddressed", 4)), entry) == "addressed"


# --------------------------------------------------------------------------
# D160: verdicts beside the pole that count against the gate
# --------------------------------------------------------------------------


def test_the_gate_would_notice_a_declared_violating_verdict_read_as_a_pass() -> None:
    """A call whose modal verdict is one the entry declares violating counts
    against the gate, not only a call that reached the negative pole (D160).

    `J-concerns-addressed` asks whether every concern was answered, and its
    middle value is defined as at least one left unanswered. Read as a pass, the
    entry caught none of the findings it traces on the committed log. The
    pole-only entry beside it is the other direction: its middle value passes.
    """
    entry = _entry()
    assert entry.violating == ("partially_addressed", "unaddressed")
    rollup = _only(
        _verdicts(entry, "CALL-04", partially_addressed=10)
        + _verdicts(entry, "CALL-03", addressed=10),
        entry,
    )
    assert [(call.call_id, call.violated) for call in rollup.calls] == [
        ("CALL-03", False),
        ("CALL-04", True),
    ]
    assert rollup.violations == 1
    assert rollup.gate_failed

    other = _entry("J-confidence-exceeds-sources")
    assert other.violating == (other.negative,)
    held = _only(_verdicts(other, "CALL-04", borderline=10), other)
    assert not held.calls[0].violated
    assert not held.gate_failed


def test_the_tie_rule_would_notice_a_split_with_a_violating_verdict_read_as_a_pass() -> None:
    """D160's half of the tie rule, for the reason the pole's half exists.

    Five `addressed` and five `partially_addressed`, on an entry counting the
    second against its gate, is an evaluator that could not decide between a
    pass and a violation -- and scale order would record the pass. Driven
    through the roll-up and through `_modal`, which the synthesis's headline
    also calls (D154), so both read the split the same way.
    """
    entry = _entry()
    rollup = _only(_verdicts(entry, "CALL-04", addressed=5, partially_addressed=5), entry)
    call = rollup.calls[0]
    assert call.tied
    assert call.verdict == "partially_addressed"
    assert call.violated
    assert _modal((("addressed", 5), ("partially_addressed", 5)), entry) == "partially_addressed"
    assert _modal((("partially_addressed", 5), ("unaddressed", 5)), entry) == entry.negative


# --------------------------------------------------------------------------
# The denominator: applicable calls, and every other status beside it
# --------------------------------------------------------------------------


def test_the_rate_counts_calls_rather_than_repetitions() -> None:
    """The unit a rate is about is the call.

    D124 rejected feeding N results into the deterministic roll-up because it
    divides by the number of applicable results, so ten repetitions of one call
    would weight that call ten times in its own rate -- the shape
    `DuplicateCallError` refuses, arriving through a legitimate door.
    """
    entry = _entry()
    outcomes = _verdicts(entry, "CALL-04", unaddressed=10) + _verdicts(
        entry, "CALL-03", addressed=10
    )
    rollup = _only(outcomes, entry)
    assert rollup.applicable == 2
    assert rollup.violations == 1
    assert rollup.pass_rate == 0.5


@pytest.mark.parametrize(
    "status",
    [Status.ERRORED, Status.NOT_APPLICABLE, Status.UNEVALUABLE, Status.REFUSED],
)
def test_every_status_that_is_not_applicable_leaves_the_denominator(status: Status) -> None:
    """The criterion D130 added, asserted **per status**.

    `unevaluable` has had its own criterion since P2 and `refused` gained one
    at P4; `errored` and `not_applicable` were asserted by neither, and two of
    four exclusions checked individually is what made the other two's absence a
    gap rather than a general impression that the denominator counts
    `applicable` only.
    """
    entry = _entry()
    outcomes = _verdicts(entry, "CALL-03", addressed=10) + _status(entry, "CALL-04", status, 10)
    rollup = _only(outcomes, entry)
    assert rollup.applicable == 1, f"a {status.value} call is in the denominator"
    assert rollup.result_count(status) == 10
    assert rollup.pass_rate == 1.0


def test_the_rate_is_none_rather_than_zero_when_no_call_produced_a_verdict() -> None:
    """A rate of 0.0 says every call violated. `None` says none was judged.

    Reporting the second as the first fails a gate on a dimension that never
    ran, which is a finding about the agent invented out of a dimension's
    silence.
    """
    entry = _entry()
    rollup = _only(_status(entry, "CALL-04", Status.REFUSED, 10), entry)
    assert rollup.pass_rate is None
    assert not rollup.gate_failed


# --------------------------------------------------------------------------
# OB-14: whether a run of refusals counts as having run
# --------------------------------------------------------------------------


def test_a_dimension_whose_every_result_was_refused_measured_nothing() -> None:
    """`OB-14`, answered without a threshold.

    D127 left this at exit 0 with the counts printed, because the alternative
    was a threshold and a threshold is a gate -- and *how many refusals are too
    many* was what this roll-up existed to answer with the distribution in
    view. With it in view the answer is that the question was the wrong one:
    what matters is not how many, but whether anything was measured.
    """
    entry = _entry()
    rollup = _only(_status(entry, "CALL-04", Status.REFUSED, 10), entry)
    assert rollup.measured_nothing


def test_a_dimension_with_one_verdict_among_the_refusals_measured_something() -> None:
    """The other side of the same rule, and the reason it needs no threshold.

    Nine refusals and one verdict is a dimension that measured something,
    badly, and its counts say so. Treating that as "measured nothing" would be
    a threshold in everything but name -- and a threshold is the thing D127
    declined to invent without the distribution in view.
    """
    entry = _entry()
    outcomes = _status(entry, "CALL-04", Status.REFUSED, 9) + _verdicts(
        entry, "CALL-03", addressed=1
    )
    rollup = _only(outcomes, entry)
    assert not rollup.measured_nothing


def test_a_dimension_that_applied_to_no_call_did_not_measure_nothing() -> None:
    """The inversion, and it is the half that would have been easy to lose.

    A dimension excluded by its own precondition produced no verdict, exactly
    like one that was refused throughout -- and the two must not exit the same
    way. Nothing failed here: the precondition said the dimension does not
    apply, before any call was issued, which is an answer rather than an
    absence.
    """
    entry = _entry()
    rollup = _only(_status(entry, "CALL-04", Status.NOT_APPLICABLE, 1), entry)
    assert rollup.pass_rate is None
    assert not rollup.measured_nothing


# --------------------------------------------------------------------------
# The gate
# --------------------------------------------------------------------------


def test_a_rate_below_the_threshold_fails_the_gate() -> None:
    """The gate the judged tier did not have at P3 (`OB-8`).

    Every judged entry in this rubric declares `threshold: 1.0`, so one
    violated call fails -- which it will over a corpus seeded with defects by
    construction. D105: that is the tier working rather than failing.
    """
    entry = _entry()
    outcomes = _verdicts(entry, "CALL-04", unaddressed=10) + _verdicts(
        entry, "CALL-03", addressed=10
    )
    rollup = _only(outcomes, entry)
    assert rollup.gate_failed


def test_a_gate_holds_when_no_call_reached_the_negative_pole() -> None:
    entry = _entry()
    rollup = _only(_verdicts(entry, "CALL-03", addressed=10), entry)
    assert not rollup.gate_failed
    assert rollup.pass_rate == 1.0


def test_a_run_that_produced_nothing_for_an_entry_still_gets_a_row() -> None:
    """An entry the run never reached is a row with no calls, not a missing row.

    `roll_up_judged` takes the entries that ran rather than reading them from
    the rubric, so a run that aborted part-way reports what it obtained -- and
    an entry it never started is visibly empty rather than absent, which is the
    difference between a reader seeing a gap and inferring one.
    """
    entry = _entry()
    rollup = _only([], entry)
    assert rollup.calls == ()
    assert rollup.pass_rate is None
    assert not rollup.measured_nothing
