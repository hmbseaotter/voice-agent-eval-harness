#!/usr/bin/env python3
"""Run every phase-6 acceptance criterion that is built, and declare the rest.

    uv run python -m tools.verify_phase6

Run as a **module**, for D113's reason, and through the phase-2 loop rather than a
sixth copy of it.

**Written while its phase is open**, as phase 5's was (D176), and on the owner's
decision at this phase's contract reading (D201). Phase 6 is built across more
than one session: what spends nothing was built first, and the two deliverables
that need a live model call -- prompt caching and judge-model comparison -- are
left to a session briefed for them, with the design document beside them. Their
criteria are **declared not yet built** rather than left to read `NO EVIDENCE`,
so the list below is bound to the specification from the phase's first day and a
criterion added later cannot go unclaimed.

A declaration is printed under its own heading, never counted as a pass and never
as a failure, and the binding test refuses one naming a criterion an entry also
claims, so a declaration cannot outlive the build that replaces it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from tools.verify_phase1 import NOT_YET_BUILT, Criterion, Declared
from tools.verify_phase2 import main as _phase_main

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]

T: Final[str] = "tests/"

CRITERIA: Final[tuple[Criterion, ...]] = (
    Criterion(
        "For every design call, the second adapter's event stream equals the text adapter's "
        "with the adapter's declared gaps applied.",
        tests=(
            f"{T}test_retell_adapter.py::"
            "test_every_design_calls_retell_stream_differs_from_the_text_stream_only_where_declared",
            f"{T}test_retell_adapter.py::"
            "test_the_stream_comparison_would_notice_a_gap_filled_or_a_difference_undeclared",
            f"{T}test_retell_adapter.py::"
            "test_the_gap_check_would_notice_a_stream_and_a_declaration_that_disagree",
            f"{T}test_retell_adapter.py::"
            "test_a_retell_artifact_names_its_adapter_and_its_gaps_and_a_text_one_names_neither",
        ),
        commands=(("uv", "run", "python", "-m", "tools.make_retell_documents", "--check"),),
        caveat=(
            "The source documents are generated from the design transcripts, so the comparison "
            "shows the adapter and the text adapter agree on what Retell's documented shape can "
            "carry; it cannot show the adapter reads a log Retell itself produced, because no "
            "real vendor log is in this tree, by rule. Whether the documented shape was read "
            "correctly rests on the field table the documents are held to, and that table was "
            "typed from the documentation by one session on one day (D203)."
        ),
        spec_anchor="the second adapter's event stream equals the text adapter's",
    ),
    Criterion(
        "An unmapped value aborts naming it, a missing success flag is refused, a changed word "
        "reaches the stream, the documents use only documented fields and equal their "
        "regeneration, and the engine refuses a call that declares a gap.",
        tests=(
            f"{T}test_retell_adapter.py::"
            "test_the_adapter_would_notice_a_value_outside_its_declared_mapping",
            f"{T}test_retell_adapter.py::"
            "test_the_adapter_would_notice_a_tool_result_with_no_success_flag",
            f"{T}test_retell_adapter.py::test_the_adapter_reads_the_document_it_is_given",
            f"{T}test_retell_adapter.py::"
            "test_every_committed_retell_document_uses_only_documented_fields",
            f"{T}test_retell_adapter.py::"
            "test_the_documented_field_check_would_notice_a_field_nobody_documented",
            f"{T}test_retell_adapter.py::"
            "test_the_committed_retell_documents_match_their_regeneration",
            f"{T}test_retell_adapter.py::test_the_regeneration_check_would_notice_a_stale_document",
            f"{T}test_retell_adapter.py::"
            "test_build_context_would_notice_a_call_that_declares_a_gap",
            f"{T}test_retell_adapter.py::"
            "test_a_timing_check_would_notice_an_absent_time_read_as_a_number",
        ),
        caveat=(
            "The refusal at the shared seam is what stands in for checks that read a declared "
            "gap, and none does: a call from the second adapter can be extracted and cannot be "
            "evaluated, so nothing here shows a verdict over a vendor's log (D203)."
        ),
        spec_anchor="outside the second adapter's declared mapping aborts naming the value",
    ),
    Criterion(
        "The log inspector runs over a completed run log and emits its invariant metrics, "
        "including the proportion of retry triggers whose cited identifier exists.",
        tests=(
            f"{T}test_inspector.py::test_the_committed_reference_log_measures_what_is_recorded",
            f"{T}test_inspector.py::test_a_sound_log_reads_clean_on_every_invariant",
            f"{T}test_inspector.py::"
            "test_the_retry_metric_would_notice_a_validator_rejecting_what_its_prompt_rendered",
            f"{T}test_inspector.py::"
            "test_the_retry_metric_would_notice_an_identifier_shown_and_not_citable",
            f"{T}test_inspector.py::test_the_integrity_metrics_would_notice_each_kind_of_damage",
            f"{T}test_inspector.py::"
            "test_the_repetition_metrics_would_notice_a_gap_and_a_second_retry",
        ),
        commands=(("uv", "run", "harness", "inspect"),),
        caveat=(
            "A citable line is read from the logged prompt by one rule, that it begins with its "
            "tag. A prompt template that rendered citable lines another way would be measured "
            "wrongly and nothing here would say so (D205)."
        ),
        spec_anchor="The log inspector runs over a completed run log",
    ),
    Criterion(
        "Every value the inspector emits is a count or a proportion with both its terms, and "
        "its exit code never depends on what was measured.",
        tests=(
            f"{T}test_inspector.py::"
            "test_every_value_the_inspector_emits_is_a_count_or_a_proportion_with_both_its_terms",
            f"{T}test_inspector.py::test_the_inspector_refuses_only_a_file_it_cannot_read",
        ),
        caveat=(
            "That no metric line reads as a judgment is held by a list of words the test looks "
            "for. A score spelled some other way would pass it; the types are what cannot: a "
            "metric has two integers and no field for a verdict (D205)."
        ),
        spec_anchor="Every value the log inspector emits is a count",
    ),
    Criterion(
        "`harness severity` prints a band for every instance of the design set, computed in "
        "code, monotone in its properties, per instance, and refusing a declaration that does "
        "not describe the rubric.",
        tests=(
            f"{T}test_instance_severity.py::test_no_property_turning_true_lowers_a_band",
            f"{T}test_instance_severity.py::"
            "test_one_entry_receives_different_bands_on_two_calls_that_differ_in_what_happened",
            f"{T}test_instance_severity.py::test_what_happened_is_read_from_the_evidence_point_on",
            f"{T}test_instance_severity.py::"
            "test_the_shipped_properties_describe_exactly_the_shipped_rubric",
            f"{T}test_instance_severity.py::"
            "test_the_properties_check_would_notice_an_entry_undeclared_and_a_declaration_orphaned",
            f"{T}test_instance_severity.py::"
            "test_harness_severity_prints_a_band_for_every_instance_of_the_design_set",
        ),
        caveat=(
            "What kind of harm each entry means is declared by one session and reviewed by its "
            "owner, not measured, and the table against the ranked bands is printed and gates "
            "nothing: on the design set the two agree loosely, and nothing here says how loosely "
            "is acceptable. A judged instance and a defect of an absence are read from the start "
            "of the call, which over-attributes a write that completed before them (D206)."
        ),
        spec_anchor="`harness severity` prints a band for every instance in the design set",
    ),
    Criterion(
        "The README states which license covers which tree, and links the severity tool.",
        tests=(
            f"{T}test_phase6_acceptance.py::"
            "test_the_readme_names_a_license_for_every_top_level_path",
            f"{T}test_phase6_acceptance.py::"
            "test_the_license_check_would_notice_a_path_the_readme_does_not_name",
            f"{T}test_phase6_acceptance.py::test_the_readme_links_the_severity_tool",
        ),
        caveat=(
            "Top-level paths are read from the working tree less what `.gitignore` names, so the "
            "check runs without git; a tracked path an ignore pattern also matches is not read. "
            "`sessions/` is declared under neither license, which is a decision not yet taken "
            "rather than a tick."
        ),
        spec_anchor="The README states which license covers which tree",
    ),
)

DECLARED: Final[tuple[Declared, ...]] = (
    Declared(
        "Judge-model comparison reports per-model agreement against the gold set for every "
        "named candidate.",
        spec_anchor="Judge-model comparison reports per-model agreement against the gold set",
        kind=NOT_YET_BUILT,
        reason=(
            "Needs a live model call for each candidate, and is left to a session briefed for "
            "it under D152's and D161's rule: the expected cost printed beside the most it can "
            "cost, and approval before the first call (D201)."
        ),
    ),
    Declared(
        "Every candidate's run log names one rubric hash and one prompt-template hash, and a "
        "comparison across logs naming different ones is refused.",
        spec_anchor="Every candidate's run log names one rubric hash",
        kind=NOT_YET_BUILT,
        reason=(
            "Assertable on recorded logs with no model call, and built with the comparison it "
            "constrains, which does not exist yet (D201)."
        ),
    ),
    Declared(
        "Judge-model comparison states the tracing convention beside every figure and orders no "
        "candidate by its false alarms.",
        spec_anchor="Judge-model comparison states beside every figure",
        kind=NOT_YET_BUILT,
        reason="A property of the comparison's report, which does not exist yet (D202).",
    ),
    Declared(
        "With prompt caching enabled, the second repetition of a dimension on a call reports "
        "cache-read tokens exceeding its system message's own.",
        spec_anchor="the second repetition of a dimension on a given call reports cache-read",
        kind=NOT_YET_BUILT,
        reason=(
            "Reads a live response's usage, so it needs a live model call, and is left to a "
            "session briefed for it (D204)."
        ),
    ),
    Declared(
        "With prompt caching enabled, two repetitions' requests are byte-identical through the "
        "last cache breakpoint and every request's hash is unchanged.",
        spec_anchor="byte-identical through the last cache breakpoint",
        kind=NOT_YET_BUILT,
        reason=(
            "Needs no model call, and is built with the caching it describes, so that where the "
            "breakpoint sits is decided once and by the session that sends it (D204)."
        ),
    ),
    Declared(
        "The design document exists under `specs/` and carries its named parts.",
        spec_anchor="The design document exists under `specs/`",
        kind=NOT_YET_BUILT,
        reason=(
            "Written from the decision records by a session of its own, on the owner's decision "
            "at this phase's contract reading (D200, D201)."
        ),
    ),
)


def main(argv: list[str] | None = None) -> int:
    """The phase-2 reporting loop, over this phase's criteria and its declarations."""
    return _phase_main(argv, criteria=CRITERIA, phase=6, declared=DECLARED)


if __name__ == "__main__":
    raise SystemExit(main())
