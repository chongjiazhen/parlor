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
    self_is_secret: bool = False,
) -> list[tuple[int, str]]:
    """Scan one seat's rendered context for a secret it is not entitled to.

    Returns ``(seat, term)`` for every non-entitled seat whose secret term appears
    in ``viewer``'s outgoing context. Empty list means gate #1 holds for this seat.
    ``secret_terms`` maps seat -> the strings that would betray its role (canonical
    key and themed display name), so a leak is caught in either skin.

    ``self_is_secret`` decides whether the VIEWER'S OWN secret is audited against
    its own render, and it defaults to off because the first game in this arena
    could not need it: there a seat's role is a fact it holds from the deal to the
    end, so its own term appears in its own context by design and auditing it would
    report a leak on every call.

    That was an assumption, and the second game found it. Where a seat's belief
    about itself can diverge from what it holds - a card moved while it slept - the
    seat is no longer entitled to its own truth, and a referee leaking that truth
    back to it is a gate #1 failure of exactly the kind this function exists to
    catch. Such a caller passes ``self_is_secret=True`` and puts the viewer in
    ``entitled`` for the games where the two still agree.

    The flag is here rather than in the caller because the skip it removes was
    here: a game cannot opt out of a rule the primitive applies before it is asked.
    """
    leaks: list[tuple[int, str]] = []
    low = rendered.lower()
    for seat, terms in secret_terms.items():
        if seat in entitled:
            continue
        if seat == viewer and not self_is_secret:
            continue
        for term in terms:
            if term and term.lower() in low:
                leaks.append((seat, term))
    return leaks
