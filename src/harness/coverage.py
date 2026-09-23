"""Coverage by severity: which findings the rubric retires, per band, over one set (D188).

**Retired means caught.** A finding is retired when a rubric entry traced to it
fired on its call, read the way agreement reads an entry: a judged entry where its
gate reads a violation, a deterministic one where its verdict is one it counts
(D175). Being traced to an entry is what the rubric aims at; firing is what it did,
and the two part on every judged miss -- F-85 is traced to `J-policy-alignment`,
which is silent on its call on every repetition.

**Two ways not to be retired, named apart.** *Uncovered*: traced to no entry,
which is what the held-out traces file calls `uncovered`, and what D157 says the
report exists to show concentrated in the most severe band. *Missed*: traced, and
no entry traced to it fired on its call, each tracing entry's reading named beside
it, so a silence and an entry that gave no verdict read differently.

**Per band, and never pooled** (D157): a band's figures are over the findings that
band holds, and there is no total row across bands. **Each set is banded by its own
severity file** (D177): a held-out band orders severity within the held-out set and
is not a design-set band, so the two sets are computed and printed apart.

**Findings with no band are counted and named beside the figures** (D187), in two
groups for two causes: question-tier findings, which the scoring tool excludes
before scoring, and unplaced ones, in scope and compared by nobody.

**Read per call**, as agreement is: an entry firing on a call retires every
finding traced to it there, though it may have fired for one of them alone.

**Each band is split by who could detect a finding** (D192): a deterministic check
(`assert`), the judge, or only a human. The split sits inside the band rather than
across bands, so it is D157's per-band reading made finer rather than a pooled
figure, and it is what shows whether the tier that should catch a band's findings is
the one that does.
"""

from __future__ import annotations

import textwrap
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

from harness.agreement import Reading
from harness.core.findings import DetectableBy, Finding
from harness.core.result import Status
from harness.core.rubric import Rubric
from harness.core.severity import (
    BAND_ORDER,
    SeverityFile,
    SeverityRecord,
    join,
    moved_since_scored,
)

#: The words each section's first line carries after the set's name. The absence
#: check reads a held-out coverage report by this heading beside a held-out
#: finding's id (D188), so a change here is a change there.
COVERAGE_HEADING: Final[str] = "coverage by severity"

RETIRED: Final[str] = "retired"
MISSED: Final[str] = "missed"
UNCOVERED: Final[str] = "uncovered"
#: The three states a finding is in, in the order the report names them.
STATES: Final[tuple[str, ...]] = (RETIRED, MISSED, UNCOVERED)

#: Printed once, above both sections.
RETIRED_MEANS: Final[str] = (
    "retired: a rubric entry traced to the finding fired on its call, read as agreement reads "
    "it and per call; uncovered: traced to no entry; missed: traced, and fired on by none (D188)"
)

#: Printed under the design section. The rubric was written against these findings,
#: so an uncovered one is a gap its author could see (D177).
DESIGN_COVERAGE_CAVEAT: Final[str] = (
    "In sample: the rubric was written against these findings, and some were adjudicated with "
    "judge output in view, so the held-out section is where an uncovered severe finding would "
    "be news (D177)."
)

#: Printed under the held-out section.
HELD_OUT_COVERAGE_CAVEAT: Final[str] = (
    "Banded in the held-out set's own store, sealed before its judged run: a band orders "
    "severity within this set and is not a design-set band, and no figure here is pooled "
    "with the design set's (D177)."
)

#: Printed in place of the held-out section when no held-out labels were given.
HELD_OUT_COVERAGE_NOT_COMPUTED: Final[str] = (
    "held-out set: not computed -- no held-out labels were given. It is computed when all six "
    "of --held-out-transcripts, --held-out-corpus-version-file, --held-out-run-log, "
    "--held-out-findings, --held-out-traces and --held-out-severity are passed."
)

_WIDTH: Final[int] = 96


class CoverageError(Exception):
    """Coverage that cannot be computed as asked, refused by name rather than
    computed over fewer findings, calls or entries than the set holds."""


