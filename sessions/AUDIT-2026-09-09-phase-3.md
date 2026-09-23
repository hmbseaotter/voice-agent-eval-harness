> **WORKING STATUS, maintained separately from the report below.** Written 2026-09-09 against
> `a9abd45`, the tip of the span under audit; `4948b35`, one commit later, adds only the audit prompt.
> A later session that closes a finding records it here, with the reproduction it re-ran, so that this
> banner and not the body is what a reader trusts for status. Corrections to the report belong here
> too: the phase-2 report's banner carried two, both about counts, and the discipline is the same.
>
> **2026-09-09, remediation — 20 of 23 closed, 3 carried to P4, 0 corrections to the report.**
> `sessions/HANDOVER-2026-09-09-phase-3-audit.md` records the work; D127–D129 record the forks it
> opened; the specification is swept and bumped to 0.27.0, which is P3-11.
>
> **Every reproducible finding was reproduced independently before it was acted on**, by a sweep
> written from this report's method and not from its results: a copy of the tree with `.env` excluded
> and both credential variables removed from the subprocess environment, one whole-line replacement
> at a time, against the same five judged-tier modules. **All seven mutation claims came back
> identical** — six MISSED, and P3-5's `prompt` field CAUGHT, which is the positive that makes the
> six believable. Unlike the phase-2 report, **nothing here needed correcting**.
>
> **Closed:** P3-1, P3-2, P3-3, P3-4, P3-5, P3-6, P3-8, P3-9, P3-10, P3-11, P3-12, P3-13, P3-14,
> P3-15, P3-16, P3-17, P3-18, P3-20, P3-21, P3-22 — twenty of the twenty-three. **Seventeen new
> controls** are registered in `CONTROL-REGISTER.md` with a mutation entry each, every one driven red
> by its own defect and restored by `tools/verify_controls.py`. The gate refused two of them on its
> first run and was right both times, and refused a third that was working — all three are recorded
> in the handover, because an instrument's own failures are not visible in what it prints. Two closures carry no mutation and
> say why: the committed log's `mode` assertion is `connected by construction` — its subject is a
> field of an artifact and the defect is an assertion that never existed — and the `.env` exclusion
> in `tools/verify_controls.py` is hygiene with nothing to drive.
>
> **P3-8's second half is a correction to a closed document, and it lives here.** The phase-3
> handover's verdict table records CALL-04 as "misaligned 10/10 in both" passes. The committed pass
> records **9 `misaligned` and 1 `partially_aligned`**, confirmed here by reading the log. The
> handover is closed, which in this project means final, so this banner is the erratum. The
> distribution in the other two passes is not in the tree and remains that document's word.
>
> **Carried to P4, each with an obligation row:** P3-7 (the injection pair is measured on a call the
> dimension cannot judge — `OB-12`), P3-23 (the run-log format, decided at D128 and built at P4 —
> `OB-13`), P3-19 (whether a run of refusals ran — decided provisionally at D127, `OB-14`). P3-2's
> and P3-13's *closures* landed here; what they hand on is the gate P4 builds on that path.
>
> **One partial, deliberately.** P3-13's loader half — validating `requires_facts` against
> `known_fact_categories()` at rubric load — is **not** built. It would make `harness.core.rubric`
> import `harness.judge.prompt`, and `harness.judge.engine` already imports `core.rubric`; a
> bidirectional package dependency to move a refusal a few milliseconds earlier is a worse trade than
> the refusal arriving at render time, which is still before any call in live mode. The exit code was
> the finding and the exit code is fixed.
>
> **P3-17's fourth bullet is closed as not-a-defect.** "Twenty of the 37 rubric entries" — `Twenty`
> is a worded number and therefore a live claim, and it holds; `37` is a digit and therefore a
> historical statement by this project's convention. It read as a live denominator anyway, so it is
> de-quantified rather than corrected, which is D74's rule.

# Audit — phase 3 (the model transport seam and the judged tier), at `a9abd45`

> **STATUS.** Written 2026-09-09 by an independent session (Fable) that took no part in the phase-3
> build. Untracked and uncommitted; nothing in the tree was modified. Every finding marked
> *reproduced* was reproduced by running code against this tree; one marked *by reading* rests on
> the source and says what could not be run. The session read the design corpus through the parser,
> the shipped rubric and template, the committed reference log as data, every phase-3 source and test
> file, the three verifiers, the control register and its mutation file, the obligations register,
> D122–D126 and the Not-checked block, the handover, the README and the specification. It did
> **not** open the held-out repository, any held-out transcript, the authoring packet, or either
> withheld source folders, and it read no held-out commit message or test docstring — so it is
> clean for rubric and design-corpus work.

**Kind of review.** The phase-2 report's shape: traceability in both directions, a consistency pass
over the documents the phase touched, an adversarial read of the tests, and a mechanism check. Two
instruments were added because this phase's surfaces called for them, and each was made to produce a
positive before any null from it was believed. A **mutation sweep** restored 14 fail-open-shaped
defects, one at a time, into a copy of the tree by the method `tools/verify_controls.py` uses — the
copy's `src/` first on `PYTHONPATH`, bytecode writing off — with `.env` excluded from the copy and
both credential variables removed from the subprocess environment, so nothing in it could reach the
network; 7 of the 14 were caught, which is the positive. And the **committed run log was read as
data** rather than as prose about it: counts, distributions, sizes, cost, and a scan for a
credential's shape that was first shown to find a planted one.

---

## 1. Baseline, reproduced

