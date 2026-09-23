# Handover — the register is audited end to end, and CI re-derives it

**Status:** open. Opened 2026-09-08 and carried through 2026-09-09, from `c21c1ba` to `3ce378e`.
Answers `sessions/HANDOVER-2026-09-08-control-connectivity.md`, which is closed. `main` is pushed and
CI is green.

**Who this is for.** A session that has read no held-out transcript. Everything below reads `tests/`,
`src/`, `tools/` and the root documents.

---

## What was done

`CONTROL-REGISTER.md` is in the repository root, one row per control, each with a verdict and the
evidence behind it. `test_every_control_is_registered` reads it by name — a test matching the control
naming idiom that the register does not name turns the suite red — and
`test_every_registered_control_exists` holds the other direction. That is what earns the root
placement under D120, and it turns "roughly thirty" into a list a later pass can audit against.

The audit is D121. Run the gates first, so a failure later is yours:

```bash
uv run pytest -q && uv run python tools/verify_phase1.py && uv run python -m tools.verify_phase2 && uv run python tools/statement_inventory.py && uv run python tools/verify_controls.py
```

**Two tools, and they are not the same kind of thing.**

- `tools/verify_controls.py` is the **gate**. It re-derives every `connected` verdict by restoring the
  defect each control names into a copy of the tree and requiring the control to fail there. **CI runs
  it on every push**, so a control that comes loose turns the build red rather than waiting for
  someone to remember the command above.
- `tools/screen_controls.py` is **triage**. It finds one shape and is silent about everything else. It
  is deliberately **not** in CI: it exits 1 on a flag it cannot settle, and one of its flags today is
  a known false positive, so as a gate it would be red forever and teach a reader to ignore it.

## What the audit found

Each of the 9 phase-2 remediation commits touching `src/` was reverse-applied into a copied `src/` and
the suite run against it. That put 12 rows at `connected` by demonstration. One commit is noticed by
nothing and correctly so — `7072cf4` changes only a raw docstring and an exit-code comment.

**Seven controls were measuring nothing**, all repaired. Six are one shape: **a control that
re-implements the rule beside the check instead of calling it.** The control-character sweep's control
recomputed the detection expression on a literal of its own and was blind to the extension filter it
claimed to guard. The anchor control never moved an event. The leak-scan control was a tautology
(`x in y + x`) that never called the scan — and the seam it claimed to guard turned out to be covered
by two unrelated neighbors, a guard green and blind while the protection came from somewhere nobody
had written down. The `matched_by` control ran its own extraction and its own comparison. The
escalation control parsed a planted transcript and compared the fields itself. And one of the six was
**this audit's own guard**, `test_the_mutation_spec_would_notice_an_anchor_that_moved`, written while
documenting the shape and caught by the screen rather than by its author — which is the argument that
the shape is not inattention but what writing a control beside a check naturally produces.

**The seventh is a different mode.**
`test_adding_the_supporting_sentence_to_speech_alone_does_not_move_the_verdict` was **masked**: it
asserted the verdict alone, and CALL-02 violates on two clauses, so the verdict cannot move even when
one is wrongly resolved. With the defect restored the verdict held and the evidence quietly lost a
finding. It asserts the evidence now.

**Three rows were not controls at all**, and were worse than that. The
`test_every_traced_finding_is_on_a_call_the_entry_fires_on` pair and the `assert_detectable` variant
are consistency assertions between declarations; `connected` is not a question that can be asked of
them. The question that can be — does it compare anything? — answered badly: all three passed over an
empty table while their neighbors in the same files carried floors. Each counts and floors now.

**The screen is the transferable part, and it ships.** The signal: the check accumulates its verdict
in a loop whose feeding calls the control never makes. Calibrated against `c21c1ba` — pass it that
tree's `tests/` — where it flags the three then-known-defective controls plus one false positive.
**Read its silence correctly:** over the register it raised two rows, one true finding and one
mis-pairing, and every other row came back *silent, not clear*. A control can be disconnected with no
loop to inspect. Screening is triage; restoring the defect is the audit.

## Three times the instrument was the defect

This is the part worth carrying forward. Each of these looked like a finding about the tree and was a
finding about the tool.

1. **`git apply -R` exits 0 while skipping every hunk** when it resolves paths against a different
   repository than the patch came from — and the scratch directory sits inside one. The first sweep
   mutated nothing and would have reported that no control notices any defect. Use `patch`, and
   require the copy to differ before running anything.

2. **The gate could not see `src/` at all.** `harness` is an editable install: a `.pth` appends the
   real tree's `src` to `sys.path`, so a copied tree imported the ORIGINAL modules. A bare `raise`
   planted in the copy changed nothing. It sets `PYTHONPATH` to the copy's `src` now. Every
   `src/`-side verdict would otherwise have been reported as a finding against the control, from a
   mutation that never ran.

