"""The registry, the builder and the engine that runs one tier over one corpus.

The criterion this file's tier tests answer was added at D104. "Issues zero
model calls" is satisfied by a rubric holding no judged entry whatever the tier
selector does, so the assertion that matters is on **which entries produced a
result** -- run over a fixture rubric declaring both tiers, because D108 keeps
the shipped rubric deterministic.
"""

from __future__ import annotations

from typing import Any, Final

import pytest
import yaml

from harness.core.context import CheckContext, build_context
from harness.core.engine import (
    DuplicateCallError,
    EntryRollup,
    RunReport,
    roll_up,
    run,
    run_entry,
)
from harness.core.events import (
    Call,
    CallRecord,
    Direction,
    DisconnectionReason,
    Environment,
    EventKind,
    Outcome,
    SpeechEvent,
    StateEvent,
)
from harness.core.registry import Registry, RegistryError, ResultBuilder
from harness.core.result import Provenance, Result, Status
from harness.core.rubric import (
    CheckTier,
    Gate,
    ParamView,
    Rubric,
    RubricEntry,
    RubricSchemaError,
    UnreadParameterError,
    VerdictNotInScaleError,
    parse_rubric,
)

PROVENANCE: Final[Provenance] = Provenance(
    rubric_version="1", corpus_version="0.4.0", artifact_hash="a" * 64
)
POLICY_TOOL: Final[str] = "fetch_policy"


# --------------------------------------------------------------------------
# Fixtures: two calls, a handful of checks, a rubric declaring both tiers
# --------------------------------------------------------------------------


def _call(call_id: str, *, note: str = "nothing") -> Call:
    record = CallRecord(
        call_id=call_id,
        agent_id="verso-support",
        agent_version="2027.03.1",
        environment=Environment.PRODUCTION,
        direction=Direction.INBOUND,
        from_number="+1 (415) 555-0184",
        to_number="+1 (415) 555-0100",
        started_at="2027-03-14T09:12:03.000Z",
        answered_at="2027-03-14T09:12:05.480Z",
        ended_at="2027-03-14T09:13:23.329Z",
        duration_ms=80329,
        disconnection_reason=DisconnectionReason.CALLER_HANGUP,
        outcome=Outcome.RESOLVED,
        outcome_reason="exchange_completed",
    )
    return Call(
        source_path=f"planted/{call_id}.txt",
        record=record,
        context=(("booking_reference", "BK-0000-AA"),),
        context_source_lines=((3,),),
        events=(
            SpeechEvent(
                index=1,
                started_at_ms=0,
                ended_at_ms=900,
                kind=EventKind.AGENT,
                body="All set.",
                citation_id="T1",
                source_lines=(1,),
            ),
            StateEvent(
                index=2,
                started_at_ms=1000,
                ended_at_ms=1000,
                kind=EventKind.STATE,
                body=f"note := {note}",
                citation_id="F1",
                source_lines=(2,),
                name="note",
                value=note,
            ),
        ),
        unparsed=(),
    )


def _context(call_id: str, *, note: str = "nothing") -> CheckContext:
    return build_context(_call(call_id, note=note), {}, policy_tool=POLICY_TOOL)


