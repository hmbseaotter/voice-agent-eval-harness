#!/usr/bin/env python3
"""Run every phase-1 acceptance criterion and report what proved it.

    uv run python tools/verify_phase1.py

WHY THIS EXISTS
---------------
The build prompt's rule is to verify each criterion **by running it**, and not to
mark the phase complete until all pass. A checklist ticked by reading is not that.

This maps each criterion to the specific test node or command that establishes
it, runs them, and prints the result per criterion. Two properties follow that a
green test suite alone does not give:

* A criterion whose evidence has been deleted or renamed shows as MISSING rather
  than silently dropping off the list. A checklist that quietly shrinks is worse
  than no checklist.
* The report says which criteria are **not fully checkable by machine**, and why.
  A green tick against an unfalsifiable claim is the most expensive kind of
  false comfort in a project like this one.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
SPEC: Final[Path] = REPO_ROOT / "specs" / "voice-agent-eval-harness.md"
JUNIT: Final[Path] = REPO_ROOT / "build" / "phase1-junit.xml"


#: The severity tool's repository name, in the one place that spells it.
SIBLING: Final[str] = "comparative-judgment"


def sibling_root(repo_root: Path | None = None) -> Path:
    """Where the severity tool is checked out, relative to this repository.

    Criterion 21 knew one layout and CI uses another. Locally the repositories sit
    side by side, so `../comparative-judgment` is right. `actions/checkout`
    cannot place a repository above `GITHUB_WORKSPACE`, so CI checks it out
    **inside** this one at `comparative-judgment/`. The criterion hardcoded the
    local form, and the first CI run that ever executed this verifier reported
    `21. [FAIL]` -- the scanner had exited 2 with `not a file`, comparing
    nothing, in the criterion whose whole subject is that two repositories
    agree.

    The workflow's own interface step already used the CI path. So one path
    convention existed in two places, they disagreed, and nothing compared them
    -- which is D84's shape and this project's most-repeated finding, reached
    this time because a check had never been run rather than because it had
    gone quiet.

    Returns the sibling that has a `specs/` directory, preferring the local
    layout, and falls back to it when neither is present so the failure names
    the place a reader should look.
    """
    root = repo_root or REPO_ROOT
    side_by_side = root.parent / SIBLING
    for candidate in (side_by_side, root / SIBLING):
        if (candidate / "specs").is_dir():
            return candidate
    return side_by_side


def _sibling_specs() -> str:
    """The spec paths criterion 21 compares against, comma-joined."""
    root = sibling_root()
    return ",".join(
        str((root / "specs" / f"{SIBLING}{suffix}.md").as_posix()) for suffix in ("", ".decisions")
    )


@dataclass(frozen=True, slots=True)
class Criterion:
    text: str
    tests: tuple[str, ...] = ()
    commands: tuple[tuple[str, ...], ...] = ()
    caveat: str | None = None
    """Set when the criterion is not fully establishable by machine. The check
    still runs; the caveat says what its tick does not buy, and nothing else --
    not when the criterion was added, nor what an earlier caveat said, which the
    decisions record (D180)."""

    spec_anchor: str = ""
    """A distinctive substring of the `[P1]` acceptance criterion this verifies.

    Empty only for an entry that is deliberately not one: this list splits the
    severity criterion in two and adds the interface scanner, which the
    specification does not carry as an acceptance criterion at all.

    It exists because nothing bound this list to the document it claims to
    verify. `tests/test_acceptance.py` checked one direction -- every test node
    a criterion names still exists -- so a criterion added to the specification
    and never added here was invisible, while the closing line reported
    `len(CRITERIA)` as "all N phase-1 acceptance criteria". That number counted
    this list, not the specification's.
    """


#: The two ways a verifier claims a criterion without ticking it (D176). A
#: criterion **asserted elsewhere** is checked by another repository's machinery,
#: which this one cannot run; one **not yet built** belongs to a phase still open.
ASSERTED_ELSEWHERE: Final[str] = "asserted elsewhere"
NOT_YET_BUILT: Final[str] = "not yet built"
DECLARATION_KINDS: Final[tuple[str, ...]] = (ASSERTED_ELSEWHERE, NOT_YET_BUILT)

#: The places a criterion may be asserted elsewhere. An asserted-elsewhere
#: declaration's reason has to name one, so "elsewhere" is never nowhere.
KNOWN_ELSEWHERE: Final[tuple[str, ...]] = ("the held-out repository's gate",)


#: History in a caveat, in the two shapes found before D180: a note of the decision a criterion
#: was added at, and a sentence dating when something stopped being true. A caveat prints under
#: "read these rather than the ticks", so it states what its tick does not buy, and the decisions
#: record when and why a criterion exists. These are the markers found, not a definition of
#: history: a history sentence carrying neither passes, and D180 says so.
HISTORY_MARKERS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"\bAdded at D\d+"),
    re.compile(r"\buntil \d{4}-\d{2}-\d{2}\b"),
)


def history_in_caveats(criteria: Sequence[Criterion]) -> list[str]:
    """Each caveat carrying a history marker, named by its criterion's opening words (D180)."""
    found: list[str] = []
    for criterion in criteria:
        caveat = criterion.caveat or ""
        for marker in HISTORY_MARKERS:
            match = marker.search(caveat)
            if match:
                found.append(f"{criterion.text[:60]!r} carries {match.group(0)!r}")
    return found


