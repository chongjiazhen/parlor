"""Partial observability primitives - the spine of every game in the arena.

A player/agent may see exactly one thing: its own ``SeatView``. Anything not
reachable from that view must be underivable from it. That property (no seat can
learn another seat's secret role beyond its entitled reveals) is gate #1, and
``find_leaks`` is the mechanical check on the outgoing model payload - the same
job a prompt inspector does: audit the exact bytes that leave for the model.
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


#: What a secret is keyed to. A bare seat is the original key and still the one
#: every game in the tree passes; ``(seat, axis)`` names ONE of the several
#: independent secrets a seat may hold, so entitlement can be granted to one
#: without granting the rest.
SecretKey = int | tuple[int, str]


def subject(key: SecretKey) -> int:
    """The seat a secret is about, whether the key names an axis or not."""
    return key[0] if isinstance(key, tuple) else key


def find_leaks(
    rendered: str,
    secret_terms: dict[SecretKey, list[str]],
    entitled: set[SecretKey],
    viewer: int,
    self_is_secret: bool = False,
) -> list[tuple[SecretKey, str]]:
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

    **A key may name an AXIS.** ``secret_terms`` was keyed to a seat and a seat
    only, which makes entitlement all-or-nothing over everything that seat hides:
    a viewer told one of seat 3's secrets was skipped on ALL of seat 3's terms,
    and a leak of the others reported clean. That is the false-negative direction
    the repo's first invariant forbids by name. A key may now be ``(seat, axis)``,
    and the two rules that read a key read it through ``subject``: entitlement is
    granted to a KEY, or to a bare seat which covers every axis of it, and the
    self-skip is about the seat the secret is ABOUT.

    Nothing in the tree passes an axis yet - six call sites, all seat-keyed, all
    unchanged by construction, since a bare ``int`` takes both branches exactly
    as before. What the widening buys is that a game which needs axes can adopt
    them without the primitive reporting the viewer's own secrets at it, which is
    the pressure that would send it back to a flat seat key.
    """
    leaks: list[tuple[SecretKey, str]] = []
    low = rendered.lower()
    for key, terms in secret_terms.items():
        seat = subject(key)
        if key in entitled or seat in entitled:
            continue
        if seat == viewer and not self_is_secret:
            continue
        for term in terms:
            if term and term.lower() in low:
                leaks.append((key, term))
    return leaks
