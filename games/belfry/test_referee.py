"""The rules, the night, the day, and gate #1 on a referee that lies on purpose.

Every board here is RIGGED - built seat by seat rather than dealt - because a test
that has to search for a seed where the interesting thing happened is a test that
silently stops testing it the day the deal changes. ``rigged`` is the helper, and
the other test modules in this rung import it.

The audit tests are built as deliberately leaky referee subclasses rather than as
edits to the shipping one, so the check that the gate has teeth is permanent: a
refactor that quietly made the audit vacuous fails these instead of passing them.
"""

from __future__ import annotations

import random
import unittest

from games.belfry.audit import LeakDetected, assert_no_leak, leak_audit
from games.belfry.player import RandomPolicy, play_game
from games.belfry.referee import BelfryReferee, IllegalAction, Phase
from games.belfry.roles import ALL_ROLES, COMPACT, FULL, ROLES, Script
from games.belfry.state import Grimoire, Seat


def rigged(keys: list[str], seed: int = 0, rounds: int = 1,
           script: Script = FULL, max_days: int = 12,
           believes: str = "witness") -> BelfryReferee:
    """A referee over an exact board. No deal, no search for a lucky seed.

    The one thing it has to reproduce from the real deal is the belief the deluded
    seat is given, because a rigged board that let that seat believe the truth
    would make every test about it vacuous - including the audit test whose whole
    subject is that the belief and the truth differ.
    """
    seats = [Seat(index=i, role=ROLES[k], dealt=ROLES[k],
                  believes=ROLES[believes] if k == "sot" else ROLES[k])
             for i, k in enumerate(keys)]
    grim = Grimoire(seats=seats, script=script)
    ref = BelfryReferee(grim=grim, rng=random.Random(seed),
                        discussion_rounds=rounds, max_days=max_days)
    ref.knowledge = {s: [] for s in range(len(keys))}
    ref.entitled = {s: ({s} if seats[s].believes is seats[s].role else set())
                    for s in range(len(keys))}
    ref._begin_night(first=True)
    ref._advance()
    return ref


def default_action(ref: BelfryReferee, turn) -> dict:
    """The dullest legal answer to whatever is being asked. Lets a test drive the
    game to the one decision it cares about without writing the other forty."""
    kind = turn.kind
    legal = ref.legal_targets(turn.seat, kind)
    if kind == "speak":
        return {"say": "."}
    if kind == "nominate":
        return {"nominate": None}
    if kind == "vote":
        return {"vote": False}
    if kind == "divine":
        return {"targets": sorted(legal[:2])}
    if kind == "kill":
        return {"target": next(s for s in legal if s != turn.seat)}
    if kind == "poison":
        # Dull means dull. Poisoning the demon switches off the kill and poisoning
        # the poisoner switches off tomorrow's poisoning, so the default takes the
        # LAST legal seat that is neither - and every board below puts the role
        # under test early, so this default never lands on it.
        demon = ref.grim.demon_seat()
        return {"target": next((s for s in reversed(legal)
                                if s not in (turn.seat, demon)), legal[0])}
    return {"target": legal[0]}


def advance_to(ref: BelfryReferee, kind: str, seat: int | None = None,
               limit: int = 500):
    """Play dull legal moves until the asked-for decision comes up. Returns the
    turn. Raises if the game ends first - a test whose setup never happened must
    fail rather than pass on nothing."""
    for _ in range(limit):
        turn = ref.pending()
        if turn is None:
            raise AssertionError(f"the game ended before any {kind} step")
        if turn.kind == kind and (seat is None or turn.seat == seat):
            return turn
        ref.submit(turn.seat, default_action(ref, turn))
    raise AssertionError(f"no {kind} step within {limit} decisions")


def play_defaults(ref: BelfryReferee, limit: int = 800) -> None:
    for _ in range(limit):
        turn = ref.pending()
        if turn is None:
            return
        ref.submit(turn.seat, default_action(ref, turn))
    raise AssertionError("the game did not end")


