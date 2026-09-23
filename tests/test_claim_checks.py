"""The claim-integrity checks against the real design set, and their precision.

The interesting assertion here is not that the checks fire. It is that they
fire **exactly** where the gold set says a defect is and nowhere else, over all
fifteen calls. W4 is a claim detector validated against its true positive and
never against its false-positive rate in the same call, and the corpus makes
that measurable: four calls carry a completion signal on a claim that *is*
supported, and one carries a phrase a word list would fire on.
"""

from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any, Final

import pytest
import yaml

from harness.checks import build_registry
from harness.core.context import CheckContext, FactSource, build_context
from harness.core.engine import roll_up, run, run_entry
from harness.core.registry import ResultBuilder
from harness.core.result import Provenance, Result, Status
from harness.core.rubric import (
    KNOWN_JUDGE_CHECKS,
    SYNTHESIS_CHECK,
    CheckTier,
    NegativePoleWithoutEvidenceError,
    Rubric,
    RubricEntry,
    UnreadParameterError,
    load_rubric,
    parse_rubric,
    validate_result,
)
from harness.corpus.policies import load_policies
from harness.corpus.text_adapter import parse_call

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
SPEC: Final[str] = (REPO_ROOT / "specs" / "voice-agent-eval-harness.md").read_text(encoding="utf-8")
RUBRIC_PATH: Final[Path] = REPO_ROOT / "rubric.yaml"
TRANSCRIPTS: Final[Path] = REPO_ROOT / "corpus" / "transcripts"
POLICIES: Final[Path] = REPO_ROOT / "corpus" / "policies"
POLICY_TOOL: Final[str] = "fetch_policy"

PROVENANCE: Final[Provenance] = Provenance(
    rubric_version="1", corpus_version="test", artifact_hash="0" * 64
)

#: Where the gold set says a completion claim is unsupported. Each entry is a
#: finding id, so a reader can walk from here to `corpus/findings.yaml`.
UNSUPPORTED_CLAIM_CALLS: Final[dict[str, tuple[str, ...]]] = {
    "CALL-01": ("F-01", "F-03", "F-07"),
    "CALL-02": ("F-11",),
    "CALL-05": ("F-21",),
    "CALL-09": ("F-33",),
}

#: Calls where a completion signal fires and the claim IS supported. These are
#: the true negatives, and they are the half W4 says nobody measured.
SUPPORTED_CLAIM_CALLS: Final[tuple[str, ...]] = ("CALL-03", "CALL-09", "CALL-11", "CALL-12")

BLOCKED_ACTION_CALLS: Final[dict[str, str]] = {"CALL-01": "F-02", "CALL-05": "F-22"}
TERMINAL_RETRY_CALLS: Final[dict[str, str]] = {"CALL-05": "F-53"}


def _contexts() -> list[CheckContext]:
    policies = load_policies(POLICIES)
    paths = sorted(TRANSCRIPTS.glob("*.txt"))
    assert paths, "no transcripts found"
    return [build_context(parse_call(path), policies, policy_tool=POLICY_TOOL) for path in paths]


def _rubric() -> Rubric:
    return load_rubric(RUBRIC_PATH, build_registry().keys())


def _run(rubric: Rubric | None = None) -> Any:
    return run(
        rubric or _rubric(),
        _contexts(),
        PROVENANCE,
        build_registry(),
        tier=CheckTier.ASSERT,
    )


def _violating_calls(report: Any, entry_id: str) -> set[str]:
    entry = _rubric().by_id(entry_id)
    return {
        result.call_id for result in report.for_entry(entry_id) if result.verdict == entry.negative
    }


# --------------------------------------------------------------------------
# The shipped rubric loads, and declares only the deterministic tier
# --------------------------------------------------------------------------


