"""Judge-versus-label agreement, per rubric entry, over one set of calls (D175).

**Both directions, per entry.** An entry should fire on the calls carrying the
findings traced to it and stay silent on every other call in the set, so each
entry gets four counts: hits and misses on the traced calls, false alarms and
correct silences on the rest. A fifth counts the calls the entry gave no verdict
on, by status, **apart from silence**: an errored call read as a correct silence
would be a measurement failure reported as agreement. The five sum to the set's
call count, which is the denominator the specification asks each set to carry.

**Fires means what the gate reads.** A judged entry fires on a call whose modal
verdict it counts against its gate (`CallRollup.violated`, D158, D160); a
deterministic entry fires where its verdict is one it counts, which for every
deterministic entry is its negative pole alone. Agreement then measures the
verdict a gate acts on, not a looser or stricter reading of the same answers.

**Two sets, never pooled.** The design set's traces are the rubric's own
`traces_to`, placed on each finding's `call_ref`. The held-out set's are
`traces.yaml`, re-checked here against every invariant its validator states
rather than trusted, because a file that drifted after it was sealed is exactly
what a check at the point of use exists to notice.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import yaml

from harness.core.engine import RunReport
from harness.core.findings import Finding
from harness.core.result import NON_RATE_STATUSES, Status
from harness.core.rubric import CheckTier, Rubric, RubricEntry
from harness.heldout import HELD_OUT_FINDING_ID as _HELD_OUT_FINDING_ID
from harness.judge.rollup import CallRollup, JudgedEntryRollup

#: The commit `rubric-frozen-v1` points at: the rubric the held-out labels were
#: written against, and so the only one they can be scored with. Pinned rather
#: than resolved through git, so the command needs no clone when it runs, and
#: compared with the tag by `tests/test_agreement.py`, so a moved tag fails a test
#: rather than leaving this constant quietly wrong (D175).
RUBRIC_FROZEN_V1: Final[str] = "6d3a7101aaa1f15b440de43fe5142434f69c9dc9"

#: The tag naming the commit above, read by the test that compares the two rather
#: than written there, because the published snapshot rewrites it: a snapshot tags
#: its own first commit, and reusing this name there made the freeze appear to
#: postdate the held-out seal it must precede (D209). The freeze itself is named
#: in `freeze-proof/`, which is published and needs no history to verify.
FREEZE_TAG: Final[str] = "rubric-frozen-v1"

#: A held-out finding's id: `HF-` and two or more digits, which never collides
#: with a design finding's `F-NN`. Defined in `harness.heldout` since D196,
#: where `harness.findings_view` reads it too, and re-exported here because this
#: is where the label checks that read it live.
HELD_OUT_FINDING_ID: Final[re.Pattern[str]] = _HELD_OUT_FINDING_ID

#: The four keys a `traces.yaml` holds, and no others.
TRACES_KEYS: Final[tuple[str, ...]] = (
    "rubric-frozen-v1",
    "traces",
    "uncovered",
    "calls_without_findings",
)

#: Printed under the design section. The design findings were adjudicated with
#: some judge output in view -- F-90 was surfaced by the judged tier -- so for a
#: judged entry this is not agreement against labels written blind (D21).
DESIGN_CAVEAT: Final[str] = (
    "Design findings were adjudicated with some judge output in view (F-90 came from the "
    "judged tier), so for judged entries this is not agreement against labels written "
    "blind; that is the held-out section's (D21)."
)

#: Printed in place of the held-out section when no held-out labels were given.
HELD_OUT_NOT_COMPUTED: Final[str] = (
    "held-out set: not computed -- no held-out labels were given. It is computed when all "
    "five of --held-out-transcripts, --held-out-corpus-version-file, --held-out-run-log, "
    "--held-out-findings and --held-out-traces are passed."
)

#: Printed under the held-out section, which is the agreement D21 means: labels
#: written before this rubric's judged run, sealed by the manifest its log names.
HELD_OUT_CAVEAT: Final[str] = (
    "Held-out labels were written before the judged run and sealed by the labels manifest "
    "its log names (D21, D26, D173)."
)

#: One entry's reading of one call: its status, and whether the verdict it gave
#: is one the entry counts against its gate.
Reading = tuple[Status, bool]


class AgreementError(Exception):
    """Agreement that cannot be computed as asked, refused by name rather than
    computed over fewer calls, entries or labels than the set holds."""


@dataclass(frozen=True, slots=True)
class Traces:
    """The held-out labels' answer to the rubric's `traces_to` (D105, D125)."""

    rubric_frozen: str
    traces: Mapping[str, tuple[str, ...]]
    """Every rubric entry at the freeze, to the held-out findings it should catch."""
    uncovered: frozenset[str]
    """Held-out findings no entry is expected to catch."""
    calls_without_findings: frozenset[str]
    """Held-out calls declared to carry no finding."""


def _string_list(value: object, key: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise AgreementError(f"traces.yaml: {key} must be a list of non-empty strings")
    if len(set(value)) != len(value):
        raise AgreementError(f"traces.yaml: {key} names an id more than once")
    return tuple(value)


def parse_traces(text: str) -> Traces:
    """A `traces.yaml`, its shape checked and nothing yet compared with anything."""
    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise AgreementError(f"traces.yaml does not parse: {exc}") from exc
    if not isinstance(document, dict):
        raise AgreementError("traces.yaml is not a mapping")
    missing = [key for key in TRACES_KEYS if key not in document]
    extra = sorted(str(key) for key in document if key not in TRACES_KEYS)
    if missing or extra:
        raise AgreementError(
            f"traces.yaml holds {', '.join(sorted(map(str, document)))}; it holds exactly "
            f"{', '.join(TRACES_KEYS)}"
        )
    frozen = document["rubric-frozen-v1"]
    if not isinstance(frozen, str):
        raise AgreementError("traces.yaml: rubric-frozen-v1 must be a commit SHA, as a string")
    raw_traces = document["traces"]
    if not isinstance(raw_traces, dict) or not all(isinstance(key, str) for key in raw_traces):
        raise AgreementError("traces.yaml: traces must map rubric entry ids to lists")
    return Traces(
        rubric_frozen=frozen,
        traces={
            entry_id: _string_list(ids, f"traces.{entry_id}")
            for entry_id, ids in raw_traces.items()
        },
        uncovered=frozenset(_string_list(document["uncovered"], "uncovered")),
        calls_without_findings=frozenset(
            _string_list(document["calls_without_findings"], "calls_without_findings")
        ),
    )


def load_traces(path: Path) -> Traces:
    return parse_traces(path.read_text(encoding="utf-8"))


def check_held_out_labels(
    traces: Traces, rubric: Rubric, findings: Sequence[Finding], calls: Sequence[str]
) -> None:
    """Refuse held-out labels breaking any invariant their validator states (D175).

    Re-checked here rather than trusted. Every problem is named at once, so a file
    breaking two rules is not repaired one refusal at a time.
    """
    problems: list[str] = []
    if traces.rubric_frozen != RUBRIC_FROZEN_V1:
        problems.append(
            f"it names rubric-frozen-v1 {traces.rubric_frozen!r}, and that tag points at "
            f"{RUBRIC_FROZEN_V1}"
        )
    entry_ids = {entry.id for entry in rubric.entries}
    if absent := sorted(entry_ids - set(traces.traces)):
        problems.append(f"traces lists no row for rubric entry id(s) {', '.join(absent)}")
    if strangers := sorted(set(traces.traces) - entry_ids):
        problems.append(f"traces names id(s) the rubric does not declare: {', '.join(strangers)}")
    finding_ids = [finding.id for finding in findings]
    if malformed := sorted(i for i in finding_ids if not HELD_OUT_FINDING_ID.fullmatch(i)):
        problems.append(f"finding id(s) that are not HF-NN: {', '.join(malformed)}")
    known = set(finding_ids)
    traced = {finding for ids in traces.traces.values() for finding in ids}
    if unheld := sorted((traced | traces.uncovered) - known):
        problems.append(f"traces or uncovered name id(s) findings.yaml does not hold: {unheld}")
    if doubled := sorted(traced & traces.uncovered):
        problems.append(f"finding(s) traced to an entry and also uncovered: {', '.join(doubled)}")
    if orphaned := sorted(known - traced - traces.uncovered):
        problems.append(f"finding(s) neither traced to an entry nor uncovered: {orphaned}")
    call_set = set(calls)
    referenced = {finding.call_ref for finding in findings}
    if elsewhere := sorted(referenced - call_set):
        problems.append(f"findings sit on call(s) this set does not read: {', '.join(elsewhere)}")
    if unread := sorted(traces.calls_without_findings - call_set):
        problems.append(
            f"calls_without_findings names call(s) this set does not read: {', '.join(unread)}"
        )
    if both := sorted(referenced & traces.calls_without_findings):
        problems.append(f"call(s) carrying a finding and also listed without one: {both}")
    if unaccounted := sorted(call_set - referenced - traces.calls_without_findings):
        problems.append(
            f"call(s) carrying no finding and not listed without one: {', '.join(unaccounted)}"
        )
    if problems:
        raise AgreementError(
            "the held-out labels break what their validator states:\n  " + "\n  ".join(problems)
        )


@dataclass(frozen=True, slots=True)
class EntryAgreement:
    """One entry against one set's calls: four counts in both directions, and a
    fifth for the calls it gave no verdict on, by status."""

    entry: RubricEntry
    hits: int
    """Fired on a call carrying a finding traced to this entry."""
    misses: int
    """Silent on such a call."""
    false_alarms: int
    """Fired on any other call in the set."""
    correct_silences: int
    """Silent on any other call in the set."""
    no_verdict: tuple[tuple[str, int], ...]
    """Status to count, for the calls this entry gave no verdict on, in the
    channel's order."""

    @property
    def unscored(self) -> int:
        return sum(count for _, count in self.no_verdict)

    @property
    def calls(self) -> int:
        return self.hits + self.misses + self.false_alarms + self.correct_silences + self.unscored


