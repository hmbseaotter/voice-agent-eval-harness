"""The held-out absence check, proven against true positives.

This check is the only mechanism protecting the held-out set, and a detector
that has only ever returned "clean" has been proven against nothing. The
specification makes the same point about the citation validator at P3: assert
the detector against a fabricated positive, so it is *proven* rather than
assumed.

**No real held-out transcript is copied here, at any point.** The positives are
synthesized in a temporary directory outside the repository: text carrying the
format header and an undeclared `call_id`. Copying a genuine held-out file into
this tree to test the check that forbids held-out files in this tree would be a
self-defeating test, and the copy would be in the working tree for as long as
the test ran.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest
import yaml
from tools import check_holdout_absence
from tools.check_holdout_absence import (
    _FORMAT_MARKER,
    _MARKER_WINDOW,
    _MAX_BYTES,
    declared_design_set,
    declared_fixture_set,
    declared_held_out_set,
    main,
    scan,
    scan_agreement_sections,
    scan_coverage_reports,
    scan_labels,
    scan_reports,
    scan_run_logs,
    scan_unreadable,
)

from harness.agreement import SetAgreement, render_set
from harness.core.artifact import build_payload, write_artifact
from harness.core.findings import Finding, dump_findings, load_findings, render_markdown
from harness.core.severity import BAND_ORDER, SeverityRecord
from harness.corpus.text_adapter import parse_call
from harness.coverage import BandCoverage, FindingCoverage, SetCoverage, render_coverage
from harness.extract import extract

REPO_ROOT: Path = Path(__file__).resolve().parents[1]

#: A held-out-shaped transcript. Synthesized, not copied: the call id is one the
#: companion repository uses, and everything else is invented for this test.
#:
#: **The header is built from the scanner's own marker rather than copied.**
#: Two reasons, and the second is the one that bit. A copy can drift from the
#: constant it is meant to imitate, so a format change would leave this fixture
#: testing the old shape. And once the scan learned to look for the marker
#: anywhere in a file rather than only on line 1, a verbatim marker in this file
#: made *this file* a held-out transcript in the working tree -- the scan
#: reported it, correctly. Interpolating the constant means the file carries a
#: call id and a template, which is not a transcript, while the fixture the test
#: writes to disk is exactly one.
#:
#: It is written in the **current** format, deliberately. A fixture frozen at an
#: older version stops resembling the thing it stands in for, and then the check
#: is proven against a shape no held-out file has.
SYNTHETIC_HELDOUT: str = f"""{_FORMAT_MARKER} v2

[call]
call_id: CALL-13
agent_id: fixture
agent_version: 0
environment: test
direction: inbound
from_number: +1 (415) 555-0101
to_number: +1 (415) 555-0100
started_at: 2027-01-01T00:00:00.000Z
answered_at: 2027-01-01T00:00:01.000Z
ended_at: 2027-01-01T00:01:00.000Z
duration_ms: 60000
disconnection_reason: caller_hangup
outcome: resolved
outcome_reason: information_provided

[context]
# none

[events]
  1 |  0:01.000 |  0:01.000 | SYSTEM      | call.answered
  2 |  0:01.500 |  0:04.900 | CALLER      | Synthetic. Not a real held-out transcript.
