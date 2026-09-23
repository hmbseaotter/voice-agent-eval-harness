# Handover — phase 6 opened, and what spends nothing built

**Status: open.** Opened 2026-09-20 by the session OB-47 owed: phase 6's contract reading, its
forks settled with the owner, and the deliverables that need no model call. Decisions D201 to D206,
specification 0.61.0. No live model call was made, no rubric or prompt file was touched, and nothing
from the held-out repository was read.

## What happened

**The contract was read before anything was built, and the reading found more than criteria gaps**
(D201). Of phase 6's four requirements, one had no criterion and could not be met as written, one
could not be satisfied under the frozen prompt, and two were covered in half. Every fork was put to
the owner as a selectable question and every answer is recorded in the decision it produced.

- **The second adapter's requirement was written for a format this project no longer has** (D203).
  It asked for a stream byte-identical to the text adapter's, and was not re-read when the adapter
  was retargeted to a real platform. It now asks for a stream that differs only where a declared gap
  names what the source cannot carry. All sixteen design calls compare equal on those terms.
- **The caching requirement asked for something the frozen template cannot give** (D204). Each
  dimension's question sits in the system message, ahead of the transcript, so no cached prefix
  holds a transcript for two dimensions. It is retargeted to the repetitions of one dimension.
- **The tracing convention stays, and phase 6 reports under it** (D202). The first recommendation
  rested on a gloss the owner's question exposed as wrong: `detectable_by` is assigned by kind of
  oracle (D42), not by cost. The decision does not depend on the gloss and the record says so.
- **OB-7 is closed by a firing table**, not by a figure: the judged family joins `FAMILY_TABLES`,
  and `JUDGED_AGREEMENT_PENDING` is empty.

**Which platform's documentation was read, and when.** Retell's, Vapi's and Amazon Connect's public
documentation, all on **2026-09-20**, by three sub-agents of the session told to quote field names
verbatim, give a URL for each fact and mark anything inferred. The adapter is written against
**Retell's `GET /v2/get-call/{call_id}`**, response schema `V2PhoneCallResponse`, from the OpenAPI
document the Get Call page embeds, `x-retell-spec-revision: 2026-09-14-b240eb0`
(`docs.retellai.com/api-references/get-call.md` and `docs.retellai.com/openapi-final.yaml`). Vapi's
was read from `api.vapi.ai/api-json` and Connect's from the Admin Guide's contact-record and Contact
Lens pages; D203 records why neither could be written against as documented. **The field table in
`src/harness/corpus/retell_adapter.py` was typed from those reports by one session on one day**, and
nothing re-reads the documentation.

**What was built**, each with tests and controls: the second adapter, its generator and sixteen
source documents under `corpus/retell/`; the event model at v3, admitting absence, with a closed
vocabulary of gaps; the log inspector, `harness inspect`; per-instance severity, `harness severity`,
with `severity-properties.yaml`; the README's license statement, asserted for the first time; the
judged firing table; and `tools.verify_phase6`, in `VERIFIERS` and in CI, ticking six criteria and
declaring six not yet built.

**Two things the new instruments found on their first reading**, neither fixed here:

- **Every informed retry in the committed reference log is the synthesis citing a fact identifier it
  is given no fact lines to cite**, and two of the eight cited identifiers its prompt shows inside
  the other dimensions' rationales (D205). The prompt shows the model an identifier and then refuses
  it. The template is frozen.
- **Per-instance severity agrees loosely with the ranked bands** on the design set: the rule that a
  misinformed caller with no handoff is medium puts seventeen instances there whose traced findings
  are ranked low (D206). The table is printed and gates nothing.

## What is owed

### 1. No check reads a declared gap, so a call from the second adapter cannot be evaluated

A `Call` whose source declares a gap is refused by `build_context`, by name, because every consumer
would turn the absence into a claim: the lifecycle check would report a missing `call.ended` for a
source that logs no lifecycle, the rule-without-retrieval check would fire where nothing can know
what was retrieved, and the judged prompt's explicit negative statement would say no clause was
retrieved. So `--adapter retell` exists on extraction alone. Owed: each check, and each fact renderer
of the judged prompt, declares what it reads, and one reading something the call declares unavailable
returns `unevaluable` naming it; then `harness run` can take the second adapter. This is what the
phase's goal, *the properties a reader will test*, still lacks most: nothing yet shows a verdict over
a vendor's log.

