# Session prompt — sweep the specification, for phase 5's close

> **SPENT — 2026-09-19.** The sweep ran; its report is
> `sessions/SWEEP-2026-09-19-phase-5.md`, and its findings were applied the next day.
> Kept because its *method* is the reusable part; the tree it describes has moved.

*Paste the section below as the first message of a fresh session in the harness repository. Run it
on **Claude Fable 5.1** at effort **xhigh**.*

*Why a different model: the six decisions this sweep must read hardest, D193 to D198, were written
on Claude Opus 5 in the session that would otherwise sweep them, and re-reading one's own prose for
staleness is the blind spot every audit here has used a different model to avoid. xhigh rather than
max because nothing in a sweep spends money and the work is bounded — one document read against a
tree, with part of it already held by tests.*

*State to start from: a clean checkout of `main` at `aa3d211` or later, with CI green.*

---

You are sweeping the specification of the voice-agent evaluation harness, so that phase 5 can close.

## What a sweep is here, and why this one is owed

Moving the header's `Last swept` marker **claims the specification was read against the tree** (D71).
Until 2026-09-19 nothing held that claim: the marker moved with every decision from D168 to D193,
22 values in 22 commits, because a test bound its version to the spec's. The phase-5 audit found it
(P5-7), and D194 changed the rule — the marker now names the version a sweep was recorded at, and
from 0.55.0 it may move only to a version whose changelog entry is marked `**Swept:**` and says what
the sweep read.

So this is the first sweep under that rule, and D129's test makes it a precondition for closing
phase 5: a handover marked `closed` requires the marker to have reached the last decision it records.

**You report; you do not edit the specification.** The session that worked the audit remediation
applies your findings, writes the sweep's changelog entry naming this report, moves the marker and
closes the phase. Say so in your report if you think a finding is not worth acting on.

## What to read

**The specification, `specs/voice-agent-eval-harness.md`, 452 lines**, every section except the
changelog:

`metadata`, `outcome`, `in scope`, `out of scope (v1)`, `control surface`, `triggers & scheduling`,
`tools & permissions`, `state & memory`, `model & cost routing + determinism boundary`,
`constraints`, `prior decisions`, `requirements`, `failure & escalation`, `acceptance criteria`,
`implementation phases`, `assumptions`, `decisions made`, `emitted artifacts`.

The `changelog` is historical: an entry describes what a version did and does not go stale. Read the
newest entries only for whether they describe what landed — 0.55.0 to 0.59.0 are from 2026-09-19.

**Beside it**, because the spec points at them and a sweep follows the pointer: the `Not checked`
block at the end of `specs/voice-agent-eval-harness.decisions.md`; `README.md`; `OBLIGATIONS.md`;
`HOLDOUT-OBLIGATIONS.md`; and `sessions/HANDOVER-2026-09-18-held-out-reveal.md`, which is the
document phase 5's close marks.

## What a live statement is

A statement that describes the project **now**: a count, a file that exists, a command that behaves
a certain way, a state that holds ("not yet flipped", "stays open", "waits for"), a cross-repository
claim. Each is checkable against the tree, and each is what a sweep exists to catch.

Not live: a sentence about what a decision reasoned at the time, an entry in the changelog, a
historical note. Those are records, and this project does not edit records (D53).

## What is already held by a test, so you need not re-derive it

Read these first and then look past them — a sweep that only re-runs the mechanized half finds
nothing.

- `tests/test_document_counts.py` holds the requirement and criterion counts per phase against
  `MEASURED_CONTRACT`, the spec version against the decision record's `Not checked` marker and the
  newest changelog entry, the design-set size and event totals wherever a document states them, the
  tagged quantities in the registers, and US spelling.
- `tools/statement_inventory.py` resolves every identifier named in prose — files, tests, tools,
  rubric entries, findings — and reports the ones that do not exist.
- `tests/test_contract_coverage.py` holds that each phase's criteria cover its requirements, for the
  phases mapped in `COVERAGE`.
- `tools/check_spec_interface.py` compares the findings keys, severity fields and row fields this
  specification states with the ones `comparative-judgment`'s specification states.

Run the fast document checks once before you start, so a failure you find later is not inherited:

```bash
uv run pytest -q tests/test_document_counts.py tests/test_contract_coverage.py tests/test_obligations.py tests/test_phase3_acceptance.py tests/test_findings_evidence.py
uv run python tools/statement_inventory.py
uv run python tools/check_holdout_absence.py
uv run python -m tools.verify_phase5 --junit build/phase1-junit.xml
```

