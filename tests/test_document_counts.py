"""Cross-document counts, derived rather than remembered.

Six of the fourteen stale statements an independent audit found were **numbers**:
308 events against 285, 47 findings against 51, "eleven" for a ten-item list in
three places, seven judged dimensions against six in six places, a decision
header reading D1-D30 against a document holding fifty-odd.

None of them was wrong when written. Each went stale because the thing it
counted changed and the sentence did not, and nothing compared the two. That is
the same shape as every other finding in this project's last three audits, and
it is the one shape a twenty-line script can close outright: **a number quoted
in prose is a claim, and a claim about a countable thing can be counted.**

What this file does *not* do is check that the prose around each number is
right. It checks that the number is. A sentence can still be wrong in every
other way, and these tests will pass.
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
import tokenize
from collections import Counter
from pathlib import Path
from typing import Final

import yaml

from harness.checks import build_registry
from harness.core.context import build_context
from harness.core.rubric import CheckTier, load_rubric
from harness.corpus.policies import load_policies
from harness.corpus.text_adapter import parse_call
from harness.judge.prompt import absent_categories

REPO_ROOT: Path = Path(__file__).resolve().parents[1]
SPECS: Path = REPO_ROOT / "specs"
SPEC: str = (SPECS / "voice-agent-eval-harness.md").read_text(encoding="utf-8")
DECISIONS: str = (SPECS / "voice-agent-eval-harness.decisions.md").read_text(encoding="utf-8")
COVERAGE: str = (SPECS / "taxonomy-coverage.md").read_text(encoding="utf-8")
SCENARIO_MAP: str = (SPECS / "taxonomy-scenario-map.md").read_text(encoding="utf-8")
SWEEP: str = (SPECS / "error-type-sweep.md").read_text(encoding="utf-8")

#: The documents write ranges with an en dash, so the patterns must match one.
#: Named rather than embedded: an en dash and a hyphen are indistinguishable in
#: most editors, and a pattern that silently stopped matching would make these
#: tests pass by finding nothing -- which is the failure mode they exist to
#: prevent, one level up.
EN_DASH: str = "\u2013"

#: Decision headings use an em dash, not the en dash ranges use.
EM_DASH: str = "\u2014"


def _transcripts() -> list[Path]:
    found = sorted((REPO_ROOT / "corpus" / "transcripts").glob("CALL-*.txt"))
    assert found, "no transcripts"
    return found


def _findings() -> list[dict[str, object]]:
    document = yaml.safe_load(
        # "The corpus carries N findings" means the gold set, which is what
        # every downstream reader sees.
        (REPO_ROOT / "corpus" / "findings.yaml").read_text(encoding="utf-8")
    )
    rows = document["findings"] if isinstance(document, dict) else document
    assert isinstance(rows, list) and rows
    return rows


# --------------------------------------------------------------------------
# The decision record's own numbering
# --------------------------------------------------------------------------


def test_the_decision_numbering_agrees_with_itself() -> None:
    """Three statements of one number, in one file.

    The header read "D1-D30 recorded" while *Document status* read D1-D50 and
    the highest heading was D50. The header is the first thing a reader sees.
    """
    headings = sorted(int(n) for n in re.findall(r"^## D(\d+) —", DECISIONS, re.MULTILINE))
    assert headings, "no decision headings parsed; the heading shape has changed"
    highest = headings[-1]

    recorded = re.search(rf"Decisions \*\*D1{EN_DASH}D(\d+)\*\* recorded", DECISIONS)
    assert recorded, "Document status no longer states a range"
    assert int(recorded.group(1)) == highest, (
        f"Document status says D1{EN_DASH}D{recorded.group(1)}; the highest heading is D{highest}"
    )

    continues = re.search(r"Numbering continues from \*\*D(\d+)\*\*", DECISIONS)
    assert continues, "Document status no longer states the next number"
    assert int(continues.group(1)) == highest + 1, (
        f"numbering continues from D{continues.group(1)}; the highest heading is D{highest}"
    )


def _out_of_numeric_order(record: str) -> list[tuple[int, int]]:
    """Adjacent heading pairs that run backwards.

    Separated from its test so the control can run the same comparison over a
    record it has shuffled. A check whose only evidence is that it has never
    fired has been proven against nothing -- and this one was written *because*
    a check with that property let D100 land after D102.
    """
    headings = [int(n) for n in re.findall(rf"^## D(\d+) {EM_DASH}", record, re.MULTILINE)]
    return [
        (headings[i], headings[i + 1])
        for i in range(len(headings) - 1)
        if headings[i + 1] < headings[i]
    ]


def _decisions_after_the_not_checked_block(record: str) -> list[str]:
    """Decision numbers appearing below the `Not checked` heading."""
    if "## Not checked" not in record:
        return []
    return re.findall(
        rf"^## D(\d+) {EM_DASH}", record[record.index("## Not checked") :], re.MULTILINE
    )


def test_the_decisions_appear_in_numeric_order() -> None:
    """Gaps and duplicates were checked; **order was not**, and it broke.

    D100 was appended *after* the `Not checked` block, so the file read D99,
    D101, D102, the block, then D100. Two things wrong at once: a reader working
    forward met a decision after the section summarizing what is unresolved,
    which is the arrangement D58 moved that block to the end to prevent; and the
    sequence went backwards with no check noticing, because "no gaps and no
    duplicates" is true of a shuffled list.
    """
    out_of_place = _out_of_numeric_order(DECISIONS)
    assert not out_of_place, "decisions appear out of numeric order: " + ", ".join(
        f"D{a} then D{b}" for a, b in out_of_place
    )


def test_no_decision_follows_the_not_checked_block() -> None:
    """D58 moved that block below the last decision because sitting between D44
    and D45 guaranteed a reader met it before the entries superseding parts of
    it. A decision appended after it puts the block back in the middle."""
    trailing = _decisions_after_the_not_checked_block(DECISIONS)
    assert not trailing, (
        "decision(s) appended after the Not-checked block: "
        + ", ".join(f"D{n}" for n in trailing)
        + ". The block summarizes what is unresolved and belongs after what it summarizes."
    )


def test_both_ordering_checks_fire_on_the_arrangement_that_occurred() -> None:
    """The plants, and they are the real arrangement rather than an invented one.

    D100 is lifted out of the record and reinserted after the `Not checked`
    heading -- exactly where a session put it -- and both checks must report it.
    Neither mutation touches a file: the comparisons take text, so the control
    shuffles a copy.
    """
    d100 = DECISIONS.index(f"## D100 {EM_DASH}")
    d101 = DECISIONS.index(f"## D101 {EM_DASH}")
    entry = DECISIONS[d100:d101]
    without = DECISIONS[:d100] + DECISIONS[d101:]

    block = without.index("## Not checked")
    line_end = without.index("\n", block) + 1
    shuffled = without[:line_end] + "\n" + entry + without[line_end:]

    # The *predecessor* is whatever the highest decision happens to be, so
    # asserting the pair verbatim makes this control fail every time a decision
    # is added -- which it did, one commit later, on D103. What the check must
    # report is that the sequence steps backwards *to* D100.
    backwards = _out_of_numeric_order(shuffled)
    assert [pair for pair in backwards if pair[1] == 100], (
        f"the order check does not report a step backwards to D100: {backwards}"
    )
    assert _decisions_after_the_not_checked_block(shuffled) == ["100"], (
        "the placement check does not report D100 below the Not-checked block"
    )

    # And the false-positive half: the record as it stands must be clean under
    # both, or the plants above prove nothing about the live document.
    assert not _out_of_numeric_order(DECISIONS)
    assert not _decisions_after_the_not_checked_block(DECISIONS)


def test_the_decisions_are_numbered_without_gaps() -> None:
    """A missing number reads as a deleted decision, which is the one thing a
    decision record must not appear to do."""
    headings = sorted(int(n) for n in re.findall(r"^## D(\d+) —", DECISIONS, re.MULTILINE))
    missing = sorted(set(range(1, headings[-1] + 1)) - set(headings))
    assert not missing, f"no heading for: {missing}"
    assert len(headings) == len(set(headings)), "a decision number is used twice"


# --------------------------------------------------------------------------
# Counts of things that exist on disk
# --------------------------------------------------------------------------


def test_every_quoted_findings_total_matches_the_findings_document() -> None:
    r""" "The 47 candidate findings are unadjudicated" survived two rounds that
    changed the count.

    **Scoped to the present tense, and it was not always.** The regex used to be
    `The (\d+) candidate findings`, which matched D63's record of what a tag
    claimed on a particular day as readily as a live claim -- so a
    count-synchronizing edit rewrote a historical statement from 51 to 86 and
    this check required it, which is the exact failure D53 names: a decision
    record edited to agree with later decisions stops being a record. It now
    binds a phrase only a present-tense claim uses.
    """
    actual = len(_findings())
    quoted = [int(n) for n in re.findall(r"The corpus carries \*\*(\d+)\*\* findings", DECISIONS)]
    assert quoted, "no present-tense findings total is stated where one was"
    for number in quoted:
        assert number == actual, f"a document says {number} candidate findings; there are {actual}"


def test_every_quoted_event_total_matches_the_corpus() -> None:
    """ "twelve design transcripts, 308 events" against a corpus of 285."""
    actual = sum(len(parse_call(transcript).events) for transcript in _transcripts())
    quoted = [
        int(n) for n in re.findall(r"design transcripts, \*?\*?(\d+)\*?\*? events", DECISIONS)
    ]
    assert quoted, "no event total is stated where one was"
    for number in quoted:
        assert number == actual, f"a document says {number} events; the corpus has {actual}"


def test_the_not_checked_marker_agrees_with_the_spec_version() -> None:
    """A third statement of the same version, in a second file.

    Two markers were already bound to each other -- the spec header's version
    and its `Last swept` line. The decision record carries a third, and nothing
    read it: it said 0.22.0 against a spec at 0.19.0, a version this project has
    never been at. `git log -S` finds it in no commit, so it was a typo made
    while moving the other two and it survived a full suite, a phase-1 verifier
    run and an independent sweep.
    """
    version = re.search(r"^- Spec version: (\d+\.\d+\.\d+)", SPEC, re.MULTILINE)
    assert version, "the header no longer states a spec version"

    marker = re.search(r"^## Not checked — as of (\d+\.\d+\.\d+) @ D(\d+)", DECISIONS, re.MULTILINE)
    assert marker, "the decision record no longer states a not-checked marker"
    assert marker.group(1) == version.group(1), (
        f"the not-checked block is marked {marker.group(1)}; the spec is {version.group(1)}"
    )

    headings = sorted(int(n) for n in re.findall(r"^## D(\d+) —", DECISIONS, re.MULTILINE))
    assert int(marker.group(2)) <= headings[-1], (
        f"the not-checked block is marked at D{marker.group(2)}, "
        f"past the highest decision D{headings[-1]}"
    )


def test_the_transcript_count_is_the_declared_design_set() -> None:
    declared = [
        line.strip()
        for line in (REPO_ROOT / "corpus" / "DESIGN_SET").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    # Not a literal any more: D4's 12 was superseded when the error-type sweep
    # found classes the twelve calls could not carry without becoming implausible.
    # What must hold is that the declaration and the directory agree.
    assert declared == [p.stem for p in _transcripts()], (
        f"DESIGN_SET says {declared}; the directory has {[p.stem for p in _transcripts()]}"
    )


# --------------------------------------------------------------------------
# Counts of things that exist only in prose
# --------------------------------------------------------------------------


def test_the_judged_dimension_count_agrees_across_every_document() -> None:
    """Six in D42 and in the spec's own list, seven in six other places, and the
    cost model derived from the wrong one.

    **The check cannot tell a claim from a description of a past claim**, and
    that is deliberate. It caught D58's own prose describing this defect and
    refused it. The alternative -- a heuristic for "this sentence is
    retrospective" -- would be the thing it is guarding against: a check whose
    exemptions grow until it stops firing. So the constraint stands and the
    prose works around it: write the historical number as a digit, or name the
    decision instead of restating its count.
    """
    block = DECISIONS[DECISIONS.index("## D42 —") : DECISIONS.index("## D43 —")]
    body = block[block.index("What survives is what nothing else can do") :]
    dimensions = re.findall(r"^- \*\*", body, re.MULTILINE)
    assert len(dimensions) == 6, f"D42 now lists {len(dimensions)} dimensions; update this test"

    for name, text in (
        ("spec", SPEC),
        ("decisions", DECISIONS),
        ("coverage", COVERAGE),
    ):
        for match in re.finditer(
            r"\b(six|seven|eight)\b[^.\n]{0,24}judged (?:dimension|scale)", text
        ):
            word = match.group(1)
            # D16's option (A) is a record of what was considered, annotated
            # as such; it is the one deliberate exception.
            if "Seven at the time" in text[match.start() : match.start() + 400]:
                continue
            assert word == "six", (
                f"{name} says {word!r} judged dimensions near: "
                f"{text[match.start() : match.start() + 90]!r}"
            )


def test_the_deterministic_weakness_list_length_matches_its_prose() -> None:
    """The list is `W2-W10, W19` — nine plus one. Three documents called it
    eleven, including the acceptance criterion built on it."""
    named = re.search(rf"Part 3 \(W2{EN_DASH}W10, W19\)", SPEC)
    assert named, "the criterion no longer names the list"
    length = len(range(2, 11)) + 1
    assert length == 10

    for name, text in (("spec", SPEC), ("coverage", COVERAGE)):
        for match in re.finditer(r"rather than (\w+) requirements", text):
            assert match.group(1) == "ten", (
                f"{name} says {match.group(1)!r} requirements for a {length}-item list"
            )


def _tally_rows() -> list[tuple[str, int, list[int]]]:
    """`(label, stated count, items)` for each row of the coverage tally.

    Cells are bolded in the document, and an empty item list is written as an em
    dash rather than left blank. Both are stripped here rather than in each
    caller, because a parser duplicated across two tests is the shape this file
    exists to catch.
    """
    # Scoped to Part 2's tally, which is the one this parser is about. Part 2b
    # carries a second tally over classes S1-S10, and `\d+` reads those labels
    # as 1, 6, 7, 8 -- colliding with taxonomy item numbers and reporting them
    # as double-counted. Two tallies with different denominators must not be
    # read by one parser, which is the same argument Part 2b makes in prose.
    start = COVERAGE.index("\n### Tally\n")
    end = COVERAGE.index("\n## ", start)
    rows: list[tuple[str, int, list[int]]] = []
    for line in COVERAGE[start:end].splitlines():
        cells = [cell.strip().strip("*").strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 3 or not cells[1].isdigit():
            continue
        if not cells[0] or cells[0][0].isdigit():
            continue
        rows.append((cells[0], int(cells[1]), [int(n) for n in re.findall(r"\d+", cells[2])]))
    assert len(rows) >= 4, f"only {len(rows)} tally rows parsed; the table shape has changed"
    return rows


def test_the_taxonomy_tally_counts_match_its_own_item_lists() -> None:
    """The tally rows carry a count and a list. Nothing compared them, and two
    numbers in the surrounding prose had already drifted from the table."""
    seen: set[int] = set()
    for label, count, numbers in _tally_rows():
        assert len(numbers) == count, (
            f"tally row {label!r} says {count} and lists {len(numbers)}: {numbers}"
        )
        overlap = seen & set(numbers)
        assert not overlap, f"tally row {label!r} repeats items already counted: {sorted(overlap)}"
        seen |= set(numbers)


def test_the_spec_version_and_the_last_sweep_agree_with_the_changelog() -> None:
    """The header states a version and a sweep point; the changelog states the
    same version one line down. They are edited by hand, together, every time.

    **The sweep point names the version a sweep was recorded at, not the current
    one** (D194). This test used to require the two to be equal, so every bump
    moved the marker and claimed a sweep: from D168 to D193 it moved with every
    decision, and the phase-completion test beside it would have passed at phase
    5's close with no sweep performed (the phase-5 audit's P5-7). It now asks
    only that the marker names a version the changelog has, at or before the
    current one; what that version's entry must say is the next test's.
    """
    version = re.search(r"^- Spec version: (\d+\.\d+\.\d+)$", SPEC, re.MULTILINE)
    assert version, "the header no longer states a spec version"
    changelog = SPEC[SPEC.index("## changelog") :]
    latest = re.search(r"^- (\d+\.\d+\.\d+) \(", changelog, re.MULTILINE)
    assert latest, "the changelog's first entry no longer starts with a version"
    assert version.group(1) == latest.group(1), (
        f"header says {version.group(1)}; the newest changelog entry is {latest.group(1)}"
    )

    swept = re.search(r"^- Last swept: [\d-]+ @ (\d+\.\d+\.\d+) @ D(\d+)", SPEC, re.MULTILINE)
    assert swept, "the header no longer states a sweep point"
    assert _version(swept.group(1)) <= _version(version.group(1)), (
        f"last swept at {swept.group(1)}, past the spec version {version.group(1)}"
    )
    assert re.search(rf"^- {re.escape(swept.group(1))} \(", changelog, re.MULTILINE), (
        f"last swept at {swept.group(1)}, a version the changelog has no entry for"
    )


#: The first version whose sweep marker must name a changelog entry recording a
#: sweep (D194). Every marker before it moved with a decision's bump and is left
#: as history rather than re-read.
_SWEEP_ENTRIES_FROM: Final[tuple[int, ...]] = (0, 55, 0)

#: How a changelog entry says it records a sweep, followed by what the sweep read.
_SWEEP_TAG: Final[str] = "**Swept:**"


def _version(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split("."))


def _unevidenced_sweep(spec: str) -> str | None:
    """Why the header's sweep marker is not a sweep the changelog records, or `None`
    (D194). A marker at or past `_SWEEP_ENTRIES_FROM` must name a version whose
    changelog entry carries `_SWEEP_TAG`, so a decision's bump cannot move it."""
    swept = re.search(r"^- Last swept: [\d-]+ @ (\d+\.\d+\.\d+) @ D(\d+)", spec, re.MULTILINE)
    if swept is None:
        return "the header no longer states a sweep point"
    if _version(swept.group(1)) < _SWEEP_ENTRIES_FROM:
        return None
    changelog = spec[spec.index("## changelog") :]
    entry = re.search(rf"^- {re.escape(swept.group(1))} \(.*$", changelog, re.MULTILINE)
    if entry is None:
        return f"the header claims a sweep at {swept.group(1)}, a version with no changelog entry"
    if _SWEEP_TAG not in entry.group(0):
        return (
            f"the header claims a sweep at {swept.group(1)}, and that version's changelog entry "
            f"does not say it records one: it carries no {_SWEEP_TAG}"
        )
    return None