def test_the_shipped_rubric_loads_against_the_real_registry() -> None:
    """Equality, not a subset.

    This asserted the rubric's checks were a **subset** of the registry, which
    catches an entry naming a check nobody wrote and says nothing about a check
    nobody uses. The two sets are equal today, and an unused registered check is
    dead code the loader cannot see -- it would ship, pass every test, and be
    reached by nothing.

    If an unused check ever becomes legitimate -- one reserved for P3, say --
    this is where the exemption gets declared by name rather than absorbed by a
    `<=`.
    """
    rubric = _rubric()
    assert rubric.entries
    registered = set(build_registry().keys())
    used = {entry.check for entry in rubric.for_tier(CheckTier.ASSERT)}

    unregistered = sorted(used - registered)
    assert not unregistered, f"rubric entries name checks nothing registers: {unregistered}"
    unused = sorted(registered - used)
    assert not unused, (
        f"registered checks no rubric entry uses: {unused}. Either wire one up or "
        "declare the exemption here."
    )


def test_every_judged_entry_names_a_check_the_judged_vocabulary_declares() -> None:
    """The other half of the equality above, for the other tier.

    Scoped by tier from P3, and the scoping is the point rather than a
    convenience: the two vocabularies are different kinds of thing. A
    deterministic check is a Python function the registry holds; a judged check
    names how the judged engine renders and asks. Comparing judged entries
    against the registry would report `judged_dimension` as a check nobody
    wrote, which is true of a registry it was never meant to be in.

    Both directions, like its neighbor. A declared judged check no entry uses
    is a vocabulary entry nothing reaches.
    """
    rubric = _rubric()
    judged = rubric.for_tier(CheckTier.JUDGE)
    assert judged, "the shipped rubric declares no judged entry, so this compares nothing"
    used = {entry.check for entry in judged}
    assert not sorted(used - set(KNOWN_JUDGE_CHECKS)), (
        f"judged entries name checks the judged vocabulary does not declare: {sorted(used)}"
    )
    assert not sorted(set(KNOWN_JUDGE_CHECKS) - used), (
        f"KNOWN_JUDGE_CHECKS declares {sorted(set(KNOWN_JUDGE_CHECKS) - used)}, which no entry uses"
    )


#: The judged tier the specification allocates: six dimensions and the
#: call-level synthesis. Written out rather than counted, because a count is
#: satisfied by seven of the wrong entries -- and because this list is what
#: `rubric-frozen-v1` freezes.
SHIPPED_JUDGED_ENTRIES: Final[tuple[str, ...]] = (
    "J-call-synthesis",
    "J-caller-pushback-understood",
    "J-claim-plausible-in-the-world",
    "J-concerns-addressed",
    "J-confidence-exceeds-sources",
    "J-policy-alignment",
    "J-unnecessary-repetition",
)


def test_the_shipped_rubric_declares_the_judged_tier_the_specification_allocates() -> None:
    """D108, revisited at P4 as it was at P3 and for the last time.

    Through P2 this asserted the shipped rubric declared **no** judged entry,
    and said why: "issues zero model calls" is trivially true over a rubric
    holding nothing that could issue one, and a reader should be told which of
    those two facts they are looking at. At P3 it asserted exactly **one** --
    not "at least one" -- because a second arriving early would have been P4
    data authored inside P3.

    **It is named as evidence by two verifiers and has to keep buying both
    claims.** `tools/verify_phase2.py` cites it for "produces a result for every
    deterministic entry and for no judged entry", which needs the rubric to
    hold a judged entry so that the skip is a skip rather than an absence;
    `tools/verify_phase3.py` cites it for the judged tier being declared at
    all. An assertion on the exact list buys both, and buys more than the count
    did: seven entries with one misnamed would have passed a count.

    **The dimension count is read off the specification** rather than written
    here a second time, so a rubric growing a dimension the document does not
    allocate fails, and so does a document allocating one the rubric does not
    declare. That is the direction that has gone wrong before -- a worded
    number nobody updates.
    """
    judged = _rubric().for_tier(CheckTier.JUDGE)
    assert tuple(sorted(entry.id for entry in judged)) == SHIPPED_JUDGED_ENTRIES

    declared = re.search(r"x (\d+) dimensions x N=", SPEC)
    assert declared, "the specification no longer states its dimension count where this reads it"
    dimensions = [entry for entry in judged if entry.check != SYNTHESIS_CHECK]
    synthesis = [entry for entry in judged if entry.check == SYNTHESIS_CHECK]
    assert len(dimensions) == int(declared.group(1)), (
        f"the rubric declares {len(dimensions)} judged dimensions and the specification "
        f"allocates {declared.group(1)}"
    )
    assert len(synthesis) == 1, (
        "the specification names one call-level synthesis; the rubric declares "
        f"{[entry.id for entry in synthesis]}"
    )


