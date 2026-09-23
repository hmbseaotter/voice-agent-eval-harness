# Session prompt — audit phase 5, and the obligations closed since the freeze

> **SPENT — 2026-09-19.** The audit ran; its report is
> `sessions/AUDIT-2026-09-19-phase-5.md`, whose banner records all 16 findings closed.
> Kept as a record, not as a brief to paste.

*Paste the section below as the first message of a fresh session in the harness repository. Run it
on **Claude Fable 5.1** at effort **max**.*

*Why a different model from the builder: phase 5 and the obligations closed after the freeze were
built on Claude Opus 5, the coverage report among them (recorded in
`sessions/PHASE-5-COVERAGE-SESSION-PROMPT.md`). A fresh session supplies most of the independence — no
memory of why a choice seemed fine, no commitment to defend — but a model auditing its own output
shares the blind spots that produced it. The phase-3 and phase-4 audits took a different model for
that reason. `max` because an audit's failure mode is missing something, which is what reasoning depth
buys, and because this audit is what stands between phase 5 and its close (OB-46).*

*Expect long turns at this effort. That is the setting working, not a hang.*

*State to start from: a clean checkout of `main` at `c5ad3ce` or later, with CI green. Another session
may be working on `comparative-judgment` beside this repository and pushing there; check `git status`
before any command that acts on the whole tree, and leave anything you did not write untouched.*

---

You are auditing **phase 5** of the voice-agent evaluation harness, and the obligations closed after
the `rubric-frozen-v1` tag. You did not build any of it. That is the point of you.

## Read this part first: what you may read, and what may never enter this tree

