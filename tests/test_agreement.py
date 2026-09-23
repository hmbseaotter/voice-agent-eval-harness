"""Agreement counting, and the held-out labels' checks, over invented inputs (D175).

**Nothing here reads a held-out transcript, run log or label.** The labels are
invented: `HF-` ids placed on design calls, with every other field borrowed from a
design finding, and traces written by the test itself.
"""

from __future__ import annotations

import importlib
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import Any, Final

import pytest
import yaml

from harness.agreement import (
    FREEZE_TAG,
    RUBRIC_FROZEN_V1,
    AgreementError,
    EntryAgreement,
    SetAgreement,
    check_held_out_labels,
    count_entry,
    design_expected,
    judged_readings,
    parse_traces,
    render_set,
)
from harness.checks import build_registry
from harness.core.findings import Finding, load_findings
from harness.core.result import Status
from harness.core.rubric import Rubric, load_rubric
from harness.judge.rollup import CallRollup, JudgedEntryRollup

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]


def _rubric() -> Rubric:
    return load_rubric(REPO_ROOT / "rubric.yaml", build_registry().keys())


def _the_freeze_is_in_this_history() -> bool:
    """Whether the pinned freeze commit is an object of this repository.

    It is, in the working repository. It is not in the published snapshot, whose log
    is one commit -- and until D211 this tool re-pointed the pin so that the two tests
    below would pass there, which made `harness agreement` refuse the real held-out
    labels in public and cost five red builds over a tag invented for the same reason.

    The freeze's *absence* is what these two tests cannot work around, so they skip on
    it and on nothing else: a tree that holds the freeze and has lost the tag still
    fails, which is the case D175 wrote the first of them for. What they check is
    carried without git by `tests/test_freeze_proof.py`, against the published objects.
    """
    return (
        subprocess.run(
            ["git", "cat-file", "-e", f"{RUBRIC_FROZEN_V1}^{{commit}}"],
            cwd=REPO_ROOT,
            capture_output=True,
        ).returncode
        == 0
    )


_NO_FREEZE_HERE: Final[str] = (
    "the pinned freeze commit is not in this repository's log, so this reads a tree "
    "the freeze predates -- a published snapshot. tests/test_freeze_proof.py carries "
    "the property here, from the published objects and without git (D211)."
)


