"""Partial observability primitives - the spine of every game in the arena.

A player/agent may see exactly one thing: its own ``SeatView``. Anything not
reachable from that view must be underivable from it. That property (no seat can
learn another seat's secret role beyond its entitled reveals) is gate #1, and
``find_leaks`` is the mechanical check on the outgoing model payload - the same
job CoomKit's prompt inspector does: audit the exact bytes that leave for the
model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Knowledge:
    """One entitled reveal: what ``seat`` is, expressed as a fiction-safe label.

    The label is the whole reveal ("evil", "fellow-evil", "magic"), never the
    other seat's exact role. The seer learning a seat is "evil" must not also tell
    it which evil role that seat holds; the watcher's two "magic" seats must be
    indistinguishable from each other. Labels enforce that.
    """

    seat: int
    label: str


@dataclass
class SeatView:
    """Everything one seat may see, and nothing else. The only private channel.

    ``knowledge`` holds only entitled reveals. ``public`` is identical for every
    seat. If a fact is in neither, no correct render may expose it.
    """

    seat: int
    own_role: str
    own_team: str
    knowledge: tuple[Knowledge, ...]
    public: dict


def find_leaks(
    rendered: str,
    secret_terms: dict[int, list[str]],
    entitled: set[int],
    viewer: int,
) -> list[tuple[int, str]]:
    """Scan one seat's rendered context for another seat's secret.

    Returns ``(seat, term)`` for every non-entitled other seat whose secret term
    appears in ``viewer``'s outgoing context. Empty list means gate #1 holds for
    this seat. ``secret_terms`` maps seat -> the strings that would betray its
    role (canonical key and themed display name), so a leak is caught in either
    skin.
    """
    leaks: list[tuple[int, str]] = []
    low = rendered.lower()
    for seat, terms in secret_terms.items():
        if seat == viewer or seat in entitled:
            continue
        for term in terms:
            if term and term.lower() in low:
                leaks.append((seat, term))
    return leaks
