"""Severity, joined by `id` from a file this project does not write.

`comparative-judgment` scores the findings and emits a **separate** severity
file. The harness reads it and joins on `id`. Two properties follow, and both
are enforced here rather than trusted:

* **The producing tool never mutates the findings document.** A `severity` field
  in `corpus/findings.yaml` is rejected by name in `harness.core.findings`.
  That file is the gold set and it **exists** -- adjudicated 2026-09-01, scored
  2026-09-05. This paragraph said it was "deliberately absent until a human has
  worked through the candidates", which was true when written and stopped being
  true four days later, in a docstring nothing reads back.
* **Provenance travels with the value.** The file carries the run, the anchor
  set and a hash of the comparison log, so a severity can always be traced back
  to the judgments that produced it. A missing provenance field is a break, not
  a warning -- a consumer that silently stopped seeing `unplaced` would report
  bands for findings nobody compared, which is the failure that field exists to
  prevent.

  **And, from schema 2, the text each band was placed on.** Every row carries
  the tool's `content_hash` of the finding it scored, and `finding_content_hash`
  recomputes it: `test_every_scored_finding_still_matches_the_text_it_was_scored_against`
  runs it over the gold set on every run, and the coverage report refuses a set
  holding a band on moved text (D189), so a finding edited after an export turns
  the suite red instead of leaving this file describing text that no longer
  exists. That is a second definition of one hash in two
  repositories, which this paragraph used to refuse -- rightly, while nothing
  compared the two. Compared on every run, a drift between the definitions is
  the same red as an edited finding (D148). `cj load` still refuses a changed
  finding at the source, and reports how many comparisons were made against the
  old text.

Extra fields are tolerated. The producing tool may add one without this refusing
to read the file; the interface scanner is what catches the two sides drifting
apart about what the fields *mean*.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from harness.core.findings import Finding, Tier

#: Every field the severity file must carry. `severities` and `unplaced` are the
#: payload; the rest is provenance. Asserted against the producing tool's own
#: specification by `tools/check_spec_interface.py` -- do not hand-verify it.
#: The bands in descending severity, and the three cuts between them in the same
#: order: a finding above the first cut's midpoint is `critical`, one between the
#: first and second midpoints `high`, and so on down. The producing tool's `BANDS`
#: and `CUT_ORDER`, restated so a file is checked against the rule its bands were
#: drawn by and not only against the rows it states (D171).
BAND_ORDER: Final[tuple[str, ...]] = ("critical", "high", "medium", "low")
CUT_ORDER: Final[tuple[str, ...]] = ("critical_high", "high_medium", "medium_low")

#: The bands a severity may carry. Closed, and checked at join time.
#:
#: `severity` was any string the producer wrote. The harness consumes this file
#: to band findings in a report, so an unrecognized label does not fail -- it
#: renders, as a band nobody defined, in a report whose whole purpose is to be
#: read. Validating a token is not recomputing the value, and this check stays a
#: check of the token; whether a band agrees with the cuts it was drawn by is
#: `_check_bands`', on load (D171).
SEVERITY_BANDS: Final[frozenset[str]] = frozenset(BAND_ORDER)

#: The one schema this reader accepts. Schema 2 added `content_hash`,
#: `appearances` and `informative` to every row (D148, and D33 in the producing
#: tool), and schema 3 added `cuts` (D156, and D34 there). Pinned rather than
#: treated as a floor: a newer schema may move a field this one reads, and
#: accepting it unseen is how a consumer ends up reporting something the
#: producer stopped meaning.
SEVERITY_SCHEMA_VERSION: Final[str] = "3"

SEVERITY_FIELDS: Final[tuple[str, ...]] = (
    "schema_version",
    "anchor_set_version",
    "comparison_log_hash",
    "run_id",
    "calibration",
    "severities",
    "unplaced",
    "cuts",
)

#: What every row inside `severities` must carry. **A separate tuple, because it
#: is a separate population** -- these are per-row keys and the ones above are
#: top-level, and folding them together would have the loader demand a
#: `content_hash` beside `run_id`. They were briefly folded together, in the
#: cross-repository scanner rather than here, and
#: `test_the_scanner_and_the_library_agree_about_severity_fields` caught it on
#: the run that introduced it (D148).
SEVERITY_ROW_FIELDS: Final[tuple[str, ...]] = (
    "id",
    "severity",
    "theta",
    "content_hash",
    "appearances",
    "informative",
)

#: What every entry inside `cuts` must carry, from schema 3. **Not asserted
#: across repositories**, unlike the two tuples above: the producing tool's
#: specification names `cuts` and not the fields inside an entry, so the
#: interface scanner checks the one and this loader checks the others. A field
#: renamed on the producing side is refused here instead, by every test that
#: loads the committed file, on the first re-export carrying the rename.
_CUT_FIELDS: Final[tuple[str, ...]] = ("name", "above_id", "below_id", "gap", "between")


class SeverityError(Exception):
    """Base for every refusal to read or join a severity file."""


@dataclass(frozen=True, slots=True)
class SeverityRecord:
    id: str
    severity: str
    theta: float
    content_hash: str
    """The hash of the finding text this band was placed on, written by the
    scoring tool at schema 2.

    **A band without it is a conclusion with its basis stripped off.** The tool
    refuses to load a judged finding whose text has changed, but that refusal
    fires only when somebody runs the tool, and the store holding the hashes is
    gitignored -- correctly, since a local judgment log is not a repository
    artifact. So until schema 2 this project could hold a severity file
    describing wording it no longer had, and did: a repository-wide spelling
    pass edited three judged findings on 2026-09-07 and nothing here noticed for
    four days (D140)."""
    appearances: int
    """Live comparisons this finding appears in."""
    informative: int
    """Those that were decided rather than tied.

    The two differ and the difference is the point. A tie is a judgment the tool
    keeps and the fit excludes, so ten appearances with eight ties is a band
    placed on two results -- the shape whose position moves furthest when one
    more comparison arrives, which is how one new finding silently re-banded
    three others (D144)."""


@dataclass(frozen=True, slots=True)
class SeverityCut:
    """One band cut as the file states it, accepted only once its rows agree.

    A cut is the two adjacent findings either side of a band boundary, and the
    boundary is their midpoint at each fit (D12 in the producing tool). **It can
    stop describing a gap with nothing refusing it**: placing F-90 took
    `high_medium` from adjacent anchors at a gap of 0.060 to 1.4005 with
    seventeen findings between them, and three of them changed band silently
    (D144). The tool reports how far apart each cut's anchors are and refuses
    nothing for it (D34 there), because a line between one finding inside a cut
    and seventeen would be a threshold nobody chose; this module re-derives
    what the file states and does not draw that line either (D156).

    **A cut is accepted only in a shape the tool can draw** (D171): one of the
    three names, stated once, anchored on two findings whose `theta` puts the
    one stated above above the one stated below, beside the other two cuts with
    midpoints in descending severity."""

    name: str
    above_id: str
    below_id: str
    gap: float
    """The anchor above's `theta` minus the anchor below's."""
    between: tuple[str, ...]
    """The scored findings strictly between the two anchors, most severe first."""


@dataclass(frozen=True, slots=True)
class SeverityFile:
    schema_version: str
    anchor_set_version: str
    comparison_log_hash: str
    run_id: str
    """Derived, not minted -- a hash of the log, the anchor set and the cuts. Two
    exports from an unchanged state carry the same id, so it names the *result*
    rather than the act of exporting."""
    calibration: tuple[tuple[str, str], ...]
    """What each band boundary was drawn against. Surfaced rather than dropped:
    a pairwise scale has no origin, so an ordering can be internally perfect
    while the whole set sits a band too high, and this is the only thing that
    would tell a reader."""
    severities: tuple[SeverityRecord, ...]
    unplaced: tuple[str, ...]
    """Findings nobody compared. They get no band rather than a defaulted one --
    banding them would report the prior as though it were a judgment."""
    cuts: tuple[SeverityCut, ...]
    """Every band cut, each re-derived from this file's own rows before it was
    accepted. All three are required, as the tool draws them, so an empty list is
    refused rather than read as a file stating no cuts (D171); the committed
    file's are also pinned by a test, which notices them moving."""


