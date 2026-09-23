"""Rendering a judge prompt, and validating against what it rendered.

Run over the **shipped** template and the **shipped** corpus wherever the
property is about them. A prompt test against a fixture template proves the
renderer works and says nothing about the file that will actually be sent --
which is the gap between a check and a control this project keeps paying for.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Final

import pytest

from harness.checks import build_registry
from harness.core.context import CheckContext, build_context
from harness.core.events import EventKind
from harness.core.rubric import Rubric, load_rubric
from harness.corpus.policies import load_policies
from harness.corpus.text_adapter import parse_call
from harness.judge.citations import (
    MalformedResponseError,
    informed_retry_message,
    invalid_citations,
    normalize_identifier,
    parse_answer,
    read_answer,
)
from harness.judge.prompt import (
    EMPTY_CATEGORY_STATEMENT,
    FACT_RENDERERS,
    SYSTEM_BOUNDARY,
    CitableUniverse,
    PromptTemplate,
    RenderedPrompt,
    TemplateError,
    UnknownFactCategoryError,
    fill,
    known_fact_categories,
    load_template,
    render_facts,
    render_prompt,
    render_transcript,
    response_schema,
)

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
TEMPLATE_PATH: Final[Path] = REPO_ROOT / "prompts" / "judge-dimension.v1.md"
TRANSCRIPTS: Final[Path] = REPO_ROOT / "corpus" / "transcripts"
POLICIES: Final[Path] = REPO_ROOT / "corpus" / "policies"
POLICY_TOOL: Final[str] = "fetch_policy"

#: A design call that retrieves a policy, so `policy_clauses` renders facts.
CALL_WITH_POLICY: Final[str] = "CALL-02"

#: A design call that retrieves none, so a named category renders empty.
CALL_WITHOUT_POLICY: Final[str] = "CALL-01"


def _context(call_id: str) -> CheckContext:
    policies = load_policies(POLICIES)
    path = TRANSCRIPTS / f"{call_id}.txt"
    assert path.is_file(), f"{call_id} is not in the design set"
    return build_context(parse_call(path), policies, policy_tool=POLICY_TOOL)


def _template() -> PromptTemplate:
    return load_template(TEMPLATE_PATH)


def _rubric() -> Rubric:
    return load_rubric(REPO_ROOT / "rubric.yaml", build_registry().keys())


def _render(
    call_id: str = CALL_WITH_POLICY, *, requires_facts: Sequence[str] | None = None
) -> RenderedPrompt:
    """Render the SHIPPED judged entry over a design call.

    Reads the entry from `rubric.yaml` rather than from a fixture, so every
    assertion below is about the prompt this project will actually send.
    `requires_facts` is the one override, because two of the requirement's
    three fact behaviors -- omitted entirely, and named-but-empty -- are
    properties of what an entry declares rather than of the corpus.
    """
    entry = _rubric().by_id("J-policy-alignment")
    assert entry.judge is not None
    spec = entry.judge
    return render_prompt(
        _template(),
        _context(call_id),
        entry_id=entry.id,
        question=spec.question,
        criteria=spec.criteria,
        scale=entry.scale,
        scale_definitions=spec.scale_definitions,
        requires_facts=spec.requires_facts if requires_facts is None else requires_facts,
    )


# --------------------------------------------------------------------------
# The template splits into two messages, and that split is the injection posture
# --------------------------------------------------------------------------


def test_the_shipped_template_splits_into_a_system_half_and_a_user_half() -> None:
    template = _template()
    assert template.text.count(SYSTEM_BOUNDARY) == 1
    assert template.system_half and template.user_half


def test_a_template_without_the_boundary_is_refused() -> None:
    """A template that silently rendered as one message would put the whole
    instruction hierarchy back beside the transcript with nothing to say so."""
    with pytest.raises(TemplateError):
        _ = PromptTemplate(text="no boundary here").system_half


def test_every_instruction_is_in_the_system_message_and_only_data_in_the_user_one() -> None:
    """The posture, asserted rather than described.

    The security requirement is that no raw caller or agent speech is spliced
    into a judge prompt outside the delimited untrusted block. This asserts the
    stronger property the shipped template buys: speech is not in the system
    message at all, so the message carrying the model's instructions contains
    nothing an attacker influenced.
    """
    rendered = _render()
    context = _context(CALL_WITH_POLICY)
    speech = [claim.text for claim in context.stimulus.turns if len(claim.text) > 40]
    assert speech, "the fixture call has no caller speech long enough to be distinctive"
    for turn in speech:
        assert turn not in rendered.system, (
            "caller speech reached the system message, which carries the instructions"
        )
        assert turn in rendered.user


def test_the_untrusted_block_is_delimited_and_labeled() -> None:
    rendered = _render()
    user = rendered.user
    assert "<<<BEGIN UNTRUSTED TRANSCRIPT>>>" in user
    assert "<<<END UNTRUSTED TRANSCRIPT>>>" in user
    assert "untrusted data" in user.lower()
    assert "instruction" in user.lower()


def test_the_injected_turn_is_rendered_as_data_rather_than_dropped() -> None:
    """D7's corpus carries an injection attempt in caller speech, and the
    renderer's job is to *show* it inside the untrusted block -- not to filter
    it. A renderer that dropped caller turns would remove the input the
    injection acceptance criterion is measured on."""
    rendered = _render("CALL-06")
    user = rendered.user
    start = user.index("<<<BEGIN UNTRUSTED TRANSCRIPT>>>")
    end = user.index("<<<END UNTRUSTED TRANSCRIPT>>>")
    caller_lines = [
        line
        for line in user[start:end].splitlines()
        if line.startswith("[T") and EventKind.CALLER.value in line
    ]
    assert caller_lines, "no caller turn was rendered for the injection call"


# --------------------------------------------------------------------------
# Two populations, numbered independently
# --------------------------------------------------------------------------


def test_speech_is_tagged_t_and_facts_are_tagged_f() -> None:
    rendered = _render()
    universe = rendered.citable
    assert universe.transcript and universe.facts
    assert all(name.startswith("T") for name in universe.transcript)
    assert all(name.startswith("F") for name in universe.facts)


def test_the_two_populations_are_numbered_independently() -> None:
    """`[T3]` and `[F3]` are different things and both may exist, which is what
    makes validating each against its own set possible at all."""
    rendered = _render()
    universe = rendered.citable
    assert "T1" in universe.transcript
    assert "F1" in universe.facts
    assert universe.text_of("T1") != universe.text_of("F1")


def test_a_fabricated_citation_is_rejected() -> None:
    """The criterion asks for this directly, and says why: the reference
    implementation's citation validation produced zero confirmed true positives
    precisely because it was never tested against a deliberately fabricated
    citation, so nothing distinguished "the judges never fabricated" from "the
    detector never fired"."""
    rendered = _render()
    universe = rendered.citable
    assert invalid_citations(["T999"], universe) == ("T999",)
    assert invalid_citations(["F999"], universe) == ("F999",)
    assert invalid_citations(["not-an-identifier"], universe) == ("not-an-identifier",)


