"""The changeling decision audit reads the referee's night log, so each check is
pinned against a hand-built log where the answer is known - and against the
variant that would fool a matcher written from one deal in hand: a swapper whose
victim was a wolf (the reveal shows PACK, so the vote is not dominated), a pack
seat told nobody (no partner to vote), and a log line the parser does not know.
"""

from __future__ import annotations

import unittest

from eval.changeling_audit import (control, partner_votes, reveals,
                                   shown_village_votes)


def game(log, votes, truth, seats=5):
    return {"log": log, "votes": votes, "truth": truth,
            "dealt": dict(truth), "accused": [], "winner": "pack"}


def vote(seat, target, target_holds_pack=False):
    return {"seat": seat, "target": target,
            "target_holds_pack": target_holds_pack}


TRUTH = {"0": "spotter", "1": "pack", "2": "bystander", "3": "swapper",
         "4": "pack"}


class TestReveals(unittest.TestCase):
    def test_look_meet_and_take_are_read_and_the_rest_is_ignored(self):
        log = ["deal: seat 0=spotter, seat 1=pack | centre=bystander",
               "meet: seat 1 (pack) sees [4]",
               "meet: seat 4 (pack) sees [1]",
               "look: seat 0 sees seat 2 = bystander",
               "take: seat 3 robs seat 1, now holds pack; seat 1 holds swapper "
               "and is not told",
               "switch: seat 9 exchanges seats 1 and 4, blind; neither is told",
               "wake: seat 5 looks and sees pack",
               "drink: seat 2 swaps with centre slot 1, blind; now holds x and "
               "believes deceived"]
        r = reveals(game(log, [], TRUTH))
        self.assertEqual(r[1], [(4, "fellow-pack")])
        self.assertEqual(r[0], [(2, "bystander")])
        # the robber learns its own new card AND what the victim now holds
        self.assertEqual(r[3], [(3, "pack"), (1, "swapper")])
        self.assertNotIn(9, r)
        self.assertNotIn(5, r)

    def test_a_centre_look_reveals_no_seat(self):
        log = ["look: seat 0 sees centre slots (0, 2) = ['bystander', 'pack']"]
        self.assertEqual(reveals(game(log, [], TRUTH)), {})

    def test_meet_with_nobody_is_an_empty_reveal(self):
        log = ["meet: seat 1 (pack) sees no one"]
        self.assertEqual(reveals(game(log, [], TRUTH)).get(1, []), [])


class TestShownVillageVotes(unittest.TestCase):
    def test_a_spotter_voting_the_seat_it_saw_as_village_is_counted(self):
        g = game(["look: seat 0 sees seat 2 = bystander"],
                 [vote(0, 2), vote(1, 0), vote(2, 3)], TRUTH)
        hits, total, priced, _ = shown_village_votes([g])
        self.assertEqual((hits, total, priced), (1, 1, 0))

    def test_a_spotter_voting_elsewhere_is_in_the_denominator_only(self):
        g = game(["look: seat 0 sees seat 2 = bystander"], [vote(0, 4)], TRUTH)
        self.assertEqual(shown_village_votes([g])[:2], (0, 1))

    def test_a_reveal_of_pack_does_not_make_the_vote_dominated(self):
        g = game(["look: seat 0 sees seat 1 = pack"], [vote(0, 1)], TRUTH)
        self.assertEqual(shown_village_votes([g])[:2], (0, 0))

    def test_the_swapper_voting_its_victim_is_counted_and_priced(self):
        # victim now holds the swapper card - village - so the vote is dominated
        # given what the seat knew; but the switcher moved a wolf onto it after,
        # which is the PRICE column, not a defence
        g = game(["take: seat 3 robs seat 1, now holds pack; seat 1 holds "
                  "swapper and is not told"],
                 [vote(3, 1, target_holds_pack=True)], TRUTH)
        hits, total, priced, _ = shown_village_votes([g])
        self.assertEqual((hits, total, priced), (1, 1, 1))

    def test_a_swapper_that_robbed_a_wolf_is_not_dominated_on_its_own_seat(self):
        # it holds pack now; its own-seat reveal is pack and no seat was shown
        # village, so nothing here is dominated
        g = game(["take: seat 3 robs seat 1, now holds pack; seat 1 holds "
                  "swapper and is not told"], [vote(3, 0)], TRUTH)
        self.assertEqual(shown_village_votes([g])[:2], (0, 1))

    def test_a_kindred_fellow_is_a_shown_village_seat(self):
        g = game(["meet: seat 0 (kindred) sees [2]"], [vote(0, 2)], TRUTH)
        self.assertEqual(shown_village_votes([g])[:2], (1, 1))


class TestPartnerVotes(unittest.TestCase):
    def test_a_pack_seat_voting_its_told_partner_is_counted(self):
        g = game(["meet: seat 1 (pack) sees [4]", "meet: seat 4 (pack) sees [1]"],
                 [vote(1, 4, target_holds_pack=True), vote(4, 0)], TRUTH)
        hits, total, priced, _ = partner_votes([g])
        self.assertEqual((hits, total, priced), (1, 2, 1))

    def test_a_lone_wolf_has_no_partner_and_is_not_in_the_denominator(self):
        g = game(["meet: seat 1 (pack) sees no one"], [vote(1, 4)], TRUTH)
        self.assertEqual(partner_votes([g])[:2], (0, 0))

    def test_kindred_meeting_is_not_a_pack_partner(self):
        g = game(["meet: seat 0 (kindred) sees [2]"], [vote(0, 2)], TRUTH)
        self.assertEqual(partner_votes([g])[:2], (0, 0))


class TestControl(unittest.TestCase):
    def test_refuses_when_neither_check_has_a_denominator(self):
        g = game(["switch: seat 0 exchanges seats 1 and 4, blind; neither is told"],
                 [vote(0, 1)], TRUTH)
        self.assertEqual(control([g]), 3)

    def test_passes_when_both_checks_fired(self):
        g = game(["look: seat 0 sees seat 2 = bystander",
                  "meet: seat 1 (pack) sees [4]"],
                 [vote(0, 2), vote(1, 4)], TRUTH)
        self.assertEqual(control([g]), 0)


if __name__ == "__main__":
    unittest.main()
