"""What a check may read, split by what the thing is evidence *of*.

**The system-level event log and retrieved policy clauses are ground truth;
agent speech is the subject under test.** A check that treats speech as
evidence has inverted the whole design: it would confirm the agent's claim
using the agent's claim, and every grounding check in the tier would pass on
the calls it exists to fail.

So a check does not receive "the call". It receives three populations, and they
are different types:

* `GroundTruth` -- the context record, the fact-population events, the clauses
  of every policy document retrieved in the call, and the call-record fields
  that are not disposition claims. **This is the only population a claim
  resolves against.** It is built from a `Call` by `build_context`, and there
  is no constructor taking free text, so a check cannot widen it.

* `Subject` -- agent speech, and the call record's four disposition labels.
  What is under test. The two are one population because they are two owners of
  the same kind of statement: the agent's spoken claim and the platform's
  claimed disposition are both assertions about what happened, and the findings
  document already splits them by `owner` for exactly that reason.

* `Stimulus` -- caller speech. Neither evidence nor subject. A caller can say
  anything, so the *content* of a caller turn never supports a claim about the
  world -- but the *occurrence* of one is a fact about the conversation, and
  several findings turn on it ("the caller raised an access requirement at
  event 4 and again at event 25, and was directed to a web form"). Keeping it
  third means a check that needs the trigger can have it without the trigger
  becoming evidence.

The event model's two citation populations are unchanged: `T` for speech, `F`
for facts. This refines `T` along the boundary the model already draws by kind,
for the one question checks ask that the model does not: which side of the
comparison is this on.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from harness.core.events import (
    Call,
    DisclosureEvent,
    Event,
    EventKind,
    PolicyEvent,
    SpeechEvent,
    StateEvent,
    SystemEvent,
    ToolCallEvent,
    ToolResultEvent,
)
from harness.corpus.policies import PolicyDocument

#: Call-record fields that are the platform's *claim* about the call rather
#: than a fact about it. The event model is explicit: these are the artifact
#: under test, and a harness that reconciled them on read would delete the
#: defect it exists to detect. They are in `Subject`, never in `GroundTruth`.
DISPOSITION_FIELDS: Final[tuple[str, ...]] = (
    "duration_ms",
    "disconnection_reason",
    "outcome",
    "outcome_reason",
)

#: Call-record fields that are facts about the call: when it started, which
#: agent version answered. Enumerated rather than derived as "everything else",
#: so a field added to the record joins one population by decision rather than
#: joining ground truth by default.
RECORD_FACT_FIELDS: Final[tuple[str, ...]] = (
    "call_id",
    "agent_id",
    "agent_version",
    "environment",
    "direction",
    "from_number",
    "to_number",
    "started_at",
    "answered_at",
    "ended_at",
)


class SourceGapError(Exception):
    """A call whose source declares it cannot carry something, offered to a check.

    Named rather than tolerated, and raised before any population is built, so
    the refusal reaches the deterministic tier, the judged tier, the report,
    agreement and coverage through the one seam they share.
    """

    def __init__(self, call_id: str, unavailable: tuple[str, ...]) -> None:
        super().__init__(
            f"{call_id}: its source declares it cannot carry {', '.join(unavailable)}, and no "
            "check reads that declaration yet, so a verdict here would rest on values "
            "nobody supplied. The call can be extracted; it cannot be evaluated (D203)."
        )
        self.call_id = call_id
        self.unavailable = unavailable


class FactSource(StrEnum):
    """Where a fact came from. Carried so a verdict's evidence can name it."""

    CONTEXT = "context"
    """The context record: what the agent could see before it spoke."""

    EVENT = "event"
    """A fact-population event: tool call, result, state, policy, disclosure,
    system."""

    POLICY_CLAUSE = "policy"
    """A clause of a document retrieved in this call -- including the clauses
    the agent did not apply, which is the point of retrieval returning a
    document."""

    CALL_RECORD = "call"
    """A call-record field that is not a disposition claim."""


