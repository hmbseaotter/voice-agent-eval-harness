"""Tests for the interface scanner.

The scanner is the deliverable D15 chose over repairing a third instance of a
defect class, and this repository's own build prompt says an unverified guard is
worse than none, because it is relied upon. It was written and hand-checked and
then had no tests at all — 200-odd lines carrying two regex families and a
negation subtlety its own comment documents at length.

Four of these tests exist for specific past failures rather than for coverage:

- the removed-pattern regression, because a previous pattern fired on the
  sentence *resolving* the problem it detects ("No format adapter is needed");
- the retired-claim case, because a struck sentence with a supersede note is the
  correct way to close a stale cross-claim, and a detector that punishes the
  repair trains people not to make it;
- the widened-universe case, because instance four of the class was found by a
  human concatenating one more file per side by hand;
- the list-sentence case, because the tool's `cuts` subcommand once stood in for
  the `cuts` field its field list did not name (P4-17, D178).
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest
from tools.check_spec_interface import (
    FINDINGS_KEYS,
    HARNESS_ONLY_KEYS,
    HARNESS_SENTENCES,
    LISTS,
    SEVERITY_FIELDS,
    SEVERITY_ROW_FIELDS,
    TOOL_SENTENCES,
    _live_text,
    check,
    check_lists,
    listed_names,
)

from harness.core.findings import REQUIRED_KEYS
from harness.core.severity import SEVERITY_FIELDS as LIBRARY_SEVERITY_FIELDS
from harness.core.severity import SEVERITY_ROW_FIELDS as LIBRARY_SEVERITY_ROW_FIELDS

REPO_ROOT = Path(__file__).resolve().parents[1]
SCANNER = REPO_ROOT / "tools" / "check_spec_interface.py"

#: Imported, never retyped. A test that re-declares the constant it is testing
#: agrees with itself and with nothing else -- and this file held its own copy
#: of both lists, so one interface existed in three places and the other in
#: three more. The severity triple happened to agree; the findings triple did
#: not, and no test could have said so.
KEYS = FINDINGS_KEYS
HARNESS_KEYS = (*FINDINGS_KEYS, *HARNESS_ONLY_KEYS)
FIELDS = SEVERITY_FIELDS
ROWS = SEVERITY_ROW_FIELDS


def _named(names: tuple[str, ...]) -> str:
    return ", ".join(f"`{name}`" for name in names)


def _harness(
    *,
    keys: tuple[str, ...] = HARNESS_KEYS,
    fields: tuple[str, ...] = FIELDS,
    rows: tuple[str, ...] = ROWS,
    extra: str = "",
) -> str:
    """A harness-side specification whose list sentences name exactly what is given.

    Built on the phrases `HARNESS_SENTENCES` opens its lists with, so the fixture
    moves with the scanner rather than restating it.
    """
    findings = HARNESS_SENTENCES["findings keys"].opens
    fields_opens = HARNESS_SENTENCES["severity file fields"].opens
    rows_opens = HARNESS_SENTENCES["severity row fields"].opens
    return (
        f"- The system {findings} requiring on every entry {_named(keys)}.\n"
        f"- The tool emits a separate severity file keyed by finding id, {fields_opens} "
        f"{_named(fields)}, {rows_opens} {_named(rows)}.\n"
        f"{extra}"
    )


def _tool(
    *,
    keys: tuple[str, ...] = KEYS,
    fields: tuple[str, ...] = FIELDS,
    rows: tuple[str, ...] = ROWS,
    extra: str = "",
) -> str:
    """A tool-side specification whose list sentences name exactly what is given."""
    reader = TOOL_SENTENCES["findings keys"]
    fields_opens = TOOL_SENTENCES["severity file fields"].opens
    rows_opens = TOOL_SENTENCES["severity row fields"].opens
    return (
        f"- [P1] {reader.opens} — each entry carrying {_named(keys)} — {reader.closes} "
        "keyed by finding id.\n"
        f"- WHEN a severity file is written, the system {fields_opens} {_named(fields)}.\n"
        f"- WHEN a severity file is written, the system {rows_opens} {_named(rows)}.\n"
        f"{extra}"
    )


def _run(harness: str, tool: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCANNER), harness, tool],
        capture_output=True,
        text=True,
        check=False,
    )


#: Writes a named file into the test's own directory and hands back its path.
#: Named for the two *sides* the scanner compares -- a harness-side document and
#: a tool-side one.
SideWriter = Callable[[str, str], str]


@pytest.fixture
def side(tmp_path: Path) -> SideWriter:
    def write(name: str, body: str) -> str:
        path = tmp_path / name
        path.write_text(body, encoding="utf-8")
        return str(path)

    return write


class TestAgreement:
    def test_a_matching_pair_passes(self, side: SideWriter) -> None:
        result = _run(side("h.md", _harness()), side("t.md", _tool()))
        assert result.returncode == 0, result.stderr
        assert "OK" in result.stdout


class TestDisagreement:
    def test_a_missing_findings_key_fails_and_names_it(self, side: SideWriter) -> None:
        short = _harness(keys=tuple(k for k in HARNESS_KEYS if k != "detectable_by"))
        result = _run(side("h.md", short), side("t.md", _tool()))
        assert result.returncode == 1
        assert "detectable_by" in result.stderr
        assert "harness" in result.stderr

    def test_a_missing_severity_field_fails_and_names_it(self, side: SideWriter) -> None:
        """The field set is the part a consumer actually reads provenance from."""
        short = _harness(fields=tuple(f for f in FIELDS if f != "calibration"))
        result = _run(side("h.md", short), side("t.md", _tool()))
        assert result.returncode == 1
        assert "calibration" in result.stderr
        assert "producer" in result.stderr

    def test_a_missing_row_field_fails_and_names_it(self, side: SideWriter) -> None:
        short = _tool(rows=tuple(r for r in ROWS if r != "theta"))
        result = _run(side("h.md", _harness()), side("t.md", short))
        assert result.returncode == 1
        assert "severity row field `theta` is named in the harness side's list" in result.stderr

    def test_a_key_named_in_neither_side_fails(self, side: SideWriter) -> None:
        harness = _harness(keys=tuple(k for k in HARNESS_KEYS if k != "tier"))
        tool = _tool(keys=tuple(k for k in KEYS if k != "tier"))
        result = _run(side("h.md", harness), side("t.md", tool))
        assert result.returncode == 1
        assert "named in neither side" in result.stderr

    def test_severity_backfilled_into_the_findings_document_fails(self, side: SideWriter) -> None:
        body = _harness(extra="Severity is backfilled into the findings document.\n")
        result = _run(side("h.md", body), side("t.md", _tool()))
        assert result.returncode == 1
        assert "backfilled" in result.stderr

    def test_a_stale_cross_claim_fails(self, side: SideWriter) -> None:
        body = _tool(extra="The harness spec names no format for its findings document.\n")
        result = _run(side("h.md", _harness()), side("t.md", body))
        assert result.returncode == 1
        assert "stale cross-claim" in result.stderr


class TestTheRemovedPattern:
    def test_the_sentence_resolving_the_defect_does_not_fire(self, side: SideWriter) -> None:
        """A detector that fires on its own fix trains the reader to ignore it.

        An earlier pattern matched `format adapter is needed` and so fired
        inside "No format adapter is needed" — the sentence recording that the
        problem was solved. The pattern was removed rather than negated, and
        this test is what keeps it removed.
        """
        body = _harness(extra="No format adapter is needed: both sides settled YAML.\n")
        result = _run(side("h.md", body), side("t.md", _tool()))
        assert result.returncode == 0, result.stderr


class TestRetiredClaims:
    def test_a_struck_stale_claim_with_a_supersede_note_passes(self, side: SideWriter) -> None:
        """Striking a claim and explaining why is the repair, not a violation."""
        body = _tool(
            extra=(
                "~~This settles a gap in the harness spec, which names no format.~~ "
                "**Discharged.** Both sides now name YAML.\n"
            )
        )
        result = _run(side("h.md", _harness()), side("t.md", body))
        assert result.returncode == 0, result.stderr

    def test_the_same_claim_unstruck_still_fails(self, side: SideWriter) -> None:
        """The retirement must be marked, not merely intended."""
        body = _tool(extra="This settles a gap in the harness spec, which names no format.\n")
        result = _run(side("h.md", _harness()), side("t.md", body))
        assert result.returncode == 1

    def test_a_quoted_stale_claim_does_not_fire(self, side: SideWriter) -> None:
        """A record explaining a stale claim has to reproduce it.

        The tool's D15 quotes the exact sentence whose staleness justified
        building this script. Firing there is the removed pattern's defect
        wearing different clothes — the detector going off on the text that
        documents the problem. Found by pointing this script at the decision
        records for the first time, which is the widening that also found
        instance four.
        """
        body = _tool(
            extra=(
                'One instance was a stale assertion that the harness "names no format" '
                "for its findings document, found in a sweep after it had named one.\n"
            )
        )
        result = _run(side("h.md", _harness()), side("t.md", body))
        assert result.returncode == 0, result.stderr


class TestWidenedUniverse:
    def test_a_key_stated_only_in_a_second_file_does_not_count(self, side: SideWriter) -> None:
        """A list is what its sentence in the specification says (D178).

        This test used to assert the opposite: a key stated only in a decision
        record counted for that side, because instance four forced the scanner to
        read every document and a record legitimately does not repeat every key.
        That was right for the claims and wrong for the lists -- it is the same
        rule that let a subcommand's name stand in for a field (P4-17). The claims
        still read every file; the next test is what holds that half.
        """
        spec = _harness(keys=tuple(k for k in HARNESS_KEYS if k != "tier"))
        record = "The `tier` field excludes questions from the anchor set.\n"
        result = _run(
            f"{side('h.md', spec)},{side('h-dec.md', record)}",
            side("t.md", _tool()),
        )
        assert result.returncode == 1
        assert "findings key `tier` is named in the tool side's list" in result.stderr

    def test_a_stale_claim_in_a_second_file_is_caught(self, side: SideWriter) -> None:
        """The finding that motivated the change: it lived in a decision record."""
        result = _run(
            side("h.md", _harness()),
            f"{side('t.md', _tool())},"
            f"{side('t-dec.md', 'the harness names no format for its findings document')}",
        )
        assert result.returncode == 1
        assert "stale cross-claim" in result.stderr


class TestUsage:
    def test_no_arguments_is_a_usage_error(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCANNER)], capture_output=True, text=True, check=False
        )
        assert result.returncode == 2

    def test_a_missing_file_is_a_usage_error_naming_it(self, side: SideWriter) -> None:
        result = _run(side("h.md", _harness()), "does-not-exist.md")
        assert result.returncode == 2
        assert "does-not-exist.md" in result.stderr

    def test_an_empty_side_is_a_usage_error(self, side: SideWriter) -> None:
        result = _run(side("h.md", _harness()), ",")
        assert result.returncode == 2


class TestTheRealDocuments:
    def test_the_two_repositories_agree_right_now(self) -> None:
        """Not a unit test — the check itself, run over the live documents.

        Skipped rather than failed when the sibling repository is absent, since
        a clone of this repo alone is a legitimate state.

        **Two layouts, because this looked in one and ran in neither.** It
        checked only `../comparative-judgment`, which is a working copy's shape
        and not CI's: the workflow checks the sibling out *inside* the workspace
        at `comparative-judgment/`. So this test ran on one machine and skipped
        every CI run, while the workflow step above cited it as the reason a
        failed checkout was safe to tolerate — "the scanner's own test skips when
        the checkout is absent rather than failing. That skip is visible in the
        test output." The skip was visible and meant nothing, because it was
        unconditional there. D84's fourth instance, and the sharpest: a check
        whose trigger could not be satisfied in the environment it guarded.
        """
        root = Path(__file__).resolve().parents[1]
        tool = next(
            (
                candidate / "comparative-judgment" / "specs"
                for candidate in (root.parent, root)
                if (candidate / "comparative-judgment" / "specs").is_dir()
            ),
            None,
        )
        if tool is None:
            pytest.skip(
                "comparative-judgment is checked out neither beside this repository "
                "nor inside it; the live-document comparison did not run"
            )
        harness_side = ",".join(
            str(root / "specs" / name)
            for name in (
                "voice-agent-eval-harness.md",
                "voice-agent-eval-harness.decisions.md",
                "voice-agent-eval-harness.build-prompt.md",
            )
        )
        tool_side = ",".join(
            str(tool / name)
            for name in ("comparative-judgment.md", "comparative-judgment.decisions.md")
        )
        result = _run(harness_side, tool_side)
        assert result.returncode == 0, result.stderr


# --------------------------------------------------------------------------
# A list is what its sentence says (P4-17, D178)
# --------------------------------------------------------------------------
#
# Module-level rather than in a class, because `tools/verify_controls.py`
# addresses a control as `<module>::<name>` and each of these is one.


def test_a_field_named_only_outside_its_list_does_not_count(side: SideWriter) -> None:
    """P4-17, planted. The tool's field list once lacked `cuts` while two of its
    criteria named the `cuts` subcommand, and a scanner matching a name anywhere
    reported agreement on a field the producer's list did not carry."""
    tool = _tool(
        fields=tuple(f for f in FIELDS if f != "cuts"),
        extra="- [ ] [P1] `cuts` naming an unknown finding leaves `cuts.json` byte-identical.\n",
    )
    result = _run(side("h.md", _harness()), side("t.md", tool))
    assert result.returncode == 1
    assert (
        "severity file field `cuts` is named in the harness side's list but not the tool side's"
        in result.stderr
    )


