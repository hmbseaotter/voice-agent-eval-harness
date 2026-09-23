"""The judged family's firing table, over the committed reference log (D202).

Every deterministic family has an `EXPECTED_FIRING` table: where each entry
fires on the design set, asserted in both directions. The judged tier had none,
and its seven entries sat in `JUDGED_AGREEMENT_PENDING` from phase 3, waiting
on agreement against held-out labels. That agreement was measured on 2026-09-18
and, as D175 requires, never committed -- so the pending set could not close on
a committed figure, and OB-7 asked what closes it instead.

**This does.** A judged entry fires where its gate's reading of its repetitions
counts against the call (D158, D160), and over a committed log replay makes that
a fixed function of the repository. So the judged family gets the table every
other family has, and joins `FAMILY_TABLES`.

**What it is, and what it is not.** It is where each judged entry fires on the
design set *in the committed reference run*, pinned so that a re-recording which
moves one is seen. It is not blind agreement: the design findings were
adjudicated with judge output in view (D21), and the blind figure is the
held-out section of `harness agreement`, recomputable by anyone from the
held-out repository's published labels and committed run log, and never
committed here.

**The disagreements are recorded by name rather than absorbed.** Nineteen
firings land on calls carrying no finding their entry traces, and one traced
call is missed. Every one of the nineteen is on a call that carries findings --
every design call does -- so none can be called a true false alarm without a
human reading which finding the judge was answering. That reading is the
version-2 cycle's (D202): each becomes a trace, a judge-type finding the gold set
lacks, or a false alarm. Until then a twentieth, or one of these going quiet,
fails here rather than arriving as a changed count nobody re-derives.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest

from harness import cli
from harness.agreement import design_expected, readings_for
from harness.checks import build_registry
from harness.core.findings import load_findings
from harness.core.result import Status
from harness.core.rubric import CheckTier, load_rubric
from harness.heldout import declared_held_out_calls
from harness.judge.prompt import load_template

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]

#: Where each judged entry's gate counts against a design call, in the committed
#: reference log. Calls only: which findings an entry traces is the rubric's to
#: say, and a second copy of `traces_to` here would be one more thing to drift.
EXPECTED_FIRING: Final[dict[str, frozenset[str]]] = {
    "J-policy-alignment": frozenset({"CALL-02", "CALL-04"}),
    "J-concerns-addressed": frozenset(
        {"CALL-04", "CALL-05", "CALL-09", "CALL-10", "CALL-12", "CALL-18", "CALL-19", "CALL-20"}
    ),
    "J-unnecessary-repetition": frozenset({"CALL-12"}),
    "J-caller-pushback-understood": frozenset(
        {"CALL-05", "CALL-08", "CALL-09", "CALL-10", "CALL-18", "CALL-19"}
    ),
    "J-claim-plausible-in-the-world": frozenset({"CALL-02", "CALL-05", "CALL-10"}),
    "J-confidence-exceeds-sources": frozenset(
        {"CALL-02", "CALL-05", "CALL-08", "CALL-10", "CALL-19"}
    ),
    "J-call-synthesis": frozenset(
        {
            "CALL-01",
            "CALL-02",
            "CALL-04",
            "CALL-05",
            "CALL-06",
            "CALL-08",
            "CALL-09",
            "CALL-10",
            "CALL-19",
        }
    ),
}

#: Fired on a call carrying no finding the entry traces (D202's nineteen).
RECORDED_FALSE_ALARMS: Final[frozenset[tuple[str, str]]] = frozenset(
    {
        ("J-concerns-addressed", "CALL-18"),
        ("J-concerns-addressed", "CALL-19"),
        ("J-concerns-addressed", "CALL-20"),
        ("J-caller-pushback-understood", "CALL-05"),
        ("J-caller-pushback-understood", "CALL-08"),
        ("J-caller-pushback-understood", "CALL-09"),
        ("J-caller-pushback-understood", "CALL-18"),
        ("J-claim-plausible-in-the-world", "CALL-02"),
        ("J-claim-plausible-in-the-world", "CALL-10"),
        ("J-confidence-exceeds-sources", "CALL-02"),
        ("J-confidence-exceeds-sources", "CALL-05"),
        ("J-confidence-exceeds-sources", "CALL-19"),
        ("J-call-synthesis", "CALL-01"),
        ("J-call-synthesis", "CALL-02"),
        ("J-call-synthesis", "CALL-04"),
        ("J-call-synthesis", "CALL-06"),
        ("J-call-synthesis", "CALL-08"),
        ("J-call-synthesis", "CALL-09"),
        ("J-call-synthesis", "CALL-19"),
    }
)

#: Silent on a call carrying a finding the entry traces: F-85 on CALL-19, the
#: recorded miss `tests/test_reference_run.py` has pinned since phase 3.
RECORDED_MISSES: Final[frozenset[tuple[str, str]]] = frozenset({("J-policy-alignment", "CALL-19")})


def _compare(
    fired: dict[str, frozenset[str]], traced: dict[str, frozenset[str]]
) -> tuple[list[str], set[tuple[str, str]], set[tuple[str, str]]]:
    """What differs from the table, and the false alarms and misses found.

    One function for the assertion and its control, so the control drives the
    comparison the assertion makes rather than a copy of it (D121).
    """
    problems = [
        f"{entry_id} fires on {sorted(calls)} and the table says "
        f"{sorted(EXPECTED_FIRING.get(entry_id, frozenset()))}"
        for entry_id, calls in sorted(fired.items())
        if calls != EXPECTED_FIRING.get(entry_id, frozenset())
    ]
    false_alarms = {
        (entry_id, call) for entry_id, calls in fired.items() for call in calls - traced[entry_id]
    }
    misses = {
        (entry_id, call) for entry_id, calls in fired.items() for call in traced[entry_id] - calls
    }
    return problems, false_alarms, misses


@pytest.fixture(scope="module")
def measured() -> tuple[dict[str, frozenset[str]], dict[str, frozenset[str]]]:
    args = cli.build_parser().parse_args(["agreement"])
    root = cli._repo_root()
    rubric = load_rubric(cli._resolve(args.rubric, root), build_registry().keys())
    findings = {finding.id: finding for finding in load_findings(cli._resolve(args.findings, root))}
    calls, deterministic, judged = cli._replayed_set(
        rubric,
        root,
        load_template(cli._resolve(args.template, root)),
        declared_held_out_calls(cli._resolve(cli._HELDOUT_SET, root)),
        transcripts=args.transcripts,
        policies=args.policies,
        corpus_version_file=args.corpus_version_file,
        policy_tool=args.policy_tool,
        run_log=args.run_log,
        rubric_file=args.rubric,
        held_out=False,
    )
    rollups = {rollup.entry.id: rollup for rollup in judged}
    traced = design_expected(rubric, findings)
    fired: dict[str, frozenset[str]] = {}
    for entry in rubric.for_tier(CheckTier.JUDGE):
        readings = readings_for(entry, deterministic, rollups)
        fired[entry.id] = frozenset(
            call for call in calls if readings[call][0] is Status.APPLICABLE and readings[call][1]
        )
    return fired, {entry_id: traced[entry_id] for entry_id in fired}


def test_every_judged_entry_fires_where_the_committed_reference_log_is_recorded_as_firing(
    measured: tuple[dict[str, frozenset[str]], dict[str, frozenset[str]]],
) -> None:
    fired, traced = measured
    assert set(fired) == set(EXPECTED_FIRING), (
        f"judged entries with no row, or rows with no entry: {set(fired) ^ set(EXPECTED_FIRING)}"
    )
    problems, false_alarms, misses = _compare(fired, traced)
    assert not problems, "\n".join(problems)
    assert false_alarms == RECORDED_FALSE_ALARMS, (
        f"new: {sorted(false_alarms - RECORDED_FALSE_ALARMS)}; "
        f"gone quiet: {sorted(RECORDED_FALSE_ALARMS - false_alarms)}"
    )
    assert misses == RECORDED_MISSES, (
        f"new: {sorted(misses - RECORDED_MISSES)}; now caught: {sorted(RECORDED_MISSES - misses)}"
    )


def test_the_judged_firing_comparison_would_notice_a_firing_that_moved(
    measured: tuple[dict[str, frozenset[str]], dict[str, frozenset[str]]],
) -> None:
    fired, traced = measured
    moved = dict(fired)
    moved["J-unnecessary-repetition"] = frozenset({"CALL-12", "CALL-07"})
    problems, false_alarms, _ = _compare(moved, traced)
    assert any("J-unnecessary-repetition" in problem for problem in problems)
    assert ("J-unnecessary-repetition", "CALL-07") in false_alarms

    quiet = dict(fired)
    quiet["J-policy-alignment"] = frozenset({"CALL-02"})
    problems, _, misses = _compare(quiet, traced)
    assert problems
    assert ("J-policy-alignment", "CALL-04") in misses
