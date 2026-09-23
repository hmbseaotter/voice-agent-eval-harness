"""Rendering a judge prompt: two tagged populations, one untrusted block.

The rule this module exists to hold is W1's fix, and it is one sentence: **a
validator must validate against the same universe the prompt renders.** So
rendering does not return a string. It returns the rendered messages *and* the
citable universe that was rendered into them, together, from one pass -- there
is no way to render a transcript and then ask a second function what could be
cited, because that second function is where the two drift apart.

**Two populations, numbered independently.** `[T<n>]` for speech, `[F<n>]` for
established facts (`specs/event-model.md` §3.4). Numbered independently means
`[T3]` and `[F3]` are different things and both may exist, and the validator
therefore checks each against its own set rather than against the union --
which is the difference between catching a fabricated `[F9]` on a call with
twelve turns and waving it through.

**Speech appears in exactly one place.** The security requirement is that no
raw caller or agent speech is spliced into a judge prompt outside the delimited
untrusted block. That is structural here rather than reviewed: the facts
sections render `Fact` values, and `GroundTruth` is built by `build_context`
from the fact-population events only -- a `SpeechEvent` returns `None` from
`_event_fact` and never becomes a `Fact` at all. The transcript block is the
only renderer that reads `Claim.text`.

**A fact category the entry names and nothing renders is an abort.** Not an
omission. An entry asking for `state_writes` and silently getting a prompt with
no state in it is a judge answering a different question from the one the
rubric declared, and the run would report its verdict as though it had been
asked properly.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final

from harness.core.context import CheckContext, Fact, FactSource

#: Splits the template into the two messages. Everything above becomes the
#: system prompt and everything below becomes the user message, which is what
#: puts every instruction in one message and only data in the other.
SYSTEM_BOUNDARY: Final[str] = "<!-- END SYSTEM -->"

#: The placeholder syntax. Doubled braces rather than `str.format`, because a
#: judge prompt contains JSON braces and a scale written with them, and a
#: formatter that treated those as fields would fail on the template this
#: project actually wants to write.
_PLACEHOLDER: Final[re.Pattern[str]] = re.compile(r"\{\{([A-Z_]+)\}\}")

#: HTML comment blocks. Stripped from what is sent, and therefore out of the
#: hash too, which covers the sent halves: a comment cannot change a response,
#: so hashing one refuses a replay for an edit that could not have altered it.
_COMMENT: Final[re.Pattern[str]] = re.compile(r"<!--.*?-->", re.DOTALL)

#: What a named-but-empty fact category renders as. An explicit negative
#: statement rather than an empty list, because a heading with nothing under it
#: reads as an oversight and invites the model to supply the missing content
#: from its own knowledge -- which is precisely the fabrication the fact
#: population exists to prevent.
EMPTY_CATEGORY_STATEMENT: Final[str] = (
    "None. This call established no facts of this kind. That is a fact about the "
    "call, not an omission from this prompt: do not supply any from your own "
    "knowledge, and do not treat the absence as permission to assume."
)

#: Rendered when an entry names no fact category at all. Never reached, because
#: the section is omitted entirely in that case -- kept as the assertion that
#: "omitted entirely" and "empty" are different renderings of different states.
NO_FACTS_SECTION: Final[str] = ""

#: Section headings that belong to one kind of judged entry and are removed from
#: the rendered half for the other. Named here rather than written at the call
#: site, so the template and the renderer cannot come to disagree about which
#: headings exist -- and `test_every_droppable_section_exists_in_the_template`
#: fails when one is renamed in the file and not here.
#:
#: One scaffold rather than two, which is `_drop_section`'s own argument: two
#: templates are two things that can disagree, and the run log carries one
#: prompt-template hash.
SYNTHESIS_ONLY_SECTIONS: Final[tuple[str, ...]] = (
    "# Your answer, and the dimensions it rests on",
    "# Dimension results for this call",
)

#: The section a synthesis entry does not get, because it has its own.
DIMENSION_ONLY_SECTIONS: Final[tuple[str, ...]] = ("# Your answer",)


class PromptError(Exception):
    """Base for every refusal to render a prompt."""


class UnknownFactCategoryError(PromptError):
    """An entry named a fact category no renderer knows.

    Aborts naming the category rather than omitting it, because the alternative
    is a judge answering without the evidence its rubric entry declared it
    needed, and reporting a verdict that looks exactly like a considered one.
    """

    def __init__(self, entry_id: str, category: str, known: Sequence[str]) -> None:
        super().__init__(
            f"rubric entry {entry_id!r}: requires_facts names {category!r}, which is not a "
            f"known fact renderer. Known: {', '.join(known) or '(none)'}. Refused rather "
            "than omitted -- a judge asked without the facts its entry declared is "
            "answering a different question."
        )
        self.entry_id = entry_id
        self.category = category


class TemplateError(PromptError):
    """A template that cannot be rendered as written."""


@dataclass(frozen=True, slots=True)
class PromptTemplate:
    """The scaffold, and the hash that makes a run log falsifiable.

    Frozen and carrying its own hash, so the value that goes into the run-log
    header and the value that renders the prompt cannot be two different
    things. A hash computed separately from the text it describes is a hash
    that will one day describe a file nobody sent.
    """

    text: str

    @property
    def sha256(self) -> str:
        """A hash of what is SENT, not of the file that produced it.

        The first version hashed `self.text` -- the whole file, comments
        included -- on the reasoning that a change to a template's stated
        reasoning is worth forcing a reader to look at the log again. That
        reasoning is about documentation review, and this hash is not for
        documentation review.

        **What the staleness check is for** is D8's sentence: a committed run
        log goes stale the moment a prompt template changes, and would then
        report a fossil that *quietly disagrees with live behavior*. A comment
        cannot change live behavior -- comments are stripped before rendering
        and no model sees them -- so a comment edit invalidating every recorded
        log is a refusal with nothing behind it. The cost is real and was paid
        once: a one-word spelling fix in this file's own prose would have
        discarded a full recorded run.

        So the hash covers the two rendered halves. Editing the instruction
        hierarchy, the citation rules or the answer shape still moves it,
        because those are sent. Editing the comment that explains why they are
        shaped that way does not.
        """
        system, user = self._halves()
        return hashlib.sha256(f"{system}\n{SYSTEM_BOUNDARY}\n{user}".encode()).hexdigest()

    @property
    def system_half(self) -> str:
        return self._halves()[0]

    @property
    def user_half(self) -> str:
        return self._halves()[1]

    def _halves(self) -> tuple[str, str]:
        if self.text.count(SYSTEM_BOUNDARY) != 1:
            raise TemplateError(
                f"the template must contain exactly one {SYSTEM_BOUNDARY!r} line, and this "
                f"one contains {self.text.count(SYSTEM_BOUNDARY)}. The boundary is what puts "
                "every instruction in the system message and only data in the user message; "
                "a template without it would render the whole hierarchy beside the "
                "transcript with nothing to say so, and one carrying it twice would split "
                "at the wrong place."
            )
        head, tail = self.text.split(SYSTEM_BOUNDARY, 1)
        return _strip_comments(head), _strip_comments(tail)

    @property
    def placeholders(self) -> frozenset[str]:
        """The placeholders the model will actually be shown.

        Read from the halves rather than from the raw text, for the same reason
        the halves strip comments: a maintainer note *mentioning* `{{FACTS}}`
        is documentation, and counting it would make the renderer demand a
        value for a placeholder nobody is going to send.
        """
        return frozenset(_PLACEHOLDER.findall(self.system_half + self.user_half))


def _strip_comments(half: str) -> str:
    """Remove HTML comment blocks, which are notes to a maintainer.

    **What is hashed is what is sent, and this is stripped before both.** The
    first version hashed the whole file, on the reasoning that a change to a
    template's stated reasoning is worth forcing a reader to look at the log
    again. That reasoning is about documentation review, and this hash is not
    for documentation review: D8's staleness check exists because a fossil log
    *quietly disagrees with live behavior*, and a comment cannot change
    behavior. Hashing one discards a recorded run for an edit that could not
    have altered a single response -- which it then did, over a one-word
    spelling fix in the template's own prose.

    Comments do not belong in the prompt either: they cost input tokens on
    every call, and they address a maintainer in a message the model is told is
    authoritative.

    It also has to go for a duller reason. A comment explaining the
    `{{FACTS}}` placeholder *contains* that placeholder, so the renderer would
    demand a value for a token that is documentation -- D89's constraint, that
    a document explaining a checker cannot contain the checker's own trigger,
    arriving in a prompt template. The first draft of the shipped template
    tripped exactly that.
    """
    return _COMMENT.sub("", half).strip()


def load_template(path: Path) -> PromptTemplate:
    """Read a template from disk. The one place a template comes from."""
    return PromptTemplate(text=path.read_text(encoding="utf-8"))


@dataclass(frozen=True, slots=True)
class CitableUniverse:
    """Exactly what the rendered prompt offered, by population.

    Returned *with* the rendered text rather than derivable from it. W1 is the
    version where a validator checked against a universe assembled separately
    from the one the prompt showed the model, and every fabricated citation
    that happened to fall inside the wider set was accepted.
    """

    transcript: Mapping[str, str]
    facts: Mapping[str, str]
    """Identifier to the text rendered beside it, in rendered order. The text
    is carried because a judged result's evidence quotes the line rather than
    naming it: `[T14] agent: ...` is auditable by reading, and a bare `T14`
    sends the reader back to re-render the prompt to find out what they are
    looking at."""

    @property
    def all_identifiers(self) -> frozenset[str]:
        return frozenset(self.transcript) | frozenset(self.facts)

    def text_of(self, identifier: str) -> str | None:
        """The line an identifier was rendered as, or `None` if it was not."""
        if identifier in self.transcript:
            return self.transcript[identifier]
        return self.facts.get(identifier)

    def population_of(self, identifier: str) -> str | None:
        """Which set an identifier belongs to by syntax, or `None`.

        Syntax rather than membership: `[F9]` on a call with two facts belongs
        to the fact population and is invalid, and calling it "unknown" would
        lose the distinction between a citation of the wrong kind and one that
        simply does not exist.
        """
        if identifier.startswith("T"):
            return "transcript"
        if identifier.startswith("F"):
            return "facts"
        return None


@dataclass(frozen=True, slots=True)
class SynthesisInput:
    """What the synthesis entry is given that a dimension is not.

    `results` is one pre-rendered line per dimension result for this call, and
    `entry_ids` is the set a `rests_on` identifier is validated against. The
    two travel together for the reason `RenderedPrompt` carries its own citable
    universe: a validator that reconstructed the valid set separately from what
    was rendered is W1, one population over.
    """

    results: tuple[str, ...]
    entry_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RenderedPrompt:
    """What the transport is given, and what the validator is held to."""

    system: str
    user: str
    citable: CitableUniverse
    template_hash: str

    rests_on: tuple[str, ...] = ()
    """Dimension identifiers this prompt listed as available to rest on. Empty
    for every entry that is not the synthesis, which is what makes "a `rests_on`
    identifier that produced no result" a question with an answer rather than a
    comparison against nothing."""


#: One fact renderer per category an entry may name. Explicit, like the check
#: registry and for the same reason: a category set that varied with import
#: order would make `UnknownFactCategoryError` fire or not fire according to
#: something no rubric author can see.
#:
#: Each renderer selects from `GroundTruth`, which cannot contain speech. That
#: is what makes "no raw speech outside the untrusted block" a property of the
#: type rather than of every renderer being written carefully.
FactRenderer = Callable[[CheckContext], tuple[Fact, ...]]

FACT_RENDERERS: Final[Mapping[str, FactRenderer]] = {
    "policy_clauses": lambda context: context.ground_truth.of_source(FactSource.POLICY_CLAUSE),
    "context_record": lambda context: context.ground_truth.of_source(FactSource.CONTEXT),
    "tool_events": lambda context: context.ground_truth.of_source(FactSource.EVENT),
    "call_record": lambda context: context.ground_truth.of_source(FactSource.CALL_RECORD),
}


def known_fact_categories() -> tuple[str, ...]:
    """Sorted, so a refusal message reads the same on every machine."""
    return tuple(sorted(FACT_RENDERERS))


def absent_categories(
    context: CheckContext, categories: Sequence[str], *, entry_id: str
) -> tuple[str, ...]:
    """Which of `categories` this call renders nothing for, in the order named.

    The named function behind D125's precondition. The engine calls it rather
    than asking `FACT_RENDERERS` itself, for the reason D121 gives about
    controls: a caller that re-implemented "did this category yield anything"
    beside the renderer would be measuring its own copy of the rule, and the
    two would drift the first time a renderer changed what it selects.

    **An unknown category aborts here too**, and it has to: this runs before
    the prompt is rendered, so leaving the refusal to `render_facts` would let
    a dimension with a misspelled precondition category silently apply to every
    call -- which is the state the precondition exists to end.
    """
    for category in categories:
        if category not in FACT_RENDERERS:
            raise UnknownFactCategoryError(entry_id, category, known_fact_categories())
    return tuple(category for category in categories if not FACT_RENDERERS[category](context))


def render_facts(
    context: CheckContext, categories: Sequence[str], *, entry_id: str
) -> tuple[str, Mapping[str, str]]:
    """The facts section and the `[F<n>]` identifiers it offered.

    Three behaviors the requirement distinguishes, and this returns a different
    thing for each:

    * **no category named** -- the section is omitted entirely, and the caller
      is told so by an empty body;
    * **a category named that yields nothing** -- an explicit negative
      statement, never a heading over nothing;
    * **a category named that nothing renders** -- an abort naming it.

    Numbering runs across all named categories in the order the entry names
    them, so `[F1]` is stable for a given entry and call.
    """
    for category in categories:
        if category not in FACT_RENDERERS:
            raise UnknownFactCategoryError(entry_id, category, known_fact_categories())

    if not categories:
        return NO_FACTS_SECTION, MappingProxyType({})

    lines: list[str] = []
    rendered: dict[str, str] = {}
    index = 0
    for category in categories:
        facts = FACT_RENDERERS[category](context)
        lines.append(f"### {category}")
        if not facts:
            lines.append(EMPTY_CATEGORY_STATEMENT)
            lines.append("")
            continue
        for fact in facts:
            index += 1
            identifier = f"F{index}"
            line = f"[{identifier}] ({fact.reference}) {fact.text}"
            rendered[identifier] = line
            lines.append(line)
        lines.append("")
    return "\n".join(lines).strip(), MappingProxyType(rendered)


def render_transcript(context: CheckContext) -> tuple[str, Mapping[str, str]]:
    """The untrusted block's body and the `[T<n>]` identifiers it offered.

    Every speech turn in stream order, caller and agent both. The caller's
    turns are here because the question a judge is asked is about a
    conversation and half a conversation cannot answer it -- and because the
    seeded prompt-injection attempt lives in caller speech by design (D7), so a
    renderer that dropped caller turns would quietly remove the very input the
    injection acceptance criterion is measured on.

    Speakers are labeled from the event kind rather than from the text, so a
    caller turn cannot present itself as an agent turn by saying so.
    """
    turns = sorted(
        [*context.subject.agent_turns, *context.stimulus.turns],
        key=lambda claim: claim.event_index if claim.event_index is not None else 0,
    )
    lines: list[str] = []
    rendered: dict[str, str] = {}
    for index, claim in enumerate(turns, start=1):
        identifier = f"T{index}"
        line = f"[{identifier}] {claim.key}: {claim.text}"
        rendered[identifier] = line
        lines.append(line)
    return "\n".join(lines), MappingProxyType(rendered)


def render_scale(scale: Sequence[str], definitions: Mapping[str, str]) -> str:
    """The scale as the model sees it, one member per line with its meaning.

    Definitions are rubric data. A scale rendered as bare tokens asks the model
    to guess what `partially_aligned` means, and two runs of the same rubric
    would then be measuring two different things depending on what it guessed.
    """
    lines: list[str] = []
    for member in scale:
        meaning = definitions.get(member, "").strip()
        lines.append(f"- `{member}` -- {meaning}" if meaning else f"- `{member}`")
    return "\n".join(lines)


def fill(template_half: str, values: Mapping[str, str], *, half: str) -> str:
    """Substitute placeholders, refusing anything left over in either direction.

    Both directions, because both have a failure mode and neither is loud on
    its own. A placeholder with no value ships the literal `{{FACTS}}` token to
    the model, which answers anyway. A value for a placeholder that is not in
    the template is content the author believed was being sent and that no
    model ever saw -- the quieter of the two, and the one that would make a
    security control look present while it was absent.
    """
    present = frozenset(_PLACEHOLDER.findall(template_half))
    missing = sorted(present - frozenset(values))
    if missing:
        raise TemplateError(
            f"the {half} half of the template has placeholder(s) with no value: "
            f"{', '.join(missing)}. An unfilled placeholder is sent to the model as its "
            "own literal text, and the model answers anyway."
        )
    unused = sorted(frozenset(values) - present)
    if unused:
        raise TemplateError(
            f"value(s) supplied for placeholder(s) the {half} half of the template does not "
            f"contain: {', '.join(unused)}. That content was never sent, and a control "
            "believed to be in the prompt but absent from it is worse than one that was "
            "never written."
        )
    return _PLACEHOLDER.sub(lambda match: values[match.group(1)], template_half)


def render_prompt(
    template: PromptTemplate,
    context: CheckContext,
    *,
    entry_id: str,
    question: str,
    criteria: str,
    scale: Sequence[str],
    scale_definitions: Mapping[str, str],
    requires_facts: Sequence[str],
    synthesis: SynthesisInput | None = None,
) -> RenderedPrompt:
    """One judged prompt, and the universe it offered, from one pass.

    The two come back together and that is the whole design. A `render` that
    returned only text would leave the validator to reconstruct what could be
    cited, and a reconstruction that drifts from the render is W1 exactly: a
    citation validator that produced zero confirmed true positives because it
    was checking against a universe the model was never shown.
    """
    facts_body, fact_ids = render_facts(context, requires_facts, entry_id=entry_id)
    transcript_body, transcript_ids = render_transcript(context)

    # **The kind of entry decides which sections survive.** A dimension never
    # sees the synthesis instructions and a synthesis never sees the dimension
    # one, because two answer-shape instructions in one message is a model
    # choosing which to follow -- and the schema it is handed only matches one
    # of them.
    system_half = template.system_half
    user_half = template.user_half
    for heading in DIMENSION_ONLY_SECTIONS if synthesis else SYNTHESIS_ONLY_SECTIONS:
        system_half = _drop_section(system_half, heading)
        user_half = _drop_section(user_half, heading)

    system = fill(
        system_half,
        {
            "QUESTION": question.strip(),
            "CRITERIA": criteria.strip(),
            "SCALE": render_scale(scale, scale_definitions),
        },
        half="system",
    )
    if not requires_facts:
        # Omitted *entirely*, heading included. The requirement distinguishes
        # "no category named" from "a named category that is empty", and a
        # heading over an empty body would render them identically.
        user_half = _drop_section(user_half, "# Established facts")
        user_values = {"TRANSCRIPT": transcript_body}
    else:
        user_values = {"FACTS": facts_body, "TRANSCRIPT": transcript_body}
    if synthesis is not None:
        user_values["DIMENSION_RESULTS"] = render_dimension_results(synthesis.results)
    user = fill(user_half, user_values, half="user")

    return RenderedPrompt(
        system=system,
        user=user,
        citable=CitableUniverse(transcript=transcript_ids, facts=fact_ids),
        template_hash=template.sha256,
        rests_on=() if synthesis is None else tuple(synthesis.entry_ids),
    )


#: What the dimension-results block says when this call produced none.
#: An explicit statement rather than an empty block, for the reason
#: `EMPTY_CATEGORY_STATEMENT` gives: a heading over nothing reads as an
#: oversight and invites the model to supply what it thinks should be there.
NO_DIMENSION_RESULTS: Final[str] = (
    "None. No other dimension produced a result for this call. That is a fact "
    "about the run, not an omission from this prompt: do not invent a dimension "
    "identifier, and do not assume a verdict for one."
)


def render_dimension_results(results: Sequence[str]) -> str:
    """The synthesis's own data block, or an explicit statement that it is empty."""
    return "\n\n".join(results) if results else NO_DIMENSION_RESULTS


