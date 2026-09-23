"""Running the judged tier: N repetitions, one informed retry, five statuses.

The deterministic engine and this one are deliberately separate. They share the
`Result` contract and nothing else: a judged call has a transport, a run log, a
retry budget and a repetition count, and folding those into `run_entry` would
put four judged concerns into the function `--tier assert` runs.

**Classification order is the design, not an implementation detail.** Three
outcomes present identically as "no valid result" and this project's whole
thesis is that they must not be reported as one:

1. `stop_reason == "refusal"` -> `status: refused`, **retry budget untouched**.
   The model declined; retrying identical input against a classifier that just
   declined it spends money to reach the same place (D23). This is an expected
   event here rather than an exotic one, because D7 requires the corpus to
   carry prompt-injection attempts in caller speech.
2. `stop_reason == "max_tokens"` -> `status: errored`, carrying the stop
   reason. Truncated structured output is unparseable, so without this branch a
   truncation would present as a schema failure, burn the informed retry on
   identical input, and resolve to `errored` anyway -- the same conflation as
   (1) by a different route (D24).
3. anything else -> parse, then validate citations. An invalid citation buys
   exactly one informed retry; exhaustion is `errored`.

Each of the three is reached **before** the next, which is why the checks are
ordered rather than collected. A parse attempted before the stop reason is read
turns (2) into (3).

**N repetitions, and one Result each.** The requirement is N repetitions with
one run-log entry per repetition, and reporting a *distribution* over them is
P4. So this returns the repetitions individually rather than aggregating them:
inventing an aggregation here would be authoring P4's answer inside P3, and the
obvious candidates -- first, modal, worst -- are three different claims about
what N means.

**A judged run continues past a failure and stops at a ceiling.** `errored` and
`refused` are per-result and the loop goes on; a call ceiling and an exhausted
transport are per-run and it stops -- having already written every entry it
obtained, because `RecordingTransport` writes as it goes rather than at the end.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from harness.core.context import CheckContext
from harness.core.registry import ResultBuilder
from harness.core.result import Provenance, Result
from harness.core.rubric import (
    SYNTHESIS_CHECK,
    CheckTier,
    JudgeSpec,
    Rubric,
    RubricEntry,
    validate_result,
)
from harness.core.transport import (
    STOP_MAX_TOKENS,
    STOP_REFUSAL,
    CallCeilingReachedError,
    GenerationConfig,
    JudgeRequest,
    JudgeResponse,
    Transport,
    TransportError,
)
from harness.judge.citations import (
    JudgedAnswer,
    informed_retry_message,
    invalid_citations,
    read_answer,
    unresolved_dimensions,
)
from harness.judge.prompt import (
    PromptTemplate,
    RenderedPrompt,
    SynthesisInput,
    absent_categories,
    render_prompt,
    response_schema,
)
from harness.judge.rollup import _modal

#: What an `errored` result says when the response was cut off at the token
#: ceiling. A constant because both legs of the repetition reach it -- the first
#: attempt and the retry -- and two wordings for one classification is two
#: things a log inspector has to know to look for.
_TRUNCATED: Final[str] = (
    "the response was truncated at max_tokens, so no complete structured answer was "
    "returned. Raise this entry's max_tokens; the stop reason is in the run log."
)

#: What an `errored` result says when the response carried no stop reason.
#: "Every run-log entry for a judged call carries a `stop_reason`; the count
#: missing one is zero" is a criterion about the ARTIFACT, and it was asserted
#: over committed logs while the engine treated a missing one as an ordinary
#: complete answer.
_NO_STOP_REASON: Final[str] = (
    "the response carried no stop_reason, so whether it is complete is unknown. A "
    "verdict read out of it would be a verdict about an unknown quantity."
)

#: How many informed retries one (entry, call, repetition) gets. One, and the
#: specification says one: a model that could not cite from a list it was shown
#: twice is not going to be helped by a third showing, and each showing carries
#: a whole transcript.
INFORMED_RETRY_BUDGET: Final[int] = 1


@dataclass(frozen=True, slots=True)
class JudgedOutcome:
    """One repetition's result, plus what only a judged call has.

    The judged fields live here rather than on `Result` because **the Result
    contract freezes at P2** and every later phase reads it. A phase that added
    a field to it would be a phase that changed the channel, which is the thing
    the freeze exists to prevent.
    """

    result: Result
    repetition: int
    """Which of N this outcome is, from 1. **`0` means no repetition was
    performed**, because the entry's precondition did not hold for this call
    and no request was issued -- so `request_hash` and `stop_reason` are empty
    for the same reason, and the run log holds nothing for it."""

    request_hash: str
    stop_reason: str
    informed_retries: int
    """0 when the first answer validated, 1 when the retry was spent. The
    third counter in the system and named for what it counts: `repetition` is
    N, `informed_retries` is this, and `transport_attempts` in the run log is
    the backoff loop. A single "retry count" would be one of the three."""

    unresolved_dimensions: tuple[str, ...] = ()
    """Dimension identifiers a synthesis rested on that produced no result for
    this call in this run. **A defect carried beside the result rather than
    instead of it**: the requirement says report, and a synthesis that reasoned
    from a dimension that did not run still produced a verdict a reader has to
    be able to see and distrust. Empty for every entry that is not the
    synthesis."""


@dataclass(frozen=True, slots=True)
class JudgedRun:
    """Everything one judged run produced, and why it stopped if it stopped early."""

    outcomes: tuple[JudgedOutcome, ...] = ()
    aborted: str | None = None
    """The named cause when the run halted before finishing: a call ceiling
    reached, or a transport that exhausted its backoff. `None` when the run
    completed. Results already obtained are in `outcomes` either way -- an
    abort that discarded them would make the run log the only record of work
    the harness had actually done."""

    entry_ids: tuple[str, ...] = ()

    def for_entry(self, entry_id: str) -> tuple[JudgedOutcome, ...]:
        return tuple(o for o in self.outcomes if o.result.entry_id == entry_id)

    def for_call(self, call_id: str) -> tuple[JudgedOutcome, ...]:
        return tuple(o for o in self.outcomes if o.result.call_id == call_id)


class JudgedCallAborted(Exception):
    """A transport failure part-way through one call's repetitions.

    **Carries the outcomes already obtained**, and that is the whole reason it
    exists. The repetition loop used to let a `TransportError` propagate, so a
    run that failed on repetition 2 of 10 discarded repetition 1 -- while
    `RecordingTransport` had already written it to the run log. The run then
    reported `results: 0` over a log holding one entry, which is the harness
    disagreeing with its own artifact about work it had actually done.

    Found by a CLI replay test whose reference log covered fewer repetitions
    than the rubric asked for: the cache miss on repetition 2 was correct
    behavior, and the zero was not.
    """

    def __init__(self, cause: Exception, obtained: Sequence[JudgedOutcome]) -> None:
        super().__init__(str(cause))
        self.cause = cause
        self.obtained = tuple(obtained)


def _spec_of(entry: RubricEntry) -> JudgeSpec:
    """The judged configuration, or a refusal that this is not a judged entry.

    The loader guarantees `judge` is present exactly when the tier is `judge`,
    so reaching here without one means an entry was built around the loader.
    Raised rather than defaulted: a judged call assembled from defaults is a
    call whose configuration is in Python.
    """
    if entry.judge is None:
        raise ValueError(
            f"rubric entry {entry.id!r} reached the judged engine with no judged "
            "configuration. Entries are built by the loader, which refuses that shape."
        )
    return entry.judge


def build_request(
    entry: RubricEntry,
    rendered: RenderedPrompt,
    *,
    call_id: str,
    repetition: int,
    retry_index: int,
    user: str | None = None,
) -> JudgeRequest:
    """One wire request. `user` overrides the rendered message for the retry.

    **A synthesis is asked for `rests_on` only when its prompt listed a dimension**
    (D165). The schema used to follow the entry alone, so a synthesis shown none --
    its prompt saying `NO_DIMENSION_RESULTS`, "do not invent a dimension identifier"
    -- was still held to naming one, and any name it gave came back unresolved, a
    defect on every repetition that was the harness's and not the model's (P4-28).
    Shown dimensions, the schema is the one every recorded synthesis request carries.
    """
    spec = _spec_of(entry)
    asks_rests_on = is_synthesis(entry) and bool(rendered.rests_on)
    return JudgeRequest(
        entry_id=entry.id,
        call_id=call_id,
        repetition=repetition,
        retry_index=retry_index,
        system=rendered.system,
        prompt=rendered.user if user is None else user,
        schema=response_schema(entry.scale, synthesis=asks_rests_on),
        config=GenerationConfig(model=spec.model, max_tokens=spec.max_tokens, effort=spec.effort),
    )


def is_synthesis(entry: RubricEntry) -> bool:
    """Whether this entry is the call-level synthesis.

    Read off the entry's declared `check`, which the loader validates against
    `KNOWN_JUDGE_CHECKS`. Not off the id, and not off a flag: the check key is
    how every other tier decision in this project is made, and an id-shaped
    test would make `J-synthesis-of-something-else` behave differently from
    `J-call-synthesis` for no reason a rubric author could see.
    """
    return entry.check == SYNTHESIS_CHECK


def _evidence_for(answer: JudgedAnswer, rendered: RenderedPrompt) -> tuple[str, ...]:
    """The cited lines, quoted, so a reader can audit without re-rendering.

    Falls back to the bare identifier only for something the universe does not
    hold -- which cannot happen on this path, because evidence is built only
    after every citation validated. Kept as a total function rather than an
    assertion, so a future caller that validates differently degrades to a
    weaker evidence line instead of raising inside a result builder.
    """
    lines: list[str] = []
    for raw in answer.citations:
        identifier = raw.strip().strip("[]")
        lines.append(rendered.citable.text_of(identifier) or raw)
    lines.append(f"judge rationale: {answer.rationale}")
    return tuple(lines)


def _result_from_answer(
    answer: JudgedAnswer, rendered: RenderedPrompt, builder: ResultBuilder, entry: RubricEntry
) -> Result:
    """An applicable result, validated against the entry that asked for it.

    `validate_result` is called here rather than left to a caller, so a verdict
    outside the declared scale is refused at the point the model produced it.
    Structured output makes that unlikely and not impossible -- and "unlikely"
    is what the schema already bought; this is what happens when it does not
    hold.
    """
    result = builder.applicable(answer.verdict, _evidence_for(answer, rendered))
    validate_result(result, entry)
    return result


def _refused_result(builder: ResultBuilder, response: JudgeResponse) -> Result:
    """`status: refused`, carrying the category the API gave for it.

    The category and explanation go in the run log unconditionally; the detail
    here is for a human reading the run's output, which is why it names the
    category rather than reproducing the explanation verbatim.
    """
    category = response.stop_category or "(none given)"
    return builder.refused(f"the model declined to answer; stop_details.category={category}")


def _rendered(
    entry: RubricEntry,
    context: CheckContext,
    template: PromptTemplate,
    *,
    synthesis: SynthesisInput | None,
) -> RenderedPrompt:
    """This entry's prompt for this call, with the synthesis block or without it.

    One function for both paths, so a dimension's prompt and a synthesis
    repetition's can differ only in the block the synthesis is given. Two copies
    of these arguments would be two chances for them to differ in something else.
    """
    spec = _spec_of(entry)
    return render_prompt(
        template,
        context,
        entry_id=entry.id,
        question=spec.question,
        criteria=spec.criteria,
        scale=entry.scale,
        scale_definitions=spec.scale_definitions,
        requires_facts=spec.requires_facts,
        synthesis=synthesis,
    )


def evaluate_call(
    entry: RubricEntry,
    context: CheckContext,
    provenance: Provenance,
    *,
    template: PromptTemplate,
    transport: Transport,
    prior: Sequence[JudgedOutcome] = (),
    rubric: Rubric | None = None,
) -> tuple[JudgedOutcome, ...]:
    """One judged entry against one call, N times.

    **A dimension's prompt is rendered once** and reused across repetitions.
    That is what makes N a measurement of evaluator variance rather than of
    rendering variance (D17): the requests are byte-identical by construction,
    so any difference in the verdicts came from the model.

    **The synthesis's prompt is rendered per repetition**, each over its own
    resample of the dimensions' results (D154). Its input is itself a sample:
    rendered once, its repetitions all read one draw of the other dimensions,
    so they measured only what varies once that draw is fixed and were reported
    as though they measured the verdict (D150). `rubric` is required for a
    synthesis and read only for one, because a tied dimension is resolved by
    that dimension's own scale, which an outcome does not carry.
    """
    spec = _spec_of(entry)

    # **The precondition, before anything is rendered or sent** (D125). A
    # dimension whose subject is absent from this call does not apply to it,
    # and answering anyway is what produced four reproducible `misaligned`
    # verdicts on calls that had retrieved no clause to be misaligned with.
    #
    # `not_applicable` rather than `unevaluable`, and the two are not
    # interchangeable: `unevaluable` says the corpus failed to supply ground
    # truth the dimension needed, which is a finding against the corpus.
    # Nothing failed here. The agent did not retrieve a policy, so there is no
    # clause for the question to be about -- the builder's own words for that
    # status are "the check's precondition did not occur in this call".
    absent = absent_categories(context, spec.applies_when_facts_present, entry_id=entry.id)
    if absent:
        builder = ResultBuilder(entry=entry, call_id=context.call_id, provenance=provenance)
        return (
            JudgedOutcome(
                result=builder.not_applicable(
                    f"this call establishes no {', '.join(absent)}, which this dimension is "
                    "about, so there is nothing here for it to judge. No call was issued."
                ),
                repetition=0,
                request_hash="",
                stop_reason="",
                informed_retries=0,
            ),
        )

    if not is_synthesis(entry):
        renders = (_rendered(entry, context, template, synthesis=None),) * spec.repetitions
    else:
        if rubric is None:
            raise ValueError(
                f"{entry.id!r} is a synthesis and was given no rubric, so a tied dimension "
                "could not be shown the verdict the report resolves it to (D154)"
            )
        renders = tuple(
            _rendered(
                entry,
                context,
                template,
                synthesis=synthesis_input(
                    prior, call_id=context.call_id, rubric=rubric, repetition=repetition
                ),
            )
            for repetition in range(1, spec.repetitions + 1)
        )

    outcomes: list[JudgedOutcome] = []
    for repetition, rendered in enumerate(renders, start=1):
        try:
            outcomes.append(
                _evaluate_repetition(
                    entry,
                    context,
                    provenance,
                    rendered=rendered,
                    transport=transport,
                    repetition=repetition,
                    synthesis=is_synthesis(entry),
                )
            )
        except (CallCeilingReachedError, TransportError) as exc:
            # Everything obtained so far travels with the exception. The run log
            # already holds these entries, and a run that reported fewer results
            # than its own log would be disagreeing with the artifact the
            # requirement is written about.
            raise JudgedCallAborted(exc, outcomes) from exc
    return tuple(outcomes)


def synthesis_input(
    prior: Sequence[JudgedOutcome], *, call_id: str, rubric: Rubric, repetition: int
) -> SynthesisInput:
    """The other dimensions' results for one call, as one repetition of the synthesis sees them.

    **`call_id` is checked, not carried.** It appears nowhere in what is
    rendered; it is here so that handing this function another call's outcomes
    raises instead of quietly producing a prompt. A run-wide accumulator in the
    caller would merge two calls' repetitions into one line and the block would
    read as a plausible summary of a call that never happened -- which is a
    defect a test on the rendered text cannot see, because the rendering names
    no call. Made impossible rather than detectable.

    **One line per entry, not per repetition.** N repetitions of one dimension
    are a distribution, and handing a synthesis ten near-identical rationales
    would spend its context on the part that varies least. The modal verdict
    with its counts is the distribution; one rationale from a repetition that
    reached that verdict is the reasoning.

    **An entry that produced no verdict still appears**, carrying its status.
    A dimension that did not apply to this call, or errored, or was refused, is
    a fact about the call the synthesis needs -- and leaving it out would let
    the synthesis read absence as agreement.

    **Each repetition reads its own resample** (D154). Every dimension's line
    is `dimension_line` over `resample` of that dimension's outcomes for this
    `repetition`, so the synthesis's repetitions stop reading one draw, and the
    headline a line carries is the report's modal verdict. `rubric` supplies
    the scale and the violating verdicts a tied headline is resolved by (D160).

    `entry_ids` is every entry listed, which is exactly the set a `rests_on`
    identifier is validated against: an id it can see is an id it may name.
    """
    stray = sorted({outcome.result.call_id for outcome in prior} - {call_id})
    if stray:
        raise ValueError(
            f"the synthesis for {call_id!r} was given results for {', '.join(stray)}. Its "
            "prompt is about one call, so another call's repetitions would merge into these "
            "lines and read as a summary of a call that never happened."
        )
    by_entry: dict[str, list[JudgedOutcome]] = {}
    for outcome in prior:
        by_entry.setdefault(outcome.result.entry_id, []).append(outcome)

    lines = tuple(
        dimension_line(
            rubric.by_id(entry_id),
            resample(by_entry[entry_id], call_id=call_id, entry_id=entry_id, repetition=repetition),
        )
        for entry_id in sorted(by_entry)
    )
    return SynthesisInput(results=lines, entry_ids=tuple(sorted(by_entry)))


def resample(
    outcomes: Sequence[JudgedOutcome], *, call_id: str, entry_id: str, repetition: int
) -> tuple[JudgedOutcome, ...]:
    """One dimension's repetitions as one repetition of the synthesis sees them (D154).

    **A draw with replacement, as many as there are**, so the line the synthesis
    reads varies across its repetitions the way it would across reruns -- in its
    counts, in its headline where a dimension is close, and in the rationale it
    quotes -- while keeping the shape the synthesis has always read. Rendered
    once per call, every repetition read one draw of the other dimensions'
    results, and N samples of that conditional were reported as N samples of the
    verdict (D150).

    **Seeded by the call, the dimension and the repetition, and by nothing a run
    decides.** Each index is read off a SHA-256 digest rather than `random`, whose
    integer draws Python does not promise to reproduce across versions, so a
    replay renders exactly the prompts the recording sent and finds every one.
    """
    population = sorted(outcomes, key=lambda outcome: outcome.repetition)
    if not population:
        return ()
    drawn: list[JudgedOutcome] = []
    for draw in range(len(population)):
        seed = f"{call_id}\n{entry_id}\n{repetition}\n{draw}".encode()
        index = int.from_bytes(hashlib.sha256(seed).digest()[:8], "big") % len(population)
        drawn.append(population[index])
    return tuple(drawn)


def dimension_line(entry: RubricEntry, outcomes: Sequence[JudgedOutcome]) -> str:
    """One dimension's result for one call, as the synthesis block renders it.

    **The headline is the report's modal verdict, tie rule included** (D154).
    It was `Counter.most_common`, which names whichever tied verdict the earliest
    repetition returned, while the report resolves a tie toward the negative
    pole -- and in the committed run the two disagreed on every tied
    dimension-call pair there was, so the synthesis reasoned from verdicts the
    report did not publish. `_modal` is called rather than restated, so the two
    cannot drift apart again.

    An entry that produced no verdict still appears, carrying its status, for the
    reason `synthesis_input` gives.
    """
    verdicts = [o.result.verdict for o in outcomes if o.result.verdict is not None]
    if not verdicts:
        statuses = sorted({o.result.status.value for o in outcomes})
        detail = next((o.result.detail for o in outcomes if o.result.detail), "")
        return f"{entry.id}: no verdict ({', '.join(statuses)}). {detail}".strip()
    counts = Counter(verdicts)
    distribution = tuple((member, counts[member]) for member in entry.scale if counts[member])
    modal = _modal(distribution, entry)
    spread = ", ".join(f"{v} x{n}" for v, n in sorted(counts.items()))
    rationale = next(
        (
            o.result.evidence[-1]
            for o in outcomes
            if o.result.verdict == modal and o.result.evidence
        ),
        "",
    )
    return (
        f"{entry.id}: {modal} ({counts[modal]} of {len(verdicts)} repetitions; {spread})\n"
        f"  {rationale}"
    ).rstrip()


def _evaluate_repetition(
    entry: RubricEntry,
    context: CheckContext,
    provenance: Provenance,
    *,
    rendered: RenderedPrompt,
    transport: Transport,
    repetition: int,
    synthesis: bool = False,
) -> JudgedOutcome:
    """One repetition, with the classification order the module docstring sets."""
    builder = ResultBuilder(entry=entry, call_id=context.call_id, provenance=provenance)
    request = build_request(
        entry, rendered, call_id=context.call_id, repetition=repetition, retry_index=0
    )
    response = transport.send(request)

    # (0) A response carrying no stop reason at all. The API sends one on every
    # message, so this is a transport or a log that lost it -- and the engine
    # used to read the empty string as "not a refusal, not a truncation" and
    # carry on parsing, which resolves a response of unknown completeness to a
    # verdict. Both run-log count guards would flag the empty value in a
    # committed log; nothing flagged it in the run that produced one.
    if not response.stop_reason:
        return JudgedOutcome(
            result=builder.errored(_NO_STOP_REASON),
            repetition=repetition,
            request_hash=request.request_hash,
            stop_reason=response.stop_reason,
            informed_retries=0,
        )

    # (1) A refusal, before anything is parsed. It consumes no retry.
    if response.stop_reason == STOP_REFUSAL:
        return JudgedOutcome(
            result=_refused_result(builder, response),
            repetition=repetition,
            request_hash=request.request_hash,
            stop_reason=response.stop_reason,
            informed_retries=0,
        )

    # (2) Truncation, before anything is parsed. Parsing first would report
    # this as a schema failure and spend the retry on the same request.
    if response.stop_reason == STOP_MAX_TOKENS:
        return JudgedOutcome(
            result=builder.errored(_TRUNCATED),
            repetition=repetition,
            request_hash=request.request_hash,
            stop_reason=response.stop_reason,
            informed_retries=0,
        )

    # (3) A complete response: parse, then check citations, then retry once.
    validation = _validate(response, rendered)
    answer = validation.answer
    if answer is not None:
        return JudgedOutcome(
            result=_result_from_answer(answer, rendered, builder, entry),
            repetition=repetition,
            request_hash=request.request_hash,
            stop_reason=response.stop_reason,
            informed_retries=0,
            unresolved_dimensions=(
                unresolved_dimensions(answer.rests_on, rendered.rests_on) if synthesis else ()
            ),
        )

    if INFORMED_RETRY_BUDGET < 1:  # pragma: no cover - the budget is one
        return JudgedOutcome(
            result=builder.errored(validation.detail or "the response could not be validated"),
            repetition=repetition,
            request_hash=request.request_hash,
            stop_reason=response.stop_reason,
            informed_retries=0,
        )

    # The correction names every fault it was sent for, each in its own words (D179),
    # and shows a synthesis the dimensions it may rest on beside a schema failure (D164).
    retry_request = build_request(
        entry,
        rendered,
        call_id=context.call_id,
        repetition=repetition,
        retry_index=1,
        user=informed_retry_message(
            rendered.user,
            validation.rejected,
            rendered.citable,
            failure="; ".join(validation.schema_failures) or None,
            dimensions=rendered.rests_on,
        ),
    )
    retry_response = transport.send(retry_request)

    if retry_response.stop_reason == STOP_REFUSAL:
        return JudgedOutcome(
            result=_refused_result(builder, retry_response),
            repetition=repetition,
            request_hash=retry_request.request_hash,
            stop_reason=retry_response.stop_reason,
            informed_retries=1,
        )

    # The retry gets the SAME classification order the first attempt gets.
    # It did not, and the asymmetry was invisible because both legs reach
    # `errored`: a retry truncated at `max_tokens` was parsed anyway, failed,
    # and resolved to "retry budget exhausted ... the response is not valid
    # JSON" while the run log carried `max_tokens`. The requirement is that
    # truncation is distinguishable from a validation failure BY LOG
    # INSPECTION, which it was -- and the result described the wrong one.
    if retry_response.stop_reason == STOP_MAX_TOKENS:
        return JudgedOutcome(
            result=builder.errored(_TRUNCATED),
            repetition=repetition,
            request_hash=retry_request.request_hash,
            stop_reason=retry_response.stop_reason,
            informed_retries=1,
        )

    retry = _validate(retry_response, rendered)
    retry_answer = retry.answer
    if retry_answer is not None:
        return JudgedOutcome(
            result=_result_from_answer(retry_answer, rendered, builder, entry),
            repetition=repetition,
            request_hash=retry_request.request_hash,
            stop_reason=retry_response.stop_reason,
            informed_retries=1,
            unresolved_dimensions=(
                unresolved_dimensions(retry_answer.rests_on, rendered.rests_on) if synthesis else ()
            ),
        )

    return JudgedOutcome(
        result=builder.errored(
            "the retry budget for this dimension is exhausted and no valid answer was "
            f"produced. Last failure: {retry.detail}"
        ),
        repetition=repetition,
        request_hash=retry_request.request_hash,
        stop_reason=retry_response.stop_reason,
        informed_retries=1,
    )


@dataclass(frozen=True, slots=True)
class _Validation:
    """Every fault one response shows, found in one pass (D179).

    `answer` is set only when there is none. `schema_failures` is what the
    correction's schema wording names; `detail` names everything, the rejected
    identifiers first, for an `errored` result.
    """

    answer: JudgedAnswer | None
    rejected: tuple[str, ...]
    schema_failures: tuple[str, ...]

    @property
    def detail(self) -> str | None:
        parts = list(self.schema_failures)
        if self.rejected:
            parts.insert(0, f"cited identifier(s) not in the prompt: {', '.join(self.rejected)}")
        return "; ".join(parts) or None


def _validate(response: JudgeResponse, rendered: RenderedPrompt) -> _Validation:
    """Parse and check citations and `rests_on`, naming every fault found.

    One function so the first attempt and the retry are validated identically.
    Two copies of this would be two chances for the retry to be judged by a
    weaker rule than the attempt it is correcting.

    **Every fault, not the first** (P4-30, D179). This returned at the first fault
    it met -- the parse, then the citations, then `rests_on` -- so an answer citing
    `T999` with an empty `rests_on` was corrected for `T999` alone, and a retry that
    fixed it and kept the other was refused. Invalid JSON still stops everything,
    since nothing past it can be read.
    """
    reading = read_answer(response.text)
    schema = [str(failure) for failure in reading.failures]
    rejected = invalid_citations(reading.citations, rendered.citable) if reading.citations else ()
    # A synthesis resting on nothing is the declared schema's failure too (D163). Asked
    # only when the prompt listed dimensions to rest on: a synthesis shown none has
    # nothing to name.
    if rendered.rests_on and reading.rests_on == ():
        schema.append(
            "'rests_on' is empty, and the synthesis's declared schema requires at least one "
            "identifier"
        )
    answer = reading.answer if not rejected and not schema else None
    return _Validation(answer=answer, rejected=rejected, schema_failures=tuple(schema))


def run_judged(
    rubric: Rubric,
    contexts: Sequence[CheckContext],
    provenance: Provenance,
    *,
    template: PromptTemplate,
    transport: Transport,
) -> JudgedRun:
    """Every judged entry against every call, in a fixed order.

    Order is (call, entry, repetition), sorted, for the same reason the
    deterministic engine sorts: an order that depends on iteration is an order
    that will differ, and the run log is addressed by content rather than by
    position precisely so that it does not have to be stable -- but a *report*
    read by a human does.

    A `CallCeilingReachedError` or a `TransportError` stops the run and is
    recorded in `aborted`. Everything obtained before it is returned, and
    everything obtained before it is already in the run log.
    """
    entries = judged_order(rubric)
    outcomes: list[JudgedOutcome] = []
    aborted: str | None = None

    for context in sorted(contexts, key=lambda c: c.call_id):
        if aborted is not None:
            break
        # **What this call has produced so far**, which is what a synthesis
        # rests on. Scoped to the call rather than to the run: a synthesis
        # reasoning across dimensions for CALL-02 has no business seeing
        # CALL-04's verdicts, and a run-wide accumulator would hand it every
        # verdict recorded before it in file order -- a different prompt
        # depending on which call happened to be evaluated first.
        so_far: list[JudgedOutcome] = []
        for entry in entries:
            try:
                produced = evaluate_call(
                    entry,
                    context,
                    provenance,
                    template=template,
                    transport=transport,
                    prior=tuple(so_far),
                    rubric=rubric,
                )
            except JudgedCallAborted as exc:
                outcomes.extend(exc.obtained)
                if isinstance(exc.cause, CallCeilingReachedError):
                    aborted = str(exc.cause)
                else:
                    aborted = (
                        f"the transport failed on entry {entry.id!r} call "
                        f"{context.call_id!r} and the run cannot continue: {exc.cause}"
                    )
                break
            outcomes.extend(produced)
            so_far.extend(produced)

    return JudgedRun(
        outcomes=tuple(outcomes),
        aborted=aborted,
        entry_ids=tuple(entry.id for entry in entries),
    )


def judged_order(rubric: Rubric) -> tuple[RubricEntry, ...]:
    """Judged entries in execution order: every dimension, then every synthesis.

    **The order is the contract, not a convenience.** A synthesis rests on the
    results of the dimensions evaluated for the same call, so one evaluated
    before them rests on nothing -- shown no dimension, it is asked for no
    `rests_on` (D165) and returns a verdict about the call that synthesizes
    nothing, for a reason that is the harness's and not the model's.

    Within each group the order is by id, for the reason both engines sort: an
    order that depends on iteration is an order that will differ, and a report
    a human reads has to be stable even though the run log is addressed by
    content.
    """
    entries = sorted(rubric.for_tier(CheckTier.JUDGE), key=lambda entry: entry.id)
    # `sorted` is stable and `False < True`, so this is "dimensions in id order,
    # then syntheses in id order" -- written as one key rather than two list
    # comprehensions so that a control can plant the ordering defect by
    # changing what is sorted on.
    return tuple(sorted(entries, key=is_synthesis))


def first_attempt_dimension_requests(
    rubric: Rubric, contexts: Sequence[CheckContext], template: PromptTemplate
) -> tuple[JudgeRequest, ...]:
    """Every first-attempt request the rubric's dimensions would send, built before any is sent.

    **Known ahead for a dimension and not for a synthesis** (OB-24, D168). A
    dimension's prompt depends on the call alone, so its requests can be built and
    looked up in a log before anyone approves spend; a synthesis's depends on what
    the dimensions answer, which exists only once the run has it. Rendered the way
    `evaluate_call` renders them -- once per call, reused across repetitions, and
    only for the calls whose precondition holds -- so a request built here hashes
    as the run's own does.
    """
    requests: list[JudgeRequest] = []
    for entry in judged_order(rubric):
        if is_synthesis(entry):
            continue
        spec = _spec_of(entry)
        for context in contexts:
            if absent_categories(context, spec.applies_when_facts_present, entry_id=entry.id):
                continue
            rendered = _rendered(entry, context, template, synthesis=None)
            requests.extend(
                build_request(
                    entry,
                    rendered,
                    call_id=context.call_id,
                    repetition=repetition,
                    retry_index=0,
                )
                for repetition in range(1, spec.repetitions + 1)
            )
    return tuple(requests)