@dataclass(frozen=True, slots=True)
class Declared:
    """A criterion a verifier claims without ticking it (D176).

    **Never a pass and never a failure.** A tick needs evidence this repository
    produces, and an entry with none reads `NO EVIDENCE`, which fails. A criterion
    asserted by another repository, or not built yet, is neither: it is printed
    under its own heading with its reason, and counted apart.
    """

    text: str
    spec_anchor: str
    """A distinctive substring of the `[Pn]` acceptance criterion this declares."""
    kind: str
    """One of `DECLARATION_KINDS`."""
    reason: str
    """Where the criterion is asserted, or what is still to be built."""


def unclaimed_criteria(
    lines: Sequence[str], criteria: Sequence[Criterion], declared: Sequence[Declared]
) -> list[str]:
    """Criterion lines no entry claims and no declaration names (D176)."""
    return [
        line
        for line in lines
        if not any(entry.spec_anchor and entry.spec_anchor in line for entry in criteria)
        and not any(declaration.spec_anchor in line for declaration in declared)
    ]


def doubly_claimed_criteria(
    lines: Sequence[str], criteria: Sequence[Criterion], declared: Sequence[Declared]
) -> list[str]:
    """Criterion lines both an entry and a declaration claim (D176).

    A declaration that outlived the build would go on excusing a criterion an
    entry now verifies, so the two together are refused.
    """
    return [
        line
        for line in lines
        if any(entry.spec_anchor and entry.spec_anchor in line for entry in criteria)
        and any(declaration.spec_anchor in line for declaration in declared)
    ]


def declaration_problems(lines: Sequence[str], declared: Sequence[Declared]) -> list[str]:
    """Why each declaration cannot stand, one line each; empty when all can (D176)."""
    problems: list[str] = []
    for declaration in declared:
        name = declaration.text[:60]
        if not declaration.spec_anchor or not any(
            declaration.spec_anchor in line for line in lines
        ):
            problems.append(f"{name}: its anchor names no acceptance criterion of the phase")
        if declaration.kind not in DECLARATION_KINDS:
            problems.append(f"{name}: kind {declaration.kind!r} is not one of {DECLARATION_KINDS}")
        if not declaration.reason.strip():
            problems.append(f"{name}: it gives no reason")
        elif declaration.kind == ASSERTED_ELSEWHERE and not any(
            place in declaration.reason for place in KNOWN_ELSEWHERE
        ):
            problems.append(f"{name}: it is asserted elsewhere and names none of {KNOWN_ELSEWHERE}")
    return problems


T = "tests/"

