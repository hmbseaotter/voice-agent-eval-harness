> **FROZEN — 2026-09-06.** Its work is done: adjudication produced
> `corpus/findings.yaml` (2026-09-01), scoring produced
> `corpus/findings.severity.json` (2026-09-05), and O-1 to O-3 were discharged
> (2026-09-06, D83). The opening line "Nothing in this session has been
> committed" was true when written and has not been true since.
>
> **It was being maintained selectively**, which is the worst of both: items 2
> and 9 were struck through on 09-05 while item 3 stayed open through its own
> discharge on 09-06, so a reader could not tell an open item from an unvisited
> one. It is frozen rather than updated — a handover is a record of what one
> session handed the next, and editing it to match today deletes that.
>
> **One section is still live and is not frozen:** *What must never be read*.
> The prohibition it states is a standing rule, not a fact about that session.

# Handover — adjudication, corpus repair, and the sweep that followed

**Session:** 2026-09-01 to 09-02. **Ends at:** D77, corpus 0.5.0, spec 0.20.0, 350 tests.
**Nothing in this session has been committed, staged or pushed.** The working tree is the deliverable.

---

## What must never be read

This is first because it is the only thing here that cannot be undone.

- **Held-out content, wherever in `../voice-agent-eval-harness-holdout/` it lives.** Never open,
  glob, grep, `cat` or diff a transcript, and do not read that repository's commit messages.
  **Metadata is safe** — filenames, counts, SHAs, dirty-file status. **Rules are safe** — a check,
  a convention, a workflow step, the packet builder's redaction list. The line is *content versus
  existence*, and it has always been the line; what changed on 2026-09-07 is that this bullet now
  states it as the rule rather than as a gloss on a directory.
  **Stated as the directory rather than a range, since 2026-09-06.** It read `CALL-13.txt` …
  `CALL-17.txt` until `CALL-21` was added, at which point an enumeration written to protect a set
  named every member but the newest one — and a reader following it literally would have concluded
  the sixth was fair game. A prohibition that has to be re-enumerated whenever the thing it protects
  grows is a prohibition that fails open.
  **And stating it as a directory failed the same way, one level up.** An audit found held-out
  content in two **docstrings** of that repository's test file — descriptions of a repaired defect
  and a repaired cross-call contradiction — which the directory-scoped wording did not reach, in a
  file any harness session may open. The principle covered them the whole time and the sentence did
  not.
  **The obvious widening is wrong and was rejected**, which is worth recording so it is not
  proposed again. Prohibiting the whole held-out repository except its README and workflow would
  have forbidden the work that discharged `HOLDOUT-OBLIGATIONS.md` O-4, O-5 and O-6 on 2026-09-07:
  each was closed by writing a check **in that repository**, which means reading its tests and its
  tools. A register whose discharge path is "port the check" cannot also forbid reading the file
  the check goes in. **So the fix runs the other way** — the prohibition governs content wherever it
  sits, and the content comes out of those two docstrings so the file stays readable. **That second
  half is still owed**, and belongs to a session already contaminated: rewriting a docstring means
  reading it, and a fresh session doing it would be contaminated for nothing.
  If a task appears to require reading held-out content, say so and stop rather than working
  around it.
- **Two read-prohibited paths** recorded in `private/clean-room-sources.md`. Neither was approached.
- A session that has read held-out content **must not do rubric or gold-set work**; start a fresh
  one. That rule is why this session exists in the shape it does.

---

## What this session was asked to do, and what it became

The ask was narrow: adjudicate 51 candidate findings into `corpus/findings.yaml`, with the human
making every ruling — **D10, because a model-generated gold set makes judge-versus-human agreement
measure a model against itself.**

It became five rounds, each opened by a question the previous round could not answer:

1. **Adjudication** (D64) — call by call. Rulings went to a tracked ledger, not worksheet ticks,
   because the worksheet is byte-asserted against its own generator and the first tick would have
   turned the suite red.
