"""The versioned frozen extraction artifact, and its content hash.

Every result the harness later produces is stamped with the rubric version, the
corpus version and *this artifact's content hash*, so any report can be
recomputed from the inputs it names. That only works if the hash is a function
of the corpus and nothing else.

Two consequences drive the design here:

* **Paths are stored relative, with forward slashes.** An absolute path would
  make the hash machine-dependent, so two people extracting the same corpus
  would get different hashes and every downstream "recompute this and check"
  claim would be unfalsifiable. It is also W23 -- hardcoded absolute Windows
  paths composed with backslash f-strings, in an implementation nothing ran on
  a fresh clone without editing source.

* **Serialization is canonical.** Sorted keys, `\\n` line endings, UTF-8, one
  trailing newline. Byte-identical output across runs is an acceptance
  criterion from P4 onward, and an artifact that serializes differently on two
  machines makes that criterion unreachable no matter how deterministic the
  code above it is.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Final, assert_never

from harness.core.events import (
    TRANSCRIPT_FORMAT_VERSION,
    Call,
    DisclosureEvent,
    Event,
    PolicyEvent,
    SpeechEvent,
    StateEvent,
    SystemEvent,
    ToolCallEvent,
    ToolResultEvent,
)

#: Version of the artifact's own schema, independent of the transcript format's.
#: They change for different reasons: the transcript format changes when the
#: corpus's source grammar changes, this changes when the extracted shape does.
ARTIFACT_VERSION: Final[str] = "1"

_HASH_FIELD: Final[str] = "content_hash"


def _event_to_dict(event: Event) -> dict[str, Any]:
    """One event as plain data, with its kind-specific fields.

    Explicit narrowing rather than a generic `asdict`, so adding an event kind
    without deciding how it serializes is a type error here rather than a
    silently missing field in the artifact.
    """
    payload: dict[str, Any] = {
        "index": event.index,
        "started_at_ms": event.started_at_ms,
        "ended_at_ms": event.ended_at_ms,
        "kind": event.kind.value,
        "body": event.body,
        "citation_id": event.citation_id,
        "source_lines": list(event.source_lines),
    }
    match event:
        case SpeechEvent():
            pass
        case ToolCallEvent():
            payload |= {
                "tool_call_id": event.tool_call_id,
                "name": event.name,
                "arguments": event.arguments,
            }
        case ToolResultEvent():
            payload |= {
                "tool_call_id": event.tool_call_id,
                "status": event.status.value,
                "successful": event.successful,
                "detail": event.detail,
            }
        case StateEvent():
            payload |= {"name": event.name, "value": event.value}
        case PolicyEvent():
            payload |= {
                "document": event.document,
                "clause": event.clause,
                "text": event.text,
            }
        case DisclosureEvent():
            payload |= {
                "name": event.name,
                "state": event.state.value,
                "text": event.text,
            }
        case SystemEvent():
            payload |= {"name": event.name, "arguments": event.arguments}
        case _:
            assert_never(event)
    return payload


def _relative_path(source_path: str, repo_root: Path) -> str:
    """Repo-relative, forward-slashed, so the hash is machine-independent."""
    try:
        relative = Path(source_path).resolve().relative_to(repo_root.resolve())
    except ValueError:
        # Outside the repository: keep the name only rather than embedding an
        # absolute path that would poison the hash for everyone else.
        return Path(source_path).name
    return relative.as_posix()


def build_payload(
    calls: tuple[Call, ...], corpus_version: str, repo_root: Path, *, adapter: str = "text"
) -> dict[str, Any]:
    """The artifact's content, without its hash.

    `adapter` is written only when it is not the text adapter (D203), for the
    reason `unavailable` is: an artifact extracted from the corpus's own
    serialization keeps the bytes, and so the hash, it has always had.
    """
    payload: dict[str, Any] = {
        "artifact_version": ARTIFACT_VERSION,
        "transcript_format_version": TRANSCRIPT_FORMAT_VERSION,
        "corpus_version": corpus_version,
        "calls": [_call_to_dict(call, repo_root) for call in calls],
    }
    if adapter != "text":
        payload["adapter"] = adapter
    return payload


def _call_to_dict(call: Call, repo_root: Path) -> dict[str, Any]:
    """One call as plain data.

    **`unavailable` is written only when the call declares a gap** (event model
    v3, D203), so an artifact extracted from the text serialization, which
    carries everything, is byte for byte what it was before the field existed --
    and its content hash, which every committed result and run log is stamped
    with, does not move.
    """
    payload: dict[str, Any] = {
        "source_path": _relative_path(call.source_path, repo_root),
        "call": asdict(call.record),
        "context": [list(pair) for pair in call.context],
        "events": [_event_to_dict(event) for event in call.events],
        "unparsed": [asdict(line) for line in call.unparsed],
    }
    if call.unavailable:
        payload["unavailable"] = list(call.unavailable)
    return payload


def canonical_bytes(payload: dict[str, Any]) -> bytes:
    """The one serialization the hash is taken over."""
    text = json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2)
    return (text + "\n").encode("utf-8")


def content_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def write_artifact(path: Path, payload: dict[str, Any]) -> str:
    """Write the artifact with its hash embedded. Returns the hash."""
    digest = content_hash(payload)
    document = dict(payload)
    document[_HASH_FIELD] = digest
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(document, sort_keys=True, ensure_ascii=False, indent=2) + "\n")
    return digest


def verify_artifact(path: Path) -> tuple[bool, str, str]:
    """Recompute the hash from the file's own content.

    Returns `(matches, recorded, recomputed)`. A reader can run this without
    the corpus, which is the point: the claim "this report was computed from
    that corpus" is checkable by recomputation rather than by trust.
    """
    with path.open(encoding="utf-8") as handle:
        document: dict[str, Any] = json.load(handle)
    recorded = str(document.pop(_HASH_FIELD, ""))
    recomputed = content_hash(document)
    return recorded == recomputed, recorded, recomputed
