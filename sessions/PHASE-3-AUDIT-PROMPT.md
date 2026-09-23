# Session prompt — audit phase 3, the judged tier

> **SPENT — 2026-09-09.** The audit this brief was written for ran; its report is
> `sessions/AUDIT-2026-09-09-phase-3.md`, whose banner carries what was acted on. Kept as
> the record of what that session was asked to read, not as a brief to paste.

*Paste the section below as the first message of a fresh session. Run it on **Claude Fable 5.1** at
effort **max**.*

*Why a different model from the builder: phase 3 was built on Claude Opus 5 at effort `xhigh`
(recorded in `sessions/PHASE-3-SESSION-PROMPT.md`). A fresh session supplies most of the
independence — no memory of why a choice seemed fine, no commitment to defend — but a model auditing
its own output shares the blind spots that produced it. A different model is a second axis and it is
cheap to take. `max` because an audit's failure mode is missing something, which is what reasoning
depth buys, and the scope is bounded to one phase.*

*Expect long turns at this effort. That is the setting working, not a hang.*

---

You are auditing **phase 3** of the voice-agent evaluation harness. You did not build it. That is
the point of you.

## Read this part first, because it is the only thing here that cannot be undone

**Never read held-out content, anywhere it lives.** Do not open, glob, grep, `cat` or diff any
transcript in `voice-agent-eval-harness-holdout`, and do not read that repository's commit messages
or its test docstrings. Do not open `holdout-authoring-packet/`, nor
the two withheld source folders outside both repositories, which hold the material the corpus was written clean of.

**The line is content versus existence.** Counts, rules, call identifiers and file names are safe —
`HELDOUT_SET` in the repository root is exactly that. A transcript is not, and neither is a sentence
*about* what one contains.

**Why it matters here.** Phase 3 authored a judged rubric entry. Auditing it is rubric work, and a
session that has read held-out content cannot do rubric work: it then knows what the rubric will be
scored against. If you are unsure which side of the line something falls on, stop and ask.

## The rule this project applies to its own audits

**Reproduce before you report.** This is not caution, it is measured: of the phase-2 audit's 17
findings, **3 did not hold**; of the 2026-08-29 audit's 44, **3 did not hold**. The decision record
draws the conclusion explicitly — that ratio is the argument for reproducing before acting, not
against commissioning audits.

So every finding you report carries **the reproduction that produced it**: the command, the input,
the observed output. A finding you reached by reading alone is still worth reporting — mark it
`(by reading)` and say what you could not run. Never present the two as the same thing.

**One item in the phase-2 audit broke the corpus if taken literally.** Widening a resolution search
as it recommended cleared a call the entry exists to fail. Check what your own recommendations would
do before recommending them.

## Baseline first

Reproduce the state before you judge it. A failure you find later is then yours, not inherited.

```bash
uv run pytest -q && uv run python tools/verify_phase1.py && uv run python -m tools.verify_phase2 && uv run python -m tools.verify_phase3 && uv run python tools/statement_inventory.py && uv run python tools/verify_controls.py
```

Note that the phase-2 and phase-3 verifiers are invoked as **modules** and the other two as paths;
`python tools/verify_phase3.py` fails with a `ModuleNotFoundError`, because the phase-3 verifier
imports the reporting loop from phase 2 rather than keeping a third copy of it.

Record what you actually observed — counts, exit codes, the artifact digest — in the report's first
section. If any number in this prompt or in the handover disagrees with what you measure, **the
measurement wins and the disagreement is a finding.**

## What you are auditing

The span is `db02c76..a9abd45` — 24 commits, roughly 8,800 insertions across 36 files. Read
`sessions/HANDOVER-2026-09-09-phase-3.md` first; it is the builder's own account and therefore both
your best map and a document with an interest in the outcome.

**The contract is the specification's `[P3]` requirements and acceptance criteria** in
`specs/voice-agent-eval-harness.md`. Audit against that, not against the handover's description of
it. Where the two disagree, that is a finding.

The surfaces:

- **`src/harness/core/transport.py`** — the model transport seam: live and replay implementations,
  unconditional run-log recording, staleness refusal.
- **`src/harness/judge/`** — `engine.py`, `prompt.py`, `citations.py`: one judged dimension end to
  end, with the tagged citation universe, set-membership validation, informed retry, and `errored`
  on exhaustion.
- **`prompts/judge-dimension.v1.md`** — the judge prompt, versioned as corpus data.
- **`rubric.yaml`** — one `tier: judge` entry, added at P3.
- **`runs/reference-corpus-0.6.0.jsonl`** — the committed reference log the replay path reads.
- **`tools/verify_phase3.py`** — the phase gate. Audit the verifier as hard as the code: a tick that
  does not stand for what it claims is this project's most-repeated defect.
- **`OBLIGATIONS.md` + `tests/test_obligations.py`** — a mechanism built this phase.
- Decisions **D122–D126**, and the `Not checked` block.

## Where to look hardest

Ordered by what this project's history says is most likely to be wrong.

**1. Fail-open paths.** The recurring shape. Phase 2's audit found an exit code that collapsed four
states into "held", a conditional CI check that verified nothing while reporting success, and globs
that contributed nothing to an aggregate floor. Phase 3 adds a network boundary, a retry loop and a
replay path — three new places for a failure to read as a success. Ask of every error path: *what
does this look like when it silently does nothing?*

