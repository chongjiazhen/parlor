"""Play-time discretion: the false neighbour count a switched-off gauge is told.

RULES §Discretion calls per-query discretion a variant axis to measure. This is
the first arm on it, and it is scoped to one sentence - the gauge's count - so
the thing under test is whether the referee can carry a lie across nights, not
whether it can carry a roster. Three guards, each written before the code:

- **Off by default is byte-identical.** A model adjudicator built without
  ``night=True`` consumes the deal RNG exactly as the seeded fallback does and
  sends nothing, so every arm recorded before this file is still that arm.
- **The ask is referee-side.** The prior tellings and the true count reach the
  referee's own model and nothing else: no seat ask, neither public channel.
- **The record carries the tellings for BOTH arms**, so the control's own
  coherence rate reads from the same field the model arm's does - a scorer
  that parsed the control off log prose and the model off events would be two
  instruments wearing one name.
"""

from __future__ import annotations

import json
import random
import unittest

from games.belfry import night as nightinfo
from games.belfry.adjudicator import GAUGE_COHERENCE_RULE, ModelAdjudicator
from games.belfry.player import RandomPolicy, play_game
from games.belfry.referee import BelfryReferee
from games.belfry.roles import COMPACT, FULL, ROLES
from games.belfry.state import Grimoire, Seat


class RecordingBackend:
    def __init__(self, choice: str | None = None):
        self.contexts: list[str] = []
        self.choice = choice

    def complete_meta(self, context: str) -> tuple[str, str]:
        self.contexts.append(context)
        choice = self.choice or json.loads(context)["options"][0]
        return json.dumps({"choice": choice}), "fake-upstream"


def board(keys: list[str], poisoned: tuple[int, ...] = ()) -> Grimoire:
    seats = [Seat(index=i, role=ROLES[k], dealt=ROLES[k], believes=ROLES[k])
             for i, k in enumerate(keys)]
    grim = Grimoire(seats=seats, script=FULL)
    for seat in poisoned:
        grim.seat(seat).poisoned = True
    return grim


POISONED_GAUGE = ["fiend", "gauge", "venom", "warder", "bulwark"]


class TestGaugeCount(unittest.TestCase):
    def test_a_healthy_count_asks_nobody(self):
        grim = board(POISONED_GAUGE)
        calls = []
        count, true, neighbours = nightinfo.gauge_count(
            grim, random.Random(0), 1, 1, choose=lambda o, b: calls.append(1))
        self.assertEqual((count, true), (2, 2))
        self.assertEqual(neighbours, (0, 2))
        self.assertEqual(calls, [])

    def test_a_false_count_is_the_chooser_s_pick_from_the_offered_options(self):
        grim = board(POISONED_GAUGE, poisoned=(1,))
        seen = {}

        def choose(options, board):
            seen["options"], seen["board"] = options, board
            return options[-1]

        count, true, _ = nightinfo.gauge_count(grim, random.Random(0), 1, 1,
                                               choose=choose)
        self.assertEqual(true, 2)
        self.assertEqual(seen["options"], [0, 1])
        self.assertEqual(count, 1)
        self.assertEqual(seen["board"]["true_count"], 2)
        self.assertEqual(seen["board"]["neighbours"], [0, 2])

    def test_without_a_chooser_the_seeded_draw_is_the_old_one(self):
        grim = board(POISONED_GAUGE, poisoned=(1,))
        for seed in range(10):
            old = nightinfo.gauge(grim, random.Random(seed), 1, 1)
            count, _, _ = nightinfo.gauge_count(grim, random.Random(seed), 1, 1)
            self.assertTrue(old.text.startswith(f"{count} "), (old.text, count))


