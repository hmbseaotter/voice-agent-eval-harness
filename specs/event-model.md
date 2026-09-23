# The canonical event model

**Status:** v3. This is the contract. Everything else in the extraction tier is a mapping onto it.

**What v3 changed** (D203): the model admits absence. v2 said an adapter records what its source
cannot supply as unavailable and gave it nowhere to record it — every field was required, so the only
way to build a call from a source that lacked one was to default it, which §5 forbids. v3 gives the
call an `unavailable` list drawn from a closed vocabulary of gaps (§5), and lets exactly the fields
a surveyed platform was found not to carry be absent: an event's timing, and the record's
`answered_at` and `environment`. It was found by writing the second adapter against Retell's
documentation rather than against this table.

## Why this document exists separately

The harness evaluates calls. It does not own the format those calls arrive in, and it must not: every
voice platform logs differently, and an engineer adopting this harness already has logs in whatever
shape their vendor emits. A harness that only reads one invented format is a demonstration, not a
tool.

So the layering is:

```
vendor log  ──adapter──▶  canonical event stream  ──▶  checks, judges, report
(their shape)             (this document)              (never sees vendor shape)
```

**Nothing above the adapter line knows which platform a call came from.** That is the property the
second adapter exists to prove, and it is why the canonical model is specified before any
serialization of it.

## What the canonical model is designed against

The model is a **fusion of what real platforms already emit**, not an invention. Each element below
exists because production voice platforms log it; the mapping table in §4 names which concept each
one corresponds to. Where platforms disagree, the model takes the union and the adapter records what
its source could not supply.

This is a correction to an earlier assumption. The transcript format's first version carried a single
timestamp per event on the stated grounds that "start-stamped logs are what real systems
overwhelmingly emit". That premise was never checked and is false — real platforms carry turn start
*and* end, word-level timing, and separate STT/TTS windows. A model designed from a guess about the
world will not receive what the world sends.

---

## 1. The call record

| Field | Meaning |
|---|---|
| `call_id` | Stable identifier joining transcript, tool calls and outcomes. |
| `agent_id`, `agent_version` | Which agent, which release. Regression analysis needs both. |
| `environment` | `production` \| `staging` \| `test`. **May be unavailable** (v3): Retell's call object carries none. |
| `direction` | `inbound` \| `outbound`. |
| `from_number`, `to_number` | Endpoints. |
| `started_at`, `answered_at`, `ended_at` | UTC ISO-8601, millisecond precision. **Three, not two**: ring-to-answer is a real interval and collapsing it loses it. **`answered_at` may be unavailable** (v3), and is then absent rather than copied from `started_at`, which would report that interval as zero. |
| `duration_ms` | As the platform reports it — *not* recomputed. |
| `disconnection_reason` | Closed vocabulary, §3.3. |
| `outcome`, `outcome_reason` | The platform's own disposition labels. `outcome` is a closed vocabulary, §3.3. |

**`duration_ms`, `disconnection_reason`, `outcome` and `outcome_reason` are the artifact under test, not
ground truth.** They are what the system claimed. A harness that reconciled them on read would delete
the defect it exists to detect.

## 2. The context record — what the agent could see

A map of variables injected into the agent's prompt **before the conversation began**.

This is not a convenience. It is the difference between two findings that look identical in a
transcript and have different owners:

- the agent had a value and misused it — **an agent defect**;
- the agent never had the value and asserted it anyway — **also an agent defect, but a different
  one**;
- the platform should have supplied the value and did not — **a platform defect**.

Without a record of the agent's information set, all three read the same and a finding cannot say
which it is. Every platform surveyed has this concept (§4); the harness's first format omitted it,
and the first human review of the corpus found exactly the ambiguity that omission produces.

**A variable declared in the context record is one the platform maintains.** If it should have
changed during the call and did not, that is a platform defect and is assertable. A variable that
appears nowhere at all is a design gap, which is a different finding again.

