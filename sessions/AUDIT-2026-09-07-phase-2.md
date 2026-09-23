> **WORKING STATUS, maintained separately from the report below.** Added 2026-09-08, when the
> report was committed. Every finding acted on was reproduced first, independently of the report's
> own reproduction.
>
> **Closed:** P2-1 (errored and unevaluable reach the exit code, as 3), P2-4 (the phase gate names
> every family, not the four somebody remembered), P2-5 (the coverage caveat, stale since the tier
> closed at 61 of 61), P2-6 (`tests/test_rubric_coverage.py` binds the union of the firing tables to
> the rubric's entry ids, which is the mechanism P2-4 was a symptom of), P2-7 (retrieval requires a
> successful result, with a planted control), P2-8 (`Provenance` refuses a blank field, and
> `load_corpus` returns a digest rather than a half-built stamp), P2-10 (the reuse verdict is read
> from the report, and the staleness scan is a deny-list), P2-12 (three tests assert what their names
> say), P2-13 (params frozen at every depth), P2-17 (registry and rubric compared by equality).
>
> **Closed, 2026-09-08 by a rubric-cleared session:** P2-11 in full. The README, `pyproject.toml`,
> the decision record's status line, the CLI's exit-code list and `values.py`'s lost `\b` were made
> current earlier; the file carrying that escape held a literal 0x08 byte, and a repo-wide sweep now
> refuses control characters in source. **The W rows are now ticked**, row by row, each cell naming
> the check, the test, and whether the evidence is a verdict the design corpus produces or a fixture.
> W5 splits three ways and the cell says so. W8 gets a **third disposition, *not reached***: its
> closure lives in `values.complete_year` and no shipped check calls it, so a tick would claim what
> the tier does not have and leaving it open would say the tier carries a defect it has no code for.
> W5 and W6 are marked fixture-only, which is the residue the design call owed at D109 closes.
>
> **Also closed, 2026-09-08:** P2-14 (every `*POLICY_TOOL` constant is read with `ast` and bound to
> the register, so a tenth copy is found by construction rather than by counting), P2-15 (six items,
> two of them behavior: a `RegistryError` from `satisfied()` on a wide scale is re-raised instead of
> becoming one `errored` row per call, and two contexts sharing a `call_id` are refused instead of
> being weighted twice in every pass rate), P2-16 (the month lists, the shared capability trigger and
> the two number tables each have a test that would notice them diverging), P2-3 (the criterion now
> describes the mechanism the build took, and the residue is recorded at D109's amendment).
>
> **P2-2 and P2-9's signal-list items are closed too, 2026-09-08.** P2-2 took its first option:
> `available_value_never_spoken` now declares `number_cues` and `cue_window_words`, filters
> candidates through `cue_follows` and compares through `grounded`, which closes the D111 gap the
> finding names — `"one moment for me."` no longer contributes the value 1. `complete_year` took
> the second option alone, for the reason W8's row now gives. P2-9 (a) and (e) are closed by one
> module owning both boundaries, with (j) taken in the same batch because option (A) adds exactly
> the kind of `match` mode that was falling silently to literal. **Both are recorded as D115 and
> D116, and neither moved a verdict**: 555 results, identical in status, verdict and evidence, so
> each carries planted controls rather than resting on a corpus that cannot tell the difference.
>
> **P2-9 (f), (g) and (h) are closed too, 2026-09-08, as D117** — the three items that were pure
> check logic with no rubric judgment in them. Timestamps are compared as instants, with an
> unreadable value or an offset-aware/naive pair reported `unevaluable` naming the field rather than
> passing. `context.state_writes` returns every write of every state variable, so no check is built
> on a mapping that keeps one. And the two "after" lookups now state the direction each means —
> which are **opposite**: `handoff_without_context` wants a write after the invocation, and
> `precondition_satisfied_by_assertion` wants one at or before it, because a state recorded after the
> gate was passed did not establish anything at the moment it was passed. The report describes those
> two as one item, "both names say after", which is right about the defect and backwards about the
> direction for the second.
>
> **A fourth site the report does not list**, found by asking which other callers shared the shape:
> `verification_absent_before_gated_write` read the verification states out of the same
> last-write-wins dict, so a call that verified before a gated write and refreshed the flag afterwards
> reported no verification below it — a false violation on an absolute gate. Closed with the rest.
> No verdict moved (555 results, three evidence strings reworded), so all four rest on eight planted
> controls, each of which fails when its defect is restored.
>
> **P2-9 is closed, 2026-09-08, as D118** — (b), (c), (d), (i) and (k), the five that each change
> what an entry means. The deadline resolution is searched from the first statement onwards rather
> than inside the stating turns; the spoken date compares the month as well as the day; a
> confirmation asked before the attempt as well as after is no longer the finding; the silence check
> reads the agent through the subject population rather than both speakers off the raw stream; and a
> topic that cannot be resolved is refused **without discarding what the other topics found**.
>
> That last one is the substantive decision, and the report understates it: strip clause 2.4 out of
> `refund.v1` and CALL-02's `settlement_timing` violation — about clause 3.2, and unrelated —
> vanished with it; declare a second action tool on `exchange` and CALL-01's `confirmation` finding
> vanished with it. Neither loss was visible in the result. D114's precedence, one level down.
>
> **One of the report's items breaks the corpus if taken literally.** Widening (b) to the whole call
> clears CALL-09: its agent says "I've moved you across to the June date" thirteen events before the
> deadline is first put in relative terms, so the scope is bounded below as well as above.
>
> No verdict moved (555 results, one evidence string reworded). Eight more planted controls, each
> failing when its defect is restored. **A neighbor found while planting one:**
> `test_a_holding_phrase_clears_the_gap_it_precedes` asserted that the entry fires and that the
> transcript contains the words — both true of a check ignoring the signal list. No design call
> exercises the clearing at all. P2-12's shape, in a test written before it.
>
> **What remains is the design call owed at D109's amendment**, which is corpus authoring and needs
> the owner's agreement before a transcript is written.
>
> **One inconsistency found, surfaced at D117, and closed on the owner's decision:** the rubric
> declares `holder_confirmed` and `caller_verified` as **state variables**, and `corpus/entities.md`
> listed both only among tool-result detail keys. Both are now declared state variables written in no
> transcript, and the register says why: those entries' findings **are** the absence of the state, so
> the name a check looks for has to be one the corpus is permitted to contain — otherwise the
> negative instance neither entry has could never be authored.
>
> **One finding this batch produced, wider than P2-3 as written.** P2-3 says the lexicon values for
> two scale words are decorative. Measured against all fifteen design calls, **five** parameters of
> `A-available-value-never-spoken` move no verdict: `number_words` (every value, and the thirty-word
> lexicon cut to one word), `number_scales` (values), `digit_pattern`, `number_joiners` and
> `strip_characters`. Changing that entry's `sources.exchange_difference.match` from `numeric` to
> `literal` moves nothing either. The instrument works — changing the source `key` moves CALL-09,
> changing the email source's signals moves CALL-11 and CALL-12. The cause is corpus coverage: only
> CALL-09 reaches the numeric source and its verdict is `withheld`, reached by finding no figure,
> which is what a wholly broken matcher would also produce. `tests/test_values.py` covers `figures_in`
> in 32 tests against a **fixture** lexicon; nothing binds the rubric's own tables to a verdict.
> Closing it means authoring a design call in which an agent speaks a payload figure in words, which
> is corpus work and is owed to a cleared session. The list was held by a test that failed when the
> gap was closed without being recorded, and D116 added two more rows to it — `number_cues` and
> `cue_window_words` configure a candidate filter, and a filter cannot show its work where the arm
> reaches no candidate.
>
> **Closed 2026-09-08 as D119.** `CALL-22` states a `difference_due` of `1,250.00` and its agent says
> "one thousand two hundred and fifty dollars" aloud. All seven parameters now move a verdict, and so
> does the `numeric` → `literal` mutation. The test holding the list is **deleted**, not emptied, so
> this paragraph no longer names it: a test asserting that an empty list is empty would keep the shape
> of a finding after the finding was gone. Closing it first required D115's recorded residue to be
> corrected — `matching.values` stopped a value at a comma, so the payload read as `1`.
>
> **Two corrections to the report.** Its baseline table says `GATES FAILED: 20 of 37`. A clean tree
> at `6dc2033` gives **36 of 37**, checked by stashing the fixes and re-running. P2-14 says the
> policy-tool name is hardcoded "ten times" across "nine test files"; it is nine times across
> **eight** test files plus `cli.py`'s default. Both tables are presented as reproduced. Neither
> correction touches a finding: every one checked reproduced exactly as written.
>
> **No longer true, and recorded because the report says it.** When the report was written the
> `phase-2` branch had never run CI: the workflow triggers on push to `main` and on pull requests,
> and the branch was local. It was then pushed and run by hand (`34214979207`, the first run ever to
> execute both verifiers), merged to `main`, and **deleted on 2026-09-08** once it held no commit
> `main` did not. `6dc2033`, the tip this report was written against, is an ancestor of `main` and
> stays reachable by hash — `git show 6dc2033` works without the branch.

# Audit — phase 2 (deterministic evaluation slice), at `6dc2033`

*Written against the `phase-2` branch, which has since been merged and deleted. The commit is an ancestor of `main`.*

> **STATUS.** Written 2026-09-07 by an independent session (Fable) that took no part in the phase-2
> build. Untracked and uncommitted; nothing in the tree was modified. Every finding marked
> *reproduced* was reproduced by running code against this tree; a finding marked *by reading* rests
> on the source alone and says so. The session read the design corpus through the parser and the
> rubric, the specs, the decision record, every phase-2 source and test file, and both verifiers. It
> did **not** read any held-out transcript, the held-out repository, `comparative-judgment`, or either
> withheld source folders, so it is clean for rubric and design-corpus work.

**Kind of review.** An independent **phase-completion conformance audit**: traceability in both
directions (requirement → criterion → verifier entry → test → code, and code → requirement), a
consistency pass over every document the phase touched (stale statements, contradictions,
duplication, counts against their referents), an adversarial review of the tests (do they assert the
property they are named for; what boundary or malformed input has no test), and a mechanism check
(is each "remember to run X" a hook or a habit). In this repository's own vocabulary that is not a
*sweep* (the author's own re-read of the spec at a trigger, D71/D98) and more than an adversarial
review; its precedents are the 2026-08-29 and 2026-09-06 independent audits.

---

## 1. Baseline, reproduced

| what | result |
|---|---|
| branch / tip | `phase-2` at `6dc2033` (2026-09-07 22:49 -0700), 18 commits over `main` (`648bfa0`), **local only, not pushed** |
| `uv run pytest -q --junit-xml=build/phase1-junit.xml` | **709 passed** in 163 s, exit 0 |
| `uv run mypy` / `ruff check .` / `ruff format --check .` | no issues in 55 files / all checks passed / 76 files formatted |
| `uv run harness run --tier assert` | **exit 1**, `GATES FAILED: 20 of 37`, as D105 requires over a seeded corpus |
| `python tools/verify_phase1.py --junit build/phase1-junit.xml` | 21 of 21 PASS, reading the report |
| `python -m tools.verify_phase2 --junit build/phase1-junit.xml` | 24 of 24 PASS (22 anchored + 2 declared extras), reading the report |
| `tools/check_holdout_absence.py` | OK: 15 design transcripts + 5 fixtures, nothing else |
| `harness.findings_view --check` | view is current, 89 findings |
| rubric | 37 entries, 37 registered checks (one each), 20 entries declare `negative_instance: none` |
| coverage | findings 89 = 61 `assert` + 22 `judge` + 6 `human`; **61 of 61** `assert` findings traced by some entry; nothing traced that is not `assert` |
| P2 contract | 12 requirement statements, 22 criteria, pinned by `tests/test_document_counts.py` |
| local hooks | `.git/hooks/` is empty; `core.hooksPath` set to a machine-wide hooks directory, whose `pre-commit` carries both `SECRET-GUARD` and `PRIVATE-GUARD` (Case 2 install, verified) |

Every gate the phase declares is green. The findings below are about what the green ticks do and do
not buy.

---

## 2. Findings

Severity: **High** = a fail-open path or a verifier tick that does not stand for what it claims;
**Medium** = a real gap the held-out set or the next phase will hit; **Low** = hygiene, duplication,
or an untested edge with no current instance. Tags name the audit category the finding answers.

### High

**P2-1 (High, reproduced) — Errored results never reach the exit code; a check that throws on every call exits 0 and prints "every gate held".** `[fail-open] [errors] [code without requirement] [missing test]`
Reproduction: copy `rubric.yaml`, keep only `A-completion-claim-unsupported`, set `params.topics: oops`, run `harness run --tier assert --rubric <copy>`. Output: `errored: 15`, `every gate held`, **exit 0**. Mechanism: `run_entry` (`src/harness/core/engine.py:90`) turns any exception into `status: errored`, and `run_command` (`src/harness/cli.py:184-206`) returns 1 only when a gate failed; errored and unevaluable counts are printed and then ignored. This is the W11 shape one level up: the status channel distinguishes the five states, and the exit code collapses four of them into "held". Two things compound it: (a) parameter *type* validation lives inside the checks as `TypeError`s (`_topics`, `_mapping`, the `window` check in `account_detail_disclosed_before_verification`), so a malformed rubric is not refused by name at load, it becomes 15 errored rows; (b) the exception-to-errored conversion has no requirement behind it. The only P2 text about `errored` is "reached at P3". The engine docstring gives the reason (one broken check must not cost the other sixty results), which is sound; what is missing is the consequence.
Closure: exit non-zero when `errored > 0` (a distinct code, or fold into 1 with the reason printed), never print `every gate held` when any errored or unevaluable result exists, add the requirement the engine implements, and a CLI test that mutates a parameter's type and asserts the exit code.

**P2-2 (High, reproduced) — Four value-layer functions have no production caller, and the W5–W8 criterion is ticked against them.** `[dead code] [criterion ticked against a neighbor] [stale rule]`
`cue_follows`, `grounded`, `complete_year` and `MatchMode` in `src/harness/checks/values.py` are imported by nothing under `src/` or `tools/` (grep: only `parse_spelled` and `figures_in` are used, by `conduct.py` and `omission.py`). Verifier criterion 13 ("each deterministic failure mode … has a test that fails when the defect is present") is satisfied for W5, W6, W7 and W8 by `tests/test_values.py` tests of those four functions. The tests are good; the tier does not route through them, so the tick says the *module* closes W5–W8 while no rubric entry does. Consequence for D111's stated Rule ("a turn containing a number word with no declared cue produces no candidate"): the one shipped check that reads spelled figures, `available_value_never_spoken`, has no cue parameter and collects every spelled number in agent speech. Reproduced with that entry's own tables: `"One moment for me."` yields `{Decimal('1')}`. A source whose value is `1` or `1.00` would read as spoken. That is W4's shape, in the module whose docstring says it closes W4.
Closure: either route a shipped entry through `cue_follows`/`grounded` (a money-grounding entry is the natural one, and none of the 61 assert findings needed it, which is worth saying), or move the four functions and their tests behind an explicit "reserved for P3/P4" note and amend criterion 13's caveat so the tick stops claiming the tier.

### Medium

**P2-3 (Medium, reproduced) — The spec's "every parameter" criterion describes a mechanism the build replaced, and the mechanism that shipped is blind to nested keys.** `[contradiction: spec vs code] [duplication] [untested]`
Spec criterion (added at D104): "*Every* parameter declared in *every* rubric entry is read by the check that entry names, asserted by a test that **mutates each declared parameter in turn** and requires each mutation to move a verdict or produce a named refusal; a parameter no mutation moves is reported by name." D109 chose option (C), the `ParamView` read-tracker, over (A), the per-parameter mutation test, and gave good reasons. The criterion text was not amended, and verifier entry 14 ticks it with read-tracker tests plus four mutation cases. Two consequences:
- `ParamView` records **top-level** keys only. Every entry's real configuration is nested (`topics.*.claim_signals`, `sources.*.match`, `bands.*.fraction`, …), and nested keys are read with plain `dict` access or `.get(..., default)` (`omission.py:98,159`, `policy.py:147`, `records.py:236,256`). A nested key that no code reads is invisible to D109's guard.
- It is already happening: `number_words.hundred` and `number_words.thousand` duplicate `number_scales`, and `_compose` consults only the scale table. Reproduced: with `number_words.hundred = 5` and `number_scales.hundred = 100`, "two hundred" still composes to 200. The lexicon values for the two scale words are decorative, which is W20 at the nested level.
Closure: amend the criterion to say what is built (read-tracking at the top level, mutation cases for a named sample) and record the nested blind spot as the residue; derive scale membership from `number_scales` alone so the duplicate entries go; consider a recursive view, or a test that walks every nested key of every entry and asserts at least one mutation case names it.

**P2-4 (Medium, by reading) — Verifier criterion 23 (gold-set agreement, the D105 phase gate) claims firing-set tests for 21 of 37 entries.** `[undocumented omission]`
`tools/verify_phase2.py:303-326` names `test_the_completion_claim_check_fires_on_exactly_the_seeded_calls` and the `platform`, `omission` and `policy` family tests. It does not name `tests/test_record_checks.py::test_each_record_entry_fires_on_exactly_its_seeded_calls` (5 entries), `tests/test_conduct_checks.py::test_each_conduct_entry_fires_on_exactly_its_seeded_calls` (9 entries), or the two remaining claim-family tests (`test_the_blocking_state_check_…`, `test_the_terminal_retry_check_…`). All of those tests exist and pass, so nothing is wrong today; the PASS printed for the phase gate rests on the families somebody remembered to list.
Closure: name the three missing tests. Better, see P2-6 for the mechanism that would have caught it.

**P2-5 (Medium, reproduced) — Stale caveat in the same criterion: "the rubric covers every assert-detectable finding: it does not yet".** `[stale statement] [contradiction]`
`tools/verify_phase2.py:322`. Coverage is 61 of 61 (section 1), commit `32e379a` is titled "Close the tier at 61 of 61", and the decision record's Not-checked block (line 5010) already says the tier covers every `assert` finding and records that the block itself "said 45 of 61 … until the tier was finished". The verifier's caveat is printed on every run under "NOT FULLY CHECKABLE BY MACHINE", so the stale sentence is the one a reader is told to read instead of the tick.
Closure: rewrite the caveat to what remains true (agreement is per entry against the calls the gold set names; the severity-weighted arithmetic is P5).

**P2-6 (Medium, by reading) — No mechanism binds the six per-family firing tables to the rubric's entry list.** `[list length vs. enumeration] [missing mechanism]`
Each family test file carries an `EXPECTED_FIRING` table and asserts, per row, that the row's findings equal the entry's `traces_to`. Nothing asserts that the **union** of all tables (plus the three claim-family constants) equals the set of rubric entry ids. A 38th entry with no table row would run, fire or not, and be claimed by no agreement test and no verifier line, exactly the shape P2-4 shows for the verifier. `test_the_check_ran_on_every_named_negative_instance_and_found_nothing` is the model to copy: it iterates the rubric, so it cannot miss an entry.
Closure: one test that collects every family's table keys and asserts equality with `{entry.id for entry in rubric.entries}`, in both directions.

**P2-7 (Medium, reproduced) — `_retrieved_documents` says "successful retrieval" and never checks the result.** `[docstring/code mismatch] [untested edge]`
`src/harness/core/context.py:341-357`: any `fetch_policy` call naming a document puts every clause of that document into ground truth, whatever its result. Reproduced: CALL-02 with the `fetch_policy` result forced to `error successful=false` still reports `retrieved_policies == ['refund.v1']`, so `governing_clause_not_applied` would charge the agent with ignoring clauses of a document that never arrived. All eight `fetch_policy` invocations in the design set succeed, so no test and no corpus call reaches the branch.
Closure: require `invocation.succeeded` (the `Invocation` helper already exists for this) and plant the failed-fetch fixture.

**P2-8 (Medium, reproduced) — `Provenance` accepts empty strings; an empty `CORPUS_VERSION` stamps every result blank and nothing fails.** `[criterion ticked against a neighbor] [missing validation]`
`Provenance("", "", "")` constructs. `load_corpus` (`cli.py:82`) deliberately builds `Provenance("", corpus_version, digest)` as a carrier and the caller rebuilds it. With a version file containing only a newline the run prints `results: 555   missing a provenance value: 555` and continues; the exit 1 that followed came from the gates, and a quiet rubric would exit 0. `test_every_result_carries_all_three_provenance_values` asserts the fields have no defaults, which is the neighbor of "no field is empty", and the registry docstring's "there is no path to a result that omits it" is true of `None` and false of `""`.
Closure: `__post_init__` refusing blank fields; `load_corpus` returning the three values rather than a half-built stamp; a CLI test with an empty version file; and the `missing_stamp` count either removed (unreachable once the type refuses blanks) or made fatal.

**P2-9 (Medium, reproduced where marked) — Precision and ordering hazards the design set does not exercise.** `[edge cases without tests] [potential improvements]`
Each is silent over the fifteen design calls; each is the kind of thing the held-out set exists to find. None is asserted either way.
- (a) `A-deadline-never-resolved` resolution signals are bare month names matched as substrings: `may` matches "maybe" and "you may"; `march` matches "marching". Two agent turns in the set carry "may"/"maybe"; none co-occurs with the relative phrase today. *By reading.*
- (b) `deadline_never_resolved` (`conduct.py:307`) looks for the resolution only **inside the turns that stated the relative phrase**; a resolution in a separate later turn still fires. CALL-09 has no later agent turn, so the corpus cannot show it. *By reading.*
- (c) `confirmation_requested_after_the_attempt` flags a call that asked **before and after** the attempt. *Reproduced*: CALL-09 with "Are you happy to go ahead?" appended to event 12 (before the refusal at 17) still returns `after`.
- (d) `spoken_local_date_wrong` compares the day only. *Reproduced*: CALL-19 event 12 rewritten to "twenty-third of May" against a 23 April door time returns `local`.
- (e) `_argument` and `_detail_field` (`records.py:38-45`, also `policy.py:197`, `conduct.py:127`, `omission.py:55,412,459`) and the `f"{argument}=" in …` test in `precondition_satisfied_by_assertion` have no leading boundary. The corpus already carries the colliding pairs `event`/`target_event`, `at`/`closed_at`/`rescheduled_at`/`scanned_at`, `band`/`price_band`, `note`/`internal_note`; no current rubric key is the short member, so this is latent. *Reproduced (pairs enumerated from the corpus).*
- (f) `timestamp_ordering_violated` compares ISO strings lexicographically, which holds only while both timestamps share format and zone; the spec calls them opaque. *By reading.*
- (g) `repeated_request_with_no_record` keeps only the **last** `STATE` index per name, so a variable set between the two asks and again after the last ask reports "no STATE event sets it between them". *By reading.*
- (h) `handoff_without_context`'s `required_state_after` and `precondition_satisfied_by_assertion`'s state lookup accept a state recorded anywhere in the call, including before the invocation; both names say "after". *By reading.*
- (i) `completion_claim_without_successful_write` and `governing_clause_not_applied` return `unevaluable` the moment one topic is ambiguous, discarding violations already collected on other topics in the same call. *By reading.*
- (j) `available_value_never_spoken`: an unknown `match` value falls silently to literal matching, while an unknown `from` raises. *By reading.*
- (k) `silence_exceeds_threshold` reads `earlier.body` off the raw stream for both speakers, so a caller's "one moment" clears the gap, and it bypasses the population seam that `context.py`'s docstring warns about. *By reading.*
Closure: a fixture per item, each planted as a control the way the W-tests are; word-boundary matching for signal lists (or a declared `match: word` option); a leading boundary in the two regex helpers.

**P2-10 (Medium, by reading) — The stale-report reuse path hard-codes a passing suite, and its staleness scan omits trees that tests read.** `[unsubstantiated statement] [mechanism gap]`
`tools/verify_phase1.py:load_suite_results` appends `0` to `_SUITE_EXIT` when it reuses a report, so both verifiers print "The suite as a whole passed too, not only the tests these criteria name" without reading the report's `failures`/`errors` attributes. A report with a failing test that no criterion names earns the sentence anyway. In CI the pytest step fails first, so the exposure is local. Separately, `_SOURCE_ROOTS` is `src, tests, tools, corpus, specs` and `_SOURCE_FILES` is `rubric.yaml, pyproject.toml, uv.lock`; `.github/workflows/checks.yml` (read by `tests/test_phase2_acceptance.py`), `hooks/pre-commit` (driven by `tests/test_hooks.py`) and the root `HELDOUT_SET` (read by `tests/test_holdout_absence.py`) are outside the scan, so an edit to any of them after a run leaves the old report "current".
Closure: derive the suite verdict from the report's own counts; add the three paths to the scan.

**P2-11 (Medium, by reading) — Documents the phase left behind.** `[stale statements] [undocumented omission]`
- `README.md` "Running it" lists `pytest`, `verify_phase1.py`, `findings_view` and `extract`; it does not mention `harness run --tier assert` or `tools.verify_phase2`. "What is here" describes `src/harness/` as "the event model, the transcript adapter, the extraction tier, the findings view generator" (no checks, engine, rubric loader or CLI) and `tools/` as "the phase-1 verifier"; the license table has no row for `rubric.yaml`, which D112 says is the third tree the license statement must name.
- `specs/taxonomy-coverage.md` Part 3: the section is still headed "GAP" and ends with "**Proposed closure**" though the criterion it proposes exists in the spec and is now met; its own maintenance rule (line 329) says "When a phase adds a deterministic check, tick the W it retires", and the phase-2 diff to this file touched only W13's wording. W2–W10, W20, W21, W22, W26 and W30 are all built and none is ticked.
- `pyproject.toml:15`: "PyYAML is the only runtime dependency in phase 1" sits beside a two-entry list (`tzdata` joined at P2).
- `src/harness/checks/values.py` `MatchMode` docstring: "W5 is the `` word boundary" has an empty code span where `\b` was lost.
- `specs/voice-agent-eval-harness.decisions.md` Document status: "D104–D108 open phase 2" while D104–D113 exist; true as written ("open"), but a reader counting will stop.
Closure: one pass over the four files; the taxonomy tick is the one with a stated rule behind it.

**P2-12 (Medium, by reading) — Tests whose names claim more than their bodies assert.** `[criterion ticked against a neighbor]`
- `tests/test_phase2_acceptance.py::test_the_workflow_runs_the_deterministic_tier_and_its_verifier` asserts the two verifier steps and nothing about `harness run --tier assert` or its `|| [ $? -eq 1 ]` guard, which is the one line in the workflow that encodes D105. Deleting that step would not fail this test.
- `tests/test_cli.py::test_a_run_whose_gates_all_hold_exits_zero` says the entry "is silent on every design call"; `lifecycle_event_missing` fires on CALL-12 (F-47), and the `threshold: 0.0` is what makes the gate hold. The exit-zero control is real; the docstring's reason is not.
- `tests/test_claim_checks.py::test_no_entry_declares_a_parameter_its_check_does_not_read` asserts that no result is `errored`; the unread-parameter guard raises `UnreadParameterError`, which is a different failure. The test still catches the case (the raise fails the test), but its assertion is about check exceptions, which P2-1 shows is its own property.
Closure: assert the `harness run` step and its exit-code guard from the workflow; fix the docstring; split the third into "the run completes" and "no result errored".

### Low

**P2-13 (Low, reproduced) — `RubricEntry.params` is immutable one level deep.** `MappingProxyType(dict(params))` leaves nested lists and dicts mutable and shared across every call's `ParamView`; `entry.params["required_system_events"].append(...)` succeeds. D109 records `ParamView` as the one non-frozen type; the frozen guarantee on the entry is shallow. Closure: freeze recursively (lists → tuples, dicts → `MappingProxyType`) at parse time, and a test that attempts the nested mutation.

**P2-14 (Low, by reading) — The policy-retrieval tool name is a class-6 corpus entity hardcoded in Python, ten times.** `src/harness/cli.py:52` `_DEFAULT_POLICY_TOOL = "fetch_policy"` is a CLI default, and nine test files each declare `POLICY_TOOL = "fetch_policy"`. The D106 register-binding test covers rubric inventories, not these. A rename in `corpus/entities.md` would leave ten copies and one test (`test_the_policy_tool_name_is_a_flag_and_not_a_constant`) that proves the flag reaches the seam but not that the default matches the register. Closure: one shared constant read from the register, or a test binding the default to `corpus/entities.md`.

**P2-15 (Low, by reading) — Engine and CLI edges with no test and, in two cases, no reachable path.**
- A check calling `satisfied()` on a three-member scale raises `RegistryError` inside the `try`, so it becomes `errored` rather than stopping the run; the docstring says rubric-shape defects "must stop the run". Untested either way.
- Duplicate `call_id`s in `contexts` are not refused; the roll-up counts both.
- `EntryRollup.gate_failed`'s `RubricSchemaError` branch is unreachable through the loader and untested.
- `cli.py:226` `if args.command != "run": parser.error(...)` is dead: `required=True` with one subparser makes argparse refuse first.
- `_repo_root()` resolves `parents[2]` of `cli.py`; correct for an editable install, wrong for a wheel installed into `site-packages`, where every default path then points outside the repo.
- Missing tests at the loader: a YAML `true` as `threshold` (the code refuses it), an empty-string `negative_instance`, a non-string `description` (silently stringified).

**P2-16 (Low, by reading) — Duplication in the rubric with nothing binding the copies.** Twelve month names appear in `A-deadline-never-resolved` (lower case) and `A-spoken-local-date-wrong` (capitalized); "at the end of my rope" is a trigger under both `dispute` and `escalation` in `A-declared-capability-not-invoked`; `hundred`/`thousand` appear in both number tables (P2-3). None is wrong; none has a test that would notice the copies diverging.

**P2-17 (Low, by reading) — The registry-to-rubric check is one-directional.** `test_the_shipped_rubric_loads_against_the_real_registry` asserts the rubric's checks are a *subset* of the registry. A registered check no entry uses would pass silently; today the two sets are equal (37 = 37) and nothing says whether an unused check is allowed. Closure: assert equality, or state the exemption.

---

## 3. Requirements against code, both directions

**Every P2 requirement has code and a test.** The twelve statements D104 counted map to verifier entries 1–22 and each entry's tests exist, pass, and assert the named property, with the caveats above: P2-3 (criterion text vs. mechanism), P2-2 (W5–W8 tests exercise code the tier does not use), P2-8 (provenance asserted as "no default", not "non-empty").

**Code with no requirement behind it**, each of which is needed and should be written down (a one-line requirement or a decision pointer), because the next phase reads this tier's behavior as settled:
1. `run_entry` converting a check exception into `status: errored` and continuing (engine.py:84-91). Needed so one broken check does not discard the run; see P2-1 for the missing consequence.
2. The CLI's exit code 2 ("could not start") and the by-name refusal of `--tier judge` (cli.py:14-23, 122-128). Needed so an empty judged run cannot look like success (D108).
3. The roll-up, `pass_rate`, `denominator` and the per-status breakdown (engine.py:121-191, cli.py:85-106). These implement the **P4** `WHILE` requirement early; the pull-forward is sensible and undocumented.
4. `RunReport`'s fixed total order by (call, entry) (engine.py:113-117). Implements the **P4** byte-identical property early.
5. `negative_instance` / `negative_instance_reason` and their refusals (rubric.py:86-102, 412-430). Backed by D107 only; the spec has no line for them, and verifier entry 24 says so.
6. The explicit `Registry` and `build_registry()` (registry.py, checks/__init__.py). Backed by the "unknown check key" refusal, indirectly.
7. `harness.corpus.policies` moved out of the hygiene test into the package (D65 support). Documented in the module docstring, nowhere in the spec.
8. `ResultBuilder.errored()` and `Status.REFUSED` in the roll-up: P3 producers, plumbed now. Documented in tests, not in a requirement.

---

## 4. Counts, enumerations and the mechanisms that hold them

| stated | referent | holds? | mechanism |
|---|---|---|---|
| 37 rubric entries | `rubric.yaml` | yes | none pins 37; `test_the_shipped_rubric_loads_against_the_real_registry` asserts subset only (P2-17) |
| 20 entries declare no negative instance (Not-checked block) | `rubric.yaml` | yes | prose count, no test |
| 61 `assert` findings, 61 traced | `corpus/findings.yaml` + rubric | yes | per-family tables (P2-6); the verifier caveat says otherwise (P2-5) |
| 12 P2 requirements, 22 P2 criteria | spec | yes | `MEASURED_CONTRACT` in `tests/test_document_counts.py`, by equality |
| 24 verifier entries = 22 anchored + 2 extras | `tools/verify_phase2.py` | yes | `test_the_unanchored_entries_are_the_declared_extras`, anchors asserted into the spec |
| "nine listed above are W2–W10" (criterion 13 caveat) | test list | yes (9 weaknesses, 12 tests) | none |
| D104–D113 contiguous, "continues from D114" | decision record | yes | the order mechanism `648bfa0` planted |
| 8 event kinds in exactly one population | `events.py` + `context.py` | yes | `test_every_event_kind_lands_in_exactly_one_population` |
| 14 call-record keys partitioned 10 + 4 | `REQUIRED_CALL_KEYS` | yes | `test_the_call_record_is_partitioned_with_no_field_in_neither_or_both` |

Lists that are numbered at print time only (`CRITERIA` via `enumerate`) cannot drift from their length. The one enumerated-by-hand structure with no length check is the set of per-family firing tables (P2-6).

---

## 5. Mechanisms versus memory

| "remember to …" | mechanism | gap |
|---|---|---|
| run the suite, type check, linters, both verifiers, the tier, the held-out scan, the findings view | `.github/workflows/checks.yml`, every step present and tested for presence | **CI has never run on `phase-2`**: the workflow triggers on push to `main` and on pull requests, and the branch is local. Eighteen commits are verified only on the author's machine. Open a PR or push to a branch the workflow watches. |
| refuse a populated `.env` or a `private/` path | global `pre-commit` (Case 2 install), plus `tests/test_hooks.py` | none |
| keep the verifier's criteria list equal to the spec's | anchors + `test_every_p2_criterion_in_the_specification_is_claimed_by_the_verifier` | none for the *tests* an entry names being the complete set for its claim (P2-4) |
| keep every entry covered by an agreement test | none | P2-6 |
| tick the W a phase retires | prose rule in `taxonomy-coverage.md` | no test; not done (P2-11) |
| reuse a JUnit report only when current | mtime scan | three trees outside it (P2-10) |
| keep `README` current with the CLI | `test_document_counts.py` guards numbers, not the running section | P2-11 |

---

## 6. What was not checked

- The held-out repository, its transcripts and any label work; `comparative-judgment`; both withheld source folders.
- Whether the 37 signal lists are the *right* abstraction for their findings (the Not-checked block already records that no test can say).
- Corpus plausibility, seeding quality, and adjudication rulings.
- P3+ design (transport, judged tier), except where a P2 type pre-plumbs it.
- Performance: the suite takes 163 s locally, dominated by tests that re-run the whole tier per case; not measured further.

---

## 7. Suggested order of work

1. P2-1 (exit code on errored), P2-8 (blank provenance): both are fail-open paths, both small.
2. P2-4, P2-5, P2-6: the verifier's phase gate, so the PASS it prints means what it says.
3. P2-7 (failed fetch), P2-3 (criterion text, decorative lexicon entries).
4. P2-9 fixtures, one per item, planted as controls.
5. P2-2 decision: route an entry through the value layer or fence the four functions off.
6. P2-10, P2-11, P2-12 documentation and test-name repairs; push the branch so CI runs.
7. P2-13 to P2-17 as they are touched.
