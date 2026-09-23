"""`harness run --tier assert` -- the deterministic tier, end to end.

    uv run harness run --tier assert

**What the exit code means, and what it does not** (D105). This corpus is
seeded with defects by construction, so a gate firing over it is the tier
working rather than failing. The run exits non-zero when a gate fails, over
the design set as over any other -- a run that exited zero here would be
reporting the W11 fail-open, which is the defect the five-value status channel
exists to prevent. "Green" for the phase is agreement with the gold set, and
`tools/verify_phase2.py` is what asserts that; this command reports what the
gates make of the results and says so.

Exit codes:

    0  every entry's gate held
    1  at least one gate failed -- expected over the design set
    2  the run could not start: a rubric that does not load, a transcript the
       adapter refuses, a tier that does not exist yet
    3  the tier could not be completed: at least one result came back errored
       or unevaluable, so the pass rate behind every rate gate was computed
       over a population that is not the one the rubric names. Distinct from
       1 because a failed gate is a finding about the *agent* and this is a
       finding about the *run*, and reporting the second as the first is the
       fail-open the five-value status channel exists to prevent

**The deterministic tier imports no transport, and that is checkable.** The
judged tier arrived at P3 with the model seam, and `--tier judge` runs it:

    uv run harness run --tier judge --mode replay --run-log runs/<a log>.jsonl

Replay is the default mode, so behavior never depends on whether a credential
happens to be present and money is never spent by accident (D8). `--mode live`
prints an estimated call count and cost and requires confirmation before
issuing anything. The Anthropic SDK is imported inside `LiveTransport`, so a
deterministic or replay run never has it in the import graph at all.

The judged tier's exit codes are the deterministic tier's (D127): N repetitions
roll up to one verdict per call by modal vote, a rate gate below its threshold
exits 1, and a tier that could not be completed exits 3 (D134).
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from harness.agreement import (
    DESIGN_CAVEAT,
    HELD_OUT_CAVEAT,
    HELD_OUT_NOT_COMPUTED,
    AgreementError,
    Traces,
    check_held_out_labels,
    design_expected,
    held_out_expected,
    load_traces,
    readings_for,
    render_set,
    set_agreement,
)
from harness.checks import build_registry
from harness.core.artifact import build_payload, content_hash
from harness.core.context import CheckContext, build_context
from harness.core.engine import EntryRollup, RunReport, roll_up, run
from harness.core.events import TranscriptError
from harness.core.findings import Finding, FindingsError, load_findings
from harness.core.registry import Registry
from harness.core.result import Provenance, Status
from harness.core.rubric import (
    SYNTHESIS_CHECK,
    CheckTier,
    Rubric,
    RubricEntry,
    RubricError,
    load_rubric,
    rubric_hash,
)
from harness.core.severity import SeverityError, join, load_severity
from harness.core.transport import (
    DEFAULT_CALL_CEILING,
    MAX_TRANSPORT_ATTEMPTS,
    CeilingTransport,
    CredentialMissingError,
    RecordingTransport,
    ReplayTransport,
    ResumingTransport,
    RunLogEntry,
    RunLogHeader,
    RunLogWriter,
    StaleReplayLogError,
    Transport,
    TransportError,
    check_labels_manifest,
    check_rubric_hash,
    credential_values,
    estimate_cost_usd,
    load_replay_transport,
    read_run_log,
    recorded_answers,
    resolve_credential,
    resumable_answers,
    resumed_header,
    stale_differences,
)
from harness.corpus.policies import PolicyError, load_policies
from harness.corpus.text_adapter import parse_call
from harness.coverage import (
    DESIGN_COVERAGE_CAVEAT,
    HELD_OUT_COVERAGE_CAVEAT,
    HELD_OUT_COVERAGE_NOT_COMPUTED,
    RETIRED_MEANS,
    CoverageError,
    render_coverage,
    set_coverage,
)
from harness.heldout import HELDOUT_SET_FILE, declared_held_out_calls
from harness.inspector import UnreadableLogError, inspect_log
from harness.inspector import render as render_inspection
from harness.instance_severity import (
    Instance,
    SeverityPropertiesError,
    instance_for,
    load_properties,
)
from harness.instance_severity import render as render_severity
from harness.judge.engine import (
    JudgedRun,
    first_attempt_dimension_requests,
    judged_order,
    run_judged,
)
from harness.judge.prompt import (
    PromptError,
    PromptTemplate,
    absent_categories,
    load_template,
    render_prompt,
    response_schema,
)
from harness.judge.rollup import JudgedEntryRollup, outcome_text, roll_up_judged
from harness.report import render_report

_DEFAULT_RUBRIC: Final[str] = "rubric.yaml"
_DEFAULT_FINDINGS: Final[str] = "corpus/findings.yaml"
#: The design set's severity export, which `harness coverage` bands the design
#: findings by. The held-out set's is its own and is read from outside (D177).
_DEFAULT_SEVERITY: Final[str] = "corpus/findings.severity.json"
_DEFAULT_SEVERITY_PROPERTIES: Final[str] = "severity-properties.yaml"
#: The committed log `harness report` replays when none is named. A default
#: rather than a required flag, because the criterion is that a **fresh clone**
#: produces the report -- and a required path is a step between cloning and
#: reading, which is the friction replay mode exists to remove.
_DEFAULT_REFERENCE_LOG: Final[str] = "runs/reference-corpus-0.6.0.jsonl"
_DEFAULT_TRANSCRIPTS: Final[str] = "corpus/transcripts"
_DEFAULT_POLICIES: Final[str] = "corpus/policies"
_DEFAULT_CORPUS_VERSION: Final[str] = "corpus/CORPUS_VERSION"

#: The corpus's policy-retrieval tool. A corpus entity name, so it is an
#: argument rather than a constant in the seam -- and a flag here rather than a
#: literal at the call site, for the same reason.
_DEFAULT_POLICY_TOOL: Final[str] = "fetch_policy"

#: The prompt scaffold every judged dimension renders through, and the
#: directory a run log is written to. Both are read by name from the repository
#: root (D120), and both are flags rather than constants at the call site so an
#: adopter pointing the harness at their own corpus can point it at their own.
_DEFAULT_TEMPLATE: Final[str] = "prompts/judge-dimension.v1.md"
_DEFAULT_RUN_LOG_DIR: Final[str] = "runs"

#: The held-out set's call identifiers, read by name from the repository root
#: (D173). A judged run reading any call it declares is a held-out run, and a
#: held-out run needs `--labels-manifest`.
_HELDOUT_SET: Final[str] = HELDOUT_SET_FILE

#: The one shape `--labels-manifest` is checked for: a full commit SHA. The
#: held-out repository cannot be seen from here, and its gate checks the rest --
#: that the commit is the one that last touched its labels manifest before the
#: log was committed there.
_LABELS_MANIFEST_SHA: Final[re.Pattern[str]] = re.compile(r"[0-9a-f]{40}")

#: Characters per token, for the pre-flight estimate. **Measured against the
#: committed reference log rather than reasoned about**, which is the whole
#: history of this constant: it was 3.5, on the argument that English prose
#: runs about four and an estimate a reader approves should be the ceiling of
#: what they are agreeing to. Against 160 real calls the estimate came in
#: BELOW every recorded input count, on all sixteen calls, by 1.30 to 1.37 --
#: because these prompts are tagged identifiers, JSON and clause text rather
#: than prose. 2.4 puts the estimate above the worst recorded ratio with room,
#: and `test_the_preflight_estimate_brackets_what_the_real_run_recorded` fails
#: if a later corpus overruns it.
#:
#: A character count rather than `messages.count_tokens`, and the reason is the
#: requirement itself: the estimate is printed BEFORE confirmation, and
#: counting tokens is a network call. A pre-flight check that went to the API
#: to find out whether to go to the API would be issuing a call before the
#: human agreed to any -- which is the thing the confirmation exists to
#: prevent, arriving through the door marked "just an estimate".
_CHARS_PER_TOKEN: Final[float] = 2.4

#: Input tokens the **synthesis** entry carries beyond its rendered transcript,
#: because its prompt also holds the other six dimensions' results and those do
#: not exist until the run happens.
#:
#: **This was recorded as an accepted optimism and is now a measured ceiling.**
#: `judged_call_estimate` renders every prompt and counts characters, which is
#: exact for the six dimensions -- they sit at 2.57 to 2.73 characters per
#: recorded token against a divisor of 2.4, so the estimate brackets them. The
#: synthesis cannot be rendered ahead of the run at all, and estimating it from
#: the transcript alone put it at 1.41 to 1.63, **below every recorded count on
#: all sixteen calls**. That is the one direction an estimate must never be
#: wrong in: an operator approving a number smaller than the bill.
#:
#: Measured against the committed reference log, the shortfall ran 1,042 to
#: 1,562 tokens. 2048 is the next power of two above the worst of them, which is
#: about 31% of headroom -- chosen rather than fitted, on D137's rule that a
#: bound taken from a sample is a bound taken from the calls that happened to be
#: easy. `test_the_preflight_estimate_brackets_what_the_real_run_recorded` fails
#: when a corpus overruns it, which is what makes it a ceiling rather than a
#: remembered number.
_SYNTHESIS_INPUT_ALLOWANCE: Final[int] = 2048


def _repo_root(module_file: Path | None = None) -> Path:
    """Where a relative default path is resolved from.

    `parents[2]` of this file is the repository root for an editable install --
    `src/harness/cli.py`, up through `src/harness` and `src` -- and is nowhere
    near it for a wheel, where the same expression names the directory above
    `site-packages`. Every default then points outside any checkout, and the
    run fails naming a path the reader has never seen.

    So the package-relative answer is used only when it looks like this
    repository, and the working directory otherwise: an adopter running an
    installed `harness` against their own corpus gets paths relative to where
    they are standing, which is the only root that can be right for them.

    Takes the file so a test can drive the installed case without installing.
    """
    source = (module_file or Path(__file__)).resolve()
    if len(source.parents) > 2:
        candidate = source.parents[2]
        if (candidate / "rubric.yaml").is_file() and (candidate / "corpus").is_dir():
            return candidate
    return Path.cwd()


def _resolve(value: str, root: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def load_corpus(
    transcripts_dir: Path, policies_dir: Path, *, policy_tool: str, corpus_version: str, root: Path
) -> tuple[tuple[CheckContext, ...], str, int]:
    """Parse the corpus, build one context per call, and return the corpus digest.

    The artifact hash is computed from the same calls the run evaluates rather
    than read from a file written earlier, so "this result was computed from
    that corpus" is true by construction instead of by sequencing.

    **It returns the digest rather than a `Provenance`.** It used to build
    `Provenance("", corpus_version, digest)` as a carrier for the caller to
    rebuild, and that half-filled value is why a blank stamp was constructible
    at all: the type could not refuse what one of its own callers depended on
    passing. Returning the value the function actually computed leaves
    `Provenance` free to require all three.
    """
    paths = sorted(transcripts_dir.glob("*.txt"))
    if not paths:
        raise FileNotFoundError(f"no transcripts found in {transcripts_dir}")
    calls = tuple(parse_call(path) for path in paths)
    unparsed = sum(len(call.unparsed) for call in calls)

    policies = load_policies(policies_dir)
    contexts = tuple(build_context(call, policies, policy_tool=policy_tool) for call in calls)
    digest = content_hash(build_payload(calls, corpus_version, root))
    return contexts, digest, unparsed


def _breakdown(rollups: tuple[EntryRollup, ...]) -> list[str]:
    """The per-check breakdown, one line per entry plus a header.

    Every status is printed beside the rate rather than folded into it. W21 is
    a tier where `threshold` was consumed by no logic and no rate was computed
    anywhere; printing the counts is what makes a reader able to tell a
    dimension that failed from one that never applied.
    """
    lines = [
        f"{'entry':<46} {'gate':<9} {'rate':>6} {'app':>4} {'n/a':>4} "
        f"{'unev':>5} {'err':>4} {'ref':>4}  result",
        "-" * 104,
    ]
    for rollup in rollups:
        rate = "--" if rollup.pass_rate is None else f"{rollup.pass_rate:.2f}"
        verdict = "FAIL" if rollup.gate_failed else "ok"
        lines.append(
            f"{rollup.entry.id:<46} {rollup.entry.gate.value:<9} {rate:>6} "
            f"{rollup.applicable:>4} {rollup.not_applicable:>4} {rollup.unevaluable:>5} "
            f"{rollup.errored:>4} {rollup.refused:>4}  {verdict}"
        )
    return lines


def confirm_spend(prompt: str) -> bool:
    """Ask before spending. Module-level so a test can replace it.

    A real prompt on stdin rather than a `--yes` flag, because the requirement
    is that a live run "requires confirmation before issuing any call", and a
    flag typed once into a shell history is not a confirmation of anything. A
    non-interactive stdin reads as "no": a live run started by a script that
    cannot answer should not spend money.
    """
    try:
        answer = input(prompt)
    except (EOFError, KeyboardInterrupt):
        return False
    return answer.strip().lower() in {"y", "yes"}


@dataclass(frozen=True, slots=True)
class JudgedEntryEstimate:
    """One judged entry's share of a live run, worked out before any call is issued."""

    entry_id: str
    model: str
    calls: int
    input_tokens_each: int
    max_tokens: int

    def ceiling_usd(self) -> float:
        """The most these calls can cost: every answer at the entry's `max_tokens`."""
        return estimate_cost_usd(
            model=self.model,
            calls=self.calls,
            input_tokens_each=self.input_tokens_each,
            output_tokens_each=self.max_tokens,
        )


