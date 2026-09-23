"""Per-instance severity: a band computed in code from boolean properties (D206).

Four claims, each the kind a convenient implementation breaks quietly: that the
band is *monotone* in its properties, which is what makes it a severity rather
than a label; that it is *per instance*, so one entry can be banded differently
on two calls; that what happened is read from the stream **from the evidence
point on** rather than from anywhere in the call; and that the declared half
describes exactly the rubric it sits beside.
"""

from __future__ import annotations

import contextlib
import dataclasses
import io
import itertools
from collections import Counter
from pathlib import Path
from typing import Final

import pytest

from harness.checks import build_registry
from harness.cli import main
from harness.core.rubric import Rubric, load_rubric
from harness.core.severity import BAND_ORDER
from harness.corpus.text_adapter import parse_call
from harness.instance_severity import (
    ENTRY_PROPERTIES,
    INSTANCE_PROPERTIES,
    PROPERTIES,
    SeverityPropertiesError,
    band,
    evidence_point,
    instance_facts,
    instance_for,
    load_properties,
    parse_properties,
)

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
PROPERTIES_FILE: Final[Path] = REPO_ROOT / "severity-properties.yaml"
TRANSCRIPTS: Final[Path] = REPO_ROOT / "corpus" / "transcripts"


def _rubric() -> Rubric:
    return load_rubric(REPO_ROOT / "rubric.yaml", build_registry().keys())


def _rank(name: str) -> int:
    """Higher is more severe."""
    return len(BAND_ORDER) - BAND_ORDER.index(name)


def test_no_property_turning_true_lowers_a_band() -> None:
    """Over every combination, which is small enough to enumerate and is the whole
    argument for calling the result a severity."""
    combinations = list(itertools.product((False, True), repeat=len(PROPERTIES)))
    assert len(combinations) == 2 ** len(PROPERTIES)
    seen = set()
    for values in combinations:
        properties = dict(zip(PROPERTIES, values, strict=True))
        before = band(properties)
        seen.add(before)
        for name in PROPERTIES:
            if properties[name]:
                continue
            after = band({**properties, name: True})
            assert _rank(after) >= _rank(before), (
                f"{name} turning true moved {before} to {after} under {properties}"
            )
    assert seen == set(BAND_ORDER), f"the decision list never produces {set(BAND_ORDER) - seen}"


def test_the_shipped_properties_describe_exactly_the_shipped_rubric() -> None:
    rubric = _rubric()
    declared = load_properties(PROPERTIES_FILE, rubric)
    assert set(declared.entries) | set(declared.excluded) == {entry.id for entry in rubric.entries}
    assert all(reason.strip() for reason in declared.excluded.values())
    assert all(sorted(row) == sorted(ENTRY_PROPERTIES) for row in declared.entries.values())
    # Read from the frozen rubric's own params rather than typed a second time.
    assert "issue_refund" in declared.lists["consequential_write_tools"]
    assert "identity_verified" in declared.lists["verification_states"]
    assert declared.lists["irreversible_tools"] <= declared.lists["consequential_write_tools"]


def test_the_properties_check_would_notice_an_entry_undeclared_and_a_declaration_orphaned() -> None:
    rubric = _rubric()
    text = PROPERTIES_FILE.read_text(encoding="utf-8")

    silent = text.replace("  A-silence-exceeds-threshold:\n", "  A-silence-exceeds-a-threshold:\n")
    assert silent != text
    with pytest.raises(SeverityPropertiesError) as refusal:
        parse_properties(silent, rubric)
    assert "rubric entries with no declared properties: A-silence-exceeds-threshold" in str(
        refusal.value
    )
    assert "declarations naming no rubric entry: A-silence-exceeds-a-threshold" in str(
        refusal.value
    )

    not_boolean = text.replace(
        "{touches_account_access: false, touches_money_or_entitlement: false, "
        "leaves_caller_misinformed: false}",
        "{touches_account_access: 0, touches_money_or_entitlement: false, "
        "leaves_caller_misinformed: false}",
        1,
    )
    assert not_boolean != text
    with pytest.raises(SeverityPropertiesError, match="not true or false"):
        parse_properties(not_boolean, rubric)

    unread = text.replace("param: gated_tools", "param: gated_tool_list")
    with pytest.raises(SeverityPropertiesError, match="declares no param"):
        parse_properties(unread, rubric)