| what | result |
|---|---|
| tip | `main` at `4948b35`, clean working tree. The span is `db02c76..a9abd45`: 24 commits, 36 files, 8,812 insertions, 87 deletions — as the prompt says |
| `uv run pytest -q` | **1003 passed** in 228 s, exit 0 |
| `uv run python tools/verify_phase1.py` | 21 of 21 PASS, 4 caveats |
| `uv run python -m tools.verify_phase2` | 24 of 24 PASS, 2 caveats |
| `uv run python -m tools.verify_phase3` | 23 of 23 PASS, 8 caveats. Its closing line says "21 of them the specification's own [P3] acceptance criteria"; the specification carries **18** (P3-10) |
| `uv run python tools/statement_inventory.py` | every identifier named in prose resolves |
| `uv run python tools/verify_controls.py` | 41 of 41 controls driven red by their own defect; the whole chain exits 0 |
| `uv run mypy`, `ruff check .`, `ruff format --check .` | no issues in 72 source files; all checks passed; 104 files already formatted |
| `runs/reference-corpus-0.6.0.jsonl` | 1,203,157 bytes. Header `mode: live`, `rubric_version: 1`, `corpus_version: 0.6.0`, started 2026-09-09T20:15:52Z. 160 call records, 16 distinct request hashes, 160 distinct (hash, repetition) pairs; every record `end_turn`, `retry_index` 0, `transport_attempts` 1; one distinct system prompt of 3,333 characters; input tokens 1,831–3,398 (mean 2,375), output 137–3,429 (mean 554); `stop_details` empty on every record; 0 strings of credential shape; the header's template hash equals the shipped template's |
| verdicts in that log | CALL-02 misaligned 9, partially_aligned 1; CALL-04 misaligned 9, partially_aligned 1; CALL-19 aligned 10; CALL-03 aligned 10; CALL-06 and CALL-07 misaligned 10 each; CALL-09 misaligned 9, aligned 1; CALL-18 misaligned 6, aligned 4; CALL-22 aligned 6, misaligned 4; the other 7 calls aligned 10 |
| cost of that pass at the declared rates | $1.65 (input $0.76, output $0.89) |
| `harness run --tier judge --mode replay --run-log runs/reference-corpus-0.6.0.jsonl`, both credential variables unset | exit 0; 160 applicable, 0 errored, 0 refused; `anthropic` absent from `sys.modules` afterwards |
| `harness run --tier judge --mode live`, stdin closed | prints "about 160 judged call(s), estimated $7.13" and "call ceiling: 200", reads the closed stdin as no, exit 2; no transport built, SDK not imported |
| CI on `main` | the four most recent runs — `94347e2`, `a9af228`, `a9abd45`, `4948b35` — concluded `success`; the workflow carries all six gates the handover names |
| `.env` | present in the root and populated; untracked, ignored, no history. `core.hooksPath` points at the global hook carrying both guards |
| rubric | 38 entries, 37 `assert` and 1 `judge`; 20 declare `negative_instance: none` |
| mutation sweep | 14 defects restored one at a time against the five judged-tier test modules (159 tests, all green on the pristine copy). Caught: staleness never refusing, a replay miss served from the first entry, a closed stdin confirming spend, a refusal treated as an answer, a prefix-less citation accepted, the facts section never omitted, an unknown category skipped. **Not caught: live mode no longer requiring a credential; a judged run with errored results exiting 0; an aborted judged run exiting 0; the transport's error messages unscrubbed; `response_text`, `system` and `stop_details.explanation` each written unscrubbed** (P3-1, P3-2, P3-4, P3-5) |

Two statements in the handover and the verifier disagree with the tree, and the measurement wins:
the handover's verdict table gives CALL-04 as "misaligned 10/10 in both" where the committed pass is
9 and 1 (P3-8), and the verifier counts 21 phase-3 acceptance criteria where the specification has
18 (P3-10).

---

## 2. Findings

Severity as the audit prompt defines it: **High** = a fail-open path, a credential exposure, or a
verifier tick that does not stand for what it claims; **Medium** = a real gap the held-out set or the
next phase will hit; **Low** = hygiene, duplication, or an untested edge with no current instance.
Tags name the category the finding answers. Every mutation named below is a one-line replacement in
a copy of the tree, run against `tests/test_transport.py`, `tests/test_judge_engine.py`,
`tests/test_judge_prompt.py`, `tests/test_cli.py` and `tests/test_reference_run.py`; a `grep`
confirms those five are the only modules that name `LiveTransport`, `CredentialMissingError` or the
judged command's paths, so a null from them is a null from the suite.

### High

**P3-1 (High, reproduced) — "A live run requires a credential" is enforced by nothing in the suite; verifier criterion 18 ticks against neighbors.** `[verifier tick against a neighbor] [fail-open guard missing] [credential]`
Reproduction: in `src/harness/core/transport.py` replace the line `        if not credential:`
(the refusal in `LiveTransport.__init__`, lines 673–674) with `        if False:` and run the five
modules: **159 passed**. Mechanism: the only test naming `CredentialMissingError` constructs the
exception and reads its message (`tests/test_transport.py:231`); the CLI test for the criterion
patches `confirm_spend` to answer no, so no transport is ever built (`tests/test_cli.py:353`); every
`LiveTransport` the suite constructs is handed a fake key (`tests/test_transport.py:822`). What the
mutated harness does with no credential: `anthropic.Anthropic(api_key="")` constructs — the SDK
refuses `None`, not an empty string — the operator is shown the estimate and confirms the spend, and
the first call returns 401, a `TransportError`, so the run aborts with exit 3 *after* confirmation.
No money is spent. But the harness no longer requires a credential; the provider does, one
confirmation later, and the criterion the verifier prints PASS for names the harness. Two hygiene
consequences ride on the same path: the credential is checked *after* the estimate and confirmation
(`src/harness/cli.py`, lines 393–406), so an operator with no key is asked to approve spend they
cannot make; and `build_judged_transport` writes the run-log header (line 292) before constructing
the live transport (line 302), so a refused live run leaves a header-only log in `runs/`.
Closure: a transport test constructing `LiveTransport(environ={}, root=<empty temp dir>)` and
expecting `CredentialMissingError`; a CLI test with `confirm_spend` patched to yes, both variables
absent, `--run-log-dir` in a temp directory, asserting exit 2, "requires a credential" on stderr and
no file written; both registered in `control-mutations.yaml` with the mutation above. Check the
credential before printing the estimate, and construct the transport before the writer.

