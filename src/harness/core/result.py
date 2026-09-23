"""The Result contract: the five-value status channel, and what stamps it.

**This channel freezes at P2.** Every later phase reads it, so the two
properties it exists for are enforced here at construction rather than checked
somewhere downstream:

* `status` is drawn from exactly five values, **validated at runtime** and not
  only by the type checker. Statuses arrive from YAML and from a run log at P3,
  where `mypy --strict` has nothing to say, and W11 is what a status channel
  costs when its members are assumed: `not_applicable` was the fail-open
  default *and* absorbed the state `unevaluable` now holds, so a parser
  regression could turn the whole absolute-gate tier green with no alarm.

* `verdict` is populated **if and only if** `status` is `applicable`. Both
  implications, because that is what "if and only if" means and because the
  specification's criteria bought only one of them until D104 -- a harness
  returning `applicable` with no verdict satisfied every criterion while
  contradicting the requirement they were written from.

`unevaluable` additionally names the ground-truth reference that was missing.
A bare `unevaluable` is indistinguishable from a check that gave up, and the
requirement says the system SHALL record that identifier; enforcing it at
construction is what stops "SHALL record" becoming "records where somebody
remembered to".

**What is deliberately not enforced here.** Two more contract rules need the
rubric entry, which a `Result` does not carry: that a verdict is a member of
its entry's declared scale, and that the scale member declared *negative* for
that entry carries non-empty evidence. Both live in `harness.core.rubric`
beside the entry that declares the scale. Splitting them is not tidiness --
W12 is an evidence-on-failure invariant that covered two literal verdict
strings and missed the negative pole of six of seven scales, and the fix is
that the guard reads the entry's declaration rather than a tuple somebody
typed. A guard that cannot see the declaration cannot be driven by it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final


class Status(StrEnum):
    """Why a result reads the way it does, before any verdict is considered.

    Five values, and none of them is silently another. A harness whose thesis
    is that evaluation must distinguish failure modes cannot report three of
    them as one -- so a dimension that did not apply, a dimension with nothing
    to judge against, a judge that could not produce a valid result, and a
    model that declined to answer are four different rows, not four spellings
    of "no".
    """

    APPLICABLE = "applicable"
    """The check ran and reached a verdict. The only status carrying one."""

    NOT_APPLICABLE = "not_applicable"
    """The check's precondition did not occur in this call. Nothing to judge,
    and nothing missing: an exchange check on a call with no exchange."""

    UNEVALUABLE = "unevaluable"
    """The check applied and the corpus supplies no ground truth to judge it
    against. A finding against the corpus, not against the call -- which is why
    it names the reference that was missing rather than resolving to a pass."""

    ERRORED = "errored"
    """The check could not produce a valid result: a retry budget exhausted, a
    response truncated at `max_tokens`. Reached at P3; declared now because the
    channel freezes here and a status added later is a channel changed later."""

    REFUSED = "refused"
    """The model declined to answer (D23). Neither an error nor an absence, and
    an expected event on a corpus that seeds prompt injection by design."""


#: The channel, in the order the specification writes it. Read by the roll-up
#: and by the validator below rather than re-typed at either site: a second copy
#: of a closed vocabulary is a second thing to keep current, and this project
#: has already paid for that once in the findings key list.
STATUSES: Final[tuple[Status, ...]] = (
    Status.APPLICABLE,
    Status.NOT_APPLICABLE,
    Status.UNEVALUABLE,
    Status.ERRORED,
    Status.REFUSED,
)

#: Statuses excluded from a rate's denominator. `applicable` is the whole
#: denominator; every other status is reported as its own count alongside the
#: rate. W21 is the version of this where `threshold` and `severity` were
#: consumed by no logic and no rate was computed anywhere.
NON_RATE_STATUSES: Final[tuple[Status, ...]] = tuple(
    status for status in STATUSES if status is not Status.APPLICABLE
)


class ResultError(Exception):
    """Base for every refusal to construct a result."""


class StatusNotInChannelError(ResultError):
    """A status outside the five.

    Named rather than coerced. A value nothing defines is not a disputed
    disposition, it is a token every downstream check reasons about while
    comparing against nothing -- the same argument `Outcome` records for the
    call record's own vocabulary.
    """

    def __init__(self, entry_id: str, offending: object) -> None:
        super().__init__(
            f"{entry_id}: status {offending!r} is not one of "
            f"{', '.join(status.value for status in STATUSES)}"
        )
        self.entry_id = entry_id
        self.offending = offending


class VerdictChannelError(ResultError):
    """The `verdict`-populated-iff-`applicable` rule, in either direction."""

    def __init__(self, entry_id: str, status: Status, verdict: str | None) -> None:
        if status is Status.APPLICABLE:
            detail = "status is 'applicable' and verdict is absent"
        else:
            detail = f"status is {status.value!r} and verdict is {verdict!r} rather than absent"
        super().__init__(
            f"{entry_id}: {detail}. A verdict is populated if and only if the status is "
            "'applicable'; both directions hold."
        )
        self.entry_id = entry_id
        self.status = status
        self.verdict = verdict


class MissingGroundTruthReferenceError(ResultError):
    """An `unevaluable` result that does not say what was missing."""

    def __init__(self, entry_id: str) -> None:
        super().__init__(
            f"{entry_id}: status 'unevaluable' carries no missing ground-truth reference. "
            "A bare 'unevaluable' cannot be told from a check that gave up, and the "
            "requirement is that the identifier of the missing reference is recorded."
        )
        self.entry_id = entry_id


@dataclass(frozen=True, slots=True)
class Provenance:
    """What a result was computed from, so a report can be recomputed from it.

    Three values, all required. The extraction artifact's hash is the one that
    makes the claim checkable rather than asserted: a reader recomputes it from
    the corpus and finds out whether this result describes the corpus in front
    of them. W30 is a tier with no run provenance at all -- no run id, no
    rubric version stamp -- in a project whose practice was diffing two runs.
    """

    rubric_version: str
    corpus_version: str
    artifact_hash: str

    def __post_init__(self) -> None:
        """Refuse a blank field.

        The registry's docstring said "there is no path to a result that omits
        it", and that was true of `None` and false of `""`. A `CORPUS_VERSION`
        file holding only a newline stamped every result with an empty string,
        the run printed `missing a provenance value: 555`, and it continued --
        the exit 1 that followed came from a gate, so a quiet rubric would have
        exited 0 with an unrecomputable report.

        `test_every_result_carries_all_three_provenance_values` asserts the
        fields have no defaults, which is the neighbor of this and not this: a
        dataclass with no default still constructs from three empty strings.
        """
        blank = [
            name
            for name in ("rubric_version", "corpus_version", "artifact_hash")
            if not getattr(self, name).strip()
        ]
        if blank:
            raise ValueError(
                f"provenance field(s) empty: {', '.join(blank)}. A result stamped with a "
                "blank value cannot be recomputed from, which is the whole reason the stamp "
                "exists."
            )


@dataclass(frozen=True, slots=True)
class Result:
    """One check's outcome for one call.

    Frozen, because a result a later stage can edit is a result the roll-up can
    quietly "fix". The evidence list is a tuple for the same reason: the
    fragments a check cites are what a reader audits it by.
    """

    entry_id: str
    """The rubric entry that produced this. Joins the result to its gate, its
    scale, its threshold and its `traces_to`."""

    call_id: str

    status: Status

    verdict: str | None
    """A member of the entry's declared scale, or `None`. Populated if and only
    if `status` is `applicable` -- enforced below, in both directions."""

    evidence: tuple[str, ...]
    """What the check read to reach this verdict, in stream order. Non-empty is
    required for the negative pole of the entry's scale, which is checked
    against the entry in `harness.core.rubric` because only the entry declares
    which pole is negative."""

    provenance: Provenance

    missing_ground_truth: str | None = None
    """Required when `status` is `unevaluable`, and meaningless otherwise: the
    identifier of the reference the corpus did not supply."""

    detail: str | None = None
    """Free text for a reader: why the check did not apply, what errored, what
    was refused. Never parsed, never compared, and never a substitute for one
    of the fields above."""

    def __post_init__(self) -> None:
        if not isinstance(self.status, Status):
            raise StatusNotInChannelError(self.entry_id, self.status)
        if (self.verdict is not None) != (self.status is Status.APPLICABLE):
            raise VerdictChannelError(self.entry_id, self.status, self.verdict)
        if self.status is Status.UNEVALUABLE and not (self.missing_ground_truth or "").strip():
            raise MissingGroundTruthReferenceError(self.entry_id)

    @property
    def counts_toward_rate(self) -> bool:
        """Only `applicable` results form a rate's denominator.

        A property rather than a comparison spelled out at each call site: W11
        is what happens when one site treats a non-`applicable` status as a
        pass, and there is no way to notice a single site drifting when the
        rule lives in every site rather than in one.
        """
        return self.status is Status.APPLICABLE
