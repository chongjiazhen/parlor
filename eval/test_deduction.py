"""The instrument control comes first, exactly as `s5_verdict` does it.

`deduction.py` re-derives the referee's execution rule so it can ask what WOULD
have happened under a different vote. A re-derivation that has drifted from the
referee produces a number that is wrong in a way no reader could see, so the first
test replays every recorded game through it and demands the recorded winner back.
Everything else here is worth nothing until that passes.
"""
from __future__ import annotations

import functools
import unittest

from eval import records_gate
from eval.deduction import PACK, min_flips, per_game, winner_from
from eval.s5_verdict import S2, load, winnable


@functools.cache
def recorded() -> list[dict]:
    """S2's games, or a skip where S2 was never run. Read lazily: at module level
    this raised at COLLECTION in any tree without the records, which took the six
    synthetic cases below out of the suite along with the two controls that
    actually need a run (`eval/records_gate.py`)."""
    records_gate.demand(S2, f"{S2}.jsonl")
    return load(S2)[1]


class TestTheRuleMatchesTheReferee(unittest.TestCase):
    def test_every_recorded_game_replays_to_its_recorded_winner(self):
        """The control. If this fails, no figure in `deduction.py` means anything -
        the rule it counts with is not the rule the games were played under."""
        played = [g for g in recorded() if g.get("winner") and g.get("votes")]
        self.assertGreater(len(played), 100, "the control needs the S5 records")
        for game in played:
            votes = {v["seat"]: v["target"] for v in game["votes"]}
            if len(votes) != len(game["truth"]):
                continue
            with self.subTest(game=game.get("game")):
                self.assertEqual(winner_from(votes, game["truth"]), game["winner"])

    def test_a_tie_accuses_everyone_tied_so_one_wolf_in_it_wins_the_village(self):
        truth = {"0": PACK, "1": "spotter", "2": "switcher"}
        # A plurality of two on seat 1, who is no wolf: the wolf walks.
        self.assertEqual(winner_from({0: 1, 1: 2, 2: 1}, truth), "pack")
        # Three seats, three different targets: everyone is tied and therefore
        # accused, the wolf among them, and the village takes it on the tie rule
        # alone. This is the branch a plurality-only reading would get wrong.
        self.assertEqual(winner_from({0: 1, 1: 2, 2: 0}, truth), "village")


class TestDecisiveness(unittest.TestCase):
    def test_a_one_vote_margin_is_found(self):
        truth = {"0": PACK, "1": "spotter", "2": "switcher", "3": "swapper"}
        # 0 takes two votes and is executed; move either one and the wolf walks.
        self.assertEqual(min_flips({"truth": truth, "votes": [
            {"seat": 0, "target": 1}, {"seat": 1, "target": 0},
            {"seat": 2, "target": 0}, {"seat": 3, "target": 1}]}), 1)

    def test_a_three_vote_plurality_survives_one_change_and_not_two(self):
        truth = {"0": PACK, "1": "spotter", "2": "switcher", "3": "swapper"}
        votes = [{"seat": s, "target": 0} for s in (1, 2, 3)] + \
                [{"seat": 0, "target": 1}]
        # Written first as "unanimous cannot be undone", which was wrong: move two
        # of the three off the wolf and onto one other seat and it hands over. The
        # instrument was right and the fixture was not.
        self.assertEqual(min_flips({"truth": truth, "votes": votes}), 2)

    def test_some_recorded_games_had_more_slack_than_the_cap(self):
        """``None`` is a real outcome on real games, not a shape that never occurs -
        without this the cap could be wrong in the safe-looking direction."""
        self.assertTrue(
            any(per_game(g)["min_flips"] is None for g in winnable(recorded())))

    def test_an_incomplete_vote_map_is_not_scored_as_decisive(self):
        truth = {"0": PACK, "1": "spotter", "2": "switcher"}
        self.assertIsNone(min_flips({"truth": truth,
                                     "votes": [{"seat": 0, "target": 1}]}))


class TestPerGame(unittest.TestCase):
    def test_chance_is_the_games_own_and_doubles_with_a_second_wolf(self):
        one = {"truth": {"0": PACK, "1": "spotter", "2": "switcher", "3": "swapper",
                         "4": "deceived"},
               "winner": "pack", "votes": [
                   {"seat": 1, "target": 2, "voter_holds_pack": False,
                    "target_holds_pack": False}]}
        two = dict(one, truth=dict(one["truth"], **{"2": PACK}))
        self.assertAlmostEqual(per_game(one)["chance"], 1 / 4)
        self.assertAlmostEqual(per_game(two)["chance"], 2 / 4)

    def test_lift_is_zero_for_a_table_voting_at_chance(self):
        game = {"truth": {"0": PACK, "1": "spotter", "2": "switcher", "3": "swapper",
                          "4": "deceived"},
                "winner": "pack",
                "votes": [{"seat": s, "target": 0, "voter_holds_pack": False,
                           "target_holds_pack": (s == 1)} for s in (1, 2, 3, 4)]}
        # One hit in four villager votes, against a one-wolf chance of exactly 1/4.
        self.assertAlmostEqual(per_game(game)["accuracy"], 0.25)
        self.assertAlmostEqual(per_game(game)["lift"], 0.0)

    def test_a_wolfs_own_vote_is_not_counted_as_a_villagers(self):
        game = {"truth": {"0": PACK, "1": "spotter", "2": "switcher"},
                "winner": "pack",
                "votes": [{"seat": 0, "target": 1, "voter_holds_pack": True,
                           "target_holds_pack": False},
                          {"seat": 1, "target": 0, "voter_holds_pack": False,
                           "target_holds_pack": True}]}
        self.assertEqual(per_game(game)["villager_votes"], 1)
        self.assertEqual(per_game(game)["accuracy"], 1.0)


if __name__ == "__main__":
    unittest.main()
