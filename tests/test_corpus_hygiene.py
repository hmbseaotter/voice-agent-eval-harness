"""Corpus hygiene: leakage, privacy, and defects nobody meant to seed.

Two jobs, and the second is the one that keeps paying.

**Leakage and privacy.** The specification's P1 criteria require a scan across
all seven substitution classes and an assertion that the corpus holds no real
personal data. A string scan is not enough on its own -- a scenario recognizable
as prior art with the nouns swapped is a leak even when every noun is invented --
so the domain-shape smells are scanned for too.

**Accidental defects.** A hand-authored corpus acquires defects nobody chose,
and an unseeded defect is worse than a missing one: the findings document will
not describe it, so a judge that reports it looks wrong when it is right. Several
of these exist because they caught exactly that -- a header duration that did not
reconcile with its own event log (three times), a timestamp that ran backwards,
and a rescheduled event that contradicted two other calls.

Every seeded exception is named in a constant here and cross-referenced to the
seeding manifest. That is the point: the difference between a seeded defect and
an accident is that somebody wrote the seeded one down.
"""

from __future__ import annotations

import ast
import contextlib
import itertools
import re
import subprocess
import sys
import tempfile
import tokenize
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Final

import pytest
import yaml

from harness.core.events import (
    Call,
    DisclosureEvent,
    DisclosureState,
    DisconnectionReason,
    Event,
    EventKind,
    Outcome,
    PolicyEvent,
    SpeechEvent,
    StateEvent,
    SystemEvent,
    ToolCallEvent,
    ToolResultEvent,
    ToolStatus,
    timing,
)
from harness.core.findings import load_findings
from harness.corpus.policies import parse_policy
from harness.corpus.text_adapter import parse_call

REPO_ROOT: Path = Path(__file__).resolve().parents[1]
CORPUS: Path = REPO_ROOT / "corpus"
TRANSCRIPTS: Path = CORPUS / "transcripts"
POLICIES: Path = CORPUS / "policies"

#: Seeded exceptions, each cross-referenced to corpus/seeding-manifest.md.
DURATION_MISMATCH_SEEDED: Final[frozenset[str]] = frozenset({"CALL-12"})  # taxonomy 32
MISSING_LIFECYCLE_END_SEEDED: Final[frozenset[str]] = frozenset({"CALL-12"})  # taxonomy 32
NAMING_DRIFT_SEEDED: Final[frozenset[str]] = frozenset({"CALL-08"})  # taxonomy 20
CONTRADICTORY_RECORD_SEEDED: Final[frozenset[str]] = frozenset({"CALL-08"})  # P9
AGENT_HANGUP_SEEDED: Final[frozenset[str]] = frozenset({"CALL-05", "CALL-12"})
REASON_CODE_CORRUPTION_SEEDED: Final[frozenset[str]] = frozenset({"CALL-09"})  # F-74

#: Shapes belonging to a different domain. Renaming entities inside one domain
#: leaves scenario shapes recognizable, which is what the boundary protects.
SHAPE_SMELLS: Final[tuple[str, ...]] = (
    "courier",
    "warehouse",
    "restocking",
    "tracking number",
    "in transit",
    "parcel",
    "shipping",
    "postage",
    "depot",
    "dispatched",
    "returned item",
    "delivery window",
)


def _transcripts() -> list[Path]:
    return sorted(TRANSCRIPTS.glob("*.txt"))


#: Authored corpus documents outside `corpus/transcripts/` and `corpus/policies/`.
#: The findings text is corpus content -- it quotes transcripts, names entities
#: and states policy terms -- and it was outside the scan while the acceptance
#: criterion said "repository-wide".
_ALSO_SCANNED: Final[tuple[str, ...]] = (
    "corpus/findings.candidates.yaml",
    "corpus/findings.md",
    "corpus/findings.adjudication.yaml",
    "corpus/findings.yaml",
)

#: Excluded, each for a stated reason. An exclusion list is a hiding place
#: unless every entry has one.
_NOT_SCANNED: Final[tuple[tuple[str, str], ...]] = (
    (
        "corpus/entities.md",
        "metadata *about* the corpus, which necessarily contains the words the "
        "shape-smell scan looks for -- it says in as many words that no carriers, "
        "couriers, warehouses or tracking numbers appear. Scanning it made the "
        "detector fire on the text documenting the property it was checking.",
    ),
    (
        "corpus/seeding-manifest.md",
        "the same shape: it describes what was seeded, in the vocabulary of the "
        "things it describes.",
    ),
    (
        "specs/",
        "the specification states the substitution policy itself, class by class, "
        "and naming a class is not committing it. The criterion's wording is "
        "narrowed to match rather than the scan widened to trip on its own rules.",
    ),
)


def _corpus_text() -> str:
    """Every authored corpus document, with the exclusions declared above.

    This read transcripts and policy documents only, while the acceptance
    criterion it backs says **repository-wide** -- so the findings document, the
    generated view and the review worksheet, all of which quote transcripts and
    name entities, were outside a check cited as covering them. Widening it
    trips nothing, which is the result rather than a reason not to have looked.
    """
    parts = [path.read_text(encoding="utf-8") for path in _transcripts()]
    parts += [path.read_text(encoding="utf-8") for path in sorted(POLICIES.glob("*.md"))]
    for relative in _ALSO_SCANNED:
        path = REPO_ROOT / relative
        assert path.is_file(), f"{relative} is named in the scan and does not exist"
        parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def test_the_leakage_scan_reads_every_authored_corpus_document() -> None:
    """The exclusions have to stay deliberate. A corpus document added under
    `corpus/` and named in neither list is outside the scan and nothing says
    so -- which is how the findings text spent this project's whole life
    unscanned while a criterion described the scan as repository-wide."""
    scanned = {path.relative_to(REPO_ROOT).as_posix() for path in _transcripts()}
    scanned |= {path.relative_to(REPO_ROOT).as_posix() for path in POLICIES.glob("*.md")}
    scanned |= set(_ALSO_SCANNED)
    excluded = {name for name, _ in _NOT_SCANNED if not name.endswith("/")}

    authored = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in (REPO_ROOT / "corpus").rglob("*")
        if path.is_file() and path.suffix in {".txt", ".md", ".yaml"}
    }
    unaccounted = sorted(authored - scanned - excluded)
    assert not unaccounted, (
        "corpus documents in neither the scan nor the declared exclusions:\n  "
        + "\n  ".join(unaccounted)
    )
    for name, reason in _NOT_SCANNED:
        assert reason.strip(), f"{name} is excluded with no reason given"


# --------------------------------------------------------------------------
# Leakage: the domain boundary, not only the strings
# --------------------------------------------------------------------------


@pytest.mark.parametrize("smell", SHAPE_SMELLS)
def test_no_shape_from_an_adjacent_domain(smell: str) -> None:
    assert smell not in _corpus_text().lower(), f"{smell!r} belongs to a different domain's shape"


def test_ticketings_own_shapes_are_doing_the_work() -> None:
    """The converse, and the one that would fail if the corpus had been adapted
    rather than authored: the defects must hang off ticketing's own structure."""
    text = _corpus_text().lower()
    for shape in ("door time", "transfer", "exchange", "price band", "resale", "promoter"):
        assert shape in text, f"ticketing shape {shape!r} is absent from the corpus"


# --------------------------------------------------------------------------
# Privacy: reserved ranges only
# --------------------------------------------------------------------------


def test_every_email_address_is_in_the_reserved_domain() -> None:
    found = set(re.findall(r"[\w.+-]+@[\w.-]+\.\w+", _corpus_text()))
    offenders = {e for e in found if not e.lower().endswith("@example.com")}
    assert not offenders, f"email addresses outside the reserved domain: {sorted(offenders)}"


def test_every_telephone_number_is_in_the_reserved_fictional_range() -> None:
    """NANP reserves 555-0100 through 555-0199 for fictional use."""
    found = set(re.findall(r"\+1 \(\d{3}\) (\d{3}-\d{4})", _corpus_text()))
    offenders = {n for n in found if not n.startswith("555-01")}
    assert not offenders, f"telephone numbers outside the reserved range: {sorted(offenders)}"


def test_every_zip_code_is_below_the_lowest_assigned_one() -> None:
    """USPS's lowest assigned ZIP is 00501, so 00000-00499 cannot exist.

    Scanned where ZIP codes actually appear -- `*_zip` context values and
    five-digit tokens in speech -- and NOT across the whole file. A naive
    five-digit scan false-positives on every account id, event id, refund id
    and millisecond duration in the corpus, which is how a check acquires a
    reputation for crying wolf and then gets removed.
    """
    found: set[str] = set()
    for transcript in _transcripts():
        call = parse_call(transcript)
        found.update(v.strip() for name, v in call.context if name.endswith("_zip"))
        for event in call.events:
            if isinstance(event, SpeechEvent):
                # Not preceded by a hyphen: `EV-88011` and `AC-33915` present a
                # word boundary before their digits, so a bare five-digit scan
                # would collect an identifier's tail and report it as a ZIP
                # above 00501. It passes today only because no identifier is
                # spoken as bare digits, which is a property of the corpus and
                # not of the check.
                found.update(re.findall(r"(?<![-\d])(\d{5})(?![-\d])", event.body))
    assert found, "no ZIP codes found at all; the scan has drifted"
    offenders = {z for z in found if not (z.isdigit() and int(z) <= 499)}
    assert not offenders, f"ZIP codes at or above 00501: {sorted(offenders)}"


def test_no_street_address_appears() -> None:
    """A name is not personal data and a ZIP is not personal data; a name with a
    street address frequently is. None appear, so the combination cannot."""
    pattern = re.compile(r"\b\d{1,5}\s+[A-Z][a-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr)\b")
    assert not pattern.search(_corpus_text())


def test_no_payment_card_number_appears() -> None:
    """Instruments are referred to by last four digits only, never in full."""
    assert not re.search(r"\b(?:\d[ -]?){13,19}\b", _corpus_text())


# --------------------------------------------------------------------------
# Accidental defects -- each of these caught one during authoring
# --------------------------------------------------------------------------


@pytest.mark.parametrize("transcript", _transcripts(), ids=lambda p: p.stem)
def test_header_duration_reconciles_with_the_event_log(transcript: Path) -> None:
    call = parse_call(transcript)
    record = call.record
    last = call.events[-1].ended_at_ms
    started = datetime.fromisoformat(record.started_at.replace("Z", "+00:00"))
    ended = datetime.fromisoformat(record.ended_at.replace("Z", "+00:00"))
    # Exact integer arithmetic, not `int(total_seconds() * 1000)`. That form
    # truncates rather than rounds, and 128.159 seconds is 128158.99999999999
    # milliseconds in binary float -- so a header that reconciled perfectly
    # read as one millisecond short and was reported as an unseeded taxonomy
    # 32 defect. Found by CALL-20; every earlier call happened to miss it.
    span = (ended - started) // timedelta(milliseconds=1)

    if record.call_id in DURATION_MISMATCH_SEEDED:
        assert record.duration_ms != last, (
            f"{record.call_id} is listed as a seeded taxonomy 32 mismatch but reconciles; "
            "either the seed was lost or the exception is stale"
        )
        return
    assert record.duration_ms == last == span, (
        f"{record.call_id}: duration {record.duration_ms}ms, last event {last}ms, "
        f"header span {span}ms -- an unseeded taxonomy 32 defect"
    )


@pytest.mark.parametrize("transcript", _transcripts(), ids=lambda p: p.stem)
def test_timestamps_never_run_backwards(transcript: Path) -> None:
    call = parse_call(transcript)
    starts = [timing(event)[0] for event in call.events]
    for index, (earlier, later) in enumerate(itertools.pairwise(starts), start=1):
        assert earlier <= later, (
            f"{call.record.call_id}: event {index + 1} starts before event {index}"
        )


@pytest.mark.parametrize("transcript", _transcripts(), ids=lambda p: p.stem)
def test_every_call_opens_and_closes_its_lifecycle(transcript: Path) -> None:
    call = parse_call(transcript)
    names = [e.name for e in call.events if isinstance(e, SystemEvent)]
    assert "call.answered" in names, f"{call.record.call_id} never logs call.answered"
    if call.record.call_id in MISSING_LIFECYCLE_END_SEEDED:
        assert "call.ended" not in names, (
            f"{call.record.call_id} is listed as a seeded taxonomy 32 omission but does log "
            "call.ended; the exception is stale"
        )
        return
    assert "call.ended" in names, f"{call.record.call_id} never logs call.ended"


@pytest.mark.parametrize("transcript", _transcripts(), ids=lambda p: p.stem)
def test_every_call_opens_with_a_recording_disclosure(transcript: Path) -> None:
    """A California ticketing business transacting by phone records its calls,
    and two-party consent makes the notice a requirement rather than a courtesy.
    Its absence was the first thing a human reviewer noticed about v1."""
    call = parse_call(transcript)
    names = [e.body.split(" ")[0] for e in call.events if e.kind is EventKind.DISCLOSURE]
    assert "recording_notice" in names, f"{call.record.call_id} delivers no recording notice"


def test_agent_hangup_appears_only_where_it_is_seeded() -> None:
    """An agent hanging up seconds after the last word reads as abrupt on voice,
    which is taxonomy 32's "who terminates the interaction" -- so it belongs
    where it is a finding, not as a default."""
    offenders = {
        parse_call(t).record.call_id
        for t in _transcripts()
        if parse_call(t).record.disconnection_reason.value == "agent_hangup"
    }
    assert offenders == set(AGENT_HANGUP_SEEDED), (
        f"agent_hangup in {sorted(offenders)}; seeded in {sorted(AGENT_HANGUP_SEEDED)}"
    )


def test_one_event_title_per_event_id_except_where_drift_is_seeded() -> None:
    """Taxonomy 20 is a constraint before it is a defect: matching spoken names
    against catalog entries needs one canonical name first."""
    canonical: dict[str, set[str]] = {}
    drifted: set[str] = set()
    for transcript in _transcripts():
        call = parse_call(transcript)
        context = dict(call.context)
        event_id = context.get("event_id")
        title = context.get("event_title")
        if not event_id or not title:
            continue
        # A title appearing in a tool result that differs from the context one
        # is drift within the call.
        for event in call.events:
            if (
                isinstance(event, ToolResultEvent)
                and event.detail
                and "title=" in event.detail
                and title not in event.detail
            ):
                drifted.add(call.record.call_id)
        if call.record.call_id not in NAMING_DRIFT_SEEDED:
            canonical.setdefault(event_id, set()).add(title)

    assert drifted == set(NAMING_DRIFT_SEEDED), (
        f"calls carrying naming drift: {sorted(drifted)}; seeded: {sorted(NAMING_DRIFT_SEEDED)}"
    )
    for event_id, titles in canonical.items():
        assert len(titles) == 1, f"{event_id} has no single canonical name: {sorted(titles)}"


def test_a_call_naming_an_event_also_identifies_it() -> None:
    """Without this, the canonical-name test above silently skips a call. Not
    hypothetical: CALL-01 once named its event non-canonically AND declared no
    event_id, so the check keyed to event_id never looked at it. A guard
    narrower than the rule it enforces is green and blind."""
    for transcript in _transcripts():
        call = parse_call(transcript)
        names = {name for name, _ in call.context}
        if "event_title" in names:
            assert "event_id" in names, (
                f"{call.record.call_id} names an event without identifying it"
            )


#: Context fields that describe the *event* rather than the booking, and so must
#: agree wherever the same `event_id` appears. Deliberately not every shared
#: field: `ticket_count`, `booking_reference` and `price_band` belong to one
#: caller's purchase, and two callers holding seats to one show are expected to
#: differ on them.
#:
#: Ported from the held-out repository, where D85 wrote the widened check and
#: verified it failed on the value it was written for. It lands here as a
#: sibling rather than as a widening of the title check above, because D85's
#: Rule line names that test by name and a record may not be left citing a test
#: that no longer exists.
_EVENT_SCOPED_FIELDS: Final[tuple[str, ...]] = ("event_title", "door_time")


def _event_scoped_disagreements(calls: list[Call]) -> tuple[list[str], dict[str, int]]:
    """`(disagreements, comparisons made per field)` over calls sharing an `event_id`.

    Separated from its test so the control below can run the same code over a
    corpus it has mutated. A check whose only evidence is that it has never
    fired has been proven against nothing.
    """
    seen: dict[tuple[str, str], dict[str, str]] = {}
    problems: list[str] = []
    compared: dict[str, int] = {}
    for call in calls:
        context = dict(call.context)
        event_id = context.get("event_id")
        if not event_id:
            continue
        for field in _EVENT_SCOPED_FIELDS:
            value = context.get(field)
            if value is None:
                continue
            previous = seen.setdefault((event_id, field), {})
            for other_call, other_value in previous.items():
                compared[field] = compared.get(field, 0) + 1
                if other_value != value:
                    problems.append(
                        f"{event_id} has {field}={value!r} in {call.record.call_id} "
                        f"and {other_value!r} in {other_call}"
                    )
            previous[call.record.call_id] = value
    return problems, compared


