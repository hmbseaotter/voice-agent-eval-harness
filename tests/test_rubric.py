"""The rubric loader: every refusal planted, each from a baseline that loads.

Every test here starts from a rubric that is **valid**, breaks exactly one
thing, and asserts the specific refusal. That ordering is the point: a
`pytest.raises` around a fixture that was already broken for a second reason
passes while proving nothing about the guard it names, and this repository has
found that shape three times in its own history.

`test_the_baseline_rubric_loads` runs first for the same reason. If it ever
fails, every refusal below is suspect rather than merely red.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any, Final, cast

import pytest
import yaml

from harness.core.result import Provenance, Result, Status
from harness.core.rubric import (
    KNOWN_JUDGE_CHECKS,
    NO_NEGATIVE_INSTANCE,
    CheckTier,
    DuplicateEntryIdError,
    EntryError,
    Gate,
    JudgedTierWithAbsoluteGateError,
    JudgeKeyOnDeterministicEntryError,
    MaxTokensUndeclaredError,
    MissingGateError,
    NegativeInstanceUndeclaredError,
    NegativePoleWithoutEvidenceError,
    ParamView,
    RateGateWithoutThresholdError,
    RubricSchemaError,
    UnknownCheckKeyError,
    UnreadParameterError,
    VerdictNotInScaleError,
    load_rubric,
    parse_rubric,
    validate_params_consumed,
    validate_result,
)
from harness.core.transport import EFFORT_LEVELS, SUPPORTED_MODELS

KNOWN_CHECKS: Final[tuple[str, ...]] = (
    "completion_claim_without_successful_write",
    "spoken_value_grounded",
)

PROVENANCE: Final[Provenance] = Provenance(
    rubric_version="1", corpus_version="0.4.0", artifact_hash="0" * 64
)


def _entry(**overrides: Any) -> dict[str, Any]:
    """A valid deterministic entry, with named fields replaced.

    A key whose override is the sentinel `...` is deleted rather than replaced,
    so "this key is missing" and "this key is wrong" are both expressible from
    one builder.
    """
    base: dict[str, Any] = {
        "id": "A-claim-integrity",
        "tier": "assert",
        "check": "completion_claim_without_successful_write",
        "gate": "rate",
        "threshold": 1.0,
        "scale": ["supported", "unsupported"],
        "negative": "unsupported",
        "traces_to": ["F-01"],
        "negative_instance": "CALL-06",
        "params": {"success_statuses": ["completed"]},
    }
    for key, value in overrides.items():
        if value is ...:
            base.pop(key, None)
        else:
            base[key] = value
    return base


def _judged_entry(**overrides: Any) -> dict[str, Any]:
    """A judged entry as the loader now requires one.

    Filled out at P3, when a judged dimension exists for real. It carried
    `check: spoken_value_grounded` and a bare `params: {}` while the judged
    tier lived only in fixtures (D108) -- which validated against the
    *deterministic* registry and declared none of the configuration a judged
    call cannot be issued without. Both are now refused by name, so the fixture
    that stands in for a judged entry has to be one.
    """
    base: dict[str, Any] = {
        "id": "J-policy-alignment",
        "tier": "judge",
        "check": "judged_dimension",
        "gate": "rate",
        "threshold": 0.9,
        "scale": ["aligned", "partially_aligned", "misaligned"],
        "negative": "misaligned",
        "traces_to": ["F-09"],
        "negative_instance": "CALL-07",
        "model": "claude-sonnet-5",
        "max_tokens": 2048,
        "effort": "high",
        "repetitions": 10,
        "question": "Did the terms the agent stated align with the retrieved clause?",
        "criteria": "Compare what was said against what the clause states.",
        "scale_definitions": {
            "aligned": "every term stated is supported by a retrieved clause",
            "partially_aligned": "some terms are supported and at least one is not",
            "misaligned": "a term stated contradicts a retrieved clause",
        },
        "requires_facts": ["policy_clauses"],
    }
    for key, value in overrides.items():
        if value is ...:
            base.pop(key, None)
        else:
            base[key] = value
    return base


def _text(*entries: dict[str, Any], version: str = "1") -> str:
    return yaml.safe_dump({"version": version, "entries": list(entries)}, sort_keys=False)


def _load(*entries: dict[str, Any], version: str = "1") -> Any:
    return parse_rubric(_text(*entries, version=version), KNOWN_CHECKS)


# --------------------------------------------------------------------------
# The baseline, first, so every refusal below means what it says
# --------------------------------------------------------------------------


def test_the_baseline_rubric_loads() -> None:
    rubric = _load(_entry(), _judged_entry())
    assert rubric.version == "1"
    assert len(rubric.entries) == 2
    first = rubric.entries[0]
    assert first.id == "A-claim-integrity"
    assert first.tier is CheckTier.ASSERT
    assert first.gate is Gate.RATE
    assert first.threshold == 1.0
    assert first.negative == "unsupported"
    assert first.positive == ("supported",)
    assert first.negative_instance == "CALL-06"
    assert first.negative_instance_reason is None


def test_a_declared_absence_of_a_negative_instance_loads_with_its_reason() -> None:
    rubric = _load(
        _entry(
            negative_instance=NO_NEGATIVE_INSTANCE,
            negative_instance_reason="every design call seeds this defect; no negative exists",
        )
    )
    entry = rubric.entries[0]
    assert entry.negative_instance is None
    assert entry.negative_instance_reason


# --------------------------------------------------------------------------
# The four schema refusals the requirement enumerates
# --------------------------------------------------------------------------


def test_a_duplicate_entry_id_is_rejected_by_name() -> None:
    with pytest.raises(DuplicateEntryIdError) as caught:
        _load(_entry(), _entry(traces_to=["F-02"]))
    assert caught.value.entry_id == "A-claim-integrity"
    assert "A-claim-integrity" in str(caught.value)


def test_a_missing_gate_is_rejected_by_name() -> None:
    with pytest.raises(MissingGateError) as caught:
        _load(_entry(gate=..., threshold=...))
    assert caught.value.entry_id == "A-claim-integrity"
    for member in Gate:
        assert member.value in str(caught.value), (
            "the refusal does not tell the reader which gates were available"
        )


def test_a_rate_gate_with_no_threshold_is_rejected_by_name() -> None:
    with pytest.raises(RateGateWithoutThresholdError) as caught:
        _load(_entry(threshold=...))
    assert caught.value.entry_id == "A-claim-integrity"
    assert "compares against nothing" in str(caught.value)


def test_an_unknown_check_key_is_rejected_by_name() -> None:
    with pytest.raises(UnknownCheckKeyError) as caught:
        _load(_entry(check="checks_the_vibe"))
    assert caught.value.entry_id == "A-claim-integrity"
    assert caught.value.check == "checks_the_vibe"
    for known in KNOWN_CHECKS:
        assert known in str(caught.value)


def test_each_of_the_four_refusals_needs_only_its_own_defect() -> None:
    """The control for the four above, run as one comparison.

    Each mutation is applied to the same baseline and the baseline is asserted
    to load, so a refusal cannot be coming from a second thing wrong with the
    fixture. Written as one test because the claim is about the *set*: four
    cases, four distinct exception types, no overlap.
    """
    assert _load(_entry()).entries

    cases: tuple[tuple[dict[str, Any], type[EntryError]], ...] = (
        ({"gate": ..., "threshold": ...}, MissingGateError),
        ({"threshold": ...}, RateGateWithoutThresholdError),
        ({"check": "not_a_check"}, UnknownCheckKeyError),
    )
    raised: list[type[EntryError]] = []
    for overrides, expected in cases:
        with pytest.raises(expected) as caught:
            _load(_entry(**overrides))
        raised.append(type(caught.value))
    with pytest.raises(DuplicateEntryIdError):
        _load(_entry(), _entry())
    raised.append(DuplicateEntryIdError)
    assert len(set(raised)) == 4, f"the four refusals are not four distinct types: {raised}"


# --------------------------------------------------------------------------
# A judged entry may never declare an absolute gate
# --------------------------------------------------------------------------


def test_a_judged_entry_with_an_absolute_gate_is_rejected_by_name_and_reason() -> None:
    with pytest.raises(JudgedTierWithAbsoluteGateError) as caught:
        _load(_judged_entry(gate="absolute", threshold=...))
    message = str(caught.value)
    assert caught.value.entry_id == "J-policy-alignment"
    assert "must never depend on a live model call" in message, (
        "the refusal names the entry but not the reason, and W13 is what happens "
        "when the reason is left to be remembered"
    )


def test_the_same_entry_loads_with_a_rate_gate() -> None:
    """The control: the refusal is about the gate, not about the entry."""
    assert _load(_judged_entry()).entries[0].tier is CheckTier.JUDGE


def test_a_deterministic_entry_may_declare_an_absolute_gate() -> None:
    """The prohibition is scoped to the judged tier and no wider."""
    rubric = _load(_entry(gate="absolute", threshold=...))
    assert rubric.entries[0].gate is Gate.ABSOLUTE


# --------------------------------------------------------------------------
# The negative-instance declaration (D107)
# --------------------------------------------------------------------------


def test_an_entry_with_no_negative_instance_is_rejected_by_name() -> None:
    with pytest.raises(NegativeInstanceUndeclaredError) as caught:
        _load(_entry(negative_instance=...))
    assert caught.value.entry_id == "A-claim-integrity"


def test_a_null_negative_instance_is_refused_like_a_missing_one() -> None:
    """`null` and a missing key both read as "forgot".

    The field's whole value is that the absence was decided, so the two shapes
    that mean nobody decided are refused identically.
    """
    with pytest.raises(NegativeInstanceUndeclaredError):
        _load(_entry(negative_instance=None))


def test_a_declared_absence_without_a_reason_is_refused() -> None:
    with pytest.raises(EntryError) as caught:
        _load(_entry(negative_instance=NO_NEGATIVE_INSTANCE))
    assert "negative_instance_reason" in str(caught.value)


def test_a_named_instance_carrying_a_reason_is_refused() -> None:
    """The reason field explains a declared absence and nothing else.

    Refused rather than ignored: a reason beside a named call reads as an
    explanation of that call, and the next reader copies the pair.
    """
    with pytest.raises(EntryError) as caught:
        _load(_entry(negative_instance="CALL-06", negative_instance_reason="because"))
    assert "explains a declared" in str(caught.value)


# --------------------------------------------------------------------------
# Scale, negative pole, threshold range, unknown keys
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("overrides", "fragment"),
    [
        ({"scale": ["only_one"]}, "at least two members"),
        ({"scale": ["same", "same"], "negative": "same"}, "repeats a member"),
        ({"negative": "catastrophic"}, "not in the declared scale"),
        ({"threshold": 1.5}, "must be a rate in [0, 1]"),
        ({"threshold": "high"}, "must be a number"),
        ({"gate": "advisory"}, "is not one of"),
        ({"tier": "human"}, "is not one of"),
        ({"traces_to": []}, "must be a non-empty list"),
        ({"params": ["not", "a", "mapping"]}, "must be a mapping"),
    ],
)
def test_a_malformed_field_is_refused_naming_the_entry(
    overrides: dict[str, Any], fragment: str
) -> None:
    with pytest.raises(EntryError) as caught:
        _load(_entry(**overrides))
    assert "A-claim-integrity" in str(caught.value)
    assert fragment in str(caught.value)


def test_an_unknown_entry_key_is_refused() -> None:
    """Silently tolerating an unknown key is how a typo becomes an absent value.

    The findings loader refuses the same way and for the same reason; a rubric
    is the document where a typo'd `treshold` would leave a rate gate reading a
    threshold nobody wrote.
    """
    with pytest.raises(EntryError) as caught:
        _load(_entry(treshold=0.9))
    assert "treshold" in str(caught.value)


def test_an_absolute_gate_carrying_a_threshold_is_refused() -> None:
    """A value nothing reads is a value that will be believed."""
    with pytest.raises(EntryError) as caught:
        _load(_entry(gate="absolute"))
    assert "read by nothing" in str(caught.value)


@pytest.mark.parametrize(
    ("document", "fragment"),
    [
        ("version: '1'\n", "'entries' must be a non-empty list"),
        ("version: '1'\nentries: []\n", "'entries' must be a non-empty list"),
        ("entries: []\n", "'version' must be a non-empty string"),
        ("- not a mapping\n", "a rubric is a mapping"),
    ],
)
def test_a_document_that_is_not_a_rubric_is_refused(document: str, fragment: str) -> None:
    with pytest.raises(RubricSchemaError) as caught:
        parse_rubric(document, KNOWN_CHECKS)
    assert fragment in str(caught.value)


# --------------------------------------------------------------------------
# Verdict against the declared scale, and evidence on the negative pole
# --------------------------------------------------------------------------


def _result(entry_id: str, verdict: str | None, evidence: tuple[str, ...]) -> Result:
    return Result(
        entry_id=entry_id,
        call_id="CALL-01",
        status=Status.APPLICABLE if verdict is not None else Status.NOT_APPLICABLE,
        verdict=verdict,
        evidence=evidence,
        provenance=PROVENANCE,
    )


def test_a_verdict_inside_the_scale_validates() -> None:
    entry = _load(_entry()).entries[0]
    validate_result(_result(entry.id, "supported", ()), entry)


def test_a_verdict_outside_the_scale_raises_naming_entry_and_verdict() -> None:
    entry = _load(_entry()).entries[0]
    with pytest.raises(VerdictNotInScaleError) as caught:
        validate_result(_result(entry.id, "probably_fine", ("event 3",)), entry)
    assert caught.value.entry_id == "A-claim-integrity"
    assert caught.value.verdict == "probably_fine"
    assert "probably_fine" in str(caught.value)


def test_the_negative_pole_with_no_evidence_raises_for_a_judged_scale() -> None:
    """Asserted on a judged scale, as the criterion asks.

    The judged tier is declared in fixtures at P2 rather than in the shipped
    rubric (D108), so this is where a judged scale exists at all. The guard
    reads `entry.negative` -- it is not keyed to a literal, which is W12: an
    evidence-on-failure invariant covering two verdict strings and missing the
    negative pole of six of seven scales.
    """
    entry = _load(_judged_entry()).entries[0]
    with pytest.raises(NegativePoleWithoutEvidenceError) as caught:
        validate_result(_result(entry.id, "misaligned", ()), entry)
    assert caught.value.entry_id == "J-policy-alignment"

    validate_result(_result(entry.id, "misaligned", ("event 12",)), entry)


def test_the_evidence_guard_reads_the_declared_pole_and_not_a_familiar_word() -> None:
    """The control for W12, planted on a scale whose negative pole is positive-sounding.

    A guard keyed to words like "fail" or "unsupported" passes this fixture
    silently, because neither appears in the scale. The negative pole here is
    `retained` -- and it is the member the entry declares, which is the only
    thing the guard is allowed to consult.
    """
    entry = _load(
        _entry(scale=["released", "retained"], negative="retained", traces_to=["F-09"])
    ).entries[0]

    with pytest.raises(NegativePoleWithoutEvidenceError):
        validate_result(_result(entry.id, "retained", ()), entry)

    # And the positive pole with no evidence is fine, so the guard is scoped to
    # the pole rather than demanding evidence from every result.
    validate_result(_result(entry.id, "released", ()), entry)


@pytest.mark.parametrize("status", [Status.NOT_APPLICABLE, Status.ERRORED, Status.REFUSED])
def test_a_result_with_no_verdict_is_not_scale_checked(status: Status) -> None:
    """A verdict-less result has nothing to compare against a scale.

    Scoped rather than universal: validating a `None` verdict against the scale
    would refuse every `not_applicable` result, which is the mirror failure.
    """
    entry = _load(_entry()).entries[0]
    validate_result(
        Result(
            entry_id=entry.id,
            call_id="CALL-01",
            status=status,
            verdict=None,
            evidence=(),
            provenance=PROVENANCE,
        ),
        entry,
    )


# --------------------------------------------------------------------------
# ParamView: a declared parameter nothing read is reportable
# --------------------------------------------------------------------------


def test_a_param_view_records_what_a_check_read() -> None:
    view = ParamView({"threshold_ms": 80_000, "signals": ["all set"], "statuses": ["completed"]})
    assert view.declared == ("signals", "statuses", "threshold_ms")
    assert view["threshold_ms"] == 80_000
    # A list, not a tuple: this constructs the view directly, so the recursive
    # freeze that `parse_rubric` applies to an entry never runs. `ParamView`
    # reports what it was handed; freezing is the loader's job.
    assert view["signals"] == ["all set"]
    assert view.unread == ("statuses",), (
        "a parameter the check never asked for is not being reported, so an entry "
        "could declare a value nothing reads -- which is W20"
    )


def test_reading_every_parameter_leaves_nothing_unread() -> None:
    view = ParamView({"a": 1, "b": 2})
    assert view["a"] == 1
    assert view["b"] == 2
    assert view.unread == ()


def test_iterating_a_param_view_counts_as_reading() -> None:
    """A check that walks its parameters has consumed them.

    Recording otherwise would report keys the check demonstrably read, and a
    guard with a false-positive rate is a guard that gets switched off.
    """
    view = ParamView({"a": 1, "b": 2})
    assert dict(view) == {"a": 1, "b": 2}
    assert view.unread == ()


def test_a_check_cannot_write_to_its_own_parameters() -> None:
    """`ParamView` is a `Mapping`, not a `MutableMapping`, and so is the entry's.

    A check that could edit its own parameters could make any rubric value
    agree with whatever it had already decided to do -- which would leave the
    rubric describing the run rather than governing it.
    """
    entry = _load(_entry()).entries[0]
    for target in (cast(dict[str, Any], entry.view()), cast(dict[str, Any], entry.params)):
        with pytest.raises(TypeError):
            target["success_statuses"] = ["anything"]


def test_an_unread_parameter_fails_the_entry_by_name() -> None:
    """The enforcement a mutation test cannot buy.

    A mutation test proves the property for the parameter it chose. This is the
    same property for every parameter of every entry on every run: an entry
    declaring a value its check ignores is refused, rather than sitting in the
    YAML looking authoritative while nothing reads it.
    """
    entry = _load(_entry(params={"success_statuses": ["completed"], "window_ms": 5000})).entries[0]
    view = entry.view()
    assert view["success_statuses"] == ("completed",)

    with pytest.raises(UnreadParameterError) as caught:
        validate_params_consumed(view, entry)
    assert caught.value.unread == ("window_ms",)
    assert "window_ms" in str(caught.value)
    assert caught.value.entry_id == "A-claim-integrity"


def test_an_entry_whose_parameters_were_all_read_passes() -> None:
    """The control: the refusal is about the unread key, not about having keys."""
    entry = _load(_entry()).entries[0]
    view = entry.view()
    assert view["success_statuses"] == ("completed",)
    validate_params_consumed(view, entry)


def test_an_entry_declaring_no_parameters_passes() -> None:
    """An empty `params` is not the same claim as an unread one.

    Some checks are fully determined by the event model and declare nothing.
    Refusing those would push a decorative parameter into every entry, which is
    the defect this guard exists to prevent, arriving from the other side.
    """
    entry = _load(_entry(params={})).entries[0]
    validate_params_consumed(entry.view(), entry)


def test_two_views_of_one_entry_do_not_share_read_state() -> None:
    """One call's read history must not satisfy another call's requirement."""
    entry = _load(_entry()).entries[0]
    first, second = entry.view(), entry.view()
    assert first["success_statuses"] == ("completed",)
    assert first.unread == ()
    assert second.unread == ("success_statuses",)


# --------------------------------------------------------------------------
# The tier selector
# --------------------------------------------------------------------------


def test_for_tier_returns_only_that_tiers_entries() -> None:
    rubric = _load(_entry(), _judged_entry())
    assert [e.id for e in rubric.for_tier(CheckTier.ASSERT)] == ["A-claim-integrity"]
    assert [e.id for e in rubric.for_tier(CheckTier.JUDGE)] == ["J-policy-alignment"]
    assert len(rubric.for_tier(CheckTier.ASSERT)) + len(rubric.for_tier(CheckTier.JUDGE)) == len(
        rubric.entries
    ), "an entry belongs to neither tier, so the selector would silently drop it"


def test_load_rubric_reads_a_file(tmp_path: Path) -> None:
    path = tmp_path / "rubric.yaml"
    path.write_text(_text(_entry()), encoding="utf-8")
    assert load_rubric(path, KNOWN_CHECKS).entries[0].id == "A-claim-integrity"


def test_a_nested_rubric_value_cannot_be_mutated() -> None:
    """P2-13. `MappingProxyType(dict(params))` froze the top level and left every
    nested list and dict mutable **and shared across every call's `ParamView`**.

    That is the level nothing is stored at: every real configuration in the
    shipped rubric is nested -- `topics.*.claim_signals`, `sources.*.match`,
    `bands.*.fraction` -- so the shallow freeze covered the one depth no value
    lives at, and an appended element would have been visible to the next call
    in the same run.

    D109 records `ParamView` as the single non-frozen type in the tier. That was
    true of the wrapper and not of what it wrapped.
    """
    entry = _load(
        _entry(
            params={
                "success_statuses": ["completed"],
                "topics": {"refund": {"claim_signals": ["refunded"]}},
            }
        )
    ).entries[0]

    assert entry.params["success_statuses"] == ("completed",)
    with pytest.raises(AttributeError):
        entry.params["success_statuses"].append("retrieved")

    nested = entry.params["topics"]["refund"]
    assert nested["claim_signals"] == ("refunded",)
    with pytest.raises(TypeError):
        nested["claim_signals"] = ("something else",)
    with pytest.raises(AttributeError):
        nested["claim_signals"].append("also this")


# --------------------------------------------------------------------------
# Three refusals the loader already made, and one it did not
# --------------------------------------------------------------------------


def test_a_yaml_true_is_not_a_threshold() -> None:
    """`isinstance(True, int)` is True, and YAML writes `yes` as a bool.

    A `threshold: yes` would otherwise be `float(True)` -- 1.0, the strictest
    possible rate gate -- from a line the author meant as a comment on whether
    the gate applies at all. The loader has refused this since it was written
    and nothing had ever run it, so the guard's evidence was that it had never
    fired.
    """
    with pytest.raises(EntryError) as raised:
        _load(_entry(threshold=True))
    assert "must be a number" in str(raised.value)
    assert "A-claim-integrity" in str(raised.value)

    # And the ordinary numbers still load, or the guard above is refusing
    # everything and this file would not notice.
    assert _load(_entry(threshold=0)).entries[0].threshold == 0.0
    assert _load(_entry(threshold=1)).entries[0].threshold == 1.0


def test_an_empty_negative_instance_is_not_a_declaration() -> None:
    """D107 says an entry names a call it must be silent on, or declares `none`
    with a reason. An empty string is neither, and it is what a half-finished
    edit leaves behind: the key present, the value gone, and `negative_instance`
    reading as declared to anything that checks for the key rather than the
    value.
    """
    for blank in ("", "   "):
        with pytest.raises(EntryError) as raised:
            _load(_entry(negative_instance=blank))
        assert "negative_instance" in str(raised.value)
        assert "non-empty string" in str(raised.value)


def test_a_description_that_is_not_a_string_is_refused_rather_than_stringified() -> None:
    """The one this group found rather than confirmed.

    `description=str(raw.get("description", ""))` accepted anything: a
    `description: 42` became `"42"`, and a `description:` with nothing after it
    became the four-character string `"None"`, which reads as a word in every
    report that prints it. Every other field in this loader refuses what it
    cannot use; a field that silently coerces is the one a reader stops
    checking.

    Absent is still fine -- `description` is optional and the empty string is
    what an entry without one gets.
    """
    for bad in (42, ["a list"], {"a": "map"}, True):
        with pytest.raises(EntryError) as raised:
            _load(_entry(description=bad))
        assert "description" in str(raised.value)

    for blank in ("", "   "):
        with pytest.raises(EntryError):
            _load(_entry(description=blank))

    assert _load(_entry(description=...)).entries[0].description == ""
    assert _load(_entry(description="what this entry is for")).entries[0].description == (
        "what this entry is for"
    )


def test_a_yaml_description_with_no_value_is_the_absent_case() -> None:
    """`description:` with nothing after it parses to `None`, not to a missing
    key, so the two have to be handled together or the shorter spelling of
    "absent" becomes the string `"None"`."""
    assert _load(_entry(description=None)).entries[0].description == ""


# --------------------------------------------------------------------------
# The judged entry: every field required, and refused by name when it is not
# --------------------------------------------------------------------------


def test_a_judged_entry_with_no_max_tokens_is_refused_by_name() -> None:
    """D24, and its own error class rather than a generic missing-key message.

    `max_tokens` is a **required** Messages API parameter, so a missing value
    is not a defaulting question but an unissuable request. The refusal has to
    happen before any call is issued, which means at load: discovering it as a
    400 at the seam costs a round trip to learn something the rubric already
    knew.
    """
    with pytest.raises(MaxTokensUndeclaredError) as excinfo:
        _load(_judged_entry(max_tokens=...))
    assert excinfo.value.entry_id == "J-policy-alignment"
    assert "J-policy-alignment" in str(excinfo.value)


def test_max_tokens_is_refused_before_any_other_judged_field_is_checked() -> None:
    """The order is the point. An entry missing several things reports the one
    the requirement names by its own clause -- a run that said "missing
    'effort'" first would send a reader to the wrong line of the spec."""
    with pytest.raises(MaxTokensUndeclaredError):
        _load(_judged_entry(max_tokens=..., effort=..., model=...))


