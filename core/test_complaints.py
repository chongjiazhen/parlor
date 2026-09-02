"""The complaint table, and the pin that keeps the shipped wording from drifting.

``core/replies.py`` raises the text a seat reads back when its reply could not be
parsed. Five games share the module, so the wording is a MEASURED string for one
of them (`docs/model-facing-text.md`, `games/changeling/phrasing.py`) and frozen
bytes for the other four. Both have to be true at once, and both are tested here
rather than argued in a docstring:

- **The default is byte-identical to what shipped.** ``GOLDEN_AS_IS`` is a sha256
  over every complaint the module can raise, rendered in a fixed order. It was
  computed against the tree BEFORE the table existed, so a default that drifts
  fails here and nowhere else.
- **The table actually reaches every call site.** ``test_every_slot_has_a
  _consumer`` swaps in a table of unique sentinels and requires each one back. A
  slot with no consumer sits unread while a golden hash still pins it, which is
  the failure this test exists to catch.

The four games that pass no table are pinned separately, through their own
``parse_action``, in ``TestTheOtherGamesAreByteIdentical``.
"""

from __future__ import annotations

import hashlib
import unittest
from dataclasses import fields
from types import SimpleNamespace

from core.replies import (
    AS_IS_COMPLAINTS,
    Complaints,
    ParseError,
    extract_json,
    parse_bool,
    parse_index,
    parse_index_set,
    salvage,
)

KEYS = ("team", "vote", "card", "say", "target", "think")

#: sha256 of ``corpus()`` under the default table, computed on the tree before
#: this module landed.
GOLDEN_AS_IS = ("7925ffc156cf9873711e02c5fbed90b3fd5694af98c0eb8bc5f831fa2"
                "e533f82")


def grab(fn, *args, **kwargs) -> str:
    """The complaint ``fn`` raises, or a failure. A call that PARSES is a broken
    fixture rather than a passing test, so it raises rather than returning ""."""
    try:
        fn(*args, **kwargs)
    except ParseError as exc:
        return str(exc)
    raise AssertionError(f"{fn.__name__} did not refuse {args!r}")


def corpus(**kw) -> str:
    """Every complaint this module can raise, in a fixed order.

    ``kw`` is the optional ``complaints=`` table, threaded to every call, so the
    same fixture serves the golden pin and the sentinel sweep.
    """
    out = [
        grab(extract_json, "no braces here at all", **kw),
        grab(salvage, "no braces here at all", KEYS, **kw),
        grab(parse_bool, "maybe", **kw),
        grab(parse_index, True, 5, **kw),
        grab(parse_index, "the one on the left", 5, **kw),
        grab(parse_index, 9, 5, **kw),
        grab(parse_index, True, 3, noun="card", **kw),
        grab(parse_index, "the red one", 3, noun="card", **kw),
        grab(parse_index, 7, 3, noun="card", **kw),
        grab(parse_index_set, {"a": 1}, 5, 2, **kw),
        grab(parse_index_set, [1, 1], 5, 2, **kw),
    ]
    return "\n<<>>\n".join(out)


class TestTheDefaultIsPinned(unittest.TestCase):
    def test_corpus_is_byte_identical_to_what_shipped(self):
        text = corpus()
        self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), GOLDEN_AS_IS)

    def test_passing_the_default_explicitly_is_the_same_bytes(self):
        self.assertEqual(corpus(), corpus(complaints=AS_IS_COMPLAINTS))


class TestTheTableReachesEveryCallSite(unittest.TestCase):
    def test_every_slot_has_a_consumer(self):
        """A slot nothing renders is a promise the arm does not keep.

        The golden hash above pins an unread slot just as happily as a read one,
        so the table is swapped for unique sentinels and each one required back.
        """
        names = [f.name for f in fields(Complaints) if f.name != "name"]
        # Placeholders differ per slot, so each template keeps its own and only
        # a leading marker is prepended.
        table = Complaints(name="sentinel", **{
            n: f"SENTINEL-{n} " + getattr(AS_IS_COMPLAINTS, n) for n in names})
        rendered = corpus(complaints=table)
        for n in names:
            with self.subTest(slot=n):
                self.assertIn(f"SENTINEL-{n} ", rendered)

    def test_a_swapped_table_changes_what_a_seat_reads(self):
        table = Complaints(name="other", **{
            f.name: "rewritten " + getattr(AS_IS_COMPLAINTS, f.name)
            for f in fields(Complaints) if f.name != "name"})
        self.assertNotEqual(corpus(), corpus(complaints=table))


class TestTheOtherGamesAreByteIdentical(unittest.TestCase):
    """cabal, belfry, quorum and durf pass no table. Their seats must read the
    strings the golden hash above pins, driven through their OWN parse path -
    a default argument nobody exercises is not a proof."""

    def test_cabal(self):
        from games.cabal.player import parse_seat, parse_team
        self.assertEqual(grab(parse_seat, "the left one", 5),
                         "no seat number in 'the left one'")
        self.assertEqual(grab(parse_team, [1, 1], 5, 2),
                         "expected 2 distinct seats, got [1, 1]")

    def test_belfry(self):
        from games.belfry.player import parse_action
        ref = SimpleNamespace(n=5)
        turn = SimpleNamespace(kind="nominate")
        self.assertEqual(
            grab(parse_action, '{"nominate": "the left one"}', ref, turn),
            "no seat number in 'the left one'")
        self.assertEqual(
            grab(parse_action, 'no object here', ref, turn),
            "nothing salvageable in reply: 'no object here'")
        self.assertEqual(
            grab(parse_action, '{"vote": "perhaps"}', ref,
                 SimpleNamespace(kind="vote")),
            "cannot read 'perhaps' as a yes/no")

    def test_quorum(self):
        from games.quorum.player import parse_action
        from games.quorum.referee import Phase
        ref = SimpleNamespace(n=5, phase=Phase.NOMINATE)
        self.assertEqual(
            grab(parse_action, '{"nominate": 9}', ref, 0),
            "seat 9 is outside 0..4")
        self.assertEqual(
            grab(parse_action, '{"nominate": true}', ref, 0),
            "True is not a seat")

    def test_durf(self):
        from games.durf.seats import _obj
        self.assertEqual(grab(_obj, "no object here", ("say", "do")),
                         "nothing salvageable in reply: 'no object here'")


if __name__ == "__main__":
    unittest.main()
