#!/usr/bin/env python3
"""Verify the published freeze proof: four git objects, recomputed from their bytes.

    uv run python -m tools.verify_freeze_proof

WHAT THE PROOF IS FOR
---------------------
The held-out repository secures its central claim -- that the rubric was not
designed against its labels -- by its seal commit citing the freeze commit's SHA.
That argument works because you cannot cite the hash of a commit that does not
yet exist, and it needs no date: author and committer dates are self-asserted,
a hash is not.

Publishing this project as a snapshot (D208) left that citation unresolvable in
the public repository, which turned a property that could be **recomputed** into
one merely **asserted in prose**. The proof restores the recomputation without
publishing any history: a commit object references its tree and its parents by
hash rather than by content, so the four objects in `freeze-proof/` can be
published on their own, and the ~290 commits behind the freeze stay private.

WHAT THIS CHECKS
----------------
Every link in the chain, each one a hash recomputation and none of them a date:

  the tag object names `rubric-frozen-v1` and points at the freeze commit
    -> the commit names the root tree
       -> the root tree names `rubric.yaml` as a blob, and `prompts` as a tree
          -> the prompts tree names the judge template as a blob
             -> both blobs are the files this repository carries at HEAD

It needs no `.git`, no network and no clone: every id is recomputed with
`sha1("<type> <size>\\0" + bytes)`, which is git's own object rule. That is what
lets the control gate drive it, since the gate runs in a copy with no history.

THE INPUTS ARE NOT THE COMPUTATION (D210)
-----------------------------------------
The chain above settles which rubric and which template were frozen. It does not
settle **what the frozen code computed over them**, and the held-out gate asserts
something stronger than the bytes: it derives the prompt-template hash by running
the frozen harness's own `load_template`, in a separate interpreter over the
frozen `src`, and refuses a hash that came from any harness but that one.

Nothing in the four objects above lets that run, and the frozen `src` tree is not
the published one -- the snapshot rewrites two constants in `agreement.py`, and
the code has moved since 2026-09-13 regardless. So the whole frozen `src` subtree
is published object by object under `objects/`, and this tool reconstructs it and
runs that probe: `reconstruct()` walks the trees, writing each blob to its frozen
path and verifying every object against its own name, and `probe()` runs the
frozen code and requires `harness.__file__` to resolve inside the reconstruction.

Computing with HEAD's code instead would have been cheaper and wrong: if
`load_template`'s hashing ever moves, HEAD yields a hash the frozen code never
computed, and the gate fails a run that was honest.

Exit 0 when every link holds, 1 when one does not, naming each.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Final

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]

#: The freeze, as the held-out repository's `labels/MANIFEST` cites it.
FREEZE_COMMIT: Final[str] = "6d3a7101aaa1f15b440de43fe5142434f69c9dc9"
FREEZE_TAG_OBJECT: Final[str] = "ae987da81a6c51725ff3a4a32267913926e2c74a"
FREEZE_TREE: Final[str] = "11319cedc6fdf66dc9f53dac12453ffb876861e9"
FREEZE_PROMPTS_TREE: Final[str] = "825ef49b436807f8e28a65f55130f6e03fe80d50"

#: The name the annotated tag object carries, which is the name the held-out
#: repository's gate reads. The snapshot tags its own pin under another name, so
#: that a published tag never claims to be this one (D209).
TAG_NAME: Final[str] = "rubric-frozen-v1"

#: The frozen `src` tree, which the root tree names, published object by object so
#: the frozen harness can be run without any history (D210).
FROZEN_SRC_TREE: Final[str] = "b4415262dd4c4e6547fc64408a18cb8a96069597"
OBJECTS_DIR: Final[str] = "objects"

#: What the frozen code computes for the frozen template. Published, so the number
#: is pinned rather than recomputed into agreement with itself; it is also the
#: `prompt_template_hash` the committed reference run log records, which
#: `tests/test_freeze_proof.py` holds it to.
FROZEN_TEMPLATE_SHA256: Final[str] = (
    "ce6ec2e5c5aa650abdfb1d4d1b31ad1dda171cbb0f18dba8e410d9ab54cc91be"
)

#: The probe, doing what the held-out repository's gate does: import the harness
#: that sits first on `sys.path` and print where that import resolved, so a hash
#: computed by any harness but the frozen one is caught rather than trusted.
PROBE: Final[str] = (
    "import sys\n"
    "from pathlib import Path\n"
    "sys.path.insert(0, sys.argv[1])\n"
    "import harness\n"
    "from harness.judge.prompt import load_template\n"
    "print(harness.__file__)\n"
    "print(load_template(Path(sys.argv[2])).sha256)\n"
)

#: A directory entry in a tree object, as the raw bytes spell it: no leading zero.
_TREE_MODE: Final[str] = "40000"


class ProofError(Exception):
    """A published object that is not what its own name says it is."""


@dataclass(frozen=True)
class Published:
    """One object of the proof, as it sits in `freeze-proof/`."""

    kind: str
    file: str
    object_id: str
    #: Tree objects carry NUL bytes and raw 20-byte ids, so they are base64 here:
    #: this repository tracks no binary file, and a text file cannot hold them.
    encoded: bool


OBJECTS: Final[tuple[Published, ...]] = (
    Published("commit", "freeze-commit.txt", FREEZE_COMMIT, False),
    Published("tag", "freeze-tag.txt", FREEZE_TAG_OBJECT, False),
    Published("tree", "freeze-tree.b64", FREEZE_TREE, True),
    Published("tree", "freeze-prompts-tree.b64", FREEZE_PROMPTS_TREE, True),
)

#: Which published file holds which tree, so both readings below agree on it.
TREE_FILES: Final[dict[str, str]] = {
    FREEZE_TREE: "freeze-tree.b64",
    FREEZE_PROMPTS_TREE: "freeze-prompts-tree.b64",
}

#: The two files the freeze is load-bearing for: the rubric the held-out labels
#: are scored against, and the prompt template the judged tier renders.
FROZEN_FILES: Final[dict[str, tuple[str, str]]] = {
    "rubric.yaml": (FREEZE_TREE, "rubric.yaml"),
    "prompts/judge-dimension.v1.md": (FREEZE_PROMPTS_TREE, "judge-dimension.v1.md"),
}

#: Every 40-hex id the proof's README may name, so a stale one is reported rather
#: than read past. The blob ids are the frozen files', recomputed below.
_HEX40: Final[re.Pattern[str]] = re.compile(r"\b[0-9a-f]{40}\b")
_HEX64: Final[re.Pattern[str]] = re.compile(r"\b[0-9a-f]{64}\b")


def git_id(kind: str, raw: bytes) -> str:
    """Git's object rule, which is the whole of what this tool trusts."""
    return hashlib.sha1(f"{kind} {len(raw)}".encode() + bytes([0]) + raw).hexdigest()


