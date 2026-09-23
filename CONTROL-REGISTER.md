# Control register

A **control** is a test planted to prove that a fix is load-bearing: restore the defect it names and
the control fails. This file is the list of them, what each one claims, and whether that claim
survived being tested.

The question a row answers is not *does the control pass*. Every control in this tree passes, and
that is the trap. A control that passes proves its assertion holds; it does not prove the assertion
is **connected** to the thing it claims to measure. A control whose mutation lands where nothing
reads it is green forever and proves nothing, and a null result from an instrument that is not
connected is indistinguishable from a finding.

`sessions/HANDOVER-2026-09-08-control-connectivity.md` commissioned this register. The audit behind
it is D121.

## What makes this list recoverable

The controls are named in a convention: `..._would_notice_...`, `..._fires_on...`, `..._fires_when_...`,
`..._moves_the_verdict`, `..._would_catch_...`, `..._the_control_...`. `test_every_control_is_registered`
reads that convention out of the tree and requires every match to appear below, so a control added
under the idiom and not registered turns the suite red. That is the difference between this file and
the grep it replaces: the grep was a result, this is a rule.

**The convention is not the population.** A control named outside it is invisible to the rule, and
several are — the `Outside the idiom` section below lists ones found by looking for the *shape* of a
control (a test that mutates something and requires an outcome to move) rather than its name. That
sweep found roughly twice as many candidates as the idiom recovers. Rows may be added by hand for
anything the idiom misses; `test_every_registered_control_exists` holds the other direction, so a row
naming a test that does not exist is equally loud.

Rows are keyed on module and test name, not line numbers. The handover's own register used line
numbers, and two of them were stale before this session finished editing the files they pointed into.

## How a verdict was reached

The procedure, run identically each time:

1. Copy `src/` — or the repository, for a check that walks a tree — to a scratch directory outside it.
2. Restore the defect **into the copy**: the real defect, in the real module, as it was before the fix.
3. Run the control against the copy, `PYTHONPATH` pointing at it.
4. **Require the control to fail.** A control that stays green here is measuring nothing.
5. Restore, and require it to go green again. A control that cannot be driven both ways has been
   proven against nothing.

**Patch a copy on disk. Never `sys.modules`.** In-memory module injection silently does nothing here,
because `harness/checks/__init__.py` binds function objects at import time.

Most `connected` verdicts below come from running that procedure in bulk: each of the 9 commits in the
phase-2 remediation that touched `src/` was reverse-applied into a copy of `src/`, and the suite run
against it. A control that fails when its own defect is restored is connected, by demonstration.

**Two limits of that instrument, both real.**

- `git apply` **exits 0 while skipping every hunk** when it resolves paths against a repository other
  than the one the patch came from — and the scratch directory used here sits inside an unrelated git
  repository, so it did. A sweep built on it would have reported every control as noticing nothing,
  from a copy that was never mutated. The sweep uses `patch`, and refuses to run when the copy does
  not differ from `src/`. This is the failure mode the register exists to find, in the register's own
  tooling.
- A check that **walks `REPO_ROOT`** rather than importing `harness` cannot be reached by a
  `PYTHONPATH` copy at all. For those the whole repository is copied and the mutation goes into the copy.
- **`tools/verify_controls.py` could not see `src/` at all until it set `PYTHONPATH`.** `harness` is
  an editable install: a `.pth` appends the real repository's `src` to `sys.path`, so a copied tree
  imported the ORIGINAL modules. Measured: a bare `raise` planted in the copy's `checks/claims.py`
  changed nothing and the control passed. Every `src/`-side verdict below would have been reported as
  a finding against the control, from a mutation that never ran. It fails **closed** -- a spurious
  finding, not a spurious pass -- which is the right direction to fail, and it was still wrong.

## Verdicts

- **connected** — the defect was restored and the control failed. Named evidence below.
- **partial** — the control catches some of the modes it claims and is blind to others. Both halves measured.
- **disconnected** — the mutation never reaches the code the control names.
- **masked** — the mutation is real, but a second uncovered gap holds the verdict fixed either way.
- **fixture-proven** — the control exercises a stand-in rather than the shipped configuration.
- **not a control** — the naming idiom caught a consistency assertion. It restores no defect and
  requires no outcome to move, so `connected` is not a question that can be asked of it. What can be
  asked is whether it compares anything, and all three of these did not.
- **unaudited** — not settled by this pass. Silence is not a verdict, and these rows say so. **There
  are none left in the table above**; the phrase is kept because the next control added will be one.

## The register

| Control | Module | Verdict | Evidence |
|---|---|---|---|
| `test_the_control_character_sweep_would_notice_one` | `test_acceptance.py` | **partial, repaired** | Finding 1. Blind to the extension filter it named; repaired and driven red on both modes. |
| `test_the_completion_claim_check_fires_on_exactly_the_seeded_calls` | `test_claim_checks.py` | connected | Fails when `27bc78d` is reverted into a copied `src/`. |
| `test_the_blocking_state_check_fires_on_exactly_the_seeded_calls` | `test_claim_checks.py` | connected | Fails when `27bc78d` is reverted into a copied `src/`. |
| `test_the_terminal_retry_check_fires_on_exactly_the_seeded_calls` | `test_claim_checks.py` | connected | Fails when `27bc78d` is reverted into a copied `src/`. |
| `test_w2_the_control_turning_the_ordering_rule_off_passes_that_call` | `test_claim_checks.py` | connected | Fails when `27bc78d` is reverted into a copied `src/`. |
| `test_the_spy_would_notice_a_connection` | `test_cli.py` | connected, load-bearing | With the spy patching every route but recording nothing, the check passes and **only this control fires**. Re-derived by `control-mutations.yaml`. |
| `test_each_conduct_entry_fires_on_exactly_its_seeded_calls` | `test_conduct_checks.py` | connected | Fails when `3a9100d` is reverted, on `A-confirmation-requested-after-the-attempt`. |
| `test_every_traced_finding_is_on_a_call_the_entry_fires_on` | `test_conduct_checks.py` | not a control, floored | A consistency assertion between two declarations; it restores no defect. It had **no floor** and passed over an empty EXPECTED_FIRING while its neighbors in the same file carried floors. Floored, driven red, re-derived by `control-mutations.yaml`. |
| `test_the_month_list_is_read_by_position_and_rotating_it_moves_the_verdict` | `test_conduct_checks.py` | connected | Fails when `3a9100d` is reverted — a targeted revert that broke 10 tests, not a broad one. |
| `test_the_leak_scan_would_notice_a_turn_that_was_in_the_corpus` | `test_context_seam.py` | **disconnected, repaired** | Finding 3. A tautology that never called the scan. Repaired, and re-derived every run by `control-mutations.yaml`. |
| `test_the_event_scoped_check_fires_on_a_door_time_its_titles_agree_with` | `test_corpus_hygiene.py` | connected, load-bearing | With the event-scoped comparison reporting nothing, the check passes and **only this control fires**. Re-derived by `control-mutations.yaml`. |
| `test_the_anchor_check_would_notice_a_moved_event` | `test_corpus_hygiene.py` | **disconnected, repaired** | Finding 2. Never executed the comparison it controls; repaired and driven red. |
| `test_the_measurement_scan_fires_on_an_undated_unbound_number` | `test_corpus_hygiene.py` | connected | Drives the shipped marker: with it matching nothing, check and control both fail. Re-derived by `control-mutations.yaml`. |
| `test_the_matched_by_check_fires_when_the_register_names_the_wrong_call` | `test_corpus_hygiene.py` | **disconnected, repaired** | Finding 5. Ran its own `re.findall` and its own `!=`, so it never drove the check's comparison. Re-derived by `control-mutations.yaml`. |
| `test_the_escalation_convention_check_fires_on_the_field_that_was_got_wrong` | `test_corpus_hygiene.py` | **disconnected, repaired** | Finding 6. Parsed a planted transcript and compared the fields itself, never running the convention comparison. Re-derived by `control-mutations.yaml`. |
| `test_the_policy_tool_binding_would_notice_a_rename` | `test_corpus_hygiene.py` | connected | With the register read as declaring no names, check and control both fail. Its second claimed mode (the constant reading finding nothing) is carried by the check's own floor, not by this control. Re-derived by `control-mutations.yaml`. |
| `test_the_enumeration_check_fires_on_the_call_that_actually_went_missing` | `test_document_counts.py` | connected | Fails when the enumeration stops reading call ids from the sentence. Re-derived by `control-mutations.yaml`. |
| `test_the_recall_net_fires_on_a_count_nobody_declared` | `test_document_counts.py` | connected | Drives the shipped net: with its nouns unrecognized, check and control both fail. Re-derived by `control-mutations.yaml`. |
| `test_the_tag_check_fires_on_a_number_that_disagrees_with_its_tag` | `test_document_counts.py` | connected | Drives the real extraction over a document it mutates; fails when the extraction records no sites. Its docstring records an earlier draft that compared two integers it had just computed. Re-derived by `control-mutations.yaml`. |
| `test_the_retired_term_check_fires_on_a_term_the_spec_retired` | `test_document_counts.py` | connected | Drives the shipped marker over a synthetic document; fails when the marker matches nothing. Re-derived by `control-mutations.yaml`. |
| `test_the_name_check_fires_on_an_invented_test_and_rejoins_a_wrapped_one` | `test_document_counts.py` | connected | Was `read as connected`; now demonstrated. Fails when the name extraction finds nothing. Re-derived by `control-mutations.yaml`. |
| `test_each_omission_entry_fires_on_exactly_its_seeded_calls` | `test_omission_checks.py` | connected | Fails when `82045ea` is reverted, on `A-available-value-never-spoken` — a revert that broke 5 tests. |
| `test_every_traced_finding_is_assert_detectable_and_on_a_call_the_entry_fires_on` | `test_omission_checks.py` | not a control, floored | A consistency assertion, floorless like its two siblings, passing over an empty table. Floored, driven red, re-derived by `control-mutations.yaml`. |
| `test_w9_a_bare_length_filter_with_no_stopwords_fires_on_benign_turns` | `test_omission_checks.py` | connected | Fails when `27bc78d` is reverted into a copied `src/`. |
| `test_each_platform_entry_fires_on_exactly_its_seeded_calls` | `test_platform_checks.py` | connected | Fails when `27bc78d` is reverted into a copied `src/`. |
| `test_each_policy_entry_fires_on_exactly_its_seeded_calls` | `test_policy_checks.py` | connected | Fails when `27bc78d` is reverted into a copied `src/`. |
| `test_each_record_entry_fires_on_exactly_its_seeded_calls` | `test_record_checks.py` | connected | Fails when `df1eb0a` is reverted — the name-boundary commit, 22 tests. |
| `test_every_traced_finding_is_on_a_call_the_entry_fires_on` | `test_record_checks.py` | not a control, floored | The second module carrying this name. Same missing floor, same repair. A mutation spec keyed on control name kept only one of the two, which is why that file is a list. Re-derived by `control-mutations.yaml`. |
| `test_the_union_check_would_notice_an_unclaimed_entry` | `test_rubric_coverage.py` | connected | Screened as suspect, cleared by restoration: with `_covered()` returning an empty union, the check and the control both fail. The flag was a mis-pairing — the screen read the neighboring duplicates test as its check. |
| `test_the_check_would_catch_a_slowed_transcript` | `test_speech_plausibility.py` | connected | Was `read as connected`; now demonstrated. Fails when the rate measurement returns None for every utterance. Re-derived by `control-mutations.yaml`. |
| `test_the_register_guard_would_notice_an_unregistered_control` | `test_document_counts.py` | connected | The control on this register's own guard. Plants a control name matching the idiom and requires the guard to report it missing; asserts the register parses to something rather than to nothing. Added because the guard demanded it — the first row this file required of itself. Re-derived by `control-mutations.yaml`. |
| `test_the_mutation_spec_would_notice_an_anchor_that_moved` | `test_document_counts.py` | **disconnected, repaired** | Finding 4, and it was written by this audit. It re-counted a list built in the test; with `hits` pinned to 1 so no anchor could be reported stale, the check and the control both passed. The counting is `_stale_mutation_anchors` now, called by both, and the control drives it over a file it writes. Re-derived by `control-mutations.yaml`. |
| `test_the_gate_would_notice_a_mutation_that_does_not_change_the_file_size` | `test_verify_controls.py` | connected by construction | Finding 8's control. Drives both directions itself over a sample module: a same-size edit with the mtime pinned is invisible without the gate's environment and seen with it. No mutation entry — the defect it guards is CPython's cache validation, not a line in this tree. |
| `test_the_gate_refuses_to_write_bytecode_and_to_copy_a_stale_cache` | `test_verify_controls.py` | connected | The narrower half, bound to the tool: fails when the gate stops setting `PYTHONDONTWRITEBYTECODE`. Re-derived by `control-mutations.yaml`. |

### On the strength of a connected verdict

A revert that breaks 196 tests proves little about any one of them. Two of the nine reverts are that
broad — `d024a43`, the rubric freeze, and `27bc78d`, the cue requirement at 103 tests — and a row whose
only evidence is one of those is weaker than a row that failed under a targeted revert. The rows
carrying `3a9100d` (10 tests), `82045ea` (5) and `df1eb0a` (22) are the strong ones. Rows resting on
`27bc78d` alone are marked connected because the control did fail when a real defect was restored,
which is the claim being made; a sharper verdict wants a surgical revert of the single hunk.

Two reverts could not be scored per-control at all: `d033efd` removes `state_writes` and `1dbd22c`
removes `DuplicateCallError`, so the tree stops importing and collection aborts. Those fixes are
guarded in the strongest available sense — the suite will not load without them — but a per-control
verdict needs a revert of the behavior alone, keeping the symbol.

One revert was noticed by nothing, correctly: `7072cf4` changes only a raw docstring and an exit-code
comment. There is no behavior there to guard.

## Findings

### Finding 1 — the control-character sweep control named three modes and covered one

`test_the_control_character_sweep_would_notice_one` asserted that `_CONTROL` held the byte that
prompted it, then **recomputed the sweep's detection expression on a literal of its own**. Its
docstring claimed it would catch a sweep "whose character set is empty, or whose extension filter
matches nothing".

Measured, with a real 0x08 byte planted in a `.py` file in a copied repository:

- Filter intact: the sweep **fails**, correctly naming the planted byte.
- `_CONTROL` emptied: the sweep passes over the byte, and the control **fails**. This half worked.
- Suffix set changed to one matching nothing: the sweep passes over the byte, and **the control passes
  with it**. Blind.

The walk, the filter and the character set are now one named function, `_control_character_offenders`,
which the check and the control both call. The control plants the byte in a file on disk and requires
the sweep to name it, plus a file with an unswept suffix that it must *not* name, which pins the
filter from both sides. Driven red on both modes and restored.

### Finding 2 — the anchor control asserted a property of the corpus, not of the check

`test_the_anchor_check_would_notice_a_moved_event` never moved an event. It asserted that the anchor
table parsed to a floor of 12 calls, and that the first row's fragment did not also appear in the
neighboring event. Both are properties of the corpus. Its docstring claimed it guarded two modes: "a
parser bug returning zero rows, or a comparison that always succeeded".

Measured, in a copied repository:

- `_anchor_rows` returning nothing: the check **fails** and the control **fails**. Covered — though the
  check already fails on that by itself, so the control adds nothing here.
- The per-row comparison neutered so it can never append a problem: the check passes over a manifest
  that no longer describes the corpus, and **the control passes with it**. Blind, and this is the mode
  the anchor table exists for.

The comparison is now `_anchor_problems`, called by both. The control moves an anchor onto its
neighbor — the renumbered transcript the table was written to catch — and requires the comparison to
name it. Driven red and restored.

### Finding 3 — the leak-scan control was a tautology, and neighbors were doing its job

`test_the_leak_scan_would_notice_a_turn_that_was_in_the_corpus` guarded the seam that keeps agent
speech out of the grounding corpus — the property that stops a claim being resolved against the claim
that made it. It read:

