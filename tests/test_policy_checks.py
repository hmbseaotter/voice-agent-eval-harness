"""Policy: the grounding criterion's fixture, and the clauses nobody applied.

The specification's grounding criterion asks for a fixture where **the only
supporting value lives in a retrieved clause**. That fixture is in the corpus
rather than invented here: `refund.v1` 2.4 states the booking fee is
non-refundable, it is among the fourteen clauses returned to CALL-02 at event
12, the agent promises the fee back at event 14, and no `POLICY` event cites
it. The criterion added at D104 is the other half -- that agent speech is not
admitted as evidence -- and it is asserted here by removing the clause from the
ground truth and watching the verdict move, then by adding the supporting
sentence to speech alone and watching it not.
"""

from __future__ import annotations

import copy
import dataclasses
from pathlib import Path
from typing import Any, Final

import pytest
import yaml

from harness.checks import build_registry
from harness.core.context import CheckContext, build_context
from harness.core.engine import run, run_entry
from harness.core.result import Provenance, Status
from harness.core.rubric import CheckTier, Rubric, load_rubric, parse_rubric
from harness.corpus.policies import load_policies, parse_policy
from harness.corpus.text_adapter import parse_call

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
RUBRIC_PATH: Final[Path] = REPO_ROOT / "rubric.yaml"
TRANSCRIPTS: Final[Path] = REPO_ROOT / "corpus" / "transcripts"
POLICIES: Final[Path] = REPO_ROOT / "corpus" / "policies"
POLICY_TOOL: Final[str] = "fetch_policy"

PROVENANCE: Final[Provenance] = Provenance(
    rubric_version="1", corpus_version="test", artifact_hash="0" * 64
)

EXPECTED_FIRING: Final[dict[str, tuple[frozenset[str], tuple[str, ...]]]] = {
    "A-governing-clause-not-applied": (frozenset({"CALL-02"}), ("F-09", "F-10", "F-50")),
    "A-rule-stated-without-retrieval": (frozenset({"CALL-06", "CALL-07"}), ("F-26", "F-28")),
    "A-tool-argument-contradicts-applied-clause": (frozenset({"CALL-04"}), ("F-18",)),
}


def _contexts() -> list[CheckContext]:
    policies = load_policies(POLICIES)
    return [
        build_context(parse_call(path), policies, policy_tool=POLICY_TOOL)
        for path in sorted(TRANSCRIPTS.glob("*.txt"))
    ]


def _rubric() -> Rubric:
    return load_rubric(RUBRIC_PATH, build_registry().keys())