def object_bytes(proof: Path, entry: Published) -> bytes:
    raw = (proof / entry.file).read_bytes()
    return base64.b64decode(raw) if entry.encoded else raw


def parse_tree(raw: bytes) -> dict[str, tuple[str, str]]:
    """A tree object: repeated `<mode> <name>\\0<20 raw bytes>`, by name."""
    entries: dict[str, tuple[str, str]] = {}
    at = 0
    while at < len(raw):
        space = raw.index(b" ", at)
        nul = raw.index(bytes([0]), space)
        mode = raw[at:space].decode("ascii")
        name = raw[space + 1 : nul].decode("utf-8")
        entries[name] = (mode, raw[nul + 1 : nul + 21].hex())
        at = nul + 21
    return entries


def blob_id(path: Path) -> str:
    """The id git would give this file's committed bytes.

    Newlines are normalized first: the objects were committed as LF, and a
    checkout that put CRLF on disk is a checkout property rather than a changed
    rubric -- the same reading `test_the_rubric_and_the_template_at_head_are_the_frozen_commits`
    takes.
    """
    return git_id("blob", path.read_bytes().replace(b"\r\n", b"\n"))


def verify(proof: Path, repo: Path) -> list[str]:
    """Every problem found, in the order the chain is walked. Empty means it holds."""
    problems: list[str] = []
    raw: dict[str, bytes] = {}

    for entry in OBJECTS:
        path = proof / entry.file
        if not path.is_file():
            problems.append(f"{entry.file}: missing, so the {entry.kind} cannot be recomputed")
            continue
        try:
            raw[entry.file] = object_bytes(proof, entry)
        except (ValueError, OSError) as exc:
            problems.append(f"{entry.file}: cannot be read as a git object ({exc})")
            continue
        found = git_id(entry.kind, raw[entry.file])
        if found != entry.object_id:
            problems.append(
                f"{entry.file}: hashes to {found}, and the proof claims {entry.object_id}; "
                "the published bytes are not the object they are said to be"
            )
    if problems:
        return problems

    tag = raw["freeze-tag.txt"].decode("utf-8")
    for expected in (f"object {FREEZE_COMMIT}", "type commit", f"tag {TAG_NAME}"):
        if not re.search(rf"^{re.escape(expected)}$", tag, re.MULTILINE):
            problems.append(f"freeze-tag.txt: no line reads {expected!r}")

    commit = raw["freeze-commit.txt"].decode("utf-8")
    named_tree = re.match(r"tree ([0-9a-f]{40})\n", commit)
    if named_tree is None:
        problems.append("freeze-commit.txt: does not open with a tree line")
    elif named_tree.group(1) != FREEZE_TREE:
        problems.append(
            f"freeze-commit.txt: names tree {named_tree.group(1)}, and the published root tree is "
            f"{FREEZE_TREE}; the commit and the tree beside it are not one pair"
        )

    root = parse_tree(raw["freeze-tree.b64"])
    if root.get("prompts", ("", ""))[1] != FREEZE_PROMPTS_TREE:
        problems.append(
            "freeze-tree.b64: its `prompts` entry is not the published prompts tree, so the "
            "template's blob cannot be reached from the commit"
        )

    trees = {tree_id: parse_tree(raw[name]) for tree_id, name in TREE_FILES.items()}
    for relative, (tree_id, name) in FROZEN_FILES.items():
        frozen = trees[tree_id].get(name)
        if frozen is None:
            problems.append(f"the frozen tree names no {name}, so {relative} is not covered")
            continue
        current = repo / relative
        if not current.is_file():
            problems.append(f"{relative}: missing from this tree, so nothing can be compared")
            continue
        found = blob_id(current)
        if found != frozen[1]:
            problems.append(
                f"{relative}: is blob {found} here and {frozen[1]} at the freeze, so this file has "
                "moved since the held-out labels were scored against it"
            )

    problems.extend(_frozen_harness_problems(proof, repo, root))
    problems.extend(_readme_problems(proof, raw))
    return problems


