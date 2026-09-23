# voice-agent-eval-harness

An LLM-as-a-judge evaluation harness for agentic voice-support calls, shipped as a **worked
reference rather than a framework**: an authored corpus, the findings drawn from it, the severity
those findings carry, and the checks that stop the three from quietly disagreeing.

**Reading and verifying all of it needs no API key and costs nothing.** The corpus is authored, the
findings are adjudicated by a human, and every claim made about them is asserted by a test. A model
is required only for the judged tier, and only against transcripts of your own.

The thing worth looking at is not the agent. It is the apparatus around it: what a defect is, how a
finding cites the line that proves it, how severity gets assigned without anybody picking a number,
and what keeps a document from drifting away from the artifact it describes.

## What is here

| path | what it is | license |
| --- | --- | --- |
| `corpus/` | sixteen<!-- #design_set_size --> authored call transcripts, the reference policy documents they retrieve, the findings drawn from them, the severity file joined onto those findings by id, and `corpus/retell/`, the same calls as Retell call objects, generated from the transcripts for the second adapter and invented like the rest (D203) | CC BY 4.0 |
| `specs/` | the specification, the canonical event model, the transcript format, the taxonomy coverage map, and the decision record the design was written from rather than reconstructed against | CC BY 4.0 |
| `rubric.yaml` | the rubric: which check runs against which finding, with what parameters, at what tier, behind what gate. Authored, and at the root rather than in the package because it is an argument rather than a default (D112) | CC BY 4.0 |
| `src/harness/` | the package: the event model and the vocabulary of what a source cannot carry, the transcript adapter and the **second adapter**, over a Retell call object (D203), the extraction tier, the findings view generator, the deterministic checks, the rubric loader, the engine that runs them, the **model transport seam** with its live and replay implementations and its run-log writer, the **judged tier** — prompt rendering, citation validation and the repetition engine — the two-audience report, judge-versus-label agreement, coverage by severity, the severity loader, the **log inspector** (D205), **per-instance severity** computed from declared boolean properties (D206), the held-out declaration every command that writes reads, and the `harness` command | Apache-2.0 |
| `tools/` | the checks that are not tests — the **six**<!-- #phase_verifiers --> phase verifiers, the control gate that re-derives every `connected` verdict by restoring its defect, the cross-repository interface scanner, the held-out absence scan, the gold-set builder, the generator of the Retell source documents, the statement inventory, the builder of the published snapshot, which refuses to export a file carrying an absolute filesystem path it has not been told about, the freeze-proof verifier that recomputes a published citation from git's own object rule, the screen that triages the control register for controls testing a copy of their rule, and the generator of the findings review worksheet | Apache-2.0 |
| `tests/` | the suite, including the document-agreement guards that make a stale number a build failure | Apache-2.0 |
| `hooks/` | repository hooks, including the guard that refuses a populated `.env` | Apache-2.0 |
| `OBLIGATIONS.md` | what a session decided was owed and did not do, harvested from the handovers by rule and carrying a machine-read status per row (D126) | CC BY 4.0 |
| `runs/` | the recorded judged runs, including the committed reference log every replay and every report is served from | CC BY 4.0 |
| `snapshots/` | the rendered report the suite and CI compare against byte for byte | CC BY 4.0 |
| `prompts/` | the judge prompt scaffold, hashed into every run log so a replay against a changed prompt refuses rather than serving a fossil (D8, D123) | CC BY 4.0 |
| `severity-properties.yaml` | what kind of harm a violation of each rubric entry means, as three declared booleans per entry: the authored half of per-instance severity, beside the frozen rubric and never in it (D206) | CC BY 4.0 |
| `CONTROL-REGISTER.md`, `HOLDOUT-OBLIGATIONS.md` | the registers: every control with the defect that drives it red, and what the held-out set is owed | CC BY 4.0 |
| `HELDOUT_SET` | the held-out calls' identifiers, declared here because nothing in this repository can discover them | CC BY 4.0 |
| `freeze-proof/` | the freeze commit's own object bytes, its annotated tag, the two trees reaching the frozen `rubric.yaml` and prompt template, and under `objects/` the whole frozen `src` subtree named by object id — published so that the held-out repository's citation of the freeze by SHA can be recomputed rather than believed, and so its gate can run the frozen harness's own code, in a snapshot whose log contains neither (D209, D210) | CC BY 4.0 |
| `README.md` | this document | CC BY 4.0 |
| `control-mutations.yaml` | the mutation that drives each control red, read by the control gate | Apache-2.0 |
| `pyproject.toml`, `uv.lock` | the package declaration and its exact resolved dependencies | Apache-2.0 |
| `.github/`, `.gitignore`, `.gitattributes` | the CI workflow, the ignore rules and the line-ending rule | Apache-2.0 |
| `LICENSE`, `LICENSE-CC-BY` | the two license texts themselves | — |
| `SNAPSHOT.md` | what this published repository is, and what it leaves in the private working history it was taken from | CC BY 4.0 |
| `.env.example` | the credential template. Copy it to `.env` **only** if you intend to spend money; nothing else in this repository needs it | Apache-2.0 |

