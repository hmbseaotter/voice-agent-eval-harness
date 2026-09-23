# Handover — phase 4, the full rubric and the report

**Status: closed** 2026-09-12, `7860094` to `64b5848`, with the phase-4 audit's pre-freeze findings closed in it and the rest carried by `HANDOVER-2026-09-12-phase-4-audit.md`. Opened 2026-09-09. Answers
`sessions/PHASE-4-SESSION-PROMPT.md`.

*Being written as the phase runs rather than at the end, because `OBLIGATIONS.md` harvests the owed
section below and an obligation found on the first hour should not wait for the last one to be
registered. That heading is named here without being written, for the reason the judge template
names its own boundary marker the same way: a document explaining a checker cannot contain the
checker's own trigger (D89), and the harvest keys on the heading.*

---

## Run the gates first, so a failure later is yours

```bash
uv run pytest -q && uv run python tools/verify_phase1.py && uv run python -m tools.verify_phase2 && uv run python -m tools.verify_phase3 && uv run python -m tools.verify_phase4 && uv run python tools/statement_inventory.py && uv run python tools/verify_controls.py
```

Note the addition: `tools/verify_phase4.py`. It is the other three verifiers' shape and imports the
phase-2 reporting loop rather than keeping a fourth copy. **It was wired into CI on the day it was
written**, which phase 3's was not — and that omission had already cost something before anyone
noticed.

---

## What this phase found, before what it built

Four findings, and three of them were found by *running* rather than by reading. That is the same
ratio phase 3 reported, and the reason is the same: this project's documents are checked for
resolution and for counts, and neither of those reads a number for whether it is big enough.

### 1. The contract could not tell the design from its inversion, in four places

Phase 2 opened by asking whether its own acceptance criteria covered its own requirements and found
five of twelve covered in half (D104). **Nothing mechanizes that check**, so phase 4 ran it by hand
over five `[P4]` requirement statements and eleven criteria. Four of the five were covered only in
the half the requirement names, and one deliverable — the two-audience report — carried no criterion
at all.

The four halves, because they are what to look for when the same check runs at P5:

- **The synthesis citation criterion was satisfied by a checker that reports every citation as a
  defect.** The design inverted, ticked green.
- **Two criteria about the rate named no tier**, and `_breakdown` has printed all five status counts
  beside every rate since P2 — so both went green off a tier that was already there while the judged
  roll-up this phase builds went untested.
- **The verdict-distribution criterion resolved either way on a unanimous fixture.** A renderer
  printing the first verdict with N under it satisfies "a verdict distribution, not a single verdict".
- **The escaping criterion was satisfied by deleting the characters.** The requirement's verb is
  *escape*.

Nine criteria added before a line of code, and a tenth with the precondition. **11 to 21.** D130
records it, and `OB-16` records the half of the check that is mechanizable and still is not built:
whether every requirement is *named* by at least one criterion is a comparison a test could make,
and two phases have now made it by hand.

### 2. The precondition's fix reached twice the calls the defect had been measured on

D125 left a structural fix and named two branches: the entry declares a precondition, or the class
moves to the deterministic tier. **The second turned out to be already there** —
`A-rule-stated-without-retrieval` has been in the deterministic tier since P2. Reading them as a fork
was the fork's own mistake: what was wrong was not that the class lacked an assertable check, but
that a *judged* dimension was answering a question it had no subject for.

`CONFLATED_NO_CLAUSE_CALLS` pinned four calls — the no-clause calls the dimension flagged
`misaligned`. The precondition excludes eight. **The difference is the no-clause calls that came back
`aligned`**: a verdict as meaningless as the flagged ones and far harder to see, because a pass on a
corpus seeded with defects reads as the dimension working. What phase 3 measured was the visible
half.

That difference is what would have condemned a criteria edit — D125's falsifier exists to catch a fix
reaching calls the defect had not touched. It does not condemn this one, and **the reason is the
boundary rather than the count**: the precondition excludes on the dimension's own subject, the
clause this call retrieved, and not on a list of calls chosen by their verdicts. A fix justified by
which calls it moves is a fit; a fix justified by what the dimension is about is a definition.

