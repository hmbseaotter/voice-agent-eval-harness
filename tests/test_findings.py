"""Findings schema, the Markdown view, and the severity join.

The findings document is two things at once -- the traceability anchor every
rubric entry resolves to, and the gold set judge agreement is measured against.
Both roles fail quietly rather than loudly if the schema slips, so the checks
here are about the shape of the document rather than its content.

Three deserve the emphasis they get:

* **A severity field is rejected BY NAME.** Not ignored, not dropped. Severity is
  joined by id from a file this project does not write; the field appearing here
  means either something wrote to a document it does not own, or a person is
  about to hand-maintain a value with no provenance. The second is worse,
  because it looks fine.
* **Three evidence fragments round-trip as three.** That is the entire reason the
  format is YAML rather than a Markdown table (D22): a table cell physically
  cannot keep fragments from different points in a call separate.
* **The generated view regenerates identically.** A generated file nobody
  verifies drifts from its source and becomes a second, disagreeing source.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
import yaml

from harness.core.findings import (
    REQUIRED_KEYS,
    DetectableBy,
    Finding,
    FindingsError,
    SeverityFieldPresentError,
    Tier,
    dump_findings,
    load_findings,
    parse_findings,
    render_markdown,
)
from harness.core.severity import (
    SEVERITY_BANDS,
    SEVERITY_FIELDS,
    JoinedFinding,
    SeverityCut,
    SeverityError,
    SeverityFile,
    SeverityRecord,
    finding_content_hash,
    join,
    load_severity,
    moved_since_scored,
    parse_severity,
)
from harness.findings_view import main as view_main

REPO_ROOT: Path = Path(__file__).resolve().parents[1]
FIXTURES: Path = Path(__file__).resolve().parent / "fixtures"
SMALL: Path = FIXTURES / "findings_small.yaml"
SMALL_SEVERITY: Path = FIXTURES / "severity_small.json"
CANDIDATES: Path = REPO_ROOT / "corpus" / "findings.candidates.yaml"
GOLD: Path = REPO_ROOT / "corpus" / "findings.yaml"


# --------------------------------------------------------------------------
# Schema
# --------------------------------------------------------------------------


def test_every_entry_carries_every_required_key() -> None:
    """The acceptance criterion is that the count lacking any of them is zero.

    **Over the gold set, not the drafts.** This loaded `findings.candidates.yaml`
    while the criterion it backs is about "the findings document", which D77
    settled as `corpus/findings.yaml`. The drafts are an input to adjudication;
    the gold set is what agreement is measured against and what every downstream
    reader sees, so a criterion verified against the drafts is verified against
    the wrong document -- and would stay green if the two diverged.
    """
    findings = load_findings(GOLD)
    assert findings
    lacking = [
        f.id
        for f in findings
        if not all(getattr(f, key) for key in REQUIRED_KEYS if key not in {"detectable_by", "tier"})
    ]
    assert lacking == []
    for finding in findings:
        assert isinstance(finding.detectable_by, DetectableBy)
        assert isinstance(finding.tier, Tier)


def test_three_evidence_fragments_round_trip_as_three() -> None:
    findings = load_findings(SMALL)
    original = next(f for f in findings if f.id == "F-90")
    assert len(original.evidence) == 3

    round_tripped = parse_findings(dump_findings(findings))
    recovered = next(f for f in round_tripped if f.id == "F-90")

    assert len(recovered.evidence) == 3
    assert recovered.evidence == original.evidence
    # Distinct, not merely three-of-something: the fixture's fragments are
    # deliberately similar, so a collapse would still look plausible.
    assert len(set(recovered.evidence)) == 3
    # And each keeps its own internal newline rather than being folded.
    assert all("\n" in fragment for fragment in recovered.evidence)


def test_a_severity_field_is_rejected_by_name() -> None:
    document = """
findings:
  - id: F-01
    call_ref: CALL-01
    owner: agent
    observation: An observation.
    evidence:
      - 'event 1 — something'
    consequence: A consequence.
    detectable_by: assert
    tier: defect
    severity: critical
"""
    with pytest.raises(SeverityFieldPresentError) as caught:
        parse_findings(document)
    message = str(caught.value)
    assert "F-01" in message, "the refusal must name the offending finding"
    assert "severity" in message, "the refusal must name the offending field"
    assert "joined" in message or "separate file" in message


def test_evidence_must_be_a_list_not_a_string() -> None:
    """A string is iterable, so a loader that only checked truthiness would
    accept one and silently produce one-character 'fragments'."""
    document = """
findings:
  - id: F-01
    call_ref: CALL-01
    owner: agent
    observation: An observation.
    evidence: 'event 1 — something'
    consequence: A consequence.
    detectable_by: assert
    tier: defect
"""
    with pytest.raises(FindingsError, match="non-empty list"):
        parse_findings(document)


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("    detectable_by: assert\n", "missing required key"),
        ("    tier: defect\n", "missing required key"),
        ("    consequence: A consequence.\n", "missing required key"),
        ("    owner: agent\n", "missing required key"),
    ],
    ids=["no-detectable-by", "no-tier", "no-consequence", "no-owner"],
)
def test_a_missing_required_key_is_refused(mutation: str, expected: str) -> None:
    document = """