@pytest.mark.parametrize("bad", [0, -1, "2048", 20.48, True])
def test_a_max_tokens_that_is_not_a_positive_integer_is_refused(bad: object) -> None:
    with pytest.raises(EntryError):
        _load(_judged_entry(max_tokens=bad))


def test_an_unsupported_model_is_refused_at_load_rather_than_at_the_seam() -> None:
    """A refusal a reader can act on, rather than a provider error they have to
    interpret -- and one that costs no request."""
    with pytest.raises(EntryError) as excinfo:
        _load(_judged_entry(model="claude-not-a-real-model"))
    assert "claude-not-a-real-model" in str(excinfo.value)
    for supported in SUPPORTED_MODELS:
        assert supported in str(excinfo.value)


def test_an_undeclared_effort_level_is_refused_naming_the_declared_ones() -> None:
    with pytest.raises(EntryError) as excinfo:
        _load(_judged_entry(effort="medium-high"))
    for level in EFFORT_LEVELS:
        assert level in str(excinfo.value)


@pytest.mark.parametrize("bad", [0, -3, "ten", 2.5, None, True])
def test_repetitions_must_be_a_positive_integer_and_is_never_defaulted(bad: object) -> None:
    """N is read from the entry. A default would make the reported verdict
    distribution a property of the code rather than of the rubric."""
    with pytest.raises(EntryError):
        _load(_judged_entry(repetitions=bad))
    with pytest.raises(EntryError):
        _load(_judged_entry(repetitions=...))


