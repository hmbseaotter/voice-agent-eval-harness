"""The model transport seam: recording, replay, staleness, ceiling, credentials.

Every test here runs with **no credential and no network**. That is not a
convenience: D8's claim is that a reader clones this repository and runs it with
no API key, and a suite that needed one to test the seam would be asserting the
opposite of the claim.

The live transport is exercised through a stub client rather than a real one.
What that buys and what it does not is worth stating: it proves the backoff
loop, the transient/non-transient split, the streaming threshold and the
response mapping. It does not prove the SDK accepts the parameters -- that is a
fact about `anthropic` 1.4.0, checked against the installed package's own
signature in `test_the_sdk_accepts_every_parameter_the_seam_sends`.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, ClassVar, Final

import pytest

from harness.core.transport import (
    _DOTENV_CACHE,
    BACKOFF_BASE_SECONDS,
    BACKOFF_CEILING_SECONDS,
    BLOB_FIELDS,
    CREDENTIAL_VARIABLES,
    DOTENV_FILENAME,
    MAX_TRANSPORT_ATTEMPTS,
    MIN_RETRY_WINDOW_SECONDS,
    MINIMUM_CREDENTIAL_LENGTH,
    PRICING_USD_PER_MTOK,
    REDACTION,
    REQUEST_TIMEOUT_SECONDS,
    SDK_RETRIES,
    STOP_END_TURN,
    STOP_MAX_TOKENS,
    STOP_REFUSAL,
    STREAMING_THRESHOLD_TOKENS,
    SUPPORTED_MODELS,
    CallCeilingReachedError,
    CeilingTransport,
    CredentialMissingError,
    GenerationConfig,
    JudgeRequest,
    JudgeResponse,
    LabelsManifestMismatchError,
    RecordingTransport,
    ReplayCacheMissError,
    RubricHashMismatchError,
    RunLogFormatError,
    RunLogHeader,
    RunLogWriter,
    StaleReplayLogError,
    TransientTransportError,
    UnpricedModelError,
    backoff_delay,
    blob_hash,
    check_labels_manifest,
    check_rubric_hash,
    client_options,
    credential_environment,
    credential_values,
    estimate_cost_usd,
    load_replay_transport,
    rates_for,
    read_dotenv,
    read_run_log,
    read_run_log_to_last_record,
    resolve_credential,
    scrub_credentials,
    stale_differences,
)

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
SCHEMA: Final[dict[str, Any]] = {"type": "object", "properties": {}}


def _request(**overrides: Any) -> JudgeRequest:
    base: dict[str, Any] = {
        "entry_id": "J-policy-alignment",
        "call_id": "CALL-02",
        "repetition": 1,
        "retry_index": 0,
        "system": "you are evaluating one call",
        "prompt": "[T1] agent: all set",
        "schema": SCHEMA,
        "config": GenerationConfig(model="claude-sonnet-5", max_tokens=2048, effort="high"),
    }
    base.update(overrides)
    return JudgeRequest(**base)


def _response(**overrides: Any) -> JudgeResponse:
    base: dict[str, Any] = {
        "text": '{"verdict": "aligned", "rationale": "ok", "citations": ["T1"]}',
        "stop_reason": STOP_END_TURN,
        "stop_category": None,
        "stop_explanation": None,
        "input_tokens": 100,
        "output_tokens": 20,
        "model": "claude-sonnet-5",
        "latency_ms": 12,
    }
    base.update(overrides)
    return JudgeResponse(**base)


def _header(**overrides: Any) -> RunLogHeader:
    base: dict[str, Any] = {
        "rubric_version": "1",
        "prompt_template_hash": "a" * 64,
        "corpus_version": "0.4.0",
        "artifact_hash": "b" * 64,
        "mode": "replay",
        "started_at": "2026-09-09T12:00:00Z",
    }
    base.update(overrides)
    return RunLogHeader(**base)


class _Spy:
    """A transport that records what it was asked and answers from a script."""

    def __init__(self, responses: list[JudgeResponse] | None = None) -> None:
        self.seen: list[JudgeRequest] = []
        self._responses = responses

    def send(self, request: JudgeRequest) -> JudgeResponse:
        self.seen.append(request)
        if self._responses:
            return self._responses.pop(0)
        return _response()

    @property
    def calls(self) -> int:
        return len(self.seen)


# --------------------------------------------------------------------------
# The request hash: what it covers, and what it deliberately does not
# --------------------------------------------------------------------------


def test_the_request_hash_covers_only_what_the_model_sees() -> None:
    """Two requests differing only in who is asking hash the same.

    The hash addresses the replay lookup, and a hash that moved when the entry
    id changed would make a recorded log unreplayable after a rename that
    changed nothing about the request.
    """
    assert _request().request_hash == _request(entry_id="J-other", call_id="CALL-99").request_hash


def test_the_request_hash_moves_when_any_part_of_the_request_does() -> None:
    """Each of the four things the model sees, one at a time."""
    base = _request().request_hash
    assert _request(system="different").request_hash != base
    assert _request(prompt="different").request_hash != base
    assert _request(schema={"type": "string"}).request_hash != base
    assert (
        _request(
            config=GenerationConfig(model="claude-opus-5", max_tokens=2048, effort="high")
        ).request_hash
        != base
    )


def test_repetitions_share_a_hash_because_they_are_the_same_request() -> None:
    """N repetitions send byte-identical requests, which is what makes N a
    measurement of the model's variance rather than of the prompt's (D17).

    The pair (hash, repetition) is therefore what replay keys on -- and this is
    the assertion that says why a hash alone would not do.
    """
    assert _request(repetition=1).request_hash == _request(repetition=7).request_hash


# --------------------------------------------------------------------------
# Credentials never reach a log or an error message
# --------------------------------------------------------------------------


def test_a_credential_in_the_environment_is_removed_from_text() -> None:
    secret = "sk-ant-notarealkey-0123456789"
    scrubbed = scrub_credentials(f"before {secret} after", [secret])
    assert secret not in scrubbed
    assert scrubbed == f"before {REDACTION} after"


def test_every_declared_credential_variable_is_scrubbed() -> None:
    """Both names, not just the one the live path happens to read.

    A key exported under the SDK's alternative name is the same secret, and a
    scrubber that knew about one of two would be a guard with a hole shaped
    like an environment variable.
    """
    for name in CREDENTIAL_VARIABLES:
        secret = "sk-ant-" + name.lower() + "-value"
        assert secret not in scrub_credentials(f"x {secret} y", [secret])


def test_a_value_too_short_to_be_a_key_does_not_redact_the_whole_log() -> None:
    """An empty or one-character variable would otherwise match between every
    pair of characters and destroy the log in the name of protecting it."""
    short = "a" * (MINIMUM_CREDENTIAL_LENGTH - 1)
    text = "the quick brown fox"
    assert scrub_credentials(text, [short]) == text
    assert scrub_credentials(text, [""]) == text


def test_the_run_log_carries_no_credential_that_was_in_the_prompt(tmp_path: Path) -> None:
    """The requirement, asserted over a real written artifact.

    Scans the file the writer produced rather than the string the scrubber
    returned -- "no credential value appears in any run log" is a property of
    the artifact, and asserting it on the scrubber's output would be asserting
    it one layer above where it has to hold.
    """
    secret = "sk-ant-notarealkey-0123456789"
    path = tmp_path / "run.jsonl"
    writer = RunLogWriter(path, _header(), credentials=[secret])

    # Drives `RecordingTransport.send` -> `RunLogWriter.record`, the shipped
    # path, rather than serializing an entry beside it. A control that called
    # `RunLogEntry.as_dict` itself would prove the scrubber works and say
    # nothing about whether the writer uses it -- which is the shape D121 found
    # in six controls, every one of them measuring nothing. The first draft of
    # this test was that shape, and the writer grew an injectable `environ` so
    # that it did not have to be.
    transport = RecordingTransport(_Spy(), writer)
    transport.send(_request(prompt=f"a transcript that somehow contains {secret} in it"))

    written = path.read_text(encoding="utf-8")
    assert secret not in written, "the run log contains a credential value"
    assert REDACTION in written


def test_no_scrubbed_field_of_a_run_log_entry_carries_a_credential(tmp_path: Path) -> None:
    """All four fields the writer scrubs, planted at once.

    Until 2026-09-09 the only test drove the **prompt** field, and removing the
    scrub from `response_text`, from `system` or from a refusal's `explanation`
    left the entire judged-tier suite green. `response_text` is the field most
    likely to carry a stray secret, because it is the model's text and not this
    project's -- a judge asked to quote the prompt back can put anything in it.

    The count of redaction tokens is asserted as well as the absence of the
    values: a writer that dropped the four fields entirely would satisfy "the
    secret is not in the file" and lose the log.
    """
    secret = "sk-ant-notarealkey-0123456789"
    path = tmp_path / "run.jsonl"
    writer = RunLogWriter(path, _header(), credentials=[secret])

    response = _response(
        text=f"the model quoted {secret} back",
        stop_reason=STOP_REFUSAL,
        stop_category="policy",
        stop_explanation=f"declined; the prompt held {secret}",
    )
    request = _request(
        system=f"a system prompt mentioning {secret}",
        prompt=f"a transcript containing {secret}",
    )
    RecordingTransport(_Spy([response]), writer).send(request)

    written = path.read_text(encoding="utf-8")
    assert secret not in written, "a scrubbed field of the run log carries a credential value"
    assert written.count(REDACTION) == 4, (
        f"expected all four scrubbed fields to be redacted, found {written.count(REDACTION)}"
    )


def test_a_missing_credential_is_refused_naming_the_variables_and_not_their_values() -> None:
    error = str(CredentialMissingError())
    for name in CREDENTIAL_VARIABLES:
        assert name in error


# --------------------------------------------------------------------------
# The ceiling refuses before the call
# --------------------------------------------------------------------------


def test_a_run_reaching_its_ceiling_issues_no_further_call() -> None:
    """Asserted by a transport spy counting calls, as the criterion asks."""
    spy = _Spy()
    ceiling = CeilingTransport(spy, 2)
    ceiling.send(_request())
    ceiling.send(_request(repetition=2))
    with pytest.raises(CallCeilingReachedError):
        ceiling.send(_request(repetition=3))
    assert spy.calls == 2, "the refused call reached the inner transport anyway"


def test_the_ceiling_is_a_number_of_calls_issued_and_not_that_number_plus_one() -> None:
    """The control on the boundary. A ceiling checked after the call rather
    than before would let exactly one more through, and the count above would
    still read 2 if the check were merely misplaced by one in the other
    direction."""
    spy = _Spy()
    ceiling = CeilingTransport(spy, 1)
    ceiling.send(_request())
    with pytest.raises(CallCeilingReachedError):
        ceiling.send(_request())
    assert spy.calls == 1


def test_a_refused_call_is_not_recorded_because_it_did_not_happen(tmp_path: Path) -> None:
    """Composition order, asserted. `Recording(Ceiling(inner))` means a call
    the ceiling refused has no run-log entry -- rather than an entry describing
    a call nobody made."""
    path = tmp_path / "run.jsonl"
    writer = RunLogWriter(path, _header())
    transport = RecordingTransport(CeilingTransport(_Spy(), 1), writer)
    transport.send(_request())
    with pytest.raises(CallCeilingReachedError):
        transport.send(_request(repetition=2))
    _, entries = read_run_log(path)
    assert len(entries) == 1


# --------------------------------------------------------------------------
# Recording is unconditional
# --------------------------------------------------------------------------


def test_every_call_that_returns_is_recorded(tmp_path: Path) -> None:
    path = tmp_path / "run.jsonl"
    transport = RecordingTransport(_Spy(), RunLogWriter(path, _header()))
    for repetition in (1, 2, 3):
        transport.send(_request(repetition=repetition))
    _, entries = read_run_log(path)
    assert [entry.request.repetition for entry in entries] == [1, 2, 3]


def _call_records(path: Path) -> list[dict[str, Any]]:
    """The call records of a run log, with the blob records filtered out.

    A log is no longer one record per call: `system`, `prompt` and `schema` are
    written once and referenced (D128, D131), so a test indexing lines by
    position reads a blob and reports it as a malformed call.
    """
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    return [row for row in rows if row.get("record") == "call"]


def _blob_records(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    return [row for row in rows if row.get("record") == "blob"]


def test_every_recorded_entry_carries_a_stop_reason(tmp_path: Path) -> None:
    """ "Every run-log entry for a judged call carries a stop_reason; the count
    missing one is zero" -- asserted as the criterion words it, over responses
    that reached the log by three different routes."""
    path = tmp_path / "run.jsonl"
    responses = [
        _response(stop_reason=STOP_END_TURN),
        _response(stop_reason=STOP_MAX_TOKENS, text="{ truncated"),
        _response(stop_reason=STOP_REFUSAL, stop_category="cyber", stop_explanation="declined"),
    ]
    transport = RecordingTransport(_Spy(responses), RunLogWriter(path, _header()))
    for repetition in (1, 2, 3):
        transport.send(_request(repetition=repetition))

    calls = _call_records(path)
    assert len(calls) == 3
    assert sum(1 for row in calls if not row.get("stop_reason")) == 0


def test_a_refusal_records_its_category_and_explanation(tmp_path: Path) -> None:
    """D23. The two fields that make a refusal distinguishable from a
    retry-exhaustion `errored` by log inspection alone."""
    path = tmp_path / "run.jsonl"
    transport = RecordingTransport(
        _Spy([_response(stop_reason=STOP_REFUSAL, stop_category="cyber", stop_explanation="no")]),
        RunLogWriter(path, _header()),
    )
    transport.send(_request())
    _, entries = read_run_log(path)
    assert entries[0].response.stop_category == "cyber"
    assert entries[0].response.stop_explanation == "no"


def test_the_generation_configuration_is_recorded_beside_the_stop_reason(tmp_path: Path) -> None:
    """The requirement names both, and a log carrying one without the other
    cannot answer "was this truncated because max_tokens was too low"."""
    path = tmp_path / "run.jsonl"
    RecordingTransport(_Spy(), RunLogWriter(path, _header())).send(_request())
    row = _call_records(path)[0]
    assert row["generation_config"] == {
        "model": "claude-sonnet-5",
        "max_tokens": 2048,
        "effort": "high",
    }
    assert row["stop_reason"] == STOP_END_TURN
    assert row["input_tokens"] == 100
    assert row["output_tokens"] == 20
    assert row["latency_ms"] == 12
    assert row["response_text"]
    # The three referenced fields, asserted on what they **resolve to** rather
    # than on the presence of a hash. A record naming three blobs the log does
    # not carry would satisfy any check for a non-empty reference, and the
    # requirement is that the exact prompt sent is recoverable.
    _, entries = read_run_log(path)
    assert entries[0].request.system and entries[0].request.prompt and entries[0].request.schema


# --------------------------------------------------------------------------
# The run log stores what was sent once and references it (D128, D131)
# --------------------------------------------------------------------------


def test_one_string_sent_n_times_is_stored_once_and_referenced_n_times(tmp_path: Path) -> None:
    """The whole of D128, measured on the file rather than argued.

    N repetitions of one dimension send byte-identical requests by design
    (D17), so the old format wrote one 3,333-character system prompt 160 times
    and called it a record of what was sent. The claim here is not that the
    file is smaller -- it is that the number of stored copies is one, which is
    what makes the size a consequence rather than a coincidence.
    """
    path = tmp_path / "run.jsonl"
    writer = RunLogWriter(path, _header())
    transport = RecordingTransport(_Spy([_response() for _ in range(5)]), writer)
    for repetition in range(1, 6):
        transport.send(_request(repetition=repetition))

    calls = _call_records(path)
    blobs = _blob_records(path)
    assert len(calls) == 5
    # Three fields, one distinct value each across five identical requests.
    assert len(blobs) == 3, [blob["field"] for blob in blobs]
    assert {blob["field"] for blob in blobs} == set(BLOB_FIELDS)
    for call in calls:
        assert {call["system_ref"], call["prompt_ref"], call["schema_ref"]} == {
            blob["blob_hash"] for blob in blobs
        }


def test_a_blob_is_written_before_the_record_that_references_it(tmp_path: Path) -> None:
    """The ordering invariant, asserted on positions in the file.

    A run that aborts part-way must leave behind the results it obtained, and
    the reader resolves references in one pass. Both hold only if a blob
    precedes every record naming it: written the other way round, a truncation
    between the two writes leaves a dangling reference inside the results the
    requirement says are persisted.
    """
    path = tmp_path / "run.jsonl"
    transport = RecordingTransport(_Spy([_response(), _response()]), RunLogWriter(path, _header()))
    transport.send(_request(call_id="CALL-02"))
    transport.send(_request(call_id="CALL-03", prompt="[T1] agent: a different call"))

    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    seen: set[str] = set()
    for position, row in enumerate(rows):
        if row.get("record") == "blob":
            seen.add(row["blob_hash"])
        elif row.get("record") == "call":
            for field in BLOB_FIELDS:
                assert row[f"{field}_ref"] in seen, (
                    f"line {position}: the call record references a {field} blob that appears "
                    "later in the file, so a log truncated here would not resolve"
                )


def test_what_the_writer_stored_resolves_back_to_what_was_sent(tmp_path: Path) -> None:
    """Recoverability, which is the requirement the format change had to keep.

    "Record the exact prompt sent" is satisfied by a reference only if
    following it returns the string. Asserted on all three referenced fields
    and on equality with the request object, not on the fields being non-empty.
    """
    path = tmp_path / "run.jsonl"
    request = _request(system="SYSTEM|one", prompt="[T1] caller: two", schema={"type": "object"})
    RecordingTransport(_Spy(), RunLogWriter(path, _header())).send(request)

    _, entries = read_run_log(path)
    assert len(entries) == 1
    assert entries[0].request.system == request.system
    assert entries[0].request.prompt == request.prompt
    assert entries[0].request.schema == request.schema
    assert entries[0].request.request_hash == request.request_hash


def test_a_reference_to_a_blob_the_log_does_not_carry_is_refused_by_name(tmp_path: Path) -> None:
    """A damaged log is not a stale one and is not a cache miss.

    Three failures present as "this log is no use" and the advice each implies
    is different: a miss says record more, staleness says re-record, and this
    says the file was damaged. Re-recording on that advice spends money to fix
    a truncation.
    """
    path = tmp_path / "run.jsonl"
    RecordingTransport(_Spy(), RunLogWriter(path, _header())).send(_request())
    kept = [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if json.loads(line).get("field") != "prompt"
    ]
    path.write_text("\n".join(kept) + "\n", encoding="utf-8")

    with pytest.raises(RunLogFormatError) as raised:
        read_run_log(path)
    assert "prompt" in str(raised.value)
    assert not isinstance(raised.value, StaleReplayLogError | ReplayCacheMissError)


def test_a_call_record_with_no_reference_at_all_is_refused_by_name(tmp_path: Path) -> None:
    """The other half, told apart from the first.

    A record carrying no prompt reference was written by something that does
    not know this format; one whose reference dangles was written by something
    that does and then lost a line. The messages name different causes because
    the reader has to send somebody to fix different things.
    """
    path = tmp_path / "run.jsonl"
    RecordingTransport(_Spy(), RunLogWriter(path, _header())).send(_request())
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    for row in rows:
        if row.get("record") == "call":
            del row["prompt_ref"]
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8"
    )

    with pytest.raises(RunLogFormatError) as raised:
        read_run_log(path)
    assert "prompt_ref" in str(raised.value)


def test_a_blob_that_does_not_hash_to_its_own_identifier_is_refused(tmp_path: Path) -> None:
    """The log's index, checked against what the log stores.

    Every downstream claim about a committed log -- the exact prompt sent first
    among them -- rests on its self-description. Checked on read rather than
    trusted, because the check costs a hash of a string already parsed, and a
    file whose index disagrees with its contents can otherwise be replayed
    against for as long as nobody looks.
    """
    path = tmp_path / "run.jsonl"
    RecordingTransport(_Spy(), RunLogWriter(path, _header())).send(_request())
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    for row in rows:
        if row.get("record") == "blob" and row["field"] == "system":
            row["content"] = row["content"] + " and one word more"
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8"
    )

    with pytest.raises(RunLogFormatError) as raised:
        read_run_log(path)
    assert "disagrees with what it stores" in str(raised.value)


def test_the_reader_would_notice_a_torn_line_escaping_as_a_decode_error(tmp_path: Path) -> None:
    """P4-11. A line cut off mid-write is refused by file and line (OB-28, D167).

    It escaped as the parser's own `JSONDecodeError`, so replay and report exited
    1 -- the code for a gate that failed -- with a traceback. The strict reader
    refuses a torn final line, and even a resume's reading refuses a torn line
    with complete records after it, which is damage rather than an abort.
    """
    path = tmp_path / "run.jsonl"
    recording = RecordingTransport(_Spy(), RunLogWriter(path, _header()))
    recording.send(_request())
    recording.send(_request(repetition=2))
    lines = path.read_text(encoding="utf-8").splitlines()

    torn_tail = tmp_path / "torn-tail.jsonl"
    cut = [*lines[:-1], lines[-1][: len(lines[-1]) // 2]]
    torn_tail.write_bytes("\n".join(cut).encode("utf-8"))
    with pytest.raises(RunLogFormatError) as raised:
        read_run_log(torn_tail)
    assert str(torn_tail) in str(raised.value)
    assert f"line {len(lines)}" in str(raised.value)

    middle = len(lines) // 2
    torn_middle = tmp_path / "torn-middle.jsonl"
    damaged = [*lines[:middle], lines[middle][:10], *lines[middle + 1 :]]
    torn_middle.write_bytes(("\n".join(damaged) + "\n").encode("utf-8"))
    with pytest.raises(RunLogFormatError) as raised:
        read_run_log_to_last_record(torn_middle)
    assert f"line {middle + 1}" in str(raised.value)


def test_a_resume_would_notice_its_torn_tail_refused_instead_of_dropped(tmp_path: Path) -> None:
    """A resume's reading drops a torn final line and counts it (OB-28, D167).

    A run that stops mid-write leaves its last line incomplete, and that is the
    log a resume exists to finish. Its reading returns every complete record and
    says it dropped one, where the strict reader refuses the same file; a reading
    that refused too would refuse every log an abort mid-write leaves.
    """
    path = tmp_path / "run.jsonl"
    recording = RecordingTransport(_Spy(), RunLogWriter(path, _header()))
    recording.send(_request())
    recording.send(_request(repetition=2))
    lines = path.read_text(encoding="utf-8").splitlines()
    cut = [*lines[:-1], lines[-1][: len(lines[-1]) // 2]]
    path.write_bytes("\n".join(cut).encode("utf-8"))

    header, entries, dropped = read_run_log_to_last_record(path)
    assert dropped == 1
    assert header == _header()
    assert [entry.request.repetition for entry in entries] == [1]
    with pytest.raises(RunLogFormatError):
        read_run_log(path)


def test_a_credential_is_scrubbed_inside_the_blob_and_the_hash_covers_the_scrub(
    tmp_path: Path,
) -> None:
    """Both halves, and the second is the one a format change could have lost.

    Two of the referenced fields pass through the scrubber, and an audit found
    three of the four scrub sites driven by nothing. Moving them into a blob
    record is exactly the kind of edit that relocates a scrub past its own
    test.

    The second half is new with the format: the blob is filed under a hash of
    the **scrubbed** content, so a reader can recompute it from what the file
    holds. Hashed before scrubbing, every committed log would carry an index
    that fails its own check.
    """
    path = tmp_path / "run.jsonl"
    secret = "sk-ant-notarealkey-0123456789"
    writer = RunLogWriter(path, _header(), credentials=[secret])
    RecordingTransport(_Spy(), writer).send(_request(system=f"key {secret} here"))

    text = path.read_text(encoding="utf-8")
    assert secret not in text
    for blob in _blob_records(path):
        assert blob_hash(blob["content"]) == blob["blob_hash"], (
            "the blob is filed under a hash of the value before it was scrubbed, so the "
            "log's own index cannot be recomputed from what the log holds"
        )


# --------------------------------------------------------------------------
# Replay: a miss aborts, and issues nothing
# --------------------------------------------------------------------------


def test_replay_serves_a_recorded_response(tmp_path: Path) -> None:
    path = tmp_path / "run.jsonl"
    RecordingTransport(_Spy(), RunLogWriter(path, _header())).send(_request())
    replay = load_replay_transport(path, _header())
    assert replay.send(_request()).text == _response().text


def test_replay_on_a_missing_hash_aborts_and_issues_no_live_call(tmp_path: Path) -> None:
    """Asserted by a transport spy: the spy is not wired in at all, which is
    the strongest form of "issued no call" available -- there is nothing for a
    fallback to reach."""
    path = tmp_path / "run.jsonl"
    RecordingTransport(_Spy(), RunLogWriter(path, _header())).send(_request())
    replay = load_replay_transport(path, _header())
    with pytest.raises(ReplayCacheMissError) as excinfo:
        replay.send(_request(prompt="a prompt that was never recorded"))
    assert excinfo.value.request_hash in str(excinfo.value)


def test_replay_distinguishes_repetitions_of_one_request(tmp_path: Path) -> None:
    """N byte-identical requests share a hash, so a lookup keyed on the hash
    alone would return the first answer N times -- reporting a flat verdict
    distribution from a log that recorded a varied one."""
    path = tmp_path / "run.jsonl"
    first = _response(text='{"verdict": "aligned", "rationale": "a", "citations": ["T1"]}')
    second = _response(text='{"verdict": "misaligned", "rationale": "b", "citations": ["T1"]}')
    transport = RecordingTransport(_Spy([first, second]), RunLogWriter(path, _header()))
    transport.send(_request(repetition=1))
    transport.send(_request(repetition=2))

    replay = load_replay_transport(path, _header())
    assert replay.send(_request(repetition=1)).text == first.text
    assert replay.send(_request(repetition=2)).text == second.text


# --------------------------------------------------------------------------
# Staleness: two inputs, because they move independently
# --------------------------------------------------------------------------


def test_a_log_recorded_under_a_different_rubric_version_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "run.jsonl"
    RecordingTransport(_Spy(), RunLogWriter(path, _header(rubric_version="1"))).send(_request())
    with pytest.raises(StaleReplayLogError) as excinfo:
        load_replay_transport(path, _header(rubric_version="2"))
    assert "rubric version" in str(excinfo.value)


def test_a_log_recorded_under_a_different_prompt_template_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "run.jsonl"
    RecordingTransport(_Spy(), RunLogWriter(path, _header())).send(_request())
    with pytest.raises(StaleReplayLogError) as excinfo:
        load_replay_transport(path, _header(prompt_template_hash="c" * 64))
    assert "prompt-template hash" in str(excinfo.value)


def test_allow_stale_replay_lets_a_stale_log_through(tmp_path: Path) -> None:
    """The criterion asks for both halves: it aborts, and it succeeds with the
    flag. A refusal with no override is a wall, and the flag is the deliberate
    decision that the difference does not matter for what you are doing."""
    path = tmp_path / "run.jsonl"
    RecordingTransport(_Spy(), RunLogWriter(path, _header())).send(_request())
    replay = load_replay_transport(path, _header(prompt_template_hash="c" * 64), allow_stale=True)
    assert replay.send(_request()).text == _response().text


def test_the_staleness_comparison_names_both_inputs_when_both_moved() -> None:
    """Two values because they come from two places and move independently.
    A single combined stamp would report "something changed" and leave the
    reader to find out what."""
    differences = stale_differences(
        _header(rubric_version="1", prompt_template_hash="a" * 64),
        _header(rubric_version="2", prompt_template_hash="c" * 64),
        allow_stale=False,
    )
    assert len(differences) == 2


def test_the_staleness_comparison_ignores_the_corpus_and_artifact_fields() -> None:
    """Recorded so a reader can see them, and deliberately not compared: a
    judged response depends on the prompt it was sent, and refusing on a corpus
    version that moved for an unrelated call would refuse on something that
    cannot have changed this request."""
    assert (
        stale_differences(
            _header(corpus_version="0.4.0", artifact_hash="b" * 64),
            _header(corpus_version="9.9.9", artifact_hash="d" * 64),
            allow_stale=False,
        )
        == ()
    )


# --------------------------------------------------------------------------
# The cost estimate refuses rather than reassures
# --------------------------------------------------------------------------


def test_an_unpriced_model_refuses_rather_than_estimating_zero() -> None:
    """The first draft returned `(0.0, 0.0)` for an unknown model, so a live
    run of any size reported `$0.00` -- in the one place this project puts a
    human gate."""
    with pytest.raises(UnpricedModelError):
        rates_for("claude-not-a-model")
    with pytest.raises(UnpricedModelError):
        estimate_cost_usd(
            model="claude-not-a-model", calls=1000, input_tokens_each=6000, output_tokens_each=500
        )


def test_every_supported_model_is_priced() -> None:
    """Otherwise a rubric entry the loader accepts produces a run nobody can
    cost, and the refusal above fires at the moment a human is being asked to
    agree to the spend."""
    for model in SUPPORTED_MODELS:
        rates_for(model)


def test_the_estimate_is_arithmetic_a_reader_can_recompute() -> None:
    """1,000 calls of 6,000 in and 500 out on Sonnet 5, at $2.00/$10.00 per
    million: 6M input tokens is $12.00 and 0.5M output tokens is $5.00."""
    cost = estimate_cost_usd(
        model="claude-sonnet-5", calls=1000, input_tokens_each=6000, output_tokens_each=500
    )
    assert cost == pytest.approx(17.00)


# --------------------------------------------------------------------------
# The declared transport posture
# --------------------------------------------------------------------------


def test_the_posture_constants_are_declared_rather_than_inherited() -> None:
    """The specification requires an explicit per-request timeout rather than
    the SDK's ten-minute default, a declared backoff maximum, and a streaming
    threshold. Asserted as bounds rather than as exact values: the numbers are
    a build decision and this is the property that they were decided."""
    assert 0 < REQUEST_TIMEOUT_SECONDS < 600, "the SDK default is 600s; this must be its own"
    assert MAX_TRANSPORT_ATTEMPTS >= 2, "a declared maximum of one is not a retry policy"
    assert BACKOFF_CEILING_SECONDS > 0
    assert STREAMING_THRESHOLD_TOKENS > 0
    assert len(PRICING_USD_PER_MTOK) >= len(SUPPORTED_MODELS)


def test_the_retry_window_outlasts_a_transient_overload() -> None:
    """How long the schedule survives, which is the quantity that matters.

    **`MAX_TRANSPORT_ATTEMPTS >= 2` is true of a policy that gives up in seven
    seconds**, and that is what the declared maximum meant until D145: four
    attempts on a 1-2-4 schedule is a window of seven seconds, guarding a live
    recording that runs for over an hour and costs about fourteen dollars.

    On 2026-09-11 an `overloaded_error` outlasted it and aborted a run at call
    575 of roughly 1,040 -- every one of those 575 having succeeded on its first
    attempt, so the run was healthy right up to the moment it was discarded. A
    529 is inside `status >= 500`, so `_is_transient` had classified it
    correctly; what failed was the schedule, and the attempt count is the wrong
    thing to have declared on its own.

    Asserted as the sum rather than as a count, so raising the ceiling or the
    base satisfies it as readily as adding an attempt. The bound is the property;
    which constants deliver it is a build decision.
    """
    delays = [backoff_delay(attempt) for attempt in range(1, MAX_TRANSPORT_ATTEMPTS)]
    window = sum(delays)
    assert window >= MIN_RETRY_WINDOW_SECONDS, (
        f"the backoff schedule adds up to {window:g}s, below the declared minimum of "
        f"{MIN_RETRY_WINDOW_SECONDS:g}s. A run of a thousand calls is an hour of wall clock "
        f"and a real bill; the schedule that guards it gives up in {window:g}s. Delays: {delays}"
    )


def test_the_pricing_table_cannot_be_mutated() -> None:
    """A `Final` mapping is a read-only view whose backing dict is mutable by
    anyone holding a reference. This is a tuple for that reason, and this is
    the assertion that keeps it one."""
    assert isinstance(PRICING_USD_PER_MTOK, tuple)
    with pytest.raises(TypeError):
        PRICING_USD_PER_MTOK[0] = ("x", 1.0, 1.0)  # type: ignore[index]


def test_streaming_is_chosen_by_the_declared_threshold() -> None:
    below = GenerationConfig(
        model="claude-sonnet-5", max_tokens=STREAMING_THRESHOLD_TOKENS - 1, effort="high"
    )
    at = GenerationConfig(
        model="claude-sonnet-5", max_tokens=STREAMING_THRESHOLD_TOKENS, effort="high"
    )
    assert not below.should_stream
    assert at.should_stream


# --------------------------------------------------------------------------
# The live path, through a stub client
# --------------------------------------------------------------------------


class _StubBlock:
    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text


class _StubUsage:
    def __init__(self, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class _StubMessage:
    """The subset of an SDK message the seam reads, and no more.

    Written out rather than mocked, so the fields this project depends on are
    visible in one place: a message the SDK stopped populating would break here
    with a readable failure instead of an attribute error deep in a mapping.
    """

    def __init__(
        self,
        *,
        text: str = '{"verdict": "aligned", "rationale": "ok", "citations": ["T1"]}',
        stop_reason: str = STOP_END_TURN,
        stop_details: object | None = None,
        model: str = "claude-sonnet-5",
    ) -> None:
        self.content = [_StubBlock(text)]
        self.stop_reason = stop_reason
        self.stop_details = stop_details
        self.model = model
        self.usage = _StubUsage(1234, 56)


class _StubDetails:
    def __init__(self, category: str | None, explanation: str | None) -> None:
        self.category = category
        self.explanation = explanation


def test_a_message_maps_onto_the_response_type() -> None:
    from harness.core.transport import _response_from_message

    response = _response_from_message(_StubMessage(), latency_ms=42, attempts=2)
    assert response.stop_reason == STOP_END_TURN
    assert response.input_tokens == 1234
    assert response.output_tokens == 56
    assert response.latency_ms == 42
    assert response.transport_attempts == 2
    assert response.model == "claude-sonnet-5"


def test_stop_details_are_read_only_on_a_refusal() -> None:
    """The API populates `stop_details` for `refusal` and sends null for every
    other stop reason, so an unguarded read is a crash waiting for the first
    declined request -- on a corpus that seeds prompt injection by design."""
    from harness.core.transport import _response_from_message

    refused = _response_from_message(
        _StubMessage(stop_reason=STOP_REFUSAL, stop_details=_StubDetails("cyber", "declined")),
        latency_ms=1,
        attempts=1,
    )
    assert refused.refused
    assert refused.stop_category == "cyber"
    assert refused.stop_explanation == "declined"

    # The same details object on a non-refusal is ignored rather than read: the
    # field is meaningless there, and copying it would put a category on a
    # response that was never declined.
    ordinary = _response_from_message(
        _StubMessage(stop_reason=STOP_END_TURN, stop_details=_StubDetails("cyber", "declined")),
        latency_ms=1,
        attempts=1,
    )
    assert ordinary.stop_category is None
    assert ordinary.stop_explanation is None


def test_a_truncated_response_is_marked_truncated_and_not_refused() -> None:
    from harness.core.transport import _response_from_message

    response = _response_from_message(
        _StubMessage(stop_reason=STOP_MAX_TOKENS, text="{ trunc"), latency_ms=1, attempts=1
    )
    assert response.truncated
    assert not response.refused


def test_the_sdk_accepts_every_parameter_the_seam_sends() -> None:
    """The half a stub cannot buy: that `anthropic` takes these argument names.

    Checked against the installed package's own signature rather than against a
    recollection of the API. `output_config` is the one most worth pinning --
    `effort` is nested inside it and not top-level, and a build that recalled
    otherwise would assemble a request that fails only when money is being
    spent.

    Asserted here rather than in prose, because a claim about a third-party
    package is exactly the claim that goes stale between two pins.
    """
    import inspect

    import anthropic

    sent = {"model", "max_tokens", "system", "messages", "thinking", "output_config"}
    accepted = set(inspect.signature(anthropic.resources.messages.Messages.create).parameters)
    assert sent <= accepted, f"the SDK does not accept: {sorted(sent - accepted)}"

    client_params = set(inspect.signature(anthropic.Anthropic.__init__).parameters)
    assert {"timeout", "max_retries"} <= client_params

    # Sampling parameters are removed on both models this project uses and
    # return a 400, so the seam never sends them. That they are absent from the
    # signature entirely is the strongest available form of the same fact.
    assert not ({"temperature", "top_p", "top_k"} & accepted)

    # `output_config` is the shape most likely to drift, and the one this
    # project verified rather than recalled: `effort` is nested INSIDE it, not
    # top-level, and `format` sits beside it. A build that remembered
    # otherwise would assemble a request that fails only when money is being
    # spent.
    from anthropic.types.output_config_param import OutputConfigParam

    assert {"effort", "format"} <= set(OutputConfigParam.__annotations__)


def test_the_replay_path_does_not_import_the_sdk() -> None:
    """D8's key-free claim, as a property of the import graph.

    Run in a subprocess, and it has to be: this suite imports `anthropic`
    elsewhere -- `test_the_sdk_accepts_every_parameter_the_seam_sends` needs
    the installed package's own signature -- so an in-process check would find
    it in `sys.modules` and report a failure that is an artifact of the test
    session rather than of the code.

    What this buys: a reader who clones this repository and runs the
    deterministic or replay tier never loads the SDK, never needs a credential,
    and cannot be surprised by an import-time side effect from a package they
    did not ask for. The `LiveTransport` constructor is where the import lives,
    so the property holds by construction and this asserts it stays that way.
    """
    import subprocess
    import sys

    program = (
        "import sys\n"
        "import harness.cli\n"
        "import harness.core.transport\n"
        "import harness.judge.engine\n"
        "import harness.judge.prompt\n"
        "assert 'anthropic' not in sys.modules, sorted(\n"
        "    m for m in sys.modules if m.startswith('anthropic')\n"
        ")\n"
        "print('clean')\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", program], capture_output=True, text=True, check=False
    )
    assert completed.returncode == 0, (
        "importing the replay path pulled in the Anthropic SDK:\n" + completed.stderr
    )
    assert "clean" in completed.stdout


# --------------------------------------------------------------------------
# The uncommitted .env, which is the route a key takes without being handled
# --------------------------------------------------------------------------


def _write_dotenv(tmp_path: Path, body: str) -> Path:
    path = tmp_path / DOTENV_FILENAME
    path.write_text(body, encoding="utf-8")
    # The parse is cached by resolved path, and pytest gives each test its own
    # tmp_path, so no test can read another's file. Cleared anyway: a cache
    # that survived between tests would make the order they run in matter.
    _DOTENV_CACHE.clear()
    return path


def test_a_dotenv_supplies_a_credential_the_environment_does_not_have(tmp_path: Path) -> None:
    """The specification's `tools & permissions` says credentials come "from
    the environment or an uncommitted `.env`", and only the first half existed
    until a live run needed the second. It is the route by which an operator
    supplies a key without it passing through anything that logs it."""
    _write_dotenv(tmp_path, "ANTHROPIC_API_KEY=sk-ant-fromfile-0123456789\n")
    env = credential_environment(tmp_path, environ={})
    assert env["ANTHROPIC_API_KEY"] == "sk-ant-fromfile-0123456789"


def test_an_exported_variable_wins_over_the_file(tmp_path: Path) -> None:
    """A key in the environment was put there for this invocation; a key in a
    file was put there once and may be a leftover. When they disagree, believe
    the more deliberate one."""
    _write_dotenv(tmp_path, "ANTHROPIC_API_KEY=sk-ant-fromfile-0123456789\n")
    env = credential_environment(tmp_path, environ={"ANTHROPIC_API_KEY": "sk-ant-exported-9876"})
    assert env["ANTHROPIC_API_KEY"] == "sk-ant-exported-9876"


def test_both_credential_values_are_scrubbed_when_the_two_disagree(tmp_path: Path) -> None:
    """The loser of that contest is still a secret. A scrubber that only knew
    the winning value would leave the other one in the log, which is the worse
    half of a disagreement nobody noticed.

    **The same variable name in both places, which is what "disagree" means.**
    This test used to put the file's key under `ANTHROPIC_AUTH_TOKEN` and the
    environment's under `ANTHROPIC_API_KEY` -- two names, nothing in contest,
    and both values survived a `setdefault` that discards a loser only when
    there is one. It was green against a neighbor of its own subject for as
    long as the `.env` route existed, and the property it names was false the
    whole time.
    """
    _write_dotenv(tmp_path, "ANTHROPIC_API_KEY=sk-ant-fromfile-0123456789\n")
    environ = {"ANTHROPIC_API_KEY": "sk-ant-exported-98765"}

    winner = credential_environment(tmp_path, environ=environ)["ANTHROPIC_API_KEY"]
    assert winner == "sk-ant-exported-98765", "the exported variable no longer wins"

    values = credential_values(tmp_path, environ=environ)
    assert set(values) == {"sk-ant-exported-98765", "sk-ant-fromfile-0123456789"}, (
        "the scrubber's population lost the value authentication discarded"
    )
    scrubbed = scrub_credentials("a sk-ant-exported-98765 b sk-ant-fromfile-0123456789 c", values)
    assert "sk-ant-exported-98765" not in scrubbed
    assert "sk-ant-fromfile-0123456789" not in scrubbed


def test_a_credential_that_contains_another_is_redacted_whole(tmp_path: Path) -> None:
    """Order matters, and the ordering rule is the reason it is written down.

    Redacting the shorter value first leaves the longer one's tail behind in
    the log, next to a redaction token that reads as though the job was done.
    """
    _write_dotenv(tmp_path, "ANTHROPIC_API_KEY=sk-ant-0123456789\n")
    values = credential_values(tmp_path, environ={"ANTHROPIC_AUTH_TOKEN": "sk-ant-0123456789-ext"})
    scrubbed = scrub_credentials("x sk-ant-0123456789-ext y", values)
    # Asserted as an exact string rather than as "the digits are gone". The
    # digits are gone either way -- the shorter value consumes them -- and what
    # survives a declaration-order scrub is the longer value's TAIL, sitting
    # beside a redaction token that reads as though the job was done. The
    # control gate caught this test asserting the neighbor rather than the
    # property, which is the shape it exists to find.
    assert scrubbed == f"x {REDACTION} y", f"a live tail survived: {scrubbed!r}"


def test_only_the_declared_credential_names_are_read_from_the_file(tmp_path: Path) -> None:
    """A loader that imported every key it found would be a configuration
    mechanism nobody asked for, and would widen what the scrubber has to reason
    about to whatever an operator put in the file."""
    _write_dotenv(
        tmp_path,
        "ANTHROPIC_API_KEY=sk-ant-fromfile-0123456789\n"
        "DATABASE_URL=postgres://someone:hunter2@example.invalid/db\n"
        "PATH=/nowhere\n",
    )
    values = read_dotenv(tmp_path / DOTENV_FILENAME)
    assert set(values) == {"ANTHROPIC_API_KEY"}


def test_the_file_reader_tolerates_the_shapes_a_hand_edited_file_takes(tmp_path: Path) -> None:
    """The alternative to tolerating them is an operator whose key is silently
    not found -- which presents as "live mode says I have no credential" with a
    file sitting right there that plainly does."""
    _write_dotenv(
        tmp_path,
        "# a comment\n"
        "\n"
        '  export ANTHROPIC_API_KEY="sk-ant-quoted-0123456789"  \n'
        "ANTHROPIC_AUTH_TOKEN='sk-ant-single-0123456789'\n",
    )
    values = read_dotenv(tmp_path / DOTENV_FILENAME)
    assert values["ANTHROPIC_API_KEY"] == "sk-ant-quoted-0123456789"
    assert values["ANTHROPIC_AUTH_TOKEN"] == "sk-ant-single-0123456789"


def test_reading_the_file_does_not_export_anything(tmp_path: Path) -> None:
    """A loader that exported the value would put it in the environment of
    every subprocess this process starts, which is a wider blast radius than
    the one thing that needs it."""
    _write_dotenv(tmp_path, "ANTHROPIC_API_KEY=sk-ant-fromfile-0123456789\n")
    credential_environment(tmp_path, environ={})
    assert os.environ.get("ANTHROPIC_API_KEY", "") != "sk-ant-fromfile-0123456789"


def test_a_missing_file_is_not_an_error(tmp_path: Path) -> None:
    """Replay is the default mode and runs with no credential at all, so an
    absent `.env` is the ordinary case rather than a failure."""
    _DOTENV_CACHE.clear()
    assert read_dotenv(tmp_path / DOTENV_FILENAME) == {}
    assert credential_environment(tmp_path, environ={}) == {}


def test_a_dotenv_credential_is_kept_out_of_the_run_log(tmp_path: Path) -> None:
    """The requirement does not care which route the key took. Asserted over a
    written file, driving the shipped writer, for a key that came from the
    file rather than from the environment."""
    secret = "sk-ant-fromfile-0123456789"
    _write_dotenv(tmp_path, f"ANTHROPIC_API_KEY={secret}\n")
    values = credential_values(tmp_path, environ={})

    path = tmp_path / "run.jsonl"
    transport = RecordingTransport(_Spy(), RunLogWriter(path, _header(), credentials=values))
    transport.send(_request(prompt=f"a transcript that somehow contains {secret}"))

    written = path.read_text(encoding="utf-8")
    assert secret not in written
    assert REDACTION in written


def test_the_dotenv_file_is_ignored_by_git() -> None:
    """This reads a file two independent mechanisms already keep out of
    history: the `.gitignore` entry required from the first commit, and the
    fail-closed pre-commit guard that blocks a populated one. Asserted here
    because the reader is what makes a real key likely to be there at all."""
    ignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert any(line.strip() == DOTENV_FILENAME for line in ignore.splitlines()), (
        f"{DOTENV_FILENAME} is not gitignored, and the credential reader now gives an "
        "operator a reason to create one"
    )


# --------------------------------------------------------------------------
# The posture is read from the client, not from a comment claiming it
# --------------------------------------------------------------------------


class _RecordingClient:
    """Stands in for `anthropic.Anthropic`, capturing how it was constructed."""

    last_kwargs: ClassVar[dict[str, Any]] = {}

    def __init__(self, **kwargs: Any) -> None:
        type(self).last_kwargs = dict(kwargs)
        self.messages = self


#: A real directory that holds no `.env`. Passed as `root` wherever a test
#: builds a transport, because `root` otherwise defaults to the working
#: directory -- which during a test run is this checkout, and on the machine a
#: live run is issued from this checkout has a real key sitting in it. A unit
#: test that reads the operator's own credential passes or fails according to
#: whose machine it is on.
NO_DOTENV: Final[Path] = REPO_ROOT / "src"


def _live_transport(monkeypatch: pytest.MonkeyPatch, **kwargs: Any) -> Any:
    """A `LiveTransport` built against a stub client and a fake credential.

    Patches the SDK's constructor rather than the module, because the import is
    deferred into `LiveTransport.__init__` and by then `anthropic` is already in
    `sys.modules` -- so the attribute is what the deferred import resolves.
    """
    import anthropic

    from harness.core.transport import LiveTransport

    monkeypatch.setattr(anthropic, "Anthropic", _RecordingClient)
    kwargs.setdefault("root", NO_DOTENV)
    return LiveTransport(environ={"ANTHROPIC_API_KEY": "sk-ant-fake-0123456789"}, **kwargs)


def test_a_live_transport_with_no_credential_in_reach_refuses(tmp_path: Path) -> None:
    """The requirement's first clause, driven rather than described.

    The only test that named `CredentialMissingError` constructed the exception
    and read its message; every `LiveTransport` the suite built was handed a
    fake key. So replacing the refusal with `if False:` left all 159 judged-tier
    tests green, and verifier criterion 18 -- "A live run requires a credential,
    prints an estimated call count and cost, and issues no call until confirmed"
    -- ticked on the two clauses that were covered.

    What the harness does without this: `anthropic.Anthropic(api_key="")`
    constructs, because the SDK refuses `None` and not an empty string, and the
    401 arrives one confirmation later. No money is spent and the requirement
    still says the harness requires a credential.

    Asserted through the constructor, so it also covers the deferred SDK
    import: the refusal has to come first, or a clone with no key would need
    `anthropic` installed to be told it has no key.
    """
    from harness.core.transport import LiveTransport

    _DOTENV_CACHE.clear()
    with pytest.raises(CredentialMissingError):
        LiveTransport(environ={}, root=tmp_path)


def test_the_credential_lookup_reads_both_routes_and_refuses_only_when_both_are_empty(
    tmp_path: Path,
) -> None:
    """The named function both callers ask. A refusal that fired when a `.env`
    key was present would send an operator looking for a key they had."""
    _write_dotenv(tmp_path, "ANTHROPIC_API_KEY=sk-ant-fromfile-0123456789\n")
    assert resolve_credential(tmp_path, environ={}) == (
        "ANTHROPIC_API_KEY",
        "sk-ant-fromfile-0123456789",
    )
    assert resolve_credential(tmp_path, environ={"ANTHROPIC_API_KEY": "sk-ant-exported-98765"}) == (
        "ANTHROPIC_API_KEY",
        "sk-ant-exported-98765",
    )
    _DOTENV_CACHE.clear()
    with pytest.raises(CredentialMissingError):
        resolve_credential(tmp_path / "empty", environ={})


def test_the_sdk_retry_count_is_zero_so_our_backoff_replaces_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The posture the specification requires this project to STATE, asserted.

    It was prose until 2026-09-09: D122 recorded that the backoff replaces the
    SDK's rather than wrapping it, the module docstring said so, and nothing
    read the value the client was actually built with. The SDK defaults to 2,
    so the failure mode is silent -- two retry mechanisms layered, multiplying
    the wall-clock cost of every failure across a run of a thousand calls, and
    making `transport_attempts` in the run log a number that describes one of
    the two.

    Read from the constructor call rather than from `client_options()` alone,
    because a function returning the right value and a client built from a
    different one are two different claims.
    """
    _live_transport(monkeypatch)
    assert _RecordingClient.last_kwargs["max_retries"] == SDK_RETRIES
    assert SDK_RETRIES == 0, "our backoff replaces the SDK's; a non-zero here wraps it instead"


