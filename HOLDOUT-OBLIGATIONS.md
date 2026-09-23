# Held-out obligations — corpus convention changes that this repository cannot verify

**What this is.** A standing list of changes made to the design corpus's conventions that the
held-out set must be brought into line with, and that **no check in this repository can detect**.

**Why it exists.** `corpus/entities.md` states the gap in its own words: *"The held-out set is not in
this tree and this check does not reach it; keeping the two consistent is a manual step at authoring
time."* `tests/test_corpus_hygiene.py` and `tools/check_holdout_absence.py` both cover only what is
in this tree. A green suite here says nothing about any held-out transcript. **And a red build there
hides a divergence as well as a green one**: O-12 records a widening in this repository that the
other side did not notice for as long as its own gate was failing for an unrelated reason. **Stated as the set
rather than a range since 2026-09-06**, when `CALL-21` joined it — the sentence had enumerated the
members, which meant its claim quietly narrowed the moment the set grew.

**Why it is written before the work rather than after.** The moment an obligation is easiest to
forget is when the change that created it is finished and feels done. Each entry is added when the
convention changes, not when someone remembers.

**How an entry is discharged.** In a session that does no design work on this repository — the
handover's rule is that a fresh session is the only mitigation for contamination, and revising
held-out transcripts means reading them. Tick the entry, name the session, and state what was
changed. **Nothing here can confirm the tick; that is the point of recording it.**

**What is not at risk, and until when.** Revising a held-out transcript costs neither property (a)
nor property (b) only while no held-out label exists. None could exist before `rubric-frozen-v1`
(D21, D36); that tag now exists in the harness's working history, and its object is published in its `freeze-proof/` (D209); the labels were sealed at C1 on 2026-09-17 and revealed on
2026-09-18 (O-9), so that condition no longer holds: a revision now has to be weighed
against both properties, and what one would cost is a question for whoever proposes it. The risk this file addresses is only that the two sets
silently diverge — after which the rubric is designed against one convention and applied to
transcripts built on another, which is precisely the agreement measurement the project exists to
produce.

---

## Open

> **A repair brief exists.** `sessions/HOLDOUT-REPAIR-BRIEF.md` states the conforming shapes for O-1 and
> O-2, the verified clause counts, the renumbering hazard and what to re-check afterwards. It was
> written by a session that may **not** read the five, so it names rules rather than defects, and
> it is instructions rather than a discharge.
>
> **All three were discharged on 2026-09-06** by a cleared session — O-1 and O-2 by repair, stated in
> counts below, and O-3 by the decision it always asked for. Two pieces of work follow from O-3's
> decision and are owed elsewhere rather than here; the entry says which.
>
> **O-1 to O-3 are the three that brief covers. Entries from O-4 on were opened afterwards** and are
> not in it; each carries its own settling decision. Opening them is this file working as designed:
> closing a gap on the design side is what reveals the matching one on the other.
>
> **O-4 to O-6 were opened by the session that closed audit findings H-5 to H-8, and discharged by
> that same session the next day** — which the rule above forbids, and the exception is narrow enough
> to state. The bar exists because discharging normally means *revising* held-out transcripts, and
> revising them means reading them. These three were dischargeable by writing checks and re-targeting
> a redaction: the checks read the transcripts, and the session did not. The held-out suite was run
> with tracebacks suppressed, so a failure would have named a test rather than a call.

### O-1 — Every identifier used in a tool call must be resolved within the call

**Settled 2026-09-01.** The design corpus is being repaired so that no tool-call argument enters a
call from nowhere the transcript records. An audit of all 80 tool-call arguments then in the corpus, across the twelve
design transcripts found thirteen unsourced; `CALL-09` used `EV-44901` as an exchange target at
events 11, 13 and 17 with no `find_performance` call and only `EV-44803` in context.

**The rule:** an identifier appearing in a tool call must trace to a context value, the call record,
prior caller or agent speech, or a prior tool result. Where it does not, the agent makes the lookup
that produces it — for a performance, `find_performance` keyed on `event_title` and the requested
date, whose result supplies the id.

**What the held-out set must satisfy:** the same rule, in every held-out transcript. Inserting a
call-and-result pair renumbers every event after it, so the transcripts' own indices, any positional
reference, and that repository's CI all need re-checking after the edit.

**Discharged:** ☑ — session `f43fee59-3162-4cf8-85d7-6aba414372ed` , date 2026-09-06

**Twenty-six non-excepted tool-call arguments across the five; four unsourced, in four transcripts.**
Three were the `clause` argument and left with the O-2 repair. The fourth was a bare integer on a
write, repaired by re-keying that call onto the booking already in its context — which is also the
convention every other write in the design set follows, so the repair moved the held-out set toward
the canon rather than away from it. **No exception was added.** Twenty-three arguments now resolve and
none is unsourced. **No event was inserted, in any transcript, so nothing renumbered**; event counts
and every timestamp are unchanged, and all five still parse with a zero unparsed-line count.

**A limit of the check, found while repairing and worth stating here because it applies to this
repository too:** no bare integer of one or two characters can ever pass it. The speech and
prior-event paths require three characters and the arithmetic path sums context values rather than
subtracting them, so a small-integer argument has no honest repair available — only a coincidental
match against an unrelated context number, which is the false source the length floor exists to
prevent. The repair is to change what the argument is. Recorded as D83.