CRITERIA: Final[tuple[Criterion, ...]] = (
    Criterion(
        "The format specification exists, and every declared design transcript parses with a zero "
        "unparsed-line count.",
        tests=(
            f"{T}test_acceptance.py::test_the_format_specification_exists_and_names_its_version",
            f"{T}test_text_adapter.py::test_the_real_corpus_parses_with_a_zero_unparsed_count",
        ),
        commands=((sys.executable, "-m", "harness.extract"),),
        spec_anchor="The format specification exists, and",
    ),
    Criterion(
        "Every findings entry carries id, call_ref, owner, observation, evidence, consequence, "
        "detectable_by and tier; the count lacking any of them is zero.",
        tests=(f"{T}test_findings.py::test_every_entry_carries_every_required_key",),
        spec_anchor="; the count lacking any of them is zero.",
    ),
    Criterion(
        "The findings document parses as YAML, and an entry whose evidence holds three separate "
        "fragments round-trips with all three still distinct.",
        tests=(f"{T}test_findings.py::test_three_evidence_fragments_round_trip_as_three",),
        spec_anchor="holds three separate fragments round-trips with all three still distinct",
    ),
    Criterion(
        "A findings document containing a severity field is rejected by name.",
        tests=(f"{T}test_findings.py::test_a_severity_field_is_rejected_by_name",),
        spec_anchor="findings document containing a severity field is rejected by name.",
    ),
    Criterion(
        "A finding's severity resolves by joining the severity file on id.",
        tests=(
            f"{T}test_findings.py::test_severity_joins_on_id_and_unplaced_gets_no_band",
            f"{T}test_findings.py::test_the_join_is_total_over_the_gold_set",
        ),
        caveat="What stays outside a machine is whether the ordering those bands encode is the "
        "right ordering, which is human work (D10).",
        spec_anchor="A finding's severity resolves by joining the severity file on",
    ),
    Criterion(
        "The generated Markdown view regenerates identically from the YAML.",
        tests=(f"{T}test_findings.py::test_the_markdown_view_regenerates_identically",),
        commands=((sys.executable, "-m", "harness.findings_view", "--check"),),
        spec_anchor="The generated Markdown view",
    ),
    Criterion(
        "A transcript with a turn wrapped across three source lines reassembles into one string, "
        "asserted against the source file.",
        tests=(
            f"{T}test_text_adapter.py::test_three_line_wrap_reassembles_to_a_hardcoded_string",
            f"{T}test_text_adapter.py::test_the_corpus_contains_a_three_line_wrap",
            f"{T}test_corpus_hygiene.py::test_the_corpus_carries_a_wrapped_assignment",
            f"{T}test_corpus_hygiene.py::test_a_wrapped_context_value_keeps_every_source_fragment",
        ),
        spec_anchor="A transcript with a turn wrapped across three source lines reassembles",
    ),
    Criterion(
        "A transcript carrying an unknown tool-status token aborts extraction, naming file, line "
        "and token.",
        tests=(
            f"{T}test_text_adapter.py::test_unknown_tool_status_aborts_naming_file_line_and_token",
        ),
        spec_anchor="A transcript carrying an unknown tool-status token aborts extraction",
    ),
    Criterion(
        "A malformed transcript line produces a non-zero unparsed-line count and fails the run.",
        tests=(
            f"{T}test_text_adapter.py::test_malformed_lines_are_counted_and_not_discarded",
            f"{T}test_text_adapter.py::test_a_nonzero_unparsed_count_fails_the_run",
        ),
        spec_anchor="A malformed transcript line produces a non-zero unparsed-line count",
    ),
    Criterion(
        "A staged .env over 20 bytes is refused by the pre-commit guard, verified by attempting it "
        "in a scratch repository.",
        tests=(f"{T}test_hooks.py::test_populated_env_is_refused",),
        spec_anchor="over 20 bytes is refused by the pre-commit guard, verified by attempting",
    ),
    Criterion(
        "A staged path under private/ is refused by the pre-commit guard, verified the same way.",
        tests=(f"{T}test_hooks.py::test_private_path_is_refused",),
        spec_anchor="is refused by the pre-commit guard, verified",
    ),
    Criterion(
        "Both guards fail closed: an indeterminate staged-blob size, or an unresolvable staged "
        "path, blocks rather than allows.",
        tests=(
            f"{T}test_hooks.py::test_indeterminate_blob_size_fails_closed",
            f"{T}test_hooks.py::test_failed_enumeration_fails_closed",
        ),
        spec_anchor=": an indeterminate staged-blob size, or an unresolvable staged path",
    ),
    Criterion(
        ".gitignore covers .env, private/, __pycache__/ and *.pyc, present in the first commit.",
        tests=(f"{T}test_acceptance.py::test_the_hygiene_floor_was_in_the_first_commit",),
        spec_anchor=", present in the first commit.",
    ),
    Criterion(
        "The pre-commit hook source is present under a documented path, and following the "
        "documented installation reproduces both refusals in a scratch clone.",
        tests=(
            f"{T}test_acceptance.py::test_the_hook_source_is_present_under_a_documented_path",
            f"{T}test_acceptance.py::test_the_documented_hook_installation_actually_works",
        ),
        spec_anchor="under a documented path, and following the documented installation",
    ),
    Criterion(
        "uv.lock exists and pins exact resolved versions; no dependency is expressed only as a "
        "floor.",
        tests=(
            f"{T}test_acceptance.py::test_no_dependency_is_expressed_only_as_a_floor",
            f"{T}test_acceptance.py::test_the_lockfile_exists_and_pins_every_declared_dependency",
        ),
        spec_anchor="exists and pins exact resolved versions; no dependency is expressed only",
    ),
    Criterion(
        "LICENSE (Apache-2.0) and LICENSE-CC-BY exist.",
        tests=(f"{T}test_acceptance.py::test_both_licenses_exist_now_too",),
        spec_anchor="LICENSE-CC-BY",
    ),
    Criterion(
        "A repository-wide scan finds no entity name, figure or policy term belonging to prior "
        "third-party material, across all seven substitution classes.",
        tests=(
            f"{T}test_corpus_hygiene.py::test_ticketings_own_shapes_are_doing_the_work",
            f"{T}test_corpus_hygiene.py::test_every_tool_called_is_declared_in_the_entity_register",
        ),
        caveat="PARTIALLY CHECKABLE, and the residue is the important half. No string watch-list "
        "exists or can exist: the source material was never read (D6), so a scan cannot compare "
        "against it. What IS checked is the domain boundary — twelve scenario-shape smells from an "
        "adjacent domain, each asserted absent — plus the substitution-class discipline. The "
        "structural claim rests on the corpus having been authored rather than adapted, which is "
        "a property of the process and not of any test.",
        spec_anchor="A repository-wide scan finds no entity name, figure or policy term",
    ),
    Criterion(
        "The corpus contains no real personal data, asserted against the substitution-class "
        "checklist.",
        tests=(
            f"{T}test_corpus_hygiene.py::test_every_email_address_is_in_the_reserved_domain",
            f"{T}test_corpus_hygiene.py::test_every_zip_code_is_below_the_lowest_assigned_one",
            f"{T}test_corpus_hygiene.py::test_every_telephone_number_is_in_the_reserved_fictional_range",
            f"{T}test_corpus_hygiene.py::test_no_payment_card_number_appears",
            f"{T}test_corpus_hygiene.py::test_no_street_address_appears",
        ),
        spec_anchor="The corpus contains no real personal data, asserted against the",
    ),
    Criterion(
        "The held-out transcripts declared in HELDOUT_SET exist in the companion repository "
        "and not in this working tree, asserted by a path check.",
        tests=(
            f"{T}test_holdout_absence.py::test_the_repository_currently_holds_only_what_it_declares",
            f"{T}test_holdout_absence.py::test_a_held_out_transcript_in_the_tree_is_found",
            f"{T}test_holdout_absence.py::test_renaming_the_file_does_not_hide_it",
            f"{T}test_holdout_absence.py::test_a_held_out_run_log_is_found_by_its_header",
            f"{T}test_holdout_absence.py::test_a_held_out_call_record_is_found_wherever_it_is_pasted",
            f"{T}test_holdout_absence.py::test_a_design_run_log_is_not_mistaken_for_a_held_out_one",
            f"{T}test_holdout_absence.py::test_a_held_out_record_past_the_window_or_the_cap_is_still_found",
            f"{T}test_holdout_absence.py::test_the_check_reports_a_held_out_run_log_in_the_tree_it_scans",
            f"{T}test_holdout_absence.py::test_a_rendered_report_over_held_out_calls_is_found",
            f"{T}test_holdout_absence.py::test_a_design_report_is_not_mistaken_for_a_held_out_one",
            f"{T}test_holdout_absence.py::test_every_reading_finds_its_artifact_as_a_powershell_redirect_writes_it",
            f"{T}test_holdout_absence.py::test_a_file_no_reading_can_decode_is_reported_rather_than_skipped",
            f"{T}test_holdout_absence.py::test_a_run_log_record_laid_out_across_lines_is_found",
            f"{T}test_holdout_absence.py::test_an_extraction_artifact_over_a_declared_call_is_found",
            f"{T}test_holdout_absence.py::test_held_out_labels_are_found_in_their_own_structure",
            f"{T}test_holdout_absence.py::test_design_labels_or_a_document_naming_a_held_out_id_are_not_mistaken_for_held_out_ones",
            f"{T}test_holdout_absence.py::test_agreements_held_out_section_is_found_and_its_design_section_is_not",
            f"{T}test_holdout_absence.py::test_the_check_reports_labels_agreement_and_an_undecodable_file_in_the_tree_it_scans",
        ),
        commands=((sys.executable, "tools/check_holdout_absence.py"),),
        caveat="This side is checkable and checked. That the held-out set exists in the "
        "companion repository is asserted there, not here — by construction, since checking "
        "it from here would require reaching into the tree this check exists to stay out of. "
        "Its workflow asserts that its tracked files are exactly an allowlist, that its "
        "membership matches HELDOUT_SET here, that every transcript parses clean, that the "
        "conventions this repository enforces hold there too, that its agent personas are "
        "declared, that every kind of name it uses is declared in a file of its own, that "
        "its label chain's gate passes over its own history, and that its own Python passes "
        "this repository's lint, format and type gates — none of which is asserted from "
        "here, and none of which can be.",
        spec_anchor="No held-out transcript exists anywhere",
    ),
    Criterion(
        "Every taxonomy item and every known weakness carries a disposition; no item is left "
        "without one.",
        tests=(
            f"{T}test_acceptance.py::"
            "test_every_taxonomy_item_and_known_weakness_carries_a_disposition",
            f"{T}test_acceptance.py::test_the_scenario_map_allocates_every_taxonomy_item",
        ),
        spec_anchor="Every taxonomy item and every known weakness",
    ),
    Criterion(
        "The severity file's field list agrees with the producing tool's own specification.",
        commands=(
            (
                sys.executable,
                "tools/check_spec_interface.py",
                "specs/voice-agent-eval-harness.md,specs/voice-agent-eval-harness.decisions.md,"
                "specs/voice-agent-eval-harness.build-prompt.md",
                _sibling_specs(),
            ),
        ),
        caveat=(
            "Needs the sibling repository checked out, either beside this one or inside it; "
            "`sibling_root` finds whichever is present. When neither is, this criterion "
            "FAILS rather than skipping -- a comparison of two repositories that silently "
            "passes with one of them missing is the fail-open D84 is named for."
        ),
        spec_anchor="",
    ),
)


