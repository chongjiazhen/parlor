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
member it covers. `TheLiveRungsConform` below is the separate, weaker assertion
that the live rungs satisfy the same names; neither test substitutes for the
other and both are kept.
"""

from __future__ import annotations

import unittest

from core.observability import SeatView
from core.seam import SEAM, Asked, Audited, Rendered, Transport, audit_render

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


class TheLiveRungsConform(unittest.TestCase):
    """The separate, weaker assertion: the seam is not fiction.

    `TheSeamCarriesTheAudit` proves the seam WORKS; this proves it DESCRIBES
    something. Neither substitutes for the other - a seam could be internally
    consistent and match no rung, or match every rung and audit nothing - so a
    rename must be able to fail one without the other.

    **`changeling` is the only rung that satisfies the whole of it, and that is
    recorded rather than papered over.** Measured 2026-09-04: `quorum` renders
    and hides nothing the seam can see, `cabal` has no `ask` and no
    `secret_terms`, `belfry` has everything but `entitled_seats`. A conformance
    test that asserted all four against the full seam would have to shrink the
    seam to the rendering core, which is exactly the accidental intersection the
    synthetic fixture exists to avoid inheriting.
    """

    @staticmethod
    def _referee(module: str):
        import importlib
        import inspect
        mod = importlib.import_module(module)
        return next(c for n, c in vars(mod).items()
                    if inspect.isclass(c) and n.endswith("Referee")
                    and c.__module__ == module)

    def test_every_rung_satisfies_the_rendering_core(self):
        for game in ("cabal", "changeling", "quorum", "belfry"):
            cls = self._referee(f"games.{game}.referee")
            for member in SEAM["Rendered"]:
                with self.subTest(game=game, member=member):
                    self.assertTrue(hasattr(cls, member),
                                    f"{game} lost {member}")

    def test_changeling_satisfies_the_whole_seam(self):
        """The rung a table is closest to, and the only one holding every member
        a table needs. If this ever fails, either changeling moved or the seam
        drifted away from the one rung that evidences it."""
        cls = self._referee("games.changeling.referee")
        for group in ("Audited", "Asked"):
            for member in SEAM[group]:
                with self.subTest(group=group, member=member):
                    self.assertTrue(hasattr(cls, member),
                                    f"changeling lost {member}")

    def test_the_shipped_transports_satisfy_the_protocol(self):
        """The console and the model backend are two implementations of the same
        one method, which is what makes a browser seat a third rather than a
        rewrite."""
        from core.backends import Backend
        from core.console import ConsoleBackend
        for cls in (Backend, ConsoleBackend):
            for member in SEAM["Transport"]:
                with self.subTest(transport=cls.__name__, member=member):
                    self.assertTrue(hasattr(cls, member))

    def test_the_written_member_list_matches_the_protocols(self):
        """SEAM is a hand-written copy of what the Protocols declare, kept because
        `__protocol_attrs__` is a CPython private that 3.10 - the floor this
        package claims - does not have. A copy is a thing that drifts, so it is
        checked against the computed answer wherever the interpreter has one, and
        skipped rather than silently trusted where it does not."""
        for proto in (Rendered, Audited, Asked, Transport):
            computed = getattr(proto, "__protocol_attrs__", None)
            if computed is None:
                self.skipTest("interpreter exposes no __protocol_attrs__")
            with self.subTest(protocol=proto.__name__):
                self.assertEqual(sorted(SEAM[proto.__name__]), sorted(computed))


if __name__ == "__main__":
    unittest.main()