3. **The gate's verdict depended on how fast the machine was.** Its first CI run reported two
   connected controls as measuring nothing, and they were exactly the two entries whose replacement is
   the **same number of bytes** as the line it replaces. CPython validates a cached `.pyc` on the
   source's size and its mtime in whole seconds; the unmutated run writes that cache and the mutated
   run reuses it when the edit preserves the size and both land inside one second. CI is fast enough
   that it did; this machine is slower per entry, so the same mutations were seen here. It sets
   `PYTHONDONTWRITEBYTECODE` and no longer copies `__pycache__` into the tree it mutates, and
   `tests/test_verify_controls.py` plants that exact shape and requires it to be seen.

**All three failed closed** — a masked or missing mutation makes a control look *disconnected*, never
connected, so the error is loud rather than silent. That direction was luck rather than design in at
least the third case, and the next instrument may not have it.

**So: if the gate reports a control green with its defect restored, suspect the mutation before the
control.** Four times it printed a `[FAIL]` that was not one — three mutations aimed at code the
control does not reach, and one masked by a cache. Check the entry's `defect:` line against what the
control actually plants before believing it.

## Phase 3 starts next, and the owner has settled how

The sweep and version bump that the previous handover put ahead of phase 3 are **done** --
`c1f2ae6`, and the spec header reads `Last swept: 2026-09-08 @ 0.26.0 @ D119`. Only D120 and D121
have accrued since, against a trigger of ~8-10, so no sweep is due. **Phase 3 is the next milestone**
and its contract is the specification's `[P3]` requirements: the model transport seam with live and
replay implementations, one judged dimension end to end, the run log, the citation universe and its
informed retry, and the `refused` / `errored` / `max_tokens` distinctions.

Three things the owner decided on 2026-09-09, so the next session does not have to ask again:

- **Start it in a fresh session.** Not for context hygiene but for clearance: phase 3 authors a judged
  rubric entry, and rubric work requires a session that has read no held-out content. A new session is
  provably clean; an inherited one is only arguably clean.
- **Claude Opus 5, effort `xhigh`.** `xhigh` is the setting the API reference calls best for coding and
  long-horizon agentic work **when the full task spec is given up front**, which `[P3]` is. Opus 5
  rather than Fable 5.1 because this is implementation against a precise written contract rather than
  open-ended reasoning, at half the per-token rate. Raise to `max` for the seam's replay and staleness
  semantics and the retry/`errored` boundary if those prove to be where the difficulty actually is.
- **The `anthropic` SDK is approved**, pinned with `==` like the other two runtime dependencies, on one
  condition: **build the replay implementation before any live call**, so the tier runs key-free and
  spends nothing until live calls are deliberately enabled. `pyproject.toml` already anticipates the
  dependency; D8 settled key-free running, and the live-call ceiling moved to P3 at D23-D29. Record the
  dependency decision in the decision record when it lands, at whatever number is next.

## What is owed, in the order I would take it

Every row in **both** register tables has had its defect restored; none is `unaudited`. What is left
is outside them.

1. **Completeness of the `Outside the idiom` table.** Its rows are all audited — seven connected, one
   masked and repaired — but the table is hand-maintained, found by looking for the shape of a control
   rather than by a rule. A control named outside the idiom and never noticed is invisible to both
   tables. Widening the rule would also catch ordinary negative-input tests, so the line is judgment:
   does the mutation restore a defect that was once real?

2. **Checks with no control at all.** This register audits controls, so a check nobody planted one for
   is invisible to it. The three floorless consistency assertions are the warning: green over an empty
   table, and nothing said so. Sweeping for checks whose comparison is *inline* would find the
   population that **cannot** have a connected control — there is nothing for one to call.

3. **Two reverts that could not be scored per-control.** `d033efd` removes `state_writes` and
   `1dbd22c` removes `DuplicateCallError`, so collection aborts. A surgical revert — the behavior hunk
   only, keeping the symbol — would give real per-control verdicts for the ordering and engine
   families.

4. **Rows resting on a broad revert.** `27bc78d` breaks 103 tests and `d024a43` breaks 196. Those rows
   are `connected` honestly but weakly; a single-hunk revert would sharpen them.

5. **One mutation per control proves one defect.** Each row shows its control catches *that* defect,
   not every defect of its check. Mutation testing over the checks is the general form; the gate is
   the curated, cheap version of it.

## Constraints that do not lift

- **Never open, glob, grep, cat or diff a transcript in `voice-agent-eval-harness-holdout`**, and do
  not read that repository's commit messages or test docstrings. Counts, rules, call identifiers and
  file names are safe; content is not. If unsure, stop and ask.
- **Do not build phase 3** — no transport seam, no model calls, no judged dimensions.
- No new packages without flagging for approval first.
- Show every commit message before committing. Never commit a populated `.env` or anything under
  `private/`.
- Worded numbers are live claims and are read by count guards; digits are historical statements. When
  a count would need maintaining, de-quantify it (D74) rather than adding a checker.
- A stated measurement in `tests/` or `tools/` prose must be dated or bound, and declared in
  `_STATED_MEASUREMENTS`. This session tripped that check three times writing up its own findings,
  which is the check working.
- US spelling, and this session tripped that check twice as well.
- `sessions/` holds what a session wrote for the next; the root holds what a mechanism reads by name
  (D120). `CONTROL-REGISTER.md` is in the root because a test reads it — if you ever delete that test,
  the register belongs here instead.
