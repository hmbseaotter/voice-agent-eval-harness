> **SUPERSEDED.** Phase 1 is closed. This file is kept as the record of what phase 1 was asked
> to build, not as instructions to follow: its counts are frozen at the moment it was written and
> several are now wrong. **The live documents are `specs/voice-agent-eval-harness.md` and
> `specs/voice-agent-eval-harness.decisions.md`**, and the decision numbering continues from
> *Document status* at the end of the latter, not from any number quoted here.

# Build prompt — voice-agent evaluation harness, **phase 1**

> Hand this file to a building agent (a fresh Claude Code session, Cursor, Aider, …). It targets
> **phase 1 only**. The full target is `specs/voice-agent-eval-harness.md`; the reasoning behind
> every settled fork is in `specs/voice-agent-eval-harness.decisions.md` (D1–D22).

## Recommended build-time session settings
- **Model:** Claude Opus 5. **Effort:** `xhigh` (Extra), not `max`.
- **Multi-agent orchestration: OFF for this phase.** Parallel transcript authoring would fragment
  the corpus — independent agents produce inconsistent voice, tool-naming conventions and defect
  calibration, and corpus coherence is a single-author property that review cannot repair
  afterwards. Phases 5 and 6 are where orchestration earns its keep.

## Read first, in this order
1. `specs/voice-agent-eval-harness.md` — the whole target.
2. `specs/voice-agent-eval-harness.decisions.md` — D1–D30, especially the "Not checked" section.
3. `specs/taxonomy-coverage.md` — the 35-item failure-mode taxonomy you will seed from and the
   W1–W35 known-weakness list, each item carrying a disposition. **Written to be self-contained**:
   every item is stated in enough detail to author a scenario against without opening anything else.
   Twelve taxonomy gaps and ten unaddressed known weaknesses are recorded there rather than
   resolved, deliberately (D30) — they are corpus-authoring decisions, and this phase is where the
   corpus is authored. Treat them as work, not as background.
4. `private/clean-room-sources.md` — the read-prohibited paths, and the substitution boundary. Read
   this **before** touching corpus content.
5. `private/substitution-classes.md` — the seven substitution classes, and the scenario-shape smells
   a string scan cannot catch.
6. The **handover reference document** (~3,180 lines), whose location is given in
   `private/clean-room-sources.md`. **Optional, and no longer the primary route.** Item 3 extracts
   what this phase needs from it; read the original only when the map points at something you need
   more detail on, or when you want the architecture and methodology chapters the map does not
   cover. It is safe to read in full — the two withheld paths are not.

## Work in this order
1. Restate the outcome in one sentence.
2. Review the spec's **assumptions** block. Flag any assumption that looks wrong or risky and
   confirm it with the human BEFORE building — the highest-leverage step in this list.
3. List any remaining ambiguities or missing information.
4. **PLAN GATE — enter plan mode, present an implementation plan for phase 1, and get human
   approval BEFORE writing anything.**
5. Build **only** phase 1. Treat every higher-phase item as documented-but-not-yet: do not build
   it, and do not make architectural choices that block it.
6. Verify each phase-1 acceptance criterion **by running it**. Do not mark the phase complete until
   all pass.

---

## HARD CONSTRAINTS — read before anything else