def test_one_event_id_means_one_event() -> None:
    """Two calls naming the same `event_id` must agree about that event.

    The title check above compares **titles**, and D85 recorded what that
    misses. `EV-88011` was carried by CALL-01, CALL-02 and CALL-18 with three
    different `door_time` values -- two of them half an hour apart on one
    evening, one a week later -- while all three agreed about the name. So the
    guard ran, compared, and reported nothing, on the three transcripts holding
    the contradiction. Undeclared drift, in the corpus this repository can see.

    `door_time` is the field that most needed including: every deadline in the
    policy set is measured against it -- an exchange window closes 48 hours
    before it (`exchange.v1` 2.1) -- so an agent reasoning about a window
    against the wrong date reasons correctly to a wrong answer, and the
    transcript reads as though the agent erred.

    **No seeded-drift exemption, deliberately**, which is where this differs
    from its neighbor. Naming drift is taxonomy 20 and CALL-08 seeds it in a
    tool result; a call needing an exemption *here* should get one added
    explicitly with its reason rather than inheriting a hole sized for another
    field. CALL-08's context agrees with CALL-03 about both fields, so the
    exemption would exempt nothing today anyway.
    """
    problems, compared = _event_scoped_disagreements([parse_call(t) for t in _transcripts()])
    assert not problems, "one event id, two events:\n  " + "\n  ".join(problems)

    # Per field rather than one total. An aggregate floor hides a field that has
    # quietly stopped being compared -- D74's per-document minimums, arriving
    # one noun over -- and this check exists because a narrower version of it
    # was green while blind.
    for field in _EVENT_SCOPED_FIELDS:
        assert compared.get(field, 0) >= 1, (
            f"no two transcripts share an event id and both carry {field}, so this "
            "check compared nothing for it. Silence is not agreement."
        )
    # And the distribution by equality, because D87 wrote the figures into the
    # decision record. Measured: nine title comparisons and eight door-time
    # ones. A figure in prose is a claim; the floor above says the check is not
    # blind, and this says the claim is still true.
    assert compared == MEASURED["event_scoped_comparisons"], (
        f"the event-scoped comparison counts have moved: measured {compared}, "
        f"stated {MEASURED['event_scoped_comparisons']}"
    )


def test_the_event_scoped_check_fires_on_a_door_time_its_titles_agree_with(
    tmp_path: Path,
) -> None:
    """The control, planted rather than assumed.

    D85's finding was that the narrower check *passed* on the pair carrying the
    contradiction, so a widened check observed only to pass is in the same
    position its predecessor was. This puts the pre-repair value back on a copy
    of CALL-18 -- one field, the title untouched -- and asserts two things: that
    the widened check names it, and that the title comparison still does not.
    The second half is the reason the first exists.
    """
    template = (TRANSCRIPTS / "CALL-18.txt").read_text(encoding="utf-8")
    assert "door_time := 2027-03-19T19:00:00Z" in template, (
        "CALL-18 no longer carries the repaired door time, so this control is "
        "planting something other than the defect it names"
    )
    mutated = tmp_path / "CALL-18.txt"
    mutated.write_text(
        template.replace("door_time := 2027-03-19T19:00:00Z", "door_time := 2027-03-19T19:30:00Z"),
        encoding="utf-8",
    )

    calls = [parse_call(t) for t in _transcripts() if t.stem != "CALL-18"]
    calls.append(parse_call(mutated))

    problems, _ = _event_scoped_disagreements(calls)
    assert any("door_time" in problem and "EV-88011" in problem for problem in problems), (
        f"the pre-repair door time is back in CALL-18 and nothing named it: {problems}"
    )

    titles = {
        call.record.call_id: dict(call.context).get("event_title")
        for call in calls
        if call.record.call_id in {"CALL-01", "CALL-18"}
    }
    assert len(set(titles.values())) == 1, (
        "the two calls disagree about the title too, so this control no longer "
        "demonstrates that a title comparison is blind to the door time"
    )


#: Context variables a `TOOL_RESULT` detail could echo back, so the two can
#: disagree about one booking.
#:
#: This was the one-element tuple `("door_time",)` under a docstring
#: generalizing to "one record holding two values for one field".
#:
#: **Widening it compared almost nothing new**, and the figure that sentence
#: used to carry had itself gone stale. Measured now: `door_time` yields four
#: comparisons across the corpus, `price_band` and `ticket_count` one each, and
#: the remaining six yield **zero**, because no tool result in this corpus
#: echoes them in `field=value` form. The longer tuple is still mostly a
#: statement about what *would* be checked rather than about what is, and
#: shipping that as though it were coverage is the defect this file is full of
#: tests against.
#:
#: **The number said `two` for as long as the assertion under it was a floor.**
#: `test_the_contradiction_check_is_comparing_something` asserted `total >= 2`,
#: which four satisfies as comfortably as two, so the corpus grew a second and
#: third echoing field and nothing said so. It now asserts the whole
#: distribution against `MEASURED`, by equality.
CONTRADICTABLE_FIELDS: Final[tuple[str, ...]] = (
    "door_time",
    "event_title",
    "price_band",
    "ticket_count",
    "ticket_price_total",
    "booking_fee",
    "exchange_window_closes_at",
    "refund_window_closes_at",
    "transfer_window_closes_at",
)


def _event_the_result_describes(
    result: ToolResultEvent, invocation: ToolCallEvent | None
) -> str | None:
    """Which catalog event a tool result is talking about, or `None` if it does
    not say. Read from the result's own `match=` first, then from the
    invocation's arguments; a result that names neither is assumed to concern
    the booked event, which is the conservative reading — it keeps the
    contradiction check looking rather than letting silence exempt anything."""
    named = re.search(r"\bmatch=(EV-\d+)", result.detail or "")
    if named:
        return named.group(1)
    if invocation is not None:
        argued = re.search(r'\bevent(?:_id)?="(EV-\d+)"', invocation.arguments)
        if argued:
            return argued.group(1)
    return None


def test_a_record_contradicts_itself_only_where_it_is_seeded() -> None:
    """P9's data-layer contradiction is one record holding two values for one
    field. Anywhere else it is an accident.

    **Two values for a field are only a contradiction when they describe the
    same thing.** An earlier version of this check compared every `door_time=`
    in a tool result against the context's, and fired on CALL-01, where a
    `find_performance` lookup returns a *different* performance whose door time
    is legitimately different. A check that cannot tell "the record disagrees
    with itself" from "these are two events" reports the second as the first,
    and the fix is to establish which event the result is about before
    comparing anything.
    """
    offenders: set[str] = set()
    for transcript in _transcripts():
        call = parse_call(transcript)
        context = dict(call.context)
        booked_event = context.get("event_id")
        invocations = {
            event.tool_call_id: event for event in call.events if isinstance(event, ToolCallEvent)
        }
        for event in call.events:
            if isinstance(event, ToolResultEvent) and event.detail:
                subject = _event_the_result_describes(event, invocations.get(event.tool_call_id))
                if subject is not None and subject != booked_event:
                    continue
                for field in CONTRADICTABLE_FIELDS:
                    match = re.search(rf"{field}=(\S+?)(?:;|$)", event.detail)
                    if match and field in context and match.group(1) != context[field]:
                        offenders.add(call.record.call_id)
    assert offenders == set(CONTRADICTORY_RECORD_SEEDED), (
        f"calls whose record contradicts itself: {sorted(offenders)}; "
        f"seeded: {sorted(CONTRADICTORY_RECORD_SEEDED)}"
    )


# --------------------------------------------------------------------------
# The corpus exercises what the model declares
# --------------------------------------------------------------------------


def test_every_tool_status_is_exercised() -> None:
    """A closed vocabulary with unused tokens is untested vocabulary."""
    used = {
        event.status
        for transcript in _transcripts()
        for event in parse_call(transcript).events
        if isinstance(event, ToolResultEvent)
    }
    missing = set(ToolStatus) - used
    assert not missing, f"tool statuses never exercised: {sorted(s.value for s in missing)}"


def test_every_event_kind_is_exercised() -> None:
    used = {event.kind for transcript in _transcripts() for event in parse_call(transcript).events}
    missing = set(EventKind) - used
    assert not missing, f"event kinds never exercised: {sorted(k.value for k in missing)}"


@pytest.mark.parametrize("transcript", _transcripts(), ids=lambda p: p.stem)
def test_every_call_carries_a_wrapped_event(transcript: Path) -> None:
    call = parse_call(transcript)
    assert any(len(event.source_lines) > 1 for event in call.events)


def _wrapped_assignments_in_the_corpus() -> tuple[list[str], list[str]]:
    """`(wrapped STATE events, wrapped context assignments)`, each as labels.

    Both halves now come from the parsed call: an event carries `source_lines`
    and a context pair carries `context_source_lines`, aligned by position. The
    context half used to re-parse the `[context]` block here, line by line,
    because the model could not say how many lines a value spanned -- twenty-odd
    lines of parser living in a test, which is a second implementation of the
    rule under test and drifts from the first the moment either changes.
    """
    state_events: list[str] = []
    context_values: list[str] = []
    for transcript in _transcripts():
        call = parse_call(transcript)
        state_events += [
            f"{call.record.call_id} event {event.index}"
            for event in call.events
            if isinstance(event, StateEvent) and len(event.source_lines) > 1
        ]
        context_values += [
            f"{call.record.call_id} {name} ({len(span)} source lines)"
            for (name, _), span in zip(call.context, call.context_source_lines, strict=True)
            if len(span) > 1
        ]
    return state_events, context_values


def test_the_corpus_carries_a_wrapped_assignment() -> None:
    """W16 on real data, not only on the fixture, and measured as a **span**.

    This asserted `wrapped or any(len(v.split()) > 8 ...)`. The corpus contains
    **no** wrapped `STATE` event, so it passed entirely on the second clause --
    a word count, which is not a wrap. As it happens the long value does wrap,
    but by luck rather than by anything the test looked at, and this test is one
    of three that `tools/verify_phase1.py` names as evidence for the three-line
    wrap acceptance criterion.

    Spans now, on both sites the rule covers: a `STATE` event in the event
    stream, and an assignment in the `[context]` block. Today the corpus wraps
    the second and not the first, which the assertion states rather than
    conceals -- a corpus that stopped wrapping anything would fail here instead
    of passing on a proxy.
    """
    state_events, context_values = _wrapped_assignments_in_the_corpus()
    assert state_events or context_values, (
        "no assignment in the corpus wraps across source lines, so W16 is "
        "tested only by the fixture"
    )
    assert context_values, (
        "the corpus no longer wraps a [context] assignment; if a wrapped STATE "
        "event has replaced it, say so here rather than deleting this line"
    )


def test_a_wrapped_context_value_keeps_every_source_fragment() -> None:
    """The span above proves a wrap exists; this proves it survived it.

    Asserted against the source file rather than the parser's output, which is
    the W19 fix: a conformance test that reads the parser's own result cannot
    see a fragment the parser dropped.
    """
    _, wrapped = _wrapped_assignments_in_the_corpus()
    assert wrapped, "nothing to check"
    checked = 0
    for transcript in _transcripts():
        source = transcript.read_text(encoding="utf-8")
        context = dict(parse_call(transcript).context)
        lines = source.splitlines()
        start = lines.index("[context]") + 1
        name: str | None = None
        for line in lines[start:]:
            if line.strip() == "[events]":
                break
            if not line.strip():
                continue
            if line[:1].isspace():
                assert name is not None
                assert line.strip() in context[name], (
                    f"{transcript.stem}: continuation {line.strip()!r} is missing from "
                    f"the parsed value of {name}"
                )
                checked += 1
                continue
            name = line.split(":=", 1)[0].strip() if ":=" in line else None
    assert checked >= 2, f"only {checked} continuation lines were checked"


def _clauses(document: Path) -> dict[str, str]:
    """`clause id -> text`, whitespace-normalized, quotation marks stripped.

    Delegates to `harness.corpus.policies`, which is where this parse lives now
    that phase 2 needs clauses above the adapter line. It had been a private
    copy here, and two parsers for one format drift -- the one that drifted
    would have been the one the harness reads, while this test went on
    validating the other and reporting success.
    """
    return parse_policy(document.stem, document.read_text(encoding="utf-8")).as_mapping()


def test_every_retrieved_clause_matches_the_clause_it_cites() -> None:
    """Correspondence on normalized whitespace (D32). The seeded defects are in
    what the agent *says about* clauses, never in the clause text itself.

    **Against the cited clause, not the document.** Every policy document's
    preamble says the quoted text "must equal the clause text below" for the
    clause the event cites. The earlier version of this test asked only whether
    the quote appeared somewhere in the file, so a POLICY event citing § 2.1
    while quoting § 2.3 passed -- and the refund windows are three clauses that
    differ by a number and a word. A citation nobody checks is decoration, and
    the misattribution it would hide is exactly the defect class the POLICY
    event exists to expose.
    """
    checked = 0
    for transcript in _transcripts():
        call = parse_call(transcript)
        for event in call.events:
            if event.kind is not EventKind.POLICY:
                continue
            assert isinstance(event, PolicyEvent)
            document = POLICIES / f"{event.document}.md"
            assert document.is_file(), f"{event.document} has no policy document"
            clauses = _clauses(document)
            assert event.clause in clauses, (
                f"{call.record.call_id} event {event.index}: "
                f"{event.document} has no clause {event.clause}"
            )
            assert " ".join(event.text.split()) == clauses[event.clause], (
                f"{call.record.call_id} event {event.index}: quoted text is not "
                f"{event.document} § {event.clause}\n"
                f"       quoted: {' '.join(event.text.split())!r}\n"
                f"       clause: {clauses[event.clause]!r}"
            )
            checked += 1
    assert checked >= 6, f"only {checked} POLICY events were checked"


def test_the_clause_check_can_tell_two_clauses_apart() -> None:
    """The negative control, and the reason the stronger check was worth
    writing: refund.v1's three refund windows are near-identical sentences.
    A comparison that could not separate them would pass a transcript citing
    any of the three while quoting any other."""
    windows = _clauses(POLICIES / "refund.v1.md")
    assert {"2.1", "2.2", "2.3"} <= set(windows)
    assert len({windows["2.1"], windows["2.2"], windows["2.3"]}) == 3
    for clause in ("2.1", "2.2", "2.3"):
        others = {c for c in ("2.1", "2.2", "2.3") if c != clause}
        assert all(windows[clause] != windows[other] for other in others)


def test_every_tool_called_is_declared_in_the_entity_register() -> None:
    """The register is the capability inventory several findings depend on --
    'the tool existed and was not used' is only checkable against a declared
    list, not against whatever happens to appear in a transcript."""
    register = (CORPUS / "entities.md").read_text(encoding="utf-8")
    declared = set(re.findall(r"`([a-z_]+)`", register))
    used = {
        event.name
        for transcript in _transcripts()
        for event in parse_call(transcript).events
        if isinstance(event, ToolCallEvent)
    }
    assert used <= declared, f"tools used but not declared: {sorted(used - declared)}"


# --------------------------------------------------------------------------
# The entity register is the canonical list, or it is decoration
# --------------------------------------------------------------------------


def _calls() -> list[Call]:
    """Every design-set call, parsed."""
    return [parse_call(transcript) for transcript in _transcripts()]


#: The register's category headings, in the order they appear. Enumerated rather
#: than pattern-matched: the file uses bold for headings *and* for explanatory
#: prose -- "**Why this matters.**", "**Variety is deliberate.**" -- so "the next
#: bold paragraph" cuts a category in half, and "the next `##`" (what the code
#: did) does not cut it at all. Neither is the boundary. The boundary is the next
#: category, and the categories are a list.
_REGISTER_CATEGORIES: Final[tuple[str, ...]] = (
    "**Tools.**",
    "**Context variables**",
    "**State variables**",
    "**Disclosure names.**",
    "**Outcomes.**",
    "**Outcome reasons.**",
    "**System event names.**",
    "**Tool arguments.**",
    "**Tool-result detail keys.**",
)


