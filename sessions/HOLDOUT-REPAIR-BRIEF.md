> **SPENT for O-1 and O-2 — 2026-09-06.** Both were discharged (D83). This brief
> is kept because its *method* is the reusable part: it was written by a session
> that could not read the held-out set, for one that could, and it therefore
> names **rules and conforming shapes, never defects**. That constraint is what
> let the repair happen without the specifying session becoming contaminated,
> and it is the shape any future held-out brief should take.
>
> **Its counts are frozen at the moment of writing** and several are now wrong:
> the set is no longer five, the design set is no longer fourteen, and the
> statement that the five carry none of the vocabulary added since was
> falsified by the obligations register. Read it as a method, not as a
> description of the set today.

# Held-out repair brief — what O-1 and O-2 require of `CALL-13`…`CALL-17`

**Who this is for.** A session that **may read the held-out transcripts**. No session working on the
harness, the rubric, the gold set or the corpus may read them, so the repair has to happen somewhere
else, and that somewhere else needs instructions it can act on without asking questions back.

**Who wrote it, and what that means for how it reads.** A session that may **not** read them. So this
brief names **rules and conforming shapes**, never defects: it cannot tell you that `CALL-15` has a
bad `fetch_policy` call, only what a good one looks like and how to find the bad ones yourself.
Where a step's outcome is unknowable from here, it says so rather than guessing.

**Status — discharged, 2026-09-06.** ~~O-1, O-2 and O-3 are all **undischarged**.~~ All three are
now ticked in `HOLDOUT-OBLIGATIONS.md`, and the held-out set has been repaired and has grown to six.
What was found, in counts, is recorded there; the reasoning is D83 to D86 in the decision record.

**This document remains useful and is not retired.** Its instructions are spent, but the conforming
shapes, the renumbering hazard and the re-check list below govern *any* future edit to the held-out
set, and the next one will have no brief written for it. Read the sections that describe rules; treat
the sections that describe what is owed as history.

**Brought current 2026-09-06.** The O-3 section was written before D73 and described two new
calls, a 14:5 ratio and no escalation class. Corrected here rather than annotated, because this
document is instructions to act on rather than a record of what was believed — the decision
record is where the history lives.

---

## Why this matters more than a tidy-up

The two repairs are not cosmetic. The design corpus was changed so that **no tool-call argument
enters a call from nowhere the transcript records**, and a check now enforces it:
`tests/test_corpus_hygiene.py::test_no_tool_call_argument_appears_from_nowhere`.

That check globs `corpus/transcripts/`, which holds design calls only — so it has never run against
the held-out five. If they still carry the old conventions, then at phase 5 the harness will
evaluate them and the provenance defect will look like a **seeded** one. Judge-versus-human
agreement would then be measured on a set whose defects include artifacts of when it was written.
That is the failure mode the held-out set exists to avoid.

---

## Before you start

1. **Confirm your permission.** You must be a session explicitly cleared to read
   `voice-agent-eval-harness-holdout/transcripts/CALL-13.txt` … `CALL-17.txt`. If you are not, stop.
2. **Do not copy held-out content into the main repository**, not even into a scratch file, a commit
   message or a test fixture. `tools/check_holdout_absence.py` asserts the main working tree holds
   exactly the 14 declared design transcripts and 5 declared test fixtures and no others.
3. **Do not write, infer or sketch labels.** Labels are a phase-5 artifact and must not exist until
   after the `rubric-frozen-v1` tag, with their commit citing the main repository's freeze SHA (D21).
4. **Read `specs/transcript-format.md` (v2.1) and `specs/event-model.md` § 3.5 first.** The
   conforming shapes below are summaries of those two documents, which govern.

---

## O-1 — every identifier in a tool call must be resolved within the call

**The rule.** A value the agent passes to a tool must trace to one of:

- a **context** value present before the call began;
- a field of the **call record**;
- **prior caller or agent speech**;
- the **body of an earlier event**, including an earlier tool result;
- **arithmetic over context values**.

A value first appearing in the result of the very call that used it is **not** sourced — it was
asserted and then confirmed, which is exactly the shape being rejected.

**The one declared exception**, and it is deliberately a short list: `fetch_policy(document=…)`. A
document's *name* is part of the tool's contract the way the tool's own name is. What an agent cannot
know without reading the document is **which clause answers the question** — which is why the clause
argument was removed rather than excepted. If you find you want a second exception, that is a signal
the transcript should change instead.

**How to find them.** For each transcript, walk the events in order, and for every `TOOL_CALL`
collect its argument values. For each value, search only the events *before* it. The design-set audit
did this over all 80 tool-call arguments across 12 transcripts and found **13** unsourced.

**How to repair one.** Do not delete the argument and do not invent a context value for it. **Give
the agent the lookup that produces it.** The design-set example: `CALL-09` used `EV-44901` as an
exchange target at three events with no `find_performance` call and only `EV-44803` in context. The
repair inserted a `find_performance` call keyed on `event_title` and the requested date, whose result
supplies the id — so the agent now learns the value the way an agent would.

---

## O-2 — policy retrieval returns a whole document

**The old shape** — `fetch_policy(document=…, clause=…)` — could only be called correctly by an agent
that already knew where the answer was. The clause argument entered every call from nowhere.

