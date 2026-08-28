"""Gate #1 as an executable guarantee, not a habit.

Same contract as the other rungs': ``assert_no_leak`` runs inside the driver by
default and a leak raises rather than being scored, because the property this
arena exists to prove must not be something a caller can forget to switch on.

What this rung adds is the surface. The other games audit a payload the referee
built out of true statements; here the referee builds some of them out of false
ones on purpose, and a lie that landed on the truth is a leak like any other. The
check does not have to know which is which - it reads the bytes and the
entitlement the referee committed to when it wrote them, which is exactly the
point of grading a referee on its output rather than on its intentions.
"""

from __future__ import annotations

from games.belfry.referee import BelfryReferee


class LeakDetected(AssertionError):
    """A seat's outgoing payload named a role it is not entitled to know - another
    seat's, or, for the seat that is wrong about itself, its own."""


def leak_audit(ref: BelfryReferee) -> list[tuple[int, int, str]]:
    """Every ``(viewer, leaked_seat, term)``. Empty means gate #1 holds.

    For the seat on the clock the ASK is audited too. It carries seat numbers -
    the legal-target list, the nominee, the master - so it is exactly the string a
    convenience would one day interpolate a role into, and it is bytes leaving for
    the model like any other.
    """
    out: list[tuple[int, int, str]] = []
    acting = set(ref.acting_seats())
    terms = ref.secret_terms()
    for viewer in range(ref.n):
        for seat, term in ref.audit(viewer):
            out.append((viewer, seat, term))
        if viewer in acting:
            ask = ref.ask(viewer).lower()
            for seat in range(ref.n):
                if seat in ref.entitled[viewer]:
                    continue
                for form in terms[seat]:
                    if form.lower() in ask:
                        out.append((viewer, seat, form))
    return out


def assert_no_leak(ref: BelfryReferee) -> None:
    leaks = leak_audit(ref)
    if leaks:
        raise LeakDetected(f"gate #1 violated: {leaks}")