def _looks_for_the_token(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """Violated when the token the entry declares is in the ground truth."""
    token = str(params["token"])
    hits = [fact.reference for fact in context.ground_truth.facts if token in fact.text]
    if hits:
        return builder.violated(tuple(hits))
    return builder.satisfied()


def _always_not_applicable(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    del context, params
    return builder.not_applicable("nothing in this call triggers the check")


def _always_unevaluable(context: CheckContext, params: ParamView, builder: ResultBuilder) -> Result:
    del context, params
    return builder.unevaluable("context:venue_timezone", "the corpus supplies no timezone")


def _raises(context: CheckContext, params: ParamView, builder: ResultBuilder) -> Result:
    del context, params, builder
    raise ValueError("this check is broken")


def _off_scale(context: CheckContext, params: ParamView, builder: ResultBuilder) -> Result:
    del context, params
    return builder.applicable("probably_fine", ("event 1",))


def _satisfied_on_a_wide_scale(
    context: CheckContext, params: ParamView, builder: ResultBuilder
) -> Result:
    """`satisfied()` resolves *the* positive pole, and a three-member scale has
    two. The entry using this declares one, so the builder must refuse."""
    del context, params
    return builder.satisfied(("event 1",))


def _ignores_its_params(context: CheckContext, params: ParamView, builder: ResultBuilder) -> Result:
    del context, params
    return builder.satisfied()


def _registry() -> Registry:
    registry = Registry()
    registry.register("looks_for_the_token", _looks_for_the_token)
    registry.register("always_not_applicable", _always_not_applicable)
    registry.register("always_unevaluable", _always_unevaluable)
    registry.register("raises", _raises)
    registry.register("off_scale", _off_scale)
    registry.register("ignores_its_params", _ignores_its_params)
    registry.register("satisfied_on_a_wide_scale", _satisfied_on_a_wide_scale)
    # The judged check key, bound to a stand-in. These tests are about the tier
    # SELECTOR, not about judging: what they assert is which entries produce a
    # result. The judged engine and its transport live in `harness.judge` and
    # are exercised in `test_judge_engine.py`.
    registry.register("judged_dimension", _always_not_applicable)
    return registry


def _entry(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": "A-token",
        "tier": "assert",
        "check": "looks_for_the_token",
        "gate": "rate",
        "threshold": 1.0,
        "scale": ["clean", "tainted"],
        "negative": "tainted",
        "traces_to": ["F-01"],
        "negative_instance": "CALL-B",
        "params": {"token": "poison"},
    }
    for key, value in overrides.items():
        if value is ...:
            base.pop(key, None)
        else:
            base[key] = value
    return base


def _judged_entry(**overrides: Any) -> dict[str, Any]:
    """A loader-valid judged entry, for the tier-selector tests.

    Every judged field is here because the loader refuses an entry without
    them from P3 -- `max_tokens` by its own named refusal (D24), and the rest
    because a judged call cannot be assembled without them. The fixture used to
    be an `assert` entry with `tier` flipped, which the loader accepted while
    the judged tier lived only in fixtures.
    """
    base: dict[str, Any] = {
        "id": "J-judged",
        "tier": "judge",
        "check": "judged_dimension",
        "gate": "rate",
        "threshold": 0.9,
        "scale": ["aligned", "misaligned"],
        "negative": "misaligned",
        "traces_to": ["F-09"],
        "negative_instance": "CALL-B",
        "model": "claude-sonnet-5",
        "max_tokens": 2048,
        "effort": "high",
        "repetitions": 3,
        "question": "Did the terms stated align with the retrieved clause?",
        "criteria": "Compare what was said against what the clause states.",
        "scale_definitions": {
            "aligned": "every term stated is supported",
            "misaligned": "a term stated contradicts a clause",
        },
        "requires_facts": [],
    }
    for key, value in overrides.items():
        if value is ...:
            base.pop(key, None)
        else:
            base[key] = value
    return base


def _rubric(*entries: dict[str, Any]) -> Rubric:
    text = yaml.safe_dump({"version": "1", "entries": list(entries)}, sort_keys=False)
    return parse_rubric(text, _registry().keys())


# --------------------------------------------------------------------------
# The builder stamps provenance, and resolves verdicts from the entry
# --------------------------------------------------------------------------


def test_every_result_the_builder_makes_carries_its_provenance() -> None:
    """Structural rather than counted.

    "Every result carries the rubric version, the corpus version and the
    extraction-artifact hash" is a property of the only type that produces a
    result, so the count of results missing any of the three is zero because
    there is no path that omits one -- not because something tallied them
    afterwards.
    """
    entry = _rubric(_entry()).entries[0]
    builder = ResultBuilder(entry=entry, call_id="CALL-A", provenance=PROVENANCE)
    made = (
        builder.satisfied(),
        builder.violated(("event 2",)),
        builder.not_applicable("no trigger"),
        builder.unevaluable("context:venue_timezone", "nothing to judge against"),
        builder.errored("the check raised"),
    )
    for result in made:
        assert result.provenance is PROVENANCE
        assert result.entry_id == "A-token"
        assert result.call_id == "CALL-A"
    assert {result.status for result in made} == {
        Status.APPLICABLE,
        Status.NOT_APPLICABLE,
        Status.UNEVALUABLE,
        Status.ERRORED,
    }


def test_the_poles_come_from_the_entry_and_not_from_the_check() -> None:
    """A check never spells its own verdicts.

    Planted on a scale whose members are `clean` and `tainted`: a builder that
    returned a familiar word like "pass" or "supported" would produce a verdict
    outside this entry's scale, and the strings would be living in Python.
    """
    entry = _rubric(_entry()).entries[0]
    builder = ResultBuilder(entry=entry, call_id="CALL-A", provenance=PROVENANCE)
    assert builder.satisfied().verdict == "clean"
    assert builder.violated(("event 2",)).verdict == "tainted"

    renamed = _rubric(_entry(scale=["ok", "bad"], negative="bad")).entries[0]
    other = ResultBuilder(entry=renamed, call_id="CALL-A", provenance=PROVENANCE)
    assert other.satisfied().verdict == "ok"
    assert other.violated(("event 2",)).verdict == "bad"


def test_the_pole_helpers_refuse_a_scale_with_more_than_two_members() -> None:
    """Refused by name rather than guessing which member is "the" positive one."""
    entry = _rubric(_entry(scale=["clean", "partial", "tainted"], negative="tainted")).entries[0]
    builder = ResultBuilder(entry=entry, call_id="CALL-A", provenance=PROVENANCE)
    with pytest.raises(RegistryError, match="two poles"):
        builder.satisfied()
    assert builder.applicable("partial", ("event 1",)).verdict == "partial"


# --------------------------------------------------------------------------
# The tier selector: only deterministic entries execute
# --------------------------------------------------------------------------


def test_only_the_selected_tiers_entries_produce_a_result() -> None:
    """The half of the `--tier assert` requirement the call count does not buy.

    Asserted on which entries produced a result, over a rubric that declares
    both tiers -- because a rubric holding no judged entry satisfies "zero
    model calls" whatever the selector does.
    """
    rubric = _rubric(
        _entry(),
        _judged_entry(),
    )
    assert {entry.tier for entry in rubric.entries} == {CheckTier.ASSERT, CheckTier.JUDGE}, (
        "the fixture rubric does not declare both tiers, so this proves nothing"
    )

    report = run(rubric, [_context("CALL-A")], PROVENANCE, _registry(), tier=CheckTier.ASSERT)
    assert report.entry_ids == ("A-token",)
    assert "J-judged" not in report.entry_ids


def test_selecting_the_judged_tier_runs_the_judged_entry_and_not_the_other() -> None:
    """The control. The assertion above is that a set excludes something, and a
    selector that returned nothing at all would satisfy it too."""
    rubric = _rubric(
        _entry(),
        _judged_entry(),
    )
    report = run(rubric, [_context("CALL-A")], PROVENANCE, _registry(), tier=CheckTier.JUDGE)
    assert report.entry_ids == ("J-judged",)


# --------------------------------------------------------------------------
# Running: order, failures, post-conditions
# --------------------------------------------------------------------------


def test_results_come_back_in_a_fixed_total_order() -> None:
    """Sorted by (call, entry), and identical across two runs.

    Tier A output is asserted byte-identical from P4, and an order that depends
    on dictionary or registry iteration is an order that will differ.
    """
    rubric = _rubric(_entry(id="A-second"), _entry(id="A-first"))
    contexts = [_context("CALL-B"), _context("CALL-A")]
    registry = _registry()

    first = run(rubric, contexts, PROVENANCE, registry, tier=CheckTier.ASSERT)
    second = run(rubric, list(reversed(contexts)), PROVENANCE, registry, tier=CheckTier.ASSERT)

    keys = [(r.call_id, r.entry_id) for r in first.results]
    assert keys == [
        ("CALL-A", "A-first"),
        ("CALL-A", "A-second"),
        ("CALL-B", "A-first"),
        ("CALL-B", "A-second"),
    ]
    assert keys == [(r.call_id, r.entry_id) for r in second.results]


def test_a_check_that_raises_errors_that_result_and_the_run_continues() -> None:
    """One broken check must not cost the other sixty results."""
    rubric = _rubric(_entry(), _entry(id="A-broken", check="raises", params={}))
    report = run(
        rubric,
        [_context("CALL-A"), _context("CALL-B")],
        PROVENANCE,
        _registry(),
        tier=CheckTier.ASSERT,
    )
    broken = report.for_entry("A-broken")
    assert len(broken) == 2
    for result in broken:
        assert result.status is Status.ERRORED
        assert result.verdict is None
        assert result.detail is not None
        assert "ValueError" in result.detail and "this check is broken" in result.detail
    assert all(r.status is Status.APPLICABLE for r in report.for_entry("A-token"))


def test_a_verdict_outside_the_scale_stops_the_run_rather_than_being_reported() -> None:
    """Not caught, deliberately.

    A check raising is a defect in that check; a verdict outside its declared
    scale is a disagreement between the rubric and the code, and reporting it
    as one `errored` row would leave the disagreement in place.
    """
    rubric = _rubric(_entry(id="A-off", check="off_scale", params={}))
    with pytest.raises(VerdictNotInScaleError):
        run(rubric, [_context("CALL-A")], PROVENANCE, _registry(), tier=CheckTier.ASSERT)


def test_an_entry_whose_parameters_went_unread_stops_the_run() -> None:
    """D109, enforced at the point the check returns."""
    rubric = _rubric(
        _entry(id="A-ignored", check="ignores_its_params", params={"threshold_ms": 800})
    )
    with pytest.raises(UnreadParameterError, match="threshold_ms"):
        run(rubric, [_context("CALL-A")], PROVENANCE, _registry(), tier=CheckTier.ASSERT)


def test_a_check_reading_its_parameter_passes_the_same_gate() -> None:
    """The control: the refusal above is about the unread key, not about
    declaring parameters at all."""
    rubric = _rubric(_entry())
    report = run(rubric, [_context("CALL-A")], PROVENANCE, _registry(), tier=CheckTier.ASSERT)
    assert report.results[0].status is Status.APPLICABLE


def test_the_check_reads_its_token_from_the_rubric() -> None:
    """Mutating the parameter moves the verdict. Same corpus, two rubrics."""
    contexts = [_context("CALL-A", note="poison")]
    clean = run(
        _rubric(_entry()), contexts, PROVENANCE, _registry(), tier=CheckTier.ASSERT
    ).results[0]
    assert clean.verdict == "tainted", "the fixture does not contain the declared token"

    moved = run(
        _rubric(_entry(params={"token": "harmless"})),
        contexts,
        PROVENANCE,
        _registry(),
        tier=CheckTier.ASSERT,
    ).results[0]
    assert moved.verdict == "clean", (
        "changing the token in the rubric did not change the verdict, so the "
        "check is reading something other than its entry"
    )


def test_run_entry_is_callable_on_its_own() -> None:
    """Separated from `run` so a control can drive one entry over one call.

    A guard reachable only through the loop that calls it is a guard nothing
    can plant against a single mutated input.
    """
    entry = _rubric(_entry()).entries[0]
    result = run_entry(entry, _context("CALL-A", note="poison"), PROVENANCE, _registry())
    assert result.verdict == "tainted"
    assert result.evidence


# --------------------------------------------------------------------------
# Roll-up: statuses counted, denominator, gates
# --------------------------------------------------------------------------


def _rollup(*entries: dict[str, Any], notes: tuple[str, ...] = ("poison", "nothing")) -> Any:
    rubric = _rubric(*entries)
    contexts = [_context(f"CALL-{i}", note=note) for i, note in enumerate(notes)]
    report = run(rubric, contexts, PROVENANCE, _registry(), tier=CheckTier.ASSERT)
    return roll_up(report, rubric), report


def test_the_rollup_counts_every_status_separately() -> None:
    rollups, _ = _rollup(
        _entry(),
        _entry(id="A-na", check="always_not_applicable", params={}),
        _entry(id="A-unev", check="always_unevaluable", params={}),
        _entry(id="A-broken", check="raises", params={}),
    )
    by_id = {rollup.entry.id: rollup for rollup in rollups}
    assert (by_id["A-token"].applicable, by_id["A-token"].violations) == (2, 1)
    assert by_id["A-na"].not_applicable == 2 and by_id["A-na"].applicable == 0
    assert by_id["A-unev"].unevaluable == 2
    assert by_id["A-broken"].errored == 2


def test_only_applicable_results_form_the_denominator() -> None:
    """`unevaluable` is excluded, which is the criterion, and so is every other
    non-applicable status, which is the requirement."""
    rollups, _ = _rollup(_entry(id="A-unev", check="always_unevaluable", params={}))
    rollup = rollups[0]
    assert rollup.unevaluable == 2
    assert rollup.denominator == 0
    assert rollup.pass_rate is None, (
        "a dimension nothing was applicable for is reporting a rate, so an "
        "unevaluable result reached a denominator"
    )
    assert rollup.gate_failed is False


def test_a_rate_of_zero_is_not_the_same_as_no_denominator() -> None:
    """0.0 says every applicable result violated; `None` says there were none."""
    rollups, _ = _rollup(_entry(), notes=("poison", "poison"))
    assert rollups[0].pass_rate == 0.0
    assert rollups[0].denominator == 2


def test_a_rate_gate_fails_below_its_declared_threshold_and_passes_at_it() -> None:
    at_one, _ = _rollup(_entry(threshold=1.0))
    assert at_one[0].pass_rate == 0.5
    assert at_one[0].gate_failed is True

    at_half, _ = _rollup(_entry(threshold=0.5))
    assert at_half[0].gate_failed is False, (
        "a rate exactly at the threshold is failing, so the comparison is > "
        "rather than the >= the threshold means"
    )

    lenient, _ = _rollup(_entry(threshold=0.25))
    assert lenient[0].gate_failed is False


def test_an_absolute_gate_fails_on_a_single_violation() -> None:
    strict, _ = _rollup(_entry(gate="absolute", threshold=...))
    assert strict[0].violations == 1
    assert strict[0].gate_failed is True

    clean, _ = _rollup(_entry(gate="absolute", threshold=...), notes=("nothing", "nothing"))
    assert clean[0].violations == 0
    assert clean[0].gate_failed is False


def test_the_rollup_counts_a_refused_result_even_though_p2_produces_none() -> None:
    """`refused` is in the channel from P2 because the channel freezes here.

    Nothing at P2 can produce one -- the builder has no `refused()`, because
    only a model declining to answer produces that status and there is no model
    at this tier. The roll-up counts it anyway, so the count is plumbed before
    P3 rather than added alongside the thing that first sets it.
    """
    entry = _rubric(_entry()).entries[0]
    refused = Result(
        entry_id=entry.id,
        call_id="CALL-0",
        status=Status.REFUSED,
        verdict=None,
        evidence=(),
        provenance=PROVENANCE,
        detail="the model declined",
    )
    report = RunReport(results=(refused,), tier=CheckTier.ASSERT)
    rollup = roll_up(report, _rubric(_entry()))[0]
    assert rollup.refused == 1
    assert rollup.denominator == 0


def test_the_rollup_covers_every_entry_of_the_tier_including_silent_ones() -> None:
    """An entry that produced no result still appears, with zeroes.

    An entry missing from the roll-up is an entry a reader cannot tell from one
    that passed, and the coverage note has to be able to say which entries ran.
    """
    rubric = _rubric(_entry(), _entry(id="A-second"))
    report = RunReport(results=(), tier=CheckTier.ASSERT)
    rollups = roll_up(report, rubric)
    assert [rollup.entry.id for rollup in rollups] == ["A-token", "A-second"]
    assert all(rollup.denominator == 0 for rollup in rollups)


# --------------------------------------------------------------------------
# The registry itself
# --------------------------------------------------------------------------


def test_a_check_registered_twice_is_refused() -> None:
    registry = Registry()
    registry.register("only_once", _always_not_applicable)
    with pytest.raises(RegistryError, match="registered twice"):
        registry.register("only_once", _always_unevaluable)


def test_an_unregistered_check_is_refused_naming_what_is_known() -> None:
    with pytest.raises(RegistryError) as caught:
        _registry().get("no_such_check")
    assert "no_such_check" in str(caught.value)
    assert "looks_for_the_token" in str(caught.value)


def test_registry_keys_are_sorted_so_a_message_reads_the_same_everywhere() -> None:
    keys = _registry().keys()
    assert keys == tuple(sorted(keys))
    assert len(keys) == len(_registry())
    assert "raises" in _registry()


@pytest.mark.parametrize("key", ["", " ", "trailing "])
def test_a_malformed_check_key_is_refused(key: str) -> None:
    with pytest.raises(RegistryError, match="empty or carries surrounding whitespace"):
        Registry().register(key, _always_not_applicable)


# --------------------------------------------------------------------------
# Rubric-shape defects stop the run, wherever in the call they surface
# --------------------------------------------------------------------------


def test_asking_for_the_positive_pole_of_a_three_member_scale_stops_the_run() -> None:
    """One class of defect that behaved two ways depending on where it was raised.

    `validate_result` and `validate_params_consumed` run *after* the check
    returns and were never inside the engine's `try`, so a verdict off the
    scale and an unread parameter both stopped the run, as the docstring says
    they must. `satisfied()` on a scale with more than two members raises the
    same class of defect from *inside* the call, and the broad `except
    Exception` turned it into one `errored` result per call: the run then
    reported every other entry as evaluated and exited on the gates, with a
    rubric that cannot be executed.

    The distinction is the point. A check that raises is a defect in the check
    and costs one result; an entry whose scale and builder call disagree is a
    defect in the rubric and there is no result to report.
    """
    rubric = _rubric(
        _entry(
            id="A-three-poles",
            check="satisfied_on_a_wide_scale",
            scale=["clean", "odd", "tainted"],
            negative="tainted",
        )
    )
    with pytest.raises(RegistryError) as raised:
        run(rubric, (_context("CALL-A"),), PROVENANCE, _registry(), tier=CheckTier.ASSERT)
    assert "A-three-poles" in str(raised.value)
    assert "two-member scale" in str(raised.value)


def test_a_check_that_raises_still_costs_only_its_own_result() -> None:
    """The control for the test above, and the reason the broad catch stays.

    Narrowing `except Exception` to a list of what a check might raise is not
    possible, and the one exception nobody listed would take the run down with
    sixty results already computed. `RegistryError` is re-raised by name; every
    other exception is still one `errored` row.
    """
    rubric = _rubric(_entry(id="A-broken", check="raises"), _entry(id="A-fine"))
    report = run(
        rubric,
        (_context("CALL-A"), _context("CALL-B")),
        PROVENANCE,
        _registry(),
        tier=CheckTier.ASSERT,
    )
    assert len(report.results) == 4
    errored = [result for result in report.results if result.status is Status.ERRORED]
    assert {result.entry_id for result in errored} == {"A-broken"}
    assert all(
        result.status is not Status.ERRORED
        for result in report.results
        if result.entry_id == "A-fine"
    )


# --------------------------------------------------------------------------
# One call, one context
# --------------------------------------------------------------------------


def test_two_contexts_with_one_call_id_are_refused() -> None:
    """A rate gate divides by "the calls this entry applied to", and that is a
    population only if each call appears once.

    Two transcript files declaring the same `call_id` is all it takes, and
    nothing upstream compares them: every entry produced one result per
    context, so the call was weighted twice in every pass rate and appeared
    twice in every firing set, silently and with no line of output to say so.

    Refused rather than de-duplicated. Which of the two is the real call is not
    a question the engine can answer, and keeping the first would make the run
    depend on the order the corpus happened to be read in.
    """
    rubric = _rubric(_entry())
    with pytest.raises(DuplicateCallError) as raised:
        run(
            rubric,
            (_context("CALL-A"), _context("CALL-B"), _context("CALL-A")),
            PROVENANCE,
            _registry(),
            tier=CheckTier.ASSERT,
        )
    assert raised.value.call_ids == ("CALL-A",)
    assert "CALL-B" not in str(raised.value)


def test_distinct_call_ids_are_not_refused() -> None:
    """The planted pass. A duplicate check that refuses every corpus is a
    duplicate check nobody can run."""
    rubric = _rubric(_entry())
    report = run(
        rubric,
        (_context("CALL-A"), _context("CALL-B")),
        PROVENANCE,
        _registry(),
        tier=CheckTier.ASSERT,
    )
    assert {result.call_id for result in report.results} == {"CALL-A", "CALL-B"}


# --------------------------------------------------------------------------
# The roll-up's fail-closed branch, which the loader makes unreachable
# --------------------------------------------------------------------------


def test_a_rate_gate_reaching_the_rollup_with_no_threshold_fails_closed() -> None:
    """Unreachable through the loader, which is not the same as unnecessary.

    `parse_rubric` refuses a rate gate with no threshold, so nothing built the
    entry this branch guards against and nothing had ever executed it. The
    branch is what stops W21 -- a threshold consumed by no logic, a rate
    computed nowhere, and a pass reported anyway -- so it is exercised here by
    constructing the entry directly rather than left as a comment claiming it
    would work.
    """
    entry = RubricEntry(
        id="A-no-threshold",
        tier=CheckTier.ASSERT,
        check="looks_for_the_token",
        gate=Gate.RATE,
        scale=("clean", "tainted"),
        negative="tainted",
        violating=("tainted",),
        traces_to=("F-01",),
        negative_instance="CALL-B",
        negative_instance_reason=None,
        threshold=None,
        params={},
        description="built without the loader, which is the point",
    )
    rollup = EntryRollup(
        entry=entry,
        applicable=2,
        not_applicable=0,
        unevaluable=0,
        errored=0,
        refused=0,
        violations=1,
    )
    assert rollup.pass_rate == 0.5
    with pytest.raises(RubricSchemaError) as raised:
        _ = rollup.gate_failed
    assert "A-no-threshold" in str(raised.value)

    # And it fails closed only when a rate was computed at all: an entry
    # nothing applied to has no rate to compare, threshold or not.
    empty = EntryRollup(
        entry=entry,
        applicable=0,
        not_applicable=3,
        unevaluable=0,
        errored=0,
        refused=0,
        violations=0,
    )
    assert empty.gate_failed is False