def test_the_sweep_marker_names_a_changelog_entry_that_records_a_sweep() -> None:
    """A sweep marker moves only with a sweep (D194).

    Moving `Last swept` claims the specification was swept at that version, and
    `test_a_swept_marker_is_evidenced_by_the_changelog` asks only that the newest
    entry names a decision at or past it, which a decision's own entry satisfies
    by construction. So the marker had moved with every decision from D168 to
    D193 with no sweep behind any of them. From 0.55.0 the version it names must
    have an entry that says it records a sweep, and what the sweep read.

    Planted first, so the check is proven to refuse one: a marker naming a
    decision's entry is refused, the same entry marked as a sweep is not, and a
    marker before 0.55.0 is history. Then the specification itself.
    """
    planted = (
        "- Last swept: 2026-09-20 @ 0.56.0 @ D193 -- trigger\n\n## changelog\n"
        "- 0.56.0 (2026-09-20): **a decision (D193).** What it changed.\n"
    )
    assert _unevidenced_sweep(planted) is not None
    swept = planted.replace("What it changed.", f"{_SWEEP_TAG} the whole document.")
    assert _unevidenced_sweep(swept) is None
    assert _unevidenced_sweep(planted.replace("0.56.0", "0.54.0")) is None

    problem = _unevidenced_sweep(SPEC)
    assert problem is None, problem


# --------------------------------------------------------------------------
# The register's enumerations, against the declarations they are prose about
# --------------------------------------------------------------------------

REGISTER: str = (REPO_ROOT / "corpus" / "entities.md").read_text(encoding="utf-8")

#: `CALL-01` ... `CALL-12` written as a range. Both the ellipsis character the
#: documents actually use and the three-dot form, because a pattern that
#: silently stopped matching would expand no range and compare a five-element
#: set against a fifteen-element one -- loudly, which is the point.
_CALL_RANGE: Final[re.Pattern[str]] = re.compile(r"CALL-(\d{2})`?\s*(?:…|\.\.\.)\s*`?CALL-(\d{2})")


def _first_sentence(text: str) -> str:
    """Up to the first full stop that ends a sentence rather than a filename.

    `corpus/transcripts/CALL-NN.txt` sits inside the design-set sentence, so a
    naive split on "." cuts it in half. A stop followed by whitespace or the end
    of the text is the one that ends a sentence here.
    """
    return re.split(r"\.(?=\s|$)", text, maxsplit=1)[0]


def _enumeration(label: str) -> str:
    """The register's `<label> set:` sentence, unwrapped onto one line.

    Bounded at the first blank line or the next paragraph marker, then cut to
    its first sentence -- because the held-out paragraph goes on to explain the
    shared numbering space by naming design calls, and those are prose about
    the *other* set rather than members of this one.
    """
    marker = f"\n{label} set: "
    assert marker in REGISTER, f"corpus/entities.md no longer carries a {label!r} set line"
    lines = REGISTER[REGISTER.index(marker) + 1 :].splitlines()
    collected = [lines[0]]
    for line in lines[1:]:
        if not line.strip() or line.startswith(("**", "#")):
            break
        collected.append(line)
    return _first_sentence(" ".join(collected))


def _enumerated_calls(sentence: str) -> set[str]:
    """The call ids a sentence names, with ranges expanded.

    `CALL-NN` is a filename placeholder rather than a call and is excluded by
    the digit class, which is why the pattern is not `CALL-\\S\\S`.
    """
    if "…" in sentence or "..." in sentence:
        assert _CALL_RANGE.search(sentence), (
            "the sentence writes a range this test cannot expand, so it would "
            f"compare only the ids it happened to parse: {sentence!r}"
        )
    ids = {
        f"CALL-{number:02d}"
        for low, high in _CALL_RANGE.findall(sentence)
        for number in range(int(low), int(high) + 1)
    }
    return ids | set(re.findall(r"CALL-\d{2}", sentence))


def test_the_registers_design_set_enumeration_agrees_with_the_declaration() -> None:
    """`corpus/DESIGN_SET` is the declaration; the register's line is prose about
    it, and nothing compared the two.

    D83 found the line one call stale -- it enumerated fourteen while the
    declaration held fifteen -- and said in as many words that "a check asserting
    the two agree is a few lines and would have caught it". This is those lines.
    The staleness survived D73 and two documentation sweeps.

    **The size guard next door would not have caught it and did not.**
    `test_every_worded_design_set_size_agrees_with_the_declaration` reads number
    *words* followed by a countable noun; this line states no number at all. It
    enumerates. A list and a count decay the same way and are caught by
    different checks, which is why both exist rather than one standing in for
    the other.
    """
    declared = {
        line.strip()
        for line in (REPO_ROOT / "corpus" / "DESIGN_SET").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }
    assert declared, "corpus/DESIGN_SET declares nothing"
    assert _enumerated_calls(_enumeration("Design")) == declared, (
        "the register enumerates a design set the declaration does not match:\n"
        f"  register says:      {sorted(_enumerated_calls(_enumeration('Design')))}\n"
        f"  corpus/DESIGN_SET:  {sorted(declared)}"
    )