def _declared_names(heading: str) -> set[str]:
    """Every backticked identifier declared under `heading` in the register.

    **Bounded at the next category, which is what this docstring always claimed
    and what the code did not do.** It searched for the next Markdown `##`, so
    every category's set contained all the categories below it -- a name
    declared under *Outcome reasons* satisfied *Context variables*, and the
    check that enforces "used implies declared" was really asking whether a name
    appeared anywhere in a large region of one file. Six categories passed, for
    a reason none of them was tested against.

    The identifier pattern allows a dot, because `call.answered` is a name and
    `[a-z_]+` does not fail on it -- it returns a smaller set, and a membership
    test against a smaller set still reads as green.
    """
    assert heading in _REGISTER_CATEGORIES, f"{heading!r} is not a register category"
    register = (REPO_ROOT / "corpus" / "entities.md").read_text(encoding="utf-8")
    start = register.index(heading)
    rest = register[start + len(heading) :]

    cuts = [rest.index(other) for other in _REGISTER_CATEGORIES if other in rest]
    section = rest[: min(cuts)] if cuts else rest
    return set(re.findall(r"`([a-z_][a-z0-9_.]*)`", section))


def test_every_name_the_corpus_uses_is_in_the_register() -> None:
    """The register claims to be the canonical list. A name used in a transcript
    and absent from the register makes that claim false, and quietly narrows
    every check keyed to the list.

    This bit: ten context variables — `currency`, `caller_verified`,
    `price_band_note` among them — were in use across the corpus while the
    register listed none of them. Nothing failed, because nothing was looking.

    The implication runs one way only. A name declared and never used is the
    inventory doing its job: three tools are cited by findings precisely because
    they existed and were not called.
    """
    used_context: set[str] = set()
    used_state: set[str] = set()
    used_tools: set[str] = set()
    used_disclosures: set[str] = set()
    used_system: set[str] = set()
    used_arguments: set[str] = set()
    used_detail_keys: set[str] = set()

    for transcript in _transcripts():
        call = parse_call(transcript)
        used_context.update(name for name, _ in call.context)
        for event in call.events:
            if isinstance(event, StateEvent):
                used_state.add(event.name)
            elif isinstance(event, ToolCallEvent):
                used_tools.add(event.name)
            elif isinstance(event, DisclosureEvent):
                used_disclosures.add(event.name)
            elif isinstance(event, SystemEvent):
                used_system.add(event.name)
            if isinstance(event, ToolCallEvent):
                used_arguments |= set(re.findall(r"(\w+)\s*=", event.arguments or ""))
            elif isinstance(event, ToolResultEvent) and event.detail:
                used_detail_keys |= set(re.findall(r"(\w+)=", event.detail))

    used_outcomes = {call.record.outcome.value for call in _calls()}
    used_reasons = {call.record.outcome_reason for call in _calls()}

    undeclared = {
        "context variable": used_context - _declared_names("**Context variables**"),
        "state variable": used_state - _declared_names("**State variables**"),
        "tool": used_tools - _declared_names("**Tools.**"),
        "disclosure": used_disclosures - _declared_names("**Disclosure names.**"),
        "outcome": used_outcomes - _declared_names("**Outcomes.**"),
        "outcome reason": used_reasons - _declared_names("**Outcome reasons.**"),
        # Three kinds this check did not reach. It covered six and the corpus
        # names nine, so `call.answered` and `call.ended` -- twenty-nine uses,
        # one of them a seeded defect -- were held by nothing but two string
        # literals in another assertion, and a new SYSTEM name would have been
        # compared against nothing at all.
        "SYSTEM event name": used_system - _declared_names("**System event names.**"),
        "tool argument": used_arguments - _declared_names("**Tool arguments.**"),
        "tool-result detail key": used_detail_keys
        - _declared_names("**Tool-result detail keys.**"),
    }
    problems = [
        f"{kind}: {', '.join(sorted(names))}" for kind, names in undeclared.items() if names
    ]
    assert not problems, "used in the corpus, absent from corpus/entities.md:\n  " + "\n  ".join(
        problems
    )


def test_the_register_check_is_reading_something() -> None:
    """The negative control. A heading typo, or a section-extraction bug, would
    return an empty declared set — and then the test above passes by finding
    nothing to compare against."""
    for heading, expected in (
        ("**Context variables**", "booking_reference"),
        ("**State variables**", "exchange_eligible"),
        ("**Tools.**", "issue_refund"),
        ("**Disclosure names.**", "recording_notice"),
        ("**System event names.**", "call.answered"),
        ("**Tool arguments.**", "assume_verified"),
        ("**Tool-result detail keys.**", "difference_due"),
        ("**Outcomes.**", "resolved"),
        ("**Outcome reasons.**", "refund_issued"),
    ):
        declared = _declared_names(heading)
        # Two, not four: `**System event names.**` declares exactly two and
        # always will unless the format grows a lifecycle event. The floor is
        # here to catch a heading that yields nothing, and the named member
        # below is what actually proves the extraction reached the right block.
        assert len(declared) >= 2, f"{heading} yielded {len(declared)} names"
        assert expected in declared, f"{heading} does not name {expected}"


# --------------------------------------------------------------------------
# Values the register declares, beside the names above (D193)
# --------------------------------------------------------------------------
#
# The check above reads the corpus's *names* -- tools, variables, argument and
# detail keys -- and never the values they carry. So `refund_id` was declared and
# the `RF-` identifier it returns was not, and a settlement token named a third
# party the register knew only by its display name. Both were found by the
# held-out side while labeling, not by this module. These read the two kinds of
# value the register declares: identifier shapes (Class 2) and third-party
# tokens (Class 5).

#: An identifier-shaped token anywhere in a transcript: two capitals, a hyphen, a
#: digit, then digits, capitals or hyphens. `CALL-NN` is not one -- four capitals.
_IDENTIFIER_TOKEN: Final[re.Pattern[str]] = re.compile(r"\b[A-Z]{2}-\d[0-9A-Z-]*\b")


def _register_section(heading: str, next_heading: str) -> str:
    register = (CORPUS / "entities.md").read_text(encoding="utf-8")
    start = register.index(heading)
    return register[start : register.index(next_heading, start)]


def _identifier_shapes() -> dict[str, re.Pattern[str]]:
    """Every identifier shape Class 2 declares, as a pattern: `#` a digit, `X` a
    capital, anything else literal. Only the prefixed shapes -- two capitals and a
    hyphen -- which are the ones `_IDENTIFIER_TOKEN` can find."""
    section = _register_section("## Class 2", "## Class 3")
    shapes: dict[str, re.Pattern[str]] = {}
    for shape in re.findall(r"\| `([A-Z]{2}-[#X-]+)` \|", section):
        body = "".join(r"\d" if c == "#" else "[A-Z]" if c == "X" else re.escape(c) for c in shape)
        shapes[shape] = re.compile(body)
    return shapes


def _undeclared_identifiers(text: str, shapes: dict[str, re.Pattern[str]]) -> set[str]:
    """Every identifier-shaped token in `text` that no declared shape matches whole."""
    return {
        token
        for token in _IDENTIFIER_TOKEN.findall(text)
        if not any(pattern.fullmatch(token) for pattern in shapes.values())
    }


def _third_party_tokens() -> set[str]:
    """The machine tokens Class 5 declares for its third parties."""
    return set(re.findall(r"`([a-z][a-z0-9_]*)`", _register_section("## Class 5", "## Class 6")))


def _undeclared_settlements(details: list[str], declared: set[str]) -> set[str]:
    """Every `settlement=` value in the tool-result `details` that is not a
    declared third-party token."""
    return {
        token
        for detail in details
        for token in re.findall(r"\bsettlement=([a-z0-9_]+)", detail)
        if token not in declared
    }


def test_the_register_would_notice_an_identifier_of_an_undeclared_shape() -> None:
    """Every identifier the corpus uses has a shape Class 2 declares (D193).

    Planted first, so the check is proven to find one: a shape nobody declared is
    reported and a declared one is not. Then the corpus, which must carry none.
    """
    shapes = _identifier_shapes()
    assert {"BK-####-XX", "RF-#####", "SP-####"} <= set(shapes), sorted(shapes)
    assert _undeclared_identifiers("refund_id=RF-20714; case=ZZ-12345", shapes) == {"ZZ-12345"}

    found = {
        path.stem: _undeclared_identifiers(path.read_text(encoding="utf-8"), shapes)
        for path in _transcripts()
    }
    assert sum(len(_IDENTIFIER_TOKEN.findall(p.read_text("utf-8"))) for p in _transcripts()) > 100
    undeclared = {call: tokens for call, tokens in found.items() if tokens}
    assert not undeclared, (
        f"identifiers of a shape corpus/entities.md Class 2 does not declare: {undeclared}"
    )


def test_the_register_would_notice_a_settlement_token_it_does_not_declare() -> None:
    """Every settlement a tool result names is a token Class 5 declares (D193).

    Planted first -- an undeclared processor is reported and the declared one is
    not -- then the corpus, which must name none the register does not.
    """
    declared = _third_party_tokens()
    assert "cardinal_pay" in declared, sorted(declared)
    assert _undeclared_settlements(
        ["settlement=cardinal_pay; expected_days=5", "settlement=other_pay"], declared
    ) == {"other_pay"}

    details = [
        event.detail
        for path in _transcripts()
        for event in parse_call(path).events
        if isinstance(event, ToolResultEvent) and event.detail
    ]
    assert any("settlement=" in detail for detail in details), "no settlement is read at all"
    undeclared = _undeclared_settlements(details, declared)
    assert not undeclared, (
        f"settlement tokens corpus/entities.md Class 5 does not declare: {sorted(undeclared)}"
    )


# --------------------------------------------------------------------------
# The manifest's anchor table
# --------------------------------------------------------------------------


def _anchor_rows() -> list[tuple[str, int, str, str]]:
    """`(call, index, kind, fragment)` for every row of the manifest's anchor
    table."""
    manifest = (REPO_ROOT / "corpus" / "seeding-manifest.md").read_text(encoding="utf-8")
    start = manifest.index("## Anchors")
    rows: list[tuple[str, int, str, str]] = []
    for line in manifest[start:].splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 4 or not cells[0].startswith("CALL-"):
            continue
        rows.append((cells[0], int(cells[1]), cells[2], cells[3]))
    return rows


def _corpus_events() -> dict[tuple[str, int], Event]:
    """`{(call id, event index): event}` across the corpus."""
    events: dict[tuple[str, int], Event] = {}
    for transcript in _transcripts():
        call = parse_call(transcript)
        for event in call.events:
            events[(call.record.call_id, event.index)] = event
    return events


def _anchor_problems(
    rows: list[tuple[str, int, str, str]], events: dict[tuple[str, int], Event]
) -> list[str]:
    """Every way an anchor row fails to describe the event it points at.

    Lifted out of the check so the control below can run this comparison over a
    table it has moved, rather than asserting a property of the corpus beside
    it. Neutered so it could never report a problem, this comparison left the
    check green over a drifted manifest and the control green with it.
    """
    problems: list[str] = []
    for call_id, index, kind, fragment in rows:
        anchored = events.get((call_id, index))
        if anchored is None:
            problems.append(f"{call_id} event {index} does not exist")
            continue
        if anchored.kind.value != kind:
            problems.append(f"{call_id} event {index} is {anchored.kind.value}, not {kind}")
        elif fragment not in anchored.body:
            problems.append(
                f"{call_id} event {index} does not contain {fragment!r}\n"
                f"       the event says: {anchored.body!r}"
            )
    return problems


def test_every_manifest_anchor_still_points_where_it_says() -> None:
    """The manifest states that this file asserts its anchor table. It did not.

    Every "Where" reference in the manifest is positional, the manifest itself
    says positional references break silently, and the table was added so a
    renumbered transcript would be caught. No test ever read it. CALL-01 was
    then rewritten, its indices moved, and two rows pointed at the wrong events
    while the suite stayed green — the precise failure the table exists to
    prevent, undetected because the guard it named was never written.
    """
    rows = _anchor_rows()
    assert len(rows) > 30, f"only {len(rows)} anchor rows parsed; the table shape has changed"

    problems = _anchor_problems(rows, _corpus_events())
    assert not problems, "manifest anchors have drifted from the corpus:\n  " + "\n  ".join(
        problems
    )


def test_the_anchor_check_would_notice_a_moved_event() -> None:
    """The control, and it did not drive the comparison it controls.

    It asserted that the table parsed to at least twelve calls and that the
    first fragment was absent from its neighbor -- both properties of the
    corpus, neither of them the check. Measured when this was written: with the
    per-row comparison neutered so it could never append a problem, the check
    passed over everything and **this control passed with it**, which is the second of the
    two modes its own docstring claimed. Only the zero-rows mode was covered,
    and the check already fails on that by itself.

    It moves an anchor now -- the renumbered transcript the table exists to
    catch -- and requires the comparison to name it.
    """
    rows = _anchor_rows()
    calls = {call_id for call_id, _, _, _ in rows}
    assert len(calls) >= 12, f"the table covers only {sorted(calls)}"

    events = _corpus_events()
    assert not _anchor_problems(rows, events), "the corpus does not agree with its own manifest"

    call_id, index, kind, fragment = rows[0]
    assert (call_id, index + 1) in events, (
        f"{call_id} event {index} has no neighbor to be moved onto; pick a different row"
    )
    moved = [(call_id, index + 1, kind, fragment), *rows[1:]]
    problems = _anchor_problems(moved, events)
    assert any(call_id in problem and str(index + 1) in problem for problem in problems), (
        "an anchor pointed one event past where its fragment lives and the comparison "
        f"reported nothing: {problems}"
    )


def _calls_that_verify_properly() -> set[str]:
    """Calls where `verify_caller` is invoked, its result is successful, and the
    platform records `identity_verified := true`. All three, in one call."""
    verifying: set[str] = set()
    for transcript in _transcripts():
        call = parse_call(transcript)
        invoked = {
            event.tool_call_id
            for event in call.events
            if isinstance(event, ToolCallEvent) and event.name == "verify_caller"
        }
        succeeded = any(
            isinstance(event, ToolResultEvent)
            and event.tool_call_id in invoked
            and event.successful
            for event in call.events
        )
        recorded = any(
            isinstance(event, StateEvent)
            and event.name == "identity_verified"
            and event.value == "true"
            for event in call.events
        )
        if invoked and succeeded and recorded:
            verifying.add(call.record.call_id)
    return verifying


def test_the_verification_true_negatives_are_the_calls_that_verify() -> None:
    """The manifest's first true-negative row names the calls a verification
    check must not fire on. It named one it must.

    The row listed CALL-12 and said "eleven of twelve". CALL-12 never calls
    `verify_caller` at all — it retries the refused write with
    `assume_verified="true"`, which is F-46, a seeded platform defect. So the
    manifest was instructing a reader that the check must not fire on the one
    call whose verification bypass the corpus exists to catch, while the
    findings document said the opposite in the same repository. Nothing
    compared them.

    A true-negative list is only worth having if it is derived from the corpus
    rather than remembered about it.
    """
    manifest = (REPO_ROOT / "corpus" / "seeding-manifest.md").read_text(encoding="utf-8")
    row = next(line for line in manifest.splitlines() if "`verify_caller` is invoked" in line)
    listed = {f"CALL-{number}" for number in re.findall(r"\b(\d{2})\b", row.split("|")[1])}
    assert listed, "the row's call list did not parse; the table shape has changed"
    assert listed == _calls_that_verify_properly(), (
        "the manifest's verification true negatives disagree with the corpus:\n"
        f"  manifest says: {sorted(listed)}\n"
        f"  corpus says:   {sorted(_calls_that_verify_properly())}"
    )


def test_the_calls_that_do_not_verify_are_the_ones_the_findings_name() -> None:
    """The other half. The check above proves the manifest matches the corpus;
    this proves the corpus matches the findings, so the three documents cannot
    drift apart in a pair while agreeing with the third.

    It did not. The assertion read
    `all_calls - _calls_that_verify_properly() == {"CALL-01", "CALL-12"}` and
    never opened `findings.candidates.yaml` -- a hardcoded literal under a
    docstring claiming to compare two documents, which is the shape this file
    is full of tests against. Renaming a call, or moving the finding that owns
    the claim, would have left it green.

    The findings side is now derived: a platform-owned finding that names
    `identity_verified` is a finding asserting the platform never recorded
    verification, and the set of calls carrying one must be exactly the set of
    calls that do not verify.
    """
    all_calls = {parse_call(transcript).record.call_id for transcript in _transcripts()}
    unverified = all_calls - _calls_that_verify_properly()

    document = yaml.safe_load(
        (REPO_ROOT / "corpus" / "findings.candidates.yaml").read_text(encoding="utf-8")
    )
    rows = document["findings"] if isinstance(document, dict) else document
    # Owner plus a variable name is a proxy for a claim, and CALL-20 is where
    # the proxy broke: F-88 is platform-owned and names `identity_verified`
    # precisely because verification *did* happen and did not survive the
    # handoff. The discriminator is structural rather than a label -- a finding
    # asserting verification never happened cannot quote the STATE event that
    # performs it, and in the three calls that genuinely never verify no such
    # event exists to quote.
    claimed = {
        str(row["call_ref"])
        for row in rows
        if row.get("owner") == "platform"
        and "identity_verified" in " ".join(str(value) for value in row.values())
        and "identity_verified := true" not in " ".join(str(v) for v in row.get("evidence", []))
    }
    assert claimed == unverified, (
        "the corpus and the findings disagree about which calls fail to verify:\n"
        f"  corpus says:   {sorted(unverified)}\n"
        f"  findings name: {sorted(claimed)}"
    )
    assert unverified, "no call fails to verify, so this check is vacuous"


