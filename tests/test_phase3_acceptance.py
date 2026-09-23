"""Every phase verifier's list, bound to the document it claims to verify.

`tools/verify_phase1.py` once printed "All 21 phase-1 acceptance criteria pass"
while counting its own list, so a criterion added to the specification and never
added to the tool was invisible. `tests/test_phase2_acceptance.py` closed that
for phase 2. **Phase 3 shipped with no counterpart**, and its verifier's closing
line was wrong the day it was written: it reported "21 of them the
specification's own [P3] acceptance criteria" over a document carrying 18,
because three of its anchors point into *requirement* prose rather than into the
criteria section. Each of those three is worth running and none is an acceptance
criterion.

**Parameterized over all three verifiers rather than written as a third copy.**
The rule does not vary by phase, and the phase-1 and phase-2 modules each hold
their own version of it only because there was nowhere else to put it. A fourth
phase adds a row to `VERIFIERS`. The two older copies stay where they are:
`tools/verify_phase2.py` names two of their tests as its own evidence, so
deleting them to remove a duplicate would delete a criterion's evidence.
"""

from __future__ import annotations

import importlib
import re
from pathlib import Path
from typing import Final, NamedTuple

import pytest
import yaml
from tools.verify_phase1 import (
    ASSERTED_ELSEWHERE,
    NOT_YET_BUILT,
    Criterion,
    Declared,
    criteria_in_document,
    declaration_problems,
    doubly_claimed_criteria,
    history_in_caveats,
    unclaimed_criteria,
)

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
SPEC: Final[str] = (REPO_ROOT / "specs" / "voice-agent-eval-harness.md").read_text(encoding="utf-8")
WORKFLOW: Final[Path] = REPO_ROOT / ".github" / "workflows" / "checks.yml"


class Verifier(NamedTuple):
    """Declared shape of one verifier's list.

    The two counts are decisions rather than measurements: how many entries
    verify something the specification does not carry as a criterion at all,
    and how many anchor into requirement prose instead. Deriving either from
    the tool would make this test agree with whatever the tool does, which is
    the failure it exists to prevent.
    """

    phase: int
    module: str
    extras: int
    requirement_anchors: int

    def __repr__(self) -> str:  # pragma: no cover - pytest ids only
        return f"P{self.phase}"

    @property
    def criteria(self) -> tuple[Criterion, ...]:
        loaded: tuple[Criterion, ...] = importlib.import_module(self.module).CRITERIA
        return loaded

    @property
    def declared(self) -> tuple[Declared, ...]:
        """The criteria this verifier claims without ticking (D176); none before phase 5."""
        loaded: tuple[Declared, ...] = getattr(importlib.import_module(self.module), "DECLARED", ())
        return loaded


#: Phase 1 splits one specification criterion across two entries, which is why
#: its in-criteria count (20) exceeds the document's `[P1]` bullet count (19).
#: Recorded at 0.15.0 and deliberate; the alternative is an entry that verifies
#: two things and reports one verdict.
VERIFIERS: Final[tuple[Verifier, ...]] = (
    Verifier(1, "tools.verify_phase1", extras=1, requirement_anchors=0),
    Verifier(2, "tools.verify_phase2", extras=2, requirement_anchors=0),
    Verifier(3, "tools.verify_phase3", extras=2, requirement_anchors=3),
    #: Phase 4 adds a row rather than a fourth copy, which is what this table
    #: was parameterized for. **Zero extras and zero requirement anchors**: its
    #: contract was amended before the build started (D130) rather than after
    #: it, so every entry verifies a criterion the document carries -- which is
    #: what phase 3's three requirement anchors were the absence of.
    Verifier(4, "tools.verify_phase4", extras=0, requirement_anchors=0),
    #: Phase 5 joins while its phase is open (D176): its entries tick what is
    #: built, and the three criteria the held-out repository's gate asserts are
    #: declared rather than ticked. The coverage report's two were declared not yet
    #: built until the report was (D188).
    Verifier(5, "tools.verify_phase5", extras=0, requirement_anchors=0),
    #: Phase 6 joins on the day its contract was read (D201), as phase 5 did
    #: while open: what spends nothing is ticked, and the criteria that need a
    #: live model call, with the design document's, are declared not yet built.
    Verifier(6, "tools.verify_phase6", extras=0, requirement_anchors=0),
)


