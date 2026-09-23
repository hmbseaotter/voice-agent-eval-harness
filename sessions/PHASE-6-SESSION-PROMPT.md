# Session prompt — open phase 6, and build what spends nothing

> **SPENT — 2026-09-20.** The session ran and phase 6 opened; its record is
> `sessions/HANDOVER-2026-09-20-phase-6-opening.md`. **Do not paste this to start a new
> session**: it tells a reader to start from a commit that does not resolve in the
> published snapshot's log, and to open a phase that is open already and half built — 6 of
> its 12 criteria ticked, the rest declared in `tools/verify_phase6.py`.

*Paste the section below as the first message of a fresh session in the harness repository. Run it
on **Claude Fable 5.1** at effort **xhigh**, which the reveal handover records as the owner's choice
for this phase.*

*Why Fable rather than the model that built phase 5: most of this phase is open-ended design rather
than building against a written contract. A second adapter has to be shaped like a real platform's
call object, an inspector's invariants have to be invented before they can be asserted, and
per-instance severity has to be decomposed into boolean properties nobody has enumerated. Phases 1
to 5 built against clauses that already existed; this one writes the clauses first.*

*Why xhigh rather than max: nothing in this session's scope spends money — the two deliverables that
need a live call are explicitly left to a session briefed for them. What xhigh buys is the reading,
which is where this phase's expensive mistakes are made: a criterion written against the wrong half
of a requirement is a mistake every later session inherits.*

*State to start from: a clean checkout of `main` at `76c2022` or later, level with `origin/main`,
with CI green. No other session should touch the harness tree while this one runs a chain.*

---

You are opening **phase 6** of the voice-agent evaluation harness: reading its contract, settling
what that reading finds, and then building the deliverables that need no model call. Phase 5 closed
on 2026-09-20, which fired OB-47's trigger — this session is what that row owes.

## Read this first

- **`sessions/PHASE-6-CONTRACT-READING.md`** — phase 6's contract gathered into one document: its
  four requirements, four acceptance criteria and six scope bullets quoted whole, then each
  requirement beside the criteria that claim to cover it, then the deliverables against both. It was
  assembled for this session and carries no decisions; the verdicts are yours to write and the gaps
  it names are ones you may overturn.
- **The clauses in place**, in `specs/voice-agent-eval-harness.md`: the `[P6]` scope bullets, the
  requirements, the criteria, and phase 6's row under `implementation phases`.
- **What a reading produces**, from the three that came before: D104 (phase 2), D130 (phase 4) and
  D157 (phase 5). Each found requirements covered in one half, or a deliverable with no criterion at
  all, and each recorded what it decided rather than quietly adding clauses.
- **`specs/event-model.md` §4 and §5** before writing any adapter: §4 is the per-element mapping to
  Retell, Vapi and Amazon Connect, and §5 is the three things an adapter owes — ordering, vocabulary
  mapping, and honest gaps, with a field the source cannot supply recorded as unavailable rather
  than defaulted.
- **`sessions/HANDOVER-2026-09-18-held-out-reveal.md`**, now closed, for what phase 5 left; and in
  `OBLIGATIONS.md`, rows **OB-16**, **OB-47**, **OB-49**, **OB-7** and **OB-50**.

## Step 1 — the contract reading, before anything is built

Read the four requirements against the four criteria in both directions, and write a verdict for
each pair: covered, covered in part, or not covered, and what a covering criterion would have to
fail on. The gathered document has a page per pair for exactly this.

**Settle these before writing any criterion**, because a criterion written first inherits them:

- **OB-49 — whether a finding may be traced to entries of both tiers.** Judge-model comparison is
  measured as agreement against the gold set, and that set's traces stay inside one tier: 64
  deterministic-to-assert, 19 judged-to-judge, none across. Under that convention a judge catching
  an assert-type finding scores a false alarm, so every agreement figure phase 6 reports inherits
  the answer. The register makes this due at this reading.
