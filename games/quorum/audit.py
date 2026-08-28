"""Gate #1 as an executable guarantee, for a rung whose secrets are not words.

``assert_no_leak`` runs inside the game driver by default, so every game - demo,
test, and every game in an N-game eval - is audited at every reachable state and a
leak raises rather than being scored. It lives here rather than in ``core/``
because the spine must not know about this game's roles, cards or themes.

**Two mechanisms, because this rung has two kinds of secret and one scanner cannot
reach both.**

*Identity* is a word. A role's display name is a token that may appear in one
seat's payload and not another's, so ``core.observability.find_leaks`` reaches it
exactly as it does in cabal, and the repo invariant keeping that matcher naive
holds without argument.

*A card is not a word.* The vocabulary is shared with the public record: the
referee announces ``Enacted: Writ.`` on every event, so "a writ was enacted"
(public, legal) and "your discard was a writ" (private, a leak) are the same
substring. A scanner that could tell them apart would be a parser with opinions
about which sentence a term sits in, and it would be wrong on the first render
nobody predicted.

**So the second mechanism does not scan for a value - it asks whether the render
DEPENDS on one.** Take the state, replace every field this seat is not entitled
to with a different legal value, render again, and require the two renders to be
byte-identical. A render that changes is a render that read something it should
not have, whatever words came out; a render that does not change cannot be
carrying the field at all. That is a stronger property than substring matching,
not a weaker one - it catches a leak whose surface text looks innocent - and it
needs no new matcher, so ``find_leaks`` stays naive.

**A note on the first instinct, which was wrong and is worth recording.** The
obvious version of this is to substitute a UNIQUE POISON TOKEN and scan for it.
It does not survive contact: a token has to be a ``Card`` for the render to look
it up in the theme, so it needs a row in every skin's vocabulary and a side to
advance - and the seat that IS entitled would then legitimately render the token,
so the scan reports a leak on a legal turn. Substituting a different legal value
and comparing bytes has neither problem.
"""

from __future__ import annotations

import copy

from core.observability import find_leaks
from games.quorum.referee import Phase, QuorumReferee
from games.quorum.roles import Card, Side


class LeakDetected(AssertionError):
    """A seat's outgoing payload carried a secret it is not entitled to - either a
    role name it may not know, or a dependence on a card it may not see."""


#: The other card kind. One statement, so a variant that adds a third kind fails
#: loudly here rather than silently auditing nothing.
_OTHER_CARD = {Card.CHARTER: Card.WRIT, Card.WRIT: Card.CHARTER}

_OTHER_SIDE = {Side.MAJORITY: Side.MINORITY, Side.MINORITY: Side.MAJORITY}


# ---- the identity half -----------------------------------------------------

def secret_terms(ref: QuorumReferee) -> dict[int, list[str]]:
    """Each seat's role, in both skins - the sentinels a leak would trip."""
    return {
        s: [role.key, ref.theme.role_names[role.key]]
        for s, role in ref.assignment.items()
    }


def self_line(ref: QuorumReferee, seat: int) -> str:
    """The one line of a seat's render where its OWN role legitimately appears.

    It has to leave the audited corpus, and the reason is sharper here than in
    cabal: this setup seats THREE ``elector`` seats, so three seats hold the same
    display name by construction. The term one of them legitimately reads in "Your
    role: ..." is character-for-character the term that would betray the other two,
    and a naive scan reports a mutual leak on every call in every skin. The repo's
    standing remedy for a colliding term is to rename it, and that remedy cannot
    reach here - the collision IS the deal.

    So the corpus is narrowed rather than the matcher weakened, which is the same
    move ``include_speech=False`` already makes, and the same shape both sibling
    games arrived at independently. It removes ONE line: a duplicate term anywhere
    else in the payload is still caught.
    """
    v = ref.seat_view(seat)
    return f"You are seat {v.seat}. Your role: {v.own_role} ({v.own_team})."


