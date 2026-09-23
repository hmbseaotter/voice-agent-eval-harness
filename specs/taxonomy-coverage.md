# Taxonomy and known-weakness coverage map

> **Scope, as of 0.20.0.** Every disposition below is against the inherited 35-item taxonomy and
> the W1–W35 list, both mapped before the error-type sweep. That sweep added classes the
> taxonomy does not enumerate at all — idempotency, retrieved-data injection, authentication
> factor strength, AI-status disclosure, delivery state — so **the tallies here describe the
> taxonomy's coverage and not the corpus's** (D66). The added classes are recorded in
> `specs/error-type-sweep.md` and mapped in **Part 2b** below, which carries its own
> identifiers rather than renumbering the inherited 35.

**What this is.** The corpus seeds defects from a 35-item failure-mode taxonomy, and the build is
guided by a 35-item list of known weaknesses in a prior reference implementation. Until this file
existed, neither list appeared in this repository: the specification referenced three taxonomy items
by number and one W-number, and nothing recorded what the other sixty-six were or whether they were
handled. A phase-1 corpus could have covered fifteen of thirty-five and nobody would have known.

**Why it is self-contained.** Every item below is stated in enough detail to act on without reading
the source document. That is deliberate — a builder should not need to open the reference to author
a transcript, and the two lists are the only part of it phase 1 actually needs.

**Status of the two lists.**

| | |
|---|---|
| Taxonomy | 35 numbered failure categories, plus a 10-pattern causal layer (P1–P10). Already generalized at source: no transcript text, no identifiers, no figures. |
| Known weaknesses | W1–W35, defects measured in a prior implementation. **Not requirements** — a post-hoc diff checklist. The governing rule is: *if your implementation differs from the reference at a point on this list, the reference is probably the wrong one.* |

**How to read a disposition.**

- **SEEDED** — a design-set transcript must carry this defect. Phase 1 owes it a scenario.
- **CHECKED** — a rubric entry detects it. The named tier and dimension say which.
- **DEFERRED** — consciously out, with the reason. Not an oversight.
- **GAP** — neither covered nor consciously deferred at the time of writing. Each one names what would close it.

---

## Part 1 — the causal layer (P1–P10)

Ten recurring mechanisms, each with a hypothesis about *why* the failure happens, ordered by blast
radius rather than count. This layer is what turns a findings list into an analysis, and the report
design should reproduce it: the specification's two-audience report split (agent-behavior versus
data/integration findings) is the beginning of it, not the whole.

| # | Pattern | Mechanism | Disposition |
|---|---|---|---|
| P1 | Fabricated completion — the agent states something was done when the call failed, has not run, or does not exist | The spoken turn is not conditioned on the tool result; "I called the tool" and "the tool succeeded" are treated as one event | **SEEDED + CHECKED** — Tier A claim-integrity |
| P2 | Tool errors change nothing the agent says next | No error branch and no error taxonomy: nothing separates a fixable precondition failure from hard ineligibility from environmental unavailability. This is the mechanism *behind* P1 | **SEEDED + CHECKED** — Tier A |
| P3 | Authentication absent, disclosure ungoverned — a caller-ID-style identifier treated as a credential | A verification gate protects one write action and no disclosure at all. The asymmetry is the tell | **SEEDED** — needs a check; see taxonomy 15, 24 |
| P4 | Grounding failures against retrieved data — facts in hand restated wrongly, policies no tool supplied asserted as fact | Retrieved values paraphrased rather than substituted; grounded and ungrounded claims arrive in one register | **SEEDED + CHECKED** — judged: policy groundedness |
| P5 | Guardrails enforced inconsistently across flows | Compliance implemented per-action rather than as a shared pre-action layer; the guarantee is only as strong as the least careful flow | **SEEDED** — detection is cross-corpus, DEFERRED with taxonomy 13/16/25 |
| P6 | Dialogue state does not commit — a filled slot is re-requested; a confirmation demanded repeatedly | The confirmation received is not written to the state then read. No loop detection, no escape hatch, so the failure is unbounded | **SEEDED + CHECKED** — Tier A state-versus-action |
| P7 | Unmanaged latency and dead air | No holding phrase, filler, heartbeat or timeout. On a voice channel a long enough silence is functionally a dropped call | **SEEDED** — checkable from timestamps; see taxonomy 32, 33 |
| P8 | Outcome and reason labels disagree with the event log | Whatever derives the labels is not reading tool results either. These fields cannot serve as eval labels, sampling criteria or regression signal | **SEEDED + CHECKED** — Tier A metadata-versus-log |
| P9 | Data-layer contradictions independent of the model — one record with two values, impossible timelines, naming drift | Integration and fixture defects, not model behavior. They set a **ceiling on grounding**: an agent cannot be more correct than the data it was handed | **SEEDED** — routed to the data/integration audience of the report |
| P10 | No graceful degradation; the correct fallback is present in the payload and never offered | No designed unhappy path. The agent's only two modes are success and pretending | **SEEDED + CHECKED** — judged: fallback appropriateness |

> **Authoring note.** P9's "ceiling on grounding" is the reason the corpus needs at least one
> deliberate data-layer contradiction that the agent could not have spoken correctly. Without it the
> report's data/integration audience has nothing to read, and the grounding dimension's ceiling is
> asserted rather than demonstrated.

---

## Part 2 — the 35 failure categories

### Truthfulness and grounding

