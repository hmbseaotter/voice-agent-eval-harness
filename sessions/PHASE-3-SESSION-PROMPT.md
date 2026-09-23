# Session prompt — build phase 3, the judged tier

> **SPENT — 2026-09-09.** Phase 3 was built and closed; the session's own record is
> `sessions/HANDOVER-2026-09-09-phase-3.md`. Kept as the record of what the phase was
> asked for, not as a brief to paste.

*Paste the section below as the first message of a fresh session. Run it on **Claude Opus 5** at
effort **xhigh** — the owner settled that on 2026-09-09, and the reasoning is in
`sessions/HANDOVER-2026-09-08-control-register.md`.*

*Why a fresh session rather than a continuation: phase 3 authors a judged rubric entry, and rubric
work requires a session that has read no held-out content. A new session is provably clean; an
inherited one is only arguably clean.*

---

You are building **phase 3** of the voice-agent evaluation harness: the judged tier.

## Read this part first, because it is the only thing here that cannot be undone

**Never read held-out content, anywhere it lives.** Do not open, glob, grep, `cat` or diff any
transcript in `voice-agent-eval-harness-holdout`, and do not read that repository's commit messages
or its test docstrings. Do not open `holdout-authoring-packet/`, nor
the two withheld source folders outside both repositories, which hold the material the corpus was written clean of.

**The line is content versus existence.** Counts, rules, call identifiers and file names are safe —
`HELDOUT_SET` in the repository root is exactly that, and reading it is expected. A transcript is
not, and neither is a sentence *about* what one contains.

**Why it cannot be undone.** A session that reads held-out content can no longer design, tune or
review the rubric, because it then knows what the rubric will be scored against — and phase 3 authors
a judged rubric entry. The content lands in this session's transcript outside the repository, where
`tools/check_holdout_absence.py` cannot look. A green absence scan means no copy is in the tree, not
that no session has read one.

**If you are unsure which side of the line something falls on, stop and ask** rather than opening it.

## Start here

1. Read `sessions/HANDOVER-2026-09-08-control-register.md` — it carries the state, the conventions,
   and what the previous session left owed.
2. Run the gates before changing anything, so a failure later is yours:

```bash
uv run pytest -q && uv run python tools/verify_phase1.py && uv run python -m tools.verify_phase2 && uv run python tools/statement_inventory.py && uv run python tools/verify_controls.py
```

Expect 826 passing, 21 of 21 `[P1]`, 24 of 24 `[P2]`, the inventory clean, and 29 of 29 controls
driven red by their own defect. `main` is pushed and CI is green.

## What phase 3 is

**The contract is the specification's `[P3]` requirements and acceptance criteria** in
`specs/voice-agent-eval-harness.md` — not a build prompt. Phase 1's build prompt was superseded at
the end of that phase; phase 2's contract was its `[P2]` requirements, and phase 3's is the same
shape. Two deliverables:

- **A model transport seam** with live and replay implementations, unconditional run-log recording,
  and staleness refusal.
- **One judged dimension end to end** — prompt, declared JSON schema, tagged citation universe,
  set-membership validation, informed retry, `errored` on exhaustion.

The `[P3]` markers also cover the run log's contents, credential exclusion from every log and error
message, and the retry/exhaustion behavior. Read them all before designing; several are stated as
SHALL clauses with testable criteria attached.

`rubric.yaml` declares no `tier: judge` entry today, and a comment at the top says so deliberately.
That is what makes "the deterministic tier issues zero model calls" trivially true right now —
revisit that claim when a judged entry exists for real.

## Decisions you inherit, so you need not re-ask

- **The `anthropic` SDK is approved** as a new dependency. Pin it with `==`, as the two existing
  runtime dependencies are — this project states its pins rather than declaring floors and calling
  them pins.
- **Build the replay implementation before any live call.** The condition on that approval is that
  the tier runs key-free and spends nothing until live calls are deliberately enabled. D8 settled
  key-free running; the live-call ceiling moved into P3 when the pre-build audit re-cut the phases.
- **Record the dependency as a decision** in `specs/voice-agent-eval-harness.decisions.md` at
  whatever number is next, in the house shape: fork, options considered, decision, why, consequences.

## How this project works

These are not stylistic preferences. Each exists because something went wrong without it.

- **Every change carries a control, driven red and restored.** A check whose only evidence is that it
  has never fired has been proven against nothing. Register it in `CONTROL-REGISTER.md` and give it an
  entry in `control-mutations.yaml` so `tools/verify_controls.py` re-derives the verdict — CI runs
  that gate on every push.
- **When a control looks disconnected, suspect the mutation first.** That gate has printed a `[FAIL]`
  that was not a finding 4 times: 3 mutations aimed at code the control does not reach, and 1 masked
  by a stale bytecode cache. Check the entry's `defect:` line against what the control actually plants.
- **Do not write a control that re-implements the rule beside the check.** Give the check a named
  function and make the control call it. 7 controls in this tree were written the other way and every
  one of them was measuring nothing.
- **Worded numbers are live claims** and are read by count guards; **digits are historical
  statements**. When a count would need maintaining, de-quantify it rather than adding a checker.
- **A stated measurement in `tests/` or `tools/` prose must be dated or bound**, and declared in
  `_STATED_MEASUREMENTS`. Writing up your own findings will trip this; that is the check working.
- **US spelling**, enforced by test.
- **Show every commit message before committing**, and commit only after approval. Stage selectively.
  Never commit a populated `.env` or anything under `private/`. **Do not push unless asked.**
- **`sessions/` holds what a session wrote for the next; the root holds what a mechanism reads by
  name.** Put your handover in `sessions/`.

## Scope

Phase 3 is the two deliverables above and the `[P3]` clauses that support them. **Do not build P4 or
P5** — the remaining judged dimensions, the synthesis dimension, report generation, snapshot tests,
held-out labels and judge validation are later phases with their own contracts.

Spending starts in this phase. Before the first live call, say what it will cost and get agreement.