def test_the_pinned_frozen_commit_is_the_one_the_tag_points_at() -> None:
    """Pinned so the command needs no clone, compared here so a moved tag fails a
    test rather than leaving the constant quietly wrong (D175).

    Not a control: the control gate runs in a copy of the tree with no `.git`, and
    git cannot answer there. CI fetches every tag (D166), and outside a clone this
    refuses rather than passing.

    **Skipped where the freeze is not in the log** (D211), which is a snapshot rather
    than a clone; a tree that holds the freeze and not the tag still fails here.
    """
    if not _the_freeze_is_in_this_history():
        pytest.skip(_NO_FREEZE_HERE)

    resolved = subprocess.run(
        ["git", "rev-parse", f"{FREEZE_TAG}^{{commit}}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert resolved == RUBRIC_FROZEN_V1


def test_the_rubric_and_the_template_at_head_are_the_frozen_commits() -> None:
    """Judged under the frozen rubric, pinned rather than trusted (D183).

    `rubric_version` is a string an editor moves by hand, and
    `prompt_template_hash` covers the scaffold's two sent halves, so an entry's
    question, criteria or scale text can move without either moving: a run would
    judge under the edited text and every stamp would still read as the freeze.
    This compares both files at HEAD with the commit `RUBRIC_FROZEN_V1` names.

    Decoded as UTF-8 with newlines normalized rather than compared as bytes, so a
    checkout whose line endings differ is not reported as a changed rubric -- the
    same property the rubric hash in a held-out run's header is computed with.

    Not a control, for the reason the tag pin above gives: the control gate runs in
    a copy of the tree with no `.git`, and git cannot answer there.

    **Skipped where the freeze is not in the log** (D211). In a snapshot this used to
    pass by tautology, because the pin had been re-pointed at that snapshot's own first
    commit; `test_the_frozen_blobs_are_the_files_at_head` makes the real comparison
    there, against the frozen trees the proof publishes.
    """
    if not _the_freeze_is_in_this_history():
        pytest.skip(_NO_FREEZE_HERE)

    for name in ("rubric.yaml", "prompts/judge-dimension.v1.md"):
        frozen = (
            subprocess.run(
                ["git", "show", f"{RUBRIC_FROZEN_V1}:{name}"],
                cwd=REPO_ROOT,
                capture_output=True,
                check=True,
            )
            .stdout.decode("utf-8")
            .replace("\r\n", "\n")
        )
        current = (REPO_ROOT / name).read_text(encoding="utf-8")
        assert current == frozen, (
            f"{name} at HEAD is not what the frozen commit names. The held-out labels "
            "are scored against the frozen rubric, so this file may not move while that freeze "
            "stands."
        )


def test_agreement_would_notice_its_counts_read_in_one_direction() -> None:
    """Four counts in both directions, and calls with no verdict counted apart (D175).

    One call of each kind: a traced call fired on and one not, an untraced call fired
    on and one not, and two calls with no verdict -- one of them traced, which must
    not count as a miss, and one a precondition excluded, which must not count as a
    correct silence.
    """
    entry = _rubric().entries[0]
    calls = ["CALL-01", "CALL-02", "CALL-03", "CALL-04", "CALL-05", "CALL-06"]
    readings = {
        "CALL-01": (Status.APPLICABLE, True),
        "CALL-02": (Status.APPLICABLE, False),
        "CALL-03": (Status.APPLICABLE, True),
        "CALL-04": (Status.APPLICABLE, False),
        "CALL-05": (Status.ERRORED, False),
        "CALL-06": (Status.NOT_APPLICABLE, False),
    }
    row = count_entry(entry, readings, frozenset({"CALL-01", "CALL-02", "CALL-05"}), calls)
    assert (row.hits, row.misses, row.false_alarms, row.correct_silences) == (1, 1, 1, 1)
    assert row.no_verdict == (("not_applicable", 1), ("errored", 1))
    assert row.calls == len(calls)


def test_agreement_would_notice_a_call_left_without_a_reading() -> None:
    """A call the entry has no reading for refuses the count rather than shrinking
    the denominator (D175)."""
    entry = _rubric().entries[0]
    with pytest.raises(AgreementError, match="has no result for 1 of the set's 2 call"):
        count_entry(
            entry, {"CALL-01": (Status.APPLICABLE, True)}, frozenset(), ["CALL-01", "CALL-02"]
        )


def test_a_judged_entry_would_notice_its_middle_verdict_read_as_a_pass() -> None:
    """A judged entry fires where its gate reads a violation: a modal verdict it
    counts, which for `J-policy-alignment` includes its middle value (D160, D162).

    A call whose modal verdict passes is silent, and a call with no applicable
    repetition reads as its most frequent status.
    """
    entry = _rubric().by_id("J-policy-alignment")
    assert len(entry.violating) > 1, "the entry counts only its pole, so this proves nothing"
    middle = next(verdict for verdict in entry.violating if verdict != entry.negative)
    passing = next(verdict for verdict in entry.scale if verdict not in entry.violating)

    def _distribution(*pairs: tuple[str, int]) -> tuple[tuple[str, int], ...]:
        return tuple(sorted(pairs, key=lambda pair: entry.scale.index(pair[0])))

    rollup = JudgedEntryRollup(
        entry=entry,
        calls=(
            CallRollup(entry, "CALL-01", _distribution((entry.negative, 7), (passing, 3)), (), ()),
            CallRollup(entry, "CALL-02", _distribution((passing, 9), (middle, 1)), (), ()),
            CallRollup(entry, "CALL-03", _distribution((middle, 6), (passing, 4)), (), ()),
            CallRollup(entry, "CALL-04", (), (("unevaluable", 2), ("errored", 8)), ()),
        ),
    )
    assert judged_readings(rollup) == {
        "CALL-01": (Status.APPLICABLE, True),
        "CALL-02": (Status.APPLICABLE, False),
        "CALL-03": (Status.APPLICABLE, True),
        "CALL-04": (Status.ERRORED, False),
    }


def _findings() -> list[Finding]:
    """Two invented held-out findings, on design calls, borrowing a design finding's
    other fields."""
    borrowed = load_findings(REPO_ROOT / "corpus" / "findings.yaml")[0]
    return [
        replace(borrowed, id="HF-01", call_ref="CALL-01"),
        replace(borrowed, id="HF-02", call_ref="CALL-02"),
    ]


def _traces_document(rubric: Rubric) -> dict[str, Any]:
    first = rubric.entries[0].id
    return {
        "rubric-frozen-v1": RUBRIC_FROZEN_V1,
        "traces": {entry.id: (["HF-01"] if entry.id == first else []) for entry in rubric.entries},
        "uncovered": ["HF-02"],
        "calls_without_findings": ["CALL-03"],
    }


def _check(document: dict[str, Any], findings: list[Finding] | None = None) -> None:
    rubric = _rubric()
    check_held_out_labels(
        parse_traces(yaml.safe_dump(document)),
        rubric,
        _findings() if findings is None else findings,
        ["CALL-01", "CALL-02", "CALL-03"],
    )


def test_the_traces_file_would_notice_a_key_missing_or_added() -> None:
    """A `traces.yaml` holds exactly its four keys (D175)."""
    document = _traces_document(_rubric())
    parse_traces(yaml.safe_dump(document))
    without = {key: value for key, value in document.items() if key != "uncovered"}
    with pytest.raises(AgreementError, match="it holds exactly"):
        parse_traces(yaml.safe_dump(without))
    with pytest.raises(AgreementError, match="it holds exactly"):
        parse_traces(yaml.safe_dump({**document, "notes": []}))


def test_the_held_out_labels_would_notice_each_broken_invariant() -> None:
    """Every invariant the held-out validator states, each broken alone and refused
    by name, and the unbroken labels accepted (D175)."""
    rubric = _rubric()
    first, second = rubric.entries[0].id, rubric.entries[1].id
    _check(_traces_document(rubric))

    def _refused(
        fragment: str, document: dict[str, Any], findings: list[Finding] | None = None
    ) -> None:
        with pytest.raises(AgreementError) as refused:
            _check(document, findings)
        assert fragment in str(refused.value), str(refused.value)

    base = _traces_document(rubric)
    _refused("names rubric-frozen-v1", {**base, "rubric-frozen-v1": "0" * 40})
    rows = {key: value for key, value in base["traces"].items() if key != second}
    _refused("lists no row for rubric entry", {**base, "traces": rows})
    _refused(
        "the rubric does not declare", {**base, "traces": {**base["traces"], "X-invented": []}}
    )
    renamed = [replace(_findings()[0], id="F-01"), _findings()[1]]
    _refused("not HF-NN", {**base, "traces": {**base["traces"], first: ["F-01"]}}, renamed)
    _refused("findings.yaml does not hold", {**base, "uncovered": ["HF-02", "HF-99"]})
    _refused("also uncovered", {**base, "traces": {**base["traces"], first: ["HF-01", "HF-02"]}})
    _refused("neither traced to an entry nor uncovered", {**base, "uncovered": []})
    moved = [_findings()[0], replace(_findings()[1], call_ref="CALL-09")]
    _refused("findings sit on call(s) this set does not read", base, moved)
    _refused(
        "calls_without_findings names", {**base, "calls_without_findings": ["CALL-03", "CALL-09"]}
    )
    _refused("also listed without one", {**base, "calls_without_findings": ["CALL-01", "CALL-03"]})
    _refused("not listed without one", {**base, "calls_without_findings": []})


def _traces_of_the_right_shape(**overrides: Any) -> str:
    """A `traces.yaml` of the right shape, before anything is compared with anything."""
    document: dict[str, Any] = {
        "rubric-frozen-v1": RUBRIC_FROZEN_V1,
        "traces": {"A-invented": []},
        "uncovered": [],
        "calls_without_findings": [],
    }
    document.update(overrides)
    return yaml.safe_dump(document)


def test_the_traces_file_would_notice_a_duplicate_id_or_a_frozen_commit_that_is_not_a_string() -> (
    None
):
    """Two shape checks that nothing read until the phase-5 audit's P5-6.

    A list naming a finding twice would count one trace as two, and the rule is the
    one `_string_list` states for every list in the file. A `rubric-frozen-v1` that is
    not a string would be compared with a commit SHA and never equal it, so the labels
    would be refused for the wrong reason.
    """
    assert parse_traces(_traces_of_the_right_shape()).rubric_frozen == RUBRIC_FROZEN_V1
    with pytest.raises(AgreementError, match="names an id more than once"):
        parse_traces(_traces_of_the_right_shape(uncovered=["HF-01", "HF-01"]))
    with pytest.raises(AgreementError, match="must be a commit SHA"):
        parse_traces(_traces_of_the_right_shape(**{"rubric-frozen-v1": 12345}))


def test_the_totals_row_sums_each_column_into_its_own() -> None:
    """The last row of a section totals each column over the entries, and no test had
    ever read it: a renderer printing misses in the false-alarm column was green (the
    phase-5 audit's P5-6).

    The five counts are deliberately different from one another, so a column swapped
    with its neighbor changes the row.
    """
    rubric = _rubric()
    rows = (
        EntryAgreement(
            entry=rubric.entries[0],
            hits=1,
            misses=2,
            false_alarms=3,
            correct_silences=4,
            no_verdict=(("errored", 5),),
        ),
        EntryAgreement(
            entry=rubric.entries[1],
            hits=10,
            misses=20,
            false_alarms=30,
            correct_silences=40,
            no_verdict=(("refused", 50),),
        ),
    )
    lines = render_set(SetAgreement(name="design set", calls=("CALL-01",), entries=rows), ".")
    totals = next(line for line in lines if line.startswith("every entry"))
    assert totals.split()[2:7] == ["11", "22", "33", "44", "55"]
    assert totals.endswith("165 entry-call pairs")


#: The five family tables, each naming the calls a deterministic entry should fire on.
_FIRING_TABLES: Final[tuple[str, ...]] = (
    "tests.test_platform_checks",
    "tests.test_policy_checks",
    "tests.test_record_checks",
    "tests.test_omission_checks",
    "tests.test_conduct_checks",
)

#: Where the two definitions disagree today, and why it is not a defect in either.
#: `A-gated-write-without-verification` fires on CALL-12 and CALL-18; the findings
#: traced to it, F-75 and F-80, both sit on CALL-18, so agreement counts the CALL-12
#: firing as a false alarm while the family table asserts it as correct. The firing is
#: sound and the finding it answers on CALL-12 is traced to another entry -- which is
#: OB-49's one-tier convention inside a single tier (the phase-5 audit's P5-9).
_DIFFER_BY_DESIGN: Final[frozenset[tuple[str, str]]] = frozenset(
    {("A-gated-write-without-verification", "CALL-12")}
)


def test_the_firing_tables_and_agreements_expected_calls_differ_only_where_recorded() -> None:
    """Two definitions of where a deterministic entry should fire, compared.

    The family tables say which calls each entry fires on; agreement derives the same
    thing from `traces_to` and each finding's `call_ref`. Nothing compared them, and
    they differ on one entry-call pair, which the phase-5 audit found by reading both
    (P5-9). A second difference is a decision somebody has to take, so it fails here
    rather than appearing as a false alarm in a report nobody re-derives.
    """
    findings = {
        finding.id: finding for finding in load_findings(REPO_ROOT / "corpus" / "findings.yaml")
    }
    expected = design_expected(_rubric(), findings)

    tabled: dict[str, frozenset[str]] = {}
    for name in _FIRING_TABLES:
        table = importlib.import_module(name).EXPECTED_FIRING
        for entry_id, (calls, _) in table.items():
            tabled[entry_id] = frozenset(calls)
    assert len(tabled) >= 20, f"only {len(tabled)} entries read from the family tables"

    differences = {
        (entry_id, call)
        for entry_id, calls in tabled.items()
        for call in calls ^ expected.get(entry_id, frozenset())
    }
    assert differences == _DIFFER_BY_DESIGN, (
        "the family tables and agreement's expected calls disagree somewhere new: "
        f"{sorted(differences - _DIFFER_BY_DESIGN)}, and these no longer disagree: "
        f"{sorted(_DIFFER_BY_DESIGN - differences)}"
    )