| # | Category | Disposition |
|---|---|---|
| 1 | **Doubling down under correction.** Given an explicit correction from the caller, the agent restates the wrong fact and manufactures a plausible justification rather than re-reading the payload. Distinct from the original fabrication and arguably worse — a confident, coherent explanation of a wrong fact is not flagged by the caller or by an automated check | **SEEDED + CHECKED at P4** — caller-pushback understanding. Recorded as a GAP through P3, with the note that closing it meant either an eighth dimension or an explicit deferral; D133 took neither, and widened judged dimension 4 instead. Its original wording keyed on a reversal or transfer *following* the objection, and the design set carries one reversal which the seeding manifest records as correct — so that dimension had a negative instance and no positive one, while this item had seeded findings and no dimension. One entry covers both, tracing F-37 and F-86, with CALL-20 as the negative instance. **What is claimed here is coverage by the entry's criteria, not agreement**; whether a judge catches them is what a live run answers |
| 2 | **Grounded and ungrounded facts interleaved in one sentence.** A figure traceable to a system variable and one traceable to nothing, delivered in the same breath and the same register | **SEEDED + CHECKED** — policy groundedness |
| 3 | **A claim anchored to a field absent from the payload.** A deadline stated as running from a reference event the record carries no field for. The value may look reasonable; the *anchor* is ungrounded | **SEEDED + CHECKED** — policy groundedness. Worth a distinct scenario from 2: the check shape differs |
| 4 | **A policy assertion with no retrieval behind it at all.** Not a misstated fact — a categorical business-rule claim with no lookup anywhere in the call. It may be correct; nothing makes it checkable | **SEEDED + CHECKED** — policy groundedness. This is why the reference policy documents are a P1 deliverable |
| 5 | **Arithmetic self-contradiction inside one spoken disclosure.** Two deductions described so the net result is arithmetically undefined, with no final figure spoken. Distinct from a wrong number: no number is derivable | **GAP.** Deterministic and cheap. Closing it is one Tier A check |

### Verifiability to the caller

| # | Category | Disposition |
|---|---|---|
| 6 | **Unverifiable confirmation — no anchor the caller can check.** Confirming against "the details on your account" names nothing, so a stale address or wrong payment instrument passes undetected and consent to a *specific* instrument cannot later be evidenced | **SEEDED + CHECKED** — disclosure clarity |
| 7 | **No spell-back of a voice-captured new high-consequence value.** Distinct from heard-value reconciliation, which only fires when a corresponding on-file value exists. When the value is genuinely new there is nothing to reconcile against, so read-back is the only mitigation — and a single recognition error is undetectable to both parties until downstream delivery fails | **GAP, and a deliberate one to close.** The source records that the prior implementation explicitly excluded it. Ticketing supplies it naturally: a new email for ticket delivery, a name change on a transfer |
| 8 | **A relative reference never normalized to an absolute value.** A relative day or quantity confirmed repeatedly but never resolved, spoken or recorded, so no downstream system could act on it | **GAP.** Deterministic. Ticketing is rich in these — "the day before the show" |

### Request handling

| # | Category | Disposition |
|---|---|---|
| 9 | **Silent partial fulfillment.** A multi-part request narrowed to one part with no acknowledgement the rest was dropped. Also appears as a *qualifier* silently dropped from a lookup | **SEEDED + CHECKED** — intent satisfaction, relevance/scoping |
| 10 | **No feasibility or eligibility check before engaging.** Distinct from a declared precondition erroring — here no check is made. The system state already indicated the request was impossible and the agent spent the call confirming something it could not do | **SEEDED + CHECKED** — fallback appropriateness |
| 11 | **Explanatory context withheld.** The one fact that would have made a refusal comprehensible was in the payload and never mentioned | **SEEDED + CHECKED** — disclosure clarity |
| 12 | **Answer completeness varies across calls for the same intent** | **DEFERRED** — cross-corpus family, named in `out of scope`. The corpus is paired to support it later |

### Controls and consistency

| # | Category | Disposition |
|---|---|---|
| 13 | **One logical control under divergent names with divergent enforcement.** The same obligation as two or three differently-named variables across flows, with three enforcement behaviors including "not enforced" | **DEFERRED** with the cross-corpus family. Seed it anyway: the variables must exist in the corpus for the later check to have anything to find |
| 14 | **Inconsistent confirmation gating on irreversible actions.** One flow confirms before an irreversible write; another performs a destructive write with none. *The destructive one is the ungated one* | **SEEDED + CHECKED** — Tier A. Ticketing's irreversible writes: transfer, name change, refund |
| 15 | **Security theater — a verification step that collects input, sets no state and gates nothing.** The agent asks for a credential it already had, the state variable never changes, nothing is gated on it | **SEEDED + CHECKED** — Tier A state-versus-action; see 24 |
| 16 | **Cross-call inconsistency in required disclosure language** | **DEFERRED** — cross-corpus family, named in `out of scope` |

### Posture and boundaries

| # | Category | Disposition |
|---|---|---|
| 17 | **Claiming authority beyond the system's visibility boundary.** Contradicting a caller's account of an external system — a processor, a bank, a carrier — on the strength of a local field that cannot see it. Both likely wrong *and* the wrong posture on a dispute | **GAP.** The source calls it subtle enough to deserve its own judged dimension: *does the agent's confidence exceed what its data sources can support?* |
| 18 | **Explicit frustration or distress cues produce no change of path** | **SEEDED + CHECKED** — sentiment handling. Note the source records this dimension was once built with *no backing finding*; seed it so this corpus does not repeat that |
| 19 | **Deflecting an explicit request via a lookup.** Defensible when the capability exists and the agent might resolve it; not defensible when the agent already knew the request could not be satisfied | **SEEDED + CHECKED** — relevance/scoping |