### 3. A judged dimension the corpus cannot exercise is a finding about one of them

D42's fourth dimension is *"When the caller objected and a reversal or transfer followed, had the
agent misunderstood them in the first place?"* The design set contains **one** reversal — CALL-20's escalation — and
the seeding manifest records it as correct behavior. So the dimension as worded had a negative
instance and no positive one, and `traces_to` is a required non-empty field. **It could not be
authored.**

Sitting beside it, taxonomy item 1 — *doubling down under correction* — was a recorded GAP with two
seeded judge findings and no dimension. D133 widened the trigger to any caller pushback and covered
both. The narrower reading survives as the entry's `negative_instance`: the one reversal the corpus
contains is exactly the call the dimension must stay silent on.

**How the gap was found is the transferable part.** Not by reading transcripts for reversals — by
asking which findings a `traces_to` could honestly name, and finding the answer was none. A field
that must be filled is a question that must be answered, which is the argument D107 makes for
`negative_instance` one field over.

### 4. A copied `max_tokens` carried its reasoning only as far as the two entries were alike

Phase 3 raised its entry from 2048 to 4096 before its first live call, on the discovery that
`max_tokens` bounds **thinking plus output**. That lesson went into the entry, the handover and the
conventions list. Phase 4 then gave five new dimensions 4096 by copying it.

The first live pass truncated one. `J-confidence-exceeds-sources` — the only dimension that renders
facts, so the largest prompt and the most to reason over — returned 4,096 output tokens of a 4,096
ceiling, resolving to `errored` carrying its stop reason. Its median answer ran to about a thousand
and its p90 to eighteen hundred; every other dimension's largest answer was under fourteen hundred.

**The check written for that found a second instance before it had run once against its own data**,
and the second was phase 3's own entry: `J-policy-alignment` never truncated in three live passes and
its largest recorded answer was **3,429 tokens of a 4,096 ceiling** — eighty-four per cent full, on a
margin nobody had looked at because nothing was looking.

So the split is a property of the tier rather than a list of entries that broke: **the two entries
that render facts get 8192 and the four that judge the conversation alone get 4096.** D135, and
`test_every_entrys_max_tokens_clears_what_the_reference_run_recorded` is the mechanism — a value read
off the artifact rather than reasoned about beside itself.

**The rule that fix produced was itself wrong, and the next pass proved it (D137).** D135 framed the
result as a property of the tier — *the entries that render facts get 8192, the ones that judge the
conversation alone get 4096* — and that read as discipline and was a sample.
`J-caller-pushback-understood` truncated twice on the next complete pass, on CALL-05 and CALL-12,
the two longest calls in the corpus and the two that were not in the partial pass D135's numbers came
from. Its median answer is 330 tokens and its ninetieth percentile 1,020; it reached 4,096.

**The entries differ in their median by a factor of five and in their tail by far less**, because the
tail is set by how hard the hardest call is and every dimension faces the same hardest call. Every
judged entry is at 8192 now. What a generous ceiling costs is not money — `max_tokens` is a ceiling
and only tokens produced are billed — it is the pre-flight estimate, which charges the full ceiling
on every call because an operator approves a bound. That figure is now roughly five times the bill,
which is defensible only while it is labeled a ceiling, and it is.

### 5. One dimension of six was measuring something other than its name

`J-confidence-exceeds-sources` came back `exceeds_sources` on **13 of 16 calls, including its own
negative instance, ten repetitions for ten.** CALL-12 is the call the seeding manifest records as the
true negative for exactly this class — *a figure the agent does not have is declined rather than
invented*.

**An entry defect, not a measurement**, by D125's test: its criteria said the agent exceeded its
sources when it *"asserted something its sources cannot settle"*, with *"most often a claim about a
system it cannot see"* offered as a hint. A hint is not a bound, and against that framing almost any
confident sentence qualifies. That is phase 3's conflation arriving in a different entry.

