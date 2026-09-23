# Transcript format — v2

**Format version token:** `2`. **This is adapter 1's source format, not the contract.** The contract
is `specs/event-model.md`; this document specifies one serialization of it.

Realistic wrapped text rather than line-oriented records or JSONL (D5): a format that forbade
wrapping would design out the bug class the extraction tier exists to catch, and the project would be
teaching a lesson it had arranged not to need.

## What changed from v1, and why

v1 was designed from stated requirements without reference to how production voice platforms actually
log calls. A human review of the first corpus, and then a survey of published platform schemas, found
four things wrong with that:

| v1 | v2 |
|---|---|
| No record of what the agent could see at call start | `[context]` block — universal across platforms under various names |
| One event per tool call, status conflating permission with outcome | `TOOL_CALL` and `TOOL_RESULT` as separate events linked by id, with an explicit `successful` flag |
| One timestamp per event; latency declared unmeasurable | Start **and** end on every event, millisecond precision |
| `terminated_by: caller \| agent \| system` | `disconnection_reason` over a real vocabulary |
| No representation of recording notice, consent or mandated statements | `DISCLOSURE` events |

The third row retires D33. Its reasoning rested on "start-stamped logs are what real systems
overwhelmingly emit", which was never checked and is false. **Taxonomy 33 — a property you intend to
gate on being unmeasurable from the available instrumentation — is a real category and stays seeded,
but by an honest instance rather than by crippling the format.**

---

## 1. File shape

UTF-8, LF line endings. A trailing CR and a leading byte-order mark are both stripped rather than rejected: each is an encoding artifact a Windows editor or checkout can introduce, neither carries anything about the call, and refusing a corpus for either would be a refusal with no defect behind it. Four parts, in order:

```
#format: voice-agent-eval-harness/transcript v2

[call]
<key: value>

[context]
<name := value>

[events]
<event lines>
```

Line 1 is the format marker and is mandatory. Blank lines and `#` comments are ignored below it.

## 2. `[call]`

`key: value`, no wrapping. Required keys, in this order:

`call_id`, `agent_id`, `agent_version`, `environment`, `direction`, `from_number`, `to_number`,
`started_at`, `answered_at`, `ended_at`, `duration_ms`, `disconnection_reason`, `outcome`,
`outcome_reason`.

A missing key is a parse failure naming it; so is an unknown key. Tolerating unknown keys is how a
typo'd key becomes an absent value nobody notices.

Timestamps are UTC ISO-8601 with millisecond precision and a `Z` suffix. `duration_ms` is recorded as
the platform reported it and is never recomputed — see the event model on why these four fields are
the artifact under test.

## 3. `[context]`

`name := value`, one per line. These are the variables the agent's prompt was built with **before the
conversation began**.

```
account_zip := 00312
currency := USD
identity_verified := false
```

An empty `[context]` block is written explicitly as `# none` rather than left blank, so "the agent
was given nothing" is distinguishable from "nobody filled this in".

### 3.1 Wrapping — positional, exactly like §4.1

**A line that begins with whitespace continues the value above it**, and its content is appended
joined with one space. A line beginning in column 0 must be `name := value`; anything else is a parse
failure naming it. A `#` in column 0 is a comment; an indented `#` is content.

```
disclosure_refund_timing := Refunds are issued to the original payment method
    and reach your statement within five business days. The booking fee is not
    refundable.
```

**This rule was missing, and its absence corrupted silently.** §3 said only "wrapping permitted", and
the parser used a *content-based* rule — any line not matching `name :=` continued the previous
value — while its own docstring described that as "the same continuation rule as the event stream",
which is positional. Two consequences, both reproduced by an independent audit:

| Written | Parsed as |
|---|---|
| a wrapped value whose continuation contains ` := ` | **two variables**, the second fabricated |
| a wrapped value whose continuation begins with `#` | **one variable with its tail deleted** |

Neither produced an unparsed line, an error, or a counter. That is **W17** — a fabricated fact
entering the record from punctuation — and **W16** — a fragment silently lost — reappearing in the
one block for which this document never wrote a rule. The context record is what decides whether a
finding's owner is the agent or the platform (`specs/event-model.md` §2), so a fabricated variable
there is not a cosmetic defect.

The polarity is the fix. A positional marker cannot collide with the content it delimits; a
content-based one collides with exactly the values most worth wrapping.

## 4. `[events]`

