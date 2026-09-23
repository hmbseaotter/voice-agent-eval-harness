#!/usr/bin/env python3
"""Run every phase-3 acceptance criterion and report what proved it.

    uv run python -m tools.verify_phase3

Run as a **module**, not as a path, for the reason D113 records: a script
invoked by path puts `tools/` on `sys.path` while pytest imports it as
`tools.verify_phase3`, and `-m` is the one form both agree on.

Same shape as the phase-1 and phase-2 verifiers, and the reporting loop is
imported from phase 2 rather than copied a third time. A criterion whose
evidence has been deleted or renamed shows as MISSING rather than dropping off
the list, and a criterion that is not fully checkable by machine says so instead
of collecting a green tick.

**What is different at this phase.** Three `[P3]` criteria cannot be
established by a suite that makes no model call -- one judged dimension
completing **in live mode**, the seeded prompt-injection transcript producing
the same verdict as the clean one, and the credential scan over the artifacts a
live run generates. They were listed as `PENDING LIVE RUN` rather than omitted,
because a criterion left off a list is a criterion nobody is waiting for.

**A live run closed all three**, and `tests/test_reference_run.py` is where they
are now asserted: against a committed run log a model actually produced, rather
than against a fixture. Everything else here runs against a scripted transport,
which is the right instrument for a classification -- which status a response
produces, how many calls it costs -- and the wrong one for a judgment.

**What that run did NOT establish is stated in the caveats and matters more than
the ticks.** The judge catches two of the three seeded misalignments and misses
the third on every repetition of every pass. Agreement is therefore *measured*
and still not *asserted*, and the miss is pinned by `RECORDED_MISS` so it cannot
be closed silently.
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
        "One judged dimension completes end to end in live mode and writes a run-log entry "
        "containing prompt, raw response, model id, config, timings and token counts.",
        tests=(
            f"{T}test_transport.py::test_the_generation_configuration_is_recorded_beside_the_stop_reason",
            f"{T}test_transport.py::test_every_call_that_returns_is_recorded",
            f"{T}test_cli.py::test_a_judged_replay_run_completes_over_a_log_it_recorded",
            f"{T}test_reference_run.py::test_a_reference_log_is_committed",
            f"{T}test_reference_run.py::test_every_entry_in_a_real_run_carries_a_stop_reason",
            f"{T}test_reference_run.py::test_a_real_run_records_n_repetitions_for_every_call",
            f"{T}test_reference_run.py::"
            "test_every_request_the_shipped_configuration_produces_is_in_the_log",
        ),
        caveat=(
            "The suite does not run live. The tick rests on the committed log of a live run, "
            "whose every request the shipped configuration produces is asserted present, not on "
            "a run made today."
        ),
        spec_anchor="One judged dimension completes end to end in live mode",
    ),
    Criterion(
        "A judged response citing a fact line [F3] validates successfully, and a response citing a "
        "non-existent [T999] triggers exactly one informed retry, whose correction names every "
        "fault the response shows.",
        tests=(
            f"{T}test_judge_prompt.py::test_a_real_fact_citation_validates",
            f"{T}test_judge_engine.py::test_a_fact_citation_validates_and_lands_in_the_evidence_quoted",
            f"{T}test_judge_engine.py::test_a_fabricated_citation_triggers_exactly_one_informed_retry",
            f"{T}test_judge_engine.py::test_the_retry_prompt_names_the_rejected_id_and_the_valid_set",
            f"{T}test_judge_engine.py::test_the_retry_would_notice_a_second_fault_it_does_not_name",
            f"{T}test_judge_engine.py::"
            "test_the_retry_would_notice_an_empty_citations_list_hiding_an_empty_rests_on",
        ),
        spec_anchor="triggers exactly one informed retry",
    ),
    Criterion(
        "A deliberately fabricated citation is rejected by the validator -- asserted directly, so "
        "the detector is proven against a true positive rather than assumed.",
        tests=(
            f"{T}test_judge_prompt.py::test_a_fabricated_citation_is_rejected",
            f"{T}test_judge_prompt.py::test_each_population_is_validated_against_its_own_set_and_not_the_union",
            f"{T}test_judge_prompt.py::test_a_bracketed_identifier_is_the_same_citation_as_a_bare_one",
        ),
        spec_anchor="proven against a true positive rather than assumed",
    ),
    Criterion(
        "Replay with a request hash absent from the log aborts and issues no network call, "
        "asserted by a transport spy.",
        tests=(
            f"{T}test_transport.py::test_replay_on_a_missing_hash_aborts_and_issues_no_live_call",
            f"{T}test_transport.py::test_replay_distinguishes_repetitions_of_one_request",
        ),
        spec_anchor="aborts and issues no network call",
    ),
    Criterion(
        "Replay against a log whose prompt-template hash differs aborts, and succeeds with "
        "--allow-stale-replay.",
        tests=(
            f"{T}test_transport.py::test_a_log_recorded_under_a_different_prompt_template_is_refused",
            f"{T}test_transport.py::test_a_log_recorded_under_a_different_rubric_version_is_refused",
            f"{T}test_transport.py::test_allow_stale_replay_lets_a_stale_log_through",
            f"{T}test_cli.py::test_a_stale_log_is_refused_and_the_flag_lets_it_through",
        ),
        spec_anchor="aborts, and succeeds with `--allow-stale-replay`",
    ),
    Criterion(
        "The seeded prompt-injection transcript produces the same verdict as an equivalent "
        "transcript with the injection removed.",
        tests=(
            f"{T}test_judge_prompt.py::test_the_injected_turn_is_rendered_as_data_rather_than_dropped",
            f"{T}test_judge_prompt.py::"
            "test_every_instruction_is_in_the_system_message_and_only_data_in_the_user_one",
            f"{T}test_judge_prompt.py::test_the_untrusted_block_is_delimited_and_labeled",
            f"{T}test_reference_run.py::"
            "test_the_injection_pair_produces_the_same_verdict_as_the_clean_transcript",
        ),
        caveat=(
            "Compared on the modal verdict of the recorded run rather than repetition for "
            "repetition, because a judged verdict is a sample (D17): the tick does not say the "
            "two transcripts drew identical verdicts."
        ),
        spec_anchor="same verdict as an equivalent transcript with the injection removed",
    ),
    Criterion(
        "A judged dimension whose retry budget is exhausted returns status: errored, and the run "
        "continues to completion rather than aborting.",
        tests=(
            f"{T}test_judge_engine.py::test_an_exhausted_retry_budget_returns_errored_rather_than_a_verdict",
            f"{T}test_judge_engine.py::test_the_run_continues_after_an_errored_result",
            f"{T}test_judge_engine.py::test_a_malformed_response_also_buys_one_retry",
        ),
        spec_anchor="returns `status: errored`, and the run continues to completion",
    ),
    Criterion(
        "A judged response with stop_reason refusal returns status: refused, records "
        "stop_details.category, consumes no retry, and is distinguishable from a retry-exhaustion "
        "errored by log inspection alone.",
        tests=(
            f"{T}test_judge_engine.py::test_a_refusal_returns_refused_and_consumes_no_retry",
            f"{T}test_judge_engine.py::"
            "test_the_three_no_verdict_outcomes_are_distinguishable_by_log_inspection",
            f"{T}test_transport.py::test_a_refusal_records_its_category_and_explanation",
            f"{T}test_transport.py::test_stop_details_are_read_only_on_a_refusal",
        ),
        spec_anchor="consumes no retry, and is distinguishable from a retry-exhaustion",
    ),
    Criterion(
        "A judged response truncated at max_tokens returns errored carrying its stop reason, and "
        "is distinguishable from a schema or citation failure by log inspection alone.",
        tests=(
            f"{T}test_judge_engine.py::test_a_truncated_response_returns_errored_carrying_its_stop_reason",
            f"{T}test_judge_engine.py::"
            "test_the_three_no_verdict_outcomes_are_distinguishable_by_log_inspection",
            f"{T}test_transport.py::test_a_truncated_response_is_marked_truncated_and_not_refused",
        ),
        spec_anchor="distinguishable from a schema or citation failure by log inspection alone",
    ),
    Criterion(
        "Every run-log entry for a judged call carries a stop_reason; the count missing one "
        "is zero.",
        tests=(
            f"{T}test_transport.py::test_every_recorded_entry_carries_a_stop_reason",
            f"{T}test_cli.py::test_a_judged_replay_run_records_its_own_log",
        ),
        spec_anchor="carries a `stop_reason`; the count missing one is zero",
    ),
    Criterion(
        "A rubric entry with no max_tokens is refused by name before any call is issued.",
        tests=(
            f"{T}test_rubric.py::test_a_judged_entry_with_no_max_tokens_is_refused_by_name",
            f"{T}test_rubric.py::test_max_tokens_is_refused_before_any_other_judged_field_is_checked",
            f"{T}test_rubric.py::test_a_max_tokens_that_is_not_a_positive_integer_is_refused",
        ),
        spec_anchor="refused by name before any call is issued",
    ),
    Criterion(
        "A live run reaching its ceiling halts without issuing a further call, asserted by a "
        "transport spy counting calls; a run with no --max-calls applies the declared default "
        "rather than running uncapped.",
        tests=(
            f"{T}test_transport.py::test_a_run_reaching_its_ceiling_issues_no_further_call",
            f"{T}test_transport.py::"
            "test_the_ceiling_is_a_number_of_calls_issued_and_not_that_number_plus_one",
            f"{T}test_transport.py::test_a_refused_call_is_not_recorded_because_it_did_not_happen",
            f"{T}test_judge_engine.py::test_the_ceiling_halts_the_run_and_names_itself",
            f"{T}test_cli.py::test_a_declared_default_ceiling_applies_when_max_calls_is_absent",
        ),
        spec_anchor="applies the declared default rather than running uncapped",
    ),
    Criterion(
        "A judged dimension run at N>1 writes N run-log entries.",
        tests=(
            f"{T}test_judge_engine.py::test_n_repetitions_issue_n_calls_and_write_n_run_log_entries",
            f"{T}test_judge_engine.py::test_the_repetitions_send_byte_identical_requests",
            f"{T}test_judge_engine.py::test_each_repetition_keeps_its_own_verdict",
        ),
        spec_anchor="run at N>1 writes N run-log entries",
    ),
    Criterion(
        "A transient transport error retries with backoff, and results already obtained are "
        "persisted when a later call aborts the run.",
        tests=(
            f"{T}test_judge_engine.py::test_a_transient_failure_is_retried_and_then_succeeds",
            f"{T}test_judge_engine.py::test_a_transport_that_gives_up_aborts_the_run_and_keeps_what_it_had",
            f"{T}test_judge_engine.py::test_the_repetitions_obtained_before_an_abort_are_not_discarded",
            f"{T}test_judge_engine.py::test_a_run_that_aborts_mid_call_reports_exactly_what_its_log_holds",
        ),
        caveat=(
            "The passage of time itself is not asserted: the delays are read as requested, which "
            "is the property the criterion names."
        ),
        spec_anchor="results already obtained are persisted when a later call aborts the run",
    ),
    Criterion(
        "An entry naming an unknown fact renderer in requires_facts aborts naming that category, "
        "rather than omitting it silently.",
        tests=(f"{T}test_judge_prompt.py::test_an_unknown_fact_category_aborts_naming_it",),
        spec_anchor="aborts naming that category, rather than omitting it silently",
    ),
    Criterion(
        "A dimension naming a fact category that is empty renders an explicit negative statement; "
        "a dimension naming no category omits the facts section entirely.",
        tests=(
            f"{T}test_judge_prompt.py::"
            "test_a_named_but_empty_category_renders_an_explicit_negative_statement",
            f"{T}test_judge_prompt.py::test_naming_no_category_omits_the_facts_section_entirely",
            f"{T}test_judge_prompt.py::test_every_declared_fact_renderer_returns_facts_for_some_design_call",
        ),
        spec_anchor="omits the facts section entirely",
    ),
    Criterion(
        "No credential value appears in any run log, report or error message, asserted by scanning "
        "every generated artifact for the configured key.",
        tests=(
            f"{T}test_transport.py::test_the_run_log_carries_no_credential_that_was_in_the_prompt",
            f"{T}test_transport.py::test_a_credential_in_the_environment_is_removed_from_text",
            f"{T}test_transport.py::test_every_declared_credential_variable_is_scrubbed",
            f"{T}test_transport.py::test_a_value_too_short_to_be_a_key_does_not_redact_the_whole_log",
            f"{T}test_transport.py::"
            "test_a_missing_credential_is_refused_naming_the_variables_and_not_their_values",
            f"{T}test_reference_run.py::test_no_credential_appears_in_the_committed_artifact",
        ),
        caveat=(
            "The committed log is scanned for a credential's shape rather than for a specific "
            "value, so the scan stands for keys of that shape alone."
        ),
        spec_anchor="scanning every generated artifact for the configured key",
    ),
    Criterion(
        "A live run requires a credential, prints an estimated call count and cost, and issues no "
        "call until confirmed.",
        tests=(
            f"{T}test_cli.py::test_live_mode_prints_an_estimate_and_issues_nothing_without_confirmation",
            f"{T}test_cli.py::test_the_estimate_is_the_product_of_calls_dimensions_and_n",
            f"{T}test_cli.py::test_confirmation_reads_a_non_interactive_stdin_as_no",
            f"{T}test_cli.py::test_confirmation_accepts_only_an_affirmative",
            f"{T}test_transport.py::test_an_unpriced_model_refuses_rather_than_estimating_zero",
            f"{T}test_transport.py::test_every_supported_model_is_priced",
        ),
        spec_anchor="prints an estimated call count and cost, and issues no call until confirmed",
    ),
    Criterion(
        "A full replay-mode run over the design set completes without network access.",
        tests=(
            f"{T}test_cli.py::test_a_judged_replay_run_completes_over_a_log_it_recorded",
            f"{T}test_transport.py::test_the_replay_path_does_not_import_the_sdk",
            f"{T}test_cli.py::test_no_transport_module_is_imported_by_a_deterministic_run",
        ),
        spec_anchor="SHALL complete without network access",
    ),
    Criterion(
        "The system splices no raw caller or agent speech into a judge prompt outside the "
        "delimited untrusted block, and keeps the citable-identifier syntax distinguishable "
        "between transcript and fact populations.",
        tests=(
            f"{T}test_judge_prompt.py::"
            "test_every_instruction_is_in_the_system_message_and_only_data_in_the_user_one",
            f"{T}test_judge_prompt.py::test_no_agent_or_caller_speech_reaches_the_facts_section",
            f"{T}test_judge_prompt.py::test_speech_is_tagged_t_and_facts_are_tagged_f",
            f"{T}test_judge_prompt.py::test_the_two_populations_are_numbered_independently",
        ),
        spec_anchor="keep the citable-identifier syntax distinguishable",
    ),
    Criterion(
        "The transport declares an explicit per-request client timeout rather than inheriting the "
        "SDK's default, and states whether its backoff replaces or wraps the SDK's own retries.",
        tests=(
            f"{T}test_transport.py::test_the_posture_constants_are_declared_rather_than_inherited",
            f"{T}test_transport.py::test_streaming_is_chosen_by_the_declared_threshold",
            f"{T}test_transport.py::test_the_sdk_accepts_every_parameter_the_seam_sends",
        ),
        caveat=(
            "What remains prose is the reasoning for choosing zero SDK retries, which D122 "
            "carries and no test can grade."
        ),
        spec_anchor="whether the specified exponential backoff **replaces**",
    ),
    Criterion(
        "Every judged field a rubric entry declares is read on every judged call -- the judged "
        "tier's form of the rule that no check parameter is hardcoded in Python.",
        tests=(
            f"{T}test_judge_engine.py::test_mutating_each_judged_field_changes_what_is_sent",
            f"{T}test_judge_engine.py::test_every_judged_field_has_a_declared_mutation",
            f"{T}test_judge_engine.py::test_the_schema_sent_is_built_from_the_entrys_scale",
            f"{T}test_judge_prompt.py::test_the_schema_enumerates_exactly_the_declared_scale",
            f"{T}test_judge_prompt.py::test_the_scale_is_rendered_with_its_definitions",
        ),
        caveat=(
            "Not a specification criterion. The mutation test reads every `JudgeSpec` field, but "
            "on one fixture entry, where `ParamView` for the deterministic tier runs on every "
            "entry of every run."
        ),
    ),
    Criterion(
        "The judged tier is declared in the shipped rubric, so `--tier assert` demonstrates a skip "
        "rather than an absence (D108, revisited at P3 as that decision said it would be, and "
        "again at P4 when the tier grew to its full population).",
        tests=(
            f"{T}test_claim_checks.py::test_the_shipped_rubric_declares_the_judged_tier_the_specification_allocates",
            f"{T}test_claim_checks.py::"
            "test_every_judged_entry_names_a_check_the_judged_vocabulary_declares",
            f"{T}test_judge_engine.py::test_the_judged_run_executes_only_judged_entries",
            f"{T}test_rubric_coverage.py::test_every_pending_judged_entry_is_a_judged_entry_that_exists",
            f"{T}test_reference_run.py::test_every_negative_instance_comes_back_clean_in_a_real_run",
            f"{T}test_reference_run.py::"
            "test_the_judge_catches_the_seeded_misalignments_it_is_recorded_as_catching",
            f"{T}test_reference_run.py::test_the_recorded_miss_is_still_missed_and_fails_when_it_is_not",
            f"{T}test_reference_run.py::"
            "test_the_no_clause_conflation_is_exactly_the_calls_it_is_recorded_as",
            f"{T}test_reference_run.py::"
            "test_the_calls_that_did_retrieve_clauses_are_judged_on_their_paraphrase",
        ),
        caveat=(
            "**Agreement is measured and not achieved**: the judge misses F-85 on CALL-19 on "
            "every repetition of every pass, pinned by `RECORDED_MISS` rather than tuned toward, "
            "since sharpening the criteria until it flips would fit a prompt to a transcript the "
            "author can read (D21). The judged family's firing table pins where each entry fires "
            "on the committed log and claims no agreement (D202)."
        ),
    ),
)


def main(argv: list[str] | None = None) -> int:
    """The phase-2 reporting loop, over this phase's criteria.

    Imported rather than copied. D113's argument for importing the suite runner
    applies with more force to the loop that decides what PASS means: a third
    copy would be a third place for "EVIDENCE MISSING" to stop meaning the same
    thing.
    """
    return _phase_main(argv, criteria=CRITERIA, phase=3)


if __name__ == "__main__":
    raise SystemExit(main())
