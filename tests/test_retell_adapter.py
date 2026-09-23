"""Adapter 2, held to the requirement D203 reworded.

The requirement is that for the same call the Retell adapter's event stream
differs from the text adapter's **only where a declared gap names what the
source cannot carry**. "Only" runs both ways, and the second way is the one a
convenient implementation breaks: an undeclared difference fails, and so does a
declared gap the adapter quietly filled -- because a filled gap is a default,
and a default is indistinguishable from a measurement.

**What keeps this from being a round trip proving itself.** The source documents
are generated from the transcripts (`tools/make_retell_documents.py`), so an
adapter and a generator that were wrong together would agree. Four things here
do not pass through that loop: the comparison is against the *text adapter's*
stream, which the generator does not write; every document is held to the
fields and types Retell's documentation states; and a changed word, a missing
success flag and an unmapped value are each driven through the adapter alone.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any, Final

import pytest
from tools.make_retell_documents import generate, stale

from harness.checks import build_registry
from harness.core.artifact import _event_to_dict
from harness.core.context import SourceGapError, build_context
from harness.core.engine import run_entry
from harness.core.events import (
    Call,
    Event,
    MalformedTranscriptError,
    SpeechEvent,
    ToolCallEvent,
    ToolResultEvent,
    UnknownTokenError,
)
from harness.core.gaps import Gap, UndeclaredGapError, apply, check_declared
from harness.core.result import Provenance, Status
from harness.core.rubric import load_rubric
from harness.corpus import retell_adapter, text_adapter
from harness.corpus.policies import load_policies
from harness.corpus.retell_adapter import (
    DOCUMENTED_ANALYSIS_FIELDS,
    DOCUMENTED_CALL_FIELDS,
    DOCUMENTED_ENTRY_FIELDS,
    DOCUMENTED_WORD_FIELDS,
    UNAVAILABLE,
)

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
TRANSCRIPTS: Final[Path] = REPO_ROOT / "corpus" / "transcripts"
DOCUMENTS: Final[Path] = REPO_ROOT / "corpus" / "retell"
POLICIES: Final[Path] = REPO_ROOT / "corpus" / "policies"
PROVENANCE: Final[Provenance] = Provenance(
    rubric_version="1", corpus_version="test", artifact_hash="0" * 64
)

#: Call-record fields the source carries in another representation rather than
#: not at all, with what each becomes. Not gaps: Retell reports a number as `+`
#: and digits and counts an agent's versions, and the adapter passes on what the
#: platform says rather than reformatting it toward this corpus.
_REPRESENTED_OTHERWISE: Final[tuple[str, ...]] = ("agent_version", "from_number", "to_number")


def _pairs() -> list[tuple[Call, Call]]:
    pairs = []
    for transcript in sorted(TRANSCRIPTS.glob("*.txt")):
        text = text_adapter.parse_call(transcript)
        document = DOCUMENTS / f"{text.record.call_id}.json"
        pairs.append((text, retell_adapter.parse_call(document)))
    return pairs


def _canonical(events: tuple[Event, ...]) -> bytes:
    """The artifact's own serialization of a stream, less each event's source
    reference, which the event model defines per source."""
    rows = []
    for event in events:
        row = _event_to_dict(event)
        del row["source_lines"]
        rows.append(row)
    return json.dumps(rows, sort_keys=True, ensure_ascii=False, indent=2).encode("utf-8")


def _differences(text: Call, retell: Call) -> list[str]:
    """Where the adapter's call is not the text call with the declared gaps applied."""
    expected = apply(text, UNAVAILABLE)
    problems: list[str] = []
    if _canonical(expected.events) != _canonical(retell.events):
        for index, (ours, theirs) in enumerate(
            zip(expected.events, retell.events, strict=False), start=1
        ):
            if _canonical((ours,)) != _canonical((theirs,)):
                problems.append(f"event {index} differs beyond the declared gaps")
                break
        else:
            problems.append(
                f"{len(expected.events)} events expected and {len(retell.events)} produced"
            )
    if expected.unavailable != retell.unavailable:
        problems.append(f"declares {retell.unavailable}, and the adapter's gaps are {UNAVAILABLE}")
    if expected.context != retell.context:
        problems.append("the context record differs")
    if expected.context_source_lines != retell.context_source_lines:
        problems.append("the context record's provenance differs")
    for field in dataclasses.fields(expected.record):
        if field.name in _REPRESENTED_OTHERWISE:
            continue
        if getattr(expected.record, field.name) != getattr(retell.record, field.name):
            problems.append(f"the call record's {field.name} differs")
    return problems


