# Session prompt — sweep the specification, for the publication and the accrued count

> **SPENT — 2026-09-22.** The sweep ran; its report is
> `sessions/SWEEP-2026-09-22-publication.md`, and its findings were applied the same day.
> Kept because its *method* is the reusable part; the tree it describes has moved.

*Paste the section below as the first message of a fresh session in the harness repository. Run it
on **Claude Fable 5.1** at effort **xhigh**.*

*Why a different model: all ten decisions this sweep must read hardest, D201 to D210, were written on
Claude Opus 5 — six by the session that opened phase 6 and four by the session that published the
project — and re-reading one's own prose for staleness is the blind spot every audit here has used a
different model to avoid. The last sweep ran this way and returned 27 findings, 26 of which applied
whole. xhigh rather than max because nothing in a sweep spends money and the work is bounded: one
specification read against a tree, with part of it already held by tests.*

*State to start from: a clean checkout of `main` at `6843c5f` or later, with CI green. The push that
carries this brief may skip CI, so check the run before it.*

---

You are sweeping the specification of the voice-agent evaluation harness. Two of the marker's three
triggers have fired, and one of them fired unobserved.

## Why this one is owed, and what already went out unswept

The header's `Last swept` marker claims the specification was read against the tree (D71), and since
D194 it moves only to a version whose changelog entry is marked `**Swept:**` and says what the sweep
read. It stands at **2026-09-20 @ 0.60.0 @ D200**. The specification is at **0.65.0** and the decision
record at **D210**.

- **The accrued count is at its ceiling.** `tests/test_document_counts.py` holds
  `accrued <= 10`, and D201 to D210 make exactly ten. The next decision recorded turns `main` red, so
  every further fork in this project is behind this sweep.
- **The *before publishing* clause fired and nobody read it.** That clause is deliberately
  unmechanized — the header says so, because it is an event outside the tree — and on 2026-09-21 this
  project was published twice over, as a public snapshot, with the marker where it is. So the
  specification a public reader now meets has not been read against the tree since 0.60.0. **That is
  a finding for your report, not a fact to work around**: say what it cost, if anything.

## You report; you do not edit

The specification, the decision record and the registers are not yours to change in this session.
Your report is the one file you add. A later session applies what the owner accepts, writes the
sweep's changelog entry naming your report, and moves the marker. Say in your report if you think a
finding is not worth acting on, and say whether the marker may move to the version that applies you.

## What to read

**The specification, `specs/voice-agent-eval-harness.md`**, every section except the changelog:

`metadata`, `outcome`, `in scope`, `out of scope (v1)`, `control surface`, `triggers & scheduling`,
`tools & permissions`, `state & memory`, `model & cost routing + determinism boundary`, `constraints`,
`prior decisions`, `requirements`, `failure & escalation`, `acceptance criteria`,
`implementation phases`, `assumptions`, `decisions made`, `emitted artifacts`.

The `changelog` is historical: an entry describes what a version did and does not go stale. Read the
newest entries only for whether they describe what landed — 0.61.0 to 0.65.0 are all from 2026-09-20
and 2026-09-21.

**Beside it**, because the specification points at them and a sweep follows the pointer: the
`Not checked` block at the end of `specs/voice-agent-eval-harness.decisions.md`; `README.md`;
`OBLIGATIONS.md`; `HOLDOUT-OBLIGATIONS.md`; `CONTROL-REGISTER.md`; and
`specs/voice-agent-eval-harness.build-prompt.md`'s supersede banner.

**And three bodies of prose that no sweep has ever read**, because they did not exist at 0.60.0:

- `freeze-proof/README.md` — published, and a public reader's first encounter with the project's
  central evidence claim. It states sizes, counts, dates and a recipe. Some of it is held by
  `tests/test_freeze_proof.py`; the rest is prose.
- **the snapshot note's template, `SNAPSHOT_NOTE` in `tools/make_public_snapshot.py`** — read the
  template in the tool rather than a built copy, because the template is what generates every
  published one. What it writes is the first file a stranger opens in the public repository, and
  nothing holds its prose. (The note itself is not a file in this tree, which is why this brief names
  the constant: prose here may name only a path that resolves here.)
- `sessions/PHASE-6-CONTRACT-READING.md` and the phase-6 briefs beside it, for whether their status
  banners still describe what happened.

## What a live statement is

A statement describing the project **now**: a count, a file that exists, a command that behaves a
certain way, a state that holds ("stays open", "is private", "not yet built"), a cross-repository
claim. Each is checkable, and each is what a sweep exists to catch.

Not live: a sentence about what a decision reasoned at the time, a changelog entry, a historical note.
Those are records, and this project does not edit records (D53).

## What is already held by a test, so you need not re-derive it

Read these first and then look past them — a sweep that only re-runs the mechanized half finds nothing.

- `tests/test_document_counts.py` holds requirement and criterion counts per phase against
  `MEASURED_CONTRACT`, the spec version against the `Not checked` marker and the newest changelog
  entry, the design-set size and event totals wherever a document states them, the tagged quantities
  in the registers, the accrued-decision ceiling, and US spelling.
- `tools/statement_inventory.py` resolves every identifier named in prose and reports the ones that
  do not exist.
- `tests/test_contract_coverage.py` holds that each phase's criteria cover its requirements.
- `tests/test_freeze_proof.py` holds the published objects' ids, the chain, the frozen blobs against
  the files at HEAD, the digests the proof's README names, and that the frozen code computes the
  published template hash.
