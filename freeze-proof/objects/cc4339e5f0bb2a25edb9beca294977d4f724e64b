"""Rolling N repetitions into something a reader and a gate can both use.

Phase 3 deliberately built none of this (D124). `evaluate_call` returns one
`JudgedOutcome` per repetition and no aggregation, because **first**, **modal**
and **worst** are three different claims about what N means, and choosing one
inside the engine would have answered P4's question in a helper.

This is P4 answering it, and the answer has two halves that are easy to conflate.

**What a reader gets is the distribution.** The requirement says so: "WHILE
reporting a judged dimension evaluated at N>1, the system SHALL report the
verdict distribution across those repetitions rather than a single verdict." A
call whose ten repetitions split 6/4 is a different fact about this rubric from
one that came back ten for ten, and a report that showed one verdict for both
would be hiding the measurement N exists to make.

**What a gate gets is one verdict per call, and it is the modal one.** The
alternatives are worse in ways that are not symmetric:

* **first** discards N-1 samples, which makes N decorative -- the rubric would
  be paying for ten calls to use one.
* **worst** makes a single flip in ten fail the call, so raising N makes a
  dimension strictly more likely to fail. The measurement would be moving the
  verdict, which is the one thing an evaluator must not do.
* **modal** is what the distribution's own shape says, and it is stable under
  N: a verdict that holds for six of ten holds for six of twenty.

**A tie is not agreement, and it resolves toward the negative pole.** Five for
`addressed` and five for `unaddressed` is an evaluator that could not decide,
and the two available readings are "record that nothing went wrong" and "record
that something did". Recording nothing is the fail-open: it turns an unresolved
measurement into a pass, on a tier whose whole thesis is that failure modes must
not be reported as one thing. Ties are counted and reported separately, so a
reader is never left inferring one from a rate.

**A tie with another verdict the entry declares violating resolves to that
verdict, for the same reason** (D160). `J-concerns-addressed` counts
`partially_addressed` against its gate, so five for `addressed` and five for
`partially_addressed` is the same undecided evaluator, and scale order would
have recorded it as a pass.

**A tie that involves no violating verdict** cannot change the gate, and it is
resolved by scale order so the report is deterministic -- the rubric declares
its scale in order, and the alternative is a verdict that depends on which
repetition came back first.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from harness.core.result import Status
from harness.core.rubric import Gate, RubricEntry, RubricSchemaError

if TYPE_CHECKING:
    # For annotations only. The engine imports `_modal` from here, so that the
    # synthesis is shown the headline this module publishes (D154), and an
    # import of the engine at run time would make the two modules a cycle.
    from harness.judge.engine import JudgedOutcome


@dataclass(frozen=True, slots=True)
class CallRollup:
    """One entry's N repetitions against one call."""

    entry: RubricEntry
    call_id: str
    distribution: tuple[tuple[str, int], ...]
    """Verdict to count, in the entry's declared scale order. **Every applicable
    repetition is in here**, including the ones that disagree, which is what the
    requirement asks a report to show."""

    statuses: tuple[tuple[str, int], ...]
    """Status to count, for the repetitions that produced no verdict."""

    unresolved_dimensions: tuple[str, ...]
    """Identifiers a synthesis rested on that produced no result for this call.
    Reported as a defect and carried here so the report does not have to walk
    the outcomes again."""

    @property
    def applicable(self) -> int:
        return sum(count for _, count in self.distribution)

    @property
    def verdict(self) -> str | None:
        """The modal verdict, or `None` when nothing was applicable.

        `None` is not a verdict and is not a pass: it says this entry produced
        no verdict for this call, which the statuses beside it explain.
        """
        if not self.distribution:
            return None
        return _modal(self.distribution, self.entry)

    @property
    def tied(self) -> bool:
        """Whether the top of the distribution is shared.

        Reported rather than resolved silently. A tie is a fact about how well
        this entry separates a case, and it is exactly the fact a single modal
        verdict destroys.
        """
        if len(self.distribution) < 2:
            return False
        counts = sorted((count for _, count in self.distribution), reverse=True)
        return counts[0] == counts[1]

    @property
    def violated(self) -> bool:
        """Whether this call counts against the gate: its modal verdict is one the
        entry declares violating, which is the negative pole unless the entry
        declares more (D160)."""
        return self.verdict in self.entry.violating


