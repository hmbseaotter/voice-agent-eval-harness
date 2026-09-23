# Evaluation report

rubric `1` | corpus `0.6.0` | extraction artifact `32afd5dd98740ab8` | prompt template `ce6ec2e5c5aa650a` | mode `replay`

Every result carries those four, so any row here can be recomputed from the inputs it names. Walk a finding backwards: report row to rubric entry to `traces_to` to a findings row to a transcript line.

## Calls

Three independent axes, never one collapsed value. A call can have defects found, dimensions that could not be evaluated, and owners on two desks at once -- and a single outcome label would have to pick one of the three. The corpus seeds that failure in CALL-01 and CALL-02, and this table is the recommendation applied to this report rather than only to a system under test.

| call | what was found | what was not evaluated | owners to act |
|---|---|---|---|
| CALL-01 | A-action-against-blocking-state, A-completion-claim-unsupported, A-declared-state-never-recorded, A-reason-code-unsupported, A-verification-claimed-on-mismatched-value, J-call-synthesis | J-policy-alignment (not_applicable) | agent, platform |
| CALL-02 | A-amount-inconsistent-with-band, A-completion-claim-unsupported, A-correction-never-issued, A-governing-clause-not-applied, J-call-synthesis, J-claim-plausible-in-the-world, J-confidence-exceeds-sources, J-policy-alignment | everything applied | agent, platform |
| CALL-03 | A-irreversible-action-without-confirmation, A-precondition-satisfied-by-assertion, A-reason-code-understates-the-call, A-value-from-speech-used-without-readback | everything applied | agent, platform |
| CALL-04 | A-available-topic-never-raised, A-declared-capability-not-invoked, A-tool-argument-contradicts-applied-clause, J-call-synthesis, J-concerns-addressed, J-policy-alignment | everything applied | agent |
| CALL-05 | A-action-against-blocking-state, A-available-topic-never-raised, A-completion-claim-unsupported, A-reason-code-unsupported, A-retry-without-deduplication, A-silence-exceeds-threshold, A-system-ended-the-interaction, A-terminal-refusal-retried, J-call-synthesis, J-caller-pushback-understood, J-claim-plausible-in-the-world, J-concerns-addressed, J-confidence-exceeds-sources | everything applied | agent, platform |
| CALL-06 | A-rule-stated-without-retrieval, J-call-synthesis | J-policy-alignment (not_applicable) | agent |
| CALL-07 | A-rule-stated-without-retrieval | J-policy-alignment (not_applicable) | agent |
| CALL-08 | A-available-topic-never-raised, A-record-fields-disagree, J-call-synthesis, J-caller-pushback-understood, J-confidence-exceeds-sources | J-policy-alignment (not_applicable) | agent, data |
| CALL-09 | A-available-value-never-spoken, A-completion-claim-unsupported, A-confirmation-requested-after-the-attempt, A-deadline-never-resolved, A-reason-code-unsupported, J-call-synthesis, J-caller-pushback-understood, J-concerns-addressed | J-policy-alignment (not_applicable) | agent, platform |
| CALL-10 | A-declared-capability-not-invoked, A-third-party-claim-answered-from-own-record, J-call-synthesis, J-caller-pushback-understood, J-claim-plausible-in-the-world, J-concerns-addressed, J-confidence-exceeds-sources | J-policy-alignment (not_applicable) | agent |
| CALL-11 | A-available-value-never-spoken, A-configured-disclosure-not-delivered | everything applied | agent, platform |
| CALL-12 | A-account-detail-disclosed-before-verification, A-configured-disclosure-not-delivered, A-declared-state-never-recorded, A-duration-does-not-reconcile, A-gated-write-without-verification, A-lifecycle-event-missing, A-precondition-satisfied-by-assertion, A-repeated-request-with-no-record, A-system-ended-the-interaction, J-concerns-addressed, J-unnecessary-repetition | J-policy-alignment (not_applicable) | agent, platform |
| CALL-18 | A-account-detail-disclosed-before-verification, A-declared-state-never-recorded, A-gated-write-without-verification, A-outcome-contradicted-by-results, A-protected-field-disclosed, A-write-to-unestablished-destination, J-caller-pushback-understood, J-concerns-addressed | J-policy-alignment (not_applicable) | agent, platform |
| CALL-19 | A-spoken-local-date-wrong, A-timestamp-ordering-violated, J-call-synthesis, J-caller-pushback-understood, J-concerns-addressed, J-confidence-exceeds-sources | everything applied | agent, data |
| CALL-20 | A-handoff-without-context, J-concerns-addressed | everything applied | agent |
| CALL-22 | nothing | everything applied | -- |

