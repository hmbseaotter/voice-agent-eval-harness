# Entity register

Every entity in this corpus is invented. This file is the canonical list, and it exists for two
reasons that pull in opposite directions.

**One canonical name per entity.** Taxonomy 20 — reference-data naming drift that breaks automated
matching — is a *constraint on the harness*, not only a seeded defect: any check matching a spoken
entity name against a catalog entry needs a single canonical name first. So the register comes before
the corpus, and drift is seeded **once, on purpose**, where it is a finding rather than an accident.

**Nothing here is carried over.** Every instance in the corpus, findings, rubric or prose is an
invented but plausible substitute. Renaming inside the same domain would not be enough — a scenario
recognizable as prior art with the nouns swapped is a leak even when every noun is invented — so the
domain itself is event ticketing, which has no shipping, no inventory and no goods in transit.

**The setting is the United States.** `en-US`, USD, NANP numbers, US ZIP codes. California
specifically, which is why every call opens with a recording disclosure: two-party consent makes that
notice a legal requirement rather than a courtesy, and a ticketing business transacting by phone
records its calls.

**US spelling throughout**, in the transcripts and in everything written about them. The repository
was authored British and converted in one pass; the point is not the spelling itself but that a
corpus claiming `en-US` while its agent says "cancelled" is contradicting its own metadata, and a
reader who notices that will reasonably wonder what else was declared rather than done.

---

## Class 1 — company, brand, product and catalog entities

| Entity | Canonical name | Notes |
|---|---|---|
| Ticketing platform | **Verso Tickets** | San Francisco. The system under test belongs to it. |
| Venue | **Ridgeline Pavilion** | 1,100 seats. Bands: Orchestra, Mezzanine, Balcony. |
| Venue | **Lakemont Arena** | 4,200 seats. Bands: Floor, Lower Bowl, Upper Bowl. |
| Venue | **The Alder Room** | 240 seats, general admission, no bands. |
| Production | **The Halloway Ensemble** | Chamber music. Touring, multiple dates. |
| Production | **Brightwater** | Band. Arena shows. |
| Production | **Understory** | A play. Limited run at The Alder Room. |
| Production | **Fox & Field** | Comedy duo. |

Price bands are catalog entities and take the same discipline: **Orchestra**, **Mezzanine**,
**Balcony**, **Floor**, **Lower Bowl**, **Upper Bowl**. No other band names appear.

## Class 2 — identifiers, addresses and contact details

| Kind | Pattern | Why this pattern |
|---|---|---|
| Booking reference | `BK-####-XX` | Invented shape; no checksum, so none can be inferred. |
| Event identifier | `EV-#####` | |
| Account identifier | `AC-#####` | |
| Refund identifier | `RF-#####` | What `issue_refund` returns as `refund_id`. |
| Transfer identifier | `TR-####` | What `transfer_booking` returns as `transfer_id`. |
| Exchange identifier | `EX-####` | What `exchange_tickets` returns as `exchange_id`. |
| Message identifier | `MS-#####` | What `send_confirmation` returns as `message_id`, and what a context record's `last_confirmation` carries. |
| Specialist identifier | `SP-####` | The specialist who accepted a handoff, as `transfer_to_specialist` returns it in `accepted_by`. |
| Tool call identifier | `t#` | Call-local. Links a `TOOL_CALL` to its `TOOL_RESULT`. |
| Email | `<local>@example.com` | Reserved by RFC 2606; can never be registered. |
| Telephone | `+1 (415) 555-01##` | NANP reserves `555-0100`–`555-0199` for fictional use. Permanently unassignable. |
| ZIP code | `00###`, in `00000`–`00499` | Five-digit US format, and **below USPS's lowest assigned ZIP (`00501`)**, so no such code exists. |

**Personal names.** Holders get an initial and a surname (`R. Adeyemi`, `P. Sandoval`). They are
invented, belong to no real person, and are paired only with reserved-range contact details — so no
row in this corpus is real personal data even in combination. **That combination is the thing to
watch**: a name is not personal data and a ZIP is not personal data, and the two together frequently
are. (That sentence sat two paragraphs below until 2026-09-07, where "that combination" pointed at a
held-out transcript relying on a speech rule rather than at the pairing it is about.)