"""


def test_the_fixture_is_a_transcript_the_current_parser_accepts(tmp_path: Path) -> None:
    """The fixture claims to be held-out-shaped. Nothing about a string literal
    makes that true, and the version it was written against has already moved
    once. Parsing it is what keeps the claim honest: when the format changes
    and the fixture does not, this fails instead of the fixture quietly
    becoming a shape no held-out transcript has."""
    path = tmp_path / "CALL-13.txt"
    path.write_text(SYNTHETIC_HELDOUT, encoding="utf-8", newline="")
    call = parse_call(path)
    assert call.record.call_id == "CALL-13"
    assert call.events, "the fixture parses to no events"


def test_the_repository_currently_holds_only_what_it_declares() -> None:
    assert main() == 0


def test_the_design_and_fixture_sets_do_not_overlap() -> None:
    assert not set(declared_design_set()) & set(declared_fixture_set())


def test_a_held_out_transcript_in_the_tree_is_found(tmp_path: Path) -> None:
    """Planted with an id taken from `HELDOUT_SET` rather than written here.

    This named `CALL-13` as a literal. That is the first member of a set that
    has grown once already, and a literal would go on passing if the set were
    renumbered entirely -- proving that *some* transcript is found, which is not
    what the test claims. The declaration is what the tool reads, so it is what
    the test should plant from.
    """
    held_out = declared_held_out_set()
    assert held_out, "HELDOUT_SET declares nothing, so this test plants nothing"
    call_id = held_out[0]

    (tmp_path / "corpus" / "transcripts").mkdir(parents=True)
    (tmp_path / "corpus" / "transcripts" / f"{call_id}.txt").write_text(
        SYNTHETIC_HELDOUT.replace("CALL-13", call_id), encoding="utf-8", newline=""
    )
    found = scan(tmp_path)
    assert call_id in found
    assert call_id not in declared_design_set()
    assert call_id not in declared_fixture_set()


def test_a_held_out_id_is_reported_as_held_out_and_not_merely_undeclared(tmp_path: Path) -> None:
    """The two cases need different words, and had the same ones.

    A file carrying a held-out id and a file carrying an id nobody has declared
    are not the same event. The first means delete this and treat every session
    that opened it as contaminated; the second means somebody forgot a
    declaration. The check reported both as "declared neither in DESIGN_SET nor
    FIXTURE_SET", which is true of a held-out transcript and buries what it is.

    Both branches are asserted, because a message that fires on everything
    tells a reader nothing -- the same reason the undeclared case is still
    reported at all.
    """
    held_out = declared_held_out_set()
    assert held_out, "HELDOUT_SET declares nothing"

    (tmp_path / "corpus" / "transcripts").mkdir(parents=True)
    (tmp_path / "corpus" / "transcripts" / "one.txt").write_text(
        SYNTHETIC_HELDOUT.replace("CALL-13", held_out[0]), encoding="utf-8", newline=""
    )
    (tmp_path / "corpus" / "transcripts" / "two.txt").write_text(
        SYNTHETIC_HELDOUT.replace("CALL-13", "CALL-97"), encoding="utf-8", newline=""
    )
    found = scan(tmp_path)
    assert held_out[0] in found and "CALL-97" in found

    assert held_out[0] not in declared_design_set(), "the plant is a declared design call"
    assert "CALL-97" not in declared_held_out_set(), (
        "the undeclared plant is in HELDOUT_SET, so both branches would take the same path"
    )


def test_renaming_the_file_does_not_hide_it(tmp_path: Path) -> None:
    """A filename check is defeated by a rename, which is exactly what someone
    would do while 'just having a quick look'. The scan reads line 1 instead."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "meeting-notes.md").write_text(
        SYNTHETIC_HELDOUT, encoding="utf-8", newline=""
    )
    assert "CALL-13" in scan(tmp_path)


def test_a_copy_stashed_under_private_is_found(tmp_path: Path) -> None:
    """`private/` is gitignored, which is precisely why it is scanned: a stashed
    copy is still a copy, and that is where one would be stashed."""
    (tmp_path / "private").mkdir()
    (tmp_path / "private" / "scratch.txt").write_text(
        SYNTHETIC_HELDOUT, encoding="utf-8", newline=""
    )
    assert "CALL-13" in scan(tmp_path)


def test_tool_generated_trees_are_skipped(tmp_path: Path) -> None:
    """The skip list holds only directories with no authored content. If it ever
    grows to include one that does, this is where that shows up."""
    for skipped in (".git", ".venv", "__pycache__", ".pytest_cache"):
        (tmp_path / skipped).mkdir()
        (tmp_path / skipped / "copy.txt").write_text(
            SYNTHETIC_HELDOUT, encoding="utf-8", newline=""
        )
    assert scan(tmp_path) == {}


def test_the_projects_own_output_directory_is_not_a_hiding_place(tmp_path: Path) -> None:
    """`build/` was on the skip list and this test asserted the exemption, so
    the hiding place was a pinned property.

    It does not belong there. The other entries are tool-generated trees nobody
    authors into; `build/` is gitignored, writable, and the harness's own output
    directory -- which is D37's argument exactly: skipping a directory creates
    the hiding place the scan exists to deny.
    """
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "copy.txt").write_text(SYNTHETIC_HELDOUT, encoding="utf-8", newline="")
    assert "CALL-13" in scan(tmp_path)