class TestModelAdjudicatorNight(unittest.TestCase):
    def test_off_by_default_draws_from_the_rng_and_sends_nothing(self):
        backend = RecordingBackend()
        adj = ModelAdjudicator(backend, random.Random(1))
        for seed in range(10):
            expected = random.Random(seed).choice([0, 1])
            got = adj.gauge_false_count([0, 1], random.Random(seed),
                                        {"seat": 1})
            self.assertEqual(got, expected)
        self.assertEqual(backend.contexts, [])
        self.assertEqual(adj.events, [])

    def test_night_mode_asks_with_the_rule_and_the_prior_tellings(self):
        backend = RecordingBackend(choice="1")
        adj = ModelAdjudicator(backend, random.Random(1), night=True,
                               ask_seed=7)
        board = {"seat": 1, "night": 2, "neighbours": [0, 2], "true_count": 2,
                 "prior": [{"night": 1, "neighbours": [0, 2], "count": 1,
                            "truthful": False}]}
        got = adj.gauge_false_count([0, 1], random.Random(0), board)
        self.assertEqual(got, 1)
        ask = json.loads(backend.contexts[0])
        self.assertEqual(ask["choice_key"], "gauge_false_count")
        self.assertEqual(sorted(ask["options"]), ["0", "1"])
        self.assertEqual(ask["rule"], GAUGE_COHERENCE_RULE)
        self.assertEqual(ask["board"]["prior"], board["prior"])
        self.assertEqual(adj.events[-1].key, "gauge_false_count")
        self.assertFalse(adj.events[-1].fallback)

    def test_night_mode_needs_an_ask_seed(self):
        with self.assertRaises(ValueError):
            ModelAdjudicator(RecordingBackend(), random.Random(1), night=True)

    def test_an_illegal_reply_falls_back_onto_the_menu(self):
        backend = RecordingBackend(choice="7")
        adj = ModelAdjudicator(backend, random.Random(1), night=True,
                               ask_seed=7, retries=0)
        got = adj.gauge_false_count([0, 1], random.Random(0), {"seat": 1})
        self.assertIn(got, (0, 1))
        self.assertTrue(adj.events[-1].fallback)


def _first_poisoned_gauge_seed(seats: int, model: bool, limit: int = 400):
    """A seed whose game tells a switched-off gauge something. Found by playing,
    because rigging a live referee's poison from outside would test the rig."""
    for seed in range(limit):
        adj = None
        if model:
            adj = ModelAdjudicator(RecordingBackend(), random.Random(seed),
                                   night=True, ask_seed=seed)
        ref = BelfryReferee.new(seats, seed=seed, script=COMPACT,
                                adjudicator=adj)
        rec = play_game(ref, {s: RandomPolicy(rng=random.Random(seed))
                              for s in range(seats)})
        if any(not row["truthful"] for row in rec.gauge_told):
            return seed, rec, adj
    raise AssertionError("no seed produced a false gauge telling")


class TestRefereeIntegration(unittest.TestCase):
    def test_the_control_records_tellings_with_no_adjudicator(self):
        seed, rec, _ = _first_poisoned_gauge_seed(9, model=False)
        rows = rec.gauge_told
        self.assertTrue(rows)
        for row in rows:
            self.assertEqual(set(row), {"seat", "night", "neighbours", "count",
                                        "truthful", "source"})
            self.assertEqual(row["source"], "random")
        self.assertIsNone(rec.adjudicator)

    def test_the_model_arm_records_the_same_field_with_model_provenance(self):
        seed, rec, adj = _first_poisoned_gauge_seed(9, model=True)
        false_rows = [r for r in rec.gauge_told if not r["truthful"]]
        events = [e for e in adj.events if e.key == "gauge_false_count"]
        self.assertEqual(len(false_rows), len(events))
        self.assertTrue(all(r["source"] == "model" for r in false_rows))
        self.assertEqual(rec.adjudicator["calls"], len(adj.events))

    def test_the_ask_reaches_no_seat_and_no_public_channel(self):
        seed, rec, adj = _first_poisoned_gauge_seed(9, model=True)
        ref = BelfryReferee.new(9, seed=seed, script=COMPACT,
                                adjudicator=ModelAdjudicator(
                                    RecordingBackend(), random.Random(seed),
                                    night=True, ask_seed=seed))
        play_game(ref, {s: RandomPolicy(rng=random.Random(seed))
                        for s in range(9)})
        for seat in range(9):
            ctx = ref.render_context(seat)
            self.assertNotIn("true_count", ctx)
            self.assertNotIn("prior", ctx)
            self.assertNotIn(GAUGE_COHERENCE_RULE, ctx)
        public = json.dumps(ref.public_events)
        self.assertNotIn("true_count", public)
        self.assertNotIn(GAUGE_COHERENCE_RULE, public)


if __name__ == "__main__":
    unittest.main()