### Data and specification hygiene

| # | Category | Disposition |
|---|---|---|
| 20 | **Reference-data naming drift that breaks automated matching.** The same catalog entity under two names across calls | **CONSTRAINT ON THE HARNESS, not only a seeded defect.** The source flags it as a prerequisite: *any automated check matching spoken entity names against catalog entries needs this resolved first.* Phase 1 owes a single canonical name per entity in the corpus, and may then seed drift deliberately in one call |
| 21 | **Specification gaps surfaced by the data.** A component that is either a deliberate product decision or a missing implementation, indistinguishable from the transcript — e.g. a total with no tax component, internally consistent, which would make every spoken total wrong once added | **SEEDED + CHECKED** — this is what `tier: question` in the findings document is for, and why `not_applicable` and `unevaluable` are separate |
| 22 | **Missed actionable state.** The agent invents a value rather than surfacing the real actionable state that was available | **SEEDED** — minor alone; notable for what it says about P4's mechanism |

### Action and state

| # | Category | Disposition |
|---|---|---|
| 23 | **Fabricated *in-progress* state.** Distinct from a fabricated *completed* action: the agent narrates an ongoing operation never initiated, sustained across turns with repeated reassurance, while an availability flag already showed it was impossible. The check differs — it asserts progress language is accompanied by a *pending* operation in the log | **SEEDED + CHECKED** — Tier A. The source calls this the highest-cost variant on a real-time channel, because harm compounds per turn |
| 24 | **A gate reports success while its governing state was never recorded.** Distinct from a precondition erroring and from a control that gates nothing: the action *succeeds* while the consent variable stays unset. Either the condition was met and not recorded, or the gate was not enforced — both are defects, so it files confidently without disambiguating | **SEEDED + CHECKED** — Tier A. The source calls it cheap and high-yield |
| 25 | **A control whose passing state is never reachable anywhere in the corpus** | **DEFERRED** — cross-corpus reachability, named in `out of scope`. Seed the failing states so the later check has a corpus to run on |
| 26 | **Sequencing defects where every step is correct but the order is wrong.** A confirmation placed *after* a failed attempt; an eligibility query issued only after the outcome was announced. Each step exists and is well-formed; the order means the check cannot influence the action | **GAP, and it is also W2's fix.** Assertable as an expected-order property over the event log. The source recommends it as a check family for the deterministic tier explicitly |
| 27 | **Multi-stage assembly where a later stage silently drops a mandated fragment.** A compliance-bearing utterance composed in two stages, the second overwriting the first, the required disclosure living only in the first — so the omission originates in *configuration* and is invisible from the spoken transcript alone | **GAP.** Worth seeding specifically: it is the one class needing a check that compares **two different fact sources** — configured default versus delivered output — which nothing else in the corpus exercises |

### Request handling and design

| # | Category | Disposition |
|---|---|---|
| 28 | **Deflecting an in-channel task to another channel when the agent could have completed it.** The caller is live, yet is routed to a link or form for something the system could have done on the call. Distinct from deflecting via a lookup, and from a missing capability: here the capability exists and is not used | **GAP.** The source names the judged dimension it implies: *could the stated next step have been performed in-channel?* |
| 29 | **Reactive rather than proactive orchestration.** Context known before the interaction is not prefetched; retrieval starts after the caller states intent and the caller waits | **DEFERRED** — architectural rather than model behavior, and there is no live system under test. Record as a stated coverage gap |

### Posture

| # | Category | Disposition |
|---|---|---|
| 30 | **Caller assertions contradicting system records, as first-class recordable events.** A dispute should be captured as a structured record rather than talked past. Across a corpus, several contradictions pointing in *opposite* directions are evidence about the backing data systems rather than about any turn | **GAP** for the single-call half; the corpus-level half belongs with the cross-corpus family. Gives the agent a designed behavior for a situation that otherwise has none |

### Data, instrumentation and specification

| # | Category | Disposition |
|---|---|---|
| 31 | **External-world plausibility — where a judge genuinely beats a deterministic check.** Some data defects are internally consistent and detectable only against real-world knowledge: a named third-party service whose actual characteristics cannot support the timings the record asserts. No internal-consistency assertion catches it, because nothing in the payload disagrees with anything else | **SEEDED at phase 1 (CALL-05), finding F-52** — and seeded twice, which is the instructive part. CALL-02's F-10 held this category until policy retrieval began returning whole documents: once `refund.v1` § 3.2 was in the payload, something in the payload *did* disagree with the claim, F-10 became assertable, and the category was empty without anything saying so. The replacement is a claim about the settlement path rather than about a transaction, so no clause, result or state event bears on it. It remains the distinct, defensible reason to spend a model call beyond intent/relevance/tone/groundedness. **Authoring constraint:** the substituted third party must be a real-enough service class with invented specifics, or an invented service with stated characteristics; a wholly invented name with no stated properties makes the category unjudgeable |
| 32 | **Call-lifecycle instrumentation as a checkable surface.** Three cheap deterministic checks over *metadata* rather than content: whether end-of-interaction events are emitted consistently; whether header duration reconciles with the logged timeline; and who terminates the interaction, since a system that hangs up promptly reads as abrupt on voice | **GAP.** Inconsistent event emission is precisely the condition that lets real failures go unlogged — the oracle-completeness precondition. Cheap to seed and cheap to check |
| 33 | **A property you intend to gate on may be unmeasurable from the available instrumentation.** Timestamps marking only the *start* of an utterance make agent-side latency impossible to compute: the observable gaps conflate speech duration, processing and caller think time. The correct output is a finding **against the telemetry schema**, not a guessed measurement | **SEEDED at phase 1 (CALL-12), by a different instance than originally planned.** D33 proposed carrying one timestamp per event so latency would be unmeasurable — on the premise that start-stamped logs are what real systems emit. **That premise was checked at v2 and is false**: platforms carry turn start and end, word-level timing and separate STT/TTS windows, so D33 is superseded by D40 and the format now carries both. The category survives by an honest instance instead: event boundaries make a silence *computable* but not *attributable*, because no audio layer sits behind this corpus, so a gap cannot be divided into model latency, tool latency and caller think time. Finding F-49 |
| 34 | **Single-valued outcome labels are structurally insufficient.** Beyond labels being wrong: one value cannot express an interaction that failed in several independent ways. The fix is orthogonal labels — resolution state, which capability was unavailable, which team must act | **CHECKED, and adopted.** The report's orthogonal labels are a P4 deliverable. Note the source's point: this is a schema recommendation **the harness's own report should follow too**, not only a criticism of the system under test |

