> **WORKING STATUS, maintained separately from the report below.** Written 2026-09-12 against
> `6f7ae94`, the tip of the span under audit; `6ac9b8b`, one commit later, adds only the audit
> prompt. A later session that closes a finding records it here, with the reproduction it re-ran, so
> that this banner and not the body is what a reader trusts for status. Corrections to the report
> belong here too.
>
> **2026-09-12, remediation before the freeze — six closed, two half closed, ten open for after the
> freeze, and five corrections to the report.** Every checkable claim in the report was reproduced
> independently before anything was changed, in copies of the tree by the control gate's method: both
> High findings' mutations with their positives, P4-10's, the tie rule, the three cut shapes and the
> bands against their midpoints, the torn log, and the scanner against the sibling's pushed
> specification. Every one came back as the report states it.
>
> **Closed.** P4-7 (`415affe`): the rubric's two stale comment blocks. P4-1, P4-2 and P4-8 (`c5f7ab9`,
> D158): the judged status columns count results, a call's statuses print beside its verdicts, the
> audience sections are asserted in both directions on the rendered report, and a judged entry is found
> by its modal verdict — four controls, five mutation entries. P4-3 (`eda6c17`): the reference-run
> helper calls the roll-up's tie rule, with a control. P4-6 (`57ee0d3`, D159): the specification swept at
> 0.29.0 — the judged tier's exit code and the verifier list corrected, `--resume` in the contract as a
> `[P4]` requirement and criterion, and the `Not checked` block refreshed.
>
> **Half closed.** P4-5 (`64b5848`): every scored finding's band is pinned; the loader's inversion, name
> and band-against-midpoint checks remain. P4-13 (`57ee0d3`): the README's judged paragraph and verifier
> list, the three command docstrings and the tool's version in the `Not checked` block are corrected;
> the report caveat's scope and the OB-17 figures remain.
>
> **Open, for after the freeze**, each carried as a deferred obligation whose trigger is the
> `rubric-frozen-v1` tag existing, and listed in `sessions/HANDOVER-2026-09-12-phase-4-audit.md`: P4-4 (OB-24), P4-5's
> loader checks (OB-25), P4-9 (OB-26), P4-10 (OB-27), P4-11 (OB-28), P4-12 (OB-29), P4-13's remainder
> (OB-30), P4-14 (OB-31), P4-15 (OB-32), P4-16 (OB-33), P4-17 (OB-34) and P4-18 (OB-35).
>
> **Corrections to the report**, each checked against the tree before it was written here:
> 1. The commit that recorded the report, `7e9cf79`, says "Nine Medium"; the report has seven Medium
>    and nine Low.
> 2. The report's own status line called it "Untracked and uncommitted"; `7e9cf79` committed it.
> 3. P4-3 names five assertions reading the test helper; the helper was read on nine lines in seven
>    tests.
> 4. P4-9 says the tool's criterion promises byte-identical exports across platforms. The criterion
>    promises two exports over an unchanged log, anchor set and cuts, and names no platform. The defect
>    stands — the same judgments recorded on another platform hash differently — and only the claim it
>    breaks is narrower than stated.
> 5. P4-14's closure pins the uncommitted recording's name and hash in a test, which would fail on CI
>    and on every clone without that file. The 8,192-token truncation belongs in a dated constant.

>
> **2026-09-12, re-verification at `fc56fa7` by the audit's own session (Claude Fable 5.1, effort
> `max`), before the tag — section 8.** The chain re-run step by step at `fc56fa7`: 1147 tests,
> 21, 24, 23 and 22 verifier checks, the inventory resolving, all 110 controls driven red and
> restored (8.1). Every reproduction run twice, in `.env`-free `git archive` copies — positive on
> `7e9cf79`, null on
> `fc56fa7` — with the probes the owner asked for. **P4-1, P4-2, P4-3 and P4-7 hold. P4-6 and P4-8
> hold with a gap**: the expected-cost figure still has no requirement and nothing carries it, and
> D158's "nothing a rubric entry traces was hidden" is false for F-35. **Both half closures hold and
> their remainders are carried in full** (OB-25, OB-30), with the change that matters shown: a
> `theta` moved across its cut midpoint with the band left alone passes every test. **All five
> corrections accepted.** The twelve carried items drop and soften nothing; their shared trigger is
> read by nothing in the tree and only by the test OB-32 owes, itself behind that trigger. Two new
> findings: **P4-19** (Low), the resume criterion ticks with no caveat and its wording is met by the
> fail-open beside it; **P4-20** (Medium), by the gate's reading `J-concerns-addressed` catches none of
> the seven findings it traces — the judge answers `partially_addressed` on every repetition of the
> calls that carry them and the gate reads `unaddressed` alone — and nothing records it. Before the
> tag: P4-20's record, P4-19's caveat line, the expected-cost requirement or a row for it, and the
> push both repositories still lack.
>
> **2026-09-12, second remediation before the freeze, after the re-verification.** P4-20 is closed by
> D160 (`213a517`): `J-concerns-addressed` declares `partially_addressed` violating beside its pole, a
> tie with it resolves toward it, a `[P4]` requirement and criterion carry it, 5 controls re-derive it,
> and a pin holds every judged entry's catch record per finding. The 7 synthesis requests the tie rule
> changed were listed by a replay that records a miss rather than aborting, before anything was spent,
> and recorded again live for $0.29 under a call ceiling agreed first; each gave the verdict of the
> answer it replaced. P4-8's gap is closed by the correction attached to D158, and the P4-8 control,
> which had restated the pole rule beside the check, now reads the entry's violating verdicts. P4-6's
> gap and P4-19 are closed by D161 (`edcda16`): the expected figure has a requirement and a criterion
> caveated with OB-33, and the resume criterion names the rubric-version refusal, drives it through a
> resume, and is caveated with OB-24. Both repositories were pushed before these fixes, and CI passed
> on `e15170d`. **Two additions to section 8**, each checked against the tree: the entry's own comment
> in `rubric.yaml` said its gate fired over this corpus by construction while it held at 1.00, false in
> the file the tag freezes until D160 made it true, and P4-20 did not cite it; and the entry's scale
> definitions overlap, since a call with one concern of several unanswered fits both violating
> verdicts, which D160 records rather than rewrites. **One imprecision**: 8.7 says the judge never
> answers the pole on the seeded calls, where CALL-09 returned it on 3 of 10 repetitions — never as a
> call's modal verdict.

>
> **2026-09-13, second re-verification at `b3c519f` by the audit's own session, before the tag —
> section 9.** The chain re-run step by step: 1156 tests, 21, 24, 23 and 24 verifier checks, the inventory
> resolving, all 115 controls driven red and restored (9.1). **P4-20's closure holds**: the join reads
> none of seven caught on `e15170d` and seven of seven on `b3c519f` with F-85 still missed, the tie
> rule resolves through the roll-up and the synthesis headline alike, and each mutation goes red — the
> tie clause disabled makes the replay miss the seven re-recorded requests. **The re-recording holds**:
> 15 lines differ, the header and seven prompt-and-answer pairs, 1256 byte-identical, each prompt
> differing in the headline the tie moved and the rationale beneath it, each answer keeping its verdict,
> and the snapshot moving where D160 says. **The D158 correction is accepted. D161 holds**: each tick
> stands for what its criterion says, and the caveats name OB-33 and OB-24. **The banner's two additions
> and its imprecision are accepted.** Four new findings: **P4-21** (Medium), D160's rule decides the
> middle values of `J-policy-alignment` and `J-caller-pushback-understood` in the same words and the
> record says nothing about them — a decision the freeze forecloses; **P4-22** (Low), the catch-record
> pin restates the gate's rule; **P4-23** (Medium), an answer with no citations becomes an applicable
> result for every verdict, the pole included, because the rationale line satisfies the evidence guard;
> **P4-24** (Low), the frozen entry names none of the three calls it now fails without a traced finding.
> Before the tag: P4-21's decision, recorded either way, and P4-24's line.
>
> **2026-09-13, third remediation before the freeze, after the second re-verification.** P4-21 is closed
> by D162 (`211c848`): `J-policy-alignment` and `J-caller-pushback-understood` count their middle values on
> D160's reading and the owner's decision, which moves no call's gate for the first and fails CALL-09 for
> the second. The 3 synthesis requests whose resampled headlines changed were listed by the replay that
> records a miss rather than aborting, before anything was spent, and recorded again live for $0.12 under
> a call ceiling agreed first; CALL-22's answer moved from `no_material_defect` to `minor_defect` with that
> row's modal verdict unmoved. P4-22 is closed in the same commit: the catch-record pin and its neighbors
> read `CallRollup.violated`, and the pin fails once `violated` reads the pole alone. So is P4-24: the
> frozen entries name the calls they fail without a traced finding. P4-23 is closed by D163 (`4dbd777`),
> fixed before the tag on the owner's decision rather than carried: an answer citing nothing is refused as
> the declared schema's failure and spends the one informed retry. **One addition to section 9**: the
> synthesis's `rests_on` list had the same gap, its schema requiring at least one identifier and nothing
> local enforcing it, and D163 refuses an empty one the same way whenever the prompt listed dimensions to
> rest on. Neither refusal changes a recorded result. D160 carries a correction: its sentence that every
> judged verdict carries citations by schema was true of the API-side schema and of nothing local.

>
> **2026-09-13, third re-verification at `95aa288` by the audit's own session, before the tag —
> section 10.** The chain re-run step by step: 1159 tests, 21, 24, 23 and 24 verifier checks, the
> inventory resolving, all 117 controls driven red and restored (10.1). **P4-21's closure holds with a
> gap**: both declarations follow the entries' words, neither catch record moved, CALL-09 is the one
> new failure — and it is not a false positive, but the frozen comment names F-35 where the judge's
> rationales rest the failing pushback on F-36. **The re-recording holds**: 7 lines differ, the header
> and three prompt-and-answer pairs, 1264 byte-identical, the snapshot moving in exactly the three
> places named. **P4-22's closure holds**: the pin reads the roll-up and goes red when `violated`
> returns to the pole; the three neighbors that also read it stay green on this corpus, which D162
> overstates. **P4-23's closure and its twin hold**: each refusal spends the retry and resolves to
> `errored`, nothing recorded is refused; the retry names neither empty list and a synthesis shown no
> dimension resolves applicable either way. Five new findings, all Low: **P4-25** the comment's
> attribution, **P4-26** D162's mutation sentence, **P4-27** the retry's wording, **P4-28** the schema
> versus the validator when nothing is listed, **P4-29** a count. Before the tag: P4-25's line.
>
> **2026-09-13, fourth remediation before the freeze, after the third re-verification.** P4-25, P4-26 and
> P4-29 are closed by `94fd27c`: the frozen entry's comment names F-36's exchange as the half every
> repetition on CALL-09 faults, with the cost question of F-35 and F-65 beside it, and a correction
> attached to D162 records that attribution, the mutation sentence (1 of the 4 tests red) and the count
> (4 graded entries); the `Not checked` sentence on CALL-09 follows. P4-27 is closed by D164 (`0b62ec7`),
> fixed before the tag on the owner's decision rather than carried: the retry for a schema failure names
> the failure the engine found, and a synthesis corrected for one is shown the dimension identifiers its
> prompt listed, while the retry for rejected identifiers, the kind all 8 recorded retries are, is
> byte-identical. P4-28 is closed by D165 (`2d876e7`), also fixed rather than carried: a synthesis is
> asked for `rests_on` only when its prompt listed a dimension. Neither engine change moves a recorded
> request. Each was checked by replaying the whole committed log through the changed engine, whose replay
> log matched the committed one record for record, and by replaying a copy with the relevant line
> altered, which aborted on a cache miss. The ceiling of 6 that section 10 left unchecked is not in the
> tree; the remediation session's own record shows the owner's D162 decision naming it, and the resume
> that recorded the 3 requests running with `--max-calls 6`.

>
> **2026-09-13, fourth re-verification at `f401138` by the audit's own session, before the tag —
> section 11.** The chain re-run step by step: 1162 tests, 21, 24, 23 and 24 verifier checks, the
> inventory resolving, all 120 controls driven red and restored (11.1). **P4-25's closure holds**: the
> comment, the correction attached to D162 and the `Not checked` sentence say what the ten rationales
> say. **P4-26's and P4-29's closures hold.** **D164 holds**: each retry names the failure it was sent
> for, the synthesis's lists its dimensions bare, the rejected-identifier retry is the recorded wording,
> all 8 recorded retries are that kind, and the replay serves every record while a one-character change
> to that wording makes it abort after 55. **D165 holds**: a synthesis shown no dimension is sent no
> `rests_on` and its answer stands, one shown dimensions keeps `rests_on` at `minItems: 1`, and no
> recorded request moved; the template's prose still asks such a synthesis for `rests_on` in a key its
> schema forbids, which the schema resolves and the shipped rubric cannot reach. One new finding,
> **P4-30** (Low): the retry names the first failure found, so an answer with two faults is corrected
> for one and refused for the other. Nothing from this pass must close before the tag.
>
> **2026-09-13, after the fourth re-verification.** P4-30 is carried as OB-36 on the owner's decision —
> item 13 in `sessions/HANDOVER-2026-09-12-phase-4-audit.md`, triggered by the tag like OB-30 to OB-35 —
> after the remediation reproduced it: a synthesis answer with a rejected citation and an empty
> `rests_on`, or with both lists empty, is corrected for the first fault only, a retry fixing only that
> fault resolves to `errored`, and a retry fixing both is applicable. Section 11's note on the template's
> `rests_on` sentences stays with D165, which records the template as left unedited, also on the owner's
> decision.

# Audit — phase 4 (the full rubric, the report, and the obligations closed before the freeze), at `6f7ae94`

> **STATUS.** Written 2026-09-12 by an independent session (Claude Fable 5.1, effort `max`) that
> took no part in the phase-4 build or in the obligations closed after it. Written untracked, and
> committed afterwards as `7e9cf79`; nothing in the tree was modified — every mutation below was applied to a copy of the
> tree under the session's scratch directory, with `.env` excluded from the copy and both credential
> variables removed from the environment. Every finding marked *reproduced* was reproduced by running
> something against this tree or a copy of it; one marked *by reading* rests on the source and says
> what could not be run. The session read the design corpus only through the harness (as rendered
> prompts inside the committed run logs, never as transcript files), the shipped rubric and
> template, both run logs in `runs/` as data, every phase-4 source and test module named in the
> prompt, the four verifiers, the control gate and its mutation file, the obligations register,
> D127–D157 and the `Not checked` block, the handover, the README, the specification, and the
> sibling tool's hash, cut and file-writing code. It did **not** open the held-out repository, any
> held-out transcript, the authoring packet, either withheld source folder,
> `HOLDOUT-OBLIGATIONS.md`, `sessions/HOLDOUT-SESSION-PROMPT.md` or
> `sessions/HOLDOUT-REPAIR-BRIEF.md`, and it read no held-out commit message or test docstring — so
> it is clean for rubric work. No live model call was made.

**Kind of review.** The phase-3 report's shape: the baseline reproduced first, both run logs read as
data, every verifier tick asked what would have to break for it to print FAIL, a mutation sweep of the
ticks that looked green-and-blind, the counts recomputed, and a sample of the prose checked against
the tree. Each instrument was made to produce a positive before a null from it was believed: every
mutation that stayed green is paired below with a neighboring mutation that went red in the same
module, so a blind tick is distinguishable from a copy that was never mutated.

---

## 1. Baseline, reproduced