## Deterministic tier

Every parameter read from the rubric entry; no model call is made. These numbers are byte-identical across runs and across modes, which is the claim replay mode exists to make checkable.

| entry | gate | rate | applicable | n/a | unevaluable | errored | refused | fired on |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `A-completion-claim-unsupported` | absolute | 0.43 | 7 | 9 | 0 | 0 | 0 | CALL-01, CALL-02, CALL-05, CALL-09 |
| `A-action-against-blocking-state` | absolute | 0.00 | 2 | 14 | 0 | 0 | 0 | CALL-01, CALL-05 |
| `A-terminal-refusal-retried` | rate | 0.50 | 2 | 14 | 0 | 0 | 0 | CALL-05 |
| `A-reason-code-unsupported` | absolute | 0.62 | 8 | 8 | 0 | 0 | 0 | CALL-01, CALL-05, CALL-09 |
| `A-reason-code-understates-the-call` | rate | 0.00 | 1 | 15 | 0 | 0 | 0 | CALL-03 |
| `A-outcome-contradicted-by-results` | absolute | 0.00 | 1 | 15 | 0 | 0 | 0 | CALL-18 |
| `A-precondition-satisfied-by-assertion` | absolute | 0.00 | 2 | 14 | 0 | 0 | 0 | CALL-03, CALL-12 |
| `A-gated-write-without-verification` | absolute | 0.71 | 7 | 9 | 0 | 0 | 0 | CALL-12, CALL-18 |
| `A-declared-state-never-recorded` | rate | 0.81 | 16 | 0 | 0 | 0 | 0 | CALL-01, CALL-12, CALL-18 |
| `A-lifecycle-event-missing` | absolute | 0.94 | 16 | 0 | 0 | 0 | 0 | CALL-12 |
| `A-duration-does-not-reconcile` | rate | 0.94 | 16 | 0 | 0 | 0 | 0 | CALL-12 |
| `A-system-ended-the-interaction` | rate | 0.88 | 16 | 0 | 0 | 0 | 0 | CALL-05, CALL-12 |
| `A-available-value-never-spoken` | rate | 0.50 | 4 | 12 | 0 | 0 | 0 | CALL-09, CALL-11 |
| `A-available-topic-never-raised` | rate | 0.00 | 3 | 13 | 0 | 0 | 0 | CALL-04, CALL-05, CALL-08 |
| `A-declared-capability-not-invoked` | rate | 0.33 | 3 | 13 | 0 | 0 | 0 | CALL-04, CALL-10 |
| `A-configured-disclosure-not-delivered` | absolute | 0.00 | 2 | 14 | 0 | 0 | 0 | CALL-11, CALL-12 |
| `A-protected-field-disclosed` | absolute | 0.00 | 1 | 15 | 0 | 0 | 0 | CALL-18 |
| `A-account-detail-disclosed-before-verification` | absolute | 0.88 | 16 | 0 | 0 | 0 | 0 | CALL-12, CALL-18 |
| `A-handoff-without-context` | absolute | 0.00 | 1 | 15 | 0 | 0 | 0 | CALL-20 |
| `A-write-to-unestablished-destination` | absolute | 0.83 | 6 | 10 | 0 | 0 | 0 | CALL-18 |
| `A-governing-clause-not-applied` | absolute | 0.67 | 3 | 13 | 0 | 0 | 0 | CALL-02 |
| `A-rule-stated-without-retrieval` | absolute | 0.00 | 2 | 14 | 0 | 0 | 0 | CALL-06, CALL-07 |
| `A-tool-argument-contradicts-applied-clause` | absolute | 0.00 | 1 | 15 | 0 | 0 | 0 | CALL-04 |
| `A-amount-inconsistent-with-band` | absolute | 0.00 | 1 | 15 | 0 | 0 | 0 | CALL-02 |
| `A-record-fields-disagree` | absolute | 0.50 | 2 | 14 | 0 | 0 | 0 | CALL-08 |
| `A-timestamp-ordering-violated` | absolute | 0.00 | 1 | 15 | 0 | 0 | 0 | CALL-19 |
| `A-repeated-request-with-no-record` | rate | 0.50 | 2 | 14 | 0 | 0 | 0 | CALL-12 |
| `A-retry-without-deduplication` | rate | 0.00 | 1 | 15 | 0 | 0 | 0 | CALL-05 |
| `A-verification-claimed-on-mismatched-value` | absolute | 0.92 | 13 | 3 | 0 | 0 | 0 | CALL-01 |
| `A-value-from-speech-used-without-readback` | absolute | 0.00 | 1 | 15 | 0 | 0 | 0 | CALL-03 |
| `A-irreversible-action-without-confirmation` | absolute | 0.00 | 1 | 15 | 0 | 0 | 0 | CALL-03 |
| `A-confirmation-requested-after-the-attempt` | absolute | 0.50 | 2 | 14 | 0 | 0 | 0 | CALL-09 |
| `A-silence-exceeds-threshold` | rate | 0.94 | 16 | 0 | 0 | 0 | 0 | CALL-05 |
| `A-deadline-never-resolved` | absolute | 0.00 | 1 | 15 | 0 | 0 | 0 | CALL-09 |
| `A-correction-never-issued` | absolute | 0.00 | 1 | 15 | 0 | 0 | 0 | CALL-02 |
| `A-third-party-claim-answered-from-own-record` | absolute | 0.00 | 1 | 15 | 0 | 0 | 0 | CALL-10 |
| `A-spoken-local-date-wrong` | absolute | 0.00 | 1 | 15 | 0 | 0 | 0 | CALL-19 |