def _tagged_criterion_lines(phase: int) -> list[str]:
    """The specification's own `[Pn]` acceptance-criterion bullets.

    Matched on the bullet shape rather than on a section heading, because a
    criterion moved between subsections is still a criterion and a scan keyed
    on headings would drop it silently.
    """
    lines = [
        line.strip()
        for line in SPEC.splitlines()
        if re.match(rf"^- \[[ x]\] \[P{phase}[,\]]", line.strip())
    ]
    assert lines, f"no [P{phase}] criteria parsed; the marker shape changed"
    return lines


@pytest.mark.parametrize("verifier", VERIFIERS, ids=repr)
def test_every_tagged_criterion_is_claimed_by_its_verifier(verifier: Verifier) -> None:
    """A criterion the document carries and no entry claims is a criterion
    nobody runs -- and the closing line would still say every check passed.

    A declaration claims one too (D176), and is printed as declared rather than
    ticked; `test_no_criterion_is_both_ticked_and_declared` keeps the two apart."""
    unclaimed = [
        line[:100]
        for line in unclaimed_criteria(
            _tagged_criterion_lines(verifier.phase), verifier.criteria, verifier.declared
        )
    ]
    assert not unclaimed, (
        f"[P{verifier.phase}] acceptance criteria that no entry in {verifier.module} claims:\n  "
        + "\n  ".join(unclaimed)
    )


@pytest.mark.parametrize("verifier", VERIFIERS, ids=repr)
def test_every_anchor_points_into_the_specification(verifier: Verifier) -> None:
    """An anchor that matches nothing claims a criterion that is not there."""
    for criterion in verifier.criteria:
        if not criterion.spec_anchor:
            continue
        assert criterion.spec_anchor in SPEC, (
            f"{verifier.module}: the anchor {criterion.spec_anchor!r} appears nowhere in the "
            "specification, so this entry claims a criterion the document does not carry"
        )


@pytest.mark.parametrize("verifier", VERIFIERS, ids=repr)
def test_the_unanchored_entries_are_the_declared_extras(verifier: Verifier) -> None:
    """Each verifier adds entries the specification does not carry as criteria.

    Declared as a number, so the difference between `len(CRITERIA)` and the
    document's count is accounted for rather than absorbed.
    """
    unanchored = [c.text[:60] for c in verifier.criteria if not c.spec_anchor]
    assert len(unanchored) == verifier.extras, (
        f"{verifier.module} has {len(unanchored)} unanchored entries, "
        f"{verifier.extras} declared: {unanchored}"
    )


@pytest.mark.parametrize("verifier", VERIFIERS, ids=repr)
def test_every_criterion_names_evidence_that_still_exists(verifier: Verifier) -> None:
    """A node id that has been renamed shows here rather than as MISSING later."""
    missing: list[str] = []
    for criterion in verifier.criteria:
        for node in criterion.tests:
            path, _, name = node.partition("::")
            source = REPO_ROOT / path
            if not source.is_file():
                missing.append(f"{node} (no such file)")
                continue
            if f"def {name}(" not in source.read_text(encoding="utf-8"):
                missing.append(node)
    assert not missing, f"{verifier.module} names evidence that does not exist:\n  " + "\n  ".join(
        missing
    )


@pytest.mark.parametrize("verifier", VERIFIERS, ids=repr)
def test_no_criterion_is_left_with_no_evidence_at_all(verifier: Verifier) -> None:
    empty = [c.text[:70] for c in verifier.criteria if not c.tests and not c.commands]
    assert not empty, f"{verifier.module} has criteria with neither a test nor a command: {empty}"