def _readme_problems(proof: Path, raw: dict[str, bytes]) -> list[str]:
    """The README publishes a digest per object; a stale one is a wrong recipe."""
    readme = proof / "README.md"
    if not readme.is_file():
        return ["freeze-proof/README.md: missing, so the proof publishes no recipe"]
    text = readme.read_text(encoding="utf-8")

    problems: list[str] = []
    digests = {hashlib.sha256(raw[entry.file]).hexdigest(): entry.file for entry in OBJECTS}
    for digest, name in digests.items():
        if digest not in text:
            problems.append(f"README.md: does not name the SHA-256 digest of {name}")
    if FROZEN_TEMPLATE_SHA256 not in text:
        problems.append("README.md: does not name the template hash the frozen code computes")
    for stray in set(_HEX64.findall(text)) - set(digests) - {FROZEN_TEMPLATE_SHA256}:
        problems.append(f"README.md: names a 64-hex digest no published object has: {stray}")

    known = {entry.object_id for entry in OBJECTS}
    known.add(FROZEN_SRC_TREE)
    known.update(path.name.removesuffix(".b64") for path in (proof / OBJECTS_DIR).glob("*"))
    for tree_id, name in FROZEN_FILES.values():
        entries = parse_tree(raw[TREE_FILES[tree_id]])
        if name in entries:
            known.add(entries[name][1])
    for stray in set(_HEX40.findall(text)) - known:
        problems.append(f"README.md: names a 40-hex id the proof does not account for: {stray}")
    return problems


def read_object(proof: Path, object_id: str, kind: str) -> bytes:
    """One published object, verified against its own file name.

    A blob's newlines are normalized first, for the reason `blob_id` gives: the
    objects were committed as LF, and a checkout that put CRLF on disk is a
    checkout property rather than a changed object.
    """
    name = f"{object_id}.b64" if kind == "tree" else object_id
    path = proof / OBJECTS_DIR / name
    if not path.is_file():
        raise ProofError(f"objects/{name}: missing, so the frozen src cannot be reconstructed")
    raw = path.read_bytes()
    raw = base64.b64decode(raw) if kind == "tree" else raw.replace(b"\r\n", b"\n")
    found = git_id(kind, raw)
    if found != object_id:
        raise ProofError(f"objects/{name}: hashes to {found}, so it is not the object it is named")
    return raw