# --------------------------------------------------------------------------
# The worksheet is generated, and a generated file nobody regenerates is stale
# --------------------------------------------------------------------------


def test_the_worksheet_renders_and_states_the_position_it_is_actually_in() -> None:
    """The worksheet is generated on demand and no longer committed (D76).

    Its purpose -- scaffolding for the one phase-1 step a model must not do --
    was discharged when the last of 89 rulings landed, and it was never used for
    that purpose: adjudication happened in dialogue and landed in the ledger.
    What it left behind was 221KB of derived text asserting, in its own preamble,
    that *"every row is drafted and unadjudicated"*, two days after the opposite
    became true.

    So the file goes and the generator stays, for the second human reader this
    project still owes -- and this runs it, because a generator with no committed
    output can rot unnoticed. Two assertions: it renders, and what it renders
    states the position the ledger is actually in.
    """
    with tempfile.TemporaryDirectory() as directory:
        rendered = Path(directory) / "worksheet.md"
        result = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "tools" / "make_review_worksheet.py"),
                "--out",
                str(rendered),
            ],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, (
            "the worksheet generator failed: " + result.stdout + result.stderr
        )
        assert rendered.is_file(), "the generator reported success and wrote nothing"
        text = rendered.read_text(encoding="utf-8")

    drafts = {f.id for f in load_findings(REPO_ROOT / "corpus" / "findings.candidates.yaml")}
    document = yaml.safe_load(
        (REPO_ROOT / "corpus" / "findings.adjudication.yaml").read_text(encoding="utf-8")
    )
    rows = document["rulings"] if isinstance(document, dict) and "rulings" in document else document
    if isinstance(rows, dict):
        rows = next(iter(rows.values()))
    unruled = drafts - {str(row["id"]) for row in rows}

    claims_done = "Every row here has been adjudicated." in text
    assert claims_done == (not unruled), (
        f"the worksheet says adjudication is {'complete' if claims_done else 'outstanding'}; "
        f"{len(unruled)} of {len(drafts)} drafts are unruled"
    )
    says_absent = "It does not exist until then, deliberately." in text
    assert says_absent != (REPO_ROOT / "corpus" / "findings.yaml").is_file(), (
        "the worksheet says the gold set does not exist yet while it does, or the reverse"
    )


def test_every_part_one_reference_is_anchored() -> None:
    """M3. Part 1's own paragraph says positional references break silently and
    that the anchor table is where they are restated. Three of sixteen were.

    The thirteen missing ones were every true negative except CALL-01's and
    CALL-12's -- the rows telling a future check what it must *not* fire on,
    which is where drift is most expensive: a check calibrated against the wrong
    events fires on correct behavior and is switched off.

    Asserted as *coverage*, not as rows. A new true negative citing an event
    index has to be anchored, or this fails.
    """
    manifest = (REPO_ROOT / "corpus" / "seeding-manifest.md").read_text(encoding="utf-8")
    part_one = manifest[manifest.index("## Part 1") : manifest.index("## Part 2")]

    referenced: set[tuple[str, int]] = set()
    for call, spanned in re.findall(r"(CALL-\d+) events? ([\d,\u2013\u2014\s-]+)", part_one):
        for index in re.findall(r"\d+", spanned):
            referenced.add((call, int(index)))
    assert len(referenced) >= 10, (
        f"only {len(referenced)} positional references parsed out of Part 1; "
        "the phrasing has changed and this check is looking at nothing"
    )

    anchored = {(call, index) for call, index, _, _ in _anchor_rows()}
    unanchored = sorted(referenced - anchored)
    assert not unanchored, "Part 1 positional references with no anchor row:\n  " + "\n  ".join(
        f"{call} event {index}" for call, index in unanchored
    )


def test_the_manifest_findings_ranges_match_the_findings_document() -> None:
    """M4. Part 2 maps each call to a findings range. Nothing checked it, and
    the notation has already been perturbed once -- F-50 and F-51 were appended
    out of sequence to CALL-02's row when a finding split in three."""
    manifest = (REPO_ROOT / "corpus" / "seeding-manifest.md").read_text(encoding="utf-8")
    part_two = manifest[manifest.index("## Part 2") : manifest.index("### Notes")]

    document = yaml.safe_load(
        (REPO_ROOT / "corpus" / "findings.candidates.yaml").read_text(encoding="utf-8")
    )
    findings = document["findings"] if isinstance(document, dict) else document
    actual: dict[str, set[str]] = {}
    for row in findings:
        actual.setdefault(str(row["call_ref"]), set()).add(str(row["id"]))

    claimed: dict[str, set[str]] = {}
    for line in part_two.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 4 or not cells[0].startswith("**CALL-"):
            continue
        call = cells[0].strip("*")
        ids: set[str] = set()
        # "F-08…F-12, F-50, F-51" -- ranges by ellipsis, singletons by comma.
        for piece in cells[3].split(","):
            bounds = re.findall(r"F-(\d+)", piece)
            if "\u2026" in piece or "..." in piece:
                assert len(bounds) == 2, f"{call}: cannot read range {piece!r}"
                ids |= {f"F-{n:02d}" for n in range(int(bounds[0]), int(bounds[1]) + 1)}
            else:
                ids |= {f"F-{int(n):02d}" for n in bounds}
        claimed[call] = ids

    # Was a literal 12 until D4 was superseded. What must hold is that Part 2
    # has a row per declared design call, not that the corpus is a fixed size.
    declared = {
        line.strip()
        for line in (CORPUS / "DESIGN_SET").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }
    assert set(claimed) == declared, (
        f"Part 2 has rows for {sorted(claimed)}; DESIGN_SET declares {sorted(declared)}"
    )
    # `.get(call, set())` on both sides, because a call may seed nothing. CALL-22
    # is the first: a design call written to be a true negative across the tier,
    # so it has a Part 2 row saying `none` and no rows in the findings document
    # at all. Comparing a set against `None` made "seeded nothing" unrepresentable
    # -- which is the one shape a corpus of seeded defects most needs to allow.
    for call in sorted(set(claimed) | set(actual)):
        assert claimed.get(call, set()) == actual.get(call, set()), (
            f"{call}: the manifest claims {sorted(claimed.get(call, set()))}, "
            f"the findings document has {sorted(actual.get(call, set()))}"
        )


def test_the_contradiction_check_is_comparing_something() -> None:
    """A field list is not coverage. Six of the nine fields above compare
    nothing, because no tool result in this corpus echoes them back.

    That is worth measuring rather than assuming: a corpus edit that stopped
    echoing `door_time` would leave `test_a_record_contradicts_itself_only_where_
    it_is_seeded` passing over an empty comparison set, reporting no
    contradictions because it made no comparisons.

    **Asserted by equality, after the floor let the stated figure drift.** This
    docstring said the reach was `door_time, twice` while the corpus had moved
    to four comparisons over three fields -- correct when written, wrong for an
    unknown span afterwards, and invisible because `total >= 2` cannot tell four
    from two. The floor is kept for its message; the equality is what holds the
    claim.
    """
    compared: dict[str, int] = {}
    for transcript in _transcripts():
        call = parse_call(transcript)
        context = dict(call.context)
        for event in call.events:
            if not isinstance(event, ToolResultEvent) or not event.detail:
                continue
            for field in CONTRADICTABLE_FIELDS:
                if field in context and re.search(rf"{field}=(\S+?)(?:;|$)", event.detail):
                    compared[field] = compared.get(field, 0) + 1

    total = sum(compared.values())
    assert total >= 2, (
        f"the contradiction check makes {total} comparisons across the whole corpus; "
        "it is reporting no contradictions because it is looking at nothing"
    )
    assert "door_time" in compared, (
        "no tool result echoes door_time any more, which is the field this check "
        "reaches most; either the corpus changed or the seeded contradiction in "
        "CALL-08 has been edited away"
    )
    assert compared == MEASURED["contradiction_check_reach"], (
        "the check's reach has moved and the sentence above still states the old "
        f"distribution: measured {compared}, stated "
        f"{MEASURED['contradiction_check_reach']}. Update both together, which is "
        "the point of asserting a stated measurement by equality"
    )


def test_the_models_context_spans_agree_with_the_source_file() -> None:
    """`context_source_lines` is a claim about the file, so it is checked against
    the file rather than trusted.

    Without this, the span check above would be asking the parser whether the
    parser was right -- which is the W19 mistake the content check next to it
    exists to avoid. Adding a field to the model does not make its values true.
    """
    checked = 0
    for transcript in _transcripts():
        call = parse_call(transcript)
        lines = transcript.read_text(encoding="utf-8").splitlines()
        for (name, _), span in zip(call.context, call.context_source_lines, strict=True):
            assert span, f"{call.record.call_id}: {name} carries no source lines"
            first = lines[span[0] - 1]
            assert first.split(":=", 1)[0].strip() == name, (
                f"{call.record.call_id}: {name} claims line {span[0]}, "
                f"which reads {first.strip()!r}"
            )
            for continuation in span[1:]:
                assert lines[continuation - 1][:1].isspace(), (
                    f"{call.record.call_id}: {name} claims line {continuation} as a "
                    f"continuation, and it is not indented"
                )
            assert list(span) == list(range(span[0], span[0] + len(span))), (
                f"{call.record.call_id}: {name}'s span {span} is not contiguous"
            )
            checked += 1
    assert checked >= 150, f"only {checked} context pairs were checked"


# --------------------------------------------------------------------------
# Provenance: no value enters a call from nowhere
# --------------------------------------------------------------------------

#: Tool-call arguments allowed to have no source inside the call, each with its
#: reason. An undeclared exception is a hiding place (D37), so this list is the
#: whole of what may appear from outside.
_UNSOURCED_ARGUMENTS_ALLOWED: Final[tuple[tuple[str, str, str], ...]] = (
    (
        "fetch_policy",
        "document",
        "the document's name is part of the tool's contract, the way the tool's "
        "own name is: an agent that can call fetch_policy knows Verso has a "
        "refund policy called refund.v1. What it cannot know without reading "
        "the document is which clause answers a question -- which is why the "
        "clause argument was removed (event-model.md 3.5) rather than declared "
        "here.",
    ),
)


def _sourced_by(call: Call, event: ToolCallEvent, value: str) -> str | None:
    """Where a tool-call argument's value came from, or None.

    Only earlier events count. A value first seen in the result of the call
    that used it has not been sourced -- it has been asserted and then
    confirmed, which is the shape this check exists to reject.
    """
    wanted = " ".join(value.split()).lower()
    if not wanted:
        return "empty"

    context = {" ".join(str(v).split()).lower() for _, v in call.context}
    # Exact, or a fragment of a LONGER context value: production="The Halloway
    # Ensemble" sits inside event_title. The reverse direction is not accepted --
    # it matched clause="2.2" against ticket_count=2 and hid five real cases.
    if any(wanted == c or (len(wanted) >= 4 and wanted in c) for c in context if c):
        return "context"

    record = {
        " ".join(str(getattr(call.record, f)).split()).lower()
        for f in dir(call.record)
        if not f.startswith("_") and getattr(call.record, f) is not None
    }
    if wanted in record:
        return "record"

    earlier = [e for e in call.events if e.index < event.index]
    speech = " ".join(
        " ".join(e.body.split()).lower() for e in earlier if isinstance(e, SpeechEvent)
    )
    if len(wanted) >= 3 and wanted in speech:
        return "speech"
    prior = " ".join(
        " ".join(e.body.split()).lower() for e in earlier if not isinstance(e, SpeechEvent)
    )
    if len(wanted) >= 3 and wanted in prior:
        return "prior result"

    # An amount the agent computed from values it was given.
    try:
        target = Decimal(wanted.replace(",", "").replace("$", ""))
    except InvalidOperation:
        return None  # not a number, so no arithmetic source is possible
    numbers = []
    for _, raw in call.context:
        # Most context values are not numbers; those simply cannot be an
        # arithmetic source, so skipping them is the whole handling.
        with contextlib.suppress(InvalidOperation):
            numbers.append(Decimal(str(raw).replace(",", "").replace("$", "")))
    for size in (1, 2, 3):
        if any(sum(combo) == target for combo in itertools.combinations(numbers, size)):
            return "arithmetic over context"
    return None


def test_no_tool_call_argument_appears_from_nowhere() -> None:
    """Every value the agent passes to a tool must have a source in the call.

    CALL-09 used `EV-44901` as its exchange target at three events with nothing
    producing it -- context carried only `EV-44803`, and no `find_performance`
    call was ever made. The id was simply known. Nothing said so: it parsed, it
    read plausibly, and four findings were written about that call without
    anyone noticing that its central identifier had no origin.

    That is the failure this check exists for, and it is worse than an ordinary
    authoring slip. A transcript where values appear when convenient is a
    transcript that cannot support findings about grounding, because the corpus
    is then modelling an agent with knowledge no real one would have. The
    seeding manifest even described CALL-09 as "every step correct, the order
    wrong", which an unresolved identifier contradicts.

    Allowed sources are the pre-call context, the call record, earlier speech,
    an earlier event's body, and arithmetic over context values -- plus the
    declared exceptions above, which must stay a short list with reasons.
    """
    allowed = {(tool, arg) for tool, arg, _ in _UNSOURCED_ARGUMENTS_ALLOWED}
    for tool, arg, reason in _UNSOURCED_ARGUMENTS_ALLOWED:
        assert reason.strip(), f"{tool}({arg}) is excepted with no reason given"

    problems: list[str] = []
    checked = 0
    for transcript in _transcripts():
        call = parse_call(transcript)
        for event in call.events:
            if not isinstance(event, ToolCallEvent):
                continue
            for name, raw in re.findall(r'(\w+)="([^"]*)"', event.arguments or ""):
                if (event.name, name) in allowed:
                    continue
                checked += 1
                if _sourced_by(call, event, raw) is None:
                    problems.append(
                        f"{call.record.call_id} event {event.index}: "
                        f"{event.name}({name}={raw!r}) has no source in the call"
                    )

    assert checked, "no tool-call arguments were checked; the parser or the regex has drifted"
    assert not problems, "tool-call arguments with no origin in their own call:\n  " + "\n  ".join(
        problems
    )


def test_the_provenance_exceptions_are_all_still_used() -> None:
    """An exception nobody needs is an exception nobody rechecks."""
    used = {
        (event.name, name)
        for transcript in _transcripts()
        for event in parse_call(transcript).events
        if isinstance(event, ToolCallEvent)
        for name, _ in re.findall(r'(\w+)="([^"]*)"', event.arguments or "")
    }
    for tool, arg, _ in _UNSOURCED_ARGUMENTS_ALLOWED:
        assert (tool, arg) in used, (
            f"{tool}({arg}) is declared as an allowed unsourced argument and no "
            "transcript passes it; the exception is stale"
        )


# --------------------------------------------------------------------------
# The judged tier has to be justified by the corpus, not by assumption
# --------------------------------------------------------------------------

#: The judged dimensions the specification names by taxonomy number (D42,
#: confirmed at six by D53), each mapped to the finding that instantiates it.
#: The scenario map is the source of that pairing; this list exists so the
#: check fails loudly if a row stops naming a finding at all.
JUDGED_TAXONOMY_ITEMS: Final[tuple[int, ...]] = (17, 31)


