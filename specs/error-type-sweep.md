# Error-type sweep — what the corpus covers, and what it deliberately does not

**What this is.** A record of a systematic pass over catalogd voice-agent failure modes, checked
one at a time against every finding in the corpus. It exists so that *"we checked what the corpus
does not cover"* is a document a reader can audit rather than a claim they have to take.

**Where the material came from.** The project author supplied a set of problem ideas to make the
problem set richer, drawn from experience of reviewing agentic voice-support calls. This file records
**the mapping**, not the source: what this corpus already expressed, what it structurally cannot,
what was added as a result and why. Nothing here reproduces the source material.

**When.** 2026-09-01, after all 70 findings then in the corpus had been adjudicated and before the
gold set was generated. That ordering was wrong and is recorded in D68: enrichment belongs *before*
adjudication, because every class added afterwards needs adjudicating again.

---

## The three tests a candidate had to pass

Recorded because a corpus is never exhausted, and a sweep with no stopping rule stops when whoever is
doing it gets tired. A class earned a seeding only if **all three** held:

1. **The corpus cannot currently express it.** Not "has no finding for it" — cannot state it at all
   with the transcripts, fields and events it has.
2. **It contributes a detection shape the corpus lacks**, rather than a further instance of one it
   already carries. This is the test that does the work, and it came out of measurement: five
   findings split during adjudication produced only *two* distinct assertion shapes between them.
3. **It fits a call at or below 0.35 findings per event, or justifies a new call on its own.**
   Density is what separates a corpus from a catalog. At 0.18 the calls read as calls; one call
   reached 0.50 and read as a list. (An earlier draft of this document said 0.54 — that call's
   density before it gained two events. Two figures for one measurement sat in two documents,
   neither dated, which is the drift a spelled-out number invites.)

---

## Result

Of the **141** failure modes examined, roughly **45 were already expressed**, about **25 are
structurally inapplicable to this corpus**, and about **40 were candidates**. Those three do
not sum to 141, and the balance is a fourth bucket the first version of this document failed
to name: types the corpus expresses **partly**, where a finding covers some of the class and
not the rest. They were left alone deliberately — a partial instance is a weaker candidate
than an absent one, and none cleared test 2.

**Thirty-five findings and two calls came out of it** — twelve in the new calls, twenty-three
in existing ones. Sixteen of the thirty-five come from the classes tabled below; the rest are
the splits and re-cuts those classes forced, plus the two new calls' own supporting rows.

### Structurally inapplicable, and why

These are not gaps. Recording the reason matters more than recording the absence:

| area | why the corpus cannot carry it |
|---|---|
| **Speech, audio and recognition** — barge-in, endpointing, mispronunciation, recognition disparity, cross-talk, audio-path degradation | No audio layer sits behind this corpus. The format carries turn boundaries and no waveform, which D40 settled deliberately. A finding about what a recognizer heard would have no oracle here. |
| **Model and prompt lifecycle** — version drift, run-to-run variance, context truncation, judge drift | Properties of a harness across runs, not of a transcript. Several are already project concerns: N=10 repetitions (D17) exists because of variance, and judge drift is what the held-out set measures against. |
| **Review-process hazards** — design-versus-defect ambiguity, single-run inference, aggregate-score gating, unvalidated judge | These describe the evaluation process rather than the system under test. Each is already a decision here: the `question` tier exists for the first, N=10 for the second, absolute gates for the third, and the fourth is the project's entire thesis. |
| **Post-call and outbound** — recording retention, do-not-call windows, time-of-day rules | Every call in the corpus is inbound and ends at hang-up. Nothing after the call is in scope. |

### Added by the sweep

| class | where | findings |
|---|---|---|
| Retry against a hard refusal; no deduplication on a timed-out write | CALL-05 | F-53, F-54 |
| Injection arriving in retrieved data rather than caller speech | CALL-08 | F-55 |
| Authentication factor strength — a spoofable identifier plus one knowledge factor | CALL-03 | F-56 |
| AI-status disclosure configured and never delivered; not answered when asked | CALL-12 | F-57, F-58 |
| Delivery state versus acceptance at the API boundary | CALL-11, CALL-12 | F-59, F-60 |
| Termination etiquette — who ends the interaction | CALL-05, CALL-12 | F-71, F-72 |
| A single reason code for a call that completed two actions | CALL-03 | F-73 |
| A reason code naming an action the call never performed | CALL-09 | F-74 |
| Over-disclosure under pressure — no verification, bypass reasoning spoken aloud, an internal field read out, payment data volunteered, delivery redirected, a gate enforced in one flow and absent in another, a successful call filed as abandoned | **CALL-18** (new) | F-75 … F-81 |
| A zone conversion off by a day; an impossible reschedule timeline; a policy anchored to a field the record lacks; false assurance under direct challenge | **CALL-19** (new) | F-82 … F-86 |

