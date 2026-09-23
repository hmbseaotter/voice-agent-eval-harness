# Sweep — the specification at 0.59.0 @ D198, read against the tree for phase 5's close

> **STATUS.** Written 2026-09-19 at `63023f9` by a session that took no part in the phase-5 build,
> its audit or the audit's remediation (Claude Fable 5.1). **It reports and edits nothing**: this
> file is the only one the session added, and the specification, the decision record and the
> registers are as it found them. The session that worked the audit remediation applies what it
> accepts from section 2, writes the sweep's changelog entry, moves the `Last swept` marker and
> closes the phase. A later session that acts on a finding records it in this banner, so that the
> banner and not the body is what a reader trusts for status.
>
> **2026-09-20, applied — 26 of 27 applied whole, 1 in part, none declined.** Worked by the
> session that built phase 5's coverage report and its audit's remediation, on the owner's
> decisions. Each finding was reproduced or re-read before it was acted on.
>
> **The close first.** S-1 and S-2 both reproduced: the check that evaluates *at phase completion*
> matched `**Status: closed**` and not `**Status:** closed.`, and this handover named nothing past
> D193. Before the close relied on that check it was made to fire, in a copy of the tree outside the
> repository: closed with the marker unmoved it is red in either form, and green once the marker
> names a swept version. The pattern reads both forms now, with a planted case and a control
> (**D199**), and the handover records D194 to D200 before its status line moved.
>
> **Applied in the specification** (`8fb9932`, version 0.60.0): S-3 status, S-4 provenance, S-5
> visibility, S-6 severity fields and OB-18, S-7 phase 1's prerequisite, S-8 the five deferred
> taxonomy items, S-9 how the corpus reached sixteen calls, S-10 the extraction artifact, S-11 the
> design document moved to phase 6 (**D200**), S-12 no build log was kept, S-26 the byte-identical
> comparison, and S-27's four statements reworded to be true on both sides of the close. S-13 is a
> note appended under D198, since a record is not edited (D53).
>
> **Applied beside it** (same commit): S-14 to S-20 in the `Not checked` block, S-21 OB-46, S-22 and
> S-14's other half in `HOLDOUT-OBLIGATIONS.md`, S-24's enumerations and the two missing table rows
> in the README, with `runs/` and `snapshots/` licensed as the corpus is, on the owner's decision.
>
> **S-25, in part.** Its first half holds and is applied: the workflow's header comment called the
> golden-report regression outstanding beside the step that runs it. Its second half does not. The
> sentence in `specs/taxonomy-coverage.md` was stale and is corrected, but the report says "the map
> has no mention of D133" and row 1 of that map names D133 twice, recording that it took neither
> option and widened judged dimension 4 instead.
>
> **S-23 was left open deliberately**, which is what it asked for: the owner could not say whether
> D83's reach statement was made beside the held-out figures, nothing in the tree records it, so the
> reveal handover gained it as item 7 and the register carries it as **OB-50**.
>
> **Phase 5 is closed**: OB-46 closed on the audit, this sweep and the marker at 0.60.0 @ D200.
>
> **27 findings, none acted on: 9 Wrong, 14 Stale and 3 Unbacked, and one, S-27, listing four
> statements that are true today and turn false in the closing commit.** Two of them, S-1 and
> S-2, are about the close itself and should be read first: as the tree stands, the reveal
> handover can be marked closed with D129's test green and no sweep entry written, by either of
> two independent routes.
>
> **No model call was made, nothing was tagged, and no other repository was edited.** Four reads
> went outside this tree, all read-only and each stated where it is used: the account's
> repository listing for visibility (S-5); `comparative-judgment`'s specification header and tip
> commit (S-18); and, for S-3 and S-4, the installed specification skill's template, and whether
> one commit id resolves in the toolkit's checkout and in the repository rooted at the owner's
> home directory. **The held-out repository was not opened**, by listing, by path or by search.

**Kind of review.** A sweep, not an audit: every section of the specification except the changelog
was read for statements that describe the project *now*, and each was checked against the tree.
The mechanized half was run first and then read past, as the brief asked. Every finding marked
*(reproduced)* carries the command and what it printed; one marked *(by reading)* names the lines
read on both sides.

---

## 1. Baseline, reproduced

At `63023f9`, working tree clean before and after, `main` level with `origin/main`.

