"""Per-instance severity: a band computed in code from boolean properties (D206).

**An instance is one rubric entry counting against its gate on one call.** The
ranked severity beside the gold set (`harness.core.severity`) is a human's
ordering of labeled findings, and it exists only where somebody labeled. An
engineer pointing this harness at their own transcripts has instances and no
findings, so each instance needs a band nobody ranked: computed, from properties
a reader can check, with no model asked and no scale handed to anyone (D15).

**Two layers of booleans.** *What kind of harm a violation of the entry means*
is declared per entry in `severity-properties.yaml`, beside the frozen rubric
and never in it. *What happened in the call* is read here from the event
stream, from the instance's evidence point on:

* `consequential_write_completed` -- a tool the rubric declares as a gated write
  completed at or after that point;
* `that_write_is_irreversible` -- and it is one the rubric declares irreversible;
* `identity_unverified_at_the_evidence` -- no verification state was true by then;
* `no_handoff_completed` -- no declared handoff tool completed anywhere in the
  call, so nobody downstream was given the chance to catch it.

Every tool and state name behind those four comes from the frozen rubric's own
params, through the `reads` table in the data file. None is typed here.

**Why the combination is a severity and not a label.** The band is a decision
list over the properties in which each appears only positively, so no property
turning true can lower a band: the properties are *aggravating facts* and the
list orders instances by consequence realized. Its top rule is the ranked
file's own calibration note -- critical is whatever can give a non-owner insight
into the account -- reached here by rule rather than by comparison. A label
would name what kind of thing happened; this says which of two instances cost
more, and says why in terms a reader can dispute.

**What it does not know.** The evidence point is the smallest event index an
instance's evidence names. A defect of the record or of an absence names none
and is read from the start of the call, and a judged instance's citations are
not carried past the roll-up, so it is read the same way. Both over-attribute
in one direction only: a write that completed before the defect counts as after
it. The design set's computed bands are printed against its ranked ones so that
is a number rather than a worry, and the table gates nothing.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

import yaml

from harness.core.context import tool_invocations
from harness.core.events import Call, StateEvent
from harness.core.rubric import Rubric
from harness.core.severity import BAND_ORDER

ENTRY_PROPERTIES: Final[tuple[str, ...]] = (
    "touches_account_access",
    "touches_money_or_entitlement",
    "leaves_caller_misinformed",
)
INSTANCE_PROPERTIES: Final[tuple[str, ...]] = (
    "consequential_write_completed",
    "that_write_is_irreversible",
    "identity_unverified_at_the_evidence",
    "no_handoff_completed",
)
PROPERTIES: Final[tuple[str, ...]] = ENTRY_PROPERTIES + INSTANCE_PROPERTIES

#: The lists an instance property needs, each found in the frozen rubric's params.
READS: Final[tuple[str, ...]] = (
    "consequential_write_tools",
    "success_statuses",
    "verification_states",
    "irreversible_tools",
    "handoff_tools",
)

_EVIDENCE_EVENT: Final[re.Pattern[str]] = re.compile(r"\bevents? (\d+)")
_TRUE: Final[frozenset[str]] = frozenset({"true", "yes"})


class SeverityPropertiesError(Exception):
    """The declared half cannot be used as written, refused by name."""


def band(properties: Mapping[str, bool]) -> str:
    """The band for one instance's properties: a decision list, most severe first.

    Every property appears only positively, which is what makes the list
    monotone: adding a true property can match an earlier rule and never
    unmatches one. `test_no_property_turning_true_lowers_a_band` holds that
    over every combination rather than trusting this sentence.
    """
    account = properties["touches_account_access"]
    money = properties["touches_money_or_entitlement"]
    misinformed = properties["leaves_caller_misinformed"]
    wrote = properties["consequential_write_completed"]
    irreversible = wrote and properties["that_write_is_irreversible"]
    unverified = properties["identity_unverified_at_the_evidence"]
    unattended = properties["no_handoff_completed"]

    if account and unverified:
        # The ranked file's calibration note, by rule: a non-owner may have been
        # given insight into the account.
        return "critical"
    if account or (money and irreversible):
        return "high"
    if (money and wrote) or (misinformed and unattended):
        return "medium"
    return "low"


@dataclass(frozen=True, slots=True)
class SeverityProperties:
    """`severity-properties.yaml`, checked against the rubric it sits beside."""

    version: str
    entries: Mapping[str, Mapping[str, bool]]
    excluded: Mapping[str, str]
    lists: Mapping[str, frozenset[str]]
    """Each name in `READS`, resolved through the rubric's own params."""


