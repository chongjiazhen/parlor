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
                self.assertEqual(
                    winner_from(votes, game["truth"],
                                game.get("vote_rule", "plurality")),
                    game["winner"])

    def test_a_tie_accuses_everyone_tied_so_one_wolf_in_it_wins_the_village(self):
        truth = {"0": PACK, "1": "spotter", "2": "switcher"}
        # A plurality of two on seat 1, who is no wolf: the wolf walks.
        self.assertEqual(winner_from({0: 1, 1: 2, 2: 1}, truth), "pack")
        # Three seats, three different targets: everyone is tied and therefore
        # accused, the wolf among them, and the village takes it on the tie rule
        # alone. This is the branch a plurality-only reading would get wrong.
        self.assertEqual(winner_from({0: 1, 1: 2, 2: 0}, truth), "village")

    def test_under_the_min2_rule_a_flat_tally_accuses_nobody(self):
        """The referee since 2026-09-02. A record naming ``plurality-min2`` is
        replayed under it: one finger each kills nobody, so the pack wins while a
        wolf is seated and the village wins when none is."""
        truth = {"0": PACK, "1": "spotter", "2": "switcher"}
        self.assertEqual(winner_from({0: 1, 1: 2, 2: 0}, truth, "plurality-min2"),
                         "pack")
        no_wolf = {"0": "bystander", "1": "spotter", "2": "switcher"}
        self.assertEqual(winner_from({0: 1, 1: 2, 2: 0}, no_wolf, "plurality-min2"),
                         "village")
        # a real plurality is unchanged by the rule
        self.assertEqual(winner_from({0: 1, 1: 0, 2: 0}, truth, "plurality-min2"),
                         "village")


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


# ---- the chance bar is the TABLE's, not a constant -------------------------

def _game(truth: dict, votes_none: int = 0) -> dict:
    """One record row: dawn holdings per seat, plus blind villager votes."""
    return {"truth": {str(s): k for s, k in truth.items()},
            "votes": [{"seat": 0, "target": 1, "voter_holds_pack": False,
                       "target_holds_pack": False, "knowledge_class": "none",
                       "voter_believes_pack": False, "voter_diverged": False}
                      for _ in range(votes_none)]}


def test_seats_are_read_off_the_record_not_assumed():
    from eval.s5_verdict import seats_in
    assert seats_in(_game({0: "pack", 1: "bystander"})) == 2
    assert seats_in(_game({i: "bystander" for i in range(6)})) == 6
    # a row predating the field is a five-seat record, never a guess
    assert seats_in({}) == 5


def test_the_chance_bar_moves_with_the_TABLE():
    """Hardcoded 5 and 4 returned SETUP_5's bar for a six-seat record - a
    plausible number, several points off, with nothing raising. One wolf among
    five seats is 1/4 to a random villager; among six it is 1/5."""
    from eval.s5_verdict import derived_chance
    five = _game({0: "pack", 1: "b", 2: "b", 3: "b", 4: "b"})
    six = _game({0: "pack", 1: "b", 2: "b", 3: "b", 4: "b", 5: "b"})
    assert abs(derived_chance([five]) - 0.25) < 1e-9
    assert abs(derived_chance([six]) - 0.20) < 1e-9


def test_the_blind_bar_moves_with_the_table_too():
    """Same defect, same fix, the other function - and it is the one cut on the
    stratum the gate is actually read from."""
    from eval.s5_verdict import blind_chance
    five = _game({0: "pack", 1: "b", 2: "b", 3: "b", 4: "b"}, votes_none=3)
    six = _game({0: "pack", 1: "b", 2: "b", 3: "b", 4: "b", 5: "b"}, votes_none=3)
    assert abs(blind_chance([five]) - 0.25) < 1e-9
    assert abs(blind_chance([six]) - 0.20) < 1e-9


def test_s2_is_a_five_seat_record_so_its_published_bar_cannot_move():
    """The generalisation must be a no-op on every record that exists. S5's read
    is published; widening arithmetic whose numbers are published is a
    re-baseline unless the numbers are shown not to move."""
    from eval.s5_verdict import S2, load, seats_in
    _, games = load(S2)
    assert games, "S2 record missing - this test guards a published number"
    assert {seats_in(g) for g in games} == {5}