| check | result |
| --- | --- |
| `uv run pytest -q tests/test_document_counts.py tests/test_contract_coverage.py tests/test_obligations.py tests/test_phase3_acceptance.py tests/test_findings_evidence.py` | `139 passed in 30.02s` |
| `uv run python tools/statement_inventory.py` | `every identifier named in prose resolves` |
| `uv run python tools/check_holdout_absence.py` | `held-out absence check OK`, naming the 16 declared design-set transcripts, 5 declared test fixtures and no file it could not decode; 6.2 s |
| `uv run pytest -q --junit-xml=<a junit of this session's own under build/>` | `1312 passed in 1169.46s (0:19:29)`, 0 failures, 0 errors, 0 skipped |
| CI on `63023f9` (`gh run list`) | `success`, 2026-09-20T04:28:01Z to 04:37:54Z, which runs all five phase verifiers, the control gate and the interface scanner |
| `uv run python -m tools.verify_phase5 --junit build/phase1-junit.xml` | `All 11 checks pass, each by running it`, `3 more are declared and not ticked: 3 asserted elsewhere, 0 not yet built`, `The suite as a whole passed too`; exit 0 |

**The junit the brief names was stale by the verifier's own rule, so the verifier re-ran the
suite.** `report_is_current` compares the report's mtime with the newest file anywhere in the
tree, and the brief itself (`sessions/PHASE-5-SWEEP-PROMPT.md`, 21:24) is newer than the report
written at 15:54. The verifier deleted `build/phase1-junit.xml`, ran the suite and rewrote it,
which is the mechanism working. It is recorded because the same thing happens to the closing
session the moment this report lands: a `--junit` run that takes fourteen minutes or more reads
as a hang, and it is not one.

---

## 2. Findings

Severity is the brief's: **Wrong** is false today, **Stale** was true when written and describes a
state the project has left, **Unbacked** may be true and nothing in the tree can tell.

### The close itself

**S-1 — Wrong — D129's test cannot see the reveal handover closed in the form it is written in**
*(reproduced)*

- **Says.** `specs/voice-agent-eval-harness.md:12`: *at phase completion* is one of two mechanized
  clauses, "a closed handover for phase N requires this marker to reach the last decision that
  handover records". D194's *Why* (`specs/voice-agent-eval-harness.decisions.md:10339`): "D129's
  test at a phase's close now needs a real sweep entry to go green."
- **True instead.** `_closed_handovers` (`tests/test_document_counts.py:2738`) finds a closed
  handover by `^\*\*Status:?\s*closed`. Phases 3 and 4 write `**Status: closed** 2026-09-12, …`,
  colon inside the bold. The reveal handover, and the cross-project one beside it, write
  `**Status:** open.`, colon then the closing asterisks. Changing `open` to `closed` in place
  gives a line the pattern does not match, so the test compares nothing for phase 5 and stays
  green on the two handovers it already reads.
- **Checked.** The test's pattern against both forms:

  ```
  True <- **Status: closed** 2026-09-12, ...
  False <- **Status:** closed. Closed 2026-09-19 ...
  False <- **Status:** open. Opened 2026-09-18 ...
  ```
- **Proposed.** Close the handover as `**Status: closed** 2026-09-…`, the form the two the test
  reads use. The pattern accepting both forms, with a control that plants the second, is the
  durable fix and is a test change, so it is the owner's and the closing session's to weigh, not
  this report's. Worth acting on either way: this is the one finding that lets the phase close
  unswept with everything green.

**S-2 — Wrong — the reveal handover names nothing past D193, where the marker already stands**
*(reproduced)*

- **Says.** The same two sentences as S-1, and
  `sessions/HANDOVER-2026-09-18-held-out-reveal.md:24` to `:31`, whose "Since then" paragraph ends
  at D193.
- **True instead.** The test takes the highest `D<n>` a closed handover names as the last decision
  it records. The reveal handover's is D193 and the marker reads `0.54.0 @ D193`, a version D194
  leaves as history. So even written in the form S-1 asks for, the handover closes green today
  with no `**Swept:**` entry anywhere. D194 to D198 are phase 5's own remediation and the
  handover records none of them.
- **Checked.** D129's rule evaluated in memory over `sessions/HANDOVER-*.md`:

  ```
  marker: D193
  HANDOVER-2026-09-09-phase-3.md    status=closed   max D=126
  HANDOVER-2026-09-09-phase-4.md    status=closed   max D=156
  HANDOVER-2026-09-18-held-out-reveal.md   max D=193
  reveal handover names up to D193; closed today it is at or behind the marker
  ```
- **Proposed.** Before the status line moves, the handover's status paragraph records the
  independent audit and D194 to D198, which S-21 asks for anyway. The test then goes red until the
  marker names a `**Swept:**` entry at or past D198, which is the order D129 wants.

### The specification

