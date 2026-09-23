"""The check registry, built explicitly.

`build_registry()` is the one list of what exists. Registration is not done by
decorator and not by import side effect: the rubric loader refuses an entry
naming an unregistered check, and that refusal is one of the four the
requirement enumerates. A registry populated by whichever modules happened to
be imported would make that refusal depend on import order -- something no
rubric author can see and no error message could explain.

Adding a check is two edits in one file: write it, and add its line here.
"""

from __future__ import annotations

from harness.checks.claims import (
    action_after_blocking_state,
    completion_claim_without_successful_write,
    repeated_after_terminal_status,
)
from harness.checks.conduct import (
    confirmation_requested_after_the_attempt,
    correction_never_issued,
    deadline_never_resolved,
    irreversible_action_without_confirmation,
    silence_exceeds_threshold,
    spoken_local_date_wrong,
    third_party_claim_answered_from_own_record,
    value_from_speech_used_without_readback,
    verification_claimed_on_mismatched_value,
)
from harness.checks.omission import (
    account_detail_disclosed_before_verification,
    available_topic_never_raised,
    available_value_never_spoken,
    configured_disclosure_not_delivered,
    declared_capability_not_invoked,
    handoff_without_context,
    protected_field_disclosed,
    write_to_unestablished_destination,
)
from harness.checks.platform import (
    declared_state_never_recorded,
    duration_does_not_reconcile,
    lifecycle_event_missing,
    outcome_contradicted_by_results,
    precondition_satisfied_by_assertion,
    reason_code_understates_completed_writes,
    reason_code_unsupported_by_results,
    system_ended_the_interaction,
    verification_absent_before_gated_write,
)
from harness.checks.policy import (
    governing_clause_not_applied,
    rule_stated_without_retrieval,
    tool_argument_contradicts_applied_clause,
)
from harness.checks.records import (
    amount_inconsistent_with_declared_band,
    record_fields_disagree,
    repeated_request_with_no_record,
    retry_without_deduplication,
    timestamp_ordering_violated,
)
from harness.core.registry import Registry


def build_registry() -> Registry:
    registry = Registry()
    registry.register(
        "completion_claim_without_successful_write", completion_claim_without_successful_write
    )
    registry.register("action_after_blocking_state", action_after_blocking_state)
    registry.register("repeated_after_terminal_status", repeated_after_terminal_status)
    registry.register("reason_code_unsupported_by_results", reason_code_unsupported_by_results)
    registry.register(
        "reason_code_understates_completed_writes", reason_code_understates_completed_writes
    )
    registry.register("outcome_contradicted_by_results", outcome_contradicted_by_results)
    registry.register("precondition_satisfied_by_assertion", precondition_satisfied_by_assertion)
    registry.register(
        "verification_absent_before_gated_write", verification_absent_before_gated_write
    )
    registry.register("declared_state_never_recorded", declared_state_never_recorded)
    registry.register("lifecycle_event_missing", lifecycle_event_missing)
    registry.register("duration_does_not_reconcile", duration_does_not_reconcile)
    registry.register("system_ended_the_interaction", system_ended_the_interaction)
    registry.register("available_value_never_spoken", available_value_never_spoken)
    registry.register("available_topic_never_raised", available_topic_never_raised)
    registry.register("declared_capability_not_invoked", declared_capability_not_invoked)
    registry.register("configured_disclosure_not_delivered", configured_disclosure_not_delivered)
    registry.register("protected_field_disclosed", protected_field_disclosed)
    registry.register(
        "account_detail_disclosed_before_verification",
        account_detail_disclosed_before_verification,
    )
    registry.register("handoff_without_context", handoff_without_context)
    registry.register("write_to_unestablished_destination", write_to_unestablished_destination)
    registry.register("governing_clause_not_applied", governing_clause_not_applied)
    registry.register("rule_stated_without_retrieval", rule_stated_without_retrieval)
    registry.register(
        "tool_argument_contradicts_applied_clause", tool_argument_contradicts_applied_clause
    )
    registry.register(
        "amount_inconsistent_with_declared_band", amount_inconsistent_with_declared_band
    )
    registry.register("record_fields_disagree", record_fields_disagree)
    registry.register("timestamp_ordering_violated", timestamp_ordering_violated)
    registry.register("repeated_request_with_no_record", repeated_request_with_no_record)
    registry.register("retry_without_deduplication", retry_without_deduplication)
    registry.register(
        "verification_claimed_on_mismatched_value", verification_claimed_on_mismatched_value
    )
    registry.register(
        "value_from_speech_used_without_readback", value_from_speech_used_without_readback
    )
    registry.register(
        "irreversible_action_without_confirmation", irreversible_action_without_confirmation
    )
    registry.register(
        "confirmation_requested_after_the_attempt", confirmation_requested_after_the_attempt
    )
    registry.register("silence_exceeds_threshold", silence_exceeds_threshold)
    registry.register("deadline_never_resolved", deadline_never_resolved)
    registry.register("correction_never_issued", correction_never_issued)
    registry.register(
        "third_party_claim_answered_from_own_record", third_party_claim_answered_from_own_record
    )
    registry.register("spoken_local_date_wrong", spoken_local_date_wrong)
    return registry
