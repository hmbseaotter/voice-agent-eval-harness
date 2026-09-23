# About this repository's history

This repository is a **snapshot**. Its first commit carries the project as it stood on the day it
was built; the working history that produced it — around three hundred commits, each with the
message this project's rules require — is kept in a private repository and is not published here.

**Why.** Early session documents named a directory path from the machine the work was done on, and
that path carried private context nothing in this project needs. Removing it from the working tree
is one commit; removing it from history means rewriting every commit after it, and this project's
evidence is pinned to commit identifiers: a frozen-rubric tag, a pinned constant compared against
it by test, a companion repository whose label commits cite the freeze commit by SHA, and several
dozen documents that cite commits as evidence. Rewriting would have invalidated citations that
another repository has already made and cannot re-make. A snapshot leaves all of that intact where
it is true, and publishes the work without the private detail.

**What that means for a reader.**

- **The narrative is here, in more detail than a log.** `specs/voice-agent-eval-harness.md` carries
  the changelog, and `specs/voice-agent-eval-harness.decisions.md` every fork taken, why, and what
  enforces it — over two hundred entries. `sessions/` holds the audits and the sweeps, each with a
  status banner a later session maintains, the handovers with a status line, and the briefs sessions
  were given, marked **SPENT** once the handover or report they name exists.
- **Commit identifiers cited in those documents refer to the private history.** A SHA in an audit
  banner or a decision entry is a real commit of this project; it is not resolvable in this
  repository's own log. **One citation is not left in that state.** The held-out repository's seal
  commit cites the freeze commit by SHA, which is how it proves the rubric was frozen before its
  labels existed, and `freeze-proof/` publishes that commit's own bytes together with its tag, the
  two trees reaching the frozen `rubric.yaml` and prompt template, and under `objects/` the whole
  frozen `src` subtree, so the frozen code itself can be run over them (D209, D210). It is
  recomputed rather than believed: `uv run python -m tools.verify_freeze_proof`, no history, no
  network, no clone.
- **The freeze pin names the freeze here, exactly as it does in the working repository.**
  `RUBRIC_FROZEN_V1` is 6d3a710, so `harness agreement` and `harness coverage` accept the real
  held-out labels in this tree — which they did not until 2026-09-22, when a sweep found that the
  pin had been re-pointed at this snapshot's own first commit to keep two tests green (D211).
  Those two tests need the freeze commit **in the log**, which no snapshot has, so here they skip
  and say why; the property they check is carried without git by
  `tests/test_freeze_proof.py`, against the published objects. This repository carries no tag,
  either: `rubric-frozen-v1` lives in the working history, and its object is in `freeze-proof/`.
- **Everything else runs as it is documented.** The suite, the phase verifiers, the control gate and
  the report snapshot need no credential and no network: `uv run pytest`, then the commands in the
  README's *Running it* section.

Built by `tools/make_public_snapshot.py` from the working repository at 57c971b.