#: The standing board for tests that DRIVE the game rather than set state by
#: hand. The last seat is a lightning rod: ``default_action`` poisons the last
#: legal seat, so the role under test is never the one the default switches off.
#: A first-night-only role is the right rod - after night one it does nothing at
#: all, poisoned or not.
FIVE = ["fiend", "venom", "gauge", "warder", "bulwark", "tally"]


class TestTheNightKill(unittest.TestCase):
    def test_the_demon_kills_the_seat_it_chose(self):
        ref = rigged(FIVE)
        advance_to(ref, "kill")
        ref.submit(0, {"target": 2})
        self.assertFalse(ref.grim.seat(2).alive)

    def test_a_protected_seat_survives(self):
        ref = rigged(FIVE)
        advance_to(ref, "protect", seat=3)
        ref.submit(3, {"target": 2})
        advance_to(ref, "kill")
        ref.submit(0, {"target": 2})
        self.assertTrue(ref.grim.seat(2).alive)

    def test_the_seat_the_demon_cannot_kill_survives(self):
        ref = rigged(FIVE)
        advance_to(ref, "kill")
        ref.submit(0, {"target": 4})
        self.assertTrue(ref.grim.seat(4).alive)

    def test_a_poisoned_demon_kills_nobody(self):
        # On the SECOND night: poison lasts until the poisoner's next step, so a
        # first-night poisoning has already worn off by the time anybody is killed.
        ref = rigged(FIVE)
        advance_to(ref, "poison", seat=1)
        ref.submit(1, default_action(ref, ref.pending()))
        advance_to(ref, "poison", seat=1)
        ref.submit(1, {"target": 0})
        advance_to(ref, "kill")
        ref.submit(0, {"target": 2})
        self.assertTrue(ref.grim.seat(2).alive)

    def test_a_poisoned_protector_protects_nobody(self):
        ref = rigged(FIVE)
        advance_to(ref, "poison", seat=1)
        ref.submit(1, default_action(ref, ref.pending()))
        advance_to(ref, "poison", seat=1)
        ref.submit(1, {"target": 3})
        advance_to(ref, "protect", seat=3)
        ref.submit(3, {"target": 2})
        advance_to(ref, "kill")
        ref.submit(0, {"target": 2})
        self.assertFalse(ref.grim.seat(2).alive)

    def test_the_night_s_deaths_are_announced_at_dawn_and_not_before(self):
        ref = rigged(FIVE)
        advance_to(ref, "kill")
        before = [text for tag, text in ref.public_events]
        self.assertNotIn("Seat 2 is dead.", before)
        ref.submit(0, {"target": 2})
        said = [text for tag, text in ref.public_events if tag == "event"]
        self.assertTrue(any(line.startswith("Dawn.") and "Seat 2" in line
                            for line in said))
        # Announced once, at dawn, and never as a bare death during the night.
        self.assertNotIn("Seat 2 is dead.", said)

    def test_poison_is_cleared_at_the_top_of_the_next_night(self):
        ref = rigged(FIVE)
        advance_to(ref, "poison", seat=1)
        ref.submit(1, {"target": 2})
        self.assertTrue(ref.grim.seat(2).poisoned)
        advance_to(ref, "poison", seat=1)          # the following night
        self.assertFalse(ref.grim.seat(2).poisoned)