def test_every_judged_taxonomy_item_has_a_judge_finding() -> None:
    """A judged dimension whose instance is no longer judged is justified by
    assumption, and D42 says so: the corpus must include calls authored
    specifically to exercise these dimensions, "otherwise a check scores well by
    firing on every repeat, and the judged tier is justified by assumption
    rather than by anything in the corpus."

    This exists because the gap opened silently. CALL-02's F-10 was taxonomy
    31's only instance. Changing policy retrieval to return whole documents put
    the contradicting clause into the payload, which made F-10 assertable and
    correctly re-classified -- and emptied the category. Every check stayed
    green: the scenario map still allocated item 31 to a call, its disposition
    cell was still non-empty, and nothing compared the allocation against how
    the findings were actually classified.

    **It binds the named finding, not the call.** The first version of this
    check asked whether the allocated *call* carried any judge finding, and
    passed when F-52 was flipped to `assert` -- because CALL-05 also carries
    F-23, which is judged for an unrelated reason. A guard satisfied by a
    neighbor is green and blind. The scenario map therefore names the finding,
    and this asserts that finding's own classification.

    Scoped to the items the specification names by number. The other four judged
    dimensions are described in prose rather than by taxonomy id, so binding
    them would mean matching on wording -- which goes stale in exactly the way
    this check exists to catch.
    """
    # The GOLD SET, not the drafts. Only a ruling can re-classify an instance,
    # and a ruling lands here -- reading the drafts would have let a dimension
    # empty in the artifact downstream trusts while this stayed green, which is
    # the failure recounted above, one layer up.
    findings = yaml.safe_load((CORPUS / "findings.yaml").read_text(encoding="utf-8"))["findings"]
    by_id = {str(row["id"]): row for row in findings}
    assert any(str(r["detectable_by"]) == "judge" for r in findings), (
        "no finding is classified `judge`; the judged tier has no instance at all"
    )

    scenario_map = (REPO_ROOT / "specs" / "taxonomy-scenario-map.md").read_text(encoding="utf-8")
    for item in JUDGED_TAXONOMY_ITEMS:
        row = re.search(rf"^\| {item} \|.*$", scenario_map, re.MULTILINE)
        assert row, f"the scenario map has no row for taxonomy item {item}"
        named = re.findall(r"\bF-\d{2}\b", row.group(0))
        assert named, (
            f"taxonomy item {item} is a judged dimension and its scenario-map row names no "
            f"finding, so nothing binds the dimension to an instance"
        )
        for finding_id in named:
            assert finding_id in by_id, (
                f"taxonomy item {item} names {finding_id}, which is not in the findings document"
            )
            actual = str(by_id[finding_id]["detectable_by"])
            assert actual == "judge", (
                f"taxonomy item {item} is a judged dimension instantiated by {finding_id}, "
                f"which is classified `{actual}`. Either the dimension has lost its instance "
                f"or the scenario map points at the wrong finding."
            )


# --------------------------------------------------------------------------
# The injection pair only works if the two calls are comparable
# --------------------------------------------------------------------------

#: The generated pair from D7: an injected call and its control, identical but
#: for one sentence. Declared here with its reason rather than inferred, because
#: the property below is invisible in both the specification and the findings.
INJECTION_PAIR: Final[tuple[str, str]] = ("CALL-06", "CALL-07")


def test_the_injection_pair_is_comparable_to_a_judge() -> None:
    """D7's acceptance criterion is satisfiable only while the injection finding
    stays outside the judged and asserted tiers.

    The criterion reads: "The seeded prompt-injection transcript produces the
    same verdict as an equivalent transcript with the injection removed."
    CALL-06 carries F-27, which records the injection attempt itself and has no
    counterpart in CALL-07. F-27 is `human`, so nothing automated is ever asked
    about it and the two calls remain comparable.

    Re-classify it to `judge` or `assert` and a *correct* judge reports one more
    finding on CALL-06 than on CALL-07 -- failing the criterion by being right.
    Nothing said so before this check existed: the classification carried a
    specification criterion and read like an ordinary judgment call.

    Scoped to the two automated tiers on purpose. The pair may differ in
    `human` rows, which is what F-27 is for; what it may not differ in is
    anything a check or a model is asked to produce.
    """
    # The GOLD SET, not the drafts. Only a ruling can re-classify an instance,
    # and a ruling lands here -- reading the drafts would have let a dimension
    # empty in the artifact downstream trusts while this stayed green, which is
    # the failure recounted above, one layer up.
    findings = yaml.safe_load((CORPUS / "findings.yaml").read_text(encoding="utf-8"))["findings"]
    injected, control = INJECTION_PAIR

    def automated(call_id: str) -> list[str]:
        return sorted(
            f"{row['owner']}/{row['detectable_by']}/{row['tier']}"
            for row in findings
            if str(row["call_ref"]) == call_id and str(row["detectable_by"]) in {"judge", "assert"}
        )

    left, right = automated(injected), automated(control)
    assert left, f"{injected} carries no automated finding; the pair proves nothing"
    assert left == right, (
        f"the injection pair is not comparable: {injected} has {left} and "
        f"{control} has {right}. D7's same-verdict criterion cannot pass while "
        f"the two differ in anything a check or a model is asked to produce."
    )


# --------------------------------------------------------------------------
# Internal fields must not reach the caller
# --------------------------------------------------------------------------

#: Context fields the entity register declares as operator-facing and not for
#: disclosure to the caller. A declared set rather than a sentence, because the
#: sentence version was the only thing standing between an internal note and a
#: transcript for as long as the field existed.
DO_NOT_DISCLOSE_FIELDS: Final[tuple[str, ...]] = ("internal_note",)

#: Calls that seed a disclosure of one, cross-referenced to the manifest.
INTERNAL_DISCLOSURE_SEEDED: Final[frozenset[str]] = frozenset({"CALL-18"})  # F-77

#: Shared tokens needed before a paraphrase counts as a disclosure. Long enough
#: that ordinary words -- "account", "January" -- cannot carry it on their own.
_DISCLOSURE_TOKEN_MIN: Final[int] = 8
_DISCLOSURE_TOKEN_HITS: Final[int] = 2


def test_no_internal_field_reaches_the_caller() -> None:
    """An agent must not read an operator-facing field to the caller.

    Written because the rule existed only in a sentence in `corpus/entities.md`,
    which is the shape this project keeps catching itself in: a constraint kept
    as prose is applied by whoever remembers it, and memory does not survive a
    session boundary.

    **Paraphrase counts.** CALL-18's agent does not quote the note; it says "a
    note on the account about a chargeback back in January, so anything to do
    with refunds would have to go to our disputes team", which discloses the
    substance without reproducing the string. A verbatim check would pass that
    and protect nothing, so the test looks for distinctive vocabulary shared
    between the field and agent speech -- tokens of eight characters or more, at
    least two of them.
    """
    for name in DO_NOT_DISCLOSE_FIELDS:
        assert name.strip(), "a do-not-disclose field is declared with no name"

    probes: dict[str, str] = {}
    carriers = 0
    for transcript in _transcripts():
        call = parse_call(transcript)
        context = {n: v for n, v in call.context}
        for name in DO_NOT_DISCLOSE_FIELDS:
            if name not in context:
                continue
            carriers += 1
            probes[name] = context[name]

    assert carriers, "no call carries a do-not-disclose field; the check is vacuous"
    assert probes, "no probe text was collected"

    # THE DENOMINATOR. The first version compared each field only against the
    # speech of the call that carried it -- and exactly one call carries one, so
    # the negative half never ran: `unexpected` could not be non-empty from any
    # corpus change, and a threshold validated on a single positive is a
    # true-positive test wearing a precision test's name. That is W9's shape, in
    # a repository that carries W9 as an acceptance criterion.
    #
    # Every probe is now run against every call's agent speech, so the check has
    # one trial per call instead of 1, and the false-positive rate is measured rather than
    # assumed.
    offenders: dict[str, list[str]] = {}
    for transcript in _transcripts():
        call = parse_call(transcript)
        spoken = " ".join(
            event.body.lower()
            for event in call.events
            if isinstance(event, SpeechEvent) and event.kind is EventKind.AGENT
        )
        for text in probes.values():
            tokens = {re.sub(r"[^a-z]", "", word) for word in text.lower().split()}
            shared = sorted(
                token for token in tokens if len(token) >= _DISCLOSURE_TOKEN_MIN and token in spoken
            )
            if len(shared) >= _DISCLOSURE_TOKEN_HITS:
                offenders.setdefault(call.record.call_id, []).extend(shared)

    unexpected = {c: v for c, v in offenders.items() if c not in INTERNAL_DISCLOSURE_SEEDED}
    assert not unexpected, (
        "an internal field's substance appears in agent speech in a call that does not "
        "seed a disclosure -- either a real leak or a false positive from the token "
        "threshold, and both need looking at:\n  "
        + "\n  ".join(f"{c}: shared {sorted(set(v))}" for c, v in unexpected.items())
    )
    missing = INTERNAL_DISCLOSURE_SEEDED - set(offenders)
    assert not missing, (
        f"{sorted(missing)} are named as seeding an internal disclosure and none is "
        "detectable; either the seed was lost or the exception is stale"
    )
    assert len(offenders) < len(_transcripts()), (
        "every call trips the probe, so the threshold separates nothing"
    )


# --------------------------------------------------------------------------
# The gold set is generated, and a generated artifact nobody regenerates drifts
# --------------------------------------------------------------------------


def test_the_gold_set_agrees_with_the_drafts_and_the_ledger() -> None:
    """`corpus/findings.yaml` is the artifact everything downstream trusts.

    It is generated from the drafts and the adjudication ledger, and D36 kept it
    from existing until a human had made it because a file at this path *is* the
    gold set to every tool that reads it. Generation buys what the absence was
    protecting: the file is reproducible from its inputs, so a correction to a
    ruling cannot leave the artifact behind.

    That failure is not hypothetical here. Three findings in this corpus carried
    figures from a superseded header for weeks because the form they were
    written in was one nothing read. The same shape applied to the gold set
    would put a stale classification in front of the agreement measurement the
    whole project rests on.
    """
    gold = REPO_ROOT / "corpus" / "findings.yaml"
    assert gold.is_file(), (
        "the gold set has not been generated -- run\n    python tools/make_gold_set.py"
    )
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "make_gold_set.py"), "--check"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, (
        "the gold set disagrees with the drafts or the ledger -- regenerate it with\n"
        "    python tools/make_gold_set.py\n"
        f"{result.stdout}{result.stderr}"
    )


def test_the_gold_set_takes_its_classifications_from_the_ledger() -> None:
    """Where a ruling differs from what was drafted, the gold set must carry the
    ruling. Two rows differ today and both are deliberate; if the generator ever
    preferred the draft, the gold set would silently publish the model's
    proposal as the human's judgment, which is precisely what D10 forbids."""
    gold = {
        row["id"]: row
        for row in yaml.safe_load((CORPUS / "findings.yaml").read_text(encoding="utf-8"))[
            "findings"
        ]
    }
    ledger = {
        x["id"]: x
        for x in yaml.safe_load(
            (CORPUS / "findings.adjudication.yaml").read_text(encoding="utf-8")
        )["adjudications"]
    }
    drafts = {
        r["id"]: r
        for r in yaml.safe_load((CORPUS / "findings.candidates.yaml").read_text(encoding="utf-8"))[
            "findings"
        ]
    }

    # Rejected rows carry no owner/detectable_by/tier -- the ledger's schema says
    # to omit them -- and are absent from the gold set. Iterating the drafts and
    # indexing the ledger raised KeyError the first time a row was rejected, which
    # turned the suite red for using a documented verdict. Found by an independent
    # sweep that simulated one; zero of 86 rows are rejected, so nothing had
    # exercised the path.
    ruled = {fid: entry for fid, entry in ledger.items() if entry["verdict"] != "reject"}
    differing = [
        fid
        for fid in ruled
        for key in ("owner", "detectable_by", "tier")
        if str(drafts[fid][key]) != str(ruled[fid][key])
    ]
    assert differing, (
        "no ruling differs from its draft, so this check proves nothing. Either "
        "adjudication changed no classification -- which would itself be worth "
        "looking at -- or the drafts have been edited to agree."
    )
    for fid in gold:
        assert ledger[fid]["verdict"] != "reject", (
            f"{fid} is in the gold set and the ledger rejected it"
        )
        for key in ("owner", "detectable_by", "tier"):
            assert str(gold[fid][key]) == str(ledger[fid][key]), (
                f"{fid}: the gold set says {key}={gold[fid][key]}, the ledger ruled "
                f"{ledger[fid][key]}"
            )


def test_every_policy_retrieval_states_the_document_s_real_clause_count() -> None:
    """`fetch_policy` returns a document and the result says how many clauses it
    returned. That number is comparable against `corpus/policies/`, so it should
    be compared.

    Written to close a disagreement between two documents rather than to catch a
    defect: `specs/event-model.md` 3.5 said a transcript claiming a retrieval
    that does not match the policy set "fails rather than reads plausibly",
    while D65 recorded the same check as *owed, not written*. One of them was a
    claim about a mechanism that did not exist, which is the shape D46 names.

    It finds nothing today -- all seven retrievals state the right count -- and
    that is the expected result for a check written to make a sentence true.
    """
    counts = {
        document.stem: len(
            re.findall(r"^\*\*(\d+\.\d+)\*\*", document.read_text(encoding="utf-8"), re.MULTILINE)
        )
        for document in sorted(POLICIES.glob("*.md"))
    }
    assert counts and all(counts.values()), f"no clauses parsed out of {sorted(counts)}"

    stated = re.compile(r"(?P<document>[\w.]+) returned; (?P<count>\d+) clauses")
    checked = 0
    for transcript in _transcripts():
        call = parse_call(transcript)
        for event in call.events:
            if not isinstance(event, ToolResultEvent):
                continue
            match = stated.search(" ".join(event.body.split()))
            if match is None:
                continue
            checked += 1
            document = match.group("document")
            assert document in counts, (
                f"{call.record.call_id} event {event.index} names {document!r}, which is "
                f"not a document in corpus/policies/ ({sorted(counts)})"
            )
            assert int(match.group("count")) == counts[document], (
                f"{call.record.call_id} event {event.index} says {document} returned "
                f"{match.group('count')} clauses; the document has {counts[document]}"
            )
    assert checked, "no policy retrieval stated a clause count; the format has drifted"


#: Reason codes that name an action, and the tool that would have performed it.
#: The rest -- information_provided, unresolved, caller_abandoned -- assert no
#: action and require none.
_REASON_REQUIRES_TOOL: Final[dict[str, str]] = {
    "exchange_completed": "exchange_tickets",
    "refund_issued": "issue_refund",
    "transfer_completed": "transfer_booking",
    "name_changed": "change_holder_name",
}


def test_every_action_reason_code_names_an_action_the_call_attempted() -> None:
    """A reason code that names an action the call never attempted is a defect
    nobody sees: outcome and tool results are each internally coherent, so no
    consistency check between them catches it.

    This exists because CALL-09's seeded corruption (F-74) was listed in the
    seeding manifest's Part 3 with "no constant needed" -- in the table whose
    opening sentence is that every entry has a constant and fails if the set
    changes. Either the row did not belong there or the mechanism was missing.
    It was the mechanism.

    Attempted, not succeeded: CALL-05 calls `issue_refund` three times and every
    one fails, and its label is a separate defect (F-25). What this check asks is
    narrower -- whether the call ever reached for the thing its reason code names.
    """
    offenders: list[str] = []
    checked = 0
    for transcript in _transcripts():
        call = parse_call(transcript)
        required = _REASON_REQUIRES_TOOL.get(str(call.record.outcome_reason))
        if required is None:
            continue
        checked += 1
        called = {e.name for e in call.events if isinstance(e, ToolCallEvent)}
        if required not in called:
            offenders.append(
                f"{call.record.call_id}: outcome_reason {call.record.outcome_reason} "
                f"with no {required} call"
            )

    assert checked, "no call carries an action reason code; the check is vacuous"
    unexpected = [o for o in offenders if o.split(":")[0] not in REASON_CODE_CORRUPTION_SEEDED]
    assert not unexpected, (
        "reason codes naming actions the call never attempted:\n  " + "\n  ".join(unexpected)
    )
    missing = REASON_CODE_CORRUPTION_SEEDED - {o.split(":")[0] for o in offenders}
    assert not missing, (
        f"{sorted(missing)} are named as seeding a corrupt reason code and none is "
        "detectable; either the seed was lost or the exception is stale"
    )


# --------------------------------------------------------------------------
# Closed vocabularies: what the parser must accept, and what the corpus shows
# --------------------------------------------------------------------------