def test_a_transcript_is_found_whatever_it_is_called(tmp_path: Path) -> None:
    """The scan read six suffixes while its docstring promised "under any name".

    Written as `.log`, `.bak`, `.py`, `.text`, `.rst` or `.csv`, a held-out
    transcript was invisible to all six. The allow list was the defect -- it has
    to enumerate every extension a person might type, and that is not a finite
    set -- so the polarity is inverted: everything is read except named binary
    formats.
    """
    names = ("notes.log", "copy.bak", "scratch.py", "x.text", "doc.rst", "a.csv", "no_suffix")
    for name in names:
        (tmp_path / name).write_text(SYNTHETIC_HELDOUT, encoding="utf-8", newline="")
    found = scan(tmp_path)
    assert "CALL-13" in found
    assert {path.name for path in found["CALL-13"]} == set(names)


def test_a_transcript_pasted_inside_another_file_is_found(tmp_path: Path) -> None:
    """The marker had to be on line 1, so a transcript pasted into a scratch
    script sat below a docstring and an import and was never seen. That is the
    "just having a quick look" move D2 exists to catch, and widening the suffix
    list alone would not have caught it -- two independent narrowings wore one
    docstring's promise."""
    (tmp_path / "scratch.py").write_text(
        '"""Poking at a transcript."""\n\nimport sys\n\nSAMPLE = """' + SYNTHETIC_HELDOUT + '"""\n',
        encoding="utf-8",
        newline="",
    )
    assert "CALL-13" in scan(tmp_path)


def test_documentation_quoting_the_marker_is_not_a_transcript(tmp_path: Path) -> None:
    """The false-positive half of looking for the marker anywhere. The format
    specification and the scanner both quote the marker while documenting it,
    and neither is a transcript. What separates them from a real one is the
    `call_id` that follows: documentation does not carry one."""
    (tmp_path / "transcript-format.md").write_text(
        "# The format\n\n```\n" + _FORMAT_MARKER + " v2\n\n[call]\n<key: value>\n```\n",
        encoding="utf-8",
    )
    assert scan(tmp_path) == {}


def test_a_transcript_file_with_no_call_id_is_still_reported(tmp_path: Path) -> None:
    """A marker on line 1 means the file *is* a transcript, whatever else is
    true of it. Stripping the `call_id` must not be a way through -- it is
    reported as unreadable rather than waved past."""
    header, _, rest = SYNTHETIC_HELDOUT.partition("call_id: CALL-13\n")
    (tmp_path / "anonymous.txt").write_text(header + rest, encoding="utf-8", newline="")
    assert "<unreadable call_id>" in scan(tmp_path)