@dataclass(frozen=True, slots=True)
class Fact:
    """One ground-truth statement, and where a reader finds it."""

    source: FactSource
    reference: str
    """Human-readable and stable: `context - account_zip`, `event 11`,
    `refund.v1 - 2.4`, `call - started_at`. This is what lands in a result's
    evidence list, so it is written to be looked up rather than parsed."""
    key: str
    """The variable, tool, clause or field name, where there is one."""
    text: str
    """The value this fact contributes, normalized to single spaces."""
    event_index: int | None = None
    """Stream position, for the ordering assertions. `None` for the context
    record and the policy documents, which precede the stream."""


@dataclass(frozen=True, slots=True)
class Claim:
    """One statement under test: an agent turn, or a disposition label."""

    reference: str
    key: str
    text: str
    event_index: int | None = None
    speech: SpeechEvent | None = None
    """The turn itself, where the claim is one. A check locating a claim needs
    the timing and the citation id; it must not need them to *support* a claim,
    which is what the type split is for."""


def _normalize(text: str) -> str:
    return " ".join(text.split())


def _event_fact(event: Event) -> Fact | None:
    """One fact-population event as a `Fact`. Speech returns `None`.

    Exhaustive by kind rather than by "not speech": under the negative form, an
    event kind added later would join ground truth without anyone deciding it
    should -- which is exactly how W17 put fabricated facts into a grounding
    blob, by classifying anything containing an `=` as a variable.
    """
    reference = f"event {event.index}"
    match event:
        case ToolCallEvent():
            return Fact(
                source=FactSource.EVENT,
                reference=reference,
                key=event.name,
                text=_normalize(f"{event.name}({event.arguments})"),
                event_index=event.index,
            )
        case ToolResultEvent():
            detail = f" :: {event.detail}" if event.detail else ""
            return Fact(
                source=FactSource.EVENT,
                reference=reference,
                key=event.tool_call_id,
                text=_normalize(
                    f"{event.status.value} successful={str(event.successful).lower()}{detail}"
                ),
                event_index=event.index,
            )
        case StateEvent():
            return Fact(
                source=FactSource.EVENT,
                reference=reference,
                key=event.name,
                text=_normalize(event.value),
                event_index=event.index,
            )
        case PolicyEvent():
            return Fact(
                source=FactSource.EVENT,
                reference=f"event {event.index} ({event.document} - {event.clause})",
                key=f"{event.document} {event.clause}",
                text=_normalize(event.text),
                event_index=event.index,
            )
        case DisclosureEvent():
            return Fact(
                source=FactSource.EVENT,
                reference=reference,
                key=event.name,
                text=_normalize(f"{event.state.value} {event.text or ''}"),
                event_index=event.index,
            )
        case SystemEvent():
            return Fact(
                source=FactSource.EVENT,
                reference=reference,
                key=event.name,
                text=_normalize(f"{event.name}({event.arguments})"),
                event_index=event.index,
            )
        case SpeechEvent():
            return None


@dataclass(frozen=True, slots=True)
class GroundTruth:
    """The only population a claim is resolved against.

    Frozen, and built only by `build_context` from a `Call`. There is no
    constructor taking arbitrary text and no method that adds one, so a check
    cannot widen the corpus it is grounding against -- which is the structural
    half of "agent speech is not evidence". The control half is a test that
    plants the supporting value in an agent turn and asserts the verdict does
    not move.
    """

    facts: tuple[Fact, ...]

    @property
    def corpus(self) -> str:
        """The concatenation a grounding check resolves a claim against.

        Tool-call details, variable values and retrieved policy clauses, joined
        with newlines. Speech is not in it, by construction rather than by
        filtering at this point: nothing that is not a `Fact` can reach here.
        """
        return "\n".join(fact.text for fact in self.facts)

    def of_source(self, source: FactSource) -> tuple[Fact, ...]:
        return tuple(fact for fact in self.facts if fact.source is source)

    def keyed(self, key: str) -> tuple[Fact, ...]:
        return tuple(fact for fact in self.facts if fact.key == key)

    def context_value(self, name: str) -> str | None:
        for fact in self.facts:
            if fact.source is FactSource.CONTEXT and fact.key == name:
                return fact.text
        return None