def _drop_section(body: str, heading: str) -> str:
    """Remove a heading and everything under it up to the next heading.

    Used for the facts section when an entry names no category. Written as a
    removal from the rendered half rather than as a second template, so there
    is one hashed scaffold rather than two that can disagree.
    """
    lines = body.splitlines()
    kept: list[str] = []
    dropping = False
    for line in lines:
        if line.strip() == heading:
            dropping = True
            continue
        if dropping and line.startswith("# "):
            dropping = False
        if not dropping:
            kept.append(line)
    return "\n".join(kept).strip()


def response_schema(scale: Sequence[str], *, synthesis: bool = False) -> dict[str, object]:
    """The declared JSON schema, built from the entry's declared scale.

    Built rather than written, so a scale renamed in the rubric renames the
    enum in the same edit. A schema listing verdicts the entry does not declare
    would let a model return one, and `validate_result` would then refuse it
    downstream -- caught, but caught after the money was spent.

    `additionalProperties: false` and a `required` list on every field, because
    structured output guarantees schema conformance and a schema that permits
    anything guarantees nothing. `minItems: 1` on citations is the machine half
    of "cite at least one identifier": a verdict a reader cannot trace is an
    assertion, and the negative pole of every scale in this project is refused
    downstream with an empty evidence list anyway.
    """
    properties: dict[str, object] = {
        "verdict": {"type": "string", "enum": list(scale)},
        "rationale": {"type": "string"},
        "citations": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        },
    }
    required = ["verdict", "rationale", "citations"]
    if synthesis:
        # `minItems: 1` for the same reason `citations` has it: a synthesis that
        # rests on nothing is not a synthesis. The specification's word for this
        # entry is "constrained to cite the dimensions it rests on", and a
        # schema permitting an empty list would make the constraint prose.
        properties["rests_on"] = {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        }
        required.append("rests_on")
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }
