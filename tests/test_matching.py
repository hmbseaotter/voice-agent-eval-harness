"""The boundary that keeps a declared name out of a longer one.

Two shapes, one rule, and the reason each is here is that neither defect fires
over the design set: routing every signal list and every field key through
`harness.checks.matching` moves no verdict of 555. A change that moves nothing
is proven by nothing, so every function below is asserted against the naive
implementation it replaced -- the claim is about what a bare substring did, so
the control has to do the bare substring.
"""

from __future__ import annotations

import re
from typing import Final

import pytest

from harness.checks import matching

MONTHS: Final[tuple[str, ...]] = (
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
)
"""`A-deadline-never-resolved`'s resolution signals, copied deliberately: a
fixture that read the rubric would pass if the rubric's list were emptied."""


# --------------------------------------------------------------------------
# Signal lists
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "signal"),
    [
        ("The day before the show, maybe the fifth.", "may"),
        ("There's a marching band before the doors open.", "march"),
    ],
)
def test_a_month_name_does_not_match_inside_a_longer_word(text: str, signal: str) -> None:
    """The defect, stated as the thing that goes wrong.

    `A-deadline-never-resolved` treats a turn as resolving the deadline when it
    carries a month name. Under substring matching "maybe" resolves it, and the
    one call the entry exists to fail passes.
    """
    assert signal in text.casefold(), "the control no longer contains the fragment it plants"
    assert matching.signal_in(text, MONTHS) is None


def test_the_homograph_half_is_not_closed_by_a_boundary() -> None:
    """The recorded residue, asserted so nobody infers it was handled.

    "You may hear from the promoter" carries `may` as a whole word. A boundary
    separates a fragment from a word; it cannot separate two words that are
    spelled the same. Case would separate them here and D111 forbids asking:
    the form speech was written down in carries nothing, and the held-out set
    was authored by hand to the same conventions. Closing this needs the month
    required near a date-shaped token, which is a change to what the entry
    declares.
    """
    assert matching.signal_in("You may hear from the promoter.", MONTHS) == "may"


def test_the_substring_match_is_the_thing_that_fails() -> None:
    """The other half of the same claim: naive matching really does fire here.

    Asserted against `in` directly rather than through this module, because the
    claim is about what the replaced implementation did.
    """
    text = "The day before the show, maybe the fifth."
    naive = next((month for month in MONTHS if month in text.casefold()), None)
    assert naive == "may", "the fragment no longer collides, so this control proves nothing"
    assert matching.signal_in(text, MONTHS) is None


def test_a_genuine_month_name_still_matches() -> None:
    """CALL-10 and CALL-12 use both colliding words as real months in agent
    speech, so the boundary has to keep them."""
    assert matching.signal_in("I have the purchase down as March fourth.", MONTHS) == "march"
    assert matching.signal_in("That's one ticket for Understory on May ninth.", MONTHS) == "may"


def test_a_multi_word_phrase_matches_across_its_own_spaces() -> None:
    """Signal lists are mostly phrases, and a boundary applies to the phrase,
    not to each word in it."""
    assert matching.signal_in("The day before the show.", ["the day before the show"]) is not None
    assert matching.signal_in("bear with me a moment", ["bear with me"]) == "bear with me"


def test_a_signal_is_returned_in_the_spelling_the_entry_used() -> None:
    """Evidence quotes the rubric, not a normalization of it."""
    assert matching.signal_in("purchased in MARCH", ["March"]) == "March"


def test_case_folding_is_declared_and_turning_it_off_changes_the_answer() -> None:
    assert matching.signal_in("in March", ["march"], True) == "march"
    assert matching.signal_in("in March", ["march"], False) is None


def test_an_apostrophe_is_a_word_character_for_this_boundary() -> None:
    """`all set` must not match inside "isn't all settled", and a signal that
    is itself a contraction must still match."""
    assert matching.signal_in("that isn't coming from us", ["isn't coming from us"]) is not None
    assert matching.signal_in("you're all settled", ["all set"]) is None


# --------------------------------------------------------------------------
# Field keys
# --------------------------------------------------------------------------

COLLISIONS: Final[tuple[tuple[str, str], ...]] = (
    ("event", "target_event"),
    ("at", "closed_at"),
    ("at", "rescheduled_at"),
    ("at", "scanned_at"),
    ("band", "price_band"),
    ("note", "internal_note"),
)
"""Every colliding pair `corpus/entities.md` declares today. No rubric key is
currently the short member of one, which is what made this latent."""