- **OB-7 — what closes `JUDGED_AGREEMENT_PENDING`**, now that held-out agreement is measured and
  never committed (D175).
- **P5-9's single difference**, recorded in OB-49's row: the family tables and agreement's expected
  calls disagree on one entry-call pair, by that same convention inside one tier.

**What the reading then lands:**

1. A decision per gap — add a criterion, add a requirement, or record why the deliverable carries
   neither. Each is a fork and each is the owner's.
2. A `COVERAGE` entry for phase 6 in `tests/test_contract_coverage.py`, mapping each requirement
   anchor to the criterion anchors that cover it, with phase 6 removed from `UNMAPPED_PHASES`.
   That is what closes **OB-16** for this phase.
3. `MEASURED_CONTRACT` in `tests/test_document_counts.py` updated if the reading adds a requirement
   or a criterion; it pins phase 6 at four and four today.
4. Whether a phase-6 verifier is written now under `tools/`, named as its five siblings are and
   declaring what is not yet built, as D176 had phase 5's verifier run while its phase was
   open — or at the phase's end, as phases 1 to 4 did. That is a fork; put it to the owner
   with your recommendation.

## Step 2 — build what spends nothing, in this order

**1. The second adapter (R1, S1), which is the phase's *Done when*.** A function from a source
document to a `Call`, beside `harness.corpus.text_adapter`, shaped like a real platform's call
object — Retell, Vapi or Amazon Connect — chosen from that platform's public documentation. The
requirement is that its event stream is **byte-identical** to the text adapter's for the same call,
so the corpus needs a source document per call in the chosen shape, authored from the design
transcripts. Three things to hold to: the sample data is invented, as the corpus is, and no real
vendor log or customer data enters this tree; a field the source cannot supply is recorded as
unavailable rather than defaulted (§5); and the byte-identical claim is asserted by a test over
every design call, not over one.

**2. The deterministic log inspector (R4, C1, S3).** Invariants over a completed run log, emitting
metrics rather than scores — the distinction is the deliverable, so a metric that reads like a score
is the thing to catch in review. C1 names one metric: the proportion of retry triggers whose cited
identifier exists. The others are yours to propose, each with what it would mean if it moved.

**3. Per-instance severity (S4).** Computed in code from decomposed boolean properties rather than
scored on a scale by a model — the counterpart to the comparative-judgment tool's ranked severity,
and a deliverable with **no requirement and no criterion** until the reading gives it one. Expect to
write the properties down before writing the code: which booleans, read from what, and why their
combination is a severity rather than a label.

**4. Docs routing (C3), and the design document (S2).** C3 asks that the README state which license
covers which tree and link the severity tool; read the README's table against that criterion before
assuming either half is owed — the table exists and gained two rows on 2026-09-20. The design
document is phase 6's at D200: written **from the decision records**, carrying the runtime
guardrail's shared rule and recommended implementation, the three deployment cadences and the
four-stage gate ladder as recommendations for a system under test, and the audio-layer follow-up
question. It is prose and spends nothing; its scale makes it the one deliverable worth asking the
owner how to sequence.

## What this session does not do

- **No live model call.** Prompt caching (R2, C4) and judge-model comparison (R3, C2, S6) both need
  one, and both are left to a session briefed for them. If anything you build would issue a call,
  stop. Should the owner decide to bring that work forward, the rule is D152's and D161's: print
  what a pass is expected to cost beside the most it can cost, and stop for approval before the
  first call.
- **No rubric work.** `rubric.yaml` and `prompts/judge-dimension.v1.md` are frozen at
  `rubric-frozen-v1` and pinned there by test. A rubric change is the version-2 cycle D191 weighed
  and deferred to phase 7.
- **No held-out content in this tree**, and nothing from the held-out repository is needed here. The
  absence check runs on every push and reads six shapes (D195).
- **Phase 7 is not yours.** D191 widened it and OB-48 carries it.
- **Never tag.**

## How this repository is worked

- **The owner decides every fork**, through a selectable question with your recommendation first.
  End every substantive turn with an **Assumptions** list.
