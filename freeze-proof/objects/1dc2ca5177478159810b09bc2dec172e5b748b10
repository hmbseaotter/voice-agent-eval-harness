"""Claim integrity and ordering: what the agent said happened, against what did.

Four of the nine measured defects in a prior deterministic tier are here, and
each is closed by the shape of the check rather than by a comment.

**W2 -- ordering.** Claim integrity looked for a matching success *anywhere* in
the call, so it could not distinguish "announced completion after the tool
returned" from "announced completion before the tool was invoked". CALL-09 is
the corpus's worked example of the second: the agent says "I've moved you
across to the June date" at event 12, the exchange is not attempted until event
15, and it eventually succeeds at event 20. The outcome is fine and the
ordering is the defect. Support is therefore counted only from results whose
index is **below** the claim's.

**W3 -- resolution.** A claim mapped to several candidate actions and resolved
them by disjunction, so two similarly-named actions with one success and one
failure produced a false pass on an absolute gate. A topic here declares its
action tools, and when more than one of them was actually invoked the check
returns `unevaluable` naming the ambiguity. Resolve to a single action or
refuse; never disjoin.

**W4 -- precision.** The claim detector matched confirmation questions: "are
you all set?" read as a completion claim, failing a gate where no matching
action existed. Signals are phrases rather than words and an entry declares
excluded signals, because the corpus contains "you have fourteen days from when
the tickets were **issued**" and "the twenty-two dollars was taken when you
**booked**" -- past-tense references that a word list would fire on. The
false-positive rate is measured over the whole design set, not only asserted
absent on one call.

**W10 -- later resolution.** The unresolved-precondition correlation ignored
ordering and later resolution: a variable set, later re-set, then used
successfully still reported a violation. `action_after_blocking_state` reads
the **latest** value of the variable before the invocation, so a state that was
cleared before use is not a violation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from harness.checks import matching
from harness.core.context import CheckContext, tool_invocations
from harness.core.registry import ResultBuilder
from harness.core.result import Result
from harness.core.rubric import ParamView


def _fold(text: str, fold_case: bool) -> str:
    return text.casefold() if fold_case else text


def _topics(params: ParamView) -> Mapping[str, Mapping[str, Any]]:
    topics = params["topics"]
    if not isinstance(topics, Mapping) or not topics:
        raise TypeError("'topics' must be a non-empty mapping of topic name to its signals")
    return topics


def _matching_signal(text: str, topic: Mapping[str, Any], fold_case: bool) -> str | None:
    """The claim signal this turn carries, if the turn is a claim at all.

    An excluded signal wins over a claim signal, so "are you all set?" cannot be
    rescued by also containing "all set". Checking exclusions first is the whole
    of W4's fix at this level; the measured false-positive rate is the rest.
    """
    if matching.signal_in(text, topic["excluded_signals"], fold_case) is not None:
        return None
    return matching.signal_in(text, topic["claim_signals"], fold_case)


def completion_claim_without_successful_write(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """An agent turn claiming an action, with no successful write behind it.

    "Behind" is meant in the ordering sense: a result that arrived after the
    claim did not support it when it was made.
    """
    topics = _topics(params)
    success_statuses = {str(status) for status in params["success_statuses"]}
    require_before = bool(params["require_result_before_claim"])
    fold_case = bool(params["fold_case"])

    invocations = tool_invocations(context.events)
    invoked = {invocation.name for invocation in invocations}

    violations: list[str] = []
    refusals: list[tuple[str, str]] = []
    claims_found = 0

    for claim in context.subject.agent_turns:
        text = _fold(claim.text, fold_case)
        for topic_name, topic in topics.items():
            signal = _matching_signal(text, topic, fold_case)
            if signal is None:
                continue
            claims_found += 1

            tools = [str(tool) for tool in topic["action_tools"]]
            candidates = sorted(name for name in tools if name in invoked)
            if len(candidates) > 1:
                # W3. Two similarly-named actions, one succeeding and one
                # failing, is the shape that produced a false pass; refusing is
                # the only answer that is not a guess.
                #
                # **The topic is refused, not the call.** Returning here
                # discarded every violation the other topics had already
                # produced: CALL-01 loses a real `confirmation` finding because
                # `exchange` is ambiguous, and the two have nothing to do with
                # each other.
                refusals.append(
                    (
                        f"topic:{topic_name}",
                        f"{claim.reference} claims {topic_name!r} and {len(candidates)} of its "
                        f"declared action tools were invoked ({', '.join(candidates)}). A claim "
                        "resolving to more than one action is refused rather than disjoined.",
                    )
                )
                continue

            supporting = [
                invocation
                for invocation in invocations
                if invocation.name in tools
                and invocation.result is not None
                and invocation.result.status.value in success_statuses
                and invocation.result.successful
                and (
                    not require_before
                    or (
                        claim.event_index is not None
                        and invocation.result.index < claim.event_index
                    )
                )
            ]
            if not supporting:
                violations.append(
                    f"{claim.reference} claims {topic_name!r} ({signal!r}) and no "
                    + (
                        f"{', '.join(tools)} result before it carries "
                        f"{'/'.join(sorted(success_statuses))} with successful=true"
                        if require_before
                        else f"{', '.join(tools)} result carries "
                        f"{'/'.join(sorted(success_statuses))} with successful=true"
                    )
                )

    if not claims_found:
        return builder.not_applicable("no agent turn carries a declared completion signal")
    if violations:
        # D114's precedence, one level down: evidence actually computed outranks
        # a neighbor that could not be. The refusal is carried in the evidence
        # rather than in `missing_ground_truth`, which answers "why is there no
        # verdict here" and does not apply to a result that has one.
        return builder.violated(tuple(violations) + tuple(detail for _, detail in refusals))
    if refusals:
        return builder.unevaluable(*refusals[0])
    return builder.satisfied()


def _latest_state_before(context: CheckContext, name: str, index: int) -> tuple[str, int] | None:
    """The last value this state variable was set to before `index`.

    W10 is what reading the *first* value costs: a variable set, later re-set,
    then used successfully still reported a violation.
    """
    latest: tuple[str, int] | None = None
    for event in context.events:
        if event.index >= index:
            break
        fact_name = getattr(event, "name", None)
        value = getattr(event, "value", None)
        if fact_name == name and isinstance(value, str):
            latest = (value, event.index)
    return latest


def action_after_blocking_state(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """A write attempted while the state the platform recorded said it could not.

    Eligibility is the content of a read, not the status of a write: a prior
    read reported that the action was not permitted and the platform recorded
    it, and the agent invoked the tool anyway.
    """
    gates = params["gates"]
    if not isinstance(gates, Mapping) or not gates:
        raise TypeError("'gates' must be a non-empty mapping of gate name to its declaration")
    fold_case = bool(params["fold_case"])

    violations: list[str] = []
    considered = 0

    for invocation in tool_invocations(context.events):
        for gate_name, gate in gates.items():
            blocked: Sequence[str] = [str(tool) for tool in gate["blocked_tools"]]
            if invocation.name not in blocked:
                continue
            state_name = str(gate["blocking_state"])
            blocking_value = _fold(str(gate["blocking_value"]), fold_case)
            latest = _latest_state_before(context, state_name, invocation.call.index)
            if latest is None:
                continue
            considered += 1
            value, at_index = latest
            if _fold(value, fold_case) == blocking_value:
                violations.append(
                    f"event {at_index} set {state_name} := {value}, and "
                    f"event {invocation.call.index} invoked {invocation.name} "
                    f"({gate_name}) with no intervening change"
                )

    if not considered:
        return builder.not_applicable(
            "no declared gate variable was set before a declared blocked tool was invoked"
        )
    if violations:
        return builder.violated(tuple(violations))
    return builder.satisfied()


def _arguments_key(arguments: str, ignore: Sequence[str], fold_case: bool) -> str:
    """An invocation's arguments with the declared keys removed.

    So "the identical call" means identical apart from the arguments an entry
    says do not make it a different request -- which is how a retry carrying a
    deduplication key is told from one that is not.
    """
    parts = [part.strip() for part in arguments.split(",")]
    kept = [part for part in parts if not any(part.startswith(f"{key!s}=") for key in ignore)]
    return _fold(", ".join(kept), fold_case)


def repeated_after_terminal_status(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """The same request re-issued after a status that says nothing will change.

    `refused_ineligible` is defined as a hard rule refusing, which no further
    input changes. Re-issuing the identical call is not a retry, it is the
    absence of an error taxonomy -- the causal pattern behind fabricated
    completion, with nothing separating a fixable precondition from hard
    ineligibility from environmental unavailability.
    """
    terminal = {str(status) for status in params["terminal_statuses"]}
    ignore_arguments = [str(key) for key in params["ignore_arguments"]]
    fold_case = bool(params["fold_case"])

    violations: list[str] = []
    seen: dict[tuple[str, str], tuple[int, str]] = {}
    refusals = 0

    for invocation in tool_invocations(context.events):
        key = (
            invocation.name,
            _arguments_key(invocation.call.arguments, ignore_arguments, fold_case),
        )
        previous = seen.get(key)
        if previous is not None:
            at_index, status = previous
            violations.append(
                f"event {at_index} returned {status} for {invocation.name}, and event "
                f"{invocation.call.index} issued the identical request again"
            )
        if invocation.result is not None and invocation.result.status.value in terminal:
            refusals += 1
            seen[key] = (invocation.result.index, invocation.result.status.value)

    if not refusals:
        return builder.not_applicable(
            f"no result in this call carries a declared terminal status "
            f"({'/'.join(sorted(terminal))})"
        )
    if violations:
        return builder.violated(tuple(violations))
    return builder.satisfied()