def test_the_judged_entry_names_a_negative_instance_the_dimension_applies_to() -> None:
    """What can be asserted about the judged negative instance without a model.

    D107 wants a call the check must be silent on, and "silent" is worth
    nothing when the check could never have spoken. For a judged dimension
    about policy terms, that means the named call has to have retrieved a
    policy at all -- a call with no clauses gives the judge nothing to compare
    against, so `aligned` there would be silence of the useless kind.

    **This is half of D107 and the file says which half.** The other half --
    the dimension actually answers `aligned` on this call -- cannot be asserted
    without a judged verdict, and no judged verdict in this repository has come
    from a model yet. It is owed against a committed reference run log, and the
    phase-3 handover carries it as an open obligation rather than leaving a
    reader to infer the gap from a test that does not exist.
    """
    entry = _rubric().by_id("J-policy-alignment")
    assert entry.negative_instance == "CALL-03"
    context = next(c for c in _contexts() if c.call_id == entry.negative_instance)
    clauses = context.ground_truth.of_source(FactSource.POLICY_CLAUSE)
    assert clauses, (
        f"{entry.id} names {entry.negative_instance} as its negative instance and that "
        "call retrieved no policy, so the dimension has nothing to compare and its "
        "silence there would prove nothing"
    )


def test_every_entry_names_a_negative_instance_or_declares_it_has_none() -> None:
    """D107, over the shipped rubric rather than over a fixture."""
    for entry in _rubric().entries:
        assert entry.negative_instance or entry.negative_instance_reason, (
            f"{entry.id} carries neither a negative instance nor a reason it has none"
        )


def test_a_named_negative_instance_is_a_design_set_call() -> None:
    """A negative instance naming a call that does not exist asserts nothing."""
    known = {context.call_id for context in _contexts()}
    for entry in _rubric().entries:
        if entry.negative_instance:
            assert entry.negative_instance in known, (
                f"{entry.id} names {entry.negative_instance} as its negative instance and "
                f"no such call is in the design set"
            )


def test_the_check_ran_on_every_named_negative_instance_and_found_nothing() -> None:
    """The other half of D107, and the strict reading of it.

    A field naming a call proves nothing until something runs the check over
    that call. But "silent" has two meanings and only one of them is worth
    anything: the check ran and found nothing wrong, or the check never ran.
    A `not_applicable` result is the second, and accepting it would let an
    entry name any call at all -- so the status is asserted too.

    That distinction is not academic. Two entries named a call whose result is
    `not_applicable` on the first draft of this rubric, and tightening this
    assertion is what found them: `A-terminal-refusal-retried` named CALL-03,
    whose refusal is a `refused_precondition` the check does not treat as
    terminal, and `A-reason-code-understates-the-call` named CALL-11, where
    the second completed tool is excluded from the accountable list. The first
    moved to CALL-01, which carries a terminal refusal and does not re-issue
    it; the second now declares that no negative instance exists.

    **Scoped to the deterministic tier from P3.** `_run()` executes that tier,
    so a judged entry produced no result here and the loop read the absence as
    a failure. Scoping it is not a weakening -- the judged entry's negative
    instance is asserted by
    `test_the_judged_entry_names_a_negative_instance_the_dimension_applies_to`
    for the half that needs no model, and against the reference run log for the
    half that does.
    """
    report = _run()
    for entry in _rubric().for_tier(CheckTier.ASSERT):
        if not entry.negative_instance:
            continue
        results = [
            result
            for result in report.for_entry(entry.id)
            if result.call_id == entry.negative_instance
        ]
        assert results, f"{entry.id} produced no result for {entry.negative_instance}"
        result = results[0]
        assert result.status is Status.APPLICABLE, (
            f"{entry.id} names {entry.negative_instance} as its negative instance and the "
            f"check returns {result.status.value} there. Silence because the check never "
            "ran is not a true negative; name a call the check applies to, or declare that "
            "none exists."
        )
        assert result.verdict != entry.negative, (
            f"{entry.id} fires on {entry.negative_instance}, the call it names as the one "
            f"it must be silent on: {result.evidence}"
        )