### Voice-channel specific

| # | Category | Disposition |
|---|---|---|
| 35 | **Personalization is a voice-channel risk, not a neutral nicety.** Speaking a personal name puts a proper noun through recognition and synthesis, where mangling is most likely and most alienating across diverse populations — and personal names carry no reliable signal about how someone should be addressed. The mitigation is a channel-level policy decision | **DEFERRED** — audio-layer testing is out of scope; the defect lives in layers a text transcript cannot show. Worth naming in the design document as a worked example of *why* the audio layer is excluded, which is stronger than excluding it silently |

### Tally

*Updated at the end of phase 1's corpus authoring. The dispositions above were written before the
corpus existed; where one has moved, the tally below is the current state and
`specs/taxonomy-scenario-map.md` is the authoritative allocation.*

| Disposition | Count | Items |
|---|---|---|
| SEEDED + CHECKED | 15 | 2, 3, 4, 6, 9, 10, 11, 14, 15, 18, 19, 21, 23, 24, 34 |
| SEEDED, check deferred | 2 | 13, 22 |
| **SEEDED at phase 1, check gap remains** | **12** | **1, 5, 7, 8, 17, 26, 27, 28, 30, 31, 32, 33** |
| DEFERRED with a reason | 5 | 12, 16, 25, 29, 35 |
| Harness constraint | 1 | 20 |
| **GAP — neither seeded nor consciously deferred** | **0** | — |

**All twelve gaps are now seeded, and seeding is not checking.** The distinction is the whole point
of the middle row and is stated again in the scenario map's Part 4, because it is the thing most
likely to be lost: a defect present in the corpus is not a defect the harness detects.

Of the twelve: **five** are cheap deterministic checks the corpus can now carry with no new
dimension (5, 7, 8, 26, 32) — 7 is the spell-back gap, and it belongs here rather than in a bucket of
its own, which is where an earlier version of this paragraph left it by naming it after the count
without classifying it. **Two** are inside the judged tier D42 settled on (17 and 31, its items 6 and
5). **Two** implied a judged dimension the specification did not have (1 and 28); D133 closed item 1 at P4 by widening judged dimension 4 rather than adding an eighth, as its row says, and 28 stands — D35 records
what each would ask, why a deterministic check cannot answer it, and what the corpus already carries
for it. **Three** are structural observations worth a finding rather than a check (30, 33, and 27's
configuration half). Five plus two plus two plus three is twelve.

Item 7 is worth one further line: it was explicitly excluded by the prior implementation, so
including it is a visible improvement rather than parity.

**Why seed what cannot yet be checked.** Seeding a defect during authoring costs a few lines; adding
one afterwards means re-authoring a transcript, re-extracting, and invalidating any findings already
adjudicated against it. Phase 1 was the only cheap moment, and it has passed.

---

## Part 2b — classes the 35-item taxonomy does not enumerate

**Why this is a section and not ten more rows** (D66). The 35 categories in Part 2 are an inherited
analysis, and their numbering is how every other document in this repository refers to them.
Renumbering that list to absorb classes found later would misrepresent where those classes came
from, and would silently change the meaning of "taxonomy 17" in five other files. So these carry
their own identifiers, `S1`–`S11`. The `S` is for the sweep that found most of them
(`specs/error-type-sweep.md`); **S11 arrived later, at D73**, from that sweep's own list of
what it had left uncovered.

**What they are.** A systematic pass over 141 catalogd voice-agent failure modes, run against all
70 findings the corpus then held. Roughly 45 were already expressed, about 25 are structurally
inapplicable to a text corpus with no audio layer, and the classes below are what survived a
three-part test: the corpus could not express it, it contributed a **detection shape** the corpus
lacked, and it fit a call at or below 0.35 findings per event or justified a new call.

**Dispositions read differently here than in Part 2.** Every one of these is **seeded**, because a
class earned its place only by being seeded. What none of them has is a *check*, and that is not a
gap peculiar to them: **phase 1 builds no Tier A checks at all**. So the disposition column records
what a check would have to be — deterministic, judged, or neither — which is the same question Part 2
asks and the same answer format, against a phase that has not started.

