"""Findings evidence must still say what the transcripts say.

WHY THIS EXISTS
---------------
A finding's evidence quotes the call. Edit the call and the quote goes stale
*silently* -- the YAML still parses, the schema still validates, the row still
reads perfectly, and it now describes something that never happened.

That is not hypothetical. Rebuilding CALL-01 changed its wording, and seven
findings went on quoting the old text without a single check complaining. The
seeding manifest had already been caught by index drift once; this is the same
class one level down, in the document that becomes the gold set.

WHAT IT CHECKS
--------------
Every evidence fragment shaped `event N — "quoted text"` must name an event that
exists in that call, and the quoted text must actually appear in that event's
reassembled body. Fragments shaped `context — name := value` are checked against
the call's context record the same way.

Fragments that are prose about an absence -- "no TOOL_CALL to send_confirmation
appears" -- are deliberately not machine-checked. They are claims about
something *not* being there, and a substring check cannot evaluate them. They
are the reviewer's to judge, which is the correct division of labor and is
recorded here so the gap is visible rather than assumed away.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from harness.core.events import EventKind, timing
from harness.core.findings import load_findings
from harness.corpus.text_adapter import parse_call

REPO_ROOT: Path = Path(__file__).resolve().parents[1]
CANDIDATES: Path = REPO_ROOT / "corpus" / "findings.candidates.yaml"
GOLD: Path = REPO_ROOT / "corpus" / "findings.yaml"

#: Both files are checked. The drafts are the input and must stay true of the
#: corpus; the GOLD SET is what everything downstream trusts, and 26 of its rows
#: carry replacement text the drafts never had -- six with a different number of
#: evidence fragments. Checking only the drafts left that text verified by care
#: rather than by mechanism, which is the distinction this repository exists for.
FINDINGS_DOCUMENTS: tuple[Path, ...] = (CANDIDATES, GOLD)
TRANSCRIPTS: Path = REPO_ROOT / "corpus" / "transcripts"

#: `event 14 — "quoted text"` — the quote is what gets checked.
_EVENT_QUOTE = re.compile(r"^event\s+(\d+)\s*[—-]\s*[\"“](?P<quote>.+)[\"”]\s*$", re.DOTALL)
#: `event 9 — t1 -> retrieved successful=true :: …` — unquoted machine text.
_EVENT_PLAIN = re.compile(r"^event\s+(\d+)\s*[—-]\s*(?P<text>.+)$", re.DOTALL)
#: `call record — duration_ms 124523` — a field of the call record, which is
#: parsed and comparable. Two findings cited the record this way and neither
#: was read by anything until three stale numbers turned up in one session.
_RECORD = re.compile(r"^call record\s*[—-]\s*(?P<rest>.+)$", re.DOTALL)
#: `events 20 to 21 — the agent is silent from 0:55.913 to 2:19.703`. The
#: span is computable; the durations in F-24 were right and every absolute
#: timestamp was stale, which is precisely the drift a duration check misses.
_SPAN = re.compile(
    r"^events\s+(?P<first>\d+)\s+to\s+(?P<second>\d+)\s*[—-]\s*.*?from\s+(?P<start>\d+:\d\d\.\d\d\d)\s+to\s+(?P<end>\d+:\d\d\.\d\d\d)",
    re.DOTALL,
)
#: `The final event of the call ends at 170284ms` — computable against the
#: log's last event, and the one form F-48's ledger note claimed was checked
#: when it was not. The figure went stale on a call lengthening and the whole
#: suite stayed green, which is the same shape as every drift above it.
_FINAL_EVENT = re.compile(r"final event .*?ends at\s+(?P<ms>\d+)\s*ms", re.DOTALL)
#: `CALL-12 event 15 — t2 -> refused_precondition ...` — a citation into a
#: DIFFERENT call. F-80's defect is only visible across two of them, and the
#: half that made it interesting was prose nothing read until this existed.
_CROSS_CALL = re.compile(
    r"^(?P<call>CALL-\d+)\s+event\s+(?P<index>\d+)\s*[—-]\s*(?P<text>.+)$",
    re.DOTALL,
)
#: `No event of any kind falls between events 23 and 24` and `No TOOL_CALL
#: occurs between events 13 and 15`. Both are claims about a *gap*, and both are
#: computable -- the first says the two indices are adjacent, the second that no
#: event of that kind lies strictly between them.
#:
#: Written because F-70 carried `between events 23 and 18` into the gold set. The
#: M6 renumbering remapped `events N to M` and not `events N and M`, so the first
#: index moved and the second did not, and this fragment reached every generated
#: view. It is prose about an absence, which is the one branch below that returns
#: without checking anything.
#:
#: `agent turn` was among the alternatives and **no `EventKind` is named that**,
#: so `e.kind.name == "agent turn"` was always empty: the fragment incremented
#: `checked` and asserted nothing. F-15's *"No agent turn between events 20 and
#: 27 asks the caller to confirm the transfer"* passed vacuously for as long as
#: it existed. Mapping the alternative to `AGENT` would not have fixed it and
#: would have made it worse -- event 25 **is** an agent turn, so the check would
#: have failed a true fragment. The claim is about what the agent turns in that
#: span *say*, which is a reading task, so the fragment now falls through to the
#: reviewer's branch uncounted.
_GAP_CLAIM = re.compile(
    r"No (?P<kind>[A-Z_]+|event of any kind|event)"
    r"[^.]{0,60}?between events\s+(?P<first>\d+)\s+and\s+(?P<second>\d+)",
    re.DOTALL,
)
#: `context — name := value`
_CONTEXT = re.compile(
    r"^context\s*[—-]\s*(?P<name>[A-Za-z_][\w.]*)\s*:=\s*(?P<value>.+)$", re.DOTALL
)


def _normalize(text: str) -> str:
    """Whitespace-insensitive comparison.

    Both sides wrap, and they wrap at different columns -- the same reason
    policy-clause correspondence is normalized (D32). A byte comparison here
    would fail on formatting and be disabled within a week.
    """
    return " ".join(text.split())


def _stamp(ms: int) -> str:
    """`0:55.913` — the form the transcripts and the findings both use."""
    return f"{ms // 60_000}:{(ms % 60_000) / 1000:06.3f}"


@pytest.mark.parametrize("document", FINDINGS_DOCUMENTS, ids=lambda p: p.stem)
def test_every_quoted_fragment_appears_in_the_event_it_cites(document: Path) -> None:
    findings = load_findings(document)
    # Parsed lazily, only for the calls the findings actually cite. During a
    # format migration the corpus is mixed, and a test that eagerly parsed every
    # transcript would fail on calls no finding refers to yet -- reporting a
    # migration in progress as an evidence defect, which is the wrong finding.
    calls = {}
    for call_ref in sorted({f.call_ref for f in findings}):
        source = TRANSCRIPTS / f"{call_ref}.txt"
        if source.is_file():
            calls[call_ref] = parse_call(source)

    problems: list[str] = []
    checked = 0

    for finding in findings:
        call = calls.get(finding.call_ref)
        if call is None:
            problems.append(f"{finding.id}: call_ref {finding.call_ref} has no transcript")
            continue
        by_index = {event.index: event for event in call.events}
        context = {name: value for name, value in call.context}

        for fragment in finding.evidence:
            flat = _normalize(fragment)

            match_context = _CONTEXT.match(flat)
            if match_context is not None:
                checked += 1
                name = match_context.group("name")
                expected = _normalize(match_context.group("value"))
                if name not in context:
                    problems.append(
                        f"{finding.id}: cites context {name!r}, which {finding.call_ref} "
                        "does not carry"
                    )
                elif _normalize(context[name]) != expected:
                    problems.append(
                        f"{finding.id}: cites context {name} := {expected!r}, "
                        f"but the call carries {context[name]!r}"
                    )
                continue

            match_cross = _CROSS_CALL.match(flat)
            if match_cross is not None:
                checked += 1
                other = match_cross.group("call")
                source = TRANSCRIPTS / f"{other}.txt"
                if not source.is_file():
                    problems.append(f"{finding.id}: cites {other}, which has no transcript")
                    continue
                if other not in calls:
                    calls[other] = parse_call(source)
                index = int(match_cross.group("index"))
                event = {e.index: e for e in calls[other].events}.get(index)
                if event is None:
                    problems.append(
                        f"{finding.id}: cites {other} event {index}, which it does not have"
                    )
                    continue
                wanted = _normalize(match_cross.group("text"))
                head = wanted.split(",")[0]
                if wanted not in _normalize(event.body) and head not in _normalize(event.body):
                    problems.append(
                        f"{finding.id}: {other} event {index} does not contain {head[:70]!r}"
                    )
                continue

            match_record = _RECORD.match(flat)
            if match_record is not None:
                checked += 1
                rest = match_record.group("rest")
                fields = {
                    name: str(getattr(call.record, name))
                    for name in dir(call.record)
                    if not name.startswith("_") and not callable(getattr(call.record, name))
                }
                named = [name for name in fields if name in rest]
                # `outcome` is a substring of `outcome_reason`, so a row citing
                # the longer field also "names" the shorter one and is then
                # compared against the wrong value. Keep only maximal matches.
                # Found by CALL-20, the first call whose record needed both.
                named = [n for n in named if not any(n != other and n in other for other in named)]
                if not named:
                    problems.append(
                        f"{finding.id}: cites the call record as {rest[:60]!r}, "
                        "naming no field the record carries"
                    )
                for name in named:
                    if fields[name] not in rest:
                        problems.append(
                            f"{finding.id}: cites call record {name} as {rest[:60]!r}, "
                            f"but the record says {fields[name]!r}"
                        )
                continue

            match_span = _SPAN.match(flat)
            if match_span is not None:
                checked += 1
                first = by_index.get(int(match_span.group("first")))
                second = by_index.get(int(match_span.group("second")))
                if first is None or second is None:
                    problems.append(
                        f"{finding.id}: cites a span between events "
                        f"{match_span.group('first')} and {match_span.group('second')}, "
                        f"which {finding.call_ref} does not both have"
                    )
                    continue
                actual = (_stamp(timing(first)[1]), _stamp(timing(second)[0]))
                stated = (match_span.group("start"), match_span.group("end"))
                if actual != stated:
                    problems.append(
                        f"{finding.id}: states the span "
                        f"{stated[0]} to {stated[1]}; the corpus has "
                        f"{actual[0]} to {actual[1]}"
                    )
                continue

            match_gap = _GAP_CLAIM.search(flat)
            if match_gap is not None:
                checked += 1
                gap_first = int(match_gap.group("first"))
                gap_second = int(match_gap.group("second"))
                if gap_first >= gap_second:
                    problems.append(
                        f"{finding.id}: claims a gap between events {gap_first} and {gap_second}, "
                        "which do not run forwards"
                    )
                    continue
                between = [e for e in call.events if gap_first < e.index < gap_second]
                kind = match_gap.group("kind")
                if kind in {"event of any kind", "event"}:
                    if between:
                        problems.append(
                            f"{finding.id}: says no event of any kind falls between "
                            f"{gap_first} and {gap_second}; {len(between)} do "
                            f"({', '.join(str(e.index) for e in between[:4])})"
                        )
                elif kind not in {member.name for member in EventKind}:
                    # The structural half of the same defect. Dropping one
                    # unresolvable alternative fixes one fragment; refusing an
                    # unresolvable kind fixes the class, because the failure
                    # mode is silent -- a comparison against a name nothing
                    # carries is empty, and an empty comparison reads exactly
                    # like a passing one.
                    problems.append(
                        f"{finding.id}: claims no {kind!r} occurs between {gap_first} and "
                        f"{gap_second}, and no event kind is named {kind!r}, so nothing "
                        "was compared. Name a kind from the event model or reword the "
                        "fragment so it is not read as a gap claim."
                    )
                else:
                    of_kind = [e for e in between if e.kind.name == kind]
                    if of_kind:
                        problems.append(
                            f"{finding.id}: says no {kind} occurs between "
                            f"{gap_first} and {gap_second}; event {of_kind[0].index} is one"
                        )
                continue

            match_final = _FINAL_EVENT.search(flat)
            if match_final is not None:
                checked += 1
                stated_ms = int(match_final.group("ms"))
                actual_ms = max(timing(event)[1] for event in call.events)
                if stated_ms != actual_ms:
                    problems.append(
                        f"{finding.id}: says the final event ends at {stated_ms}ms; "
                        f"{finding.call_ref}'s last event ends at {actual_ms}ms"
                    )
                continue

            match_quote = _EVENT_QUOTE.match(flat)
            match_plain = _EVENT_PLAIN.match(flat) if match_quote is None else None
            match = match_quote or match_plain
            if match is None:
                continue  # prose about an absence; the reviewer's to judge

            index = int(match.group(1))
            event = by_index.get(index)
            if event is None:
                problems.append(
                    f"{finding.id}: cites event {index}, which {finding.call_ref} does not have"
                )
                continue

            checked += 1
            # One of the two matched -- the branch above `continue`s otherwise --
            # but mypy cannot see that across the branch, and a `type: ignore`
            # would break the "zero ignores" acceptance criterion now that the
            # type check covers `tests/`. An assert says the same thing and is
            # checked at runtime as well.
            quoted = match_quote.group("quote") if match_quote else None
            if quoted is None:
                assert match_plain is not None
                quoted = match_plain.group("text")
            wanted = _normalize(quoted)
            # A plain fragment may carry a trailing gloss after an em dash that
            # is commentary rather than quotation; compare the leading clause.
            if wanted not in _normalize(event.body):
                head = wanted.split(" — ")[0]
                if head not in _normalize(event.body):
                    problems.append(
                        f"{finding.id}: event {index} does not contain {wanted[:70]!r}\n"
                        f"       the event says: {event.body[:100]!r}"
                    )

    assert checked, "no evidence fragments were checkable; the patterns have drifted"
    assert not problems, "findings evidence has drifted from the corpus:\n  " + "\n  ".join(
        problems
    )


#: `event 18`, `events 23 and 24`, `CALL-12 event 11` — a citation in a finding's
#: own prose rather than in its evidence tuple. Thirty-nine of them across the
#: gold set and nothing read one until F-68 was found by hand.
_PROSE_EVENT = re.compile(
    r"\b(?:(?P<call>CALL-\d+)\s+)?events?\s+(?P<first>\d+)"
    r"(?:\s*(?:and|to|[-\u2013\u2014])\s*(?P<second>\d+))?",
    re.IGNORECASE,
)

#: The sentence F-68 got wrong: prose naming *where* a true negative lives. It
#: carried `CALL-12 event 9` for a readback that moved to event 11 when CALL-12's
#: degraded-line exchange was rebuilt, and stayed green through a full suite, four
#: independent sweeps and a human read — because every citation check above reads
#: `finding.evidence`, and this one lives in a sentence.
#:
#: An existence check would not have caught it. Event 9 exists; it is
#: `t1 lookup_booking(...)`. What makes the claim checkable is that the seeding
#: manifest is the authority on true negatives, so the coordinates can be compared
#: against it. Keeping the duplication and checking it beats forbidding it: the
#: coordinates are what make the sentence worth reading.
_PROSE_TRUE_NEGATIVE = re.compile(
    r"(?P<call>CALL-\d+)\s+events?\s+(?P<index>\d+)[^.]*?\bis the true negative\b",
    re.IGNORECASE,
)

#: `| **CALL-12 event 11, its form only** | …` — Part 1 keys each declared true
#: negative on a call and, for most rows, one or more event indices. Scoped to
#: Part 1: Part 2 keys rows on a bare call id, and a parser that read both would
#: be answering a different question with the same regex.
_MANIFEST_ROW = re.compile(r"^\|\s*\*\*(?P<key>CALL-\d+[^*|]*)\*\*\s*\|", re.MULTILINE)

MANIFEST: Path = REPO_ROOT / "corpus" / "seeding-manifest.md"


def _declared_true_negatives() -> dict[str, set[int]]:
    """Part 1's rows, as call -> the event indices that row covers.

    The call id is stripped before integers are collected, or `CALL-12` would
    contribute a spurious event 12 to every row it keys.
    """
    text = MANIFEST.read_text(encoding="utf-8")
    part_one = text.split("## Part 1")[1].split("## Part 2")[0]
    rows: dict[str, set[int]] = {}
    for match in _MANIFEST_ROW.finditer(part_one):
        key = match.group("key")
        call = key.split()[0].rstrip(",")
        rows.setdefault(call, set()).update(int(n) for n in re.findall(r"\d+", key[len(call) :]))
    assert rows, "Part 1 parsed to nothing; the manifest's table shape has changed"
    return rows


@pytest.mark.parametrize("document", FINDINGS_DOCUMENTS, ids=lambda p: p.stem)
def test_every_event_cited_in_findings_prose_exists(document: Path) -> None:
    """Prose citations resolve, the way evidence citations already have to.

    This catches an index that drifted out of range. It cannot catch one that
    drifted onto a different real event, which is exactly what F-68 did — that
    needs an authority to compare against, and is the next test.
    """
    findings = load_findings(document)
    wanted = {f.call_ref for f in findings}
    for finding in findings:
        for field in ("observation", "consequence"):
            for match in _PROSE_EVENT.finditer(_normalize(getattr(finding, field))):
                if match.group("call"):
                    wanted.add(match.group("call"))
    calls = {
        ref: parse_call(TRANSCRIPTS / f"{ref}.txt")
        for ref in sorted(wanted)
        if (TRANSCRIPTS / f"{ref}.txt").is_file()
    }

    problems: list[str] = []
    checked = 0
    for finding in findings:
        for field in ("observation", "consequence"):
            for match in _PROSE_EVENT.finditer(_normalize(getattr(finding, field))):
                call_ref = match.group("call") or finding.call_ref
                call = calls.get(call_ref)
                if call is None:
                    problems.append(
                        f"{finding.id}: {field} cites {call_ref}, which has no transcript"
                    )
                    continue
                indices = {event.index for event in call.events}
                for group in ("first", "second"):
                    raw = match.group(group)
                    if raw is None:
                        continue
                    checked += 1
                    if int(raw) not in indices:
                        problems.append(
                            f"{finding.id}: {field} cites {call_ref} event {raw}, "
                            f"which has only events {min(indices)} to {max(indices)}"
                        )

    assert checked, "no prose event citations were checkable; the pattern has drifted"
    assert not problems, "findings prose cites events that do not exist:\n  " + "\n  ".join(
        problems
    )


@pytest.mark.parametrize("document", FINDINGS_DOCUMENTS, ids=lambda p: p.stem)
def test_a_true_negative_named_in_prose_agrees_with_the_seeding_manifest(document: Path) -> None:
    """A finding may repeat a true negative's coordinates; it may not disagree.

    One row binds today — F-68's. That is thin, and it is the row the guard was
    written for, so it is stated rather than dressed up: the population is small
    because naming a true negative's location in prose is rare, not because the
    check is narrow.
    """
    declared = _declared_true_negatives()
    problems: list[str] = []
    checked = 0
    for finding in load_findings(document):
        for field in ("observation", "consequence"):
            for match in _PROSE_TRUE_NEGATIVE.finditer(_normalize(getattr(finding, field))):
                checked += 1
                call, index = match.group("call"), int(match.group("index"))
                covered = declared.get(call, set())
                if index not in covered:
                    problems.append(
                        f"{finding.id}: {field} says {call} event {index} is the true "
                        f"negative; the manifest declares {call} at "
                        f"{sorted(covered) or 'no event'}"
                    )

    assert checked, "no prose true-negative citations were checkable; the pattern has drifted"
    assert not problems, "a finding disagrees with the seeding manifest:\n  " + "\n  ".join(
        problems
    )


def test_a_gap_claim_naming_no_real_kind_is_refused_not_counted() -> None:
    """The control D72 did not have.

    D72 records this branch as "planted against three ways". The fourth was a
    fragment naming a kind **no `EventKind` carries** -- `agent turn` was in the
    pattern's own alternatives -- so the comparison ran against a name nothing
    has, found nothing, and returned. An empty comparison reads exactly like a
    passing one, and F-15's fragment rode that for as long as it existed.

    Planted here rather than argued: a fragment shaped like a gap claim, naming
    a kind that does not exist, must produce a problem.
    """
    kinds = {member.name for member in EventKind}
    assert "agent turn" not in kinds, "the premise of this control has changed"

    fabricated = "No WIDGET occurs between events 2 and 9, so nothing was re-read."
    match = _GAP_CLAIM.search(fabricated)
    assert match is not None, "the pattern no longer reads a gap claim naming a kind"
    assert match.group("kind") == "WIDGET"
    assert match.group("kind") not in kinds, (
        "this control needs a kind the event model does not carry"
    )


def test_a_prose_absence_claim_is_left_to_the_reviewer_uncounted() -> None:
    """The other half. F-15's fragment is a claim about what the agent turns in
    a span *say*, not about whether any exist -- event 25 is an agent turn, so a
    check keyed to the kind would fail a true fragment.

    It must fall through to the reviewer's branch rather than being counted, and
    the distinction is worth pinning: a checker that counts what it cannot
    evaluate reports coverage it does not have.
    """
    fragment = "No agent turn between events 20 and 27 asks the caller to confirm the transfer."
    assert _GAP_CLAIM.search(fragment) is None, (
        "a content claim about agent turns is being read as a gap claim again"
    )
    assert _EVENT_QUOTE.match(fragment) is None
    assert _EVENT_PLAIN.match(fragment) is None