- **Every new check gets a control**: an entry in `control-mutations.yaml` naming a module-level
  test, a `find` line present exactly once in its file, a row in `CONTROL-REGISTER.md`, and the
  count tag moved. The gate runs in a copy of the tree with no `.git`, and every mutation shares one
  copy, so a test that writes a file removes it again. Drive each new control red before trusting
  it.
- **The document chain moves together** when a decision lands: the specification's version and its
  changelog entry, the decision record's `Not checked` marker and its refresh sentence, the
  `Document status` paragraph and the numbering line. `Last swept` is **not** part of that chain any
  more: since D194 it moves only to a version whose changelog entry is marked `**Swept:**`, and the
  next sweep is due at this phase's close.
- **Commits:** show each message verbatim and ask; stage files by name; no attribution lines; fetch
  before committing; verify the stored message with `git cat-file commit HEAD | sed '1,/^$/d'`
  compared by `cmp` against the file you committed with. **Do not push unless asked**; before any
  push compare the remote's owner with `gh api user`, watch CI after it, and keep CI runs
  sequential. A push whose every commit is documentation prose may carry `[skip ci]` under the rule
  the README's CI section states, with the fast document checks run first; anything touching code,
  tests, tooling, config, CI or project data runs CI.
- Write files with LF endings, and write any script that carries escapes with a file-writing tool
  rather than a shell heredoc. US spelling is enforced by test. Worded numbers are live claims read
  by count guards; digits are historical statements.
- `sessions/` holds what a session wrote for the next; the root holds what a mechanism reads by name.

## Definition of done for this session

- Phase 6's contract is read, its gaps decided with the owner, and `COVERAGE` carries phase 6 with
  `UNMAPPED_PHASES` no longer naming it — OB-16 closed for this phase.
- The deliverables above are built, each with tests and controls, and each named in the contract by
  a requirement or a criterion or recorded as deliberately carrying neither.
- The full chain is green:

```bash
uv run ruff check . && uv run ruff format --check . && uv run mypy
uv run python -m harness.extract
uv run pytest -q --junit-xml=build/phase1-junit.xml
uv run python tools/verify_phase1.py --junit build/phase1-junit.xml
uv run python -m tools.verify_phase2 --junit build/phase1-junit.xml
uv run python -m tools.verify_phase3 --junit build/phase1-junit.xml
uv run python -m tools.verify_phase4 --junit build/phase1-junit.xml
uv run python -m tools.verify_phase5 --junit build/phase1-junit.xml
uv run harness report --out build/report.ci.md && diff -u snapshots/report.md build/report.ci.md
uv run python -m harness.findings_view --check
uv run python tools/check_spec_interface.py specs/voice-agent-eval-harness.md,specs/voice-agent-eval-harness.decisions.md,specs/voice-agent-eval-harness.build-prompt.md ../comparative-judgment/specs/comparative-judgment.md,../comparative-judgment/specs/comparative-judgment.decisions.md
uv run python tools/statement_inventory.py
uv run python tools/check_holdout_absence.py
PYTHONUNBUFFERED=1 uv run python tools/verify_controls.py
```

The suite takes 10 to 14 minutes and the control gate 45 to 60 over 325 entries. A phase verifier
given `--junit` re-runs the suite whenever a file in the tree is newer than that report, so a
fourteen-minute verifier run is that and not a hang.

- A handover in `sessions/`, in the shape the others there use, with a *What is owed* section whose
  items the obligations harvest turns into rows.

## One thing worth knowing before you start

The second adapter was retargeted once already. It began as a JSONL adapter of this project's own
invention, and that was refused because it would have proven nothing: the claim under test is that
an engineer can point this harness at **their vendor's** logs, and a format this project designed
cannot test it. The same trap is one step further in — an adapter written against a platform's
schema as you imagine it, rather than as its documentation states it, proves the same nothing more
convincingly.

Read §4's mapping table before you write the source documents, and say in the handover which
platform's documentation you read and when.