def identity_leaks(ref: QuorumReferee) -> list[tuple[int, int, str]]:
    """Every ``(viewer, leaked_seat, term)``. Empty means no identity leaked.

    Audits the referee-authored payload only. A player naming a role out loud is a
    claim, true or false, and therefore gameplay; the referee doing it is the leak.
    """
    out: list[tuple[int, int, str]] = []
    terms = secret_terms(ref)
    for viewer in ref.assignment:
        rendered = ref.render_context(viewer, include_speech=False)
        rendered = rendered.replace(self_line(ref, viewer), "")
        for seat, term in find_leaks(rendered, terms, entitled={viewer},
                                     viewer=viewer):
            out.append((viewer, seat, term))
    return out


# ---- the cascade half ------------------------------------------------------

def _counterfactual(ref: QuorumReferee, viewer: int) -> QuorumReferee:
    """The same state with every field ``viewer`` is not entitled to replaced by a
    different legal value.

    Entitlement is read from the referee rather than restated here - ``ref`` alone
    decides who may see a hand, and it decides it from ``(office, phase)``. A second
    copy of that rule in the audit is how an audit comes to certify the bug it was
    written to catch.
    """
    alt = copy.copy(ref)
    alt.inspections = {k: dict(v) for k, v in ref.inspections.items()}

    # A hand the viewer may see stays as it is; every other hand flips. Which is
    # which comes from the referee's own accessor, at this phase, for this seat -
    # never from a second copy of the rule.
    sees_now = ref.entitled_hand(viewer) is not None
    keeps_proposer_hand = sees_now and ref.phase is Phase.PROPOSER_DISCARD
    keeps_enactor_hand = sees_now and ref.phase is Phase.ENACTOR_DISCARD
    if not keeps_proposer_hand:
        alt.proposer_hand = [_OTHER_CARD[c] for c in ref.proposer_hand]
    if not keeps_enactor_hand:
        alt.enactor_hand = [_OTHER_CARD[c] for c in ref.enactor_hand]

    # Nobody is entitled to the piles. Their COUNTS are public and must survive the
    # flip untouched, which is what makes this a real check rather than a tautology.
    alt.deck = [_OTHER_CARD[c] for c in ref.deck]
    alt.discards = [_OTHER_CARD[c] for c in ref.discards]

    # An inspection belongs to the seat that paid for it and to nobody else.
    for inspector, found in alt.inspections.items():
        if inspector != viewer:
            alt.inspections[inspector] = {s: _OTHER_SIDE[side]
                                          for s, side in found.items()}
    return alt


def dependence_leaks(ref: QuorumReferee) -> list[tuple[int, str]]:
    """Every ``(viewer, field)`` whose value reached that seat's payload.

    Empty means each seat's bytes are a function of what that seat is entitled to
    and of nothing else.
    """
    out: list[tuple[int, str]] = []
    for viewer in ref.assignment:
        base = ref.render_context(viewer, include_speech=False)
        alt = _counterfactual(ref, viewer)
        if alt.render_context(viewer, include_speech=False) != base:
            out.append((viewer, _blame(ref, viewer)))
    return out


def _blame(ref: QuorumReferee, viewer: int) -> str:
    """Which unentitled field the render moved on, flipped one at a time.

    Reported rather than left as "something changed" because a leak that cannot be
    attributed is a leak somebody argues about. If no single field reproduces it,
    say so instead of guessing - two fields interacting is a real answer.
    """
    base = ref.render_context(viewer, include_speech=False)
    for field in ("proposer_hand", "enactor_hand", "deck", "discards",
                  "inspections"):
        alt = copy.copy(ref)
        alt.inspections = {k: dict(v) for k, v in ref.inspections.items()}
        full = _counterfactual(ref, viewer)
        setattr(alt, field, getattr(full, field))
        if alt.render_context(viewer, include_speech=False) != base:
            return field
    return "unattributed (no single field reproduces it)"


# ---- the gate --------------------------------------------------------------

def assert_no_leak(ref: QuorumReferee) -> None:
    """Raise on any gate #1 violation. The driver calls this every turn."""
    ident = identity_leaks(ref)
    if ident:
        viewer, seat, term = ident[0]
        raise LeakDetected(
            f"gate #1 violated in seat {viewer}'s context: it names seat {seat} "
            f"via {term!r}")
    depend = dependence_leaks(ref)
    if depend:
        viewer, field = depend[0]
        raise LeakDetected(
            f"gate #1 violated in seat {viewer}'s context: the render depends on "
            f"{field}, which that seat is not entitled to at phase "
            f"{ref.phase.value}")
