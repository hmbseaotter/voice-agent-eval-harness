"""The two commands that wrote held-out content into this tree, and now refuse (D196).

`harness.extract` writes every turn of every call it parses, and `harness.findings_view`
every finding it is given; both defaulted `--out` inside the checkout and read no
`HELDOUT_SET`, so pointing either at the held-out files -- which a session may read in
place since the reveal -- put their content here under another name (the phase-5
audit's P5-2).

**No held-out file is read here.** The held-out side of each test is design data
renamed: a design transcript carrying a call id `HELDOUT_SET` declares, and design
findings under `HF-` ids, which is the pattern `tests/test_cli.py` uses for the same
reason.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from harness import extract as extract_module
from harness import findings_view
from harness.core.findings import dump_findings, load_findings
from harness.heldout import declared_held_out_calls, held_out_write_refusal

REPO_ROOT: Path = Path(__file__).resolve().parents[1]


def _held_out_call() -> str:
    declared = sorted(declared_held_out_calls(REPO_ROOT / "HELDOUT_SET"))
    assert declared, "HELDOUT_SET declares nothing, so these tests plant nothing"
    return declared[0]


def _checkout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A checkout of this repository's shape: a root declaring the held-out set, which
    both commands resolve their defaults and their `--out` against."""
    root = tmp_path / "checkout"
    (root / "build").mkdir(parents=True)
    (root / "corpus").mkdir()
    for name in (Path("HELDOUT_SET"), Path("corpus") / "CORPUS_VERSION"):
        (root / name).write_text(
            (REPO_ROOT / name).read_text(encoding="utf-8"), encoding="utf-8", newline="\n"
        )
    monkeypatch.setattr(extract_module, "_repo_root", lambda: root)
    monkeypatch.setattr(findings_view, "_repo_root", lambda: root)
    return root


def _transcripts(tmp_path: Path, call_id: str) -> Path:
    """One design transcript, renamed to `call_id`, outside the checkout."""
    directory = tmp_path / f"transcripts-{call_id}"
    directory.mkdir()
    design = (REPO_ROOT / "corpus" / "transcripts" / "CALL-01.txt").read_text(encoding="utf-8")
    (directory / f"{call_id}.txt").write_text(
        design.replace("CALL-01", call_id), encoding="utf-8", newline=""
    )
    return directory


def _findings_file(tmp_path: Path, *, finding_id: str, call_ref: str) -> Path:
    borrowed = load_findings(REPO_ROOT / "corpus" / "findings.yaml")[0]
    path = tmp_path / f"findings-{finding_id}.yaml"
    path.write_text(
        dump_findings((replace(borrowed, id=finding_id, call_ref=call_ref),)),
        encoding="utf-8",
        newline="\n",
    )
    return path


def test_extraction_over_a_declared_call_refuses_an_out_path_inside_the_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The artifact carries every turn of every call, so over a call `HELDOUT_SET`
    declares it may not be written inside this tree -- the rule D185 gave the report,
    one command over (D196). Nothing is written, and the flag is named."""
    call_id = _held_out_call()
    root = _checkout(tmp_path, monkeypatch)
    transcripts = _transcripts(tmp_path, call_id)
    inside = root / "build" / "artifact.json"

    assert extract_module.main(["--transcripts", str(transcripts), "--out", str(inside)]) == 2
    assert "--out" in capsys.readouterr().err
    assert not inside.exists(), "the artifact was written after the refusal"

    outside = tmp_path / "outside" / "artifact.json"
    outside.parent.mkdir()
    assert extract_module.main(["--transcripts", str(transcripts), "--out", str(outside)]) == 0
    assert call_id in outside.read_text(encoding="utf-8")


def test_extraction_over_the_design_set_still_writes_inside_the_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The false-positive half: the design artifact is what CI writes on every run,
    into `build/`, and the refusal does not touch it (D196)."""
    root = _checkout(tmp_path, monkeypatch)
    transcripts = _transcripts(tmp_path, "CALL-01")
    inside = root / "build" / "artifact.json"
    assert extract_module.main(["--transcripts", str(transcripts), "--out", str(inside)]) == 0
    written = json.loads(inside.read_text(encoding="utf-8"))
    assert [call["call"]["call_id"] for call in written["calls"]] == ["CALL-01"]


def test_extraction_is_refused_when_the_declaration_cannot_be_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A command that cannot tell whether its calls are held out cannot tell whether it
    may write them here, so it refuses rather than assuming they are not (D173, D196)."""
    root = _checkout(tmp_path, monkeypatch)
    (root / "HELDOUT_SET").unlink()
    transcripts = _transcripts(tmp_path, "CALL-01")
    assert (
        extract_module.main(
            ["--transcripts", str(transcripts), "--out", str(root / "build" / "artifact.json")]
        )
        == 2
    )
    assert "HELDOUT_SET" in capsys.readouterr().err


def test_the_view_over_held_out_labels_refuses_an_out_path_inside_the_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The view renders every finding it is given, observation, evidence and all, and
    its default `--out` is the tracked design view. Held out by either mark: the
    finding's call is declared, or its id has the held-out shape (D196)."""
    call_id = _held_out_call()
    root = _checkout(tmp_path, monkeypatch)
    inside = root / "build" / "view.md"
    by_call = _findings_file(tmp_path, finding_id="F-01", call_ref=call_id)
    by_id = _findings_file(tmp_path, finding_id="H" + "F-07", call_ref="CALL-01")

    for findings in (by_call, by_id):
        assert findings_view.main(["--findings", str(findings), "--out", str(inside)]) == 2
        assert "--out" in capsys.readouterr().err
        assert not inside.exists(), "the view was written after the refusal"

    outside = tmp_path / "outside" / "view.md"
    outside.parent.mkdir()
    assert findings_view.main(["--findings", str(by_id), "--out", str(outside)]) == 0
    assert outside.read_text(encoding="utf-8").startswith("# Findings")


def test_the_design_view_still_writes_inside_the_checkout_and_check_is_not_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The false-positive half, and the one mode that writes nothing: `--check` reads a
    view and compares it, so it is not refused even over held-out labels (D196)."""
    root = _checkout(tmp_path, monkeypatch)
    inside = root / "build" / "view.md"
    design = _findings_file(tmp_path, finding_id="F-01", call_ref="CALL-01")
    assert findings_view.main(["--findings", str(design), "--out", str(inside)]) == 0

    held_out = _findings_file(tmp_path, finding_id="H" + "F-07", call_ref=_held_out_call())
    before = inside.read_text(encoding="utf-8")
    assert findings_view.main(["--findings", str(held_out), "--out", str(inside), "--check"]) == 1
    assert inside.read_text(encoding="utf-8") == before, "--check wrote the view it compared"


def test_the_refusal_reads_both_halves_of_its_rule(tmp_path: Path) -> None:
    """The shared refusal, directly: held-out content and a destination inside the
    checkout are both required, and the message names the flag a reader has to change
    (D196)."""
    root = tmp_path / "checkout"
    root.mkdir()
    inside, outside = root / "out.json", tmp_path / "out.json"
    assert (
        held_out_write_refusal("x", held_out=False, destination=inside, given="o", root=root) == ""
    )
    assert (
        held_out_write_refusal("x", held_out=True, destination=outside, given="o", root=root) == ""
    )
    refusal = held_out_write_refusal(
        "an artifact over declared calls", held_out=True, destination=inside, given="o", root=root
    )
    assert "an artifact over declared calls" in refusal and "--out o" in refusal
