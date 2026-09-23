"""The phase-2 verifier's list, bound to the document it claims to verify.

`tools/verify_phase1.py` printed "All 21 phase-1 acceptance criteria pass"
while counting its own list, so a criterion added to the specification and
never added to the tool was invisible. The same binding is here from the
start: every `[P2]` criterion in the specification must be claimed by an entry
carrying a distinctive substring of it, and every test node an entry names must
exist in the suite.
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Final

import pytest
import yaml
from tools.verify_phase2 import CRITERIA

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
SPEC: Final[str] = (REPO_ROOT / "specs" / "voice-agent-eval-harness.md").read_text(encoding="utf-8")
WORKFLOW: Final[Path] = REPO_ROOT / ".github" / "workflows" / "checks.yml"


def _p2_criteria() -> list[str]:
    lines = [
        line.strip()
        for line in SPEC.splitlines()
        if re.match(r"^- \[[ x]\] \[P2[,\]]", line.strip())
    ]
    assert len(lines) >= 20, f"only {len(lines)} [P2] criteria parsed; the marker shape changed"
    return lines


def test_every_p2_criterion_in_the_specification_is_claimed_by_the_verifier() -> None:
    unclaimed = [
        line[:100]
        for line in _p2_criteria()
        if not any(c.spec_anchor and c.spec_anchor in line for c in CRITERIA)
    ]
    assert not unclaimed, (
        "[P2] acceptance criteria that no entry in tools/verify_phase2.py claims:\n  "
        + "\n  ".join(unclaimed)
    )


def test_every_anchor_points_into_the_specification() -> None:
    """An anchor that matches nothing claims a criterion that is not there."""
    for criterion in CRITERIA:
        if not criterion.spec_anchor:
            continue
        assert criterion.spec_anchor in SPEC, (
            f"the anchor {criterion.spec_anchor!r} appears nowhere in the specification, so "
            "this entry claims a criterion the document does not carry"
        )


def test_the_unanchored_entries_are_the_declared_extras() -> None:
    """Two entries are deliberately not specification criteria.

    The gold-set agreement gate (D105) and the negative-instance rule (D107)
    are decisions this phase made, not lines the document carries. Naming them
    here stops a reader treating the count difference as drift.
    """
    unanchored = [criterion.text[:60] for criterion in CRITERIA if not criterion.spec_anchor]
    assert len(unanchored) == 2, unanchored
    assert any("agree with the gold set" in c.text for c in CRITERIA if not c.spec_anchor)
    assert any("silent on" in c.text for c in CRITERIA if not c.spec_anchor)


def test_every_criterion_names_evidence_that_still_exists() -> None:
    """A node id that has been renamed shows here rather than as MISSING later."""
    missing: list[str] = []
    for criterion in CRITERIA:
        for node in criterion.tests:
            path, _, name = node.partition("::")
            source = REPO_ROOT / path
            if not source.is_file():
                missing.append(f"{node} (no such file)")
                continue
            if f"def {name}(" not in source.read_text(encoding="utf-8"):
                missing.append(node)
    assert not missing, "criteria naming evidence that does not exist:\n  " + "\n  ".join(missing)


def test_no_criterion_is_left_with_no_evidence_at_all() -> None:
    empty = [c.text[:70] for c in CRITERIA if not c.tests and not c.commands]
    assert not empty, f"criteria with neither a test nor a command: {empty}"


# --------------------------------------------------------------------------
# The CI workflow
# --------------------------------------------------------------------------


def test_the_workflow_runs_every_gate_this_phase_declares() -> None:
    """The criterion names four gates; the workflow has to run all of them.

    Read from the workflow's own steps rather than from a memory of what CI
    does, because a step deleted in a hurry is exactly the edit nobody
    announces.
    """
    document = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = document["jobs"]["checks"]["steps"]
    commands = "\n".join(str(step.get("run", "")) for step in steps)

    for gate, fragment in (
        ("type check", "mypy"),
        ("lint", "ruff check"),
        ("format check", "ruff format --check"),
        ("test suite", "pytest"),
        ("interface scanner", "check_spec_interface.py"),
    ):
        assert fragment in commands, f"the workflow no longer runs the {gate} ({fragment!r})"


def test_the_workflow_runs_the_deterministic_tier_and_its_verifier() -> None:
    """Phase 2 adds two things CI has to run, or the phase is verified only on
    the machine that happens to run it by hand.

    The name says "the deterministic tier **and** its verifier"; the body
    asserted only the second half, so deleting the `harness run --tier assert`
    step would have left this green. That step is also the one line in the
    workflow encoding D105: the run exits 1 over a corpus seeded with defects,
    and `|| [ $? -eq 1 ]` accepts exactly that and nothing else. Dropping the
    guard turns the expected exit into a red build; widening it to `|| true` or
    `continue-on-error` accepts a rubric that does not load (2) and a tier that
    could not complete (3). Both directions are asserted, because a guard is
    wrong in two ways and only one of them is visible in a green run.
    """
    document = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = document["jobs"]["checks"]["steps"]
    commands = "\n".join(str(step.get("run", "")) for step in steps)
    assert "tools.verify_phase2" in commands, "CI does not run the phase-2 verifier"
    assert "verify_phase1.py" in commands, (
        "CI does not run the phase-1 verifier, so a phase-2 change regressing phase 1 is "
        "caught only by whoever remembers to run it"
    )

    tier_steps = [step for step in steps if "harness run" in str(step.get("run", ""))]
    assert len(tier_steps) == 1, (
        "CI does not run `harness run --tier assert` exactly once, so the P2 criterion "
        "naming that command is verified only by whoever remembers to run it"
    )
    step = tier_steps[0]
    command = str(step["run"])
    assert "--tier assert" in command, "the run step does not select the deterministic tier"
    assert "[ $? -eq 1 ]" in command, (
        "the run step no longer accepts exit 1, so the expected outcome over a corpus "
        "seeded with defects (D105) fails the build"
    )
    assert "|| true" not in command and not step.get("continue-on-error"), (
        "the run step accepts every exit code, so a rubric that does not load (2) or a "
        "tier that could not complete (3) passes CI as though the gates had held"
    )


@pytest.mark.parametrize("verifier", ["verify_phase1.py", "verify_phase2.py"])
def test_each_verifier_is_executable_and_reads_the_same_suite_run(verifier: str) -> None:
    """One suite, one run, read twice.

    `verify_phase2` imports the runner from `verify_phase1` rather than keeping
    a copy: that machinery carries the delete-the-report-first lesson and the
    non-zero-exit-with-no-failure lesson, and two copies would be two places
    for those to drift (D113).
    """
    source = (REPO_ROOT / "tools" / verifier).read_text(encoding="utf-8")
    # What this asserts is that the module is runnable and takes the report
    # flag -- not a literal signature. The first draft matched
    # `def main() -> int:` exactly and broke the moment `main` gained an
    # argument, which is a guard narrower than the rule it stands for.
    assert re.search(r"^def main\(", source, re.MULTILINE), f"{verifier} has no main"
    assert 'if __name__ == "__main__":' in source
    assert '"--junit"' in source, (
        f"{verifier} cannot be pointed at an existing report, so CI has to spawn a second "
        "pytest run for it"
    )
    if verifier == "verify_phase2.py":
        assert "from tools.verify_phase1 import" in source
        assert "def _run_suite" not in source, (
            "the phase-2 verifier has grown its own copy of the suite runner"
        )


def test_a_report_older_than_the_sources_is_not_reused(tmp_path: Path) -> None:
    """The staleness decision, driven directly rather than through a suite run.

    D113 said "there is one test suite, so there is one run to read" and that
    was true of the function the two verifiers share and false of the run: each
    spawned its own pytest, and CI ran a third as its own step. Reuse fixes
    that, and it must never reuse a report that no longer describes the tree --
    the whole reason `_run_suite` deletes its report before running is that a
    stale report is undetectable when it agrees.
    """
    from tools.verify_phase1 import report_is_current

    missing = tmp_path / "absent.xml"
    assert report_is_current(missing) is False

    stale = tmp_path / "stale.xml"
    stale.write_text("<testsuite/>", encoding="utf-8")
    os.utime(stale, (0, 0))
    assert report_is_current(stale) is False, (
        "a report timestamped at the epoch is being treated as current, so an edit made "
        "after a run would be verified against the run that preceded it"
    )

    fresh = tmp_path / "fresh.xml"
    fresh.write_text("<testsuite/>", encoding="utf-8")
    os.utime(fresh, (time.time() + 3600, time.time() + 3600))
    assert report_is_current(fresh) is True


def test_ci_writes_the_report_once_and_both_verifiers_read_it() -> None:
    """One run per push, asserted from the workflow rather than from intent."""
    document = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    commands = [str(step.get("run", "")) for step in document["jobs"]["checks"]["steps"]]
    joined = "\n".join(commands)

    assert "--junit-xml=build/phase1-junit.xml" in joined, (
        "the pytest step does not write a report for the verifiers to read"
    )
    for verifier in ("verify_phase1.py", "tools.verify_phase2"):
        line = next(c for c in commands if verifier in c)
        assert "--junit build/phase1-junit.xml" in line, (
            f"the {verifier} step does not read the report, so it spawns its own pytest run"
        )
    assert sum(1 for c in commands if "pytest" in c) == 1, "more than one step runs pytest directly"


def test_the_reuse_path_accepts_the_relative_path_ci_passes_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The guard that would have caught the crash this fix shipped with.

    Nothing exercised `load_suite_results` with a real argument until it was
    run for the first time, and it raised: `Path.relative_to` on a relative
    path, inside the progress line announcing the reuse. That is the defect
    `harness.extract._display` exists because of -- a progress line failing the
    run it reports on -- reintroduced one tool over.

    CI passes `--junit build/phase1-junit.xml`, a relative path, which is why
    that is what this passes.
    """
    from tools.verify_phase1 import load_suite_results

    report = tmp_path / "junit.xml"
    # A real node id rather than an invented one. `test_every_test_name_in_prose_exists`
    # reads test names out of string literals and refuses ones this tree does
    # not have -- correctly, and declaring an exemption for a fixture would be
    # the carve-out a later reader extends. Naming a test that exists costs
    # nothing and shows the exact node-id shape the parser produces.
    node = "test_no_criterion_is_left_with_no_evidence_at_all"
    report.write_text(
        f'<testsuites><testsuite><testcase classname="tests.test_phase2_acceptance" '
        f'name="{node}"/></testsuite></testsuites>',
        encoding="utf-8",
    )
    os.utime(report, (time.time() + 3600, time.time() + 3600))

    monkeypatch.chdir(tmp_path)
    results = load_suite_results(Path("junit.xml"))
    assert results == {f"tests/test_phase2_acceptance.py::{node}": "pass"}
    assert "rather than re-running" in capsys.readouterr().out