@dataclass(frozen=True, slots=True)
class JoinedFinding:
    finding: Finding
    severity: SeverityRecord | None
    """`None` for an unplaced finding and for every `tier: question` entry. Not
    a default and not a zero: the absence is the information."""


def parse_severity(text: str) -> SeverityFile:
    document: Any = json.loads(text)
    if not isinstance(document, dict):
        raise SeverityError("severity file must be a JSON object")

    missing = tuple(field for field in SEVERITY_FIELDS if field not in document)
    if missing:
        raise SeverityError(
            f"severity file is missing required field(s): {', '.join(missing)}. "
            "Every one is required: the payload is unusable without `severities`, and dropping a "
            "provenance field makes a value untraceable to the judgments behind it."
        )

    declared = str(document["schema_version"])
    if declared != SEVERITY_SCHEMA_VERSION:
        raise SeverityError(
            f"severity file declares schema_version {declared!r}; this harness reads "
            f"{SEVERITY_SCHEMA_VERSION!r}. Refused by version rather than by a missing field, "
            "because the producing tool's contract tolerates extra fields -- so absence is legal "
            "and a check that tolerated it would assert nothing."
        )

    raw_severities = document["severities"]
    if not isinstance(raw_severities, list):
        raise SeverityError("'severities' must be a list")
    records: list[SeverityRecord] = []
    for position, row in enumerate(raw_severities, start=1):
        if not isinstance(row, dict):
            raise SeverityError(f"severities[{position}] must be a mapping")
        for key in SEVERITY_ROW_FIELDS:
            if key not in row:
                raise SeverityError(
                    f"severities[{position}] is missing {key!r}. Schema 2 requires every row to "
                    "say what it scored and how well determined it is; a file written before that "
                    "declares schema_version 1 and is refused above by name."
                )
        try:
            theta = float(row["theta"])
        except (TypeError, ValueError) as exc:
            # Every other malformation in this function raises SeverityError;
            # `float()` raised ValueError straight through the contract, so a
            # caller catching SeverityError caught everything except a
            # non-numeric theta.
            raise SeverityError(
                f"severities[{position}] has a non-numeric theta: {row['theta']!r}"
            ) from exc
        try:
            appearances = int(row["appearances"])
            informative = int(row["informative"])
        except (TypeError, ValueError) as exc:
            raise SeverityError(
                f"severities[{position}] has non-integer comparison counts: "
                f"appearances={row['appearances']!r}, informative={row['informative']!r}"
            ) from exc
        if not 0 <= informative <= appearances:
            raise SeverityError(
                f"severities[{position}] reports {informative} decided comparisons out of "
                f"{appearances}, which cannot both be true"
            )
        records.append(
            SeverityRecord(
                id=str(row["id"]),
                severity=str(row["severity"]),
                theta=theta,
                content_hash=str(row["content_hash"]),
                appearances=appearances,
                informative=informative,
            )
        )

    raw_cuts = document["cuts"]
    if not isinstance(raw_cuts, list):
        raise SeverityError("'cuts' must be a list")
    cuts = _cuts(raw_cuts, records)
    _check_bands(records, cuts)

    raw_unplaced = document["unplaced"]
    if not isinstance(raw_unplaced, list):
        raise SeverityError("'unplaced' must be a list")

    raw_calibration = document["calibration"]
    if not isinstance(raw_calibration, dict):
        raise SeverityError("'calibration' must be a mapping")

    return SeverityFile(
        schema_version=str(document["schema_version"]),
        anchor_set_version=str(document["anchor_set_version"]),
        comparison_log_hash=str(document["comparison_log_hash"]),
        run_id=str(document["run_id"]),
        calibration=tuple(sorted((str(k), str(v)) for k, v in raw_calibration.items())),
        severities=tuple(records),
        unplaced=tuple(str(item) for item in raw_unplaced),
        cuts=cuts,
    )