def test_a_list_sentence_that_is_gone_fails_and_names_it(side: SideWriter) -> None:
    """Reworded away, a list sentence must turn the check red, not quiet."""
    opens = TOOL_SENTENCES["severity file fields"].opens
    tool = _tool().replace(opens, "SHALL record these fields:")
    result = _run(side("h.md", _harness()), side("t.md", tool))
    assert result.returncode == 1
    assert "severity file fields sentence states" in result.stderr
    assert "0 times" in result.stderr


def test_a_list_sentence_stated_twice_fails(side: SideWriter) -> None:
    opens = HARNESS_SENTENCES["severity file fields"].opens
    harness = _harness(extra=f"- A second severity sentence, {opens} `run_id`.\n")
    result = _run(side("h.md", harness), side("t.md", _tool()))
    assert result.returncode == 1
    assert "2 times" in result.stderr


def test_an_extra_name_in_a_list_fails_and_names_it(side: SideWriter) -> None:
    tool = _tool(fields=(*FIELDS, "confidence"))
    result = _run(side("h.md", _harness()), side("t.md", tool))
    assert result.returncode == 1
    assert "`confidence`, which this scanner does not expect" in result.stderr


def test_a_struck_earlier_list_beside_the_live_one_passes(side: SideWriter) -> None:
    """A superseded list kept struck through, as this project keeps history, is not
    a second list."""
    opens = TOOL_SENTENCES["severity file fields"].opens
    struck = f"~~The system {opens} {_named(FIELDS[:-1])}.~~ **Superseded at schema 3.**\n"
    result = _run(side("h.md", _harness()), side("t.md", _tool(extra=struck)))
    assert result.returncode == 0, result.stderr