@pytest.mark.parametrize("verifier", VERIFIERS, ids=repr)
def test_no_criterion_is_both_ticked_and_declared(verifier: Verifier) -> None:
    """A declaration naming a criterion an entry now ticks has outlived its build (D176)."""
    both = doubly_claimed_criteria(
        _tagged_criterion_lines(verifier.phase), verifier.criteria, verifier.declared
    )
    assert not both, f"{verifier.module} ticks and declares: " + "; ".join(
        line[:80] for line in both
    )


@pytest.mark.parametrize("verifier", VERIFIERS, ids=repr)
def test_every_declaration_names_a_criterion_and_its_reason(verifier: Verifier) -> None:
    """Every declaration anchors into one of its phase's criteria, is of a known kind
    and gives its reason, an asserted-elsewhere one naming where (D176)."""
    problems = declaration_problems(_tagged_criterion_lines(verifier.phase), verifier.declared)
    assert not problems, f"{verifier.module}:\n  " + "\n  ".join(problems)


def test_phase_5_declares_the_gate_asserted_criteria_and_the_unbuilt_report() -> None:
    """Which three, and of which kind, so a fourth declaration is a decision rather
    than a drift (D176). The three asserted elsewhere name the held-out repository's
    gate. **The unbuilt report is declared no longer**: the coverage report by
    severity was built and its two criteria are ticked (D188), so a declaration
    returning for either is refused here as well as by the claim check."""
    from tools.verify_phase5 import DECLARED

    assert sorted((d.kind, d.spec_anchor) for d in DECLARED) == sorted(
        [
            (
                ASSERTED_ELSEWHERE,
                "first commit is later than the freeze commit the published",
            ),
            (ASSERTED_ELSEWHERE, "first commit message cites the freeze commit"),
            (ASSERTED_ELSEWHERE, "The hash manifest matches the published held-out labels"),
        ]
    )
    assert not any(d.kind == NOT_YET_BUILT for d in DECLARED)
    assert all(
        "the held-out repository's gate" in d.reason
        for d in DECLARED
        if d.kind == ASSERTED_ELSEWHERE
    )


def test_phase_6_declares_what_needs_a_model_call_and_the_design_document() -> None:
    """Which six, all of one kind, so a seventh declaration is a decision rather than
    a drift, and so one of these being built is noticed: the claim check refuses a
    criterion both ticked and declared, and this refuses a declaration that quietly
    left (D176, D201)."""
    from tools.verify_phase6 import DECLARED

    assert sorted(d.spec_anchor for d in DECLARED) == sorted(
        [
            "Judge-model comparison reports per-model agreement against the gold set",
            "Every candidate's run log names one rubric hash",
            "Judge-model comparison states beside every figure",
            "the second repetition of a dimension on a given call reports cache-read",
            "byte-identical through the last cache breakpoint",
            "The design document exists under `specs/`",
        ]
    )
    assert all(d.kind == NOT_YET_BUILT for d in DECLARED)


#: Two invented criterion lines, for the controls below: planted rather than read
#: from the specification, so each control drives one clause of one helper.
_TICKED_LINE: Final[str] = "- [ ] [P9] An invented criterion that an entry ticks."
_DECLARED_LINE: Final[str] = "- [ ] [P9] An invented criterion that is declared."


def test_the_claim_check_would_notice_a_declaration_ignored() -> None:
    """A criterion a declaration names is claimed, and one nothing names is not (D176)."""
    ticked = (Criterion("ticks one", tests=("planted.py::entry",), spec_anchor="an entry ticks"),)
    declared = (
        Declared("declares one", spec_anchor="is declared", kind=NOT_YET_BUILT, reason="Not yet."),
    )
    lines = [_TICKED_LINE, _DECLARED_LINE]
    assert unclaimed_criteria(lines, ticked, declared) == []
    assert unclaimed_criteria(lines, ticked, ()) == [_DECLARED_LINE]


