# Handover — after the held-out reveal

**Status: closed** 2026-09-20, `3a6f0fe` to this commit. Opened 2026-09-18. Its phase was audited on 2026-09-19, remediated in D194 to D198, and the specification swept for this close at 0.60.0 (D199, D200). The held-out label chain completed that day, as the
session working on the held-out set reported: C1 sealed the labels manifest, C2 committed this
repository's held-out run log unmodified, and C3 published the labels, each with that repository's
gate green. O-9 and O-10 are discharged in `HOLDOUT-OBLIGATIONS.md`, and the rule against searching
the labeling sessions is retired there.

**Agreement was computed and not committed.** `harness agreement` ran over the five held-out inputs
in place on 2026-09-18, from `2581b17`, and its held-out section went to stdout and to the owner, as
D175 requires; no held-out number is in this tree. The session that ran it,
`4fd70902-d338-4ae6-a51d-a2cf626bec77`, read held-out content once the labels were public, on the
owner's decision, and does no further rubric work.

**The coverage report by severity is built** (D188), the last piece of phase 5 this repository
owed: `harness coverage` reads each set's severity file in place, the held-out one included, and
`tools.verify_phase5` ticks both of its criteria where it had declared them not yet built. Since
D189 it also refuses a band placed on text that has changed since it was scored. It ran over the
held-out inputs in place on 2026-09-18, and its held-out section went to stdout and to the owner
alone, as agreement's did; no held-out figure is in this tree. The session that built it,
`7316ed13-b742-4337-9728-804081814351`, read held-out content once the labels were public and does
no rubric work.

**Since then, on the same day**, D191 recorded, with no held-out figure, that the deterministic tier
recognizes a defect only in the design set's own words, and widened phase 7 to answer it; D192 split
each coverage band by detection type. OB-7's trigger, phase 5 measuring agreement against held-out
labels, has fired, and its row in `OBLIGATIONS.md` is open again: held-out agreement is measured and
never committed (D175), so `JUDGED_AGREEMENT_PENDING` cannot close on a committed figure, and what
closes it is still to decide. D193 closed items 1 and 2: the register declares the settlement token
and five identifier shapes, and the name check gained a check for each kind of value, named in that
commit's message for the held-out side.

**Then the phase was audited, remediated and swept.** An independent session on another model read
phase 5 and everything since the freeze on 2026-09-19 and returned 16 findings (`sessions/AUDIT-2026-09-19-phase-5.md`); all 16 are closed, in D194 to D198 and the commits its
banner names. A second independent session then swept the specification (`sessions/SWEEP-2026-09-19-phase-5.md`), returning 27 statements to correct, of which two were
about this close: the check that evaluates *at phase completion* read only one of the two forms
this project writes a closed status line in (D199), and this handover named no decision past the
marker. Both are repaired, and the specification is swept at 0.60.0 @ D200.

## What is owed

### 1. A settlement processor the design corpus names is declared in no register

Found by the held-out side while labeling, and checked here: the design set's CALL-02 and CALL-11
carry `settlement=cardinal_pay`, and `corpus/entities.md` declares no such processor. D101's rule is
that every kind of name the corpus uses is declared, and the check that holds it passes, so a
settlement processor is a kind of name that check does not extract. Owed: declare it, and either
widen the check to that kind or record why it stays outside. As the held-out side reported, a
single declaration in `corpus/entities.md` covers both sets.

### 2. Four identifier shapes the design corpus uses are declared in no register

Identifiers shaped `RF-`, `TR-`, `MS-` and `EX-` appear in the design transcripts and in no Class 2
table of `corpus/entities.md`, the same gap as item 1 in another kind of name. Owed: declare the
shapes, and the same decision about the check. **When a widening of the check lands, name it in its
commit message or in a handover.** As the held-out side reported, its name check copies
`_declared_names` and `_REGISTER_CATEGORIES` from `tests/test_corpus_hygiene.py`, a test there pins
the copy by comparing the helpers whole but only two patterns of the part that reads names from a
transcript, and its CI runs against this repository's `main`; so a widening either turns its build
red or passes it by without failing. Catching up is that side's work.

### 3. Phase 5 is complete here, and is not yet closed

Every phase-5 criterion this repository can tick is ticked by `tools.verify_phase5`, and the three it
cannot, the label ordering, the frozen-commit citation and the manifest's recomputation, are asserted
by the held-out repository's gate, which that side reported green from C1 to C3. What has not happened
was what closed phases 2 to 4: an independent audit of the phase by a session that built none of it,
as `sessions/AUDIT-2026-09-12-phase-4.md` was for phase 4, and this handover marked closed, which
requires the specification's `Last swept` marker to reach the last decision it records. Both have
now happened: the audit of 2026-09-19 with all 16 findings closed, the sweep recorded at 0.60.0,
and this handover closed at the top. **Owed: nothing further here.**

### 4. Phase 6 opens once phase 5 closes

Phase 6 is next in the specification's plan: the second adapter, the log inspector, per-instance
severity, prompt caching and judge-model comparison. It has had neither the contract reading D157
gave phase 5 before it opened, since the contract-coverage table still declares phase 6 unmapped
(OB-16), nor a session brief. Owed once phase 5 closes: the reading, and a brief for a fresh session.
The tracing question in item 6 bears on that reading.

### 5. Phase 7 carries D191's widening, and a fresh held-out set

D191 widened phase 7 because the deterministic tier recognizes a defect only in the design set's own
words: its entries are to read the parser's structured claims, the reason-code and outcome tables are
to be re-expressed or explicitly deferred, and the result is to be measured on a fresh, larger
held-out set authored and labeled blind to the widened tier, through the same label chain. D191's
rule is judgment, not a check, so this item is what keeps the widening from being lost before phase 7
opens. The owner chose Fable 5.1 at effort xhigh for that phase's session.

### 6. Whether a finding may be traced to entries of both tiers

Both sets trace every finding to entries of its own tier only. In the design set's `traces_to`, 64
traces run from deterministic entries to assert-type findings and 19 from judged entries to
judge-type ones, with no trace across the tiers, and the held-out traces follow the same convention;
both counted here on 2026-09-18. Under it, a judged entry that fires on a call whose finding is
assert-type scores a false alarm in `harness agreement`, and the finding stays uncovered in `harness
coverage`: where the deterministic tier cannot reach a finding, the judge's catch reads as its
error. The question was raised for phase 6 in the held-out repository's phase-5 labeling notes, as
that side reported, and no record here carried it; D191 covers the deterministic tier's reach, not
this convention. It bears on phase 6's opening reading, since judge-model comparison measures
agreement against the gold set (item 4), on the design set's own `traces_to`, and on what closes
OB-7. Owed: decide, before phase 6's criteria are written, whether a finding may be traced to every
entry that can reach it from either tier, or record why the convention stays.


### 7. The reach statement D83 owes the published held-out result

D83 decided that the published result states which classes the held-out measurement does not reach,
and `HOLDOUT-OBLIGATIONS.md` records that as still owed "in the published result at phase 5". Phase
5's result was computed on 2026-09-18 and went to the owner; nothing in this tree records the
statement being made beside it, and the owner does not recall either way. It carried no `OB-` row
because it was written into a register rather than under a handover's *What is owed*, which is the
gap OB-15 names, and the specification sweep found it as S-23 with the phase about to close over it.
Owed: the five classes O-3 lists as absent from the held-out set, stated wherever a held-out result
is published or reported, and a line here or in the register when that happens.
