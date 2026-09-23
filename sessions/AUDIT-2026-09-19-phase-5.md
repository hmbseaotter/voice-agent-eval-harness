> **WORKING STATUS, maintained separately from the report below.** Written 2026-09-19 against
> `c5ad3ce`, the tip of the span under audit; `2a20a95`, one commit later, adds only the audit
> prompt. A later session that closes a finding records it here, with the reproduction it re-ran, so
> that this banner and not the body is what a reader trusts for status. Corrections to the report
> belong here too.
>
> **2026-09-19, remediation — all 16 closed, on the owner's decisions.** Worked by the session
> that built the coverage report, which had read held-out content and does no rubric work. Every
> finding was reproduced or re-read before anything changed: the appendix's two scripts printed the
> output recorded beneath them, line for line, and each `by reading` finding was checked against the
> code and the data it cites. None was withdrawn.
>
> **Closed.** P5-3 (`37096bc`): items 1 and 2 of the reveal handover no longer state a held-out
> count or a shape the held-out set alone uses; `f562412`'s message is pushed and is recorded here
> rather than rewritten. P5-7 (`164ce67`, D194): the sweep marker names the version a sweep was
> recorded at, and from 0.55.0 moves only to a version whose changelog entry says it records one —
> **the sweep itself is owed at phase 5's close**. P5-1 and P5-4 (`b039f32`, D195): every reading
> decodes by byte-order mark, a file none can decode fails the check by name, and the label files, a
> findings view, agreement's section, a record laid out across lines and an extraction artifact each
> have a reading; the two cp1252 logs were moved out of `build/`. P5-2 (`b163a74`, D196):
> `harness.extract` and `harness.findings_view` refuse an `--out` path inside the checkout over
> held-out content, with a requirement and a criterion. P5-5 (`5160a0f`, D197): agreement and
> coverage refuse a held-out log judged under another rubric or none. P5-16 (`e15d9ec`): a header
> missing a field raises `RunLogFormatError` by name, and the two measurement commands' staleness
> refusal stops offering a flag they do not take. P5-6 (`0800888`): five tests and seven control
> entries for the checks that had none, including a `main()`-level test for the report reading.
> P5-14 (`0698181`): the control gate writes each line ending back as it found it. P5-9
> (`3850885`): the family tables and agreement's expected calls are compared, and the one difference
> is pinned in the test and recorded in OB-49's row. P5-11 (`ffd011e`, D198): Class 6 declares the
> two reason codes and the remedy, with a check for the kind. P5-8, P5-12 and P5-13 (`fcffebe`): the
> phase-5 verifier's caveat says what is true since the reveal, and the README names
> `--held-out-policies` and states the `[skip ci]` rule. P5-15 and P5-10 (`7540163`): D192 carries a
> correction, and D188 a note.
>
> **Corrections to the report.** Two spellings (`0043136`), and its appendix reformatted as `ruff
> format` writes Python inside Markdown (`dc205d8`), which CI checks; neither script's behavior
> changed. **What the remediation leaves owed**, beyond the sweep above: OB-49's decision at phase
> 6's opening reading, which P5-9 bears on, and OB-7.
>
> **2026-09-19, as written — 16 findings, none closed.** 3 High (P5-1 to P5-3), 4 Medium (P5-4 to
> P5-7) and 9 Low (P5-8 to P5-16). One finding, P5-3, could not be stated in full without held-out
> content; the part that could not is recorded here only as having been given to the owner in the
> conversation, on the owner's rule for this report.

# Audit — phase 5 (held-out labels and validation, and the obligations closed after the freeze), at `c5ad3ce`

> **STATUS.** Written 2026-09-19 by an independent session (Claude Fable 5.1, effort `max`) that
> took no part in the phase-5 build or in the obligations closed after the freeze. Nothing in the
> tree was modified; this report is the only file the session added. Every mutation and every
> planted artifact below was made in a copy of the tree, or in a directory of invented files, under
> the session's scratch directory outside both repositories, with `.env` excluded from every copy
> and neither credential variable set. Every finding marked *reproduced* was reproduced by running
> something against this tree or a copy of it; one marked *by reading* rests on the source and says
> what could not be run. No live model call was made, nothing was tagged, and nothing in the
> held-out repository or in `comparative-judgment` was edited, committed, dispatched or opened as
> an issue.
>
> **This session read held-out content, on the owner's decision, and does no rubric work.** It read
> six inputs in place in the held-out repository and nothing else there: the labels' findings,
> traces and severity export, the transcripts, the corpus version file and the one run log whose
> name starts `heldout-`. **This report carries none of it**: no transcript text, label, figure,
> finding id or band. A finding about a held-out path is stated in terms of the code and of
> invented data, and section 6 says how the tree was searched and how the search was shown able to
> find something.

**Kind of review.** The phase-3 and phase-4 reports' shape: the baseline reproduced first, every
verifier tick asked what would have to break for it to print FAIL, a small mutation sweep of the
lines that looked unguarded, the counts recomputed, and a sample of the prose checked against the
tree. Each instrument was made to produce a positive before a null from it was believed, and one
of this session's own instruments failed that test first: the first mutation sweep reported 10 of
11 mutations killed in 4 seconds each, which was one git-dependent test failing in a copy with no
`.git`, whatever the mutation. It was rebuilt with an unmutated baseline and named failures before
any result below was taken from it (section 4).

---

## 1. Baseline, reproduced

Run as the prompt's chain, one step at a time so each exit code is its own, from a detached shell
with every log captured whole under the scratch directory. The tree was clean at `2a20a95` before,
between and after.