### 2. Prompt caching is specified and not built

D204's requirement and its two criteria are declared not yet built in `tools.verify_phase6`. One
criterion needs no model call: the requests for two repetitions are byte-identical through the last
cache breakpoint, the synthesis's differ only after it, and no request's hash moves. The other reads
a live response. Owed to a session briefed to spend, under D152's and D161's rule: the expected cost
beside the most it can cost, and approval before the first call. `harness inspect` already measures
what caching can serve, 88 of 104 entry-call pairs on the committed log.

### 3. Judge-model comparison is specified and not built

Three criteria, declared not yet built: per-model agreement for every named candidate, every
candidate's log naming one rubric hash and one template hash with requests differing in the model
alone, and the report stating the tracing convention beside every figure with no candidate ordered
by false alarms (D201, D202). `SUPPORTED_MODELS` names two models and a candidate outside it needs
adding there and to the pricing table, which is code and not rubric. A candidate's minimum cacheable
prefix differs by model. Owed to the same session as item 2.

### 4. The design document is unwritten, and three of its four parts have no source in this tree

D200 gave it to phase 6 and D201 gave it a criterion and a session of its own. **Searching the
decision record for its named parts finds them only in D200**: the runtime guardrail's shared rule
and recommended implementation, the three deployment cadences and the four-stage gate ladder are
named in the specification and described nowhere. `specs/taxonomy-coverage.md` carries the
guardrail's motivating weakness, and D33 and D72 carry the audio-layer question. The specification
says the document is written *from the decision records*, and for three parts there is no record to
write from. Owed: before any prose, the owner says where those three parts' content comes from, and
whether that source is inside the clean-room boundary.

### 5. The version-2 cycle reads every judged false alarm three ways

D202: each of the 19 judged false alarms on the design set lands on a call carrying findings, and a
human reads each into one of three, the entry's question reaches an existing finding, so a trace is
added, across tiers or within one, which also gives P5-9's CALL-12 finding its second trace; the
judge found a conversational defect the gold set lacks, so a judge-type finding is added (D43); or it
is a true false alarm. `J-call-synthesis` gets a call-level expected set. Both existing sets' traces
are frozen or sealed, so this lands with the version-2 rubric and phase 7's fresh held-out set,
labeled that way blind.

### 6. The synthesis prompt shows identifiers it does not let the model cite

D205's first reading. The dimensions' rationales, rendered into the synthesis prompt, quote their own
fact citations, and the synthesis is given no fact lines. All eight informed retries of the committed
log follow from it. A finding about `prompts/judge-dimension.v1.md`, which is frozen, so it is the
version-2 cycle's: either the synthesis is given the fact lines, or the rationales are rendered with
their citations removed.

### 7. Per-instance severity's declarations are one session's judgment

The 43 declarations in `severity-properties.yaml` were authored in one pass and are for the owner's
review; the table against the ranked bands is the instrument, and tuning toward the design set would
be in sample. Two limits are structural and recorded in D206: a judged instance's citations are not
carried past the roll-up, so its evidence point is the start of the call, and a defect of the record
or of an absence has no evidence point at all.

### 8. The second adapter maps four of Retell's nine roles, and no real vendor log has been read

`node_transition`, `dtmf`, `sms`, `injected` and `transfer_target` abort by name. Section 4 of the
event model maps three of them to `SYSTEM` without saying how an untimed one is positioned. No real
vendor log is in this tree, by rule, so the claim the adapter supports is that it reads Retell's
documented shape, as one session read the documentation on 2026-09-20. Owed when either moves: the
field table re-read against the documentation when `x-retell-spec-revision` changes.

### 9. A specification sweep is due at this phase's close

Six decisions have accrued since the sweep recorded at 0.60.0, of the ten the trigger allows, and
*at phase completion* fires when this handover closes. `Last swept` was deliberately not moved
(D194).