def _resolve_list(rubric: Rubric, name: str, spec: object) -> frozenset[str]:
    if not isinstance(spec, dict) or "entry" not in spec or "param" not in spec:
        raise SeverityPropertiesError(f"reads.{name} must name an entry and a param")
    try:
        entry = rubric.by_id(str(spec["entry"]))
    except KeyError as exc:
        raise SeverityPropertiesError(
            f"reads.{name} names {spec['entry']!r}, which the rubric does not declare"
        ) from exc
    if spec["param"] not in entry.params:
        raise SeverityPropertiesError(
            f"reads.{name}: {entry.id} declares no param {spec['param']!r}"
        )
    value: Any = entry.params[spec["param"]]
    if "field" in spec:
        if not isinstance(value, Mapping):
            raise SeverityPropertiesError(f"reads.{name}: {spec['param']} is not a mapping")
        value = [member[spec["field"]] for member in value.values()]
    values = frozenset(str(member) for member in value)
    if not values:
        raise SeverityPropertiesError(f"reads.{name} resolves to nothing in {entry.id}")
    return values


def parse_properties(text: str, rubric: Rubric) -> SeverityProperties:
    """The declared half, refused unless it describes exactly this rubric.

    Both directions, as every register here is held: a rubric entry with no
    declaration would be banded by silence, and a declaration naming no entry is
    a row that stopped describing anything when its entry was renamed.
    """
    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise SeverityPropertiesError(f"severity properties do not parse: {exc}") from exc
    if not isinstance(document, dict):
        raise SeverityPropertiesError("severity properties are not a mapping")
    entries = document.get("entries")
    excluded = document.get("excluded") or {}
    reads = document.get("reads")
    if not isinstance(entries, dict) or not isinstance(excluded, dict):
        raise SeverityPropertiesError("severity properties need `entries` and `excluded` maps")
    if not isinstance(reads, dict) or sorted(reads) != sorted(READS):
        raise SeverityPropertiesError(f"`reads` must name exactly {', '.join(READS)}")

    declared = {entry.id for entry in rubric.entries}
    problems: list[str] = []
    if silent := sorted(declared - set(entries) - set(excluded)):
        problems.append(f"rubric entries with no declared properties: {', '.join(silent)}")
    if strangers := sorted((set(entries) | set(excluded)) - declared):
        problems.append(f"declarations naming no rubric entry: {', '.join(strangers)}")
    if both := sorted(set(entries) & set(excluded)):
        problems.append(f"entries both declared and excluded: {', '.join(both)}")
    for entry_id, reason in sorted(excluded.items()):
        if not isinstance(reason, str) or not reason.strip():
            problems.append(f"{entry_id} is excluded with no reason")
    for entry_id, properties in sorted(entries.items()):
        if not isinstance(properties, dict) or sorted(properties) != sorted(ENTRY_PROPERTIES):
            problems.append(f"{entry_id} must declare exactly {', '.join(ENTRY_PROPERTIES)}")
        elif not all(type(value) is bool for value in properties.values()):
            problems.append(f"{entry_id} declares a property that is not true or false")
    if problems:
        raise SeverityPropertiesError(
            "severity properties do not describe this rubric:\n  " + "\n  ".join(problems)
        )
    return SeverityProperties(
        version=str(document.get("version", "")),
        entries={entry_id: dict(properties) for entry_id, properties in entries.items()},
        excluded={entry_id: str(reason) for entry_id, reason in excluded.items()},
        lists={name: _resolve_list(rubric, name, reads[name]) for name in READS},
    )


def load_properties(path: Path, rubric: Rubric) -> SeverityProperties:
    return parse_properties(path.read_text(encoding="utf-8"), rubric)


def evidence_point(evidence: Sequence[str]) -> int:
    """The smallest event index an instance's evidence names, or 0 for the start
    of the call when it names none."""
    indices = [int(number) for text in evidence for number in _EVIDENCE_EVENT.findall(text)]
    return min(indices, default=0)