@dataclass(frozen=True, slots=True)
class SetAgreement:
    """Every rubric entry's agreement over one set, in rubric order."""

    name: str
    calls: tuple[str, ...]
    entries: tuple[EntryAgreement, ...]


def count_entry(
    entry: RubricEntry,
    readings: Mapping[str, Reading],
    expected: frozenset[str],
    calls: Sequence[str],
) -> EntryAgreement:
    """The five counts, over exactly the set's calls.

    A call the entry has no reading for is refused rather than dropped: agreement
    over fewer calls than the set holds would carry a denominator nobody chose.
    """
    missing = [call for call in calls if call not in readings]
    if missing:
        raise AgreementError(
            f"{entry.id} has no result for {len(missing)} of the set's {len(calls)} call(s): "
            f"{', '.join(missing)}"
        )
    hits = misses = false_alarms = silences = 0
    no_verdict: Counter[str] = Counter()
    for call in calls:
        status, fired = readings[call]
        if status is not Status.APPLICABLE:
            no_verdict[status.value] += 1
        elif fired and call in expected:
            hits += 1
        elif fired:
            false_alarms += 1
        elif call in expected:
            misses += 1
        else:
            silences += 1
    return EntryAgreement(
        entry=entry,
        hits=hits,
        misses=misses,
        false_alarms=false_alarms,
        correct_silences=silences,
        no_verdict=tuple(
            (status.value, no_verdict[status.value])
            for status in NON_RATE_STATUSES
            if no_verdict[status.value]
        ),
    )


