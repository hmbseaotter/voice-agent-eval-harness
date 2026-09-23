# Sweep — the specification at 0.65.0 @ D210, read against the tree for the publication and the accrued count

> **STATUS.** Written 2026-09-22 at `9a22427` by a session that took no part in phase 6's opening,
> the publication or the freeze proof (Claude Fable 5.1). **It reports and edits nothing**: this
> file is the only one the session added, and the specification, the decision record and the
> registers are as it found them. A later session applies what the owner accepts from section 2,
> writes the sweep's changelog entry, and moves the `Last swept` marker; section 7 says how far the
> marker may move. A session that acts on a finding records it in this banner, so that the banner
> and not the body is what a reader trusts for status.
>
> **2026-09-22, applied — 23 of 26 applied whole, 2 left recorded as unbacked, 1 left as judged.** Worked by the session that published the project, on the owner's decisions, and recorded at specification 0.66.0 with the `Last swept` marker moved there. Every finding was re-verified in this tree before it was acted on, and all of those checked reproduced; two figures had drifted since the report was written — 296 commits on `main` is 297, and the brief this sweep answered is itself now spent. **S-1 and S-16 are applied as D211**, on a shape this report did not list: the snapshot rewrites nothing at all, which removes S-1's stale-tag failure by removing the tag, makes the published pin name the freeze so the held-out commands accept real labels there, and leaves the published tree one commit differing in 2 files. **S-6 and S-23 stay as this report left them** — unbacked from this side, with S-23's reconciliation recorded as reported. **S-11's site is left alone**, as the report advised, beyond changing *two things* to *one thing*.
>
> **Two triggers fired, and one of them fired in public.** The accrued count stands at ten, D201 to
> D210, which is the ceiling `tests/test_document_counts.py` holds, so the next decision recorded
> turns `main` red without this sweep. And *before publishing* fired unobserved: the project was
> published as a snapshot on 2026-09-21 with the marker at 0.60.0, then rebuilt and pushed four
> more times, so the specification a stranger reads has not been read against the tree since
> 0.60.0. Section 6 says what that cost.
>
> **26 findings, none acted on: 11 Wrong, 13 Stale and 2 Unbacked.** The one to read first is S-1:
> the public repository's CI has failed on every one of its five builds, on one test, because of the
> order in which the snapshot tool tells its operator to push, and every step after the suite has
> been skipped in public every time. The second is S-16: in the published tree the pin
> `RUBRIC_FROZEN_V1` names the snapshot's own first commit, so the two commands the README says
> can recompute the held-out figures refuse the real held-out labels there.
>
> **No model call was made, nothing was tagged, no other repository was edited, and the held-out
> repository was not opened** — not by listing, by path or by search. Reads outside this tree were
> read-only GitHub API calls and are each named in section 4: the account's repository listing for
> visibility; the published snapshot's commits, tag, top-level tree and three of its files; the CI
> run lists of this repository, the snapshot and `comparative-judgment`, with the failed logs of the
> snapshot's five runs; the secret *names* of those three repositories; and the dispatch lines of
> `comparative-judgment`'s workflow with its three newest commit subjects. **A second report of this
> same sweep, written the same day by a session working in the held-out repository and kept outside
> this tree, was read as a reference after the findings above were written**: S-24 to S-26 are what
> it found that this sweep had missed and could confirm here, two of its readings are recorded under
> S-6 and S-23 as reported rather than verified, and it enters the tree nowhere.

**Kind of review.** A sweep, not an audit: every section of the specification except the changelog
was read for statements that describe the project *now*, and each was checked against the tree,
with the `Not checked` block, the README, both obligation registers, the control register's counts
and newest sections, the freeze proof's README, the snapshot note's template, the phase-6 contract
reading and the tops of every session document beside it. The mechanized half was run first and
then read past, as the brief asked. Every finding is marked **(reproduced)**, where a command or a
read of the thing itself printed the contrary, or **(by reading)**, where the contrary is in another
document of this tree and nothing here computes it. Severity is the brief's: **Wrong** is false
today, **Stale** was true when written and describes a state the project has left, **Unbacked** may
be true and nothing in the tree can tell.

**Numbers in this report are written as digits throughout**, because a digit is what this
project's count guards read as a record, and every count here is one: a measurement of the tree
at `9a22427` and of GitHub on 2026-09-22.

---

## 1. Baseline, reproduced

At `9a22427`, `main`, working tree clean. The two newest commits, `6843c5f` and `9a22427`, carry
`[skip ci]` in their bodies and are prose-only, so CI's verdict at HEAD is the run at `45d41b2`,
which passed (2026-09-22T01:32:59Z).

```
$ uv run pytest -q tests/test_document_counts.py tests/test_contract_coverage.py tests/test_obligations.py tests/test_phase3_acceptance.py tests/test_findings_evidence.py
149 passed in 60.78s (0:01:00)

$ uv run python tools/statement_inventory.py
every identifier named in prose resolves

$ uv run python tools/check_holdout_absence.py
held-out absence check OK -- the working tree carries exactly the 16 declared design-set transcripts and 5 declared test fixtures, no others, no held-out run log, no report over held-out calls, no coverage report over held-out findings, no held-out labels or agreement section, and no file it could not decode

$ uv run python -m tools.verify_freeze_proof
the freeze proof verifies: rubric-frozen-v1 -> 6d3a710
  rubric.yaml is byte for byte the file the freeze named
  prompts/judge-dimension.v1.md is byte for byte the file the freeze named
  the frozen src reconstructs from objects/ and computes
  ce6ec2e5c5aa650abdfb1d4d1b31ad1dda171cbb0f18dba8e410d9ab54cc91be for the template, in its own code
  recomputed from the published bytes alone -- no history, no network, no clone

$ uv run python tools/check_spec_interface.py specs/voice-agent-eval-harness.md,specs/voice-agent-eval-harness.decisions.md,specs/voice-agent-eval-harness.build-prompt.md ../comparative-judgment/specs/comparative-judgment.md,../comparative-judgment/specs/comparative-judgment.decisions.md
spec interface: OK -- 6 findings keys and 8 severity fields and 6 row fields agree, each read from its list sentence in the two specifications, across 3 harness file(s) and 2 tool file(s); severity joined by id on both sides, no stale cross-claims
```

