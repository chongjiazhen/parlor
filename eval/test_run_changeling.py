"""The changeling eval lane: the arms, the exclusions, and the refusal to read a
gate off a random side.

The load-bearing test here is the instrument control - the random arm MUST score at
chance. If it does not, either the chance formula or the scorer is wrong, and every
number the lane produces is wrong with it. A scorer is not validated by producing
plausible output.
"""

from __future__ import annotations

import argparse
import inspect
import os
import json
import random
import shutil
import sys
import tempfile
import unittest
from collections import Counter
from unittest import mock

import eval.run_changeling
import eval.run_cabal
from core.runlog import record_paths
from eval.gate3_bar import REFERENCE_CHANCE
from eval.run_changeling import (_chance, land, one_game, report, score,
                                 villager_votes)
from games.changeling.player import RandomPolicy
from games.changeling.referee import ChangelingReferee
from games.changeling.roles import SETUPS


def make_args(**kw):
    base = dict(arm="random", backend=None, model="none", rounds=1, retries=0,
                register="character", temperature=0.8, timeout=5.0,
                max_tokens=512, theme=None, seed=1000, games=1, out=None,
                seats=5)
    base.update(kw)
    return argparse.Namespace(**base)


def random_records(n: int, seed: int = 1000):
    args = make_args(seed=seed)
    return [one_game(i, args) for i in range(n)]


class TestRandomArmScoresAtChance(unittest.TestCase):
    """The instrument control. Everything else the lane reports is read against
    this, so if the random arm does not land on chance the lane is broken."""

    @classmethod
    def setUpClass(cls):
        cls.records = random_records(300)
        cls.s = score(cls.records)

    def test_blind_accuracy_brackets_the_computed_chance(self):
        g3 = self.s["gate3_deduction"]
        lo, hi = g3["blind_accuracy_ci95"]
        chance = _chance(self.s)
        self.assertLessEqual(lo, chance, "random arm scored ABOVE chance")
        self.assertGreaterEqual(hi, chance, "random arm scored BELOW chance")

    def test_the_random_arm_never_falls_back(self):
        """A fallback IS the random policy, so a nonzero rate here means the arm
        wiring is calling something it should not."""
        self.assertEqual(self.s["integrity"]["fallback_rate"], 0.0)

    def test_the_verdict_refuses_to_read_a_gate_off_the_random_arm(self):
        text = report(self.s, make_args(arm="random"), 1.0)
        self.assertIn("this IS the chance baseline", text)
        self.assertNotIn("gate #3 HOLDS", text)


class TestUnwinnableGamesAreExcludedAndReported(unittest.TestCase):
    """RULES.md measures 2.8% of games seating no wolf at dawn. The village cannot
    win them however it plays, so they leave the denominator and are named."""

    @classmethod
    def setUpClass(cls):
        cls.records = random_records(300)
        cls.s = score(cls.records)

    def test_the_run_actually_contains_some(self):
        self.assertGreater(self.s["games_unwinnable"], 0,
                           "no unwinnable game in range - test proves nothing")

    def test_they_are_out_of_the_scored_denominator(self):
        self.assertEqual(self.s["games_scored"] + self.s["games_unwinnable"],
                         self.s["games_completed"])

    def test_they_are_named_in_the_report_rather_than_averaged_in(self):
        text = report(self.s, make_args(), 1.0)
        self.assertIn("seated no pack at dawn", text)

    def test_scoring_them_in_would_move_the_number(self):
        """Confirms the exclusion is load-bearing, not decoration."""
        g3 = self.s["gate3_deduction"]
        with_all = sum(1 for r in self.records
                       if r.winner == "village") / self.s["games_completed"]
        self.assertNotEqual(round(with_all, 6),
                            round(g3["village_win_rate"], 6))