def test_a_scale_member_with_no_definition_is_refused_by_name() -> None:
    """A scale rendered as bare tokens asks the model to guess what
    `partially_aligned` means, and two runs of one rubric then measure whatever
    it guessed each time."""
    definitions = {"aligned": "a", "misaligned": "c"}
    with pytest.raises(EntryError) as excinfo:
        _load(_judged_entry(scale_definitions=definitions))
    assert "partially_aligned" in str(excinfo.value)


def test_a_definition_for_a_verdict_the_scale_does_not_declare_is_refused() -> None:
    """Text nothing renders. The other direction of the same equality, and the
    quieter one: an author who renamed a scale member and left the old
    definition behind would otherwise see it silently ignored."""
    definitions = {
        "aligned": "a",
        "partially_aligned": "b",
        "misaligned": "c",
        "unclear": "d",
    }
    with pytest.raises(EntryError) as excinfo:
        _load(_judged_entry(scale_definitions=definitions))
    assert "unclear" in str(excinfo.value)


def test_a_judged_entry_declaring_params_is_refused() -> None:
    """Everything a judged entry configures is in its named fields, each read
    by the renderer, the schema builder or the seam. A `params` mapping would
    be read by nothing, which is W20 arriving in the other tier."""
    with pytest.raises(EntryError) as excinfo:
        _load(_judged_entry(params={"threshold_ms": 500}))
    assert "params" in str(excinfo.value)