Five pipe-delimited fields:

```
<index> | <start> | <end> | <KIND> | <body>
```

- **index** — 1-based, strictly sequential, written explicitly so a hand-edited transcript that loses
  an event fails to parse rather than silently renumbering.
- **start**, **end** — `M:SS.mmm` offsets from `[call] started_at`. Minutes may exceed two digits.
  Both required; for an instantaneous event they are equal.
- **KIND** — one of the eight in the event model, uppercase, case-sensitive.
- **body** — the kind-specific syntax in §5.

Whitespace around fields is insignificant. Alignment is cosmetic.

### 4.1 Wrapping — one rule, all kinds

**A line whose index field is empty continues the event above it.** Its body is appended, joined with
exactly one space. The index, start, end and kind fields of a continuation must all be empty.

```
 12 |  0:41.100 |  0:48.930 | AGENT | Thanks — I've got the booking here. Before I
    |           |           |       | change anything, can I take the ZIP code on
    |           |           |       | the account?
```

The rule is stated over **events, not turns**. In the implementation this project diffs against, the
wrapping rule covered turns, so a wrapped variable value silently lost its leading fragment while the
adjacent branch handled the identical case correctly. A rule with one branch cannot develop that
asymmetry.

A body containing a literal newline is not representable. Values wrap at spaces or they do not wrap.

## 5. Event bodies

| KIND | Body |
|---|---|
| `CALLER` | free text |
| `AGENT` | free text |
| `TOOL_CALL` | `<id> <name>(<args>)` |
| `TOOL_RESULT` | `<id> -> <status> successful=<true\|false>` , optionally ` :: <detail>` |
| `STATE` | `<name> := <value>` |
| `POLICY` | `<document>.<version> § <clause> -> "<text>"` |
| `DISCLOSURE` | `<name> -> <state>` , optionally ` :: "<text>"` |
| `SYSTEM` | `<dotted.name>` or `<dotted.name>(<args>)` |

```
  9 |  0:41.100 |  0:41.180 | TOOL_CALL   | t4 exchange_tickets(booking="BK-4471-QD", target="EV-88120")
 10 |  0:41.180 |  0:43.902 | TOOL_RESULT | t4 -> refused_ineligible successful=false :: exchange window closed
```

`<id>` is a call-local identifier matching `^t\d+$`. Every `TOOL_RESULT` must reference a `TOOL_CALL`
that appears **earlier** in the stream, and every `TOOL_CALL` must have exactly one result. Both are
checked at extraction; a dangling call or an orphan result is a parse failure naming the id.

**There is no untyped catch-all kind.** The implementation this project diffs against classified any
system note containing an `=` as a variable, so fabricated "facts" flowed into the grounding blob and
the judge's established-facts block. The structural fix is that every line declares its kind in a
dedicated field, so nothing is inferred from punctuation and there is no unconstrained kind for a
fabricated fact to occupy.

## 6. What this format does not carry

**No audio layer.** Barge-in, endpointing, ASR and TTS defects do not survive into text. Real
platforms carry word-level timing and STT/TTS windows; this format carries neither, because the
corpus has no audio behind it and inventing per-word timings would be fabricating precision.

That omission is itself the honest instance of taxonomy 33: **event-level start and end make the gap
between two events computable, but not its attribution.** A silence containing no tool call cannot be
divided into model latency, deliberate pause, and caller think time — the instrumentation does not
carry what would separate them. The correct output is a finding against the telemetry schema, not a
guessed measurement.

---

## 7. Changelog

- **v2.1** (2026-08-29): §3.1 added — the `[context]` continuation rule, which this document had
  never stated. The parser had one anyway, it was content-based where §4.1's is positional, and
  the difference fabricated a variable from any wrapped value containing `:=` and deleted the tail
  of any beginning with `#`. Found by an independent audit; both cases reproduced.
- **v2** (2026-08-28): restructured against published platform schemas after a human review found the
  format could not express what the first corpus needed. `[context]` added; `TOOL_CALL`/`TOOL_RESULT`
  split with a linking id and an explicit `successful` flag; start and end timestamps at millisecond
  precision; `DISCLOSURE` and `SYSTEM` kinds; `disconnection_reason` replacing `terminated_by`. The
  canonical event model moved to `specs/event-model.md`, which this now serializes rather than
  defines.
- v1 (2026-08-28): initial specification, co-developed with the text adapter against two pilot
  transcripts.