**The conforming shape is three events:**

```
TOOL_CALL    fetch_policy(document="refund.v1")
TOOL_RESULT  -> retrieved successful=true :: refund.v1 returned; 14 clauses
POLICY       refund.v1 § 2.2 -> "<the clause text, verbatim>"
```

The `POLICY` event records **the clause the agent applied**, not one a tool was told to fetch. That
is what turns the corpus's weakest finding class — *nothing was retrieved* — into its strongest: *the
governing clause was returned and a different one was applied*.

**The clause counts, verified against `corpus/policies/` on 2026-09-01:**

| document | clauses |
|---|---|
| `refund.v1` | **14** |
| `transfer.v1` | **10** |
| `exchange.v1` | **10** |

The count in a result line is checkable, and in the main repository it is checked, by
`test_every_policy_retrieval_states_the_document_s_real_clause_count`. State the real number.

**`POLICY` events themselves need no change.** They already cite one clause and quote it, and clause
correspondence is compared after collapsing runs of whitespace, so re-wrapping is harmless.

**Discharge by inspection is a legitimate outcome.** Whether any held-out transcript calls
`fetch_policy` at all is **unknown from here, deliberately** — answering it would mean reading them.
If none does, tick O-2 and say so; that is a complete discharge, not a shortcut.

---

## O-3 — a decision, not a repair

The held-out five carry none of the vocabulary added since they were authored, and the five have
not been touched since. The error-type sweep added **35 findings** across two new calls, D70 added
12 further events inside CALL-12, and D73 added a third new call. D4's ratio of 12:5 became 14:5
at D68 and **15:5** at D73, with no growth on the held-out side.

**A caution on how the obligation is worded.** `HOLDOUT-OBLIGATIONS.md` says the five *"exercise
none of the 35 findings"*. That is trivially true of the literal findings and **unverified** for
the behavior classes behind them — it was written by a session that could not read the five, and
none has since. Absence follows from **authoring order** only where the vocabulary did not exist
yet: the escalation tokens below, and the context fields `billing_zip`, `internal_note`,
`venue_timezone`, `original_door_time`. Every other class is a claim about content. You are the
first session able to check, so report what is actually absent rather than inheriting the claim.

**The question to settle** is whether the held-out set should carry the classes added since — over-
disclosure to a non-account-holder, time and zone arithmetic, idempotency, retrieved-data injection,
authentication factor strength, AI-status disclosure, delivery state, and **escalation**.
`HOLDOUT-OBLIGATIONS.md` calls escalation *"the sharpest case in this entry"*, and it is the one
case that needs no inspection: CALL-20 (D73) introduced `disconnection_reason: transferred`,
`outcome_reason: escalated`, and the register names `transfer_to_specialist` and `escalated`, none
of which existed when the five were written. It is not a class they merely lack — it is vocabulary
they could not have used. Adding a held-out call is a
much heavier act than adding a design call, because the held-out set is what agreement is measured
against. **Record the decision either way**; leaving it unstated is the outcome to avoid.

---

## The renumbering hazard

**Inserting a call-and-result pair renumbers every event after it.** Both repairs insert events. So
after any edit, re-check in the held-out repository:

- every **event index** in the transcript body is sequential from 1 with no gaps;
- every **positional reference** anywhere in that repository still points where it says;
- timestamps remain **monotonic**, and the header's `duration_ms` still relates to the log the way it
  did before (if a mismatch was seeded there, it must stay seeded and stay the same size);
- **speech rate** for any turn you added or re-timed sits in the plausible band — the design corpus
  uses 110–185 wpm with a median pinned at 130–160;
- that repository's **CI workflow** still passes: it asserts the set is exactly `CALL-13`…`CALL-17`,
  that each parses clean, and that no labels-shaped file exists before the freeze.

If the held-out repository has no equivalent of the main repo's provenance and clause-count checks,
**port them**. A repair with no check behind it is the state that produced this brief.

---

## Recording the discharge

Edit `HOLDOUT-OBLIGATIONS.md` in the **main** repository — it is metadata about the held-out set, not
held-out content, so it is the right place and it is safe to touch:

```
**Discharged:** ☑ — session <identifier> , date <YYYY-MM-DD>
```

Add one line per obligation saying **what was actually found**, in counts rather than content: *"four
unsourced arguments across two transcripts, repaired with `find_performance` lookups"* is exactly
right. *"`CALL-15` was the bad one"* is more than the main repository should carry, and *"no
`fetch_policy` call exists in any of the five"* is fine and is a discharge by inspection.

Then open a decision entry in the main repository's record — numbering continues from **D83** — since
a change to the held-out set is a project decision and not a private edit.

---

## What this brief cannot tell you

- **Whether any of these defects is actually present.** All three obligations may turn out to be
  discharged by inspection. That would be a good outcome and should be recorded as one.
- **How many events each transcript has**, or what any of them contains. Not knowable from here.
- **Whether the held-out repository's tooling is current** with the main repository's. Check it;
  the phase-1 verifier notes that the companion repository had no tests, no CI and no linter until
  2026-08-29, so "it has a workflow" is recent rather than long-standing.
