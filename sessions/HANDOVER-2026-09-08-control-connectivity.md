# Handover — audit the controls, because they are the whole evidence base

**Status:** closed 2026-09-08, which is what `sessions/HANDOVER-2026-09-08-control-register.md` says of it in answering it; this line read *open* until 2026-09-22. Written 2026-09-08 against `66c4d9f`, working tree clean, `main` in sync with
`origin/main`, CI green. Nothing here is started.

**Who this is for.** A session that has done no design work on this repository and has not read any
held-out transcript. The work below reads `tests/` and `src/`, never `corpus/transcripts/` content
beyond what a check already prints.

---

## The state you are inheriting

Phase 2 is closed: 818 tests, 21 of 21 `[P1]` criteria, 24 of 24 `[P2]`, both verifiers walking
their criteria by running them. All eight held-out obligations are discharged. `rubric.yaml`
declares no `tier: judge` entry, so the judged tier is unbuilt by design and phase 3 has not begun.

Run the gates before you change anything, so a failure later is yours:

```bash
uv run pytest -q && uv run python tools/verify_phase1.py && uv run python -m tools.verify_phase2 && uv run python tools/statement_inventory.py
```

---

## Why this work, and why now

The `Not checked` block in `specs/voice-agent-eval-harness.decisions.md` names this as the largest
unaudited surface in the project, and it is not a hunch. Twenty-five commits closed the phase-2
audit's seventeen findings. They changed **what checks mean** — scope, ordering, name boundaries,
candidate filtering — across eight modules. **No verdict moved anywhere**: 555 results before, 592
after `CALL-22` joined the corpus, identical in status, verdict and evidence everywhere else.

That is the expected signature of latent defects. It is equally the condition under which a *wrong*
fix is invisible, because the corpus cannot separate the two. What stands behind the whole
remediation is roughly thirty planted controls, and **nothing has audited them**.

Two were already found to be measuring nothing. Neither was found by rereading.

---

## The question this sweep answers

Not *does the control pass* — every one of them passes today, and that is the trap. A control that
passes proves its assertion holds. It does not prove the assertion is **connected** to the thing it
claims to measure.

> **For each control: does its mutation actually reach the code under test?**

A control whose mutation lands somewhere nothing reads is green forever and proves nothing. That is
what "a null result from an instrument that is not connected is indistinguishable from a finding"
means in practice.

---

## The procedure

This is the one that found the two. It is mechanical; run it identically every time.

1. Copy `src/` to a scratch directory outside the repository.
2. Restore the defect **into the copy** — the real defect the control claims to catch, in the real
   module, as it was before the fix.
3. Run the control with `PYTHONPATH` pointing at the copy.
4. **Require the control to fail.** A control that stays green here is measuring nothing.
5. Restore, and confirm it goes green again. A control that cannot be driven both ways has been
   proven against nothing.

**Patch a copy of `src/` on disk. Do not patch `sys.modules`.** This is not style — in-memory module
injection is one of the two failure modes already found, and it silently does nothing here because
`harness/checks/__init__.py` binds function objects at import time. A control built that way passes
before and after the mutation, so it reports a clean result while connected to nothing.

---

## The three failure modes seen so far

Name which one you have found; they need different fixes.

1. **Disconnected instrument.** The mutation never reaches the code. The `sys.modules` case above.
   *Fix:* rewrite the control against a real patched copy.
2. **Masked by a second gap.** The control asserts a verdict that a *different* uncovered gap holds
   fixed either way, so the mutation is real but the verdict cannot move. This was the silence
   control. *Fix:* the second gap is the finding; the control is downstream of it.
3. **Proven by a fixture that is not the thing.** The control exercises a stand-in rather than the
   shipped configuration. `f1a95c8` records the fullest example: `tests/test_values.py` covers the
   reader in 32 tests against a **fixture** lexicon, while nothing bound the rubric's own tables to
   any verdict — so seven parameters of one entry moved no verdict, and the instrument looked fine.
   D119 and `CALL-22` closed that one by authoring a call the parameters could act on.
   *Fix:* usually corpus authoring, which is owed to a cleared session — record it, do not fake it.

Read `f1a95c8`, `3a9100d` and `27bc78d` before starting. They are the worked examples.

---

## The register — build this first

There is **no register of controls**. The list below was recovered by grepping the project's own
naming idiom (`..._would_notice_...`, `..._fires_on_...`, `..._moves_the_verdict`, `..._would_catch_...`),
which means the count is a grep result rather than a checkable list. Producing the register is the
first deliverable and the durable one: it turns "roughly thirty" into something a later pass can
audit against.

For each row record: **what defect it claims to catch**, **where that defect lived**, **the verdict**
(connected / disconnected / masked / fixture-proven), and **the evidence** — the actual failure output
when the defect was restored.

