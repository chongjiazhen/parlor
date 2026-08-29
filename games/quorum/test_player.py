"""Action channel, policies, driver, and the console seat."""

from __future__ import annotations

import inspect
import io
import random
import unittest

from core.console import ConsoleBackend, TooManyHumans, human_seats
from core.replies import ParseError
from games.quorum.audit import LeakDetected
from games.quorum.demo import opening_view
from games.quorum.player import (ACTION_KEYS, LLMPolicy, RandomPolicy,
                                 parse_action, play_game)
from games.quorum.referee import IllegalAction, Phase, QuorumReferee
from games.quorum.roles import ADVANCES, Card, Side


def at(phase: Phase, seed: int = 3) -> QuorumReferee:
    """A referee parked at ``phase``, driven there by legal random play."""
    ref = QuorumReferee.new(5, seed=seed, discussion_rounds=1)
    rng = random.Random(seed)
    pol = RandomPolicy(rng=rng)
    for _ in range(400):
        if ref.phase is phase:
            return ref
        if ref.phase is Phase.DONE:
            break
        clock = ref.on_clock()
        seat = clock[0] if clock else None
        if ref.phase is Phase.VOTE:
            ref.vote({s: pol.act(ref, s)["vote"] for s in clock})
        elif ref.phase is Phase.NOMINATE:
            ref.nominate(seat, pol.act(ref, seat)["nominate"])
        elif ref.phase is Phase.DISCUSS:
            ref.speak(seat, pol.act(ref, seat)["say"])
        elif ref.phase is Phase.PROPOSER_DISCARD:
            ref.proposer_discard(seat, pol.act(ref, seat)["discard"])
        elif ref.phase is Phase.ENACTOR_DISCARD:
            ref.enactor_discard(seat, pol.act(ref, seat)["discard"])
        elif ref.phase is Phase.POWER:
            ref.use_power(seat, pol.act(ref, seat)["target"])
    raise AssertionError(f"never reached {phase}")


class TestParsing(unittest.TestCase):
    def test_each_phase_reads_its_own_key(self):
        ref = at(Phase.NOMINATE)
        seat = ref.proposer
        target = ref.eligible_nominees()[0]
        self.assertEqual(
            parse_action(f'{{"nominate": {target}}}', ref, seat)["nominate"], target)

        ref = at(Phase.VOTE)
        self.assertTrue(parse_action('{"vote": "approve"}', ref, ref.living()[0])["vote"])

        ref = at(Phase.PROPOSER_DISCARD)
        self.assertEqual(
            parse_action('{"discard": 2}', ref, ref.proposer)["discard"], 2)

    def test_prose_around_the_object_costs_nothing(self):
        ref = at(Phase.VOTE)
        seat = ref.living()[0]
        got = parse_action('Sure. ```json\n{"think":"hm","vote":false}\n```',
                           ref, seat)
        self.assertFalse(got["vote"])
        self.assertEqual(got["think"], "hm")

    def test_a_discard_index_outside_the_hand_is_refused(self):
        ref = at(Phase.PROPOSER_DISCARD)
        with self.assertRaises(ParseError):
            parse_action('{"discard": 3}', ref, ref.proposer)

    def test_a_seat_holding_no_cards_cannot_discard(self):
        """The index is bounded by what THIS seat may see, so a seat out of office
        is refused by the parser before the referee ever sees the move."""
        ref = at(Phase.PROPOSER_DISCARD)
        other = next(s for s in ref.living() if s != ref.proposer)
        with self.assertRaises(ParseError):
            parse_action('{"discard": 0}', ref, other)

    def test_an_empty_utterance_is_not_a_move(self):
        ref = at(Phase.DISCUSS)
        with self.assertRaises(ParseError):
            parse_action('{"say": "   "}', ref, ref.next_speaker())

    def test_the_ask_names_every_key_the_parser_reads(self):
        """A key the referee asks for and the salvage path does not know is a
        truncated reply thrown away for nothing."""
        for phase in (Phase.NOMINATE, Phase.DISCUSS, Phase.VOTE,
                      Phase.PROPOSER_DISCARD, Phase.ENACTOR_DISCARD, Phase.POWER):
            ref = at(phase)
            seat = ref.on_clock()[0]
            ask = ref.action_prompt(seat)
            with self.subTest(phase=phase.value):
                self.assertTrue(any(f'"{k}"' in ask for k in ACTION_KEYS))