**S-3 — Stale — `Status: DRAFT`** *(by reading)*

- **Says.** `specs/voice-agent-eval-harness.md:5`.
- **True instead.** The template this specification was produced from gives the line four values,
  `DRAFT | READY-FOR-BUILD | IN-BUILD | BUILT`. Five phases are built and verified, the rubric is
  frozen under the `rubric-frozen-v1` tag, and phases 6 and 7 are not built. Nothing reads the
  line: a search of `tests/test_document_counts.py` and `tools/statement_inventory.py` for it
  finds no reader.
- **Proposed.** `Status: IN-BUILD — phases 1 to 5 built and verified; 6 and 7 not`. If `DRAFT` is
  kept on purpose, because the document is still amended per decision, the line should say so as
  `Visibility` does.

**S-4 — Wrong — `Produced by: /specify @ f72b756` names a commit of another repository**
*(reproduced)*

- **Says.** `specs/voice-agent-eval-harness.md:11`. The template defines the line as "which
  generation of the toolkit wrote this spec", taken with `git -C <toolkit-repo> log -1`.
- **True instead.** `f72b756` is not a commit of the toolkit. It resolves in the repository rooted
  at the owner's home directory, where the installed skill's folder sits, as `f72b756 2026-08-27
  18:55:56 -0700 Sync installed cooperation-rules.md with the bundle repo`. In the toolkit's own
  checkout, `git cat-file -t f72b756` prints `fatal: Not a valid object name f72b756`. Run from the
  installed skill's folder, `git -C` climbs to the enclosing repository, which is how the line
  came to name it. It survived because nothing can read it from here: `git cat-file -t f72b756`
  in this tree prints the same `fatal`.
- **Proposed.** `Produced by: /specify, installed copy, toolkit sha unknown (the id first recorded
  here, f72b756, is a commit of the machine's configuration repository dated 2026-08-27, not of
  the toolkit)`. The date is still useful: it bounds which toolkit generation it was.

**S-5 — Wrong — the held-out companion is called public, and all three repositories are private**
*(reproduced; confirmed by the owner in this session)*

- **Says.** `specs/voice-agent-eval-harness.md:106`: "`hmbseaotter/voice-agent-eval-harness-holdout`
  (public, held-out set …)", beside "(private → public)" for this repository.
- **True instead.** `gh repo list hmbseaotter --json name,visibility` printed `PRIVATE` for all
  three, which the owner confirmed: private now, public when the three are done. Line 14 of the
  same document is careful about exactly this, "**Not yet flipped**, and the line says so rather
  than naming the intended end state as if it were the current one"; line 106 names the end state.
  `README.md:172` and the `Not checked` block both say all three are private.
- **Proposed.** "(private → public, held-out set …)", and the same arrow on
  `comparative-judgment`. Lines 18, 43 and 107 and `README.md:154` say the labels' plaintext is
  "published"; with line 106 corrected they read correctly as published *to the companion
  repository*, and need no change unless the owner wants the word qualified.

**S-6 — Stale — `prior decisions` says the severity rows carry three fields and OB-18 is due**
*(reproduced)*

- **Says.** `specs/voice-agent-eval-harness.md:120`: carrying the content hash "is D82's own
  rejected option, reopened as OB-18 and due with the next export", and "`severities` holds `id`,
  `severity` and `theta` with nothing to separate the two".
- **True instead.** The committed `corpus/findings.severity.json` is at schema 3 and every row
  carries `appearances`, `content_hash`, `id`, `informative`, `severity` and `theta`. OB-18 is
  `closed` in `OBLIGATIONS.md` on D148's evidence. Line 29 of the same document already says all
  of this, so the specification disagrees with itself across ninety lines.
- **Proposed.** End each of the two sentences with what closed it: "…reopened as OB-18 and closed
  at D148, when the row gained `content_hash` at schema 2", and "…three comparisons where its
  neighbors carry ten; `severities` held `id`, `severity` and `theta` alone until schema 2 added
  `appearances` and `informative`".

**S-7 — Stale — assumption 1's discharge says no scoring has happened** *(reproduced)*

- **Says.** `specs/voice-agent-eval-harness.md:359`: the prerequisite's second half, that the tool
  has scored the design-set findings, "is not, and cannot be until the corpus exists", closing on
  "any scoring, which has not happened"; and the tool is "at spec 0.6.0 / D26".
- **True instead.** The severity file scores all 83 defect-tier findings with an empty `unplaced`
  (`schema 3 rows 83 unplaced [] cuts 3`), the corpus has existed since phase 1, and the tool's
  specification header reads `Spec version: 0.12.0`. This is the class the 0.21.0 sweep found, a
  discharge stale in the direction that understates what is done.