| what | result |
|---|---|
| tip | `main` at `2a20a95`, clean, level with `origin/main`. The span `6d3a710..c5ad3ce` is 41 commits, 10 to `dff180c` and 31 after it; 50 files, 10,534 insertions and 570 deletions, of which 16 files and 2,846 insertions are under `src/` and `tools/` — as the prompt says |
| `ruff check`, `ruff format --check`, `mypy` | all checks passed; 128 files already formatted; no issues in 84 source files |
| `python -m harness.extract` | exit 0; 16 calls, 408 events, 0 unparsed lines, content hash `32afd5dd…` |
| `pytest -q` | **1286 passed** in 665.66 s, exit 0 |
| `tools/verify_phase1.py` | exit 0; all 21 checks pass, 20 of them `[P1]` criteria, 4 caveats |
| `tools.verify_phase2` | exit 0; all 24, 22 of them `[P2]` criteria, 2 caveats |
| `tools.verify_phase3` | exit 0; all 23, 18 `[P3]` criteria and 3 requirement prose, 7 caveats |
| `tools.verify_phase4` | exit 0; all 24, all `[P4]` criteria, 6 caveats |
| `tools.verify_phase5` | exit 0; all 10 checks pass, 10 of them `[P5]` criteria, **all 10 carry a caveat**; 3 more declared and not ticked, all 3 asserted elsewhere, 0 not yet built |
| `harness report --out` diffed against `snapshots/report.md` | byte-identical |
| `harness.findings_view --check` | view is current, 90 findings |
| interface scanner | OK; 6 findings keys, 8 severity fields and 6 row fields agree, across 3 harness files and 2 tool files |
| `tools/statement_inventory.py` | every identifier named in prose resolves |
| `tools/check_holdout_absence.py` | OK; 16 declared design transcripts and 5 declared fixtures, no held-out run log, report or coverage report. **It passes over 2 files it cannot read** (P5-1) |
| `harness agreement`, design section | exit 0; 16 calls, 44 entries; every entry: 69 hits, 1 miss, 20 false alarms, 194 correct silences, 420 no verdict, 704 entry-call pairs. The miss is `J-policy-alignment` on CALL-19, which `RECORDED_MISS` pins. 19 of the 20 false alarms are judged entries'; the other is P5-9 |
| `harness coverage`, design section | exit 0; 90 findings on 16 calls, severity run `b5b6c281ec6d7c14`; critical 4 held, 3 traced, 3 retired; high 14, 14, 14; medium 28, 27, 27; low 37, 33, 32; F-76, F-90, F-60, F-55, F-89 and F-42 uncovered, F-85 missed, 7 question-tier with F-54 retired, 0 unplaced — D188's and D192's figures |
| `tools/verify_controls.py` | exit 0; all **286** controls were driven red by their own defect and restored, 286 `[ OK ]` lines, no `[FAIL]` or `[STOP]`, in 46 m 49 s while this session's own sweeps shared the machine. The tree was clean after it |
| the held-out sections, over the 6 inputs in place, to stdout only | `harness coverage`: **computed, exit 0**. `harness agreement`: **computed, exit 0**. Nothing else about either is recorded here |
| `control-mutations.yaml` | 120 entries at the freeze, **286** now, 216 distinct controls; 170 entries added or re-anchored since the freeze, over 104 distinct controls. `CONTROL-REGISTER.md` says 286 |
| the rubric's `traces_to` | 64 traces from deterministic entries to assert-type findings and 19 from judged entries to judge-type ones, none across the tiers, 78 of 90 findings traced — the reveal handover's counts |
| `corpus/findings.severity.json` since the freeze | 2 commits, `dff180c` and `8b20ac8`, each moving `comparison_log_hash` and `run_id` and nothing else; parsed, every other key equals the freeze's. 83 rows; 4 critical, 14 high, 28 medium, 37 low. D172's and D190's claim holds |
| `.cj-store` | 418 log records, the last one the D190 assignment; byte-identical to the backup beside the checkout (compared with `cmp`, nothing read) |
| line endings | `git ls-files --eol`: every tracked text file `i/lf`, 0 files `w/crlf` |
| D193's count | 116 identifier-shaped tokens across the design transcripts, as D193 says |
| CI | every push-event run on `main` in the span concluded `success` except 2 canceled by a dispatch run on the same commit seconds later, which succeeded; the newest, on `2a20a95`, succeeded. 6 commits carry `[skip ci]` (P5-13) |
| credentials | neither credential variable was set in the environment. A populated `.env` sits in the working tree, gitignored and unread by this session; replay is the default mode, and nothing in the baseline asked for a key |

Where a number in the prompt, a handover or the decision record disagreed with what was measured,
the measurement is in the table and the disagreement is a finding. None of the counts did. The
disagreements found are in prose rather than in counts: P5-3, P5-7, P5-8 and P5-12.

---

## 2. Findings

Severity as the prompt defines it: **High** = held-out content in this tree, a fail-open path, or a
gate or verifier tick that does not stand for what it claims; **Medium** = a real gap phase 5's
close, phase 6 or the next held-out set will hit; **Low** = hygiene, duplication, or an untested
edge with no current instance. Every copy of the tree below excluded `.env`, `.git`, `.venv`, the
caches, `build/`, `private/` and `.cj-store/`, and ran with the copy's `src/` first on `PYTHONPATH`
and bytecode writing off — the method `tools/verify_controls.py` uses. Every invented held-out
artifact is design data with a call renamed to an id `HELDOUT_SET` declares, or a design finding
renamed to the `HF-NN` shape, as the suite's own fixtures are.

### High

**P5-1 (High, reproduced) — The absence check skips every file it cannot decode as UTF-8, so all four shapes are blind to what a PowerShell redirect writes on this machine, while the phase-5 verifier's caveat names the absence check as what reports a redirected held-out section.** `[verifier caveat against a neighbor] [fail-open] [instrument]`

Reproduction. Each of the tool's four readings was called on a scratch directory holding one
invented artifact, beside a positive control carrying the same text:

```
positive controls (each must be reported):
  transcript, run-log header, run-log call record, report, coverage   -> REPORTED, all 5
the same content, re-encoded as a PowerShell redirect writes it:
  utf16-transcript / utf16-runlog-call / utf16-report / utf16-coverage  -> not reported, all 4
  utf8bom-transcript                                                    -> REPORTED
  utf8bom-report                                                        -> not reported
  utf8bom-coverage, the command's whole output                          -> REPORTED
  utf8bom-coverage, the held-out section alone                          -> not reported
  utf8-coverage, the held-out section alone                             -> REPORTED
```

Both encodings were measured here rather than assumed. `powershell.exe -NoProfile` on this machine,
redirecting a native command's output with `>`, wrote a file opening `FF FE`: UTF-16LE, Windows
PowerShell 5.1's default. The session's own PowerShell, whose profile sets `Out-File:Encoding` to
`utf8`, wrote `EF BB BF`: UTF-8 with a byte-order mark. A redirect from Git Bash wrote plain ASCII
for the report, agreement and coverage outputs, which the check reads.

Mechanism. `tools/check_holdout_absence.py:215-220`, `:275-278`, `:312-318` and `:352-358` each
read with `path.read_text(encoding="utf-8")` and return `None` on `UnicodeDecodeError`, so a text
file in another encoding is treated as a binary one and passed over in silence. Beside that, the
report and coverage markers anchor at a line's start (`:242`, `:251-253`), and a byte-order mark is
a character in front of the first line, so a heading on line 1 stops matching. **The tree shows the
silent skip today**: `build/v1.log` and `build/v2.log`, verifier output redirected there on
2026-09-08, are cp1252 rather than UTF-8 because of one em dash each, and the check's OK line is
printed over them unread. Their content is benign; what they show is that redirected command
output in a non-UTF-8 encoding already sits in `build/`, which is the accident the check exists for.

What rests on it. `tools/verify_phase5.py:211-215`, the caveat of the `harness coverage` criterion,
tells a reader that a redirect can still put the held-out section in this tree and that the absence
check is what reports it there. On this machine, where PowerShell is the primary shell, it does
not. D185 and D188 each chose the shape for that reason, and
`tests/test_holdout_absence.py` writes every planted artifact as UTF-8 without a byte-order mark,
so no test exercises the redirect the shapes were built to catch.

