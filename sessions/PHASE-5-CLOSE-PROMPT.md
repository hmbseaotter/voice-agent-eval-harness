# Session prompt — apply the sweep's findings, record the sweep, and close phase 5

> **SPENT — 2026-09-20.** The close ran: the sweep's findings were applied from
> `sessions/SWEEP-2026-09-19-phase-5.md`, the sweep was recorded at specification 0.60.0
> and phase 5 closed (D194, D199). Kept as a record, not as a brief to paste.

*Paste the section below into the session that worked the phase-5 audit's remediation (D194 to
D198), which the sweep's brief names as the one that applies its findings. That session runs on
**Claude Opus 5**; keep the effort it already runs at. If its context is too long to carry another
chain, a fresh session on Claude Opus 5 at effort **xhigh** can take this instead: everything it
needs is in the repository.*

*Why that session and not another model: the blind spot a different model exists to avoid is
re-reading one's own prose for staleness, and the sweep was that reading, done on Claude Fable 5.1.
What is left is applying corrections across every interlock this repository has — the version
chain, the decision record, the registers, the control gate — which that session crossed five times
on 2026-09-19. What guards the other direction is written into the prompt: each finding is
reproduced before it is acted on, and every fork goes to the owner.*

*State to start from: a clean checkout of `main` at `d894f72` or later, level with `origin/main`. No
other session should touch the harness tree while this one runs a chain.*

---

You are applying the findings of the specification sweep, recording that sweep in the
specification, and closing phase 5 of the voice-agent evaluation harness. Make the edits; this is
not a request for a second review.

## What you are working from

`sessions/SWEEP-2026-09-19-phase-5.md`, written at `63023f9` by a session on another model that
built none of phase 5. Read all of it before you change anything, its banner and section 4
included. It carries 27 findings, S-1 to S-27: 9 Wrong, 14 Stale, 3 Unbacked, and one, S-27, that
lists four statements true today and false the moment the phase closes. Each gives the statement,
where it is, what is true instead, how it was checked and a proposed wording.

Three things about it to hold on to:

- **Its line numbers are as of `63023f9`.** Once your edits begin they drift, so find each statement
  by the words the finding quotes.
- **Its proposed wordings are proposals.** You wrote several of the sentences they correct and you
  know the documents' voice; keep the correction's substance and word it as the document would.
- **Its body is a record and its banner is the status.** Record what you did with each finding in
  the banner, as the audit reports' banners do, and leave the body as written (D53).

## Reproduce before you act

Of the phase-2 audit's 17 findings 3 did not hold, and of the 2026-08-29 audit's 44, 3 did not. So
re-run each finding's check, or re-read the lines a *by reading* finding cites, before acting on
it. A finding that does not hold is recorded in the banner with what you ran and what it printed;
it is not skipped quietly and it is not applied anyway.

Run the fast document checks once before you start, so a failure you meet later is not inherited:

```bash
uv run pytest -q tests/test_document_counts.py tests/test_contract_coverage.py tests/test_obligations.py tests/test_phase3_acceptance.py tests/test_findings_evidence.py
uv run python tools/statement_inventory.py
uv run python tools/check_holdout_absence.py
```

One thing the sweep met that you will meet too: a phase verifier given `--junit
build/phase1-junit.xml` re-runs the whole suite whenever any file in the tree is newer than that
report, and the sweep's report and this brief both are. A verifier run of fourteen minutes or more
is that, not a hang.

## The order, which is part of the mechanism

**1. S-1 and S-2 first, because they decide whether the close is tested at all.** As the tree
stands the reveal handover can be marked closed with
`tests/test_document_counts.py::test_a_closed_phase_handover_requires_the_sweep_marker_to_have_reached_it`
green and no sweep entry written, by two independent routes: the test's pattern does not match that
handover's status line in the form it is written in, and the handover names no decision past D193,
where the marker already stands. Before you rely on that test for the close, make it produce a
positive: in a scratch copy outside the repository, close the handover in the form the test reads,
with D194 to D198 named in it and the marker unmoved, and see the test go red. A null from an
instrument nobody has seen fire is the shape this project keeps finding.

**2. Put the forks to the owner before editing what they decide.** They are listed below. Batch the
independent ones into one selectable question each, recommendation first.

**3. Apply the corrections**, smallest unit of separate concern per commit: code and test changes
apart from prose, and the specification's version chain kept whole within a commit.

**4. Write the sweep's changelog entry last among the versions, and move the marker to it.** Every
decision this work produces lands before that entry, so the sweep's version is the newest and the
marker names the highest decision.

**5. Close the handover last of all**, in a commit of its own, once everything above is green.

## The forks that are the owner's

Ask each through a selectable question. The recommendation given here is the sweep's, stated so
you can put it first; the decision is not yours or the sweep's.