- **Proposed.** "Both halves of phase 1's prerequisite are satisfied: the tool exists, and it
  scored the design-set findings on 2026-09-05 (D82), re-exported since. Still deliberately not
  claimed: that repository's current defect state." Drop the pinned version, on D74's rule; S-18
  is the same pin in another place.

**S-8 — Wrong — five items are said to be deferred for being cross-corpus, and three are**
*(by reading)*

- **Says.** `specs/voice-agent-eval-harness.md:361`: "five items stay deferred because they are
  *cross-corpus* properties that no single call can carry".
- **True instead.** `specs/taxonomy-coverage.md:167` lists the five as 12, 16, 25, 29 and 35. Rows
  12, 16 and 25 are cross-corpus, as `out of scope` (line 54) and the `Not checked` block say. Row
  29 is deferred as "architectural rather than model behavior, and there is no live system under
  test", and row 35 because "audio-layer testing is out of scope".
- **Proposed.** "…but five items stay deferred: three because they are cross-corpus properties no
  single call can carry (12, 16, 25), one because it is architectural with no live system to
  observe (29), and one because it lives in the audio layer (35). None is a property of
  ticketing."

**S-9 — Stale — sixteen design calls are explained as twelve plus two, and the held-out set is
said not to have grown** *(reproduced)*

- **Says.** `specs/voice-agent-eval-harness.md:109`: "12 design at D4, and D68 added two…. The
  held-out set did not grow with it, which is recorded as O-3 in `HOLDOUT-OBLIGATIONS.md` rather
  than resolved."
- **True instead.** Twelve and two is fourteen. D4's own superseding note
  (`specs/voice-agent-eval-harness.decisions.md:87`) gives the path as "D68, then D73, then D119",
  which is CALL-20 and CALL-22. `HELDOUT_SET` declares 6 calls, the sixth seeded at D86 on O-3's
  decision, and O-3 has carried `☑` since 2026-09-06. The count is held by a guard; the sentence
  explaining it is not.
- **Proposed.** "12 design at D4; D68 added two when an error-type sweep found classes the twelve
  could not carry, D73 a third for escalation and D119 a fourth. The held-out set grew by one,
  the escalation call O-3's decision asked for (D83, D86); what O-3 still owes is the reach
  statement (S-23)."

**S-10 — Wrong — the extraction artifact is said to be rebuilt only on a corpus version change**
*(by reading)*

- **Says.** `specs/voice-agent-eval-harness.md:77`: "the frozen extraction artifact (rebuilt only
  on a corpus version change)".
- **True instead.** `load_corpus` (`src/harness/cli.py:250` to `:275`) parses the corpus and hashes
  the payload on every run, and its docstring says why: the hash "is computed from the same calls
  the run evaluates rather than read from a file written earlier". `harness.extract` rewrites
  `build/extraction-artifact.json` on every invocation, CI invokes it on every build, and the
  file is ignored by `.gitignore:22`. Nothing reads the written file back, and nothing consults
  the corpus version to decide whether to rebuild.
- **Proposed.** "…the frozen extraction artifact (written by `harness.extract` under the ignored
  `build/`, and re-derived by every run rather than read back, so a result's artifact hash is
  true by construction)".

**S-11 — Wrong — the design document is described in the present tense and does not exist**
*(reproduced)*

- **Says.** `specs/voice-agent-eval-harness.md:67`: "The design document specifies three
  deployment cadences and a four-stage gate ladder". Lines 30 and 321 list it as written during
  phase 1, from the decision records; lines 56 and 58 assign it content.
- **True instead.** `git ls-files | grep -i design` prints `corpus/DESIGN_SET` alone, `private/`
  holds two files and neither is it, and `git grep -i "gate ladder\|deployment cadence"` outside
  the specification prints nothing. Phase 1 is closed under three tags with no criterion asking
  for the document, so nothing noticed.
- **Proposed.** The owner's fork, since it moves a deliverable: say which phase owns the design
  document (phase 6's docs routing is where the README's two-audience half already went), move
  the `[P1]` scope bullet's second half and phase 1's chosen-optional clause there, and put lines
  56, 58 and 67 in the future tense: "The design document will specify…".

**S-12 — Unbacked — the build log is said to live under `private/`, which holds none**
*(reproduced on this machine)*

- **Says.** `specs/voice-agent-eval-harness.md:118` and `:377`: "Build log lives under `private/`
  until publication is decided" (D10's option (B), D11).