def test_a_record_repeating_a_list_sentence_does_not_double_it(side: SideWriter) -> None:
    """Lists are read from each side's specification, the first file named. A
    decision record quoting a list sentence is history, not a second list -- on
    either side."""
    result = _run(
        f"{side('h.md', _harness())},{side('h-dec.md', _harness())}",
        f"{side('t.md', _tool())},{side('t-dec.md', _tool())}",
    )
    assert result.returncode == 0, result.stderr


def test_a_matching_pair_of_lists_agrees_exactly() -> None:
    """Each list is read from its own span. The harness's field list stops where its
    row list opens, and its findings list sets the harness-only keys aside; read
    past that close, or with those keys left in, the pair disagrees with itself."""
    assert check_lists(_harness(), _tool()) == []


def test_a_missing_key_reaches_the_whole_check() -> None:
    """The list comparison is part of the check a run reports, not a function beside it."""
    harness = _harness(keys=tuple(k for k in HARNESS_KEYS if k != "detectable_by"))
    tool = _tool()
    problems = check(harness, tool, harness_specification=harness, tool_specification=tool)
    assert any("findings key `detectable_by`" in problem for problem in problems), problems


def test_a_key_in_neither_list_is_named_as_missing_from_both() -> None:
    harness = _harness(keys=tuple(k for k in HARNESS_KEYS if k != "tier"))
    tool = _tool(keys=tuple(k for k in KEYS if k != "tier"))
    assert "findings key `tier` is named in neither side's list" in check_lists(harness, tool)