findings:
  - id: F-01
    call_ref: CALL-01
    owner: agent
    observation: An observation.
    evidence:
      - 'event 1 — something'
    consequence: A consequence.
    detectable_by: assert
    tier: defect
"""
    with pytest.raises(FindingsError, match=expected):
        parse_findings(document.replace(mutation, ""))


def test_an_unknown_key_is_refused_rather_than_ignored() -> None:
    """Silently tolerating an unknown key is how a typo'd key becomes an absent
    value nobody notices -- the same rule the transcript adapter applies to
    metadata."""
    document = """
findings:
  - id: F-01
    call_ref: CALL-01
    owner: agent
    observation: An observation.
    evidence:
      - 'event 1 — something'
    consequence: A consequence.
    detectible_by: assert
    detectable_by: assert
    tier: defect
"""
    with pytest.raises(FindingsError, match="unknown key"):
        parse_findings(document)


def test_a_duplicate_id_is_refused() -> None:
    findings = load_findings(SMALL)
    doubled = dump_findings((*findings, findings[0]))
    with pytest.raises(FindingsError, match="duplicate finding id"):
        parse_findings(doubled)


@pytest.mark.parametrize(
    ("field", "value"),
    [("owner", "everyone"), ("detectable_by", "maybe"), ("tier", "concern")],
)
def test_a_value_outside_its_vocabulary_is_refused(field: str, value: str) -> None:
    """`owner` was the one closed vocabulary with no case here.

    It is the field D43 added, it is what makes a row actionable by one team
    rather than by nobody, and the loader has always enforced it -- so the gap
    was in the test, not the code. The document is now built from a mapping
    rather than spliced with conditionals, which is why the field could be added
    by naming it once instead of by editing three lines.
    """
    fields = {"owner": "agent", "detectable_by": "assert", "tier": "defect"}
    fields[field] = value
    document = f"""
findings:
  - id: F-01
    call_ref: CALL-01
    owner: {fields["owner"]}
    observation: An observation.
    evidence:
      - 'event 1 — something'
    consequence: A consequence.
    detectable_by: {fields["detectable_by"]}
    tier: {fields["tier"]}
