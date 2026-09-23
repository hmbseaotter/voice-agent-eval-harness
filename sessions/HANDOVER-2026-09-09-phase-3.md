# Handover — the judged tier runs live, and it misses one of the three it should catch

**Status: closed** 2026-09-09, `db02c76` to `a9af228`. Answers
`sessions/PHASE-3-SESSION-PROMPT.md`, which is closed. Answered by
`sessions/PHASE-4-SESSION-PROMPT.md`. `main` is pushed and CI is green.

**What `closed` means here, because it changed this phase.** It means **this document is final and
will not be edited again** — not that nothing in it is still owed. Until now a handover's status
conflated those two: `open` meant both "still being written" and "things in here are outstanding",
so a document could not be finished while any of its owed items remained. `OBLIGATIONS.md` owns the
second question now (D126), and five of this handover's six owed items are live there — `OB-6` to
`OB-11`. Read the register for what is outstanding; read this for what happened.

**Where the numbers stand:** 1,003 tests (826 at the start), `mypy --strict` over 72 files, 21 of 21
`[P1]`, 24 of 24 `[P2]`, 23 of 23 `[P3]`, the statement inventory clean, and 41 of 41 controls driven
red by their own defect. Decisions D122 to D126. **Every one of those gates now runs in CI**, which
was not true when the phase started.

**Read `## What the live runs found` before anything else.** The seam and the tier are built and
every mechanical criterion passes; what a reader needs from this phase is the measurement, and the
measurement is that a judged dimension is not the same thing as a working one.

**Who this is for.** A session that has read no held-out transcript. Everything below reads `tests/`,
`src/`, `tools/`, `prompts/` and the root documents. **The constraint does not lift**, and it binds
harder here than it did for the control audit: this phase authored a judged rubric entry, and a
session that has read held-out content cannot tune or review one.

---

## Run the gates first, so a failure later is yours

```bash
uv run pytest -q && uv run python tools/verify_phase1.py && uv run python -m tools.verify_phase2 && uv run python -m tools.verify_phase3 && uv run python tools/statement_inventory.py && uv run python tools/verify_controls.py
```

**Every one of these now runs in CI**, which was not true when this phase started: `verify_phase3`
was built here and initially not wired in, and `statement_inventory` had never been. A gate that
runs only when somebody remembers is a gate that has quietly stopped verifying — the argument the
phase-1 CI step makes in its own comment, and one this phase managed to re-earn twice.

Note the addition: `tools/verify_phase3.py`. It is the phase-1 and phase-2 verifiers' shape, and it
**imports the reporting loop from phase 2** rather than keeping a third copy — D113's argument for
importing the suite runner applies harder to the loop that decides what PASS means.

---

## What phase 3 built

**The contract was the specification's `[P3]` requirements and criteria**, as the session prompt
said, and both deliverables landed.

### The model transport seam — `src/harness/core/transport.py`

One request type, two implementations, one log. Four properties are structural rather than promised,
because each is the kind of thing that decays into "wherever somebody remembered to":

- **Recording is unconditional, by wrapping.** `RecordingTransport` is the only transport the engine
  is given. There is no path to a judged call that omits its run-log entry — the same argument
  `ResultBuilder` makes for provenance. Replay records too, which looks redundant until you ask what
  "every run-log entry carries a `stop_reason`; the count missing one is zero" is asserted over.
- **The ceiling refuses before the call.** Composition is `Recording(Ceiling(inner))`, and the order
  carries the meaning: a refused call is a call that did not happen, so it has no entry.
- **Replay never imports the SDK.** `LiveTransport` defers `import anthropic` into its constructor,
  and `test_the_replay_path_does_not_import_the_sdk` asserts it in a subprocess — a subprocess
  because this suite imports the SDK elsewhere, to check its signature.
- **Our backoff replaces the SDK's** (`max_retries=0`), with an explicit 120-second timeout and a
  declared streaming threshold. D122 records why, and the specification required the posture to be
  stated rather than merely chosen.

### One judged dimension end to end — `src/harness/judge/`

`J-policy-alignment`, in the shipped `rubric.yaml`: *did the terms the agent stated align with the
policy clause this call retrieved?* Chosen over the other five because it is the only candidate that
needs `requires_facts`, so it exercises the `[F<n>]` population and the unknown-renderer refusal for
real rather than leaving them fixture-only. Eight of the sixteen design calls retrieve a policy;
three carry a seeded misalignment (F-08, F-17, F-85); CALL-03 is the negative instance, and it is a
sharp one — defective in other ways, correct on policy terms.