**Each pair carries its provenance**, the way every event carries `source_ref` (§3): which lines of
the source it came from, aligned with the pairs by position. This was missing, and the context record
was the only part of a call the model could not describe the origin of — so a test asserting the
`[context]` block's wrapping had to re-implement the parser to work out how many lines a value
spanned. An adapter whose source has no line numbers records the provenance its source can supply,
or records that it cannot; the rule in §5 is unchanged.

## 3. The event stream

Ordered, indexed, typed. Every event carries:

| Field | Meaning |
|---|---|
| `index` | 1-based position. Strictly sequential. **Ordering checks use this, never timestamps.** |
| `started_at_ms`, `ended_at_ms` | Offsets from the call's `started_at`. An adapter whose source carries both supplies both. **Absent, never zero, where the source carries none** (v3): Retell stamps an utterance's words and gives a tool call and its result no timing at all, and a check that reads timing as a quantity returns `unevaluable` naming it. |
| `kind` | §3.1. |
| `body` | The reassembled raw text of the event. |
| `citation_id` | `T<n>` for speech, `F<n>` for established facts. Two populations, §3.4. |
| `source_ref` | Where in the source this came from — line numbers for text, a 1-based record index into the interleaved array for a JSON call object. **Each adapter's own by definition**, so it is the one event field two adapters' streams are never compared on. |

### 3.1 Event kinds

| Kind | Population | Carries |
|---|---|---|
| `CALLER` | `T` | Caller speech. |
| `AGENT` | `T` | Agent speech — the subject under test. |
| `TOOL_CALL` | `F` | `tool_call_id`, `name`, `arguments`. |
| `TOOL_RESULT` | `F` | `tool_call_id`, `status`, **`successful`**, `detail`. |
| `STATE` | `F` | `name`, `value` — a variable set *during* the call. |
| `POLICY` | `F` | `document`, `clause`, `text` — **the clause the agent applied**, not the clause a tool returned. See §3.5. |
| `DISCLOSURE` | `F` | `name`, `state`, `text` — recording notice, consent, mandated statements. |
| `SYSTEM` | `F` | `name`, `arguments` — lifecycle, routing, guardrail events. |

### 3.2 Invocation and result are separate events

**A tool call and its result are two events linked by `tool_call_id`.** This is how every platform
surveyed models it, and it is what makes the following chain expressible:

> read establishes eligibility → write is attempted → **result confirms the write succeeded** → only
> now may anything that depends on it happen

Every step is a distinct event with a distinct index, so *"an action was taken before the
confirmation it depends on existed"* is an ordering assertion over the stream. No judgment required.

`successful` is a boolean carried **separately from** `status`. That looks redundant and is not:
platforms carry both, and a result whose `successful` disagrees with its `status` is a real
data-integrity defect the model has to be able to represent.

**Eligibility is the content of a read, not the status of a write.** A write's result says whether
the write happened. Whether it was *permitted* is something a prior read reported. Collapsing those
was a defect in the first version of this model: it made "the agent proceeded against state that said
it could not" inexpressible, because there was no prior state to proceed against.

### 3.3 Closed vocabularies

**`status`** on a `TOOL_RESULT` — matched case-sensitively:

| Token | `successful` | Meaning |
|---|---|---|
| `completed` | true | A write was performed. |
| `retrieved` | true | A read returned data. |
| `refused_ineligible` | false | A hard rule refuses. No further input changes it. |
| `refused_precondition` | false | A fixable precondition is unmet. |
| `unavailable` | false | The capability could not be reached. |
| `timeout` | false | No response within the tool's budget. |
| `malformed` | false | Rejected as invalid before execution. |
| `error` | false | Unclassified failure. |

The three refusal-and-failure distinctions are load-bearing: the causal pattern behind fabricated
completion is an agent with no error taxonomy, nothing separating a fixable precondition from hard
ineligibility from environmental unavailability. A vocabulary that collapsed them would make "the
agent treated an unavailable service as an ineligible request" unstateable.

**`disconnection_reason`** — drawn from the vocabularies real platforms publish:
`caller_hangup`, `agent_hangup`, `transferred`, `voicemail_reached`, `inactivity_timeout`,
`max_duration_reached`, `network_error`, `asr_error`, `system_error`.