### O-2 — Policy retrieval returns a whole document

**Settled 2026-09-01.** `fetch_policy` no longer takes a clause. It takes a document and returns it
whole, and the `POLICY` event records **the clause the agent applied** rather than the clause a tool
was told to fetch. The old signature could only be called correctly by an agent that already knew
where the answer was, so the clause argument entered every call from nowhere. Recorded in
`specs/event-model.md` § 3.5.

**The conforming shape is now three events:**

```
TOOL_CALL    fetch_policy(document="refund.v1")
TOOL_RESULT  -> retrieved successful=true :: refund.v1 returned; 14 clauses
POLICY       refund.v1 § 2.2 -> "<the clause text, verbatim>"
```

**What the held-out set must satisfy:** every `fetch_policy` call in `CALL-13`…`CALL-17` drops its
clause argument, and the result line names the document and its clause count. The count is checkable
against `corpus/policies/` — refund.v1 has 14 clauses, transfer.v1 and exchange.v1 have 10 each.
`POLICY` events themselves need no change: they already cite one clause and quote it, and clause
correspondence under whitespace normalization is unaffected.

**Whether any held-out transcript calls `fetch_policy` at all is unknown here, and deliberately so** —
answering it means reading them. If none does, this entry is discharged by inspection and should be
ticked saying so.

**Discharged:** ☑ — session `f43fee59-3162-4cf8-85d7-6aba414372ed` , date 2026-09-06

**Three of the five carried the retired two-argument signature; the other two make no policy retrieval
at all.** All three were repaired to document-only calls whose results name the document and state its
real clause count. The counts were re-derived from `corpus/policies/` rather than taken from the brief,
and agree with it: 14, 10, 10. Each repair fitted the existing two lines, so **no event was inserted
and nothing renumbered.**

**Two things were checked that this entry assumed rather than asserted**, and both hold: all three
cited clauses exist in their documents, and all three `POLICY` quotations equal their clause verbatim
under whitespace normalization. That mattered more after the repair than before — the old shape claimed
only that a clause came back, while the new one claims the whole document did, which is what makes
"the governing clause was returned and a different one was applied" assertable.

**The clause-count check alone would not have caught this**, and that is worth recording: the retired
shape's result states no count, so there was no number for the check to find wrong. It would have
passed on all five while three carried the defect it exists for. The port therefore adds a companion
that fails on the signature itself.

### O-3 — The design set now exercises classes the held-out set cannot

**Settled 2026-09-01 (D66, D68), and restated twice.** The first version of this entry was written
when this was nine findings; the error-type sweep took it to thirty-five across two new calls; and
D73 added a third, CALL-20, with an escalation class of its own.

A systematic pass over catalogd voice-agent failure modes (see `specs/error-type-sweep.md`) added
**thirty-five** findings — twenty-three to existing calls, twelve in two entirely new design
transcripts (and, at D70, twelve further events inside CALL-12 carrying six declared true
negatives, which the held-out five cannot exercise either):

- **CALL-18** — a caller who is not the account holder, helped too much. No verification at all, the
  bypass reasoning spoken aloud on a recorded line, an operator-facing field read out, card brand,
  last four and billing ZIP volunteered, delivery redirected to an address the account has never
  seen, a write gated in one flow and ungated here, and the whole call filed as abandoned.
- **CALL-19** — a rescheduled event, a UTC door time read out as a local one a day late, an
  impossible reschedule timestamp, and a policy clause anchored to a field the booking does not
  carry.
- **CALL-20** (D73, after the sweep) — a dispute no policy covers, escalated to a human and handed
  over empty. It brings an escalation class the held-out five have no instance of at all:
  `disconnection_reason: transferred`, `outcome_reason: escalated`, and two register names
  (`transfer_to_specialist`, `escalated`) that did not exist when the five were authored. **This
  is the sharpest case in this entry**, because it is not a defect class the five merely lack —
  it is vocabulary they could not have used.

Plus, in existing calls: retry against a hard refusal, deduplication on a timed-out write, injection
arriving in retrieved data, authentication factor strength, AI-status disclosure, delivery state
versus API acceptance, termination etiquette, and two reason-code defects.

**This is coverage, not conformance.** Nothing here makes a held-out transcript malformed — the five
remain valid under the format whatever they contain. What is at stake is that the design set now
teaches a judge to look for classes the held-out set has no instance of, so the agreement figure is
measured on a narrower surface than the judge was built for, and nothing in either repository says
so.

**The ratio also changed.** D4's twelve-to-five became fourteen-to-five (D68) and then
**fifteen-to-five** (D73), and ~~the five carry none of the classes added since~~ — **corrected
2026-09-06, by the first session that could check.** That claim was written by sessions that could not
read the five and it is wrong, not merely unverified. Of the eight classes: **five are absent**
(escalation, AI-status disclosure, retrieved-data injection, idempotency and deduplication,
over-disclosure to a non-account-holder); **one is absent in part** — no zone arithmetic anywhere, no
local-time conversion, while date arithmetic against a stated window appears in two calls; **one
exists only as a uniform convention**, since all five verify identically, so nothing isolates
authentication factor strength as a variable; and **one is genuinely present** — delivery state versus
API acceptance. The absences are confirmed mechanically where the vocabulary allows: no `transferred`,
no `escalated`, no `transfer_to_specialist`, all five `resolved`.