The prompt lives in two places on purpose (D123): `prompts/judge-dimension.v1.md` holds the scaffold
and is hashed into every run log; the question, criteria and scale definitions are entry fields where
a rubric mutation can reach them. **The template splits into two messages** at an END SYSTEM marker,
and the split is the injection posture: every instruction is in the system message, and the only
thing in the user message is data.

### Two things built alongside them

**The credential route the specification always named.** `tools & permissions` says credentials are
read "from the environment or an uncommitted `.env`", and only the environment half existed. The
reader takes the two declared credential names and no others, lets an exported variable win over the
file, never exports what it read, and scrubs both values when the two disagree. `.env.example` ships
so the requirement is visible rather than discovered as an error message — and it is
`.env.example`, not `.env`, because a committed file with that exact name is what the fail-closed
pre-commit guard blocks and would be the obvious place for a real key to land later.

**`OBLIGATIONS.md`, which is the answer to this handover's own owed item 5.** Every register in this
project mechanizes a *claim*; nothing mechanized a *discharge*. See the section below.

---

## Defects this phase found in its own work

Grouped, because there were more than a list wants. **Every one was found by running something
rather than by reading** — which is the phase's most transferable result and the reason the count is
not embarrassing.

1. **Repetitions obtained before an abort were discarded.** A transport failure on repetition 2 of 10
   lost repetition 1 — while `RecordingTransport` had already written it to the run log. The run
   reported `results: 0` over a log holding one entry: the harness disagreeing with its own artifact
   about work it had done, in the one requirement that says results already obtained are persisted
   before any abort. Found by a CLI replay test whose reference log covered fewer repetitions than the
   rubric asked for. `JudgedCallAborted` carries the partial outcomes now.

2. **An unpriced model was costed at zero.** `PRICING_USD_PER_MTOK.get(model, (0.0, 0.0))`, so a live
   run of any size reported `$0.00` — a fail-open at the one moment a human is asked to agree to the
   spend. It refuses by name now.

3. **The estimate itself was a guess, and wrong by about three and a half times.** The constants said
   6,000 input tokens and 500 output per call; the shipped corpus renders a mean of about 1,700 input.
   Wrong in the direction that makes a reader approve more spending than they were told. The estimate
   renders every prompt and counts characters now, and bounds output at the entry's own `max_tokens`.

**Caught before it could cost anything.** The entry declared `max_tokens: 2048` on reasoning that
considered only the answer — a verdict, a few sentences, a citation list. But `max_tokens` bounds
**thinking plus output**, and this entry runs adaptive thinking at effort `high`. A judge that
thought for fifteen hundred tokens would have been truncated, and a truncated structured response
resolves to `errored` (D24). That is the harness working, and it would have been 160 of them. Raised
to 4096, still below the streaming threshold.

**A design flaw, found by paying for it once.** The prompt-template hash covered the **whole file**,
comments included, on the reasoning that a change to a template's stated reasoning is worth forcing a
reader to look at the log again. That reasoning is about documentation review and this hash is not
for documentation review: D8's staleness check exists because a fossil log *quietly disagrees with
live behavior*, and a comment cannot change behavior. The bill arrived as a one-word US-spelling fix
in the template's own prose, which under the old scheme would have discarded a recorded run whether
or not the word was in a comment. It hashes the two rendered halves now, so the next comment edit
costs nothing. **The word was in the sent text, so that run was discarded anyway.**

**Three verification gaps in my own claims**, found by counting rather than by reading — the SDK
retry count asserted nowhere, the backoff schedule unasserted on a false premise, and judged-field
coverage by enumeration. All three closed; see owed item 4.

**Two things a guard caught that I had written down wrongly.** `CONFLATED_NO_CLAUSE_CALLS` was
recorded as three calls from a reading of the verdict tables and the guard reported four: CALL-18 had
been described in this handover as a boundary case *with clauses present* and had retrieved none. And
`OBLIGATIONS.md` shipped with "Eleven rows" written in prose — a worded number nobody would update at
twelve — which is now computed from the table it describes.

**And one that no guard could catch, which is the phase's sharpest limit.** The decision record's
Not-checked block said *"No live call has been made"* after 480 of them. Every document guard passed.
They verify that identifiers **resolve** and that counts **agree**; none reads prose for **truth**.

---

## What the live runs found, which is the phase's actual result

Three full passes over the design set, 160 judged calls each, about $4.90 in total. **Every call in
every pass returned `end_turn`** — no truncation and no refusal, on a corpus that seeds prompt
injection by design.