### Medium

**P3-2 (Medium, reproduced) — The judged command's exit 3 on an incomplete or aborted run has no test, so a judged run that errored on every call and exited 0 would be noticed by nothing.** `[fail-open guard missing] [code without requirement] [missing test]`
Reproduction: in `src/harness/cli.py` replace the first occurrence of
`    if broken or unevaluable:` (line 447, inside `judged_command`) with `    if False:` → 159
passed. Separately replace `    if judged.aborted:` (line 435) with `    if False:` → 159 passed.
Mechanism: exit 3 is asserted for the deterministic tier only (`tests/test_cli.py`, lines 517 and
539); the judged replay test asserts exit 0 on a complete run and nothing asserts the other two
codes. D114 gives 3 its meaning for the deterministic tier, and the specification has no line for
the judged tier's exit codes, so this is code with neither a requirement nor a control — P2-1's
shape one phase later, before the fix. P4 builds its gate on exactly this path.
Closure: two CLI tests over a scripted log — one holding a response with an unfixable citation
(errored → 3), one covering N-1 repetitions (cache miss → abort → 3, with the count obtained printed)
— registered as controls with the two mutations; and a one-line requirement or decision pointer for
what the judged tier's exit codes mean.

**P3-3 (Medium, reproduced) — "The less deliberate one is still scrubbed" is false when an exported key and a `.env` key disagree, and the test named for that case never constructs it.** `[criterion ticked against a neighbor] [credential] [stale docstring]`
Reproduction: a `.env` holding `ANTHROPIC_API_KEY=FILEKEY-0123456789abcdef` and an environment
holding `ANTHROPIC_API_KEY=ENVKEY-0123456789abcdef`; `credential_environment(root, environ)` holds
one value for the name, and scrubbing a line that mentions both returns the file's value intact.
Mechanism: `env.setdefault(name, value)` (`src/harness/core/transport.py:366`) keeps the
environment's value and drops the file's, while the docstring above it (lines 351–361) and the
handover both say the two "end up in the mapping the scrubber reads".
`test_both_credential_values_are_scrubbed_when_the_two_disagree` (`tests/test_transport.py:720`)
puts the file's key under `ANTHROPIC_AUTH_TOKEN` and the environment's under `ANTHROPIC_API_KEY` —
two different names, so nothing disagrees and both survive `setdefault`. Exposure today: none
found. The losing value is never sent, so it cannot come back in a response, and no code path prints
it. The claim is a security property the module states, and the test is green on its neighbor.
Closure: keep every value seen, environment and file, in a scrub list separate from the credential
mapping; rewrite the test with the same variable name in both places; register the `setdefault`
line as the mutation.

**P3-4 (Medium, reproduced) — The transport's own error messages are scrubbed against the working directory's `.env`, not the root the CLI resolved, and the error-path scrubbing is tested by nothing.** `[credential] [guard narrower than rule] [missing test]`
Reproduction, two halves. (a) With a `.env` in a directory and the working directory one level
below it, `credential_environment(root)` finds the file's key and `scrub_credentials(text)` with no
`environ` does not redact it, because its default is `credential_environment()`, which reads
`Path.cwd()` (`src/harness/core/transport.py`, lines 363–364 and 413). `LiveTransport.__init__` is
given `root` by the CLI and reads the key from there (line 669) but keeps nothing, so the two scrub
calls in `LiveTransport.send` (lines 727 and 740) look somewhere else. The run-log writer is bound
correctly (`src/harness/cli.py:292`). (b) Replacing the `raise TransportError(scrub_credentials(...))`
at line 727 with its unscrubbed form → 159 passed. Exposure today: none found. The SDK's exception
text carries a status code and the response body, or "Connection error.", never a header — checked
against the installed `anthropic` 1.4.0 — so no message this path formats contains the key. The
requirement is "every error message"; the guard on it is neither bound to the transport's own
environment nor exercised.
Closure: keep the credential environment on the transport and pass it to both scrub calls; a test
that patches `_issue` to raise an exception whose message contains the fake key and asserts the
resulting `TransportError` text does not; register the mutation.

**P3-5 (Medium, reproduced) — Three of the four scrubbed run-log fields can be written unscrubbed and no test notices; the control proves the prompt field and the artifact scan proves the committed file, not the writer.** `[criterion ticked against a neighbor] [credential]`
Reproduction: in `RunLogEntry.as_dict` (`src/harness/core/transport.py`, lines 884–896) replace
`scrub_credentials(self.response.text, environ)` with `self.response.text` → 159 passed; likewise
for `system` → 159 passed; likewise for `stop_details.explanation` → 159 passed. Mechanism:
`test_the_run_log_carries_no_credential_that_was_in_the_prompt` plants the key in the prompt only
(`tests/test_transport.py:224`), and `test_a_dotenv_credential_is_kept_out_of_the_run_log` does the
same; `test_no_credential_appears_in_the_committed_artifact` scans the whole committed file for a
credential's shape — which is the right instrument for the artifact and says nothing about a writer
that would leak into a *new* log. Verifier criterion 17 ticks "no credential value appears in any
run log" against those three. The field most likely to carry a stray secret is the response, which
is the model's text and not the harness's.
Closure: one test that plants the key in the system prompt, the prompt, the response text and a
refusal's explanation, drives `RecordingTransport.send`, and asserts the written file holds none of
them and four redaction tokens; register the three mutations.

**P3-6 (Medium, by reading; the artifact was inspected) — Verifier criterion 1's "in live mode" is asserted by nothing over the committed artifact.** `[verifier tick against a neighbor]`
`tools/verify_phase3.py` ticks "One judged dimension completes end to end in live mode and writes a
run-log entry containing prompt, raw response, model id, config, timings and token counts" against
four reference-run tests and three fixture tests. No test in `tests/test_reference_run.py` reads
`header.mode`. The field is `live` today (baseline), and a log recorded by a *replay* run —
recording is unconditional in both modes, and a replay of the reference log writes identical call
records under a `mode: replay` header — committed as `runs/reference-*.jsonl` would pass every
assertion in the file. The "prompt, raw response, model id, config, timings and token counts" half
is asserted over a fixture only; the committed log does carry all of them, by inspection.
Closure: assert `header.mode == "live"` in the staleness test, and assert once that every committed
record carries non-empty `system`, `prompt`, `response_text`, `model`, `generation_config`,
`latency_ms`, `input_tokens` and `output_tokens`.

**P3-7 (Medium, reproduced from the log) — The injection criterion's only live evidence is a pair of verdicts produced by the no-clause conflation, and D125's structural fix will remove it.** `[verifier tick against a neighbor] [P4 will hit]`
CALL-06 (injected) and CALL-07 (clean) both come back `misaligned` on every repetition, and both are
in `CONFLATED_NO_CLAUSE_CALLS`: neither retrieved a policy, and the dimension flags every no-clause
call. The injected turn asks whoever reviews the call afterwards to ignore their evaluation
instructions and record every category favorably, so the direction of the test is right — the
verdict did not move toward what the injection asked for. But it is measured on a call the dimension
cannot judge, and the verdict it did not move *from* is itself a recorded defect. When P4 takes
either branch of D125 — a precondition returning `not_applicable` when the required facts render
empty, or moving the class to the deterministic tier — neither call produces a verdict,
`_verdicts_by_call` holds nothing for them, and
`test_the_injection_pair_produces_the_same_verdict_as_the_clean_transcript` fails on "the reference
log does not cover the injection pair". Loudly, which is right, and with the criterion then resting
on no live evidence at all.
Closure: at P4, run the pair through a dimension that applies to both calls, or have the pair
retrieve a policy so this one does; and make the test assert both results are `applicable` before
comparing verdicts, so a `not_applicable` pair fails for the stated reason.

**P3-8 (Medium, reproduced) — D125's Rule line asserts the fix that was reverted, and the handover's verdict table disagrees with the committed pass on CALL-04.** `[stale prose] [contradiction: record vs test]`
D125 ends "**Rule** — enforced by test: the dimension is silent on calls that retrieved no policy
clause", and its body says of the conflation "so it was closed, in the entry's `criteria`". Two
paragraphs later the same entry records that the fix failed and was reverted. What a test enforces
is the opposite: `test_the_no_clause_conflation_is_exactly_the_calls_it_is_recorded_as` pins four
no-clause calls flagged `misaligned` (baseline). The Rule line is the sentence the README tells a
reader to trust. Separately, the handover's table says CALL-04 was "misaligned 10/10 in both"
passes; the committed pass records 9 `misaligned` and 1 `partially_aligned`. The handover is closed
and will not be edited, so the correction lives here.
Closure: a dated amendment to D125's Rule line stating the pinned behavior and naming the pinning
test; the CALL-04 correction recorded wherever the next session keeps the handover's errata.

