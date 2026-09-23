"""The obligations register, read by rule rather than by a reader.

Every other register in this project mechanizes a **claim**. This one mechanizes
a **discharge**, which nothing did: handovers carried a `What is owed` section,
the decision record carries a `Not checked` block, and whether an item was ever
addressed depended on the next session reading a document.

The rule is the control register's, one subject over: **harvest the population
by a rule rather than listing it.** Every numbered item under a `## What is
owed` heading in every handover must appear in the register, and every register
row must name an item that exists. A list would go stale the first time a
handover was written; a rule cannot.

**What this cannot do is stated in the register itself and is worth repeating
where a reader of the tests will meet it.** It does not know whether an
obligation *should* be discharged. Every status here was typed by somebody. What
it removes is the failure where nobody notices an item exists -- not the one
where somebody looks at it and is wrong.
"""

from __future__ import annotations

import re
import subprocess
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Final, NamedTuple

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
REGISTER: Final[Path] = REPO_ROOT / "OBLIGATIONS.md"
HOLDOUT_REGISTER: Final[Path] = REPO_ROOT / "HOLDOUT-OBLIGATIONS.md"
SESSIONS: Final[Path] = REPO_ROOT / "sessions"

#: The statuses a row may carry. Closed, and closed deliberately: a vocabulary
#: that grows to fit whatever somebody wanted to say is a vocabulary that stops
#: dividing anything. `wontfix` is absent on purpose -- a decision never to do
#: something belongs in the decision record, where it has to state a fork and
#: its consequences.
STATUSES: Final[frozenset[str]] = frozenset({"open", "deferred", "closed"})

#: What a row carrying no trigger or evidence writes in that column. A visible
#: token rather than an empty cell, because an empty cell is indistinguishable
#: from a row somebody stopped editing half way.
ABSENT: Final[str] = "—"

_OWED_HEADING: Final[re.Pattern[str]] = re.compile(r"^##\s+What is owed.*?$", re.MULTILINE)
#: A numbered owed item, in either shape the handovers in this tree actually
#: use: a `### 1. Title` heading, or a `1. **Title**` list entry. Both are
#: present -- the phase-3 handover uses the first and the control-register
#: handover the second -- and a harvest that knew only one silently covered
#: half the population while reporting the other half as orphaned rows. That is
#: how this pattern was widened: the reverse-direction guard fired on its first
#: run, which is the guard working before the register had ever been read.
#:
#: The bold is required on the list shape and not on the heading shape, because
#: a bare `1.` in prose is an ordinary numbered list and this is scoped to the
#: owed section but not to a single paragraph within it.
_ITEM: Final[re.Pattern[str]] = re.compile(
    r"^###\s+(\d+)\.\s+(.+)$|^(\d+)\.\s+\*\*(.+?)\*\*",
    re.MULTILINE,
)


class Row(NamedTuple):
    """One register row, parsed."""

    id: str
    source: str
    item: str
    anchor: str
    status: str
    obligation: str
    detail: str

    @property
    def key(self) -> tuple[str, str]:
        """Where the row points: which handover, which numbered item."""
        return (self.source, self.item)


def _rows() -> tuple[Row, ...]:
    """Every row of the register table, parsed positionally.

    Deliberately strict about the column count. A row with a stray pipe parses
    into the wrong fields and would compare a status against an obligation, so
    it is refused rather than absorbed.
    """
    parsed: list[Row] = []
    for line in REGISTER.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| OB-"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        assert len(cells) == 7, f"register row has {len(cells)} columns, expected 7: {line[:70]}"
        parsed.append(Row(*cells))
    return tuple(parsed)


def _owed_items() -> Mapping[tuple[str, str], str]:
    """Every numbered item under a `What is owed` heading, across all handovers.

    Harvested rather than listed. A handover written next week with an owed
    section is in this population the moment it lands, which is what makes the
    register's completeness a rule instead of somebody's diligence.
    """
    found: dict[tuple[str, str], str] = {}
    for path in sorted(SESSIONS.glob("HANDOVER-*.md")):
        text = path.read_text(encoding="utf-8")
        heading = _OWED_HEADING.search(text)
        if heading is None:
            continue
        body = text[heading.end() :]
        end = re.search(r"^##\s", body, re.MULTILINE)
        if end is not None:
            body = body[: end.start()]
        for heading_n, heading_t, list_n, list_t in _ITEM.findall(body):
            number, title = (heading_n, heading_t) if heading_n else (list_n, list_t)
            found[(path.name, number)] = title.strip()
    return found