@dataclass(frozen=True, slots=True)
class FindingCoverage:
    """One finding, its band, and whether an entry traced to it fired on its call."""

    finding: Finding
    severity: SeverityRecord | None
    """`None` for a question-tier finding and for an unplaced one (D187)."""
    readings: tuple[tuple[str, str], ...]
    """Each entry traced to this finding, in rubric order, to its reading of the
    finding's call: `fired`, `silent`, or the status it gave in place of a verdict."""

    @property
    def state(self) -> str:
        if not self.readings:
            return UNCOVERED
        if any(reading == "fired" for _, reading in self.readings):
            return RETIRED
        return MISSED

    @property
    def label(self) -> str:
        """The id, and for a missed finding what each entry traced to it read."""
        if self.state != MISSED:
            return self.finding.id
        read = ", ".join(f"{entry}: {reading}" for entry, reading in self.readings)
        return f"{self.finding.id} ({read})"


@dataclass(frozen=True, slots=True)
class BandCoverage:
    """One severity band of one set, most severe finding first."""

    band: str
    findings: tuple[FindingCoverage, ...]

    @property
    def holds(self) -> int:
        return len(self.findings)

    @property
    def traced(self) -> int:
        return sum(1 for finding in self.findings if finding.state != UNCOVERED)

    @property
    def retired(self) -> int:
        return sum(1 for finding in self.findings if finding.state == RETIRED)

    def of(self, kind: DetectableBy) -> BandCoverage:
        """This band's findings of one detection type, as a band of their own (D192)."""
        return BandCoverage(
            band=self.band,
            findings=tuple(f for f in self.findings if f.finding.detectable_by is kind),
        )


@dataclass(frozen=True, slots=True)
class SetCoverage:
    """Every finding of one set: the banded ones by band, and the two groups with none."""

    name: str
    calls: tuple[str, ...]
    severity_run: str
    """The `run_id` of the severity file this set was banded by."""
    bands: tuple[BandCoverage, ...]
    """One per band, in `BAND_ORDER`, an empty band included."""
    questions: tuple[FindingCoverage, ...]
    """Question-tier findings, which the scoring tool excludes from scoring (D187)."""
    unplaced: tuple[FindingCoverage, ...]
    """Findings in scope that nobody compared, so they carry no band."""

    @property
    def findings(self) -> int:
        return sum(band.holds for band in self.bands) + len(self.questions) + len(self.unplaced)


def _reading(reading: Reading) -> str:
    status, fired = reading
    if status is not Status.APPLICABLE:
        return status.value
    return "fired" if fired else "silent"