@dataclass(frozen=True, slots=True)
class Subject:
    """What is under test: the agent's speech and the platform's labels."""

    claims: tuple[Claim, ...]

    @property
    def agent_turns(self) -> tuple[Claim, ...]:
        return tuple(claim for claim in self.claims if claim.speech is not None)

    @property
    def dispositions(self) -> tuple[Claim, ...]:
        return tuple(claim for claim in self.claims if claim.speech is None)

    def disposition(self, field: str) -> str | None:
        for claim in self.dispositions:
            if claim.key == field:
                return claim.text
        return None


@dataclass(frozen=True, slots=True)
class Stimulus:
    """Caller speech. What was said to the system, and never evidence for it."""

    turns: tuple[Claim, ...]


@dataclass(frozen=True, slots=True)
class CheckContext:
    """Everything a deterministic check may read, for one call."""

    call_id: str
    ground_truth: GroundTruth
    subject: Subject
    stimulus: Stimulus
    events: tuple[Event, ...]
    """The ordered stream, for ordering assertions. Reading an `AGENT` body out
    of here to support a claim would defeat the split above -- the population
    types are what a check is meant to reach for, and this is here because
    "event 14 happened before event 15" is a question about order, not about
    evidence."""
    retrieved_policies: tuple[PolicyDocument, ...]
    """Documents `fetch_policy` returned in this call, whole. The clauses the
    agent did *not* apply are in here, which is what makes "a clause governing
    the question was in the returned document" assertable."""


@dataclass(frozen=True, slots=True)
class Invocation:
    """A tool call paired with its result, linked by `tool_call_id`.

    Invocation and result are separate events by design, and the chain between
    them is what makes "an action was taken before the confirmation it depends
    on existed" an ordering assertion rather than a judgment (D41). Pairing
    them is a property of the canonical stream, so it lives here rather than in
    whichever check needed it first.

    `result` is `None` for an invocation nothing answered. That is a real shape
    -- a call cut off mid-flight -- and it is distinct from a result that
    failed, which several findings turn on.
    """

    call: ToolCallEvent
    result: ToolResultEvent | None

    @property
    def name(self) -> str:
        return self.call.name

    @property
    def succeeded(self) -> bool:
        """The declared flag, never derived from the status.

        Platforms carry both, and a result whose `successful` disagrees with
        its status is a data-integrity defect the model must be able to
        represent -- so a check comparing the two needs them separate.
        """
        return self.result is not None and self.result.successful


def tool_invocations(events: Sequence[Event]) -> tuple[Invocation, ...]:
    """Every tool call in stream order, each with its result where one came.

    Matched on `tool_call_id` rather than on adjacency: a platform may
    interleave, and an adjacency rule would pair the wrong two events on the
    first log that does.
    """
    results = {event.tool_call_id: event for event in events if isinstance(event, ToolResultEvent)}
    return tuple(
        Invocation(call=event, result=results.get(event.tool_call_id))
        for event in events
        if isinstance(event, ToolCallEvent)
    )


def state_writes(events: Sequence[Event]) -> Mapping[str, tuple[int, ...]]:
    """Every index at which each state variable was written, in stream order.

    **Every** index, and that is the whole point of the helper. Three checks
    were built on `{event.name: event.index for event in events ...}`, a dict
    comprehension that silently keeps only the *last* write of each name -- so
    a variable set between two asks and set again afterwards read as never set
    between them, and a verification recorded before a gated write and refreshed
    after it read as no verification below the write. Both are false violations,
    on a variable whose history is exactly what the check is asking about.

    Pairing a name with its writes is a property of the canonical stream, like
    `tool_invocations`, so it lives here rather than in whichever check needed
    it first -- and a check that only wants membership asks `name in
    state_writes(...)`, which reads the same and cannot lose a write.

    **Ordering is left to the caller, because the checks do not agree on it.**
    `handoff_without_context` wants a write *after* an invocation, and
    `precondition_satisfied_by_assertion` wants one at or before it. A helper
    picking one would be wrong for the other, so it returns the history and each
    check states its own comparison.
    """
    writes: dict[str, list[int]] = {}
    for event in events:
        if isinstance(event, StateEvent):
            writes.setdefault(event.name, []).append(event.index)
    return {name: tuple(indices) for name, indices in writes.items()}


