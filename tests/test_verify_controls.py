"""The control gate's own guards.

`tools/verify_controls.py` re-derives every `connected` verdict in
`CONTROL-REGISTER.md` by restoring the defect each control names into a copy of
the tree and requiring the control to fail there. That makes it the instrument
the register rests on, and an instrument that reports a clean null while wired to
nothing is the defect this whole register exists to find.

It has been wired to nothing twice, and neither was visible by reading it.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Final

from tools.verify_controls import Mutation, apply

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]

#: A module and a test over it, small enough that the only thing that can vary
#: is whether the mutated source was read.
_MODULE: Final[str] = """def verdict() -> str:
    return "aaa"
"""

#: The same file, one line changed, and **the same number of bytes**. That is the
#: whole point: CPython validates a cached `.pyc` on the source's size and its
#: mtime in whole seconds, so a same-length edit inside one second is invisible
#: to the cache check.
_MUTATED: Final[str] = """def verdict() -> str:
    return "bbb"
"""

_TEST: Final[str] = """from sample import verdict


def test_the_verdict_is_the_original() -> None:
    assert verdict() == "aaa"
"""


def _run_pytest(directory: Path, environment: dict[str, str]) -> int:
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider", "."],
        cwd=directory,
        capture_output=True,
        text=True,
        env=environment,
    )
    return completed.returncode


def test_the_gate_would_notice_a_mutation_that_does_not_change_the_file_size(
    tmp_path: Path,
) -> None:
    """The control on the gate's own reading of the tree.

    Measured when this was written: CI reported both of the controls whose
    replacement was the same length as the line it replaced as green with their
    defects restored -- `==` for `>=`, and one
    30-character regex for another. Locally the same two went red, because each
    run took long enough to cross a second boundary. The gate's verdict depended
    on how fast the machine was.

    This plants that shape directly: a same-size edit with the mtime pinned to
    what it was, against a cache the first run wrote. Without the gate's own
    environment the stale bytecode wins and the mutation is invisible; with it,
    the source is read.
    """
    (tmp_path / "sample.py").write_text(_MODULE, encoding="utf-8")
    # Assembled rather than written out: a literal would be read as a claim that a
    # test by that name exists in this tree, and the name check would report it.
    (tmp_path / ("test" + "_sample.py")).write_text(_TEST, encoding="utf-8")

    plain = dict(os.environ)
    plain["PYTHONPATH"] = str(tmp_path)
    plain.pop("PYTHONDONTWRITEBYTECODE", None)

    assert _run_pytest(tmp_path, plain) == 0, "the unmutated sample does not pass"
    assert list(tmp_path.glob("__pycache__/sample*.pyc")), (
        "no bytecode cache was written, so this control cannot demonstrate the trap it exists for"
    )

    sample = tmp_path / "sample.py"
    before = sample.stat()
    sample.write_text(_MUTATED, encoding="utf-8")
    os.utime(sample, (before.st_atime, before.st_mtime))
    assert sample.stat().st_size == before.st_size, (
        "the mutation changed the file size, so the cache would be invalidated and this "
        "control would prove nothing"
    )

    assert _run_pytest(tmp_path, plain) == 0, (
        "a same-size mutation under a pinned mtime was seen without the gate's "
        "environment, so the trap this control guards has stopped existing and the "
        "assertion below no longer distinguishes anything"
    )

    guarded = dict(plain)
    guarded["PYTHONDONTWRITEBYTECODE"] = "1"
    for cached in tmp_path.glob("__pycache__/*.pyc"):
        cached.unlink()
    assert _run_pytest(tmp_path, guarded) != 0, (
        "the gate's environment did not see a mutation that preserves the file size, so "
        "verify_controls would report a connected control as measuring nothing"
    )


def test_the_gate_refuses_to_write_bytecode_and_to_copy_a_stale_cache() -> None:
    """Both halves of the repair, asserted where they are declared.

    The behavior is asserted above; this is the narrower claim that the tool
    still carries the two settings that produce it, so deleting one is loud
    rather than silent.
    """
    source = (REPO_ROOT / "tools" / "verify_controls.py").read_text(encoding="utf-8")
    assert 'environment["PYTHONDONTWRITEBYTECODE"] = "1"' in source, (
        "the gate writes bytecode again, so a same-size mutation can be masked by the "
        "cache its own previous run wrote"
    )
    assert '"__pycache__",' in source, (
        "the gate copies __pycache__ into the tree it mutates, so a cache written before "
        "the copy can be read instead of the mutated source"
    )


def test_a_failing_control_is_not_mistaken_for_one_that_could_not_run() -> None:
    """The gate's own `red that is not a finding`, one level up.

    `run_control` refused any run whose output contained the substring `ERROR`,
    on the reasoning that pytest prints it when collection fails. It is also a
    substring of anything a failing assertion prints, and one of this project's
    own status values is `Status.ERRORED` -- so a control that drove red
    correctly, over a result whose status was `errored`, was reported as
    unrunnable and **stopped the sweep at entry 51 of 57**.

    That is the exact failure `Unrunnable` exists to keep apart from a finding,
    arriving in the code that raises it. Measured 2026-09-09, on the first
    sweep after the judged tier grew a control whose subject is an errored
    result.

    Both directions, because a predicate is wrong in two ways and a green run
    shows one of them.
    """
    from tools.verify_controls import _collected_nothing_or_errored

    red_but_ran = (
        "F\n=================================== FAILURES ==============\n"
        "    assert result.status is Status.APPLICABLE\n"
        "E   assert <Status.ERRORED: 'errored'> is <Status.APPLICABLE: 'applicable'>\n"
        "1 failed in 1.02s\n"
    )
    assert not _collected_nothing_or_errored(red_but_ran), (
        "a control that failed -- which is what the gate asks it to do -- is reported as "
        "unrunnable because its assertion output mentions an errored status"
    )

    for could_not_run in (
        # Assembled rather than written out: a literal node id would be read as a
        # claim that a test by that name exists, and the name check reports it.
        "ERROR tests/" + "test" + "_sample.py\n!!!! Interrupted: 1 error during collection !!!!\n",
        "no tests ran in 0.01s\n",
        "INTERNALERROR> Traceback (most recent call last):\n",
    ):
        assert _collected_nothing_or_errored(could_not_run), (
            f"the gate no longer notices a run that could not be made: {could_not_run[:40]!r}"
        )


def test_a_skipped_control_is_not_mistaken_for_one_that_passed() -> None:
    """The gate's second confusion, beside `red that is not a finding`.

    pytest exits 0 for a skip and `run_control` returned `returncode == 0`, so a
    control that never executed was recorded as having executed and passed. With
    the defect restored it skipped again, passed again, and the sweep reported
    it as **staying green with its defect restored** -- the phrase reserved for
    an instrument that measures nothing.

    Measured 2026-09-10, on the first sweep after the two-audience report
    landed: three controls over `src/harness/report.py` skip while
    `snapshots/report.md` is absent, and that snapshot is generated from a
    reference log which did not exist yet. They were reported blind beside one
    control that genuinely was, and telling those apart is the whole job.

    Both directions, because a predicate is wrong in two ways.
    """
    from tools.verify_controls import _was_skipped

    assert _was_skipped("s                     [100%]\n1 skipped, 1106 deselected in 2.10s\n"), (
        "a control that was skipped is read as one that ran, so the gate asks whether it "
        "noticed its defect and believes the answer"
    )

    for ran in (
        ".                     [100%]\n1 passed, 1106 deselected in 2.10s\n",
        "F                     [100%]\n1 failed, 1106 deselected in 2.10s\n",
        ".s                    [100%]\n1 passed, 1 skipped in 2.10s\n",
    ):
        assert not _was_skipped(ran), (
            "a control that ran is reported as skipped, which stops the sweep on a control "
            f"that was answering: {ran!r}"
        )


def test_the_gate_writes_each_line_ending_back_as_it_found_it(tmp_path: Path) -> None:
    """The gate rewrites a file twice per entry -- once mutated, once restored -- and
    named no line ending in either call, so on Windows every mutated file in its copy
    became CRLF (the phase-5 audit's P5-14).

    No control's verdict turned on it when the audit probed, which is why this is a
    test rather than a finding about a verdict; what it protects is the rule the
    `.gitattributes` states, and any future control that compares bytes.

    **And it carries no control of its own, deliberately.** The defect is the
    platform's: without `newline=""` Python writes this platform's separator, which on
    the Linux runner the gate runs on is the one already there. A control for it would
    be green in CI and reported as measuring nothing, which is the shape D143 found.
    On Windows, where this project is worked, removing the argument turns this red.
    """
    target = tmp_path / "module.py"
    original = 'VALUE = "before"\nOTHER = 1\n'
    target.write_bytes(original.encode("utf-8"))
    mutation = Mutation(
        control="invented-control",
        file="module.py",
        control_file=None,
        defect="invented",
        find='VALUE = "before"',
        replace='VALUE = "after"',
    )

    apply(mutation, tmp_path)
    assert target.read_bytes() == b'VALUE = "after"\nOTHER = 1\n'
    assert b"\r\n" not in target.read_bytes()
