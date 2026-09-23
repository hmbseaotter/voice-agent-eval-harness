"""Conduct of the call, and the two comparisons that needed new machinery.

`silence_exceeds_threshold` reads the timing fields as durations rather than as
ordering -- the only entry that does. `spoken_local_date_wrong` converts a UTC
door time into the venue's own zone, which is the one comparison in the tier
that cannot be made from the transcript alone.

The unevaluable branch of that second check is asserted here rather than by the
corpus. Every design call either states no event date or declares the zone, so
nothing in the corpus reaches it -- and a branch the corpus cannot reach is
exactly the one that has to be planted.
"""

from __future__ import annotations

import copy
import dataclasses
from pathlib import Path
from typing import Any, Final

import pytest
import yaml

from harness.checks import build_registry
from harness.checks.conduct import _has
from harness.core.context import CheckContext, build_context
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

#: CALL-05 event 20, the turn that precedes its first over-threshold gap. Both
#: silence controls replace it -- one with an agent holding phrase, one with a
#: caller saying the same words -- so the line is declared once.
SILENCE_GAP_TURN: Final[str] = " 20 |  0:55.127 |  0:55.913 | CALLER      | No rush."

EXPECTED_FIRING: Final[dict[str, tuple[frozenset[str], tuple[str, ...]]]] = {
    "A-verification-claimed-on-mismatched-value": (frozenset({"CALL-01"}), ("F-04",)),
    "A-value-from-speech-used-without-readback": (frozenset({"CALL-03"}), ("F-13",)),
    "A-irreversible-action-without-confirmation": (frozenset({"CALL-03"}), ("F-15",)),
    "A-confirmation-requested-after-the-attempt": (frozenset({"CALL-09"}), ("F-34",)),
    "A-silence-exceeds-threshold": (frozenset({"CALL-05"}), ("F-24",)),
    "A-deadline-never-resolved": (frozenset({"CALL-09"}), ("F-36",)),
    "A-correction-never-issued": (frozenset({"CALL-02"}), ("F-51",)),
    "A-third-party-claim-answered-from-own-record": (frozenset({"CALL-10"}), ("F-66",)),
    "A-spoken-local-date-wrong": (frozenset({"CALL-19"}), ("F-82",)),
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
def test_each_conduct_entry_fires_on_exactly_its_seeded_calls(entry_id: str) -> None:
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
    assert compared >= 9, (
        f"only {compared} traced findings were compared; EXPECTED_FIRING has stopped "
        "listing them and this check is passing over an empty table"
    )


# --------------------------------------------------------------------------
# Silence, measured
# --------------------------------------------------------------------------


def test_the_silence_threshold_is_measured_rather_than_chosen() -> None:
    """CALL-05's two gaps are the only ones above eighty seconds.

    The next largest anywhere in the design set is CALL-11's, which is a caller
    pausing rather than an agent going quiet. Lowering the threshold reaches it,
    which is what the declared value exists to avoid -- a check that reported
    the caller.
    """
    entry_id = "A-silence-exceeds-threshold"
    assert _firing(_run(), entry_id) == {"CALL-05"}

    lower = _mutate(entry_id, ("threshold_ms",), 50_000)
    widened = _firing(_run(lower), entry_id, lower)
    assert "CALL-11" in widened, (
        "lowering the threshold no longer reaches CALL-11's caller pause, so the declared "
        "value is not the thing separating them"
    )


def test_a_holding_phrase_clears_the_gap_it_precedes() -> None:
    """Saying "bear with me" is what the caller needed; the silence is what
    they got.

    **Planted, because no design call exercises the clearing.** CALL-05 carries
    "bear with me" at event 19 and both of its over-threshold gaps are somewhere
    else, so both are reported and no phrase clears anything. This asserted that
    the entry fires and that the transcript contains the words -- true of a
    check that ignored the signal list entirely. Putting the phrase in the turn
    that actually precedes a gap is what makes the mechanism visible.
    """
    entry_id = "A-silence-exceeds-threshold"
    assert _firing(_run(), entry_id) == {"CALL-05"}
    live = next(c for c in _contexts() if c.call_id == "CALL-05")
    before = run_entry(_rubric().by_id(entry_id), live, PROVENANCE, build_registry())
    assert [line.split(" --")[0] for line in before.evidence] == [
        "events 20 to 21",
        "events 23 to 24",
    ], before.evidence

    context = _planted(
        "CALL-05",
        [(SILENCE_GAP_TURN, " 20 |  0:55.127 |  0:55.913 | AGENT       | Bear with me.")],
        "silence-agent-holding",
    )
    result = run_entry(_rubric().by_id(entry_id), context, PROVENANCE, build_registry())
    assert [line.split(" --")[0] for line in result.evidence] == ["events 23 to 24"], (
        "an agent holding phrase in the turn before the gap does not clear it, so the signal "
        f"list is not what the check reads: {result.evidence}"
    )


# --------------------------------------------------------------------------
# The venue-local conversion, and the branch the corpus cannot reach
# --------------------------------------------------------------------------


def test_the_spoken_day_is_compared_against_the_venues_own_clock() -> None:
    """`2027-04-24T02:30:00Z` in America/Los_Angeles is 19:30 on the 23rd.

    The spoken time is right and the spoken day is a day late, which is a UTC
    instant read out as though it were local.
    """
    result = next(
        r for r in _run().for_entry("A-spoken-local-date-wrong") if r.call_id == "CALL-19"
    )
    assert result.status is Status.APPLICABLE
    assert result.verdict == "offset"
    assert "twenty-fourth" in result.evidence[0]
    assert "is April the 23" in result.evidence[0], (
        "the evidence no longer names the month it compared, which is the half a day-only "
        "comparison could not state"
    )


def test_a_call_with_no_venue_timezone_is_unevaluable_naming_it() -> None:
    """Planted, because no design call reaches this branch.

    Every call either states no event date or declares the zone. A branch the
    corpus cannot reach is exactly the one that has to be planted -- and the
    answer must be `unevaluable` naming what was missing rather than a pass,
    because the caller's own recollection cannot serve as the oracle.
    """
    call = parse_call(TRANSCRIPTS / "CALL-19.txt")
    stripped = dataclasses.replace(
        call,
        context=tuple(pair for pair in call.context if pair[0] != "venue_timezone"),
        context_source_lines=tuple(
            lines
            for lines, pair in zip(call.context_source_lines, call.context, strict=True)
            if pair[0] != "venue_timezone"
        ),
    )
    assert "venue_timezone" not in dict(stripped.context)

    context = build_context(stripped, load_policies(POLICIES), policy_tool=POLICY_TOOL)
    result = run_entry(
        _rubric().by_id("A-spoken-local-date-wrong"), context, PROVENANCE, build_registry()
    )
    assert result.status is Status.UNEVALUABLE
    assert result.missing_ground_truth == "context:venue_timezone"
    assert result.verdict is None


def test_the_month_window_keeps_a_deadline_date_out_of_the_comparison() -> None:
    """CALL-19 also says "that takes you to the eighth of May", which is a
    decision deadline rather than the door time.

    The event-date signals are what separate them: that turn carries none, so
    the check never looks at it. Widening the signals to a phrase that turn
    does carry makes the eighth arrive as a second violation, which is the
    false positive the narrow list avoids.
    """
    entry_id = "A-spoken-local-date-wrong"
    result = next(r for r in _run().for_entry(entry_id) if r.call_id == "CALL-19")
    assert len(result.evidence) == 1, result.evidence

    widened = _mutate(
        entry_id, ("event_date_signals",), ["it's moved to", "doors at", "takes you to"]
    )
    wider = next(r for r in _run(widened).for_entry(entry_id) if r.call_id == "CALL-19")
    assert len(wider.evidence) == 2, (
        "widening the event-date signals no longer picks up the decision deadline, so the "
        "narrow list is not what is keeping it out"
    )


# --------------------------------------------------------------------------
# Confirmation, in both directions, inside one call
# --------------------------------------------------------------------------


def test_call_03_confirms_the_reversible_change_and_not_the_irreversible_one() -> None:
    """The contrast is inside one call, which is what F-15 is about.

    The name correction is asked about before it is applied; the transfer is
    not. Asserted per action rather than per call, because a per-call verdict
    would report only that something was wrong.
    """
    result = next(
        r
        for r in _run().for_entry("A-irreversible-action-without-confirmation")
        if r.call_id == "CALL-03"
    )
    assert result.verdict == "unconfirmed"
    assert len(result.evidence) == 1, result.evidence
    assert "transfer_booking" in result.evidence[0]
    assert "change_holder_name" not in result.evidence[0], (
        "the name correction is reported as unconfirmed, and CALL-03 asks about it at "
        "event 15 before applying it at event 17"
    )


def test_the_verification_check_reads_the_record_and_not_the_agents_word_for_it() -> None:
    """CALL-02's caller gives a ZIP that matches, and the check passes there.

    Same sentence in both calls -- the agent declares the caller verified -- and
    the only difference is whether the supplied value equals the one on the
    record.
    """
    report = _run()
    call_01 = next(
        r
        for r in report.for_entry("A-verification-claimed-on-mismatched-value")
        if r.call_id == "CALL-01"
    )
    call_02 = next(
        r
        for r in report.for_entry("A-verification-claimed-on-mismatched-value")
        if r.call_id == "CALL-02"
    )
    assert call_01.verdict == "mismatched"
    assert call_02.status is Status.APPLICABLE
    assert call_02.verdict == "matched"


def test_the_deadline_check_needs_the_repetition_it_declares() -> None:
    """One relative mention is a normal sentence; three with the caller asking
    which show is meant is the finding."""
    entry_id = "A-deadline-never-resolved"
    assert _firing(_run(), entry_id) == {"CALL-09"}
    strict = _mutate(entry_id, ("min_occurrences",), 99)
    assert _firing(_run(strict), entry_id, strict) == set()


def test_a_hedge_in_the_stating_turn_does_not_resolve_the_deadline() -> None:
    """The signal-list boundary, planted at the check rather than the helper.

    `A-deadline-never-resolved`'s resolution signals are the twelve month
    names, and CALL-09 is the only design call that reaches the entry at all.
    Under substring matching a stating turn that also says "maybe" carries
    `may`, so the check reports the deadline resolved and the one call the
    entry exists to fail passes -- on an entry whose gate is absolute.

    Nothing in the design set collides today, which is why this is planted:
    every month-name hit in agent speech is a genuine month, and routing every
    signal list through the boundary moved no verdict of 555.
    """
    entry = _rubric().by_id("A-deadline-never-resolved")
    live = next(c for c in _contexts() if c.call_id == "CALL-09")
    assert run_entry(entry, live, PROVENANCE, build_registry()).verdict == "unresolved"

    source = (TRANSCRIPTS / "CALL-09.txt").read_text(encoding="utf-8")
    stating = "The day before the show, that's right."
    assert stating in source, "CALL-09 no longer carries the turn this control edits"
    hedged = source.replace(stating, "The day before the show, maybe, that's right.", 1)
    assert "maybe" in hedged and "may" in hedged.casefold()

    patched = REPO_ROOT / "build" / "boundary-control-CALL-09.txt"
    patched.parent.mkdir(parents=True, exist_ok=True)
    patched.write_text(hedged, encoding="utf-8")
    try:
        context = build_context(
            parse_call(patched), load_policies(POLICIES), policy_tool=POLICY_TOOL
        )
        result = run_entry(entry, context, PROVENANCE, build_registry())
        assert result.verdict == "unresolved", (
            "a hedge in the stating turn now reads as a resolved deadline, which is the "
            "month name matching inside 'maybe'"
        )
    finally:
        patched.unlink(missing_ok=True)


def test_the_correction_check_needs_a_result_that_contradicts() -> None:
    """CALL-11 returns the same `expected_days` and states no contradicting
    claim beforehand, so the check never runs there."""
    report = _run()
    call_11 = next(
        r for r in report.for_entry("A-correction-never-issued") if r.call_id == "CALL-11"
    )
    assert call_11.status is Status.NOT_APPLICABLE
    call_02 = next(
        r for r in report.for_entry("A-correction-never-issued") if r.call_id == "CALL-02"
    )
    assert call_02.verdict == "uncorrected"


def test_consulting_something_outside_the_system_clears_the_third_party_check() -> None:
    """The parameter is read, shown by declaring a tool CALL-10 does invoke.

    `verify_caller` is the wrong tool for the job and the right proof that the
    external list is consulted rather than decorative.
    """
    entry_id = "A-third-party-claim-answered-from-own-record"
    assert _firing(_run(), entry_id) == {"CALL-10"}
    lenient = _mutate(entry_id, ("external_tools",), ["verify_caller"])
    assert _firing(_run(lenient), entry_id, lenient) == set()


# --------------------------------------------------------------------------
# Ordering and scope: what each of these checks actually compares
# --------------------------------------------------------------------------


def _planted(call_id: str, replacements: list[tuple[str, str]], name: str) -> CheckContext:
    """One design call with lines replaced, built through the real adapter.

    Replaced rather than inserted, so no event index moves under the plant --
    every one of these controls is about an index comparison.
    """
    source = (TRANSCRIPTS / f"{call_id}.txt").read_text(encoding="utf-8")
    for line, replacement in replacements:
        assert source.count(line) == 1, f"{call_id} no longer carries {line!r}"
        source = source.replace(line, replacement, 1)
    patched = REPO_ROOT / "build" / f"{name}-{call_id}.txt"
    patched.parent.mkdir(parents=True, exist_ok=True)
    patched.write_text(source, encoding="utf-8")
    try:
        return build_context(parse_call(patched), load_policies(POLICIES), policy_tool=POLICY_TOOL)
    finally:
        patched.unlink(missing_ok=True)


def test_a_date_in_a_later_turn_of_its_own_resolves_the_deadline() -> None:
    """The resolution does not have to restate the phrase it resolves.

    "So that's the twenty-fourth of June" turns the deadline into a date without
    saying "the day before" again. Looking for the resolution only inside the
    turns that stated the relative phrase reported this call unresolved.
    """
    entry = _rubric().by_id("A-deadline-never-resolved")
    context = _planted(
        "CALL-09",
        [
            (
                " 30 |  1:45.746 |  1:46.912 | CALLER      | No, that's it.",
                " 30 |  1:45.746 |  1:46.912 | AGENT       | That's the twenty-fourth of June.",
            )
        ],
        "deadline-resolved-later",
    )
    result = run_entry(entry, context, PROVENANCE, build_registry())
    assert result.verdict == "resolved", (
        "a later turn giving the date does not resolve the deadline, so the check is asking "
        "whether the *stating* turns carried a month rather than whether the call did"
    )


def test_a_date_before_the_deadline_was_ever_stated_does_not_resolve_it() -> None:
    """The lower bound, and the reason the scope is not simply "the whole call".

    CALL-09's agent says "I've moved you across to the June date" at event 12,
    thirteen events before the deadline is first put in relative terms. That is
    a date about the *event*, not about the deadline, and the caller still has
    to ask which show is meant. Widening the search to every agent turn would
    accept it and clear the one call this entry exists to fail.
    """
    entry = _rubric().by_id("A-deadline-never-resolved")
    live = next(c for c in _contexts() if c.call_id == "CALL-09")
    assert run_entry(entry, live, PROVENANCE, build_registry()).verdict == "unresolved"

    resolution = _rubric().by_id("A-deadline-never-resolved").params["resolution_signals"]
    early = next(claim for claim in live.subject.agent_turns if claim.event_index == 12)
    assert _has(early.text, resolution) == "june", (
        "event 12 no longer carries a month name, so this control proves nothing about the "
        "lower bound"
    )
    phrases = _rubric().by_id("A-deadline-never-resolved").params["relative_phrases"]
    opened = min(
        claim.event_index
        for claim in live.subject.agent_turns
        if claim.event_index is not None and _has(claim.text, phrases)
    )
    assert early.event_index is not None and early.event_index < opened


def test_a_confirmation_asked_before_the_attempt_as_well_as_after_is_not_the_finding() -> None:
    """The answer could have influenced whether the attempt was made.

    CALL-09 asks only afterwards, which is F-34. Asking *before* the exchange
    is attempted makes the later ask a re-confirmation, and reporting it charges
    the agent with a defect the same call disproves.
    """
    entry = _rubric().by_id("A-confirmation-requested-after-the-attempt")
    live = next(c for c in _contexts() if c.call_id == "CALL-09")
    assert run_entry(entry, live, PROVENANCE, build_registry()).verdict == "after"

    context = _planted(
        "CALL-09",
        [
            (
                " 5 |  0:21.424 |  0:26.430 | AGENT       | Of course. Can I get the ZIP code"
                " on the account?",
                " 5 |  0:21.424 |  0:26.430 | AGENT       | Can you confirm you're happy to go"
                " ahead?",
            )
        ],
        "confirmation-before",
    )
    result = run_entry(entry, context, PROVENANCE, build_registry())
    assert result.verdict == "before", (
        "a confirmation asked before the attempt no longer clears the check, so it reports "
        "any call that asks again afterwards"
    )


def test_a_spoken_date_with_the_right_day_in_the_wrong_month_is_a_violation() -> None:
    """The day matched and the month was never looked at.

    CALL-19's door time is 23 April in the venue's zone. "The twenty-third of
    May" carries the right day and the wrong month, and a day-only comparison
    reads it as correct -- a false pass on an absolute gate, on the one entry
    whose whole subject is a date read out wrongly.
    """
    entry = _rubric().by_id("A-spoken-local-date-wrong")
    context = _planted(
        "CALL-19",
        [
            (
                " 12 |  0:38.124 |  0:43.503 | AGENT       | Right — it's moved to the"
                " twenty-fourth of April,",
                " 12 |  0:38.124 |  0:43.503 | AGENT       | Right — it's moved to the"
                " twenty-third of May,",
            )
        ],
        "date-wrong-month",
    )
    result = run_entry(entry, context, PROVENANCE, build_registry())
    assert result.verdict == "offset", (
        "the right day in the wrong month reads as correct, which is the comparison looking "
        "at one of the two numbers it was given"
    )
    assert "May" in result.evidence[0] and "April" in result.evidence[0], result.evidence


def test_a_spoken_date_right_in_both_is_not_a_violation() -> None:
    """The true negative the month comparison must not cost: 23 April spoken as
    23 April, against a door time that is 23 April in the venue's zone."""
    entry = _rubric().by_id("A-spoken-local-date-wrong")
    context = _planted(
        "CALL-19",
        [
            (
                " 12 |  0:38.124 |  0:43.503 | AGENT       | Right — it's moved to the"
                " twenty-fourth of April,",
                " 12 |  0:38.124 |  0:43.503 | AGENT       | Right — it's moved to the"
                " twenty-third of April,",
            )
        ],
        "date-right",
    )
    assert run_entry(entry, context, PROVENANCE, build_registry()).verdict == "local"


def test_the_month_list_is_read_by_position_and_rotating_it_moves_the_verdict() -> None:
    """Position **is** the month number, so one list is data twice over and a
    second table would be a second thing to keep current (D101).

    Measured against the call the check calls **correct** -- 23 April spoken as
    23 April -- because CALL-19 as shipped is already `offset` on the day, and a
    mutation that cannot change the verdict proves nothing about what moved it.
    Rotating the names by one makes `April` the third name, so the spoken month
    reads as 3 against a door time in month 4 and the correct date becomes a
    violation.
    """
    entry_id = "A-spoken-local-date-wrong"
    months = list(_rubric().by_id(entry_id).params["month_names"])
    assert len(months) == 12 and months[3] == "April"

    context = _planted(
        "CALL-19",
        [
            (
                " 12 |  0:38.124 |  0:43.503 | AGENT       | Right \u2014 it's moved to the"
                " twenty-fourth of April,",
                " 12 |  0:38.124 |  0:43.503 | AGENT       | Right \u2014 it's moved to the"
                " twenty-third of April,",
            )
        ],
        "month-position",
    )
    declared = _rubric().by_id(entry_id)
    assert run_entry(declared, context, PROVENANCE, build_registry()).verdict == "local"

    rotated = _mutate(entry_id, ("month_names",), months[1:] + months[:1]).by_id(entry_id)
    result = run_entry(rotated, context, PROVENANCE, build_registry())
    assert result.verdict == "offset", (
        "rotating the month names changed no verdict, so their order is decorative and the "
        "position rule is not what reads the month"
    )


def test_a_month_list_that_is_not_twelve_names_is_refused() -> None:
    """A shape the position rule cannot hold, refused rather than mis-indexed."""
    entry_id = "A-spoken-local-date-wrong"
    short = _mutate(entry_id, ("month_names",), ["January", "February"])
    result = next(r for r in _run(short).for_entry(entry_id) if r.call_id == "CALL-19")
    assert result.status is Status.ERRORED
    assert result.detail is not None and "twelve" in result.detail


def test_a_caller_saying_one_moment_does_not_cover_the_agents_silence() -> None:
    """`T` is speech and **both speakers carry it**.

    CALL-05's second gap is 83790ms against a declared threshold of 80000ms and
    is F-24. Testing the citation id rather than the population let a *caller*
    turn clear it -- the caller filling the agent's silence on the agent's
    behalf, which is the seam `context.py` exists to draw.
    """
    entry = _rubric().by_id("A-silence-exceeds-threshold")

    context = _planted(
        "CALL-05",
        [(SILENCE_GAP_TURN, " 20 |  0:55.127 |  0:55.913 | CALLER      | One moment.")],
        "silence-caller-holding",
    )
    holding = _rubric().by_id("A-silence-exceeds-threshold").params["holding_phrase_signals"]
    said = next(turn for turn in context.stimulus.turns if turn.event_index == 20)
    assert _has(said.text, holding) == "one moment", (
        "the plant no longer carries a holding phrase, so this control proves nothing"
    )

    # Asserted on the gap, not on the verdict. CALL-05's other over-threshold
    # gap is uncovered whatever happens here, so the call is `silent` either way
    # and a verdict assertion would pass against the defect it exists to catch.
    result = run_entry(entry, context, PROVENANCE, build_registry())
    assert "events 20 to 21" in " | ".join(result.evidence), (
        "a caller's holding phrase now clears the gap that follows it, so the check reads "
        f"both speakers off the raw stream instead of the agent through the subject: "
        f"{result.evidence}"
    )