"""
    with pytest.raises(FindingsError, match=field):
        parse_findings(document)


def test_every_closed_vocabulary_on_a_finding_has_a_case_above() -> None:
    """The parametrization is a list somebody maintains, so it drifts from the
    schema the way every other list in this project has. This is the check that
    it has not: a new closed vocabulary on a finding needs a case."""
    covered = {"owner", "detectable_by", "tier"}
    enumerated = {
        name
        for name, annotation in Finding.__annotations__.items()
        if isinstance(annotation, str) and annotation in {"Owner", "DetectableBy", "Tier"}
    }
    assert enumerated == covered, (
        f"Finding carries closed vocabularies {sorted(enumerated)}; "
        f"the parametrization covers {sorted(covered)}"
    )


def test_gold_set_ids_are_unique_and_every_call_ref_resolves() -> None:
    findings = load_findings(GOLD)
    ids = [f.id for f in findings]
    assert len(set(ids)) == len(ids)
    transcripts = {p.stem for p in (REPO_ROOT / "corpus" / "transcripts").glob("*.txt")}
    unresolved = sorted({f.call_ref for f in findings} - transcripts)
    assert unresolved == [], f"call_ref values with no transcript: {unresolved}"


# --------------------------------------------------------------------------
# The generated view
# --------------------------------------------------------------------------


def test_the_markdown_view_regenerates_identically() -> None:
    """The view is of the **gold set**, and for two days it was not.

    The spec's P1 criterion reads "the generated Markdown view of *the findings
    document*", and what existed was a view of the candidates -- titled
    "Findings - design set", stating 81 defects and 8 questions against a gold
    set holding 82 and 7, and carrying pre-ruling text for 21 rows, 14 of them
    differing in the evidence a reader checks against the transcript. A reviewer
    reading it was reading proposals in the rows where a proposal had been
    revised, which is exactly where reading matters most.
    """
    findings = load_findings(GOLD)
    once = render_markdown(findings)
    twice = render_markdown(findings)
    assert once == twice

    on_disk = REPO_ROOT / "corpus" / "findings.md"
    assert on_disk.is_file(), "the view has never been generated"
    assert on_disk.read_text(encoding="utf-8") == once, "the view on disk is stale"


def test_the_view_checker_reports_a_stale_view(tmp_path: Path) -> None:
    stale = tmp_path / "view.md"
    stale.write_text("not the view\n", encoding="utf-8")
    assert view_main(["--findings", str(CANDIDATES), "--out", str(stale), "--check"]) == 1
    assert view_main(["--findings", str(CANDIDATES), "--out", str(stale)]) == 0
    assert view_main(["--findings", str(CANDIDATES), "--out", str(stale), "--check"]) == 0


def test_the_view_renders_evidence_as_a_list_not_a_cell() -> None:
    """A view that flattened three fragments into one cell would quietly undo
    the reason this document is YAML."""
    rendered = render_markdown(load_findings(SMALL))
    assert "1. event 4" in rendered
    assert "2. event 9" in rendered
    assert "3. event 14" in rendered


# --------------------------------------------------------------------------
# Severity, joined by id
# --------------------------------------------------------------------------


def test_the_severity_file_parses_with_every_top_level_field() -> None:
    severity = load_severity(SMALL_SEVERITY)
    assert severity.schema_version == "3"
    assert severity.run_id == "4f2c9a10be77d3e5"
    assert severity.unplaced == ("F-92",)
    assert dict(severity.calibration)["critical_high"].startswith("Critical means")
    assert [cut.name for cut in severity.cuts] == ["critical_high", "high_medium", "medium_low"]


@pytest.mark.parametrize("field", SEVERITY_FIELDS)
def test_a_missing_severity_field_is_a_break(field: str) -> None:
    document = json.loads(SMALL_SEVERITY.read_text(encoding="utf-8"))
    del document[field]
    with pytest.raises(SeverityError, match=field):
        parse_severity(json.dumps(document))


def test_an_extra_severity_field_is_tolerated() -> None:
    """The producing tool may add a field without this refusing to read it. The
    interface scanner is what catches the two sides drifting about meaning."""
    severity = load_severity(SMALL_SEVERITY)
    assert severity.run_id  # `tool_version` in the fixture is simply ignored


def test_severity_joins_on_id_and_unplaced_gets_no_band() -> None:
    findings = load_findings(SMALL)
    joined = join(findings, load_severity(SMALL_SEVERITY))
    by_id = {j.finding.id: j for j in joined}

    assert by_id["F-90"].severity is not None
    assert by_id["F-90"].severity.severity == "critical"
    # Unplaced: no band rather than a defaulted one. The absence is the
    # information -- banding it would report the prior as though it were a
    # judgment.
    assert by_id["F-92"].severity is None
    # A question-tier entry is excluded from scoring by the tool, so its
    # absence is expected rather than a gap.
    assert by_id["F-91"].finding.tier is Tier.QUESTION
    assert by_id["F-91"].severity is None


def test_a_defect_in_neither_severities_nor_unplaced_refuses_by_name() -> None:
    findings = load_findings(SMALL)
    severity = SeverityFile(
        schema_version="3",
        anchor_set_version="1",
        comparison_log_hash="deadbeef",
        run_id="0",
        calibration=(),
        severities=(
            SeverityRecord(
                id="F-90",
                severity="critical",
                theta=2.0,
                content_hash="0" * 64,
                appearances=10,
                informative=8,
            ),
        ),
        unplaced=(),
        cuts=(),
    )
    with pytest.raises(SeverityError, match="F-92"):
        join(findings, severity)


def test_a_severity_file_naming_an_unknown_finding_refuses() -> None:
    findings = load_findings(SMALL)
    severity = SeverityFile(
        schema_version="3",
        anchor_set_version="1",
        comparison_log_hash="deadbeef",
        run_id="0",
        calibration=(),
        severities=(
            SeverityRecord(
                id="F-999",
                severity="low",
                theta=0.0,
                content_hash="0" * 64,
                appearances=10,
                informative=8,
            ),
        ),
        unplaced=("F-92",),
        cuts=(),
    )
    with pytest.raises(SeverityError, match="F-999"):
        join(findings, severity)


def test_an_id_both_scored_and_unplaced_refuses() -> None:
    findings = load_findings(SMALL)
    severity = SeverityFile(
        schema_version="3",
        anchor_set_version="1",
        comparison_log_hash="deadbeef",
        run_id="0",
        calibration=(),
        severities=(
            SeverityRecord(
                id="F-90",
                severity="critical",
                theta=2.0,
                content_hash="0" * 64,
                appearances=10,
                informative=8,
            ),
        ),
        unplaced=("F-90", "F-92"),
        cuts=(),
    )
    with pytest.raises(SeverityError, match="both scored and unplaced"):
        join(findings, severity)


def test_the_join_is_total_over_the_gold_set() -> None:
    """The small fixture proves file parsing; this proves the join at the
    corpus's real size, so a scoring run covering every defect resolves."""
    findings = load_findings(GOLD)
    defects = tuple(f for f in findings if f.tier is Tier.DEFECT)
    severity = SeverityFile(
        schema_version="3",
        anchor_set_version="1",
        comparison_log_hash="0" * 64,
        run_id="synthetic",
        calibration=(("critical_high", "placeholder"),),
        severities=tuple(
            SeverityRecord(
                id=f.id,
                severity="medium",
                theta=0.0,
                content_hash="0" * 64,
                appearances=10,
                informative=8,
            )
            for f in defects[:-1]
        ),
        unplaced=(defects[-1].id,),
        cuts=(),
    )
    joined = join(findings, severity)
    assert len(joined) == len(findings)
    assert isinstance(joined[0], JoinedFinding)
    banded = [j for j in joined if j.severity is not None]
    assert len(banded) == len(defects) - 1
    # Question-tier entries are excluded from scoring by the tool, so their
    # absence from both lists is expected rather than a gap. Asserted only when
    # the candidate set carries one -- during a rebuild it may not yet.
    questions = [j for j in joined if j.finding.tier is Tier.QUESTION]
    assert all(j.severity is None for j in questions)


# --------------------------------------------------------------------------
# The severity parser's malformation paths (T6)
# --------------------------------------------------------------------------