#: Set by `_run_suite` when pytest exits non-zero. Read by `main` so that a
#: failing test **no criterion names** cannot leave this tool printing that all
#: 21 criteria pass. It could: the tool read only the JUnit nodes its own
#: `CRITERIA` list names, so a test outside that list failed in silence. That is
#: how a green report survived a suite that did not pass on a fresh clone.
_SUITE_EXIT: list[int] = []

#: What pytest printed, kept so that a non-zero exit with no failing test can be
#: reported as what it is rather than as a failing test.
_SUITE_OUTPUT: list[str] = []


def _run_suite() -> dict[str, str]:
    """node id -> 'pass' | 'fail' | 'error' | 'skip', from one pytest run.

    **The report is deleted before the run**, so a report this run did not write
    cannot be read as though it had. That is not hypothetical: on 2026-09-07 the
    JUnit path became briefly unwritable, pytest exited non-zero from its own
    reporting hook after every test had passed, and this tool read the previous
    run's XML and printed a per-criterion verdict from it. The verdict happened
    to be right, which is the worst version -- a stale report is indetectable
    when it agrees with the current one.
    """
    JUNIT.parent.mkdir(parents=True, exist_ok=True)
    JUNIT.unlink(missing_ok=True)
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", f"--junit-xml={JUNIT}", "-p", "no:cacheprovider"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    _SUITE_EXIT.append(completed.returncode)
    _SUITE_OUTPUT.append(completed.stdout + completed.stderr)
    if not JUNIT.is_file():
        return {}
    return _parse_report(JUNIT)


