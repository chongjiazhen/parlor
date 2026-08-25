"""Player-policy tests: reply parsing, the refuse-and-retell loop, and the one
plumbing rule the discussion phase adds - a model's private reasoning must never
reach the table.

No network: a scripted fake backend stands in for the model, so these run in the
same dependency-free suite as the gates.
"""

import random
import unittest

from core.backends import Backend, Endpoint
from core.replies import ParseError
from games.cabal.player import (
    GameRecord,
    LLMPolicy,
    RandomPolicy,
    parse_action,
    parse_seat,
    parse_team,
    play_game,
)
from games.cabal.referee import CabalReferee, IllegalAction, Phase
from games.cabal.roles import HUNTER, LOYALIST, MIMIC, SEER, SETUP_5, WATCHER, Team

FIXED = {0: SEER, 1: WATCHER, 2: LOYALIST, 3: MIMIC, 4: HUNTER}


def fixed_ref(discussion_rounds=1):
    return CabalReferee(setup=SETUP_5, assignment=dict(FIXED), leader=0,
                        discussion_rounds=discussion_rounds)


class FakeBackend(Backend):
    """Replays scripted replies and records every prompt it was given."""

    def __init__(self, replies):
        super().__init__(endpoint=Endpoint("fake", "http://0.0.0.0/v1", False, ""),
                         model="fake")
        self.replies = list(replies)
        self.prompts = []

    #: ``complete_meta`` is the seam the policy calls - it returns the reply AND
    #: the upstream that served it. Overriding ``complete`` instead would leave the
    #: real HTTP path live under the test.
    def complete_meta(self, context: str) -> tuple[str, str]:
        self.prompts.append(context)
        return (self.replies.pop(0) if self.replies else "{}"), "fake-upstream"


class TestParsing(unittest.TestCase):
    """Phase -> key mapping only. The generic reply-reading is covered by
    ``core/test_replies.py``; these cases pin what this GAME asks for."""

    def test_a_truncated_reply_survives_the_whole_path(self):
        ref = fixed_ref(discussion_rounds=0)
        truncated = ('think": "seat 0 is our partner so the best play here is to '
                     'send", "team": [0, 3], "note": "cut off mid-')
        self.assertEqual(parse_action(truncated, ref)["team"], [0, 3])

    def test_the_wrong_key_for_the_phase_is_refused(self):
        ref = fixed_ref(discussion_rounds=0)          # PROPOSE wants "team"
        with self.assertRaises(ParseError):
            parse_action('{"vote": "approve"}', ref)

    def test_seat_forms(self):
        self.assertEqual(parse_seat(2, 5), 2)
        self.assertEqual(parse_seat("seat 3", 5), 3)
        with self.assertRaises(ParseError):
            parse_seat(9, 5)

    def test_team_forms(self):
        self.assertEqual(parse_team([2, 0], 5, 2), [0, 2])
        self.assertEqual(parse_team("seats 1 and 4", 5, 2), [1, 4])
        with self.assertRaises(ParseError):
            parse_team([1, 1], 5, 2)           # duplicates are not a team of two

    def test_vote_synonyms(self):
        ref = fixed_ref()
        ref.propose(0, [0, 1])
        ref.speaking_order()
        for seat in ref.speaking_order():
            ref.speak(seat, "hm")
        self.assertTrue(parse_action('{"vote": "Approve."}', ref)["vote"])
        self.assertFalse(parse_action('{"vote": "no"}', ref)["vote"])

    def test_card_words_map_to_the_referee_convention(self):
        ref = fixed_ref(discussion_rounds=0)
        ref.propose(0, [3, 4])
        ref.vote({s: True for s in ref.assignment})
        self.assertIs(ref.phase, Phase.MISSION)
        self.assertTrue(parse_action('{"card": "fail"}', ref)["card"])
        self.assertFalse(parse_action('{"card": "success"}', ref)["card"])

    def test_empty_say_is_not_a_move(self):
        ref = fixed_ref()
        ref.propose(0, [0, 1])
        with self.assertRaises(ParseError):
            parse_action('{"think": "I will stay quiet", "say": ""}', ref)