def test_every_design_calls_retell_stream_differs_from_the_text_stream_only_where_declared() -> (
    None
):
    """The phase's *Done when*, over every design call rather than over one."""
    pairs = _pairs()
    assert len(pairs) >= 16, f"only {len(pairs)} design calls were compared"
    carried = 0
    for text, retell in pairs:
        problems = _differences(text, retell)
        assert not problems, f"{text.record.call_id}: " + "; ".join(problems)
        carried += len(retell.events)

        # Speech is carried whole, so it is identical to the text stream itself and
        # not only to the gap-applied one: nothing removed is speech, so no `T`
        # citation id moves.
        spoken = [event for event in text.events if isinstance(event, SpeechEvent)]
        heard = [event for event in retell.events if isinstance(event, SpeechEvent)]
        assert [
            (e.kind, e.body, e.started_at_ms, e.ended_at_ms, e.citation_id) for e in spoken
        ] == [(e.kind, e.body, e.started_at_ms, e.ended_at_ms, e.citation_id) for e in heard], (
            f"{text.record.call_id}: a speech event is not byte-identical"
        )
        assert retell.record.from_number == "+" + "".join(
            character for character in text.record.from_number if character.isdigit()
        )
    assert carried > 300, f"only {carried} events were carried across the design set"


def test_the_stream_comparison_would_notice_a_gap_filled_or_a_difference_undeclared() -> None:
    """Both directions of *only*, each planted on a real pair."""
    text, retell = _pairs()[1]
    assert not _differences(text, retell)

    tool = next(event for event in retell.events if isinstance(event, ToolCallEvent))
    filled = tuple(
        dataclasses.replace(event, started_at_ms=0, ended_at_ms=0) if event is tool else event
        for event in retell.events
    )
    assert _differences(text, dataclasses.replace(retell, events=filled)), (
        "a tool event given a timing its source does not carry was not reported"
    )

    result = next(event for event in retell.events if isinstance(event, ToolResultEvent))
    dropped = tuple(
        dataclasses.replace(event, detail=None) if event is result else event
        for event in retell.events
    )
    assert _differences(text, dataclasses.replace(retell, events=dropped)), (
        "a tool result that lost its detail was not reported"
    )

    assert _differences(text, dataclasses.replace(retell, unavailable=())), (
        "a call declaring no gap was not reported"
    )


def _document(call_id: str = "CALL-02") -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads((DOCUMENTS / f"{call_id}.json").read_text("utf-8"))
    return loaded


def _written(tmp_path: Path, document: dict[str, Any]) -> Path:
    path = tmp_path / "call.json"
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8", newline="\n")
    return path


def _first(document: dict[str, Any], role: str) -> dict[str, Any]:
    entry: dict[str, Any] = next(
        entry for entry in document["transcript_with_tool_calls"] if entry["role"] == role
    )
    return entry


def test_the_adapter_would_notice_a_value_outside_its_declared_mapping(tmp_path: Path) -> None:
    """Section 5: an unmappable value aborts naming it, and is never read as `error`."""
    document = _document()
    _first(document, "tool_call_result")["content"] = json.dumps({"status": "sort_of_worked"})
    with pytest.raises(UnknownTokenError, match="sort_of_worked"):
        retell_adapter.parse_call(_written(tmp_path, document))

    document = _document()
    document["disconnection_reason"] = "dial_busy"
    with pytest.raises(UnknownTokenError, match="dial_busy"):
        retell_adapter.parse_call(_written(tmp_path, document))

    document = _document()
    document["transcript_with_tool_calls"].append({"role": "dtmf", "digit": "1"})
    with pytest.raises(UnknownTokenError, match="dtmf"):
        retell_adapter.parse_call(_written(tmp_path, document))