def test_a_real_fact_citation_validates() -> None:
    """The other direction. A rejector that rejected everything would satisfy
    the test above."""
    rendered = _render()
    universe = rendered.citable
    assert invalid_citations(["F1", "T1"], universe) == ()


def test_each_population_is_validated_against_its_own_set_and_not_the_union() -> None:
    """The sharpest case, and the one a union check waves through.

    A universe with many transcript lines and few facts: `F9` does not exist,
    but *something* numbered 9 was rendered. Checked against the union it
    passes; checked against its own population it does not.
    """
    universe = CitableUniverse(
        transcript={f"T{n}": f"line {n}" for n in range(1, 13)},
        facts={"F1": "fact one", "F2": "fact two"},
    )
    assert invalid_citations(["F9"], universe) == ("F9",)
    assert invalid_citations(["T9"], universe) == ()


def test_a_bracketed_identifier_is_the_same_citation_as_a_bare_one() -> None:
    """Refusing two of the three spellings would spend the retry budget on
    formatting rather than on fabrication."""
    universe = CitableUniverse(transcript={"T1": "line"}, facts={})
    assert invalid_citations(["[T1]", "T1", " T1 "], universe) == ()
    assert normalize_identifier("[T1]") == "T1"
    assert normalize_identifier("garbage") == "garbage"


# --------------------------------------------------------------------------
# Established facts: omitted, empty, or unknown
# --------------------------------------------------------------------------


def test_naming_no_category_omits_the_facts_section_entirely() -> None:
    rendered = _render(requires_facts=())
    user = rendered.user
    assert "Established facts" not in user
    assert rendered.citable.facts == {}
    assert "<<<BEGIN UNTRUSTED TRANSCRIPT>>>" in user, "the transcript survived the removal"


def test_a_named_but_empty_category_renders_an_explicit_negative_statement() -> None:
    """ "Omitted entirely" and "empty" are different states, and the requirement
    distinguishes them. A heading over nothing reads as an oversight and
    invites the model to supply the missing content from its own knowledge."""
    rendered = _render(CALL_WITHOUT_POLICY)
    user = rendered.user
    assert "Established facts" in user
    assert EMPTY_CATEGORY_STATEMENT in user
    assert rendered.citable.facts == {}


