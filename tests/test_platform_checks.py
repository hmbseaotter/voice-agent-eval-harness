"""The platform-owned checks: dispositions, gates, state and lifecycle.

Every check in this family compares one part of the system's record against
another part of it and reads no agent speech at all. That is asserted here
rather than left to inspection, because the family's whole justification is
that a defect the agent cannot be blamed for still has to be detectable -- and
a check that reached for a spoken confirmation to decide whether a gate held
would be asking the subject under test to certify itself.

Firing sets are asserted as equality in both directions against the gold set,
so a check that started firing on a fourteenth call fails here rather than
quietly widening.
"""

from __future__ import annotations

import copy
import dataclasses
from pathlib import Path
from typing import Any, Final

import pytest
import yaml

from harness.checks import build_registry
from harness.core.context import CheckContext, build_context, state_writes
from harness.core.engine import run, run_entry
from harness.core.findings import load_findings
from harness.core.result import Provenance, Status
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

#: Where each platform entry must fire, and the findings it is there for.
#: Equality in both directions, so widening fails here.
EXPECTED_FIRING: Final[dict[str, tuple[frozenset[str], tuple[str, ...]]]] = {
    "A-reason-code-unsupported": (
        frozenset({"CALL-01", "CALL-05", "CALL-09"}),
        ("F-06", "F-25", "F-74"),
    ),
    "A-reason-code-understates-the-call": (frozenset({"CALL-03"}), ("F-73",)),
    "A-outcome-contradicted-by-results": (frozenset({"CALL-18"}), ("F-81",)),
    "A-precondition-satisfied-by-assertion": (
        frozenset({"CALL-03", "CALL-12"}),
        ("F-14", "F-46"),
    ),
    "A-gated-write-without-verification": (frozenset({"CALL-12", "CALL-18"}), ("F-75", "F-80")),
    "A-declared-state-never-recorded": (
        frozenset({"CALL-01", "CALL-12", "CALL-18"}),
        ("F-05", "F-46", "F-75"),
    ),
    "A-lifecycle-event-missing": (frozenset({"CALL-12"}), ("F-47", "F-72")),
    "A-duration-does-not-reconcile": (frozenset({"CALL-12"}), ("F-48",)),
    "A-system-ended-the-interaction": (frozenset({"CALL-05", "CALL-12"}), ("F-71", "F-72")),
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


# --------------------------------------------------------------------------
# Each entry fires exactly where the gold set says
# --------------------------------------------------------------------------


@pytest.mark.parametrize("entry_id", sorted(EXPECTED_FIRING))
def test_each_platform_entry_fires_on_exactly_its_seeded_calls(entry_id: str) -> None:
    expected, findings = EXPECTED_FIRING[entry_id]
    firing = _firing(_run(), entry_id)
    assert firing == set(expected), (
        f"{entry_id} fires on {sorted(firing)} and the gold set puts {sorted(findings)} on "
        f"{sorted(expected)}"
    )


def test_every_traced_finding_resolves_to_a_findings_row() -> None:
    """A `traces_to` naming nothing is a claim with no anchor.

    This is a P4 acceptance criterion and it costs nothing to hold from P2, so
    an entry added later cannot cite a finding id that does not exist.
    """
    known = {finding.id for finding in load_findings(FINDINGS)}
    unresolved = [
        (entry.id, finding)
        for entry in _rubric().entries
        for finding in entry.traces_to
        if finding not in known
    ]
    assert not unresolved, f"traces_to entries resolving to no findings row: {unresolved}"


def test_every_traced_finding_is_one_a_deterministic_check_could_catch() -> None:
    """A rubric entry in the deterministic tier tracing a `judge` finding would
    be claiming coverage the tier cannot deliver."""
    by_id = {finding.id: finding for finding in load_findings(FINDINGS)}
    wrong_tier = [
        (entry.id, finding, by_id[finding].detectable_by.value)
        for entry in _rubric().for_tier(CheckTier.ASSERT)
        for finding in entry.traces_to
        if by_id[finding].detectable_by.value != "assert"
    ]
    assert not wrong_tier, (
        "deterministic entries tracing findings the gold set does not classify as "
        f"assert-detectable: {wrong_tier}"
    )


def test_the_expected_firing_table_names_the_findings_its_entries_trace() -> None:
    """The table above is prose about the rubric, so it is checked against it."""
    for entry_id, (_, findings) in EXPECTED_FIRING.items():
        assert set(findings) == set(_rubric().by_id(entry_id).traces_to), (
            f"{entry_id}'s traces_to and this file's table disagree about which findings it is for"
        )


# --------------------------------------------------------------------------
# The family reads no speech
# --------------------------------------------------------------------------


def _scrubbed_contexts() -> list[CheckContext]:
    """Every call with every spoken turn replaced by one meaningless sentence.

    `dataclasses.replace` rather than reconstructing the event by field name:
    the second breaks silently when an event kind gains a field, and it would
    break by producing an event that is subtly not the one it replaced.
    """
    policies = load_policies(POLICIES)
    scrubbed: list[CheckContext] = []
    for path in sorted(TRANSCRIPTS.glob("*.txt")):
        call = parse_call(path)
        muted = tuple(
            dataclasses.replace(event, body="redacted")
            if event.citation_id.startswith("T")
            else event
            for event in call.events
        )
        scrubbed.append(
            build_context(
                dataclasses.replace(call, events=muted), policies, policy_tool=POLICY_TOOL
            )
        )
    return scrubbed


def test_no_platform_check_changes_its_verdict_when_speech_is_rewritten() -> None:
    """The seam keeps speech out of the ground truth; this asserts the family
    does not reach around it.

    Every agent and caller turn is replaced with a sentence carrying none of
    the corpus's vocabulary, and every platform entry must return exactly what
    it returned before. A check consulting a spoken confirmation to decide
    whether a gate held would move.
    """
    rubric = _rubric()
    before = _run(rubric)
    after = run(rubric, _scrubbed_contexts(), PROVENANCE, build_registry(), tier=CheckTier.ASSERT)
    for entry_id in EXPECTED_FIRING:
        assert _firing(before, entry_id) == _firing(after, entry_id), (
            f"{entry_id} changed its verdicts when every spoken turn was replaced, so it "
            "is reading speech -- which for a platform-owned check means asking the "
            "subject under test to certify itself"
        )


def test_the_scrub_does_move_a_check_that_reads_speech_by_design() -> None:
    """The control, and the reason the assertion above is not vacuous.

    `A-completion-claim-unsupported` reads speech deliberately: it locates the
    claim under test. If the scrub leaves that check where it was, the scrub is
    doing nothing and the comparison above is two identical runs.
    """
    rubric = _rubric()
    before = _firing(_run(rubric), "A-completion-claim-unsupported")
    after_report = run(
        rubric, _scrubbed_contexts(), PROVENANCE, build_registry(), tier=CheckTier.ASSERT
    )
    after = _firing(after_report, "A-completion-claim-unsupported")
    assert before, "the claim check fires nowhere, so this control has no baseline"
    assert before != after, (
        "scrubbing every spoken turn left the speech-reading check exactly where it was, "
        "so the scrub changes nothing and the platform assertion compares two identical runs"
    )


# --------------------------------------------------------------------------
# Parameters, mutated one at a time
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("entry_id", "path", "value", "expected"),
    [
        (
            "A-lifecycle-event-missing",
            ("required_system_events",),
            ["call.answered"],
            set(),
        ),
        (
            "A-duration-does-not-reconcile",
            ("tolerance_ms",),
            60_000,
            set(),
        ),
        (
            "A-system-ended-the-interaction",
            ("system_ended_reasons",),
            ["caller_hangup"],
            {
                "CALL-01", "CALL-02", "CALL-03", "CALL-04", "CALL-06", "CALL-07",
                "CALL-08", "CALL-09", "CALL-10", "CALL-11", "CALL-18", "CALL-19",
                "CALL-22",
            },
        ),
        (
            "A-declared-state-never-recorded",
            ("variables",),
            ["booking_reference"],
            {
                "CALL-01", "CALL-02", "CALL-03", "CALL-04", "CALL-05", "CALL-06",
                "CALL-07", "CALL-08", "CALL-09", "CALL-10", "CALL-11", "CALL-12",
                "CALL-18", "CALL-19", "CALL-20", "CALL-22",
            },
        ),
        (
            "A-precondition-satisfied-by-assertion",
            ("assertions",),
            {"difference_accepted": {"state_variables": ["difference_confirmed"]}},
            # CALL-22 joins CALL-09 here: it is the second design call whose
            # exchange carries `difference_accepted`, and the difference between
            # them is what the entry's own reason field says -- CALL-09 asks
            # after the attempt, CALL-22 asks before it. Neither records the
            # state, so a declaration naming one would report both.
            {"CALL-09", "CALL-22"},
        ),
    ],
)  # fmt: skip
def test_mutating_a_platform_parameter_moves_the_firing_set(
    entry_id: str, path: tuple[str, ...], value: Any, expected: set[str]
) -> None:
    """Each parameter its own case, and each with the set it should move to.

    Asserting the destination rather than only that something changed: a
    mutation that moved the set somewhere unexpected is a check reading the
    parameter in a way nobody intended, which a not-equal assertion would call
    a pass.
    """
    mutated = _mutate(entry_id, path, value)
    assert _firing(_run(mutated), entry_id, mutated) == expected