**2. Credential and secret exposure — treat this as a security review.** `[P3]` requires that
credential values are excluded from every log, report, error message and run-log entry. Phase 3 is
the first code that sends data to an external service and the first that spends money. Check the
run-log writer, every exception path, every `repr`, and what an SDK exception carries by default.
`.env.example` was added this phase; check what the real `.env` shape implies.

**3. The verifier's ticks, one at a time.** For each criterion `verify_phase3.py` prints PASS for,
ask what would have to break for it to print FAIL, and whether that is the thing the criterion
claims. This project has repeatedly found a criterion ticked against a *neighbor* of its claim — a
guard narrower than its rule is green and blind.

**4. Controls that measure nothing.** `CONTROL-REGISTER.md` and `control-mutations.yaml` exist
because 7 controls in this tree were found to be measuring nothing, all one shape: **a control that
re-implements the rule beside the check instead of calling it.** Phase 3 added controls. Check them
for that shape, and check that every new check that needed a control got one. `tools/verify_controls.py`
re-derives the registered ones; a control with no entry is one nobody has driven either way.

**5. Prose that was true when written.** The handover names this as the largest and least
mechanizable class, with a worked example: the `Not checked` block said "No live call has been made"
after hundreds of them had been, every guard passed, and a human found it. The document guards verify
that identifiers resolve and that counts agree — **none reads prose for truth.** Sample the live
claims in the README, the spec, the decision record's recent entries and the handover, and check them
against the tree. Report what you sampled and what you did not; an inventory that does not say its
own coverage is the shape this project keeps catching.

**6. Requirements against code, in both directions.** Every `[P3]` clause should have code, and every
new behavior should have a requirement. Phase 2's audit found an exception-to-`errored` conversion
with no requirement behind it — sound behavior, missing consequence.

## What the builder itself flagged — probe these, do not inherit them

The handover records these as open. Treat each as a **claim to verify**, not a conclusion. If one
turns out understated, that is a finding; if overstated, say so.

- **Agreement is measured, not asserted.** The judge agreed with the gold set on 2 of 3 seeded
  instances, and the third is described as a clean miss. A second finding was found, a fix attempted,
  and the fix reverted. Read why, and decide whether the revert was right.
- **~8 acceptance criteria have a viable mechanism that is not built; ~12 have none** — out of 68
  across three phases, with 14 carrying caveats and 15 open `Not checked` entries. Those numbers are
  the builder's own classification and the classification is judgment. Sample it.
- **`OBLIGATIONS.md` does not cover the `Not checked` block's open entries** — a differently-shaped
  population deliberately not folded in. Is that the right call?
- **The obligations harvest keys on (handover filename, item number)**, so renumbering or deleting an
  owed heading breaks a row. Is that fragility guarded, or only documented?
- **`runs/reference-corpus-0.6.0.jsonl` is about 1.2MB**, roughly half of it a byte-identical system
  prompt repeated across every entry. Nobody has decided whether that is acceptable. Decide whether
  it needs deciding.

## What to produce

A report in `sessions/`, named for the phase and dated the day you write it, following the `AUDIT-`
convention the two reports already there use. Read one of them before writing yours — the format
below is theirs, not an invention of this prompt.

1. **Baseline, reproduced** — what you ran and what it printed.
2. **Findings**, each with an id (`P3-1`, …), a severity, a `(reproduced)` or `(by reading)` marker,
   tags naming the category, the reproduction, the mechanism (`file:line`), and a **closure** —
   what would fix it, not merely that it is wrong.
   - **High** = a fail-open path, a credential exposure, or a verifier tick that does not stand for
     what it claims.
   - **Medium** = a real gap the held-out set or the next phase will hit.
   - **Low** = hygiene, duplication, or an untested edge with no current instance.
3. **Requirements against code, both directions.**
4. **Counts, enumerations, and the mechanisms that hold them.**
5. **Mechanisms versus memory** — what is enforced versus what depends on somebody remembering.
6. **What was not checked** — explicitly, including what you were not allowed to read.
7. **Suggested order of work.**

Add a maintained **status banner** at the top, as both existing reports carry: findings are closed by
later sessions and the banner is how a reader knows which. A banner that goes stale in your own
direction is a live wrong statement — phase 2's did, and its own author found it.

## Rules

- **Audit, do not fix.** Report and propose closures. If you find something you think must be fixed
  during the audit, say why and ask first.
- **Do not make a live model call without asking.** Replay must work without an API key; if it does
  not, that is itself a finding. A live call spends real money and needs the owner's agreement,
  including what it will cost.
- **Do not build P4.** The remaining judged dimensions, synthesis, reports and snapshots are the next
  phase and it has its own prompt.
- Show every commit message before committing, and commit only after approval. Never commit a
  populated `.env` or anything under `private/`. **Do not push unless asked.**
- Worded numbers are live claims read by count guards; digits are historical statements. US spelling
  is enforced by test. A stated measurement in `tests/` or `tools/` prose must be dated or bound.
- `sessions/` holds what a session wrote for the next; the root holds what a mechanism reads by name.

## One thing worth knowing before you start

Three times in this project an audit instrument was itself the defect — a patch tool that reported
success while applying nothing, a gate that could not see the code it was testing, and a gate whose
verdict depended on machine speed. Each looked like a finding about the tree.

**Before you trust a null result, prove your instrument can produce a positive one.** A clean scan
from something that is not connected is indistinguishable from a clean tree.