def _cuts(raw_cuts: list[Any], records: list[SeverityRecord]) -> tuple[SeverityCut, ...]:
    """Each cut as the file states it, refused where the file's own rows disagree.

    The file says which findings lie strictly between a cut's anchors, and it
    carries every finding's `theta`, so the first is recomputable from the
    second. Recomputing it here is **a second definition of one rule in two
    repositories** -- strictly between, most severe first -- which is the shape
    D82 refused for the content hash and D148 accepted once something compared
    the two. Compared on every load, a between-set or a gap the rows contradict
    is the same red whether the file was edited by hand or the two definitions
    have drifted apart (D156).

    The gap is compared exactly. JSON carries a float's shortest round-trip
    form, so the `theta` read back are the values the tool subtracted, and the
    subtraction repeats bit for bit.

    **And a cut the tool could not have drawn is refused** (OB-25, D171), as its
    `thresholds` refuses it: a name outside the three, a name stated twice, an
    anchor pair the file's own `theta` inverts or collapses to one finding, a
    missing cut, and midpoints out of descending severity, which is two
    boundaries crossed. An inverted cut passed the gap and between-set checks,
    its negative gap and empty between-set both consistent with its rows (P4-5).
    """
    theta = {record.id: record.theta for record in records}
    ranked = sorted(records, key=lambda record: (-record.theta, record.id))
    cuts: list[SeverityCut] = []
    for position, entry in enumerate(raw_cuts, start=1):
        if not isinstance(entry, dict):
            raise SeverityError(f"cuts[{position}] must be a mapping")
        for key in _CUT_FIELDS:
            if key not in entry:
                raise SeverityError(f"cuts[{position}] is missing {key!r}")
        name = str(entry["name"])
        if name not in CUT_ORDER:
            raise SeverityError(
                f"cuts[{position}] is named {name!r}; a cut is one of {', '.join(CUT_ORDER)}, "
                "the three boundaries between the four bands"
            )
        if any(cut.name == name for cut in cuts):
            raise SeverityError(f"cut {name!r} is defined more than once")
        above_id = str(entry["above_id"])
        below_id = str(entry["below_id"])
        try:
            gap = float(entry["gap"])
        except (TypeError, ValueError) as exc:
            raise SeverityError(
                f"cuts[{position}] has a non-numeric gap: {entry['gap']!r}"
            ) from exc
        if not isinstance(entry["between"], list):
            raise SeverityError(f"cuts[{position}] 'between' must be a list")
        between = tuple(str(item) for item in entry["between"])

        unscored = sorted({above_id, below_id} - set(theta))
        if unscored:
            raise SeverityError(
                f"cut {name!r} is anchored on {', '.join(unscored)}, which this file does not "
                "score, so nothing in the file says where the cut lies"
            )
        if theta[above_id] <= theta[below_id]:
            raise SeverityError(
                f"cut {name!r} has inverted: {above_id} is stated above {below_id}, and the "
                f"file's own theta puts it at or below ({theta[above_id]!r} against "
                f"{theta[below_id]!r}). A boundary drawn between two findings means nothing "
                "once they have swapped, or when they are one finding."
            )
        if gap != theta[above_id] - theta[below_id]:
            raise SeverityError(
                f"cut {name!r} states a gap of {gap!r} and the theta of {above_id} and "
                f"{below_id} differ by {theta[above_id] - theta[below_id]!r}. The file "
                "disagrees with itself: re-export it rather than editing either figure."
            )
        derived = tuple(
            record.id for record in ranked if theta[below_id] < record.theta < theta[above_id]
        )
        if between != derived:
            raise SeverityError(
                f"cut {name!r} lists {', '.join(between) or 'nothing'} strictly between "
                f"{above_id} and {below_id}, and the file's own theta puts "
                f"{', '.join(derived) or 'nothing'} there, most severe first. The file disagrees "
                "with itself: re-export it rather than editing either field."
            )
        cuts.append(
            SeverityCut(name=name, above_id=above_id, below_id=below_id, gap=gap, between=between)
        )
    absent_cuts = [name for name in CUT_ORDER if all(cut.name != name for cut in cuts)]
    if absent_cuts:
        raise SeverityError(
            f"the file states no cut {', '.join(absent_cuts)}; the tool draws all three, and a "
            "band cannot be placed without them"
        )
    midpoints = _midpoints(cuts, theta)
    if any(higher <= lower for higher, lower in itertools.pairwise(midpoints)):
        stated = ", ".join(
            f"{name} {value!r}" for name, value in zip(CUT_ORDER, midpoints, strict=True)
        )
        raise SeverityError(
            "the cuts' midpoints are not in descending severity order, so two boundaries have "
            f"crossed: {stated}"
        )
    return tuple(cuts)