def test_the_registers_held_out_enumeration_agrees_with_the_declaration() -> None:
    """The same line one noun over, and it decayed the same way on the same day.

    `HELDOUT_SET` is this repository's declaration of a set it cannot see, and
    the register enumerates that set too. When `CALL-21` joined, three documents
    were left describing five transcripts. The design half of this check would
    have been green throughout.

    Included here rather than left for a later session because writing only the
    design half, in the commit whose subject is a guard narrower than its rule,
    would have been that defect committed twice.
    """
    declared = {
        line.strip()
        for line in (REPO_ROOT / "HELDOUT_SET").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    assert declared, "HELDOUT_SET declares nothing"
    assert _enumerated_calls(_enumeration("Held-out")) == declared, (
        "the register enumerates a held-out set the declaration does not match:\n"
        f"  register says:  {sorted(_enumerated_calls(_enumeration('Held-out')))}\n"
        f"  HELDOUT_SET:    {sorted(declared)}"
    )


def test_the_enumeration_check_fires_on_the_call_that_actually_went_missing() -> None:
    """Both controls are the defects that happened, not invented ones.

    Dropping `CALL-20` from the design line reproduces exactly what D83 found in
    the register; dropping `CALL-21` from the held-out line reproduces what
    2026-09-06 found in three documents. A check that has only ever been
    observed to pass has been proven against nothing, and these two were both
    observed to fail before being trusted.
    """
    for sentence, dropped in (
        (_enumeration("Design"), "CALL-20"),
        (_enumeration("Held-out"), "CALL-21"),
    ):
        assert dropped in _enumerated_calls(sentence), (
            f"{dropped} is not in the register's enumeration, so removing it plants nothing"
        )
        # Removed wherever it sits rather than only in the `and` position: the
        # enumeration grows, and a control that only plants against the last name
        # in it stops planting anything the next time a call is added.
        planted = re.sub(rf"`{dropped}`(,| and)?\s*", "", sentence, count=1)
        assert planted != sentence, (
            f"the sentence no longer names {dropped} in the shape this control "
            f"removes, so nothing was planted: {sentence!r}"
        )
        assert dropped not in _enumerated_calls(planted), (
            f"{dropped} survived being removed from the sentence, so the "
            "extraction is not reading the enumeration it reports on"
        )


# --------------------------------------------------------------------------
# The recall net: a count nothing checks has to say so
# --------------------------------------------------------------------------
#
# Every count defect this project has found has one root: the checkers **fail
# open**. A number a pattern does not match is a number nothing checks, and
# silence is indistinguishable from success. The instances are all that shape --
# a capital letter on `Thirteen design calls`, an ordinal, digits where the
# strict guard reads only words, an endpoint range for the held-out set, a
# held-out count in a document nothing scanned.
#
# Patching each pattern treats instances forever. This inverts the direction:
# a deliberately over-broad net finds **sites**, and every site it finds must be
# accounted for -- verified by a strict checker, or declared as something other
# than a live count, with a reason. A number in prose that matches nothing and
# is declared nowhere fails the build.
#
# Keyed on `(document, number, noun)` rather than on the sentence, so rewording
# passes and changing a number fails. That is the whole behavior wanted: an
# edit that moves a count is exactly the edit that needs looking at.

_NET_WORDS: Final[str] = (
    "one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|"
    "fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty"
)
_NET_ORDINALS: Final[str] = (
    "first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|"
    "twelfth|thirteenth|fourteenth|fifteenth|sixteenth"
)

#: Wider than `_WORDS`, which is what a strict checker converts to an integer.
#: This is what a *reader* would recognize as a count. The lookbehind keeps the
#: net off identifiers -- `CALL-18`, `D74`, `F-56`, `O-3`, `0.21.0`, `S11` -- and
#: the thousands group keeps `1,050` one token, so changing it to `1,200` reads
#: as a different number rather than as the same leading `1`.
_NET_NUMBER: Final[str] = (
    r"(?<![\w\-`§#.,])(?:(?:" + _NET_WORDS + r")|(?:" + _NET_ORDINALS + r")|\d{1,3}(?:,\d{3})*)\b"
)

#: Nouns whose count something in this tree determines. Deliberately not every
#: noun: `days`, `hours`, `words per minute` and `business days` are quantities
#: about the world rather than about this corpus, and a net that caught them
#: would drown the inventory that makes it useful.
_NET_NOUNS: Final[tuple[str, ...]] = (
    "transcript",
    "call",
    "finding",
    "decision",
    "dimension",
    "criterion",
    "criteria",
    "event",
    "clause",
    "taxonomy item",
)

_RECALL_NET: Final[re.Pattern[str]] = re.compile(
    r"("
    + _NET_NUMBER
    + r")\*{0,2}[\s\-]+(?:[\w`*,]+[\s\-]+){0,2}?("
    + "|".join(_NET_NOUNS)
    + r")s?\b",
    re.IGNORECASE,
)


def _net_documents() -> dict[str, str]:
    """Live prose only, on the rule the held-out size guard already states.

    The specification's changelog and the decision record are dated by
    construction, and D53 settled that a record edited to agree with later
    decisions stops being a record -- so a superseded count inside either is a
    true statement about a past state. The audit report is excluded for the same
    reason and says so in its own banner. Everything a reader would take as a
    claim about the project *now* is in scope.
    """
    spec_body = SPEC[: SPEC.index("## changelog")]
    return {
        "spec": spec_body,
        "register": (REPO_ROOT / "corpus" / "entities.md").read_text(encoding="utf-8"),
        "manifest": (REPO_ROOT / "corpus" / "seeding-manifest.md").read_text(encoding="utf-8"),
        "coverage": COVERAGE,
        "sweep": SWEEP,
        "map": SCENARIO_MAP,
        "gold": (REPO_ROOT / "corpus" / "findings.yaml").read_text(encoding="utf-8"),
        "drafts": (REPO_ROOT / "corpus" / "findings.candidates.yaml").read_text(encoding="utf-8"),
        "verifier": (REPO_ROOT / "tools" / "verify_phase1.py").read_text(encoding="utf-8"),
        "obligations": (REPO_ROOT / "HOLDOUT-OBLIGATIONS.md").read_text(encoding="utf-8"),
    }


#: Shapes the net finds that are not counts of anything, with the reason each is
#: not. Applied before the inventory, because these are classes rather than
#: sites and listing them individually would bury the inventory that matters.
_NOT_A_COUNT: Final[tuple[tuple[str, str], ...]] = (
    (
        "one",
        "`one` before a singular noun is English's indefinite article. `one call handed "
        "to a human` is not a count, and forty-odd such sites would bury the inventory.",
    ),
    (
        "ordinal",
        "an ordinal is a positional reference inside one call or one list -- `the third "
        "call`, `the fourth closes the call` -- and moves with the thing it points into "
        "rather than with any total.",
    ),
    (
        "per-call",
        "`event`, `clause` and `tool call` counts measure one transcript's internals. "
        "They are resolved where they are cited: the findings-evidence checker resolves "
        "every span and citation these rest on, and no total in the tree determines them.",
    ),
)

#: The inventory. `(document, number, noun)` -> what accounts for it.
#:
#: **An exemption nobody has to justify is one that grows**, so every entry
#: carries its sentence -- the argument `_NOT_SCANNED` makes one file over, and
#: `_PLANNED` makes in `tools/statement_inventory.py`.
#:
#: Three kinds of entry, and the distinction is the mechanism rather than
#: bookkeeping. **VERIFIED** means a checker compares the value against
#: something computed, and names it. **HISTORICAL** means the sentence is dated
#: or explicitly past-tense in a live document, so it is a record and correct.
#: **UNCHECKED** means neither -- a live count that nothing computes. That third
#: list is the useful output: it is this project's inventory of claims it is
#: carrying on trust, and it should be short and should shrink.
_DECLARED_COUNTS: Final[dict[tuple[str, str, str], str]] = {
    # -- VERIFIED ---------------------------------------------------------
    # Enumerated rather than crossed. The first draft generated the product of
    # six documents and two nouns, declaring seven shapes that do not exist --
    # and `test_no_declared_count_has_quietly_stopped_existing` rejected it,
    # which is that test doing exactly the job it was written for on the commit
    # that introduced it.
    **{
        shape: (
            "VERIFIED: the design-set size, against corpus/DESIGN_SET by "
            "test_every_worded_design_set_size_agrees_with_the_declaration"
        )
        for shape in (
            ("spec", "sixteen", "call"),
            ("spec", "sixteen", "transcript"),
            ("register", "sixteen", "call"),
            ("map", "sixteen", "call"),
        )
    },
    ("spec", "10", "decision"): (
        "VERIFIED: the sweep trigger, by "
        "test_the_sweep_trigger_is_a_mechanism_and_not_only_a_sentence"
    ),
    ("spec", "35", "taxonomy item"): (
        "VERIFIED: the taxonomy's fixed size, by "
        "test_the_taxonomy_tally_covers_every_item_exactly_once"
    ),
    ("spec", "three", "criterion"): (
        "VERIFIED: phase 5's criteria asserted by the held-out repository's gate, by "
        "test_phase_5_declares_the_gate_asserted_criteria_and_the_unbuilt_report (D176)"
    ),
    ("spec", "6", "dimension"): (
        "VERIFIED: the judged-dimension count, by "
        "test_the_judged_dimension_count_agrees_across_every_document"
    ),
    ("spec", "six", "dimension"): (
        "VERIFIED: the judged-dimension count, by "
        "test_the_judged_dimension_count_agrees_across_every_document"
    ),
    ("map", "six", "dimension"): (
        "VERIFIED: the judged-dimension count, by "
        "test_the_judged_dimension_count_agrees_across_every_document"
    ),
    # -- NOT A COUNT AT ALL -----------------------------------------------
    ("spec", "5", "dimension"): (
        "NOT A COUNT: `Sonnet 5 for dimensions, Opus 5 for synthesis` is a model name. "
        "The digit is a version and moves when Anthropic ships, not when this corpus grows."
    ),
    ("spec", "41", "finding"): (
        "NOT A COUNT of this corpus: an audit of the comparative-judgment repository, "
        "whose findings this tree does not hold and cannot count."
    ),
    ("verifier", "1", "criterion"): (
        "NOT PROSE: `sum(1 for criterion in CRITERIA ...)` is Python. The verifier is "
        "scanned because its criterion *text* is prose a reader trusts; its code is not."
    ),
    # -- HISTORICAL, in a live document -----------------------------------
    ("spec", "6", "finding"): (
        "HISTORICAL: the phase-0 assumption as originally stated (`~6 findings per "
        "transcript`), carried with its dated discharges beneath it. Rewriting it would "
        "delete the estimate the discharge is judging."
    ),
    ("spec", "12", "call"): (
        "HISTORICAL: the same assumption and its first discharge, both stating the corpus "
        "as it then stood."
    ),
    ("spec", "70", "finding"): "HISTORICAL: the assumption's projected total, as estimated.",
    ("spec", "three", "finding"): (
        "HISTORICAL: what `e28650c` edited on 2026-09-07 -- the three already-judged "
        "findings whose text the US-spelling pass moved, named by `cj load`'s own refusal "
        "and recorded at D140. Dated and past-tense; de-quantifying it would delete the "
        "figure OB-18 has to discharge."
    ),
    ("spec", "51", "finding"): (
        "HISTORICAL: the assumption's discharge, explicitly dated and explicitly labeled "
        "`the number was wrong`."
    ),
    ("spec", "86", "finding"): "HISTORICAL: the restatement at 0.20.0, labeled as such.",
    ("spec", "14", "call"): "HISTORICAL: the same restatement.",
    ("coverage", "70", "finding"): (
        "HISTORICAL: `all 70 findings the corpus **then** held` -- the sweep's own input, "
        "and the number that makes its arithmetic readable."
    ),
    ("sweep", "70", "finding"): (
        "HISTORICAL: `after all 70 findings **then** in the corpus had been adjudicated`."
    ),
    ("sweep", "five", "finding"): (
        "HISTORICAL: a measurement of what adjudication did on one day -- five findings "
        "split, producing two shapes."
    ),
    ("coverage", "three", "taxonomy item"): (
        "HISTORICAL: what the specification referenced before this file existed."
    ),
    ("obligations", "80", "call"): (
        "HISTORICAL: `all 80 tool-call arguments **then** in the corpus`, the audit's own "
        "denominator."
    ),
    ("obligations", "twelve", "transcript"): (
        "HISTORICAL: the same audit, `across the twelve design transcripts` it then had."
    ),
    ("obligations", "nine", "finding"): (
        "HISTORICAL: `written **when this was** nine findings`, which is the sentence "
        "recording that the entry has been restated twice."
    ),
    ("obligations", "four", "transcript"): (
        "HISTORICAL: a measurement inside a discharge record -- four of the set carried "
        "unsourced arguments on the day they were repaired."
    ),
    ("obligations", "five", "transcript"): (
        "HISTORICAL: `three documents describing five transcripts` is the narrative of the "
        "defect that produced HELDOUT_SET. **The live requirement that shared this shape "
        "was de-quantified when this inventory was written** -- it read `the same rule, in "
        "all five transcripts` while the set held six, in the file whose whole purpose is "
        "stopping that. Shape-keying could not tell the two apart, which is this net's "
        "stated limit."
    ),
    ("verifier", "21", "criterion"): (
        "HISTORICAL: both sites are code comments narrating how `All 21 criteria pass` was "
        "once printed by a repository whose suite was red."
    ),
    ("map", "12", "transcript"): (
        "HISTORICAL: `the design set **as it stood at** 12 transcripts`, written as digits "
        "per this project's convention for a historical count."
    ),
    ("map", "12", "call"): (
        "ACCURATE AND SCOPED: `Part 1 -- the 12 design calls this map covers`. The map "
        "covers twelve of the fifteen and its banner says which three are mapped elsewhere. "
        "Not the design-set size, and not stale."
    ),
    # -- UNCHECKED: live counts nothing computes --------------------------
    ("spec", "five", "dimension"): (
        "UNCHECKED: phase 4's `five further judged dimensions` follows from the "
        "judged-dimension count minus the one phase 3 delivers, and nothing computes it."
    ),
    **{
        (document, number, noun): (
            "UNCHECKED: a small relational claim -- `two calls share an event id`, `three "
            "transcripts`, `two findings` -- naming the members alongside the number, so a "
            "reader can check it and no test does. Each is a corpus measurement and each "
            "can decay; they are listed rather than exempted so the list is the inventory "
            "of what is carried on trust."
        )
        for document, number, noun in (
            ("manifest", "two", "call"),
            ("manifest", "two", "finding"),
            ("manifest", "three", "finding"),
            ("manifest", "three", "transcript"),
            ("coverage", "two", "call"),
            ("sweep", "two", "call"),
            ("map", "two", "call"),
            ("gold", "two", "call"),
            ("drafts", "two", "call"),
            ("drafts", "two", "finding"),
            ("obligations", "two", "call"),
            ("obligations", "three", "call"),
        )
    },
}


def _net_sites() -> dict[tuple[str, str, str], list[str]]:
    """`{(document, number, noun): the sentences it appears in}`, class rules applied."""
    ordinals = set(_NET_ORDINALS.split("|"))
    sites: dict[tuple[str, str, str], list[str]] = {}
    for document, text in _net_documents().items():
        for match in _RECALL_NET.finditer(text):
            number, noun = match.group(1).lower(), match.group(2).lower()
            noun = "criterion" if noun == "criteria" else noun
            whole = re.sub(r"\s+", " ", match.group(0))
            if number == "one" or number in ordinals:
                continue
            if noun in {"event", "clause"} or "tool call" in whole.lower():
                continue
            sites.setdefault((document, number, noun), []).append(whole)
    return sites


#: Where a quotation of a decision is checked. Scoped to the documents that
#: cite decisions at all -- the record, the specification, the two registers and
#: the session documents.
_QUOTING_DOCUMENTS: Final[tuple[str, ...]] = (
    "specs/voice-agent-eval-harness.decisions.md",
    "specs/voice-agent-eval-harness.md",
    "OBLIGATIONS.md",
    "CONTROL-REGISTER.md",
)

#: A quotation introduced by naming the decision it comes from: `D42's fourth
#: dimension is "..."`, `D82 says "..."`, `D125's rule reads "..."`.
#:
#: **Deliberately narrow, and the width was measured rather than guessed.** Four
#: broader designs were tried first and every one of them reported between 45%
#: and 95% false positives, because quotation marks in this prose do at least
#: four jobs -- citation, coinage, scare-quoting and hypothetical utterance --
#: and nothing positional separates them. Requiring the *syntax* of attribution,
#: a decision id followed by a possessive or a reporting verb, is the one signal
#: that picks out "this text is in that decision" from "this is a phrase I am
#: holding at arm's length". It covers a handful of sites rather than hundreds.
#: That is the trade: a guard over the sites where a misquote is a false claim
#: rather than a style, and silence over the rest, which
#: `test_the_quotation_guard_finds_a_misquotation` holds it to.
_ATTRIBUTED_QUOTATION: Final[re.Pattern[str]] = re.compile(
    r"\bD(\d{1,3})(?:\u2019s|'s)?\s+(?:[\w-]+\s+){0,4}?"
    r"(?:is|are|reads?|says?|said|names?|states?|calls?|put it|quoted as|wording is)"
    r"\s*:?\s*\*{0,2}[\u201c\"]([^\u201c\u201d\"]{20,300})"
)

#: Quotations of wording that is deliberately not the decision's current text --
#: a superseded version, or a misquotation exhibited as the error it was. Both
#: are different claims from "this is what that decision says", and both are
#: legitimate.
#:
#: **Keyed on (document, substring), not on the substring alone**, which is this
#: project's own lesson arriving in a third place: the spelling guard scoped its
#: quoted-as-evidence exemptions to the document that may name them *after a
#: plant proved a global exemption blind*. The same hole opened here immediately.
#: D149 exhibits the handover's misquotation of D42 as its subject, and the
#: exemption that lets it do so is the exact string of the defect -- so an
#: unscoped entry would have excused the defect anywhere, including in the
#: handover it was found in. It missed only because that document wraps the
#: phrase across a line, which is luck rather than a mechanism.
#:
#: Each entry carries its reason: an exemption nobody has to justify is one that
#: grows, and this table's entries all say *I meant to write the wrong words*,
#: which is a claim a reader has to be able to reject.
_QUOTING_A_SUPERSEDED_VERSION: Final[dict[tuple[str, str], str]] = {
    ("specs/voice-agent-eval-harness.decisions.md", "had the agent misunderstood them?"): (
        "D149 exhibits the misquotation it was written about. The entry's subject is that this "
        "exact span was punctuated as D42's wording and is not, so quoting it correctly would "
        "destroy the example -- the same shape as the row below, one step further: that one "
        "quotes a decision's superseded text, this one quotes a citing sentence's wrong text. "
        "**The justification is the control on this table.** An exemption may say *I meant to "
        "write the wrong words*, and it has to say why in a sentence a reader can reject."
    ),
    ("specs/voice-agent-eval-harness.decisions.md", "Every call selects its account on"): (
        "D66's summary of F-56 as it stood before the quantifier pass corrected it. The "
        "sentence around the quotation says so and calls it *wrong when written*, which is the "
        "record doing its job: the error is preserved deliberately, so re-spelling it to match "
        "the corrected D66 would delete the finding."
    ),
}


def _decision_bodies() -> dict[int, str]:
    """Each decision's own text, normalized for comparison."""
    starts = sorted(
        ((int(m.group(1)), m.start()) for m in re.finditer(r"^## D(\d+) — ", DECISIONS, re.M)),
        key=lambda pair: pair[1],
    )
    bodies: dict[int, str] = {}
    for index, (number, start) in enumerate(starts):
        end = starts[index + 1][1] if index + 1 < len(starts) else len(DECISIONS)
        bodies[number] = _normalize_quotation(DECISIONS[start:end])
    return bodies


def _normalize_quotation(text: str) -> str:
    """Compare wording, not typography or wrapping.

    Curly quotes, em dashes and line breaks all vary between a quotation and its
    source without the words differing, and trailing punctuation is routinely
    pulled inside the quotation marks by a sentence that ends there.
    """
    swapped = (
        text.replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u2014", "--")
        .replace("\u2013", "-")
    )
    # Emphasis is typography, not wording. A citing sentence routinely bolds the
    # part it is drawing attention to -- `"had the agent misunderstood them **in
    # the first place**?"` -- and the source does not, so a comparison that kept
    # the markers would report a faithful quotation as a misquotation. Removed
    # throughout rather than stripped from the ends, because that is where the
    # emphasis actually falls.
    for marker in ("**", "*", "`", "_"):
        swapped = swapped.replace(marker, "")
    return " ".join(swapped.split()).lower().strip(" .,;:")


def _quoting_documents() -> dict[str, str]:
    paths = [REPO_ROOT / name for name in _QUOTING_DOCUMENTS]
    paths += sorted((REPO_ROOT / "sessions").glob("*.md"))
    return {
        path.relative_to(REPO_ROOT).as_posix(): path.read_text(encoding="utf-8")
        for path in paths
        if path.is_file()
    }


def _attributed_quotations() -> list[tuple[str, int, str]]:
    """`(document, decision number, quoted text)` for every attributed quotation."""
    found: list[tuple[str, int, str]] = []
    for name, text in _quoting_documents().items():
        for match in _ATTRIBUTED_QUOTATION.finditer(text):
            found.append((name, int(match.group(1)), match.group(2)))
    return found


def test_every_quotation_attributed_to_a_decision_is_one() -> None:
    """A quotation is a claim that the words are somebody else's.

    **Found by reading, after two of them turned out not to be.** The handover
    quoted D42's fourth dimension as *"had the agent misunderstood them?"* where
    D42 says *"had the agent misunderstood them in the first place?"*, and quoted
    an acceptance criterion as *"a distribution, not a single verdict"* where the
    specification says *"a verdict distribution, not a single verdict"*. Both
    preserved the meaning and neither was the quotation it was punctuated as --
    and the first sits in the finding that justifies widening that dimension, so
    the sentence doing the arguing was not the sentence being argued about.

    `tools/statement_inventory.py` already requires every `D<n>` named in prose
    to resolve. It cannot ask whether the decision *says what the citing sentence
    claims*, and nothing else did either: both misquotations passed every gate in
    this tree.
    """
    quotations = _attributed_quotations()
    assert len(quotations) >= 4, (
        f"the attribution pattern matched {len(quotations)} sites; it has stopped matching and "
        "would pass by seeing nothing, which is the failure this check exists to prevent"
    )

    bodies = _decision_bodies()
    wrong: list[str] = []
    for document, number, quoted in quotations:
        excused = any(
            document == where and _normalize_quotation(key) in _normalize_quotation(quoted)
            for where, key in _QUOTING_A_SUPERSEDED_VERSION
        )
        if excused:
            continue
        body = bodies.get(number)
        if body is None:
            continue
        if _normalize_quotation(quoted) not in body:
            wrong.append(f"{document} quotes D{number} as: {' '.join(quoted.split())[:120]}")

    assert not wrong, (
        "quotation(s) attributed to a decision that does not contain them. Either quote the "
        "decision verbatim, or drop the quotation marks and paraphrase -- or, if the decision has "
        "since been corrected and the old wording is the point, add it to "
        "_QUOTING_A_SUPERSEDED_VERSION with the reason:\n  " + "\n  ".join(wrong)
    )


def test_every_quotation_exemption_is_still_excusing_something() -> None:
    """An exemption whose site has gone is a hole with nothing behind it.

    The same shape as `test_every_quoted_spelling_exemption_is_still_quoted` one
    guard over: a carve-out outlives the sentence it was written for, and the
    next quotation that happens to match it is excused by an entry nobody
    reconsidered.
    """
    quotations = _attributed_quotations()
    for (document, key), reason in _QUOTING_A_SUPERSEDED_VERSION.items():
        assert reason.strip(), f"the exemption for {key!r} in {document} carries no reason"
        used = any(
            where == document and _normalize_quotation(key) in _normalize_quotation(quoted)
            for where, _number, quoted in quotations
        )
        assert used, (
            f"the exemption for {key!r} in {document} excuses no quotation that is there; "
            "either the site moved or the carve-out has outlived it"
        )


def test_the_quotation_guard_finds_a_misquotation() -> None:
    """The control, in-module, because the defect is one word inside a quotation.

    A mutation file can restore a defect into a copy of the repository; what it
    cannot easily do is express *the same quotation with one word removed* as a
    whole-line replacement in a document that wraps. So this plants the real
    defect -- the handover's own D42 quotation as it read before 2026-09-11 --
    and requires the comparison to reject it.
    """
    bodies = _decision_bodies()
    real = (
        "When the caller objected and a reversal or transfer followed, had the agent "
        "misunderstood them in the first place?"
    )
    assert _normalize_quotation(real) in bodies[42], (
        "D42 no longer contains the wording this control is built on, so the control is "
        "measuring nothing and the population it guards has moved"
    )
    misquoted = real.replace(" in the first place", "")
    assert _normalize_quotation(misquoted) not in bodies[42], (
        "dropping three words from D42's fourth dimension still matches it, so the comparison "
        "is not comparing what it claims to"
    )


def test_every_countable_claim_in_live_prose_is_checked_or_declared() -> None:
    """The recall net, and the reason it is a net rather than another pattern.

    A strict checker verifies a value and says nothing about the site it could
    not parse. This finds sites and refuses to be silent about them: anything the
    net sees must be verified by a named checker, or declared as historical, or
    declared as not a count -- each with a sentence saying which and why.

    **Written after several instances of one failure**, and
    `test_the_net_would_have_seen_every_count_defect_this_project_has_found`
    holds it to them rather than letting this docstring claim it. One of those
    instances it does *not* reach, and that test asserts the gap as well as the
    coverage: `Without the eleven` puts no noun beside its number.

    **Its own limit, stated rather than discovered later.** Keying on
    `(document, number, noun)` means two sentences in one document sharing a
    shape are one entry, so a stale site can hide behind a correct one. That is
    not hypothetical -- it happened while this inventory was being written, in
    `HOLDOUT-OBLIGATIONS.md`, and the repair was to de-quantify the live sentence
    rather than to make the net finer. A finer key would fail on every rewording
    and would be turned off within a week.
    """
    sites = _net_sites()
    assert len(sites) >= 30, (
        f"the net found only {len(sites)} shapes across the live documents; it has "
        "stopped matching and would pass by seeing nothing, which is the failure it "
        "exists to prevent"
    )

    undeclared = {
        shape: examples for shape, examples in sites.items() if shape not in _DECLARED_COUNTS
    }
    assert not undeclared, (
        "a count in live prose is neither verified by a checker nor declared as "
        "something else. Add it to a checker, or add an entry to _DECLARED_COUNTS "
        "saying what it is:\n  "
        + "\n  ".join(f"{shape}: {examples}" for shape, examples in sorted(undeclared.items()))
    )


def test_no_declared_count_has_quietly_stopped_existing() -> None:
    """The other direction, which the exemption lists one file over also need.

    A declaration matching nothing is a stale exemption: it says a site was
    classified when the site is gone, and it will silently absolve a *different*
    site that later takes the same shape. `_NOT_SCANNED` states the same argument
    about hiding places; this is it enforced rather than argued.
    """
    stale = sorted(set(_DECLARED_COUNTS) - set(_net_sites()))
    assert not stale, (
        "_DECLARED_COUNTS classifies shapes that no longer appear. Remove them, "
        "or the classification will absolve whatever takes the shape next:\n  "
        + "\n  ".join(str(shape) for shape in stale)
    )


def test_the_recall_net_fires_on_a_count_nobody_declared() -> None:
    """The control, planted in the shape the net exists for.

    Every failure this net was written after had one property: a strict checker
    ran, matched nothing, and reported success. So the thing to demonstrate is
    not that the net finds a wrong number -- it is that it refuses to be quiet
    about a number it cannot classify.
    """
    planted = "The corpus now carries nineteen design calls and eighteen findings.\n"
    sites: set[tuple[str, str, str]] = set()
    for match in _RECALL_NET.finditer(planted):
        sites.add(("planted", match.group(1).lower(), match.group(2).lower()))
    assert ("planted", "nineteen", "call") in sites, (
        "the net did not see a worded count of design calls, which is the exact "
        "shape it was built after"
    )
    assert ("planted", "eighteen", "finding") in sites
    assert not sites & set(_DECLARED_COUNTS), (
        "the planted shapes are already declared, so this control demonstrates nothing"
    )


def test_the_net_would_have_seen_every_count_defect_this_project_has_found() -> None:
    """The claim in the section comment above, asserted rather than asserted-in-prose.

    Each string below is a defect that reached a commit and was found by a reader
    afterwards. The strict checkers missed every one for a different reason; the
    net's whole justification is that one over-broad pattern covers all of them,
    and a justification stated in a comment is a claim like any other (D46).
    """
    reproduced = {
        "Thirteen design calls carry `caller_ani`": "a capital letter",
        "the same rule, in all five transcripts": "a held-out count in an unscanned file",
        "twelve design transcripts": "a count that went stale by addition",
        "the corpus yielded 51 findings across 12 calls": "digits, which the strict guard skips",
        "the fourteenth design call uses something weaker": "an ordinal before a countable noun",
    }
    for sentence, why in reproduced.items():
        assert _RECALL_NET.search(sentence), f"the net does not see {why}: {sentence!r}"

    # And the one it does NOT see, asserted so the gap cannot be forgotten into
    # a claim of coverage. `Without the eleven` has no noun beside the number --
    # it stands in for a list named earlier -- so no noun-anchored net reaches
    # it. Extending to bare number words was measured rather than assumed and
    # rejected: `the two together`, `the one place`, `the twenty-two dollars`
    # and 149 more like them, against a handful of real counts. A net at that
    # signal-to-noise is a net somebody turns off.
    assert not _RECALL_NET.search("Without the eleven, the verification check"), (
        "the net now sees a bare number standing in for its noun, which is more "
        "than this test claims for it -- re-measure the noise before widening the "
        "claim in the section comment above"
    )


# --------------------------------------------------------------------------
# Tagged quantities: the site says which number it is, instead of a pattern
# guessing
# --------------------------------------------------------------------------
#
# The strict checkers infer *which* quantity a number states from the words
# around it -- a number word followed by `design calls` is taken to be the
# design-set size. That inference works until a sentence phrases the claim
# differently, and it cannot reach a number with no noun beside it at all. That
# last shape is measured and un-nettable: `Without the eleven` stands in for a
# list named earlier, and widening a net to bare number words returns 152 sites
# of which almost none are counts.
#
# A tag closes exactly that. `fifteen design calls<!-- #design_set_size -->`
# says which quantity it is, so the check is an identity rather than a guess,
# and a future sentence phrased outside every pattern can still be checked by
# tagging it. Written as an HTML comment: invisible when the Markdown renders,
# greppable, and needing no tooling this repository does not already have.

#: What documenting a secret means here, beyond naming it once. A name in prose
#: is not documentation: when a build breaks, the reader needs to know what the
#: token grants and whether it has simply expired; at setup they need to know
#: where to make one. Each marker below answers one of those, and the guard
#: fails naming which is missing rather than saying "undocumented".
_SECRET_REFERENCE: Final[re.Pattern[str]] = re.compile(r"secrets\.([A-Z][A-Z0-9_]{2,})")
_GRANT: Final[re.Pattern[str]] = re.compile(r"\b(?:Contents|Actions|Metadata|Workflows):")
_TOKEN_CREATION_URL: Final[str] = "settings/personal-access-tokens"

#: What the README must say when the workflow reads no secret at all (D212).
#: Until 2026-09-22 it always read one, and this check refused a workflow that
#: read none as a comparison of nothing -- which was right while a secret was
#: the only way to reach a private sibling, and became a false alarm when both
#: read tokens were retired. Silence is still refused; the claim is what changed.
_NO_SECRET_CLAIM: Final[str] = "reads no secret"


def _undocumented_secrets(workflow: str, readme: str) -> list[str]:
    """What a workflow reads that its README does not explain.

    Takes both texts rather than reading them, so the control can run this over
    a workflow it has written. A control that restates the arithmetic proves the
    arithmetic rather than the check.
    """
    problems: list[str] = []
    names = sorted(
        name for name in set(_SECRET_REFERENCE.findall(workflow)) if name != "GITHUB_TOKEN"
    )
    if not names and _NO_SECRET_CLAIM not in readme:
        problems.append(
            "the workflow reads no secret and the README does not say so, so this check "
            f"compared nothing: write that it {_NO_SECRET_CLAIM!r} where a reader will meet it"
        )

    for name in names:
        mentions = [line for line in readme.splitlines() if name in line]
        if not mentions:
            problems.append(f"{name}: the README never names it")
        elif not any(_GRANT.search(line) for line in mentions):
            problems.append(f"{name}: named, but never on a line stating what it grants")

    if "expire" not in readme.lower():
        problems.append(
            "no expiry warning anywhere: a fine-grained token stops working on a date "
            "nobody is watching for, and that is the failure this documentation exists for"
        )
    if _TOKEN_CREATION_URL not in readme:
        problems.append("no pointer to where a replacement token is created")
    return problems


_QUANTITY_TAG: Final[re.Pattern[str]] = re.compile(r"<!--\s*#([a-z_]+)\s*-->")

#: What a tagged site may write its number as. Deliberately wider than `_WORDS`,
#: which is what the strict guards convert: a tag is checked by identity, so it
#: does not need the number in any particular form.
_TAGGED_NUMBER: Final[re.Pattern[str]] = re.compile(
    r"(?<![\w-])(" + _NET_WORDS + r"|\d{1,3}(?:,\d{3})*)\b", re.IGNORECASE
)

_TAG_WORDS: Final[dict[str, int]] = {
    word: value + 1 for value, word in enumerate(_NET_WORDS.split("|"))
}


def _obligation_rows(text: str) -> int:
    """How many rows the obligations register's table holds.

    Takes the text rather than reading it, for the reason its neighbor below
    gives: a count whose only evidence is that it has never disagreed has been
    proven against nothing, and the control needs to run this over a register
    it has mutated.
    """
    return len(re.findall(r"^\| OB-", text, re.MULTILINE))


def _discharged_obligations(text: str) -> int:
    """How many entries in the obligations register carry a discharged mark.

    Takes the text rather than reading it, so the control can run this over a
    register it has mutated -- the same reason `_sites_in` does. A count whose
    only evidence is that it has never disagreed has been proven against
    nothing.
    """
    return len(re.findall(r"^\*\*Discharged:\*\*\s*☑", text, re.MULTILINE))


#: Representative US spellings, used only to build the pattern below and to
#: plant its pairs in the control. Stored in the US form and transformed rather
#: than written out as the forms being forbidden, because this module is inside
#: the scan's own scope: a written-out list would mean the check finds the file
#: that defines it. A text checker cannot spell out what it forbids.
US_SPELLINGS: Final[frozenset[str]] = frozenset(
    {"regularization", "initialize", "normalization", "behavior", "recognized", "maximizing"}
)

#: The US forms whose pairs no -ize/-ise substitution reaches, so the pattern has
#: to name them. Kept as US spellings for the same reason; `_other_variety` is
#: where they become the other form, and it is the one function this scan skips.
IRREGULAR: Final[tuple[str, ...]] = (
    "license",
    "defense",
    "center",
    "catalog",
    "judgment",
    "analyze",
    "analyzed",
    "analyzing",
)

#: What the scan reads. `.txt` is included where the severity tool's equivalent
#: does not have it: the transcripts are the subject of this project, the corpus
#: declares `en-US`, and a corpus contradicting its own metadata is the argument
#: 745d1a6 was made on. Extensionless files -- `LICENSE`, `HELDOUT_SET` -- fall
#: out by suffix rather than by name.
SPELLING_SUFFIXES: Final[frozenset[str]] = frozenset(
    {".py", ".md", ".toml", ".yml", ".yaml", ".txt"}
)


def _other_variety(american: str) -> str:
    """The other variety's spelling of a US word.

    Every form this module forbids is written out here and nowhere else, for the
    reason the declarations above give. `_spelling_exempt_lines` locates this
    function so the scan can skip it, which is the narrowest hole that lets the
    guard read its own module at all.
    """
    irregular = {
        "license": "licence",
        "defense": "defence",
        "center": "centre",
        "catalog": "catalogue",
        "judgment": "judgement",
        "analyze": "analyse",
        "analyzed": "analysed",
        "analyzing": "analysing",
    }
    if american in irregular:
        return irregular[american]
    if american.startswith("behavior"):
        return "behaviour" + american[len("behavior") :]
    return american.replace("iz", "is")


#: The *shapes* of the variety this project does not use, rather than a list of
#: its words. Ported from the severity tool, where D29 records why: a list is
#: exactly as wide as the sweep that built it, and that sweep had missed ten
#: forms sitting in files it had just read.
#:
#: Anchored on word boundaries -- unanchored, the `-our` shape is found inside
#: ordinary words such as `resource`. Identifiers are handled by splitting them
#: before matching instead; see `_flagged`.
_OTHER_VARIETY: Final[re.Pattern[str]] = re.compile(
    r"\b(?:"
    r"[a-z]{3,}(?:isation|isations|ised|ises|ising|iser|isers|isable|(?<!w)ise)"
    r"|[a-z]{3,}(?:our|ours|oured|ouring|oural|ourally|ourer|ourers"
    r"|ourite|ourites|ourful|ourless)"
    r"|(?:travel|signal|label|relabel|cancel|marvel|counsel|fuel|dial)(?:led|ling|ler)"
    r"|" + "|".join(_other_variety(word) for word in IRREGULAR) + r")\b",
    re.IGNORECASE,
)

#: Words the pattern catches that are spelled the same in both varieties. Every
#: entry is here because a dictionary agrees it is not a difference, and never
#: because converting one was inconvenient. An exemption nobody has to justify
#: is one that grows.
#:
#: `exercisable` is the one this repository added to the ported list, from
#: `corpus/policies/transfer.v1.md`. That file is compared byte-for-byte against
#: the clauses transcripts quote from it, so a false positive there would have
#: been a change to two artifacts to satisfy a guard that was wrong.
_SAME_IN_BOTH: Final[frozenset[str]] = frozenset(
    {
        "advise",
        "advised",
        "advises",
        "advising",
        "appraised",
        "chastise",
        "comprise",
        "comprised",
        "compromise",
        "compromised",
        "concise",
        "demise",
        "despise",
        "despised",
        "devise",
        "devised",
        "disguise",
        "disguised",
        "enterprise",
        "excise",
        "exercisable",
        "exercise",
        "exercised",
        "exercises",
        "exercising",
        "expertise",
        "franchise",
        "franchised",
        "imprecise",
        "improvise",
        "improvised",
        "incise",
        "merchandise",
        "paradise",
        "praised",
        "precise",
        "premise",
        "promise",
        "promised",
        "promises",
        "promising",
        "raised",
        "raises",
        "raising",
        "revise",
        "revised",
        "revises",
        "revising",
        "supervise",
        "supervised",
        "surprise",
        "surprised",
        "surprises",
        "surprising",
        "televise",
        "treatise",
        "unexercised",
        "unraised",
    }
)

#: Lines that quote the other variety as *evidence*, keyed on a fragment that
#: does not itself contain a forbidden spelling -- otherwise this table would be
#: found by the scan it belongs to. Each entry says why converting the line
#: would damage it, because an exemption nobody has to justify is one that grows.
_QUOTED_AS_EVIDENCE: Final[dict[str, str]] = {
    "Narrow D1's committing": (
        "A commit title from the severity tool's history, quoted verbatim in the audit. "
        "Re-spelling a quotation makes it a misquotation."
    ),
    "British-spelled (": (
        "Three spellings quoted as examples of the variety this project does not use. "
        "The sentence is about those words; converting them leaves it saying nothing."
    ),
    "its agent says": (
        "The word quoted as the evidence in this file's own en-US argument. Converting "
        "it would take the evidence out of the claim it supports."
    ),
}

#: Splits an identifier into the words a boundary-anchored pattern can see. `_`
#: is a word character and a camel hump is not a boundary, so a snake_case name
#: whose component carries the suffix is invisible without this -- which is the
#: shape this conversion had to rename by hand.
_IDENTIFIER_SEAM: Final[re.Pattern[str]] = re.compile(r"(?<=[a-z])(?=[A-Z])")


def _flagged(text: str) -> list[str]:
    """The forms in `text` belonging to the variety this project dropped."""
    split = _IDENTIFIER_SEAM.sub(" ", text).replace("_", " ")
    return [word for word in _OTHER_VARIETY.findall(split) if word.lower() not in _SAME_IN_BOTH]


def _spelling_exempt_lines() -> range:
    """The lines this module spends writing out the forms it forbids.

    Located with `ast` rather than by a marker comment, so moving or
    reformatting `_other_variety` cannot silently widen the hole.
    """
    module = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == "_other_variety":
            assert node.end_lineno is not None
            return range(node.lineno, node.end_lineno + 1)
    raise AssertionError("_other_variety is not defined in this module")


def _spelling_scope() -> list[Path]:
    """The files this repository *tracks*, in the formats the conversion covered.

    Tracked rather than everything under the root, and the difference is not
    theoretical. The harness's CI checks the severity tool out **inside** its
    own workspace so the two specifications can be compared -- and a walk of the
    directory then reads another repository's files and reports its spellings as
    this one's. That is what happened on this guard's first run: green locally,
    where no sibling is checked out, and red in CI, naming a file the repository
    does not own.

    A walk also lets an untracked scratch file fail a build, which is a second
    way for a check's universe to be wider than the rule it enforces.
    """
    listed = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    tracked = [REPO_ROOT / name for name in listed if name]
    return sorted(path for path in tracked if path.suffix in SPELLING_SUFFIXES and path.is_file())


def _declared_lines(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def _quantities() -> dict[str, int]:
    """Every quantity a tag may name, computed from whatever determines it.

    **`phase_verifiers` is a glob** rather than a number, and it joined on
    2026-09-09 because the README said "the two phase verifiers" with three on
    disk. The recall net does not know "verifier" as a noun, so the worded
    count went stale unguarded through a whole phase -- the phase that added
    the third one.

    **`control_mutations` joined on 2026-09-11, after the register had been
    wrong about itself.** `CONTROL-REGISTER.md` closed with "twenty of them are
    re-derived on every run of `tools/verify_controls.py`" while
    `control-mutations.yaml` held ninety-two, so the document whose entire
    subject is a claim in a document going stale was carrying one -- and nothing
    saw it, because the recall net scans ten documents and that is not among
    them. A worded number in a register of this project's own bookkeeping is the
    shape that drifted for `OBLIGATIONS.md` and `HOLDOUT-OBLIGATIONS.md` before
    it.

    **`heldout_set_size` is deliberately absent.** Nothing in the tagged
    documents states it as a number -- the register states it as an
    *enumeration*, which `test_the_registers_held_out_enumeration_agrees_with_
    the_declaration` binds, and the specification was de-quantified when the set
    grew. A registry entry nothing uses is not coverage, and the test below
    refuses one.
    """
    dimensions = re.search(r"x (\d+) dimensions x N=", SPEC)
    assert dimensions, "the spec no longer states the dimension count where this reads it"
    return {
        "design_set_size": len(_declared_lines(REPO_ROOT / "corpus" / "DESIGN_SET")),
        "discharged_obligations": _discharged_obligations(
            (REPO_ROOT / "HOLDOUT-OBLIGATIONS.md").read_text(encoding="utf-8")
        ),
        "obligation_rows": _obligation_rows(
            (REPO_ROOT / "OBLIGATIONS.md").read_text(encoding="utf-8")
        ),
        "judged_dimensions": int(dimensions.group(1)),
        "phase_verifiers": len(list((REPO_ROOT / "tools").glob("verify_phase*.py"))),
        "control_mutations": len(_mutations()),
        "taxonomy_items": 35,
    }


#: Documents carrying tags. Scoped deliberately: these are the ones a reader
#: takes as current. `corpus/seeding-manifest.md` is listed carrying **none**,
#: which is a result rather than an omission -- de-quantifying its two wrong
#: counts (D89) left it stating no derived quantity at all.
#:
#: `HOLDOUT-OBLIGATIONS.md` joined on 2026-09-07, after its rollup line went
#: stale a second time -- inside the sentence recording the first.
#: `OBLIGATIONS.md` joined on 2026-09-09 carrying its own row count, before that
#: number had a chance to go stale rather than after: the register was written
#: with a worded total in its prose, which is the shape both of the other
#: bookkeeping quantities were in when they drifted. These two are the tagged
#: documents whose quantities are about this project's own bookkeeping rather
#: than about the corpus.
_TAGGED_DOCUMENTS: Final[tuple[str, ...]] = (
    "README.md",
    "specs/voice-agent-eval-harness.md",
    "corpus/entities.md",
    "corpus/seeding-manifest.md",
    "HOLDOUT-OBLIGATIONS.md",
    "OBLIGATIONS.md",
    "CONTROL-REGISTER.md",
)


def _sites_in(relative: str, text: str) -> list[tuple[str, str, str]]:
    """`(document, tag name, the number written in front of the tag)`.

    Takes the text rather than reading it, so the control below can run the
    same extraction over a document it has mutated. A check whose only evidence
    is that it has never fired has been proven against nothing.
    """
    sites: list[tuple[str, str, str]] = []
    for match in _QUANTITY_TAG.finditer(text):
        before = text[max(0, match.start() - 70) : match.start()]
        numbers = _TAGGED_NUMBER.findall(before)
        assert numbers, (
            f"{relative}: the tag #{match.group(1)} has no number in front of it, so it "
            f"labels nothing: ...{before[-60:]!r}"
        )
        sites.append((relative, match.group(1), numbers[-1].lower()))
    return sites


def _tagged_sites() -> list[tuple[str, str, str]]:
    return [
        site
        for relative in _TAGGED_DOCUMENTS
        for site in _sites_in(relative, (REPO_ROOT / relative).read_text(encoding="utf-8"))
    ]


def _as_int(token: str) -> int:
    return _TAG_WORDS[token] if token in _TAG_WORDS else int(token.replace(",", ""))


def test_every_tagged_quantity_states_the_number_it_names() -> None:
    """A tagged number is checked by identity rather than by inference.

    This is the half of the counting problem no pattern reaches. A strict guard
    infers the quantity from the surrounding words, so it is bounded by the
    phrasings somebody thought of; a bare number standing in for its noun is
    outside every one of them, and widening a net to catch those was measured at
    152 sites of which almost none are counts. A tag is the site saying what it
    is, which costs one HTML comment and is exact.
    """
    quantities = _quantities()
    sites = _tagged_sites()
    assert sites, "no tagged quantities found; the convention has been removed or never applied"

    wrong: list[str] = []
    for relative, name, token in sites:
        assert name in quantities, (
            f"{relative}: #{name} is not a declared quantity. Add it to _quantities() with "
            f"what computes it, or correct the tag. Declared: {sorted(quantities)}"
        )
        if _as_int(token) != quantities[name]:
            wrong.append(f"{relative}: #{name} is tagged on {token!r}; it is {quantities[name]}")
    assert not wrong, "a tagged number disagrees with what determines it:\n  " + "\n  ".join(wrong)


def test_no_declared_quantity_is_unused_and_no_tag_is_undeclared() -> None:
    """Both directions, because either alone is green and blind.

    A quantity nobody tags is a registry entry computing something no document
    claims -- harmless until a reader takes the registry for coverage. A tag
    naming no quantity is checked against nothing at all, which is worse, and is
    the shape this whole line of work is about.
    """
    used = {name for _, name, _ in _tagged_sites()}
    declared = set(_quantities())
    assert not used - declared, f"tags naming no declared quantity: {sorted(used - declared)}"
    assert not declared - used, (
        f"declared quantities nothing tags: {sorted(declared - used)}. A registry entry no "
        "document uses is not coverage; remove it, or tag the claim it computes"
    )


def test_the_tag_check_fires_on_a_number_that_disagrees_with_its_tag() -> None:
    """The control, run over a mutated document rather than over arithmetic.

    The first draft of this test compared two integers it had just computed and
    could not fail -- the same unfalsifiable shape D88 records deleting one file
    over. It now changes the number in front of a real tag, re-runs the real
    extraction, and asserts the real comparison rejects it. **A tag's whole
    value is that a wrong number under a right tag becomes detectable**, which
    no amount of pattern-widening achieves, so that is what gets planted.
    """
    quantities = _quantities()
    relative = _TAGGED_DOCUMENTS[0]
    text = (REPO_ROOT / relative).read_text(encoding="utf-8")
    sites = _sites_in(relative, text)
    assert sites, f"{relative} carries no tag to plant against"

    name, token = sites[0][1], sites[0][2]
    planted = "sixteen" if _as_int(token) != 16 else "twelve"
    assert _as_int(planted) != quantities[name], "the planted number happens to be correct"

    tag = f"<!-- #{name} -->"
    index = text.index(tag)
    head = text[:index]
    cut = head.lower().rindex(token)
    mutated = head[:cut] + planted + head[cut + len(token) :] + text[index:]

    mutated_sites = _sites_in(relative, mutated)
    disagreeing = [
        site for site in mutated_sites if _as_int(site[2]) != quantities.get(site[1], -1)
    ]
    assert disagreeing, (
        f"the number in front of #{name} was changed to {planted!r} and the extraction "
        "still reported agreement, so it is not reading the number it claims to"
    )


# --------------------------------------------------------------------------
# A term the specification says it retired, and a workflow it describes
# --------------------------------------------------------------------------

#: How the specification records that it stopped using a term. It writes the old
#: name in quotes beside the new one -- `Retargeted from "JSONL adapter"` -- so
#: the document already knows which words it has left. Nothing read that, and
#: two other lines went on using the retired name for as long as the marker sat
#: above them saying it had been retired.
_RETIRED_TERM: Final[re.Pattern[str]] = re.compile(r'Retargeted from "([^"]+)"')

#: The marker has to be able to quote the term it retires, or it cannot say what
#: it says -- so exactly one occurrence is allowed: the quoted one, at the span
#: the pattern captures. **A first draft allowed a 200-character window around
#: the marker instead, and its own control rejected it**: a reuse on the very
#: next line fell inside the window and went undetected. The real
#: specification's two live uses were far enough away that the loose version
#: passed, which is what a window buys -- correct today, blind to the case that
#: arrives next.


def test_no_term_the_spec_says_it_retired_is_still_used_as_a_live_claim() -> None:
    """The specification records its own retargets and then contradicted them.

    `Retargeted from "JSONL adapter"` sits in the in-scope P6 bullet, and two
    other live lines went on naming a JSONL adapter: a WHERE requirement and
    phase 6's `Includes:` list -- the latter two lines above its own `Done when:`
    line, which already said "the second adapter". A document disagreeing with
    itself inside three lines, with the correction written above both.

    **The changelog is excluded**, and the exclusion is the point rather than a
    convenience: an entry recording that a term was retired has to name it, and
    editing that would be rewriting the record to satisfy a checker (D53).
    """
    body = SPEC[: SPEC.index("## changelog")]
    markers = list(_RETIRED_TERM.finditer(body))
    assert markers, (
        "the specification no longer records a retargeted term in the shape this reads, so "
        "this check has nothing to hold and would pass by finding nothing"
    )

    live: list[str] = []
    for marker in markers:
        term = marker.group(1)
        quoted = marker.start(1)
        for found in re.finditer(re.escape(term), body):
            if found.start() != quoted:
                line = body[: found.start()].count("\n") + 1
                live.append(
                    f"line {line}: {term!r} is still used, and the spec says it was retired"
                )
    assert not live, (
        "the specification uses a term it records as retired:\n  "
        + "\n  ".join(live)
        + "\nEither the retarget did not happen, or these lines were left behind."
    )


#: Descriptions of CI that were true before D84 and are false after it. Held as
#: retired phrasings rather than as a general claim, because comparing prose
#: about a workflow against the workflow is not something a check can do in
#: general -- this pairs two specific sentences with the `exit 1` that falsified
#: them, and says so rather than implying more.
_RETIRED_CI_CLAIMS: Final[tuple[tuple[str, str], ...]] = (
    (
        "emits a warning rather than failing",
        "D84 made both workflows exit non-zero when the sibling repository is absent",
    ),
    (
        "stops the check running while the build stays green",
        "that is the failure D84 found and reversed, after a week of green builds that "
        "verified nothing",
    ),
)


def test_the_spec_does_not_describe_a_fail_closed_workflow_as_a_warning() -> None:
    """The specification described the CI behavior D84 replaced.

    It said the interface assertion "emits a warning rather than failing" and
    that "the build stays green", and called a harness build that cannot pass
    without a second repository the worse alternative. D84 chose that
    alternative, and the workflow has exited non-zero since -- after the
    companion workflow spent a week reporting success while verifying nothing
    about transcript contents.

    **Its limit, stated rather than implied.** This does not compare prose about
    a workflow against the workflow in general; nothing here can. It pairs two
    retired sentences with the `exit 1` that falsified them, and fails if either
    the sentences come back or the workflow stops failing closed. A third way of
    describing the same thing wrongly is outside it.
    """
    workflow = (REPO_ROOT / ".github" / "workflows" / "checks.yml").read_text(encoding="utf-8")
    assert "exit 1" in workflow, (
        "the harness workflow no longer exits non-zero anywhere, so it may have gone back to "
        "warning; D84 is the entry to re-read before changing this check"
    )
    body = SPEC[: SPEC.index("## changelog")]
    for phrase, reason in _RETIRED_CI_CLAIMS:
        assert reason.strip(), f"{phrase!r} is listed with no reason"
        assert phrase not in body, (
            f"the specification says {phrase!r}, and {reason}. The sentence describes CI as it "
            "was before D84"
        )


def test_the_retired_term_check_fires_on_a_term_the_spec_retired() -> None:
    """The control, planted with the term this check was written after.

    Driven through the same extraction the check uses, over a synthetic document
    rather than the real specification: writing the retired term into a file
    this check reads would make the suite report its own control, which has
    happened five times in this session's work and is cheaper to design around
    than to rediscover.
    """
    term = "JSONL" + " adapter"
    marker = f'Retargeted from "{term}": a format of this project\'s own invention proves nothing.'

    clean = f"- [P6] A second adapter shaped like a real platform's object. {marker}\n"
    assert _RETIRED_TERM.search(clean), "the marker pattern no longer matches its own shape"
    found = list(_RETIRED_TERM.finditer(clean))
    quoted = found[0].start(1)
    assert all(m.start() == quoted for m in re.finditer(re.escape(term), clean)), (
        "the marker's own quotation of the term was counted as a live use, which would make "
        "this check fail on every correctly-retired term"
    )

    # Deliberately on the very next line. An earlier version allowed a window
    # around the marker, and a reuse this close sat inside it.
    dirty = clean + f"- WHERE [P6] the {term} is selected, the system SHALL do so.\n"
    outside = [m.start() for m in re.finditer(re.escape(term), dirty) if m.start() != quoted]
    assert outside, (
        "a live use of the retired term outside the marker's sentence was not detected, which "
        "is the defect this check exists for"
    )


def test_the_taxonomy_tally_covers_every_item_exactly_once() -> None:
    """M5, the half the count check does not reach. Row counts matching row
    lengths says each row is self-consistent; it says nothing about whether the
    rows together account for items 1-35, or for those items only.

    A taxonomy item in no row is an item with no disposition, which is the
    acceptance criterion this document exists to satisfy.
    """
    covered: set[int] = set()
    for _, _, numbers in _tally_rows():
        covered |= set(numbers)

    expected = set(range(1, 36))
    assert not expected - covered, f"taxonomy items in no tally row: {sorted(expected - covered)}"
    assert not covered - expected, (
        f"tally rows name items outside 1-35: {sorted(covered - expected)}"
    )


def test_every_taxonomy_disposition_cell_says_something() -> None:
    r"""The existing acceptance test matches `\|.+?\|` on the disposition cell,
    and **whitespace satisfies `.+?`**. A row can carry a blank disposition and
    still be counted as carrying one, which is the criterion passing on the
    shape of a table rather than on its content.
    """
    rows = re.findall(
        r"^\|\s*(\d{1,2})\s*\|\s*(\*\*.+?)\s*\|\s*(.+?)\s*\|\s*$", COVERAGE, re.MULTILINE
    )
    assert len(rows) >= 30, f"only {len(rows)} taxonomy rows parsed; the table shape has changed"

    vocabulary = ("SEEDED", "CHECKED", "GAP", "DEFERRED", "ADOPTED", "CONSTRAINT")
    blank = [number for number, _, disposition in rows if not disposition.strip()]
    assert not blank, f"taxonomy rows with a blank disposition: {blank}"

    unrecognized = [
        (number, disposition[:48])
        for number, _, disposition in rows
        if not any(token in disposition.upper() for token in vocabulary)
    ]
    assert not unrecognized, (
        "taxonomy rows whose disposition names none of "
        f"{vocabulary}:\n  " + "\n  ".join(f"{n}: {d}" for n, d in unrecognized)
    )


def test_the_quoted_cj_load_split_matches_the_findings_document() -> None:
    """The findings total was bound; the defect/question split was not.

    The *Not checked* block reported `cj load` as having "admitted 44 and
    excluded 3", which was true of a 47-finding corpus and stayed on the page
    through two rounds that took it to 51. The tool admits defects and excludes
    question-tier entries, so both halves are derivable and neither should have
    been a remembered number.
    """
    # Reads the GOLD SET, not the drafts: `cj load` runs against
    # corpus/findings.yaml, and F-05's tier differs between the two because
    # adjudication changed it. Binding this to the drafts would have the
    # sentence describe a split the tool never sees.
    gold = yaml.safe_load((REPO_ROOT / "corpus" / "findings.yaml").read_text(encoding="utf-8"))[
        "findings"
    ]
    tiers = Counter(str(row["tier"]) for row in gold)
    admitted, excluded = tiers["defect"], tiers["question"]
    assert admitted and excluded, f"one tier is empty: {dict(tiers)}"

    quoted = re.findall(r"admitted \*?\*?(\d+)\*?\*? and excluded \*?\*?(\d+)\*?\*?", DECISIONS)
    assert quoted, "the cj-load sentence no longer states a split"
    for stated_admitted, stated_excluded in quoted:
        assert (int(stated_admitted), int(stated_excluded)) == (admitted, excluded), (
            f"a document says cj load admitted {stated_admitted} and excluded "
            f"{stated_excluded}; the corpus has {admitted} defects and {excluded} questions"
        )
    assert admitted + excluded == len(_findings())


#: Number words for counts that something else determines. Historical counts are
#: written as digits, which is the convention
#: `test_the_judged_dimension_count_agrees_across_every_document` states in its
#: own docstring -- the guard scans words, so a digit is how a record stays a
#: record without needing an exemption.
_WORDS: Final[dict[str, int]] = {
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
}

#: `\*{0,2}` for emphasis and `\s` rather than a literal space, because these
#: documents hard-wrap. **fourteen** calls and fourteen calls are the same
#: claim; so is a count that wraps between the number and its noun, and one
#: historical count does exactly that. A guard written against a single space
#: would have read eleven sites and silently skipped the twelfth.
_DESIGN_SET_SIZE = re.compile(
    r"\b("
    + "|".join(_WORDS)
    + r")\b\*{0,2}[\s-]+(?P<other>other[\s-]+)?(?:design[\s-]+(?:set\s+)?)?(?:transcript|call)s?\b"
)
#: `other` is captured rather than merely allowed, because it changes the
#: arithmetic: "eleven other design calls" is a claim about the design set minus
#: the one being discussed, so it must equal `declared - 1`. F-47's evidence said
#: exactly that, in the gold set, and stayed at eleven through two corpus
#: growths -- invisible to this guard because the pattern required `design` to
#: follow the number directly and one adjective was enough to hide it.


def test_every_worded_design_set_size_agrees_with_the_declaration() -> None:
    """D4 said twelve; D68 says fourteen; nine live statements still said twelve.

    Every one of them sat in prose no check read, in four documents, and each
    was corrected by hand at 0.19.0 or missed entirely. This is the same narrow
    condition D63 drew: a number that something else determines. `DESIGN_SET`
    determines this one.
    """
    declared = len(
        [
            line.strip()
            for line in (REPO_ROOT / "corpus" / "DESIGN_SET")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip() and not line.startswith("#")
        ]
    )
    # (label, text, minimum matches expected). The corpus documents were added
    # after an independent sweep ran this test's own regex over the files it did
    # NOT scan and found six statements wrong -- three of them inside
    # `findings.yaml`, which is the artifact judge-versus-human agreement runs
    # against and the one file where a stale sentence is a stale label. A guard
    # scoped to the specs while the gold set drifted was checking the cheaper
    # half.
    #
    # The minimums are per document rather than one total, because an aggregate
    # floor hides a document that has quietly stopped matching. Only the two
    # that certainly state the size carry a non-zero minimum; the rest may
    # legitimately never mention it, and saying so here is the difference
    # between a deliberate zero and an unnoticed one.
    sources: tuple[tuple[str, str, int], ...] = (
        ("spec", SPEC, 5),
        ("decisions", DECISIONS, 3),
        ("coverage", COVERAGE, 0),
        ("scenario map", SCENARIO_MAP, 0),
        ("sweep", SWEEP, 0),
        ("gold set", (REPO_ROOT / "corpus" / "findings.yaml").read_text(encoding="utf-8"), 0),
        (
            "drafts",
            (REPO_ROOT / "corpus" / "findings.candidates.yaml").read_text(encoding="utf-8"),
            0,
        ),
        ("manifest", (REPO_ROOT / "corpus" / "seeding-manifest.md").read_text(encoding="utf-8"), 0),
        ("register", (REPO_ROOT / "corpus" / "entities.md").read_text(encoding="utf-8"), 0),
    )

    checked = 0
    for name, text, minimum in sources:
        found = 0
        for match in _DESIGN_SET_SIZE.finditer(text):
            found += 1
            expected = declared - 1 if match.group("other") else declared
            assert _WORDS[match.group(1)] == expected, (
                f"{name} says {match.group(1)!r} where the design set has {declared}"
                f"{' (minus the one being discussed)' if match.group('other') else ''}: "
                f"{text[match.start() : match.start() + 70]!r}"
            )
        assert found >= minimum, (
            f"{name} states the design-set size {found} times, expected at least "
            f"{minimum}; the pattern may have stopped matching its phrasing"
        )
        checked += found

    # Every assertion above sits inside the loop, so an empty match set passes
    # loudly. The sweep that wrote this test flagged eleven such tests and
    # counted every one of them at runtime rather than trusting the shape; this
    # one is held to the same standard from the start. Eleven statements match
    # today, and a floor of six survives ordinary rewording while refusing a
    # pattern that has quietly stopped matching anything.
    assert checked >= 6, (
        f"the design-set size is stated in only {checked} places; the guard is blind"
    )


#: A quoted count is a count being discussed rather than claimed. The one in the
#: decision record -- `loses "eight substitution classes"` -- is the case that
#: forced this, and it is the same shape as the dimension guard's exemption.
_CLASS_COUNT = re.compile(
    r"(?<![\"\u201c])\b(six|seven|eight|nine)\b[^.\n]{0,30}?(?:substitution|entity) class"
)


def test_the_substitution_class_count_agrees_across_every_document() -> None:
    """Seven classes, enumerated in `constraints`. Three documents said eight.

    Corrected in the acceptance criterion at 0.4.0 and in the build prompt at
    D58 -- and *prior decisions* still said eight when this sweep read it, a
    third site both earlier passes missed while each recorded the fix as done.
    """
    enumerated = re.findall(
        r"\((\d)\) [a-z]", SPEC[SPEC.index("Follow the substitution-by-class") :][:1400]
    )
    assert enumerated, "the class enumeration in `constraints` no longer parses"
    count = max(int(n) for n in enumerated)
    assert count == 7, f"`constraints` now enumerates {count} classes; update this test"

    for name, text in (("spec", SPEC), ("decisions", DECISIONS), ("coverage", COVERAGE)):
        for match in _CLASS_COUNT.finditer(text):
            assert match.group(1) == "seven", (
                f"{name} says {match.group(1)!r} substitution classes near: "
                f"{text[match.start() : match.start() + 70]!r}"
            )


def _part_2b() -> str:
    """The section of the coverage map that carries the sweep's own classes."""
    start = COVERAGE.index("## Part 2b")
    return COVERAGE[start : COVERAGE.index("\n## Part 3", start)]


def test_the_part_2b_tally_counts_match_its_own_class_lists() -> None:
    """The second tally, held to the standard the first one is.

    Part 2b exists because the sweep found classes the inherited 35-item
    taxonomy does not enumerate, and it carries `S1`-`S10` rather than
    renumbering. A tally stating counts is a claim about a list sitting three
    inches above it, which is the narrow condition this whole file is for --
    and a new tally arriving unchecked is how the first one went stale.
    """
    section = _part_2b()
    defined = {int(n) for n in re.findall(r"^\| S(\d+) \|", section, re.MULTILINE)}
    assert defined == set(range(1, len(defined) + 1)), (
        f"Part 2b's classes are not S1..S{len(defined)}: {sorted(defined)}"
    )

    counted: set[int] = set()
    rows = 0
    for line in section.splitlines():
        cells = [cell.strip().strip("*").strip() for cell in line.strip().strip("|").split("|")]
        # A class row's second cell is prose, so `isdigit` already excludes it.
        # An earlier version also skipped rows whose label began with "S",
        # meaning to skip `| S1 |` -- and skipped every "SEEDED ..." tally row
        # with it, leaving one row parsed and the test green on nothing.
        if len(cells) != 3 or not cells[1].isdigit():
            continue
        if cells[0] in {"Disposition", ""}:
            continue
        rows += 1
        listed = {int(n) for n in re.findall(r"S(\d+)", cells[2])}
        assert len(listed) == int(cells[1]), (
            f"Part 2b row {cells[0]!r} says {cells[1]}, lists {len(listed)}: {sorted(listed)}"
        )
        assert not (listed & counted), (
            f"Part 2b row {cells[0]!r} repeats classes: {sorted(listed & counted)}"
        )
        counted |= listed

    assert rows >= 4, f"only {rows} Part 2b tally rows parsed; the table shape has changed"
    assert counted == defined, (
        f"the Part 2b tally accounts for {sorted(counted)}; the section defines {sorted(defined)}"
    )


def test_the_zero_rejection_tally_matches_the_ledger() -> None:
    """Three numbers carrying an argument, in the block that exists to record
    what has *not* been checked.

    "86 rulings, 60 `accept`, 26 `accept-with-edits`" against a ledger holding
    89 / 62 / 27 -- stale two decisions after that same block was re-dated for
    going stale, and its own preamble complains that its figures "went stale
    three spec versions running". The zero-rejection point it makes is sound and
    is left standing; the three numbers carrying it are countable, which is
    D63's narrow condition.
    """
    document = yaml.safe_load(
        (REPO_ROOT / "corpus" / "findings.adjudication.yaml").read_text(encoding="utf-8")
    )
    rows = document["rulings"] if isinstance(document, dict) and "rulings" in document else document
    if isinstance(rows, dict):
        rows = next(iter(rows.values()))
    verdicts = Counter(str(row["verdict"]) for row in rows)

    stated = re.search(
        r"\*\*(\d+) rulings, and none of them a rejection\.\*\* (\d+) `accept`, "
        r"(\d+) `accept-with-edits`, zero `reject`",
        DECISIONS,
    )
    assert stated, "the not-checked block no longer states the ruling tally in the shape read here"
    total, accept, edits = (int(n) for n in stated.groups())

    assert total == len(rows), f"the block says {total} rulings; the ledger holds {len(rows)}"
    assert accept == verdicts["accept"], (
        f"the block says {accept} `accept`; the ledger holds {verdicts['accept']}"
    )
    assert edits == verdicts["accept-with-edits"], (
        f"the block says {edits} `accept-with-edits`; "
        f"the ledger holds {verdicts['accept-with-edits']}"
    )
    assert verdicts["reject"] == 0, (
        f"the block says zero rejections; the ledger holds {verdicts['reject']} -- "
        "the observation it records has changed and the entry needs rewriting, not re-counting"
    )


def test_the_judged_call_estimate_follows_from_the_design_set() -> None:
    """One quantity, and it is now computed rather than quoted.

    The spec said 980 judged calls and the not-checked block said 980 while the
    spec had moved to 1,050; both were derived from the design-set size, the
    judged-dimension count and N, every one of which is pinned elsewhere in this
    file. This test used to bind the **quoted total** to that arithmetic.

    **The total is gone from the document (D74), and the arithmetic is not.**
    D132's precondition means the product overstates the run: a dimension that
    does not apply to a call issues nothing for it, and `J-policy-alignment`
    applies to half the design set. So what is asserted here is the relation
    rather than a figure -- the spec's shape is an upper bound, the harness's
    own estimate is at or below it, and the gap is exactly the calls the
    preconditions exclude. A quoted total would have to be maintained; a
    relation moves with the rubric.
    """
    stated = re.search(r"(\w+) transcripts x (\d+) dimensions x N=(\d+)", SPEC)
    assert stated, "the spec no longer states the judged-call arithmetic in the shape read here"
    calls = _WORDS[stated.group(1)]
    dimensions, repetitions = int(stated.group(2)), int(stated.group(3))

    declared = len(_declared_lines(REPO_ROOT / "corpus" / "DESIGN_SET"))
    assert calls == declared, (
        f"the arithmetic is written for {calls} calls; the design set has {declared}"
    )
    assert dimensions == 6, (
        f"the arithmetic assumes {dimensions} judged dimensions; D42 settled six"
    )

    # Plus synthesis: one further dimension per call, at the same N.
    ceiling = calls * (dimensions + 1) * repetitions

    rubric = load_rubric(REPO_ROOT / "rubric.yaml", build_registry().keys())
    policies = load_policies(REPO_ROOT / "corpus" / "policies")
    contexts = [
        build_context(parse_call(path), policies, policy_tool="fetch_policy")
        for path in sorted((REPO_ROOT / "corpus" / "transcripts").glob("*.txt"))
    ]
    issued = 0
    excluded = 0
    for entry in rubric.for_tier(CheckTier.JUDGE):
        assert entry.judge is not None
        applies = sum(
            1
            for context in contexts
            if not absent_categories(
                context, entry.judge.applies_when_facts_present, entry_id=entry.id
            )
        )
        issued += applies * entry.judge.repetitions
        excluded += (len(contexts) - applies) * entry.judge.repetitions

    assert issued + excluded == ceiling, (
        f"the harness issues {issued} judged calls and excludes {excluded}, which is "
        f"{issued + excluded} against the document's {ceiling}. The two no longer describe the "
        "same run."
    )
    assert issued <= ceiling, "the harness issues more calls than the document's arithmetic allows"


def test_every_test_named_in_a_rule_line_exists() -> None:
    """A **Rule** line is this record's promise that a mechanism exists.

    D46's finding is that a document claiming to be machine-checked is making a
    claim like any other, and a Rule line is the densest form of it: every
    decision from D19 on ends with one naming what enforces it. D73's named a
    guard that does not exist under that name -- the register check is
    `test_every_name_the_corpus_uses_is_in_the_register` -- and the citation
    survived a full suite and two sweeps, because nothing reads prose for
    identifiers.

    **Scoped to Rule lines deliberately.** Elsewhere the record names tests *as
    they were then*: D57 discusses two by their pre-rename names while
    describing what they did wrong, which is a record and must stay one. A Rule
    line is the one place a test name is a live claim.
    """
    functions = set()
    for source in list((REPO_ROOT / "tests").glob("*.py")) + list(
        (REPO_ROOT / "tools").glob("*.py")
    ):
        functions |= set(re.findall(r"^def (test_\w+)\(", source.read_text(encoding="utf-8"), re.M))
    assert functions, "no test functions found; this check would pass on an empty repository"

    rule_paragraphs = re.findall(r"\*\*Rule\*\* —(.*?)(?:\n\n|\n---)", DECISIONS, re.DOTALL)
    assert len(rule_paragraphs) >= 20, (
        f"only {len(rule_paragraphs)} Rule lines parsed; the shape has changed and this check "
        "would be reading almost nothing"
    )

    missing: list[str] = []
    checked = 0
    for paragraph in rule_paragraphs:
        for name in re.findall(r"\b(test_\w+)\b", paragraph):
            if name in {p.stem for p in (REPO_ROOT / "tests").glob("*.py")}:
                continue  # a module, cited as a file
            checked += 1
            if name not in functions:
                missing.append(name)

    assert checked >= 15, f"only {checked} test names cited across all Rule lines; expected more"
    assert not missing, (
        "a Rule line names a test that does not exist, so a decision's stated mechanism is "
        f"unfindable: {sorted(set(missing))}"
    )


#: Test names that appear in prose and correctly do not exist in this tree, each
#: with the reason. Two kinds, and both are legitimate.
#:
#: **Named as gone.** A document correcting a stale citation has to reproduce
#: the stale name, or the correction says nothing. That is the constraint D89
#: recorded -- a document explaining a checker cannot contain the checker's
#: trigger -- reaching a fourth checker.
#:
#: **Living in the other repository.** `HOLDOUT-OBLIGATIONS.md` names checks in
#: `voice-agent-eval-harness-holdout`, which is the whole point of that file.
#: D83's Rule line learned the converse rule the hard way: a Rule line may name
#: only a test that exists *here*, because a record claiming a mechanism must
#: name one this tree can run.
#: **Scoped to the document that may name it, not exempted globally.** The first
#: draft keyed on the name alone, and a plant proved it blind: with
#: `test_the_review_worksheet_on_disk_is_current` exempted everywhere, that
#: retired name could be written into any document and the guard stayed quiet.
#: The control had passed throughout, because it exercised the extraction and
#: not the exemption -- a check narrower than the claim made for it, in the
#: commit closing three of those.
_THIS_MODULE: Final[str] = "tests/test_document_counts.py"

_TEST_NAMES_NOT_IN_THIS_TREE: Final[dict[str, tuple[str, str]]] = {
    "test_the_review_worksheet_on_disk_is_current": (
        "corpus/findings.adjudication.yaml",
        "named as gone: the ledger's header reproduces it to say that no test has carried "
        "that name since D76 made the worksheet rendered rather than committed",
    ),
    "test_no_event_id_names_two_different_events_across_the_two_corpora": (
        "HOLDOUT-OBLIGATIONS.md",
        "lives in the held-out repository, which is the only place that can compare the two "
        "corpora; named in O-4 as its discharge",
    ),
    "test_every_redaction_still_matches_the_harness": (
        "HOLDOUT-OBLIGATIONS.md",
        "lives in the held-out repository, beside the packet builder it checks; named in "
        "O-6 as its discharge",
    ),
    "test_holdout_conventions": (
        "HOLDOUT-OBLIGATIONS.md",
        "a pytest module in the held-out repository, not a test function -- this tree's own "
        "module names are filtered by stem and that filter cannot know the other's",
    ),
}


def _prose_of_source(source: Path) -> str:
    """Comments and string literals only, so identifiers are not read as prose."""
    pieces: list[str] = []
    with source.open("rb") as handle:
        for token in tokenize.tokenize(handle.readline):
            if token.type in {tokenize.COMMENT, tokenize.STRING}:
                pieces.append(token.string)
    return "\n".join(pieces)


def _test_names_in(text: str) -> set[str]:
    """Every `test_*` name a text names, with wrapped names rejoined.

    **These documents hard-wrap, and a test name is long enough to break across
    a line.** Two real names in the suite are written `..._only_where_\\n
    it_is_seeded` and `..._agrees_with_\\n    the_declaration`, and a scan that
    did not rejoin them would report both as missing -- inventing two defects
    while looking for one. That is the same wrap-handling lesson as W16 and W17,
    and the third time this session a measurement taken without it manufactured
    a finding.

    **The rejoin accepts CRLF as well as LF**, because the working tree carries
    both: `core.autocrlf` is on, so a file rewritten by a tool on Windows comes
    back with `\r\n` and a rejoin keyed on `_\n` silently stops rejoining --
    reporting every wrapped name in that file as missing. Found when a file this
    function reads was rewritten while adding a design call, which is the wrap
    lesson arriving a third time by a route the first two did not have.
    """
    return set(re.findall(r"\b(test_[a-z0-9_]+)\b", re.sub(r"_\r?\n\s*", "_", text)))


def _defined_test_names() -> set[str]:
    return {
        name
        for source in sorted((REPO_ROOT / "tests").glob("*.py"))
        + sorted((REPO_ROOT / "tools").glob("*.py"))
        for name in re.findall(r"^def (test_\w+)\(", source.read_text(encoding="utf-8"), re.M)
    }


def test_every_test_name_in_prose_exists() -> None:
    """A test name in prose is a claim that a mechanism exists.

    `test_every_test_named_in_a_rule_line_exists` holds that claim **in Rule
    lines in the decision record**, and D73's Rule line is why it was written.
    Everywhere else the claim went unchecked, and three documents were naming
    tests that do not exist: the adjudication ledger's header named the
    worksheet check by a name retired at D76, and a decision entry plus a
    comment in the test suite named a judged-dimension guard **that has never
    existed under any name** -- written the day before this check, in the entry
    arguing that a document matters *because* a named test reads it.

    **Scope, and why the decision record keeps the narrower guard.** This reads
    the corpus documents, the specifications other than the record, the
    obligations register, and the suite's own comments and docstrings. The
    decision record is excluded here and keeps its Rule-line check, for the
    reason that check's docstring already gives: the record names tests *as they
    were then*, and D57 discusses two by their pre-rename names while describing
    what they did wrong. Reading every name there would demand rewriting
    history to satisfy a checker.
    """
    defined = _defined_test_names()
    assert defined, "no test functions found; this check would pass on an empty repository"
    modules = {path.stem for path in (REPO_ROOT / "tests").glob("*.py")}

    sources: dict[str, str] = {}
    for pattern in ("corpus/*.md", "corpus/*.yaml", "specs/*.md"):
        for path in sorted(REPO_ROOT.glob(pattern)):
            if path.name.endswith("decisions.md"):
                continue
            sources[path.relative_to(REPO_ROOT).as_posix()] = path.read_text(encoding="utf-8")
    sources["HOLDOUT-OBLIGATIONS.md"] = (REPO_ROOT / "HOLDOUT-OBLIGATIONS.md").read_text(
        encoding="utf-8"
    )
    # Handover documents, which name the mechanisms they hand over. Added when
    # one was written naming three tests and nothing read it -- the same shape as
    # the ledger header and the decision entry that prompted this check. The
    # audit reports beside them stay out for the reason the decision record does:
    # they are another session's record of what was true then, and one of them
    # names a test this session deleted on purpose.
    #
    # The assertion is the move's residue (D120). This glob read the repository
    # root until sessions/ existed, and a glob that stops matching drops its
    # sources without a word: the floor below is aggregated across some thirty of
    # them, so this check would have gone on passing while reading no handover at
    # all. Failing closed here is what makes the next move loud.
    handovers = sorted((REPO_ROOT / "sessions").glob("HANDOVER-*.md"))
    assert handovers, (
        "no handover document was found under sessions/. This check reads them by "
        "glob, and a glob that matches nothing contributes nothing to a floor that "
        "is aggregated across every source"
    )
    for handover in handovers:
        sources[handover.relative_to(REPO_ROOT).as_posix()] = handover.read_text(encoding="utf-8")
    for source in sorted((REPO_ROOT / "tests").glob("*.py")) + sorted(
        (REPO_ROOT / "tools").glob("*.py")
    ):
        sources[source.relative_to(REPO_ROOT).as_posix()] = _prose_of_source(source)

    for name, (where, reason) in _TEST_NAMES_NOT_IN_THIS_TREE.items():
        assert reason.strip(), f"{name} is exempted with no reason given"
        assert where in sources, f"{name} is exempted in {where}, which this check does not read"

    missing: list[str] = []
    checked = 0
    for label, text in sources.items():
        for name in sorted(_test_names_in(text) - modules):
            checked += 1
            if name in defined:
                continue
            exemption = _TEST_NAMES_NOT_IN_THIS_TREE.get(name)
            # The declaring module is allowed too: a register of exemptions has
            # to be able to name what it exempts, and its keys are string
            # literals in a file this check reads. Sixth instance in this
            # session of a checker reading its own text -- see D94.
            if exemption is None or label not in {exemption[0], _THIS_MODULE}:
                missing.append(f"{label}: {name}")

    assert checked >= 40, (
        f"only {checked} test names were read across {len(sources)} sources; the pattern "
        "has stopped matching and this check would pass by finding nothing"
    )
    assert not missing, (
        "prose names a test that does not exist, so a stated mechanism is unfindable. "
        "Correct the name, or declare it in _TEST_NAMES_NOT_IN_THIS_TREE with the reason "
        "it is legitimately absent:\n  " + "\n  ".join(missing)
    )


def test_no_exempted_test_name_has_quietly_come_back() -> None:
    """The other direction. An exemption for a name that now exists, or that no
    document names any more, absolves whatever takes its place next -- which is
    the argument `_NOT_SCANNED` makes one file over and `_DECLARED_COUNTS` makes
    in this one."""
    defined = _defined_test_names()
    revived = sorted(name for name in _TEST_NAMES_NOT_IN_THIS_TREE if name in defined)
    assert not revived, (
        f"these are exempted as absent and now exist here: {revived}. Remove the exemption"
    )

    # And an exemption whose document no longer names it is equally stale.
    unused = sorted(
        name
        for name, (where, _) in _TEST_NAMES_NOT_IN_THIS_TREE.items()
        if name not in _test_names_in((REPO_ROOT / where).read_text(encoding="utf-8"))
    )
    assert not unused, (
        f"these are exempted in a document that no longer names them: {unused}. An "
        "exemption with no subject absolves whatever takes its place"
    )


def test_the_name_check_fires_on_an_invented_test_and_rejoins_a_wrapped_one() -> None:
    """The control, planted with the name this check was written after.

    The plant is the guard a decision entry claimed reads the scenario map --
    named here only by assembly below, because writing it out would put it in a
    file this check reads. It has never existed under any name. The second half
    plants the other failure mode, the one that would make this check report
    defects rather than miss them: a real name broken across a line.
    """
    defined = _defined_test_names()

    # Both plants are assembled rather than written out. A literal would sit in
    # a file this check reads, and the check would report its own control as a
    # defect -- the fifth time in this run of work that a checker has fired on
    # its own text. Splitting the prefix is the whole trick: `"test"` and
    # `"_every_..."` are not names, and neither fragment matches the pattern.
    invented = "test" + "_every_judged_dimension_has_an_instance_in_the_corpus"
    assert invented not in defined, (
        "the invented name now exists, so this control no longer plants anything"
    )
    assert invented in _test_names_in(f"the guard `{invented}` reads its rows"), (
        "the extraction does not see a name in backticks"
    )

    real = "test" + "_the_registers_held_out_enumeration_agrees_with_the_declaration"
    assert real in defined, "the wrapped-name control names a test that does not exist"
    split = real.index("_agrees_with_") + len("_agrees_with_")
    wrapped = f"bound by `{real[:split]}\n    {real[split:]}`."
    assert real in _test_names_in(wrapped), (
        "a name wrapped across two lines was not rejoined, so this check would report "
        "every wrapped citation as a missing test"
    )


def test_every_identifier_named_in_prose_resolves() -> None:
    """The statement inventory, run as a check rather than as an errand.

    Seven classes -- repository paths, finding ids, call ids, decision numbers,
    policy documents, policy clauses, taxonomy items. Each is a statement naming
    something that either resolves or does not, and each was being maintained by
    reading until D76.

    Run as a subprocess rather than imported, which exercises the tool's CLI and
    avoids a dynamic import this project could only silence with the `type:
    ignore` its own acceptance criteria forbid.

    It runs with the decision record's historical paths excluded, because that
    document names files which existed when an entry was written and D53 forbids
    editing a record to agree with a later state. `--all` shows those.
    """
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "statement_inventory.py")],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, (
        "identifiers named in prose that do not resolve:" + result.stdout + result.stderr
    )


