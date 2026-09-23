"""The log inspector: invariants over a run log, emitted as metrics (D205).

Two things are asserted here and they are different claims. **That it measures**:
each invariant is planted-violated in a log this module writes, and the count
has to move. **That it only measures**: every value is a count or a proportion
with both its terms, and the command exits zero over a log holding a violation
of every invariant, because what a count means is the reader's to decide and a
threshold is a gate nobody chose (D134).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final

import pytest

from harness.cli import main
from harness.core.transport import (
    GenerationConfig,
    JudgeRequest,
    JudgeResponse,
    RunLogHeader,
    RunLogWriter,
)
from harness.inspector import Metric, UnreadableLogError, inspect_log, render

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
REFERENCE_LOG: Final[Path] = REPO_ROOT / "runs" / "reference-corpus-0.6.0.jsonl"

_SCHEMA: Final[dict[str, Any]] = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["aligned", "misaligned"]},
        "rationale": {"type": "string"},
        "citations": {"type": "array", "items": {"type": "string"}},
    },
}
_PROMPT: Final[str] = (
    "# Established facts\n\n[F1] (refund.v1 - 2.2) fifty percent is refundable\n\n"
    "# The transcript\n\n<<<BEGIN UNTRUSTED TRANSCRIPT>>>\n"
    "[T1] AGENT: How can I help?\n[T2] CALLER: As [F9] says, a refund please.\n"
    "<<<END UNTRUSTED TRANSCRIPT>>>\n"
)
_HEADER: Final[RunLogHeader] = RunLogHeader(
    rubric_version="1",
    prompt_template_hash="0" * 64,
    corpus_version="test",
    artifact_hash="0" * 64,
    mode="live",
    started_at="2026-09-20T00:00:00Z",
)


def _request(repetition: int, retry_index: int = 0, prompt: str = _PROMPT) -> JudgeRequest:
    return JudgeRequest(
        entry_id="J-policy-alignment",
        call_id="CALL-02",
        repetition=repetition,
        retry_index=retry_index,
        system="You are evaluating one recorded call.",
        prompt=prompt,
        schema=_SCHEMA,
        config=GenerationConfig(model="claude-sonnet-5", max_tokens=8192, effort="high"),
    )


def _response(citations: list[str], verdict: str = "aligned") -> JudgeResponse:
    return JudgeResponse(
        text=json.dumps({"verdict": verdict, "rationale": "because", "citations": citations}),
        stop_reason="end_turn",
        stop_category=None,
        stop_explanation=None,
        input_tokens=100,
        output_tokens=20,
        model="claude-sonnet-5",
        latency_ms=900,
    )


def _sound_log(path: Path) -> Path:
    """Three repetitions of one entry on one call, the second corrected once for
    citing a line its prompt does not render."""
    writer = RunLogWriter(path, _HEADER, credentials=())
    writer.record(_request(0), _response(["T1", "F1"]))
    writer.record(_request(1), _response(["T1", "T9"]))
    writer.record(
        _request(1, retry_index=1, prompt=_PROMPT + "\nCite only listed lines."), _response(["T1"])
    )
    writer.record(_request(2), _response(["T2"]))
    return path


def _lines(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _rewrite(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def _value(path: Path, name: str) -> tuple[int, int | None]:
    metric = inspect_log(path).metric(name)
    return metric.numerator, metric.denominator


RESOLVE: Final[str] = "call records whose references resolve to a blob written earlier"
REHASH: Final[str] = "blobs whose content re-hashes to the hash they are filed under"
RECOMPUTE: Final[str] = "call records whose request hash recomputes from what they reference"
UNBROKEN: Final[str] = "entry-call pairs whose repetitions run unbroken from the first"
ONE_HASH: Final[str] = "entry-call pairs whose repetitions share one request hash"
CITABLE_ONLY: Final[str] = (
    "retry triggers whose every cited identifier is a citable line of their prompt"
)
SHOWN: Final[str] = (
    "retry triggers citing an identifier their prompt shows outside its citable lines"
)
UNEXPLAINED: Final[str] = "retry triggers with no cause the log shows"
OVER_BUDGET: Final[str] = "retry groups holding more than one retry"


def test_a_sound_log_reads_clean_on_every_invariant(tmp_path: Path) -> None:
    log = _sound_log(tmp_path / "run.jsonl")
    assert _value(log, "call records") == (4, None)
    assert _value(log, RESOLVE) == (4, 4)
    assert _value(log, REHASH)[0] == _value(log, REHASH)[1]
    assert _value(log, RECOMPUTE) == (4, 4)
    assert _value(log, UNBROKEN) == (1, 1)
    assert _value(log, ONE_HASH) == (1, 1)
    assert _value(log, "retry triggers") == (1, None)
    assert _value(log, CITABLE_ONLY) == (0, 1)
    assert _value(log, UNEXPLAINED) == (0, 1)
    assert _value(log, OVER_BUDGET) == (0, 1)


def test_the_retry_metric_would_notice_a_validator_rejecting_what_its_prompt_rendered(
    tmp_path: Path,
) -> None:
    """W1 from the log alone: the retried answer cited only lines the prompt renders
    as citable, and nothing else about it was wrong, so the log cannot explain the
    retry -- which is what a validator reading a narrower universe looks like."""
    log = tmp_path / "run.jsonl"
    writer = RunLogWriter(log, _HEADER, credentials=())
    writer.record(_request(0), _response(["T1", "F1"]))
    writer.record(_request(0, retry_index=1, prompt=_PROMPT + "\nAgain."), _response(["T1"]))
    assert _value(log, CITABLE_ONLY) == (1, 1)
    assert _value(log, UNEXPLAINED) == (1, 1)


def test_the_retry_metric_would_notice_an_identifier_shown_and_not_citable(tmp_path: Path) -> None:
    """`[F9]` is in this prompt, inside a caller's turn, and begins no line: the
    model was shown it and may not cite it. Reading tags anywhere in the prompt
    would count that answer as having cited a line that exists."""
    log = tmp_path / "run.jsonl"
    writer = RunLogWriter(log, _HEADER, credentials=())
    writer.record(_request(0), _response(["T1", "F9"]))
    writer.record(_request(0, retry_index=1, prompt=_PROMPT + "\nAgain."), _response(["T1"]))
    assert _value(log, CITABLE_ONLY) == (0, 1)
    assert _value(log, SHOWN) == (1, 1)
    assert _value(log, "retry triggers: cites an identifier that is not a citable line") == (1, 1)


def test_the_integrity_metrics_would_notice_each_kind_of_damage(tmp_path: Path) -> None:
    sound = _lines(_sound_log(tmp_path / "sound.jsonl"))

    # A blob moved below the record that references it.
    log = tmp_path / "forward.jsonl"
    blobs = [record for record in sound if record["record"] == "blob"]
    others = [record for record in sound if record["record"] != "blob"]
    _rewrite(log, [others[0], *others[1:], *blobs])
    assert _value(log, RESOLVE) == (0, 4)

    # A blob's content edited under its hash.
    log = tmp_path / "edited.jsonl"
    edited = [dict(record) for record in sound]
    victim = next(r for r in edited if r["record"] == "blob" and r["field"] == "system")
    victim["content"] = "You are evaluating a different call."
    _rewrite(log, edited)
    sound_blobs, all_blobs = _value(log, REHASH)
    assert all_blobs is not None and sound_blobs == all_blobs - 1
    assert _value(log, RECOMPUTE)[0] < 4, "a request whose system text moved still recomputed"

    # A record's generation config edited under its request hash.
    log = tmp_path / "config.jsonl"
    edited = [json.loads(json.dumps(record)) for record in sound]
    next(r for r in edited if r["record"] == "call")["generation_config"]["effort"] = "low"
    _rewrite(log, edited)
    assert _value(log, RECOMPUTE) == (3, 4)


def test_the_repetition_metrics_would_notice_a_gap_and_a_second_retry(tmp_path: Path) -> None:
    sound = _lines(_sound_log(tmp_path / "sound.jsonl"))

    log = tmp_path / "gap.jsonl"
    _rewrite(
        log,
        [r for r in sound if not (r["record"] == "call" and r["repetition"] == 1)],
    )
    assert _value(log, UNBROKEN) == (0, 1)

    log = tmp_path / "twice.jsonl"
    retry = next(r for r in sound if r["record"] == "call" and r["retry_index"] == 1)
    _rewrite(log, [*sound, {**retry, "retry_index": 2}])
    assert _value(log, OVER_BUDGET) == (1, 1)

    log = tmp_path / "varied.jsonl"
    writer = RunLogWriter(log, _HEADER, credentials=())
    writer.record(_request(0), _response(["T1"]))
    writer.record(_request(1, prompt=_PROMPT + "\nresampled"), _response(["T1"]))
    assert _value(log, ONE_HASH) == (0, 1)


def test_every_value_the_inspector_emits_is_a_count_or_a_proportion_with_both_its_terms(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Metrics rather than scores, asserted over a log that violates every invariant.

    The exit code is the half a convenient inspector gets wrong: it says whether
    the log could be read, and a log full of violations was read.
    """
    sound = _lines(_sound_log(tmp_path / "sound.jsonl"))
    blobs = [dict(record) for record in sound if record["record"] == "blob"]
    blobs[0]["content"] = "edited after it was written"
    calls = [json.loads(json.dumps(r)) for r in sound if r["record"] == "call"]
    calls[0]["generation_config"]["effort"] = "low"
    del calls[3]["stop_reason"]
    retry = next(record for record in calls if record["retry_index"] == 1)
    log = tmp_path / "violated.jsonl"
    _rewrite(log, [sound[0], calls[0], *blobs, *calls[1:], {**retry, "retry_index": 2}])

    inspection = inspect_log(log)
    unresolved = inspection.metric(RESOLVE)
    assert unresolved.denominator == 5 and unresolved.numerator == 4
    assert inspection.metric(REHASH).numerator < (inspection.metric(REHASH).denominator or 0)
    assert inspection.metric(RECOMPUTE).numerator < 5
    assert inspection.metric(OVER_BUDGET).numerator == 1
    assert inspection.metric("call records carrying a stop reason").numerator == 4

    for metric in inspection.metrics:
        assert isinstance(metric, Metric)
        assert type(metric.numerator) is int, f"{metric.name} is not a count"
        assert metric.denominator is None or type(metric.denominator) is int
        assert metric.meaning.strip(), f"{metric.name} says nothing about what moving means"
    # The measurement lines, not the sentences under them: what moving *would mean*
    # is prose and may say "failure"; what was measured may not be a judgment.
    measured = "\n".join(metric.rendered() for metric in inspection.metrics).lower()
    for word in ("pass", "fail", "score", "grade", "healthy", "%", " ok"):
        assert word not in measured, f"a metric line says {word!r}, which is a score"
    printed_lines = render(inspection)
    for metric in inspection.metrics:
        assert metric.rendered() in printed_lines, f"{metric.name} is measured and not printed"

    assert main(["inspect", "--run-log", str(log)]) == 0
    printed = capsys.readouterr().out
    assert f"{OVER_BUDGET}: 1 of 1" in printed