**The held-out labels are public.** The held-out label chain completed on 2026-09-18 (C1, C2 and C3,
each with the held-out repository's gate green), and the rule against searching the labeling sessions
is retired; see `HOLDOUT-OBLIGATIONS.md`. On the owner's decision you **may** read these six, in place,
in the held-out repository's checkout beside this one, and **nothing else
in that repository** — not its specifications, tools, tests, sessions, commit history or other runs:

- `labels/findings.yaml`, `labels/traces.yaml` and `labels/severity.json`;
- `transcripts/`, `CORPUS_VERSION`, and the run log under `runs/` whose name starts `heldout-`.

Open nothing outside both repositories either: no authoring packet or practice folder, no other
session's transcript, no memory folder.

**Why you may read them.** `tools/check_holdout_absence.py` recognizes held-out material by its
**shapes** — a transcript's format marker, a run log's records, a rendered report's heading beside a
declared call, a coverage section's heading, an `HF-` finding id. A held-out sentence paraphrased into
a decision, a figure quoted in a commit message or a label restated in a handover has none of those
shapes, and only a reader who has seen the held-out content can look for it. You are that reader.

**What does not end with the reveal:** no held-out transcript text, run log, label, figure, or report
over held-out findings or calls ever enters this repository's tree, a commit, a test fixture or a
message to be committed. **That includes your audit report**, which is committed here. State a finding
about a held-out path in terms of the code and invented data — *the held-out section counts a finding
twice when …* — never in terms of what the held-out set holds or scores. If a finding cannot be stated
without held-out content, give it to the owner in the conversation, and write in the report only that
a finding was given there. When you search this tree for held-out content, report how many strings you
searched for and where, never the strings.

Run a held-out section to **stdout only**, never with `--out` and never redirected into this checkout.

**You author no rubric.** `rubric.yaml` and `prompts/judge-dimension.v1.md` are frozen at the
`rubric-frozen-v1` tag and pinned there by test. A session that has read held-out content does no
rubric work in this project, and an audit does none.

## The rule this project applies to its own audits

**Reproduce before you report.** Of the phase-2 audit's 17 findings, **3 did not hold**; of the
2026-08-29 audit's 44, **3 did not hold**. The phase-3 audit's 23 needed no correction, and every
checkable claim in the phase-4 audit held when it was reproduced independently, with five corrections
to the report recorded in its banner. The difference is reproduction: every finding carries
the command, the input and the observed output that produced it.

A finding you reached by reading alone is still worth reporting — mark it `(by reading)` and say what
you could not run. Never present the two as the same thing. And check what your own recommendations
would do before recommending them: one phase-2 closure, taken literally, cleared a call the entry
exists to fail.

## Baseline first

Reproduce the state before you judge it. A failure you find later is then yours, not inherited.

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
uv run harness agreement
uv run harness coverage
PYTHONUNBUFFERED=1 uv run python tools/verify_controls.py
```

The suite takes 12 to 15 minutes and the control gate 45 to 60, re-deriving every entry in
`control-mutations.yaml` in its own copy of the tree. The phase-2 to phase-5 verifiers are invoked as
**modules**, because each imports machinery from an earlier one. Replay needs no API key; if anything
in the baseline asks for one, that is a finding.

Then the held-out sections, over the six inputs in place and to stdout only:

```bash
H=../voice-agent-eval-harness-holdout   # the held-out checkout, beside this one
uv run harness coverage --held-out-transcripts "$H/transcripts" --held-out-corpus-version-file "$H/CORPUS_VERSION" --held-out-run-log "$H"/runs/heldout-*.jsonl --held-out-findings "$H/labels/findings.yaml" --held-out-traces "$H/labels/traces.yaml" --held-out-severity "$H/labels/severity.json"
```

`harness agreement` takes the same inputs without `--held-out-severity`. Both exit 0 when computed and
2 when refused.

Record what you observed — counts, exit codes, digests — in the report's first section, for the design
set; for the held-out sections record only that each computed or was refused, and the exit code. If a
number in this prompt, a handover or the decision record disagrees with what you measure, **the
measurement wins and the disagreement is a finding.**

## What you are auditing

The span is `6d3a710..c5ad3ce`, from the commit `rubric-frozen-v1` points at to D193: 41 commits,
about 10,500 insertions across 50 files, 2,846 of them in 16 files under `src/` and `tools/`. Two parts:

- **The obligations closed after the freeze**, `6d3a710..dff180c`, 10 commits: OB-24 to OB-33, the
  phase-4 audit's residue carried past the tag — the verifiers CI requires read from one list, the
  report's credential posture pinned, the synthesis truncation carried, deferred triggers read against
  what has happened, a torn run log refused, a resume counting what its log answers, what N measures
  per entry, the expected figure pricing recorded retries, the severity loader refusing a cut the tool
  could not draw, and the design store rewritten to LF. Decisions **D166–D172**.
- **Phase 5 itself**, `dff180c..c5ad3ce`, 31 commits: a held-out run's labels manifest, paths, log
  name and rubric hash (D173, D174, D182–D184, D186); agreement per rubric entry with the sets apart
  (D175); the phase-5 verifier and what it declares (D176); the label chain recorded (D177); a report
  over held-out calls kept out of this tree (D185); question-tier findings named rather than
  `unplaced` (D187); the coverage report by severity, its content-hash recheck and its split by
  detection type (D188, D189, D192); the design store's bands assigned (D190); the deterministic
  tier's reach recorded and phase 7 widened (D191); and the entities register's values (D193). The
  interface scanner (D178), the informed retry (D179) and the verifiers' caveats (D180) landed in the
  same span.

Read first, in this order:

1. `sessions/HANDOVER-2026-09-18-held-out-reveal.md` — phase 5's own account, still `open`; its item 3
   is this audit.
2. `sessions/HANDOVER-2026-09-12-phase-4-audit.md` — what the obligations closed after the freeze
   answered.
3. `sessions/AUDIT-2026-09-15-cross-project.md` and its handover — a session outside both repositories
   read the **seams** between them up to `6a0f144` (D180). It did not audit phase 5 as a whole; do
   not treat its clean items as covering the code behind them.

Each is the builder's account, and therefore both your best map and a document with an interest in
the outcome.

**The contract is the specification's `[P5]` scope bullets, requirements and acceptance criteria** in
`specs/voice-agent-eval-harness.md` — 3, 4 and 13 — and, for each obligation closed in the span, the
`evidence:` its row gives in `OBLIGATIONS.md`. `tools.verify_phase5` ticks 10 criteria and **declares**
3 as asserted by the held-out repository's gate. Audit against the contract, not against the
handovers' description of it; where the two disagree, that is a finding.

The surfaces:

- **`src/harness/coverage.py`** and **`src/harness/agreement.py`** — what fired, what is retired,
  uncovered and missed, per band and per detection type, and how each set's labels are checked.
- **`src/harness/cli.py`** — `coverage_command`, `agreement_command`, the held-out inputs' refusals,
  a held-out run's manifest, paths, log name and rubric hash, and the report's `--out` refusal.
- **`src/harness/core/severity.py`** and **`corpus/findings.severity.json`** — the content-hash
  recheck, the cut and band checks, and the store's assigned bands.
- **`src/harness/core/rubric.py`**, **`src/harness/core/transport.py`**, **`src/harness/judge/`** and
  **`src/harness/report.py`** — what the post-freeze obligations changed in them.
- **`tools/check_holdout_absence.py`** — every shape it reads, and what it cannot.
- **`tools/verify_phase5.py`** and the earlier verifiers, **`tools/verify_controls.py`** and
  **`tools/check_spec_interface.py`** — audit the gates as hard as the code: a tick that does not
  stand for what it claims is this project's most-repeated defect.
- **`corpus/entities.md`** and **`tests/test_corpus_hygiene.py`** — the register and the widened name
  check (D193), which the held-out repository copies part of.
- **`tests/test_contract_coverage.py`**, **`OBLIGATIONS.md`**, **`HOLDOUT-OBLIGATIONS.md`**,
  **`CONTROL-REGISTER.md`** and **`control-mutations.yaml`** — the mechanisms that say what is covered,
  owed and connected.
- Decisions **D166–D193**, and the `Not checked` block, dated `as of 0.54.0 @ D193`.

## Where to look hardest

Ordered by what this project's history says is most likely to be wrong, with the one irreversible
defect first.

**1. Held-out content in this tree.** Three mechanisms guard it: path refusals for a held-out run and
a report (D174, D185); the absence check's shapes (D185, D188); and a rule with no mechanism behind
it — decisions, handovers and commit messages carry no held-out figure, which is why D191 records the
deterministic tier's reach without one. Search the tree, the specification's history and every commit
message in the span for distinctive strings you take from the held-out files, and prove your search
can find one first: plant a string in a copy **outside** the tree and see it reported. Then ask of
each shape the absence check reads what a held-out artifact reformatted by hand, or quoted in part,
would look like to it.

**2. Fail-open paths in the phase-5 commands.** `harness agreement` and `harness coverage` exit 0 when
they compute, and they are measurements, not gates. Ask of every input what it looks like when it
silently computes nothing: a held-out traces file tracing no finding, a severity file banding none, a
run log answering none of the transcripts given, a findings file whose calls the transcripts do not
hold, a set whose every finding is question-tier. And ask whether a refusal can be reached at all —
D189's recheck refuses a band placed on moved text; find the input that shows it firing.

**3. One definition of "fired", or two.** A finding is retired when an entry traced to it fired on its
call, read the way the gate reads it (D188) — for a judged entry, its modal verdict (D158). Agreement
and coverage should read one function for that; check that they do, and that the design and held-out
sections read it the same way.

**4. The verifier's ticks and its declarations.** For each of the 10 criteria `verify_phase5` prints
PASS for, ask what would have to break for it to print FAIL, and whether that is the thing the
criterion claims. For each of the 3 it declares, check that the reason is something this repository
genuinely cannot assert, and name what then rests on the held-out side's report alone — you may not
read that side's gate, so say so rather than inferring it.

**5. Controls that measure nothing.** `control-mutations.yaml` held 120 entries at the freeze and
holds 286. Check the ones added since for the shapes this project has found before: a control skipped
and read as passing (D143), a test reading a committed artifact rather than the code a mutation
changed (D151), and a control that re-implements its rule beside the check instead of calling it.
Check that every new check that needed a control got one.

**6. Second definitions.** D189 moved the content hash into one harness function the suite and the
coverage report both read; D186 hashes the rubric a held-out run judged under; the interface scanner
compares two specifications' field lists (D178); and the held-out repository copies two helpers of the
name check here. Check that each comparison runs over what it claims to, and look for a second
definition that nothing compares.

**7. Prose that was true when written.** None of the document guards reads prose for truth. Sample the
live claims in the README, the specification, D166–D193, the registers, the docstrings and the three
handovers, check them against the tree, and report what you sampled and what you did not.

**8. Mechanisms versus memory.** Name what is enforced and what rests on a session remembering: the
rule that held-out figures stay out of prose; the `[skip ci]` rule this repository adopted in the span
(six commits since the freeze skipped CI as text-only, and nothing in the tree keeps a code change out
of such a push); and the cross-session courtesy of keeping CI runs sequential.

## What the builder flagged — probe these, do not inherit them

Treat each as a **claim to verify**, not a conclusion. If one turns out understated, that is a
finding; if overstated, say so.

- **The `Last swept` marker has moved with every decision since D168**, each version bump claiming a
  sweep, which is the per-decision claim D74 declined to demand. From D188 to D193 each bump rested on
  reading the `Not checked` block and writing the changelog entry, not on a sweep of the whole
  specification. Decide whether the marker's claim holds, and what phase 5's close requires of it.
- **D191 records the deterministic tier's reach without a figure.** Re-run the held-out coverage and
  check that its qualitative statements hold — in the conversation with the owner, not in the report.
- **Both sets trace each finding to entries of one tier only** (OB-49): 64 traces from deterministic
  entries to assert-type findings and 19 from judged entries to judge-type ones in the design set, and
  the held-out traces are said to follow the same convention. Check both counts, and what the
  convention does to agreement's false alarms and coverage's uncovered set.
- **OB-7 is open again**: held-out agreement is measured and never committed (D175), so
  `JUDGED_AGREEMENT_PENDING` cannot close on a committed figure, and what closes it is undecided.
- **Held-out paths are tested with invented data only**: design calls declared held out and renamed,
  under a log re-recorded to match. Check that the fixtures exercise what actually differs between the
  sets, and name a held-out-only path no invented fixture reaches.
- **D193's checks are narrow by design**: the identifier check reads only two-capital prefixed shapes,
  and the settlement check takes every lowercase token in backticks in Class 5 as declared. Decide
  whether either narrowness hides a present or likely gap.
- **The coverage report reads the held-out calls' policies from `--policies` unless
  `--held-out-policies` is given.** Check that default against what the held-out calls read.
- **D190 assigned the design store's bands once** and re-exported, and the committed severity file
  moved on two provenance fields alone; check that claim against the file's history.
- **Open obligations**: `OB-1` to `OB-4`, `OB-7`, `OB-9`, `OB-15` and `OB-46` are `open`; `OB-5`,
  `OB-16` and `OB-47` to `OB-49` are `deferred`. For each deferred row, ask whether its trigger is an
  event somebody will notice.
- **Phase 5 is not closed.** The reveal handover is `open`, and a closed handover for a phase requires
  the sweep marker to reach the last decision it records. Say what must happen, in what order, for the
  phase to close.

## What to produce

A report named `sessions/AUDIT-<date>-phase-5.md`, dated the day you write it, following the
convention the reports already in `sessions/` use. Read one of them before writing yours — the format
below is theirs, not an invention of this prompt.

1. **Baseline, reproduced** — what you ran and what it printed, for the design set; for the held-out
   sections, only whether each computed and its exit code.
2. **Findings**, each with an id (`P5-1`, …), a severity, a `(reproduced)` or `(by reading)` marker,
   tags naming the category, the reproduction, the mechanism (`file:line`), and a **closure** — what
   would fix it, not merely that it is wrong.
   - **High** = held-out content in this tree, a fail-open path, or a gate or verifier tick that does
     not stand for what it claims.
   - **Medium** = a real gap phase 5's close, phase 6 or the next held-out set will hit.
   - **Low** = hygiene, duplication, or an untested edge with no current instance.
3. **Requirements against code, both directions.**
4. **Counts, enumerations, and the mechanisms that hold them.**
5. **Mechanisms versus memory.**
6. **Held-out content** — what you read, how you searched this tree for it, how you proved the search
   could find something, and that the report itself carries none.
7. **What was not checked** — explicitly, including what you were not allowed to read.
8. **Suggested order of work**, with what must close before phase 5 can close separated from what can
   follow it.

Add a maintained **status banner** at the top, as the existing reports carry: findings are closed by
later sessions and the banner is how a reader knows which. Before committing the report, run
`tools/check_holdout_absence.py` and the fast document checks over it:

```bash
uv run pytest -q tests/test_document_counts.py tests/test_contract_coverage.py tests/test_obligations.py tests/test_phase3_acceptance.py tests/test_findings_evidence.py
```

## Rules

- **Audit, do not fix.** Report and propose closures. If you find something you think must be fixed
  during the audit — above all, held-out content already in the tree — say why and ask first.
- **Never spend.** Nothing in this audit needs a model call; if anything would issue one, stop.
- **Never tag.** And touch nothing in the held-out repository or in `comparative-judgment`: no edit, no
  commit, no dispatch, no issue.
- **The owner decides every fork**, through a selectable question with your recommendation first. End
  every substantive turn with an **Assumptions** list.
- **Commits:** show each message verbatim and ask; stage files by name; no attribution lines; verify
  the stored message with `git cat-file commit HEAD | sed '1,/^$/d'` compared by `cmp` against the file
  you committed with. **Do not push unless asked**, and before any push compare the remote's owner with
  `gh api user`; watch CI after it, and keep CI runs sequential with the other session's.
- Write files with LF endings, and write any script that carries escapes with a file-writing tool
  rather than a shell heredoc. Worded numbers are live claims read by count guards; digits are
  historical statements. US spelling is enforced by test.
- `sessions/` holds what a session wrote for the next; the root holds what a mechanism reads by name.

## One thing worth knowing before you start

Four times in this project an audit instrument was itself the defect — a patch tool that reported
success while applying nothing, a gate that could not see the code it was testing, a gate whose
verdict depended on machine speed, and a control gate that read a skipped test as a pass (D143). Each
looked like a finding about the tree.

**Before you trust a null result, prove your instrument can produce a positive one.** A clean search
for held-out content from a search that cannot find any is indistinguishable from a clean tree.
