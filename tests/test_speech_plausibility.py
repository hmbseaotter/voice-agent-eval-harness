"""Every utterance takes a plausible amount of time to say.

This test exists because a human reviewer noticed something no assertion in the
suite could: CALL-01 ran twenty seconds of conversation that would take a person
the better part of a minute. Measuring it found a median of 116 words per
minute across the corpus, with individual utterances at 42 and at 253 — the
first slower than dictation, the second faster than an auctioneer.

The durations were then recomputed. Without a check they would drift back the
moment anyone edits a line of dialogue without touching its timestamps, and the
drift would be invisible: a transcript with implausible timings parses, passes
every structural check, and reads perfectly.

**What this is not.** It is not a claim that the corpus reproduces real speech
timing. There is no audio behind these transcripts and there is no such thing as
a correct duration for an invented utterance. It is a plausibility floor: an
utterance whose implied rate falls outside the range human speech actually
occupies is wrong in a way a reader will notice, and that is worth catching.

**The band.** Conversational English runs roughly 130-160 wpm; read-aloud and
telephone speech sit in the same region. The band here is deliberately wider
than that at 110-185, because the tight range is a population statistic and
these are individual utterances — a slow, careful readback of a booking
reference and a quick "That's the one" are both real. Anything outside the wide
band is not natural variation, it is a timestamp that no longer matches its
text.
"""

from __future__ import annotations

import statistics
from pathlib import Path

from harness.core.events import DisclosureEvent, EventKind, SpeechEvent, timing
from harness.corpus.text_adapter import parse_call

REPO_ROOT: Path = Path(__file__).resolve().parents[1]
TRANSCRIPTS: Path = REPO_ROOT / "corpus" / "transcripts"

#: The plausibility band, words per minute. See the module docstring on why it
#: is wider than the 130-160 figure normal conversation actually occupies.
SLOWEST_PLAUSIBLE_WPM: float = 110.0
FASTEST_PLAUSIBLE_WPM: float = 185.0

#: Utterances shorter than this carry too few words for a rate to mean anything:
#: a two-word reply spoken with a half-second pause on either side implies a
#: rate that says more about the pause than the speech.
MINIMUM_WORDS_FOR_A_RATE: int = 4


def _transcripts() -> list[Path]:
    found = sorted(TRANSCRIPTS.glob("CALL-*.txt"))
    assert found, f"no transcripts under {TRANSCRIPTS}"
    return found


def _rate_wpm(event: SpeechEvent) -> float | None:
    """Words per minute implied by an utterance's own start and end stamps, or
    `None` where the utterance is too short for that number to mean anything."""
    words = len(event.body.split())
    if words < MINIMUM_WORDS_FOR_A_RATE:
        return None
    started, ended = timing(event)
    seconds = (ended - started) / 1000.0
    if seconds <= 0:
        return None
    return words / seconds * 60.0


def _measured() -> list[tuple[str, int, int, float]]:
    """`(call_id, index, word count, wpm)` for every measurable utterance."""
    rows: list[tuple[str, int, int, float]] = []
    for transcript in _transcripts():
        call = parse_call(transcript)
        for event in call.events:
            if not isinstance(event, SpeechEvent):
                continue
            rate = _rate_wpm(event)
            if rate is not None:
                rows.append((call.record.call_id, event.index, len(event.body.split()), rate))
    return rows


def test_every_utterance_is_spoken_at_a_plausible_rate() -> None:
    rows = _measured()
    assert len(rows) > 100, f"only {len(rows)} utterances were measurable; the corpus is thin"

    outliers = [
        f"{call_id} event {index}: {words} words in {words / rate * 60:.1f}s = {rate:.0f} wpm"
        for call_id, index, words, rate in rows
        if not SLOWEST_PLAUSIBLE_WPM <= rate <= FASTEST_PLAUSIBLE_WPM
    ]
    assert not outliers, (
        f"{len(outliers)} of {len(rows)} utterances are spoken at an implausible rate "
        f"(band: {SLOWEST_PLAUSIBLE_WPM:.0f}-{FASTEST_PLAUSIBLE_WPM:.0f} wpm):\n  "
        + "\n  ".join(outliers)
    )


