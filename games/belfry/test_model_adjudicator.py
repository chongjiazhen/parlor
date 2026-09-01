"""Tests for the bounded setup-only Belfry model adjudicator."""

from __future__ import annotations

import json
import random
import unittest

from eval.belfry_steering_verdict import offered_order
from games.belfry.adjudicator import (HERRING_STEER_RULE, ModelAdjudicator,
                                      preferred_herring)
from games.belfry.player import RandomPolicy, play_game
from games.belfry.referee import BelfryReferee
from games.belfry.roles import COMPACT, FULL, ROLES, Team
from games.belfry.state import deal


class FakeBackend:
    def __init__(self, reply: str):
        self.reply = reply

    def complete_meta(self, _context: str) -> tuple[str, str]:
        return self.reply, "fake-upstream"


class RecordingBackend:
    """Keeps every ask, so a test can read the bytes that went out. Answers with
    the first option it was offered unless told which to take, so a test about
    the ask never trips the refusal loop it is not testing."""

    def __init__(self, choice: str | None = None):
        self.choice, self.contexts = choice, []

    def complete_meta(self, context: str) -> tuple[str, str]:
        self.contexts.append(context)
        choice = self.choice or json.loads(context)["options"][0]
        return json.dumps({"choice": choice}), "fake-upstream"


class RaisingBackend:
    def complete_meta(self, _context: str) -> tuple[str, str]:
        raise RuntimeError("unavailable")


class RefusingThenAnsweringBackend:
    """Malformed for the first ``refusals`` asks, then a legal choice.

    The shape a recovered call has to have: the model, not the seeded menu, picks
    the option, and it took the referee sending the reply back to get there.
    """

    def __init__(self, refusals: int, choice: str, bad: str = "not json"):
        self.refusals, self.choice, self.bad = refusals, choice, bad
        self.contexts: list[str] = []

    def complete_meta(self, context: str) -> tuple[str, str]:
        self.contexts.append(context)
        if len(self.contexts) <= self.refusals:
            return self.bad, "fake-upstream"
        return json.dumps({"choice": self.choice}), "fake-upstream"


class RaisingThenAnsweringBackend:
    """Transport dies once, then answers. Recovery is a RULES word, so this call
    is clean - counting it recovered would inflate the rate with the network."""

    def __init__(self, choice: str):
        self.choice, self.calls = choice, 0

    def complete_meta(self, _context: str) -> tuple[str, str]:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("unavailable")
        return json.dumps({"choice": self.choice}), "fake-upstream"


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
                adj = ModelAdjudicator(backend, random.Random(9), backoff=0.0)
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

    def test_a_sent_back_reply_is_re_asked_and_counted_recovered(self):
        """The reason S29 exists. Every published ``recovered`` count was a
        structural zero, because the flag was a literal and one bad reply spent
        the choice."""
        backend = RefusingThenAnsweringBackend(1, "witness")
        adj = ModelAdjudicator(backend, random.Random(9), backoff=0.0)

        self.assertIs(
            adj.sot_belief([ROLES["witness"], ROLES["gauge"]], random.Random(4)),
            ROLES["witness"])
        event = adj.events[0]
        self.assertTrue(event.recovered)
        self.assertFalse(event.fallback)
        self.assertEqual(event.selected, "witness")
        self.assertEqual(event.upstream, "fake-upstream")

    def test_the_re_ask_carries_the_complaint_and_leaves_the_first_ask_alone(self):
        """The opening call stays the question S8b measured; only the re-ask is
        new, and it says what was wrong or the model has no reason to differ."""
        backend = RefusingThenAnsweringBackend(1, "witness")
        adj = ModelAdjudicator(backend, random.Random(9), backoff=0.0)

        adj.sot_belief([ROLES["witness"], ROLES["gauge"]], random.Random(4))

        self.assertEqual(
            backend.contexts[0],
            '{"choice_key": "sot_belief", "options": ["witness", "gauge"]}')
        self.assertEqual(json.loads(backend.contexts[1])["choice_key"],
                         "sot_belief")
        self.assertIn("refused", json.loads(backend.contexts[1]))

    def test_a_clean_first_reply_is_not_recovered(self):
        adj = ModelAdjudicator(FirstOptionBackend(), random.Random(9), backoff=0.0)

        adj.sot_belief([ROLES["witness"]], random.Random(4))

        self.assertFalse(adj.events[0].recovered)

    def test_the_retry_budget_is_bounded_and_the_fallback_is_not_recovered(self):
        """Three attempts, then the seeded menu. A fallback that also read
        recovered would let one call be counted in two partitions."""
        backend = RefusingThenAnsweringBackend(99, "witness")
        adj = ModelAdjudicator(backend, random.Random(9), backoff=0.0)

        self.assertIs(
            adj.sot_belief([ROLES["witness"], ROLES["gauge"]], random.Random(4)),
            ROLES["gauge"])
        self.assertEqual(len(backend.contexts), 3)
        event = adj.events[0]
        self.assertTrue(event.fallback)
        self.assertFalse(event.recovered)
        self.assertIsNone(event.upstream)

    def test_a_transport_failure_that_later_answers_is_clean_not_recovered(self):
        """Recovery is the model being sent back by the rules. A 500 is the
        network, and counting it would put the endpoint's health into a figure
        that is supposed to read the model's discretion."""
        backend = RaisingThenAnsweringBackend("witness")
        adj = ModelAdjudicator(backend, random.Random(9), backoff=0.0)

        self.assertIs(
            adj.sot_belief([ROLES["witness"], ROLES["gauge"]], random.Random(4)),
            ROLES["witness"])
        self.assertEqual(backend.calls, 2)
        self.assertFalse(adj.events[0].recovered)
        self.assertFalse(adj.events[0].fallback)


