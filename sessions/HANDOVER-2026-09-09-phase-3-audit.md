# Handover — remediating the phase-3 audit

**Status:** open. Opened 2026-09-09, from `19f2985`. Answers
`sessions/AUDIT-2026-09-09-phase-3.md`, which is a report rather than a prompt — so this document
answers findings rather than a contract, and the audit's own working-status banner is where each
finding's disposition is recorded.

**Where the numbers stand:** 23 findings, every one evaluated and every reproducible one reproduced
independently before it was acted on. Decisions D127–D129. Specification swept and bumped to 0.27.0,
which is the trigger the audit found had fired twice with nothing watching.

---

## What an audit is worth, measured

The report was produced by a different model than built the phase, and it did something this project
had not: it ran a **mutation sweep** instead of a reading. Fourteen fail-open-shaped defects restored
one at a time into a copy of the tree, against the five judged-tier test modules. Seven caught, seven
not.

**Every claim it made about a mutation reproduced here, independently, before anything was changed.**
That mattered more than it sounds: the phase-2 audit had three of seventeen findings that needed
correcting first, one of which cleared a call if taken literally. This one had none — the mutation
results came back identical, including the single CAUGHT among the scrubbed run-log fields, which is
the positive that makes the six MISSED believable.

The sweep is worth copying. It is a **different instrument from the control register**, and the
difference is the whole finding: the register audits *controls*, so a check nobody planted a control
for is invisible to it. That is `OB-2`, which had sat open and abstract since 8 September. It now has
seven instances, and every one is a guard that exists in the code and is driven by nothing — the
refusal is there, the scrub is there, the exit code is there, and the suite would not have noticed
their removal.

---

## The seven the suite could not see

| what | what removing it did |
|---|---|
| `LiveTransport`'s credential refusal | 159 judged-tier tests stayed green. The only test naming `CredentialMissingError` constructed the exception to read its message; every transport the suite built was handed a fake key. |
| the judged tier's exit 3 on `errored`/`unevaluable` | stayed green. A run that errored on all 160 calls and exited 0 was nobody's failure. |
| the judged tier's exit 3 on an aborted run | stayed green. |
| `scrub_credentials` on the transport's error messages | stayed green, and the call was bound to the *working directory's* `.env` rather than to the root the CLI resolved. |
| `scrub_credentials` on `response_text` | stayed green. |
| `scrub_credentials` on `system` | stayed green. |
| `scrub_credentials` on `prompt` | **caught** — the one test planted its key there. |

**The last row is why the other six are believable.** A sweep that caught nothing would be a sweep
that mutated nothing, which is the failure `tools/verify_controls.py` exists because of.

---

## The two that were not about code

**A stated security property that was false.** `credential_environment` answered two questions with
one mapping: *which key do I authenticate with*, and *what do I remove from a log*. Resolving the
first discards the loser — an exported variable beats a `.env` one of the same name — so the second
never saw it. The module's docstring said the opposite in as many words, and the test named for that
case put the two values under **two different variable names**, so nothing disagreed and both
survived. It was green on a neighbor of its own subject for as long as the `.env` route existed.

There was no exposure: the losing value is never sent, so it cannot come back in a response, and no
path printed it. What was wrong was the claim.

**A documented credential route that could not work.** `.env.example` offers `ANTHROPIC_AUTH_TOKEN`
as an alternative to `ANTHROPIC_API_KEY`, and the transport passed whichever it found as `api_key=`.
The SDK sends `api_key` as `X-Api-Key` and `auth_token` as `Authorization: Bearer` — read off two
constructed clients rather than inferred — so a token supplied that way went out under the wrong
header and produced a 401 with no message saying why. A documented route that cannot work is worse
than one that is not documented, because it is the one somebody follows.

---

## Two counts that were wrong, and one of them was mine

**The phase-3 verifier's closing line was wrong the day it was written.** It printed "21 of them the
specification's own [P3] acceptance criteria" over a document carrying 18: it counted every anchored
entry, and three of its anchors point into requirement prose rather than into the criteria section.
Phases 1 and 2 each have a test binding their list to the document — added at 0.15.0, after exactly
this — and **phase 3 shipped without one**, so a `[P3]` criterion added to the specification and
never added to the tool was invisible.

