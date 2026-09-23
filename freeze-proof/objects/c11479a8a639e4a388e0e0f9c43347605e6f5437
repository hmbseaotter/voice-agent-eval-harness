"""Running the deterministic tier: entries over calls, results out.

The engine is the one place that decides which entries execute, so
`--tier assert` is a single filter rather than a condition repeated at three
call sites. W26 is the version with no supported way to run the deterministic
tier alone, where any full-rubric invocation made live calls.

Three things happen around every check, and each closes a requirement:

* the result is validated against its entry -- verdict inside the declared
  scale, evidence present on the declared negative pole;
* the entry's `ParamView` is checked for parameters the check never read
  (D109), so a value in the rubric that describes nothing fails the entry;
* an exception out of a check becomes `status: errored` for that result and
  the run continues, rather than taking the run down. A check that raises is a
  defect in the check, and losing the other sixty results to it would make the
  tier harder to fix than to abandon.

**Order is fixed and total.** Results come back sorted by (call, entry), never
in registry or dictionary order, because Tier A output is asserted
byte-identical across runs from P4 and an order that depends on iteration is
an order that will differ.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from harness.core.context import CheckContext
from harness.core.registry import Registry, RegistryError, ResultBuilder
from harness.core.result import Provenance, Result, Status
from harness.core.rubric import (
    CheckTier,
    Gate,
    Rubric,
    RubricEntry,
    RubricSchemaError,
    validate_params_consumed,
    validate_result,
)


class DuplicateCallError(Exception):
    """Two contexts carrying one `call_id`.

    The population a rate gate divides by is "the calls this entry applied to",
    and that is only a population if each call appears once. Raised rather than
    de-duplicated: which of the two contexts is the real one is not a question
    the engine can answer, and quietly keeping the first would make the run
    depend on the order the corpus happened to be read in.
    """

    def __init__(self, call_ids: Sequence[str]) -> None:
        super().__init__(
            "more than one context carries the same call_id: "
            + ", ".join(call_ids)
            + ". Every entry would produce one result per context, so each of these calls "
            "would be weighted twice in its entry's pass rate."
        )
        self.call_ids = tuple(call_ids)


@dataclass(frozen=True, slots=True)
class RunReport:
    """Every result of one run, and what the gates make of them."""

    results: tuple[Result, ...]
    tier: CheckTier

    def for_entry(self, entry_id: str) -> tuple[Result, ...]:
        return tuple(result for result in self.results if result.entry_id == entry_id)

    def for_call(self, call_id: str) -> tuple[Result, ...]:
        return tuple(result for result in self.results if result.call_id == call_id)

    @property
    def entry_ids(self) -> tuple[str, ...]:
        """Which entries produced a result. The tier-selector criterion is
        asserted on this rather than on a call count, because a rubric with no
        judged entry satisfies "zero model calls" whatever the selector did."""
        seen: list[str] = []
        for result in self.results:
            if result.entry_id not in seen:
                seen.append(result.entry_id)
        return tuple(seen)


def run_entry(
    entry: RubricEntry,
    context: CheckContext,
    provenance: Provenance,
    registry: Registry,
) -> Result:
    """One entry against one call, with both post-conditions applied.

    A check raising becomes `errored` **for that result**, carrying the
    exception's text. Rubric-shape defects are not: a verdict outside its
    scale, an unread parameter, an unevidenced negative pole, or `satisfied()`
    called on a scale with more than two members. The first three are checked
    after the call and were never caught; the fourth is raised from inside it
    and was, which made one class of defect behave two ways depending on where
    in the call it surfaced.
    """
    view = entry.view()
    builder = ResultBuilder(entry=entry, call_id=context.call_id, provenance=provenance)
    try:
        result = registry.get(entry.check)(context, view, builder)
    # `satisfied()` and `violated()` resolve the two poles of a two-member
    # scale and raise `RegistryError` when the entry declares three. That is
    # the same class as the two validators below -- a defect in the rubric or
    # the check, which the docstring says must stop the run -- and it was the
    # one member of that class raised *inside* this try, so it became one
    # `errored` result per call and the run reported sixty-odd others as
    # though the entry had been evaluated. Re-raised, so all three behave the
    # same way.
    except RegistryError:
        raise
    # Broad on purpose: this is the boundary between a check's code and the
    # run. Narrowing it would mean listing the exceptions a check might
    # raise, which nobody can know, and the one it did not list would take
    # the run down with sixty results already computed.
    except Exception as exc:
        return builder.errored(f"{type(exc).__name__}: {exc}")

    validate_result(result, entry)
    validate_params_consumed(view, entry)
    return result


def run(
    rubric: Rubric,
    contexts: Sequence[CheckContext],
    provenance: Provenance,
    registry: Registry,
    *,
    tier: CheckTier,
) -> RunReport:
    """Every entry of one tier against every call, in a fixed order.

    The tier filter is here and only here. An entry of another tier is not
    executed and produces no result -- which is the half of the `--tier assert`
    requirement that "issues no model call" does not cover.
    """
    entries = rubric.for_tier(tier)
    seen: dict[str, int] = {}
    for context in contexts:
        seen[context.call_id] = seen.get(context.call_id, 0) + 1
    repeated = sorted(call_id for call_id, count in seen.items() if count > 1)
    if repeated:
        # A duplicated id is not a duplicated result: every entry produces one
        # result per context, so the call is weighted twice in every rate gate
        # and appears twice in every firing set, silently. Two transcript files
        # declaring the same `call_id` is all it takes, and nothing upstream
        # compares them.
        raise DuplicateCallError(repeated)
    results = [
        run_entry(entry, context, provenance, registry)
        for context in sorted(contexts, key=lambda c: c.call_id)
        for entry in sorted(entries, key=lambda e: e.id)
    ]
    return RunReport(results=tuple(results), tier=tier)


@dataclass(frozen=True, slots=True)
class EntryRollup:
    """One entry's results, counted by status, with its gate applied."""

    entry: RubricEntry
    applicable: int
    not_applicable: int
    unevaluable: int
    errored: int
    refused: int
    violations: int
    """`applicable` results whose verdict is the entry's declared negative
    pole."""

    @property
    def denominator(self) -> int:
        """Only `applicable` results. Every other status is reported beside the
        rate rather than folded into it -- W21 is a tier where `threshold` was
        consumed by no logic and no rate was computed anywhere."""
        return self.applicable

    @property
    def pass_rate(self) -> float | None:
        """`None` when nothing was applicable, which is not the same as zero.

        A rate of 0.0 says every applicable result violated; `None` says there
        were none. Reporting the second as the first would fail a gate on a
        dimension that never ran.
        """
        if not self.applicable:
            return None
        return (self.applicable - self.violations) / self.applicable

    @property
    def gate_failed(self) -> bool:
        """An absolute gate fails on one violation. A rate gate fails when the
        rate is below its threshold, and never on an empty denominator."""
        if self.entry.gate is Gate.ABSOLUTE:
            return self.violations > 0
        rate = self.pass_rate
        if rate is None:
            return False
        if self.entry.threshold is None:
            # Fail closed and say what it means. The loader refuses a rate gate
            # with no threshold, so an entry reaching here without one did not
            # come through the loader -- and comparing against nothing while
            # reporting a pass is W21 exactly.
            raise RubricSchemaError(
                f"rubric entry {self.entry.id!r}: a rate gate reached the roll-up with no "
                "threshold, so it was not built by the loader that refuses that shape."
            )
        return rate < self.entry.threshold


def roll_up(report: RunReport, rubric: Rubric) -> tuple[EntryRollup, ...]:
    """Per entry, in rubric order, for every entry the tier executed."""
    rollups: list[EntryRollup] = []
    for entry in rubric.for_tier(report.tier):
        results = report.for_entry(entry.id)
        rollups.append(
            EntryRollup(
                entry=entry,
                applicable=sum(1 for r in results if r.status is Status.APPLICABLE),
                not_applicable=sum(1 for r in results if r.status is Status.NOT_APPLICABLE),
                unevaluable=sum(1 for r in results if r.status is Status.UNEVALUABLE),
                errored=sum(1 for r in results if r.status is Status.ERRORED),
                refused=sum(1 for r in results if r.status is Status.REFUSED),
                violations=sum(1 for r in results if r.verdict == entry.negative),
            )
        )
    return tuple(rollups)