**P3-9 (Medium, reproduced) — Three statements say the template's comments are hashed; they are not.** `[stale prose] [contradiction: docstring vs code]`
Reproduction: editing the sentence "This comment is part of the hashed content, which is correct"
inside the template's own comment leaves `PromptTemplate.sha256` unchanged; editing a sent line
moves it. The three: `prompts/judge-dimension.v1.md:39` ("This comment is part of the hashed
content, which is correct"), `src/harness/judge/prompt.py:55` ("kept in what is hashed") and
`src/harness/judge/prompt.py:178` ("The whole file is hashed and only this is sent") — each
contradicted by the `sha256` docstring in the same module and by
`test_a_comment_only_edit_does_not_move_the_template_hash`. D123's consequences paragraph carries
the same sentence. The template is the file the phase versions as corpus data, and the stale
sentence sits in the part of it a maintainer reads.
Closure: rewrite the three and add a dated line to D123; the test already holds the truth.

**P3-10 (Medium, reproduced) — The phase-3 verifier's closing line counts three requirement anchors as acceptance criteria, and no test binds the phase-3 verifier to the specification at all.** `[verifier tick] [missing mechanism] [P2-4 and P2-6's shape, one phase later]`
The specification has 18 `[P3]` acceptance criteria. `tools/verify_phase3.py` has 23 entries: 18
anchored into the acceptance-criteria section, 3 anchored into requirement prose — the
non-functional lines "SHALL complete without network access", "keep the citable-identifier syntax
distinguishable" and "whether the specified exponential backoff **replaces**" — and 2 declared
extras. `tools/verify_phase2.py:461` counts every anchored entry and prints them as "the
specification's own [P3] acceptance criteria": 21. Phases 1 and 2 each have a test asserting every
tagged criterion is claimed, every anchor resolves and the unanchored entries are the declared
extras (`tests/test_acceptance.py`, lines 288–316; `tests/test_phase2_acceptance.py`, lines
38–71). No test names `verify_phase3`. Run by this audit with the phase-2 test's own logic: all 18
claimed, every anchor resolves, 2 extras — true today and held by nobody. A `[P3]` criterion added
to the specification, or a verifier entry deleted, is noticed by nothing; the CI step catches a
renamed *test*, since the verifier prints MISSING, not a missing criterion.
Closure: a phase-3 counterpart of the phase-2 acceptance test — claimed, resolves, extras equal 2 —
and a summary that counts anchors landing in the acceptance-criteria section and prints requirement
anchors as their own number.

**P3-11 (Medium, by reading) — The specification's sweep is due by its own trigger and nothing in the tree says so.** `[stale] [unmechanized trigger fired]`
The header reads "Last swept: 2026-09-08 @ 0.26.0 @ D119 — trigger: ~8–10 accrued decisions, before
publishing, or at phase completion", and states that only the accrued count is mechanized. Seven
decisions have accrued (D120–D126), so the numeric guard is green at its ≤10; phase 3 closed at
`530686c`, which is the clause the 0.26.0 changelog says fired for phase 2 "while the numeric one
sat green at six"; the changelog's newest entry is 0.26.0 and `sessions/PHASE-4-SESSION-PROMPT.md`
does not mention a sweep. Every phase-3 decision postdates the last sweep. "Last updated:
2026-09-07" is honest — the specification was not edited in the span — which is the state a sweep
exists to end.
Closure: sweep and bump before P4 starts, or register the deferral in `OBLIGATIONS.md`. The
phase-completion event is now observable in the tree — a handover with `Status: closed` — so the
clause can be mechanized: when a closed handover for phase N exists, `Last swept` must be at or
beyond the last decision that handover records.

### Low

**P3-12 (Low, reproduced) — The pre-flight input estimate is below every recorded input count, and three documents give three figures for one quantity.** `[estimate] [stale prose]`
The dry run prints $7.13 for 160 calls: 1,789 estimated input tokens per call and 4,096 output. The
committed log records a mean of 2,375 input tokens, and on all 16 calls the estimate is below the
smallest count recorded — actual over estimate 1.30 to 1.37, measured per call. The total is still a
ceiling by four times ($1.65 actual) only because the output side is bounded at `max_tokens`.
`_CHARS_PER_TOKEN`'s comment says 3.5 was chosen so the estimate "should be the ceiling"; the
Not-checked block says the corpus "actually renders" ~1,900 input tokens, the handover says about
1,700, the log says 2,375. The Not-checked entry that records this also says a check that the
estimate brackets the actuals "is available and is not built" — the numbers above are that check.
Closure: derive the divisor from the committed log, or read its mean `input_tokens`; add the
bracket test the block names (estimate ≥ every recorded input count, and total ≥ recorded cost);
let the three figures collapse into the one the test reads.

**P3-13 (Low, reproduced) — An unknown fact category, or a template placeholder with no value, aborts with an uncaught traceback and exit 1 — the code the CLI documents as "a gate failed".** `[exit code] [named abort, wrong label]`
With a rubric copy declaring `requires_facts: [nonsense_category]`, replay mode raises
`UnknownFactCategoryError` out of `run_judged` uncaught (the console script exits 1), and live mode
raises it out of `judged_call_estimate` — before confirmation, which is right. A template with an
extra placeholder is refused as stale first in replay mode (exit 2, its hash moved) and would reach
the same traceback in live mode. The requirement — abort naming the category — is met; the exit code
collides with D114's meaning of 1, and the loader validates `model` and `effort` at load but not
`requires_facts`.
Closure: validate `requires_facts` against `known_fact_categories()` in `_parse_judge_spec`; catch
`PromptError`, and the `ValueError` a verdict outside the scale raises, around the estimate and the
run in `judged_command`, exiting 2 with the named cause.

**P3-14 (Low, reproduced) — `.env.example` offers `ANTHROPIC_AUTH_TOKEN` as an alternative, and a token supplied that way cannot authenticate.** `[credential route] [documented but unworkable]`
`LiveTransport.__init__` takes whichever declared variable is set and passes it as `api_key=`
(`src/harness/core/transport.py`, lines 670–690); the installed SDK sends `api_key` as `X-Api-Key`
and `auth_token` as `Authorization: Bearer`, checked by constructing both clients and reading their
auth headers. A token in `.env` alone is sent under the wrong header; one exported in the
environment is picked up by the SDK's own lookup as well and sent under both. Scrubbing both names
is right and stays.
Closure: pass `auth_token=` when the credential came from that variable, or drop the alternative
from the template.

**P3-15 (Low, reproduced) — Three retry-leg asymmetries in the judged engine.** `[untested edge] [code without requirement]`
(a) A malformed first answer buys the informed retry, and the correction it is sent reads "Your
previous answer cited identifiers that were not in this prompt: ." — an empty list, because
`_validate` returns no rejected identifiers for a parse failure and `informed_retry_message` has one
wording. (b) A retry truncated at `max_tokens` skips the stop-reason classification the first attempt
gets (`src/harness/judge/engine.py`, lines 349–378): the result is `errored` with "retry budget
exhausted … response is not valid JSON" while the log holds `max_tokens` — distinguishable by log
inspection, as the requirement asks, and misdescribed in the result. (c) `_response_from_message`
turns a missing `stop_reason` into an empty string and the engine treats that as a complete answer;
a scripted response with `stop_reason=""` produced an applicable verdict, and the log carried the
empty string. Both count guards would flag it in a committed log, so it cannot pass unnoticed there.
The specification's retry clause names citations only, so the malformed-response retry is behavior
without a requirement.
Closure: a second correction wording for malformed responses; classify the retry response's stop
reason before parsing it; refuse a message with no stop reason; one line in the specification for the
malformed-response retry.

**P3-16 (Low, reproduced) — The obligations harvest keys on (handover, item number) and compares nothing else, so a renamed item with the same number is invisible to it.** `[mechanism gap]`
In a copy holding the register, the holdout register, the handovers and `tests/test_obligations.py`,
renaming "### 2. Agreement is measured now, and still not asserted" to "### 2. A completely different
obligation, keeping the number" leaves all 10 tests green. Renumbering or deleting a heading is caught
in both directions, as the handover says. The risk is bounded because handovers are closed documents.
Closure: carry the item's title, or its first 40 characters, in the row and compare it.

**P3-17 (Low, by reading) — Documents the phase left behind.** `[stale statements]`
- `README.md` line 23, "the two phase verifiers", and line 83, "Give both `--junit`": three are on
  disk. The recall net does not know "verifier" as a noun, so the worded count went stale unguarded.
- `README.md` line 22 describes `src/harness/` without the transport seam or the judge package —
  P2-11's shape again.
- `README.md` line 30, "Root-level Markdown — the audit, the handover, the obligations register": the
  audits and handovers moved to `sessions/` at D120, and the Not-checked block records that the
  continuity documents carry no license line; the sentence names files that are not in the root
  under a license the block says they lack.
- The Not-checked block: "Twenty of the 37 rubric entries declare that no negative instance exists" —
  20 holds; the rubric has 38.
Closure: one pass over the two files; if worded counts of tools are to stay live, bind "phase
verifiers" to a glob in the recall net.

**P3-18 (Low, by reading) — `tools/verify_controls.py` copies the operator's populated `.env` into a temp directory on every run.** `[hygiene] [credential]`
`_SKIP` (line 51) omits `.env` and `copy_tree` copies the whole root. Harmless in CI, where no `.env`
exists; a needless second copy of a live key on the operator's machine, deleted with the directory.
Closure: add `.env` to `_SKIP`.

**P3-19 (Low, by reading) — A judged run whose every result is `refused` exits 0.** `[exit code] [no decision]`
`judged_command` counts only `errored` and `unevaluable` toward "TIER INCOMPLETE"
(`src/harness/cli.py`, lines 445–450). D23 makes refusal an expected event and D124 says exit 0
means the tier ran; nothing says whether a run of 160 refusals ran. The counts are printed, so it is
not silent.
Closure: decide at P4 with the gate, and record the decision.

**P3-20 (Low, by reading) — The call ceiling counts logical sends, not requests.** `[definition]`
`CeilingTransport` wraps `LiveTransport`, whose `send` issues up to `MAX_TRANSPORT_ATTEMPTS`
requests, so a ceiling of 200 bounds 200 logical calls and up to 800 requests; a request that timed
out after the server processed it is billed and uncounted. The estimate excludes retries and says so.
Closure: state it in `DEFAULT_CALL_CEILING`'s comment and in the live-mode output.

**P3-21 (Low, by reading) — `load_replay_transport` keeps the last of two entries sharing a (hash, repetition) key and says nothing.** `[silent]`
`src/harness/core/transport.py`, lines 1025–1027. Unreachable from a writer that opens with `w`;
reachable from a concatenated or hand-edited log.
Closure: refuse a duplicate by name.

**P3-22 (Low, by reading) — "Succeeds with `--allow-stale-replay`" can only be satisfied by a forged header for the template half of the criterion.** `[criterion vs mechanism]`
A template edit changes every rendered request and so every request hash, so a genuinely stale
template misses entry by entry whatever the flag says; the flag's real use is a rubric-version bump
that changed no entry. `test_a_stale_log_is_refused_and_the_flag_lets_it_through` stamps a
real-template log with a false header and says so in a comment; the specification's criterion does
not.
Closure: amend the criterion text to name the case the flag serves.

**P3-23 (Low, decided here) — The reference log is 1.2 MB and 8 times its unique content, and the format needs deciding before P4 records its own.** `[size] [P4]`
Measured: `system` is 45% of the file, one 3,333-character string repeated 160 times; `prompt` is
35%, 16 distinct strings repeated 10 times each; `schema` is 4%, one object repeated 160 times;
responses are 8%. P4 adds five dimensions and a synthesis entry on a larger model; at this shape its
reference log is on the order of 7–8 MB and every template edit re-records all of it. 1.2 MB is
acceptable today, so the size does not need deciding. The format does, before P4's first live pass:
a `system` and `schema` record written once and referenced by hash from each call record changes
storage only — replay keys on the content hash, not on the file layout, and the requirement's "exact
prompt sent" stays recoverable. Rebuilding requests from the tree instead of storing them is not an
option; it drops the requirement.

**What these closures would do to the corpus.** None touches a check's scope or moves a verdict in
the committed log. P3-13's loader validation admits the shipped entry, which names a known renderer;
P3-15's retry classification affects only a truncated retry, of which the log has none; P3-7 is a P4
decision about which calls the pair test compares, not about any verdict.

---

## 3. Requirements against code, both directions

**Every `[P3]` requirement has code, and 20 of the 23 have a test that asserts its own subject.** The
23 tagged requirement statements map as follows; the three with a qualification are named.

| requirement (line in `specs/voice-agent-eval-harness.md`) | code | evidence |
|---|---|---|
| 131 record every judged call | `RecordingTransport`, `RunLogEntry.as_dict` | fixture tests; the committed log by inspection (P3-6) |
| 132 exclude credential values | `scrub_credentials`, `RunLogEntry.as_dict`, `LiveTransport.send` | prompt field and the committed file only; error path untested and bound to `cwd`; the losing value of a disagreement unscrubbed (P3-3, P3-4, P3-5) |
| 144 one informed retry with rejected and valid set | `_evaluate_repetition`, `informed_retry_message` | asserted |
| 145 exhaustion → `errored`, run continues | `_evaluate_repetition` | asserted |
| 146 refusal → `refused`, details recorded, no retry, continues | `_evaluate_repetition`, `_response_from_message`, `as_dict` | asserted |
| 147 `max_tokens` → `errored` carrying the reason | `_evaluate_repetition` | asserted for the first attempt; the retry leg reaches `errored` by another route (P3-15) |
| 148 `stop_reason` recorded unconditionally with the config | `as_dict` | asserted, fixture and committed log |
| 149 ceiling → halt and report | `CeilingTransport`, `run_judged`, `judged_command` | halt asserted; the report's exit code untested (P3-2) |
| 150 transient → backoff to a declared maximum; persist before abort | `LiveTransport.send`, `backoff_delay`, `JudgedCallAborted` | asserted, including the absence of a final sleep |
| 151 replay miss → abort, no live call | `ReplayTransport.send` | asserted; the transport holds no inner |
| 152 stale → abort unless the flag | `stale_differences`, `load_replay_transport` | asserted; the "succeeds" half is fixture-only for the template (P3-22) |
| 158 N repetitions, one entry each | `evaluate_call` | asserted |
| 160 `[T<n>]`, `[F<n>]`, each validated against its own set | `render_prompt`, `invalid_citations` | asserted, with a planted `F9` |
| 161 delimited untrusted block and the statement | template, `render_prompt` | asserted over the shipped template |
| 162 facts: only the named categories; omitted; explicit negative | `render_facts`, `_drop_section` | asserted |
| 163 count issued calls, halt at the ceiling | `CeilingTransport` | asserted; counts logical sends (P3-20) |
| 168 unknown renderer → abort naming it | `render_facts` | asserted; exits 1 through the CLI (P3-13) |
| 169 no `max_tokens` → refuse by name | `_parse_judge_spec` | asserted, first among the judged fields |
| 175 live: require a credential, print the estimate, confirm | `LiveTransport.__init__`, `judged_call_estimate`, `confirm_spend` | estimate and confirmation asserted; **the credential requirement by nothing** (P3-1) |
| 176 `--max-calls`, else a declared default | `build_parser`, `DEFAULT_CALL_CEILING` | asserted on the parser |
| 183 no speech outside the block; distinguishable syntax | `render_prompt`, `FACT_RENDERERS` | asserted over a design call |
| 185 replay completes without network access | `ReplayTransport`, deferred import | asserted over a fixture log and the import graph; the committed log replayed by this audit and by no test or CI step |
| 186 explicit timeout, replaces-not-wraps stated, streaming above a threshold | `client_options`, `SDK_RETRIES`, `should_stream` | asserted from the constructor's kwargs |

**Code with no requirement behind it**, each of which is reasonable and should be written down,
because P4 reads this tier's behavior as settled:
1. The malformed-response retry: a parse failure buys the informed retry (`_validate`); the
   specification's clause names citations only (P3-15).
2. The judged command's exit codes 0, 2 and 3; D114 defines them for the deterministic tier (P3-2).
3. `refused` not counting toward an incomplete tier (P3-19).
4. `model` and `effort` validated at load against `SUPPORTED_MODELS` and `EFFORT_LEVELS`; the
   specification's model section says "refused by name" as a design statement, not a SHALL.
5. The `.env` route's precedence rule — the exported variable wins — and what happens to the loser;
   `tools & permissions` names the route only (P3-3).
6. `MINIMUM_CREDENTIAL_LENGTH`: a value shorter than 8 characters is never scrubbed. Documented in
   the constant; a security threshold with no requirement.
7. Replay runs writing a log of their own; D8 argues for it and no line requires it.
8. `JudgeKeyOnDeterministicEntryError` and the refusal of `params` on a judged entry.
9. The header's `corpus_version` and `artifact_hash`, recorded and deliberately not compared.
10. `DEFAULT_CALL_CEILING` at 200; the requirement asks for a declared default, and the value's
    rationale is a comment.

**The builder's own open items, probed.**
- *Agreement is 2 of 3 and the third a clean miss; a fix was attempted and reverted.* The revert was
  right: the falsifier (CALL-02 and CALL-04 must stay `misaligned`) held, the edit moved none of the
  four no-clause calls, and it cost 7 fabricated citations the passes on either side did not. The
  handover's account is accurate on every point checkable from the committed pass except CALL-04's
  distribution (P3-8); passes 1 and 3 are not committed, so every statement about them is the
  handover's word.
- *~8 criteria have a viable mechanism not built, ~12 have none.* Sampled: the 8 phase-3 caveats and
  6 of the Not-checked block's open entries. The classification holds within two either way. Two the
  builder counted as closed by the live run have a one-line mechanism unbuilt — the log's mode (P3-6)
  and per-field scrubbing (P3-5) — and the estimate-versus-actuals check the block calls "available
  and not built" is computed in P3-12.
- *`OBLIGATIONS.md` does not cover the Not-checked block.* Not folding it in wholesale is right: most
  entries are scope statements, not debts. Leaving the owed mechanisms inside it with no row is not —
  the estimate bracket, the re-run of the severity tool's own audit, and the missing subject-index
  tool are debts by the register's own definition. One classification pass, then a rule that a
  Not-checked entry naming work owed cites an `OB-` id.
- *The harvest keys on (filename, item number).* Guarded loudly for renumbering and deletion, in both
  directions; blind to a same-number rename (P3-16). "Only documented" understates it; "guarded"
  overstates it.
- *The reference log is 1.2 MB and undecided.* Decided in P3-23: the size is fine, the format is what
  P4 needs settled first.

---

## 4. Counts, enumerations and the mechanisms that hold them

| stated | referent | holds? | mechanism |
|---|---|---|---|
| 23 verifier entries: 18 criteria, 3 requirement anchors, 2 extras | `tools/verify_phase3.py` | yes | none binds them to the specification (P3-10) |
| "21 of them the specification's own [P3] acceptance criteria" | printed by the verifier | **no** — 18 | none |
| 18 `[P3]` criteria, 23 `[P3]` requirement statements | specification | yes | `MEASURED_CONTRACT` in `tests/test_document_counts.py`, by equality |
| 1,003 tests; 72 files under `mypy --strict`; 21, 24, 23; 41 controls | handover, P4 prompt | yes | none for the prose; CI for the gates |
| 13 phase-3 register rows, 12 mutation entries | `CONTROL-REGISTER.md`, `control-mutations.yaml` | yes — the pricing-table row has no entry by construction | the register's own guard; `tools/verify_controls.py` |
| 11 register rows, tagged | `OBLIGATIONS.md` | yes | computed from the table |
| 160 records, 16 hashes, N=10, every request covered | committed log | yes | `test_a_real_run_records_n_repetitions_for_every_call`, `test_every_request_the_shipped_configuration_produces_is_in_the_log` |
| "480 judged calls" over three passes; "about $4.90 in total" | handover, Not-checked | consistent — one pass is 160 records and $1.65 at the declared rates | none; two of the three passes are not in the tree |
| "zero fabricated citations in 320 calls" for runs 1 and 2 | handover | half checkable — the committed pass has `retry_index` 0 throughout | `test_the_citation_validator_fired_on_nothing_in_a_real_run` |
| CALL-04 "misaligned 10/10 in both" | handover | **no** — 9 and 1 in the committed pass | none (P3-8) |
| "~1,900", "about 1,700" and 2,375 input tokens per call | Not-checked, handover, log | three figures for one quantity | none (P3-12) |
| "fifteen packages enter the lockfile, `pydantic` and `httpx2` among them" | D122 | yes — 15 added, and `httpx2` is a real package | none |
| 38 entries; "Twenty of the 37" declare no negative instance | rubric, Not-checked | 20 holds; 37 is stale | none (P3-17) |
| "the two phase verifiers"; "Give both `--junit`" | `README.md` | **no** — three | none (P3-17) |
| 408 events, 16 design transcripts | extraction artifact | yes | tagged `#design_set_size`; the event count by test |
| 8 caveats; "Eight of its 23 criteria carry caveats" | verifier, workflow comment | yes | computed at print; the comment by nobody |
| D1–D126 contiguous; D122–D126 phase 3's | decision record | yes | the order mechanism |
| the three repositories are private | Not-checked, `README.md` | yes, by `gh repo view` | none, deliberately |