def test_every_scored_finding_still_matches_the_text_it_was_scored_against() -> None:
    """What OB-18 was owed for, and what four days of silence bought.

    A severity band describes a finding's text. Until schema 2 the exported file
    said which finding and not which text, so `corpus/findings.yaml` could be
    edited and every band went on describing wording nobody had compared --
    detectable only by somebody running `cj load`, which is the tool nobody runs
    during a repository-wide sweep. `e28650c` was exactly that sweep: 51
    spellings across 17 files on 2026-09-07, three of them inside judged
    findings, unnoticed until 2026-09-11 (D140).

    Now the file carries the hash and this recomputes it, through the harness's
    own `finding_content_hash` rather than a copy kept here (D189), so the suite and
    the coverage report cannot come to disagree about what the hash covers. A
    finding edited after export fails here, in the suite, on the commit that edits
    it.
    """
    findings = {finding.id: finding for finding in load_findings(GOLD)}
    severity = load_severity(REPO_ROOT / "corpus" / "findings.severity.json")

    moved: list[str] = []
    for record in severity.severities:
        finding = findings.get(record.id)
        assert finding is not None, f"{record.id} is scored and absent from the gold set"
        if finding_content_hash(finding) != record.content_hash:
            moved.append(record.id)

    assert not moved, (
        "severity band(s) describe text that has since changed: "
        f"{', '.join(sorted(moved))}. Either the finding was edited after it was scored -- in "
        "which case re-run `cj load --accept-revisions` and re-export -- or this project's copy of "
        "the hash has drifted from the scoring tool's, which is the other thing this comparison "
        "exists to catch."
    )


def test_the_recheck_would_notice_a_finding_edited_after_scoring() -> None:
    """The harness's recheck names exactly the scored findings whose text has moved,
    and passes over a row the findings do not hold, which is the join's to refuse
    (D140, D189).

    One word of F-85's observation is changed, which is the size of edit `e28650c`
    made, and one fragment of F-04's evidence gains trailing whitespace, which the
    tool's hash strips and so does not count as a move.
    """
    findings = load_findings(GOLD)
    severity = load_severity(REPO_ROOT / "corpus" / "findings.severity.json")
    assert moved_since_scored(findings, severity) == ()

    def edited(finding: Finding) -> Finding:
        if finding.id == "F-85":
            return replace(finding, observation=finding.observation.replace(" the ", " a ", 1))
        if finding.id == "F-04":
            return replace(finding, evidence=(finding.evidence[0] + "  ", *finding.evidence[1:]))
        return finding

    moved = tuple(edited(finding) for finding in findings)
    assert moved[[f.id for f in moved].index("F-85")].observation != next(
        f.observation for f in findings if f.id == "F-85"
    ), "the planted edit changed nothing"
    assert moved_since_scored(moved, severity) == ("F-85",)
    assert moved_since_scored(tuple(f for f in findings if f.id != "F-85"), severity) == ()


def test_a_severity_row_records_how_well_determined_it_is() -> None:
    """OB-21. Two rows that look identical can rest on very different evidence.

    Asserted as a property rather than as a table of numbers: every row reports
    at least one comparison, and no row claims more decided comparisons than it
    has. The corpus demonstrates why the field is worth carrying -- F-90's band
    rests on three comparisons where every other finding's rests on ten, and
    before schema 2 nothing in the file distinguished them (D144).
    """
    severity = load_severity(REPO_ROOT / "corpus" / "findings.severity.json")
    spread = {record.informative for record in severity.severities}
    assert len(spread) > 1, (
        "every scored finding reports the same number of decided comparisons, so the field is "
        "carrying no information and this test is asserting nothing"
    )
    for record in severity.severities:
        assert record.appearances >= record.informative >= 0, record.id
        assert record.appearances > 0, (
            f"{record.id} carries a band on no comparisons at all, which `unplaced` exists to "
            "report instead"
        )


def _severity_document() -> dict[str, Any]:
    """The fixture as mutable JSON. Typed `Any` deliberately: these tests
    deform the document in ways a precise type would forbid, which is the
    point of them."""
    document = json.loads((FIXTURES / "severity_small.json").read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    return document


def _one_cut(**fields: object) -> dict[str, object]:
    """A cut on the fixture's one scored finding, with `fields` replacing its own.

    Anchored on F-90 at both ends, which the producing tool never writes and
    this loader refuses (D171) -- but only after the field checks these cases
    exercise, so each malformed case still deforms only the field it names. A
    field set to `None` is removed.
    """
    cut: dict[str, object] = {
        "name": "critical_high",
        "above_id": "F-90",
        "below_id": "F-90",
        "gap": 0.0,
        "between": [],
    }
    cut.update(fields)
    return {key: value for key, value in cut.items() if value is not None}


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (lambda d: d.__setitem__("severities", {"F-90": "critical"}), "must be a list"),
        (lambda d: d.__setitem__("unplaced", "F-91"), "must be a list"),
        (lambda d: d.__setitem__("calibration", ["top"]), "must be a mapping"),
        (lambda d: d["severities"].__setitem__(0, ["F-90", "critical", 2.14]), "must be a mapping"),
        (lambda d: d["severities"][0].pop("theta"), "missing 'theta'"),
        (lambda d: d["severities"][0].pop("severity"), "missing 'severity'"),
        (lambda d: d["severities"][0].pop("id"), "missing 'id'"),
        (lambda d: d["severities"][0].__setitem__("theta", "quite high"), "non-numeric theta"),
        (lambda d: d.__setitem__("cuts", {"critical_high": _one_cut()}), "'cuts' must be a list"),
        (lambda d: d.__setitem__("cuts", [["F-90"]]), r"cuts\[1\] must be a mapping"),
        (lambda d: d.__setitem__("cuts", [_one_cut(between=None)]), "missing 'between'"),
        (lambda d: d.__setitem__("cuts", [_one_cut(gap="wide")]), "non-numeric gap"),
        (lambda d: d.__setitem__("cuts", [_one_cut(between="F-91")]), "'between' must be a list"),
    ],
    ids=[
        "severities-not-a-list",
        "unplaced-not-a-list",
        "calibration-not-a-mapping",
        "row-not-a-mapping",
        "row-missing-theta",
        "row-missing-severity",
        "row-missing-id",
        "theta-not-a-number",
        "cuts-not-a-list",
        "cut-not-a-mapping",
        "cut-missing-between",
        "gap-not-a-number",
        "between-not-a-list",
    ],
)
def test_a_malformed_severity_file_refuses_by_name(
    mutate: Callable[[dict[str, Any]], object], expected: str
) -> None:
    """Every malformation raises `SeverityError` and says which one.

    The last case is the reason this exists. `theta=float(row["theta"])` let a
    `ValueError` escape the contract every other branch honors, so a caller
    catching `SeverityError` caught everything *except* a non-numeric theta --
    the one field whose type actually matters, since it is the ordering the
    whole tool produces.
    """
    document = _severity_document()
    mutate(document)
    with pytest.raises(SeverityError, match=expected):
        parse_severity(json.dumps(document))


