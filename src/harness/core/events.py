"""Contract types for the canonical event model.

`specs/event-model.md` is the prose; this is the same thing in code. Nothing
above the adapter line may depend on which platform a call came from, so these
types are the whole of what a check, a judge prompt or a report ever sees.

Every type is a frozen dataclass and every module constant is `typing.Final`.
The point is not ceremony: an event stream a check can mutate is one where a
check can quietly "fix" the defect it was supposed to report.

The event types share a base carrying what every event has and subclass it with
the fields each kind's grammar defines, so uniform iteration needs no narrowing
while kind-specific access needs it -- and `mypy --strict` rejects a consumer
that reads a tool status off a speech event rather than discovering it at
runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

#: Format token on line 1 of every conforming transcript.
TRANSCRIPT_FORMAT_VERSION: Final[str] = "2"
FORMAT_HEADER: Final[str] = (
    f"#format: voice-agent-eval-harness/transcript v{TRANSCRIPT_FORMAT_VERSION}"
)


class EventKind(StrEnum):
    """The eight event kinds. Closed, matched case-sensitively.

    There is no untyped catch-all on purpose. The implementation this project
    diffs against classified any system note containing an `=` as a variable
    (W17), so fabricated "facts" flowed into the grounding blob and into the
    judge's established-facts block. Every line declaring its kind in a
    dedicated field means nothing is inferred from punctuation, and there is no
    unconstrained kind for a fabricated fact to occupy.
    """

    CALLER = "CALLER"
    AGENT = "AGENT"
    TOOL_CALL = "TOOL_CALL"
    TOOL_RESULT = "TOOL_RESULT"
    STATE = "STATE"
    POLICY = "POLICY"
    DISCLOSURE = "DISCLOSURE"
    SYSTEM = "SYSTEM"


class ToolStatus(StrEnum):
    """Outcome of a tool invocation.

    **Eligibility is the content of a read, not the status of a write.** A
    write's result says whether the write happened; whether it was *permitted*
    is something a prior read reported. v1 collapsed those, which made "the
    agent proceeded against state that said it could not" inexpressible --
    there was no prior state to proceed against.

    The three refusal-and-failure distinctions are load-bearing. The causal
    pattern behind fabricated completion is an agent with no error taxonomy:
    nothing separating a fixable precondition from hard ineligibility from
    environmental unavailability. Collapsing them would make "the agent treated
    an unavailable service as an ineligible request" unstateable.
    """

    COMPLETED = "completed"
    RETRIEVED = "retrieved"
    REFUSED_INELIGIBLE = "refused_ineligible"
    REFUSED_PRECONDITION = "refused_precondition"
    UNAVAILABLE = "unavailable"
    TIMEOUT = "timeout"
    MALFORMED = "malformed"
    ERROR = "error"

    @property
    def implies_success(self) -> bool:
        """What `successful` *should* be for this status.

        Compared against the declared flag rather than replacing it. Platforms
        carry both, and a result whose `successful` disagrees with its status is
        a real data-integrity defect the model has to be able to represent --
        so this is a check, not a derivation.
        """
        return self in (ToolStatus.COMPLETED, ToolStatus.RETRIEVED)


class DisconnectionReason(StrEnum):
    """Why the call ended. Generalized from the vocabularies platforms publish.

    Replaces v1's `terminated_by: caller | agent | system`, which could not
    distinguish a caller hanging up from an inactivity timeout -- two events
    that mean opposite things about the call.
    """

    CALLER_HANGUP = "caller_hangup"
    AGENT_HANGUP = "agent_hangup"
    TRANSFERRED = "transferred"
    VOICEMAIL_REACHED = "voicemail_reached"
    INACTIVITY_TIMEOUT = "inactivity_timeout"
    MAX_DURATION_REACHED = "max_duration_reached"
    NETWORK_ERROR = "network_error"
    ASR_ERROR = "asr_error"
    SYSTEM_ERROR = "system_error"


class Outcome(StrEnum):
    """The platform's own disposition for the call.

    Closed for the same reason `disconnection_reason` is: **validating the
    token is not reconciling the claim.** Both fields are the artifact under
    test, and a harness that recomputed either would delete the defect it
    exists to detect -- but an unknown token is not a disputed disposition, it
    is a value nobody can interpret, and comparing against it silently compares
    against nothing.

    This was open until an audit noticed the asymmetry: `disconnection_reason`
    aborted extraction on an unrecognized token while `outcome` accepted any
    string at all, and the entity register declared reason codes without
    declaring outcomes.
    """

    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    TRANSFERRED = "transferred"
    ABANDONED = "abandoned"


class DisclosureState(StrEnum):
    """Whether a mandated statement was delivered, and what the caller did."""

    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    DECLINED = "declined"
    SKIPPED = "skipped"


class Environment(StrEnum):
    PRODUCTION = "production"
    STAGING = "staging"
    TEST = "test"


class Direction(StrEnum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


#: Speech: the subject under test and its untrusted input. Cited as `[T<n>]`.
SPEECH_KINDS: Final[tuple[EventKind, ...]] = (EventKind.CALLER, EventKind.AGENT)

#: Established facts: what the system did. Cited as `[F<n>]`.
FACT_KINDS: Final[tuple[EventKind, ...]] = (
    EventKind.TOOL_CALL,
    EventKind.TOOL_RESULT,
    EventKind.STATE,
    EventKind.POLICY,
    EventKind.DISCLOSURE,
    EventKind.SYSTEM,
)

#: `[call]` keys every conforming transcript must carry, in file order.
REQUIRED_CALL_KEYS: Final[tuple[str, ...]] = (
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
    "duration_ms",
    "disconnection_reason",
    "outcome",
    "outcome_reason",
)


def citation_population(kind: EventKind) -> str:
    """`"T"` for speech, `"F"` for established facts.

    Two prefixes rather than one shared syntax is the structural fix for W1,
    where the citation validator built its citable set from conversation turns
    only while the prompt rendered established facts in the identical
    `[line N]` syntax. The populations were disjoint, so every established-fact
    line was uncitable by construction and the "hallucination detector" never
    caught a hallucination.

    Read from both tuples rather than deriving `"F"` as *not speech*. Under the
    derivation `FACT_KINDS` was declared `Final` and referenced nowhere, so a
    ninth kind would have been classified `"F"` whether or not anyone added it
    to the tuple -- and `FACT_KINDS` would have been quietly wrong while looking
    authoritative. A constant nothing reads is a comment with a type annotation.
    """
    if kind in SPEECH_KINDS:
        return "T"
    if kind in FACT_KINDS:
        return "F"
    raise AssertionError(  # pragma: no cover - the partition test forbids this
        f"{kind.value!r} is in neither SPEECH_KINDS nor FACT_KINDS"
    )


@dataclass(frozen=True, slots=True)
class BaseEvent:
    """What every event carries, whatever its kind."""

    index: int
    """1-based position in the stream. Strictly sequential, no gaps.
    **Ordering checks use this, never timestamps.**"""

    started_at_ms: int | None
    ended_at_ms: int | None
    """Offsets from the call's `started_at`. A single stamp cannot express how
    long an utterance took, which is what v1 got wrong, so an adapter whose
    source carries both supplies both.

    **`None` is "the source does not carry this", and never zero** (event model
    v3, D203). Retell's documented call object gives a tool call and its result
    no timing field at all, and a defaulted offset is indistinguishable from a
    measured one -- the silence check would read an invented gap and the
    duration check an invented end. A call carrying one names the gap in
    `Call.unavailable`, and the two are held together by
    `harness.core.gaps.check_declared`."""

    kind: EventKind

    body: str
    """The reassembled body. For a wrapped event this is every fragment joined
    with single spaces -- the invariant the extraction tier exists to protect
    and the one W19's conformance test could not see."""

    citation_id: str
    source_lines: tuple[int, ...]
    """Every 1-based source line this event was assembled from."""

    @property
    def duration_ms(self) -> int | None:
        """How long the event took, or `None` where the source carries no timing."""
        if self.started_at_ms is None or self.ended_at_ms is None:
            return None
        return self.ended_at_ms - self.started_at_ms


