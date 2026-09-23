r"""How a declared name matches text: at a boundary, never inside a longer one.

Two shapes share one rule, which is why they share one module.

**A signal list** is a phrase list from a rubric entry, matched against speech.
Matched as a bare substring, `may` matches inside "maybe" and `march` inside
"marching" -- so `A-deadline-never-resolved`, whose resolution signals are the
twelve month names, would read a hedge as a resolved deadline and pass a call
it exists to fail. Both words are live vocabulary here: CALL-10 and CALL-12 use
them as genuine month names in agent speech.

**What this does not close, stated because a boundary looks like it should.**
"You may hear from the promoter" carries `may` as a whole word. It is a
homograph of the month, not a fragment of a longer one, and no boundary
separates them -- `test_the_homograph_half_is_not_closed_by_a_boundary` holds
that as a recorded residue rather than leaving a reader to infer it was
handled. Case would separate them in this corpus and must not be asked to:
D111 refuses to key on how speech was written down, because that is a property
of transcription and the held-out set was authored by hand. Separating them
needs what `spoken_local_date_wrong` already does -- require the month near a
date-shaped token -- which is a change to what the entry declares.

**A field key** is a tool argument or a tool-result detail key, matched against
`name="value"` or `key=value`. The trailing side was already anchored by the
`=`, so `event` never matched `event_id=`; the *leading* side was open, so
`event` matched inside `target_event=`. `corpus/entities.md` declares four
colliding pairs today -- `event`/`target_event`, `at`/`closed_at` (and
`rescheduled_at`, `scanned_at`), `band`/`price_band`, `note`/`internal_note` --
and no rubric key is currently the short member of one, which is what made this
latent rather than firing.

**Neither defect fires over the design set**, measured both ways: routing every
signal list and every field key through this module moves no verdict of 555.
That is why each function here has a planted control -- a guard whose only
evidence is that it has never fired has been proven against nothing.

**Two grammars read `key=value`, and the difference is now deliberate.** `field`
stops a value at `;` or a quote, so it reads values containing spaces --
`internal_note=do not disclose` is one value, not one word. `values` reads a
token, so it can return every occurrence of a repeated key without swallowing
the pair after it.

What was *not* deliberate: `values` also stopped at a comma, so a thousands
separator truncated the value. `difference_due=1,250.00` came back as `1`, which
is not a shortened value but a different one -- and it is the *money* key, in the
check whose subject is whether a money figure was spoken. Corrected by refusing
to end a value on a comma rather than by refusing to cross one, which keeps
`booking=19:00:00Z, event=19:30:00Z` two values and makes `1,250.00` one.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Final

_BOUNDARY: Final[str] = r"(?<![\w'])"
"""No word character and no apostrophe immediately before the match.

The apostrophe is in the class so that `all set` cannot match inside a
contraction's tail, and it is the same boundary `values.cue_follows` uses --
one idiom rather than two.
"""

_KEY_BOUNDARY: Final[str] = r"(?<!\w)"
"""No word character immediately before a field key.

Narrower than `_BOUNDARY` on purpose: a key is an identifier, and `_` is a word
character, so `price_band` shields `band` without an apostrophe rule.
"""


def signal_in(text: str, signals: Iterable[object], fold_case: bool = True) -> str | None:
    """The first declared signal this text carries, as declared, or `None`.

    Returns the signal in the spelling the rubric used, not the folded one, so
    evidence quotes the entry rather than a normalization.
    """
    haystack = text.casefold() if fold_case else text
    for signal in signals:
        needle = str(signal).casefold() if fold_case else str(signal)
        if re.search(rf"{_BOUNDARY}{re.escape(needle)}(?![\w'])", haystack):
            return str(signal)
    return None


def argument(arguments: str, name: str) -> str | None:
    """The value of `name="..."` in a tool call's argument string."""
    match = re.search(rf'{_KEY_BOUNDARY}{re.escape(name)}="([^"]*)"', arguments)
    return match.group(1) if match else None


def carries_argument(arguments: str, name: str) -> bool:
    """Whether a tool call passes `name=` at all, whatever its value."""
    return re.search(rf"{_KEY_BOUNDARY}{re.escape(name)}=", arguments) is not None


def field(detail: str, key: str) -> str | None:
    """The value of `key=value` in a tool result's detail, stripped."""
    match = re.search(rf'{_KEY_BOUNDARY}{re.escape(key)}="?([^;"]*)"?', detail)
    return match.group(1).strip() if match else None


def values(detail: str, key: str) -> list[str]:
    """Every `key=value` in one detail string, in position order.

    A value runs to the next `;` or space and **never ends on a comma**, so a
    thousands separator stays inside the figure while a comma separating two
    pairs stays outside it.
    """
    return [
        match.group(1)
        for match in re.finditer(rf"{_KEY_BOUNDARY}{re.escape(key)}=([^;\s]*[^;\s,])", detail)
    ]


def carries_field(detail: str, key: str) -> bool:
    """Whether a result's detail states `key=` at all, whatever its value."""
    return re.search(rf"{_KEY_BOUNDARY}{re.escape(key)}=", detail) is not None
