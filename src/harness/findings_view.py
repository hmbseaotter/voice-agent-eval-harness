"""Regenerate the Markdown reading view from the findings YAML.

    uv run python -m harness.findings_view --check     # CI: is the view stale?
    uv run python -m harness.findings_view             # rewrite it

The YAML is the source of truth. `--check` exists because a generated file that
nobody verifies drifts from its source and then quietly becomes a second,
disagreeing source -- which is the shape this project keeps finding.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from harness.core.findings import load_findings, render_markdown
from harness.heldout import (
    HELD_OUT_FINDING_ID,
    HELDOUT_SET_FILE,
    any_held_out,
    declared_held_out_calls,
    held_out_write_refusal,
)

_DEFAULT_FINDINGS: str = "corpus/findings.yaml"
_DEFAULT_OUT: str = "corpus/findings.md"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _display(path: Path, root: Path) -> str:
    """Repo-relative when it can be, absolute otherwise.

    `Path.relative_to` raises for a path outside the root, so a success message
    that assumed repo-relative crashed whenever the output was written
    elsewhere -- which is exactly what a test writing to a temp directory does.
    A progress line should never be able to fail the run it is reporting on.
    """
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="harness.findings_view", description=__doc__)
    parser.add_argument("--findings", default=_DEFAULT_FINDINGS)
    parser.add_argument("--out", default=_DEFAULT_OUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if the view on disk differs from the regenerated one",
    )
    args = parser.parse_args(argv)

    root = _repo_root()
    findings_path = Path(args.findings)
    if not findings_path.is_absolute():
        findings_path = root / findings_path
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = root / out_path

    findings = load_findings(findings_path)
    rendered = render_markdown(findings)

    # **A view over held-out labels is held-out content** (D196). It renders every
    # finding it is given -- observation, evidence and consequence -- and this
    # command read no `HELDOUT_SET`, defaulting `--out` to the tracked design view,
    # so pointing it at the held-out labels overwrote that file with them. Held out
    # by either mark: a finding's id has the held-out shape, or its call is declared.
    # `--check` writes nothing, so it is not refused.
    if not args.check:
        try:
            held_out_set = declared_held_out_calls(root / HELDOUT_SET_FILE)
        except OSError as exc:
            print(
                f"view refused: {exc}. The view reads HELDOUT_SET to tell whether the "
                "findings it renders are held out, and so whether it may be written inside "
                "this checkout.",
                file=sys.stderr,
            )
            return 2
        held_out = any_held_out((finding.call_ref for finding in findings), held_out_set) or any(
            HELD_OUT_FINDING_ID.fullmatch(finding.id) for finding in findings
        )
        refusal = held_out_write_refusal(
            "a findings view over held-out labels carries every finding it renders",
            held_out=held_out,
            destination=out_path,
            given=args.out,
            root=root,
        )
        if refusal:
            print(f"view refused: {refusal}", file=sys.stderr)
            return 2

    if args.check:
        if not out_path.is_file():
            print(f"{out_path} does not exist; regenerate it", file=sys.stderr)
            return 1
        current = out_path.read_text(encoding="utf-8")
        if current != rendered:
            print(f"{out_path} is stale; regenerate it", file=sys.stderr)
            return 1
        print(f"view is current: {len(findings)} findings")
        return 0

    with out_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(rendered)
    print(f"wrote {_display(out_path, root)} ({len(findings)} findings)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
