> **STATUS as of 2026-09-06, added when this report was committed.** Every finding acted on was
> reproduced first, and the baseline in §1 was reproduced exactly (354 tests, artifact `5767c15a…`).
> **All five High findings held.**
>
> **Closed:** H-1 (sweep performed, 0.21.0 @ D86, and the trigger is now a test), H-2 (de-quantified
> per D74, `_HELDOUT_SET_SIZE` guard added), H-3 (real severity file read by a test; two refusals in
> `join`), H-4 (`agent turn` dropped, unresolvable kind refused, two controls planted), H-11 (three
> tests retargeted at the gold set; criterion names all eight keys), the `severity.py` half of H-9,
> the two stale caveats in `verify_phase1.py`, C-1 (pushed), C-2 (CI runs the configured scope),
> and the H-18 / H-2 banners on three spent documents.
>
> **Second pass, 2026-09-06, by a session cleared for design-corpus work.** **H-6** closed by repair
> rather than by declaring the drift (D87): `EV-88011` realigned, a new id allocated for the later
> performance, and the held-out repository's widened check ported as a sibling with a planted control.
> **H-7** closed both halves (D88): the escalation convention is in the register, written without
> naming a transcript so it survives the authoring packet's redaction, and the register's design-set
> and held-out enumerations are now compared against their declarations. **H-16 decided** along with
> it — `Outcome.transferred` stays, because D39's argument for wide vocabularies outranks D73's
> schema smell, and what was missing was the sentence saying it is never correct here. **H-8** closed
> by de-quantifying all three statements (D89), one of which was wrong in a way this report did not
> name: it counted the wrong population as well as counting it stale. **H-5** closed by bringing the
> scenario map current rather than superseding it (D93): superseding was not available, because
> `specs/taxonomy-coverage.md` calls that map "the authoritative allocation" and the guard binding each
> judged dimension to its instantiating finding reads its rows. All eight cited lines reproduced; two
> needed correcting first, and both fixes stand for different reasons than this report gave.
>
> **Third pass, 2026-09-07.** **H-9** closed both halves and widened the guard that missed them
> (D94) — the ledger header also said the gold set "does not exist", the same sentence this report
> found in `severity.py`, whose fix had not reached it. **H-10** closed (D95), with two guards: the
> specification's own retarget markers, and the two retired CI sentences paired with the `exit 1`
> that falsified them. **H-13, H-14, H-15 and H-17** closed (D97, D99). **H-12 is half closed**: the
> prohibition now governs content wherever it lives, and this report's proposed widening was
> **rejected with a reason** — forbidding the whole held-out repository except its README and
> workflow would have forbidden the work that discharged `HOLDOUT-OBLIGATIONS.md` O-4 to O-6. The
> two docstrings were filed there as O-7 and **closed later the same day**, composed without
> reading the ones they replaced. The sweep this report's H-1 made mechanical then fired at
> eleven accrued decisions and was performed (D98), taking the specification to 0.22.0.
>
> **§3's O-1 to O-6 are closed**, later the same day. **O-2 to O-6** by writing checks in the
> held-out repository rather than by reading it — the four conventions ported, including the
> `_sourced_by` AST-equality test D83 left open; the labels denylist inverted to an allowlist over
> tracked files, which the old root-only glob let `transcripts/CALL-13.labels.yaml` through; the
> `HELDOUT_SET` mirror made mechanical; a lint, format and type gate where there had been no
> configuration at all; and the packet builder's leak scan tested in both directions. **O-1 closed
> too**, and its framing here was the thing worth correcting: it needed no reader. Persona
> extraction is deterministic, so a generator writes the declaration, the owner runs it once, and CI
> re-runs it in check mode. The count it produced matches exactly what this report's own contaminated
> session found by reading them.
>
> **Open: nothing, as of 2026-09-07.** Every finding in this report is closed.
>
> **H-12's docstrings** closed as `HOLDOUT-OBLIGATIONS.md` O-7 — and the prediction made here was
> wrong in a way worth keeping. This section said the work was "best done by a session **already**
> contaminated", reasoning that rewriting held-out content out of a docstring requires reading it.
> It does not: the replacements were **composed without reading the ones they replaced**, so a
> clean session did the work and no session was contaminated for it. The same correction landed on
> O-1, where this report asked for a cleared reader and a generator was enough. **Twice, the
> assumption that held-out work needs a contaminated session was the expensive half of the
> finding.**
>
> **C-3 to C-10** closed in comparative-judgment (D27–D32 and the commits beside them): the D14
> retags, `Progress.complete` in placement mode, a CJ-side interface trigger, the ticks removed
> rather than made to mean something, US spelling with a shape-based guard, exact pins, an
> enforced coverage floor, and the header that restated a high-water mark.
>
> **Two things both number themselves O-n, and this line is the disambiguation.** §3's O-1 to O-6 are
> *this report's* findings about the held-out repository, and are now all closed.
> `HOLDOUT-OBLIGATIONS.md` has its own O-1 to O-8, **all eight discharged**. The two sequences are
> unrelated and neither renumbers, because both are cited by number elsewhere — which is why this
> paragraph exists rather than one of them being tidied away.
>
> **This block went stale on 2026-09-07**, in the *Open* paragraph — the one line a reader opens
> this file for. Three later passes appended what they closed and none revisited the bottom, so the
> report named two things as open that were shut hours earlier. It is the shape the whole report is
> about, in the report's own summary, which is where `HOLDOUT-OBLIGATIONS.md` records the same
> thing happening to its discharged heading twice. The difference is that that file's count is
> computed and this paragraph is prose, and prose about what is open is not a countable claim.
>
> **This block is the only part of this report that is maintained** — §1's baseline
> (354 tests, artifact `5767c15a…`) and every finding below are dated records of what was found on
> the day, and are deliberately not edited to agree with later work (D53).
>
> The open items are the live list; this report is the record of how they were found.

