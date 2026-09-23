# Phase 6's contract, laid out to be read

> **READ 2026-09-20, and the contract moved.** The verdicts are inline in Part 2 and the outcome
> is in Part 3; everything else below is the contract as it was gathered on 2026-09-20 at 0.60.0 @
> D200, which is what the reading read. Phase 6 now has **5 requirements and 12 criteria** (D201 to
> D206, specification 0.61.0, and D207 after CI turned `main` red on the license criterion). Two requirements could
> not be met as written and were retargeted: the second adapter's, which asked for a stream
> byte-identical to a format this project no longer has (D203), and prompt caching's, which asked
> for something the frozen template cannot give (D204). Phase 6 joined the contract coverage table,
> which is what OB-16 asked of this phase. What the reading owes onward is in
> `sessions/HANDOVER-2026-09-20-phase-6-opening.md`.

*A working document for the contract reading OB-16 and OB-47 ask for, assembled on 2026-09-20 from
`specs/voice-agent-eval-harness.md` at 0.60.0 @ D200. Every clause below is quoted verbatim; the
line numbers are as of that version. A PDF of the same content, laid out so each comparison sits on
one page, was rendered for reading in a browser and is not committed.*

**What a contract reading is here.** Before a phase opens, its requirements and its acceptance
criteria are read against each other in both directions: every requirement should have a criterion
that would fail if the requirement were unmet, and every criterion should back a requirement. D104
did this for phase 2 and found five requirements whose criteria bought one half of each; D130 did it
for phase 4 and found four covered only in the half the requirement names, plus a deliverable
carrying no criterion at all; D157 did it for phase 5 and found its criteria covered its one
requirement while missing property (a)'s mechanism and any meaning for its weighting. The pattern is
not that the contract is sloppy — it is that a requirement and a criterion are written at different
times, for different readers, and nothing compares them until someone does.

**Why phase 6 needs one now.** `tests/test_contract_coverage.py` lists phase 6 in `UNMAPPED_PHASES`,
so nothing asserts that its criteria cover its requirements (OB-16). Phase 5 closed on 2026-09-20,
which fired OB-47's trigger: phase 6's contract reading and its session brief are what that row owes.

---

## Part 1 — Each set whole

### The four requirements, in full

> **R1** *(specs/voice-agent-eval-harness.md:187)*
> WHERE [P6] the second adapter is selected, the system SHALL produce an event stream byte-identical
> to the text adapter's output for the same call.

> **R2** *(:188)*
> WHERE [P6] prompt caching is enabled, the system SHALL place the transcript block ahead of the last
> cache breakpoint so it is shared across dimensions for a given call.

> **R3** *(:189)*
> WHERE [P6] judge-model comparison is requested, the system SHALL run the identical rubric against
> each named candidate model and SHALL report per-model agreement against the gold set.

> **R4** *(:196)*
> Error handling / observability: the system SHALL emit a run log sufficient to reproduce any judged
> result, and the log inspector SHALL assert invariants over it emitting metrics rather than scores.
> [P6]

### The four acceptance criteria, in full

> **C1** *(:229, under **happy path**)*
> [P6] The log inspector runs over a completed run log and emits its invariant metrics, including the
> proportion of retry triggers whose cited identifier exists.

> **C2** *(:230, under **happy path**)*
> [P6] Judge-model comparison reports per-model agreement against the gold set for every named
> candidate.

> **C3** *(:297, under **edge cases**)*
> [P6] The README states which license covers which tree, and links the severity tool at
> `hmbseaotter/comparative-judgment` (D20). Split from the P1 criterion above: phase 1 defers the
> README to phase 6, so the original single criterion could not pass in the phase it was tagged to.

> **C4** *(:313, under **constraint validation**)*
> [P6] With prompt caching enabled, the second dimension evaluated for a given call reports non-zero
> cache-read input tokens — asserted on a transcript known to exceed the ~1,024-token minimum
> cacheable prefix, below which a prefix silently does not cache and returns zero with nothing wrong.
> A short adversarial transcript may sit under that floor, so the fixture is chosen rather than taken
> from the corpus at random.

