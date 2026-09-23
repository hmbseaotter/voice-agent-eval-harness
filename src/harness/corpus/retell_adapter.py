"""Adapter 2: a Retell call object -> the canonical event stream.

**Written against Retell's public documentation as it stated the schema on
2026-09-20**, and against nothing else: `GET /v2/get-call/{call_id}`, response
schema `V2PhoneCallResponse`, from the OpenAPI document the Get Call page embeds
(`x-retell-spec-revision: 2026-09-14-b240eb0`). The tables below are that
schema's field names and types. Where this module needed something the
documentation does not state, it does not guess: the value is declared
unavailable, or the document is refused by name.

This is the adapter `specs/event-model.md` exists for. The claim under test is
that an engineer can point the harness at *their vendor's* logs, and an adapter
over a format of this project's own would have proven nothing (D203) -- nor
would one written against a vendor's schema as somebody imagined it.

**What the documented call object cannot carry, and so is declared rather than
invented** (`UNAVAILABLE`):

* `transcript_with_tool_calls` has nine roles and none is a disclosure, an
  applied policy clause or the call's lifecycle. Knowledge-base retrieval
  appears only as a URL to a file whose format is undocumented.
* `collected_dynamic_variables` is a call-level string map: it says what was
  set and not when, so it is no positioned `STATE` event.
* `tool_call_invocation` and `tool_call_result` entries carry **no timing
  field**. Only utterances do, through `words[].start` and `words[].end`.
* The call has no answered-at stamp and no environment. `agent_tag` is a
  user-defined label on an agent's version, not a property of the call.

**What a deployment supplies, and the platform only carries.** A tool result's
`content` is documented as "a string, a stringified json, etc." -- it is
whatever the deployment's own tool returned, so its status words are the
deployment's and `tool_statuses` maps them. `call_analysis.custom_analysis_data`
is the documented home of a deployment's own post-call fields, which is where
this corpus's deployment records `outcome` and `outcome_reason`. Both mappings
are arguments rather than constants for that reason.

**Roles this adapter does not map.** `node_transition`, `dtmf`, `sms`,
`injected` and `transfer_target` are documented, the design corpus uses none,
and section 4 of the event model maps three of them to `SYSTEM` without saying
how an untimed one is positioned. A document carrying one aborts naming the
role, which is section 5's rule for a value a mapping does not cover.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

from harness.core.events import (
    Call,
    CallRecord,
    Direction,
    DisconnectionReason,
    Event,
    EventKind,
    MalformedTranscriptError,
    Outcome,
    SpeechEvent,
    ToolCallEvent,
    ToolResultEvent,
    ToolStatus,
    UnknownTokenError,
    citation_population,
)
from harness.core.gaps import Gap, check_declared
from harness.corpus.text_adapter import check_tool_pairing

#: The revision marker of the OpenAPI document this was written against, and
#: the day its pages were read. A reader comparing this module with Retell's
#: current documentation starts from these two facts.
RETELL_SPEC_REVISION: Final[str] = "2026-09-14-b240eb0"
DOCUMENTATION_READ_ON: Final[str] = "2026-09-20"

#: What Retell's documented call object cannot carry. Declared on every call
#: this adapter produces, and what `harness.core.gaps.apply` is given to say
#: what the text adapter's stream becomes under the same gaps.
UNAVAILABLE: Final[frozenset[Gap]] = frozenset(
    {
        Gap.DISCLOSURE_EVENTS,
        Gap.POLICY_EVENTS,
        Gap.STATE_EVENTS,
        Gap.LIFECYCLE_EVENTS,
        Gap.TOOL_TIMING,
        Gap.RECORD_ANSWERED_AT,
        Gap.RECORD_ENVIRONMENT,
        Gap.CONTEXT_PROVENANCE,
    }
)

#: Retell's `DisconnectionReason` onto the closed vocabulary, for the values
#: with an equivalent. **Partial on purpose**: the rest of Retell's enum --
#: dial failures, concurrency and payment refusals, websocket errors -- has no
#: canonical member, and a value outside this table aborts naming it. Bucketing
#: them into `system_error` would convert an unknown into a known-bad and hide
#: the gap, which is what section 5 forbids.
DISCONNECTION_REASONS: Final[Mapping[str, DisconnectionReason]] = {
    "user_hangup": DisconnectionReason.CALLER_HANGUP,
    "agent_hangup": DisconnectionReason.AGENT_HANGUP,
    "call_transfer": DisconnectionReason.TRANSFERRED,
    "voicemail_reached": DisconnectionReason.VOICEMAIL_REACHED,
    "inactivity": DisconnectionReason.INACTIVITY_TIMEOUT,
    "max_duration_reached": DisconnectionReason.MAX_DURATION_REACHED,
    "error_asr": DisconnectionReason.ASR_ERROR,
}

#: The status words this corpus's deployment returns from its tools, onto the
#: closed vocabulary. The deployment's, not Retell's: the platform carries a
#: tool's response as an opaque string.
VERSO_TOOL_STATUSES: Final[Mapping[str, ToolStatus]] = {
    "ok": ToolStatus.COMPLETED,
    "found": ToolStatus.RETRIEVED,
    "not_eligible": ToolStatus.REFUSED_INELIGIBLE,
    "precondition_failed": ToolStatus.REFUSED_PRECONDITION,
    "service_unavailable": ToolStatus.UNAVAILABLE,
    "timed_out": ToolStatus.TIMEOUT,
    "bad_request": ToolStatus.MALFORMED,
    "failed": ToolStatus.ERROR,
}

_SPEECH_ROLES: Final[Mapping[str, EventKind]] = {
    "agent": EventKind.AGENT,
    "user": EventKind.CALLER,
}

#: Top-level fields of `V2PhoneCallResponse`, with the JSON type the
#: documentation states for each. Used to hold the committed source documents to
#: the documented shape; **not** used to refuse a real log carrying more, since
#: no schema there sets `additionalProperties: false`.
DOCUMENTED_CALL_FIELDS: Final[Mapping[str, type | tuple[type, ...]]] = {
    "call_type": str,
    "from_number": str,
    "to_number": str,
    "direction": str,
    "telephony_identifier": dict,
    "call_id": str,
    "agent_id": str,
    "agent_name": str,
    "agent_version": int,
    "agent_tag": (str, type(None)),
    "call_status": str,
    "metadata": dict,
    "retell_llm_dynamic_variables": dict,
    "collected_dynamic_variables": dict,
    "custom_sip_headers": dict,
    "data_storage_setting": (str, type(None)),
    "opt_in_signed_url": bool,
    "start_timestamp": int,
    "end_timestamp": int,
    "transfer_end_timestamp": int,
    "duration_ms": int,
    "transcript": str,
    "transcript_object": list,
    "transcript_with_tool_calls": list,
    "scrubbed_transcript_with_tool_calls": list,
    "recording_url": str,
    "recording_multi_channel_url": str,
    "scrubbed_recording_url": str,
    "scrubbed_recording_multi_channel_url": str,
    "public_log_url": str,
    "knowledge_base_retrieved_contents_url": str,
    "latency": dict,
    "disconnection_reason": str,
    "transfer_destination": (str, type(None)),
    "call_analysis": dict,
    "call_cost": dict,
    "llm_token_usage": dict,
}

#: The fields of each entry of `transcript_with_tool_calls` this adapter maps,
#: by role, with the documented type. `words[]` items are `word`, `start`,
#: `end`; `start` and `end` are numbers, "in second", relative audio time.
DOCUMENTED_ENTRY_FIELDS: Final[Mapping[str, Mapping[str, type | tuple[type, ...]]]] = {
    "agent": {"role": str, "content": str, "words": list},
    "user": {"role": str, "content": str, "words": list},
    "tool_call_invocation": {
        "role": str,
        "tool_call_id": str,
        "name": str,
        "arguments": str,
        "thought_signature": str,
    },
    "tool_call_result": {"role": str, "tool_call_id": str, "content": str, "successful": bool},
}
DOCUMENTED_WORD_FIELDS: Final[Mapping[str, type | tuple[type, ...]]] = {
    "word": str,
    "start": (int, float),
    "end": (int, float),
}
DOCUMENTED_ANALYSIS_FIELDS: Final[Mapping[str, type | tuple[type, ...]]] = {
    "call_summary": str,
    "in_voicemail": bool,
    "user_sentiment": str,
    "call_successful": bool,
    "custom_analysis_data": dict,
}


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Refuse a JSON object naming one key twice.

    `json` keeps the last and says nothing, which is how a findings file and a
    rubric here have each collapsed a duplicated key silently. A call object
    whose second `successful` overrode its first would parse cleanly.
    """
    seen: dict[str, Any] = {}
    for key, value in pairs:
        if key in seen:
            raise ValueError(f"the key {key!r} appears twice in one object")
        seen[key] = value
    return seen