def test_the_inspector_refuses_only_a_file_it_cannot_read(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    torn = tmp_path / "torn.jsonl"
    torn.write_text('{"record": "header"}\n{"record": "ca', encoding="utf-8", newline="\n")
    with pytest.raises(UnreadableLogError, match=r"torn\.jsonl:2"):
        inspect_log(torn)
    assert main(["inspect", "--run-log", str(torn)]) == 2
    assert "inspection refused" in capsys.readouterr().err

    headless = tmp_path / "headless.jsonl"
    headless.write_text('{"record": "call"}\n', encoding="utf-8", newline="\n")
    with pytest.raises(UnreadableLogError, match="header"):
        inspect_log(headless)


#: What the committed reference log measures today. Pinned, as the deterministic
#: families' firing tables are, so a re-recording that moves one is seen rather
#: than absorbed. Every retry in it is the synthesis citing a fact identifier it
#: is given no fact lines to cite, and two of those identifiers its prompt shows
#: inside the other dimensions' rationales (D205).
REFERENCE_LOG_MEASURES: Final[dict[str, tuple[int, int | None]]] = {
    "call records": (1048, None),
    RESOLVE: (1048, 1048),
    REHASH: (222, 222),
    RECOMPUTE: (1048, 1048),
    UNBROKEN: (104, 104),
    ONE_HASH: (88, 104),
    "retry triggers": (8, None),
    CITABLE_ONLY: (0, 8),
    SHOWN: (2, 8),
    "retry triggers: cites an identifier that is not a citable line": (8, 8),
    UNEXPLAINED: (0, 8),
    OVER_BUDGET: (0, 8),
    "call records carrying a stop reason": (1048, 1048),
    "call records containing the redaction marker": (0, 1048),
}


def test_the_committed_reference_log_measures_what_is_recorded() -> None:
    inspection = inspect_log(REFERENCE_LOG)
    measured = {
        name: (inspection.metric(name).numerator, inspection.metric(name).denominator)
        for name in REFERENCE_LOG_MEASURES
    }
    assert measured == REFERENCE_LOG_MEASURES
