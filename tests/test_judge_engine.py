"""The judged engine: N repetitions, one informed retry, and five statuses kept apart.

Every test here uses a scripted transport. That is the point rather than a
limitation: the properties under test are *classifications* -- which status a
given response produces, and how many calls it costs -- and a real model would
make them non-deterministic in exactly the dimension being asserted.

The three distinctions this file exists for are the ones a harness whose thesis
is "evaluation must distinguish failure modes" cannot get wrong:

* a model that **declined** (`refused`), consuming no retry;
* a response **truncated** at `max_tokens` (`errored`, carrying the reason);
* a complete response that **failed validation** (`errored`, after one retry).

All three look identical to a caller that only reads "no verdict".
"""

from __future__ import annotations

import dataclasses
import json
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Final

import pytest

from harness.checks import build_registry
from harness.core.context import CheckContext, build_context
from harness.core.registry import ResultBuilder
from harness.core.result import Provenance, Status
from harness.core.rubric import CheckTier, JudgeSpec, Rubric, RubricEntry, load_rubric
from harness.core.transport import (
    STOP_END_TURN,
    STOP_MAX_TOKENS,
    STOP_REFUSAL,
    CallCeilingReachedError,
    CeilingTransport,
    JudgeRequest,
    JudgeResponse,
    RecordingTransport,
    RunLogHeader,
    RunLogWriter,
    TransientTransportError,
    read_run_log,
)
from harness.corpus.policies import load_policies
from harness.corpus.text_adapter import parse_call
from harness.judge.engine import (
    INFORMED_RETRY_BUDGET,
    JudgedCallAborted,
    JudgedOutcome,
    build_request,
    dimension_line,
    evaluate_call,
    judged_order,
    run_judged,
    synthesis_input,
)
from harness.judge.prompt import (
    PromptTemplate,
    UnknownFactCategoryError,
    load_template,
    render_prompt,
    response_schema,
)
from harness.judge.rollup import roll_up_judged

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
TEMPLATE_PATH: Final[Path] = REPO_ROOT / "prompts" / "judge-dimension.v1.md"
TRANSCRIPTS: Final[Path] = REPO_ROOT / "corpus" / "transcripts"
POLICIES: Final[Path] = REPO_ROOT / "corpus" / "policies"
POLICY_TOOL: Final[str] = "fetch_policy"
ENTRY_ID: Final[str] = "J-policy-alignment"
SYNTHESIS_ID: Final[str] = "J-call-synthesis"

PROVENANCE: Final[Provenance] = Provenance(
    rubric_version="1", corpus_version="test", artifact_hash="0" * 64
)


def _context(call_id: str = "CALL-02") -> CheckContext:
    policies = load_policies(POLICIES)
    return build_context(
        parse_call(TRANSCRIPTS / f"{call_id}.txt"), policies, policy_tool=POLICY_TOOL
    )


def _contexts() -> tuple[CheckContext, ...]:
    """Every design-set call, built once per call site.

    Not cached: these tests mutate nothing, and a module-level cache would make
    the order they run in matter.
    """
    policies = load_policies(POLICIES)
    return tuple(
        build_context(parse_call(path), policies, policy_tool=POLICY_TOOL)
        for path in sorted(TRANSCRIPTS.glob("*.txt"))
    )


def _template() -> PromptTemplate:
    return load_template(TEMPLATE_PATH)


def _rubric() -> Rubric:
    return load_rubric(REPO_ROOT / "rubric.yaml", build_registry().keys())


def _entry(repetitions: int = 1) -> RubricEntry:
    """The shipped judged entry, optionally with N narrowed for a test.

    Narrowing N is done by rebuilding the entry rather than by editing the
    rubric, so every other field is the shipped one. A fixture entry here would
    make these tests assertions about a fixture.
    """
    import dataclasses

    entry = _rubric().by_id(ENTRY_ID)
    assert entry.judge is not None
    return dataclasses.replace(
        entry, judge=dataclasses.replace(entry.judge, repetitions=repetitions)
    )


def _answer(verdict: str = "aligned", citations: tuple[str, ...] = ("T1",)) -> str:
    return json.dumps({"verdict": verdict, "rationale": "because", "citations": list(citations)})


def _response(**overrides: Any) -> JudgeResponse:
    base: dict[str, Any] = {
        "text": _answer(),
        "stop_reason": STOP_END_TURN,
        "stop_category": None,
        "stop_explanation": None,
        "input_tokens": 100,
        "output_tokens": 20,
        "model": "claude-sonnet-5",
        "latency_ms": 5,
    }
    base.update(overrides)
    return JudgeResponse(**base)


def _answer_for(request: JudgeRequest) -> str:
    """A well-formed answer to whatever this request asked, read off its schema.

    The declared schema carries the entry's scale as an enum and says whether
    `rests_on` is required, so a fixture built from it cannot drift from the
    rubric the way a hand-written literal does.
    """
    properties = request.schema["properties"]
    assert isinstance(properties, dict)
    verdict = properties["verdict"]["enum"][0]
    payload: dict[str, Any] = {
        "verdict": verdict,
        "rationale": "because",
        "citations": ["T1"],
    }
    if "rests_on" in properties:
        # Every entry the prompt listed. A synthesis fixture naming one that
        # was not listed would be exercising the defect path by accident.
        listed = re.findall(r"^([A-Z]-[a-z-]+): ", request.prompt, re.MULTILINE)
        payload["rests_on"] = listed or ["J-policy-alignment"]
    return json.dumps(payload)


class _Scripted:
    """Answers from a script, and records every request it was given.

    **An unscripted answer is shaped by the entry that was asked**, rather than
    being one canned verdict for every request. A judged run now spans seven
    entries with five different scales, and a fixture returning `aligned` to all
    of them was refused by `validate_result` on six -- correctly, and for a
    reason about the fixture rather than about the engine under test.

    The verdict is the asked entry's own first scale member, and the synthesis
    additionally rests on the entries the prompt listed. Both are read off the
    request, so a scale renamed in the rubric moves this fixture with it.
    """

    def __init__(self, *responses: JudgeResponse) -> None:
        self.seen: list[JudgeRequest] = []
        self._script = list(responses)

    def send(self, request: JudgeRequest) -> JudgeResponse:
        self.seen.append(request)
        if self._script:
            return self._script.pop(0)
        return _response(text=_answer_for(request))

    @property
    def calls(self) -> int:
        return len(self.seen)


class _Flaky:
    """Fails transiently `failures` times, then answers."""

    def __init__(self, failures: int) -> None:
        self.attempts = 0
        self._failures = failures

    def send(self, request: JudgeRequest) -> JudgeResponse:
        del request
        self.attempts += 1
        if self.attempts <= self._failures:
            raise TransientTransportError("the transport failed transiently")
        return _response()


def _valid_citation(call_id: str = "CALL-02") -> str:
    """A citation this prompt genuinely offers, taken from the render itself.

    Read from the universe rather than assumed to be `T1`, so a change to what
    the renderer offers moves this fixture rather than silently making these
    tests assert against something the prompt no longer shows.
    """
    entry = _entry()
    assert entry.judge is not None
    rendered = render_prompt(
        _template(),
        _context(call_id),
        entry_id=entry.id,
        question=entry.judge.question,
        criteria=entry.judge.criteria,
        scale=entry.scale,
        scale_definitions=entry.judge.scale_definitions,
        requires_facts=entry.judge.requires_facts,
    )
    return next(iter(rendered.citable.facts))


# --------------------------------------------------------------------------
# The happy path, and what a verdict carries
# --------------------------------------------------------------------------


def test_a_valid_answer_produces_an_applicable_result_carrying_the_verdict() -> None:
    fact = _valid_citation()
    transport = _Scripted(_response(text=_answer("aligned", (fact,))))
    outcomes = evaluate_call(
        _entry(), _context(), PROVENANCE, template=_template(), transport=transport
    )
    assert len(outcomes) == 1
    result = outcomes[0].result
    assert result.status is Status.APPLICABLE
    assert result.verdict == "aligned"
    assert outcomes[0].informed_retries == 0
    assert transport.calls == 1


