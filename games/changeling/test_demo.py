"""The demo's own guard, changeling's copy. Reasoning in ``games/cabal/test_demo.py``.

The stake is higher here than in cabal: this deck holds duplicates, so knowing
one seat's dealt card narrows what every other seat can be holding, and the night
may have made that card false for its own seat without telling it.
"""

from __future__ import annotations

import io
import random

import pytest

from core.console import ConsoleBackend, human_seats
from games.changeling.demo import build_policies, opening_view
from games.changeling.player import (ACTION_KEYS, LLMPolicy, RandomPolicy,
                                     play_game)
from games.changeling.referee import ChangelingReferee


def test_the_sample_view_is_withheld_from_a_human_table():
    ref = ChangelingReferee.new(5, seed=5)
    out = opening_view(ref, {0})
    assert ref.render_context(0) not in out
    assert "withheld" in out


def test_it_is_shown_when_nobody_is_playing():
    """The control: a guard that withheld unconditionally would pass the test
    above and quietly cost the demo its point."""
    ref = ChangelingReferee.new(5, seed=5)
    assert ref.render_context(0) in opening_view(ref, set())


def test_a_human_in_another_seat_is_still_withheld_seat_zeros_view():
    ref = ChangelingReferee.new(5, seed=5)
    assert ref.render_context(0) not in opening_view(ref, {3})


class _Args:
    backend = None
    model = "auto"
    retries = 2
    register = "character"
    seed = None
    no_thinking = False
    human = "0"
    human_retries = 4


def test_only_the_named_seat_gets_a_console():
    ref = ChangelingReferee.new(5, seed=5)
    policies = build_policies(ref, _Args(), random.Random(5))
    assert isinstance(policies[0].backend, ConsoleBackend)
    for seat in (1, 2, 3, 4):
        assert isinstance(policies[seat], RandomPolicy)


def test_a_hand_played_game_reaches_a_winner_with_gate_one_audited():
    ref = ChangelingReferee.new(5, seed=5)
    console = ConsoleBackend(keys=ACTION_KEYS)
    console.stdin = io.StringIO("say I will wait\nvote 1\n" * 40)
    console.stdout = io.StringIO()
    rng = random.Random(5)
    human = LLMPolicy(backend=console, retries=8, fallback=RandomPolicy(rng))
    policies = {s: (human if s == 0 else RandomPolicy(rng)) for s in range(ref.n)}

    rec = play_game(ref, policies)           # audit=True: a leak raises

    assert rec.winner is not None
    assert rec.fallbacks == 0
    served = {d.served_by for d in rec.decision_log if d.seat == 0}
    assert served == {"human"}