class TestRetryLoop(unittest.TestCase):
    def test_unparseable_then_good_reply(self):
        ref = fixed_ref(discussion_rounds=0)
        backend = FakeBackend(["I'd rather not.", '{"team": [0, 1]}'])
        policy = LLMPolicy(backend=backend, retries=2)
        action = policy.act(ref, 0)
        self.assertEqual(action["team"], [0, 1])
        self.assertFalse(policy.last_fell_back)
        self.assertIn("refused", backend.prompts[1])

    def test_illegal_move_is_retold_to_the_same_seat(self):
        ref = fixed_ref(discussion_rounds=0)
        ref.propose(0, [0, 1])
        ref.vote({s: True for s in ref.assignment})
        # seat 0 is good and may not fail; it should be told so, then correct itself
        backend = FakeBackend(['{"card": "fail"}', '{"card": "success"}'])
        policy = LLMPolicy(backend=backend, retries=2)
        action = policy.act(ref, 0)
        self.assertFalse(action["card"])
        self.assertIn("cannot fail", backend.prompts[1])
        self.assertFalse(policy.last_fell_back)

    def test_falls_back_to_random_after_the_cap(self):
        ref = fixed_ref(discussion_rounds=0)
        backend = FakeBackend(["no", "still no", "never"])
        policy = LLMPolicy(backend=backend, retries=2)
        action = policy.act(ref, 0)
        self.assertEqual(len(action["team"]), 2)          # a legal team, from random
        self.assertTrue(policy.last_fell_back)
        self.assertEqual(len(backend.prompts), 3)         # retries capped

    def test_transport_failure_is_retried_not_raised(self):
        class Dead(FakeBackend):
            def complete_meta(self, context):
                self.prompts.append(context)
                raise ConnectionError("endpoint down")

        policy = LLMPolicy(backend=Dead([]), retries=1, backoff=0)
        action = policy.act(fixed_ref(discussion_rounds=0), 0)
        self.assertEqual(len(action["team"]), 2)
        self.assertTrue(policy.last_fell_back)


class TestPrivateReasoningNeverGoesPublic(unittest.TestCase):
    def test_think_is_dropped_say_is_kept(self):
        ref = fixed_ref(discussion_rounds=1)
        ref.propose(0, [0, 1])
        reply = ('{"think": "I am the informant and seat 3 reads evil to me", '
                 '"say": "Seat 3 has been quiet."}')
        policy = LLMPolicy(backend=FakeBackend([reply]), retries=0)
        action = policy.act(ref, 0)
        ref.speak(0, action["say"])
        for viewer in ref.assignment:
            rendered = ref.render_context(viewer)
            self.assertIn("Seat 3 has been quiet.", rendered)
            self.assertNotIn("I am the informant", rendered)
        self.assertNotIn("I am the informant", " ".join(t for _, t in ref.public_events))
        self.assertNotIn("I am the informant", " ".join(ref.log))

    def test_driver_never_puts_think_on_the_table(self):
        """The same rule as above, but through the driver - that is the code path a
        real game uses, and the one that would quietly regress."""
        from games.cabal.demo import _SpeechOnly
        import random
        reply = '{"think": "SECRET-REASONING", "say": "Nothing to report."}'
        backend = FakeBackend([reply] * 500)
        rng = random.Random(4)
        ref = CabalReferee.new(5, seed=4, discussion_rounds=1)
        llm = LLMPolicy(backend=backend, retries=0, fallback=RandomPolicy(rng=rng))
        policies = {s: _SpeechOnly(llm, RandomPolicy(rng=rng)) for s in ref.assignment}
        rec = play_game(ref, policies)
        self.assertTrue(rec.utterances)
        haystack = " ".join(
            [t for _, t in ref.public_events] + ref.log + rec.utterances
            + [ref.render_context(v) for v in ref.assignment]
        )
        self.assertIn("Nothing to report.", haystack)
        self.assertNotIn("SECRET-REASONING", haystack)

    def test_a_lie_in_say_is_gameplay_not_a_leak(self):
        """A player may name a role out loud - true or false. Gate #1 audits the
        referee's own bytes, so the audit view must not see the claim at all."""
        ref = fixed_ref(discussion_rounds=1)
        ref.propose(0, [0, 1])
        ref.speak(0, "Seat 3 is the mimic, I saw it.")
        self.assertIn("mimic", ref.render_context(2))
        self.assertNotIn("mimic", ref.render_context(2, include_speech=False))

    def test_the_audit_still_fires_on_a_referee_authored_leak(self):
        """Positive control. The audit view drops player speech - it must not have
        gone blind to the channel it exists to police."""
        from games.cabal.audit import leak_audit as audit
        ref = fixed_ref(discussion_rounds=1)
        ref.propose(0, [0, 1])
        ref._event("clerical note: seat 3 is the mimic")
        self.assertTrue(any(term == "mimic" for _, _, term in audit(ref)))

    def test_the_ask_itself_names_no_foreign_role(self):
        from games.cabal.audit import leak_audit as audit
        ref = fixed_ref(discussion_rounds=1)
        for phase_setup in (lambda r: None,
                            lambda r: r.propose(0, [0, 1])):
            r = fixed_ref(discussion_rounds=1)
            phase_setup(r)
            self.assertEqual(audit(r), [])


