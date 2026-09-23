"""The reference policy documents, parsed into clauses.

Retrieval returns a **document**; the `POLICY` event names the clause the agent
applied (D65). Both halves are needed above the adapter line and for different
questions:

* the applied clause, to check that what the agent quoted is what that clause
  says -- correspondence on normalized whitespace, never bytes (D32), because
  the transcript and the document wrap at different points;
* **every** clause of every document retrieved in the call, to check the
  sharper class: a clause governing the question was inside the returned
  document and the agent applied a different one, or none. That class is only
  expressible because retrieval returns the whole document.

The parse lived only in the test suite until phase 2 needed it above the
adapter line. It is here now, and the corpus-hygiene test reads this rather
than keeping a second copy: two parsers for one format drift, and the one that
drifted would be the one the harness reads while the hygiene test kept
validating the other.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

#: A clause heading and its body, up to the next clause, section or rule.
#: Clause ids are `<section>.<index>`, stable, and cited as `<document> § <id>`.
_CLAUSE: Final[re.Pattern[str]] = re.compile(
    r"\*\*(?P<id>\d+\.\d+)\*\*\s*(?P<text>.*?)(?=\n\*\*\d+\.\d+\*\*|\n## |\n---)",
    re.DOTALL,
)


class PolicyError(Exception):
    """A policy document that cannot be read as one."""


@dataclass(frozen=True, slots=True)
class PolicyDocument:
    """One versioned policy document and its clauses, in file order."""

    name: str
    """The identifier a `fetch_policy` call names, e.g. `refund.v1`."""

    clauses: tuple[tuple[str, str], ...]
    """`(clause id, normalized text)` pairs, in the order the document states
    them. A tuple rather than a mapping so the order is part of the artifact --
    a clause count is checkable against it, and the order is what a reader
    scanning for the governing rule actually follows."""

    def text_of(self, clause: str) -> str:
        for clause_id, text in self.clauses:
            if clause_id == clause:
                return text
        raise PolicyError(f"{self.name} has no clause {clause!r}")

    def has(self, clause: str) -> bool:
        return any(clause_id == clause for clause_id, _ in self.clauses)

    def as_mapping(self) -> dict[str, str]:
        return dict(self.clauses)


def parse_policy(name: str, text: str) -> PolicyDocument:
    """Clause ids to normalized clause text.

    Whitespace is collapsed and surrounding quotation marks stripped, which is
    the normalization D32 settled: the transcript quotes a clause inside a
    wrapped event body and the document wraps it differently, so a byte
    comparison would fail on two identical sentences.
    """
    clauses = tuple(
        (match.group("id"), " ".join(match.group("text").split()).strip('"'))
        for match in _CLAUSE.finditer(text)
    )
    if not clauses:
        raise PolicyError(f"no clauses parsed out of {name}; the document format changed")
    seen: set[str] = set()
    for clause_id, _ in clauses:
        if clause_id in seen:
            raise PolicyError(f"{name} states clause {clause_id!r} twice")
        seen.add(clause_id)
    return PolicyDocument(name=name, clauses=clauses)


def load_policies(directory: Path) -> dict[str, PolicyDocument]:
    """Every `*.md` in the directory, keyed by the name a tool call would use.

    Sorted, for the reason extraction sorts transcripts: an artifact whose
    content depends on filesystem enumeration order hashes differently on two
    machines, and every "recompute this and check" claim downstream rests on it
    not doing that.
    """
    documents = {
        path.stem: parse_policy(path.stem, path.read_text(encoding="utf-8"))
        for path in sorted(directory.glob("*.md"))
    }
    if not documents:
        raise PolicyError(f"no policy documents found in {directory}")
    return documents
