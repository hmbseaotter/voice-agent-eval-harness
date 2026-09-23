# Handover — phase-2 residue, closed

**Session:** 2026-09-08. **Starts at** `9b8a91a`, D114, corpus 0.5.1, 746 tests.
**Ends at** `76bd9c7`, D119, corpus 0.6.0, 816 tests. Ten commits, all pushed, CI green.

Unlike the handover this session was given, **everything here is committed and pushed.** The working
tree is not the deliverable; `main` is.

**Every test this document names is checked to exist.** `test_every_test_name_in_prose_exists` now
reads root `HANDOVER-*.md` files, which it did not when this one was written — a document naming a
mechanism, with nothing binding the name, is the shape that check exists for. The audit reports beside
it stay out, for the reason the decision record does: they record what was true then, and one of them
named a test this session deleted on purpose.

---

## What must never be read

This is first because it is the only thing here that cannot be undone.

- **Held-out content, wherever it lives.** Never open, glob, grep, `cat` or diff a transcript in
  `voice-agent-eval-harness-holdout`, and do not read that repository's commit messages or its test
  docstrings. Never open `holdout-authoring-packet/`, nor
  the two withheld source folders outside both repositories, which hold the material the corpus was written clean of.
- **The line is content versus existence.** Counts, rules, call identifiers and file names are safe:
  `HELDOUT_SET` at the repository root is exactly that, and reading it is expected. A transcript is
  not, and neither is a sentence *about* what one contains.
- **Why it cannot be undone.** A session that reads held-out content can no longer design, tune or
  review the rubric, because it then knows what the rubric will be scored against. Session
  transcripts persist at `~/.claude/projects/<encoded-root>/<uuid>.jsonl`, outside this repository,
  where `tools/check_holdout_absence.py` cannot look. **A green absence scan means no copy is in the
  tree, not that no session has read one.**
- **If you are unsure which side of the line something falls on, stop and ask** rather than opening
  it. That instruction was in the prompt that opened this session and it was used once.

**This session is clean.** It read no held-out transcript, no held-out commit message, and neither
withheld folder. That is why it was allowed to touch the rubric, the taxonomy ticks and the corpus.
The contaminated sessions are listed in the owner's memory, not here.

---

## Where it stands

| | |
|---|---|
| branch | `main` at `76bd9c7`, pushed; `phase-2` deleted, on both sides |
| suite | 816 passing, none skipped, locally and in CI |
| verifiers | `tools/verify_phase1.py` 21 of 21; `python -m tools.verify_phase2` 24 of 24 |
| tier | `harness run --tier assert` exits 1, `GATES FAILED: 36 of 37`, 592 results, none errored or unevaluable |
| types / lint | `mypy --strict` clean over 58 files; `ruff check` and `ruff format --check` clean over 80 |
| corpus | `CORPUS_VERSION` 0.6.0, sixteen design calls, 89 findings |
| CI | green at `34290153809`; every prior run reported `1 skipped` and that is now fixed |

Run all of it:

```bash
uv run pytest -q --junit-xml=build/phase1-junit.xml && uv run python tools/verify_phase1.py --junit build/phase1-junit.xml && uv run python -m tools.verify_phase2 --junit build/phase1-junit.xml
```

---

## What closed

**The four items the previous handover left**, plus the nine it listed as open beside them.

- **P2-2** — the value layer had four functions no shipped check called, while the phase-2 verifier
  ticked W5–W8 with tests of them. `available_value_never_spoken` now declares `number_cues` and
  `cue_window_words`, filters candidates through `cue_follows` and compares through `grounded`. The
  live consequence is closed with it: `"one moment for me."` yielded `Decimal('1')`, so a
  `difference_due` of `1` read as spoken on the check whose subject is values that were **not**
  spoken. **D116.**
- **P2-9, all eleven items.** (a) and (e) became one module owning both boundaries, with (j) in the
  same batch because the option taken adds exactly the kind of `match` mode that was falling silently
  to literal — **D115**. (f), (g) and (h) were three shapes of comparing something that is not time
  — **D117**. (b), (c), (d), (i) and (k) were five checks judging over a scope that is not the one
  their entry asks about — **D118**.
- **P2-11's W ticks.** Every row in `specs/taxonomy-coverage.md` Part 3 now names the check, the
  test, and **which kind of evidence stands behind it** — a verdict the design corpus produces, or a
  fixture. W8 got a third disposition, *not reached*: its closure lives in `values.complete_year`
  and no shipped check calls it.
- **The design call owed at D109's amendment.** `CALL-22` — **D119**.
- **The CI skip.** `test_the_report_being_judged_cannot_make_itself_current` waited for a JUnit
  report that a fresh checkout does not have while the tests run, so the guard against the staleness
  scan becoming a tautology had only ever executed on a developer's machine.

**All eight held-out obligations in `HOLDOUT-OBLIGATIONS.md` are discharged.** None was opened by
this session.

---

## Four things worth carrying forward

