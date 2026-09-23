"""The findings document: loader, validator, and the Markdown view.

**The YAML is the source of truth; the Markdown is generated for reading.**

YAML rather than a Markdown table or CSV, because `evidence` holds verbatim
multi-line quotes and the schema requires fragments from different points in a
call to stay visibly separate (D22). A table cell physically cannot carry that
and CSV quoting handles it badly. The generated view therefore renders evidence
as a list rather than a column -- a view that flattened three fragments into one
cell would undo the reason the format was chosen.

**Severity is not here.** It lives in a separate file keyed by `id` and is joined
in `harness.core.severity`. A `severity` field appearing in this document is
rejected by name rather than ignored: the tool that produces severity must never
mutate a document it does not own, and a document that has acquired the field
anyway is evidence that something did.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Final

import yaml


class DetectableBy(StrEnum):
    """Which tier could catch this finding at all.

    Not a severity and not a confidence. It is the classification the whole
    project turns on: what a deterministic assertion can catch, what needs a
    model's judgment, and what needed a human to notice. Human judgment, per
    D10 -- if this is model-assigned, judge-versus-human agreement measures a
    model against itself.
    """

    ASSERT = "assert"
    JUDGE = "judge"
    HUMAN = "human"


class Owner(StrEnum):
    """Whose defect this is.

    Added after a human review found a single row bundling two defects with
    different owners: the platform failing to record a verification state, and
    the agent claiming verification it never attempted. Those have different
    fixes, land on different desks, and belong in different sections of the
    report -- and a row that carries both is actionable by nobody.

    The specification already splits the report into an agent-behavior audience
    and a data/integration one at P4. This is that split made a property of the
    finding rather than a judgment made later while rendering, which is where
    it would have been guessed.
    """

    AGENT = "agent"
    """The agent's own behavior: what it said, what it chose to do."""
    PLATFORM = "platform"
    """The orchestration around it: a gate not enforced, a state not recorded,
    a disposition label derived from something other than the tool results."""
    DATA = "data"
    """The records themselves: contradictions, missing components, values the
    agent could not have spoken correctly whatever it did."""


class Tier(StrEnum):
    """`defect` -- the system did something wrong.

    `question` -- something is wrong or absent in a way that cannot be resolved
    from the transcript, so it is a question for whoever owns the system rather
    than a defect charged against the call. Taxonomy 21 is the worked example: a
    total with no fee component, internally consistent, which is either a
    deliberate product decision or a missing implementation and is
    indistinguishable from the outside.

    The distinction is load-bearing downstream. `comparative-judgment` excludes
    `question` entries from scoring and reports the count, because rating a
    non-defect would put it in the anchor set where it would distort every later
    placement.
    """

    DEFECT = "defect"
    QUESTION = "question"


#: Required on every entry. Asserted against the producing tool's own
#: specification by `tools/check_spec_interface.py` -- do not hand-verify it.
REQUIRED_KEYS: Final[tuple[str, ...]] = (
    "id",
    "call_ref",
    "owner",
    "observation",
    "evidence",
    "consequence",
    "detectable_by",
    "tier",
)

#: Keys accepted beyond the required set. Deliberately empty: silently
#: tolerating an unknown key is how a typo'd key becomes an absent value nobody
#: notices, which is the same failure the transcript adapter refuses for
#: metadata.
OPTIONAL_KEYS: Final[tuple[str, ...]] = ()

_SEVERITY_KEY: Final[str] = "severity"


class FindingsError(Exception):
    """Base for every refusal to load a findings document."""


class SeverityFieldPresentError(FindingsError):
    """A findings document carries a `severity` field.

    Rejected by name rather than ignored. Severity is joined by `id` from a file
    the severity tool owns; the tool never mutates this document. A `severity`
    field here means either that something wrote to a document it does not own,
    or that a person is about to hand-maintain a value with no provenance -- and
    the second is worse, because it looks fine.
    """

    def __init__(self, finding_id: str) -> None:
        super().__init__(
            f"finding {finding_id!r} carries a {_SEVERITY_KEY!r} field. Severity is not part of "
            "the findings document: it lives in a separate file keyed by id, carrying the run, "
            "anchor set and comparison log it came from, and is joined at read time."
        )
        self.finding_id = finding_id


@dataclass(frozen=True, slots=True)
class Finding:
    """One finding. Human-authored ground truth (D10)."""

    id: str
    call_ref: str
    owner: Owner
    observation: str
    """Self-contained prose: readable without the transcript open."""
    evidence: tuple[str, ...]
    """A list, so fragments from different points in a call stay separate."""
    consequence: str
    detectable_by: DetectableBy
    tier: Tier