**Confidentiality boundary (non-negotiable).**
- **Do NOT read any path listed as read-prohibited in `private/clean-room-sources.md`.**
  Both sit outside the clean-room boundary (D6, and the handover's implement-first rule). The reference
  implementation is a *post-hoc completeness check* run after your build, never a template consulted
  before or during it. Reading either destroys a property the project depends on: the new corpus's
  independence is currently **structural**, not a claim about restraint, and that cannot be restored
  once lost.
- Reuse **nothing** from prior material outside the clean-room boundary — no transcript text, findings, entity names, figures,
  policy terms, tool names or status vocabulary. Apply the handover's substitution-by-class policy to
  all seven classes.

**Ground truth is human, not model-authored (D10).** You may draft transcripts and policy documents —
those are the artifact under test. The **findings rows, the `detectable by` classification and the
severity ordering must be the human's judgment.** If the gold set is model-generated, "judge-versus-
human agreement" measures a model against itself and the project's headline result is void. Draft
candidate observations for review if asked; never assign a final label unprompted.

**Never do unattended.** Commit a populated `.env`; commit anything under `private/`; make a live
model call (phase 1 has none); publish anything derived from material outside the clean-room boundary.

---

## Prerequisite outside this spec
The **comparative-judgment severity tool** (`hmbseaotter/comparative-judgment`, D12/D20) must exist and have scored the
design-set findings before the severity backfill item can complete. Everything else in phase 1 can
proceed in parallel with it (D13).

---

## Phase 1 scope — required floor

1. **Transcript format specification.** Event grammar; a **closed** tool-status vocabulary; line
   numbering; citation identifiers tagged `[T<n>]` for transcript lines and `[F<n>]` for established
   facts (two distinguishable populations — this is the structural fix for the reference's W1, where
   one shared syntax made the validator reject the very facts the prompt called ground truth); and
   the multi-line turn-wrapping rule. Realistic wrapped text is adapter 1 (D5).
2. **Repo hygiene floor, in the FIRST commit.** `.gitignore` covering at minimum `.env`, `private/`,
   `__pycache__/`, `*.pyc`; `LICENSE` (Apache-2.0) and `LICENSE-CC-BY` (CC BY 4.0); the `.env` guard
   and the `private/` guard. These go first because the repo is built private and flipped public
   later, and **the flip publishes history retroactively** — a guard added in week three does not
   protect week one.
   - Both guards must **fail closed** and live in the **global** hook: `core.hooksPath` is set
     machine-wide, so a repo-local `.git/hooks/pre-commit` never fires (D14).
3. **Taxonomy → ticketing scenario map.** Map all 35 taxonomy items to concrete event-ticketing
   scenarios *before* authoring. Any item with no natural instance is recorded as a stated coverage
   gap, never forced. This is the recorded mitigation for the spec's assumption 3.
4. **12 design transcripts + reference policy documents.** Domain: **event ticketing** (D18).
   Policy documents (return and refund at minimum) are versioned corpus artifacts retrieved in-call
   by a **logged lookup**, so the event log shows what was retrieved — that is what makes both
   "misstated a retrieved clause" and "asserted policy with no retrieval at all" detectable. Seed
   defects across deterministic-detectable and judgment-requiring classes, including **at least one
   prompt-injection attempt in caller speech plus an otherwise-equivalent transcript without it**,
   so the D7 acceptance criterion can compare verdicts.
5. **Findings document, in YAML.** One entry per finding: a stable `id`, the call reference,
   `observation` (self-contained, readable without the transcript open), `evidence` **as a list** so
   fragments from different points in a call stay visibly separate, `consequence`, `detectable_by`
   ∈ {assert, judge, human}, and `tier` ∈ {defect, question}. YAML because evidence holds verbatim
   multi-line quotes a Markdown table cell cannot carry (D22). Generate a Markdown view for reading;
   the YAML is the source of truth.
6. **Severity, joined not backfilled.** The external tool emits a **separate** severity file keyed by
   finding `id`, carrying `schema_version`, `anchor_set_version`, `comparison_log_hash`, `run_id`,
   `calibration`, `severities` and `unplaced`. The harness joins on `id`. Severity is **not** a
   field in the findings document, and the tool never mutates it — a findings document containing a
   severity field must be rejected by name (D22). The field list is asserted against the tool's own
   specification by `tools/check_spec_interface.py`; do not hand-verify it.

## Phase 1 scope — chosen optional items

7. **Extraction tier, pulled forward from phase 2.** Text adapter → ordered, indexed, typed event
   stream with wrapped turns reassembled → versioned frozen artifact. The phase must end with
   something that **executes**. This is also the fastest way to find format-spec defects: a grammar
   only looks complete until a parser reads it.
8. **Decision records accumulated during the work**, with the design document written from them —
   not reconstructed afterwards. Reconstructed rationale gives the reason you would give now rather
   than the reason you had, and the rejected alternatives vanish silently. Append to
   `specs/voice-agent-eval-harness.decisions.md`, continuing from the number that file's
   *Document status* section names — **not** a number written here, which goes stale the moment
   the record grows. It said D23 while D23–D30 already existed, which is the same defect its own
   0.3.0 changelog records catching when it said D19.
9. **5 held-out transcripts authored**, placed **directly into `hmbseaotter/voice-agent-eval-harness-holdout`** and
   never into the main working tree, so no session working on the harness can read them
   incidentally. **Their labels are withheld** until after the `rubric-frozen-v1` tag (phase 5).

**Deferred by choice:** the README skeleton with two-audience docs routing → phase 6. A README
written before the artifact exists describes an intention rather than a thing.

---

## Determinism boundary for this phase
Everything in phase 1 is **plain code — no model calls at runtime**. The extraction tier, both
guards, and all validation are deterministic. Apply the type and value discipline: `mypy --strict`
with no ignores, frozen dataclasses for contract types, `typing.Final` for constants, tuples over
lists for fixed collections.

Stack: Python 3.12+, `uv` with a committed `uv.lock` pinning **exact resolved versions** — not
floors. (W35 in the handover is precisely this defect: floors described as pins, in a project whose
thesis is reproducibility.)

---

## Phase 1 acceptance criteria — verify by RUNNING each

- [ ] The format specification exists, and all 12 design transcripts parse under it with a **zero**
      unparsed-line count.
- [ ] Every findings entry carries `id`, `observation`, `evidence`, `consequence`, `detectable_by`
      and `tier`; the count lacking any of them is zero.
- [ ] The findings document parses as YAML, and an entry whose `evidence` holds three separate
      fragments round-trips with all three still distinct.
- [ ] A findings document containing a severity field is rejected by name.
- [ ] The generated Markdown view regenerates identically from the YAML.
- [ ] A transcript with a turn wrapped across three source lines reassembles into one string,
      asserted **against the source file**, not only against the parser's own output. (The reference's
      W19 was a conformance test that never re-read the source — the one invariant the extraction
      tier exists to protect was the one its test could not see.)
