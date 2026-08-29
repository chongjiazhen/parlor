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
from games.changeling.demo import (build_policies, constrained_deal,
                                   opening_view)
from games.changeling.player import (ACTION_KEYS, LLMPolicy, RandomPolicy,
                                     play_game)
from games.changeling.referee import ChangelingReferee
from games.changeling.roles import SETUP_5, Side


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


# ---- --human-role: a UAT deal, and the stream it must not touch --------------

def _keys(dealt, centre):
    return sorted([c.key for c in dealt.values()] + [c.key for c in centre])


def test_the_wanted_card_reaches_the_seat_whoever_was_holding_it():
    """Some seeds refuse, and that is the pack guard below doing its job on a real
    deal rather than a contrived one - so this asserts on the deals that happen."""
    served = 0
    for seed in range(30):
        try:
            dealt, _ = constrained_deal(SETUP_5, random.Random(seed), 2, "spotter")
        except SystemExit:
            continue
        served += 1
        assert dealt[2].key == "spotter", f"seed {seed}"
    assert served > 15, f"only {served}/30 seeds could seat the card"


def test_the_deck_is_permuted_not_edited():
    """A swap moves one pair. A re-deal that dropped or duplicated a card would
    change what counting claims against the multiset can prove - the game's central
    deduction."""
    plain = sorted(c.key for c in SETUP_5.deck)
    for seed in range(30):
        try:
            dealt, centre = constrained_deal(SETUP_5, random.Random(seed), 0,
                                             "deceived")
        except SystemExit:
            continue
        assert _keys(dealt, centre) == plain, f"seed {seed}"


def test_it_leaves_the_generator_where_an_unconstrained_deal_would():
    """The landmine this whole design exists for. A re-deal loop consumes draws,
    so the same seed would give a different night and different policy choices, and
    a constrained game could not be compared with its unconstrained twin. One deal
    is taken, so the stream position is identical afterwards."""
    from games.changeling.night import deal
    for seed in (0, 7, 1000):
        a = random.Random(seed)
        deal(SETUP_5, a)
        b = random.Random(seed)
        constrained_deal(SETUP_5, b, 1, "swapper")
        assert a.random() == b.random(), f"seed {seed}: the deal consumed extra draws"


def test_a_card_this_deck_does_not_hold_is_refused():
    with pytest.raises(SystemExit) as caught:
        constrained_deal(SETUP_5, random.Random(0), 0, "waker")
    assert "waker" in str(caught.value)


def test_it_refuses_to_empty_the_seats_of_the_last_pack_card():
    """`require_seated_pack` is a promise printed in the rules every seat reads.
    Swapping the only seated pack into the centre would retract it silently."""
    refused = 0
    for seed in range(400):
        rng = random.Random(seed)
        try:
            dealt, _ = constrained_deal(SETUP_5, rng, 0, "bystander")
        except SystemExit:
            refused += 1
            continue
        assert any(c.side is Side.PACK for c in dealt.values()), f"seed {seed}"
    assert refused, "no seed exercised the guard - it is untested, not satisfied"


def test_a_normal_run_marks_the_record_None_and_a_constrained_one_True():
    ref = ChangelingReferee.new(5, seed=3, discussion_rounds=1)
    rng = random.Random(3)
    rec = play_game(ref, {s: RandomPolicy(rng) for s in range(5)})
    assert rec.uat is None, "an ordinary game must not look like a UAT one"
    ref = ChangelingReferee.new(5, seed=3, discussion_rounds=1)
    rec = play_game(ref, {s: RandomPolicy(rng) for s in range(5)}, uat=True)
    assert rec.uat is True