def test_an_ordinary_file_is_not_mistaken_for_a_transcript(tmp_path: Path) -> None:
    """The false-positive half. A check that flagged ordinary files would be
    switched off within a week, and then it would protect nothing."""
    (tmp_path / "README.md").write_text("# A readme\n\ncall_id: CALL-13\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("Talked about CALL-13 today.\n", encoding="utf-8")
    assert scan(tmp_path) == {}


#: An invented labels manifest. It names no commit in any repository.
_INVENTED_MANIFEST: str = "0123456789abcdef" * 2 + "01234567"


def _run_log_line(record: dict[str, object]) -> str:
    """One run-log line, serialized the way the harness's writer serializes one.

    Built at run time rather than written out: a record typed into this file on
    one line would make this file carry what the run-log scan looks for, the trap
    `SYNTHETIC_HELDOUT` fell into once with the format marker.
    """
    return json.dumps(record, sort_keys=True) + "\n"


def _header(**extra: object) -> dict[str, object]:
    return {
        "record": "header",
        "rubric_version": "1",
        "prompt_template_hash": "a" * 64,
        "corpus_version": "0.0.0",
        "artifact_hash": "b" * 64,
        "mode": "live",
        "started_at": "2027-01-01T00:00:00Z",
        **extra,
    }


def _call(call_id: str) -> dict[str, object]:
    return {
        "record": "call",
        "call_id": call_id,
        "entry_id": "J-invented",
        "prompt": "[T1] Synthetic. Not a real held-out prompt.",
    }


#: A report as `harness.report.render_report` writes one, cut to the heading, the
#: provenance line and one row of the calls table. Synthesized like every positive
#: here: invented hashes, an invented entry, and whichever call id the test plants.
_REPORT_SHAPED: str = """# Evaluation report

rubric `1` | corpus `0.0.0` | extraction artifact `0000000000000000` | mode `replay`

## Calls

| call | what was found | what was not evaluated | owners to act |
|---|---|---|---|
| {call} | J-invented | everything applied | agent |
"""


def test_a_rendered_report_over_held_out_calls_is_found(tmp_path: Path) -> None:
    """A report naming a call `HELDOUT_SET` declares is held-out output wherever it
    sits and whatever it is called (D185).

    Its tables carry that call's verdicts, which are the judge's answers on a
    held-out call, and it carries neither the transcript marker nor a run-log record,
    so neither of the other two readings sees it.
    """
    held_out = declared_held_out_set()
    assert held_out, "HELDOUT_SET declares nothing, so this test plants nothing"
    pasted = tmp_path / "notes" / "scratch.md"
    pasted.parent.mkdir()
    pasted.write_text(_REPORT_SHAPED.format(call=held_out[0]), encoding="utf-8", newline="\n")
    found = scan_reports(tmp_path, frozenset(held_out))
    assert list(found) == [pasted], found
    assert held_out[0] in found[pasted]


def test_a_design_report_is_not_mistaken_for_a_held_out_one(tmp_path: Path) -> None:
    """The false-positive half, and the one this repository's own snapshot rests on.

    Three files carrying half of what marks a held-out report each: a report over a
    design call, a document quoting the heading with no call id, and a file naming a
    held-out call with no report around it. The heading and a declared call id are
    required together, which is what keeps `snapshots/report.md` and `HELDOUT_SET`
    out of this reading.
    """
    (tmp_path / "design-report.md").write_text(
        _REPORT_SHAPED.format(call=declared_design_set()[0]), encoding="utf-8", newline="\n"
    )
    (tmp_path / "doc.md").write_text(
        "The report opens with `# Evaluation report`, then its provenance line.\n",
        encoding="utf-8",
        newline="\n",
    )
    (tmp_path / "declaration.txt").write_text(
        declared_held_out_set()[0] + "\n", encoding="utf-8", newline="\n"
    )
    assert scan_reports(tmp_path, frozenset(declared_held_out_set())) == {}


def test_a_held_out_run_log_is_found_by_its_header(tmp_path: Path) -> None:
    """A header naming a labels manifest marks a held-out run's log (D173, D174).

    Only a held-out run writes one, so the header alone is enough -- in a whole log,
    and on a line of `grep` output pasted into a note, where it starts no line and so
    only the line reading sees it (D195 added a second reading, of JSON values that
    start a line, which reads the whole log too).
    """
    (tmp_path / "runs").mkdir()
    log = tmp_path / "runs" / "reference-heldout.jsonl"
    header = _run_log_line(_header(labels_manifest=_INVENTED_MANIFEST))
    log.write_text(header, encoding="utf-8", newline="")
    note = tmp_path / "note.txt"
    note.write_text("runs/reference-heldout.jsonl:1:" + header, encoding="utf-8", newline="")
    found = scan_run_logs(tmp_path, frozenset(declared_held_out_set()))
    assert set(found) == {log, note}, found
    assert "labels manifest" in found[log]
    assert "labels manifest" in found[note]


def test_a_held_out_call_record_is_found_wherever_it_is_pasted(tmp_path: Path) -> None:
    """A call record citing a call HELDOUT_SET declares, with no header, pasted into a
    scratch script and re-serialized compactly, is found (D174).

    Planted from the declaration rather than a literal, as the transcript tests are.
    """
    held_out = declared_held_out_set()
    assert held_out, "HELDOUT_SET declares nothing, so this test plants nothing"
    record = json.dumps(_call(held_out[0]), sort_keys=True, separators=(",", ":"))
    (tmp_path / "scratch.py").write_text(
        '"""Poking at a log."""\n\nimport json\n\nRECORD = ' + repr(record) + "\n",
        encoding="utf-8",
        newline="",
    )
    found = scan_run_logs(tmp_path, frozenset(held_out))
    assert held_out[0] in found.get(tmp_path / "scratch.py", ""), found


def test_a_design_run_log_is_not_mistaken_for_a_held_out_one(tmp_path: Path) -> None:
    """The false-positive half, and the one every design log in `runs/` rests on (D174).

    A design log has a header and call records, but its header names no manifest --
    a design run is refused the flag (D173) -- and its calls are design calls. A
    document naming the key in prose is not a header either.
    """
    lines = _run_log_line(_header()) + "".join(
        _run_log_line(_call(call_id)) for call_id in declared_design_set()
    )
    (tmp_path / "design.jsonl").write_text(lines, encoding="utf-8", newline="")
    (tmp_path / "notes.md").write_text(
        "The header's `labels_manifest` key names the manifest commit.\n", encoding="utf-8"
    )
    assert scan_run_logs(tmp_path, frozenset(declared_held_out_set())) == {}


def test_a_held_out_record_past_the_window_or_the_cap_is_still_found(tmp_path: Path) -> None:
    """The transcript scan's 64 KB window and 2 MB cap do not apply to run logs (D174).

    A design-size run log is 2.5 MB, so a cap would skip a held-out log unread, and a
    window would miss a record anywhere past its first 64 KB.
    """
    held_out = declared_held_out_set()
    assert held_out, "HELDOUT_SET declares nothing"
    padding = _run_log_line(_call(declared_design_set()[0]))
    record = _run_log_line(_call(held_out[0]))
    late = tmp_path / "late.jsonl"
    late.write_text(
        padding * (_MARKER_WINDOW // len(padding) + 1) + record, encoding="utf-8", newline=""
    )
    large = tmp_path / "large.jsonl"
    large.write_text(
        padding * (_MAX_BYTES // len(padding) + 1) + record, encoding="utf-8", newline=""
    )
    assert late.stat().st_size < _MAX_BYTES < large.stat().st_size
    found = scan_run_logs(tmp_path, frozenset(held_out))
    assert set(found) == {late, large}, found


def test_the_check_reports_a_held_out_run_log_in_the_tree_it_scans(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The check itself, not only the scan: a held-out log fails it, in a held-out
    transcript's words (D174).

    Run over a planted tree that holds no design transcript, so the check fails for
    that as well; what is asserted is the line naming the log.
    """
    (tmp_path / "private").mkdir()
    (tmp_path / "private" / "copy.jsonl").write_text(
        _run_log_line(_header(labels_manifest=_INVENTED_MANIFEST)), encoding="utf-8", newline=""
    )
    monkeypatch.setattr(check_holdout_absence, "REPO_ROOT", tmp_path)
    assert main() == 1
    err = capsys.readouterr().err
    assert "private/copy.jsonl carries a run-log header naming a labels manifest" in err, err


#: An invented held-out finding's id, assembled rather than written out, so this file
#: carries the pieces of one and never a whole one beside a heading.
_HELD_OUT_ID: str = "H" + "F-07"


def _coverage_section(name: str, finding_id: str) -> str:
    """A section as `harness.coverage.render_coverage` writes one, over a single
    invented finding carrying `finding_id` in the critical band (D188).

    Rendered by the shipped renderer rather than typed out, so the heading the check
    looks for is the one the command prints, and a renamed heading turns these tests
    red rather than leaving the check reading a shape nothing writes.
    """
    borrowed = replace(load_findings(REPO_ROOT / "corpus" / "findings.yaml")[0], id=finding_id)
    record = SeverityRecord(
        id=finding_id,
        severity="critical",
        theta=1.0,
        content_hash="0" * 64,
        appearances=10,
        informative=10,
    )
    covered = FindingCoverage(finding=borrowed, severity=record, readings=())
    coverage = SetCoverage(
        name=name,
        calls=(borrowed.call_ref,),
        severity_run="0" * 64,
        bands=tuple(
            BandCoverage(band=band, findings=(covered,) if band == "critical" else ())
            for band in BAND_ORDER
        ),
        questions=(),
        unplaced=(),
    )
    return "\n".join(render_coverage(coverage, "Invented for a test.")) + "\n"


def test_a_coverage_report_over_held_out_findings_is_found(tmp_path: Path) -> None:
    """A coverage section naming a held-out finding is held-out output wherever it sits
    and whatever it is called (D188).

    It carries the finding's band, which is a held-out label, and no call id, transcript
    marker or run-log record, so none of the other three readings sees it.
    """
    pasted = tmp_path / "notes" / "scratch.txt"
    pasted.parent.mkdir()
    pasted.write_text(
        "Pasted from a terminal:\n\n" + _coverage_section("held-out set", _HELD_OUT_ID),
        encoding="utf-8",
        newline="\n",
    )
    found = scan_coverage_reports(tmp_path)
    assert list(found) == [pasted], found
    assert _HELD_OUT_ID in found[pasted]


def test_a_design_coverage_report_is_not_mistaken_for_a_held_out_one(tmp_path: Path) -> None:
    """The false-positive half: the heading and a held-out finding's id are required
    together, so a design section, a document quoting the heading beside a held-out id
    in running prose, and a file naming a held-out id alone are all left alone (D188).

    The design section is what `harness coverage` prints every time it runs, so a check
    reporting it would fail whoever redirected the design figures into this tree.
    """
    (tmp_path / "design.txt").write_text(
        _coverage_section("design set", "F-07"), encoding="utf-8", newline="\n"
    )
    (tmp_path / "doc.md").write_text(
        f"Each section opens `held-out set: coverage by severity` and names ids like "
        f"{_HELD_OUT_ID}.\n",
        encoding="utf-8",
        newline="\n",
    )
    (tmp_path / "labels.txt").write_text(_HELD_OUT_ID + "\n", encoding="utf-8", newline="\n")
    assert scan_coverage_reports(tmp_path) == {}


def test_the_check_reports_a_coverage_report_in_the_tree_it_scans(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The check itself, not only the scan: a held-out coverage report fails it, in a
    held-out transcript's words (D188).

    Run over a planted tree holding no design transcript, so the check fails for that as
    well; what is asserted is the line naming the report.
    """
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "coverage.txt").write_text(
        _coverage_section("held-out set", _HELD_OUT_ID), encoding="utf-8", newline="\n"
    )
    monkeypatch.setattr(check_holdout_absence, "REPO_ROOT", tmp_path)
    assert main() == 1
    err = capsys.readouterr().err
    assert (
        f"build/coverage.txt carries a coverage report naming held-out finding(s) {_HELD_OUT_ID}"
        in (err)
    ), err


# --------------------------------------------------------------------------
# D195: every encoding a redirect writes here, a file no reading can decode, and
# the held-out artifacts the four readings above had no reading for
# --------------------------------------------------------------------------


def _held_out_finding() -> Finding:
    """A design finding carrying the invented held-out id, on a call HELDOUT_SET declares."""
    held_out = declared_held_out_set()
    assert held_out, "HELDOUT_SET declares nothing, so this test plants nothing"
    borrowed = load_findings(REPO_ROOT / "corpus" / "findings.yaml")[0]
    return replace(borrowed, id=_HELD_OUT_ID, call_ref=held_out[0])


def _agreement_section(name: str) -> str:
    """A section as `harness.agreement.render_set` writes one, over one call and no
    entries: rendered by the shipped renderer, so the heading the check reads is the
    one the command prints."""
    agreement = SetAgreement(name=name, calls=(declared_held_out_set()[0],), entries=())
    return "\n".join(render_set(agreement, "Invented for a test.")) + "\n"


def _undecodable() -> bytes:
    """Text in the code page `build/v1.log` and `build/v2.log` were written in, whose
    em dash is a byte no UTF-8 decoder accepts (the phase-5 audit's P5-1)."""
    return "verifier output — redirected".encode("cp1252")


def test_every_reading_finds_its_artifact_as_a_powershell_redirect_writes_it(
    tmp_path: Path,
) -> None:
    """Each shape the check reads is found in UTF-16 and in UTF-8 with a byte-order
    mark, the two encodings a PowerShell redirect writes on this project's machine
    (D195). Every reading skipped both, and a heading on line 1 behind a mark stopped
    matching, so the check passed over exactly the redirect it was built to catch.

    Plain UTF-8 runs first as the positive control, so a miss below is the encoding's.
    """
    held_out = frozenset(declared_held_out_set())
    call = sorted(held_out)[0]
    shapes: tuple[tuple[str, str, Callable[[Path], object]], ...] = (
        ("transcript", SYNTHETIC_HELDOUT, lambda root: scan(root).get("CALL-13")),
        (
            "run log",
            _run_log_line(_header(labels_manifest=_INVENTED_MANIFEST)),
            lambda root: scan_run_logs(root, held_out),
        ),
        ("report", _REPORT_SHAPED.format(call=call), lambda root: scan_reports(root, held_out)),
        ("coverage", _coverage_section("held-out set", _HELD_OUT_ID), scan_coverage_reports),
        ("labels", dump_findings((_held_out_finding(),)), scan_labels),
        ("agreement", _agreement_section("held-out set"), scan_agreement_sections),
    )
    for codec in ("utf-8", "utf-16", "utf-8-sig"):
        for name, text, found_by in shapes:
            root = tmp_path / codec / name
            root.mkdir(parents=True)
            (root / "redirected.txt").write_bytes(text.encode(codec))
            assert found_by(root), f"the {name} written as {codec} is not found"


def test_a_file_no_reading_can_decode_is_reported_rather_than_skipped(tmp_path: Path) -> None:
    """Fail closed (D195): a file with no binary suffix that decodes as neither UTF-8
    nor UTF-16 is one no reading could look inside, so it is reported. A binary file
    by name and a UTF-16 one are not."""
    (tmp_path / "build").mkdir()
    redirected = tmp_path / "build" / "v1.log"
    redirected.write_bytes(_undecodable())
    (tmp_path / "picture.png").write_bytes(bytes(range(256)))
    (tmp_path / "wide.txt").write_bytes("plain words".encode("utf-16"))
    assert scan_unreadable(tmp_path) == [redirected]


def test_a_run_log_record_laid_out_across_lines_is_found(tmp_path: Path) -> None:
    """A header or a call record passed through `json.tool` has its kind and what it
    names on different lines, which the line reading cannot join; each is decoded as a
    JSON value instead (D195). A design call's record, laid out the same way, is not."""
    held_out = declared_held_out_set()
    assert held_out, "HELDOUT_SET declares nothing, so this test plants nothing"
    header = tmp_path / "header.json"
    header.write_text(
        json.dumps(_header(labels_manifest=_INVENTED_MANIFEST), indent=2),
        encoding="utf-8",
        newline="\n",
    )
    record = tmp_path / "record.json"
    record.write_text(json.dumps(_call(held_out[0]), indent=2), encoding="utf-8", newline="\n")
    (tmp_path / "design.json").write_text(
        json.dumps(_call(declared_design_set()[0]), indent=2), encoding="utf-8", newline="\n"
    )
    found = scan_run_logs(tmp_path, frozenset(held_out))
    assert set(found) == {header, record}, found


def test_an_extraction_artifact_over_a_declared_call_is_found(tmp_path: Path) -> None:
    """`harness.extract` writes every turn of every call it parses, so its artifact over
    a declared call is a held-out transcript in JSON; it is found by the call it names,
    and the design artifact is not (D195). Written by the shipped writer."""
    held = tmp_path / "held"
    held.mkdir()
    (held / "CALL-13.txt").write_text(SYNTHETIC_HELDOUT, encoding="utf-8", newline="")
    artifact = tmp_path / "build" / "extraction-artifact.json"
    write_artifact(artifact, build_payload(extract(held), "0.0.0", tmp_path))
    design = tmp_path / "design" / "extraction-artifact.json"
    write_artifact(
        design, build_payload(extract(REPO_ROOT / "corpus" / "transcripts"), "0.0.0", REPO_ROOT)
    )
    found = scan_run_logs(tmp_path, frozenset(declared_held_out_set()))
    assert set(found) == {artifact}, found


def test_held_out_labels_are_found_in_their_own_structure(tmp_path: Path) -> None:
    """The three label files and a findings view rendered over them are held-out
    content (D195): the findings and the severity export by a finding's `id`, the
    traces file by the ids it lists, and the view by its per-finding heading."""
    finding = _held_out_finding()
    findings = tmp_path / "findings.yaml"
    findings.write_text(dump_findings((finding,)), encoding="utf-8", newline="\n")
    traces = tmp_path / "traces.yaml"
    traces.write_text(
        yaml.safe_dump({"traces": {"A-invented": [finding.id]}, "uncovered": []}),
        encoding="utf-8",
        newline="\n",
    )
    severity = tmp_path / "severity.json"
    design_severity = (REPO_ROOT / "corpus" / "findings.severity.json").read_text("utf-8")
    severity.write_text(design_severity.replace('"F-', '"H' + "F-"), encoding="utf-8", newline="\n")
    view = tmp_path / "findings.md"
    view.write_text(render_markdown((finding,)), encoding="utf-8", newline="\n")
    found = scan_labels(tmp_path)
    assert set(found) == {findings, traces, severity, view}, found


def test_design_labels_or_a_document_naming_a_held_out_id_are_not_mistaken_for_held_out_ones(
    tmp_path: Path,
) -> None:
    """The false-positive half (D195): the design findings, severity export and view,
    a document naming a held-out id in prose, and code holding one are left alone."""
    for name in ("findings.yaml", "findings.severity.json", "findings.md"):
        (tmp_path / name).write_text(
            (REPO_ROOT / "corpus" / name).read_text("utf-8"), encoding="utf-8", newline="\n"
        )
    (tmp_path / "doc.md").write_text(
        f"Held-out ids look like {_HELD_OUT_ID}, and a finding reads `id: {_HELD_OUT_ID}`.\n",
        encoding="utf-8",
        newline="\n",
    )
    (tmp_path / "scratch.py").write_text(
        f'INVENTED = "{_HELD_OUT_ID}"\n', encoding="utf-8", newline="\n"
    )
    assert scan_labels(tmp_path) == {}


def test_agreements_held_out_section_is_found_and_its_design_section_is_not(
    tmp_path: Path,
) -> None:
    """Agreement's held-out section carries the judge's hits and misses on held-out
    calls, and it is recognized by the heading its renderer writes (D195). The design
    section, which `harness agreement` prints every time it runs, is not reported."""
    held = tmp_path / "held.txt"
    held.write_text(
        "Pasted:\n\n" + _agreement_section("held-out set"), encoding="utf-8", newline="\n"
    )
    (tmp_path / "design.txt").write_text(
        _agreement_section("design set"), encoding="utf-8", newline="\n"
    )
    assert set(scan_agreement_sections(tmp_path)) == {held}


def test_the_check_reports_labels_agreement_and_an_undecodable_file_in_the_tree_it_scans(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The check itself, not only the scans (D195): each of the three fails it, by
    name. Run over a planted tree holding no design transcript, so the check fails for
    that as well; what is asserted is the line naming each file."""
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "findings.yaml").write_text(
        dump_findings((_held_out_finding(),)), encoding="utf-8", newline="\n"
    )
    (tmp_path / "build" / "agreement.txt").write_text(
        _agreement_section("held-out set"), encoding="utf-8", newline="\n"
    )
    (tmp_path / "build" / "v1.log").write_bytes(_undecodable())
    monkeypatch.setattr(check_holdout_absence, "REPO_ROOT", tmp_path)
    assert main() == 1
    err = capsys.readouterr().err
    assert "build/findings.yaml carries held-out labels" in err, err
    assert "build/agreement.txt carries agreement's held-out section" in err, err
    assert "build/v1.log decodes as neither UTF-8 nor UTF-16" in err, err


def test_the_check_reports_a_rendered_report_in_the_tree_it_scans(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The check itself, not only the scan (D185), and the sibling D185 did not get.

    Its two tests called `scan_reports` and `_carries_a_held_out_report` directly, so
    the loop in `main()` could be unwired with both green and the OK line still saying
    no report over held-out calls was found -- which the phase-5 audit's P5-6
    demonstrated by removing it. The run-log and coverage readings each had this test
    from the start.
    """
    held_out = declared_held_out_set()
    assert held_out, "HELDOUT_SET declares nothing, so this test plants nothing"
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "report.md").write_text(
        _REPORT_SHAPED.format(call=held_out[0]), encoding="utf-8", newline="\n"
    )
    monkeypatch.setattr(check_holdout_absence, "REPO_ROOT", tmp_path)
    assert main() == 1
    err = capsys.readouterr().err
    assert f"build/report.md carries a rendered report naming {held_out[0]}" in err, err