Run as the prompt's chain, one step at a time so each exit code is its own rather than the chain's,
from a detached shell with the log captured whole (D145's rule). The tree was clean at `6ac9b8b`
before and after.

| what | result |
|---|---|
| tip | `main` at `6ac9b8b`, clean working tree, **10 commits ahead of `origin/main`** — the last push was `462f153`, so CI has run on none of the nine obligation commits after it (section 6). The span `7860094..6f7ae94` is 17 commits, 57 files, 12,912 insertions, 639 deletions, as the prompt says |
| `uv run pytest -q` | **1141 passed** in 484.68 s, exit 0 |
| `uv run python tools/verify_phase1.py` | exit 0; "All 21 checks pass, each by running it — 20 of them the specification's own [P1] acceptance criteria" |
| `uv run python -m tools.verify_phase2` | exit 0; "All 24 checks pass, each by running it — 22 of them the specification's own [P2] acceptance criteria" |
| `uv run python -m tools.verify_phase3` | exit 0; "All 23 checks pass, each by running it — 18 of them the specification's own [P3] acceptance criteria, 3 its [P3] requirement prose"; 8 carry a caveat. The closing count P3-10 reported wrong is right now |
| `uv run python -m tools.verify_phase4` | exit 0; "All 21 checks pass, each by running it — 21 of them the specification's own [P4] acceptance criteria"; **15 of the 21 carry a stated caveat** (P4-18) |
| `uv run python tools/statement_inventory.py` | exit 0; "every identifier named in prose resolves" — run again with this report in `sessions/`, which the tool globs, and still resolving |
| `uv run python tools/verify_controls.py` | exit 0; "All 104 controls were driven red by their own defect and restored", 104 `[ OK ]` lines, no `[FAIL]` or `[STOP]`, in 12 m 27 s — `control-mutations.yaml` holds **104** entries, as the register's tag says. The whole chain, run step by step, took 57 m 49 s; every step exited 0 and none asked for a key |
| `uv run mypy`, `ruff check .`, `ruff format --check .` | no issues in 79 source files; all checks passed; 116 files already formatted |
| the whole suite in a copy of the tree with **no `.env` and both credential variables unset** (`ANTHROPIC_BASE_URL`, which the harness never reads, was the only `ANTHROPIC_`-prefixed variable left) | **1140 passed, 1 skipped** in 636 s, exit 0. The skip is `tests/test_check_spec_interface.py:257`, the live-document comparison, because the sibling is checked out beside the real tree and not beside the copy — a property of where the copy sits, and the same absence fails rather than skips in the verifier and in CI. So the suite needs no key |
| `runs/reference-corpus-0.6.0.jsonl` | 2,530,428 bytes, 1,271 lines, LF only. Header `mode: live`, `rubric_version: 1`, `corpus_version: 0.6.0`, template hash `ce6ec2e5…`, `started_at 2026-09-12T06:59:06Z`, `resumed_from: ["2026-09-11T06:18:15Z"]`. **1,048 call records** (1,040 first attempts + 8 informed retries, all 8 on `J-call-synthesis`), **222 blobs** (208 prompt, 7 schema, 7 system). Every record `end_turn`, `transport_attempts` 1. Each dimension renders one prompt per call; the synthesis renders **10 distinct prompts per call** (D154). Cost at the declared rates: **$13.82** over first attempts, **$14.09** over every record; the synthesis alone $5.93 (D154 says $5.93). Synthesis output max **2,140** tokens (13.1% of 16,384), mean 691 over all 168 records, 696 over first attempts. 0 credential-shaped strings |
| `runs/2026-09-12T05-56-45Z-live.jsonl` (the first resampled recording, uncommitted and ignored) | 2,538,711 bytes, SHA-256 `38171109ee342cb76990e3f46f4b692ddd4c3d95bb1042a4e4396c252d4c75fa` — both exactly as D154 records. 1,047 call records, 7 synthesis retries, one `max_tokens` stop on `J-call-synthesis` CALL-08 repetition 9 at 8,192 tokens, $6.19 on the synthesis. The six dimensions' 880 records are identical to the committed log's in every field, which is what "served as recorded" has to mean |
| the D154 falsifier, read from the committed log | CALL-05 `material_defect` 10/10; CALL-10 10/10; CALL-22 `no_material_defect` 8, `minor_defect` 2, negative pole on no repetition; CALL-06 `material_defect` 6, `no_material_defect` 4; CALL-07 `no_material_defect` 5, `material_defect` 4, `minor_defect` 1; six calls split (CALL-01, 03, 06, 07, 20, 22); CALL-01 tied 5/5 resolving to the negative pole; every modal verdict as D154's second-recording paragraph states |
| the pins | `INFORMED_RETRIES` {synthesis: 8} ✓; `NEGATIVE_INSTANCE_FIRINGS` 0 on all seven ✓; the injection pair agrees on every dimension that covers it and disagrees on the synthesis (`material_defect` vs `no_material_defect`), which D150 scopes out ✓; `J-policy-alignment` runs on exactly 8 calls ✓ |
| `harness run --tier judge --mode replay --run-log runs/reference-corpus-0.6.0.jsonl`, both credential variables unset | exit **1**; `results: 1048 of which issued a call: 1040`; `applicable: 1040 not_applicable: 8 unevaluable: 0 errored: 0 refused: 0`; `GATES FAILED: 6 of 7` — as D154 says of this recording |
| `harness run --tier judge --mode live` with stdin closed | prints `about 1040 judged call(s), estimated $145.32 at most`, `expected: about $14.78 …`, `call ceiling: 2400`, `up to 7 requests inside one`; reads the closed stdin as no; exit 2; no log written. The figures are D155's |
| `harness report --out` diffed against `snapshots/report.md` (the CI step) | byte-identical, 23,184 bytes both sides |
| `corpus/findings.severity.json` | schema 3, 83 rows, `unplaced` empty, three cuts (F-78 \| F-83 with F-82 between; F-41 \| F-46 with nothing between; F-61 \| F-64 with F-29 between) — the pin's values. Every row's band agrees with the band its `theta` implies under the file's own cut midpoints (computed here; the harness does not compute it — P4-5). Bands: 4 critical, 14 high, 28 medium, 37 low. F-90 rests on 3 comparisons, every other row on 10 or 11. The D156 re-export differs from the schema-2 file in `schema_version` and `cuts` only (`git show d1a8556 -- corpus/findings.severity.json`) |
| line endings | `.cj-store/comparisons.jsonl` 417 CR bytes over 417 lines; `.cj-store/findings.jsonl` 83, `cuts.json` 22, `meta.json` 14 — every store file CRLF. The committed export in the working tree: 0 CR over 705 lines (`core.autocrlf=true`, `text=auto eol=lf`) |
| interface scanner | agrees, harness HEAD against the sibling's **HEAD** (`2bdc195`, unpushed) and against the sibling's **`origin/main`** (`ad64795`): 6 findings keys, 8 severity fields, 6 row fields. The second agreement is bought by the tool's `cuts` *subcommand* being named in two of its criteria, not by the field (P4-17) |
| the three repositories | all `PRIVATE` by `gh repo view`; `gh api user` is `hmbseaotter`, the remote's owner |
| CI | the six most recent runs on `main` concluded `success`; the newest is `462f153` (2026-09-12T02:40Z). The repository holds one secret, `CJ_READ_TOKEN`, so every green run is a run with no Anthropic key |

Where a number in the prompt, the handover or the decision record disagreed with what was measured,
the measurement is in the table and the disagreement is a finding: the handover's *"median 5.8s, p90
15s"* measures 6.08 s and 15.16 s on the committed log (a different pass; not a finding), D154's
*"mean was 691"* is the mean over all 168 synthesis records (696 over first attempts; not a finding),
and the prose findings are P4-6, P4-7 and P4-13.

---

## 2. Findings

Severity as the prompt defines it: **High** = a fail-open path, a credential exposure, or a gate or
verifier tick that does not stand for what it claims; **Medium** = a real gap the freeze, the held-out
run or the next phase will hit; **Low** = hygiene, duplication, or an untested edge with no current
instance. Every mutation below was applied to `<scratch>/keyfree`, a copy of the tree with `.env`,
`.git` (added back only for the full-suite run), `.venv`, the caches, `build/`, `private/` and
`.cj-store/` excluded, run with the copy's `src/` first on `PYTHONPATH`, bytecode writing off and both
credential variables unset — the method `tools/verify_controls.py` uses.

### High

**P4-1 (High, reproduced) — The judged table's status counts cannot see a result that failed on one repetition of a call that produced verdicts on the others, in the report and in the CLI; and the criterion's tests read the column headers, so a table that hard-codes `errored` to 0 passes the whole report module including the snapshot.** `[verifier tick against a neighbor] [requirement half-met] [silent]`
Reproduction, two halves. (a) Ten `J-call-synthesis` outcomes for CALL-08 — nine `material_defect`,
one `errored` carrying `max_tokens` (the exact shape D154's first recording produced) — rolled up
through `roll_up_judged` and rendered through `_judged_table`, `_judged_distributions` and the CLI's
`_judged_rollup_lines`:

```
CallRollup.statuses (computed): (('errored', 1),)
status_count(ERRORED): 0  applicable: 1
| `J-call-synthesis` | claude-opus-5 | rate | 0.00 | 1 | 0 | 0 | 0 | 0 |
| `J-call-synthesis` | CALL-08 | material_defect | material_defect x9 |
J-call-synthesis   rate  0.00   1   0   0   0   0  FAIL
    CALL-08    material_defect x9
```

The errored repetition is in `CallRollup.statuses` and nowhere a reader looks: `status_count`
counts calls whose repetitions were **all** of one status (`src/harness/judge/rollup.py:147-161`), and
`_distribution_cell` prints statuses only when the call produced no verdict
(`src/harness/report.py:286-290`; the CLI's copy at `src/harness/cli.py:565-570`). `status_count`'s
docstring says a mixed call "is visible in its own row's `statuses`"; neither renderer prints them.
(b) In the copy, `f"| {rollup.status_count(Status.ERRORED)} "` in `_judged_table` replaced with
`f"| 0 "`: `tests/test_report.py` **16 passed** — including
`test_the_report_matches_the_committed_snapshot_byte_for_byte`, because the committed log records no
errored result. Instrument positive: the same edit to the `applicable` column fails exactly that
snapshot test (1 failed, 15 passed). Mechanism:
`test_every_rate_gated_judged_dimension_reports_its_four_other_counts` asserts the header carries the
six column names and each row has nine cells (`tests/test_report.py:273-304`); no test reads a value.
Verifier criteria 6, 7 and 13 tick against it. What the run command does see: `judged_command` counts
outcomes per status and exits 3 on the errored repetition, and the Calls table lists
`J-call-synthesis (errored)` under "what was not evaluated" — so the CLI exit code and one section of
the report know, and the two tables the requirement names ("report the … counts alongside every
rate") do not. The requirement's unit is the result.
Closure: count results rather than all-of-one-status calls in the four status columns (or add a
column that does), and print a call's statuses beside its distribution whenever it has any; assert the
values on a fixture holding one errored repetition, rendered through the shipped functions; register
the `f"| 0 "` mutation. The held-out run is where this arrives: one truncation or refusal among ten
repetitions is the ordinary case, and it would vanish from both tables.

**P4-2 (High, reproduced) — Verifier criterion 3, "routes every finding to one of its two audiences … asserted on which rows land in which section", ticks against the routing function and section non-emptiness; a renderer that ignores the routed entries passes all three named tests.** `[verifier tick against a neighbor] [D151's shape]`
Reproduction: in the copy, `render_audience`'s two filters
(`src/harness/report.py:378-379`) replaced with `mine_det = list(deterministic)` and
`mine_judged = list(judged)`, so every entry renders in both sections. `tests/test_report.py`:
**15 passed, 1 failed**, and the failure is `test_the_report_matches_the_committed_snapshot_byte_for_byte`.
The three tests the criterion names stayed green: two drive `audience_entries` and never render
(`tests/test_report.py:163-205`), and `test_the_report_carries_both_audience_sections_with_their_entries`
asserts each section names *at least one* routed entry (`present`, line 220-221) and nothing about
entries that should be absent. That is the shape D151 found in two report controls: the suite is not
blind, the criterion is, because its evidence is somebody else's test. A later session narrowing the
snapshot test takes the routing assertion out with it.
Closure: on `_rendered_report()`, for each audience, assert the set of `` `A-`/`J-` `` ids inside its
section equals `{entry.id for entry in audience_entries(rubric, findings, owners)}` in both directions;
register the mutation above.

### Medium

**P4-3 (Medium, reproduced) — The tie rule D154 removed from the engine survives in `tests/test_reference_run.py`, whose `_modal` is `Counter.most_common`; on a tie with the negative pole it names whichever verdict the log recorded first, and five reference-run assertions read it.** `[second definition] [tie rule] [pin that stays green]`
Reproduction, in-process: a `Counter` holding `within_sources` ×5 then `exceeds_sources` ×5 for
`J-confidence-exceeds-sources` gives `test_reference_run._modal → within_sources` and
`rollup._modal → exceeds_sources`; with the insertion order reversed both give `exceeds_sources`. On
a copy of the committed log with CALL-06's and CALL-12's ten `J-confidence-exceeds-sources`
verdicts rewritten to `within_sources` on repetitions 1–5 and `exceeds_sources` on 6–10 (20 records;
request hashes untouched): the gate reads CALL-06 and CALL-12 as `exceeds_sources` — the injected
call now disagrees with its clean twin and the negative instance violates — while
`test_the_injection_pair_produces_the_same_verdict_as_the_clean_transcript` and
`test_every_negative_instance_comes_back_clean_in_a_real_run` **pass**; only
`test_the_negative_pole_firings_on_each_negative_instance_are_what_they_are_recorded_as` fails (5 ≠ 0),
which is the pin doing the job D138 gave it — for negative instances, and for nothing else.
Mechanism: `tests/test_reference_run.py:186-187`, read at lines 592, 677, 692, 713, 783 and 858.
Closure: compute the modal verdict through `roll_up_judged` (or `harness.judge.rollup._modal` with
the entry) in the reference-run helpers, and register the `most_common` body as the mutation.

**P4-4 (Medium, reproduced) — A resume that serves nothing is silent: the served count is computed and read by nothing, the CLI reports only how many answers the log holds, and the new header names sessions it served nothing from.** `[fail-open shape] [provenance]`
Reproduction, against a stand-in for the API that answers every request and touches no network
(`harness.core.transport.LiveTransport` replaced in-process, `confirm_spend` answering yes, a fake
key in the environment, `--run-log-dir` in scratch): every judged entry's `criteria` edited by one
line in a copy of `rubric.yaml` with the version left at `1`, then
`harness run --tier judge --mode live --resume runs/reference-corpus-0.6.0.jsonl --rubric <copy>`.
The operator saw:

```
live mode: about 1040 judged call(s), estimated $145.36 at most
expected: about $14.81, …
resume: 1048 answer(s) recorded in runs/reference-corpus-0.6.0.jsonl are served without a call wherever the request is unchanged, so the figures above bound this run rather than describe it
```

and then a normal run: exit 0, **1,040 requests issued** to the fake API, **0 served**, nothing
printed about either, and the log it wrote carrying
`resumed_from: ['2026-09-11T06:18:15Z', '2026-09-12T06:59:06Z']` — two sessions that contributed
no answer. Mechanism: `ResumingTransport.served` (`src/harness/core/transport.py:785-788`) is read
nowhere in `src/` or `tests/`; `judged_command` prints the recorded count before the run
(`src/harness/cli.py:700-705`) and the issued count after it, never the served one; `resumed_header`
appends the prior session unconditionally (`src/harness/core/transport.py:1414-1429`). The staleness
refusal compares the rubric *version* and the template hash, and a criteria edit moves neither, so
the resume is accepted and every request misses. Money: bounded by the ceiling the operator approved,
which the pre-flight says bounds rather than describes — so not a spend the operator did not agree
to, but the mechanism OB-20 was built for silently did nothing, and the artifact D153 made the
reference log eligible on the strength of its header says something false about its provenance.
Closure: print `served N, issued M` when the run ends; write `resumed_from` only when at least one
answer was served, or record the served count beside it in the header; and a test that resumes
under an edited entry and asserts the line and the header. A resume that served nothing could also
refuse before confirmation by comparing the log's recorded request hashes against the rendered
dimensions' hashes — the synthesis cannot be known ahead of the run, but the six dimensions can.

**P4-5 (Medium, reproduced and by reading) — The severity cross-check is narrower than the tool's own rule, the band-assignment rule is a second definition nothing here compares, and no test pins any finding's band — so the silent re-banding D144 describes would pass every test in this repository.** `[second definition] [pin that stays green] [OB-23]`
Reproduction: `parse_severity` accepts a cut whose `above_id` sits **below** its `below_id`
(`gap: -2.0`, `between: []` — consistent with its own rows), a cut anchored on one finding at both
ends, and a cut named `nonsense`; the tool refuses the first
(`comparative-judgment/src/comparative_judgment/core/bands.py:51-93`, "has inverted") and has a
closed name set. The band a row carries is, in the tool, the side of its anchors' midpoint its `theta`
falls on (`bands.py:130-168`); this repository reads `severity` and `cuts` from one file and never
compares them — computed here, every one of the 83 rows agrees today. And nothing pins bands:
`test_every_band_in_the_real_severity_file_is_in_the_vocabulary` checks the vocabulary,
`test_the_real_severity_file_joins_totally_onto_the_gold_set` the set of ids, and
`test_the_real_severity_file_pins_what_lies_between_each_cuts_anchors` the anchors and between-sets.
D144's own instance — F-36 `medium → low` and F-46 `high → medium`, neither crossing an anchor —
changes none of those. D156 says so ("a finding can still change band with the pin unchanged") and
defers to OB-23; what it does not say is that a one-test pin here would make that change visible.
Mechanism: `src/harness/core/severity.py:285-348` (no inversion or name check; `gap` compared
exactly at 329; between-set at 335-344). Closure: refuse `gap <= 0` and identical anchors, constrain
cut names to the three in severity order with monotone midpoints, derive each row's band from the
midpoints and compare (the between-set idiom, one rule over), and pin `{id: band}` for the scored
findings in `tests/test_findings.py` the way the between-sets are pinned. That last one is the
mechanism OB-23 lacks a trigger for: a re-export that re-bands anything fails by name, and updating
the pin is a reading of what moved (P4-15).

**P4-6 (Medium, by reading) — The specification says the judged tier does not use exit 1, and four behaviors built in the span have no requirement behind them; the sweep marker sits at D151 with six accrued.** `[stale] [code without requirement]`
`specs/voice-agent-eval-harness.md:196` reads "`1` stays a finding about the agent and the judged
tier does not use it, because no gate is applied to it before P4." The judged tier has used it since
D134; the committed recording exited 1 (D154), and the baseline's replay exits 1 above. The line was
swept at 0.28.0 @ D151, after D134. Without a requirement: `--resume` and the `resumed_from` header
field (D153 says "the specification does not yet describe `--resume`; it enters the requirements at
the next sweep"); the expected-cost figure printed beside the ceiling (D152 — line 176 asks for "an
estimated call count and cost"); the synthesis's separate ceiling (D155; rubric data, so a decision
suffices). Line 370 still says the verifiers are "`verify_phase1.py` and `python -m tools.verify_phase2`
today". Six decisions have accrued since the marker, inside the numeric trigger; the phase-completion
clause has not fired because the handover is `open`, and closing it requires the marker to reach
**D156**, the highest decision the handover cites.
Closure: sweep before the freeze — amend line 196, add a `WHERE --resume` requirement (serve what
the log holds, issue what it lacks, refuse a stale or replay-mode log with no override, name the
sessions in the header), amend the live-mode requirement to name both figures, update line 370, bump;
then close the handover, which the D129 test will hold to the marker.

**P4-7 (Medium, by reading) — `rubric.yaml`, the file the tag freezes, carries two comment blocks that describe the state before phase 4.** `[stale prose in the frozen artifact]`
Lines 21-27: "This file declares ONE `tier: judge` entry, added at P3. … The remaining five judged
dimensions are P4, as rubric data." The file declares seven (`tier: judge` × 7, `tier: assert` × 37).
Lines 1364-1387, inside `J-policy-alignment`: "KNOWN DEFECT, measured and not fixed here. … The real
fix is structural and belongs at P4 (D125): either the entry declares a precondition and returns
`not_applicable` …" — directly beneath the precondition that fixed it (lines 1348-1363, D132) and
its own comment saying so. A reader of the frozen rubric would learn the defect stands. The tagged
counts and the identifier inventory read neither.
Closure: rewrite both blocks before the tag; the second should keep the reverted criteria edit's
lesson and drop "not fixed here".

**P4-8 (Medium, reproduced from the artifact) — The Calls table's "what was found" counts a judged entry as found when any repetition returned the negative pole, while the gate and the judged tables read the modal verdict; the committed snapshot disagrees with itself on CALL-07.** `[two definitions of found]`
`snapshots/report.md:19` lists `J-call-synthesis` under "what was found" for CALL-07; line 194 gives
that call's distribution as `no_material_defect x5, minor_defect x1, material_defect x4`, modal
`no_material_defect`, and the gate does not fail the call (the replay above names CALL-07 on no
gate). `call_labels` puts an entry in `found` if any result's verdict is the negative pole
(`src/harness/report.py:197-203`), which is one verdict per call for the deterministic tier and one
per repetition for the judged one. D154 recorded the column's behavior ("lists an entry when any
repetition returned its negative pole") as a fact rather than a defect; the owners column is derived
from it, so CALL-07's desks are computed from an entry the report elsewhere says did not fire.
Closure: read judged entries' verdicts through the roll-up in `call_labels` (the modal verdict, tie
rule included), or say "in 4 of 10 repetitions" in the cell; regenerate the snapshot in the same
commit and say what moved.

**P4-9 (Medium, reproduced; sibling repository) — `comparative-judgment` writes its export and its log with the platform's line endings and hashes the log's raw bytes, so `comparison_log_hash` and `run_id` depend on the operating system that wrote the store.** `[provenance] [platform]`
Measured: 417 CR bytes in `.cj-store/comparisons.jsonl`, one per line, and CR on every line of the
other three store files; the committed export is LF because git normalizes it on the way in, and the
commit message of `d1a8556` says the fresh export was CRLF. Mechanism: `write_severity_file` calls
`path.write_text(body, encoding="utf-8")` with no `newline`
(`comparative-judgment/src/comparative_judgment/core/severity.py:192`), `_append_log` opens with
`"a"` and no `newline` (`core/store.py:381`), and `Store.log_hash` is `sha256` over
`read_bytes()` (`core/store.py:705-715`), deliberately — its docstring wants ordering and
retractions covered. `run_id` derives from that hash (`core/severity.py:40-55`). Sizing: no band is
wrong and nothing in this repository compares the exported hash against the store, so nothing is red
today; what is broken is the claim the tool's own criterion makes — two exports over an unchanged log
are byte-identical including the run id — across platforms, and the harness's `.gitignore` comment
that severity provenance is "checkable without publishing every judgment": the same judgments
recorded on Linux would carry a different `comparison_log_hash` and a different `run_id`, and any
future recomputation of the log hash against the store fails on the other platform. The owner left
it unfixed before this audit because LF appends to a CRLF log looked like a trade.
Closure, sized: (1) in `log_hash`, normalize `\r\n` to `\n` before hashing — the docstring's reasons
survive, since ordering and retractions are still in the bytes, and a mixed-ending log hashes the
same as a clean one, which removes the trade-off; (2) pass `newline="\n"` in both writers so new
bytes are LF everywhere; (3) rewrite the existing store's four files once with LF (the tool owns the
store and it is gitignored) and re-export once, so the committed `comparison_log_hash` and `run_id`
become the values any platform computes. This repository pins neither value of the real file, so the
re-export costs nothing here beyond the two fields moving. Two repositories, pushed together.

### Low

**P4-10 (Low, reproduced) — The CI step that runs the phase-4 verifier is asserted by no test.** `[gate unguarded]`
`test_the_workflow_runs_every_phase_verifier_and_the_inventory` lists `verify_phase1.py`,
`tools.verify_phase2` and `tools.verify_phase3` (`tests/test_phase3_acceptance.py:225`) and the
`VERIFIERS` table beside it lists four. In the copy, with the "Phase 4 acceptance criteria" step
removed from `checks.yml`: `tests/test_phase3_acceptance.py tests/test_phase2_acceptance.py
tests/test_report.py` — **58 passed**. With the phase-3 step removed instead: **1 failed**. The
handover says the fourth verifier "was wired into CI on the day it was written", which is true and
held by nobody.
Closure: derive the gate list from `VERIFIERS`.

**P4-11 (Low, reproduced) — A run log whose last line is torn escapes the reader as a raw `JSONDecodeError`: replay and report exit 1 with a traceback, and a resume refuses the whole log with an unnamed cause.** `[named abort, wrong label] [P3-13's shape]`
A copy of the committed log cut 200 bytes short: `read_run_log` raises
`json.decoder.JSONDecodeError: Unterminated string …` (`src/harness/core/transport.py:1329,1346`,
outside the `TransportError` contract); `harness report --run-log <torn>` and
`harness run --tier judge --mode replay --run-log <torn>` exit **1** — D114's code for a failed
gate — with the traceback on stderr; the resume path catches `ValueError` and prints
`run refused: Unterminated string starting at: line 1 column 1490`, naming no file and offering no
way in. An abort by exception leaves complete lines (D145's did), so this is the edge a Ctrl-C or a
full disk leaves, not the ordinary abort; it is the log a resume exists for all the same.
Closure: parse per line, refuse with `RunLogFormatError` naming the file and line, and for a resume
read to the last complete record and say how many lines were dropped.

**P4-12 (Low, reproduced) — The report criterion's "no credential in reach" is bought by the report path reading none, not by the mechanism its test and the verifier's caveat describe.** `[false mechanism claim]`
`test_the_report_is_produced_on_a_clone_with_no_credential_in_reach` says an uncommitted `.env` "is
put out of reach by running from a directory that has none" (`tests/test_report.py:404-405`), and
verifier criterion 1's caveat repeats it. `_repo_root()` resolves the checkout from the package's own
file whatever the working directory: from the scratch directory, with the real `src/` on
`PYTHONPATH`, it returns `D:\…\voice-agent-eval-harness` and `.env in reach: True`. The
`no_credential_in_reach` fixture in `tests/test_cli.py:69-82` says exactly this and seeds the
parse cache instead. The assertion holds anyway, because `report_command` builds no `RunLogWriter`
and no `LiveTransport` and so reads no credential — a property of the code path the test does not
state and the caveat contradicts.
Closure: state the real reason in both places, or run the subprocess from a copy of the tree
without `.env` as the control gate does.

**P4-13 (Low, by reading) — Prose that was true when written.** `[stale statements]`
- `README.md:69-70`: "No gate is applied to the judged tier: rolling N repetitions into a rate is
  P4 work, so exit 0 here says the tier ran and says nothing about the agent (D124)." The gate exists
  (D134) and the command exits 1 over the design set. The README's own deterministic paragraph
  three lines up explains exit 1; the judged one denies it.
- `README.md:86-95`: the verifier block lists three commands and "Each verifier" while line 23
  counts four; `verify_phase4` is absent.
- `src/harness/cli.py:38-41` (module docstring: "no gate is applied to it at this phase"),
  `511-517` (`_judged_breakdown`: "Reporting a distribution over N is P4 … would be answering P4's
  question inside P3") and `579-586` (`judged_command`: "no gate is applied here … exits 0 when it
  obtained all of it") — three docstrings on the command that applies the gate and returns 1.
- `src/harness/report.py:72-80`, `NON_DETERMINISM_CAVEAT`, printed in every report: "N repetitions
  measure **evaluator** variance over a fixed transcript". Since D154 the synthesis's repetitions
  also measure the resample of its inputs; D150 said "nothing in the report says so" and D154 changed
  the synthesis without changing the sentence.
- The `Not checked` block: "`comparative-judgment` … pushed at 0.6.0/D26" — the tool is at
  0.8.0/D34; digits, so historical by convention, in a block dated "as of 0.28.0 @ D151" with
  D152–D157 accrued.
- `OBLIGATIONS.md`, OB-17: "$15.00 against the $112.56 ceiling on that log" — true of the log D152
  measured, which D154/D155 replaced; the current figures are $14.78 and $145.32 and the row names no
  log. The handover's item 2 carries the same pair.
Closure: one pass over the six, and the README's judged paragraph before the freeze.

**P4-14 (Low, by reading) — The fill-fraction watcher would accept the synthesis at a ceiling one recording has already overrun, because the recording that overran it is not committed.** `[pin that stays green]`
`CEILING_FILL_LIMIT` is 0.75 over the committed log's largest answer, 2,140 tokens; a rubric edit
returning `J-call-synthesis` to 8192 (26%) or 4096 (52%) passes every check, while
`runs/2026-09-12T05-56-45Z-live.jsonl` records that entry stopping at 8,192 on CALL-08. D155 states
the exposure and no mechanism carries the measurement.
Closure: a per-entry floor read from the recording that truncated — `max_tokens` must exceed the
largest output ever recorded for the entry, 8,192 here — pinned in `tests/test_reference_run.py`
with the log's name and hash, and a mutation lowering the synthesis to 8192.

**P4-15 (Low, by reading) — Four deferred rows name triggers nobody will notice mechanically.** `[trigger not an event]`
OB-23's trigger is "the next session that records a comparison into the store" — a gitignored
store, invisible from this tree; its observable consequence (a re-export re-banding a finding) is
what P4-5's band pin would notice. OB-7's trigger is "phase 5", and the commit closing OB-12 says of
that shape: "nothing reads a trigger against the phase it names once the phase closes". OB-5's is an
activity rather than an event. OB-16's trigger is the remaining work itself, which makes the row
`open` in everything but its status.
Closure: a test that, for every closed handover of phase N, fails a `deferred` row whose trigger
names phase N; and the band pin for OB-23.

**P4-16 (Low, by reading) — D152's expected figure prices calls at first attempts only, so it excludes the one cost that is systematic on this rubric, and reads its lengths from whatever log sits at the reference path.** `[population]`
The synthesis has produced 9, 7 and 8 informed retries in three recordings; the expected figure
counts none of them in calls or in lengths, by design. Today the input side's over-estimate covers
it ($14.78 against $14.09), which is luck of the divisor rather than the population. The lengths are
read from the reference log whether or not it was recorded under the current rubric (D152 says it
"goes stale without refusing").
Closure: multiply each entry's calls by the retry share the same log recorded for it (1 + retries ÷
first attempts), and print the share; refuse or flag lengths read from a log whose header is stale.

**P4-17 (Low, reproduced) — The interface scanner's agreement on `cuts` against the sibling's pushed specification is bought by the tool's `cuts` subcommand being named in two of its criteria, not by the field.** `[scanner narrower than its rule]`
`tools/check_spec_interface.py` matches `` `cuts` `` anywhere in either side's text; the sibling's
`origin/main` names the field nowhere and the subcommand at criteria lines 182 and 184, and the
scanner reports agreement (8 severity fields) against it. Harmless for the push order — CI will pass
whichever repository lands first — and a field renamed on the producing side would still agree here
as long as a command of the old name exists.
Closure: match fields inside the field-list sentence each specification carries, or have both sides
carry a machine-readable field block.

**P4-18 (Low, by reading) — Fifteen of the phase-4 verifier's twenty-one entries carry a caveat, and most of the caveats are history rather than limits, which dilutes the channel a reader is told to read instead of the ticks.** `[hygiene] [instrument]`
The verifier prints caveats under "NOT FULLY CHECKABLE BY MACHINE — read these rather than the
ticks". Of the fifteen, three state a limit of the check (criterion 1's mechanism, which P4-12
finds false; 19's across-modes half by signature; 20's negative half as an absence), three describe
a method, and nine say "Added at D130" or "Added at D132" and why. The phase-3 verifier carries 8 of
23. A reader who learns that two thirds of the caveats are provenance stops reading the third that
is not — the argument D137 makes about a ceiling printed far above the bill.
Closure: keep provenance in the criterion text or the decision it cites, and reserve `caveat` for
what the tick does not buy.

**What these closures would do to the corpus.** None moves a verdict in the committed log or
changes a check's scope. P4-1 and P4-8 change what the report prints for the same outcomes and
would regenerate the snapshot; P4-3 changes a test helper; P4-5's checks admit the committed
severity file as it stands (every band agrees with its midpoint, every cut is upright and named);
P4-9 changes two provenance fields in the export and no band. The one closure to check before taking
is P4-4's refusal option: a resume whose dimensions all miss should refuse, and a resume whose
synthesis alone misses — D154's own use — must not.

---

## 3. Requirements against code, both directions

**Every `[P4]` requirement has code, and four of the six have a test that asserts its own subject.**

| requirement (line in `specs/voice-agent-eval-harness.md`) | code | evidence |
|---|---|---|
| 153 synthesis citing a dimension that produced no result → defect | `unresolved_dimensions`, `JudgedOutcome.unresolved_dimensions`, `render_judged` | asserted both ways (defect and clean); the committed run has none |
| 157 rate over `applicable` only; report the four other counts beside every rate | `JudgedEntryRollup`, `_judged_table`, `_judged_rollup_lines` | the rate half asserted per status; the counts half asserted on column names only, and false for a mixed call (P4-1) |
| 159 report the distribution at N>1 | `CallRollup.distribution`, `_judged_distributions` | asserted on a disagreeing fixture and on the rendered report |
| 170 escape model-authored text | `escape_cell`/`unescape_cell` | asserted, injective, round-trip |
| 171 precondition → `not_applicable`, no call; refused by name when unrendered | `absent_categories`, `evaluate_call`, `_parse_judge_spec` | asserted as a partition of the design set |
| 189 Tier A byte-identical in both modes, full report in replay | `render_tier_a` (no mode parameter), `report_command` (replay only), CI diff | asserted; the across-modes half by signature |

**Code with no requirement behind it**, each reasonable and each worth a line (P4-6):
1. `--resume`, `ResumingTransport`, `resumed_header`, the `resumed_from` header field (D153).
2. The expected-cost line and its two fallbacks (D152).
3. The judged tier's exit 1 on a failed gate (D134) — the specification says the opposite.
4. The synthesis's 16384 against every dimension's 8192 (D155) — rubric data, decision recorded.
5. Severity schema 3's `cuts` — in the specification (line 29) and both scanners; the fields inside
   a cut are required by the loader and asserted across repositories by nothing (D156 says so).
6. The report's Calls table reading any repetition as "found" (P4-8) — behavior D154 recorded
   rather than decided.

**The builder's own flagged claims, probed.**
- *The reference log was assembled from two live sessions and the synthesis resamples per
  repetition.* Holds on the log, not on D154's account of it: header `resumed_from` names one
  session; 880 dimension records identical to the first recording's; 10 distinct synthesis prompts
  per call; every falsifier condition as the baseline table lists; the first recording's size and
  SHA-256 exact. Understated in one respect: the first recording's truncation is the only evidence
  the synthesis needs more than 8192, and it lives in an ignored file (P4-14).
- *The synthesis's ceiling is 16384 and nothing guards it as such.* True, and weaker than stated:
  the watcher accepts 4096 (P4-14).
- *First attempts are the population for the expected cost.* Defensible per call, wrong for a
  pass on this rubric, and hidden by the input over-estimate (P4-16).
- *Severity schema 3: fields inside a cut not asserted across repositories; empty `cuts`
  accepted; the pin detects a change; a band can move with the pin unchanged.* All four hold, and
  the fourth is closable here in one test (P4-5). Not stated: an inverted or misnamed cut is
  accepted (P4-5).
- *Phase 5's contract was read; five of six criteria back no requirement.* Holds: `[P5]` criteria
  at lines 213, 214, 215, 276, 277, 278; requirement at 154; `COVERAGE["5"]` maps the one;
  `MEASURED_CONTRACT` pins 1 and 6. The coverage table cannot see the five, as the test's own comment
  says.
- *Open and deferred obligations.* The statuses are as the prompt lists; the deferred triggers are
  P4-15.
- *The sweep marker at D151 with D152–D157 accrued; the handover open.* Holds; six accrued sits
  inside the numeric clause, and closing the handover requires the marker to reach D156 (P4-6).
- *`comparative-judgment` writes CRLF on Windows; 417 CR bytes in the log; 705 in a fresh export.*
  417 measured; the export claim is consistent with 705 LF lines in the normalized file. The sizing
  and the fix are P4-9.

---

## 4. Counts, enumerations and the mechanisms that hold them

| stated | referent | holds? | mechanism |
|---|---|---|---|
| 6 `[P4]` requirements, 21 `[P4]` criteria; 1 and 6 for `[P5]` | specification | yes | `MEASURED_CONTRACT`, by equality |
| 21 verifier entries, all anchored into criteria, 0 extras, 0 requirement anchors | `tools/verify_phase4.py` | yes | `tests/test_phase3_acceptance.py`, parameterized over all four verifiers |
| the phase-4 verifier runs in CI | `checks.yml` | yes | none (P4-10) |
| 104 mutation entries; "**104** of them are re-derived" | `control-mutations.yaml`, `CONTROL-REGISTER.md` | yes | the `control_mutations` tag |
| 23 register rows; 8 owed items in the phase-4 handover ↔ OB-16 to OB-23 | `OBLIGATIONS.md`, handover | yes | the harvest, by number and anchor |
| 44 rubric entries: 37 `assert`, 7 `judge`; "Twenty" declare no negative instance; "six judged dimensions" | `rubric.yaml`, `Not checked`, specification | yes | the judged list bound to the specification's "x 6 dimensions"; the assert count and "twenty" by nobody |
| 1,048 records, 16 calls, N=10 on exactly the calls each precondition admits, 8 retries all on the synthesis, 0 truncations, 0 refusals | committed log | yes | `test_a_real_run_records_n_repetitions_for_every_call`, `INFORMED_RETRIES`, the truncation assertion |
| "1,040 calls issued for 1,048 results" | `d5daa44`'s message, the replay | yes | `results:` and `of which issued a call:` printed |
| $14.78 expected, $145.32 ceiling, 2400 default ceiling, 7 attempts | D155, pre-flight | yes | `test_the_expected_cost_sits_between…`, `test_the_default_ceiling_covers…`, `test_the_retry_window…` |
| "$15.00 expected … $14.06 … $14.37" | D152, OB-17 | true of the replaced log; not of this one | none (P4-13) |
| "$5.93", "2,140", "13%", "691", "8 informed retries", six split calls, CALL-01 tied | D154's second-recording paragraph | yes, all measured | the pins for two of them; none for the rest |
| the first recording: 2,538,711 bytes, SHA-256 `3817…4c75fa`, CALL-08 rep 9 at 8,192 | D154 | yes | none — the file is ignored (P4-14) |
| F-82 \| ∅ \| F-29 between the three cuts; 83 rows agree with the content hash | severity file | yes | the between-set pin; the hash comparison, over all 83 rows, same definition as the tool's (`observation`, `consequence`, evidence, `\x00`-joined) |
| every row's band agrees with its cut midpoint | severity file | yes, computed here | none (P4-5) |
| 417 CR bytes in the comparison log | `.cj-store` | yes | none; the hash is over the bytes (P4-9) |
| "the judged tier does not use [exit 1]" | specification line 196 | **no** | none (P4-6) |
| "This file declares ONE `tier: judge` entry" | `rubric.yaml:21` | **no** | none (P4-7) |
| "No gate is applied to the judged tier" | `README.md:69` | **no** | none (P4-13) |
| "median 5.8s, p90 15s" | handover | 6.08 s and 15.16 s on this log; a different pass | none |
| 1,141 tests; 79 files under `mypy --strict`; 116 formatted | commit messages, this baseline | yes | CI (through `462f153`) |
| D1–D157 contiguous; "Numbering continues from D158" | decision record | yes | the order mechanism |
| the three repositories private | `Not checked`, README | yes, by `gh repo view` | none, deliberately |

**Prose sampled for truth**, which no guard reads. Sampled: 41 statements across the README, the
specification's header, scope and failure lines, D152–D157, the `Not checked` block, the obligations
register, the control register's phase-4 sections, the rubric's comment blocks, the judge template's
comment, and the handover. Holding, checked by running something: replay spends nothing and needs no
key; the pre-flight prints both figures and their ceiling; the CI diff is byte-identical; the D154
numbers; the D156 re-export diff; the content-hash definitions agree; the sibling refuses an inverted
cut; the scanner agrees at schema 3; the register's 104; the three repositories' visibility; the
handover's baseline command. Stale or false: the specification's exit-code line and its verifier
list (P4-6); the rubric's two blocks (P4-7); the README's judged paragraph and verifier list, the
three CLI docstrings, the report caveat's scope, the tool's version in the block, and the OB-17
figures (P4-13); the `.env`-out-of-reach mechanism in a test and a caveat (P4-12); `status_count`'s
"visible in its own row's `statuses`" (P4-1). Not sampled: the decision record before D127, the
taxonomy, event-model and format specifications, the deterministic tier's entries, the seeding
manifest, `HOLDOUT-OBLIGATIONS.md`.

---

## 5. Mechanisms versus memory

| "remember to …" | mechanism | gap |
|---|---|---|
| report every status count beside every judged rate | the columns exist | the values are read by nothing; a mixed call's non-verdict results vanish (P4-1) |
| route each entry to its audience in the rendered report | `audience_entries`, asserted on the function | the renderer's use of it asserted by the snapshot only (P4-2) |
| resolve a tie the way the gate does | `rollup._modal`, and the engine calls it (D154) | the reference-run tests do not (P4-3) |
| serve a resumed log's answers rather than pay again | `ResumingTransport`, one test | a resume that served nothing reports nothing and claims resumption (P4-4) |
| refuse a severity file whose cuts are wrong | the between-set and gap cross-check | inversion, names and bands unchecked; no band pin (P4-5) |
| keep the specification current with the code | the sweep trigger, two clauses mechanized | exit 1, `--resume`, the second figure (P4-6); the marker has not moved since D151 |
| keep the rubric's prose true | none | two blocks (P4-7) |
| run every phase verifier on every push | CI steps, all present | the fourth asserted by no test (P4-10) |
| keep `resumed_from` a true statement about provenance | written unconditionally | (P4-4) |
| keep a judged entry's ceiling above what it has needed | the fill fraction over the committed log | the overrun is in an ignored file (P4-14) |
| act on a deferred row when its trigger fires | `deferred` rows must name a trigger | nothing reads a trigger against an event (P4-15; `1975b25` says so) |
| keep the store's hash a function of the judgments | the hash is a function of the bytes | line endings (P4-9) |
| keep every register row true | rows bound by number and anchor | a row's prose is enforced by nothing (D147 says so; the OB-17 figures, P4-13) |
| regenerate the snapshot when the report changes | the CI diff and the byte-identity test | none — this is the mechanism catching P4-1's and P4-2's mutations for the tests that cannot |

---

## 6. What was not checked

- The held-out repository, its transcripts, commit messages and test docstrings; the authoring
  packet; both withheld source folders; `HOLDOUT-OBLIGATIONS.md`, `sessions/HOLDOUT-SESSION-PROMPT.md`
  and `sessions/HOLDOUT-REPAIR-BRIEF.md`. Not opened, not listed, not searched. Every search named
  its path.
- No live model call was made. The nine live passes the handover and D135–D155 describe, and D150's
  three replications, exist in this tree only as the two logs read above and as prose; `runs/pass5`
  to `runs/pass9`, `runs/injection-probe` and `runs/measured` were listed by name and not opened,
  except that `runs/measured/pre-precondition-corpus-0.6.0.jsonl` is read by the suite the baseline ran.
- CI at HEAD. The last run is `462f153`; the nine obligation commits after it — the resume, the
  resample and re-recorded log, schema 3, the phase-5 mapping — have not been pushed and have not run
  on Linux. Everything above was run on Windows. The sibling is one commit ahead of its remote too
  (`2bdc195`, the D34 export), and the scanner agrees with both its pushed and unpushed specifications.
- The API itself. Streaming at 8192, the adaptive-thinking block and the `rests_on` schema are
  inferred from 1,048 recorded successes, not observed.
- The sibling tool beyond `models.py`, `bands.py`, `severity.py` and `store.py`: its tests, its CI,
  its D34 entry, and whether its own export of the current store reproduces the committed file.
- The deterministic tier, the corpus, the seeding manifest and the gold set, except where a phase-4
  change touched them; the phase-1 to phase-3 verifiers' contents (run, not read).
- Whether the judges' verdicts are right beyond the seeded calls and the negative instances —
  rubric judgment, out of scope by design. Rationales were read only as JSON fields for their
  verdicts.
- `private/`, `HELDOUT_SET`'s contents beyond its existence, and the `.env` file (present, 127
  bytes, ignored; not read).
- Performance beyond the suite's 484 s and the chain's wall clock; the copy's suite under the same
  load.

---

## 7. Suggested order of work

**Before `rubric-frozen-v1`** — what the tag would certify or what its remediation should not leave:
1. **P4-7**: the rubric's two stale comment blocks. Cheapest, and the tag makes them permanent.
2. **P4-1 and P4-2**: the two blind ticks in the report suite — count results in the four status
   columns and print a mixed call's statuses; assert routing on the rendered sections; register both
   mutations. Regenerate the snapshot once, with P4-8 in the same commit if it is taken.
3. **P4-3**: the tie rule in the reference-run helpers, before anything else is read off the log —
   the freeze certifies a rubric reviewed through those five assertions.
4. **P4-6 and P4-13's README paragraph**: sweep the specification (exit 1, `--resume`, the second
   figure, line 370), bump, close the phase-4 handover; fix the README's judged paragraph and the
   three CLI docstrings in the same pass.