**What is owed: a decision, not necessarily an edit.** Either seed comparable instances in the
held-out set — which means authoring, in a session that can read it — or state in the published
result which classes the held-out measurement does not reach. Both are defensible. Leaving it
undecided is not, because the asymmetry is invisible from either repository and will not surface on
its own.

**Four new context fields** were declared for CALL-18 and CALL-19 and do not appear in the held-out
set: `billing_zip`, `internal_note`, `venue_timezone`, `original_door_time`. Held-out transcripts
need not carry them; the entity register's used-implies-declared direction is what matters and it
does not reach that tree. **Confirmed absent from all five, 2026-09-06.**

**Discharged:** ☑ — session `f43fee59-3162-4cf8-85d7-6aba414372ed` , date 2026-09-06

**Decided, which is what this entry asked for: both, scoped.** State the reach in the published
result for every class above, **and** seed one held-out call for escalation — the only class the five
could not have expressed at all, since its vocabulary post-dates them. Recorded as **D83**, with the
reasoning: seeding's cost is a near-twin of the design set's escalation call, which would inflate
agreement, and that cost is remediable by controlling what the authoring session can see.

**What the discharge does not do is the work.** The decision is made and the obligation is closed;
two things follow from it and are owed elsewhere.

**The escalation call — done, 2026-09-06.** Authored by a different model from
`holdout-authoring-packet/`, which held the format spec, the event model, the entity canon and the
existing transcripts with every design-call reference redacted behind a visible marker and a leak scan
over the result, and which supplied **no scenario**. The resemblance comparison afterwards found
difference on every axis free to vary and agreement only on the two fields the assignment fixed. The
held-out set is now six, and its workflow asserts that. Recorded as **D86**.

**The reach statement — still owed**, in the published result at phase 5. Seeding closed the
escalation gap and nothing else: every other class enumerated above is still absent, and the ratio is
now sixteen-to-six. **Adding one call did not retire that sentence**, and this is the point at which it
would be easiest to believe it had.

### O-4 — Event identifiers are one namespace across both corpora, and neither side can see the other's

**Settled 2026-09-06 (D87).** `EV-88011` held three `door_time` values across three design calls. D87
repaired it: CALL-18 realigned to the canonical `2027-03-19T19:00:00Z`, and CALL-02's later performance
given a newly allocated id, **`EV-88214`**.

**The convention this creates.** One `event_id` names one performance — one title *and* one door time
— and where two calls name the same id they must agree about both. That is now checked here by
`test_one_event_id_means_one_event` and in the held-out repository by its own port of the same rule.
**Both checks compare a set to itself.** Neither looks across the boundary, so the namespace they share
is the one thing neither can hold.

**Why it is a real risk rather than a tidy one.** D85 repaired the held-out side by allocating a *new*
event id there, and this repository does not know its value. D87 allocates `EV-88214` here, and that
repository does not know this one. Two corpora drawing identifiers from one `EV-#####` space with
nothing comparing them will collide silently, and a collision is worse than a duplicate: two calls
would name one event and disagree about its door time, which is exactly the defect D85 and D87 each
spent an entry repairing on their own side.

**What the held-out set must satisfy:**

1. No held-out transcript names an event id that appears in `corpus/transcripts/` **unless** it agrees
   about `event_title` and `door_time`. `EV-88011` is now unambiguously
   `2027-03-19T19:00:00Z`; if a held-out call still names it, that is the value it must carry.
2. No held-out transcript uses `EV-88214`, allocated here on 2026-09-06.
3. Whatever id D85 allocated on the held-out side collides with nothing in this tree.

**This one can be made mechanical, in the only place that can see both sides.** The held-out workflow
already checks this repository out at `.harness/`. A step there can read every `event_id :=` from its
own transcripts and from `.harness/corpus/transcripts/`, and fail on an id that appears in both with a
differing event-scoped field — the same shape the audit proposed for `HELDOUT_SET`, and the same
argument: the check belongs where both sides are visible, which is never here. Until it exists this
entry is a manual step at authoring time, like everything above it.

**Discharged:** ☑ — session `43b504d3-1197-4a88-8b5f-e42df87c90fd`, date 2026-09-07

**Made mechanical rather than checked by hand**, which is what this entry asked for. The held-out
suite gains `test_no_event_id_names_two_different_events_across_the_two_corpora`: it reads the
event-scoped context fields from both trees — its own, and the harness at `.harness/` — and fails on
an id present in both that disagrees about `event_title` or `door_time`. **It passes**, so the two
corpora name no event in common and nothing collided.

**A disjoint id set is the pass, and there is deliberately no comparison floor.** The expected state
is that the two sets share nothing, so a floor would fail on the correct outcome; what is asserted
instead is that both sides were read, because the failure worth guarding is a check that loaded
nothing rather than two sets that legitimately do not overlap.

**The discharging session did not read a transcript**, which is why it could do this at all while
also being the session that set the design-corpus conventions above. It wrote a check; the check
reads. The suite was run with tracebacks suppressed, so a failure would have named a test and not a
call.

