"""``docs/changeling-waker-criterion.md`` pinned so it cannot drift after the arm
landed.

Every case is written against a SYNTHETIC record, never the live one, so a run on
disk cannot change what any of them assert. That is the same discipline
``eval/test_quorum_live1_verdict.py`` carries and for the same reason: this file is
what stops the arithmetic being edited to agree with the result.
"""
from __future__ import annotations

import json
import unittest
from unittest import mock

from eval import waker_verdict as verdict


def vote(hit: bool, cls: str = "none", wolf: bool = False,
         diverged: bool = False) -> dict:
    return {"seat": 0, "target": 1, "voter_holds_pack": wolf,
            "target_holds_pack": hit, "knowledge_class": cls,
            "voter_believes_pack": False, "voter_diverged": diverged}


def game(votes_: list[dict], *, seats: int = 6, waker: bool = True,
         decisions: int = 18, fallbacks: int = 0, winner: str = "village") -> dict:
    truth = {str(s): ("pack" if s == 0 else "bystander") for s in range(seats)}
    dealt = dict(truth)
    if waker:
        dealt["1"] = "waker"
    return {"truth": truth, "dealt": dealt, "votes": votes_, "winner": winner,
            "decisions": decisions, "fallbacks": fallbacks, "recovered": 0}


def arm(n_games: int, hits: int, misses: int, **kw) -> list[dict]:
    """``n_games`` games carrying ``hits + misses`` blind votes spread one game at
    a time - the game is the bootstrap's resampling unit, so a single pile is not
    an arm-shaped record."""
    pattern = [True] * hits + [False] * misses
    rows = []
    for i in range(n_games):
        chunk = pattern[i::n_games]
        rows.append(game([vote(h) for h in chunk], **kw))
    return rows


def summary_for(games: list[dict]) -> dict:
    blind = sum(1 for g in games for v in g["votes"]
                if v["knowledge_class"] == "none" and not v["voter_holds_pack"])
    return {"score": {"games_completed": len(games),
                      "gate3_deduction": {"blind_votes": blind}},
            "args": {"seats": 6, "seed": 12000, "temperature": 0.8, "rounds": 2,
                     "arm": "llm", "no_thinking": True}}


def run(games, control=None, path=verdict.CAMPAIGN, summary=None):
    """Drive ``report`` against synthetic records, with no disk involved."""
    summary = summary_for(games) if summary is None else summary

    def fake_load(p):
        if control is not None and p == "CTRL":
            return summary_for(control), control
        if p == "CTRL":
            raise FileNotFoundError(p)
        return summary, games

    with mock.patch.object(verdict, "load", fake_load):
        return verdict.report(path, "CTRL")


def control_arm(two_wolf: int = 90, one_wolf: int = 70) -> list[dict]:
    """A random control whose DERIVED chance lands on the criterion's 30.14%.

    The mix is the point. A deck that always deals one wolf of six gives 1/5 =
    20.00%, which is not this deck: the waker arm's own control read 31.12%
    because real games mix one- and two-wolf dawns, and the bar is weighted by
    villager votes across that mix. 90 two-wolf and 70 one-wolf games put it on
    30.14% exactly, so this fixture exercises the AGREES branch rather than
    accidentally testing the clause that moves the bar.
    """
    rows = []
    for _ in range(two_wolf):
        g = game([vote(False)], seats=6)
        g["truth"]["1"] = "pack"
        rows.append(g)
    rows += [game([vote(False)], seats=6) for _ in range(one_wolf)]
    return rows


def clustered(hits: int, misses: int, per_game: int = 4,
              n_games: int = 200) -> list[dict]:
    """The same votes packed ``per_game`` at a time, the rest of the arm
    empty.

    The game is the bootstrap's resampling unit, so clustering widens that
    interval while leaving Wilson - which counts votes - untouched. That is
    the only shape where 'both floors' and 'either floor' give different
    answers, which is why the fixture exists.
    """
    pattern = [True] * hits + [False] * misses
    rows, i = [], 0
    while i < len(pattern):
        rows.append(game([vote(h) for h in pattern[i:i + per_game]]))
        i += per_game
    rows += [game([]) for _ in range(max(0, n_games - len(rows)))]
    return rows


