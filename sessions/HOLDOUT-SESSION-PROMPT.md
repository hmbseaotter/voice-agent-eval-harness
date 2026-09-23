> **SPENT — 2026-09-06.** The session this prompt was written for ran
> (`f43fee59-…`, and its follow-on `71a48c77-…`), read the held-out set under
> clearance, and discharged O-1, O-2 and O-3. **Do not paste this to start a new
> session**: it names a five-transcript set that has since grown, a held-out
> `HEAD` that has moved, and an absence of `tests/` and `pyproject.toml` that is
> no longer true. It is kept as the record of how a session was cleared to read
> the held-out set and what it was allowed to bring back — which is the part
> worth reusing, and which `HOLDOUT-REPAIR-BRIEF.md` states as rules.
>
> The live documents are `HOLDOUT-OBLIGATIONS.md` (standing) and `HELDOUT_SET`
> (the declaration every check reads).

# Session prompt — discharge the held-out obligations

*Paste this as the first message of a session cleared to read the held-out transcripts.
`HOLDOUT-REPAIR-BRIEF.md` anticipated such a session and never gave it a starting point; this is
that starting point. The brief governs the work; this orients the session that does it.*

---

You are cleared to read the held-out transcripts. That permission is what makes this session
possible and it is also what disqualifies it from everything else, so read both halves of this
before starting.

## What you may do, and what you must not

**You MAY read** `voice-agent-eval-harness-holdout/transcripts/CALL-13.txt` … `CALL-17.txt`, and
edit them. That is the point of this session. `HOLDOUT-REPAIR-BRIEF.md` step 1 tells you to stop
unless you are cleared — you are; this prompt is the clearance.

**You MUST NOT, having read them:**

1. **Do any rubric, gold-set, or design-corpus work.** Once you have read held-out content you are
   contaminated for the measurement this project exists to produce. If a task drifts toward the
   rubric or `corpus/`, stop and say so rather than continuing.
2. **Copy held-out content into the main repository** — not into a file, a scratch note, a test
   fixture, a commit message, or a decision entry. This is the sharpest risk in the handoff,
   because anything you write there is readable by every future uncontaminated session.
3. **Write, infer, or sketch labels.** Labels are a phase-5 artifact and must not exist until after
   the `rubric-frozen-v1` tag, with their commit citing the main repository's freeze SHA (D21).

**The line you are allowed to write across is counts and rules, never content.** From the brief,
and it is exact: *"four unsourced arguments across two transcripts, repaired with `find_performance`
lookups"* is right. *"`CALL-15` was the bad one"* is more than the main repository may carry.

## Where things are

```
main     <the harness checkout>
holdout  <the held-out checkout, beside it>
```

Both are private GitHub repositories under `hmbseaotter`, which matches the authenticated `gh` user,
so the push guardrail is satisfied on both. The owner approves every commit message before it lands.

## Read these first, in this order

1. `HOLDOUT-REPAIR-BRIEF.md` (main) — the conforming shapes, the renumbering hazard, what to
   re-check afterwards. It was written by a session that could **not** read the five, so it names
   rules rather than defects. It governs, and it was brought current on 2026-09-06.
2. `HOLDOUT-OBLIGATIONS.md` (main) — the three obligations and how a discharge is recorded.
3. `specs/transcript-format.md` (v2.1) and `specs/event-model.md` § 3.5 (main) — these two govern
   the shapes the brief summarizes.

## The three obligations, in one line each

**O-1 — every identifier in a tool call must be resolved within the call.** Walk each transcript in
order; for every `TOOL_CALL`, check each argument value traces to something *earlier* — context, the
call record, prior speech, an earlier event body, or arithmetic over context values. A value that
first appears in the result of the call that used it is **not** sourced. One declared exception:
`fetch_policy(document=…)`. Repair by giving the agent the lookup that produces the value, never by
deleting the argument or inventing a context entry.

**O-2 — policy retrieval returns a whole document.** `fetch_policy` takes a document and no clause;
the result names the document and its clause count; a `POLICY` event records the clause the agent
*applied*. Verified counts: `refund.v1` 14, `transfer.v1` 10, `exchange.v1` 10. **If none of the five
calls `fetch_policy` at all, that is a complete discharge by inspection** — tick it and say so.

**O-3 — a decision, not a repair, and it is the owner's to make.** Either seed comparable instances
in the held-out set, or state in the published result which classes the held-out measurement does not
reach. Do not settle this yourself; put the choice to the owner. Leaving it unstated is the one
outcome the obligation rules out. Read the brief's caution on how O-3 is worded before you start:
most of what it asserts about the five has never been checked, and you are the first session that
can check it.

## What is already established, so you need not re-derive it

Metadata only — no session has read the content:

```
holdout HEAD    ee82c0b on main, working tree clean, last pushed 2026-08-30
tracked files   .github/workflows/checks.yml, .gitignore, LICENSE, README.md,
                transcripts/CALL-13.txt … CALL-17.txt
```

Note what is **not** there: no `tests/`, no `pyproject.toml`, no linter configuration. The brief asks
you to check whether that repository's tooling is current with the main one and to **port the checks
if it has no equivalent** — the file list says it has a CI workflow and nothing else, so expect to
port rather than to find. The two checks that matter most are
`tests/test_corpus_hygiene.py::test_no_tool_call_argument_appears_from_nowhere` and
`test_every_policy_retrieval_states_the_document_s_real_clause_count`.

## How to finish

In the **main** repository — safe to touch, it is metadata about the held-out set rather than
held-out content:

1. Tick each obligation in `HOLDOUT-OBLIGATIONS.md`: `**Discharged:** ☑ — session <id> , date
   <YYYY-MM-DD>`, with one line saying what was found **in counts**. Discharge by inspection is a
   real discharge; record it as one.
2. Open a decision entry in `specs/voice-agent-eval-harness.decisions.md` — numbering continues from
   **D83** — in the record's shape: fork, options considered, decision, why, consequences, rule. A change to
   the held-out set is a project decision.

In the **holdout** repository: the transcript edits and any checks you port, committed there.