# --------------------------------------------------------------------------
# The held-out set's size, which the design-set guard's success concealed
# --------------------------------------------------------------------------

#: The same shape as `_DESIGN_SET_SIZE`, for the other set. The design guard
#: passing is what hid this: a reader seeing one count enforced assumes the
#: neighboring one is too, and nine statements said "five" for four days after
#: the set grew to six -- in the specification, the verifier, three briefs, a
#: handover and the decision record.
#:
#: Two shapes, because the documents use both: a worded or digit count in front
#: of "held-out", and the enumerated range `CALL-13…CALL-17` that names the set
#: by its endpoints and decays the same way.
_HELDOUT_SET_SIZE = re.compile(
    r"\b(" + "|".join(_WORDS) + r"|\d+)\b\*{0,2}[\s-]+held[\s-]out\b",
    re.IGNORECASE,
)


def _not_checked_block() -> str:
    """The decision record's present-tense section, which is not a record.

    Everything else in that file is dated by construction. This block is
    re-dated at each sweep and describes the project now, so a count inside it
    decays exactly like one in the specification -- which is why it is read by
    the size guards and the rest of the file is not.
    """
    start = DECISIONS.index("## Not checked")
    return DECISIONS[start : DECISIONS.index("## Document status", start)]


def _declared_heldout() -> list[str]:
    return [
        line.strip()
        for line in (REPO_ROOT / "HELDOUT_SET").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def test_every_worded_heldout_set_size_agrees_with_the_declaration() -> None:
    """`HELDOUT_SET` is the declaration; prose is the claim.

    The design-set guard scans number words followed by `design`, `transcript`
    or `call`. "5 held-out", "the five", "CALL-13…CALL-17" are all outside it,
    so the sixth transcript landed and every one of those statements stayed as
    it was -- including a caveat in `verify_phase1.py` asserting that the text
    above it had been corrected, which it had not.
    """
    declared = len(_declared_heldout())
    assert declared >= 5, f"HELDOUT_SET declares {declared}"

    # Live prose only. The specification's changelog and the decision record are
    # dated by construction, and D53 settled that a record edited to agree with
    # later decisions stops being a record -- so "5 held-out" inside either is a
    # true statement about a past state, not a stale one.
    #
    # **With one exception, added 2026-09-07 after it went stale.** The decision
    # record's *Not checked* block is not historical: it is written in the
    # present tense, it is re-dated at every sweep, and its own preamble says it
    # exists "so the next session does not rediscover these as fresh defects".
    # Excluding the whole file as a record therefore excluded the one section of
    # it that makes live claims, and that section said the held-out set was five
    # for a day after it became six -- while an audit reported the statement
    # class closed.
    sources: tuple[tuple[str, str], ...] = (
        ("spec", SPEC[: SPEC.index("## changelog")]),
        ("verifier", (REPO_ROOT / "tools" / "verify_phase1.py").read_text(encoding="utf-8")),
        ("not-checked block", _not_checked_block()),
    )
    for name, text in sources:
        for match in _HELDOUT_SET_SIZE.finditer(text):
            token = match.group(1)
            value = _WORDS.get(token.lower(), None)
            if value is None:
                value = int(token) if token.isdigit() else None
            if value is None:
                continue
            assert value == declared, (
                f"{name} says {token!r} held-out where HELDOUT_SET declares {declared}: "
                f"...{text[max(0, match.start() - 60) : match.end() + 40]}..."
            )


def test_no_live_document_enumerates_the_held_out_set_by_its_endpoints() -> None:
    """`CALL-13…CALL-17` is a count wearing a different hat, and it decayed the
    same way when `CALL-21` joined the set.

    Historical statements are exempt by the same rule D53 set: a record edited
    to agree with later decisions stops being a record. So the decision record
    and the changelog may say it; documents that describe the set *now* may not.
    """
    endpoints = re.compile(r"CALL-13\s*(?:\u2026|\.\.\.|-|to|through)\s*CALL-17")
    live = ("specs/voice-agent-eval-harness.md", "tools/verify_phase1.py", "HELDOUT_SET")
    offenders = []
    for name in live:
        text = (REPO_ROOT / name).read_text(encoding="utf-8")
        if endpoints.search(text):
            offenders.append(name)
    assert not offenders, (
        "documents describing the held-out set now name it by the endpoints it "
        f"outgrew: {', '.join(offenders)}"
    )


def test_the_sweep_trigger_is_a_mechanism_and_not_only_a_sentence() -> None:
    """The spec header carries `trigger: ~8-10 accrued decisions`, and D71 treated
    it as a rule by acting on it. Nothing compared the accrued count to it, so it
    fired at D79 and went unhonored through D86 -- fifteen decisions, with the
    version, the Not-checked marker and the changelog all left behind.

    A trigger nothing evaluates is a note about intent.
    """
    swept = re.search(r"Last swept: \S+ @ (\d+\.\d+\.\d+) @ D(\d+)", SPEC)
    assert swept, "the header no longer records a sweep point"
    headings = sorted(int(n) for n in re.findall(r"^## D(\d+) —", DECISIONS, re.MULTILINE))
    assert headings, "no decision headings parsed"
    accrued = headings[-1] - int(swept.group(2))
    assert accrued <= 10, (
        f"{accrued} decisions have accrued since the last sweep (D{swept.group(2)} -> "
        f"D{headings[-1]}), past the header's own ~8-10 trigger. Sweep and bump, "
        "or restate the trigger."
    )


def test_a_swept_marker_is_evidenced_by_the_changelog() -> None:
    """Bumping the version *claims* a sweep (D71), so the claim needs evidence.

    The trigger has three clauses and only one of them is observable from this
    tree. `accrued <= 10` above evaluates the numeric clause; "before
    publishing" and "at phase completion" are events nothing here can see, and
    the second is the clause that actually fired for phase 2 -- six accrued,
    well inside the threshold, with the changelog carrying no entry for D114
    through D119. A trigger nothing evaluates is a note about intent, and that
    sentence applied to one of its own clauses.

    What *is* mechanizable is the honesty of the bump. Moving `Last swept` to a
    decision the changelog does not reach means claiming a sweep the record
    cannot evidence, so this asserts the newest entry names a decision at or
    beyond the marker.

    **Equality against the highest decision is deliberately not asserted.** D74
    weighed and rejected it: `Last swept` lagging is the trigger counting down,
    not a marker going stale, and demanding equality would force a sweep claim
    per decision.
    """
    swept = re.search(r"^- Last swept: [\d-]+ @ \d+\.\d+\.\d+ @ D(\d+)", SPEC, re.MULTILINE)
    assert swept, "the header no longer records a sweep point"

    changelog = SPEC[SPEC.index("## changelog") :]
    newest = re.search(r"^- \d+\.\d+\.\d+ \(.*$", changelog, re.MULTILINE)
    assert newest, "the changelog's first entry no longer starts with a version"

    cited = [int(number) for number in re.findall(r"D(\d+)", newest.group(0))]
    assert cited, (
        "the newest changelog entry names no decision, so nothing connects the version it "
        "declares to the record the sweep read"
    )
    assert max(cited) >= int(swept.group(1)), (
        f"the header claims a sweep at D{swept.group(1)} and the newest changelog entry "
        f"reaches only D{max(cited)}. Bumping the version claims a sweep was performed; the "
        "entry is the evidence, so write it or move the marker back."
    )


def test_the_header_says_which_clauses_of_its_own_trigger_are_unmechanized() -> None:
    """The part that cannot be checked has to be visible, not implied.

    Leaving it implicit is how phase 2 completed with the numeric clause green
    and nobody swept: the reader assumed a mechanism covered the sentence, and
    one covered a third of it. **It then happened a second time**, for phase 3,
    with the honesty note in place and read by nobody -- which is what D129
    turned the phase-completion clause into a test for.

    One clause is still unobservable. *Before publishing* is an event outside
    this tree, and a proxy for it would be a mechanism that fires on the wrong
    thing, so the requirement is that the header keeps SAYING so.
    """
    trigger = re.search(r"^- Last swept: .*$", SPEC, re.MULTILINE)
    assert trigger, "the header no longer records a sweep point"
    line = trigger.group(0)
    assert "unmechanized" in line and "before publishing" in line.lower(), (
        "the trigger no longer says which of its clauses a test evaluates, so a reader has "
        "no way to tell the checked clauses from the one nothing can observe"
    )


#: A status line saying the handover is closed, in **both** forms this project
#: writes: `**Status: closed** 2026-09-12`, with the colon inside the bold, and
#: `**Status:** closed.`, with the colon before the closing asterisks. The pattern
#: read only the first, and the two handovers open at the time were written the
#: second way -- so closing either in place gave a line the check below could not
#: see, and phase 5 could have closed with its sweep clause never evaluated
#: (D199, the specification sweep's S-1).
_STATUS_CLOSED: Final[re.Pattern[str]] = re.compile(
    r"^\*\*Status:?(?:\*\*)?:?\s*closed", re.MULTILINE | re.IGNORECASE
)


def _closed_handovers() -> list[tuple[str, int]]:
    """Every closed handover, with the highest decision number it names.

    A closed handover is this tree's observable form of "the phase is over":
    `Status: closed` means the document is final, which nothing else in the
    repository states. The highest `D<n>` it references stands for the last
    decision it records -- a proxy, and a conservative one, since a handover
    that merely *mentions* a later decision only pulls the requirement forward.
    """
    found: list[tuple[str, int]] = []
    for path in sorted((REPO_ROOT / "sessions").glob("HANDOVER-*.md")):
        text = path.read_text(encoding="utf-8")
        if not _STATUS_CLOSED.search(text):
            continue
        cited = [int(n) for n in re.findall(r"\bD(\d{1,3})\b", text)]
        if cited:
            found.append((path.name, max(cited)))
    return found


def test_the_close_check_reads_a_status_line_in_either_form_this_project_writes() -> None:
    """The instrument, driven before the close relies on it (D199).

    `test_a_closed_phase_handover_requires_the_sweep_marker_to_have_reached_it`
    evaluates the specification's own *at phase completion* sweep clause, and it
    finds a closed handover by its status line. This project writes that line two
    ways -- `**Status: closed** 2026-09-12`, which phases 3 and 4 use, and
    `**Status:** open.`, which the reveal handover and the cross-project one use --
    and the pattern read only the first.

    So closing either of the second pair in place produced a line the check could
    not see: it would have compared nothing for that phase and stayed green on the
    handovers it already read. The specification sweep found it as S-1, and a copy
    of the tree with the handover closed both ways showed the check red for one form
    and green for the other. Both forms are read now, and a third that nobody writes
    is not.
    """
    closed = (
        "**Status: closed** 2026-09-12, `7860094` to `64b5848`, with the audit's findings closed",
        "**Status:** closed. Closed 2026-09-20, `3a6f0fe` to this commit.",
        "**Status:** CLOSED. Shouted, and still closed.",
    )
    for line in closed:
        assert _STATUS_CLOSED.search(line), f"a closed handover written {line[:24]!r} is not read"
    for line in ("**Status:** open. Opened 2026-09-18, at `3a6f0fe`.", "**Status: open**, still"):
        assert not _STATUS_CLOSED.search(line), (
            f"an open handover written {line[:24]!r} reads closed"
        )

    assert _closed_handovers(), "no handover in sessions/ is read as closed, so the check is blind"


def test_a_closed_phase_handover_requires_the_sweep_marker_to_have_reached_it() -> None:
    """D129. The sweep clause that has actually fired, mechanized.

    The header's trigger says "at phase completion", and until 2026-09-09 that
    clause was evaluated by nobody: it fired for phase 2 while the numeric
    clause sat green at six, and again for phase 3 at seven. Both times the
    specification went un-swept and its `Last updated` line was honest -- which
    is the state a sweep exists to end.

    A handover whose status line says `closed` is the event. The rule it
    implies is exact: the sweep marker must be at or beyond the last decision
    that handover records. Red the moment a phase closes and the sweep has not
    happened, which is the right order -- the handover is what says the phase
    is over.

    What it cannot say is whether a sweep was *thorough*, only that one was
    claimed. That is the same limit `OBLIGATIONS.md` states about itself: a
    mechanism removes the failure where nobody notices, not the one where
    somebody looks and is wrong. D71's rule covers the rest -- a bump has to be
    evidenced by a changelog entry naming a decision at or beyond the marker.
    """
    swept = re.search(r"^- Last swept: .*?@ D(\d+)", SPEC, re.MULTILINE)
    assert swept, "the header no longer records which decision it was swept at"
    marker = int(swept.group(1))

    closed = _closed_handovers()
    assert closed, (
        "no handover in sessions/ is marked closed, so this test compares nothing. A phase "
        "that ended without one is a phase whose completion nothing records."
    )
    behind = [f"{name} reaches D{last}" for name, last in closed if last > marker]
    assert not behind, (
        f"the specification was last swept at D{marker}, and a closed phase handover records "
        "decisions past it. `at phase completion` is one of this document's own sweep "
        "triggers and it has fired:\n  " + "\n  ".join(behind)
    )


def test_the_discharged_obligation_count_follows_the_marks_it_reads() -> None:
    """The register's rollup number, planted rather than assumed.

    That line has gone stale twice -- "all three" when three existed, then "all
    six" while seven were discharged, inside the very sentence recording the
    first instance. Tagging it moves the failure from a reader noticing to a
    build failing, but only if the extraction actually tracks the marks.

    So both directions are planted. A discharged mark appended must raise the
    count by one, and an existing mark flipped back to open must lower it by
    one. An extraction matching nothing, or matching every line, passes
    neither.
    """
    text = (REPO_ROOT / "HOLDOUT-OBLIGATIONS.md").read_text(encoding="utf-8")
    before = _discharged_obligations(text)
    assert before >= 1, "no obligation is marked discharged, so this control has no baseline"

    appended = text + "\n**Discharged:** ☑ -- planted by a control, not a real entry\n"
    assert _discharged_obligations(appended) == before + 1, (
        "appending a discharged mark did not move the count, so the extraction is not "
        "reading the marks"
    )

    reopened = text.replace("**Discharged:** ☑", "**Discharged:** ☐", 1)
    assert _discharged_obligations(reopened) == before - 1, (
        "reopening an obligation did not move the count, so the extraction cannot tell a "
        "discharged entry from an open one"
    )


def test_every_secret_the_workflow_reads_is_documented() -> None:
    """A secret is the one thing a reader cannot recover from the code.

    Every other fact about this repository is discoverable by reading it. A
    token is not: it lives in repository settings, it grants something the
    workflow does not state, and it stops working on a date nothing announces.
    So the README has to carry what the code cannot -- what it grants, that it
    expires, and where a replacement is made.

    This asserts documentation and not correctness. Whether the token installed
    today actually carries the permission the README claims is knowable only by
    running CI, and is not claimed here.
    """
    workflow = (REPO_ROOT / ".github" / "workflows" / "checks.yml").read_text(encoding="utf-8")
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    problems = _undocumented_secrets(workflow, readme)
    assert not problems, (
        "the workflow reads secrets the README does not explain:\n  " + "\n  ".join(problems)
    )


def test_the_secret_documentation_guard_finds_an_undocumented_secret() -> None:
    """The control, because a repository already documented proves nothing.

    Five plants, one per thing the guard claims to check: a secret absent from
    the README, one named without its grant, a README with no expiry warning,
    one with nowhere to make a replacement, and -- since D212 -- a workflow that
    reads no secret beside a README that does not say so. A guard that checked
    only the name would pass four of these.

    `GITHUB_TOKEN` is planted too, in the other direction: it is provided by
    the runner rather than installed by anybody, so requiring documentation for
    it would be a demand nobody can satisfy.
    """
    good = (
        "| `A_TOKEN` | here | `Contents: Read-only` on x |\n"
        "It expires; see https://github.com/settings/personal-access-tokens/new\n"
    )
    assert not _undocumented_secrets("uses: ${{ secrets.A_TOKEN }}", good)

    absent = _undocumented_secrets("${{ secrets.B_TOKEN }}", good)
    assert any("never names it" in p for p in absent), absent

    no_grant = _undocumented_secrets(
        "${{ secrets.A_TOKEN }}",
        "A_TOKEN is needed. It expires. https://github.com/settings/personal-access-tokens/new",
    )
    assert any("what it grants" in p for p in no_grant), no_grant

    no_expiry = _undocumented_secrets(
        "${{ secrets.A_TOKEN }}",
        "| `A_TOKEN` | `Contents: Read-only` |\nsettings/personal-access-tokens",
    )
    assert any("expiry warning" in p for p in no_expiry), no_expiry

    # D212: a workflow reading nothing is documented by saying so, not by silence.
    unclaimed = _undocumented_secrets("uses: actions/checkout@v7", good)
    assert any("does not say so" in p for p in unclaimed), unclaimed
    assert not _undocumented_secrets(
        "uses: actions/checkout@v7", good + "This workflow reads no secret.\n"
    )

    no_route = _undocumented_secrets(
        "${{ secrets.A_TOKEN }}", "| `A_TOKEN` | `Contents: Read-only` | It expires. |"
    )
    assert any("replacement token is created" in p for p in no_route), no_route

    assert not _undocumented_secrets("${{ secrets.A_TOKEN }} ${{ secrets.GITHUB_TOKEN }}", good), (
        "GITHUB_TOKEN is supplied by the runner, so demanding documentation for it would "
        "be a requirement nobody can meet"
    )


def test_no_other_variety_spelling_returns() -> None:
    """This project converted to US at 745d1a6, and nothing held it there.

    That conversion was word-boundary only, which cannot reach inside a
    compound: it left ten forms behind in the severity tool when the same
    method was used there, and it left this repository's own count in the same
    condition. This is the guard the harness did not have and the severity tool
    now does.

    Quoted spellings are exempted by `_QUOTED_AS_EVIDENCE` rather than
    converted. An audit that quotes three spellings as examples of a variety,
    and a corpus document that quotes one as the evidence for its own `en-US`
    claim, are made false by being corrected.
    """
    scanned = _spelling_scope()
    assert len(scanned) >= 40, (
        f"the scan reached {len(scanned)} files, too few to be reading this repository; "
        "the suffix list or the skip set has drifted"
    )

    here = Path(__file__).resolve()
    exempt = _spelling_exempt_lines()

    offenders: list[str] = []
    for path in scanned:
        skip = exempt if path.resolve() == here else range(0)
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if number in skip or any(key in line for key in _QUOTED_AS_EVIDENCE):
                continue
            offenders += [
                f"{path.relative_to(REPO_ROOT)}:{number}: {word}" for word in _flagged(line)
            ]
    assert not offenders, (
        "this project converted to US spelling at 745d1a6, and these did not. Convert "
        "each -- or, where a word is spelled the same in both varieties and the pattern "
        "has merely caught its shape, add it to _SAME_IN_BOTH, which is a list of things "
        "a dictionary agrees about and not of things that were inconvenient:\n  "
        + "\n  ".join(offenders)
    )


def test_the_spelling_guard_finds_a_planted_word() -> None:
    """The guard above has only ever returned green.

    A pattern with a typo, or a scope reaching no file, reports a clean
    repository in exactly the words a clean one produces. So the pattern runs
    against text that must match and text that must not.

    The last plant is the one that matters: it is the shape the conversion
    needed a human for, and it fails the moment anybody narrows this pattern
    back to word boundaries.
    """
    for american in US_SPELLINGS:
        assert _flagged(_other_variety(american)), f"the guard does not find {american}'s pair"

    assert not _flagged("analysis realistic optimistic pairwise imprecise mechanism"), (
        "the guard flags words spelled the same in both varieties -- `mechanism` is in "
        "that list because a stem-based conversion of this repository turned 103 of them "
        "into something else before the census caught it"
    )
    assert not _flagged("advised revised exercising promised surprising exercisable"), (
        "the allowlist is not applied, so ordinary prose is reported as a spelling to fix"
    )

    for shape in ("local" + "isation", "signal" + "ling", "general" + "ised"):
        assert _flagged(shape), (
            f"{shape!r} is the shape D29 was written about and the guard misses it, so "
            "the pattern has been narrowed back into a list"
        )

    assert _flagged(_other_variety("regularized") + "_wins"), (
        "the guard cannot see inside an identifier, so it is blind to the case the "
        "conversion had to rename by hand"
    )


def test_every_quoted_spelling_exemption_is_still_quoted() -> None:
    """An exemption for a line that no longer exists covers nothing.

    Each key names a real line that quotes the other variety as evidence. If a
    document is rewritten and the quotation goes, the exemption stays behind as
    a hole nobody is defending -- which is how such a table stops meaning
    anything. Each is also asserted to be *needed*: an exempted line with no
    forbidden spelling on it is an exemption doing no work.
    """
    scanned = _spelling_scope()
    for key, reason in _QUOTED_AS_EVIDENCE.items():
        assert reason.strip(), f"{key!r} is exempted with no reason given"
        matched = [
            line
            for path in scanned
            for line in path.read_text(encoding="utf-8").splitlines()
            if key in line
        ]
        assert matched, f"{key!r} is exempted and appears nowhere; remove the exemption"
        assert any(_flagged(line) for line in matched), (
            f"{key!r} is exempted and no line it names carries a spelling this guard "
            "would flag, so the exemption is doing no work"
        )


def test_the_spelling_scan_reads_only_this_repository() -> None:
    """The control for the scan's universe, planted as what actually broke CI.

    This workflow checks the severity tool out **inside** this workspace so the
    two specifications can be compared. That checkout is untracked here, so it
    must be invisible to the scan -- and before this was scoped to tracked
    files it was not: the guard read that repository's own test module, which
    necessarily contains the spellings it forbids, and reported them as this
    repository's. Green locally, where no sibling exists, and red in CI.

    Planted rather than argued: an untracked directory carrying a spelling is
    created, asserted absent from the scope, and removed.
    """
    intruder = REPO_ROOT / "not-this-repository"
    planted = intruder / "sibling.py"
    try:
        intruder.mkdir(exist_ok=True)
        # Built rather than written out, for the reason the declarations give:
        # this module is inside the scan it is testing.
        planted.write_text('"""' + _other_variety("behavior") + '."""', encoding="utf-8")

        assert _flagged(planted.read_text(encoding="utf-8")), (
            "the plant carries no spelling this guard would flag, so it proves nothing"
        )
        assert planted.resolve() not in {path.resolve() for path in _spelling_scope()}, (
            "an untracked file inside the working tree is in the scan's universe, so a "
            "sibling checkout or a scratch file can fail this repository's build"
        )
    finally:
        planted.unlink(missing_ok=True)
        if intruder.exists():
            intruder.rmdir()


# --------------------------------------------------------------------------
# The phase contract: requirements and criteria, counted by tag
# --------------------------------------------------------------------------
#
# D104. Phase 2 was about to be built against "5 SHALL [P2] requirements", a
# figure obtained by searching for the literal string `SHALL [P2]`. That string
# matches only the *ubiquitous* bullets, because every other EARS form puts the
# phase tag before the verb -- `WHEN [P2] ... SHALL`, `IF [P2] ... SHALL`,
# `WHERE [P2] ... SHALL`. Seven requirements were therefore invisible to the
# reading, including the whole rubric-validation family and the tier selector.
#
# The lesson generalizes past P2, so these read by tag for any phase and pin the
# counts a decision has been written about.

#: A phase tag as the documents write it: `[P2]`, and `[P1, and re-run ...]` for
#: the one criterion that carries a qualifier. The alternation is deliberate --
#: a pattern reading only `\[P(\d)\]` drops that criterion silently, which is
#: the fail-open shape the recall net exists to answer.
_PHASE_TAG: Final[re.Pattern[str]] = re.compile(r"\[P(\d)(?:,[^\]]*)?\]")

#: EARS keywords that open a requirement bullet. `The system SHALL [P<n>]` puts
#: its tag after the verb; every one of these puts it before.
_EARS_KEYWORDS: Final[tuple[str, ...]] = ("WHEN", "WHILE", "IF", "WHERE")

#: Counted from the documents on 2026-09-07, at D108. Changing a number here is
#: the edit that needs looking at, which is the whole point of pinning it.
#:
#: **P4's criteria went 11 to 20 on 2026-09-09**, when phase 4 ran the same
#: coverage check phase 2 opened with and found four of its five requirements
#: covered only in the half the requirement names, plus a whole deliverable --
#: the two-audience report -- carrying no criterion at all. Every number here
#: is asserted by equality against the document, so this line records *why* one
#: moved and never stands in for the count itself.
#:
#: **P5's criteria went 4 to 6 on 2026-09-12**, when phase 5's contract was read
#: before the phase opened: nothing asserted the freeze-SHA citation D21 chose as
#: property (a)'s evidence, and nothing gave the report's weighting a meaning, so
#: coverage is stated per band instead (D157).
#:
#: **P4 went to 7 requirements and 22 criteria on 2026-09-12**, when `--resume`
#: entered the contract at the phase-4 audit's sweep (D159): a path that spends
#: money had no requirement for the audit's served-count fix to be measured against.
#:
#: **P5 went to 2 requirements and 7 criteria on 2026-09-14**, when a held-out
#: run's labels manifest entered the contract (D173): the flag and its refusals
#: are behavior of this harness, and the manifest criterion's header half named
#: a key no run here could write.
#:
#: **P5 went to 8 criteria the same day**, when a held-out run was refused paths
#: inside the checkout (D174): the refusal joined D173's requirement as a clause
#: and has a criterion of its own, so the requirement count stays at 2.
#:
#: **P5 went to 9 criteria on 2026-09-15**, when `harness agreement` was built
#: (D175): the agreement requirement gained what it counts and refuses as clauses,
#: and the command has a criterion of its own beside the one asking for each set's
#: denominator, so the requirement count stays at 2.
#:
#: **P5 went to 4 requirements and 13 criteria on 2026-09-18**, when the coverage
#: report was built (D188): what it counts and where its held-out section may go
#: are behavior of this harness, so it carries a requirement of its own, and the
#: command has a criterion beside the two the report already had.
MEASURED_CONTRACT: Final[dict[str, dict[str, int]]] = {
    "requirements": {"1": 9, "2": 12, "3": 23, "4": 9, "5": 5, "6": 5},
    "criteria": {"1": 19, "2": 22, "3": 18, "4": 24, "5": 14, "6": 12},
}

#: What the reading D104 started from returns for P2. Held so the control below
#: asserts the narrow reading is narrower rather than assuming it.
MEASURED_LITERAL_SHALL_P2: Final[int] = 5


def _section(heading: str, next_heading: str) -> str:
    start = SPEC.index(heading)
    return SPEC[start : SPEC.index(next_heading, start)]


def _phase_of(line: str) -> str | None:
    match = _PHASE_TAG.search(line)
    return match.group(1) if match else None


def _requirement_bullets() -> list[str]:
    section = _section("## requirements", "## failure & escalation")
    return [line for line in section.splitlines() if line.startswith("- ")]


def _criterion_bullets() -> list[str]:
    section = _section("## acceptance criteria", "## implementation phases")
    return [line for line in section.splitlines() if re.match(r"^- \[[ x]\] ", line)]


def _by_phase(bullets: list[str]) -> Counter[str]:
    """Phase tag to count. A bullet carrying none is not counted here; the test
    below asserts that set is empty, so this never silently under-counts."""
    return Counter(phase for phase in (_phase_of(line) for line in bullets) if phase)


def _requirements_for_phase_by_literal_shall(phase: str) -> list[str]:
    """The reading D104 started from, kept so a control can run it.

    Separated from its test for the reason `_event_scoped_disagreements` is: a
    narrow reading observed only to agree with a wide one has been compared
    against nothing.
    """
    token = f"SHALL [P{phase}]"
    return [line for line in _requirement_bullets() if token in line]


def test_every_requirement_and_criterion_carries_a_phase_tag() -> None:
    """An untagged bullet belongs to no phase and is verified by no phase gate.

    Asserted before the counts below, because an untagged bullet would make
    those counts agree by being absent from both sides.
    """
    for label, bullets in (
        ("requirement", _requirement_bullets()),
        ("acceptance criterion", _criterion_bullets()),
    ):
        untagged = [line[:96] for line in bullets if not _PHASE_TAG.search(line)]
        assert not untagged, (
            f"{label}s carrying no phase tag, so no phase gate verifies them:\n  "
            + "\n  ".join(untagged)
        )


def test_the_requirement_and_criterion_counts_per_phase_are_the_measured_ones() -> None:
    """Both distributions, by equality rather than by floor.

    A floor would let a requirement be deleted and go unnoticed, which is the
    direction that matters: a phase gate reads the criteria list, and a
    requirement nothing implements is invisible from the gate's side.
    """
    assert _by_phase(_requirement_bullets()) == Counter(MEASURED_CONTRACT["requirements"]), (
        f"requirements per phase: measured {dict(_by_phase(_requirement_bullets()))}, "
        f"stated {MEASURED_CONTRACT['requirements']}"
    )
    assert _by_phase(_criterion_bullets()) == Counter(MEASURED_CONTRACT["criteria"]), (
        f"criteria per phase: measured {dict(_by_phase(_criterion_bullets()))}, "
        f"stated {MEASURED_CONTRACT['criteria']}"
    )


def test_the_literal_shall_reading_misses_every_ears_keyword_form() -> None:
    """The control for D104, run over the live document rather than a mutation.

    The miscount needs no planting: the narrow reading is still executable, and
    running both over the same section reproduces the gap that produced it. The
    assertion is not only that the counts differ but that **every** bullet the
    narrow reading drops opens with an EARS keyword -- which is the mechanism of
    the miss, and the part that would still be true if the numbers moved.
    """
    p2_by_tag = [line for line in _requirement_bullets() if _phase_of(line) == "2"]
    p2_by_literal = _requirements_for_phase_by_literal_shall("2")

    assert len(p2_by_literal) == MEASURED_LITERAL_SHALL_P2, (
        f"the literal `SHALL [P2]` reading now finds {len(p2_by_literal)}, "
        f"not the {MEASURED_LITERAL_SHALL_P2} D104 recorded"
    )
    assert len(p2_by_literal) < len(p2_by_tag), (
        "the literal reading no longer misses anything, so this control compares "
        "two readings that have become the same one and proves nothing"
    )

    missed = [line for line in p2_by_tag if line not in p2_by_literal]
    not_ears = [
        line[:96]
        for line in missed
        if not any(line.startswith(f"- {keyword} ") for keyword in _EARS_KEYWORDS)
    ]
    assert not not_ears, (
        "the literal reading drops a bullet that is not an EARS-keyword form, so "
        "the miss has a second cause D104 did not record:\n  " + "\n  ".join(not_ears)
    )
    assert len(missed) == len(p2_by_tag) - MEASURED_LITERAL_SHALL_P2


# --------------------------------------------------------------------------
# The control register, which is a list of what stands behind every fix
# --------------------------------------------------------------------------

#: The naming convention controls are written in. A control is a test planted
#: to prove a fix is load-bearing, and this is how the tree says so. The
#: convention is not the population -- a control named outside it is invisible
#: here, which CONTROL-REGISTER.md says in the section listing the ones that
#: are -- but it is what makes the registered half recoverable by rule rather
#: than by grep. The handover this register answers rebuilt the list with a
#: grep and said so: "the count is a grep result rather than a checkable list".
_CONTROL_IDIOM: Final[tuple[str, ...]] = (
    "would_notice",
    "fires_on",
    "fires_when",
    "moves_the_verdict",
    "would_catch",
    "the_control",
)

CONTROL_REGISTER: Final[Path] = REPO_ROOT / "CONTROL-REGISTER.md"


def _controls_named_in_the_idiom() -> set[str]:
    """Every test in the tree whose name follows the control convention."""
    return {name for name in _defined_test_names() if any(k in name for k in _CONTROL_IDIOM)}


def _registered_controls() -> set[str]:
    """Every test name the register names, from its tables and its prose.

    The module stems are subtracted for the reason
    `test_every_test_name_in_prose_exists` subtracts them: the register names
    `test_corpus_hygiene.py` in a column beside every row, and a module is not
    a test that has to exist under that name.
    """
    modules = {path.stem for path in (REPO_ROOT / "tests").glob("*.py")}
    return _test_names_in(CONTROL_REGISTER.read_text(encoding="utf-8")) - modules


def test_every_control_is_registered() -> None:
    """A control nobody wrote down is a control nobody can audit.

    The register exists because the list of controls was recoverable only by
    grepping the naming convention, which makes it a result rather than a
    checkable list -- and a result goes stale the first time a control is added
    and nobody re-runs the grep. This is the direction that catches that.
    """
    idiom = _controls_named_in_the_idiom()
    assert idiom, "no test matches the control idiom; this check would pass on an empty rule"

    unregistered = sorted(idiom - _registered_controls())
    assert not unregistered, (
        "these follow the control naming convention and CONTROL-REGISTER.md does not name "
        "them:\n  " + "\n  ".join(unregistered) + "\nAdd a row, with a verdict and the "
        "evidence behind it. A control that is not registered is one no later pass can audit."
    )


def test_every_registered_control_exists() -> None:
    """The other direction. A row naming a test that does not exist points a
    reader at a mechanism that is not there, which is the defect
    `test_every_test_name_in_prose_exists` was written for -- and the register
    sits in the repository root, which that check does not read."""
    registered = _registered_controls()
    assert registered, "CONTROL-REGISTER.md names no tests; it is not being read"

    absent = sorted(registered - _defined_test_names())
    assert not absent, "CONTROL-REGISTER.md names tests that do not exist:\n  " + "\n  ".join(
        absent
    )


def test_the_register_guard_would_notice_an_unregistered_control(tmp_path: Path) -> None:
    """The control on the register's own guard, driven both ways.

    Written because the guard above is the sort of check that would pass over
    an empty rule: an idiom matching nothing, or a register read as an empty
    string, compares two empty sets and says nothing is missing. Both are
    planted here rather than argued about.
    """
    idiom = _controls_named_in_the_idiom()
    registered = _registered_controls()

    invented = "test" + "_the_widget_check_would_notice_a_widget"
    assert invented not in idiom, "the invented control now exists; this control plants nothing"
    assert any(key in invented for key in _CONTROL_IDIOM), (
        "the invented name does not match the idiom, so it would never have been required"
    )
    assert sorted((idiom | {invented}) - registered) == [invented], (
        "an unregistered control matching the idiom is not reported as missing"
    )

    # And the register is really being read, rather than parsed to nothing:
    # every name it yields is a test name, and it yields the rows above.
    assert "test_the_anchor_check_would_notice_a_moved_event" in registered, (
        "the register parsed to a set that does not contain a row it visibly carries, so "
        "these comparisons are running over an empty document"
    )
    stale = tmp_path / "empty.md"
    stale.write_text("no names here", encoding="utf-8")
    assert not _test_names_in(stale.read_text(encoding="utf-8")), (
        "the name extraction finds test names in a document that carries none"
    )


# --------------------------------------------------------------------------
# The mutation specs, which are what makes a `connected` verdict re-derivable
# --------------------------------------------------------------------------

CONTROL_MUTATIONS: Final[Path] = REPO_ROOT / "control-mutations.yaml"


def _mutations() -> list[dict[str, str]]:
    """The mutation specs, as a list.

    A list rather than a mapping keyed on control name, because
    `test_every_traced_finding_is_on_a_call_the_entry_fires_on` exists in two
    modules: a mapping kept one of them and dropped the other without a word.
    """
    document = yaml.safe_load(CONTROL_MUTATIONS.read_text(encoding="utf-8"))
    entries: list[dict[str, str]] = document["controls"]
    assert entries, "control-mutations.yaml declares no controls, so the gate verifies nothing"
    return entries


def test_every_mutation_names_a_registered_control() -> None:
    """The spec file and the register are two lists, so something has to compare
    them. D101's rule: a list beside a table is a list that drifts."""
    registered = _registered_controls()
    unknown = sorted(e["control"] for e in _mutations() if e["control"] not in registered)
    assert not unknown, (
        "control-mutations.yaml drives controls CONTROL-REGISTER.md does not name:\n  "
        + "\n  ".join(unknown)
    )
    defined = _defined_test_names()
    absent = sorted(e["control"] for e in _mutations() if e["control"] not in defined)
    assert not absent, "control-mutations.yaml names tests that do not exist:\n  " + "\n  ".join(
        absent
    )


def _stale_mutation_anchors(entries: list[dict[str, str]], root: Path) -> list[str]:
    """Every mutation whose `find` no longer resolves to exactly one line under `root`.

    A function rather than a loop inside the check, so the control can hand it
    entries whose anchors it has broken on purpose. It was inline, and the
    control beside it re-counted a list it had built itself -- the shape this
    whole register exists to find, written into the register's own guard on the
    day the register was written. With `hits` pinned to 1 so no anchor could
    ever be reported stale, the check passed and that control passed with it.
    """
    stale: list[str] = []
    for body in entries:
        control = f"{body['control']} ({body['file']})"
        path = root / body["file"]
        if not path.is_file():
            stale.append(f"{control}: {body['file']} is not a file under {root}")
            continue
        lines = [line.rstrip() for line in path.read_text(encoding="utf-8").splitlines()]
        hits = lines.count(body["find"].rstrip())
        if hits != 1:
            stale.append(f"{control}: `find` matches {hits} lines in {body['file']}")
    return stale


def test_every_mutation_find_line_is_present_exactly_once() -> None:
    """A mutation anchored to a line that has moved is a gate that stops firing.

    This is not hypothetical and it is not a rare edit: `ruff format` collapsed
    `_SWEPT` onto one line during the sweep that wrote these entries, and the
    anchor for the control-character mutation stopped matching. The tool
    refuses that case loudly, but only when it is run; a formatter runs on
    every commit. Asserting it here means the anchor is checked by the suite.

    Exactly once, not at least once. `    return problems` also matches
    `    return problems, compared` under substring rules, which is why the
    tool compares whole lines and why this does too.
    """
    stale = _stale_mutation_anchors(_mutations(), REPO_ROOT)
    assert not stale, (
        "these mutations are anchored to lines that have moved, so the gate would refuse "
        "to run rather than verify them:\n  " + "\n  ".join(stale)
    )


def test_the_mutation_spec_would_notice_an_anchor_that_moved(tmp_path: Path) -> None:
    """The control on the two checks above.

    Both compare counts, and a comparison over an empty spec passes by reading
    nothing. This plants the two failure modes the anchor check exists for -- a
    line that has moved, and one that matches in two places -- and requires the
    counting to report each.
    """
    entries = _mutations()
    assert len(entries) >= 2, "too few mutations for this control to mean anything"
    assert _stale_mutation_anchors(entries, REPO_ROOT) == [], (
        "the shipped anchors do not resolve, so this control cannot tell a planted "
        "failure from the state of the tree"
    )

    # A file this control writes, so the two failure modes are real rather than
    # asserted about a list built here. Re-counting a literal is what the first
    # version of this control did, and it passed with the counting pinned to 1.
    (tmp_path / "sample.py").write_text("alpha = 1\nrepeated = 2\nrepeated = 2\n", encoding="utf-8")
    planted = [
        {"control": "control_whose_anchor_moved", "file": "sample.py", "find": "gone = 0"},
        {"control": "control_whose_anchor_is_doubled", "file": "sample.py", "find": "repeated = 2"},
        {"control": "control_whose_anchor_resolves", "file": "sample.py", "find": "alpha = 1"},
        {"control": "control_whose_file_is_absent", "file": "no-such-file.py", "find": "alpha = 1"},
    ]
    reported = _stale_mutation_anchors(planted, tmp_path)
    named = " ".join(reported)
    assert "control_whose_anchor_moved" in named, f"an anchor matching nothing passed: {reported}"
    assert "control_whose_anchor_is_doubled" in named, (
        f"an anchor matching two lines passed, and substring drift is how it happens: {reported}"
    )
    assert "control_whose_file_is_absent" in named, f"a missing file passed: {reported}"
    assert "control_whose_anchor_resolves" not in named, (
        f"an anchor that resolves exactly once was reported stale: {reported}"
    )