class TestTheDemonChangingHands(unittest.TestCase):
    def test_a_demon_that_kills_itself_passes_the_role_to_a_minion(self):
        ref = rigged(FIVE)
        advance_to(ref, "kill")
        ref.submit(0, {"target": 0})
        self.assertFalse(ref.grim.seat(0).alive)
        self.assertEqual(ref.grim.seat(1).role.key, "fiend")
        self.assertIsNone(ref.winner)

    def test_the_successor_is_told_and_is_entitled_to_itself(self):
        ref = rigged(FIVE)
        advance_to(ref, "kill")
        ref.submit(0, {"target": 0})
        self.assertIn(1, ref.entitled[1])
        self.assertIn("You are the demon now.",
                      [r.text for r in ref.knowledge[1]])

    def test_the_heir_takes_over_an_executed_demon_on_a_big_table(self):
        ref = rigged(["fiend", "heir", "gauge", "witness", "bulwark",
                      "warder", "tally"])
        ref.block = 0
        ref._dusk()
        self.assertEqual(ref.grim.seat(1).role.key, "fiend")
        self.assertIsNone(ref.winner)

    def test_the_heir_does_not_take_over_below_five_alive(self):
        ref = rigged(["fiend", "heir", "gauge", "witness", "bulwark"])
        for seat in (3, 4):
            ref.grim.seat(seat).alive = False
        ref.block = 0
        ref._dusk()
        self.assertEqual(ref.winner, "good")

    def test_executing_the_demon_with_no_successor_ends_the_game(self):
        ref = rigged(FIVE)
        ref.block = 0
        ref._dusk()
        self.assertEqual(ref.winner, "good")


class TestTheDay(unittest.TestCase):
    def test_a_seat_may_nominate_once(self):
        ref = rigged(FIVE)
        turn = advance_to(ref, "nominate")
        ref.submit(turn.seat, {"nominate": (turn.seat + 1) % 5})
        self.assertTrue(ref.grim.seat(turn.seat).nominated_today)

    def test_a_seat_may_not_be_nominated_twice_in_a_day(self):
        ref = rigged(FIVE)
        first = advance_to(ref, "nominate")
        ref.submit(first.seat, {"nominate": 2})
        second = advance_to(ref, "nominate")
        with self.assertRaises(IllegalAction):
            ref.submit(second.seat, {"nominate": 2})

    def test_a_nomination_opens_a_vote_for_everyone_with_a_vote(self):
        ref = rigged(FIVE)
        turn = advance_to(ref, "nominate")
        ref.submit(turn.seat, {"nominate": 2})
        self.assertIs(ref.phase, Phase.VOTE)
        self.assertEqual(sorted(ref.eligible_voters(2)),
                         sorted(ref.grim.alive_seats()))

    def test_a_nomination_that_reaches_half_the_living_seats_stands(self):
        ref = rigged(FIVE)
        turn = advance_to(ref, "nominate")
        ref.submit(turn.seat, {"nominate": 2})
        while ref.phase is Phase.VOTE:
            t = ref.pending()
            ref.submit(t.seat, {"vote": True})
        self.assertEqual(ref.block, 2)

    def test_a_nomination_short_of_the_bar_does_not_stand(self):
        ref = rigged(FIVE)
        turn = advance_to(ref, "nominate")
        ref.submit(turn.seat, {"nominate": 2})
        first = True
        while ref.phase is Phase.VOTE:
            t = ref.pending()
            ref.submit(t.seat, {"vote": first})
            first = False
        self.assertIsNone(ref.block)

    def test_a_tie_on_the_highest_count_leaves_nobody_standing(self):
        ref = rigged(FIVE)
        n1 = advance_to(ref, "nominate")
        ref.submit(n1.seat, {"nominate": 2})
        while ref.phase is Phase.VOTE:
            t = ref.pending()
            ref.submit(t.seat, {"vote": True})
        self.assertEqual(ref.block, 2)
        n2 = advance_to(ref, "nominate")
        ref.submit(n2.seat, {"nominate": 3})
        while ref.phase is Phase.VOTE:
            t = ref.pending()
            ref.submit(t.seat, {"vote": True})
        self.assertIsNone(ref.block)

    def test_the_dead_keep_their_voice_and_one_vote(self):
        ref = rigged(FIVE)
        advance_to(ref, "kill")
        ref.submit(0, {"target": 2})
        self.assertIn(2, ref.eligible_voters(3))
        self.assertIn(2, ref._speak_order)
        turn = advance_to(ref, "nominate")
        ref.submit(turn.seat, {"nominate": 3})
        while ref.phase is Phase.VOTE:
            t = ref.pending()
            ref.submit(t.seat, {"vote": True})
        self.assertFalse(ref.grim.seat(2).ghost_vote)
        self.assertNotIn(2, ref.eligible_voters(4))

    def test_a_ghost_vote_against_costs_nothing(self):
        ref = rigged(FIVE)
        advance_to(ref, "kill")
        ref.submit(0, {"target": 2})
        turn = advance_to(ref, "nominate")
        ref.submit(turn.seat, {"nominate": 3})
        while ref.phase is Phase.VOTE:
            t = ref.pending()
            ref.submit(t.seat, {"vote": t.seat != 2})
        self.assertTrue(ref.grim.seat(2).ghost_vote)

    def test_a_dead_seat_cannot_nominate(self):
        ref = rigged(FIVE)
        advance_to(ref, "kill")
        ref.submit(0, {"target": 2})
        seats = []
        while ref.phase is Phase.NOMINATE:
            t = ref.pending()
            seats.append(t.seat)
            ref.submit(t.seat, {"nominate": None})
        self.assertNotIn(2, seats)


