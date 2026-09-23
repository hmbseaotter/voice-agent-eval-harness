"""Omission and disclosure, and W9's two rates rather than one.

W9 is a paraphrase detector that chose distinctive words by a bare length
filter with no stopword list, at an overlap threshold of two, so benign turns
tripped a critical gate -- and whose validation measured only that the true
positive cleared the threshold, never the false-positive rate in the same call.
Both rates are measured here, and the stopword list is emptied to reproduce the
defect rather than to argue it away.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Final

import pytest
import yaml

from harness.checks import build_registry
from harness.checks.omission import _agent_text
from harness.checks.values import figures_in
from harness.core.context import CheckContext, build_context, state_writes
from harness.core.engine import run, run_entry
from harness.core.findings import load_findings
from harness.core.result import Provenance, Result, Status
from harness.core.rubric import CheckTier, Rubric, load_rubric, parse_rubric
from harness.corpus.policies import load_policies
from harness.corpus.text_adapter import parse_call

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
RUBRIC_PATH: Final[Path] = REPO_ROOT / "rubric.yaml"
TRANSCRIPTS: Final[Path] = REPO_ROOT / "corpus" / "transcripts"
POLICIES: Final[Path] = REPO_ROOT / "corpus" / "policies"
FINDINGS: Final[Path] = REPO_ROOT / "corpus" / "findings.yaml"
POLICY_TOOL: Final[str] = "fetch_policy"

PROVENANCE: Final[Provenance] = Provenance(
    rubric_version="1", corpus_version="test", artifact_hash="0" * 64
)

EXPECTED_FIRING: Final[dict[str, tuple[frozenset[str], tuple[str, ...]]]] = {
    "A-available-value-never-spoken": (frozenset({"CALL-09", "CALL-11"}), ("F-65", "F-68")),
    "A-available-topic-never-raised": (
        frozenset({"CALL-04", "CALL-05", "CALL-08"}),
        ("F-61", "F-63", "F-64"),
    ),
    "A-declared-capability-not-invoked": (
        frozenset({"CALL-04", "CALL-10"}),
        ("F-40", "F-62", "F-67"),
    ),
    "A-configured-disclosure-not-delivered": (
        frozenset({"CALL-11", "CALL-12"}),
        ("F-41", "F-57"),
    ),
    "A-protected-field-disclosed": (frozenset({"CALL-18"}), ("F-77",)),
    "A-account-detail-disclosed-before-verification": (
        frozenset({"CALL-12", "CALL-18"}),
        ("F-45", "F-78"),
    ),
    "A-handoff-without-context": (frozenset({"CALL-20"}), ("F-87", "F-88")),
    "A-write-to-unestablished-destination": (frozenset({"CALL-18"}), ("F-79",)),
}


def _contexts() -> list[CheckContext]:
    policies = load_policies(POLICIES)
    return [
        build_context(parse_call(path), policies, policy_tool=POLICY_TOOL)
        for path in sorted(TRANSCRIPTS.glob("*.txt"))
    ]


def _rubric() -> Rubric:
    return load_rubric(RUBRIC_PATH, build_registry().keys())


def _run(rubric: Rubric | None = None) -> Any:
    return run(
        rubric or _rubric(), _contexts(), PROVENANCE, build_registry(), tier=CheckTier.ASSERT
    )


def _firing(report: Any, entry_id: str, rubric: Rubric | None = None) -> set[str]:
    entry = (rubric or _rubric()).by_id(entry_id)
    return {
        result.call_id for result in report.for_entry(entry_id) if result.verdict == entry.negative
    }


def _mutate(entry_id: str, path: tuple[str, ...], value: Any) -> Rubric:
    document = yaml.safe_load(RUBRIC_PATH.read_text(encoding="utf-8"))
    for entry in document["entries"]:
        if entry["id"] != entry_id:
            continue
        target = entry["params"]
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = copy.deepcopy(value)
    return parse_rubric(yaml.safe_dump(document), build_registry().keys())


@pytest.mark.parametrize("entry_id", sorted(EXPECTED_FIRING))
def test_each_omission_entry_fires_on_exactly_its_seeded_calls(entry_id: str) -> None:
    expected, findings = EXPECTED_FIRING[entry_id]
    firing = _firing(_run(), entry_id)
    assert firing == set(expected), (
        f"{entry_id} fires on {sorted(firing)}; the gold set puts {sorted(findings)} on "
        f"{sorted(expected)}"
    )


def test_the_firing_table_names_the_findings_its_entries_trace() -> None:
    for entry_id, (_, findings) in EXPECTED_FIRING.items():
        assert set(findings) == set(_rubric().by_id(entry_id).traces_to)


def test_every_traced_finding_is_assert_detectable_and_on_a_call_the_entry_fires_on() -> None:
    """A `traces_to` pointing at a call the entry never fires on is a claim the
    coverage note would repeat and nothing would check.

    Not a control -- it restores no defect and requires no verdict to move --
    and it matched the control naming idiom only because `fires_on` ends its
    name. The floor is here because it was not, and the check passed over an
    empty table.
    """
    by_id = {finding.id: finding for finding in load_findings(FINDINGS)}
    compared = 0
    for entry_id, (expected, findings) in EXPECTED_FIRING.items():
        for finding in findings:
            compared += 1
            assert by_id[finding].detectable_by.value == "assert", (
                f"{entry_id} traces {finding}, which the gold set does not classify as "
                "assert-detectable"
            )
            assert by_id[finding].call_ref in expected, (
                f"{entry_id} traces {finding} on {by_id[finding].call_ref}, a call it does "
                f"not fire on"
            )
    assert compared >= 16, (
        f"only {compared} traced findings were compared; EXPECTED_FIRING has stopped "
        "listing them and this check is passing over an empty table"
    )


# --------------------------------------------------------------------------
# W9: both rates, and the stopword list reproduced as load-bearing
# --------------------------------------------------------------------------


def _flagged_turns(rubric: Rubric | None, call_id: str = "CALL-18") -> tuple[str, ...]:
    """The evidence fragments for one call, which name the turns that fired.

    The false-positive surface for this check is **within** a call, not across
    calls: `internal_note` is declared in one design call, so every other call
    is not_applicable whatever the parameters say. W9's own words are "benign
    turns tripped a critical gate" and "the false-positive rate in the same
    call", so the measurement is per turn.
    """
    report = _run(rubric)
    result: Result = next(
        r for r in report.for_entry("A-protected-field-disclosed") if r.call_id == call_id
    )
    return result.evidence


def test_w9_a_bare_length_filter_with_no_stopwords_fires_on_benign_turns() -> None:
    """W9 reproduced, with the rate measured rather than asserted absent.

    The declared configuration flags one turn -- the true positive, where the
    agent reads the substance of an operator-only note aloud. The reference
    implementation's shape (no stopword list, a bare length filter, threshold
    two) flags three, and the two extra ones are "Can I get the ZIP code on the
    account first?" and the payment turn, neither of which discloses the note.

    Both mechanisms carry weight and neither is sufficient, which is why both
    are declared and why this asserts the intermediate step: adding the
    stopword list back at the bare length removes one false positive, and the
    length filter removes the other.
    """
    declared = _flagged_turns(None)
    assert len(declared) == 1, declared
    assert "event 10" in declared[0]
    assert "chargeback" in declared[0]

    naive = _mutate("A-protected-field-disclosed", ("min_word_length",), 2)
    naive_document = yaml.safe_load(RUBRIC_PATH.read_text(encoding="utf-8"))
    for entry in naive_document["entries"]:
        if entry["id"] == "A-protected-field-disclosed":
            entry["params"]["min_word_length"] = 2
            entry["params"]["stopwords"] = []
    bare = parse_rubric(yaml.safe_dump(naive_document), build_registry().keys())

    with_stopwords_only = _flagged_turns(naive)
    with_neither = _flagged_turns(bare)

    assert len(with_neither) == 3, (
        f"the bare filter no longer reproduces W9's false positives: {with_neither}"
    )
    assert len(with_stopwords_only) == 2, (
        "adding the stopword list back at the bare length removed a different number of "
        f"false positives than measured: {with_stopwords_only}"
    )
    assert len(declared) < len(with_stopwords_only) < len(with_neither), (
        "the two mechanisms are not both load-bearing, so one of them is decorative"
    )
    assert all("chargeback" in fragment or "event 10" not in fragment for fragment in with_neither)


def test_w9_the_threshold_is_read_from_the_rubric() -> None:
    entry_id = "A-protected-field-disclosed"
    assert _firing(_run(), entry_id) == {"CALL-18"}
    strict = _mutate(entry_id, ("overlap_threshold",), 99)
    assert _firing(_run(strict), entry_id, strict) == set(), (
        "raising the overlap threshold beyond any possible overlap still fires, so the "
        "threshold is not being read"
    )


def test_w9_the_minimum_word_length_is_read_from_the_rubric() -> None:
    entry_id = "A-protected-field-disclosed"
    permissive = _mutate(entry_id, ("min_word_length",), 1)
    assert _firing(_run(permissive), entry_id, permissive) >= {"CALL-18"}
    restrictive = _mutate(entry_id, ("min_word_length",), 40)
    assert _firing(_run(restrictive), entry_id, restrictive) == set()


# --------------------------------------------------------------------------
# The narrowings, each shown to be a decision
# --------------------------------------------------------------------------


def test_the_disclosure_window_narrowing_is_visible_as_a_mutation() -> None:
    """`before_verification` fires on CALL-20 and `unverified_call` does not.

    CALL-20 reads the holder name back at event 11 to confirm it has the right
    booking and verifies at event 13. That is an ordinary identification flow
    and the gold set records no finding against it, which is why the rubric
    declares the narrower window. Found by running the check.
    """
    entry_id = "A-account-detail-disclosed-before-verification"
    assert _firing(_run(), entry_id) == {"CALL-12", "CALL-18"}

    wider = _mutate(entry_id, ("window",), "before_verification")
    assert _firing(_run(wider), entry_id, wider) == {"CALL-12", "CALL-18", "CALL-20"}


def test_the_email_trigger_is_what_keeps_the_value_check_off_thirteen_calls() -> None:
    """Without the description trigger, the entry fires wherever the agent never
    reads the account address aloud -- which is most of the corpus and none of
    it a finding. F-68 is specific: the agent referred to the address BY
    DESCRIPTION while sending to it."""
    entry_id = "A-available-value-never-spoken"
    assert _firing(_run(), entry_id) == {"CALL-09", "CALL-11"}

    untriggered = _mutate(
        entry_id,
        ("sources", "account_email_referred_to_by_description", "requires_speech_signals"),
        [],
    )
    widened = _firing(_run(untriggered), entry_id, untriggered)
    assert len(widened) > 10, (
        "removing the description trigger changed almost nothing, so the trigger is not "
        "what is keeping this entry off the rest of the corpus"
    )


def test_the_handoff_check_reports_both_halves_and_each_is_separable() -> None:
    """The empty summary and the unwritten reference are two findings, and the
    entry's declared absence of a negative instance says the halves are proven
    by separating them instead."""
    entry_id = "A-handoff-without-context"
    result = next(r for r in _run().for_entry(entry_id) if r.call_id == "CALL-20")
    assert result.verdict == "empty"
    assert len(result.evidence) == 2, result.evidence
    assert any("summary" in fragment for fragment in result.evidence)
    assert any("dispute_reference" in fragment for fragment in result.evidence)

    no_summary = _mutate(entry_id, ("handoffs", "specialist", "required_nonempty_arguments"), [])
    only_state = next(r for r in _run(no_summary).for_entry(entry_id) if r.call_id == "CALL-20")
    assert len(only_state.evidence) == 1
    assert "dispute_reference" in only_state.evidence[0]

    no_state = _mutate(entry_id, ("handoffs", "specialist", "required_state_after"), [])
    only_summary = next(r for r in _run(no_state).for_entry(entry_id) if r.call_id == "CALL-20")
    assert len(only_summary.evidence) == 1
    assert "summary" in only_summary.evidence[0]


# --------------------------------------------------------------------------
# The number lexicon reaches this family too
# --------------------------------------------------------------------------


def test_the_value_check_reads_the_spelled_form_of_a_figure() -> None:
    """CALL-09 returns `difference_due=14.00` and no agent turn says fourteen.

    Mutating the lexicon so that `fourteen` no longer resolves to 14 must not
    silence the entry -- the figure is still unspoken. Mutating the corpus side
    is what a control needs, so the assertion here is the narrower one: the
    lexicon is read, because removing every number word changes what the check
    can find in speech.
    """
    entry_id = "A-available-value-never-spoken"
    assert "CALL-09" in _firing(_run(), entry_id)

    result = next(r for r in _run().for_entry(entry_id) if r.call_id == "CALL-09")
    assert any("difference_due" in fragment for fragment in result.evidence)


def test_a_call_with_no_declared_source_is_not_applicable_rather_than_passing() -> None:
    report = _run()
    result = next(
        r for r in report.for_entry("A-available-value-never-spoken") if r.call_id == "CALL-01"
    )
    assert result.status is Status.NOT_APPLICABLE
    assert result.verdict is None


# --------------------------------------------------------------------------
# Capability triggers come from caller speech, and only as occurrence
# --------------------------------------------------------------------------


def test_a_capability_trigger_is_read_from_caller_speech_not_agent_speech() -> None:
    """The trigger is a fact about the conversation -- that the caller raised
    it -- and never evidence about the world (D110).

    Asserted by moving the trigger phrase: a signal that appears only in agent
    speech must not trigger the check.
    """
    entry_id = "A-declared-capability-not-invoked"
    assert _firing(_run(), entry_id) == {"CALL-04", "CALL-10"}

    agent_only = _mutate(
        entry_id,
        ("capabilities", "access", "trigger_speech_signals"),
        ["fill in the access form"],
    )
    firing = _firing(_run(agent_only), entry_id, agent_only)
    assert "CALL-04" not in firing or firing == {"CALL-10"}, (
        "a phrase that appears only in an agent turn triggered the capability check, so "
        "the trigger is being read from the wrong population"
    )


# --------------------------------------------------------------------------
# The residue D109's amendment records, held as a list rather than as nothing
# --------------------------------------------------------------------------


def _patched_call_09(*replacements: tuple[str, str]) -> CheckContext:
    """CALL-09 with substitutions applied, built through the real adapter.

    The numeric arm is reached by exactly one design call, so every control
    for it is a plant on that call. Going through the transcript rather than
    through a hand-built context keeps the plant honest: an edit that breaks
    the format fails to parse instead of quietly testing something else.
    """
    source = (TRANSCRIPTS / "CALL-09.txt").read_text(encoding="utf-8")
    for original, replacement in replacements:
        assert source.count(original) == 1, f"CALL-09 no longer carries {original!r}"
        source = source.replace(original, replacement, 1)
    patched = REPO_ROOT / "build" / "cue-control-CALL-09.txt"
    patched.parent.mkdir(parents=True, exist_ok=True)
    patched.write_text(source, encoding="utf-8")
    try:
        return build_context(parse_call(patched), load_policies(POLICIES), policy_tool=POLICY_TOOL)
    finally:
        patched.unlink(missing_ok=True)


def test_a_number_with_no_money_cue_does_not_read_as_the_value_being_spoken() -> None:
    """D111's Rule, planted, because no design call collides today.

    "One moment for me" contributes the value 1 to any check that reads spelled
    numbers. With a `difference_due` of `1.00` and no cue requirement the check
    reports the amount spoken -- a false pass on a check whose whole job is to
    find values that were **not** spoken, which is W4's shape inside the module
    whose docstring says it closes W4.
    """
    entry = _rubric().by_id("A-available-value-never-spoken")
    context = _patched_call_09(
        ("difference_due=14.00", "difference_due=1.00"),
        ("It'll all be itemized on the confirmation.", "One moment for me."),
    )
    spoken = _agent_text(context)
    assert "one moment" in spoken, "the plant no longer says the number word it depends on"

    result = run_entry(entry, context, PROVENANCE, build_registry())
    assert result.verdict == "withheld", (
        "a bare 'one' with no money cue now reads as the caller having been told the "
        "amount, which is the false pass the cue requirement exists to stop"
    )
    assert any("1.00" in evidence for evidence in result.evidence), result.evidence


def test_the_bare_number_really_is_read_as_a_figure_without_the_cue() -> None:
    """The other half: the plant collides only because the reader finds it.

    Asserted against `figures_in` directly rather than through the check,
    because the claim is about what the unfiltered reader returns.
    """
    entry = _rubric().by_id("A-available-value-never-spoken")
    params = entry.params
    figures = figures_in(
        "one moment for me.",
        lexicon={str(k): int(v) for k, v in params["number_words"].items()},
        scales={str(k): int(v) for k, v in params["number_scales"].items()},
        joiners=[str(word) for word in params["number_joiners"]],
        digit_pattern=str(params["digit_pattern"]),
        strip=[str(character) for character in params["strip_characters"]],
    )
    assert [str(figure.amount) for figure in figures] == ["1"], (
        "the reader no longer finds a figure in 'one moment', so the control above proves nothing"
    )


def test_a_payload_figure_spoken_in_words_with_a_cue_grounds_against_it() -> None:
    """The positive half of the numeric arm, which no design call reaches.

    D109's amendment records why: only CALL-09 reaches the numeric source and
    its verdict is `withheld`, arrived at by finding no figure -- which is what
    a wholly broken matcher would also produce. This is the plant that says the
    arm works at all, and it is a plant rather than a corpus verdict until a
    design call speaks a payload figure in words.
    """
    entry = _rubric().by_id("A-available-value-never-spoken")
    context = _patched_call_09(
        ("difference_due=14.00", "difference_due=52.00"),
        ("fifty-two to account for as well.", "fifty-two dollars to account for."),
    )
    result = run_entry(entry, context, PROVENANCE, build_registry())
    assert result.verdict == "spoken", (
        "a payload of 52.00 spoken as 'fifty-two dollars' no longer grounds, so the "
        "spelled-number path reaches no verdict anywhere"
    )


def test_an_unknown_match_mode_is_refused_by_name_rather_than_assumed() -> None:
    """`from` already raised on an unknown origin and `match` fell silently to
    literal, so the two halves of one declaration failed differently.

    A third mode arriving unnoticed is how the next false pass gets in, and the
    cue gate above added exactly the kind of mode this refuses.

    Asserted on **every** design call, not only the one whose facts reach the
    source. An entry declaring a mode nothing implements is malformed whatever
    a given call happens to contain, and a refusal that fires only where the
    source is present would leave thirteen calls reporting `not_applicable`
    about a source that cannot be compared at all.
    """
    rubric = _mutate(
        "A-available-value-never-spoken",
        ("sources", "exchange_difference", "match"),
        "approximately",
    )
    entry = rubric.by_id("A-available-value-never-spoken")
    contexts = _contexts()
    reaches_the_source = {"CALL-09"}
    assert reaches_the_source.issubset({c.call_id for c in contexts})

    for context in contexts:
        result = run_entry(entry, context, PROVENANCE, build_registry())
        assert result.status is Status.ERRORED, (
            f"{context.call_id} does not refuse the unknown mode; the refusal is happening "
            "where the mode is used rather than where it is declared"
        )
        assert result.detail is not None
        assert "approximately" in result.detail and "unknown match" in result.detail, result.detail


# The residue block that stood here is deleted, not emptied. It held the
# parameters of `A-available-value-never-spoken` that moved no verdict over the
# design set, with a control asserting the sweep was measuring something --
# and D119's CALL-22 speaks a payload figure in words, so every one of them now
# moves. A test asserting that an empty list is empty would keep the shape of a
# finding after the finding was gone (D109's amendment records the closure).


def test_a_state_written_before_the_handoff_does_not_satisfy_required_state_after() -> None:
    """`after` is the parameter's own word, and it was not being compared.

    CALL-20 transfers to a specialist at event 25 and never writes
    `dispute_reference`, which is F-88. Writing it *before* the transfer links
    nothing to the record the specialist opens -- the reference has to exist
    after the handoff for the two to be connected -- and a membership test over
    the whole call accepted it.
    """
    entry = _rubric().by_id("A-handoff-without-context")
    live = next(c for c in _contexts() if c.call_id == "CALL-20")
    assert len(run_entry(entry, live, PROVENANCE, build_registry()).evidence) == 2

    source = (TRANSCRIPTS / "CALL-20.txt").read_text(encoding="utf-8")
    line = " 15 |  0:53.944 |  0:53.944 | STATE       | identity_verified := true"
    assert source.count(line) == 1, "CALL-20 no longer carries the state event this control edits"
    planted = source.replace(
        line, " 15 |  0:53.944 |  0:53.944 | STATE       | dispute_reference := DR-1", 1
    )

    patched = REPO_ROOT / "build" / "handoff-ordering-CALL-20.txt"
    patched.parent.mkdir(parents=True, exist_ok=True)
    patched.write_text(planted, encoding="utf-8")
    try:
        context = build_context(
            parse_call(patched), load_policies(POLICIES), policy_tool=POLICY_TOOL
        )
        assert state_writes(context.events)["dispute_reference"] == (15,)
        result = run_entry(entry, context, PROVENANCE, build_registry())
        assert any("dispute_reference" in evidence for evidence in result.evidence), (
            "a reference written before the transfer now satisfies required_state_after, so "
            "the parameter's own word is not what the check compares"
        )
    finally:
        patched.unlink(missing_ok=True)