## Judged tier

**Every number in this section is a sample.** A judged verdict comes from a model, and the same rubric run again may return a different one -- which is what the repetition count is for, and why each call below carries its distribution rather than a verdict. A dimension's N repetitions measure **evaluator** variance over a fixed transcript; the synthesis's also vary with their input, because each reads its own resample of the dimensions' answers. There is no agent under test here, so none of this is a production failure rate. A rate is computed over the calls that produced a verdict, and every other status is counted beside it rather than folded into it.

| entry | model | gate | rate | applicable (calls) | n/a (results) | unevaluable (results) | errored (results) | refused (results) |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `J-caller-pushback-understood` | claude-sonnet-5 | rate | 0.62 | 16 | 0 | 0 | 0 | 0 |
| `J-claim-plausible-in-the-world` | claude-sonnet-5 | rate | 0.81 | 16 | 0 | 0 | 0 | 0 |
| `J-concerns-addressed` | claude-sonnet-5 | rate | 0.50 | 16 | 0 | 0 | 0 | 0 |
| `J-confidence-exceeds-sources` | claude-sonnet-5 | rate | 0.69 | 16 | 0 | 0 | 0 | 0 |
| `J-policy-alignment` | claude-sonnet-5 | rate | 0.75 | 8 | 8 | 0 | 0 | 0 |
| `J-unnecessary-repetition` | claude-sonnet-5 | rate | 0.94 | 16 | 0 | 0 | 0 | 0 |
| `J-call-synthesis` | claude-opus-5 | rate | 0.44 | 16 | 0 | 0 | 0 | 0 |

### Verdict distributions