The scanner ran against the sibling checkout beside this root, at its `3521160` of 2026-09-19, one
commit behind the public tip, whose only change is the workflow's dispatch target. The full suite
and the phase-6 verifier were run as well; their lines are at the end of this section. What the tree holds, counted rather than read: 1,371 tests collected across 45 modules; 359
entries in `control-mutations.yaml`, which is the tagged figure the control register carries; 44
rubric entries, 37 `assert` and 7 `judge`, of which 20 declare no negative instance; 43 declarations
in `severity-properties.yaml`; 90 findings in `corpus/findings.yaml`, 7 of them question-tier, and 83
rows with an empty `unplaced` in the severity file at schema 3; 6 held-out identifiers in
`HELDOUT_SET`; 16 Retell documents under `corpus/retell/`; 35 taxonomy rows and 35 known-weakness
rows in `specs/taxonomy-coverage.md`, with the tally's GAP row at 0; 296 commits on `main`, 219 of
them reachable from the freeze commit `6d3a710` and 77 after it; and under `freeze-proof/objects/`
36 files, 30 blobs and 6 base64 trees, which is 34 frozen files with 5 empty ones sharing a blob.

The header's marker reads `2026-09-20 @ 0.60.0 @ D200`; the specification is at 0.65.0 and the
record at D210, so `accrued` is 10 against a ceiling of 10.

**GitHub, read once on 2026-09-22 (UTC):**

| repository | visibility | created | notes |
| --- | --- | --- | --- |
| `voice-agent-eval-harness-private` | private | 2026-08-28 | the working repository, id 1349335515; holds one secret, `CJ_READ_TOKEN`, installed 2026-09-06 |
| `voice-agent-eval-harness` | public | 2026-09-21T10:05Z | the snapshot: 2 commits, `3958a91` then `4b965b1`, tag `snapshot-rubric-pin-v1` at `3958a91`, built from `6843c5f`; holds no secret |
| `voice-agent-eval-harness-holdout` | private | 2026-08-28 | not opened |
| `comparative-judgment` | public | 2026-08-28 | tip `3b844ef`, 2026-09-21, *Update GitHub Actions workflow to use private repo*; holds one secret, `HARNESS_DISPATCH_TOKEN` |

The snapshot has been pushed 5 times, at 2026-09-21T10:20Z, 11:41Z, and 2026-09-22T00:22Z, 01:47Z
and 04:20Z. Every one of the 5 CI runs failed; section 2 opens with why.

Full suite and phase-6 verifier, run locally at `9a22427`:

```
$ uv run pytest -q
FAILED tests/test_phase2_acceptance.py::test_the_reuse_path_accepts_the_relative_path_ci_passes_it
1 failed, 1370 passed in 2296.95s (0:38:16)

$ uv run pytest -q "tests/test_phase2_acceptance.py::test_the_reuse_path_accepts_the_relative_path_ci_passes_it"
1 passed in 2.07s

$ uv run python -m tools.verify_phase6
All 6 checks pass, each by running it — 6 of them the specification's own [P6] acceptance criteria.
6 carry a stated caveat above; a tick is not a claim they do not.
6 more are declared and not ticked: 0 asserted elsewhere, 6 not yet built.
The suite as a whole passed too, not only the tests these criteria name.
```

The one failure is recorded as measured and not explained. That run shared the checkout with the
phase-6 verifier's own whole-suite run and three fast-check runs; the test compares a report's
modification time with the newest file in the tree; alone it passes in 2 seconds; the verifier's
concurrent run reported the suite whole as passed; and CI at `45d41b2` is green. A test that reads
modification times across the tree is sensitive to a second run in the same checkout, which is an
observation about how this baseline was taken rather than a finding about the tree.

---

## 2. Findings

### The publication

**S-1 — Wrong (reproduced). The public repository's CI has never been green, and the tail of the
workflow has never run there.**

- *Where:* `tools/make_public_snapshot.py:275-281`, the push instructions the tool prints (*push
  main, then push the tag*); the snapshot note's template at `tools/make_public_snapshot.py:138-140`
  (*Everything else runs as it is documented ... `uv run pytest`*); and `README.md:263-264`
  (*Every workflow here can be run by hand*).
- *What is true instead:* all 5 runs of the snapshot's workflow failed at the **Tests** step, on the
  same test each time, and the 14 steps after it were skipped every time — the deterministic tier,
  the 6 phase verifiers, the report diff, the statement inventory, the control gate, the held-out
  absence check, the findings view and the interface check. None of those has ever run in the
  public repository. The failing test is `test_the_pinned_frozen_commit_is_the_one_the_tag_points_at`,
  and the reason is push order: the workflow triggers on the branch push and resolves the tag
  before the tag push arrives, so on a first build the tag does not exist and on a refresh it still
  names the previous build's first commit. On the newest run the tag resolved to `5882092f…`, the
  first commit of the build before, against a pin of `3958a91…`; when this sweep read the tag a
  few minutes later it was at `3958a91`, so a clone made now passes the test that CI failed.
- *How checked:*

  ```
  $ gh run list -R hmbseaotter/voice-agent-eval-harness --limit 6 --json databaseId,headSha,createdAt,conclusion
  35686517394 4b965b1 2026-09-22T04:20:34Z failure
  35677099444 74c54ad 2026-09-22T01:47:55Z failure
  35671660288 9f8811a 2026-09-22T00:22:10Z failure
  35595449219 9b50e59 2026-09-21T11:41:59Z failure
  35588185512 bc04772 2026-09-21T10:20:08Z failure
  $ gh run view 35686517394 -R hmbseaotter/voice-agent-eval-harness --log-failed | grep -E 'FAILED |passed'
  FAILED tests/test_agreement.py::test_the_pinned_frozen_commit_is_the_one_the_tag_points_at - AssertionError: assert '5882092fe4da...c97614d925038' == '3958a9125c87...f53425f3f1e1e'
  1 failed, 1370 passed in 100.11s (0:01:40)
  ```

  The run before it asserted `bab9a3c9…` against `5882092f…`; the one before that could not resolve
  `snapshot-rubric-pin-v1` at all; the second asserted `511356dc…` against `35a32c89…`; the first
  could not resolve `rubric-frozen-v1`, the name the snapshot reused before D209. The step list of
  the newest run reads `success` through *Extraction runs and the corpus parses clean*, `failure` at
  *Tests*, and `skipped` for everything after.
- *Proposed:* the tool's printed instructions push both refs in one command, so the workflow sees
  the tag when it starts — `git push --force --atomic origin main snapshot-rubric-pin-v1` — and the
  docstring says why; then the current build's workflow is re-run by hand once, so the public
  repository shows a run that reached the end. Not tested here: whether an atomic push of a branch
  and a tag makes the tag visible to the run the branch push starts; if it does not, the tag goes
  first and the branch second. Either way the note's sentence should say what a reader will see in
  the Actions tab until then.

**S-2 — Wrong (reproduced). The README says all three repositories are private, and that each holds
one secret.**

- *Where:* `README.md:219-221` — *Each repository holds exactly one secret ... all three of these
  are private.*
- *What is true instead:* two of the four are public since 2026-09-21, and the public snapshot holds
  no secret at all. The sentence is in the public README at its line 222.
