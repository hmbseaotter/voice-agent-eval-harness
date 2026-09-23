"""Properties of the shipped rubric that no single family test owns.

Two kinds live here. The first is **coverage**: every rubric entry is claimed
by an agreement test, in both directions. The second is **duplication**: a
value written into two entries, where each family test asserts its own entry's
behavior and neither compares the copies.

Each family test file carries an `EXPECTED_FIRING` table and asserts, per row,
that the row's findings equal the entry's `traces_to`. Nothing asserted that the
**union** of those tables is the rubric. A thirty-eighth entry with no table row
would run, fire or not, and be claimed by no agreement test and no verifier line.

That is not hypothetical at one remove: the phase gate's own criterion named the
claim, platform, omission and policy families and omitted `record`, `conduct`
and two of the three claim entries. Every one of those tests existed and passed,
so nothing was wrong -- the PASS rested on the families somebody remembered to
list. This file is the mechanism that makes remembering unnecessary, and it is
modelled on `test_the_check_ran_on_every_named_negative_instance_and_found_nothing`,
which iterates the rubric and therefore cannot miss an entry.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final

from tests.test_conduct_checks import EXPECTED_FIRING as CONDUCT_FIRING
from tests.test_judged_firing import EXPECTED_FIRING as JUDGED_FIRING
from tests.test_omission_checks import EXPECTED_FIRING as OMISSION_FIRING
from tests.test_platform_checks import EXPECTED_FIRING as PLATFORM_FIRING
from tests.test_policy_checks import EXPECTED_FIRING as POLICY_FIRING
from tests.test_record_checks import EXPECTED_FIRING as RECORD_FIRING

from harness.checks import build_registry
from harness.core.rubric import CheckTier, load_rubric

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
RUBRIC_PATH: Final[Path] = REPO_ROOT / "rubric.yaml"

#: The claim family names its entries in three constants rather than one table,
#: because its three checks take different shapes. Listed here by id so the
#: union below is complete; if a fourth claim entry arrives, this line is what
#: fails rather than nothing.
CLAIM_ENTRIES: Final[frozenset[str]] = frozenset(
    {
        "A-completion-claim-unsupported",
        "A-action-against-blocking-state",
        "A-terminal-refusal-retried",
    }
)

#: `(module name, table keys)` for every family that uses the table shape.
FAMILY_TABLES: Final[tuple[tuple[str, frozenset[str]], ...]] = (
    ("test_conduct_checks", frozenset(CONDUCT_FIRING)),
    ("test_omission_checks", frozenset(OMISSION_FIRING)),
    ("test_platform_checks", frozenset(PLATFORM_FIRING)),
    ("test_policy_checks", frozenset(POLICY_FIRING)),
    ("test_record_checks", frozenset(RECORD_FIRING)),
    ("test_claim_checks", CLAIM_ENTRIES),
    ("test_judged_firing", frozenset(JUDGED_FIRING)),
)


#: Judged entries whose firing on the design set **nothing asserts**. Empty since
#: D202, and kept as a declaration rather than deleted, so that a judged entry
#: added without a row in `tests/test_judged_firing.py` has somewhere to be named
#: and the guard below stays total across both tiers.
#:
#: **What it held, and why it could not close the way it was written to.** From
#: phase 3 it named the one judged entry, and from phase 4 all seven, waiting on
#: agreement against held-out labels that could not exist before the
#: `rubric-frozen-v1` tag (D21). Phase 5 measured that agreement on 2026-09-18 and,
#: as D175 requires, the held-out figures went to the owner and were never
#: committed -- so the set could not close on a committed figure, which is what
#: OB-7 recorded when its trigger fired.
#:
#: **What closed it** (D202, the owner's decision): the judged family gets the
#: firing table every other family has, over the committed reference log, with
#: today's disagreements with the gold set recorded by name. That is a
#: measurement against a committed artifact and it is not blind agreement -- the
#: design findings were adjudicated with judge output in view -- and the blind
#: figure stays the held-out section of `harness agreement`, recomputable from
#: the held-out repository's published labels and committed log.
JUDGED_AGREEMENT_PENDING: Final[frozenset[str]] = frozenset()


def _covered() -> frozenset[str]:
    return frozenset().union(*(entries for _, entries in FAMILY_TABLES))


def _accounted_for() -> frozenset[str]:
    """Every entry something says something about -- asserted or declared owed.

    The union of the family tables and the pending set. Kept as one function so
    the coverage test and its control ask the same question: a control
    comparing against its own idea of what is covered would be re-implementing
    the rule beside the check, which is the shape D121 found in six controls.
    """
    return _covered() | JUDGED_AGREEMENT_PENDING


def test_every_rubric_entry_is_claimed_by_exactly_one_family() -> None:
    """Both directions, and the second is the one that was missing.

    An entry no table names is an entry no agreement test asserts anything
    about. A table row naming no entry is a row that silently stopped testing
    when the entry it referred to was renamed.

    **Widened at P3 to stay total across both tiers.** The judged entry has no
    firing table and cannot have one yet, so this compares against the family
    tables *plus* the declared-pending set. That keeps the guard covering every
    entry rather than being scoped to the tier it happens to work for -- which
    would be this file's own opening paragraph happening again, one tier over.
    """
    rubric = load_rubric(RUBRIC_PATH, build_registry().keys())
    declared = frozenset(entry.id for entry in rubric.entries)
    accounted = _accounted_for()

    unclaimed = sorted(declared - accounted)
    assert not unclaimed, (
        "rubric entries no family firing table names and no pending declaration "
        f"covers, so nothing asserts where they fire: {', '.join(unclaimed)}"
    )
    orphaned = sorted(accounted - declared)
    assert not orphaned, (
        "firing tables or pending declarations naming entries the rubric does not "
        f"have, so those rows assert nothing: {', '.join(orphaned)}"
    )


def test_every_pending_judged_entry_is_a_judged_entry_that_exists() -> None:
    """The declaration cannot go stale in either direction.

    An id here that the rubric does not declare is a gap recorded about
    nothing. An id here that is *deterministic* would be excusing an entry a
    family table should have claimed -- which is the guard above being waived
    by the mechanism meant to keep it honest.
    """
    rubric = load_rubric(RUBRIC_PATH, build_registry().keys())
    judged = {entry.id for entry in rubric.for_tier(CheckTier.JUDGE)}
    assert judged >= JUDGED_AGREEMENT_PENDING, (
        "declared pending but not a judged entry in the shipped rubric: "
        f"{sorted(JUDGED_AGREEMENT_PENDING - judged)}"
    )
    assert judged - JUDGED_AGREEMENT_PENDING - _covered() == frozenset(), (
        "a judged entry is neither in a family firing table nor declared pending: "
        f"{sorted(judged - JUDGED_AGREEMENT_PENDING - _covered())}"
    )
    assert not (JUDGED_AGREEMENT_PENDING & _covered()), (
        "a judged entry is both claimed by a firing table and declared pending: "
        f"{sorted(JUDGED_AGREEMENT_PENDING & _covered())}"
    )


def test_no_entry_is_claimed_by_two_families() -> None:
    """Two families asserting the same entry is not an error, but it means one
    of them is the authority and nobody said which. Today none overlaps."""
    seen: dict[str, str] = {}
    duplicated: list[str] = []
    for module, entries in FAMILY_TABLES:
        for entry_id in sorted(entries):
            if entry_id in seen:
                duplicated.append(f"{entry_id} in {seen[entry_id]} and {module}")
            seen[entry_id] = module
    assert not duplicated, "entries claimed by two families: " + "; ".join(duplicated)


def test_the_union_check_would_notice_an_unclaimed_entry() -> None:
    """The control. A union built from an empty table set, or a `load_rubric`
    returning nothing, would make the test above pass by comparing two empty
    sets -- which is the failure mode it exists to prevent one level down."""
    rubric = load_rubric(RUBRIC_PATH, build_registry().keys())
    declared = frozenset(entry.id for entry in rubric.entries)
    assert len(declared) >= 30, f"the rubric parsed to {len(declared)} entries"
    assert _accounted_for() == declared

    invented = declared | {"A-an-entry-no-table-names"}
    assert sorted(invented - _accounted_for()) == ["A-an-entry-no-table-names"], (
        "the comparison does not report an entry the tables do not name"
    )


# --------------------------------------------------------------------------
# Copies. None is wrong; none had anything that would notice them diverging.
# --------------------------------------------------------------------------


def _params(entry_id: str) -> Mapping[str, Any]:
    rubric = load_rubric(RUBRIC_PATH, build_registry().keys())
    entry = next((e for e in rubric.entries if e.id == entry_id), None)
    assert entry is not None, f"{entry_id} is not in the rubric; this names an entry that moved"
    return entry.params


def test_the_two_month_lists_are_the_same_twelve_months() -> None:
    """Twelve month names, written into two entries.

    `A-deadline-never-resolved` carries them lower case as `resolution_signals`
    and `A-spoken-local-date-wrong` carries them capitalized as `month_names`.
    Each family test asserts its own entry's firing set, so a month dropped
    from one list and not the other changes what one check sees, and nothing
    compares them.

    Case is what the two legitimately differ by -- one matches normalized
    speech, the other parses a spoken date -- so the comparison is case-folded
    rather than exact, and each list is then asserted to keep its own case.
    W7 is what an unstated case difference between two arms of one check costs:
    a lower-cased month silently disabled the date arm, a false pass on the
    headline failure mode.
    """
    resolution = _params("A-deadline-never-resolved")["resolution_signals"]
    months = _params("A-spoken-local-date-wrong")["month_names"]

    folded_resolution = {str(name).lower() for name in resolution}
    folded_months = {str(name).lower() for name in months}
    assert folded_resolution == folded_months, (
        "the two month lists have diverged: only in resolution_signals "
        f"{sorted(folded_resolution - folded_months)}, only in month_names "
        f"{sorted(folded_months - folded_resolution)}"
    )
    assert len(folded_months) == 12, f"{len(folded_months)} distinct months, not twelve"

    assert all(str(name).islower() for name in resolution)
    assert all(str(name)[:1].isupper() for name in months)


def test_a_capability_trigger_shared_by_two_capabilities_is_declared_deliberately() -> None:
    """ "at the end of my rope" triggers both `dispute` and `escalation`.

    That is not a mistake -- a caller at the end of their rope plausibly wants
    either -- but it means the check has two capabilities to invoke on one
    phrase, and whichever it reports first is the one a reader sees. Nothing
    said so, so a third capability picking up the same phrase would look
    exactly like the two that already do.

    This does not forbid the overlap. It requires it to be **this** overlap: a
    new shared trigger fails here and gets a sentence, rather than arriving
    silently.
    """
    capabilities = _params("A-declared-capability-not-invoked")["capabilities"]

    seen: dict[str, list[str]] = {}
    for name, capability in capabilities.items():
        for signal in capability["trigger_speech_signals"]:
            seen.setdefault(str(signal), []).append(str(name))
    shared = {signal: sorted(names) for signal, names in seen.items() if len(names) > 1}

    assert shared == {"at the end of my rope": ["dispute", "escalation"]}, (
        "the set of triggers shared by two capabilities changed. Each one means the check "
        f"has two tools to choose between on one phrase: {shared}"
    )


def test_the_two_number_tables_agree_on_the_words_they_both_carry() -> None:
    """`hundred` and `thousand` are in `number_words` and in `number_scales`.

    `_compose` reads the scale table for a scale word and discards the lexicon
    value entirely, so `number_words["hundred"]` is read for **membership** --
    the word has to be recognized as a number word at all -- and its value is
    read by nothing. Set it to 5 and "two hundred" still composes to 200.

    That is W20 one level down, and it is why D109's `ParamView` guard cannot
    see it: the guard records top-level keys, and both tables *are* top-level
    keys that are read. The duplication itself is recorded as residue under
    P2-3. What can be closed today is that the two tables must not disagree
    about the same word, and that every scale word is in the lexicon -- a scale
    word the lexicon does not carry is never tokenized, so its scale is
    unreachable.
    """
    params = _params("A-available-value-never-spoken")
    words = params["number_words"]
    scales = params["number_scales"]

    shared = sorted(set(words) & set(scales))
    assert shared == ["hundred", "thousand"], f"the overlap changed: {shared}"
    disagreeing = {
        name: (words[name], scales[name]) for name in shared if words[name] != scales[name]
    }
    assert not disagreeing, (
        "the two tables give different values for the same word, and only one of them is "
        f"read: {disagreeing}. `_compose` uses number_scales, so the number_words value is "
        "the one that can be wrong without any check noticing"
    )
    assert set(scales) <= set(words), (
        f"scale words absent from the lexicon: {sorted(set(scales) - set(words))}. A word "
        "the lexicon does not carry is never tokenized, so its scale is unreachable"
    )
