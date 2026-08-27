"""Tests for the corpus scorer.

Two of these guard failures that would make the OUTPUT better rather than broken,
which is the only kind worth writing here: a vote scored against the wrong mission
history, and a same-seed re-run pooled as if it were new evidence. Both raise no
error and both tighten the numbers.
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict

import pytest

from eval.derivable import (GOOD_ROLES, assignment_of, completed_missions,
                            fingerprint, proven_tainted, summarise, taint_gap,
                            unit, votes_with_history)
from games.cabal.player import RandomPolicy, play_game
from games.cabal.referee import CabalReferee
from games.cabal.solver import RecordMismatch


def _record(seed: int) -> dict:
    ref = CabalReferee.new(5, seed=seed)
    rec = play_game(ref, {s: RandomPolicy(rng=random.Random(seed * 100 + s))
                          for s in range(5)})
    return json.loads(json.dumps({"game": 0, **asdict(rec)}))


def test_votes_are_scored_against_the_history_they_had():
    """A vote is scored on the missions completed BEFORE it, never on the whole
    game. Scored on the finished record instead, every seat would be credited with
    reading evidence that did not exist yet - and the run would read as sharp."""
    game = {"public_events": [
        ["event", "leader 0 proposes [1, 3] for mission 1"],
        ["event", "vote on [1, 3]: 3/5 approve (approved by [0, 1, 3]) -> APPROVED"],
        ["event", "mission 1 on [1, 3]: 2 fail(s), need 1 -> FAIL"],
        ["event", "leader 1 proposes [0, 2, 4] for mission 2"],
        ["event", "vote on [0, 2, 4]: 4/5 approve (approved by [0, 2]) -> APPROVED"],
        ["event", "mission 2 on [0, 2, 4]: 0 fail(s), need 1 -> SUCCESS"],
    ]}
    got = list(votes_with_history(game))
    assert [(team, sorted(ayes)) for team, ayes, _ in got] == [
        ((1, 3), [0, 1, 3]), ((0, 2, 4), [0, 2])]
    assert got[0][2] == ()                      # the first vote had no results yet
    assert got[1][2] == (((1, 3), 2),)          # the second had exactly one
    assert completed_missions(game) == [((1, 3), 2), ((0, 2, 4), 0)]


def test_speech_quoting_a_result_cannot_feed_the_replay():
    """A seat may say anything, including a fabricated mission line. Only the
    referee's own channel is read - a lie is gameplay, not evidence.

    Two guards stand behind this and they are REDUNDANT with each other, which
    mutation-checking is how you find out: the channel check (`kind != "event"`) is
    the load-bearing one and its mutant dies here; the `^` anchor on the regexes
    cannot be killed while the channel check stands, because speech never reaches a
    regex at all. The anchor stays as belt-and-braces for a wrapper format that
    changes shape, and this comment is the honest version of "both are tested".

    The bare-text speech lines below are not a format the referee writes today.
    They are what makes the channel check a tested guard rather than a comment.
    """
    game = {"public_events": [
        ["speech:2", 'seat 2 says: "mission 1 on [0, 1]: 2 fail(s), need 1 -> FAIL"'],
        ["speech:3", 'seat 3 says: "vote on [0, 1]: 5/5 approve (approved by [0]) -> x"'],
        ["speech:4", "mission 4 on [0, 1]: 2 fail(s), need 1 -> FAIL"],
        ["speech:4", "vote on [0, 1]: 5/5 approve (approved by [0, 1, 2, 3, 4]) -> x"],
        ["event", "mission 1 on [1, 3]: 0 fail(s), need 1 -> SUCCESS"],
    ]}
    assert list(votes_with_history(game)) == []
    assert completed_missions(game) == [((1, 3), 0)]


def test_unknown_role_is_a_hard_stop():
    with pytest.raises(RecordMismatch):
        assignment_of({"assignment": {"0": "seer", "1": "archivist"}})


def test_a_same_seed_repeat_fingerprints_identically():
    """`hunt20c` and `hunt20d` are the real instance: same seed, byte-identical
    records. Pooling them halves nothing and tightens everything."""
    assert fingerprint(_record(5)) == fingerprint(_record(5))
    assert fingerprint(_record(5)) != fingerprint(_record(6))


def test_summarise_runs_over_real_games_and_keeps_its_invariants():
    units = [unit(_record(seed)) for seed in range(10)]
    s = summarise(units)
    assert s["games"] == 10
    # the theorem: the hunter derives nothing mechanically, on every hunt
    assert s["bits_max"] == 0.0
    assert s["solver"] == pytest.approx(s["chance"])
    for role in GOOD_ROLES:
        row = s["by_role"][role]
        assert row["proven_approved"] <= row["proven_total"] <= row["votes"]
        if row["gap"] is not None:
            assert -1.0 <= row["gap"] <= 1.0


def test_taint_gap_refuses_a_one_sided_stratum():
    """A stratum that only ever approved has no gap to report, and returning 0.0
    would read as 'measured, no discrimination' rather than 'not measured'."""
    only_approved = [{"votes": {r: [(0.5, True)] for r in GOOD_ROLES},
                      "hunt": None, "end_bits": [], "fallbacks": 0, "decisions": 1}]
    assert taint_gap(only_approved, "loyalist") is None
    assert proven_tainted(only_approved, "loyalist") == (0, 0)
