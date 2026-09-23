# Session prompt — build phase 4, the full rubric and the report

> **SPENT — 2026-09-09.** Phase 4 was built and closed; the session's own record is
> `sessions/HANDOVER-2026-09-09-phase-4.md`. Kept as a record, not as a brief to paste.

*Paste the section below as the first message of a fresh session. Run it on **Claude Opus 5** at
effort **max** — the owner settled that on 2026-09-09.*

*Why `max` throughout rather than the `xhigh` phase 3 was built at: this is the first phase where a
design error costs money rather than time. A full run commits over a thousand judged calls — the
`Spending` section below has the figure — so a rubric entry that has to be re-authored means paying
for the run twice. Depth is cheaper than a repeat.*

*Why Opus 5 and not Fable 5.1: the contract is written up front, and the work is data rather than
open-ended design — five dimensions added as rubric entries against an engine that already exists.
Fable was the right call for the phase-3 audit, where there was no contract to implement against and
the task was finding what was absent. That is a different shape of problem.*

*Why a fresh session: this phase authors six rubric prompts, and a session that has read held-out
content cannot design a rubric. The clearance block below is the binding constraint, not a formality.*

---

You are building **phase 4** of the voice-agent evaluation harness: every remaining dimension as
data, the report a human actually reads, and the snapshots that hold both still.

## Read this part first, because it is the only thing here that cannot be undone

**Never read held-out content, anywhere it lives.** Do not open, glob, grep, `cat` or diff any
transcript in `voice-agent-eval-harness-holdout`, and do not read that repository's commit messages
or its test docstrings. Do not open `holdout-authoring-packet/`, nor
the two withheld source folders outside both repositories, which hold the material the corpus was written clean of.

**The line is content versus existence.** Counts, rules, call identifiers and file names are safe —
`HELDOUT_SET` in the repository root is exactly that, and reading it is expected. A transcript is
not, and neither is a sentence *about* what one contains.

**Why it binds here.** Phase 4 authors **five judged rubric entries and a synthesis dimension** —
six new prompts, six sets of criteria, six scales. A session that has read held-out content cannot
design or review a rubric, because it then knows what the rubric will be scored against, and P5
measures agreement against exactly that. The clearance argument is phase 3's, six times over — and
it binds harder because **P5 opens with the `rubric-frozen-v1` tag**, so what you author here is what
gets frozen.

**If you are unsure which side of the line something falls on, stop and ask** rather than opening it.

## Start here

1. Read `sessions/HANDOVER-2026-09-09-phase-3.md` — closed, and it carries what phase 3 measured
   rather than only what it built. Its `## What the live runs found` section is the part that
   changes how you should approach this phase.
2. Read `sessions/HANDOVER-2026-09-09-phase-3-audit.md` — an independent audit of phase 3 and its
   remediation. **Read its method before its findings.** The audit ran a *mutation sweep* rather than
   a reading, and that instrument found a population the control register cannot see.
3. Read `OBLIGATIONS.md`. It is the live view of what is outstanding, and **five of its rows name
   phase 4 as their trigger**: `OB-6` the remaining judged dimensions, `OB-8` the roll-up and gate,
   `OB-12` what D7's injection pair is measured on, `OB-13` the run-log format, `OB-14` whether a run
   of refusals counts as having run. `OB-7` names phase 5 and is the one to leave alone.
4. Run the gates before changing anything, so a failure later is yours:

```bash
uv run pytest -q && uv run python tools/verify_phase1.py && uv run python -m tools.verify_phase2 && uv run python -m tools.verify_phase3 && uv run python tools/statement_inventory.py && uv run python tools/verify_controls.py
```

Expect **1,040 passing**, 21 of 21 `[P1]`, 24 of 24 `[P2]`, 23 of 23 `[P3]`, the inventory clean, and
**58 of 58 controls** driven red by their own defect. `main` is pushed and CI is green at `0819598`.
Every one of these runs in CI, so a gate you break is a build you break.

`tools/verify_controls.py` takes about half an hour. Run it before you start and once before you
commit, not between edits.