**The initial-and-surname rule governs the *record*, not speech.** A holder name stored in a context
variable, a `STATE` event or a tool argument is written `X. Surname`. A caller saying their own name
aloud may say all of it, because people do, and a transcript that had every caller speak their own
initial would be describing a world nobody lives in. The rule exists to keep a *stored* identity thin;
a spoken given name adds nothing storable and reads as a person talking. This was unstated, and a
held-out transcript relies on it.

**Agent personas.** The agent introduces itself by a given name in every call, and thirteen are
used: **Alex**, **Amara**, **Dana**, **Ines**, **Kit**, **Marco**, **Marek**, **Nadia**, **Priya**,
**Ray**, **Reyna**, **Sam**, **Theo** (Nadia and Theo twice each). Given name only, no surname: the
persona is a presentation choice and not a stored identity, so nothing about it is a record.

**These were undeclared until an independent sweep counted them**, which is the same hole D71 found
one noun over. That sweep's mutation battery caught that renaming the ticketing platform in a single
transcript was caught by nothing, because the register check reads Class 6 — the machine tokens that
reach the parser as fields — and Class 1 lives in free speech. The platform name was then bound by a
test; the persona, which appears in **every** call and is invented under the same policy, was left
open. `test_every_agent_persona_is_declared` closes it.

**Variety is deliberate.** A single persona across sixteen calls<!-- #design_set_size --> would read as one operator working
every shift, and F-58 — an agent that will not answer *"am I talking to a person?"* — depends on the
introduction sounding like a person introducing themselves. Recorded because the alternative reading,
that the variety is incidental, was equally available from the corpus alone.

**No street addresses appear anywhere.** A ZIP is used for verification and nothing more.

## Class 3 — money

US dollars. Ticket prices $18.00–$96.00, booking fees $2.50–$8.50, all invented. Figures are chosen
so arithmetic in a transcript can be checked: where a total is stated, its components are in the
context record or the event log.

## Class 4 — policy terms

`corpus/policies/` is the authority: `refund.v1`, `exchange.v1`, `transfer.v1`. Every window,
eligibility rule and timing in the corpus comes from a clause in one of them. Nothing is invented at
the point of use — a policy term spoken in a call either matches a clause or is a seeded defect, and
there is no third category.

## Class 5 — named third parties

This class carries an authoring constraint, and it is the one place where "invent everything" is the
wrong instruction.

| Third party | What it is | Stated characteristics |
|---|---|---|
| **Cardinal Pay** | Card payment processor | Invented name, **real service class**. Card refunds are submitted, then settle through the card networks — days, not minutes, and no instant reversal. `refund.v1 § 3.2` states five business days. Appears in tool results as the settlement token `cardinal_pay`. |
| **Northfield Credit Union** | The caller's bank in the dispute call | Invented. Appears only as the institution the caller reports something about, so the agent's visibility boundary has something concrete on the other side of it. |

**Why this matters.** Taxonomy 31 — external-world plausibility — is the clearest justification in
the corpus for spending a model call, because it is the one defect class where nothing in the payload
disagrees with anything else and only real-world knowledge catches it. That depends on the third
party being *checkable*. A wholly invented service with no stated properties makes the category
unjudgeable and quietly deletes the argument.

So the rule is: a real-enough service class with invented specifics. "Card refunds settle in days,
not minutes" is a fact about how card payments work, not about Cardinal Pay — which is exactly why a
judge can evaluate it and a deterministic check cannot.

**No carriers, couriers, warehouses or tracking numbers appear.** Not an oversight: those are the
shape of a different domain, and importing them would reintroduce a family resemblance the
substitution policy exists to prevent.

## Class 6 — tool names, variable names, vocabularies, reason codes

**Tools.** `lookup_booking`, `verify_caller`, `fetch_policy`, `fetch_event_details`, `find_performance`,
`check_exchange_eligibility`, `check_refund_eligibility`, `check_availability`, `exchange_tickets`,
`issue_refund`, `transfer_booking`, `change_holder_name`, `send_confirmation`,
`check_access_requirements`, `reserve_seats`, `log_dispute`, `check_resale_eligibility`,
`transfer_to_specialist`.

**`transfer_to_specialist` was added for CALL-20** and is the only tool that hands the *call* itself
to someone else — `transfer_booking` moves a booking between holders and is a different thing that
reads alike, which is why both names are spelled out here. It takes a `queue` and a `summary`. The
`summary` argument exists because a handoff that carries nothing is only expressible against a
payload that was supposed to carry something: without the argument there is no defect to see, only
an absence to argue about.