The phase-5 verifier needs a junit file; produce one with `uv run pytest -q
--junit-xml=build/phase1-junit.xml` (about 14 minutes), or run the verifier without `--junit`, which
re-runs the suite itself.

## Where to look hardest

Ordered by what this project's history says goes stale first.

**1. The five versions written on 2026-09-19, 0.55.0 to 0.59.0.** They are the phase-5 audit's
remediation: D194 (the sweep marker), D195 (what the absence check reads), D196 (extraction and the
findings view refusing to write held-out content), D197 (the rubric hash on the scoring commands) and
D198 (the register's result vocabulary). Check each entry, each decision's `Rule` line, and each
requirement or criterion they added, against the code and tests as they now stand. This is the half
the session that wrote them cannot read independently, which is why you are on a different model.

**2. Status claims.** `Status: DRAFT`, `Visibility: not yet flipped`, `Produced by: /specify @
f72b756`, the `Reproducibility` and `Integrity` lines, and every sentence in `prior decisions` and
`assumptions` that says something is pending, open, not yet built, or waiting. Phase 5's held-out
numbers were computed on 2026-09-18 and are never committed; the phase-5 audit's P5-8 found one
caveat still saying they wait for the reveal, and that class of sentence is what it belongs to.

**3. Counts and enumerations the tests do not hold.** The contract's own numbers are held; the
prose around them is not — how many rubric entries, how many controls, how many design findings,
how many verifiers, what the CI workflow runs, what each phase's deliverables are.

**4. The phase table and the phases not yet built.** `implementation phases` describes 6 and 7;
D191 widened phase 7 and the scope bullet says so. Check that the table, the scope bullets and the
decisions agree about what each phase now contains, and that phase 5's own row describes what was
actually built.

**5. Cross-repository claims.** What the specification says `comparative-judgment` emits and what
the held-out repository asserts. The interface scanner holds the field lists; the prose around them
is not held by anything. **Do not open the held-out repository.** Nothing here needs it: its labels
are public but no statement in this specification turns on their content, and a sweep that reads
them puts the reader under rules this task does not need.

**6. The `Not checked` block.** It carries a refresh sentence per version since 0.29.0 and a rule
that an entry describing a state the project has left must be moved rather than left standing. Read
its entries against today, not against their refresh sentences.

## What to produce

A report in `sessions/`, named `SWEEP-<date>-phase-5.md`, following the shape the audit reports
there use: a status banner at the top, then the baseline you reproduced, then findings.

Each finding carries an id (`S-1`, …), what the statement says, where it is (`file:line`), what is
true instead, how you checked, and the wording you propose. Mark each `(reproduced)` or `(by
reading)`. Severity is simpler than an audit's:

- **Wrong** — the statement is false today.
- **Stale** — true when written, describing a state the project has left.
- **Unbacked** — the statement may be true and nothing in the tree can tell; say what would settle it.

Close with two sections: **what you read and what you did not**, explicitly, since a sweep's claim
is coverage; and **what the sweep's changelog entry should say it read**, in a sentence or two, for
the session that writes it.

## Rules

- **Report, do not edit.** The specification, the decision record and the registers are not yours to
  change in this session. Your report is the one file you add.
- **Reproduce before you report.** Of the phase-2 audit's 17 findings 3 did not hold; of the
  2026-08-29 audit's 44, 3 did not. Every checkable claim carries the command and what it printed.
- **Never spend.** Nothing here needs a model call; if anything would issue one, stop.
- **Never tag, and touch no other repository.**
- **The owner decides every fork**, through a selectable question with your recommendation first.
  End every substantive turn with an **Assumptions** list.
- **Commits:** show the message verbatim and ask; stage files by name; no attribution lines. **Do
  not push unless asked.** Your report is prose in `sessions/`, so its push may carry `[skip ci]`
  under the rule the README's CI section states — run the fast document checks over it first.
- Write files with LF endings. US spelling is enforced by test. Worded numbers are live claims read
  by count guards; digits are historical statements.

## One thing worth knowing before you start

The last sweep that was actually performed, at 0.21.0, found **nine live statements still calling
the design set twelve calls**, a substitution-class count corrected twice in prose and still wrong,
an assumption discharge stale in the direction that flattered it, and a version marker reading a
number this project had never been at — which had survived a full suite, a phase-1 verifier run and
an independent audit, because nothing read it.

That is the yield a sweep is for. The mechanized half will be green when you start.