- *How checked:* the repository listing above; `gh secret list -R hmbseaotter/voice-agent-eval-harness`
  prints nothing; the same for the private working repository prints `CJ_READ_TOKEN
  2026-09-06T09:29:40Z`.
- *Proposed:* *Two of the repositories are private today, the working repository and the held-out
  one; the published snapshot and `comparative-judgment` are public. The working repository and
  `comparative-judgment` each hold one secret, because CI has to reach across a boundary the default
  `GITHUB_TOKEN` cannot cross while the far side is private; the snapshot holds none.*

**S-3 — Wrong (reproduced). The README names the wrong repository as the one `comparative-judgment`
dispatches to.**

- *Where:* `README.md:246` — *`comparative-judgment`'s `.github/workflows/checks.yml` |
  `hmbseaotter/voice-agent-eval-harness`, whose workflow it starts*; `README.md:227`, where
  `HARNESS_DISPATCH_TOKEN` grants *Actions: Read and write on this repository*; `README.md:204`, the
  topology table's third row, where the tool *asks this repository to run the interface scanner*;
  and `README.md:269-271`, where a reader checking the token is told a dispatch run *must appear in
  this repository's Actions tab* — which, in the public copy, it never will.
- *What is true instead:* that workflow names `hmbseaotter/voice-agent-eval-harness-private`, the
  working repository, since its commit `3b844ef` of 2026-09-21T10:08Z, and its dispatch at 10:13Z
  landed there. In the public README, *this repository* is the snapshot, which nothing dispatches
  to and which holds no token.
- *How checked:* `gh api repos/hmbseaotter/comparative-judgment/contents/.github/workflows/checks.yml`
  decoded, lines 133 and 148: *needs Actions: write on hmbseaotter/voice-agent-eval-harness-private*
  and `--repo hmbseaotter/voice-agent-eval-harness-private --ref main`; `gh run list -R
  hmbseaotter/voice-agent-eval-harness-private` shows `2026-09-21T10:13:58Z workflow_dispatch
  a112053 success`.
- *Proposed:* name the working repository in both places, and say in the token section that the
  snapshot is a copy of a tree, not a participant in the three-way arrangement.

**S-4 — Stale (reproduced). The `CJ_READ_TOKEN` sentences describe a token that is no longer
load-bearing.**

- *Where:* `README.md:225`, `README.md:277-278` (*the one token this repository holds, expires on
  2026-11-05*) and `README.md:290-294` (*`CJ_READ_TOKEN` lapses → the sibling checkout fails, and
  the interface check compares nothing*).
- *What is true instead:* `comparative-judgment` went public on 2026-09-21, so the checkout falls
  back to `github.token` as the workflow comment says it will, and a lapse now costs nothing. The
  token still exists in the working repository, so the expiry date is true there and false in the
  public README, which holds no token. `README.md:280` says the read tokens stop being needed once
  the repositories are public; that has happened for this one.
- *How checked:* the repository listing; `.github/workflows/checks.yml:50` — `token: ${{
  secrets.CJ_READ_TOKEN || github.token }}`; the secret listing in S-2.
- *Proposed:* say that the token was needed while the sibling was private, that the sibling is
  public since 2026-09-21 and the checkout no longer depends on it, that it still sits in the
  working repository and expires on 2026-11-05, and that removing it is the owner's call.

**S-5 — Stale (by reading). The README still says the held-out repository resolves the
`rubric-frozen-v1` tag.**

- *Where:* `README.md:203` — *the `rubric-frozen-v1` tag its phase-5 tools resolve*; `README.md:226`
  — *the `rubric-frozen-v1` tag they resolve the frozen source from*.
- *What is true instead:* O-12 was discharged on 2026-09-21 (`HOLDOUT-OBLIGATIONS.md:614-633`): that
  side's gate reconstructs the frozen `src` from `freeze-proof/objects/` and runs its probe against
  the reconstruction, *in place of archiving a commit this repository no longer publishes*. The
  commit that recorded the discharge, `6843c5f`, changed the register and not the README.
- *How checked:* by reading O-12's discharge paragraph and `git show --stat 6843c5f`.
- *Proposed:* *the freeze proof under `freeze-proof/`, which its gate verifies by recomputation*
  in both places.

**S-6 — Unbacked. Which repository the held-out workflow checks out, and whether
`HARNESS_READ_TOKEN` still does anything.**

- *Where:* `README.md:245` — the held-out workflow checks out `hmbseaotter/voice-agent-eval-harness`;
  `README.md:226` and `README.md:295-296`.
- *What may be true instead:* that name now resolves to the public snapshot, and the token named
  beside it was minted for the working repository, whose id is unchanged by the rename. If the
  held-out workflow was not re-pointed, it checks out the snapshot with a token scoped to a
  different repository, which works only because the snapshot is public; if it was re-pointed, the
  README's row is wrong in another way. Nothing in this tree can tell, and this sweep did not open
  that repository.
- *What would settle it:* one read of that workflow's `repository:` line by a session cleared to
  open the held-out repository, recorded beside O-12 as the other ports are.
- *As reported, not verified here:* the second report of this sweep, written from inside that
  repository, reads its workflow as checking out `hmbseaotter/voice-agent-eval-harness` — now the
  public snapshot — and as passing no token since a commit of 2026-09-21 made there, with
  `HARNESS_READ_TOKEN` still installed and unused. If that holds, `README.md:226`'s row and the lapse
  bullet at `:295-296` are retired rather than corrected. The rule this register lives by applies:
  nothing here can confirm it, so it is recorded as reported.

### The specification

**S-7 — Stale (reproduced). The header still says the project is not yet public.**

- *Where:* `specs/voice-agent-eval-harness.md:14` — *Visibility: private today; public is the plan
  ... Not yet flipped, and the line says so rather than naming the intended end state as if it were
  the current one*; and `:13` — *Artifacts land in: the `voice-agent-eval-harness` repository root*.
- *What is true instead:* the project is public since 2026-09-21 as a snapshot under
  `voice-agent-eval-harness` (D208), and the working repository, where the artifacts land, is
  private under `voice-agent-eval-harness-private`. The line was written to avoid naming an end
  state as the current one, and now names a starting state as the current one, in the one document
  whose header a public reader meets first.
- *How checked:* the repository listing; `git remote -v` here prints the `-private` name.
- *Proposed:* *Visibility: the working repository is private, under `voice-agent-eval-harness-private`;
  the project is public since 2026-09-21 as a snapshot of one commit under
  `voice-agent-eval-harness`, built by `tools/make_public_snapshot.py` (D208), because a history
  scan before the flip found what a flip would publish. The held-out repository is private today.*
  And for line 13: *the working repository's root*, with the private name.

