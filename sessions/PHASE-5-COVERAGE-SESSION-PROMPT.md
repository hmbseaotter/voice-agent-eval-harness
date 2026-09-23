# Session prompt — build phase 5's coverage report by severity

> **SPENT — 2026-09-18.** The coverage report by severity was built and is in the tree
> (D188, extended by D192). Kept as a record, not as a brief to paste.

*Paste the section below as the first message of a fresh session in the harness repository. Run it
on **Claude Opus 5** at effort **xhigh**.*

*Why a fresh session: the session that ran the held-out agreement had a context too long to carry
another build cleanly, and everything it knew that this build needs is in the repository now — the
handover of 2026-09-18, the decision record and the obligations registers. Reading held-out content is
not the reason: the labels are public, this build must read them, and it authors no rubric.*

*Why Opus 5 and not Fable 5.1: the contract is written — two criteria, a scope bullet and three
decisions — and the work is building against it with this repository's full verification machinery.
That is Opus's shape of problem, as it was for phase 4. The one open term in the contract is a single
fork to put to the owner, not open-ended design.*

*Why xhigh rather than max: nothing here spends money. The report makes no model call, so a design
error costs a check chain of about an hour rather than a paid run, which is what put phase 4 at max.
It is still more than high, because the build crosses every interlock this repository has — the
specification and its sweep markers, the decision record, the phase verifier's declared-to-ticked
conversion, the contract coverage table, the control register and its gate — and missing one costs a
full chain.*

*State to start from: a clean checkout of `main` at `4adb18d` or later, with CI green. No other
session should touch the harness tree while this one runs a chain.*

---

You are building the one piece of **phase 5** of the voice-agent evaluation harness that is still
declared not yet built: **the coverage report by severity**, for the design set and the held-out set
apart.

## Read this part first: what you may read, and what may never enter this tree

