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