class TheBar(unittest.TestCase):
    def test_the_bar_is_the_criterions_and_it_is_the_higher_of_two(self):
        """30.14% derived, against the arm's own 28.82% measured. The criterion
        names the higher so a reader cannot pick after the fact."""
        self.assertEqual(verdict.CRITERION_BAR, 0.3014)
        self.assertEqual(verdict.MEASURED_ARM_BLIND, 0.2882)
        self.assertGreater(verdict.CRITERION_BAR, verdict.MEASURED_ARM_BLIND)

    def test_an_own_arm_that_disagrees_by_over_a_point_BECOMES_the_bar(self):
        """The criterion's own clause: 'if that arm disagrees with 30.14% by more
        than a point, the run's own arm is the bar and this number is the thing
        that was wrong.'"""
        # a control whose derived chance is far from 30.14%: two wolves of six
        ctrl = [game([vote(False)], seats=6) for _ in range(40)]
        for g in ctrl:
            g["truth"]["1"] = "pack"
        text, _ = run(arm(200, 160, 80), control=ctrl)
        self.assertIn("RUN'S OWN random arm", "\n".join(text))

    def test_an_own_arm_that_agrees_leaves_the_criterions_bar_standing(self):
        ctrl = control_arm()
        text, _ = run(arm(200, 160, 80), control=ctrl)
        joined = "\n".join(text)
        self.assertIn("the criterion's bar stands", joined)
        self.assertIn("THE BAR IS 30.14%", joined)

    def test_an_absent_control_is_recorded_not_defaulted(self):
        """S2 ran no random side and S5 had to record it. A tool that quietly used
        the criterion's number would have hidden the same gap."""
        text, _ = run(arm(200, 160, 80), control=None)
        self.assertIn("ABSENT", "\n".join(text))


class GateThree(unittest.TestCase):
    def test_both_floors_must_clear_not_either(self):
        """The clause S5 could not apply cleanly, stated in advance here.

        **This needs a record where the two floors DISAGREE, or it proves
        nothing.** Asserting only that the sentence is printed, on an arm
        where both floors clear anyway, passed a mutant reading `any` for
        `all`: the gate would have held on ONE floor while the criterion
        demands two. 60/160 = 37.50% clustered four votes to a game puts
        Wilson at 30.37% (clears) and the game bootstrap at 22.86% (does
        not) - votes inside one game share a deal, so clustering widens the
        resampling unit's interval while leaving the vote count alone.
        """
        text, _ = run(clustered(60, 100, per_game=4))
        joined = "\n".join(text)
        self.assertIn("requires BOTH floors to clear", joined)
        self.assertIn("Wilson floor 30.37% clears", joined)
        self.assertIn("bootstrap floor 22.86% does NOT clear", joined)
        self.assertIn("gate #3 NOT SHOWN", joined)

    def test_both_floors_clearing_is_what_HOLDS_looks_like(self):
        """The other half: without it a tool that never returned HOLDS would
        pass the test above."""
        text, _ = run(arm(200, 160, 80))
        self.assertIn("gate #3 HOLDS", "\n".join(text))

    def test_a_table_at_chance_is_not_shown_rather_than_failed(self):
        text, _ = run(arm(200, 72, 168))
        joined = "\n".join(text)
        self.assertIn("gate #3 NOT SHOWN", joined)
        self.assertIn("no second campaign", joined)

    def test_a_thin_blind_stratum_is_REFUSED_not_failed(self):
        """Pre-committed: under 150 blind votes the gate is refused, because an
        interval that wide spans everything and reads as a result."""
        text, code = run(arm(200, 50, 50))
        joined = "\n".join(text)
        self.assertIn("REFUSED, not failed", joined)
        self.assertIn(str(verdict.BLIND_FLOOR_VOTES), joined)
        self.assertEqual(code, 3)

    def test_the_power_promise_reproduces_at_the_landed_N(self):
        """'the floor clears from a true rate of 36% upward; 35% does not.'"""
        text, _ = run(arm(200, 160, 80))
        joined = "\n".join(text)
        self.assertIn("a true 36%", joined)
        block = joined.split("power, as computed BEFORE")[1]
        self.assertIn("a true 35%: Wilson floor", block)
        line35 = [l for l in block.splitlines() if "a true 35%" in l][0]
        self.assertIn("does NOT clear", line35)