def test_a_fact_citation_validates_and_lands_in_the_evidence_quoted() -> None:
    """The criterion: a judged response citing a fact line `[F3]` validates.

    The evidence quotes the rendered line rather than naming the identifier: a
    bare `F3` sends the reader back to re-render the prompt to find out what
    they are looking at.
    """
    fact = _valid_citation()
    transport = _Scripted(_response(text=_answer("aligned", (fact,))))
    outcomes = evaluate_call(
        _entry(), _context(), PROVENANCE, template=_template(), transport=transport
    )
    evidence = outcomes[0].result.evidence
    assert any(line.startswith(f"[{fact}]") for line in evidence), evidence
    assert any(line.startswith("judge rationale:") for line in evidence)


def test_a_negative_verdict_carries_evidence_or_the_entry_refuses_it() -> None:
    """The Result contract's evidence-on-negative-pole rule, reaching a judged
    scale for the first time. The schema requires at least one citation, and
    this is what happens when that holds: a `misaligned` verdict arrives with
    the line it rests on."""
    fact = _valid_citation()
    transport = _Scripted(_response(text=_answer("misaligned", (fact,))))
    outcomes = evaluate_call(
        _entry(), _context(), PROVENANCE, template=_template(), transport=transport
    )
    assert outcomes[0].result.verdict == "misaligned"
    assert outcomes[0].result.evidence


# --------------------------------------------------------------------------
# N repetitions
# --------------------------------------------------------------------------


def test_n_repetitions_issue_n_calls_and_write_n_run_log_entries(tmp_path: Path) -> None:
    """The criterion: a judged dimension run at N>1 writes N run-log entries."""
    fact = _valid_citation()
    path = tmp_path / "run.jsonl"
    header = RunLogHeader(
        rubric_version="1",
        prompt_template_hash=_template().sha256,
        corpus_version="test",
        artifact_hash="0" * 64,
        mode="replay",
        started_at="2026-09-09T12:00:00Z",
    )
    scripted = _Scripted(*[_response(text=_answer("aligned", (fact,))) for _ in range(4)])
    transport = RecordingTransport(scripted, RunLogWriter(path, header))
    outcomes = evaluate_call(
        _entry(repetitions=4), _context(), PROVENANCE, template=_template(), transport=transport
    )
    assert [o.repetition for o in outcomes] == [1, 2, 3, 4]
    assert scripted.calls == 4
    _, entries = read_run_log(path)
    assert len(entries) == 4


def test_the_repetitions_send_byte_identical_requests() -> None:
    """What makes N a measurement of the model's variance rather than of the
    prompt's (D17). The prompt is rendered once and reused."""
    transport = _Scripted()
    evaluate_call(
        _entry(repetitions=3), _context(), PROVENANCE, template=_template(), transport=transport
    )
    prompts = {request.prompt for request in transport.seen}
    systems = {request.system for request in transport.seen}
    assert len(prompts) == 1 and len(systems) == 1
    assert len({request.request_hash for request in transport.seen}) == 1


def test_each_repetition_keeps_its_own_verdict() -> None:
    """The distribution P4 will report is only there to be reported if the
    repetitions are kept apart here."""
    fact = _valid_citation()
    transport = _Scripted(
        _response(text=_answer("aligned", (fact,))),
        _response(text=_answer("misaligned", (fact,))),
        _response(text=_answer("aligned", (fact,))),
    )
    outcomes = evaluate_call(
        _entry(repetitions=3), _context(), PROVENANCE, template=_template(), transport=transport
    )
    assert [o.result.verdict for o in outcomes] == ["aligned", "misaligned", "aligned"]


# --------------------------------------------------------------------------
# The informed retry, and exhaustion
# --------------------------------------------------------------------------


def test_a_fabricated_citation_triggers_exactly_one_informed_retry() -> None:
    """The criterion: a response citing a non-existent `[T999]` triggers exactly
    one informed retry. Exactly one, asserted on the call count."""
    fact = _valid_citation()
    transport = _Scripted(
        _response(text=_answer("aligned", ("T999",))),
        _response(text=_answer("aligned", (fact,))),
    )
    outcomes = evaluate_call(
        _entry(), _context(), PROVENANCE, template=_template(), transport=transport
    )
    assert transport.calls == 2, "the retry budget is one, and this spent something else"
    assert outcomes[0].informed_retries == 1
    assert outcomes[0].result.status is Status.APPLICABLE


def test_a_retry_truncated_at_max_tokens_is_reported_as_truncation() -> None:
    """The retry gets the same classification order the first attempt gets.

    It did not, and the asymmetry hid behind a shared destination: both legs
    reach `errored`, so the status was right and the *reason* was wrong. A retry
    cut off at the token ceiling was parsed anyway, failed to parse, and
    resolved to "the retry budget ... is exhausted ... the response is not valid
    JSON" while the run log carried `max_tokens` two lines away.

    The requirement is that truncation is distinguishable from a schema or
    citation failure **by log inspection alone**. It was. The result described
    the other one.
    """
    transport = _Scripted(
        _response(text=_answer("aligned", ("T999",))),
        _response(text='{"verdict": "align', stop_reason=STOP_MAX_TOKENS),
    )
    outcomes = evaluate_call(
        _entry(), _context(), PROVENANCE, template=_template(), transport=transport
    )
    assert transport.calls == 2
    result = outcomes[0].result
    assert result.status is Status.ERRORED
    assert "truncated at max_tokens" in (result.detail or ""), result.detail
    assert "not valid JSON" not in (result.detail or "")
    assert outcomes[0].stop_reason == STOP_MAX_TOKENS


def test_a_response_carrying_no_stop_reason_is_not_read_as_a_complete_answer() -> None:
    """A verdict read out of a response of unknown completeness is a verdict
    about an unknown quantity.

    The API sends a stop reason on every message, so an empty one is a transport
    or a log that lost it. The engine read the empty string as "not a refusal,
    not a truncation" and carried on parsing -- and a scripted response with
    `stop_reason=""` produced an `applicable` verdict, with the empty string in
    the log. Both run-log count guards would flag that in a *committed* log;
    nothing flagged it in the run that produced one.
    """
    transport = _Scripted(_response(stop_reason=""))
    outcomes = evaluate_call(
        _entry(), _context(), PROVENANCE, template=_template(), transport=transport
    )
    assert transport.calls == 1, "a response with no stop reason bought a retry it should not"
    result = outcomes[0].result
    assert result.status is Status.ERRORED
    assert result.verdict is None
    assert "no stop_reason" in (result.detail or ""), result.detail


def test_a_malformed_answer_is_corrected_in_its_own_words_not_an_empty_citation_list() -> None:
    """The retry has two causes and used to have one wording.

    A response that did not parse buys the informed retry -- reasonably, and the
    specification's clause names citations only, which is why the behavior is
    now written down. But `_validate` returns no rejected identifiers for a
    parse failure, so the correction read "Your previous answer cited
    identifiers that were not in this prompt: ." -- an empty list, telling the
    model nothing about what was wrong while looking like it had.
    """
    transport = _Scripted(
        _response(text="here is my answer: it was fine"),
        _response(text=_answer("aligned", ("T1",))),
    )
    evaluate_call(_entry(), _context(), PROVENANCE, template=_template(), transport=transport)
    retry = transport.seen[1]
    assert "could not be read as the JSON object" in retry.prompt
    assert "were not in this prompt: ." not in retry.prompt, (
        "the citation wording was sent with an empty rejected list"
    )
    # The valid set still travels, because a malformed answer is going to be
    # asked for citations too.
    assert "Transcript identifiers, in full:" in retry.prompt


def test_the_retry_prompt_names_the_rejected_id_and_the_valid_set() -> None:
    """The retry is *informed*. A model told only "try again" tends to return
    the same answer."""
    fact = _valid_citation()
    transport = _Scripted(
        _response(text=_answer("aligned", ("T999",))),
        _response(text=_answer("aligned", (fact,))),
    )
    evaluate_call(_entry(), _context(), PROVENANCE, template=_template(), transport=transport)
    retry = transport.seen[1]
    assert "T999" in retry.prompt
    assert f"[{fact}]" in retry.prompt
    assert retry.retry_index == 1
    assert transport.seen[0].retry_index == 0