def _parse_report(report: Path) -> dict[str, str]:
    """node id -> verdict, from one JUnit file."""
    results: dict[str, str] = {}
    for case in ET.parse(report).getroot().iter("testcase"):
        classname = str(case.get("classname", ""))
        name = str(case.get("name", ""))
        node = classname.replace(".", "/") + ".py::" + name
        # Parametrized ids carry a [param] suffix; strip it so a criterion can
        # name the function without knowing its parameters.
        base = node.split("[")[0]
        verdict = "pass"
        if case.find("failure") is not None:
            verdict = "fail"
        elif case.find("error") is not None:
            verdict = "error"
        elif case.find("skipped") is not None:
            verdict = "skip"
        if results.get(base) in (None, "pass") or verdict != "pass":
            results[base] = verdict
    return results


#: Directories the staleness scan does **not** walk. Everything else in the
#: repository counts as source.
#:
#: This was an allow-list -- `src, tests, tools, corpus, specs` plus three named
#: root files -- and an allow-list fails in the wrong direction. Three trees the
#: suite reads sat outside it: `.github/workflows/checks.yml` (read by
#: `tests/test_phase2_acceptance.py`), `hooks/pre-commit` (driven by
#: `tests/test_hooks.py`) and the root `HELDOUT_SET` (read by
#: `tests/test_holdout_absence.py`). Editing any of them left the previous
#: report "current", so the next verifier run graded the edit against the run
#: that preceded it -- exactly the hazard `report_is_current` exists to prevent.
#:
#: A deny-list cannot fail that way. A directory nobody thought to exclude makes
#: the scan slower, or makes a report look stale when it is not, and a report
#: wrongly called stale is re-run. A file nobody thought to include made a stale
#: report look current, and there is no second chance at that.
_SCAN_EXCLUDED_DIRS: Final[frozenset[str]] = frozenset(
    {
        ".git",
        ".venv",
        "build",  # where the report being judged is written
        "__pycache__",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        ".cj-store",
        "node_modules",
    }
)