**S-8 — Stale (by reading). Four sentences describe the flip D2 planned rather than the snapshot
D208 took.**

- *Where:* `specs/voice-agent-eval-harness.md:107` — the three-repo topology, each *(private →
  public)*; `:119` — *a history scan at the flip to public*; `:387` — *Built private and flipped
  public after a history scan (D2)*; `:35` — *once public*.
- *What is true instead:* there are four repositories, not three; the harness did not flip but was
  copied; the history scan happened, on 2026-09-21, and its result was that the history could not be
  published as it stood (D208); `comparative-judgment` flipped with its history; the held-out
  repository has not moved.
- *How checked:* by reading D208 and D209 against each line, and the listing in section 1.
- *Proposed:* line 107 gains the fourth name and says which arrow has been taken and how; line 119
  reads *the history scan before publication, which D208 records*; line 387 reads *Built private,
  and published as a snapshot after a history scan (D2, D208)*; line 35 reads *now that the tree is
  public*.

**S-9 — Wrong (by reading). The status line says everything that needs no model call is built.**

- *Where:* `specs/voice-agent-eval-harness.md:5` — *phase 6 is open, its contract read and what needs
  no model call built and verified, with prompt caching, judge-model comparison and the design
  document still to build (D201)*.
- *What is true instead:* three pieces of phase 6 need no model call and are not built. A check that
  reads a declared gap, which OB-51 records and the phase-6 contract reading calls *the phase's own
  goal* (`sessions/PHASE-6-CONTRACT-READING.md:220-222`). The caching layout criterion at `:322`,
  which says *with no model call* in its own text and is declared not yet built in
  `tools/verify_phase6.py:209-218`. The comparison's hash criterion at `:233`, likewise *with no
  model call* and declared at `tools/verify_phase6.py:182-191`. The line's own qualifier covers the
  second and third under their deliverables' names and does not cover the first.
- *How checked:* the verifier's `DECLARED` tuple and the register's OB-51 row. The other reading of
  this line, that its qualifier names the unbuilt deliverables and so the line is consistent, is
  the one the second report took; it is arguable for the two criteria and not for OB-51, which no
  deliverable name in the line covers.
- *Proposed:* *phase 6 is open, its contract read, and the second adapter, the log inspector and
  per-instance severity built and verified; prompt caching, judge-model comparison, the design
  document and a check that reads a declared gap (OB-51) are still to build (D201, D203); 7 is not*.

**S-10 — Stale (by reading). Three `[P5]` clauses name a tag the held-out gate no longer resolves,
and the fork D209 deferred is now due.**

- *Where:* `specs/voice-agent-eval-harness.md:295` — *asserted by a script that resolves the tag in
  the main repository and compares the two SHAs*; `:294` — *later than the `rubric-frozen-v1` tag*;
  `:155` — *name a frozen commit other than the one `rubric-frozen-v1` points at*; and, a site the
  second report found and this tree confirms, `tools/verify_phase5.py:265-268`, the declared reason
  for the freeze-citation criterion — *Asserted by the held-out repository's gate, which compares the
  frozen commit each label commit cites with the one the tag points at* — which the verifier prints
  on every run. D209 speaks of the two criteria that name the tag; three do (`:294`, `:295`, `:302`),
  with the requirement at `:155` a fourth. `:302` is held by a test in this repository and stands.
- *What is true instead:* since O-12's discharge the gate reads the freeze commit out of the
  published proof rather than resolving a tag anywhere (`HOLDOUT-OBLIGATIONS.md:614-618`), and the
  harness itself compares labels against the pinned `RUBRIC_FROZEN_V1` (`src/harness/agreement.py:171`),
  never against a tag. D209 left the two criteria alone deliberately, calling an amendment to a
  closed phase's criterion its own fork and saying the wording may need to move when the port lands
  (`specs/voice-agent-eval-harness.decisions.md:11064-11069`). It has landed. Whether a closed
  phase's criteria may be reworded is the owner's fork; this report only says the condition D209
  named has arrived.
- *How checked:* by reading O-12 and D209, and `agreement.py:160-175`.
- *Proposed, if the owner takes the fork:* 295 reads *asserted by a script that reads the freeze
  commit out of the published proof under `freeze-proof/` and compares the two SHAs (D209, D210,
  O-12)*; 294 reads *later than the freeze commit that proof names*; 155 reads *other than the freeze
  commit this repository pins as `RUBRIC_FROZEN_V1`*; the verifier's reason reads *which reads the
  freeze commit out of the published proof and compares it with the one each label commit cites*.
  `:353`, phase 5's ordered list, is a record of the order the phase ran in and stays.

**S-11 — Wrong (by reading), low, and not worth acting on alone. One sentence counts two and
lists one.**

- *Where:* `specs/voice-agent-eval-harness.md:369` — *Two things are deliberately not claimed here:
  that repository's current defect state (...)*. The second thing, its version, is named in the
  sentence before the colon.
- *Proposed:* if the line is touched for another reason, *Its version is its own specification's to
  state, and its current defect state is not claimed either*.

### The freeze proof and the snapshot note

**S-12 — Wrong (reproduced). The proof's README calls the held-out seal commit public.**

- *Where:* `freeze-proof/README.md:51` — *holdout seal commit (public, 2026-09-17) cites 6d3a710*;
  `:18-19` — *a citation published on 2026-09-17*; `:158-159` — *the holdout published this one on
  2026-09-17*.
- *What is true instead:* the held-out repository is private. The seal commit C1 was made there on
  2026-09-17 and the plaintext labels were revealed at C3 on 2026-09-18 (O-9); neither is reachable
  by a stranger, so the first link of the chain the README draws is the one link a public reader
  cannot follow. This document is a public reader's first meeting with the project's central
  evidence claim, and its first sentence about that claim sends them to a 404.
- *How checked:* the repository listing in section 1; `HOLDOUT-OBLIGATIONS.md:521-531` for C1 and
  C3.
- *Proposed:* *holdout seal commit (2026-09-17, in the held-out repository, which is private today)*
  at line 51, *a citation committed there on 2026-09-17* at 19, and a sentence under *What it is for*
  saying that the citation's own repository is not yet public and that the proof stands on this side
  regardless.

**S-13 — Wrong (reproduced). The commit count behind the freeze is off by about a quarter.**

- *Where:* `freeze-proof/README.md:28` — *The roughly 290 commits behind the freeze stay private*.
- *What is true instead:* 219 commits are reachable from the freeze; `main` holds 296, 77 of them
  after it. 290 is close to the whole history and not to the part behind the freeze.
- *How checked:*

  ```
  $ git rev-list --count 6d3a7101aaa1f15b440de43fe5142434f69c9dc9
  219
  $ git rev-list --count HEAD
  296
  ```

