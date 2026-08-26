"""Gate #1 as an executable guarantee, not a habit.

Same contract as ``games/cabal/audit.py``, and here for the same reason: the
no-leak property must not depend on a caller remembering to check it, so
``assert_no_leak`` runs inside the driver by default and a leak raises rather than
being scored. The eval lane once forgot to pass an opt-in callback and ran live
models unaudited for a session; that is why the default is on and not a flag.

What this game adds to the cabal version is in ``referee.audit``: a seat's OWN dawn
card is a secret from that seat once its belief has diverged, and secrets are
matched as seat-card associations rather than as bare card names, because this deck
holds duplicates. Both arguments live next to the code that implements them.
"""

from __future__ import annotations

from games.changeling.referee import ChangelingReferee, Phase


class LeakDetected(AssertionError):
    """A seat's outgoing payload named a dawn card it is not entitled to know -
    another seat's, or, uniquely to this game, its own."""


def leak_audit(ref: ChangelingReferee) -> list[tuple[int, int, str]]:
    """Every ``(viewer, leaked_seat, term)``. Empty means gate #1 holds.

    For whichever seats are on the clock, the ASK is audited too: it is bytes
    leaving for the model like any other.
    """
    out: list[tuple[int, int, str]] = []
    acting = set(ref.acting_seats())
    for viewer in range(ref.n):
        for seat, term in ref.audit(viewer):
            out.append((viewer, seat, term))
        if viewer in acting:
            # The ask carries no seat-card association today, and this is what
            # keeps that true tomorrow rather than a comment claiming it.
            ask = ref.ask(viewer)
            for seat in range(ref.n):
                for form in ref.secret_terms()[seat]:
                    if form.lower() in ask.lower():
                        out.append((viewer, seat, form))
    return out


def assert_no_leak(ref: ChangelingReferee) -> None:
    leaks = leak_audit(ref)
    if leaks:
        raise LeakDetected(f"gate #1 violated: {leaks}")