class TestChanceIsComputedFromTheRunsOwnMix(unittest.TestCase):
    def test_a_two_wolf_dawn_carries_twice_the_chance_of_a_one_wolf_dawn(self):
        one = {"gate3_deduction": {"by_dawn_wolves": {1: (0, 100)}}}
        two = {"gate3_deduction": {"by_dawn_wolves": {2: (0, 100)}}}
        self.assertAlmostEqual(_chance(one), 0.25)
        self.assertAlmostEqual(_chance(two), 0.50)

    def test_the_bar_is_read_off_the_TABLE_and_not_off_a_constant(self):
        """A six-seat villager is one of more voters and points at more seats, so
        its chance bar is 20% where the five-seat bar is 25%. Hardcoded 5 and 4
        returned SETUP_5's number for a six-seat run - plausible, ~5 points wrong,
        and nothing raises."""
        rows = {"gate3_deduction": {"by_dawn_wolves": {1: (0, 100)}}}
        self.assertAlmostEqual(_chance({**rows, "seats": 5}), 0.25)
        self.assertAlmostEqual(_chance({**rows, "seats": 6}), 0.20)

    def test_the_bar_survives_a_json_round_trip(self):
        """JSON has no integer keys. The criterion asks a reader to recompute the
        bar off the written record, and before this the string key died on the
        subtraction - in-process it never appears, so no shipped path showed it."""
        live = {"seats": 6, "gate3_deduction": {"by_dawn_wolves": {1: (0, 100)}}}
        onwire = json.loads(json.dumps(live))
        self.assertEqual(list(onwire["gate3_deduction"]["by_dawn_wolves"]), ["1"])
        self.assertAlmostEqual(_chance(onwire), _chance(live))

    def test_a_record_written_before_seats_existed_reads_as_five(self):
        """Every record before 2026-09-02 was five-seat and carries no key.
        `eval.s5_verdict` still reads S2's, so the default is not a convenience."""
        rows = {"gate3_deduction": {"by_dawn_wolves": {1: (0, 100)}}}
        self.assertAlmostEqual(_chance(rows), _chance({**rows, "seats": 5}))

    def test_unwinnable_games_do_not_drag_chance_down(self):
        mixed = {"gate3_deduction": {"by_dawn_wolves": {0: (0, 50), 1: (0, 100)}}}
        self.assertAlmostEqual(_chance(mixed), 0.25)


class TestVerdicts(unittest.TestCase):
    def setUp(self):
        self.s = score(random_records(60))

    def test_a_high_fallback_rate_VOIDS_the_run(self):
        void = dict(self.s, integrity=dict(self.s["integrity"],
                                           fallback_rate=0.42))
        text = report(void, make_args(arm="llm"), 1.0)
        self.assertIn("VOID", text)
        self.assertNotIn("gate #3 HOLDS", text)

    def test_the_run_log_CALLS_NO_GATE_however_well_the_blind_stratum_did(self):
        """2026-09-02: the log called gate #3 off a bar the criterion never gave
        it. `_chance` is the run's OWN dawn-wolf mix and the criterion's bar is
        the measured `--arm random` reference, and on the skin pair they were
        36.47% against 35.84% - `greek-named`'s 35.90% floor HOLDS against one
        and is NOT SHOWN against the other. The interval is wrong too: the log
        publishes a BOOTSTRAP over games and the criterion's word is Wilson. A
        run log has neither the bar nor the interval the gate is cut on, so it
        reports and does not call."""
        for blind, ci in ((0.9, (0.85, 0.95)), (0.2, (0.15, 0.25))):
            g3 = dict(self.s["gate3_deduction"], blind_accuracy=blind,
                      blind_accuracy_ci95=ci)
            text = report(dict(self.s, gate3_deduction=g3),
                          make_args(arm="llm"), 1.0)
            for claim in ("gate #3 HOLDS", "gate #3 not shown", "gate #2 readable",
                          "gate #2 not shown"):
                self.assertNotIn(claim, text, f"blind={blind}: {claim!r}")

    def test_the_log_prints_BOTH_bars_and_selects_neither(self):
        """The discipline `eval.s5_verdict` already applies: every bar on the
        table against the floor, none quietly selected."""
        text = report(self.s, make_args(arm="llm"), 1.0)
        self.assertIn(f"{REFERENCE_CHANCE:.2%}", text)
        self.assertIn(f"{_chance(self.s):.2%}", text)
        self.assertIn("eval.gate3_bar", text)

    def test_gate2_is_still_named_as_conditional_on_gate3(self):
        """The conditionality is a measured fact, not a verdict, so dropping the
        verdict must not drop it: with voting at chance evil wins ~65% with no
        deception at all."""
        text = report(self.s, make_args(arm="llm"), 1.0)
        self.assertIn("conditional on gate #3", text)

    def test_an_empty_blind_stratum_is_REFUSED_not_rendered_as_zero(self):
        g3 = dict(self.s["gate3_deduction"], blind_accuracy=None,
                  blind_accuracy_ci95=None)
        text = report(dict(self.s, gate3_deduction=g3), make_args(arm="llm"), 1.0)
        self.assertIn("BLIND ACCURACY     REFUSED", text)
        self.assertNotIn("BLIND ACCURACY     0.00%", text)


