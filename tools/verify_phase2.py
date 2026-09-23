#!/usr/bin/env python3
"""Run every phase-2 acceptance criterion and report what proved it.

    uv run python -m tools.verify_phase2

Run as a **module**, not as a path. This imports the suite runner from
`verify_phase1` rather than keeping a second copy of it (D113), and a script
invoked by path puts `tools/` on `sys.path` while pytest imports it as
`tools.verify_phase2` -- two invocation modes wanting two different import
forms. `-m` is the one form both agree on, and it needs no path manipulation
at the top of this file to work.

Same shape as the phase-1 verifier and for the same reasons: a criterion whose
evidence has been deleted or renamed shows as MISSING rather than dropping off
the list, and a criterion that is not fully checkable by machine says so
instead of collecting a green tick.

Two things are different at this phase.

**The gold-set gate.** D105: this corpus is seeded with defects by
construction, so `harness run` exits non-zero over it and that is the tier
working. "Green" for phase 2 is **agreement with the gold set** -- the right
gates firing on the right calls -- which the run's exit code cannot express.
That agreement is a criterion here in its own right.

**The criteria list moved.** D104 re-derived the `[P2]` criteria against the
`[P2]` requirements and added six, closing halves that nothing asserted. The
`spec_anchor` on every entry binds this list to the document, so a criterion
added to the specification and never added here is visible rather than silent.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Final

from tools.verify_phase1 import (
    ASSERTED_ELSEWHERE,
    NOT_YET_BUILT,
    Criterion,
    Declared,
    criteria_in_document,
    diagnose_suite_exit,
    load_suite_results,
)

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]

T: Final[str] = "tests/"

CRITERIA: Final[tuple[Criterion, ...]] = (
    Criterion(
        "`uv run harness run --tier assert` completes over the design set, issues zero model "
        "calls (asserted by a transport spy), and prints a per-check breakdown.",
        tests=(
            f"{T}test_cli.py::test_the_assert_tier_completes_with_every_route_to_a_socket_refused",
            f"{T}test_cli.py::test_the_spy_would_notice_a_connection",
            f"{T}test_cli.py::test_no_transport_module_is_imported_by_a_deterministic_run",
            f"{T}test_cli.py::test_the_run_prints_a_line_for_every_entry_of_the_tier",
        ),
        spec_anchor="issues zero model calls (asserted by a transport spy)",
    ),
    Criterion(
        "Every result carries the rubric version, the corpus version and the extraction-artifact "
        "hash; the count of results missing any of the three is zero.",
        tests=(
            f"{T}test_engine.py::test_every_result_the_builder_makes_carries_its_provenance",
            f"{T}test_cli.py::test_no_result_is_missing_a_provenance_value",
            f"{T}test_result_contract.py::test_every_result_carries_all_three_provenance_values",
        ),
        spec_anchor="the count of results missing any of the three is zero",
    ),
    Criterion(
        "A rubric declaring tier: judge with gate: absolute is rejected, and the error names "
        "that entry id.",
        tests=(
            f"{T}test_rubric.py::"
            "test_a_judged_entry_with_an_absolute_gate_is_rejected_by_name_and_reason",
            f"{T}test_rubric.py::test_the_same_entry_loads_with_a_rate_gate",
            f"{T}test_rubric.py::test_a_deterministic_entry_may_declare_an_absolute_gate",
        ),
        spec_anchor="with `gate: absolute` is rejected, and the error names that entry id.",
    ),
    Criterion(
        "A check returning a verdict outside its declared scale raises, naming entry id and "
        "verdict.",
        tests=(
            f"{T}test_rubric.py::test_a_verdict_outside_the_scale_raises_naming_entry_and_verdict",
            f"{T}test_engine.py::"
            "test_a_verdict_outside_the_scale_stops_the_run_rather_than_being_reported",
        ),
        spec_anchor="outside its declared scale raises, naming entry id and verdict.",
    ),
    Criterion(
        "A negative-pole verdict with empty evidence raises, asserted for a judged scale.",
        tests=(
            f"{T}test_rubric.py::test_the_negative_pole_with_no_evidence_raises_for_a_judged_scale",
            f"{T}test_rubric.py::"
            "test_the_evidence_guard_reads_the_declared_pole_and_not_a_familiar_word",
        ),
        spec_anchor="empty evidence raises, asserted for a judged scale.",
    ),
    Criterion(
        "A dimension with no corresponding ground truth returns status: unevaluable, and that "
        "result is excluded from the rate denominator.",
        tests=(
            f"{T}test_engine.py::test_only_applicable_results_form_the_denominator",
            f"{T}test_engine.py::test_a_rate_of_zero_is_not_the_same_as_no_denominator",
        ),
        spec_anchor="returns `status: unevaluable`, and that result is excluded",
    ),
    Criterion(
        "Every unevaluable result names the ground-truth reference that was missing; the count "
        "carrying no such identifier is zero.",
        tests=(
            f"{T}test_result_contract.py::"
            "test_unevaluable_names_the_reference_the_corpus_did_not_supply",
            f"{T}test_result_contract.py::test_a_bare_unevaluable_is_refused",
            f"{T}test_result_contract.py::"
            "test_a_whitespace_reference_does_not_satisfy_the_requirement",
            f"{T}test_policy_checks.py::"
            "test_removing_every_governing_clause_makes_the_result_unevaluable",
        ),
        spec_anchor="names the ground-truth reference that was missing",
    ),
    Criterion(
        "A rubric carrying a duplicate entry id, a missing gate, a rate gate with no threshold, "
        "or an unknown check key is rejected in each of the four cases, naming the entry.",
        tests=(
            f"{T}test_rubric.py::test_a_duplicate_entry_id_is_rejected_by_name",
            f"{T}test_rubric.py::test_a_missing_gate_is_rejected_by_name",
            f"{T}test_rubric.py::test_a_rate_gate_with_no_threshold_is_rejected_by_name",
            f"{T}test_rubric.py::test_an_unknown_check_key_is_rejected_by_name",
            f"{T}test_rubric.py::test_each_of_the_four_refusals_needs_only_its_own_defect",
        ),
        spec_anchor="rejected in each of the four cases, naming the offending entry.",
    ),
    Criterion(
        "A rubric carrying entries of both tiers, run with --tier assert, produces a result for "
        "every deterministic entry and for no judged entry.",
        tests=(
            f"{T}test_engine.py::test_only_the_selected_tiers_entries_produce_a_result",
            f"{T}test_engine.py::"
            "test_selecting_the_judged_tier_runs_the_judged_entry_and_not_the_other",
            # Through P2 this named the test asserting the shipped rubric
            # declared NO judged entry, which recorded that the shipped run's
            # silence was trivial (D108). Its successor asserts the inverse: a
            # judged tier exists, so the skip is a decision the selector makes
            # rather than an absence. Renamed at P4, when the assertion moved
            # from a count of one to the exact list -- which still buys this
            # claim, and buys more: seven entries with one misnamed would have
            # passed a count.
            f"{T}test_claim_checks.py::test_the_shipped_rubric_declares_the_judged_tier_the_specification_allocates",
        ),
        spec_anchor="produces a result for every deterministic entry and for no judged entry",
    ),
    Criterion(
        "An absolute-gate negative verdict fails both the call and the run, asserted on the "
        "process exit code.",
        tests=(
            f"{T}test_cli.py::test_an_absolute_gate_negative_fails_the_run_on_the_process_exit_code",
            f"{T}test_cli.py::test_a_run_whose_gates_all_hold_exits_zero",
            f"{T}test_engine.py::test_an_absolute_gate_fails_on_a_single_violation",
        ),
        spec_anchor="fails both the call and the run, asserted on the process exit code.",
    ),
    Criterion(
        "mypy --strict passes with zero errors and zero ignores.",
        commands=((sys.executable, "-m", "mypy"),),
        spec_anchor="`mypy --strict` passes with zero errors and zero ignores.",
    ),
    Criterion(
        "ruff check and ruff format --check pass.",
        commands=(
            (sys.executable, "-m", "ruff", "check", "."),
            (sys.executable, "-m", "ruff", "format", "--check", "."),
        ),
        spec_anchor="`ruff check` and `ruff format --check` pass.",
    ),
    Criterion(
        "Each deterministic failure mode named in taxonomy-coverage Part 3 (W2-W10, W19) has a "
        "test that fails when that defect is present.",
        tests=(
            f"{T}test_claim_checks.py::"
            "test_w2_a_claim_before_the_action_is_a_violation_even_when_it_later_succeeds",
            f"{T}test_claim_checks.py::"
            "test_w2_the_control_turning_the_ordering_rule_off_passes_that_call",
            f"{T}test_claim_checks.py::"
            "test_w3_a_topic_resolving_to_two_invoked_tools_is_unevaluable_not_disjoined",
            f"{T}test_claim_checks.py::"
            "test_a_word_list_would_have_fired_on_three_turns_a_phrase_list_does_not",
            f"{T}test_values.py::test_w5_a_spoken_integer_does_not_ground_against_a_longer_payload_figure",
            f"{T}test_values.py::test_w5_the_word_boundary_is_the_thing_that_fails",
            f"{T}test_values.py::test_w6_a_thousands_separator_in_the_payload_is_stripped_too",
            f"{T}test_values.py::test_w7_a_cue_is_found_case_insensitively_when_the_entry_says_so",
            f"{T}test_values.py::test_w8_a_december_call_naming_a_january_date_resolves_forward",
            f"{T}test_values.py::test_w8_a_date_too_far_from_the_call_is_refused_rather_than_guessed",
            f"{T}test_omission_checks.py::"
            "test_a_number_with_no_money_cue_does_not_read_as_the_value_being_spoken",
            f"{T}test_omission_checks.py::"
            "test_a_payload_figure_spoken_in_words_with_a_cue_grounds_against_it",
            f"{T}test_conduct_checks.py::test_the_spoken_day_is_compared_against_the_venues_own_clock",
            f"{T}test_omission_checks.py::"
            "test_w9_a_bare_length_filter_with_no_stopwords_fires_on_benign_turns",
            f"{T}test_claim_checks.py::"
            "test_w10_a_state_cleared_before_the_action_is_not_a_violation",
        ),
        caveat=(
            "W19 is a phase-1 property -- a conformance test that re-reads the source "
            "transcript and asserts reassembly -- and it is verified by the phase-1 verifier, "
            "not here. The nine listed above are W2-W10. This entry claims the deterministic "
            "tier's own failure modes; it does not re-claim the extraction tier's. "
            "W8 is the one row this tick does NOT stand for at tier level: its two tests "
            "exercise values.complete_year, and no shipped check completes a year -- "
            "spoken_local_date_wrong compares the day alone. W2-W7, W9 and W10 all run "
            "through code the assert tier executes, W5 and W6 as fixtures of the value "
            "layer the tier calls and the rest over the design corpus itself."
        ),
        spec_anchor="has a test that fails when that defect is present",
    ),
    Criterion(
        "Every parameter declared in every rubric entry is read by the check that entry names.",
        tests=(
            f"{T}test_rubric.py::test_an_unread_parameter_fails_the_entry_by_name",
            f"{T}test_rubric.py::test_an_entry_whose_parameters_were_all_read_passes",
            f"{T}test_engine.py::test_an_entry_whose_parameters_went_unread_stops_the_run",
            f"{T}test_claim_checks.py::test_no_entry_declares_a_parameter_its_check_does_not_read",
        ),
        spec_anchor=(
            "asserted by an unread-parameter guard that runs over every entry of every call"
        ),
    ),
    Criterion(
        "A CI workflow runs the type check, both linters, the test suite and "
        "tools/check_spec_interface.py, and fails the build on any non-zero exit.",
        tests=(
            f"{T}test_phase2_acceptance.py::test_the_workflow_runs_every_gate_this_phase_declares",
            f"{T}test_phase2_acceptance.py::test_the_workflow_runs_the_deterministic_tier_and_its_verifier",
        ),
        spec_anchor="fails the build on any non-zero exit.",
    ),
    Criterion(
        "Editing a threshold or signal list in the rubric changes harness behavior, asserted by "
        "a test that mutates the rubric and observes a different verdict.",
        tests=(
            f"{T}test_claim_checks.py::test_mutating_a_declared_parameter_moves_a_verdict",
            f"{T}test_claim_checks.py::test_the_signal_list_is_read_from_the_rubric",
            f"{T}test_platform_checks.py::test_mutating_a_platform_parameter_moves_the_firing_set",
            f"{T}test_values.py::test_the_lexicon_is_data_and_changing_it_changes_the_reading",
        ),
        spec_anchor="mutates the rubric and observes a different verdict",
    ),
    Criterion(
        "Contract types are frozen dataclasses and module constants are typing.Final, asserted "
        "by a test that attempts mutation and expects failure.",
        tests=(
            f"{T}test_result_contract.py::test_every_contract_dataclass_is_declared_frozen",
            f"{T}test_result_contract.py::test_the_frozen_scan_asks_the_question_it_thinks_it_asks",
            f"{T}test_result_contract.py::test_mutating_a_frozen_result_fails",
            f"{T}test_result_contract.py::"
            "test_every_final_constant_holds_a_value_that_cannot_be_mutated",
            f"{T}test_result_contract.py::test_mutating_a_final_tuple_constant_fails",
        ),
        spec_anchor="asserted by a test that attempts mutation and expects failure.",
    ),
    Criterion(
        "verdict is None for every result whose status is not applicable; the count of "
        "violations is zero.",
        tests=(
            f"{T}test_result_contract.py::test_a_verdict_on_any_other_status_is_refused",
            f"{T}test_result_contract.py::test_no_other_status_counts_toward_a_rate",
        ),
        spec_anchor="is not `applicable`; the count of violations is zero.",
    ),
    Criterion(
        "verdict is populated for every result whose status IS applicable; the count of "
        "violations is zero.",
        tests=(
            f"{T}test_result_contract.py::test_applicable_without_a_verdict_is_refused",
            f"{T}test_result_contract.py::test_applicable_with_a_verdict_is_the_one_shape_that_holds",
        ),
        spec_anchor="is populated for every result whose `status` **is** `applicable`",
    ),
    Criterion(
        "The status channel admits exactly the five declared values and refuses a sixth by name.",
        tests=(
            f"{T}test_result_contract.py::test_a_sixth_status_is_refused_by_name",
            f"{T}test_result_contract.py::"
            "test_a_status_that_is_merely_the_right_string_is_still_refused",
            f"{T}test_result_contract.py::"
            "test_the_channel_is_exactly_the_five_the_specification_declares",
            f"{T}test_result_contract.py::test_every_declared_status_constructs",
        ),
        spec_anchor="admits exactly the five declared values and refuses a sixth by name",
    ),
    Criterion(
        "A grounding check resolves a claim against the concatenation of tool-call details, "
        "variable values and retrieved policy clauses.",
        tests=(
            f"{T}test_policy_checks.py::test_the_only_supporting_value_lives_in_a_retrieved_clause",
            f"{T}test_policy_checks.py::"
            "test_removing_every_governing_clause_makes_the_result_unevaluable",
            f"{T}test_context_seam.py::"
            "test_a_retrieved_document_puts_every_clause_in_the_ground_truth",
        ),
        spec_anchor="asserted by a fixture where the only supporting value lives in a retrieved",
    ),
    Criterion(
        "No deterministic check admits agent speech as evidence, asserted by a control that adds "
        "the supporting value to an agent turn and to nowhere else.",
        tests=(
            f"{T}test_context_seam.py::"
            "test_a_value_that_lives_only_in_an_agent_turn_is_not_in_the_ground_truth",
            f"{T}test_context_seam.py::"
            "test_no_agent_turn_in_the_design_set_appears_in_its_calls_ground_truth",
            f"{T}test_context_seam.py::"
            "test_the_leak_scan_would_notice_a_turn_that_was_in_the_corpus",
            f"{T}test_policy_checks.py::"
            "test_adding_the_supporting_sentence_to_speech_alone_does_not_move_the_verdict",
            f"{T}test_platform_checks.py::"
            "test_no_platform_check_changes_its_verdict_when_speech_is_rewritten",
            f"{T}test_platform_checks.py::"
            "test_the_scrub_does_move_a_check_that_reads_speech_by_design",
        ),
        spec_anchor="adds the supporting value to an agent turn and to nowhere else",
    ),
    # -- Not a specification criterion: the phase gate D105 defines --------
    Criterion(
        "The tier's verdicts agree with the gold set: every entry fires on exactly the calls the "
        "findings document puts its traced findings on. (D105 -- the phase gate, since the run's "
        "exit code cannot express it.)",
        tests=(
            f"{T}test_claim_checks.py::test_the_completion_claim_check_fires_on_exactly_the_seeded_calls",
            f"{T}test_claim_checks.py::"
            "test_the_completion_claim_check_is_silent_where_the_claim_is_supported",
            f"{T}test_platform_checks.py::"
            "test_each_platform_entry_fires_on_exactly_its_seeded_calls",
            f"{T}test_omission_checks.py::test_each_omission_entry_fires_on_exactly_its_seeded_calls",
            f"{T}test_policy_checks.py::test_each_policy_entry_fires_on_exactly_its_seeded_calls",
            # The record and conduct families, and the two claim entries that
            # are not the completion claim. All four tests existed and passed
            # while this list omitted them, so the PASS this criterion printed
            # rested on the families somebody remembered to name -- 21 of 37
            # entries. `tests/test_rubric_coverage.py` is the mechanism that
            # makes remembering unnecessary; these lines are the claim it backs.
            f"{T}test_record_checks.py::test_each_record_entry_fires_on_exactly_its_seeded_calls",
            f"{T}test_conduct_checks.py::test_each_conduct_entry_fires_on_exactly_its_seeded_calls",
            f"{T}test_claim_checks.py::test_the_blocking_state_check_fires_on_exactly_the_seeded_calls",
            f"{T}test_claim_checks.py::test_the_terminal_retry_check_fires_on_exactly_the_seeded_calls",
            f"{T}test_rubric_coverage.py::test_every_rubric_entry_is_claimed_by_exactly_one_family",
            f"{T}test_platform_checks.py::test_every_traced_finding_resolves_to_a_findings_row",
            f"{T}test_platform_checks.py::"
            "test_every_traced_finding_is_one_a_deterministic_check_could_catch",
        ),
        caveat=(
            "What is not asserted is the coverage reported per severity band, which is a P5 "
            "deliverable, and whether the 37 signal lists are the right abstraction for the "
            "findings they trace, which no test can say."
        ),
    ),
    Criterion(
        "Every rubric entry names a design-set call the check must be silent on, or declares "
        "that none exists with a reason; and the check is asserted silent there. (D107 -- not a "
        "specification criterion.)",
        tests=(
            f"{T}test_claim_checks.py::"
            "test_every_entry_names_a_negative_instance_or_declares_it_has_none",
            f"{T}test_claim_checks.py::test_a_named_negative_instance_is_a_design_set_call",
            f"{T}test_claim_checks.py::"
            "test_the_check_ran_on_every_named_negative_instance_and_found_nothing",
        ),
    ),
)


def main(
    argv: list[str] | None = None,
    *,
    criteria: tuple[Criterion, ...] = CRITERIA,
    phase: int = 2,
    declared: tuple[Declared, ...] = (),
) -> int:
    """Report a phase's criteria against the suite, and its declarations beside them.

    Takes the criteria and the phase number so `tools/verify_phase3.py` can
    import this loop rather than keep a third copy of it. D113's argument for
    importing the suite runner applies with more force here: a third copy would
    be a third place for "EVIDENCE MISSING" to stop meaning the same thing, and
    the two that already exist have drifted in their closing lines.

    The defaults are phase 2's, so every existing caller is unchanged.

    `declared` lists the criteria a verifier claims without ticking (D176): each
    is printed under its own heading with its reason, and counted in the closing
    line by kind, never as a pass and never as a failure. No phase before 5 has
    any, so its default changes nothing for them.
    """
    parser = argparse.ArgumentParser(prog=f"verify_phase{phase}", description=__doc__)
    parser.add_argument(
        "--junit",
        default=None,
        help=(
            "read this JUnit report instead of running the suite. Ignored when the report "
            "is missing or older than the newest source file."
        ),
    )
    args = parser.parse_args(argv)
    results = load_suite_results(Path(args.junit) if args.junit else None)

    failures = 0
    caveats: list[tuple[int, str]] = []

    for number, criterion in enumerate(criteria, start=1):
        states: list[str] = []
        for node in criterion.tests:
            verdict = results.get(node)
            states.append("MISSING" if verdict is None else verdict)
        for command in criterion.commands:
            completed = subprocess.run(
                list(command), cwd=REPO_ROOT, capture_output=True, text=True, check=False
            )
            states.append("pass" if completed.returncode == 0 else "fail")

        if not states:
            verdict = "NO EVIDENCE"
        elif all(state == "pass" for state in states):
            verdict = "PASS"
        elif "MISSING" in states:
            verdict = "EVIDENCE MISSING"
        else:
            verdict = "FAIL"

        if verdict != "PASS":
            failures += 1
        mark = "OK " if verdict == "PASS" else "!! "
        print(f"{mark}{number:>2}. [{verdict}] {criterion.text}")
        for node in criterion.tests:
            print(f"        {results.get(node, 'MISSING'):>7}  {node}")
        for command in criterion.commands:
            printable = " ".join(str(part) for part in command).replace(sys.executable, "python")
            print(f"        {'ran':>7}  {printable}")
        if criterion.caveat:
            caveats.append((number, criterion.caveat))
        print()

    if caveats:
        print("=" * 78)
        print("NOT FULLY CHECKABLE BY MACHINE — read these rather than the ticks")
        print("=" * 78)
        for number, caveat in caveats:
            print(f"\n  {number}. {caveat}")
        print()

    # D176. Printed whatever the ticks above say, and counted neither way: a
    # declaration is not evidence, and it is not a failure of the phase either.
    if declared:
        print("=" * 78)
        print("DECLARED, NOT TICKED — asserted elsewhere, or not yet built")
        print("=" * 78)
        for declaration in declared:
            print(f"\n  [{declaration.kind}] {declaration.text}")
            print(f"    {declaration.reason}")
        print()

    print("=" * 78)
    if failures:
        print(f"PHASE {phase} NOT COMPLETE — {failures} of {len(criteria)} criteria did not pass")
        return 1

    from tools.verify_phase1 import _SUITE_EXIT, _SUITE_OUTPUT

    suite_exit = _SUITE_EXIT[-1] if _SUITE_EXIT else None
    if suite_exit:
        for line in diagnose_suite_exit(suite_exit, results):
            print(line.replace("PHASE 1", f"PHASE {phase}"))
        print((_SUITE_OUTPUT[-1] if _SUITE_OUTPUT else "").strip()[-700:])
        return 1

    anchored = sum(1 for criterion in criteria if criterion.spec_anchor)
    in_criteria = criteria_in_document(criteria, phase)
    in_requirements = anchored - in_criteria
    sentence = (
        f"All {len(criteria)} checks pass, each by running it — "
        f"{in_criteria} of them the specification's own [P{phase}] acceptance criteria"
    )
    if in_requirements:
        sentence += f", {in_requirements} its [P{phase}] requirement prose"
    print(sentence + ".")
    print(f"{len(caveats)} carry a stated caveat above; a tick is not a claim they do not.")
    elsewhere = sum(1 for declaration in declared if declaration.kind == ASSERTED_ELSEWHERE)
    pending = sum(1 for declaration in declared if declaration.kind == NOT_YET_BUILT)
    if elsewhere or pending:
        print(
            f"{len(declared)} more are declared and not ticked: {elsewhere} asserted "
            f"elsewhere, {pending} not yet built."
        )
    print("The suite as a whole passed too, not only the tests these criteria name.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