# --------------------------------------------------------------------------
# The drift detector's own drift detector
# --------------------------------------------------------------------------


def test_the_shared_and_harness_only_keys_partition_the_loaders_list() -> None:
    """One interface, three copies, none bound to the others.

    `harness.core.findings.REQUIRED_KEYS` had eight keys; this scanner named
    six; this test file re-declared the same six as a literal. Nothing asserted
    any pair equal, and the severity triple agreed only by luck.

    The six are not stale -- they are the keys that cross the repository
    boundary, and the severity tool has no use for which call a finding came
    from or whose defect it is. But a subset that exists only as the difference
    between two hand-maintained tuples is indistinguishable from a stale copy,
    which is exactly how an independent audit read it. This asserts the
    partition, so adding a key to the loader forces the choice instead of
    widening a gap nobody can see.
    """
    assert set(FINDINGS_KEYS) | set(HARNESS_ONLY_KEYS) == set(REQUIRED_KEYS)
    assert not set(FINDINGS_KEYS) & set(HARNESS_ONLY_KEYS)
    assert set(HARNESS_ONLY_KEYS) == {"call_ref", "owner"}, (
        "the harness-only set changed; say why in the scanner's comment and here"
    )


def test_the_scanner_and_the_library_agree_about_severity_fields() -> None:
    """The other half of the same shape. This triple agrees today and nothing
    made it agree.

    **Both populations, because schema 2 added a second one.** The row fields
    arrived in the scanner alone and this test refused the result, correctly:
    the library's top-level tuple is what the loader requires beside `run_id`,
    and a `content_hash` demanded there would reject every file the producing
    tool writes. They are separate tuples on both sides now, and both are
    asserted -- a row field renamed by the producer is as invisible to this
    project as a top-level one.
    """
    assert SEVERITY_FIELDS == LIBRARY_SEVERITY_FIELDS
    assert SEVERITY_ROW_FIELDS == LIBRARY_SEVERITY_ROW_FIELDS