def _modal(distribution: Sequence[tuple[str, int]], entry: RubricEntry) -> str:
    """The most-repeated verdict, with ties resolved as the module docstring says.

    A named function rather than an expression inside `verdict`, so a control
    can drive the tie rule directly instead of re-implementing it -- which is
    the shape D121 found in six controls, every one of them measuring nothing.
    """
    top = max(count for _, count in distribution)
    tied = [verdict for verdict, count in distribution if count == top]
    if entry.negative in tied:
        return entry.negative
    # The pole is answered above, so this names only the verdicts the entry adds to
    # it (D160) -- which keeps each half of the rule provable on its own.
    for member in entry.violating:
        if member != entry.negative and member in tied:
            return member
    for member in entry.scale:
        if member in tied:
            return member
    # Unreachable: every verdict in the distribution came through
    # `validate_result`, which refuses one outside the declared scale.
    raise RubricSchemaError(  # pragma: no cover
        f"rubric entry {entry.id!r}: a verdict outside the declared scale reached the roll-up"
    )


def outcome_text(call: CallRollup) -> str:
    """What one entry's repetitions returned on one call, as a reader sees it.

    The verdicts in scale order with a tie marked, then **every result that
    produced no verdict**, by status. The report and the command line print this
    one text: until the audit of 2026-09-12 each kept its own copy, and both
    printed a call's statuses only when it had no verdict at all, so a call with
    nine verdicts and one `errored` repetition showed the nine and hid the one
    (P4-1, D158).
    """
    spread = ", ".join(f"{name} x{count}" for name, count in call.distribution)
    if spread and call.tied:
        spread += " (tied)"
    statuses = ", ".join(f"{name} x{count}" for name, count in call.statuses)
    if spread and statuses:
        return f"{spread}; {statuses}"
    return spread or statuses or "--"