def test_a_severity_file_scoring_one_finding_twice_refuses() -> None:
    """The `"scores N id(s) more than once"` branch had no case.

    A duplicate is not cosmetic: the join builds `{record.id: record}`, so one
    of the two rows wins and which one is an implementation detail nobody chose.
    The refusal lives in the **join** rather than in `parse_severity`, which is
    why parsing a duplicated file succeeds -- worth knowing, because a caller
    that parses without joining gets no warning at all.
    """
    document = _severity_document()
    document["severities"].append(dict(document["severities"][0]))
    parsed = parse_severity(json.dumps(document))
    assert len(parsed.severities) == len(document["severities"])

    findings = load_findings(SMALL)
    with pytest.raises(SeverityError, match="more than once"):
        join(findings, parsed)


# --------------------------------------------------------------------------
# A cut, re-derived from the rows it was drawn over (OB-19)
# --------------------------------------------------------------------------


def _scored(identifier: str, band: str, theta: float) -> dict[str, object]:
    return {
        "id": identifier,
        "severity": band,
        "theta": theta,
        "content_hash": "c" * 64,
        "appearances": 10,
        "informative": 8,
    }


def _cut_document(**cut: object) -> dict[str, Any]:
    """The fixture with two more findings inside its `high_medium` cut, stated there.

    The fixture's three cuts agree with its rows. This adds F-96 at 0.8 and F-97
    at 0.2 strictly between `high_medium`'s anchors, F-93 at 1.0 above and F-94
    at 0.0 below, one on each side of that cut's midpoint, and lists them there
    most severe first. Keyword arguments replace `high_medium`'s own fields, so
    each test states the one thing it makes the file claim. Parsed and never
    joined: the two ids are not in the small findings document, and whether a
    file agrees with itself is a property of the file.
    """
    document = _severity_document()
    document["severities"].extend([_scored("F-96", "high", 0.8), _scored("F-97", "medium", 0.2)])
    (stated,) = [entry for entry in document["cuts"] if entry["name"] == "high_medium"]
    stated["between"] = ["F-96", "F-97"]
    stated.update(cut)
    return document


def test_a_cut_its_rows_agree_with_parses_into_what_lies_between_its_anchors() -> None:
    parsed = parse_severity(json.dumps(_cut_document()))
    assert parsed.cuts == (
        SeverityCut(name="critical_high", above_id="F-90", below_id="F-93", gap=1.5, between=()),
        SeverityCut(
            name="high_medium",
            above_id="F-93",
            below_id="F-94",
            gap=1.0,
            between=("F-96", "F-97"),
        ),
        SeverityCut(name="medium_low", above_id="F-94", below_id="F-95", gap=1.0, between=()),
    )


def test_the_schema_pin_would_notice_a_file_declaring_the_schema_before_cuts() -> None:
    """A file declaring schema 2 is refused by its version, whatever it carries.

    No test had driven this refusal: every malformed file in this module was
    refused by a missing field first, so the version comparison could have gone
    and the suite would have stayed green. A file declaring the old schema while
    carrying the new field is the case only the version decides.
    """
    document = _cut_document()
    document["schema_version"] = "2"
    with pytest.raises(SeverityError, match="declares schema_version '2'"):
        parse_severity(json.dumps(document))


def test_the_cut_cross_check_would_notice_an_anchor_the_file_does_not_score() -> None:
    """Nothing can say where a cut lies when the file carries no `theta` for its
    anchor. Refused as a `SeverityError`; without the refusal the lookup would
    raise `KeyError` through the contract, the shape a non-numeric theta once
    had."""
    with pytest.raises(SeverityError, match="F-999"):
        parse_severity(json.dumps(_cut_document(above_id="F-999")))


