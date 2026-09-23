# Session prompt — audit phase 4, and the obligations closed before the freeze

> **SPENT — 2026-09-12.** The audit ran; its report is
> `sessions/AUDIT-2026-09-12-phase-4.md` and its remediation
> `sessions/HANDOVER-2026-09-12-phase-4-audit.md`. Kept as a record, not as a brief to paste.

*Paste the section below as the first message of a fresh session. Run it on **Claude Fable 5.1** at
effort **max**.*

*Why a different model from the builder: phase 4 was built on Claude Opus 5 at effort `max`
(recorded in `sessions/PHASE-4-SESSION-PROMPT.md`), and the obligations closed after it were worked on
Claude Opus 5 as well. A fresh session supplies most of the independence — no memory of why a choice
seemed fine, no commitment to defend — but a model auditing its own output shares the blind spots that
produced it. A different model is a second axis, cheap to take, and the phase-3 audit took it for the
same reason. `max` because an audit's failure mode is missing something, which is what reasoning depth
buys, and because what this audit passes is what `rubric-frozen-v1` freezes.*

*Expect long turns at this effort. That is the setting working, not a hang.*

---

You are auditing **phase 4** of the voice-agent evaluation harness, and the obligations closed after
it and before the `rubric-frozen-v1` tag. You did not build any of it. That is the point of you.

## Read this part first, because it is the only thing here that cannot be undone

**Never read held-out content, anywhere it lives.** Do not open, glob, grep, `cat` or diff any
transcript in `voice-agent-eval-harness-holdout`, and do not read that repository's commit messages
or its test docstrings. Do not open `holdout-authoring-packet/`, nor
the two withheld source folders outside both repositories, which hold the material the corpus was written clean of. In this repository, do not open `HOLDOUT-OBLIGATIONS.md`,
`sessions/HOLDOUT-SESSION-PROMPT.md` or `sessions/HOLDOUT-REPAIR-BRIEF.md`. When you search this
repository, name the paths you search rather than searching from its root.

**The line is content versus existence.** Counts, rules, call identifiers and file names are safe —
`HELDOUT_SET` in the repository root is exactly that. A transcript is not, and neither is a sentence
*about* what one contains.

**Why it matters here.** Everything in this span is rubric work — seven judged entries, the synthesis,
the roll-up and its gate — and the freeze follows this audit and its remediation. A session that has
read held-out content cannot do rubric work: it then knows what the rubric will be scored against, and
the tag would certify a rubric reviewed with that knowledge. If you are unsure which side of the line
something falls on, stop and ask.

## The rule this project applies to its own audits

**Reproduce before you report.** This is not caution, it is measured: of the phase-2 audit's 17
findings, **3 did not hold**; of the 2026-08-29 audit's 44, **3 did not hold**. The phase-3 audit's 23
needed no correction, and its banner records why: every reproducible finding was reproduced
independently before it was acted on. The decision record draws the conclusion explicitly — that ratio
is the argument for reproducing before acting, not against commissioning audits.

So every finding you report carries **the reproduction that produced it**: the command, the input,
the observed output. A finding you reached by reading alone is still worth reporting — mark it
`(by reading)` and say what you could not run. Never present the two as the same thing.

**One item in the phase-2 audit broke the corpus if taken literally.** Widening a resolution search
as it recommended cleared a call the entry exists to fail. Check what your own recommendations would
do before recommending them.

## Baseline first

Reproduce the state before you judge it. A failure you find later is then yours, not inherited.

```bash
uv run pytest -q && uv run python tools/verify_phase1.py && uv run python -m tools.verify_phase2 && uv run python -m tools.verify_phase3 && uv run python -m tools.verify_phase4 && uv run python tools/statement_inventory.py && uv run python tools/verify_controls.py
```

The phase-2, phase-3 and phase-4 verifiers are invoked as **modules** and the other tools as paths,
because each of those three verifiers imports machinery from an earlier one rather than keeping a copy
of it; `python tools/verify_phase3.py` fails with a `ModuleNotFoundError` for exactly that reason.
Each verifier also re-runs the whole suite, and `tools/verify_controls.py` re-derives every entry in
`control-mutations.yaml` against its own copy of the tree, so the baseline takes a while; let it
finish. Replay needs no API key; if anything in the baseline asks for one, that is a finding.

Record what you actually observed — counts, exit codes, the artifact digests — in the report's first
section. If any number in this prompt, the handover or the decision record disagrees with what you
measure, **the measurement wins and the disagreement is a finding.**

## What you are auditing

The span is `7860094..6f7ae94` — 17 commits, about 12,900 insertions across 57 files — in two parts:

- **Phase 4 itself**, `7860094..d5daa44`, 7 commits: the five further judged dimensions, the
  synthesis with its citation check, the judged roll-up and its gate, the two-audience report, the
  snapshot, and the reference run recorded against them. Decisions **D130–D151**, and the
  specification's sweep to 0.28.0.