- **True instead.** `ls private/` prints `clean-room-sources.md` and `substitution-classes.md`,
  both dated 2026-08-29. The directory is ignored, so another machine or the external backup the
  line mentions could hold one; this checkout does not.
- **Would settle it.** The owner saying where the build log is, or that D10's (B) was not carried
  out, in which case the two lines and D10 need a note. Worth asking before the flip to public,
  since the history scan D2 plans is partly a search for this file.

### The five versions written on 2026-09-19

Each `Rule` line, requirement and criterion D194 to D198 added was read against the code and the
tests; section 3 lists what held. One thing did not.

**S-13 — Wrong — P5-11 is said to have found the third kind a week after D193; it was a day**
*(reproduced)*

- **Says.** The 0.59.0 changelog entry (`specs/voice-agent-eval-harness.md:393`): "found it a week
  later". D198's *Fork* (`specs/voice-agent-eval-harness.decisions.md:10481`): "found the third
  kind one week later".
- **True instead.** D193 was decided on 2026-09-18 (decision record line 10292) and committed as
  `c5ad3ce` at 2026-09-19 00:47. The phase-5 audit's banner says it was written 2026-09-19
  against `c5ad3ce`. The interval is a day, and no reading makes it a week.
- **Proposed.** "a day later" in both. Both are records written today, and the project corrects a
  record's error of fact in the open, as `7540163` did for D192; an entry that says so beside the
  change keeps D53's rule.

### The `Not checked` block

Its refresh sentences for 0.55.0 to 0.59.0 each say no entry moved, and for the subjects they
name that is right. Read against today instead, as the brief asked, seven entries need a change:
six describe a state the project has left, which is the rule the block states for itself, and
one points at the wrong item.

**S-14 — Stale — whether held-out labels have been written "is not recorded here"** *(by reading)*

- **Says.** `specs/voice-agent-eval-harness.decisions.md:10531`: "the tag now exists, and whether
  they have been written since is not recorded here". `HOLDOUT-OBLIGATIONS.md:22` to `:25` says
  the same of that file, under **What is not at risk, and until when**.
- **True instead.** Both documents record it. D177 records the label chain; O-9 carries `☑` with
  C3's commit id; `HOLDOUT-OBLIGATIONS.md:608` says "The held-out labels were published on
  2026-09-18". In the register the stale sentence guards a live risk: revising a held-out
  transcript "costs neither property (a) nor property (b) only while no held-out label exists",
  and that *until when* had arrived by 2026-09-17, when C1 sealed the manifest.
- **Proposed.** Block: "…the tag now exists, and the labels were sealed on 2026-09-17 and
  published on 2026-09-18 (D177, O-9)." Register: "…that tag now exists, and the labels were
  sealed at C1 on 2026-09-17 and published on 2026-09-18 (O-9), so the condition no longer holds:
  a revision to a held-out transcript now has to be weighed against both properties." What such a
  revision would cost is the owner's to word; the report's point is that the sentence still
  reads as though the question were open.

**S-15 — Stale — generalization is still "unknown", waiting on "the held-out set at P5"**
*(by reading)*

- **Says.** `specs/voice-agent-eval-harness.decisions.md:10579` to `:10582`: "What is still unknown
  is whether it generalizes… the only measurement that can say otherwise is the held-out set at
  P5."
- **True instead.** That measurement ran on 2026-09-18 and its figures went to the owner and were
  never committed (D175, the reveal handover). This is P5-8's class, one entry over from the
  caveat P5-8 corrected.
- **Proposed.** "Whether it generalizes was measured on 2026-09-18, on the held-out set; the
  figures went to the owner and are not in this tree (D175), and OB-7 carries what closing
  `JUDGED_AGREEMENT_PENDING` now needs."

**S-16 — Wrong — "The first has since been measured" points at the wrong item** *(by reading)*

- **Says.** `specs/voice-agent-eval-harness.decisions.md:10546` lists three things the
  deterministic tier's coverage does not say: that judge and human findings are reachable, that
  the entries generalize to the held-out set, and that a phrase list is the right abstraction.
  Then: "**The first has since been measured, and they do not**".
- **True instead.** What D191 measured is the second. The first is settled by classification and
  the sentence before it says so.
- **Proposed.** "**The second has since been measured, and they do not**".

**S-17 — Stale — twenty entries with no negative instance are "more than half"** *(reproduced)*

- **Says.** `specs/voice-agent-eval-harness.decisions.md:10547`: "Twenty of the rubric's
  entries…. That is more than half".
