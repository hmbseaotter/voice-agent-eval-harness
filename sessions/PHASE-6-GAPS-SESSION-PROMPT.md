# Session prompt — let a check read a declared gap, so a vendor's log can be evaluated

*Paste the section below as the first message of a fresh session in the harness repository. Run it
on **Claude Opus 5** at effort **xhigh**.*

*Why Opus and not the model that opened phase 6: the rule this work needs already exists. Event model
v3 defines what a source may declare it cannot carry, `harness.core.gaps` holds the vocabulary, and
`build_context` refuses a call that declares one. What is left is systematic: every check and every
fact renderer says what it reads, and one reading something a call declares unavailable returns
`unevaluable` naming it. That is building against a written contract across forty-odd entries, which
is the shape phases 2 to 5 were built in.*

*Why xhigh: nothing here spends money, and the work crosses the seam every tier shares. A check that
returns the wrong status for an absence is a false verdict about an agent, which is the failure this
whole project is organized against.*

*State to start from: a clean checkout of `main` at `cf17711` or later, level with `origin/main`,
with CI green. No other session should touch the harness tree while this one runs a chain.*

---

You are closing **OB-51**, which is what phase 6's own goal — *the properties a reader will test* —
still lacks most: today the second adapter reads a vendor-shaped call and nothing can evaluate one.

## What stands today

`--adapter retell` parses Retell's documented call object into a `Call`, and every design call
compares equal to the text adapter's stream on the terms D203 set: identical where the source carries
the material, declared where it does not. **Then the seam refuses it.**
`harness.core.context.build_context` raises `SourceGapError` for any call whose `unavailable` is
non-empty, and its docstring says why: nothing downstream reads the declaration, so every consumer
would turn an absence into a claim. The record facts would render an absent `answered_at` as the text
`None`; the lifecycle check would report a missing `call.ended` for a source that logs no lifecycle;
the judged prompt's explicit negative statement would say no clause was retrieved where the truth is
that nothing here can know.

So the adapter is selected on extraction alone, and `harness run` cannot take it.

## What to read first

- **`src/harness/core/gaps.py`** — `Gap`, the closed vocabulary of eight declarations, with
  `apply`, `check_declared` and `parse_gaps`. A name nothing defines is refused there, which is why
  the vocabulary is closed.
- **`src/harness/core/context.py`**, the refusal and the three populations a check may read.
- **`specs/event-model.md` §5**, the contract an adapter owes, and the v3 note at its head: the model
  admits absence, and a value nobody supplied may not be defaulted.
- **D203** for what v3 changed and why the seam refuses; **D205** for how the inspector reports a
  reading it could not make; **`sessions/HANDOVER-2026-09-20-phase-6-opening.md`** item 1, which is
  OB-51 in the handover's own words.
- **`src/harness/core/result.py`** for the five-value status channel, and what `unevaluable` already
  means in it — the phase-2 contract this work extends rather than invents.

## The work

**1. Every check declares what it reads.** A check states which of the gap vocabulary's declarations
would make its reading impossible — the lifecycle check reads `events.SYSTEM.lifecycle`, the
rule-without-retrieval check reads `events.POLICY`, a record check reads `record.answered_at`. The
declaration belongs beside the check, where a reader of the check sees it, rather than in a table
somewhere else that goes stale.

**2. A check whose reading a call declares unavailable returns `unevaluable`, naming the
declaration.** Not `pass`, which would claim the property holds; not `fail`, which would report a
defect against an agent for something its platform does not log. `unevaluable` is the status phase 2
defined for exactly this and the roll-up already excludes from rate denominators (D23, and the
exclusions D158 asserted per status).

**3. The judged tier's fact renderers do the same.** The prompt's explicit negative statements are
the sharp case: a rendered "no clause was retrieved" over a source with `events.POLICY` declared is
a false statement put in front of a judge. A renderer whose material is declared unavailable says so
in the prompt, or the dimension resting on it is not asked — that is a fork, and it is the owner's.

**4. Then the seam opens.** `build_context` stops refusing a call that declares a gap, and
`harness run --adapter retell` produces a verdict over all sixteen source documents. The refusal's
docstring becomes the record of why it stood, which is how this project has retired other refusals.