**The citation validator fired seven times, all in the third pass**, and that pass is the one whose
criteria edit was reverted. Runs 1 and 2 produced zero fabricated citations in 320 calls; run 3's
wording pointed the judge at a facts section that was empty on those calls, and it cited `F1`
anyway. Every one was caught by set membership, retried once with the rejected identifier and the
full valid set, and answered validly on the retry — so the informed-retry path is the only part of
this tier that has now been exercised by a real model rather than a fixture. It was exercised by a
defect this session introduced, which is worth stating plainly rather than reporting as a feature.

### The judge agrees with the gold set on two of three, and the third is a clean miss

Runs 1 and 2 reproduce each other on every unambiguous call:

| call | seeded | verdict distribution | reading |
|---|---|---|---|
| CALL-02 | F-08 | misaligned in both | caught |
| CALL-04 | F-17 | misaligned 10/10 in both | caught |
| CALL-19 | F-85 | **aligned 10/10 in both** | **missed** |
| CALL-03 | negative instance | **aligned 10/10 in both** | D107's other half, proven |
| CALL-06 / CALL-07 | injection pair | **same modal verdict** | D7's criterion, met |

The committed reference log is pass 2, at `runs/reference-corpus-0.6.0.jsonl`, and every number
above is asserted against it by `tests/test_reference_run.py` rather than remembered.

**CALL-19 is a genuine miss and it stays a miss.** F-85 is the agent giving a specific deadline that
the retrieved clause dates from an announcement the record does not carry — the subtlest of the
three, because it needs the judge to notice that a clause's anchor is absent rather than that a
figure is wrong. Sharpening the criteria until that call flips would be fitting a prompt to a
transcript I can read, which is exactly what D21's held-out set exists to detect. **Recorded, not
tuned.** CALL-22 is the same category with less certainty: clauses present, verdicts moving between
passes, which is what N=10 is for.

### A second finding, an attempted fix, and why the fix was reverted

CALL-06, CALL-07, CALL-09 and CALL-18 come back misaligned, and **none of them retrieved a policy at
all**. With an empty clause set the criteria's "a term is misaligned when it ... states a rule the
clauses do not support" is unconditionally true of every term the agent utters — so the dimension
conflates **misparaphrasing a clause that was retrieved** with **stating terms that had no retrieval
behind them**. Only the first is what `traces_to` names.

That is a defect in the entry rather than a disagreement about data, so unlike CALL-19 it was in
scope to fix. **The fix was attempted and failed, and the failure is the more useful record.** A
branch was added saying an empty clause set means there is nothing to compare — without removing the
disjunct that contradicts it. The judge read both and said so in its own rationale: *"that case only
applies when the agent stated no policy terms at all, which is not true here."* It also cost **7
fabricated citations in 160 calls** — the new wording pointed at a facts section that on those calls
is empty, and the model cited `F1` — where the passes on either side of it produced zero. Strictly
worse on both counts, so it was reverted.

**Two things that went right about the attempt, and they are the transferable part.** The falsifier
was written down before the run: *CALL-02 and CALL-04 must stay misaligned*. They did, so the edit
was not too broad — it was simply ineffective, which is a different verdict and one that is only
available because the test was named in advance. And the pin that now guards the defect
(`CONFLATED_NO_CLAUSE_CALLS`) immediately caught a misreading in this very handover: CALL-18 had
been written up as a boundary case "with clauses present", and it retrieved none. It is a fourth
instance of the conflation, not an unrelated wobble.

**The real fix is structural and belongs at P4** (D125): either the entry declares a precondition and
returns `not_applicable` when its required facts render empty, or the class moves to the
deterministic tier, where D42 says it belongs — whether a retrieval happened is an event-stream
question, not a judgment. **One attempt at prompt wording was enough to establish that**, and a
second would have been iteration against sixteen transcripts I can read.

**The general shape, for the next session.** A disagreement between the judge and the gold set is one
of two things, and they are treated oppositely. If the entry's own definition does not decide the
case, that is a defect in the entry — fix it, and the fix must be defensible without reference to
which calls disagreed. If the definition decides it and the judge got it wrong anyway, that is the
measurement, and editing until it agrees is overfitting. **And a fix in the first category can still
fail**, which is why the falsifier goes in writing before the run rather than after it.

---

## What is owed, in the order I would take it

**These six are registered as `OB-6` to `OB-11` in `OBLIGATIONS.md`, which is the live view.** The
headings below are the source the register harvests, so **renumbering or deleting one breaks a
register row** — change both together. What follows is the reasoning; the register carries the
status.

