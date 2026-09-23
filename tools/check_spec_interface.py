#!/usr/bin/env python3
"""Check that both sides of the findings interface still agree about it.

WHY THIS EXISTS (D15, comparative-judgment; D22, this repo)
----------------------------------------------------------
The harness and the comparative-judgment tool describe one interface across
several documents in two repositories. Four defects have come from that split:

  1. The harness named no findings format while the tool's spec had fixed one.
  2. The tool did not know about the `question` tier, so it would have rated
     non-defects and let them into the anchor set.
  3. The tool's assumptions still asserted the harness "currently names no
     format" after the harness had named one and pushed it.
  4. The same assertion survived a second time in the tool's D5 -- in a
     decision record, which is a file this script was never pointed at.

Each was individually well-formed prose that read as entirely normal. No spec
linter can see any of them, because none of them is wrong *within* one file.
At the third instance of a shape the deliverable is the detector rather than
another repair -- so this is it.

Instance four is why the arity changed. The original version took exactly two
files: one spec per side. That made it a detector whose coverage was narrower
than the rule it enforces -- the rule is "these two projects agree about this
interface", and the interface is asserted in both specs, both decision records
and both build prompts. It was found by a human widening the universe by one
file per side, by hand, which is precisely the labor this script exists to
replace. It now takes a list per side.

A fifth class it now covers: the severity file's FIELD SET. Both documents
described that file, and nothing checked that they described the same one. The
harness spec named three of the five provenance fields the tool emits, and the
disagreement was invisible until someone read both. That agreement had been
holding by the attentiveness of two readers, which is the exact condition this
script was written to stop relying on.

A sixth: A NAME COUNTED WHERE IT IS NOT A FIELD (P4-17, D178). This script
matched a backticked name anywhere in either side's documents, and the tool's
specification once named `cuts` only as a subcommand, in two acceptance
criteria -- so it reported agreement on a field the tool's field list did not
carry, and a field renamed on the producing side would have gone on agreeing
for as long as a command of the old name existed. A name now counts only where
it is listed. Each side's specification -- the first file named for that side
-- carries one sentence enumerating each list, found by the phrase that opens
it and bounded by that sentence's end, and the set it names must be exactly the
set below. A list sentence missing, or its opening phrase stated twice, is a
disagreement rather than a pass: a detector that goes quiet when the sentence it
reads is reworded is the fail-open this script exists to remove.

The rule it enforces is deliberately narrow: it checks agreement on facts both
sides assert, not that either is correct. It is a drift detector, not a
reviewer.

USAGE
-----
    check_spec_interface.py HARNESS_FILE[,HARNESS_FILE...] TOOL_FILE[,TOOL_FILE...]

Each side is a comma-separated list, its specification first. The lists are read
from the specification alone; every file on a side is concatenated for the
ownership claims and the stale cross-claims, so a decision record repeating a
stale assertion still fails.

    # the two specs, as before
    check_spec_interface.py specs/harness.md ../tool/specs/tool.md

    # every document that describes the interface
    check_spec_interface.py \\
        specs/harness.md,specs/harness.decisions.md,specs/harness.build-prompt.md \\
        ../tool/specs/tool.md,../tool/specs/tool.decisions.md

Exits 0 when the two sides agree, 1 on any disagreement, 2 on a usage error.
Run it before any commit that touches either side's interface description; the
CI workflow runs it too (D28).
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from harness.core.findings import REQUIRED_KEYS

# The six keys of a findings entry, settled by harness D22 and mirrored by the
# tool's D10. Both sides must name every one of them.
#: Findings keys the harness enforces but the severity tool never reads.
#:
#: The tool compares one finding against another to place it in a severity
#: order. Which call a finding came from, and whose defect it is, change nothing
#: about that comparison -- so these two do not cross the repository boundary
#: and requiring the tool's specification to name them would be requiring it to
#: document a field it has no use for.
#:
#: Declared, not implied. This list existed only as the *difference* between two
#: hand-maintained tuples, and an independent audit read that difference as the
#: scanner having drifted two keys behind the code. It had not -- but nothing in
#: either file said so, and a subset indistinguishable from a stale copy is a
#: defect in the documentation of the subset.
HARNESS_ONLY_KEYS: Final[tuple[str, ...]] = ("call_ref", "owner")

#: The findings keys both sides must name. Derived from the loader's own list
#: rather than retyped, so adding a key to `REQUIRED_KEYS` forces a decision
#: here -- shared, or harness-only -- instead of silently widening the gap.
FINDINGS_KEYS: Final[tuple[str, ...]] = tuple(
    key for key in REQUIRED_KEYS if key not in HARNESS_ONLY_KEYS
)

# The severity file's provenance fields. The tool writes these; the harness
# reads them. Both sides must name every one, so that a field added or renamed
# in the producing tool cannot pass unnoticed by the consumer.
#
# `severities` and `unplaced` are the payload; the rest is provenance. All are
# listed because a consumer that silently stops seeing `unplaced` would report
# bands for findings nobody compared, which is the failure that field exists to
# prevent. `cuts` joined at schema 3 -- how each band boundary was drawn, which
# the harness re-derives from the rows rather than trusting (D156 here; D34 in
# the tool). The fields inside a cut are not listed: the tool's specification
# does not name them, so the loader requires them instead.
SEVERITY_FIELDS: Final[tuple[str, ...]] = (
    "schema_version",
    "anchor_set_version",
    "comparison_log_hash",
    "run_id",
    "calibration",
    "severities",
    "unplaced",
    "cuts",
)

# What every row inside `severities` carries from schema 2. **Separate from the
# tuple above, because the two are different populations**: those are top-level
# keys, these are per-row. They were folded into one list when the row fields
# arrived and `test_the_scanner_and_the_library_agree_about_severity_fields`
# refused it, correctly -- the library's tuple is what the loader requires at
# the top level, and a `content_hash` demanded beside `run_id` would reject
# every file the producing tool writes.
#
# Checked the same way and for the same reason: a field renamed on the producing
# side is otherwise invisible on this one. They are what a band was placed on --
# the text, and how decisively (D140, D144 here; D33 in the tool).
SEVERITY_ROW_FIELDS: Final[tuple[str, ...]] = (
    "id",
    "severity",
    "theta",
    "content_hash",
    "appearances",
    "informative",
)


@dataclass(frozen=True, slots=True)
class ListSentence:
    """Where one side's specification enumerates one list.

    `opens` is the phrase that opens the list and must occur exactly once in the
    specification. The list runs from there to `closes` when one is given -- for
    a sentence that goes on to enumerate something else -- and otherwise to the
    end of its sentence: the first full stop followed by whitespace, or the end of
    the line, since each of these sentences sits in one bullet.
    """

    opens: str
    closes: str | None = None


#: The three lists, each with what it must hold and how it is named in a
#: disagreement. The harness's findings list also names the harness-only keys,
#: which are set aside before comparing, as they always were.
LISTS: Final[tuple[tuple[str, str, tuple[str, ...]], ...]] = (
    ("findings keys", "findings key", FINDINGS_KEYS),
    ("severity file fields", "severity file field", SEVERITY_FIELDS),
    ("severity row fields", "severity row field", SEVERITY_ROW_FIELDS),
)

#: The harness specification's list sentences: the findings requirement, and the
#: in-scope bullet that names the severity file's fields and then its row fields.
HARNESS_SENTENCES: Final[dict[str, ListSentence]] = {
    "findings keys": ListSentence("SHALL [P1] read the findings document as YAML,"),
    "severity file fields": ListSentence("carrying, at minimum,", closes="and **on every row**"),
    "severity row fields": ListSentence("and **on every row**"),
}

#: The tool specification's: its in-scope reader bullet, and the two severity-file
#: requirements, the first of which says its list "is enumerated here rather than
#: described, because the consuming harness reads provenance from it".
TOOL_SENTENCES: Final[dict[str, ListSentence]] = {
    "findings keys": ListSentence(
        "**YAML findings reader**", closes="and a **severity-file writer**"
    ),
    "severity file fields": ListSentence("SHALL record exactly these top-level fields:"),
    "severity row fields": ListSentence("SHALL record on **every row**"),
}

_NAME = re.compile(r"`([^`\n]+)`")

# Claims each side must make about severity ownership. Stored as (label, regex)
# so a failure names the missing idea rather than a pattern.
SEVERITY_CLAIMS: Final[tuple[tuple[str, str], ...]] = (
    ("severity is keyed by finding id", r"severity[^.]{0,80}\bid\b"),
    ("severity is a separate file", r"separate\s+severity\s+file|severity[- ]file\s+writer"),
)

# Assertions one side makes ABOUT the other that go stale silently. Each is a
# regex that must NOT appear, with the reason it is now false.
STALE_CROSS_CLAIMS: Final[tuple[tuple[str, str], ...]] = (
    (
        r"harness[^.]{0,60}names?\s+no\s+format",
        "the harness spec names YAML (its D22); this assertion is stale",
    ),
    # A second pattern, `format adapter is needed`, was tried and removed. It
    # matched inside the sentence that FIXED the defect -- "No format adapter
    # is needed" -- because it had no notion of negation. A detector that
    # fires on the text resolving the problem it detects is worse than a
    # narrower one: it trains the reader to ignore it. The pattern above
    # catches the actual stale assertion; the consequence does not need its
    # own rule. (Measured on first run, not reasoned about afterwards.)
)

#: Struck text is not a live assertion. A struck sentence with a supersede note
#: is the correct way to retire a stale claim -- it keeps the history visible --
#: so firing on it would punish exactly the repair this script asks for.
#: Instance four above was fixed that way.
_RETIRED = re.compile(r"~~.*?~~", re.DOTALL)

#: Neither is a quotation. A decision record that *explains* a stale claim has
#: to reproduce it, and D15 does precisely that: its Why block quotes the very
#: sentence whose staleness justified building this script. Firing there is the
#: same defect as the removed `format adapter is needed` pattern -- a detector
#: that fires on the text documenting the problem it detects. Found by widening
#: the universe to the decision records, which is to say: found by this script's
#: own first honest run, not by reasoning.
_QUOTED = re.compile(r"\"[^\"\n]{0,200}\"|“[^”\n]{0,200}”|'[^'\n]{0,200}'")


def _live_text(text: str) -> str:
    """The parts of a document that still assert something in their own voice."""
    return _QUOTED.sub(" ", _RETIRED.sub(" ", text))


def _fail(problems: list[str]) -> None:
    for p in problems:
        print(f"  DISAGREEMENT: {p}", file=sys.stderr)


def _sentence_end(text: str, start: int) -> int:
    """Where the sentence running from `start` ends.

    A full stop followed by whitespace, or the end of the line. A dotted name such
    as `findings.severity.json` has no whitespace after its dots, so it does not end
    the sentence it sits in.
    """
    for index in range(start, len(text)):
        if text[index] == "\n":
            return index
        if text[index] == "." and (index + 1 == len(text) or text[index + 1].isspace()):
            return index
    return len(text)


def listed_names(specification: str, sentence: ListSentence) -> frozenset[str] | str:
    """The names one list sentence enumerates, or why no list could be read.

    Read from struck-out text removed and nothing else: a quotation mark or an
    apostrophe inside an enumerating sentence is not a quotation, and blanking it
    would drop names from the list.
    """
    text = _RETIRED.sub(" ", specification)
    count = text.count(sentence.opens)
    if count != 1:
        return f"states {sentence.opens!r} {count} times, and its list needs exactly one"
    start = text.index(sentence.opens) + len(sentence.opens)
    segment = text[start : _sentence_end(text, start)]
    if sentence.closes is not None:
        if sentence.closes not in segment:
            return (
                f"no longer closes the list opened by {sentence.opens!r} with "
                f"{sentence.closes!r} in the same sentence"
            )
        segment = segment[: segment.index(sentence.closes)]
    return frozenset(_NAME.findall(segment))


def check_lists(harness_specification: str, tool_specification: str) -> list[str]:
    """Disagreements between the two specifications' list sentences."""
    problems: list[str] = []
    for label, noun, expected in LISTS:
        read: dict[str, frozenset[str]] = {}
        for side, specification, sentences in (
            ("harness", harness_specification, HARNESS_SENTENCES),
            ("tool", tool_specification, TOOL_SENTENCES),
        ):
            names = listed_names(specification, sentences[label])
            if isinstance(names, str):
                problems.append(f"the {side} specification's {label} sentence {names}")
                continue
            if side == "harness" and label == "findings keys":
                names = names - frozenset(HARNESS_ONLY_KEYS)
            read[side] = names
        if len(read) != 2:
            continue
        suffix = ""
        if noun != "findings key":
            suffix = " -- the consumer and the producer disagree about the payload"
        for name in expected:
            in_harness, in_tool = name in read["harness"], name in read["tool"]
            if in_harness != in_tool:
                named, missing = ("harness", "tool") if in_harness else ("tool", "harness")
                problems.append(
                    f"{noun} `{name}` is named in the {named} side's list but not the "
                    f"{missing} side's{suffix}"
                )
            elif not in_harness:
                problems.append(f"{noun} `{name}` is named in neither side's list")
        for side in ("harness", "tool"):
            for name in sorted(read[side] - frozenset(expected)):
                problems.append(
                    f"the {side} side's {label} list names `{name}`, which this scanner does not "
                    "expect there -- add it here or take it out of that sentence"
                )
    return problems