**The inventory is declared here so that "the capability existed and was not used" is checkable.**
Several findings turn on exactly that, and an absence can only be a finding against a list somebody
wrote down — not against whatever happens to appear in a transcript.

**So the two directions are not symmetric.** A name declared here and never used is the inventory
working as intended — `check_access_requirements`, `check_resale_eligibility` and `log_dispute` are
each cited by a finding *because* they were available and were not called. A name used in the corpus
and not declared here is always a defect in this register: it means the corpus invented vocabulary
its own canonical list does not know about, and every check keyed to the list silently stops covering
it. `tests/test_corpus_hygiene.py` asserts that direction — used implies declared — over the design
set, which is every transcript this repository can see. The held-out set is not in this tree and this
check does not reach it; keeping the two consistent is a manual step at authoring time, and that gap
is stated here rather than left for a reader to discover.

**Closed vocabularies** are format contracts, not corpus inventories, and the distinction is
worth stating because it was conflated once. They are specified in `specs/event-model.md` §3.3 —
tool-result `status`, `disconnection_reason` and disclosure `state`. `ToolStatus` and `EventKind`
are demonstrated in full by the corpus and each has an exercise test. `DisconnectionReason`,
`DisclosureState` and `Outcome` are broader than any corpus needs — they carry what real platforms
emit, so an adapter receives what vendors send (D39) — and the corpus shows the subset its calls
have occasion to. Every token of all five is asserted to round-trip through the parser; what the
corpus demonstrates is asserted separately. Neither claim stands in for the other, and no token is
exempted.

**This was two paragraphs with the same bold opening until 2026-09-07**, the second stating where
the vocabularies are specified and the first stating what they are for. A reader met the same three
words twice and had to work out that the second was not a restatement of the first.

**Context variables** (injected before the call).

*Identity and account:* `caller_ani`, `matched_account_id`, `matched_by`, `account_holder_name`,
`account_zip`, `account_email`, `identity_verified`, `caller_verified`, `holder_confirmed`,
`open_bookings`.

`matched_by` records *how* the account was found and its values are deliberately not a closed vocabulary.
Every design call is matched on `caller_ani` except CALL-18, which is matched on
`booking_reference`, because the caller there is not the account holder and the number they call
from is not on the account. That difference is the whole subject of that call and closing the
vocabulary would have made it unstateable.

**The distinction is `matched_by`, not what a context record carries.** This sentence used to count
the calls carrying `caller_ani` and state the count, and it was wrong twice over: the count had gone
stale by addition, and counting that variable was the wrong claim to begin with, because every design
call carries both a calling number and a booking reference. Only the value of `matched_by` separates
them. Rewritten rather than re-pinned (D74): a quantified claim is checkable and decays, and this one
had no check.

*The booking:* `booking_reference`, `event_title`, `event_id`, `ticket_count`, `price_band`,
`price_band_note`, `ticket_price_total`, `booking_fee`, `currency`, `payment_instrument`,
`purchased_at`, `charge_count`, `delivery_state`, `delivery_attempts`.

*Windows and eligibility:* `exchange_window_closes_at`, `refund_window_closes_at`,
`transfer_window_closes_at`, `refund_band`, `transfer_state`, `current_holder`, `resale_eligible`.

*Event status:* `event_state`, `reschedule_announced`, `cancellation_announced`.

*Scheduling:* `door_time`, `original_door_time`, `venue_timezone` — the second only where an
event has moved,
so a reader can tell a reschedule from a booking that was always on this date. The first two are
UTC instants and nothing in the corpus carries a local time; `venue_timezone` is what makes
the conversion checkable rather than a matter of assuming where the venue is. It was added
because a finding about a spoken local time has no oracle without it — the caller's own
recollection cannot serve as one, for the reason F-59 gives.

*Payment:* `billing_zip` — the ZIP the card is billed to, distinct from
`account_zip`. It is declared separately because it is an AVS factor: disclosing it is uplift
for card-not-present fraud elsewhere, which is a different harm from disclosing an address.

*Internal, not for disclosure to the caller:* `internal_note`. **This is a declared set, not a
sentence.** `tests/test_corpus_hygiene.py::test_no_internal_field_reaches_the_caller`
asserts that no agent turn shares distinctive vocabulary with one of these fields, in any
call except those named as seeding a disclosure. It began as prose — the constraint lived in
this paragraph and in the finding reporting its breach — which is the shape this project keeps
finding in itself, so it was replaced by the check rather than left as a claim about care.

