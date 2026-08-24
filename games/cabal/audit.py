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
    """A seat's outgoing payload named a role it is not entitled to know."""


def secret_terms(ref: CabalReferee) -> dict[int, list[str]]:
    """Each seat's role, in both skins - the sentinels a leak would trip."""
    return {
        s: [role.key, ref.theme.role_names[role.key]]
        for s, role in ref.assignment.items()
    }


def leak_audit(ref: CabalReferee) -> list[tuple[int, int, str]]:
    """Return every (viewer, leaked_seat, term). Empty == gate #1 holds.

    Audits the referee-authored payload only: ``include_speech=False`` drops other
    players' utterances, because a player naming a role out loud is a claim (true
    or false) and therefore gameplay. The referee doing it would be the leak. For
    whichever seats are on the clock, the ask is audited too - it is bytes that
    leave for the model like any other, and a role name added to a prompt string
    is exactly the regression that would otherwise go unseen.
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
        for seat, term in find_leaks(payload, terms, entitled, viewer):
            out.append((viewer, seat, term))
    return out


def assert_no_leak(ref: CabalReferee) -> None:
    leaks = leak_audit(ref)
    if leaks:
        raise LeakDetected(f"gate #1 violated: {leaks}")