Closure. Decode by byte-order mark (`utf-8-sig`, and UTF-16 when the file opens `FF FE` or
`FE FF`), and **fail closed** on a file with no binary suffix that still does not decode: report it
as unreadable rather than skip it. Add, for each shape, a test that writes the artifact as each of
the 2 PowerShell encodings, with a control per encoding. Checked before recommending: failing
closed today would report exactly `build/v1.log` and `build/v2.log`, which are ignored and
deletable; no tracked file fails to decode, and the only file in the tree opening with a byte-order
mark is the ignored `resume_session.txt`.

**P5-2 (High, reproduced) — `python -m harness.extract` and `python -m harness.findings_view` take an input path, write inside this checkout by default, and read no `HELDOUT_SET`; the absence check sees neither result.** `[fail-open] [rule applied to 4 commands of 6]`

Reproduction, in a copy of the tree, with design CALL-01 renamed to CALL-13, an id `HELDOUT_SET`
declares, in a directory outside the copy:

```
$ python -m harness.extract --transcripts <outside>/renamed          (no --out given)
calls: 1  events: 21  unparsed lines: 0
artifact: build/extraction-artifact.json                              exit=0
   -> 10,427 bytes inside the copy, naming CALL-13 and carrying every turn of the call
$ python tools/check_holdout_absence.py                                exit=0, "OK"
positive control: the same call as a transcript file under build/      exit=1, names CALL-13 as HELD-OUT

$ python -m harness.findings_view --findings <outside>/hf-findings.yaml   (no --out given)
wrote corpus/findings.md (90 findings)                                 exit=0
   -> the tracked view now carries 90 HF- ids (0 before)
$ python tools/check_holdout_absence.py                                exit=0, "OK"
$ python -m harness.findings_view --check                              exit=1, "is stale"
the same view written with --out build/labels-view.md: view check exit=0, absence check exit=0
```

Mechanism. `src/harness/extract.py:72-74` defaults `--out` to `build/extraction-artifact.json` and
`:104-105` writes every parsed event there; `src/harness/findings_view.py:43-44` defaults `--out`
to the tracked `corpus/findings.md` and `:74-75` writes it. Neither reads `HELDOUT_SET`. D174 refuses
a held-out run's paths inside the checkout, D175 and D188 refuse held-out inputs inside it and print
to stdout alone, and D185 closed the same shape for `harness report` after the cross-project audit
had checked the run and agreement commands and not that one. These 2 entry points were not looked
at then either, and they are worse than what D185 closed: `harness report` needed an explicit
`--out` inside the tree, and these land there when only the input is named. After the reveal a
session may read the held-out transcripts and labels in place, so pointing either command at them
is an ordinary thing to do. The overwritten view is noticed by its own staleness check, for the
tracked default alone; the artifact and a view under `build/` are noticed by nothing.

Closure. The refusal the 4 commands share: in `harness.extract`, when any parsed call is declared in
`HELDOUT_SET` and `--out` resolves inside the repository, refuse naming the flag and write nothing;
in `harness.findings_view`, the same when any finding's id has the held-out shape
`harness.agreement.HELD_OUT_FINDING_ID` names or its call is declared. Each with a criterion and a
control, as D185's landed, and an absence-check reading for both artifacts (P5-4). Checked before
recommending: CI and the baseline run both commands on their defaults over the design set, which
the refusal does not touch; by the cross-project audit's list the held-out repository imports
`parse_call` and not this entry point, which nothing here can confirm.

**P5-3 (High by the prompt's definition, small in substance; by reading, after a search) — The reveal handover and a pushed commit message state a count of held-out calls carrying a named transcript value, and the handover states a second fact about what the held-out transcripts contain, in a document that says no held-out number is in this tree.** `[held-out content in prose] [rule with no mechanism]`

`sessions/HANDOVER-2026-09-18-held-out-reveal.md:41-43`, in item 1, says how many held-out calls
carry the settlement value the item is about, and commit `f562412`'s message repeats it in its
first bullet. `:54-55`, in item 2, says the held-out set uses an identifier shape the design
transcripts do not carry. `:9-11` and `:19-20` of the same document say no held-out number and no
held-out figure is in this tree. Each statement arrived as that side's note and was taken in as
written; the count is the kind of figure, and the value the kind of transcript text, that the
owner's rule keeps out of this tree, a commit and a commit message, and that D191 was worded to
avoid. **Whether the statements are true of the held-out set was given to the owner in the
conversation and is not recorded here.** Neither discloses a label, a band or a judge's answer, and
the value is one the design corpus also carries, which is why the substance is small.

The literal search of section 6 found nothing else: no held-out transcript text, label text,
identifier, score or hash in any tracked or ignored file, in any of 1,293 blobs or in any of 283
commit messages. What the tree does hold of that repository is chain metadata, recorded as that side
reported it and not content: the commit ids of C1, C2 and C3 and a digest of the run log, in
`HOLDOUT-OBLIGATIONS.md` and in the messages of `3a6f0fe` and `4adb18d`. The digest was recomputed
over the file in place and agrees. D191's qualitative sentences were checked against a
fresh held-out coverage and agreement run, in the conversation.

Closure. The owner's: reword item 1 to what the declaration needs — that a single declaration in
the register covers both sets, as that side reported — and item 2 to say only that catching up is
that side's work. The commit message is pushed, and this project's rules forbid rewriting pushed
history, so the instance is recorded rather than erased. The rule itself needs a mechanism, which
section 5 proposes: a search tool that carries no held-out string and builds its needles from the
6 files at run time, run at a phase's close by a session permitted to read them.

### Medium

**P5-4 (Medium, reproduced) — Several held-out artifacts have no reading in the absence check at all, and a run log reformatted by hand or quoted in part is not read as one.** `[backstop narrower than its rule]`

```
reformatted by hand, or quoted in part:
  run-log header, pretty-printed (json indent=2)        -> not reported
  run-log call record, pretty-printed                   -> not reported
  run-log blob records alone                            -> not reported   (a prompt blob carries the rendered transcript)
  a transcript's [events] table without its marker line -> not reported
held-out artifacts the tool has no reading for:
  agreement's held-out section                          -> not reported
  the labels' findings file, traces file, severity file -> not reported, all 3
  an extraction artifact over a declared call           -> not reported
```

Same probe and same 5 positive controls as P5-1. Mechanism:
`tools/check_holdout_absence.py:279-285` matches a record's kind and its manifest key or call id on
**one line**, so a record passed through `jq .` or `python -m json.tool` has them on different
lines; a `blob` record carries `blob_hash`, `content`, `field` and `record` and no `call_id`, so the
record that holds the rendered transcript is neither of the 2 kinds the reading knows; and the 4
shapes of `:234-254` include no label file, though `labels/findings.yaml` quotes transcript lines
verbatim in its evidence, and no agreement section, though D175 keeps held-out agreement out of
this tree. The criterion's own sentence names the header and the call record, so the tick stands
for what it says; the gap is between the 4 shapes and the rule they backstop.

Closure. Read run-log records as JSON values rather than as lines, and report a `call_id` naming a
declared call in any JSON object, which also reads an extraction artifact; read a label file by the
held-out id shape as a finding's `id` beside a `call_ref` naming a declared call, and a severity or
traces file by the same id shape in their own structure; read agreement's section by the heading its
renderer writes. Checked before recommending, over every file in the tree, ignored directories
included: each of the 3 discriminators as worded flags nothing today.

**P5-5 (Medium, reproduced) — `harness agreement` and `harness coverage` replay a held-out log without comparing the rubric hash its header names, so a log naming another rubric, or none, is scored.** `[requirement half-met] [refusal on 1 replaying command of 4]`

Reproduction, by the suite's own method: the design corpus split in 2 outside the checkout, 8 design
calls declared held out in a `HELDOUT_SET` of the probe's own, invented labels, and the committed
reference log re-headed 3 ways:

```
agreement  right-rubric-hash     exit=0  held-out section computed
agreement  another-rubric-hash   exit=0  held-out section computed
agreement  no-rubric-hash        exit=0  held-out section computed
run replay right-rubric-hash     exit=1  (gates fail over a seeded corpus, as designed)
run replay another-rubric-hash   exit=2  run refused: ... was recorded under rubric hash 0000… and this run names de66…
run replay no-rubric-hash        exit=2  run refused: ... was recorded under rubric hash none ...
```

Mechanism. `check_rubric_hash` is called at `src/harness/cli.py:698`, on `harness run`'s replay, and
at `src/harness/core/transport.py:1593`, on a resume. `_replayed_set` (`src/harness/cli.py:1627-1693`),
which both phase-5 commands replay through, checks only that a held-out log names a manifest
(`:1683-1686`). D186 chose a refusal with no override because the hash is the claim the labels are
scored against, and the 2 commands that score the labels are the 2 that never read it. An edit to a
judged entry's text is caught anyway, since the rendered request no longer hashes to a recorded one
and the replay stops part-way; an edit to a deterministic entry, or to an entry's `violating` or
`traces_to`, is not, because the deterministic tier is recomputed live and those fields reach no
prompt. HEAD is pinned to the freeze by test, so the default path cannot drift unnoticed today; a
`--rubric` flag, or the version-2 cycle D191 weighed, scores a version-1 log under another rubric
with nothing said. `tools/verify_phase5.py:147-152` says an edited working copy is caught where a
log is replayed or resumed, which is true of 1 replaying command of 4.

Closure. In `_replayed_set`, when `held_out`, refuse a log whose `rubric_hash` is absent or differs
from `rubric_hash` of the rubric file the command loaded, with a criterion clause and a control.
Checked before recommending: the suite's held-out fixture logs already carry the right hash, so the
refusal turns no existing test red.

**P5-6 (Medium, reproduced) — The absence check's loop over rendered reports can be removed with the suite green, and 6 more phase-5 lines can be removed or changed the same way; `--held-out-policies` is read by no test at all.** `[check with no control]`

Reproduction, by the control gate's method (section 4 has the instrument's own controls):