def test_an_unknown_fact_category_aborts_naming_it() -> None:
    """Not omitted silently. A judge asked without the facts its entry declared
    is answering a different question from the one the rubric asked, and its
    verdict would look exactly like a considered one."""
    with pytest.raises(UnknownFactCategoryError) as excinfo:
        render_facts(_context(CALL_WITH_POLICY), ["state_writes"], entry_id="J-x")
    assert excinfo.value.category == "state_writes"
    assert "state_writes" in str(excinfo.value)
    for known in known_fact_categories():
        assert known in str(excinfo.value)


def test_every_declared_fact_renderer_returns_facts_for_some_design_call() -> None:
    """A renderer nothing can reach is a category an entry may name and get
    nothing from -- the empty-category branch firing not because the call had
    no such facts but because the renderer never works."""
    contexts = [_context(call) for call in ("CALL-01", "CALL-02", "CALL-03")]
    for category in known_fact_categories():
        assert any(FACT_RENDERERS[category](context) for context in contexts), (
            f"the {category!r} renderer returned nothing for any sampled call"
        )


def test_no_agent_or_caller_speech_reaches_the_facts_section() -> None:
    """Structural, and asserted anyway. `GroundTruth` cannot contain speech --
    a `SpeechEvent` returns `None` from `_event_fact` and never becomes a
    `Fact`. This is the assertion that would notice if that ever changed."""
    context = _context(CALL_WITH_POLICY)
    body, _ = render_facts(context, list(known_fact_categories()), entry_id="J-x")
    for claim in [*context.subject.agent_turns, *context.stimulus.turns]:
        if len(claim.text) > 40:
            assert claim.text not in body


# --------------------------------------------------------------------------
# Placeholders: both directions
# --------------------------------------------------------------------------


def test_an_unfilled_placeholder_is_refused() -> None:
    """An unfilled placeholder is sent to the model as its own literal text,
    and the model answers anyway."""
    with pytest.raises(TemplateError) as excinfo:
        fill("a {{QUESTION}} and a {{CRITERIA}}", {"QUESTION": "q"}, half="system")
    assert "CRITERIA" in str(excinfo.value)


def test_a_value_for_a_placeholder_the_template_lacks_is_refused() -> None:
    """The quieter of the two failures, and the one that would make a security
    control look present while it was absent: content the author believed was
    being sent, that no model ever saw."""
    with pytest.raises(TemplateError) as excinfo:
        fill("only {{QUESTION}}", {"QUESTION": "q", "CRITERIA": "c"}, half="system")
    assert "CRITERIA" in str(excinfo.value)


def test_the_rendered_prompt_carries_no_unfilled_placeholder() -> None:
    rendered = _render()
    assert "{{" not in rendered.system
    assert "{{" not in rendered.user


# --------------------------------------------------------------------------
# The schema is built from the entry's declared scale
# --------------------------------------------------------------------------


def test_the_schema_enumerates_exactly_the_declared_scale() -> None:
    """Built rather than written, so a scale renamed in the rubric renames the
    enum in the same edit."""
    entry = _rubric().by_id("J-policy-alignment")
    schema = response_schema(entry.scale)
    properties = schema["properties"]
    required = schema["required"]
    assert isinstance(properties, dict)
    assert isinstance(required, list)
    assert properties["verdict"]["enum"] == list(entry.scale)
    assert schema["additionalProperties"] is False
    assert set(required) == {"verdict", "rationale", "citations"}
    assert properties["citations"]["minItems"] == 1


def test_the_scale_is_rendered_with_its_definitions() -> None:
    """A scale rendered as bare tokens asks the model to guess what
    `partially_aligned` means, and two runs of one rubric then measure whatever
    it guessed each time."""
    entry = _rubric().by_id("J-policy-alignment")
    assert entry.judge is not None
    system = _render().system
    for member in entry.scale:
        assert member in system
        definition = entry.judge.scale_definitions[member].strip()
        assert definition.split("\n")[0][:40] in system


# --------------------------------------------------------------------------
# Parsing a response
# --------------------------------------------------------------------------


def test_a_well_formed_answer_parses() -> None:
    answer = parse_answer('{"verdict": "aligned", "rationale": "why", "citations": ["T1", "F2"]}')
    assert answer.verdict == "aligned"
    assert answer.citations == ("T1", "F2")


@pytest.mark.parametrize(
    "text",
    [
        "not json at all",
        '{"verdict": "aligned", "rationale": "why"}',
        '{"verdict": "aligned", "citations": ["T1"]}',
        '{"verdict": "aligned", "rationale": "why", "citations": "T1"}',
        '{"verdict": "aligned", "rationale": "why", "citations": []}',
        '["aligned"]',
    ],
)
def test_a_response_that_is_not_the_declared_object_is_refused(text: str) -> None:
    """No field is defaulted. Supplying one would turn a broken response into a
    plausible verdict, which is the failure this whole tier exists to avoid."""
    with pytest.raises(MalformedResponseError):
        parse_answer(text)