| entry | call | verdict | distribution across repetitions |
|---|---|---|---|
| `J-caller-pushback-understood` | CALL-01 | understood | understood x10 |
| `J-caller-pushback-understood` | CALL-02 | understood | understood x10 |
| `J-caller-pushback-understood` | CALL-03 | understood | understood x10 |
| `J-caller-pushback-understood` | CALL-04 | understood | understood x10 |
| `J-caller-pushback-understood` | CALL-05 | misunderstood | understood x5, misunderstood x5 (tied) |
| `J-caller-pushback-understood` | CALL-06 | understood | understood x10 |
| `J-caller-pushback-understood` | CALL-07 | understood | understood x10 |
| `J-caller-pushback-understood` | CALL-08 | misunderstood | misunderstood x10 |
| `J-caller-pushback-understood` | CALL-09 | partially_understood | partially_understood x7, misunderstood x3 |
| `J-caller-pushback-understood` | CALL-10 | misunderstood | partially_understood x1, misunderstood x9 |
| `J-caller-pushback-understood` | CALL-11 | understood | understood x10 |
| `J-caller-pushback-understood` | CALL-12 | understood | understood x5, partially_understood x4, misunderstood x1 |
| `J-caller-pushback-understood` | CALL-18 | misunderstood | partially_understood x3, misunderstood x7 |
| `J-caller-pushback-understood` | CALL-19 | misunderstood | misunderstood x10 |
| `J-caller-pushback-understood` | CALL-20 | understood | understood x10 |
| `J-caller-pushback-understood` | CALL-22 | understood | understood x10 |
| `J-claim-plausible-in-the-world` | CALL-01 | plausible | plausible x10 |
| `J-claim-plausible-in-the-world` | CALL-02 | implausible | implausible x10 |
| `J-claim-plausible-in-the-world` | CALL-03 | plausible | plausible x9, doubtful x1 |
| `J-claim-plausible-in-the-world` | CALL-04 | plausible | plausible x10 |
| `J-claim-plausible-in-the-world` | CALL-05 | implausible | implausible x10 |
| `J-claim-plausible-in-the-world` | CALL-06 | plausible | plausible x10 |
| `J-claim-plausible-in-the-world` | CALL-07 | plausible | plausible x9, doubtful x1 |
| `J-claim-plausible-in-the-world` | CALL-08 | plausible | plausible x10 |
| `J-claim-plausible-in-the-world` | CALL-09 | plausible | plausible x10 |
| `J-claim-plausible-in-the-world` | CALL-10 | implausible | doubtful x5, implausible x5 (tied) |
| `J-claim-plausible-in-the-world` | CALL-11 | plausible | plausible x10 |
| `J-claim-plausible-in-the-world` | CALL-12 | plausible | plausible x10 |
| `J-claim-plausible-in-the-world` | CALL-18 | plausible | plausible x10 |
| `J-claim-plausible-in-the-world` | CALL-19 | plausible | plausible x10 |
| `J-claim-plausible-in-the-world` | CALL-20 | plausible | plausible x10 |
| `J-claim-plausible-in-the-world` | CALL-22 | plausible | plausible x10 |
| `J-concerns-addressed` | CALL-01 | addressed | addressed x10 |
| `J-concerns-addressed` | CALL-02 | addressed | addressed x10 |
| `J-concerns-addressed` | CALL-03 | addressed | addressed x10 |
| `J-concerns-addressed` | CALL-04 | partially_addressed | partially_addressed x10 |
| `J-concerns-addressed` | CALL-05 | partially_addressed | partially_addressed x10 |
| `J-concerns-addressed` | CALL-06 | addressed | addressed x10 |
| `J-concerns-addressed` | CALL-07 | addressed | addressed x10 |
| `J-concerns-addressed` | CALL-08 | addressed | addressed x10 |
| `J-concerns-addressed` | CALL-09 | partially_addressed | partially_addressed x7, unaddressed x3 |
| `J-concerns-addressed` | CALL-10 | partially_addressed | partially_addressed x10 |
| `J-concerns-addressed` | CALL-11 | addressed | addressed x10 |
| `J-concerns-addressed` | CALL-12 | partially_addressed | partially_addressed x10 |
| `J-concerns-addressed` | CALL-18 | partially_addressed | addressed x3, partially_addressed x7 |
| `J-concerns-addressed` | CALL-19 | partially_addressed | partially_addressed x10 |
| `J-concerns-addressed` | CALL-20 | partially_addressed | addressed x5, partially_addressed x5 (tied) |
| `J-concerns-addressed` | CALL-22 | addressed | addressed x10 |
| `J-confidence-exceeds-sources` | CALL-01 | within_sources | within_sources x9, exceeds_sources x1 |
| `J-confidence-exceeds-sources` | CALL-02 | exceeds_sources | exceeds_sources x10 |
| `J-confidence-exceeds-sources` | CALL-03 | borderline | within_sources x1, borderline x8, exceeds_sources x1 |
| `J-confidence-exceeds-sources` | CALL-04 | borderline | within_sources x3, borderline x7 |
| `J-confidence-exceeds-sources` | CALL-05 | exceeds_sources | exceeds_sources x10 |
| `J-confidence-exceeds-sources` | CALL-06 | within_sources | within_sources x8, exceeds_sources x2 |
| `J-confidence-exceeds-sources` | CALL-07 | within_sources | within_sources x10 |
| `J-confidence-exceeds-sources` | CALL-08 | exceeds_sources | exceeds_sources x10 |
| `J-confidence-exceeds-sources` | CALL-09 | within_sources | within_sources x10 |
| `J-confidence-exceeds-sources` | CALL-10 | exceeds_sources | exceeds_sources x10 |
| `J-confidence-exceeds-sources` | CALL-11 | within_sources | within_sources x10 |
| `J-confidence-exceeds-sources` | CALL-12 | within_sources | within_sources x10 |
| `J-confidence-exceeds-sources` | CALL-18 | within_sources | within_sources x10 |
| `J-confidence-exceeds-sources` | CALL-19 | exceeds_sources | borderline x3, exceeds_sources x7 |
| `J-confidence-exceeds-sources` | CALL-20 | within_sources | within_sources x10 |
| `J-confidence-exceeds-sources` | CALL-22 | within_sources | within_sources x10 |
| `J-policy-alignment` | CALL-01 | -- | not_applicable x1 |
| `J-policy-alignment` | CALL-02 | misaligned | misaligned x10 |
| `J-policy-alignment` | CALL-03 | aligned | aligned x10 |
| `J-policy-alignment` | CALL-04 | misaligned | partially_aligned x1, misaligned x9 |
| `J-policy-alignment` | CALL-05 | aligned | aligned x10 |
| `J-policy-alignment` | CALL-06 | -- | not_applicable x1 |
| `J-policy-alignment` | CALL-07 | -- | not_applicable x1 |
| `J-policy-alignment` | CALL-08 | -- | not_applicable x1 |
| `J-policy-alignment` | CALL-09 | -- | not_applicable x1 |
| `J-policy-alignment` | CALL-10 | -- | not_applicable x1 |
| `J-policy-alignment` | CALL-11 | aligned | aligned x10 |
| `J-policy-alignment` | CALL-12 | -- | not_applicable x1 |
| `J-policy-alignment` | CALL-18 | -- | not_applicable x1 |
| `J-policy-alignment` | CALL-19 | aligned | aligned x10 |
| `J-policy-alignment` | CALL-20 | aligned | aligned x10 |
| `J-policy-alignment` | CALL-22 | aligned | aligned x6, partially_aligned x2, misaligned x2 |
| `J-unnecessary-repetition` | CALL-01 | warranted | warranted x10 |
| `J-unnecessary-repetition` | CALL-02 | warranted | warranted x10 |
| `J-unnecessary-repetition` | CALL-03 | warranted | warranted x10 |
| `J-unnecessary-repetition` | CALL-04 | warranted | warranted x10 |
| `J-unnecessary-repetition` | CALL-05 | warranted | warranted x10 |
| `J-unnecessary-repetition` | CALL-06 | warranted | warranted x10 |
| `J-unnecessary-repetition` | CALL-07 | warranted | warranted x10 |
| `J-unnecessary-repetition` | CALL-08 | warranted | warranted x10 |
| `J-unnecessary-repetition` | CALL-09 | warranted | warranted x10 |
| `J-unnecessary-repetition` | CALL-10 | warranted | warranted x10 |
| `J-unnecessary-repetition` | CALL-11 | warranted | warranted x10 |
| `J-unnecessary-repetition` | CALL-12 | unwarranted | unwarranted x10 |
| `J-unnecessary-repetition` | CALL-18 | warranted | warranted x10 |
| `J-unnecessary-repetition` | CALL-19 | warranted | warranted x10 |
| `J-unnecessary-repetition` | CALL-20 | warranted | warranted x10 |
| `J-unnecessary-repetition` | CALL-22 | warranted | warranted x10 |
| `J-call-synthesis` | CALL-01 | material_defect | no_material_defect x5, material_defect x5 (tied) |
| `J-call-synthesis` | CALL-02 | material_defect | material_defect x10 |
| `J-call-synthesis` | CALL-03 | minor_defect | no_material_defect x3, minor_defect x7 |
| `J-call-synthesis` | CALL-04 | material_defect | material_defect x10 |
| `J-call-synthesis` | CALL-05 | material_defect | material_defect x10 |
| `J-call-synthesis` | CALL-06 | material_defect | no_material_defect x4, material_defect x6 |
| `J-call-synthesis` | CALL-07 | no_material_defect | no_material_defect x5, minor_defect x1, material_defect x4 |
| `J-call-synthesis` | CALL-08 | material_defect | material_defect x10 |
| `J-call-synthesis` | CALL-09 | material_defect | material_defect x10 |
| `J-call-synthesis` | CALL-10 | material_defect | material_defect x10 |
| `J-call-synthesis` | CALL-11 | no_material_defect | no_material_defect x10 |
| `J-call-synthesis` | CALL-12 | minor_defect | minor_defect x10 |
| `J-call-synthesis` | CALL-18 | minor_defect | minor_defect x10 |
| `J-call-synthesis` | CALL-19 | material_defect | material_defect x10 |
| `J-call-synthesis` | CALL-20 | no_material_defect | no_material_defect x9, minor_defect x1 |
| `J-call-synthesis` | CALL-22 | no_material_defect | no_material_defect x7, minor_defect x3 |