def _midpoints(cuts: Sequence[SeverityCut], theta: dict[str, float]) -> tuple[float, ...]:
    """Each cut's boundary, the midpoint of its anchors' `theta`, in `CUT_ORDER`."""
    by_name = {cut.name: cut for cut in cuts}
    return tuple(
        (theta[by_name[name].above_id] + theta[by_name[name].below_id]) / 2 for name in CUT_ORDER
    )


def _band_for(value: float, midpoints: Sequence[float]) -> str:
    """The band a `theta` falls in, walking the midpoints from most severe down.

    A value exactly on a midpoint falls to the less severe side, as the tool's
    `band_for` places it: a band is not inflated by a tie with a boundary drawn
    between two other findings.
    """
    for index, midpoint in enumerate(midpoints):
        if value > midpoint:
            return BAND_ORDER[index]
    return BAND_ORDER[len(midpoints)]


def _check_bands(records: Sequence[SeverityRecord], cuts: Sequence[SeverityCut]) -> None:
    """Refuse a row whose band is not the one its `theta` falls in (OB-25, D171).

    The tool bands a finding by the side of each cut's midpoint its `theta` falls
    on, so the file carries everything that decides a band beside the band
    itself: a second definition of one rule, compared on every load as the
    between-set is. A row can cross a midpoint while staying between that cut's
    anchors, which the between-set, the gap and both pins on the committed file
    all pass (P4-5). A band outside the vocabulary is left to `join`, which names
    it as a band nobody defined rather than as a misplaced one.
    """
    theta = {record.id: record.theta for record in records}
    midpoints = _midpoints(cuts, theta)
    for record in records:
        if record.severity not in SEVERITY_BANDS:
            continue
        derived = _band_for(record.theta, midpoints)
        if record.severity != derived:
            raise SeverityError(
                f"{record.id} is banded {record.severity!r} and its theta {record.theta!r} "
                f"falls in {derived!r} by the cuts' midpoints. The file disagrees with itself: "
                "re-export it rather than editing either field."
            )


