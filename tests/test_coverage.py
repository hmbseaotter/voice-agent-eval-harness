"""The coverage report by severity, over planted readings of the design set (D188).

Every reading here is planted rather than replayed, so each test says which entry
fired on which call and asserts what the report makes of it. **Nothing held out is
read**: the findings, the bands and the traces are the design set's own, and the one
invented severity export is the design export with a single row moved to `unplaced`.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Final

import pytest

from harness.agreement import Reading
from harness.checks import build_registry
from harness.core.findings import DetectableBy, load_findings
from harness.core.result import Status
from harness.core.rubric import load_rubric
from harness.core.severity import BAND_ORDER, parse_severity
from harness.coverage import (
    DESIGN_COVERAGE_CAVEAT,
    MISSED,
    RETIRED,
    UNCOVERED,
    CoverageError,
    SetCoverage,
    render_coverage,
    set_coverage,
)

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
RUBRIC = load_rubric(REPO_ROOT / "rubric.yaml", build_registry().keys())
FINDINGS = load_findings(REPO_ROOT / "corpus" / "findings.yaml")
SEVERITY_TEXT: Final[str] = (REPO_ROOT / "corpus" / "findings.severity.json").read_text(
    encoding="utf-8"
)
CALLS: Final[tuple[str, ...]] = tuple(
    path.stem for path in sorted((REPO_ROOT / "corpus" / "transcripts").glob("*.txt"))
)
TRACES: Final[dict[str, tuple[str, ...]]] = {entry.id: entry.traces_to for entry in RUBRIC.entries}


def _readings(
    fired: Mapping[str, str] | None = None, gave: Mapping[str, tuple[str, Status]] | None = None
) -> dict[str, dict[str, Reading]]:
    """Every entry silent on every design call, except that each entry in `fired`
    fires on the call named, and each in `gave` returns the status named there."""
    readings: dict[str, dict[str, Reading]] = {
        entry.id: {call: (Status.APPLICABLE, False) for call in CALLS} for entry in RUBRIC.entries
    }
    for entry_id, call in (fired or {}).items():
        readings[entry_id][call] = (Status.APPLICABLE, True)
    for entry_id, (call, status) in (gave or {}).items():
        readings[entry_id][call] = (status, False)
    return readings


def _coverage(
    readings: dict[str, dict[str, Reading]], severity: str = SEVERITY_TEXT
) -> SetCoverage:
    return set_coverage(
        "design set", RUBRIC, FINDINGS, parse_severity(severity), TRACES, readings, CALLS
    )


def _state(coverage: SetCoverage, finding_id: str) -> tuple[str, str]:
    everything = [f for band in coverage.bands for f in band.findings]
    everything += [*coverage.questions, *coverage.unplaced]
    (found,) = [f for f in everything if f.finding.id == finding_id]
    return found.state, found.label


def test_coverage_would_notice_a_finding_read_in_the_wrong_state() -> None:
    """Retired where an entry traced to it fired on its call, missed where every such
    entry was silent or gave no verdict, uncovered where none is traced to it (D188).

    F-04 is critical and traced to one entry, which fires on its call. F-85 is traced
    to `J-policy-alignment`, which errors on CALL-19, so it is missed and the label
    says the entry errored rather than that it was silent. F-45 is traced and nothing
    fires on its call, so it is missed as a silence. F-76 is traced to nothing.
    """
    coverage = _coverage(
        _readings(
            fired={"A-verification-claimed-on-mismatched-value": "CALL-01"},
            gave={"J-policy-alignment": ("CALL-19", Status.ERRORED)},
        )
    )
    assert _state(coverage, "F-04") == (RETIRED, "F-04")
    assert _state(coverage, "F-85") == (MISSED, "F-85 (J-policy-alignment: errored)")
    assert _state(coverage, "F-45") == (
        MISSED,
        "F-45 (A-account-detail-disclosed-before-verification: silent)",
    )
    assert _state(coverage, "F-76") == (UNCOVERED, "F-76")
    critical = coverage.bands[0]
    assert critical.band == "critical"
    assert (critical.holds, critical.traced, critical.retired) == (4, 3, 1)


def test_coverage_would_notice_its_bands_pooled_or_its_findings_misbanded() -> None:
    """Each band holds the findings its severity file puts there, most severe first, and
    the traced count is the rubric's, whatever fired (D157, D188).

    With every entry silent, nothing is retired in any band; with an entry firing on
    one critical call, only the critical band moves.
    """
    silent = _coverage(_readings())
    assert [band.band for band in silent.bands] == list(BAND_ORDER)
    assert [(b.holds, b.traced, b.retired) for b in silent.bands] == [
        (4, 3, 0),
        (14, 14, 0),
        (28, 27, 0),
        (37, 33, 0),
    ]
    rows = json.loads(SEVERITY_TEXT)["severities"]
    for band in silent.bands:
        stated = sorted(
            (row for row in rows if row["severity"] == band.band),
            key=lambda row: (-row["theta"], row["id"]),
        )
        assert [f.finding.id for f in band.findings] == [row["id"] for row in stated], band.band

    one_fires = _coverage(
        _readings(fired={"A-verification-claimed-on-mismatched-value": "CALL-01"})
    )
    assert [b.retired for b in one_fires.bands] == [1, 0, 0, 0]


def test_coverage_would_notice_an_unbanded_finding_left_out_or_counted_twice() -> None:
    """Question-tier findings and unplaced ones carry no band, and each is named in its
    own group rather than in a band or in both groups (D187, D188).

    The invented export moves F-44, a low finding that anchors no cut and sits between
    none, from `severities` to `unplaced`, so the file still agrees with its cuts.
    """
    document = json.loads(SEVERITY_TEXT)
    document["severities"] = [row for row in document["severities"] if row["id"] != "F-44"]
    document["unplaced"] = ["F-44"]
    coverage = _coverage(_readings(), severity=json.dumps(document))
    assert [f.finding.id for f in coverage.unplaced] == ["F-44"]
    assert [f.finding.id for f in coverage.questions] == [
        "F-27",
        "F-31",
        "F-49",
        "F-54",
        "F-56",
        "F-59",
        "F-84",
    ]
    assert coverage.bands[3].holds == 36
    assert coverage.findings == len(FINDINGS)
    rendered = "\n".join(render_coverage(coverage, DESIGN_COVERAGE_CAVEAT))
    assert "no band: 7 finding(s) question-tier" in rendered, rendered
    assert "no band: 1 finding(s) unplaced" in rendered, rendered


def test_coverage_would_notice_an_input_it_cannot_cover() -> None:
    """A traced id the set does not hold, a finding on a call the set does not read, and
    an entry with no reading for one of the set's calls are each refused by name,
    rather than covered over fewer of them than the set holds (D188)."""
    with pytest.raises(CoverageError, match="traces name id\\(s\\) the set's findings do not hold"):
        set_coverage(
            "design set",
            RUBRIC,
            FINDINGS,
            parse_severity(SEVERITY_TEXT),
            {**TRACES, "J-policy-alignment": ("F-85", "F-999")},
            _readings(),
            CALLS,
        )
    with pytest.raises(CoverageError, match="findings sit on call\\(s\\) this set does not read"):
        set_coverage(
            "design set",
            RUBRIC,
            FINDINGS,
            parse_severity(SEVERITY_TEXT),
            TRACES,
            _readings(),
            tuple(call for call in CALLS if call != "CALL-18"),
        )
    unread = _readings()
    del unread["A-account-detail-disclosed-before-verification"]["CALL-12"]
    with pytest.raises(CoverageError, match="has no reading for CALL-12"):
        _coverage(unread)


def test_coverage_would_notice_a_band_on_text_that_moved() -> None:
    """A set whose finding was edited after its band was placed is refused, naming the
    finding, rather than covered under a severity nobody gave its wording (D189)."""
    edited = tuple(
        replace(finding, consequence=finding.consequence + " Edited after scoring.")
        if finding.id == "F-45"
        else finding
        for finding in FINDINGS
    )
    with pytest.raises(CoverageError, match=r"changed since it was scored: F-45$"):
        set_coverage(
            "design set",
            RUBRIC,
            edited,
            parse_severity(SEVERITY_TEXT),
            TRACES,
            _readings(),
            CALLS,
        )


def test_coverage_would_notice_a_band_split_wrong_by_detection_type() -> None:
    """Each band splits into the findings a deterministic check, the judge or only a
    human could detect, each with its own holds, traced and retired, and the parts add
    up to the band (D192).

    With every entry silent, the split's traced counts are the rubric's alone; firing
    the entry traced to F-04, an assert-type critical finding, retires one finding in
    the critical band's assert part and none in its judge part.
    """
    silent = _coverage(_readings())
    split = {
        (band.band, kind.value): (band.of(kind).holds, band.of(kind).traced)
        for band in silent.bands
        for kind in DetectableBy
    }
    assert split == {
        ("critical", "assert"): (3, 3),
        ("critical", "judge"): (1, 0),
        ("critical", "human"): (0, 0),
        ("high", "assert"): (14, 14),
        ("high", "judge"): (0, 0),
        ("high", "human"): (0, 0),
        ("medium", "assert"): (24, 24),
        ("medium", "judge"): (4, 3),
        ("medium", "human"): (0, 0),
        ("low", "assert"): (19, 19),
        ("low", "judge"): (18, 14),
        ("low", "human"): (0, 0),
    }
    for band in silent.bands:
        assert sum(band.of(kind).holds for kind in DetectableBy) == band.holds, band.band

    fired = _coverage(_readings(fired={"A-verification-claimed-on-mismatched-value": "CALL-01"}))
    critical = fired.bands[0]
    assert critical.of(DetectableBy.ASSERT).retired == 1
    assert critical.of(DetectableBy.JUDGE).retired == 0


def test_the_coverage_section_would_notice_its_bands_pooled() -> None:
    """One row per band, each followed by its three detection types, and no total
    across bands: a pooled figure is what D157 refused, and printing it beside the rows
    would invite reading it first (D188, D192)."""
    lines = render_coverage(_coverage(_readings()), DESIGN_COVERAGE_CAVEAT)
    start = lines.index("-" * 34) + 1
    table = lines[start : lines.index("", start)]
    bands = [row.split()[0] for row in table if not row.startswith(" ")]
    assert bands == list(BAND_ORDER), table
    kinds = [kind.value for kind in DetectableBy]
    for position in range(len(BAND_ORDER)):
        block = table[position * (1 + len(kinds)) : (position + 1) * (1 + len(kinds))]
        assert [row.split()[0] for row in block[1:]] == kinds, block
        assert all(row.startswith("  ") for row in block[1:]), block
    assert len(table) == len(BAND_ORDER) * (1 + len(kinds)), f"a row follows the bands: {table}"
    assert not any(" 83 " in f" {line} " for line in lines), "a figure pools the 83 banded findings"


def test_coverage_refuses_an_entry_with_no_traces_row_and_one_with_no_readings() -> None:
    """Two refusals the command itself cannot reach, and so had neither a test nor a
    control until the phase-5 audit's P5-6 found them: it always passes every entry's
    traces and every entry's readings.

    They exist for the caller that does not: an entry missing from the traces, or from
    the readings, would otherwise count as catching nothing and pull its findings into
    the uncovered set, which is a figure about the rubric read as a figure about the
    corpus (D188).
    """
    entry_id = RUBRIC.entries[0].id
    severity = parse_severity(SEVERITY_TEXT)

    thinned = {name: ids for name, ids in TRACES.items() if name != entry_id}
    with pytest.raises(CoverageError) as raised:
        set_coverage("design set", RUBRIC, FINDINGS, severity, thinned, _readings(), CALLS)
    assert f"no traces row for rubric entry id(s) {entry_id}" in str(raised.value)

    readings = _readings()
    del readings[entry_id]
    with pytest.raises(CoverageError) as raised:
        set_coverage("design set", RUBRIC, FINDINGS, severity, TRACES, readings, CALLS)
    assert f"no readings for rubric entry id(s) {entry_id}" in str(raised.value)