def test_an_exhausted_retry_budget_returns_errored_rather_than_a_verdict() -> None:
    """The criterion: a judged dimension whose retry budget is exhausted returns
    `status: errored`. A status, not a verdict -- the harness reports that it
    could not evaluate this dimension on this call, rather than reporting a
    judgment it does not have."""
    transport = _Scripted(
        _response(text=_answer("aligned", ("T999",))),
        _response(text=_answer("aligned", ("T998",))),
    )
    outcomes = evaluate_call(
        _entry(), _context(), PROVENANCE, template=_template(), transport=transport
    )
    assert transport.calls == 2
    assert outcomes[0].result.status is Status.ERRORED
    assert outcomes[0].result.verdict is None
    assert outcomes[0].informed_retries == INFORMED_RETRY_BUDGET


def test_a_malformed_response_also_buys_one_retry() -> None:
    """Schema failure and citation failure take the same path, so the retry is
    judged by one rule rather than by two that can drift apart."""
    fact = _valid_citation()
    transport = _Scripted(
        _response(text="not json at all"), _response(text=_answer("aligned", (fact,)))
    )
    outcomes = evaluate_call(
        _entry(), _context(), PROVENANCE, template=_template(), transport=transport
    )
    assert transport.calls == 2
    assert outcomes[0].result.status is Status.APPLICABLE


def test_the_engine_would_notice_an_uncited_answer_read_as_applicable() -> None:
    """P4-23. An answer citing nothing reached the gate as a verdict.

    `parse_answer` accepted an empty `citations` list, `invalid_citations` had nothing to
    reject, and `_evidence_for` appends the rationale to every result's evidence, so the
    evidence guard saw a line and passed -- and an uncited `misaligned` counted against
    the gate as surely as a cited one, held back only by the API-side schema (D163). Now
    an uncited answer is the declared schema's failure: it spends the one informed retry,
    and a retry that still cites nothing is `errored`.
    """
    uncited = _response(text=_answer("misaligned", citations=()))

    transport = _Scripted(uncited, uncited)
    (outcome,) = evaluate_call(
        _entry(), _context(), PROVENANCE, template=_template(), transport=transport
    )
    assert transport.calls == 2, "an uncited answer did not spend the informed retry"
    assert outcome.informed_retries == 1
    assert outcome.result.status is Status.ERRORED
    assert outcome.result.verdict is None

    recovered = _Scripted(uncited, _response(text=_answer("misaligned")))
    (outcome,) = evaluate_call(
        _entry(), _context(), PROVENANCE, template=_template(), transport=recovered
    )
    assert outcome.result.status is Status.APPLICABLE
    assert outcome.result.verdict == "misaligned"
    assert len(outcome.result.evidence) > 1, "the recovered verdict carries no cited line"


def test_the_retry_would_notice_a_schema_failure_it_does_not_name() -> None:
    """P4-27. The correction for a schema failure never said what the failure was.

    `_validate` holds its own account of what went wrong, and the retry dropped it: an
    answer that parsed and cited nothing was told it could not be read as the declared
    object and sent guidance about prose and code fences it had not got wrong, with
    nothing saying which list came back empty. The correction now names the failure
    beside the wording it always had -- here invalid JSON, and an empty `citations`
    list (D164).
    """
    for first, named in (
        (_response(text="not json at all"), "response is not valid JSON"),
        (_response(text=_answer("misaligned", citations=())), "'citations' is empty"),
    ):
        transport = _Scripted(first, _response(text=_answer("misaligned")))
        evaluate_call(_entry(), _context(), PROVENANCE, template=_template(), transport=transport)
        assert transport.calls == 2, f"the failure naming {named!r} did not buy the retry"
        retry = transport.seen[1].prompt
        assert "could not be read as the JSON object this prompt declares: " in retry
        assert named in retry, f"the retry did not name the failure it was sent for: {named!r}"


def test_the_run_continues_after_an_errored_result() -> None:
    """The other half of the same criterion: the run continues to completion
    rather than aborting."""
    transport = _Scripted(
        _response(text=_answer("aligned", ("T999",))),
        _response(text=_answer("aligned", ("T998",))),
    )
    outcomes = evaluate_call(
        _entry(repetitions=3), _context(), PROVENANCE, template=_template(), transport=transport
    )
    assert len(outcomes) == 3
    assert outcomes[0].result.status is Status.ERRORED
    assert [o.result.status for o in outcomes[1:]] == [Status.APPLICABLE, Status.APPLICABLE]


# --------------------------------------------------------------------------
# The three failure modes, kept apart
# --------------------------------------------------------------------------


def test_a_refusal_returns_refused_and_consumes_no_retry() -> None:
    """D23. Retrying identical input against a classifier that just declined it
    spends money to reach the same place."""
    transport = _Scripted(
        _response(stop_reason=STOP_REFUSAL, stop_category="cyber", stop_explanation="declined")
    )
    outcomes = evaluate_call(
        _entry(), _context(), PROVENANCE, template=_template(), transport=transport
    )
    assert transport.calls == 1, "a refusal consumed the retry budget"
    assert outcomes[0].result.status is Status.REFUSED
    assert outcomes[0].informed_retries == 0
    assert "cyber" in (outcomes[0].result.detail or "")


def test_a_truncated_response_returns_errored_carrying_its_stop_reason() -> None:
    """D24. Truncated structured output is unparseable, so without this branch
    a truncation would present as a schema failure, burn the retry on identical
    input, and resolve to `errored` anyway -- by a route that loses the
    reason."""
    transport = _Scripted(_response(stop_reason=STOP_MAX_TOKENS, text='{"verdict": "ali'))
    outcomes = evaluate_call(
        _entry(), _context(), PROVENANCE, template=_template(), transport=transport
    )
    assert transport.calls == 1, "a truncation spent the retry on identical input"
    assert outcomes[0].result.status is Status.ERRORED
    assert outcomes[0].stop_reason == STOP_MAX_TOKENS


def test_the_three_no_verdict_outcomes_are_distinguishable_by_log_inspection(
    tmp_path: Path,
) -> None:
    """The criterion's exact words, for two of them: "distinguishable from a
    retry-exhaustion `errored` by log inspection alone".

    Asserted on the written log rather than on the in-memory results, because
    "by log inspection alone" is a claim about the file.
    """
    path = tmp_path / "run.jsonl"
    header = RunLogHeader(
        rubric_version="1",
        prompt_template_hash=_template().sha256,
        corpus_version="test",
        artifact_hash="0" * 64,
        mode="replay",
        started_at="2026-09-09T12:00:00Z",
    )
    scripted = _Scripted(
        _response(stop_reason=STOP_REFUSAL, stop_category="cyber", stop_explanation="declined"),
        _response(stop_reason=STOP_MAX_TOKENS, text='{"verdict": "ali'),
        _response(text=_answer("aligned", ("T999",))),
        _response(text=_answer("aligned", ("T998",))),
    )
    transport = RecordingTransport(scripted, RunLogWriter(path, header))
    outcomes = evaluate_call(
        _entry(repetitions=3), _context(), PROVENANCE, template=_template(), transport=transport
    )
    assert [o.result.status for o in outcomes] == [
        Status.REFUSED,
        Status.ERRORED,
        Status.ERRORED,
    ]

    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if json.loads(line)["record"] == "call"
    ]
    reasons = [row["stop_reason"] for row in rows]
    assert reasons == [STOP_REFUSAL, STOP_MAX_TOKENS, STOP_END_TURN, STOP_END_TURN]
    assert rows[0]["stop_details"]["category"] == "cyber"
    assert rows[1]["stop_details"]["category"] is None
    # The retry-exhaustion pair is the only one carrying a retry_index of 1.
    assert [row["retry_index"] for row in rows] == [0, 0, 0, 1]


# --------------------------------------------------------------------------
# Transport failure and the ceiling: the run stops, and keeps what it had
# --------------------------------------------------------------------------


def test_a_transient_failure_is_retried_and_then_succeeds() -> None:
    """The backoff loop lives in `LiveTransport`; this asserts the engine does
    not treat a transport that eventually answered as a failure."""
    flaky = _Flaky(failures=0)
    outcomes = evaluate_call(
        _entry(), _context(), PROVENANCE, template=_template(), transport=flaky
    )
    assert outcomes[0].result.status in {Status.APPLICABLE, Status.ERRORED}
    assert flaky.attempts == 1


