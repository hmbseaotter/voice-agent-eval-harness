"""Reading figures out of speech and out of facts, and comparing them.

A voice transcript spells its numbers. Across the design set, agent speech
carries **three** bare integers and no currency symbol, no ISO date and no bare
decimal: the agent says "eighty-five dollars", "five business days", "the
twenty-fourth". A grounding layer built on digit patterns would find nothing in
speech, return `not_applicable` on every call, and be a check proven against
nothing -- which is why this module exists before any check that uses it.

Every table here is passed in. The number lexicon is a signal list in the exact
sense the requirement means, so it lives in the rubric entry: mutating
`ninety` from 90 to 19 must change a verdict, and it does.

**What the shipped tier calls, because a module can close a defect the tier
never reaches.** `available_value_never_spoken` reads speech and payloads
through `figures_in`, filters candidates through `cue_follows` and compares
through `grounded`; `spoken_local_date_wrong` reads ordinals through
`parse_spelled`. **`complete_year` is called by nothing.** No shipped check
completes a year -- the date check compares the day alone -- so W8 below is
closed in this module and not reached by the tier, and the phase-2 verifier's
thirteenth criterion says so rather than ticking it. That is the residue of an
audit finding: the other three functions had no production caller either, and
the criterion claimed the tier through all four.

**Four known defects are closed here by construction, and each has a control.**

* **W5** -- a spoken figure grounding against a *longer* payload figure sharing
  its integer part, because the decimal point is a non-word character. Spoken
  "twenty-two dollars" against a payload of `22.50`: `\\b22\\b` matches inside
  `22.50`, because the character after `22` is a `.` and that *is* a word
  boundary. Every comparison here uses a digit-and-separator boundary instead,
  under both match modes, and the control asserts the difference against `re`
  directly -- because the claim is about what the old boundary did.
* **W6** -- one-sided normalization: separators stripped from the spoken value
  and never from the payload, so `1,050` never matched `1050`. Both sides go
  through the same function, and the control asserts it by mutating only the
  payload's separators.
* **W7** -- date matching case-sensitive while quantity matching was not, so a
  lower-cased month silently disabled the date arm: a false *pass* on its
  headline failure mode. Case folding is declared per call and applied to both
  sides, and the control flips it.
* **W8** -- a spoken date completed with a year sliced from call metadata,
  unvalidated, with no handling of a year boundary. `complete_year` chooses
  among declared candidate offsets by distance to the call date and refuses
  outside a declared window, and the control is a December call naming a
  January date.
"""

from __future__ import annotations

import datetime as dt
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Final


class ValueTableError(Exception):
    """A malformed table from the rubric. Never raised for malformed *speech*:
    a caller saying something unparseable is data, not a defect in the run."""


class MatchMode(StrEnum):
    r"""How a spoken figure is compared against the facts.

    Both are correct, for different kinds of figure, and an entry declares
    which it means.

    `NUMERIC` parses the facts into decimals and compares by value, so
    "eighty-five dollars" grounds against `85.00` and `22` does not ground
    against `22.50`. Right for quantities, where `85` and `85.00` are the same
    amount.

    `SUBSTRING` compares normalized surfaces under a digit-and-separator
    boundary. Right for identifiers, where **leading zeros are significant**:
    the ZIP `00461` is a token, and reading it as a decimal makes it 461 and
    equal to a ZIP that does not exist.

    Neither is W5. W5 is the `\b` word boundary, which finds `22` inside
    `22.50` because the character after it is a `.`; the boundary here is
    digits-and-separators, and the control asserts the difference against `re`
    directly rather than through this module.

    Raw, because it was not. The line above held a literal 0x08 byte where
    `\b` belonged -- the file was written through a shell that interpreted the
    escape -- so the sentence read "W5 is the `` word boundary" and named
    nothing. `test_no_source_file_carries_a_control_character` is the sweep
    that finds the next one; a raw docstring is what keeps this one readable
    when it is next edited.
    """

    NUMERIC = "numeric"
    SUBSTRING = "substring"