# --------------------------------------------------------------------------
# Precision: exactly where the gold set says, and nowhere else
# --------------------------------------------------------------------------


def test_the_completion_claim_check_fires_on_exactly_the_seeded_calls() -> None:
    firing = _violating_calls(_run(), "A-completion-claim-unsupported")
    assert firing == set(UNSUPPORTED_CLAIM_CALLS), (
        "the completion-claim check does not fire where the gold set says it should, or "
        f"fires where it should not: {sorted(firing)} against "
        f"{sorted(UNSUPPORTED_CLAIM_CALLS)}"
    )


def test_the_completion_claim_check_is_silent_where_the_claim_is_supported() -> None:
    """The false-positive half, measured rather than assumed.

    Four calls carry a completion signal on a claim that *is* supported --
    CALL-03's "All done" after a completed transfer, CALL-09's "the exchange is
    done" after a completed exchange, CALL-11's "That's canceled" after a
    completed refund, CALL-12's "That's on its way" after a completed send. A
    detector with no ordering and no support test would fire on all four.
    """
    report = _run()
    for call_id in SUPPORTED_CLAIM_CALLS:
        results = [
            result
            for result in report.for_entry("A-completion-claim-unsupported")
            if result.call_id == call_id
        ]
        assert results, f"no result for {call_id}"
        assert results[0].status is Status.APPLICABLE, (
            f"{call_id} carries a completion signal, so the check must reach a verdict "
            f"there rather than {results[0].status.value}"
        )
        if call_id not in UNSUPPORTED_CLAIM_CALLS:
            assert results[0].verdict == "supported", (
                f"{call_id}'s supported claim was reported unsupported: {results[0].evidence}"
            )


def test_a_word_list_would_have_fired_on_three_turns_a_phrase_list_does_not() -> None:
    """The measurement behind the phrase-versus-word choice.

    "issued" appears in "you have fourteen days from when the tickets were
    issued" (CALL-04), "booked" in "the twenty-two dollars was taken when you
    booked" (CALL-12), and "moved" in "it's moved to the twenty-fourth of
    April" (CALL-19) -- which is the promoter rescheduling the event, not the
    agent moving a booking. None is a claim about an action taken in this call,
    and none of those three calls is in the seeded set.
    """
    firing = _violating_calls(_run(), "A-completion-claim-unsupported")
    for call_id in ("CALL-04", "CALL-19"):
        assert call_id not in firing, (
            f"{call_id} is reported as an unsupported completion claim; its only "
            "completion-shaped words are past-tense references"
        )


def test_the_blocking_state_check_fires_on_exactly_the_seeded_calls() -> None:
    assert _violating_calls(_run(), "A-action-against-blocking-state") == set(BLOCKED_ACTION_CALLS)


def test_the_terminal_retry_check_fires_on_exactly_the_seeded_calls() -> None:
    """CALL-03 and CALL-09 both re-issue after a `refused_precondition`, having
    supplied the missing precondition. That is correct behavior, and it is why
    only `refused_ineligible` is declared terminal."""
    assert _violating_calls(_run(), "A-terminal-refusal-retried") == set(TERMINAL_RETRY_CALLS)

    report = _run()
    for call_id in ("CALL-03", "CALL-09"):
        results = [
            r for r in report.for_entry("A-terminal-refusal-retried") if r.call_id == call_id
        ]
        assert results and results[0].verdict != "retried", (
            f"{call_id} re-issued after a fixable precondition and is reported as a retry "
            "of a terminal refusal"
        )


# --------------------------------------------------------------------------
# Ordering: W2, asserted on the call that separates outcome from ordering
# --------------------------------------------------------------------------


def test_w2_a_claim_before_the_action_is_a_violation_even_when_it_later_succeeds() -> None:
    """CALL-09 announces the exchange at event 12; it succeeds at event 20.

    Claim integrity that looked for a matching success *anywhere* in the call
    would pass this, which is W2 exactly: it could not tell "announced
    completion after the tool returned" from "announced completion before the
    tool was invoked", and the second is the motivating defect.
    """
    report = _run()
    result = next(
        r for r in report.for_entry("A-completion-claim-unsupported") if r.call_id == "CALL-09"
    )
    assert result.verdict == "unsupported"
    assert any("event 12" in fragment for fragment in result.evidence)


