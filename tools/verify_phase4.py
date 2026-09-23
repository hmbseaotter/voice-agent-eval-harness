#!/usr/bin/env python3
"""Run every phase-4 acceptance criterion and report what proved it.

    uv run python -m tools.verify_phase4

Run as a **module**, not as a path, for the reason D113 records: a script
invoked by path puts `tools/` on `sys.path` while pytest imports it as
`tools.verify_phase4`, and `-m` is the one form both agree on.

Same shape as the first three verifiers, and the reporting loop is imported
from phase 2 rather than copied a fourth time.

**What is different at this phase.** Its contract was **amended before a line
of code was written** (D130). Phase 4 opened by running phase 2's coverage
check over its own five requirements and eleven criteria, and found four of the
five covered only in the half the requirement names, plus a whole deliverable
-- the two-audience report -- carrying no criterion at all. Nine criteria were
added, and a tenth arrived with the precondition D132 built. So **ten of the
entries below verify a criterion that did not exist when the phase started**,
and each of those exists because the original could not tell the design from
its inversion.

The four halves worth naming, because they are what a reader should look for
when they run this list against a later phase:

* a synthesis citation checker that reported **every** citation as a defect
  passed the criterion as written;
* two criteria about the rate named no tier, and the deterministic breakdown
  has printed all five status counts since P2 -- so both went green off a tier
  that was already there;
* the verdict-distribution criterion resolved either way on a unanimous
  fixture;
* the escaping criterion was satisfied by a renderer that deleted the
  characters rather than escaping them.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from tools.verify_phase1 import Criterion
from tools.verify_phase2 import main as _phase_main

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]

T: Final[str] = "tests/"

CRITERIA: Final[tuple[Criterion, ...]] = (
    Criterion(
        "`uv run harness report` on a fresh clone with no credential present produces the full "
        "report in replay mode and exits zero.",
        tests=(
            f"{T}test_report.py::test_the_report_is_produced_on_a_clone_with_no_credential_in_reach",
            f"{T}test_report.py::test_the_report_carries_both_audience_sections_with_their_entries",
            f"{T}test_report.py::test_the_report_would_notice_its_path_reading_a_credential",
        ),
        caveat=(
            "Both declared credential variables are removed from the subprocess environment. The "
            "directory the command runs from does not keep `.env` out of reach, since the command "
            "reads `.env` at the repository root it resolves whatever the working directory "
            "(P4-12); the tick holds because the report path reads no credential at all, which "
            "the third test pins by making every credential reader raise (OB-29)."
        ),
        spec_anchor="on a fresh clone with no credential present",
    ),
    Criterion(
        "Every rubric entry's `traces_to` resolves to an existing findings row; unresolved count "
        "is zero.",
        tests=(
            f"{T}test_platform_checks.py::test_every_traced_finding_resolves_to_a_findings_row",
        ),
        spec_anchor="resolves to an existing findings row",
    ),
    Criterion(
        "The report routes every finding to one of its two audiences by `owner`, asserted on "
        "which rows land in which section rather than on the sections existing.",
        tests=(
            f"{T}test_report.py::"
            "test_every_entry_is_routed_to_an_audience_by_the_owner_of_what_it_traces",
            f"{T}test_report.py::"
            "test_an_entry_tracing_findings_on_two_desks_appears_in_both_sections",
            f"{T}test_report.py::test_the_report_carries_both_audience_sections_with_their_entries",
            f"{T}test_report.py::"
            "test_the_audience_sections_would_notice_an_entry_rendered_on_the_wrong_desk",
        ),
        spec_anchor="routes every finding to one of its two audiences",
    ),
    Criterion(
        "Every call carries orthogonal labels rather than one collapsed value, asserted on a call "
        "that failed in more than one independent way.",
        tests=(
            f"{T}test_report.py::"
            "test_a_call_that_failed_in_more_than_one_way_carries_orthogonal_labels",
            f"{T}test_report.py::"
            "test_the_calls_table_would_notice_a_judged_entry_found_on_a_minority_of_repetitions",
        ),
        spec_anchor="orthogonal** labels rather than one collapsed value",
    ),
    Criterion(
        "The non-determinism caveat renders inline, beside the judged numbers it qualifies, "
        "asserted on its position within the report rather than on its presence anywhere in it.",
        tests=(
            f"{T}test_report.py::"
            "test_the_non_determinism_caveat_is_inline_above_the_numbers_it_qualifies",
        ),
        spec_anchor="renders **inline**, beside the judged numbers",
    ),
    Criterion(
        "Every rate-gated dimension reports its pass rate together with its `not_applicable`, "
        "`unevaluable` and `errored` counts.",
        tests=(
            f"{T}test_report.py::test_every_rate_gated_judged_dimension_reports_its_four_other_counts",
            f"{T}test_judge_rollup.py::test_the_rate_is_none_rather_than_zero_when_no_call_produced_a_verdict",
            f"{T}test_report.py::"
            "test_the_judged_tables_would_notice_an_errored_repetition_among_verdicts",
            f"{T}test_report.py::"
            "test_a_call_row_would_notice_its_errored_repetition_dropped_beside_its_verdicts",
        ),
        spec_anchor="together with its `not_applicable`, `unevaluable` and `errored` counts",
    ),
    Criterion(
        "That reporting is asserted for a judged rate-gated dimension, not only a deterministic "
        "one.",
        tests=(
            f"{T}test_report.py::test_every_rate_gated_judged_dimension_reports_its_four_other_counts",
            f"{T}test_report.py::"
            "test_the_judged_tables_would_notice_an_errored_repetition_among_verdicts",
        ),
        spec_anchor="asserted for a **judged** rate-gated dimension",
    ),
    Criterion(
        "The same evidence-on-negative-pole guard fires for each of the judged scales, not only "
        "for one.",
        tests=(
            f"{T}test_claim_checks.py::"
            "test_the_evidence_guard_fires_for_every_judged_scale_the_rubric_declares",
            f"{T}test_rubric.py::test_the_evidence_guard_reads_the_declared_pole_and_not_a_familiar_word",
        ),
        spec_anchor="fires for **each** of the six judged scales",
    ),
    Criterion(
        "A rationale containing a pipe character and a newline renders without corrupting the "
        "report table.",
        tests=(
            f"{T}test_report.py::test_a_pipe_and_a_newline_render_without_corrupting_the_table",
        ),
        spec_anchor="pipe character and a newline renders without corrupting",
    ),
    Criterion(
        "The escaped rendering still carries what it escaped: the model's text is recoverable "
        "from the rendered cell rather than merely absent from where it would have broken the "
        "table.",
        tests=(
            f"{T}test_report.py::test_the_escaped_text_still_carries_what_it_escaped",
            f"{T}test_report.py::test_escaping_is_injective_so_two_rationales_cannot_render_the_same",
        ),
        spec_anchor="still **carries** what it escaped",
    ),
    Criterion(
        "A judged dimension evaluated at N>1 is reported as a verdict distribution, not a single "
        "verdict.",
        tests=(
            f"{T}test_judge_rollup.py::"
            "test_a_dimension_whose_repetitions_disagree_is_reported_as_a_distribution",
            f"{T}test_report.py::test_a_judged_dimension_is_reported_as_a_distribution_in_the_report",
            f"{T}test_cli.py::test_a_judged_replay_run_completes_over_a_log_it_recorded",
        ),
        spec_anchor="reported as a verdict distribution, not a single verdict",
    ),
    Criterion(
        "A dimension whose N repetitions disagree is reported with the count standing against "
        "each verdict it produced.",
        tests=(
            f"{T}test_judge_rollup.py::"
            "test_a_dimension_whose_repetitions_disagree_is_reported_as_a_distribution",
            f"{T}test_judge_rollup.py::"
            "test_the_distribution_is_in_scale_order_rather_than_count_order",
        ),
        spec_anchor="whose N repetitions **disagree**",
    ),
    Criterion(
        "A rate-gated dimension reports `refused` counts alongside the other three, and `refused` "
        "results are excluded from the rate denominator.",
        tests=(
            f"{T}test_judge_rollup.py::test_every_status_that_is_not_applicable_leaves_the_denominator",
            f"{T}test_report.py::test_every_rate_gated_judged_dimension_reports_its_four_other_counts",
            f"{T}test_report.py::"
            "test_the_judged_tables_would_notice_an_errored_repetition_among_verdicts",
        ),
        spec_anchor="reports `refused` counts alongside",
    ),
    Criterion(
        "`errored` and `not_applicable` results are excluded from the rate denominator, asserted "
        "per status.",
        tests=(
            f"{T}test_judge_rollup.py::test_every_status_that_is_not_applicable_leaves_the_denominator",
        ),
        spec_anchor="excluded from the rate denominator, asserted per status",
    ),
    Criterion(
        "A synthesis narrative citing a rubric id that produced no result in the same run is "
        "reported as a defect.",
        tests=(
            f"{T}test_judge_engine.py::"
            "test_a_synthesis_resting_on_a_dimension_that_produced_no_result_is_a_reported_defect",
            f"{T}test_judge_engine.py::"
            "test_the_synthesis_is_shown_the_dimensions_it_is_allowed_to_rest_on",
        ),
        spec_anchor="citing a rubric id that produced no result",
    ),
    Criterion(
        "A synthesis narrative citing only ids that did produce a result in the same run is "
        "reported clean.",
        tests=(
            f"{T}test_judge_engine.py::"
            "test_a_synthesis_resting_only_on_dimensions_that_ran_is_reported_clean",
        ),
        spec_anchor="citing only ids that **did** produce a result",
    ),
    Criterion(
        "A judged dimension whose declared precondition is not met returns `not_applicable` and "
        "issues no call, and one declaring no precondition applies to every call -- asserted as a "
        "partition of the design set.",
        tests=(
            f"{T}test_judge_engine.py::"
            "test_a_dimension_whose_precondition_fails_returns_not_applicable_and_issues_nothing",
            f"{T}test_judge_engine.py::test_a_dimension_whose_precondition_holds_is_evaluated_normally",
            f"{T}test_judge_engine.py::"
            "test_the_precondition_would_notice_a_dimension_that_stopped_applying_to_anything",
            f"{T}test_rubric.py::test_a_precondition_on_a_category_the_entry_never_renders_is_refused",
        ),
        spec_anchor="whose declared precondition is not met",
    ),
    Criterion(
        "The byte-identical golden-report regression runs in CI, not only when a human remembers "
        "to run it.",
        tests=(f"{T}test_report.py::test_the_golden_report_regression_runs_in_ci",),
        spec_anchor="golden-report regression runs in CI",
    ),
    Criterion(
        "The Tier A report section is byte-identical across two consecutive runs and across both "
        "modes.",
        tests=(
            f"{T}test_report.py::test_the_tier_a_section_is_byte_identical_across_runs_and_across_modes",
        ),
        caveat=(
            "The across-modes half is asserted on the renderer's signature, since a suite may not "
            "issue a live run: the tick says the section cannot depend on the mode, not that a "
            "live render was compared."
        ),
        spec_anchor="Tier A report section is byte-identical",
    ),
    Criterion(
        "The full report is byte-identical across two consecutive replay runs; the same assertion "
        "is NOT applied to live runs.",
        tests=(f"{T}test_report.py::test_two_consecutive_replay_reports_are_byte_identical",),
        caveat=(
            "The negative half -- that live is not asserted this way -- is a property of what "
            "this suite does **not** contain, and no test can assert an absence of itself. What "
            "stands behind it is that the report command has no `--mode` flag at all: there is "
            "no live report to compare."
        ),
        spec_anchor="NOT applied to live runs",
    ),
    Criterion(
        "The golden-report regression compares against a committed artifact rather than two runs "
        "of the same build against each other.",
        tests=(
            f"{T}test_report.py::test_a_report_snapshot_is_committed",
            f"{T}test_report.py::test_the_report_matches_the_committed_snapshot_byte_for_byte",
        ),
        spec_anchor="compares against a **committed** artifact",
    ),
    Criterion(
        "A live run resumed from a log cut in half issues exactly the requests that log lacks, "
        "completes under a call ceiling of that many, exits as a replay of the full log does, "
        "prints how many answers it served and how many calls it issued, and writes a log reading "
        "`mode: live` that names the session it resumed; a log whose last line was cut off "
        "mid-write is resumed from its last complete record, and a log recorded in replay mode, "
        "or against a different rubric version or prompt template, or answering none of the "
        "dimension requests the run would send, is refused before any confirmation is asked for.",
        tests=(
            f"{T}test_cli.py::test_a_resumed_run_issues_only_the_calls_its_log_lacks",
            f"{T}test_cli.py::test_a_resume_log_is_refused_before_anyone_is_asked_to_approve_spend",
            f"{T}test_cli.py::test_a_resume_would_notice_a_log_answering_no_dimension_request_run_anyway",
            f"{T}test_cli.py::test_a_resume_under_an_edited_entry_would_notice_its_counts_misprinted",
            f"{T}test_cli.py::test_a_resume_reads_a_torn_log_to_its_last_complete_record",
            f"{T}test_cli.py::test_resume_needs_live_mode",
        ),
        caveat=(
            "The refusal reads the dimensions' first attempts alone, because a synthesis's request "
            "exists only once the dimensions answer: a log answering one dimension request is "
            "resumed however little else it answers, and only the run's end says how much was "
            "served. The header is written before the first call, so a resumed run that aborts "
            "before it reaches an answer its log holds still names the session it resumed, and "
            "prints that it served 0."
        ),
        spec_anchor="resumed from a log cut in half",
    ),
    Criterion(
        "A judged entry that declares its middle value `violating` fails its gate on a call whose "
        "modal verdict is that value and resolves a five-five split between that value and the "
        "positive pole to it, while an entry declaring nothing still passes its middle value; a "
        "declaration naming a verdict outside the scale, omitting the negative pole or naming "
        "every member is refused by name.",
        tests=(
            f"{T}test_judge_rollup.py::"
            "test_the_gate_would_notice_a_declared_violating_verdict_read_as_a_pass",
            f"{T}test_judge_rollup.py::"
            "test_the_tie_rule_would_notice_a_split_with_a_violating_verdict_read_as_a_pass",
            f"{T}test_rubric.py::"
            "test_an_entry_declaring_no_violating_verdicts_violates_on_its_negative_pole_alone",
            f"{T}test_rubric.py::"
            "test_the_loader_would_notice_a_violating_verdict_outside_the_scale",
            f"{T}test_rubric.py::"
            "test_the_loader_would_notice_a_violating_set_without_its_negative_pole",
            f"{T}test_rubric.py::test_the_loader_would_notice_a_violating_set_naming_every_verdict",
            f"{T}test_reference_run.py::test_every_traced_finding_is_caught_or_missed_as_recorded",
        ),
        caveat=(
            "That counting a middle value is right for the entries that do it is not what the "
            "tick buys: that is agreement against labels written blind, which is the held-out "
            "section of `harness agreement` and is never committed (D175, D202). Nor does it say "
            "an entry's definitions separate its "
            "two violating verdicts -- a call with one instance of several failing fits both, "
            "which the gate no longer depends on (D160, D162)."
        ),
        spec_anchor="declares its middle value `violating`",
    ),
    Criterion(
        "A live run prints an expected cost beside its estimated ceiling, pricing each entry at "
        "the mean first-attempt answer the committed reference log recorded and at the calls per "
        "first attempt it recorded, informed retries included, which on that log sits between "
        "what its recorded calls spent and the ceiling; an entry the log never recorded is priced "
        "at its ceiling and named, a log recorded under another rubric version or prompt template "
        "is named with its differences beside the figure, and with no recorded run to read the "
        "line says the figure was not computed.",
        tests=(
            f"{T}test_cli.py::"
            "test_live_mode_prints_an_estimate_and_issues_nothing_without_confirmation",
            f"{T}test_reference_run.py::"
            "test_the_expected_cost_sits_between_what_the_reference_run_spent_and_the_ceiling",
            f"{T}test_cli.py::test_an_entry_nothing_recorded_is_priced_at_its_ceiling_and_named",
            f"{T}test_cli.py::"
            "test_the_expected_figure_says_why_it_is_absent_when_nothing_was_recorded",
            f"{T}test_cli.py::test_the_expected_figure_would_notice_recorded_retries_left_out",
            f"{T}test_reference_run.py::"
            "test_the_retry_share_would_notice_the_retries_a_log_records_uncounted",
            f"{T}test_cli.py::test_the_expected_figure_would_notice_a_stale_log_left_unflagged",
        ),
        caveat=(
            "A retry is priced at its entry's first-attempt size, though it also carries the "
            "rejected answer and the valid identifiers. The stale-log line compares the rubric "
            "version and the template hash alone, so an entry edited under an unchanged version "
            "is not named, as replay does not refuse it, and the figure predicts from one "
            "recording."
        ),
        spec_anchor="prints an expected cost beside its estimated ceiling",
    ),
)


def main(argv: list[str] | None = None) -> int:
    """The phase-2 reporting loop, over this phase's criteria."""
    return _phase_main(argv, criteria=CRITERIA, phase=4)


if __name__ == "__main__":
    raise SystemExit(main())