class TestTheValet(unittest.TestCase):
    BOARD = ["fiend", "venom", "valet", "gauge", "bulwark", "tally"]

    def test_a_valet_vote_without_its_master_does_not_count(self):
        ref = rigged(self.BOARD)
        advance_to(ref, "master", seat=2)
        ref.submit(2, {"target": 4})
        turn = advance_to(ref, "nominate")
        ref.submit(turn.seat, {"nominate": 3})
        while ref.phase is Phase.VOTE:
            t = ref.pending()
            ref.submit(t.seat, {"vote": t.seat != 4})
        counted = [text for tag, text in ref.public_events
                   if tag == "event" and text.startswith("Votes for")][-1]
        self.assertNotIn("2", counted.split("(")[1])

    def test_a_valet_vote_with_its_master_counts(self):
        ref = rigged(self.BOARD)
        advance_to(ref, "master", seat=2)
        ref.submit(2, {"target": 4})
        turn = advance_to(ref, "nominate")
        ref.submit(turn.seat, {"nominate": 3})
        while ref.phase is Phase.VOTE:
            t = ref.pending()
            ref.submit(t.seat, {"vote": True})
        counted = [text for tag, text in ref.public_events
                   if tag == "event" and text.startswith("Votes for")][-1]
        self.assertIn("2", counted.split("(")[1])

    def test_the_dropped_vote_is_not_announced(self):
        """The seat whose vote it was knows why - its own render says so. Nobody
        else learns anything, which is the rule at a table where that seat simply
        keeps its hand down."""
        ref = rigged(self.BOARD)
        advance_to(ref, "master", seat=2)
        ref.submit(2, {"target": 4})
        turn = advance_to(ref, "nominate")
        ref.submit(turn.seat, {"nominate": 3})
        while ref.phase is Phase.VOTE:
            t = ref.pending()
            ref.submit(t.seat, {"vote": t.seat != 4})
        public = " ".join(text for tag, text in ref.public_events
                          if tag == "event")
        self.assertNotIn("did not count", public)