def test_w2_the_control_turning_the_ordering_rule_off_passes_that_call() -> None:
    """The other side of the same fixture, driven from the rubric.

    With `require_result_before_claim` false, CALL-09's later success supports
    the earlier claim and the call passes -- which is the behavior W2
    describes. The parameter is the difference, and it is in the rubric.
    """
    document = yaml.safe_load(RUBRIC_PATH.read_text(encoding="utf-8"))
    for entry in document["entries"]:
        if entry["id"] == "A-completion-claim-unsupported":
            entry["params"]["require_result_before_claim"] = False
    relaxed = parse_rubric(yaml.safe_dump(document), build_registry().keys())

    result = next(
        r
        for r in _run(relaxed).for_entry("A-completion-claim-unsupported")
        if r.call_id == "CALL-09"
    )
    assert result.verdict == "supported", (
        "turning the ordering rule off did not change CALL-09's verdict, so the check is "
        "not reading `require_result_before_claim` from the entry"
    )


def test_w10_a_state_cleared_before_the_action_is_not_a_violation() -> None:
    """The later-resolution half, planted on CALL-01.

    W10 was an unresolved-precondition correlation that ignored ordering and
    later resolution: a variable set, later re-set, then used successfully
    still reported a violation. A STATE event clearing `exchange_eligible`
    between the block and the invocation must clear the violation with it.
    """
    entry = _rubric().by_id("A-action-against-blocking-state")
    live = next(c for c in _contexts() if c.call_id == "CALL-01")
    assert run_entry(entry, live, PROVENANCE, build_registry()).verdict == "blocked"

    source = (TRANSCRIPTS / "CALL-01.txt").read_text(encoding="utf-8")
    assert " 12 |" in source and "exchange_eligible := false" in source, (
        "CALL-01 no longer carries the state event this control edits"
    )
    cleared = source.replace("exchange_eligible := false", "exchange_eligible := true", 1)
    patched = REPO_ROOT / "build" / "w10-control-CALL-01.txt"
    patched.parent.mkdir(parents=True, exist_ok=True)
    patched.write_text(cleared, encoding="utf-8")
    try:
        context = build_context(
            parse_call(patched), load_policies(POLICIES), policy_tool=POLICY_TOOL
        )
        result = run_entry(entry, context, PROVENANCE, build_registry())
        assert result.verdict != "blocked", (
            "the gate variable no longer says false at the moment of the invocation and the "
            "check still reports a violation, which is W10"
        )
    finally:
        patched.unlink(missing_ok=True)


# --------------------------------------------------------------------------
# W3: resolve to a single action or refuse
# --------------------------------------------------------------------------


def _ambiguous_exchange() -> Rubric:
    """The shipped rubric with `exchange` resolving to two invoked tools.

    W3's shape: two similarly-named actions, one succeeding and one failing.
    Two design calls reach it -- CALL-01 and CALL-09 -- and they differ in
    whether anything else in the call was found, which is what the two controls
    below are about.
    """
    document = yaml.safe_load(RUBRIC_PATH.read_text(encoding="utf-8"))
    for entry in document["entries"]:
        if entry["id"] == "A-completion-claim-unsupported":
            entry["params"]["topics"]["exchange"]["action_tools"] = [
                "exchange_tickets",
                "find_performance",
            ]
    return parse_rubric(yaml.safe_dump(document), build_registry().keys())


def test_w3_a_topic_resolving_to_two_invoked_tools_is_unevaluable_not_disjoined() -> None:
    """Planted, because the corpus contains no ambiguous topic.

    W3 is two similarly-named actions with one success and one failure
    producing a false pass on an absolute gate. Declaring both tools on one
    topic reproduces the ambiguity; the check refuses and names both, and the
    result carries the missing-reference identifier its status requires.
    """
    result = next(
        r
        for r in _run(_ambiguous_exchange()).for_entry("A-completion-claim-unsupported")
        if r.call_id == "CALL-09"
    )
    assert result.status is Status.UNEVALUABLE
    assert result.verdict is None
    assert result.missing_ground_truth == "topic:exchange"
    assert result.detail is not None
    assert "exchange_tickets" in result.detail and "find_performance" in result.detail


