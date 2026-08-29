"""What a run's numbers are worth, before anyone reads them.

Promoted to ``core/`` on the bar this repo sets: cabal and changeling were
computing the same integrity block from the same fields, and a second
implementation of a void bar is how two runs come to void differently. Nothing
here knows about roles or hidden information - it reads decision counts and a
per-decision seat, which is arena vocabulary, not any one game's.

**Three outcomes per decision, not two.** A decision is CLEAN when nothing the
model wrote was sent back, RECOVERED when the parser or the rules refused an
attempt and a later one landed, and a FALLBACK when nothing landed and the random
policy played it. The three partition ``decisions``. Before this the middle one was
invisible: it was counted with the clean decisions and survived only as a sampled
trace line, capped and printed after the run ended. A run at 1% fallback and 30%
recovered is not a run at 1% - the model needed the referee to correct it on nearly
a third of its moves, and that is a fact about the model its fallback rate does not
carry.

**A refusal is split by what did the refusing.** A 429 says nothing about play; an
unparsed or illegal reply says everything. So a decision that only ever failed in
TRANSPORT is clean, not recovered, and a game the network flaked in is still a
clean game. The attempt counts are kept beside the decision counts as the
diagnostic behind them, never as the headline - attempts are unbounded in the
retry budget and a rate over them means nothing.

Note what a refusal is NOT here: a dropped decision. The referee always retells and
re-asks, so a refused attempt costs latency and never removes a move from the
record. A clean game is therefore a stricter claim than "no seat made an illegal
decision" - it is "nothing any seat wrote was sent back", malformed replies
included, since a reply the parser could not read is the model failing to answer
just as much as an illegal move is.

**And a rate is CAUSED or WITNESSED.** ``fallbacks / decisions`` is the caused
half: the share of a seat's OWN decisions the random policy played. It says
nothing about the table that seat sat at, and a seat with a spotless caused rate
whose opponents fell back on a third of their moves was not playing against a
model at all - its votes answered noise. Two seats read as equal on the caused
rate and are not. The witnessed half is per seat-game, so it survives averaging:
the run-level mean is dull by construction, and ``witnessed_worst`` plus the count
over the void bar is the number worth reading.

The caused rate keeps the name ``fallback_rate``. Every published summary and every
record in ``eval/records/`` quotes it, and renaming a number that did not change is
how a re-read of an old run comes back with a different answer.
"""

from __future__ import annotations

import random
from collections import Counter

#: Above this share of random decisions the scorer voids a verdict. One constant,
#: because cabal warns and changeling VOIDs off the same threshold and a drifting
#: pair of literals is the bug this module exists to make impossible.
VOID_BAR = 0.10


def policy_rng(seed: int | None) -> random.Random:
    """The random policy's stream, derived from a run seed but NOT equal to it.

    Both games seeded the referee and the policies with the same integer, which
    makes them the same MT19937 sequence read at two offsets - so the deal and
    the policy's draws are dependent, and the exact chance baselines a control is
    read against assume they are not. Measured on quorum, 2026-08-29: the random
    control's enactor honesty came in at 32.550% over 20,540 claims (z = -2.38
    against the exact 33.333%) coupled, and 33.449% over 48,971 claims (z = +0.54)
    with the policy stream offset; every one of nine coupled blocks was negative
    while the decoupled blocks straddled zero. The control is the floor a criterion
    cites as evidence its bar is right, so a control that misses its own baseline
    by construction costs the bar its credibility even when the bar is exact
    arithmetic and unaffected.

    Reproducibility is preserved: the derivation is pure, so one run seed still
    names one policy stream. An unpinned run stays unpinned - ``None`` seeds from
    the OS, exactly as before, because a default here would make every run look
    reproducible while the record says nothing about it.
    """
    if seed is None:
        return random.Random()
    # A cheap avalanche, not a hash: enough to put the two streams in unrelated
    # regions of the state space, and stable across versions the way a library
    # hash is not.
    return random.Random((seed ^ 0x9E3779B9) & 0xFFFFFFFF)


#: Above this share of RECOVERED decisions the report says so, loudly, and does NOT
#: void. **Set 2026-08-28, before any run had produced the number** - S9 introduced
#: `recovered` and gave it no bar, so a run at 1% fallback and 40% recovered passed
#: every check and read as clean. changeling's 200-game run is the first record that
#: will carry it, and picking a bar with that number in view is the peeking this
#: repo refuses by name.
#:
#: **Warn rather than void, and the asymmetry is the point.** A fallback is a
#: decision no model made - the random policy played it, so the number is not the
#: model's and a verdict resting on it is void. A recovered decision IS the model's:
#: it was refused, told why, and got it right, which is legal play under the rules
#: the referee enforces. What it is not is the same measurement as a run that never
#: missed, so it belongs beside the verdict rather than in place of it.
#:
#: 25%, i.e. one decision in four needing the referee. Chosen as the point at which
#: the refuse-and-retell loop stops being a safety net and becomes part of how the
#: seat plays - two and a half times the void bar, because the failure it describes
#: is milder by exactly that kind of margin. No run has been measured against it.
RECOVERED_WARN_BAR = 0.25