**The fix is derivable from the sibling entry**, which is what makes it a definition rather than a
fit. `J-claim-plausible-in-the-world` asks a neighboring question, carries an explicit exclusion —
*do not judge claims about this system's own records* — and behaves: two of sixteen, both traced,
negative instance clean. The broken entry had no exclusion and no trigger. It gained both, and went
to **6 of 16**. D136 carries the falsifier, which was written to disk before the edit was made.

### 6. Three of the falsifier's four conditions cleared, and the fourth was written wrongly

The two over-broadness conditions held — CALL-10 and CALL-08, the seeded findings, both stayed at
the negative pole ten for ten. Two of the three ineffectiveness conditions held. **The fourth said
CALL-12 must become `within_sources`, and it became `borderline`** with the negative pole appearing 4
times in 10.

The property that mattered held: the modal verdict is not the negative pole, so the call does not
violate and the gate does not fail it. The words asked for something stronger than the property, and
asking for it would have condemned a fix that did what it was written to do.

**That is a defect in the falsifier and it is recorded as one.** The value of writing it first
survives: the three conditions that mattered were checkable exactly because they were fixed in
advance, and the fourth being wrong is visible only because it was written before there was a result
to shade it toward. A falsifier composed afterwards would have said `borderline` all along.

It exposed an ambiguity nobody had noticed since P3: **what "silent on a negative instance" means for
a tier that answers N times.** The guard demanded the negative pole appear in none of the N; the gate
reads the modal verdict; and on CALL-12 the two disagreed about one call. D138 settles it on the
gate's reading, states plainly that the choice was made after seeing the data, and pins the firing
count separately so the early warning the stricter reading gave is bought back rather than lost.

**Eight passes against a budgeted $15–25, and the budget was the estimate's fault rather than the
run's.** Every overrun bought a defect: the first two the ceiling, the third the broken dimension, the
fourth the ceiling rule and the falsifier's own wording, the sixth CALL-12's missing charge. All were
found by running rather than by reading, and most *during* a run rather than after it, because the run
log is written as the run goes. Once the ceiling settled at D137 a pass costs about **$14** and takes
about **2.2 hours** — 1,044 calls, median 5.8s, p90 15s.

**Pass seven was wasted and the reason is worth more than the $3.50.** It died after four of sixteen
calls because a control sweep was started against the tree while it was recording — `verify_controls`
copies the repository ninety times and runs pytest in each copy, and the live run did not survive the
company. The run's own output was piped through `tail`, so the evidence of *how* it died was discarded
in the same command that lost it. **Two rules, both cheap:** nothing heavy runs against the tree while
a pass is recording, and a paid run's output is captured whole.

### 7. The corpus modeled money leaving and never money arriving

`issue_refund` had a place to record money going out and nothing recorded money coming in. So an
agent telling a caller their money *was taken* had a price field to stand on and nothing else, and
the judge split on whether a price is a capture.

**Two instances, four days apart, and the second cost a live pass because the first was not written
down.** CALL-22's was diagnosed by the owner from the sentence itself — *"the one thousand two
hundred and fifty dollars has gone on the card"* reads as money arriving or money leaving depending
on who is speaking — and fixed with `charged=1,250.00` on the tool result. That was taken as a wording
repair. CALL-12's is the same gap one turn over: *"The twenty-two dollars was taken when you booked"*,
with `ticket_price_total := 22.00` and no payment anywhere in the call.

**What makes the second one an entry rather than a repeat** is that `corpus/seeding-manifest.md`
declares CALL-12 events 16–17 a **true negative** and justifies it with *"A recorded charge stated as
the record has it."* There was no recorded charge. A declaration and an artifact disagreed, and the
manifest's anchors cannot see it: they assert that *text exists at an event*, never that *a record
supports a sentence*. D141 carries it; the fixture now carries `charged=22.00`.