def test_the_cut_cross_check_would_notice_a_gap_its_anchors_contradict() -> None:
    """The between-set is right and the gap is not, so only the gap's own
    comparison can refuse the file."""
    with pytest.raises(SeverityError, match=r"states a gap of 2\.0"):
        parse_severity(json.dumps(_cut_document(gap=2.0)))


def test_the_cut_cross_check_would_notice_a_finding_left_out_of_between() -> None:
    """The rows put F-96 and F-97 between the anchors and the cut names F-96
    alone. That is OB-19's defect at its smallest: a finding inside a cut that
    the file does not mention, with the evidence for it in the same file."""
    with pytest.raises(SeverityError, match="lists F-96 strictly between"):
        parse_severity(json.dumps(_cut_document(between=["F-96"])))


def test_the_cut_cross_check_would_notice_an_anchor_counted_between_its_own_cut() -> None:
    """Strictly between. A cut listing its own anchors among the findings inside
    it is refused, so a derivation that counted them would agree with this file
    and fail here."""
    with pytest.raises(SeverityError, match="lists F-93, F-96, F-97, F-94 strictly between"):
        parse_severity(json.dumps(_cut_document(between=["F-93", "F-96", "F-97", "F-94"])))


def test_the_cut_cross_check_would_notice_between_listed_least_severe_first() -> None:
    """The right findings in the wrong order. Most severe first is the order the
    tool writes, so a derivation ranking the other way would agree with this
    file and fail here."""
    with pytest.raises(SeverityError, match="lists F-97, F-96 strictly between"):
        parse_severity(json.dumps(_cut_document(between=["F-97", "F-96"])))


def test_the_cut_check_would_notice_a_cut_named_outside_the_three() -> None:
    """P4-5. A cut is one of the three boundaries between the four bands (OB-25, D171).

    `nonsense` was accepted, since nothing read a cut's name. The tool's names are
    a closed set in severity order, and a band cannot be placed by a cut it does
    not have.
    """
    with pytest.raises(SeverityError, match="is named 'nonsense'"):
        parse_severity(json.dumps(_cut_document(name="nonsense")))


def test_the_cut_check_would_notice_a_cut_named_twice() -> None:
    """The tool refuses a cut defined more than once, and so does the loader (D171)."""
    document = _severity_document()
    document["cuts"].append(dict(document["cuts"][0]))
    with pytest.raises(SeverityError, match="'critical_high' is defined more than once"):
        parse_severity(json.dumps(document))


def test_the_cut_check_would_notice_an_inverted_or_single_anchor_cut() -> None:
    """P4-5. Anchors the file's own `theta` inverts, or one finding at both ends.

    Each was accepted with a gap and a between-set consistent with its rows: a
    negative gap with nothing between, and a gap of zero. The tool refuses both
    as inverted, since a boundary between two findings means nothing once they
    have swapped or are one finding (OB-25, D171).
    """
    for above_id, below_id, gap in (("F-94", "F-93", -1.0), ("F-93", "F-93", 0.0)):
        document = _cut_document(above_id=above_id, below_id=below_id, gap=gap, between=[])
        with pytest.raises(SeverityError, match="'high_medium' has inverted"):
            parse_severity(json.dumps(document))


def test_the_cut_check_would_notice_a_missing_cut() -> None:
    """All three cuts or no band can be placed. An empty list was read as a file
    stating no cuts, which the tool never exports, and two cuts place no band
    (OB-25, D171)."""
    for kept in ((), ("critical_high", "medium_low")):
        document = _severity_document()
        document["cuts"] = [entry for entry in document["cuts"] if entry["name"] in kept]
        with pytest.raises(SeverityError, match="states no cut"):
            parse_severity(json.dumps(document))


def test_the_cut_check_would_notice_boundaries_that_have_crossed() -> None:
    """Three cuts each valid alone, drawn in reverse, so their midpoints ascend.

    Every cut names two scored findings in order with a consistent gap and
    nothing between, and no check of one cut can see that `critical_high` now
    lies below `medium_low`. The tool refuses that as two boundaries crossed
    (OB-25, D171).
    """
    document = _severity_document()
    redrawn = {
        "critical_high": ("F-94", "F-95", 1.0),
        "high_medium": ("F-93", "F-94", 1.0),
        "medium_low": ("F-90", "F-93", 1.5),
    }
    for entry in document["cuts"]:
        entry["above_id"], entry["below_id"], entry["gap"] = redrawn[entry["name"]]
    with pytest.raises(SeverityError, match="two boundaries have crossed"):
        parse_severity(json.dumps(document))


def test_the_band_check_would_notice_a_row_on_the_wrong_side_of_its_cuts_midpoint() -> None:
    """P4-5's case: a row crosses a midpoint while staying between that cut's anchors.

    F-96 moves from 0.8 to 0.3, still strictly between F-93 and F-94 and still
    listed first between them, and now below `high_medium`'s midpoint of 0.5 with
    its band left `high`. The between-set, the gap and both pins on the committed
    file pass that shape, which is how the audit moved F-29 across `medium_low`
    with nothing noticing (OB-25, D171).
    """
    document = _cut_document()
    (row,) = [entry for entry in document["severities"] if entry["id"] == "F-96"]
    row["theta"] = 0.3
    with pytest.raises(SeverityError, match=r"F-96 is banded 'high' .* falls in 'medium'"):
        parse_severity(json.dumps(document))