def load_severity(path: Path) -> SeverityFile:
    return parse_severity(path.read_text(encoding="utf-8"))


def join(findings: tuple[Finding, ...], severity: SeverityFile) -> tuple[JoinedFinding, ...]:
    """Join severity onto findings by `id`. The join is total, and refuses if not.

    A `tier: defect` finding that appears in neither `severities` nor `unplaced`
    means the severity file does not know about it -- the two documents describe
    different sets, and any coverage arithmetic over them would be wrong while
    looking right. That refuses by name.

    A `tier: question` finding is *expected* to be absent from both: the scoring
    tool excludes questions and reports the count, because rating a non-defect
    would put it into the anchor set where it would distort every later
    placement.
    """
    by_id = {record.id: record for record in severity.severities}
    unplaced = set(severity.unplaced)

    duplicated = len(severity.severities) - len(by_id)
    if duplicated:
        raise SeverityError(f"severity file scores {duplicated} id(s) more than once")
    both = sorted(set(by_id) & unplaced)
    if both:
        raise SeverityError(f"id(s) both scored and unplaced: {', '.join(both)}")

    known = {finding.id for finding in findings}
    strangers = sorted((set(by_id) | unplaced) - known)
    if strangers:
        raise SeverityError(
            f"severity file names id(s) absent from the findings document: {', '.join(strangers)}"
        )

    # A scored question. The docstring above says a question is *expected* to be
    # absent, and the join tolerated its absence -- it did not refuse its
    # presence. The two are different claims, and only one of them was checked:
    # a question that reached the anchor set would distort every later placement,
    # which is the reason for excluding it, so its appearance here is the defect
    # worth naming rather than the shape to shrug at.
    questions = {finding.id for finding in findings if finding.tier is not Tier.DEFECT}
    scored_questions = sorted((set(by_id) | unplaced) & questions)
    if scored_questions:
        raise SeverityError(
            "severity file scores or unplaces question-tier id(s), which the scoring tool "
            f"excludes by design: {', '.join(scored_questions)}"
        )

    unknown_bands = sorted({record.severity for record in severity.severities} - SEVERITY_BANDS)
    if unknown_bands:
        raise SeverityError(
            f"severity file uses band(s) outside the vocabulary: {', '.join(unknown_bands)}; "
            f"expected one of {', '.join(sorted(SEVERITY_BANDS))}"
        )

    joined: list[JoinedFinding] = []
    orphans: list[str] = []
    for finding in findings:
        record = by_id.get(finding.id)
        if record is None and finding.id not in unplaced and finding.tier is Tier.DEFECT:
            orphans.append(finding.id)
        joined.append(JoinedFinding(finding=finding, severity=record))
    if orphans:
        raise SeverityError(
            "defect-tier finding(s) appear in neither 'severities' nor 'unplaced': "
            f"{', '.join(orphans)}. The two documents describe different sets."
        )
    return tuple(joined)


