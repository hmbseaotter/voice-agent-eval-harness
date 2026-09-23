#!/usr/bin/env python3
"""Generate the findings review worksheet.

    uv run python tools/make_review_worksheet.py

WHY THIS EXISTS
---------------
D10 makes the findings rows, their classifications and the severity ordering the
human's judgment. That is a validity precondition, not a courtesy: if the gold
set is model-generated, "judge-versus-human agreement" measures a model against
itself and the project's headline result is void.

Adjudicating dozens of candidate rows means holding three documents open at once
-- the candidates, the seeding manifest, and the transcript itself. This
collapses them into one file so the reviewer's attention goes on the judgment
rather than on navigation.

EACH CALL IS RENDERED IN FULL, IN ORDER, BEFORE ITS FINDINGS.
The first version showed only the events a finding happened to cite -- five
scattered lines out of thirty, in the order the findings mentioned them rather
than the order they occurred. A reviewer asked, reasonably, what happened before
line 13 and whether anything happened after line 17. Neither question was
answerable from the page, and a finding cannot be judged against a fragment: the
question "should the agent have said this?" depends on everything that came
first.

So the call record, the context record and the whole event stream are laid out
in sequence at the top of each call's section, and the findings follow.

It lives in `tools/` rather than `src/harness/` on purpose. It is scaffolding
for a human step in phase 1, not a capability of the harness, and a reader
should be able to tell those apart from the directory alone.

WHAT IT DELIBERATELY DOES NOT DO
--------------------------------
It does not pre-tick anything. Every proposed classification is rendered as a
proposal beside an unticked row of alternatives, because a worksheet that
defaults to the model's answer collects agreement rather than judgment -- and
agreement collected that way is indistinguishable, afterwards, from the model
having assigned the label itself.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Final

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from harness.core.findings import DetectableBy, Finding, Owner, Tier, load_findings
from harness.extract import main as extract_main

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
CANDIDATES: Final[Path] = REPO_ROOT / "corpus" / "findings.candidates.yaml"
MANIFEST: Final[Path] = REPO_ROOT / "corpus" / "seeding-manifest.md"
ARTIFACT: Final[Path] = REPO_ROOT / "build" / "extraction-artifact.json"
OUT: Final[Path] = REPO_ROOT / "corpus" / "findings.review-worksheet.md"

_EVENT_REF: Final[re.Pattern[str]] = re.compile(r"\bevents?\s+(\d+)")


def _escape_cell(text: str) -> str:
    """Markdown table cells cannot hold a raw pipe or newline.

    W29 is this defect measured: model text interpolated into report tables
    unescaped, with the shipped report already carrying corrupted rationale
    tails that nothing detected.
    """
    return text.replace("|", "\\|").replace("\n", " ")


def _clock(milliseconds: int) -> str:
    minutes, rest = divmod(milliseconds, 60_000)
    seconds, millis = divmod(rest, 1000)
    return f"{minutes}:{seconds:02d}.{millis:03d}"


def _load_artifact() -> dict[str, dict[str, Any]]:
    """call_id -> the whole extracted call.

    Read from the frozen artifact rather than re-parsed from the transcript, so
    the text a reviewer reads is the text the harness actually extracted. If
    those ever diverge, the reviewer is adjudicating something the harness will
    never see. That reason is why the missing-artifact case **builds** it rather
    than falling back to re-parsing: a fallback path would be a second way to
    produce the worksheet, and the two could disagree exactly when it mattered.

    Building it here rather than telling the caller to run extraction first is
    the fix for a real break. `build/` is gitignored, and the test that runs
    this tool with `--check` therefore passed on every machine that had already
    run extraction and failed on a fresh clone -- including CI, which ran the
    test suite before the extraction step. A dependency satisfied only by
    yesterday's command is not a dependency anyone can see.
    """
    if not ARTIFACT.is_file():
        print(f"{_display(ARTIFACT)} is missing; extracting", file=sys.stderr)
        if extract_main([]) != 0:
            raise SystemExit("extraction failed; cannot render the worksheet")
    document = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    return {str(call["call"]["call_id"]): call for call in document["calls"]}


def _display(path: Path) -> str:
    """Repo-relative where possible, so the message is the same on every machine."""
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def _manifest_rows() -> dict[str, str]:
    """call_id -> its row from the seeding manifest's per-call table.

    Raises if the table cannot be found. The previous version silently rendered
    nothing when the manifest's headings changed shape -- a generator quietly
    producing less, with no error and no warning, which is precisely the failure
    this project keeps writing checks against.
    """
    text = MANIFEST.read_text(encoding="utf-8")
    rows = {
        match.group(1): match.group(0).strip()
        for match in re.finditer(r"^\|\s*\*\*(CALL-\d{2})\*\*\s*\|.*$", text, re.MULTILINE)
    }
    if not rows:
        raise SystemExit(
            f"{MANIFEST} has no per-call rows matching `| **CALL-NN** | … |`. The worksheet "
            "will not silently render without them: a reviewer judging a finding without the "
            "seeding intent in front of them is doing a different job."
        )
    return rows


def _render_call_in_full(call_id: str, call: dict[str, Any], manifest_row: str | None) -> list[str]:
    record = call["call"]
    lines: list[str] = [f"## {call_id}", ""]

    if manifest_row:
        cells = [cell.strip() for cell in manifest_row.strip("|").split("|")]
        if len(cells) >= 3:
            lines += [f"**Scenario.** {cells[1]}", "", f"**Seeded.** {cells[2]}", ""]

    lines += ["<details open>", "<summary><b>The call, in full</b></summary>", ""]

    lines += ["**Call record**", "", "| field | value |", "|---|---|"]
    for key, value in record.items():
        lines.append(f"| `{key}` | {_escape_cell(str(value))} |")
    lines.append("")

    lines += [
        "**Context — everything the agent could see before it spoke**",
        "",
        "| name | value |",
        "|---|---|",
    ]
    if call["context"]:
        for name, value in call["context"]:
            lines.append(f"| `{name}` | {_escape_cell(str(value))} |")
    else:
        lines.append("| *(none)* | The agent was given nothing at call start. |")
    lines.append("")

    lines += [
        "**Event stream — every event, in order**",
        "",
        "| # | start | end | kind | cite | body |",
        "|---|---|---|---|---|---|",
    ]
    for event in call["events"]:
        lines.append(
            f"| {event['index']} "
            f"| {_clock(int(event['started_at_ms']))} "
            f"| {_clock(int(event['ended_at_ms']))} "
            f"| `{event['kind']}` "
            f"| `{event['citation_id']}` "
            f"| {_escape_cell(str(event['body']))} |"
        )
    lines.append("")

    if call["unparsed"]:
        lines += ["**Unparsed lines**", ""]
        for line in call["unparsed"]:
            lines.append(f"- line {line['line_number']}: {line['reason']}")
        lines.append("")

    lines += ["</details>", "", "---", ""]
    return lines


def _cited_events(finding: Finding) -> tuple[int, ...]:
    seen: list[int] = []
    for fragment in finding.evidence:
        for match in _EVENT_REF.finditer(fragment):
            index = int(match.group(1))
            if index not in seen:
                seen.append(index)
    return tuple(seen)


def _render_finding(finding: Finding, events: dict[tuple[str, int], tuple[str, str]]) -> list[str]:
    lines: list[str] = [f"### {finding.id} · {finding.call_ref}", ""]

    lines += ["**Observation** — *drafted; reword freely*", "", f"> {finding.observation}", ""]

    lines += ["**Evidence** — *drafted*", ""]
    for position, fragment in enumerate(finding.evidence, start=1):
        lines.append(f"{position}. {fragment.replace(chr(10), ' ')}")
    lines.append("")

    cited = _cited_events(finding)
    if cited:
        listed = ", ".join(str(index) for index in sorted(cited))
        lines += [
            f"*Cites events {listed} — the full stream is at the top of this call's section.*",
            "",
        ]
        for index in sorted(cited):
            entry = events.get((finding.call_ref, index))
            if entry is None:
                lines.append(f"- **{index}: no such event in {finding.call_ref}**")
                continue
            kind, body = entry
            lines.append(f"- **{index}** `{kind}` — {body}")
        lines.append("")

    lines += ["**Consequence** — *drafted*", "", f"> {finding.consequence}", ""]

    # Every box is UNTICKED, including the proposed one. The proposal is visible
    # in its own column; pre-ticking it would collect agreement rather than
    # judgment, and agreement collected that way is indistinguishable afterwards
    # from the model having assigned the label itself.
    owner = " ".join(f"`[ ]` {member.value}" for member in Owner)
    detectable = " ".join(f"`[ ]` {member.value}" for member in DetectableBy)
    tier = " ".join(f"`[ ]` {member.value}" for member in Tier)
    lines += [
        "**Classifications — proposed, yours to set**",
        "",
        "| field | proposal | your call |",
        "|---|---|---|",
        f"| `owner` | `{finding.owner.value}` | {owner} |",
        f"| `detectable_by` | `{finding.detectable_by.value}` | {detectable} |",
        f"| `tier` | `{finding.tier.value}` | {tier} |",
        "",
        "**Verdict** — `[ ]` accept as written · `[ ]` accept with edits · `[ ]` reject",
        "",
        "**Your wording / notes**",
        "",
        "```",
        "",
        "```",
        "",
    ]
    return lines


def _unruled() -> list[str]:
    """Draft ids with no ruling in the ledger, in document order.

    The preamble used to open "Every row is **drafted and unadjudicated**" as a
    literal, and went on saying it after all 89 rows had been ruled -- in the one
    document whose whole purpose is to show what still needs judging. A reader
    opening it to answer "is anything left?" was told yes by a sentence that had
    stopped being true.
    """
    import yaml

    ledger = REPO_ROOT / "corpus" / "findings.adjudication.yaml"
    if not ledger.is_file():
        return [finding.id for finding in load_findings(CANDIDATES)]
    document = yaml.safe_load(ledger.read_text(encoding="utf-8"))
    rows = document["rulings"] if isinstance(document, dict) and "rulings" in document else document
    if isinstance(rows, dict):
        rows = next(iter(rows.values()))
    ruled = {str(row["id"]) for row in rows}
    return [finding.id for finding in load_findings(CANDIDATES) if finding.id not in ruled]


def _next_step() -> list[str]:
    """The gold set exists or it does not, and `cj` is blocked or it is not.

    Both were stated as literals: "It does not exist until then, deliberately"
    survived the gold set being generated, and "Do not run `cj` before this is
    finished" survived adjudication finishing -- turning a live instruction into
    a stale one in the same paragraph that had already stopped being true.
    """
    outstanding = _unruled()
    gold = REPO_ROOT / "corpus" / "findings.yaml"
    if outstanding or not gold.is_file():
        return [
            "When you are done, the decisions become `corpus/findings.yaml`, the gold set.",
            "It does not exist until then, deliberately.",
            "",
            "**Do not run `cj` before this is finished.** The scoring tool detects findings text",
            "that has moved under judgments already made, and accepting a revision appends to the",
            "comparison log — which changes the log hash the severity file names. Adjudicate",
            "first, score once.",
        ]
    return [
        "**`corpus/findings.yaml` exists**, generated from the drafts and the ledger. Adjudication",
        "is complete, so the condition that blocked scoring is discharged: the findings text will",
        "not move under judgments already made.",
        "",
        "**Scoring with `cj` is the next step, and it happens once.** Re-scoring reworded text",
        "appends a revision acceptance to the comparison log, which changes the log hash the",
        "severity file names.",
    ]


def _adjudication_state() -> list[str]:
    """What the reader actually needs to know: is anything left to rule on?"""
    outstanding = _unruled()
    if not outstanding:
        return [
            "**Every row here has been adjudicated.** `corpus/findings.adjudication.yaml` carries",
            "a ruling for every draft, each with the reasoning behind it, and the gold set",
            "is generated from the two. **Nothing on this page is waiting for a decision** — it is",
            "now a reading view of the corpus with its findings in place, kept because a finding",
            "still cannot be judged against a fragment.",
            "",
            "To change a ruling, edit the ledger and regenerate; to change a row's wording, edit",
            "`corpus/findings.candidates.yaml` unless the ledger carries replacement text for that",
            "row, in which case the ledger wins.",
        ]
    return [
        f"**{len(outstanding)} of {len(load_findings(CANDIDATES))} rows are still unadjudicated**: "
        + ", ".join(outstanding[:12])
        + ("…" if len(outstanding) > 12 else "")
        + ". The `owner`, `detectable_by` and `tier`",
        "values on them are proposals, filled in because the schema requires them and an empty",
        "field cannot be reviewed — not because they are decided. D10 makes those and the row",
        "text your judgment, because a gold set generated by a model would make",
        "*judge-versus-human agreement* measure a model against itself.",
        "",
        "For each: rule on the wording, tick an `owner`, a `detectable_by` and a `tier`, and mark",
        "a verdict. **Rejecting a row is a real option and a useful signal** — a drafted finding",
        "that does not survive review is information about the corpus.",
    ]


def main(*, check: bool = False, out: Path | None = None) -> int:
    findings = load_findings(CANDIDATES)
    calls = _load_artifact()
    manifest = _manifest_rows()

    events: dict[tuple[str, int], tuple[str, str]] = {
        (call_id, int(event["index"])): (str(event["kind"]), str(event["body"]))
        for call_id, call in calls.items()
        for event in call["events"]
    }

    lines: list[str] = [
        "# Findings review worksheet",
        "",
        "*Generated by `tools/make_review_worksheet.py`. A working document, not an artifact of",
        "the project — scaffolding for the one phase-1 step a model must not do.*",
        "",
        "## How to use this",
        "",
        "Each call is laid out **in full and in order** — the call record, everything the",
        "agent could see before it spoke, and every event — and its findings follow. A",
        "finding cannot be judged against a fragment: whether the agent should have said",
        "something depends on everything that came before it.",
        "",
        *_adjudication_state(),
        "",
        "`corpus/seeding-manifest.md` Part 1 lists the **true negatives**: behavior that is",
        "deliberately correct, which no check may fire on. Worth reading before ruling on",
        "anything.",
        "",
        *_next_step(),
        "",
        "---",
        "",
    ]

    by_call: dict[str, list[Finding]] = {}
    for finding in findings:
        by_call.setdefault(finding.call_ref, []).append(finding)

    for call_id in sorted(by_call):
        call = calls.get(call_id)
        if call is None:
            lines += [f"## {call_id}", "", f"**No extracted call for {call_id}.**", "", "---", ""]
        else:
            lines += _render_call_in_full(call_id, call, manifest.get(call_id))
        for finding in by_call[call_id]:
            lines += _render_finding(finding, events)
            lines += ["---", ""]

    rendered = "\n".join(lines).rstrip("\n") + "\n"
    # The worksheet is no longer committed (D76): its purpose was discharged
    # when the last ruling landed, and a 221KB derived file nothing reads is a
    # staleness surface rather than a deliverable. The generator stays, so the
    # second human reader the project still owes can render it on demand.
    destination = out or OUT
    where = (
        destination.relative_to(REPO_ROOT).as_posix()
        if destination.is_relative_to(REPO_ROOT)
        else str(destination)
    )

    if check:
        if not destination.is_file():
            print(f"{where} has never been generated", file=sys.stderr)
            return 1
        if destination.read_text(encoding="utf-8") != rendered:
            print(f"{where} is stale; regenerate it", file=sys.stderr)
            return 1
        print(f"{where} is current")
        return 0

    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(rendered)
    print(
        f"wrote {where} — "
        f"{len(findings)} findings across {len(by_call)} calls, each rendered in full"
    )
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render the findings review worksheet.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 if the worksheet at the output path differs from what would be generated",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="where to write it; defaults to corpus/findings.review-worksheet.md, which is "
        "gitignored because the worksheet is rendered on demand rather than committed",
    )
    _args = parser.parse_args()
    raise SystemExit(main(check=_args.check, out=_args.out))