class TestDriver(unittest.TestCase):
    def test_random_game_terminates_and_audits_clean(self):
        import random
        for seed in range(20):
            ref = CabalReferee.new(5, seed=seed, discussion_rounds=1)
            pol = RandomPolicy(rng=random.Random(seed))
            rec = play_game(ref, {s: pol for s in ref.assignment})
            self.assertIsNone(rec.error)
            self.assertIn(rec.winner, ("good", "evil"))
            self.assertEqual(rec.fallbacks, 0)
            self.assertTrue(rec.utterances)

    def test_record_captures_vote_truth_and_hunt(self):
        import random
        ref = CabalReferee.new(5, seed=11, discussion_rounds=1)
        pol = RandomPolicy(rng=random.Random(11))
        rec = play_game(ref, {s: pol for s in ref.assignment})
        self.assertTrue(rec.votes)
        for v in rec.votes:
            truth = any(ref.assignment[s].team is Team.EVIL for s in [v.seat])
            self.assertEqual(v.seat_is_evil, truth)
        if rec.hunt:
            self.assertEqual(rec.hunt["hit"], rec.hunt["target"] == rec.hunt["seer"])


class TestUpstreamAttribution(unittest.TestCase):
    """Under a routing alias (``auto``) the gateway picks a different upstream per
    request and nothing in the catalog says which answered - only the response
    body does. If the run cannot name what served each decision, its numbers
    belong to no model in particular."""

    class Rotating(FakeBackend):
        """Answers legally, naming a different upstream each call."""

        def __init__(self, reply: str, names):
            super().__init__([])
            self.reply, self.names, self.calls = reply, list(names), 0

        def complete_meta(self, context):
            self.prompts.append(context)
            served = self.names[self.calls % len(self.names)]
            self.calls += 1
            return self.reply, served

    def test_the_policy_counts_who_served_each_decision(self):
        backend = self.Rotating('{"team": [0, 1]}', ["up-a", "up-b"])
        policy = LLMPolicy(backend=backend, retries=0)
        ref = fixed_ref(discussion_rounds=0)
        for _ in range(4):
            policy.act(ref, 0)
        self.assertEqual(dict(policy.upstreams), {"up-a": 2, "up-b": 2})

    def test_a_shared_policy_is_counted_once_not_once_per_seat(self):
        """demo.py seats every player on ONE policy object. Summing the counter per
        seat would report five times the calls that actually happened."""
        backend = self.Rotating("{}", ["only-up"])       # never legal -> all retries
        policy = LLMPolicy(backend=backend, retries=0,
                           fallback=RandomPolicy(rng=random.Random(1)))
        ref = CabalReferee.new(5, seed=7, discussion_rounds=1)
        rec = play_game(ref, {s: policy for s in ref.assignment})
        self.assertEqual(rec.upstreams, {"only-up": backend.calls})
        self.assertEqual(rec.fallbacks, rec.decisions)   # nothing legal ever landed

    def test_the_record_carries_the_mix(self):
        backend = self.Rotating('{"say": "hello"}', ["up-a", "up-b", "up-a"])
        ref = CabalReferee.new(5, seed=3, discussion_rounds=1)
        policies = {s: LLMPolicy(backend=backend, retries=0,
                                 fallback=RandomPolicy(rng=random.Random(3)))
                    for s in ref.assignment}
        # only the DISCUSS phase can use the scripted reply; the rest fall back,
        # which is fine - what is under test is that served upstreams are recorded
        rec = play_game(ref, policies)
        self.assertTrue(rec.upstreams)
        self.assertLessEqual(set(rec.upstreams), {"up-a", "up-b"})
        self.assertEqual(sum(rec.upstreams.values()), backend.calls)




