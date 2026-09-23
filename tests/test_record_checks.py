"""Records against themselves, and the narrowing that only running found.

A comparison of the context record against any tool result carrying
`door_time` fires on CALL-01 and CALL-09, where `find_performance` returns a
*different* performance and a different door time is the point of the call.
`fetch_event_details` returns the same event by id. The tools are declared per
entry for that reason, and the mutation below puts `find_performance` back and
watches the two false positives arrive.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Final

import pytest
import yaml

from harness.checks import build_registry
from harness.core.context import CheckContext, build_context, state_writes
from harness.core.engine import run, run_entry
from harness.core.findings import load_findings
from harness.core.result import Provenance, Result, Status
from harness.core.rubric import CheckTier, Rubric, load_rubric, parse_rubric
from harness.corpus.policies import load_policies
from harness.corpus.text_adapter import parse_call

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
RUBRIC_PATH: Final[Path] = REPO_ROOT / "rubric.yaml"
TRANSCRIPTS: Final[Path] = REPO_ROOT / "corpus" / "transcripts"
POLICIES: Final[Path] = REPO_ROOT / "corpus" / "policies"
FINDINGS: Final[Path] = REPO_ROOT / "corpus" / "findings.yaml"
POLICY_TOOL: Final[str] = "fetch_policy"

PROVENANCE: Final[Provenance] = Provenance(
    rubric_version="1", corpus_version="test", artifact_hash="0" * 64
)

EXPECTED_FIRING: Final[dict[str, tuple[frozenset[str], tuple[str, ...]]]] = {
    "A-amount-inconsistent-with-band": (frozenset({"CALL-02"}), ("F-12",)),
    "A-record-fields-disagree": (frozenset({"CALL-08"}), ("F-29", "F-30")),
    "A-timestamp-ordering-violated": (frozenset({"CALL-19"}), ("F-83",)),
    "A-repeated-request-with-no-record": (frozenset({"CALL-12"}), ("F-69", "F-70")),
    "A-retry-without-deduplication": (frozenset({"CALL-05"}), ("F-54",)),
}


def _contexts() -> list[CheckContext]:
    policies = load_policies(POLICIES)
    return [
        build_context(parse_call(path), policies, policy_tool=POLICY_TOOL)
        for path in sorted(TRANSCRIPTS.glob("*.txt"))
    ]


def _rubric() -> Rubric:
    return load_rubric(RUBRIC_PATH, build_registry().keys())


def _run(rubric: Rubric | None = None) -> Any:
    return run(
        rubric or _rubric(), _contexts(), PROVENANCE, build_registry(), tier=CheckTier.ASSERT
    )


def _firing(report: Any, entry_id: str, rubric: Rubric | None = None) -> set[str]:
    entry = (rubric or _rubric()).by_id(entry_id)
    return {
        result.call_id for result in report.for_entry(entry_id) if result.verdict == entry.negative
    }


def _mutate(entry_id: str, path: tuple[str, ...], value: Any) -> Rubric:
    document = yaml.safe_load(RUBRIC_PATH.read_text(encoding="utf-8"))
    for entry in document["entries"]:
        if entry["id"] != entry_id:
            continue
        target = entry["params"]
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = copy.deepcopy(value)
    return parse_rubric(yaml.safe_dump(document), build_registry().keys())


@pytest.mark.parametrize("entry_id", sorted(EXPECTED_FIRING))
def test_each_record_entry_fires_on_exactly_its_seeded_calls(entry_id: str) -> None:
    expected, findings = EXPECTED_FIRING[entry_id]
    firing = _firing(_run(), entry_id)
    assert firing == set(expected), (
        f"{entry_id} fires on {sorted(firing)}; the gold set puts {sorted(findings)} on "
        f"{sorted(expected)}"
    )


def test_the_firing_table_names_the_findings_its_entries_trace() -> None:
    for entry_id, (_, findings) in EXPECTED_FIRING.items():
        assert set(findings) == set(_rubric().by_id(entry_id).traces_to)


def test_every_traced_finding_is_on_a_call_the_entry_fires_on() -> None:
    """Every finding an entry traces is on a call that entry fires on.

    Not a control: it restores no defect and requires no verdict to move. It is
    a consistency assertion between two declarations, and it matched the control
    naming idiom only because `fires_on` ends its name.

    It carries a floor because it did not, and passed over an empty table --
    the shape its neighbors in this file guard against and this one did not.
    """
    by_id = {finding.id: finding for finding in load_findings(FINDINGS)}
    compared = 0
    for entry_id, (expected, findings) in EXPECTED_FIRING.items():
        for finding in findings:
            compared += 1
            assert by_id[finding].call_ref in expected, (
                f"{entry_id} traces {finding} on {by_id[finding].call_ref}, a call it does "
                "not fire on"
            )
    assert compared >= 7, (
        f"only {compared} traced findings were compared; EXPECTED_FIRING has stopped "
        "listing them and this check is passing over an empty table"
    )


# --------------------------------------------------------------------------
# The narrowing that running found
# --------------------------------------------------------------------------


def test_including_the_tool_that_returns_a_different_event_adds_two_false_positives() -> None:
    """`find_performance` answers "what else is on", so its door time differs by
    design. CALL-01 and CALL-09 both exchange into another performance, and a
    check that compared their results against the booking's context would
    report the exchange itself as a data defect."""
    entry_id = "A-record-fields-disagree"
    assert _firing(_run(), entry_id) == {"CALL-08"}

    widened = _mutate(entry_id, ("tools",), ["fetch_event_details", "find_performance"])
    firing = _firing(_run(widened), entry_id, widened)
    assert {"CALL-01", "CALL-09"} <= firing, (
        "including find_performance no longer produces the false positives this narrowing "
        "exists to avoid, so the narrowing is describing something that cannot happen"
    )


def test_call_19_is_a_real_negative_and_not_a_call_the_check_skipped() -> None:
    """CALL-19 fetches the same event and its fields agree, so the check runs
    there and comes out clean. That is what makes it a negative instance rather
    than a declared absence."""
    result = next(r for r in _run().for_entry("A-record-fields-disagree") if r.call_id == "CALL-19")
    assert result.status is Status.APPLICABLE
    assert result.verdict == "agree"


def test_the_repeated_request_check_turns_on_order() -> None:
    """CALL-20 asks for the booking reference before looking it up.

    Same sentence, opposite meaning, and the only difference is which event
    came first. It is this entry's negative instance for that reason, and the
    result is `applicable` rather than `not_applicable`.
    """
    report = _run()
    call_20 = next(
        r for r in report.for_entry("A-repeated-request-with-no-record") if r.call_id == "CALL-20"
    )
    assert call_20.status is Status.APPLICABLE
    assert call_20.verdict == "asked_once"

    call_12 = next(
        r for r in report.for_entry("A-repeated-request-with-no-record") if r.call_id == "CALL-12"
    )
    assert call_12.verdict == "asked_again"
    assert len(call_12.evidence) == 2, call_12.evidence
    assert any("lookup_booking" in fragment for fragment in call_12.evidence)
    assert any("holder_confirmed" in fragment for fragment in call_12.evidence)


def test_the_question_tier_entry_reports_and_cannot_fail_the_run() -> None:
    """F-54 is `tier: question` -- for whoever owns the system rather than a
    defect charged against this call -- so its gate is a rate at zero.

    A gate that failed the run would be charging it. The entry still fires and
    still appears in the breakdown; what it does not do is take the run down.
    """
    from harness.core.engine import roll_up

    rubric = _rubric()
    rollup = next(
        r for r in roll_up(_run(rubric), rubric) if r.entry.id == "A-retry-without-deduplication"
    )
    assert rollup.violations == 1
    assert rollup.gate_failed is False, (
        "a question-tier entry is failing the run, which charges the call with something "
        "the transcript cannot resolve"
    )


def test_a_deduplication_key_would_clear_the_retry() -> None:
    """The parameter is read, shown by declaring an argument the call carries.

    `booking` is on every issue_refund invocation, so declaring it as a
    deduplication argument silences the entry -- which is the wrong rubric and
    the right proof that the list is consulted.
    """
    entry_id = "A-retry-without-deduplication"
    assert _firing(_run(), entry_id) == {"CALL-05"}
    lenient = _mutate(entry_id, ("deduplication_arguments",), ["booking"])
    assert _firing(_run(lenient), entry_id, lenient) == set()


def test_the_band_fractions_are_read_from_the_rubric() -> None:
    entry_id = "A-amount-inconsistent-with-band"
    assert _firing(_run(), entry_id) == {"CALL-02"}

    # 91.50 against a base of 85.00 is 1.0764...; a band declaring that fraction
    # makes the call consistent, which nothing but reading the rubric could do.
    widened = _mutate(
        entry_id,
        ("bands", "partial_50"),
        {"fraction": "1.0764705882352941", "of": "ticket_price_total"},
    )
    assert _firing(_run(widened), entry_id, widened) == set()


def test_an_undeclared_band_is_unevaluable_rather_than_a_pass() -> None:
    """A band the entry has no fraction for is a gap in the rubric, not a clean
    call, and the result names it."""
    mutated = _mutate(
        "A-amount-inconsistent-with-band",
        ("bands",),
        {"full": {"fraction": "1.0", "of": "ticket_price_total"}},
    )
    result = next(
        r
        for r in _run(mutated).for_entry("A-amount-inconsistent-with-band")
        if r.call_id == "CALL-02"
    )
    assert result.status is Status.UNEVALUABLE
    assert result.missing_ground_truth == "band:partial_50"


def test_the_ordering_check_names_which_pair_it_compared() -> None:
    result = next(
        r for r in _run().for_entry("A-timestamp-ordering-violated") if r.call_id == "CALL-19"
    )
    assert result.verdict == "impossible"
    assert "rescheduled_at" in result.evidence[0] and "door_time" in result.evidence[0]


# --------------------------------------------------------------------------
# Timestamps are instants, not strings
# --------------------------------------------------------------------------

_ORDERING_ENTRY: Final[str] = "A-timestamp-ordering-violated"
_DOOR: Final[str] = "door_time=2027-04-24T02:30:00Z;"
_RESCHEDULE: Final[str] = "rescheduled_at=2027-04-28T10:00:00Z"


def _ordering_result(door: str, reschedule: str) -> Result:
    """The entry's verdict on CALL-19 with its ordered pair replaced.

    CALL-19 is the only design call carrying both halves of a declared
    ordering, so every control for this entry is a plant on it. Its own values
    are both `Z`-suffixed and lexicographic order happens to agree with
    chronological order there, which is why the defect was silent.
    """
    source = (TRANSCRIPTS / "CALL-19.txt").read_text(encoding="utf-8")
    assert source.count(_DOOR) == 1 and source.count(_RESCHEDULE) == 1, (
        "CALL-19 no longer carries the pair these controls edit"
    )
    planted = source.replace(_DOOR, f"door_time={door};", 1).replace(
        _RESCHEDULE, f"rescheduled_at={reschedule}", 1
    )
    patched = REPO_ROOT / "build" / "ordering-control-CALL-19.txt"
    patched.parent.mkdir(parents=True, exist_ok=True)
    patched.write_text(planted, encoding="utf-8")
    try:
        context = build_context(
            parse_call(patched), load_policies(POLICIES), policy_tool=POLICY_TOOL
        )
        return run_entry(_rubric().by_id(_ORDERING_ENTRY), context, PROVENANCE, build_registry())
    finally:
        patched.unlink(missing_ok=True)


def test_an_ordered_pair_written_in_two_offsets_is_not_a_violation() -> None:
    """The false violation the string comparison produced, planted.

    `2027-04-24T02:30:00Z` is 02:30 UTC and `2027-04-24T00:30:00-05:00` is
    05:30 UTC, so the door time is genuinely later than the reschedule. Sorted
    as text the door time is *smaller*, because `0` precedes `2` three
    characters in, and the check reported an impossible ordering on an absolute
    gate.
    """
    door, reschedule = "2027-04-24T00:30:00-05:00", "2027-04-24T02:30:00Z"
    assert door < reschedule, "the pair no longer sorts the wrong way as text"
    assert _ordering_result(door, reschedule).verdict == "ordered", (
        "an ordering that holds as instants is reported impossible, which is the string "
        "comparison assuming both timestamps carry the same offset"
    )


def test_a_reversed_pair_hidden_by_the_offsets_is_caught() -> None:
    """The other direction: a real violation the string comparison missed.

    `2027-04-24T20:00:00-07:00` is 03:00 UTC on the 25th, after a door time of
    01:00 UTC on the 25th. As text the reschedule sorts first, because `24`
    precedes `25`, so nothing fired.
    """
    door, reschedule = "2027-04-25T01:00:00Z", "2027-04-24T20:00:00-07:00"
    assert reschedule < door, "the pair no longer sorts the right way as text"
    assert _ordering_result(door, reschedule).verdict == "impossible", (
        "a reschedule made after the door time it set is not reported, because the offsets "
        "make it sort earlier as text"
    )


def test_a_timestamp_that_is_not_one_is_unevaluable_rather_than_ordered() -> None:
    """A value the check cannot read is a finding about the corpus, not a pass.

    W11 is the cost of the other choice: one value meaning both "no ground
    truth existed" and "nothing was wrong".
    """
    result = _ordering_result("2027-04-24T02:30:00Z", "shortly afterwards")
    assert result.status is Status.UNEVALUABLE
    assert result.verdict is None
    assert result.missing_ground_truth is not None
    assert "rescheduled_at" in result.missing_ground_truth


def test_an_offset_aware_timestamp_against_a_naive_one_is_unevaluable() -> None:
    """The pair the format spec's own word -- opaque -- allows, and which names
    no comparable instants at all."""
    result = _ordering_result("2027-04-24T02:30:00Z", "2027-04-28T10:00:00")
    assert result.status is Status.UNEVALUABLE
    assert result.detail is not None and "offset" in result.detail


# --------------------------------------------------------------------------
# Every write of the variable, not the last one
# --------------------------------------------------------------------------


def test_a_variable_set_between_the_asks_clears_it_even_if_set_again_after() -> None:
    """The false violation the last-write-wins comprehension produced.

    CALL-12 asks the holder question at event 22 and again at 24, and emits no
    state event at all -- which is the seeded finding. A state event planted
    *between* the asks answers the first question, so the repeat is no longer
    unrecorded; a second one after the last ask is what the old code saw
    instead, because a dict comprehension keeps only the final index.

    `holder_confirmed` is what the rubric entry declares, and `corpus/entities.md`
    declares it a state variable written in no transcript -- because this
    entry's finding *is* the absence of the write. That the register permits it
    is what makes this plant, and one day a real negative instance, authorable
    at all (D117).
    """
    entry = _rubric().by_id("A-repeated-request-with-no-record")
    live = next(c for c in _contexts() if c.call_id == "CALL-12")
    assert run_entry(entry, live, PROVENANCE, build_registry()).verdict == "asked_again"

    source = (TRANSCRIPTS / "CALL-12.txt").read_text(encoding="utf-8")
    between = " 23 |  1:39.618 |  1:40.318 | CALLER      | Yes."
    after = " 38 |  2:49.584 |  2:50.284 | AGENT       | Goodbye."
    assert source.count(between) == 1 and source.count(after) == 1, (
        "CALL-12 no longer carries the two events this control replaces"
    )
    planted = source.replace(
        between, " 23 |  1:39.618 |  1:39.618 | STATE       | holder_confirmed := true", 1
    ).replace(after, " 38 |  2:49.584 |  2:49.584 | STATE       | holder_confirmed := true", 1)

    patched = REPO_ROOT / "build" / "state-history-control-CALL-12.txt"
    patched.parent.mkdir(parents=True, exist_ok=True)
    patched.write_text(planted, encoding="utf-8")
    try:
        context = build_context(
            parse_call(patched), load_policies(POLICIES), policy_tool=POLICY_TOOL
        )
        assert state_writes(context.events)["holder_confirmed"] == (23, 38), (
            "the plant did not produce the two writes this control depends on"
        )
        result = run_entry(entry, context, PROVENANCE, build_registry())
        assert not any("holder_confirmation" in evidence for evidence in result.evidence), (
            "a state event between the two asks does not clear the repeat, which is the "
            "comprehension keeping only the write after the last ask"
        )
    finally:
        patched.unlink(missing_ok=True)