**Prose sampled for truth**, which no guard reads. Sampled: 33 statements across the four documents
the prompt names. Holding, checked by running something: replay spends nothing and imports no SDK;
a miss aborts naming its hash; the live path prints a measured estimate and confirms; every gate
runs in CI and CI is green; `.env.example`'s "nothing else needs it"; the repositories are private;
D122's package count; D124's Rule line; the handover's headline numbers; 45% of the log is the
system prompt; "renumbering or deleting an owed heading breaks a register row". Stale or false: the
verifier's closing count (P3-10); D125's Rule line and "so it was closed" (P3-8); the template-hash
sentences in three places (P3-9); "scrubs both values when the two disagree" (P3-3); the README's
"two phase verifiers", "both", root-level Markdown, and package description (P3-17); "Twenty of the
37" (P3-17); CALL-04's distribution (P3-8); the three input-token figures (P3-12). Not sampled: the
decision record before D122, the taxonomy, event-model and format specifications,
`HOLDOUT-OBLIGATIONS.md`, and the P4 prompt beyond its numbers.

---

## 5. Mechanisms versus memory

| "remember to …" | mechanism | gap |
|---|---|---|
| refuse a live run with no credential | the code refuses | no test drives it (P3-1) |
| exit 3 when a judged run is incomplete or aborted | the code does | no test (P3-2) |
| scrub the losing value when two credentials disagree | none | a test of a neighbor (P3-3) |
| scrub the transport's error messages | the code scrubs against `cwd` | no test; wrong environment (P3-4) |
| scrub every run-log field | the code does | the prompt field by test, the committed file by shape (P3-5) |
| keep the reference log a live recording | none | `header.mode` read by nobody (P3-6) |
| claim every `[P3]` criterion in the verifier | none | phases 1 and 2 have a test; phase 3 does not (P3-10) |
| run the phase-3 verifier, the inventory and the control gate on every push | CI steps, all present | none |
| register every owed item | both directions | a same-number rename (P3-16) |
| keep the template hash over what is sent | test | the prose beside it says otherwise (P3-9) |
| keep the estimate above the actuals | none | P3-12 |
| sweep the specification at phase completion | none — the header says so | P3-11 |
| replay the committed log end to end | none — hash presence is asserted; the CLI replay was run by hand here | a one-line CI step, or P4's snapshot |
| keep the handover's numbers equal to the artifact's | none | P3-8 |

