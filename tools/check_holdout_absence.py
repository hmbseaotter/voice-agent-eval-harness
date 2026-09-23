#!/usr/bin/env python3
"""Assert that no held-out transcript exists in this repository's working tree.

    uv run python tools/check_holdout_absence.py

WHY THIS EXISTS
---------------
This is **the only mechanism protecting the held-out set**, and it is worth
being precise about why the alternatives are not mechanisms at all.

The specification is explicit that physical absence is the only protection that
does not depend on obedience (D2), and that the companion repository's name is a
signal rather than an enforcement (D19). A rule saying "do not read the held-out
transcripts" protects nothing: any session working on the harness can read
anything in the harness's own tree, and a rule is not a boundary. Keeping the
files somewhere else is the boundary. This script is what notices when that stops
being true.

It also runs at **every later phase**, not only the one that authored the set.
The property has to hold for the whole life of the project, and the build prompt
that first stated it is superseded at the end of phase 1 -- which is why the
requirement moved into the specification and why this is a committed check
rather than a step in a document.

HOW IT LOOKS
------------
Not by filename. A filename check is defeated by renaming a file, which is
exactly what someone would do while "just having a quick look". It looks for the
transcript format header on line 1 of every file in the tree, so a held-out
transcript pasted anywhere, under any name, is found -- and then compares the
`call_id` of everything it finds against the declared design set.

Gitignored directories are searched too, `private/` included. A stashed copy is
still a copy, and `private/` is precisely where one would be stashed.

RUN LOGS
--------
A held-out run's log is held-out content too: its prompts carry the transcripts
the judge was shown, and its records carry the judge's answers. It never carries
the format marker, so it is looked for by its records instead -- a header naming a
labels manifest, or a call record for a call `HELDOUT_SET` declares -- on any line
of any file, read whole, with no size cap and no window (D174).

REPORTS
-------
A report rendered over held-out calls is held-out output as well: its tables carry
each call's verdicts and both tiers' roll-ups, which are the judge's answers on
those calls. It carries neither the transcript marker nor a run-log record, so it
is looked for by the heading the renderer writes **beside** a call id `HELDOUT_SET`
declares -- both together, so a design report and a document quoting the heading
are not reported (D185).

COVERAGE REPORTS
----------------
A coverage report over held-out findings names them and their severity bands, which
are held-out labels, and it carries no call id at all, so the report reading above
cannot see one. It is looked for by the heading `harness coverage` writes at the head
of each section **beside** a held-out finding's id -- both together, so a design
section and the tests that invent `HF-` ids are not reported (D188).

ENCODINGS
---------
Every reading decodes a file by its byte-order mark -- UTF-8 with one, or UTF-16 --
and as UTF-8 without one, because a redirect is how held-out output would arrive
here: Windows PowerShell 5.1 writes UTF-16, and a profile set to `utf8` writes UTF-8
with a mark. A file with no binary suffix that decodes as none of them is
**reported** rather than skipped, since a reading that cannot look inside a file has
not found it clean (D195).

LABELS, AGREEMENT AND JSON
--------------------------
The held-out labels -- findings, traces and a severity export -- are recognized in
their own structure by a held-out finding's id, and a findings view rendered over
them by its per-finding heading. Agreement's held-out section is recognized by the
heading `harness agreement` writes for it. And any JSON value that starts a line is
decoded whole, however it is laid out, so a run-log record pretty-printed across
lines, or an extraction artifact over a declared call, is read by what it names
rather than by how it is spaced. A run log's blob record alone names no call and
is not recognized, a limit D195 states.

Exit 0 when the tree holds exactly the design set and nothing else; 1 otherwise.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Final

import yaml

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
DESIGN_SET_FILE: Final[Path] = REPO_ROOT / "corpus" / "DESIGN_SET"
FIXTURE_SET_FILE: Final[Path] = REPO_ROOT / "tests" / "fixtures" / "FIXTURE_SET"
#: The held-out set's identifiers, declared here because nothing in this tree
#: can discover them. Read so that finding one of these is reported as **what it
#: is** rather than as an unrecognized id: the two cases need different words
#: and different urgency, and this check exists for the second.
HELDOUT_SET_FILE: Final[Path] = REPO_ROOT / "HELDOUT_SET"
TRANSCRIPTS: Final[Path] = REPO_ROOT / "corpus" / "transcripts"

_FORMAT_MARKER: Final[str] = "#format: voice-agent-eval-harness/transcript"
_CALL_ID: Final[re.Pattern[str]] = re.compile(r"^\s*call_id:\s*(CALL-\d+)\s*$", re.MULTILINE)

#: Tool-generated trees with no authored content. Everything else is searched,
#: including gitignored directories such as `private/`.
#: Nothing authors into any of these. `build/` is deliberately **not** among
#: them: it is gitignored, it is writable, and it is the project's own output
#: directory -- exactly the shape D37 refuses to skip, since skipping a
#: directory creates the hiding place the scan exists to deny. It was on this
#: list, and a test pinned the exemption.
_SKIP_DIRS: Final[frozenset[str]] = frozenset(
    {".git", ".venv", "venv", "__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache"}
)

#: Binary suffixes, skipped by name. **A deny list, not an allow list.**
#:
#: This was an allow list of six suffixes while the docstring above promised a
#: transcript is found "under any name". It was not: the same synthetic
#: transcript written as `.log`, `.bak`, `.py`, `.text`, `.rst` and `.csv` was
#: invisible to all six. An allow list has to enumerate every extension a person
#: might type, which is not a finite set, so the polarity was the defect.
#:
#: Anything not listed here is opened and read. A file that decodes as none of the
#: encodings `_decoded` reads is reported rather than skipped (D195); one larger than
#: the cap below is skipped by the transcript reading alone.
_BINARY_SUFFIXES: Final[frozenset[str]] = frozenset(
    {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".bmp",
        ".ico",
        ".webp",
        ".svgz",
        ".pdf",
        ".zip",
        ".gz",
        ".bz2",
        ".xz",
        ".7z",
        ".tar",
        ".whl",
        ".exe",
        ".dll",
        ".so",
        ".dylib",
        ".pyc",
        ".pyd",
        ".o",
        ".a",
        ".bin",
        ".mp3",
        ".mp4",
        ".wav",
        ".flac",
        ".ogg",
        ".avi",
        ".mov",
        ".webm",
        ".woff",
        ".woff2",
        ".ttf",
        ".otf",
        ".eot",
        ".db",
        ".sqlite",
        ".sqlite3",
        ".lock",
    }
)

#: Files larger than this are not transcripts. Opening a 40 MB blob to check it
#: is how a check becomes slow enough that someone removes it.
_MAX_BYTES: Final[int] = 2 * 1024 * 1024

#: How far into a file the marker is looked for. A transcript pasted into a
#: scratch script sits below a docstring and some imports, not on line 1.
_MARKER_WINDOW: Final[int] = 64 * 1024

#: Byte-order marks, and the codec each names. Measured on this project's machine: a
#: redirect in Windows PowerShell 5.1 writes UTF-16LE with a mark, and one whose
#: profile sets `Out-File` to `utf8` writes UTF-8 with a mark (the phase-5 audit's
#: P5-1). Each on its own line, so a control can take one away (D195).
_BOMS: Final[tuple[tuple[bytes, str], ...]] = (
    (b"\xef\xbb\xbf", "utf-8-sig"),
    (b"\xff\xfe", "utf-16"),
    (b"\xfe\xff", "utf-16"),
)


def _decoded(path: Path) -> str:
    """The file's text, decoded by its byte-order mark, or as UTF-8 without one (D195).

    Raises `UnicodeDecodeError` for a file that is neither, which every reading below
    treats as nothing it can see, and `scan_unreadable` reports.
    """
    data = path.read_bytes()
    for mark, codec in _BOMS:
        if data.startswith(mark):
            return data.decode(codec)
    return data.decode("utf-8")


def _files(root: Path) -> Iterator[Path]:
    """Every file under `root` outside the tool-generated trees, which are pruned rather
    than entered and filtered (D195).

    Each scan below used to walk everything, `.venv` and `.git` included, and discard
    what sat under them afterwards; with seven readings that took most of a minute over
    a checkout, which is how a check becomes slow enough that someone removes it.
    """
    for directory, subdirectories, names in os.walk(root):
        subdirectories[:] = [name for name in subdirectories if name not in _SKIP_DIRS]
        for name in names:
            yield Path(directory) / name


def _declared(path: Path) -> tuple[str, ...]:
    lines = path.read_text(encoding="utf-8").split("\n")
    return tuple(
        line.strip() for line in lines if line.strip() and not line.strip().startswith("#")
    )


def declared_design_set() -> tuple[str, ...]:
    return _declared(DESIGN_SET_FILE)


def declared_held_out_set() -> tuple[str, ...]:
    """The held-out identifiers, from the file that mirrors them.

    Identifiers are metadata and safe to hold here; the transcripts are content
    and are not. That distinction is what lets this check say "this **is** a
    held-out transcript" instead of "this id is declared nowhere" -- and the
    difference matters, because the first is an instruction to delete a file and
    treat every session that touched it as contaminated, while the second reads
    like a missing declaration somebody should add.
    """
    return _declared(HELDOUT_SET_FILE)


def declared_fixture_set() -> tuple[str, ...]:
    """Synthetic transcripts the tests own.

    Declared rather than excluded. Skipping `tests/fixtures/` would have been
    one line shorter and would have created a hiding place -- and a hiding place
    is the one thing this check exists to deny. Every transcript in the tree has
    to be accounted for by name, so adding a fixture means declaring it.
    """
    return _declared(FIXTURE_SET_FILE)


def _looks_like_a_transcript(path: Path) -> str | None:
    """The `call_id` if this file carries a conforming transcript, else `None`.

    **Carries, not is.** The marker used to be required on line 1, which meant a
    transcript pasted into a Python string, a Markdown fence or a JSON blob was
    invisible -- and pasting one into a scratch script to "just have a quick
    look" is the move this check exists to catch. It is now looked for anywhere
    in the first `_MARKER_WINDOW` bytes.

    Widening it that far needs the second condition below, or the format
    specification and this file would both report themselves: they quote the
    marker while documenting it. So a marker found **below line 1** counts only
    when a `call_id` follows it, which documentation does not carry and a real
    transcript always does. A marker **on line 1** is still enough on its own --
    that file is a transcript whatever else is true of it, and one with its
    `call_id` stripped is reported as unreadable rather than waved through.
    """
    if path.suffix.lower() in _BINARY_SUFFIXES:
        return None
    try:
        if path.stat().st_size > _MAX_BYTES:
            return None
        text = _decoded(path)[:_MARKER_WINDOW]
    except (UnicodeDecodeError, OSError, ValueError):
        return None

    marker_at = text.find(_FORMAT_MARKER)
    if marker_at < 0:
        return None
    match = _CALL_ID.search(text, marker_at)
    if match is not None:
        return match.group(1)
    return "<unreadable call_id>" if marker_at == 0 else None


#: A run-log record as the harness's run-log writer serializes one: a JSON object
#: per line, its kind under `record`. Spacing is optional in all four, so a record
#: re-serialized compactly before it was pasted somewhere is still read (D174).
_HEADER_RECORD: Final[re.Pattern[str]] = re.compile(r'"record"\s*:\s*"header"')
_CALL_RECORD: Final[re.Pattern[str]] = re.compile(r'"record"\s*:\s*"call"')
_MANIFEST_KEY: Final[re.Pattern[str]] = re.compile(r'"labels_manifest"\s*:')

#: The heading `harness.report.render_report` writes first, and any call id. A
#: report is recognized by **both**: the heading alone is in this repository's own
#: snapshot and in the renderer's source, and a call id alone is in every document
#: naming one. Together they are a rendered report over calls it names (D185).
_REPORT_MARKER: Final[re.Pattern[str]] = re.compile(r"^# Evaluation report\s*$", re.MULTILINE)
_ANY_CALL_ID: Final[re.Pattern[str]] = re.compile(r"\bCALL-\d+\b")
_RECORD_CALL_ID: Final[re.Pattern[str]] = re.compile(r'"call_id"\s*:\s*"(CALL-\d+)"')

#: The heading `harness.coverage.render_coverage` writes at the head of a section, and
#: a held-out finding's id. A coverage report is recognized by **both**: the heading
#: alone opens every design section, and an `HF-` id alone sits in the tests that
#: invent held-out labels. Together they are a coverage report over held-out findings
#: (D188).
_COVERAGE_MARKER: Final[re.Pattern[str]] = re.compile(
    r"^[\w-]+ set: coverage by severity\b", re.MULTILINE
)
_HELD_OUT_FINDING_ID: Final[re.Pattern[str]] = re.compile(r"\bHF-\d{2,}\b")


def _carries_a_held_out_run_log(path: Path, held_out: frozenset[str]) -> str | None:
    """What marks this file as carrying a held-out run log, or `None` (D174).

    A judged run's log holds the prompts its calls' transcripts were rendered
    into and the judge's answers, and never the transcript format marker, so the
    transcript scan above cannot see one. Two records mark it: a header naming a
    labels manifest, which only a held-out run writes (D173), and a call record
    whose `call_id` `HELDOUT_SET` declares. Either is looked for on any line of
    any file, the way a transcript is looked for anywhere in one, so records
    pasted into a scratch file are found as well as a whole log.

    **The whole file, with no size cap and no window.** Those exist to keep the
    transcript scan out of blobs, and a run log is the blob this reading is for:
    a design-size log is 2.5 MB, and a pasted record can sit anywhere in a file.
    """
    suffix = path.suffix.lower()
    if suffix in _BINARY_SUFFIXES:
        return None
    try:
        text = _decoded(path)
    except (UnicodeDecodeError, OSError, ValueError):
        return None
    for line in text.splitlines():
        if _HEADER_RECORD.search(line) and _MANIFEST_KEY.search(line):
            return "a run-log header naming a labels manifest"
        if _CALL_RECORD.search(line):
            match = _RECORD_CALL_ID.search(line)
            if match is not None and match.group(1) in held_out:
                return f"a run-log call record for {match.group(1)}, which HELDOUT_SET declares"
    # The lines above read a record serialized on one line, wherever it was pasted. A
    # record pretty-printed across lines, or an extraction artifact, is read here as a
    # JSON value, by what it names rather than how it is spaced (D195).
    for value in _json_values(text):
        for mapping in _mappings(value):
            if mapping.get("record") == "header" and "labels_manifest" in mapping:
                return "a run-log header naming a labels manifest, laid out across lines"
            call = mapping.get("call_id")
            if isinstance(call, str) and call in held_out:
                return f"a JSON record naming {call}, which HELDOUT_SET declares"
    return None


def _json_values(text: str) -> Iterator[object]:
    """Every JSON value that starts a line of `text`, decoded whole however it is laid
    out: a run log's records one per line, a record pretty-printed across lines, or a
    whole file such as an extraction artifact (D195). A line that starts a value which
    does not decode is passed over."""
    decoder = json.JSONDecoder()
    offset = 0
    for line in text.splitlines(keepends=True):
        start = offset
        offset += len(line)
        stripped = line.lstrip()
        if not stripped.startswith(("{", "[")):
            continue
        try:
            value, _ = decoder.raw_decode(text, start + len(line) - len(stripped))
        except ValueError:
            continue
        yield value


def _mappings(value: object) -> Iterator[dict[object, object]]:
    """Every mapping inside a decoded JSON or YAML value, at any depth."""
    pending = [value]
    while pending:
        current = pending.pop()
        if isinstance(current, dict):
            yield current
            pending.extend(current.values())
        elif isinstance(current, list):
            pending.extend(current)


def scan_run_logs(root: Path, held_out: frozenset[str]) -> dict[Path, str]:
    """Every path in the tree carrying a held-out run log, with what marks it (D174)."""
    found: dict[Path, str] = {}
    for path in _files(root):
        reason = _carries_a_held_out_run_log(path, held_out)
        if reason is not None:
            found[path] = reason
    return found


def _carries_a_held_out_report(path: Path, held_out: frozenset[str]) -> str | None:
    """What marks this file as carrying a report over held-out calls, or `None` (D185).

    Read whole, with no size cap and no window, for the reason the run-log reading
    gives: a pasted table can sit anywhere in a file, and a report is small beside
    the logs that reading is sized for.
    """
    if path.suffix.lower() in _BINARY_SUFFIXES:
        return None
    try:
        # Named apart from the run-log reading's `text` deliberately: that line is
        # what a control mutation anchors on, and a second copy of it would leave
        # the gate refusing to run rather than verifying the control.
        rendered = _decoded(path)
    except (UnicodeDecodeError, OSError, ValueError):
        return None
    if _REPORT_MARKER.search(rendered) is None:
        return None
    named = sorted({call for call in _ANY_CALL_ID.findall(rendered) if call in held_out})
    if not named:
        return None
    listed = ", ".join(named)
    return f"a rendered report naming {listed}, which HELDOUT_SET declares"


def scan_reports(root: Path, held_out: frozenset[str]) -> dict[Path, str]:
    """Every path in the tree carrying a report over held-out calls, with what marks it (D185)."""
    found: dict[Path, str] = {}
    for path in _files(root):
        reason = _carries_a_held_out_report(path, held_out)
        if reason is not None:
            found[path] = reason
    return found


def _carries_a_held_out_coverage_report(path: Path) -> str | None:
    """What marks this file as carrying a coverage report over held-out findings, or
    `None` (D188).

    Read whole, for the report reading's reason: a pasted section can sit anywhere in
    a file. No `HELDOUT_SET` is needed, since a held-out finding's id says which set it
    belongs to by its shape.
    """
    if path.suffix.lower() in _BINARY_SUFFIXES:
        return None
    try:
        # Named apart from the other readings' variables, for the reason given there:
        # a control mutation anchors on a whole line, and a second copy of one would
        # leave the gate refusing to run.
        sections = _decoded(path)
    except (UnicodeDecodeError, OSError, ValueError):
        return None
    if _COVERAGE_MARKER.search(sections) is None:
        return None
    named = sorted(set(_HELD_OUT_FINDING_ID.findall(sections)))
    if not named:
        return None
    shown = ", ".join(named[:3]) + (f" and {len(named) - 3} more" if len(named) > 3 else "")
    return f"a coverage report naming held-out finding(s) {shown}"


def scan_coverage_reports(root: Path) -> dict[Path, str]:
    """Every path in the tree carrying a coverage report over held-out findings (D188)."""
    found: dict[Path, str] = {}
    for path in _files(root):
        reason = _carries_a_held_out_coverage_report(path)
        if reason is not None:
            found[path] = reason
    return found


#: The heading `harness.core.findings.render_markdown` writes for each finding, when
#: the finding's id has the held-out shape: a findings view rendered over held-out
#: labels (D195).
_VIEW_FINDING: Final[re.Pattern[str]] = re.compile(r"^## HF-\d{2,} — CALL-\d+", re.MULTILINE)

#: The heading `harness.agreement.render_set` writes at the head of the held-out
#: section. The design section's opens `design set:`, so the set's name alone tells the
#: two apart (D175, D195).
_AGREEMENT_HEADING: Final[re.Pattern[str]] = re.compile(
    r"^held-out set: \d+ calls, \d+ rubric entries$", re.MULTILINE
)


def _names_a_held_out_finding(mapping: dict[object, object]) -> bool:
    """A finding, a severity row or a traces file naming a held-out finding (D195).

    A finding and a severity row carry the finding's id under `id`; the traces file
    lists ids under each rubric entry in `traces`, and under `uncovered`.
    """
    ident = mapping.get("id")
    if isinstance(ident, str) and _HELD_OUT_FINDING_ID.fullmatch(ident):
        return True
    traced = mapping.get("traces")
    listed = list(traced.values()) if isinstance(traced, dict) else []
    listed.append(mapping.get("uncovered"))
    return any(
        isinstance(ids, list)
        and any(isinstance(i, str) and _HELD_OUT_FINDING_ID.fullmatch(i) for i in ids)
        for ids in listed
    )


def _carries_held_out_labels(path: Path) -> str | None:
    """What marks this file as carrying held-out labels, or a view rendered over them,
    or `None` (D195).

    The labels are recognized in their own structure -- a finding or a severity row
    whose `id` has the held-out shape, or a traces file listing one -- so a document
    that merely names such an id, as the tests inventing them do, is not reported.
    Only a file naming one at all is parsed.
    """
    if path.suffix.lower() in _BINARY_SUFFIXES:
        return None
    try:
        labels = _decoded(path)
    except (UnicodeDecodeError, OSError, ValueError):
        return None
    if _HELD_OUT_FINDING_ID.search(labels) is None:
        return None
    if _VIEW_FINDING.search(labels) is not None:
        return "a findings view rendered over a held-out finding"
    values = list(_json_values(labels))
    with contextlib.suppress(yaml.YAMLError):
        values.append(yaml.safe_load(labels))
    for value in values:
        for mapping in _mappings(value):
            if _names_a_held_out_finding(mapping):
                return "held-out labels, naming a held-out finding in their own structure"
    return None


def scan_labels(root: Path) -> dict[Path, str]:
    """Every path in the tree carrying held-out labels or a view over them (D195)."""
    found: dict[Path, str] = {}
    for path in _files(root):
        reason = _carries_held_out_labels(path)
        if reason is not None:
            found[path] = reason
    return found


def _carries_held_out_agreement(path: Path) -> str | None:
    """What marks this file as carrying agreement's held-out section, or `None` (D195)."""
    if path.suffix.lower() in _BINARY_SUFFIXES:
        return None
    try:
        counted = _decoded(path)
    except (UnicodeDecodeError, OSError, ValueError):
        return None
    if _AGREEMENT_HEADING.search(counted) is None:
        return None
    return "agreement's held-out section"


