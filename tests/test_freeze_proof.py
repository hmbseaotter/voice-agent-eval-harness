"""Hold the published freeze proof to being what it says it is.

WHY THIS EXISTS
---------------
`freeze-proof/` is the opening of a commit-reveal: the held-out repository's seal
commit cites the freeze commit's SHA, and these four objects are what a reader
recomputes that citation against (D209). Publishing this project as a snapshot
left the citation unresolvable in the public log, so the proof is the only route
from that citation to the rubric it names.

**The proof is bytes, and bytes are exactly what rots quietly.** A file rewritten
by a formatter, a digest gone stale in the README, an editor normalizing a
newline -- each leaves a proof that still looks like a proof and no longer
verifies. Nothing about that is visible to a reader, which is why it is a build
failure here.

EACH PROPERTY ASSERTED APART
----------------------------
Each test below fails for its own reason, rather than all of them calling
`verify()` and reporting the same list. That is what lets the control gate drive
several of them red separately: a corrupted object, a moved rubric, a stale digest
and a moved template are different defects, and one test covering all of them
would be driven red by any one and prove only that one path works.

THE INPUTS ARE NOT THE COMPUTATION
----------------------------------
Since D210 the proof also carries the frozen `src` tree, because the held-out gate
does not merely read the frozen template: it computes that template's hash by
running the frozen harness's own code, and refuses a hash that came from any
other. So two tests below reconstruct `src/` from the published objects alone and
run that code -- the acceptance test for D210, and the one that makes the gate
portable.

NO GIT, DELIBERATELY
--------------------
Every id here is recomputed with git's object rule rather than asked of git. The
control gate runs in a copy of the tree with no `.git`, so a check that shelled
out to git could not be driven red at all -- the reason
`test_the_pinned_frozen_commit_is_the_one_the_tag_points_at` is not a control.
This one is.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Final

import pytest
from tools.verify_freeze_proof import (
    FREEZE_COMMIT,
    FREEZE_PROMPTS_TREE,
    FREEZE_TREE,
    FROZEN_FILES,
    FROZEN_SRC_TREE,
    FROZEN_TEMPLATE_SHA256,
    OBJECTS,
    TAG_NAME,
    TREE_FILES,
    ProofError,
    blob_id,
    frozen_template,
    git_id,
    object_bytes,
    parse_tree,
    probe,
    reconstruct,
    verify,
)

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
PROOF: Final[Path] = REPO_ROOT / "freeze-proof"


def _bytes() -> dict[str, bytes]:
    return {entry.file: object_bytes(PROOF, entry) for entry in OBJECTS}


def test_every_published_object_hashes_to_the_id_it_claims() -> None:
    """Git's own rule, `sha1("<type> <size>\\0" + bytes)`, over the published files.

    This is the whole proof: a reader who runs it needs no clone and no trust.
    """
    assert len(OBJECTS) == 4, "the proof publishes four objects; this check reads what it is given"
    for entry in OBJECTS:
        raw = object_bytes(PROOF, entry)
        assert git_id(entry.kind, raw) == entry.object_id, (
            f"freeze-proof/{entry.file} does not hash to {entry.object_id}, so the published bytes "
            "are not the object the proof names. The proof is the only route from the held-out "
            "seal commit's citation to this rubric; do not regenerate it, find what changed."
        )


def test_the_published_chain_runs_from_the_tag_to_the_frozen_files() -> None:
    """The tag names the freeze, the freeze names the tree, the tree names the files.

    A link asserted in prose is the state this proof was written to leave.
    """
    raw = _bytes()

    tag = raw["freeze-tag.txt"].decode("utf-8").splitlines()
    assert f"object {FREEZE_COMMIT}" in tag, tag
    assert "type commit" in tag, tag
    assert f"tag {TAG_NAME}" in tag, tag

    commit = raw["freeze-commit.txt"].decode("utf-8")
    assert commit.startswith(f"tree {FREEZE_TREE}\n"), commit[:80]

    root = parse_tree(raw["freeze-tree.b64"])
    assert root["prompts"] == ("40000", FREEZE_PROMPTS_TREE), root["prompts"]
    for relative, (tree_id, name) in FROZEN_FILES.items():
        assert name in parse_tree(raw[TREE_FILES[tree_id]]), (
            f"the frozen tree names no {name}, so {relative} is outside the proof"
        )


def test_the_frozen_blobs_are_the_files_at_head() -> None:
    """The rubric and the template here are the ones the labels were scored against.

    The public snapshot's own pin cannot say this: there the pin points at the
    snapshot's first commit, so comparing HEAD against it is a tautology. This
    compares HEAD against the freeze's own tree, which is the real claim.
    """
    raw = _bytes()
    for relative, (tree_id, name) in FROZEN_FILES.items():
        frozen = parse_tree(raw[TREE_FILES[tree_id]])[name][1]
        assert blob_id(REPO_ROOT / relative) == frozen, (
            f"{relative} is not the blob the freeze named. The held-out labels are scored against "
            "the frozen text, so this file may not move while those labels stand."
        )


def test_the_proof_readme_names_the_digests_the_files_have() -> None:
    """A recipe that prints a digest the README does not carry is a wrong recipe.

    Checked in both directions: every published object's digest is named, and the
    README names no 64-hex string that is not one of them -- a stale digest left
    beside a corrected one reads exactly like a current one.
    """
    text = (PROOF / "README.md").read_text(encoding="utf-8")
    digests = {hashlib.sha256(raw).hexdigest() for raw in _bytes().values()}
    assert len(digests) == 4, "two objects share a digest, which cannot happen"

    for digest in digests:
        assert digest in text, f"freeze-proof/README.md does not name the digest {digest}"
    assert FROZEN_TEMPLATE_SHA256 in text, (
        "the README does not name the hash the frozen code computes for the template"
    )

    named = set(re.findall(r"\b[0-9a-f]{64}\b", text))
    allowed = digests | {FROZEN_TEMPLATE_SHA256}
    assert named == allowed, f"README.md names digests nothing has: {sorted(named - allowed)}"


def test_the_verifier_reports_a_corrupted_object_rather_than_passing(tmp_path: Path) -> None:
    """One byte, and the proof must stop verifying. Planted, because a checker that
    cannot fail reads exactly like a tree that is clean.

    The mutation is inside the commit's tree line, so it is also the shape that
    would break the chain -- and the hash check catches it first, which is the
    order a reader benefits from: the object is wrong before anything it says is.
    """
    copy = tmp_path / "freeze-proof"
    shutil.copytree(PROOF, copy)
    target = copy / "freeze-commit.txt"
    raw = target.read_bytes()
    target.write_bytes(raw.replace(b"tree 11319ced", b"tree 11319cedf", 1))

    problems = verify(copy, REPO_ROOT)
    assert problems, "a corrupted commit object verified, so this check proves nothing"
    assert "freeze-commit.txt" in problems[0], problems


def test_the_command_exits_one_when_the_proof_does_not_verify(tmp_path: Path) -> None:
    """Exit codes, because the register and the README both point a reader at the
    command rather than at the function.
    """
    copy = tmp_path / "freeze-proof"
    shutil.copytree(PROOF, copy)
    (copy / "freeze-tag.txt").unlink()

    run = subprocess.run(
        [sys.executable, "-m", "tools.verify_freeze_proof", "--proof", str(copy)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert run.returncode == 1, run.stdout + run.stderr
    assert "freeze-tag.txt" in run.stderr, run.stderr

    ok = subprocess.run(
        [sys.executable, "-m", "tools.verify_freeze_proof"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert ok.returncode == 0, ok.stdout + ok.stderr


def test_the_frozen_src_reconstructs_from_the_published_objects(tmp_path: Path) -> None:
    """The acceptance test for D210: `src/` at the freeze, from `objects/` alone.

    No clone, no private repository, no network. `reconstruct` verifies every
    object against its own file name as it walks, so a reconstruction that
    completes is one that was proved rather than copied.
    """
    raw = _bytes()
    assert parse_tree(raw["freeze-tree.b64"])["src"][1] == FROZEN_SRC_TREE, (
        "the root tree's `src` entry is not the published frozen src tree"
    )

    src = tmp_path / "src"
    reconstruct(PROOF, src)
    files = sorted(path.relative_to(src).as_posix() for path in src.rglob("*") if path.is_file())
    assert len(files) == 34, f"reconstructed {len(files)} files rather than 34: {files}"
    assert "harness/judge/prompt.py" in files, files
    assert "harness/cli.py" in files, files


def test_the_frozen_code_computes_the_frozen_template_hash(tmp_path: Path) -> None:
    """The frozen harness's own `load_template`, over the published template.

    This is the property the held-out gate asserts and the four core objects
    cannot: they settle which bytes were frozen, not what the frozen code made
    of them. The guard on where `harness` resolved is the gate's own, kept here
    so that a hash computed by this repository's current code cannot pass for
    the frozen one.
    """
    src = tmp_path / "src"
    reconstruct(PROOF, src)

    relative = frozen_template(src)
    assert relative == "prompts/judge-dimension.v1.md", relative

    where, computed = probe(src, REPO_ROOT / relative)
    assert Path(where).resolve().is_relative_to(src.resolve()), (
        f"the template hash came from a harness other than the frozen one: {where}"
    )
    assert computed == FROZEN_TEMPLATE_SHA256, (
        f"the frozen code computes {computed} and the proof publishes "
        f"{FROZEN_TEMPLATE_SHA256}; either the template or the frozen code has moved"
    )


def test_the_published_template_hash_is_what_the_reference_run_log_recorded() -> None:
    """The one number in the proof that a recorded run also carries.

    A hash the proof computes and nothing else uses would be self-consistent and
    unmoored. The committed reference log is what every replay and every report
    is served from, and it stamped this template hash at the time.
    """
    log = REPO_ROOT / "runs" / "reference-corpus-0.6.0.jsonl"
    header = json.loads(log.read_text(encoding="utf-8").splitlines()[0])
    assert header["prompt_template_hash"] == FROZEN_TEMPLATE_SHA256, (
        "the reference run log's prompt_template_hash is not what the frozen code computes"
    )


def test_a_corrupted_published_object_stops_the_reconstruction(tmp_path: Path) -> None:
    """One byte in `objects/`, and the walk must refuse rather than write it.

    Planted, because a reconstruction that accepts whatever it finds proves only
    that files were copied.
    """
    copy = tmp_path / "freeze-proof"
    shutil.copytree(PROOF, copy)
    target = copy / "objects" / "8b5876692b985c1f525be1c280b3894d17531eee"
    target.write_bytes(
        target.read_bytes().replace(b"Rendering a judge prompt", b"Rendering a judge prompts", 1)
    )

    with pytest.raises(ProofError) as refused:
        reconstruct(copy, tmp_path / "src")
    assert "8b58766" in str(refused.value), refused.value


def test_the_probe_would_import_another_harness_without_the_reconstruction(
    tmp_path: Path,
) -> None:
    """Why the guard above is not decoration.

    Pointed at a directory holding no `harness`, the probe still succeeds: it
    imports the harness this checkout installs and prints a hash computed by
    today's code. That is the failure the gate's guard exists to catch, and it is
    silent in every other respect -- today the hash even agrees.
    """
    empty = tmp_path / "not-a-harness"
    empty.mkdir()
    where, computed = probe(empty, REPO_ROOT / "prompts" / "judge-dimension.v1.md")
    assert not Path(where).resolve().is_relative_to(empty.resolve()), (
        "a directory holding no harness somehow provided one"
    )
    assert computed == FROZEN_TEMPLATE_SHA256, (
        "today's code computes a different hash than the frozen code, which is exactly the case "
        "the guard makes detectable -- read the guard again rather than relaxing it"
    )
