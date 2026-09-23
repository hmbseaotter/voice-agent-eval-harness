#!/usr/bin/env python3
"""Build the published snapshot of this repository, and refuse to build a dirty one.

    uv run python tools/make_public_snapshot.py --out <directory>

WHY A SNAPSHOT
--------------
The public repository carries this project's files and not its history. Early
session documents named a directory path from the machine the work was done on,
carrying context nothing here needs, and that path is in commits that cannot be
rewritten without invalidating what other repositories have already cited: a
frozen-rubric tag, a constant compared against it by test, the held-out
repository's label commits citing the freeze commit by SHA, and several dozen
documents that cite commits as evidence. So the publication is a snapshot, the
working history stays private, and `SNAPSHOT.md` in the built tree says so to
whoever arrives there.

WHAT IT REFUSES
---------------
A snapshot is published once and cached by strangers, so this checks the export
before it becomes a repository. It refuses an absolute filesystem path it has
not seen before -- the class the original defect belonged to -- and the check is
**a pattern rather than a word list**, because a list of things to keep out of a
public tree, kept inside that tree, publishes them.

`ALLOWED_PATHS` holds the five files that carry a match deliberately: a redacted
path inside a quoted terminal line, an invented installation path a test asserts
on, one false positive, the path `tests/test_public_snapshot.py` plants to prove
this scan can match at all, and this file, whose pattern is written out in its
own source and therefore matches itself. A new match is a person's decision, not
this script's: it prints what it found and exits 2.

WHAT IT CHANGES, AND WHY EACH ONE
---------------------------------
Two files differ in the published tree, and they are the whole difference:

1. `SNAPSHOT.md` is added, saying what is published and what is not.
2. `README.md` gains a row licensing that file, because a `[P6]` criterion asks
   the README to name a license for every top-level path.

**Nothing else is rewritten, and that is D211.** Until then this tool re-pointed
`RUBRIC_FROZEN_V1` at the snapshot's own first commit, so that two git-dependent
tests would pass in a tree whose log does not contain the freeze -- and the 2026-09-22
sweep found what that cost. `harness agreement` and `harness coverage` refuse held-out
labels whose traces name any commit but that pin, so in the published tree they refused
the *real* labels, and the recomputation the README promises could be made only from
the private repository. A tag had to be invented for the same reason, its name could
not be `rubric-frozen-v1` without making the freeze look later than the seal that
cites it, and pushing that tag after the branch turned the public build red five times
running.

So the pin now names the freeze everywhere, and the two tests that need the freeze
*in the log* skip where it is absent. Nothing is lost: since D210 `freeze-proof/`
carries the same property without git, and `tests/test_freeze_proof.py` asserts it --
the published tree gains a check rather than losing one, because comparing HEAD
against a pin that named the snapshot's own commit was a tautology.

Every document that cites a commit still means the private history's commit, and
`SNAPSHOT.md` says so.

Exit 0 when the snapshot is built, 2 when it refuses.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tarfile
from io import BytesIO
from pathlib import Path
from typing import Final

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]

#: Read here to find the freeze commit, which `SNAPSHOT.md` names. The snapshot
#: carries no tag of its own and rewrites no constant (D211).
SOURCE_TAG: Final[str] = "rubric-frozen-v1"

#: An absolute filesystem path, which is what the private context this snapshot
#: exists to leave behind was written as. Both separators, and the two home
#: directories a POSIX machine would name.
_ABSOLUTE_PATH: Final[re.Pattern[str]] = re.compile(r"[A-Z]:[\\/][A-Za-z_.…]|/Users/|/home/")

#: Matches this project legitimately carries, each read and kept deliberately:
#: a path redacted inside a quoted terminal line, an installation path invented
#: for a test, a line where the pattern matches no path at all, the path a test
#: plants to hold this scan to matching one, and this file: the pattern above is
#: written out here, so it finds itself. Exempting the scanner's own source means
#: a path written into it would pass, which is why it is one short file and not a
#: package. An entry whose reason has gone is dropped by
#: `test_every_allowed_path_exists_and_still_carries_a_match`.
ALLOWED_PATHS: Final[frozenset[str]] = frozenset(
    {
        "sessions/AUDIT-2026-09-12-phase-4.md",
        "tests/test_cli.py",
        "tests/test_public_snapshot.py",
        "tests/test_transport.py",
        "tools/make_public_snapshot.py",
    }
)

SNAPSHOT_NOTE: Final[str] = """# About this repository's history

This repository is a **snapshot**. Its first commit carries the project as it stood on the day it
was built; the working history that produced it — around three hundred commits, each with the
message this project's rules require — is kept in a private repository and is not published here.

**Why.** Early session documents named a directory path from the machine the work was done on, and
that path carried private context nothing in this project needs. Removing it from the working tree
is one commit; removing it from history means rewriting every commit after it, and this project's
evidence is pinned to commit identifiers: a frozen-rubric tag, a pinned constant compared against
it by test, a companion repository whose label commits cite the freeze commit by SHA, and several
dozen documents that cite commits as evidence. Rewriting would have invalidated citations that
another repository has already made and cannot re-make. A snapshot leaves all of that intact where
it is true, and publishes the work without the private detail.

**What that means for a reader.**