**`state`** on a `DISCLOSURE`: `delivered`, `acknowledged`, `declined`, `skipped`.

**`outcome`** on the call record: `resolved`, `unresolved`, `transferred`, `abandoned`.

`outcome` is closed for the same reason `disconnection_reason` is, and the reason is worth stating
because it looks like a contradiction of §1. **Validating the token is not reconciling the claim.**
Both fields are the artifact under test and neither is ever recomputed — but an unrecognized token is
not a disputed disposition, it is a value nothing can compare against, and a check keyed to it
compares against nothing while appearing to pass. This was open until an audit found the asymmetry:
`disconnection_reason` aborted extraction on an unknown token, `outcome` accepted any string, and the
entity register declared reason codes while declaring no outcomes at all.

`outcome_reason` stays open. It is the free-text half of the pair — the register lists the values the
corpus uses, and the corpus is asserted against that list, but an adapter reading a real vendor log
will meet reasons this project never enumerated and must not abort on them.

An unknown token in any of these aborts extraction, naming the source and the token. A vocabulary
compared without validation is a live risk on a freshly authored corpus.

### 3.4 Two citation populations

`[T<n>]` for speech, `[F<n>]` for established facts, numbered independently.

The rule this enforces: **a validator must validate against the same universe the prompt renders.**
Two distinguishable prefixes make that checkable rather than hopeful.

---

### 3.5 Retrieval returns a document; the POLICY event names the clause applied

`fetch_policy` takes a document and returns it whole. It does **not** take a clause.

The earlier signature was `fetch_policy(document, clause)`, and it could only be called correctly by
an agent that already knew which clause answered the question — knowing that `refund.v1 § 3.2` is
the settlement-timing rule presupposes having read `refund.v1`. A retrieval tool that must be told
where the answer is cannot be used to discover a rule the caller does not know exists, so the clause
argument entered every call from nowhere: no context value, no prior result, no caller turn produced
it. That was found by auditing where every tool-call argument comes from, not by reading the tool's
definition.

So the sequence is three events, and each carries a different claim:

```
TOOL_CALL    fetch_policy(document="refund.v1")
TOOL_RESULT  -> retrieved successful=true :: refund.v1 returned; 14 clauses
POLICY       refund.v1 § 2.2 -> "Where the request is made between 14 days..."
```

**The `POLICY` event is the agent's selection, and that is the point of the change.** Under the old
shape the only expressible defect was *nothing was retrieved*, which cannot separate an agent that
guessed correctly from one that guessed wrongly. Under this shape a sharper class becomes assertable
without a model: **a clause governing the question asked was inside the returned document, and the
agent applied a different one, or none.** CALL-02 is the worked example — `refund.v1 § 2.4` states
the booking fee is non-refundable, it is in the fourteen clauses returned at event 12, and the agent
promised the fee back anyway.

The result's clause count is checkable against the document itself, so a transcript claiming a
retrieval that does not match the policy set fails rather than reads plausibly.

**What this does not change.** Clause correspondence (D32) is untouched: a `POLICY` event still
cites exactly one clause and quotes it, and the quoted text must still equal that clause under
whitespace normalization. Widening retrieval did not widen what a quotation is allowed to say.

## 4. Mapping to platform schemas

This is the table an engineer writing a third adapter reads. It is also the evidence that the model
above is a fusion rather than an invention.

