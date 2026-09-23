"""What the system knew and the caller was never told, and what it told them anyway.

Two families that look opposite and share a shape: both compare something
present in the ground truth against the *absence* of something in speech.

Speech is still the subject here, not evidence. These checks read agent turns
to establish that a thing was **not** said, which is a property of the subject
under test; nothing about the world is taken from a spoken sentence. Caller
speech appears only as `stimulus` -- to establish that a trigger occurred, in
the two checks where the trigger is something the caller raised.

**W9 is closed in `protected_field_disclosed`.** The reference implementation's
paraphrase detector selected distinctive words by a bare length filter with no
stopword list, at an overlap threshold of two, so benign turns tripped a
critical gate -- and its validation measured only that the true positive
cleared the threshold, never the false-positive rate in the same call. The
stopword list and the threshold are rubric data here, and both rates are
measured over the whole design set.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any, Final

from harness.checks import matching
from harness.checks.values import MatchMode, cue_follows, figures_in, grounded
from harness.core.context import (
    CheckContext,
    FactSource,
    state_writes,
    tool_invocations,
)
from harness.core.events import DisclosureEvent, StateEvent
from harness.core.registry import ResultBuilder
from harness.core.result import Result
from harness.core.rubric import ParamView

_WORD = re.compile(r"[A-Za-z']{2,}")

_MATCH_MODES: Final[frozenset[str]] = frozenset({MatchMode.NUMERIC.value, "literal"})
"""How a source's value is compared against speech, declared per source.

`numeric` reads the payload as figures and compares decimals, so "eighty-five
dollars" grounds against `85.00`. `literal` compares the value's own surface at
a word boundary, for a value that is not a figure at all -- an email address.
An unknown value is refused by name rather than falling silently to one of
these, which is how the third mode would otherwise arrive unnoticed.

The numeric spelling is `MatchMode.NUMERIC.value` rather than the string, so a
rename of the enum member cannot leave this list agreeing with nothing. Only
`literal` is spelled out, because it names a comparison the value layer does
not make.

**`MatchMode.SUBSTRING` is deliberately not offered here.** It exists for a
figure-shaped identifier whose leading zeros are significant, and no shipped
source declares one; the single identifier-shaped value the rubric does carry
is an email address, whose terminal `.com` collides with that mode's
digit-and-separator boundary at a sentence end. Offering a mode nothing uses is
the defect this check was just repaired for.
"""


def _mapping(params: ParamView, key: str) -> Mapping[str, Any]:
    value = params[key]
    if not isinstance(value, Mapping) or not value:
        raise TypeError(f"{key!r} must be a non-empty mapping")
    return value


def _agent_text(context: CheckContext) -> str:
    return "\n".join(claim.text for claim in context.subject.agent_turns).casefold()


def _detail_values(context: CheckContext, key: str) -> list[tuple[int, str]]:
    """`(event index, value)` for every `key=value` in a tool result's detail."""
    found: list[tuple[int, str]] = []
    for invocation in tool_invocations(context.events):
        result = invocation.result
        if result is None or not result.detail:
            continue
        for value in matching.values(result.detail, key):
            found.append((result.index, value))
    return found