**5. Criteria and contract.** Phase 6 has 5 requirements and 12 criteria; whether this work needs a
criterion of its own, or is covered by the adapter's, is a fork for the owner. If a criterion lands,
`MEASURED_CONTRACT`, the `COVERAGE` entry and `tools.verify_phase6` move with it.

## What to hold to

- **Prove the negative before you rely on it.** For each check, plant a call declaring the gap it
  reads and see it return `unevaluable` naming the declaration, and a call declaring an unrelated gap
  and see it evaluate as before. A check that returned `unevaluable` for everything would pass the
  first half and be useless.
- **The design set must not move.** Every design call declares no gap, so every existing verdict,
  the report's bytes and the extraction artifact's hash stay as they are. The snapshot and the
  content hash are the guards; if either moves, stop and say so.
- **`unevaluable` is not a quiet pass.** Count what it hides: `harness inspect` and the report both
  say how many readings were not made, and a run where most checks are unevaluable should be legible
  as such rather than as a clean bill.
- **Every new check gets a control**, driven red before it is trusted, with a row in
  `CONTROL-REGISTER.md` and the count tag moved. There are 354 entries today.

## What this session does not do

- **No live model call.** Judge-model comparison (OB-53) and prompt caching (OB-52) are a later
  session's, briefed to spend. If anything here would issue a call, stop.
- **No rubric or prompt-template edit.** Both are frozen at `rubric-frozen-v1` and pinned by test. A
  renderer change that would alter a recorded request is the version-2 cycle's, not this session's —
  and if the work turns out to need one, that is a finding to raise, not a change to make.
- **No held-out content in this tree**, and nothing from the held-out repository is needed.
- **The design document is not yours** (OB-54): three of its four parts have no source in this tree
  and the owner has parked the question of where they come from.
- **Never tag.**

## How this repository is worked

- **The owner decides every fork**, through a selectable question with your recommendation first.
  Cite the decision that defines a term when you recommend on it. End every substantive turn with an
  **Assumptions** list.
- **The document chain moves together** when a decision lands: the specification's version and its
  changelog entry, the decision record's `Not checked` marker and its refresh sentence, the
  `Document status` paragraph and the numbering line. `Last swept` is not part of that chain: since
  D194 it moves only to a version whose changelog entry is marked `**Swept:**`, and a sweep is due at
  this phase's close (OB-59).
- **Commits:** show each message verbatim and ask; stage files by name; no attribution lines; fetch
  before committing; verify the stored message with `git cat-file commit HEAD | sed '1,/^$/d'`
  compared by `cmp` against the file you committed with. **Do not push unless asked**; before any
  push compare the remote's owner with `gh api user`, watch CI after it, and keep CI runs sequential.
- **CI checks the sibling repository out inside this root**, which D207 records: a test that
  enumerates the repository's own trees must skip a directory carrying its own `.git`. A check that
  is green here and red there is the shape that cost a red `main` on 2026-09-21.
- Write files with LF endings, and write any script that carries escapes with a file-writing tool
  rather than a shell heredoc. US spelling is enforced by test. Worded numbers are live claims read
  by count guards; digits are historical statements.

## Definition of done

- Every check and every fact renderer declares what it reads, and one whose material a call declares
  unavailable returns `unevaluable` naming the declaration, proven both ways per check.
- `harness run --adapter retell` produces a verdict over the sixteen Retell source documents, and the
  design set's verdicts, the report's bytes and the artifact's hash are unchanged.
- OB-51 is closed in `OBLIGATIONS.md` with evidence naming its tests.
- The full chain is green, including `tools/verify_controls.py` over every entry, and a handover in
  `sessions/` records what this leaves owed.

## One thing worth knowing before you start

The refusal you are removing was not caution. It was written because the alternative is a verdict
about an agent computed from a value nobody supplied, and this project has already found that shape
twice: a check keyed to a defaulted field, and a judged dimension asked about material its prompt did
not carry. The declaration exists so that *unknown* and *absent* stop being the same word.

Take the refusal out only when every reader of the thing it protects can say which it is.