def test_a_deterministic_entry_carrying_a_judged_key_is_refused_by_name() -> None:
    """The mirror of the unread-parameter guard, one level up: nothing in the
    deterministic tier reads `max_tokens`, so an entry declaring one would
    describe behavior it does not have."""
    with pytest.raises(JudgeKeyOnDeterministicEntryError) as excinfo:
        _load(_entry(max_tokens=2048, effort="high"))
    assert set(excinfo.value.keys) == {"effort", "max_tokens"}


def test_a_judged_entry_naming_a_deterministic_check_is_refused() -> None:
    """Two vocabularies, chosen by tier. The judged entry's `check` names how
    the judged engine renders and asks; it is not a Python function the
    registry holds."""
    with pytest.raises(UnknownCheckKeyError) as excinfo:
        _load(_judged_entry(check="completion_claim_without_successful_write"))
    for known in KNOWN_JUDGE_CHECKS:
        assert known in str(excinfo.value)


def test_a_deterministic_entry_naming_the_judged_check_is_refused() -> None:
    """The other direction, so the two vocabularies cannot be used
    interchangeably by accident."""
    with pytest.raises(UnknownCheckKeyError):
        _load(_entry(check="judged_dimension"))


# --------------------------------------------------------------------------
# D160: the verdicts that count against a judged gate
# --------------------------------------------------------------------------