class TestTheTriggeredRoles(unittest.TestCase):
    def test_the_dying_oracle_wakes_and_learns_a_role(self):
        ref = rigged(["fiend", "venom", "oracle", "gauge", "bulwark", "tally"])
        advance_to(ref, "kill")
        ref.submit(0, {"target": 2})
        turn = ref.pending()
        self.assertEqual((turn.seat, turn.kind), (2, "ravenkeep"))
        ref.submit(2, {"target": 0})
        self.assertIn("Seat 0 is the Fiend.",
                      [r.text for r in ref.knowledge[2]])

    def test_a_martyr_nomination_by_a_townsfolk_executes_the_nominator(self):
        ref = rigged(["fiend", "venom", "martyr", "gauge", "bulwark", "tally"])
        turn = advance_to(ref, "nominate", seat=3)
        ref.submit(3, {"nominate": 2})
        self.assertFalse(ref.grim.seat(3).alive)
        self.assertTrue(ref.grim.seat(2).alive)

    def test_a_trigger_execution_records_that_no_vote_carried_it(self):
        """The day-1 instrument control reads this field. A trigger execution
        names the nominator and fires only on a townsfolk one, so it is good with
        probability 1 while the scorer prices every execution against the board
        rate - pooled, that read as the random policy missing chance."""
        ref = rigged(["fiend", "venom", "martyr", "gauge", "bulwark", "tally"])
        advance_to(ref, "nominate", seat=3)
        ref.submit(3, {"nominate": 2})
        self.assertEqual([(e.seat, e.by_vote) for e in ref.executions],
                         [(3, False)])

    def test_an_execution_the_table_voted_up_says_so(self):
        ref = rigged(["fiend", "venom", "martyr", "gauge", "bulwark", "tally"])
        ref.block = 2
        ref._dusk()
        self.assertEqual([(e.seat, e.by_vote) for e in ref.executions],
                         [(2, True)])

    def test_a_martyr_nomination_by_an_evil_seat_is_an_ordinary_nomination(self):
        ref = rigged(["fiend", "venom", "martyr", "gauge", "bulwark", "tally"])
        turn = advance_to(ref, "nominate", seat=0)
        ref.submit(0, {"nominate": 2})
        self.assertTrue(ref.grim.seat(0).alive)
        self.assertIs(ref.phase, Phase.VOTE)

    def test_the_trigger_fires_once_per_game(self):
        ref = rigged(["fiend", "venom", "martyr", "gauge", "bulwark", "tally"])
        advance_to(ref, "nominate", seat=3)
        ref.submit(3, {"nominate": 2})
        turn = advance_to(ref, "nominate", seat=4)
        ref.submit(4, {"nominate": 2})
        self.assertTrue(ref.grim.seat(4).alive)

    def test_executing_the_seat_that_must_not_be_executed_loses_the_game(self):
        ref = rigged(["fiend", "venom", "pilgrim", "gauge", "bulwark"])
        ref.block = 2
        ref._dusk()
        self.assertEqual(ref.winner, "evil")

    def test_a_poisoned_pilgrim_is_just_an_execution(self):
        ref = rigged(["fiend", "venom", "pilgrim", "gauge", "bulwark"])
        ref.grim.seat(2).poisoned = True
        ref.block = 2
        ref._dusk()
        self.assertIsNone(ref.winner)


class TestThePublicDayPower(unittest.TestCase):
    BOARD = ["fiend", "venom", "duelist", "gauge", "bulwark", "tally"]

    def test_the_real_holder_kills_the_demon(self):
        ref = rigged(self.BOARD)
        turn = advance_to(ref, "speak", seat=2)
        ref.submit(2, {"say": "I name it.", "slay": 0})
        self.assertFalse(ref.grim.seat(0).alive)
        self.assertEqual(ref.winner, "good")

    def test_any_seat_may_try_and_nothing_happens(self):
        ref = rigged(self.BOARD)
        turn = advance_to(ref, "speak", seat=3)
        ref.submit(3, {"say": "I name it.", "slay": 0})
        self.assertTrue(ref.grim.seat(0).alive)
        self.assertIn("Nothing happens.",
                      [t for _, t in ref.public_events])

    def test_the_public_record_reads_the_same_either_way(self):
        """A power only its true holder could invoke would make every invocation a
        proof of the role. The announcement has to be identical."""
        lines = []
        for actor in (2, 3):
            ref = rigged(self.BOARD)
            advance_to(ref, "speak", seat=actor)
            ref.submit(actor, {"say": ".", "slay": 1})
            lines.append([t for tag, t in ref.public_events
                          if tag == "event" and "calls seat" in t][-1])
        self.assertEqual(lines[0].replace("Seat 2", "Seat X"),
                         lines[1].replace("Seat 3", "Seat X"))

    def test_the_power_is_spent_once(self):
        ref = rigged(self.BOARD)
        advance_to(ref, "speak", seat=3)
        ref.submit(3, {"say": ".", "slay": 1})
        advance_to(ref, "speak", seat=3)
        with self.assertRaises(IllegalAction):
            ref.submit(3, {"say": ".", "slay": 2})

    def test_a_poisoned_holder_kills_nobody(self):
        ref = rigged(self.BOARD)
        advance_to(ref, "poison", seat=1)
        ref.submit(1, {"target": 2})
        advance_to(ref, "speak", seat=2)
        ref.submit(2, {"say": ".", "slay": 0})
        self.assertTrue(ref.grim.seat(0).alive)