def test_the_client_timeout_is_this_projects_own_and_not_the_sdks_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The other half of the same posture. Ten minutes is not a timeout so much
    as the absence of one, for a batch that cannot afford to discover a hung
    request ten minutes at a time."""
    _live_transport(monkeypatch)
    assert _RecordingClient.last_kwargs["timeout"] == REQUEST_TIMEOUT_SECONDS
    assert client_options() == {
        "timeout": REQUEST_TIMEOUT_SECONDS,
        "max_retries": SDK_RETRIES,
    }


def test_the_credential_is_passed_explicitly_rather_than_left_to_the_sdk(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A key that came from `.env` is deliberately NOT exported, so the SDK's
    own environment lookup would not find it. Passing it explicitly is what
    makes the `.env` route work at all."""
    _live_transport(monkeypatch)
    assert _RecordingClient.last_kwargs["api_key"] == "sk-ant-fake-0123456789"


def test_a_token_from_the_alternative_variable_travels_under_the_bearer_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`.env.example` offers `ANTHROPIC_AUTH_TOKEN` as an alternative, and until
    2026-09-09 a token supplied that way could not authenticate.

    The SDK sends `api_key` as `X-Api-Key` and `auth_token` as
    `Authorization: Bearer` -- read off two constructed clients, not inferred.
    Passing a bearer token as `api_key` puts it in the wrong header, so the
    documented route produced a 401 and no message saying why. A route that is
    documented and cannot work is worse than one that is not documented.
    """
    import anthropic

    from harness.core.transport import LiveTransport

    monkeypatch.setattr(anthropic, "Anthropic", _RecordingClient)
    LiveTransport(environ={"ANTHROPIC_AUTH_TOKEN": "sk-ant-bearer-0123456789"}, root=NO_DOTENV)
    assert _RecordingClient.last_kwargs.get("auth_token") == "sk-ant-bearer-0123456789"
    assert "api_key" not in _RecordingClient.last_kwargs, (
        "a bearer token was passed as api_key, which the SDK sends as X-Api-Key"
    )


# --------------------------------------------------------------------------
# The backoff schedule, asserted without a test that waits
# --------------------------------------------------------------------------


def test_the_backoff_schedule_is_exponential_from_the_declared_base() -> None:
    assert backoff_delay(1) == BACKOFF_BASE_SECONDS
    assert backoff_delay(2) == BACKOFF_BASE_SECONDS * 2
    assert backoff_delay(3) == BACKOFF_BASE_SECONDS * 4


def test_the_backoff_is_capped_at_the_declared_ceiling() -> None:
    """The half worth naming. Without a cap a long schedule waits minutes on a
    late attempt, which on a run of a thousand calls is the difference between
    a slow failure and a hung one."""
    assert backoff_delay(50) == BACKOFF_CEILING_SECONDS
    assert all(backoff_delay(a) <= BACKOFF_CEILING_SECONDS for a in range(1, 51))


def test_the_retry_loop_sleeps_the_declared_schedule_and_not_after_the_last_try(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The loop's sleeps, driven through an injected function.

    This is what the caveat said could not be asserted without a test that
    waits, and it was wrong: the sleeps are a *sequence of requested delays*,
    and a recorder captures them in no time at all. What was untestable was the
    passage of time, which is not the property anyone cares about.

    Two claims, and the second is the one a reader would not think to check:
    the delays follow `backoff_delay`, AND there is no sleep after the final
    attempt. A loop that slept before giving up would spend wall-clock to reach
    the same place.
    """
    slept: list[float] = []
    transport = _live_transport(monkeypatch, sleep=slept.append)

    def _always_fails(request: JudgeRequest) -> None:
        del request
        raise ConnectionError("the network is down")

    monkeypatch.setattr(transport, "_issue", _always_fails)
    monkeypatch.setattr(transport, "_is_transient", lambda _exc: True)

    with pytest.raises(TransientTransportError):
        transport.send(_request())

    expected = [backoff_delay(a) for a in range(1, MAX_TRANSPORT_ATTEMPTS)]
    assert slept == expected, f"slept {slept}, declared schedule is {expected}"
    assert len(slept) == MAX_TRANSPORT_ATTEMPTS - 1, (
        "the loop slept once per attempt, including after the last one"
    )