# Audit report — voice-agent-eval-harness · voice-agent-eval-harness-holdout · comparative-judgment

**Date:** 2026-09-06. **Auditing session:** `48bc4312-7f9c-4a89-bec7-6b894bd1734c`. **Nothing in any of the three repositories was changed.** Every command that writes ran against a scratch copy.

## 0. Read this first

**This session is contaminated, by design and with the owner's clearance.** It read all six held-out transcripts end to end, the held-out repository's commit subjects, and its test docstrings. Everything in this report about the held-out set is a count or a rule, never content, and the session id is recorded in the contaminated-sessions memory. **Do not resume session `48bc4312-…` for rubric, gold-set, held-out-label or design-corpus work.** The report itself is safe to keep in the harness tree.

**What "recent work" covered.** Harness: `d8c219c` (2026-09-04) through `6535862` (2026-09-06), i.e. severity scoring, D78–D86, the held-out discharge and CALL-21. Held-out repo: everything on 2026-09-06 (`56a5c1d` … `fb209bf`). Comparative-judgment: last commit 2026-08-29, one commit ahead of origin. Everything else in all three repositories was read too, so the findings are not limited to that window.

**Severity key.** *High* = a claim the project makes is currently false or a guard it relies on does not bind. *Medium* = a real gap, inconsistency or unenforced rule. *Low* = hygiene, dead code, wording.

---

## 1. Baseline, established by running it

| Check | Result |
|---|---|
| Harness `pytest -q` | **354 passed** in 128 s, none skipped |
| Harness `ruff check`, `ruff format --check`, `mypy` (strict, src+tools+tests) | all clean |
| Harness `python -m harness.extract` | 15 calls, 375 events, 0 unparsed; hash `5767c15a…` |
| Harness `tools/verify_phase1.py` | 21/21 pass, 4 caveats (two of them stale, see H-2, H-3) |
| Harness `check_holdout_absence`, `make_gold_set --check`, `findings_view --check`, `statement_inventory` | all pass |
| Harness `check_spec_interface` vs local CJ **and** vs CJ `origin/main` | both OK (6 keys, 7 fields) |
| CJ `pytest` with coverage | **223 passed**, 98 % (1153 stmts, 20 missed) |
| CJ `ruff check`, `ruff format --check`, `mypy --strict src` | clean |
| CJ `mypy` **as configured in pyproject** (src + tests) | **fails**: `tests/test_constraints.py:171` (see C-2) |
| Held-out `pytest tests` (harness auto-detected as sibling) | 6 passed |
| Held-out `.py` files under the harness's ruff / format / strict-mypy standards | 12 ruff errors, 1 file unformatted, 1 mypy error (see O-5) |
| Global git hooks (a machine-wide hooks directory) | pre-commit carries SECRET-GUARD, PRIVATE-GUARD and the contradiction gate; pre-push carries the owner check; `gh` is authenticated as `hmbseaotter` |

