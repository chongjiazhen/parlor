"""Reading a reply, refusing an illegal move, and counting what happened.

The accounting is the part worth testing hardest. A fallback that is not counted
is the random policy wearing a model's name, and a recovered decision counted as
clean is a run reported as something it was not - both of them silent, and both of
them read by ``core/integrity.py`` off the fields this module writes.
"""

from __future__ import annotations

import random
import unittest

from core.replies import ParseError
from games.belfry.player import (LLMPolicy, RandomPolicy, illegal_reason,
                                 parse_action, play_game)
from games.belfry.referee import BelfryReferee, Turn
from games.belfry.test_referee import FIVE, advance_to, rigged


class Canned:
    """A backend that reads from a list. Anything past the end repeats the last
    line, so a test only writes the replies it is about."""

    def __init__(self, replies, upstream="canned"):
        self.replies = list(replies)
        self.upstream = upstream
        self.seen = []

    def complete_meta(self, context):
        self.seen.append(context)
        reply = self.replies[min(len(self.seen) - 1, len(self.replies) - 1)]
        if isinstance(reply, Exception):
            raise reply
        return reply, self.upstream


class TestParsing(unittest.TestCase):
    def turn_for(self, ref):
        return ref.pending()

    def test_a_night_choice_reads_a_bare_number(self):
        ref = rigged(FIVE)
        turn = ref.pending()
        out = parse_action('{"think": "x", "target": 3}', ref, turn)
        self.assertEqual(out["target"], 3)
        self.assertEqual(out["think"], "x")

    def test_a_night_choice_reads_prose_around_the_object(self):
        ref = rigged(FIVE)
        turn = ref.pending()
        out = parse_action('Sure! {"target": "seat 2"} - that one.', ref, turn)
        self.assertEqual(out["target"], 2)

    def test_a_missing_key_is_refused_rather_than_defaulted(self):
        ref = rigged(FIVE)
        turn = ref.pending()
        with self.assertRaises(ParseError):
            parse_action('{"think": "hmm"}', ref, turn)

    def test_a_seat_outside_the_table_is_refused(self):
        ref = rigged(FIVE)
        turn = ref.pending()
        with self.assertRaises(ParseError):
            parse_action('{"target": 99}', ref, turn)

    def test_speech_is_required_to_say_something(self):
        ref = rigged(FIVE)
        turn = advance_to(ref, "speak")
        with self.assertRaises(ParseError):
            parse_action('{"say": "   "}', ref, turn)

    def test_a_public_day_power_is_optional_and_read_when_present(self):
        ref = rigged(FIVE)
        turn = advance_to(ref, "speak")
        plain = parse_action('{"say": "hello"}', ref, turn)
        self.assertNotIn("slay", plain)
        armed = parse_action('{"say": "hello", "slay": 2}', ref, turn)
        self.assertEqual(armed["slay"], 2)

    def test_a_null_day_power_is_not_a_move(self):
        ref = rigged(FIVE)
        turn = advance_to(ref, "speak")
        for value in ("null", "none", "pass", None):
            out = parse_action('{"say": "hi", "slay": %s}'
                               % ("null" if value is None else f'"{value}"'),
                               ref, turn)
            self.assertNotIn("slay", out)

    def test_a_pass_is_read_as_a_pass(self):
        ref = rigged(FIVE)
        turn = advance_to(ref, "nominate")
        for text in ('{"nominate": null}', '{"nominate": "pass"}',
                     '{"nominate": "nobody"}'):
            self.assertIsNone(parse_action(text, ref, turn)["nominate"])

    def test_a_vote_reads_a_word_or_a_boolean(self):
        ref = rigged(FIVE)
        turn = advance_to(ref, "nominate")
        ref.submit(turn.seat, {"nominate": (turn.seat + 1) % ref.n})
        vote = ref.pending()
        self.assertTrue(parse_action('{"vote": true}', ref, vote)["vote"])
        self.assertTrue(parse_action('{"vote": "yes"}', ref, vote)["vote"])
        self.assertFalse(parse_action('{"vote": "no"}', ref, vote)["vote"])

    def test_the_two_seat_choice_needs_two_distinct_seats(self):
        ref = rigged(["fiend", "venom", "diviner", "warder", "bulwark", "tally"])
        turn = advance_to(ref, "divine")
        self.assertEqual(parse_action('{"targets": [1, 3]}', ref, turn)["targets"],
                         [1, 3])
        with self.assertRaises(ParseError):
            parse_action('{"targets": [2, 2]}', ref, turn)

    def test_a_truncated_reply_is_salvaged_rather_than_thrown_away(self):
        """A provider that cuts a long reply mid-object leaves unambiguous key/value
        text behind. Throwing it away spends a retry and, at the cap, replaces a
        real decision with a random one."""
        ref = rigged(FIVE)
        turn = ref.pending()
        out = parse_action('{"think": "a long thought that got cut", "target": 2',
                           ref, turn)
        self.assertEqual(out["target"], 2)