class TestVoteKnowledgeSplit(unittest.TestCase):
    """A vote by a seat that was TOLD one of these seats is evil is not evidence of
    deduction. Recorded per vote rather than per role, because a seer whose known
    evils are off the table is voting as blind as anyone else that round."""

    def test_it_marks_the_seat_the_night_informed(self):
        ref = fixed_ref(discussion_rounds=0)          # seat 0 seer, 3 and 4 evil
        rng = random.Random(0)
        policies = {s: RandomPolicy(rng=rng) for s in ref.assignment}
        rec = GameRecord()

        def vote_on(team):
            ref.propose(ref.leader, team)
            rec.votes.clear()
            play_one_vote(ref, policies, rec)
            return {v.seat: v.knew_evil_on_team for v in rec.votes}

        knew = vote_on([0, 3])
        self.assertTrue(knew[0])        # seer, told about seat 3
        self.assertFalse(knew[2])       # loyalist, told nothing
        self.assertTrue(knew[4])        # evil, knows its fellow

    def test_a_seer_with_no_known_evil_on_the_table_counts_as_blind(self):
        ref = fixed_ref(discussion_rounds=0)
        rng = random.Random(0)
        policies = {s: RandomPolicy(rng=rng) for s in ref.assignment}
        rec = GameRecord()
        ref.propose(ref.leader, [1, 2])
        play_one_vote(ref, policies, rec)
        self.assertFalse({v.seat: v.knew_evil_on_team for v in rec.votes}[0])


def play_one_vote(ref, policies, rec):
    """The driver's VOTE branch, isolated: run one vote and record it."""
    from games.cabal.player import VoteRecord
    team = ref.proposal
    team_has_evil = any(ref.assignment[s].team is Team.EVIL for s in team)
    votes = {}
    for seat in sorted(ref.assignment):
        known_evil = {k.seat for k in ref.entitled_knowledge(seat)
                      if k.label in ("evil", "fellow-evil")}
        votes[seat] = policies[seat].act(ref, seat)["vote"]
        rec.votes.append(VoteRecord(
            seat=seat, approved=votes[seat],
            seat_is_evil=ref.assignment[seat].team is Team.EVIL,
            team_has_evil=team_has_evil,
            knew_evil_on_team=bool(known_evil & set(team)),
        ))
    ref.vote(votes)


class TestPerDecisionAttribution(unittest.TestCase):
    """The per-run mix says who played the run. Only the per-decision record says
    who made THAT move - and under a routing alias the seat that misread the hunt
    and the seat that voted well can be different models entirely."""

    def test_each_decision_names_the_upstream_that_answered_it(self):
        backend = TestUpstreamAttribution.Rotating('{"vote": "approve"}',
                                                   ["up-a", "up-b"])
        ref = fixed_ref(discussion_rounds=0)
        ref.propose(0, [0, 1])
        policy = LLMPolicy(backend=backend, retries=0)
        rec = GameRecord()
        served = []
        for seat in sorted(ref.assignment):
            policy.act(ref, seat)
            served.append(policy.last_upstream)
        del rec
        self.assertEqual(served, ["up-a", "up-b", "up-a", "up-b", "up-a"])

    def test_a_fallback_names_nobody(self):
        """The random policy answered it, not a model. Attributing it to whichever
        upstream last succeeded would put a random move on a model's record."""
        backend = TestUpstreamAttribution.Rotating("{}", ["up-a"])   # never legal
        policy = LLMPolicy(backend=backend, retries=0,
                           fallback=RandomPolicy(rng=random.Random(1)))
        ref = CabalReferee.new(5, seed=7, discussion_rounds=1)
        rec = play_game(ref, {s: policy for s in ref.assignment})
        self.assertTrue(rec.decision_log)
        self.assertTrue(all(d.fell_back for d in rec.decision_log))
        self.assertTrue(all(d.served_by == "" for d in rec.decision_log))

    def test_the_log_carries_it_through_a_real_game(self):
        backend = TestUpstreamAttribution.Rotating('{"say": "hello"}', ["up-a"])
        ref = CabalReferee.new(5, seed=3, discussion_rounds=1)
        rec = play_game(ref, {s: LLMPolicy(backend=backend, retries=0,
                                           fallback=RandomPolicy(rng=random.Random(3)))
                              for s in ref.assignment})
        spoke = [d for d in rec.decision_log if d.phase == "discuss" and not d.fell_back]
        self.assertTrue(spoke)
        self.assertTrue(all(d.served_by == "up-a" for d in spoke))


if __name__ == "__main__":
    unittest.main()