@dataclass(frozen=True, slots=True)
class SpeechEvent(BaseEvent):
    """`CALLER` or `AGENT`. Free text, never interpreted."""


@dataclass(frozen=True, slots=True)
class ToolCallEvent(BaseEvent):
    """`<id> <name>(<args>)` -- the invocation only.

    Its result is a separate event linked by `tool_call_id`, which is how every
    platform surveyed models it and what makes the dependency chain expressible:
    read establishes eligibility, write is attempted, result confirms it
    succeeded, and only then may anything depending on it happen.
    """

    tool_call_id: str
    name: str
    arguments: str
    """Captured raw. Phase 1 does not decompose arguments."""


@dataclass(frozen=True, slots=True)
class ToolResultEvent(BaseEvent):
    """`<id> -> <status> successful=<bool> [:: detail]`."""

    tool_call_id: str
    status: ToolStatus
    successful: bool
    """Declared, not derived. Compare against `status.implies_success`: a
    disagreement is a data-integrity defect, not a parse error."""
    detail: str | None


@dataclass(frozen=True, slots=True)
class StateEvent(BaseEvent):
    """`<name> := <value>` -- a variable set *during* the call.

    Distinct from the context record, which is what the agent was given before
    it spoke. The distinction carries weight: a context variable that should
    have changed and did not is a platform defect, and that is only sayable
    because the two are separate.
    """

    name: str
    value: str


@dataclass(frozen=True, slots=True)
class PolicyEvent(BaseEvent):
    """A *logged retrieval* of a policy clause.

    The log line is what makes two failures separately detectable: misstating a
    clause that was retrieved, and asserting a rule with no retrieval anywhere
    in the call. Without it the second is invisible, because a confident
    sentence and a grounded sentence look identical in speech.
    """

    document: str
    clause: str
    text: str


