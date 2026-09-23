"""Phase-1 acceptance criteria that were otherwise passing by inspection.

The build prompt's rule is to verify each criterion **by running it**. Most are
covered by the module that owns the thing they check. These four were not: they
were true, and nothing would have noticed them becoming false.

The one worth reading is `test_the_documented_hook_installation_actually_works`.
The criterion is not "the hook file exists" but "following the documented
installation reproduces both refusals in a scratch clone", and those are
different claims -- the second is the one a reader of this repository actually
depends on.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tomllib
from collections.abc import Iterable
from pathlib import Path
from typing import Final

import pytest
from tools.verify_phase1 import CRITERIA

REPO_ROOT: Path = Path(__file__).resolve().parents[1]

POPULATED_ENV: Final[str] = "API_KEY=sk-not-a-real-key-01234567\n"


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=check)


# --------------------------------------------------------------------------
# The repo-hygiene floor, asserted against git history rather than the tree
# --------------------------------------------------------------------------


def test_the_hygiene_floor_was_in_the_first_commit() -> None:
    """ "Present in the first commit" is the criterion, and it is not the same
    claim as "present now".

    A repository built private and flipped public publishes its history
    retroactively, so a guard added in week three does not protect week one.
    The only way to check this is to read the first commit.
    """
    first = _git(REPO_ROOT, "rev-list", "--max-parents=0", "HEAD").stdout.strip().split("\n")[0]
    listing = _git(REPO_ROOT, "ls-tree", "-r", "--name-only", first).stdout.split("\n")
    names = {line.strip() for line in listing if line.strip()}

    assert ".gitignore" in names
    assert "LICENSE" in names
    assert "LICENSE-CC-BY" in names

    ignore = _git(REPO_ROOT, "show", f"{first}:.gitignore").stdout
    for entry in (".env", "private/", "__pycache__/", "*.pyc"):
        assert entry in ignore, f"{entry!r} was not in the first commit's .gitignore"


def test_both_licenses_exist_now_too() -> None:
    assert (REPO_ROOT / "LICENSE").is_file()
    assert (REPO_ROOT / "LICENSE-CC-BY").is_file()
    assert "Apache License" in (REPO_ROOT / "LICENSE").read_text(encoding="utf-8")


def test_the_format_specification_exists_and_names_its_version() -> None:
    spec = REPO_ROOT / "specs" / "transcript-format.md"
    assert spec.is_file()
    text = spec.read_text(encoding="utf-8")
    assert "voice-agent-eval-harness/transcript v2" in text


# --------------------------------------------------------------------------
# Reproducibility: pins, not floors
# --------------------------------------------------------------------------


def _unpinned(declared: Iterable[str]) -> list[str]:
    """The declared requirements that are not an exact pin.

    Only the version specifier is judged. An environment marker follows a `;`
    and makes comparisons of its own -- `python_version < "3.13"` -- which say
    where a requirement applies rather than which versions satisfy it, so the
    text from the `;` on is set aside before any clause looks.

    Four clauses, and each catches a requirement none of the others does: a
    compatible release such as `~=2.5` has no `==`, a pin with a floor bolted on
    has `==` and a `>`, a pin with a ceiling bolted on has `==` and a `<`, and a
    prefix match such as `==2.*` has `==`, no `>` and no `<`, and is a range all
    the same. The guard and its control both call this, so the rule is stated
    once and the control proves the statement the guard applies.
    """
    specifiers = ((requirement, requirement.split(";", 1)[0]) for requirement in declared)
    return [
        requirement
        for requirement, specifier in specifiers
        if "==" not in specifier or ">" in specifier or "<" in specifier or "*" in specifier
    ]


def test_no_dependency_is_expressed_only_as_a_floor() -> None:
    """W35 measured: a dependency file that stated floors and called them pins,
    in a project whose thesis is reproducibility.

    `requires-python` is deliberately excluded. It is an interpreter
    compatibility range, and pinning it to one version would be a different and
    worse claim.
    """
    config = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    declared: list[str] = list(config["project"]["dependencies"])
    for group in config.get("dependency-groups", {}).values():
        declared.extend(str(item) for item in group)

    assert declared, "no dependencies declared at all"
    unpinned = _unpinned(declared)
    assert not unpinned, f"expressed as a floor or a range rather than a pin: {unpinned}"


def test_the_pin_rule_would_notice_every_shape_of_range() -> None:
    """The control, because a repository that is already pinned proves nothing.

    The guard beside it had none, and was narrower than its name: it required
    `==` and refused `>`, so a pin with a ceiling and a prefix match both passed
    it, and with every declared requirement an exact pin nothing it missed was
    there to find. The rule and this control are comparative-judgment's, where
    the measurement was made first.

    One planted requirement per clause, each one only that clause flags,
    because a requirement two clauses both flag survives the deletion of either.
    The bare floor is that kind -- it has no `==` and it has a `>` -- and stays
    as the plainest statement of what the guard is for, not as proof of any one
    clause. The exact pin is planted so a rule that flags everything fails here
    too, and a marker is planted both ways: an exact pin whose marker compares a
    version must pass, and a floor behind a marker must still fail, so neither
    judging the marker nor skipping every marked requirement survives.
    """
    assert _unpinned(["numpy>=2.0"]) == ["numpy>=2.0"]
    assert _unpinned(["numpy~=2.5"]) == ["numpy~=2.5"], (
        "a compatible release has no `==`, `>` or `<`; only the missing `==` flags it"
    )
    assert _unpinned(["numpy==2.5.2,>=2"]) == ["numpy==2.5.2,>=2"], (
        "a pin with a floor attached; only the `>` flags it"
    )
    assert _unpinned(["numpy==2.5.2,<3"]) == ["numpy==2.5.2,<3"], (
        "a pin with a ceiling attached; only the `<` flags it"
    )
    assert _unpinned(["numpy==2.*"]) == ["numpy==2.*"], (
        "a prefix match is a range with no `>` or `<` in it; only the `*` flags it"
    )
    assert _unpinned(["numpy==2.5.2"]) == [], "an exact pin was flagged"

    marked_pin = 'pytest==9.1.1; python_version < "3.13"'
    marked_floor = 'numpy>=2.0; python_version < "3.13"'
    assert _unpinned([marked_pin]) == [], "an exact pin was flagged for its marker"
    assert _unpinned([marked_floor]) == [marked_floor], "a floor escaped behind a marker"


def test_the_lockfile_exists_and_pins_every_declared_dependency() -> None:
    lock = REPO_ROOT / "uv.lock"
    assert lock.is_file()
    text = lock.read_text(encoding="utf-8")

    config = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    declared: list[str] = list(config["project"]["dependencies"])
    for group in config.get("dependency-groups", {}).values():
        declared.extend(str(item) for item in group)

    for requirement in declared:
        name, _, version = requirement.partition("==")
        normalized = name.strip().lower().replace("_", "-")
        assert f'name = "{normalized}"' in text, f"{name} is not in the lockfile"
        assert f'version = "{version.strip()}"' in text, (
            f"{name} is pinned to {version.strip()} but the lockfile does not carry that version"
        )


# --------------------------------------------------------------------------
# Coverage bookkeeping
# --------------------------------------------------------------------------


def test_every_taxonomy_item_and_known_weakness_carries_a_disposition() -> None:
    """A gap is a recorded decision; a blank is an oversight, and only one of
    those is acceptable at a phase boundary."""
    text = (REPO_ROOT / "specs" / "taxonomy-coverage.md").read_text(encoding="utf-8")

    # Taxonomy rows look like `| 12 | **Title.** ... | **DISPOSITION** ... |`
    taxonomy = {
        int(m.group(1))
        for m in re.finditer(r"^\|\s*(\d{1,2})\s*\|\s*\*\*.+?\|.+?\|\s*$", text, re.MULTILINE)
    }
    missing = sorted(set(range(1, 36)) - taxonomy)
    assert not missing, f"taxonomy items with no disposition row: {missing}"

    weaknesses = {
        int(m.group(1)) for m in re.finditer(r"^\|\s*W(\d{1,2})\s*\|", text, re.MULTILINE)
    }
    missing_w = sorted(set(range(1, 36)) - weaknesses)
    assert not missing_w, f"known weaknesses with no disposition row: {missing_w}"


def test_the_scenario_map_allocates_every_taxonomy_item() -> None:
    text = (REPO_ROOT / "specs" / "taxonomy-scenario-map.md").read_text(encoding="utf-8")
    mapped = {
        int(m.group(1))
        for m in re.finditer(r"^\|\s*(\d{1,2})\s*\|.+?\|.+?\|\s*$", text, re.MULTILINE)
    }
    missing = sorted(set(range(1, 36)) - mapped)
    assert not missing, f"taxonomy items absent from the scenario map: {missing}"


# --------------------------------------------------------------------------
# The documented installation, not merely the hook file
# --------------------------------------------------------------------------


def test_the_hook_source_is_present_under_a_documented_path() -> None:
    assert (REPO_ROOT / "hooks" / "pre-commit").is_file()
    readme = (REPO_ROOT / "hooks" / "README.md").read_text(encoding="utf-8")
    assert "core.hooksPath" in readme, "the README must address the case that breaks Case 1"
    assert "hooks/pre-commit" in readme


def test_the_documented_hook_installation_actually_works(tmp_path: Path) -> None:
    """Clone, follow `hooks/README.md`, and attempt both forbidden commits.

    ONE LINE HERE IS THE WHOLE POINT OF D14. The clone gets
    `core.hooksPath` set to its own `.git/hooks`, because on the machine this
    was written the setting is global -- and while it is, a repo-local hook
    NEVER FIRES. Without that line this test fails, and the failure is the
    documented behavior rather than a bug: it is exactly why the README has a
    Case 2 at all, and exactly why the guards are declared machine-level
    controls this repository provides but cannot install for you.

    Setting it locally reproduces a machine with no global hooks path, which is
    the reader Case 1 is written for.
    """
    clone = tmp_path / "clone"
    _git(tmp_path, "clone", "--quiet", "--no-hardlinks", str(REPO_ROOT), str(clone))
    _git(clone, "config", "user.email", "test@example.invalid")
    _git(clone, "config", "user.name", "Test")
    _git(clone, "config", "core.autocrlf", "false")
    _git(clone, "config", "core.hooksPath", ".git/hooks")

    # The documented Case 1 install, in its copy form.
    hooks_dir = clone / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    target = hooks_dir / "pre-commit"
    target.write_text(
        (clone / "hooks" / "pre-commit").read_text(encoding="utf-8"), encoding="utf-8", newline=""
    )
    target.chmod(0o755)

    (clone / ".env").write_text(POPULATED_ENV, encoding="utf-8", newline="")
    _git(clone, "add", "-f", ".env")
    refused_env = _git(clone, "commit", "-m", "should be refused", check=False)
    assert refused_env.returncode != 0, "a populated .env was committed in a scratch clone"
    assert "SECRET-GUARD-BLOCKED" in refused_env.stderr
    _git(clone, "restore", "--staged", ".env")

    (clone / "private").mkdir(exist_ok=True)
    (clone / "private" / "notes.md").write_text("draft\n", encoding="utf-8", newline="")
    _git(clone, "add", "-f", "private/notes.md")
    refused_private = _git(clone, "commit", "-m", "should be refused", check=False)
    assert refused_private.returncode != 0, "a private/ path was committed in a scratch clone"
    assert "PRIVATE-GUARD-BLOCKED" in refused_private.stderr


@pytest.mark.parametrize("guard", ["SECRET-GUARD-BLOCKED", "PRIVATE-GUARD-BLOCKED"])
def test_the_shipped_hook_carries_both_guards(guard: str) -> None:
    assert guard in (REPO_ROOT / "hooks" / "pre-commit").read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# The checklist cannot shrink silently
# --------------------------------------------------------------------------


def test_every_criterion_names_evidence_that_still_exists() -> None:
    """`tools/verify_phase1.py` maps each acceptance criterion to the test that
    establishes it. Rename or delete one of those tests and the criterion goes
    quietly unevidenced -- the report would still print, one line shorter.

    This is cheaper than running the suite twice in CI and catches the same
    defect: a checklist that shrinks without anyone deciding to shrink it.
    """
    from tools.verify_phase1 import CRITERIA

    # sys.executable, NOT "python". A bare "python" resolves through PATH to
    # whatever interpreter happens to be first, which on this machine is the
    # system one -- where the `harness` package is not installed, so collection
    # half-failed and the check reported every criterion as unevidenced. A
    # correct principle reaching for the wrong mechanism, which is W24's lesson
    # in a new place.
    collected = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "-p",
            "no:cacheprovider",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    known = {line.split("[")[0].strip() for line in collected.split("\n") if "::" in line}

    assert known, "collected no tests at all; the collection command has broken"

    missing: list[str] = []
    for criterion in CRITERIA:
        if not criterion.tests and not criterion.commands:
            missing.append(f"criterion with no evidence at all: {criterion.text[:60]}")
        for node in criterion.tests:
            if node not in known:
                missing.append(node)
    assert not missing, (
        "acceptance criteria naming evidence that does not exist:\n  " + "\n  ".join(missing)
    )


def _p1_criteria() -> list[str]:
    spec = (REPO_ROOT / "specs" / "voice-agent-eval-harness.md").read_text(encoding="utf-8")
    lines = [
        line.strip()
        for line in spec.splitlines()
        if re.match(r"^- \[[ x]\] \[P1[,\]]", line.strip())
    ]
    assert len(lines) >= 15, f"only {len(lines)} [P1] criteria parsed; the marker shape changed"
    return lines


def test_every_p1_criterion_in_the_specification_is_verified() -> None:
    """M1. This file already checked one direction -- every test node a criterion
    names still exists. The reverse was unchecked, so a criterion added to the
    specification and never added to `CRITERIA` was invisible, while the tool's
    closing line reported `len(CRITERIA)` as "all 21 phase-1 acceptance
    criteria" -- a count of the tool's own list, not the document's. Measured
    when this was written: 19 `[P1]` criteria against 21 entries.

    Each entry now carries a `spec_anchor`, a distinctive substring of the
    criterion it verifies. This asserts every `[P1]` line is claimed by one.
    """
    unclaimed = [
        line[:96]
        for line in _p1_criteria()
        if not any(c.spec_anchor and c.spec_anchor in line for c in CRITERIA)
    ]
    assert not unclaimed, (
        "[P1] acceptance criteria that no entry in tools/verify_phase1.py claims:\n  "
        + "\n  ".join(unclaimed)
    )


def test_every_anchor_still_points_into_the_specification() -> None:
    """The other half. An anchor that stopped matching would silently un-claim
    its criterion and let the test above pass while covering less."""
    spec = (REPO_ROOT / "specs" / "voice-agent-eval-harness.md").read_text(encoding="utf-8")
    orphaned = [c.spec_anchor for c in CRITERIA if c.spec_anchor and c.spec_anchor not in spec]
    assert not orphaned, "anchors no longer found in the specification:\n  " + "\n  ".join(orphaned)


def test_the_unanchored_entries_are_the_declared_extras() -> None:
    """`CRITERIA` may hold more than the specification does, and does: it splits
    the severity criterion across two entries and adds the interface scanner,
    which is not an acceptance criterion in the specification at all. The excess
    has to stay deliberate, or "all 21" is a number nobody can reconcile with
    the document it claims to verify."""
    unanchored = [c for c in CRITERIA if not c.spec_anchor]
    assert len(unanchored) == 1, (
        f"{len(unanchored)} entries carry no spec anchor, not 1:\n  "
        + "\n  ".join(c.text for c in unanchored)
    )
    # Identified by the command it runs rather than by its wording, which is
    # edited more often than its subject.
    ran = " ".join(" ".join(str(part) for part in cmd) for cmd in unanchored[0].commands)
    assert "check_spec_interface" in ran, unanchored[0].text
    assert len(CRITERIA) == len(_p1_criteria()) + 2, (
        f"CRITERIA has {len(CRITERIA)} entries against {len(_p1_criteria())} [P1] criteria; "
        "the two deliberate extras are the split severity criterion and the interface scanner"
    )


# --------------------------------------------------------------------------
# What the phase-1 verifier says when pytest exits non-zero
# --------------------------------------------------------------------------


def test_the_verifier_tells_a_failing_test_from_a_pytest_that_could_not_report() -> None:
    """The message is the whole product of that branch, and nothing exercised it.

    On 2026-09-07 the JUnit path became briefly unwritable. Every test passed,
    pytest exited 1 from its own reporting hook, and `tools/verify_phase1.py`
    printed *"a test that no criterion names still failed"*. There was no such
    test. A reader following that sentence looks for a failure that does not
    exist, which is worse than the tool saying nothing -- and it is the same
    defect this repository keeps finding elsewhere: **a message that claims more
    than the evidence under it supports.**

    Worse, the run that printed it had read the *previous* run's report, because
    the file was deleted only by being overwritten. `_run_suite` now unlinks it
    first, so a report this run did not write cannot be read as though it had.
    """
    from tools.verify_phase1 import diagnose_suite_exit

    # Node ids deliberately shaped so they are not test names. A fixture whose
    # ids looked like real ones would sit in a file the prose guard reads, and
    # be reported as citations of tests that do not exist -- and the comment
    # explaining that cannot quote them either, for the same reason. Seventh
    # instance in this session of a checker reading its own text.
    failing = diagnose_suite_exit(1, {"tests/mod.py::alpha_case": "fail", "b": "pass"})
    assert any("still failed" in line for line in failing), failing
    assert any("alpha_case" in line for line in failing), (
        "the failing node is not named, so the message sends a reader looking"
    )

    unwritten = diagnose_suite_exit(1, {})
    assert any("wrote no JUnit report" in line for line in unwritten), unwritten
    assert not any("still failed" in line for line in unwritten), (
        "a pytest that produced no report was reported as a failing test, which is the "
        "defect this check exists for"
    )

    clean = diagnose_suite_exit(1, {"a": "pass", "b": "skip"})
    assert any("did not come from a" in line for line in clean), clean
    assert not any("still failed" in line for line in clean), (
        "a report with no failing test was reported as a failing test"
    )


def test_the_verifier_deletes_its_report_before_running() -> None:
    """A stale report is undetectable when it agrees with the current one.

    The tool parses `build/phase1-junit.xml` after running pytest. If pytest
    fails to write it, the file from the previous run is still there and every
    per-criterion verdict above comes from it. That happened, and the verdicts
    were right, which is the worst version: nothing distinguished a current
    report from a stale one that agreed.
    """
    source = (REPO_ROOT / "tools" / "verify_phase1.py").read_text(encoding="utf-8")
    body = source[source.index("def _run_suite") : source.index("def diagnose_suite_exit")]
    assert "JUNIT.unlink(missing_ok=True)" in body, (
        "the phase-1 verifier no longer deletes its JUnit report before running, so a "
        "report it did not write can be parsed as though it had been"
    )
    assert body.index("JUNIT.unlink") < body.index("subprocess.run"), (
        "the report is deleted after the run rather than before it, which deletes the "
        "evidence instead of the staleness"
    )


#: Directories the source sweep does not walk: caches, the virtual environment,
#: git's own store. Same deny-list shape as the verifier's staleness scan, for
#: the same reason -- a directory nobody excluded costs a moment, a file nobody
#: included is a defect nothing looks at.
_UNSWEPT: Final[frozenset[str]] = frozenset(
    {
        ".git",
        ".venv",
        "build",
        "__pycache__",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        ".cj-store",
        "node_modules",
        "private",
    }
)

#: Everything below 0x20 except tab, newline and carriage return.
_CONTROL: Final[frozenset[str]] = frozenset(
    chr(code) for code in range(0x20) if chr(code) not in "\t\n\r"
) | {chr(0x7F)}


#: The suffixes the sweep reads. Named rather than inline, because the control
#: drives this same set: a filter matching nothing left the sweep green over a
#: planted byte, and the control that claimed to catch that was green with it.
_SWEPT: Final[frozenset[str]] = frozenset({".py", ".md", ".yaml", ".yml", ".toml", ".txt", ".cfg"})


def _control_character_offenders(root: Path) -> list[str]:
    """Every `path:line carries 0xNN` under `root`, as the sweep reports them.

    One function rather than two copies of the rule, so the control exercises
    this walk, this extension filter and this character set instead of
    recomputing the detection expression over a literal it wrote itself.
    """
    offenders: list[str] = []
    for parent, directories, files in os.walk(root):
        directories[:] = [d for d in directories if d not in _UNSWEPT]
        for name in files:
            path = Path(parent) / name
            if path.suffix not in _SWEPT:
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for number, line in enumerate(content.splitlines(), start=1):
                found = sorted({ord(ch) for ch in line if ch in _CONTROL})
                if found:
                    relative = path.relative_to(root).as_posix()
                    codes = ", ".join(f"0x{code:02X}" for code in found)
                    offenders.append(f"{relative}:{number} carries {codes}")
    return offenders


def test_no_source_file_carries_a_control_character() -> None:
    """A shell ate an escape, and the file kept the result.

    `src/harness/checks/values.py` line 70 read "W5 is the `` word boundary".
    The backticks were not empty: between them sat a literal 0x08 byte, written
    when `\\b` passed through a shell that interpreted it. The sentence named
    the thing it exists to name and rendered as nothing, in a docstring about
    the difference between two boundary rules -- and it survived ruff, mypy,
    the full suite and two audits, because none of them looks at bytes.

    That is the general shape: a mangled escape is invisible to every tool that
    reads the file as text, and it is trivially visible to one that reads it as
    bytes. This is that one.

    Tab, newline and carriage return are allowed. Everything else below 0x20,
    and DEL, is not.
    """
    offenders = _control_character_offenders(REPO_ROOT)
    assert not offenders, "control characters in source:\n  " + "\n  ".join(offenders)


def test_the_control_character_sweep_would_notice_one(tmp_path: Path) -> None:
    """The planted control, driven through the sweep rather than beside it.

    It asserted `_CONTROL` held the byte and then recomputed the detection
    expression on a literal of its own, which proves the character set and
    nothing about the walk or the extension filter -- two of the three things
    its own first sentence claimed. Measured when this was written: with
    `_CONTROL` emptied the sweep passed over a planted 0x08 byte and this
    control failed, correctly; with the suffix set matching nothing the sweep
    passed over the same byte and **this control passed with it**. It plants
    the byte in a file on disk now and requires the sweep to name it, so the
    walk and the filter are inside what is asserted.
    """
    assert "\x08" in _CONTROL, "the sweep no longer looks for the byte that prompted it"
    assert "\t" not in _CONTROL and "\n" not in _CONTROL

    (tmp_path / "clean.py").write_text('x = "the word boundary"\n', encoding="utf-8")
    (tmp_path / "planted.py").write_text('x = "the `\x08` word boundary"\n', encoding="utf-8")
    # A suffix the sweep does not read, carrying the same byte. This pins the
    # filter from both sides: widened to everything, this file starts being
    # reported; narrowed to nothing, the planted file above stops being.
    (tmp_path / "ignored.bin").write_text("the `\x08` boundary\n", encoding="utf-8")

    offenders = _control_character_offenders(tmp_path)
    assert offenders == ["planted.py:1 carries 0x08"], (
        f"the sweep did not name exactly the planted byte: {offenders}"
    )


def test_the_sibling_repository_is_found_in_either_layout(tmp_path: Path) -> None:
    """Criterion 21 knew one of the two layouts, and CI uses the other.

    Locally the two repositories sit side by side, so `../comparative-judgment`
    is right and every local run of this verifier passed. `actions/checkout`
    cannot place a repository above `GITHUB_WORKSPACE`, so CI checks the
    severity tool out **inside** this one -- and the first CI run ever to
    execute this verifier reported `21. [FAIL]`, the scanner having exited 2
    with `not a file`, comparing nothing, in the criterion whose whole subject
    is that two repositories agree.

    The workflow's own interface step already used the CI path. One convention,
    two copies, disagreeing, with nothing comparing them: D84's shape, reached
    this time because the check had never been run rather than because it had
    gone quiet.
    """
    from tools.verify_phase1 import SIBLING, sibling_root

    beside = tmp_path / "beside"
    (beside / "harness").mkdir(parents=True)
    (beside / SIBLING / "specs").mkdir(parents=True)
    assert sibling_root(beside / "harness") == beside / SIBLING

    inside = tmp_path / "inside"
    (inside / SIBLING / "specs").mkdir(parents=True)
    assert sibling_root(inside) == inside / SIBLING, (
        "the sibling checked out inside this repository is not found, which is exactly the "
        "layout every CI run uses"
    )

    # Both present: the local layout wins, so a developer's own clone is what a
    # local run compares against rather than a copy vendored inside.
    both = tmp_path / "both"
    (both / "harness" / SIBLING / "specs").mkdir(parents=True)
    (both / SIBLING / "specs").mkdir(parents=True)
    assert sibling_root(both / "harness") == both / SIBLING

    # Neither: fall back to the conventional place, so the failure names where a
    # reader should look. It must not resolve to something that exists -- a
    # comparison silently passing with one repository missing is the fail-open
    # this criterion exists to prevent.
    alone = tmp_path / "alone"
    (alone / "harness").mkdir(parents=True)
    assert sibling_root(alone / "harness") == alone / SIBLING
    assert not (alone / SIBLING).exists()


def test_the_interface_criterion_takes_its_path_from_the_resolver() -> None:
    """The wiring, not just the helper.

    `sibling_root` being right buys nothing while the criterion still carries
    the literal `../comparative-judgment` it was built with, which is what made
    the CI failure possible in a repository that has a resolver-shaped fix for
    everything else.
    """
    from tools.verify_phase1 import CRITERIA, _sibling_specs

    matching = [
        criterion
        for criterion in CRITERIA
        if any(any("check_spec_interface" in part for part in cmd) for cmd in criterion.commands)
    ]
    assert len(matching) == 1, (
        f"{len(matching)} criteria run the interface scanner; this test names one"
    )
    assert matching[0].commands[0][-1] == _sibling_specs(), (
        "the interface criterion carries a path the resolver did not produce, so the two "
        "layouts are back to being one hardcoded layout"
    )