def test_the_claim_check_would_notice_a_criterion_both_ticked_and_declared() -> None:
    """A criterion an entry ticks and a declaration also names is found, so a
    declaration cannot outlive the build that replaced it (D176)."""
    ticked = (Criterion("ticks it", tests=("planted.py::entry",), spec_anchor="is declared"),)
    declared = (
        Declared("declares it", spec_anchor="is declared", kind=NOT_YET_BUILT, reason="Not yet."),
    )
    lines = [_TICKED_LINE, _DECLARED_LINE]
    assert doubly_claimed_criteria(lines, ticked, declared) == [_DECLARED_LINE]
    assert doubly_claimed_criteria(lines, ticked, ()) == []


def test_a_declaration_would_notice_each_way_it_cannot_stand() -> None:
    """A declaration naming no criterion, of an unknown kind, giving no reason, or
    asserted elsewhere without naming where, is refused by name, and a sound one is
    not (D176)."""
    gate = "Asserted by the held-out repository's gate."
    sound = Declared("sound", spec_anchor="is declared", kind=ASSERTED_ELSEWHERE, reason=gate)
    assert declaration_problems([_DECLARED_LINE], (sound,)) == []
    for broken, fragment in (
        (
            Declared(
                "anchorless", spec_anchor="names nothing", kind=ASSERTED_ELSEWHERE, reason=gate
            ),
            "names no acceptance criterion",
        ),
        (
            Declared("unknown", spec_anchor="is declared", kind="decided later", reason=gate),
            "is not one of",
        ),
        (
            Declared("reasonless", spec_anchor="is declared", kind=NOT_YET_BUILT, reason=" "),
            "gives no reason",
        ),
        (
            Declared(
                "nowhere", spec_anchor="is declared", kind=ASSERTED_ELSEWHERE, reason="Somewhere."
            ),
            "names none of",
        ),
    ):
        problems = declaration_problems([_DECLARED_LINE], (broken,))
        assert any(fragment in problem for problem in problems), (broken.text, problems)