| # | Class | Disposition |
|---|---|---|
| S1 | **Idempotency.** A hard refusal retried unchanged, and a timed-out write with no deduplication key — the two halves of "the same action attempted twice". `issue_refund` is called three times with identical arguments after a refusal that cannot change | **SEEDED, deterministic check owed to P2.** CALL-05, F-53 and F-54. Both `assert`: repeated identical arguments after a terminal status is a comparison over the event stream. F-54 is `question` tier — whether a write that timed out was applied is not answerable from the transcript, which is the finding |
| S2 | **Injection arriving in retrieved data.** The corpus already seeded injection in caller speech; this is the same payload reaching the agent through a tool result, where "untrusted" is less obvious and the delimiting rule is the same | **SEEDED, judged.** CALL-08, F-55, `owner: data`. Deliberately `judge`: whether the agent treated retrieved content as instruction is a reading of its reply, not a comparison. The design-set pair for the P3 injection criterion is the caller-speech one; this is its retrieved-data counterpart |
| S3 | **Authentication factor strength.** A spoofable identifier plus one knowledge factor, treated as verification. Not a defect of the call — a property of the verification design the corpus uses throughout | **SEEDED, human.** CALL-03, F-56, `question` tier. The one class here that a check should *not* try to answer: ANI plus ZIP is a design decision to be argued with, and recording it as a question is what the `question` tier exists for |
| S4 | **AI-status disclosure recorded but not delivered.** The context record carries `disclosure_ai_status` while no `ai_status` DISCLOSURE event occurs — and when the caller asks outright whether they are speaking to a person, the reply addresses the booking instead | **SEEDED, split.** CALL-12, F-57 (`assert` — a record claiming a delivery the event stream does not contain) and F-58 (`judge` — whether a reply that does not deny is an answer). The split is the point: the configuration half is countable and the conversational half is not |
| S5 | **Delivery state versus acceptance.** A provider accepting a message is not a recipient receiving it, and a record that says `sent` collapses the two. The agent then tells the caller it has arrived | **SEEDED, judged and human.** CALL-11 and CALL-12, F-59 and F-60. F-59 is `human`/`question`: whether the platform *should* record acceptance as delivery is a schema argument, not a call defect. Nothing here is `assert`, because the transcript cannot distinguish the two states — which is the finding |
| S6 | **Termination etiquette.** Who ends the interaction, and whether the log says so. `agent_hangup` in two calls, one of them with no `call.ended` event at all | **SEEDED, deterministic check owed to P2.** CALL-05 and CALL-12, F-71 and F-72, both `assert`, both `owner: platform`. **This class is why the sweep was worth running**: the defect had been seeded, pinned by a test constant and described in the seeding manifest, with no finding anywhere. Every mechanism was green |
| S7 | **One reason code for a call that completed two actions.** The vocabulary has room for one outcome reason and the call performed two writes, so the record names whichever the author picked | **SEEDED, deterministic check owed to P2.** CALL-03, F-73, `assert`, `owner: platform`. A count of successful writes against a single-valued field |
| S8 | **A reason code naming an action the call never performed.** The converse of S7, and the sharper one: not an incomplete record but a false one | **SEEDED, and this one has a corpus-side check today.** CALL-09, F-74, `assert`. `test_every_action_reason_code_names_an_action_the_call_attempted` asserts the property over the corpus; the *harness* check that detects it in an evaluated call is still P2 work. The distinction is the same one Part 2's tally draws |
| S9 | **Over-disclosure under pressure.** A caller who is not the account holder, helped too much: no verification, bypass reasoning spoken aloud, an internal field read out, payment data volunteered, delivery redirected, a gate enforced in one flow and absent in another, and a successful call filed as abandoned | **SEEDED, split, new call.** CALL-18, F-75–F-81. Five `assert`, two `judge`. Inexpressible in the corpus before this call existed — every other caller is the account holder, so a bypass has nowhere to happen. `test_no_internal_field_reaches_the_caller` covers one of the seven on the corpus side |
| S10 | **Time, zone and scheduling arithmetic.** A zone conversion off by a day, a reschedule timeline that cannot happen, a policy anchored to a field the record does not carry, and false assurance under direct challenge | **SEEDED, split, new call.** CALL-19, F-82–F-86. Mixed `assert`, `judge` and `human`. The zone conversion is the cleanest deterministic case the corpus carries — two timestamps and a stated day, all three in the log |
| S11 | **Escalation, and what survives the handoff.** A dispute no policy covers, correctly routed to a human — and then handed over with no account of why, and with nothing linking this call to the record the specialist opens | **SEEDED, mixed. Not from the sweep** — added at D73, after the sweep's own owed list named escalation as its strongest remaining candidate. CALL-20, F-87–F-89: two `assert`, one `judge`, all `owner: agent`. **The class the corpus most lacked**: every other call in the set is about what an agent said and did *inside* a call, and this is the only one about what the next actor receives, or whether the call can be found again from outside it |

### Tally for Part 2b

| Disposition | Count | Classes |
|---|---|---|
| SEEDED, deterministic check owed to P2 | 4 | S1, S6, S7, S8 |
| SEEDED, judged tier | 1 | S2 |
| SEEDED, mixed — split across tiers by finding | 5 | S4, S5, S9, S10, S11 |
| SEEDED, human question by design | 1 | S3 |
| **GAP — neither seeded nor consciously deferred** | **0** | — |

**Read this tally next to Part 2's, not merged into it.** Part 2 measures an inherited 35-item
taxonomy against a corpus; this measures a corpus against classes found by sweeping it. The two
denominators are different and adding them would produce a number that means nothing. What both say
is the same thing: **seeding is not checking**, and no Tier A check exists yet for either set.

**What remains uncovered after the sweep** is recorded in `specs/error-type-sweep.md` rather than
here — concurrency and stale reads, account enumeration, authentication lockout, abuse handling,
jurisdictional drift, and cross-call answer-completeness variation. Each names why it was not seeded.