class TestRandomPlay(unittest.TestCase):
    def test_the_control_policy_is_always_legal_and_the_gate_holds(self):
        for seed in range(15):
            ref = QuorumReferee.new(5, seed=seed, discussion_rounds=1)
            rng = random.Random(seed)
            rec = play_game(ref, {s: RandomPolicy(rng=rng) for s in ref.assignment})
            self.assertEqual(rec.error, "")
            self.assertIn(rec.winner, {Side.MAJORITY.value, Side.MINORITY.value})
            self.assertEqual(rec.fallbacks, 0)

    def test_the_prompt_a_seat_sends_is_the_string_the_gate_audits(self):
        ref = at(Phase.PROPOSER_DISCARD)
        prompt = ref.prompt_for(ref.proposer)
        self.assertIn(ref.render_context(ref.proposer), prompt)
        self.assertIn("discard", prompt)


class TestDrawRecord(unittest.TestCase):
    def test_the_cascade_is_written_down_whole(self):
        ref = QuorumReferee.new(5, seed=4, discussion_rounds=0)
        rng = random.Random(4)
        rec = play_game(ref, {s: RandomPolicy(rng=rng) for s in ref.assignment})
        self.assertTrue(rec.draws)
        for d in rec.draws:
            self.assertEqual(len(d.drew), 3)
            self.assertEqual(len(d.passed), 2)
            # what came out plus the two dropped is exactly what went in
            self.assertEqual(sorted(d.drew),
                             sorted([d.proposer_dropped, d.enactor_dropped,
                                     d.enacted]))
            self.assertIn(d.enacted, d.passed)

    def test_forced_marks_the_event_where_the_office_had_no_other_move(self):
        ref = QuorumReferee.new(5, seed=4, discussion_rounds=0)
        rng = random.Random(4)
        rec = play_game(ref, {s: RandomPolicy(rng=rng) for s in ref.assignment})
        for d in rec.draws:
            sides = {ADVANCES[Card(c)] for c in d.drew}
            self.assertEqual(d.forced, len(sides) == 1)
            if d.forced:
                # the distinction the rung exists for: this enactment is the deck's
                # doing, not the seat's
                self.assertEqual(len(set(d.drew)), 1)

    def test_the_record_never_carries_a_card_into_a_seat_view(self):
        """The decision log is quoted into transcripts, so it says which INDEX was
        dropped and never which card."""
        ref = QuorumReferee.new(5, seed=4, discussion_rounds=0)
        rng = random.Random(4)
        rec = play_game(ref, {s: RandomPolicy(rng=rng) for s in ref.assignment})
        for d in rec.decision_log:
            if "discard" in d.phase:
                self.assertNotIn("writ", d.played.lower())
                self.assertNotIn("charter", d.played.lower())


class _Backend:
    """A scripted backend. ``replies`` is consumed in order; an exception instance
    in the list is raised instead, which is how a transport failure is spelled."""

    model = "scripted"
    seed = None

    def __init__(self, replies):
        self.replies = list(replies)
        self.seen: list[str] = []

    def complete_meta(self, context):
        self.seen.append(context)
        item = self.replies.pop(0) if self.replies else "{}"
        if isinstance(item, Exception):
            raise item
        return item, "scripted"


class TestLLMPolicy(unittest.TestCase):
    def test_an_illegal_move_is_refused_and_the_seat_is_told_why(self):
        ref = at(Phase.NOMINATE)
        seat = ref.proposer
        legal = ref.eligible_nominees()[0]
        backend = _Backend([f'{{"nominate": {seat}}}', f'{{"nominate": {legal}}}'])
        pol = LLMPolicy(backend=backend, retries=2, backoff=0)
        action = pol.act(ref, seat)
        self.assertEqual(action["nominate"], legal)
        self.assertFalse(pol.last_fell_back)
        self.assertEqual(pol.last_rule_refusals, 1)
        self.assertIn("not an eligible nominee", backend.seen[1])

    def test_the_refusal_the_seat_reads_is_the_referees_own(self):
        ref = at(Phase.POWER)
        seat = ref.proposer
        backend = _Backend([f'{{"target": {seat}}}',
                            f'{{"target": {ref.legal_power_targets(seat)[0]}}}'])
        pol = LLMPolicy(backend=backend, retries=2, backoff=0)
        pol.act(ref, seat)
        self.assertIn("not a legal target", backend.seen[1])

    def test_exhausting_the_retries_falls_back_and_counts_it(self):
        ref = at(Phase.VOTE)
        seat = ref.living()[0]
        pol = LLMPolicy(backend=_Backend(["nonsense", "still nonsense", "no"]),
                        retries=2, backoff=0)
        action = pol.act(ref, seat)
        self.assertIn("vote", action)
        self.assertTrue(pol.last_fell_back)
        self.assertEqual(pol.last_upstream, "")

    def test_a_transport_failure_is_not_counted_as_a_rule_refusal(self):
        ref = at(Phase.VOTE)
        seat = ref.living()[0]
        pol = LLMPolicy(backend=_Backend([RuntimeError("429"), '{"vote": true}']),
                        retries=2, backoff=0)
        pol.act(ref, seat)
        self.assertEqual(pol.last_refusals, 1)
        self.assertEqual(pol.last_rule_refusals, 0)
        self.assertFalse(pol.last_fell_back)

    def test_a_fallback_is_counted_in_the_record_and_its_rate(self):
        ref = QuorumReferee.new(5, seed=5, discussion_rounds=0)
        pol = LLMPolicy(backend=_Backend([]), retries=0, backoff=0)
        rec = play_game(ref, {s: pol for s in ref.assignment}, max_turns=40)
        self.assertGreater(rec.fallbacks, 0)
        self.assertEqual(rec.fallback_rate, rec.fallbacks / rec.decisions)