## What phase 4 is

**The contract is the specification's `[P4]` requirements and acceptance criteria** in
`specs/voice-agent-eval-harness.md`, at 0.27.0. Phase 1's build prompt was superseded at the end of
that phase; phases 2 and 3 ran off their own clauses and this is the same shape. Three deliverables:

- **The remaining five judged dimensions, added as rubric data only**, plus the call-level
  **synthesis dimension** constrained to cite the dimensions it rests on.
- **Report generation for two audiences** — agent-behavior findings versus data and integration
  findings — with orthogonal labels and an inline non-determinism caveat.
- **Snapshot tests at their correct scopes**: Tier A byte-identical in **both** modes, the full
  report byte-identical in **replay only**. D8 is explicit that conflating those destroys the
  regression signal the moment somebody regenerates a snapshot to make CI green.

The `[P4]` markers also cover the roll-up phase 3 deliberately did not build: the verdict
distribution across N, the rate computed over `applicable` results only with every other status
reported beside it, the escaping of model-authored text that would corrupt a table, and the
synthesis citation check.

**"Done when: adding a dimension required no engine change."** That is the specification's own
phrasing and it is the real acceptance test of phase 3's work. If you find yourself editing
`src/harness/judge/` to add a dimension, that is a finding about phase 3 and it should be recorded as
one rather than absorbed.

## Open by checking whether your contract covers itself

**Phase 4's contract is five `[P4]` requirement statements and eleven `[P4]` acceptance criteria.**
That is small — phase 3 carried 23 requirement statements — because the engine is already specified
and this phase is mostly data. It is also the shape D104 found dangerous: phase 2 opened by asking
whether its criteria covered its requirements, found **five of twelve covered in half**, each time in
the half the requirement named, and added six criteria before writing a line of code.

**Nothing mechanizes that check.** `MEASURED_CONTRACT` in `tests/test_document_counts.py` pins the
counts per phase and says nothing about coverage. Do what phase 2 did, requirement by requirement,
and record what you find — including "all five are fully covered", which is a result rather than a
formality.

Watch particularly for a criterion that **cannot distinguish the design from its inversion**. That is
the specific defect D104 found: a grounding criterion whose fixture resolved either way.

## Decisions you inherit, so you need not re-ask

- **Sonnet 5 for the dimensions, Opus 5 for synthesis** (D16), **N=10** (D17), and `max_tokens`,
  `effort`, `question`, `criteria`, `scale_definitions` and `requires_facts` declared per entry. The
  loader refuses each missing field by name, and `max_tokens` by a refusal of its own (D24).
- **`max_tokens` bounds thinking plus output.** Phase 3's entry was drafted at 2048 on reasoning
  that considered only the answer, and adaptive thinking at effort `high` would have truncated it.
  4096 is what the shipped entry uses; a dimension with a larger fact population may need more.
- **N repetitions are reported individually at P3, and the distribution is yours** (D124). Choosing
  the aggregation is a decision, not a helper — first, modal and worst are three different claims
  about what N means. Record it.
- **A judge/gold-set disagreement is either an entry defect or a measurement, and the two are
  treated oppositely** (D125). This is the decision that will matter most to you, because you are
  about to produce five dimensions' worth of disagreements. If the entry's own definition does not
  decide the case, that is a defect and you fix it — and the fix must be defensible without
  reference to which calls disagreed. If the definition decides it and the judge got it wrong
  anyway, that is the measurement, and editing until it agrees is overfitting to sixteen transcripts
  you can read. **Write the falsifier down before you run the fix.** Phase 3 did, and it is the only
  reason a failed fix could be called ineffective rather than over-broad.
- **Anything derivable from the context record, tool calls, results, state and their order is
  `assert`, not `judge`** (D42). Phase 3 surfaced one class that is currently inside a judged
  dimension and probably should not be — *the agent stated policy terms with no successful retrieval
  behind them*. Whether a retrieval happened is an event-stream question. Decide it deliberately
  rather than inheriting it; `OB-12` is the row.