def test_a_reused_report_with_a_failing_test_does_not_earn_the_pass_sentence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The reuse path read node verdicts and asserted nothing about the suite.

    `load_suite_results` appended `0` to `_SUITE_EXIT` whenever it reused a
    report, so both verifiers printed "The suite as a whole passed too, not only
    the tests these criteria name" without reading a single failure count. That
    sentence is the reason `_SUITE_EXIT` exists -- it was added because "All 21
    criteria pass" had been printed by a tree whose suite was red -- and the
    reuse path put the hazard back with the claim still printed.

    Both channels are asserted: the `<testsuite>` counters, and a `<failure>`
    element on a case no criterion names.
    """
    import tools.verify_phase1 as verifier

    monkeypatch.setattr(verifier, "_SUITE_EXIT", [])
    monkeypatch.setattr(verifier, "_SUITE_OUTPUT", [])

    report = tmp_path / "junit.xml"
    node = "test_no_criterion_is_left_with_no_evidence_at_all"
    report.write_text(
        '<testsuites><testsuite failures="1" errors="0">'
        f'<testcase classname="tests.test_phase2_acceptance" name="{node}">'
        '<failure message="assert 0">boom</failure></testcase>'
        "</testsuite></testsuites>",
        encoding="utf-8",
    )
    os.utime(report, (time.time() + 3600, time.time() + 3600))

    results = verifier.load_suite_results(report)
    assert results == {f"tests/test_phase2_acceptance.py::{node}": "fail"}
    assert verifier._SUITE_EXIT == [1], (
        "a reused report recording a failure still reports the suite as passing, so both "
        "verifiers would print that the suite passed"
    )
    assert "1 failure(s)" in verifier._SUITE_OUTPUT[0]


def test_a_clean_reused_report_still_reports_the_suite_as_passing(tmp_path: Path) -> None:
    """The planted pass.

    A verdict derived from the report is worthless if it refuses every report:
    the reuse path would then re-run the suite every time, which is the cost
    D113 added it to avoid.
    """
    from tools.verify_phase1 import _report_verdict

    report = tmp_path / "clean.xml"
    node = "test_no_criterion_is_left_with_no_evidence_at_all"
    report.write_text(
        '<testsuites><testsuite failures="0" errors="0">'
        f'<testcase classname="tests.test_phase2_acceptance" name="{node}"/>'
        "</testsuite></testsuites>",
        encoding="utf-8",
    )
    assert _report_verdict(report) == (0, "")


def test_the_staleness_scan_covers_every_tree_the_suite_reads() -> None:
    """Three trees the suite reads sat outside the scan's allow-list.

    `.github/workflows/checks.yml` is read by the workflow tests in this file,
    `hooks/pre-commit` is driven by `tests/test_hooks.py`, and the root
    `HELDOUT_SET` is read by `tests/test_holdout_absence.py`. None was under
    `src, tests, tools, corpus, specs`, so editing any of them left the previous
    report current and the edit was then graded against the run before it.

    Asserted against the real repository, because the property is "this scan
    covers this repository"; a fixture tree would only restate the deny-list
    back to itself.

    Each path is moved into the future and the scan's answer must move with it.
    Comparing the existing mtimes against the baseline would not have failed
    against the old allow-list -- any edit anywhere under `src` or `tools` makes
    those files older than the newest, which is a neighbor of the property, not
    the property.
    """
    from tools.verify_phase1 import REPO_ROOT as root
    from tools.verify_phase1 import _newest_source_mtime

    for relative in (
        Path(".github") / "workflows" / "checks.yml",
        Path("hooks") / "pre-commit",
        Path("HELDOUT_SET"),
    ):
        path = root / relative
        assert path.is_file(), f"{relative.as_posix()} is gone; this test names a path that moved"
        original = (path.stat().st_atime, path.stat().st_mtime)
        baseline = _newest_source_mtime()
        ahead = time.time() + 7200
        try:
            os.utime(path, (ahead, ahead))
            assert _newest_source_mtime() > baseline, (
                f"editing {relative.as_posix()} does not move the staleness scan, so a report "
                "written before that edit is still treated as describing this tree"
            )
        finally:
            os.utime(path, original)


def test_the_report_being_judged_cannot_make_itself_current() -> None:
    """`build/` is excluded, and it has to be.

    The scan now walks the whole tree rather than five named roots, and the
    JUnit report lives in the tree. Were `build/` scanned, writing the report
    would set the newest mtime to the report's own, and `report_is_current`
    would return True for every report ever written -- the staleness guard
    reduced to a tautology by the change that widened it.

    **This test wrote the report when there is none, rather than skipping.**
    It used to skip, and the condition it skipped on is the one CI always meets:
    pytest writes `--junit-xml` at the *end* of a session, `build/` is
    gitignored, so on a fresh checkout the file does not exist while the tests
    run. The guard against the staleness scan becoming a tautology had therefore
    only ever executed on a machine with a previous run's report lying around --
    the one place it is least needed. Nothing was falsely claimed, because no
    verifier criterion names this test and a skipped test cannot tick one
    (`verify_phase1` records `skip` as its own verdict and a criterion passes
    only when every named test is `pass`). What was missing was the run.

    Creating the file also widens what is asserted: the baseline is taken before
    the file exists, so **its appearance and its mtime are both invisible** to
    the scan, not only its mtime.
    """
    from tools.verify_phase1 import JUNIT, _newest_source_mtime

    baseline = _newest_source_mtime()
    JUNIT.parent.mkdir(parents=True, exist_ok=True)
    original = (JUNIT.stat().st_atime, JUNIT.stat().st_mtime) if JUNIT.is_file() else None
    if original is None:
        # Well-formed enough to be a report; nothing here parses it, and it is
        # removed again below. pytest writes the real one when the session ends.
        JUNIT.write_text('<?xml version="1.0" encoding="utf-8"?>\n<testsuites />\n', "utf-8")
    ahead = time.time() + 7200
    try:
        os.utime(JUNIT, (ahead, ahead))
        assert _newest_source_mtime() == baseline, (
            "the report's own mtime moved the scan's answer, so every report would be current"
        )
    finally:
        if original is None:
            JUNIT.unlink(missing_ok=True)
        else:
            os.utime(JUNIT, original)
