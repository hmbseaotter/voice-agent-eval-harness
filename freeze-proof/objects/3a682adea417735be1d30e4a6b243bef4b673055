"""What a check is, how it returns a result, and how the engine finds it.

Three decisions are encoded here rather than left to each check author.

**A check cannot produce an unstamped result.** It does not construct a
`Result`; it asks a `ResultBuilder` that already holds the entry, the call and
the provenance triple. "Every result carries the rubric version, the corpus
version and the extraction-artifact hash" is then a property of the type rather
than of a count somebody runs afterwards -- there is no path to a result that
omits it. W30 is a tier with no run provenance at all, in a project whose
practice was diffing two runs.

**A check does not spell its own verdicts.** `satisfied()` and `violated()`
resolve to the entry's declared poles, so the strings live in the rubric and
nowhere else. A check that wrote `"supported"` would be a check whose scale is
in Python, and renaming the scale in the rubric would produce a verdict outside
it -- caught, but caught late and for the wrong reason.

**The registry is explicit.** Checks are registered by a function that lists
them, not by import side effects. A decorator-populated registry makes "the
known checks" depend on which modules happened to be imported, so a rubric
entry naming an unregistered check is refused or accepted according to import
order -- and the refusal is one of the four the requirement enumerates.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol

from harness.core.context import CheckContext
from harness.core.result import Provenance, Result, Status
from harness.core.rubric import ParamView, RubricEntry


class RegistryError(Exception):
    """A check key that is registered twice, or looked up and not found."""


@dataclass(frozen=True, slots=True)
class ResultBuilder:
    """The only way a check produces a result.

    Frozen and per-(entry, call): it carries the identity and the stamp so the
    check supplies only the finding.
    """

    entry: RubricEntry
    call_id: str
    provenance: Provenance

    def _build(
        self,
        status: Status,
        verdict: str | None,
        evidence: Sequence[str],
        *,
        missing_ground_truth: str | None = None,
        detail: str | None = None,
    ) -> Result:
        return Result(
            entry_id=self.entry.id,
            call_id=self.call_id,
            status=status,
            verdict=verdict,
            evidence=tuple(evidence),
            provenance=self.provenance,
            missing_ground_truth=missing_ground_truth,
            detail=detail,
        )

    def _pole(self, *, negative: bool) -> str:
        positive = self.entry.positive
        if len(self.entry.scale) != 2 or len(positive) != 1:
            raise RegistryError(
                f"rubric entry {self.entry.id!r}: satisfied()/violated() resolve the two poles "
                f"of a two-member scale, and this entry declares {len(self.entry.scale)} "
                f"({', '.join(self.entry.scale)}). Use applicable() with an explicit verdict."
            )
        return self.entry.negative if negative else positive[0]

    def satisfied(self, evidence: Sequence[str] = ()) -> Result:
        """The positive pole of a two-member scale, named by the entry."""
        return self._build(Status.APPLICABLE, self._pole(negative=False), evidence)

    def violated(self, evidence: Sequence[str]) -> Result:
        """The negative pole. Evidence is not optional here and the signature
        says so: a negative verdict a reader cannot audit is an assertion, not
        a finding, and `validate_result` refuses one with an empty list."""
        return self._build(Status.APPLICABLE, self._pole(negative=True), evidence)

    def applicable(self, verdict: str, evidence: Sequence[str] = ()) -> Result:
        """An explicit verdict, for a scale with more than two members."""
        return self._build(Status.APPLICABLE, verdict, evidence)

    def not_applicable(self, detail: str) -> Result:
        """The check's precondition did not occur in this call.

        Distinct from `unevaluable`: nothing is missing, there is simply
        nothing to judge. W11 is the cost of conflating them -- one value that
        was both the fail-open default and "no ground truth existed".
        """
        return self._build(Status.NOT_APPLICABLE, None, (), detail=detail)

    def unevaluable(self, missing_ground_truth: str, detail: str) -> Result:
        """The check applies and the corpus supplies nothing to judge against.

        A finding against the corpus rather than against the call, and the
        missing reference is required -- `Result` refuses a bare one.
        """
        return self._build(
            Status.UNEVALUABLE,
            None,
            (),
            missing_ground_truth=missing_ground_truth,
            detail=detail,
        )

    def errored(self, detail: str) -> Result:
        return self._build(Status.ERRORED, None, (), detail=detail)

    def refused(self, detail: str) -> Result:
        """The model declined to answer (D23).

        Added at P3, when the status became reachable. It was declared at P2
        because the channel freezes there and a status added later is a channel
        changed later -- but the builder had no way to produce one, so the
        judged engine's first draft reached into `_build` directly. A private
        method called from another module is a contract nobody declared, and
        the alternative to declaring it is that every future caller reaches in
        too.

        Carries no evidence and no verdict, like the other three non-applicable
        constructors. A refusal is not a judgment about the call.
        """
        return self._build(Status.REFUSED, None, (), detail=detail)


class Check(Protocol):
    """A deterministic check.

    Receives the three populations, its entry's parameters, and the builder.
    Receives no path, no clock and no network: everything it may read is in
    `context`, and everything it may be configured by is in `params`.
    """

    def __call__(
        self, context: CheckContext, params: ParamView, builder: ResultBuilder
    ) -> Result: ...


CheckFn = Callable[[CheckContext, ParamView, ResultBuilder], Result]


class Registry:
    """Check key to implementation.

    Built explicitly by a function that lists its contents, so `known_checks()`
    is the same set whatever has been imported. The rubric loader compares an
    entry's `check` against it, and that refusal is one of the four the
    requirement enumerates -- a set that varied with import order would make
    the refusal depend on something no rubric author can see.
    """

    def __init__(self) -> None:
        self._checks: dict[str, CheckFn] = {}

    def register(self, key: str, check: CheckFn) -> None:
        if key in self._checks:
            raise RegistryError(f"check {key!r} is registered twice")
        if not key or key.strip() != key:
            raise RegistryError(f"check key {key!r} is empty or carries surrounding whitespace")
        self._checks[key] = check

    def get(self, key: str) -> CheckFn:
        try:
            return self._checks[key]
        except KeyError:
            raise RegistryError(
                f"check {key!r} is not registered. Known: {', '.join(self.keys()) or '(none)'}"
            ) from None

    def keys(self) -> tuple[str, ...]:
        """Sorted, so a refusal message and a rubric review read the same order
        on every machine."""
        return tuple(sorted(self._checks))

    def __len__(self) -> int:
        return len(self._checks)

    def __contains__(self, key: object) -> bool:
        return key in self._checks