- *Proposed:* *The commits behind the freeze stay private, and nothing here needs them*, with no
  number; or *the 219 commits behind the freeze*, as a dated figure.

**S-14 — Wrong (reproduced). The recipe for verifying any object under `objects/` names an object
that is not there.**

- *Where:* `freeze-proof/README.md:140-142`:

  ```
  id=31520e09762db6d753e6937776f1ac6d54271eca   # any name in objects/, without .b64
  { printf "blob $(wc -c < objects/$id)\0"; cat objects/$id; } | sha1sum
  ```

- *What is true instead:* `31520e09…` is the frozen `rubric.yaml` blob, which the root tree names and
  `objects/` does not hold: `objects/` is the frozen `src` subtree only. Run as printed from
  `freeze-proof/`, the recipe fails with *No such file or directory* and prints a digest of nothing.
- *How checked:*

  ```
  $ ls freeze-proof/objects | grep -c 31520e09
  0
  $ id=01ff64826b991836ebc7dca84c0c6324588578a5; { printf "blob $(wc -c < freeze-proof/objects/$id)\0"; cat freeze-proof/objects/$id; } | sha1sum
  01ff64826b991836ebc7dca84c0c6324588578a5 *-
  ```

  The four core recipes at lines 121-124 and the rubric recipe at 130 all print the ids the README
  names, and the four SHA-256 digests match.
- *Proposed:* pick a name that exists rather than quote one — `id=$(ls objects | grep -v '\.b64$' |
  head -1)   # any blob under objects/` — and say in the sentence above it that `objects/` holds the
  frozen `src` subtree and the rubric blob is the previous recipe's.

**S-15 — Stale (reproduced). The snapshot note describes the proof as D209 left it, not as D210
did.**

- *Where:* `tools/make_public_snapshot.py:127-131`, the template's second bullet — *`freeze-proof/`
  publishes that commit's own bytes together with its tag and the two trees reaching the frozen
  `rubric.yaml` and prompt template ... (D209)*.
- *What is true instead:* since D210 the proof also publishes the whole frozen `src` subtree, 36
  objects, and the verifier runs the frozen code over it. The note built from `6843c5f`, after
  D210, says the same in public.
- *How checked:* the template; the public note's tail, read through the API, carries the sentence
  unchanged.
- *Proposed:* add *and, under `objects/`, the whole frozen `src` subtree, so the held-out gate can run
  the frozen code (D210)* to the bullet.

**S-16 — Wrong in the published tree (by reading, with the constant reproduced). In the snapshot,
the held-out agreement and coverage commands refuse the real held-out labels, and the note does not
say so.**

- *Where:* `README.md:104-111` and `README.md:117-126`, which tell a reader the held-out section is
  printed when the held-out inputs are given; `specs/voice-agent-eval-harness.decisions.md:11204-11205`
  and D202 (`:10711-10713`), which say blind agreement is *recomputable from the held-out repository's
  published labels and committed log*; and the snapshot note's pin bullet at
  `tools/make_public_snapshot.py:132-137`, which says the tests pass and nothing about the commands.
- *What is true instead:* `check_held_out_labels` refuses traces naming any commit but
  `RUBRIC_FROZEN_V1` (`src/harness/agreement.py:171-174`). In the published tree that constant is
  `3958a9125c870c79605bae6282cf53425f3f1e1e`, the snapshot's own first commit, so the real
  `traces.yaml`, which cites `6d3a710`, is refused by `harness agreement` and `harness coverage`
  there. The recomputation the README and the record promise can be made only from the private
  working repository. Today the held-out repository is private too, so no stranger is stopped yet;
  the owner is, and the promise is in print.
- *How checked:* `gh api repos/hmbseaotter/voice-agent-eval-harness/contents/src/harness/agreement.py`
  decoded, line 47; the comparison at `agreement.py:171` read here.
- *Proposed:* the owner's fork, with three options in the order this sweep would take them. (a) The
  note says it: *In this snapshot the held-out agreement and coverage commands refuse the real
  held-out labels, because the pin they check them against is this snapshot's own; run them from a
  checkout that pins the freeze.* (b) The two commands compare labels against the freeze commit the
  proof names, read from `freeze-proof/freeze-commit.txt` by git's own rule, so the pin the snapshot
  rewrites stops being the one the labels are checked against. (c) The snapshot leaves
  `RUBRIC_FROZEN_V1` alone and makes the tag test skip where the tag is absent, which trades one
  false statement for a weaker test. (a) now and (b) as a registered obligation is the
  recommendation.

**S-17 — Wrong (reproduced). The snapshot note says every session document carries a maintained
status banner.**

- *Where:* `tools/make_public_snapshot.py:123-124` — *`sessions/` holds the audits, the sweeps and the
  briefs sessions were given, each with a status banner a later session maintained*.
- *What is true instead:* 12 of the 32 files carry none in their opening lines: the 11 session and
  audit briefs from phase 3 onward, and `sessions/HANDOVER-2026-09-08-phase-2-residue.md`, which opens
  with a session line rather than a status. The README's own sentence at `:328-330` claims a spent
  marker for the two held-out briefs only, which is what exists.
- *How checked:* the first 5 lines of every file under `sessions/` searched for a status marker
  (*STATUS*, *Status*, *SPENT*, *FROZEN*, *READ 2026*, *WORKING STATUS*, *Received*); the 12 above
  matched none. Of the 11 briefs, 9 are spent — the session each names has run and is recorded in a
  handover or a decision — and the sharpest is `sessions/PHASE-6-SESSION-PROMPT.md`, which still
  tells a reader to start from `76c2022` or later and open phase 6: that commit resolves here and not
  in the published log, and the phase it opens is open and half built, so a stranger who does what
  it says starts a second phase-6 session against a contract that has moved.
- *Proposed:* a **SPENT** line at the top of each of the 9, in the shape the two held-out briefs use,
  naming the handover or decision that discharged it; and the template sentence narrowed to what is
  true — *the audits and the sweeps with a status banner a later session maintains, the handovers
  with a status line, and the briefs sessions were given, marked spent once the handover they name
  exists*.

### The `Not checked` block

**S-18 — Stale (by reading). The license entry describes the README's boundary as it was before D201,
and two refresh sentences say no entry describes what the README licenses.**

- *Where:* `specs/voice-agent-eval-harness.decisions.md:11192` — *`src/` and `tools/` Apache-2.0,
  `corpus/`, `specs/` and `rubric.yaml` CC BY 4.0*; the 0.61.0 and 0.62.0 refresh sentences at
  `:11154`.