def test_a_transport_that_gives_up_aborts_the_run_and_keeps_what_it_had(
    tmp_path: Path,
) -> None:
    """The criterion: results already obtained are persisted before any abort.

    Asserted on the log file, because that is where "persisted" has to be true.
    """
    path = tmp_path / "run.jsonl"
    header = RunLogHeader(
        rubric_version="1",
        prompt_template_hash=_template().sha256,
        corpus_version="test",
        artifact_hash="0" * 64,
        mode="replay",
        started_at="2026-09-09T12:00:00Z",
    )

    class _DiesOnThirdCall:
        def __init__(self) -> None:
            self.calls = 0

        def send(self, request: JudgeRequest) -> JudgeResponse:
            self.calls += 1
            if self.calls > 2:
                raise TransientTransportError("the transport gave up")
            return _response(text=_answer_for(request))

    transport = RecordingTransport(_DiesOnThirdCall(), RunLogWriter(path, header))
    judged = run_judged(
        _rubric(), [_context()], PROVENANCE, template=_template(), transport=transport
    )
    assert judged.aborted is not None
    assert "cannot continue" in judged.aborted
    _, entries = read_run_log(path)
    assert len(entries) == 2, "the results obtained before the abort were not persisted"


def test_the_ceiling_halts_the_run_and_names_itself() -> None:
    transport = CeilingTransport(_Scripted(), 3)
    judged = run_judged(
        _rubric(), [_context()], PROVENANCE, template=_template(), transport=transport
    )
    assert judged.aborted is not None
    assert "ceiling" in judged.aborted
    assert transport.issued == 3


def test_the_ceiling_error_is_not_swallowed_as_an_ordinary_transport_failure() -> None:
    """The two aborts are reported differently, because they mean different
    things: one is a budget the operator set and the other is a provider that
    stopped answering."""
    with pytest.raises(CallCeilingReachedError):
        CeilingTransport(_Scripted(), 0).send(
            build_request(
                _entry(),
                render_prompt(
                    _template(),
                    _context(),
                    entry_id=ENTRY_ID,
                    question="q",
                    criteria="c",
                    scale=("aligned", "misaligned"),
                    scale_definitions={"aligned": "a", "misaligned": "b"},
                    requires_facts=("policy_clauses",),
                ),
                call_id="CALL-02",
                repetition=1,
                retry_index=0,
            )
        )


# --------------------------------------------------------------------------
# Ordering, and what a run reports
# --------------------------------------------------------------------------


def test_results_come_back_in_a_fixed_order() -> None:
    """Sorted by call then entry then repetition. An order that depends on
    iteration is an order that will differ, and a report a human reads has to
    be stable."""
    contexts = [_context("CALL-04"), _context("CALL-02"), _context("CALL-03")]
    judged = run_judged(
        _rubric(), contexts, PROVENANCE, template=_template(), transport=_Scripted()
    )
    calls = [o.result.call_id for o in judged.outcomes]
    assert calls == sorted(calls)


def test_a_run_reports_which_entries_it_executed() -> None:
    """And in execution order, which is not id order.

    `entry_ids` was a sorted tuple while the tier held one entry, so ordering
    asserted nothing. It is the order the entries ran in, and from P4 that
    order carries a contract: every synthesis runs after every dimension,
    because a synthesis evaluated first rests on nothing.
    """
    rubric = _rubric()
    judged = run_judged(
        rubric, [_context()], PROVENANCE, template=_template(), transport=_Scripted()
    )
    assert judged.entry_ids == tuple(entry.id for entry in judged_order(rubric))
    assert judged.entry_ids[-1] == SYNTHESIS_ID, (
        f"the synthesis is not last in execution order: {judged.entry_ids}"
    )
    assert judged.for_entry(ENTRY_ID)
    assert judged.for_call("CALL-02")


def test_the_judged_run_executes_only_judged_entries() -> None:
    """The tier filter, in the other engine. The deterministic entries in the
    shipped rubric must not reach a transport."""
    rubric = _rubric()
    transport = _Scripted()
    judged = run_judged(rubric, [_context()], PROVENANCE, template=_template(), transport=transport)
    produced = {o.result.entry_id for o in judged.outcomes}
    assert produced == {entry.id for entry in rubric.for_tier(CheckTier.JUDGE)}
    assert produced.isdisjoint({entry.id for entry in rubric.for_tier(CheckTier.ASSERT)})


def test_an_outcome_carries_the_hash_of_the_request_that_produced_it() -> None:
    """So a result can be walked back to its run-log entry, which is what makes
    "a run log sufficient to reproduce any judged result" checkable."""
    outcomes = evaluate_call(
        _entry(), _context(), PROVENANCE, template=_template(), transport=_Scripted()
    )
    assert isinstance(outcomes[0], JudgedOutcome)
    assert len(outcomes[0].request_hash) == 64


# --------------------------------------------------------------------------
# Every judged field is read, per field
# --------------------------------------------------------------------------


#: The two calls `_exchange` fingerprints, and why it takes two.
#:
#: CALL-02 retrieves a policy and CALL-09 retrieves none, which is what makes
#: the precondition field observable at all. `applies_when_facts_present` does
#: not change what is *in* a request -- it changes whether one is issued -- so
#: on a single call whose facts are present, every value of it produces the
#: same exchange and the field would be reported as moving nothing. Over the
#: pair, removing the precondition turns CALL-09 from zero requests into N.
#:
#: Widened from one call on 2026-09-09, when D125's structural fix added the
#: ninth `JudgeSpec` field. The alternative was an assertion of its own outside
#: the loop, which is the hand-written list this pair exists to refuse.
_FINGERPRINTED_CALLS: Final[tuple[str, ...]] = ("CALL-02", "CALL-09")


def _exchange(entry: RubricEntry) -> tuple[tuple[str, ...], ...]:
    """A fingerprint of everything one evaluation puts on the wire.

    Every request's system message, user message, generation config and declared
    schema, in order, over both calls of `_FINGERPRINTED_CALLS`. **One
    fingerprint rather than a per-field assertion**, and that is what lets the
    coverage below be a rule: `repetitions` changes how many requests there are,
    `applies_when_facts_present` changes whether there are any, and every other
    field changes what is in one -- so a single comparison catches all three
    without the test knowing which kind a given field is.
    """
    requests = []
    for call_id in _FINGERPRINTED_CALLS:
        transport = _Scripted()
        evaluate_call(
            entry, _context(call_id), PROVENANCE, template=_template(), transport=transport
        )
        requests.extend(transport.seen)
    return tuple(
        (
            request.system,
            request.prompt,
            json.dumps(request.config.as_dict(), sort_keys=True),
            json.dumps(request.schema, sort_keys=True),
        )
        for request in requests
    )


def _sent(entry: RubricEntry, call_id: str = "CALL-02") -> JudgeRequest:
    """What one repetition of `entry` puts on the wire."""
    transport = _Scripted()
    evaluate_call(entry, _context(call_id), PROVENANCE, template=_template(), transport=transport)
    return transport.seen[0]


#: A value for every field of `JudgeSpec` that differs from the shipped entry's.
#: Keyed by field name so `test_every_judged_field_has_a_declared_mutation` can
#: compare the keys against `dataclasses.fields` and fail on a field nobody
#: covered -- which is the difference between coverage by RULE and coverage by
#: the list somebody happened to write.
_FIELD_MUTATIONS: Final[Mapping[str, Any]] = {
    "model": "claude-opus-5",
    "max_tokens": 8000,
    "effort": "max",
    "repetitions": 2,
    "question": "A different question entirely?",
    "criteria": "Different criteria entirely.",
    "scale_definitions": {
        "aligned": "a completely different definition",
        "partially_aligned": "another one",
        "misaligned": "and a third",
    },
    "requires_facts": (),
    # Removing the precondition rather than adding one, because the shipped
    # entry declares `policy_clauses` and no fact category renders empty on
    # CALL-02 -- so the only value of this field that changes the exchange is
    # the absent one, observed on CALL-09.
    "applies_when_facts_present": (),
}


