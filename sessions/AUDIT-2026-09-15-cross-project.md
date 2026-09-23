> **Received 2026-09-15, written by a session working outside both repositories under
> `phase5-audit`.** The report below is as received, with one class of change this banner names:
> where it named the held-out repository's design document with no prefix, that name carries the
> report's own `holdout:` prefix here, because prose in this tree may only name a path that resolves
> in it (O-11). Citations read
> `repo:path:line@sha`, where `harness:` resolves in this repository and `holdout:` names a path in
> the held-out repository, which nothing here reads. What each finding is owed, and what has been
> answered since, is in `sessions/HANDOVER-2026-09-15-cross-project-audit.md` and the obligations
> register.

# Cross-project audit, harness side — phase 5 seams

**Date:** 2026-09-15
**Scope:** how `hmbseaotter/voice-agent-eval-harness` (the harness) and `hmbseaotter/voice-agent-eval-harness-holdout` (the held-out set) fit together before phase 5 goes further. This is the harness's report. A companion report for the held-out repository was written in the same session. This report stands on its own: every expectation of the held-out side is stated here in words, formats and paths, and a harness session can act on it without opening that repository. It carries no held-out content.

---

## Header

### Clones audited

| repository | ref | commit | note |
|---|---|---|---|
| harness | `main` | `6a0f1443407ee9eb3749e840d7d421ae6f48787f` | full clone; committed 2026-09-15 16:01 -0700, "Keep verifier caveats to what a tick does not buy" |
| held-out | `main` | `5760aa9ca20047c7acde9704deb9b89ed5a687ac` | partial clone (`--no-checkout --filter=blob:none`), sparse checkout excluding `transcripts/`, `NAMES`, `PERSONAS`; committed 2026-09-14 00:01 -0700, "Add seal and reveal for the held-out labels" |
| freeze | tag `rubric-frozen-v1` | `6d3a7101aaa1f15b440de43fe5142434f69c9dc9` | annotated tag `ae987da8…`, "Freeze the rubric at the end of phase 4" |

Citations read `repo:path:line@sha`, with short SHAs `6a0f144` (harness main), `5760aa9` (held-out main) and `6d3a710` (the freeze commit).

### Rules followed

1. Worked only under `phase5-audit`. Opened no local working copy of either repository, no `private/` directory, no review folder, no session transcript, no other project's memory folder.
2. Both repositories are fresh GitHub clones under `phase5-audit/clones`, made with the Bash tool exactly as instructed; the held-out clone took its four sparse patterns on stdin.
3. The exclusion was verified before any file in the held-out clone was read (results below).
4. No git command that needs a file's contents was run on `transcripts/`, `NAMES` or `PERSONAS`. History was read with `git log --name-only`, membership with `git ls-files -t` and `git ls-tree --name-only`; nothing changed the sparse patterns.
5. The held-out test suite was not run. Held-out CI was read through `gh run list` (conclusions) and `gh secret list` only; no log was opened.
6. Nothing was edited, committed, pushed, opened as an issue or PR, or dispatched, in either repository. The harness's own checks were run inside the harness clone; results are under "Checked and aligned".
7. No held-out transcript text or label content was found in anything read.
8. Nothing in this report states or infers what the held-out labels contain or how many there are. None exist in what was read.
9. The companion report stays at interface level (its rule).
10. This report names the held-out side's expectations itself, in formats and rules, and never held-out content.

### Exclusion checks on the held-out clone

| check | result |
|---|---|
| `transcripts/`, `NAMES`, `PERSONAS` on disk | all three absent |
| `git ls-files -t \| grep -c '^S'` | 8, one line per excluded file: six under `transcripts/` (the count the held-out README publishes at its line 4), plus `NAMES` and `PERSONAS` |
| files on disk | `.github/workflows/checks.yml`, `.gitignore`, `LICENSE`, `holdout:PHASE-5-LABELS.md`, `README.md`, `ruff.toml`, six modules under `tests/`, nine under `tools/`; nothing else |

