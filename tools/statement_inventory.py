#!/usr/bin/env python3
"""Every identifier a document names, resolved against the thing it names.

    uv run python tools/statement_inventory.py

WHY THIS EXISTS
---------------
Four reading sweeps happened before this was written, and each found what it
looked at. Two of them never opened the review worksheet, whose preamble had
been telling readers that *"every row is drafted and unadjudicated"* for two
days after the last of 89 rulings landed.

The lesson was not "sweep again". It was that one mechanical class-check --
"every `test_*` named in prose must exist" -- found a live defect in a Rule line
in two minutes, after a full suite and two sweeps had passed over it. So this
enumerates the classes where a statement names something that either resolves or
does not, and reports the ones that do not.

WHAT IT DOES NOT DO
-------------------
It does not read prose for truth. "The corpus demonstrates a minimal
verification mechanism" is a claim no script settles, and roughly 200 existence
claims in these documents are of that kind. The honest output of an inventory
is partly the list of what it cannot check, which is why that is said here
rather than left implied.

RECORDS NAME THINGS THAT NO LONGER EXIST, AND THAT IS CORRECT
-------------------------------------------------------------
The decision record describes states the project has since left -- a file that
existed then, a test since renamed. D53 is explicit that a record edited to
agree with later decisions stops being a record, so `--live-only` (the default)
skips the decision record's own historical prose for path checks. Run with
`--all` to see those too.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Final

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from harness.core.findings import load_findings

REPO_ROOT = Path(__file__).resolve().parents[1]
DECISIONS = REPO_ROOT / "specs" / "voice-agent-eval-harness.decisions.md"
SPEC = REPO_ROOT / "specs" / "voice-agent-eval-harness.md"

#: Written as a shape rather than a path, so it names no file.
_PLACEHOLDERS = {"corpus/transcripts/CALL-NN.txt"}

#: Artifacts the project has committed to producing and has not produced yet.
#: The `in scope` section names deliverables, so a path there is a promise
#: rather than a reference, and a checker that cannot tell the two apart would
#: force the specification to stop naming what it intends to build.
#:
#: Deliberately a short list with a reason each, on the same argument the corpus
#: checks make about their own exception lists: an exemption nobody has to
#: justify is one that grows. **An entry here is removed when the artifact
#: lands**, and the check then holds it like any other path.
_PLANNED: dict[str, str] = {
    # Empty, and correctly so. corpus/findings.severity.json landed on 2026-09-05
    # and the excuse expired the same run -- which is the mechanism working, not a
    # gap. The next entry here should be removed the same way.
}

_CLAUSE = re.compile(r"^\s*\*\*(?P<id>\d+\.\d+)\*\*", re.MULTILINE)

#: A document named by bare filename, with any line reference dropped:
#: `HOLDOUT-OBLIGATIONS.md`, `sessions/AUDIT-2026-09-07-phase-2.md:142`. The
#: capital start is the convention these documents are named under and keeps the
#: pattern off prose. Added on 2026-09-08 (D120): six continuity documents moved
#: from the root into `sessions/`, breaking seven live pointers, and **nothing in the
#: tree read a document name as something that had to resolve** -- the path check
#: below has always required a directory prefix, which a root document has none
#: of. The move is what made the class visible; the class predates it.
_DOCUMENT = re.compile(r"`([A-Z][A-Za-z0-9._-]*\.md)(?::[\d,]+)?`")


def _live_prose(path: Path, text: str) -> str:
    """The part of a document that claims something about the project *now*.

    Two documents are dated by construction, and the recall net over in
    `tests/test_document_counts.py` excludes exactly these two for exactly this
    reason: the specification's changelog describes states the project has left,
    and D53 settled that a record edited to agree with later decisions stops
    being a record. `HOLDOUT-REPAIR-BRIEF.md` without its folder is a true
    statement in three decision entries and two changelog entries, because that
    is where the file was when they were written.
    """
    if path == DECISIONS:
        return ""
    if path == SPEC:
        return text.partition("## changelog")[0]
    return text


#: Directories whose Markdown this tool reads, beside the repository root. Named
#: rather than walked, because a walk would pull in the held-out packet and the
#: build tree; asserted to exist, because this function fails *open* -- a folder
#: it does not read contributes no citations, and a resolver reading nothing
#: reports nothing unresolved. `sessions/` joined on 2026-09-08 with the six
#: continuity documents that left the root (D120), and the set it reads is the
#: same set it read the day before.
_DOCUMENT_DIRS: Final[tuple[str, ...]] = ("specs", "corpus", "sessions")


def _documents() -> list[Path]:
    found = list(REPO_ROOT.glob("*.md"))
    for folder in _DOCUMENT_DIRS:
        directory = REPO_ROOT / folder
        assert directory.is_dir(), (
            f"{folder}/ is named here and is not a directory; its documents would be "
            "skipped and every identifier they cite would go unresolved in silence"
        )
        found += list(directory.glob("*.md"))
    return sorted(found)


def _clause_ids(policy: Path) -> set[str]:
    """The policy documents number clauses in bold, not in headings.

    The first version of this tool read `## N.N` headings, found none, and
    reported all 25 clause citations in the project as unresolved. A checker
    whose extraction is wrong does not report nothing -- it reports everything,
    which is the more dangerous failure of the two.
    """
    return set(_CLAUSE.findall(policy.read_text(encoding="utf-8")))


def inventory(*, live_only: bool = True) -> dict[str, list[str]]:
    findings = {f.id for f in load_findings(REPO_ROOT / "corpus" / "findings.yaml")}

    def _declared(path: Path) -> set[str]:
        return {
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        }

    design = _declared(REPO_ROOT / "corpus" / "DESIGN_SET")
    # Was `{f"CALL-{n}" for n in range(13, 18)}` until 2026-09-06. A contiguous
    # range is the wrong shape for a set that is not contiguous and can grow:
    # CALL-21 joined the held-out set, CALL-18 to CALL-20 are design calls in
    # between, and this line silently rejected the new id as belonging to
    # neither set. Declared in a file now, for the same reason DESIGN_SET is.
    held_out = _declared(REPO_ROOT / "HELDOUT_SET")
    numbers = sorted(
        int(n) for n in re.findall(r"^## D(\d+) —", DECISIONS.read_text("utf-8"), re.M)
    )
    highest = numbers[-1]
    clauses = {p.stem: _clause_ids(p) for p in (REPO_ROOT / "corpus" / "policies").glob("*.md")}

    found: dict[str, list[str]] = {}

    def note(kind: str, item: str) -> None:
        found.setdefault(kind, []).append(item)

    for path in _documents():
        text = path.read_text(encoding="utf-8")
        name = path.name
        live = _live_prose(path, text) if live_only else text

        for ref in set(
            re.findall(r"`((?:src|tests|tools|corpus|specs|sessions|hooks)/[\w./-]+)`", live)
        ):
            if ref in _PLACEHOLDERS or ref in _PLANNED:
                continue
            if not (REPO_ROOT / ref).exists():
                note("path does not exist", f"{name}: {ref}")

        # A bare name resolves beside the document that writes it, or at the
        # root -- which is how a reader follows it, and how the documents inside
        # `sessions/` go on naming each other without a prefix.
        for ref in set(_DOCUMENT.findall(live)):
            if ref in _PLANNED:
                continue
            if not ((path.parent / ref).exists() or (REPO_ROOT / ref).exists()):
                note("document does not exist", f"{name}: {ref}")

        for ref in set(re.findall(r"\bF-(\d{2})\b", text)):
            if f"F-{ref}" not in findings:
                note("finding id not in the gold set", f"{name}: F-{ref}")

        for ref in set(re.findall(r"\bCALL-(\d{2})\b", text)):
            if f"CALL-{ref}" not in design and f"CALL-{ref}" not in held_out:
                note("call id is neither design nor held-out", f"{name}: CALL-{ref}")

        # "Numbering continues from **D76**" names the next number, not a decision.
        for match in re.finditer(r"\bD(\d{1,3})\b(?!\.)", text):
            start = max(0, match.start() - 40)
            if "continues from" in text[start : match.start()]:
                continue
            if int(match.group(1)) > highest:
                note("decision reference past the record", f"{name}: D{match.group(1)}")

        for doc, clause in set(re.findall(r"\b(\w+\.v\d)\s*§\s*(\d+\.\d+)", text)):
            if doc not in clauses:
                note("policy document does not exist", f"{name}: {doc}")
            elif clause not in clauses[doc]:
                note("policy clause does not exist", f"{name}: {doc} § {clause}")

        for ref in set(re.findall(r"\btaxonomy (\d{1,2})\b", text)):
            if not 1 <= int(ref) <= 35:
                note("taxonomy item out of range", f"{name}: taxonomy {ref}")

    for planned, reason in _PLANNED.items():
        assert reason.strip(), f"{planned} is excused with no reason given"
        if (REPO_ROOT / planned).exists():
            note(
                "planned artifact now exists; remove it from _PLANNED",
                f"{planned} — excused as: {reason}",
            )

    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--all",
        action="store_true",
        help="also check paths inside the decision record, which legitimately names files "
        "that existed when an entry was written",
    )
    args = parser.parse_args(argv)

    found = inventory(live_only=not args.all)
    if not found:
        print("every identifier named in prose resolves")
        return 0
    for kind, items in sorted(found.items()):
        print(f"\n{kind.upper()}  ({len(items)})", file=sys.stderr)
        for item in sorted(set(items)):
            print(f"   {item}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