---

## Part 3 — known weaknesses W1–W35

Grouped as the source groups them. **These are not requirements.** They are what to diff against
after building, and the rule is that a difference favors the new implementation.

### Already addressed by a requirement

| W | Defect | Where it is handled |
|---|---|---|
| W1 | The citation validator built its citable set from conversation turns only, while established facts rendered tool calls and variables in the *identical* `[line N]` syntax — the two populations completely disjoint, so every established-fact line was uncitable by construction. The "hallucination detector" never caught a hallucination; both observed citation failures were this bug, and the informed retry was built to fix a validator defect | Requirement: tag `[T<n>]` and `[F<n>]`, validator accepts the union, each validated against its own set. **The general lesson is the durable part: a validator must validate against the same universe the prompt renders** |
| W11 | `not_applicable` was the fail-open default at gate level, and also absorbed "a dimension applied but no ground truth existed" — so a parser regression could convert the whole absolute-gate tier to PASS with no alarm | The five-value status channel splits the states; `unevaluable` is separate; `refused` was added later for the same reason (D23) |
| W12 | The evidence-on-failure invariant covered two verdict strings and missed the negative pole of six of seven scales | Requirement drives the guard from the entry's **declared scale**, not a literal tuple |
| W13 | The roll-up's absolute-gate test was keyed to the literal string `"fail"`, so declaring a judged dimension an absolute gate was a silent no-op | Rubric validation rejects `tier: judge` with `gate: absolute` by name. **The silent no-op is not a bug to be fixed by making that combination effective** — the combination is forbidden, because an absolute gate must never depend on a live model call. This read "do not make judged absolute gates work" until 2026-09-07, which named a category the rule exists to deny: a dimension has a `tier` and a `gate`, and it is the *pairing* that cannot exist, not a kind of gate. Once it has a name, making it work sounds like an option |
| W14 | Nothing validated a verdict against its entry's declared scale anywhere | Requirement raises naming the entry and the offending verdict |
| W15 | Tool status was an opaque token compared case-sensitively in three places with no vocabulary validation — a live risk when the corpus is freshly authored | Closed tool-status vocabulary in the format spec; extraction aborts naming file, line and token |
| W18 | Metadata lines with unexpected characters were silently discarded, with no unparsed-line counter | Requirement: increment a counter, report non-zero as a failure |
| W20 | `params` were decorative for the entire deterministic tier — only the entry `id` was read, everything else hardcoded, in one case disagreeing with the YAML. Undercut the headline claim, for the tier a reader studies first | **Built at P2.** `ParamView` records every key a check reads and the engine raises `UnreadParameterError` naming the entry and the keys it left unread (D109). Its residue is recorded rather than closed: reading is not using, so the parameters of `A-available-value-never-spoken` that no design call reaches move no verdict, and a test holds that list so it fails when the gap is closed without being recorded |
| W21 | `threshold` and `severity` were consumed by no logic and no rate was computed anywhere | **Built at P2.** `EntryRollup.pass_rate` computes over `applicable` results and `gate_failed` compares it against the entry's declared `threshold`; the other statuses are printed beside the rate rather than folded into it |
| W22 | No rubric schema validation — a missing gate or duplicate id surfaced as a `KeyError` deep in the roll-up | **Built at P2.** `load_rubric` raises `RubricSchemaError` / `RubricError` naming the entry, and D116 extends the same discipline inside a check: a source declaring a match mode nothing implements is refused by name where it is declared, not where it is used |
| W25 | No exception handling on the model path, no retry or backoff; nothing written until every call completed, so a failure on the last call discarded every call already paid for | Requirement: backoff to a declared maximum, **and persist results already obtained before any abort** |
| W26 | No supported way to run the deterministic tier alone; any full-rubric invocation made live calls | **Built at P2.** `harness run --tier assert` selects the deterministic tier, asserted over a fixture rubric declaring both tiers rather than over the shipped one, which declares no judged entry (D108) |
| W29 | Model text interpolated into Markdown tables unescaped; the shipped report already contained corrupted rationale tails nothing detected | Requirement: escape before rendering |
| W30 | No run provenance — no run id, no rubric version stamp, no raw-response capture, no record a retry fired. The practice of diffing two runs was not executable against what it emitted | **Half built at P2.** `Provenance` stamps rubric version, corpus version and artifact hash on every result, refuses a blank field, and the run reports how many results lack one. The model-call log is P3's, and there is no model call to log yet |
| W32 | Prompt-injection surface unmitigated — raw speech spliced into the judge prompt in the same syntax the model was asked to cite. Treated injection only as something to test the *agent* with, never as a threat to the judge | Requirement: delimited untrusted block, stating no instruction inside is authoritative |
| W34 | No `.gitignore`, tests, README or LICENSE | All P1 deliverables with criteria |
| W35 | `requirements.txt` stated floors and called them pins, in a project whose thesis is reproducibility | Constraint plus criterion: `uv.lock` pins exact versions, no dependency expressed only as a floor |

### Consciously deferred

| W | Defect | Disposition |
|---|---|---|
| W27 | The report generator re-executed the entire judged tier on every invocation — a second full spend, with results that could differ from the run just inspected | Replay is the default mode, so reporting spends nothing. **DEFERRED**: no explicit requirement forbids re-execution; replay makes it structurally unattractive rather than impossible |
| W28 | No prompt caching; the transcript re-sent per dimension, the largest avoidable input cost | **DEFERRED to P6**, named in scope |
| W33 | Dead code shipped beside its replacement, with the inventory pointing readers at the wrong module | **N/A** to a fresh build. Worth one line in the design document as a hygiene lesson |
| W24 | The report generator shelled out to a Unix `date` binary; worked only because Git-Bash was on PATH. The comment rationalized it as "real wall-clock time from the OS, not guessed" — a sound rule reaching for the wrong mechanism | **N/A** — but the *lesson* is worth keeping: a correct principle can select an incorrect mechanism, and the reader is taught the wrong thing either way |