class TestWinConditions(unittest.TestCase):
    def test_two_alive_with_the_demon_is_an_evil_win(self):
        ref = rigged(FIVE)
        for seat in (2, 3, 4, 5):
            ref.grim.seat(seat).alive = False
        ref._check_win()
        self.assertEqual(ref.winner, "evil")

    def test_the_speaker_wins_at_three_with_no_execution(self):
        ref = rigged(["fiend", "venom", "speaker", "gauge", "bulwark"])
        for seat in (3, 4):
            ref.grim.seat(seat).alive = False
        ref._dusk()
        self.assertEqual(ref.winner, "good")

    def test_a_poisoned_speaker_does_not_win(self):
        ref = rigged(["fiend", "venom", "speaker", "gauge", "bulwark"])
        for seat in (3, 4):
            ref.grim.seat(seat).alive = False
        ref.grim.seat(2).poisoned = True
        ref._dusk()
        self.assertNotEqual(ref.winner, "good")

    def test_the_day_bound_ends_the_game_with_no_winner(self):
        """The structural bound, and it has to be reachable: a referee whose only
        exit is a win condition hangs the first time one of them is wrong, and a
        hang is not a test failure anybody can read."""
        ref = rigged(["fiend", "venom", "gauge", "bulwark", "bulwark"],
                     max_days=2)
        play_defaults(ref)
        self.assertIsNone(ref.winner)
        self.assertIn("bound", ref.reason)


class TestFalseInformation(unittest.TestCase):
    def test_a_poisoned_seat_is_told_a_false_count(self):
        ref = rigged(["fiend", "venom", "gauge", "warder", "bulwark", "tally"])
        advance_to(ref, "poison", seat=1)
        ref.submit(1, {"target": 2})
        line = [r for r in ref.knowledge[2] if "neighbours" in r.text][-1]
        self.assertFalse(line.truthful)

    def test_the_deluded_seat_never_reads_its_own_role(self):
        ref = rigged(["fiend", "venom", "sot", "gauge", "bulwark", "tally"])
        rendered = ref.render_context(2).lower()
        self.assertNotIn("you are the sot", rendered)
        self.assertIn("sot", ref.preamble().lower())   # the script still lists it

    def test_a_false_reveal_never_states_a_true_association(self):
        """The gate #1 requirement behind ``night._other_role``. Across many
        boards: every non-truthful reveal that names one seat and one role names a
        role that seat does not hold and does not register as."""
        checked = 0
        for seed in range(40):
            # The board-watcher, poisoned: the one role that produces single-seat
            # associations by the handful, so the property has a sample to hold on.
            ref = rigged(["fiend", "venom", "mimic", "gauge", "warder",
                          "bulwark", "witness"], seed=seed)
            advance_to(ref, "poison", seat=1)
            ref.submit(1, {"target": 2})
            play_defaults(ref)
            for viewer, reveals in ref.knowledge.items():
                for r in reveals:
                    if r.truthful or not r.role or len(r.seats) != 1:
                        continue
                    checked += 1
                    seat = r.seats[0]
                    self.assertNotEqual(r.role, ref.grim.role_of(seat).key)
        self.assertGreater(checked, 0, "no false association was ever built")


class LeaksAnotherSeat(BelfryReferee):
    """A referee that names a seat's role in a render nobody was entitled to."""

    def seat_lines(self, seat: int, include_speech: bool = True) -> str:
        victim = (seat + 1) % self.n
        return (super().seat_lines(seat, include_speech) + "\n  "
                + self.reveal_forms(victim, self.grim.role_of(victim).key)[0]
                + ".")