| # | Control | Module |
|---|---|---|
| 1 | `test_the_control_character_sweep_would_notice_one` | `tests/test_acceptance.py:461` |
| 2 | `test_the_completion_claim_check_fires_on_exactly_the_seeded_calls` | `tests/test_claim_checks.py:196` |
| 3 | `test_the_blocking_state_check_fires_on_exactly_the_seeded_calls` | `tests/test_claim_checks.py:250` |
| 4 | `test_the_terminal_retry_check_fires_on_exactly_the_seeded_calls` | `tests/test_claim_checks.py:254` |
| 5 | `test_w2_the_control_turning_the_ordering_rule_off_passes_that_call` | `tests/test_claim_checks.py:292` |
| 6 | `test_the_spy_would_notice_a_connection` | `tests/test_cli.py:80` |
| 7 | `test_each_conduct_entry_fires_on_exactly_its_seeded_calls` | `tests/test_conduct_checks.py:101` |
| 8 | `test_every_traced_finding_is_on_a_call_the_entry_fires_on` | `tests/test_conduct_checks.py:115` |
| 9 | `test_the_month_list_is_read_by_position_and_rotating_it_moves_the_verdict` | `tests/test_conduct_checks.py:534` |
| 10 | `test_the_leak_scan_would_notice_a_turn_that_was_in_the_corpus` | `tests/test_context_seam.py:200` |
| 11 | `test_the_event_scoped_check_fires_on_a_door_time_its_titles_agree_with` | `tests/test_corpus_hygiene.py:463` |
| 12 | `test_the_anchor_check_would_notice_a_moved_event` | `tests/test_corpus_hygiene.py:985` |
| 13 | `test_the_measurement_scan_fires_on_an_undated_unbound_number` | `tests/test_corpus_hygiene.py:2282` |
| 14 | `test_the_matched_by_check_fires_when_the_register_names_the_wrong_call` | `tests/test_corpus_hygiene.py:2369` |
| 15 | `test_the_escalation_convention_check_fires_on_the_field_that_was_got_wrong` | `tests/test_corpus_hygiene.py:2597` |
| 16 | `test_the_policy_tool_binding_would_notice_a_rename` | `tests/test_corpus_hygiene.py:2891` |
| 17 | `test_the_enumeration_check_fires_on_the_call_that_actually_went_missing` | `tests/test_document_counts.py:499` |
| 18 | `test_the_recall_net_fires_on_a_count_nobody_declared` | `tests/test_document_counts.py:883` |
| 19 | `test_the_tag_check_fires_on_a_number_that_disagrees_with_its_tag` | `tests/test_document_counts.py:1362` |
| 20 | `test_the_retired_term_check_fires_on_a_term_the_spec_retired` | `tests/test_document_counts.py:1504` |
| 21 | `test_the_name_check_fires_on_an_invented_test_and_rejoins_a_wrapped_one` | `tests/test_document_counts.py:2120` |
| 22 | `test_each_omission_entry_fires_on_exactly_its_seeded_calls` | `tests/test_omission_checks.py:104` |
| 23 | `test_every_traced_finding_is_assert_detectable_and_on_a_call_the_entry_fires_on` | `tests/test_omission_checks.py:118` |
| 24 | `test_w9_a_bare_length_filter_with_no_stopwords_fires_on_benign_turns` | `tests/test_omission_checks.py:155` |
| 25 | `test_each_platform_entry_fires_on_exactly_its_seeded_calls` | `tests/test_platform_checks.py:112` |
| 26 | `test_each_policy_entry_fires_on_exactly_its_seeded_calls` | `tests/test_policy_checks.py:99` |
| 27 | `test_each_record_entry_fires_on_exactly_its_seeded_calls` | `tests/test_record_checks.py:87` |
| 28 | `test_every_traced_finding_is_on_a_call_the_entry_fires_on` | `tests/test_record_checks.py:101` |
| 29 | `test_the_union_check_would_notice_an_unclaimed_entry` | `tests/test_rubric_coverage.py:103` |
| 30 | `test_the_check_would_catch_a_slowed_transcript` | `tests/test_speech_plausibility.py:110` |

**Three notes on the list itself, each of which is a finding if you can confirm it.**

- Rows 8 and 28 are **the same name in two modules**. Either that is deliberate and should be said,
  or one of them is shadowing the other in a reader's mind.
- `test_no_source_file_carries_a_control_character` (`tests/test_acceptance.py:424`) matched the
  grep and is **not** a control — it is the check that row 1 guards. Expect other near-misses in
  both directions: the idiom is a convention, not a declaration.
- The idiom is the only thing making this list recoverable. If a control was named outside it, this
  register does not have it. Widening the grep is part of the job.

---

## What "done" looks like

- A register on disk, one row per control, with a verdict and the evidence behind each.
- Every disconnected or masked control either repaired, or recorded with the reason it cannot be
  (corpus authoring owed to a cleared session is a legitimate reason; "it looked fine" is not).
- A decision recorded in `specs/voice-agent-eval-harness.decisions.md`, where
  numbering continues from **D121**.
- Whatever the sweep changes carries its own control, driven red and restored, per the standing rule
  that a check whose only evidence is that it never fired is proven against nothing.
- The `Not checked` block updated: it currently says these controls are unaudited. When they are, it
  should say what the audit found instead — including the ones you could not settle.

---

## Constraints that do not lift

- **Never open, glob, grep, cat or diff a transcript in `voice-agent-eval-harness-holdout`**, and do
  not read that repository's commit messages or test docstrings. Counts, rules, call identifiers and
  file names are safe; content is not. If unsure which side of the line something falls on, stop and
  ask.
- **Do not build phase 3** — no transport seam, no model calls, no judged dimensions. That is the
  next phase and it is not this work.
- No new packages without flagging for approval first.
- Show every commit message before committing. Never commit a populated `.env` or anything under
  `private/`.
- Numbers in these documents follow the convention: **worded numbers are live claims** and are read
  by count guards; **digits are historical statements**. When a count would need maintaining,
  de-quantify it (D74) rather than adding a checker.
- `sessions/` holds what a session wrote for the next; the root holds what a mechanism reads by name
  (D120). Put your handover here, not in the root.