class TestLegality(unittest.TestCase):
    def test_an_illegal_target_is_named_with_the_legal_list(self):
        # The protecting step, because it is one of the few with an illegal seat
        # to name at all: it may not choose itself.
        ref = rigged(FIVE)
        turn = advance_to(ref, "protect")
        illegal = next(s for s in range(ref.n)
                       if s not in ref.legal_targets(turn.seat, turn.kind))
        reason = illegal_reason(ref, turn, {"target": illegal})
        self.assertIn(str(illegal), reason)
        self.assertIn("choose from", reason)

    def test_a_legal_move_has_no_complaint(self):
        ref = rigged(FIVE)
        turn = ref.pending()
        legal = ref.legal_targets(turn.seat, turn.kind)[0]
        self.assertEqual(illegal_reason(ref, turn, {"target": legal}), "")

    def test_the_complaint_matches_what_the_ask_printed(self):
        """One source for the legal list. Two would let a seat be refused for the
        move its own prompt told it to make."""
        ref = rigged(FIVE)
        turn = ref.pending()
        ask = ref.ask(turn.seat)
        for seat in ref.legal_targets(turn.seat, turn.kind):
            self.assertIn(str(seat), ask.split("Choose from:")[-1])


class TestTheRetryLoop(unittest.TestCase):
    def test_a_clean_decision_is_neither_refused_nor_a_fallback(self):
        ref = rigged(FIVE)
        policy = LLMPolicy(backend=Canned(['{"target": 2}']), backoff=0)
        policy.act(ref, ref.pending().seat)
        self.assertFalse(policy.last_fell_back)
        self.assertEqual(policy.last_refusals, 0)

    def test_an_illegal_reply_is_sent_back_with_the_reason(self):
        ref = rigged(FIVE)
        turn = advance_to(ref, "protect")
        seat = turn.seat
        illegal = next(s for s in range(ref.n)
                       if s not in ref.legal_targets(seat, turn.kind))
        legal = ref.legal_targets(seat, turn.kind)[0]
        policy = LLMPolicy(backend=Canned(['{"target": %d}' % illegal,
                                           '{"target": %d}' % legal]), backoff=0)
        action = policy.act(ref, seat)
        self.assertEqual(action["target"], legal)
        self.assertFalse(policy.last_fell_back)
        self.assertEqual(policy.last_rule_refusals, 1)
        self.assertIn("refused", policy.backend.seen[1])

    def test_nothing_legal_falls_back_and_says_so(self):
        ref = rigged(FIVE)
        policy = LLMPolicy(backend=Canned(["not json at all"]), retries=1,
                           backoff=0, fallback=RandomPolicy(random.Random(0)))
        action = policy.act(ref, ref.pending().seat)
        self.assertTrue(policy.last_fell_back)
        self.assertEqual(policy.last_refusals, 2)
        self.assertEqual(policy.last_upstream, "")
        self.assertIn("target", action)

    def test_a_transport_failure_is_not_counted_against_the_model(self):
        """A 429 says nothing about play; an unparsed reply says everything. The
        integrity block splits them, so the policy has to."""
        ref = rigged(FIVE)
        policy = LLMPolicy(backend=Canned([RuntimeError("429"),
                                           '{"target": 2}']), backoff=0)
        policy.act(ref, ref.pending().seat)
        self.assertEqual(policy.last_refusals, 1)
        self.assertEqual(policy.last_rule_refusals, 0)


class TestVoteProvenance(unittest.TestCase):
    """A vote cast by the random fallback is not a model vote. The driver writes
    the same decision's provenance onto the VoteRecord it lands, so the scorer
    can drop it without asking the policy anything."""

    class Stubborn:
        """Answers every ask with garbage, so every decision falls back."""

        def __init__(self, rng):
            self.rng = rng
            self.last_fell_back = False
            self.last_refusals = 0
            self.last_rule_refusals = 0
            self.last_refusal = ""
            self.last_upstream = ""
            self.trace = []
            self.upstreams = {}

        def act(self, ref, seat):
            self.last_fell_back = True
            return RandomPolicy(self.rng).act(ref, seat)

    def _run_game(self, policy_for, seed=0):
        ref = BelfryReferee.new(5, seed=seed, max_days=2)
        policies = {s: policy_for(s) for s in range(5)}
        return play_game(ref, policies)

    def test_a_fallback_vote_carries_its_own_provenance(self):
        rec = self._run_game(lambda s: self.Stubborn(random.Random(s)))
        self.assertIsNone(rec.error)
        votes = [d for d in rec.decision_log if d.kind == "vote"]
        self.assertTrue(votes)
        for v, d in zip(rec.votes, votes):
            self.assertTrue(v.fell_back)
            self.assertTrue(d.fell_back)
            self.assertEqual(v.turn, d.turn)

    def test_a_clean_vote_carries_no_fallback(self):
        rec = self._run_game(lambda s: RandomPolicy(random.Random(s)))
        self.assertIsNone(rec.error)
        self.assertTrue(rec.votes)
        for v, d in zip(rec.votes,
                        [d for d in rec.decision_log if d.kind == "vote"]):
            self.assertFalse(v.fell_back)
            self.assertFalse(d.fell_back)
            self.assertEqual(v.turn, d.turn)

    def test_vote_turns_are_unique_and_joinable(self):
        """A day holds many votes by the same seat, so (day, seat) cannot join
        a vote to its decision. turn can, and every vote has one."""
        ref = BelfryReferee.new(7, seed=0)
        rng = random.Random(0)
        rec = play_game(ref, {s: RandomPolicy(rng) for s in range(7)})
        turns = [v.turn for v in rec.votes]
        self.assertEqual(len(turns), len(set(turns)))
        self.assertNotIn(-1, turns)
        # and the game DID put one seat at the same (day, seat) more than once,
        # or the uniqueness above is not exercising the defect
        self.assertLess(len({(v.day, v.seat) for v in rec.votes}), len(turns))

    def test_an_llm_vote_that_fell_back_is_marked_on_both_records(self):
        ref = BelfryReferee.new(5, seed=0, max_days=2)
        rng = random.Random(0)
        policies = {s: LLMPolicy(backend=Canned(["not json at all"]), retries=0,
                                 backoff=0,
                                 fallback=RandomPolicy(random.Random(s)))
                    for s in range(5)}
        rec = play_game(ref, policies)
        self.assertIsNone(rec.error)
        for v in rec.votes:
            self.assertTrue(v.fell_back)
        for d in rec.decision_log:
            if d.kind == "vote":
                self.assertTrue(d.fell_back)


