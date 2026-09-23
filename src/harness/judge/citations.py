"""Validating citations by set membership, and the one informed retry.

Deterministic, and listed as such in the specification's determinism boundary:
"citation validation by set membership" is plain code. No model is asked whether
a citation is real.

**Each population is validated against its own set.** `[T3]` is checked against
the transcript identifiers and `[F3]` against the fact identifiers, never
against the union. A validator using the union accepts a fabricated `[F9]` on a
call with twelve turns and two facts, because `F9` is not in the fact set but
*something* numbered 9 was rendered -- which is the near miss that reads as a
pass. The two prefixes exist precisely so this check can be made.

**The retry is informed, and once.** A judge that cited something that does not
exist is told which identifiers were rejected and given the full valid set
again. Once, because a second identical correction spends money to reach the
same place: if the model could not cite from a list it was shown twice, a third
showing is not the missing ingredient. Exhaustion resolves to `errored`, which
is a status and not a verdict -- the harness reports that it could not evaluate
this dimension on this call, rather than reporting a judgment it does not have.

**The detector is proven against a true positive.** The specification asks for
that in as many words, because the reference implementation's citation
validation produced zero confirmed true positives -- it was never tested
against a deliberately fabricated citation, so nothing distinguished "the
judges never fabricated" from "the detector never fired".
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

from harness.judge.prompt import CitableUniverse

#: Strips the brackets a model may or may not include. `[T3]`, `T3` and ` T3 `
#: are the same citation, and refusing two of the three would spend the retry
#: budget on formatting rather than on fabrication. Anything else is left
#: exactly as it arrived, so a genuinely malformed identifier stays malformed
#: and is reported as rejected rather than repaired into something valid.
_BRACKETED: Final[re.Pattern[str]] = re.compile(r"^\[?([A-Za-z]+\d+)\]?$")


class CitationError(Exception):
    """Base for the response-validation refusals."""


class MalformedResponseError(CitationError):
    """The response is not the JSON object the schema declared.

    Reached when structured output did not hold -- most often because the
    response was truncated at `max_tokens`, which is why the engine checks the
    stop reason *before* it gets here. A truncation reported as a schema
    failure is D24's conflation by a different route.
    """


class UncitedAnswerError(MalformedResponseError):
    """The response cites nothing, which the declared schema's `minItems: 1` forbids.

    Refused here rather than trusted to the schema (P4-23, D163). The engine appends the
    judge's rationale to every result's evidence, so a verdict citing nothing still carried
    an evidence line, passed the evidence guard, and counted against a gate -- the pole
    included -- on nothing a reader could audit. As a schema failure it spends the one
    informed retry, so the model is asked again before anything is recorded.
    """


@dataclass(frozen=True, slots=True)
class JudgedAnswer:
    """A well-formed judge response, before its citations are checked."""

    verdict: str
    rationale: str
    citations: tuple[str, ...]

    rests_on: tuple[str, ...] = ()
    """Rubric identifiers a synthesis says its verdict depends on. Empty for
    every other entry, because the field is only in the declared schema for a
    synthesis shown at least one dimension (D165) -- so an empty tuple here
    means *not asked for*, never *asked for and left blank*: the schema requires
    at least one when it is present."""


def normalize_identifier(raw: str) -> str:
    """`[T3]` -> `T3`. Anything not of that shape is returned unchanged."""
    match = _BRACKETED.match(raw.strip())
    return match.group(1) if match else raw.strip()


@dataclass(frozen=True, slots=True)
class AnswerReading:
    """Everything a response's text yields, with every schema failure found reading it.

    `answer` is built only when every declared field reads as the schema says.
    `citations` and `rests_on` are kept beside it, so a fault in one field does not
    hide a fault in another: an empty `citations` list no longer stops an empty
    `rests_on` from being found (P4-30, D179). `rests_on` absent reads as empty, as
    it always has; either is `None` when it could not be read as a list.
    """

    answer: JudgedAnswer | None
    failures: tuple[MalformedResponseError, ...]
    citations: tuple[str, ...] | None = None
    rests_on: tuple[str, ...] | None = None


def read_answer(text: str) -> AnswerReading:
    """Every schema failure a response's text shows, in the order they are met.

    Every field is required by the schema, so a missing one means the schema
    did not hold rather than that a default should be supplied. Supplying one
    would turn a broken response into a plausible verdict, which is the failure
    this whole tier is built to avoid.

    Invalid JSON, or a value that is not an object, stops the reading: nothing
    past it can be read. Past that, a missing declared field, a `citations` or
    `rests_on` that is not a list and an empty `citations` are each recorded,
    and the reading goes on (D179).
    """
    try:
        payload: Any = json.loads(text)
    except json.JSONDecodeError as exc:
        return AnswerReading(None, (MalformedResponseError(f"response is not valid JSON: {exc}"),))
    if not isinstance(payload, Mapping):
        kind = type(payload).__name__
        refusal = MalformedResponseError(
            f"response parsed as {kind}, and the declared schema is an object"
        )
        return AnswerReading(None, (refusal,))
    failures: list[MalformedResponseError] = []
    missing = [key for key in ("verdict", "rationale", "citations") if key not in payload]
    if missing:
        failures.append(
            MalformedResponseError(f"response is missing declared field(s): {', '.join(missing)}")
        )
    citations: tuple[str, ...] | None = None
    if "citations" in payload:
        listed = payload["citations"]
        if not isinstance(listed, Sequence) or isinstance(listed, str):
            failures.append(MalformedResponseError("'citations' is not a list"))
        else:
            citations = tuple(str(item) for item in listed)
            if not citations:
                failures.append(
                    UncitedAnswerError(
                        "'citations' is empty, and the declared schema requires at least one "
                        "identifier"
                    )
                )
    rests_on: tuple[str, ...] | None = None
    resting = payload.get("rests_on", ())
    if not isinstance(resting, Sequence) or isinstance(resting, str):
        failures.append(MalformedResponseError("'rests_on' is not a list"))
    else:
        rests_on = tuple(str(item) for item in resting)
    answer: JudgedAnswer | None = None
    if not failures and citations is not None and rests_on is not None:
        answer = JudgedAnswer(
            verdict=str(payload["verdict"]),
            rationale=str(payload["rationale"]),
            citations=citations,
            rests_on=rests_on,
        )
    return AnswerReading(answer, tuple(failures), citations, rests_on)


def parse_answer(text: str) -> JudgedAnswer:
    """The declared JSON object, or a refusal naming the first thing wrong with it.

    For a caller that wants one refusal. The engine reads every fault through
    `read_answer`, because a correction naming only the first spends the one
    retry on half of it (D179).
    """
    reading = read_answer(text)
    if reading.failures:
        raise reading.failures[0]
    if reading.answer is None:  # pragma: no cover - no failure means every field was read
        raise MalformedResponseError("the response could not be read as the declared object")
    return reading.answer


def unresolved_dimensions(rests_on: Sequence[str], produced: Sequence[str]) -> tuple[str, ...]:
    """Dimension identifiers a synthesis rested on that produced no result here.

    **A defect to report, not a retry to spend.** The requirement's verb is
    *report*: "WHEN the synthesis dimension cites a rubric identifier that did
    not produce a result in the same run, the system SHALL report that citation
    as a defect." A fabricated `[T<n>]` buys the informed retry because the
    model can be shown the valid set and answer again; a synthesis resting on a
    dimension that did not run has reasoned from a result that does not exist,
    and re-asking would not tell a reader that it had.

    Returns the raw identifiers in the order they arrived, like
    `invalid_citations` and for the same reason: the report quotes them back,
    and quoting a repaired form would hide the shape the model produced.

    Duplicates are preserved. A synthesis naming one absent dimension twice has
    done it twice, and de-duplicating here would make the report's count
    disagree with the response the log holds.
    """
    valid = frozenset(produced)
    return tuple(raw for raw in rests_on if raw.strip() not in valid)


def invalid_citations(cited: Sequence[str], universe: CitableUniverse) -> tuple[str, ...]:
    """The cited identifiers that were not offered, in the order they arrived.

    **The named function the requirement is bought with**, and named for the
    same reason `scrub_credentials` is: a control has to be able to drive the
    shipped comparison rather than re-implement it beside the check. Six
    controls in this tree did the latter and every one of them was measuring
    nothing (D121).

    Returns the *raw* identifiers rather than the normalized ones, because the
    retry prompt quotes them back to the model and quoting a repaired form
    would hide the shape the model actually produced.
    """
    rejected: list[str] = []
    for raw in cited:
        identifier = normalize_identifier(raw)
        population = universe.population_of(identifier)
        if population == "transcript":
            valid = identifier in universe.transcript
        elif population == "facts":
            valid = identifier in universe.facts
        else:
            # Neither prefix. Not a citation this project's two populations can
            # express, so it cannot be checked against either set -- and a
            # citation that cannot be checked is rejected rather than assumed.
            valid = False
        if not valid:
            rejected.append(raw)
    return tuple(rejected)


def informed_retry_message(
    original_user: str,
    rejected: Sequence[str],
    universe: CitableUniverse,
    *,
    failure: str | None = None,
    dimensions: Sequence[str] = (),
) -> str:
    """The user message for the one retry, carrying the correction.

    Both halves the requirement names: **the rejected identifiers** and **the
    full valid identifier set**. The rejected ones alone would leave the model
    to guess what it should have cited; the valid set alone would not tell it
    what it got wrong, and a model told only "try again" tends to return the
    same answer.

    **Two wordings, because the retry has two causes.** A citation failure has
    rejected identifiers to quote; a response that did not parse as the declared
    schema has none, and this used to send the citation wording with an empty
    list -- "cited identifiers that were not in this prompt: ." -- which tells a
    model nothing about what was actually wrong. The valid set is sent either
    way: a malformed answer is still going to be asked for citations, and the
    universe is what it must draw them from.

    **The schema wording names the failure it was sent for** (D164). It used to
    say only that the answer could not be read as the declared object, so an
    answer that parsed and cited nothing was sent guidance about prose and code
    fences, and never told which list came back empty (P4-27). `failure` is the
    engine's own account: invalid JSON, a missing field, an empty `citations`
    or `rests_on`. **A synthesis corrected for a schema failure is shown its
    dimensions too**, bare, because `unresolved_dimensions` compares them as
    given; the identifier lists alone told a synthesis resting on nothing to
    cite transcript lines. A retry for rejected identifiers alone keeps its
    wording whatever `dimensions` holds, and every retry the committed log
    records is one of those.

    **An answer with both faults is told both** (D179). `failure` is the schema
    failures alone, joined by "; ", and a correction carrying rejected
    identifiers and a schema failure states each in the words above, the
    identifiers first, and shows a synthesis its dimensions. Naming only the
    first fault spent the one retry on half a correction (P4-30).

    Appended to the original message rather than replacing it. The transcript
    and facts have to still be there for the retry to be answerable at all, and
    rebuilding them would risk rendering a different universe from the one
    being corrected against.
    """
    transcript = ", ".join(f"[{identifier}]" for identifier in universe.transcript) or "(none)"
    facts = ", ".join(f"[{identifier}]" for identifier in universe.facts) or "(none)"
    complaints: list[str] = []
    if rejected:
        quoted = ", ".join(repr(item) for item in rejected)
        complaints.append(
            f"Your previous answer cited identifiers that were not in this prompt: {quoted}."
        )
    if failure or not rejected:
        named = f": {failure}" if failure else ""
        complaints.append(
            "Your previous answer could not be read as the JSON object this prompt "
            f"declares{named}. Return that object and nothing else: no prose before or after "
            "it, no code fence, and every key present."
        )
    complaint = "\n\n".join(complaints)
    closing = "Answer again, in the same JSON shape, citing only from those two lists."
    if dimensions and failure:
        closing = (
            f"Dimension identifiers, in full: {', '.join(dimensions)}\n\n"
            "Answer again, in the same JSON shape, citing only from the transcript and fact "
            "lists and resting only on those dimensions."
        )
    return (
        f"{original_user}\n\n"
        "# Correction\n\n"
        f"{complaint}\n\n"
        "An identifier that does not appear below does not exist. Do not infer one from a "
        "range, do not renumber, and do not cite a line you believe should be there.\n\n"
        f"Transcript identifiers, in full: {transcript}\n\n"
        f"Established-fact identifiers, in full: {facts}\n\n"
        f"{closing}"
    )