def reconstruct(proof: Path, into: Path) -> None:
    """Write the frozen `src` tree into `into`, verifying every object on the way.

    The walk is the proof: a path exists here only because a tree object named it,
    and a tree object is read only after its own id is recomputed.
    """

    def walk(tree_id: str, at: Path) -> None:
        at.mkdir(parents=True, exist_ok=True)
        for name, (mode, object_id) in parse_tree(read_object(proof, tree_id, "tree")).items():
            if mode == _TREE_MODE:
                walk(object_id, at / name)
            else:
                (at / name).write_bytes(read_object(proof, object_id, "blob"))

    walk(FROZEN_SRC_TREE, into)


def frozen_template(src: Path) -> str:
    """`_DEFAULT_TEMPLATE` as the frozen CLI assigns it, read rather than assumed.

    The held-out gate recovers the template's path this way rather than hard-coding
    it, so this does too: a proof that only works against a path written here would
    not carry that step.
    """
    text = (src / "harness" / "cli.py").read_text(encoding="utf-8")
    found = re.search(r'^_DEFAULT_TEMPLATE[^=]*=\s*"([^"]+)"', text, re.MULTILINE)
    if found is None:
        raise ProofError("the frozen cli.py assigns no _DEFAULT_TEMPLATE")
    return found.group(1)


def probe(src: Path, template: Path) -> tuple[str, str]:
    """Run the frozen code. Returns where `harness` resolved and the hash it computed."""
    run = subprocess.run(
        [sys.executable, "-c", PROBE, str(src), str(template)],
        cwd=src.parent,
        capture_output=True,
        text=True,
    )
    if run.returncode != 0:
        raise ProofError(f"the frozen harness could not be run: {run.stderr.strip()[-300:]}")
    lines = run.stdout.strip().splitlines()
    if len(lines) != 2:
        raise ProofError(f"the probe printed {len(lines)} lines rather than two")
    return lines[0], lines[1]


def _frozen_harness_problems(
    proof: Path, repo: Path, root: dict[str, tuple[str, str]]
) -> list[str]:
    """Reconstruct the frozen src from the objects alone, and run its own code."""
    if root.get("src", ("", ""))[1] != FROZEN_SRC_TREE:
        return [
            "freeze-tree.b64: its `src` entry is not the published frozen src tree, so the "
            "reconstruction below would not be the code the freeze named"
        ]
    with tempfile.TemporaryDirectory(prefix="freeze-proof-") as scratch:
        src = Path(scratch) / "src"
        try:
            reconstruct(proof, src)
            relative = frozen_template(src)
            template = repo / relative
            if not template.is_file():
                return [f"{relative}: the frozen CLI names it and this tree does not carry it"]
            where, computed = probe(src, template)
        except ProofError as error:
            return [str(error)]

        problems: list[str] = []
        if not Path(where).resolve().is_relative_to(src.resolve()):
            problems.append(
                "the template hash came from a harness other than the frozen one: the probe "
                f"imported {where}"
            )
        if computed != FROZEN_TEMPLATE_SHA256:
            problems.append(
                f"the frozen code computes {computed} for {relative}, and the proof publishes "
                f"{FROZEN_TEMPLATE_SHA256}; either the template or the frozen code is not the "
                "one the labels were judged under"
            )
        return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="verify_freeze_proof", description=__doc__)
    parser.add_argument(
        "--proof", default=None, help="the proof directory; freeze-proof/ by default"
    )
    parser.add_argument("--repo", default=None, help="the tree whose frozen files are compared")
    args = parser.parse_args(argv)

    repo = Path(args.repo).resolve() if args.repo else REPO_ROOT
    proof = Path(args.proof).resolve() if args.proof else repo / "freeze-proof"

    problems = verify(proof, repo)
    if problems:
        print("the freeze proof does not verify:", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1

    print(f"the freeze proof verifies: {TAG_NAME} -> {FREEZE_COMMIT[:7]}")
    for relative in FROZEN_FILES:
        print(f"  {relative} is byte for byte the file the freeze named")
    print(f"  the frozen src reconstructs from {OBJECTS_DIR}/ and computes")
    print(f"  {FROZEN_TEMPLATE_SHA256} for the template, in its own code")
    print("  recomputed from the published bytes alone -- no history, no network, no clone")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