def judged_call_estimate(
    rubric: Rubric, contexts: Sequence[CheckContext], template: PromptTemplate
) -> tuple[int, float]:
    """How many judged calls a run will issue, and what they cost.

    The count is the product the requirement wants printed and nobody holds in
    their head: calls x judged entries x N, **less the calls each entry's
    precondition excludes**. Retries are deliberately not in it -- the estimate
    bounds the EXPECTED call count and the ceiling bounds the actual one. That
    distinction is why the live call ceiling moved into this phase alongside the
    estimate rather than staying at P6.

    The **synthesis** entry's rendered size is the transcript alone: its prompt
    also carries the other dimensions' results, which do not exist until the run
    happens. This under-stated that entry's input and was the one place the
    estimate was optimistic rather than a ceiling -- recorded as such, and left
    uncorrected on the grounds that the correction would be a guess at what a
    run has not produced yet.

    **That stopped being true once a run had produced it** (D142). The committed
    reference log measures the shortfall on every call, so
    `_SYNTHESIS_INPUT_ALLOWANCE` is added to that entry's per-call input: the
    same idiom as `_CHARS_PER_TOKEN` one field over, a constant taken from the
    log rather than from reasoning about prose, with a test that fails when a
    corpus overruns it.

    **The input side is measured, not assumed.** Every prompt is rendered and
    its characters counted, so the figure describes the run about to happen
    rather than a constant somebody typed. The first draft did use constants --
    6,000 input tokens and 500 output per call -- and they were wrong by about
    three and a half times against the shipped corpus, in the direction that
    makes a reader approve more spending than they were told. A number a human
    is asked to agree to should not be a guess when the thing it describes is
    sitting in memory.

    **The output side is the entry's own `max_tokens`**, which is the ceiling
    the model cannot exceed. Estimating a typical answer instead would be
    estimating; this is the most that can be spent, which is what an approval
    should be for. Adaptive thinking bills into that ceiling too, so a
    rationale-plus-citations answer will come in well under it.
    """
    estimates = judged_entry_estimates(rubric, contexts, template)
    calls = sum(estimate.calls for estimate in estimates)
    return calls, sum(estimate.ceiling_usd() for estimate in estimates)


def judged_entry_estimates(
    rubric: Rubric, contexts: Sequence[CheckContext], template: PromptTemplate
) -> tuple[JudgedEntryEstimate, ...]:
    """Each judged entry's calls and per-call input, which both printed figures price.

    Split out of `judged_call_estimate` so the ceiling and the expected figure
    beside it (D152) cannot count calls or measure input two different ways: they
    differ only in what each answer is assumed to cost.
    """
    estimates: list[JudgedEntryEstimate] = []
    for entry in rubric.for_tier(CheckTier.JUDGE):
        if entry.judge is None:  # pragma: no cover - the loader guarantees this
            continue
        # **Only the calls this entry applies to** (D132). A dimension whose
        # precondition excludes a call issues nothing for it, so counting it
        # would tell an operator they are about to spend money on a request the
        # run will not make -- wrong in the direction that makes an estimate
        # bigger than the bill, which is the safe direction and still wrong.
        applicable = [
            context
            for context in contexts
            if not absent_categories(
                context, entry.judge.applies_when_facts_present, entry_id=entry.id
            )
        ]
        if not applicable:
            continue
        characters = sum(_rendered_size(entry, context, template) for context in applicable)
        input_each = int(characters / len(applicable) / _CHARS_PER_TOKEN) + 1
        if entry.check == SYNTHESIS_CHECK:
            input_each += _SYNTHESIS_INPUT_ALLOWANCE
        estimates.append(
            JudgedEntryEstimate(
                entry_id=entry.id,
                model=entry.judge.model,
                calls=len(applicable) * entry.judge.repetitions,
                input_tokens_each=input_each,
                max_tokens=entry.judge.max_tokens,
            )
        )
    return tuple(estimates)


def _answer_lengths(entries: Sequence[RunLogEntry]) -> dict[str, int]:
    """Each judged entry's mean answer, in output tokens, over the first attempts in `entries`.

    **First attempts only**, because a retry is priced through its entry's retry
    share, at this length, rather than through a length of its own (D170).
    **Rounded up**, so a figure priced on these lengths is never below what those
    first attempts cost.
    """
    lengths: dict[str, list[int]] = {}
    for entry in entries:
        if entry.request.retry_index == 0:
            lengths.setdefault(entry.request.entry_id, []).append(entry.response.output_tokens)
    return {entry_id: math.ceil(sum(seen) / len(seen)) for entry_id, seen in lengths.items()}


def _retry_shares(entries: Sequence[RunLogEntry]) -> dict[str, float]:
    """Each judged entry's calls per first attempt in `entries`, informed retries included.

    **One plus retries over first attempts** (OB-33, D170). The synthesis spends
    informed retries in every recording, and a figure priced on first attempts alone
    left them to the input side's over-estimate, which covered them by luck of the
    divisor rather than by counting them.
    """
    first: dict[str, int] = {}
    retried: dict[str, int] = {}
    for entry in entries:
        counts = first if entry.request.retry_index == 0 else retried
        counts[entry.request.entry_id] = counts.get(entry.request.entry_id, 0) + 1
    return {entry_id: 1 + retried.get(entry_id, 0) / count for entry_id, count in first.items()}


def recorded_answer_lengths(log: Path) -> dict[str, int]:
    """Each judged entry's mean answer, in output tokens, over a log's first attempts."""
    _, entries = read_run_log(log)
    return _answer_lengths(entries)


def recorded_retry_shares(log: Path) -> dict[str, float]:
    """Each judged entry's calls per first attempt in a log, informed retries included."""
    _, entries = read_run_log(log)
    return _retry_shares(entries)


def expected_cost_usd(
    estimates: Sequence[JudgedEntryEstimate],
    answer_lengths: Mapping[str, int],
    retry_shares: Mapping[str, float] | None = None,
) -> tuple[float, tuple[str, ...]]:
    """What a run is expected to cost, and the entries priced at their ceiling instead.

    An entry the recorded run never exercised has no answer length, and inventing
    one would be the constant this estimate's first draft was. It is priced at its
    ceiling, which keeps the figure safe, and returned by name, so the line an
    operator reads can say which part of it is a bound rather than a prediction.

    **Each entry's calls are multiplied by its retry share** (OB-33, D170), so the
    informed retries the recorded run made are priced. A retry is priced at its
    entry's first-attempt size, though it also carries the rejected answer and the
    valid identifiers. With no shares given, nothing retries.
    """
    cost = 0.0
    unrecorded: list[str] = []
    for estimate in estimates:
        length = answer_lengths.get(estimate.entry_id)
        if length is None:
            unrecorded.append(estimate.entry_id)
            cost += estimate.ceiling_usd()
            continue
        share = 1.0 if retry_shares is None else retry_shares.get(estimate.entry_id, 1.0)
        cost += share * estimate_cost_usd(
            model=estimate.model,
            calls=estimate.calls,
            input_tokens_each=estimate.input_tokens_each,
            output_tokens_each=length,
        )
    return cost, tuple(unrecorded)