### The six scope bullets, in full

> **S1** *(:46)* A second adapter shaped like a real platform's call object (Retell, Vapi or
> Connect), proving the core is format-agnostic against something that exists in the world.
> Retargeted from "JSONL adapter": a JSONL format of this project's own invention would prove
> nothing, because the claim under test is that an engineer can point the harness at *their vendor's*
> logs. `specs/event-model.md` §4 carries the per-element mapping an adapter author reads, and §5 the
> contract an adapter owes — ordering, vocabulary mapping, and honest gaps.

> **S2** *(:47)* The design document, written from the decision records rather than reconstructed
> afterwards: the shared rule and the recommended implementation for a runtime guardrail, the three
> deployment cadences and the four-stage gate ladder as recommendations for a system under test, and
> the audio-layer follow-up question. Deferred here from phase 1 at D200.

> **S3** *(:48)* Deterministic log inspector — invariants over the run log emitting metrics, not
> scores.

> **S4** *(:49)* Per-instance severity, computed in code from decomposed boolean properties rather
> than scored on a scale by a model.

> **S5** *(:50)* Prompt caching on the transcript block, and a live-mode cost estimate with a call
> ceiling.

> **S6** *(:51)* Judge-model comparison — the same rubric run with candidate models, agreement
> measured against the gold set.

### The phase row, in full

> *(:347)* **phase 6 — hardening, adaptability and self-inspection**
> **Goal:** the properties a reader will test.
> **Includes:** second adapter, log inspector, per-instance severity, prompt caching, cost ceiling,
> judge-model comparison, docs routing.
> **Done when:** the second adapter produces a byte-identical event stream.

---

## Part 2 — The comparisons, one pair at a time

Each block puts a requirement beside the criteria that claim to cover it, so the two can be read
without turning a page. The **verdict** line is the reading's to write.

### R1 — the second adapter

| the requirement | the criteria that cover it |
| --- | --- |
| WHERE [P6] the second adapter is selected, the system SHALL produce an event stream byte-identical to the text adapter's output for the same call. | **None.** No `[P6]` criterion names the adapter. The phase row's *Done when* says "the second adapter produces a byte-identical event stream", which is a completion note rather than an acceptance criterion, and nothing reads it. |

- **What the requirement asserts:** (a) a second adapter exists and can be selected; (b) its event
  stream is byte-identical to the text adapter's for the same call.
- **What a covering criterion would have to fail on:** an adapter whose stream differs in ordering,
  in vocabulary mapping, or in a gap it fills silently — the three things `specs/event-model.md` §5
  says an adapter owes.
- **Verdict: not covered, and not coverable as written** (read 2026-09-20, D201, D203). No criterion named
  the adapter. More than that, the requirement could not be met by an honest source document: read on
  that day, Retell's documented call object gives a disclosure, an applied policy clause, a state change
  and a call's lifecycle no entry, and a tool call and its result no timing, so every design call's
  indices and fact citation ids shift. The owner retargeted it to *identical where carried, declared
  where not*, and it gained two criteria: the stream, and the inversion the stream's criterion cannot
  see, an adapter that reads the transcript beside its source.

### R2 — prompt caching

| the requirement | the criteria that cover it |
| --- | --- |
| WHERE [P6] prompt caching is enabled, the system SHALL place the transcript block ahead of the last cache breakpoint so it is shared across dimensions for a given call. | **C4:** With prompt caching enabled, the second dimension evaluated for a given call reports non-zero cache-read input tokens — asserted on a transcript known to exceed the ~1,024-token minimum cacheable prefix. |

- **What the requirement asserts:** (a) the transcript block sits ahead of the last cache breakpoint;
  (b) it is therefore shared across dimensions for one call.
- **What C4 asserts:** that a second dimension reads from cache, which is evidence of (b) and
  evidence *about* (a) rather than a reading of it. A prompt whose block sat after the breakpoint but
  cached for another reason would pass.