**Three of these needed no transcript change at all.** The corpus already contained the defect and no
finding said so: `issue_refund` called three times with identical arguments after a hard refusal
(F-53), a call completing two writes under one reason code (F-73), and — the sharpest — **an
`agent_hangup` seeded in two calls, pinned by a test constant, and described in the seeding manifest
as belonging "where it is a finding rather than as a default", with no finding anywhere** (F-71,
F-72). A seeded defect with no finding is exactly what the manifest's Part 3 exists to prevent.

---

## What remains uncovered, deliberately

Recorded so the next sweep starts from a baseline rather than from scratch, and so a reader knows
these were considered rather than missed.

- **Concurrency and stale reads.** Two sessions acting on one account, or an agent acting on a
  payload retrieved before a mid-call change. Both need state that moves *during* a call from
  outside it, which no transcript in this corpus carries and which the format has no way to show.
- **What an agent should do when a transfer fails.** CALL-20 seeds the successful path only. A
  transfer is an action like any other and is not complete until its result comes back, which gives
  three failure shapes the corpus does not carry: **(a)** the agent believes it initiated a transfer
  and did not, so nothing comes back at all; **(b)** the transfer was initiated and failed
  technically, so an error comes back; **(c)** no human answered, so a timeout comes back. (b) and
  (c) are mutually exclusive — a call cannot be both — so showing them needs two calls, not one.
  **The detailed policy is left open** — retry, warm-hold, route elsewhere — because that is a
  question for a human to answer comprehensively rather than a defect to seed. **But open is not the
  same as unbounded, and a floor is stated here so the gap cannot be read as permission**: whatever
  the policy, a failed transfer must leave the caller with somewhere to go. Telling them there is a
  technical problem and asking them to call back in ten minutes is the simplest thing that clears
  the floor. Silence, a dropped call, or an assurance that the transfer succeeded do not, and a call
  seeding any of those would be a defect against this floor rather than against an unwritten policy.
- **Account enumeration.** Differing responses revealing whether an account exists. Needs two calls
  differing only in whether the account is real — a generated pair like CALL-06 and CALL-07 — and
  the class did not clear test 2 on its own.
- **Authentication lockout.** Verification that can fail but never recover. The corpus has no call
  where verification is attempted and fails; adding one is a reasonable future seeding.
- **Abuse and threat handling.** No defined behavior for profanity or threats. Plausible and
  seedable; it did not clear test 3 without a further new call.
- **Jurisdictional obligation drift.** Disclosure rules differing by state, applied uniformly. D44
  put the corpus in one US state, so showing drift needs a second locale the entity register does
  not carry.
- **Cross-call answer-completeness variation.** The same intent answered fully in one call and
  thinly in another. Expressible in principle; it needs a deliberate pair and would sit close to
  CALL-06 and CALL-07's shape without adding a new detection shape.

---

## The uncomfortable half

Two things this sweep found are about the corpus's own documents rather than about the calls, and
both are the same shape the project keeps catching in itself.

**A seeded defect can exist with no finding, and nothing notices.** `AGENT_HANGUP_SEEDED` pinned the
property, `test_corpus_hygiene` asserted it, the manifest described it as a finding — and no finding
existed. Every mechanism was green. What was missing was anything binding a seeded exception to a
row in the findings document.

**A sweep is only as good as its stopping rule, and the rule came from measurement rather than
principle.** Test 2 exists because splitting judged rows produced repetition rather than coverage,
which was visible only after counting. A sweep run without it would have grown the corpus and
covered nothing new.

---

## Owed, and recorded here so it is in one place

D46's rule is that a document claiming to be machine-checked is making a claim. The honest
counterpart is that a debt recorded in one decision entry is invisible to a reader of another, so
they are collected here and struck through as they close.

- ~~The clause count stated in a `fetch_policy` result is checkable against `corpus/policies/` and
  nothing checked it (D65), while `specs/event-model.md` § 3.5 described the check as existing.~~
  **Closed** — `test_every_policy_retrieval_states_the_document_s_real_clause_count`, written after
  an independent sweep found the two documents disagreeing. It finds nothing today, which is the
  expected result for a check written to make a sentence true.