def available_value_never_spoken(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """A value the system had, that the caller needed, and nobody said out loud.

    CALL-09's exchange returns `difference_due=14.00`; the caller asks what it
    will cost at event 18 and again at event 22, and no agent turn contains
    that figure. CALL-11 sends to an address the context record holds and the
    agent refers to it as "the email address we have on file", never saying it.

    Spelled and digit forms are both searched, because speech spells its
    numbers and the form carries nothing (D111).

    **A figure with no declared cue near it is not a candidate**, which is the
    rest of D111's Rule and was stated there before it was built. Without it
    "One moment for me" contributes the value 1, and a `difference_due` of
    `1.00` reads as spoken on a check whose whole job is to find values that
    were not spoken -- W4's shape inside the module whose docstring says it
    closes W4. Over the design set the agent says thirty-four figures and
    twenty-seven carry no money cue, among them "fourteen" (the value of
    CALL-09's own payload, in two other calls), the ZIP `00461` read as 461,
    and two booking references read back digit by digit which compose to 19 and
    16. Adding the cue moved no verdict of 555, so the control is planted.
    """
    sources = _mapping(params, "sources")
    lexicon = {str(k): int(v) for k, v in _mapping(params, "number_words").items()}
    scales = {str(k): int(v) for k, v in _mapping(params, "number_scales").items()}
    joiners = [str(word) for word in params["number_joiners"]]
    digit_pattern = str(params["digit_pattern"])
    strip = [str(character) for character in params["strip_characters"]]

    cues = [str(cue) for cue in params["number_cues"]]
    window = int(params["cue_window_words"])

    spoken = _agent_text(context)
    # `_agent_text` folds the speech, so folding is the case policy of this
    # whole check rather than a per-source option; it is passed rather than
    # assumed so both sides of every comparison fold the same way (W7).
    said = tuple(
        figure
        for figure in figures_in(
            spoken,
            lexicon=lexicon,
            scales=scales,
            joiners=joiners,
            digit_pattern=digit_pattern,
            strip=strip,
        )
        if cue_follows(spoken, figure, cues=cues, window_words=window, fold_case=True) is not None
    )

    # Refused here rather than where the mode is used, so an entry declaring a
    # mode nothing implements fails on every call rather than only on the calls
    # whose facts happen to reach that source.
    modes = {}
    for name, source in sources.items():
        declared = str(source["match"])
        if declared not in _MATCH_MODES:
            raise TypeError(
                f"source {name!r} declares an unknown match {declared!r}; "
                f"the declared modes are {', '.join(sorted(_MATCH_MODES))}"
            )
        modes[name] = declared

    violations: list[str] = []
    considered = 0
    for name, source in sources.items():
        origin = str(source["from"])
        key = str(source["key"])
        required_signals = [str(signal) for signal in source.get("requires_speech_signals", [])]
        if required_signals and matching.signal_in(spoken, required_signals) is None:
            continue

        if origin == "context":
            value = context.ground_truth.context_value(key)
            candidates = [] if value is None else [("context", value)]
        elif origin == "result_detail":
            candidates = [
                (f"event {index}", value) for index, value in _detail_values(context, key)
            ]
        else:
            raise TypeError(f"source {name!r} declares an unknown origin {origin!r}")
        if not candidates:
            continue
        considered += 1

        for reference, value in candidates:
            if modes[name] == MatchMode.NUMERIC.value:
                # The payload is the facts and speech is the subject, so the
                # question `grounded` answers is the right way round: which of
                # the figures the agent said does this payload support.
                supported = {
                    figure.amount
                    for figure in said
                    if grounded(
                        figure.amount,
                        figure.surface,
                        value,
                        mode=MatchMode.NUMERIC,
                        corpus_pattern=digit_pattern,
                        strip=strip,
                        fold_case=True,
                    )
                }
                carried = figures_in(
                    value,
                    lexicon=lexicon,
                    scales=scales,
                    joiners=joiners,
                    digit_pattern=digit_pattern,
                    strip=strip,
                )
                if carried and all(figure.amount in supported for figure in carried):
                    continue
            elif matching.signal_in(spoken, [value]) is not None:
                continue
            violations.append(
                f"{reference} -- {key} is {value!r} and no agent turn in this call says it"
            )

    if not considered:
        return builder.not_applicable("no declared source is present in this call")
    if violations:
        return builder.violated(tuple(violations))
    return builder.satisfied()


def available_topic_never_raised(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """The facts raise a subject and no agent turn ever does.

    CALL-05's eligibility read names the remedy in its own payload and the
    context names the holder who could perform it; no agent turn mentions
    either. CALL-08's refusal names a conflict between two door times in as
    many words, and no agent turn mentions a conflict or a second value.
    """
    topics = _mapping(params, "topics")
    spoken = _agent_text(context)

    violations: list[str] = []
    considered = 0
    for topic in topics.values():
        present: str | None = None
        if "fact_key" in topic:
            value = context.ground_truth.context_value(str(topic["fact_key"]))
            wanted = topic.get("fact_value")
            if value is not None and (wanted is None or value == str(wanted)):
                present = f"context -- {topic['fact_key']} := {value}"
        else:
            needle = str(topic["fact_contains"]).casefold()
            for fact in context.ground_truth.facts:
                if fact.source is FactSource.EVENT and needle in fact.text.casefold():
                    present = f"{fact.reference} -- {fact.text[:90]}"
                    break
        if present is None:
            continue
        considered += 1

        if matching.signal_in(spoken, topic["speech_signals"]) is not None:
            continue
        violations.append(
            f"{present}, and no agent turn mentions {' / '.join(topic['speech_signals'])}"
        )

    if not considered:
        return builder.not_applicable("no declared topic is raised by the facts of this call")
    if violations:
        return builder.violated(tuple(violations))
    return builder.satisfied()


def declared_capability_not_invoked(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """A capability the system has, a trigger the caller raised, and no call to it.

    An absence can only be a finding against a list somebody wrote down, which
    is why the tool inventory is declared rather than inferred from whatever
    happens to appear in a transcript. The trigger comes from caller speech --
    its *occurrence*, which is a fact about the conversation, never its content
    as evidence about the world (D110).
    """
    capabilities = _mapping(params, "capabilities")
    heard = "\n".join(turn.text for turn in context.stimulus.turns).casefold()
    invoked = {invocation.name for invocation in tool_invocations(context.events)}

    violations: list[str] = []
    triggered = 0
    for name, capability in capabilities.items():
        hit = matching.signal_in(heard, capability["trigger_speech_signals"])
        if hit is None:
            continue
        triggered += 1
        tool = str(capability["tool"])
        if tool in invoked:
            continue
        violations.append(
            f"the caller raised {name!r} ({hit!r}) and {tool} is declared and never invoked"
        )

    if not triggered:
        return builder.not_applicable("no declared capability trigger occurs in this call")
    if violations:
        return builder.violated(tuple(violations))
    return builder.satisfied()


def configured_disclosure_not_delivered(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """The platform's record says a statement was configured; the log disagrees.

    Two failures, one shape. CALL-12 carries `disclosure_ai_status` and emits
    no `ai_status` event at all. CALL-11 carries the refund-timing template and
    delivers a sentence carrying neither the settlement period nor the fee
    statement -- an omission that originates in configuration and is invisible
    from the spoken transcript alone.
    """
    disclosures = _mapping(params, "disclosures")
    delivered = {
        event.name: event for event in context.events if isinstance(event, DisclosureEvent)
    }

    violations: list[str] = []
    configured = 0
    for name, declaration in disclosures.items():
        variable = str(declaration["context_variable"])
        template = context.ground_truth.context_value(variable)
        if template is None:
            continue
        configured += 1
        event = delivered.get(name)
        if event is None:
            violations.append(
                f"context -- {variable} is configured and no {name} DISCLOSURE event "
                "appears anywhere in this call"
            )
            continue
        spoken = (event.text or "").casefold()
        missing = [
            str(element)
            for element in declaration["required_elements"]
            if matching.signal_in(spoken, [element]) is None
        ]
        if missing:
            violations.append(
                f"event {event.index} -- {name} delivered without {', '.join(missing)}, "
                f"which the configured template states"
            )

    if not configured:
        return builder.not_applicable("no declared disclosure is configured in this call")
    if violations:
        return builder.violated(tuple(violations))
    return builder.satisfied()


def _distinctive(text: str, stopwords: set[str], minimum_length: int) -> set[str]:
    return {
        word
        for word in (match.group(0).casefold() for match in _WORD.finditer(text))
        if len(word) >= minimum_length and word not in stopwords
    }


def protected_field_disclosed(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """An operator-facing field whose substance reaches the caller.

    W9 is this check done badly: distinctive words chosen by a bare length
    filter with no stopword list, at a threshold of two, so benign turns
    tripped a critical gate -- and validated only against its true positive.
    The stopword list, the minimum word length and the threshold are all
    declared here, and both rates are measured over the design set.
    """
    fields = [str(name) for name in params["protected_fields"]]
    stopwords = {str(word).casefold() for word in params["stopwords"]}
    minimum_length = int(params["min_word_length"])
    threshold = int(params["overlap_threshold"])

    violations: list[str] = []
    present = 0
    for field in fields:
        value = context.ground_truth.context_value(field)
        if value is None:
            continue
        present += 1
        wanted = _distinctive(value, stopwords, minimum_length)
        for claim in context.subject.agent_turns:
            shared = wanted & _distinctive(claim.text, stopwords, minimum_length)
            if len(shared) >= threshold:
                violations.append(
                    f"{claim.reference} shares {len(shared)} distinctive word(s) with "
                    f"{field} ({', '.join(sorted(shared))})"
                )

    if not present:
        return builder.not_applicable("this call declares none of the protected fields")
    if violations:
        return builder.violated(tuple(violations))
    return builder.satisfied()


def _verified_at(context: CheckContext, tools: set[str], states: set[str]) -> int | None:
    earliest: int | None = None
    for invocation in tool_invocations(context.events):
        result = invocation.result
        if invocation.name in tools and result is not None and result.successful:
            earliest = result.index if earliest is None else min(earliest, result.index)
    for event in context.events:
        if isinstance(event, StateEvent) and event.name in states:
            earliest = event.index if earliest is None else min(earliest, event.index)
    return earliest


def account_detail_disclosed_before_verification(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """Account values spoken before anything established who is on the line.

    CALL-12 reads back the holder's name, the event and the full delivery
    address at event 11, while the write later in the call is gated on a
    verification that never happens. CALL-18 volunteers the card brand, its
    last four and the billing ZIP, unprompted, to a caller who is not the
    account holder.

    **`window` is why this is not simply "spoken before verification".** Under
    that reading the check fires on CALL-20, where the agent reads the holder
    name back at event 11 to confirm it has the right booking and verifies at
    event 13 -- an ordinary identification flow the gold set records no finding
    against. The defect the corpus seeds is disclosure in a call where
    verification never happens at all, so `unverified_call` is what the rubric
    declares; `before_verification` is the wider reading, kept because the
    mutation between them is what shows the narrowing was a decision.
    """
    fields = [str(name) for name in params["fields"]]
    tools = {str(tool) for tool in params["verification_tools"]}
    states = {str(name) for name in params["verification_states"]}
    window = str(params["window"])
    if window not in {"unverified_call", "before_verification"}:
        raise TypeError(f"window {window!r} is not one of 'unverified_call', 'before_verification'")

    verified_at = _verified_at(context, tools, states)
    if window == "unverified_call" and verified_at is not None:
        return builder.satisfied((f"event {verified_at} -- verification occurs in this call",))
    values = [
        (field, value)
        for field in fields
        if (value := context.ground_truth.context_value(field)) is not None
    ]
    if not values:
        return builder.not_applicable("this call declares none of the account fields")

    violations: list[str] = []
    for claim in context.subject.agent_turns:
        if claim.event_index is None:
            continue
        if verified_at is not None and claim.event_index > verified_at:
            continue
        spoken = claim.text.casefold()
        disclosed = sorted(field for field, value in values if value.casefold() in spoken)
        if disclosed:
            violations.append(
                f"{claim.reference} states {', '.join(disclosed)} and verification "
                + (f"does not occur until event {verified_at}" if verified_at else "never occurs")
            )

    if violations:
        return builder.violated(tuple(violations))
    return builder.satisfied()


def handoff_without_context(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """A call handed on carrying no account of why, and no reference linking it.

    The `summary` argument exists because a handoff that carries nothing is
    only expressible against a payload that was supposed to carry something:
    without the argument there is no defect to see, only an absence to argue
    about.
    """
    handoffs = _mapping(params, "handoffs")
    recorded = state_writes(context.events)

    violations: list[str] = []
    performed = 0
    for name, declaration in handoffs.items():
        tool = str(declaration["tool"])
        for invocation in tool_invocations(context.events):
            if invocation.name != tool:
                continue
            performed += 1
            for argument in declaration["required_nonempty_arguments"]:
                passed = matching.argument(invocation.call.arguments, str(argument))
                if passed is None or not passed.strip():
                    violations.append(
                        f"event {invocation.call.index} -- {tool} carries an empty "
                        f"{argument}, so the {name} handoff arrives with no account of why"
                    )
            for variable in declaration["required_state_after"]:
                # `after` is the parameter's own word, and it was not being
                # compared: a write anywhere in the call cleared the
                # requirement, including one recorded before the handoff was
                # made, which links nothing to the record the transfer opens.
                after = [
                    index
                    for index in recorded.get(str(variable), ())
                    if index > invocation.call.index
                ]
                if not after:
                    violations.append(
                        f"event {invocation.call.index} -- {tool} completed and "
                        f"{variable} is never written after it, so nothing links this call "
                        "to the record the specialist opens"
                    )

    if not performed:
        return builder.not_applicable("no declared handoff tool is invoked in this call")
    if violations:
        return builder.violated(tuple(violations))
    return builder.satisfied()


def write_to_unestablished_destination(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """A write sent somewhere the account record does not know about.

    CALL-18's confirmation goes to an address the caller supplied in the same
    turn; the account's own address is never used, mentioned or offered as an
    alternative.
    """
    destinations = _mapping(params, "destinations")

    violations: list[str] = []
    considered = 0
    for tool, declaration in destinations.items():
        argument = str(declaration["argument"])
        established = [
            value
            for key in declaration["established_context_keys"]
            if (value := context.ground_truth.context_value(str(key))) is not None
        ]
        if not established:
            continue
        for invocation in tool_invocations(context.events):
            if invocation.name != tool:
                continue
            destination = matching.argument(invocation.call.arguments, argument)
            if destination is None:
                continue
            considered += 1
            if destination.casefold() in {value.casefold() for value in established}:
                continue
            violations.append(
                f"event {invocation.call.index} -- {tool} sends to {destination!r} and "
                f"the account record holds {', '.join(established)}"
            )

    if not considered:
        return builder.not_applicable("no declared destination write occurs in this call")
    if violations:
        return builder.violated(tuple(violations))
    return builder.satisfied()