`LICENSE` is the Apache-2.0 text and `LICENSE-CC-BY` the CC BY 4.0 text. **Every tracked top-level path is named in the table above or in the paragraph below**, and `test_the_readme_names_a_license_for_every_top_level_path` fails on one that is not, so a new tree arrives with a license or with a decision that it has none (D201).

**The handovers and audit reports in `sessions/` are under neither**, and the boundary above is why:
it is drawn as a path, on the argument that one which cannot be drawn as a directory is one no reader
can check (D31), and `sessions/` is named on neither side. That is a decision the owner has not taken
rather than an omission — the decision record's `Not checked` block records it that way, and
assigning a license is not a refactor's to do. This sentence named the audit and the handover as
root-level Markdown until 2026-09-09; they moved to `sessions/` at D120.

## Running it

```bash
uv sync
uv run pytest
```

```bash
uv run harness run --tier assert
```

Runs the deterministic tier over the corpus: every rubric entry against every call, a verdict per
entry, then the roll-up. **It exits 1 here, and that is the tier working.** The corpus is seeded
with defects by construction, so a gate that held over it would mean the checks had stopped
finding them (D105). Exit 2 is a run that could not start — a rubric that does not load, a
transcript the adapter refuses. Exit 3 is a tier that could not be completed: something errored
or came back unevaluable, so a pass rate behind a gate would have been computed over a
population that is not the one the rubric names.

```bash
uv run harness run --tier judge --mode replay --run-log runs/reference-<version>.jsonl
```

Runs the judged tier from a recorded run log. **This is the default mode and it spends nothing** —
replay neither reads a credential nor imports the Anthropic SDK, which is a property of the import
graph rather than a branch somebody has to take (D8, D122). A request the log does not hold aborts
naming the missing hash rather than quietly going to the network, and a log recorded against a
different rubric version or prompt template is refused unless you pass `--allow-stale-replay`.

The judged tier has a gate: N repetitions become one verdict per call by modal vote, and a rate gate
below its threshold exits 1 -- a finding about the agent, as it is for the deterministic tier (D134).

```bash
cp .env.example .env    # then add a key
uv run harness run --tier judge --mode live
```

**This one spends money**, which is why it is the only mode behind an explicit flag. It prints an
estimated call count and cost — measured from the prompts it is about to send, not from a constant —
priced both at the most the run can cost and at what it is expected to cost, from the answer lengths
the committed reference run recorded for each dimension. It issues nothing until you confirm at the
prompt. `--max-calls N` caps the run; without it a
declared default ceiling applies rather than running uncapped. Recording is unconditional, so a live
run leaves behind a log the replay command above can serve — and if the run aborts, `--resume` with
that log finishes it, serving what was recorded and issuing only the calls it lacks.

```bash
uv run harness agreement
```