def finding_content_hash(finding: Finding) -> str:
    """The scoring tool's hash of the text a band was placed on, recomputed (D148, D189).

    **A second definition of one hash in two repositories**, which D82 rejected while
    nothing compared the two and D148 accepted once something did: compared against
    the `content_hash` every row carries, a drift between the definitions is the same
    red as a finding edited after it was scored. It lived in the suite until D189,
    which moved it here so the coverage report can refuse a band on moved text rather
    than only the suite noticing it, and only for the design set.

    The shape is the tool's: observation, then consequence, then evidence in order,
    each stripped and joined with a separator that cannot occur in the text, so two
    decompositions cannot collide.
    """
    parts = [
        finding.observation.strip(),
        finding.consequence.strip(),
        *(fragment.strip() for fragment in finding.evidence),
    ]
    return hashlib.sha256("\x00".join(parts).encode("utf-8")).hexdigest()


def moved_since_scored(findings: Sequence[Finding], severity: SeverityFile) -> tuple[str, ...]:
    """The scored ids whose finding text no longer hashes to the one their band was
    placed on, in the file's order (D140, D189).

    A band on moved text describes wording nobody compared, which is what `e28650c`
    left behind for four days. A row naming an id `findings` does not hold is `join`'s
    to refuse, and is passed over here.
    """
    by_id = {finding.id: finding for finding in findings}
    return tuple(
        record.id
        for record in severity.severities
        if record.id in by_id and finding_content_hash(by_id[record.id]) != record.content_hash
    )