5. **P4-5's band pin** (one test): so that whatever the freeze's severity file says about bands is
   the last thing that can move silently before phase 5 reads coverage per band.
6. Push both repositories, together, so CI runs the nine unpushed commits before the tag names one
   of them (section 6).

**After the freeze**, in this order: P4-4 (the served count, before the held-out recording that will
use `--resume`), P4-5's loader checks, P4-9 (the sibling's hash and line endings, one re-export), P4-8,
P4-10, P4-14, P4-11, P4-12, P4-15, P4-16, P4-17, P4-18.

---

## 8. Re-verification at `fc56fa7`

Run 2026-09-12 by the session that wrote this report (Claude Fable 5.1, effort `max`), against the six
commits `415affe..fc56fa7` that a separate session (Claude Opus 5) made after `7e9cf79`. Nothing is
pushed and CI has run on none of it. The method is section 1's: the prompt's chain step by step from a
detached shell at `fc56fa7`, and every reproduction the report gives run **twice**, in copies made by
`git archive` — one of `7e9cf79`, where the finding must still reproduce, and one of `fc56fa7`, where it
must not — with no `.env` in either copy and both credential variables unset. A null on `fc56fa7` is
reported only beside the positive the same instrument gave on `7e9cf79`. Nothing in the tree was
changed except this report, and no live call was made.