def _load(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(
            path.read_text(encoding="utf-8-sig"), object_pairs_hook=_no_duplicate_keys
        )
    except ValueError as exc:
        raise MalformedTranscriptError(f"{path}: not a readable JSON call object: {exc}") from exc
    if not isinstance(document, dict):
        raise MalformedTranscriptError(f"{path}: a call object is a JSON object")
    return document


def _require[T](path: Path, holder: Mapping[str, Any], key: str, kind: type[T], where: str) -> T:
    """A field the canonical model needs, at the type the documentation states.

    Refused by name when absent or mistyped, never defaulted. `bool` is excluded
    where an integer is asked for, because Python counts `True` as one.
    """
    if key not in holder:
        raise MalformedTranscriptError(f"{path}: {where} carries no {key!r}")
    value = holder[key]
    if not isinstance(value, kind) or (kind is int and isinstance(value, bool)):
        raise MalformedTranscriptError(
            f"{path}: {where} {key!r} is {type(value).__name__}, and the documentation "
            f"states {kind.__name__}"
        )
    return value


def _iso(epoch_ms: int) -> str:
    """Milliseconds since the epoch as the model's stamp: UTC, millisecond
    precision, `Z` suffix."""
    moment = datetime.fromtimestamp(epoch_ms / 1000, tz=UTC)
    return moment.strftime("%Y-%m-%dT%H:%M:%S.") + f"{epoch_ms % 1000:03d}Z"


def _milliseconds(seconds: float) -> int:
    """A documented offset "in second" as whole milliseconds. Rounded, because
    7.488 seconds is 7488.000000000001 milliseconds in binary floating point."""
    return round(seconds * 1000)


def _render_arguments(path: Path, where: str, raw: str) -> str:
    """Retell's stringified JSON arguments as the model's one-line form.

    `name="value"` pairs in the object's own order. The model captures a tool
    call's arguments raw and decomposes nothing, so this renders and does not
    interpret; a value that is not a string is rendered as the JSON it is.
    """
    try:
        arguments = json.loads(raw, object_pairs_hook=_no_duplicate_keys)
    except ValueError as exc:
        raise MalformedTranscriptError(
            f"{path}: {where} arguments are documented as a stringified JSON object, and "
            f"these do not parse: {exc}"
        ) from exc
    if not isinstance(arguments, dict):
        raise MalformedTranscriptError(f"{path}: {where} arguments are not a JSON object")
    return ", ".join(
        f'{name}="{value}"' if isinstance(value, str) else f"{name}={json.dumps(value)}"
        for name, value in arguments.items()
    )


def _speech(
    path: Path, entry: Mapping[str, Any], position: int, index: int, citation_id: str
) -> SpeechEvent:
    where = f"transcript_with_tool_calls[{position}]"
    content = _require(path, entry, "content", str, where)
    words = _require(path, entry, "words", list, where)
    if not content.strip():
        raise MalformedTranscriptError(f"{path}: {where} is an utterance with no words in it")
    if not words:
        # The utterance's only timing is its words', so an utterance with none
        # has no start and no end -- and the gap this adapter declares covers
        # tool events, not speech. Refused rather than stamped with a guess.
        raise MalformedTranscriptError(
            f"{path}: {where} carries no words, and an utterance's timing is its words'"
        )
    first, last = words[0], words[-1]
    for word, which in ((first, "first"), (last, "last")):
        if not isinstance(word, dict):
            raise MalformedTranscriptError(f"{path}: {where} {which} word is not an object")
    started = first.get("start")
    ended = last.get("end")
    if (
        not isinstance(started, (int, float))
        or not isinstance(ended, (int, float))
        or isinstance(started, bool)
        or isinstance(ended, bool)
    ):
        raise MalformedTranscriptError(
            f"{path}: {where} words carry no numeric start and end, so the utterance has no timing"
        )
    started_ms, ended_ms = _milliseconds(started), _milliseconds(ended)
    if ended_ms < started_ms:
        raise MalformedTranscriptError(f"{path}: {where} ends before it starts")
    return SpeechEvent(
        index=index,
        started_at_ms=started_ms,
        ended_at_ms=ended_ms,
        kind=_SPEECH_ROLES[str(entry["role"])],
        body=content.strip(),
        citation_id=citation_id,
        source_lines=(position,),
    )


def _tool_call(
    path: Path, entry: Mapping[str, Any], position: int, index: int, citation_id: str
) -> ToolCallEvent:
    where = f"transcript_with_tool_calls[{position}]"
    tool_call_id = _require(path, entry, "tool_call_id", str, where)
    name = _require(path, entry, "name", str, where)
    arguments = _render_arguments(path, where, _require(path, entry, "arguments", str, where))
    return ToolCallEvent(
        index=index,
        started_at_ms=None,
        ended_at_ms=None,
        kind=EventKind.TOOL_CALL,
        body=f"{tool_call_id} {name}({arguments})",
        citation_id=citation_id,
        source_lines=(position,),
        tool_call_id=tool_call_id,
        name=name,
        arguments=arguments,
    )


def _tool_result(
    path: Path,
    entry: Mapping[str, Any],
    position: int,
    index: int,
    citation_id: str,
    tool_statuses: Mapping[str, ToolStatus],
) -> ToolResultEvent:
    where = f"transcript_with_tool_calls[{position}]"
    tool_call_id = _require(path, entry, "tool_call_id", str, where)
    # **Refused, not defaulted.** The documentation marks `successful` optional
    # and says of its absence that the outcome "wasn't recorded, which doesn't
    # mean it failed". The model requires the confirmation flag, and deriving it
    # from the status would make a result whose flag disagrees with its status
    # -- a defect the model exists to represent -- impossible to observe.
    successful = _require(path, entry, "successful", bool, where)
    raw = _require(path, entry, "content", str, where)
    try:
        payload = json.loads(raw, object_pairs_hook=_no_duplicate_keys)
    except ValueError as exc:
        raise MalformedTranscriptError(
            f"{path}: {where} content is not the JSON this deployment's tools return: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise MalformedTranscriptError(f"{path}: {where} content is not a JSON object")
    token = _require(path, payload, "status", str, f"{where} content")
    if token not in tool_statuses:
        raise UnknownTokenError(
            str(path), position, "tool status", token, ", ".join(sorted(tool_statuses))
        )
    status = tool_statuses[token]
    detail_raw = payload.get("detail")
    if detail_raw is not None and not isinstance(detail_raw, str):
        raise MalformedTranscriptError(f"{path}: {where} content detail is not a string")
    detail = detail_raw.strip() or None if detail_raw else None
    body = f"{tool_call_id} -> {status.value} successful={str(successful).lower()}"
    if detail:
        body += f" :: {detail}"
    return ToolResultEvent(
        index=index,
        started_at_ms=None,
        ended_at_ms=None,
        kind=EventKind.TOOL_RESULT,
        body=body,
        citation_id=citation_id,
        source_lines=(position,),
        tool_call_id=tool_call_id,
        status=status,
        successful=successful,
        detail=detail,
    )


def _record(path: Path, document: Mapping[str, Any]) -> CallRecord:
    call_type = _require(path, document, "call_type", str, "the call")
    if call_type != "phone_call":
        raise MalformedTranscriptError(
            f"{path}: call_type is {call_type!r}; the model's endpoints and direction are a "
            "phone call's, and the documentation gives a web call neither"
        )
    direction = _require(path, document, "direction", str, "the call")
    if direction not in [member.value for member in Direction]:
        raise MalformedTranscriptError(f"{path}: direction {direction!r} is not one Retell states")
    reason = _require(path, document, "disconnection_reason", str, "the call")
    if reason not in DISCONNECTION_REASONS:
        raise UnknownTokenError(
            str(path), 0, "disconnection reason", reason, ", ".join(sorted(DISCONNECTION_REASONS))
        )
    analysis = _require(path, document, "call_analysis", dict, "the call")
    custom = _require(path, analysis, "custom_analysis_data", dict, "call_analysis")
    outcome = _require(path, custom, "outcome", str, "call_analysis.custom_analysis_data")
    if outcome not in [member.value for member in Outcome]:
        raise UnknownTokenError(
            str(path), 0, "outcome", outcome, ", ".join(member.value for member in Outcome)
        )
    duration = _require(path, document, "duration_ms", int, "the call")
    if duration < 0:
        raise MalformedTranscriptError(f"{path}: duration_ms is {duration}")
    return CallRecord(
        call_id=_require(path, document, "call_id", str, "the call"),
        agent_id=_require(path, document, "agent_id", str, "the call"),
        # Retell counts an agent's published versions; the release label a
        # deployment gives one has no documented field.
        agent_version=str(_require(path, document, "agent_version", int, "the call")),
        environment=None,
        direction=Direction(direction),
        from_number=_require(path, document, "from_number", str, "the call"),
        to_number=_require(path, document, "to_number", str, "the call"),
        started_at=_iso(_require(path, document, "start_timestamp", int, "the call")),
        answered_at=None,
        ended_at=_iso(_require(path, document, "end_timestamp", int, "the call")),
        duration_ms=duration,
        disconnection_reason=DISCONNECTION_REASONS[reason],
        outcome=Outcome(outcome),
        outcome_reason=_require(
            path, custom, "outcome_reason", str, "call_analysis.custom_analysis_data"
        ),
    )


def _context(path: Path, document: Mapping[str, Any]) -> tuple[tuple[str, str], ...]:
    variables = document.get("retell_llm_dynamic_variables", {})
    if not isinstance(variables, dict):
        raise MalformedTranscriptError(f"{path}: retell_llm_dynamic_variables is not an object")
    pairs: list[tuple[str, str]] = []
    for name, value in variables.items():
        if not isinstance(value, str):
            raise MalformedTranscriptError(
                f"{path}: retell_llm_dynamic_variables {name!r} is not a string, and the "
                "documentation states a string-to-string map"
            )
        pairs.append((name, value.strip()))
    return tuple(pairs)


def parse_call(
    path: Path, *, tool_statuses: Mapping[str, ToolStatus] = VERSO_TOOL_STATUSES
) -> Call:
    """Parse one Retell call object into the canonical form.

    Ordering is the array's own: `transcript_with_tool_calls` is documented as
    the transcript "weaved with tool call invocation and results", and that
    order is all the documentation gives a tool entry, so it is what the index
    follows.
    """
    document = _load(path)
    record = _record(path, document)
    context = _context(path, document)
    entries = _require(path, document, "transcript_with_tool_calls", list, "the call")

    events: list[Event] = []
    counters = {"T": 0, "F": 0}
    for position, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise MalformedTranscriptError(
                f"{path}: transcript_with_tool_calls[{position}] is not an object"
            )
        role = entry.get("role")
        if isinstance(role, str) and role in _SPEECH_ROLES:
            kind = _SPEECH_ROLES[role]
        elif role == "tool_call_invocation":
            kind = EventKind.TOOL_CALL
        elif role == "tool_call_result":
            kind = EventKind.TOOL_RESULT
        else:
            raise UnknownTokenError(
                str(path),
                position,
                "transcript role",
                str(role),
                ", ".join([*_SPEECH_ROLES, "tool_call_invocation", "tool_call_result"]),
            )
        population = citation_population(kind)
        counters[population] += 1
        citation_id = f"{population}{counters[population]}"
        index = len(events) + 1
        if kind is EventKind.TOOL_CALL:
            events.append(_tool_call(path, entry, position, index, citation_id))
        elif kind is EventKind.TOOL_RESULT:
            events.append(_tool_result(path, entry, position, index, citation_id, tool_statuses))
        else:
            events.append(_speech(path, entry, position, index, citation_id))

    frozen = tuple(events)
    check_tool_pairing(path, frozen, ())
    call = Call(
        source_path=str(path),
        record=record,
        context=context,
        context_source_lines=tuple(() for _ in context),
        events=frozen,
        unparsed=(),
        unavailable=tuple(sorted(gap.value for gap in UNAVAILABLE)),
    )
    check_declared(call)
    return call
