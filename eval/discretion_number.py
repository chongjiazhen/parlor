"""Calculate the discretion number for Belfry adjudicator spike.

The discretion number measures how well players can distinguish between
different referee models based solely on their discretionary choices.
"""

from __future__ import annotations

import random
from collections import Counter
from typing import Any

from games.belfry.state import Adjudicator, deal
from games.belfry.roles import FULL


def extract_discretionary_choices(log_entries: list[str]) -> dict[str, Any]:
    """Extract discretionary choices from game log entries.
    
    Returns a dictionary mapping choice type to its value.
    """
    choices = {}
    for entry in log_entries:
        if entry.startswith("discretion: "):
            if "sot and believes it is the" in entry:
                # Format: "discretion: seat {sot} is the sot and believes it is the {role}"
                believes_part = entry.split("believes it is the ")[1]
                sot_belief = believes_part.rstrip(".")
                choices["sot_belief"] = sot_belief
            elif "reads as the demon to the diviner all game" in entry:
                # Format: "discretion: seat {seat} reads as the demon to the diviner all game"
                parts = entry.split("discretion: seat ")
                if len(parts) > 1:
                    seat_part = parts[1]
                    herring_seat = seat_part.split(" ")[0].rstrip(".")
                    choices["herring_registration"] = int(herring_seat)
            elif "the hermit registers" in entry:
                if "as evil, and as the" in entry:
                    choices["hermit_registration"] = ("evil",
                        entry.split("as evil, and as the")[1].split()[0].rstrip(",."))
                elif "as good, as itself" in entry:
                    choices["hermit_registration"] = ("good", "itself")
                elif "as good, and as the" in entry:
                    choices["hermit_registration"] = ("good",
                        entry.split("as good, and as the")[1].split()[0].rstrip(",."))
            elif "the mimic registers" in entry:
                if "as good, and as the" in entry:
                    choices["mimic_registration"] = ("good",
                        entry.split("as good, and as the")[1].split()[0].rstrip(",."))
                elif "as good, as itself" in entry:
                    choices["mimic_registration"] = ("good", "itself")
                elif "as evil, and as the" in entry:
                    choices["mimic_registration"] = ("evil",
                        entry.split("as evil, and as the")[1].split()[0].rstrip(",."))
                elif "as evil, as itself" in entry:
                    choices["mimic_registration"] = ("evil", "itself")
    return choices


def _held_out_source_accuracy(values_a: list[Any], values_b: list[Any]) -> float:
    """Classify held-out choices from empirical arm distributions.

    The score is balanced accuracy: a tie earns half a point, so indistinguishable
    adjudicators score chance (0.5) rather than a value driven by choice entropy.
    """
    train_a, test_a = values_a[::2], values_a[1::2]
    train_b, test_b = values_b[::2], values_b[1::2]
    if not train_a or not test_a or not train_b or not test_b:
        return 0.5

    counts_a, counts_b = Counter(train_a), Counter(train_b)

    def correct(value: Any, source_a: bool) -> float:
        probability_a = counts_a[value] / len(train_a)
        probability_b = counts_b[value] / len(train_b)
        if probability_a == probability_b:
            return 0.5
        predicted_a = probability_a > probability_b
        return float(predicted_a is source_a)

    points = sum(correct(value, True) for value in test_a)
    points += sum(correct(value, False) for value in test_b)
    return points / (len(test_a) + len(test_b))


