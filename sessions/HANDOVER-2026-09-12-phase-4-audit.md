# Handover — remediating the phase-4 audit

**Status:** closed 2026-09-22 — every item it carries is registered as OB-24 to OB-36 and closed there with evidence, 13 of 13. Opened 2026-09-12, at `64b5848`. Answers `sessions/AUDIT-2026-09-12-phase-4.md`, which
is a report rather than a prompt, so this document carries the findings that report placed after the
freeze rather than a contract. The report's working-status banner records each finding's disposition.

**Where the numbers stand:** 18 findings. Before the freeze six were closed and two half closed —
P4-7 (`415affe`); P4-1, P4-2 and P4-8 (`c5f7ab9`, D158); P4-3 (`eda6c17`); P4-6 (`57ee0d3`, D159), with
part of P4-13; and the band pin, half of P4-5 (`64b5848`). Every checkable claim in the report was
reproduced independently first, and every one held. Five corrections to the report are recorded in its
banner.

**Why the rest is owed here.** The audit placed ten findings, and the remainders of two, after the
`rubric-frozen-v1` tag, and its fourth re-verification added P4-30, carried here as item 13 on the owner's decision. A list in a banner is read by whoever opens it; a numbered item under the heading
below is harvested by `tests/test_obligations.py` and has to have a row in `OBLIGATIONS.md`, which is the
difference this project draws between a result and a rule. Every row's trigger is the tag existing — an
event `git tag --list rubric-frozen-v1` shows, rather than a phase name nothing reads once the phase
closes, which is the point P4-15 makes about the triggers before these.

---

## What is owed

### 1. A resume that serves nothing says nothing, and its header still claims it resumed

P4-4. `ResumingTransport.served` is read nowhere, the command prints how many answers the log holds before the run and never how many it served, and `resumed_header` names the earlier session whether or not an answer came from it. A criteria edit that leaves the rubric version unchanged passes the staleness check, so every request misses and the resume silently does nothing. The closure: print the served and issued counts when the run ends, name the earlier session in the header only when an answer was served, and test a resume under an edited entry. D159 worded the `--resume` requirement to what is built so this fix has something to meet. A refusal before confirmation is possible for the dimensions and not for the synthesis, whose requests cannot be known ahead of the run.

### 2. The severity loader accepts an inverted, single-anchor or unnamed cut, and never checks a band against its midpoint

P4-5's remaining half. `parse_severity` accepts a cut whose anchors are inverted, a cut anchored on one finding at both ends, and a cut named `nonsense`, all three reproduced; the tool refuses the first and has a closed name set. Nothing compares a row's band with the side of its cut midpoints its `theta` falls on, and all 83 agree today. The band pin makes a re-banding fail by name; these checks are what would refuse a malformed file rather than notice a changed one.

### 3. The severity tool's log hash depends on the platform's line endings

P4-9, in `comparative-judgment`. Its writers pass no `newline`, and `log_hash` hashes the log's raw bytes, so the same judgments recorded on another platform carry a different `comparison_log_hash` and `run_id`. The report overstated the claim this breaks — the tool's criterion promises identical exports over an unchanged state and names no platform — and the defect stands. The report's closure removes the trade-off it was deferred for: normalize line endings inside `log_hash`, write LF in both writers, rewrite the existing store once and re-export, pushed with this repository.

### 4. No test holds the phase-4 verifier's CI step

P4-10. `test_the_workflow_runs_every_phase_verifier_and_the_inventory` names three verifiers, so removing the phase-4 step from `.github/workflows/checks.yml` fails nothing, reproduced. The closure: derive the list it checks from the verifier table the same module holds.

### 5. A torn run log escapes the reader as a raw decode error

P4-11. A log cut mid-line makes `read_run_log` raise `JSONDecodeError`, so replay and report exit 1 — the code for a failed gate — with a traceback, reproduced, and a resume refuses naming no file. The closure: refuse with a named error giving the file and line, and let a resume read to the last complete record and say how many lines it dropped.

### 6. The report test's credential mechanism is not the one that holds

P4-12. `test_the_report_is_produced_on_a_clone_with_no_credential_in_reach` says running from a directory with no `.env` puts the file out of reach, and the phase-4 verifier's first caveat repeats it; the command looks for `.env` at the repository root whatever the working directory. The assertion holds because the report path reads no credential. The closure: state that reason in both places, or run the command from a copy of the tree without `.env`.

### 7. Two stale statements the pre-freeze sweep left: the report caveat and the OB-17 figures

P4-13's remainder. The report's non-determinism caveat says N repetitions measure evaluator variance over a fixed transcript, which since D154 is not all the synthesis's repetitions measure; and OB-17's evidence quotes figures from the log D154 and D155 replaced. Changing the caveat regenerates the snapshot.

### 8. Nothing carries the recording that overran the synthesis's old ceiling

P4-14. The fill-fraction watcher reads the committed log, where the synthesis's largest answer is 2,140 tokens, so a ceiling lowered to 8192 or 4096 passes every check, while the recording that stopped at 8,192 on CALL-08 is uncommitted. The report's closure pins that file's name and hash in a test, which would fail on CI and on any clone without it. The closure that works is a dated constant carrying the truncation, and a mutation lowering the synthesis to 8192.

### 9. Deferred triggers nobody will notice mechanically

P4-15. OB-23's trigger is a session writing to a gitignored store, OB-7's names a phase, OB-5's is an activity, and OB-16's is the remaining work itself. The closure: a test that reads deferred rows' triggers against observable events — the rows carrying this handover's items use one, the tag existing — and, for OB-23, the band pin, which now notices what that trigger could not.

### 10. The expected cost counts no informed retries

P4-16. The pre-flight's expected figure prices first attempts, and the synthesis has produced nine, seven and eight informed retries in three recordings; today the input over-estimate covers the gap. The closure: multiply each entry's calls by the retry share its log recorded, print the share, and flag answer lengths read from a log whose header is stale.

### 11. The interface scanner agrees on a subcommand's name, not the field

P4-17. `tools/check_spec_interface.py` matches a backticked field name anywhere in either specification, and the tool's pushed specification names `cuts` only as a subcommand, reproduced. The closure: match fields inside the field-list sentence each specification carries, or give both sides a machine-readable field block.

### 12. Most of the phase-4 verifier's caveats are history rather than limits

P4-18. Eighteen of its twenty-four entries carry a caveat, and most say when a criterion was added rather than what its tick does not buy, in the section a reader is told to read instead of the ticks. The closure: keep provenance in the criterion or its decision, and reserve the caveat for a limit.

### 13. The retry names the first failure it finds, so an answer with two faults is corrected for one

P4-30. `_validate` reports one failure, in order: the parse, then the citations, then `rests_on`. A synthesis answer citing `T999` with an empty `rests_on` is sent a retry naming `'T999'` alone, and one with both lists empty a retry naming the empty `citations` list alone; a retry that fixes the named fault and keeps the other is refused, and the result is `errored` — the one retry the requirement grants spent on half a correction. The committed log holds no such answer, since its 8 retries each corrected rejected citations and nothing else. The closure: collect every failure in `_validate` and name them all in the correction, keeping the recorded retries' wording where a single failure is found; `parse_answer`'s empty-citations refusal has to let `rests_on` be read as well.