@dataclass(frozen=True, slots=True)
class DisclosureEvent(BaseEvent):
    """A mandated statement: recording notice, consent, required wording."""

    name: str
    state: DisclosureState
    text: str | None


@dataclass(frozen=True, slots=True)
class SystemEvent(BaseEvent):
    """Lifecycle, routing and guardrail events."""

    name: str
    arguments: str


def timing(event: BaseEvent) -> tuple[int, int]:
    """An event's start and end offsets, for a reader whose source carries both.

    The text serialization always does, so a test over the design transcripts
    states that by calling this rather than by narrowing `int | None` at every
    site. A source that carries no timing for an event declares the gap
    (`harness.core.gaps`), and reading its timing through here fails by name
    instead of computing on `None`.
    """
    if event.started_at_ms is None or event.ended_at_ms is None:
        raise ValueError(
            f"event {event.index} ({event.kind.value}) carries no timing: its source "
            "does not record when it started or ended"
        )
    return event.started_at_ms, event.ended_at_ms


Event = (
    SpeechEvent
    | ToolCallEvent
    | ToolResultEvent
    | StateEvent
    | PolicyEvent
    | DisclosureEvent
    | SystemEvent
)


@dataclass(frozen=True, slots=True)
class CallRecord:
    """The `[call]` block, recorded verbatim.

    `duration_ms`, `disconnection_reason`, `outcome` and `outcome_reason` are the
    artifact under test, not ground truth -- they are what the system claimed.
    A harness that reconciled them on read would delete the defect it exists to
    detect.
    """

    call_id: str
    agent_id: str
    agent_version: str
    environment: Environment | None
    """`None` where the source carries no environment (event model v3, D203):
    Retell's call object has none, and its nearest field is a user-defined tag
    on the agent's version rather than a property of the call."""
    direction: Direction
    from_number: str
    to_number: str
    started_at: str
    answered_at: str | None
    """`None` where the source carries no answered-at stamp, as Retell's does
    not. Never copied from `started_at`: ring-to-answer is a real interval and a
    copied stamp would report it as zero."""
    ended_at: str
    duration_ms: int
    disconnection_reason: DisconnectionReason
    outcome: Outcome
    outcome_reason: str


@dataclass(frozen=True, slots=True)
class UnparsedLine:
    """A source line the adapter could not parse.

    Recorded rather than raised, and reported rather than discarded. The
    reference implementation's extraction test crashed on a malformed file
    instead of reporting the violation it had already recorded (W19), and its
    metadata handling dropped unexpected lines silently with no counter (W18).
    """

    line_number: int
    raw: str
    reason: str


@dataclass(frozen=True, slots=True)
class Call:
    """One parsed call, in canonical form."""

    source_path: str
    record: CallRecord
    context: tuple[tuple[str, str], ...]
    """What the agent could see before the conversation began. Ordered as
    written, so a reader sees what the platform sent in the order it sent it."""
    context_source_lines: tuple[tuple[int, ...], ...]
    """Which source lines each context pair came from, aligned with `context`
    by position.

    Every event carries `source_lines`; the context record did not, which made
    the `[context]` block the one part of a transcript whose provenance this
    model could not express. That is not only an inconsistency: two tests
    asserting the block's wrapping rule had to open the transcript file and
    re-read it, because the parsed object could not say how many lines a value
    spanned -- and a conformance test that re-derives what the parser already
    knew is the W19 mistake with extra steps."""
    events: tuple[Event, ...]
    unparsed: tuple[UnparsedLine, ...]
    unavailable: tuple[str, ...] = ()
    """What this call's source cannot carry, by name, as `harness.core.gaps.Gap`
    values (event model v3, D203).

    Empty for the text serialization, which carries everything, and then not
    written to the artifact at all, so a text-sourced artifact is byte for byte
    what it was before the field existed. **A gap is recorded here rather than
    defaulted into the stream**: section 5 of the event model says why -- a
    defaulted value is indistinguishable from a real one, and a check keyed to
    it would be asserting on a value nobody supplied. Until the checks read this
    field the engine refuses a call that declares one."""


class TranscriptError(Exception):
    """Base for every abort the adapter raises rather than records."""


class UnknownTokenError(TranscriptError):
    """A token outside one of the closed vocabularies.

    An abort rather than an unparsed-line count, because the distinction
    matters: a line the grammar cannot read is a counting problem, but a token
    outside a closed vocabulary means the corpus and the harness disagree about
    the vocabulary itself, and every downstream check keyed to it is then
    reasoning about a token nothing defines (W15).
    """

    def __init__(
        self, path: str, line_number: int, vocabulary: str, token: str, allowed: str
    ) -> None:
        super().__init__(
            f"{path}:{line_number}: unknown {vocabulary} {token!r}; "
            f"the closed vocabulary is {allowed}"
        )
        self.path = path
        self.line_number = line_number
        self.vocabulary = vocabulary
        self.token = token


class MalformedTranscriptError(TranscriptError):
    """A file-level defect: wrong header, missing section, bad call record.

    Distinct from an unparsed *line*: a file whose call record is wrong has no
    usable call to attach a per-line counter to.
    """