*Disclosure state:* `disclosure_refund_timing`, `disclosure_ai_status` — whether the platform
believes a mandated statement was already delivered. It is context rather than a `DISCLOSURE` event because it records the
platform's belief going in, not something that happened in the call.

Two pairs are easy to conflate and are not the same thing. `identity_verified` is the platform's
verification flag; `caller_verified` is the precondition a write tool tests, and `holder_confirmed`
records only that the caller said yes when asked. `price_band` is a catalog name; `price_band_note`
is the human-readable gloss the agent may read aloud, and a value in it is not a fact about
eligibility.

**State variables** (set during the call): `identity_verified`, `exchange_eligible`,
`refund_eligible`, `transfer_target_name`, `transfer_target_email`, `dispute_reference`,
`access_requirement`, `caller_verified`, `holder_confirmed`.

`identity_verified` appears in both lists deliberately: the platform supplies it at call start and is
supposed to update it. A context variable that should have changed and did not is a **platform**
defect, and that is only sayable because context and state are separate records.

**`caller_verified` and `holder_confirmed` are declared here and written in no transcript, which is
the inventory working as intended.** Both are also tool-result detail keys, and the pair above says
why they are not the same thing as `identity_verified`. They are listed as state variables because
the rubric asks for them as states: `A-precondition-satisfied-by-assertion` reports a call where an
argument asserted a precondition and no `STATE` event recorded it, and
`A-repeated-request-with-no-record` reports a question asked twice with no `STATE` event answering it
in between. Both findings **are** the absence, so the design set emits neither name and the register
must still permit them — otherwise the name a check is looking for is one the corpus is forbidden to
contain, and the negative instance those entries lack could never be authored. Added 2026-09-08 on
the owner's decision, after D117 recorded the mismatch rather than closing it.

**Disclosure names.** `recording_notice`, `refund_timing`, `exchange_timing`,
`transfer_irreversible`, `ai_status`. The last is declared and, in the design set, never
emitted: CALL-12 carries `disclosure_ai_status` in context and no `ai_status` event, which
is the defect F-57 states. A name declared and unused is the inventory working as intended.

**Outcomes.** `resolved`, `unresolved`, `transferred`, `abandoned`. Closed and validated at
extraction, like `disconnection_reason` and for the same reason: both are the platform's own claim
about the call and neither is recomputed, but an unrecognized token is not a disputed claim — it is a
value nothing can compare against.

**System event names.** `call.answered`, `call.ended`.

**Tool arguments.** `account`, `amount`, `assume_verified`, `band`, `booking`,
`difference_accepted`, `document`, `event`, `name`, `production`, `queue`, `readback_confirmed`,
`reference`, `summary`, `target_event`, `to`, `venue`, `when`, `zip`.

**Tool-result detail keys.** `accepted_by`, `at`, `available`, `band`, `booking`,
`caller_verified`, `charged`, `closed_at`, `code`, `difference_due`, `door_time`, `eligible`,
`event`,
`exchange_id`, `expected_days`, `gate`, `holder`, `holder_confirmed`, `internal_note`,
`last_confirmation`, `match`, `measured_from`, `message_id`, `note`, `previous`, `price_band`,
`queue`, `reason`, `refund_id`, `remedy`, `rescheduled_at`, `reversible`, `scanned`, `scanned_at`,
`settlement`, `status`, `ticket_count`, `title`, `transfer_id`.

**Tool-result detail values.** Two of the keys above carry a vocabulary rather than a datum: a
`reason` and a `remedy`. Their values are `window_closed`, `booking_transferred` and
`reversal_by_current_holder` — a reason code is where the platform says *why*, so a value the
register does not know is a case nobody enumerated (D198). The other keys hold identifiers,
amounts, timestamps and free text, which are data rather than vocabulary. A
`call.ended(reason=...)` is a different thing that reads alike: that is a disconnection reason,
a closed vocabulary of the event model, declared in `specs/event-model.md` §3.3.

**These three were added because the rule had a scope nobody had written down.** The rule is *used
implies declared*; it was enforced over six kinds of name and the corpus uses nine. The three
missing ones were not chosen — they were what a sweep found, and one of them mattered:
`call.answered` opens every call and `call.ended` closes all but one; that absence is CALL-12's
seeded taxonomy 32 omission, and the only thing holding either was two string literals inside one
assertion. `assume_verified` is CALL-12's verification bypass and `difference_due` is cited by findings;
both were names the canon had never seen.