def test_every_judged_field_has_a_declared_mutation() -> None:
    """The coverage guard, and the whole point of this pair.

    `test_mutating_each_judged_field_changes_what_is_sent` was written as eight
    hand-listed assertions. All eight fields were covered -- and a NINTH field
    added to `JudgeSpec` would have failed nothing, which is coverage by the
    list somebody wrote rather than by the type.

    That is exactly the gap `ParamView` closes for the deterministic tier: it
    refuses an entry whose check ignored a declared parameter, on every run,
    for every parameter, rather than for whichever one a test chose. A judged
    entry has no `params`, so this is the equivalent -- and it is the *coverage*
    half, which is the half a mutation test cannot buy for itself.
    """
    declared = {field.name for field in dataclasses.fields(JudgeSpec)}
    covered = set(_FIELD_MUTATIONS)
    assert covered == declared, (
        "judged fields with no declared mutation: "
        f"{sorted(declared - covered)}; mutations for fields that do not exist: "
        f"{sorted(covered - declared)}"
    )


def test_mutating_each_judged_field_changes_what_is_sent() -> None:
    """The judged tier's form of "no parameter is hardcoded in Python".

    The deterministic tier buys that property with `ParamView`, which fails an
    entry whose check never read a declared key (D109). A judged entry has no
    `params` -- its configuration is the fields of `JudgeSpec` -- so the
    equivalent assertion is this one: change any one of them, and something the
    model receives changes.

    **Driven by `dataclasses.fields` rather than by a hand-written list**, so a
    field added to `JudgeSpec` and forgotten here fails rather than passing
    silently. W20 is a tier where `params` were decorative for every entry
    except the one somebody looked at, and a fixed list of eight assertions is
    that shape one level up.

    Compared on a fingerprint of the whole exchange, which is what makes the
    loop uniform: `repetitions` changes how many requests there are while every
    other field changes what is in one, and a single comparison catches both.
    """
    base_entry = _entry()
    assert base_entry.judge is not None
    baseline = _exchange(base_entry)

    unmoved: list[str] = []
    for field in dataclasses.fields(JudgeSpec):
        mutated = dataclasses.replace(
            base_entry,
            judge=dataclasses.replace(
                base_entry.judge, **{field.name: _FIELD_MUTATIONS[field.name]}
            ),
        )
        if _exchange(mutated) == baseline:
            unmoved.append(field.name)

    assert not unmoved, (
        f"judged field(s) that move nothing the model receives: {unmoved}. A field the "
        "engine ignores is a value in the rubric that does not describe the rubric's "
        "behavior, which is W20 in the tier with no ParamView to catch it."
    )


def test_the_schema_sent_is_built_from_the_entrys_scale() -> None:
    """The ninth thing a judged entry configures, and it is not a `JudgeSpec`
    field: `scale` lives on the entry itself because both tiers have one. It is
    read on every judged call all the same, so it is asserted here beside the
    eight."""
    import dataclasses

    entry = _entry()
    sent = _sent(entry)
    properties = sent.schema["properties"]
    assert isinstance(properties, dict)
    assert properties["verdict"]["enum"] == list(entry.scale)

    widened = dataclasses.replace(entry, scale=(*entry.scale, "unclear"))
    assert _sent(widened).schema != sent.schema


def test_the_repetitions_obtained_before_an_abort_are_not_discarded() -> None:
    """The control on a defect this phase introduced and then fixed.

    A transport that dies on repetition 3 of 5 used to lose repetitions 1 and 2
    with the exception, while `RecordingTransport` had already written both to
    the run log -- so the run reported fewer results than its own log held.
    Found by a CLI replay test, not by reading.

    Drives `evaluate_call` and requires the partial outcomes to travel with the
    abort. With the outcomes dropped, `obtained` is empty and this fails.
    """

    class _DiesOnThird:
        def __init__(self) -> None:
            self.calls = 0

        def send(self, request: JudgeRequest) -> JudgeResponse:
            del request
            self.calls += 1
            if self.calls >= 3:
                raise TransientTransportError("the transport gave up")
            return _response()

    with pytest.raises(JudgedCallAborted) as excinfo:
        evaluate_call(
            _entry(repetitions=5),
            _context(),
            PROVENANCE,
            template=_template(),
            transport=_DiesOnThird(),
        )
    assert len(excinfo.value.obtained) == 2, (
        "the repetitions completed before the abort were discarded, and the run log "
        "holds entries the run would not report"
    )
    assert [o.repetition for o in excinfo.value.obtained] == [1, 2]
    assert isinstance(excinfo.value.cause, TransientTransportError)


def test_a_run_that_aborts_mid_call_reports_exactly_what_its_log_holds(
    tmp_path: Path,
) -> None:
    """The property the control above exists for, at the level it matters.

    The run's reported results and the run log's entries have to be the same
    set. A harness that disagreed with its own artifact about work it had done
    would make every later question about that log unanswerable.
    """
    path = tmp_path / "run.jsonl"
    header = RunLogHeader(
        rubric_version="1",
        prompt_template_hash=_template().sha256,
        corpus_version="test",
        artifact_hash="0" * 64,
        mode="replay",
        started_at="2026-09-09T12:00:00Z",
    )

    class _DiesOnFourth:
        def __init__(self) -> None:
            self.calls = 0

        def send(self, request: JudgeRequest) -> JudgeResponse:
            self.calls += 1
            if self.calls >= 4:
                raise TransientTransportError("the transport gave up")
            return _response(text=_answer_for(request))

    transport = RecordingTransport(_DiesOnFourth(), RunLogWriter(path, header))
    judged = run_judged(
        _rubric(), [_context()], PROVENANCE, template=_template(), transport=transport
    )
    _, entries = read_run_log(path)
    assert judged.aborted is not None
    # Three issued calls, three run-log entries, three outcomes. The equality
    # holds here because CALL-02 retrieves a policy, so no entry's precondition
    # excludes it and every outcome cost a call -- which is the case this test
    # is about. A call where one did would report more outcomes than entries,
    # legitimately, and that is a different assertion.
    assert len(judged.outcomes) == len(entries) == 3
    assert all(outcome.repetition for outcome in judged.outcomes), (
        "an outcome that cost no call is in this comparison, so the two sides are counting "
        "different things"
    )


# --------------------------------------------------------------------------
# The precondition: a dimension whose subject is absent does not apply (D125)
# --------------------------------------------------------------------------


def test_a_dimension_whose_precondition_fails_returns_not_applicable_and_issues_nothing() -> None:
    """D125's structural fix, on the calls that produced the defect.

    CALL-09 retrieves no policy. Before the precondition, the dimension asked a
    judge whether the terms the agent stated aligned with a clause set that was
    empty -- and "states a rule the clauses do not support" is unconditionally
    true against nothing, so it came back `misaligned` on every repetition of
    every pass. The answer was reproducible and meaningless.

    Three claims, and the third is the one a reading would skip: the status is
    `not_applicable` rather than a verdict, **no request is issued at all**, and
    the outcome says so by carrying `repetition: 0` rather than pretending a
    repetition happened.
    """
    entry = _entry(repetitions=10)
    transport = _Scripted()
    outcomes = evaluate_call(
        entry, _context("CALL-09"), PROVENANCE, template=_template(), transport=transport
    )

    assert not transport.seen, "a dimension that does not apply issued a request anyway"
    assert len(outcomes) == 1, (
        "a dimension that does not apply produced one outcome per repetition, which invents "
        f"repetitions nothing performed: {[o.repetition for o in outcomes]}"
    )
    outcome = outcomes[0]
    assert outcome.result.status is Status.NOT_APPLICABLE
    assert outcome.result.verdict is None
    assert outcome.repetition == 0
    assert not outcome.request_hash and not outcome.stop_reason
    assert "policy_clauses" in (outcome.result.detail or "")


def test_a_dimension_whose_precondition_holds_is_evaluated_normally() -> None:
    """The inversion, and it is not the same assertion read backwards.

    A precondition that reported every category absent would satisfy the test
    above on every call in the corpus, and a tier answering `not_applicable`
    everywhere reads as a clean run rather than as a broken one -- which is
    W11's shape, arriving through a fix. CALL-02 retrieves a policy, so the
    dimension has its subject and has to behave as it did before.
    """
    entry = _entry(repetitions=2)
    transport = _Scripted()
    outcomes = evaluate_call(
        entry, _context("CALL-02"), PROVENANCE, template=_template(), transport=transport
    )

    assert len(transport.seen) == 2, (
        "the dimension stopped issuing requests on a call it applies to"
    )
    assert [o.repetition for o in outcomes] == [1, 2]
    assert all(o.result.status is Status.APPLICABLE for o in outcomes), (
        f"statuses: {[o.result.status.value for o in outcomes]}"
    )