def instance_facts(call: Call, point: int, lists: Mapping[str, frozenset[str]]) -> dict[str, bool]:
    """What happened in the call from the evidence point on, as the four booleans."""
    completed = [
        invocation
        for invocation in tool_invocations(call.events)
        if invocation.result is not None
        and invocation.succeeded
        and invocation.result.status.value in lists["success_statuses"]
    ]
    writes = [
        invocation
        for invocation in completed
        if invocation.name in lists["consequential_write_tools"]
        and invocation.result is not None
        and invocation.result.index >= point
    ]
    verified_in_context = any(
        name in lists["verification_states"] and value.strip().lower() in _TRUE
        for name, value in call.context
    )
    verified_by = [
        event.index
        for event in call.events
        if isinstance(event, StateEvent)
        and event.name in lists["verification_states"]
        and event.value.strip().lower() in _TRUE
    ]
    # Verified "at the evidence" means by the time the defect happened. An
    # instance read from the start of the call (point 0) is unverified unless the
    # context record already said otherwise.
    verified = verified_in_context or any(index <= point for index in verified_by)
    return {
        "consequential_write_completed": bool(writes),
        "that_write_is_irreversible": any(
            invocation.name in lists["irreversible_tools"] for invocation in writes
        ),
        "identity_unverified_at_the_evidence": not verified,
        "no_handoff_completed": not any(
            invocation.name in lists["handoff_tools"] for invocation in completed
        ),
    }


@dataclass(frozen=True, slots=True)
class Instance:
    """One entry counting against its gate on one call, with its computed band."""

    entry_id: str
    call_id: str
    properties: Mapping[str, bool]
    band: str
    ranked_bands: tuple[str, ...]
    """The ranked bands of the findings this entry traces to on this call, most
    severe first. Empty where it traces none there, and for any call nobody
    labeled."""

    @property
    def true_properties(self) -> tuple[str, ...]:
        return tuple(name for name in PROPERTIES if self.properties[name])


def instance_for(
    entry_id: str,
    call: Call,
    evidence: Sequence[str],
    declared: SeverityProperties,
    ranked_bands: Sequence[str] = (),
) -> Instance:
    properties = {
        **declared.entries[entry_id],
        **instance_facts(call, evidence_point(evidence), declared.lists),
    }
    return Instance(
        entry_id=entry_id,
        call_id=call.record.call_id,
        properties=properties,
        band=band(properties),
        ranked_bands=tuple(sorted(ranked_bands, key=BAND_ORDER.index)),
    )


def confusion(instances: Sequence[Instance]) -> dict[tuple[str, str], int]:
    """Computed band against the most severe ranked band each instance traces to.

    Counts and nothing else: there is no agreement figure and no threshold. An
    instance tracing no ranked finding on its call is counted under `untraced`,
    which on the design set is where the judged tier's false alarms land.
    """
    table: Counter[tuple[str, str]] = Counter()
    for instance in instances:
        ranked = instance.ranked_bands[0] if instance.ranked_bands else "untraced"
        table[(instance.band, ranked)] += 1
    return dict(table)


def render(instances: Sequence[Instance], excluded: Mapping[str, str]) -> list[str]:
    columns = (*BAND_ORDER, "untraced")
    lines = [
        f"per-instance severity: {len(instances)} instances, computed in code with no model call",
        "An instance is one rubric entry counting against its gate on one call. Its band is a "
        "decision list over the properties printed beside it (D206).",
        "",
        f"{'entry':<48} {'call':<8} {'band':<9} properties that are true",
        "-" * 110,
    ]
    for instance in sorted(
        instances, key=lambda i: (BAND_ORDER.index(i.band), i.call_id, i.entry_id)
    ):
        lines.append(
            f"{instance.entry_id:<48} {instance.call_id:<8} {instance.band:<9} "
            + (", ".join(instance.true_properties) or "none")
        )
    lines += [
        "",
        "Computed band (rows) against the most severe ranked band of the findings each "
        "instance traces to on its call (columns). Counts only; this table gates nothing.",
        f"{'':<10}" + "".join(f"{column:>10}" for column in columns),
    ]
    table = confusion(instances)
    for row in BAND_ORDER:
        lines.append(
            f"{row:<10}" + "".join(f"{table.get((row, column), 0):>10}" for column in columns)
        )
    for entry_id, reason in sorted(excluded.items()):
        lines += ["", f"excluded: {entry_id} -- {' '.join(reason.split())}"]
    return lines
