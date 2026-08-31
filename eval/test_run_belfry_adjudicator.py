"""Test that run_belfry correctly handles adjudicator arguments."""

from __future__ import annotations

import argparse
import unittest
from unittest import mock

from eval.run_belfry import build_adjudicator, main
from games.belfry.adjudicator import ModelAdjudicator


def make_args(**over) -> argparse.Namespace:
    base = dict(adjudicator="model", adjudicator_backend="local",
                adjudicator_model="judge-model", model="player-model",
                temperature=0.85, register="character", timeout=120.0,
                max_tokens=1536, no_thinking=False)
    base.update(over)
    return argparse.Namespace(**base)


class TestRunBelfryAdjudicator(unittest.TestCase):
    """Test adjudicator argument handling in run_belfry."""

    def test_adjudicator_argument_exists(self):
        """Test that --adjudicator argument is available."""
        with mock.patch("sys.argv", ["run_belfry.py", "--games", "0",
                                      "--adjudicator", "random"]), \
             mock.patch("builtins.print"):
            main()

    def test_adjudicator_choices(self):
        """Test that valid adjudicator choices are accepted."""
        for choice, extra in (("random", []),
                              ("model", ["--adjudicator-backend", "local",
                                         "--adjudicator-model", "judge-model"])):
            with self.subTest(choice=choice):
                with mock.patch("sys.argv", ["run_belfry.py", "--games", "0",
                                              "--adjudicator", choice, *extra]), \
                     mock.patch("builtins.print"):
                    main()

    def test_random_default_uses_deal_rng(self):
        args = argparse.Namespace(adjudicator="random")
        self.assertIsNone(build_adjudicator(args, 1000))

    def test_model_adjudicator_uses_game_seed_not_run_seed(self):
        """Changing the game index must change the adjudicator sampler too."""
        args = make_args()
        first = build_adjudicator(args, 6100)
        second = build_adjudicator(args, 6101)
        self.assertIsInstance(first, ModelAdjudicator)
        self.assertEqual(first.backend.seed, 6100)
        self.assertEqual(second.backend.seed, 6101)

    def test_model_adjudicator_has_its_own_hard_temperature(self):
        """Player exploration must not make setup discretion nondeterministic."""
        adjudicator = build_adjudicator(make_args(temperature=0.85), 6100)
        self.assertEqual(adjudicator.backend.temperature, 0.0)
        self.assertEqual(adjudicator.backend.model, "judge-model")


if __name__ == '__main__':
    unittest.main()