def test_an_entry_declaring_no_violating_verdicts_violates_on_its_negative_pole_alone() -> None:
    """Absent is the pole, which is what every entry read before D160, so an entry
    declaring nothing keeps the gate it had."""
    rubric = _load(_entry(), _judged_entry())
    assert [entry.violating for entry in rubric.entries] == [("unsupported",), ("misaligned",)]


def test_a_declared_violating_set_is_held_in_scale_order() -> None:
    """Declared in any order and read in scale order, so the tie rule meets the
    verdicts in the order the report prints them."""
    rubric = _load(_judged_entry(violating=["misaligned", "partially_aligned"]))
    assert rubric.entries[0].violating == ("partially_aligned", "misaligned")


def test_the_loader_would_notice_a_violating_verdict_outside_the_scale() -> None:
    """A verdict the scale does not declare can never come back, so counting it
    counts nothing -- and a misspelled middle value would leave the entry reading
    its pole alone while the rubric says otherwise."""
    with pytest.raises(EntryError) as excinfo:
        _load(_judged_entry(violating=["partialy_aligned", "misaligned"]))
    assert "partialy_aligned" in str(excinfo.value)


def test_the_loader_would_notice_a_violating_set_without_its_negative_pole() -> None:
    """The pole is the scale's own declaration that something went wrong, so a set
    leaving it out would pass a call whose modal verdict is the pole."""
    with pytest.raises(EntryError) as excinfo:
        _load(_judged_entry(violating=["partially_aligned"]))
    assert "omits the negative pole" in str(excinfo.value)