```python
widened = context.ground_truth.corpus + "\n" + context.subject.agent_turns[0].text
assert context.subject.agent_turns[0].text in widened
```

`x in (y + "\n" + x)` is true for every `y`, including the empty string. It never called the scan.

Measured, with `GroundTruth.corpus` returning empty in a copied `src/` — the seam grounding against
nothing at all:

- The scan reported no leak and passed. **The control passed with it.**
- Two unrelated tests in the same module failed. **That is the only reason the seam was covered.**

The second bullet is the finding under the finding. The named guard was green and blind, and the
protection came from somewhere nobody had written down — this project's own "criterion ticked against
a neighbor". Refactor those two neighbors and the cover leaves with them, silently.

Two repairs, because there were two gaps. The comparison is now `_leaked_turns`, which the check and
the control both call, and the control drives it in both directions over a corpus it builds. And the
check gained the floor it never had: it asserted `turns >= 100` on the subject side while **nothing
guarded the ground-truth side**, so a seam producing no corpus passed. Each mutation is now caught by
the right mechanism — a groundless seam fails the check, a broken comparison fails the control.

This row was found by a static screen for the shape, in minutes, after the first two were repaired.

### Findings 5 and 6 — two corpus guards that compared beside their checks

Both were found by auditing the rows the screen had been silent about, and both are the same shape as
the first four.

`test_the_matched_by_check_fires_when_the_register_names_the_wrong_call` re-pointed the register's
paragraph at a different call and then ran **its own** `re.findall` and **its own** `!=`. The check's
comparison was `named == exceptional`, inline. Weaken that equality to a superset test — the shape
that lets the register name an *extra* call — and the check passes over it and the control passes with
it. The comparison is `_matched_by_disagreement` now, called by both, and the control drives it in
two directions: a re-pointed paragraph and a widened one.

`test_the_escalation_convention_check_fires_on_the_field_that_was_got_wrong` planted
`outcome: transferred` into a copy of the escalated call, parsed it with the real parser, and then
compared the parsed fields against `ESCALATION_RECORD` itself. It never ran the convention check.
Make that comparison unable to report a violation and the check passes over a corpus that no longer
holds the convention, with the control green beside it. The comparison is `_convention_violations`
now, and the control hands it the record it planted.

### Three rows that were not controls at all, and were worse than that

`test_every_traced_finding_is_on_a_call_the_entry_fires_on` exists in `test_conduct_checks.py` and
`test_record_checks.py`, and `test_omission_checks.py` carries the `assert_detectable` variant. They
match the naming idiom because `fires_on` ends their names, but they restore no defect and require no
outcome to move: they are consistency assertions between two declarations. `connected` is not a
question that can be asked of them.

The question that *can* be asked — does it compare anything? — had a worse answer. **All three passed
over an empty `EXPECTED_FIRING`**, having compared nothing, while their neighbors in the same files
carried floors for exactly that. Each now counts what it compared and asserts a floor, and each was
driven red by emptying its table.

### Finding 8 — the gate's verdict depended on how fast the machine was

The first CI run of `tools/verify_controls.py` reported two controls green with their defects
restored. Both pass locally. They were exactly the two entries whose replacement is the **same number
of bytes** as the line it replaces: `==` for `>=`, and one 30-character regex for another.

CPython validates a cached `.pyc` against the source's **size and mtime in whole seconds**. The gate's
unmutated run writes that cache; the mutated run then reuses it whenever the edit preserves the size
and both runs land inside one second. CI is fast enough — roughly four tenths of a second per entry —
that they did. Locally each entry crosses a second boundary, so the same mutations were seen.

Demonstrated rather than inferred: with a stale cache present, a same-size edit under a pinned mtime
left the test passing; with the cache removed and bytecode writing off, the same edit failed it.

The gate sets `PYTHONDONTWRITEBYTECODE` now and no longer copies `__pycache__` into the tree it
mutates. `test_the_gate_would_notice_a_mutation_that_does_not_change_the_file_size` plants that exact
shape and requires it to be seen.

**It failed closed, and that is the only reason this is a footnote rather than a disaster.** A masked
mutation makes a control look *disconnected*, never connected — a spurious finding, which is loud, not
a spurious pass, which is silent. That direction was luck rather than design, and it is worth stating
because the next instrument may not have it.

### What the findings have in common

None was found by rereading, and each had passed every prior audit. Six of the eight are the same
shape: **a control that re-implements the rule beside the check instead of calling it.** A control
written that way is proof about its own copy of the logic, which is the one copy that cannot fail in
production. The repair was the same each time: give the check a named function and make the control
drive it.

The shape *is* findable once named, and cheaply. The first two came from reading for one question —
*does this control call the function the check calls?* — and the third from an AST screen for the
same question. **The base rate is now known, because every row was audited**: of the register's
control rows, six were defective. Not three of three, and not one in ten — the honest figure sits
between, and it took restoring every defect to get it. The screen found one of the six; the rest came
from restoration.

The screen is triage and not a verdict. It also flagged `test_the_spy_would_notice_a_connection`,
which turned out sound — it calls `socket.create_connection` and requires the fixture to raise, and
the screen missed that because it counted only bare-name calls. Only restoring the defect settles it.

### Finding 4 — the register's own guard carried the shape, written the day the register was

`test_the_mutation_spec_would_notice_an_anchor_that_moved` was added by this audit, to guard the
anchors in `control-mutations.yaml`. It built a list in the test and re-counted it:

```python
plausible = [moved, doubled, doubled]
assert [line for line in plausible if plausible.count(line) != 1] == [doubled, doubled]
```

That is the counting rule written a second time, next to the check, over data the control invented.
Measured: with `hits` pinned to `1` in the check so no anchor could ever be reported stale, the check
passed over a spec whose anchors had all moved, and **the control passed with it**.

The counting is `_stale_mutation_anchors` now, called by the check and by the control, and the
control drives it over a small file it writes — an anchor matching nothing, one matching twice, one
resolving cleanly, and a file that is absent — requiring the first three to be reported and the
fourth not. Driven red and restored, and re-derived every run.

Worth stating plainly: this was written **while** documenting the shape, by someone who had just
repaired three instances of it, and the screen caught it rather than the author. The shape is not a
lapse of attention. It is what writing a control next to a check naturally produces.

## The screen, and what its silence is worth

The findings above were found by one question — *does this control drive the check's own comparison,
or a copy of it?* Mechanized as `tools/screen_controls.py`, the signal is: **the check accumulates its
verdict inside a loop, and the calls feeding that accumulator are ones the control never makes.**

```bash
uv run python tools/screen_controls.py
```

**It was calibrated before it was trusted**, against the tree as it stood at `c21c1ba`, before any
repair — pass it that tree's `tests/` as an argument. It flags four rows there: the three then known
to be defective, which is no false negatives on the known set, plus one false positive. An earlier
version flagged on inline accumulation alone and false-positived the moment a repair delegated the
comparison but kept the loop — what matters is not that the check loops, but whether what it
accumulates comes from a function the control also calls.

Run over the register it raised two rows. One was Finding 4, confirmed by restoration. The other,
`test_the_union_check_would_notice_an_unclaimed_entry`, was a **mis-pairing**: the screen guesses a
control's check by taking the nearest preceding test, and picked the neighboring duplicates test
instead. Restoring the defect settled it — with `_covered()` returning an empty union, the check and
the control both fail, so that row is `connected`.

**What the screen does not say is most of what there is to say.** Every other row came back
`clear(no inline verdict)`, which means the check does not accumulate a verdict in a loop, so the
signal does not apply. That is the screen being **silent**, not the row being clear. The shape it
detects is one shape; a control can be disconnected in ways that leave no loop to inspect. Rows whose
only evidence is this screen are still `unaudited`, and they are marked so.

So the honest ledger for the screen: cheap, calibrated 3 of 3 in both directions, one true find, one
false positive resolved by restoration, and structurally silent on the majority. **Screening is
triage. Restoring the defect is the audit.**

## Re-deriving a verdict instead of asserting one

A row saying `connected` is a claim in a document, and this project's recurring failure is a claim in
a document going stale. `control-mutations.yaml` names, per control, the one line whose mutation
restores the defect it guards. `tools/verify_controls.py` copies the repository, applies each
mutation to the copy, and **requires the named control to fail there and to pass without it**. So a
`connected` verdict covered by that file is re-derived on every run rather than trusted.

```bash
uv run python tools/verify_controls.py
```

**CI runs it on every push**, beside the phase verifiers. That is the difference between a gate and an
instruction in a handover: this file's whole argument is that a claim nobody re-derives goes stale, and
a gate nobody runs is the same defect wearing a tool's clothes. It was not wired in when it was
written, which is worth recording rather than quietly fixing.

Its refusals matter as much as its passes. A `find` matching zero lines, or two, stops the run with
exit 2 rather than reporting a verdict — because a mutation that silently lands nowhere is the exact
failure this whole exercise exists to find, and it must not be the way this tool fails. It refused
twice while being written: once on `    return problems`, which also matches `    return problems,
compared` one function over under substring rules (it compares whole lines now), and once when
`ruff format` collapsed `_SWEPT` onto a single line and the anchor stopped matching.

That second refusal is why `test_every_mutation_find_line_is_present_exactly_once` is in the suite. A
formatter runs on every commit; a gate that only notices its anchors have drifted when someone
remembers to run it is a gate that quietly stops verifying. Both directions are asserted, and both
were driven red.

**What this does not do.** It re-derives the rows it covers, and the register's `unaudited` rows have
no entry — their absence is the honest form of "nobody has driven this either way". It is also one
mutation per control, chosen by the person who repaired it, so it proves the control catches *that*
defect and not that it catches every defect. Mutation testing over the checks would be the general
form; this is the curated, cheap version of it.

## Outside the idiom

The naming convention recovers the rows above. Looking instead for the *shape* of a control — a test
that mutates something and requires an outcome to move — finds substantially more, including these,
none of which the idiom matches:

These are audited too, by the same procedure, and each has an entry in
`control-mutations.yaml` so its verdict re-derives. Seven were connected; one was **masked**, which is
a failure mode none of the first six had.

| Control | Module | Verdict | Evidence |
|---|---|---|---|
| `test_w10_a_state_cleared_before_the_action_is_not_a_violation` | `test_claim_checks.py` | connected | Fails when the blocking *value* stops being compared, so any write to the gating variable blocks the tool. |
| `test_mutating_a_declared_parameter_moves_a_verdict` | `test_claim_checks.py` | connected | Fails when the declared success statuses stop being compared, which makes `success_statuses` a parameter the check does not read. |
| `test_a_hedge_in_the_stating_turn_does_not_resolve_the_deadline` | `test_conduct_checks.py` | connected | Fails when the declared-name boundary is dropped and signals match as bare substrings -- D115's `may` inside `maybe`, against a signal list of month names. |
| `test_a_state_written_before_the_handoff_does_not_satisfy_required_state_after` | `test_omission_checks.py` | connected | Fails when `index > invocation.call.index` is dropped, so a write before the handoff satisfies a requirement about the state after it. |
| `test_a_variable_set_between_the_asks_clears_it_even_if_set_again_after` | `test_record_checks.py` | connected | Fails under last-write-wins, where a write between the asks is forgotten the moment a later one exists. |
| `test_adding_the_supporting_sentence_to_speech_alone_does_not_move_the_verdict` | `test_policy_checks.py` | **masked, repaired** | Finding 7, and the first of this mode. It asserted the verdict alone; CALL-02 violates on 2.4 **and** 3.2, so the verdict cannot move even when 2.4 is wrongly resolved. Measured: with a grounding blob counting a spoken clause as applied, the verdict held at `unapplied` and the evidence went from two findings to one, 2.4 silently gone. It asserts the evidence now. |
| `test_a_deduplication_key_would_clear_the_retry` | `test_record_checks.py` | connected | Fails when the declared deduplication arguments are read as an empty list. |
| `test_a_word_list_would_have_fired_on_three_turns_a_phrase_list_does_not` | `test_claim_checks.py` | connected | Fails when a phrase in the shipped signal list is replaced by the bare word `moved`, which then fires on CALL-19 where the promoter moved the event and the agent moved nothing. |

### Phase 3 — the transport seam and the judged tier

Added with the judged tier. None matches the naming idiom either, so these are hand-added rows like
the ones above; each has an entry in `control-mutations.yaml`, so `tools/verify_controls.py`
re-derives every verdict here on every push.

**Three of these restore a defect that was real in this phase**, not a hypothetical one. That is
worth saying because the rest of this file is about controls whose defects were found by earlier
sessions: these were found while the code was being written, by tests that failed for the right
reason.

| Control | Module | Verdict | Evidence |
|---|---|---|---|
| `test_the_repetitions_obtained_before_an_abort_are_not_discarded` | `test_judge_engine.py` | connected | The sharpest row here, and the defect was shipped for an hour. A transport failure part-way through a call's repetitions discarded the repetitions already completed, while `RecordingTransport` had already written them to the run log — so the run reported `results: 0` over a log holding one entry. Found by a CLI replay test whose reference log covered fewer repetitions than the rubric asked for, not by reading. Fails when `JudgedCallAborted` is given an empty list instead of the partial outcomes. |
| `test_an_unpriced_model_refuses_rather_than_estimating_zero` | `test_transport.py` | connected | The second real one. The estimate was `PRICING_USD_PER_MTOK.get(model, (0.0, 0.0))`, so a live run of any size against an unpriced model reported `$0.00` — a fail-open at the one moment a human is asked to agree to the spend. Fails when the refusal is replaced by that zero. |
| `test_the_pricing_table_cannot_be_mutated` | `test_transport.py` | connected by construction | The third. The pricing table was a `MappingProxyType`, and `test_every_final_constant_holds_a_value_that_cannot_be_mutated` flagged it: a read-only *view* whose backing dict is mutable by anyone holding a reference. Nothing held one, which is exactly the "effectively immutable" this tree does not accept. No mutation entry — the assertion is the type, and the old code fails it directly. |
| `test_the_replay_path_does_not_import_the_sdk` | `test_transport.py` | connected | D122's condition, as a property of the import graph. Fails when the `TYPE_CHECKING` guard becomes `if True`, so the deferred SDK import runs at module scope and every replay run loads it. |
| `test_the_run_log_carries_no_credential_that_was_in_the_prompt` | `test_transport.py` | connected | Drives `RecordingTransport.send` → `RunLogWriter.record` over a real file rather than serializing an entry beside it — the writer grew an injectable `environ` so that it could. The first draft called `RunLogEntry.as_dict` itself, which is the shape D121 found in six controls. Fails when the scrubber's length test is raised past any real key. |
| `test_the_ceiling_is_a_number_of_calls_issued_and_not_that_number_plus_one` | `test_transport.py` | connected | Fails on an off-by-one in the ceiling comparison, which admits exactly one call past the limit. |
| `test_a_refused_call_is_not_recorded_because_it_did_not_happen` | `test_transport.py` | connected | **The same defect as the row above**, driving a different property: the call the ceiling should have refused is issued and therefore recorded, so the log carries an entry for a call the run reported refusing. Said plainly rather than left to look independently proven — two controls over one mutation is one demonstration, not two. |
| `test_each_population_is_validated_against_its_own_set_and_not_the_union` | `test_judge_prompt.py` | connected | W1's shape. Fails when a fact citation is validated against every rendered identifier's *number* rather than against the fact population, so `[F9]` is accepted on a call with twelve transcript lines and two facts because `T9` exists. |
| `test_mutating_each_judged_field_changes_what_is_sent` | `test_judge_engine.py` | connected | The judged tier's form of "no parameter is hardcoded", per field. The deterministic tier buys it with `ParamView`; a judged entry has no `params`, so this is the equivalent. Fails when the generation configuration is written at the call site instead of read from the entry — W20 in the tier with no `ParamView` to catch it. |

### Three mechanisms that replaced a caveat, 2026-09-09