def test_what_happened_is_read_from_the_evidence_point_on() -> None:
    """CALL-02 verifies the caller and later completes a refund. An instance whose
    evidence sits after the refund must not inherit it, and one whose evidence sits
    before the verification was unverified when it happened."""
    declared = load_properties(PROPERTIES_FILE, _rubric())
    call = parse_call(TRANSCRIPTS / "CALL-02.txt")
    last = call.events[-1].index

    from_the_start = instance_facts(call, 0, declared.lists)
    assert from_the_start["consequential_write_completed"]
    assert from_the_start["identity_unverified_at_the_evidence"]
    assert from_the_start["no_handoff_completed"]

    after_everything = instance_facts(call, last, declared.lists)
    assert not after_everything["consequential_write_completed"], (
        "a write that completed before the evidence point was counted as following it"
    )
    assert not after_everything["identity_unverified_at_the_evidence"], (
        "the caller was verified before this point and read as unverified"
    )

    assert evidence_point(("event 12 -- something", "events 7 to 9 -- a gap")) == 7
    assert evidence_point(("call -- outcome_reason refund_issued",)) == 0


def test_one_entry_receives_different_bands_on_two_calls_that_differ_in_what_happened() -> None:
    """Per instance, not per entry: same declared kind of harm, different band,
    because of what the stream shows and nothing else."""
    declared = load_properties(PROPERTIES_FILE, _rubric())
    entry_id = "A-amount-inconsistent-with-band"
    refunded = instance_for(entry_id, parse_call(TRANSCRIPTS / "CALL-02.txt"), (), declared)

    quiet_call = parse_call(TRANSCRIPTS / "CALL-02.txt")
    quiet = dataclasses.replace(
        quiet_call, events=tuple(event for event in quiet_call.events if event.index < 12)
    )
    unrefunded = instance_for(entry_id, quiet, ("event 5 -- planted",), declared)

    assert {name: refunded.properties[name] for name in ENTRY_PROPERTIES} == {
        name: unrefunded.properties[name] for name in ENTRY_PROPERTIES
    }
    assert refunded.properties["consequential_write_completed"]
    assert not unrefunded.properties["consequential_write_completed"]
    assert any(
        refunded.properties[name] != unrefunded.properties[name] for name in INSTANCE_PROPERTIES
    )
    assert (refunded.band, unrefunded.band) == ("medium", "low"), (
        "the same entry was given one band on a call where a refund completed after the "
        "defect and on a call where nothing was written"
    )


@pytest.fixture(scope="module")
def printed() -> str:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = main(["severity"])
    assert code == 0
    return output.getvalue()


#: How many instances of the design set fall in each computed band today, over the
#: committed reference log. Pinned so that an edit to a declaration or to the
#: decision list is seen as a moved count rather than absorbed.
DESIGN_SET_BANDS: Final[dict[str, int]] = {"critical": 8, "high": 3, "medium": 46, "low": 23}


def test_harness_severity_prints_a_band_for_every_instance_of_the_design_set(printed: str) -> None:
    rows = [
        line.split()
        for line in printed.splitlines()
        if line.startswith(("A-", "J-")) and len(line.split()) >= 3
    ]
    bands = Counter(row[2] for row in rows if row[2] in BAND_ORDER)
    assert dict(bands) == DESIGN_SET_BANDS
    assert f"{sum(DESIGN_SET_BANDS.values())} instances" in printed
    assert "with no model call" in printed
    assert "this table gates nothing" in printed
    assert not any(row[0] == "J-call-synthesis" for row in rows), "an excluded entry was banded"
    assert "excluded: J-call-synthesis" in printed

    per_entry: dict[str, set[str]] = {}
    for row in rows:
        per_entry.setdefault(row[0], set()).add(row[2])
    assert any(len(found) > 1 for found in per_entry.values()), (
        "no entry of the design set is banded differently on two calls, so nothing here "
        "shows the severity is per instance"
    )
