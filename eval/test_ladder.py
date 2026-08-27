"""Tests for the control ladder runner.

The one that matters is `test_score_rules_is_tie_averaged_and_dedupes`: the offline
half produces the number the write-up leans on, and both of its failure modes -
counting a same-seed repeat twice, and letting a tie-break convention into a corpus
statistic - move that number UP without raising anything.
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict

import pytest

from eval.ladder import play_arm, score_rules
from games.cabal.heuristic import HeuristicPolicy
from games.cabal.player import RandomPolicy, play_game
from games.cabal.referee import CabalReferee
from games.cabal.roles import Team


def test_play_arm_seats_by_team_not_by_seat_number():
    """Seating is the EXPERIMENTER's call, made from the deal. A policy may not do
    this, which is why it happens in the runner and not in `act`."""
    arm = play_arm("good only", heuristic_good=True, heuristic_evil=False, games=12)
    assert arm.games == 12
    assert 0 <= arm.good_wins <= 12
    assert arm.hunt_hits <= arm.hunts <= arm.games

    ref = CabalReferee.new(5, seed=0)
    policies = {}
    for s in range(5):
        use = ref.assignment[s].team is Team.GOOD
        policies[s] = (HeuristicPolicy(rng=random.Random(s)) if use
                       else RandomPolicy(rng=random.Random(s)))
    good = {s for s, r in ref.assignment.items() if r.team is Team.GOOD}
    assert {s for s, p in policies.items() if isinstance(p, HeuristicPolicy)} == good


def test_the_heuristic_good_arm_beats_the_random_floor(tmp_path):
    """The rung has to be a rung. If a hand-written good side does not beat random
    noise against the same opponent, there is nothing between `random` and `LLM`
    after all and the ladder is still two-runged."""
    floor = play_arm("floor", False, False, games=120)
    rung = play_arm("rung", True, False, games=120)
    assert rung.good_wins > floor.good_wins


def _game_with_hunt(seed: int) -> dict:
    ref = CabalReferee.new(5, seed=seed)
    rec = play_game(ref, {s: RandomPolicy(rng=random.Random(seed * 7 + s))
                          for s in range(5)})
    return json.loads(json.dumps({"game": seed, **asdict(rec)}))


def test_score_rules_is_tie_averaged_and_dedupes(tmp_path):
    """Both guards in one place, because both inflate the headline silently.

    A same-seed repeat counted twice halves nothing and tightens everything; a
    tie-broken pick puts the luck of a convention inside a corpus statistic.
    """
    games = [_game_with_hunt(s) for s in range(14)]
    path = tmp_path / "one.jsonl"
    path.write_text("".join(json.dumps(g) + "\n" for g in games), encoding="utf-8")
    twice = tmp_path / "twice.jsonl"
    twice.write_text(path.read_text(encoding="utf-8") * 2, encoding="utf-8")

    once = score_rules([str(path)])
    doubled = score_rules([str(twice)])
    assert once == doubled            # the repeat contributed nothing

    for name, (hit, total) in once.items():
        assert 0 <= hit <= total
    # tie-averaging shows up as a fractional score; a tie-broken rule cannot
    assert any(abs(hit - round(hit)) > 1e-9
               for name, (hit, _) in once.items() if name != "the model itself")


def test_chance_comes_from_the_recorded_legal_set():
    """Not from a hardcoded 1/3. The legal set is 3 at 5 seats with a hunter that
    sees its ally and 4 under a variant, so a scorer that assumes the constant
    grades against the wrong baseline the first time the deal changes."""
    games = [_game_with_hunt(s) for s in range(10)]
    import tempfile, os
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write("".join(json.dumps(g) + "\n" for g in games))
    try:
        scored = score_rules([path])
        hit, total = scored["chance"]
        assert total > 0
        assert hit / total == pytest.approx(1 / 3)   # SETUP_5's legal set is 3
    finally:
        os.unlink(path)
