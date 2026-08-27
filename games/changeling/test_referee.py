"""The day, and gate #1 for a game where a seat's own card is a secret from it.

The audit tests here are built as deliberately leaky referees rather than as file
mutations, so the check that the gate has teeth is permanent: a later refactor that
quietly makes the audit vacuous fails these instead of passing them.
"""

from __future__ import annotations

import unittest
from dataclasses import replace

from core.observability import Knowledge
from games.changeling.night import centre_ref, resolve_night
from games.changeling.referee import ChangelingReferee, IllegalAction, Phase
from games.changeling.roles import (BYSTANDER, DECEIVED, PACK, SETUP_5, SPOTTER,
                                    SWAPPER, SWITCHER, THEME_FOLK, THEME_PLAIN,
                                    Act, Side, THEMES)


def find_diverged_seed(limit: int = 200) -> int:
    """A seed whose night actually diverged somebody. Tests about divergence must
    run on a game that has some, or they pass on the empty set."""
    for seed in range(limit):
        ref = ChangelingReferee.new(5, seed=seed)
        if ref.night.diverged():
            return seed
    raise AssertionError("no diverged night in range - the night engine is broken")


class LeaksOwnTruth(ChangelingReferee):
    """The bug this rung exists to catch: a referee that renders what a seat HOLDS
    where its belief was due. Passes every `cabal`-shaped test."""

    def self_line(self, seat: int) -> str:
        card = self.holds(seat)
        return (f"You are seat {seat}. You went to sleep as the "
                f"{self.theme.card_names[card.key]} "
                f"({self.theme.side_names[card.side]}).")


class LeaksAnotherSeat(ChangelingReferee):
    """A referee that names a seat's dawn card in a reveal nobody was entitled to."""

    def seat_lines(self, seat: int, include_speech: bool = True) -> str:
        base = super().seat_lines(seat, include_speech)
        victim = (seat + 1) % self.n
        return base + "\n  - " + self.reveal_forms(victim, self.holds(victim).key)[0]


class TestPreambleIsSeatInvariant(unittest.TestCase):
    """The preamble names every card in the deck, so it is excluded from the audit.
    That exclusion is only sound while it is identical for every seat."""

    def test_every_seat_gets_byte_identical_preamble(self):
        ref = ChangelingReferee.new(5, seed=find_diverged_seed())
        texts = {ref.preamble() for s in range(ref.n)}
        self.assertEqual(len(texts), 1)

    def test_preamble_does_not_mention_any_seat_number(self):
        """A seat fact interpolated in here would ride straight past the audit."""
        ref = ChangelingReferee.new(5, seed=3)
        self.assertNotIn("Seat ", ref.preamble())
        self.assertNotIn("You are", ref.preamble())


class TestThemedCentre(unittest.TestCase):
    """The face-down pile is the one piece of furniture a skin renames, and it is
    named in three different places: the deck listing's power clauses, the
    face-down line under them, and a centre reveal in a seat's own night. A skin
    that renames two of the three describes two different tables."""

    SKINNED = replace(THEME_FOLK, name="test-centre", centre_name="sideboard")

    def test_the_shipping_skins_render_the_bytes_they_rendered_before(self):
        """Adding the field must not move the default face - a preamble edit is a
        prompt edit, and changeling has a 200-game run queued on this one."""
        for theme in (THEME_FOLK, THEME_PLAIN):
            ref = ChangelingReferee.new(5, seed=3, theme=theme)
            text = ref.preamble()
            self.assertIn("in hands or in the centre,", text)
            self.assertIn("lie face down in the centre and belong to nobody.", text)
            self.assertIn("or at two centre cards", text)
            self.assertIn("for a centre card without looking", text)

    def test_a_renamed_centre_reaches_every_place_the_word_appears(self):
        """The guard that earns its keep: it fails on a place missed today and on
        a place added tomorrow, which no amount of reading the renderer catches."""
        for seed in range(30):
            ref = ChangelingReferee.new(5, seed=seed, theme=self.SKINNED)
            for seat in range(ref.n):
                rendered = ref.render_context(seat)
                self.assertNotIn("centre", rendered.lower(),
                                 f"seed {seed}, seat {seat} still says centre")
                self.assertIn("sideboard", rendered.lower())

    def test_a_centre_reveal_is_rendered_in_the_skin_s_word(self):
        """Driven directly, because a spotter that looked at the centre is not in
        every deal and a sweep that silently never hit one would pass empty."""
        ref = ChangelingReferee.new(5, seed=3, theme=self.SKINNED)
        line = ref._knowledge_line(Knowledge(centre_ref(0), "pack"))
        self.assertIn("Sideboard card 1 is the", line)


