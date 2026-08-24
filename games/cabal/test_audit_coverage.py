"""Gate #1, exhaustively: every phase, every theme, every acting seat.

The other leak tests audit whatever state a game happens to reach. That is not a
guarantee - a role name added to one phase's ask string (say, "name the seer") is
invisible until a test walks that phase in the skin whose display name collides.
So this file drives the referee to each phase deliberately and audits the full
outgoing payload, ``prompt_for`` included, in all three skins.

It also pins the driver's own guarantee: ``play_game`` audits by default, and a
planted leak makes the game raise rather than be scored.
"""

import random
import unittest

from games.cabal.audit import LeakDetected, assert_no_leak, leak_audit
from games.cabal.player import RandomPolicy, play_game
from games.cabal.referee import CabalReferee, Phase
from games.cabal.roles import THEMES


def drive_to(phase: Phase, theme, seed: int = 0) -> CabalReferee:
    """A referee parked in the requested phase, under the requested skin."""
    ref = CabalReferee.new(5, seed=seed, theme=theme, discussion_rounds=1)
    if phase is Phase.PROPOSE:
        return ref
    ref.propose(ref.leader, sorted(ref.assignment)[:ref.setup.team_sizes[0]])
    if phase is Phase.DISCUSS:
        return ref
    for seat in ref.speaking_order():
        ref.speak(seat, "a word from me")
    if phase is Phase.VOTE:
        return ref
    ref.vote({s: True for s in ref.assignment})
    if phase is Phase.MISSION:
        return ref
    # three clean missions to reach the endgame strike
    ref.mission({s: False for s in ref.proposal})
    while ref.phase is not Phase.HUNT:
        size = ref.setup.team_sizes[ref.mission_index]
        ref.propose(ref.leader, sorted(ref.assignment)[:size])
        for seat in ref.speaking_order():
            ref.speak(seat, "a word from me")
        ref.vote({s: True for s in ref.assignment})
        ref.mission({s: False for s in ref.proposal})
    return ref


class TestEveryPhaseInEverySkin(unittest.TestCase):
    PHASES = [Phase.PROPOSE, Phase.DISCUSS, Phase.VOTE, Phase.MISSION, Phase.HUNT]

    def test_no_ask_or_view_names_a_foreign_role(self):
        for theme_name, theme in THEMES.items():
            for phase in self.PHASES:
                for seed in range(6):
                    ref = drive_to(phase, theme, seed)
                    self.assertIs(ref.phase, phase)
                    self.assertEqual(
                        leak_audit(ref), [],
                        f"leak in {phase.value} under {theme_name} (seed {seed})",
                    )

    def test_the_audit_reads_the_ask_not_only_the_view(self):
        """Guards the guard, second half. The phase sweep above only catches a role
        name planted in an ask while the audit still READS asks - drop that and the
        sweep goes quiet. So plant the leak in the ask itself and require a hit.
        """
        for phase in self.PHASES:
            ref = drive_to(phase, THEMES["plain"])
            acting = ref.acting_seats()[0]
            entitled = {k.seat for k in ref.entitled_knowledge(acting)}
            victim = next(s for s in sorted(ref.assignment)
                          if s != acting and s not in entitled)
            term = ref.assignment[victim].key
            real_ask = ref.action_prompt
            ref.action_prompt = (
                lambda seat, _r=real_ask, _v=victim, _t=term:
                f"{_r(seat)}\n(seat {_v} is the {_t})"
            )
            self.assertIn(
                (acting, victim, term), leak_audit(ref),
                f"audit missed a leak planted in the {phase.value} ask",
            )

    def test_every_phase_actually_asks_someone(self):
        """Guards the guard: an audit over an empty acting-seat set proves nothing,
        so each phase must put at least one seat on the clock."""
        for phase in self.PHASES:
            ref = drive_to(phase, THEMES["plain"])
            self.assertTrue(ref.acting_seats(), f"{phase.value} asks nobody")
            for seat in ref.acting_seats():
                self.assertTrue(ref.prompt_for(seat).strip())


class TestDriverAuditsByDefault(unittest.TestCase):
    def test_a_planted_leak_stops_the_game(self):
        """The driver must refuse to score a leaking game, not merely notice one."""
        ref = CabalReferee.new(5, seed=1, discussion_rounds=1)
        victim = next(s for s, r in ref.assignment.items() if r.key == "mimic")
        ref._event(f"clerical note: seat {victim} is the mimic")
        pol = RandomPolicy(rng=random.Random(1))
        with self.assertRaises(LeakDetected):
            play_game(ref, {s: pol for s in ref.assignment})

    def test_the_same_game_is_scored_when_the_leak_is_absent(self):
        ref = CabalReferee.new(5, seed=1, discussion_rounds=1)
        pol = RandomPolicy(rng=random.Random(1))
        rec = play_game(ref, {s: pol for s in ref.assignment})
        self.assertIn(rec.winner, ("good", "evil"))

    def test_assert_no_leak_is_silent_on_a_clean_board(self):
        assert_no_leak(CabalReferee.new(5, seed=2, discussion_rounds=1))


if __name__ == "__main__":
    unittest.main()