class TestProvenance(unittest.TestCase):
    """A claim or vote the random fallback filed is not a model observation.
    The driver writes the same decision's provenance onto the record it lands,
    and a mixed arm's fallback ceiling is over the MODEL's decisions only."""

    def test_a_fallback_vote_and_claim_carry_true_and_clean_ones_false(self):
        ref = QuorumReferee.new(5, seed=7, discussion_rounds=1)
        broken = LLMPolicy(backend=_Backend([]), retries=0, backoff=0,
                           fallback=RandomPolicy(rng=random.Random(1)))
        policies = {s: RandomPolicy(rng=random.Random(s))
                    for s in ref.assignment}
        policies[ref.proposer] = broken
        rec = play_game(ref, policies)
        self.assertEqual(rec.error, "")
        self.assertTrue(rec.votes)
        self.assertTrue(rec.claims or rec.votes)
        for v in rec.votes:
            decision = next(d for d in rec.decision_log
                            if d.turn == v.turn and d.seat == v.seat
                            and d.phase == "vote")
            self.assertEqual(v.fell_back, decision.fell_back)
        for c in rec.claims:
            decision = next(d for d in rec.decision_log
                            if d.turn == c.turn and d.seat == c.seat)
            self.assertEqual(c.fell_back, decision.fell_back)

    def test_every_decision_knows_whether_a_model_controlled_it(self):
        ref = QuorumReferee.new(5, seed=7, discussion_rounds=1)
        model_seat = ref.proposer
        policies = {s: RandomPolicy(rng=random.Random(s))
                    for s in ref.assignment}
        policies[model_seat] = LLMPolicy(backend=_Backend([]), retries=0,
                                         backoff=0,
                                         fallback=RandomPolicy(
                                             rng=random.Random(1)))
        rec = play_game(ref, policies)
        for d in rec.decision_log:
            self.assertEqual(d.model_controlled, d.seat == model_seat)


class TestClaimEventIndex(unittest.TestCase):
    """The driver records the event the REFEREE returned, never a recomputed
    ``len(rec.draws) - 1``, and one event is claimed at most once per seat."""

    def test_the_entry_event_is_the_referees_and_never_repeats_a_seat(self):
        filed = []

        class Spying(QuorumReferee):
            def record_claim(self, seat, cards):
                rec = super().record_claim(seat, cards)
                filed.append(rec)
                return rec

        ref = Spying.new(5, seed=7, discussion_rounds=1)
        policies = {s: RandomPolicy(rng=random.Random(s), claim_rate=1.0)
                    for s in ref.assignment}
        rec = play_game(ref, policies)
        self.assertEqual(rec.error, "")
        self.assertTrue(rec.claims)
        self.assertEqual([(c.seat, c.event) for c in rec.claims],
                         [(r.seat, r.event) for r in filed])
        keys = [(c.seat, c.event) for c in rec.claims]
        self.assertEqual(len(keys), len(set(keys)))