| Canonical | Retell | Vapi | Amazon Connect / Contact Lens | Notes |
|---|---|---|---|---|
| call record | `call_id`, `agent_id`, `agent_version`, `call_type`, `direction`, `from_number`, `to_number`, `start_timestamp`, `end_timestamp`, `duration_ms` | call object + `artifact` | contact record | Direct. |
| `disconnection_reason` | `disconnection_reason` (rich enum) | `endedReason` | disconnect reason | Our vocabulary is a generalization of theirs. |
| context record | `retell_llm_dynamic_variables` | `assistantOverrides.variableValues` | contact attributes | Universally present under different names. |
| `STATE` | `collected_dynamic_variables` | extracted variables | contact attributes set in-flow | Set during, not before. **Retell's is a call-level string map**: it says what was set and not when, so it supplies no positioned event and the adapter declares the gap (D203). |
| event stream | `transcript_with_tool_calls` | `artifact.messages` | Contact Lens turn-by-turn | An interleaved, ordered array in all three. |
| `CALLER` / `AGENT` | `role: "user"` / `"agent"`, `content`, `words[]` | `role`, `message`, `time`, `endTime`, `secondsFromStart`, `duration` | participant turns | Vapi carries start and end directly. |
| `TOOL_CALL` | `role: "tool_call_invocation"` — `tool_call_id`, `name`, `arguments` (a stringified JSON object), **no timing field** | `role: "tool_calls"` — `toolCalls[]`, whose item shape the documentation does not declare | Lambda invocation, in flow logs separate from the transcript | The same idea everywhere and not the same shape: read on 2026-09-20, only Retell's documentation states every field's type (D203). |
| `TOOL_RESULT` | `role: "tool_call_result"` — `tool_call_id`, `content`, **`successful`**, **no timing field** | `role: "tool_call_result"` — `toolCallId`, `result`, no success flag | Lambda result | Retell's `successful` is the confirmation flag this model requires. It is documented as optional, and the adapter refuses a result without one rather than deriving it from the status. `content` is the deployment's own tool response, so its status words are the deployment's to map. |
| `SYSTEM` | `node_transition`, `dtmf`, `injected` | status updates | flow events | Routing and keypad events. **None of the three logs a call's lifecycle as an entry** — Retell's `node_transition` and `dtmf` carry no timing either — so `call.answered` and `call.ended` have no carrier there, and the adapter declares that gap and aborts on the three roles it does not yet map (D203). |
| `DISCLOSURE` | — | — | — | **Not a first-class type in the platform APIs surveyed**, though consent and disclosure delivery are named as distinct logged events in call-logging practice. Adapters that cannot supply it record it as unavailable rather than absent. |

**Where a source cannot supply something, the adapter says so.** A field the source does not carry is
recorded as unavailable, never defaulted — a defaulted value is indistinguishable from a real one,
and a check keyed to it would be asserting on a value nobody supplied.

---

## 5. Writing an adapter

An adapter is a function from a source document to a `Call`. It owes three things:

1. **Ordering.** Events in the canonical stream are in the order they occurred, indexed from 1 with
   no gaps. If the source's ordering is unreliable, the adapter says so rather than guessing.
2. **Vocabulary mapping.** Source status values map onto the closed vocabularies in §3.3. An
   unmappable value aborts naming it — it must not be silently bucketed into `error`, because that
   would convert an unknown into a known-bad and hide the gap.
3. **Honest gaps.** Anything the source does not carry is unavailable, not defaulted. **Unavailable
   is recorded, by name, on the call** (v3): `Call.unavailable` holds members of the closed
   vocabulary in `harness.core.gaps` — an event kind the source has no entry for, tool-event timing,
   a record field, the context record's provenance — and each name is defined by what it removes
   from a complete stream, which is what lets two adapters' streams be compared: the second
   adapter's must equal the text adapter's with its declared gaps applied, so an undeclared
   difference fails and so does a declared gap the adapter filled. A call and its declaration are
   checked against each other in both directions when the adapter builds it.

   **No check reads the declaration yet**, so the seam every tier shares refuses a call that
   carries one: a lifecycle check would otherwise report a missing `call.ended` for a source that
   logs no lifecycle, and a judged prompt would state that no clause was retrieved where nothing
   can know. Such a call can be extracted and cannot yet be evaluated.

An adapter owes **nothing** about scenario content, entity naming or defect seeding. Those are
properties of a corpus, not of a format.

The corpus in this repository is authored in the text serialization specified by
`specs/transcript-format.md`. That format exists because a wrapped, human-readable log is the harder
parsing case and therefore the better test of the tier; it is adapter 1, not the canonical model, and
nothing above the adapter line depends on it.
