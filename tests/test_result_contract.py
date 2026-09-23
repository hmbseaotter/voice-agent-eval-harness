"""The Result contract, asserted in both directions and against a sixth value.

The criteria this file answers were amended at D104, because as written they
bought one half of the requirement they came from. `verdict is None when status
is not applicable` was asserted; `verdict is populated when status is` was not,
so a harness returning `applicable` with no verdict passed. Both directions are
here, and the second is the one that was missing.

Every guard is planted. A contract whose only evidence is that nothing has
violated it has been proven against nothing -- and this channel freezes at P2,
so a hole in it is a hole every later phase reads through.
"""

from __future__ import annotations

import ast
import dataclasses
import importlib
from pathlib import Path
from typing import Any, Final, cast

import pytest

from harness.core.result import (
    NON_RATE_STATUSES,
    STATUSES,
    MissingGroundTruthReferenceError,
    Provenance,
    Result,
    Status,
    StatusNotInChannelError,
    VerdictChannelError,
)

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
CORE: Final[Path] = REPO_ROOT / "src" / "harness" / "core"

PROVENANCE: Final[Provenance] = Provenance(
    rubric_version="1", corpus_version="0.4.0", artifact_hash="0" * 64
)


def _result(
    status: Status,
    verdict: str | None,
    *,
    entry_id: str = "A-example",
    evidence: tuple[str, ...] = ("event 15 -- t3 -> refused_ineligible successful=false",),
    missing_ground_truth: str | None = None,
) -> Result:
    return Result(
        entry_id=entry_id,
        call_id="CALL-01",
        status=status,
        verdict=verdict,
        evidence=evidence,
        provenance=PROVENANCE,
        missing_ground_truth=missing_ground_truth,
    )


# --------------------------------------------------------------------------
# The status channel is closed at five
# --------------------------------------------------------------------------


def test_the_channel_is_exactly_the_five_the_specification_declares() -> None:
    """The vocabulary itself, against the document rather than against habit."""
    assert tuple(status.value for status in STATUSES) == (
        "applicable",
        "not_applicable",
        "unevaluable",
        "errored",
        "refused",
    )
    assert set(STATUSES) == set(Status), (
        "STATUSES and the Status enum disagree, so one of them is a second copy "
        "of a closed vocabulary that has drifted from the other"
    )


def test_the_non_rate_statuses_are_derived_and_not_typed_twice() -> None:
    """`NON_RATE_STATUSES` is `STATUSES` minus `applicable`, computed.

    A hand-written second tuple is how a status gets added to one list and not
    the other, which is W11 arriving by a different route: a member missing
    from the exclusion list silently joins a rate's denominator.
    """
    assert set(NON_RATE_STATUSES) == set(STATUSES) - {Status.APPLICABLE}
    assert Status.APPLICABLE not in NON_RATE_STATUSES
    assert len(NON_RATE_STATUSES) == len(STATUSES) - 1


@pytest.mark.parametrize("status", STATUSES)
def test_every_declared_status_constructs(status: Status) -> None:
    """All five, so the channel is exercised rather than asserted."""
    verdict = "supported" if status is Status.APPLICABLE else None
    missing = "policy:cancellation.v1" if status is Status.UNEVALUABLE else None
    result = _result(status, verdict, missing_ground_truth=missing)
    assert result.status is status


def test_a_sixth_status_is_refused_by_name() -> None:
    """The control for the closure claim.

    `mypy --strict` rejects this at the call site, which is why the runtime
    check is the one that matters: statuses arrive from YAML at P2 and from a
    run log at P3, and neither is type-checked. The cast is how the test
    reaches the runtime path the type checker would otherwise hide.
    """
    with pytest.raises(StatusNotInChannelError) as caught:
        _result(cast(Status, "inconclusive"), None)
    message = str(caught.value)
    assert "inconclusive" in message, "the refusal does not name the offending value"
    assert "A-example" in message, "the refusal does not name the entry it came from"
    for status in STATUSES:
        assert status.value in message, (
            f"the refusal does not tell the reader that {status.value!r} was available"
        )


