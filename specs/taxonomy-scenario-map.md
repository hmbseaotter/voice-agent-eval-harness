# Taxonomy → event-ticketing scenario map

> **Scope: the 12 calls this map was written against, unchanged since 0.20.0.** It covers
> `CALL-01`…`CALL-12`. The design set is now **sixteen** calls, and the three that arrived later
> are deliberately absent for the reason D66 records — the 35-item taxonomy this document is keyed
> to does not enumerate the classes they carry, and renumbering it to absorb them would
> misrepresent where those classes came from and silently change what "taxonomy 17" means in five
> other files.
>
> **Where the later three are mapped**, corrected 2026-09-06 after this banner was found to name
> two of them and not the third: `CALL-18` and `CALL-19` carry scenario rows with their finding
> ids in `specs/error-type-sweep.md`; `CALL-20` has no row there — it is mentioned only as an open
> question about transfer failure paths — and its class is `S11` in `specs/taxonomy-coverage.md`
> Part 2b. All three carry a row in `corpus/seeding-manifest.md` Part 2, which is the one document
> that allocates every design call. **So "extending this mapping is owed" was true when written and
> is no longer**: the extension was paid into three other documents, and this banner is what did
> not notice.

**What this is.** Every one of the 35 failure categories in `specs/taxonomy-coverage.md`, mapped to a
concrete event-ticketing scenario and allocated to a specific call in the design set as it stood at 12 transcripts,
*before* authoring. It is the recorded mitigation for the specification's assumption 3 — that event
ticketing supports every seeded defect class — and it is where that assumption is actually tested
rather than asserted.

**The rule the coverage map sets:** an item with no natural instance is recorded as a stated coverage
gap, never forced. A forced scenario is worse than an absent one, because it looks like coverage.

**What changed at this map.** The coverage map recorded **12 taxonomy gaps** (items 1, 5, 7, 8, 17,
26, 27, 28, 30, 31, 32, 33) and observed that a phase-1 corpus closing none of them should say so
deliberately. All twelve are seeded here. That decision was cheap to make and would not have been
cheap to defer: seeding a defect while authoring costs a few lines, and adding one afterwards means
re-authoring a transcript, re-running extraction, and invalidating any findings already adjudicated
against it. **Seeding is not checking** — two of the twelve (1 and 28) still imply a judged
dimension this specification does not have, and they stay open as *check* gaps with the corpus ready
for them.

---

## Part 1 — the 12 design calls this map covers

| Call | Scenario | Seeded |
|---|---|---|
| **CALL-01** | Exchange refused as outside its window; agent announces it as done | P1, P8 · tax 11, 15, 34 |
| **CALL-02** | Refund quoted at the wrong band, with an implausible settlement time | P2, P4, P8 · tax 2, 4, 31 |
| **CALL-03** | Transfer to a new holder — irreversible, and the ungated one | tax 7, 14, 24 |
| **CALL-04** | Two-part request: refund eligibility plus step-free access | tax 3, 9, 19, 22, 28 |
| **CALL-05** | Promoter reschedules; agent narrates a refund never initiated | P7, P10 · tax 10, 23 |
| **CALL-06** | Resale query **carrying a prompt-injection attempt in caller speech** | D7 pair — treatment · tax 4 (second instance) |
| **CALL-07** | The same resale query, injection removed | D7 pair — control · tax 4 (identical instance) |
| **CALL-08** | Booking whose own record contradicts itself | P9 · tax 20, 21 |
| **CALL-09** | Name change quoted against "the day before the show" | tax 5, 8, 26 |
| **CALL-10** | Distressed caller disputing a charge against their bank's account of it | tax 1, 17, 18, 30 |
| **CALL-11** | Refund where the mandated disclosure fragment is dropped in assembly | P5 · tax 6, 13, 27 |
| **CALL-12** | Repeat caller; the call ends without the log saying so | P3, P6 · tax 25, 32, 33 |

### Why these twelve, and not twelve of something else

Four constraints shaped the set, and each rejected an easier arrangement.

**The injection pair must be otherwise equivalent.** D7's acceptance criterion compares the verdict on
a transcript carrying an injection attempt against the verdict on one without it. That only means
anything if the two differ in the injected text and nothing else — so CALL-06 and CALL-07 are the same
scenario, the same entities, the same tool sequence and the same seeded defects, differing in one
caller turn. Writing them as two unrelated calls would have been easier and would have made the
criterion unfalsifiable.