# --------------------------------------------------------------------------
# The harvest, in both directions
# --------------------------------------------------------------------------


def test_the_register_parses_to_something_rather_than_to_nothing() -> None:
    """The floor. Every assertion below compares against this population, and a
    parse that silently returned nothing would make all of them pass over an
    empty table -- which is the shape three floorless assertions in this suite
    were found to have (D121)."""
    rows = _rows()
    assert rows, "the obligations register parsed to no rows at all"
    assert len(rows) == len({row.id for row in rows}), "the register repeats an id"
    assert _owed_items(), "no handover declares an owed item, so the harvest compares nothing"


def test_every_owed_item_in_a_handover_has_a_register_row() -> None:
    """The rule that makes this a register rather than a list.

    An owed item written into a handover and never registered is invisible to
    everything: no test names it, no gate counts it, and the only thing standing
    between it and being forgotten is whether the next session reads that
    handover to the end.
    """
    registered = {row.key for row in _rows()}
    missing = sorted(
        f"{source} item {item} ({title[:60]})"
        for (source, item), title in _owed_items().items()
        if (source, item) not in registered
    )
    assert not missing, (
        "handover items owed and not registered in OBLIGATIONS.md:\n  " + "\n  ".join(missing)
    )


def test_every_register_row_still_points_at_the_obligation_it_was_written_for() -> None:
    """The half a number cannot carry.

    Renumbering and deletion were caught in both directions from the start; a
    **rename that keeps the number** was invisible. An audit changed "Agreement
    is measured now, and still not asserted" to a completely different heading,
    left the `2.` in place, and all ten tests here stayed green -- with the row
    then asserting a status about an obligation nobody had written.

    The anchor is a distinctive substring of the item's own title, which is the
    idiom the phase verifiers use to bind an entry to a specification criterion.
    Substring rather than equality, because a title may be edited for wording
    without becoming a different obligation, and a rule that fired on every
    comma is a rule somebody turns off.
    """
    owed = _owed_items()
    drifted: list[str] = []
    for row in _rows():
        title = owed.get(row.key)
        if title is None:
            continue  # the other direction's test reports this
        anchor = row.anchor.strip("`")
        assert anchor, f"{row.id} carries no anchor, so it compares only a number"
        if anchor not in title:
            drifted.append(f"{row.id} -> {row.source} item {row.item}: {anchor!r} not in {title!r}")
    assert not drifted, "register rows whose source item was renamed under them:\n  " + "\n  ".join(
        drifted
    )


def test_every_register_row_names_an_owed_item_that_exists() -> None:
    """The other direction. A row whose source was renumbered or rewritten
    asserts nothing, and says so loudly rather than sitting there looking
    current -- which is how the control register's line-numbered predecessor
    went stale before its author finished editing the files it pointed into."""
    owed = _owed_items()
    orphaned = sorted(
        f"{row.id} -> {row.source} item {row.item}" for row in _rows() if row.key not in owed
    )
    assert not orphaned, "register rows naming handover items that do not exist:\n  " + "\n  ".join(
        orphaned
    )


# --------------------------------------------------------------------------
# What a status has to carry
# --------------------------------------------------------------------------


def test_every_row_carries_a_status_from_the_closed_vocabulary() -> None:
    offenders = sorted(f"{row.id}: {row.status!r}" for row in _rows() if row.status not in STATUSES)
    assert not offenders, f"rows with a status outside {sorted(STATUSES)}:\n  " + "\n  ".join(
        offenders
    )


def test_a_deferred_row_names_what_would_make_it_actionable() -> None:
    """A deferral with no trigger is an open item wearing a decision's clothes.

    This is the assertion the register exists for more than any other. "Later"
    is what an obligation says on the day it stops being tracked, and the
    difference between a deferral and an abandonment is entirely whether
    anybody wrote down what would bring it back.
    """
    offenders = sorted(
        row.id
        for row in _rows()
        if row.status == "deferred" and (row.detail == ABSENT or "trigger:" not in row.detail)
    )
    assert not offenders, (
        "deferred rows naming no trigger, so nothing says what would make them actionable: "
        + ", ".join(offenders)
    )


#: A trigger naming an event this repository records: a tag, by the command that shows it.
_TAG_TRIGGER: Final[re.Pattern[str]] = re.compile(r"`git tag --list ([\w.\-]+)`")