def test_the_loader_would_notice_a_violating_set_naming_every_verdict() -> None:
    """A gate no verdict passes fails on every call it judges, which measures the
    rubric rather than the agent."""
    with pytest.raises(EntryError) as excinfo:
        _load(_judged_entry(violating=["aligned", "partially_aligned", "misaligned"]))
    assert "every member of the scale" in str(excinfo.value)


def test_a_deterministic_entry_declaring_violating_verdicts_is_refused_by_name() -> None:
    """A deterministic check resolves two poles and nothing between them, so the key
    would describe behavior the tier does not have. Refused by the guard every
    judged-only key meets, which is why `violating` is listed among them."""
    with pytest.raises(JudgeKeyOnDeterministicEntryError) as excinfo:
        _load(_entry(violating=["unsupported"]))
    assert set(excinfo.value.keys) == {"violating"}


def test_requires_facts_is_optional_and_defaults_to_naming_nothing() -> None:
    """An entry naming no fact category is legitimate: the facts section is
    then omitted entirely, which is a different rendering from a named category
    that turned out to be empty."""
    entry = _load(_judged_entry(requires_facts=...)).entries[0]
    assert entry.judge is not None
    assert entry.judge.requires_facts == ()


def test_requires_facts_must_be_a_list_of_non_empty_strings() -> None:
    with pytest.raises(EntryError):
        _load(_judged_entry(requires_facts="policy_clauses"))
    with pytest.raises(EntryError):
        _load(_judged_entry(requires_facts=["policy_clauses", ""]))