class TestVillagerVotesAreKeyedOnTruth(unittest.TestCase):
    def test_a_seat_holding_pack_is_never_counted_as_a_villager(self):
        """Keying on belief would put a sleeping wolf's vote in the deduction
        denominator, which is the whole error this game makes easy to commit."""
        for rec in random_records(80):
            for v in villager_votes(rec):
                self.assertFalse(v.voter_holds_pack)

    def test_seats_that_believe_pack_but_hold_village_ARE_counted(self):
        found = False
        for rec in random_records(200):
            for v in villager_votes(rec):
                if v.voter_believes_pack:
                    found = True
        self.assertTrue(found, "no sleeper villager in range - the night is inert")


class TestReviewFixes(unittest.TestCase):
    """Regressions for defects found by review 2026-08-27."""

    def test_the_sampler_seed_is_the_GAMES_seed_not_the_runs(self):
        """`2cfe9d5`'s invariant: Backend.seed rides in the payload and one_game
        hands each game the number it deals with. This lane shipped seed=args.seed,
        pinning the sampler to one value for every game in a run."""
        from eval.run_changeling import build_backend
        args = make_args(backend="local", model="m", seed=1000)
        args.no_thinking = True
        self.assertEqual(build_backend(args, 1007).seed, 1007)
        self.assertEqual(build_backend(args, 1000).seed, 1000)

    def test_chance_is_weighted_by_villager_VOTES_not_by_games(self):
        """A 2-wolf dawn yields 3 villager votes against a 1-wolf dawn's 4, so the
        two weightings disagree - 0.357 against 0.375 on an even mix. The rate
        _chance gates is per-vote, so game-weighting set the bar ~1.8 points too
        high and made gate #3 harder than chance."""
        mixed = {"gate3_deduction": {"by_dawn_wolves": {1: (0, 100), 2: (0, 100)}}}
        self.assertAlmostEqual(_chance(mixed), 250 / 700, places=6)
        self.assertNotAlmostEqual(_chance(mixed), 0.375, places=3)

    def test_the_random_reference_is_on_the_scored_denominator(self):
        """It is printed beside a run figure computed over winnable games only."""
        from eval.run_changeling import (MEASURED_RANDOM_VILLAGE_WINS,
                                         MEASURED_RANDOM_VILLAGE_WINS_ALL_GAMES)
        self.assertGreater(MEASURED_RANDOM_VILLAGE_WINS,
                           MEASURED_RANDOM_VILLAGE_WINS_ALL_GAMES)
        self.assertAlmostEqual(MEASURED_RANDOM_VILLAGE_WINS, 0.3951, places=4)

    def test_an_empty_sample_yields_no_interval_rather_than_a_zero_width_one(self):
        from core.stats import wilson
        self.assertIsNone(wilson(0, 0))
        self.assertIsNotNone(wilson(0, 5))

    def test_each_live_seat_gets_its_own_policy_object(self):
        """One shared LLMPolicy makes `upstreams` a single Counter that the record
        sums once per seat, multiplying the census by the live-seat count."""
        from eval.run_changeling import build_policies
        from games.changeling.referee import ChangelingReferee
        args = make_args(arm="llm", backend="local", model="m")
        args.no_thinking = True
        ref = ChangelingReferee.new(5, seed=3, discussion_rounds=1)
        policies = build_policies(ref, args, random.Random(0), seed=3)
        live = [p for p in policies.values() if hasattr(p, "upstreams")]
        self.assertEqual(len(live), 5)
        self.assertEqual(len({id(p) for p in live}), 5, "seats share one policy")