def set_coverage(
    name: str,
    rubric: Rubric,
    findings: Sequence[Finding],
    severity: SeverityFile,
    traces: Mapping[str, Sequence[str]],
    readings: Mapping[str, Mapping[str, Reading]],
    calls: Sequence[str],
) -> SetCoverage:
    """Every finding of one set, banded by that set's own severity file (D177, D188).

    `traces` maps each rubric entry to the findings it is traced to -- the rubric's
    `traces_to` for the design set, `traces.yaml` for the held-out set -- and
    `readings` each entry to its reading of every call in the set. A finding the
    severity join refuses, a traced id the set does not hold, a finding on a call the
    set does not read, and an entry with no reading for one of its calls are each
    refused, because coverage over fewer of them than the set holds would state
    figures nobody asked for. **So is a band placed on text that has since moved**
    (D189): its figure would count a finding under a severity nobody gave the wording
    it now has.
    """
    joined = join(tuple(findings), severity)
    held = {finding.id for finding in findings}
    call_set = set(calls)

    problems: list[str] = []
    if moved := moved_since_scored(findings, severity):
        problems.append(
            f"band(s) placed on text that has changed since it was scored: {', '.join(moved)}"
        )
    if untraced_entries := [entry.id for entry in rubric.entries if entry.id not in traces]:
        problems.append(f"no traces row for rubric entry id(s) {', '.join(untraced_entries)}")
    if unread_entries := [entry.id for entry in rubric.entries if entry.id not in readings]:
        problems.append(f"no readings for rubric entry id(s) {', '.join(unread_entries)}")
    strangers = sorted({finding for ids in traces.values() for finding in ids} - held)
    if strangers:
        problems.append(f"traces name id(s) the set's findings do not hold: {', '.join(strangers)}")
    if elsewhere := sorted({finding.call_ref for finding in findings} - call_set):
        problems.append(f"findings sit on call(s) this set does not read: {', '.join(elsewhere)}")
    for entry_id, by_call in sorted(readings.items()):
        if unanswered := [call for call in calls if call not in by_call]:
            problems.append(f"{entry_id} has no reading for {', '.join(unanswered)}")
    if problems:
        raise CoverageError(
            f"coverage of the {name} cannot be computed:\n  " + "\n  ".join(problems)
        )

    tracing: dict[str, list[str]] = {finding: [] for finding in held}
    for entry in rubric.entries:
        for finding in traces[entry.id]:
            tracing[finding].append(entry.id)

    covered: list[FindingCoverage] = [
        FindingCoverage(
            finding=item.finding,
            severity=item.severity,
            readings=tuple(
                (entry_id, _reading(readings[entry_id][item.finding.call_ref]))
                for entry_id in tracing[item.finding.id]
            ),
        )
        for item in joined
    ]
    # Most severe first within a band, as a cut's `between` lists them.
    by_band: dict[str, list[tuple[float, str, FindingCoverage]]] = {band: [] for band in BAND_ORDER}
    for item in covered:
        if item.severity is not None:
            by_band[item.severity.severity].append((-item.severity.theta, item.finding.id, item))
    unplaced = set(severity.unplaced)
    return SetCoverage(
        name=name,
        calls=tuple(calls),
        severity_run=severity.run_id,
        bands=tuple(
            BandCoverage(
                band=band,
                findings=tuple(item for *_, item in sorted(by_band[band], key=lambda row: row[:2])),
            )
            for band in BAND_ORDER
        ),
        questions=tuple(
            item for item in covered if item.severity is None and item.finding.id not in unplaced
        ),
        unplaced=tuple(item for item in covered if item.finding.id in unplaced),
    )


def _named(label: str, items: Sequence[FindingCoverage]) -> list[str]:
    """One line, wrapped, naming `items` after `label`, or saying there are none."""
    text = ", ".join(item.label for item in items) or "none"
    lead = f"  {label:<10} "
    return textwrap.wrap(
        text,
        width=_WIDTH,
        initial_indent=lead,
        subsequent_indent=" " * len(lead),
        break_on_hyphens=False,
    )


def render_coverage(coverage: SetCoverage, caveat: str) -> list[str]:
    """One set's section: a row per band with one row per detection type beneath it,
    then every finding named by its state.

    **No total row.** A figure across bands is the pooled one D157 refused, and
    printing it beside the per-band rows would invite reading it first. The detection
    types always print, all three, so a type a band holds none of reads as zero rather
    than as absent (D192).
    """
    lines = [
        f"{coverage.name}: {COVERAGE_HEADING}, {coverage.findings} findings on "
        f"{len(coverage.calls)} calls, banded by severity run {coverage.severity_run[:16]}",
        caveat,
        "",
        f"{'band':<10} {'holds':>6} {'traced':>7} {'retired':>8}",
        "-" * 34,
    ]
    for band in coverage.bands:
        lines.append(f"{band.band:<10} {band.holds:>6} {band.traced:>7} {band.retired:>8}")
        for kind in DetectableBy:
            part = band.of(kind)
            lines.append(f"  {kind.value:<8} {part.holds:>6} {part.traced:>7} {part.retired:>8}")
    headings = {
        RETIRED: "retired, most severe first:",
        UNCOVERED: "uncovered -- traced to no rubric entry:",
        MISSED: "missed -- traced, and no entry traced to it fired on its call:",
    }
    for state in (RETIRED, UNCOVERED, MISSED):
        lines += ["", headings[state]]
        for band in coverage.bands:
            lines += _named(band.band, [f for f in band.findings if f.state == state])
    for group, what in (
        (coverage.questions, "question-tier, which the scoring tool excludes from scoring (D187)"),
        (coverage.unplaced, "unplaced, in scope and compared by nobody"),
    ):
        lines += ["", f"no band: {len(group)} finding(s) {what}"]
        if group:
            for state in STATES:
                lines += _named(state, [f for f in group if f.state == state])
    return lines