def _newest_source_mtime() -> float:
    """The newest mtime anywhere in the repository, caches aside."""
    newest = 0.0
    for parent, directories, files in os.walk(REPO_ROOT):
        directories[:] = [d for d in directories if d not in _SCAN_EXCLUDED_DIRS]
        for name in files:
            try:
                newest = max(newest, (Path(parent) / name).stat().st_mtime)
            except OSError:
                # A file that vanished between listing and stat is not a reason
                # to fail the run; the scan's answer is "at least this new", and
                # a missed file can only make a report look older than it is.
                continue
    return newest


def _display(path: Path) -> str:
    """Repo-relative when it can be, absolute otherwise.

    A progress line should never be able to fail the run it is reporting on.
    """
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def report_is_current(report: Path) -> bool:
    """Whether this JUnit file still describes the tree as it stands.

    Separated from `load_suite_results` so a control can drive the decision
    without running the suite to observe it -- the same reason
    `_event_scoped_disagreements` is separated from its test.
    """
    return report.is_file() and report.stat().st_mtime >= _newest_source_mtime()


def _report_verdict(report: Path) -> tuple[int, str]:
    """What a reused report says about the suite as a whole.

    The reuse path appended `0` to `_SUITE_EXIT` unconditionally, so both
    verifiers printed "The suite as a whole passed too, not only the tests these
    criteria name" without reading anything about failures. A report carrying a
    failing test that no criterion names earned that sentence -- which is the
    exact claim `_SUITE_EXIT` was added to stop being made on faith, one path
    over from where it was added.

    Read from the `<testsuite>` counters rather than from the per-case scan
    alone: `_parse_report` collapses parametrized ids, and a collection error
    can raise the counter without producing a `<testcase>` anybody could name.
    Both are consulted, and either one is enough to refuse.
    """
    failures = errors = 0
    cases: list[str] = []
    try:
        root = ET.parse(report).getroot()
    except ET.ParseError as broken:
        return 1, f"{_display(report)} is not parseable as JUnit XML: {broken}"
    for suite in root.iter("testsuite"):
        failures += int(suite.get("failures") or 0)
        errors += int(suite.get("errors") or 0)
    for verdict in _parse_report(report).values():
        if verdict in {"fail", "error"}:
            cases.append(verdict)
    if not failures and not errors and not cases:
        return 0, ""
    return 1, (
        f"{_display(report)} records {failures} failure(s) and {errors} error(s) "
        f"across {len(cases)} test(s). This verdict was read from the reused "
        "report, not from a pytest run; re-run the suite to see the output."
    )


