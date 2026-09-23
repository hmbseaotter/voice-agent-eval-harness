"""The ground-truth seam: what a check may read, and what it may read it *as*.

The requirement is that the system-level event log and retrieved policy clauses
are ground truth and agent speech is the subject under test. The specification's
grounding criterion cannot tell that design from its inversion -- its fixture
puts the supporting value in a retrieved clause, and a grounding blob that
concatenated speech alongside the three ground-truth sources would resolve it
either way and pass. D104 added the criterion this file answers, and the control
below is what answers it: the supporting value is planted in an agent turn and
in nowhere else, and the corpus a claim resolves against must not contain it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest

from harness.core.context import (
    DISPOSITION_FIELDS,
    RECORD_FACT_FIELDS,
    Claim,
    Fact,
    FactSource,
    build_context,
    state_writes,
)
from harness.core.events import (
    REQUIRED_CALL_KEYS,
    Call,
    CallRecord,
    Direction,
    DisclosureEvent,
    DisclosureState,
    DisconnectionReason,
    Environment,
    Event,
    EventKind,
    Outcome,
    PolicyEvent,
    SpeechEvent,
    StateEvent,
    SystemEvent,
    ToolCallEvent,
    ToolResultEvent,
    ToolStatus,
)
from harness.corpus.policies import load_policies, parse_policy
from harness.corpus.text_adapter import parse_call

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
TRANSCRIPTS: Final[Path] = REPO_ROOT / "corpus" / "transcripts"
POLICIES: Final[Path] = REPO_ROOT / "corpus" / "policies"

#: The corpus's retrieval tool. Named here rather than imported from the seam,
#: because the seam takes it as an argument for the same reason a check does:
#: it is a corpus entity name, and no such value is hardcoded in the harness.
POLICY_TOOL: Final[str] = "fetch_policy"

#: Planted into an agent turn and into nothing else.
ONLY_IN_SPEECH: Final[str] = "quinquagenarian"
#: Planted into a STATE event and into nothing else.
ONLY_IN_FACTS: Final[str] = "sesquipedalian"


def _transcripts() -> list[Path]:
    paths = sorted(TRANSCRIPTS.glob("*.txt"))
    assert paths, "no transcripts found; the corpus moved"
    return paths


def _record() -> CallRecord:
    return CallRecord(
        call_id="CALL-XX",
        agent_id="verso-support",
        agent_version="2027.03.1",
        environment=Environment.PRODUCTION,
        direction=Direction.INBOUND,
        from_number="+1 (415) 555-0184",
        to_number="+1 (415) 555-0100",
        started_at="2027-03-14T09:12:03.000Z",
        answered_at="2027-03-14T09:12:05.480Z",
        ended_at="2027-03-14T09:13:23.329Z",
        duration_ms=80329,
        disconnection_reason=DisconnectionReason.CALLER_HANGUP,
        outcome=Outcome.RESOLVED,
        outcome_reason="exchange_completed",
    )


def _speech(index: int, kind: EventKind, body: str) -> SpeechEvent:
    return SpeechEvent(
        index=index,
        started_at_ms=index * 1000,
        ended_at_ms=index * 1000 + 900,
        kind=kind,
        body=body,
        citation_id=f"T{index}",
        source_lines=(index,),
    )


def _planted_call() -> Call:
    """A call whose speech and facts each carry a token the other lacks."""
    events: tuple[Event, ...] = (
        SystemEvent(
            index=1,
            started_at_ms=0,
            ended_at_ms=0,
            kind=EventKind.SYSTEM,
            body="call.answered",
            citation_id="F1",
            source_lines=(1,),
            name="call.answered",
            arguments="",
        ),
        _speech(2, EventKind.CALLER, "I want to move my tickets."),
        _speech(3, EventKind.AGENT, f"Certainly, the {ONLY_IN_SPEECH} booking is moved."),
        StateEvent(
            index=4,
            started_at_ms=4000,
            ended_at_ms=4000,
            kind=EventKind.STATE,
            body=f"exchange_note := {ONLY_IN_FACTS}",
            citation_id="F2",
            source_lines=(4,),
            name="exchange_note",
            value=ONLY_IN_FACTS,
        ),
    )
    return Call(
        source_path="planted/CALL-XX.txt",
        record=_record(),
        context=(("booking_reference", "BK-0000-AA"),),
        context_source_lines=((3,),),
        events=events,
        unparsed=(),
    )


# --------------------------------------------------------------------------
# The control: speech is not evidence
# --------------------------------------------------------------------------


def test_a_value_that_lives_only_in_an_agent_turn_is_not_in_the_ground_truth() -> None:
    """The planted control for the requirement's second half.

    The token is in one agent turn and in nothing else in the call. If it can
    be found in the corpus a claim resolves against, then a grounding check
    would confirm the agent's claim using the agent's claim -- and every
    grounding entry in the tier would pass on the calls it exists to fail.
    """
    context = build_context(_planted_call(), {}, policy_tool=POLICY_TOOL)

    assert ONLY_IN_SPEECH in " ".join(claim.text for claim in context.subject.agent_turns), (
        "the plant is not in the agent turn, so this control is proving nothing"
    )
    assert ONLY_IN_FACTS in context.ground_truth.corpus, (
        "the fact-side plant is missing, so a corpus that contained neither token "
        "would pass this test while grounding against nothing"
    )
    assert ONLY_IN_SPEECH not in context.ground_truth.corpus, (
        "agent speech reached the grounding corpus: a claim would be resolved "
        "against the claim that made it"
    )


def test_caller_speech_is_not_in_the_ground_truth_either() -> None:
    """A caller can say anything, so the content of a caller turn supports no
    claim about the world. Its *occurrence* is available as `stimulus`."""
    context = build_context(_planted_call(), {}, policy_tool=POLICY_TOOL)
    assert [claim.text for claim in context.stimulus.turns] == ["I want to move my tickets."]
    assert "move my tickets" not in context.ground_truth.corpus


def _leaked_turns(call_id: str, agent_turns: tuple[Claim, ...], corpus: str) -> list[str]:
    """Every agent turn of `call_id` that is present in `corpus`.

    The comparison the scan makes, as a function rather than inline in the
    check, so the control can hand it a corpus that *does* contain a turn and
    require it to say so. It was inline, and the control beside it built a
    string and asserted a turn was in it -- `x in y + x`, true for every `y`
    including the empty one, so the scan could ground against nothing and both
    stayed green.
    """
    leaked: list[str] = []
    for claim in agent_turns:
        if claim.text and claim.text in corpus:
            leaked.append(f"{call_id} {claim.reference}: {claim.text[:60]}")
    return leaked


def test_no_agent_turn_in_the_design_set_appears_in_its_calls_ground_truth() -> None:
    """The same claim over the real corpus rather than over a plant.

    The plant proves the seam excludes a token; this proves it excludes every
    agent turn of every design call, which is the property the requirement
    states. Both are here because a plant says the check can fire and says
    nothing about the corpus it is aimed at.
    """
    policies = load_policies(POLICIES)
    leaked: list[str] = []
    groundless: list[str] = []
    turns = 0
    for transcript in _transcripts():
        call = parse_call(transcript)
        context = build_context(call, policies, policy_tool=POLICY_TOOL)
        corpus = context.ground_truth.corpus
        if not corpus.strip():
            groundless.append(call.record.call_id)
        turns += len(context.subject.agent_turns)
        leaked.extend(_leaked_turns(call.record.call_id, context.subject.agent_turns, corpus))
    assert not leaked, "agent speech present in the grounding corpus:\n  " + "\n  ".join(leaked)
    assert turns >= 100, f"only {turns} agent turns compared; the scan has stopped finding them"
    # The other side of the same floor, and it was missing. `turns` guards the
    # subject; nothing guarded the ground truth, so a seam producing no corpus
    # at all reported no leak and passed. Measured when this was written:
    # `GroundTruth.corpus` returning empty left this check green and its control
    # green, and only two neighbors in this module noticed.
    assert not groundless, (
        "these calls ground against an empty corpus, so the scan above compared every "
        "agent turn against nothing and found nothing: " + ", ".join(groundless)
    )


def test_the_leak_scan_would_notice_a_turn_that_was_in_the_corpus() -> None:
    """The control, and it was a tautology.

    It built `corpus + turn` and asserted the turn was in it, which is true for
    every corpus including the empty one, and never called the scan. Measured
    when this was written: with `ground_truth.corpus` returning empty -- the
    seam grounding against nothing at all -- the scan reported no leak and this
    control passed with it. Two neighbors in this module caught that mutation,
    which is the only reason the seam was covered: a guard green and blind
    while the protection came from somewhere nobody had written down.

    It drives the comparison now, in both directions, over a corpus it controls.
    """
    context = build_context(_planted_call(), {}, policy_tool=POLICY_TOOL)
    turns = context.subject.agent_turns
    assert turns and turns[0].text, "the planted call has no agent turn to leak"

    clean = _leaked_turns("CALL-XX", turns, context.ground_truth.corpus)
    assert clean == [], f"the planted call already leaks, so this control proves nothing: {clean}"

    widened = context.ground_truth.corpus + "\n" + turns[0].text
    found = _leaked_turns("CALL-XX", turns, widened)
    assert found, (
        "a corpus containing an agent turn verbatim was reported as carrying no leak, so "
        "the scan would read a leak as absence"
    )
    assert turns[0].text[:60] in found[0], f"the leak is reported without naming the turn: {found}"


# --------------------------------------------------------------------------
# The disposition labels are the subject, not the ground truth
# --------------------------------------------------------------------------


def test_the_four_disposition_labels_are_under_test_and_not_evidence() -> None:
    """`duration_ms`, `disconnection_reason`, `outcome` and `outcome_reason` are
    what the system *claimed*. A harness that reconciled them on read would
    delete the defect it exists to detect."""
    context = build_context(_planted_call(), {}, policy_tool=POLICY_TOOL)
    assert context.subject.disposition("outcome") == "resolved"
    assert context.subject.disposition("outcome_reason") == "exchange_completed"

    record_keys = {fact.key for fact in context.ground_truth.of_source(FactSource.CALL_RECORD)}
    for field in DISPOSITION_FIELDS:
        assert field not in record_keys, (
            f"{field} is in the ground truth; a disposition check would then be "
            "comparing the platform's claim against itself"
        )


def test_the_call_record_is_partitioned_with_no_field_in_neither_or_both() -> None:
    """Every declared call key belongs to exactly one population.

    Enumerated rather than derived as "everything that is not a disposition",
    so a field added to the record joins a population by decision. Under the
    negative form it would join ground truth by default, which is how W17 put
    fabricated facts into a grounding blob -- by classifying whatever it had
    not thought about.
    """
    facts, dispositions = set(RECORD_FACT_FIELDS), set(DISPOSITION_FIELDS)
    assert not facts & dispositions, f"in both populations: {sorted(facts & dispositions)}"
    assert facts | dispositions == set(REQUIRED_CALL_KEYS), (
        "the two populations do not cover the call record: "
        f"unclassified {sorted(set(REQUIRED_CALL_KEYS) - facts - dispositions)}, "
        f"unknown {sorted(facts | dispositions - set(REQUIRED_CALL_KEYS))}"
    )


# --------------------------------------------------------------------------
# Every event kind lands in exactly one population
# --------------------------------------------------------------------------


def _one_of_each_kind() -> dict[EventKind, Event]:
    return {
        EventKind.CALLER: _speech(1, EventKind.CALLER, "caller words"),
        EventKind.AGENT: _speech(2, EventKind.AGENT, "agent words"),
        EventKind.TOOL_CALL: ToolCallEvent(
            index=3,
            kind=EventKind.TOOL_CALL,
            body='t1 lookup_booking(reference="BK-0000-AA")',
            citation_id="F1",
            tool_call_id="t1",
            name="lookup_booking",
            arguments='reference="BK-0000-AA"',
            started_at_ms=0,
            ended_at_ms=1,
            source_lines=(1,),
        ),
        EventKind.TOOL_RESULT: ToolResultEvent(
            index=4,
            kind=EventKind.TOOL_RESULT,
            body="t1 -> retrieved successful=true",
            citation_id="F2",
            tool_call_id="t1",
            status=ToolStatus.RETRIEVED,
            successful=True,
            detail="found",
            started_at_ms=0,
            ended_at_ms=1,
            source_lines=(1,),
        ),
        EventKind.STATE: StateEvent(
            index=5,
            kind=EventKind.STATE,
            body="refund_eligible := false",
            citation_id="F3",
            name="refund_eligible",
            value="false",
            started_at_ms=0,
            ended_at_ms=1,
            source_lines=(1,),
        ),
        EventKind.POLICY: PolicyEvent(
            index=6,
            kind=EventKind.POLICY,
            body="refund.v1 2.2",
            citation_id="F4",
            document="refund.v1",
            clause="2.2",
            text="Where the request is made between 14 days",
            started_at_ms=0,
            ended_at_ms=1,
            source_lines=(1,),
        ),
        EventKind.DISCLOSURE: DisclosureEvent(
            index=7,
            kind=EventKind.DISCLOSURE,
            body="recording_notice -> delivered",
            citation_id="F5",
            name="recording_notice",
            state=DisclosureState.DELIVERED,
            text="This call is recorded.",
            started_at_ms=0,
            ended_at_ms=1,
            source_lines=(1,),
        ),
        EventKind.SYSTEM: SystemEvent(
            index=8,
            kind=EventKind.SYSTEM,
            body="call.ended",
            citation_id="F6",
            name="call.ended",
            arguments='reason="caller_hangup"',
            started_at_ms=0,
            ended_at_ms=1,
            source_lines=(1,),
        ),
    }


def test_every_event_kind_lands_in_exactly_one_population() -> None:
    """All eight, so a kind added later has to be placed rather than defaulted."""
    by_kind = _one_of_each_kind()
    assert set(by_kind) == set(EventKind), "a kind is missing from this fixture"

    call = Call(
        source_path="planted/CALL-XX.txt",
        record=_record(),
        context=(),
        context_source_lines=(),
        events=tuple(by_kind[kind] for kind in EventKind),
        unparsed=(),
    )
    context = build_context(call, {}, policy_tool=POLICY_TOOL)

    fact_indices = {
        fact.event_index
        for fact in context.ground_truth.of_source(FactSource.EVENT)
        if fact.event_index is not None
    }
    speech_indices = {
        claim.event_index
        for claim in (*context.subject.agent_turns, *context.stimulus.turns)
        if claim.event_index is not None
    }

    assert not fact_indices & speech_indices, "an event reached both populations"
    assert fact_indices | speech_indices == {event.index for event in call.events}, (
        "an event reached neither population, so a check would never see it"
    )
    assert fact_indices == {3, 4, 5, 6, 7, 8}
    assert speech_indices == {1, 2}


# --------------------------------------------------------------------------
# Retrieved policy documents, whole
# --------------------------------------------------------------------------


def test_a_retrieved_document_puts_every_clause_in_the_ground_truth() -> None:
    """Including the clauses the agent did not apply.

    That is the point of retrieval returning a document (D65): the sharper
    defect class is "a clause governing the question was inside the returned
    document and the agent applied a different one", and it is only expressible
    against the whole document. CALL-02 is the worked example -- refund.v1
    2.4 states the booking fee is non-refundable, it is in the document
    returned at event 12, and the agent promised the fee back anyway.
    """
    policies = load_policies(POLICIES)
    call = parse_call(TRANSCRIPTS / "CALL-02.txt")
    context = build_context(call, policies, policy_tool=POLICY_TOOL)

    assert [document.name for document in context.retrieved_policies] == ["refund.v1"]
    clause_keys = {fact.key for fact in context.ground_truth.of_source(FactSource.POLICY_CLAUSE)}
    assert clause_keys == {f"refund.v1 {clause}" for clause, _ in policies["refund.v1"].clauses}

    applied = {
        fact.key
        for fact in context.ground_truth.of_source(FactSource.EVENT)
        if fact.key.startswith("refund.v1 ")
    }
    assert applied, "CALL-02 applies no clause, so this fixture is not the one described"
    assert clause_keys - applied, (
        "every clause of the retrieved document was applied, so the un-applied "
        "clauses this test is about are not present in this call"
    )
    assert "refund.v1 2.4" in clause_keys


def test_the_retrieval_tool_name_is_a_parameter_and_not_a_constant() -> None:
    """Passing a different tool name retrieves nothing.

    `fetch_policy` is a corpus entity name (class 6). The rule that no such
    value is hardcoded in Python applies to the seam as much as to a check, and
    the way to assert it is to change the value and see behavior change.
    """
    policies = load_policies(POLICIES)
    call = parse_call(TRANSCRIPTS / "CALL-02.txt")
    assert build_context(call, policies, policy_tool=POLICY_TOOL).retrieved_policies
    assert not build_context(call, policies, policy_tool="get_policy").retrieved_policies


def test_a_call_that_retrieves_nothing_has_no_policy_clauses_in_its_ground_truth() -> None:
    context = build_context(_planted_call(), load_policies(POLICIES), policy_tool=POLICY_TOOL)
    assert context.retrieved_policies == ()
    assert context.ground_truth.of_source(FactSource.POLICY_CLAUSE) == ()


# --------------------------------------------------------------------------
# The policy parser
# --------------------------------------------------------------------------


def test_every_policy_document_parses_into_clauses() -> None:
    documents = load_policies(POLICIES)
    assert set(documents) == {"refund.v1", "exchange.v1", "transfer.v1"}
    for document in documents.values():
        assert document.clauses, f"{document.name} parsed into no clauses"
        assert len(set(dict(document.clauses))) == len(document.clauses)


def test_the_parser_keeps_near_identical_clauses_apart() -> None:
    """refund.v1's three refund windows differ by a number and a word.

    A parse that collapsed them would make "the agent applied the wrong window"
    unstateable, which is the defect CALL-02 seeds.
    """
    windows = load_policies(POLICIES)["refund.v1"].as_mapping()
    assert {"2.1", "2.2", "2.3"} <= set(windows)
    assert len({windows["2.1"], windows["2.2"], windows["2.3"]}) == 3


def test_a_document_with_no_clauses_is_refused_rather_than_returned_empty() -> None:
    with pytest.raises(Exception, match="no clauses parsed"):
        parse_policy("empty.v1", "# Nothing here\n\nJust prose.\n")


def test_a_document_repeating_a_clause_is_refused() -> None:
    with pytest.raises(Exception, match="twice"):
        parse_policy("dupe.v1", '**1.1** "first"\n\n**1.1** "second"\n\n---\n')


def test_clause_text_of_and_has_agree() -> None:
    document = load_policies(POLICIES)["refund.v1"]
    assert document.has("2.4")
    assert document.text_of("2.4")
    assert not document.has("99.9")
    with pytest.raises(Exception, match="no clause"):
        document.text_of("99.9")


# --------------------------------------------------------------------------
# The fact corpus itself
# --------------------------------------------------------------------------


def test_the_context_record_reaches_the_ground_truth_with_its_provenance() -> None:
    call = parse_call(TRANSCRIPTS / "CALL-01.txt")
    context = build_context(call, load_policies(POLICIES), policy_tool=POLICY_TOOL)
    assert context.ground_truth.context_value("account_zip") == "00312"
    zips = [
        fact
        for fact in context.ground_truth.of_source(FactSource.CONTEXT)
        if fact.key == "account_zip"
    ]
    assert len(zips) == 1
    assert "line " in zips[0].reference, (
        "the context fact does not carry its source line, so a reader cannot "
        "find the value the verdict rests on"
    )


def test_a_tool_result_contributes_its_status_and_its_detail() -> None:
    """The detail is where an eligibility reason lives, and several findings
    rest on the agent having had it."""
    call = parse_call(TRANSCRIPTS / "CALL-01.txt")
    context = build_context(call, {}, policy_tool=POLICY_TOOL)
    corpus = context.ground_truth.corpus
    assert "refused_ineligible successful=false" in corpus
    assert "window_closed" in corpus, "a result detail did not reach the ground truth"


def test_facts_are_normalized_to_single_spaces() -> None:
    """A wrapped event reassembles with single spaces, and a fact keeps that.

    A grounding comparison against text carrying the source's line breaks would
    fail on values that are present, which is a false failure on the tier that
    can fail a whole run.
    """
    fact = Fact(source=FactSource.EVENT, reference="event 1", key="k", text="a b")
    assert fact.text == "a b"
    call = parse_call(TRANSCRIPTS / "CALL-01.txt")
    context = build_context(call, {}, policy_tool=POLICY_TOOL)
    assert not any("\n" in f.text or "  " in f.text for f in context.ground_truth.facts)


def _parsed_from(source: str, path: Path) -> Call:
    """Write `source` and parse it, so a control can mutate a transcript
    without touching the corpus."""
    path.write_text(source, encoding="utf-8", newline="")
    return parse_call(path)


def test_a_failed_policy_retrieval_puts_no_clause_into_ground_truth(tmp_path: Path) -> None:
    """`_retrieved_documents` said "documents named by a **successful**
    retrieval" and read only the invocation, never its result.

    A `fetch_policy` that errored still put every clause of that document into
    ground truth, so `governing_clause_not_applied` would charge the agent with
    ignoring clauses of a document that never arrived. All eight retrievals in
    the design set succeed, so no corpus call and no test reached the branch --
    which is why this control plants one rather than looking for one.
    """
    source = (REPO_ROOT / "corpus" / "transcripts" / "CALL-02.txt").read_text(encoding="utf-8")
    policies = load_policies(REPO_ROOT / "corpus" / "policies")

    good = build_context(
        _parsed_from(source, tmp_path / "CALL-02.txt"), policies, policy_tool=POLICY_TOOL
    )
    assert [document.name for document in good.retrieved_policies] == ["refund.v1"], (
        "the fixture no longer retrieves a policy successfully"
    )

    failed_source = source.replace(
        "t2 -> retrieved successful=true :: refund.v1 returned; 14 clauses",
        "t2 -> error successful=false :: policy service unreachable",
    )
    assert failed_source != source, "the retrieval result line has moved"
    failed = build_context(
        _parsed_from(failed_source, tmp_path / "CALL-02-failed.txt"),
        policies,
        policy_tool=POLICY_TOOL,
    )
    assert failed.retrieved_policies == (), (
        "a failed fetch_policy still put its clauses into ground truth"
    )


# --------------------------------------------------------------------------
# Every write of a state variable, not the last one
# --------------------------------------------------------------------------


def _state_stream(*writes: tuple[str, int]) -> tuple[StateEvent, ...]:
    """A stream of `STATE` events at the indices given, and nothing else."""
    return tuple(
        StateEvent(
            index=index,
            started_at_ms=index * 1000,
            ended_at_ms=index * 1000,
            kind=EventKind.STATE,
            body=f"{name} := true",
            citation_id=f"F{index}",
            source_lines=(index,),
            name=name,
            value="true",
        )
        for name, index in writes
    )


def test_a_variable_written_twice_keeps_both_indices() -> None:
    """The defect this helper exists for, stated as the thing that goes wrong.

    Three checks were built on `{event.name: event.index for event in events}`,
    which keeps only the **last** write of each name. A variable set between two
    asks and set again after the last ask then read as never set between them,
    and a verification recorded before a gated write and refreshed after it read
    as no verification below the write. Both are false violations, and both are
    about a variable whose history is exactly what the check is asking.
    """
    events = _state_stream(("holder_confirmed", 4), ("holder_confirmed", 9))
    assert state_writes(events) == {"holder_confirmed": (4, 9)}

    naive = {event.name: event.index for event in events}
    assert naive == {"holder_confirmed": 9}, (
        "the comprehension no longer loses the first write, so this control proves nothing"
    )


def test_the_indices_come_back_in_stream_order() -> None:
    """Callers ask `first < index < last` and `index > invocation`, so order is
    part of the contract rather than an accident of the dict."""
    assert state_writes(_state_stream(("a", 2), ("b", 3), ("a", 7))) == {"a": (2, 7), "b": (3,)}


def test_a_stream_with_no_state_events_maps_nothing() -> None:
    """CALL-12 emits no state event at all, so a check asking about a variable
    there must get an empty history rather than a `KeyError`."""
    assert state_writes(()) == {}
    assert state_writes(()).get("holder_confirmed", ()) == ()
