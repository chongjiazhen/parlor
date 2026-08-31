"""Tests for the bounded setup-only Belfry model adjudicator."""

from __future__ import annotations

import json
import random
import unittest

from games.belfry.adjudicator import ModelAdjudicator
from games.belfry.player import RandomPolicy, play_game
from games.belfry.referee import BelfryReferee
from games.belfry.roles import FULL, ROLES
from games.belfry.state import deal


class FakeBackend:
    def __init__(self, reply: str):
        self.reply = reply

    def complete_meta(self, _context: str) -> tuple[str, str]:
        return self.reply, "fake-upstream"


class RaisingBackend:
    def complete_meta(self, _context: str) -> tuple[str, str]:
        raise RuntimeError("unavailable")


class FirstOptionBackend:
    def __init__(self):
        self.contexts: list[str] = []

    def complete_meta(self, context: str) -> tuple[str, str]:
        self.contexts.append(context)
        return json.dumps({"choice": json.loads(context)["options"][0]}), "fake-upstream"


class PromptCapturingRandomPolicy(RandomPolicy):
    """Legal noise that records the exact player payload before answering it."""

    def __init__(self, rng: random.Random):
        super().__init__(rng)
        self.payloads: list[str] = []

    def act(self, ref: BelfryReferee, seat: int) -> dict:
        self.payloads.append(ref.prompt_for(seat))
        return super().act(ref, seat)


def referee_with_fixed_model_adjudicator() -> BelfryReferee:
    """A deal whose legal setup choices come from a deterministic fake model."""
    return BelfryReferee.new(
        11,
        seed=42,
        script=FULL,
        adjudicator=ModelAdjudicator(FirstOptionBackend(), random.Random(9)),
    )


class TestModelAdjudicator(unittest.TestCase):
    def test_illegal_choice_uses_seeded_menu_fallback(self):
        adj = ModelAdjudicator(
            FakeBackend('{"choice":"not-offered"}'), random.Random(9))

        self.assertIs(
            adj.sot_belief([ROLES["witness"], ROLES["gauge"]], random.Random(4)),
            ROLES["gauge"])
        self.assertIs(adj.events[0].fallback, True)

    def test_fenced_json_choice_is_accepted(self):
        adj = ModelAdjudicator(
            FakeBackend('```json\n{"choice":"witness"}\n```'), random.Random(9))

        self.assertIs(
            adj.sot_belief([ROLES["witness"], ROLES["gauge"]], random.Random(4)),
            ROLES["witness"])
        self.assertFalse(adj.events[0].fallback)
        self.assertEqual(adj.events[0].upstream, "fake-upstream")

    def test_invalid_responses_fall_back_without_provenance(self):
        invalid_backends = [
            FakeBackend("not json"),
            FakeBackend('{"choice":"witness","extra":true}'),
            FakeBackend('{"choice":1}'),
            RaisingBackend(),
        ]
        roles = [ROLES["witness"], ROLES["gauge"]]

        for backend in invalid_backends:
            with self.subTest(backend=type(backend).__name__):
                adj = ModelAdjudicator(backend, random.Random(9))
                self.assertIs(adj.sot_belief(roles, random.Random(4)), ROLES["gauge"])
                event = adj.events[0]
                self.assertTrue(event.fallback)
                self.assertIsNone(event.upstream)

    def test_valid_choice_sends_only_choice_key_and_legal_menu(self):
        backend = FirstOptionBackend()
        adj = ModelAdjudicator(backend, random.Random(9))

        self.assertIs(adj.sot_belief([ROLES["witness"]], random.Random(4)),
                      ROLES["witness"])
        event = adj.events[0]
        self.assertEqual(event.key, "sot_belief")
        self.assertEqual(event.options, ("witness",))
        self.assertFalse(event.fallback)
        self.assertFalse(event.recovered)
        self.assertEqual(event.upstream, "fake-upstream")
        self.assertEqual(backend.contexts, [
            '{"choice_key": "sot_belief", "options": ["witness"]}'])

    def test_all_setup_choices_translate_menu_values_to_domain_values(self):
        adj = ModelAdjudicator(FirstOptionBackend(), random.Random(9))

        self.assertEqual(adj.herring_registration([3, 5], random.Random(4)), 3)
        self.assertEqual(adj.hermit_registration([ROLES["fiend"]], random.Random(4)),
                         (True, ROLES["fiend"]))
        self.assertEqual(adj.mimic_registration([ROLES["witness"]], random.Random(4)),
                         (True, ROLES["witness"]))

    def test_deal_keeps_model_choice_events_referee_side(self):
        adjudicator = ModelAdjudicator(FirstOptionBackend(), random.Random(9))

        grim = deal(11, FULL, random.Random(42), adjudicator)

        self.assertEqual(grim.adjudicator_events, adjudicator.events)
        self.assertEqual([event.upstream for event in grim.adjudicator_events],
                         ["fake-upstream", "fake-upstream"])
        self.assertNotIn("fake-upstream", "\n".join(grim.log))

    def test_model_choice_provenance_never_reaches_player_prompt(self):
        ref = referee_with_fixed_model_adjudicator()
        policy = PromptCapturingRandomPolicy(random.Random(11))

        rec = play_game(ref, {seat: policy for seat in range(ref.n)})

        self.assertIsNone(rec.error)
        self.assertTrue(policy.payloads)
        self.assertTrue(ref.grim.adjudicator_events)
        self.assertTrue(all("adjudicator" not in payload.lower()
                            for payload in policy.payloads))
        self.assertTrue(all("fake-upstream" not in payload
                            for payload in policy.payloads))


if __name__ == "__main__":
    unittest.main()
