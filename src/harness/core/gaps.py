"""What a source cannot carry, by name, and what each name does to a stream.

`specs/event-model.md` section 5 says an adapter owes honest gaps: anything its
source does not carry is unavailable, never defaulted. This module is where
"unavailable" stops being a word and becomes a closed vocabulary with a
meaning (event model v3, D203).

**Each gap is defined by what it removes from a complete stream.** `apply` takes
a call that carries everything -- which the text serialization does -- and
returns the call a source with those gaps could at most supply: the event kinds
it has no entry for removed, the survivors renumbered and their fact citations
with them, the timing it does not record absent. That is what makes the second
adapter's requirement checkable rather than hopeful. *Identical where carried*
is an equality between `apply(text_call, gaps)` and what the adapter produced,
so an undeclared difference fails it, and so does a declared gap the adapter
quietly filled.

**What is deliberately not here.** A source's *representation* of a field it
does carry -- a phone number in another format, a version counted rather than
labeled -- is not a gap, and `apply` leaves the call record's carried fields
alone. The requirement is about the event stream; the record's carried fields
are compared by the adapter's own tests, field by field.
"""

from __future__ import annotations

from dataclasses import replace
from enum import StrEnum
from typing import Final

from harness.core.events import (
    Call,
    Event,
    EventKind,
    SystemEvent,
    citation_population,
)


class Gap(StrEnum):
    """What a source may declare it cannot carry. Closed: a name nothing defines
    would be a gap nothing can apply, and a call declaring it would be refused
    for a reason no reader could look up."""

    DISCLOSURE_EVENTS = "events.DISCLOSURE"
    """No entry for a mandated statement being delivered."""

    POLICY_EVENTS = "events.POLICY"
    """No entry for the clause the agent applied."""

    STATE_EVENTS = "events.STATE"
    """No positioned, timed entry for a variable set during the call. A call-level
    map of collected variables is not one: it says what was set and not when."""

    LIFECYCLE_EVENTS = "events.SYSTEM.lifecycle"
    """No entry for the call being answered or ending. Narrower than the whole
    `SYSTEM` kind on purpose: a source may log routing and keypad events and
    still log no lifecycle."""

    TOOL_TIMING = "events.TOOL.timing"
    """No start or end offset on a tool call or its result."""

    RECORD_ANSWERED_AT = "record.answered_at"
    RECORD_ENVIRONMENT = "record.environment"

    CONTEXT_PROVENANCE = "context.source_lines"
    """The context record's pairs carry no source lines, because the source has
    no lines. Section 2 of the event model allows exactly this, said rather than
    left empty."""


#: `SYSTEM` event names that are lifecycle rather than routing or guardrail.
LIFECYCLE_EVENT_NAMES: Final[frozenset[str]] = frozenset({"call.answered", "call.ended"})

_KIND_GAPS: Final[tuple[tuple[Gap, EventKind], ...]] = (
    (Gap.DISCLOSURE_EVENTS, EventKind.DISCLOSURE),
    (Gap.POLICY_EVENTS, EventKind.POLICY),
    (Gap.STATE_EVENTS, EventKind.STATE),
)

_TOOL_KINDS: Final[tuple[EventKind, ...]] = (EventKind.TOOL_CALL, EventKind.TOOL_RESULT)


class UndeclaredGapError(Exception):
    """A call whose stream and whose `unavailable` disagree about a gap."""


def parse_gaps(names: tuple[str, ...]) -> frozenset[Gap]:
    """The declared names as `Gap` members, refusing one nothing defines."""
    known = {gap.value for gap in Gap}
    strangers = sorted(name for name in names if name not in known)
    if strangers:
        raise UndeclaredGapError(
            f"gap name(s) nothing defines: {', '.join(strangers)}; the closed vocabulary is "
            f"{', '.join(sorted(known))}"
        )
    return frozenset(Gap(name) for name in names)


def _removed(event: Event, gaps: frozenset[Gap]) -> bool:
    for gap, kind in _KIND_GAPS:
        if gap in gaps and event.kind is kind:
            return True
    return (
        Gap.LIFECYCLE_EVENTS in gaps
        and isinstance(event, SystemEvent)
        and event.name in LIFECYCLE_EVENT_NAMES
    )