### 8. D82 wrote down what its open gap would look like, and three days later it looked like that

D82 left the severity file attesting to the comparison log rather than to what was compared, chose to
document the gap and name `cj load` as its detector, and predicted the failure in as many words: *"A
severity file can still be committed alongside findings it no longer describes, and only a person
running `cj load` will find out."*

The instance arrived by the one route that mitigation cannot reach. Not an author editing a finding —
`e28650c`, the repository-wide US-spelling pass, 51 spellings across 17 files, three of which were
also the subject of ten pairwise human comparisons each. **Nobody was editing findings.** A trigger
sentence in `severity.py` is read by someone working on severity; a cross-cutting sweep is the edit
where no such person exists. D140, OB-18.

### 9. Four reference-run assertions were written against a rubric holding one judged entry

Three had been failing since the second entry landed and one had quietly stopped being true.
`test_a_real_run_records_n_repetitions_for_every_call` counted rows per call across the whole log and
compared them to one entry's `repetitions` — 60 or 70 against an expected 10, **so it could not have
passed whatever the run recorded**. The request-coverage test rebuilt only `J-policy-alignment`, the
one entry carrying a precondition, and reported every call that retrieved no policy as uncovered.
The citation validator's `== {0}` met its first true positives: four informed retries, all on the
synthesis entry, which is the only entry whose prompt names other entries.

**The fourth is the one worth the entry.** The pre-flight estimate test compared one dimension's
figure against the largest input recorded for that call *by any entry* — always the synthesis, whose
prompt carries six dimension results the renderer cannot see. Sixteen calls failed with sixteen
near-identical lines. Every line was true and every line was about the wrong entry: measured per
entry, the six dimensions sit at 2.57–2.73 characters per recorded token against a divisor of 2.4 and
are bracketed comfortably; the synthesis sits at 1.41–1.63 and was **below every recorded count**.

**The neighbor shape, inverted.** A guard narrower than its rule is green and blind. A guard *wider*
than its rule is red and uninformative — and that is worse in one specific way: nobody looks at a
green check, but everybody looks at a red one's message, and this message named calls when the defect
lived in an entry. D142 adds a measured `_SYNTHESIS_INPUT_ALLOWANCE` and compares per entry.

### 5–6, corrected 2026-09-10 — the cited true negative is a different turn of the same call

*Appended, not woven in: 5 and 6 above are what was written at the time.*

Findings 5 and 6 both rest on one quotation — *a figure the agent does not have is declined rather
than invented* — offered as the manifest's true negative "for exactly this class". **That is the row
for CALL-12 events 30–31**, the delivery-time question. The judge's `exceeds_sources` rationales, in
all three passes, object to **event 17** instead: *"The twenty-two dollars was taken when you
booked."* The manifest's row for that turn reads *"A recorded charge stated as the record has it"* —
and nothing in the call recorded a charge. The argument picked a true-negative row by call when the
manifest records them by turn, and took the one that read best.

**So finding 6 is wrong about why condition 3 failed.** The falsifier's demand that CALL-12 become
`within_sources` was correct and the fix did not meet it, because the obstacle was a missing field in
the fixture rather than loose wording in the dimension — something no narrowing could have reached. A
condition that was detecting a real defect was written off as a defect in itself.

**What stands:** the fix (13 of 16 to 6 of 16, every remaining firing traceable to a recorded
defect), and D138's modal reading, which never depended on this call being clean. D141 carries the
diagnosis, the fix — `charged=22.00` on CALL-12's event-10 result — and the class both instances
belong to.

---

## What is owed, in the order I would take it

**These are registered in `OBLIGATIONS.md`, which is the live view.** The headings below are the
source the register harvests, and it compares the anchor as well as the number, so renaming one
breaks a row on purpose.

### 1. Nothing mechanizes whether a phase's criteria cover its requirements