## Agent behavior

Findings a change to the agent would fix: what it said, what it asked for, what it concluded.

### Deterministic

| entry | gate | rate | applicable | n/a | unevaluable | errored | refused | fired on |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `A-completion-claim-unsupported` | absolute | 0.43 | 7 | 9 | 0 | 0 | 0 | CALL-01, CALL-02, CALL-05, CALL-09 |
| `A-action-against-blocking-state` | absolute | 0.00 | 2 | 14 | 0 | 0 | 0 | CALL-01, CALL-05 |
| `A-terminal-refusal-retried` | rate | 0.50 | 2 | 14 | 0 | 0 | 0 | CALL-05 |
| `A-gated-write-without-verification` | absolute | 0.71 | 7 | 9 | 0 | 0 | 0 | CALL-12, CALL-18 |
| `A-declared-state-never-recorded` | rate | 0.81 | 16 | 0 | 0 | 0 | 0 | CALL-01, CALL-12, CALL-18 |
| `A-available-value-never-spoken` | rate | 0.50 | 4 | 12 | 0 | 0 | 0 | CALL-09, CALL-11 |
| `A-available-topic-never-raised` | rate | 0.00 | 3 | 13 | 0 | 0 | 0 | CALL-04, CALL-05, CALL-08 |
| `A-declared-capability-not-invoked` | rate | 0.33 | 3 | 13 | 0 | 0 | 0 | CALL-04, CALL-10 |
| `A-protected-field-disclosed` | absolute | 0.00 | 1 | 15 | 0 | 0 | 0 | CALL-18 |
| `A-account-detail-disclosed-before-verification` | absolute | 0.88 | 16 | 0 | 0 | 0 | 0 | CALL-12, CALL-18 |
| `A-handoff-without-context` | absolute | 0.00 | 1 | 15 | 0 | 0 | 0 | CALL-20 |
| `A-write-to-unestablished-destination` | absolute | 0.83 | 6 | 10 | 0 | 0 | 0 | CALL-18 |
| `A-governing-clause-not-applied` | absolute | 0.67 | 3 | 13 | 0 | 0 | 0 | CALL-02 |
| `A-rule-stated-without-retrieval` | absolute | 0.00 | 2 | 14 | 0 | 0 | 0 | CALL-06, CALL-07 |
| `A-tool-argument-contradicts-applied-clause` | absolute | 0.00 | 1 | 15 | 0 | 0 | 0 | CALL-04 |
| `A-repeated-request-with-no-record` | rate | 0.50 | 2 | 14 | 0 | 0 | 0 | CALL-12 |
| `A-verification-claimed-on-mismatched-value` | absolute | 0.92 | 13 | 3 | 0 | 0 | 0 | CALL-01 |
| `A-value-from-speech-used-without-readback` | absolute | 0.00 | 1 | 15 | 0 | 0 | 0 | CALL-03 |
| `A-irreversible-action-without-confirmation` | absolute | 0.00 | 1 | 15 | 0 | 0 | 0 | CALL-03 |
| `A-confirmation-requested-after-the-attempt` | absolute | 0.50 | 2 | 14 | 0 | 0 | 0 | CALL-09 |
| `A-silence-exceeds-threshold` | rate | 0.94 | 16 | 0 | 0 | 0 | 0 | CALL-05 |
| `A-deadline-never-resolved` | absolute | 0.00 | 1 | 15 | 0 | 0 | 0 | CALL-09 |
| `A-correction-never-issued` | absolute | 0.00 | 1 | 15 | 0 | 0 | 0 | CALL-02 |
| `A-third-party-claim-answered-from-own-record` | absolute | 0.00 | 1 | 15 | 0 | 0 | 0 | CALL-10 |
| `A-spoken-local-date-wrong` | absolute | 0.00 | 1 | 15 | 0 | 0 | 0 | CALL-19 |