| mutation, one whole line each | fast phase-5 modules | the phase-5 selection of `tests/test_cli.py` |
|---|---|---|
| `tools/check_holdout_absence.py:443`: `main()`'s loop over `scan_reports` reads an empty mapping | survives, 24 passed | not read by it |
| the registered sibling, the loop over `scan_coverage_reports` at `:453` (positive control) | **killed** by `test_the_check_reports_a_coverage_report_in_the_tree_it_scans` | — |
| `src/harness/cli.py:1736`: agreement reads the held-out calls' policies from `--policies` alone | survives, 36 passed | survives, 39 passed |
| `src/harness/cli.py:1823`: the same line in coverage | survives | survives |
| `src/harness/coverage.py:213`: an entry with no traces row is not refused | survives | survives |
| `src/harness/coverage.py:215`: an entry with no readings is not refused | survives | survives |
| `src/harness/agreement.py:109`: a traces list naming one finding twice is accepted | survives | survives |
| `src/harness/agreement.py:130`: a frozen commit that is not a string is accepted | survives | survives |
| `src/harness/agreement.py:398`: the totals row prints misses in the false-alarm column | survives | survives |

Then the whole suite, once, with all 8 applied together, beside an unmutated copy: each copy failed
the same 6 tests, the ones that read git or enumerate tracked files and cannot answer in a copy with
no `.git`, and passed the same 1279. No test is red only with the mutations in, so each survives the
whole suite.

The first is the one that matters. D174 and D188 each landed a test that plants an artifact in a
tree and runs the check's `main()` over it
(`test_the_check_reports_a_held_out_run_log_in_the_tree_it_scans` and its coverage sibling, each
with a mutation entry on its loop); D185's 2 absence tests call `scan_reports` and
`_carries_a_held_out_report` directly, so the third shape can be unwired from the check while the
function-level tests stay green and the OK line goes on saying no report over held-out calls was
found. It is wired today: the report positive control of P5-1 went through the same function, and
`main()`, run in a copy of the tree over a planted report naming CALL-13, failed naming it and passed
once it was removed. `--held-out-policies` is named by no file under
`tests/` or `tools/`, on either command, so the flag can stop being read with nothing red; it works
today, since an invented held-out set computes the same figures with the flag naming the design
policies and is refused an empty directory. The 2 coverage refusals cannot be reached from the
command, which always passes every entry, and the 2 traces-shape refusals and the totals row are
each asserted by no test.

Closure. A `main()`-level test for a rendered report, with a mutation entry on `:443`, as its 2
siblings have; one test per command passing `--held-out-policies`, with an entry on each line; and
entries, or a recorded reason, for the other 5. Checked before recommending: none of these closures
moves a count the document guards pin except `control-mutations.yaml`'s own tagged total.

**P5-7 (Medium, measured) — The `Last swept` marker has moved with every decision since D168, so the phase-completion test will pass at phase 5's close whether or not anyone sweeps the specification.** `[mechanism measuring nothing] [prose true when written]`

The marker's history over the span, read from git: 22 values in 22 commits, D168 to D193, one per
decision, D181 to D184 arriving together under D185's bump. D129's test,
`test_a_closed_phase_handover_requires_the_sweep_marker_to_have_reached_it`, goes red when a
handover is marked closed and the marker is behind the last decision it cites; the reveal handover
cites nothing past D193 and the marker reads D193, so closing it today passes with no sweep
performed. `test_a_swept_marker_is_evidenced_by_the_changelog` asks that the newest changelog entry
name a decision at or past the marker, which a per-decision entry satisfies by construction. The
header (`specs/voice-agent-eval-harness.md:12`) still says the phase-completion clause is
mechanized, and D74 declined to demand a sweep claim per decision, which is what the marker now
makes. The builder's flag that the bumps from D188 to D193 rested on the `Not checked` block and
the changelog entry is consistent with what a sweep would have caught and did not: P5-8's caveat,
stale since the reveal, sits in the section a reader is told to read instead of the ticks, and the
README sentence in P5-6.