def calculate_discretion_number(
    adjudicator_a: Adjudicator | None,
    adjudicator_b: Adjudicator | None,
    num_games_per_adjudicator: int = 20,
    script = FULL,
    base_seed: int = 1000
) -> float:
    """Calculate the discretion number between two adjudicators.
    
    The discretion number is the accuracy with which we can distinguish
   
    games run with adjudicator_a vs adjudicator_b based solely on their
    discretionary choice patterns.
    
    Args:
        adjudicator_a: First adjudicator (None for random/default)
        adjudicator_b: Second adjudicator (None for random/default)
        num_games_per_adjudicator: Number of games to run for each adjudicator
        script: The role script to use
        base_seed: Base seed for game generation
        
    Returns:
        Discretion number as a float between 0.0 and 1.0
        (0.5 = chance, 1.0 = perfect discrimination, 0.0 = anti-correlated)
    """
    # Generate games with adjudicator A
    choices_a: list[dict[str, Any]] = []
    for i in range(num_games_per_adjudicator):
        seed = base_seed + i * 2  # Even seeds for adjudicator A
        grim = deal(9, script, random.Random(seed), adjudicator_a)
        choices = extract_discretionary_choices(grim.log)
        choices_a.append(choices)
    
    # Generate games with adjudicator B
    choices_b: list[dict[str, Any]] = []
    for i in range(num_games_per_adjudicator):
        seed = base_seed + i * 2 + 1  # Odd seeds for adjudicator B
        grim = deal(9, script, random.Random(seed), adjudicator_b)
        choices = extract_discretionary_choices(grim.log)
        choices_b.append(choices)
    
    # For each choice type, calculate how well we can distinguish the distributions
    choice_types = ["sot_belief", "herring_registration", "hermit_registration", "mimic_registration"]
    discriminative_scores = []
    
    for choice_type in choice_types:
        # Extract values for this choice type from both adjudicators
        values_a = [c.get(choice_type) for c in choices_a if c.get(choice_type) is not None]
        values_b = [c.get(choice_type) for c in choices_b if c.get(choice_type) is not None]
        
        if not values_a or not values_b:
            # Skip if we don't have data for this choice type
            continue
            
        discriminative_scores.append(_held_out_source_accuracy(values_a, values_b))
    
    # The discretion number is the average discriminative power across choice types
    # If adjudicators are identical, we expect ~0.5 (chance level)
    # If they are completely different, we expect ~1.0
    if discriminative_scores:
        discretion_number = sum(discriminative_scores) / len(discriminative_scores)
        # Ensure it's in the valid range
        return max(0.0, min(1.0, discretion_number))
    else:
        return 0.5  # Default to chance if we can't calculate


def discretion_number_report(
    adjudicator_a_name: str,
    adjudicator_b_name: str,
    discretion_number: float
) -> list[str]:
    """Generate a report lines for the discretion number calculation."""
    lines = [
        "",
        "Adjudicator Comparison - Discretion Number",
        f"  Adjudicator A: {adjudicator_a_name}",
        f"  Adjudicator B: {adjudicator_b_name}",
        f"  Discretion Number: {discretion_number:.3f}",
    ]
    
    # Interpret the discretion number
    if discretion_number > 0.7:
        interpretation = "Strong discrimination - adjudicators produce clearly different choice patterns"
    elif discretion_number > 0.6:
        interpretation = "Moderate discrimination - adjudicators produce somewhat different choice patterns"
    elif discretion_number > 0.4:
        interpretation = "Weak discrimination - adjudicators produce slightly different choice patterns"
    else:
        interpretation = "No discrimination - adjudicators produce indistinguishable choice patterns"
        
    lines.append(f"  Interpretation: {interpretation}")
    
    # Compare to void (random) baseline
    void_baseline = 0.5
    if discretion_number > void_baseline + 0.1:
        lines.append(f"  Adjudicators are distinguishably different (>{void_baseline:.1f} + 0.1)")
    elif discretion_number < void_baseline - 0.1:
        lines.append(f"  Adjudicators are unexpectedly similar (<{void_baseline:.1f} - 0.1)")
    else:
        lines.append(f"  Adjudicator difference is within expected random variation")
        
    return lines


if __name__ == "__main__":
    # Example usage: compare random vs fixed adjudicator
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
    
    # Test 1: Random vs Random (should be ~0.5)
    disc_rand_rand = calculate_discretion_number(None, None, num_games_per_adjudicator=10)
    print(f"Random vs Random: {disc_rand_rand:.3f}")
    
    # Test 2: Fixed vs Random (should be > 0.5)
    fixed_adjudicator = FixedAdjudicator()
    disc_fixed_rand = calculate_discretion_number(fixed_adjudicator, None, num_games_per_adjudicator=10)
    print(f"Fixed vs Random: {disc_fixed_rand:.3f}")
    
    # Test 3: Fixed vs Fixed (should be ~0.5 if same fixed, or variable if different)
    disc_fixed_fixed = calculate_discretion_number(fixed_adjudicator, fixed_adjudicator, num_games_per_adjudicator=10)
    print(f"Fixed vs Fixed (same): {disc_fixed_fixed:.3f}")
    
    # Generate report
    report_lines = discretion_number_report("Fixed Adjudicator", "Random Adjudicator", disc_fixed_rand)
    for line in report_lines:
        print(line)
