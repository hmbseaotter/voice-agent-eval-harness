"""Triage the control register for the shape four defective controls all had.

The question is *does the control drive the check's own comparison, or a copy of
it?* A control that re-implements the rule beside the check is proof about its
own copy of the logic, which is the one copy that cannot fail in production. Four
controls in this tree were written that way; none was found by rereading, and one
was written by the audit that found the other three.

**The signal.** The check accumulates its verdict inside a loop -- appending to a
list an assert then tests -- and the calls that FEED that accumulator are ones the
control never makes. Then there is nothing shared for the control to drive.

**It is calibrated, which is the only reason its flags mean anything.** Run
against `c21c1ba`, before any repair:

    git archive c21c1ba tests | tar -x -C <scratch>
    uv run python tools/screen_controls.py <scratch>/tests

It flags four rows there. Three are the controls then known to be defective --
no false negatives on the known set, which is the property worth having. The
fourth is `test_the_union_check_would_notice_an_unclaimed_entry`, a false
positive from mis-pairing, and it still flags today after restoration settled
that row as connected. So the ratio to expect from a flag is roughly three in
four, and the ratio to expect from a silence is unknown.

An earlier version keyed on inline accumulation alone and false-positived the
moment a repair delegated the comparison but kept the loop. What matters is not
that the check loops; it is whether what it accumulates comes from a function the
control also calls. A repair that removes the loop entirely moves a row from
`clear` to `silent`, which is a loss of signal rather than a gain.

**Read the silence correctly, because it is most of the output.** `clear (no
inline verdict)` means the check does not accumulate in a loop, so this signal
does not apply -- the screen is SILENT about that row, not clearing it. A control
can be disconnected with no loop to inspect. And the check a control guards is
guessed by taking the nearest preceding test, which has been wrong: it read the
neighboring duplicates test as the union control's check and flagged it. Only
restoring the defect settles a row.

Screening is triage. `tools/verify_controls.py` is the audit.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path
from typing import Final

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
REGISTER: Final[Path] = REPO_ROOT / "CONTROL-REGISTER.md"

#: Calls that carry no evidence about which comparison a control drives.
_UNINFORMATIVE: Final[frozenset[str]] = frozenset(
    {
        "sorted",
        "len",
        "set",
        "dict",
        "list",
        "any",
        "all",
        "frozenset",
        "tuple",
        "str",
        "int",
        "print",
        "enumerate",
        "zip",
        "range",
        "min",
        "max",
        "sum",
        "next",
        "iter",
        "repr",
        "ord",
        "chr",
        "isinstance",
        "getattr",
        "open",
        "join",
        "format",
        "strip",
        "split",
        "splitlines",
        "lower",
        "upper",
        "rstrip",
        "lstrip",
        "append",
        "extend",
        "add",
        "get",
        "items",
        "keys",
        "values",
        "count",
        "index",
        "startswith",
        "endswith",
        "replace",
        "relative_to",
        "as_posix",
        "walk",
        "read_text",
        "write_text",
        "glob",
        "search",
        "match",
        "findall",
        "sub",
        "group",
        "is_file",
        "mkdir",
        "exists",
    }
)


def call_names(node: ast.AST) -> set[str]:
    """Every function this subtree calls, by name.

    Attribute calls count by their attribute -- `socket.create_connection` is
    `create_connection`. Counting only bare names is what made an earlier screen
    report `test_the_spy_would_notice_a_connection` as calling nothing at all.
    """
    found: set[str] = set()
    for node_ in ast.walk(node):
        if isinstance(node_, ast.Call):
            function = node_.func
            if isinstance(function, ast.Name):
                found.add(function.id)
            elif isinstance(function, ast.Attribute):
                found.add(function.attr)
    return found - _UNINFORMATIVE


def accumulator_feeders(check: ast.FunctionDef) -> set[str] | None:
    """Calls supplying the value `check` accumulates in a loop and then asserts.

    `None` when the check reaches its verdict some other way, which is this
    screen having no opinion rather than an opinion of `clear`.
    """
    feeders: set[str] = set()
    accumulators: set[str] = set()
    for node in ast.walk(check):
        if not isinstance(node, (ast.For, ast.While)):
            continue
        for inner in ast.walk(node):
            if (
                isinstance(inner, ast.Call)
                and isinstance(inner.func, ast.Attribute)
                and inner.func.attr in {"append", "extend", "add"}
                and isinstance(inner.func.value, ast.Name)
            ):
                accumulators.add(inner.func.value.id)
                for argument in inner.args:
                    feeders |= call_names(argument)
    for node in ast.walk(check):
        if isinstance(node, ast.Assert):
            for name in ast.walk(node.test):
                if isinstance(name, ast.Name) and name.id in accumulators:
                    return feeders
    return None


def registered_controls() -> set[str]:
    return set(re.findall(r"`(test_\w+)`", REGISTER.read_text(encoding="utf-8")))


def main() -> int:
    tests = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / "tests"
    names = registered_controls()
    if not names:
        print("CONTROL-REGISTER.md names no controls; this screen would read nothing")
        return 2

    flagged: list[str] = []
    silent = 0
    rows: list[tuple[str, str, str]] = []
    for path in sorted(tests.glob("test_*.py")):
        functions = [
            node
            for node in ast.parse(path.read_text(encoding="utf-8")).body
            if isinstance(node, ast.FunctionDef)
        ]
        for index, function in enumerate(functions):
            if function.name not in names:
                continue
            check = next(
                (e for e in reversed(functions[:index]) if e.name.startswith("test_")), None
            )
            if check is None:
                rows.append(("silent", function.name, "no preceding test to read as its check"))
                silent += 1
                continue
            feeders = accumulator_feeders(check)
            shared = (feeders or set()) & call_names(function)
            if feeders is None:
                rows.append(("silent", function.name, "check reaches its verdict without a loop"))
                silent += 1
            elif shared:
                rows.append(("clear", function.name, "drives " + ", ".join(sorted(shared))))
            else:
                rows.append(("FLAG", function.name, f"check accumulates in {check.name}"))
                flagged.append(function.name)

    for verdict, name, why in sorted(rows, key=lambda row: {"FLAG": 0, "clear": 1}.get(row[0], 2)):
        print(f"{verdict:<7} {name[:64]:<64} {why}")

    print("\n" + "=" * 78)
    print(f"{len(flagged)} flagged, {len(rows) - len(flagged) - silent} cleared, {silent} silent.")
    print("SILENT IS NOT CLEAR: the signal only applies where a check accumulates in a loop.")
    print("A flag is a suspicion, not a verdict -- the check is guessed by position and has been")
    print("wrong. Settle every row by restoring the defect; see tools/verify_controls.py.")
    return 1 if flagged else 0


if __name__ == "__main__":
    raise SystemExit(main())
