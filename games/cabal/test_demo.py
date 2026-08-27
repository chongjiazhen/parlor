"""The demo's own guard: what it prints before anyone has moved.

Gate #1 is the referee's guarantee about what it renders to a seat, and
``assert_no_leak`` enforces it every turn. This file covers the hole that guard
by construction cannot see - the harness printing a seat's view to the terminal
for the reader's benefit, past the referee entirely. It is only a leak when a
person is at the table, which is exactly when nothing else is watching.
"""

from __future__ import annotations

import io
import random

import pytest

from core.console import ConsoleBackend, human_seats
from games.cabal.demo import build_policies, opening_view
from games.cabal.player import ACTION_KEYS, LLMPolicy, RandomPolicy, play_game
from games.cabal.referee import CabalReferee


def test_the_sample_view_is_withheld_from_a_human_table():
    ref = CabalReferee.new(5, seed=3)
    out = opening_view(ref, {0})
    assert ref.render_context(0) not in out
    assert "withheld" in out


def test_it_is_shown_when_nobody_is_playing():
    """The control for the test above: without it, a guard that withheld the view
    unconditionally would pass and the demo would have quietly lost its point."""
    ref = CabalReferee.new(5, seed=3)
    out = opening_view(ref, set())
    assert ref.render_context(0) in out


def test_a_human_in_another_seat_is_still_withheld_seat_zeros_view():
    """The case that motivates the guard: seat 0's role is precisely what a person
    in seat 3 must not know."""
    ref = CabalReferee.new(5, seed=3)
    assert ref.render_context(0) not in opening_view(ref, {3})


class _Args:
    backend = None
    model = "auto"
    retries = 2
    speaker = False
    register = "character"
    seed = None
    human = "0"
    human_retries = 4


def test_only_the_named_seat_gets_a_console():
    ref = CabalReferee.new(5, seed=3)
    policies = build_policies(ref, _Args(), random.Random(3))
    assert isinstance(policies[0].backend, ConsoleBackend)
    for seat in (1, 2, 3, 4):
        assert isinstance(policies[seat], RandomPolicy)


def test_a_hand_played_game_reaches_a_winner_with_gate_one_audited():
    """End to end through the real driver: the console's replies go through the
    game's own parser and the referee's own refusals, and the audit runs on every
    turn as it does for a model table."""
    ref = CabalReferee.new(5, seed=3)
    console = ConsoleBackend(keys=ACTION_KEYS)
    console.stdin = io.StringIO("team 0 1 2\nvote y\ncard pass\nsay ok\ntarget 1\n" * 40)
    console.stdout = io.StringIO()
    rng = random.Random(3)
    human = LLMPolicy(backend=console, retries=8, fallback=RandomPolicy(rng=rng))
    policies = {s: (human if s == 0 else RandomPolicy(rng=rng)) for s in ref.assignment}

    rec = play_game(ref, policies)           # audit=True: a leak raises

    assert rec.winner is not None
    assert rec.fallbacks == 0
    # every move the person made is attributed to them, not to a model
    served = {d.served_by for d in rec.decision_log if d.seat == 0}
    assert served == {"human"}