def deterministic_readings(report: RunReport, entry: RubricEntry) -> dict[str, Reading]:
    """Where a deterministic entry fires: its verdict is one it counts against its gate."""
    return {
        result.call_id: (result.status, result.verdict in entry.violating)
        for result in report.for_entry(entry.id)
    }


def judged_readings(rollup: JudgedEntryRollup) -> dict[str, Reading]:
    """Where a judged entry fires: the gate's own reading of its N answers.

    A call with no applicable repetition reads as its most frequent status, with
    a tie going to the status the channel lists first.
    """
    readings: dict[str, Reading] = {}
    for call in rollup.calls:
        if call.verdict is not None:
            readings[call.call_id] = (Status.APPLICABLE, call.violated)
        else:
            readings[call.call_id] = (_most_frequent_status(call), False)
    return readings


def _most_frequent_status(call: CallRollup) -> Status:
    counts = dict(call.statuses)
    present = [status for status in NON_RATE_STATUSES if counts.get(status.value)]
    if not present:
        raise AgreementError(
            f"{call.entry.id} on {call.call_id} carries neither a verdict nor a status"
        )
    return max(present, key=lambda status: counts[status.value])


def design_expected(rubric: Rubric, findings: Mapping[str, Finding]) -> dict[str, frozenset[str]]:
    """The design set's traces: each entry's `traces_to`, placed on its findings' calls."""
    expected: dict[str, frozenset[str]] = {}
    for entry in rubric.entries:
        unheld = [finding for finding in entry.traces_to if finding not in findings]
        if unheld:
            raise AgreementError(
                f"{entry.id} traces {', '.join(unheld)}, which the findings file does not hold"
            )
        expected[entry.id] = frozenset(findings[finding].call_ref for finding in entry.traces_to)
    return expected