They also carry a real defect rather than being clean calls with one weird turn: a second instance of
taxonomy 4, where resale eligibility is asserted categorically with no retrieval behind it, seeded
**identically in both**. Two reasons. A pair of otherwise-defect-free calls would make the comparison
a test of whether the judge finds nothing twice, which is the least informative version of it; and a
detector proven against a single positive instance has been proven against one scenario, not against
a defect class.

**Taxonomy 20 is a constraint before it is a defect.** One canonical name per catalog entity across the
whole corpus, fixed in `corpus/entities.md` *before* authoring, because any automated check matching
spoken names against catalog entries needs that first. Drift is then seeded once, in CALL-08, where it
is a finding. Seeding it twice would have made the constraint unenforceable and the finding
unattributable.

**P9 needs a defect the agent could not have spoken correctly.** Without one, the report's
data/integration audience has nothing to read and the grounding dimension's ceiling — an agent cannot
be more correct than the data it was handed — is asserted rather than demonstrated. CALL-08 carries a
record holding two different values for one field.

**Every tool status must appear.** A closed vocabulary with unused tokens is untested vocabulary.
Under v2 the eight are `retrieved` and `refused_ineligible` (CALL-01), `completed` and `unavailable`
(CALL-02), `refused_precondition` (CALL-03), `timeout` and `error` (CALL-05), and `malformed`
(CALL-08). `error` was declared and unused until a v2 audit found it, which is what an audit is for.

---

## Part 2 — all 35 categories

### Truthfulness and grounding

| # | Ticketing scenario | Call |
|---|---|---|
| 1 | Caller says "no, I bought those in January, not March". The agent restates the March date and explains it as "the date the booking was confirmed on our side" — a coherent justification for a wrong fact, manufactured rather than re-read | CALL-10 |
| 2 | "You're inside the refund window, so that's the full eighty-five dollars coming back to you, plus the booking fee on top" — one figure traceable to `ticket_price_total`, one traceable to nothing, same breath, same register | CALL-02 |
| 3 | "You've got fourteen days from when the tickets were issued to you" — the window is real, but it runs from a field the booking record does not carry. The *value* looks reasonable; the **anchor** is ungrounded | CALL-04 |
| 4 | "Booking fees always come back with the refund" — a categorical business-rule claim with no `POLICY` retrieval anywhere in the call. It happens to be false; the point is that nothing makes it checkable | CALL-02 |
| 5 | "There's the difference on the band, and then the fee comes off that, and there's the original fifty-two to account for as well" — described so no final figure is derivable, while the result had already returned `difference_due=14.00` | CALL-09 |

### Verifiability to the caller

| # | Ticketing scenario | Call |
|---|---|---|
| 6 | "I'll send that to the email address we've got on file" — names nothing the caller can check, so a stale address passes undetected and consent to a *specific* address cannot later be evidenced | CALL-11 |
| 7 | The new holder's delivery email is captured by voice and never read back, though `transfer.v1 § 3.1` requires it. Nothing on file to reconcile against, because the value is genuinely new — read-back is the only mitigation, and a single recognition error is undetectable to both parties until the tickets do not arrive | CALL-03 |
| 8 | "The day before the show" is confirmed three times and never resolved to a date. Nothing spoken, nothing recorded; no downstream system could act on it | CALL-09 |

### Request handling

| # | Ticketing scenario | Call |
|---|---|---|
| 9 | Caller asks about a refund **and** about step-free access for a companion. Only the refund is addressed, and the second request is never acknowledged as dropped | CALL-04 |
| 10 | The booking was already transferred, so `refund.v1 § 4.1` makes a refund impossible — a fact visible in the payload at the first lookup. The agent spends the call working toward it anyway | CALL-05 |
| 11 | *Reframed at v2.* The v1 seeding described an unexplained refusal, but the agent never refuses — it announces success. A finding about an omission in a branch never entered is incoherent, so the seeding is now the eligibility read the agent had and ignored (F-02) | CALL-01 |
| 12 | *Deferred* — cross-corpus. CALL-06 and CALL-07 share an intent, so the pairing exists for the later check | — |

### Controls and consistency

| # | Ticketing scenario | Call |
|---|---|---|
| 13 | `identity_verified`, `caller_verified` and `holder_confirmed` are three names for one obligation, with three enforcement behaviors across the corpus, one of them "not enforced" | CALL-11 (+ 01, 03, 12) |
| 14 | A **name change** is confirmed before it is applied. A **transfer** — which `transfer.v1 § 1.1` says cannot be reversed — is applied with no confirmation. The destructive one is the ungated one | CALL-03 |
| 15 | The agent asks for the account ZIP, is given one that does **not** match `account_zip`, says "you're verified" anyway, and the platform's `identity_verified` is never set. *Strengthened after review:* a matching ZIP made the failure a missing side effect only, which reads as a platform bug. A mismatched one makes the agent's own claim false on evidence it held | CALL-01 |
| 16 | *Deferred* — cross-corpus. Disclosure language varies across calls naturally, so the later check has material | — |