def test_a_refused_topic_does_not_discard_what_the_other_topics_found() -> None:
    """The refusal is of the topic, not of the call.

    CALL-01 claims two topics: `exchange` at events 16 and 18, and
    `confirmation` at event 16. Declaring a second action tool on `exchange`
    makes that topic ambiguous and refusable -- and the `confirmation` finding
    has nothing to do with it. Returning `unevaluable` the moment one topic
    could not be resolved threw a real violation away, on an absolute gate.

    CALL-09 is the other half and is asserted above: there the only claim *is*
    the ambiguous topic, so refusing it leaves nothing and the call is
    unevaluable. Both calls run under the same mutation, which is what makes
    this a difference in what the calls contain rather than in what was asked.
    """
    baseline = next(
        r for r in _run().for_entry("A-completion-claim-unsupported") if r.call_id == "CALL-01"
    )
    assert baseline.verdict == "unsupported"
    assert len(baseline.evidence) == 3, baseline.evidence

    result = next(
        r
        for r in _run(_ambiguous_exchange()).for_entry("A-completion-claim-unsupported")
        if r.call_id == "CALL-01"
    )
    assert result.status is Status.APPLICABLE, (
        "one ambiguous topic still discards the violations the others found"
    )
    assert result.verdict == "unsupported"
    surviving = [line for line in result.evidence if "claims 'confirmation'" in line]
    assert len(surviving) == 1, f"the confirmation finding was lost: {result.evidence}"
    assert not any("no exchange_tickets result" in line for line in result.evidence), (
        "the ambiguous topic produced a violation anyway, which is the disjunction W3 names"
    )
    refused = [line for line in result.evidence if "refused rather than disjoined" in line]
    assert len(refused) == 2, (
        "the refusal is reported once per claim, so both exchange claims should say they were "
        f"skipped rather than judged: {result.evidence}"
    )


# --------------------------------------------------------------------------
# Every parameter is read, and mutating one moves a verdict
# --------------------------------------------------------------------------


def test_no_entry_declares_a_parameter_its_check_does_not_read() -> None:
    """D109, over the shipped rubric.

    `validate_params_consumed` runs **outside** the engine's `try`, so an
    unread parameter raises `UnreadParameterError` and stops the run rather
    than producing a result. This asserted `not errored` instead -- a different
    property with a different mechanism, since a check that raises *is* caught
    and does become `errored`. The test did catch the case, in that the
    exception failed it, but it caught it the way an unhandled crash catches
    anything, and the message a reader got named neither the entry nor the
    parameter.
    """
    try:
        report = _run()
    except UnreadParameterError as unread:
        pytest.fail(f"an entry declares a parameter its check never reads: {unread}")
    assert report.results


def test_no_check_raises_on_any_design_call() -> None:
    """The other property the test above was carrying.

    An exception out of a check is caught and becomes `status: errored`, which
    is a result rather than a stopped run -- so unlike the unread-parameter
    guard, nothing about it is visible unless something looks. This looks.
    """
    report = _run()
    broken = [
        (r.entry_id, r.call_id, r.detail) for r in report.results if r.status is Status.ERRORED
    ]
    assert not broken, "checks raised on:\n  " + "\n  ".join(map(str, broken))


@pytest.mark.parametrize(
    ("entry_id", "path", "value"),
    [
        ("A-completion-claim-unsupported", ("success_statuses",), ["retrieved"]),
        ("A-completion-claim-unsupported", ("fold_case",), False),
        ("A-action-against-blocking-state", ("gates", "exchange", "blocking_value"), "true"),
        # `refused_precondition` rather than `timeout`: CALL-05 also re-issues
        # after a timeout, so that mutation moves the evidence and leaves the
        # firing set where it was. This one moves the set, to CALL-03 and
        # CALL-09 -- the two calls that re-issue after supplying the missing
        # precondition, which is why only `refused_ineligible` is declared.
        ("A-terminal-refusal-retried", ("terminal_statuses",), ["refused_precondition"]),
    ],
)
def test_mutating_a_declared_parameter_moves_a_verdict(
    entry_id: str, path: tuple[str, ...], value: Any
) -> None:
    """The criterion, per parameter rather than once.

    Each mutation is applied to the shipped rubric and the whole design set is
    re-run; the set of calls the entry fires on must change. A parameter no
    mutation moves is a parameter the check is not reading, whatever the YAML
    beside it says.
    """
    before = _violating_calls(_run(), entry_id)

    document = yaml.safe_load(RUBRIC_PATH.read_text(encoding="utf-8"))
    for entry in document["entries"]:
        if entry["id"] != entry_id:
            continue
        target = entry["params"]
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = copy.deepcopy(value)
    mutated = parse_rubric(yaml.safe_dump(document), build_registry().keys())

    after = _violating_calls(_run(mutated), entry_id)
    assert before != after, (
        f"changing {'.'.join(path)} on {entry_id} left every verdict where it was, so the "
        "check is not reading it from the rubric"
    )


