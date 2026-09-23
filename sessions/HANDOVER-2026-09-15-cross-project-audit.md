# Handover — remediating the cross-project audit

**Status:** closed 2026-09-22 — every item it carries is registered as OB-37 to OB-43 and closed there with evidence, 7 of 7. Opened 2026-09-15, at `2432c4a`. Answers
`sessions/AUDIT-2026-09-15-cross-project.md`, which is a report rather than a prompt: it was written by
a session that cloned both repositories under `phase5-audit`, read no held-out transcript or label, and
carries none here.

**Where the numbers stand:** 7 items. The report's six findings, XH-1 to XH-6, and one this session
found that the report did not look for. Every harness-side citation in the report was checked against
the tree at `6a0f144` first, and every one held; nothing about the held-out repository can be checked
from here, and those statements are recorded as that session reported them.

**What the held-out session settled in the same week.** Its note of 2026-09-15 asked four questions,
which are XH-1 to XH-4 read from the other side. D181 to D184 record the owner's answers: the severity
export's schema, the corpus version a held-out run carries, a header naming the rubric it judged under,
and a log this repository names itself. Each closes the records half of its finding; three leave
behavior owed, and those rows stay open until it lands with its criteria and controls.

## What is owed

### 1. The held-out severity export has no schema this repository states

XH-1. Phase 5's coverage report reads a second severity file for the held-out set, and nothing here
named its schema, so nothing could check that export before it was sealed — after which nothing may be
edited. Answered by D181: the scoring tool's export at schema 3, keyed by finding id, cuts in the same
file, checkable before sealing with this repository's own loader. Whether the scoring tool can key a
second store on the held-out ids sits with that store, not here.

### 2. A held-out run's corpus version is defined on neither side

XH-2. `--corpus-version-file` defaults inside this checkout, so a held-out run made on the defaults
stamps the design corpus's version into a header that is committed once and never changes, and
`harness agreement` then demands a held-out corpus version file nobody had defined. Answered by D182:
the held-out set's own version, from a file committed there. Owed here: `held_out_paths_inside` refuses
that flag inside the checkout on a held-out run, with its criterion and control.

### 3. The run-log name this repository writes is not one the held-out gate admits

XH-3. The writer names a log by start time and mode; that gate admits a run log only under a `heldout-`
prefix, leaving a rename between writing a paid-for log and committing it. Answered by D184: this
repository writes the prefix on a run whose header carries a labels manifest. Owed here: the writer's
path, with its criterion and control.

### 4. Nothing pins the rubric's content to the freeze

XH-4. Judged under the frozen rubric rests on the rubric version and the prompt template hash, and
neither moves when an entry's text moves, so a log judged under edited entry text passes every check on
both sides. Answered by D183. Owed here: a test pinning `rubric.yaml` and the prompt template at HEAD to
the freeze commit, and a hash of the rubric in a held-out run's header, with its criterion and control.

### 5. O-11 dates the D101 port to the day it was reported

XH-5. O-11 carries 2026-09-14 in three places; the held-out commit it describes is dated 2026-09-11,
2026-09-12 in UTC, as the report states and nothing here can confirm. Owed: date the port to its commit
and keep the reported date as the date it was reported.

### 6. Harness documents describing the held-out side have gone stale

XH-6. `README.md` describes that repository's labels as committed after the freeze, where no label
commit exists there yet; it states what that repository reads from this one more narrowly than it now
does, and calls the two spent briefs the documents that govern it, where its own design document does.
`tools/verify_phase1.py`'s absence caveat enumerates that workflow's steps and omits two. Owed: the
three sentences and the caveat, the caveat stating a limit rather than history, as D180 requires.

### 7. A report over held-out calls can be written into this tree

Found in this session; the report checked the run and agreement commands and did not look at this one.
`harness report` reads no `HELDOUT_SET`, does not check a log's labels manifest, and writes wherever
`--out` points, so a report over held-out calls — per-call verdicts and rollups, no transcript text or
rationale — can be rendered into the checkout, where the absence check would not see it. Owed: the
refusal the owner chooses, with its criterion and control, and whether the absence check should
recognize a rendered report.