- ~~**The taxonomy-coverage mapping for the classes this sweep added is owed, not done** (D66).~~
  **Closed** — `specs/taxonomy-coverage.md` **Part 2b**, the sweep's classes under their own
  `S` identifiers with their own tally. **This said "ten classes as `S1`–`S10`" until 2026-09-07**;
  `S11` arrived at D73 from this sweep's own list of what it had left uncovered, and the sentence
  counting them did not move. De-quantified rather than re-pinned, per D74. Not renumbered into the inherited 35, because "taxonomy 17" means
  something in five other files and would have quietly come to mean something else. Every class is
  seeded and none has a check, which is not a gap peculiar to them: **phase 1 builds no Tier A checks
  at all**, so the disposition column records what a check would have to be rather than whether one
  exists. `test_the_part_2b_tally_counts_match_its_own_class_lists` binds the new tally to its own
  class list, and the Part 2 tally parser was rescoped in the same edit — it had been reading `S1,
  S6, S7, S8` as taxonomy items 1, 6, 7 and 8 and reporting them double-counted.
- **Three closed vocabularies are largely unexercised, and the unused tokens are now classified
  rather than waved at.** `DisconnectionReason` is used at 2 of 9, `DisclosureState` at 1 of 4,
  `Outcome` at 3 of 4. The parser is tested against every token
  (`test_every_closed_vocabulary_token_round_trips_through_the_parser`) and the corpus's own subset
  is pinned so it cannot shrink (`test_the_corpus_demonstrates_the_vocabulary_it_claims_to`). What
  was missing was any statement of *why* each unused token is unused, which is the difference
  between an exemption and a shrug:

  | token | why it is unused |
  |---|---|
  | `DisconnectionReason.asr_error` | **Structurally inapplicable.** No audio layer sits behind this corpus (D40), which is the same reason the whole speech-and-recognition family was ruled out above |
  | `DisconnectionReason.voicemail_reached` | **Structurally inapplicable.** Every call in the corpus is inbound; reaching voicemail is an outbound event |
  | `DisconnectionReason.transferred` + `Outcome.transferred` | **A genuine candidate, and the strongest one.** Transfer to a human is a real ticketing outcome, it exercises two vocabularies at once, and escalation behavior is a failure surface the corpus does not touch at all. It needs a call, and that call must clear D68's three tests like any other |
  | `DisconnectionReason.inactivity_timeout`, `max_duration_reached`, `network_error`, `system_error` | **Genuine candidates, lower value.** Platform-side terminations. CALL-12 already carries a degrading line as a true negative, so the material is adjacent — but a termination reason on its own adds no detection shape, which is D68's test 2 |
  | `DisclosureState.skipped` | **The sharp one.** It is the value a correct platform would have recorded in the very call where F-57 reports the opposite — a disclosure marked delivered that no event delivers. Seeding it would give that finding its true negative |
  | `DisclosureState.acknowledged`, `declined` | **Genuine candidates.** Caller responses to a disclosure, which no call in the corpus records |

  **None of these is seeded here**, because seeding one means authoring findings, and findings are
  adjudicated by a human (D10). They are recorded as candidates with their reasons, which is what
  the next corpus session needs and what "state the exemption" should always have meant.

- **D22's justification for YAML is narrowed, because one third of it will probably never be
  exercised.** D22 chose YAML over a Markdown table and CSV for three reasons, and they have not
  aged equally:

  1. **`evidence` is a list**, so fragments from different points in a call stay visibly separate.
     **Exercised throughout** — every one of the 86 rows uses it, several with three or four
     fragments.
  2. **Block scalars carry text whose line breaks are content.** **Exercised, and it took an
     independent sweep to notice**: dozens of `consequence` fields carry paragraph breaks that
     `make_gold_set._fold()` was silently flattening on every generation since the first. Fixed, and
     now asserted by `test_the_findings_format_uses_the_block_scalar_it_was_chosen_for`.
  3. **`evidence` holds verbatim multi-line quotes.** **Not exercised, and the corpus has no natural
     case.** Every quotable source in it — event bodies, context values, policy clauses — is prose
     that wraps. Line breaks in a quote of any of them would be presentation, not content, and `>-`
     is the correct marker for that. A search of all three policy documents found no clause with
     internal structure: no lists, no sub-items, nothing whose shape a fold would destroy.

  **This is a narrowing, not a discharge.** Reason 3 is the one that was quoted in the spec's own
  in-scope bullet, and it is the one with nothing behind it. Manufacturing a row to satisfy it would
  mean either inventing a finding — which D10 reserves to the human — or putting structure into a
  policy document that the domain does not call for. Reasons 1 and 2 carry the format on their own,
  and stating that plainly is better than a corpus row authored to make a sentence true.