def _expected_line(
    estimates: Sequence[JudgedEntryEstimate], log: Path, current: RunLogHeader
) -> str:
    """The figure printed beside the ceiling, or the reason there is none (D152).

    **Retries are priced and a stale log is named** (OB-33, D170). Each entry's
    calls are multiplied by the retry share `log` recorded for it, and every share
    above one is printed. A log recorded under another rubric version or prompt
    template still prices the figure, its lengths being the only ones there are,
    and a second line names what differs the way replay names it, so an operator
    approving spend sees that the prediction describes another state.
    """
    if not log.is_file():
        return (
            f"expected: not computed -- no recorded run at {log.name} to take answer lengths from"
        )
    try:
        recorded, entries = read_run_log(log)
        lengths = _answer_lengths(entries)
        shares = _retry_shares(entries)
    except (TransportError, OSError, ValueError, KeyError) as exc:
        return f"expected: not computed -- {log.name} could not be read ({exc})"
    cost, unrecorded = expected_cost_usd(estimates, lengths, shares)
    retried = [
        f"{entry_id} x{share:.2f}" for entry_id, share in sorted(shares.items()) if share > 1
    ]
    line = (
        f"expected: about ${cost:.2f}, with each entry answering at the mean length "
        f"{log.name} recorded for it and its calls multiplied by the retries recorded there: "
        + (", ".join(retried) if retried else "none")
    )
    if unrecorded:
        line += "; priced at the ceiling because nothing recorded them: " + ", ".join(unrecorded)
    stale = stale_differences(recorded, current, allow_stale=False)
    if stale:
        line += (
            f"\nexpected: {log.name} was recorded under another rubric or template, so the "
            "lengths and retries above may not describe this run -- " + "; ".join(stale)
        )
    return line


def _rendered_size(entry: RubricEntry, context: CheckContext, template: PromptTemplate) -> int:
    """Characters in one judged request: both messages and the declared schema."""
    spec = entry.judge
    assert spec is not None  # the caller filters on it
    rendered = render_prompt(
        template,
        context,
        entry_id=entry.id,
        question=spec.question,
        criteria=spec.criteria,
        scale=entry.scale,
        scale_definitions=spec.scale_definitions,
        requires_facts=spec.requires_facts,
    )
    return len(rendered.system) + len(rendered.user) + len(str(response_schema(entry.scale)))


def labels_manifest_problem(
    call_ids: Sequence[str], held_out_set: frozenset[str], manifest: str
) -> str:
    """Why this run and its `--labels-manifest` cannot go together, or "" when they can (D173).

    A run is held out when any call it reads is declared in `HELDOUT_SET`, and is
    held out whole or refused: a log holding both sets' answers would put design
    calls under a header naming held-out labels. Only a held-out run takes the
    flag, so a manifest in a header marks a held-out log and nothing else. Its
    shape is all that is checked.
    """
    held_out = [call_id for call_id in call_ids if call_id in held_out_set]
    if not held_out:
        if manifest:
            return (
                "--labels-manifest names the labels a held-out run is scored against, and no "
                "call this run reads is declared in HELDOUT_SET"
            )
        return ""
    undeclared = len(call_ids) - len(held_out)
    if undeclared:
        return (
            f"{len(held_out)} call(s) this run reads are declared in HELDOUT_SET and "
            f"{undeclared} are not; a held-out run log holds held-out calls alone, so run "
            "the two sets apart"
        )
    if not manifest:
        return (
            "every call this run reads is declared in HELDOUT_SET, so it needs "
            "--labels-manifest <sha>: the held-out repository's commit that last touched its "
            "labels manifest, which the run log's header names for that repository's gate"
        )
    if not _LABELS_MANIFEST_SHA.fullmatch(manifest):
        return (
            f"--labels-manifest {manifest!r} is not a full commit SHA: it takes 40 lowercase "
            "hex characters"
        )
    return ""


def held_out_paths_inside(args: argparse.Namespace, root: Path) -> list[str]:
    """The flags whose paths would put a held-out run inside this checkout (D174).

    A held-out run reads transcripts and a recorded log that must never be in this
    tree, and writes a log that must never be written into it: the default
    `--run-log-dir` is `runs/`, where `.gitignore` re-includes any
    `reference-*.jsonl`. So all five are refused before anything is written, and
    the absence check stays the backstop for whatever arrives by another route.

    **`--corpus-version-file` joins them at D182.** Its default resolves inside this
    checkout and holds the design corpus's version, so a held-out run left on the
    defaults stamped a version describing a corpus it never read into a header the
    held-out repository commits unmodified and never changes afterwards.
    `--policies` is deliberately not here: both sets read the same policy documents,
    and refusing it would ask that side to keep a copy that could drift from them.
    """
    checkout = root.resolve()
    inside: list[str] = []
    for flag, value in (
        ("--transcripts", args.transcripts),
        ("--run-log-dir", args.run_log_dir),
        ("--run-log", args.run_log),
        ("--resume", args.resume),
        ("--corpus-version-file", args.corpus_version_file),
    ):
        if value and _resolve(value, root).resolve().is_relative_to(checkout):
            inside.append(f"{flag} {value}")
    return inside


def build_judged_transport(
    args: argparse.Namespace,
    header: RunLogHeader,
    root: Path,
    recorded: Mapping[tuple[str, int], RunLogEntry] | None = None,
) -> tuple[Transport, Path, ResumingTransport | None, CeilingTransport]:
    """The seam, composed for the requested mode, and where it records.

    **Composition order carries meaning.** `Recording(Ceiling(inner))`: the
    ceiling refuses before the call, so a refused call has no run-log entry --
    rather than an entry describing a call nobody made.

    **A resumed run is `Recording(Resuming(Ceiling(live)))`** (D153). The
    ceiling moves inside the resume because a served answer is not a call: a
    ceiling that counted served answers would halt a resumed run before it had
    issued the calls it came to finish.

    Recording wraps **both** modes. A replay run writing its own log looks
    redundant until you ask what "every run-log entry carries a stop_reason;
    the count missing one is zero" is asserted over, and the answer has to be a
    log this run produced.

    **The resume and the ceiling come back with it** (OB-24, D168), so the
    command can say, when the run ends, how many answers were served from the
    resumed log and how many calls went out.
    """
    inner: Transport
    ceiling: CeilingTransport
    resuming: ResumingTransport | None = None
    if args.mode == "live":
        # Imported here, not at module scope. The deterministic tier and every
        # replay run must load this module without the SDK in the import graph
        # at all -- which is what makes "runs with no key" a fact about the
        # imports rather than a branch somebody has to take.
        from harness.core.transport import LiveTransport

        ceiling = CeilingTransport(LiveTransport(root=root), args.max_calls)
        if recorded is not None:
            resuming = ResumingTransport(recorded, ceiling)
        inner = ceiling if resuming is None else resuming
    else:
        # D173. Read through `recorded_answers` rather than `load_replay_transport`,
        # which drops the header this run's labels manifest is compared with.
        # `harness report` keeps that function: it writes no run log, so it has no
        # header for a manifest to go into, and takes no `--labels-manifest`.
        replay_log = _resolve(args.run_log, root)
        replayed, answers = recorded_answers(
            replay_log, header, allow_stale=args.allow_stale_replay
        )
        check_labels_manifest(replayed, header, replay_log)
        check_rubric_hash(replayed, header, replay_log)
        ceiling = CeilingTransport(ReplayTransport(answers), args.max_calls)
        inner = ceiling

    # **The writer is built last, and the order carries meaning.**
    # `RunLogWriter.__init__` truncates its file and writes the header, so a
    # transport that refuses -- no credential, a stale log, a log that does not
    # parse -- used to leave a header-only file in `runs/` describing a run
    # nobody made. It scrubs against every credential value in reach, including
    # one an exported variable overrode, so a key that came from `.env` is
    # still removed from every line it writes.
    log_dir = _resolve(args.run_log_dir, root)
    stamp = header.started_at.replace(":", "-")
    # **A held-out run's log is named for the gate that will admit it** (D184). The
    # header's `labels_manifest` is set on a held-out run and on no other, so the
    # name follows a value the header already carries rather than a second
    # determination that could disagree with it. What it replaces is a rename
    # performed by hand between writing a paid-for log and committing it, whose
    # omission is silent until that gate reads the path.
    prefix = "heldout-" if header.labels_manifest else ""
    out_path = log_dir / f"{prefix}{stamp}-{header.mode}.jsonl"
    writer = RunLogWriter(out_path, header, credentials=credential_values(root))
    return RecordingTransport(inner, writer), out_path, resuming, ceiling


def _judged_breakdown(judged: JudgedRun) -> list[str]:
    """Per entry and call: every repetition's verdict and status, individually.

    Printed before the roll-up, which is where N becomes a distribution and one
    modal verdict (D134). These lines are the repetitions that summary is
    computed from, so a reader can check the one against the other.
    """
    lines = [
        f"{'entry':<24} {'call':<10} {'rep':>4} {'status':<15} {'verdict':<18} "
        f"{'retry':>5}  stop_reason",
        "-" * 104,
    ]
    for outcome in judged.outcomes:
        result = outcome.result
        lines.append(
            f"{result.entry_id:<24} {result.call_id:<10} {outcome.repetition:>4} "
            f"{result.status.value:<15} {(result.verdict or '--'):<18} "
            f"{outcome.informed_retries:>5}  {outcome.stop_reason or '(none)'}"
        )
    return lines