**Severity provenance chain, reproduced end to end (this closes D82's open gap empirically as of today):**

- `sha256(.cj-store/comparisons.jsonl)` = `9771a324…` = `comparison_log_hash` in `corpus/findings.severity.json`. The log holds 410 comparisons and 1 accepted revision.
- `cj load` on a **copy** of the store against `corpus/findings.yaml`: 82 admitted, 7 question-tier excluded, **no pending revision or removal** — the gold-set text has not moved since the export.
- `cj export` from the copy is **byte-identical** to the committed severity file, run id `053f9e69d7a79cc0` included.
- The 82 scored ids equal the 82 `tier: defect` ids in the gold set; the 7 excluded ids equal the 7 `tier: question` ids; `unplaced` is empty.
- `cj status`: min appearances 10, mean 10.00, 5.00 comparisons per item — D8's ~10 estimate is met exactly.

---

## 2. Harness findings

### High

**H-1 — The specification's own sweep trigger has fired and no sweep has happened.**
`specs/voice-agent-eval-harness.md:12` reads `Last swept: 2026-09-01 @ 0.20.0 @ D71 — trigger: ~8–10 accrued decisions`. The decision record is at **D86**: fifteen decisions have accrued. The spec header, version and "Not checked" block are all still at 0.20.0/D71, and the changelog has **no entry for D79–D86** (D78 was appended into the *0.19.0* entry, out of sequence). Every stale statement in H-2, H-9 and H-10 is what the trigger exists to catch, and nothing binds it: `test_the_spec_version_and_the_last_sweep_agree_with_the_changelog` ties the marker to the version but nothing compares the accrued-decision count to the trigger. **Fix:** perform the sweep and bump (D71's own precedent); add a test asserting `highest D − last-swept D ≤ 10`, so the trigger becomes a mechanism.

**H-2 — Statements about the held-out set that commit `cdb896a` ("bring every statement … current after it grew to six") did not reach.**

| Location | Says | Should say |
|---|---|---|
| `specs/voice-agent-eval-harness.md:42` | "5 held-out transcripts authored" | six / the declared set |
| `specs/voice-agent-eval-harness.md:109` | "fifteen design calls + 5 held-out" | six |
| `specs/voice-agent-eval-harness.md:284` | phase 1 "the 5 held-out transcripts" | historical, but reads as current |
| `tools/verify_phase1.py:210` | criterion text "The 5 held-out transcripts exist" — while its own caveat (line ~226) claims "This text said 'the five' … until 2026-09-06" | the text was not changed; the caveat asserts a correction that did not happen |
| `HOLDOUT-OBLIGATIONS.md:90` | "every `fetch_policy` call in `CALL-13`…`CALL-17`" | the set |
| `HOLDOUT-REPAIR-BRIEF.md:1,48,126,163` | title enumerates five; "exactly the 14 declared design transcripts" (15); "the five carry none of the vocabulary added since" (falsified in OBLIGATIONS); "asserts the set is exactly CALL-13…CALL-17" — under a "Brought current 2026-09-06" banner | bring current or mark the sections historical |
| `HOLDOUT-SESSION-PROMPT.md:15,79,84` | "You MAY read … CALL-13 … CALL-17"; "holdout HEAD ee82c0b"; "no `tests/`, no `pyproject.toml`" | the document's purpose is spent; it needs a status banner like the brief's |
| `HANDOVER-adjudication-2026-09-01.md:215` | O-1…O-3 "all three still ☐" | discharged 2026-09-06 (item 2 of the same list *was* struck through on 09-05, so the file is being maintained selectively) |
| `specs/voice-agent-eval-harness.decisions.md:3346–3347` (Not checked) | "The design-set findings have not been scored … Scoring is now the next step and has not been taken"; "Now populated: five transcripts" | scored 2026-09-05 (D82); six |

**Why nothing caught it:** `_DESIGN_SET_SIZE` in `tests/test_document_counts.py` scans number *words* followed by `design/transcript/call`; "5 held-out", "the five", "CALL-13…CALL-17" are all outside it. **Fix:** a `_HELDOUT_SET_SIZE` guard reading `HELDOUT_SET`, scanning the same nine documents plus `HOLDOUT-*.md`, `HANDOVER-*.md` and `tools/verify_phase1.py`; and rewrite counts that are not load-bearing as "the held-out set" (D74's own rule: quantifying a claim makes it decay).

**H-3 — The real severity file is never read by the suite, and the phase-1 severity criterion is verified only against a fixture.**
`grep findings.severity tests/` finds nothing. `tools/verify_phase1.py:98` still caveats criterion 5 with "The real scoring run … has not happened yet" — it happened on 2026-09-05. Two adjacent gaps in `src/harness/core/severity.py`: `join()` does not refuse a **scored question-tier** finding (it only tolerates absence), and the `severity` band string is never validated against `{critical, high, medium, low}`. **Fix:** one test that loads `corpus/findings.yaml` + `corpus/findings.severity.json`, asserts the join is total, `unplaced` is empty, the 82/7 split, and every band is in the vocabulary; a refusal for a scored question; retire the caveat. (The provenance check in §1 is what that test would automate.)

**H-4 — A branch of the evidence checker counts a fragment as checked and never evaluates it.**
`tests/test_findings_evidence.py:88` admits `agent turn` as a `_GAP_CLAIM` kind; line 253 then filters `e.kind.name == "agent turn"`, which no event kind is named, so `of_kind` is always empty. Live instance: F-15's fragment *"No agent turn between events 20 and 27 asks the caller to confirm the transfer"* (`corpus/findings.yaml:417`) increments `checked` and passes vacuously. The fragment is a claim about the *content* of agent turns, not their absence, so mapping the kind to `AGENT` would false-positive (event 25 is an agent turn). **Fix:** drop `agent turn` from the alternatives so the fragment falls through to the reviewer's branch, or require the claim to end at the indices; plant a case either way. D72 records this branch as "planted against three ways" — the fourth shape was not among them.

**H-5 — `specs/taxonomy-scenario-map.md` claims currency ("Scope, as of 0.20.0") and still describes format v1 and the pre-D44 canon.**
Lines 125 (`Thornbury Building Society`, `payment_instrument` — the corpus has Northfield Credit Union and `charge_count`), 127 (`Gallery band` — not a declared band), 142 (`returns OK` — no such status), 145 (`CONFIG` kind — v2 has none), 165 (`call_ended`, `duration_seconds` — v2 names are `call.ended`, `duration_ms`), 166 ("one timestamp per event (D33)" — superseded by D40), 182 (`UNAVAILABLE`). The banner at line 4 names CALL-18 and CALL-19 "mapped in `specs/error-type-sweep.md` instead" and omits CALL-20, which that file does not map either (S11 lives in taxonomy-coverage Part 2b). The document's own rule ("When the corpus changes, this map changes first") is not being followed, and the tests bind only row existence and the F-ids on rows 17/31. **Fix:** either banner it SUPERSEDED like the build prompt, or bring it current and add a check that every backticked token in it is declared in the event model or register and every proper noun is a Class 1/5 entity.

### Medium

**H-6 — D85's design-set half is still open and confirmed present.** `EV-88011` carries three `door_time` values across CALL-01 (`19:00Z` on 03-19), CALL-02 (`19:30Z` on 03-26) and CALL-18 (`19:30Z` on 03-19); `test_one_event_title_per_event_id_except_where_drift_is_seeded` compares titles only. Undeclared drift in the design corpus; the held-out repository's widened check (`_EVENT_SCOPED_FIELDS`) is the shape to port. Needs a session cleared for design-corpus work.

**H-7 — Two more items D83/D86 handed to "a design-corpus session" are still open.** (a) The escalation convention `outcome: resolved` + `disconnection_reason: transferred` + `outcome_reason: escalated` lives in the seeding manifest and in per-machine memory; `corpus/entities.md:228–236` declares `escalated` but not which `outcome` an escalation takes — the exact gap that produced CALL-21's one wrong field. (b) `corpus/entities.md:242` (`Design set: …`) is prose about `corpus/DESIGN_SET` with no test comparing them; D83 says "a few lines and would have caught it — not written here". Also the packet builder's `LINE_REDACTIONS` targets that very line, so keeping it correct matters twice.

**H-8 — Register and manifest counts that are wrong against the corpus.** `corpus/entities.md:172`: "Thirteen design calls carry `caller_ani`; CALL-18 carries `booking_reference`" — all **15** carry `caller_ani`, and CALL-18 carries both (its `matched_by` is what differs). `corpus/seeding-manifest.md:25`: "Without the **eleven**" beside a list of **twelve** calls; "the **fourteenth** uses something weaker still" in a fifteen-call set. The derived test checks the call list, not the words. (The packet builder's `REDACTIONS` matches the `Thirteen design calls` sentence verbatim, so fixing it will make that pattern go stale — the leak scan is what guards that, correctly.)

**H-9 — Documents that still call the drafts "the findings document".** `corpus/seeding-manifest.md:7` ("Not the findings document — that is `corpus/findings.candidates.yaml`") and `:53` ("the statements live in `corpus/findings.candidates.yaml`"); D77 made `corpus/findings.yaml` the document and `findings.md` its view. `src/harness/core/severity.py:10` still says `corpus/findings.yaml` "is deliberately absent until a human has worked through the candidates" — it has existed since 2026-09-01. The adjudication ledger's header (`findings.adjudication.yaml`) names `test_the_review_worksheet_on_disk_is_current`, which no longer exists; the Rule-line guard scans only the decision record.

**H-10 — Specification contradicts the workflow and itself.** `specs/voice-agent-eval-harness.md:29` still says the CI interface assertion "emits a warning rather than failing when [the sibling] is absent" — D84 made both workflows fail (`checks.yml` `exit 1`). Lines 178 (`WHERE [P6] the JSONL adapter is selected`) and 311 (phase 6 "Includes: JSONL adapter") contradict the in-scope P6 bullet and D40, which retargeted adapter 2 to a real vendor shape.

**H-11 — Phase-1 acceptance tests bound to the drafts rather than the gold set.** `tests/test_findings.py:69` (`test_every_entry_carries_every_required_key`), `:243`, `:385` load `findings.candidates.yaml`; the spec's criteria are about "the findings document", which D77 settled as `findings.yaml`. `tools/verify_phase1.py:75` still lists six keys where the spec's criterion lists eight (`call_ref`, `owner`). Cheap to retarget; the gold set is what agreement is measured against.

**H-12 — Held-out *content* lives outside `transcripts/`, where the read prohibition does not reach.** `HANDOVER-adjudication-2026-09-01.md` prohibits reading the transcripts directory and the commit messages; `voice-agent-eval-harness-holdout/tests/test_holdout_conventions.py:180` and `:352` describe, in docstrings, a repaired defect and a repaired cross-call contradiction in that set. Both are history now, but they are exactly the "counts and rules, never content" line the brief draws, crossed in a file any harness session may open. **Fix:** rewrite those docstrings as rules (the brief's own standard), and widen the prohibition's wording to the whole held-out repository except its README and workflow.

### Low

- **H-13** `src/harness/corpus/text_adapter.py:383` — a second `if not body` inside the speech branch is unreachable (line ~366 already raised). `:586` — the "file is empty" branch is unreachable: `"".split("\n")` is `[""]`, so `lines` is never falsy; an empty file reports "first line must be …, found ''".
- **H-14** No test for a **BOM-prefixed** transcript; the header check would refuse it with the message above. Given the project's own `Out-File -Encoding utf8` incident (commit `6535862`), reading with `utf-8-sig` or naming the BOM in the refusal is worth a case.
- **H-15** `tools/check_holdout_absence.py` never reads `HELDOUT_SET`, so a genuine held-out copy is reported as "declared neither in DESIGN_SET nor FIXTURE_SET" rather than "this *is* a held-out transcript"; `tests/test_holdout_absence.py` hard-codes `CALL-13` instead of taking an id from `HELDOUT_SET`.
- **H-16** `Outcome.transferred` stays in the closed vocabulary although D73 calls it "a schema smell" and D86 shows it misled the authoring session; nothing says when it is correct. Deprecate in the register or document the case.
- **H-17** Wording: `tests/test_corpus_hygiene.py:1720` "fourteen calls"; `specs/error-type-sweep.md:150` "ten classes as `S1`–`S10`" (eleven); `corpus/entities.md:154` and `:162` are two "**Closed vocabularies**" paragraphs saying overlapping things; in the same file the sentence "That combination is the thing to watch: a name is not personal data and a ZIP is not…" now follows the held-out sentence rather than the name-plus-contact-details sentence it refers to.
- **H-18** `HANDOVER-adjudication-2026-09-01.md:4` opens "Nothing in this session has been committed" and is dated, yet items 2 and 9 were updated on 09-05 while item 3 was not on 09-06. Either freeze it under a banner or maintain all of it.
- **H-19** Commit `6535862` has a UTF-8 BOM in its subject (known; back-burner).

---

## 3. Held-out repository findings (counts and rules only)

**O-1 (Medium) — Six agent persona names used across the held-out set are declared nowhere.** `corpus/entities.md:69` declares thirteen personas "used in every call" — the design set's. `test_every_agent_persona_is_declared` (D74) covers the design set only and is not ported; the authoring packet copies the register, so a new authoring session inherits no persona list either. Decide where held-out personas are declared (the register is the Class 1 canon and persona names are vocabulary, not labels; the alternative is a held-out-side declaration file) and port the check.

**O-2 (Medium) — Four harness conventions hold in the held-out set today only by luck, because nothing there runs them.** Verified this session against all six: every context, state, tool, disclosure, outcome and reason name used is declared in the register (0 undeclared in each class); the platform is named in every call; every `event="X at Y"` names declared entities; speech plausibility holds (61 measurable utterances, 0 outside 110–185 wpm, median 145). The persona check fails (O-1). None of these run in the held-out CI. Port them (they need only the parser and the register, both already checked out there), or take D83's suggestion and move the shared helpers into the `harness` package. Cheapest first step: a test in the held-out suite that parses both `_sourced_by` bodies with `ast` and asserts equality — the two copies are logically identical today (only the harness copy is annotated), and that test turns "two copies can disagree" into a red build.

**O-3 (Medium) — The labels guard is root-only and name-shaped.** `.github/workflows/checks.yml:65` runs `ls labels* label-* *labels*.json *labels*.yaml` in the repository root. `transcripts/CALL-13.labels.yaml`, `gold.yaml`, `annotations/`, `ground_truth.md` all pass it. **Fix:** invert to an allowlist — `git ls-files` must equal exactly `README.md`, `LICENSE`, `.gitignore`, the workflow, `voice-agent-eval-harness-holdout/tests/test_holdout_conventions.py`, `voice-agent-eval-harness-holdout/tools/build_authoring_packet.py` and `transcripts/CALL-*.txt`. Stronger, shorter, and it also catches a stray packet.

**O-4 (Medium) — `HELDOUT_SET` is a manual mirror with no check, and the check is one line away.** The held-out workflow already checks the harness out at `.harness/`; a step asserting `.harness/HELDOUT_SET` (comment lines stripped) equals the stems of `transcripts/CALL-*.txt` closes the "standing duty" in `HOLDOUT-OBLIGATIONS.md` mechanically, in the only place that can see both sides.

**O-5 (Low) — No lint, format or type gate for the held-out repository's own Python.** Under the harness's configuration: 12 ruff errors (mostly line length in `voice-agent-eval-harness-holdout/tools/build_authoring_packet.py`), that file would be reformatted, and `tests/test_holdout_conventions.py:115` fails strict mypy because the "verbatim" copy of `_sourced_by` dropped its parameter annotations. The workflow also lacks the `permissions:` and `concurrency:` blocks its two siblings carry.

**O-6 (Low) — The packet builder is untested.** Its whole guarantee is "the leak scan deletes a leaking packet"; no test plants a design-set identifier and asserts the packet is gone and the exit code is 1. It also copies the held-out transcripts to a directory outside every repository by default — correct, but worth a test that the output never lands inside a git tree.

**O-7 (Info) — Reconciled counts.** All six parse with 0 unparsed lines. Non-excepted tool-call arguments: 23 across the original five (`HOLDOUT-OBLIGATIONS.md` says twenty-six before the three `clause` arguments were removed, twenty-three after — consistent), 31 across six, 0 unsourced. `fetch_policy` calls: 3, all stating the real clause count. Two pairs of calls share an event id, so the ported door-time check compares something. All six carry `caller_ani`. Commit subjects are metadata only and carry no content.

---

## 4. Comparative-judgment findings

**C-1 (High) — One commit is unpushed.** `3766b9e` (2026-08-29, "Narrow D1's committing licence from synthetic to design-set") exists only locally; `origin/main` is at `55adadd`. The harness CI checks CJ out from GitHub, so the record the harness's D61 reasoning relies on is unpublished (the interface scanner passes either way — verified against `origin/main`). Push it.

**C-2 (Medium) — The declared type-check scope is not what CI enforces, and the declared scope fails.** `pyproject.toml:53` says `files = ["src", "tests"]`; `.github/workflows/checks.yml:52` runs `mypy --strict src`; `uv run mypy` as configured fails at `tests/test_constraints.py:171` (`package["name"].lower()` on `object`). The spec ("mypy --strict across the package") and the harness's own argument for type-checking tests (most assertions live there) both point at fixing the test and running the configured command.

**C-3 (Medium) — Requirements D14 moved to phase 2 are still tagged P1 and are unimplemented.** `specs/comparative-judgment.md:123` (WHILE P1: "an estimate of comparisons remaining"), `:156` (P1 NFR: "estimated remaining, and elapsed session time"), `:16` (reproducibility of "standard errors"), `:239–240` (phase-1 floor "with … standard errors", chosen optional "session timer"). The in-scope list and D14 say P2; the TUI shows only "items still short: N" (`ui/tui.py:143`). Retag or reword so a phase walkthrough cannot tick them against a neighbor.

**C-4 (Medium) — `Progress.complete` uses bootstrap semantics after placement.** `core/session.py:314`: `complete = not below and not blocked`, with `below` computed against the appearance target. Reproduced this session: after a newcomer is fully placed (3 comparisons, `next_pair()` is `None`, `placing=True`, the item is banded), `Progress.complete` is `False` and `items_below_target == ("F-NEW",)`. The TUI compensates via `placing`; `cj status` does not and prints `complete no` plus a "below target" line for a finished placement. The spec's own acceptance line ("after cuts exist it does not report the appearance target as the finishing condition") is met only in the TUI. **Fix:** in placing mode, complete = every non-anchor judged item has ≥ `PLACEMENT_COMPARISONS` appearances; test `cj status` in placement mode.

**C-5 (Medium) — No cross-repository trigger on the CJ side.** The interface scanner (D15) lives in the harness and runs only in the harness's CI, so a CJ spec edit that breaks the interface stays green until the harness next builds. Options: CJ's workflow checks the harness out with a read token and runs `tools/check_spec_interface.py`; or CJ dispatches the harness workflow on push. D15's Rule line already names this as "judgment, not checkable until it is wired into a hook".

**C-6 (Low) — Acceptance-criteria checkboxes are inconsistent and unmechanized.** 13 `[x]` versus 54 `[ ]`; several unticked P1 criteria are implemented and tested (byte-identical refit, insertion-order invariance, the 5-second fit). The 0.6.0 changelog says "the criteria above now carry checkboxes tied to named tests" — only the eight new ones do. Adopt a verifier with spec anchors (the harness's `verify_phase1.py` shape) or remove the ticks.

**C-7 (Low) — Wording and spelling.** `README.md:30` "Three commands refuse" introduces four invocations of two commands. The whole repository is British-spelled ("Licence", "regularised", "initialises") while the harness converted to US at `745d1a6`; the repository is internally consistent, so this is a cross-repo choice to make deliberately, not a defect.

**C-8 (Low) — Floors in the declaration.** `pyproject.toml` declares `numpy>=2.0`, `pyyaml>=6.0`, `textual>=0.80`; only `uv.lock` pins. The harness's W35 posture (and its test `test_no_dependency_is_expressed_only_as_a_floor`) requires `==` in the declaration too; CJ's test checks the lockfile only. Decide whether CJ adopts the stricter form.

**C-9 (Low) — The decision record's header restates the high-water mark** (`decisions.md:6` "D1–D26 recorded"); the harness retired that pattern at D58 as unmaintainable. Correct today.

**C-10 (Info)** — Coverage is measured (98 %) but not enforced; an optional `--cov-fail-under`. Tests reach freely into `session._store` and `session._fit()`; the seam scan covers `src/` only, which is fine, but the convention is unstated.

---

## 5. Test-suite evaluation

**Strengths, worth keeping.** Every guard added since D46 was planted against and observed to fire; negative controls exist for the check that would otherwise pass on an empty set (`checked`/`compared` floors, per-document minimums, both halves of a partition); the cross-document count guards (`test_document_counts.py`) are the right shape for a project whose recurring defect is a stale number; CJ's refusal tests are one-per-audit-finding and read as a changelog.

**Weaknesses found, in priority order.**
1. A vacuous branch in the evidence checker (H-4) — the one class the suite claims to have closed.
2. The real severity file is unread (H-3) and the phase-1 severity, key-set and id-uniqueness criteria are verified against the drafts (H-11).
3. Held-out size and CI-shape statements have no guard (H-2); the design-set guard's success hides that its neighbor is missing.
4. Four conventions the held-out CI does not run (O-2), and a copied helper with no equality test.
5. CJ: `Progress.complete` in placement mode is tested only through the TUI message (C-4); the configured mypy scope fails (C-2).
6. Missing input-edge cases: BOM-prefixed transcript (H-14); scored question-tier finding and unknown band label in `severity.join` (H-3); packet builder leak-scan deletion path (O-6).

**No vacuous or tautological test was found** in either suite by reading; D71's runtime count of loop-only tests still holds for the harness. The CJ suite's `test_the_same_pair_renders_through_two_different_formatters` is the one test whose *earlier* tautology the file itself documents and has since fixed.

---

## 6. Mechanisms, hooks and triggers

| Mechanism | Status |
|---|---|
| Global pre-commit (secret + private guards, fail-closed) and pre-push owner check | present and verified on disk; `test_hooks.py` and `test_the_documented_hook_installation_actually_works` prove both refusals |
| Harness CI: type, lint, format, extract, tests, held-out absence, view freshness, interface scan (fails without sibling) | present; `CJ_READ_TOKEN` in place per D84 |
| Held-out CI: set membership, no-labels, parse, ported checks, fails without harness | present; `HARNESS_READ_TOKEN` per D84 |
| CJ CI: tests, mypy (src only), lint, format on 3.12/3.13 | present; scope narrower than declared (C-2) |
| Spec sweep trigger (8–10 decisions) | **prose only; fired at D79, unhonored** (H-1) |
| Held-out set size in prose | **no guard** (H-2) |
| `HELDOUT_SET` ↔ held-out `transcripts/` | **no check on either side** (O-4) |
| Held-out repo: labels file shape | root-only glob (O-3) |
| Held-out repo: lint/type | **none** (O-5) |
| Interface drift triggered from the CJ side | **none** (C-5) |
| `entities.md` "Design set:" ↔ `DESIGN_SET`; escalation outcome convention in the register | **none / not done** (H-7) |
| Gold set ↔ drafts+ledger, view ↔ gold, artifact hash, statement inventory | present, in tests and CI |
| Severity file ↔ store (log hash, run id, revisions) | reproduced by hand (§1); **no test** (H-3) |

---

## 7. Already recorded by the project — not re-reported as new

A second human reader of corpus and gold set; D79's F-75 rank tension; D82's `cj verify` owed in CJ; D85's design-set door-time drift (H-6 confirms it is still there); D86's register convention (H-7); the phase-5 reach statement; the transfer failure paths (a)/(b)/(c) with the stated floor; `anchor_set_version` unsettable from the CLI; the CJ TUI never run by a human; λ, `MAX_ITER`, `PLACEMENT_COMPARISONS` and the appearance target as unvalidated constants; the remaining O(n) session cost; the BOM commit subject; `Outcome.transferred` as a schema smell (H-16 asks for a decision, not a rediscovery).

## 8. Checked and found clean (base rate)

Corpus: all 15 design transcripts parse clean; every quoted fragment, cross-call citation, span, final-event figure and gap claim (except H-4's branch) resolves; every POLICY quotation equals its clause; every tool-call argument has a source; the injection pair differs by exactly one appended utterance; the density ceiling holds (max 0.342). Documents: decision numbering D1–D86 is gapless and the status block agrees; every Rule-line test exists; every identifier in prose resolves (`statement_inventory`); the seven severity fields and six shared findings keys agree across both repositories, locally and against GitHub. CJ: fit determinism, regularization, connectivity, refusals, append-only log, derived run id, seam scan — all behave as specified when driven from the CLI. Held-out: parse, provenance, clause counts, event-scoped agreement, register vocabulary, Class 1 entities, speech band — all hold (O-1 excepted).

## 9. Suggested order of work for the working session

1. Push CJ `3766b9e` (C-1). Two minutes.
2. Sweep and bump the harness spec (H-1), taking H-2, H-9, H-10 with it; add the trigger test and the held-out-size guard.
3. Fix the `_GAP_CLAIM` branch and plant the F-15 shape (H-4); add the real-severity-file test and the two `join` refusals (H-3); retarget the three draft-bound tests (H-11).
4. Held-out repository: allowlist for tracked files (O-3), `HELDOUT_SET` step (O-4), `_sourced_by` AST-equality test and the ported persona/register/speech checks (O-1, O-2), lint gate (O-5), rules-only docstrings (H-12).
5. Decide the scenario map's status (H-5) and the register counts (H-8).
6. CJ: mypy scope (C-2), D14 retags (C-3), `Progress.complete` (C-4), CJ-side interface trigger (C-5).
7. In a design-corpus-cleared session: H-6 and H-7.

## 10. Assumptions this report rests on

- **Assumed the owner's clearance to read the held-out transcripts stands for this session only**, and that the safe-report rule is "counts and rules, never content" as `HOLDOUT-SESSION-PROMPT.md` states it; every held-out statement above was written to that rule.
- Assumed the three local checkouts are the working state to audit; the harness and held-out repositories are clean and at `origin/main`, CJ is one commit ahead, none has a dirty tree.
- Assumed "recent work" means the commits listed in §0; everything else was read anyway.
- Assumed the sweep trigger in the spec header ("~8–10 accrued decisions") is meant as a rule, because D71 treated it as one.
- Assumed line numbers are stable as of commit `6535862` (harness), `fb209bf` (held-out) and `3766b9e` (CJ).
- Did not run the CJ TUI interactively, did not exercise GitHub Actions remotely, and did not re-measure D16's iteration counts; those remain as the projects record them.