def test_a_status_that_is_merely_the_right_string_is_still_refused() -> None:
    """`"applicable"` is not `Status.APPLICABLE`, and the difference is the point.

    `Status` is a `StrEnum`, so the bare string compares equal to the member and
    would satisfy any check written as `status == "applicable"`. The contract
    holds the member, because that is what makes the vocabulary closed: a bare
    string is whatever the caller typed.
    """
    with pytest.raises(StatusNotInChannelError):
        _result(cast(Status, "applicable"), "supported")


# --------------------------------------------------------------------------
# verdict is populated if and only if status is applicable -- both directions
# --------------------------------------------------------------------------


def test_applicable_with_a_verdict_is_the_one_shape_that_holds() -> None:
    result = _result(Status.APPLICABLE, "unsupported")
    assert result.verdict == "unsupported"
    assert result.counts_toward_rate is True


def test_applicable_without_a_verdict_is_refused() -> None:
    """The implication the criteria did not buy until D104.

    Asserted first among the two, because it is the one an implementation can
    violate while passing every criterion the specification carried: the other
    direction was already checked.
    """
    with pytest.raises(VerdictChannelError) as caught:
        _result(Status.APPLICABLE, None)
    assert "A-example" in str(caught.value)
    assert "verdict is absent" in str(caught.value)


@pytest.mark.parametrize("status", NON_RATE_STATUSES)
def test_a_verdict_on_any_other_status_is_refused(status: Status) -> None:
    """Every non-`applicable` status, not one of them.

    W12 is the version of this that covered two verdict strings and missed six
    scales; the shape repeats whenever a guard is written against an example
    rather than against the vocabulary.
    """
    missing = "policy:cancellation.v1" if status is Status.UNEVALUABLE else None
    with pytest.raises(VerdictChannelError) as caught:
        _result(status, "supported", missing_ground_truth=missing)
    assert status.value in str(caught.value)


@pytest.mark.parametrize("status", NON_RATE_STATUSES)
def test_no_other_status_counts_toward_a_rate(status: Status) -> None:
    missing = "policy:cancellation.v1" if status is Status.UNEVALUABLE else None
    assert _result(status, None, missing_ground_truth=missing).counts_toward_rate is False


# --------------------------------------------------------------------------
# unevaluable names what was missing
# --------------------------------------------------------------------------


def test_unevaluable_names_the_reference_the_corpus_did_not_supply() -> None:
    result = _result(Status.UNEVALUABLE, None, missing_ground_truth="context:venue_timezone")
    assert result.missing_ground_truth == "context:venue_timezone"


def test_a_bare_unevaluable_is_refused() -> None:
    """The requirement says the system SHALL record that identifier.

    Enforced at construction rather than checked in the report, because a rule
    applied where somebody remembered to apply it is the rule this repository
    keeps rediscovering as prose.
    """
    with pytest.raises(MissingGroundTruthReferenceError) as caught:
        _result(Status.UNEVALUABLE, None)
    assert "A-example" in str(caught.value)


def test_a_whitespace_reference_does_not_satisfy_the_requirement() -> None:
    """The branch a non-empty check written as `is not None` would let through."""
    with pytest.raises(MissingGroundTruthReferenceError):
        _result(Status.UNEVALUABLE, None, missing_ground_truth="   ")


def test_the_other_statuses_do_not_require_a_missing_reference() -> None:
    """The guard is scoped to the status that means it, and no wider.

    A guard one noun wider than its rule refuses results nobody meant to
    refuse, which is the mirror of the failure the rest of this file is about.
    """
    for status in (Status.NOT_APPLICABLE, Status.ERRORED, Status.REFUSED):
        assert _result(status, None).missing_ground_truth is None


# --------------------------------------------------------------------------
# Frozen dataclasses and Final constants, over the whole contract surface
# --------------------------------------------------------------------------


