#!/usr/bin/env python3
"""The design calls as Retell call objects, generated from the design transcripts.

    uv run python -m tools.make_retell_documents            # write corpus/retell/
    uv run python -m tools.make_retell_documents --check    # CI: are they stale?

The second adapter needs a source document per design call in the platform's
shape (D203). These are those documents: the same sixteen calls, serialized as
`GET /v2/get-call` would return them, carrying what Retell's documented call
object can carry and nothing else. **Invented sample data, like the corpus it is
generated from** -- no vendor log and no customer data is read here or written.

WHY A GENERATOR AND NOT SIXTEEN HAND-TYPED FILES
------------------------------------------------
Two hundred utterances with word-level timings and a hundred tool entries are a
large surface for typing errors, and the byte comparison the adapter is held to
would report each one as an adapter defect. `--check` keeps the documents from
drifting away from the transcripts, as the findings view's does.

WHAT KEEPS THE ROUND TRIP FROM PROVING ONLY ITSELF
--------------------------------------------------
A generator and an adapter written together can agree with each other and be
wrong together. What breaks that is in `tests/test_retell_adapter.py`, not here:
the adapter's stream is compared with the *text adapter's*, which this module
does not produce; every document is held to a table of the fields and types
Retell's documentation states; and a document with a word changed, a success
flag removed or an unknown status is driven through the adapter by itself.

WHAT IS INVENTED BEYOND THE TRANSCRIPT
--------------------------------------
Per-word timings. The text serialization stamps an utterance's start and end;
Retell stamps each word. Words are spread evenly across the utterance, which
the documentation's own caveat covers -- word timestamps are "not guaranteed to
be accurate" -- and the first word's start and the last word's end are the
transcript's own stamps exactly, which is all the adapter reads.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from harness.core.events import (
    Call,
    Event,
    SpeechEvent,
    StateEvent,
    ToolCallEvent,
    ToolResultEvent,
    timing,
)
from harness.corpus.retell_adapter import (
    DISCONNECTION_REASONS,
    VERSO_TOOL_STATUSES,
)
from harness.corpus.text_adapter import parse_call
from harness.heldout import HELDOUT_SET_FILE, any_held_out, declared_held_out_calls

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
TRANSCRIPTS: Final[Path] = REPO_ROOT / "corpus" / "transcripts"
DOCUMENTS: Final[Path] = REPO_ROOT / "corpus" / "retell"

_ARGUMENT: Final[re.Pattern[str]] = re.compile(r'([A-Za-z_][A-Za-z0-9_]*)="([^"]*)"')
_SPEECH_ROLES: Final[Mapping[str, str]] = {"AGENT": "agent", "CALLER": "user"}


class CannotRepresentError(Exception):
    """A transcript this generator cannot turn into a document without guessing."""


def _inverse[K, V](mapping: Mapping[K, V]) -> dict[V, K]:
    inverse: dict[V, K] = {}
    for key, value in mapping.items():
        if value in inverse:
            raise CannotRepresentError(f"{value!r} is the image of two source values")
        inverse[value] = key
    return inverse


def _epoch_ms(stamp: str) -> int:
    moment = datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=UTC)
    return int(moment.timestamp()) * 1000 + int(stamp[-4:-1])


def _e164(number: str) -> str:
    """A number as Retell's own examples print one: `+` and digits."""
    return "+" + "".join(character for character in number if character.isdigit())


def _words(event: SpeechEvent) -> list[dict[str, Any]]:
    """The utterance's words, spread evenly between its own two stamps.

    The first start and the last end are the transcript's stamps exactly, in
    seconds; everything between is invented, and nothing reads it.
    """
    started, ended = timing(event)
    tokens = event.body.split()
    count = len(tokens)
    bounds = [round(started + (ended - started) * step / count) for step in range(count + 1)]
    return [
        {"word": token, "start": bounds[step] / 1000, "end": bounds[step + 1] / 1000}
        for step, token in enumerate(tokens)
    ]


def _arguments(call_id: str, event: ToolCallEvent) -> str:
    """The raw argument string as the stringified JSON object Retell documents.

    Refuses a string it cannot rebuild exactly, because the adapter renders the
    object back and a lossy parse here would surface there as a false defect.
    """
    pairs = _ARGUMENT.findall(event.arguments)
    rebuilt = ", ".join(f'{name}="{value}"' for name, value in pairs)
    if rebuilt != event.arguments:
        raise CannotRepresentError(
            f"{call_id} event {event.index}: arguments {event.arguments!r} are not "
            'name="value" pairs this generator can rebuild'
        )
    if len({name for name, _ in pairs}) != len(pairs):
        raise CannotRepresentError(f"{call_id} event {event.index}: an argument is named twice")
    return json.dumps(dict(pairs), ensure_ascii=False)