- **True instead.** The denominator was removed on 2026-09-09 as decoration, and the next sentence
  still depends on it. `rubric.yaml` holds 44 entries, 37 `assert` and 7 `judge`; 20 declare
  `none`, all of them `assert`. That is 45% of the rubric and 54% of the deterministic tier.
- **Proposed.** "Twenty of the deterministic tier's entries…. That is more than half of that
  tier", which stays true however many judged entries are added.

**S-18 — Stale — `comparative-judgment` is pinned at 0.10.1/D36** *(reproduced, read-only)*

- **Says.** `specs/voice-agent-eval-harness.decisions.md:10527`, and the 0.51.0 refresh sentence
  that pinned it.
- **True instead.** That repository's specification header reads `Spec version: 0.12.0`, and its
  tip, level with its `origin/main`, is `3521160 2026-09-19 00:03 Record phase 2 at 0.12.0:
  D37-D45`. The pin went stale within a day of being refreshed.
- **Proposed.** De-quantify on D74's rule, since nothing here can hold it: "built, swept, audited
  and pushed; its version is its own specification's to state".

**S-19 — Stale — "The audit" names five documents, and the tree holds seven** *(reproduced)*

- **Says.** `specs/voice-agent-eval-harness.decisions.md:10602`: five documents kept two ways, the
  four tracked ones listed by path.
- **True instead.** `ls sessions/AUDIT-*` prints six: the four listed,
  `AUDIT-2026-09-15-cross-project.md` and `AUDIT-2026-09-19-phase-5.md`. With the report held
  outside the repository that is seven, and this report makes an eighth document of the same
  standing that is not an audit.
- **Proposed.** De-quantify: "'The audit' names one report held outside this repository and every
  `sessions/AUDIT-*.md`, each tracked with a maintained status banner", keeping the sentence on
  the phase-2 report's three corrections.

**S-20 — Stale — twelve gaps and eleven unaddressed weaknesses "are now recorded rather than
resolved"** *(by reading)*

- **Says.** `specs/voice-agent-eval-harness.decisions.md:10517`: they "are corpus and check
  decisions for phase 1", and a phase-1 corpus closing none should say so.
- **True instead.** Phase 1 closed them. `specs/taxonomy-coverage.md:171` says "All twelve gaps
  are now seeded", its tally holds 0 under **GAP**, and Part 3 no longer has an *unaddressed*
  disposition: its 35 rows are 17 addressed, 9 retired by the deterministic tier, 4 deferred, 4
  partial and 1 not reached. The block's own opening paragraph cites "eleven unaddressed
  weaknesses against ten" as a figure that went stale, in the block that still states it.
- **Proposed.** "What replaced it was twelve taxonomy gaps and a list of unaddressed weaknesses,
  recorded for phase 1 to decide. Phase 1 seeded all twelve and phase 2 retired the
  deterministic weaknesses; `specs/taxonomy-coverage.md` carries each item's disposition now."

### Beside the specification

**S-21 — Stale — OB-46 and the reveal handover say no independent audit of phase 5 has run**
*(reproduced)*

- **Says.** `OBLIGATIONS.md:111`: "no independent audit of it has run".
  `sessions/HANDOVER-2026-09-18-held-out-reveal.md:59` to `:63`: "What has not happened is… an
  independent audit… Owed: the audit, its findings dispositioned, then the close."
- **True instead.** `sessions/AUDIT-2026-09-19-phase-5.md` exists, and its banner records all 16
  findings closed on the owner's decisions. What is left of item 3 is this sweep applied and the
  close.
- **Proposed.** The handover's status paragraph gains the audit, D194 to D198 and this sweep,
  which also answers S-2. OB-46 stays `open` until the close, saying what is left: "…the phase is
  not closed: its independent audit ran on 2026-09-19 and is remediated (D194 to D198); the sweep
  of the specification and the handover's close remain".

**S-22 — Stale — the design-to-held-out ratio is "now fifteen-to-six"** *(reproduced)*

- **Says.** `HOLDOUT-OBLIGATIONS.md:209` to `:210`.
- **True instead.** `corpus/DESIGN_SET` declares 16 and `HELDOUT_SET` 6; CALL-22 joined at D119.
  The count guards read the design-set size where it is tagged, and this sentence carries no tag.
- **Proposed.** "the ratio is now sixteen-to-six", or the ratio dropped in favor of the two
  declarations, as D74 would have it.

**S-23 — Unbacked — the reach statement is "still owed, in the published result at phase 5", and
nothing records it made or carried forward** *(reproduced, by search)*

- **Says.** `HOLDOUT-OBLIGATIONS.md:208`: D83 decided that the published result states which
  classes the held-out measurement does not reach, and O-3's discharge leaves that owed "in the
  published result at phase 5".
