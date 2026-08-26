"""The belief/truth split, which is the only reason this rung exists.

Every test here is about one property: a seat's knowledge of its own card can be
stale or false, and nothing in the night tells it. A referee that renders truth
where belief was due passes every `cabal`-era test and is wrong, so these assert on
the divergence directly rather than on the game's outcome.
"""

from __future__ import annotations

import random
import unittest

from games.changeling.night import (ImpossibleDeal, NightResult, centre_ref,
                                    deal, legal_targets, resolve_night)
from games.changeling.roles import (BYSTANDER, DECEIVED, PACK, SPOTTER, SWAPPER,
                                    SWITCHER, Act, Setup, Side)


def scripted(script: dict):
    """A chooser that plays one exact night. ``script`` maps Act -> the option to
    take, so a test states the night it means instead of hunting for a seed."""
    def choose(seat: int, act: Act, options: list):
        assert act in script, (
            f"seat {seat} was asked for {act.value} and the script does not say - "
            "pin the deal, or script every act the deck can produce")
        want = script[act]
        assert want in options, f"scripted {act} target {want!r} is not legal"
        return want
    return choose


def night(deck, seats, centre, script=None, n=None):
    """One NAMED night: the deal is pinned, so a test asserts about the position it
    describes rather than about whatever a seed happened to deal."""
    setup = Setup(n=n or len(seats), deck=tuple(deck), centre=len(centre),
                  require_seated_pack=False)
    return resolve_night(setup, random.Random(0), scripted(script or {}),
                         dealt=dict(enumerate(seats)), centre=list(centre))


def keys(mapping) -> dict:
    return {s: c.key for s, c in mapping.items()}


class TestDeal(unittest.TestCase):
    def test_every_deal_seats_a_pack(self):
        """Unconstrained, 6/56 of deals seat no pack and the day is undefined."""
        from games.changeling.roles import SETUP_5
        for seed in range(300):
            seats, _ = deal(SETUP_5, random.Random(seed))
            self.assertTrue(any(c.side is Side.PACK for c in seats.values()),
                            f"seed {seed} seated no pack")

    def test_a_deck_that_cannot_seat_a_pack_RAISES(self):
        """The predicate is the policy; the bound beside it is what stops an
        unsatisfiable one spinning forever unattended."""
        packless = Setup(n=2, deck=(BYSTANDER, BYSTANDER, SPOTTER), centre=1)
        with self.assertRaises(ImpossibleDeal):
            deal(packless, random.Random(0))

    def test_deck_that_cannot_fill_the_table_is_refused_at_construction(self):
        with self.assertRaises(ValueError):
            Setup(n=5, deck=(PACK, PACK), centre=3)


class TestNoSwapMeansNoDivergence(unittest.TestCase):
    """The control. Without it every divergence test below proves nothing - a night
    that diverged every seat would pass all of them."""

    def test_a_night_with_no_mover_leaves_belief_equal_to_truth(self):
        r = night(deck=(PACK, SPOTTER, BYSTANDER, BYSTANDER),
                  seats=(PACK, SPOTTER, BYSTANDER), centre=(BYSTANDER,),
                  script={Act.LOOK: ("seat", 0)})
        self.assertEqual(keys(r.truth), keys(r.belief))
        self.assertEqual(r.diverged(), set())


class TestTake(unittest.TestCase):
    """The robber looks; its victim is never told. The first way the two split."""

    def setUp(self):
        self.r = night(deck=(SWAPPER, PACK, BYSTANDER),
                       seats=(SWAPPER, PACK), centre=(BYSTANDER,),
                       script={Act.TAKE: ("seat", 1)})

    def test_the_robber_belief_follows_its_new_truth(self):
        self.assertEqual(self.r.truth[0].key, "pack")
        self.assertEqual(self.r.belief[0].key, "pack")
        self.assertNotIn(0, self.r.diverged())

    def test_the_victim_holds_swapper_and_still_believes_its_old_card(self):
        self.assertEqual(self.r.truth[1].key, "swapper")
        self.assertEqual(self.r.belief[1].key, "pack")
        self.assertIn(1, self.r.diverged())

    def test_the_victim_is_told_nothing(self):
        self.assertEqual(self.r.knowledge[1], ())