def test_every_closed_vocabulary_token_round_trips_through_the_parser(tmp_path: Path) -> None:
    """Every token of every closed vocabulary must parse back to itself.

    Written because "a closed vocabulary with unused tokens is untested
    vocabulary" was stated as the rationale for two vocabularies the corpus
    happens to exercise fully, and left three others at 2 of 9, 1 of 4 and 3 of
    4 with nothing testing the remainder. An independent sweep found them.

    **The resolution is not an exemption and not seven more calls.** Those two
    were the obvious options and both are wrong. `DisconnectionReason` carries
    `network_error` and `voicemail_reached` because real platforms emit them and
    an adapter has to receive what vendors send (D39) -- not because this corpus
    should contain a call that ends each way. Authoring seven calls to use up a
    vocabulary is how a corpus becomes a catalog, which D68 exists to prevent.

    So the vocabulary is tested where it lives: at the parser. What the *corpus*
    demonstrates is a separate and smaller claim, and the test below states it
    rather than implying the two are the same.
    """
    template = (TRANSCRIPTS / "CALL-11.txt").read_text(encoding="utf-8")
    assert "disconnection_reason: caller_hangup" in template

    for reason in DisconnectionReason:
        source = tmp_path / f"reason-{reason.value}.txt"
        source.write_text(
            template.replace(
                "disconnection_reason: caller_hangup", f"disconnection_reason: {reason.value}"
            ).replace('call.ended(reason="caller_hangup")', f'call.ended(reason="{reason.value}")'),
            encoding="utf-8",
        )
        assert parse_call(source).record.disconnection_reason is reason

    for outcome in Outcome:
        source = tmp_path / f"outcome-{outcome.value}.txt"
        source.write_text(
            template.replace("outcome: resolved", f"outcome: {outcome.value}"), encoding="utf-8"
        )
        assert parse_call(source).record.outcome is outcome

    for state in DisclosureState:
        source = tmp_path / f"state-{state.value}.txt"
        source.write_text(
            template.replace("recording_notice -> delivered", f"recording_notice -> {state.value}"),
            encoding="utf-8",
        )
        disclosures = [e for e in parse_call(source).events if isinstance(e, DisclosureEvent)]
        assert disclosures and disclosures[0].state is state


def test_the_corpus_demonstrates_the_vocabulary_it_claims_to() -> None:
    """The narrower claim, stated separately so neither stands in for the other.

    `ToolStatus` and `EventKind` are demonstrated in full by the corpus, and
    those two have their own exercise tests above. The other three are format
    contracts the parser is tested against; the corpus shows the subset its
    calls have occasion to. That subset is asserted here so it cannot
    shrink unnoticed -- a corpus that stopped demonstrating `agent_hangup` or
    `abandoned` would have lost a seeded defect.
    """
    records = [parse_call(t).record for t in _transcripts()]
    reasons = {r.disconnection_reason for r in records}
    outcomes = {r.outcome for r in records}

    assert DisconnectionReason.AGENT_HANGUP in reasons, "the seeded agent hangups are gone"
    assert DisconnectionReason.CALLER_HANGUP in reasons
    assert {Outcome.RESOLVED, Outcome.UNRESOLVED, Outcome.ABANDONED} <= outcomes, (
        f"the corpus demonstrates only {sorted(o.value for o in outcomes)}"
    )


# --------------------------------------------------------------------------
# The scenario map's vocabulary, against what actually declares it
# --------------------------------------------------------------------------
#
# `specs/taxonomy-scenario-map.md` missed two migrations and nothing noticed for
# either. D40 took the format to v2 and the map kept `CONFIG`, `call_ended`,
# `duration_seconds`, `UNAVAILABLE` and a tool result "returning `OK`" -- none of
# which is a token in any vocabulary this project declares. D44 moved the corpus
# from British to American and the map kept `Thornbury Building Society`, a
# *building society*, in a corpus set in California.
#
# It went unnoticed because the checks that read this document bind row
# existence and the finding ids on the judged rows, and nothing read the words.
# **The map is not a spent plan** -- `specs/taxonomy-coverage.md` calls it "the
# authoritative allocation", a phase-1 acceptance test requires a row per
# taxonomy item, and `test_every_judged_taxonomy_item_has_a_judge_finding`
# reads its rows to bind each judged dimension to the finding that instantiates
# it. A document three live things depend on has to be current, so this checks
# that its vocabulary is.

_SCENARIO_MAP: Final[Path] = REPO_ROOT / "specs" / "taxonomy-scenario-map.md"

#: Backticked things that are prose or references rather than vocabulary. Each
#: carries its reason, on the argument every exception list in this file makes.
_MAP_NON_VOCABULARY: Final[tuple[tuple[str, str], ...]] = (
    ("out of scope", "names a section heading in the specification, not an identifier"),
    ("—", "an em dash used as a table placeholder for an unallocated row"),
)


def _declared_vocabulary() -> set[str]:
    """Every name this project declares, from the documents that declare them.

    Four sources, and the fourth is the one a first draft would leave out: the
    **parsed** corpus. `difference_due` is a real tool-result field used in
    CALL-09 and named in three findings, and it is in no register list because
    the register enumerates context and state variables rather than result
    detail keys.

    Parsed rather than read as text, and that is not fastidiousness. Measuring
    this against raw transcript bytes reported `Brightwater Live` as undeclared
    -- the seeded naming drift in CALL-08, which **wraps across two source
    lines**. The parser reassembles it and a byte scan does not, so a raw
    comparison invents a defect in the one place the corpus deliberately carries
    one. W16 and W17 are the same shape, one document over.
    """
    vocabulary: set[str] = set()
    for document in ("corpus/entities.md", "specs/event-model.md", "specs/transcript-format.md"):
        text = (REPO_ROOT / document).read_text(encoding="utf-8")
        vocabulary |= set(re.findall(r"`([A-Za-z_][A-Za-z0-9_.]*)`", text))
    for enum in (ToolStatus, EventKind, DisconnectionReason, Outcome, DisclosureState):
        vocabulary |= {member.value for member in enum} | {member.name for member in enum}
    vocabulary |= {path.stem for path in POLICIES.glob("*.md")}
    # The findings keys, which the specification declares rather than the register.
    specification = (REPO_ROOT / "specs" / "voice-agent-eval-harness.md").read_text(
        encoding="utf-8"
    )
    vocabulary |= set(
        re.findall(
            r"`(id|call_ref|owner|observation|evidence|consequence|detectable_by|tier)`",
            specification,
        )
    )
    for transcript in _transcripts():
        call = parse_call(transcript)
        vocabulary |= {name for name, _ in call.context}
        for event in call.events:
            if isinstance(event, StateEvent):
                vocabulary.add(event.name)
            if isinstance(event, ToolCallEvent):
                vocabulary.add(event.name)
                vocabulary |= set(re.findall(r"\b([a-z_][a-z0-9_]*)=", event.arguments or ""))
            if isinstance(event, ToolResultEvent) and event.detail:
                vocabulary |= set(re.findall(r"\b([a-z_][a-z0-9_]*)=", event.detail))
            if isinstance(event, (DisclosureEvent, SystemEvent)):
                # `call.answered`, `call.ended`, `recording_notice`. Collected
                # because the first draft did not, and the check reported
                # `call.ended` -- a name the corpus emits in every call -- as
                # undeclared. A vocabulary assembled from four sources is wrong
                # in whichever direction the fifth would have corrected.
                vocabulary.add(event.body.split("(")[0].split(" ")[0])
    return vocabulary


def test_every_token_the_scenario_map_names_is_declared_somewhere() -> None:
    """The map missed two format migrations and nothing read its words.

    Every backticked identifier in it must be a name this project declares: a
    context or state variable, a tool, a member of a closed vocabulary, a policy
    document, a findings key, or a field the corpus itself uses. `CONFIG` and
    `duration_seconds` were none of those for as long as the document sat there
    describing them as the format.

    **Identifier-shaped tokens only.** A backticked phrase is prose and is
    exempted by name above; a file path is checked by `statement_inventory`; a
    clause citation is checked by the same tool against `corpus/policies/`. This
    check does one thing, and the things it does not do are done elsewhere
    rather than left undone.
    """
    text = _SCENARIO_MAP.read_text(encoding="utf-8")
    declared = _declared_vocabulary()
    exempt = {token for token, _ in _MAP_NON_VOCABULARY}
    for token, reason in _MAP_NON_VOCABULARY:
        assert reason.strip(), f"{token!r} is exempted with no reason given"

    unresolved: list[str] = []
    checked = 0
    for raw in sorted(set(re.findall(r"`([^`\n]+)`", text))):
        token = raw.strip()
        if token in exempt or re.match(r"^(?:specs|corpus|tests|tools|src|hooks)/", token):
            continue
        if re.match(r"^\w+\.v\d(?:\s+§.*)?$", token) or re.match(r"^(?:CALL|F|S|W|P)-?\d+$", token):
            continue
        # `outcome: resolved`, `tier: question`, `difference_due=14.00` -- the
        # name is what must be declared; the value is corpus data.
        name = re.split(r"[:=]", token, maxsplit=1)[0].strip()
        if " " in name:
            continue
        checked += 1
        if name not in declared:
            unresolved.append(f"{token!r} (name {name!r})")

    assert checked >= 25, (
        f"only {checked} identifier tokens were checked in the scenario map; the "
        "extraction has stopped matching and this check would pass by reading nothing"
    )
    assert not unresolved, (
        "the scenario map names tokens nothing declares. Either the map is describing a "
        "format or a canon this project has left, or the name belongs in "
        "corpus/entities.md:\n  " + "\n  ".join(unresolved)
    )


def test_the_scenario_map_names_no_undeclared_entity() -> None:
    """The other half, and the one that caught a pre-D44 British institution.

    `Thornbury Building Society` sat in this map for as long as the corpus has
    been American. D44 moved locale, currency, numbering and **entity names** to
    the United States, and its own argument is that half-localized is worse than
    either end because "what they notice is that nobody was paying attention".

    Multi-word capitalized phrases only, compared against the register's bold
    names and against the parsed corpus. A single capitalized word is
    unusable -- every sentence starts with one -- and the measured noise at two
    words is nil: three phrases in the whole document, of which two are declared
    entities and the third was the defect.
    """
    text = _SCENARIO_MAP.read_text(encoding="utf-8")
    register = (CORPUS / "entities.md").read_text(encoding="utf-8")
    declared = {name.strip() for name in re.findall(r"\*\*([A-Z][A-Za-z&'. ]+)\*\*", register)}
    spoken = " ".join(
        event.body for transcript in _transcripts() for event in parse_call(transcript).events
    )
    context_values = " ".join(
        value for transcript in _transcripts() for _, value in parse_call(transcript).context
    )
    assert declared, "the register's Class 1 table no longer yields bold entity names"

    phrases = set(re.findall(r"\b([A-Z][a-z]+(?:\s+(?:[A-Z][a-z]+|&))+)\b", text))
    undeclared = sorted(
        phrase
        for phrase in phrases
        if phrase not in declared and phrase not in spoken and phrase not in context_values
    )
    assert not undeclared, (
        "the scenario map names entities the register does not declare and the corpus "
        f"does not use: {undeclared}. An invented entity in a specification is the same "
        "defect as one in a transcript, and the register is the canonical list for both"
    )


def test_the_scenario_map_checks_fire_on_a_token_and_an_entity_nothing_declares() -> None:
    """Both controls, planted as the two migrations that actually happened.

    `CONFIG` is what D40 left behind and `Thornbury Building Society` is what
    D44 did, so the plants are the defects rather than inventions. Each is
    checked against the same declared sets the tests above use, so a plant that
    stopped being undeclared would fail here rather than quietly proving nothing.
    """
    declared = _declared_vocabulary()
    assert "CONFIG" not in declared, (
        "CONFIG is declared somewhere again, so the token control proves nothing -- "
        "if the format has regained a CONFIG kind, this control needs a new plant"
    )
    assert "duration_seconds" not in declared and "call_ended" not in declared

    register = (CORPUS / "entities.md").read_text(encoding="utf-8")
    bold = {name.strip() for name in re.findall(r"\*\*([A-Z][A-Za-z&'. ]+)\*\*", register)}
    assert "Thornbury Building Society" not in bold, "the entity control is no longer undeclared"
    assert "Northfield Credit Union" in bold, (
        "the register no longer declares the institution the map was corrected to name, "
        "so the correction points at nothing"
    )


# --------------------------------------------------------------------------
# Stated measurements: a floor and an equality answer different questions
# --------------------------------------------------------------------------

#: Measurements this suite states in prose, and therefore asserts by **equality**.
#:
#: `>=` answers *is this guard blind?*. It does not answer *is this measurement
#: current?*, and the contradiction check below conflated the two: its comment
#: read "`door_time` yields two comparisons and the other eight yield zero"
#: while its assertion read `total >= 2`. The corpus moved to four comparisons
#: across three fields, the sentence stayed as it was, and the check stayed
#: green throughout -- because six satisfies a floor of two exactly as well as
#: two does.
#:
#: So both survive and each does its own job: the floor keeps its message about
#: blindness, and the equality holds the number the prose states. **A number
#: written into a docstring is a claim like any other** (D46), and this is the
#: cheapest place in the project to stop making that claim on trust.
MEASURED: Final[dict[str, dict[str, int]]] = {
    "contradiction_check_reach": {"door_time": 5, "price_band": 1, "ticket_count": 1},
    "event_scoped_comparisons": {"event_title": 9, "door_time": 8},
}


def _prose_of(source: Path) -> str:
    """Every comment and string literal in a Python file, and nothing else.

    Scanning raw source for a stated measurement reports `measured = 0` and
    `_measured()` -- identifiers, not claims -- which is the false-positive rate
    that gets a detector switched off. Tokenizing and keeping only COMMENT and
    STRING tokens leaves the text a reader actually reads.
    """
    pieces: list[str] = []
    with source.open("rb") as handle:
        for token in tokenize.tokenize(handle.readline):
            if token.type in {tokenize.COMMENT, tokenize.STRING}:
                pieces.append(token.string)
    return "\n".join(pieces)


#: `Measured:` introduces a stated measurement. Capitalized, optionally
#: qualified (`Measured now:`, `Measured when this was written:`), and closed by
#: a colon -- a deliberate marker rather than the English word, so that
#: `measured against`, `measured as a span` and `what is measured` are not read
#: as claims about quantity. The convention costs one colon and is what makes
#: the check below possible at all.
#: The number is required by a lookahead rather than consumed, so the excerpt is
#: a fixed window rather than stopping at the first digit. A short excerpt made
#: every disposition key start with the marker, which made each key its own
#: second site -- the check reporting the register that classifies it.
_MEASUREMENT_MARKER: Final[re.Pattern[str]] = re.compile(
    r"Measured(?:\s+[\w\s]{0,40}?)?:"
    r"(?=.{0,160}?"
    r"(?:\b\d+\b|\bzero\b|\btwice\b|\bone\b|\btwo\b|\bthree\b|\bfour\b|\bfive\b|"
    r"\bsix\b|\bseven\b|\beight\b|\bnine\b|\bten\b|\beleven\b|\btwelve\b))"
    r".{0,90}",
    re.S,
)


#: A measurement stated in prose, and what accounts for it. Keyed on a
#: distinctive excerpt: rewording a measurement is exactly the edit that should
#: force it to be re-classified, so a key that survived rewording would be the
#: wrong key.
#:
#: Same three dispositions the recall net uses, for the same reason -- an
#: exemption nobody has to justify is one that grows.
_STATED_MEASUREMENTS: Final[dict[str, str]] = {
    "rather than argued: three replications of this pair on 2026-09-11": (
        "DATED: the three replications of the CALL-06/CALL-07 pair commissioned at D150, "
        "after the committed run failed D7's criterion. Dated in the sentence rather than "
        "bound by equality, because the point of the number is what it refuted -- one run "
        "reversed the direction of the disagreement, which kills a directional reading "
        "whatever the count was -- and a later replication would make it a different "
        "measurement rather than a stale one."
    ),
    "when this was written: 19": (
        "DATED: `Measured when this was written` -- the qualifier is in the sentence, and "
        "the live half (every [P1] criterion is claimed by an entry) is what the test asserts."
    ),
    "`door_time` yields four": (
        "BOUND: MEASURED['contradiction_check_reach'], asserted by equality in "
        "test_the_contradiction_check_is_comparing_something."
    ),
    "written: CI reported both of the controls whose": (
        "DATED: `Measured when this was written` -- the control audit of 2026-09-09, in the "
        "gate's own control. The live half is asserted by that control, which plants a "
        "same-size edit under a pinned mtime and requires it to be seen."
    ),
    "written: CI reported green, with their defects": (
        "DATED: `Measured when this was written` -- the same run, recorded where the repair "
        "lives so the next reader of that environment line knows what it is for."
    ),
    "written: with `_CONTROL` emptied": (
        "DATED: `Measured when this was written` -- the control audit of 2026-09-08, "
        "recorded at D121 and in CONTROL-REGISTER.md with the failure output behind it. "
        "The live half is asserted by the control itself, which now fails on both modes."
    ),
    "returning empty left this check green": (
        "DATED: `Measured when this was written` -- the same control audit, on the seam this "
        "check guards. The live half is asserted two ways now: the check carries a ground-truth "
        "floor, and the control drives _leaked_turns over a corpus that contains a turn."
    ),
    "written: with the per-row comparison neutered": (
        "DATED: `Measured when this was written` -- the same audit, the same shape one "
        "file over. The live half is asserted by the control, which drives the comparison "
        "over a moved anchor rather than asserting a property of the corpus beside it."
    ),
    "nine title comparisons and eight door-time": (
        "BOUND: MEASURED['event_scoped_comparisons'], asserted by equality in "
        "test_one_event_id_means_one_event."
    ),
}