class LeaksTheAsk(BelfryReferee):
    """A referee that lets a role name into the question. The ask is bytes leaving
    for the model like any other, which is why the audit reads it too."""

    def ask(self, seat: int) -> str:
        victim = (seat + 1) % self.n
        return (super().ask(seat) + " (For reference, "
                + self.reveal_forms(victim, self.grim.role_of(victim).key)[0]
                + ".)")


class NamesTheViewerToItself(BelfryReferee):
    """The self-leak in the THIRD person - the shape the first scan could not see
    while it excluded the viewer. A referee that writes a seat's own role into that
    seat's render in `reveal_forms`' phrasing, which is what a refreshed or
    mis-addressed reveal looks like."""

    def seat_lines(self, seat: int, include_speech: bool = True) -> str:
        return (super().seat_lines(seat, include_speech)
                + "\n  "
                + self.reveal_forms(seat, self.grim.role_of(seat).key)[0] + ".")


class LeaksItsOwnTruth(BelfryReferee):
    """The bug this rung shares with `changeling`: a referee that renders what a
    seat IS where its belief was due."""

    def self_line(self, seat: int) -> str:
        row = self.grim.seat(seat)
        return f"You are seat {seat}. You are the {row.role.display}."


def leaky(cls, keys, **kw) -> BelfryReferee:
    ref = rigged(keys, **kw)
    ref.__class__ = cls
    return ref


class TestGateOne(unittest.TestCase):
    def test_a_full_game_of_every_size_leaks_nothing(self):
        for n in (5, 6, 7, 8, 9, 10, 11, 12):
            for script in (FULL, COMPACT):
                if script is COMPACT and n > 9:
                    continue
                for seed in range(3):
                    ref = BelfryReferee.new(n, seed=seed, script=script)
                    rng = random.Random(seed)
                    rec = play_game(
                        ref, {s: RandomPolicy(rng) for s in range(n)})
                    self.assertIsNone(rec.error, (n, script.name, seed))
                    self.assertEqual(leak_audit(ref), [])

    def test_the_audit_catches_an_unentitled_reveal(self):
        ref = leaky(LeaksAnotherSeat, FIVE)
        self.assertTrue(leak_audit(ref))
        with self.assertRaises(LeakDetected):
            assert_no_leak(ref)

    def test_the_audit_catches_a_seat_being_named_to_itself(self):
        """The first scan excluded the viewer until 2026-09-02, so this exact leak
        - a seat's own role written into its own render in the third person - had
        no scan looking for it. Latent on the shipping referee, which is why the
        mutant is the only thing that can prove the scan works.

        The rig seats a seat that is WRONG about itself, and that is the whole
        test: naming a seat its own role is not a leak for the seats entitled to
        it, so a rig where everyone is right about themselves passes this mutant
        honestly and proves nothing."""
        ref = leaky(NamesTheViewerToItself,
                    ["fiend", "venom", "sot", "gauge", "bulwark", "tally"])
        self.assertTrue([s for s in range(ref.n) if s not in ref.entitled[s]],
                        "this rig seats nobody wrong about itself")
        found = leak_audit(ref)
        self.assertTrue(found, "a seat named to itself passed the audit")
        with self.assertRaises(LeakDetected):
            assert_no_leak(ref)

    def test_the_audit_catches_a_role_name_in_the_ask(self):
        ref = leaky(LeaksTheAsk, FIVE)
        self.assertTrue(leak_audit(ref))

    def test_the_audit_catches_a_deluded_seat_being_told_the_truth(self):
        ref = leaky(LeaksItsOwnTruth, ["fiend", "venom", "sot", "gauge",
                                       "bulwark", "tally"])
        leaks = [x for x in leak_audit(ref) if x[0] == 2 and x[1] == 2]
        self.assertTrue(leaks)

    def test_a_seat_that_knows_itself_is_not_reported_as_leaking_to_itself(self):
        ref = rigged(FIVE)
        self.assertEqual(leak_audit(ref), [])

    def test_the_board_watcher_is_entitled_to_every_seat(self):
        """The widest entitlement in the game, and the audit has to be a check the
        referee can pass while it holds."""
        ref = rigged(["fiend", "mimic", "gauge", "warder", "bulwark", "tally"])
        self.assertEqual(ref.entitled[1], {0, 1, 2, 3, 4, 5})
        self.assertEqual(leak_audit(ref), [])

    def test_every_single_seat_reveal_carries_its_canonical_form(self):
        """The promise ``reveal_forms`` makes. A reveal that stated the same fact
        in words the form does not match would be invisible to the audit - true,
        unentitled, and unreported."""
        checked = 0
        for seed in range(25):
            ref = BelfryReferee.new(9, seed=seed)
            rng = random.Random(seed)
            play_game(ref, {s: RandomPolicy(rng) for s in range(9)})
            for reveals in ref.knowledge.values():
                for r in reveals:
                    if not r.role or len(r.seats) != 1:
                        continue
                    if r.text == "You are the demon now.":
                        continue
                    checked += 1
                    form = f"seat {r.seats[0]} is the {ROLES[r.role].display}"
                    self.assertIn(form.lower(), r.text.lower(), r.text)
        self.assertGreater(checked, 20)

    def test_a_two_seat_reveal_carries_no_single_seat_form(self):
        """The collision that fired on the first game ever played here. Written the
        other way round, "one of seat 3 and seat 5 is the Mortician" contains seat
        5's secret verbatim."""
        for seed in range(60):
            ref = BelfryReferee.new(9, seed=seed)
            for reveals in ref.knowledge.values():
                for r in reveals:
                    if len(r.seats) != 2 or not r.role:
                        continue
                    for seat in r.seats:
                        form = f"seat {seat} is the {ROLES[r.role].display}"
                        self.assertNotIn(form.lower(), r.text.lower(), r.text)