def load_suite_results(report: Path | None) -> dict[str, str]:
    """Read an existing JUnit report when it still describes this tree, else run.

    Both phase verifiers each ran the whole suite, and CI ran it a third time
    as its own step -- three runs of the same tests per push, while D113 said
    "there is one test suite, so there is one run to read". That sentence was
    true of the *function* the two verifiers share and false of the *run*.

    Reuse is opt-in and never silent. A report older than the newest source
    file is **reported as stale and re-run**, not trusted: the whole reason
    `_run_suite` deletes its report before running is that a stale report is
    undetectable when it agrees, and a reuse path that quietly accepted one
    would put that hazard back with a flag on it.
    """
    if report is None:
        return _run_suite()
    # Resolve before anything reads or prints it. A relative path passed on the
    # command line is the ordinary case, and `Path.relative_to` raises for one
    # -- which is how the first draft of the progress line below crashed the
    # run it was reporting on. `harness.extract._display` exists because that
    # happened once already; this is the same lesson, one tool over.
    report = report if report.is_absolute() else (Path.cwd() / report).resolve()
    if not report_is_current(report):
        reason = (
            "no JUnit report at" if not report.is_file() else "older than the newest source file:"
        )
        print(f"{reason} {report}; running the suite", file=sys.stderr)
        return _run_suite()

    print(f"reading {_display(report)} rather than re-running the suite")
    exit_code, summary = _report_verdict(report)
    _SUITE_EXIT.append(exit_code)
    _SUITE_OUTPUT.append(summary)
    return _parse_report(report)


def run_suite() -> dict[str, str]:
    """The same run, readable by a later phase's verifier.

    Public rather than a second copy. `_run_suite` carries two lessons that
    cost a session each -- the report is deleted before the run, and a non-zero
    exit with no failing test is reported as what it is -- and a duplicate of
    that machinery in `verify_phase2.py` would be two places for those lessons
    to drift apart. There is one test suite, so there is one run to read.

    The import direction is odd and is the price: phase 2's verifier imports
    phase 1's. When a third phase needs it, this and `Criterion` move to
    `tools/phase_verifier.py` and both import from there (D113).
    """
    return _run_suite()


def diagnose_suite_exit(exit_code: int, results: dict[str, str]) -> list[str]:
    """Why pytest exited non-zero, in the words that send a reader to the right place.

    Two different things exit non-zero and they need different sentences. **A
    failing test** is the case this branch was written for. **A pytest that
    could not write its own report** is the case that arrived on 2026-09-07,
    when the JUnit path was briefly unwritable: every test passed, pytest exited
    1 from its own reporting hook, and this tool said "a test that no criterion
    names still failed". A reader then looks for a failure that does not exist,
    which is a worse outcome than saying nothing.

    Public, and separated from `main`, so the control can drive it. The message
    is the whole product of this branch, and a message nothing exercises is the
    shape this repository keeps finding in itself.
    """
    broken = sorted(node for node, verdict in results.items() if verdict in {"fail", "error"})
    lines = [f"PHASE 1 NOT COMPLETE — every criterion passed, but pytest exited {exit_code}."]
    if broken:
        lines.append("A test that no criterion names still failed:")
        lines += [f"  {node}" for node in broken]
        return lines
    if not results:
        lines.append("pytest wrote no JUnit report, so nothing above was read from this run.")
        lines.append(f"The report path is {JUNIT.relative_to(REPO_ROOT).as_posix()}.")
        lines.append("Read the pytest output below rather than looking for a failing test.")
        return lines
    lines.append("No test in the report failed, so the non-zero exit did not come from a")
    lines.append("test. pytest exits non-zero for its own reasons too -- a reporting hook")
    lines.append("that cannot write, a collection error, a usage error. Read its output:")
    return lines


