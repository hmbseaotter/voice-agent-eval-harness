"""Records against themselves: amounts, fields, timestamps and repeated asks.

The `owner: data` findings live here, plus the two agent-side ones about asking
again for something the system already had. What they share is that the
comparison is between two things the platform holds, and speech enters only to
locate the request under test.

**Which tool returned the record matters, and running the checks is what
showed it.** A naive comparison of the context record against any tool result
carrying `door_time` fires on CALL-01 and CALL-09, where `find_performance`
returns a *different* performance and a different door time is the whole point
of the call. `fetch_event_details` returns the same event by id, so a
disagreement there is a contradiction. The tools are declared per entry for
exactly that reason.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from typing import Any

from harness.checks import matching
from harness.core.context import CheckContext, state_writes, tool_invocations
from harness.core.registry import ResultBuilder
from harness.core.result import Result
from harness.core.rubric import ParamView


def _mapping(params: ParamView, key: str) -> Mapping[str, Any]:
    value = params[key]
    if not isinstance(value, Mapping) or not value:
        raise TypeError(f"{key!r} must be a non-empty mapping")
    return value


def amount_inconsistent_with_declared_band(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """A write for an amount the band the platform recorded does not allow.

    CALL-02 executes a refund for the full ticket price plus the fee while the
    context record declares `refund_band := partial_50`. The orchestration
    applied no check that the requested amount was consistent with the band it
    had already determined -- and the band is in the record, so the check needs
    no judgment about what the caller was owed.
    """
    bands = _mapping(params, "bands")
    band_variable = str(params["band_variable"])
    tool = str(params["tool"])
    argument = str(params["argument"])
    tolerance = Decimal(str(params["tolerance"]))

    band = context.ground_truth.context_value(band_variable)
    if band is None:
        return builder.not_applicable(f"this call declares no {band_variable}")
    if band not in bands:
        return builder.unevaluable(
            f"band:{band}",
            f"{band_variable} is {band!r} and this entry declares no fraction for it",
        )

    declaration = bands[band]
    base_key = str(declaration["of"])
    base_raw = context.ground_truth.context_value(base_key)
    if base_raw is None:
        return builder.unevaluable(
            f"context:{base_key}", f"the band is declared against {base_key}, which this call lacks"
        )
    try:
        expected = Decimal(base_raw) * Decimal(str(declaration["fraction"]))
    except InvalidOperation:
        return builder.unevaluable(
            f"context:{base_key}", f"{base_key} is {base_raw!r}, which is not a number"
        )

    violations: list[str] = []
    considered = 0
    for invocation in tool_invocations(context.events):
        if invocation.name != tool:
            continue
        raw = matching.argument(invocation.call.arguments, argument)
        if raw is None:
            continue
        try:
            amount = Decimal(raw)
        except InvalidOperation:
            continue
        considered += 1
        if abs(amount - expected) <= tolerance:
            continue
        violations.append(
            f"context -- {band_variable} := {band} over {base_key} {base_raw} allows "
            f"{expected}, and event {invocation.call.index} requests {amount}"
        )

    if not considered:
        return builder.not_applicable(f"no {tool} call in this call carries an {argument}")
    if violations:
        return builder.violated(tuple(violations))
    return builder.satisfied()


def record_fields_disagree(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """Two records describing one thing, and disagreeing about it.

    CALL-08 holds one production under two names and one event under two door
    times, from two different record sources. The agent had both and could not
    have answered the caller's question correctly from the data it was given,
    whatever it said -- which is why the owner is `data` and no speech is read.
    """
    tools = {str(tool) for tool in params["tools"]}
    fields = _mapping(params, "fields")

    violations: list[str] = []
    compared = 0
    for invocation in tool_invocations(context.events):
        if invocation.name not in tools:
            continue
        result = invocation.result
        if result is None or not result.detail:
            continue
        for detail_key, context_key in fields.items():
            returned = matching.field(result.detail, str(detail_key))
            held = context.ground_truth.context_value(str(context_key))
            if returned is None or held is None:
                continue
            compared += 1
            if returned == held:
                continue
            violations.append(
                f"event {result.index} returns {detail_key}={returned!r} and the context "
                f"record holds {context_key} := {held}"
            )

    if not compared:
        return builder.not_applicable(
            "no declared tool returned a field this entry compares against the context"
        )
    if violations:
        return builder.violated(tuple(violations))
    return builder.satisfied()


def _instant(value: str) -> dt.datetime | None:
    """One timestamp as a point in time, or `None` if it cannot be read as one.

    The format spec calls a timestamp opaque, and comparing two of them as
    *strings* quietly assumes it is not: lexicographic order agrees with
    chronological order only while both share a format and an offset.
    `2027-04-24T02:30:00Z` and `2027-04-23T19:30:00-07:00` are the same instant
    and sort the wrong way round, so one payload mixing offsets produces a
    violation on an absolute gate that never happened -- or hides one that did.
    """
    try:
        return dt.datetime.fromisoformat(value)
    except ValueError:
        return None


def timestamp_ordering_violated(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """Two timestamps in one payload, in an order that cannot have happened.

    CALL-19's event record says the reschedule was made four days *after* the
    door time it rescheduled the event to. Either the timestamp or the door
    time is wrong, and nothing in the record says which -- which is the finding,
    rather than a claim about which one to fix.

    **Compared as instants, and reported as unevaluable when they cannot be.**
    A value that does not parse, or a pair mixing an offset-aware timestamp with
    a naive one, has no ordering to assert -- so the check says the corpus gave
    it nothing to judge rather than guessing, which is the distinction W11 cost
    this project once already.
    """
    orderings = _mapping(params, "orderings")

    violations: list[str] = []
    unreadable: list[tuple[str, str]] = []
    compared = 0
    for invocation in tool_invocations(context.events):
        result = invocation.result
        if result is None or not result.detail:
            continue
        for name, ordering in orderings.items():
            earlier_key, later_key = str(ordering["earlier"]), str(ordering["later"])
            earlier = matching.field(result.detail, earlier_key)
            later = matching.field(result.detail, later_key)
            if earlier is None or later is None:
                continue
            compared += 1
            first, second = _instant(earlier), _instant(later)
            if first is None or second is None:
                missing = earlier_key if first is None else later_key
                unreadable.append(
                    (
                        f"event {result.index}:{missing}",
                        f"event {result.index} -- {name}: {missing} is "
                        f"{earlier if first is None else later!r}, which is not a timestamp",
                    )
                )
                continue
            if (first.tzinfo is None) != (second.tzinfo is None):
                unreadable.append(
                    (
                        f"event {result.index}:{earlier_key}",
                        f"event {result.index} -- {name}: {earlier_key} is {earlier} and "
                        f"{later_key} is {later}; one carries an offset and the other does "
                        "not, so they name no comparable pair of instants",
                    )
                )
                continue
            if first <= second:
                continue
            violations.append(
                f"event {result.index} -- {name}: {earlier_key} is {earlier} and "
                f"{later_key} is {later}, which is earlier"
            )

    if not compared:
        return builder.not_applicable("no result carries both halves of a declared ordering")
    if violations:
        # A violation outranks an unreadable neighbor, on D114's reasoning: an
        # ordering that was actually computed is evidence, and discarding it
        # because a different pair could not be read would lose the finding to
        # report the corpus defect beside it. The unreadable pair is still named
        # in the evidence.
        return builder.violated(tuple(violations) + tuple(detail for _, detail in unreadable))
    if unreadable:
        reference, detail = unreadable[0]
        return builder.unevaluable(reference, detail)
    return builder.satisfied()


def repeated_request_with_no_record(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """Asking again for something the call already has.

    Two shapes, both in CALL-12. The booking reference is supplied, used
    successfully by `lookup_booking`, and requested again with no event in
    between that lost or invalidated it. And the holder question is asked, is
    answered, and is asked again with **no event of any kind between the two**
    -- no state event records the first answer, and this call emits no state
    event at all.

    Order is the whole check for the first shape: CALL-20 asks for the booking
    reference *before* looking it up, which is the same sentence doing its job.
    """
    requests = _mapping(params, "requests")
    fold_case = bool(params["fold_case"])
    recorded = state_writes(context.events)

    violations: list[str] = []
    asked = 0
    for name, request in requests.items():
        turns = [
            claim
            for claim in context.subject.agent_turns
            if matching.signal_in(claim.text, request["request_signals"], fold_case) is not None
        ]
        if not turns:
            continue
        asked += 1

        supplied = request.get("already_supplied_by_tool")
        if supplied is not None:
            tool, argument = str(supplied["tool"]), str(supplied["argument"])
            used_at = [
                invocation.call.index
                for invocation in tool_invocations(context.events)
                if invocation.name == tool
                and invocation.succeeded
                and (matching.argument(invocation.call.arguments, argument) or "").strip()
            ]
            for claim in turns:
                if claim.event_index is None:
                    continue
                earlier = [index for index in used_at if index < claim.event_index]
                if earlier:
                    violations.append(
                        f"{claim.reference} asks for {name!r}, and event {min(earlier)} had "
                        f"already used it successfully via {tool}"
                    )

        variable = request.get("repeated_without_state")
        if variable is not None and len(turns) > 1:
            first, last = turns[0], turns[-1]
            if first.event_index is None or last.event_index is None:
                continue
            # Every write of the variable, not the last one. A variable set
            # between the two asks and set again after the last ask answered
            # the first question, and a comprehension keeping only the final
            # index reported it as never set between them.
            between = [
                index
                for index in recorded.get(str(variable), ())
                if first.event_index < index < last.event_index
            ]
            if not between:
                violations.append(
                    f"{first.reference} and {last.reference} both ask for {name!r}, and no "
                    f"STATE event sets {variable} between them"
                )

    if not asked:
        return builder.not_applicable("no agent turn carries a declared request signal")
    if violations:
        return builder.violated(tuple(violations))
    return builder.satisfied()


def retry_without_deduplication(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """An identical write re-issued after the one status that cannot say what happened.

    A timed-out write is the one case where nobody can tell whether the action
    occurred, and it is the case where retrying without a deduplication key
    risks doing it twice. In CALL-05 the money did not move, so the harm is
    latent rather than realized -- which is why the finding is `tier: question`
    and this entry cannot fail a run. What the row does not claim, and this
    check does not either: that a duplicate occurred, or that the backend has
    no guard of its own.
    """
    retriable = {str(status) for status in params["retriable_statuses"]}
    dedup = [str(name) for name in params["deduplication_arguments"]]
    tools = {str(tool) for tool in params["tools"]}

    violations: list[str] = []
    inconclusive = 0
    pending: dict[tuple[str, str], tuple[int, str]] = {}
    for invocation in tool_invocations(context.events):
        if invocation.name not in tools:
            continue
        key = (invocation.name, invocation.call.arguments)
        previous = pending.get(key)
        if previous is not None:
            at, status = previous
            carried = [name for name in dedup if matching.argument(invocation.call.arguments, name)]
            if not carried:
                violations.append(
                    f"event {at} returned {status}, and event {invocation.call.index} re-issued "
                    f"the identical request carrying none of {', '.join(dedup)}"
                )
        result = invocation.result
        if result is not None and result.status.value in retriable:
            inconclusive += 1
            pending[key] = (result.index, result.status.value)

    if not inconclusive:
        return builder.not_applicable(
            f"no result in this call carries a status that cannot say whether the write "
            f"happened ({'/'.join(sorted(retriable))})"
        )
    if violations:
        return builder.violated(tuple(violations))
    return builder.satisfied()