def summarise(records: list, trace_lines: int = 8) -> dict:
    """The integrity block for a run. ``records`` are per-game records carrying
    ``decisions``, ``fallbacks``, ``recovered``, ``refused_attempts``,
    ``rule_refused_attempts``, ``decision_log``, ``upstreams``, ``trace_sample``
    and ``error``."""
    decisions = sum(r.decisions for r in records)
    fallbacks = sum(r.fallbacks for r in records)
    recovered = sum(getattr(r, "recovered", 0) for r in records)
    attempts = sum(getattr(r, "refused_attempts", 0) for r in records)
    rule_attempts = sum(getattr(r, "rule_refused_attempts", 0) for r in records)

    # A game that errored never finished, so it cannot be called clean or dirty -
    # counting it either way makes the denominator a statement about crashes.
    played = [r for r in records if not r.error]
    clean_games = sum(1 for r in played
                      if r.fallbacks == 0 and getattr(r, "recovered", 0) == 0)

    served: Counter = Counter()
    for r in records:
        served.update(r.upstreams or {})

    return {
        "decisions": decisions,
        "fallbacks": fallbacks,
        "fallback_rate": fallbacks / decisions if decisions else 0.0,
        **_witnessed(records),
        "recovered": recovered,
        "recovered_rate": recovered / decisions if decisions else 0.0,
        "clean_decisions": decisions - fallbacks - recovered,
        "refused_attempts": attempts,
        "rule_refused_attempts": rule_attempts,
        "clean_games": clean_games,
        "games_finished": len(played),
        "upstreams": dict(served.most_common()),
        "trace_sample": _dedupe(
            [line for r in records for line in r.trace_sample])[:trace_lines],
    }


def _witnessed(records: list) -> dict:
    """Per seat-game: the share of the OTHER seats' decisions that fell back.

    ``None`` rather than ``0.0`` on an empty sample, the same refusal ``wilson``
    makes for the same reason - "0.00%" reads as a measurement of a clean table
    when what happened is that nothing was measured.
    """
    rates: list[float] = []
    for r in records:
        per_seat: Counter = Counter()
        fell_per_seat: Counter = Counter()
        for d in r.decision_log:
            # A decision_log entry is a dataclass on a live run and a plain dict
            # when a recorded JSONL is re-scored. Both are real callers, so read
            # both rather than making a re-score of an old run the odd case.
            seat = d["seat"] if isinstance(d, dict) else d.seat
            fell = d.get("fell_back") if isinstance(d, dict) else d.fell_back
            per_seat[seat] += 1
            if fell:
                fell_per_seat[seat] += 1
        total, fell = sum(per_seat.values()), sum(fell_per_seat.values())
        for seat, own in per_seat.items():
            others = total - own
            if others:
                rates.append((fell - fell_per_seat[seat]) / others)
    if not rates:
        return {"witnessed_rate": None, "witnessed_worst": None,
                "witnessed_any": 0, "witnessed_over_bar": 0, "seat_games": 0}
    return {
        "witnessed_rate": sum(rates) / len(rates),
        "witnessed_worst": max(rates),
        # two counts, because they answer different questions: `_any` is how many
        # seat-games had a random opponent at all, `_over_bar` is how many had
        # enough of one that the run-level rule would have voided them.
        "witnessed_any": sum(1 for x in rates if x > 0),
        "witnessed_over_bar": sum(1 for x in rates if x > VOID_BAR),
        "seat_games": len(rates),
    }


def _dedupe(lines: list[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        if line not in out:
            out.append(line)
    return out


def report_lines(i: dict) -> list[str]:
    """The integrity paragraph, identical in both games so a reader comparing two
    runs is comparing the same sentences."""
    lines = [f"integrity  {i['fallbacks']}/{i['decisions']} decisions fell back "
             f"to random ({i['fallback_rate']:.2%} caused)"]
    if i["witnessed_rate"] is not None:
        lines.append(
            f"  witnessed  {i['witnessed_rate']:.2%} of the decisions a seat played "
            f"AGAINST fell back ({i['witnessed_any']} of {i['seat_games']} "
            f"seat-games faced any; worst {i['witnessed_worst']:.2%}, "
            f"{i['witnessed_over_bar']} above the {VOID_BAR:.0%} bar)")
    transport = i["refused_attempts"] - i["rule_refused_attempts"]
    detail = ""
    if i["refused_attempts"]:
        detail = f"  ({i['rule_refused_attempts']} attempt(s)" + (
            f", plus {transport} that died in transport" if transport else "") + ")"
    lines.append(
        f"  recovered  {i['recovered']}/{i['decisions']} decisions "
        f"({i['recovered_rate']:.2%}) were sent back by the parser or the rules and "
        f"then answered legally" + detail)
    if i["recovered_rate"] > RECOVERED_WARN_BAR:
        lines.append(
            f"  NOTE: more than {RECOVERED_WARN_BAR:.0%} of decisions needed the "
            f"referee to send them back before the model got them right. Legal "
            f"play, and NOT a void - but this is not the same measurement as a run "
            f"that never missed, and a comparison across the two should say so.")
    if i["games_finished"]:
        lines.append(f"  clean      {i['clean_games']}/{i['games_finished']} games "
                     "ran with no fallback and nothing sent back")
    return lines