def criteria_in_document(criteria: Sequence[Criterion], phase: int) -> int:
    """How many entries anchor into a `[Pn]` **acceptance criterion**.

    Not the same as how many are anchored, and the difference was printed as
    though it were: `verify_phase3` reported "21 of them the specification's own
    [P3] acceptance criteria" over a document carrying 18, because three of its
    anchors point into requirement prose -- the non-functional lines about
    network access, citable-identifier syntax and whether the specified backoff
    replaces the SDK's. Each is worth running and none is an acceptance
    criterion, so the sentence overstated the document by three.

    Named rather than inlined so the phase-acceptance tests read the number the
    summary prints instead of recomputing it beside the printer -- which is the
    shape D121 found in six controls, every one of them measuring nothing.

    Criteria are matched by bullet shape rather than by section heading: a
    criterion moved between subsections is still a criterion, and a scan keyed
    on headings would drop it.
    """
    document = SPEC.read_text(encoding="utf-8")
    marker = f"[P{phase}"
    lines = [
        stripped
        for line in document.splitlines()
        if (stripped := line.strip()).startswith(("- [ ] ", "- [x] "))
        if f"{marker}]" in stripped or f"{marker}," in stripped
    ]
    return sum(
        1
        for criterion in criteria
        if criterion.spec_anchor and any(criterion.spec_anchor in line for line in lines)
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="verify_phase1", description=__doc__)
    parser.add_argument(
        "--junit",
        default=None,
        help=(
            "read this JUnit report instead of running the suite. Ignored when the report "
            "is missing or older than the newest source file, so a stale one is re-run "
            "rather than trusted."
        ),
    )
    args = parser.parse_args(argv)
    results = load_suite_results(Path(args.junit) if args.junit else None)

    width = 4
    failures = 0
    caveats: list[tuple[int, str]] = []

    for number, criterion in enumerate(CRITERIA, start=1):
        states: list[str] = []
        # What a failing command actually said. It was captured and discarded,
        # so the report read `fail` and nothing else -- and the first CI run to
        # execute this tool failed on a command whose message ("not a file")
        # named the cause exactly, in output nobody printed. Diagnosing it took
        # a local reproduction of a one-line error the run already had.
        command_output: list[str] = []
        for node in criterion.tests:
            verdict = results.get(node)
            states.append("MISSING" if verdict is None else verdict)
        for command in criterion.commands:
            completed = subprocess.run(
                list(command), cwd=REPO_ROOT, capture_output=True, text=True, check=False
            )
            states.append("pass" if completed.returncode == 0 else "fail")
            if completed.returncode != 0:
                said = (completed.stdout + completed.stderr).strip()
                command_output.append(
                    f"exit {completed.returncode}: {said[-500:]}"
                    if said
                    else f"exit {completed.returncode}, and it printed nothing"
                )

        if not states:
            verdict = "NO EVIDENCE"
        elif all(state == "pass" for state in states):
            verdict = "PASS"
        elif "MISSING" in states:
            verdict = "EVIDENCE MISSING"
        else:
            verdict = "FAIL"

        if verdict != "PASS":
            failures += 1
        mark = "OK " if verdict == "PASS" else "!! "
        print(f"{mark}{number:>{width - 2}}. [{verdict}] {criterion.text}")
        for node in criterion.tests:
            print(f"        {results.get(node, 'MISSING'):>7}  {node}")
        for command in criterion.commands:
            printable = " ".join(str(part) for part in command).replace(sys.executable, "python")
            print(f"        {'ran':>7}  {printable}")
        for said in command_output:
            for line in said.splitlines():
                print(f"        {'':>7}  {line}")
        if criterion.caveat:
            caveats.append((number, criterion.caveat))
        print()

    if caveats:
        print("=" * 78)
        print("NOT FULLY CHECKABLE BY MACHINE — read these rather than the ticks")
        print("=" * 78)
        for number, caveat in caveats:
            print(f"\n  {number}. {caveat}")
        print()

    print("=" * 78)
    if failures:
        print(f"PHASE 1 NOT COMPLETE — {failures} of {len(CRITERIA)} criteria did not pass")
        return 1

    # A failing test that no criterion names used to be invisible here: this
    # tool read only the JUnit nodes `CRITERIA` mentions, so the suite could be
    # red while every tick above was green. That is not hypothetical -- it is
    # how "All 21 criteria pass" was printed by a repository whose suite did not
    # pass on a fresh clone.
    suite_exit = _SUITE_EXIT[0] if _SUITE_EXIT else None
    if suite_exit:
        # Two different things exit non-zero here and they need different
        # sentences. A failing test is the case this branch was written for. A
        # pytest that could not write its own report is the case that arrived
        # later, and calling that "a test failed" sent a reader to look for a
        # failure that did not exist.
        for line in diagnose_suite_exit(suite_exit, results):
            print(line)
        print((_SUITE_OUTPUT[0] if _SUITE_OUTPUT else "").strip()[-700:])
        return 1

    anchored = sum(1 for criterion in CRITERIA if criterion.spec_anchor)
    in_criteria = criteria_in_document(CRITERIA, 1)
    in_requirements = anchored - in_criteria
    sentence = (
        f"All {len(CRITERIA)} checks pass, each by running it — "
        f"{in_criteria} of them the specification's own [P1] acceptance criteria"
    )
    if in_requirements:
        sentence += f", {in_requirements} its [P1] requirement prose"
    print(sentence + ".")
    print(f"{len(caveats)} carry a stated caveat above; a tick is not a claim they do not.")
    print("The suite as a whole passed too, not only the tests these criteria name.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