### Retired by the deterministic tier

**This was the substantive finding of the coverage check, and it is now a closed one.** W2–W10 are
nine *measured* correctness defects in the reference's deterministic tier. The specification says
"Tier A deterministic checks, every parameter read from the rubric entry" and says nothing about the
failure modes those checks must avoid. Seven of the nine are false *passes* or false *failures* on an
absolute gate — the tier that fails the whole run.

**Ticked at P2 and after, row by row, under this section's own maintenance rule.** Phase 2 built the
checks and ticked nothing; the rows were decided by a session cleared to review the rubric, because
whether a check retires a W is a judgment about what the check does rather than a bookkeeping step.
Each cell below names the check and the test, and says which kind of evidence stands behind it: a
verdict the design corpus itself produces, or a fixture. **Where it is a fixture the cell says so**,
because a defect closed only against a fixture is closed against something other than the corpus the
tier is scored on.

| W | Defect | Where it is handled |
|---|---|---|
| W2 | Claim-integrity ignored event ordering — it looked for a matching success *anywhere* in the call, so it could not distinguish "announced completion after the tool returned" from "announced completion before the tool was invoked". That distinction is the motivating defect, and the sibling error-check *did* compare indices | `completion_claim_without_successful_write` compares the claim's index against the invocation's. **Corpus evidence:** CALL-09 announces the exchange at event 12 and it succeeds at event 20, and `test_w2_a_claim_before_the_action_is_a_violation_even_when_it_later_succeeds` requires `unsupported`. Its companion turns the ordering rule off and requires that call to pass, so the rule is what produces the verdict |
| W3 | Claim→action mapping resolved multiple candidates by **disjunction** — two similarly-named actions, one succeeding and one failing, produced a false pass on an absolute gate | A topic resolving to more than one invoked tool returns `unevaluable` naming both, never a disjunction. **Fixture:** no design call is ambiguous, so `test_w3_a_topic_resolving_to_two_invoked_tools_is_unevaluable_not_disjoined` declares the ambiguity in the rubric to reach the branch |
| W4 | The claim detector matched confirmation questions — "are you all set?" classified as a completion claim, failing a gate when no matching action existed | Phrase lists rather than word lists, with `excluded_signals` consulted first so a confirmation question cannot be rescued by containing a claim signal. **Corpus evidence:** `test_a_word_list_would_have_fired_on_three_turns_a_phrase_list_does_not` measures the rate the word list would have had, over the design set. The same shape one layer down is D116: a spoken figure is a candidate only when a declared cue follows it |
| W5 | Word-boundary matching let a spoken figure ground against a *longer* payload figure sharing its integer part, because the decimal point is a non-word character | **Three places, and one tick would be wrong for two of them.** In the tier's numeric arm the comparison is by decimal value, so `22` cannot ground against `22.50` and no boundary is involved. In the `literal` arm and in every signal list the boundary is D115's, which closed a live collision: CALL-18 says `00461` aloud and `"461" in spoken` was true. The digits-and-separators boundary the row describes lives in `grounded` under `MatchMode.SUBSTRING`; **fixture only** — `test_w5_the_word_boundary_is_the_thing_that_fails` asserts it against `re` directly, and no shipped source declares that mode (D116) |
| W6 | Entity normalization was one-sided — separators stripped from the spoken value but never from the payload, so thousands separators produced false failures | `available_value_never_spoken` reads speech and payload through the same `figures_in` with the same `strip`, so one-sided normalization is not expressible. **Fixture only, and measured as such:** reintroducing the defect — normalizing the payload side with an empty `strip` — moves no verdict of 555, because the one payload the corpus reaches carries no separator. `test_w6_a_thousands_separator_in_the_payload_is_stripped_too` is what holds it. The design call owed at D109 is what would give it a corpus verdict |
| W7 | Date matching was case-sensitive while quantity matching was not: a lower-cased month silently disabled the date arm — a false *pass* on its headline failure mode | `spoken_local_date_wrong` case-folds the month table and the turn's tokens alike. **Corpus evidence, measured by reintroducing the defect:** dropping the fold flips CALL-19 from `offset` to `local` — a false pass on an absolute gate — and fails `test_the_spoken_day_is_compared_against_the_venues_own_clock` and two others. The `cue_follows` test the phase-2 verifier names for this row is a fixture of the value layer, which the tier now calls (D116); the corpus evidence is the date check |
| W9 | The paraphrase-disclosure detector selected distinctive words by a bare length filter with no stopword list at an overlap threshold of two, so benign turns tripped a critical gate. The original validation measured only that the true positive cleared the threshold — never the false-positive rate in the same call | `protected_field_disclosed` declares its stopword list, minimum word length and overlap threshold, and `_distinctive` compares whole tokens. **Corpus evidence:** `test_w9_a_bare_length_filter_with_no_stopwords_fires_on_benign_turns` reproduces the reference's shape against the shipped rubric and counts the turns each flags in CALL-18 — the true positive under both, the benign turns only under the naive one |
| W10 | The unresolved-precondition correlation ignored ordering and later resolution: a variable set, later re-set, then used successfully still reported a violation | `action_against_blocking_state` reads the gate variable as of the invocation's index, so a later clearing clears the violation. **Fixture:** no design call sets and re-sets the variable, so `test_w10_a_state_cleared_before_the_action_is_not_a_violation` plants the clearing STATE event on CALL-01 and requires the violation to go with it |
| W19 | The extraction conformance test checked index sequences, kind vocabulary and view agreement — a genuinely good list — but nothing about **turn reassembly**, and never re-read the source transcript. The one failure mode the tier exists to prevent is the one its test could not see. It also crashed on a malformed file rather than reporting the violation it had already recorded | **Phase 1's, not this tier's.** The extraction conformance test re-reads each source transcript and asserts reassembly, and `tools/verify_phase1.py` is what runs it. Recorded here so the row is not read as owed by the deterministic tier |