@dataclass(frozen=True, slots=True)
class JudgedEntryRollup:
    """One judged entry over every call, with its gate applied."""

    entry: RubricEntry
    calls: tuple[CallRollup, ...]

    @property
    def applicable(self) -> int:
        """**Calls, not repetitions.** The unit a rate is about is the call: a
        call either has the defect or it does not, and dividing by repetitions
        would weight one call ten times in its own rate -- which is the shape
        `DuplicateCallError` refuses, arriving through a legitimate door."""
        return sum(1 for call in self.calls if call.verdict is not None)

    def result_count(self, status: Status) -> int:
        """Results of this status across every call: one per repetition that
        produced no verdict, and one per call a precondition excluded.

        **Results, where `applicable` and the rate count calls** (D158). This
        counted calls whose repetitions were *all* of one status until the audit
        of 2026-09-12, so a call with nine verdicts and one `errored` repetition
        was counted under no status -- while the docstring said it was visible in
        its own row, where neither renderer printed it (P4-1).
        """
        return sum(
            count for call in self.calls for name, count in call.statuses if name == status.value
        )

    @property
    def violations(self) -> int:
        return sum(1 for call in self.calls if call.violated)

    @property
    def tied(self) -> tuple[str, ...]:
        """Calls whose modal verdict was reached over a tie."""
        return tuple(call.call_id for call in self.calls if call.tied)

    @property
    def unresolved_dimensions(self) -> tuple[tuple[str, str], ...]:
        """(call id, identifier) for every citation of a dimension that produced
        no result. The requirement's word for these is *defect*."""
        return tuple(
            (call.call_id, identifier)
            for call in self.calls
            for identifier in call.unresolved_dimensions
        )

    @property
    def pass_rate(self) -> float | None:
        """`None` when no call produced a verdict, which is not the same as zero.

        The deterministic roll-up draws the same distinction and for the same
        reason: a rate of 0.0 says every call violated; `None` says none was
        judged. Reporting the second as the first fails a gate on a dimension
        that never ran.
        """
        if not self.applicable:
            return None
        return (self.applicable - self.violations) / self.applicable

    @property
    def measured_nothing(self) -> bool:
        """Whether this entry produced no verdict **and it was not because the
        dimension did not apply**.

        `OB-14`'s question -- *does a judged run of refusals count as having
        run* -- answered without a threshold, which is what that obligation
        said the alternative to one had to be. The question is not *how many
        refusals are too many*; it is whether anything was measured. A
        dimension with nine refusals and one verdict measured something, badly,
        and its counts say so. A dimension with nothing but refusals measured
        nothing, and reporting that as a clean run is W11's fail-open in the
        line a CI job reads.

        A dimension that produced no verdict because it applied to no call is a
        different thing and is not this: nothing failed, and the precondition
        said so before any call was issued.
        """
        if self.applicable:
            return False
        return any(
            call.verdict is None
            and any(name != Status.NOT_APPLICABLE.value for name, _ in call.statuses)
            for call in self.calls
        )

    @property
    def gate_failed(self) -> bool:
        """A rate gate below its threshold. An absolute gate cannot get here.

        The loader refuses `tier: judge` with `gate: absolute` by name, because
        an absolute gate must never depend on a live model call -- so an entry
        reaching this property with one did not come through the loader.
        """
        if self.entry.gate is Gate.ABSOLUTE:  # pragma: no cover - refused by the loader
            raise RubricSchemaError(
                f"rubric entry {self.entry.id!r}: a judged entry declared an absolute gate and "
                "reached the roll-up. The loader refuses that shape."
            )
        rate = self.pass_rate
        if rate is None:
            return False
        if self.entry.threshold is None:
            raise RubricSchemaError(
                f"rubric entry {self.entry.id!r}: a rate gate reached the roll-up with no "
                "threshold, so it was not built by the loader that refuses that shape."
            )
        return rate < self.entry.threshold


def roll_up_judged(
    outcomes: Sequence[JudgedOutcome], entries: Sequence[RubricEntry]
) -> tuple[JudgedEntryRollup, ...]:
    """Per entry, per call, in the order the entries were given.

    Entries are passed in rather than read from a rubric, so this rolls up
    exactly what ran -- a run that aborted part-way has outcomes for some
    entries and none for others, and a roll-up built from the rubric would
    invent empty rows for the ones that never started.
    """
    rollups: list[JudgedEntryRollup] = []
    for entry in entries:
        mine = [o for o in outcomes if o.result.entry_id == entry.id]
        by_call: dict[str, list[JudgedOutcome]] = {}
        for outcome in mine:
            by_call.setdefault(outcome.result.call_id, []).append(outcome)

        calls: list[CallRollup] = []
        for call_id in sorted(by_call):
            group = by_call[call_id]
            verdicts = Counter(o.result.verdict for o in group if o.result.verdict is not None)
            statuses = Counter(o.result.status.value for o in group if o.result.verdict is None)
            calls.append(
                CallRollup(
                    entry=entry,
                    call_id=call_id,
                    # Scale order, not count order: the report reads left to
                    # right and a distribution that reordered itself with the
                    # data would make two calls incomparable at a glance.
                    distribution=tuple(
                        (member, verdicts[member]) for member in entry.scale if verdicts[member]
                    ),
                    statuses=tuple(sorted(statuses.items())),
                    unresolved_dimensions=tuple(
                        identifier for o in group for identifier in o.unresolved_dimensions
                    ),
                )
            )
        rollups.append(JudgedEntryRollup(entry=entry, calls=tuple(calls)))
    return tuple(rollups)