def test_the_adapter_would_notice_a_tool_result_with_no_success_flag(tmp_path: Path) -> None:
    """Refused, not supplied: Retell documents `successful` as optional, and a flag
    derived from the status could never disagree with it."""
    document = _document()
    del _first(document, "tool_call_result")["successful"]
    with pytest.raises(MalformedTranscriptError, match="successful"):
        retell_adapter.parse_call(_written(tmp_path, document))


def test_the_adapter_reads_the_document_it_is_given(tmp_path: Path) -> None:
    """The design's inversion: an adapter reading the transcript beside its source
    passes every comparison above. A word changed in the document, and nowhere
    else, has to reach the stream."""
    document = _document()
    entry = _first(document, "agent")
    entry["content"] = entry["content"] + " Marmalade."
    changed = retell_adapter.parse_call(_written(tmp_path, document))
    bodies = [event.body for event in changed.events if isinstance(event, SpeechEvent)]
    assert any(body.endswith("Marmalade.") for body in bodies)
    assert _differences(_pairs()[1][0], changed), "the changed word did not reach the comparison"


def _undocumented(document: dict[str, Any]) -> list[str]:
    """Fields a source document carries that Retell's documentation does not state,
    or carries at another type."""
    problems: list[str] = []

    def held(where: str, holder: dict[str, Any], table: Any) -> None:
        for key, value in holder.items():
            if key not in table:
                problems.append(f"{where}.{key} is not a documented field")
            elif not isinstance(value, table[key]) or (
                table[key] is int and isinstance(value, bool)
            ):
                problems.append(f"{where}.{key} is {type(value).__name__}")

    held("call", document, DOCUMENTED_CALL_FIELDS)
    held("call_analysis", document.get("call_analysis", {}), DOCUMENTED_ANALYSIS_FIELDS)
    for position, entry in enumerate(document.get("transcript_with_tool_calls", []), start=1):
        role = entry.get("role")
        if role not in DOCUMENTED_ENTRY_FIELDS:
            problems.append(f"entry {position} has the undocumented or unmapped role {role!r}")
            continue
        held(f"entry {position}", entry, DOCUMENTED_ENTRY_FIELDS[role])
        for word in entry.get("words", []):
            held(f"entry {position} word", word, DOCUMENTED_WORD_FIELDS)
    for name in ("retell_llm_dynamic_variables", "collected_dynamic_variables"):
        for key, value in document.get(name, {}).items():
            if not isinstance(value, str):
                problems.append(f"{name}.{key} is not a string, and the map is string to string")
    return problems


def test_every_committed_retell_document_uses_only_documented_fields() -> None:
    documents = sorted(DOCUMENTS.glob("*.json"))
    assert len(documents) >= 16, f"only {len(documents)} source documents are committed"
    for path in documents:
        problems = _undocumented(json.loads(path.read_text("utf-8")))
        assert not problems, f"{path.name}: " + "; ".join(problems)


def test_the_documented_field_check_would_notice_a_field_nobody_documented() -> None:
    """An answered-at stamp is exactly what a convenient document would grow."""
    document = _document()
    document["answered_timestamp"] = document["start_timestamp"] + 2900
    assert any("answered_timestamp" in problem for problem in _undocumented(document))

    document = _document()
    _first(document, "tool_call_invocation")["time_sec"] = 31.864
    assert any("time_sec" in problem for problem in _undocumented(document))

    document = _document()
    document["agent_version"] = "2027.03.1"
    assert any("agent_version" in problem for problem in _undocumented(document))