**Closure, proposed here and adopted at P2**, one acceptance criterion rather than ten
requirements: *each named deterministic failure mode has a test that fails when the defect is
present.* That keeps the list as a diff checklist — which is what it is — while making the check
runnable. It is the `[P2]` criterion at `specs/voice-agent-eval-harness.md` line 252, and
`tools/verify_phase2.py` runs it.

### Not reached — a third disposition, because neither of the other two is true

| W | Defect | Disposition |
|---|---|---|
| W8 | Spoken dates were completed with a year sliced from call metadata, unvalidated; an unexpected header format yielded a nonsense year, and nothing handled a year boundary | **NOT REACHED.** `values.complete_year` closes it — candidate years are declared, and a best candidate further than a declared window returns nothing rather than a date — and **no shipped check calls it**. `spoken_local_date_wrong` is the tier's only date comparison and it compares the day alone, so the tier completes no year and cannot exhibit the defect |

**Why this row gets its own disposition rather than a tick or a place in the table above.** Ticking
it would claim a closure the tier does not reach; leaving it among the retired rows would say the
tier carries a defect it has no code for. Neither is true, and the difference matters at the next
phase. When this row was written the date check compared the day alone, and the note here was that
whatever closed *that* would complete a year and inherit W8 the moment it did. **Half of it has since
been closed** — D118 added the month, so a spoken date whose month is wrong no longer reads as correct
— and the year is the half that remains. A spoken date carries no year, so completing one is the
only way to compare the whole date, and the function that does it correctly is `complete_year`. The
row moves out of this section on the day a check calls it.

`values.py` says which of its functions the tier calls, and `tools/verify_phase2.py`'s thirteenth
criterion carries the caveat naming this as the row its tick does not stand for. D116 records the
fork: the value layer's uncalled comparison functions were wired into the tier, and this one was not,
for the reason above.

**What is still owed on this section.** Not a tick — a corpus verdict. W5 and W6 above are closed
against fixtures, because the payload figure the numeric arm reaches is never spoken in any design
call, so a wholly broken matcher would produce the verdict the corpus already shows. The design call
owed at D109's amendment is what converts both cells from *fixture* to *corpus evidence*, and it is
corpus authoring rather than a change to this document.

### Partially addressed

| W | Defect | Residue |
|---|---|---|
| W16 | Multi-line **variable** values silently truncated, the leading fragment dropped when a value wrapped. Latent in the reference corpus; the adjacent action branch handled the identical case correctly | **Closed twice.** Format v2 §4.1 states the rule over *events*, not turns, and the adapter implements one branch for every kind. But the `[context]` block had no stated rule at all, and the parser's implicit one dropped the tail of any value whose continuation began with `#` — the same defect, in the one place nobody had looked. §3.1 closes that (D55). |
| W17 | Any system note containing an `=` was classified as a variable, so fabricated "facts" flowed into the grounding blob and the judge's established-facts block | **Closed twice, same story.** D34's dedicated `KIND` field removed the inference from the event stream. The `[context]` block then reproduced it exactly: a wrapped value containing `:=` was split into a fabricated second variable, a fact entering the record from punctuation. Positional continuation closes it (D55). **A hazard removed from one grammar can reappear in an adjacent one that was never given a rule.** |
| W23 | Hardcoded absolute Windows paths composed with backslash f-strings; nothing ran on a fresh clone without editing source. No CLI, no corpus argument, no environment override | The outcome asserts a fresh clone works; no requirement forbids absolute paths |
| W31 | The pinned model id was a floating alias, commented as pinned — the first thing a reviewer finds in a project about reproducibility | Exact model IDs are named; nothing forbids an alias being introduced later |

---

## Provenance and maintenance

Derived from the project's primary reference document, whose location is recorded in
`private/clean-room-sources.md` and which is safe to read in full. This map is the abstraction the
repository keeps, so a builder does not need to open it.

**When to revisit.** When a taxonomy GAP is closed by a new dimension or check, move it and say
where. When a phase adds a deterministic check, tick the W it retires — and a tick is a judgment
about what the check does, so it is made by a session cleared to review the rubric rather than as
bookkeeping at the end of a build. **A row has three dispositions, not two.** Retired and open are
the obvious ones; *not reached* is for a defect the repository has closed somewhere that no shipped
check calls, and W8 is the worked example. Ticking such a row claims a closure the tier does not
have, and leaving it open says the tier carries a defect it has no code for. **Say which kind of
evidence a tick rests on**: a verdict the design corpus produces, or a fixture. W5 and W6 are the
worked example of the second, and the cell says so rather than reading like the first. The tally at the end of Part 2
is the number to keep honest — twelve items in the two seeded-but-unchecked rows today, and zero in *neither seeded nor consciously deferred*, and a phase-1 corpus that closes none of them
should say so deliberately rather than by omission.