- `tests/test_public_snapshot.py` holds that no tracked file carries an absolute filesystem path
  outside a named allowance.
- `tools/check_spec_interface.py` compares the findings keys, severity fields and row fields this
  specification states against `comparative-judgment`'s.

Run the fast document checks once before you start, so a failure you find later is not inherited:

```bash
uv run pytest -q tests/test_document_counts.py tests/test_contract_coverage.py tests/test_obligations.py tests/test_phase3_acceptance.py tests/test_findings_evidence.py
uv run python tools/statement_inventory.py
uv run python tools/check_holdout_absence.py
uv run python -m tools.verify_freeze_proof
```

## Where to look hardest

Ordered by what this project's history says goes stale first.

**1. The ten decisions since the marker.** D201 and D202 opened phase 6 on its contract reading; D203
made the second adapter Retell's call object and took the event model to v3, where a source may
declare what it cannot carry; D204 settled prompt caching; D205 the log inspector; D206 per-instance
severity; D207 the license check's population; D208 published this project as a snapshot rather than
as rewritten history; D209 published the freeze commit's own object bytes and stopped the snapshot
reusing the freeze tag's name; D210 added the frozen `src` so the held-out gate can run the frozen
code. Check each one's `Rule` line, and each requirement or criterion it added, against the code and
the tests as they now stand.

**2. Publication claims, which are the newest class in this project and the least read.** The working
repository is private under one name and published as a snapshot under another; a companion repository
is public with its history; the third is private and unscanned. Read every sentence that says what is
private, what is public, what a reader will find, what CI runs, which repository a token belongs to,
and what a cross-repository check reaches. The README's CI and token sections, the specification's
`Visibility` and `Reproducibility` lines and the `Not checked` block's repositories entry are where
this class lives.

**3. The freeze tag, which two documents still name as though it resolves.** The published snapshot
carries `snapshot-rubric-pin-v1` and no `rubric-frozen-v1`; the held-out gate no longer resolves that
name at all but verifies against `freeze-proof/`. Two `[P5]` acceptance criteria name the tag, and
D209 left them alone deliberately, calling an amendment to a closed phase's criterion its own fork.
Read them and say whether that still holds, and whether any other prose implies the tag is
resolvable where it is not.

**4. Counts and enumerations the tests do not hold.** The contract's numbers are held; the prose
around them is not — how many rubric entries, how many controls, how many tests, how many verifiers,
what the CI workflow runs, what each phase's deliverables are, how large the published proof is.

**5. Phase 6's status, which is half built.** Six of its twelve criteria are ticked and six are
declared not yet built; the metadata `Status` line, the phase table and the scope bullets each say
something about that. Check they agree with `tools/verify_phase6.py` and with the register's open
obligations, OB-51 to OB-59.

**6. The `Not checked` block, read against today rather than against its refresh sentences.** It
carries one refresh sentence per version since 0.29.0 and a rule that an entry describing a state the
project has left must move rather than stand. Three of the last four versions added a sentence saying
nothing moved; test that.

**7. Cross-repository claims.** `tools/check_spec_interface.py` holds the field lists; the prose
around them is not held by anything. **Do not open the held-out repository.** Nothing here needs it,
and a sweep that reads it puts the reader under rules this task does not need.

## What to produce

A report in `sessions/`, named `SWEEP-<date>-publication.md`, following the shape the reports there
use: a status banner at the top, then the baseline you reproduced, then the findings.

Each finding carries an id (`S-1`, …), what the statement says, where it is (`file:line`), what is
true instead, how you checked, and the wording you propose. Mark each `(reproduced)` or
`(by reading)`. Severity:

- **Wrong** — the statement is false today.
- **Stale** — true when written, describing a state the project has left.
- **Unbacked** — it may be true and nothing in the tree can tell; say what would settle it.

Close with three sections: **what you read and what you did not**, explicitly, since a sweep's claim
is coverage; **what the sweep's changelog entry should say it read**, in a sentence or two, for the
session that writes it; and **whether the publication going out unswept cost anything**, which is the
one question this sweep exists to answer that no previous one was asked.

## Rules

- **Report, do not edit.** Your report is the one file you add.
- **Reproduce before you report.** Of the phase-2 audit's 17 findings 3 did not hold; of the
  2026-08-29 audit's 44, 3 did not. Every checkable claim carries the command and what it printed.
- **Never spend.** Nothing here needs a model call; if anything would issue one, stop.
- **Never tag, and touch no other repository.**
- **The owner decides every fork**, through a selectable question with your recommendation first. End
  every substantive turn with an **Assumptions** list.
- **Commits:** show the message verbatim and ask; stage files by name; no attribution lines. **Do not
  push unless asked.** Your report is prose in `sessions/`, so its push may carry `[skip ci]` under
  the rule the README's CI section states — run the fast document checks over it first.
- Write files with LF endings. US spelling is enforced by test. Worded numbers are live claims read by
  count guards; digits are historical statements.

## One thing worth knowing before you start

The last sweep that was actually performed before 0.60.0, at 0.21.0, found **nine live statements
still calling the design set twelve calls**, a substitution-class count corrected twice in prose and
still wrong, an assumption discharge stale in the direction that flattered it, and a version marker
reading a number this project had never been at — which had survived a full suite, a phase-1 verifier
run and an independent audit, because nothing read it.

The 0.60.0 sweep, under the new rule, moved seven entries of the `Not checked` block alone.

That is the yield a sweep is for. The mechanized half will be green when you start, and this time the
project has also been made public in between — so a statement that was merely wrong is now wrong in
front of strangers.