def held_out_expected(traces: Traces, findings: Mapping[str, Finding]) -> dict[str, frozenset[str]]:
    """The held-out set's traces, placed on their findings' calls.

    Built only after `check_held_out_labels` has passed, which is what makes every
    id here one the findings hold.
    """
    return {
        entry_id: frozenset(findings[finding].call_ref for finding in ids)
        for entry_id, ids in traces.traces.items()
    }


def readings_for(
    entry: RubricEntry, deterministic: RunReport, judged: Mapping[str, JudgedEntryRollup]
) -> dict[str, Reading]:
    """Where one entry fired over a set's calls, read the way its tier's gate reads it.

    Shared by agreement and the coverage report (D188), so the two cannot come to
    disagree about when an entry fired.
    """
    if entry.tier is CheckTier.JUDGE:
        rollup = judged.get(entry.id)
        if rollup is None:
            raise AgreementError(f"{entry.id} has no judged roll-up: the run log did not cover it")
        return judged_readings(rollup)
    return deterministic_readings(deterministic, entry)


def set_agreement(
    name: str,
    rubric: Rubric,
    calls: Sequence[str],
    deterministic: RunReport,
    judged: Sequence[JudgedEntryRollup],
    expected: Mapping[str, frozenset[str]],
) -> SetAgreement:
    """Every rubric entry, in rubric order, against the set's calls."""
    rollups = {rollup.entry.id: rollup for rollup in judged}
    rows: list[EntryAgreement] = []
    for entry in rubric.entries:
        if entry.id not in expected:
            raise AgreementError(f"{entry.id} has no traces in this set")
        readings = readings_for(entry, deterministic, rollups)
        rows.append(count_entry(entry, readings, expected[entry.id], calls))
    return SetAgreement(name=name, calls=tuple(calls), entries=tuple(rows))


def render_set(agreement: SetAgreement, caveat: str) -> list[str]:
    """One set's section: a row per entry whose five counts sum to the set's calls,
    and a row totalling every entry-call pair."""
    lines = [
        f"{agreement.name}: {len(agreement.calls)} calls, {len(agreement.entries)} rubric entries",
        caveat,
        "",
        f"{'entry':<42} {'tier':<6} {'hit':>4} {'miss':>5} {'false':>6} {'silent':>7} "
        f"{'no verdict':>10}  of",
        "-" * 96,
    ]
    for row in agreement.entries:
        breakdown = ", ".join(f"{status} {count}" for status, count in row.no_verdict)
        lines.append(
            f"{row.entry.id:<42} {row.entry.tier.value:<6} {row.hits:>4} {row.misses:>5} "
            f"{row.false_alarms:>6} {row.correct_silences:>7} {row.unscored:>10}  {row.calls}"
            + (f"  ({breakdown})" if breakdown else "")
        )
    rows = agreement.entries
    lines.append("-" * 96)
    lines.append(
        f"{'every entry':<42} {'':<6} {sum(r.hits for r in rows):>4} "
        f"{sum(r.misses for r in rows):>5} {sum(r.false_alarms for r in rows):>6} "
        f"{sum(r.correct_silences for r in rows):>7} {sum(r.unscored for r in rows):>10}  "
        f"{sum(r.calls for r in rows)} entry-call pairs"
    )
    return lines
