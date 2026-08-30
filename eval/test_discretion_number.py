"""Test the discretion number calculation for the adjudicator spike."""

from __future__ import annotations

import random
import unittest

from eval.run_belfry import build_adjudicator, one_game, score
from games.belfry.referee import BelfryReferee
from games.belfry.roles import FULL
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
        # Always return (False, "fiend")
        return (False, "fiend")

    def mimic_registration(self, good_roles, rng):
        self.call_count += 1
        # Always return (True, "witness")
        return (True, "witness")


def extract_discretionary_choices(log_entries):
    """Extract discretionary choices from game log entries."""
    choices = {}
    for entry in log_entries:
        if entry.startswith("discretion: "):
            if "sot and believes it is the" in entry:
                # Extract what the sot believes it is
                # Format: "discretion: seat {sot} is the sot and believes it is the {role}"
                believes_part = entry.split("believes it is the ")[1]
                sot_belief = believes_part.rstrip(".")
                choices["sot_belief"] = sot_belief
            elif "reads as the demon to the diviner all game" in entry:
                # Extract which seat reads as the demon
                # Format: "discretion: seat {seat} reads as the demon to the diviner all game"
                parts = entry.split("discretion: seat ")
                if len(parts) > 1:
                    seat_part = parts[1]
                    herring_seat = seat_part.split(" ")[0].rstrip(".")
                    choices["herring_registration"] = int(herring_seat)
            elif "the hermit registers" in entry:
                # Extract hermit registration
                # Format: "discretion: the hermit registers as {evil/good}, and as the {role}"
                if "as evil, and as the" in entry:
                    choices["hermit_registration"] = ("evil", 
                        entry.split("as evil, and as the")[1].split()[0].rstrip(",."))
                elif "as good, and as the" in entry:
                    choices["hermit_registration"] = ("good", 
                        entry.split("as good, and as the")[1].split()[0].rstrip(",."))
            elif "the mimic registers" in entry:
                # Extract mimic registration
                # Format: "discretion: the mimic registers as {good/evil}, and as the {role}"
                if "as good, and as the" in entry:
                    choices["mimic_registration"] = ("good", 
                        entry.split("as good, and as the")[1].split()[0].rstrip(",."))
                elif "as evil, and as the" in entry:
                    choices["mimic_registration"] = ("evil", 
                        entry.split("as evil, and as the")[1].split()[0].rstrip(",."))
    return choices


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


class TestDiscretionNumberCalculation(unittest.TestCase):
    """Test calculation of the discretion number."""

    def test_discretion_number_random_vs_fixed(self):
        """Test that we can distinguish random from fixed adjudicators."""
        from eval.discretion_number import calculate_discretion_number
        
        class FixedAdjudicator:
            """An adjudicator that always makes the same discretionary choices."""
            def sot_belief(self, spare_roles, rng):
                return spare_roles[0] if spare_roles else None
            def herring_registration(self, good_seats, rng):
                return good_seats[0] if good_seats else None
            def hermit_registration(self, evil_roles, rng):
                return (False, "fiend")
            def mimic_registration(self, good_roles, rng):
                return (True, "witness")
        
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


if __name__ == '__main__':
    unittest.main()