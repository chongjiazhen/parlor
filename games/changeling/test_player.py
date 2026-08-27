"""Policies, the driver, and the record it produces.

The driver's job is to be boring and honest: refuse nothing silently, count every
fallback, and never score a game whose bytes leaked.
"""

from __future__ import annotations

import random
import unittest

from core.replies import ParseError
from games.changeling.audit import LeakDetected
from games.changeling.player import (GameRecord, LLMPolicy, RandomPolicy,
                                     parse_action, play_game)
from games.changeling.referee import ChangelingReferee, Phase
from games.changeling.roles import Side


class FakeBackend:
    """Replies from a script, so the retry loop is tested without a model."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = 0

    def complete_meta(self, prompt: str):
        self.calls += 1
        if not self.replies:
            raise RuntimeError("script exhausted")
        item = self.replies.pop(0)
        if isinstance(item, Exception):
            raise item
        return item, "fake-model"


def one_game(seed: int, rounds: int = 1) -> GameRecord:
    ref = ChangelingReferee.new(5, seed=seed, discussion_rounds=rounds)
    rng = random.Random(seed)
    return play_game(ref, {s: RandomPolicy(rng) for s in range(5)})


class TestRandomArmPlaysCleanly(unittest.TestCase):
    def test_many_games_finish_with_no_error_and_no_fallback(self):
        for seed in range(200):
            rec = one_game(seed)
            self.assertIsNone(rec.error, f"seed {seed}: {rec.error}")
            self.assertIn(rec.winner, ("village", "pack"))
            self.assertEqual(rec.fallbacks, 0, "the control arm cannot fall back")

    def test_every_seat_votes_exactly_once_and_never_for_itself(self):
        rec = one_game(5)
        self.assertEqual(len(rec.votes), 5)
        self.assertEqual(sorted(v.seat for v in rec.votes), [0, 1, 2, 3, 4])
        for v in rec.votes:
            self.assertNotEqual(v.seat, v.target)

    def test_the_record_keeps_truth_and_belief_side_by_side(self):
        """A record holding only one of them could not answer the question this
        game exists to ask."""
        for seed in range(80):
            rec = one_game(seed)
            if rec.diverged:
                seat = rec.diverged[0]
                self.assertNotEqual(rec.truth[seat], rec.belief[seat])
                self.assertEqual(len(rec.truth), 5)
                self.assertEqual(len(rec.belief), 5)
                return
        self.fail("no diverged game in range")


class TestOutcomeIsReadFromTruth(unittest.TestCase):
    def test_village_wins_exactly_when_an_accused_seat_holds_pack(self):
        for seed in range(200):
            rec = one_game(seed)
            caught = any(rec.truth[a] == "pack" for a in rec.accused)
            self.assertEqual(rec.winner == "village", caught, f"seed {seed}")

    def test_belief_never_decides_the_winner(self):
        """Mutation bait: scoring on belief would agree with truth most of the
        time, so this looks for a game where the two disagree and pins it."""
        for seed in range(400):
            rec = one_game(seed)
            by_truth = any(rec.truth[a] == "pack" for a in rec.accused)
            by_belief = any(rec.belief[a] == "pack" for a in rec.accused)
            if by_truth != by_belief:
                self.assertEqual(rec.winner == "village", by_truth)
                return
        self.fail("truth and belief never disagreed on an accused seat")


class TestVoteRecordStrata(unittest.TestCase):
    def test_knowledge_class_is_keyed_on_the_DEALT_card(self):
        """The reveal is a historical fact, so the class comes from the deal. Using
        the dawn card would relabel a seat by something that happened after it was
        told - and would put `false` on a seat that was never deceived."""
        for seed in range(120):
            ref = ChangelingReferee.new(5, seed=seed, discussion_rounds=1)
            rng = random.Random(seed)
            rec = play_game(ref, {s: RandomPolicy(rng) for s in range(5)})
            for v in rec.votes:
                self.assertEqual(v.knowledge_class,
                                 ref.night.dealt[v.seat].knowledge_class)

    def test_the_three_voter_booleans_come_apart(self):
        """holds / believes / diverged are separate columns because in this game
        they disagree. A run where they never do would mean the night is inert."""
        seen = set()
        for seed in range(400):
            for v in one_game(seed).votes:
                seen.add((v.voter_holds_pack, v.voter_believes_pack))
        self.assertIn((True, False), seen, "no seat ever held pack unknowingly")
        self.assertIn((False, True), seen, "no seat ever believed pack wrongly")


class TestParse(unittest.TestCase):
    def setUp(self):
        self.ref = ChangelingReferee.new(5, seed=3, discussion_rounds=1)

    def test_an_empty_utterance_is_not_a_move(self):
        with self.assertRaises(ParseError):
            parse_action('{"say": "   "}', self.ref, 0)

    def test_a_vote_outside_the_table_is_refused(self):
        self.ref.close_round()
        with self.assertRaises(ParseError):
            parse_action('{"vote": 9}', self.ref, 0)

    def test_think_is_read_and_never_published(self):
        act = parse_action('{"say": "hello", "think": "secret"}', self.ref, 0)
        self.assertEqual(act["think"], "secret")
        self.ref.speak(0, act["say"])
        joined = " ".join(t for _, t in self.ref.public_events)
        self.assertNotIn("secret", joined)


class TestRetryLoop(unittest.TestCase):
    def test_a_refused_reply_is_retold_and_the_seat_answers_again(self):
        ref = ChangelingReferee.new(5, seed=3, discussion_rounds=1)
        policy = LLMPolicy(backend=FakeBackend(['{"nope": 1}', '{"say": "here"}']),
                           backoff=0)
        action = policy.act(ref, 0)
        self.assertEqual(action["say"], "here")
        self.assertFalse(policy.last_fell_back)
        self.assertTrue(any("unparsed" in t for t in policy.trace))

    def test_exhausted_retries_fall_back_to_random_and_are_COUNTED(self):
        ref = ChangelingReferee.new(5, seed=3, discussion_rounds=1)
        policy = LLMPolicy(backend=FakeBackend(['{}'] * 3), retries=2, backoff=0)
        action = policy.act(ref, 0)
        self.assertIn("say", action)              # random supplied a legal move
        self.assertTrue(policy.last_fell_back)
        self.assertEqual(policy.last_upstream, "", "a fallback was attributed to a "
                                                   "model that did not serve it")

    def test_a_self_vote_is_refused_and_retold(self):
        ref = ChangelingReferee.new(5, seed=3, discussion_rounds=1)
        ref.close_round()
        policy = LLMPolicy(backend=FakeBackend(['{"vote": 0}', '{"vote": 2}']),
                           backoff=0)
        self.assertEqual(policy.act(ref, 0)["vote"], 2)
        self.assertTrue(any("illegal" in t for t in policy.trace))

    def test_the_fallback_REASON_rides_on_the_decision(self):
        """cabal's JSONL records note:'' on every fallback, so its refusal
        diagnosis survives only in a sampled trace and an end-of-run report. Same
        bug, not repeated: the refusal string is on the decision itself."""
        ref = ChangelingReferee.new(5, seed=3, discussion_rounds=1)
        policies = {s: RandomPolicy(random.Random(s)) for s in range(5)}
        policies[0] = LLMPolicy(backend=FakeBackend(['{}'] * 40), retries=1,
                                backoff=0)
        rec = play_game(ref, policies)
        fell = [d for d in rec.decision_log if d.fell_back]
        self.assertTrue(fell)
        self.assertTrue(all(d.note for d in fell),
                        "a fallback landed with no reason recorded")

    def test_a_transport_failure_is_distinguishable_from_a_bad_reply(self):
        ref = ChangelingReferee.new(5, seed=3, discussion_rounds=1)
        policy = LLMPolicy(backend=FakeBackend([RuntimeError("boom"),
                                                '{"say": "ok"}']), backoff=0)
        policy.act(ref, 0)
        self.assertTrue(any("call failed" in t for t in policy.trace))


class TestAuditRunsInsideTheDriver(unittest.TestCase):
    def test_a_leaking_referee_RAISES_rather_than_being_scored(self):
        """The eval lane once ran live models unaudited because a callback was
        opt-in. This is why the audit is on by default and raises."""
        from games.changeling.test_referee import LeaksOwnTruth, find_diverged_seed
        ref = LeaksOwnTruth.new(5, seed=find_diverged_seed(),
                                discussion_rounds=1)
        rng = random.Random(0)
        with self.assertRaises(LeakDetected):
            play_game(ref, {s: RandomPolicy(rng) for s in range(5)})

    def test_audit_off_is_possible_but_never_the_default(self):
        import inspect
        sig = inspect.signature(play_game)
        self.assertIs(sig.parameters["audit"].default, True)


class TestReviewFixes(unittest.TestCase):
    """Regressions for defects found by review 2026-08-27. Each asserts the FIXED
    behaviour, so a revert fails here rather than going quiet."""

    class SelfVoter:
        """A policy that is neither of the two shipped ones - the case the coercion
        laundered, since LLMPolicy retries a self-vote and RandomPolicy cannot make
        one."""
        def act(self, ref, seat):
            if ref.phase is Phase.DISCUSS:
                return {"say": "..."}
            return {"vote": seat}

    def test_a_self_vote_is_refused_not_laundered_into_the_record(self):
        ref = ChangelingReferee.new(5, seed=3, discussion_rounds=1)
        policies = {s: RandomPolicy(random.Random(s)) for s in range(5)}
        policies[2] = self.SelfVoter()
        rec = play_game(ref, policies)
        self.assertIsNotNone(rec.error, "an illegal self-vote was scored silently")
        self.assertIn("IllegalAction", rec.error)
        self.assertFalse([v for v in rec.votes if v.seat == v.target])

    def test_the_record_keeps_what_the_table_SAW_not_what_was_proposed(self):
        ref = ChangelingReferee.new(5, seed=3, discussion_rounds=1)

        class Rambler:
            def act(self, ref, seat):
                if ref.phase is Phase.DISCUSS:
                    return {"say": "x  y" + "z" * 900}
                return {"vote": ref.legal_votes(seat)[0]}

        policies = {s: Rambler() for s in range(5)}
        rec = play_game(ref, policies)
        published = [t.split(": ", 1)[1] for tag, t in rec.public_events
                     if tag == "speech"]
        self.assertEqual(rec.utterances, published)
        for u in rec.utterances:
            self.assertLessEqual(len(u), 280)
            self.assertNotIn("  ", u)


if __name__ == "__main__":
    unittest.main()