class TestThePayload(unittest.TestCase):
    def test_the_preamble_is_byte_identical_for_every_seat(self):
        ref = BelfryReferee.new(7, seed=3)
        first = ref.preamble()
        for seat in range(ref.n):
            self.assertEqual(ref.render_context(seat).split("\n\n")[0],
                             first.split("\n\n")[0])

    def test_the_preamble_names_every_role_on_the_script(self):
        """A seat that cannot read an ability cannot evaluate a claim to hold it."""
        ref = BelfryReferee.new(7, seed=1, script=COMPACT)
        text = ref.preamble()
        for role in COMPACT.roles:
            self.assertIn(role.display, text)

    def test_the_preamble_ties_no_role_to_a_seat(self):
        ref = BelfryReferee.new(7, seed=1)
        text = ref.preamble().lower()
        for seat in range(ref.n):
            for role in ALL_ROLES:
                self.assertNotIn(f"seat {seat} is the {role.display}".lower(),
                                 text)

    def test_the_public_record_never_names_a_role(self):
        for seed in range(15):
            ref = BelfryReferee.new(9, seed=seed)
            rng = random.Random(seed)
            play_game(ref, {s: RandomPolicy(rng) for s in range(9)})
            public = " ".join(t for tag, t in ref.public_events
                              if tag == "event")
            for role in ALL_ROLES:
                self.assertNotIn(role.display, public, role.key)

    def test_a_seat_off_the_clock_has_no_ask(self):
        ref = rigged(FIVE)
        turn = ref.pending()
        other = next(s for s in range(5) if s != turn.seat)
        with self.assertRaises(IllegalAction):
            ref.ask(other)


class TestDeterminism(unittest.TestCase):
    def test_the_same_seed_plays_the_same_game(self):
        def run(seed):
            ref = BelfryReferee.new(7, seed=seed)
            rng = random.Random(seed)
            rec = play_game(ref, {s: RandomPolicy(rng) for s in range(7)})
            return rec.winner, rec.reason, rec.dealt, rec.final, rec.days

        self.assertEqual(run(42), run(42))
        self.assertNotEqual(run(42)[2], run(43)[2])


if __name__ == "__main__":
    unittest.main()