- **Verdict: cannot be covered as written** (D204). The frozen template carries each dimension's
  question in the *system* message, which a cached prefix renders ahead of the transcript, and the
  committed log holds one distinct system message per judged entry, so no prefix holding a
  transcript is shared by two dimensions and C4 had nothing to read. What the template shares is the
  request across one dimension's repetitions. The owner retargeted both clauses to that, C4 now
  asks for more cache-read tokens than the system message alone accounts for, and a second
  criterion holds the layout with no model call.

### R3 — judge-model comparison

| the requirement | the criteria that cover it |
| --- | --- |
| WHERE [P6] judge-model comparison is requested, the system SHALL run the identical rubric against each named candidate model and SHALL report per-model agreement against the gold set. | **C2:** Judge-model comparison reports per-model agreement against the gold set for every named candidate. |

- **What the requirement asserts:** (a) the rubric run against each candidate is identical; (b)
  per-model agreement against the gold set is reported for each.
- **What C2 asserts:** (b) alone. Nothing fails if one candidate is run under an edited rubric, which
  is the comparison's whole point — D186 and D197 exist because a hash is what says two runs were
  judged under the same rubric.
- **Verdict: covered in part** (D201, D202). C2 buys (b). The transport is not the gap: the request
  hash covers the model, so replay cannot serve one candidate's answers as another's. Two criteria
  were added: one rubric hash and one template hash across candidates, with a comparison over
  differing ones refused; and the tracing convention stated beside every figure, with no candidate
  ordered by false alarms, because every judged false alarm on the design set lands on a call
  carrying findings.

### R4 — the run log and the log inspector

| the requirement | the criteria that cover it |
| --- | --- |
| Error handling / observability: the system SHALL emit a run log sufficient to reproduce any judged result, and the log inspector SHALL assert invariants over it emitting metrics rather than scores. [P6] | **C1:** The log inspector runs over a completed run log and emits its invariant metrics, including the proportion of retry triggers whose cited identifier exists. |

- **What the requirement asserts:** (a) the run log suffices to reproduce any judged result; (b) the
  inspector asserts invariants over it; (c) what it emits are metrics, not scores.
- **What C1 asserts:** (b) and, by naming one metric, part of (c). Half (a) is phase 3's replay
  property, asserted there rather than here — the reading decides whether a `[P6]` requirement may
  lean on a `[P3]` criterion, or whether the requirement should be split.
- **Verdict: covered in part** (D201, D205). C1 buys (b) and one metric, and an inspector printing a
  pass or a quality figure satisfied it, so (c) gained a criterion: every value a count or a
  proportion with both terms, and an exit code that never depends on what was measured. Half (a)
  rests on phase 3's replay criteria and the requirement is kept whole, as D130 declined to move a
  requirement to suit a criteria gap.

### The criterion that backs no requirement

| the criterion | the requirement it backs |
| --- | --- |
| **C3:** The README states which license covers which tree, and links the severity tool at `hmbseaotter/comparative-judgment` (D20). | **None.** Docs routing appears in the phase row's *Includes* and in no `[P6]` requirement. The criterion exists because phase 1 deferred its README criterion here, which its own second sentence says. |

- **Verdict: backs no requirement, recorded rather than given one** (D201), as D157 recorded phase
  5's. The reading also found that no test asserted it. It has one now, after the owner extended
  D31's line to every top-level path the README's table had not named.

---

## Part 3 — Scope against the contract

Every scope bullet, and what in the contract holds it. This is the direction D130 found a whole
deliverable missing in.

