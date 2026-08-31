"""Test the discretion number calculation for the adjudicator spike."""

from __future__ import annotations

import random
import unittest

from eval.run_belfry import build_adjudicator, one_game, score
from eval.discretion_number import (calculate_discretion_number,
                                    extract_discretionary_choices)
from games.belfry.referee import BelfryReferee
from games.belfry.roles import FULL, ROLES
from games.belfry.state import Adjudicator, deal


class FixedAdjudicator:
    """An adjudicator that always makes the same discretionary choices."""

    def __init__(self):
        self.call_count = 0

    def sot_belief(self, spare_roles, rng):
        self.call_count += 1
        # Always return the first spare role
        return spare_roles[0] if spare_roles else None

    def herring_registration(self, good_seats, rng):
        self.call_count += 1
        # Always return the first good seat
        return good_seats[0] if good_seats else None

    def hermit_registration(self, evil_roles, rng):
        self.call_count += 1
        # Always return (False, fiend)
        return (False, ROLES["fiend"])

    def mimic_registration(self, good_roles, rng):
        self.call_count += 1
        # Always return (True, witness)
        return (True, ROLES["witness"])


class TestDiscretionaryChoiceExtraction(unittest.TestCase):
    """Test extraction of discretionary choices from game logs."""

    def test_extract_choices_from_sample_log(self):
        """Test that we can extract discretionary choices from sample log entries."""
        log_entries = [
            "discretion: seat 0 is the sot and believes it is the witness",
            "discretion: seat 5 reads as the demon to the diviner all game",
            "discretion: the hermit registers as evil, and as the mimic",
            "discretion: the mimic registers as good, and as the witness"
        ]
        
        choices = extract_discretionary_choices(log_entries)
        
        print(f"Extracted choices: {choices}")
        
        self.assertEqual(choices.get("sot_belief"), "witness")
        self.assertEqual(choices.get("herring_registration"), 5)
        self.assertEqual(choices.get("hermit_registration"), ("evil", "mimic"))
        self.assertEqual(choices.get("mimic_registration"), ("good", "witness"))

    def test_extract_choices_keeps_as_itself_registrations(self):
        choices = extract_discretionary_choices([
            "discretion: the hermit registers as good, as itself",
            "discretion: the mimic registers as evil, as itself",
        ])

        self.assertEqual(choices["hermit_registration"], ("good", "itself"))
        self.assertEqual(choices["mimic_registration"], ("evil", "itself"))


class TestDiscretionNumberCalculation(unittest.TestCase):
    """Test calculation of the discretion number."""

    def test_discretion_number_random_vs_fixed(self):
        """Test that we can distinguish random from fixed adjudicators."""
        class FixedAdjudicator:
            """An adjudicator that always makes the same discretionary choices."""
            def sot_belief(self, spare_roles, rng):
                return spare_roles[0] if spare_roles else None
            def herring_registration(self, good_seats, rng):
                return good_seats[0] if good_seats else None
            def hermit_registration(self, evil_roles, rng):
                return (False, ROLES["fiend"])
            def mimic_registration(self, good_roles, rng):
                return (True, ROLES["witness"])
        
        fixed_adjudicator = FixedAdjudicator()
        
        # Calculate discretion number between fixed and random adjudicators
        discretion_number = calculate_discretion_number(
            fixed_adjudicator, 
            None,  # None = random adjudicator
            num_games_per_adjudicator=20,
            base_seed=1000
        )
        
        # With our test setup, we should be able to distinguish well
        # Fixed adjudicator always makes same choices, random makes different choices
        # So we should be able to distinguish them with high accuracy
        self.assertGreaterEqual(discretion_number, 0.7)
        print(f"Discretion number (fixed vs random): {discretion_number}")
        
        # Also test random vs random (should be lower, but not 0.5 due to sampling variability)
        disc_rand_rand = calculate_discretion_number(
            None, None,
            num_games_per_adjudicator=20,
            base_seed=2000
        )
        print(f"Discretion number (random vs random): {disc_rand_rand}")
        
        # And fixed vs fixed (same adjudicator should be hard to distinguish)
        disc_fixed_fixed = calculate_discretion_number(
            fixed_adjudicator, fixed_adjudicator,
            num_games_per_adjudicator=20,
            base_seed=3000
        )
        print(f"Discretion number (fixed vs fixed): {disc_fixed_fixed}")
        
        # Fixed vs fixed should have lower discretion number than fixed vs random
        self.assertGreater(discretion_number, disc_fixed_fixed)

    def test_same_adjudicator_scores_at_chance(self):
        """Held-out source classification must not distinguish identical arms."""
        score = calculate_discretion_number(
            None, None, num_games_per_adjudicator=200, base_seed=4000)
        self.assertAlmostEqual(score, 0.5, delta=0.1)


if __name__ == '__main__':
    unittest.main()