**1. An audit item taken literally can break the corpus.** P2-9(b) says the deadline check looks for
the resolution only inside the turns that stated the phrase. Widening it to the whole call clears
CALL-09 — its agent says "I've moved you across to the June date" thirteen events before the deadline
is first put in relative terms. The scope is bounded *below* as well as above, and a control asserts
it. Reproduce before believing a finding, including this one.

**2. A recorded residue can contain a defect.** D115 recorded that `matching.field` and
`matching.values` read `key=value` by two grammars and left it as a decision for whoever needed it.
Half of that was deliberate; the other half was `values` stopping at a comma, so
`difference_due=1,250.00` read as `1` — on the money key, in the money check, while `field` reading
the same string returned the whole value. **A recorded residue should name what is deliberate about
it, not only what differs.**

**3. Two of this session's own controls were measuring nothing**, and both were caught by the same
procedure rather than by rereading. The method is: copy `src/` to a scratch directory, put the defect
back, run the suite with `PYTHONPATH` pointing at the copy, and require the control to fail. One
silence control asserted a verdict that a *second* uncovered gap held fixed either way; one W7
measurement used in-memory module injection, which silently does nothing here because
`harness/checks/__init__.py` binds function objects at import. **A null result from an instrument
that is not connected is indistinguishable from a finding.**

**4. Every change in this session moved zero verdicts.** 555 results before, 592 after the corpus
grew, and no status or verdict differs anywhere except where a new call was added. That is expected
for latent defects and it is exactly why each one carries a planted control: a guard whose only
evidence is that it has never fired has been proven against nothing.

---

## Owed, in priority order

**1. A sweep and a version bump, and they go together.** The spec header records `Last swept:
2026-09-07 @ 0.25.0 @ D113`; the record now ends at D119. That is six accrued against a stated
trigger of *~8–10 accrued decisions, before publishing, or **at phase completion***, and phase 2 is
complete — so the trigger is met by its third clause even though
`test_the_sweep_trigger_is_a_mechanism_and_not_only_a_sentence` is still green. **The changelog has
no entry for D114–D119.** Per D71, bumping the version *claims* a sweep, so perform one rather than
asserting it.

**2. Phase 3 — the judged tier.** `specs/voice-agent-eval-harness.md` carries the `[P3]` requirements:
the model transport seam with live and replay implementations, one judged dimension end to end, the
run log, the citation universe and its informed retry, and the `refused` / `errored` / `max_tokens`
distinctions. D108 records that the shipped rubric declares no judged entry, which is why "issues
zero model calls" is trivially true today — revisit that when one exists for real.

**3. Residues recorded rather than closed.** Each is deliberate and each is written down where a
reader meets it:
- **W8 is *not reached***. `complete_year` is called by nothing, because `spoken_local_date_wrong`
  compares the month and the day but not the year. D118 closed the month half; whatever closes the
  year half will wire that function and inherit W8 the moment it does.
- **W5 and W6 are fixture evidence**, not corpus verdicts — reintroducing W6 moves no verdict,
  because the payload figure the numeric arm reaches was never spoken until CALL-22 and is now
  spoken correctly. A call where it is spoken *wrongly* would give both a corpus verdict.
- **`MatchMode.SUBSTRING` is offered by no shipped source.** Its digit-and-separator boundary is
  wrong for the one identifier-shaped value the rubric carries — an email address, whose terminal
  `.com` collides with it at a sentence end.
- **The holding-phrase clearing has no corpus instance.** CALL-05 carries "bear with me" at event 19
  and both of its over-threshold gaps are elsewhere, so both are reported and no phrase clears
  anything. A planted control now covers it.
- **`field` and `values` still read a value differently**, and after D115's amendment that difference
  is deliberate: `field` crosses a space because `internal_note=do not disclose` is one value.

**4. Two register questions the corpus has not yet forced.** `caller_verified` and `holder_confirmed`
are now declared state variables written in no transcript — deliberately, because the findings that
name them *are* the absence of the write. Both entries still declare `negative_instance: none`, and
the register now permits the calls that would change that.

---

## Two things a next session should not have to rediscover

**A design call may seed nothing.** `CALL-22` is the first, and making that representable took an
edit to `test_the_manifest_findings_ranges_match_the_findings_document`, which compared a set against
`None`. If you author another clean call, the machinery is now ready for it; if you author a defective
one, D10 reserves every findings row's wording, `owner`, `detectable_by` and `tier` to the project
owner — **draft rows and ask, never label them.**

**A sixteenth call touches more than the corpus.** Adding one moved `DESIGN_SET`, `CORPUS_VERSION`,
the register's class-7 enumeration, the manifest's verification row and its Part 2 table, every
`#design_set_size` tag, the judged-call estimate, a quoted event total, a `door_time` distribution,
three platform firing sets and one pass rate. **Every one of those was found by an existing guard
rather than by reading**, which is the mechanism working — but budget for it. Where a statement of the
size is present tense it was re-pinned; where it is historical narrative it was de-quantified instead,
which is D74's rule and the reason the next call will move fewer of them.