**The held-out labels are public.** The held-out label chain completed on 2026-09-18 (C1, C2 and C3,
each with the held-out repository's gate green) and the rule against searching the labeling sessions
is retired; see `HOLDOUT-OBLIGATIONS.md`. So you **may** read these six files, in place, in
the held-out repository's checkout beside this one, and **nothing else in
that repository**:

- `labels/findings.yaml`, `labels/traces.yaml` and `labels/severity.json`;
- `transcripts/`, `CORPUS_VERSION`, and the run log under `runs/` whose name starts `heldout-` —
  needed only if the report reads a run, which is the first question below.

**What does not end with the reveal:** no held-out transcript text, run log, label, or report over
held-out findings or calls ever enters this repository's tree, a commit, a test fixture or a message
to be committed. The absence check (`tools/check_holdout_absence.py`) still runs on every push, and
agreement's held-out section still goes to stdout only (D175). **Test with invented data only.**

**You author no rubric.** `rubric.yaml` and `prompts/judge-dimension.v1.md` are frozen at the
`rubric-frozen-v1` tag and pinned there by test. A session that has read held-out content does no
rubric work in this project, and you will have read it.

## Where things stand

Read, in this order: `sessions/HANDOVER-2026-09-18-held-out-reveal.md`; the specification's phase-5
criteria and its scope bullet on the coverage report; decisions D157, D175, D176, D177, D185 and D187
in `specs/voice-agent-eval-harness.decisions.md`; `tools/verify_phase5.py`.

- `tools.verify_phase5` ticks the phase-5 criteria that are built and **declares** the two coverage
  criteria not yet built. Building them means turning those two declarations into ticked criteria and
  removing the declarations: the binding test refuses a criterion that is both ticked and declared
  (D176).
- The design set's severity file is `corpus/findings.severity.json`, schema 3, read by
  `harness.core.severity.load_severity`. The held-out set's is `labels/severity.json` in the held-out
  repository, which that side reports passes the same loader. Read it in place; never copy it here.
- Nothing in the harness reads either file into a coverage figure yet.

## What the contract says, and what it does not

The two criteria: the report lists findings retired by severity and names the uncovered set
explicitly, for the design set and the held-out set apart, each banded by its own severity file
(D177); and it states, for each severity band, how many findings are retired out of how many that
band holds, read per band rather than pooled (D157), never pooling one set's bands with the other's
(D177), and counting and naming the findings that carry no band beside those figures (D187).

Settled already, so do not re-ask: **no weights** — a weight per band would be a threshold nobody
chose (D157); **the sets stay apart**, each banded by its own store's cuts (D177); **question-tier
findings are not `unplaced`**, and the report names the findings with no band rather than leaving
them out of both (D187).

**Not settled, and not defined anywhere: what "retired" means.** No document says when a finding
counts as retired, and the build turns on it. Put it to the owner before writing any code.

## Decide these with the owner before building

Ask each as a selectable question, your recommendation first, with the evidence you read.

1. **What makes a finding retired.** The readings that survive a read of the record:
   - *traced*: some rubric entry is traced to it — `traces_to` in `rubric.yaml` for the design set,
     the traces file for the held-out set — and the uncovered set is the findings traced to none.
     The held-out traces file's own key for those is `uncovered`, and D157's reason for per-band
     coverage is an uncovered set concentrated in the most severe band;
   - *caught*: an entry traced to it fired on its call in a run, which needs each set's deterministic
     tier and judged replay, as agreement already computes them;
   - both, side by side.
   Note what each costs: *caught* reads transcripts and a run log, and agreement already reports
   firing per entry.
2. **Where the held-out section goes.** The held-out output names held-out findings and their bands,
   so it may not be written into this tree: stdout only, as agreement's is (D175), or also a file
   outside the checkout, as the evaluation report may be (D185).
3. **Which command carries it.** A section of `harness agreement`, a new subcommand, or a section of
   `harness report` — noting that `snapshots/report.md` is diffed byte for byte in CI, so the last
   moves the snapshot deliberately.
4. **Whether the absence check learns the shape.** It recognizes a held-out transcript by its format
   marker, a held-out run log by its records, and a rendered evaluation report by its heading beside
   a declared call id (D185). A coverage report over held-out findings is none of those.
5. **How the contract records it.** D157 deliberately gave the coverage report no requirement
   statement, so that the stable half of the contract did not move for the table's sake. A refusal
   or an output rule is behavior, and D185 gave its refusal a requirement; ask whether this build
   does the same.

## What exists to build on

- `harness.core.severity`: `load_severity`, `join`, `BAND_ORDER`, and the file's `unplaced` list.
- `harness.agreement`: `load_traces`, `check_held_out_labels`, `design_expected`,
  `held_out_expected`, `HELD_OUT_FINDING_ID` and `RUBRIC_FROZEN_V1`.
- `harness.core.findings`: `load_findings`, and `Tier`, whose docstring says why question-tier
  findings are never scored.
- `src/harness/cli.py`: `agreement_command` for held-out inputs given in part or inside the checkout
  and a stdout-only held-out section; `report_command` for D185's refusal of an output path inside the
  checkout over held-out calls.

## Tests

Held-out paths are tested with **invented data** built from the design set, never with held-out
files. `tests/test_cli.py` shows the pattern: `_split_corpus` declares design calls held out in a
`HELDOUT_SET` of the test's own, and `_invented_labels` borrows design findings under `HF-` ids. An
invented held-out severity export can be the design export with its ids remapped the same way, which
keeps its bands agreeing with its cuts.

Every behavior change gets a control: an entry in `control-mutations.yaml` naming a module-level test,
a `find` line present exactly once in its file, and a row in `CONTROL-REGISTER.md`, with the count tag
updated. Controls run in a copy of the tree with no `.git`, and every mutation in the gate shares one
copy, so a test that writes a file must remove it again.

## Definition of done

- The two coverage criteria are ticked by `tools.verify_phase5`, their declarations removed, and the
  verifier exits 0 over the whole suite.
- Both sets' coverage is stated per band, with the unbanded findings counted and named, and the
  held-out section never written into this tree.
- The specification's version, its `Last swept` marker, the decision record's `Not checked` marker
  and refresh sentence, the changelog, the document status and numbering all move together; the
  record checks in `tests/test_document_counts.py` hold you to each.
- `MEASURED_CONTRACT` and `tests/test_contract_coverage.py` agree with whatever the specification now
  says.
- The full chain is green: ruff check, ruff format --check, mypy, the whole pytest suite, verifiers 1
  to 5, `harness report --out` diffed against `snapshots/report.md`, the findings view check, the
  absence check, `tools/check_spec_interface.py` over CI's file lists, `tools/statement_inventory.py`,
  and `tools/verify_controls.py` with every control driven red and restored.

## How this repository is worked

- **The owner decides every fork**, through a selectable question with your recommendation first.
  End every substantive turn with an **Assumptions** list.
- **Commits:** show each message verbatim and ask; stage files by name; no attribution lines; verify
  the stored message with `git cat-file commit HEAD | sed '1,/^$/d'` compared by `cmp` against the
  file you committed with. **Before any push**, compare the remote's owner with `gh api user`. Watch CI
  after each push, and keep CI runs sequential.
- **Never tag. Never spend** — this build needs no model call; if anything would issue one, stop.
- Write files with LF endings, and write any script that carries escapes with a file-writing tool
  rather than a shell heredoc. US spelling. Verify what you can check rather than assuming it.

## When you are done

Report the coverage figures for both sets to the owner in the conversation — never in a committed
file for the held-out set — and say which of the owner's answers shaped them.