2. **Provenance repair** (D64–D65) — a reviewer asked *what set the clause number* in
   `fetch_policy(document, clause)`. Nothing did. An audit found **thirteen of eighty tool-call
   arguments with no origin in their own call**. `fetch_policy` now returns a whole document and a
   `POLICY` event records the clause the agent *applied* — which turned the corpus's weakest
   findings ("nothing was retrieved") into its strongest ("the governing clause was returned and a
   different one applied").
3. **The 141-type sweep** (D66–D68) — `specs/error-type-sweep.md`. Thirty-five findings, two new
   calls, and a stopping rule. **Three findings needed no transcript change**: the defects were
   already seeded with no finding, including an `agent_hangup` in two calls, pinned by a test
   constant, described in the manifest as belonging "where it is a finding", with no finding
   anywhere.
4. **The gold set** — 86 rows, generated by `tools/make_gold_set.py` from the drafts and the ledger.
5. **An independent sweep** (D69–D70) — a fresh session read the finished work and returned 24
   items. See below.
6. **A documentation sweep** (D71) — because adding a changelog entry moves `Last swept`, and a
   version bump therefore *claims* a sweep. Rather than assert one, it was performed, and
   extended on request to verifying that the checks themselves bind.

---

## Where it stands

| | |
|---|---|
| corpus | 15 design calls, **375 events**, **89 findings** |
| split | 61 assert / 22 judge / 6 human · 82 defect / 7 question · 62 agent / 19 platform / 8 data |
| density | max **0.342** (CALL-12), ceiling 0.35, now machine-checked |
| tests | **350 pass**; ruff check + format clean; mypy clean |
| phase 1 | **21/21 criteria**, each by running it; 4 carry stated caveats |
| `cj load` | **82 admitted, 7 question-tier excluded** by name — re-run against the current gold set |
| held-out | absence check OK; the companion repo is untouched and clean |

**Generated, never hand-edited:** `corpus/findings.yaml` (the gold set) and `corpus/findings.md`,
its Markdown view. **Read `findings.md`, not the drafts** — 23 rows carry ledger text, so the
drafts differ from the corpus in 21 of them, 14 in the evidence itself (D77).
Edit `findings.candidates.yaml` (drafts) or `findings.adjudication.yaml` (rulings) and regenerate.

**Rendered on demand, not committed:** the review worksheet (D76). Its purpose was discharged when
the last ruling landed — `python tools/make_review_worksheet.py` puts it back, anywhere with
`--out`.

**The ledger wins.** `make_gold_set.py` takes `owner`/`detectable_by`/`tier` from
`findings.adjudication.yaml`, and its text where present. That is D10 made mechanical.

---

## What the independent sweep found, and what did not survive it

Twenty-one of 24 reproduced exactly. Three did not, and saying so is the point of reproducing first:
a branch reported as *structurally unreachable* is reachable (just not from a corpus change); one
item hedged itself and was right to; one reported as two defects is one, and merging them would have
buried ordinary prose staleness under a `KeyError`.

**The three that mattered were not the ones labeled most severe.**

- **A false sentence inside the gold set.** F-56 said every call selects its account the same way.
  CALL-18 does not. **This session wrote CALL-18, noticed the collision while designing it, and
  dropped the thread.** Nothing caught it because every evidence check binds a finding to its own
  transcript, and the claim was about the corpus. A cross-call citation form now exists — and on its
  first real use it caught a CALL-18 citation that this session's own renumbering script had missed.
- **`_fold` was flattening 38 consequences** that carried paragraph breaks, on every generation since
  the first. The report looked at evidence fragments and found none; the live case was one field
  across.
- **The `reject` path had never run.** Zero of 86 rulings reject — which D38 predicts. A simulated
  rejection broke two tests.

**Two documents claimed machine-checking they did not have** (D46, twice in one session). The
sharper one: F-48's ledger note said the final-event figure was checked. The span form is read; that
fragment is not a span. The figure went stale on the CALL-12 lengthening and **all 329 tests stayed
green.** `_FINAL_EVENT` reads it now. The wrong claim is **left standing in the note** rather than
edited — per D53, a note that quietly becomes true is not a record of anything.

---

## What the documentation sweep found (D71)

**By reading.** Nine live statements still called the design set 12 calls, D68 having moved every
count that had a test behind it and left every count that did not — including a derived total of
840 judged calls, now **980**. A substitution-class count of eight sat in *prior decisions* after two
earlier passes had each corrected the site in front of them and recorded the fix as done. Assumption
2's discharge was stale in the direction that flattered it: 51 findings over 12 calls at 4.25 each,
against **86 over 14 at 6.14** — the original ~6 estimate was closer than the correction. Two
taxonomy documents describe a design set that has since grown and mention neither new call; both are
now **scoped rather than remapped**, for D66's reason.

**And a third version marker read `0.22.0`** — a version this project has never been at. `git log -S`
finds it in no commit: a typo made while moving the other two markers, which survived a full suite, a
phase-1 verifier run and an independent sweep, because nothing read it.

**By running.** A static pass over 201 test functions found **no vacuous test** — none without an
assertion, none tautological — and eleven whose assertions all sit inside a loop. Every one was
counted at runtime through a trace hook rather than reasoned about: they run between 1 and 694 times.
A mutation battery then planted **15 defects one at a time**; 14 were named by between one and
forty-eight tests, and **one was caught by nothing**: renaming the ticketing platform in a single
transcript. The register check reads substitution **Class 6** — the machine tokens that reach the
parser as fields — and **Class 1**, company and venue and production names, lives in free speech
where an undeclared name looks like every other capitalized word.

**Five guards added**, each planted against and observed to fire before being kept: the design-set
size, the substitution-class count, the third version marker, and the two halves of Class 1 that are
enumerable. The design-set guard is itself loop-only, so it also asserts a **floor on how many
statements it matched** — a pattern that has quietly stopped matching anything is the failure this
whole sweep exists to catch.

---

## CALL-20, and what a fifteenth call found (D73)

Built because D72 named escalation the strongest remaining candidate and the reviewer said it was
worth implementing rather than recording. **A design conversation changed it twice**, and both
corrections came from a stated model of what a handoff owes rather than from a test.

The first draft ended on a queue position — the agent stopped participating while the caller was
second in a queue, with the record already saying the transfer succeeded. **The corpus had already
ruled on that and this session had not noticed**: 50 tool results across 8 statuses, including
`timeout` and `error`. Every action waits for its result. The draft also claimed that defect was the
sharpest escalation finding available; it is class **S5** — acceptance versus delivery — seeded twice
already, so the claim was withdrawn.

The call now records `disconnection_reason: transferred` · `outcome: resolved` ·
`outcome_reason: escalated`, three fields answering three questions, **declared as a true negative**.
`escalated` joined the register because the set genuinely had no value for a call handed to a human.
F-88 is the row the call exists for: `dispute_reference` is declared and written in no transcript,
so nothing links this call to the record the specialist opens. Fifteen calls are about what an agent
said inside a call; that is the only finding about whether the call can be found again from outside.

**Four harness defects, found by adding one call.** `outcome` is a substring of `outcome_reason`, so
record citations were compared against the wrong field; the verify check inferred *never verified*
from owner plus variable name; `int(total_seconds() * 1000)` truncates, so a header that reconciled
exactly read as an unseeded taxonomy 32 defect; and a queue label collided with CALL-18's
internal-note vocabulary. All four fixed, each planted against and observed to fire.

---

## The second sweep (D74) — eleven items, all eleven real

A second independent session swept the work on 2026-09-02 and **every item reproduced**, against the
first sweep's twenty-one of twenty-four. It also opened by correcting a miss of its own: its
quantifier regex had not covered the *N of the M calls* shape, so **F-71 was already wrong when it
swept and it did not flag it**.

**The sharpest item was about a guard built two days earlier.**
`test_every_worded_design_set_size_agrees_with_the_declaration` exists to stop exactly this drift and
was scoped to five specification documents. The sweep ran **the test's own regex** over the four it
did not scan and found six wrong statements — **three inside `corpus/findings.yaml`**, which is the
artifact agreement is measured against.

The six are **rewritten rather than re-pinned**. Quantifying a claim makes it checkable and makes it
decay; *every call except CALL-18* is as informative and cannot go stale by addition. The guard now
scans nine documents with **per-document minimums**, because a document sitting in its loop was
contributing zero matches, hidden inside an aggregate floor.

Also closed: the ruling tally and the judged-call estimate now have tests rather than hand
maintenance (one quantity had been sitting at 980 in one document and 1,050 in another); D7's
acceptance criterion turned out to rest on a property nothing checked, so the injection pair's diff
is now a test; and **Class 1's hole ran one noun past where D71 reached** — thirteen agent personas,
one in every call, invented under the same policy as the platform name D71 bound, declared nowhere.

**One item was pushed back on.** `Last swept: … @ D71` is not "behind the work it covers" — it
records when a sweep last happened, and two decisions accruing against a trigger of eight to ten is
that trigger counting down. Making it assert equality with the highest decision would force a sweep
claim per decision, which is the failure D71 exists to prevent.

**Nothing found was a corpus defect.** The transcripts, the parse, the density and CALL-20 were all
clean on the sweep's own measurement. Every item was documentation or a check.

---

## Owed, in priority order

1. **A second human reader.** The corpus has one author; the gold set has one adjudicator. Everything
   else here is a mechanism; this is the gap no mechanism closes.
2. ~~Severity scoring — phase 1's own stated prerequisite, and the one hard blocker for phase 2.~~
   **Done 2026-09-05.** The estimates here were low: **82** admitted (not 79) and **410** pairwise
   comparisons (not ~395), 112 of them ties. Cuts `F-78:F-83`, `F-14:F-53`, `F-36:F-64` give bands
   of 4 / 15 / 27 / 36 with none unplaced. The warning was right — one revision has since been
   accepted, and both the log hash and `run_id` moved with it (D82).
3. **The held-out obligations** — `HOLDOUT-OBLIGATIONS.md`, O-1 to O-3, **all three still `☐`**. O-3
   grew: the five cannot exercise **35 findings and 2 calls**, and now 12 more events. **Needs a
   session that may read them — not this one.** `HOLDOUT-REPAIR-BRIEF.md` is written for exactly that
   session: conforming shapes, verified clause counts (refund.v1 14, transfer.v1 10, exchange.v1 10),
   the renumbering hazard, the re-check list, and how to record a discharge. It names rules rather
   than defects, because its author could not read the five either. **The risk if this is skipped**:
   the design corpus was repaired so no tool-call argument comes from nowhere, and the guard that
   enforces it has never run against the held-out five — so at phase 5 an authoring artifact would
   read as a seeded defect, on the set agreement is measured against.
4. ~~The taxonomy-coverage mapping for the sweep's new classes (D66).~~ **Closed at D72** —
   `specs/taxonomy-coverage.md` Part 2b, classes `S1`–`S10` with their own identifiers and tally.
5. ~~Two owed items restated rather than closed.~~ **Closed at D72** — the unused vocabulary tokens
   are classified with reasons rather than exempted, and D22's justification for YAML is **narrowed**:
   two of its three legs are carried, the third has nothing behind it and probably never will.
   Satisfying it would mean authoring a finding a human must adjudicate, which inverts D10.
6. **Phase 2's own inheritance.** Twelve taxonomy items are seeded with no check (five are cheap
   deterministic ones: 5, 7, 8, 26, 32), all ten Part 2b classes are seeded with no check, and a P2
   criterion needs **ten tests** for the deterministic failure modes `W2–W10, W19`.