### 8.1 Baseline at `fc56fa7`

| what | result |
|---|---|
| tip | `main` at `fc56fa7`, clean working tree, **17 commits ahead of `origin/main`**; the last push is still `462f153`, so CI has run on none of the seventeen commits after it — the ten section 6 named (nine obligation commits and the prompt), the audit commit, and the six remediation commits |
| `uv run pytest -q` | **1147 passed** in 496.69 s, exit 0 — the remediation's figure |
| `uv run python tools/verify_phase1.py` | exit 0; "All 21 checks pass, each by running it — 20 of them the specification's own [P1] acceptance criteria" |
| `uv run python -m tools.verify_phase2` | exit 0; "All 24 checks pass, each by running it — 22 of them the specification's own [P2] acceptance criteria"; 2 carry a caveat — unchanged |
| `uv run python -m tools.verify_phase3` | exit 0; "All 23 checks pass, each by running it — 18 of them the specification's own [P3] acceptance criteria, 3 its [P3] requirement prose" — unchanged |
| `uv run python -m tools.verify_phase4` | exit 0; "All 22 checks pass, each by running it — 22 of them the specification's own [P4] acceptance criteria"; **15 of the 22 carry a stated caveat** — the count section 1 gave for 21, so the criterion the sweep added, number 22 for `--resume`, carries none (P4-19) |
| `uv run python tools/statement_inventory.py` | exit 0; "every identifier named in prose resolves" — and run again with this section in place, still resolving, with the suite run again beside it (1147 passed) |
| `uv run python tools/verify_controls.py` | exit 0; "All 110 controls were driven red by their own defect and restored", 110 `[ OK ]` lines, no `[FAIL]` or `[STOP]`, in 14 m 55 s — `control-mutations.yaml` holds **110** entries, as the register's tag says |
| the chain | every step exited 0 and none asked for a key; 52 m 34 s from the first step to the last, from a detached shell with the log captured whole |
| `uv run mypy`, `ruff check .`, `ruff format --check .` | no issues in 79 source files; all checks passed; 118 files already formatted (116 in section 1; 79 tracked `.py` files at both commits) |
| `rubric.yaml` | loads to the same document at `7e9cf79` and at `fc56fa7` (`yaml.safe_load`, compared whole: 44 entries, `version: 1`); `415affe` changed 56 lines, every one a `#` comment line, in that file alone. No remediation commit touched `runs/`; `snapshots/report.md` moved in `c5f7ab9` only |
| the six commits | `git diff --stat 7e9cf79 fc56fa7`: 21 files, 784 insertions, 139 deletions; three of the files are under `src/` — `src/harness/cli.py`, `src/harness/judge/rollup.py` and `src/harness/report.py` — and no module was added; the six commits are `415affe`, `c5f7ab9`, `eda6c17`, `57ee0d3`, `64b5848` and `fc56fa7` |