@dataclass(frozen=True, slots=True)
class Figure:
    """One number found in a piece of text, with where and how it was written."""

    surface: str
    """As written: `eighty-five`, `4417`, `22.50`."""
    amount: Decimal
    start: int
    end: int
    spelled: bool
    """True when it was read out of words rather than digits. Carried because a
    check reporting evidence should quote what was said, not a normalization."""


_WORD: Final[re.Pattern[str]] = re.compile(r"[A-Za-z']+|\d[\d,]*(?:\.\d+)?")


def normalize(text: str, *, strip: Sequence[str], fold_case: bool) -> str:
    """The one normalization, applied to both sides of every comparison.

    W6 is what happens when it is applied to one: separators stripped from the
    spoken value and never from the payload, so a thousands separator produced
    a false failure on every figure above nine hundred and ninety-nine.
    """
    for character in strip:
        text = text.replace(character, "")
    return text.casefold() if fold_case else text


def _compose(values: Sequence[int], scales: Mapping[str, int], words: Sequence[str]) -> int:
    """Standard English composition over one run of number words.

    `eighty five` -> 85. `two hundred and ten` -> 210. `one thousand fifty` ->
    1050. Written out rather than table-driven because the composition rule is
    the same for every lexicon, and it is the lexicon that is rubric data.
    """
    total = 0
    current = 0
    for value, word in zip(values, words, strict=True):
        scale = scales.get(word)
        if scale is None:
            current += value
        elif scale >= 1000:
            total += max(current, 1) * scale
            current = 0
        else:
            current = max(current, 1) * scale
    return total + current


def parse_spelled(
    text: str,
    *,
    lexicon: Mapping[str, int],
    scales: Mapping[str, int],
    joiners: Sequence[str],
) -> tuple[Figure, ...]:
    """Every spelled number in `text`, composed.

    Hyphens separate words, so `eighty-five` arrives as two lexicon hits and
    composes without a hyphen rule. A joiner (`and`) inside a run does not end
    it; a joiner at the start or end of a run is not part of it.

    **A tens word never follows a unit inside one English cardinal**, so one
    that does starts a new figure. Without that boundary, "gate C, seven
    forty-two last night" composes additively to 49 and "six thirty" to 36 --
    both of which are clock times the corpus states in exactly that form, and
    both of which would then be figures no fact could ever ground. The tens set
    is *derived* from the lexicon's own values rather than declared beside it:
    a second list is a second thing to keep current, and this project has paid
    for that once already.
    """
    folded = {word.casefold(): value for word, value in lexicon.items()}
    folded_scales = {word.casefold(): value for word, value in scales.items()}
    joined = {word.casefold() for word in joiners}
    tens = {
        word
        for word, value in folded.items()
        if word not in folded_scales and 20 <= value <= 90 and value % 10 == 0
    }
    units = {
        word for word, value in folded.items() if word not in folded_scales and 1 <= value <= 9
    }

    figures: list[Figure] = []
    run_words: list[str] = []
    run_values: list[int] = []
    run_start = 0
    run_end = 0

    def flush() -> None:
        if run_values:
            figures.append(
                Figure(
                    surface=text[run_start:run_end],
                    amount=Decimal(_compose(run_values, folded_scales, run_words)),
                    start=run_start,
                    end=run_end,
                    spelled=True,
                )
            )
        run_words.clear()
        run_values.clear()

    for match in _WORD.finditer(text):
        word = match.group(0).casefold()
        if word in folded:
            if run_words and word in tens and run_words[-1] in units:
                flush()
            if not run_values:
                run_start = match.start()
            run_words.append(word)
            run_values.append(folded[word])
            run_end = match.end()
            continue
        if word in joined and run_values:
            continue
        flush()
    flush()
    return tuple(figures)


