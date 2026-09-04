"""The table-facing seam, asserted against a synthetic implementation.

`core/` has no Protocol and no ABC anywhere else: the referee contract is
duck-typed, and `core/registry.py` says why there was never a factory - nothing
needed one. A separate private repo consuming this package as an installed
dependency does need one, because a rename here would break it silently in a tree
this suite cannot see.

**The synthetic implementation is the point, not a convenience.** A test that
read the seam off the live rungs would pass on whatever they happen to expose
today, which is the failure mode `rules/code-modification` names for a test
pinned to a registry read rather than a fixture. The class below implements the
seam and NOTHING else, so a member the seam does not declare cannot be reached by
accident, and a member it declares but nobody calls shows up as an unused stub.

**Presence is not signature.** `runtime_checkable` checks that an attribute
exists and never what it accepts or returns, so every test here CALLS through the
member it covers. `core/test_seam_conformance` is the separate, weaker assertion
that the live rungs satisfy the same names; neither test substitutes for the
other and both are kept.
"""

from __future__ import annotations

import unittest

from core.observability import SeatView
from core.seam import Transport, audit_render

#: The two secrets the synthetic referee holds. Distinct, non-colliding words:
#: the repo invariant is that `find_leaks` stays naive and a colliding term gets
#: RENAMED, so a fixture that collided with ordinary English would be testing the
#: matcher's tolerance rather than the seam.
BELL = "bellwether"
NIGHTJAR = "nightjar"


class _Ref:
    """A referee that satisfies the seam and implements nothing beyond it.

    Two seats, one secret each. ``prompt_for`` and ``render_context`` return
    whatever the test handed the constructor, because what this fixture exists to
    exercise is the audit over bytes, not the production of them.
    """

    n = 2
    phase = "discuss"

    def __init__(self, rendered: str, entitled: frozenset = frozenset()):
        self._rendered = rendered
        self._entitled = set(entitled)

    def prompt_for(self, seat: int, include_speech: bool = True) -> str:
        return self._rendered

    def render_context(self, seat: int, include_speech: bool = True) -> str:
        return self._rendered

    def seat_view(self, seat: int) -> SeatView:
        return SeatView(seat=seat, own_role="role", own_team="team",
                        knowledge=(), public={})

    def acting_seats(self):
        return (0,)

    def ask(self, seat: int) -> str:
        return "name a seat"

    def secret_terms(self):
        return {0: [BELL], 1: [NIGHTJAR]}

    def entitled_seats(self, viewer: int):
        return set(self._entitled)


class _Transport:
    """The decision transport, which is one method and its two return values."""

    def complete_meta(self, context: str,
                      history: list[tuple[str, str]] | None = None):
        return (f"saw:{context}", "synthetic")


class TheSeamCarriesTheAudit(unittest.TestCase):
    """`audit_render` is the single place a table reaches `find_leaks`.

    It takes the rendered string rather than computing it, so a caller audits the
    exact bytes it is about to send. durf found the alternative silently wrong:
    an entitlement recomputed at audit time lets a fact declared LATER make an
    earlier render read clean.
    """

    def test_a_render_naming_no_secret_is_clean(self):
        ref = _Ref("the table talks about the weather")
        self.assertEqual(audit_render(ref, 0, ref.prompt_for(0)), [])

    def test_a_render_naming_another_seats_secret_is_caught(self):
        ref = _Ref(f"seat one is the {NIGHTJAR}")
        self.assertEqual(audit_render(ref, 0, ref.prompt_for(0)),
                         [(1, NIGHTJAR)])

    def test_an_entitled_viewer_sees_no_leak(self):
        """Entitlement is what separates a reveal from a leak, so the same bytes
        must audit clean for a viewer that was told."""
        ref = _Ref(f"seat one is the {NIGHTJAR}", entitled=frozenset({1}))
        self.assertEqual(audit_render(ref, 0, ref.prompt_for(0)), [])

    def test_the_viewers_own_secret_is_skipped(self):
        """A seat holds its own role from the deal, so its own term appears in
        its own context by design. The primitive's self-skip is what keeps that
        from reporting a leak on every call, and the seam must not defeat it."""
        ref = _Ref(f"you are the {BELL}")
        self.assertEqual(audit_render(ref, 0, ref.prompt_for(0)), [])

    def test_the_ask_is_auditable_by_the_same_call(self):
        """The ask is bytes leaving for the model like any other, and the seam
        has to be able to audit it without a second entry point."""
        ref = _Ref("")
        self.assertEqual(audit_render(ref, 0, ref.ask(0)), [])


class TheTransportReturnsAReplyAndItsSource(unittest.TestCase):
    def test_complete_meta_returns_both_halves(self):
        reply, served_by = _Transport().complete_meta("context")
        self.assertEqual(reply, "saw:context")
        self.assertEqual(served_by, "synthetic")

    def test_history_is_accepted_and_optional(self):
        """A table replays earlier turns of the same session, so the seam has to
        carry the parameter or every table would reach past it."""
        reply, _ = _Transport().complete_meta("context", [("ask", "reply")])
        self.assertEqual(reply, "saw:context")

    def test_the_synthetic_transport_satisfies_the_declared_protocol(self):
        self.assertIsInstance(_Transport(), Transport)


if __name__ == "__main__":
    unittest.main()
