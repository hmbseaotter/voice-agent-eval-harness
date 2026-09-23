"""What the held-out set declares, and where a command may write what it reads.

Four commands refuse to write held-out content inside this checkout: a held-out
run's paths and its log (D174), agreement's and the coverage report's held-out
sections (D175, D188), and a report over held-out calls (D185). Two more wrote
there on their defaults and read no `HELDOUT_SET` at all -- `harness.extract`,
whose artifact carries every turn of every call it parses, and
`harness.findings_view`, whose view carries every finding it is given (the
phase-5 audit's P5-2, D196).

The pieces they share live here rather than in `harness.cli`, which imports the
whole harness: the declaration, the shape of a held-out finding's id, and the
one refusal. `harness.cli` and `harness.agreement` read them from here too, so
there is one definition of each rather than one per entry point.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path
from typing import Final

#: Where the held-out call identifiers are declared, relative to the repository root.
HELDOUT_SET_FILE: Final[str] = "HELDOUT_SET"

#: A held-out finding's id. The design set's are `F-nn`; the held-out labels use
#: `HF-nn`, which is what tells a held-out finding from a design one by shape alone.
HELD_OUT_FINDING_ID: Final[re.Pattern[str]] = re.compile(r"HF-\d{2,}")


def declared_held_out_calls(path: Path) -> frozenset[str]:
    """The call identifiers `HELDOUT_SET` declares, read the way the absence check reads them.

    A file that is not there raises rather than reading as an empty set (D173). A
    run that cannot tell whether its calls are held out cannot tell whether it
    needs a labels manifest, and a held-out log written without one is refused by
    the held-out repository's gate only after its calls were paid for. A corpus
    with no held-out set gives the file no identifiers.
    """
    declared = path.read_text(encoding="utf-8").split("\n")
    return frozenset(
        line.strip() for line in declared if line.strip() and not line.strip().startswith("#")
    )


def held_out_write_refusal(
    carries: str, *, held_out: bool, destination: Path, given: str, root: Path
) -> str:
    """Why this output may not be written where `--out` points, or `""` (D196).

    The rule D174, D175, D185 and D188 each state for one command: held-out
    content may go to stdout, and to a file outside this checkout, and never to a
    file inside it. `carries` says what the output holds, because a refusal a
    reader cannot act on is a refusal they route around.
    """
    if not held_out:
        return ""
    if not destination.resolve().is_relative_to(root.resolve()):
        return ""
    return (
        f"{carries}, and --out {given} would write it inside {root}; write it outside this "
        "checkout, or leave the held-out inputs out of this run (D196)."
    )


def any_held_out(names: Iterable[str], held_out_set: frozenset[str]) -> bool:
    """Whether any of these call identifiers is one `HELDOUT_SET` declares."""
    return any(name in held_out_set for name in names)