class TestSeatSeesBeliefNotTruth(unittest.TestCase):
    def setUp(self):
        self.ref = ChangelingReferee.new(5, seed=find_diverged_seed())
        self.diverged = sorted(self.ref.night.diverged())

    def test_the_game_under_test_actually_has_a_diverged_seat(self):
        """The control: every assertion below is vacuous without one."""
        self.assertTrue(self.diverged)

    def test_seat_view_renders_the_believed_card(self):
        for seat in self.diverged:
            view = self.ref.seat_view(seat)
            believed = self.ref.theme.card_names[self.ref.believes(seat).key]
            held = self.ref.theme.card_names[self.ref.holds(seat).key]
            self.assertEqual(view.own_role, believed)
            self.assertNotEqual(view.own_role, held)

    def test_a_diverged_seat_is_told_a_side_it_may_not_win_with(self):
        for seat in self.diverged:
            if self.ref.believes(seat).side is not self.ref.holds(seat).side:
                view = self.ref.seat_view(seat)
                self.assertEqual(
                    view.own_team,
                    self.ref.theme.side_names[self.ref.believes(seat).side])
                break


class TestGateOne(unittest.TestCase):
    def test_no_leak_in_any_seat_across_many_deals(self):
        for seed in range(200):
            ref = ChangelingReferee.new(5, seed=seed)
            self.assertEqual(ref.audit_all(), {}, f"seed {seed} leaked")

    def test_the_audit_catches_a_referee_that_renders_truth_to_a_seat(self):
        """Without this the clean sweep above proves only that nothing is rendered
        at all. A leaky referee MUST be caught, or the gate is decoration."""
        seed = find_diverged_seed()
        leaky = LeaksOwnTruth.new(5, seed=seed)
        # Skip games where the leak is invisible because belief and truth agree for
        # every seat - there the leaky renderer is accidentally correct.
        self.assertTrue(leaky.night.diverged())
        caught = leaky.audit_all()
        self.assertTrue(caught, "a referee rendering dawn truth passed the audit")
        for seat in leaky.night.diverged():
            self.assertIn(seat, caught)

    def test_the_audit_catches_an_unentitled_reveal_about_another_seat(self):
        leaky = LeaksAnotherSeat.new(5, seed=7)
        self.assertTrue(leaky.audit_all(),
                        "an unentitled third-party reveal passed the audit")

    def test_a_stale_reveal_does_not_confer_entitlement(self):
        """The spotter read a card that has since moved. It may keep believing it;
        the referee may not restate it as a fact about the seat's dawn card."""
        for seed in range(200):
            ref = ChangelingReferee.new(5, seed=seed)
            for viewer in range(ref.n):
                for k in ref.entitled_knowledge(viewer):
                    if k.seat < 0 or k.label in ("switched", "fellow-pack"):
                        continue
                    if k.label != ref.holds(k.seat).key:
                        self.assertNotIn(k.seat, ref.entitled_seats(viewer))
                        return
        self.fail("no stale reveal found in range - widen the search")

    def test_every_knowledge_line_is_a_known_reveal_form(self):
        """The structural guarantee behind matching on associations instead of bare
        card names: a phrasing written outside ``reveal_forms`` would tie a seat to
        a card in bytes the audit never searches. This fails when that happens."""
        for seed in range(200):
            ref = ChangelingReferee.new(5, seed=seed)
            for viewer in range(ref.n):
                for k in ref.entitled_knowledge(viewer):
                    line = ref._knowledge_line(k).strip()[2:].strip()
                    if k.seat < 0 or k.label == "switched":
                        continue           # centre and positional name no seat-card
                    key = "pack" if k.label == "fellow-pack" else k.label
                    self.assertIn(line, ref.reveal_forms(k.seat, key),
                                  f"seed {seed}: {line!r} is outside reveal_forms")


class TestNightIsNotInThePublicRecord(unittest.TestCase):
    def test_events_never_tie_a_seat_to_a_card(self):
        """The card multiset is public, so an event naming who acted would identify
        roles by elimination."""
        for seed in range(100):
            ref = ChangelingReferee.new(5, seed=seed)
            events = " ".join(t for tag, t in ref.public_events if tag == "event")
            for seat in range(ref.n):
                for key in ("pack", "spotter", "swapper", "switcher", "deceived",
                            "bystander"):
                    for form in ref.reveal_forms(seat, key):
                        self.assertNotIn(form, events)