| scope bullet | requirement, as gathered | criterion, as gathered | what the reading decided |
| --- | --- | --- | --- |
| S1 second adapter | R1 | — | R1 retargeted to *identical where carried, declared where not*, and two criteria: the stream, and a source naming a value outside the declared mapping aborting by name (D203) |
| S2 design document (D200) | — | — | a criterion of its own — the document exists under `specs/`, carrying its named parts — and a session of its own (D201). Unwritten: OB-54 |
| S3 log inspector | R4 | C1 | a second criterion: every value it emits is a count, or a proportion printed with its numerator and denominator (D205) |
| S4 per-instance severity | — | — | a requirement and a criterion of its own: severity computed in code from declared boolean properties, printed for every instance with no model call (D206) |
| S5 prompt caching, and a live-mode cost estimate with a call ceiling | R2 (caching only) | C4 (caching only) | R2 retargeted to the repetitions of one dimension, with two criteria, one of which needs no model call (D204). The cost estimate and ceiling were read as discharged in phases 3 and 4 (D152, D161, D170). Unbuilt: OB-52 |
| S6 judge-model comparison | R3 | C2 | two further criteria: one rubric hash and one template hash across candidates, and the tracing convention stated beside every figure (D201, D202). Unbuilt: OB-53 |
| docs routing (phase row only) | — | C3 | asserted for the first time, over every top-level path, and extended to name a license for each (D201); the check itself was corrected at D207 |

Three of the six deliverables had no criterion when this was gathered, and two had no requirement
either. All six carry one now, which is what took phase 6 from four requirements and four criteria
to five and twelve. What the reading could not close is carried as OB-51 to OB-59, and the phase's
own goal — a verdict over a vendor's log — is OB-51: no check yet reads a declared gap, so the
second adapter is selected on extraction alone.

---

## Part 4 — What the reading must produce

1. **A decision per gap**, in the shape D104, D130 and D157 used: add a criterion, add a requirement,
   or record why the deliverable carries neither. Each fork is the owner's.
2. **A `COVERAGE` entry for phase 6** in `tests/test_contract_coverage.py`, mapping each requirement
   anchor to the criterion anchors that cover it, and phase 6 removed from `UNMAPPED_PHASES` — which
   is what closes OB-16 for this phase.
3. **`MEASURED_CONTRACT` updated** in `tests/test_document_counts.py` if the reading adds a
   requirement or a criterion; it currently pins phase 6 at 4 and 4.
4. **A session brief for the build**, as `sessions/PHASE-5-COVERAGE-SESSION-PROMPT.md` was for phase
   5, naming the model and effort the owner chooses.

## Part 5 — What must be settled before criteria are written

- **OB-49 — whether a finding may be traced to entries of both tiers.** Judge-model comparison
  measures agreement against the gold set, and the gold set's traces run within one tier: 64
  deterministic-to-assert and 19 judged-to-judge, with none across. Under that convention a judge
  catching an assert-type finding scores a false alarm. Whatever phase 6's criteria say about
  agreement inherits it, which is why the register makes this due at the opening reading.
- **OB-7 — what closes `JUDGED_AGREEMENT_PENDING`**, now that held-out agreement is measured and
  never committed (D175).
- **P5-9's single difference**, recorded in OB-49's row: the family tables and agreement's expected
  calls disagree on one entry-call pair, by the same convention inside one tier.
- **OB-50 — D83's reach statement**, owed wherever a held-out result is published.

## Part 6 — Reading it

Nothing in this document is a decision. It is the contract gathered into one place: the sets whole in
Part 1, the pairs side by side in Part 2, the deliverables against both in Part 3.

The gaps named above are what assembling it made visible; a reading is entitled to disagree with each
of them, and the point of quoting every clause verbatim is that it can.

## Part 7 — The reading, as it ran

*Added 2026-09-20 by the session that ran it. Parts 1 to 6 are left as gathered, and quote the
clauses as they stood at 0.60.0; the specification at 0.61.0 carries them as decided.*

The verdicts are written into Part 2 above. Part 3's gaps were decided as follows, each by the owner:
per-instance severity gained a requirement and a criterion and the design document a criterion;
docs routing stays without a requirement; and the second half of S5, the cost estimate and the call
ceiling, is recorded as built at phases 3 and 4. Part 5's questions are D202's, except OB-50, which
this reading did not touch and which stays open. Part 4's fourth item, a brief for the build, was
`sessions/PHASE-6-SESSION-PROMPT.md`; what is still to build is briefed by
`sessions/HANDOVER-2026-09-20-phase-6-opening.md`. Decisions D201 to D206.
