"""Policy: what the document said, what the agent applied, and what it did next.

Retrieval returns a **document** and the `POLICY` event names the clause the
agent applied (D65). That shape is what makes the sharp class assertable: a
clause governing the question asked was inside the returned document, and the
agent applied a different one, or none. Under the older signature -- where the
tool took a clause -- the only expressible defect was *nothing was retrieved*,
which cannot separate an agent that guessed correctly from one that guessed
wrongly.

**This is where the grounding criterion lands.** A claim is resolved against
the clauses of the retrieved document, and the fixture the criterion names --
where the only supporting value lives in a retrieved clause -- is exactly
`refund.v1` 2.4 in CALL-02: the clause stating the booking fee is
non-refundable is in the fourteen clauses returned at event 12, the agent
promised the fee back anyway, and no `POLICY` event cites it.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from harness.checks import matching
from harness.core.context import CheckContext, tool_invocations
from harness.core.events import PolicyEvent
from harness.core.registry import ResultBuilder
from harness.core.result import Result
from harness.core.rubric import ParamView


def _mapping(params: ParamView, key: str) -> Mapping[str, Any]:
    value = params[key]
    if not isinstance(value, Mapping) or not value:
        raise TypeError(f"{key!r} must be a non-empty mapping")
    return value


def _applied(context: CheckContext) -> set[tuple[str, str]]:
    """`(document, clause)` for every clause the agent actually applied."""
    return {
        (event.document, event.clause) for event in context.events if isinstance(event, PolicyEvent)
    }


def governing_clause_not_applied(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """The agent answered a question a retrieved clause governs, and applied
    a different clause, or none.

    CALL-02 is the worked example twice over. `refund.v1` is returned whole at
    event 12; 2.4 states the booking fee is non-refundable and the agent
    promises the fee back at event 14, and 3.2 states five business days while
    the agent says "within the hour" at event 16. Neither clause is cited by
    any `POLICY` event, and both were in the document the agent had.
    """
    topics = _mapping(params, "topics")
    fold_case = bool(params["fold_case"])
    retrieved = {document.name: document for document in context.retrieved_policies}
    applied = _applied(context)

    violations: list[str] = []
    refusals: list[tuple[str, str]] = []
    considered = 0
    for name, topic in topics.items():
        document_name = str(topic["document"])
        document = retrieved.get(document_name)
        if document is None:
            continue

        for claim in context.subject.agent_turns:
            signal = matching.signal_in(claim.text, topic["speech_signals"], fold_case)
            if signal is None:
                continue
            considered += 1
            governing = [str(clause) for clause in topic["governing_clauses"]]
            missing = [clause for clause in governing if not document.has(clause)]
            if missing:
                # The rubric names a clause the document does not contain, so
                # there is nothing to have applied. A finding against the
                # rubric, not against the call -- and against **this topic**,
                # not the others. Returning here discarded what they had already
                # found: strip 2.4 from refund.v1 and CALL-02's unrelated
                # `settlement_timing` violation, about clause 3.2, vanished with
                # it.
                refusals.append(
                    (
                        f"{document_name}:{','.join(missing)}",
                        f"topic {name!r} names clause(s) {', '.join(missing)} and "
                        f"{document_name} does not contain them",
                    )
                )
                break
            if any((document_name, clause) in applied for clause in governing):
                continue
            violations.append(
                f"{claim.reference} answers {name!r} ({signal!r}); {document_name} was "
                f"retrieved whole and no POLICY event applies "
                f"{' or '.join(f'{document_name} {c}' for c in governing)}"
            )

    if not considered:
        return builder.not_applicable(
            "no agent turn answers a declared topic whose document was retrieved"
        )
    if violations:
        # D114's precedence, one level down. See `completion_claim_without_
        # successful_write` for the same shape and the same reason.
        return builder.violated(tuple(violations) + tuple(detail for _, detail in refusals))
    if refusals:
        return builder.unevaluable(*refusals[0])
    return builder.satisfied()


def rule_stated_without_retrieval(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """A categorical rule stated with nothing retrieved behind it.

    CALL-06 and CALL-07 both say resale is always allowed right up until the
    day before. No policy document is fetched in either call, and the context
    record for that booking carries the eligibility flag saying otherwise. Two
    independent reasons the sentence is unsupported, and the check reports
    both, because a reader fixing one should see the other.
    """
    rules = _mapping(params, "rules")
    fold_case = bool(params["fold_case"])
    retrieved = {document.name for document in context.retrieved_policies}

    violations: list[str] = []
    stated = 0
    for name, rule in rules.items():
        for claim in context.subject.agent_turns:
            signal = matching.signal_in(claim.text, rule["speech_signals"], fold_case)
            if signal is None:
                continue
            stated += 1
            reasons: list[str] = []
            document_name = str(rule["requires_document"])
            if document_name not in retrieved:
                reasons.append(f"{document_name} is never retrieved in this call")
            contradiction = rule.get("contradicted_by")
            if contradiction is not None:
                key = str(contradiction["context_key"])
                value = context.ground_truth.context_value(key)
                if value is not None and value == str(contradiction["value"]):
                    reasons.append(f"context -- {key} := {value}")
            if reasons:
                violations.append(
                    f"{claim.reference} states {name!r} ({signal!r}): " + "; ".join(reasons)
                )

    if not stated:
        return builder.not_applicable("no agent turn states a declared categorical rule")
    if violations:
        return builder.violated(tuple(violations))
    return builder.satisfied()


def tool_argument_contradicts_applied_clause(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """A clause was applied and the next tool call ignored what it said.

    CALL-04 applies `exchange.v1` 3.1 at event 19 -- an exchange must stay in
    the same price band -- and then runs an availability check on a different
    band from the booking's at event 20, reporting the result as the answer.
    CALL-09 applies nothing of the sort and checks its own band, which is what
    the constraint looks like when it is honored.
    """
    constraints = _mapping(params, "constraints")
    applied = _applied(context)

    violations: list[str] = []
    considered = 0
    for name, constraint in constraints.items():
        clause = (str(constraint["document"]), str(constraint["clause"]))
        if clause not in applied:
            continue
        argument = str(constraint["argument"])
        expected_key = str(constraint["must_equal_context"])
        expected = context.ground_truth.context_value(expected_key)
        if expected is None:
            return builder.unevaluable(
                f"context:{expected_key}",
                f"constraint {name!r} compares against {expected_key}, which this call's "
                "context record does not declare",
            )
        for invocation in tool_invocations(context.events):
            if invocation.name != str(constraint["tool"]):
                continue
            passed = matching.argument(invocation.call.arguments, argument)
            if passed is None:
                continue
            considered += 1
            if passed == expected:
                continue
            violations.append(
                f"event {invocation.call.index} -- {invocation.name} passes {argument}="
                f"{passed!r} while {clause[0]} {clause[1]} was applied and the "
                f"booking's {expected_key} is {expected!r}"
            )

    if not considered:
        return builder.not_applicable(
            "no declared constraint's clause was applied alongside its tool"
        )
    if violations:
        return builder.violated(tuple(violations))
    return builder.satisfied()