`MEASURED_CONTRACT` in `tests/test_document_counts.py` pins the requirement and criterion counts per
phase and says nothing about the relation between them. Two phases have now opened by running that
check by hand — D104 for phase 2, D130 for phase 4 — and both found requirements covered only in the
half the requirement names.

**The adequacy half is a reading and will stay one.** Whether a criterion covers *both* halves of
its requirement, and whether it can be told from the design's inversion, is judgment: D104's
grounding criterion and D130's synthesis criterion were both green against a fixture that resolved
either way, and no scan sees that.

**The completeness half is not, and it is built.** *Every requirement is named by at least one
criterion* is a comparison a test can make, given a way to address a requirement bullet — and the
phase verifiers already anchor a criterion to the document by distinctive substring, so the
machinery existed one field over. `tests/test_contract_coverage.py` is that comparison, with two
controls, one of them planted in the specification because the defect is a requirement written
without a criterion and that cannot be expressed as a change to code.

**What is left is the population, not the mechanism.** Only phase 4 is mapped, because phase 4 is
the phase that ran the reading. Mapping 1 to 3 means making a coverage claim about criteria this
session did not audit, and a table asserting what somebody guessed would report green over exactly
the state the check exists to find. The unmapped phases are **declared rather than exempted** —
`JUDGED_AGREEMENT_PENDING`'s idiom one register over, so the guard stays total and a phase is either
mapped or named. What closes it is one reading pass per phase, of the kind D104 and D130 each did
for their own.

### 2. The pre-flight estimate is a multiple of the bill, and nothing prints the other number

`judged_call_estimate` charges every call the full `max_tokens` for output, deliberately: an operator
approves a **ceiling** rather than a guess, and D127's predecessor was a constant that understated
input by three and a half times, which is wrong in the direction that gets more money spent than was
agreed.

D137 raised every judged entry to 8192 and D142 added the synthesis input allowance, and the
printed figure is **$112.56** against a full pass that realized **$14.11** on 2026-09-11 -- eight
times, measured on that date rather than stated as a standing ratio, because this heading said *six
times* until the handover was swept and the number had moved underneath it twice. The gap is not a
defect in the arithmetic; it is the arithmetic working, and it is large enough to be a different
problem. **A number that many times the bill is a number an operator learns to skip**, and an
approval nobody reads is the thing the confirmation exists to prevent -- one step removed, which is
this project's own argument about a guard a reader believes they have.

D137's caveat names the remedy and does not build it: **a second figure beside the ceiling** --
expected cost, computed from what the committed log actually recorded per entry, printed next to the
bound. The log already carries the token counts, and `test_the_preflight_estimate_brackets_what_the_real_run_recorded`
already reads them, so the data and the machinery both exist. What is missing is the line.

### 3. The severity file records what was judged about, not what was judged

**The four unsound rows this item was opened for are discharged.** On 2026-09-11 the owner accepted
the three carried-over revisions and placed F-90: `corpus/findings.severity.json` scores all **83**
defect-tier findings, `unplaced` is empty, `cj load` reports admitted 83 and excluded 7 rather than
refusing, and the gold-set join is green. What that placement cost is D144, and it is not small --
two of the three band cuts had to be re-drawn.

**Discharged 2026-09-11 (D148).** Schema 2 carries `content_hash` on every row, and
`test_every_scored_finding_still_matches_the_text_it_was_scored_against` recomputes it from
the gold set on every run. What follows is what it was owed for, kept because the reasoning
is the point and a discharged row with its argument deleted is a tick.

**What remained was the mechanism.** The severity file recorded `id`, `severity` and `theta` per
finding, plus a `comparison_log_hash` over the whole comparison log. So it attests to *the judgments*
and not to *what was judged*. The per-finding content hashes that would catch a finding's text moving
under a band live only in `.cj-store/findings.jsonl`, which is gitignored and correctly so.

That gap is D82's, left open deliberately with `cj load` named as its detector -- and on 2026-09-07
`e28650c`'s repository-wide spelling pass walked straight past that documentation, because it was a
cross-cutting sweep and there was no person working on severity to read it (D140). **The detector
only fires when somebody runs it, and the edits that break this are exactly the ones where nobody
thinks to.**