`tests/test_phase3_acceptance.py` binds all three, parameterized, so phase 4 adds a row rather than a
fourth copy. `criteria_in_document` lives in `verify_phase1` and is called by every summary, so the
number printed and the number asserted are the same number.

**The pre-flight estimate was below every recorded input count.** On all sixteen calls, by 1.30 to
1.37. Its divisor was reasoned from English prose; these prompts are tagged identifiers, JSON and
clause text. The total stayed a ceiling only because the output side is bounded at `max_tokens`,
which is luck rather than design — and this is the number a human approves a spend against. The
divisor is measured against the committed log now, and the check the decision record described as
"available and not built" is built.

---

## Four sentences that asserted what a test denied

Three said the prompt template's comments are hashed. They are not, deliberately: hashing a comment
refuses a replay for an edit that could not have altered a response, and finding that out cost a
recorded run. The fourth is the one worth sitting with — **D125's `Rule` line stated the behavior of
a fix the same entry records as reverted two paragraphs above.** The Rule line is the sentence the
README tells a reader to trust.

That is not a typo. It is what happens when a decision is written while the fix is being attempted
and the conclusion arrives afterwards: the summary was written from the plan. The correction is dated
and names the test that pins the actual behavior.

---

## The gate found two things in the remediation, and one of them was in the gate

Seventeen controls were planted here. `tools/verify_controls.py` refused two of
them on its first full run, and both refusals were correct.

**A control asserting a neighbor of its own property.**
`test_a_credential_that_contains_another_is_redacted_whole` was written to prove
the scrub order: longest value first, so a value containing another does not get
replaced inside it and leave a live tail. It asserted `"0123456789" not in
scrubbed`. The digits are gone **either way** — the shorter value consumes them —
and what survives a declaration-order scrub is the longer value's tail, `-ext`,
sitting beside a redaction token that reads as though the job was done. Green
with its defect restored, which is the guard-narrower-than-its-rule shape this
project keeps finding, arriving in a control written to close a finding about
exactly that. Asserted as an exact string now.

**A mutation that removed a check instead of restoring a defect.**
`test_every_register_row_still_points_at_the_obligation_it_was_written_for` was
registered with `if anchor not in title:` → `if False:`, and stayed green —
correctly. With no drifted row in the register there is nothing for that
comparison to find either way, so deleting it changes nothing. **A control has to
be driven by a defect that produces a difference.** The mutation now renames
every harvested heading under its number, which is the state the guard exists to
detect.

That is the third and fourth time this gate has printed something that was not a
finding about the control it named, and this time one of them was not a finding
at all:

**The gate misreported a working control, and stopped.** `run_control` refused
any run whose output contained the substring `ERROR`, on the reasoning that
pytest prints it when collection fails. It is also a substring of anything a
failing assertion prints, and one of this project's own status values is
`Status.ERRORED` — so a control that had driven red exactly as asked, over an
errored result, was reported as unrunnable and **the sweep stopped at entry 51 of
57**. Six controls behind it never ran.

`Unrunnable`'s own docstring says a control that stayed green and a sweep that
could not be made are findings about two different things, and reporting the
second as the first is the fail-open D114 is named for. This was the reverse, and
it cost the same thing: a `[STOP]` that reads like a defect, six unexamined
controls, and a gate whose exit code says nothing about them. Matched on pytest's
own markers now, asserted in both directions.

**The transferable part:** the gate is an instrument, and an instrument's own
failures are not visible in the artifact it produces. This one printed `[STOP]`
beside a control that was working — indistinguishable, without reading the
output, from the `[FAIL]` two entries earlier that was real.

**And a third, caught by where the suite was run rather than by what it asserts.** Moving the
credential check ahead of the estimate — the requirement's own order — made
`test_live_mode_prints_an_estimate_and_issues_nothing_without_confirmation` depend on the machine. It
passed here, where `.env` holds a real key, and would have gone red on CI and on every clone: with no
credential reachable the run is refused before it prints anything, which is the new behavior working.
The test supplies its own fake key now.