class TestTheDriver(unittest.TestCase):
    def run_random(self, n=7, seed=0):
        ref = BelfryReferee.new(n, seed=seed)
        rng = random.Random(seed)
        return ref, play_game(ref, {s: RandomPolicy(rng) for s in range(n)})

    def test_a_game_records_a_winner_and_a_board(self):
        ref, rec = self.run_random()
        self.assertIn(rec.winner, ("good", "evil", None))
        self.assertEqual(len(rec.dealt), 7)
        self.assertEqual(len(rec.final), 7)
        self.assertGreater(rec.decisions, 0)

    def test_the_record_holds_what_was_published_not_what_was_proposed(self):
        ref = rigged(FIVE)
        turn = advance_to(ref, "speak")
        long_line = "x" * 400
        policies = {s: RandomPolicy(random.Random(0)) for s in range(ref.n)}

        class Says:
            def act(self, ref, seat):
                return {"say": long_line}

        policies[turn.seat] = Says()
        # One decision is enough: the driver reads back what `speak` published.
        ref.submit(turn.seat, {"say": long_line})
        self.assertLess(len(ref.last_said), len(long_line))

    def test_every_decision_is_logged_once(self):
        ref, rec = self.run_random()
        self.assertEqual(len(rec.decision_log), rec.decisions)
        self.assertEqual(rec.fallbacks, sum(1 for d in rec.decision_log
                                            if d.fell_back))

    def test_a_random_table_never_falls_back(self):
        """The control policy plays legal moves by construction. A fallback here
        would mean the legal-target list and the referee disagree."""
        for seed in range(5):
            _, rec = self.run_random(9, seed)
            self.assertEqual(rec.fallbacks, 0)
            self.assertIsNone(rec.error)

    def test_votes_are_recorded_with_the_alignment_a_scorer_stratifies_on(self):
        for seed in range(8):
            ref, rec = self.run_random(9, seed)
            for v in rec.votes:
                self.assertIs(v.voter_evil,
                              ref.grim.seat(v.seat).align.value == "evil")
                self.assertIn(v.nominee, range(9))

    def test_the_driver_stops_at_the_referee_s_bound(self):
        ref = BelfryReferee.new(7, seed=1, max_days=1)
        rng = random.Random(1)
        rec = play_game(ref, {s: RandomPolicy(rng) for s in range(7)})
        self.assertIsNone(rec.error)
        self.assertLessEqual(rec.days, 1)


if __name__ == "__main__":
    unittest.main()


class TestTheDeadMaySpeakButNotSlay(unittest.TestCase):
    """The dead speak every round, and the speak ask advertises ``slay``
    unconditionally. ``_apply_slay`` refuses a dead seat, so a pre-check that
    does not is how a legal-looking action reaches ``submit`` and raises - which
    ends the game and drops the record from every figure.
    """

    def _dead_speaker(self):
        ref = rigged(FIVE)
        turn = advance_to(ref, "speak")
        ref.grim.seat(turn.seat).alive = False
        return ref, turn

    def test_a_dead_seat_naming_a_target_is_refused_before_submit(self):
        ref, turn = self._dead_speaker()
        target = next(t for t in range(ref.grim.n) if t != turn.seat)
        reason = illegal_reason(ref, turn, {"say": "I accuse.", "slay": target})
        self.assertIn("dead", reason)

    def test_a_dead_seat_may_still_speak(self):
        ref, turn = self._dead_speaker()
        self.assertEqual(illegal_reason(ref, turn, {"say": "I accuse."}), "")

    def test_a_living_seat_is_untouched(self):
        ref = rigged(FIVE)
        turn = advance_to(ref, "speak")
        allowed = ref.legal_targets(turn.seat, "slay")
        self.assertEqual(
            illegal_reason(ref, turn, {"say": "hi", "slay": allowed[0]}), "")
