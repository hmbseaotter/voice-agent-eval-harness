"""The value layer, with W5, W6, W7 and W8 each planted rather than argued.

Nine of the ten defects in `specs/taxonomy-coverage.md` Part 3 are *measured*
correctness defects in a prior deterministic tier, and seven produce a false
pass or a false failure on an absolute gate. Four of them are about reading a
figure out of text and comparing it, and this is where they are closed.

A control here runs the defect **and** the fix over one fixture wherever it can,
so the false pass is visible rather than asserted to be absent.

**Closed in this module is not the same as closed in the tier, and the two were
conflated once.** An audit found that the phase-2 verifier ticked W5-W8 with
tests from this file while no rubric entry called the functions they exercise.
`cue_follows` and `grounded` are now called by `available_value_never_spoken`
(D116), joining `parse_spelled` and `figures_in`, which the tier already called,
so those tests stand behind code it runs. `complete_year` is still called by
nothing: no
shipped check completes a year, `taxonomy-coverage.md` gives W8 a *not reached*
disposition rather than a tick, and the verifier's caveat names it. W5 and W6
remain fixture evidence for the tier as well, because the payload figure its
numeric arm reaches is never spoken in any design call.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Final

import pytest

from harness.checks.values import (
    Figure,
    MatchMode,
    ValueTableError,
    complete_year,
    cue_follows,
    figures_in,
    grounded,
    normalize,
    parse_digits,
    parse_spelled,
)

#: The lexicon as a rubric entry declares it. General English rather than
#: fitted to the corpus: a table sized to the design set would pass here and
#: fail silently on the held-out set, which is the failure this corpus exists
#: to make visible (D111).
LEXICON: Final[dict[str, int]] = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    "hundred": 100, "thousand": 1000,
}  # fmt: skip
SCALES: Final[dict[str, int]] = {"hundred": 100, "thousand": 1000}
JOINERS: Final[tuple[str, ...]] = ("and",)

#: A second lexicon, for the entries whose subject is a date. Kept apart from
#: the cardinal table on purpose: `second` is an ordinal *and* a unit of time
#: ("any second now", "one second"), and `first` is an ordinary adverb ("the
#: ZIP code on the account first"). A check that read ordinals while grounding
#: money would find a figure in both.
ORDINALS: Final[dict[str, int]] = LEXICON | {
    "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
    "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10,
    "eleventh": 11, "twelfth": 12, "thirteenth": 13, "fourteenth": 14,
    "fifteenth": 15, "sixteenth": 16, "seventeenth": 17, "eighteenth": 18,
    "nineteenth": 19, "twentieth": 20, "thirtieth": 30,
}  # fmt: skip

#: Digits as they appear in tool results and the context record: `85.00`,
#: `1,050.00`, `14.00`, `00312`.
#: Comma groups must be followed by exactly three digits, so a trailing
#: comma in prose ("billing to 00461, so nothing else...") is not swallowed
#: into the figure. Found by running the parser over the corpus rather than
#: by reading it: the earlier pattern produced the surface `00461,`.
DIGIT_PATTERN: Final[str] = r"(?<![\d.])\d+(?:,\d{3})*(?:\.\d+)?(?!\d)"
STRIP: Final[tuple[str, ...]] = (",", "$")


def _spelled(text: str) -> tuple[Figure, ...]:
    return parse_spelled(text, lexicon=LEXICON, scales=SCALES, joiners=JOINERS)


def _amounts(text: str) -> list[Decimal]:
    return [figure.amount for figure in _spelled(text)]


# --------------------------------------------------------------------------
# Spelled numbers, as the corpus writes them
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("that's the full eighty-five dollars coming back", [85]),
        ("it's ninety-six dollars for the two of you", [96, 2]),
        ("within five business days", [5]),
        ("you have fourteen days from when the tickets were issued", [14]),
        ("the original fifty-two to account for", [52]),
        ("the twenty-two dollars will come back to your card", [22]),
        ("two hundred and ten", [210]),
        ("one thousand fifty", [1050]),
        ("Doors are at seven", [7]),
        ("gate C, seven forty-two last night", [7, 42]),
        ("The app is showing six thirty, though.", [6, 30]),
        ("doors at half seven", [7]),
    ],
)
def test_the_corpus_spells_its_figures_and_they_compose(text: str, expected: list[int]) -> None:
    assert _amounts(text) == [Decimal(value) for value in expected]


def test_a_hyphen_needs_no_rule_of_its_own() -> None:
    """`eighty-five` arrives as two lexicon hits and composes, so the hyphen is
    handled by tokenizing rather than by a case somebody has to remember."""
    assert _amounts("eighty-five") == _amounts("eighty five") == [Decimal(85)]
    figure = _spelled("eighty-five dollars")[0]
    assert figure.surface == "eighty-five", "the evidence would quote a normalization, not speech"
    assert figure.spelled is True


def test_a_joiner_does_not_end_a_run_and_is_not_part_of_one() -> None:
    assert _amounts("two hundred and ten") == [Decimal(210)]
    assert _amounts("and then five") == [Decimal(5)]
    assert _spelled("two hundred and ten")[0].surface == "two hundred and ten"


def test_a_tens_word_after_a_unit_starts_a_new_figure() -> None:
    """The clock-time boundary, and the reason it is not a special case.

    A tens word never follows a unit inside one English cardinal -- there is no
    number said "seven forty". The corpus states clock times in exactly that
    form ("seven forty-two", "six thirty"), and additive composition reads them
    as 49 and 36: figures no fact could ever ground, on turns that are about a
    scan time and an app display.

    The boundary does not touch the legal direction, which is asserted beside
    it: a unit after a tens word is ordinary English and composes.
    """
    assert _amounts("seven forty-two") == [Decimal(7), Decimal(42)]
    assert _amounts("six thirty") == [Decimal(6), Decimal(30)]
    assert [f.surface for f in _spelled("seven forty-two")] == ["seven", "forty-two"]

    assert _amounts("eighty-five") == [Decimal(85)]
    assert _amounts("twenty-two") == [Decimal(22)]
    assert _amounts("one hundred twenty") == [Decimal(120)], (
        "a tens word after a scale is not after a unit, and must still compose"
    )


def test_a_word_that_is_not_a_number_ends_the_run() -> None:
    assert _amounts("two tickets and one charge") == [Decimal(2), Decimal(1)]


def test_the_lexicon_is_data_and_changing_it_changes_the_reading() -> None:
    """The mutation the no-hardcoding rule is about, at the layer that reads.

    `ninety` is 90 here and 19 in the mutated table, and the same sentence
    reads differently. A lexicon compiled into Python would make this test
    unwritable, which is the point of it being rubric data.
    """
    mutated = dict(LEXICON) | {"ninety": 19}
    assert parse_spelled("ninety-six dollars", lexicon=LEXICON, scales=SCALES, joiners=JOINERS)[
        0
    ].amount == Decimal(96)
    assert parse_spelled("ninety-six dollars", lexicon=mutated, scales=SCALES, joiners=JOINERS)[
        0
    ].amount == Decimal(25)


def test_a_digit_read_back_parses_as_digits_and_not_as_a_quantity_by_accident() -> None:
    """ "B-K, nine one four five, T-C" composes to 19, which is meaningless.

    It is not a defect: the cue requirement is what stops it becoming a
    candidate, and that is asserted below. Recorded here so a reader meeting
    the 19 knows it was expected.
    """
    assert _amounts("B-K, nine one four five, T-C") == [Decimal(19)]


# --------------------------------------------------------------------------
# D111: both forms compare by value, and the form itself carries nothing
# --------------------------------------------------------------------------


def test_a_spoken_figure_grounds_against_the_digits_in_the_facts() -> None:
    """The fact says `85.00` and the speech says "eighty-five dollars".

    This is the whole reason the value layer exists. A grounding check built on
    digit patterns would find nothing in speech across the design set: agent
    turns carry three bare integers in fifteen calls.
    """
    figure = _spelled("the full eighty-five dollars coming back")[0]
    assert grounded(
        figure.amount,
        figure.surface,
        "ticket_price_total := 85.00\nrefund_band := full",
        mode=MatchMode.NUMERIC,
        corpus_pattern=DIGIT_PATTERN,
        strip=STRIP,
        fold_case=True,
    )


def test_a_spoken_figure_the_facts_do_not_carry_is_not_grounded() -> None:
    """The control. The assertion above is that something was found, and a
    matcher returning True for everything would satisfy it."""
    figure = _spelled("the full eighty-five dollars coming back")[0]
    assert not grounded(
        figure.amount,
        figure.surface,
        "ticket_price_total := 96.00",
        mode=MatchMode.NUMERIC,
        corpus_pattern=DIGIT_PATTERN,
        strip=STRIP,
        fold_case=True,
    )


# --------------------------------------------------------------------------
# W5: the decimal point is a word boundary
# --------------------------------------------------------------------------


def test_w5_a_spoken_integer_does_not_ground_against_a_longer_payload_figure() -> None:
    """Spoken "twenty-two dollars" against a payload of `22.50`.

    The reference implementation matched on word boundaries, and the character
    after `22` in `22.50` is a `.` -- which *is* a word boundary. So the spoken
    figure grounded against a payload figure that merely shared its integer
    part, and the false pass landed on an absolute gate.

    Both modes run over one fixture, so the defect is visible beside the fix
    rather than asserted to be absent.
    """
    figure = _spelled("the twenty-two dollars will come back")[0]
    assert figure.amount == Decimal(22)
    corpus = 'issue_refund(booking="BK-7724-RP", amount="22.50")'

    assert not grounded(
        figure.amount,
        "22",
        corpus,
        mode=MatchMode.NUMERIC,
        corpus_pattern=DIGIT_PATTERN,
        strip=STRIP,
        fold_case=True,
    ), "22 grounded against 22.50 under numeric comparison, which is W5 unfixed"

    assert (
        grounded(
            figure.amount,
            "22",
            corpus,
            mode=MatchMode.SUBSTRING,
            corpus_pattern=DIGIT_PATTERN,
            strip=STRIP,
            fold_case=True,
        )
        is False
    ), "the substring boundary should also block this; see the next test"


def test_w5_the_word_boundary_is_the_thing_that_fails() -> None:
    """The defect reproduced directly, so the boundary choice is evidenced.

    `\\b22\\b` finds `22` inside `22.50`; the digit-and-separator boundary this
    module uses does not. Asserted against `re` rather than through the module,
    because the claim is about what the *old* boundary did.
    """
    import re

    assert re.search(r"\b22\b", "amount=22.50"), (
        "the word boundary no longer matches inside 22.50, so W5's mechanism has "
        "changed and this control is describing something that cannot happen"
    )
    assert not re.search(r"(?<![\d.,])22(?![\d.,])", "amount=22.50")


def test_w5_an_exact_figure_still_grounds_under_both_modes() -> None:
    """Scoped: the boundary refuses a partial match, not every match."""
    corpus = 'issue_refund(amount="22.50")'
    for mode in (MatchMode.NUMERIC, MatchMode.SUBSTRING):
        assert grounded(
            Decimal("22.50"),
            "22.50",
            corpus,
            mode=mode,
            corpus_pattern=DIGIT_PATTERN,
            strip=STRIP,
            fold_case=True,
        ), f"an exact figure failed to ground under {mode.value}"


# --------------------------------------------------------------------------
# W6: normalization applies to both sides
# --------------------------------------------------------------------------


def test_w6_a_thousands_separator_in_the_payload_is_stripped_too() -> None:
    """One-sided normalization is what W6 measured: separators stripped from
    the spoken value and never from the payload, so every figure above nine
    hundred and ninety-nine failed against a payload that carried one."""
    corpus = 'issue_refund(amount="1,050.00")'
    assert grounded(
        Decimal(1050),
        "one thousand fifty",
        corpus,
        mode=MatchMode.NUMERIC,
        corpus_pattern=DIGIT_PATTERN,
        strip=STRIP,
        fold_case=True,
    )
    assert not grounded(
        Decimal(1050),
        "one thousand fifty",
        corpus,
        mode=MatchMode.NUMERIC,
        corpus_pattern=DIGIT_PATTERN,
        strip=(),
        fold_case=True,
    ), "with no separator stripped the payload no longer parses, which is the one-sided case"


def test_w6_normalize_is_one_function_used_by_both_sides() -> None:
    assert normalize("1,050.00", strip=STRIP, fold_case=False) == "1050.00"
    assert normalize("$85.00", strip=STRIP, fold_case=False) == "85.00"
    assert normalize("APRIL", strip=(), fold_case=True) == "april"


# --------------------------------------------------------------------------
# W7: case folding is declared, and flipping it changes behavior
# --------------------------------------------------------------------------


def test_w7_a_cue_is_found_case_insensitively_when_the_entry_says_so() -> None:
    """W7 was date matching that was case-sensitive while quantity matching was
    not, so a lower-cased month silently disabled the date arm -- a false
    *pass* on the arm's headline failure mode. Folding is declared, and the
    control flips it over one fixture."""
    figure = _spelled("that's the full eighty-five dollars coming back")[0]
    text = "that's the full eighty-five Dollars coming back"

    assert cue_follows(text, figure, cues=("dollars",), window_words=2, fold_case=True) == "dollars"
    assert cue_follows(text, figure, cues=("dollars",), window_words=2, fold_case=False) is None


# --------------------------------------------------------------------------
# The cue requirement: a number is not a claim
# --------------------------------------------------------------------------


def test_a_number_with_no_cue_is_not_a_candidate() -> None:
    """ "One moment for me" contributes the value 1 to any check that reads
    spelled numbers. W4 is a claim detector matching turns that are not claims,
    validated against its true positive and never against its false-positive
    rate in the same call."""
    text = "One moment for me."
    figure = _spelled(text)[0]
    assert figure.amount == Decimal(1)
    assert cue_follows(text, figure, cues=("dollars",), window_words=3, fold_case=True) is None


def test_a_read_back_carries_no_money_cue() -> None:
    text = "Let me read that back before I go any further - B-K, nine one four five, T-C."
    figure = _spelled(text)[0]
    assert cue_follows(text, figure, cues=("dollars",), window_words=3, fold_case=True) is None


def test_a_cue_beyond_the_declared_window_is_not_found() -> None:
    """The window is a parameter, and it bounds a false positive rather than
    only being present."""
    text = "eighty-five of the very best premium dollars"
    figure = _spelled(text)[0]
    assert cue_follows(text, figure, cues=("dollars",), window_words=2, fold_case=True) is None
    assert cue_follows(text, figure, cues=("dollars",), window_words=6, fold_case=True) == "dollars"


def test_a_cue_matches_a_whole_word_and_not_a_fragment() -> None:
    text = "fourteen dollarsomething"
    figure = _spelled(text)[0]
    assert cue_follows(text, figure, cues=("dollars",), window_words=2, fold_case=True) is None


# --------------------------------------------------------------------------
# W8: completing a year, with validation and a boundary
# --------------------------------------------------------------------------


def test_w8_a_december_call_naming_a_january_date_resolves_forward() -> None:
    """The boundary W8 says nothing handled.

    A year sliced from call metadata gives 2 January *2027* for a call on 30
    December 2027 -- eleven months in the past, for a date the caller is
    plainly talking about as upcoming.
    """
    resolved = complete_year(
        1, 2, dt.date(2027, 12, 30), year_offsets=(0, 1, -1), max_days_away=400
    )
    assert resolved == dt.date(2028, 1, 2)


def test_w8_a_january_call_naming_a_december_date_resolves_backward() -> None:
    resolved = complete_year(
        12, 28, dt.date(2028, 1, 3), year_offsets=(0, 1, -1), max_days_away=400
    )
    assert resolved == dt.date(2027, 12, 28)


def test_w8_a_date_too_far_from_the_call_is_refused_rather_than_guessed() -> None:
    """The validation half. An unresolvable date returns `None` so the caller
    can report `unevaluable`, rather than grounding against a guess."""
    assert (
        complete_year(1, 2, dt.date(2027, 6, 15), year_offsets=(0, 1, -1), max_days_away=60) is None
    )


def test_w8_a_leap_day_skips_the_years_that_do_not_have_one() -> None:
    """An invalid candidate is skipped rather than aborting: the other declared
    offsets are still live, and 29 February exists in one year of four."""
    assert complete_year(
        2, 29, dt.date(2027, 3, 1), year_offsets=(0, 1, -1), max_days_away=400
    ) == dt.date(2028, 2, 29)
    assert (
        complete_year(2, 29, dt.date(2027, 3, 1), year_offsets=(0,), max_days_away=400) is None
    ), "with no valid candidate year the result is None rather than an exception"


def test_w8_the_offsets_are_data_and_narrowing_them_changes_the_answer() -> None:
    assert complete_year(
        1, 2, dt.date(2027, 12, 30), year_offsets=(0,), max_days_away=400
    ) == dt.date(2027, 1, 2)


# --------------------------------------------------------------------------
# Digit parsing and the combined reader
# --------------------------------------------------------------------------


def test_digits_parse_with_their_separators_stripped() -> None:
    figures = parse_digits('amount="1,050.00" fee="12.50"', pattern=DIGIT_PATTERN, strip=STRIP)
    assert [figure.amount for figure in figures] == [Decimal("1050.00"), Decimal("12.50")]
    assert figures[0].surface == "1,050.00"
    assert figures[0].spelled is False


def test_a_pattern_match_that_is_not_a_number_is_skipped_rather_than_raising() -> None:
    """Malformed *text* is data. Only a malformed table is an error."""
    assert parse_digits("1,2,3,", pattern=r"[\d,]+", strip=()) == ()


def test_a_pattern_that_does_not_compile_is_refused_by_name() -> None:
    with pytest.raises(ValueTableError, match="does not compile"):
        parse_digits("anything", pattern="(unclosed", strip=())


def test_the_combined_reader_returns_both_forms_in_position_order() -> None:
    figures = figures_in(
        "the card ending 4417 and eighty-five dollars",
        lexicon=LEXICON,
        scales=SCALES,
        joiners=JOINERS,
        digit_pattern=DIGIT_PATTERN,
        strip=STRIP,
    )
    assert [(f.surface, f.spelled) for f in figures] == [
        ("4417", False),
        ("eighty-five", True),
    ]
    assert [f.start for f in figures] == sorted(f.start for f in figures)


def test_a_trailing_comma_in_prose_is_not_part_of_the_figure() -> None:
    """Found by running the parser over the corpus, not by reading it.

    CALL-18 says "the Visa ending 8820, billing to 00461, so nothing else
    needs doing". The first pattern matched `00461,` and, once the separator
    was stripped, read it as the decimal 461 -- a surface a reader cannot find
    in the transcript and a value that is not the ZIP.
    """
    figures = parse_digits(
        "the Visa ending 8820, billing to 00461, so nothing else",
        pattern=DIGIT_PATTERN,
        strip=STRIP,
    )
    assert [figure.surface for figure in figures] == ["8820", "00461"]
    assert (
        parse_digits('amount="1,050.00"', pattern=DIGIT_PATTERN, strip=STRIP)[0].surface
        == "1,050.00"
    ), "the fix must not stop a real thousands separator parsing"


def test_an_identifier_is_compared_by_surface_because_leading_zeros_count() -> None:
    """`00461` read as a decimal is 461, which is a ZIP that cannot exist.

    Both match modes are correct, for different kinds of figure. Quantities go
    through NUMERIC, where 85 and 85.00 are the same amount; identifiers go
    through SUBSTRING, where the surface is the token.
    """
    corpus = "context - billing_zip := 00461"
    assert grounded(
        Decimal(461),
        "00461",
        corpus,
        mode=MatchMode.SUBSTRING,
        corpus_pattern=DIGIT_PATTERN,
        strip=STRIP,
        fold_case=True,
    )
    assert not grounded(
        Decimal(461),
        "461",
        corpus,
        mode=MatchMode.SUBSTRING,
        corpus_pattern=DIGIT_PATTERN,
        strip=STRIP,
        fold_case=True,
    ), "a ZIP with its leading zeros dropped grounded against the real one"
    assert grounded(
        Decimal(461),
        "461",
        corpus,
        mode=MatchMode.NUMERIC,
        corpus_pattern=DIGIT_PATTERN,
        strip=STRIP,
        fold_case=True,
    ), "numeric comparison does lose the leading zeros, which is why identifiers do not use it"


def test_an_ordinal_date_needs_the_ordinal_lexicon_to_read_correctly() -> None:
    """ "the twenty-fourth of April" is 24, and the cardinal table reads it as 20.

    F-82 is a finding about exactly this phrase -- the agent gave the
    rescheduled date as the twenty-fourth when the venue-local date is the
    twenty-third -- so an entry whose subject is a date declares the ordinal
    table, and one whose subject is money does not.
    """
    cardinal_only = parse_spelled(
        "it's moved to the twenty-fourth of April", lexicon=LEXICON, scales=SCALES, joiners=JOINERS
    )
    assert [f.amount for f in cardinal_only] == [Decimal(20)], (
        "the cardinal table no longer stops at `twenty`, so this contrast is stale"
    )

    with_ordinals = parse_spelled(
        "it's moved to the twenty-fourth of April",
        lexicon=ORDINALS,
        scales=SCALES,
        joiners=JOINERS,
    )
    assert [f.amount for f in with_ordinals] == [Decimal(24)]
    assert with_ordinals[0].surface == "twenty-fourth"

    assert [
        f.amount
        for f in parse_spelled(
            "on the twenty-first", lexicon=ORDINALS, scales=SCALES, joiners=JOINERS
        )
    ] == [Decimal(21)]


def test_the_ordinal_table_is_kept_apart_because_two_of_its_words_are_not_numbers() -> None:
    """`second` is a unit of time and `first` is an adverb, in this corpus.

    Both appear in agent speech meaning neither one nor two, so a money check
    reading the ordinal table would find a figure in "any second now" and in
    "the ZIP code on the account first". The cue requirement is the second
    guard; keeping the tables apart is the first.
    """
    for text in ("It should be with you any second now.", "Can I get the ZIP code first?"):
        assert parse_spelled(text, lexicon=LEXICON, scales=SCALES, joiners=JOINERS) == ()
        assert parse_spelled(text, lexicon=ORDINALS, scales=SCALES, joiners=JOINERS) != ()
