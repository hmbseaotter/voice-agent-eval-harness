"""Extraction-tier tests.

THE ONE THAT MATTERS IS THE REASSEMBLY PAIR. W19 records that the reference
implementation's extraction conformance test checked index sequences, kind
vocabulary and view agreement -- a genuinely good list -- but nothing about turn
reassembly, and it never re-read the source transcript. The single failure mode
the tier exists to prevent was the one its test could not see.

So reassembly is asserted twice, because the two assertions fail for different
reasons:

  * against a FIXTURE with a hardcoded expected string -- independent of the
    parser and of any reconstruction logic here, so a parser that drops a
    fragment cannot make the expectation move with it;
  * against the REAL CORPUS by re-reading each transcript and rebuilding the
    expected body from its raw lines -- the half W19 was missing, and the half
    that keeps covering transcripts authored after it was written.

The v2 additions are the tool-pairing checks. A dangling call or an orphan
result means the log cannot say whether an action completed, and every ordering
assertion built on it would be reasoning about a confirmation that is not there.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.core.artifact import build_payload, content_hash, verify_artifact, write_artifact
from harness.core.events import (
    FACT_KINDS,
    SPEECH_KINDS,
    Call,
    DisconnectionReason,
    EventKind,
    MalformedTranscriptError,
    SpeechEvent,
    StateEvent,
    ToolCallEvent,
    ToolResultEvent,
    ToolStatus,
    UnknownTokenError,
    citation_population,
    timing,
)
from harness.corpus.text_adapter import parse_call
from harness.extract import extract, main

REPO_ROOT: Path = Path(__file__).resolve().parents[1]
FIXTURES: Path = Path(__file__).resolve().parent / "fixtures"
TRANSCRIPTS: Path = REPO_ROOT / "corpus" / "transcripts"


# --------------------------------------------------------------------------
# Reassembly -- the W19 fix
# --------------------------------------------------------------------------

#: Written out by hand from tests/fixtures/wrapped.txt. Deliberately a literal:
#: nothing in the code under test contributes to this expectation.
EXPECTED_WRAPPED_TURN: str = (
    "This turn is wrapped across exactly three source lines so that the "
    "reassembly invariant has something to assert against."
)

EXPECTED_WRAPPED_VALUE: str = (
    "a variable value that also wraps, to prove the rule covers assignments and not only turns"
)

EXPECTED_WRAPPED_CONTEXT: str = (
    "a context value that also wraps, to prove the rule covers the context block "
    "and not only the event stream"
)


def test_three_line_wrap_reassembles_to_a_hardcoded_string() -> None:
    call = parse_call(FIXTURES / "wrapped.txt")
    turn = call.events[0]
    assert isinstance(turn, SpeechEvent)
    assert len(turn.source_lines) == 3, "the fixture's first turn must span three source lines"
    assert turn.body == EXPECTED_WRAPPED_TURN


def test_wrapped_state_value_reassembles_too() -> None:
    """W16: in the reference the wrapping rule covered turns, so a wrapped
    variable value silently lost its leading fragment while the adjacent branch
    handled the identical case correctly."""
    call = parse_call(FIXTURES / "wrapped.txt")
    assignment = call.events[1]
    assert isinstance(assignment, StateEvent)
    assert len(assignment.source_lines) == 2
    assert assignment.name == "long_value"
    assert assignment.value == EXPECTED_WRAPPED_VALUE


def test_the_context_block_wraps_by_the_same_rule() -> None:
    """New in v2, and the same reasoning: one rule over the whole file rather
    than a rule per section, so no section can develop its own bug."""
    call = parse_call(FIXTURES / "wrapped.txt")
    context = dict(call.context)
    assert context["long_context_value"] == EXPECTED_WRAPPED_CONTEXT
    assert context["identity_verified"] == "false"


def _expected_body_from_source(path: Path, source_lines: tuple[int, ...]) -> str:
    """Rebuild an event's body by re-reading the transcript file itself.

    This is the half W19 was missing. It reads the raw lines the parser claims
    the event came from, takes the fifth pipe-delimited field of each, and joins
    them -- so a parser that silently drops a fragment produces a body this
    function does not.
    """
    raw = path.read_text(encoding="utf-8").split("\n")
    fragments = []
    for line_number in source_lines:
        fields = raw[line_number - 1].split("|")
        assert len(fields) == 5, f"line {line_number} is not a five-field event line"
        fragments.append(fields[4].strip())
    return " ".join(fragment for fragment in fragments if fragment)


@pytest.mark.parametrize("transcript", sorted(TRANSCRIPTS.glob("*.txt")), ids=lambda p: p.stem)
def test_every_wrapped_event_matches_its_source_lines(transcript: Path) -> None:
    call = parse_call(transcript)
    wrapped = [event for event in call.events if len(event.source_lines) > 1]
    assert wrapped, f"{transcript.name} carries no wrapped event to assert against"
    for event in wrapped:
        assert event.body == _expected_body_from_source(transcript, event.source_lines)


def test_the_corpus_contains_a_three_line_wrap() -> None:
    """The acceptance criterion names three source lines specifically, and a
    corpus of only two-line wraps would pass the test above while leaving the
    stated case unexercised."""
    spans = [
        len(event.source_lines)
        for transcript in sorted(TRANSCRIPTS.glob("*.txt"))
        for event in parse_call(transcript).events
    ]
    assert max(spans) >= 3


# --------------------------------------------------------------------------
# Aborts versus counted failures -- the distinction is the requirement
# --------------------------------------------------------------------------


def test_unknown_tool_status_aborts_naming_file_line_and_token() -> None:
    with pytest.raises(UnknownTokenError) as caught:
        parse_call(FIXTURES / "unknown_status.txt")
    error = caught.value
    assert error.token == "sortof"
    assert error.vocabulary == "tool status"
    assert error.line_number == 26, "the line the offending token actually appears on"
    assert "unknown_status.txt" in error.path
    message = str(error)
    # The refusal names the good tokens as well as the bad one; naming only the
    # offender makes the reader go looking.
    assert "refused_ineligible" in message


def test_malformed_lines_are_counted_and_not_discarded() -> None:
    """W18 was the absence of this counter; W19 was a test that crashed rather
    than reporting the violation it had already recorded."""
    call = parse_call(FIXTURES / "malformed.txt")
    reasons = " | ".join(line.reason for line in call.unparsed)
    assert len(call.unparsed) == 5, reasons
    assert "expected 5 pipe-delimited fields" in reasons
    assert "out of sequence" in reasons
    assert "unknown event kind" in reasons
    assert "continuation line with no event above it" in reasons
    assert "ends" in reasons and "before it starts" in reasons
    # The well-formed lines still parse. A file with a defect is not a file with
    # nothing in it.
    assert len(call.events) == 4


def test_a_rejected_body_does_not_desynchronize_the_next_event() -> None:
    """One defect costs one finding.

    Asserted over the **unparsed reasons**, not the surviving event indices.
    That distinction is the whole test: the desync it is named for left the
    index expectation un-advanced on two rejection paths, so the next line --
    entirely valid, and commented "Another well-formed line" in the fixture --
    was reported out of sequence. The old assertion compared event indices,
    which the bug does not disturb, so it passed for as long as the bug existed.

    The fixture has five deliberate defects on five lines. If a sixth line
    appears here, a good line is being punished for a bad one.
    """
    call = parse_call(FIXTURES / "malformed.txt")
    damaged = [line.line_number for line in call.unparsed]
    assert damaged == [24, 26, 27, 28, 29], [
        (line.line_number, line.reason) for line in call.unparsed
    ]

    source = (FIXTURES / "malformed.txt").read_text(encoding="utf-8").splitlines()
    for line_number in damaged:
        assert "well-formed" not in source[line_number - 1], (
            f"line {line_number} is commented well-formed and was rejected anyway"
        )


def test_a_rejected_line_with_a_readable_index_resyncs_the_expectation() -> None:
    """The mechanism behind the test above. A line the grammar cannot read may
    still declare where it sits, and the field-count path -- the one that was
    not advancing -- is reachable with a perfectly readable index."""
    call = parse_call(FIXTURES / "malformed.txt")
    # Line 24 declares index 2 and is rejected for its field count; line 25
    # declares index 3 and is well formed. It survives only because the
    # expectation resynced past the damaged line.
    assert 3 in [event.index for event in call.events]


def test_a_malformed_result_is_counted_rather_than_blamed_on_its_invocation(
    tmp_path: Path,
) -> None:
    """A malformed line is a counting problem, which is this module's first
    stated principle and a requirement of the specification.

    The pairing check runs over surviving events, so a `TOOL_RESULT` rejected
    into `unparsed` used to leave its `TOOL_CALL` looking dangling -- and the
    abort named the well-formed invocation and never mentioned the malformed
    line. One changed arrow was enough.
    """
    source = (FIXTURES / "wrapped.txt").read_text(encoding="utf-8")
    broken = source.replace("t1 -> ", "t1 => ", 1)
    assert broken != source, "the fixture no longer contains the body being damaged"
    path = tmp_path / "CALL-90.txt"
    path.write_text(broken, encoding="utf-8", newline="")

    call = parse_call(path)
    assert len(call.unparsed) == 1
    only = call.unparsed[0]
    assert "tool result" in only.reason
    assert only.line_number > 0


def test_a_dangling_call_in_a_clean_file_still_aborts() -> None:
    """The other half. Suppressing the pairing abort when a line is unreadable
    must not suppress it when every line is readable -- otherwise the fix for a
    misleading message would have deleted the check."""
    with pytest.raises(MalformedTranscriptError) as caught:
        parse_call(FIXTURES / "dangling_call.txt")
    assert "no result" in str(caught.value)


def test_a_nonzero_unparsed_count_fails_the_run(tmp_path: Path) -> None:
    exit_code = main(
        [
            "--transcripts",
            str(FIXTURES),
            "--out",
            str(tmp_path / "artifact.json"),
            "--corpus-version-file",
            str(REPO_ROOT / "corpus" / "CORPUS_VERSION"),
        ]
    )
    assert exit_code != 0


def test_the_real_corpus_parses_with_a_zero_unparsed_count() -> None:
    calls = extract(TRANSCRIPTS)
    # Keyed on the DECLARATION, not the directory. Replacing the hard-coded 12
    # with a glob produced an assertion that could not fail, because extract()
    # globs the same directory -- a brittle check swapped for a vacuous one.
    declared = [
        line.strip()
        for line in (REPO_ROOT / "corpus" / "DESIGN_SET").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    assert sorted(c.record.call_id for c in calls) == sorted(declared)
    assert sum(len(call.unparsed) for call in calls) == 0


# --------------------------------------------------------------------------
# Tool pairing -- the structural half of the dependency chain (v2)
# --------------------------------------------------------------------------


def test_a_result_with_no_earlier_invocation_aborts() -> None:
    with pytest.raises(MalformedTranscriptError, match="no earlier invocation"):
        parse_call(FIXTURES / "orphan_result.txt")


def test_an_invocation_with_no_result_aborts() -> None:
    """A call whose outcome is never confirmed cannot be reasoned about, and
    every ordering assertion built on it would be reasoning about a
    confirmation that is not there."""
    with pytest.raises(MalformedTranscriptError, match="no result"):
        parse_call(FIXTURES / "dangling_call.txt")


@pytest.mark.parametrize("transcript", sorted(TRANSCRIPTS.glob("*.txt")), ids=lambda p: p.stem)
def test_every_result_follows_its_invocation_in_the_corpus(transcript: Path) -> None:
    call = parse_call(transcript)
    calls_at = {e.tool_call_id: e.index for e in call.events if isinstance(e, ToolCallEvent)}
    for event in call.events:
        if isinstance(event, ToolResultEvent):
            assert event.tool_call_id in calls_at
            assert calls_at[event.tool_call_id] < event.index


def test_successful_agrees_with_status_across_the_corpus() -> None:
    """`successful` is declared, not derived -- so a disagreement is a
    representable data-integrity defect rather than a parse error. None is
    seeded, so any disagreement here is an accident."""
    for transcript in sorted(TRANSCRIPTS.glob("*.txt")):
        call = parse_call(transcript)
        for event in call.events:
            if isinstance(event, ToolResultEvent):
                assert event.successful == event.status.implies_success, (
                    f"{call.record.call_id} event {event.index}: "
                    f"{event.status.value} with successful={event.successful}"
                )


# --------------------------------------------------------------------------
# File-level defects
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("find", "replace", "expected"),
    [
        ("#format:", "#fmt:", "first line must be"),
        ("call_id: CALL-90\n", "", "missing [call] key"),
        ("environment: test", "environment_kind: test", "unknown [call] key"),
        ("call_id: CALL-90", "call_id: booking-90", "does not match"),
        ("duration_ms: 20000", "duration_ms: a while", "not an integer"),
        ("environment: test", "environment: sandbox", "environment 'sandbox' is not one of"),
        ("disconnection_reason: caller_hangup", "disconnection_reason: gave_up", "is not one of"),
        ("outcome: resolved", "outcome: sorted_out", "outcome 'sorted_out' is not one of"),
        ("[events]", "", "missing section"),
        ("[context]", "", "missing section"),
    ],
    ids=[
        "bad-header",
        "missing-key",
        "unknown-key",
        "bad-call-id",
        "bad-duration",
        "bad-environment",
        "bad-disconnection",
        "bad-outcome",
        "no-events",
        "no-context",
    ],
)
def test_file_level_defects_abort_by_name(
    tmp_path: Path, find: str, replace: str, expected: str
) -> None:
    source = (FIXTURES / "wrapped.txt").read_text(encoding="utf-8")
    broken = tmp_path / "broken.txt"
    broken.write_text(source.replace(find, replace, 1), encoding="utf-8", newline="")
    with pytest.raises(MalformedTranscriptError) as caught:
        parse_call(broken)
    assert expected in str(caught.value)


# --------------------------------------------------------------------------
# Citation populations -- the W1 fix
# --------------------------------------------------------------------------


def test_speech_and_facts_are_two_independent_citation_populations() -> None:
    call = parse_call(TRANSCRIPTS / "CALL-02.txt")
    speech = [e.citation_id for e in call.events if e.kind in (EventKind.CALLER, EventKind.AGENT)]
    facts = [
        e.citation_id for e in call.events if e.kind not in (EventKind.CALLER, EventKind.AGENT)
    ]
    assert speech == [f"T{n}" for n in range(1, len(speech) + 1)]
    assert facts == [f"F{n}" for n in range(1, len(facts) + 1)]
    assert speech and facts
    assert len(set(speech + facts)) == len(speech + facts)


def test_the_call_record_and_context_are_read_verbatim() -> None:
    call = parse_call(TRANSCRIPTS / "CALL-01.txt")
    assert call.record.disconnection_reason is DisconnectionReason.CALLER_HANGUP
    assert call.record.outcome == "resolved"
    context = dict(call.context)
    # The context record is what makes "the agent had this value" checkable.
    assert context["identity_verified"] == "false"
    assert context["account_zip"] == "00312"
    assert context["account_email"] == "r.adeyemi@example.com"


def test_typed_events_carry_their_kind_specific_fields() -> None:
    call = parse_call(TRANSCRIPTS / "CALL-01.txt")
    results = [e for e in call.events if isinstance(e, ToolResultEvent)]
    statuses = {r.status for r in results}
    assert ToolStatus.RETRIEVED in statuses
    assert ToolStatus.REFUSED_INELIGIBLE in statuses
    refused = next(r for r in results if r.status is ToolStatus.REFUSED_INELIGIBLE)
    assert refused.successful is False
    assert refused.detail is not None and "window closed" in refused.detail


def test_every_event_carries_a_start_and_an_end() -> None:
    """v2's correction to D33. A single stamp cannot express how long an
    utterance took, which is what the first format got wrong."""
    for transcript in sorted(TRANSCRIPTS.glob("*.txt")):
        call = parse_call(transcript)
        for event in call.events:
            started, ended = timing(event)
            assert ended >= started
            assert event.duration_ms == ended - started


# --------------------------------------------------------------------------
# The frozen artifact
# --------------------------------------------------------------------------


def test_the_artifact_hash_is_stable_across_extractions() -> None:
    first = build_payload(extract(TRANSCRIPTS), "0.2.0", REPO_ROOT)
    second = build_payload(extract(TRANSCRIPTS), "0.2.0", REPO_ROOT)
    assert content_hash(first) == content_hash(second)


def test_the_artifact_records_repo_relative_paths() -> None:
    """W23: absolute paths would make the hash machine-dependent, so the same
    corpus would hash differently for two readers."""
    payload = build_payload(extract(TRANSCRIPTS), "0.2.0", REPO_ROOT)
    paths = [call["source_path"] for call in payload["calls"]]
    assert paths == sorted(paths), "calls are ordered, not filesystem-enumerated"
    for path in paths:
        assert path.startswith("corpus/transcripts/")
        assert "\\" not in path and ":" not in path


def test_the_written_artifact_verifies_by_recomputation(tmp_path: Path) -> None:
    payload = build_payload(extract(TRANSCRIPTS), "0.2.0", REPO_ROOT)
    out = tmp_path / "artifact.json"
    digest = write_artifact(out, payload)
    matches, recorded, recomputed = verify_artifact(out)
    assert matches, f"recorded {recorded}, recomputed {recomputed}"
    assert recorded == digest


def test_a_tampered_artifact_fails_verification(tmp_path: Path) -> None:
    payload = build_payload(extract(TRANSCRIPTS), "0.2.0", REPO_ROOT)
    out = tmp_path / "artifact.json"
    write_artifact(out, payload)
    text = out.read_text(encoding="utf-8")
    out.write_text(text.replace("BK-4471-QD", "BK-0000-XX"), encoding="utf-8", newline="\n")
    matches, _, _ = verify_artifact(out)
    assert not matches


# --------------------------------------------------------------------------
# The [context] continuation rule (format spec 3.1)
# --------------------------------------------------------------------------


def _with_context(tmp_path: Path, block: str) -> Call:
    """Parse a fixture whose `[context]` block has `block` prepended."""
    source = (FIXTURES / "wrapped.txt").read_text(encoding="utf-8")
    path = tmp_path / "CALL-90.txt"
    path.write_text(
        source.replace("[context]\n", "[context]\n" + block, 1), encoding="utf-8", newline=""
    )
    return parse_call(path)


def test_a_context_continuation_containing_an_assignment_is_not_a_new_variable(
    tmp_path: Path,
) -> None:
    """The corruption this rule exists to stop. Under the old content-based
    rule the second line became a variable of its own, so the record carried a
    fact nobody wrote -- W17, in the one block whose rule the format spec had
    never stated, and the block that decides whether a finding's owner is the
    agent or the platform."""
    call = _with_context(
        tmp_path,
        "note := the caller said the following\n    delivery := was never mentioned on the call\n",
    )
    context = dict(call.context)
    assert "delivery" not in context, "an indented continuation was read as an assignment"
    assert context["note"] == (
        "the caller said the following delivery := was never mentioned on the call"
    )


def test_a_context_continuation_beginning_with_a_hash_keeps_its_text(tmp_path: Path) -> None:
    """The other half: an indented `#` is content, not a comment. Under the old
    rule the tail was dropped in silence -- W16."""
    call = _with_context(
        tmp_path, "note := the caller quoted a reference\n    #4471 and then hung up\n"
    )
    context = dict(call.context)
    assert context["note"] == "the caller quoted a reference #4471 and then hung up"


def test_an_unindented_assignment_is_still_a_new_variable(tmp_path: Path) -> None:
    """The false-positive half. A rule that swallowed genuine assignments into
    the value above them would be the same defect pointing the other way."""
    call = _with_context(tmp_path, "note := first value\ndelivery := second value\n")
    context = dict(call.context)
    assert context["note"] == "first value"
    assert context["delivery"] == "second value"


def test_an_unindented_line_that_is_not_an_assignment_aborts(tmp_path: Path) -> None:
    with pytest.raises(MalformedTranscriptError) as caught:
        _with_context(tmp_path, "note := first value\nthis is not an assignment\n")
    assert "not indented as a continuation" in str(caught.value)


def test_the_corpus_context_wrapping_survives_a_round_trip() -> None:
    """W16 on real data. CALL-11's disclosure value wraps across three source
    lines; asserted against the source file rather than the parser's own output,
    which is the W19 fix applied to this block."""
    call = parse_call(REPO_ROOT / "corpus" / "transcripts" / "CALL-11.txt")
    value = dict(call.context)["disclosure_refund_timing"]
    source = (REPO_ROOT / "corpus" / "transcripts" / "CALL-11.txt").read_text(encoding="utf-8")
    start = source.index("disclosure_refund_timing :=")
    fragments = source[start:].split("\n")
    assert fragments[1].startswith("    "), "the fixture no longer wraps; pick another value"
    for fragment in fragments[:3]:
        tail = fragment.split(":=", 1)[-1].strip()
        assert tail and tail in value, f"source fragment {tail!r} is missing from the parsed value"


def test_speech_and_fact_kinds_partition_the_event_kinds() -> None:
    """M6. `FACT_KINDS` was declared `Final` and referenced nowhere, because
    `citation_population` derived `"F"` as *not speech*. A ninth kind would have
    been classified `"F"` whether or not anyone added it to the tuple, and the
    tuple would have been quietly wrong while looking authoritative.

    It is read now, and this asserts the property that makes reading it safe:
    every kind is in exactly one of the two.
    """
    assert set(SPEECH_KINDS) | set(FACT_KINDS) == set(EventKind)
    assert not set(SPEECH_KINDS) & set(FACT_KINDS)
    for kind in EventKind:
        assert citation_population(kind) in {"T", "F"}


def test_the_two_citation_populations_are_both_non_empty() -> None:
    """The negative control. A partition test passes if one side swallows
    everything, and W1 is exactly what happens when the fact population is
    empty: every established-fact line uncitable by construction, and a
    hallucination detector that never catches one."""
    assert SPEECH_KINDS and FACT_KINDS
    assert {citation_population(kind) for kind in EventKind} == {"T", "F"}


# --------------------------------------------------------------------------
# Abort paths that were reachable, specified, and untested (T4)
# --------------------------------------------------------------------------


def _fixture_with(tmp_path: Path, old: str, new: str, *, name: str = "CALL-90.txt") -> Path:
    """A copy of the wrapped fixture with one substitution applied."""
    source = (FIXTURES / "wrapped.txt").read_text(encoding="utf-8")
    assert old in source, f"the fixture no longer contains {old!r}"
    path = tmp_path / name
    path.write_text(source.replace(old, new, 1), encoding="utf-8", newline="")
    return path


def test_an_unknown_disclosure_state_aborts_naming_it(tmp_path: Path) -> None:
    """`event-model.md` §3.3 states the abort rule for **all four** closed
    vocabularies. Only tool status had a test, so three of the four were
    specified and unproven -- and a vocabulary compared without validation is
    the live risk on a freshly authored corpus that D-record argues for."""
    source = (FIXTURES / "wrapped.txt").read_text(encoding="utf-8")
    disclosure = (
        '  6 |  0:21.000 |  0:24.000 | DISCLOSURE  | recording_notice -> mumbled :: "Hello."\n'
    )
    path = tmp_path / "CALL-90.txt"
    path.write_text(source.rstrip("\n") + "\n" + disclosure, encoding="utf-8", newline="")
    with pytest.raises(UnknownTokenError) as caught:
        parse_call(path)
    message = str(caught.value)
    assert "mumbled" in message
    assert "delivered" in message, "the refusal should name the good tokens too"


def test_a_duplicate_tool_call_id_aborts(tmp_path: Path) -> None:
    source = (FIXTURES / "wrapped.txt").read_text(encoding="utf-8")
    second = '  6 |  0:21.000 |  0:21.200 | TOOL_CALL   | t1 do_something(arg="again")\n'
    path = tmp_path / "CALL-90.txt"
    path.write_text(source.rstrip("\n") + "\n" + second, encoding="utf-8", newline="")
    with pytest.raises(MalformedTranscriptError) as caught:
        parse_call(path)
    assert "used twice" in str(caught.value)


def test_a_missing_section_aborts_naming_it(tmp_path: Path) -> None:
    path = _fixture_with(tmp_path, "[context]", "[ctx]")
    with pytest.raises(MalformedTranscriptError) as caught:
        parse_call(path)
    assert "context" in str(caught.value)


def test_a_duplicate_call_key_aborts_naming_it(tmp_path: Path) -> None:
    path = _fixture_with(tmp_path, "environment: test", "environment: test\nenvironment: test")
    with pytest.raises(MalformedTranscriptError) as caught:
        parse_call(path)
    assert "duplicate" in str(caught.value)
    assert "environment" in str(caught.value)


def test_an_empty_file_aborts(tmp_path: Path) -> None:
    path = tmp_path / "CALL-90.txt"
    path.write_text("", encoding="utf-8")
    with pytest.raises(MalformedTranscriptError) as caught:
        parse_call(path)
    assert "empty" in str(caught.value) or "first line" in str(caught.value)


def test_an_empty_speech_body_is_rejected(tmp_path: Path) -> None:
    """A turn with no words is not a turn. It would otherwise reach the citation
    universe as an empty citable line, which is the W1 family."""
    source = (FIXTURES / "wrapped.txt").read_text(encoding="utf-8")
    lines = source.splitlines()
    # A single-line event, deliberately: emptying the first line of a *wrapped*
    # one leaves its continuations to supply a body, which is not the case
    # under test.
    for position, line in enumerate(lines):
        if "| CALLER" in line and not lines[position + 1].lstrip().startswith("|"):
            head, _, _ = line.rpartition("|")
            lines[position] = head + "| "
            break
    else:  # pragma: no cover - the fixture always has a single-line speech event
        pytest.fail("the fixture has no unwrapped speech event")
    path = tmp_path / "CALL-90.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="")
    call = parse_call(path)
    assert call.unparsed, "an empty speech body produced no unparsed line"


@pytest.mark.parametrize(
    ("old", "new", "kind"),
    [
        ('t1 do_something(arg="value")', "t1 do_something", "TOOL_CALL"),
        ("long_value := a variable value", "long_value a variable value", "STATE"),
    ],
    ids=["tool-call-without-parentheses", "state-without-an-assignment"],
)
def test_a_body_failing_its_kind_grammar_is_counted(
    tmp_path: Path, old: str, new: str, kind: str
) -> None:
    """Per-kind body grammars had no failure case. A body the grammar cannot
    read is a counting problem, not an abort -- the same rule the whole adapter
    is built on, and untested for five of the eight kinds."""
    source = (FIXTURES / "wrapped.txt").read_text(encoding="utf-8")
    if old not in source:
        pytest.skip(f"the fixture no longer contains {old!r}")
    path = tmp_path / "CALL-90.txt"
    path.write_text(source.replace(old, new, 1), encoding="utf-8", newline="")
    call = parse_call(path)
    assert call.unparsed, f"a malformed {kind} body produced no unparsed line"


def test_extraction_over_a_directory_with_no_transcripts_refuses(tmp_path: Path) -> None:
    with pytest.raises((FileNotFoundError, SystemExit, MalformedTranscriptError)):
        extract(tmp_path)


def test_a_trailing_carriage_return_is_stripped(tmp_path: Path) -> None:
    """The format specification says a trailing CR is stripped rather than
    rejected, so a file edited on Windows parses. Nothing checked it."""
    source = (FIXTURES / "wrapped.txt").read_text(encoding="utf-8")
    path = tmp_path / "CALL-90.txt"
    path.write_bytes(source.replace("\n", "\r\n").encode("utf-8"))
    call = parse_call(path)
    assert not call.unparsed, [line.reason for line in call.unparsed]
    assert call.record.call_id == "CALL-90"


def test_a_repeated_section_marker_aborts_naming_its_lines(tmp_path: Path) -> None:
    """P3. `_sections` assigned `found[marker] = offset` over the whole file, so
    a second `[call]` overwrote the first and everything between them was never
    read. A doubled block parsed cleanly and reported the **second** `call_id`.

    That is the worst shape a silent failure takes: it does not lose a value,
    it substitutes one. `transcript-format.md` §1 says "four parts, in order";
    the parser enforced the order and not the cardinality.
    """
    source = (FIXTURES / "wrapped.txt").read_text(encoding="utf-8")
    head, _, rest = source.partition("[context]")
    doubled = head + head.split("\n", 1)[1].replace("CALL-90", "CALL-91") + "[context]" + rest
    path = tmp_path / "CALL-90.txt"
    path.write_text(doubled, encoding="utf-8", newline="")

    with pytest.raises(MalformedTranscriptError) as caught:
        parse_call(path)
    message = str(caught.value)
    assert "repeated" in message
    assert "[call]" in message


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("started_at", "2027-03-14 09:12:03Z"),
        ("answered_at", "2027-03-14T09:12:05Z"),
        ("ended_at", "2027-03-14T09:13:23.329"),
    ],
    ids=["no-T-separator", "no-milliseconds", "no-Z-suffix"],
)
def test_a_malformed_call_timestamp_aborts_naming_it(
    tmp_path: Path, field: str, value: str
) -> None:
    """P10. All three stamps were stored as raw strings with no format check,
    while `transcript-format.md` §2 requires UTC ISO-8601 with millisecond
    precision and a `Z`.

    It matters more than a format nit:
    `test_header_duration_reconciles_with_the_event_log` calls
    `datetime.fromisoformat` on these strings, so a malformed stamp surfaced as
    a `ValueError` raised from inside a hygiene test rather than as a named
    parse failure at the point the file was read.
    """
    source = (FIXTURES / "wrapped.txt").read_text(encoding="utf-8")
    original = next(line for line in source.splitlines() if line.startswith(f"{field}:"))
    path = tmp_path / "CALL-90.txt"
    path.write_text(source.replace(original, f"{field}: {value}", 1), encoding="utf-8", newline="")

    with pytest.raises(MalformedTranscriptError) as caught:
        parse_call(path)
    message = str(caught.value)
    assert field in message
    assert "millisecond" in message


def test_a_negative_duration_aborts(tmp_path: Path) -> None:
    """`duration_ms` was checked for integrality and not for sign, so a call
    could report having lasted a negative time and parse."""
    source = (FIXTURES / "wrapped.txt").read_text(encoding="utf-8")
    original = next(line for line in source.splitlines() if line.startswith("duration_ms:"))
    path = tmp_path / "CALL-90.txt"
    path.write_text(source.replace(original, "duration_ms: -1", 1), encoding="utf-8", newline="")

    with pytest.raises(MalformedTranscriptError) as caught:
        parse_call(path)
    assert "negative" in str(caught.value)


# --------------------------------------------------------------------------
# Encoding artifacts, and a message that could not be produced
# --------------------------------------------------------------------------


def test_a_byte_order_mark_does_not_refuse_a_transcript(tmp_path: Path) -> None:
    """A BOM is an encoding artifact, not a defect in a call.

    `_read_lines` already strips a trailing CR rather than rejecting it, on the
    stated ground that failing a corpus for its line endings would be a refusal
    with no defect behind it. A leading byte-order mark is the same argument one
    artifact over: invisible in every editor that writes one, carrying nothing
    about the call, and exactly what `Out-File -Encoding utf8` produces -- which
    this project has been bitten by once already, in a commit subject.

    Left unstripped it reached the header comparison as part of the first line,
    and the transcript was refused with a message quoting the mark as an escape.
    That reads as a corrupt file rather than as an encoding artifact, which is
    the difference between a reader fixing it in seconds and a reader opening a
    hex editor.
    """
    source = (TRANSCRIPTS / "CALL-11.txt").read_text(encoding="utf-8")
    marked = tmp_path / "CALL-11.txt"
    marked.write_bytes(b"\xef\xbb\xbf" + source.encode("utf-8"))

    call = parse_call(marked)
    assert call.record.call_id == "CALL-11"
    assert not call.unparsed, "a byte-order mark produced unparsed lines"

    plain = parse_call(TRANSCRIPTS / "CALL-11.txt")
    assert [event.body for event in call.events] == [event.body for event in plain.events], (
        "the marked copy parsed to a different event stream than the plain one, so the "
        "mark reached content rather than being stripped at the edge"
    )


def test_an_empty_file_is_reported_as_empty(tmp_path: Path) -> None:
    """The message existed and could not be produced.

    `parse_call` chose between "first line must be ..." and "file is empty" on
    `not lines` -- and `"".split("\\n")` is `[""]`, never `[]`, so `lines` was
    truthy for every input including an empty file. The empty case therefore
    reported that its first line must be the header, `found ''`: true, and the
    least useful available way to say a file has nothing in it.

    A branch that cannot be reached is not a fallback. It is a claim the code
    makes about its own behavior that nothing tests, which is this repository's
    recurring subject.
    """
    for name, content in (("empty.txt", ""), ("blank.txt", "\n\n   \n")):
        path = tmp_path / name
        path.write_text(content, encoding="utf-8")
        with pytest.raises(MalformedTranscriptError) as raised:
            parse_call(path)
        assert "file is empty" in str(raised.value), (
            f"{name} was not reported as empty: {raised.value}"
        )

    # And a file with content still gets the header message, so the new branch
    # has not swallowed the old one.
    wrong = tmp_path / "wrong.txt"
    wrong.write_text("not the header\n[call]\n", encoding="utf-8")
    with pytest.raises(MalformedTranscriptError) as raised:
        parse_call(wrong)
    assert "first line must be" in str(raised.value), (
        "a non-empty file with a wrong header was reported as empty"
    )


def test_no_speech_event_reaches_a_second_emptiness_check() -> None:
    """The removed branch, asserted gone rather than assumed gone.

    `_build_event` rejected an empty body for every kind, then checked again
    inside the CALLER/AGENT branch. The second check could not run. It read as
    defense in depth and was dead code, and a reader trusting it would believe
    speech was validated twice.

    This asserts the shape rather than the behavior, because the behavior is
    unobservable: both versions raise the same exception for the same input,
    which is exactly why the dead branch survived.
    """
    source = (REPO_ROOT / "src" / "harness" / "corpus" / "text_adapter.py").read_text(
        encoding="utf-8"
    )
    build = source[source.index("def _build_event") : source.index("def _find_token_line")]
    assert build.count("if not body:") == 1, (
        "the emptiness check appears more than once in _build_event; the second one cannot "
        "be reached, because the first raises for every kind"
    )
    assert 'raise ValueError(f"{pending.kind.value} event has an empty body")' in build, (
        "the surviving emptiness check no longer names the kind, so the one message that "
        "does the work has been changed rather than the dead one removed"
    )
