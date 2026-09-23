#!/usr/bin/env python3
"""Run every phase-5 acceptance criterion that is built, and declare the rest.

    uv run python -m tools.verify_phase5

Run as a **module**, for D113's reason, and through the phase-2 loop rather than a
fifth copy of it.

**Written while its phase is open** (D176), which no earlier verifier was. Three of
the phase's criteria are not this repository's to tick, and each is **declared**
rather than ticked or left to read `NO EVIDENCE`: they are asserted by the held-out
repository's gate over its own history -- the label ordering, the frozen-commit
citation and the manifest's recomputation -- which this repository cannot read and
does not try to. The coverage report's two criteria were declared not yet built
until the report was, and are ticked below (D188).

A declaration is printed under its own heading, never counted as a pass and never
as a failure, and the binding test refuses one naming a criterion an entry also
claims, so a declaration cannot outlive the build that replaces it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from tools.verify_phase1 import ASSERTED_ELSEWHERE, Criterion, Declared
from tools.verify_phase2 import main as _phase_main

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]

T: Final[str] = "tests/"

CRITERIA: Final[tuple[Criterion, ...]] = (
    Criterion(
        "Judge-versus-human agreement is reported for design and held-out sets separately, "
        "each with its denominator.",
        tests=(
            f"{T}test_cli.py::test_agreement_would_notice_its_design_section_miscounted",
            f"{T}test_cli.py::test_agreement_would_notice_its_held_out_section_left_out",
            f"{T}test_agreement.py::test_agreement_would_notice_its_counts_read_in_one_direction",
        ),
        caveat=(
            "The held-out section is proven over invented labels on a split design corpus. Its "
            "real numbers were computed on 2026-09-18, go to stdout and are never committed "
            "(D175), so no tick here reads them. What is pinned in this tree is where each judged "
            "entry fires on the committed log, which is not agreement against labels written "
            "blind (D202)."
        ),
        spec_anchor="reported for design and held-out sets separately, each with its denominator",
    ),
    Criterion(
        "`harness agreement` prints the five counts per entry over each set's calls, and refuses "
        "every input it cannot score.",
        tests=(
            f"{T}test_cli.py::test_agreement_would_notice_its_design_section_miscounted",
            f"{T}test_cli.py::test_agreement_would_notice_its_held_out_section_left_out",
            f"{T}test_cli.py::test_agreement_would_notice_held_out_inputs_given_in_part",
            f"{T}test_cli.py::test_agreement_would_notice_a_held_out_input_inside_the_checkout",
            f"{T}test_cli.py::test_agreement_would_notice_design_calls_declared_held_out",
            f"{T}test_cli.py::"
            "test_agreement_would_notice_a_held_out_set_holding_an_undeclared_call",
            f"{T}test_cli.py::test_agreement_would_notice_a_held_out_log_naming_no_manifest",
            f"{T}test_cli.py::test_agreement_would_notice_held_out_labels_breaking_an_invariant",
            f"{T}test_cli.py::test_agreement_would_notice_a_replay_that_stopped_part_way",
            f"{T}test_agreement.py::test_the_traces_file_would_notice_a_key_missing_or_added",
            f"{T}test_agreement.py::test_the_held_out_labels_would_notice_each_broken_invariant",
        ),
        caveat=(
            "That a `traces.yaml` breaks none of the invariants its validator states is re-checked "
            "here; that the labels are right is a judgment no test makes (D175). **The pin "
            "those labels are checked against is not evidence here**: the test that held it "
            "skips where the freeze is not in the log, which a snapshot's is not, and this "
            "verifier reads a skip as absent evidence rather than as a pass (D143). "
            "`tests/test_freeze_proof.py` holds the frozen rubric and template without git, "
            "and D211 records the trade."
        ),
        spec_anchor="`harness agreement` prints, for every rubric entry over each set's calls",
    ),
    Criterion(
        "A judged run over held-out calls needs a well-formed labels manifest and writes it into "
        "its log's header, and every run that cannot go with one is refused.",
        tests=(
            f"{T}test_transport.py::test_a_header_carries_the_labels_manifest_a_held_out_run_names",
            f"{T}test_transport.py::test_the_manifest_check_would_notice_a_log_naming_other_labels",
            f"{T}test_cli.py::test_a_held_out_replay_writes_its_labels_manifest_into_the_log",
            f"{T}test_cli.py::test_a_held_out_run_would_notice_its_labels_manifest_missing",
            f"{T}test_cli.py::test_a_run_mixing_held_out_and_design_calls_would_be_noticed",
            f"{T}test_cli.py::test_a_design_run_would_notice_a_labels_manifest_it_has_no_use_for",
            f"{T}test_cli.py::test_a_malformed_labels_manifest_would_be_noticed",
            f"{T}test_cli.py::test_a_judged_run_would_notice_its_held_out_set_missing",
            f"{T}test_cli.py::test_a_held_out_replay_would_notice_a_log_naming_other_labels",
            f"{T}test_cli.py::test_a_held_out_resume_would_notice_a_log_naming_other_labels",
        ),
        caveat=(
            "This repository writes the manifest into the header and checks its shape alone. "
            "Whether it names the commit that sealed the labels is for the held-out repository's "
            "gate to check, declared below rather than ticked (D173, D176)."
        ),
        spec_anchor="is refused without `--labels-manifest`",
    ),
    Criterion(
        "A held-out run is refused paths inside this checkout, each named by its flag, before "
        "anything is written or a log is read.",
        tests=(
            f"{T}test_cli.py::test_a_held_out_run_would_notice_a_path_inside_the_checkout",
            f"{T}test_cli.py::test_a_held_out_resume_would_notice_its_log_inside_the_checkout",
        ),
        caveat=(
            "The paths are compared with the root the harness resolves its defaults from. A "
            "held-out log reaching the tree by any other route is the absence check's to report, "
            "which phase 1's verifier runs (D174)."
        ),
        spec_anchor="resolving inside the repository, each refusal naming its flag",
    ),
    Criterion(
        "A report over held-out calls is refused an `--out` path inside this checkout, and is "
        "produced to a path outside it and on stdout.",
        tests=(
            f"{T}test_cli.py::"
            "test_a_report_over_held_out_calls_would_notice_an_out_path_inside_the_checkout",
            f"{T}test_cli.py::test_a_design_report_is_still_written_where_it_is_asked_for",
            f"{T}test_holdout_absence.py::test_a_rendered_report_over_held_out_calls_is_found",
            f"{T}test_holdout_absence.py::test_a_design_report_is_not_mistaken_for_a_held_out_one",
        ),
        caveat=(
            "The refusal reads the calls the corpus holds, so a report whose corpus names no "
            "held-out call is written wherever it is asked for. A report reaching this tree by "
            "another route is the absence check's to report, which phase 1's verifier runs (D185)."
        ),
        spec_anchor="is refused an `--out` path inside the",
    ),
    Criterion(
        "A held-out run's log is written under the prefix the held-out repository's gate admits.",
        tests=(f"{T}test_cli.py::test_a_held_out_runs_log_is_named_for_the_gate_that_admits_it",),
        caveat=(
            "The name follows the header's labels manifest, which only a held-out run carries. "
            "That the gate admits the name is asserted in that repository, not here (D184)."
        ),
        spec_anchor="written under the `heldout-` prefix",
    ),
    Criterion(
        "A held-out run's header names the rubric it judged under, a log naming another is "
        "refused, and HEAD's rubric and template are the freeze commit's.",
        tests=(
            f"{T}test_transport.py::test_a_header_carries_the_rubric_a_held_out_run_judged_under",
            f"{T}test_transport.py::"
            "test_the_rubric_check_would_notice_a_log_judged_under_another_rubric",
            f"{T}test_cli.py::test_a_held_out_replay_writes_the_rubric_it_judged_under",
            f"{T}test_cli.py::test_a_held_out_replay_would_notice_a_log_judged_under_another_rubric",
            f"{T}test_cli.py::"
            "test_agreement_and_coverage_refuse_a_held_out_log_judged_under_another_rubric",
            f"{T}test_freeze_proof.py::test_the_frozen_blobs_are_the_files_at_head",
        ),
        caveat=(
            "The pin reads what is committed, so a run made from an edited working copy is caught "
            "by the header value rather than by it, and only where a log is read: a replay, a "
            "resume, and the two commands that score the held-out labels (D197). "
            "That the held-out gate compares the same hash against the freeze is asserted there "
            "(D183, D186). **That HEAD's rubric and template are the freeze's is evidenced without "
            "git since 2026-09-22**: the test that asked git for the frozen commit skips where a "
            "snapshot's log lacks it, and a skip is absent evidence rather than a pass (D143), so "
            "the proof's own comparison stands in its place (D211)."
        ),
        spec_anchor="names a hash of the rubric it judged under",
    ),
    Criterion(
        "An extraction artifact over a declared call, and a findings view over held-out labels, "
        "are refused an --out path inside the repository.",
        tests=(
            f"{T}test_held_out_writes.py::"
            "test_extraction_over_a_declared_call_refuses_an_out_path_inside_the_checkout",
            f"{T}test_held_out_writes.py::"
            "test_extraction_over_the_design_set_still_writes_inside_the_checkout",
            f"{T}test_held_out_writes.py::test_extraction_is_refused_when_the_declaration_cannot_be_read",
            f"{T}test_held_out_writes.py::"
            "test_the_view_over_held_out_labels_refuses_an_out_path_inside_the_checkout",
            f"{T}test_held_out_writes.py::"
            "test_the_design_view_still_writes_inside_the_checkout_and_check_is_not_refused",
        ),
        caveat=(
            "Both commands take an input path, so the rule is about where their output goes and "
            "not about what they may read; a session may read the held-out files in place since "
            "the reveal. A redirect of either command's stdout is the absence check's to report "
            "(D195, D196)."
        ),
        spec_anchor="are each refused an `--out` path inside the repository",
    ),
    Criterion(
        "The coverage report lists findings retired by severity and names the uncovered set, "
        "for the design set and the held-out set apart.",
        tests=(
            f"{T}test_cli.py::test_coverage_would_notice_its_design_section_miscounted",
            f"{T}test_cli.py::test_coverage_would_notice_its_held_out_section_left_out",
            f"{T}test_coverage.py::test_coverage_would_notice_a_finding_read_in_the_wrong_state",
        ),
        caveat=(
            "Retired is read per call, as agreement is: an entry firing on a call retires every "
            "finding traced to it there, though it may have fired for one of them. The held-out "
            "section is proven over invented labels on renamed copies of the design calls, and "
            "its real figures are never written into this tree (D188)."
        ),
        spec_anchor="lists findings retired by severity and names the uncovered set explicitly",
    ),
    Criterion(
        "The coverage report states, per severity band, how many findings are retired out of how "
        "many the band holds, never pooled, and names the findings with no band.",
        tests=(
            f"{T}test_cli.py::test_coverage_would_notice_its_design_section_miscounted",
            f"{T}test_coverage.py::"
            "test_coverage_would_notice_its_bands_pooled_or_its_findings_misbanded",
            f"{T}test_coverage.py::"
            "test_coverage_would_notice_an_unbanded_finding_left_out_or_counted_twice",
            f"{T}test_coverage.py::test_the_coverage_section_would_notice_its_bands_pooled",
            f"{T}test_coverage.py::test_coverage_would_notice_a_band_split_wrong_by_detection_type",
        ),
        caveat=(
            "A band's figure is as good as the band: each set's cuts are its own, so a held-out "
            "band is not a design-set band, and the design figures are in sample (D177, D188)."
        ),
        spec_anchor="states, for each severity band, how many findings are retired",
    ),
    Criterion(
        "`harness coverage` prints both sets' sections, the held-out one on stdout alone, and "
        "refuses every input it cannot cover.",
        tests=(
            f"{T}test_cli.py::test_coverage_would_notice_its_design_section_miscounted",
            f"{T}test_cli.py::test_coverage_would_notice_its_held_out_section_left_out",
            f"{T}test_cli.py::test_coverage_would_notice_held_out_inputs_given_in_part",
            f"{T}test_cli.py::test_coverage_would_notice_a_held_out_input_inside_the_checkout",
            f"{T}test_cli.py::test_coverage_would_notice_a_severity_file_its_join_refuses",
            f"{T}test_cli.py::test_coverage_would_notice_a_findings_file_edited_after_scoring",
            f"{T}test_coverage.py::test_coverage_would_notice_a_band_on_text_that_moved",
            f"{T}test_findings.py::test_the_recheck_would_notice_a_finding_edited_after_scoring",
            f"{T}test_cli.py::test_coverage_would_notice_a_finding_on_a_call_its_set_does_not_read",
            f"{T}test_cli.py::test_coverage_would_notice_each_refusal_it_shares_with_agreement",
            f"{T}test_cli.py::test_coverage_would_notice_an_out_flag_that_writes_a_file",
            f"{T}test_coverage.py::test_coverage_would_notice_an_input_it_cannot_cover",
            f"{T}test_holdout_absence.py::test_a_coverage_report_over_held_out_findings_is_found",
            f"{T}test_holdout_absence.py::"
            "test_a_design_coverage_report_is_not_mistaken_for_a_held_out_one",
            f"{T}test_holdout_absence.py::"
            "test_the_check_reports_a_coverage_report_in_the_tree_it_scans",
            f"{T}test_holdout_absence.py::"
            "test_every_reading_finds_its_artifact_as_a_powershell_redirect_writes_it",
        ),
        caveat=(
            "Stdout alone is a rule about what the command writes: a redirect can still put the "
            "held-out section in this tree, and the absence check is what reports it there, by "
            "its heading beside a held-out finding's id, in UTF-8 or UTF-16 (D188, D195)."
        ),
        spec_anchor="`harness coverage` prints, for each severity band of each set",
    ),
)

DECLARED: Final[tuple[Declared, ...]] = (
    Declared(
        "The held-out label files' first commit is later than the freeze commit the published "
        "proof names.",
        spec_anchor="first commit is later than the freeze commit the published",
        kind=ASSERTED_ELSEWHERE,
        reason=(
            "Asserted by the held-out repository's gate over that repository's history: every "
            "commit touching its labels manifest must carry the frozen commit and be dated after "
            "it. This repository cannot read that history, and does not try to (D176)."
        ),
    ),
    Declared(
        "The held-out label files' first commit message cites the freeze commit.",
        spec_anchor="first commit message cites the freeze commit",
        kind=ASSERTED_ELSEWHERE,
        reason=(
            "Asserted by the held-out repository's gate, which reads the freeze commit out of "
            "the published proof under `freeze-proof/` and compares it with the one each label "
            "commit cites; it resolved a tag until O-12 was discharged on 2026-09-21. This "
            "repository pins that commit as `RUBRIC_FROZEN_V1` (D175, D176, D209, D210)."
        ),
    ),
    Declared(
        "The hash manifest matches the published held-out labels, and every held-out run-log "
        "header names a manifest commit that resolves in the companion repository.",
        spec_anchor="The hash manifest matches the published held-out labels",
        kind=ASSERTED_ELSEWHERE,
        reason=(
            "Asserted by the held-out repository's gate, which recomputes the manifest and "
            "resolves the commit a held-out log's header names. Writing that key is this "
            "repository's half, ticked above under its own criterion (D173, D176)."
        ),
    ),
)


def main(argv: list[str] | None = None) -> int:
    """The phase-2 reporting loop, over this phase's criteria and its declarations."""
    return _phase_main(argv, criteria=CRITERIA, phase=5, declared=DECLARED)


if __name__ == "__main__":
    raise SystemExit(main())