- *What is true instead:* since D201 the README names a license for every top-level path and
  `test_the_readme_names_a_license_for_every_top_level_path` holds it; D207 corrected the check's
  population. The entry's point stands — `sessions/` is under neither, by a decision the owner has
  not taken — but its enumeration is 0.60.0's, and the two refresh sentences that should have moved
  it say no entry describes what the README licenses, which this one does.
- *How checked:* by reading the entry against `README.md:41-48` and `:337-341`.
- *Proposed:* the entry's enumeration reads *code, configuration and tooling Apache-2.0, authored
  data and documentation CC BY 4.0, every top-level path named (D201)*; the next refresh sentence
  records that it moved.

**S-19 — Stale (reproduced). The entry that says what "the audit" names lists four audit reports
where six exist.**

- *Where:* `specs/voice-agent-eval-harness.decisions.md:11245` — the four `sessions/AUDIT-*.md` it
  enumerates end at 2026-09-12.
- *What is true instead:* `sessions/AUDIT-2026-09-15-cross-project.md` and
  `sessions/AUDIT-2026-09-19-phase-5.md` are tracked with maintained banners. The 0.60.0 sweep moved
  this entry and it still enumerates four; the entry's opening clause, *every `sessions/AUDIT-*.md`*,
  is the true statement and the list under it is not.
- *How checked:* `ls sessions/AUDIT-*.md` prints 6.
- *Proposed:* drop the enumeration, which the opening clause already makes, or extend it to six.

### Beside the specification

**S-20 — Stale (reproduced). OB-59 counts six accrued decisions where ten have accrued.**

- *Where:* `OBLIGATIONS.md:124` — *Six decisions have accrued since the sweep recorded at 0.60.0*.
- *What is true instead:* ten, D201 to D210, the ceiling. The row's trigger, that the phase-6
  handover is marked closed, has not fired and stands: this sweep ran on the accrued count and the
  publication, not at the phase's close, so a sweep will be owed again when phase 6 closes if
  decisions land between.
- *How checked:* `accrued = 210 - 200` from the header and the record.
- *Proposed:* *Decisions have accrued since the sweep recorded at 0.60.0*, or the row records this
  sweep in its trigger column as the one that met the accrued clause. The second report proposes
  the other reading: close the row on this sweep as its evidence, since the obligation is a sweep
  and one has run. That loses the close trigger, which is the clause that has not fired, so this
  report keeps the row deferred; the owner decides.

**S-21 — Stale (by reading), and worth a decision rather than an edit. The README's `tools/` row
enumerates nine kinds of tool and the directory holds eleven.**

- *Where:* `README.md:23`.
- *What is true instead:* `tools/screen_controls.py` (added 2026-09-08) and
  `tools/make_review_worksheet.py` (2026-08-28) are not in the list. Both predate the last sweep,
  which read this row for enumerations and did not flag them, so the row may be meant as the tools
  a reader runs rather than every file. If so, it should say so.
- *How checked:* `ls tools/` against the row; `git log --diff-filter=A` for the two dates.
- *Proposed, if the row is meant as complete:* append *the screen that triages the control register
  for controls testing a copy of their rule, and the generator of the findings review worksheet*.

**S-22 — Wrong (by reading), low. The contract reading's banner says CI met the license
criterion.**

- *Where:* `sessions/PHASE-6-CONTRACT-READING.md:6` — *and D207 after CI met the license criterion*.
- *What is true instead:* CI ran the criterion and turned `main` red on it, reading a sibling checkout
  as an unlicensed tree; D207 corrected the check. *Met* reads as *satisfied*. Not worth a commit on
  its own; worth a word if the banner is touched.

**S-23 — Unbacked. The two figures O-12 reports from the held-out suite do not reconcile, and the
register says so.**

- *Where:* `HOLDOUT-OBLIGATIONS.md:618-622` — 184 passing with a harness checked out, 55 passing and
  130 skipped without one, *and those two figures do not reconcile*.
- *What would settle it:* a run of that suite by a session cleared to open the held-out repository.
  Recorded here so the next sweep does not rediscover it; nothing to act on from this side.
- *As reported, not verified here:* the second report, written from inside that repository, read
  its green CI run of 2026-09-22 as `184 passed, 1 skipped`, which makes 185 both ways and
  reconciles the two figures. If the owner takes that reading, O-12's sentence becomes *184 passing
  and 1 skipped with a harness checked out, 55 passing and 130 skipped without — 185 both ways, as
  that repository's CI run of 2026-09-22 shows; reported, since nothing here runs that suite*.

### Confirmed here from the second reading

Three findings the second report made that this sweep had not, each re-verified in this tree before
it was taken.

**S-24 — Stale (reproduced). Three handovers say *open* while every obligation they carry is
closed, and one of them is called closed by its successor.**

- *Where:* `sessions/HANDOVER-2026-09-12-phase-4-audit.md:3`,
  `sessions/HANDOVER-2026-09-15-cross-project-audit.md:3` and
  `sessions/HANDOVER-2026-09-08-control-connectivity.md:3`, each *Status: open*.
- *What is true instead:* the phase-4 audit handover's items are OB-24 to OB-36 and the cross-project
  handover's OB-37 to OB-43, and every one of those 20 rows is `closed` with evidence.
  `sessions/HANDOVER-2026-09-08-control-register.md:4` names the connectivity handover as the
  document it answers and calls it closed. The two other handovers still marked open, the control
  register's (OB-1 to OB-5, four open and one deferred) and the phase-3 audit's (OB-15, open), are
  rightly open. Nothing mechanized reads a remediation handover's status line: the close test reads
  phase handovers only.
- *How checked:* the status lines by grep; the register rows by grep on `OBLIGATIONS.md`, counted:
  13 closed of 13, 7 closed of 7.
- *Proposed:* *Status: closed*, with the date and *every item registered as OB-nn to OB-mm and closed
  there*, on the two audit handovers, and the connectivity handover's line brought level with what
  its successor says of it. Closing is the owner's call, since the lines were left open by the
  sessions that closed the rows.

**S-25 — Stale (by reading). The held-out labels are called *published* in seven places, and their
repository is private; one phase-1 bullet still calls them withheld.**

- *Where:* `specs/voice-agent-eval-harness.md:18` — *with plaintext published afterwards — so a reader
  can recompute the hash*; `:108` — *labels are published*; `:296` — *the published held-out labels*;
  `README.md:203` — *published after the rubric freeze*; `HOLDOUT-OBLIGATIONS.md:26`, `:660` and
  `:681` — *published on 2026-09-18*; and the snapshot note's second bullet at
  `tools/make_public_snapshot.py:127-129`. Beside them, `:42` — *Their labels are withheld*, a phase-1
  scope bullet the reveal of 2026-09-18 has overtaken.