def test_the_precondition_would_notice_a_dimension_that_stopped_applying_to_anything() -> None:
    """The population, not one call of it.

    The two tests above are about one call each, and a precondition mechanism
    can be wrong in a way neither sees: excluding more than it should, and
    quietly. Over the whole design set the two populations have to partition
    it -- every call is either judged or excluded, and the excluded set is
    exactly the calls with no retrieved clause.

    Asserted as a partition rather than as a count, because a count is
    satisfied by the right number of the wrong calls.
    """
    entry = _entry(repetitions=1)
    assert entry.judge is not None
    judged: list[str] = []
    excluded: list[str] = []
    for path in sorted((REPO_ROOT / "corpus" / "transcripts").glob("*.txt")):
        context = _context(path.stem)
        transport = _Scripted()
        outcomes = evaluate_call(
            entry, context, PROVENANCE, template=_template(), transport=transport
        )
        if transport.seen:
            judged.append(context.call_id)
        else:
            excluded.append(context.call_id)
            assert outcomes[0].result.status is Status.NOT_APPLICABLE

    assert judged and excluded, (
        "the precondition put every call on one side, so it is not dividing anything: "
        f"judged {judged}, excluded {excluded}"
    )
    assert sorted(excluded) == sorted(
        context.call_id for context in _contexts() if not context.retrieved_policies
    ), f"excluded {sorted(excluded)}, which is not the set of calls with no retrieved clause"


def test_a_precondition_naming_an_unknown_category_aborts_before_any_call() -> None:
    """The abort has to happen here rather than at rendering.

    A misspelled precondition category is a rubric defect, and the render-time
    refusal cannot catch it: the precondition is evaluated first precisely so
    that a dimension which does not apply costs nothing, so a category nothing
    renders would make the precondition vacuous and the dimension apply to
    every call -- silently, which is the state D125 exists to end.
    """
    import dataclasses

    entry = _entry(repetitions=1)
    assert entry.judge is not None
    broken = dataclasses.replace(
        entry,
        judge=dataclasses.replace(
            entry.judge,
            requires_facts=("policy_clauses", "policy_clauzes"),
            applies_when_facts_present=("policy_clauzes",),
        ),
    )
    transport = _Scripted()
    with pytest.raises(UnknownFactCategoryError) as raised:
        evaluate_call(
            broken, _context("CALL-02"), PROVENANCE, template=_template(), transport=transport
        )
    assert "policy_clauzes" in str(raised.value)
    assert not transport.seen, "a request was issued before the unknown category was refused"


# --------------------------------------------------------------------------
# The synthesis: what it is given, and what it may rest on
# --------------------------------------------------------------------------


def _synthesis_entry(repetitions: int = 1) -> RubricEntry:
    """The shipped synthesis entry, with N narrowed for a test.

    Narrowed the way `_entry` narrows it and for the same reason: every other
    field stays the shipped one, so these remain assertions about the rubric
    rather than about a fixture.
    """
    entry = _rubric().by_id(SYNTHESIS_ID)
    assert entry.judge is not None
    return dataclasses.replace(
        entry, judge=dataclasses.replace(entry.judge, repetitions=repetitions)
    )


def _prior(call_id: str = "CALL-02") -> tuple[JudgedOutcome, ...]:
    """Two dimensions' worth of results for one call, as the run would have them."""
    rubric = _rubric()
    outcomes: list[JudgedOutcome] = []
    for entry_id, verdict in (
        ("J-concerns-addressed", "partially_addressed"),
        ("J-unnecessary-repetition", "warranted"),
    ):
        entry = rubric.by_id(entry_id)
        builder = ResultBuilder(entry=entry, call_id=call_id, provenance=PROVENANCE)
        for repetition in (1, 2):
            outcomes.append(
                JudgedOutcome(
                    result=builder.applicable(
                        verdict, ("[T1] caller: hello", "rationale: because")
                    ),
                    repetition=repetition,
                    request_hash="h",
                    stop_reason=STOP_END_TURN,
                    informed_retries=0,
                )
            )
    return tuple(outcomes)


def _synthesis_answer(rests_on: Sequence[str]) -> str:
    return json.dumps(
        {
            "verdict": "minor_defect",
            "rationale": "because the dimensions disagree about how much it mattered",
            "citations": ["T1"],
            "rests_on": list(rests_on),
        }
    )


def test_a_synthesis_resting_on_a_dimension_that_produced_no_result_is_a_reported_defect() -> None:
    """The requirement's own verb is **report**, and that is what happens.

    A fabricated transcript citation buys the informed retry, because the model
    can be shown the valid set and answer again. A synthesis that rested on a
    dimension which did not run has reasoned from a result that does not exist,
    and re-asking would not tell a reader that it had -- so the verdict stands,
    the defect travels beside it, and the report names both.
    """
    entry = _synthesis_entry()
    transport = _Scripted(_response(text=_synthesis_answer(["J-concerns-addressed", "J-ghost"])))
    outcomes = evaluate_call(
        entry,
        _context("CALL-02"),
        PROVENANCE,
        template=_template(),
        transport=transport,
        prior=_prior(),
        rubric=_rubric(),
    )
    assert len(transport.seen) == 1, "the defect bought a retry, which it must not"
    outcome = outcomes[0]
    assert outcome.result.status is Status.APPLICABLE, "the verdict was discarded rather than kept"
    assert outcome.unresolved_dimensions == ("J-ghost",)


def test_a_synthesis_resting_only_on_dimensions_that_ran_is_reported_clean() -> None:
    """The inversion, and the criterion D130 added because nothing bought it.

    A checker that reported **every** citation as a defect satisfies the
    criterion above -- the design inverted, ticked green. That is exactly what
    D104 found in the P2 grounding criterion whose fixture resolved either way,
    and a citation checker is where it is cheapest to write by accident.
    """
    entry = _synthesis_entry()
    transport = _Scripted(
        _response(text=_synthesis_answer(["J-concerns-addressed", "J-unnecessary-repetition"]))
    )
    outcomes = evaluate_call(
        entry,
        _context("CALL-02"),
        PROVENANCE,
        template=_template(),
        transport=transport,
        prior=_prior(),
        rubric=_rubric(),
    )
    assert outcomes[0].unresolved_dimensions == ()


def test_the_engine_would_notice_a_synthesis_resting_on_nothing_read_as_applicable() -> None:
    """P4-23's twin, on the synthesis's second required list (D163).

    The synthesis's schema requires `rests_on` to name at least one dimension, because a
    synthesis resting on nothing is not a synthesis -- but `parse_answer` accepted an
    empty list, and `unresolved_dimensions` finds nothing unresolved in nothing, so the
    verdict stood clean with no defect beside it. Now it spends the one informed retry,
    and a retry that still rests on nothing is `errored`.
    """
    entry = _synthesis_entry()
    resting_on_nothing = _response(text=_synthesis_answer([]))

    transport = _Scripted(resting_on_nothing, resting_on_nothing)
    (outcome,) = evaluate_call(
        entry,
        _context("CALL-02"),
        PROVENANCE,
        template=_template(),
        transport=transport,
        prior=_prior(),
        rubric=_rubric(),
    )
    assert transport.calls == 2, "a synthesis resting on nothing did not spend the informed retry"
    assert outcome.informed_retries == 1
    assert outcome.result.status is Status.ERRORED

    recovered = _Scripted(
        resting_on_nothing, _response(text=_synthesis_answer(["J-concerns-addressed"]))
    )
    (outcome,) = evaluate_call(
        entry,
        _context("CALL-02"),
        PROVENANCE,
        template=_template(),
        transport=recovered,
        prior=_prior(),
        rubric=_rubric(),
    )
    assert outcome.result.status is Status.APPLICABLE
    assert outcome.unresolved_dimensions == ()


