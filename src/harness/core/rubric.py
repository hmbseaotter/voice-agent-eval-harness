"""The rubric: entries, schema validation, and the parameter view checks read.

The rubric is **data**, and the tier it drives reads every threshold, signal
list and inventory from it. W20 is what the alternative looks like measured:
`params` decorative for the entire deterministic tier, only the entry `id`
actually read, everything else hardcoded and in one case disagreeing with the
YAML it sat beside -- in the tier a reader studies first.

Three mechanisms hold that here, and only the first is the obvious one.

1. **Schema validation on load**, naming the offending entry. A missing gate or
   a duplicate id surfaced as a `KeyError` deep in the roll-up (W22); an entry
   is now refused where it is read, by name, with the reason.

2. **`ParamView` records every key a check reads**, so the engine can refuse an
   entry that declared a parameter nothing consumed. That turns "every
   parameter is read from the rubric" from a property a test samples into one
   the run enforces: a check that quietly stopped reading `threshold_ms` fails
   the entry rather than passing with a constant.

3. **Verdict validation against the entry's declared scale**, and the
   evidence-on-negative-pole guard driven by the entry's declared negative pole
   rather than by a literal. W12 covered two verdict strings and missed the
   negative pole of six of seven scales; W14 was that nothing validated a
   verdict against its scale anywhere. Both live here because only the entry
   declares the scale, and a guard that cannot see the declaration cannot be
   driven by it.

**A judged entry may never declare an absolute gate.** Rejected by name at load
(W13 was the version where the roll-up's absolute-gate test keyed on the literal
string `"fail"`, so declaring a judged dimension an absolute gate was a silent
no-op). **That silence is not a bug to be fixed by making the combination
effective** -- the combination is forbidden, because an absolute gate must never
depend on a live model call. A dimension has a `tier` and it has a `gate`, and
it is the *pairing* that cannot exist rather than a kind of gate; naming it as
one makes making it work sound like an option.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final

import yaml

from harness.core.result import Result, Status
from harness.core.transport import EFFORT_LEVELS, SUPPORTED_MODELS


class CheckTier(StrEnum):
    """Which tier executes this entry.

    Named `CheckTier` rather than `Tier` because `harness.core.findings.Tier` is
    a different closed vocabulary in the same package -- `defect` | `question`,
    about a finding rather than about a check. Two enums called `Tier` in one
    package is a name collision waiting for the import that gets it wrong.
    """

    ASSERT = "assert"
    """Deterministic. Plain code, no model call, byte-identical across runs."""

    JUDGE = "judge"
    """Requires a model. Declared here from P2 so the tier selector and the
    absolute-gate refusal have something real to act on; executed from P3."""


class Gate(StrEnum):
    """What a failing verdict does to the run.

    Two values, closed. A third meaning "report but never fail" was considered
    and not added: a rate gate with a threshold of zero already expresses it,
    and a gate that cannot fail is the fail-open default W11 is about, arriving
    with a name that makes it sound deliberate.
    """

    ABSOLUTE = "absolute"
    """A single negative-pole verdict fails the call and fails the run."""

    RATE = "rate"
    """The pass rate over `applicable` results is compared to `threshold`."""


#: The token an entry uses to declare, deliberately, that the design set holds
#: no call on which this check must be silent (D107). A *missing* key and a
#: `null` are both refused, because either reads as "forgot" and the whole
#: value of the field is that the absence was decided rather than defaulted.
NO_NEGATIVE_INSTANCE: Final[str] = "none"

#: Required on every entry.
REQUIRED_ENTRY_KEYS: Final[tuple[str, ...]] = (
    "id",
    "tier",
    "check",
    "gate",
    "scale",
    "negative",
    "traces_to",
    "negative_instance",
)

#: Accepted beyond the required set. `threshold` is required for a rate gate and
#: refused for an absolute one, which is a conditional the key list cannot
#: express, so it lives here and is checked below.
OPTIONAL_ENTRY_KEYS: Final[tuple[str, ...]] = (
    "threshold",
    "params",
    "negative_instance_reason",
    "description",
)

#: What a judged entry's `check` may name. A separate vocabulary from the
#: deterministic registry, because the two are different kinds of thing: a
#: deterministic check is a Python function the registry holds, and a judged
#: check names how the judged engine renders and asks. Validating a judged
#: entry against the deterministic registry would refuse every judged entry by
#: telling the author their check is not implemented, which is true of the
#: wrong registry.
#: The check key the call-level synthesis declares. Named rather than spelled
#: at four call sites, because "is this the synthesis" is asked by the renderer,
#: the schema builder, the engine's ordering and the report -- and four string
#: literals is four places for one of them to be misspelled into `False`.
SYNTHESIS_CHECK: Final[str] = "judged_synthesis"

KNOWN_JUDGE_CHECKS: Final[tuple[str, ...]] = ("judged_dimension", SYNTHESIS_CHECK)

#: Keys only a judged entry may carry. Every one of them is read -- by the
#: prompt renderer, the schema builder, the transport or the roll-up -- and an
#: `assert` entry declaring one is refused, for the same reason W20 exists: a
#: value in the rubric that describes nothing is a value a reader will believe.
#: `violating` is the one the model never sees (D160): it decides what the gate
#: counts, which is why it is a field of the entry rather than of `JudgeSpec`.
JUDGE_ENTRY_KEYS: Final[tuple[str, ...]] = (
    "model",
    "max_tokens",
    "effort",
    "repetitions",
    "question",
    "criteria",
    "scale_definitions",
    "requires_facts",
    "applies_when_facts_present",
    "violating",
)


class RubricError(Exception):
    """Base for every refusal to load or apply a rubric."""


class RubricSchemaError(RubricError):
    """A rubric that does not parse as a rubric at all."""


class EntryError(RubricError):
    """Every entry-level refusal names the entry it came from.

    A base carrying `entry_id` rather than eight unrelated exceptions, because
    the caller's job is the same in every case: print the name and stop.
    """

    def __init__(self, entry_id: str, message: str) -> None:
        super().__init__(f"rubric entry {entry_id!r}: {message}")
        self.entry_id = entry_id


class DuplicateEntryIdError(EntryError):
    def __init__(self, entry_id: str) -> None:
        super().__init__(entry_id, "duplicate id; every entry id is unique within a rubric")


class MissingGateError(EntryError):
    def __init__(self, entry_id: str) -> None:
        super().__init__(
            entry_id,
            f"no 'gate'; every entry declares one of {', '.join(g.value for g in Gate)}",
        )


class RateGateWithoutThresholdError(EntryError):
    def __init__(self, entry_id: str) -> None:
        super().__init__(
            entry_id,
            "gate is 'rate' and no 'threshold' is declared. A rate gate with no threshold "
            "compares against nothing and passes whatever the results are (W21).",
        )


class UnknownCheckKeyError(EntryError):
    def __init__(self, entry_id: str, check: str, known: tuple[str, ...]) -> None:
        super().__init__(
            entry_id,
            f"check {check!r} is not implemented. Known checks: {', '.join(known) or '(none)'}",
        )
        self.check = check


class JudgedTierWithAbsoluteGateError(EntryError):
    """The two fields are each fine and the pairing is forbidden.

    Named for the pairing rather than for a compound noun. There is no such
    thing as a judged absolute gate: a dimension has a `tier` and it has a
    `gate`, and once the combination has a name, making it work sounds like a
    feature somebody declined to build rather than a configuration that must be
    refused at load.
    """

    def __init__(self, entry_id: str) -> None:
        super().__init__(
            entry_id,
            "declares tier 'judge' with gate 'absolute'. An absolute gate fails the whole "
            "run, and must never depend on a live model call. The pairing is forbidden "
            "rather than unimplemented: declare a rate gate, or move the check to the "
            "deterministic tier.",
        )


class NegativeInstanceUndeclaredError(EntryError):
    def __init__(self, entry_id: str) -> None:
        super().__init__(
            entry_id,
            f"no 'negative_instance'. Name a design-set call on which this check must be "
            f"silent, or declare {NO_NEGATIVE_INSTANCE!r} with a "
            f"'negative_instance_reason'. A check proven only to fire has been proven "
            f"against nothing.",
        )


class VerdictNotInScaleError(EntryError):
    def __init__(self, entry_id: str, verdict: str, scale: tuple[str, ...]) -> None:
        super().__init__(
            entry_id,
            f"verdict {verdict!r} is not in the declared scale ({', '.join(scale)})",
        )
        self.verdict = verdict


class NegativePoleWithoutEvidenceError(EntryError):
    def __init__(self, entry_id: str, negative: str) -> None:
        super().__init__(
            entry_id,
            f"verdict {negative!r} is this entry's declared negative pole and the evidence "
            "list is empty. A negative verdict a reader cannot audit is an assertion, not "
            "a finding.",
        )


class MaxTokensUndeclaredError(EntryError):
    """A judged entry with no `max_tokens`, refused before any call is issued.

    Its own class rather than a generic missing-key message, because the
    specification gives it its own clause and the reason is sharper than
    "required field" (D24). `max_tokens` is a **required** Messages API
    parameter, so a missing value is not a defaulting question but an
    unissuable request -- and it is the parameter most deserving of per-entry
    control, since these prompts carry a whole transcript, the tagged fact
    population and a declared JSON schema.
    """

    def __init__(self, entry_id: str) -> None:
        super().__init__(
            entry_id,
            "declares tier 'judge' and no 'max_tokens'. It is a required Messages API "
            "parameter, so the request cannot be issued at all -- refused here, by name, "
            "rather than discovered as a 400 at the seam.",
        )


class JudgeKeyOnDeterministicEntryError(EntryError):
    """An `assert` entry carrying judged-only configuration.

    The mirror of the unread-parameter guard, one level up: a deterministic
    entry declaring `max_tokens` and an `effort` is an entry whose reader will
    believe a model is involved, and nothing would ever read either value.
    """

    def __init__(self, entry_id: str, keys: Sequence[str]) -> None:
        super().__init__(
            entry_id,
            f"declares tier 'assert' and judged-only key(s) {', '.join(keys)}. Nothing in "
            "the deterministic tier reads them, so the entry would describe behavior it "
            "does not have.",
        )
        self.keys = tuple(keys)


class UnreadParameterError(EntryError):
    def __init__(self, entry_id: str, unread: tuple[str, ...]) -> None:
        super().__init__(
            entry_id,
            f"declared parameter(s) {', '.join(unread)} were not read by the check. A "
            "parameter the check ignores is a value in the rubric that does not describe "
            "the rubric's behavior, which is W20 exactly.",
        )
        self.unread = unread


class ParamView(Mapping[str, Any]):
    """An entry's `params`, recording which keys the check actually read.

    Not a frozen dataclass, and the reason is worth stating rather than
    exempting: this is a runtime accessor, not a contract type. It has to
    accumulate observations as the check runs, and the observations are the
    product. The values it exposes are the entry's own immutable mapping; what
    changes is the set of keys that have been asked for.

    The engine reads `unread` after the check returns and refuses the entry if
    anything was declared and not consumed. That is what makes "every parameter
    is read from the rubric entry" a property of every run rather than of
    whichever parameter a mutation test happened to pick.
    """

    def __init__(self, params: Mapping[str, Any]) -> None:
        self._params: Final[Mapping[str, Any]] = MappingProxyType(dict(params))
        self._read: set[str] = set()

    def __getitem__(self, key: str) -> Any:
        self._read.add(key)
        return self._params[key]

    def __iter__(self) -> Iterator[str]:
        # Iterating is reading: a check that walks every parameter has read them
        # all, and recording otherwise would make `unread` report keys the check
        # demonstrably consumed.
        self._read.update(self._params)
        return iter(self._params)

    def __len__(self) -> int:
        return len(self._params)

    @property
    def unread(self) -> tuple[str, ...]:
        return tuple(sorted(set(self._params) - self._read))

    @property
    def declared(self) -> tuple[str, ...]:
        return tuple(sorted(self._params))


@dataclass(frozen=True, slots=True)
class JudgeSpec:
    """The judged half of an entry: what to ask, how, and how many times.

    A nested value rather than eight loose fields on `RubricEntry`, so
    `entry.judge is None` is the one question a caller asks to know which tier
    it is holding -- rather than eight optional fields that can be half-filled.

    Every field here is read on every judged call: `question`, `criteria` and
    `scale_definitions` by the prompt renderer, `requires_facts` by the fact
    renderer, `model`, `max_tokens` and `effort` by the seam, `repetitions` by
    the engine's loop. That is the same property `ParamView` enforces for the
    deterministic tier, bought here by there being no field a code path can
    skip -- and asserted by
    `test_mutating_each_judged_field_changes_what_is_sent`.
    """

    model: str
    max_tokens: int
    effort: str
    repetitions: int
    """N. Read from the entry, never defaulted -- "N repetitions, N read from
    the rubric entry" is the requirement, and a default would make the recorded
    verdict distribution a property of the code rather than of the rubric."""

    question: str
    criteria: str
    scale_definitions: Mapping[str, str]
    """One definition per scale member. A scale rendered as bare tokens asks
    the model what `partially_aligned` means, and two runs of one rubric then
    measure whatever it guessed each time."""

    requires_facts: tuple[str, ...]
    """Fact categories to render, in order. Empty means the facts section is
    omitted entirely, which is a different rendering from a named category that
    turned out to be empty."""

    applies_when_facts_present: tuple[str, ...] = ()
    """Categories that must yield at least one fact for this dimension to apply
    at all. Empty -- the default -- means the dimension applies to every call.

    D125's structural fix, and it exists because a dimension without one was
    measured answering a question it could not answer. `J-policy-alignment`
    asks whether the terms the agent stated align with **the clause this call
    retrieved**; on a call that retrieved none, "states a rule the clauses do
    not support" is unconditionally true of every term uttered, so the
    dimension came back `misaligned` on four calls it had no clause to compare
    against, reproducibly, across three live passes.

    Declared per entry rather than inferred from `requires_facts` being empty,
    because a dimension may legitimately want to judge the **absence** of
    facts: `EMPTY_CATEGORY_STATEMENT` exists so a named-but-empty category
    renders as an explicit negative rather than a silence, and inferring the
    precondition would take that away from every entry at once.

    The check runs **before the call is issued**, so a dimension that does not
    apply costs nothing. That is a consequence rather than the reason.
    """


@dataclass(frozen=True, slots=True)
class RubricEntry:
    """One rubric entry. Everything a check is allowed to know."""

    id: str
    tier: CheckTier
    check: str
    gate: Gate
    scale: tuple[str, ...]
    negative: str
    """The scale member that means "this went wrong". Declared per entry and
    read by the evidence guard, never inferred from position or spelling."""
    violating: tuple[str, ...]
    """Every verdict that counts a call against the gate, in scale order: the
    negative pole alone, unless a judged entry declares more (D160). An entry
    asking whether *every* concern was answered is answered no by its middle
    value as much as by its pole, and read the other way it caught nothing it
    traces."""
    traces_to: tuple[str, ...]
    """Finding ids this entry is meant to catch. Resolved against the findings
    document by test; a rubric that traces to nothing is a check nobody asked
    for."""
    negative_instance: str | None
    """A design-set call on which this check must be silent, or `None` when the
    entry declared `none` deliberately (D107)."""
    negative_instance_reason: str | None
    threshold: float | None
    params: Mapping[str, Any]
    description: str
    judge: JudgeSpec | None = None
    """Present exactly when `tier` is `judge`, and the one question a caller
    asks to tell the two tiers apart at the point of use."""

    @property
    def positive(self) -> tuple[str, ...]:
        return tuple(member for member in self.scale if member != self.negative)

    def view(self) -> ParamView:
        return ParamView(self.params)


@dataclass(frozen=True, slots=True)
class Rubric:
    version: str
    entries: tuple[RubricEntry, ...]

    def for_tier(self, tier: CheckTier) -> tuple[RubricEntry, ...]:
        """The entries a tier selector executes, and no others.

        The tier selector reads this rather than filtering at the call site: a
        judged entry reaching the deterministic engine is a model call the
        `--tier assert` requirement forbids, and one filter is auditable where
        three are not.
        """
        return tuple(entry for entry in self.entries if entry.tier is tier)

    def by_id(self, entry_id: str) -> RubricEntry:
        for entry in self.entries:
            if entry.id == entry_id:
                return entry
        raise RubricSchemaError(f"no rubric entry with id {entry_id!r}")


def _require_str(entry: dict[str, Any], key: str, entry_id: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value.strip():
        raise EntryError(entry_id, f"{key!r} must be a non-empty string")
    return value


def _optional_str(entry: dict[str, Any], key: str, entry_id: str) -> str:
    """An absent key is "", a present one must be a non-empty string.

    This was `str(raw.get(key, ""))`, which accepted anything and stringified
    it: `description: 42` became `"42"` and a YAML `description:` with no value
    became `"None"` -- a four-character description that reads as a word. Every
    other field in this loader refuses what it cannot use, and a field that
    silently coerces is the one a reader stops checking.
    """
    if key not in entry or entry[key] is None:
        return ""
    value = entry[key]
    if not isinstance(value, str) or not value.strip():
        raise EntryError(entry_id, f"{key!r} must be a non-empty string when present")
    return value


def _require_str_list(entry: dict[str, Any], key: str, entry_id: str) -> tuple[str, ...]:
    value = entry.get(key)
    if not isinstance(value, list) or not value:
        raise EntryError(entry_id, f"{key!r} must be a non-empty list")
    for position, item in enumerate(value, start=1):
        if not isinstance(item, str) or not item.strip():
            raise EntryError(entry_id, f"{key}[{position}] must be a non-empty string")
    return tuple(str(item) for item in value)


def _parse_judge_spec(raw: dict[str, Any], entry_id: str, scale: tuple[str, ...]) -> JudgeSpec:
    """The judged configuration, every field required and every value checked.

    Ordered so the refusal a reader gets is the one the specification names.
    `max_tokens` is tested first and by its own class, because its absence is a
    *named* refusal in the requirements rather than one of a list -- a run that
    reported "missing 'effort'" first would send a reader to the wrong clause.
    """
    if "max_tokens" not in raw:
        raise MaxTokensUndeclaredError(entry_id)
    max_tokens = raw["max_tokens"]
    if isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or max_tokens < 1:
        raise EntryError(entry_id, f"'max_tokens' must be a positive integer, found {max_tokens!r}")

    model = _require_str(raw, "model", entry_id)
    if model not in SUPPORTED_MODELS:
        raise EntryError(
            entry_id,
            f"model {model!r} is not in the supported set ({', '.join(SUPPORTED_MODELS)}). "
            "Refused at load rather than at the seam, so an unsupported model costs a "
            "refusal instead of an assembled request.",
        )

    effort = _require_str(raw, "effort", entry_id)
    if effort not in EFFORT_LEVELS:
        raise EntryError(entry_id, f"effort {effort!r} is not one of {', '.join(EFFORT_LEVELS)}")

    repetitions = raw.get("repetitions")
    if isinstance(repetitions, bool) or not isinstance(repetitions, int) or repetitions < 1:
        raise EntryError(
            entry_id,
            f"'repetitions' must be a positive integer, found {repetitions!r}. N is read "
            "from the entry and never defaulted: a default would make the reported verdict "
            "distribution a property of the code rather than of the rubric.",
        )

    question = _require_str(raw, "question", entry_id)
    criteria = _require_str(raw, "criteria", entry_id)

    definitions = raw.get("scale_definitions")
    if not isinstance(definitions, dict):
        raise EntryError(
            entry_id,
            f"'scale_definitions' must be a mapping, found {type(definitions).__name__}",
        )
    undefined = tuple(member for member in scale if not str(definitions.get(member, "")).strip())
    if undefined:
        raise EntryError(
            entry_id,
            f"'scale_definitions' does not define {', '.join(undefined)}. A scale rendered "
            "as bare tokens asks the model to guess what each means, and two runs of one "
            "rubric then measure whatever it guessed.",
        )
    extra = tuple(sorted(key for key in definitions if key not in scale))
    if extra:
        raise EntryError(
            entry_id,
            f"'scale_definitions' defines {', '.join(extra)}, which the scale does not "
            "declare. A definition for a verdict that cannot be returned is text nothing "
            "renders.",
        )

    facts_raw = raw.get("requires_facts", [])
    if not isinstance(facts_raw, list):
        raise EntryError(
            entry_id, f"'requires_facts' must be a list, found {type(facts_raw).__name__}"
        )
    for position, item in enumerate(facts_raw, start=1):
        if not isinstance(item, str) or not item.strip():
            raise EntryError(entry_id, f"requires_facts[{position}] must be a non-empty string")

    precondition_raw = raw.get("applies_when_facts_present", [])
    if not isinstance(precondition_raw, list):
        raise EntryError(
            entry_id,
            f"'applies_when_facts_present' must be a list, found {type(precondition_raw).__name__}",
        )
    for position, item in enumerate(precondition_raw, start=1):
        if not isinstance(item, str) or not item.strip():
            raise EntryError(
                entry_id, f"applies_when_facts_present[{position}] must be a non-empty string"
            )
    # A precondition on a category the entry never renders is a precondition on
    # nothing the judge will ever see -- and it would silently make the
    # dimension apply to every call, which is the state D125 exists to fix.
    # Refused by name rather than tolerated.
    unrendered = tuple(item for item in precondition_raw if item not in facts_raw)
    if unrendered:
        raise EntryError(
            entry_id,
            f"'applies_when_facts_present' names {', '.join(str(u) for u in unrendered)}, "
            "which 'requires_facts' does not render. A precondition on a category the prompt "
            "never carries is a precondition on nothing.",
        )

    return JudgeSpec(
        model=model,
        max_tokens=int(max_tokens),
        effort=effort,
        repetitions=int(repetitions),
        question=question,
        criteria=criteria,
        scale_definitions=MappingProxyType({str(k): str(v) for k, v in definitions.items()}),
        requires_facts=tuple(str(item) for item in facts_raw),
        applies_when_facts_present=tuple(str(item) for item in precondition_raw),
    )


def _parse_violating(
    raw: dict[str, Any], entry_id: str, scale: tuple[str, ...], negative: str
) -> tuple[str, ...]:
    """The verdicts that count a call against a judged entry's gate (D160).

    Absent, it is the negative pole alone, which is what every entry read before
    D160. Declared, it is held in scale order and meets three rules, each refused
    by name: every member is in the scale, the negative pole is among them, and
    at least one member is left out -- a gate its own pole passes is not a gate,
    and a gate no verdict passes measures the rubric rather than the agent.
    """
    if "violating" not in raw:
        return (negative,)
    declared = _require_str_list(raw, "violating", entry_id)
    off_scale = tuple(member for member in declared if member not in scale)
    if off_scale:
        raise EntryError(
            entry_id,
            f"'violating' names {', '.join(off_scale)}, which the scale "
            f"({', '.join(scale)}) does not declare. A verdict that cannot be returned "
            "counts against nothing.",
        )
    if negative not in declared:
        raise EntryError(
            entry_id,
            f"'violating' omits the negative pole {negative!r}, so a call whose modal "
            "verdict is the pole would pass the gate.",
        )
    if set(declared) == set(scale):
        raise EntryError(
            entry_id,
            "'violating' names every member of the scale, so no verdict passes and the gate "
            "fails on every call it judges.",
        )
    return tuple(member for member in scale if member in declared)


def _parse_entry(raw: object, position: int, known_checks: tuple[str, ...]) -> RubricEntry:
    if not isinstance(raw, dict):
        raise RubricSchemaError(f"entry {position}: expected a mapping, found {type(raw).__name__}")

    raw_id = raw.get("id")
    entry_id = raw_id if isinstance(raw_id, str) and raw_id.strip() else f"(entry {position})"
    if not isinstance(raw_id, str) or not raw_id.strip():
        raise EntryError(entry_id, "'id' must be a non-empty string")

    unknown = tuple(
        key
        for key in raw
        if key not in REQUIRED_ENTRY_KEYS
        and key not in OPTIONAL_ENTRY_KEYS
        and key not in JUDGE_ENTRY_KEYS
    )
    if unknown:
        raise EntryError(entry_id, f"unknown key(s): {', '.join(sorted(unknown))}")

    # Gate first, so that a rubric missing several things reports the one the
    # requirement names. A missing gate reported as "missing tier" sends a
    # reader to the wrong line.
    if "gate" not in raw:
        raise MissingGateError(entry_id)
    gate_raw = _require_str(raw, "gate", entry_id)
    if gate_raw not in {member.value for member in Gate}:
        raise EntryError(
            entry_id, f"gate {gate_raw!r} is not one of {', '.join(g.value for g in Gate)}"
        )
    gate = Gate(gate_raw)

    tier_raw = _require_str(raw, "tier", entry_id)
    if tier_raw not in {member.value for member in CheckTier}:
        raise EntryError(
            entry_id, f"tier {tier_raw!r} is not one of {', '.join(t.value for t in CheckTier)}"
        )
    tier = CheckTier(tier_raw)

    if tier is CheckTier.JUDGE and gate is Gate.ABSOLUTE:
        raise JudgedTierWithAbsoluteGateError(entry_id)

    check = _require_str(raw, "check", entry_id)
    # Two vocabularies, chosen by tier. A judged entry validated against the
    # deterministic registry would be refused with "check is not implemented",
    # which is true of a registry it was never meant to be in.
    permitted = KNOWN_JUDGE_CHECKS if tier is CheckTier.JUDGE else known_checks
    if check not in permitted:
        raise UnknownCheckKeyError(entry_id, check, permitted)

    scale = _require_str_list(raw, "scale", entry_id)
    if len(set(scale)) != len(scale):
        raise EntryError(entry_id, f"'scale' repeats a member: {', '.join(scale)}")
    if len(scale) < 2:
        raise EntryError(entry_id, "'scale' needs at least two members to be a scale")
    negative = _require_str(raw, "negative", entry_id)
    if negative not in scale:
        raise EntryError(
            entry_id,
            f"negative pole {negative!r} is not in the declared scale ({', '.join(scale)})",
        )

    threshold: float | None = None
    if gate is Gate.RATE:
        if "threshold" not in raw:
            raise RateGateWithoutThresholdError(entry_id)
        candidate = raw["threshold"]
        if isinstance(candidate, bool) or not isinstance(candidate, int | float):
            raise EntryError(entry_id, f"'threshold' must be a number, found {candidate!r}")
        threshold = float(candidate)
        if not 0.0 <= threshold <= 1.0:
            raise EntryError(entry_id, f"'threshold' must be a rate in [0, 1], found {threshold}")
    elif "threshold" in raw:
        raise EntryError(
            entry_id,
            "gate is 'absolute' and a 'threshold' is declared. An absolute gate compares "
            "against no rate, so the value would be read by nothing.",
        )

    traces_to = _require_str_list(raw, "traces_to", entry_id)

    if "negative_instance" not in raw or raw["negative_instance"] is None:
        raise NegativeInstanceUndeclaredError(entry_id)
    negative_raw = _require_str(raw, "negative_instance", entry_id)
    negative_instance: str | None = None if negative_raw == NO_NEGATIVE_INSTANCE else negative_raw
    reason = raw.get("negative_instance_reason")
    if negative_instance is None:
        if not isinstance(reason, str) or not reason.strip():
            raise EntryError(
                entry_id,
                f"declares negative_instance {NO_NEGATIVE_INSTANCE!r} with no "
                "'negative_instance_reason'. Declaring the absence is allowed; declaring it "
                "without saying why is the silence the field exists to replace.",
            )
    elif reason is not None:
        raise EntryError(
            entry_id,
            "names a negative_instance and also a 'negative_instance_reason'. The reason "
            f"field explains a declared {NO_NEGATIVE_INSTANCE!r} and nothing else.",
        )

    params = raw.get("params", {})
    if not isinstance(params, dict):
        raise EntryError(entry_id, f"'params' must be a mapping, found {type(params).__name__}")

    judge: JudgeSpec | None = None
    if tier is CheckTier.JUDGE:
        if params:
            raise EntryError(
                entry_id,
                "declares tier 'judge' and 'params'. Everything a judged entry configures "
                "is in its named judged fields, each of which is read by the renderer, the "
                "schema builder or the seam; a 'params' mapping here would be read by "
                "nothing, which is W20 arriving in the other tier.",
            )
        judge = _parse_judge_spec(raw, entry_id, scale)
    else:
        misplaced = tuple(sorted(key for key in raw if key in JUDGE_ENTRY_KEYS))
        if misplaced:
            raise JudgeKeyOnDeterministicEntryError(entry_id, misplaced)

    return RubricEntry(
        id=raw_id,
        tier=tier,
        check=check,
        gate=gate,
        scale=scale,
        negative=negative,
        violating=_parse_violating(raw, entry_id, scale, negative),
        traces_to=traces_to,
        negative_instance=negative_instance,
        negative_instance_reason=reason if isinstance(reason, str) else None,
        threshold=threshold,
        params=_frozen(params),
        description=_optional_str(raw, "description", entry_id),
        judge=judge,
    )


def parse_rubric(text: str, known_checks: tuple[str, ...]) -> Rubric:
    """Parse and validate. Every refusal names the offending entry."""
    document = yaml.safe_load(text)
    if not isinstance(document, dict):
        raise RubricSchemaError("a rubric is a mapping with 'version' and 'entries'")
    version = document.get("version")
    if not isinstance(version, str) or not version.strip():
        raise RubricSchemaError("'version' must be a non-empty string")
    raw_entries = document.get("entries")
    if not isinstance(raw_entries, list) or not raw_entries:
        raise RubricSchemaError("'entries' must be a non-empty list")

    entries = tuple(
        _parse_entry(raw, position, known_checks)
        for position, raw in enumerate(raw_entries, start=1)
    )

    seen: set[str] = set()
    for entry in entries:
        if entry.id in seen:
            raise DuplicateEntryIdError(entry.id)
        seen.add(entry.id)

    return Rubric(version=version, entries=entries)


def _frozen(value: Any) -> Any:
    """A rubric value nothing downstream can edit, at every depth.

    `MappingProxyType(dict(params))` froze the top level and left every nested
    list and dict mutable and **shared across every call's `ParamView`**:
    `entry.params["required_system_events"].append(...)` succeeded, and the
    appended element was then visible to the next call in the same run.

    Every real configuration in this rubric is nested -- `topics.*.claim_signals`,
    `sources.*.match`, `bands.*.fraction` -- so the shallow freeze covered the
    one level nothing was stored at. D109 records `ParamView` as the single
    non-frozen type in the tier; that was true of the wrapper and not of what it
    wrapped.
    """
    if isinstance(value, dict):
        return MappingProxyType({key: _frozen(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_frozen(item) for item in value)
    return value


def rubric_hash(path: Path) -> str:
    """The rubric a run judged under, hashed so another repository can compare it (D183).

    **Text, not bytes.** Read with universal newlines and encoded UTF-8, so a
    checkout whose line endings differ hashes as the freeze commit's blob does.
    That is the property `load_template` already gives the prompt-template hash,
    measured when the same question was asked of it; hashing the file's bytes
    would report a rubric nobody touched as a different one on another platform.

    **The whole file, comments included**, which is the opposite of what
    `PromptTemplate.sha256` does and for the opposite reason. That hash answers
    whether the prompt sent would differ, so it covers the two halves actually
    sent. This one answers whether the rubric a run judged under is the rubric the
    held-out labels were written against, and an entry's question, criteria or
    scale text changes that while moving neither `rubric_version` nor the
    template's hash.
    """
    return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def load_rubric(path: Path, known_checks: tuple[str, ...]) -> Rubric:
    return parse_rubric(path.read_text(encoding="utf-8"), known_checks)


def validate_result(result: Result, entry: RubricEntry) -> None:
    """The two contract rules that need the entry, applied after a check returns.

    Separated from `Result.__post_init__` because neither is knowable from a
    result alone, and separated from the engine so a test can run it directly
    over a result the engine never produced. A guard reachable only through the
    thing it guards is a guard nothing can plant.
    """
    if result.status is not Status.APPLICABLE:
        return
    if result.verdict not in entry.scale:
        raise VerdictNotInScaleError(entry.id, str(result.verdict), entry.scale)
    if result.verdict == entry.negative and not result.evidence:
        raise NegativePoleWithoutEvidenceError(entry.id, entry.negative)


def validate_params_consumed(view: ParamView, entry: RubricEntry) -> None:
    """Refuse an entry whose check ignored a parameter the entry declared.

    This is the half of "every parameter is read from the rubric entry" that a
    mutation test cannot buy. A mutation test proves the property for the
    parameter it chose to mutate; this proves it for every parameter of every
    entry on every run, because an unread key fails the entry rather than
    sitting in the YAML looking authoritative.

    W20 is what that looks like when nothing enforces it: `params` decorative
    for the whole deterministic tier, one of them disagreeing with the code
    beside it, and the disagreement invisible because nothing read either.
    """
    unread = view.unread
    if unread:
        raise UnreadParameterError(entry.id, unread)