Judge-versus-label agreement, read from recorded runs, so it spends nothing (D175). For every rubric
entry it counts, over each set's calls, the hits and misses on the calls carrying a finding traced to
that entry, the false alarms and correct silences on every other call, and the calls it gave no
verdict on, by status, so each row sums to the set's call count. A judged entry fires where its gate
reads a violation, which is the verdict the harness acts on. The design section is printed over the
committed reference log every time. The held-out section is printed only when every `--held-out-*`
input is given — the transcripts, the corpus version file, the held-out run's log, and the labels'
`findings.yaml` and `traces.yaml` — each from outside this checkout, and only to stdout. It exits 0
when computed and 2 when refused: it is a measurement, not a gate. `--held-out-policies` is the
one held-out input with a default: the held-out calls read `--policies` unless it names their own,
which the present held-out set does not need. A held-out log judged under another rubric than the
one this run reads, or under none, is refused (D197).

```bash
uv run harness coverage
```

Coverage by severity, read from the same replays (D188). A finding is **retired** when a rubric entry
traced to it fired on its call, **uncovered** when no entry is traced to it, and **missed** when one
is and none fired. For each severity band of each set it prints how many findings the band holds,
how many are traced and how many are retired, and the same three for each kind of finding within the
band — one a deterministic check could catch, one that needs the judge, one only a human would
notice — then names the retired, the uncovered and the missed band by band, and the findings with no
band beside them. Each set is banded by its own severity file, and nothing is totalled across bands or across sets (D157, D177). The held-out section also takes
`--held-out-severity`, that set's own severity export, and goes to stdout alone, as agreement's does.
A band placed on finding text that has changed since it was scored is refused rather than counted
(D189). Its exit codes are agreement's.

```bash
uv run harness inspect
```

The log inspector (D205): invariants over a completed run log, the committed reference log by
default and any other with `--run-log`. **It emits metrics and never a score.** Every line is a
count, or a proportion printed with both its terms, with a sentence under it saying what it would
mean if it moved: whether every reference resolves to a blob written earlier, whether each blob
re-hashes and each request hash recomputes, whether repetitions run unbroken and share one request,
and what each informed retry was for, read from the logged prompt rather than from the validator
that rejected the answer. It exits 0 whenever the log could be read and 2 when it could not, and
never 1: deciding a count is too high is a threshold, and nobody chose one.

```bash
uv run harness severity
```

Per-instance severity over the design set (D206): a band for every rubric entry counting against
its gate on a call, **computed in code with no model call**, from what kind of harm a violation of
the entry means, declared in `severity-properties.yaml`, and what happened in the call, read from
the event stream. No property turning true can lower a band, which is what makes it a severity
rather than a label. The computed bands are printed against the ranked bands of the findings each
instance traces to, as a table of counts that gates nothing.

```bash
uv run python tools/verify_phase1.py
uv run python -m tools.verify_phase2
uv run python -m tools.verify_phase3
uv run python -m tools.verify_phase4
uv run python -m tools.verify_phase5
uv run python -m tools.verify_phase6
```

Each verifier walks its phase's acceptance criteria **by running them** rather than by reading a
checkbox, and prints the caveats that a passing criterion does not erase. Give each
`--junit build/phase1-junit.xml` and they read one report instead of every one of them spawning
another pytest run (D113). The phase-5 verifier was written while its phase was open (D176). It ticks what is
built and prints, under their own heading, the criteria the held-out repository's gate asserts,
counted apart and never ticked (D176). The phase-6 verifier was written on the day that phase's contract was read (D201): it ticks the second adapter, the log inspector, per-instance severity and the license table, and declares prompt caching, judge-model comparison and the design document not yet built.

```bash
uv run python -m harness.findings_view --check
```

Asks whether the generated Markdown view of the findings is stale against the YAML it derives from.
Drop `--check` to regenerate it.

```bash
uv run python -m harness.extract
```

Runs the extraction tier: transcripts in, a frozen artifact out.

```bash
uv run python -m harness.extract --adapter retell --out build/extraction.retell.json
```