def test_the_retry_would_notice_a_synthesis_not_shown_the_dimensions_it_may_rest_on() -> None:
    """P4-27's second half. A synthesis resting on nothing was told to cite transcript lines.

    The correction restated the transcript and fact identifiers and asked for citations from
    those two lists, when what the synthesis lacked was a dimension. A synthesis corrected for
    a schema failure is now shown the dimension identifiers its prompt listed, bare, and asked
    to rest only on them (D164). A synthesis corrected for rejected identifiers is not: all 8
    retries the committed log records are that kind, and their wording is the recorded one.
    """
    entry = _synthesis_entry()
    transport = _Scripted(
        _response(text=_synthesis_answer([])),
        _response(text=_synthesis_answer(["J-concerns-addressed"])),
    )
    evaluate_call(
        entry,
        _context("CALL-02"),
        PROVENANCE,
        template=_template(),
        transport=transport,
        prior=_prior(),
        rubric=_rubric(),
    )
    retry = transport.seen[1].prompt
    assert "'rests_on' is empty" in retry
    assert (
        "Dimension identifiers, in full: J-concerns-addressed, J-unnecessary-repetition" in retry
    ), "a synthesis corrected for resting on nothing was not shown what it may rest on"
    assert retry.endswith("resting only on those dimensions.")

    cited_wrongly = json.dumps(
        {
            "verdict": "minor_defect",
            "rationale": "because",
            "citations": ["T999"],
            "rests_on": ["J-concerns-addressed"],
        }
    )
    rejected = _Scripted(
        _response(text=cited_wrongly),
        _response(text=_synthesis_answer(["J-concerns-addressed"])),
    )
    evaluate_call(
        entry,
        _context("CALL-02"),
        PROVENANCE,
        template=_template(),
        transport=rejected,
        prior=_prior(),
        rubric=_rubric(),
    )
    retry = rejected.seen[1].prompt
    assert "'T999'" in retry
    assert "Dimension identifiers" not in retry, (
        "a synthesis corrected for rejected identifiers was sent a wording no recorded retry has"
    )
    assert retry.endswith("citing only from those two lists.")


def test_the_retry_would_notice_a_second_fault_it_does_not_name() -> None:
    """P4-30. A synthesis citing `T999` with an empty `rests_on` was corrected for `T999` alone.

    `_validate` returned at the first fault it met, so the correction quoted the rejected
    identifier and said nothing of the empty list, and a retry that fixed the citation and
    kept the empty list was refused -- the one retry spent on half a correction. Every
    fault is now named, each in its own words, and a synthesis with a schema fault among
    them is shown the dimensions it may rest on (D179).
    """
    entry = _synthesis_entry()
    two_faults = json.dumps(
        {
            "verdict": "minor_defect",
            "rationale": "because",
            "citations": ["T999"],
            "rests_on": [],
        }
    )
    transport = _Scripted(
        _response(text=two_faults),
        _response(text=_synthesis_answer(["J-concerns-addressed"])),
    )
    (outcome,) = evaluate_call(
        entry,
        _context("CALL-02"),
        PROVENANCE,
        template=_template(),
        transport=transport,
        prior=_prior(),
        rubric=_rubric(),
    )
    retry = transport.seen[1].prompt
    assert "cited identifiers that were not in this prompt: 'T999'." in retry
    assert "declares: 'rests_on' is empty" in retry
    assert "Dimension identifiers, in full: J-concerns-addressed" in retry
    assert outcome.result.status is Status.APPLICABLE


def test_the_retry_would_notice_an_empty_citations_list_hiding_an_empty_rests_on() -> None:
    """P4-30's other drive. With both lists empty the correction named `citations` alone,
    because the empty-citations refusal ended the reading before `rests_on` (D179)."""
    entry = _synthesis_entry()
    both_empty = json.dumps(
        {
            "verdict": "minor_defect",
            "rationale": "because",
            "citations": [],
            "rests_on": [],
        }
    )
    transport = _Scripted(
        _response(text=both_empty),
        _response(text=_synthesis_answer(["J-concerns-addressed"])),
    )
    evaluate_call(
        entry,
        _context("CALL-02"),
        PROVENANCE,
        template=_template(),
        transport=transport,
        prior=_prior(),
        rubric=_rubric(),
    )
    retry = transport.seen[1].prompt
    assert (
        "'citations' is empty, and the declared schema requires at least one identifier; "
        "'rests_on' is empty"
    ) in retry


def test_the_retry_would_notice_rejected_identifiers_beside_a_missing_field() -> None:
    """A missing field no longer hides the identifiers an answer did cite (D179)."""
    no_verdict = json.dumps({"rationale": "because", "citations": ["T999"]})
    transport = _Scripted(_response(text=no_verdict), _response(text=_answer("aligned", ("T1",))))
    evaluate_call(_entry(), _context(), PROVENANCE, template=_template(), transport=transport)
    retry = transport.seen[1].prompt
    assert "cited identifiers that were not in this prompt: 'T999'." in retry
    assert "declares: response is missing declared field(s): verdict" in retry


def test_an_exhausted_retry_would_notice_a_fault_left_out_of_its_last_failure() -> None:
    """The `errored` result names every fault the retry still showed, not the first (D179)."""
    entry = _synthesis_entry()
    two_faults = json.dumps(
        {
            "verdict": "minor_defect",
            "rationale": "because",
            "citations": ["T999"],
            "rests_on": [],
        }
    )
    transport = _Scripted(_response(text=two_faults), _response(text=two_faults))
    (outcome,) = evaluate_call(
        entry,
        _context("CALL-02"),
        PROVENANCE,
        template=_template(),
        transport=transport,
        prior=_prior(),
        rubric=_rubric(),
    )
    assert outcome.result.status is Status.ERRORED
    detail = outcome.result.detail or ""
    assert "cited identifier(s) not in the prompt: T999" in detail
    assert "'rests_on' is empty" in detail


def test_the_schema_would_notice_a_synthesis_shown_no_dimension_asked_to_rest_on_one() -> None:
    """P4-28. A synthesis shown no dimension was sent a schema demanding it name one.

    `response_schema` was handed the entry, not what the prompt listed, so a synthesis given
    no dimension results -- its prompt saying `NO_DIMENSION_RESULTS`, "do not invent a
    dimension identifier" -- was still sent `rests_on` with `minItems: 1`, and D163's guard
    asked for a name only when one had been listed. A model held to the schema must name
    something, and any name comes back unresolved, so every repetition would carry a defect
    the harness caused. The request now asks for `rests_on` only when a dimension was listed
    (D165); shown the dimensions, the schema is the one every recorded synthesis carries.
    """
    entry = _synthesis_entry()
    unlisted = json.dumps({"verdict": "minor_defect", "rationale": "because", "citations": ["T1"]})
    transport = _Scripted(_response(text=unlisted))
    (outcome,) = evaluate_call(
        entry,
        _context("CALL-02"),
        PROVENANCE,
        template=_template(),
        transport=transport,
        prior=(),
        rubric=_rubric(),
    )
    (request,) = transport.seen
    properties, required = request.schema["properties"], request.schema["required"]
    assert isinstance(properties, Mapping) and isinstance(required, Sequence)
    assert "rests_on" not in properties, "a synthesis shown no dimension was asked to rest on one"
    assert "rests_on" not in required
    assert outcome.result.status is Status.APPLICABLE
    assert outcome.informed_retries == 0
    assert outcome.unresolved_dimensions == ()

    shown = _Scripted()
    evaluate_call(
        entry,
        _context("CALL-02"),
        PROVENANCE,
        template=_template(),
        transport=shown,
        prior=_prior(),
        rubric=_rubric(),
    )
    properties = shown.seen[0].schema["properties"]
    assert isinstance(properties, Mapping)
    assert properties["rests_on"]["minItems"] == 1, "a synthesis shown dimensions lost its rests_on"