| finding | the fork | the sweep's recommendation |
| --- | --- | --- |
| S-1 | Close the handover in the form the test reads and leave the test alone, or also widen the test's pattern to both forms with a planted case and a control | Both. The form alone repairs this close and leaves the next handover written the other way to the same blind test |
| S-3 | `Status: IN-BUILD`, or keep `DRAFT` and have the line say why | `IN-BUILD`, naming which phases are built |
| S-4 | Reword `Produced by` to say the toolkit's commit is unknown and what `f72b756` is, or leave the line and record the fact in a decision | Reword; the line's one job is to identify a toolkit generation and it identifies something else |
| S-11 | Which phase owns the design document | Phase 6, beside the docs routing that phase 1 already deferred there, with the present-tense sentences about it made future |
| S-12 | A question of fact: where the build log is, or whether D10's option (B) was carried out | None; only the owner knows. The specification then says what is true |
| S-13 | How two records written on 2026-09-19 are corrected | An appended note under D198, in the form `7540163` used for D192, and the sweep's own changelog entry saying that 0.59.0's "a week later" is a day; neither record edited in place |
| S-23 | Whether D83's reach statement was made beside the held-out figures | If it was not, an owed item in the reveal handover before it closes, which the harvest in `tests/test_obligations.py` then requires as a register row, and the tagged row count moves with it |
| S-24 | The license for `runs/` and `snapshots/`, which the README's table omits | None; assigning a license is the owner's |
| S-26 | A sentence saying the byte-identical comparison is made with `--out`, a renderer change, or nothing | The sentence. A renderer change is code and is not worth holding the close for |

The owner confirmed during the sweep, on 2026-09-19, that all three repositories are private now
and become public when the three are done. So S-5 is a wording correction and not a fork.

## The corrections to apply once reproduced

S-5 to S-10, S-14 to S-22, and the enumerations in S-24 and S-25. Four notes on them:

- **Live text is edited; records are annotated.** `prior decisions`, `assumptions`, the scope
  bullets, the README and the registers' prose describe the project now and are corrected in place.
  A decision's text and a changelog entry are records: a correction to one is an appended note
  that says so (D53).
- **The `Not checked` block has its own rule**, which you know: an entry describing a state the
  project has left is struck or moved and says what replaced it, and the block's refresh sentence
  for this version says which entries moved. This time seven do.
- **Where the sweep proposes de-quantifying (S-7, S-18, S-19), that is D74's rule applied**: a
  figure nothing here can hold goes, and one a test can hold gets a tag. Prefer that to re-pinning
  a number that went stale within a day of its last refresh.
- **S-25 touches `.github/workflows/checks.yml`**, a comment only, but a push carrying it is not
  prose-only.

## Statements that change with the close

S-27 lists four sentences that call phase 5 open. Prefer wording that is true on both sides of the
close, for instance that the phase-5 verifier *was written while its phase was open* (D176), and
apply it with the other corrections. The closing commit is then the handover's status line and the
register rows alone, and nothing in the specification has to change after its swept version.

## Recording the sweep

The sweep is recorded as the newest version's changelog entry, marked `**Swept:**`, saying what was
read and naming the report. Section 5 of the report drafts that sentence; adjust it to what you
actually applied. The marker then moves to that version and to the highest decision recorded. As of
`d894f72` the record ends at D198 and the specification stands at 0.59.0, so the next decision and
the next version follow those; check both before relying on them, and name no decision in prose
before it is recorded, which the statement inventory refuses. Whether the sweep is its own decision, as D159 was for phase 4's, and whether any fork above
needs one, is for you to propose and the owner to settle.

The tests that hold this, all in `tests/test_document_counts.py`:
`test_the_sweep_marker_names_a_changelog_entry_that_records_a_sweep`,
`test_the_spec_version_and_the_last_sweep_agree_with_the_changelog`,
`test_a_swept_marker_is_evidenced_by_the_changelog` and
`test_the_sweep_trigger_is_a_mechanism_and_not_only_a_sentence`, with the version chain you have
walked five times: the header, the changelog, the `Not checked` heading and its refresh sentence,
and the decision record's `Document status`.

## The close

Before its status line moves, `sessions/HANDOVER-2026-09-18-held-out-reveal.md` records what has
happened since it was written: the independent audit of 2026-09-19 and its remediation, D194 to
D198, this sweep and whatever decisions applying it produced (S-2, S-21). Then, in one commit:

- the status line, written `**Status: closed**` with the date and the commit span, the form phases
  3 and 4 use;
- OB-46 closed with its evidence, and any row the forks above opened in place;
- OB-47's trigger has then fired, and it is read by a person: tell the owner so in your closing
  message.

**Do not open phase 6.** Its contract reading, its brief and OB-49's question are owed after the
close and are not this session's work.

## What to hand back

A closing message the owner can read cold: what each of the 27 findings came to — applied,
declined by the owner, or did not hold — in one line apiece; the versions and decisions this
produced; the state of the checks; and what is owed next, which is at least OB-47, OB-49 and OB-7,
plus anything S-12 or S-23 left open.

## Rules

- **Do exactly this work.** No refactor, no neighboring sentence improved on the way past, no
  finding of your own applied without asking. Something you notice that the sweep missed is worth
  raising with the owner as a proposal, after the requested work.
- **Never spend.** Nothing here needs a model call; if anything would issue one, stop.
- **Never tag, and touch no other repository.** Nothing here needs the held-out repository opened,
  and you do no rubric work: `rubric.yaml` and the prompt template stay as `rubric-frozen-v1` names
  them. No held-out content enters this tree.
- **The owner decides every fork**, through a selectable question with your recommendation first.
  End every substantive turn with an **Assumptions** list.
- **Commits:** show each message verbatim and ask; stage files by name; no attribution lines; fetch
  before committing. **Do not push unless asked.** A push whose every commit is prose may carry
  `[skip ci]` under the rule the README's CI section states, with the fast document checks run
  first; a push carrying a test, a control, the workflow file or any project data runs CI.
- Write files with LF endings. US spelling is enforced by test. Worded numbers are live claims read
  by count guards; digits are historical statements.
- **Before you report the work done**, re-run the fast document checks, the statement inventory,
  the absence check and the phase-5 verifier, and the control gate if you touched a test or a
  control, and say what each printed.
