"""The demo's own guard, belfry's copy. Reasoning in ``games/cabal/test_demo.py``.

The stake is the same and the shape is slightly different: this game's first
decision belongs to whoever wakes first, so the sample view is that seat's rather
than seat 0's. A guard keyed to seat 0 would have printed nothing in this rung and
would still have looked correct.
"""

from __future__ import annotations

import io
import random

from core.console import ConsoleBackend
from games.belfry.demo import build_policies, opening_view
from games.belfry.player import (ACTION_KEYS, LLMPolicy, RandomPolicy,
                                 play_game)
from games.belfry.referee import BelfryReferee


def test_the_sample_view_is_withheld_from_a_human_table():
    ref = BelfryReferee.new(7, seed=5)
    out = opening_view(ref, {0})
    for seat in range(ref.n):
        assert ref.seat_lines(seat) not in out
    assert "withheld" in out


def test_it_is_shown_when_nobody_is_playing():
    """The control: a guard that withheld unconditionally would pass the test
    above and quietly cost the demo its point."""
    ref = BelfryReferee.new(7, seed=5)
    turn = ref.pending()
    assert ref.render_context(turn.seat) in opening_view(ref, set())


def test_a_human_in_another_seat_is_still_withheld_the_sample():
    ref = BelfryReferee.new(7, seed=5)
    out = opening_view(ref, {3})
    for seat in range(ref.n):
        assert ref.seat_lines(seat) not in out


class _Args:
    backend = None
    model = "auto"
    retries = 2
    register = "character"
    seed = None
    no_thinking = False
    human = "2"
    human_retries = 4


def test_only_the_named_seat_gets_a_console():
    ref = BelfryReferee.new(7, seed=5)
    policies = build_policies(ref, _Args(), random.Random(5))
    assert isinstance(policies[2].backend, ConsoleBackend)
    for seat in (0, 1, 3, 4, 5, 6):
        assert isinstance(policies[seat], RandomPolicy)


def test_a_hand_played_game_reaches_an_end_with_gate_one_audited():
    """A person answering every question this game can ask, in shorthand, all the
    way to a result - which is also the closest thing to a fixture for the console
    reading each of this rung's action keys."""
    ref = BelfryReferee.new(5, seed=5)
    console = ConsoleBackend(keys=ACTION_KEYS)
    console.stdin = io.StringIO(
        "say I will wait\ntarget 1\ntargets 1 2\nvote n\nnominate pass\n" * 200)
    console.stdout = io.StringIO()
    rng = random.Random(5)
    human = LLMPolicy(backend=console, retries=12, fallback=RandomPolicy(rng))
    policies = {s: (human if s == 0 else RandomPolicy(rng)) for s in range(ref.n)}

    rec = play_game(ref, policies)           # audit=True: a leak raises

    assert rec.error is None
    assert rec.fallbacks == 0
    served = {d.served_by for d in rec.decision_log if d.seat == 0}
    assert served == {"human"}