def test_every_readable_fault_is_named_not_the_first() -> None:
    """A missing field, an empty `citations` and a `rests_on` that is not a list, in one
    response, are all recorded; invalid JSON still stops the reading, since nothing past it
    can be read (P4-30, D179)."""
    reading = read_answer('{"rationale": "why", "citations": [], "rests_on": "J-a"}')
    assert reading.answer is None
    assert [str(failure) for failure in reading.failures] == [
        "response is missing declared field(s): verdict",
        "'citations' is empty, and the declared schema requires at least one identifier",
        "'rests_on' is not a list",
    ]
    assert len(read_answer("not json at all").failures) == 1


# --------------------------------------------------------------------------
# The informed retry carries both halves
# --------------------------------------------------------------------------


def test_the_retry_message_names_the_rejected_ids_and_the_full_valid_set() -> None:
    """Both halves, because each alone fails differently: the rejected ones
    without the valid set leave the model guessing what it should have cited,
    and the valid set without the rejection does not say what went wrong."""
    universe = CitableUniverse(transcript={"T1": "a", "T2": "b"}, facts={"F1": "c"})
    message = informed_retry_message("ORIGINAL", ["T999"], universe)
    assert "ORIGINAL" in message, "the transcript must survive, or the retry is unanswerable"
    assert "T999" in message
    for identifier in ("[T1]", "[T2]", "[F1]"):
        assert identifier in message


def test_the_retry_message_keeps_the_transcript_it_is_correcting_against() -> None:
    """Appended rather than replacing. Rebuilding the prompt would risk
    rendering a different universe from the one being corrected against."""
    rendered = _render()
    message = informed_retry_message(
        rendered.user,
        ["T999"],
        rendered.citable,
    )
    assert "<<<BEGIN UNTRUSTED TRANSCRIPT>>>" in message


# --------------------------------------------------------------------------
# The template hash
# --------------------------------------------------------------------------


def test_the_template_hash_moves_when_the_template_does() -> None:
    """It is one of the two staleness inputs, so a hash that did not move would
    make a replay run serve a fossil recorded against a different prompt."""
    original = _template()
    edited = PromptTemplate(text=original.text + "\nan added line\n")
    assert edited.sha256 != original.sha256


def test_a_comment_only_edit_does_not_move_the_template_hash() -> None:
    """The other half, and the reason the hash covers the sent halves.

    D8's staleness check exists because a committed run log "would then report
    a fossil that quietly disagrees with live behavior". A comment cannot
    change live behavior -- comments are stripped before rendering and no model
    sees them -- so a comment edit invalidating every recorded log is a refusal
    with nothing behind it.

    The cost was paid once before this changed: a one-word spelling fix in this
    template's own prose would have discarded a full recorded run.
    """
    original = _template()
    commented = PromptTemplate(
        text=original.text.replace(
            "The judge prompt scaffold.", "The judge prompt scaffold. An added sentence."
        )
    )
    assert commented.text != original.text, "the edit did not land, so this compares nothing"
    assert commented.sha256 == original.sha256


def test_an_edit_to_the_sent_text_does_move_the_template_hash() -> None:
    """The control on the control. A hash that ignored everything would satisfy
    the test above, and this is the half that would notice."""
    original = _template()
    for edited in (
        original.text.replace("# The question", "# The question, restated"),
        original.text.replace("# The transcript", "# The transcript, restated"),
    ):
        changed = PromptTemplate(text=edited)
        assert changed.text != original.text
        assert changed.sha256 != original.sha256


def test_the_rendered_prompt_reports_the_hash_of_the_template_that_rendered_it() -> None:
    """Carried through from the render rather than recomputed by the caller. A
    hash computed separately from the text it describes is a hash that will one
    day describe a file nobody sent."""
    assert _render().template_hash == _template().sha256


def test_render_transcript_labels_speakers_from_the_event_kind() -> None:
    """So a caller turn cannot present itself as an agent turn by saying so."""
    body, universe = render_transcript(_context(CALL_WITH_POLICY))
    assert universe
    kinds = {line.split("] ", 1)[1].split(":", 1)[0] for line in body.splitlines()}
    # The canonical vocabulary token, not a prettier spelling of it. Rendering
    # `agent` where the event model says `AGENT` would be a second spelling of
    # a closed vocabulary, which is the thing every other vocabulary in this
    # project is validated against rather than restyled.
    assert kinds <= {EventKind.AGENT.value, EventKind.CALLER.value}, (
        f"unexpected speaker labels: {kinds}"
    )
    assert len(kinds) == 2, "one of the two speaker kinds was not rendered"
