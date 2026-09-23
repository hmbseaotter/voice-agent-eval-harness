"""Phase 6's acceptance criteria that belong to no one deliverable's module.

The second adapter, the log inspector and per-instance severity each have a
module of their own. What is here is the docs-routing criterion phase 1 deferred
to this phase, which no test had asserted until phase 6's contract reading found
it so (D201): *the README states which license covers which tree, and links the
severity tool*.
"""

from __future__ import annotations

import fnmatch
import re
import sys
from pathlib import Path
from typing import Final

import pytest

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
README: Final[Path] = REPO_ROOT / "README.md"

LICENSES: Final[frozenset[str]] = frozenset({"CC BY 4.0", "Apache-2.0"})
SEVERITY_TOOL: Final[str] = "https://github.com/hmbseaotter/comparative-judgment"

#: Paths the README declares under neither license, each with the words that
#: declare it. A decision the owner has not taken is stated rather than implied.
UNDER_NEITHER: Final[dict[str, str]] = {
    "sessions": "The handovers and audit reports in `sessions/` are under neither",
}

_ROW: Final[re.Pattern[str]] = re.compile(r"^\|(?P<paths>[^|]*)\|.*\|(?P<license>[^|]*)\|\s*$")
_PATH: Final[re.Pattern[str]] = re.compile(r"`([^`]+)`")


def _ignored_patterns() -> list[str]:
    patterns = []
    for line in (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith(("#", "!")):
            patterns.append(stripped.strip("/"))
    return patterns


def _another_repositorys_checkout(entry: Path) -> bool:
    """A directory carrying its own `.git` is another repository's working copy.

    CI checks `comparative-judgment` out **inside** this root, for the interface
    scanner, so on every run the root holds a tree this repository does not own and
    cannot license. The check below read it as an unlicensed path and turned `main`
    red with a true claim about the wrong population (D207). A sibling checked out
    under any other name would have done the same, which is why this reads for the
    `.git` rather than for the name.
    """
    return entry.is_dir() and (entry / ".git").exists()


def _top_level_paths() -> list[str]:
    """What sits in the repository root, is not ignored, and belongs to this
    repository, without asking git, so this runs in the control gate's copy of the
    tree, which has no `.git`."""
    patterns = _ignored_patterns()
    return sorted(
        entry.name
        for entry in REPO_ROOT.iterdir()
        if entry.name != ".git"
        and not _another_repositorys_checkout(entry)
        and not any(fnmatch.fnmatch(entry.name, pattern) for pattern in patterns)
    )


def _licensed_by_the_readme(text: str) -> dict[str, str]:
    """Top-level name to the license its table row states."""
    section = text[text.index("## What is here") : text.index("## Running it")]
    stated: dict[str, str] = {}
    for line in section.splitlines():
        row = _ROW.match(line)
        if row is None:
            continue
        for path in _PATH.findall(row.group("paths")):
            stated[path.strip("/").split("/")[0]] = row.group("license").strip()
    return stated


def _unlicensed(paths: list[str], text: str) -> list[str]:
    """Top-level paths the README neither licenses nor declares under neither."""
    stated = _licensed_by_the_readme(text)
    problems: list[str] = []
    for name in paths:
        if name in UNDER_NEITHER:
            if UNDER_NEITHER[name] not in text:
                problems.append(f"{name} is no longer declared under neither license")
        elif name not in stated:
            problems.append(f"{name} is named in no row of the README's license table")
        elif name.startswith("LICENSE"):
            continue
        elif stated[name] not in LICENSES:
            problems.append(f"{name} is given {stated[name]!r}, which is neither license")
    return problems


def test_the_readme_names_a_license_for_every_top_level_path() -> None:
    paths = _top_level_paths()
    assert len(paths) >= 20, f"only {len(paths)} top-level paths were read: {paths}"
    assert "src" in paths and "corpus" in paths
    assert not any(name in paths for name in ("build", "private", ".venv")), (
        "an ignored path was read as tracked, so the ignore rules are not being applied"
    )
    problems = _unlicensed(paths, README.read_text(encoding="utf-8"))
    assert not problems, "\n".join(problems)


def test_the_license_check_would_notice_a_path_the_readme_does_not_name() -> None:
    text = README.read_text(encoding="utf-8")
    assert _unlicensed(["src", "a-new-tree"], text) == [
        "a-new-tree is named in no row of the README's license table"
    ]
    relicensed = text.replace("| Apache-2.0 |", "| MIT |", 1)
    assert any(
        "neither license" in problem for problem in _unlicensed(_top_level_paths(), relicensed)
    )
    undeclared = text.replace(UNDER_NEITHER["sessions"], "The handovers are somewhere")
    assert any("sessions" in problem for problem in _unlicensed(["sessions"], undeclared))


def test_the_readme_links_the_severity_tool() -> None:
    assert SEVERITY_TOOL in README.read_text(encoding="utf-8")


def test_the_license_check_reads_this_repositorys_trees_and_not_a_sibling_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Another repository's working copy inside this root is not a tree this one
    licenses (D207).

    CI checks `comparative-judgment` out at `comparative-judgment/` so the interface
    scanner can read its specification, and the check above read that directory as an
    unlicensed top-level path: green on a machine whose sibling sits elsewhere, red in
    CI, on the first run after the criterion was asserted. It reads for the `.git` a
    checkout carries rather than for the name, so a sibling checked out under any name
    is skipped and an ordinary directory is not.
    """
    root = tmp_path / "root"
    (root / "src").mkdir(parents=True)
    (root / ".gitignore").write_text("build/\n", encoding="utf-8", newline="\n")
    sibling = root / "comparative-judgment"
    (sibling / ".git").mkdir(parents=True)
    (root / "corpus").mkdir()
    (root / "build").mkdir()
    # Patched on the running module rather than on a fresh import of it: pytest
    # imports a test module under its own name, so a second import is a second
    # module object and the patch would land on the copy nothing calls.
    monkeypatch.setattr(sys.modules[__name__], "REPO_ROOT", root)

    paths = _top_level_paths()
    assert "comparative-judgment" not in paths, "a sibling checkout is read as a tree of this one"
    assert "build" not in paths, "an ignored path is read as tracked"
    assert set(paths) == {".gitignore", "corpus", "src"}, paths

    ordinary = root / "docs"
    ordinary.mkdir()
    assert "docs" in _top_level_paths(), "a directory of this repository is skipped"