class VoidConditions(unittest.TestCase):
    def test_fallback_over_ten_percent_voids_and_STILL_prints_arithmetic(self):
        """AGENTS.md: a refused record is still audited. This repo publishes
        figures from records, so a verdict tool that returned at the refusal
        leaves a published number with no instrument behind it."""
        games = arm(200, 160, 80, decisions=18, fallbacks=3)
        text, code = run(games)
        joined = "\n".join(text)
        self.assertIn("VOID", joined)
        self.assertEqual(code, 2)
        self.assertIn("gate #3 VOID", joined)
        self.assertIn("Wilson    floor", joined)   # the arithmetic is still there

    def test_a_short_run_voids(self):
        text, code = run(arm(60, 40, 20))
        self.assertIn(f"against {verdict.GAMES_PROMISED} promised", "\n".join(text))
        self.assertEqual(code, 2)


class InstrumentControl(unittest.TestCase):
    def test_a_five_seat_record_is_flagged_against_a_six_seat_criterion(self):
        games = [game([vote(True)], seats=5) for _ in range(200)]
        text, _ = run(games)
        self.assertIn("DISAGREES", "\n".join(text))

    def test_settings_that_miss_the_criterion_are_named(self):
        games = arm(200, 160, 80)
        s = summary_for(games)
        s["args"]["temperature"] = 0.0
        text, _ = run(games, summary=s)
        self.assertIn("DISAGREES: promised 0.8", "\n".join(text))

    def test_a_scorer_disagreement_stops_before_any_bar(self):
        games = arm(200, 160, 80)
        s = summary_for(games)
        s["score"]["gate3_deduction"]["blind_votes"] = 999
        text, code = run(games, summary=s)
        joined = "\n".join(text)
        self.assertIn("DISAGREES", joined)
        self.assertNotIn("gate #3 -", joined)
        self.assertEqual(code, 1)

    def test_an_off_criterion_record_says_it_is_an_audit(self):
        text, _ = run(arm(200, 160, 80), path="eval/records/somebody-else.json")
        self.assertIn("NOT the pre-committed arm", "\n".join(text))


class GateTwoIsConditional(unittest.TestCase):
    def test_gate_two_is_not_read_while_gate_three_fails(self):
        text, _ = run(arm(200, 72, 168))
        joined = "\n".join(text)
        self.assertIn("NOT READ", joined.split("gate #2")[1])

    def test_gate_two_gets_no_verdict_even_when_read(self):
        """The criterion declares no bar for #2, so it is a rate with an interval
        and nothing more. rate_ok's 5% CI floor is pre-declared nowhere."""
        text, _ = run(arm(200, 160, 80))
        self.assertIn("NO VERDICT", "\n".join(text).split("gate #2")[1])


class TheWakerSplitIsNotAGate(unittest.TestCase):
    def test_it_is_reported_as_an_observation_with_no_bar(self):
        games = arm(100, 80, 40, waker=True) + arm(100, 80, 40, waker=False)
        text, _ = run(games)
        block = "\n".join(text).split("the waker split")[1]
        self.assertIn("OBSERVATION", "\n".join(text))
        self.assertIn("waker seated", block)
        self.assertIn("waker in centre", block)
        for word in ("VERDICT", "clears", "HOLDS"):
            self.assertNotIn(word, block.split("free off")[0])