- **The narrative is here, in more detail than a log.** `specs/voice-agent-eval-harness.md` carries
  the changelog, and `specs/voice-agent-eval-harness.decisions.md` every fork taken, why, and what
  enforces it — over two hundred entries. `sessions/` holds the audits and the sweeps, each with a
  status banner a later session maintains, the handovers with a status line, and the briefs sessions
  were given, marked **SPENT** once the handover or report they name exists.
- **Commit identifiers cited in those documents refer to the private history.** A SHA in an audit
  banner or a decision entry is a real commit of this project; it is not resolvable in this
  repository's own log. **One citation is not left in that state.** The held-out repository's seal
  commit cites the freeze commit by SHA, which is how it proves the rubric was frozen before its
  labels existed, and `freeze-proof/` publishes that commit's own bytes together with its tag, the
  two trees reaching the frozen `rubric.yaml` and prompt template, and under `objects/` the whole
  frozen `src` subtree, so the frozen code itself can be run over them (D209, D210). It is
  recomputed rather than believed: `uv run python -m tools.verify_freeze_proof`, no history, no
  network, no clone.
- **The freeze pin names the freeze here, exactly as it does in the working repository.**
  `RUBRIC_FROZEN_V1` is {freeze}, so `harness agreement` and `harness coverage` accept the real
  held-out labels in this tree — which they did not until 2026-09-22, when a sweep found that the
  pin had been re-pointed at this snapshot's own first commit to keep two tests green (D211).
  Those two tests need the freeze commit **in the log**, which no snapshot has, so here they skip
  and say why; the property they check is carried without git by
  `tests/test_freeze_proof.py`, against the published objects. This repository carries no tag,
  either: `rubric-frozen-v1` lives in the working history, and its object is in `freeze-proof/`.
- **Everything else runs as it is documented.** The suite, the phase verifiers, the control gate and
  the report snapshot need no credential and no network: `uv run pytest`, then the commands in the
  README's *Running it* section.

Built by `tools/make_public_snapshot.py` from the working repository at {source}.
"""

README_ROW: Final[str] = (
    "| `SNAPSHOT.md` | what this published repository is, and what it leaves in the private "
    "working history it was taken from | CC BY 4.0 |\n"
)
README_ANCHOR: Final[str] = "| `.env.example` |"


def run(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(
        args, cwd=cwd or REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def export(ref: str, out: Path) -> None:
    """Every tracked file at `ref`, and nothing else: no history, no ignored file."""
    archive = subprocess.run(
        ["git", "archive", ref], cwd=REPO_ROOT, capture_output=True, check=True
    ).stdout
    with tarfile.open(fileobj=BytesIO(archive)) as tar:
        tar.extractall(out, filter="data")


def absolute_paths(out: Path) -> list[str]:
    """Files in the export carrying an absolute path this script has not been told about."""
    found: list[str] = []
    for path in sorted(out.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(out).as_posix()
        if relative in ALLOWED_PATHS:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if _ABSOLUTE_PATH.search(text):
            found.append(relative)
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="make_public_snapshot", description=__doc__)
    parser.add_argument("--out", required=True, help="an empty or absent directory to build in")
    parser.add_argument("--ref", default="HEAD", help="what to publish; HEAD by default")
    args = parser.parse_args(argv)

    out = Path(args.out).resolve()
    if out.exists() and any(out.iterdir()):
        print(f"snapshot refused: {out} exists and is not empty", file=sys.stderr)
        return 2
    source = run("git", "rev-parse", "--short", args.ref)
    freeze = run("git", "rev-list", "-n", "1", SOURCE_TAG)

    out.mkdir(parents=True, exist_ok=True)
    export(args.ref, out)

    dirty = absolute_paths(out)
    if dirty:
        print(
            "snapshot refused: these files carry an absolute filesystem path, which is the class "
            "of detail this snapshot exists to leave behind. Read each one; if it is legitimate, "
            "add it to ALLOWED_PATHS with the reason:\n  " + "\n  ".join(dirty),
            file=sys.stderr,
        )
        return 2

    readme = out / "README.md"
    contents = readme.read_text(encoding="utf-8")
    if README_ANCHOR not in contents:
        print("snapshot refused: the README's license table has moved", file=sys.stderr)
        return 2
    readme.write_text(
        contents.replace(README_ANCHOR, README_ROW + README_ANCHOR), encoding="utf-8", newline="\n"
    )

    (out / "SNAPSHOT.md").write_text(
        SNAPSHOT_NOTE.format(freeze=freeze[:7], source=source),
        encoding="utf-8",
        newline="\n",
    )

    run("git", "init", "-q", "-b", "main", cwd=out)
    run("git", "add", "-A", cwd=out)
    run(
        "git",
        "commit",
        "-q",
        "-m",
        "voice-agent evaluation harness: the project, without its private history\n\n"
        "A snapshot of the working repository. SNAPSHOT.md says what is published\n"
        "here and what is not, and why the history is not.",
        cwd=out,
    )
    snapshot_commit = run("git", "rev-parse", "HEAD", cwd=out)

    print(f"snapshot of {source} built in {out}")
    print(f"  one commit, {snapshot_commit[:7]}, and no tag: nothing here is re-pointed (D211)")
    print("  push it with:")
    print(f"    git -C {out} remote add origin <the public repository>")
    print(f"    git -C {out} push --force -u origin main")
    print("  --force because every build is a history of its own; one ref, so the")
    print("  workflow the push starts sees the tree it will be judged on")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