- **True instead.** Phase 5's result was computed on 2026-09-18 and went to the owner. A search
  for the statement across the decision record from D175 on, the phase-5 audit, the reveal
  handover, `OBLIGATIONS.md` and the agreement and coverage modules finds it nowhere after D86's
  entry. It has no `OB-` row, because it was written into a register and not under a handover's
  *What is owed*, which is the gap OB-15 names. The phase is about to close over it.
- **Would settle it.** The owner saying whether the reach was stated beside the figures. If not,
  an item in the reveal handover before it closes, which the harvest turns into a row: the five
  classes O-3 lists as absent, stated wherever the held-out result is eventually published.

**S-24 — Stale — two README enumerations stop at phase 3** *(reproduced)*

- **Says.** `README.md:22` enumerates the package through the judged tier and "the `harness`
  command". `README.md:279` to `:281` enumerates `sessions/` as "the audit reports, the handovers,
  and the two briefs that governed the held-out repository".
- **True instead.** `ls src/harness` shows `report.py`, `agreement.py`, `coverage.py` and
  `heldout.py`, and `core/severity.py`, none of which the row names, while the same README
  documents `harness agreement` and `harness coverage` forty lines later. `sessions/` holds seven
  `PHASE-*` session and audit briefs, and now a sweep report. The **What is here** table also
  omits `runs/` and `snapshots/`, which hold the reference log and the snapshot its own replay
  and report commands read, and so states no license for either.
- **Proposed.** Add "the two-audience report, judge-versus-label agreement, coverage by severity,
  and the held-out declaration every command that writes reads" to the package row; "the session
  and audit briefs" to the `sessions/` sentence; and a row each for `runs/` and `snapshots/`,
  whose license is the owner's to state.

**S-25 — Stale — outside the listed documents, found by following a pointer** *(by reading)*

Neither document below was swept; each is one sentence met on the way to something else.

- `.github/workflows/checks.yml:13` to `:14`: "What is still outstanding is the golden-report
  regression, which needs the report (P4)". Line 162 of the same file is that regression's step.
- `specs/taxonomy-coverage.md:179`: "**Two** imply a judged dimension the specification still does
  not have (1 and 28)". The specification's line 86 says D133 "also closes taxonomy item 1", and
  the map has no mention of D133.

**S-26 — Unbacked — "byte-identical" holds for `--out` and not for a redirect on Windows**
*(reproduced)*

- **Says.** `specs/voice-agent-eval-harness.md:16` and `:21`: the full report is byte-identical in
  replay mode, measurable by `uv run harness report` on a fresh clone.
- **True instead.** With neither credential variable set, `uv run harness report` exits 0, and
  `--out` writes a file `cmp` finds identical to `snapshots/report.md`. The same command
  redirected with `>` on this machine differs from the snapshot at "char 20, line 1": stdout is
  written in text mode, so every line ends `\r\n`. Two runs through one channel agree, which is
  what the requirement asks; a reader who redirects and compares with the snapshot sees a diff
  and nothing tells them why.
- **Would settle it.** Either a sentence beside the claim that the comparison is made with
  `--out`, as CI makes it, or the renderer writing `\n` to stdout as the file writer does. Small,
  and not worth holding the close for.

### True today, false in the closing commit

**S-27 — four statements the close must move in the same commit** *(by reading)*

Not findings against today. Each describes phase 5 as open, nothing reads any of them, and each
becomes a P5-8 the moment the handover's status line changes.

- `specs/voice-agent-eval-harness.md:388`: "and phase 5, still open, has `tools.verify_phase5`".
- `README.md:129`: "The phase-5 verifier runs while its phase is open."
- `tools/verify_phase5.py:9`: "**Written while its phase is open** (D176)". True forever as
  history; the docstring's present tense around it is what to check.
- `OBLIGATIONS.md`, OB-46 and OB-47: OB-47's trigger is "phase 5 closed, with the held-out reveal
  handover marked closed; read by a person", so the close is the moment a person has to read it.

---

## 3. What was checked and held

Recorded so the next sweep does not re-derive it, and so a null here is not mistaken for an
unread line.

- **D194.** `_SWEEP_ENTRIES_FROM` is `(0, 55, 0)`, the tag is `**Swept:**`, the planted cases
  refuse a decision's entry and admit a marked one, and a marker before 0.55.0 is left alone. The
  accrued count stands at 5, D193 to D198, under the header's trigger.
- **D195.** The reference log holds 222 blob records, of which 208 are `prompt` blobs and none
  names a call, as its caveat says. The check took 6.2 s here against its "about 6 seconds". Its
  nine named tests resolve.