### O-5 — The escalation convention is now written down and checked here, and checked nowhere else

**Settled 2026-09-06 (D88).** `corpus/entities.md` now states which `outcome` an escalation takes —
`disconnection_reason: transferred`, `outcome: resolved` for a successful handoff and `unresolved` for
a failed one, `outcome_reason: escalated` — and states that `Outcome.transferred` is never that value,
declared only because an adapter has to receive what vendors send (D39).

**Nothing changed about the convention.** It is the one D73 settled and
`corpus/seeding-manifest.md` has declared as a true negative since. What changed is where it is
written, and that it is now bound by tests. **So this entry is not "the held-out set must be brought
into line with a change"** — it is the narrower and more easily forgotten thing: a rule that four
checks now enforce on one corpus and no check enforces on the other.

**What the held-out set must satisfy:**

1. Every call filed with `outcome_reason: escalated` carries the other two fields as above.
2. No call files `outcome: transferred`. D86 records that one was authored that way and the field was
   returned for correction, so this should hold today — **should**, which is the word this file exists
   because of.

**The port is four lines and the held-out suite can already run it.** Its workflow checks this
repository out at `.harness/` and its tests import `parse_call` from there, which is all the corpus
half of these checks needs: read each transcript's `[call]` block and compare the three fields. The
register half does not port — `corpus/entities.md` is a design-side document — so what travels is the
rule, not the check that the rule is written down.