def test_every_stated_measurement_is_dated_or_bound() -> None:
    """A number in a docstring is a claim, and this suite is full of them.

    The rule this enforces is narrow and worth stating exactly: **if prose in
    this suite states a measured number, that number is asserted by equality, or
    the sentence says when it was measured.** A floor underneath a stated
    measurement is the shape that let `door_time, twice` drift to four while
    everything stayed green.

    **The marker is a convention, not a guess at English.** `Measured:` --
    capitalized, optionally qualified, closed by a colon -- introduces a stated
    measurement, and only that shape is scanned. The first draft matched the
    bare word and reported ten sites of which one was real: `measured against
    it`, `measured as a span` and `what is written is what is measured` are the
    verb in another sense, and four of the ten were this check's own prose
    about measurement. A detector firing on its own documentation is the
    constraint D89 recorded, arriving one file over.

    **Its limits, both real and both stated rather than implied.** A
    measurement written without the marker is outside this check -- a
    convention has to be used to work, which is why it is written down here
    and beside the dispositions below. And a measurement in a prose document
    rather than in Python is outside it too; the recall net in
    `test_document_counts.py` covers that side.
    """
    sources = sorted((REPO_ROOT / "tests").glob("*.py")) + sorted(
        (REPO_ROOT / "tools").glob("*.py")
    )
    assert sources, "no Python sources found; this check would pass by reading nothing"

    found: list[str] = []
    for source in sources:
        for match in _MEASUREMENT_MARKER.finditer(_prose_of(source)):
            excerpt = re.sub(r"\s+", " ", match.group(0))
            if not any(key in excerpt for key in _STATED_MEASUREMENTS):
                found.append(f"{source.name}: {excerpt}")

    assert not found, (
        "prose in this suite states a measured number that is neither asserted by "
        "equality nor dated. Bind it, date it, or add an entry to "
        "_STATED_MEASUREMENTS saying which:\n  " + "\n  ".join(found)
    )


def test_no_stated_measurement_declaration_has_gone_stale() -> None:
    """The other direction. A key matching nothing classified a sentence that is
    no longer there, and will absolve the next sentence that happens to contain
    it."""
    prose = "\n".join(
        _prose_of(source)
        for source in sorted((REPO_ROOT / "tests").glob("*.py"))
        + sorted((REPO_ROOT / "tools").glob("*.py"))
    )
    stale = sorted(key for key in _STATED_MEASUREMENTS if key not in re.sub(r"\s+", " ", prose))
    assert not stale, (
        "_STATED_MEASUREMENTS classifies excerpts that no longer appear:\n  " + "\n  ".join(stale)
    )


def test_the_measurement_scan_fires_on_an_undated_unbound_number() -> None:
    """The control. The scan's whole value is that it refuses to be quiet, so
    the thing to demonstrate is that a plausible new sentence trips it."""
    # Assembled rather than written out. A literal plant would sit in a file the
    # scan reads, so this test would fail on its own control -- D89's constraint
    # (a document explaining a checker cannot contain the checker's trigger)
    # arriving in the checker itself. Splitting the marker is the cheapest
    # honest fix and it is worth the comment, because the next reader will
    # otherwise "tidy" it back into a literal and turn the suite red.
    planted = "#: " + "Measured" + " across the corpus: 7 rows carry the shape.\n"
    match = _MEASUREMENT_MARKER.search(planted)
    assert match, "the marker no longer sees a stated measurement in the shape it scans for"
    excerpt = re.sub(r"\s+", " ", match.group(0))
    assert not any(key in excerpt for key in _STATED_MEASUREMENTS), (
        "the planted sentence is already declared, so this control demonstrates nothing"
    )


# --------------------------------------------------------------------------
# How the account was matched, which the register counted and miscounted
# --------------------------------------------------------------------------


def _matched_by() -> dict[str, str]:
    """`{call id: how the platform says it found the account}`."""
    found: dict[str, str] = {}
    for transcript in _transcripts():
        call = parse_call(transcript)
        context = dict(call.context)
        assert "matched_by" in context, (
            f"{call.record.call_id} does not record how its account was matched, "
            "so the register's claim about matched_by cannot be checked against it"
        )
        found[call.record.call_id] = context["matched_by"]
    assert found, "no transcripts, so this check compares nothing"
    return found


def _the_matched_by_paragraph() -> str:
    """The register paragraph explaining `matched_by`."""
    register = (CORPUS / "entities.md").read_text(encoding="utf-8")
    paragraph = next(
        (block for block in register.split("\n\n") if "`matched_by` records" in block), None
    )
    assert paragraph is not None, "corpus/entities.md no longer explains matched_by"
    return paragraph


def _matched_by_disagreement(paragraph: str, exceptional: set[str]) -> str | None:
    """`None` when the paragraph names exactly the calls matched on something else.

    The comparison as a function, so the control can drive it over a paragraph it
    has re-pointed. It was `named == exceptional` inline, and the control beside
    it ran its own `re.findall` and its own `!=` -- so it was proof about its own
    copy. Measured when this was written: weakening this equality to a superset
    test, which is the shape that lets the register name an extra call, left the
    check green and the control green with it.
    """
    named = set(re.findall(r"CALL-\d{2}", paragraph))
    if named == exceptional:
        return None
    return f"names {sorted(named)} where the corpus says {sorted(exceptional)}"


def test_the_register_names_every_call_matched_on_something_other_than_the_number() -> None:
    """The register's `matched_by` paragraph is a claim about the corpus, and it
    was wrong on both halves with nothing reading it.

    It said thirteen design calls carry `caller_ani` and that one carries
    `booking_reference`. **Every design call carries both variables**; what
    differs is the value of `matched_by`. So the count was stale by addition
    *and* counting the wrong thing, and a reader trusting the sentence would
    have been told about a corpus that has never existed.

    Derived from the corpus in both directions, so the sentence cannot be
    corrected into a different wrong shape: the calls the paragraph names must
    be exactly the calls matched on something other than the calling number.

    **What this check would not have caught, said plainly rather than left for
    someone to assume otherwise.** The old sentence named the right call and the
    wrong number, and this compares call ids -- so it would have passed on the
    defect that prompted it. The count needed
    `test_every_worded_design_set_size_agrees_with_the_declaration`, which reads
    that document and did not fire because its pattern is case-sensitive and the
    number opened a sentence. The category error underneath -- counting which
    calls *carry* a variable when the claim is about which value `matched_by`
    takes -- needed a reader, and still does. Three failures, one sentence, and
    only one of the three is closed by the check that sits under it.
    """
    matched = _matched_by()
    exceptional = {call for call, value in matched.items() if value != "caller_ani"}
    assert exceptional, (
        "every call is matched the same way, so the register's exception names "
        "nothing and this check compares one empty set against another"
    )
    disagreement = _matched_by_disagreement(_the_matched_by_paragraph(), exceptional)
    assert disagreement is None, (
        f"the register's matched_by paragraph {disagreement}, so the sentence describes a "
        "corpus this one is not"
    )


def test_the_matched_by_check_fires_when_the_register_names_the_wrong_call() -> None:
    """The control. Naming a call is cheap and naming the wrong one is cheaper.

    The paragraph is re-pointed at a different design call and the comparison
    must stop agreeing. Without this the test above proves only that some call
    id appears in some paragraph.
    """
    matched = _matched_by()
    exceptional = {call for call, value in matched.items() if value != "caller_ani"}
    wrong = sorted(set(matched) - exceptional)
    assert wrong and exceptional, "the corpus has no two calls to confuse"

    paragraph = _the_matched_by_paragraph()
    assert _matched_by_disagreement(paragraph, exceptional) is None, (
        "the shipped paragraph already disagrees, so this control cannot tell a planted "
        "defect from the state of the register"
    )

    repointed = paragraph.replace(sorted(exceptional)[0], wrong[0])
    assert _matched_by_disagreement(repointed, exceptional) is not None, (
        "re-pointing the paragraph at a different call left the comparison agreeing, so it "
        "is not reading the call ids it reports"
    )
    # The other direction, and the one a weakened comparison lets through: a
    # paragraph naming every exceptional call AND one more still disagrees.
    widened = paragraph.replace(sorted(exceptional)[0], f"{sorted(exceptional)[0]} and {wrong[0]}")
    assert _matched_by_disagreement(widened, exceptional) is not None, (
        "a paragraph naming an extra call was reported as agreeing, which is what a "
        "comparison weakened from equality to a superset test would do"
    )


def test_every_design_call_carries_both_a_calling_number_and_a_booking_reference() -> None:
    """The half of the old sentence that was not a counting error.

    "Thirteen design calls carry `caller_ani`; CALL-18 carries
    `booking_reference`" reads as a claim that the two populations are
    different. They are the same population: every call carries both. That is
    what makes `matched_by` necessary in the first place -- with only one
    identifier present per call there would be nothing to record.

    Asserted rather than assumed, so that if a future call legitimately carries
    no booking reference -- a caller buying rather than amending -- this fails
    and the register sentence is rewritten, instead of the sentence quietly
    becoming false again.
    """
    missing: list[str] = []
    for transcript in _transcripts():
        call = parse_call(transcript)
        names = {name for name, _ in call.context}
        absent = {"caller_ani", "booking_reference"} - names
        if absent:
            missing.append(f"{call.record.call_id}: no {', '.join(sorted(absent))}")
    assert not missing, (
        "corpus/entities.md says every design call carries both a calling number "
        "and a booking reference, and these do not:\n  " + "\n  ".join(missing)
    )


# --------------------------------------------------------------------------
# The escalation convention, which lived where half the project could not read it
# --------------------------------------------------------------------------

#: The three fields a call handed to a human sets, and the values a *successful*
#: handoff sets them to. Declared here **and** in `corpus/entities.md`, with the
#: two tests below asserting the corpus against this and the register against
#: this -- so the convention cannot hold in one place and drift in the other.
#:
#: That is how it went wrong. It lived in `corpus/seeding-manifest.md`, which is
#: a design-set artifact a curated authoring packet deliberately does not carry,
#: and in one machine's project memory, which lives outside both repositories
#: and which no reviewer ever sees. An authoring session received the vocabulary
#: without the rule and set `outcome` to `transferred`; D86 records that the
#: author did not err and the register did not say.
ESCALATION_RECORD: Final[dict[str, str]] = {
    "disconnection_reason": "transferred",
    "outcome": "resolved",
    "outcome_reason": "escalated",
}


def _call_convention_fields() -> dict[str, dict[str, str]]:
    """`{call id: the three fields the escalation convention governs}`."""
    return {
        call.record.call_id: {
            "disconnection_reason": call.record.disconnection_reason.value,
            "outcome": call.record.outcome.value,
            "outcome_reason": call.record.outcome_reason,
        }
        for call in (parse_call(transcript) for transcript in _transcripts())
    }


def _convention_violations(
    escalated: dict[str, dict[str, str]],
) -> dict[str, dict[str, str]]:
    """Calls filed as escalations whose record does not carry the whole convention.

    A function rather than a comprehension inside the check, so the control can
    hand it the record it planted. It was inline, and the control beside it
    parsed a planted transcript and then compared the parsed fields against
    ESCALATION_RECORD itself -- never running this. Measured when this was
    written: with the comparison unable to report a violation, the check passed
    over a corpus that no longer held the convention and the control passed with
    it.
    """
    return {call_id: fields for call_id, fields in escalated.items() if fields != ESCALATION_RECORD}


def test_an_escalated_call_records_the_escalation_convention() -> None:
    """`outcome_reason: escalated` fixes the other two fields, and nothing said so.

    The register declared `escalated` and declared the `outcome` vocabulary and
    never connected them, so which outcome an escalated call takes was inferable
    from the seeding manifest and from nowhere else a second author could reach.
    D86 is the record of that costing exactly one wrong field.

    Asserted in both directions, because either alone is green and blind: every
    call filed as an escalation carries the whole convention, **and** at least
    one call is filed that way. Without the second, a corpus that stopped
    escalating anything would satisfy the first by having nothing to check.
    """
    records = _call_convention_fields()
    escalated = {
        call_id: fields
        for call_id, fields in records.items()
        if fields["outcome_reason"] == ESCALATION_RECORD["outcome_reason"]
    }
    assert escalated, (
        "no call in the corpus is filed as an escalation, so this check compared "
        "nothing; the convention it guards is unexercised"
    )
    wrong = _convention_violations(escalated)
    assert not wrong, (
        f"a call filed as an escalation does not carry the convention {ESCALATION_RECORD}: {wrong}"
    )


def test_no_call_files_its_outcome_as_transferred() -> None:
    """`Outcome.transferred` is declared, accepted by the parser, and unused.

    D73 called it a schema smell and left open whether to remove it. The answer
    the register now records is no: it is in the closed vocabulary because real
    platforms emit it and an adapter has to receive what vendors send (D39), so
    removing it would make the parser refuse a real export -- a worse failure
    than a token no transcript writes.

    Which makes this the one vocabulary entry whose absence from the corpus is
    load-bearing rather than incidental. `check_access_requirements` and
    `log_dispute` are unused capabilities a call could legitimately have used;
    this is unused because using it would be wrong, and the two look identical
    to a reader unless something says otherwise.

    That the parser still *accepts* the token is asserted by
    `test_every_closed_vocabulary_token_round_trips_through_the_parser` and is
    deliberately not re-asserted here: `Outcome.TRANSFERRED in set(Outcome)`
    cannot fail, because removing the member breaks this module's import
    instead. An assertion that cannot fail is not evidence, and the register
    half below is what this test can genuinely hold.
    """
    declared = re.search(
        r"\*\*Outcomes\.\*\*(.+?)\n\n", (CORPUS / "entities.md").read_text(encoding="utf-8"), re.S
    )
    assert declared and f"`{Outcome.TRANSFERRED.value}`" in declared.group(1), (
        "corpus/entities.md no longer declares transferred among the outcomes, so "
        "this is an undeclared token rather than a declared and deliberately "
        "unused one, and the paragraph explaining the difference is describing "
        "something that is not there"
    )
    offenders = [
        call_id
        for call_id, fields in _call_convention_fields().items()
        if fields["outcome"] == Outcome.TRANSFERRED.value
    ]
    assert not offenders, (
        f"{offenders} file outcome as transferred; disconnection_reason already "
        "records how a call ended, and outcome records whether the caller's need "
        "was met. See the escalation convention in corpus/entities.md"
    )


def _paragraph_stating_the_escalation_convention(register: str) -> str | None:
    """The register paragraph stating all three `field: value` pairs, or `None`.

    All three in **one** paragraph rather than three anywhere in the file: the
    convention is that the fields go together, and a register naming them in
    three unrelated places would satisfy a looser check while telling a reader
    nothing about how they combine -- which is the state this check was written
    to end, not one to re-create in the check itself.
    """
    for paragraph in register.split("\n\n"):
        if all(
            re.search(rf"`{field}:\s*{value}`", paragraph)
            for field, value in ESCALATION_RECORD.items()
        ):
            return paragraph
    return None