**The alternative was to state the exception, and it was rejected.** Writing "the register does not
enumerate argument names or result keys, and here is why" would have been honest and would have left
the rule with a carve-out — and a carve-out is what a later reader extends. Nine kinds, no
exemptions, is shorter to state and harder to erode. It also costs almost nothing: these are names
the corpus already fixed, and enumerating them means a *new* one has to be declared deliberately
rather than arriving unnoticed.

**Outcome reasons.** `exchange_completed`, `refund_issued`, `transfer_completed`, `name_changed`,
`information_provided`, `escalated`, `unresolved`, `caller_abandoned`.

**`escalated` was added for CALL-20**, and the gap it fills is worth recording rather than quietly closing. The set had no value for a call handed to a human, so a correctly-escalated call could only be filed as `unresolved` — making the metric that would show escalation working the metric that reports it as failing. `transfer_completed` does not fill it: that names a *booking* moving between holders, which is a different event that reads alike, and which is why both names are spelled out together here. The heading used to read "Reason codes",
which is what the field was called before it was renamed `outcome_reason` — the register naming a
field that no longer exists, in the document whose job is to be the canonical list.

**Which `outcome` an escalation takes.** The vocabularies above declare `escalated` and `transferred`
and say nothing about how they combine, which left the answer to be inferred. It is a corpus-wide
convention rather than a per-call judgment, so it is written here. A call handed to a human sets three
fields answering three different questions, and no field stands in for another:
`disconnection_reason: transferred` records **how the call ended**; `outcome: resolved` records
**whether the caller's need was met** — getting them to someone who can settle it *is* the resolution
available; and `outcome_reason: escalated` records **why**. A handoff that *fails* takes
`outcome: unresolved`; the other two fields are unchanged. A metric reading a transferred call as a
failed one is reading the wrong field of the three.

**`Outcome.transferred` is never that value, and this is the only place that says so.** It is in the
closed vocabulary because real platforms emit it and an adapter has to receive what vendors send
(D39) — not because a call authored here should carry it. `disconnection_reason` already records how
a call ended, so `outcome: transferred` straddles the two axes those two fields exist to separate, and
a platform emitting it has said nothing `disconnection_reason` had not already said. D73 named it a
schema smell and left open whether it should be removed. **The answer recorded here is no:** removing
the token would make the parser refuse a real vendor's export, which is a worse failure than a token
no transcript writes.

So it is declared and unused — but for a different reason from `check_access_requirements`,
`check_resale_eligibility` and `log_dispute`, which are capabilities a call could legitimately have
used and did not. Those are the inventory working as intended. This one is unused **because using it
would be wrong**, and a register that did not separate the two would be offering a reader a value it
does not want them to pick.

**This paragraph sits here rather than in `corpus/seeding-manifest.md` deliberately.** The convention
lived only in the manifest, which is a design-set artifact, and in one machine's project memory, which
lives outside both repositories and which no reviewer ever sees. An authoring session working from a
curated packet receives the register and not the manifest — so it had the vocabulary and not the rule,
and set the field wrongly. Neither the author nor the packet erred; the register did not say. **The
register travels with the entity canon and the manifest travels with the labels**, so a convention
about what a record means belongs with the canon. Written without naming any transcript, so that it
survives the redaction a packet applies and reaches the next author intact.

## Class 7 — call identifiers and file naming

Design set: `CALL-01` … `CALL-12`, `CALL-18`, `CALL-19`, `CALL-20` and `CALL-22`, one file each at `corpus/transcripts/CALL-NN.txt`, declared in
`corpus/DESIGN_SET`.
**`corpus/DESIGN_SET` is the declaration; this line is prose about it and went one call stale when D73
added `CALL-20`.** Nothing compared the two, which is why it stayed wrong — the register naming a set
it did not match, in the document whose job is to be the canonical list. A test now compares them, so
the second staleness was caught by construction rather than by a reader.
Held-out set: `CALL-13` … `CALL-17` and `CALL-21`, in the companion repository only, never in this
working tree. `CALL-21` was added on 2026-09-06 and takes the next free identifier rather than
extending the held-out block, because `CALL-18`…`CALL-20` are design calls: **the two sets share one
numbering space and neither is a contiguous range.** `CALL-22` was added on 2026-09-08 and takes the
next free identifier after the held-out `CALL-21` for the same reason — the space is shared, so a
design call may follow a held-out one and the next author of either set reads both declarations
before choosing a number.