if __name__ == "__main__":
    unittest.main()


class TheWakerSeatRead(unittest.TestCase):
    """The question the deck was built to ask, pre-registered as an observation."""

    def seated(self, waker_hits, table_hits, n_games=100):
        """Games where seat 1 is the waker; its vote and the table's differ."""
        rows = []
        for i in range(n_games):
            g = game([], seats=6)
            # dealt AND truth: a waker whose card was not moved. Setting only
            # `dealt` made every fixture game a moved-card game, which is not the
            # common case and quietly emptied the untouched cell.
            g["dealt"]["1"] = "waker"
            g["truth"]["1"] = "waker"
            g["votes"] = [
                dict(vote(i < waker_hits, cls="identity"), seat=1),
                dict(vote(i < table_hits, cls="identity"), seat=2),
                dict(vote(i < table_hits, cls="none"), seat=3),
            ]
            rows.append(g)
        return rows

    def test_the_waker_seat_is_the_one_DEALT_the_card(self):
        g = self.seated(1, 1, 1)[0]
        self.assertEqual(verdict.waker_seat(g), 1)
        g["dealt"]["1"] = "bystander"
        self.assertIsNone(verdict.waker_seat(g))

    def test_the_waker_is_not_also_counted_in_the_table(self):
        """A seat on both sides of the comparison would shrink every difference
        toward zero, silently."""
        rows = self.seated(60, 30)
        w = {id(v) for v in verdict.waker_votes(rows)}
        t = {id(v) for v in verdict.table_votes(rows)}
        self.assertTrue(w and t)
        self.assertFalse(w & t, "the waker's vote is in both sets")

    def test_a_real_gap_reads_and_no_gap_does_not(self):
        big = "\n".join(verdict.waker_seat_read(self.seated(90, 20)))
        self.assertIn("clears zero", big)
        flat = "\n".join(verdict.waker_seat_read(self.seated(50, 50)))
        self.assertIn("SPANS zero", flat)

    def test_a_POSITIVE_point_estimate_can_still_span_zero(self):
        """The guard that makes the interval load-bearing.

        A read that printed its point estimate AS its own interval passed
        every other case here - a large gap and a zero gap answer the same
        either way. 52 against 50 is the discriminating shape: the point is
        +2.00% and the game bootstrap still spans zero, so a zero-width
        interval would report a difference the data does not carry.
        """
        out = "\n".join(verdict.waker_seat_read(self.seated(52, 50)))
        line = [l for l in out.splitlines()
                if "difference vs the whole table" in l][0]
        self.assertIn("2.00%", line)
        self.assertIn("SPANS zero", line)

    def test_the_diverged_control_is_asserted_not_assumed(self):
        """WAKE is last in NIGHT_ORDER, so the waker's belief always matches its
        truth. The read prints that count so a night-order change cannot pass
        unnoticed as a quiet zero-vote cell."""
        out = "\n".join(verdict.waker_seat_read(self.seated(60, 40)))
        self.assertIn("instrument control: 0 waker vote(s) marked diverged", out)

    def test_card_moved_reads_dealt_against_dawn_truth(self):
        g = self.seated(1, 1, 1)[0]
        self.assertFalse(verdict.card_moved(g, 1))
        g["truth"]["1"] = "spotter"
        self.assertTrue(verdict.card_moved(g, 1))

    def test_it_carries_no_bar_and_no_verdict(self):
        out = "\n".join(verdict.waker_seat_read(self.seated(90, 20)))
        self.assertIn("no bar", out)
        self.assertIn("not promotable", out)
        for word in ("HOLDS", "NOT SHOWN", "VERDICT:"):
            self.assertNotIn(word, out)