### 1. The remaining judged dimensions are P4, as rubric data

The machinery is dimension-agnostic. What a second dimension needs is an entry: a question, criteria,
scale definitions, `requires_facts`, `model`, `max_tokens`, `effort` and `repetitions`. The loader
refuses each missing field by name, and `max_tokens` by a refusal of its own (D24).

**One of them should probably not be a judged dimension at all.** "The agent stated policy terms with
no successful retrieval behind them" is the class the conflation above surfaced, and D42's rule is
that anything derivable from the context record, tool calls, results and their order is `assert`. A
retrieval either happened or it did not; that is an event-stream question. Worth deciding
deliberately at P4 rather than inheriting it as a judged dimension because that is where it first
appeared.

### 2. Agreement is measured now, and still not asserted

`JUDGED_AGREEMENT_PENDING` in `tests/test_rubric_coverage.py` **stays open**. Two of three is a
measurement, not agreement, and a test asserting the current distribution would freeze a miss into a
green tick. What the reference run log does buy is that the measurement is now reproducible: the
numbers above come from a committed artifact rather than from a session's memory of a run.

### 3. Roll-up and gating for the judged tier are P4, deliberately

`harness run --tier judge` applies **no gate** and says so in its own output. Rolling N repetitions
into a rate means choosing an aggregation, and first / modal / worst are three different claims about
what N means (D124). Exit 0 from that command says the tier ran; it says nothing about the agent.

### 4. What is verified by a reader rather than by a mechanism

Counted at the end of this phase rather than estimated. **68 acceptance criteria across three
phases, every one with runnable evidence — none is pure assertion.** Fourteen carry caveats; adding
the fifteen open entries in the decision record's Not-checked block gives **29 places where
verification is incomplete**. Classified, and the classification is judgment:

- **~6 are not gaps** — the caveat explains scope, or a *stronger* mechanism than the criterion
  asked for.
- **~8 have a viable mechanism that is not built** — down from eleven. Three were built at the end
  of this phase and they are the pattern to copy, because each **replaced a statement in prose with
  a value read off the thing the statement was about**:
  - `SDK_RETRIES` and `client_options()` — the specification requires the backoff posture to be
    *stated*, and D122 stated it while nothing read the value the client was built with. The SDK
    defaults to 2, so the failure was silent. A recording stub reads the constructor's kwargs.
  - `backoff_delay()` and an injected sleep — the caveat claimed asserting the schedule would mean
    a test that waits. **That was wrong, and the caveat was the thing to fix:** the sleeps are a
    sequence of *requested delays*, which a recorder captures instantly. The assertion that earned
    its place is the one nobody would think to write — no sleep after the final attempt.
  - `dataclasses.fields(JudgeSpec)` driving both judged-field tests — all eight fields were covered
    by a hand-written list, so a ninth would have failed nothing. That is W20's shape one level up.
- **~12 have no viable mechanism**, and most should not. "Was the reference implementation read"
  is deliberate blindness (D6); "is this severity ordering right" and "are these signal lists the
  right abstraction" are judgment; "who reviews the rubric" needs a second person.

**The largest and least mechanizable class is prose that was true when written.** The document
guards in this tree verify that identifiers resolve and that counts agree; **none reads prose for
truth**. The Not-checked block said "No live call has been made" after 480 of them, every guard
passed, and it was found by hand. `tools/statement_inventory.py`'s own docstring estimates roughly
two hundred existence claims of that kind.

### 5. Owed items had no mechanism — **discharged, and this is where to read about it**

This item is kept rather than deleted: `OBLIGATIONS.md` harvests it, `OB-10` records it `closed`, and
removing the heading would orphan that row. What follows is what it was and what closed it.

**What it was.** `HOLDOUT-OBLIGATIONS.md` and these handovers *are* machine-read — but only by count
guards and identifier resolution. Nothing asserted an obligation was open, closed, or deliberately
deferred, so whether an owed item got addressed depended on the next session reading a document.
That is the "somebody remembers" failure this project mechanizes away everywhere else, sitting in
the documents whose whole job is to survive a session boundary.

**What closed it (D126).** `OBLIGATIONS.md` in the root, read by `tests/test_obligations.py`. The
rule is D121's applied to a new subject — **harvest the population rather than listing it**: every
numbered item under a `## What is owed` heading in every handover must have a row, and every row must
name an item that exists. Both directions. Eleven live obligations across two handovers, none of
which any mechanism knew existed.