@pytest.mark.parametrize(("short", "long"), COLLISIONS)
def test_a_tool_argument_does_not_match_inside_a_longer_argument_name(
    short: str, long: str
) -> None:
    arguments = f'{long}="Understory"'
    assert re.search(rf'{re.escape(short)}="([^"]*)"', arguments), (
        "the pair no longer collides under the naive pattern, so this proves nothing"
    )
    assert matching.argument(arguments, short) is None
    assert matching.argument(arguments, long) == "Understory"


@pytest.mark.parametrize(("short", "long"), COLLISIONS)
def test_a_detail_key_does_not_match_inside_a_longer_key(short: str, long: str) -> None:
    detail = f"{long}=2026-04-23; status=ok"
    assert re.search(rf'{re.escape(short)}="?([^;"]*)"?', detail), (
        "the pair no longer collides under the naive pattern, so this proves nothing"
    )
    assert matching.field(detail, short) is None
    assert matching.field(detail, long) == "2026-04-23"


@pytest.mark.parametrize(("short", "long"), COLLISIONS)
def test_the_containment_tests_carry_the_same_boundary(short: str, long: str) -> None:
    """`carries_argument` and `carries_field` answer "is this key present at
    all", and a boundary on the extractor with none on the presence test is a
    guard narrower than its rule."""
    assert f"{short}=" in f"{long}=x", "the pair no longer collides"
    assert matching.carries_argument(f'{long}="x"', short) is False
    assert matching.carries_argument(f'{long}="x"', long) is True
    assert matching.carries_field(f"{long}=x", short) is False
    assert matching.carries_field(f"{long}=x", long) is True


@pytest.mark.parametrize(("short", "long"), COLLISIONS)
def test_every_value_of_a_key_carries_the_boundary_too(short: str, long: str) -> None:
    detail = f"{long}=first; {long}=second"
    assert matching.values(detail, short) == []
    assert matching.values(detail, long) == ["first", "second"]


def test_a_key_at_the_start_and_after_every_separator_still_matches() -> None:
    """The boundary refuses a preceding word character and nothing else, so a
    key opening the string or following `(`, `;`, `,` or a space is found."""
    assert matching.argument('event="EV-1"', "event") == "EV-1"
    assert matching.argument('booking="B",event="EV-1"', "event") == "EV-1"
    assert matching.field("event=EV-1", "event") == "EV-1"
    assert matching.field("status=ok; event=EV-1", "event") == "EV-1"
    assert matching.values("status=ok, event=EV-1", "event") == ["EV-1"]


def test_the_two_value_grammars_differ_where_they_are_meant_to() -> None:
    """`field` reads a value that may contain spaces; `values` reads a token.

    Asserted so the difference is a decision somebody can find rather than a
    surprise in a held-out call. `internal_note=do not disclose` is why `field`
    crosses a space: read as a token it would be the word "do".
    """
    detail = "note=one two; status=ok"
    assert matching.field(detail, "note") == "one two"
    assert matching.values(detail, "note") == ["one"]


def test_a_thousands_separator_stays_inside_the_value() -> None:
    """The half of that difference which was not deliberate.

    `values` also stopped at a comma, so `difference_due=1,250.00` came back as
    `1` -- not a shortened value but a different one, on the money key, in the
    check whose subject is whether a money figure was spoken.
    """
    detail = "price difference not accepted by holder; difference_due=1,250.00"
    assert matching.values(detail, "difference_due") == ["1,250.00"]
    assert matching.field(detail, "difference_due") == "1,250.00", (
        "the two grammars disagree on this value again"
    )

    naive = re.findall(r"difference_due=([^;,\s]+)", detail)
    assert naive == ["1"], "the old grammar no longer truncates, so this control proves nothing"


def test_a_comma_between_two_pairs_still_ends_the_value() -> None:
    """Crossing a comma is not the fix; ending on one is what was wrong.

    CALL-08's refusal states two door times in one prose sentence separated by a
    comma, and reading past it would make the first value swallow the second.
    """
    detail = "event record holds conflicting door_time values (booking=19:00:00Z, event=19:30:00Z)"
    assert matching.values(detail, "booking") == ["19:00:00Z"]
    assert matching.values(detail, "event") == ["19:30:00Z)"]


def test_a_repeated_key_returns_every_occurrence_whole() -> None:
    """The reason `values` exists at all: a detail may state a key more than
    once, and each occurrence is a candidate."""
    detail = "difference_due=1,250.00; note=x; difference_due=1,250.00"
    assert matching.values(detail, "difference_due") == ["1,250.00", "1,250.00"]