def check(
    harness_text: str,
    tool_text: str,
    *,
    harness_specification: str,
    tool_specification: str,
) -> list[str]:
    """Return a list of disagreements; empty means the two sides agree."""
    problems = check_lists(harness_specification, tool_specification)
    harness_text = _live_text(harness_text)
    tool_text = _live_text(tool_text)

    for label, pattern in SEVERITY_CLAIMS:
        for name, text in (("harness", harness_text), ("tool", tool_text)):
            if re.search(pattern, text, re.IGNORECASE) is None:
                problems.append(f"{name} side no longer states that {label}")

    # Severity must never be described as living inside the findings document.
    for name, text in (("harness", harness_text), ("tool", tool_text)):
        if re.search(r"severity[^.]{0,40}backfilled\s+into", text, re.IGNORECASE):
            problems.append(
                f"{name} side describes severity as backfilled into the findings document; "
                "it is joined by id, and the producing tool may not mutate that file"
            )

    for pattern, reason in STALE_CROSS_CLAIMS:
        for name, text in (("harness", harness_text), ("tool", tool_text)):
            if re.search(pattern, text, re.IGNORECASE) is not None:
                problems.append(f"{name} side contains a stale cross-claim -- {reason}")

    return problems


def _read_side(spec: str) -> tuple[str, list[Path]]:
    """Concatenate every file named on one side of the interface."""
    paths = [Path(part) for part in spec.split(",") if part.strip()]
    if not paths:
        raise FileNotFoundError("no files named on this side")
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(str(path))
    return "\n".join(p.read_text(encoding="utf-8") for p in paths), paths


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2

    try:
        harness_text, harness_paths = _read_side(argv[1])
        tool_text, tool_paths = _read_side(argv[2])
    except FileNotFoundError as exc:
        print(f"not a file: {exc}", file=sys.stderr)
        return 2

    problems = check(
        harness_text,
        tool_text,
        harness_specification=harness_paths[0].read_text(encoding="utf-8"),
        tool_specification=tool_paths[0].read_text(encoding="utf-8"),
    )

    if problems:
        print(f"spec interface: {len(problems)} disagreement(s)", file=sys.stderr)
        _fail(problems)
        return 1

    print(
        f"spec interface: OK -- {len(FINDINGS_KEYS)} findings keys and "
        f"{len(SEVERITY_FIELDS)} severity fields and {len(SEVERITY_ROW_FIELDS)} row fields "
        f"agree, each read from its list sentence in the two specifications, across "
        f"{len(harness_paths)} harness file(s) and {len(tool_paths)} tool file(s); "
        "severity joined by id on both sides, no stale cross-claims"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