- **Owed items go in `OBLIGATIONS.md`** (D126). Writing one into a handover's `## What is owed`
  section and nowhere else is a build failure. The harvest keys on *(handover filename, item
  number)* **and on an anchor into the item's own title**, so renaming a heading breaks a row on
  purpose.
- **The judged tier's exit codes are the deterministic tier's** (D127, extending D114): `0` the tier
  ran, `2` the run could not be made, `3` the tier ran and could not be completed. `1` stays a
  finding about the agent and the judged tier does not use it — **until you build the gate, which is
  the change that gives it one.** A run whose every result is `refused` exits 0 today, deliberately
  and provisionally: the alternative is a threshold, and *how many refusals are too many* is what
  your roll-up exists to answer. `OB-14` is the row. Note that the specification already decides the
  adjacent question — `refused` results leave the rate's denominator — so what is open is the exit
  code and not the arithmetic.
- **The run log stores what was sent once and references it by content hash** (D128), and **it is
  your first task, before your first live pass.** `system` is 45% of the committed log as one string
  repeated 160 times; `schema` is another 4%. At phase 4's shape the same format is 7–8MB. The change
  is storage only — replay keys on the request hash, not on the file layout — but it invalidates the
  committed log, and re-recording is a live run. Do it before you spend, not after. `OB-13`.
- **The specification's sweep trigger is mechanized at phase completion** (D129). When you close your
  handover with `Status: closed`, a test requires `Last swept` to have reached the last decision that
  handover records. Sweep and bump before you close, or the build goes red at the end.

## Five things that will break the moment you add a second judged entry, and should

Each is deliberate. None is a defect. All want updating in the same commit as the entry that trips
them.

1. **`test_the_shipped_rubric_declares_exactly_one_judged_entry`** asserts the list is exactly
   `["J-policy-alignment"]`. It is D108's successor and it says **one**, not "at least one", because
   a second arriving early would have been P4 data authored inside P3. **It is named as evidence by
   two verifiers** — `tools/verify_phase2.py` for "produces a result for every deterministic entry
   and for no judged entry", and `tools/verify_phase3.py` for the judged tier being declared at all.
   Whatever replaces it has to still buy both claims, or those criteria lose their evidence.
2. **`JUDGED_AGREEMENT_PENDING`** in `tests/test_rubric_coverage.py` must name every judged entry
   whose agreement is not asserted, and the coverage guard is total across both tiers. A new judged
   entry is either in a family firing table or declared pending; there is no third option and no
   silence.
3. **The committed reference run log stops covering the rubric.** `runs/reference-corpus-0.6.0.jsonl`
   holds 160 calls for one dimension. Add a second and replay aborts on its first request with a
   cache miss — correctly. **Re-recording is a live run, and it is the phase's main cost.** Note the
   ordering constraint this creates with D128: change the format first, record once.
4. **`test_the_preflight_estimate_brackets_what_the_real_run_recorded`** compares the printed
   estimate against every input count in the committed log, per call. A new dimension whose prompt
   renders larger than its estimate fails it — which is the check working, and the fix is the
   divisor and not the assertion.
5. **`tests/test_phase3_acceptance.py`** binds each verifier's list to the specification, and its
   `VERIFIERS` table takes one row per phase. This phase's verifier needs a row there with its
   declared extras and requirement-anchor counts, or it ships with the defect phase 3's verifier
   shipped with: a closing line counting its own list. (The path is not written here because
   `tools/statement_inventory.py` resolves every path this document names, and a file phase 4 has
   not created yet does not resolve — which is the guard working.)

## Spending

Phase 3 measured what phase 3 cost, so this is derived rather than guessed.

**One dimension over the design set is 160 calls and cost $1.65** — `$0.0103` a call on Sonnet 5,
from the committed log's own token counts at the declared rates. Five dimensions is 800 calls and
about **$8**, plus phase 3's own entry re-recorded, plus **160 synthesis calls on Opus 5**, which
carry every other dimension's result and are the least predictable half: at 4,000 input and 1,200
output tokens each that is about **$8** on its own. **Budget $15–25 for a full pass**, with the
synthesis half carrying the uncertainty.