Added after a count of what this project verifies **mechanically** and what it verifies **by a
reader**. Of 68 acceptance criteria across three phases, 14 carried caveats; of those, four described
a property that could be mechanized and was not. Three of the four are closed here. The fourth
(W8's row at tier level) is a coverage gap in the corpus rather than a missing check.

The shape they share is worth naming: **each replaced a statement in prose with a value read off the
thing the statement was about.**

| Control | Module | Verdict | Evidence |
|---|---|---|---|
| `test_the_sdk_retry_count_is_zero_so_our_backoff_replaces_it` | `test_transport.py` | connected | The specification requires the backoff posture to be **stated**, and D122 stated it: our backoff replaces the SDK's rather than wrapping it. Nothing read the value the client was built with — the only assertion was that the SDK *accepts* the parameter. Reads the constructor's kwargs through a recording stub now. Fails when `SDK_RETRIES` becomes the SDK's own default of 2. |
| `test_the_retry_loop_sleeps_the_declared_schedule_and_not_after_the_last_try` | `test_transport.py` | connected | The schedule was unasserted on the stated grounds that checking it would mean a test that waits. That was wrong, and the caveat saying so was the thing to fix: the sleeps are a **sequence of requested delays**, and an injected recorder captures them instantly. Asserts the delays follow `backoff_delay` and that there is no sleep after the final attempt. Fails on an off-by-one that sleeps before giving up. |
| `test_every_judged_field_has_a_declared_mutation` | `test_judge_engine.py` | connected | The coverage half of the judged tier's `ParamView` analogue. `test_mutating_each_judged_field_changes_what_is_sent` covered all eight `JudgeSpec` fields — by a hand-written list, so a ninth would have failed nothing. Both tests now read `dataclasses.fields(JudgeSpec)`. Fails when a field is renamed and the mutation table is not. |

| `test_the_register_guard_would_notice_an_unregistered_obligation` | `test_obligations.py` | connected | The control on the obligations register's own guard, and the same shape as the control register's. Drives `_owed_items` over a handover-shaped document it writes rather than parsing its own string beside the check. Fails when the harvest globs a filename pattern no handover matches — a rule that harvests nothing is a list again, and a list nobody maintains is the reading it replaced. |

**One of the three is a control on a claim rather than on code**, and that is the more interesting
kind. "Our backoff replaces the SDK's" was true, documented, and unverifiable — the sort of statement
this register exists to distrust, appearing in a module docstring instead of a document.

**What these rows do not cover, and it is the same gap as everywhere else in this file.** Each shows
its control catches *that* defect. The judged tier's largest untested surface is not a control gap at
all: it is that no judged verdict in this repository has come from a model yet. Every assertion above
runs against a scripted transport, which is the right instrument for a classification and the wrong
one for a judgment.

**Three of my own mutations were aimed at the wrong code**, and each produced a `[FAIL]` the gate was
right to report and I was wrong to believe: a control cannot notice a defect that is not the one it
names. A `[FAIL]` is a suspicion until the `defect:` line has been checked against what the control
actually plants. All three cleared once re-aimed. That is the same shape as everything else in this
file, one level up: a mutation ticked against a neighbor of the defect.

Widening the idiom to catch these would also catch ordinary negative-input tests — `test_text_adapter.py`
alone has a dozen that feed malformed input and require an abort, which are feature tests, not controls.
The line between the two is whether the mutation restores a defect that was once real, and that judgment
is not in a name. So the rule stays narrow and this section stays hand-maintained.

### The phase-3 audit's remediation, 2026-09-09

An independent session audited phase 3 and ran a **mutation sweep** rather than a reading: fourteen
fail-open-shaped defects restored one at a time into a copy of the tree, against the five judged-tier
test modules. Seven were caught, which is the sweep's own positive. **Seven were not**, and every one
of them is a row below — reproduced here before being acted on, because an audit's null result is
worth exactly as much as the instrument behind it.

The pattern in the misses is worth naming, because it is not the pattern the controls were written
against. None is a check that re-implements its rule (D121's shape). Every one is a **guard that
exists in the code and is driven by nothing** — the refusal is there, the scrub is there, the exit
code is there, and the suite would not notice their removal. A control register cannot see those:
it audits controls, and a check nobody planted one for is invisible to it. That is `OB-2`, arriving
with instances.

| Control | Module | Verdict | Evidence |
|---|---|---|---|
| `test_a_live_transport_with_no_credential_in_reach_refuses` | `test_transport.py` | connected | The highest-severity miss. "A live run SHALL require a credential" was enforced by a line no test reached: every `LiveTransport` the suite built was handed a fake key, and the only test naming `CredentialMissingError` constructed the exception to read its message. Fails when the lookup returns an empty credential instead of raising — which is what the harness would then do: construct a client with `api_key=""` and let the provider refuse, one confirmation later. |
| `test_the_credential_lookup_reads_both_routes_and_refuses_only_when_both_are_empty` | `test_transport.py` | connected | The same refusal at the named function the CLI now shares. Two rows because the requirement has two callers, and a refusal only one of them could reach is the arrangement this replaced. |
| `test_live_mode_requires_a_credential_before_it_prints_an_estimate` | `test_cli.py` | connected | Not an exit code but an **order**. With the CLI's check removed the run still exits 2, from the transport constructor, so an exit-code assertion sees nothing; what fails is that the estimate was printed and the spend confirmed first. The requirement states its three clauses in the order they have to happen in. |
| `test_no_scrubbed_field_of_a_run_log_entry_carries_a_credential` | `test_transport.py` | connected | Three of the four scrubbed run-log fields could be removed one at a time with the suite green. The one test planted its key in the **prompt**; the committed-artifact scan is the right instrument for the artifact and says nothing about a writer leaking into a *new* log. Fails when `response_text` — the model's text, and the likeliest of the four to carry a stray secret — is written unscrubbed. |
| `test_both_credential_values_are_scrubbed_when_the_two_disagree` | `test_transport.py` | connected | A test green on a neighbor of its own subject. It put the file's key under one variable name and the environment's under another, so nothing disagreed and both survived a `setdefault` that discards a loser only when there is one. The property it names — the overridden value is still scrubbed — was false for as long as the `.env` route existed. Fails when one mapping answers both questions again. |
| `test_a_credential_that_contains_another_is_redacted_whole` | `test_transport.py` | connected | The ordering rule, driven. Fails when the scrub order is declaration order rather than longest first, so the shorter value is replaced inside the longer one and a live tail survives beside a redaction token. |
| `test_a_token_from_the_alternative_variable_travels_under_the_bearer_header` | `test_transport.py` | connected | `.env.example` offers `ANTHROPIC_AUTH_TOKEN` and a token supplied that way could not authenticate: the SDK sends `api_key` as `X-Api-Key` and `auth_token` as `Authorization: Bearer`, read off two constructed clients rather than inferred. Fails when the routing collapses back to `api_key`. |
| `test_a_judged_run_with_only_some_results_errored_still_reports_the_tier_incomplete` | `test_cli.py` | connected | D114's exit 3 was asserted for the deterministic tier only. A judged run that errored on every call and exited 0 would have been noticed by nothing. Fails when the incomplete branch is removed.. **Re-pointed at D143**: the all-errored run it named trips both exit-3 guards, so restoring this one changed nothing and the control measured nothing |
| `test_a_judged_run_the_transport_aborts_exits_three_and_says_what_it_obtained` | `test_cli.py` | connected | The other route to 3, and the one carrying partial results: the log holds them either way, so a silent 0 makes the artifact and the exit code disagree. Fails when the abort branch is removed. |

| `test_a_retry_truncated_at_max_tokens_is_reported_as_truncation` | `test_judge_engine.py` | connected | The retry leg skipped the classification the first attempt gets, and both legs reach `errored` — so the status was right and the reason was wrong. A truncated retry reported "not valid JSON" with `max_tokens` in the log two lines away. Fails when the retry's stop-reason branch is removed. |
| `test_a_response_carrying_no_stop_reason_is_not_read_as_a_complete_answer` | `test_judge_engine.py` | connected | An empty stop reason read as "neither a refusal nor a truncation" and parsed into a verdict. A criterion asserts the artifact carries one on every entry; nothing asserted the engine required one. Fails when the guard is removed. |
| `test_a_malformed_answer_is_corrected_in_its_own_words_not_an_empty_citation_list` | `test_judge_engine.py` | connected | One correction wording for two causes: a response that did not parse has no rejected identifiers, so the retry read "cited identifiers that were not in this prompt: ." Fails when the citation wording is sent unconditionally. |
| `test_the_preflight_estimate_brackets_what_the_real_run_recorded` | `test_reference_run.py` | connected | The check the decision record called available and not built, computed against the committed log rather than reasoned about. Fails when the divisor returns to the value derived from English prose, which put the estimate below every recorded input count on all sixteen calls. |
| `test_a_skipped_control_is_not_mistaken_for_one_that_passed` | `test_verify_controls.py` | connected | A control that was skipped is unrunnable rather than green. Fails when `_was_skipped` answers False for everything, which is the gate's state before D143 — pytest exits 0 for a skip, so three controls that never executed were reported as having stayed green with their defects restored |
| `test_the_retry_window_outlasts_a_transient_overload` | `test_transport.py` | connected | The backoff schedule adds up to at least the declared minimum window. Fails when the attempt count returns to 4, which is 7 seconds of retry guarding an hour-long recording — the schedule an `overloaded_error` outlasted on 2026-09-11, discarding 575 successful calls (D145) |
| `test_every_scored_finding_still_matches_the_text_it_was_scored_against` | `test_findings.py` | connected | Every severity band still describes the finding text it was placed on, recomputed from the gold set and compared against the hash the tool exports at schema 2. Fails when a scored finding's wording is edited — the defect `e28650c` introduced on 2026-09-07 and nothing saw for four days (D140, D148) |
| `test_every_quotation_attributed_to_a_decision_is_one` | `test_document_counts.py` | connected | A quotation introduced by naming the decision it comes from is that decision's wording. Fails when the text inside the quotation marks is not in the decision named — the defect found twice by reading on 2026-09-11, once in the finding that argues for widening the dimension it misquotes (D149) |
| `test_the_quotation_guard_finds_a_misquotation` | `test_document_counts.py` | connected by construction | The guard's own control, in-module because the defect is three words removed from inside a quotation and a whole-line mutation cannot express that in a wrapped document. Plants the handover's D42 quotation as it read before correction and requires the comparison to reject it, having first asserted D42 still contains the wording it is built on |
| `test_every_register_row_still_points_at_the_obligation_it_was_written_for` | `test_obligations.py` | connected | The obligations harvest compared a number and nothing else, so renaming an owed heading while keeping its number left all ten tests green. Fails when the anchor comparison is skipped. |
| `test_a_closed_phase_handover_requires_the_sweep_marker_to_have_reached_it` | `test_document_counts.py` | connected | D129. The specification's own *at phase completion* sweep clause, evaluated for the first time — it had fired for phase 2 and again for phase 3 with the numeric clause green both times. Fails when the scan finds no closed handover, which is the floorless-comparison shape rather than a wrong answer. |
| `test_the_count_the_summary_prints_separates_criteria_from_requirement_prose` | `test_phase3_acceptance.py` | connected | The verifier's closing line counted requirement anchors as acceptance criteria and printed 21 over a document carrying 18. Reads `criteria_in_document`, the function the summary calls, rather than recomputing the rule beside it. Fails when that function stops distinguishing a criterion bullet from requirement prose. |

| `test_a_failing_control_is_not_mistaken_for_one_that_could_not_run` | `test_verify_controls.py` | connected | **Found by the gate, in the gate.** `run_control` refused any run whose output contained the substring `ERROR`, which is also a substring of anything a failing assertion prints — and one of this project's status values is `Status.ERRORED`. A control that drove red correctly, over an errored result, was reported as unrunnable and stopped the sweep at entry 51 of 57. Fails when the predicate goes back to the bare substring. |

**Two of the nine are controls on an order and on a header**, not on a value — and both are the kind
a reading cannot settle. The ordering one exits 2 with its defect restored, so only an assertion
about *what was printed first* moves; the header one is a property of a client this project
constructs and a library it does not, so it is asserted by reading the constructed client's own auth
headers rather than by trusting a parameter name.

### Phase 4 — the run log's format (D128, D131)

Six controls on one change, and the change is storage only. That is the reason for six rather than
one: a format change that "cannot alter behavior" is exactly the shape under which a scrub, a
refusal or an ordering quietly stops holding, and an independent audit found three scrub sites in
the previous format driven by nothing at all.

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_one_string_sent_n_times_is_stored_once_and_referenced_n_times` | `test_transport.py` | connected | The whole of D128, measured on the file rather than argued: one distinct value sent N times is stored once. Fails when the writer stops skipping a blob it has already written, which is the v1 format — the same system prompt recorded 160 times. |
| `test_a_blob_is_written_before_the_record_that_references_it` | `test_transport.py` | connected | The ordering the one-pass reader relies on, asserted on positions in the file. Fails when the call record is written ahead of the blobs it names — which changes nothing about a completed run and leaves a truncated one holding a dangling reference, inside results the requirement says are persisted. |
| `test_a_reference_to_a_blob_the_log_does_not_carry_is_refused_by_name` | `test_transport.py` | connected | A damaged log is refused, and is neither a stale log nor a cache miss. Fails when an unresolvable reference resolves to an empty string instead — the fail-open the v1 format's direct read would have produced, and the one under which "the exact prompt sent is recoverable" is false with nothing complaining. |
| `test_a_call_record_with_no_reference_at_all_is_refused_by_name` | `test_transport.py` | connected | Two causes, two messages. Fails when a record carrying no reference falls through to the dangling-reference branch and is reported as a lost line — one wording for two causes, the shape the retry correction had when it read "cited identifiers that were not in this prompt: ." |
| `test_a_blob_that_does_not_hash_to_its_own_identifier_is_refused` | `test_transport.py` | connected | The log's index, checked against what the log stores. Fails when the stated hash is trusted rather than recomputed, which lets a file whose index disagrees with its contents replay for as long as nobody looks. |
| `test_a_credential_is_scrubbed_inside_the_blob_and_the_hash_covers_the_scrub` | `test_transport.py` | connected | The scrub survived the move into the blob builder, and the hash is taken over the scrubbed value so a reader can recompute it. Fails when the system scrub is left behind by the move — which is the audit's own finding, three fields over, arriving through the door marked *storage only*. |
| `test_the_sentinel_allowance_would_notice_a_mutable_value_wearing_one` | `test_result_contract.py` | connected | The `Final`-constant guard was widened to admit a bare `object()` sentinel, and the widening is one keystroke from admitting everything: `isinstance(value, object)` is true of the list and the dict the guard exists to catch. Fails when the allowance is relaxed to an isinstance check. |

**What this set does not have a mutation for, stated rather than left to be inferred.** The second
half of the last row — *the hash covers the scrub* — is asserted by that test and is not separately
planted. Removing the scrub stores and hashes the same raw value, so the log's self-check still
passes and only the credential assertion moves. A mutation that hashed the raw value while storing
the scrubbed one would be the sharp one, and it is not expressible as a single line of this
module as written.

### Phase 4 — the precondition that ends the conflation (D125)

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_a_dimension_whose_precondition_fails_returns_not_applicable_and_issues_nothing` | `test_judge_engine.py` | connected | A dimension whose subject is absent from a call does not apply to it, says so, and issues nothing. Fails when the precondition is never consulted — the state three live passes measured, where four no-clause calls came back `misaligned` against a clause set that was empty. |
| `test_the_precondition_would_notice_a_dimension_that_stopped_applying_to_anything` | `test_judge_engine.py` | connected | The inversion, over the whole design set rather than one call: the judged and excluded sets partition it, and the excluded set is exactly the calls with no retrieved clause. Fails when every named category reports absent whatever the call established — a tier that measures nothing and exits clean. |
| `test_a_precondition_on_a_category_the_entry_never_renders_is_refused` | `test_rubric.py` | connected | A precondition is refused when it names a category the entry does not render, because the judge never sees that category's output and a misspelling would make the dimension apply everywhere while reading as bounded. Fails when the loader stops comparing the two lists. |

**What the fix turned up that the measurement had not.** `CONFLATED_NO_CLAUSE_CALLS` pinned four
calls — the no-clause calls flagged `misaligned`. The precondition excludes **eight**, and the four
in the difference had come back `aligned`: a verdict as meaningless as the other four and far harder
to see, because a pass on a corpus seeded with defects reads as the dimension working.
`test_the_conflation_was_wider_than_the_half_that_showed` asserts that difference is non-empty and
that every call in it sits on the dimension's positive side, so the silent half cannot go quiet
again.

### Phase 4 — the judged roll-up, its gate and its exit code (D134)

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_a_dimension_whose_repetitions_disagree_is_reported_as_a_distribution` | `test_judge_rollup.py` | connected | Every applicable repetition is in the row, including the ones that disagree. Fails when the distribution keeps only the modal verdict with the whole count under it — which is what the P4 criterion asked for before D130 amended it, and what a unanimous fixture cannot tell apart from the real thing. |
| `test_a_tie_resolves_toward_the_negative_pole_and_says_that_it_was_a_tie` | `test_judge_rollup.py` | connected | Five for and five against records that something went wrong, and the tie is reported beside it. Fails when the tie is resolved by scale order alone — an evaluator that could not decide, reported as a pass. |
| `test_the_rate_counts_calls_rather_than_repetitions` | `test_judge_rollup.py` | connected | The denominator's unit is the call. Fails when it counts repetitions, which is D124's rejected option (C): ten repetitions of one call weighted ten times in its own rate. |
| `test_every_status_that_is_not_applicable_leaves_the_denominator` | `test_judge_rollup.py` | connected | Asserted per status, over all four. Fails when every call is in the denominator whatever its status, so a dimension that errored or was refused scores as judged and passed. |
| `test_a_dimension_whose_every_result_was_refused_measured_nothing` | `test_judge_rollup.py` | connected | `OB-14`, answered without a threshold. Fails when a dimension that produced no verdict at all never reports having measured nothing — D127's state, where a judged run of refusals exits 0 and a CI job reads the exit code. |
| `test_a_dimension_that_applied_to_no_call_did_not_measure_nothing` | `test_judge_rollup.py` | connected | The inversion, and the half easiest to lose. Fails when a dimension excluded by its own precondition is reported as having measured nothing — collapsing the two states the roll-up exists to keep apart. |

**Two of these six share a mutation target and are driven in opposite directions.** The
`measured_nothing` pair plants `any(False ...)` and `any(True ...)` on the same line: one restores
D127's silence and the other makes every skipped dimension a failure. A single control on that line
would have been green against whichever direction its author happened to imagine.

### Phase 4 — the report, the synthesis and the evidence guard's full population

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_the_escaped_text_still_carries_what_it_escaped` | `test_report.py` | connected | The model's text is recoverable from the rendered cell. Fails when a pipe is **removed** rather than escaped — and the criterion as originally written stays green under that same mutation, which is why D130 added this half. |
| `test_escaping_is_injective_so_two_rationales_cannot_render_the_same` | `test_report.py` | connected | Two rationales cannot render as the same cell. Fails when the backslash is not escaped, so `a\|b` and `a\|b` collide — invisible corruption, because the table still renders and the round trip returns something plausible for the wrong input. |
| `test_an_entry_tracing_findings_on_two_desks_appears_in_both_sections` | `test_report.py` | connected | Routing is by membership. Fails when an entry is routed by the first of its owners, so a row naming an agent defect and a platform defect reaches one desk — D43's "actionable by nobody", arriving at render time. |
| `test_a_call_that_failed_in_more_than_one_way_carries_orthogonal_labels` | `test_report.py` | connected | Three independent axes per call. Fails when the "what could not be evaluated" axis is dropped and the row collapses toward one label, which is the recommendation taxonomy 34 makes about this report and not only about a system under test. |
| `test_the_non_determinism_caveat_is_inline_above_the_numbers_it_qualifies` | `test_report.py` | connected | Position, not presence. Fails when the caveat moves to a footer — still present, still accurate, and met by a reader who has already believed the numbers. |
| `test_the_tier_a_section_is_byte_identical_across_runs_and_across_modes` | `test_report.py` | connected | The deterministic renderer takes no mode and cannot. Fails when it is given one, which is D8's conflation: a renderer with a mode can use it tomorrow, and the snapshot regenerated to make CI green takes the regression signal with it. |
| `test_the_report_matches_the_committed_snapshot_byte_for_byte` | `test_report.py` | connected | The golden regression, against something older than this run. Fails when the report's own title changes — while `test_two_consecutive_replay_reports_are_byte_identical` stays green, because nothing about the run's determinism moved. **That pairing is the criterion.** |
| `test_a_synthesis_resting_on_a_dimension_that_produced_no_result_is_a_reported_defect` | `test_judge_engine.py` | connected | The requirement's verb is *report*. Fails when the citation defect is never recorded, so a synthesis that reasoned from a dimension which did not run reports a verdict and nothing beside it. |
| `test_a_synthesis_resting_only_on_dimensions_that_ran_is_reported_clean` | `test_judge_engine.py` | connected | **The inversion, planted.** Fails when *every* identifier is reported as a defect — which passes the criterion as originally written, and is exactly the shape D104 found in the P2 grounding criterion whose fixture resolved either way. |
| `test_the_synthesis_runs_after_every_dimension_for_the_same_call` | `test_judge_engine.py` | connected | Ordering is a contract. Fails when judged entries run in plain id order, so a synthesis evaluated before its dimensions is shown none and returns a verdict that synthesizes nothing, for a reason that is the harness's (since D165; before it, a citation defect on every call). |
| `test_a_synthesis_sees_only_its_own_calls_results` | `test_judge_engine.py` | connected | Scoped per call. Fails when the synthesis is handed every outcome the run has produced so far, which makes one call's prompt depend on which call was evaluated first — and replay keys on the request hash. |
| `test_the_evidence_guard_fires_for_every_judged_scale_the_rubric_declares` | `test_claim_checks.py` | connected | **W12's own defect, restored.** Fails when the guard keys on a literal verdict instead of the entry's declared negative pole. The phase-3 criterion stays green under it, because the entry that criterion names is the one whose pole is that literal — which is what "not only for one" exists to catch. |

**Three of these twelve are paired with a control that stays green under the same mutation**, and the
pairing is the finding rather than a coincidence: escaping-versus-deleting, the snapshot-versus-two-runs
regression, and the evidence guard on one scale versus all of them. In each case the older criterion
survives the defect and the newer one does not, which is what D130 meant by *a criterion that cannot
distinguish the design from its inversion*.

### Phase 4 — the ceiling a live run found (D135)

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_every_entrys_max_tokens_clears_what_the_reference_run_recorded` | `test_reference_run.py` | connected | Every judged entry's `max_tokens` stands clear of what that entry actually produced, and no recorded answer was truncated. Fails when `J-caller-pushback-understood`'s ceiling returns to 4096, below the largest answer that entry has recorded. The mutation first returned the phase-3 entry to 4096 and went stale when that entry stopped running close to it; D143 re-derived it. |

**Its mutation is planted in `rubric.yaml`**, and it has to be: the ceiling is rubric data, so the
defect it guards cannot be expressed as a change to code. The target line carries a trailing comment
so that it is uniquely addressable — `max_tokens: 8192` sits on more than one entry's line, and a
mutation matching more than one line is refused by the gate.

### Phase 4 — the coverage check two phases had run by hand (OB-16)

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_every_requirement_of_a_mapped_phase_appears_in_the_table` | `test_contract_coverage.py` | connected | Every requirement of a mapped phase is named by at least one criterion. Fails when a requirement carries a phase tag and no criterion covers it — the state D104 found five times in phase 2 and D130 four times in phase 4, both by reading. |
| `test_every_phase_is_either_mapped_or_declared_unmapped` | `test_contract_coverage.py` | connected | The guard is total across the document. Fails when a phase drops out of both the mapping and the declared-unmapped set, so it is covered by nothing and says nothing about it — the silence `JUDGED_AGREEMENT_PENDING` refuses one register over. |
| `test_the_preflight_estimate_brackets_what_the_real_run_recorded` | `test_reference_run.py` | connected | The pre-flight estimate brackets what a real run recorded, per entry and per call. Fails when `_SYNTHESIS_INPUT_ALLOWANCE` is zeroed, which restores the pre-D142 arithmetic that sat below every recorded input count — an operator approving a number smaller than the bill |

**Only the completeness half is here, and the other half is not coming.** Whether a criterion covers
*both* halves of its requirement is judgment: D104's grounding criterion and D130's synthesis
criterion were each green against a fixture that resolved either way, and no scan sees that. What
these two remove is the failure where nobody notices a requirement has no criterion at all.

**One of the two mutations is planted in the specification**, which is unusual and is the point: the
defect is a requirement written without a criterion, and that cannot be expressed as a change to
code. It retags a `[P5]` requirement as `[P4]`, which is what a newly-written uncovered one looks
like to this check.

### The pin rule, ported from comparative-judgment, 2026-09-11

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_the_pin_rule_would_notice_every_shape_of_range` | `test_acceptance.py` | connected | Each shape of range is flagged by the clause that alone decides it, and an exact pin is not, with or without an environment marker. Fails when the `<` clause is deleted: the clause the rule shipped without, so `numpy==2.5.2,<3` read as an exact pin. Re-derived by `control-mutations.yaml`. |

**The guard had no control, and was narrower than its name.**
`test_no_dependency_is_expressed_only_as_a_floor` required `==` and refused `>`. A pin with a ceiling
passed it, so did a prefix match such as `==2.*`, and a pinned requirement whose marker reads
`python_version >= "3.12"` would have been refused for its marker. Every requirement declared today
is a plain exact pin, so the guard was green and nothing it missed was there to find. It is what the
caveat under *What is left* about a check with no control at all warns of: invisible to this file
until something else looked.

**The rule is comparative-judgment's, and nothing compares the two copies.** It was measured there
first, where the same guard's control had restated its rule instead of calling it and stayed green
with a clause deleted. Each repository's control proves its own copy.

**The entry re-derives the `<` clause only**, the clause this repository's rule never had. The other
clauses, the marker handling, and a rule that flags every pin were each driven red by hand when the
port was made, and are not re-derived on every run.

### Before the freeze — obligations phase 4 left, 2026-09-11

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_the_expected_cost_sits_between_what_the_reference_run_spent_and_the_ceiling` | `test_reference_run.py` | connected | OB-17's expected figure is priced per entry at the answer length its first attempts recorded, and sits at or above what they cost and below the ceiling (D152). Fails when the figure prices answers at the ceiling again, which prints the first line's number under a second name. Re-derived by `control-mutations.yaml`. |
| `test_a_resumed_run_issues_only_the_calls_its_log_lacks` | `test_cli.py` | connected | A resumed run issues exactly the calls its log lacks, completes under a ceiling of that many, exits as a replay of the full log does, and writes a log reading `mode: live` that names the session it resumed (D153). Fails when the resume serves nothing it recorded, so every call is issued again and the ceiling halts the run. Re-derived by `control-mutations.yaml`. |
| `test_each_synthesis_repetition_reads_its_own_resample_of_the_dimensions` | `test_judge_engine.py` | connected | Each repetition of the synthesis is rendered over its own resample of the dimensions' results, so a dimension that split reaches it differently across its repetitions, and the same outcomes render the same prompts again, which is what replay finds a request by (D154). Fails when the draw ignores the repetition, so every repetition reads one draw again. Re-derived by `control-mutations.yaml`. |
| `test_a_tied_dimension_is_shown_to_the_synthesis_as_the_report_reads_it` | `test_judge_engine.py` | connected | A tied dimension's headline in the synthesis block is the report's modal verdict, compared against `roll_up_judged` itself on a fixture where the earliest repetition's verdict is not the report's (D154). Fails when the headline is the most common verdict in repetition order again, which named the other verdict on every tied pair in the committed run. Re-derived by `control-mutations.yaml`. |
| `test_the_schema_pin_would_notice_a_file_declaring_the_schema_before_cuts` | `test_findings.py` | connected | The loader reads schema 3 and refuses any other by name, including a file that carries every field schema 3 requires (D156). Fails when the version comparison is bypassed. No test had driven that refusal before: every malformed file in the suite was refused by a missing field first. Re-derived by `control-mutations.yaml`. |
| `test_the_cut_cross_check_would_notice_an_anchor_the_file_does_not_score` | `test_findings.py` | connected | A cut anchored on a finding the file does not score is refused as a `SeverityError` (D156). Fails when the refusal is skipped, so the re-derivation's lookup raises `KeyError` through the contract. Re-derived by `control-mutations.yaml`. |
| `test_the_cut_cross_check_would_notice_a_gap_its_anchors_contradict` | `test_findings.py` | connected | A cut's stated gap is its anchors' `theta` difference, compared exactly (D156). Fails when the gap goes uncompared; the test's between-set is right, so nothing else refuses the file. Re-derived by `control-mutations.yaml`. |
| `test_the_cut_cross_check_would_notice_a_finding_left_out_of_between` | `test_findings.py` | connected | A cut's between-set is what the file's own rows place strictly between its anchors, most severe first (D156). Fails when the two go uncompared, so a cut can leave out a finding inside it with the evidence in the same file — OB-19's defect. Re-derived by `control-mutations.yaml`. |
| `test_the_cut_cross_check_would_notice_an_anchor_counted_between_its_own_cut` | `test_findings.py` | connected | Strictly between: an anchor is never inside its own cut (D156). Fails when the derivation counts the anchors, which agrees with the test's file and refuses every file the tool writes. Re-derived by `control-mutations.yaml`. |
| `test_the_cut_cross_check_would_notice_between_listed_least_severe_first` | `test_findings.py` | connected | Most severe first, the order the tool writes (D156). Fails when the derivation ranks the other way, which agrees with the test's reversed list. Re-derived by `control-mutations.yaml`. |

**Why the mutation prices at the ceiling rather than breaking the arithmetic.** OB-17 was opened for an
operator reading one figure far above the bill, and an expected line quietly printing the ceiling would
restore that with the second line still present — which a test for the line's existence passes. The
first-attempt filter was driven red by hand as well, because counting retries' answers moves the
synthesis's priced length off its recorded mean, and it is not re-derived on every run.

**The resume's header was driven red by hand as well.** With `resumed_from` never written, the
resumed log reads back naming no earlier session, and both the resume test and the header test fail;
that half is not re-derived on every run, because one mutation per control proves one defect.

**The pin beside the cut controls is not one of them.**
`test_the_real_severity_file_pins_what_lies_between_each_cuts_anchors` holds today's separation in the
committed file, so a re-export that moves a finding between a cut's anchors fails by name. What it
detects is a change rather than a defect, and updating it is a reading of the cut that moved. The
shapes a cut can be malformed in are cases of `test_a_malformed_severity_file_refuses_by_name`,
unregistered like the malformations before them.

### The phase-4 audit's remediation, 2026-09-12

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_the_judged_tables_would_notice_an_errored_repetition_among_verdicts` | `test_report.py` | connected | A call with verdicts on nine repetitions and an `errored` tenth counts that result, in the report's judged table and in the command's roll-up (D158). Fails when either renderer prints 0 there — the audit's mutation, which the whole report module and the snapshot passed before this existed (P4-1). Re-derived by `control-mutations.yaml`, once per renderer. |
| `test_a_call_row_would_notice_its_errored_repetition_dropped_beside_its_verdicts` | `test_report.py` | connected | The same call's outcome prints `errored x1` beside its verdicts, in both renderers, from the one function they share (D158). Fails when a call's statuses print only when it has no verdict, which is how both hid the repetition. Re-derived by `control-mutations.yaml`. |
| `test_the_audience_sections_would_notice_an_entry_rendered_on_the_wrong_desk` | `test_report.py` | connected | Each audience section of the rendered report names exactly the entries routed to it, in both directions. Fails when the renderer ignores the routing and every deterministic entry lands in both sections, which passed the three tests criterion 3 named and was caught by the snapshot alone (P4-2). Re-derived by `control-mutations.yaml`. |
| `test_the_calls_table_would_notice_a_judged_entry_found_on_a_minority_of_repetitions` | `test_report.py` | connected | A judged entry is under a call's "what was found" exactly when its modal verdict there is one its entry counts against the gate, read in both directions over the rendered report (D158, and D160 for the verdicts beside the pole). Fails when any repetition's negative verdict counts again, which put `J-call-synthesis` on CALL-07 (P4-8). Re-derived by `control-mutations.yaml`. |
| `test_the_modal_helper_would_notice_a_tie_with_the_negative_pole` | `test_reference_run.py` | connected | The reference-run tests read an entry's modal verdict through the roll-up's own tie rule, so a five-five tie with the negative pole names the negative pole. Fails when the helper is `Counter.most_common` again, which names whichever verdict the log recorded first and survived there after D154 took it out of the engine (P4-3). Re-derived by `control-mutations.yaml`. |

**The first control carries two mutations, one per renderer.** The report and the command line each
print the status columns from their own format string, so a mutation proven against one proves
nothing about the other; the call's outcome text is one function both print, so its control needs one.

### D160: the verdicts a judged gate counts, 2026-09-12

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_the_gate_would_notice_a_declared_violating_verdict_read_as_a_pass` | `test_judge_rollup.py` | connected | A call whose modal verdict is one its entry declares violating counts against the gate, and an entry declaring nothing still passes its middle value (D160). Fails when the roll-up counts the negative pole alone, the reading under which `J-concerns-addressed` caught none of the findings it traces. Re-derived by `control-mutations.yaml`. |
| `test_the_tie_rule_would_notice_a_split_with_a_violating_verdict_read_as_a_pass` | `test_judge_rollup.py` | connected | A five-five split between `addressed` and `partially_addressed` resolves to the violating verdict, through the roll-up and through `_modal`, which the synthesis's headline also calls. Fails when that tie falls through to scale order and records a pass. Re-derived by `control-mutations.yaml`. |
| `test_the_loader_would_notice_a_violating_verdict_outside_the_scale` | `test_rubric.py` | connected | A declared violating verdict the scale does not hold is refused by name. Fails when it is dropped without a word, leaving a misspelled middle value counting nothing. Re-derived by `control-mutations.yaml`. |
| `test_the_loader_would_notice_a_violating_set_without_its_negative_pole` | `test_rubric.py` | connected | A violating set that leaves out the negative pole is refused by name. Fails when it loads, which would pass a call whose modal verdict is the pole. Re-derived by `control-mutations.yaml`. |
| `test_the_loader_would_notice_a_violating_set_naming_every_verdict` | `test_rubric.py` | connected | A violating set naming every member of the scale is refused by name. Fails when it loads, which would fail every call whatever the judge answers. Re-derived by `control-mutations.yaml`. |

**The catch-record pin beside them is not a control.**
`test_every_traced_finding_is_caught_or_missed_as_recorded` holds, for every judged entry, whether
its modal verdict on each traced finding's call counts against its gate in the committed log, read
through the roll-up's own `violated` rather than a copy of its rule (D162, P4-22), so a finding newly
caught or newly missed fails by name. What it detects is a change rather than a defect,
and updating it is a reading of what moved.

### D163: answers the schema requires to name something, 2026-09-13

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_the_engine_would_notice_an_uncited_answer_read_as_applicable` | `test_judge_engine.py` | connected | An answer citing nothing spends the one informed retry and, citing nothing again, resolves to `errored`; cited on the retry, it is an applicable verdict carrying a cited line (D163). Fails when `parse_answer` accepts an empty `citations` list, which let an uncited verdict pass the evidence guard on its rationale line and count against the gate (P4-23). Re-derived by `control-mutations.yaml`. |
| `test_the_engine_would_notice_a_synthesis_resting_on_nothing_read_as_applicable` | `test_judge_engine.py` | connected | A synthesis answer whose `rests_on` is empty spends the one informed retry and, empty again, resolves to `errored`; resting on a listed dimension on the retry, it is an applicable verdict with no defect beside it (D163). Fails when the engine accepts an empty `rests_on`, which left a synthesis resting on nothing standing clean. Re-derived by `control-mutations.yaml`. |

### D164: retries that name what they correct, 2026-09-13

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_the_retry_would_notice_a_schema_failure_it_does_not_name` | `test_judge_engine.py` | connected | A retry sent for invalid JSON, or for an answer whose `citations` list is empty, names that failure beside the wording it always had (D164). Fails when the correction drops the failure the engine found, which sent an answer that parsed guidance about prose and code fences and never said which list came back empty (P4-27). Re-derived by `control-mutations.yaml`. |
| `test_the_retry_would_notice_a_synthesis_not_shown_the_dimensions_it_may_rest_on` | `test_judge_engine.py` | connected | A synthesis corrected because its `rests_on` came back empty is shown the dimension identifiers its prompt listed, bare, and asked to rest only on them, while a synthesis corrected for rejected identifiers keeps the wording every recorded retry has (D164). Fails when the dimension list is dropped, which told a synthesis resting on nothing to cite transcript lines (P4-27). Re-derived by `control-mutations.yaml`. |

### D165: a schema that asks only for what the prompt listed, 2026-09-13

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_the_schema_would_notice_a_synthesis_shown_no_dimension_asked_to_rest_on_one` | `test_judge_engine.py` | connected | A synthesis shown no dimension is sent a schema without `rests_on`, and its verdict stands with nothing unresolved and no retry, while a synthesis shown dimensions keeps `rests_on` with `minItems: 1` (D165). Fails when the schema follows the entry alone, which held a synthesis told not to invent a dimension identifier to naming one, so any name it gave was a defect the harness caused (P4-28). Re-derived by `control-mutations.yaml`. |

### After the freeze — the phase-4 audit's obligations, 2026-09-13

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_the_workflow_runs_every_phase_verifier_and_the_inventory` | `test_phase3_acceptance.py` | connected | CI runs every verifier `VERIFIERS` declares, read from that table in either spelling a step uses, beside the statement inventory and the control gate (OB-27). Fails when the phase-4 verifier's step is removed from the workflow, which the test's own list of three verifiers let through (P4-10). Re-derived by `control-mutations.yaml`, once for phase 4's step and once for phase 5's (D176). |
| `test_the_report_would_notice_its_path_reading_a_credential` | `test_report.py` | connected | The report is produced in full, in process, while every route to a credential raises: both functions the CLI imports and `read_dotenv`, the one reader of `.env` they share (OB-29). Fails when the report path reads the credential values, which the subprocess test beside it passes through, because running from an empty directory never put the checkout's `.env` out of reach (P4-12). Re-derived by `control-mutations.yaml`. |
| `test_the_ceiling_would_notice_an_entry_lowered_to_where_it_truncated` | `test_reference_run.py` | connected | Every entry `OBSERVED_TRUNCATIONS` names declares a ceiling above the output length a recording of it was cut at, which for the synthesis is D155's 8,192 on CALL-08 (OB-31). Fails when the synthesis returns to 8192, which every test reading the committed log passes, since the recording that truncated was never committed (P4-14). Re-derived by `control-mutations.yaml`. |
| `test_the_trigger_check_would_notice_a_fired_trigger_left_unacknowledged` | `test_obligations.py` | connected | The check that reads each deferred row's trigger against git refuses, over planted rows, a fired tag the row does not acknowledge, an acknowledgement of a tag that does not exist, and a trigger nothing can observe that does not say a person reads it (D166, OB-32). Fails when a tag's existence goes uncompared with its acknowledgement, which is how the tag fired 13 rows with nothing noticing (P4-15). Re-derived by `control-mutations.yaml`. |
| `test_the_reader_would_notice_a_torn_line_escaping_as_a_decode_error` | `test_transport.py` | connected | A run-log line cut off mid-write is refused as `RunLogFormatError` naming the file and the line, by the strict reader and, for a torn line with complete records after it, by a resume's reading too (OB-28, D167). Fails when the parser's own error escapes, which made replay and report exit 1 with a traceback and a resume refuse naming no file (P4-11). Re-derived by `control-mutations.yaml`. |
| `test_a_resume_would_notice_its_torn_tail_refused_instead_of_dropped` | `test_transport.py` | connected | A resume's reading drops a torn final line and counts it, returning every complete record before it, where the strict reader refuses the same file (OB-28, D167). Fails when that reading refuses the torn tail too, which would refuse every log a run that stopped mid-write leaves. Re-derived by `control-mutations.yaml`. |
| `test_a_resume_would_notice_a_log_answering_no_dimension_request_run_anyway` | `test_cli.py` | connected | A resume log answering none of the dimension requests the run would send is refused before any confirmation, with no log written, where a judged entry was edited under an unchanged rubric version (OB-24, D168). Fails when the refusal is removed, which let such a resume issue every call under a header naming a session that served nothing (P4-4). Re-derived by `control-mutations.yaml`. |
| `test_a_resume_under_an_edited_entry_would_notice_its_counts_misprinted` | `test_cli.py` | connected | A resume under one edited entry prints how many dimension requests its log answers before the confirmation, and how many answers it served and calls it issued when the run ends, each equal to a count taken from the logs (OB-24, D168). Fails when either count is misprinted, the served one as 0 or the pre-flight's as every request, where the command used to print only how many answers the log held (P4-4). Re-derived by `control-mutations.yaml`, once per count. |
| `test_the_expected_figure_would_notice_recorded_retries_left_out` | `test_cli.py` | connected | Each entry's calls are priced at the retry share its log recorded: an entry retrying a quarter of its calls is priced at a quarter more, and one never retrying or given no share at none (OB-33, D170). Fails when the share is dropped from the price, which priced first attempts alone and left the synthesis's retries to the input side's over-estimate (P4-16). Re-derived by `control-mutations.yaml`. |
| `test_the_retry_share_would_notice_the_retries_a_log_records_uncounted` | `test_reference_run.py` | connected | The share the expected figure multiplies calls by is one plus each entry's informed retries over its first attempts, counted here from the committed log's raw call records (OB-33, D170). Fails when every share is left at one, which reads a log whose synthesis retried as one where nothing did (P4-16). Re-derived by `control-mutations.yaml`. |
| `test_the_expected_figure_would_notice_a_stale_log_left_unflagged` | `test_cli.py` | connected | A reference log recorded under another rubric version still prices the figure, and the line beside it names the difference the way replay names it (OB-33, D170). Fails when the comparison is skipped, which priced a run on lengths recorded under another rubric or template and said nothing of it (P4-16). Re-derived by `control-mutations.yaml`. |
| `test_the_cut_check_would_notice_a_cut_named_outside_the_three` | `test_findings.py` | connected | A cut is one of the three boundaries between the four bands, and one named anything else is refused by its position and name (OB-25, D171). Fails when the name goes unread, which accepted `nonsense` beside the tool's three (P4-5). Re-derived by `control-mutations.yaml`. |
| `test_the_cut_check_would_notice_a_cut_named_twice` | `test_findings.py` | connected | A cut stated twice is refused, as the producing tool refuses it (OB-25, D171). Fails when the second is accepted, which leaves whichever is read last to place the band. Re-derived by `control-mutations.yaml`. |
| `test_the_cut_check_would_notice_an_inverted_or_single_anchor_cut` | `test_findings.py` | connected | A cut whose anchors the file's own `theta` inverts, and one anchored on a single finding, are both refused as inverted (OB-25, D171). Fails when the comparison is skipped, which accepted both with a gap and a between-set consistent with their rows (P4-5). Re-derived by `control-mutations.yaml`. |
| `test_the_cut_check_would_notice_a_missing_cut` | `test_findings.py` | connected | A file stating no cuts, or two of the three, is refused by the names it lacks (OB-25, D171). Fails when the absence goes unchecked, which read an empty list as a file stating no cuts, a file the tool never exports. Re-derived by `control-mutations.yaml`. |
| `test_the_cut_check_would_notice_boundaries_that_have_crossed` | `test_findings.py` | connected | Three cuts each valid alone, with their midpoints out of severity order, are refused as two boundaries crossed (OB-25, D171). Fails when the midpoints go uncompared, which no check of a single cut can stand in for. Re-derived by `control-mutations.yaml`. |
| `test_the_band_check_would_notice_a_row_on_the_wrong_side_of_its_cuts_midpoint` | `test_findings.py` | connected | A row whose `theta` crosses its cut's midpoint while staying between that cut's anchors, its band unchanged, is refused naming the band it states and the band its `theta` gives (OB-25, D171). Fails when the band goes uncompared, which is how the re-verification moved F-29 across `medium_low` past the loader and every pin (P4-5). Re-derived by `control-mutations.yaml`. |
| `test_the_band_check_would_notice_a_row_on_a_midpoint_banded_up` | `test_findings.py` | connected | A `theta` exactly on a midpoint belongs to the less severe band, as the tool bands it: banded down the file is accepted and banded up it is refused (D171). Fails when a tie counts upward, which refuses a file the tool writes and accepts one it could not. Re-derived by `control-mutations.yaml`. |
| `test_a_band_outside_the_vocabulary_is_refused` | `test_findings.py` | connected | A band nobody defined is refused by the join's vocabulary check and named as outside the vocabulary, not as misplaced by the band check (D171). Fails when the band check reaches it first, which refuses it for the wrong reason. Re-derived by `control-mutations.yaml`. |

### D173: the labels manifest a held-out run names, 2026-09-14

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_a_header_carries_the_labels_manifest_a_held_out_run_names` | `test_transport.py` | connected | A header naming no labels manifest writes no key, and a held-out run's header writes its manifest and reads back with it (D173). Fails when the writer leaves the manifest out or the reader drops it, either of which leaves a held-out log the held-out repository's gate refuses. Re-derived by `control-mutations.yaml`, once per half. |
| `test_the_manifest_check_would_notice_a_log_naming_other_labels` | `test_transport.py` | connected | A log naming another manifest, none where the run names one, or one where the run names none is refused naming both, and equal manifests pass (D173). Fails when the manifests go uncompared, which served answers sealed against other labels under a header naming the run's. Re-derived by `control-mutations.yaml`. |
| `test_a_held_out_resume_would_notice_a_log_naming_other_labels` | `test_cli.py` | connected | A held-out resume whose log names another manifest, or none, is refused naming it before any confirmation, and writes no log (D173). Fails when a resume skips the check, which reached the confirmation for a log whose header would name labels its answers were not recorded under. Re-derived by `control-mutations.yaml`. |
| `test_a_held_out_replay_would_notice_a_log_naming_other_labels` | `test_cli.py` | connected | A held-out replay whose log names another manifest is refused before anything is served, and writes no log (D173). Fails when a replay skips the check, which wrote a log naming one manifest over answers recorded under another. Re-derived by `control-mutations.yaml`. |
| `test_a_held_out_replay_writes_its_labels_manifest_into_the_log` | `test_cli.py` | connected | A replay over calls `HELDOUT_SET` declares, given the manifest its log names, completes and writes a log whose header names it (D173). Fails when the header is built without the flag, which the replay then refuses as a log naming other labels, and which on a live run writes a log naming none. Re-derived by `control-mutations.yaml`. |
| `test_a_held_out_run_would_notice_its_labels_manifest_missing` | `test_cli.py` | connected | A judged run over calls `HELDOUT_SET` declares, with no `--labels-manifest`, is refused naming the flag it needs, and writes no log (D173). Fails when no call is recognized as held out, when the missing flag is refused as a malformed one, or when the command ignores the check. Re-derived by `control-mutations.yaml`, once per defect. |
| `test_a_run_mixing_held_out_and_design_calls_would_be_noticed` | `test_cli.py` | connected | A run reading one call `HELDOUT_SET` declares beside calls it does not is refused with a well-formed manifest given, and writes no log (D173). Fails when the mix goes ahead, which puts design calls under a header naming held-out labels. Re-derived by `control-mutations.yaml`. |
| `test_a_design_run_would_notice_a_labels_manifest_it_has_no_use_for` | `test_cli.py` | connected | A run over no call `HELDOUT_SET` declares is refused the flag, and writes no log (D173). Fails when a design run takes it, which lets a manifest in a header mark a log that is not held out. Re-derived by `control-mutations.yaml`. |
| `test_a_malformed_labels_manifest_would_be_noticed` | `test_cli.py` | connected | An uppercase, a shortened and an overlong value are each refused as not a full commit SHA (D173). Fails when the shape goes unchecked, which lets any value through to a held-out log's header. Re-derived by `control-mutations.yaml`. |
| `test_a_judged_run_would_notice_its_held_out_set_missing` | `test_cli.py` | connected | With no `HELDOUT_SET` where the run reads it, a judged run is refused rather than read as declaring nothing, and writes no log (D173). Fails when a missing file reads as empty, which lets a held-out run go unrecognized and write a log naming no manifest. Re-derived by `control-mutations.yaml`. |

### D174: a held-out run's paths, and its log, kept out of the tree, 2026-09-14

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_a_held_out_run_would_notice_a_path_inside_the_checkout` | `test_cli.py` | connected | A held-out replay is refused its transcripts, its log directory or the log it replays when that path resolves inside the checkout, each refusal naming its flag, and nothing is written (D174). Fails when any of the three goes unchecked, when no path is compared or the refusal is ignored, or when the run is not recognized as held out for the check, any of which lets a held-out run left on defaults read and write inside this tree. Re-derived by `control-mutations.yaml`, once per defect. |
| `test_a_held_out_resume_would_notice_its_log_inside_the_checkout` | `test_cli.py` | connected | A held-out resume is refused a log inside the checkout before the log is read and before any confirmation (D174). Fails when `--resume` goes unchecked, which reads the log and is refused later, for another reason. Re-derived by `control-mutations.yaml`. |
| `test_a_held_out_run_log_is_found_by_its_header` | `test_holdout_absence.py` | connected | A file whose run-log header names a labels manifest is reported, the header alone being enough (D174). Fails when the header goes unread, which leaves a whole held-out log in the tree unseen. Re-derived by `control-mutations.yaml`. |
| `test_a_held_out_call_record_is_found_wherever_it_is_pasted` | `test_holdout_absence.py` | connected | A call record citing a call `HELDOUT_SET` declares, re-serialized compactly and pasted into a scratch script with no header, is reported (D174). Fails when call records go unread, which leaves records copied out of a held-out log unseen. Re-derived by `control-mutations.yaml`. |
| `test_a_design_run_log_is_not_mistaken_for_a_held_out_one` | `test_holdout_absence.py` | connected | A design log, whose header names no manifest and whose records cite design calls, and a document naming the key in prose, are both left alone (D174). Fails when a call record is reported whatever call it cites, which fails the check on every design log in `runs/`. Re-derived by `control-mutations.yaml`. |
| `test_a_held_out_record_past_the_window_or_the_cap_is_still_found` | `test_holdout_absence.py` | connected | A held-out record past a file's first 64 KB, and one in a file over 2 MB, are both reported (D174). Fails when the transcript scan's window or its cap is applied to this reading, which leaves a design-size log unread. Re-derived by `control-mutations.yaml`, once for each. |
| `test_the_check_reports_a_held_out_run_log_in_the_tree_it_scans` | `test_holdout_absence.py` | connected | The check fails over a tree holding a held-out run log, naming the file and what marks it, in a held-out transcript's words (D174). Fails when the check leaves run logs out of its problems, which leaves what the scan finds reported by nothing. Re-derived by `control-mutations.yaml`. |

### D175: judge-versus-label agreement, design set and held-out set apart, 2026-09-15

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_agreement_would_notice_its_counts_read_in_one_direction` | `test_agreement.py` | connected | An entry's calls fall into hits, misses, false alarms and correct silences, and a call with no verdict is counted apart by status, the five summing to the set's calls (D175). Fails when a fired call is a hit wherever it sits, when a silent traced call is a correct silence, or when a call with no verdict is counted as answered. Re-derived by `control-mutations.yaml`, once per defect. |
| `test_agreement_would_notice_a_call_left_without_a_reading` | `test_agreement.py` | connected | A call the entry has no result for refuses the count by name (D175). Fails when the refusal is skipped, which fails on that call unnamed. Re-derived by `control-mutations.yaml`. |
| `test_a_judged_entry_would_notice_its_middle_verdict_read_as_a_pass` | `test_agreement.py` | connected | A judged entry fires where its gate reads a violation, a middle verdict it counts included, and a call with no applicable repetition reads as its most frequent status (D160, D175). Fails when only the negative pole fires. Re-derived by `control-mutations.yaml`. |
| `test_the_traces_file_would_notice_a_key_missing_or_added` | `test_agreement.py` | connected | A `traces.yaml` holds exactly its four keys, and one missing or one more is refused (D175). Fails when the keys go uncompared. Re-derived by `control-mutations.yaml`. |
| `test_the_held_out_labels_would_notice_each_broken_invariant` | `test_agreement.py` | connected | Each invariant the held-out validator states, broken alone, is refused by name, and the unbroken labels are accepted (D175). Fails when any one of the eleven checks is skipped. Re-derived by `control-mutations.yaml`, once per invariant. |
| `test_agreement_would_notice_its_design_section_miscounted` | `test_cli.py` | connected | `harness agreement` prints the design section over the committed log, where `A-record-fields-disagree` scores one hit, no miss and no false alarm over sixteen calls, and says the held-out section was not computed (D175). Fails when deterministic entries never fire, when the design traces are left empty, or when the section is not printed. Re-derived by `control-mutations.yaml`, once per defect. |
| `test_agreement_would_notice_its_held_out_section_left_out` | `test_cli.py` | connected | With all five held-out inputs, over invented labels on a split design corpus, the held-out section is printed over its own eight calls, with the traced entry scoring its hit (D175). Fails when the held-out traces are left empty or the section is not printed. Re-derived by `control-mutations.yaml`, once per defect. |
| `test_agreement_would_notice_held_out_inputs_given_in_part` | `test_cli.py` | connected | Some held-out inputs without the rest are refused, naming the missing ones, before anything is read (D175). Fails when the partial set is accepted. Re-derived by `control-mutations.yaml`. |
| `test_agreement_would_notice_a_held_out_input_inside_the_checkout` | `test_cli.py` | connected | A held-out input resolving inside the checkout is refused before anything is read (D174, D175). Fails when no input is compared with the checkout or the refusal is ignored. Re-derived by `control-mutations.yaml`, once per defect. |
| `test_agreement_would_notice_design_calls_declared_held_out` | `test_cli.py` | connected | A design corpus holding a call `HELDOUT_SET` declares is refused (D175). Fails when the design section scores it. Re-derived by `control-mutations.yaml`. |
| `test_agreement_would_notice_a_held_out_set_holding_an_undeclared_call` | `test_cli.py` | connected | Held-out transcripts holding a call `HELDOUT_SET` does not declare are refused as not the held-out set (D173, D175). Fails when they are read as held out. Re-derived by `control-mutations.yaml`. |
| `test_agreement_would_notice_a_held_out_log_naming_no_manifest` | `test_cli.py` | connected | A held-out log whose header names no labels manifest is refused (D173, D175). Fails when it is scored. Re-derived by `control-mutations.yaml`. |
| `test_agreement_would_notice_held_out_labels_breaking_an_invariant` | `test_cli.py` | connected | The command refuses held-out labels whose traces name another frozen commit, not only the function it calls (D175). Fails when the command skips the check. Re-derived by `control-mutations.yaml`. |
| `test_agreement_would_notice_a_replay_that_stopped_part_way` | `test_cli.py` | connected | A design log cut in half is refused as a replay that stopped part-way (D175). Fails when the abort is scored over the calls the log still answers. Re-derived by `control-mutations.yaml`. |

### D176: a phase-5 verifier that declares what it cannot tick, 2026-09-15

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_the_claim_check_would_notice_a_declaration_ignored` | `test_phase3_acceptance.py` | connected | Over planted criterion lines, a criterion a declaration names is claimed and one nothing names is not (D176). Fails when declarations are ignored, which reports every declared criterion as claimed by nothing. Re-derived by `control-mutations.yaml`. |
| `test_the_claim_check_would_notice_a_criterion_both_ticked_and_declared` | `test_phase3_acceptance.py` | connected | A criterion an entry ticks and a declaration also names is found, and with no declaration nothing is (D176). Fails when the second claim goes unread, which lets a declaration outlive the build that replaced it. Re-derived by `control-mutations.yaml`. |
| `test_a_declaration_would_notice_each_way_it_cannot_stand` | `test_phase3_acceptance.py` | connected | A declaration naming no criterion, of an unknown kind, giving no reason, or asserted elsewhere without naming where, is refused by name, and a sound one is not (D176). Fails when any one of the four clauses is skipped. Re-derived by `control-mutations.yaml`, once per clause. |
| `test_the_loop_would_notice_its_declarations_left_unprinted` | `test_phase3_acceptance.py` | connected | Over a planted criterion and a planted JUnit report, the shared loop prints each declaration under its own heading with its reason, counts them by kind in its closing line, and exits 0 with them unticked (D176). Fails when the section or the closing count is dropped. Re-derived by `control-mutations.yaml`, once for each. |
| `test_phase_5_declares_the_gate_asserted_criteria_and_the_unbuilt_report` | `test_phase3_acceptance.py` | connected | The phase-5 verifier declares exactly the three criteria the held-out repository's gate asserts, each naming that gate, and the two coverage criteria not yet built (D176). Fails when a declaration's anchor moves off its criterion. Re-derived by `control-mutations.yaml`. |

### D178: the interface scanner reads each list from its sentence, 2026-09-15

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_a_field_named_only_outside_its_list_does_not_count` | `test_check_spec_interface.py` | connected | A field the tool's list lacks is reported missing even when a criterion names it as a subcommand: P4-17, planted (D178). Fails when a list is read from the whole specification, or runs past its sentence to the end of the document. Re-derived by `control-mutations.yaml`, once for each. |
| `test_a_list_sentence_that_is_gone_fails_and_names_it` | `test_check_spec_interface.py` | connected | A list sentence reworded away is a disagreement naming the list and the phrase it looked for (D178). Fails when a missing opening phrase is let through. Re-derived by `control-mutations.yaml`. |
| `test_a_list_sentence_stated_twice_fails` | `test_check_spec_interface.py` | connected | An opening phrase stated twice is a disagreement rather than a reading of the first (D178). Fails when a doubled phrase is accepted. Re-derived by `control-mutations.yaml`. |
| `test_an_extra_name_in_a_list_fails_and_names_it` | `test_check_spec_interface.py` | connected | A name a list sentence carries beyond the scanner's set is reported by name (D178). Fails when extra names go unread. Re-derived by `control-mutations.yaml`. |
| `test_a_struck_earlier_list_beside_the_live_one_passes` | `test_check_spec_interface.py` | connected | A superseded list kept struck through beside the live one is not a second list (D178). Fails when struck text is left in, which doubles the opening phrase. Re-derived by `control-mutations.yaml`. |
| `test_a_record_repeating_a_list_sentence_does_not_double_it` | `test_check_spec_interface.py` | connected | Lists are read from each side's specification alone, so a decision record quoting a list sentence does not double it (D178). Fails when either side's lists are read from every file. Re-derived by `control-mutations.yaml`, once per side. |
| `test_a_matching_pair_of_lists_agrees_exactly` | `test_check_spec_interface.py` | connected | Each list is read from its own span: the harness's field list stops where its row list opens, and its findings list sets the harness-only keys aside (D178). Fails when the close is ignored or those keys are kept. Re-derived by `control-mutations.yaml`, once for each. |
| `test_a_missing_key_reaches_the_whole_check` | `test_check_spec_interface.py` | connected | A key missing from a list is reported by the check a run prints, not only by the comparison beside it (D178). Fails when the check leaves the lists uncompared. Re-derived by `control-mutations.yaml`. |
| `test_a_key_in_neither_list_is_named_as_missing_from_both` | `test_check_spec_interface.py` | connected | A key neither side lists is named as missing from both (D178). Fails when that branch is skipped, which reports nothing. Re-derived by `control-mutations.yaml`. |

### D179: the informed retry names every fault an answer shows, 2026-09-15

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_the_retry_would_notice_a_second_fault_it_does_not_name` | `test_judge_engine.py` | connected | A synthesis citing `T999` with an empty `rests_on` is corrected for both, each in its own words, and shown its dimensions, and a retry fixing both is applicable: P4-30, planted (D179). Fails when an empty `rests_on` goes unchecked beside rejected identifiers, when the correction states one complaint, or when a synthesis with rejected identifiers is not shown its dimensions. Re-derived by `control-mutations.yaml`, once for each. |
| `test_the_retry_would_notice_an_empty_citations_list_hiding_an_empty_rests_on` | `test_judge_engine.py` | connected | With both lists empty, the correction names the empty `citations` and the empty `rests_on` together (D179). Fails when a schema failure stops `rests_on` being checked. Re-derived by `control-mutations.yaml`. |
| `test_the_retry_would_notice_rejected_identifiers_beside_a_missing_field` | `test_judge_engine.py` | connected | A missing field does not hide the identifiers an answer did cite: the correction quotes them beside the missing field (D179). Fails when rejected identifiers are computed only for an answer with no schema failure. Re-derived by `control-mutations.yaml`. |
| `test_an_exhausted_retry_would_notice_a_fault_left_out_of_its_last_failure` | `test_judge_engine.py` | connected | An `errored` result's last failure names every fault the retry still showed, the identifiers first (D179). Fails when it names the first alone. Re-derived by `control-mutations.yaml`. |
| `test_every_readable_fault_is_named_not_the_first` | `test_judge_prompt.py` | connected | Reading a response records a missing field, an empty `citations` and a `rests_on` that is not a list together, and invalid JSON stops the reading at one (D179). Fails when a missing field stops `citations` being read. Re-derived by `control-mutations.yaml`. |

### D180: a verifier's caveat states what its tick does not buy, 2026-09-15

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_the_history_check_would_notice_each_marker` | `test_phase3_acceptance.py` | connected | Over planted caveats, "Added at D130" and "until 2026-09-07" are each found and a limit carrying neither is not (D180). Fails when either marker matches nothing, or when no marker is read. Re-derived by `control-mutations.yaml`, once for each. |

### D182, D184 and D185: held-out output stays out of this tree, 2026-09-15

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_a_held_out_run_would_notice_a_path_inside_the_checkout` | `test_cli.py` | connected | A held-out run is refused its corpus version file inside this checkout, beside the three paths D174 named (D182). Fails when that flag carries no value to compare. Re-derived by `control-mutations.yaml`. |
| `test_a_held_out_runs_log_is_named_for_the_gate_that_admits_it` | `test_cli.py` | connected | A held-out run's log is written under the `heldout-` prefix and a design run's is not, keyed on the header's labels manifest (D184). Fails when every log is named alike. Re-derived by `control-mutations.yaml`. |
| `test_a_report_over_held_out_calls_would_notice_an_out_path_inside_the_checkout` | `test_cli.py` | connected | A report over calls `HELDOUT_SET` declares is refused an `--out` path inside this checkout, and produced outside it and on stdout (D185). Fails when the report reads no declaration, and when the path test is inverted. Re-derived by `control-mutations.yaml`, once for each. |
| `test_a_rendered_report_over_held_out_calls_is_found` | `test_holdout_absence.py` | connected | A rendered report naming a declared call is read as held-out output wherever it sits (D185). Fails when the renderer's heading matches nothing. Re-derived by `control-mutations.yaml`. |
| `test_a_design_report_is_not_mistaken_for_a_held_out_one` | `test_holdout_absence.py` | connected | The heading and a declared call id are required together, so a design report, a document quoting the heading and a file naming a held-out call are all left alone (D185). Fails when any call id counts. Re-derived by `control-mutations.yaml`. |

### D183 and D186: a held-out run's header names the rubric it judged under, 2026-09-16

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_a_held_out_replay_writes_the_rubric_it_judged_under` | `test_cli.py` | connected | A held-out run's log carries a hash of the rubric on disk, recomputed in the test rather than read off the run (D183). Fails when the run writes no hash. Re-derived by `control-mutations.yaml`. |
| `test_the_rubric_check_would_notice_a_log_judged_under_another_rubric` | `test_transport.py` | connected | A log naming another rubric, none where the run names one, and one where the run names none are all refused, with equal hashes passing (D183). Fails when the comparison is inverted. Re-derived by `control-mutations.yaml`. |

| `test_a_held_out_replay_would_notice_a_log_judged_under_another_rubric` | `test_cli.py` | connected | The command refuses a held-out replay whose log names another rubric, before anything is served and with no log written (D183). Fails under the same inverted comparison, which the register names twice rather than letting the second look independently proven. Re-derived by `control-mutations.yaml`. |

**The pin has no control**, and the reason is the tag pin's: `test_the_rubric_and_the_template_at_head_are_the_frozen_commits` asks git what the freeze commit holds, and the control gate runs in a copy of the tree with no `.git`. It is a test rather than a control, recorded here so the absence is a decision rather than a gap (D186).

### D188: coverage by severity, design set and held-out set apart, 2026-09-18

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_coverage_would_notice_a_finding_read_in_the_wrong_state` | `test_coverage.py` | connected | Over planted readings of the design set, a finding is retired where an entry traced to it fired on its call, missed where every such entry was silent or gave no verdict, with each entry's reading named, and uncovered where none is traced to it (D188). Fails when every traced finding reads as retired, when an untraced one reads as missed, or when an entry that errored reads as silent. Re-derived by `control-mutations.yaml`, once per defect. |
| `test_coverage_would_notice_its_bands_pooled_or_its_findings_misbanded` | `test_coverage.py` | connected | Each band holds the findings its severity file puts there, most severe first, and an entry firing on one critical call moves the critical band alone (D157, D188). Fails when every finding lands in one band. Re-derived by `control-mutations.yaml`. |
| `test_coverage_would_notice_an_unbanded_finding_left_out_or_counted_twice` | `test_coverage.py` | connected | Question-tier findings and unplaced ones are each named in a group of their own, over an invented export that moves one finding to `unplaced` (D187, D188). Fails when an unplaced finding is also counted question-tier, or when neither group is named. Re-derived by `control-mutations.yaml`, once per defect. |
| `test_coverage_would_notice_an_input_it_cannot_cover` | `test_coverage.py` | connected | A traced id the set does not hold, a finding on a call it does not read and an entry with no reading for one of its calls are each refused by name (D188). Fails when any of the three refusals is skipped. Re-derived by `control-mutations.yaml`, once per refusal. |
| `test_the_coverage_section_would_notice_its_bands_pooled` | `test_coverage.py` | connected | The rendered section has one row per band and no total across them (D157, D188). Fails when it prints one band's row. Re-derived by `control-mutations.yaml`. |
| `test_coverage_would_notice_its_design_section_miscounted` | `test_cli.py` | connected | `harness coverage` over the committed log and export reads critical 3 of 4 retired, high 14 of 14, medium 27 of 28 and low 32 of 37, names F-76 among the uncovered and F-85 as missed, and names the question-tier findings (D188). Fails when every traced finding is retired, when the uncovered set is not named, or when the section is not printed. Re-derived by `control-mutations.yaml`, once per defect. |
| `test_coverage_would_notice_its_held_out_section_left_out` | `test_cli.py` | connected | With all six held-out inputs, over invented labels on renamed copies of the design calls with F-04 left untraced, the held-out section is printed beside the design one, its critical band at 2 of 4 and no design id in it (D177, D188). Fails when the section is not printed, or when it is read against the design traces or banded by the design export. Re-derived by `control-mutations.yaml`, once per defect. |
| `test_coverage_would_notice_held_out_inputs_given_in_part` | `test_cli.py` | connected | Five held-out inputs without the severity export are refused naming it (D175, D188). Fails when the partial set is accepted, or when the severity export is left off the list. Re-derived by `control-mutations.yaml`, once per defect. |
| `test_coverage_would_notice_a_held_out_input_inside_the_checkout` | `test_cli.py` | connected | A held-out severity export inside the checkout is refused before anything is read (D174, D188). Fails when no input is compared with the checkout, when the refusal is ignored, or when the severity export is left off the list. Re-derived by `control-mutations.yaml`, once per defect. |
| `test_coverage_would_notice_a_severity_file_its_join_refuses` | `test_cli.py` | connected | A design export that no longer names a defect-tier finding is refused by the join (D188). Fails when the join lets the finding through. Re-derived by `control-mutations.yaml`. |
| `test_coverage_would_notice_a_finding_on_a_call_its_set_does_not_read` | `test_cli.py` | connected | Design transcripts missing a call its findings sit on are refused naming the call (D188). Fails when the refusal is skipped. Re-derived by `control-mutations.yaml`. |
| `test_coverage_would_notice_each_refusal_it_shares_with_agreement` | `test_cli.py` | connected | Design calls `HELDOUT_SET` declares, held-out transcripts holding an undeclared call, a held-out log naming no manifest, labels naming another frozen commit and a replay that stopped part-way are each refused by the coverage command (D175, D188). Fails when any one of the five is skipped. Re-derived by `control-mutations.yaml`, once per refusal. |
| `test_coverage_would_notice_an_out_flag_that_writes_a_file` | `test_cli.py` | connected | The command has no `--out`, so a held-out section goes to stdout alone and nothing is written where one pointed (D188). Fails when the command takes the flag. Re-derived by `control-mutations.yaml`. |
| `test_a_coverage_report_over_held_out_findings_is_found` | `test_holdout_absence.py` | connected | A section the shipped renderer writes, naming an invented held-out finding, is reported wherever it is pasted (D188). Fails when the coverage heading matches nothing. Re-derived by `control-mutations.yaml`. |
| `test_a_design_coverage_report_is_not_mistaken_for_a_held_out_one` | `test_holdout_absence.py` | connected | The heading and a held-out finding's id are required together, so a design section, prose quoting the heading beside a held-out id, and a file naming one alone are all left alone (D188). Fails when any finding id counts. Re-derived by `control-mutations.yaml`. |
| `test_the_check_reports_a_coverage_report_in_the_tree_it_scans` | `test_holdout_absence.py` | connected | The check fails over a tree holding a held-out coverage section, naming the file and the finding, in a held-out transcript's words (D188). Fails when the check leaves coverage reports out of its problems. Re-derived by `control-mutations.yaml`. |

**Two of agreement's controls moved with the code they drive.** The refusal of held-out inputs given in part and the label check now sit in helpers both commands call, so `test_agreement_would_notice_held_out_inputs_given_in_part` and `test_agreement_would_notice_held_out_labels_breaking_an_invariant` anchor on the helpers' lines, and the coverage command's controls anchor on the same ones (D188).

### D189: the content-hash recheck in the harness, 2026-09-18

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_the_recheck_would_notice_a_finding_edited_after_scoring` | `test_findings.py` | connected | The harness's recheck names exactly the finding whose observation lost a word, passes over whitespace the tool's hash strips, and passes over a row the findings do not hold (D140, D189). Fails when the recheck compares nothing, or when the hash stops stripping evidence fragments. Re-derived by `control-mutations.yaml`, once per defect. |
| `test_coverage_would_notice_a_band_on_text_that_moved` | `test_coverage.py` | connected | A set holding a band on a finding edited after scoring is refused, naming the finding (D189). Fails when the recheck compares nothing, or when coverage never asks it. Re-derived by `control-mutations.yaml`, once per defect. |
| `test_coverage_would_notice_a_findings_file_edited_after_scoring` | `test_cli.py` | connected | `harness coverage` refuses a findings file edited after its bands were placed, naming the finding (D140, D189). Fails when the recheck compares nothing, or when coverage never asks it. Re-derived by `control-mutations.yaml`, once per defect. |

**The suite's own hash test gains a second mutation.** `test_every_scored_finding_still_matches_the_text_it_was_scored_against` now reads `finding_content_hash` rather than a copy kept in the test, so a mutation to the harness's definition drives it red beside the edited finding its first entry plants (D148, D189).

### D192: coverage split by detection type within each band, 2026-09-18

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_coverage_would_notice_a_band_split_wrong_by_detection_type` | `test_coverage.py` | connected | Each band splits into its assert-, judge- and human-type findings, each with its own holds, traced and retired, the parts adding up to the band, and firing on one assert-type critical finding moves only that part (D192). Fails when every part holds the whole band. Re-derived by `control-mutations.yaml`. |

**Three D188 controls now also hold the split.** `test_the_coverage_section_would_notice_its_bands_pooled` requires three detection-type rows under each band and still no total across bands; `test_coverage_would_notice_its_design_section_miscounted` pins the design set's critical and low splits; and `test_coverage_would_notice_its_held_out_section_left_out` pins the critical split the untraced invented finding moves. Each is re-derived by a further entry in `control-mutations.yaml` (D192).

### D193: the register declares the values it names, 2026-09-18

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_the_register_would_notice_an_identifier_of_an_undeclared_shape` | `test_corpus_hygiene.py` | connected | Every identifier-shaped token in a design transcript matches a shape Class 2 of `corpus/entities.md` declares, and a planted undeclared shape is reported (D193). Fails when no token is compared, and when the register loses the refund or the specialist identifier's shape. Re-derived by `control-mutations.yaml`, once per defect. |
| `test_the_register_would_notice_a_settlement_token_it_does_not_declare` | `test_corpus_hygiene.py` | connected | Every `settlement=` value a tool result names is a token Class 5 declares, and a planted undeclared processor is reported (D193). Fails when no settlement is compared, and when Class 5 names Cardinal Pay without its token. Re-derived by `control-mutations.yaml`, once per defect. |

### D194: a sweep marker that names a sweep, 2026-09-19

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_the_sweep_marker_names_a_changelog_entry_that_records_a_sweep` | `test_document_counts.py` | connected | From 0.55.0 the `Last swept` marker names a version whose changelog entry says it records a sweep, and a planted marker naming a decision's entry is refused (D194). Fails when the entry is never read for a sweep, and when every marker is read as history from before the rule. Re-derived by `control-mutations.yaml`, once per defect. |

### D195: the absence check reads every encoding, fails closed, and reads what it had no reading for, 2026-09-19

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_every_reading_finds_its_artifact_as_a_powershell_redirect_writes_it` | `test_holdout_absence.py` | connected | Every shape the check reads -- transcript, run log, report, coverage section, labels and agreement's section -- is found in UTF-16 and in UTF-8 with a byte-order mark, the two encodings a PowerShell redirect writes here, with plain UTF-8 as the positive control (D195). Fails when either mark is decoded as plain UTF-8. Re-derived by `control-mutations.yaml`, once per encoding. |
| `test_a_file_no_reading_can_decode_is_reported_rather_than_skipped` | `test_holdout_absence.py` | connected | A file with no binary suffix that decodes as neither UTF-8 nor UTF-16 is reported, and a binary file by name and a UTF-16 one are not (D195). Fails when an undecodable file is skipped, and when binary files are decoded too. Re-derived by `control-mutations.yaml`, once per defect. |
| `test_a_run_log_record_laid_out_across_lines_is_found` | `test_holdout_absence.py` | connected | A held-out header and call record pretty-printed across lines are found, and a design record laid out the same way is not (D195). Fails when either is not read as a JSON value. Re-derived by `control-mutations.yaml`, once per defect. |
| `test_an_extraction_artifact_over_a_declared_call_is_found` | `test_holdout_absence.py` | connected | An extraction artifact over a declared call, written by the shipped writer, is found, and the design artifact is not (D195). Fails when a JSON object naming a declared call is not reported. Re-derived by `control-mutations.yaml`, once. |
| `test_held_out_labels_are_found_in_their_own_structure` | `test_holdout_absence.py` | connected | The held-out findings, traces and severity files and a findings view over them are each found in their own structure (D195). Fails when a mapping's id, a traces file's lists or a view's heading is not read. Re-derived by `control-mutations.yaml`, once per defect. |
| `test_design_labels_or_a_document_naming_a_held_out_id_are_not_mistaken_for_held_out_ones` | `test_holdout_absence.py` | connected | The design label files and view, a document naming a held-out id in prose and code holding one are not reported (D195). Fails when any mapping in a file naming such an id is read as a label. Re-derived by `control-mutations.yaml`, once. |
| `test_agreements_held_out_section_is_found_and_its_design_section_is_not` | `test_holdout_absence.py` | connected | Agreement's held-out section is found wherever it is pasted, and its design section is not (D195). Fails when the heading is matched only at the start of a file. Re-derived by `control-mutations.yaml`, once. |
| `test_the_check_reports_labels_agreement_and_an_undecodable_file_in_the_tree_it_scans` | `test_holdout_absence.py` | connected | The check itself reports held-out labels, agreement's held-out section and a file it cannot decode, by name (D195). Fails when any of the three loops in `main()` is unwired while its scan stays tested. Re-derived by `control-mutations.yaml`, once per loop. |
| `test_tool_generated_trees_are_skipped` | `test_holdout_absence.py` | connected | A transcript under `.git`, `.venv`, `__pycache__` or `.pytest_cache` is not reported; D195 made the walk prune those trees rather than enter and filter them. Fails when the walk enters them. Re-derived by `control-mutations.yaml`, once. |

`test_a_held_out_run_log_is_found_by_its_header` now also plants its header on a line of `grep` output, where it starts no line: D195's JSON reading reads a whole log's header too, so without that second plant its entry left the test green.

### D196: extraction and the findings view keep held-out content out of this tree, 2026-09-19

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_extraction_over_a_declared_call_refuses_an_out_path_inside_the_checkout` | `test_held_out_writes.py` | connected | An extraction artifact over a call `HELDOUT_SET` declares is refused an `--out` path inside the checkout, with nothing written, and is produced outside it (D196). Fails when extraction never asks whether its calls are held out. Re-derived by `control-mutations.yaml`, once. |
| `test_extraction_over_the_design_set_still_writes_inside_the_checkout` | `test_held_out_writes.py` | connected | The design artifact, which CI writes into `build/` on every run, is not refused (D196). Fails when output that is not held out is refused too. Re-derived by `control-mutations.yaml`, once. |
| `test_extraction_is_refused_when_the_declaration_cannot_be_read` | `test_held_out_writes.py` | connected | Extraction refuses when `HELDOUT_SET` cannot be read, rather than assuming its calls are not held out (D173, D196). Fails when a missing declaration reads as an empty set. Re-derived by `control-mutations.yaml`, once. |
| `test_the_view_over_held_out_labels_refuses_an_out_path_inside_the_checkout` | `test_held_out_writes.py` | connected | A findings view over held-out labels is refused an `--out` path inside the checkout, by the finding's call and by its id's shape (D196). Fails when the view asks neither. Re-derived by `control-mutations.yaml`, once per mark. |
| `test_the_design_view_still_writes_inside_the_checkout_and_check_is_not_refused` | `test_held_out_writes.py` | connected | The design view still writes inside the checkout, and `--check`, which writes nothing, is not refused (D196). Fails when the refusal runs for `--check` too. Re-derived by `control-mutations.yaml`, once. |
| `test_the_refusal_reads_both_halves_of_its_rule` | `test_held_out_writes.py` | connected | The shared refusal needs both halves: held-out content, and a destination inside the checkout (D196). Fails when a destination outside it is refused as well. Re-derived by `control-mutations.yaml`, once. |

### D197: the commands that score the labels read the rubric their log names, 2026-09-19

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_agreement_and_coverage_refuse_a_held_out_log_judged_under_another_rubric` | `test_cli.py` | connected | `harness agreement` and `harness coverage` refuse a held-out log whose header names another rubric's hash or none, and compute over the log as recorded (D197). Fails when neither compares the hash. Re-derived by `control-mutations.yaml`, once. |

### The phase-5 audit's P5-16: a damaged log refused by name, 2026-09-19

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_a_header_missing_a_field_is_refused_as_a_damaged_log` | `test_transport.py` | connected | A run log whose header carries no `artifact_hash` raises `RunLogFormatError` naming the field, rather than a `KeyError`: the file is damaged, which is neither a cache miss nor staleness. Fails when the reading no longer catches a missing key. Re-derived by `control-mutations.yaml`, once. |
| `test_the_log_reading_commands_refuse_a_damaged_header_and_offer_no_flag_they_lack` | `test_cli.py` | connected | `harness agreement`, `harness coverage` and `harness report` refuse a damaged header with exit 2 rather than a traceback, and the two measurement commands' staleness refusal names `--run-log` in place of the `--allow-stale-replay` neither takes. Fails when the refusal is not reworded for them. Re-derived by `control-mutations.yaml`, once. |

### The phase-5 audit's P5-6: the checks that had no control, 2026-09-19

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_the_check_reports_a_rendered_report_in_the_tree_it_scans` | `test_holdout_absence.py` | connected | The check itself reports a rendered report over a held-out call, not only the scan that finds one (D185). Fails when the loop in `main()` is unwired, which its two function-level tests cannot see. Re-derived by `control-mutations.yaml`, once. |
| `test_agreement_and_coverage_read_the_held_out_policies_they_are_given` | `test_cli.py` | connected | `--held-out-policies` is read by both commands: the design policies given explicitly compute the held-out section, and a directory holding none is refused (D175, D188). Fails when the flag is ignored. Re-derived by `control-mutations.yaml`, once. |
| `test_coverage_refuses_an_entry_with_no_traces_row_and_one_with_no_readings` | `test_coverage.py` | connected | A rubric entry with no traces row, and one with no readings, are each refused by name rather than counted as catching nothing (D188). Fails when either refusal is skipped. Re-derived by `control-mutations.yaml`, once per refusal. |
| `test_the_traces_file_would_notice_a_duplicate_id_or_a_frozen_commit_that_is_not_a_string` | `test_agreement.py` | connected | A traces list naming a finding twice, and a `rubric-frozen-v1` that is not a string, are each refused (D175). Fails when either shape check is skipped. Re-derived by `control-mutations.yaml`, once per check. |
| `test_the_totals_row_sums_each_column_into_its_own` | `test_agreement.py` | connected | The totals row sums each column into its own, over entries whose five counts differ (D175). Fails when a column is printed in its neighbor's place. Re-derived by `control-mutations.yaml`, once. |

Each of these is a check the audit drove with a mutation and found nothing red: five were asserted by no test, and the report reading's `main()` loop was reachable only through tests that call its function directly.

### The phase-5 audit's P5-9: two definitions of where an entry should fire, 2026-09-19

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_the_firing_tables_and_agreements_expected_calls_differ_only_where_recorded` | `test_agreement.py` | connected | The five family tables and agreement's expected calls, derived from `traces_to` and each finding's `call_ref`, name the same entry-call pairs but one, which is recorded in the test and beside OB-49. Fails when the expected calls are empty, and when a second difference appears. Re-derived by `control-mutations.yaml`, once. |

### D198: the register declares the vocabulary its result keys carry, 2026-09-19

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_the_register_would_notice_a_result_vocabulary_value_it_does_not_declare` | `test_corpus_hygiene.py` | connected | Every `reason=` and `remedy=` value a tool result names is one Class 6 declares, and a planted undeclared code is reported (D198). Fails when no value is compared, and when the register loses a declared remedy. Re-derived by `control-mutations.yaml`, once per defect. |

### D199: the close's test reads either form of a status line, 2026-09-20

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_the_close_check_reads_a_status_line_in_either_form_this_project_writes` | `test_document_counts.py` | connected | A handover closed as `**Status: closed**` and as `**Status:** closed.` is read as closed either way, an open one is not, and `sessions/` holds at least one the check reads (D199). Fails when the pattern reads only the first form. Re-derived by `control-mutations.yaml`, once. |

### D201: phase 6's license statement and its verifier's declarations, 2026-09-20

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_the_readme_names_a_license_for_every_top_level_path` | `test_phase6_acceptance.py` | connected | Every top-level path the ignore rules do not name is given a license by a row of the README's table, or is declared under neither (D201). Fails when the README loses the row licensing `HELDOUT_SET`. Re-derived by `control-mutations.yaml`, once. |
| `test_the_license_check_would_notice_a_path_the_readme_does_not_name` | `test_phase6_acceptance.py` | connected | A planted path the table does not name is reported, as are a row given a third license and `sessions/` no longer declared under neither (D201). Fails when an unnamed path is accepted. Re-derived by `control-mutations.yaml`, once. |
| `test_phase_6_declares_what_needs_a_model_call_and_the_design_document` | `test_phase3_acceptance.py` | connected | The phase-6 verifier declares exactly the six criteria not yet built, all of one kind (D201). Fails when the design document's declaration stops naming its criterion. Re-derived by `control-mutations.yaml`, once. |

### D202: the judged family's firing table, 2026-09-20

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_every_judged_entry_fires_where_the_committed_reference_log_is_recorded_as_firing` | `test_judged_firing.py` | connected | Each judged entry's gate counts against exactly the design calls the table names, over the committed reference log, and the firings that disagree with the gold set are the 19 false alarms and the 1 miss recorded by name (D202). Fails when the table names a call an entry is silent on. Re-derived by `control-mutations.yaml`, once. |
| `test_the_judged_firing_comparison_would_notice_a_firing_that_moved` | `test_judged_firing.py` | connected | A planted firing on a new call is reported as a moved row and a new false alarm, and a firing gone quiet as a new miss (D202). Fails when no firing set is compared with the table. Re-derived by `control-mutations.yaml`, once. |

### D203: the second adapter, identical where carried and declared where not, 2026-09-20

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_every_design_calls_retell_stream_differs_from_the_text_stream_only_where_declared` | `test_retell_adapter.py` | connected | For every design call the Retell adapter's call equals the text adapter's with the declared gaps applied, compared as the artifact's canonical bytes, and every speech event is identical with its citation id (D203). Fails when the adapter drops every tool result's detail. Re-derived by `control-mutations.yaml`, once. |
| `test_the_stream_comparison_would_notice_a_gap_filled_or_a_difference_undeclared` | `test_retell_adapter.py` | connected | A tool event given a timing its source does not carry, a result that lost its detail and a call declaring no gap are each reported by the comparison the test above makes (D203). Fails when the streams are never compared. Re-derived by `control-mutations.yaml`, once. |
| `test_the_adapter_would_notice_a_value_outside_its_declared_mapping` | `test_retell_adapter.py` | connected | A tool status, a disconnection reason and a transcript role outside the declared mapping each abort naming the value (D203). Fails when an unmapped status is no longer refused by name. Re-derived by `control-mutations.yaml`, once. |
| `test_the_adapter_would_notice_a_tool_result_with_no_success_flag` | `test_retell_adapter.py` | connected | A tool result carrying no `successful` is refused rather than given one (D203). Fails when the flag is defaulted. Re-derived by `control-mutations.yaml`, once. |
| `test_the_adapter_reads_the_document_it_is_given` | `test_retell_adapter.py` | connected | A word changed in a source document, and nowhere else, reaches the stream and the comparison, which an adapter reading the transcript beside its source would not show (D203). Fails when an utterance's words never reach the stream. Re-derived by `control-mutations.yaml`, once. |
| `test_the_documented_field_check_would_notice_a_field_nobody_documented` | `test_retell_adapter.py` | connected | An answered-at stamp, a timing on a tool entry and a version typed as a label are each reported against the table of Retell's documented fields (D203). Fails when no field is compared with the table. Re-derived by `control-mutations.yaml`, once. |
| `test_the_regeneration_check_would_notice_a_stale_document` | `test_retell_adapter.py` | connected | A committed source document that differs from its regeneration, and one no transcript produces, are each reported (D203). Fails when no document is compared. Re-derived by `control-mutations.yaml`, once. |
| `test_build_context_would_notice_a_call_that_declares_a_gap` | `test_retell_adapter.py` | connected | The seam every tier shares refuses a call whose source declares a gap, naming it, and accepts the same call from the text adapter (D203). Fails when the refusal is gone. Re-derived by `control-mutations.yaml`, once. |
| `test_the_gap_check_would_notice_a_stream_and_a_declaration_that_disagree` | `test_retell_adapter.py` | connected | A tool event with no timing on a call declaring no timing gap, a declared kind the stream still holds and a gap name nothing defines are each refused (D203). Fails when an undeclared absence is accepted. Re-derived by `control-mutations.yaml`, once. |
| `test_a_timing_check_would_notice_an_absent_time_read_as_a_number` | `test_retell_adapter.py` | connected | The silence check and the duration check return `unevaluable` naming event timing where an event carries none (D203). Fails when the silence check skips the event. Re-derived by `control-mutations.yaml`, once. |
| `test_a_retell_artifact_names_its_adapter_and_its_gaps_and_a_text_one_names_neither` | `test_retell_adapter.py` | connected | A text-sourced artifact writes neither new key, so its bytes and hash do not move, and a Retell-sourced one names its adapter and gaps (D203). Fails when every call writes a gap list. Re-derived by `control-mutations.yaml`, once. |

### D205: the log inspector's metrics, 2026-09-20

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_the_retry_metric_would_notice_an_identifier_shown_and_not_citable` | `test_inspector.py` | connected | An identifier the prompt shows inside a turn, beginning no line, is counted as shown and not citable (D205). Fails when a citable line is any tag anywhere in the prompt. Re-derived by `control-mutations.yaml`, once. |
| `test_the_retry_metric_would_notice_a_validator_rejecting_what_its_prompt_rendered` | `test_inspector.py` | connected | A retried answer whose citations, shape and scale all read as sound is counted as a retry the log cannot explain, which is W1 from the log alone (D205). Fails when an unexplained retry is never counted. Re-derived by `control-mutations.yaml`, once. |
| `test_the_integrity_metrics_would_notice_each_kind_of_damage` | `test_inspector.py` | connected | A blob below the record referencing it, a blob edited under its hash and a generation config edited under its request hash each move their metric (D205). Fails when every blob counts as re-hashing. Re-derived by `control-mutations.yaml`, once. |
| `test_the_repetition_metrics_would_notice_a_gap_and_a_second_retry` | `test_inspector.py` | connected | A missing repetition, a second retry and a prompt varying between repetitions each move their metric (D205). Fails when a group holding two retries is never counted. Re-derived by `control-mutations.yaml`, once. |
| `test_every_value_the_inspector_emits_is_a_count_or_a_proportion_with_both_its_terms` | `test_inspector.py` | connected | Over a log violating every invariant, each metric is two integers with a meaning, no metric line reads as a judgment, and the command exits 0 (D205). Fails when a proportion is printed as a percentage. Re-derived by `control-mutations.yaml`, once. |
| `test_the_inspector_refuses_only_a_file_it_cannot_read` | `test_inspector.py` | connected | A torn line and a file with no header are refused by name with exit 2 (D205). Fails when a headless file is inspected. Re-derived by `control-mutations.yaml`, once. |
| `test_the_committed_reference_log_measures_what_is_recorded` | `test_inspector.py` | connected | The committed reference log's measures are the ones pinned, so a re-recording that moves one is seen (D205). Fails when every pair counts as sharing one request hash. Re-derived by `control-mutations.yaml`, once. |

### D206: per-instance severity, 2026-09-20

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_no_property_turning_true_lowers_a_band` | `test_instance_severity.py` | connected | Over every combination of the seven properties, none turning true lowers the band, and all four bands are reachable (D206). Fails when one property enters the list negated. Re-derived by `control-mutations.yaml`, once. |
| `test_what_happened_is_read_from_the_evidence_point_on` | `test_instance_severity.py` | connected | A write and a verification that precede the evidence point are not read as following it (D206). Fails when a write anywhere in the call counts. Re-derived by `control-mutations.yaml`, once. |
| `test_the_properties_check_would_notice_an_entry_undeclared_and_a_declaration_orphaned` | `test_instance_severity.py` | connected | A rubric entry with no declaration, a declaration naming no entry, a property that is not a boolean and a read naming no param are each refused (D206). Fails when an undeclared entry is accepted. Re-derived by `control-mutations.yaml`, once. |
| `test_one_entry_receives_different_bands_on_two_calls_that_differ_in_what_happened` | `test_instance_severity.py` | connected | One entry is banded medium where a refund completed after the defect and low where nothing was written, on the same declared kind of harm (D206). Fails when what happened is never read. Re-derived by `control-mutations.yaml`, once. |
| `test_harness_severity_prints_a_band_for_every_instance_of_the_design_set` | `test_instance_severity.py` | connected | `harness severity` bands the design set's instances as pinned, excludes the synthesis with its reason and shows an entry banded differently on two calls (D206). Fails when an excluded entry's reason is never printed. Re-derived by `control-mutations.yaml`, once. |

### D207: the license check reads this repository's trees, 2026-09-21

| control | module | verdict | what it claims, and the defect that drives it red |
|---|---|---|---|
| `test_the_license_check_reads_this_repositorys_trees_and_not_a_sibling_checkout` | `test_phase6_acceptance.py` | connected | A top-level directory carrying its own `.git` is another repository's working copy and is not read as a tree this one licenses, while an ignored path stays ignored and an ordinary directory is still read (D207). Fails when a checkout is read as a tree of this repository. Re-derived by `control-mutations.yaml`, once. |
| `test_every_published_object_hashes_to_the_id_it_claims` | `test_freeze_proof.py` | connected | The four objects in `freeze-proof/` hash to the ids the proof names, under git's own rule and with no `.git` to ask, so the held-out seal's citation of the freeze is recomputed rather than believed (D209). Fails when a published byte moves. Re-derived by `control-mutations.yaml`, once. |
| `test_the_frozen_blobs_are_the_files_at_head` | `test_freeze_proof.py` | connected | `rubric.yaml` and the prompt template here are the blobs the freeze's own trees name, which is the claim the held-out labels rest on and the one the snapshot's re-pointed pin cannot make. Fails when either file moves. Re-derived by `control-mutations.yaml`, once. |
| `test_the_proof_readme_names_the_digests_the_files_have` | `test_freeze_proof.py` | connected | The digests the proof publishes are the digests its files have, read in both directions so a stale one beside a corrected one is reported. Fails when a published digest goes stale. Re-derived by `control-mutations.yaml`, once. |
| `test_the_frozen_src_reconstructs_from_the_published_objects` | `test_freeze_proof.py` | connected | The frozen `src` tree rebuilds from `freeze-proof/objects/` alone, every object verified against its own name as the trees are walked, so the held-out gate can run the frozen harness without a clone (D210). Fails when a published object stops being what it is named. Re-derived by `control-mutations.yaml`, once. |
| `test_the_frozen_code_computes_the_frozen_template_hash` | `test_freeze_proof.py` | connected | The frozen harness's own `load_template`, run in a separate interpreter over the reconstruction, computes the published hash, and `harness.__file__` resolves inside that reconstruction rather than in this checkout. Fails when the template moves. Re-derived by `control-mutations.yaml`, once. |

## What is left

**No row in either table is unaudited.** Every one has had its defect restored and its behavior
recorded, and **359**<!-- #control_mutations --> of them are re-derived on every run of
`tools/verify_controls.py` rather than resting on this document. **That number read “twenty”
until 2026-09-11**, in the one document whose whole subject is a claim going stale, and
unguarded because the recall net scans ten documents and this is not among them. It carries a
tag now, so the next reader gets a red suite rather than a wrong sentence (D146).

What that does **not** say, stated plainly because the temptation to read it otherwise is the whole
subject of this file:

- **One mutation per control proves one thing.** Each row shows the control catches *that* defect. It
  does not show the control catches every defect of its check. Mutation testing over the checks is the
  general form; this is the curated, cheap version.
- **The `Outside the idiom` rows are audited now too**, and one of them was masked. What that
  section still cannot promise is completeness: it is hand-maintained, found by looking for the shape
  of a control rather than by a rule, so a control named outside the idiom and never noticed is
  invisible to both tables.
- **A check with no control at all is invisible here.** This file audits controls. A check nobody
  planted a control for does not appear, and the three floorless assertions above are a warning about
  what that population might hold.
- **The screen is silent on most rows and that has not changed.** It found one of the six findings.
  The other five came from restoring defects, which is the only method that has never been wrong here.