class TestConsoleSeat(unittest.TestCase):
    def _console(self, typed: str) -> ConsoleBackend:
        return ConsoleBackend(keys=ACTION_KEYS, stdin=io.StringIO(typed),
                              stdout=io.StringIO())

    def test_a_person_plays_through_the_same_prompt_parser_and_loop(self):
        ref = at(Phase.VOTE)
        seat = ref.living()[0]
        backend = self._console("vote y\n")
        pol = LLMPolicy(backend=backend, retries=2, backoff=0)
        action = pol.act(ref, seat)
        self.assertTrue(action["vote"])
        self.assertFalse(pol.last_fell_back)
        # the person was shown this seat's payload, and it is the audited string
        shown = backend.stdout.getvalue()
        self.assertIn(ref.render_context(seat), shown)

    def test_the_console_shows_the_hand_only_to_the_seat_holding_it(self):
        ref = at(Phase.PROPOSER_DISCARD)
        held = ref.proposer
        other = next(s for s in ref.living() if s != held)
        b1 = self._console("discard 0\n")
        LLMPolicy(backend=b1, retries=2, backoff=0).act(ref, held)
        self.assertIn("In your hand", b1.stdout.getvalue())

        ref2 = at(Phase.VOTE)
        b2 = self._console("vote n\n")
        LLMPolicy(backend=b2, retries=2, backoff=0).act(ref2, other)
        self.assertNotIn("In your hand", b2.stdout.getvalue())

    def test_a_typo_costs_no_retry_but_an_illegal_move_does(self):
        ref = at(Phase.NOMINATE)
        seat = ref.proposer
        legal = ref.eligible_nominees()[0]
        backend = self._console(f"wat\nnominate {seat}\nnominate {legal}\n")
        pol = LLMPolicy(backend=backend, retries=2, backoff=0)
        action = pol.act(ref, seat)
        self.assertEqual(action["nominate"], legal)
        # one refusal, from the illegal nomination - the typo never left the console
        self.assertEqual(pol.last_rule_refusals, 1)

    def test_a_second_human_seat_is_refused(self):
        with self.assertRaises(TooManyHumans):
            human_seats("0 1", 5)

    def test_the_demo_withholds_the_sample_view_once_a_person_is_seated(self):
        ref = QuorumReferee.new(5, seed=1, discussion_rounds=0)
        with_human = opening_view(ref, {3})
        self.assertIn("withheld", with_human)
        for s, role in ref.assignment.items():
            self.assertNotIn(ref.theme.role_names[role.key], with_human)
        self.assertIn("private view", opening_view(ref, set()))


class TestAuditRunsInsideTheDriver(unittest.TestCase):
    """The audit's own coverage lives in ``test_audit.py``; what is tested here is
    that the DRIVER runs it - a distinction with teeth, because an audit nothing
    calls passes its own tests forever.

    **Mutation-checked 2026-08-28.** Pinning ``play_game``'s audit call to a dead
    branch turns exactly ONE test red - the first one below - out of 56 in this
    package and 746 in the repo. So this class is the only thing standing between a
    leaking referee and a scored game, and the count is written down because "some
    test would catch it" is the belief this check exists to replace.
    """

    class _LeaksAnotherSeatsRole(QuorumReferee):
        """A referee that names a role it may not. The same mutant appears in
        ``test_audit.py`` against the audit functions directly; here the subject is
        the driver, so the duplication is two different questions rather than one
        asked twice."""

        def render_context(self, seat, include_speech=True):
            base = super().render_context(seat, include_speech)
            other = next(s for s in self.living() if s != seat)
            name = self.theme.role_names[self.assignment[other].key]
            return base + f"\nSeat {other} is the {name}."

    def test_a_leaking_referee_RAISES_rather_than_being_scored(self):
        """The eval lane once ran live models unaudited because a callback was
        opt-in. This is why the audit is on by default and raises."""
        ref = self._LeaksAnotherSeatsRole.new(5, seed=3, discussion_rounds=1)
        rng = random.Random(0)
        with self.assertRaises(LeakDetected):
            play_game(ref, {s: RandomPolicy(rng=rng) for s in ref.assignment})

    def test_the_off_switch_actually_switches_it_off(self):
        """The pair that makes the default meaningful. Without this, a driver that
        ignored ``audit`` entirely would pass every other test here - and the
        signature check below would certify a flag that does nothing.

        It also shows what the default is protecting against: the identical game,
        with the identical leak, runs to a winner and reports a record.
        """
        ref = self._LeaksAnotherSeatsRole.new(5, seed=3, discussion_rounds=1)
        rng = random.Random(0)
        rec = play_game(ref, {s: RandomPolicy(rng=rng) for s in ref.assignment},
                        audit=False)
        self.assertEqual(rec.error, "")
        self.assertTrue(rec.winner)

    def test_audit_off_is_possible_but_never_the_default(self):
        self.assertIs(inspect.signature(play_game).parameters["audit"].default,
                      True)


if __name__ == "__main__":
    unittest.main()


class TestTheCallSizeIsRecorded(unittest.TestCase):
    def test_a_clean_decision_records_the_prompt_and_reply_it_sent(self):
        ref = at(Phase.NOMINATE)
        seat = ref.proposer
        legal = ref.eligible_nominees()[0]
        backend = _Backend([f'{{"nominate": {legal}}}'])
        pol = LLMPolicy(backend=backend, retries=2, backoff=0)
        pol.act(ref, seat)
        self.assertEqual(pol.last_reply_size, len(f'{{"nominate": {legal}}}'))
        self.assertEqual(pol.last_prompt_size, len(backend.seen[-1]))
        self.assertIsNone(pol.last_usage)
