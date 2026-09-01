"""The call-cost seam: one declaration, and a record that predates it.

Both guards here are about the two ways this instrument could rot. A game could
re-declare the three fields locally and drift from the others, which no value
assertion would catch - so the shape is asserted, not just the values. And the
records already on disk were written before the fields existed, so a reader that
required them would make ~8000 recorded decisions unloadable.
"""

from __future__ import annotations

import json
import unittest
from dataclasses import asdict, fields

from core import callcost
from games.belfry.player import Decision as BelfryDecision
from games.cabal.player import Decision as CabalDecision
from games.changeling.player import Decision as ChangelingDecision
from games.quorum.player import Decision as QuorumDecision

#: Every game's decision record, and one legacy line for each - the keys a record
#: written before 2026-08-30 actually carries. The changeling row is the exact key
#: set of ``eval/records/s2.json.jsonl``, read off that file; the others are their
#: own pre-instrument shapes. Hardcoded rather than derived from the dataclass,
#: because a fixture derived from the class under test cannot fail with it.
LEGACY = {
    "belfry": (BelfryDecision, {
        "turn": 1, "day": 0, "seat": 3, "kind": "poison", "played": "poisons seat 2",
        "think": "", "refused": "", "refusals": 0, "rule_refusals": 0,
        "fell_back": False, "served_by": "local/q36",
    }),
    "cabal": (CabalDecision, {
        "turn": 4, "seat": 1, "phase": "vote", "played": "votes yes", "think": "",
        "note": "", "refused": "", "refusals": 0, "rule_refusals": 0,
        "fell_back": False, "served_by": "local/q36",
    }),
    "changeling": (ChangelingDecision, {
        "turn": 2, "seat": 0, "phase": "accuse", "played": "accuses seat 4",
        "think": "", "refused": "", "refusals": 0, "rule_refusals": 0,
        "fell_back": False, "served_by": "local/q36",
    }),
    "quorum": (QuorumDecision, {
        "turn": 7, "seat": 2, "phase": "vote", "played": "votes no", "think": "",
        "refused": "", "refusals": 0, "rule_refusals": 0, "fell_back": False,
        "model_controlled": True, "served_by": "local/q36",
    }),
}


class TestTheFieldsAreDeclaredOnce(unittest.TestCase):
    """S35's own ask: four games needed the same three fields, so they are
    declared in ``core`` and inherited, not copied into each game."""

    def test_every_game_s_decision_inherits_the_one_declaration(self):
        for name, (cls, _) in LEGACY.items():
            with self.subTest(game=name):
                self.assertTrue(
                    issubclass(cls, callcost.CallCost),
                    f"{name}'s Decision does not inherit core.callcost.CallCost - "
                    "a second copy of these fields is how two games come to record "
                    "cost differently")

    def test_no_game_redeclares_a_field_it_inherits(self):
        # a subclass's own ``__annotations__`` holds only what IT declared, so an
        # intersection here is a local copy that would silently shadow the shared
        # one - the exact drift inheriting was meant to end.
        shared = {f.name for f in fields(callcost.CallCost)}
        for name, (cls, _) in LEGACY.items():
            with self.subTest(game=name):
                copied = set(cls.__annotations__) & shared
                self.assertEqual(copied, set(),
                                 f"{name}'s Decision re-declares {copied} locally")

    def test_the_fields_are_the_three_the_record_carries(self):
        self.assertEqual([f.name for f in fields(callcost.CallCost)],
                         ["prompt_size", "reply_size", "usage"])


class TestARecordWrittenBeforeTheFieldsExisted(unittest.TestCase):
    """``Decision`` is serialised per game to the run's JSONL. Every field added
    to it must default, or every record already on disk stops loading."""

    def test_a_legacy_line_still_constructs_and_defaults_the_cost(self):
        for name, (cls, legacy) in LEGACY.items():
            with self.subTest(game=name):
                dec = cls(**json.loads(json.dumps(legacy)))
                self.assertEqual(dec.prompt_size, 0)
                self.assertEqual(dec.reply_size, 0)
                self.assertIsNone(
                    dec.usage,
                    "a record that predates the instrument must report NO usage, "
                    "which is not the same claim as zero tokens")

    def test_a_legacy_line_keeps_every_value_it_did_carry(self):
        for name, (cls, legacy) in LEGACY.items():
            with self.subTest(game=name):
                dec = cls(**legacy)
                for key, value in legacy.items():
                    self.assertEqual(getattr(dec, key), value,
                                     f"{name}.{key} did not survive the load")

    def test_a_current_decision_round_trips_through_json(self):
        for name, (cls, legacy) in LEGACY.items():
            with self.subTest(game=name):
                dec = cls(**legacy, prompt_size=2802, reply_size=1272,
                          usage={"total_tokens": 1110})
                back = cls(**json.loads(json.dumps(asdict(dec))))
                self.assertEqual(back.prompt_size, 2802)
                self.assertEqual(back.reply_size, 1272)
                self.assertEqual(back.usage, {"total_tokens": 1110})


class _Policy:
    """A policy with nothing on it, which is what ``forget`` writes to first."""


class _Backend:
    def __init__(self, usage=None):
        self.last_usage = usage


class TestTheCostOfTheLastCall(unittest.TestCase):
    """The three helpers, against the cases the games actually hit: a decision
    that called a model, one that fell back without a reply, and a policy that
    never calls one at all."""

    def test_note_records_the_bytes_and_carries_the_upstream_s_usage(self):
        p = _Policy()
        callcost.note(p, "a" * 40, "b" * 9, _Backend({"total_tokens": 12}))
        self.assertEqual(callcost.spent(p),
                         {"prompt_size": 40, "reply_size": 9,
                          "usage": {"total_tokens": 12}})

    def test_forget_clears_the_previous_decision_s_cost(self):
        p = _Policy()
        callcost.note(p, "a" * 40, "b" * 9, _Backend({"total_tokens": 12}))
        callcost.forget(p)
        self.assertEqual(callcost.spent(p),
                         {"prompt_size": 0, "reply_size": 0, "usage": None},
                         "a decision that called no model reported the size of "
                         "the last decision that did")

    def test_a_backend_reporting_no_usage_leaves_the_field_None(self):
        p = _Policy()
        callcost.note(p, "ctx", "reply", _Backend(None))
        self.assertIsNone(callcost.spent(p)["usage"])

    def test_a_policy_that_never_calls_a_model_costs_nothing(self):
        self.assertEqual(callcost.spent(_Policy()),
                         {"prompt_size": 0, "reply_size": 0, "usage": None})


if __name__ == "__main__":
    unittest.main()