def _core_modules() -> list[str]:
    names = [
        f"harness.core.{path.stem}" for path in sorted(CORE.glob("*.py")) if path.stem != "__init__"
    ]
    assert len(names) >= 4, f"only {len(names)} core modules found; the layout moved"
    return names


def _dataclasses_declared_in(module_name: str) -> list[tuple[str, bool]]:
    """`(class name, declared frozen)` for every `@dataclass` in the module.

    Read from the source rather than from `__dataclass_params__`, which
    typeshed does not expose on a narrowed dataclass -- and the declaration is
    the better question anyway: the criterion is about what the contract
    *declares*, and a bare `@dataclass` with no arguments is exactly the
    omission it exists to catch.
    """
    path = CORE / f"{module_name.rsplit('.', 1)[1]}.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    declared: list[tuple[str, bool]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for decorator in node.decorator_list:
            target = decorator.func if isinstance(decorator, ast.Call) else decorator
            if not (isinstance(target, ast.Name) and target.id == "dataclass"):
                continue
            frozen = isinstance(decorator, ast.Call) and any(
                keyword.arg == "frozen"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is True
                for keyword in decorator.keywords
            )
            declared.append((node.name, frozen))
    return declared


def test_every_contract_dataclass_is_declared_frozen() -> None:
    """Read from the modules rather than listed here.

    A list of type names in a test is a list that stops covering the type added
    after it was written, and the contract surface grows for the rest of this
    phase.
    """
    mutable: list[str] = []
    found = 0
    for name in _core_modules():
        for class_name, frozen in _dataclasses_declared_in(name):
            found += 1
            if not frozen:
                mutable.append(f"{name}.{class_name}")
    assert not mutable, (
        "contract dataclasses that are not declared frozen, so a later stage can "
        "edit what an earlier one reported:\n  " + "\n  ".join(mutable)
    )
    assert found >= 10, (
        f"only {found} dataclasses found across the core package; the scan has "
        "stopped finding them and would pass over anything"
    )


def test_the_frozen_scan_asks_the_question_it_thinks_it_asks() -> None:
    """The control. The scan above reports nothing, and so does a broken one.

    A bare `@dataclass` parses as a `Name`, not a `Call`, so the frozen test
    has to handle both shapes or it reads the un-parameterized decorator -- the
    one omission that matters -- as having no `frozen` keyword by accident
    rather than by test.
    """
    bare = ast.parse("from dataclasses import dataclass\n\n@dataclass\nclass Loose:\n    a: int\n")
    node = next(n for n in ast.walk(bare) if isinstance(n, ast.ClassDef))
    decorator = node.decorator_list[0]
    assert isinstance(decorator, ast.Name), "a bare @dataclass no longer parses as a Name"

    parameterized = ast.parse(
        "from dataclasses import dataclass\n\n@dataclass(slots=True)\nclass Loose:\n    a: int\n"
    )
    other = next(n for n in ast.walk(parameterized) if isinstance(n, ast.ClassDef))
    assert isinstance(other.decorator_list[0], ast.Call)


def test_mutating_a_frozen_result_fails() -> None:
    """The mutation attempt the criterion asks for, on the type it is about.

    Routed through `Any` rather than suppressed: "mypy --strict with no ignored
    errors" is itself an acceptance criterion, and a `type: ignore` in the file
    asserting the contract would be that criterion holding everywhere except
    here.
    """
    result = _result(Status.APPLICABLE, "supported")
    with pytest.raises(dataclasses.FrozenInstanceError):
        cast(Any, result).verdict = "unsupported"


def _final_constants(module_name: str) -> list[str]:
    """Module-level names annotated `Final`, read from the source.

    `typing.Final` leaves no runtime marker, so the annotation has to be read
    from the syntax. That is also the honest scope: the criterion is about what
    the source declares constant, and this asserts the declaration is backed by
    a value that cannot be mutated.
    """
    path = CORE / f"{module_name.rsplit('.', 1)[1]}.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            annotation = ast.unparse(node.annotation)
            if annotation == "Final" or annotation.startswith("Final["):
                names.append(node.target.id)
    return names