def test_excluding_a_notification_from_the_accountable_list_is_what_keeps_call_11_quiet() -> None:
    """The exclusion, proven by mutation rather than by the comment beside it.

    CALL-11 completes a refund and a confirmation send. A notification is not a
    second action, so `send_confirmation` is absent from the accountable list
    and the check returns `not_applicable` there. Adding it makes CALL-11 fire,
    which is what makes the exclusion load-bearing rather than decorative.
    """
    entry_id = "A-reason-code-understates-the-call"
    assert "CALL-11" not in _firing(_run(), entry_id)

    widened = _mutate(
        entry_id,
        ("accountable_write_tools",),
        [
            "exchange_tickets",
            "issue_refund",
            "transfer_booking",
            "change_holder_name",
            "transfer_to_specialist",
            "send_confirmation",
        ],
    )
    assert "CALL-11" in _firing(_run(widened), entry_id, widened)


# --------------------------------------------------------------------------
# Statuses: what a check says when it does not apply
# --------------------------------------------------------------------------


def test_a_check_that_does_not_apply_says_so_rather_than_passing() -> None:
    """`not_applicable` is a distinct answer from `satisfied`, and W11 is the
    cost of collapsing them: a fail-open default that also absorbed the state
    `unevaluable` now holds."""
    report = _run()
    outcome_results = {
        result.call_id: result for result in report.for_entry("A-outcome-contradicted-by-results")
    }
    assert outcome_results["CALL-18"].status is Status.APPLICABLE
    assert outcome_results["CALL-01"].status is Status.NOT_APPLICABLE, (
        "a call with an unconstrained outcome is reported as passing the check rather than "
        "as one the check does not apply to"
    )
    assert outcome_results["CALL-01"].verdict is None
    assert outcome_results["CALL-01"].detail