def test_a_call_that_succeeds_first_time_sleeps_not_at_all(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The control on the test above. A recorder that captured nothing would
    satisfy it whatever the loop did, so this is the case that must record
    zero for the right reason."""
    slept: list[float] = []
    transport = _live_transport(monkeypatch, sleep=slept.append)
    monkeypatch.setattr(transport, "_issue", lambda _request: _StubMessage())
    assert transport.send(_request()).stop_reason == STOP_END_TURN
    assert slept == []


def test_a_header_names_the_sessions_a_resumed_log_carries(tmp_path: Path) -> None:
    """D153's header field, in both directions.

    A log one session recorded writes no `resumed_from` at all, so every log
    recorded before resuming existed -- the committed reference log among them --
    is still exactly what a writer produces. A resumed log names its sessions,
    oldest first, and reads back with them.
    """
    from harness.core import transport

    single = _header(mode="live")
    assert "resumed_from" not in single.as_dict(), (
        "a single-session header grew a field, so every log recorded before resuming changed"
    )
    resumed = _header(mode="live", resumed_from=("2026-09-09T12:00:00Z", "2026-09-10T08:00:00Z"))
    path = tmp_path / "resumed.jsonl"
    transport.RunLogWriter(path, resumed)
    header, _ = transport.read_run_log(path)
    assert header.mode == "live"
    assert header.resumed_from == resumed.resumed_from


def test_a_header_carries_the_labels_manifest_a_held_out_run_names(tmp_path: Path) -> None:
    """D173's header key, in both directions, on `resumed_from`'s pattern.

    A header naming no manifest writes no `labels_manifest` at all, so every
    design-set log -- the committed reference log among them -- is still exactly
    what a writer produces. A held-out run's header names the commit that sealed
    its labels, and reads back with it. The value is invented.
    """
    from harness.core import transport

    design = _header(mode="live")
    assert "labels_manifest" not in design.as_dict(), (
        "a header naming no manifest grew a key, so every design-set log changed"
    )
    manifest = "0123456789abcdef" * 2 + "01234567"
    path = tmp_path / "held-out.jsonl"
    transport.RunLogWriter(path, _header(mode="live", labels_manifest=manifest))
    written = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    assert written.get("labels_manifest") == manifest, "the writer left the manifest out"
    header, _ = transport.read_run_log(path)
    assert header.labels_manifest == manifest, "the reader dropped the manifest"


def test_a_header_carries_the_rubric_a_held_out_run_judged_under(tmp_path: Path) -> None:
    """D183's header key, in both directions, on `labels_manifest`'s pattern.

    A header naming no rubric hash writes no `rubric_hash` at all, so every
    design-set log -- the committed reference log among them -- is still exactly
    what a writer produces. A held-out run's header names the rubric it judged
    under, and reads back with it. The value is invented.
    """
    from harness.core import transport

    design = _header(mode="live")
    assert "rubric_hash" not in design.as_dict(), (
        "a header naming no rubric hash grew a key, so every design-set log changed"
    )
    judged_under = "9f" * 32
    path = tmp_path / "held-out.jsonl"
    transport.RunLogWriter(path, _header(mode="live", rubric_hash=judged_under))
    written = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    assert written.get("rubric_hash") == judged_under, "the writer left the rubric hash out"
    header, _ = transport.read_run_log(path)
    assert header.rubric_hash == judged_under, "the reader dropped the rubric hash"


def test_the_rubric_check_would_notice_a_log_judged_under_another_rubric(tmp_path: Path) -> None:
    """A run and the log it serves answers from name the same rubric (D183).

    Compared whole, as the labels manifest is: another rubric, none where the run
    names one, and one where the run names none are all refused, and the refusal
    names both sides. Equal hashes pass, two naming none among them. The values are
    invented, and `rubric_version` is equal throughout, which is the point -- it
    does not move when an entry's text does.
    """
    path = tmp_path / "recorded.jsonl"
    frozen = "9f" * 32
    edited = "3c" * 32
    for logged, current in ((frozen, edited), ("", frozen), (frozen, "")):
        with pytest.raises(RubricHashMismatchError, match="rubric hash") as refused:
            check_rubric_hash(_header(rubric_hash=logged), _header(rubric_hash=current), path)
        message = str(refused.value)
        assert (logged[:16] or "none") in message, message
        assert (current[:16] or "none") in message, message
    check_rubric_hash(_header(rubric_hash=frozen), _header(rubric_hash=frozen), path)
    check_rubric_hash(_header(), _header(), path)


def test_the_manifest_check_would_notice_a_log_naming_other_labels(tmp_path: Path) -> None:
    """A run and the log it serves answers from name the same labels manifest (D173).

    Compared whole: another manifest, none where the run names one, and one where
    the run names none are all refused, and the refusal names both sides. Equal
    manifests pass, two naming none among them. The values are invented.
    """
    path = tmp_path / "recorded.jsonl"
    sealed = "0123456789abcdef" * 2 + "01234567"
    other = "fedcba9876543210" * 2 + "fedcba98"
    for logged, current in ((sealed, other), ("", sealed), (sealed, "")):
        with pytest.raises(LabelsManifestMismatchError, match="labels manifest") as refused:
            check_labels_manifest(
                _header(labels_manifest=logged), _header(labels_manifest=current), path
            )
        message = str(refused.value)
        assert (logged or "none") in message, message
        assert (current or "none") in message, message
    check_labels_manifest(_header(labels_manifest=sealed), _header(labels_manifest=sealed), path)
    check_labels_manifest(_header(), _header(), path)


def test_a_header_missing_a_field_is_refused_as_a_damaged_log(tmp_path: Path) -> None:
    """A header short one field is the third failure, not a miss and not staleness.

    It escaped as a raw `KeyError` and a traceback from every command that reads a
    log, which is exit 1 -- the code for a gate that failed, and therefore a finding
    about the agent -- rather than the refusal a damaged file gets (the phase-5
    audit's P5-16). It is D167's torn line one field over: the file is damaged, and
    re-recording on any other advice fixes nothing.
    """
    path = tmp_path / "run.jsonl"
    RecordingTransport(_Spy(), RunLogWriter(path, _header())).send(_request())
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    del rows[0]["artifact_hash"]
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8"
    )

    with pytest.raises(RunLogFormatError) as raised:
        read_run_log(path)
    assert "artifact_hash" in str(raised.value)
    assert not isinstance(raised.value, StaleReplayLogError | ReplayCacheMissError)