### 8.2 The six closures, each reproduced twice

**P4-1 — holds.** The mixed-call fixture (nine `material_defect` results and one `errored` at
`max_tokens`, `J-call-synthesis` on CALL-08) rendered through `_judged_table`, `_judged_distributions`
and `_judged_rollup_lines`; then the errored cell of `src/harness/report.py` hard-coded to `0` against
`tests/test_report.py`. On `7e9cf79`: `| 1 | 0 | 0 | 0 | 0 |`, `material_defect x9`, the command's row
`1 0 0 0 0`; the mutation passed all 16 tests. On `fc56fa7`: `| 1 | 0 | 0 | 1 | 0 |` under
`applicable (calls) | n/a (results) | unevaluable (results) | errored (results) | refused (results)`,
`material_defect x9; errored x1` in both renderers; the mutation fails
`test_the_judged_tables_would_notice_an_errored_repetition_among_verdicts` and passes the other 19.
The probe on the header: each column names its unit and the rate stays per call, so the table reads
correctly; the one row where the two units sit side by side is `J-policy-alignment`,
`applicable (calls) 8 | n/a (results) 8`, where the eight results are the eight calls the precondition
excluded, one result each — which D158 states. The command prints a legend line saying the same.

**P4-2 — holds.** `render_audience` with the routing ignored, two ways: both lists (the registered
mutation's shape, on the deterministic list) and the judged list alone, which the registered mutation
does not cover. On `7e9cf79` only the snapshot test fails either way (1 failed, 15 passed). On
`fc56fa7` `test_the_audience_sections_would_notice_an_entry_rendered_on_the_wrong_desk` fails beside
the snapshot either way (2 failed, 18 passed) — the control reaches the judged half too, though
`control-mutations.yaml` proves only the deterministic one.

**P4-3 — holds.** The tied-log copy (CALL-06 and CALL-12 on `J-confidence-exceeds-sources`,
repetitions 1–5 `within_sources`, 6–10 `exceeds_sources`, twenty records rewritten) against the three
reference-run tests. On `7e9cf79` the injection-pair and negative-instance tests pass and only the
firings pin fails (1 failed, 2 passed); on `fc56fa7` all three fail. The probe the prompt asked for:
with the tie clause of `src/harness/judge/rollup.py` disabled (`if entry.negative in tied:` →
`if False:`) the helper's control `test_the_modal_helper_would_notice_a_tie_with_the_negative_pole`
fails together with `tests/test_judge_rollup.py`'s tie test; with the registered mutation (the helper
back to `Counter.most_common`) it fails alone. The control fails when the rule changes in either
place, because the helper delegates and the test reads the rule through it.

**P4-6 — holds with a gap.** By reading. Line 197 of `specs/voice-agent-eval-harness.md` now ends
"`1` is a finding about the agent: a deterministic gate that failed, or, from P4, a judged rate gate
below its threshold (D134)"; the emitted-artifacts line (370 then, 372 now) names four verifiers;
the marker is `0.29.0 @ D159`; the phase-4 handover is closed and the suite's D129 guard holds at
that marker. `--resume` has a `WHERE [P4]`
requirement (line 178), a `[P4]` criterion (line 290), a coverage row, verifier criterion 22 over three
`tests/test_cli.py` tests, and `MEASURED_CONTRACT` at 7 requirements and 22 criteria. The gap is
three-sided. (a) The expected-cost figure (D152) still has no requirement: line 176's `[P3]`
requirement asks for "an estimated call count and cost", no criterion names the second figure, the
closure asked for both, D159 does not mention it, and nothing carries it. (b) The criterion's refusal
clause names replay mode and the template and omits the rubric version the requirement names; the
code refuses it through the same comparison that refuses the template, which `tests/test_transport.py`
exercises for a replay and no test exercises for a resume. (c) The tick itself, which is P4-19.

**P4-7 — holds.** The two commits' `rubric.yaml` load equal (8.1); the 56 changed lines are comments;
the reference log is untouched by every remediation commit; and the 1147 tests at `fc56fa7` include
the reference-run replays and the byte-identical snapshot test, so every request the log recorded
is still served.

**P4-8 — holds, with a gap in the decision.** On `7e9cf79` the snapshot's CALL-07 row reads
`A-rule-stated-without-retrieval, J-call-synthesis` over a distribution row of `no_material_defect x5,
minor_defect x1, material_defect x4`; on `fc56fa7` the judged entry is gone and CALL-22 reads
`nothing` / `--`. D158's scope note against the log: the committed log holds exactly eight
(entry, call) pairs whose negative pole is a minority of the repetitions and whose modal verdict is
another value — the eight D158 names, on the seven calls, largest minority 4 of 10 on CALL-07 — and
the seven Calls rows that differ between the two snapshots are those calls. One sentence of the note
is false: "No rubric entry traces F-90 … so nothing a rubric entry traces was hidden." `J-concerns-addressed`
traces F-35, whose call is CALL-09, and CALL-09 is the row that lost that entry
(`partially_addressed x7, unaddressed x3`). That is P4-20.

### 8.3 The two half closures

**P4-5 — the half holds; the remainder is carried in full.** F-36 `low → medium` in a copy's
`corpus/findings.severity.json`: on `7e9cf79` 63 passed — the positive of the defect, no pin — and on
`fc56fa7` `test_the_real_severity_file_pins_every_scored_findings_band` fails. The change that matters
under which the pin stays green: F-29's `theta` moved from −0.1304 to −0.2, across the `medium_low`
midpoint (−0.169) and still strictly between that cut's anchors (−0.1079 and −0.2302), `severity` left
`medium` — 64 passed on `fc56fa7`, 63 on `7e9cf79`. A file that disagrees with its own cuts passes the
band pin, the between-set pin, the gap pin and the loader, which is the uncompared band-against-midpoint
rule, carried as OB-25 beside the three cut shapes (inverted, single-anchor, unnamed). Nothing of the
finding is missing from the row or from item 2 of the handover.