#: How a row records that its trigger has happened.
_FIRED: Final[re.Pattern[str]] = re.compile(r"\bfired \d{4}-\d{2}-\d{2}\b")

#: How a row records that nothing here can observe its trigger.
READ_BY_A_PERSON: Final[str] = "read by a person"


def _tag_exists(name: str) -> bool:
    """Whether this clone holds the tag, asked of git rather than assumed.

    Refuses outside a clone rather than answering: a copy with no `.git` would
    say no tag exists for every trigger, and every acknowledged row would then
    read as a claim about an event that never happened.
    """
    listed = subprocess.run(
        ["git", "tag", "--list", name],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return bool(listed.stdout.strip())


def _trigger_offenders(rows: Sequence[Row], tag_exists: Callable[[str], bool]) -> list[str]:
    """Every deferred row whose trigger disagrees with what has happened.

    Both directions for a trigger naming a tag -- a fired tag the row does not
    acknowledge, and an acknowledgement of a tag that does not exist -- and one
    rule for the rest: a trigger nothing can observe has to say a person reads
    it. Takes the lookup as an argument so a control can drive this over planted
    rows in a copy of the tree that has no `.git`.
    """
    offenders: list[str] = []
    for row in rows:
        if row.status != "deferred":
            continue
        tag = _TAG_TRIGGER.search(row.detail)
        if tag is None:
            if READ_BY_A_PERSON not in row.detail:
                offenders.append(f"{row.id}: its trigger names no observable event and no reader")
            continue
        fired = tag_exists(tag.group(1))
        acknowledged = _FIRED.search(row.detail) is not None
        if fired != acknowledged:
            state = "has fired, unacknowledged" if fired else "is acknowledged and has not fired"
            offenders.append(f"{row.id}: the tag {tag.group(1)} {state}")
    return offenders


def test_every_deferred_trigger_is_read_against_what_has_happened() -> None:
    """P4-15. A deferral's trigger, read against the event it names (D166, OB-32).

    `test_a_deferred_row_names_what_would_make_it_actionable` asks only that a
    trigger is written down. On 2026-09-13 the `rubric-frozen-v1` tag was pushed
    and fired every row the phase-4 audit placed after the freeze, and nothing in
    the tree noticed. A trigger naming a tag is now asked of git: a row whose tag
    exists carries `fired` and the date, and a row claiming `fired` for a tag that
    does not exist is refused, so the acknowledgement cannot be typed ahead of the
    event. A trigger nothing here can observe has to say a person reads it.
    """
    offenders = _trigger_offenders(_rows(), _tag_exists)
    assert not offenders, (
        "deferred rows whose trigger disagrees with what has happened:\n  " + "\n  ".join(offenders)
    )


def test_the_trigger_check_would_notice_a_fired_trigger_left_unacknowledged() -> None:
    """The control on the check above, driven over planted rows with the lookup supplied.

    Planted rather than read from the register, and told whether the tag exists
    rather than asking git, because the control gate runs this in a copy of the
    tree with no `.git`. Every direction the check has: a fired tag left
    unacknowledged, an acknowledgement of a tag that never existed, and a trigger
    nothing can observe that does not say a person reads it -- each refused, and
    each clean shape accepted.
    """
    tag = "trigger: the `x` tag exists, which `git tag --list x` shows"
    unobserved = "trigger: when somebody notices"

    def planted(detail: str) -> Row:
        return Row("OB-0", "HANDOVER-planted.md", "1", "`planted`", "deferred", "planted", detail)

    def exists(_name: str) -> bool:
        return True

    def missing(_name: str) -> bool:
        return False

    assert _trigger_offenders([planted(tag)], exists), "a fired tag left unacknowledged passed"
    assert _trigger_offenders([planted(f"{tag}; fired 2026-09-13")], missing), (
        "an acknowledgement of a tag that does not exist passed"
    )
    assert not _trigger_offenders([planted(f"{tag}; fired 2026-09-13")], exists)
    assert not _trigger_offenders([planted(tag)], missing)
    assert _trigger_offenders([planted(unobserved)], exists), "an unread trigger passed"
    assert not _trigger_offenders([planted(f"{unobserved}; {READ_BY_A_PERSON}")], exists)


def test_a_closed_row_names_its_evidence() -> None:
    """Closed is the one status that makes a claim about the world, so it is the
    one that has to point at something. A row that said `closed` and nothing
    else would be the tick this whole project distrusts."""
    offenders = sorted(
        row.id
        for row in _rows()
        if row.status == "closed" and (row.detail == ABSENT or "evidence:" not in row.detail)
    )
    assert not offenders, "closed rows naming no evidence: " + ", ".join(offenders)


def test_evidence_that_names_a_test_names_one_that_exists() -> None:
    """A closed row citing a test that has been renamed is a discharge nobody
    can check. Reuses the suite's own test-name population rather than globbing
    for the string, so a name that exists in a comment does not count."""
    existing = {
        name
        for path in sorted((REPO_ROOT / "tests").glob("*.py"))
        for name in re.findall(r"^def (test_\w+)", path.read_text(encoding="utf-8"), re.MULTILINE)
    }
    modules = {path.name for path in sorted((REPO_ROOT / "tests").glob("*.py"))}
    dangling: list[str] = []
    for row in _rows():
        for cited in re.findall(r"`(tests/[\w./]+|test_\w+)`", row.detail):
            leaf = cited.rsplit("/", 1)[-1]
            if leaf.endswith(".py"):
                if leaf not in modules:
                    dangling.append(f"{row.id} cites {cited}")
            elif leaf not in existing:
                dangling.append(f"{row.id} cites {cited}")
    assert not dangling, "register evidence naming tests that do not exist: " + ", ".join(dangling)


# --------------------------------------------------------------------------
# The holdout register keeps its own discharge rule, and gains a status check
# --------------------------------------------------------------------------


def test_every_holdout_obligation_carries_a_discharge_marker() -> None:
    """`HOLDOUT-OBLIGATIONS.md` is a separate register with a stricter rule --
    only a session cleared to read held-out content may tick an entry.

    Its discharged COUNT was already computed from the marks rather than
    maintained. What nothing asserted is that every entry has a mark at all: an
    entry added without one reads as open by absence, which is the safe
    direction and still leaves its status implied rather than stated.
    """
    text = HOLDOUT_REGISTER.read_text(encoding="utf-8")
    entries = re.split(r"^### (O-\d+)", text, flags=re.MULTILINE)
    assert len(entries) > 1, "the holdout register parsed to no entries"
    unmarked = [
        entries[i]
        for i in range(1, len(entries), 2)
        if not re.search(r"^\*\*Discharged:\*\*\s*[☐☑]", entries[i + 1], re.MULTILINE)
    ]
    assert not unmarked, "holdout obligations carrying no discharge marker: " + ", ".join(unmarked)


def test_a_discharged_holdout_obligation_names_a_session_and_a_date() -> None:
    """A tick nothing can confirm is the point of that file -- but a tick that
    does not say who made it or when cannot even be argued with."""
    text = HOLDOUT_REGISTER.read_text(encoding="utf-8")
    entries = re.split(r"^### (O-\d+)", text, flags=re.MULTILINE)
    thin: list[str] = []
    for i in range(1, len(entries), 2):
        mark = re.search(r"^\*\*Discharged:\*\*\s*☑(.*)$", entries[i + 1], re.MULTILINE)
        if mark is None:
            continue
        line = mark.group(1)
        if "session" not in line or not re.search(r"\d{4}-\d{2}-\d{2}", line):
            thin.append(entries[i])
    assert not thin, "discharged entries naming no session or no date: " + ", ".join(thin)


# --------------------------------------------------------------------------
# The control
# --------------------------------------------------------------------------


def test_the_register_guard_would_notice_an_unregistered_obligation() -> None:
    """The control on this register's own guard.

    Drives `_owed_items` over a handover-shaped document it writes, rather than
    re-implementing the harvest beside the check: a control that parsed its own
    string and compared its own sets would be proof about its own copy, which is
    the shape D121 found in six controls, every one of them measuring nothing.

    Both directions, because the guard has two and a control for one of them
    would leave the other proven by nothing.
    """
    planted = SESSIONS / "HANDOVER-0000-00-00-control-plant.md"
    planted.write_text(
        "# Planted\n\n## What is owed, in the order I would take it\n\n"
        "### 1. An obligation no register row names\n\nBody.\n",
        encoding="utf-8",
    )
    try:
        harvested = _owed_items()
        key = (planted.name, "1")
        assert key in harvested, (
            "the harvest does not see an owed item in a handover-shaped document, so the "
            "guard above is comparing against a population it cannot build"
        )
        registered = {row.key for row in _rows()}
        assert key not in registered, "the planted item is somehow already registered"
    finally:
        planted.unlink()

    # And restored: the harvest no longer sees it, so the guard is green again.
    assert (planted.name, "1") not in _owed_items()
