"""Platform-owned defects: dispositions, gates, state and lifecycle.

Every check here compares one part of the system's own record against another
part of it. **No agent speech is read at all** -- these are the findings whose
`owner` is `platform`, and they are visible from the event log and the call
record alone. That is worth stating rather than leaving to be noticed: the
family exists because a defect the agent cannot be blamed for still has to be
detectable, and a check that reached for a spoken confirmation to decide
whether a gate held would be asking the subject under test to certify itself.

The disposition labels are the artifact under test. `duration_ms`,
`disconnection_reason`, `outcome` and `outcome_reason` are what the platform
*claimed*, and a harness that reconciled them on read would delete the defect
it exists to detect -- so they arrive in `Subject`, and what they are compared
against arrives in `GroundTruth`.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from harness.checks import matching
from harness.core.context import CheckContext, state_writes, tool_invocations
from harness.core.events import SystemEvent
from harness.core.registry import ResultBuilder
from harness.core.result import Result
from harness.core.rubric import ParamView


def _mapping(params: ParamView, key: str) -> Mapping[str, Any]:
    value = params[key]
    if not isinstance(value, Mapping) or not value:
        raise TypeError(f"{key!r} must be a non-empty mapping")
    return value


def _completed_tools(context: CheckContext, statuses: set[str]) -> dict[str, int]:
    """Tool name to the index of its first result carrying a declared success.

    Success is the *declared* flag alongside a declared status, never derived
    from one: platforms carry both, and a result whose `successful` disagrees
    with its status is a data-integrity defect the model must be able to
    represent.
    """
    completed: dict[str, int] = {}
    for invocation in tool_invocations(context.events):
        result = invocation.result
        if result is None or not result.successful or result.status.value not in statuses:
            continue
        completed.setdefault(invocation.name, result.index)
    return completed


def _state_names(context: CheckContext) -> Mapping[str, tuple[int, ...]]:
    """Every write of every state variable. See `context.state_writes`."""
    return state_writes(context.events)


def reason_code_unsupported_by_results(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """The call's own reason code names an action no result carries out.

    CALL-01 is filed `exchange_completed` and its two successful results are
    both reads. A disposition label derived from something other than the tool
    results is a metric wrong by at least this call, with nothing indicating
    it.
    """
    reason_codes = _mapping(params, "reason_codes")
    statuses = {str(status) for status in params["success_statuses"]}

    reason = context.subject.disposition("outcome_reason")
    if reason is None or reason not in reason_codes:
        return builder.not_applicable(
            f"outcome_reason {reason!r} declares no required action in this entry"
        )
    required = [str(tool) for tool in reason_codes[reason]["requires_tools"]]
    completed = _completed_tools(context, statuses)
    supporting = sorted(tool for tool in required if tool in completed)
    if supporting:
        return builder.satisfied(
            tuple(f"event {completed[tool]} -- {tool} completed" for tool in supporting)
        )
    return builder.violated(
        (
            f"call -- outcome_reason {reason}",
            f"no result in this call carries {'/'.join(sorted(statuses))} with "
            f"successful=true for {', '.join(required)}",
        )
    )


def reason_code_understates_completed_writes(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """Two distinct accountable actions completed, and one reason code for both.

    CALL-03 corrects a holder name at event 17 and transfers the booking at
    event 26, both `completed successful=true`, and files one reason code. A
    reason code is a closed vocabulary somebody counts, so a call doing two
    things and reporting one is a count that is wrong by construction.

    `accountable_write_tools` is what makes this stateable without firing on
    every call that also sends a confirmation: a notification is not a second
    action, and CALL-11 completes a refund and a send while being exactly one
    thing happening.
    """
    accountable = {str(tool) for tool in params["accountable_write_tools"]}
    statuses = {str(status) for status in params["success_statuses"]}
    reason_codes = _mapping(params, "reason_codes")

    completed = _completed_tools(context, statuses)
    performed = sorted(tool for tool in completed if tool in accountable)
    if len(performed) < 2:
        return builder.not_applicable(
            f"{len(performed)} accountable write(s) completed, so one reason code covers it"
        )

    reason = context.subject.disposition("outcome_reason")
    named: set[str] = (
        {str(tool) for tool in reason_codes[reason]["requires_tools"]}
        if reason is not None and reason in reason_codes
        else set()
    )
    unaccounted = sorted(tool for tool in performed if tool not in named)
    if not unaccounted:
        # Every accountable action the call performed is named by its reason
        # code. `<= 1` was the first draft and it was wrong: CALL-03's reason
        # code names the transfer and leaves the holder-name correction
        # unaccounted, which is one unnamed action and is exactly F-73.
        return builder.satisfied(
            tuple(f"event {completed[tool]} -- {tool} completed" for tool in performed)
        )
    return builder.violated(
        (
            f"call -- outcome_reason {reason}",
            *(f"event {completed[tool]} -- {tool} completed" for tool in performed),
            f"{len(performed)} accountable actions completed and the reason code names "
            f"{', '.join(sorted(named)) or 'none'}",
        )
    )


def outcome_contradicted_by_results(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """An outcome saying nothing was accomplished, over results that accomplished it.

    CALL-18 is filed `abandoned`. The booking was retrieved, the confirmation
    was sent, and the send returned `successful=true` before the caller thanked
    the agent and hung up.
    """
    outcomes = _mapping(params, "outcomes")
    statuses = {str(status) for status in params["success_statuses"]}

    outcome = context.subject.disposition("outcome")
    if outcome is None or outcome not in outcomes:
        return builder.not_applicable(f"outcome {outcome!r} is unconstrained by this entry")

    forbidden = {str(tool) for tool in outcomes[outcome]["forbids_completed_tools"]}
    completed = _completed_tools(context, statuses)
    offending = sorted(tool for tool in completed if tool in forbidden)
    if not offending:
        return builder.satisfied()
    return builder.violated(
        (
            f"call -- outcome {outcome}",
            *(f"event {completed[tool]} -- {tool} completed" for tool in offending),
        )
    )


def precondition_satisfied_by_assertion(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """A refused precondition met on the retry by an argument asserting it.

    CALL-03's transfer is refused for want of a read-back and re-issued with
    `readback_confirmed="true"`; CALL-12's send is refused with
    `caller_verified=false` and re-issued with `assume_verified="true"`. In
    neither call does any state event record that the precondition was
    actually met. The orchestration accepted an assertion in place of a state,
    which makes the gate advisory for anything that knows the argument's name.
    """
    assertions = _mapping(params, "assertions")
    recorded = _state_names(context)

    violations: list[str] = []
    considered = 0
    for invocation in tool_invocations(context.events):
        for argument, declaration in assertions.items():
            if not matching.carries_argument(invocation.call.arguments, argument):
                continue
            considered += 1
            variables = [str(name) for name in declaration["state_variables"]]
            # Before the invocation, not anywhere in the call. The finding is
            # that an argument asserting a precondition stood in for a state
            # recording it, and a state written *after* the gate was passed did
            # not establish anything at the moment the gate was passed -- the
            # assertion still did the work. A state written before it means the
            # precondition genuinely held and the argument merely restates it.
            if any(
                index < invocation.call.index
                for name in variables
                for index in recorded.get(name, ())
            ):
                continue
            violations.append(
                f"event {invocation.call.index} -- {invocation.name} carries {argument}, and "
                f"no STATE event before it sets {' or '.join(variables)}"
            )

    if not considered:
        return builder.not_applicable("no invocation carries a declared asserting argument")
    if violations:
        return builder.violated(tuple(violations))
    return builder.satisfied()


def verification_absent_before_gated_write(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """A gated write completed with no verification anywhere before it.

    The comparison that makes this a finding rather than an impression is
    within one call: the write completed, and neither a verification tool nor a
    verification state exists below its index. A compliance property that holds
    because each flow happens to be configured correctly is not a property of
    the system.
    """
    gated = {str(tool) for tool in params["gated_tools"]}
    verification_tools = {str(tool) for tool in params["verification_tools"]}
    verification_states = {str(name) for name in params["verification_states"]}
    statuses = {str(status) for status in params["success_statuses"]}

    completed = _completed_tools(context, statuses)
    writes = {tool: index for tool, index in completed.items() if tool in gated}
    if not writes:
        return builder.not_applicable("no declared gated write completed in this call")

    verified_at = [index for tool, index in completed.items() if tool in verification_tools]
    # Every write, not the last one: a verification recorded before the write
    # and refreshed after it read as no verification below the write, which is
    # a false violation on an absolute gate.
    verified_at += [
        index
        for name, indices in _state_names(context).items()
        if name in verification_states
        for index in indices
    ]

    violations = [
        f"event {index} -- {tool} completed with no verification below it"
        for tool, index in sorted(writes.items())
        if not any(at < index for at in verified_at)
    ]
    if violations:
        return builder.violated(tuple(violations))
    return builder.satisfied()


def declared_state_never_recorded(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """A variable the platform maintains, which the call never updates.

    A variable declared in the context record is one the platform maintains. If
    it should have changed during the call and did not, that is a platform
    defect and it is assertable -- and it is only *sayable* because the context
    record and the state stream are separate records.
    """
    variables = [str(name) for name in params["variables"]]
    recorded = _state_names(context)

    declared = [name for name in variables if context.ground_truth.context_value(name) is not None]
    if not declared:
        return builder.not_applicable("the context record declares none of this entry's variables")

    missing = [name for name in declared if name not in recorded]
    if not missing:
        # The first write of each, because the evidence answers "was it ever
        # updated in this call" and the first update is the one that answers it.
        return builder.satisfied(
            tuple(f"event {min(recorded[name])} -- {name} set" for name in declared)
        )
    return builder.violated(
        tuple(
            f"context -- {name} := "
            f"{context.ground_truth.context_value(name)}, and no STATE event sets it"
            for name in missing
        )
    )


def lifecycle_event_missing(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """A call with no end-of-interaction event in its own stream.

    Inconsistent lifecycle emission is the condition under which real failures
    go unlogged: any metric counting completed interactions is wrong by at
    least this call, and nothing indicates it. The header's
    `disconnection_reason` is not corroboration -- it is the same claim from
    the same source.
    """
    required = [str(name) for name in params["required_system_events"]]
    present = {event.name for event in context.events if isinstance(event, SystemEvent)}
    missing = [name for name in required if name not in present]
    if not missing:
        return builder.satisfied()
    return builder.violated(
        (
            f"no {' or '.join(missing)} SYSTEM event appears anywhere in this call",
            f"call -- disconnection_reason {context.subject.disposition('disconnection_reason')}",
        )
    )


def duration_does_not_reconcile(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """The reported duration against the call's own event timeline.

    `duration_ms` is as the platform reports it and is never recomputed -- but
    it is comparable against the last event's end offset, and a header that
    disagrees with the stream beneath it is a data defect either way round.
    """
    tolerance = int(params["tolerance_ms"])
    reported_raw = context.subject.disposition("duration_ms")
    if reported_raw is None:
        return builder.not_applicable("the call record carries no duration")
    reported = int(reported_raw)
    # An event with no end offset cannot say when the stream ended (event model
    # v3, D203), and dropping it would reconcile the header against a stream
    # shorter than the call.
    ends = [event.ended_at_ms for event in context.events]
    timed = [end for end in ends if end is not None]
    if len(timed) != len(ends):
        return builder.unevaluable(
            "event timing",
            f"{len(ends) - len(timed)} event(s) carry no end offset, so the stream has no "
            "last moment to reconcile the reported duration against",
        )
    last = max(timed, default=0)
    drift = abs(reported - last)
    if drift <= tolerance:
        return builder.satisfied()
    return builder.violated(
        (
            f"call -- duration_ms {reported}",
            f"the last event ends at {last}ms, a difference of {drift}ms against a "
            f"declared tolerance of {tolerance}ms",
        )
    )


def system_ended_the_interaction(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """The system hung up rather than leaving the ending to the caller.

    On a voice channel the party who hangs up is itself a signal, and a system
    that ends promptly removes the moment in which a caller raises the thing
    they were working up to. It also corrupts the disposition: a call the
    system ended reads in any dashboard like a caller who was finished.
    """
    reasons = {str(reason) for reason in params["system_ended_reasons"]}
    reported = context.subject.disposition("disconnection_reason")
    if reported is None:
        return builder.not_applicable("the call record carries no disconnection reason")
    if reported not in reasons:
        return builder.satisfied()
    return builder.violated((f"call -- disconnection_reason {reported}",))