Closure. At phase 5's close, sweep the specification as a whole and record it as its own changelog
entry that says what was swept, rather than as a decision's bump. For the mechanism, either stop
moving the marker with decisions, so the accrued-count clause and D129's test measure something
again, or have D129's test require a sweep entry dated on or after the handover's close. Checked
before recommending: the second form has to be scoped to handovers closed from phase 5 on, since no
earlier close wrote such an entry.

### Low

**P5-8 (Low, by reading, with the run's output) — The phase-5 verifier's first caveat has been stale since the reveal.** `tools/verify_phase5.py:43-47` says the held-out section's real numbers wait for the reveal and that `JUDGED_AGREEMENT_PENDING` stays open until then. The reveal was 2026-09-18, the numbers were computed that day and are never committed (D175), and OB-7 records that what closes the set is undecided. D180's 2 history markers cannot see it. Closure: state the limit that is true now — the figures go to stdout and are never committed, so no tick reads them, and OB-7 is open.

**P5-9 (Low, reproduced) — Phase 2's firing tables and agreement's expected calls are 2 definitions of where a deterministic entry should fire, compared by nothing, and they differ on 1 call.** `tests/test_platform_checks.py:58` asserts `A-gated-write-without-verification` fires on CALL-12 and CALL-18; its `traces_to` names F-75 and F-80, both on CALL-18, so `harness agreement` prints the CALL-12 firing as the design set's one deterministic false alarm while phase 2's verifier ticks it as agreement with the gold set. Over the 26 entries read from 5 family tables it is the only difference. It is OB-49's effect inside one tier: the firing is sound, and the finding it answers is traced to another entry. The rubric is frozen, so the closure is a record: name it beside OB-49, and compare the 2 definitions in a test so a second difference is a decision.

**P5-10 (Low, reproduced) — A set with no banded finding cannot be covered.** Invented labels with every finding question-tier and an export with no rows: `coverage refused: the file states no cut critical_high, high_medium, medium_low`. D171 requires all 3 cuts, which need 4 scored findings, while the coverage requirement says the report shall count and name the findings carrying no band. No set is near it today. Closure: say so in D188's caveats, or let the loader accept no cuts where no row is scored.

**P5-11 (Low, reproduced) — D193's 2 checks leave a third kind of value unread, and the design corpus carries 3 of them.** `reason=window_closed`, `reason=booking_transferred` and `remedy=reversal_by_current_holder` appear in design tool results and in neither `corpus/entities.md` nor `specs/event-model.md`. D193's own argument is that the next value of an undeclared kind would pass the way the 2 it closed did. Its narrowness hides no gap of the 2 kinds it reads: no identifier-like token in the design transcripts escapes `_IDENTIFIER_TOKEN`, `settlement` is the only key naming a third party, and Class 5 backticks only `cardinal_pay`. Closure: declare the 3, or record why a result's vocabulary values stay outside D101.

**P5-12 (Low, by reading) — The README says agreement's held-out section needs every `--held-out-*` input, and `--held-out-policies` is one that is optional and named nowhere in it** (`README.md:95-97`). The default, `--policies`, is right for the present held-out set: its section computed over the design policies. Closure: name the flag and when it is needed.

**P5-13 (Low, by reading, with CI's run list) — The `[skip ci]` rule is recorded nowhere in this tree.** The 6 skipped commits each touch Markdown only, and CI's run list shows no code commit left beneath a skipped head without a run of its own: every code commit near them has a push or dispatch run on its own id. So the rule was kept. It lives in a machine-level file and a session's memory; nothing here would notice a code commit beneath a skipped head. Closure: state the rule in the README's CI section, and hold it with a `pre-push` check in `hooks/` that refuses a skipped head over any commit touching a non-prose path.

**P5-14 (Low, reproduced null) — The control gate's writer names no line ending.** `tools/verify_controls.py:145` and `:298` call `write_text` with no `newline`, so on Windows every mutated file in the gate's copy becomes CRLF, against the rule this span adopted with `.gitattributes`. Probed: all 10 entries whose mutated file is not Python, and 6 that are, stay green on a CRLF-only rewrite, so no local verdict is bought by a line ending today. Closure: `newline=""` on both, and nothing else.

**P5-15 (Low, reproduced) — D192 says no design finding is human-type, and 6 are.** Its caveats end: every uncovered and missed design finding is judge-type, and no finding is human-type (`specs/voice-agent-eval-harness.decisions.md:10224-10226`). The gold set holds 6 findings with `detectable_by: human` — F-27, F-31, F-49, F-56, F-59 and F-84 — all question-tier, so none carries a band, and all 6 are uncovered, which the report itself prints under its no-band heading. Both halves of the sentence are true of the **banded** findings only. A consequence for the fixtures: no test anywhere, by function or by command, exercises a detection-type row for `human` that is not 0, 0, 0. Closure: a correction attached to D192, as D160's and D162's were, since a record is not edited (D53).

**P5-16 (Low, reproduced) — A run log whose header lacks a key escapes `harness agreement`, `harness coverage` and `harness report` as a raw `KeyError`, exit 1; and the staleness refusal the first 2 print advises a flag they do not take.** The committed reference log with `artifact_hash` removed from its header: all 3 commands end in a traceback and exit 1, which is neither of the 2 codes agreement and coverage declare. `src/harness/core/transport.py:1439-1444` indexes the header's keys directly, and only the resume path catches `KeyError`. It is D167's defect one field over: a damaged log read as an error rather than refused by name. And the same log with its first record renamed is refused, exit 2, in replay's words, which end by offering `--allow-stale-replay`; `harness agreement --allow-stale-replay` is an argument error. D168 rewrote that message for the resume, which has no override either. Closure: raise `RunLogFormatError` for a header missing a key, and give the 2 commands the resume's wording.

---

## 3. Requirements against code, both directions

**Requirements to code.** The 4 `[P5]` requirements (`specs/voice-agent-eval-harness.md:154-157`)
were read clause by clause against `src/harness/agreement.py`, `src/harness/coverage.py` and the
commands in `src/harness/cli.py`.

| requirement clause | where it is met | held by |
|---|---|---|
| agreement per set, 5 counts per entry over the set's own calls | `count_entry`, `set_agreement`, `render_set` | 7 tests in `tests/test_agreement.py` and 9 in `tests/test_cli.py`; 20 entries mutate `src/harness/agreement.py` |
| a judged entry fires where its gate reads a violation | `judged_readings` reads `CallRollup.violated`, the gate's own property | 1 control, 1 entry. **One definition**: coverage reads the same `readings_for`, both sections of both commands call it, and the loader refuses `violating` on an `assert` entry (reproduced in memory), so a deterministic entry's reading and its gate's cannot part |
| labels breaking an invariant, or naming another frozen commit, refused | `check_held_out_labels`, 11 problems named at once | 11 entries, one per invariant |
| held-out run recognized by its calls; mixed, unflagged, malformed and no-`HELDOUT_SET` runs refused; manifest and rubric hash written and compared | `labels_manifest_problem`, `held_out_paths_inside`, `check_labels_manifest`, `check_rubric_hash` | D173's to D186's tests. **Half-met for the rubric hash**: compared on `harness run` and a resume, not where the labels are scored (P5-5) |
| a report over declared calls refused `--out` inside the repository | `report_command` | 2 tests, each with an entry |
| coverage: retired, uncovered, missed; per band and per detection type; no total; no-band findings named apart; held-out section only with all 6 inputs and to stdout; the listed refusals | `set_coverage`, `render_coverage`, `coverage_command` | 7 tests in `tests/test_coverage.py`, 9 in `tests/test_cli.py`; 20 entries mutate `src/harness/coverage.py`. Driven here over an invented held-out set, and each fired by name: an export its loader refuses, a band on text edited after scoring (the D189 recheck, on the held-out path), and a log answering none of the set's calls. The other listed refusals are held by the suite's tests |

Inputs that might compute nothing were driven through `harness coverage` over an invented held-out
set: an export banding none and a log answering no call are refused by name; traces tracing no
finding compute 0 traced and 0 retired in every band, which is what such labels say. No fail-open
was found in either command beyond P5-5.

**What the one-tier tracing convention does (OB-49), measured on the design set.** Both counts the
reveal handover gives hold: 64 traces from deterministic entries to assert-type findings, 19 from
judged entries to judge-type ones, none across. The held-out traces were read and follow the same
convention; their counts stay out of this report. Its effect on the design section is total rather
than marginal: **all 19 judged false alarms sit on calls that carry an assert-type defect-tier
finding**, so for a judged entry the false-alarm column cannot tell the judge flagging a call that
is in fact defective from the judge being wrong, and every assert-type finding a judged entry
answers stays outside that entry's hits and outside coverage's retired set. P5-9 is the same
effect inside the deterministic tier. Whatever closes OB-7 inherits this, which is a reason to take
OB-49's decision first.

**Held-out-only paths no invented fixture reaches.** The fixtures are the design calls renamed, so
they exercise ids, inputs and refusals and nothing that differs in content. Named: `--held-out-policies`
on both commands, which no test passes (P5-6); a detection-type row for `human` that is not 0, 0, 0,
since every human-type design finding is unbanded (P5-15); and a held-out log recorded live, with
`mode: live` in its header, where every fixture log says `replay` — neither command reads the mode,
so that one is a difference with no branch behind it.

**Code to requirements.** Behavior with no requirement behind it: `--held-out-policies` on both
commands (P5-6, P5-12); the `heldout-` prefix's dependence on the header's manifest is D184's and is
in the requirement. `harness.extract` and `harness.findings_view` sit under no `[P5]` clause, which
is P5-2's point: the rule the clauses apply to 4 commands has no sentence of its own.

**The 3 declarations.** Each names something this repository cannot assert: it holds no token for
the held-out repository and its CI cannot read that history. What then rests on that side's report
alone, since this session was not permitted to read that gate or its history: that C1, C2 and C3
landed in that order with the gate green at each; that the labels were first committed after the
tag and cite the frozen commit; that the manifest recomputes over the published labels, the
severity export among them; and that the manifest commit the run log's header names resolves there
and is the one that last touched the manifest before the log was committed. One link could be
checked from here and held: the digest `HOLDOUT-OBLIGATIONS.md` records for the run log is the
digest of the file in place.

---

## 4. Counts, enumerations, and the mechanisms that hold them

Every count in section 1 was recomputed rather than read, and each agreed with the document that
states it: the span's commits, files and insertions; 286 entries against the register's tagged 286;
64 and 19 traces; 116 identifier tokens; 83 rows and the 4 band sizes; 418 store records; the design
coverage and agreement tables against D188, D192 and the tests that pin them.

**The controls added since the freeze.** 170 entries, 160 of them mutating `src/` or `tools/` and
read by a test that calls the mutated code. 3 mutate a test module's own helper, which the control
calls rather than restates (`tests/test_obligations.py`, and D193's 2 in
`tests/test_corpus_hygiene.py`). None of the 3 shapes this project has found before was found again:
the gate reads a skip as unrunnable (`tools/verify_controls.py:199-204`), no new control reads a
committed artifact in place of the code its mutation changes, and none restates its rule beside the
check. The verifiers tick a criterion only when every named test's state is `pass`, so a skipped
test cannot tick (`tools/verify_phase2.py:429`).

**This session's sweep**, by the gate's method with bytes written back exactly. Its first run was
void, as the head of this report says; the results below are from the rebuilt tool, whose unmutated
baseline was green and whose 2 positive controls went red by name.

| instrument check | result |
|---|---|
| unmutated baseline, fast phase-5 modules (`tests/test_coverage.py`, `tests/test_agreement.py`, `tests/test_holdout_absence.py`, the 2 git-reading tests deselected because the copy has no `.git`) | green, 36 passed |
| unmutated baseline, the phase-5 selection of `tests/test_cli.py` | green, 39 passed |
| positive control: the registered mutation of the coverage loop in the absence check | **killed**, by name |
| positive control: D185's refusal removed from `report_command` | **killed**, by `test_a_report_over_held_out_calls_would_notice_an_out_path_inside_the_checkout` |
| 3 further mutations killed by name: a judged call with no verdict always read `not_applicable` (`test_a_judged_entry_would_notice_its_middle_verdict_read_as_a_pass`), a band left unsorted (`test_coverage_would_notice_its_bands_pooled_or_its_findings_misbanded`), the unplaced group dropped (`test_coverage_would_notice_an_unbanded_finding_left_out_or_counted_twice`) | the suite sees what it should |
| the 8 survivors of P5-6 | survive both selections; whole suite: 6 failed and 1279 passed in both the unmutated copy and the copy carrying all 8, the same 6 by name |

**Probes that came back null, each after a positive.** No control goes red on a CRLF-only rewrite of
its mutated file (P5-14; 16 entries). No input driven through `harness coverage` computed silently
over fewer findings, calls or entries than the set holds (section 3). The loader refuses `violating`
on an `assert` entry, so the deterministic gate's reading and agreement's cannot part. One content
hash, in `src/harness/core/severity.py:523`, read by the coverage report and by the suite; one rubric
hash, in `src/harness/core/rubric.py:831`; the interface scanner's list reading was read and run,
not mutated.

---

## 5. Mechanisms versus memory

| rule | enforced by | rests on memory |
|---|---|---|
| no held-out transcript, run log, report or coverage section in this tree | `tools/check_holdout_absence.py`, on every CI run, for UTF-8 files in the 4 shapes | everything outside them: another encoding (P5-1), a label file, an agreement section, an extraction artifact, a blob record, a reformatted record (P5-4) |
| a command reading held-out inputs writes nothing inside this tree | refusals in `run`, `report`, `agreement`, `coverage`, each with a control | `harness.extract` and `harness.findings_view` (P5-2); any shell redirect |
| **no held-out figure, label or transcript value in a decision, a handover or a commit message** | nothing | every session that writes about the held-out set. P5-3 is what that costs: the one instance was written the day after the reveal, by a careful session, in the document that says the tree holds none |
| a held-out log is scored under the rubric it was judged under | `check_rubric_hash` on `run` and resume; the HEAD pin test | agreement and coverage (P5-5) |
| `[skip ci]` only over prose-only pushes | nothing in this tree | the session pushing (P5-13); kept so far, 6 of 6 |
| CI runs kept sequential across sessions | the workflow's concurrency group cancels an older run on the same ref, which is how the 2 canceled runs in section 1 ended | courtesy, for runs on different refs |
| a sweep at phase completion | D129's test | the sweep itself (P5-7) |
| the 3 gate-asserted criteria | the held-out repository's gate, as reported | this repository's knowledge of it |

**A mechanism for the rule that has none.** The instrument section 6 describes carries no held-out
string: it builds its needles from the 6 files when it runs. It could be kept in this tree, or
beside the held-out repository, and run at a phase's close, and before any push that touches prose
about the held-out set, by a session permitted to read those files. It cannot see a paraphrase, and
it found P5-3's statements only because a reader went looking after it came back clean; what it
removes is the literal leak, which is the irreversible one.

---

## 6. Held-out content

**What was read**, in place and nothing else in that repository: `labels/findings.yaml`,
`labels/traces.yaml`, `labels/severity.json`, every file under `transcripts/`, `CORPUS_VERSION`, and
the run log under `runs/` whose name starts `heldout-`. No specification, tool, test, session or
commit history there was opened, and no directory there was listed beyond those paths.

**How this tree was searched.** A script under the scratch directory built 3 kinds of needle from
those files when it ran: **36,942** word 6-grams of normalized text (lowercased, every
non-alphanumeric run a space, so re-wrapping, case and punctuation do not matter), taken from the
transcripts raw and with wrapped rows rejoined, from the 3 label files and from the run log's
response texts; **676** single words; and **118** identifier-shaped values — record ids, addresses,
numbers, hashes, scores and the version string. A needle was dropped only when the shared convention
sources carried it as they stood **at the freeze commit, read from git rather than from the working
tree**, so a later leak into them could not hide itself: the design transcripts, policies, rubric,
prompt template and the 2 format specifications. 482 6-grams were dropped that way, and what they
were was listed by path and read: the recording disclosure, policy clauses, tool-call skeletons and
the rubric's own wording. The haystacks: **200 files** of the working tree with ignored directories
included (`build/`, `private/`, `.cj-store/`, `runs/`), decoded by byte-order mark so a UTF-16 file
could not hide from it; and **every object in the repository's store** — 1,293 blobs, 283 commits
and 4 tags, unreachable ones included — so the specification's whole history and every commit
message were read, not only the span's.

**How the search was shown able to find something, first.** Strings taken from the held-out files
were planted in a directory and a 2-commit repository **outside** this tree: a label sentence
verbatim; the same sentence upper-cased, re-punctuated and re-wrapped at 38 columns behind quote
markers; the same in UTF-16; one transcript row; one booking reference with one score; the sentence
in a file committed and then deleted; and the sentence in a commit message. All 7 were reported. A
paraphrase planted beside them was **not**, which is the instrument's limit and why the prose was
also read.

**What it found.** No 6-gram from a transcript or a label, no identifier, no score, no hash and no
held-out-only name in any file, blob, commit message or tag, beyond structural coincidences between
2 corpora authored to one convention (tool-call skeletons, timing columns, the findings' house
style), each read and dismissed by eye, and this repository's own public values, which the held-out
files legitimately cite (the frozen commit and the template hash). The one held-out-derived value
present is the C1 commit id of section 2's P5-3. The test fixture `SYNTHETIC_HELDOUT` in
`tests/test_holdout_absence.py` is invented, as it says.

**What was read by eye**, because no search finds a paraphrase: every commit message in the span in
full; D173 to D193 and the `Not checked` block; the 3 handovers; O-9 to O-11 and the standing duty in
`HOLDOUT-OBLIGATIONS.md`; the README's held-out paragraphs. P5-3 is what that reading found.
Pre-span prose describing the held-out transcripts' structure (D83 to D86 and O-1 to O-8) was
sampled, not swept: it predates the labels, was written under earlier rules and read by earlier
audits.

**This report carries none.** It names no held-out finding, figure, band or line; the ids it uses
are ones `HELDOUT_SET` declares, used as the suite's fixtures use them. The absence check and the
fast document checks were run over it before it was committed.

---

## 7. What was not checked

- **The held-out repository beyond the 6 inputs**, by the prompt's rule: its gate, tools, tests,
  specifications, sessions and history. Everything section 3 lists under the 3 declarations
  therefore rests on that side's report.
- **`comparative-judgment`**: only its 2 specification files, read by the interface scanner in the
  baseline. Its D35 and D36, which D172 and D190 rest on, were not read.
- **`private/`** was searched by the needle script and by the absence check and opened by neither
  this session's reader nor its editor; the populated `.env` was not read.
- **2 deviations from the prompt's reading rule, both before or beside the audit proper and both
  free of held-out content**: the session opened its own project memory folder's 2 notes at start,
  before it had read the rule against opening a memory folder; and it compared `.cj-store` with the
  backup directory beside the checkout using `cmp`, reading nothing.
- **Whether D191's diagnosis is right**, as opposed to whether its sentences match the held-out run:
  the second was checked in the conversation; the first is a judgment about why entries did not
  engage, and this session re-derived only the statuses.
- **The whole suite under each surviving mutation** was run once with the survivors applied
  together, not once each.
- **The owner's own terminal**: which encoding its redirect writes depends on its profile, which
  this session did not read. Both encodings a PowerShell 5.1 redirect can write here were measured.
- **Pre-span prose about the held-out transcripts** was sampled only (section 6).
- **`check_spec_interface.py`'s list reading** (D178) was read and run, not mutated; its 12 entries
  were taken from the control gate's pass.
- **Spelling, counts and identifiers in this report** are held by the checks run over it, not by a
  second reader.
- **This session's logs and probe scripts were not kept.** Its scratch directory was emptied at
  03:53 local time on 2026-09-19, by another process starting in this project, after every result
  above had been recorded and 1 minute after this report was written. The planted held-out
  controls of section 6 went with it, which is no loss. The appendix carries 2 snippets written
  afresh afterwards and run from a clean start, so P5-1, P5-4 and P5-5 can be re-run without it;
  every other reproduction above gives its command, input and output in place.

---

## 8. Suggested order of work

**Before phase 5 can close:**

1. **P5-3** — the owner's decision on the handover's 2 sentences and on how the instance is
   recorded, since the handover is the document being closed.
2. **P5-1, then P5-2** — the encoding fix and the fail-closed read, then the 2 refusals. These are
   the irreversible direction, and phase 6 opens with sessions that may read the held-out files.
3. **P5-5** — one refusal in `_replayed_set`, before anything else scores a held-out log.
4. **P5-8** and the README sentence of **P5-12**, with the sweep P5-7 asks for, which is what
   closing the handover claims; then the handover marked closed, OB-46 closed, and OB-47's trigger
   read.

**Can follow the close:** P5-4's readings, which P5-1's fail-closed read makes less urgent; P5-6's
controls; P5-7's mechanism; P5-9 beside OB-49 at phase 6's opening reading; P5-10, P5-11, P5-13 and
P5-14.

**Deferred rows, and whether anyone will notice their triggers.** OB-47 fires when the reveal
handover is marked closed, an act performed by editing the document that lists it as item 4. OB-49
fires at phase 6's opening reading, which OB-47 is. OB-48 fires when phase 7 opens, and the
specification's own phase-7 scope and section carry D191's widening, so the reading that opens the
phase meets it without the register. OB-5 and OB-16 are read by a person and say so. OB-7 is open,
correctly: held-out agreement is measured and never committed, so what closes
`JUDGED_AGREEMENT_PENDING` is a decision about evidence, and P5-9 and OB-49 both bear on what that
evidence would count.

---

## Appendix — 2 reproductions that stand on their own

Each runs from the repository root as `uv run python <file>`, reads design data only, writes only
under the system's temporary directory and spends nothing. Both were run from a clean start after
the session's scratch directory was lost, and printed what follows them.

**P5-1 and P5-4 — what the absence check reads, by encoding and by layout.**

```python
import importlib.util, json, sys, tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location("absence", "tools/check_holdout_absence.py")
absence = importlib.util.module_from_spec(spec)
sys.modules["absence"] = absence
spec.loader.exec_module(absence)
held = frozenset(absence.declared_held_out_set())
declared = sorted(held)[0]

report = Path("snapshots/report.md").read_text(encoding="utf-8").replace("CALL-01", declared)
records = [
    json.loads(line)
    for line in Path("runs/reference-corpus-0.6.0.jsonl").read_text(encoding="utf-8").splitlines()
]
call = dict(next(r for r in records if r.get("record") == "call"), call_id=declared)
blob = next(r for r in records if r.get("record") == "blob" and r.get("field") == "prompt")

cases = {
    "report, UTF-8 (positive control)": report.encode("utf-8"),
    "report, UTF-8 with a byte-order mark": b"\xef\xbb\xbf" + report.encode("utf-8"),
    "report, UTF-16": report.encode("utf-16"),
    "call record, one line (positive control)": json.dumps(call).encode("utf-8"),
    "call record, UTF-16": json.dumps(call).encode("utf-16"),
    "call record, indented": json.dumps(call, indent=2).encode("utf-8"),
    "prompt blob record alone": json.dumps(blob).encode("utf-8"),
}
for name, data in cases.items():
    with tempfile.TemporaryDirectory() as scratch:
        (Path(scratch) / "artifact.txt").write_bytes(data)
        seen = absence.scan_reports(Path(scratch), held) or absence.scan_run_logs(
            Path(scratch), held
        )
        print(f"{name:<42} {'REPORTED' if seen else 'not reported'}")
```

```
report, UTF-8 (positive control)           REPORTED
report, UTF-8 with a byte-order mark       not reported
report, UTF-16                             not reported
call record, one line (positive control)   REPORTED
call record, UTF-16                        not reported
call record, indented                      not reported
prompt blob record alone                   not reported
```

**P5-5 — agreement over a held-out log naming another rubric's hash, or none.** The suite's own
method: the design corpus split in 2 outside the checkout, 8 design calls declared held out in a
`HELDOUT_SET` of the probe's own, one invented label, and the committed reference log re-headed.

```python
import contextlib, io, json, shutil, tempfile
from dataclasses import replace
from pathlib import Path

import yaml

from harness import cli
from harness.agreement import RUBRIC_FROZEN_V1
from harness.checks import build_registry
from harness.core.findings import dump_findings, load_findings
from harness.core.rubric import load_rubric, rubric_hash

held_calls = tuple(f"CALL-{n:02d}" for n in range(1, 9))
work = Path(tempfile.mkdtemp())
for side in ("design", "held"):
    (work / side).mkdir()
for path in sorted(Path("corpus/transcripts").glob("*.txt")):
    shutil.copy(path, work / ("held" if path.stem in held_calls else "design"))
(work / "HELDOUT_SET").write_text("\n".join(held_calls) + "\n", encoding="utf-8", newline="\n")
shutil.copy("corpus/CORPUS_VERSION", work / "CORPUS_VERSION")
cli._HELDOUT_SET = str(work / "HELDOUT_SET")

invented = "HF-" + "01"
borrowed = load_findings(Path("corpus/findings.yaml"))[0]
(work / "findings.yaml").write_text(
    dump_findings((replace(borrowed, id=invented, call_ref="CALL-08"),)),
    encoding="utf-8",
    newline="\n",
)
rubric = load_rubric(Path("rubric.yaml"), build_registry().keys())
(work / "traces.yaml").write_text(
    yaml.safe_dump(
        {
            "rubric-frozen-v1": RUBRIC_FROZEN_V1,
            "traces": {
                e.id: ([invented] if e.id == "A-record-fields-disagree" else [])
                for e in rubric.entries
            },
            "uncovered": [],
            "calls_without_findings": [c for c in held_calls if c != "CALL-08"],
        }
    ),
    encoding="utf-8",
    newline="\n",
)

lines = (
    Path("runs/reference-corpus-0.6.0.jsonl").read_text(encoding="utf-8").splitlines(keepends=True)
)
header = dict(json.loads(lines[0]), labels_manifest="a" * 40)
for name, rubric_hash_named in (
    ("the right hash", rubric_hash(Path("rubric.yaml"))),
    ("another rubric's hash", "0" * 64),
    ("no hash", None),
):
    head = (
        dict(header) if rubric_hash_named is None else dict(header, rubric_hash=rubric_hash_named)
    )
    log = work / "heldout-probe.jsonl"
    log.write_text(json.dumps(head) + "\n" + "".join(lines[1:]), encoding="utf-8", newline="")
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        code = cli.main(
            [
                "agreement",
                "--transcripts",
                str(work / "design"),
                "--held-out-transcripts",
                str(work / "held"),
                "--held-out-corpus-version-file",
                str(work / "CORPUS_VERSION"),
                "--held-out-run-log",
                str(log),
                "--held-out-findings",
                str(work / "findings.yaml"),
                "--held-out-traces",
                str(work / "traces.yaml"),
            ]
        )
    print(
        f"header naming {name:<22} exit={code}  section computed={'held-out set: 8 calls' in out.getvalue()}"
    )
shutil.rmtree(work)
```

```
header naming the right hash         exit=0  section computed=True
header naming another rubric's hash  exit=0  section computed=True
header naming no hash                exit=0  section computed=True
```