def _judged_rollup_lines(rollups: Sequence[JudgedEntryRollup]) -> list[str]:
    """Per entry: the rate, every status beside it, and the per-call distribution.

    **The distribution is the row, not a summary of it.** "Report the verdict
    distribution across those repetitions rather than a single verdict" is the
    requirement, and a table printing one modal verdict per call would satisfy
    a reader's expectations and not the requirement.

    `refused` sits in the same row as the other three statuses and outside the
    rate, which is the pairing the criteria ask for: a rate whose denominator
    quietly excluded something is a rate a reader cannot reconstruct.

    A tie is marked rather than left to be inferred from the counts. The modal
    verdict resolves it toward a verdict the entry counts against its gate --
    the negative pole first (D160) -- and a reader looking at one verdict has no
    way to see that it was reached over a split.
    """
    lines = [
        f"{'entry':<32} {'gate':<6} {'rate':>6} {'app':>4} {'n/a':>4} "
        f"{'unev':>5} {'err':>4} {'ref':>4}  result",
        "-" * 104,
        "(app counts calls with a verdict; n/a, unev, err and ref count results)",
    ]
    for rollup in rollups:
        rate = "--" if rollup.pass_rate is None else f"{rollup.pass_rate:.2f}"
        verdict = "FAIL" if rollup.gate_failed else "ok"
        lines.append(
            f"{rollup.entry.id:<32} {rollup.entry.gate.value:<6} {rate:>6} "
            f"{rollup.applicable:>4} {rollup.result_count(Status.NOT_APPLICABLE):>4} "
            f"{rollup.result_count(Status.UNEVALUABLE):>5} "
            f"{rollup.result_count(Status.ERRORED):>4} "
            f"{rollup.result_count(Status.REFUSED):>4}  {verdict}"
        )
        for call in rollup.calls:
            lines.append(f"    {call.call_id:<10} {outcome_text(call)}")
        for call_id, identifier in rollup.unresolved_dimensions:
            lines.append(
                f"    DEFECT {call_id}: the synthesis rested on {identifier!r}, which "
                "produced no result for this call in this run"
            )
    return lines


def judged_command(args: argparse.Namespace, rubric: Rubric, root: Path) -> int:
    """The judged tier, in replay or live mode.

    Exit codes follow the deterministic command's meanings (D127): 0 when every
    judged gate held, 1 when a rate gate fell below its threshold (D134), 2 when
    the run could not be made, and 3 when it ran and could not be completed --
    an abort part-way, an `errored` or `unevaluable` result, or an entry that
    measured nothing.
    """
    entries = rubric.for_tier(CheckTier.JUDGE)
    if not entries:
        print(
            "the rubric declares no judged entry, so this tier would run nothing and "
            "print a clean table. Refused rather than reported as success.",
            file=sys.stderr,
        )
        return 2

    if args.mode == "replay" and not args.run_log:
        print(
            "replay mode needs a run log to replay: pass --run-log. There is no default, "
            "because a default would make the run depend on which file happened to be "
            "newest in the log directory.",
            file=sys.stderr,
        )
        return 2

    if args.resume and args.mode != "live":
        print(
            "--resume issues the calls a recorded run is missing, so it needs --mode live. "
            "Replay issues none, and serves a recorded run whole from --run-log.",
            file=sys.stderr,
        )
        return 2

    version_file = _resolve(args.corpus_version_file, root)
    try:
        corpus_version = version_file.read_text(encoding="utf-8").strip()
        contexts, digest, unparsed = load_corpus(
            _resolve(args.transcripts, root),
            _resolve(args.policies, root),
            policy_tool=args.policy_tool,
            corpus_version=corpus_version,
            root=root,
        )
        template = load_template(_resolve(args.template, root))
    except (TranscriptError, PolicyError, PromptError, OSError) as exc:
        print(f"run refused: {exc}", file=sys.stderr)
        return 2
    if unparsed:
        print(f"FAILED: {unparsed} unparsed line(s) in the corpus", file=sys.stderr)
        return 2

    try:
        provenance = Provenance(rubric.version, corpus_version, digest)
    except ValueError as exc:
        print(f"run refused: {exc}", file=sys.stderr)
        return 2

    # D173. Once the corpus has parsed, because the calls it holds decide whether
    # this is a held-out run, and before the credential, the estimate and the
    # confirmation: a held-out log written without a labels manifest is refused by
    # the held-out repository's gate, and refused there only after the spend.
    try:
        held_out_set = declared_held_out_calls(_resolve(_HELDOUT_SET, root))
    except OSError as exc:
        print(
            f"run refused: {exc}. A judged run reads HELDOUT_SET to tell whether its calls "
            "are held out, and so whether it needs --labels-manifest; a corpus with no "
            "held-out set gives the file no identifiers.",
            file=sys.stderr,
        )
        return 2
    manifest_problem = labels_manifest_problem(
        [context.call_id for context in contexts], held_out_set, args.labels_manifest
    )
    if manifest_problem:
        print(f"run refused: {manifest_problem}", file=sys.stderr)
        return 2
    held_out_run = any(context.call_id in held_out_set for context in contexts)
    inside = held_out_paths_inside(args, root) if held_out_run else []
    if inside:
        print(
            "run refused: a held-out run keeps its transcripts and run logs outside this "
            f"checkout, and {', '.join(inside)} would put it inside {root}; pass paths "
            "outside it (D174).",
            file=sys.stderr,
        )
        return 2

    header = RunLogHeader(
        rubric_version=rubric.version,
        prompt_template_hash=template.sha256,
        corpus_version=corpus_version,
        artifact_hash=digest,
        mode=args.mode,
        started_at=_now(),
        labels_manifest=args.labels_manifest,
        # Written on a held-out run and on no other, as the manifest beside it is
        # (D183). What it buys is the half `rubric_version` cannot: an entry's text
        # can move without that version moving, and the held-out labels are scored
        # against the rubric as it stood at the freeze.
        rubric_hash=rubric_hash(_resolve(args.rubric, root)) if args.labels_manifest else "",
    )

    recorded: Mapping[tuple[str, int], RunLogEntry] | None = None
    dropped = 0
    servable = 0
    if args.mode == "live":
        # First, and the order is the requirement's own: "SHALL require a
        # credential, SHALL print an estimated call count and cost, and SHALL
        # require confirmation". Asked after the estimate -- which is where it
        # used to be, inside the transport constructor -- an operator with no
        # key approves spend they cannot make, and is then refused.
        try:
            resolve_credential(root)
        except CredentialMissingError as exc:
            print(f"run refused: {exc}", file=sys.stderr)
            return 2
        if args.resume:
            # After the credential and before the estimate, for the reason the
            # credential check moved first: a resume log that has gone stale or
            # was never live is refused before anyone is asked to approve spend
            # (D153).
            resume_log = _resolve(args.resume, root)
            try:
                prior, recorded, dropped = resumable_answers(resume_log, header)
                header = resumed_header(prior, header, resume_log)
            except StaleReplayLogError as exc:
                # Replay's own message offers --allow-stale-replay, and a resume
                # has no such override: a log assembled across two states would
                # describe both under one header.
                print(
                    f"run refused: {resume_log.name} cannot be resumed:\n  "
                    + "\n  ".join(exc.differences)
                    + "\nA resumed log would describe two states under one header, so resuming "
                    "has no override for this. Record the run again.",
                    file=sys.stderr,
                )
                return 2
            except (TransportError, OSError, ValueError, KeyError) as exc:
                print(f"run refused: {exc}", file=sys.stderr)
                return 2
        try:
            estimates = judged_entry_estimates(rubric, contexts, template)
            calls = sum(estimate.calls for estimate in estimates)
            cost = sum(estimate.ceiling_usd() for estimate in estimates)
            dimension_requests = (
                ()
                if recorded is None
                else first_attempt_dimension_requests(rubric, contexts, template)
            )
        except (PromptError, TransportError) as exc:
            # An unknown fact renderer, or a model with no declared price.
            # Both abort naming their cause, which is the requirement -- and
            # both used to do it as an uncaught traceback exiting 1, which is
            # D114's code for "a gate failed" and therefore a finding about the
            # agent. A run that could not be made is 2.
            print(f"run refused: {exc}", file=sys.stderr)
            return 2
        if recorded is not None:
            servable = sum(
                1
                for request in dimension_requests
                if (request.request_hash, request.repetition) in recorded
            )
            # OB-24 (D168). A dimension's request is known before anything is sent,
            # so a log answering none of them is refused before spend is approved:
            # it would issue every call and write a header naming a session that
            # served nothing. The synthesis's requests are not known until the
            # dimensions answer, so they are counted when the run ends.
            if not servable:
                print(
                    f"run refused: {args.resume} holds an answer to none of the "
                    f"{len(dimension_requests)} dimension request(s) this run would send, "
                    "so a resume would issue every call and name a session that served "
                    "nothing. Run it live without --resume.",
                    file=sys.stderr,
                )
                return 2
        print(f"live mode: about {calls} judged call(s), estimated ${cost:.2f} at most")
        # OB-17 (D152). The figure above prices every answer at its entry's
        # ceiling, which is what an approval is for and far above what a run
        # spends. The line below is what it is expected to spend.
        print(_expected_line(estimates, _resolve(_DEFAULT_REFERENCE_LOG, root), header))
        if recorded is not None:
            print(
                f"resume: {len(recorded)} answer(s) recorded in {args.resume} are served "
                "without a call wherever the request is unchanged, so the figures above "
                "bound this run rather than describe it"
            )
            print(
                f"resume: {servable} of the {len(dimension_requests)} dimension request(s) "
                "this run sends are answered in that log; the synthesis's are counted "
                "when the run ends"
            )
            if dropped:
                # OB-28 (D167). A run that stopped mid-write leaves its last line torn,
                # and the resume reads past it rather than refusing the log it exists to
                # finish -- saying so, since the call that line belonged to is issued.
                print(
                    f"resume: the last line of {args.resume} was cut off mid-write and "
                    "was dropped, so the call it belonged to is issued again"
                )
        print(f"call ceiling: {args.max_calls}")
        # The multiplier is read from the constant rather than spelled out.
        # It said "four" and stayed saying it when D145 moved the retry budget
        # to seven, which is the shape this project keeps finding: a number in
        # prose beside the thing it describes, with nothing holding the two
        # together.
        print(
            "This estimate bounds the EXPECTED call count. Retries are not in it; the "
            "ceiling is what bounds the actual count -- and it counts calls, not HTTP "
            f"requests, so a transient failure can cost up to {MAX_TRANSPORT_ATTEMPTS} "
            "requests inside one."
        )
        if not confirm_spend("Issue these calls? [y/N] "):
            print("no confirmation given; no call was issued", file=sys.stderr)
            return 2

    try:
        transport, out_path, resuming, ceiling = build_judged_transport(
            args, header, root, recorded
        )
    except (TransportError, OSError) as exc:
        print(f"run refused: {exc}", file=sys.stderr)
        return 2

    try:
        judged = run_judged(rubric, contexts, provenance, template=template, transport=transport)
    except PromptError as exc:
        print(f"run refused: {exc}", file=sys.stderr)
        return 2

    print(f"tier: judge   mode: {args.mode}   calls: {len(contexts)}   entries: {len(entries)}")
    print(
        f"rubric {provenance.rubric_version} | corpus {provenance.corpus_version} | "
        f"artifact {provenance.artifact_hash[:16]} | template {template.sha256[:16]}"
    )
    print(f"run log: {out_path}")
    print()
    for line in _judged_breakdown(judged):
        print(line)
    print()

    by_status = {
        status.value: sum(1 for o in judged.outcomes if o.result.status is status)
        for status in Status
    }
    # **Two numbers, because they stopped being one.** A result that cost no
    # call is a real result -- the dimension does not apply to that call, and
    # saying so is the answer -- but it writes no run-log entry, so a reader
    # comparing `results` against the log would find them disagreeing and be
    # right to worry. `issued` is what the log is about. They were equal until
    # D125's precondition, and one number standing for both is how a reader
    # learns to stop checking.
    issued = sum(1 for outcome in judged.outcomes if outcome.repetition)
    print(f"results: {len(judged.outcomes)}   of which issued a call: {issued}")
    if resuming is not None:
        # OB-24 (D168). The pre-flight counted the dimensions only; these are the
        # run's own counts, the synthesis's included.
        print(
            f"resume: {resuming.served} answer(s) served from {args.resume} and "
            f"{ceiling.issued} call(s) issued"
        )
    print("   ".join(f"{name}: {count}" for name, count in by_status.items()))

    rollups = roll_up_judged(judged.outcomes, judged_order(rubric))
    print()
    for line in _judged_rollup_lines(rollups):
        print(line)

    if judged.aborted:
        print()
        print(f"RUN ABORTED: {judged.aborted}", file=sys.stderr)
        print(
            f"{len(judged.outcomes)} result(s) were obtained before it stopped, and every "
            f"one of them is in {out_path}.",
            file=sys.stderr,
        )
        return 3

    # Named apart from the deterministic tier's identical pair so a mutation
    # can address one of them. `if broken or unevaluable:` appeared twice in
    # this module, which made the two exits indistinguishable to a control --
    # and both were removable with `if False:` while the suite stayed green.
    judged_errored = by_status.get(Status.ERRORED.value, 0)
    judged_unevaluable = by_status.get(Status.UNEVALUABLE.value, 0)
    if judged_errored or judged_unevaluable:
        print()
        print(f"TIER INCOMPLETE: {judged_errored} errored, {judged_unevaluable} unevaluable")
        return 3

    # **`OB-14`, answered without a threshold.** A dimension whose every result
    # was refused measured nothing, and reporting that as a run is the W11
    # fail-open in the line a CI job reads. The obligation said the alternative
    # to exit 0 was a threshold and a threshold is a gate -- so the question
    # asked here is not *how many refusals are too many* but *was anything
    # measured*. A dimension with nine refusals and one verdict measured
    # something, badly, and its counts say so.
    #
    # A dimension that produced no verdict because it applied to no call is not
    # this, and `measured_nothing` says so: nothing failed, and the
    # precondition said so before a call was issued.
    silent = [rollup.entry.id for rollup in rollups if rollup.measured_nothing]
    if silent:
        print()
        print(f"TIER INCOMPLETE: {len(silent)} dimension(s) produced no verdict at all")
        for entry_id in silent:
            print(f"  {entry_id}")
        print(
            "A dimension whose every result was refused or errored measured nothing. Its "
            "counts are above; the exit code says the tier did not complete rather than "
            "that the agent behaved."
        )
        return 3

    failed = [rollup for rollup in rollups if rollup.gate_failed]
    if failed:
        print()
        print(f"GATES FAILED: {len(failed)} of {len(rollups)}")
        for rollup in failed:
            violating = sorted(call.call_id for call in rollup.calls if call.violated)
            print(f"  {rollup.entry.id} ({rollup.entry.gate.value}) on {', '.join(violating)}")
        print()
        print(
            "This corpus is seeded with defects by construction, so a gate firing over it "
            "is the tier working (D105). Agreement with the gold set is what the phase "
            "gate reads."
        )
        return 1

    print("every gate held")
    return 0