**This session read no held-out transcript, label or generated name file.** No path under `labels/` or `runs/` exists anywhere in the held-out history at `5760aa9` (`git log --name-only` over `main`): the label chain is at its stage S0, nothing sealed, which is also what its CI gate step reported on its last run.

---

## Findings, most blocking first

Ids are `XH-n`. A mismatch both projects must act on names its held-out twin `XO-n`.

### XH-1 — Held-out severity is owed in a form the held-out label chain cannot carry yet (twin: XO-1)

**Acts:** both projects. **Blocks:** the held-out judged run (C2), because O-10 requires the sealed severity to exist before it; settle before the manifest commit (C1) so the manifest is not re-sealed.

**Harness evidence.**
- `harness:HOLDOUT-OBLIGATIONS.md:505-523@6a0f144` (O-10): held-out findings get severity bands in a separate comparative-judgment store outside the tree, "sealed before that run in a form the gate can check", revealed with the labels; "how the file is sealed is the held-out session's to decide"; owed "all before C2".
- `harness:specs/voice-agent-eval-harness.decisions.md:9522-9526,9553-9561@6a0f144` (D177): option (A) chosen; the coverage report "reads a second severity file from outside this tree after the reveal".
- `harness:specs/voice-agent-eval-harness.md:219-220@6a0f144`: the two coverage criteria name "each banded by its own severity file".
- `harness:tools/verify_phase5.py:146-158@6a0f144`: both coverage criteria declared not yet built; nothing in the harness names the held-out severity file, its schema, or where it sits.
- `harness:src/harness/core/severity.py@6a0f144` is the loader that would read it; the design set's file is `harness:corpus/findings.severity.json@6a0f144` (schema 3, with cuts).

**What the held-out side does (stated here so this report is self-contained).** Its gate admits, under `labels/` and `runs/`, exactly five paths: `labels/MANIFEST`, `runs/heldout-*.jsonl`, `labels/findings.yaml`, `labels/traces.yaml`, `labels/SALT`, and turns red on any other path there (`holdout:tools/label_gate.py:81-85,411-420@5760aa9`). The manifest must hold exactly two digest lines, for `labels/findings.yaml` and `labels/traces.yaml`, after a three-line header (`holdout:tools/label_gate.py:162-187@5760aa9`; `holdout:PHASE-5-LABELS.md:130-138@5760aa9`). Its seal tool writes only those two digests (`holdout:tools/label_manifest.py:133-134@5760aa9`). Its design document still lists held-out severity as the harness's decision to make and as its one open question (`holdout:PHASE-5-LABELS.md:255-257,291-293@5760aa9`).

**What disagrees.** The harness now expects a sealed, later-revealed held-out severity file; the held-out chain has no slot for one, and the held-out side does not yet know the decision was taken.

**Direction.** State what the harness will read after the reveal: the file's name and location in the held-out repository, its schema (the comparative-judgment export the severity loader accepts, whether cuts and bands are required, ids shaped `HF-NN`), and that the manifest must seal it. Put that in O-10 or D177 rather than leaving "how the file is sealed" open, so the held-out side can extend its manifest, gate, seal and reveal in one change before C1. Whether the comparative-judgment tool accepts a second store keyed on `HF-NN` ids is outside this audit (see "Could not check").

### XH-2 — The held-out judged run's corpus-version input is defined on neither side (twin: XO-2)

**Acts:** both projects. **Blocks:** the held-out judged run.

**Harness evidence.**
- `harness:src/harness/cli.py:1335@6a0f144`: `--corpus-version-file` defaults to `corpus/CORPUS_VERSION` inside the checkout; `:790-799` reads it into the provenance and the header; `:845-853` writes `corpus_version` and `artifact_hash` into the header a held-out run commits unmodified.
- `harness:src/harness/cli.py:601-620@6a0f144` (D174) refuses `--transcripts`, `--run-log-dir`, `--run-log` and `--resume` inside the checkout, not `--corpus-version-file` or `--policies`.
- `harness:corpus/CORPUS_VERSION@6a0f144` reads `0.6.0`, the design corpus's version.
- `harness:src/harness/cli.py:1433-1447,1460-1469,1494@6a0f144` and `harness:src/harness/agreement.py:70-74@6a0f144`: `harness agreement` computes the held-out section only when all five of `--held-out-transcripts`, `--held-out-corpus-version-file`, `--held-out-run-log`, `--held-out-findings`, `--held-out-traces` are given, and reads the version file's text.