- **D196.** `tests/test_held_out_writes.py` holds six tests. `harness.heldout` is imported by
  `harness.cli`, `harness.agreement`, `harness.extract` and `harness.findings_view`. Both commands
  refuse as requirement line 157 says, on `--out` inside the checkout over held-out content and
  when `HELDOUT_SET` cannot be read, and `--check` is not refused. The phase-5 contract is 5
  requirements and 14 criteria.
- **D197.** The refusal sits in the replay both scoring commands share (`src/harness/cli.py:1705`
  to `:1712`), for a held-out set alone, with no override. `README.md:100` says the same.
- **D198.** The decision's subject is a test and a register paragraph; the test resolves.
- **`control-mutations.yaml`** holds 324 entries, and those citing D194 to D198 number 2, 16, 7, 1
  and 2, as the five `Rule` lines say.
- **The phase-5 verifier** declares three criteria and ticks eleven, as line 388 and the README
  say. `harness agreement` takes five required held-out inputs and `harness coverage` six, with
  `--held-out-policies` defaulted in both, as criteria 221 and 224 say.
- **Counts the tests do not hold, and which agree.** 44 rubric entries, six judged dimensions on
  `claude-sonnet-5` and the synthesis on `claude-opus-5`; 90 findings, 83 `defect` and 7
  `question`; 61 `assert`, 23 `judge`, 6 `human`; three cuts; `specs/event-model.md` sections 4
  and 5 are what line 46 says they are; `pyproject.toml` pins the three runtime dependencies and
  `types-PyYAML` with `==` and asks for Python 3.12; the four exit codes at line 203 are the ones
  `harness run --help` prints; the two held-out briefs are marked spent at their tops; CI runs
  take 9 to 11 minutes against the README's "about ten".
- **`subject_index.py`** is still absent from the installed toolkit, as the `Not checked` block
  says, so the subject-index check stays unavailable here and is recorded as such, as that entry
  asks. It would have had nothing to read: this specification carries no subject index.

---

## 4. What was read, and what was not

**Read in full:** every section of `specs/voice-agent-eval-harness.md` from `metadata` to `emitted
artifacts`, lines 1 to 388; the changelog's entries for 0.54.0 to 0.59.0; D194 to D198 and the
`Not checked` block in the decision record; `README.md`;
`sessions/HANDOVER-2026-09-18-held-out-reveal.md`; `src/harness/heldout.py`; the sweep-marker and
closed-handover tests in `tests/test_document_counts.py`.

**Read in part:** `OBLIGATIONS.md`, its prose in full and its table by status and by the rows the
specification and the reveal handover point at, not every row; `HOLDOUT-OBLIGATIONS.md`, lines 1
to 213 and 485 to 650 in full, O-4 to O-8 by heading and discharge mark alone;
`.github/workflows/checks.yml`, its steps and its header comment; `tools/verify_phase5.py`, its
docstring and declarations, not each criterion's caveat; `specs/taxonomy-coverage.md`, its tallies
and the rows this report cites; the `Document status` paragraph of the decision record, met once
and not checked.

**Not read:** the changelog below 0.54.0, as historical; D1 to D193, except where a finding cites
a line; `CONTROL-REGISTER.md`; `specs/event-model.md` beyond its headings,
`specs/transcript-format.md`, `specs/taxonomy-scenario-map.md` and `specs/error-type-sweep.md`;
every other handover, audit and brief in `sessions/`; the corpus itself. No verifier's criterion
was re-derived and no mutation was run: that is the audit's work, done on 2026-09-19.

**Not checked, and said so:** the API facts at lines 91 and 92 of the specification, that both
models refuse sampling parameters with a 400 and carry a 1M context, which nothing in a tree can
settle and which the `Not checked` block says were verified against documentation once; the
assumptions at lines 362 to 369 still marked open, which are judgments and not states; and every
statement about what the held-out repository's gate asserts, which this session was told not to
open that repository to check and which this tree records throughout as reported.

---

## 5. What the sweep's changelog entry should say it read

> **Swept:** every section from `metadata` to `emitted artifacts` read against the tree at
> `63023f9` by a session that built none of it, with the `Not checked` block, the README, both
> obligation registers and the reveal handover beside it, and the changelog from 0.55.0 for
> whether each entry describes what landed; the report is
> `sessions/SWEEP-2026-09-19-phase-5.md`, whose section 4 says what was not read. It found 27
> statements to correct, 2 of them in how phase 5's close is tested, and this version applies
> those the owner accepted.