class TestBothDriversAgreeOnWhatOutMeans(unittest.TestCase):
    """``--out`` is the summary path verbatim; the JSONL is ``out.jsonl``.

    The two drivers had one convention each until 2026-08-28, and the disagreement
    cost S2's records their names: a launcher written from cabal's twin passed
    ``--out eval/records/s2.json`` and ``run_changeling`` composed ``s2.json.json``.
    Pinned here rather than in one driver's file because the defect was that the two
    disagreed - a test living beside either one cannot see that.
    """

    def test_the_summary_path_is_verbatim_and_the_jsonl_is_its_sibling(self):
        self.assertEqual(record_paths("eval/records/s2.json"),
                         ("eval/records/s2.json", "eval/records/s2.json.jsonl"))

    def test_asking_for_the_paths_CREATES_the_directory_they_are_in(self):
        """`eval/records/` is gitignored, so a fresh worktree has none and a
        driver invoked by hand died `FileNotFoundError` at the first JSONL
        append - after the games had run. The launchers all carried a `mkdir`
        against this; the guarantee belongs in the one function both drivers
        route through, so it is here and the launchers are belt."""
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, True)
        records = os.path.join(root, "eval", "records")
        self.assertFalse(os.path.isdir(records))
        summary, jsonl = record_paths(os.path.join(records, "s2.json"))
        self.assertTrue(os.path.isdir(records))
        for path in (summary, jsonl):
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("{}")

    def test_a_bare_filename_has_no_directory_to_create_and_does_not_raise(self):
        """`os.path.dirname("s2.json")` is empty, and `makedirs("")` raises."""
        self.assertEqual(record_paths("s2.json"), ("s2.json", "s2.json.jsonl"))

    def test_neither_driver_composes_its_own_suffix(self):
        for module in (eval.run_changeling, eval.run_cabal):
            source = inspect.getsource(module)
            self.assertNotIn('f"{args.out}.json"', source, module.__name__)
            self.assertNotIn('f"{args.out}.jsonl"', source, module.__name__)

    def test_a_landed_record_goes_to_the_sibling_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "run.json")
            args = make_args(out=out)
            land(0, one_game(0, args), args)
            self.assertTrue(os.path.exists(out + ".jsonl"))
            self.assertFalse(os.path.exists(out + ".json.jsonl"))


if __name__ == "__main__":
    unittest.main()


class TestTheWakerDeckIsDealable(unittest.TestCase):
    """S18 froze deck A. The criterion is only binding if the flag it names runs."""

    def test_seats_six_deals_nine_cards_at_six_seats_with_a_waker(self):
        """Asserted on the RECORD, not on ``SETUPS[6]``. A test that reads the
        registry passes just as happily when ``one_game`` ignores the flag and
        deals five - which is what a mutant that reverted it did, silently."""
        setup = SETUPS[6]
        self.assertEqual((setup.n, setup.centre, len(setup.deck)), (6, 3, 9))
        self.assertIn("waker", [c.key for c in setup.deck])

        rec = one_game(0, make_args(seats=6, games=1, seed=7))
        self.assertIsNone(rec.error, rec.error)
        self.assertEqual(len(rec.truth), 6, "the run did not deal six seats")
        self.assertEqual(sorted(rec.truth), list(range(6)))

        five = one_game(0, make_args(seats=5, games=1, seed=7))
        self.assertEqual(len(five.truth), 5, "the flag changed nothing")

    def test_the_waker_is_seated_in_most_deals_so_one_run_carries_its_control(self):
        """RULES.md measured 62.0% over 4000 nights. This asserts the SHAPE - the
        card is usually seated and sometimes in the centre - not the figure, which
        belongs to the criterion and moves with the RNG."""
        seated = 0
        for seed in range(200):
            ref = ChangelingReferee.new(6, seed=seed)
            if any(c.key == "waker" for c in ref.night.dealt.values()):
                seated += 1
        self.assertTrue(40 <= seated <= 170,
                        f"waker seated in {seated}/200 - one run no longer "
                        "carries its own control")

    def test_the_five_seat_deck_still_seats_no_waker(self):
        """A deck change re-baselines everything, so SETUP_5 must not drift."""
        self.assertNotIn("waker", [c.key for c in SETUPS[5].deck])



