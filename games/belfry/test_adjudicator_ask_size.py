"""What the referee's own asks cost, priced the way a seat's are.

`core.callcost` prices every PLAYER call; the adjudicator is the one model caller
in the tree that carried no such number, so a transcript-class arm - whose whole
variable is how much session it puts in front of the model - could not price its
own ask from the record. `ChoiceEvent.ask_size` is that number, and these are the
four cases it has to get right: a plain ask, a retried one, a recalled one, and a
call no model answered.
"""

from __future__ import annotations

import json
import random
import unittest
from dataclasses import asdict

from games.belfry.adjudicator import ChoiceEvent, ModelAdjudicator
from games.belfry.roles import ROLES


class RecordingBackend:
    """Answers with the first option offered, keeping every ask that went out."""

    def __init__(self, choice: str | None = None):
        self.choice, self.contexts, self.replies = choice, [], []

    def complete_meta(self, context: str, history=None) -> tuple[str, str]:
        del history
        self.contexts.append(context)
        choice = self.choice or json.loads(context)["options"][0]
        self.replies.append(json.dumps({"choice": choice}))
        return self.replies[-1], "fake-upstream"


class TranscriptBackend(RecordingBackend):
    """Keeps the session history each ask arrived with, so a test can add up the
    bytes the recall actually sent rather than trusting the field's own sum."""

    def __init__(self, choice: str | None = None):
        super().__init__(choice)
        self.histories: list[list | None] = []

    def complete_meta(self, context: str, history=None) -> tuple[str, str]:
        self.histories.append(None if history is None else list(history))
        return super().complete_meta(context)


class RefusingOnceBackend(RecordingBackend):
    """One malformed reply, then a legal choice - the recovered shape."""

    def complete_meta(self, context: str, history=None) -> tuple[str, str]:
        del history
        self.contexts.append(context)
        if len(self.contexts) == 1:
            self.replies.append("not json")
            return self.replies[-1], "fake-upstream"
        return RecordingBackend.complete_meta(self, self.contexts.pop())


class TestTheAskIsPriced(unittest.TestCase):
    def test_a_landed_ask_records_the_bytes_that_went_out(self):
        backend = RecordingBackend()
        adj = ModelAdjudicator(backend, random.Random(9))

        adj.sot_belief([ROLES["gauge"], ROLES["warder"]], random.Random(4))

        self.assertEqual(adj.events[0].ask_size, len(backend.contexts[0]))
        self.assertGreater(adj.events[0].ask_size, 0)

    def test_a_recovered_call_prices_the_attempt_that_LANDED(self):
        # the retry carries the referee's refusal back, so it is strictly the
        # larger ask - pricing the opening one would under-report every recovery.
        backend = RefusingOnceBackend(choice="gauge")
        adj = ModelAdjudicator(backend, random.Random(9), backoff=0.0)

        adj.sot_belief([ROLES["gauge"], ROLES["warder"]], random.Random(4))

        event = adj.events[0]
        self.assertTrue(event.recovered)
        self.assertEqual(len(backend.contexts), 2)
        self.assertEqual(event.ask_size, len(backend.contexts[1]))
        self.assertGreater(len(backend.contexts[1]), len(backend.contexts[0]))

    def test_a_fallback_costs_nothing_because_no_ask_landed(self):
        backend = RecordingBackend(choice="not-offered")
        adj = ModelAdjudicator(backend, random.Random(9), retries=0)

        adj.sot_belief([ROLES["gauge"], ROLES["warder"]], random.Random(4))

        self.assertTrue(adj.events[0].fallback)
        self.assertEqual(adj.events[0].ask_size, 0,
                         "a fallback reported the size of an ask that bought "
                         "nothing, which is the player-side zero inverted")


class TestARecalledAskCarriesItsSession(unittest.TestCase):
    """The case the field exists for: under `night_transcript` the payload is the
    same size on every night and the session in front of it is what grows."""

    BOARD1 = {"seat": 1, "night": 1, "neighbours": [0, 2], "true_count": 2,
              "prior": []}
    BOARD2 = {"seat": 1, "night": 2, "neighbours": [0, 2], "true_count": 2,
              "prior": [{"night": 1, "neighbours": [0, 2], "count": 1,
                         "truthful": False}]}

    def _adj(self, backend):
        return ModelAdjudicator(backend, random.Random(1), night=True,
                                night_prior=False, night_transcript=True,
                                ask_seed=7)

    def test_the_recalled_ask_prices_the_payload_and_every_earlier_turn(self):
        backend = TranscriptBackend(choice="1")
        adj = self._adj(backend)

        adj.gauge_false_count([0, 1], random.Random(0), dict(self.BOARD1))
        adj.gauge_false_count([0, 1], random.Random(0), dict(self.BOARD2))

        first, second = adj.events[0], adj.events[1]
        self.assertEqual(first.ask_size, len(backend.contexts[0]))
        self.assertEqual(
            second.ask_size,
            len(backend.contexts[1])
            + sum(len(ask) + len(reply) for ask, reply in backend.histories[1]))
        self.assertGreater(second.ask_size, len(backend.contexts[1]),
                           "the recalled ask priced only its own payload, so "
                           "the arm's own variable is invisible in the record")

    def test_the_withheld_arm_prices_the_payload_alone(self):
        backend = TranscriptBackend(choice="1")
        adj = ModelAdjudicator(backend, random.Random(1), night=True,
                               night_prior=False, ask_seed=7)

        adj.gauge_false_count([0, 1], random.Random(0), dict(self.BOARD1))
        adj.gauge_false_count([0, 1], random.Random(0), dict(self.BOARD2))

        self.assertEqual([e.ask_size for e in adj.events],
                         [len(c) for c in backend.contexts])


class TestTheFieldIsNotModelFacing(unittest.TestCase):
    """Same guarantee `core.callcost` carries: nothing about the instrument
    reaches the payload, so every number measured before it stands."""

    def test_no_ask_mentions_the_field(self):
        backend = RecordingBackend()
        adj = ModelAdjudicator(backend, random.Random(9))

        adj.sot_belief([ROLES["gauge"], ROLES["warder"]], random.Random(4))

        self.assertNotIn("ask_size", backend.contexts[0])
        self.assertEqual(set(json.loads(backend.contexts[0])),
                         {"choice_key", "options"})


class TestAnEventWrittenBeforeTheField(unittest.TestCase):
    """The event is serialised into the game row (`games/belfry/player.py`), and
    the verdict tools read those dicts off records that predate this field."""

    def test_the_six_positional_fields_still_construct(self):
        event = ChoiceEvent("sot_belief", ("witness",), "witness", False,
                            False, "judge")
        self.assertEqual(event.ask_size, 0)

    def test_a_current_event_round_trips_through_json(self):
        event = ChoiceEvent("sot_belief", ("witness",), "witness", False,
                            False, "judge", 2802)
        back = json.loads(json.dumps(asdict(event)))
        self.assertEqual(back["ask_size"], 2802)


if __name__ == "__main__":
    unittest.main()