def _run(rubric: Rubric | None = None, contexts: list[CheckContext] | None = None) -> Any:
    return run(
        rubric or _rubric(),
        contexts if contexts is not None else _contexts(),
        PROVENANCE,
        build_registry(),
        tier=CheckTier.ASSERT,
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


def _call_02(policies: dict[str, Any] | None = None) -> CheckContext:
    return build_context(
        parse_call(TRANSCRIPTS / "CALL-02.txt"),
        policies if policies is not None else load_policies(POLICIES),
        policy_tool=POLICY_TOOL,
    )


@pytest.mark.parametrize("entry_id", sorted(EXPECTED_FIRING))
def test_each_policy_entry_fires_on_exactly_its_seeded_calls(entry_id: str) -> None:
    expected, findings = EXPECTED_FIRING[entry_id]
    firing = _firing(_run(), entry_id)
    assert firing == set(expected), (
        f"{entry_id} fires on {sorted(firing)}; the gold set puts {sorted(findings)} on "
        f"{sorted(expected)}"
    )


def test_the_firing_table_names_the_findings_its_entries_trace() -> None:
    for entry_id, (_, findings) in EXPECTED_FIRING.items():
        assert set(findings) == set(_rubric().by_id(entry_id).traces_to)


# --------------------------------------------------------------------------
# The grounding criterion, both halves
# --------------------------------------------------------------------------


def test_the_only_supporting_value_lives_in_a_retrieved_clause() -> None:
    """The criterion's fixture, taken from the corpus rather than invented.

    `refund.v1` 2.4 is the clause the verdict rests on. It is in the document
    returned at event 12, it is in this call's ground truth, and it is in no
    event, no context variable and no tool result -- so removing it from the
    policy document has to change the verdict, and nothing else can.
    """
    entry = _rubric().by_id("A-governing-clause-not-applied")
    registry = build_registry()

    live = run_entry(entry, _call_02(), PROVENANCE, registry)
    assert live.verdict == "unapplied"
    assert any("booking_fee" in fragment for fragment in live.evidence)

    clause_key = "refund.v1 2.4"
    supporting = [fact for fact in _call_02().ground_truth.keyed(clause_key)]
    assert supporting, "refund.v1 2.4 is not in this call's ground truth"
    assert all("fee" in fact.text.casefold() for fact in supporting)

    contexts = _call_02()
    assert not any(
        "non-refundable" in fact.text.casefold()
        for fact in contexts.ground_truth.facts
        if fact.key != clause_key and not fact.key.startswith("refund.v1")
    ), (
        "the supporting statement is reachable outside the retrieved clauses, so this "
        "is not the fixture the criterion describes"
    )


def _refund_without(*clauses: str) -> dict[str, Any]:
    """The policy set with clauses renumbered out of `refund.v1`."""
    source = (POLICIES / "refund.v1.md").read_text(encoding="utf-8")
    for clause in clauses:
        marker = f"**{clause}**"
        assert marker in source, f"refund.v1 no longer states {clause}; this control is stale"
        source = source.replace(marker, f"**9{clause}**", 1)
    policies = dict(load_policies(POLICIES))
    policies["refund.v1"] = parse_policy("refund.v1", source)
    return policies


def test_removing_every_governing_clause_makes_the_result_unevaluable() -> None:
    """The clauses are load-bearing, shown by taking them away.

    With 2.4 and 3.2 both gone from `refund.v1` the entry can ask neither of its
    questions and says so -- `unevaluable`, naming a missing reference -- rather
    than reporting a pass. That is the difference between "the agent applied the
    clause" and "there was no clause to apply".
    """
    entry = _rubric().by_id("A-governing-clause-not-applied")
    result = run_entry(entry, _call_02(_refund_without("2.4", "3.2")), PROVENANCE, build_registry())
    assert result.status is Status.UNEVALUABLE
    assert result.missing_ground_truth is not None
    assert result.missing_ground_truth.startswith("refund.v1:")
    assert result.verdict is None


def test_a_topic_whose_clause_is_missing_does_not_discard_the_other_topics() -> None:
    """The refusal is of the topic, not of the call.

    CALL-02 violates two topics: `booking_fee`, which names clause 2.4, and
    `settlement_timing`, which names 3.2. Renumbering 2.4 out of the document
    makes the rubric name a clause that is not there -- a finding against the
    rubric -- and it says nothing about 3.2. Returning `unevaluable` the moment
    one topic could not be asked took a real, unrelated violation with it.
    """
    entry = _rubric().by_id("A-governing-clause-not-applied")
    baseline = run_entry(entry, _call_02(load_policies(POLICIES)), PROVENANCE, build_registry())
    assert baseline.verdict == "unapplied" and len(baseline.evidence) == 2, baseline.evidence

    result = run_entry(entry, _call_02(_refund_without("2.4")), PROVENANCE, build_registry())
    assert result.status is Status.APPLICABLE, (
        "one topic naming an absent clause still discards what the others found"
    )
    assert result.verdict == "unapplied"
    assert any("3.2" in line for line in result.evidence), (
        f"the settlement_timing finding was lost: {result.evidence}"
    )
    assert any("does not contain them" in line for line in result.evidence), (
        "the refusal is not reported anywhere, so a reader cannot tell the topic was skipped"
    )


def test_adding_the_supporting_sentence_to_speech_alone_does_not_move_the_verdict() -> None:
    """The half the specification's own criterion cannot see (D104).

    The clause's text is planted into an agent turn and into nothing else. A
    grounding blob that concatenated speech alongside the three ground-truth
    sources would resolve the claim and the verdict would move. It must not.
    """
    entry = _rubric().by_id("A-governing-clause-not-applied")
    registry = build_registry()
    policies = load_policies(POLICIES)
    clause = policies["refund.v1"].text_of("2.4")

    call = parse_call(TRANSCRIPTS / "CALL-02.txt")
    planted = dataclasses.replace(
        call,
        events=tuple(
            dataclasses.replace(event, body=f"{event.body} {clause}")
            if event.index == 14
            else event
            for event in call.events
        ),
    )
    context = build_context(planted, policies, policy_tool=POLICY_TOOL)
    assert clause.casefold() in " ".join(c.text for c in context.subject.agent_turns).casefold(), (
        "the plant did not reach the agent turn"
    )

    before = run_entry(entry, _call_02(), PROVENANCE, registry)
    after = run_entry(entry, context, PROVENANCE, registry)
    assert after.verdict == before.verdict == "unapplied", (
        "putting the clause's own words into an agent turn changed the verdict, so the "
        "check is resolving a claim against the claim that made it"
    )
    # The verdict alone cannot see this, and asserting it alone was the defect.
    # CALL-02 violates on 2.4 AND on 3.2, so resolving 2.4 wrongly leaves the
    # verdict at `unapplied` either way -- masked by its neighbor. Measured when
    # this was written: with a grounding blob that counts a clause as applied
    # when its text is spoken, the verdict did not move and the evidence went
    # from two findings to one, with 2.4 silently gone.
    assert after.evidence == before.evidence, (
        "the clause's own words in an agent turn changed what the check found, so it is "
        f"resolving a claim against the claim that made it: {before.evidence} -> "
        f"{after.evidence}"
    )
    assert any("2.4" in evidence for evidence in after.evidence), (
        "the 2.4 finding is gone from the evidence while the verdict stayed `unapplied`, "
        "which is the shape a verdict-only assertion cannot see"
    )


# --------------------------------------------------------------------------
# The narrow signal, and why it is narrow
# --------------------------------------------------------------------------


def test_the_settlement_signal_avoids_the_call_that_states_the_clause_correctly() -> None:
    """ "back on the card" appears in CALL-05 too, where the agent correctly
    says five business days. A signal that fires on correct behavior is a false
    positive on an absolute gate -- the tier that fails the whole run."""
    entry_id = "A-governing-clause-not-applied"
    assert _firing(_run(), entry_id) == {"CALL-02"}

    loose = _mutate(
        entry_id, ("topics", "settlement_timing", "speech_signals"), ["back on the card"]
    )
    assert "CALL-05" in _firing(_run(loose), entry_id, loose), (
        "the wider signal no longer reaches CALL-05, so this contrast is describing "
        "something that cannot happen"
    )


def test_the_refund_window_topic_is_what_gives_this_entry_a_true_negative() -> None:
    """CALL-04 says "fourteen days ... a full refund" having applied 2.1.

    Without a topic that fires where the clause WAS applied, the entry would
    only ever be observed firing, and D107's declared-absence branch would be
    the only honest answer available.
    """
    report = _run()
    result = next(
        r for r in report.for_entry("A-governing-clause-not-applied") if r.call_id == "CALL-04"
    )
    assert result.status is Status.APPLICABLE
    assert result.verdict == "applied"


def test_the_rule_check_reports_both_reasons_and_each_is_separable() -> None:
    """No retrieval and a contradicting flag are two independent reasons.

    A reader fixing one should see the other, so both are in the evidence and
    the mutation removing the contradiction leaves the retrieval reason behind.
    """
    entry_id = "A-rule-stated-without-retrieval"
    result = next(r for r in _run().for_entry(entry_id) if r.call_id == "CALL-06")
    assert result.verdict == "ungrounded"
    assert "never retrieved" in result.evidence[0]
    assert "resale_eligible" in result.evidence[0]

    document = yaml.safe_load(RUBRIC_PATH.read_text(encoding="utf-8"))
    for entry in document["entries"]:
        if entry["id"] == entry_id:
            del entry["params"]["rules"]["resale"]["contradicted_by"]
    narrower = parse_rubric(yaml.safe_dump(document), build_registry().keys())
    only_retrieval = next(r for r in _run(narrower).for_entry(entry_id) if r.call_id == "CALL-06")
    assert only_retrieval.verdict == "ungrounded"
    assert "resale_eligible" not in only_retrieval.evidence[0]


def test_the_injection_pair_reaches_the_same_verdict() -> None:
    """CALL-07 is CALL-06 with the injected sentence removed.

    D7's acceptance criterion is that the injected transcript produces the same
    verdict as the clean one. That is a P3 property for the judged tier, and it
    costs nothing to assert here for a deterministic entry that fires on both.
    """
    report = _run()
    verdicts = {
        r.call_id: r.verdict
        for r in report.for_entry("A-rule-stated-without-retrieval")
        if r.call_id in {"CALL-06", "CALL-07"}
    }
    assert verdicts == {"CALL-06": "ungrounded", "CALL-07": "ungrounded"}


def test_the_band_constraint_engages_only_where_its_clause_was_applied() -> None:
    """CALL-09 checks its own band and would pass, but retrieves no policy at
    all -- so the constraint never engages and the answer is not_applicable.

    That is why this entry declares no negative instance, and asserting it here
    keeps the declaration honest rather than merely written down.
    """
    report = _run()
    call_09 = next(
        r
        for r in report.for_entry("A-tool-argument-contradicts-applied-clause")
        if r.call_id == "CALL-09"
    )
    assert call_09.status is Status.NOT_APPLICABLE
    assert _rubric().by_id("A-tool-argument-contradicts-applied-clause").negative_instance is None
