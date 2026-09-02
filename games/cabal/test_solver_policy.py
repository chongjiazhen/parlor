"""Tests for seating mechanical reader without widening its view."""

from __future__ import annotations

import random

import pytest

from games.cabal.player import RandomPolicy, play_game
from games.cabal.referee import CabalReferee, Phase
from games.cabal.roles import HUNTER, LOYALIST, MIMIC, SEER, SETUP_5, WATCHER
from games.cabal.solver import SolverPolicy


TRUTH = {0: SEER, 1: WATCHER, 2: LOYALIST, 3: MIMIC, 4: HUNTER}


def test_solver_policy_plays_only_mechanically_certain_votes():
    """Changing either certainty branch to random must fail this test.

    The seer knows the evil pair, so a team containing one is certainly tainted and
    a team excluding both is certainly clean. The reader has no such proof for a
    loyalist, which must remain the random control rather than invent a threshold.
    """
    policy = SolverPolicy(fallback=RandomPolicy(rng=random.Random(1)))

    def vote(seat, proposal):
        ref = CabalReferee(setup=SETUP_5, assignment=TRUTH, phase=Phase.VOTE,
                           proposal=proposal)
        return policy.act(ref, seat)["vote"]

    assert vote(0, (0, 1)) is True
    assert vote(0, (0, 3)) is False


@pytest.mark.parametrize("seed", range(12))
def test_solver_policy_is_legal_in_every_phase_and_leak_free(seed):
    """Removing fallback delegation from any non-vote phase makes a real game fail."""
    ref = CabalReferee.new(5, seed=seed)
    policies = {seat: SolverPolicy(fallback=RandomPolicy(
        rng=random.Random(seed * 10 + seat))) for seat in ref.assignment}

    rec = play_game(ref, policies)

    assert rec.error is None
    assert rec.winner in ("good", "evil")
    assert rec.fallbacks == 0


# ---- the mechanical / deferred split (S26) ---------------------------------
#
# The policy defers to its random fallback for every non-VOTE phase and every
# mixed-posterior VOTE, and those draws route around ``LLMPolicy``'s counter - so
# a solver run reported 0.00% fallback over decisions most of which WERE random.
# A deferred draw is not a fallback (nothing failed), so it gets its own pair of
# fields rather than a second meaning for ``fallbacks``.

def test_solver_policy_reports_which_mode_it_acted_in():
    policy = SolverPolicy(fallback=RandomPolicy(rng=random.Random(1)))

    def act(seat, phase, proposal=None):
        ref = CabalReferee(setup=SETUP_5, assignment=TRUTH, phase=phase,
                           proposal=proposal)
        policy.act(ref, seat)
        return policy.last_solver_mode

    assert act(0, Phase.VOTE, (0, 1)) == "mechanical"   # seer: provably clean
    assert act(0, Phase.VOTE, (0, 3)) == "mechanical"   # seer: provably tainted
    assert act(2, Phase.VOTE, (0, 1)) == "deferred"     # loyalist: mixed posterior
    assert act(2, Phase.PROPOSE) == "deferred"          # not a vote at all


def test_the_driver_counts_mechanical_and_deferred_and_neither_is_a_fallback():
    """Make a deferred draw count as mechanical and this is the test that fails."""
    ref = CabalReferee.new(5, seed=3)
    fallback = RandomPolicy(rng=random.Random(3))
    policies = {seat: SolverPolicy(fallback=fallback) for seat in ref.assignment}

    rec = play_game(ref, policies)

    assert rec.error is None
    assert rec.solver_mechanical > 0
    assert rec.solver_deferred > 0
    assert rec.solver_mechanical + rec.solver_deferred == rec.decisions
    assert rec.fallbacks == 0                  # nothing failed, so nothing fell back
    modes = [d.solver for d in rec.decision_log]
    assert modes.count("mechanical") == rec.solver_mechanical
    assert modes.count("deferred") == rec.solver_deferred
    # only a VOTE can be mechanical; every other phase is the fallback's
    assert all(d.phase == "vote" for d in rec.decision_log if d.solver == "mechanical")
    assert all(d.solver == "deferred" for d in rec.decision_log if d.phase != "vote")


def test_a_policy_without_the_split_leaves_both_counts_at_zero():
    """Random and LLM seats are not solver seats; their record says nothing about
    a split rather than counting every draw as deferred."""
    ref = CabalReferee.new(5, seed=3)
    rec = play_game(ref, {s: RandomPolicy(rng=random.Random(3)) for s in ref.assignment})
    assert (rec.solver_mechanical, rec.solver_deferred) == (0, 0)
    assert all(d.solver == "" for d in rec.decision_log)


def test_a_record_written_before_the_split_still_loads():
    """The exact key set of a pre-S26 GameRecord line, hardcoded rather than
    derived from the dataclass - the pattern ``core/test_callcost.py`` uses."""
    from games.cabal.player import Decision, GameRecord
    legacy_game = {
        "winner": "evil", "reason": "three missions failed", "turns": 30,
        "assignment": {"0": "seer"}, "votes": [], "hunt": None, "fails_played": 3,
        "missions": [False, False, False], "fallbacks": 0, "recovered": 0,
        "refused_attempts": 0, "rule_refused_attempts": 0, "decisions": 40,
        "utterances": [], "decision_log": [], "public_events": [], "log": [],
        "theme": "1984", "upstreams": {}, "trace_sample": [], "error": None,
    }
    rec = GameRecord(**legacy_game)
    assert (rec.solver_mechanical, rec.solver_deferred) == (0, 0)
    legacy_decision = {
        "turn": 4, "seat": 1, "phase": "vote", "played": "approve", "think": "",
        "note": "", "refused": "", "refusals": 0, "rule_refusals": 0,
        "fell_back": False, "served_by": "",
    }
    assert Decision(**legacy_decision).solver == ""