def test_a_judged_entry_parses_into_a_judge_spec_and_a_deterministic_one_does_not() -> None:
    """`entry.judge is None` is the one question a caller asks to know which
    tier it is holding, so both directions are asserted."""
    judged = _load(_judged_entry()).entries[0]
    assert judged.judge is not None
    assert judged.judge.model == "claude-sonnet-5"
    assert judged.judge.repetitions == 10
    assert judged.judge.requires_facts == ("policy_clauses",)

    deterministic = _load(_entry()).entries[0]
    assert deterministic.judge is None


def test_the_judge_spec_is_frozen_and_its_definitions_cannot_be_edited() -> None:
    """Contract types are frozen dataclasses, and a mapping inside one is not
    frozen by the dataclass being frozen -- this project has paid for that
    distinction once already, in `_frozen`."""
    spec = _load(_judged_entry()).entries[0].judge
    assert spec is not None
    with pytest.raises(dataclasses.FrozenInstanceError):
        spec.model = "claude-opus-5"
    with pytest.raises(TypeError):
        spec.scale_definitions["aligned"] = "edited"


def test_a_precondition_on_a_category_the_entry_never_renders_is_refused() -> None:
    """The refusal that keeps a precondition from being vacuous.

    `applies_when_facts_present` names categories that must yield something for
    the dimension to apply at all. A category the entry never renders yields
    nothing to the prompt either -- so the precondition would be evaluated
    against a renderer whose output the judge never sees, and a typo would make
    the dimension apply to every call while looking as though it were bounded.

    That is the state D125's fix exists to end, so the loader refuses it by
    name rather than at the first live run.
    """
    with pytest.raises(EntryError) as raised:
        _load(
            _judged_entry(
                requires_facts=["policy_clauses"],
                applies_when_facts_present=["tool_events"],
            )
        )
    assert "tool_events" in str(raised.value)
    assert "applies_when_facts_present" in str(raised.value)


def test_an_entry_declaring_no_precondition_loads_with_an_empty_one() -> None:
    """The default, asserted rather than assumed.

    Five of the six judged dimensions declare no precondition, because their
    subject is the conversation and every call has one. An empty tuple is the
    value that means *applies everywhere*, and a loader that defaulted it to
    the entry's `requires_facts` instead would make every dimension with facts
    silently conditional on them.
    """
    entry = _load(_judged_entry(requires_facts=["policy_clauses"])).entries[0]
    assert entry.judge is not None
    assert entry.judge.applies_when_facts_present == ()