def test_every_list_has_a_sentence_on_both_sides() -> None:
    """A list the scanner compares must be located on both sides, or its
    comparison is a key lookup away from never running."""
    labels = {label for label, _noun, _expected in LISTS}
    assert set(HARNESS_SENTENCES) == labels
    assert set(TOOL_SENTENCES) == labels


def test_the_harness_specification_lists_exactly_what_the_scanner_reads() -> None:
    """The harness half of the live comparison, with no sibling needed.

    The live-document comparison skips when comparative-judgment is absent; this
    does not, so a harness list sentence reworded away, doubled or thinned fails in
    a clone of this repository alone.
    """
    spec = (REPO_ROOT / "specs" / "voice-agent-eval-harness.md").read_text(encoding="utf-8")
    expected = {
        "findings keys": set(REQUIRED_KEYS),
        "severity file fields": set(SEVERITY_FIELDS),
        "severity row fields": set(SEVERITY_ROW_FIELDS),
    }
    for label, sentence in HARNESS_SENTENCES.items():
        names = listed_names(spec, sentence)
        assert not isinstance(names, str), f"the specification's {label} sentence {names}"
        assert names == expected[label], (
            f"the specification's {label} sentence names {sorted(names)}; "
            f"the scanner reads {sorted(expected[label])}"
        )