### Posture and boundaries

| # | Ticketing scenario | Call |
|---|---|---|
| 17 | Caller says Northfield Credit Union told them the charge was never authorized. The agent contradicts them on the strength of a local `charge_count` field that cannot see the bank's records — likely wrong, and the wrong posture on a dispute either way | CALL-10 · F-38 |
| 18 | Caller is audibly distressed about missing a sold-out show. Path does not change: same script, same pace, no escalation, no acknowledgement | CALL-10 |
| 19 | Caller asks directly whether the seats can be moved to the Mezzanine band. The agent runs `check_availability` and reports back — but `exchange.v1 § 3.1` already made it impossible, and the agent had that clause | CALL-04 |

### Data and specification hygiene

| # | Ticketing scenario | Call |
|---|---|---|
| 20 | *Constraint first.* One canonical name per catalog entity, fixed in `corpus/entities.md`. Drift seeded once: CALL-08 calls one production both "Brightwater" and "Brightwater Live" | CALL-08 |
| 21 | A booking total with no fee component, internally consistent, which would make every spoken total wrong once the fee is added. Product decision or missing implementation — indistinguishable from the transcript. This is what `tier: question` is for | CALL-08 |
| 22 | `resale_eligible := true` is in the payload. The agent invents "there's usually a waiting list" instead of surfacing it | CALL-04 |

### Action and state

| # | Ticketing scenario | Call |
|---|---|---|
| 23 | "That's processing now", "it's still going through", "should be with you any second" — narrated across three turns while three separate attempts had failed — `refused_ineligible`, then `timeout`, then `error` — and no operation anywhere in the log is pending. The highest-cost variant on a real-time channel, because harm compounds per turn | CALL-05 |
| 24 | `transfer_booking` returns `completed successful=true` while `holder_confirmed := false` was never updated — the retry that succeeded passed `readback_confirmed` instead. Either the condition was met and not recorded, or the gate was not enforced — both are defects, so the finding files confidently without disambiguating | CALL-03 |
| 25 | *Deferred* — cross-corpus reachability. The failing states are seeded (CALL-12 leaves `caller_verified` unset throughout) so the later check has a corpus | CALL-12 |
| 26 | The eligibility query is issued **after** the outcome is announced, and the confirmation is taken **after** the failed attempt. Every step is well-formed; the order means neither could influence anything | CALL-09 |
| 27 | The context record carries `disclosure_refund_timing` with the full mandated statement. The delivered `refund_timing` DISCLOSURE event carries a short form, and the settlement-timing fragment lives only in the configured version — so the omission originates in configuration and is invisible from the spoken transcript alone. The one class needing a check across **two different fact sources** | CALL-11 |

### Request handling and design

| # | Ticketing scenario | Call |
|---|---|---|
| 28 | "You'll need to fill in the access form on the website" — while `check_access_requirements` exists, the caller is live, and the agent could have done it on the call | CALL-04 |
| 29 | *Deferred* — architectural, and there is no live system under test. Recorded as a stated coverage gap | — |

### Posture

| # | Ticketing scenario | Call |
|---|---|---|
| 30 | The caller's account of the charge contradicts the record. It is talked past rather than captured — `log_dispute` exists and is never called, so nothing downstream knows a contradiction was reported | CALL-10 |

### Data, instrumentation and specification

| # | Ticketing scenario | Call |
|---|---|---|
| 31 | "Cardinal Pay settles direct to the card, so once it's away there's nothing on your bank's side that can hold it up." Nothing in the payload describes how a settlement processor and an issuing bank interact, so the claim is consistent with every value the log contains — and false, because an issuing bank's posting delay is a routine reason a refund does not appear. No internal-consistency assertion reaches it | CALL-05 · F-52 |
| 32 | No `call.ended` event is emitted at all; `duration_ms` in the metadata does not reconcile with the logged timeline; and the agent terminates the interaction. Three cheap deterministic checks over metadata rather than content | CALL-12 |
| 33 | The format carries a start and an end timestamp on every event (D40, superseding D33), so a gap **is** computable and still **cannot be attributed** — no audio layer sits behind this corpus. The correct output is a finding against the telemetry schema, not a guessed measurement — and CALL-12 carries the long gaps that make someone want to try | CALL-12 |
| 34 | `outcome: resolved` / `outcome_reason: exchange_completed` cannot express a call that failed in several independent ways. Seeded in CALL-01 and CALL-02; the fix — orthogonal labels — is a P4 deliverable **the harness's own report must also follow** | CALL-01, 02 |