def scan_agreement_sections(root: Path) -> dict[Path, str]:
    """Every path in the tree carrying agreement's held-out section (D195)."""
    found: dict[Path, str] = {}
    for path in _files(root):
        reason = _carries_held_out_agreement(path)
        if reason is not None:
            found[path] = reason
    return found


def scan_unreadable(root: Path) -> list[Path]:
    """Every file the readings open and cannot decode, which the check reports rather
    than skips (D195).

    Each reading passes over a file it cannot decode, so on its own a file in an
    encoding they do not know is found clean by all of them -- which is how verifier
    output redirected in another encoding sat in `build/` unread (the phase-5 audit's
    P5-1).
    """
    unreadable: list[Path] = []
    for path in _files(root):
        if path.suffix.lower() in _BINARY_SUFFIXES:
            continue
        try:
            _decoded(path)
        except (UnicodeDecodeError, OSError):
            unreadable.append(path)
    return unreadable


def scan(root: Path) -> dict[str, list[Path]]:
    """call_id -> every path in the tree carrying it."""
    found: dict[str, list[Path]] = {}
    for path in _files(root):
        call_id = _looks_like_a_transcript(path)
        if call_id is not None:
            found.setdefault(call_id, []).append(path)
    return found


def main() -> int:
    design_set = declared_design_set()
    fixture_set = declared_fixture_set()
    found = scan(REPO_ROOT)

    problems: list[str] = []

    overlap = sorted(set(design_set) & set(fixture_set))
    if overlap:
        problems.append(f"declared in both the design set and the fixture set: {overlap}")

    held_out = declared_held_out_set()
    declared = set(design_set) | set(fixture_set)
    strangers = sorted(set(found) - declared)
    for call_id in strangers:
        for path in found[call_id]:
            location = path.relative_to(REPO_ROOT).as_posix()
            if call_id in held_out:
                # The case this whole tool exists for, and it used to be
                # reported in the same words as a missing declaration. Naming it
                # is the difference between "add this to a list" and "delete
                # this file and treat every session that opened it as
                # contaminated".
                problems.append(
                    f"{location} carries {call_id}, which HELDOUT_SET declares as a HELD-OUT "
                    "transcript. It must never exist in this tree: delete it, and treat "
                    "anything that read it as having read held-out content."
                )
            else:
                problems.append(
                    f"{location} carries {call_id}, which is declared in none of "
                    "corpus/DESIGN_SET, tests/fixtures/FIXTURE_SET or HELDOUT_SET. If it is a "
                    "held-out transcript it must not exist here: delete it, and treat anything "
                    "that read it as having read it."
                )

    # A held-out run's log is held-out content wherever it sits, so it gets a held-out
    # transcript's words (D174).
    for path, reason in sorted(scan_run_logs(REPO_ROOT, frozenset(held_out)).items()):
        location = path.relative_to(REPO_ROOT).as_posix()
        problems.append(
            f"{location} carries {reason}: a held-out run log. It must never exist in this "
            "tree: delete it, and treat anything that read it as having read held-out content."
        )

    # A report over held-out calls carries the judge's answers on them, so it gets
    # the same words as the log those answers were recorded in (D185).
    for path, reason in sorted(scan_reports(REPO_ROOT, frozenset(held_out)).items()):
        location = path.relative_to(REPO_ROOT).as_posix()
        problems.append(
            f"{location} carries {reason}: a report over held-out calls. It must never exist "
            "in this tree: delete it, and treat anything that read it as having read held-out "
            "content."
        )

    # A coverage report over held-out findings carries their bands, which are held-out
    # labels, so it gets the same words (D188).
    for path, reason in sorted(scan_coverage_reports(REPO_ROOT).items()):
        location = path.relative_to(REPO_ROOT).as_posix()
        problems.append(
            f"{location} carries {reason}: held-out labels. It must never exist in this "
            "tree: delete it, and treat anything that read it as having read held-out content."
        )

    # The labels themselves, a view rendered over them, and agreement's held-out section
    # are held-out content wherever they sit, so they get the same words (D195).
    for path, reason in sorted(scan_labels(REPO_ROOT).items()):
        location = path.relative_to(REPO_ROOT).as_posix()
        problems.append(
            f"{location} carries {reason}. It must never exist in this tree: delete it, and "
            "treat anything that read it as having read held-out content."
        )
    for path, reason in sorted(scan_agreement_sections(REPO_ROOT).items()):
        location = path.relative_to(REPO_ROOT).as_posix()
        problems.append(
            f"{location} carries {reason}. It must never exist in this tree: delete it, and "
            "treat anything that read it as having read held-out content."
        )

    # A file no reading can decode is one none of them found clean (D195).
    for path in scan_unreadable(REPO_ROOT):
        location = path.relative_to(REPO_ROOT).as_posix()
        problems.append(
            f"{location} decodes as neither UTF-8 nor UTF-16, so no reading of this check can "
            "see inside it. Re-encode it as UTF-8 or remove it; if it is binary, add its "
            "suffix to the check's binary list."
        )

    missing = sorted(set(design_set) - set(found))
    for call_id in missing:
        problems.append(f"{call_id} is declared in the design set but no transcript carries it")

    for call_id, paths in sorted(found.items()):
        if len(paths) > 1:
            listed = ", ".join(p.relative_to(REPO_ROOT).as_posix() for p in paths)
            problems.append(f"{call_id} appears in more than one file: {listed}")

    expected_dir = {p.stem for p in TRANSCRIPTS.glob("*.txt")}
    if expected_dir != set(design_set):
        problems.append(
            f"corpus/transcripts holds {sorted(expected_dir)}, design set declares "
            f"{list(design_set)}"
        )

    if problems:
        print(f"held-out absence check FAILED: {len(problems)} problem(s)", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1

    print(
        f"held-out absence check OK -- the working tree carries exactly the "
        f"{len(design_set)} declared design-set transcripts and {len(fixture_set)} declared "
        "test fixtures, no others, no held-out run log, no report over held-out calls, no "
        "coverage report over held-out findings, no held-out labels or agreement section, "
        "and no file it could not decode"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