def test_the_band_check_would_notice_a_row_on_a_midpoint_banded_up() -> None:
    """A theta exactly on a midpoint falls to the less severe side, as the tool bands it.

    F-97 moves onto `high_medium`'s midpoint of 0.5: banded `medium` the file is
    accepted, and banded `high` it is refused. A derivation counting the tie
    upward refuses the first file and accepts the second (D171).
    """
    document = _cut_document()
    (row,) = [entry for entry in document["severities"] if entry["id"] == "F-97"]
    row["theta"] = 0.5
    parse_severity(json.dumps(document))
    row["severity"] = "high"
    with pytest.raises(SeverityError, match="F-97 is banded 'high'"):
        parse_severity(json.dumps(document))


def test_the_gold_set_generator_preserves_a_multi_line_quote() -> None:
    """D22 chose YAML because evidence may carry verbatim multi-line quotes that
    a Markdown table cell cannot hold. Zero of the 86 rows use one, so the
    justification was carried entirely by a fixture -- and the generator would
    have flattened one silently, because folding joins on whitespace.

    Found by an independent sweep. The fix is not to force a multi-line quote
    into a row that does not need one; it is to make the affordance real, so
    that a row needing one gets it.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "make_gold_set", REPO_ROOT / "tools" / "make_gold_set.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _block, _fold = module._block, module._fold

    quote = 'event 4 — "Hi, I need my — sorry, one second —\nI need the confirmation resending"'
    rendered = _block(quote, "        ")
    assert rendered.count("\n") == 1, "the line break did not survive the literal scalar"
    assert yaml.safe_load(f"evidence:\n      - |-\n{rendered}\n")["evidence"] == [quote]

    flattened = _fold(quote, "        ")
    assert "\n" in flattened and quote not in flattened.replace("\n", ""), (
        "this is what folding would have done to it, and why the branch exists"
    )


def test_the_findings_format_uses_the_block_scalar_it_was_chosen_for() -> None:
    """D22 chose YAML partly for text whose line breaks are content. Something
    has to use it, or the justification is decorative.

    An independent sweep looked for this in `evidence` and found none, which is
    true and was the wrong field: **dozens of `consequence` values carry paragraph
    breaks**, and `make_gold_set._fold()` was flattening every one of them on
    every generation since the first. The bug is fixed; this asserts the format
    is still earning its place, so a future edit that collapses the last
    multi-paragraph consequence has to do it deliberately.
    """
    text = (REPO_ROOT / "corpus" / "findings.yaml").read_text(encoding="utf-8")
    blocks = text.count("consequence: |-")
    assert blocks >= 10, (
        f"only {blocks} findings use the literal block scalar; D22's justification for YAML "
        "rests on text whose line breaks are content, and nothing would be carrying it"
    )

    rows = yaml.safe_load(text)
    rows = rows["findings"] if isinstance(rows, dict) else rows
    multiline = [r["id"] for r in rows if "\n" in str(r["consequence"])]
    assert len(multiline) == blocks, (
        f"{blocks} rows are written as block scalars but {len(multiline)} parse with a newline; "
        "the emitter and the parser disagree about which text is multi-line"
    )


# --------------------------------------------------------------------------
# The real severity file, which nothing in this suite read
# --------------------------------------------------------------------------


def test_the_real_severity_file_joins_totally_onto_the_gold_set() -> None:
    """Every severity assertion in this file ran against `severity_small.json`,
    a fixture. The scoring run happened on 2026-09-05 and produced
    `corpus/findings.severity.json`; `grep findings.severity tests/` found
    nothing, so the artifact the project's headline claim rests on was checked
    by no test at all.

    A fixture proves the loader parses a shape. It cannot notice that the real
    file describes a different set of findings than the gold set does, which is
    the failure that would silently make coverage arithmetic wrong.
    """
    findings = load_findings(REPO_ROOT / "corpus" / "findings.yaml")
    severity = load_severity(REPO_ROOT / "corpus" / "findings.severity.json")
    joined = join(findings, severity)

    assert len(joined) == len(findings)
    defects = {f.id for f in findings if f.tier is Tier.DEFECT}
    questions = {f.id for f in findings if f.tier is not Tier.DEFECT}
    scored = {row.id for row in severity.severities}

    assert scored == defects, (
        f"scored ids and defect ids differ: only-scored={sorted(scored - defects)}, "
        f"only-defect={sorted(defects - scored)}"
    )
    assert not (scored & questions), "a question-tier finding carries a severity"
    assert not severity.unplaced, f"unplaced is not empty: {severity.unplaced}"

    banded = [row for row in joined if row.severity is not None]
    assert {row.finding.id for row in banded} == defects
    for row in joined:
        if row.finding.tier is not Tier.DEFECT:
            assert row.severity is None, f"{row.finding.id} is a question and carries a band"


def test_every_band_in_the_real_severity_file_is_in_the_vocabulary() -> None:
    """`severity` was any string the producer wrote. The harness bands findings
    in a report from it, so an unrecognized label does not fail — it renders,
    as a band nobody defined, in the artifact whose purpose is to be read."""
    severity = load_severity(REPO_ROOT / "corpus" / "findings.severity.json")
    used = {row.severity for row in severity.severities}
    assert used <= SEVERITY_BANDS, f"bands outside the vocabulary: {sorted(used - SEVERITY_BANDS)}"
    assert len(used) >= 2, f"only {sorted(used)} in use; the ordering is not discriminating"


def test_the_real_severity_file_pins_what_lies_between_each_cuts_anchors() -> None:
    """OB-19. The loader refuses a file whose stated separation its own `theta`
    contradicts, and it cannot notice a separation that *changes* while staying
    consistent -- which is what D144 was: one placement took `high_medium` from
    adjacent anchors to a span with seventeen findings inside it, and three of
    them changed band. The tool reports how far apart a cut's anchors are and
    refuses nothing for it (D34 there).

    So today's separation is pinned here. A re-export that moves a finding
    between a cut's anchors, or moves an anchor, fails by name, and whoever
    re-exported reads that cut before editing this list (D156).
    """
    severity = load_severity(REPO_ROOT / "corpus" / "findings.severity.json")
    assert [(cut.name, cut.above_id, cut.below_id, cut.between) for cut in severity.cuts] == [
        ("critical_high", "F-78", "F-83", ("F-82",)),
        ("high_medium", "F-41", "F-46", ()),
        ("medium_low", "F-61", "F-64", ("F-29",)),
    ]


def test_the_real_severity_file_pins_every_scored_findings_band() -> None:
    """P4-5. The cut pin above sees a finding enter or leave a cut's anchors, and not
    one that stays between them while the midpoint moves past it. Nothing here pinned
    a band, so the silent re-banding OB-23 is registered for would have passed every
    test in this repository.

    So every scored finding's band is pinned, grouped by band. A re-export that
    re-bands anything fails here by name, and updating this is a reading of what
    moved -- which is the mechanism OB-23's trigger could not supply from a
    gitignored store.
    """
    severity = load_severity(REPO_ROOT / "corpus" / "findings.severity.json")
    by_band: dict[str, list[str]] = {}
    for record in severity.severities:
        by_band.setdefault(record.severity, []).append(record.id)
    measured = {
        band: tuple(sorted(ids, key=lambda identifier: int(identifier.split("-", 1)[1])))
        for band, ids in by_band.items()
    }
    assert measured == {
        "critical": ("F-04", "F-45", "F-76", "F-78"),
        "high": (
            "F-01",
            "F-02",
            "F-03",
            "F-12",
            "F-14",
            "F-22",
            "F-25",
            "F-41",
            "F-65",
            "F-74",
            "F-75",
            "F-79",
            "F-82",
            "F-83",
        ),
        "medium": (
            "F-05",
            "F-06",
            "F-07",
            "F-08",
            "F-09",
            "F-10",
            "F-17",
            "F-18",
            "F-21",
            "F-26",
            "F-28",
            "F-29",
            "F-30",
            "F-40",
            "F-46",
            "F-50",
            "F-51",
            "F-53",
            "F-61",
            "F-62",
            "F-63",
            "F-67",
            "F-73",
            "F-77",
            "F-80",
            "F-81",
            "F-86",
            "F-90",
        ),
        "low": (
            "F-11",
            "F-13",
            "F-15",
            "F-16",
            "F-19",
            "F-20",
            "F-23",
            "F-24",
            "F-32",
            "F-33",
            "F-34",
            "F-35",
            "F-36",
            "F-37",
            "F-38",
            "F-39",
            "F-42",
            "F-43",
            "F-44",
            "F-47",
            "F-48",
            "F-52",
            "F-55",
            "F-57",
            "F-58",
            "F-60",
            "F-64",
            "F-66",
            "F-68",
            "F-69",
            "F-70",
            "F-71",
            "F-72",
            "F-85",
            "F-87",
            "F-88",
            "F-89",
        ),
    }


def test_a_scored_question_is_refused() -> None:
    """The docstring said a question is *expected* to be absent, and the join
    checked only that its absence was tolerated — never that its presence was
    refused. Two different claims; one of them was unenforced.

    It matters because of why questions are excluded: a non-defect in the anchor
    set distorts every later placement.
    """
    findings = load_findings(SMALL)
    question = next(f for f in findings if f.tier is not Tier.DEFECT)
    document = json.loads(SMALL_SEVERITY.read_text(encoding="utf-8"))
    document["severities"].append(
        {
            "id": question.id,
            "severity": "high",
            "theta": 1.0,
            "content_hash": "b" * 64,
            "appearances": 10,
            "informative": 8,
        }
    )

    with pytest.raises(SeverityError) as caught:
        join(findings, parse_severity(json.dumps(document)))
    assert question.id in str(caught.value)
    assert "question" in str(caught.value)


def test_a_band_outside_the_vocabulary_is_refused() -> None:
    """Refused by the join's vocabulary check, and by name, rather than by the band check.

    Since D171 the loader compares each row's band with the one its `theta` falls
    in, and a band nobody defined disagrees with every one of them. It is left to
    the join, which says what is wrong with it: not a misplaced band, a band
    outside the vocabulary.
    """
    findings = load_findings(SMALL)
    document = json.loads(SMALL_SEVERITY.read_text(encoding="utf-8"))
    document["severities"][0]["severity"] = "catastrophic"

    with pytest.raises(SeverityError) as caught:
        join(findings, parse_severity(json.dumps(document)))
    assert "catastrophic" in str(caught.value)
    assert "outside the vocabulary" in str(caught.value), str(caught.value)