- [ ] A transcript carrying an unknown tool-status token aborts extraction, naming file, line and token.
- [ ] A malformed transcript line produces a non-zero unparsed-line count and **fails the run**,
      rather than being discarded silently.
- [ ] A staged `.env` over 20 bytes is refused by the pre-commit guard — verified by attempting it in
      a scratch repository. An unverified guard is worse than none, because it is relied upon.
- [ ] A staged path under `private/` is refused by the pre-commit guard, verified the same way.
- [ ] Both guards fail **closed**: an indeterminate staged-blob size, or an unresolvable staged path,
      blocks rather than allows.
- [ ] `.gitignore` covers `.env`, `private/`, `__pycache__/` and `*.pyc`, present in the first commit.
- [ ] The pre-commit hook source is present under a documented path, and following the documented
      installation reproduces both refusals in a scratch clone (D29). The guards are machine-level
      controls — `core.hooksPath` is set machine-wide, so a repo-local hook never fires — which
      means a clone of this public repository otherwise gets the ignore rules and no enforcement.
- [ ] `uv.lock` exists and pins exact resolved versions; no dependency is expressed only as a floor.
- [ ] `LICENSE` (Apache-2.0) and `LICENSE-CC-BY` exist. *(The README half of this criterion moved to
      phase 6 — phase 1 defers the README, so the original single criterion could not pass here.)*
- [ ] A repository-wide scan finds no entity name, figure or policy term belonging to any prior
      material outside the clean-room boundary, across all seven substitution classes.
- [ ] The corpus contains no real personal data, asserted against the substitution-class checklist.
- [ ] The 5 held-out transcripts exist in `voice-agent-eval-harness-holdout` and **not** in the main repo's
      working tree, asserted by a path check. *(Now also recorded in the spec's `constraint
      validation` block, and re-run at every later phase. It is the only mechanism protecting the
      held-out set, and this file is superseded at the end of phase 1 — D19's Rule cited it as a
      spec criterion before it was one.)*

---

## Reporting back
- Append any fork you resolve that the spec did not cover to
  `specs/voice-agent-eval-harness.decisions.md`, continuing from the number its *Document status*
  section names — in the same shape (fork, options considered, decision, why, consequences).
  **Do not take the number from this file.** Two versions of this instruction have now named a
  number that was already stale: D19 (caught at 0.3.0, which would have overwritten two settled
  repository names) and D23 (caught during the phase-1 build, by which time D23–D30 existed).
  A build prompt is written once and read after the record has moved on.
- Record architectural calls in the spec's **decisions made** block.
- If the spec itself changes, add a changelog line and bump the spec version.
- Do not add features outside "in scope". Do not add packages outside "constraints" without flagging
  first.

**Regeneration test (the quality bar):** could an agent rebuild phase 1 from the spec alone and
produce behaviorally identical output? If not, you have found what the spec is missing — fix it
*there*, not only in the code.