- **The obligations closed before the freeze**, `d5daa44..6f7ae94`, 10 commits: OB-12 closed at its
  trigger; the pin rule ported from `comparative-judgment`; OB-17's expected cost (D152); OB-20's
  resume (D153); OB-22's per-repetition resample, with its falsifier committed first, and the
  synthesis's own ceiling (D154, D155); a correction of six ceiling and streaming statements; OB-19's
  cut separation, exported by the severity tool at schema 3 and re-derived here (D156); phase 5's
  contract, read before the phase opens (D157); and the severity loader's docstring, which still
  described the state D148 replaced. The tool's half of OB-19 is `comparative-judgment` `2bdc195`,
  its D34.

Read `sessions/HANDOVER-2026-09-09-phase-4.md` first; it is the builder's own account and therefore
both your best map and a document with an interest in the outcome. It is still `open`, and no separate
handover was written for the obligations: for those, D152–D157, the registers and the commit messages
are the account.

**The contract is the specification's `[P4]` requirements and acceptance criteria** in
`specs/voice-agent-eval-harness.md` — 6 and 21 — and, for each obligation closed in the span, the
`evidence:` its row gives in `OBLIGATIONS.md`. Audit against those, not against the handover's
description of them. Where the two disagree, that is a finding.

The surfaces:

- **`src/harness/judge/`** — `engine.py` (the judged run, and the synthesis's resample per repetition),
  `rollup.py` (N repetitions to one verdict, and the gate), `prompt.py`, `citations.py`.
- **`src/harness/report.py`** and **`snapshots/report.md`** — the two-audience report and the snapshot
  it is compared against.
- **`src/harness/cli.py`** — the judged run's exit codes, the live pre-flight's two figures, `--resume`.
- **`src/harness/core/transport.py`** — the retry window and the resuming transport.
- **`src/harness/core/rubric.py`** and **`rubric.yaml`** — seven judged entries, their ceilings and
  preconditions.
- **`src/harness/core/severity.py`** and **`corpus/findings.severity.json`** — severity schema 3 and
  the cut cross-check.
- **`prompts/judge-dimension.v1.md`** and **`runs/reference-corpus-0.6.0.jsonl`** — the judge prompt,
  and the reference log replay reads, recorded across two live sessions.
- **`tools/verify_phase4.py`**, **`tools/verify_controls.py`** and **`tools/check_spec_interface.py`**
  — audit the gates as hard as the code: a tick that does not stand for what it claims is this
  project's most-repeated defect.
- **`tests/test_contract_coverage.py`**, **`OBLIGATIONS.md`**, **`CONTROL-REGISTER.md`** and
  **`control-mutations.yaml`** — the mechanisms that say what is covered, owed and connected.
- Decisions **D130–D157**, and the `Not checked` block, which is dated `as of 0.28.0 @ D151`.

## Where to look hardest

Ordered by what this project's history says is most likely to be wrong.

**1. Fail-open paths, now inside a gate.** The judged tier has a verdict and exit codes, and this span
added a path that serves recorded answers and issues only what is missing. Ask of every error path:
*what does this look like when it silently does nothing?* — a resume that serves nothing, a roll-up
over no applicable results, a report rendered from a log that measured nothing, a severity file whose
cuts are empty. And because the resume reads a run log back into a live run, check that nothing
scrubbed on the way out comes back in the clear, and that a log recorded under another rubric cannot
be resumed.

**2. The verifier's ticks, one at a time.** For each criterion `verify_phase4.py` prints PASS for, ask
what would have to break for it to print FAIL, and whether that is the thing the criterion claims. This
project has repeatedly found a criterion ticked against a *neighbor* of its claim — a guard narrower
than its rule is green and blind, and D142 found the inverse: a guard wider than its rule is red and
uninformative.

**3. Controls that measure nothing.** `control-mutations.yaml` holds 104 entries. This span found
controls that were skipped and read as passing (D143), and controls whose tests read the committed
artifact rather than the code the mutation changed (D151). Check the controls added since for those
shapes and for the original one — a control that re-implements the rule beside the check instead of
calling it — and check that every new check that needed a control got one.

**4. Second definitions.** D148 and D156 each recompute in this repository something the severity tool
defines — a content hash, a between-set — and call the pair a cross-check because the two are compared
on every run. Check that each comparison runs over what it claims to, and look for a second definition
that nothing compares.

**5. Measurements that became pins.** Several numbers in this span were measured from a recording or an
export and pinned: the negative-instance firings, the informed retries, the cut separation. A pin that
fails when its measurement moves in either direction is this project's idiom. Find the pins that would
stay green if the thing they measure moved the way that matters.

**6. Prose that was true when written.** The largest and least mechanizable class, and it arrived in
this span at least three times: `CONTROL-REGISTER.md` misstating its own size (D146), six ceiling and
streaming statements a single commit left untrue, and a docstring in the severity loader still
describing the state D148 replaced. The document guards verify that identifiers resolve and that counts
agree — **none reads prose for truth.** Sample the live claims in the README, the specification, the
recent decisions, the registers, the docstrings and the handover, and check them against the tree.
Report what you sampled and what you did not.

**7. Requirements against code, in both directions.** Every `[P4]` clause should have code, and every
new behavior should have a requirement or a decision behind it. The live path spends money: check the
pre-flight's expected figure and its ceiling against what the committed log records.

## What the builder itself flagged — probe these, do not inherit them

Treat each as a **claim to verify**, not a conclusion. If one turns out understated, that is a finding;
if overstated, say so.

- **The reference log was assembled from two live sessions** (D153), and its synthesis reads a
  resample of the dimensions' answers per repetition (D154). The falsifier was committed before the
  change; D154 records every condition cleared on the first recording, and a second recording with the
  same split calls and no modal verdict moved. Check the conditions against the log, not against D154's
  account of them.
- **The synthesis's ceiling is 16384 while every dimension's is 8192, and nothing guards 16384 as
  such** (D155): the fill-fraction watcher would pass at 8192 too.
- **The expected cost prices each entry at the mean answer its first attempts recorded** (D152).
  Decide whether first attempts are the right population.
- **Severity schema 3** (D156): the fields inside a cut are required by the loader and not asserted
  across repositories; an empty `cuts` is accepted; the separation pin detects a change rather than a
  defect; and a finding can still change band with the pin unchanged, which is `OB-23`.
- **Phase 5's contract was read before it opens** (D157), and two criteria were added. Five of its six
  criteria back no requirement statement, which the coverage table cannot see.
- **Open obligations**: `OB-1` to `OB-4`, `OB-9` and `OB-15` are `open`; `OB-5`, `OB-7`, `OB-16` and
  `OB-23` are `deferred`. For each deferred row, ask whether its trigger is an event somebody will
  notice.
- **The sweep marker sits at D151 with D152–D157 accrued**, and the phase-4 handover is still `open`.
  Closing it requires the marker to reach the last decision it records.
- **`comparative-judgment` writes its export and its store with Windows line endings when it runs on
  Windows.** Its `write_text` calls and its log append pass no `newline`, so on 2026-09-12 the
  store's comparison log held 417 CR bytes and a fresh export 705, before git normalized the export on
  commit. `comparison_log_hash` is taken over the log's raw bytes and `run_id` derives from it, so the
  same judgments recorded on another platform would carry a different hash and a different id. Left
  unfixed before this audit on the owner's decision, because the fix has a trade-off of its own: LF
  appends to a log already written with CRLF. Size it, and say what the fix should be.

## What to produce

A report in `sessions/`, named for the phase and dated the day you write it, following the `AUDIT-`
convention the three reports already there use. Read one of them before writing yours — the format
below is theirs, not an invention of this prompt.

1. **Baseline, reproduced** — what you ran and what it printed.
2. **Findings**, each with an id (`P4-1`, …), a severity, a `(reproduced)` or `(by reading)` marker,
   tags naming the category, the reproduction, the mechanism (`file:line`), and a **closure** — what
   would fix it, not merely that it is wrong.
   - **High** = a fail-open path, a credential exposure, or a gate or verifier tick that does not
     stand for what it claims.
   - **Medium** = a real gap the freeze, the held-out run or the next phase will hit.
   - **Low** = hygiene, duplication, or an untested edge with no current instance.
3. **Requirements against code, both directions.**
4. **Counts, enumerations, and the mechanisms that hold them.**
5. **Mechanisms versus memory** — what is enforced versus what depends on somebody remembering.
6. **What was not checked** — explicitly, including what you were not allowed to read.
7. **Suggested order of work**, with what must close before `rubric-frozen-v1` separated from what can
   follow it.

Add a maintained **status banner** at the top, as the existing reports carry: findings are closed by
later sessions and the banner is how a reader knows which. A banner that goes stale in your own
direction is a live wrong statement.

## Rules

- **Audit, do not fix.** Report and propose closures. If you find something you think must be fixed
  during the audit, say why and ask first.
- **Do not make a live model call without asking.** A live pass prints what it is expected to cost
  beside the most it can cost — $14.78 against $145.32 on the committed log (D155) — and spends real
  money, so it needs the owner's agreement, including that figure.
- **Do not tag `rubric-frozen-v1`, and do not build phase 5.** The freeze is the owner's act and
  follows this audit's remediation; held-out labels do not exist until after it.
- Show every commit message before committing, and commit only after approval. Never commit a
  populated `.env` or anything under `private/`. **Do not push unless asked**, and before any push
  compare the remote's owner with `gh api user`.
- **Two repositories.** `comparative-judgment` sits beside this one. The interface scanner compares
  the two specifications and CI runs it from either side, so the two are pushed together.
- Worded numbers are live claims read by count guards; digits are historical statements. US spelling
  is enforced by test. A stated measurement in `tests/` or `tools/` prose must be dated or bound.
- `sessions/` holds what a session wrote for the next; the root holds what a mechanism reads by name.

## One thing worth knowing before you start

Three times in this project an audit instrument was itself the defect — a patch tool that reported
success while applying nothing, a gate that could not see the code it was testing, and a gate whose
verdict depended on machine speed. This span added a fourth: a control gate that read a skipped test
as a pass (D143). Each looked like a finding about the tree.

**Before you trust a null result, prove your instrument can produce a positive one.** A clean scan from
something that is not connected is indistinguishable from a clean tree.