def test_the_loop_would_notice_its_declarations_left_unprinted(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The shared loop prints each declaration under its own heading, counts them
    by kind in its closing line, and exits 0 with them unticked (D176).

    Driven over an invented criterion and a planted JUnit report, so the loop reads
    the report rather than running the suite inside the suite: a report written now
    is newer than every source file, which is what lets the loop reuse it.
    """
    from tools.verify_phase2 import main as run_phase_loop

    report = tmp_path / "junit.xml"
    report.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<testsuites><testsuite name="pytest" errors="0" failures="0" skipped="0" tests="1">'
        '<testcase classname="planted.suite" name="planted_pass" time="0.001"/>'
        "</testsuite></testsuites>\n",
        encoding="utf-8",
    )
    criteria = (Criterion("An invented criterion.", tests=("planted/suite.py::planted_pass",)),)
    declared = (
        Declared(
            "An invented criterion checked elsewhere.",
            spec_anchor="invented elsewhere",
            kind=ASSERTED_ELSEWHERE,
            reason="Asserted by the held-out repository's gate, in this invented case.",
        ),
        Declared(
            "An invented criterion not built.",
            spec_anchor="invented pending",
            kind=NOT_YET_BUILT,
            reason="Nothing invented has been built.",
        ),
    )
    code = run_phase_loop(["--junit", str(report)], criteria=criteria, phase=9, declared=declared)
    out = capsys.readouterr().out
    assert code == 0, out
    assert "DECLARED, NOT TICKED" in out, out
    for declaration in declared:
        assert declaration.text in out, out
        assert declaration.reason in out, out
    closing = "2 more are declared and not ticked: 1 asserted elsewhere, 1 not yet built."
    assert closing in out, out


# --------------------------------------------------------------------------
# The closing line: what it is allowed to call an acceptance criterion
# --------------------------------------------------------------------------


@pytest.mark.parametrize("verifier", VERIFIERS, ids=repr)
def test_the_count_the_summary_prints_separates_criteria_from_requirement_prose(
    verifier: Verifier,
) -> None:
    """The defect this module exists for, generalized.

    `verify_phase3` counted every anchored entry and printed the total as
    acceptance criteria. Three of its anchors point into requirement prose --
    "SHALL complete without network access", the citable-identifier syntax, and
    whether the specified backoff replaces the SDK's -- so the sentence
    overstated the document by three.

    Read from `criteria_in_document`, which is the function the summary calls,
    rather than recomputed beside it. A control that re-implements the rule
    next to the check is the shape D121 found in six controls, every one of
    them measuring nothing.
    """
    criteria = verifier.criteria
    anchored = sum(1 for c in criteria if c.spec_anchor)
    in_criteria = criteria_in_document(criteria, verifier.phase)
    assert anchored - in_criteria == verifier.requirement_anchors, (
        f"{verifier.module} anchors {anchored - in_criteria} entries into requirement prose, "
        f"{verifier.requirement_anchors} declared -- the closing line's split moved"
    )
    assert len(criteria) == in_criteria + verifier.requirement_anchors + verifier.extras


def test_the_phase_3_requirement_anchors_are_the_three_non_functional_lines() -> None:
    """Which three, named, so a fourth is a decision rather than a drift.

    Phase 3 is the phase the distinction arrived with: the non-functional
    requirement lines are worth running and the document does not repeat them
    as criteria, so three entries verify a requirement directly.
    """
    from tools.verify_phase3 import CRITERIA

    lines = _tagged_criterion_lines(3)
    in_prose = sorted(
        c.spec_anchor
        for c in CRITERIA
        if c.spec_anchor and not any(c.spec_anchor in line for line in lines)
    )
    assert in_prose == [
        "SHALL complete without network access",
        "keep the citable-identifier syntax distinguishable",
        "whether the specified exponential backoff **replaces**",
    ], in_prose


# --------------------------------------------------------------------------
# CI
# --------------------------------------------------------------------------


def test_the_workflow_runs_every_phase_verifier_and_the_inventory() -> None:
    """A gate that runs only when somebody remembers has quietly stopped
    verifying. Both of phase 3's ran in that state at some point: `verify_phase3`
    was written and initially not wired in, and `statement_inventory` never had
    been.

    **The verifiers are read from `VERIFIERS`, not listed here** (OB-27). This
    named three of them, so the phase-4 step could be deleted from the workflow
    and nothing failed (P4-10): the fourth phase added its row to the table and
    never to this list. A step runs a verifier as a module or as a path, and the
    workflow uses both spellings, so either one counts.
    """
    document = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    commands = "\n".join(str(step.get("run", "")) for step in document["jobs"]["checks"]["steps"])
    for verifier in VERIFIERS:
        spellings = (verifier.module, verifier.module.replace(".", "/") + ".py")
        assert any(spelling in commands for spelling in spellings), (
            f"CI does not run {verifier.module}"
        )
    assert "statement_inventory.py" in commands, (
        "CI does not resolve the identifiers named in prose"
    )
    assert "verify_controls.py" in commands, "CI does not re-derive the control verdicts"


def test_no_caveat_carries_the_history_its_decision_records() -> None:
    """A caveat prints under "read these rather than the ticks", so it states what its tick
    does not buy. When a criterion was added, and when a sentence stopped being true, are the
    decisions' to record (P4-18, D180). The markers are the two shapes found, not a definition
    of history."""
    found = [
        f"phase {verifier.phase}: {item}"
        for verifier in VERIFIERS
        for item in history_in_caveats(verifier.criteria)
    ]
    assert not found, "caveats carrying history their decisions record:\n  " + "\n  ".join(found)


def test_the_history_check_would_notice_each_marker() -> None:
    """Each marker is found in a planted caveat, and a limit carrying neither is not (D180)."""
    planted = (
        Criterion("added", tests=("planted.py::entry",), caveat="Added at D130. Offsets compared."),
        Criterion("dated", tests=("planted.py::entry",), caveat="It read so until 2026-09-07."),
        Criterion("limit", tests=("planted.py::entry",), caveat="A suite issues no live run."),
    )
    found = history_in_caveats(planted)
    assert len(found) == 2, found
    assert any("Added at D130" in item for item in found), found
    assert any("until 2026-09-07" in item for item in found), found