def _retrieved_documents(
    call: Call, policies: dict[str, PolicyDocument], policy_tool: str
) -> tuple[PolicyDocument, ...]:
    """Documents named by a successful retrieval in this call, in call order.

    `policy_tool` is passed in rather than hardcoded: it is a corpus entity
    name (class 6), and the rule that no such value is hardcoded in Python
    applies to the seam as much as to a check.
    """
    retrieved: list[PolicyDocument] = []
    for invocation in tool_invocations(call.events):
        event = invocation.call
        if event.name != policy_tool:
            continue
        # The docstring said "successful retrieval" and the code read only the
        # invocation. A `fetch_policy` that errored still put every clause of
        # that document into ground truth, so `governing_clause_not_applied`
        # would charge the agent with ignoring clauses of a document that never
        # arrived. All eight retrievals in the design set succeed, so neither a
        # test nor a corpus call reached the branch -- the held-out set is
        # exactly where a failed fetch would first appear.
        if invocation.result is None or not invocation.result.successful:
            continue
        for name, document in policies.items():
            if f'"{name}"' in event.arguments and document not in retrieved:
                retrieved.append(document)
    return tuple(retrieved)


def build_context(
    call: Call, policies: dict[str, PolicyDocument], *, policy_tool: str
) -> CheckContext:
    """Split one parsed call into the three populations a check may read.

    **A call that declares a gap is refused here, by name** (event model v3,
    D203). Nothing downstream of this seam reads `Call.unavailable` yet, and
    every consumer would turn the absence into a claim: the record facts below
    would render an absent `answered_at` as the text `None`, the lifecycle check
    would report a missing `call.ended` for a source that logs no lifecycle at
    all, and the judged prompt would state that no clause was retrieved where
    the truth is that nothing here can know. A verdict computed on a value
    nobody supplied is what section 5 of the event model forbids, so the
    refusal stands until the checks read the declaration.
    """
    if call.unavailable:
        raise SourceGapError(call.record.call_id, call.unavailable)
    facts: list[Fact] = []

    for (name, value), lines in zip(call.context, call.context_source_lines, strict=True):
        facts.append(
            Fact(
                source=FactSource.CONTEXT,
                reference=f"context - {name}" + (f" (line {lines[0]})" if lines else ""),
                key=name,
                text=_normalize(value),
            )
        )

    for field in RECORD_FACT_FIELDS:
        facts.append(
            Fact(
                source=FactSource.CALL_RECORD,
                reference=f"call - {field}",
                key=field,
                text=_normalize(str(getattr(call.record, field))),
            )
        )

    for event in call.events:
        fact = _event_fact(event)
        if fact is not None:
            facts.append(fact)

    retrieved = _retrieved_documents(call, policies, policy_tool)
    for document in retrieved:
        for clause_id, text in document.clauses:
            facts.append(
                Fact(
                    source=FactSource.POLICY_CLAUSE,
                    reference=f"{document.name} - {clause_id}",
                    key=f"{document.name} {clause_id}",
                    text=text,
                )
            )

    claims: list[Claim] = [
        Claim(
            reference=f"event {event.index}",
            key=event.kind.value,
            text=_normalize(event.body),
            event_index=event.index,
            speech=event,
        )
        for event in call.events
        if isinstance(event, SpeechEvent) and event.kind is EventKind.AGENT
    ]
    claims.extend(
        Claim(
            reference=f"call - {field}",
            key=field,
            text=_normalize(str(getattr(call.record, field))),
        )
        for field in DISPOSITION_FIELDS
    )

    stimulus = tuple(
        Claim(
            reference=f"event {event.index}",
            key=event.kind.value,
            text=_normalize(event.body),
            event_index=event.index,
            speech=event,
        )
        for event in call.events
        if isinstance(event, SpeechEvent) and event.kind is EventKind.CALLER
    )

    return CheckContext(
        call_id=call.record.call_id,
        ground_truth=GroundTruth(facts=tuple(facts)),
        subject=Subject(claims=tuple(claims)),
        stimulus=Stimulus(turns=stimulus),
        events=call.events,
        retrieved_policies=retrieved,
    )