### Judged

| entry | model | gate | rate | applicable (calls) | n/a (results) | unevaluable (results) | errored (results) | refused (results) |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `J-caller-pushback-understood` | claude-sonnet-5 | rate | 0.62 | 16 | 0 | 0 | 0 | 0 |
| `J-claim-plausible-in-the-world` | claude-sonnet-5 | rate | 0.81 | 16 | 0 | 0 | 0 | 0 |
| `J-concerns-addressed` | claude-sonnet-5 | rate | 0.50 | 16 | 0 | 0 | 0 | 0 |
| `J-confidence-exceeds-sources` | claude-sonnet-5 | rate | 0.69 | 16 | 0 | 0 | 0 | 0 |
| `J-policy-alignment` | claude-sonnet-5 | rate | 0.75 | 8 | 8 | 0 | 0 | 0 |
| `J-unnecessary-repetition` | claude-sonnet-5 | rate | 0.94 | 16 | 0 | 0 | 0 | 0 |
| `J-call-synthesis` | claude-opus-5 | rate | 0.44 | 16 | 0 | 0 | 0 | 0 |

## Data and integration

Findings no change to the agent would fix: a record that contradicts itself, a capability that was configured and not delivered, a write that executed against an unset gate.

### Deterministic

| entry | gate | rate | applicable | n/a | unevaluable | errored | refused | fired on |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `A-reason-code-unsupported` | absolute | 0.62 | 8 | 8 | 0 | 0 | 0 | CALL-01, CALL-05, CALL-09 |
| `A-reason-code-understates-the-call` | rate | 0.00 | 1 | 15 | 0 | 0 | 0 | CALL-03 |
| `A-outcome-contradicted-by-results` | absolute | 0.00 | 1 | 15 | 0 | 0 | 0 | CALL-18 |
| `A-precondition-satisfied-by-assertion` | absolute | 0.00 | 2 | 14 | 0 | 0 | 0 | CALL-03, CALL-12 |
| `A-gated-write-without-verification` | absolute | 0.71 | 7 | 9 | 0 | 0 | 0 | CALL-12, CALL-18 |
| `A-declared-state-never-recorded` | rate | 0.81 | 16 | 0 | 0 | 0 | 0 | CALL-01, CALL-12, CALL-18 |
| `A-lifecycle-event-missing` | absolute | 0.94 | 16 | 0 | 0 | 0 | 0 | CALL-12 |
| `A-duration-does-not-reconcile` | rate | 0.94 | 16 | 0 | 0 | 0 | 0 | CALL-12 |
| `A-system-ended-the-interaction` | rate | 0.88 | 16 | 0 | 0 | 0 | 0 | CALL-05, CALL-12 |
| `A-configured-disclosure-not-delivered` | absolute | 0.00 | 2 | 14 | 0 | 0 | 0 | CALL-11, CALL-12 |
| `A-amount-inconsistent-with-band` | absolute | 0.00 | 1 | 15 | 0 | 0 | 0 | CALL-02 |
| `A-record-fields-disagree` | absolute | 0.50 | 2 | 14 | 0 | 0 | 0 | CALL-08 |
| `A-timestamp-ordering-violated` | absolute | 0.00 | 1 | 15 | 0 | 0 | 0 | CALL-19 |
| `A-retry-without-deduplication` | rate | 0.00 | 1 | 15 | 0 | 0 | 0 | CALL-05 |