def apply(call: Call, gaps: frozenset[Gap]) -> Call:
    """The call a source with these gaps could at most supply.

    Events of a kind the source has no entry for are removed; the survivors are
    renumbered from 1 with no holes, and their citation ids renumbered within
    each population, because an index and a citation id are positions in the
    stream the consumer sees, not in one it never received. `source_lines` is
    left as it is: a source reference is each adapter's own by definition
    (event model section 3), and a caller comparing two adapters' streams sets
    it aside by name rather than having it silently rewritten here.
    """
    counters = {"T": 0, "F": 0}
    events: list[Event] = []
    for event in call.events:
        if _removed(event, gaps):
            continue
        population = citation_population(event.kind)
        counters[population] += 1
        index = len(events) + 1
        citation_id = f"{population}{counters[population]}"
        if Gap.TOOL_TIMING in gaps and event.kind in _TOOL_KINDS:
            events.append(
                replace(
                    event,
                    index=index,
                    citation_id=citation_id,
                    started_at_ms=None,
                    ended_at_ms=None,
                )
            )
        else:
            events.append(replace(event, index=index, citation_id=citation_id))

    record = call.record
    if Gap.RECORD_ANSWERED_AT in gaps:
        record = replace(record, answered_at=None)
    if Gap.RECORD_ENVIRONMENT in gaps:
        record = replace(record, environment=None)
    context_source_lines = call.context_source_lines
    if Gap.CONTEXT_PROVENANCE in gaps:
        context_source_lines = tuple(() for _ in call.context)
    return replace(
        call,
        record=record,
        context_source_lines=context_source_lines,
        events=tuple(events),
        unavailable=tuple(sorted(gap.value for gap in gaps)),
    )


def check_declared(call: Call) -> None:
    """Refuse a call whose stream shows a gap it does not declare, or the reverse.

    Both directions. An absent value with no declaration is a default waiting
    to be read as a measurement; a declaration beside a value that is present
    is a gap the adapter filled, which is the same defect arriving from the
    other side.
    """
    declared = parse_gaps(call.unavailable)
    problems: list[str] = []

    untimed = [
        event.index
        for event in call.events
        if event.started_at_ms is None or event.ended_at_ms is None
    ]
    untimed_tools = [
        event.index
        for event in call.events
        if event.kind in _TOOL_KINDS and (event.started_at_ms is None or event.ended_at_ms is None)
    ]
    if sorted(untimed) != sorted(untimed_tools):
        strays = sorted(set(untimed) - set(untimed_tools))
        problems.append(f"event(s) {strays} carry no timing, and no gap covers their kind")
    if untimed_tools and Gap.TOOL_TIMING not in declared:
        problems.append(
            f"tool event(s) {untimed_tools} carry no timing and {Gap.TOOL_TIMING.value} is "
            "not declared"
        )
    if Gap.TOOL_TIMING in declared:
        timed = [
            event.index
            for event in call.events
            if event.kind in _TOOL_KINDS
            and event.started_at_ms is not None
            and event.ended_at_ms is not None
        ]
        if timed:
            problems.append(
                f"{Gap.TOOL_TIMING.value} is declared and tool event(s) {timed} carry timing"
            )

    for gap in sorted(declared):
        present = [event.index for event in call.events if _removed(event, frozenset({gap}))]
        if present:
            problems.append(f"{gap.value} is declared and event(s) {present} are of that kind")

    for gap, value, name in (
        (Gap.RECORD_ANSWERED_AT, call.record.answered_at, "answered_at"),
        (Gap.RECORD_ENVIRONMENT, call.record.environment, "environment"),
    ):
        if value is None and gap not in declared:
            problems.append(f"the record carries no {name} and {gap.value} is not declared")
        if value is not None and gap in declared:
            problems.append(f"{gap.value} is declared and the record carries {name}")

    if problems:
        raise UndeclaredGapError(
            f"{call.source_path}: the stream and its declared gaps disagree:\n  "
            + "\n  ".join(problems)
        )