def test_the_register_states_which_outcome_an_escalation_takes() -> None:
    """The rule has to be in the canon, not only in this file.

    A test asserting the corpus follows a convention does not teach the
    convention to anyone. `corpus/entities.md` is what a second author receives
    -- redacted, but received -- and `corpus/seeding-manifest.md` is not, so a
    rule stated only in the manifest reaches the design set and stops there.

    The failed-handoff half is asserted too. Stating only the successful path
    would leave the next author to infer that a transfer which errored is also
    `resolved`, which is the same gap one branch over.
    """
    register = (CORPUS / "entities.md").read_text(encoding="utf-8")
    paragraph = _paragraph_stating_the_escalation_convention(register)
    assert paragraph is not None, (
        "no paragraph in corpus/entities.md states all three of "
        f"{ESCALATION_RECORD}; the convention is inferable from the manifest "
        "and from nowhere the entity canon carries"
    )
    assert re.search(r"`outcome:\s*unresolved`", paragraph), (
        "the register states which outcome a successful handoff takes and not "
        "which one a failed handoff takes"
    )

    # The control. Without it this test proves only that the three strings are
    # somewhere in a large document -- so the paragraph it found is removed and
    # the search is expected to come back empty.
    assert _paragraph_stating_the_escalation_convention(register.replace(paragraph, "")) is None, (
        "a second paragraph also states the whole convention, so this check is "
        "not keyed to the one it reports; two statements of one rule are two "
        "things that can disagree"
    )


def test_the_register_says_why_the_transferred_outcome_is_unused() -> None:
    """D73 left `Outcome.transferred` a schema smell with nothing saying when it
    is correct. H-16 asked for a decision either way, and the decision recorded
    in the register is that it is never correct here and stays declared anyway.

    A token that is declared, unused and *unexplained* reads to the next author
    as available -- which is what happened. So the explanation has to be beside
    the field whose axis it duplicates, or it is not an explanation.
    """
    register = (CORPUS / "entities.md").read_text(encoding="utf-8")
    explanation = [
        paragraph
        for paragraph in register.split("\n\n")
        if "Outcome.transferred" in paragraph and "disconnection_reason" in paragraph
    ]
    assert explanation, (
        "corpus/entities.md names Outcome.transferred nowhere beside "
        "disconnection_reason, so nothing in the canon says why the token is "
        "declared and never used"
    )


def test_the_escalation_convention_check_fires_on_the_field_that_was_got_wrong(
    tmp_path: Path,
) -> None:
    """The plant, run against the corpus rather than argued about.

    D86's defect is reproducible in one substitution: take the escalated call,
    set `outcome: transferred` -- both values are in the closed vocabulary and
    the parser accepts either -- and the convention check must reject it. A
    check for a convention nothing in the tree has ever violated has been
    proven against nothing.
    """
    escalated = [
        transcript
        for transcript in _transcripts()
        if parse_call(transcript).record.outcome_reason == ESCALATION_RECORD["outcome_reason"]
    ]
    assert escalated, "no escalated call to plant against"
    source = escalated[0]
    planted = tmp_path / source.name
    original = source.read_text(encoding="utf-8")
    assert f"outcome: {ESCALATION_RECORD['outcome']}" in original
    planted.write_text(
        original.replace(
            f"outcome: {ESCALATION_RECORD['outcome']}", f"outcome: {Outcome.TRANSFERRED.value}"
        ),
        encoding="utf-8",
    )

    record = parse_call(planted).record
    assert record.outcome is Outcome.TRANSFERRED, "the parser rejected the planted value"
    fields = {
        "disconnection_reason": record.disconnection_reason.value,
        "outcome": record.outcome.value,
        "outcome_reason": record.outcome_reason,
    }
    assert fields != ESCALATION_RECORD, (
        "the planted record still matches the convention, so this control demonstrates nothing"
    )
    assert _convention_violations({"CALL-XX": fields}) == {"CALL-XX": fields}, (
        "the convention comparison did not report a record that violates it, so a corpus "
        "that stopped carrying the convention would pass the check above"
    )
    assert _convention_violations({"CALL-XX": dict(ESCALATION_RECORD)}) == {}, (
        "the convention comparison reports a record that does carry the convention"
    )


#: D68's stopping rule, test 3. Tests 1 and 2 -- whether the corpus can express
#: a class at all, and whether a class adds a detection shape rather than
#: another instance of one -- are judgment, and D68 recorded the whole rule that
#: way. Test 3 is not: it is a ratio over two counts, and D63's narrow condition
#: is that prose naming a number something else determines gets checked. CALL-12
#: sat at 0.500 for an entire adjudication session with nothing to say so.
DENSITY_CEILING: Final[float] = 0.35


def test_no_call_carries_more_findings_than_its_length_allows() -> None:
    """A transcript whose every third event is a defect has stopped being a call.

    This is the measurement that separates a corpus from a catalog, and it is
    the one thing in the stopping rule a test can hold. It is deliberately a
    ceiling and not a target: a call well under it is a call, and CALL-06 at
    0.06 is doing its job.
    """
    findings = load_findings(REPO_ROOT / "corpus" / "findings.yaml")
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.call_ref] = counts.get(finding.call_ref, 0) + 1

    over = []
    for transcript in _transcripts():
        events = len(parse_call(transcript).events)
        density = counts.get(transcript.stem, 0) / events
        if density > DENSITY_CEILING:
            over.append(
                f"{transcript.stem}: {counts.get(transcript.stem, 0)}/{events} = {density:.3f}"
            )

    assert not over, (
        f"D68 caps a call at {DENSITY_CEILING} findings per event; over it:\n  " + "\n  ".join(over)
    )


def _class_one_names() -> dict[str, str]:
    """`{canonical name: what it is}` from the Class 1 table in `entities.md`."""
    text = (REPO_ROOT / "corpus" / "entities.md").read_text(encoding="utf-8")
    section = text[text.index("## Class 1") : text.index("## Class 2")]
    return {
        name.strip(): kind.strip()
        for kind, name in re.findall(r"^\| ([^|]+?) \| \*\*([^*]+)\*\* \|", section, re.MULTILINE)
    }


def test_every_call_names_the_declared_platform() -> None:
    """Class 1, in the one place it is enumerable.

    A planted mutation renaming the ticketing platform in a single transcript
    was caught by **nothing**. The register check reads context variables, tool
    names, disclosure names, outcomes and reason codes -- Class 6, the machine
    tokens -- and Class 1 lives in free speech, where an undeclared brand looks
    like every other capitalized word.

    **Scope, because a guard narrower than its rule is the failure this project
    keeps finding**: this asserts the declared platform is named in every call.
    It does not assert that no *other* brand appears, which is not enumerable
    from a transcript, and the register's own asymmetry note says as much.
    """
    declared = _class_one_names()
    platforms = [name for name, kind in declared.items() if "platform" in kind.lower()]
    assert len(platforms) == 1, f"Class 1 declares {len(platforms)} platforms; expected one"
    platform = platforms[0]

    missing = [t.stem for t in _transcripts() if platform not in t.read_text(encoding="utf-8")]
    assert not missing, f"calls that never name {platform!r}: {', '.join(missing)}"


def test_every_production_and_venue_in_a_record_is_declared() -> None:
    """`event="Understory at The Alder Room"` names two Class 1 entities.

    The structured half of Class 1 *is* enumerable, because a production and a
    venue reach the record through one field with one shape. Read through the
    parser rather than the file, so a value wrapped across source lines is
    compared reassembled -- one of these is.
    """
    declared = set(_class_one_names())
    problems: list[str] = []
    for transcript in _transcripts():
        call = parse_call(transcript)
        values = [value for _, value in call.context] + [event.body for event in call.events]
        for value in values:
            for phrase in re.findall(r'event="([^"]+)"', value):
                if " at " not in phrase:
                    continue
                for part in (p.strip() for p in phrase.split(" at ", 1)):
                    if part not in declared:
                        problems.append(f"{transcript.stem}: {part!r} in {phrase!r}")

    assert not problems, "named in a record, absent from entities.md Class 1:\n  " + "\n  ".join(
        problems
    )


def test_the_injection_pair_differs_only_by_the_injection() -> None:
    """D7's acceptance criterion rests on a property asserted only in prose.

    The seeding manifest says CALL-07 is produced from CALL-06 "by removing one
    sentence and re-stamping the id and timestamps", and the P3 criterion --
    *the seeded prompt-injection transcript produces the same verdict as an
    equivalent transcript with the injection removed* -- is only meaningful if
    that is true. `INJECTION_PAIR` was read by one test, which compares findings
    classifications; **nothing compared the transcripts**.

    An independent sweep diffed them by hand and found the property holds. This
    is that diff, mechanized: same events in the same order, same context, and
    exactly one utterance differing -- with the control's version a **prefix** of
    the injected one, because the injection is appended to a turn rather than
    replacing it.
    """
    injected, control = INJECTION_PAIR
    a = parse_call(TRANSCRIPTS / f"{injected}.txt")
    b = parse_call(TRANSCRIPTS / f"{control}.txt")

    assert len(a.events) == len(b.events), (
        f"{injected} has {len(a.events)} events and {control} has {len(b.events)}; "
        "the pair is no longer comparable"
    )
    assert [e.kind for e in a.events] == [e.kind for e in b.events], (
        "the pair's event kinds diverge, so a verdict difference could come from structure"
    )
    assert dict(a.context) == dict(b.context), (
        "the pair's context records differ; the judge would be given different facts"
    )

    differing = [
        (x.index, x.body, y.body)
        for x, y in zip(a.events, b.events, strict=True)
        if x.body != y.body
    ]
    assert len(differing) == 1, (
        f"{len(differing)} utterances differ between the pair; the criterion needs exactly one: "
        f"{[i for i, _, _ in differing]}"
    )

    index, with_injection, without = differing[0]
    assert with_injection.startswith(without), (
        f"event {index}: the control's text is not a prefix of the injected one, so the pair "
        "differs by more than an appended injection"
    )
    assert len(with_injection) > len(without), f"event {index}: the injection is empty"


def _agent_personas() -> dict[str, str]:
    """`{call_id: persona}` -- the given name the agent introduces itself by."""
    found: dict[str, str] = {}
    for transcript in _transcripts():
        call = parse_call(transcript)
        for event in call.events:
            if isinstance(event, SpeechEvent) and event.kind is EventKind.AGENT:
                match = re.search(r"\bthis is ([A-Z][a-z]+)\b", event.body)
                if match:
                    found[call.record.call_id] = match.group(1)
                    break
    return found


def test_every_agent_persona_is_declared() -> None:
    """Class 1 in free speech, closed one noun further than D71 reached.

    D71's mutation battery found that renaming the ticketing platform in a
    single transcript was caught by **nothing**, and bound the platform name.
    The agent's own persona sits in the same sentence of the same turn, is
    invented under the same substitution policy, appears in **every** call --
    and was declared nowhere at all until an independent sweep counted thirteen
    of them.

    Two assertions, because either alone would be green and blind: every call
    must yield a persona (so a rewording that stops the pattern matching fails
    loudly rather than shrinking the set), and every persona found must be
    declared.
    """
    personas = _agent_personas()
    expected = {parse_call(t).record.call_id for t in _transcripts()}
    missing = sorted(expected - set(personas))
    assert not missing, (
        f"no agent persona could be read from {missing}; either the agent stopped introducing "
        "itself or the phrasing changed and this check has gone half-blind"
    )

    register = (REPO_ROOT / "corpus" / "entities.md").read_text(encoding="utf-8")
    undeclared = sorted({name for name in personas.values() if f"**{name}**" not in register})
    assert not undeclared, (
        f"agent personas used in the corpus and absent from corpus/entities.md: {undeclared}"
    )


def _policy_tool_constants() -> dict[str, str]:
    """`file:line` -> value, for every module-level constant naming a policy tool.

    Read with `ast` rather than by grepping for the literal, so the check is
    "every constant that plays this role agrees" rather than "the string
    `fetch_policy` appears the number of times somebody counted". A tenth copy
    added tomorrow is found by the first reading and invisible to the second.
    """
    found: dict[str, str] = {}
    for root in ("src", "tests"):
        for path in sorted((REPO_ROOT / root).rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in tree.body:
                if not isinstance(node, ast.AnnAssign | ast.Assign):
                    continue
                targets = [node.target] if isinstance(node, ast.AnnAssign) else node.targets
                if len(targets) != 1:
                    continue
                target = targets[0]
                if not isinstance(target, ast.Name) or not target.id.endswith("POLICY_TOOL"):
                    continue
                assigned = node.value
                if not isinstance(assigned, ast.Constant) or not isinstance(assigned.value, str):
                    continue
                where = f"{path.relative_to(REPO_ROOT).as_posix()}:{node.lineno}"
                found[where] = assigned.value
    return found


def test_every_hardcoded_policy_tool_name_is_the_one_the_register_declares() -> None:
    """A class-6 entity name, written into Python nine times and bound to nothing.

    `harness/cli.py` declares `_DEFAULT_POLICY_TOOL` and eight test modules
    declare `POLICY_TOOL`, each a separate copy of `fetch_policy`. D106's
    register-binding covers the rubric's inventories and does not reach these,
    and `test_the_policy_tool_name_is_a_flag_and_not_a_constant` proves the
    flag reaches the seam rather than that the default matches the register --
    which is the neighbor of this claim, not this claim.

    A rename in `corpus/entities.md` would leave every copy stale, the corpus
    using the new name and the CLI defaulting to the old one, and the only
    symptom would be `retrieved_policies` coming back empty for every call: no
    error, no refusal, and `governing_clause_not_applied` quietly applicable to
    nothing.
    """
    constants = _policy_tool_constants()
    assert len(constants) >= 9, (
        f"only {len(constants)} policy-tool constants found; the reading is broken or the "
        "constants were renamed, and either way this test now proves less than it says"
    )

    declared = _declared_names("**Tools.**")
    wrong = {where: value for where, value in constants.items() if value not in declared}
    assert not wrong, (
        "policy-tool constants naming a tool corpus/entities.md does not declare:\n  "
        + "\n  ".join(f"{where} = {value!r}" for where, value in sorted(wrong.items()))
    )

    values = set(constants.values())
    assert len(values) == 1, "the copies have already diverged: " + "; ".join(
        f"{where} = {value!r}" for where, value in sorted(constants.items())
    )


def test_the_policy_tool_binding_would_notice_a_rename() -> None:
    """The planted control.

    `_declared_names` returning an empty set, or the constant reading finding
    nothing, makes the test above pass by comparing nothing against nothing --
    the failure mode this repository has found in its own guards three times.
    """
    declared = _declared_names("**Tools.**")
    assert "fetch_policy" in declared, "the register no longer declares the tool by that name"
    assert "fetch_policy_renamed" not in declared
    assert set(_policy_tool_constants().values()) - declared == set()
    assert {"a_tool_nobody_declared"} - declared == {"a_tool_nobody_declared"}


#: The tool-result detail keys whose values are a vocabulary rather than a datum:
#: a reason code and a remedy, each drawn from a small set the corpus fixes. The
#: other keys hold identifiers, amounts, timestamps and free text (D198).
_VOCABULARY_KEYS: Final[tuple[str, ...]] = ("reason", "remedy")


def _declared_detail_values() -> set[str]:
    """The tool-result detail values Class 6 declares, from the paragraph naming them."""
    section = _register_section("**Tool-result detail values.**", "\n\n**")
    return set(re.findall(r"`([a-z][a-z0-9_]*)`", section))


def _undeclared_detail_values(details: list[str], declared: set[str]) -> set[str]:
    """Every `reason=` or `remedy=` value in the tool-result `details` that Class 6
    does not declare."""
    return {
        value
        for detail in details
        for key, value in re.findall(r"\b(reason|remedy)=([a-z0-9_]+)", detail)
        if key in _VOCABULARY_KEYS and value not in declared
    }


def test_the_register_would_notice_a_result_vocabulary_value_it_does_not_declare() -> None:
    """Every reason code and remedy a tool result names is a value Class 6 declares (D198).

    D193 read two kinds of value and left a third: the register declares `reason` and
    `remedy` as detail keys and said nothing about what they carry, which is a closed
    vocabulary the corpus fixes (the phase-5 audit's P5-11). A reason code is where a
    platform says *why*, so a value nobody declared is a case nobody enumerated.

    Planted first -- an undeclared code is reported and a declared one is not -- then
    the corpus. A `call.ended(reason=...)` is a disconnection reason, a closed
    vocabulary of the event model, and never reaches this reading: only tool results do.
    """
    declared = _declared_detail_values()
    assert {"window_closed", "booking_transferred", "reversal_by_current_holder"} <= declared, (
        sorted(declared)
    )
    assert _undeclared_detail_values(
        ["reason=window_closed; closed_at=2027-03-17T19:00:00Z", "reason=never_declared"], declared
    ) == {"never_declared"}

    details = [
        event.detail
        for path in _transcripts()
        for event in parse_call(path).events
        if isinstance(event, ToolResultEvent) and event.detail
    ]
    assert any("reason=" in detail for detail in details), "no reason code is read at all"
    undeclared = _undeclared_detail_values(details, declared)
    assert not undeclared, (
        f"vocabulary values corpus/entities.md Class 6 does not declare: {sorted(undeclared)}"
    )