Three statuses, and **`deferred` is the one that earns the register**: it must name what would make
it actionable, because "later" is what an obligation says on the day it stops being tracked. Four
rows are deferred and each names a phase — which reframes the count honestly as five open and four
appointments rather than nine unaddressed items. `closed` names evidence, and where the evidence
cites a test that test must exist. There is deliberately no `wontfix`: a decision never to do
something belongs in the decision record, where it has to state a fork.

**Two things to know before editing it.** The harvest keys on *(handover filename, item number)*, so
**renumbering or deleting an owed heading breaks a register row** — change both together. And it does
not cover the Not-checked block's fifteen open entries, which are a differently-shaped population
that was not folded in.

**`HOLDOUT-OBLIGATIONS.md` keeps its own register and its own rule** — only a session cleared to read
held-out content may tick an entry, which has no analogue here. It already had the better half of
this mechanism: its discharged *count* is computed from the `☑` marks rather than maintained, after
that number went stale twice. What it lacked and now has is a per-entry status check — every entry
must carry a marker, and a ticked one must name a session and a date.

### 6. The reference log is large, and nobody has decided whether that is acceptable

`runs/reference-corpus-0.6.0.jsonl` is committed and is about 1.2MB. Each entry carries the full
system prompt, and the system half is byte-identical across all 160 — roughly half a megabyte of
duplication in the committed file. Whether that is worth a format change is a real question and this
phase did not answer it.

## Conventions that cost something to learn, added to the ones already recorded

- **`max_tokens` bounds thinking plus output.** Stated because the entry's first draft did not, and
  the reasoning looked complete.
- **A template's own comments are hashed but not sent.** They had to be stripped for a duller reason
  than token cost: a comment explaining the `{{FACTS}}` placeholder *contains* that placeholder, so
  the renderer demanded a value for documentation. That is D89's constraint arriving in a prompt
  template, and the shipped file tripped it twice — once on the placeholder and once on the boundary
  marker the comment named.
- **A pre-flight estimate must not call the API.** Counting tokens with `messages.count_tokens` would
  be issuing a call before the human agreed to any — the thing the confirmation exists to prevent,
  arriving through the door marked "just an estimate".
- **Two vocabularies now, chosen by tier.** A judged entry's `check` is validated against
  `KNOWN_JUDGE_CHECKS`, not the deterministic registry. Validating it against the registry reports
  `judged_dimension` as a check nobody wrote, which is true of a registry it was never meant to be in.
- **A staleness hash covers what is SENT, not the file that produced it.** Anything else refuses a
  replay for a change that cannot have altered a response.
- **Write the falsifier down before running the fix.** D125's rule, and it paid immediately: the
  criteria edit left CALL-02 and CALL-04 misaligned as required, which made it **ineffective rather
  than over-broad** — a distinction only available because the test was named in advance.
- **A gate that runs only when somebody remembers has quietly stopped verifying.** This phase
  re-earned that twice: `verify_phase3` was built here and initially not wired into CI, and
  `statement_inventory` had never been. Both run on every push now.
- **A count of what is unverified is worth more than an impression of it.** The three mechanisms
  above exist because the caveats were counted and classified rather than read. Two of the fourteen
  caveats turned out to be wrong rather than merely incomplete.

## Constraints that do not lift

- **Never open, glob, grep, cat or diff a transcript in `voice-agent-eval-harness-holdout`**, and do
  not read that repository's commit messages or test docstrings. Counts, rules, call identifiers and
  file names are safe; content is not. If unsure, stop and ask.
- Every change carries a control, registered in `CONTROL-REGISTER.md` and re-derived by an entry in
  `control-mutations.yaml`. **Suspect the mutation before the control** when the gate reports a
  `[FAIL]`.
- **Never write a control that re-implements the rule beside the check.** This phase caught one of its
  own: the credential control serialized a run-log entry itself instead of driving the writer, and
  `RunLogWriter` grew an injectable `environ` so that it did not have to.
- Show every commit message before committing. Never commit a populated `.env` or anything under
  `private/`. Do not push unless asked.
- Worded numbers are live claims and are read by count guards; digits are historical statements.
- A stated measurement in `tests/` or `tools/` prose must be dated or bound, and declared in
  `_STATED_MEASUREMENTS`.
- US spelling, enforced by test.
- `sessions/` holds what a session wrote for the next; the root holds what a mechanism reads by name.
- **An owed item goes in `OBLIGATIONS.md` or the suite turns red.** Writing one into a handover's
  `## What is owed` section and nowhere else is now a build failure, not an oversight.