def test_the_specification_names_every_key_the_loader_requires() -> None:
    """`owner` and `call_ref` were enforced by the loader and required by
    nothing in the specification -- not in scope, not in a SHALL, not in an
    acceptance criterion. A findings document built to the specification was
    rejected by the code implementing it, and the acceptance criterion for the
    key set enumerated six of the eight.

    Asserted against the SHALL line and the criterion rather than the whole
    document, because the whole document mentions keys in passing and a
    substring search over all of it would pass on a changelog paragraph -- which
    is where `owner` was, and why nobody noticed.
    """
    spec = (REPO_ROOT / "specs" / "voice-agent-eval-harness.md").read_text(encoding="utf-8")
    requirement = next(
        line
        for line in spec.splitlines()
        if "SHALL [P1] read the findings document as YAML" in line
    )
    criterion = next(line for line in spec.splitlines() if "Every findings entry carries" in line)
    for line, label in ((requirement, "the SHALL"), (criterion, "the acceptance criterion")):
        missing = [key for key in REQUIRED_KEYS if f"`{key}`" not in line]
        assert not missing, f"{label} does not name {', '.join(missing)}"


def test_the_quote_stripping_does_not_swallow_the_document() -> None:
    """T10. `_QUOTED` treats a bare apostrophe as a quote delimiter, so
    `the tool's ... the harness's` blanks everything between them.

    That makes `STALE_CROSS_CLAIMS` fail **open**: the sentence a pattern was
    written to catch can be removed from the text before the pattern ever sees
    it. Measured on the live harness specification, the loss is small; it is
    unbounded in principle, and it is bounded by nothing but the incidence of
    possessives.

    Pinned as a fraction rather than fixed, because the pattern also does real
    work -- a decision record explaining a stale claim has to reproduce it, and
    firing there is the false positive that gets a detector switched off. If
    this ever rises, the fix is to require a non-word character before an
    opening quote, not to raise the number.
    """
    raw = (REPO_ROOT / "specs" / "voice-agent-eval-harness.md").read_text(encoding="utf-8")
    live = _live_text(raw)
    before = len(re.sub(r"\s", "", raw))
    after = len(re.sub(r"\s", "", live))
    stripped = (before - after) / before
    assert stripped < 0.06, (
        f"{stripped:.1%} of the specification is stripped before the stale-claim "
        "patterns see it; the quote rule is swallowing possessives"
    )


def test_the_stale_claim_patterns_still_have_a_document_to_read() -> None:
    """The other half. A `_live_text` that returned nothing would make every
    stale-claim pattern pass by having nothing to match against, and the scanner
    would report OK over an empty string."""
    raw = (REPO_ROOT / "specs" / "voice-agent-eval-harness.md").read_text(encoding="utf-8")
    live = _live_text(raw)
    assert len(live) > len(raw) * 0.5, "more than half the document was stripped"
    for token in ("severity", "findings", "`id`"):
        assert token in live, f"{token!r} did not survive _live_text"