# --------------------------------------------------------------------------
# A state written after the gate did not open it
# --------------------------------------------------------------------------

_ASSERTION_ENTRY: Final[str] = "A-precondition-satisfied-by-assertion"


def _call_12_with(replacements: list[tuple[str, str]], name: str) -> CheckContext:
    source = (TRANSCRIPTS / "CALL-12.txt").read_text(encoding="utf-8")
    for line, replacement in replacements:
        assert source.count(line) == 1, f"CALL-12 no longer carries {line!r}"
        source = source.replace(line, replacement, 1)
    patched = REPO_ROOT / "build" / f"{name}-CALL-12.txt"
    patched.parent.mkdir(parents=True, exist_ok=True)
    patched.write_text(source, encoding="utf-8")
    try:
        return build_context(parse_call(patched), load_policies(POLICIES), policy_tool=POLICY_TOOL)
    finally:
        patched.unlink(missing_ok=True)


_VERIFIED_EARLY: Final[tuple[str, str]] = (
    " 15 |  1:06.322 |  1:08.349 | AGENT       | Thank you for confirming that.",
    " 15 |  1:06.322 |  1:06.322 | STATE       | identity_verified := true",
)
_VERIFIED_LATE: Final[tuple[str, str]] = (
    " 34 |  2:36.746 |  2:39.328 | AGENT       | That's on its way to you.",
    " 34 |  2:36.746 |  2:36.746 | STATE       | identity_verified := true",
)


def test_a_state_recorded_after_the_assertion_does_not_clear_it() -> None:
    """The gate was passed before anything recorded the precondition.

    CALL-12's send is refused with `caller_verified=false` and re-issued at
    event 32 with `assume_verified="true"`. A state event at event 34 says the
    precondition held two events *later*; at the moment the write went out the
    argument was still the only thing standing for it, which is the whole
    finding. Accepting a state anywhere in the call cleared this.
    """
    context = _call_12_with([_VERIFIED_LATE], "assertion-after")
    assert state_writes(context.events)["identity_verified"] == (34,)
    result = run_entry(_rubric().by_id(_ASSERTION_ENTRY), context, PROVENANCE, build_registry())
    assert result.verdict == "asserted", (
        "a state recorded after the invocation now clears the assertion, so the check asks "
        "whether the precondition was ever recorded rather than whether it held"
    )


def test_a_state_recorded_before_the_assertion_does_clear_it() -> None:
    """The other half, and the negative instance this entry has nowhere in the
    design set: the argument restates a precondition that genuinely held."""
    context = _call_12_with([_VERIFIED_EARLY], "assertion-before")
    assert state_writes(context.events)["identity_verified"] == (15,)
    result = run_entry(_rubric().by_id(_ASSERTION_ENTRY), context, PROVENANCE, build_registry())
    assert result.verdict == "recorded", (
        "a state recorded before the invocation no longer clears the assertion, so the "
        "check reports a finding against a call where the precondition actually held"
    )


def test_a_verification_refreshed_after_a_gated_write_does_not_hide_the_one_before() -> None:
    """The same last-write-wins defect as the repeated-request check, in a third
    place and with the opposite consequence.

    `verification_absent_before_gated_write` collects the indices of the
    verification states and asks whether any is below the write. Reading them
    out of a dict keyed by name kept only the final write, so a call that
    verified before the write and refreshed the flag afterwards reported no
    verification below it -- a false violation on an absolute gate.
    """
    entry = _rubric().by_id("A-gated-write-without-verification")
    live = next(c for c in _contexts() if c.call_id == "CALL-12")
    assert run_entry(entry, live, PROVENANCE, build_registry()).verdict == "ungated"

    context = _call_12_with([_VERIFIED_EARLY, _VERIFIED_LATE], "verification-history")
    assert state_writes(context.events)["identity_verified"] == (15, 34)
    result = run_entry(entry, context, PROVENANCE, build_registry())
    assert result.verdict == "verified", (
        "a verification recorded before the write is lost because the same variable is "
        "written again after it, which is the dict keeping only the last index"
    )