class TestSteeredAsk(unittest.TestCase):
    """The S23 arm's ask, bound by docs/belfry-discretion-quality-criterion.md."""

    def test_the_blind_ask_is_unchanged_by_the_steering_field(self):
        """Every arm before S23 must still send the bytes S8b measured: no board,
        no rule, and the menu in the order the referee built it."""
        backend = RecordingBackend("2")
        adj = ModelAdjudicator(backend, random.Random(9), backoff=0.0)

        adj.herring_registration([0, 2, 4], random.Random(4),
                                 {"seats": 5, "demon_seat": 1})

        self.assertEqual(
            json.loads(backend.contexts[0]),
            {"choice_key": "herring_registration", "options": ["0", "2", "4"]})

    def test_a_steered_ask_carries_the_board_and_the_rule(self):
        backend = RecordingBackend("2")
        adj = ModelAdjudicator(backend, random.Random(9), backoff=0.0,
                               steer=HERRING_STEER_RULE, ask_seed=6100)

        adj.herring_registration([0, 2, 4], random.Random(4),
                                 {"seats": 5, "demon_seat": 1})

        ask = json.loads(backend.contexts[0])
        self.assertEqual(ask["board"], {"seats": 5, "demon_seat": 1})
        self.assertEqual(ask["rule"], HERRING_STEER_RULE)
        self.assertEqual(sorted(ask["options"]), ["0", "2", "4"])

    def test_the_steered_menu_is_offered_in_the_scorer_s_seeded_order(self):
        """The order is the whole defence against a position prior scoring
        against a rule it never read, so the scorer rebuilds it from the seed."""
        backend = RecordingBackend("2")
        adj = ModelAdjudicator(backend, random.Random(9), backoff=0.0,
                               steer=HERRING_STEER_RULE, ask_seed=6100)

        adj.herring_registration([0, 2, 4], random.Random(4), {})

        offered = json.loads(backend.contexts[0])["options"]
        self.assertEqual(tuple(offered), offered_order(6100, ["0", "2", "4"]))
        self.assertEqual(adj.events[0].options, tuple(offered))

    def test_steering_without_an_ask_seed_refuses_to_be_built(self):
        with self.assertRaises(ValueError):
            ModelAdjudicator(FakeBackend("{}"), random.Random(9),
                             steer=HERRING_STEER_RULE)

    def test_the_board_reaches_the_referee_s_own_call_and_nothing_else(self):
        """Gate #1 in the one place it cannot see: the demon's seat is a true
        association, and it is legal here only because this payload goes to the
        referee's own model and to neither public channel nor any seat ask."""
        backend = RecordingBackend()
        adj = ModelAdjudicator(backend, random.Random(9), backoff=0.0,
                               steer=HERRING_STEER_RULE, ask_seed=6102)
        grim = deal(5, COMPACT, random.Random(6102), adj)

        self.assertEqual(len(backend.contexts), 1)
        self.assertIn("demon_seat", backend.contexts[0])
        demon = next(s.index for s in grim.seats if s.role.team is Team.DEMON)
        self.assertEqual(
            json.loads(backend.contexts[0])["board"],
            {"seats": 5, "demon_seat": demon})
        for line in grim.log:
            self.assertNotIn("demon_seat", line)


class TestPreferredHerring(unittest.TestCase):
    def test_the_nearest_good_seat_is_the_shorter_way_round_the_circle(self):
        self.assertEqual(preferred_herring(5, 0, [2, 3, 4]), 4)

    def test_an_equal_distance_takes_the_lower_seat_number(self):
        self.assertEqual(preferred_herring(5, 0, [1, 2, 4]), 1)


if __name__ == "__main__":
    unittest.main()
