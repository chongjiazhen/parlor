"""Gate #1, exhaustively: every phase, every theme, every acting seat.

The other leak tests audit whatever state a game happens to reach. That is not a
guarantee - a role name added to one phase's ask string (say, "name the seer") is
invisible until a test walks that phase in the skin whose display name collides.
So this file drives the referee to each phase deliberately and audits the full
outgoing payload, ``prompt_for`` included, in every registered skin - the sweep
reads ``THEMES``, so a skin added later is covered the day it lands.

It also pins the driver's own guarantee: ``play_game`` audits by default, and a
planted leak makes the game raise rather than be scored.
"""

import random
import unittest

from games.cabal.audit import LeakDetected, assert_no_leak, leak_audit
from games.cabal.player import RandomPolicy, play_game
from games.cabal.referee import CabalReferee, Phase
from games.cabal.roles import ALL_ROLES, THEMES


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


class TestEverySkinIsNamedAndCollisionFree(unittest.TestCase):
    """The two properties a skin must have, checked as data rather than by playing.

    The phase sweep above can only audit roles a shipped setup actually deals, so
    it says nothing about the variant evils - which is exactly when a missing name
    or a colliding one would first bite, on the run that introduces them.
    """

    def test_every_skin_names_every_role(self):
        for name, theme in THEMES.items():
            for role in ALL_ROLES:
                self.assertIn(role.key, theme.role_names, f"{name} does not name {role.key}")

    def test_no_two_roles_in_a_skin_collide_by_substring(self):
        """`find_leaks` matches substrings, so one role's term inside another's
        makes a legitimate reveal read as a leak - the plain-skin "Loyalist" case,
        one rung further out. The invariant's remedy is to rename, so this fails
        loudly at the theme rather than quietly at the audit.
        """
        for name, theme in THEMES.items():
            terms = {r.key: [r.key.lower(), theme.role_names[r.key].lower()]
                     for r in ALL_ROLES}
            for key, mine in terms.items():
                for other, theirs in terms.items():
                    if key == other:
                        continue
                    for a in mine:
                        for b in theirs:
                            self.assertNotIn(a, b, f"{name}: {key} term '{a}' hides in {other}")

    def test_no_blurb_contains_a_role_term(self):
        """A blurb reaches every seat, so a role term inside it reports a leak on
        every context the referee renders - in a skin, not in the engine, which is
        the hardest place to look for it."""
        for name, theme in THEMES.items():
            blurb = theme.blurb.lower()
            if not blurb:
                continue
            for role in ALL_ROLES:
                for term in (role.key, theme.role_names[role.key]):
                    self.assertNotIn(term.lower(), blurb, f"{name} blurb names {role.key}")


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