7. ~~A transfer-to-human call is the strongest single corpus candidate left.~~ **Built at D73** —
   `CALL-20`, three findings, adjudicated. It did *not* end up exercising `Outcome.transferred`:
   `disconnection_reason` records how a call ended and `outcome` whether the need was met, so a
   successful handoff is `resolved`. That token now looks like a schema smell rather than a gap.
8. **The transfer failure paths** — (a) never initiated, (b) technical error, (c) no answer. (b) and
   (c) are mutually exclusive, so showing both needs two calls. What the agent should do next is
   left open **with a floor**: a failed transfer must leave the caller somewhere to go.

9. ~~A declared true negative is probably wrong, and it was found while setting severity bands.~~ **Closed at D81.**
   `corpus/seeding-manifest.md` Part 1 declares **"CALL-12 event 11, its form only — a readback that
   names what it is reading back"** as behavior no check may fire on, and F-68 and F-42 make the
   opposite — describing an address rather than naming it — a defect in CALL-11.

   Reading F-45 during band-setting produced a **third position that beats both**: the agent should
   never state the address on file. The caller spells the address they claim, and the agent verifies
   it against the record. That gets F-42's benefit — the caller can tell it is wrong, and consent to
   a specific destination is evidenced — **without** F-45's leak, and it holds whether or not
   verification has happened.

   Why it matters here: a booking reference is *"printed on every confirmation email and forwarded
   whenever tickets are shared"* (F-75's own words), so F-45 converts a widely-circulated token into
   the holder's name and email. With a ZIP that F-56 already records as spoofable-plus-one-factor,
   that is the material for operational control of the account. F-45 sits at rank 2 of 82 for
   exactly this reason.

   **What would change**: the Part 1 row's claim that naming in full is the correct *form* — it is
   the tolerable form, not the correct one — and probably the framing of F-68 and F-42, whose harm is
   real but whose implied remedy is weaker than spell-back-and-verify.

   **Closed narrower than this guessed.** The Part 1 row now says the *timing* is wrong and the
   *form* is tolerable rather than correct, and records why a check calibrated to demand it would
   be demanding a disclosure. F-68's closing sentence no longer endorses naming in full. **F-42
   needed nothing** — it already read *"They were given no way to tell which address that is"*,
   which is the spell-back framing. F-68's assertion also stands: *"no agent turn contains the
   address"* is a fact and *"nothing to check"* is a judgment, and D42 asserts what is assertable.
   One revision, accepted after export with 10 comparisons carried over (D80, D82).

---

## Two things a next session should not have to rediscover

**A seeded defect can exist with no finding, and every mechanism stays green.** That is how
`agent_hangup` survived: a test constant pinned it, the manifest described it, and nothing bound a
seeded exception to a row in the findings document.

**A guard checked as configuration but never observed to bind is not yet a guard.** Every check added
this session was planted against and observed to fire — the density ceiling was dropped to 0.30 and
named four calls; `_FINAL_EVENT` was fed the stale figure and named the row. An earlier guard in this
session was green and blind because it bound to the *call* rather than the finding, and the call
carried a second judged row that satisfied it.