class TestSwitch(unittest.TestCase):
    """The switcher moves two other seats blind. Nobody involved learns a card -
    including the switcher, whose knowledge is a RELATION and must name no card."""

    def setUp(self):
        self.r = night(deck=(SWITCHER, PACK, BYSTANDER, SPOTTER),
                       seats=(SWITCHER, PACK, BYSTANDER), centre=(SPOTTER,),
                       script={Act.SWITCH: ("seats", (1, 2))})

    def test_both_victims_diverge_and_neither_is_told(self):
        self.assertEqual(self.r.diverged(), {1, 2})
        self.assertEqual(self.r.knowledge[1], ())
        self.assertEqual(self.r.knowledge[2], ())

    def test_the_switcher_learns_a_relation_and_NO_card(self):
        labels = [k.label for k in self.r.knowledge[0]]
        self.assertEqual(labels, ["switched", "switched"])
        card_keys = {"pack", "spotter", "swapper", "switcher", "deceived",
                     "bystander"}
        # The tell this guards: labelling the moved seats with what they now hold
        # would read as a richer reveal and would hand the switcher the one thing
        # the rules deny it. Assert on the CARD VOCABULARY, not on the count -
        # a count passes a label like "switched-to-pack".
        for label in labels:
            self.assertFalse(card_keys & set(label.split("-")),
                             f"positional knowledge leaked a card: {label!r}")

    def test_the_switcher_own_card_is_untouched(self):
        self.assertEqual(self.r.truth[0].key, "switcher")
        self.assertEqual(self.r.belief[0].key, "switcher")


class TestDrink(unittest.TestCase):
    """The seat whose entitled knowledge is wrong by construction. `cabal` has no
    such seat and cannot have one."""

    def setUp(self):
        self.r = night(deck=(DECEIVED, BYSTANDER, PACK),
                       seats=(DECEIVED, BYSTANDER), centre=(PACK,),
                       script={Act.DRINK: ("centre", 0)})

    def test_it_believes_deceived_and_holds_the_centre_card(self):
        self.assertEqual(self.r.belief[0].key, "deceived")
        self.assertEqual(self.r.truth[0].key, "pack")
        self.assertIn(0, self.r.diverged())

    def test_it_learns_nothing_at_all(self):
        self.assertEqual(self.r.knowledge[0], ())

    def test_it_can_be_moved_onto_the_losing_side_without_being_told(self):
        """The whole thesis in one assertion: side is read from truth, and the seat
        holding that truth believes something else."""
        self.assertIs(self.r.side_of(0), Side.PACK)
        self.assertIs(self.r.belief[0].side, Side.VILLAGE)

    def test_its_own_card_reaches_the_centre(self):
        self.assertEqual(self.r.centre[0].key, "deceived")


class TestActingIsByDealtCard(unittest.TestCase):
    """You act on the card you were dealt; you win with the card you hold. A seat
    handed `swapper` mid-night must NOT act, and the robber that gave it away must
    still have acted."""

    def test_a_seat_handed_swapper_does_not_act(self):
        r = night(deck=(SWAPPER, BYSTANDER, PACK, SPOTTER),
                  seats=(SWAPPER, BYSTANDER, PACK), centre=(SPOTTER,),
                  script={Act.TAKE: ("seat", 1)})
        self.assertEqual(r.truth[1].key, "swapper")     # seat 1 now holds it
        self.assertEqual(r.knowledge[1], ())            # and never acted
        take_lines = [ln for ln in r.log if ln.startswith("take:")]
        self.assertEqual(len(take_lines), 1, "swapper acted more than once")