- *What is true instead:* the labels are committed in plaintext to a repository nobody outside the
  owner's account can open. The previous sweep's S-5 weighed the word when all three repositories
  were private and let it stand as *published to the companion repository*; this project's own
  publication is what changed the reading, because a stranger who takes line 18 at its word goes
  looking for labels they cannot reach and a hash they cannot recompute. This is S-12's class one
  document wider.
- *How checked:* each site by grep; the visibility in section 1.
- *Proposed:* one qualifying clause per document rather than a word swept everywhere — *committed in
  plaintext to the companion repository afterwards, which is private today* at `:18` and `:108`;
  *sealed there and revealed after the rubric freeze; that repository is private today* at
  `README.md:203`; *revealed* for *published* in the register's three sentences; and *were withheld
  until phase 5 (revealed 2026-09-18)* at `:42`. `:296` is a closed phase's criterion and may stand as
  the record of what the gate asserts. Publishing the held-out repository retires the whole finding,
  and whether to is the owner's.

**S-26 — Stale (by reading), low. Two sentences tell a reader the freeze tag exists, and in the
published copy it does not.**

- *Where:* `specs/voice-agent-eval-harness.decisions.md:11172` — *the tag exists, and the labels were
  sealed at C1*; `HOLDOUT-OBLIGATIONS.md:26` — *that tag now exists*.
- *What is true instead:* `git tag -l` in the published repository prints `snapshot-rubric-pin-v1`
  and nothing else. The tag's object is published, as `freeze-proof/freeze-tag.txt`, and its id
  recomputes, but the name does not resolve. The 0.64.0 refresh sentence read the decision-record
  sentence as being about the labels and left it; in the copy a stranger reads, *here* is the
  snapshot. This sweep had accepted that refresh's reasoning and the second report did not; the
  second report is right for the public copy.
- *How checked:* the snapshot's tag list in section 1.
- *Proposed:* *the tag exists in the working history, and its object is published in
  `freeze-proof/`*, in both places.

---

## 3. What was checked and held

Read and checked, and true today; listed so that the next sweep can start past them.

- **The publication's shape as the record states it.** The snapshot's log is 2 commits and its tag
  is `snapshot-rubric-pin-v1` at the first of them; `rubric-frozen-v1` is absent there; the snapshot
  note and a README row are the additions and `src/harness/agreement.py` the rewrite; the note names
  the freeze `6d3a710` and its source `6843c5f`; `freeze-proof/objects/` holds 36 files in public as
  here. `comparative-judgment` is public with its history and dispatches to the working repository.
  The held-out repository is private. The `Not checked` block's repositories entry (`:11167`) says
  all of this and is the one place in the tree that does.
- **The freeze proof.** All four object ids, the rubric blob id and the four SHA-256 digests
  reproduce by hand under git's rule; the verifier reconstructs `src/` and computes `ce6ec2e5…`;
  the counts 34, 30, 5 and 6 reproduce from `git ls-tree` over `b441526…`; the freeze commit is dated
  2026-09-13 as the README says; the tag object reads as quoted.
- **Phase 6's status everywhere but the header's status line.** `tools/verify_phase6.py` ticks 6
  criteria and declares 6, matching the 12 `[P6]` criteria in the specification, the changelog's
  0.61.0 entry, `README.md:166`, the `emitted artifacts` section and OB-52 to OB-54; the phase table
  at `:356-359` and scope bullets 46 to 51 agree; the phase-6 handover is open and OB-51 to OB-59
  match it. `MEASURED_CONTRACT` pins phase 6 at 5 and 12, and `UNMAPPED_PHASES` is 1, 2, 3 and 7 as
  OB-16 states.
- **D201 to D210, each Rule line against the tree.** Every test each names exists (held by
  `test_every_test_named_in_a_rule_line_exists`); the counts they give reproduce: 14 tests in
  `tests/test_retell_adapter.py` with 11 mutations, 8 in `tests/test_inspector.py` with 7, 6 in
  `tests/test_instance_severity.py` with 5, the license control, the 4 plus 2 freeze-proof tests and
  the 2 reconstruction tests, all registered in the control register's newest sections. D203's 9
  roles, 5 unmapped, is what OB-58 says; D206's 43 declarations is what the data file holds and
  OB-57 says; D204's two criteria are the two the verifier declares.
- **The requirements and criteria sections against the code**, by grep where a clause names a
  mechanism: the two credential names and the minimum length in `harness.core.transport`; the
  supported-model set of two names; six `claude-sonnet-5` entries and one `claude-opus-5` in the
  rubric; the extraction default under `build/`; the `[P6]` adapter requirement's `--adapter retell`
  and the seam's refusal; the workflow running the type check, both linters, the suite, the scanner
  with `continue-on-error` and a red build when the sibling is absent, and the report diff.
- **Constraints.** The three runtime pins and `types-PyYAML` as the fourth dev pin, all `==`; the
  seven substitution classes; 35 taxonomy items and W1 to W35 with a GAP tally of 0; Part 3's
  `W2–W10, W19`.
- **The README's running section**, command by command, against the CLI's subcommands and the
  verifier list; the license table against `test_the_readme_names_a_license_for_every_top_level_path`;
  the three-repository table's first row; the `[skip ci]` rule.
- **The registers' tagged and computed figures**: 59 obligation rows, 12 discharged held-out
  obligations, 359 mutations — all held by test and all reproduced.
- **The `Not checked` block's other entries**, read against today: the corpus, gold set, rubric and
  severity entries describe the tree as it is; the held-out entry's sentence on the tag is about the
  labels, as the 0.64.0 refresh says; `subject_index.py` is still absent from the installed
  toolkit's folder, which this sweep looked for and did not find.
- **The build prompt's supersede banner** stands: phase 1 closed, counts frozen, live documents
  named.
- **Three claims the second report could only mark unbacked from the public copy, settled here.**
  `private/` holds `clean-room-sources.md` and `substitution-classes.md` and nothing else, which is
  what `specs/voice-agent-eval-harness.md:13` and `:119` say. `freeze-proof/objects/` is 533,369
  bytes on disk, D210's figure, and the directory 545,851, the README's *about half a megabyte*. And
  the README's *about ten minutes* for a full CI run is the working repository's measurement: its
  last three green runs took 12 min 53 s, 12 min 55 s and 13 min 48 s, so the figure is low by a
  third and still the right order; the public copy has never completed a run to measure.

---

## 4. What was read, and what was not

