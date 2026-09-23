"""Run the extraction tier: transcripts in, frozen artifact out.

    uv run python -m harness.extract

Deliberately a module entry point rather than a CLI. The real CLI arrives at P2
with `harness run --tier assert` and a tier selector; building an argparse
surface now would mean tearing one out then. What phase 1 needs is for the
phase to end with something that *executes*, because a grammar only looks
complete until a parser reads it -- and that is what this is.

Exit codes:

    0  every transcript parsed, artifact written
    1  at least one unparsed line -- the count is reported, and the run fails
    2  a file-level defect or an unknown tool status -- aborted, named

**`--adapter` selects which source format is read** (D203): `text`, the
corpus's own serialization and the default, or `retell`, a Retell call object
per call. This is where the second adapter is selected and the only place it can
be: extraction produces its stream and the artifact names what its source could
not carry, while `harness run` reads the text serialization alone, because no
check reads a declared gap yet and `build_context` refuses a call carrying one.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Final

from harness.core.artifact import build_payload, write_artifact
from harness.core.events import Call, TranscriptError
from harness.corpus import retell_adapter, text_adapter
from harness.heldout import (
    HELDOUT_SET_FILE,
    any_held_out,
    declared_held_out_calls,
    held_out_write_refusal,
)

_DEFAULT_OUT: str = "build/extraction-artifact.json"
_DEFAULT_CORPUS_VERSION_FILE: str = "corpus/CORPUS_VERSION"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


#: Each selectable adapter: the parse function, the file pattern its source
#: documents carry, and where the design set's live. Two entries rather than a
#: plug-in registry -- an adapter is a function from a source document to a
#: `Call`, and a third is a line here.
ADAPTERS: Final[dict[str, tuple[Callable[[Path], Call], str, str]]] = {
    "text": (text_adapter.parse_call, "*.txt", "corpus/transcripts"),
    "retell": (retell_adapter.parse_call, "*.json", "corpus/retell"),
}


def extract(transcripts_dir: Path, adapter: str = "text") -> tuple[Call, ...]:
    """Parse every source document in the directory, in sorted order.

    Took `corpus_version` and `repo_root` and used neither; four call sites
    passed all three. Ruff did not catch it because `ARG` was not in
    `[tool.ruff.lint] select`, and pyflakes flags unused locals and imports
    rather than parameters. Both are fixed -- the rule catches the class.

    Sorted, because the artifact's hash must not depend on filesystem
    enumeration order -- that would make the same corpus hash differently on
    two machines and quietly break every "recompute and check" claim built on
    top of it.
    """
    parse, pattern, _ = ADAPTERS[adapter]
    paths = sorted(transcripts_dir.glob(pattern))
    if not paths:
        raise FileNotFoundError(f"no {pattern} source documents found in {transcripts_dir}")
    return tuple(parse(path) for path in paths)


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
    parser = argparse.ArgumentParser(prog="harness.extract", description=__doc__)
    parser.add_argument("--adapter", choices=sorted(ADAPTERS), default="text")
    parser.add_argument(
        "--transcripts",
        default=None,
        help="the source documents' directory; defaults to the selected adapter's design set",
    )
    parser.add_argument("--out", default=_DEFAULT_OUT)
    parser.add_argument("--corpus-version-file", default=_DEFAULT_CORPUS_VERSION_FILE)
    args = parser.parse_args(argv)

    root = _repo_root()
    transcripts_dir = Path(args.transcripts or ADAPTERS[args.adapter][2])
    if not transcripts_dir.is_absolute():
        transcripts_dir = root / transcripts_dir
    version_file = Path(args.corpus_version_file)
    if not version_file.is_absolute():
        version_file = root / version_file
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = root / out_path

    corpus_version = version_file.read_text(encoding="utf-8").strip()

    try:
        calls = extract(transcripts_dir, args.adapter)
    except (TranscriptError, FileNotFoundError) as exc:
        print(f"extraction aborted: {exc}", file=sys.stderr)
        return 2

    # **An artifact over held-out calls is held-out content** (D196). It carries
    # every turn of every call it parses, and this command read no `HELDOUT_SET`
    # and wrote to `build/` on its default, so pointing it at the held-out
    # transcripts -- which a session may read in place since the reveal -- put them
    # in this tree under another name. The rule is D185's, one command over.
    try:
        held_out_set = declared_held_out_calls(root / HELDOUT_SET_FILE)
    except OSError as exc:
        print(
            f"extraction refused: {exc}. Extraction reads HELDOUT_SET to tell whether the "
            "calls it parses are held out, and so whether its artifact may be written "
            "inside this checkout.",
            file=sys.stderr,
        )
        return 2
    refusal = held_out_write_refusal(
        "an extraction artifact over calls HELDOUT_SET declares carries every turn of them",
        held_out=any_held_out((call.record.call_id for call in calls), held_out_set),
        destination=out_path,
        given=args.out,
        root=root,
    )
    if refusal:
        print(f"extraction refused: {refusal}", file=sys.stderr)
        return 2

    unparsed_total = sum(len(call.unparsed) for call in calls)
    for call in calls:
        for line in call.unparsed:
            print(
                f"{call.source_path}:{line.line_number}: unparsed -- {line.reason}",
                file=sys.stderr,
            )

    payload = build_payload(calls, corpus_version, root, adapter=args.adapter)
    digest = write_artifact(out_path, payload)

    events = sum(len(call.events) for call in calls)
    print(f"calls: {len(calls)}  events: {events}  unparsed lines: {unparsed_total}")
    print(f"artifact: {_display(out_path, root)}")
    print(f"content hash: {digest}")

    if unparsed_total:
        # Reported, not discarded, and the run fails. W18 was the absence of
        # this counter entirely; W19 was a conformance test that crashed
        # instead of reporting the violation it had already recorded. The
        # artifact is still written, so the recorded violations are inspectable
        # rather than lost with the process.
        print(f"FAILED: {unparsed_total} unparsed line(s)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