def _is_immutable(value: object) -> bool:
    """Whether a value backs a `Final` declaration or merely wears one.

    The scalar types plus the two immutable containers, and **a bare
    `object()`**, which joined on 2026-09-09 when `_ABSENT` was added as the
    sentinel for "this run log does not carry that blob". A bare `object()` has
    no instance dictionary, so attribute assignment on it raises -- immutable
    in exactly the sense this guard is about.

    `type(value) is object` rather than an `isinstance` check, and the
    difference is the whole of the widening: **every** value passes
    `isinstance(value, object)`, so admitting the sentinel that way would admit
    the list and the dict this guard exists to catch. A subclass instance
    normally does carry an instance dictionary and stays an offender.
    """
    immutable = (str, int, float, bool, bytes, tuple, frozenset, type(None))
    return isinstance(value, immutable) or type(value) is object


def test_every_final_constant_holds_a_value_that_cannot_be_mutated() -> None:
    """`Final` is a claim to a type checker; this is the claim being true.

    Scanned rather than enumerated, and asserted to have found something: a
    scan that matched nothing would pass while checking nothing, which is the
    fail-open shape the recall net in `test_document_counts.py` exists for.
    """
    checked = 0
    offenders: list[str] = []
    for name in _core_modules():
        module = importlib.import_module(name)
        for constant in _final_constants(name):
            value = getattr(module, constant)
            checked += 1
            if not _is_immutable(value):
                offenders.append(f"{name}.{constant} is {type(value).__name__}")
    assert not offenders, (
        "constants declared Final whose value is mutable anyway:\n  " + "\n  ".join(offenders)
    )
    assert checked >= 8, (
        f"only {checked} Final constants found across {len(_core_modules())} core modules; "
        "the scan has stopped finding them and would pass over anything"
    )


def test_the_sentinel_allowance_would_notice_a_mutable_value_wearing_one() -> None:
    """The widening, held to being narrow.

    Admitting a bare `object()` is one keystroke away from admitting
    everything: `isinstance(value, object)` is true of the list and the dict
    this guard exists to catch, and the two readings are indistinguishable
    until something mutable is put in front of them. So the allowance is driven
    both ways here rather than trusted -- the sentinel passes, and a subclass
    instance, a list and a dict each still fail.
    """

    class _Sentinelish:
        """An `object` subclass, which is what a careless widening would admit."""

    assert _is_immutable(object()), "the sentinel idiom no longer backs a Final declaration"
    assert not _is_immutable(_Sentinelish()), (
        "an object *subclass* passes the allowance, so `type(value) is object` has been "
        "relaxed to an isinstance check and every mutable constant now passes"
    )
    assert not _is_immutable([]), "a list passes the allowance"
    assert not _is_immutable({}), "a dict passes the allowance"


def test_mutating_a_final_tuple_constant_fails() -> None:
    """The mutation attempt, on a constant rather than on an instance."""
    with pytest.raises(TypeError):
        cast(list[Status], STATUSES)[0] = Status.REFUSED


# --------------------------------------------------------------------------
# Provenance
# --------------------------------------------------------------------------


def test_every_result_carries_all_three_provenance_values() -> None:
    """The stamp, at the level a single result can assert it.

    The count-of-results-missing-any-of-the-three criterion is asserted over a
    real run once the engine exists; this asserts the shape makes omission
    impossible rather than merely unusual -- there is no default and no `None`.
    """
    result = _result(Status.APPLICABLE, "supported")
    assert result.provenance.rubric_version
    assert result.provenance.corpus_version
    assert result.provenance.artifact_hash

    fields = {field.name for field in dataclasses.fields(Provenance)}
    assert fields == {"rubric_version", "corpus_version", "artifact_hash"}
    assert all(
        field.default is dataclasses.MISSING and field.default_factory is dataclasses.MISSING
        for field in dataclasses.fields(Provenance)
    ), "a provenance field has a default, so a result can carry a stamp nobody supplied"
