"""`find_leaks` - the key, the entitlement rule and the self-skip.

The primitive's game-level coverage lives with the games that call it
(`games/cabal/test_leak_audit.py` is the oldest). What is pinned here is the KEY:
a secret used to be keyed to a seat and a seat only, so entitlement was
all-or-nothing over everything that seat hides. That is a false negative wherever
a seat holds more than one independent secret - the direction `AGENTS.md`'s first
invariant forbids by name - and the tests below hold the widened key and, just as
importantly, hold the old seat-keyed behaviour byte-for-byte, because six call
sites depend on it and none of them passes an axis.
"""

from __future__ import annotations

import unittest

from core.observability import find_leaks


class TestSeatKeyedIsUnchanged(unittest.TestCase):
    """Every existing caller passes bare seat ints. None of it may move."""

    def test_a_foreign_secret_in_the_render_is_a_leak(self):
        hits = find_leaks("seat 3 is the mimic", {3: ["mimic"]}, set(), viewer=2)
        self.assertEqual(hits, [(3, "mimic")])

    def test_an_entitled_seat_is_skipped(self):
        hits = find_leaks("seat 3 is the mimic", {3: ["mimic"]}, {3}, viewer=2)
        self.assertEqual(hits, [])

    def test_the_viewer_s_own_secret_is_skipped_by_default(self):
        hits = find_leaks("you are the mimic", {2: ["mimic"]}, set(), viewer=2)
        self.assertEqual(hits, [])

    def test_self_is_secret_audits_the_viewer_s_own(self):
        hits = find_leaks("you are the mimic", {2: ["mimic"]}, set(), viewer=2,
                          self_is_secret=True)
        self.assertEqual(hits, [(2, "mimic")])

    def test_matching_is_case_folded_substring(self):
        hits = find_leaks("SEAT 3 IS THE MIMIC", {3: ["mimic"]}, set(), viewer=2)
        self.assertEqual(hits, [(3, "mimic")])

    def test_a_blank_term_is_skipped(self):
        self.assertEqual(find_leaks("anything", {3: [""]}, set(), viewer=2), [])

    def test_a_negative_viewer_never_matches_a_key(self):
        """DURF numbers facts from 0 and passes -1, so the self-skip cannot fire."""
        hits = find_leaks("the anchor is rotted", {0: ["rotted"]}, set(), viewer=-1)
        self.assertEqual(hits, [(0, "rotted")])


class TestPerAxisKey(unittest.TestCase):
    """A seat may hold several independent secrets, each entitled separately."""

    TERMS = {(3, "faction"): ["the syndicate"], (3, "deviation"): ["pyromania"]}

    def test_entitlement_to_one_axis_does_not_excuse_another(self):
        """The false negative this widening exists to close."""
        hits = find_leaks("seat 3 is the syndicate and has pyromania",
                          self.TERMS, {(3, "faction")}, viewer=2)
        self.assertEqual(hits, [((3, "deviation"), "pyromania")])

    def test_the_entitled_axis_itself_is_still_skipped(self):
        hits = find_leaks("seat 3 is the syndicate", self.TERMS,
                          {(3, "faction")}, viewer=2)
        self.assertEqual(hits, [])

    def test_entitlement_to_the_whole_seat_covers_every_axis(self):
        """A caller that knows nothing of axes keeps its all-or-nothing power."""
        hits = find_leaks("seat 3 is the syndicate and has pyromania",
                          self.TERMS, {3}, viewer=2)
        self.assertEqual(hits, [])

    def test_no_entitlement_reports_every_axis(self):
        hits = find_leaks("seat 3 is the syndicate and has pyromania",
                          self.TERMS, set(), viewer=2)
        self.assertEqual(sorted(hits), [((3, "deviation"), "pyromania"),
                                        ((3, "faction"), "the syndicate")])

    def test_the_self_skip_reads_the_seat_out_of_an_axis_key(self):
        hits = find_leaks("you are the syndicate", self.TERMS, set(), viewer=3)
        self.assertEqual(hits, [])

    def test_self_is_secret_reaches_the_viewer_s_own_axes(self):
        hits = find_leaks("you are the syndicate", self.TERMS, set(), viewer=3,
                          self_is_secret=True)
        self.assertEqual(hits, [((3, "faction"), "the syndicate")])

    def test_an_axis_key_and_a_seat_key_may_share_one_scan(self):
        """Mixed keys: a game widening one seat need not renumber the others."""
        terms = {2: ["mimic"], (3, "deviation"): ["pyromania"]}
        hits = find_leaks("the mimic and pyromania", terms, set(), viewer=0)
        self.assertEqual(set(hits), {(2, "mimic"),
                                     ((3, "deviation"), "pyromania")})


if __name__ == "__main__":
    unittest.main()
