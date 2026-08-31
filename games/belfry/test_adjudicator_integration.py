"""Test that Belfry correctly defers discretionary choices to an adjudicator."""

from __future__ import annotations

import json
import random
import unittest

from games.belfry.adjudicator import ModelAdjudicator
from games.belfry.audit import leak_audit
from games.belfry.referee import BelfryReferee
from games.belfry.roles import FULL, ROLES
from games.belfry.state import Adjudicator, deal


class StubAdjudicator:
    """Deterministic adjudicator that always returns fixed choices."""

    def __init__(self):
        self.sot_calls = 0
        self.herring_calls = 0
        self.hermit_calls = 0
        self.mimic_calls = 0

    def sot_belief(self, spare_roles, rng):
        self.sot_calls += 1
        return spare_roles[0]

    def herring_registration(self, good_seats, rng):
        self.herring_calls += 1
        return good_seats[0]

    def hermit_registration(self, evil_roles, rng):
        self.hermit_calls += 1
        return (False, ROLES["fiend"])

    def mimic_registration(self, good_roles, rng):
        self.mimic_calls += 1
        return (True, ROLES["witness"])


class FixedModelBackend:
    def complete_meta(self, context: str) -> tuple[str, str]:
        return json.dumps({"choice": json.loads(context)["options"][0]}), "fixed-model"


def gate_one_inputs(ref: BelfryReferee) -> tuple[tuple[str, ...], tuple[str, ...], str]:
    """The bytes Gate #1 reads at this decision point, before its matching pass."""
    turn = ref.pending()
    assert turn is not None
    return (
        tuple(ref.seat_lines(seat, include_speech=False)
              for seat in range(ref.n)),
        tuple(ref.self_line(seat) for seat in range(ref.n)),
        ref.ask(turn.seat),
    )


class TestAdjudicatorIntegration(unittest.TestCase):
    """Test that deal() correctly uses an adjudicator."""

    def test_deal_without_adjudicator_is_deterministic(self):
        """Without an adjudicator, deal should behave exactly as before."""
        grim1 = deal(5, FULL, random.Random(42))
        grim2 = deal(5, FULL, random.Random(42))
        self.assertEqual(
            [s.believes.key for s in grim1.seats],
            [s.believes.key for s in grim2.seats])
        self.assertEqual(grim1.hermit_evil, grim2.hermit_evil)
        self.assertEqual(grim1.hermit_as, grim2.hermit_as)
        self.assertEqual(grim1.mimic_good, grim2.mimic_good)
        self.assertEqual(grim1.mimic_as, grim2.mimic_as)

    def test_deal_with_adjudicator_calls_present_roles(self):
        """With an adjudicator, only roles present in the deal should be delegated."""
        adjudicator = StubAdjudicator()
        grim = deal(11, FULL, random.Random(42), adjudicator)
        
        # 11-seat script has: gauge, archivist, fiend, venom, speaker, oracle, mimic, witness, duelist, sot, tally
        # No diviner (herring) or hermit in this deal
        self.assertEqual(adjudicator.sot_calls, 1)
        self.assertEqual(adjudicator.herring_calls, 0)  # diviner not in this deal
        self.assertEqual(adjudicator.hermit_calls, 0)   # hermit not in this deal
        self.assertEqual(adjudicator.mimic_calls, 1)

    def test_adjudicator_receives_correct_arguments(self):
        """The adjudicator should receive the correct arguments for each choice."""
        adjudicator = StubAdjudicator()
        grim = deal(11, FULL, random.Random(42), adjudicator)
        
        # Check that the adjudicator's choices were applied
        self.assertEqual(grim.hermit_evil, False)  # default, hermit not present
        self.assertEqual(grim.hermit_as, "")  # default, hermit not present
        self.assertEqual(grim.mimic_good, True)
        self.assertEqual(grim.mimic_as, "witness")

    def test_adjudicator_choices_are_logged(self):
        """Adjudicator choices should be logged in the same format as before."""
        adjudicator = StubAdjudicator()
        grim = deal(11, FULL, random.Random(42), adjudicator)
        
        log_text = "\n".join(grim.log)
        self.assertIn("discretion: seat", log_text)  # sot
        self.assertIn("the mimic registers", log_text)  # mimic
        # Check that herring is NOT in the log since diviner not present
        self.assertNotIn("reads as the demon", log_text)  # herring not present
        # Check that hermit is NOT in the log since hermit not present  
        self.assertNotIn("the hermit registers", log_text)  # hermit not present

    def test_adjudicator_provenance_does_not_change_gate_one_inputs(self):
        adjudicator = ModelAdjudicator(FixedModelBackend(), random.Random(9))
        ref = BelfryReferee.new(11, seed=42, script=FULL,
                                adjudicator=adjudicator)
        self.assertTrue(ref.grim.adjudicator_events)
        before = gate_one_inputs(ref)
        before_audit = leak_audit(ref)

        ref.grim.adjudicator_events.clear()

        self.assertEqual(gate_one_inputs(ref), before)
        self.assertEqual(leak_audit(ref), before_audit)


if __name__ == '__main__':
    unittest.main()