**What closes it** is D82's own rejected option (B): carry each finding's content hash into the
exported schema, in `comparative-judgment`, and re-export. `cj export` needs no new comparisons, so
this costs one export whenever it is built -- the two halves did **not** have to ship together, which
this item claimed when it was written and D140's consequences now corrects.

**Item 6 was inside this one until D147.** A band whose text has moved and a band nobody has
determined are different defects in the same file, and one number cannot be closed twice.

### 4. A band cut can stop describing a gap, and only the extreme case is detected

`cj` refuses a cut whose anchors have **inverted** -- above has fallen at or below below -- and says
so loudly; that refusal is what surfaced D144. It says nothing about a cut whose anchors have merely
**drifted apart**, with findings moving between them.

They are one defect at two magnitudes. `high_medium` was anchored on F-14 | F-53, adjacent at a gap
of 0.060. After F-90 was placed the gap was **1.4005 with seventeen findings inside it** -- a boundary
spanning a third of the scale rather than separating two neighbors -- and three findings changed band
with nothing reporting it. The inequality a separated cut satisfies is exactly the one the inversion
check tests.

**Two things are owed and they are in different repositories.**

In `comparative-judgment`: a separated cut should be reported the way an inverted one is. The
threshold is already derived from the anchors, so the count of findings between them is available
wherever the inversion check runs. What "too far apart" means is a judgment -- one finding between
anchors is ordinary drift, seventeen is not -- and naming it is the work.

Here: **nothing reads `cuts.json` at all.** The harness joins exported bands by id, so a cut could be
anchored on anything and no test would notice. That is deliberate as far as it goes -- the tool owns
the file (D22) -- but it means the repository carries bands whose construction it cannot inspect, and
the exported file records `id`, `severity` and `theta` without recording how well determined each one
is. F-90's band rests on three comparisons where every other rests on ten, and nothing committed says
so. That is OB-18's second half arriving from a different direction, and the two should be answered by
one schema change rather than two.

### 5. An aborted run throws away everything it had already paid for

A judged run that aborts keeps its results -- `RUN ABORTED` names the log and says every outcome
obtained is in it -- and then nothing can use them. Live mode **writes** a run log and never **reads**
one, so the next attempt starts at call zero and pays for all of them again.

Measured rather than supposed: the abort D145 records happened at call 575 of roughly 1,040, having
spent **$7.39** of an expected **$14**. Finishing from there would cost about **$6**; starting over
costs the full fourteen and another two and a half hours.

**The machinery already exists one mode over.** Replay looks a request up by `(request_hash,
repetition)` and serves the recorded response; that is exactly what a resume needs on a hit, and live
issuance is what it needs on a miss. What does not exist is the mode that does both.

**Two things have to be decided before it is built, and neither is a detail.**

First, what the resulting log may claim about itself. `test_the_committed_log_is_a_live_recording_and_not_a_replay_of_one`
reads the header's `mode`, and a log assembled from two live sessions is not a replay -- every call in
it was issued against the API -- but it is not one continuous live run either. Recording the
resumption in the header is the honest answer and it is a **run-log format change**, which D131
deliberately settled before this phase recorded because a format change afterwards costs a live run.
That argument cuts both ways here and the decision is not obvious.

Second, whether a resumed log may be the *reference* log at all, or only a way to finish a measurement
cheaply. D136 refused a merge of two partial recordings on the grounds that it is bespoke machinery
with no controls, and this is a near relative of that refusal.

P5 records against the held-out set and faces the same exposure, so the cost of leaving this is not
one run.
### 6. A severity band does not record how well determined it is

**Discharged 2026-09-11 (D148).** Every row carries `appearances` and `informative`, asserted
by `test_a_severity_row_records_how_well_determined_it_is`. Reported rather than gated:
nothing refuses a band resting on three comparisons, and F-90's does, because a threshold
nobody chose is the move D134 declined for the judged tier.