def parse_digits(text: str, *, pattern: str, strip: Sequence[str]) -> tuple[Figure, ...]:
    """Every digit-written number matching the declared pattern."""
    try:
        compiled = re.compile(pattern)
    except re.error as exc:
        raise ValueTableError(f"digit pattern {pattern!r} does not compile: {exc}") from exc

    figures: list[Figure] = []
    for match in compiled.finditer(text):
        surface = match.group(0)
        cleaned = normalize(surface, strip=strip, fold_case=False)
        try:
            amount = Decimal(cleaned)
        except InvalidOperation:
            continue
        figures.append(
            Figure(
                surface=surface,
                amount=amount,
                start=match.start(),
                end=match.end(),
                spelled=False,
            )
        )
    return tuple(figures)


def figures_in(
    text: str,
    *,
    lexicon: Mapping[str, int],
    scales: Mapping[str, int],
    joiners: Sequence[str],
    digit_pattern: str,
    strip: Sequence[str],
) -> tuple[Figure, ...]:
    """Spelled and digit-written figures together, in position order."""
    found = parse_spelled(text, lexicon=lexicon, scales=scales, joiners=joiners) + parse_digits(
        text, pattern=digit_pattern, strip=strip
    )
    return tuple(sorted(found, key=lambda figure: (figure.start, figure.end)))


def cue_follows(
    text: str, figure: Figure, *, cues: Sequence[str], window_words: int, fold_case: bool
) -> str | None:
    """The cue word that marks this figure's kind, if one is close enough.

    A number with no cue is not a candidate. Without this, "One moment for me"
    contributes the value 1 to a money check -- which is W4's shape: a detector
    matching turns that are not claims, measured only against its true positive
    and never against its false-positive rate in the same call.
    """
    tail = text[figure.end :]
    words = [match.group(0) for match in _WORD.finditer(tail)][:window_words]
    window = " ".join(words)
    if fold_case:
        window = window.casefold()
    for cue in cues:
        needle = cue.casefold() if fold_case else cue
        if re.search(rf"(?<![\w']){re.escape(needle)}(?![\w'])", window):
            return cue
    return None


_NUMERIC_BOUNDARY: Final[str] = r"(?<![\d.,]){needle}(?![\d.,])"


def grounded(
    amount: Decimal,
    surface: str,
    corpus: str,
    *,
    mode: MatchMode,
    corpus_pattern: str,
    strip: Sequence[str],
    fold_case: bool,
) -> bool:
    """Whether the facts support this figure.

    Under `NUMERIC` the corpus is parsed into decimals and compared by value,
    so `22` does not ground against `22.50` and `85` does ground against
    `85.00`. Under `SUBSTRING` the surface is searched for with a
    digit-and-separator boundary -- which is the mode W5 describes and the mode
    the control uses to show the false pass.
    """
    if mode is MatchMode.SUBSTRING:
        needle = re.escape(normalize(surface, strip=strip, fold_case=fold_case))
        haystack = normalize(corpus, strip=strip, fold_case=fold_case)
        return re.search(_NUMERIC_BOUNDARY.format(needle=needle), haystack) is not None

    for figure in parse_digits(corpus, pattern=corpus_pattern, strip=strip):
        if figure.amount == amount:
            return True
    return False


def complete_year(
    month: int,
    day: int,
    reference: dt.date,
    *,
    year_offsets: Sequence[int],
    max_days_away: int,
) -> dt.date | None:
    """A spoken date with no year, resolved against the call's own date.

    W8 is the version that sliced a year out of call metadata unvalidated: an
    unexpected header format yielded a nonsense year, and nothing handled a year
    boundary. Two things are different here. The candidate years are declared
    (`year_offsets`), so a call on 30 December naming 2 January resolves
    forward rather than eleven months back; and a best candidate further than
    `max_days_away` from the call returns `None` rather than a date, so the
    caller reports that it could not resolve instead of grounding against a
    guess.
    """
    candidates: list[dt.date] = []
    for offset in year_offsets:
        try:
            candidates.append(dt.date(reference.year + offset, month, day))
        except ValueError:
            # 29 February in a year that does not have one. Not an error: the
            # other candidate years are still live.
            continue
    if not candidates:
        return None
    best = min(candidates, key=lambda date: abs((date - reference).days))
    if abs((best - reference).days) > max_days_away:
        return None
    return best