def test_the_committed_retell_documents_match_their_regeneration() -> None:
    assert stale(generate()) == []


def test_the_regeneration_check_would_notice_a_stale_document(tmp_path: Path) -> None:
    documents = generate()
    for name, text in documents.items():
        (tmp_path / name).write_text(text, encoding="utf-8", newline="\n")
    assert stale(documents, tmp_path) == []

    name = sorted(documents)[0]
    (tmp_path / name).write_text(
        documents[name].replace("phone_call", "web_call"), encoding="utf-8", newline="\n"
    )
    (tmp_path / "CALL-99.json").write_text("{}\n", encoding="utf-8", newline="\n")
    problems = stale(documents, tmp_path)
    assert any(name in problem for problem in problems)
    assert any("CALL-99.json" in problem for problem in problems)


def test_build_context_would_notice_a_call_that_declares_a_gap() -> None:
    """Nothing downstream reads `Call.unavailable` yet, so the seam every tier
    shares refuses the call rather than letting an absence become a verdict."""
    text, retell = _pairs()[0]
    policies = load_policies(POLICIES)
    build_context(text, policies, policy_tool="fetch_policy")
    with pytest.raises(SourceGapError, match=Gap.LIFECYCLE_EVENTS.value):
        build_context(retell, policies, policy_tool="fetch_policy")


def test_the_gap_check_would_notice_a_stream_and_a_declaration_that_disagree() -> None:
    text, retell = _pairs()[0]
    check_declared(retell)
    check_declared(text)

    undeclared = dataclasses.replace(
        retell,
        unavailable=tuple(name for name in retell.unavailable if name != Gap.TOOL_TIMING.value),
    )
    with pytest.raises(UndeclaredGapError, match="carry no timing"):
        check_declared(undeclared)

    with pytest.raises(UndeclaredGapError, match="is declared and event"):
        check_declared(dataclasses.replace(text, unavailable=(Gap.DISCLOSURE_EVENTS.value,)))

    with pytest.raises(UndeclaredGapError, match="nothing defines"):
        check_declared(dataclasses.replace(text, unavailable=("events.MOOD",)))


@pytest.mark.parametrize(
    "entry_id", ["A-silence-exceeds-threshold", "A-duration-does-not-reconcile"]
)
def test_a_timing_check_would_notice_an_absent_time_read_as_a_number(entry_id: str) -> None:
    """The two checks that read timing as a quantity say what is missing rather
    than measure a gap, or a last moment, that the source never recorded."""
    text = text_adapter.parse_call(TRANSCRIPTS / "CALL-05.txt")
    tool = next(event for event in text.events if isinstance(event, ToolCallEvent))
    untimed = tuple(
        dataclasses.replace(event, started_at_ms=None, ended_at_ms=None) if event is tool else event
        for event in text.events
    )
    context = build_context(
        dataclasses.replace(text, events=untimed),
        load_policies(POLICIES),
        policy_tool="fetch_policy",
    )
    registry = build_registry()
    rubric = load_rubric(REPO_ROOT / "rubric.yaml", registry.keys())
    result = run_entry(rubric.by_id(entry_id), context, PROVENANCE, registry)
    assert result.status is Status.UNEVALUABLE, result
    assert result.missing_ground_truth == "event timing"


def test_a_retell_artifact_names_its_adapter_and_its_gaps_and_a_text_one_names_neither() -> None:
    """The text artifact's bytes, and so the hash every committed log is stamped
    with, do not move for a field only another adapter fills."""
    from harness.core.artifact import build_payload

    text, retell = _pairs()[0]
    ours = build_payload((text,), "test", REPO_ROOT)
    assert "adapter" not in ours
    assert "unavailable" not in ours["calls"][0]

    theirs = build_payload((retell,), "test", REPO_ROOT, adapter="retell")
    assert theirs["adapter"] == "retell"
    assert theirs["calls"][0]["unavailable"] == sorted(gap.value for gap in UNAVAILABLE)