`corpus/findings.severity.json` gave every finding `id`, `severity` and `theta` and stopped. Two rows
that look identical can rest on very different evidence, and on 2026-09-11 two of them did: **F-90's
band rests on three comparisons where every other finding's rests on ten.**

That is not a defect in the placement. The store was complete at ten appearances per item, so a new
finding is placed *against the cuts* rather than by a full pairwise entry -- three comparisons was
the tool reporting the band determined, and it was. What is missing is that the exported file cannot
say which kind of row a reader is looking at.

**Why it matters more than a footnote.** D144 is the entry for what placing F-90 cost, and the
mechanism there is the same one: a new item is compared against the cut anchors, so the anchors move,
and an anchor resting on few informative comparisons moves furthest. **A consumer choosing what to
fix first sorts on `severity`**, and a band placed on three comparisons sorts beside one placed on
ten with nothing to separate them.

**What closes it** is a field in the exported schema -- appearances, informative comparisons, or an
interval -- in `comparative-judgment`, and one `cj export`. It travels naturally with item 3, since
both are additions to the same schema and both are paid for by the same re-export, **but it is not
the same claim**: a content hash says the text has not moved, and neither says the band was well
determined. Splitting them is D147's (C), taken on the owner's instruction for this row rather than
imposed across the register.

### 7. The synthesis's N repetitions measure the variance that is left once its input is fixed

`evaluate_call` renders the judged prompt **once per call** and then loops the repetitions over it.
For the six dimensions that is exactly right: the prompt is a fixed transcript, so N=10 measures
evaluator variance, which is what D17 chose N for.

The synthesis's prompt is a transcript **plus the other dimensions' results**, and those are a
sample. So its ten repetitions condition on one draw of that sample, and what they measure is the
variance remaining after it is fixed. Four runs of one call pair, three of them commissioned to test
a different hypothesis, came back **unanimous within every run and flipped between them** -- 9 or 10
out of 10 each time, in three different configurations (D150).

**A report row reading `no_material_defect x10` therefore means something different for this entry
than for the six beside it**, and nothing in the report distinguishes them. The non-determinism
caveat P4 prints is about the judged tier in general.

**What would close it** is re-rendering the synthesis prompt per repetition, so each one draws its
own inputs. That is a change to what the tier measures on the entry the whole report is read
through, and it has two costs worth stating before anyone takes it: ten renders per call instead of
one, and a prompt that differs per repetition, which ends the byte-identical-request property D17
relies on for that entry -- replay keys on `(request_hash, repetition)` and would still work, but the
*reason* the hashes are identical stops being true.

**Write the falsifier first.** The question is not whether the distribution widens -- it will -- but
whether the modal verdict moves on calls where the gold set says it should not, and D136's falsifier
is the shape for asking that before the run rather than after.

### 8. The severity tool promised bands frozen at assignment, and nothing freezes them

**Added 2026-09-12, while item 4 was closed (D156), on the owner's decision to register it.**

`comparative-judgment`'s D2 settles that scale values are derived, so a refit can move a band, and
answers it in the same sentence: bands are frozen at assignment, and a refit produces a proposed
revision for review rather than relabeling a finding the consuming harness already cites. D12 there
leans on the same rule. Nothing in that repository specifies it as a requirement or builds it, and
D144 is what the gap looks like: one placement refit the scale, and findings changed band with
nothing asking anybody.

Item 4's close does not reach it. The tool now reports how far apart each cut's anchors are and
refuses nothing for it, and this repository pins which findings lie between them, so a finding
entering or leaving a cut is noticed. A finding that stays between a cut's anchors while their
midpoint moves past it changes band with the pin unchanged.

**What would close it** is a requirement in `comparative-judgment` -- an export that would change a
band stops for the rater's acceptance -- and its build. It is the one route that stops a silent
re-banding whatever caused the refit, and the most build of the ways item 4 could have been closed.