def test_the_synthesis_is_shown_the_dimensions_it_is_allowed_to_rest_on() -> None:
    """W1's rule, one population over: validate against what was rendered.

    The valid set for `rests_on` comes back from the renderer with the prompt,
    not from a second walk over the outcomes. A validator that rebuilt the set
    separately is the defect that produced zero confirmed true positives when
    it was done for transcript citations.
    """
    entry = _synthesis_entry()
    rendered = render_prompt(
        _template(),
        _context("CALL-02"),
        entry_id=entry.id,
        question=entry.judge.question if entry.judge else "",
        criteria=entry.judge.criteria if entry.judge else "",
        scale=entry.scale,
        scale_definitions=entry.judge.scale_definitions if entry.judge else {},
        requires_facts=entry.judge.requires_facts if entry.judge else (),
        synthesis=synthesis_input(_prior(), call_id="CALL-02", rubric=_rubric(), repetition=1),
    )
    assert rendered.rests_on == ("J-concerns-addressed", "J-unnecessary-repetition")
    for entry_id in rendered.rests_on:
        assert entry_id in rendered.user, (
            f"{entry_id} is in the validated set and not in the rendered prompt, so the model "
            "is being held to a list it was never shown"
        )


def test_a_dimension_is_not_shown_the_synthesis_instructions_or_asked_for_rests_on() -> None:
    """Two answer-shape instructions in one message is a model choosing one.

    The schema a dimension is handed has no `rests_on`, so a dimension that
    followed the synthesis instructions would return a field the schema forbids
    -- caught, and caught after the money was spent. The sections belong to one
    kind of entry and are removed from the rendered half for the other.
    """
    entry = _entry()
    rendered = render_prompt(
        _template(),
        _context("CALL-02"),
        entry_id=entry.id,
        question=entry.judge.question if entry.judge else "",
        criteria=entry.judge.criteria if entry.judge else "",
        scale=entry.scale,
        scale_definitions=entry.judge.scale_definitions if entry.judge else {},
        requires_facts=entry.judge.requires_facts if entry.judge else (),
    )
    assert rendered.rests_on == ()
    assert "rests_on" not in rendered.system
    assert "DIMENSION_RESULTS" not in rendered.user
    assert "rests_on" not in str(response_schema(entry.scale))
    assert "rests_on" in str(response_schema(entry.scale, synthesis=True))


def test_the_synthesis_runs_after_every_dimension_for_the_same_call() -> None:
    """The ordering contract, asserted on what the synthesis was given.

    A synthesis evaluated first rests on nothing: shown no dimension, it is asked
    for no `rests_on` (D165) and returns a verdict that synthesizes nothing, for a
    reason that is the harness's and not the model's.
    """
    rubric = _rubric()
    transport = _Scripted()
    judged = run_judged(
        rubric, [_context("CALL-02")], PROVENANCE, template=_template(), transport=transport
    )
    order = [request.entry_id for request in transport.seen]
    first_synthesis = order.index(SYNTHESIS_ID)
    assert set(order[first_synthesis:]) == {SYNTHESIS_ID}, (
        f"a dimension ran after the synthesis: {order}"
    )
    del judged


def test_a_synthesis_sees_only_its_own_calls_results() -> None:
    """Scoped per call, not per run.

    A run-wide accumulator would hand the synthesis every verdict recorded
    before it in file order, so the prompt for CALL-04 would depend on which
    call happened to be evaluated first -- and the same rubric over the same
    corpus would send different requests depending on the sort.
    """
    rubric = _rubric()
    transport = _Scripted()
    run_judged(
        rubric,
        [_context("CALL-02"), _context("CALL-03")],
        PROVENANCE,
        template=_template(),
        transport=transport,
    )
    seen = [r.call_id for r in transport.seen if r.entry_id == SYNTHESIS_ID]
    assert set(seen) == {"CALL-02", "CALL-03"}, (
        "the synthesis did not run for both calls, so this compares nothing"
    )

    # **Asserted on the refusal, not on the rendered text.** The block names no
    # call, by design -- the prompt is about one call and saying so on every
    # line would be noise. So a synthesis handed another call's outcomes would
    # render a plausible summary with the repetitions merged, and a test
    # reading the prompt for a foreign call id would see nothing. The guard is
    # in `synthesis_input` and this drives it.
    with pytest.raises(ValueError, match="was given results for"):
        synthesis_input(
            _prior("CALL-02") + _prior("CALL-03"),
            call_id="CALL-03",
            rubric=_rubric(),
            repetition=1,
        )


def _split_prior(call_id: str = "CALL-02") -> tuple[JudgedOutcome, ...]:
    """One dimension whose ten repetitions disagreed, each giving its own rationale.

    Six `partially_addressed` and four `addressed`, so a resample can land the
    counts anywhere from unanimous to reversed and quote any of ten rationales.
    """
    entry = _rubric().by_id("J-concerns-addressed")
    builder = ResultBuilder(entry=entry, call_id=call_id, provenance=PROVENANCE)
    verdicts = ("partially_addressed",) * 6 + ("addressed",) * 4
    return tuple(
        JudgedOutcome(
            result=builder.applicable(verdict, ("[T1] caller: hello", f"rationale: {repetition}")),
            repetition=repetition,
            request_hash="h",
            stop_reason=STOP_END_TURN,
            informed_retries=0,
        )
        for repetition, verdict in enumerate(verdicts, start=1)
    )


def test_each_synthesis_repetition_reads_its_own_resample_of_the_dimensions() -> None:
    """D154: the synthesis's repetitions sample the dimensions' results.

    Rendered once, every repetition of the synthesis read one draw of the other
    dimensions' results -- N samples of a conditional, reported as N samples of
    the verdict (D150). A dimension that split six to four is the case that tells
    the two apart: its line can come out differently on every repetition, and a
    synthesis rendered once is shown it the same way every time.

    **Asserted on what was sent, over two passes.** The prompts must vary within
    the call, and the same outcomes must send the same prompts again, because a
    replay finds a request by what it sent.
    """
    entry = _synthesis_entry(repetitions=10)
    passes: list[list[JudgeRequest]] = []
    for _ in range(2):
        transport = _Scripted()
        evaluate_call(
            entry,
            _context("CALL-02"),
            PROVENANCE,
            template=_template(),
            transport=transport,
            prior=_split_prior(),
            rubric=_rubric(),
        )
        passes.append(transport.seen)
    first, second = passes
    assert len(first) == 10, f"expected ten synthesis requests, saw {len(first)}"
    assert len({request.prompt for request in first}) > 1, (
        "every repetition of the synthesis was sent the same prompt over a dimension that "
        "split, so its repetitions are still samples of one draw"
    )
    assert [r.request_hash for r in first] == [r.request_hash for r in second], (
        "the same outcomes rendered different prompts on a second pass, so a replay would not "
        "find what the recording sent"
    )


def test_a_tied_dimension_is_shown_to_the_synthesis_as_the_report_reads_it() -> None:
    """D154: a line's headline is the report's modal verdict, tie rule included.

    In the committed run the synthesis was shown a different verdict from the
    report's on every tied dimension-call pair there was, because the line took
    `Counter.most_common` -- whichever tied verdict the earliest repetition
    returned -- where the report resolves a tie toward the negative pole.

    **A fixture only the tie rule decides**, checked before it is used: the two
    repetitions tie, and the earliest one's verdict is not the report's. The
    headline is compared with the roll-up itself rather than with a restatement
    of its rule.
    """
    entry = _rubric().by_id("J-caller-pushback-understood")
    builder = ResultBuilder(entry=entry, call_id="CALL-02", provenance=PROVENANCE)
    outcomes = tuple(
        JudgedOutcome(
            result=builder.applicable(verdict, ("[T1] caller: hello", f"rationale: {verdict}")),
            repetition=repetition,
            request_hash="h",
            stop_reason=STOP_END_TURN,
            informed_retries=0,
        )
        for repetition, verdict in enumerate(("understood", "misunderstood"), start=1)
    )
    (call,) = roll_up_judged(outcomes, (entry,))[0].calls
    earliest = Counter(outcome.result.verdict for outcome in outcomes).most_common(1)[0][0]
    assert call.tied, "the fixture does not tie, so it decides nothing about a tie"
    assert earliest != call.verdict, (
        "the earliest repetition's verdict is also the report's, so this fixture cannot tell "
        "the two rules apart"
    )
    headline = dimension_line(entry, outcomes).split("\n", 1)[0].split(": ", 1)[1].split(" (")[0]
    assert headline == call.verdict, (
        f"the synthesis is shown {headline!r} for a dimension the report reads as {call.verdict!r}"
    )