def report_command(args: argparse.Namespace, rubric: Rubric, root: Path) -> int:
    """Both tiers, rolled up and rendered, from a committed log and no credential.

    **Replay is not a mode here, it is the only route**, and that is the
    criterion: "`uv run harness report` on a fresh clone with no credential
    present produces the full report in replay mode and exits zero". A `--mode`
    flag would be a way for the deliverable to start depending on a key.

    Exit codes are the run command's and mean the same things (D114, D127): `2`
    the report could not be made, `0` it was. **Not `1` and not `3`** -- this
    command renders what a run found and is not itself a gate, so a report over
    a corpus seeded with defects exits zero having said so in every section.
    """
    registry = build_registry()
    version_file = _resolve(args.corpus_version_file, root)
    try:
        corpus_version = version_file.read_text(encoding="utf-8").strip()
        contexts, digest, unparsed = load_corpus(
            _resolve(args.transcripts, root),
            _resolve(args.policies, root),
            policy_tool=args.policy_tool,
            corpus_version=corpus_version,
            root=root,
        )
        template = load_template(_resolve(args.template, root))
        findings = {finding.id: finding for finding in load_findings(_resolve(args.findings, root))}
    except (TranscriptError, PolicyError, PromptError, FindingsError, OSError) as exc:
        print(f"report refused: {exc}", file=sys.stderr)
        return 2
    if unparsed:
        print(f"FAILED: {unparsed} unparsed line(s) in the corpus", file=sys.stderr)
        return 2

    # **A report over held-out calls is held-out output** (D185). Every call's
    # verdicts and both tiers' roll-ups are the judge's answers on those calls, and
    # this command had none of the refusals its neighbors carry: it reads no
    # `HELDOUT_SET`, checks no labels manifest, and wrote wherever `--out` pointed.
    # So D174's rule for a held-out run's paths, and D175's for agreement's held-out
    # section, reach here as one rule: stdout always, a file only outside this
    # checkout. The absence check is the backstop, and now reads a rendered report.
    if args.out:
        try:
            held_out_set = declared_held_out_calls(_resolve(_HELDOUT_SET, root))
        except OSError as exc:
            print(
                f"report refused: {exc}. A report reads HELDOUT_SET to tell whether the calls "
                "it renders are held out, and so whether it may be written inside this "
                "checkout.",
                file=sys.stderr,
            )
            return 2
        if any(context.call_id in held_out_set for context in contexts):
            destination = _resolve(args.out, root)
            if destination.resolve().is_relative_to(root.resolve()):
                print(
                    "report refused: a report over calls HELDOUT_SET declares carries the "
                    f"judge's verdicts on them, and --out {args.out} would write it inside "
                    f"{root}; write it outside this checkout, or read it on stdout (D185).",
                    file=sys.stderr,
                )
                return 2

    try:
        provenance = Provenance(rubric.version, corpus_version, digest)
    except ValueError as exc:
        print(f"report refused: {exc}", file=sys.stderr)
        return 2

    deterministic_report = run(rubric, contexts, provenance, registry, tier=CheckTier.ASSERT)
    deterministic = roll_up(deterministic_report, rubric)

    header = RunLogHeader(
        rubric_version=rubric.version,
        prompt_template_hash=template.sha256,
        corpus_version=corpus_version,
        artifact_hash=digest,
        mode="replay",
        started_at=_now(),
    )
    try:
        transport = load_replay_transport(
            _resolve(args.run_log, root), header, allow_stale=args.allow_stale_replay
        )
        judged = run_judged(rubric, contexts, provenance, template=template, transport=transport)
    except (TransportError, PromptError, OSError) as exc:
        print(f"report refused: {exc}", file=sys.stderr)
        return 2
    # **A report over a partial run is not a report**, and this is the one
    # place an abort is fatal rather than reported. The run command exits 3 and
    # prints what it obtained, because a run that stopped part-way still
    # produced results somebody has to see. A report is a document about a
    # complete run, and one rendered over half of it would carry rates computed
    # against denominators nobody chose.
    incomplete = judged.aborted
    if incomplete:
        print(f"report refused: {incomplete}", file=sys.stderr)
        return 2

    text = render_report(
        provenance=provenance,
        template_hash=template.sha256,
        mode="replay",
        rubric=rubric,
        findings=findings,
        report=deterministic_report,
        deterministic=deterministic,
        judged_outcomes=judged.outcomes,
        judged=roll_up_judged(judged.outcomes, judged_order(rubric)),
    )
    if args.out:
        destination = _resolve(args.out, root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        # `newline="\n"` so the bytes do not depend on the platform. A report
        # asserted byte-identical would otherwise pass on one operating system
        # and fail on another for a reason that is not a regression.
        destination.write_text(text, encoding="utf-8", newline="\n")
        print(f"report written to {destination}")
    else:
        sys.stdout.write(text)
    return 0


def _now() -> str:
    """UTC, second precision, `Z` suffix -- the project's timestamp standard."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_command(args: argparse.Namespace) -> int:
    root = _repo_root()
    registry: Registry = build_registry()

    try:
        tier = CheckTier(args.tier)
    except ValueError:
        print(
            f"unknown tier {args.tier!r}; declared tiers are "
            f"{', '.join(member.value for member in CheckTier)}",
            file=sys.stderr,
        )
        return 2
    try:
        rubric: Rubric = load_rubric(_resolve(args.rubric, root), registry.keys())
    except (RubricError, OSError) as exc:
        print(f"rubric refused: {exc}", file=sys.stderr)
        return 2

    if tier is CheckTier.JUDGE:
        # Refused by name through P2, when the seam did not exist and running
        # zero entries would have printed a clean table that looked like
        # success. It runs from P3. The rubric is loaded FIRST either way, so a
        # rubric that does not load is reported as a rubric problem in both
        # tiers rather than as a tier problem in one of them.
        return judged_command(args, rubric, root)

    version_file = _resolve(args.corpus_version_file, root)
    try:
        corpus_version = version_file.read_text(encoding="utf-8").strip()
        contexts, digest, unparsed = load_corpus(
            _resolve(args.transcripts, root),
            _resolve(args.policies, root),
            policy_tool=args.policy_tool,
            corpus_version=corpus_version,
            root=root,
        )
    except (TranscriptError, PolicyError, OSError) as exc:
        print(f"corpus refused: {exc}", file=sys.stderr)
        return 2

    if unparsed:
        print(f"FAILED: {unparsed} unparsed line(s) in the corpus", file=sys.stderr)
        return 2

    try:
        provenance = Provenance(rubric.version, corpus_version, digest)
    except ValueError as exc:
        # Exit 2, "could not start", rather than a traceback: an empty
        # CORPUS_VERSION file is a configuration mistake and reads like one.
        print(f"run refused: {exc}", file=sys.stderr)
        return 2
    report = run(rubric, contexts, provenance, registry, tier=tier)
    rollups = roll_up(report, rubric)

    print(f"tier: {tier.value}   calls: {len(contexts)}   entries: {len(rubric.for_tier(tier))}")
    print(
        f"rubric {provenance.rubric_version} | corpus {provenance.corpus_version} | "
        f"artifact {provenance.artifact_hash[:16]}"
    )
    print()
    for line in _breakdown(rollups):
        print(line)
    print()

    missing_stamp = sum(
        1
        for result in report.results
        if not (
            result.provenance.rubric_version
            and result.provenance.corpus_version
            and result.provenance.artifact_hash
        )
    )
    print(f"results: {len(report.results)}   missing a provenance value: {missing_stamp}")
    by_status = {
        status.value: sum(1 for result in report.results if result.status is status)
        for status in Status
    }
    print("   ".join(f"{name}: {count}" for name, count in by_status.items()))

    failed = [rollup for rollup in rollups if rollup.gate_failed]
    if failed:
        print()
        print(f"GATES FAILED: {len(failed)} of {len(rollups)}")
        for rollup in failed:
            calls = sorted(
                {
                    result.call_id
                    for result in report.for_entry(rollup.entry.id)
                    if result.verdict == rollup.entry.negative
                }
            )
            print(f"  {rollup.entry.id} ({rollup.entry.gate.value}) on {', '.join(calls)}")
        print()
        print(
            "This corpus is seeded with defects by construction, so a gate firing over it "
            "is the tier working (D105). Agreement with the gold set is what the phase "
            "gate reads; run tools/verify_phase2.py for that."
        )
        if by_status.get(Status.ERRORED.value, 0):
            print(f"and {by_status[Status.ERRORED.value]} result(s) errored, which no gate reads.")
        return 1

    # A check that throws on every call produced fifteen `errored` rows, no
    # failed gate, "every gate held" and exit 0. The status channel separates
    # the five states and the exit code collapsed four of them into "held" --
    # W11's shape one level up, in the line a CI job reads.
    #
    # `errored` is a broken check; `unevaluable` is a check that could not
    # reach a verdict. Neither is a gate failure and neither is success, so
    # they exit 3: a reader seeing 1 knows the tier found defects, and a
    # reader seeing 3 knows the tier did not run properly.
    broken = by_status.get(Status.ERRORED.value, 0)
    unevaluable = by_status.get(Status.UNEVALUABLE.value, 0)
    if broken or unevaluable:
        print()
        print(f"TIER INCOMPLETE: {broken} errored, {unevaluable} unevaluable")
        print(
            "No gate failed, and that is not the same as every gate holding: a result "
            "with no verdict was not compared against anything. Fix the check or the "
            "entry that produced it and run again."
        )
        return 3

    print("every gate held")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """The command line, built where a test can read it.

    Extracted from `main` at P3, when the judged tier added six flags with
    declared defaults. The requirement that an absent `--max-calls` applies a
    declared default ceiling rather than running uncapped is a claim about what
    the parser declares, and a test that rebuilt the parser to check it would
    be checking its own copy -- the shape D121 found in six controls, every one
    of them measuring nothing.
    """
    parser = argparse.ArgumentParser(prog="harness", description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)

    runner = subcommands.add_parser("run", help="evaluate a corpus against a rubric")
    runner.add_argument(
        "--tier",
        default=CheckTier.ASSERT.value,
        help="which tier to execute; only entries of that tier produce a result",
    )
    runner.add_argument("--rubric", default=_DEFAULT_RUBRIC)
    runner.add_argument("--transcripts", default=_DEFAULT_TRANSCRIPTS)
    runner.add_argument("--policies", default=_DEFAULT_POLICIES)
    runner.add_argument("--corpus-version-file", default=_DEFAULT_CORPUS_VERSION)
    runner.add_argument("--policy-tool", default=_DEFAULT_POLICY_TOOL)

    # The judged tier's flags. `--mode replay` is the default so that behavior
    # never depends on whether a credential happens to be in the environment,
    # and so money is never spent by accident (D8).
    runner.add_argument(
        "--mode",
        default="replay",
        choices=("replay", "live"),
        help="replay serves recorded responses and spends nothing; live issues calls",
    )
    runner.add_argument(
        "--run-log",
        default="",
        help="the recorded log replay reads. Required in replay mode for the judged tier",
    )
    runner.add_argument("--run-log-dir", default=_DEFAULT_RUN_LOG_DIR)
    runner.add_argument("--template", default=_DEFAULT_TEMPLATE)
    runner.add_argument(
        "--max-calls",
        type=int,
        default=DEFAULT_CALL_CEILING,
        help=f"call ceiling for this run; the declared default is {DEFAULT_CALL_CEILING}",
    )
    runner.add_argument(
        "--allow-stale-replay",
        action="store_true",
        help="replay against a log recorded under a different rubric or prompt template",
    )
    runner.add_argument(
        "--resume",
        default="",
        help=(
            "a live run log to resume: its recorded answers are served and only the calls "
            "it lacks are issued. Live mode only"
        ),
    )
    runner.add_argument(
        "--labels-manifest",
        default="",
        help=(
            "the held-out repository's commit that last touched its labels manifest, as 40 "
            "lowercase hex characters. Required on a judged run over calls HELDOUT_SET "
            "declares, and refused on any other (D173)"
        ),
    )

    reporter = subcommands.add_parser(
        "report", help="render the evaluation report for both audiences"
    )
    reporter.add_argument("--rubric", default=_DEFAULT_RUBRIC)
    reporter.add_argument("--transcripts", default=_DEFAULT_TRANSCRIPTS)
    reporter.add_argument("--policies", default=_DEFAULT_POLICIES)
    reporter.add_argument("--corpus-version-file", default=_DEFAULT_CORPUS_VERSION)
    reporter.add_argument("--policy-tool", default=_DEFAULT_POLICY_TOOL)
    reporter.add_argument("--findings", default=_DEFAULT_FINDINGS)
    reporter.add_argument("--template", default=_DEFAULT_TEMPLATE)
    # **Replay only, and there is no `--mode`.** The criterion is that a fresh
    # clone with no credential produces the full report and exits zero, so a
    # mode flag on this command would be a way to make the deliverable depend
    # on a key. A live run is `harness run --tier judge --mode live`, which
    # records a log this command then reads.
    reporter.add_argument(
        "--run-log",
        default=_DEFAULT_REFERENCE_LOG,
        help="the recorded judged log to replay; the committed reference log by default",
    )
    reporter.add_argument(
        "--allow-stale-replay",
        action="store_true",
        help="replay against a log recorded under a different rubric or prompt template",
    )
    reporter.add_argument(
        "--out",
        default="",
        help="write the report here instead of to stdout",
    )

    # **Replay only, and to stdout only** (D175). Agreement is read from recorded
    # runs, as the report is; and a held-out section is never written to a file,
    # because the one place a command would write it is wherever it was run from.
    agreement = subcommands.add_parser(
        "agreement",
        help="judge-versus-label agreement, design set and held-out set apart",
    )
    agreement.add_argument("--rubric", default=_DEFAULT_RUBRIC)
    agreement.add_argument("--template", default=_DEFAULT_TEMPLATE)
    agreement.add_argument("--transcripts", default=_DEFAULT_TRANSCRIPTS)
    agreement.add_argument("--policies", default=_DEFAULT_POLICIES)
    agreement.add_argument("--corpus-version-file", default=_DEFAULT_CORPUS_VERSION)
    agreement.add_argument("--policy-tool", default=_DEFAULT_POLICY_TOOL)
    agreement.add_argument("--findings", default=_DEFAULT_FINDINGS)
    agreement.add_argument(
        "--run-log",
        default=_DEFAULT_REFERENCE_LOG,
        help="the design set's recorded judged log; the committed reference log by default",
    )
    for flag, _ in _HELD_OUT_INPUTS:
        agreement.add_argument(
            flag, default="", help=f"{_HELD_OUT_HELP[flag]}; all five --held-out-* inputs, or none"
        )
    agreement.add_argument(
        "--held-out-policies",
        default="",
        help="the policies the held-out calls read; --policies when not given",
    )

    # **Stdout only**, as agreement is (D188): a held-out section names held-out
    # findings and their bands, which are labels, and the one place a command would
    # write a file is wherever it was run from.
    coverage = subcommands.add_parser(
        "coverage",
        help="findings retired per severity band, design set and held-out set apart",
    )
    coverage.add_argument("--rubric", default=_DEFAULT_RUBRIC)
    coverage.add_argument("--template", default=_DEFAULT_TEMPLATE)
    coverage.add_argument("--transcripts", default=_DEFAULT_TRANSCRIPTS)
    coverage.add_argument("--policies", default=_DEFAULT_POLICIES)
    coverage.add_argument("--corpus-version-file", default=_DEFAULT_CORPUS_VERSION)
    coverage.add_argument("--policy-tool", default=_DEFAULT_POLICY_TOOL)
    coverage.add_argument("--findings", default=_DEFAULT_FINDINGS)
    coverage.add_argument(
        "--severity",
        default=_DEFAULT_SEVERITY,
        help="the design set's severity export; the committed one by default",
    )
    coverage.add_argument(
        "--run-log",
        default=_DEFAULT_REFERENCE_LOG,
        help="the design set's recorded judged log; the committed reference log by default",
    )
    for flag, _ in _COVERAGE_HELD_OUT_INPUTS:
        coverage.add_argument(
            flag, default="", help=f"{_HELD_OUT_HELP[flag]}; all six --held-out-* inputs, or none"
        )
    coverage.add_argument(
        "--held-out-policies",
        default="",
        help="the policies the held-out calls read; --policies when not given",
    )

    # No `if args.command != "run"` guard here, and there was one. With
    # `required=True` on a subparser group, argparse refuses an unknown command
    # and a missing one before `parse_args` returns, exiting 2 with its own
    # usage message -- so the guard was unreachable, and an unreachable guard
    # reads as a tested path when nothing has run it.
    # `test_the_parser_refuses_a_command_that_is_not_run` covers the behavior
    # instead, which is the thing that has to keep working when a second
    # subcommand arrives.
    # **No rubric, no corpus and no `--out`** (D205): the inspector reads a run log
    # and nothing else, so it runs over a log recorded anywhere, and it prints
    # counts to stdout and writes no file.
    inspector = subcommands.add_parser(
        "inspect",
        help="invariants over a completed run log, as counts and proportions",
    )
    inspector.add_argument(
        "--run-log",
        default=_DEFAULT_REFERENCE_LOG,
        help="the run log to inspect; defaults to the committed reference log",
    )
    # **The design set only, and stdout only** (D206). It reads the ranked bands
    # beside its computed ones, and a held-out call's ranked band is a label, so
    # it takes no held-out input and the replay it shares refuses a call
    # `HELDOUT_SET` declares.
    severity = subcommands.add_parser(
        "severity",
        help="a band for every instance, computed in code from declared boolean properties",
    )
    severity.add_argument("--rubric", default=_DEFAULT_RUBRIC)
    severity.add_argument("--template", default=_DEFAULT_TEMPLATE)
    severity.add_argument("--transcripts", default=_DEFAULT_TRANSCRIPTS)
    severity.add_argument("--policies", default=_DEFAULT_POLICIES)
    severity.add_argument("--corpus-version-file", default=_DEFAULT_CORPUS_VERSION)
    severity.add_argument("--policy-tool", default=_DEFAULT_POLICY_TOOL)
    severity.add_argument("--findings", default=_DEFAULT_FINDINGS)
    severity.add_argument("--severity", default=_DEFAULT_SEVERITY)
    severity.add_argument("--properties", default=_DEFAULT_SEVERITY_PROPERTIES)
    severity.add_argument("--run-log", default=_DEFAULT_REFERENCE_LOG)
    return parser


#: The held-out set's five inputs, as (flag, attribute). All five or none: a
#: held-out section computed from some of them would score calls or labels the
#: others did not supply (D175).
_HELD_OUT_INPUTS: Final[tuple[tuple[str, str], ...]] = (
    ("--held-out-transcripts", "held_out_transcripts"),
    ("--held-out-corpus-version-file", "held_out_corpus_version_file"),
    ("--held-out-run-log", "held_out_run_log"),
    ("--held-out-findings", "held_out_findings"),
    ("--held-out-traces", "held_out_traces"),
)

#: The coverage report's held-out inputs: agreement's five, and the held-out set's
#: own severity export, which bands its findings (D177, D188).
_COVERAGE_HELD_OUT_INPUTS: Final[tuple[tuple[str, str], ...]] = (
    *_HELD_OUT_INPUTS,
    ("--held-out-severity", "held_out_severity"),
)

#: What each held-out input is, for the help of every command reading it.
_HELD_OUT_HELP: Final[Mapping[str, str]] = {
    "--held-out-transcripts": "the held-out transcripts, outside this checkout",
    "--held-out-corpus-version-file": "the held-out corpus version file",
    "--held-out-run-log": "the held-out judged run's log, whose header names a manifest",
    "--held-out-findings": "the held-out labels' findings.yaml",
    "--held-out-traces": "the held-out labels' traces.yaml",
    "--held-out-severity": "the held-out set's own severity export",
}


def _held_out_inputs_refusal(
    args: argparse.Namespace, inputs: Sequence[tuple[str, str]], root: Path
) -> str | None:
    """Why the held-out inputs cannot be read as given, or `None` (D174, D175).

    All of them or none: a held-out section computed from some would score calls or
    labels the others did not supply. And every one from outside this checkout, as a
    held-out run's paths are. Shared by agreement and the coverage report (D188), so
    the two refuse the same inputs in the same words.
    """
    given = [flag for flag, name in inputs if getattr(args, name)]
    if given and len(given) != len(inputs):
        missing = [flag for flag, name in inputs if not getattr(args, name)]
        return (
            "the held-out set is computed from every one of its inputs, and "
            f"{', '.join(missing)} {'is' if len(missing) == 1 else 'are'} missing"
        )
    repository = root.resolve()
    held_out_inside = [
        f"{flag} {getattr(args, name)}"
        for flag, name in inputs
        if getattr(args, name)
        and _resolve(getattr(args, name), root).resolve().is_relative_to(repository)
    ]
    if held_out_inside:
        return (
            "held-out inputs are read from outside this checkout, and "
            f"{', '.join(held_out_inside)} would read them from inside {root} (D174)"
        )
    return None


def _held_out_labels(
    args: argparse.Namespace, rubric: Rubric, root: Path, calls: Sequence[str]
) -> tuple[tuple[Finding, ...], Traces]:
    """The held-out findings and traces, refused where they break an invariant their
    validator states (D175). Shared by agreement and the coverage report (D188)."""
    findings = load_findings(_resolve(args.held_out_findings, root))
    traces = load_traces(_resolve(args.held_out_traces, root))
    check_held_out_labels(traces, rubric, findings, calls)
    return findings, traces


def _held_out_policies(args: argparse.Namespace) -> str:
    """The policies the held-out calls read: their own when `--held-out-policies` is
    given, the design set's otherwise (D175, D188).

    One function rather than the same expression at each command's call site, so the
    default has one place to be read and one control to hold it (the phase-5 audit's
    P5-6 found no test passed the flag on either command).
    """
    return str(args.held_out_policies or args.policies)


def _replayed_set(
    rubric: Rubric,
    root: Path,
    template: PromptTemplate,
    held_out_set: frozenset[str],
    *,
    transcripts: str,
    policies: str,
    corpus_version_file: str,
    policy_tool: str,
    run_log: str,
    rubric_file: str,
    held_out: bool,
) -> tuple[tuple[str, ...], RunReport, tuple[JudgedEntryRollup, ...]]:
    """One set's calls with both tiers' results: the deterministic tier run, and the
    judged tier served whole from `run_log` (D175).

    Refuses a set that is not wholly the side it is read as -- design calls
    `HELDOUT_SET` declares, or held-out calls it does not -- a held-out log naming no
    labels manifest (D173), a log recorded under another rubric version or template,
    and a replay that stopped part-way, whose agreement would cover fewer calls than
    the set holds.
    """
    corpus_version = _resolve(corpus_version_file, root).read_text(encoding="utf-8").strip()
    contexts, digest, unparsed = load_corpus(
        _resolve(transcripts, root),
        _resolve(policies, root),
        policy_tool=policy_tool,
        corpus_version=corpus_version,
        root=root,
    )
    if unparsed:
        raise AgreementError(f"{unparsed} unparsed line(s) in {transcripts}")
    calls = tuple(context.call_id for context in contexts)
    declared = sum(1 for call in calls if call in held_out_set)
    if held_out and declared != len(calls):
        raise AgreementError(
            f"{len(calls) - declared} of the {len(calls)} call(s) in {transcripts} are not "
            "declared in HELDOUT_SET, so they are not the held-out set"
        )
    if not held_out and declared:
        raise AgreementError(
            f"{declared} of the {len(calls)} call(s) in {transcripts} are declared in "
            "HELDOUT_SET, so the design section would score held-out calls"
        )
    provenance = Provenance(rubric.version, corpus_version, digest)
    deterministic = run(rubric, contexts, provenance, build_registry(), tier=CheckTier.ASSERT)
    header = RunLogHeader(
        rubric_version=rubric.version,
        prompt_template_hash=template.sha256,
        corpus_version=corpus_version,
        artifact_hash=digest,
        mode="replay",
        started_at=_now(),
    )
    log = _resolve(run_log, root)
    # **The staleness refusal offers a flag these commands do not take.** Replay's
    # message ends by offering `--allow-stale-replay`, which `harness agreement` and
    # `harness coverage` refuse as an unknown argument: they are measurements and have
    # no override, the same as the resume, whose message D168 rewrote for that reason
    # (the phase-5 audit's P5-16).
    try:
        logged, answers = recorded_answers(log, header)
    except StaleReplayLogError as exc:
        flag = "--held-out-run-log" if held_out else "--run-log"
        raise AgreementError(
            f"{log.name} was recorded against a different state:\n  "
            + "\n  ".join(exc.differences)
            + f"\nRe-record it, or point {flag} at a log recorded under this state. These "
            "commands read a log to measure it and have no override for this."
        ) from exc
    if held_out and not logged.labels_manifest:
        raise AgreementError(
            f"{log.name} names no labels manifest, and every held-out run's log names one (D173)"
        )
    # **The rubric hash is the claim the labels are scored against** (D186), and the two
    # commands that score them were the two that never read it: `check_rubric_hash` runs
    # on `harness run`'s replay and on a resume, so a held-out log judged under another
    # rubric, or under none, was replayed here and counted (the phase-5 audit's P5-5).
    # Refused with no override, as D186 chose, and only for a held-out set: a design run
    # writes no hash at all.
    if held_out:
        current = rubric_hash(_resolve(rubric_file, root))
        if logged.rubric_hash != current:
            raise AgreementError(
                f"{log.name} was judged under rubric hash {logged.rubric_hash[:16] or 'none'} "
                f"and this run reads {current[:16]}, so the held-out labels would be scored "
                "against answers given under another rubric (D186, D197)"
            )
    judged = run_judged(
        rubric, contexts, provenance, template=template, transport=ReplayTransport(answers)
    )
    stopped = judged.aborted
    if stopped:
        raise AgreementError(f"the replay of {log.name} stopped part-way: {stopped}")
    return calls, deterministic, roll_up_judged(judged.outcomes, judged_order(rubric))


def agreement_command(args: argparse.Namespace, rubric: Rubric, root: Path) -> int:
    """Judge-versus-label agreement: the design set's always, and the held-out set's once
    its labels are given (D175).

    Replay only, as `harness report` is, and for its reason: agreement is read from
    recorded runs, and a command able to issue calls would make the deliverable depend
    on a key. Exit `2` when refused and `0` when computed. Not a gate, so a design set
    seeded with defects exits zero having said so row by row.
    """
    refusal = _held_out_inputs_refusal(args, _HELD_OUT_INPUTS, root)
    if refusal is not None:
        print(f"agreement refused: {refusal}", file=sys.stderr)
        return 2
    try:
        held_out_set = declared_held_out_calls(_resolve(_HELDOUT_SET, root))
        template = load_template(_resolve(args.template, root))
        findings = {finding.id: finding for finding in load_findings(_resolve(args.findings, root))}
        calls, deterministic, judged = _replayed_set(
            rubric,
            root,
            template,
            held_out_set,
            transcripts=args.transcripts,
            policies=args.policies,
            corpus_version_file=args.corpus_version_file,
            policy_tool=args.policy_tool,
            run_log=args.run_log,
            rubric_file=args.rubric,
            held_out=False,
        )
        design = set_agreement(
            "design set", rubric, calls, deterministic, judged, design_expected(rubric, findings)
        )
        held_out_lines = [HELD_OUT_NOT_COMPUTED]
        if any(getattr(args, name) for _, name in _HELD_OUT_INPUTS):
            held_calls, held_deterministic, held_judged = _replayed_set(
                rubric,
                root,
                template,
                held_out_set,
                transcripts=args.held_out_transcripts,
                policies=_held_out_policies(args),
                corpus_version_file=args.held_out_corpus_version_file,
                policy_tool=args.policy_tool,
                run_log=args.held_out_run_log,
                rubric_file=args.rubric,
                held_out=True,
            )
            held_findings, traces = _held_out_labels(args, rubric, root, held_calls)
            held = set_agreement(
                "held-out set",
                rubric,
                held_calls,
                held_deterministic,
                held_judged,
                held_out_expected(traces, {finding.id: finding for finding in held_findings}),
            )
            held_out_lines = render_set(held, HELD_OUT_CAVEAT)
    except (
        AgreementError,
        TranscriptError,
        PolicyError,
        PromptError,
        FindingsError,
        TransportError,
        OSError,
        ValueError,
    ) as exc:
        print(f"agreement refused: {exc}", file=sys.stderr)
        return 2
    for line in render_set(design, DESIGN_CAVEAT):
        print(line)
    print()
    for line in held_out_lines:
        print(line)
    return 0


def coverage_command(args: argparse.Namespace, rubric: Rubric, root: Path) -> int:
    """Findings retired per severity band: the design set's always, and the held-out
    set's once its labels and its own severity file are given (D188).

    A finding is retired when an entry traced to it fired on its call, read from the
    same replays agreement reads, so the command refuses every input agreement
    refuses and, beside them, a severity file its loader or its join refuses. Each
    set is banded by its own file and printed apart (D177), and a held-out section
    goes to stdout alone, as agreement's does. Exit `2` when refused and `0` when
    computed: like agreement, not a gate.
    """
    refusal = _held_out_inputs_refusal(args, _COVERAGE_HELD_OUT_INPUTS, root)
    if refusal is not None:
        print(f"coverage refused: {refusal}", file=sys.stderr)
        return 2
    try:
        held_out_set = declared_held_out_calls(_resolve(_HELDOUT_SET, root))
        template = load_template(_resolve(args.template, root))
        design_calls, design_deterministic, design_judged = _replayed_set(
            rubric,
            root,
            template,
            held_out_set,
            transcripts=args.transcripts,
            policies=args.policies,
            corpus_version_file=args.corpus_version_file,
            policy_tool=args.policy_tool,
            run_log=args.run_log,
            rubric_file=args.rubric,
            held_out=False,
        )
        design_rollups = {rollup.entry.id: rollup for rollup in design_judged}
        design = set_coverage(
            "design set",
            rubric,
            load_findings(_resolve(args.findings, root)),
            load_severity(_resolve(args.severity, root)),
            {entry.id: entry.traces_to for entry in rubric.entries},
            {
                entry.id: readings_for(entry, design_deterministic, design_rollups)
                for entry in rubric.entries
            },
            design_calls,
        )
        held_out_lines = [HELD_OUT_COVERAGE_NOT_COMPUTED]
        if any(getattr(args, name) for _, name in _COVERAGE_HELD_OUT_INPUTS):
            held_calls, held_deterministic, held_judged = _replayed_set(
                rubric,
                root,
                template,
                held_out_set,
                transcripts=args.held_out_transcripts,
                policies=_held_out_policies(args),
                corpus_version_file=args.held_out_corpus_version_file,
                policy_tool=args.policy_tool,
                run_log=args.held_out_run_log,
                rubric_file=args.rubric,
                held_out=True,
            )
            labels, traces = _held_out_labels(args, rubric, root, held_calls)
            held_rollups = {rollup.entry.id: rollup for rollup in held_judged}
            held = set_coverage(
                "held-out set",
                rubric,
                labels,
                load_severity(_resolve(args.held_out_severity, root)),
                traces.traces,
                {
                    entry.id: readings_for(entry, held_deterministic, held_rollups)
                    for entry in rubric.entries
                },
                held_calls,
            )
            held_out_lines = render_coverage(held, HELD_OUT_COVERAGE_CAVEAT)
    except (
        AgreementError,
        CoverageError,
        SeverityError,
        TranscriptError,
        PolicyError,
        PromptError,
        FindingsError,
        TransportError,
        OSError,
        ValueError,
    ) as exc:
        print(f"coverage refused: {exc}", file=sys.stderr)
        return 2
    print(RETIRED_MEANS)
    print()
    for line in render_coverage(design, DESIGN_COVERAGE_CAVEAT):
        print(line)
    print()
    for line in held_out_lines:
        print(line)
    return 0


def inspect_command(args: argparse.Namespace, root: Path) -> int:
    """The log inspector (D205): metrics over one run log, never a score.

    **Exit `0` whenever the log could be read and `2` when it could not, and
    never `1`.** In this command's vocabulary `1` is a finding about the agent,
    and the inspector makes none: a log planted with a violation of every
    invariant exits `0` with each violation counted, because deciding that a
    count is too high is a threshold, and a threshold is a gate nobody chose.
    """
    try:
        inspection = inspect_log(_resolve(args.run_log, root), shown_as=args.run_log)
    except UnreadableLogError as exc:
        print(f"inspection refused: {exc}", file=sys.stderr)
        return 2
    for line in render_inspection(inspection):
        print(line)
    return 0


def severity_command(args: argparse.Namespace, rubric: Rubric, root: Path) -> int:
    """Per-instance severity over the design set (D206).

    Replay only and free of a key, as agreement and coverage are. An instance is
    an entry its tier's gate counts against a call, read through the function
    those two share, so the three cannot come to disagree about when an entry
    fired. Exit `2` when refused and `0` when computed; never a gate.
    """
    try:
        declared = load_properties(_resolve(args.properties, root), rubric)
        held_out_set = declared_held_out_calls(_resolve(_HELDOUT_SET, root))
        template = load_template(_resolve(args.template, root))
        findings = load_findings(_resolve(args.findings, root))
        ranked = {
            joined.finding.id: joined.severity.severity
            for joined in join(findings, load_severity(_resolve(args.severity, root)))
            if joined.severity is not None
        }
        calls, deterministic, judged = _replayed_set(
            rubric,
            root,
            template,
            held_out_set,
            transcripts=args.transcripts,
            policies=args.policies,
            corpus_version_file=args.corpus_version_file,
            policy_tool=args.policy_tool,
            run_log=args.run_log,
            rubric_file=args.rubric,
            held_out=False,
        )
    except (
        AgreementError,
        SeverityPropertiesError,
        SeverityError,
        FindingsError,
        TransportError,
        TranscriptError,
        OSError,
    ) as exc:
        print(f"severity refused: {exc}", file=sys.stderr)
        return 2

    parsed = {
        call.record.call_id: call
        for call in (
            parse_call(path) for path in sorted(_resolve(args.transcripts, root).glob("*.txt"))
        )
    }
    rollups = {rollup.entry.id: rollup for rollup in judged}
    by_id = {finding.id: finding for finding in findings}
    instances: list[Instance] = []
    for entry in rubric.entries:
        if entry.id in declared.excluded:
            continue
        readings = readings_for(entry, deterministic, rollups)
        evidence = {result.call_id: result.evidence for result in deterministic.for_entry(entry.id)}
        for call_id in calls:
            status, fired = readings[call_id]
            if status is not Status.APPLICABLE or not fired:
                continue
            instances.append(
                instance_for(
                    entry.id,
                    parsed[call_id],
                    evidence.get(call_id, ()),
                    declared,
                    [
                        ranked[finding_id]
                        for finding_id in entry.traces_to
                        if finding_id in ranked and by_id[finding_id].call_ref == call_id
                    ],
                )
            )
    for line in render_severity(instances, declared.excluded):
        print(line)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "inspect":
        return inspect_command(args, _repo_root())
    if args.command in ("report", "agreement", "coverage", "severity"):
        root = _repo_root()
        try:
            rubric: Rubric = load_rubric(_resolve(args.rubric, root), build_registry().keys())
        except (RubricError, OSError) as exc:
            # Loaded here rather than inside either command, so a rubric that
            # does not load is reported as a rubric problem by every command
            # that reads one -- which is the property `run_command` states in
            # its own comment about loading the rubric before the tier branch.
            print(f"rubric refused: {exc}", file=sys.stderr)
            return 2
        if args.command == "agreement":
            return agreement_command(args, rubric, root)
        if args.command == "coverage":
            return coverage_command(args, rubric, root)
        if args.command == "severity":
            return severity_command(args, rubric, root)
        return report_command(args, rubric, root)
    return run_command(args)


if __name__ == "__main__":
    raise SystemExit(main())