class TestDay(unittest.TestCase):
    def setUp(self):
        self.ref = ChangelingReferee.new(5, seed=11, discussion_rounds=1)

    def test_speech_is_published_and_capped(self):
        self.ref.speak(0, "x" * 900)
        said = [t for tag, t in self.ref.public_events if tag == "speech"][0]
        self.assertLessEqual(len(said), 280 + len("Seat 0: "))

    def test_discussion_closes_into_the_vote(self):
        self.assertIs(self.ref.phase, Phase.DISCUSS)
        self.ref.close_round()
        self.assertIs(self.ref.phase, Phase.VOTE)

    def test_a_seat_may_not_point_at_itself(self):
        self.ref.close_round()
        with self.assertRaises(IllegalAction):
            self.ref.cast(2, 2)

    def test_a_seat_may_not_vote_twice(self):
        self.ref.close_round()
        self.ref.cast(2, 3)
        with self.assertRaises(IllegalAction):
            self.ref.cast(2, 4)

    def test_voting_before_the_vote_phase_is_refused(self):
        with self.assertRaises(IllegalAction):
            self.ref.cast(0, 1)

    def test_nothing_is_published_until_every_seat_has_cast(self):
        """Votes are simultaneous. A seat reading the tally mid-vote is playing a
        different game from the one the rules describe."""
        self.ref.close_round()
        for seat in range(4):
            self.ref.cast(seat, (seat + 1) % 5)
            joined = " ".join(t for _, t in self.ref.public_events)
            self.assertNotIn("Votes:", joined)
        self.ref.cast(4, 0)
        joined = " ".join(t for _, t in self.ref.public_events)
        self.assertIn("Votes:", joined)


class TestOutcomeReadsTruth(unittest.TestCase):
    def all_point_at(self, ref, target: int) -> None:
        ref.close_round()
        for seat in range(ref.n):
            ref.cast(seat, target if seat != target else (target + 1) % ref.n)

    def test_accusing_a_seat_that_HOLDS_pack_wins_for_the_village(self):
        ref = ChangelingReferee.new(5, seed=4, discussion_rounds=1)
        wolf = next(s for s in range(5) if ref.holds(s).side is Side.PACK)
        self.all_point_at(ref, wolf)
        self.assertEqual(ref.winner, Side.VILLAGE.value)

    def test_a_seat_that_only_BELIEVES_pack_does_not_satisfy_the_village(self):
        """The thesis, at the scoring end: a seat playing the day as a wolf, whose
        card was taken before dawn, is not a wolf and accusing it loses."""
        for seed in range(400):
            ref = ChangelingReferee.new(5, seed=seed, discussion_rounds=1)
            fakes = [s for s in range(5)
                     if ref.believes(s).side is Side.PACK
                     and ref.holds(s).side is not Side.PACK]
            if not fakes:
                continue
            self.all_point_at(ref, fakes[0])
            self.assertEqual(ref.winner, Side.PACK.value)
            return
        self.fail("no seat believed pack while holding something else in range")

    def test_a_tie_accuses_every_tied_seat(self):
        ref = ChangelingReferee.new(5, seed=9, discussion_rounds=1)
        ref.close_round()
        for seat, target in {0: 1, 1: 0, 2: 1, 3: 0, 4: 2}.items():
            ref.cast(seat, target)
        self.assertEqual(ref.accused, (0, 1))

    def test_the_reveal_lands_referee_side_only(self):
        ref = ChangelingReferee.new(5, seed=4, discussion_rounds=1)
        wolf = next(s for s in range(5) if ref.holds(s).side is Side.PACK)
        self.all_point_at(ref, wolf)
        self.assertTrue(any("dawn truth" in line for line in ref.referee_log))
        joined = " ".join(t for _, t in ref.public_events)
        self.assertNotIn("dawn truth", joined)


class TestThemesChangeNoRule(unittest.TestCase):
    def test_the_same_seed_plays_the_same_game_under_every_theme(self):
        outcomes = []
        for theme in THEMES.values():
            ref = ChangelingReferee.new(5, seed=21, theme=theme,
                                        discussion_rounds=1)
            outcomes.append(({s: ref.holds(s).key for s in range(5)},
                             {s: ref.believes(s).key for s in range(5)}))
        self.assertEqual(len(set(map(str, outcomes))), 1)

    def test_gate_one_holds_under_every_theme(self):
        for theme in THEMES.values():
            for seed in range(40):
                ref = ChangelingReferee.new(5, seed=seed, theme=theme)
                self.assertEqual(ref.audit_all(), {},
                                 f"{theme.name} seed {seed} leaked")


if __name__ == "__main__":
    unittest.main()
