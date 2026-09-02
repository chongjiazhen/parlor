"""Gate #1 as an executable guarantee, not a habit.

The no-leak property is the reason this project exists, so it must not depend on
a caller remembering to check it. ``assert_no_leak`` runs inside the game driver
by default (``play_game(..., audit=True)``), which means every game - demo, test,
and every game in an N-game eval - is audited at every reachable state, and a leak
raises rather than being scored.

It lives here rather than in ``demo.py`` because the eval lane needs it too, and
rather than in ``core/observability.py`` because the spine must not know about
this game's roles or themes.
"""

from __future__ import annotations

from core.observability import find_leaks
from games.cabal.referee import CabalReferee


class LeakDetected(AssertionError):
    """A seat's outgoing payload named a role it is not entitled to know, or
    carried a line of the evil pair's conference to a seat outside the pair."""


def secret_terms(ref: CabalReferee) -> dict[int, list[str]]:
    """Each seat's role, in both skins - the sentinels a leak would trip."""
    return {
        s: [role.key, ref.theme.role_names[role.key]]
        for s, role in ref.assignment.items()
    }


def self_line(ref: CabalReferee, seat: int) -> str:
    """The one line of a seat's render where its OWN role and faction legitimately
    appear, verbatim.

    It is reconstructed here rather than exported by the referee because the
    referee's strings are the prompt: lifting that line into a helper would be a
    render refactor, and this is an audit-side concern. The duplication is held
    honest by a test asserting the line is actually present in every seat's payload
    under every shipped theme - so a render that moves it fails loudly instead of
    letting the strip below quietly match nothing.
    """
    v = ref.seat_view(seat)
    return f"You are seat {v.seat}. Your role: {v.own_role} ({v.own_team})."


def leak_audit(ref: CabalReferee) -> list[tuple[int, int, str]]:
    """Return every (viewer, leaked_seat, term). Empty == gate #1 holds.

    Audits the referee-authored payload only: ``include_speech=False`` drops other
    players' utterances, because a player naming a role out loud is a claim (true
    or false) and therefore gameplay. The referee doing it would be the leak. For
    whichever seats are on the clock, the ask is audited too - it is bytes that
    leave for the model like any other, and a role name added to a prompt string
    is exactly the regression that would otherwise go unseen.

    **A seat's own self-declaration leaves the audited corpus, and that is what
    makes a repeated role auditable at all.** Two seats dealt the same role hold
    the same secret term by construction, so the term one of them legitimately
    reads in "Your role: ..." is character-for-character the term that would betray
    the other. A naive scan reports a mutual leak in every skin - measured on a
    hand-built 7-seat deal with two ``loyalist`` seats, which is the setup this
    exists for. The repo's standing remedy for a colliding term is to rename it,
    and that remedy cannot reach here: the collision IS the deal, and renaming one
    ``loyalist`` breaks it.

    So the corpus is narrowed rather than the matcher weakened, exactly as
    ``include_speech=False`` already narrows it, and ``find_leaks`` stays naive per
    the repo invariant. This is not a skip: it removes ONE line, the only place the
    referee asserts a seat's role to that seat, so a duplicate term appearing
    anywhere else in the payload - a public event, the blurb, the ask, a future
    reveal - is still caught. The sibling game reached the same shape from the
    other direction (``games/changeling`` audits a seat's own card against its own
    line only), which is evidence about the shape rather than a coincidence.
    """
    terms = secret_terms(ref)
    acting = set(ref.acting_seats())
    out = []
    for viewer in ref.assignment:
        entitled = {k.seat for k in ref.entitled_knowledge(viewer)}
        payload = (
            ref.prompt_for(viewer, include_speech=False) if viewer in acting
            else ref.render_context(viewer, include_speech=False)
        )
        payload = payload.replace(self_line(ref, viewer), "", 1)
        for seat, term in find_leaks(payload, terms, entitled, viewer):
            out.append((viewer, seat, term))
    out += conference_audit(ref)
    return out


def conference_audit(ref: CabalReferee) -> list[tuple[int, int, str]]:
    """The second class of secret: the evil pair's conference before the hunt.

    Its bytes are entitled to the pair by the deal and to nobody else, so each
    rendered line is treated as a secret TERM of its speaker and hunted for in
    every other seat's payload with the same naive ``find_leaks``. The scan runs
    over the FULL payload - speech and notebook included - because these are
    player-authored bytes that the audit view above deliberately drops, and the
    question here is not "did the referee name a role" but "did these bytes reach a
    seat outside the pair" - which is exactly what the model would receive.

    The term is the whole rendered line, ``seat N confers: "..."``, so a good seat
    that happens to say the same words out loud does not trip it; only the
    referee's own framing of the pair's words does. A pair member is entitled to
    its partner's lines and skips its own, so a clean board audits clean.
    """
    lines = ref.conference_lines()
    if not lines:
        return []
    terms: dict[int, list[str]] = {}
    for speaker, rendered in lines:
        terms.setdefault(speaker, []).append(rendered)
    party = set(ref.conference_seats())
    acting = set(ref.acting_seats())
    out = []
    for viewer in ref.assignment:
        entitled = party if viewer in party else set()
        payload = (ref.prompt_for(viewer) if viewer in acting
                   else ref.render_context(viewer))
        for seat, term in find_leaks(payload, terms, entitled, viewer):
            out.append((viewer, seat, term))
    return out


def assert_no_leak(ref: CabalReferee) -> None:
    leaks = leak_audit(ref)
    if leaks:
        raise LeakDetected(f"gate #1 violated: {leaks}")