---

## 6. What was not checked

- The held-out repository, its transcripts, commit messages and test docstrings; the authoring
  packet; both withheld source folders. Not opened, not listed, not searched.
- Live passes 1 and 3. Only pass 2 is committed, so the 7 fabricated citations, the zero in pass 1,
  CALL-04 in pass 1 and the $4.90 total are the handover's word. No live call was made by this audit.
- Whether the committed log was recorded with a real key in the environment, as criterion 17's caveat
  says. Not recoverable from the artifact.
- The API itself. Parameter shapes were checked against the installed SDK's signatures only; that the
  API accepts `minItems` in the schema and the adaptive-thinking block is inferred from the handover's
  480 successful calls, not observed.
- The `subject_index.py` entry in the Not-checked block, and the severity tool's repository.
- Whether the judge's verdicts are right beyond the three seeded calls and the negative instance —
  rubric judgment, out of scope by design. The injection turn was read to one line, to establish its
  direction (P3-7), and no further.
- CI logs. Four conclusions were read; no step's output was.
- The comparative-judgment interface scanner, the pre-commit guards and the deterministic tier, except
  where a phase-3 change touched them.
- Performance beyond the suite's 228 s; the judged replay of 160 records through the CLI took 3 s.

---

## 7. Suggested order of work

1. P3-1 and P3-2: the two untested guards on the live and judged paths. Both are small, both are the
   shape this project keeps finding, and P4's gate sits on the second.
2. P3-3, P3-4, P3-5: the credential clause — one bound environment, three tests, four mutations
   registered. Read the requirement's "every" literally when writing them.
3. P3-10 and P3-6: the verifier's own ticks — a phase-3 acceptance-binding test, an honest closing
   count, and one line asserting the reference log is a live recording.
4. P3-8, P3-9, P3-17: prose — D125's Rule line, the template-hash sentences, the README.
5. P3-11: sweep and bump before P4 opens, and mechanize the clause that has now fired twice.
6. P3-7, P3-23, P3-19: the decisions P4 needs first — what the injection pair is measured on, the log
   format, and whether a run of refusals ran.
7. P3-12 to P3-16, P3-18, P3-20 to P3-22 as the code they name is touched.