class TestPackMeeting(unittest.TestCase):
    def test_two_seated_pack_see_each_other_and_no_one_else(self):
        r = night(deck=(PACK, PACK, BYSTANDER, SPOTTER),
                  seats=(PACK, PACK, BYSTANDER), centre=(SPOTTER,))
        self.assertEqual([(k.seat, k.label) for k in r.knowledge[0]],
                         [(1, "fellow-pack")])
        self.assertEqual([(k.seat, k.label) for k in r.knowledge[1]],
                         [(0, "fellow-pack")])
        self.assertEqual(r.knowledge[2], ())

    def test_a_lone_seated_pack_learns_nothing(self):
        """It cannot tell this from being one of two. That ambiguity is the deal
        constraint's cost and it is deliberate."""
        r = night(deck=(PACK, BYSTANDER, PACK),
                  seats=(PACK, BYSTANDER), centre=(PACK,))
        self.assertEqual(r.knowledge[0], ())


class TestLook(unittest.TestCase):
    def test_looking_at_a_seat_reads_the_card_it_holds_AT_THAT_MOMENT(self):
        """The spotter acts before TAKE and SWITCH, so its reading is true when
        made and can be false by dawn. Nothing tells it which."""
        r = night(deck=(SPOTTER, PACK, SWITCHER, BYSTANDER),
                  seats=(SPOTTER, PACK, SWITCHER), centre=(BYSTANDER,),
                  script={Act.LOOK: ("seat", 1),
                          Act.SWITCH: ("seats", (0, 1))})
        self.assertEqual([(k.seat, k.label) for k in r.knowledge[0]],
                         [(1, "pack")])
        self.assertNotEqual(r.truth[1].key, "pack")     # true when read, not now

    def test_looking_at_the_centre_addresses_slots_not_seats(self):
        r = night(deck=(SPOTTER, PACK, BYSTANDER, DECEIVED),
                  seats=(SPOTTER, PACK), centre=(BYSTANDER, DECEIVED),
                  script={Act.LOOK: ("centre", (0, 1))})
        seen = [(k.seat, k.label) for k in r.knowledge[0]]
        self.assertEqual([s for s, _ in seen], [centre_ref(0), centre_ref(1)])
        self.assertTrue(all(s < 0 for s, _ in seen))


class TestLegalTargets(unittest.TestCase):
    def test_no_action_ever_offers_the_actor_itself(self):
        for act in (Act.LOOK, Act.TAKE, Act.SWITCH):
            for opt in legal_targets(2, act, 5, 3):
                kind, target = opt
                seats = target if isinstance(target, tuple) else (target,)
                if kind in ("seat", "seats"):
                    self.assertNotIn(2, seats, f"{act} offered seat 2 itself")

    def test_switch_offers_unordered_pairs_of_others_only(self):
        opts = legal_targets(0, Act.SWITCH, 4, 3)
        self.assertEqual([t for _, t in opts], [(1, 2), (1, 3), (2, 3)])


class TestDeterminism(unittest.TestCase):
    def test_same_seed_same_night(self):
        from games.changeling.roles import SETUP_5
        a = resolve_night(SETUP_5, random.Random(7))
        b = resolve_night(SETUP_5, random.Random(7))
        self.assertEqual(keys(a.truth), keys(b.truth))
        self.assertEqual(keys(a.belief), keys(b.belief))
        self.assertEqual(a.log, b.log)

    def test_different_seeds_do_not_all_collapse_to_one_night(self):
        """Guards the mutation where the rng is ignored and every game is the same
        deal - which would read as perfect determinism."""
        from games.changeling.roles import SETUP_5
        seen = {tuple(sorted(keys(resolve_night(SETUP_5, random.Random(s)).truth)
                             .items()))
                for s in range(40)}
        self.assertGreater(len(seen), 1)


class TestDivergenceHappensAtAll(unittest.TestCase):
    """A run of ordinary nights must actually produce diverged seats. If it never
    does, the whole rung is `cabal` with fewer phases and every test above is
    passing on scripted nights that the real game never deals."""

    def test_random_nights_produce_divergence_often(self):
        from games.changeling.roles import SETUP_5
        diverged = sum(1 for s in range(200)
                       if resolve_night(SETUP_5, random.Random(s)).diverged())
        self.assertGreater(diverged, 100, f"only {diverged}/200 nights diverged")


if __name__ == "__main__":
    unittest.main()
