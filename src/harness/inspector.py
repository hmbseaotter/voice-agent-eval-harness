"""The log inspector: invariants over a completed run log, emitted as metrics (D205).

**Metrics, never scores, and the distinction is the deliverable.** Every value
here is a count, or a proportion carried as its numerator and its denominator.
None is a verdict, a grade or a comparison with a threshold, and the command's
exit code says whether the log could be read, never what was found in it. A
number a reader has to interpret is a measurement; a PASS is somebody else's
interpretation arriving without its reasoning, and a threshold is a gate nobody
chose (D134). Each metric carries, beside its name, what it would mean if it
moved -- which is the part of a score worth keeping.

**Read from the log alone.** Nothing here imports the judged engine or its
citation validator. The retry metric is the reason: it asks whether the answers
a run *rejected* cited identifiers the prompt had in fact rendered, and an
inspector that asked the validator would be the validator agreeing with itself
-- the shape D121 found in six controls. So the citable universe is re-derived
from the logged prompt, by the one rule the prompt's own layout states: a
citable line begins with its tag.

**What the first reading found, recorded because it is what the instrument is
for.** Every informed retry in the committed reference log is the synthesis
citing a fact identifier, and the synthesis is given no fact lines to cite. Two
of those answers cited identifiers the prompt *does* show -- inside the other
dimensions' rationales, which quote their own citations -- so the prompt shows
the model an identifier and then refuses it. That is a prompt-design finding
about a frozen template, handed to the version-2 cycle rather than fixed here.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from harness.core.transport import (
    BLOB_FIELDS,
    REDACTION,
    GenerationConfig,
    JudgeRequest,
    blob_hash,
)

#: A citable line begins with its tag. Read from the prompt's layout, not from
#: the renderer: transcript and fact lines are rendered `[T<n>] ...` and
#: `[F<n>] ...` at the start of a line, and an identifier quoted mid-line inside
#: another dimension's rationale is shown to the model and is not citable.
_CITABLE_LINE: Final[re.Pattern[str]] = re.compile(r"^\[([TF]\d+)\]", re.MULTILINE)
_SHOWN_ANYWHERE: Final[re.Pattern[str]] = re.compile(r"\[([TF]\d+)\]")
_RESULTS_BLOCK: Final[re.Pattern[str]] = re.compile(
    r"<<<BEGIN UNTRUSTED DIMENSION RESULTS>>>\n(.*?)\n<<<END UNTRUSTED DIMENSION RESULTS>>>",
    re.DOTALL,
)
_LISTED_DIMENSION: Final[re.Pattern[str]] = re.compile(r"^([A-Za-z][\w-]*): ", re.MULTILINE)


class UnreadableLogError(Exception):
    """A file that is not a run log: no header, or a line that is not JSON.

    The one thing the inspector refuses. Everything short of it is counted.
    """


@dataclass(frozen=True, slots=True)
class Metric:
    """One measurement: a count, or a proportion as its two terms.

    There is deliberately no float and no status field. `numerator of
    denominator` is what is printed, and a reader who wants a percentage can
    divide; a reader handed a percentage cannot recover that it was 2 of 8.
    """

    name: str
    numerator: int
    denominator: int | None
    """`None` for a plain count, which has no population it is a share of."""
    meaning: str
    """What it would mean if this moved. Never a judgment of where it stands."""

    def rendered(self) -> str:
        if self.denominator is None:
            return f"{self.name}: {self.numerator}"
        return f"{self.name}: {self.numerator} of {self.denominator}"


@dataclass(frozen=True, slots=True)
class Inspection:
    path: str
    header: Mapping[str, Any]
    metrics: tuple[Metric, ...]

    def metric(self, name: str) -> Metric:
        for metric in self.metrics:
            if metric.name == name:
                return metric
        raise KeyError(name)


def _records(path: Path) -> list[dict[str, Any]]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise UnreadableLogError(f"{path}: {exc}") from exc
    records: list[dict[str, Any]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except ValueError as exc:
            raise UnreadableLogError(f"{path}:{number}: not a JSON record: {exc}") from exc
        if not isinstance(record, dict):
            raise UnreadableLogError(f"{path}:{number}: a run-log record is a JSON object")
        records.append(record)
    if not records or records[0].get("record") != "header":
        raise UnreadableLogError(f"{path}: the first record of a run log is its header")
    return records


def _answer(record: Mapping[str, Any]) -> dict[str, Any] | None:
    try:
        answer = json.loads(str(record.get("response_text", "")))
    except ValueError:
        return None
    return answer if isinstance(answer, dict) else None


def _strings(value: object) -> list[str] | None:
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return list(value)
    return None


def _retry_causes(
    attempt: Mapping[str, Any], prompt: str | None, schema: Mapping[str, Any] | None
) -> tuple[list[str], list[str] | None]:
    """Why the log shows this first attempt was rejected, and what it cited.

    Derived from the record and the prompt and schema it references, and from
    nothing else. An attempt none of these explains is returned with no cause,
    which is the reading that matters: a run that spent its retry on an answer
    whose citations and shape were both sound was corrected by a validator that
    disagreed with its own prompt (W1).
    """
    answer = _answer(attempt)
    if answer is None:
        return ["unreadable answer"], None
    causes: list[str] = []
    cited = _strings(answer.get("citations"))
    if cited is None:
        causes.append("unreadable answer")
    elif not cited:
        causes.append("cites nothing")
    elif prompt is not None:
        citable = set(_CITABLE_LINE.findall(prompt))
        if any(identifier not in citable for identifier in cited):
            causes.append("cites an identifier that is not a citable line")

    properties = (schema or {}).get("properties", {})
    scale = properties.get("verdict", {}).get("enum") if isinstance(properties, dict) else None
    if isinstance(scale, list) and answer.get("verdict") not in scale:
        causes.append("verdict outside the schema's scale")

    if isinstance(properties, dict) and "rests_on" in properties and prompt is not None:
        rests_on = _strings(answer.get("rests_on"))
        block = _RESULTS_BLOCK.search(prompt)
        listed = set(_LISTED_DIMENSION.findall(block.group(1))) if block else set()
        if rests_on is None or not rests_on:
            causes.append("rests on nothing")
        elif any(dimension not in listed for dimension in rests_on):
            causes.append("rests on a dimension the prompt does not list")
    return causes, cited


def inspect_log(path: Path, shown_as: str | None = None) -> Inspection:
    """Every invariant over one run log, as metrics.

    `shown_as` is the path as the caller gave it, printed in place of the
    resolved one so the output does not carry a machine's directory layout.
    """
    records = _records(path)
    header = records[0]

    blobs_before: dict[str, Any] = {}
    blob_total = blob_sound = 0
    unknown = 0
    calls: list[dict[str, Any]] = []
    resolved_refs: list[bool] = []
    resolved: list[dict[str, Any] | None] = []

    for record in records[1:]:
        kind = record.get("record")
        if kind == "blob":
            blob_total += 1
            digest, content = record.get("blob_hash"), record.get("content")
            if isinstance(digest, str):
                if blob_hash(content) == digest:
                    blob_sound += 1
                blobs_before[digest] = content
        elif kind == "call":
            calls.append(record)
            references = [record.get(f"{field}_ref") for field in BLOB_FIELDS]
            # Resolved against the blobs written **so far**, which is the
            # reader's one-pass rule: a reference to a blob further down the
            # file is one a truncation between the two would strand.
            found = all(isinstance(ref, str) and ref in blobs_before for ref in references)
            resolved_refs.append(found)
            resolved.append(
                {field: blobs_before[str(record[f"{field}_ref"])] for field in BLOB_FIELDS}
                if found
                else None
            )
        else:
            unknown += 1

    recomputed = 0
    for record, content in zip(calls, resolved, strict=True):
        if content is None:
            continue
        config = record.get("generation_config")
        if not isinstance(config, dict):
            continue
        try:
            request = JudgeRequest(
                entry_id=str(record.get("entry_id")),
                call_id=str(record.get("call_id")),
                repetition=int(record.get("repetition", 0)),
                retry_index=int(record.get("retry_index", 0)),
                system=str(content["system"]),
                prompt=str(content["prompt"]),
                schema=dict(content["schema"]),
                config=GenerationConfig(
                    model=str(config.get("model")),
                    max_tokens=int(config.get("max_tokens", 0)),
                    effort=str(config.get("effort")),
                ),
            )
        except (TypeError, ValueError):
            continue
        if request.request_hash == record.get("request_hash"):
            recomputed += 1

    groups: dict[tuple[str, str, int], list[tuple[dict[str, Any], dict[str, Any] | None]]] = (
        defaultdict(list)
    )
    for record, content in zip(calls, resolved, strict=True):
        key = (
            str(record.get("entry_id")),
            str(record.get("call_id")),
            int(record.get("repetition", 0)),
        )
        groups[key].append((record, content))

    triggers = citing = citable_only = shown_not_citable = 0
    causes: Counter[str] = Counter()
    unexplained = 0
    over_budget = orphan_retries = retry_groups = 0
    for members in groups.values():
        retries = [member for member in members if int(member[0].get("retry_index", 0)) > 0]
        firsts = [member for member in members if int(member[0].get("retry_index", 0)) == 0]
        if not retries:
            continue
        retry_groups += 1
        if len(retries) > 1:
            over_budget += 1
        if not firsts:
            orphan_retries += 1
            continue
        attempt, content = firsts[0]
        triggers += 1
        prompt = str(content["prompt"]) if content is not None else None
        schema = content["schema"] if content is not None else None
        reasons, cited = _retry_causes(
            attempt, prompt, schema if isinstance(schema, dict) else None
        )
        for cause in reasons:
            causes[cause] += 1
        if not reasons:
            unexplained += 1
        if cited and prompt is not None:
            citing += 1
            citable = set(_CITABLE_LINE.findall(prompt))
            shown = set(_SHOWN_ANYWHERE.findall(prompt))
            if all(identifier in citable for identifier in cited):
                citable_only += 1
            if any(identifier in shown - citable for identifier in cited):
                shown_not_citable += 1

    pairs: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in calls:
        if int(record.get("retry_index", 0)) == 0:
            pairs[(str(record.get("entry_id")), str(record.get("call_id")))].append(record)
    contiguous = one_hash = 0
    counts_by_entry: dict[str, set[int]] = defaultdict(set)
    for (entry_id, _), attempts in pairs.items():
        repetitions = sorted(int(attempt.get("repetition", 0)) for attempt in attempts)
        if repetitions == list(range(repetitions[0], repetitions[0] + len(repetitions))) and (
            repetitions[0] in (0, 1)
        ):
            contiguous += 1
        counts_by_entry[entry_id].add(len(repetitions))
        if len({attempt.get("request_hash") for attempt in attempts}) == 1:
            one_hash += 1
    even_entries = sum(1 for counts in counts_by_entry.values() if len(counts) == 1)

    stop_reasons = Counter(
        str(record["stop_reason"]) for record in calls if "stop_reason" in record
    )
    with_stop = sum(1 for record in calls if record.get("stop_reason"))
    redacted = sum(1 for record in calls if REDACTION in json.dumps(record))

    total = len(calls)
    metrics: list[Metric] = [
        Metric("call records", total, None, "how much was judged; every proportion below is of it"),
        Metric(
            "records of a type the log format does not define",
            unknown,
            None,
            "something other than this harness wrote to the file, or the format moved",
        ),
        Metric(
            "call records whose references resolve to a blob written earlier",
            sum(resolved_refs),
            total,
            "a reference pointing forward is one a truncation would strand, leaving results "
            "the log says it persisted unrecoverable",
        ),
        Metric(
            "blobs whose content re-hashes to the hash they are filed under",
            blob_sound,
            blob_total,
            "the log was edited after it was written, or a writer hashed before it scrubbed",
        ),
        Metric(
            "call records whose request hash recomputes from what they reference",
            recomputed,
            total,
            "what the log shows was sent is not what replay is keyed on, so a judged result "
            "could not be reproduced from this log",
        ),
        Metric(
            "entry-call pairs whose repetitions run unbroken from the first",
            contiguous,
            len(pairs),
            "a run aborted part-way or a resume stitched unevenly, so a distribution is over "
            "fewer answers than it says",
        ),
        Metric(
            "entries whose every call carries one repetition count",
            even_entries,
            len(counts_by_entry),
            "an entry's calls were judged a different number of times, so its rate weighs them "
            "unequally",
        ),
        Metric(
            "entry-call pairs whose repetitions share one request hash",
            one_hash,
            len(pairs),
            "a prompt varies between repetitions, so N stops measuring evaluator variance over "
            "a fixed input; it is also the share of a run prompt caching can serve (D204)",
        ),
        Metric("retry triggers", triggers, None, "how often an answer was rejected and corrected"),
        Metric(
            "retry triggers whose every cited identifier is a citable line of their prompt",
            citable_only,
            citing,
            "retries spent on answers whose citations were sound: another declared fault, or "
            "a validator rejecting what its own prompt rendered (W1)",
        ),
        Metric(
            "retry triggers citing an identifier their prompt shows outside its citable lines",
            shown_not_citable,
            citing,
            "the prompt shows the model an identifier and then refuses it, so the prompt is "
            "inducing the retries it spends",
        ),
        *[
            Metric(f"retry triggers: {cause}", count, triggers, "what this run's retries were for")
            for cause, count in sorted(causes.items())
        ],
        Metric(
            "retry triggers with no cause the log shows",
            unexplained,
            triggers,
            "an answer was rejected though its shape, scale and citations all read as sound",
        ),
        Metric(
            "retry groups holding more than one retry",
            over_budget,
            retry_groups,
            "the single informed retry the requirement allows is not what ran",
        ),
        Metric(
            "retries with no first attempt in the log",
            orphan_retries,
            retry_groups,
            "a correction was recorded for an answer the log does not hold",
        ),
        Metric(
            "call records carrying a stop reason",
            with_stop,
            total,
            "truncation and refusal stop being distinguishable from a validation failure",
        ),
        *[
            Metric(f"stop reason: {reason}", count, total, "truncation and refusal rates")
            for reason, count in sorted(stop_reasons.items())
        ],
        Metric(
            "call records containing the redaction marker",
            redacted,
            total,
            "a credential reached a prompt or an answer and was scrubbed on the way out",
        ),
    ]
    return Inspection(path=shown_as or str(path), header=header, metrics=tuple(metrics))


def render(inspection: Inspection) -> list[str]:
    """The inspection as lines: each metric, and under it what moving would mean."""
    header = inspection.header
    lines = [
        f"run log: {inspection.path}",
        f"  mode {header.get('mode')}, rubric version {header.get('rubric_version')}, "
        f"corpus version {header.get('corpus_version')}, "
        f"{len(header.get('resumed_from', []))} resumed session(s)",
        "  Counts and proportions only. Nothing below is a verdict, and this command exits 0 "
        "whenever the log could be read.",
        "",
    ]
    for metric in inspection.metrics:
        lines.append(metric.rendered())
        lines.append(f"    if it moves: {metric.meaning}")
    return lines


def metric_names(metrics: Sequence[Metric]) -> tuple[str, ...]:
    return tuple(metric.name for metric in metrics)