def test_the_corpus_median_sits_where_conversation_sits() -> None:
    """The band above passes a corpus that is uniformly slow, so long as it is
    uniformly slow *within* the band. This pins the center as well as the
    edges: the median is where the corpus actually lives, and 116 wpm — the
    figure the review caught — would fail here while passing the band."""
    median = statistics.median(rate for _, _, _, rate in _measured())
    assert 130.0 <= median <= 160.0, (
        f"corpus median is {median:.0f} wpm; conversational English sits at 130-160"
    )


def test_the_check_would_catch_a_slowed_transcript() -> None:
    """The negative control, and it did not call the function it controls.

    It compared three fabricated floats against the two module constants --
    which proves the band excludes 42 and 253, and nothing about `_rate_wpm`.
    A bug making that function return `None` for every utterance would leave the
    band tests green over an empty list and this control green over its own
    literals. It builds events and measures them now.
    """
    fabricated = [
        (30, 42.9),  # 30 words in 42.9 seconds -- about 42 wpm
        (30, 7.1),  # 30 words in 7.1 seconds -- about 253 wpm
        (30, 12.4),  # 30 words in 12.4 seconds -- about 145 wpm
    ]
    rates = []
    for words, seconds in fabricated:
        event = SpeechEvent(
            index=1,
            started_at_ms=0,
            ended_at_ms=int(seconds * 1000),
            kind=EventKind.AGENT,
            body=" ".join(["word"] * words),
            citation_id="T1",
            source_lines=(1,),
        )
        rate = _rate_wpm(event)
        assert rate is not None, "_rate_wpm returned None for a measurable utterance"
        rates.append(rate)

    caught = [r for r in rates if not SLOWEST_PLAUSIBLE_WPM <= r <= FASTEST_PLAUSIBLE_WPM]
    assert len(caught) == 2, f"the band admits rates it was written to reject: {rates}"


def test_disclosure_speech_is_measured_too() -> None:
    """A `DISCLOSURE` carries spoken text and its own start and end stamps --
    CALL-11's is about five seconds of it -- and only `SpeechEvent` was rated.

    A mandated statement read at 300 words per minute is the defect the band
    exists to catch, and it is arguably worse there than in ordinary speech: the
    whole point of a disclosure is that the caller can follow it.
    """
    measured = 0
    outliers: list[str] = []
    for transcript in _transcripts():
        call = parse_call(transcript)
        for event in call.events:
            if not isinstance(event, DisclosureEvent) or not event.text:
                continue
            words = len(event.text.split())
            started, ended = timing(event)
            seconds = (ended - started) / 1000.0
            if words < MINIMUM_WORDS_FOR_A_RATE or seconds <= 0:
                continue
            measured += 1
            rate = words / seconds * 60.0
            if not SLOWEST_PLAUSIBLE_WPM <= rate <= FASTEST_PLAUSIBLE_WPM:
                outliers.append(f"{call.record.call_id} event {event.index}: {rate:.0f} wpm")
    assert measured >= 10, f"only {measured} disclosures were measurable"
    assert not outliers, "disclosures spoken at an implausible rate:\n  " + "\n  ".join(outliers)


def test_a_short_reply_is_not_measured() -> None:
    """ "Yes." occupying a second implies 60 wpm, and rejecting it would be
    wrong. The exemption has to be narrow enough that it cannot swallow real
    utterances, so it is asserted rather than assumed."""
    measurable = {(call_id, index) for call_id, index, _, _ in _measured()}
    for transcript in _transcripts():
        call = parse_call(transcript)
        for event in call.events:
            if not isinstance(event, SpeechEvent):
                continue
            words = len(event.body.split())
            if words >= MINIMUM_WORDS_FOR_A_RATE:
                assert (call.record.call_id, event.index) in measurable, (
                    f"{call.record.call_id} event {event.index} has {words} words "
                    "and was skipped anyway"
                )


def test_both_speech_kinds_are_measured() -> None:
    """A rate check that only ever looked at one speaker would leave half the
    corpus free to drift."""
    kinds: set[EventKind] = set()
    for transcript in _transcripts():
        call = parse_call(transcript)
        for event in call.events:
            if isinstance(event, SpeechEvent) and _rate_wpm(event) is not None:
                kinds.add(event.kind)
    assert kinds == {EventKind.CALLER, EventKind.AGENT}