**What the held-out side has.** No corpus version file: its tracked-file allowlist admits none (`holdout:.github/workflows/checks.yml:125-149@5760aa9`) and its gate admits none under `labels/` or `runs/`. Its procedure names no harness flags for the run beyond the header key `labels_manifest` (`holdout:PHASE-5-LABELS.md:199-200@5760aa9`, §6 steps 3-4).

**What disagrees.** A held-out run made as the held-out procedure reads would stamp the design corpus's version into a header that is committed and never changes; the agreement command later demands a held-out corpus version file that nobody has defined.

**Direction.** Decide what corpus version a held-out run carries: refuse the in-checkout default for a held-out run the way D174 refuses the other paths, or document that the file is passed from outside and what it should say. Then state the full command line for the held-out run in O-9 (tier, mode, `--transcripts`, `--run-log-dir`, `--corpus-version-file`, `--labels-manifest`; `--policies` stays the harness's, since both sets read the same policy documents), so the held-out side can copy it into its §6.

### XH-3 — The run-log file name the harness writes is not one the held-out gate admits (twin: XO-3)

**Acts:** one side must own it; either the harness names a held-out log itself or the held-out procedure states the rename. **Blocks:** committing the run log (C2); the held-out CI turns red on an unrenamed file. Nothing before that.

**Harness evidence.** `harness:src/harness/cli.py:683-686@6a0f144`: `out_path = log_dir / f"{stamp}-{header.mode}.jsonl"` where `stamp` is `started_at` with `:` replaced by `-`, e.g. `2026-09-20T10-00-00Z-live.jsonl`.

**What the held-out side requires.** Under `runs/`, only `runs/heldout-[A-Za-z0-9._-]+\.jsonl` is admitted (`holdout:tools/label_gate.py:85@5760aa9`); anything else there is "not a path the phase-5 chain admits" (`:416-420`). Its design document names the file `runs/heldout-<started_at>.jsonl` (`holdout:PHASE-5-LABELS.md:101@5760aa9`) and its step 4 says only "Commit the log to `runs/`" (`:200`), with no rename.

**Direction.** D173 already tells the run it is held out, so the harness could write a held-out log as `heldout-<stamp>-<mode>.jsonl`, which the held-out pattern admits, and say so in O-9. Otherwise O-9 should record that the file is renamed with a `heldout-` prefix before C2 and leave the step to the held-out procedure.

### XH-4 — "Judged under the frozen rubric" rests on two header fields, and nothing pins the rubric's content to the freeze (twin: XO-4)

**Acts:** harness primarily; the held-out side can add one citation. **Blocks:** nothing yet. `rubric.yaml` and `prompts/judge-dimension.v1.md` at `6a0f144` are byte-identical to the freeze (blobs `31520e09…` and `5e8c3e4f…` at both commits). Close before C2.

**Harness evidence.**
- `harness:tests/test_agreement.py:39-54@6a0f144` pins only that the tag resolves to `RUBRIC_FROZEN_V1`. No test in `tests/` compares `rubric.yaml` or the template at `HEAD` with the freeze commit (grep over `tests/`, `tools/`, `src/` for `rubric-frozen`).
- `harness:src/harness/agreement.py:166-170@6a0f144`: `traces.yaml` keys are compared with the entries of the rubric loaded from the checkout; `harness:src/harness/cli.py:1421-1422,1643@6a0f144` loads that rubric and template from the checkout; the `agreement` parser has no `--allow-stale-replay` (`:1417-1447`), so a post-freeze template edit would make the held-out log unreplayable there.
- `harness:src/harness/core/transport.py:1053-1067@6a0f144`: the header carries `rubric_version`, `prompt_template_hash`, `corpus_version`, `artifact_hash`, `mode`, `started_at`, optionally `resumed_from` and `labels_manifest`, and no harness commit.
- `harness:rubric.yaml:31@6a0f144`: `version: "1"`; the template hash covers the scaffold's two sent halves only (`harness:src/harness/judge/prompt.py:134-158@6a0f144`), not the entry text the rubric renders into the prompt.

**What the held-out side checks.** Its gate compares a run log's `rubric_version` and `prompt_template_hash` with what the freeze commit's own code computes, and nothing else about the harness (`holdout:tools/label_gate.py:291-335,369-374@5760aa9`); its validator reads entry ids from `rubric.yaml` at the freeze commit via `git show` (`holdout:tools/validate_labels.py:203-223@5760aa9`).

**What disagrees.** An entry's question, criteria or scale text can change at `main` without moving the version string or the scaffold hash; the harness would judge with it, the held-out gate would accept the log, and the held-out validator would still map against the frozen entry ids while `harness agreement` maps against the checkout's. Both sides rely on discipline the harness has no test for.

**Direction.** Add a test that `rubric.yaml` and `prompts/judge-dimension.v1.md` at `HEAD` are byte-identical to the commit `RUBRIC_FROZEN_V1` names, or make `harness agreement` read both from that commit. Record the harness commit a held-out run is made at, in O-9's procedure (the C2 commit message) at least, since the header has no field for it.

### XH-5 — HOLDOUT-OBLIGATIONS dates the D101 name-check port to 2026-09-14; the held-out commit is dated 2026-09-11

**Acts:** harness. **Blocks:** nothing.

**Evidence.** `harness:HOLDOUT-OBLIGATIONS.md:527,536,575@6a0f144`: O-11 "Settled 2026-09-14", "Discharged … date 2026-09-14", "O-11 on 2026-09-14". The held-out commit it cites, `d1cefa052af9c676a561f7fc10af3c7821c8b528` ("Port D101's name check, and declare here the two names it found"), carries committer date 2026-09-11 23:10:50 -0700; its CI run `34677492056` succeeded at 2026-09-12T06:11:37Z. The port's content matches O-11's description: `holdout:tools/declare_names.py@5760aa9` writes `NAMES`, the workflow re-runs it with `--check` (`holdout:.github/workflows/checks.yml:239-247@5760aa9`), and the suite holds nine kinds of name to the register or `NAMES` (`holdout:tests/test_holdout_conventions.py:955-1013@5760aa9`).

**Direction.** Date the port to its commit (2026-09-11, or 2026-09-12 UTC) and keep 2026-09-14 as the date it was reported, if that is what happened.

### XH-6 — Harness documents describing the held-out side have gone stale or incomplete

**Acts:** harness. **Blocks:** nothing.

- `harness:README.md:122@6a0f144` describes the held-out repository as "the held-out corpus, whose labels were committed after the rubric freeze". No label commit exists there (held-out history at `5760aa9` has no path under `labels/` or `runs/`; its gate reports stage S0). The row states a rule about the future in the past tense.
- `harness:README.md:122,145@6a0f144` say the held-out repository reads this one "for the conventions it ports and for `HELDOUT_SET`". It now also reads, from the same checkout: the tag `rubric-frozen-v1` (every phase-5 tool there refuses without it); `harness.core.findings` (`REQUIRED_KEYS`, `Owner`, `DetectableBy`, `Tier`, `parse_findings`, `FindingsError`); `harness.core.events` and `harness.corpus.text_adapter.parse_call`; `harness.judge.prompt.load_template` at the freeze commit; `corpus/findings.yaml` (design ids), `corpus/DESIGN_SET`, `corpus/policies`; `specs/transcript-format.md`, `specs/event-model.md`, `corpus/entities.md` (copied into a reviewer's folder, the last two redacted); and the patterns and constants in `tests/test_findings_evidence.py`, `tests/test_corpus_hygiene.py` and `tests/test_speech_plausibility.py`. `HARNESS_READ_TOKEN`'s stated purpose is narrower than what it now serves.
- `harness:tools/verify_phase1.py:374-381@6a0f144`: the caveat enumerates the held-out workflow's steps and omits two that exist there, the `NAMES` declaration check and the phase-5 gate step (`holdout:.github/workflows/checks.yml:239-257@5760aa9`).
- `harness:README.md:196@6a0f144` says `sessions/` holds "the two briefs that govern the held-out repository"; both are marked spent at their own tops (`harness:sessions/HOLDOUT-SESSION-PROMPT.md:1-11@6a0f144`, `harness:sessions/HOLDOUT-REPAIR-BRIEF.md:1-12@6a0f144`) and the held-out repository now carries its own governing document, `holdout:PHASE-5-LABELS.md`.

**Direction.** Reword the three sentences; the token row can say the same checkout is also where the held-out gate resolves the freeze tag and archives the frozen source.

---

## Conventions the harness enforces on the design set with no held-out equivalent

Listed as unported, not evaluated: whether the held-out set satisfies any of them needs its transcripts. Relevant here because O-3's reach statement (`harness:HOLDOUT-OBLIGATIONS.md:208-211@6a0f144`) is still owed and these are rules the held-out set is held to by nothing. Rules tied to the design set's own seeding (seeded exceptions, manifest anchors, the injection pair, vocabulary-exercise counts) are not listed; they have no held-out meaning.

| harness rule | where |
|---|---|
| no shape from an adjacent domain; ticketing's own shapes present | `tests/test_corpus_hygiene.py:179,183@6a0f144` |
| every email in the reserved domain; every telephone number in the reserved range; every ZIP below the lowest assigned; no street address; no payment card number | `tests/test_corpus_hygiene.py:196,202,209,236,243@6a0f144` |
| header duration reconciles with the event log; timestamps never run backwards; every call opens and closes its lifecycle; every call opens with a recording disclosure | `tests/test_corpus_hygiene.py:254,280,290,304@6a0f144` |
| a record does not contradict itself (tool-result detail against context), with its reach check | `tests/test_corpus_hygiene.py:556,1280@6a0f144` |
| every call carries a wrapped event | `tests/test_corpus_hygiene.py:616@6a0f144` |
| every retrieved clause matches the clause it cites, under whitespace normalization (O-2's discharge records this was checked by hand on 2026-09-06, not ported) | `tests/test_corpus_hygiene.py:720@6a0f144` |
| no internal field reaches the caller | `tests/test_corpus_hygiene.py:1635@6a0f144` |
| every action reason code names an action the call attempted | `tests/test_corpus_hygiene.py:1857@6a0f144` |
| every call carries both a calling number and a booking reference | `tests/test_corpus_hygiene.py:2477@6a0f144` |
| every call names the declared platform; every production and venue in a record is declared | `tests/test_corpus_hygiene.py:2793,2816@6a0f144` |
| findings density ceiling per call (a labels-side rule, applicable after the reveal) | `tests/test_corpus_hygiene.py:2756@6a0f144` |
| the corpus median speech rate sits in the conversational band (the per-utterance band is ported; the median is not) | `tests/test_speech_plausibility.py:99@6a0f144` |
| a true negative named in a finding's prose agrees with the seeding manifest (the held-out validator states it is deliberately not ported, since the manifest is design-side) | `tests/test_findings_evidence.py:441@6a0f144` |

The ported ones, for completeness: provenance of tool-call arguments and its exception list; policy retrieval's clause count and the retired clause signature; one event id means one event (both within the set and across the two corpora); a call naming an event identifies it; the escalation convention and the unused `transferred` outcome; used-implies-declared for all nine kinds of name (D101) with the register extractor; agent personas declared; per-utterance speech rate; every evidence rule of `tests/test_findings_evidence.py` except the manifest one; the gold-set generator's check mode.

---

## Checked and aligned

**Run-log header contract (seam 1).**
- The writer's first record is `"record": "header"` (`harness:src/harness/core/transport.py:1053-1062@6a0f144`); the held-out gate reads the first non-blank line and requires exactly that (`holdout:tools/label_gate.py:251-264@5760aa9`).
- `labels_manifest` exists on `RunLogHeader`, is written only when set, and read back with an empty default (`harness:src/harness/core/transport.py:1046-1051,1065-1066,1421@6a0f144`); the harness requires it on any judged run over calls `HELDOUT_SET` declares, refuses it on a design run, refuses a mix of declared and undeclared calls, and accepts only 40 lowercase hex characters (`harness:src/harness/cli.py:159,561-598,819-833@6a0f144`). The gate reads the same key and compares it with the last commit that touched the manifest before the log's commit; a missing key is reported as citing nothing.
- The gate's expected `rubric_version` and `prompt_template_hash` come from the freeze commit's own `rubric.yaml` and its own code, run from a `git archive` of its `src/` in a separate interpreter, with `_DEFAULT_TEMPLATE` read as a literal from `cli.py` at the freeze. Both dependencies exist there: `harness:src/harness/cli.py:125@6d3a710` and `harness:src/harness/judge/prompt.py:220,134-158@6d3a710`. Run in this session against the harness clone, that computation returned `rubric_version "1"` and `prompt_template_hash ce6ec2e5c5aa650abdfb1d4d1b31ad1dda171cbb0f18dba8e410d9ab54cc91be`, equal to the header of `runs/reference-corpus-0.6.0.jsonl` at the freeze and to what main's own code computes for main's template. A run at `6a0f144` would pass the gate's S2 header checks.
- `rubric.yaml` and `prompts/judge-dimension.v1.md` are identical at `6a0f144` and `6d3a710` (blob hashes `31520e09…`, `5e8c3e4f…`; `git diff` empty).

**The held-out run procedure (seam 2).**
- Absolute paths are accepted everywhere a path is taken (`harness:src/harness/cli.py:227-229@6a0f144`); a held-out run's transcripts, log directory, replay log and resume log are refused inside the checkout before anything is written (`:601-620,834-843`).
- `tools/check_holdout_absence.py` refuses a held-out run log in the tree by two records on any line of any non-binary file, read whole: a header naming `labels_manifest`, or a call record whose `call_id` is in `HELDOUT_SET` (`harness:tools/check_holdout_absence.py:217-266,319-326@6a0f144`); the call record the writer emits carries `call_id` at top level (`harness:src/harness/core/transport.py:1149-1153@6a0f144`). Run in the harness clone: `held-out absence check OK`, 16 design transcripts, 5 fixtures, no held-out run log.
- The replay and resume paths refuse a log whose `labels_manifest` differs from the run's, with no override (`harness:src/harness/core/transport.py:1515-1549@6a0f144`).

**What the held-out tools import or copy (seam 3), all present at `6a0f144`.**
- `harness.core.findings`: `REQUIRED_KEYS` (eight keys, `OPTIONAL_KEYS` empty), `Owner`, `DetectableBy`, `Tier`, `parse_findings`, `FindingsError`, `Finding` (`harness:src/harness/core/findings.py:29-147,224-243@6a0f144`). The held-out generator writes exactly those eight keys and reads its own output back through `parse_findings`; the held-out worksheet refuses if the three enums gain a value it has no definition for.
- `harness.corpus.text_adapter.parse_call` and, from `harness.core.events`, `Call`, `EventKind`, `SpeechEvent`, `ToolCallEvent`, `ToolResultEvent`, `StateEvent`, `DisclosureEvent`, `SystemEvent` (`harness:src/harness/core/events.py:31-49,236-389@6a0f144`; `harness:src/harness/corpus/text_adapter.py:592@6a0f144`).
- `HELDOUT_SET` read the same way on both sides (comments and blanks dropped, whitespace stripped): `harness:HELDOUT_SET:22-27@6a0f144` names the same six identifiers the held-out workflow compares its directory against. `corpus/DESIGN_SET` (sixteen ids) and `corpus/findings.yaml` are read for design ids the held-out validator refuses to reuse; `corpus/policies/` is the marker the held-out tools locate the harness by and the source of clause counts.
- Redactions: all four exact-string and five pattern redactions in the held-out packet builder still match `corpus/entities.md` or `specs/event-model.md` at `6a0f144`, and after applying them no design-set identifier survives in either document; `specs/transcript-format.md` names none (checked in this session with the builder's own functions). The reviewer's folder copies the same three documents.
- Copies held by held-out tests, all in the shape those tests read at `6a0f144`: the nine evidence patterns `_EVENT_QUOTE`, `_EVENT_PLAIN`, `_RECORD`, `_SPAN`, `_FINAL_EVENT`, `_CROSS_CALL`, `_GAP_CLAIM`, `_CONTEXT`, `_PROSE_EVENT` as top-level `re.compile` calls in `tests/test_findings_evidence.py:52-105,341-345`; `_sourced_by` (`tests/test_corpus_hygiene.py:1377`), `_UNSOURCED_ARGUMENTS_ALLOWED` (`:1363`), `ESCALATION_RECORD` (`:2519`), `_EVENT_SCOPED_FIELDS` (`:384`), `_REGISTER_CATEGORIES` (`:801`), `_declared_names` (`:814`), the two name-reading patterns inside `test_every_name_the_corpus_uses_is_in_the_register` (`:873,875`), the persona pattern (`:2898`), and `SLOWEST_PLAUSIBLE_WPM`, `FASTEST_PLAUSIBLE_WPM`, `MINIMUM_WORDS_FOR_A_RATE` (`tests/test_speech_plausibility.py:42,43,48`). Renaming or moving any of these fails the held-out suite by design.

**Agreement (seam 4).**
- Held-out finding ids: `HF-\d{2,}` on the harness (`harness:src/harness/agreement.py:50@6a0f144`), `^HF-(\d{2,})$` on the held-out side; no design id has that prefix.
- `traces.yaml`: exactly the keys `rubric-frozen-v1`, `traces`, `uncovered`, `calls_without_findings` (`harness:src/harness/agreement.py:53-58,114-145@6a0f144`), the same four the held-out format names; `RUBRIC_FROZEN_V1` equals the tag's commit.
- Placement rules re-checked by the harness (`harness:src/harness/agreement.py:152-199@6a0f144`) are the held-out validator's: every rubric entry present as a key and no stranger, every finding under an entry or in `uncovered` and never both, every held-out call referenced by a finding or listed under `calls_without_findings` and never both, no duplicates, findings only on calls the set reads. Design and held-out sections are rendered apart, each over its own call count.
- `harness agreement` refuses held-out inputs given in part or inside the checkout, a held-out log naming no manifest, and a set that is not wholly declared (`harness:src/harness/cli.py:1541-1608@6a0f144`); phase-5 criteria and requirements record the same (`harness:specs/voice-agent-eval-harness.md:154-155,217-218,285-286@6a0f144`).
- Harness tests over these seams pass in the clone: `tests/test_holdout_absence.py` and `tests/test_agreement.py` (25 passed) and the held-out subset of `tests/test_cli.py` and `tests/test_transport.py` (21 passed). `python -m tools.verify_phase5`: see the note at the end of this section.

**Records (seam 5).**
- O-9 and D177 describe the chain as the held-out gate enforces it: trailers `Rubric-Frozen: <F>` on every commit touching the manifest, dated after the freeze; `Judged-Run: <C2>` on the reveal; the log's `labels_manifest` equal to the commit that last touched the manifest before the log's commit; `rubric_version` and `prompt_template_hash` at the freeze; the log never changed after it is added; plaintext added once, together, after a passing log.
- D173 and D174 describe what `cli.py`, `transport.py` and `check_holdout_absence.py` do. D175 and D176 describe `agreement.py`, `cli.py` and `verify_phase5.py`; the three criteria the verifier declares as asserted by the held-out gate are the gate's S1 and S3 checks (`harness:tools/verify_phase5.py:113-145@6a0f144`).
- O-11's content matches the port at held-out commit `d1cefa0` (dates aside, XH-5). The standing rule against searching the held-out labeling sessions is in the register (`harness:HOLDOUT-OBLIGATIONS.md:558-563@6a0f144`), which is what the held-out design asked for.
- `corpus/entities.md:333-339` and `HELDOUT_SET` name the same held-out identifiers.

**CI (seam 6).**
- Held-out workflow, as read: checks itself out at `fetch-depth: 0`; checks the harness out at `.harness` with `secrets.HARNESS_READ_TOKEN || github.token`, `continue-on-error`, `fetch-depth: 0` (tags and history for the gate); runs daily at `17 6 * * *` because the harness can turn it red; makes every harness-dependent step conditional on `.harness/pyproject.toml` existing (parse, ported conventions, personas, names, the gate with `HARNESS_ROOT=.harness`, lint); and fails the job when the harness is absent. It installs the harness with `pip install ./.harness` on Python 3.12, which `harness:pyproject.toml:5,49-51@6a0f144` (`requires-python >= 3.12`, hatchling) supports.
- `gh secret list` on the held-out repository: `HARNESS_READ_TOKEN` last set 2026-09-06T08:51:03Z. Its last fifteen runs, including the scheduled one at 2026-09-15T11:43:20Z on `5760aa9`, concluded `success`, so the token worked today. The harness holds `CJ_READ_TOKEN` (set 2026-09-06T09:29:40Z) and no token for the held-out repository, consistent with the held-out design's premise that the harness cannot read it.
- Harness workflow: `tools/check_holdout_absence.py` runs on every push, pull request and dispatch (`harness:.github/workflows/checks.yml:209-214@6a0f144`); its checkout is `fetch-depth: 0` (`:37-44`), which the tag pin test needs; the phase-5 verifier runs in CI (`:153-159`). Its last eight runs concluded `success`, the latest on `6a0f144`.

**Formats (seam 4, manifest).** The manifest's three header lines and two digest lines, the salt as 64 lowercase hex characters with no newline, and the `cat`-recipe digest are consistent between the held-out design document, its tools and its tests; nothing in the harness reads them, which is by design (D176).

**Phase-5 verifier.** `uv run python -m tools.verify_phase5` was run in the harness clone; its result is recorded below under "Verifier result".

---

## Could not check

- Whether `HARNESS_READ_TOKEN` is near expiry. `gh secret list` shows only when it was set (2026-09-06T08:51:03Z); the expiry is visible to the owner alone. It worked on the 2026-09-15 scheduled run.
- Whether the held-out CI holds against harness `main` as of `6a0f144`. Its last run (2026-09-15T11:43Z) preceded the harness commits `c11f1a6`, `febbf73` and `6a0f144`. By file names those three touch nothing the held-out tools read (registers, control mutations, the decision record and specification, `tools/verify_phase*.py`, `tools/check_spec_interface.py`, `src/harness/judge/citations.py`, `src/harness/judge/engine.py`, and their tests); the next scheduled run will say.
- The held-out test suite was not run here (it needs the transcripts); its CI conclusions were read instead.
- Whether the comparative-judgment tool accepts a second store keyed on `HF-NN` ids, which XH-1 presumes. That repository was outside this audit.
- Whether `harness agreement` works end to end on real held-out inputs. It is proven over invented labels on a split design corpus, which its own verifier caveat states.
- Whether the owner's machine has the pre-commit guards installed, and whether anything sits in a `private/labels/` directory. Both are owner-only; the held-out README says the guard is not shipped there.
- Whether the held-out set satisfies any of the unported conventions listed above. That needs the transcripts, which this session did not read.
- Anything about held-out labels: none exist in what was read, and nothing was inferred.

---

## Verifier result

`uv run --no-sync python -m tools.verify_phase5` in the harness clone at `6a0f144`, run over the whole suite: exit 0. Its closing lines: "All 4 checks pass, each by running it — 4 of them the specification's own [P5] acceptance criteria. 4 carry a stated caveat above; a tick is not a claim they do not. 5 more are declared and not ticked: 3 asserted elsewhere, 2 not yet built. The suite as a whole passed too, not only the tests these criteria name." The three declared as asserted elsewhere are the held-out gate's S1 and S3 checks (label ordering, freeze citation, manifest recomputation); the two not yet built are the coverage report's, which XH-1 concerns.