**One thing this closes rather than opens, and it is worth stating.** D86's finding was that the
convention could not reach a curated authoring packet, because it lived in the manifest and the
register's escalation paragraph names a design call and is redacted. The new passage names no
transcript, so the held-out repository's authoring-packet builder copies it through its leak scan
intact and the next authoring session receives the rule. (Named without a path, because that builder
lives in the other repository and prose here may only name a path that resolves here -- the rule D83
learned in the entry that discharged this file's first three obligations.) That was D86's stated repair and it is done — but it helps only
sessions **after** this one, which is why 1 and 2 above still need checking against the six that exist.

**Discharged:** ☑ — session `43b504d3-1197-4a88-8b5f-e42df87c90fd`, date 2026-09-07

**Both halves ported and both pass.**
`test_an_escalated_call_records_the_escalation_convention` holds every call filed
`outcome_reason: escalated` to the whole three-field record, and
`test_no_call_files_its_outcome_as_transferred` holds the other direction. So the answer to the
"**should**" this entry flagged is that the set does conform: the field D86 records being returned
for correction is correct in the tree today, asserted rather than assumed.

**The floor is a rule and not content.** That this set contains an escalation is already public in
the harness's decision record — D83 decided to seed one, D86 accepted it — so asserting at least one
publishes nothing new, and without it the conformance check would be green over an empty set.

**What did not port, and why.** The register half — that `corpus/entities.md` *states* the convention
— stays in the harness: it is a design-side document, and what travels here is the rule, not the
check that the rule is written down.

### O-6 — A packet redaction now matches nothing, and the sentence it redacted was the accurate one

**Settled 2026-09-06 (D89).** The register's `matched_by` paragraph counted the calls carrying
`caller_ani` and stated the count wrongly. It is rewritten to state which value `matched_by` takes
instead of counting either population, because every design call carries both a calling number and a
booking reference and the count was of the wrong thing as well as out of date.

**What that breaks on the other side.** The held-out authoring packet's redaction list matches that
sentence **by exact string**, so the pattern now matches nothing. The packet builder's own docstring
predicts this — it says the redactions are best-effort, that the leak scan is the gate, and that two of
the original five patterns had gone stale within a day. So the failure is the designed one: the next
packet build stops with the offending line named rather than passing the material through.

**The part worth recording is the direction of the error.** The replacement text that redaction
substitutes reads *"Most design calls carry `caller_ani`; at least one carries `booking_reference`
instead"* — which is de-quantified, and which was **true of the corpus the whole time the register's own
sentence was false.** A held-out authoring session has therefore been reading a more accurate statement
of this rule than any design-side reader. That is not an argument for redacting more; it is evidence
that de-quantifying was the right instruction (D74) and that the register was the document that had not
taken it.

**What the held-out side must do:** when the next packet is built, read the line the leak scan names and
add a pattern for the rewritten sentence — or, better, drop the redaction. **The new sentence names one
design call and the old one named it too**, so a pattern is still needed; but the replacement text can
now simply be the register's own wording with the call id removed, rather than a separately maintained
paraphrase that can disagree with it.

**Discharged:** ☑ — session `43b504d3-1197-4a88-8b5f-e42df87c90fd`, date 2026-09-07

**Re-targeted, and the class closed rather than the instance.** The redaction now matches the
register's rewritten sentence, and its replacement is that sentence with the call id removed rather
than a separately maintained paraphrase that can drift from it — which is what this entry proposed.

**And the stale-pattern failure mode now has a check.** `test_every_redaction_still_matches_the_harness`
asserts every entry in `REDACTIONS` and `LINE_REDACTIONS` still has a subject in the harness documents
the packet copies. The leak scan remains the guarantee; this is the earlier signal, because a scan
that fires at build time hands the discovery to whoever is assembling a packet rather than to the
commit that staled the pattern. **Observed to fail on the pre-D89 string and to pass after restoring
the current one**, which is the second time that pattern has been proven and the first time by a test.

**One redaction was outside the lists and is now inside them.** The event model's worked-example
substitution lived inline in `build()`, where the new check could not see it — a redaction outside
the list is a redaction nothing checks, the same shape as the pattern that had already gone stale.
Moved into `LINE_REDACTIONS`, which changes no behavior and makes the check total: **all 8 patterns
match today**, verified by running them.

### O-8 — The held-out agent personas are declared nowhere, and no session needs to read them

**Settled 2026-09-07.** `corpus/entities.md` declares thirteen agent personas and says they are "used
in every call" — the *design* set's. An audit counted six more in use across the held-out set,
declared in neither repository. `test_every_agent_persona_is_declared` covers the design set only and
was **deliberately not ported** when its four sibling conventions were, because porting a check whose
declaration does not exist commits a knowingly red build.

**The persona is Class 1 vocabulary, not a label**, which is why this is an obligation rather than a
curiosity: the register's whole argument is that a name used and not declared "means the corpus
invented vocabulary its own canonical list does not know about, and every check keyed to the list
silently stops covering it".

**The discharge needs no reader, and that is the point.** `_agent_personas()` in the harness is a
deterministic extractor — a pattern over the agent's self-introduction — so the six names can be
produced by a **program**. Nobody has to read a transcript and no session has to be cleared:

1. Add a `declare_personas` generator to the held-out repository’s tools directory (named
   without a path here, because prose in this tree may only name a path that resolves in it):
   run the harness's extractor over
   `transcripts/`, write the sorted names to a `PERSONAS` file, and exit non-zero if the file on disk
   already disagrees with what it would write.
2. The owner runs it once and commits `PERSONAS`. **The owner authored this corpus**; the prohibition
   is on sessions doing design work, not on the person who wrote the calls.
3. Port the check as *used implies declared in `PERSONAS` or in the harness register*, and add
   `PERSONAS` to the workflow's tracked-file allowlist.
4. Run the generator in CI in `--check` mode, so the file cannot go stale the next time a call lands.

**Why not declare them in the harness register instead.** That was the other option the audit named,
and it is the one that needs a judgment nobody has made: it would carry six held-out-derived names
into a design-side document every future design session reads. They are only given names and reveal no
scenario, no defect and no label — arguably less than D83 already publishes about that set — but
"arguably" is doing work there, and the held-out side is the side that owns its own vocabulary. If the
register is later judged the right home, step 1 produces the list either way.

**Discharged:** ☑ — session `43b504d3-1197-4a88-8b5f-e42df87c90fd`, date 2026-09-07

**Done, and by the route above rather than by a cleared session.** The generator ran and wrote
`PERSONAS` in the held-out repository — one persona read from every call in the set, each of them now
declared. The check no longer skips,
the workflow re-runs the generator in `--check` mode so the file cannot go stale, and `PERSONAS`
joined the tracked-file allowlist in the same commit.

**The generator's count matches exactly what the contaminated session reported after reading them**,
which is the corroboration worth recording — stated as the agreement rather than as the number, since
the number is a fact about the held-out set and this file is not where it is declared. Two routes to
one answer: the first needed a person to read every transcript in the set and be trusted to stop
there, and the second needed a command.

**The session that ran it has not opened the file**, and did not need to — the generator reports a
count. That is not a claim the names can never surface: a failing check names the personas it could
not match, which is correct for whoever is fixing it, and is why the control here was run with
tracebacks suppressed. What the mechanism removes is the **reader in the ordinary case**, not the
possibility of one in the failing case.

**Planted against, in the only way available.** One declared name was removed *by index rather than by
reading* and both the suite's check and the generator's `--check` rejected the result; both passed
again after a byte-exact restore.

**What this settles beyond itself.** The obligation was filed as needing a session authorized to read,
and that framing was wrong — authorization is obedience, and obedience is what this register exists
because of. The question worth asking of the next entry like it is not *who may read this* but
**can a program produce it**. Here one could, and the answer arrived from the owner asking why
"authorized" was doing any work at all.

### O-7 — Two docstrings in the held-out repository describe its own content

**Settled 2026-09-07 (H-12).** An audit found held-out content outside `transcripts/`: two docstrings
in that repository's `tests/` describe a repaired defect and a repaired cross-call contradiction in
the set. The prohibition in `sessions/HANDOVER-adjudication-2026-09-01.md` was scoped to the transcripts
directory, so it did not reach them — in a file any harness session may open, and *must* open, since
porting a check means reading it.

**The harness-side half is done.** That prohibition now governs **content wherever it lives** rather
than a directory, and records why the obvious widening was rejected: forbidding the whole held-out
repository except its README and workflow would have forbidden the work that discharged O-4, O-5 and
O-6, each of which was closed by writing a check *in that repository*.

**What is owed here:** rewrite both docstrings as **rules** rather than as accounts of what was
repaired — the standard `sessions/HOLDOUT-REPAIR-BRIEF.md` already holds itself to, since it was written by a
session that could not read the five. The checks themselves do not change; only what their
documentation says.

**Who may do it, and why not this session.** Rewriting a docstring means reading it, so this belongs
to a session **already** contaminated. A fresh one doing it would be contaminated for nothing, which
is the audit's own sequencing advice. One of the two is a smaller loss than it looks: its content is
already stated harness-side in D85, so a session that has read the decision record has read it
anyway. The other is unread here.

**This entry runs the other way from every entry above it.** O-1 to O-6 are conventions the design
side changed that the held-out side must match. This is content on the held-out side that the design
side must never have to see — the same file, the opposite direction, and worth noticing because a
register built for one direction is exactly the kind of thing that fails open in the other.

**Done on 2026-09-07, and by a session that had not read either docstring.** This entry assumed the
work needed a contaminated session, because rewriting a docstring means reading it. It did not. Both
were located with `ast`, their text was replaced without being displayed, and each replacement was
composed from two things only: the function's own body, obtained with the docstring programmatically
stripped, and rules already published here — D64's title, D74's per-document minimums, D85's account
of the door-time contradiction.

**One of the two still carries an account, and it is D85's.** The event-id docstring has to say what
the contradiction was in order to explain why the check compares more than titles. That is the
paragraph this entry predicted would be *"a smaller loss than it looks"*: the same facts are stated
in D85 in this repository, so a reader of the decision record has met them already. What changed is
which way round it reads — the rule first, D85 cited for the history, rather than a repair note that
happens to imply a rule.

**Two claims in the drafts did not survive re-derivation**, which is the argument for composing from
the body rather than from memory. One said the harness's counterpart compares titles only; H-6 had
widened it that morning, so the draft was describing the world D85 was written in. The other said the
held-out exception list is kept identical to this repository's; nothing asserts that, since the
AST-equality test binds `_sourced_by` and not the list.

**And documenting the check found a defect in it.** Describing the comparison floor accurately meant
noticing it was an aggregate: `event_title` alone could hold the total above zero while `door_time`
stopped being compared, and `door_time` is the field D85 exists about. Fixed in a second commit
there, with the floor's predicate extracted so its control runs the check rather than restating its
arithmetic — planted, and observed to fail while the test it guards stayed green.

**Discharged:** ☑ — session `43b504d3-1197-4a88-8b5f-e42df87c90fd`, date 2026-09-07

### O-9 — The label chain runs in the held-out repository, and only its gate sees it

**Settled 2026-09-15 (D177).** The held-out repository's session set out, on 2026-09-14, the chain
the held-out labels move through. Three commits there, in order: **C1** seals the labels manifest
with the trailer `Rubric-Frozen: <F>`, F being the commit `rubric-frozen-v1` points at; **C2** commits
this harness's held-out run log unmodified; **C3** reveals the plaintext labels with the trailer
`Judged-Run: <C2>`. That repository's label gate checks the order over its history and checks C2's
header against F: its `labels_manifest`, its rubric version and its prompt template hash.

**What this repository supplies, and what it cannot see.** D173 to D176 built this side's links: a
held-out run writes `labels_manifest` into its header and keeps its paths out of this tree, agreement
is counted for each set apart, and `tools.verify_phase5` declares the criteria the gate asserts rather
than ticking them. None of that shows whether the chain has run, in what order, or whether the gate
passed, and everything above is recorded as that session reported it.

**Four answers this repository gave on 2026-09-15**, to the questions that session put beside the
chain. The severity export's schema is D181's, and is recorded with O-10. A held-out run carries the
held-out set's own corpus version, from a file committed there rather than the default inside this
checkout, and this repository refuses that flag inside the checkout on a held-out run (D182). A
held-out run's header names the rubric it judged under, by a hash this repository writes, so that
side's gate compares it with the freeze's and the commit-message trailer that side proposed is not
needed (D183). This repository writes the `heldout-` prefix that side's gate admits, so no rename sits
between writing a log and committing it (D184). D181 changes nothing here; the other three are behavior
and land with their criteria and controls.

**The run, as this repository would issue it:** the judged tier live, with `--transcripts`,
`--run-log-dir` and `--corpus-version-file` all resolving outside this checkout, and `--labels-manifest`
naming the commit that last touched the labels manifest before the log is committed. `--policies` stays
this repository's, since both sets read the same policy documents.

**Progress, as that session reported.** C1 landed on 2026-09-17: commit
`e8dcc2730bf8970c4391c1d0c7feb44e18dc11f0` there touches only the labels manifest, carries the
`Rubric-Frozen` trailer, and its gate held at S1. The held-out judged run was made the same
evening, at 2026-09-18T03:18:15Z, from this repository at `2581b17` — by the owner in their own
terminal rather than by a session here, because a live run asks a person to confirm the spend and
prints the judge's answer on every call it judged. Its log is named under the `heldout-` prefix
(D184) and was written to a directory outside both repositories, for the owner to copy across as
C2.

**C2 and C3, as that session reported on 2026-09-18.** C2
`49655ca2f0bee55ab2ef48f6f9579b2b3a014d62` committed the run log unmodified, and its gate held
at S2; the log hashes to
`f8392e7d63910b8aaf8c736ca467e3ee533cf539c279a19a6b9e1686b3b5ac5f` here as well, computed over both
the committed copy and the file the run wrote. C3
`19673ca17961ce4ab8f8af3c53a46b4e8a267e2c` published the labels and the salt, and its gate
held at S3, which completes the chain.

**What is owed there:** C1, C2 and C3 in that order, with the gate green over all of them. Ticked when
C3 lands.

**Discharged:** ☑ — reported by the session working on the held-out set, date 2026-09-18, the chain complete at C3 `19673ca17961ce4ab8f8af3c53a46b4e8a267e2c`

### O-10 — Held-out findings need severity bands, sealed before the held-out judged run

**Settled 2026-09-15 (D177).** Phase 5's coverage report states per-band coverage for the design set
and the held-out set apart, and this repository holds a severity file for the design set alone. The
held-out findings get theirs in a separate comparative-judgment store kept outside this tree, because
placing them against the design set's cuts would move those cuts (D144), and a person makes every
comparison (D10). That store's cuts are its own, so a held-out band orders severity within the held-out
set and is not a design-set band.

**When, and why then.** Before the held-out judged run: after it, whoever orders the findings can see
which ones the judge missed. The file is sealed before that run in a form the gate can check. The
manifest never changes once committed, so how the file is sealed is the held-out session's to decide.
It is revealed with the labels, and severity bands are labels (D10), so nothing about the held-out bands
is written here before the reveal (D61).

**How it is sealed, as that session reported on 2026-09-15:** a third sealed file, carrying a digest
line in the labels manifest at C1 and published with the labels at C3, refused there if it is missing,
empty or not JSON. What this repository will read from it is D181's: the scoring tool's own export at
schema 3, keyed by finding id, with its cuts in the same file, which that side can check before sealing
by loading it with this repository's own loader. Whether the scoring tool could key a second store on the
held-out ids was not settled here; the export sealed at C1 answers it in practice, since that side
reports reading it with this repository's loader before the manifest was written, and that loader
refuses a file whose bands disagree with its own cuts.

**What is owed there:** the store, every placement, and the sealed file, all before C2. Ticked once
the file is sealed.

**Discharged:** ☑ — reported by the session working on the held-out set, date 2026-09-17, sealed at C1 `e8dcc2730bf8970c4391c1d0c7feb44e18dc11f0`

### O-11 — The held-out set declares every kind of name, as D101 requires

**Ported there 2026-09-11, reported here 2026-09-14** by the session working on the held-out
set; nothing here can confirm either date. The port's own date is the cross-project audit's
reading of that commit, recorded because this entry carried the reporting date in three
places and read as though the work happened then. D101 made the register's rule, *used implies declared*, cover every kind of name the corpus
uses, with no exemption. Until this entry none here cited D101, and O-8 carried the rule to the agent
personas alone.

**The port, as reported:** a `declare_names` generator in the held-out repository's tools directory
writes a `NAMES` file, and its CI runs the name check against that file (commit d1cefa0 there). Named
without paths, as O-8 is, because prose in this tree may only name a path that resolves in it.

**Discharged:** ☑ — reported by the session working on the held-out set, date 2026-09-14, for a port committed there on 2026-09-11

That session's id was not given in the message reporting the port, so none is named here.

---

### O-12 — The gate resolves the freeze tag by name, and the published snapshot no longer carries it

**Opened 2026-09-21** by the session that published the freeze proof (D209), on a review reported
from the held-out side whose every claim was re-verified here first. Property (a) rests on the seal
commit citing the freeze commit's SHA, which is why it needs no timestamp. Publishing this project as
a snapshot (D208) left that SHA resolving nowhere in the public repository, and the snapshot reused
the tag name for its own first commit — dated four days after the seal — so the gate there reads a
tag that moved after sealing and reports it, as that side reported and as this side's reading of the
published tag's new target explains.

**What is owed there, and not here:** verifying against the published proof — recomputing the ids of
the objects in `freeze-proof/` under git's object rule and reading the freeze commit out of them —
rather than resolving a tag name in this repository, which a snapshot cannot carry without dragging
the private history behind it. Named as a behavior rather than by path, as O-8 and O-11 are, because
prose in this tree may name only a path that resolves in it.

**Extended 2026-09-21 by D210, on that side's own review.** The gate does more than read the frozen
template: it computes that template's hash by running the frozen harness's own code over the frozen
`src`, and refuses a hash that came from any other harness. So what is owed there is reconstructing
the frozen `src` from `freeze-proof/objects/` and running the probe against the reconstruction,
keeping that guard pointed at it — not archiving a commit this repository no longer publishes. This
side's verifier does exactly that, so the port has a working reference in a tree the gate can read.

**Why this side settled first:** so that the two are designed against each other rather than in
sequence. Nothing here can confirm the change, which is this file's whole subject.

**Ported there 2026-09-21, reported here the same day.** A freeze-proof module now sits beside the
gate in that repository's tools directory and recomputes the published objects; the gate reconstructs
the frozen `src` from them and runs its probe against the reconstruction, keeping the guard that
refuses a hash from any other harness, in place of archiving a commit this repository no longer
publishes (commit 7f9d1d1 there). As reported: the gate reports the phase-5 chain at S3, labels
revealed, as holding, and that suite is green both with a harness checked out and without one — 184
passing and 1 skipped in the first case, 55 passing and 130 skipped in the second, 185 either way.
**The first figure was reported as 184 alone and did not reconcile**: the skip had been dropped by
the held-out commit message this register copied, and that suite was never inconsistent.
**Verified rather than reported since 2026-09-22**, when that repository was published — its
scheduled run of that day, 184 passed and 1 skipped at `5367f81`, is readable from here, and its
workflow's harness checkout passes no token and names no secret at all. The one skip is its own
test of a reference run log at the freeze commit, which `freeze-proof/` does not publish: that
carries the frozen rubric, template and `src`, not the recorded runs.

**What the discharge also surfaced, and it is this file's own subject one layer deeper.** While that
gate was red over the freeze tag, this repository widened an event's timestamps to `int | None`
(`src/harness/core/events.py`, at event model v3, D203) because a vendor's source carries no timing
for a tool call and its result. That side did not see the widening until its gate went green again,
and has since adopted the `timing` reading rule this repository states rather than narrowing locally.
So the failure this file is written about has a second form: **a red build hides a divergence as well
as a green one**, because a build that is already red stops being read.

**Discharged:** ☑ — reported by the session working on the held-out set, date 2026-09-21, for a port
committed there the same day; nothing in this tree can confirm it

---

## Standing — a duty, not an obligation

Everything above runs one way: a convention changes here, and the held-out set must be brought into
line. **`HELDOUT_SET` runs the other way.** It declares the held-out set's call identifiers in this
repository because nothing here can discover them, and it must be updated whenever that set changes.

It is listed here rather than above because it is never discharged. An obligation is closed once; this
is a step that comes due again every time the companion repository grows, and it fails exactly as
everything else in this file fails — silently, with a green suite either side. It exists because a
hardcoded `range(13, 18)` in `tools/statement_inventory.py` rejected `CALL-21` as belonging to neither
set, which is the only reason anyone noticed the addition had left three documents describing five
transcripts.

Identifiers are metadata and safe to hold here; the transcripts are content and are not. That
distinction is the whole reason this file can name the set at all.

**No session searches the held-out repository's labeling sessions before the reveal.** Do not open,
search or list the transcripts of sessions that worked in `voice-agent-eval-harness-holdout` — by
path, by a tool that searches past sessions, or by any other route — until the held-out labels are
revealed. A session that has read one knows what the labels say, and agreement is measured against
exactly that. It binds every session on this repository, including those that build phase 5, and it
is carried into each new session prompt and handover when they are written.

**It did its job at the reveal.** The held-out labels were revealed on 2026-09-18, at C3
`19673ca17961ce4ab8f8af3c53a46b4e8a267e2c` there, so this rule no longer binds; it stays here as
the record of what held until then. D61's deferral ended with it: the sentence about the held-out
set's composition that D61 kept out of both trees published with the labels, at 0b85918 there, as
D61 said it would. What does not end is the absence check: held-out transcripts, run logs and
reports over held-out calls stay out of this tree after the reveal as before, and agreement's
held-out section still goes to stdout only (D175).

---

## Discharged

**Twelve** <!-- #discharged_obligations -->, and that number is computed rather than maintained.
O-1 to O-3 on 2026-09-06 by session `f43fee59-3162-4cf8-85d7-6aba414372ed` — O-1 and O-2 by repair,
O-3 by decision (D83). O-4 to O-8 on 2026-09-07 by session
`43b504d3-1197-4a88-8b5f-e42df87c90fd`, each by writing something in this repository or that one
rather than by editing the held-out set: a check for O-4, O-5 and O-6, a generator for O-8, and for
O-7 a pair of docstrings composed without reading the ones they replaced.
O-11 on 2026-09-11 there, reported here on 2026-09-14, by a generator and a check
written there. O-10 on 2026-09-17, as the session working on the held-out set reported, by
sealing the severity export beside the labels at C1. O-9 on 2026-09-18, as reported, when C3
revealed the labels and completed the chain. O-12 on 2026-09-21, as reported, when the gate stopped
resolving a tag this repository's snapshot no longer carries and began verifying against the
published freeze proof instead.

**This heading has gone stale twice.** It said "all three" and meant the three that existed at the
time; a note recording that went in, and then the replacement said "all six" while seven were
discharged — the shape this whole file is about, appearing in its own summary line, inside the
sentence that had just finished recording the previous instance. So it is not maintained by hand any
more. The tag above marks a quantity
`tests/test_document_counts.py::test_every_tagged_quantity_states_the_number_it_names` computes from
the `☑` marks below, so the next discharge fails a build instead of waiting for a reader.

The entries stay where they are rather than moving here, because each is now a record of what was
found as well as what was owed, and a reader arriving at "the rule" should meet "and here is how
things actually stood" without following a link.

**What the discharge does not settle.** Both repairs are now enforced *in the held-out repository* —
its own `test_holdout_conventions.py` ports both checks and its workflow runs them. That closes the
gap this file was written about, in one direction only: **the ported provenance rule is a copy of a
private helper in `tests/test_corpus_hygiene.py`, not an import of it.** Two copies of a rule are two
things that can disagree, and if this one changes and that one does not, the held-out suite goes green
against a stale convention — which is this file's own failure mode, one layer down. Moving `_sourced_by`
into the `harness` package would let both repositories import one implementation. That is a suggestion,
not a discharge, and nothing depends on it today.
