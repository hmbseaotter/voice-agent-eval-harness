"""Re-derive every `connected` verdict in the control register, by running it.

A control is a test planted to prove a fix is load-bearing: restore the defect it
names and the control fails. Whether that is *true* of a given control is not
visible in its name, its docstring, or the fact that it passes -- three controls
in this tree were confident, green, and measuring nothing. It is visible in
exactly one thing: does the control fail when the defect is put back?

This tool asks that question for every entry in `control-mutations.yaml`. It
copies the repository, applies the mutation to the copy, and requires the named
control to FAIL there and to PASS without it. A control that cannot be driven
both ways has been proven against nothing, and is reported as such.

**Why a copy on disk, and never `sys.modules`.** In-memory module injection does
nothing here: `harness/checks/__init__.py` binds the check function objects at
import time, so a swapped module leaves `build_registry()` returning the
originals. It reports a clean null from an instrument wired to nothing.

**Why `patch`/`str.replace` and never `git apply`.** `git apply` exits 0 while
skipping every hunk when it resolves paths against a repository other than the
one the patch came from. The first version of this sweep ran that way, mutated
nothing, and would have reported that no control notices any defect.

Exit codes follow D114's shape:
    0  every control was driven red and restored
    1  at least one control stayed green with its defect restored -- a finding
    2  the run could not be made: a missing file, a `find` that matches other
       than exactly once, a copy that did not differ
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import yaml

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
MUTATIONS: Final[Path] = REPO_ROOT / "control-mutations.yaml"

#: Copied so the mutation lands somewhere nothing else reads. `.venv` and `.git`
#: are the expensive ones and neither is read by a test. `__pycache__` is here
#: for correctness rather than speed: a stale `.pyc` copied in beside its source
#: can be reused instead of the mutated file, and then the mutation is invisible.
#:
#: `.env` is here for a third reason: it is the one file in this tree that may
#: hold a live credential, and this tool ran fifty times a sweep making a second
#: copy of it in a temporary directory. Harmless in CI, where no `.env` exists,
#: and a needless second copy on the machine that has one. Nothing in the copy
#: reads it -- every test that needs a credential writes its own.
_SKIP: Final[frozenset[str]] = frozenset(
    {
        ".env",
        ".venv",
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
        "build",
        "private",
        ".cj-store",
    }
)


@dataclass(frozen=True)
class Mutation:
    """One defect, restorable into a copy of the tree."""

    control: str
    file: str
    defect: str
    find: str
    replace: str
    #: Where the control itself lives, when that is not `file`. A mutation in
    #: `src/` is the defect; the control that must notice it is in `tests/`.
    control_file: str | None = None


class Unrunnable(Exception):
    """The sweep could not be made. Distinct from a control that stayed green:
    one is a finding about a control and the other is a finding about this tool,
    and reporting the second as the first is the fail-open D114 is named for."""


def load_mutations(path: Path) -> list[Mutation]:
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    entries = document.get("controls") or []
    if not entries:
        raise Unrunnable(f"{path.name} declares no controls, so this tool would verify nothing")
    return [
        Mutation(
            control=body["control"],
            file=body["file"],
            defect=" ".join(body["defect"].split()),
            find=body["find"],
            replace=body["replace"],
            control_file=body.get("control_file"),
        )
        for body in entries
    ]


def copy_tree(destination: Path) -> None:
    shutil.copytree(
        REPO_ROOT,
        destination,
        ignore=lambda _directory, names: [name for name in names if name in _SKIP],
        dirs_exist_ok=True,
    )


def apply(mutation: Mutation, root: Path) -> None:
    """Restore the defect into the copy, refusing anything ambiguous.

    `find` names a whole line, not a substring. Substring matching made
    `    return problems` match `    return problems, compared` one function
    over, and an entry that lands in two places is not the defect it names.

    A `find` matching twice is not the defect the entry names, and one matching
    nowhere is a mutation that silently does nothing -- which is the failure this
    tool exists to detect, so it must not be the way this tool fails.
    """
    target = root / mutation.file
    if not target.is_file():
        raise Unrunnable(f"{mutation.control}: {mutation.file} is not a file in the copy")
    lines = target.read_text(encoding="utf-8").splitlines(keepends=True)
    stripped = [line.rstrip("\r\n") for line in lines]
    hits = [index for index, line in enumerate(stripped) if line == mutation.find]
    if len(hits) != 1:
        raise Unrunnable(
            f"{mutation.control}: `find` matches {len(hits)} lines in {mutation.file}; "
            "an entry names one defect in one place"
        )
    ending = lines[hits[0]][len(stripped[hits[0]]) :]
    lines[hits[0]] = mutation.replace + ending
    # `newline=""` writes each line's own ending back (the phase-5 audit's P5-14).
    # Without it Python translates every "\n" into this platform's separator, so on
    # Windows the gate rewrote every mutated file as CRLF -- against the rule this
    # project adopted with its `.gitattributes`, and a difference a control comparing
    # bytes would read as its own defect.
    target.write_text("".join(lines), encoding="utf-8", newline="")


def run_control(control: str, root: Path, file: str, control_file: str | None) -> bool:
    """True when the control passes in `root`.

    Addressed as `<file>::<control>` when that file defines it, because
    `test_every_traced_finding_is_on_a_call_the_entry_fires_on` exists in two
    modules and `-k` would run both -- so a mutation in one would be reported
    as driving whichever failed, which is not the claim the entry makes.

    **`PYTHONPATH` points at the copy's `src`, and without it this tool could
    not verify a single control whose defect lives there.** `harness` is an
    editable install: a `.pth` file appends the real repository's `src` to
    `sys.path`, so a copy of the tree imports the ORIGINAL modules and a
    mutation in `<copy>/src` is invisible. Measured when this was written: a
    bare `raise` planted in the copy's `checks/claims.py` changed nothing, and
    the control passed. `PYTHONPATH` entries precede `.pth` ones, so naming the
    copy first is what makes the copy the thing under test.
    """
    module = file if file.startswith("tests/") else control_file
    selector = [f"{module}::{control}"] if module else ["-k", control]
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(root / "src")
    # Without this the gate reports controls as disconnected that are not.
    # CPython validates a cached `.pyc` on the source's (size, mtime-in-seconds).
    # The unmutated run writes a cache; the mutated run then reuses it whenever
    # the replacement is the SAME LENGTH as the line it replaced and both runs
    # land in the same second -- and a mutation that swaps `==` for `>=`, or one
    # 30-character regex for another, is exactly that. Measured when this was
    # written: CI reported green, with their defects restored, exactly the entries
    # whose replacement preserved the file size. Locally the same entries went
    # red, because each run took long enough to cross a second boundary. A gate
    # whose verdict depends on how fast the machine is, is not a gate.
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            *selector,
            "--no-header",
            "-p",
            "no:cacheprovider",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        env=environment,
    )
    if _collected_nothing_or_errored(completed.stdout):
        tail = completed.stdout[-800:]
        raise Unrunnable(f"{control}: pytest collected nothing or errored in the copy:\n{tail}")
    if _was_skipped(completed.stdout):
        tail = completed.stdout[-400:]
        raise Unrunnable(
            f"{control}: the control was SKIPPED in the copy, so it reported nothing about "
            f"its defect either way:\n{tail}"
        )
    return completed.returncode == 0


def _was_skipped(output: str) -> bool:
    """Whether the control did not run, as distinct from running and passing.

    **pytest exits 0 for a skip**, so `returncode == 0` reads a control that
    never executed as one that executed and passed. The sweep then asks the
    question it exists to ask -- did this control notice its defect? -- of
    something that answered nothing, and reports *stayed green with the defect
    restored*, which is its phrase for an instrument measuring nothing.

    It was measuring nothing, but not for the reason that verdict means. Three
    controls over `src/harness/report.py` skip while `snapshots/report.md` is
    absent, and on the sweep that first ran them the snapshot had not been
    generated. They were reported as blind beside one control that genuinely
    was, and those are not the same finding.

    **A skip is unrunnable, not green** -- the distinction `Unrunnable` exists
    for, one line below the predicate that already keeps a red that is not a
    finding apart from one that is.

    Conservative about mixed output: only a run reporting skips and neither a
    pass nor a failure measured nothing. A selector matching several tests where
    some ran is a different problem and not this one.
    """
    if not re.search(r"\b\d+ skipped\b", output):
        return False
    return not re.search(r"\b\d+ (?:passed|failed)\b", output)


def _collected_nothing_or_errored(output: str) -> bool:
    """Whether pytest failed to RUN, as distinct from running and reporting red.

    **Matched on pytest's own markers rather than on the word.** This tested
    `"ERROR" in output`, which is a substring of anything a failing assertion
    prints -- and one of this project's own status values is `Status.ERRORED`.
    So a control that drove red correctly, over a result whose status was
    `errored`, was reported as unrunnable and stopped the sweep at entry 51.

    That is the failure this tool exists to prevent, arriving in the tool: a
    red that is not a finding, indistinguishable from one that is. `Unrunnable`
    is the class whose docstring says exactly that, and it was raised for a
    control that was working.
    """
    if "no tests ran" in output:
        return True
    if "INTERNALERROR" in output or "during collection" in output:
        return True
    # pytest's short summary writes `ERROR <nodeid>` at column zero; a failing
    # assertion's own output is indented under its traceback.
    return bool(re.search(r"^ERROR\b", output, re.MULTILINE))


def main() -> int:
    try:
        mutations = load_mutations(MUTATIONS)
    except (OSError, KeyError, Unrunnable) as error:
        print(f"cannot read {MUTATIONS.name}: {error}")
        return 2

    print(f"Re-deriving {len(mutations)} control verdicts by restoring the defect each one names.")
    print("A control that stays green with its defect restored is measuring nothing.\n")

    findings: list[str] = []
    with tempfile.TemporaryDirectory(prefix="verify-controls-") as scratch:
        root = Path(scratch) / "tree"
        try:
            copy_tree(root)
        except OSError as error:
            print(f"could not copy the repository: {error}")
            return 2

        for number, mutation in enumerate(mutations, start=1):
            target = root / mutation.file
            pristine = target.read_text(encoding="utf-8")
            try:
                if not run_control(mutation.control, root, mutation.file, mutation.control_file):
                    findings.append(f"{mutation.control} fails before its defect is restored")
                    print(f"{number:3}. [FAIL] {mutation.control}\n       red without the mutation")
                    continue

                apply(mutation, root)
                if target.read_text(encoding="utf-8") == pristine:
                    raise Unrunnable(f"{mutation.control}: the copy is unchanged")

                still_green = run_control(
                    mutation.control, root, mutation.file, mutation.control_file
                )
            except Unrunnable as error:
                print(f"{number:3}. [STOP] {error}")
                return 2
            finally:
                target.write_text(pristine, encoding="utf-8", newline="")

            if still_green:
                findings.append(mutation.control)
                print(f"{number:3}. [FAIL] {mutation.control}  ({mutation.file})")
                print(f"       stayed green with the defect restored: {mutation.defect}")
            else:
                print(f"{number:3}. [ OK ] {mutation.control}  ({mutation.file})")
                print(f"       red when: {mutation.defect}")

    print("\n" + "=" * 78)
    if findings:
        print(f"{len(findings)} control(s) did not notice their own defect:")
        for finding in findings:
            print(f"  - {finding}")
        print("A null result from an instrument that is not connected is a finding about")
        print("the instrument. Repair the control, or record why it cannot be.")
        return 1
    print(f"All {len(mutations)} controls were driven red by their own defect and restored.")
    print("Every `connected` verdict in CONTROL-REGISTER.md that this file covers is re-derived,")
    print("not asserted. The register's `unaudited` rows are the ones with no entry here.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