def _entry(call_id: str, event: Event, statuses: Mapping[Any, str]) -> dict[str, Any] | None:
    """One carried event as a `transcript_with_tool_calls` entry, or `None` for a
    kind the documented array has no entry for."""
    if isinstance(event, SpeechEvent):
        return {
            "role": _SPEECH_ROLES[event.kind.value],
            "content": event.body,
            "words": _words(event),
        }
    if isinstance(event, ToolCallEvent):
        return {
            "role": "tool_call_invocation",
            "tool_call_id": event.tool_call_id,
            "name": event.name,
            "arguments": _arguments(call_id, event),
        }
    if isinstance(event, ToolResultEvent):
        payload: dict[str, Any] = {"status": statuses[event.status]}
        if event.detail is not None:
            payload["detail"] = event.detail
        return {
            "role": "tool_call_result",
            "tool_call_id": event.tool_call_id,
            "content": json.dumps(payload, ensure_ascii=False),
            "successful": event.successful,
        }
    return None


def document_for(call: Call, agent_versions: Mapping[str, int]) -> dict[str, Any]:
    """One design call as a `V2PhoneCallResponse`."""
    record = call.record
    statuses = _inverse(VERSO_TOOL_STATUSES)
    reasons = _inverse(DISCONNECTION_REASONS)
    if record.disconnection_reason not in reasons:
        raise CannotRepresentError(
            f"{record.call_id}: no Retell disconnection reason maps to "
            f"{record.disconnection_reason.value!r}"
        )
    entries = [
        entry
        for event in call.events
        if (entry := _entry(record.call_id, event, statuses)) is not None
    ]
    collected = {event.name: event.value for event in call.events if isinstance(event, StateEvent)}
    return {
        "call_type": "phone_call",
        "call_id": record.call_id,
        "agent_id": record.agent_id,
        "agent_version": agent_versions[record.agent_version],
        "call_status": "ended",
        "direction": record.direction.value,
        "from_number": _e164(record.from_number),
        "to_number": _e164(record.to_number),
        "start_timestamp": _epoch_ms(record.started_at),
        "end_timestamp": _epoch_ms(record.ended_at),
        "duration_ms": record.duration_ms,
        "disconnection_reason": reasons[record.disconnection_reason],
        "retell_llm_dynamic_variables": dict(call.context),
        "collected_dynamic_variables": collected,
        "transcript_with_tool_calls": entries,
        "call_analysis": {
            "call_successful": record.outcome.value == "resolved",
            "custom_analysis_data": {
                "outcome": record.outcome.value,
                "outcome_reason": record.outcome_reason,
            },
        },
    }


def render(document: Mapping[str, Any]) -> str:
    return json.dumps(document, ensure_ascii=False, indent=2) + "\n"


def generate(transcripts: Path = TRANSCRIPTS) -> dict[str, str]:
    """Every design call's document, keyed by file name."""
    paths = sorted(transcripts.glob("*.txt"))
    if not paths:
        raise FileNotFoundError(f"no transcripts found in {transcripts}")
    calls = [parse_call(path) for path in paths]
    held_out = declared_held_out_calls(REPO_ROOT / HELDOUT_SET_FILE)
    if any_held_out((call.record.call_id for call in calls), held_out):
        raise CannotRepresentError(
            "a call HELDOUT_SET declares is among these transcripts, and these documents are "
            "written inside this checkout"
        )
    if any(len(dict(call.context)) != len(call.context) for call in calls):
        # A JSON object keeps one value per key, so a repeated name would be lost
        # on the way in rather than reported.
        raise CannotRepresentError("a context variable is named twice in one call")
    labels = sorted({call.record.agent_version for call in calls})
    agent_versions = {label: number for number, label in enumerate(labels, start=1)}
    return {
        f"{call.record.call_id}.json": render(document_for(call, agent_versions)) for call in calls
    }


def stale(documents: Mapping[str, str], directory: Path = DOCUMENTS) -> list[str]:
    """What differs between the committed documents and their regeneration."""
    problems: list[str] = []
    for name, text in sorted(documents.items()):
        path = directory / name
        if not path.is_file():
            problems.append(f"{name} is not committed")
            continue
        with path.open(encoding="utf-8", newline="") as handle:
            committed = handle.read().replace("\r\n", "\n")
        if committed != text:
            problems.append(f"{name} differs from its regeneration")
    committed_names = (
        {path.name for path in directory.glob("*.json")} if directory.is_dir() else set()
    )
    for name in sorted(committed_names - set(documents)):
        problems.append(f"{name} is committed and no design transcript produces it")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools.make_retell_documents", description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail when the documents are stale")
    args = parser.parse_args(argv)
    try:
        documents = generate()
    except (CannotRepresentError, OSError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    if args.check:
        problems = stale(documents)
        for problem in problems:
            print(problem, file=sys.stderr)
        if problems:
            print("corpus/retell/ is stale; regenerate it without --check", file=sys.stderr)
            return 1
        print(f"corpus/retell/: {len(documents)} documents match their regeneration")
        return 0
    DOCUMENTS.mkdir(parents=True, exist_ok=True)
    for name, text in sorted(documents.items()):
        with (DOCUMENTS / name).open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    print(f"wrote {len(documents)} documents to corpus/retell/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