**The printed pre-flight estimate is not that number and is not meant to be.** It prints $7.39 for
one dimension against an actual $1.65, because it charges the full `max_tokens` for output on every
call. That is deliberate: an operator approves a ceiling. Do not "fix" the gap.

**You will want more than one pass.** Phase 3 took three: one to find out, one after a template fix,
and one to test a criteria change that failed. Budget for that shape rather than for a single run,
and **say what a run will cost and get agreement before issuing it.** `--mode live` refuses to
proceed without confirmation; `--max-calls` caps a run and counts **logical calls, not requests** —
one call can cost four on a transient failure.

## How this project works

These are not stylistic preferences. Each exists because something went wrong without it.

- **Every change carries a control, driven red and restored.** A check whose only evidence is that
  it has never fired has been proven against nothing. Register it in `CONTROL-REGISTER.md` and give
  it an entry in `control-mutations.yaml` so `tools/verify_controls.py` re-derives the verdict.
- **A control must be driven by a defect that produces a difference**, not by deleting the check.
  The phase-3 audit's remediation registered a mutation that removed a comparison, and the control
  stayed green — correctly, because with nothing for the comparison to find, removing it changes
  nothing. Restore the *state* the guard exists to detect.
- **When a control looks disconnected, suspect the mutation first.** That gate has printed a
  `[FAIL]` that was not a finding 5 times: 3 mutations aimed at code the control does not reach, 1
  masked by a stale bytecode cache, and 1 that deleted the check instead of restoring the state it
  detects. Check the entry's `defect:` line against what the control actually plants. It has also
  printed a `[STOP]` that was not a finding, halting a sweep at entry 51 of 58 because a working
  control's failure output mentioned `Status.ERRORED`.
- **Do not write a control that re-implements the rule beside the check.** Give the check a named
  function and make the control call it. 7 controls in this tree were written the other way and
  every one was measuring nothing.
- **A guard that exists in the code and is driven by nothing is invisible to the control register**,
  which audits controls rather than checks. That is `OB-2`, and the instrument that finds them is a
  **mutation sweep**: restore a fail-open-shaped defect into a copy of the tree, one at a time, and
  see whether the suite notices. The phase-3 audit ran fourteen and seven were missed. Copy the
  method, and make it produce a positive before believing a null.
- **Run the suite somewhere that is not your checkout before you claim it passes.** A test that
  depended on the operator having a real `.env` was green locally and would have been red on CI,
  found by checking each commit out into a worktree. `git worktree` costs seconds; a red build costs
  a push.
- **Replace a statement in prose with a value read off the thing it describes.** Two of phase 3's
  caveats claimed a property was unmechanizable when it was not.
- **Worded numbers are live claims** and are read by count guards; **digits are historical
  statements**. When a count would need maintaining, de-quantify it or tag it so it is computed.
- **A stated measurement in `tests/` or `tools/` prose must be dated or bound**, and declared in
  `_STATED_MEASUREMENTS`.
- **US spelling**, enforced by test. It fired twice in phase 3, once at the cost of a recorded run.
- **Show every commit message before committing**, and commit only after approval. Stage
  selectively. Never commit a populated `.env` or anything under `private/`. **Do not push unless
  asked.**
- **`sessions/` holds what a session wrote for the next; the root holds what a mechanism reads by
  name.** Put your handover in `sessions/`.

## Scope

Phase 4 is the three deliverables above and the `[P4]` clauses that support them. **Do not build P5,
P6 or P7** — held-out labels, judge validation, severity-weighted coverage, the second adapter, the
log inspector, prompt caching, judge-model comparison and the LLM-as-parser stage are later phases
with their own contracts.

**In particular, do not author or read held-out labels.** They must not exist until after the
`rubric-frozen-v1` tag, and their commit must cite this repository's freeze SHA (D21). Phase 4 is
the phase that makes that tag meaningful, which is a reason to be careful about it rather than a
reason to reach for it.
