"""Whether a phase's acceptance criteria cover that phase's requirements.

**Two phases have now opened by asking this by hand.** D104 asked it of phase 2
and found five of twelve requirements covered in half; D130 asked it of phase 4
and found four of five, plus a whole deliverable carrying no criterion at all.
Between them nothing was built, because the question looked unmechanizable -- and
half of it is.

**The adequacy half is a reading and stays one.** Whether a criterion covers
*both* halves of its requirement, and whether it can be told from the design's
inversion, is judgment. D104's grounding criterion and D130's synthesis criterion
were each green against a fixture that resolved either way, and no scan sees
that: both were syntactically present, both named the right subject, and both
were satisfied by the opposite of what the requirement asked for.

**The completeness half is not a reading.** *Every requirement is named by at
least one criterion* is a comparison, given a way to address a bullet -- and the
phase verifiers already address a criterion by distinctive substring, so the
machinery existed one field over. This is that comparison.

**What it cannot do, said here rather than discovered.** A mapping row is typed
by somebody, so this removes the failure where a requirement has no criterion at
all and not the one where it has a criterion that buys half of it. That is the
same limit `OBLIGATIONS.md` states about itself, and for the same reason: what
is mechanized is that nobody can *fail to notice*, never that somebody looked and
was right.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Final

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
SPEC: Final[str] = (REPO_ROOT / "specs" / "voice-agent-eval-harness.md").read_text(encoding="utf-8")

#: Phases whose requirements are not yet mapped, and why.
#:
#: **Declared rather than exempted**, which is `JUDGED_AGREEMENT_PENDING`'s idiom
#: one register over: the guard below stays total across every phase, and a phase
#: is either mapped or named here. There is no third option and no silence.
#:
#: Phase 4 is mapped because phase 4 is the phase that ran the reading. Phase 5
#: is mapped because its reading ran before the phase opened, and found two
#: criteria missing that the phase would otherwise have built without (D157).
#: Phase 6 is mapped because its reading opened the phase (D201), and found one
#: requirement with no criterion, one no criterion could satisfy under the frozen
#: prompt, and two covered in half.
#: Mapping the others means making a coverage claim about criteria nobody has
#: read that way, and a table asserting what somebody guessed is worse than a
#: table that says which phases nobody has been through -- it would report green
#: over exactly the state this exists to find.
#:
#: **What would close it**: one reading pass per phase, of the kind D104, D130
#: and D157 each did. `OB-16` is the row.
UNMAPPED_PHASES: Final[frozenset[str]] = frozenset({"1", "2", "3", "7"})

#: Requirement anchor to the criteria anchors that cover it, per phase. Both
#: sides are distinctive substrings, matched against the document, so a bullet
#: reworded on either side breaks the row rather than silently covering nothing
#: -- the same idiom the phase verifiers use to bind an entry to a criterion, and
#: for the reason `OBLIGATIONS.md` gives about its own anchor column: a position
#: is not an identity.
COVERAGE: Final[dict[str, dict[str, tuple[str, ...]]]] = {
    "4": {
        "the synthesis dimension cites a rubric identifier that did not produce a result": (
            "citing a rubric id that produced no result",
            "citing only ids that **did** produce a result",
        ),
        "computing a pass rate for a rate-gated dimension": (
            "together with its `not_applicable`, `unevaluable` and `errored` counts",
            "asserted for a **judged** rate-gated dimension",
            "reports `refused` counts alongside",
            "excluded from the rate denominator, asserted per status",
        ),
        "reporting a judged dimension evaluated at N>1": (
            "reported as a verdict distribution, not a single verdict",
            "whose N repetitions **disagree**",
        ),
        "model-authored text contains a table delimiter": (
            "pipe character and a newline renders without corrupting",
            "still **carries** what it escaped",
        ),
        "a judged entry declares a fact category as a precondition": (
            "whose declared precondition is not met",
        ),
        "the Tier A section of the report SHALL be byte-identical": (
            "Tier A report section is byte-identical",
            "NOT applied to live runs",
            "compares against a **committed** artifact",
            "golden-report regression runs in CI",
        ),
        "`--resume <log>` is supplied with `--mode live`": ("resumed from a log cut in half",),
        "a judged entry declares `violating` verdicts": ("declares its middle value `violating`",),
        "the system SHALL print an expected cost beside the estimated cost": (
            "prints an expected cost beside its estimated ceiling",
        ),
    },
    # Four requirements. The first is agreement, and D175's `harness agreement` is its
    # second criterion. The second is D173's: a held-out run's labels manifest is
    # behavior of this harness, so it carries a requirement of its own, and D174's
    # refusal of a held-out run's paths inside the checkout is its second criterion,
    # with D184's name for its log the third. The third requirement is D185's, and it
    # is the report's rather than a run's: where a report over held-out calls may be
    # written is behavior of this harness too. The fourth is D188's coverage report,
    # which D157 left without a requirement until it was built: what it counts and
    # where its held-out section may go are behavior once it exists, and the command
    # has a criterion beside the two the report already had.
    # Phase 5's other criteria -- the label ordering, the freeze-SHA citation, and the
    # manifest's recomputation and resolution in the companion repository -- back no
    # requirement statement, so this table cannot see them; D157 records that rather
    # than writing requirements to suit the table.
    "5": {
        "agreement against human labels separately for the design set and the held-out set": (
            "reported for design and held-out sets separately, each with its denominator",
            "prints, for every rubric entry over each set's calls",
        ),
        "a judged run has read its corpus, the system SHALL treat the run as held out": (
            "is refused without `--labels-manifest`",
            "resolving inside the repository, each refusal naming its flag",
            "written under the `heldout-` prefix",
        ),
        "a report is rendered over any call `HELDOUT_SET` declares": (
            "is refused an `--out` path inside the repository",
        ),
        "an extraction artifact or a findings view is written over held-out content": (
            "are each refused an `--out` path inside the repository",
        ),
        "the coverage report runs, the system SHALL count a finding as retired": (
            "lists findings retired by severity and names the uncovered set explicitly",
            "states, for each severity band, how many findings are retired",
            "`harness coverage` prints, for each severity band of each set",
        ),
    },
    # Five requirements, read at D201 before anything was built. The adapter's had no
    # criterion at all and gained two: the stream, and the inversion the stream's
    # criterion cannot see, an adapter that reads the transcript beside its source
    # (D203). Caching's was reworded to what the frozen prompt template can share and
    # gained the half that needs no model call (D204). Comparison's criterion bought
    # the report and not the identical rubric, and gained that and the tracing
    # convention every figure inherits (D202). The inspector's bought *runs and emits*
    # and not *metrics rather than scores* (D205); its first half, a log sufficient to
    # reproduce a judged result, rests on phase 3's replay criteria and is not split
    # out, as D130 declined to move a requirement to suit a criteria gap. Per-instance
    # severity had neither a requirement nor a criterion and gained both (D206).
    # Phase 6's other criteria -- the README's license table and the design document --
    # back no requirement statement, so this table cannot see them; D201 records that
    # rather than writing requirements to suit the table, as D157 did for phase 5.
    "6": {
        "the second adapter is selected": (
            "the second adapter's event stream equals the text adapter's",
            "outside the second adapter's declared mapping aborts naming the value",
        ),
        "prompt caching is enabled": (
            "the second repetition of a dimension on a given call reports cache-read",
            "byte-identical through the last cache breakpoint",
        ),
        "judge-model comparison is requested": (
            "Judge-model comparison reports per-model agreement against the gold set",
            "Every candidate's run log names one rubric hash",
            "Judge-model comparison states beside every figure",
        ),
        "the log inspector SHALL assert invariants over it": (
            "The log inspector runs over a completed run log",
            "Every value the log inspector emits is a count",
        ),
        "a rubric entry counts against its gate on a call": (
            "`harness severity` prints a band for every instance in the design set",
        ),
    },
}

_PHASE_TAG: Final[re.Pattern[str]] = re.compile(r"\[P(\d)(?:,[^\]]*)?\]")


def _section(heading: str, next_heading: str) -> str:
    start = SPEC.index(heading)
    return SPEC[start : SPEC.index(next_heading, start)]


def _bullets(section: str, criterion: bool) -> list[str]:
    pattern = r"^- \[[ x]\] " if criterion else r"^- "
    return [line for line in section.splitlines() if re.match(pattern, line)]


def _for_phase(phase: str, *, criterion: bool) -> list[str]:
    section = (
        _section("## acceptance criteria", "## implementation phases")
        if criterion
        else _section("## requirements", "## failure & escalation")
    )
    return [
        line
        for line in _bullets(section, criterion)
        if (match := _PHASE_TAG.search(line)) and match.group(1) == phase
    ]


def _matches(anchor: str, bullets: list[str]) -> list[str]:
    return [line for line in bullets if anchor in line]


def test_every_phase_is_either_mapped_or_declared_unmapped() -> None:
    """Total across the document, so a phase cannot go missing quietly.

    Both directions. A phase in neither set is one nobody decided about; a
    phase in both is a table claiming to cover what it also says it does not.
    """
    tagged = {
        match.group(1)
        for line in _bullets(_section("## requirements", "## failure & escalation"), False)
        if (match := _PHASE_TAG.search(line))
    }
    assert tagged, "no requirement bullet carries a phase tag; the scan reads nothing"
    accounted = set(COVERAGE) | UNMAPPED_PHASES
    assert tagged <= accounted, (
        f"phases with requirements and no coverage decision: {sorted(tagged - accounted)}"
    )
    overlap = set(COVERAGE) & UNMAPPED_PHASES
    assert not overlap, f"phases both mapped and declared unmapped: {sorted(overlap)}"
    assert set(COVERAGE), "no phase is mapped, so this file asserts nothing about coverage at all"


def test_every_mapped_requirement_is_named_by_at_least_one_criterion() -> None:
    """`OB-16`'s mechanizable half.

    Each requirement anchor must match exactly one requirement bullet of its
    phase, and each criterion anchor exactly one criterion bullet -- so a
    reworded bullet breaks the row loudly rather than covering nothing quietly.
    """
    for phase, rows in sorted(COVERAGE.items()):
        requirements = _for_phase(phase, criterion=False)
        criteria = _for_phase(phase, criterion=True)
        assert requirements and criteria, f"phase {phase} has no bullets to compare"

        for requirement_anchor, criterion_anchors in sorted(rows.items()):
            found = _matches(requirement_anchor, requirements)
            assert len(found) == 1, (
                f"P{phase}: the requirement anchor {requirement_anchor!r} matches "
                f"{len(found)} requirement bullets; it has to name exactly one"
            )
            assert criterion_anchors, (
                f"P{phase}: {requirement_anchor!r} is mapped to no criterion, which is the "
                "state this file exists to make impossible to write by accident"
            )
            for criterion_anchor in criterion_anchors:
                hits = _matches(criterion_anchor, criteria)
                assert len(hits) == 1, (
                    f"P{phase}: the criterion anchor {criterion_anchor!r} matches {len(hits)} "
                    f"[P{phase}] criterion bullets; it has to name exactly one"
                )


def test_every_requirement_of_a_mapped_phase_appears_in_the_table() -> None:
    """The direction that catches a requirement added and never covered.

    The other direction -- a table row naming a requirement that no longer
    exists -- is caught above by the exactly-one match. Both are needed: a
    mapping is a claim in two directions, and the register that taught this
    project the lesson found a stale row before it found a missing one.
    """
    for phase, rows in sorted(COVERAGE.items()):
        requirements = _for_phase(phase, criterion=False)
        uncovered = [line for line in requirements if not any(anchor in line for anchor in rows)]
        assert not uncovered, (
            f"P{phase} requirements named by no criterion in the table:\n  "
            + "\n  ".join(line[:150] for line in uncovered)
        )


def test_no_criterion_anchor_is_reused_across_two_requirements() -> None:
    """One criterion may cover two requirements; the same *anchor* may not.

    A reused anchor is a row that looks like coverage and is the same evidence
    counted twice -- which is how a coverage table drifts from being a list of
    what is checked into a list of what somebody wrote down.

    Deliberately narrower than "one criterion covers one requirement": a
    criterion legitimately serving two requirements should say so with two
    anchors into its own text, so the reading that put it there is recoverable.
    """
    for phase, rows in sorted(COVERAGE.items()):
        used = Counter(anchor for anchors in rows.values() for anchor in anchors)
        repeated = sorted(anchor for anchor, count in used.items() if count > 1)
        assert not repeated, f"P{phase}: criterion anchors used for two requirements: {repeated}"