def test_the_signal_list_is_read_from_the_rubric() -> None:
    """The criterion names a signal list specifically, so it gets its own case."""
    before = _violating_calls(_run(), "A-completion-claim-unsupported")

    document = yaml.safe_load(RUBRIC_PATH.read_text(encoding="utf-8"))
    for entry in document["entries"]:
        if entry["id"] == "A-completion-claim-unsupported":
            entry["params"]["topics"]["exchange"]["claim_signals"] = ["a phrase nobody says"]
    mutated = parse_rubric(yaml.safe_dump(document), build_registry().keys())

    after = _violating_calls(_run(mutated), "A-completion-claim-unsupported")
    assert "CALL-09" in before and "CALL-09" not in after, (
        "emptying the exchange signal list did not stop CALL-09 firing, so the signals are "
        "not coming from the rubric"
    )


# --------------------------------------------------------------------------
# The roll-up over the real corpus
# --------------------------------------------------------------------------


def test_the_design_set_fails_its_gates_because_it_is_seeded_to() -> None:
    """D105. A run that exited zero over this corpus would be the W11 fail-open.

    The tier that can fail a whole run has to be able to fail this run, or the
    demonstration demonstrates nothing.
    """
    rubric = _rubric()
    rollups = roll_up(_run(rubric), rubric)
    assert any(rollup.gate_failed for rollup in rollups), (
        "no gate fires over a corpus seeded with defects by construction"
    )
    for rollup in rollups:
        assert rollup.applicable + rollup.not_applicable + rollup.unevaluable + (
            rollup.errored + rollup.refused
        ) == len(_contexts()), f"{rollup.entry.id} produced a result for fewer than every call"


def _negative_result(entry: RubricEntry, evidence: tuple[str, ...]) -> Result:
    """A result at this entry's declared negative pole, with the given evidence.

    Built through `ResultBuilder` rather than by constructing a `Result`, so
    what is validated is what a check would actually produce.
    """
    builder = ResultBuilder(entry=entry, call_id="CALL-02", provenance=PROVENANCE)
    return builder.applicable(entry.negative, evidence)


def test_the_evidence_guard_fires_for_every_judged_scale_the_rubric_declares() -> None:
    """The criterion's valuable half: **each** of the judged scales, not one.

    It was split from the P2 criterion for a reason the specification records:
    the property belongs to the Result contract and is P2's, but at P2 the
    count of judged scales was zero and at P3 it was one -- so "not only for
    one" could not be asserted until the tier had its full population.

    W12 is what this costs when it is assumed: an evidence-on-failure invariant
    that covered two verdict strings and missed the negative pole of six of
    seven scales. Driven over every judged entry the rubric declares rather
    than over a list written here, so an entry added later is covered by the
    rule instead of by somebody remembering.
    """
    judged = _rubric().for_tier(CheckTier.JUDGE)
    assert len(judged) > 1, "one judged entry, so this asserts nothing the P3 criterion did not"

    poles = set()
    for entry in judged:
        poles.add(entry.negative)
        with pytest.raises(NegativePoleWithoutEvidenceError) as caught:
            validate_result(_negative_result(entry, ()), entry)
        assert caught.value.entry_id == entry.id
        # And the same verdict WITH evidence is fine, so what fires is the
        # empty list rather than the verdict.
        validate_result(_negative_result(entry, ("[T1] agent: something",)), entry)

    assert len(poles) > 1, (
        f"every judged entry declares the same negative pole ({poles}), so a guard keyed to "
        "that one literal would pass this test while covering nothing else"
    )