That is the hazard `no_credential_in_reach` was written for **in the same commit**, arriving from the
opposite direction: one test needed both routes closed and another needed one open, and each was
relying on the operator's machine to provide it. Found by checking out each commit into a worktree
and running the suite there — which is the only thing in this session that would have found it, since
the checkout it was written in has the key. **The suite passing is a claim about the machine it ran
on until something runs it somewhere else**; CI is that somewhere else on every push, and a worktree
is that somewhere else before the push.

---

## What is owed, in the order I would take it

**These are registered as `OB-12` to `OB-15` in `OBLIGATIONS.md`, which is the live view.** The
headings below are the source the register harvests, and it compares the anchor as well as the
number now, so renaming one breaks a row on purpose.

### 1. The injection criterion's only live evidence rests on a defect

CALL-06 and CALL-07 both come back `misaligned` on every repetition, and both are in
`CONFLATED_NO_CLAUSE_CALLS` — neither retrieved a policy, and the dimension flags every no-clause
call. The direction of the test holds: the verdict did not move toward what the injected turn asked
for. But it is measured on a call the dimension cannot judge, and the verdict it did not move *from*
is itself a recorded defect.

When D125's structural fix lands, whichever branch it takes, neither call produces a verdict and the
test fails on "the reference log does not cover the injection pair" — loudly, which is right, and
with D7's criterion then resting on no live evidence at all. The failure message names the cause now.
The fix is to run the pair through a dimension that applies to both calls.

### 2. The run log's format is decided and not built

D128: `system` and `schema` written once and referenced by content hash. Storage only — replay keys
on the request hash, not on the file layout, and "the exact prompt sent" stays recoverable. Deferred
to P4 deliberately: changing it now invalidates the committed reference log for no gain, and
re-recording is a live run. P4 is going to spend that anyway.

### 3. Whether a judged run of refusals ran

D127 leaves it at exit 0 with the counts printed, because the alternative is a threshold and a
threshold is a gate. *How many refusals are too many* is what P4's roll-up exists to decide, and
answering it in an exit code would be deciding it without the distribution in view.

### 4. The `Not checked` block holds owed work with no obligation id

`OBLIGATIONS.md` harvests handovers and deliberately does not fold in the decision record's
Not-checked block, most of whose fifteen open entries are scope statements rather than debts. But
some are debts by the register's own definition — the re-run of the severity tool's own audit, and
the missing subject-index tool. One classification pass, then a rule that a Not-checked entry naming
work owed must cite an `OB-` id.

---

## What this session did not do

- **No live call, and no spend.** Every finding was reproduced against the committed reference log or
  against a copy of the tree with both credential variables removed from the subprocess environment.
- **The reference log was not re-recorded**, so every verdict in it is the one phase 3 measured. None
  of the closures touches a check's scope or could move one: the loader still admits the shipped
  entry, the retry classification affects only a truncated retry of which the log has none, and the
  injection pair's fix is a P4 decision about which calls are compared.
- **`JUDGED_AGREEMENT_PENDING` stays open**, and `RECORDED_MISS` still pins the miss on CALL-19. The
  audit did not ask for either to move and neither should move here: they are P5's subject.
- **The phase-3 handover was not edited.** It is closed, which in this project means final. Its one
  factual error — CALL-04 recorded as "misaligned 10/10 in both" where the committed pass is 9 and 1
  — is recorded in the audit report's banner, which is where a closed document's errata live.

---

## Conventions this confirmed or added

- **An audit that runs a mutation sweep finds a different population than one that reads.** Both
  populations are real; neither instrument sees the other's. Copy the sweep.
- **Reproduce before acting, and reproduce the positive too.** The single CAUGHT result is what makes
  the six MISSED believable. A sweep with no positive is an instrument with no evidence it is
  connected — which is the same argument `tools/verify_controls.py` makes about controls.
- **A guard with no control is invisible to the control register**, by construction. The register
  audits controls; `OB-2` is the gap and it now has instances rather than a description.
- **When a check and the prose beside it disagree, the check is usually right and the prose is
  usually newer.** All four prose corrections here were sentences written from a plan, not from the
  result.
- **A count printed by a tool should be computed by a function a test can call.** `criteria_in_document`
  exists so the summary and the assertion read one number.