def _require_str(entry: dict[str, Any], key: str, where: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value.strip():
        raise FindingsError(f"{where}: {key!r} must be a non-empty string")
    return value


def _parse_entry(entry: object, position: int) -> Finding:
    where = f"entry {position}"
    if not isinstance(entry, dict):
        raise FindingsError(f"{where}: expected a mapping, found {type(entry).__name__}")

    raw_id = entry.get("id")
    if isinstance(raw_id, str) and raw_id.strip():
        where = f"finding {raw_id!r}"

    if _SEVERITY_KEY in entry:
        # Named by id where there is one, by position otherwise. An entry whose
        # `id` is `""` used to be reported as the empty string, which reads as a
        # formatting bug rather than as the finding it is -- and the message is
        # the whole point of this exception.
        named = raw_id if isinstance(raw_id, str) and raw_id.strip() else f"at {where}"
        raise SeverityFieldPresentError(named)

    missing = tuple(key for key in REQUIRED_KEYS if key not in entry)
    if missing:
        raise FindingsError(f"{where}: missing required key(s): {', '.join(missing)}")
    unknown = tuple(k for k in entry if k not in REQUIRED_KEYS and k not in OPTIONAL_KEYS)
    if unknown:
        raise FindingsError(f"{where}: unknown key(s): {', '.join(sorted(unknown))}")

    evidence = entry["evidence"]
    if not isinstance(evidence, list) or not evidence:
        raise FindingsError(f"{where}: 'evidence' must be a non-empty list")
    fragments: list[str] = []
    for index, fragment in enumerate(evidence, start=1):
        if not isinstance(fragment, str) or not fragment.strip():
            raise FindingsError(f"{where}: evidence fragment {index} must be a non-empty string")
        fragments.append(fragment)

    owner_raw = _require_str(entry, "owner", where)
    if owner_raw not in {member.value for member in Owner}:
        raise FindingsError(
            f"{where}: owner {owner_raw!r} is not one of {', '.join(m.value for m in Owner)}"
        )

    detectable_raw = _require_str(entry, "detectable_by", where)
    # One test, not two. `DetectableBy` is a `StrEnum`, so membership in
    # `__members__.values()` and membership in the value set are the same
    # question asked twice -- and the adjacent `owner` and `tier` checks ask it
    # once, which is what made the asymmetry visible.
    if detectable_raw not in {member.value for member in DetectableBy}:
        raise FindingsError(
            f"{where}: detectable_by {detectable_raw!r} is not one of "
            f"{', '.join(m.value for m in DetectableBy)}"
        )
    tier_raw = _require_str(entry, "tier", where)
    if tier_raw not in {member.value for member in Tier}:
        raise FindingsError(
            f"{where}: tier {tier_raw!r} is not one of {', '.join(m.value for m in Tier)}"
        )

    return Finding(
        id=_require_str(entry, "id", where),
        call_ref=_require_str(entry, "call_ref", where),
        owner=Owner(owner_raw),
        observation=_require_str(entry, "observation", where),
        evidence=tuple(fragments),
        consequence=_require_str(entry, "consequence", where),
        detectable_by=DetectableBy(detectable_raw),
        tier=Tier(tier_raw),
    )


def parse_findings(text: str) -> tuple[Finding, ...]:
    document = yaml.safe_load(text)
    if not isinstance(document, dict) or "findings" not in document:
        raise FindingsError("document must be a mapping with a top-level 'findings' key")
    entries = document["findings"]
    if not isinstance(entries, list) or not entries:
        raise FindingsError("'findings' must be a non-empty list")

    findings = tuple(_parse_entry(entry, position) for position, entry in enumerate(entries, 1))

    seen: set[str] = set()
    for finding in findings:
        if finding.id in seen:
            raise FindingsError(f"duplicate finding id {finding.id!r}")
        seen.add(finding.id)
    return findings


def load_findings(path: Path) -> tuple[Finding, ...]:
    return parse_findings(path.read_text(encoding="utf-8"))


def dump_findings(findings: tuple[Finding, ...]) -> str:
    """Serialize back to YAML. Present so a round-trip is assertable.

    `default_flow_style=False` and `allow_unicode=True` keep evidence fragments
    as readable block entries rather than inline quoted strings -- the round-trip
    has to preserve that three fragments are three fragments, not just that the
    characters survive.
    """
    payload = {
        "findings": [
            {
                "id": f.id,
                "call_ref": f.call_ref,
                "owner": f.owner.value,
                "observation": f.observation,
                "evidence": list(f.evidence),
                "consequence": f.consequence,
                "detectable_by": f.detectable_by.value,
                "tier": f.tier.value,
            }
            for f in findings
        ]
    }
    return yaml.safe_dump(payload, default_flow_style=False, allow_unicode=True, sort_keys=False)


def render_markdown(findings: tuple[Finding, ...]) -> str:
    """The generated reading view.

    Evidence renders as a numbered list, never as a table cell. That is not a
    styling preference: the reason this document is YAML is that fragments from
    different points in a call must stay visibly separate, and a view that
    flattened them into one cell would quietly undo it.
    """
    lines: list[str] = [
        "# Findings — design set",
        "",
        "*Generated. Do not edit this file: change the YAML and regenerate with",
        "`uv run python -m harness.findings_view`. The YAML is the source of truth.*",
        "",
        f"{len(findings)} findings across "
        f"{len({f.call_ref for f in findings})} calls. "
        f"{sum(1 for f in findings if f.tier is Tier.DEFECT)} defects, "
        f"{sum(1 for f in findings if f.tier is Tier.QUESTION)} questions.",
        "",
        "Severity is **not** in this document. It is joined by `id` from the severity file the",
        "comparative-judgment tool emits, which carries the run, anchor set and comparison log the",
        "value came from.",
        "",
        "---",
        "",
    ]
    for finding in findings:
        lines.append(f"## {finding.id} — {finding.call_ref}")
        lines.append("")
        lines.append(f"**Observation.** {finding.observation}")
        lines.append("")
        lines.append("**Evidence.**")
        lines.append("")
        for position, fragment in enumerate(finding.evidence, start=1):
            indented = fragment.replace("\n", "\n   ")
            lines.append(f"{position}. {indented}")
        lines.append("")
        lines.append(f"**Consequence.** {finding.consequence}")
        lines.append("")
        lines.append(f"*Owner:* `{finding.owner.value}` · ")
        lines[-1] += f"*Detectable by:* `{finding.detectable_by.value}` · "
        lines[-1] += f"*Tier:* `{finding.tier.value}`"
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"