class TestTheMixedArmsSeatTheRungAgainstTheModel(unittest.TestCase):
    """`mixed-village` and `mixed-pack` - the third cell of the ladder.

    The two arms that already exist hold their live side against the RANDOM
    control, and `docs/measurements.md` measures what that buys: a control that
    never claims a deal is read by its silence, and the rung's 77.36% village cell
    falls to 31.62% with that tier switched off. These arms replace the control
    with the rung, so the tell has an opponent that talks.

    `LLMPolicy` is stubbed here. A live seat that actually called a backend would
    make these tests a network probe, and what is under test is the SEATING - which
    side is live, which side is the rung, and that gate #1 still raises across the
    mix.
    """

    class FakeLive:
        """Stands in for a live seat: random moves, an LLMPolicy's shape."""

        def __init__(self, backend=None, retries=0, fallback=None):
            self.backend = backend
            self.upstreams = Counter()
            self.inner = fallback or RandomPolicy(random.Random(0))

        def act(self, ref, seat):
            return self.inner.act(ref, seat)

    @staticmethod
    def run_main(argv):
        """`main` reads `sys.argv`; this is the only door onto its arg handling."""
        with mock.patch.object(sys, "argv", ["run_changeling", *argv]):
            eval.run_changeling.main()

    def build(self, arm, seed=3, seats=5):
        """Seat one deal under `arm` with the live half stubbed."""
        from games.changeling.referee import ChangelingReferee
        args = make_args(arm=arm, backend="local", model="m", seed=seed)
        args.no_thinking = True
        ref = ChangelingReferee.new(seats, seed=seed, discussion_rounds=1)
        with mock.patch.object(eval.run_changeling, "LLMPolicy", self.FakeLive):
            return ref, eval.run_changeling.build_policies(
                ref, args, random.Random(seed), seed)

    def test_both_arms_are_registered_and_declared_live(self):
        for arm in ("mixed-village", "mixed-pack"):
            self.assertIn(arm, eval.run_changeling.ARMS)
            self.assertIn(arm, eval.run_changeling.LIVE_ARMS)

    def test_a_mixed_arm_without_a_backend_is_refused_at_the_door(self):
        """It does not start with "llm", so the old prefix guard let it through to
        deal 200 games with no endpoint - falling back on every decision and
        scoring the random policy. That run is a void, paid for in full."""
        with self.assertRaises(SystemExit):
            self.run_main(["--arm", "mixed-village"])

    def test_the_live_side_is_exactly_the_side_the_arm_names(self):
        """Seated by DAWN TRUTH, the same rule every other mixed arm uses: a seat
        wins with the card in front of it, not the one it believes it holds."""
        from games.changeling.heuristic import HeuristicPolicy
        from games.changeling.roles import Side

        for arm, want in (("mixed-village", Side.VILLAGE),
                          ("mixed-pack", Side.PACK)):
            for seed in range(3000, 3012):
                ref, policies = self.build(arm, seed=seed)
                live = {s for s, p in policies.items()
                        if isinstance(p, self.FakeLive)}
                rung = {s for s, p in policies.items()
                        if isinstance(p, HeuristicPolicy)}
                truth = {s for s in range(ref.n) if ref.holds(s).side is want}
                self.assertEqual(live, truth, f"{arm} seed {seed}")
                self.assertEqual(rung, set(range(ref.n)) - truth,
                                 f"{arm} seed {seed}")
                self.assertFalse(any(isinstance(p, RandomPolicy)
                                     for p in policies.values()),
                                 "the random control leaked into a mixed arm")

    def test_the_seating_actually_splits_rather_than_seating_one_policy(self):
        """A deal with every seat on one side would make the test above vacuous."""
        for arm in ("mixed-village", "mixed-pack"):
            ref, policies = self.build(arm, seed=3000)
            kinds = {type(p) for p in policies.values()}
            self.assertEqual(len(kinds), 2, f"{arm} seated one policy for all")

    def test_each_live_seat_still_gets_its_own_policy_object(self):
        """The comment in `build_policies` names the cost of sharing one: the
        upstream census gets weighted by seats rather than by calls, and in a
        mixed arm the live-seat count varies with the deal."""
        _, policies = self.build("mixed-village", seed=3000)
        live = [p for p in policies.values() if isinstance(p, self.FakeLive)]
        self.assertGreater(len(live), 1)
        self.assertEqual(len({id(p) for p in live}), len(live))

    def test_the_rung_seats_share_one_rng_so_the_game_is_reproducible(self):
        from games.changeling.heuristic import HeuristicPolicy
        _, policies = self.build("mixed-pack", seed=3000)
        rung = [p for p in policies.values() if isinstance(p, HeuristicPolicy)]
        self.assertGreater(len(rung), 1)
        self.assertEqual(len({id(p.rng) for p in rung}), 1)

    def test_a_leaking_referee_STILL_RAISES_under_a_mixed_arm(self):
        """Gate #1 is the driver's guarantee and does not care which policies are
        seated. Asserted per arm because the audit runs over rendered bytes, and a
        table where half the seats are the rung renders different ones."""
        from games.changeling.audit import LeakDetected
        from games.changeling.player import play_game
        from games.changeling.test_referee import LeaksOwnTruth, find_diverged_seed

        for arm in ("mixed-village", "mixed-pack"):
            seed = find_diverged_seed()
            args = make_args(arm=arm, backend="local", model="m", seed=seed)
            args.no_thinking = True
            ref = LeaksOwnTruth.new(5, seed=seed, discussion_rounds=1)
            with mock.patch.object(eval.run_changeling, "LLMPolicy",
                                   self.FakeLive):
                policies = eval.run_changeling.build_policies(
                    ref, args, random.Random(seed), seed)
            with self.assertRaises(LeakDetected, msg=arm):
                play_game(ref, policies)

    def test_an_honest_mixed_table_plays_a_whole_game_without_raising(self):
        """The control for the test above: the leak has to be the reason it raised,
        not the mix."""
        from games.changeling.player import play_game

        for arm in ("mixed-village", "mixed-pack"):
            ref, policies = self.build(arm, seed=3000)
            rec = play_game(ref, policies)
            self.assertIsNone(rec.error, rec.error)
            self.assertTrue(rec.winner)

    def test_the_written_record_names_the_arm_it_was_run_under(self):
        """Read off the file, not off the Namespace. Every later instrument reads
        `args.arm` out of the record to decide what it is looking at, and a verdict
        tool that cannot tell a mixed arm from `llm-village` compares two different
        games."""
        canned = one_game(0, make_args(arm="random", seed=1000))
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "mixed.json")
            with mock.patch.object(eval.run_changeling, "one_game",
                                   lambda i, a: canned):
                self.run_main(
                    ["--arm", "mixed-pack", "--backend", "local", "--games", "1",
                     "--seed", "1000", "--out", out])
            written = json.load(open(out, encoding="utf-8"))
        self.assertEqual(written["args"]["arm"], "mixed-pack")
