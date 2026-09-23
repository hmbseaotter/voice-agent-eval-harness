"""Drive the snapshot builder's refusal, and keep its allowance honest.

WHY THIS EXISTS
---------------
`tools/make_public_snapshot.py` is the last thing between the working tree and
a public repository, and what it looks for -- an absolute filesystem path, the
class of detail D208 exists to leave behind -- is a pattern. A pattern that
cannot match reads exactly like a clean tree: the tool prints nothing, exits 0,
and the snapshot is published. So the first test here plants a path and proves
the scan finds it, before any run of the tool is believed.

The second test reads the other direction. `ALLOWED_PATHS` names the files
that carry a match deliberately, and an allowance outlives the line it was
written for: the file is edited, the path goes, and the entry stays, silently
exempting whatever that file becomes. Each entry is held to still matching.

Neither test calls the tool's own `absolute_paths` over this repository. That
function walks a directory and is given an export, where only tracked files
exist; pointed at a checkout it would read `.git`, the virtual environment and
every build directory. The tracked-file test below walks what `git` lists and
applies the same pattern, which is the same question asked where it is cheap.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from tools.make_public_snapshot import _ABSOLUTE_PATH, ALLOWED_PATHS, absolute_paths

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_the_scan_finds_a_planted_absolute_path(tmp_path: Path) -> None:
    """Three shapes, because a pattern is believed only where it has matched."""
    (tmp_path / "windows.md").write_text(
        r"the session was told to read C:\Users\someone\Projects\thing",
        encoding="utf-8",
        newline="\n",
    )
    (tmp_path / "posix.md").write_text(
        "and then /home/someone/thing beside /Users/someone/thing",
        encoding="utf-8",
        newline="\n",
    )
    (tmp_path / "clean.md").write_text(
        "a relative path, ../voice-agent-eval-harness-holdout, names no machine",
        encoding="utf-8",
        newline="\n",
    )

    assert absolute_paths(tmp_path) == ["posix.md", "windows.md"]


def test_an_allowed_file_is_skipped_rather_than_read(tmp_path: Path) -> None:
    """The allowance is by path, so a match inside an allowed file is not found."""
    allowed = sorted(ALLOWED_PATHS)[0]
    planted = tmp_path / allowed
    planted.parent.mkdir(parents=True, exist_ok=True)
    planted.write_text(r"C:\Users\someone\thing", encoding="utf-8", newline="\n")

    assert absolute_paths(tmp_path) == []


def test_every_allowed_path_exists_and_still_carries_a_match() -> None:
    """An exemption for a line that has gone exempts whatever the file becomes."""
    stale: list[str] = []
    for relative in sorted(ALLOWED_PATHS):
        path = REPO_ROOT / relative
        if not path.exists():
            stale.append(f"{relative}: no such file")
        elif not _ABSOLUTE_PATH.search(path.read_text(encoding="utf-8")):
            stale.append(f"{relative}: carries no absolute path any more")
    assert not stale, (
        "ALLOWED_PATHS in tools/make_public_snapshot.py exempts a file from the "
        "publication scan for a reason that no longer holds; drop the entry: " + "; ".join(stale)
    )


def test_no_tracked_file_carries_an_absolute_path_outside_the_allowance() -> None:
    """What the tool refuses at publication, the suite refuses on the day it arrives."""
    listed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    tracked = [name for name in listed.split("\0") if name]
    assert len(tracked) > 100, f"git listed {len(tracked)} tracked files, which is too few to trust"

    found: list[str] = []
    for relative in tracked:
        if relative in ALLOWED_PATHS:
            continue
        path = REPO_ROOT / relative
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if _ABSOLUTE_PATH.search(text):
            found.append(relative)

    assert not found, (
        "a tracked file carries an absolute filesystem path, which is the class of detail the "
        "published snapshot exists to leave behind (D208). Read each one; if it is legitimate, "
        "add it to ALLOWED_PATHS in tools/make_public_snapshot.py with the reason: "
        + ", ".join(found)
    )