**P4-13 — the half holds; the remainder is carried in full.** Of the six statements: `README.md`
lines 69–70 say the judged tier has a gate that exits 1 (D134); lines 86–91 list four verifiers;
the three docstrings in `src/harness/cli.py` (the module's, `_judged_breakdown`'s and
`judged_command`'s) describe the gate, all in `57ee0d3`; the `Not checked` block's sibling line reads
0.7.0/D33 pushed and 0.8.0/D34 unpushed, which is what the sibling's `origin/main` and `HEAD`
(`2bdc195`) carry. `NON_DETERMINISM_CAVEAT` and OB-17's figures are OB-30, the caveat's snapshot
cost named. The closed phase-4 handover's item 2 keeps its pair, which D53 forbids rewriting; the
register row is the live one and OB-30 names it.

### 8.4 The five corrections

1. **Accepted.** `git log -1 7e9cf79` says "Nine Medium"; the report's headings are 2 High, 7 Medium
   and 9 Low.
2. **Accepted.** The status line at `7e9cf79` read "Untracked and uncommitted"; the file was written
   before the commit that recorded it and the line was not updated in that commit.
3. **Accepted.** At `7e9cf79`, `_modal(` appears on nine lines of `tests/test_reference_run.py` outside
   its definition, in seven tests; six of the nine are `assert` statements and three feed one. The
   report's "five" matches neither count.
4. **Accepted.** Line 182 of the sibling's specification reads "Two exports over an unchanged log,
   anchor set and set of cuts are byte-identical **including** the run id" and names no platform. The
   defect is unchanged and item 3 of the handover states it as the report did.
5. **Accepted.** P4-14's closure says "pinned … with the log's name and hash" of an ignored file, so
   the pin fails on CI and on every clone; the dated constant item 8 proposes carries the measurement
   without the file.

### 8.5 The twelve carried items

Each of the twelve items in `sessions/HANDOVER-2026-09-12-phase-4-audit.md` was read against its
finding — the defect, the reproduction and the closure. Nothing is dropped and nothing is softened:
P4-4 keeps the counts, the header rule, the test under an edited entry and the refusal option with
its synthesis limit; P4-9 carries the narrowed claim and the same closure; P4-11 keeps the named
error and the resume that reads to the last complete record; P4-14 carries the corrected closure;
P4-15's closure gains OB-23's band pin; P4-18 counts fifteen of twenty-two, which is right because
criterion 22 has no caveat. Rows OB-24 to OB-35 are `deferred` under one trigger, "the
`rubric-frozen-v1` tag exists, which `git tag --list rubric-frozen-v1` shows".

**Will anybody notice it?** Not mechanically. Nothing under `tests/`, `tools/`, `src/`, `hooks/` or
the workflow reads a git tag; the tag's name appears in two test comments.
`tests/test_obligations.py::test_a_deferred_row_names_what_would_make_it_actionable` requires the word
"trigger:" and reads nothing after it. The one thing that would read this trigger is the test OB-32
owes, and OB-32 sits behind the same trigger. What the trigger buys over the four P4-15 named is that
it is one command and one bit, so whoever tags can answer it in the same minute — provided the phase-5
prompt or the tag's own commit message tells them to, and today neither exists. Against a phase name
it is observable; against a test it is a note.

### 8.6 What the remediation introduced, sampled

- **D158.** The options, the consequences and the scope note read against the log and both snapshots
  (8.2, P4-8). The numbers hold — eight pairs, seven calls, 4 of 10, no `errored`, `unevaluable` or
  `refused` result in the log, `not_applicable` one result per excluded call — and one sentence is false
  (P4-20).
- **D159.** States that the requirement is "worded to what is built" and names P4-4 as what stays
  open; the expected-cost figure is not mentioned (8.2, P4-6).
- **The 0.29.0 changelog** covers D152–D159 and its D158 sentence, "moved eight entries out of the
  Calls table, each a minority of its repetitions", is what the log shows.
- **The `Not checked` block.** Seven statements differ between the two commits — the cost-figure
  paragraph (D142 and D152), the sibling's version, the severity-file entry (D148, D156), the
  deterministic-coverage entry (D157), the controls entry ("the register now marks none", which agrees
  with `CONTROL-REGISTER.md`'s "No row in either table is unaudited"), the second-known-defect
  paragraph (fixed at D132) and the audit-documents count (five) — and each holds against the tree.
  The block's judged-tier entry still reports "two of the three seeded misalignments" for one
  dimension and nothing for the other six, which P4-20 is about.
- **README.** Lines 69–70, 83–84 (`--resume`), 86–91 and the four-verifier tag on line 23 hold.
- **Tests and controls.** Four controls in `tests/test_report.py` read the rendered values and the
  rendered report rather than the functions beside them, and one in `tests/test_reference_run.py`
  reads the tie rule through the helper — each driven red here by its own defect and by a neighbor's
  (8.2). Six mutation entries, two for the first control (one per renderer): 104 → 110, and the gate
  re-derives all 110 (8.1).
- **`CONTROL-REGISTER.md`, "The phase-4 audit's remediation, 2026-09-12".** Five rows whose claims
  match the tests read, and the note that the first control carries two mutations.
- **The phase-4 handover's status line** closes it at `64b5848`; D129's guard holds at D159.
- **The banner.** The dispositions match the commits, and the corrections are 8.4.

### 8.7 New findings

**P4-19 (Low, by reading) — The resume criterion ticks with no caveat, and its wording is satisfied by the fail-open it sits beside.** `[caveat] [OB-24]`
Criterion 22 of `tools/verify_phase4.py` (printed as `OK 22. [PASS] A live run resumed from a log cut in half issues exactly the requests that log lacks, completes under a call ceiling of that many, exits as a replay of the full log does, and writes a log reading mode: live that names the session it resumed; …`,
with no caveat line after it) runs three `tests/test_cli.py` tests and prints no caveat. Its clause "names the session it resumed" is met by a resume that served nothing — P4-4,
OB-24 — and D159 says as much; the verifier, which is the document a reader is told to read instead of
the ticks, says nothing. Fifteen of the twenty-two entries carry a caveat, and the criterion written
beside an open obligation about the same path carries none — P4-18's shape, one criterion newer.
The same criterion's refusal clause omits the rubric-version case the requirement at line 178 names. Closure: a `caveat`
on criterion 22 naming OB-24 and the omitted clause — one line, no snapshot — and, when OB-24 closes,
the header clause reworded to "when an answer was served".

**P4-20 (Medium, reproduced from the artifact and the log) — By the gate's reading `J-concerns-addressed` catches none of the seven findings it traces, and D158 says nothing a rubric entry traces was hidden.** `[scope note] [pin that does not exist] [freeze]`
Reproduction: for every judged entry, each id in `traces_to` was joined to its finding's `call_ref`
and the modal verdict of the committed log on that (entry, call) was read through
`src/harness/judge/rollup.py`'s `_modal`. Six entries catch every traced finding except F-85
(`RECORDED_MISS`). `J-concerns-addressed` traces seven — F-16, F-19 and F-20 on CALL-04, F-23 on
CALL-05, F-35 on CALL-09, F-39 on CALL-10, F-58 on CALL-12, all `detectable_by: judge` — and catches
none: the distribution rows of `snapshots/report.md` read `partially_addressed x10` on CALL-04, CALL-05,
CALL-10 and CALL-12 and `partially_addressed x7, unaddressed x3` on CALL-09. Of the eleven calls that
carry none of its findings, eight read `addressed x10` and three (CALL-18, CALL-19, CALL-20) read the
middle value on a majority or a tie. So the judge answers the middle value on every seeded call and
never the pole; the gate reads `unaddressed` alone, which fires on three repetitions of one call, so the
entry's rate is 1.00 and its gate is the one of seven that holds over the seeded corpus — the entry
whose description calls F-58 "the clearest", on a call that reads `partially_addressed x10`. D158's
"nothing a rubric entry traces was hidden" is false for F-35, and the CALL-09 row it moved was the Calls table's only trace of this entry finding anything.
Nothing records the catch record: `JUDGED_AGREEMENT_PENDING` in `tests/test_rubric_coverage.py`
declares agreement unmeasured for all seven judged entries, `RECORDED_MISS` pins one call of one entry,
and the `Not checked` block reports "two of the three" for `J-policy-alignment` alone. Mechanism:
`violated` is the modal verdict equal to `entry.negative`, and the entry's `negative: unaddressed` over
the scale `[addressed, partially_addressed, unaddressed]`. The remediation introduced the sentence
and moved the row; the record was visible in the distribution rows at `7e9cf79` and this report did
not read them against `traces_to` then. Closure before the tag: append the correction to D158 (D53's
rule), and pin the design-set catch record per judged entry in `tests/test_reference_run.py` in
`RECORDED_MISS`'s shape — every traced judged finding, caught or missed by the modal verdict, failing
in both directions — so the pole is frozen knowingly. Whether `partially_addressed` should count
against a gate whose description says "every concern" is a rubric decision, the owner's, and taking it
moves the entry the tag freezes; this report does not recommend either way.

### 8.8 What must close before the tag

1. **P4-20's record**: the appended correction to D158 and the catch-record pin, or at least a
   sentence in the `Not checked` block's judged-tier entry — so the freeze is taken knowing what the
   frozen entry does on the design set.
2. **P4-19's caveat line** on criterion 22, with the rubric-version clause.
3. **P4-6's expected-cost requirement**, or a row that carries it; today nothing does.
4. **The push**, both repositories together, still outstanding: this one 17 ahead, the sibling 1
   ahead, and CI has run on none of the remediation.

Not checked in this pass: the sibling beyond its `origin/main` and `HEAD` version lines; the
held-out repository, never; the tests behind the other 21 phase-4 criteria beyond running them; a live
call, none made; and the eleven controls the specification's contract plants, beyond the gate's
re-derivation of all 110.

---

## 9. Second re-verification at `b3c519f`

Run 2026-09-13 by the same session, against the three commits after `e15170d`: `213a517` (D160),
`edcda16` (D161) and `b3c519f` (the banner paragraph). All three are pushed, CI's push run on
`b3c519f` concluded `success`, and the sibling is at its `origin/main`. The method is section 8's:
the prompt's chain step by step at `b3c519f`, and every reproduction run in `git archive` copies of
`e15170d` and `b3c519f` with no `.env` and both credential variables unset. Nothing in the tree was
changed except this report, and no live call was made.

### 9.1 Baseline at `b3c519f`

| what | result |
|---|---|
| tip | `main` at `b3c519f`, clean working tree, 0 ahead and 0 behind `origin/main`; CI's push run on it concluded `success` at 05:45Z, as did the `checks` run on `e15170d`; `comparative-judgment` is at `2bdc195`, 0 ahead of its `origin/main` |
| `uv run pytest -q` | **1156 passed** in 372.74 s, exit 0 — the remediation's figure |
| `uv run python tools/verify_phase1.py` | exit 0; "All 21 checks pass, each by running it — 20 of them the specification's own [P1] acceptance criteria"; 4 carry a caveat — unchanged |
| `uv run python -m tools.verify_phase2` | exit 0; "All 24 checks pass, each by running it — 22 of them the specification's own [P2] acceptance criteria"; 2 carry a caveat — unchanged |
| `uv run python -m tools.verify_phase3` | exit 0; "All 23 checks pass, each by running it — 18 of them the specification's own [P3] acceptance criteria, 3 its [P3] requirement prose"; 8 carry a caveat — unchanged |
| `uv run python -m tools.verify_phase4` | exit 0; "All 24 checks pass, each by running it — 24 of them the specification's own [P4] acceptance criteria"; **18 of the 24 carry a stated caveat** — the remediation's figures; criteria 22, 23 and 24 print as `OK … [PASS]`, 22 and 24 each followed by their caveat naming OB-24 and OB-33 |
| `uv run python tools/statement_inventory.py` | exit 0; "every identifier named in prose resolves" — and run again with this section in place, still resolving, with the suite run again beside it (1156 passed) |
| `uv run python tools/verify_controls.py` | exit 0; "All 115 controls were driven red by their own defect and restored", 115 `[ OK ]` lines, no `[FAIL]` or `[STOP]`, in 15 m 24 s; the five D160 controls are entries 111 to 115 — `control-mutations.yaml` holds **115** entries, as the register's tag says |
| the chain | every step exited 0 and none asked for a key; 44 m 02 s from the first step to the last, from a detached shell with the log captured whole |
| `uv run mypy`, `ruff check .`, `ruff format --check .` | no issues in 79 source files; all checks passed; 118 files already formatted |
| `control-mutations.yaml`, `tools/verify_phase4.py` | 115 entries; 24 `Criterion(` — the remediation's figures |
| the three commits | `213a517`: 20 files, 527 insertions, 64 deletions, four of them under `src/` — `src/harness/core/rubric.py`, `src/harness/judge/rollup.py`, `src/harness/judge/engine.py` and a docstring in `src/harness/cli.py` — with `rubric.yaml` (7 lines: 6 comment lines and `violating:`), the reference log and the snapshot; `edcda16`: 7 files, 114 insertions, 21 deletions, none under `src/`; `b3c519f`: this report, 19 lines |

### 9.2 P4-20's closure

**The join, twice.** Every judged entry's `traces_to` joined to its findings' calls and read through
the roll-up's `_modal` against the committed log of each copy. On `e15170d`: `J-concerns-addressed`
catches none of its seven, the other six entries catch every traced finding except F-85, 11 of 19.
On `b3c519f`: `J-concerns-addressed` catches all seven, F-85 is still missed, 18 of 19. The three pins
(`test_every_traced_finding_is_caught_or_missed_as_recorded`, the negative-instance test and the
firings pin) pass on `b3c519f`.

**The tie rule, both paths.** On `b3c519f`, `_modal` over five `addressed` and five
`partially_addressed` returns `partially_addressed`; over five `partially_addressed` and five
`unaddressed`, the pole; six `addressed` and four `partially_addressed`, `addressed`; and on an
entry declaring nothing a five-five split with `borderline` still follows scale order. The engine
imports the roll-up's `_modal` and calls it at one site, in `dimension_line`, which is the synthesis
headline (D154). With D160's clause disabled (`if member != entry.negative and member in tied:` →
`if False:`), two things fail: its control, and the byte-identical snapshot test — because the
replay then renders the seven synthesis prompts as they were before D160 and the log no longer
holds those requests. That is the headline path proven from the log rather than read. With
`violated` returned to the pole alone, the gate control and the P4-8 control fail; the catch-record
pin passes (P4-22).

**D160's argument.** It rests on the entry's own text rather than on which calls move: the question
is "whether every concern the caller actually raised was answered", and `partially_addressed` is
defined as "at least one concern was answered and at least one was left with a reply that did not
answer it" — under that question the middle value is a no. That holds. The decision was taken
knowing the catch record it produces, which D160 names and answers by leaving the prompt unchanged
and the judge's answers as they were; the held-out set is where the choice is tested. What the
argument does not do is stop at this entry: the same words decide two other entries' middle values,
and D160 does not mention them (P4-21).

**CALL-18, CALL-19 and CALL-20.** Recorded in D160's consequences and in the `Not checked` block's
judged-tier entry, each with its reading: CALL-19 on F-86, which `J-caller-pushback-understood`
traces; CALL-20 on a five-five tie, its finding F-89 `detectable_by: judge`; CALL-18 as a false
positive, F-76 being its only judge-detectable finding — all three checked against
`corpus/findings.yaml`. Not recorded in `rubric.yaml`: the entry's new comment gives the reason for
`violating` and the catch record and names none of the three, and `negative_instance` stays CALL-03.
A reader of the frozen file does not find it (P4-24).

**The evidence guard.** Driven through `evaluate_call` on `b3c519f` with a transport answering
`{"verdict": …, "rationale": "because", "citations": []}` for the entry on CALL-09: `partially_addressed`
becomes an applicable result with evidence `("judge rationale: because",)`, no informed retry, and
the roll-up reads it as violated with the gate failed; `unaddressed` does exactly the same; `addressed`
passes. So a violating middle verdict reaches the gate with no citation — and so does the pole,
because the guard at `src/harness/core/rubric.py` line 846 asks for non-empty evidence and the
engine's `_evidence_for` appends the rationale line whatever the citations. The committed log holds
no uncited answer among its 1048 (P4-23).

### 9.3 The re-recording

The two logs have 1271 records each; **15 lines differ and 1256 are byte-identical**, compared
positionally. The 15: the header, whose `started_at` moved to `2026-09-13T02:19:25Z` and whose
`resumed_from` names `2026-09-11T06:18:15Z` and `2026-09-12T06:59:06Z` — the two sessions the log
is assembled from besides its own, and nothing else in the header; seven `prompt` blobs; and seven
`J-call-synthesis` records, CALL-18 repetitions 2 and 4 and CALL-20 repetitions 3, 4, 6, 7 and 10,
each immediately after its blob. Each of the seven prompts differs from the one it replaced in two
lines: the `J-concerns-addressed` headline, `addressed` → `partially_addressed` over the same
`addressed x5, partially_addressed x5`, and the judge rationale quoted beneath it, which follows the
headline. Every record's `prompt_ref` resolves to a blob in the new log. The seven answers kept
their verdicts (`minor_defect` twice, `no_material_defect` five times), ended `end_turn` at retry
index 0, and cost $0.2917 by the pricing table against $0.2355 for the answers they replaced — D160's
$0.29 and $0.24. The snapshot moved by 22 lines: eight Calls rows gained `J-concerns-addressed`
(CALL-04, 05, 09, 10, 12, 18, 19, 20), the entry's rate went 1.00 → 0.50 in both judged tables, and
CALL-20's modal verdict reads `partially_addressed` over the same tied distribution — the 8 of 16
calls, the tie and the unchanged synthesis rows D160 states.

### 9.4 The correction attached to D158

**Accepted.** It names the false sentence, the scope it was checked on (CALL-22 alone), F-35's call,
the row's distribution, and what the join then found; every figure in it agrees with section 8.7 and
with the join above.

### 9.5 D161

**The expected figure — holds.** Requirement at line 180 of `specs/voice-agent-eval-harness.md`,
criterion at line 294, coverage row, verifier criterion 24 over four tests, `MEASURED_CONTRACT` at 9
requirements and 24 criteria. The tests assert what the criterion says: the line is printed
(`test_live_mode_prints_an_estimate_and_issues_nothing_without_confirmation`), each entry is priced
at the mean of its first attempts computed from the raw records and sits between what those attempts
spent and the ceiling (`test_the_expected_cost_sits_between_what_the_reference_run_spent_and_the_ceiling`),
an entry the log never recorded is priced at its ceiling and named, and with no log the line says
`not computed`. The caveat names the two things the figure does not do and OB-33.

**The resume criterion — holds.** It names the rubric version; `_record_reference_log` takes a
`rubric_version` and the refusal test drives a log recorded under version `0` through `--resume`,
asserting exit 2, the reason `rubric version`, no override offered and no confirmation asked, beside
the replay-mode and template cases. The caveat says the header clause is satisfied by a resume that
served nothing and names OB-24 — which is P4-19's closure.

### 9.6 What the three commits introduced, sampled

- **D160.** Options, decision, why and consequences read against the log, the gold set and both
  snapshots. Its figures hold: 8 of 16 calls, 5 seeded and 3 not; F-76, F-86 and F-89 as stated; the
  tie arithmetic (a violating verdict wins 62.3% of recordings of an even call with ties and 37.7%
  without, and two recordings disagree 47.0% of the time either way, over N=10 at one half); $0.29
  against $0.24; 1,041 served of 1,048. The ceiling of 14 is not in the log and was not checked. The
  replay "with a transport that records a miss rather than aborting" is a method, not a shipped path.
  One sentence rests on a guard that does not hold on the engine path (P4-23), and the principle it
  states is applied to one entry of three (P4-21).
- **D161.** Read in 9.5; both caveats say what the ticks do not buy.
- **The 0.30.0 and 0.31.0 changelog entries** say what D160 and D161 say, with the same figures.
- **The `Not checked` block** at 0.31.0 @ D161: three statements moved — the sibling's line now
  reads pushed at 0.8.0/D34, which its `origin/main` confirms; the cost-figure entry names the
  requirement and OB-33; the judged-tier entry gains the catch record, the overlap and the three
  calls, each as the tree has them.
- **The five controls and their register rows.** Each mutation entry names a whole line that exists
  once; each row's claim matches the test it names; the P4-8 control's row now says "one its entry
  counts against the gate"; the register's tag reads 115. Their re-derivation is 9.1.
- **The banner paragraph.** Every claim checked: the seven requests, the ceiling agreed first (D160),
  the verdicts kept, CI on `e15170d`, the pushes. **Both additions to section 8 accepted**: the
  entry's comment "it fires over this corpus by construction" was false while the gate held at 1.00,
  and section 8.7 did not cite it; the scale definitions overlap as stated. **The imprecision
  accepted**: 8.7's "never the pole" is true of a call's modal verdict and not of CALL-09's three
  repetitions, which the same sentence goes on to count.

### 9.7 New findings

**P4-21 (Medium, by reading; the log's rows read) — D160's rule is applied to one of the three entries whose middle value it decides, and the record does not say why the other two stay passes.** `[scope] [freeze]`
D160's argument is that a question asking whether every X was Y is answered no by a verdict defined
as at least one X not Y. Two other entries define their middle value in those words.
`J-policy-alignment` asks "whether the terms the agent stated … are supported by the policy clause",
and `partially_aligned` is "at least one term is supported and at least one is not — a correct rule
stated alongside a wrong figure, deadline or condition". `J-caller-pushback-understood` asks
"whether the agent understood what they were being told", and `partially_understood` is "at least one
pushback was engaged with and at least one was answered by restating the original position". Neither
declares `violating`, D160 names neither, and criterion 23's caveat says the tick does not buy the
choice for the entry that made it — nothing says the other entries' middle values were read against
their questions and left as passes for a reason. On the committed log: `partially_aligned` is no
call's modal verdict (one repetition on CALL-04, two on CALL-22), so counting it moves nothing today;
`partially_understood` is CALL-09's modal verdict (7 of 10) and would count that call, which carries
no finding the entry traces, and CALL-12's `understood x5, partially_understood x4, misunderstood x1`
could tie in the synthesis's resamples. Why before the tag: `violating` is a field of the file the
tag freezes, and D21's argument means it cannot be extended once held-out labels exist without the
tuning the freeze rules out. Closure: a recorded decision for each of the two, either way — a
paragraph appended to D160 or a decision of its own — and, for any entry counted, D160's own path.

**P4-22 (Low, reproduced) — The catch-record pin restates the gate's rule beside the roll-up instead of reading it.** `[second definition]`
`test_every_traced_finding_is_caught_or_missed_as_recorded` computes `_modal(counter, entry) in
entry.violating`; the gate computes `CallRollup.violated`. With `violated` returned to the pole alone
in a copy, the gate control and the P4-8 control fail and the pin passes. The register says the pin
is not a control, and it is not; but its subject is "counts against its gate", which is the
roll-up's word, and a copy of the rule beside it is the shape P4-3 had. Closure: compute the record
through `roll_up_judged` and read `violated`, one line.

**P4-23 (Medium, reproduced) — A judged answer with no citations becomes an applicable result for every verdict, and the evidence-on-negative-pole guard cannot fire on the engine path.** `[guard driven by nothing]`
`parse_answer` in `src/harness/judge/citations.py` requires the `citations` key and accepts an empty
list; `invalid_citations` rejects nothing from an empty list, so no informed retry fires; and
`_evidence_for` in `src/harness/judge/engine.py` appends `judge rationale: …` to the evidence, so
the guard at `src/harness/core/rubric.py` line 846 — a verdict equal to the pole must carry non-empty
evidence — sees one line and passes. Reproduced through `evaluate_call` for `unaddressed` and
`partially_addressed` alike (9.2). What holds the line is the API-side schema, `minItems: 1` on
`citations`, asserted only on the schema object in `tests/test_judge_prompt.py`; the committed log
has no uncited answer among 1048, so today's report rests on cited verdicts, and the exposure is a
provider that does not honor the schema or a log edited by hand and replayed. Not introduced by
D160 — the path is phase 3's — and named here because D160's consequences rest on the guard:
"every judged verdict carries citations by schema" is true of the schema and of nothing local.
Closure: refuse an empty `citations` in `parse_answer` so the informed retry has something to say,
and let the guard count citations rather than the evidence tuple the rationale is appended to; a
control that drives `citations: []` through the engine.

**P4-24 (Low, by reading) — The frozen entry names none of the three calls it now fails without a traced finding.** `[freeze] [record]`
The comment D160 added to `J-concerns-addressed` in `rubric.yaml` gives the reason for `violating`
and the catch record; CALL-18 read as a false positive, CALL-19 on a finding another entry traces
and CALL-20 on a tie are in D160 and the `Not checked` block only, and nothing pins the false
positive but the snapshot. `negative_instance` is the idiom for a call the entry must be silent on;
a call it fires on without a finding is its mirror and has no field. Closure: one comment line in
the entry naming the three and their readings, or a `false_positives`-shaped note beside
`negative_instance`.

### 9.8 What must close before the tag

1. **P4-21's decision**, recorded either way, because `violating` cannot be revisited after the
   labels exist. Counting either entry re-records what its ties move; leaving both at the pole costs
   a paragraph.
2. **P4-24's line** in the entry, so the frozen file says what the decision record says — one line,
   no snapshot.

P4-22 and P4-23 change no verdict and can be carried as rows.

Not checked in this pass: the ceiling of 14 D160 names, which the log does not record; the tests
behind the other 22 phase-4 criteria beyond running them; the sibling beyond its version line and
push state; the held-out repository, never; a live call, none made.

---

## 10. Third re-verification at `95aa288`

Run 2026-09-13 by the same session, against the three commits after `34046bf`: `211c848` (D162),
`4dbd777` (D163) and `95aa288` (the banner paragraph). All are pushed, CI's push run on `95aa288`
concluded `success`, and `comparative-judgment` is unchanged at `2bdc195`. The method is section 8's:
the prompt's chain step by step at `95aa288`, and every reproduction run in `git archive` copies of
`34046bf` and `95aa288` with no `.env` and both credential variables unset; the D163 probes drive the
engine through the fixtures of `tests/test_judge_engine.py` itself. Nothing in the tree was changed
except this report, and no live call was made.

### 10.1 Baseline at `95aa288`

| what | result |
|---|---|
| tip | `main` at `95aa288`, clean working tree, 0 ahead and 0 behind `origin/main`; CI's push run on it concluded `success` at 11:43Z; the sibling is at `2bdc195`, 0 ahead |
| `uv run pytest -q` | **1159 passed** in 310.20 s, exit 0 — the remediation's figure |
| `uv run python tools/verify_phase1.py` | exit 0; "All 21 checks pass, each by running it — 20 of them the specification's own [P1] acceptance criteria"; 4 carry a caveat — unchanged |
| `uv run python -m tools.verify_phase2` | exit 0; "All 24 checks pass, each by running it — 22 of them the specification's own [P2] acceptance criteria"; 2 carry a caveat — unchanged |
| `uv run python -m tools.verify_phase3` | exit 0; "All 23 checks pass, each by running it — 18 of them the specification's own [P3] acceptance criteria, 3 its [P3] requirement prose"; 8 carry a caveat — unchanged |
| `uv run python -m tools.verify_phase4` | exit 0; "All 24 checks pass, each by running it — 24 of them the specification's own [P4] acceptance criteria"; **18 of the 24 carry a stated caveat** — the remediation's figures, unchanged from section 9 |
| `uv run python tools/statement_inventory.py` | exit 0; "every identifier named in prose resolves" — and run again with this section in place, still resolving, with the suite run again beside it (1159 passed) |
| `uv run python tools/verify_controls.py` | exit 0; "All 117 controls were driven red by their own defect and restored", 117 `[ OK ]` lines, no `[FAIL]` or `[STOP]`, in 11 m 52 s; the two D163 controls are entries 116 and 117 — `control-mutations.yaml` holds **117** entries, as the register's tag says |
| the chain | every step exited 0 and none asked for a key; 37 m 15 s from the first step to the last, from a detached shell with the log captured whole |
| `uv run mypy`, `ruff check .`, `ruff format --check .` | no issues in 79 source files; all checks passed; 118 files already formatted |
| `control-mutations.yaml`, `tools/verify_phase4.py` | 117 entries; 24 `Criterion(` — the remediation's figures |
| the three commits | `211c848`: 8 files, 128 insertions, 32 deletions, none under `src/` — `rubric.yaml` (21 lines, all comments and the two `violating:` lines), the reference log, the snapshot, the reference-run tests, the verifier's caveat, the register, the specification and the decision record; `4dbd777`: 7 files, 186 insertions, 3 deletions, two under `src/` (`src/harness/judge/citations.py`, `src/harness/judge/engine.py`), two controls, two tests and one parametrized case, the register and D163; `95aa288`: this report, 16 lines |

### 10.2 P4-21's closure

**The declarations, against the words.** `J-policy-alignment` declares `violating: [partially_aligned,
misaligned]` and `J-caller-pushback-understood` declares `violating: [partially_understood,
misunderstood]`, each with a comment giving D160's reasoning in the entry's own terms — the question,
the middle value's definition, and what it moves on the committed log. The reading section 9.7 gave
is the one the comments give. D162 says the other entries' middle values are graded rather than of
this shape, which section 9's reading of every judged entry's definitions also found (P4-29 on the
count).

**The join, twice.** On `34046bf`: `J-policy-alignment` catches F-08 and F-17 and misses F-85;
`J-caller-pushback-understood` catches F-37 and F-86; 18 of 19 in all. On `95aa288`: the same
records, 18 of 19 — neither entry's catch record moved. The policy entry fails CALL-02 and CALL-04 on
both, so its gate moved on no call, as D162 says; the pushback entry fails CALL-05, CALL-08, CALL-10,
CALL-18 and CALL-19 on `34046bf` and adds CALL-09 on `95aa288`, over `partially_understood x7,
misunderstood x3` — the rate's move from 0.69 to 0.62 in the snapshot.

**Does "plausibly reads on F-35" hold up?** Partly, and the record names the wrong half. The
judge's ten rationales on CALL-09 for this entry all name two pushbacks: the caller re-asking what
the exchange would cost (T7, T9 — F-35's exchange, and F-65's) and the caller asking which show's
date the deadline meant (T13 — F-36's exchange, "including when the caller asked explicitly which
show was meant", an `assert` finding that `A-deadline-never-resolved` traces and fires on in the same
Calls row). In the seven `partially_understood` repetitions the cost pushback is the one the agent
"engaged with", by pointing to the itemized confirmation, and the date pushback is the one answered
by restating; the three `misunderstood` repetitions read both as restated. So the verdict reads on
two recorded defects of the call, and the half that fails the gate is F-36's, not F-35's. CALL-09 is
not a false positive; the frozen comment attributes it to the wrong finding (P4-25).

### 10.3 The re-recording

The two logs have 1271 records each; **7 lines differ and 1264 are byte-identical**, compared
positionally: the header, whose `started_at` moved to `2026-09-13T07:28:09Z` and whose `resumed_from`
names three sessions — `2026-09-11T06:18:15Z`, `2026-09-12T06:59:06Z` and `2026-09-13T02:19:25Z` —
and nothing else; three `prompt` blobs; and three `J-call-synthesis` records, CALL-12 repetitions 6
and 10 and CALL-22 repetition 7, each after its blob. Each prompt differs from the one it replaced in
the headline line and the rationale beneath it: on CALL-12 the pushback entry's resample splits five
and five and the headline moves `understood` → `partially_understood`; on CALL-22 the policy entry's
resample reads `aligned x4, misaligned x2, partially_aligned x4` and the headline moves `aligned` →
`partially_aligned`. CALL-12's two answers keep `minor_defect`; CALL-22's moves `no_material_defect`
→ `minor_defect`, so its row reads `no_material_defect x7, minor_defect x3` with the modal verdict
unmoved. All three ended `end_turn` at retry index 0, and cost $0.1193 by the pricing table against
$0.1166 replaced — D162's $0.12. Every record's `prompt_ref` resolves. The snapshot moved by 8 lines:
CALL-09's Calls row gains `J-caller-pushback-understood`, that entry's rate reads 0.62 in both judged
tables, and CALL-22's synthesis row — exactly the three places the owner named.

### 10.4 P4-22's closure

`_violated` in `tests/test_reference_run.py` builds a `CallRollup` over the counter and reads its
`violated`, and `CallRollup.verdict` is a property computing `_modal` over the distribution, so the
helper reads the gate's rule rather than a copy. The catch-record pin, the seeded test, the
recorded-miss test and the negative-instance test call it; the firings pin still sums repetitions by
`entry.violating`, which is the only reading a per-repetition count can have.

**Under `violated` returned to the pole alone**, in a copy of `95aa288`, the five run together: the
catch-record pin fails and the other four pass. Why each passes:

- the seeded test: `J-policy-alignment`'s seeded calls are `misaligned x10` and `misaligned x9`, caught
  by the pole as surely as by the declaration — not discriminating on this corpus, not blind;
- the recorded-miss test: CALL-19 is `aligned x10`, missed under either rule — not discriminating;
- the negative-instance test: every negative instance's modal verdict is its entry's positive pole,
  so no rule reads it as violated — not discriminating;
- the firings pin: it counts repetitions returning a verdict in `entry.violating` and never asks the
  roll-up, so it passes whatever `violated` says — blind to that mutation by construction, since the
  roll-up offers no per-repetition rule to read; its subject is the declaration, and the mutation
  moves the roll-up away from the declaration.

D162 says returning `violated` to the pole "turns them red with the gate's controls". On this corpus
it turns one of the four red (P4-26).

### 10.5 P4-23's closure and its twin

**Driven through `evaluate_call` at `95aa288`**, with the test module's scripted transport. A dimension
answer with `citations: []` twice: two requests sent, `informed_retries` 1, `errored`, no verdict, no
evidence. The same answer once and a cited one on the retry: applicable `misaligned` with two evidence
lines. A synthesis answer with `rests_on: []` twice, shown the fixture's dimensions: two sent, one
retry, `errored`. Once and then resting on a listed dimension: applicable, `unresolved_dimensions`
empty. The committed log has no answer with an empty `citations` list and none of its 168 synthesis
answers with an empty `rests_on`, so replay refuses nothing it serves; the suite's replays and the
snapshot pass at `95aa288` (10.1).

**The retry's wording.** The second request's correction reads "Your previous answer could not be read
as the JSON object this prompt declares. Return that object and nothing else: no prose before or after
it, no code fence, and every key present", then the transcript and fact identifier lists, then "Answer
again, in the same JSON shape, citing only from those two lists." For an uncited answer every key was
present and the guidance points at faults it did not have; the two lists at least say what to cite.
For a synthesis resting on nothing the message names no dimension and no `rests_on` at all: the model
is told to cite transcript and fact identifiers, which is not what was missing. The failure text the
engine holds — "'citations' is empty …", "'rests_on' is empty …" — is not passed to
`informed_retry_message`. That is a gap (P4-27).

**A synthesis shown no dimension.** It renders: `synthesis_input` over an empty `prior` yields no
dimension line and an empty `entry_ids`, `render_prompt` accepts it, and the request's schema still
carries `rests_on` with `minItems: 1`, because `response_schema` reads the entry and not what was
listed. Driven through `evaluate_call` with `prior=()`: an answer with `rests_on: []` becomes an
applicable `minor_defect` with nothing unresolved and no retry — a clean synthesis resting on nothing,
the case D163's guard leaves for "there was nothing to name"; an answer naming one dimension becomes
an applicable verdict with that dimension unresolved, reported as a defect. A live model, held to the
schema, must name something, so every repetition of such a synthesis would carry a defect by
construction. The case is not reachable with the shipped rubric — `run_judged` hands the synthesis
every dimension's outcome for the call, statuses included — and only a rubric whose judged tier is the
synthesis alone would reach it, which nothing refuses at load (P4-28).

### 10.6 What the three commits introduced, sampled

- **D162.** Read against the log, the gold set, the snapshot and the reference-run tests. Its
  figures hold: no call moves on the policy entry, CALL-09 on the pushback entry, 0.69 → 0.62, the
  three requests and their resamples, $0.12, 1,045 served, CALL-22's row and the synthesis's negative
  instance at 0. Two statements the tree does not bear out: the mutation sentence (P4-26) and the
  count of entries whose middle value is graded (P4-29). The ceiling of 6 is not in the log and was
  not checked.
- **D163.** Its account of the engine path is what section 9.7 found and what 10.5 reproduces; its
  stated limits — the retry's wording, the synthesis shown no dimension — are the two 10.5 probes,
  and each is a little wider than the sentence that names it (P4-27, P4-28). "None of its 168
  synthesis answers rests on nothing" holds.
- **The correction attached to D160.** Accepted; it says what P4-23 said.
- **The 0.32.0 changelog entry** says what D162 says, with the same figures.
- **The `Not checked` block** at 0.32.0 @ D162: the intro names the refresh and the judged-tier
  entry gains one sentence on D162, true of the tree.
- **The two controls and their register rows.** Each mutation entry names a whole line that exists
  once (`if not citations:` and `if rendered.rests_on and not answer.rests_on:`); each row's claim
  matches its test; the register's tag reads 117. Their re-derivation is 10.1.
- **P4-24's comment lines.** `J-concerns-addressed` names CALL-18, CALL-19 and CALL-20 with the
  readings D160 gave; `J-caller-pushback-understood` names CALL-09 — with F-35 alone (P4-25).
- **The banner paragraph.** Every claim checked against the tree except one: "the pin fails once
  `violated` reads the pole alone" is true, and the neighbors it says read `violated` stay green under
  that mutation on this corpus (10.4). The addition to section 9 — the `rests_on` twin — is accepted.

### 10.7 New findings

**P4-25 (Low, reproduced from the artifact) — The frozen comment attributes CALL-09's failure to F-35, and the judge's rationales rest the failing half on F-36.** `[freeze] [record]`
The comment D162 added to `J-caller-pushback-understood` in `rubric.yaml` says its CALL-09 verdicts
"plausibly read on F-35, where the caller asked again and was told the answer would appear on a
document". All ten rationales name two pushbacks; in the seven `partially_understood` ones the cost
pushback (F-35's exchange, T7 and T9) is the one engaged with, and the date pushback (T13, F-36's
exchange, "never resolved to a date, including when the caller asked explicitly which show was
meant") is the one answered by restating — the half that fails the gate. CALL-09 is not a false
positive: the entry fires on two recorded defects of the call, neither traced by it, one of them an
`assert` finding the deterministic tier already catches there. Closure: one line in the comment naming
F-36 beside F-35, and "plausibly" dropped, before the tag freezes the attribution.

**P4-26 (Low, reproduced) — D162 says returning `violated` to the pole turns four tests red; on this corpus it turns one.** `[record]`
Under that mutation the catch-record pin fails and the seeded, recorded-miss and negative-instance
tests pass, each because the committed log holds no call the two rules separate for it (10.4). The
three read `violated` and would discriminate on another corpus; the sentence claims a redness the
tree does not show. Closure: correct the sentence, appended (D53).

**P4-27 (Low, reproduced) — The informed retry for D163's two refusals does not say which list was empty, and for a synthesis points at the wrong lists.** `[retry]`
`informed_retry_message` has two wordings, rejected identifiers or a malformed object; an empty list is
sent the second, whose guidance — no prose, no fence, every key present — describes faults the answer
did not have, and whose closing line tells a synthesis to cite from the transcript and fact lists when
what it lacked was a dimension. D163 states the first half and not the second. The failure text
exists in the engine and is dropped. Closure: a third wording naming the empty list and, for
`rests_on`, the dimensions the prompt listed; D163's own control covers the recovery either way.

**P4-28 (Low, reproduced) — A synthesis shown no dimension is sent a schema demanding a name and a validator accepting none.** `[schema] [edge]`
`response_schema` gives `rests_on` `minItems: 1` whatever `synthesis_input` listed, and D163's guard
asks for a name only when something was listed. Driven with `prior=()`: an empty `rests_on` is a clean
applicable verdict, and any name is an applicable verdict with an unresolved-dimension defect — so a
live model, held to the schema, produces a defect on every repetition. Unreachable with the shipped
rubric, since the synthesis is handed every dimension's outcome, and reachable by a rubric whose
judged tier is the synthesis alone, which the loader does not refuse. Closure: build `rests_on` into
the schema only when a dimension was listed, or refuse to render a synthesis shown none.

**P4-29 (Low, by reading) — D162 counts three entries with a graded middle value; there are four.** `[count]`
`borderline` is the middle value of both `J-unnecessary-repetition` and `J-confidence-exceeds-sources`,
beside `doubtful` and `minor_defect`; the sentence names three values and calls them three entries.
The claim that none is of the "at least one … not" shape holds for all four. Closure: the count,
appended.

### 10.8 What must close before the tag

1. **P4-25's line** in the frozen entry's comment — one line, no snapshot — so the file the tag
   freezes attributes CALL-09 to the exchange the judge marked, and stops calling it plausible.

P4-26 and P4-29 are corrections to D162, appended; P4-27 and P4-28 change no recorded result and can
be carried as rows.

Not checked in this pass: the ceiling of 6 D162 names; the tests behind the other 22 phase-4 criteria
beyond running them; the sibling beyond its push state; the held-out repository, never; a live call,
none made.

---

## 11. Fourth re-verification at `f401138`

Run 2026-09-13 by the same session, against the four commits after `ea99dbf`: `94fd27c` (the
records), `0b62ec7` (D164), `2d876e7` (D165) and `f401138` (the banner paragraph). All are pushed,
CI's push run on `f401138` concluded `success`, and `comparative-judgment` is unchanged at
`2bdc195`. The method is section 8's: the prompt's chain step by step at `f401138`, and every
reproduction run in `git archive` copies of `ea99dbf` and `f401138` with no `.env` and both credential
variables unset, the engine driven through the fixtures of `tests/test_judge_engine.py`. Nothing in
the tree was changed except this report, and no live call was made.

### 11.1 Baseline at `f401138`

| what | result |
|---|---|
| tip | `main` at `f401138`, clean working tree, 0 ahead and 0 behind `origin/main`; CI's push run on it concluded `success` at 20:42Z; the sibling is at `2bdc195`, 0 ahead |
| `uv run pytest -q` | **1162 passed** in 519.84 s, exit 0 — the remediation's figure; the two copies' replays ran beside it, which is the wall clock |
| `uv run python tools/verify_phase1.py` | exit 0; "All 21 checks pass, each by running it — 20 of them the specification's own [P1] acceptance criteria"; 4 carry a caveat — unchanged |
| `uv run python -m tools.verify_phase2` | exit 0; "All 24 checks pass, each by running it — 22 of them the specification's own [P2] acceptance criteria"; 2 carry a caveat — unchanged |
| `uv run python -m tools.verify_phase3` | exit 0; "All 23 checks pass, each by running it — 18 of them the specification's own [P3] acceptance criteria, 3 its [P3] requirement prose"; 8 carry a caveat — unchanged |
| `uv run python -m tools.verify_phase4` | exit 0; "All 24 checks pass, each by running it — 24 of them the specification's own [P4] acceptance criteria"; **18 of the 24 carry a stated caveat** — the remediation's figures, unchanged from section 10 |
| `uv run python tools/statement_inventory.py` | exit 0; "every identifier named in prose resolves" — and run again with this section in place, still resolving, with the suite run again beside it (1162 passed) |
| `uv run python tools/verify_controls.py` | exit 0; "All 120 controls were driven red by their own defect and restored", 120 `[ OK ]` lines, no `[FAIL]` or `[STOP]`, in 14 m 04 s; the three D164 and D165 controls are entries 118 to 120 — `control-mutations.yaml` holds **120** entries, as the register's tag says |
| the chain | every step exited 0 and none asked for a key; 47 m 30 s from the first step to the last, from a detached shell with the log captured whole |
| `uv run mypy`, `ruff check .`, `ruff format --check .` | no issues in 79 source files; all checks passed; 118 files already formatted |
| `control-mutations.yaml`, `tools/verify_phase4.py` | 120 entries; 24 `Criterion(` — the remediation's figures |
| the four commits | `94fd27c`: 2 files, 20 insertions, 4 deletions — the entry's comment and the decision record, no code; `0b62ec7`: 6 files, 198 insertions, 8 deletions, two under `src/` (`src/harness/judge/citations.py`, `src/harness/judge/engine.py`), two controls, two tests, the register and D164; `2d876e7`: 6 files, 129 insertions, 14 deletions, the same two source files, one control, one test, two docstrings, the register and D165; `f401138`: this report, 16 lines |
| replay of the committed log, both copies | `harness run --tier judge --mode replay` over `runs/reference-corpus-0.6.0.jsonl`: exit 1, `results: 1048 of which issued a call: 1040`, `applicable: 1040 not_applicable: 8`, **`GATES FAILED: 7 of 7`** — every request served on `ea99dbf` and on `f401138` alike. Seven of seven since D160; section 1 read six of seven, `J-concerns-addressed` being the gate that held |

### 11.2 P4-25's closure

The comment now in `J-caller-pushback-understood` reads: its `partially_understood x7, misunderstood
x3` "reads on two pushbacks: every repetition marks the one about which show a deadline meant as
answered by restating, which is F-36's exchange, and the 3 `misunderstood` ones fault the cost
question of F-35 and F-65 too. A-deadline-never-resolved traces F-36, J-concerns-addressed F-35."
Against the ten rationales section 10.2 read, on a log no commit since has touched: all ten name the
same two pushbacks; all ten fault the date pushback at T13, the seven `partially_understood` by
naming it the one answered by restating and the three `misunderstood` beside the cost pushback; the
seven count the cost pushback at T7 and T9 as engaged. The comment says exactly that. The correction
attached to D162 says the same in the same terms — the pushback faulted in all ten, the seven that
count the cost question as engaged, the three that fault both, the half that fails the gate being
F-36's — and the `Not checked` sentence reads "the pushback all 10 of its repetitions fault is F-36's,
which `A-deadline-never-resolved` traces", which both bear out. **Holds.**

### 11.3 P4-26's and P4-29's closures

The correction's second sentence: returning `violated` to the pole alone "turns 1 of the 4 tests
red, the catch-record pin", the seeded, recorded-miss and negative-instance tests reading
`CallRollup.violated` and passing "because no call in the committed log separates the pole-only rule
from the declared one for them". That is section 10.4's reproduction, test for test and reason for
reason; the four are the four D162's original sentence named, so the firings pin, which section 10.4
also ran, is rightly outside the count. The third sentence: the graded middle values "belong to 4
entries, not 3", `borderline` being the middle value of both `J-unnecessary-repetition` and
`J-confidence-exceeds-sources` — which is what the rubric's scales say, beside `doubtful` and
`minor_defect`. **Both hold.**

### 11.4 D164

**Each retry, read.** Driven through `evaluate_call` on `f401138`, the second request's correction
block begins, for invalid JSON: "Your previous answer could not be read as the JSON object this
prompt declares: response is not valid JSON: Expecting value: line 1 column 1 (char 0). Return that
object and nothing else …"; for an empty `citations` list: "… declares: 'citations' is empty, and the
declared schema requires at least one identifier. Return that object …"; for a synthesis with an
empty `rests_on`: "… declares: 'rests_on' is empty, and the synthesis's declared schema requires at
least one identifier …", then the transcript and fact lists, then "Dimension identifiers, in full:
J-concerns-addressed, J-unnecessary-repetition" — bare — and "Answer again, in the same JSON shape,
citing only from the transcript and fact lists and resting only on those dimensions." Each spends
one retry and, corrected, resolves applicable. On `ea99dbf` the same three drives produce the one
generic wording section 10.5 quoted, with no failure named and no dimension listed — the positive.

**The recorded wording.** A synthesis whose citation is rejected (`T999`) gets "Your previous answer
cited identifiers that were not in this prompt: 'T999'." and the closing "Answer again, in the same
JSON shape, citing only from those two lists.", with no dimension list — the first and last lines of
every recorded retry's correction block. The committed log holds 8 informed retries, all on
`J-call-synthesis`, all for rejected identifiers and none for a schema failure, and none mentions
"Dimension identifiers".

**The replay.** Both copies serve every record (11.1). The positive control: with the
rejected-identifier wording altered by one character in the `f401138` copy, the same replay aborts
after 55 results, exit 3 — the first synthesis retry's request no longer in the log. The instrument
sees a changed retry, and the unchanged one served all eight.

**The guidance beside the named failure.** The schema wording keeps "Return that object and nothing
else: no prose before or after it, no code fence, and every key present" after the colon. Beside
"'citations' is empty, and the declared schema requires at least one identifier" and the identifier
lists, that sentence is redundant rather than misleading: the fault is named first and the fix is
what follows. It no longer misleads enough to matter. **Holds**, with one edge in 11.7 (P4-30).

### 11.5 D165

**A synthesis shown no dimension**, driven with `prior=()` on `f401138`: the request's schema has the
keys `citations`, `rationale` and `verdict`, `rests_on` neither present nor required,
`additionalProperties` false; an answer without `rests_on` stands — applicable, no retry, nothing
unresolved; an answer naming a dimension anyway is applicable with that dimension unresolved, the
defect the prompt warned it against. **A synthesis shown dimensions** keeps `rests_on`, required,
`minItems: 1`. No recorded request moved: the replay served all 1,048 records, every recorded
synthesis having been shown dimensions. **Holds.**

**The template's `rests_on` instruction.** For the `prior=()` request, the system message carries
four lines about `rests_on` — "Name in `rests_on` the dimensions your verdict would change without",
"Return JSON matching the schema you have been given: … and `rests_on` as a list of the dimension
identifiers whose results you actually used", "`rests_on` is not a formality …" — while the schema
forbids the key, and the user message says "None. No other dimension produced a result for this call
… do not invent a dimension identifier, and do not assume a verdict for one." So yes: a synthesis
shown no dimension is told in prose to name dimensions in a key its schema does not have. The
instruction that governs is "matching the schema you have been given", and structured output cannot
carry the key, so the contradiction cannot reach a result; it is confusing rather than harmful, and it
is unreachable with the shipped rubric, which hands the synthesis every dimension's outcome. D165
records the template as left unedited to keep its hash. It does not matter for the tag; it belongs to
the next template version, and is not numbered here.

### 11.6 What the four commits introduced, sampled

- **D164.** Its account of the old retry is section 10.5's; its claims — 8 recorded retries, all on
  the synthesis and all for rejected identifiers; the replay serving every request through the changed
  engine; the copy with the rejected wording altered aborting on a miss — are 11.4's reproductions.
  Its reading of the `[P3]` requirement holds: the requirement says a response that cannot be read as
  the declared schema spends the single retry with the parse failure named. Options (A), (B), (C) and
  the choice of (B) are as the code has it. The dimensions are listed bare, and `unresolved_dimensions`
  compares them bare.
- **D165.** Its account of the case is section 10.5's, its `NO_DIMENSION_RESULTS` sentence is the
  renderer's, and its consequences are 11.5's; the ordering contract's new reason is what the
  `prior=()` drive shows.
- **The note attached to D163** says its retry caveat no longer holds and points at D164 — true.
- **The correction attached to D162** is 11.2 and 11.3.
- **The three controls and their register rows.** Each mutation entry names a whole line that exists
  once (`named = f": {failure}" if failure else ""`, `if dimensions and not rejected:`,
  `asks_rests_on = is_synthesis(entry) and bool(rendered.rests_on)`); each row's claim matches its
  test; the register's tag reads 120. Their re-derivation is 11.1.
- **The corrected ordering row** says a synthesis run before its dimensions "is shown none and
  returns a verdict that synthesizes nothing … (since D165; before it, a citation defect on every
  call)" — both halves are what the `prior=()` drives at `95aa288` and `f401138` showed.
- **The banner paragraph.** Every claim checked: the comment, the correction, D164's wording and the
  8 recorded retries, D165's schema, the replay through the changed engine, the copy that aborted.
  The ceiling of 6 is stated as outside the tree, which is where it is.

### 11.7 New findings

**P4-30 (Low, reproduced) — The retry names the first failure the engine finds, so an answer with two faults is corrected for one and refused for the other.** `[retry] [edge]`
`_validate` reports one failure: the parse, then the citations, then `rests_on`. A synthesis answer
citing `T999` with an empty `rests_on` is sent a retry naming `'T999'` alone; an answer with both
lists empty is sent one naming `citations` alone. In both drives the retry that fixes the named fault
and keeps the other is refused, and the result is `errored` — the one retry the requirement grants
spent on half a correction. A retry fixing both is applicable. The committed log holds no such answer:
its 8 retries each corrected rejected citations and nothing else. Closure: collect every failure in
`_validate` and name them all in the correction — one function, no snapshot.

### 11.8 What must close before the tag

Nothing from this pass. P4-30 changes no recorded result and can be carried as a row; the template's
`rests_on` sentences are a note for the next template version.

Not checked in this pass: the ceiling of 6, which is outside the tree; the tests behind the other 22
phase-4 criteria beyond running them; the sibling beyond its push state; the held-out repository,
never; a live call, none made.