The same tier over the **second adapter** (D203): the design calls as Retell call objects, from
`corpus/retell/`, written against Retell's public documentation as it read on 2026-09-20. What that
call object cannot carry is declared on each call rather than invented — no entry for a disclosure,
an applied policy clause, a state change or a call's lifecycle, and no timing on a tool call or its
result — and the adapter's stream equals the text adapter's everywhere else, for every design call.
**A call from this adapter can be extracted and cannot yet be evaluated**: no check reads a declared
gap, so the seam every tier shares refuses one by name, and `harness run` reads the text
serialization alone. `uv run python -m tools.make_retell_documents --check` asks whether those
source documents are stale against the transcripts they are generated from.

## The three repositories, and what each needs from the others

This project is one of three that depend on each other in ways no one of their test suites can see. The published snapshot is a fourth repository and not a fourth participant: it is a copy of the working repository's tree, it holds no secret, and nothing dispatches to it or reads from it.
That is the reason for `HOLDOUT-OBLIGATIONS.md`, and the reason the two checks below exist at all.

| repository | what it is | what it needs from elsewhere |
| --- | --- | --- |
| **voice-agent-eval-harness-private** (the working repository, which the public `voice-agent-eval-harness` is a snapshot of) | the corpus, the findings, the harness | reads [`comparative-judgment`](https://github.com/hmbseaotter/comparative-judgment)'s specification in CI, to check the shared findings interface still agrees |
| [**voice-agent-eval-harness-holdout**](https://github.com/hmbseaotter/voice-agent-eval-harness-holdout) | the held-out corpus, whose labels are sealed there and revealed after the rubric freeze | reads this repository for the conventions it ports, `HELDOUT_SET`, the modules its tools import, the documents its packet copies, and the freeze proof under `freeze-proof/`, which its gate verifies by recomputation (O-12) |
| [**comparative-judgment**](https://github.com/hmbseaotter/comparative-judgment) | the severity tool: scores by pairwise comparison, never by picking a number | asks the working repository to run the interface scanner when its own specification changes |

Two facts about this shape are worth stating plainly, because both have already caused a silent
failure:

- **The findings interface spans two repositories and is checked in one.** `tools/check_spec_interface.py`
  compares this specification against the severity tool's, field by field. It runs here, so a change
  made *there* is caught only when this repository builds — which is why that repository now asks
  this one to build when its specification moves.
- **The held-out set cannot be checked from here.** `HELDOUT_SET` names its call identifiers because
  nothing here can discover them, and it must be updated whenever that set grows. Identifiers are
  metadata and safe to hold; the transcripts are content and are not.

## Access: the tokens CI needs, and when it needs them

**This workflow reads no secret.** One secret is left in the arrangement and it is a *write*
permission. A secret exists here because CI has to reach *across* a repository boundary that the
default `GITHUB_TOKEN` cannot cross — it is scoped to the repository running the workflow — and
**reading** across that boundary needs no secret once the far side is public, while **starting a
workflow** in another repository needs one either way.

**One of the four repositories is private**: the working one, because it holds the history the
snapshot is taken from. The snapshot and `comparative-judgment` are public since 2026-09-21 and the
held-out companion since 2026-09-22, so both read tokens were retired on 2026-09-22 — `CJ_READ_TOKEN`
here and `HARNESS_READ_TOKEN` in that repository (D212, O-12).

| secret | lives in | grants | so that |
| --- | --- | --- | --- |
| `HARNESS_DISPATCH_TOKEN` | `comparative-judgment` | `Actions: Read and write` on the working repository | a specification change there can ask the working repository to run the interface scanner now, rather than whenever it next builds |

`Actions: Read and write` is the narrowest grant that can start a workflow; GitHub offers no
write-only option for it.

**The steps below are the only copy of this procedure.** The other repositories' READMEs say what
their own token is for and when it expires, and point here for how to make one, so the steps cannot
drift apart between documents. They are written for any token these repositories need: the one above
today, and the read tokens again under the conditions in *If you run copies privately*.

### Setting one up, step by step

1. **Put the repositories under one account.** These four are the author's, under `hmbseaotter`: the
   working repository, the snapshot built from it, the held-out companion and the severity tool. To
   run them under another account, copy them there and change the repository names the workflows
   spell out, including the error messages beside them that name the same repository:

   | workflow | names |
   | --- | --- |
   | this repository's `.github/workflows/checks.yml` | `hmbseaotter/comparative-judgment`, which it checks out |
   | `voice-agent-eval-harness-holdout`'s `.github/workflows/checks.yml` | `hmbseaotter/voice-agent-eval-harness`, the published snapshot, which it checks out (O-12) |
   | `comparative-judgment`'s `.github/workflows/checks.yml` | `hmbseaotter/voice-agent-eval-harness-private`, whose workflow it starts |

2. **Create the token**, one per secret you need — the table above has one row today. GitHub → your
   avatar → **Settings** → **Developer settings** → **Personal access tokens** → **Fine-grained
   tokens** → **Generate new token**, or go straight to
   <https://github.com/settings/personal-access-tokens/new>.

   | field | value |
   | --- | --- |
   | Resource owner | the account that owns the repositories |
   | Repository access | **Only select repositories** → the repository named in the row's *grants* column |
   | Permissions | **Repository permissions** → the permission from that column, and nothing else |
   | Expiration | your choice — and record it, in step 5 |

3. **Install it where the row says it lives.** Copy the token on the page that follows; GitHub will
   not show it again. Then open the repository under *lives in* → **Settings** → **Secrets and
   variables** → **Actions** → **New repository secret**, named exactly as the table spells it.

4. **Check that it works.** Every workflow here can be run by hand: the repository's **Actions**
   tab → **checks** → **Run workflow**.
   - `HARNESS_DISPATCH_TOKEN`: run `comparative-judgment`'s workflow. Its `notify-harness` job must
     print *Asked the harness to run its interface scanner.*, and a `workflow_dispatch` run must
     appear in the working repository's **Actions** tab, which is where that workflow dispatches.
   - **the sibling checkout, which needs no token while `comparative-judgment` is public**: run this
     repository's workflow. *Check out the severity tool alongside it* must pass, and *Interface
     agreement across both repositories* must print `spec interface: OK`. It fails loudly rather than
     quietly if that repository ever stops being readable (D84).

5. **Record when it expires**, in the README of the repository that holds it, and change that date
   whenever the token is replaced. It is the one fact about a token no file in the tree can recover,
   and the failure below is what happens when nobody has it.

**No read token is left to expire.** `CJ_READ_TOKEN` was installed on 2026-09-06 with a 60-day
lifetime, while `comparative-judgment` was private, and was deleted on 2026-09-22 once that
repository had been public for a day; `HARNESS_READ_TOKEN` went the same day, in the held-out
repository. `HARNESS_DISPATCH_TOKEN` is a write permission and stays, with its own expiry stated in
the repository that holds it.

### If you run copies privately

Everything above assumes this account's arrangement: three public repositories and one private
working copy. **A copy whose repositories are private needs the two read tokens back**, because the
default `GITHUB_TOKEN` is scoped to the repository running the workflow and cannot read a second
private one. Both were installed by exactly the steps above, and their grants were:

| secret | lives in | grants | so that |
| --- | --- | --- | --- |
| `CJ_READ_TOKEN` | the repository running this workflow | `Contents: Read-only` on `comparative-judgment` | the interface scanner can check the severity tool's specification out and compare it |
| `HARNESS_READ_TOKEN` | `voice-agent-eval-harness-holdout` | `Contents: Read-only` on the harness repository it checks out | the held-out suite reads the conventions it ports, `HELDOUT_SET`, the modules its tools import, and the freeze proof it reconstructs the frozen source from |

**Pass a read token on its own line rather than OR-ing it with the default token.** An expression of
the form *secret or else the default* looks like a fallback and is not one: an expired secret is still
a non-empty string, so it is passed rather than fallen back from, and a checkout that needs no token
then fails on a dead one. Both workflows carried that shape and both dropped it (D212).

### They expire, and that is the failure mode that has actually happened

A fine-grained token has a maximum lifetime, so **any token you install will stop working on a date
nobody is watching for**. What that costs:

- **`HARNESS_DISPATCH_TOKEN` lapses** → a specification change in the severity tool stops asking this
  repository to check the interface. That step fails loudly and names the permission required.
- **The sibling stops being readable** → the checkout fails and the interface check compares nothing.
  This is not hypothetical: it is D84. The checkout failed on every run from the day it was added,
  and the interface scanner "never once compared the two interfaces it exists to compare" — in a
  workflow that reported success. The step now **fails the build** and says what to check instead of
  skipping quietly. `CJ_READ_TOKEN` was what fixed the cause, and it is retired since 2026-09-22
  because the sibling is public; the guard stays, because a repository can be made private again.
- **A read token in a private copy lapses** → the same shape one repository over: the held-out suite
  stops reading what it ports, and its workflow fails rather than going quiet.

The pattern is deliberate and is the lesson underneath them all: **a check that goes quiet is worse
than a check that goes red**, because the quiet one still reports success.

**`[skip ci]` and when it may be used.** A full run here takes about ten minutes, so a push whose
every commit changes documentation prose only — a README, a specification, the decision record, a
register, a handover — may carry `[skip ci]` in its head commit's message, with the fast document
checks run locally first:

```bash
uv run pytest -q tests/test_document_counts.py tests/test_contract_coverage.py tests/test_obligations.py tests/test_phase3_acceptance.py tests/test_findings_evidence.py
```

It is **not** prose-only if any commit in the push touches code, tests, tooling, config or CI, or
project data that happens to be prose: transcripts, findings, labels, rubrics, prompts, policies,
logs, snapshots or generated views. One such commit anywhere in the push means the whole push runs
CI, because a skip on the head commit silences it for everything beneath. Nothing in this tree
enforces this: the phase-5 audit's P5-13 found the rule kept on all six skipped pushes so far and
held by nobody but the session doing the pushing.

## Where the reasoning lives

- `specs/voice-agent-eval-harness.md` — the specification, its acceptance criteria and its changelog.
- `specs/voice-agent-eval-harness.decisions.md` — every fork taken, why, and what enforces it. Each
  decision from D19 onward ends with a `**Rule**` line naming a test, a scan, or explicitly
  *judgment, not checkable*.
- `HOLDOUT-OBLIGATIONS.md` — what this repository owes the held-out one, and what it has discharged.
  It exists because a convention changed here can leave that set out of step with nothing able to
  notice.
- `sessions/` — everything one session wrote for the next: the audit and sweep reports, the
  handovers, the session and audit briefs, and the two briefs that governed the held-out repository, both marked spent at their own tops: that
  repository now carries its own design document. They accumulate, one per session, which is
  why they are no longer in the root. The line is that **the root holds what a mechanism reads by
  name and this folder holds what a reader reads for continuity** — a boundary that can be drawn as
  a path, which is D31's test for whether a placement rule is checkable at all. Start with
  `sessions/AUDIT-2026-09-06-harness-holdout-cj.md`, an independent read of all three repositories,
  with what survived reproduction and what did not.

## License

Code, configuration and tooling are Apache-2.0 (`LICENSE`): `src/`, `tools/`, `tests/`, `hooks/`, the CI workflow and the package and control-gate configuration. Authored data and documentation are CC BY 4.0 (`LICENSE-CC-BY`): `corpus/`, `specs/`, `rubric.yaml`, `severity-properties.yaml`, the recorded runs and snapshots, the prompt scaffold, the registers, the published freeze proof and this README. The table under *What is here* states each path's.
The boundary is a path boundary rather than a per-file one, deliberately (D31): a license line that
cannot be drawn as a directory is one no reader can check and no packaging tool can respect.