**Read whole:** `specs/voice-agent-eval-harness.md` from `metadata` to `emitted artifacts`, and the
changelog entries 0.60.0 to 0.65.0 for whether they describe what landed; D201 to D210 in full, the
`Not checked` block and `Document status` in `specs/voice-agent-eval-harness.decisions.md`;
`README.md`; `OBLIGATIONS.md`; `freeze-proof/README.md`; `tools/make_public_snapshot.py` including
`SNAPSHOT_NOTE`; `tools/verify_phase6.py`; `sessions/PHASE-6-CONTRACT-READING.md`;
`.github/workflows/checks.yml`; `pyproject.toml`; the first 1,200 lines of
`tests/test_document_counts.py` and, by grep, its remaining test names, `MEASURED_CONTRACT`, the
tagged-document list, the secret and close guards.

**Read in part:** `HOLDOUT-OBLIGATIONS.md` — its head, O-3, O-9 to O-12, *Standing* and
*Discharged*; not the bodies of O-1, O-2 and O-4 to O-8, which are discharged records.
`CONTROL-REGISTER.md` — lines 1 to 137 and 960 to the end; not the middle, whose rows are held by
`test_every_registered_control_exists` and re-derived by the gate. The opening lines of every file
under `sessions/`, for banners. `specs/voice-agent-eval-harness.build-prompt.md` — the banner only.
`specs/event-model.md` — the status line and section headings. `specs/taxonomy-coverage.md` — the
tally and Part 3's heading. `src/harness/agreement.py` — the pins and `check_held_out_labels`;
`src/harness/core/transport.py`, `src/harness/core/rubric.py` and `src/harness/extract.py` by grep;
`tests/test_agreement.py:40-95`; `tests/test_freeze_proof.py` and `tests/test_public_snapshot.py` by
their test names.

**Not read:** the decision record before D201; the changelog before 0.60.0; the bodies of the
session documents other than the contract reading and the last sweep's first 60 lines and headings;
`specs/taxonomy-scenario-map.md`, `specs/transcript-format.md`, `specs/error-type-sweep.md`; the
corpus, the findings, the rubric's text, the prompt template; the code beyond the greps above; the
tests beyond the names cited. **The held-out repository was not opened** — its visibility was read
from the account listing and nothing else of it. `comparative-judgment`'s content was not read
beyond its workflow's dispatch lines and three commit subjects.

**Outside the tree, all read-only:** the GitHub API for the visibility, ids and dates of the four
repositories under `hmbseaotter`; the snapshot's commits, tags, top-level tree, its snapshot note,
its README at lines 39, 222 and 278, its `src/harness/agreement.py` at lines 47 and 54, and its
`objects/` count; the CI run lists of the working repository, the snapshot and
`comparative-judgment`, and the failed-step logs of the snapshot's five runs; the secret names of
those three repositories; the sibling checkout of `comparative-judgment` beside this root, for the
interface scanner; and the locally installed toolkit's `specify` folder, for `subject_index.py`.

**The second report.** After the findings above were written, a report of this same sweep written
the same day by a session working inside the held-out repository, and kept outside this
repository, was read once as a reference. It names no held-out call, finding or label, and it does
not enter this tree: its file name is this one's, and its prose names the snapshot note by a file
name that does not resolve here, which the identifier inventory refuses. What it found that this
sweep had missed was re-verified here before it was taken (S-24 to S-26, and a site under S-10);
what it could read from inside that repository and this sweep cannot is recorded under S-6 and
S-23 as reported. Where the two disagree — the header's status line (S-9), OB-59's disposition
(S-20) and the *Artifacts land in* line (S-7) — this report says so at the finding.

---

## 5. What the sweep's changelog entry should say it read

Every section from `metadata` to `emitted artifacts` read against the tree at `9a22427` and against
GitHub on 2026-09-22 by a session that built none of it, with the `Not checked` block, the README,
both obligation registers, the control register's counts and newest sections, the freeze proof's
README, the snapshot note's template, the phase-6 contract reading and the tops of every session
document beside it, and the changelog from 0.60.0 for whether each entry describes what landed; the
report is `sessions/SWEEP-2026-09-22-publication.md`, whose section 4 says what was not read and
what a second reading of the same day from the held-out side contributed. It was the first sweep
after the project was published, and section 6 of the report says what the unswept publication
cost.

---

## 6. Whether the publication going out unswept cost anything

It did, in three kinds, and none of them is the kind the *before publishing* clause was written to
catch.

**What it did not cost.** Nothing private went out: the snapshot tool's scan held, the frozen blobs
were scanned before D210 with the scan proved able to fire, and this sweep found no absolute path
or private name in what it read of the public tree. The corpus, the findings, the severity file, the
rubric, the run log and the report are byte for byte what this tree holds, and the freeze proof
verifies in public exactly as it does here. The evidence is intact.

**What it cost in front of strangers.** The published README says all three repositories are
private, that this repository holds a token it does not hold, and that `comparative-judgment`
dispatches to a repository it no longer names (S-2, S-3, S-4). The specification's header tells the
same reader the project is not yet public (S-7). The freeze proof's README, the document written
for exactly this reader, labels its first link public when it is private, prints a recipe that fails
as written, and gives a commit count that is not the count (S-12, S-13, S-14); the specification,
the README and the register call labels *published* that sit in that private repository (S-25).
The snapshot note promises status banners that a third of the session documents do not have, and
one spent brief still tells a stranger to open phase 6 from a commit they cannot reach (S-17). Each
of these is a
sentence a careful stranger can check in a minute and find wrong, in a project whose thesis is that
a document must not drift from the artifact it describes.

**What it cost in the mechanism.** The public repository's CI has never passed, five builds running,
and the 14 steps that make this project's claims checkable have never executed there (S-1). That
is not a wrong sentence; it is the badge every reader sees first, and it is red for a reason that
has nothing to do with the code. And the pin the snapshot rewrites to make one test pass makes two
commands refuse the labels they exist to score (S-16), so the one measurement the README calls
recomputable is recomputable only from the private repository. Neither would have been caught by a
sweep of the specification alone; both were caught by reading the publication as a reader would,
which is the reading the clause asks for and nobody made.

**Why the clause could not have been mechanized, and what could be.** The flip is an event outside
the tree, as the header says. What is inside the tree is the tool that builds the snapshot, and it
can refuse to build while the header's marker is behind the record, the way
`test_a_closed_phase_handover_requires_the_sweep_marker_to_have_reached_it` refuses a close. That is
a proposal, not a finding: it would have turned the five builds into one refusal, and the owner
decides whether a publication should be gated the way a close is.

---

## 7. Whether the marker may move

**It may move to the version that applies this report**, provided that version's changelog entry
carries `**Swept:**` and the sentence in section 5, and provided every decision that version
records past D210 is one this report's findings produced — S-10's rewording of a closed phase's
criteria and S-16's choice of mechanism are the two that look like decisions. A decision on some
other matter recorded in the same version would be one this sweep did not read, and the marker
should then stop at the last decision it did. The accrued count returns to 0 or to the number of
such decisions, and OB-59's trigger stands for phase 6's close.