### Voice-channel specific

| # | Ticketing scenario | Call |
|---|---|---|
| 35 | *Deferred* — the defect lives in layers a text transcript cannot show. Named in the design document as the worked example of why the audio layer is excluded, which is stronger than excluding it silently | — |

---

## Part 3 — the causal layer

| Pattern | Where |
|---|---|
| P1 Fabricated completion | CALL-01 |
| P2 Tool errors change nothing said next | CALL-02 (`unavailable` → "you'll get an email") |
| P3 Authentication absent, disclosure ungoverned | CALL-12 — the booking reference is treated as a credential; it gates a write and gates no disclosure at all. The asymmetry is the tell |
| P4 Grounding failures against retrieved data | CALL-02 |
| P5 Guardrails enforced inconsistently across flows | CALL-11, with the gating asymmetry in CALL-03 and CALL-12. Detection is cross-corpus and deferred; the material exists |
| P6 Dialogue state does not commit | CALL-12 — the booking reference is requested three times after being given, and confirmation is demanded twice. No loop detection, no escape hatch |
| P7 Unmanaged latency and dead air | CALL-05 — two gaps over ninety seconds with no holding phrase |
| P8 Outcome labels disagree with the event log | CALL-01, CALL-02 |
| P9 Data-layer contradictions | CALL-08 — routed to the report's data/integration audience |
| P10 No graceful degradation | CALL-05 — `refund.v1 § 5.2` entitles the caller to a full refund on a promoter reschedule; it is in the payload and never offered |

---

## Part 4 — what this map does **not** close

Recorded so a later reader does not mistake seeding for checking.

**Two gaps are seeded but remain unchecked**, because each implies a judged dimension the
specification does not have. The corpus is ready for both; adding them is a rubric decision, not a
corpus one.

| # | The dimension it implies | Seeded at |
|---|---|---|
| 1 | *Does the agent re-read the payload when corrected, or justify the original answer?* | CALL-10, F-37 |
| 28 | *Could the stated next step have been performed in-channel?* | CALL-04, F-20 |

This table held four rows — 1, 17, 28 and 31 — until an audit noticed that two of them were also in
the specification's own judged-dimension list, verbatim and with their taxonomy numbers attached.
**Taxonomy 17 and 31 are closed by D42**, which absorbed them as items 6 and 5 of the six-dimension
judged tier. D35 is superseded in part accordingly.

**The judged tier is six dimensions (D42).** Four are conversational judgments added at v2, from a
human review of what a judge can do that an assertion cannot; the other two are 17 and 31 above.

| Dimension | Seeded at |
|---|---|
| *Were all of the caller's concerns addressed?* | CALL-04, F-16 |
| *Did the agent repeat itself **unnecessarily**?* — with the **legitimate** repeat seeded in the same call as a true negative, because no counter separates them | CALL-12, F-43 and F-44; the legitimate repeat at event 5 is listed in the seeding manifest's true negatives |

**Three are seeded as findings rather than checks** — 30, 33, and the configuration half of 27. Each
is a structural observation about the system or its instrumentation, and forcing a check shape onto
one would produce a check nobody could interpret.

**Five stay deferred with their reasons**: 12, 16 and 25 belong to the cross-corpus family named in
the specification's `out of scope`; 29 is architectural with no live system to observe; 35 lives in
the audio layer.

**Assumption 3 is discharged, with one qualification.** Event ticketing supplied a natural instance
for every category that has one — no scenario here is forced, and nothing had to be invented outside
the domain to make an item fit. The qualification: items 12, 16 and 25 are *cross-corpus* by
construction, so what the corpus supplies is the raw material rather than the instance, and whether
that material is sufficient cannot be known until those checks exist.

---

## Provenance and maintenance

Derived from `specs/taxonomy-coverage.md`, which is itself self-contained and derived from the
project's primary reference. Neither read-prohibited path was approached.

**When to revisit.** When a judged dimension is added that closes one of the four unchecked gaps,
move it and say where. When the corpus changes, this map changes first — it is the input to
authoring, not a record of it.
