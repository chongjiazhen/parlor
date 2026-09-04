"""The demo's own guard, changeling's copy. Reasoning in ``games/cabal/test_demo.py``.

The stake is higher here than in cabal: this deck holds duplicates, so knowing
one seat's dealt card narrows what every other seat can be holding, and the night
may have made that card false for its own seat without telling it.
"""

from __future__ import annotations

import io
import random
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from core.console import ConsoleBackend, human_seats
from games.changeling.demo import (BRIEFING, LISTEN_NOTE, build_policies,
                                    constrained_deal, opening_view)
from games.changeling.player import (ACTION_KEYS, LLMPolicy, RandomPolicy,
                                      play_game)
from games.changeling.referee import (TURNS_FIXED, TURNS_RANDOM_ACTIVE,
                                      ChangelingReferee)
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
    briefing = False


def test_only_the_named_seat_gets_a_console():
    ref = ChangelingReferee.new(5, seed=5)
    policies = build_policies(ref, _Args(), random.Random(5))
    assert isinstance(policies[0].backend, ConsoleBackend)
    for seat in (1, 2, 3, 4):
        assert isinstance(policies[seat], RandomPolicy)


# ---- --briefing: wired into the console, and said once, not twice ----------


class _BriefingArgs(_Args):
    briefing = True


def test_the_briefing_flag_is_off_by_default_on_the_console():
    """The console keeps its own furniture text when the referee's frame arm
    is off - nothing changed for the un-flagged path."""
    ref = ChangelingReferee.new(5, seed=5)
    policies = build_policies(ref, _Args(), random.Random(5))
    assert policies[0].backend.briefing == BRIEFING


def test_the_flag_drops_the_consoles_own_furniture_text():
    """ref.briefing_text() now rides IN the payload, and a human seat prints
    its own payload every render - so the console's furniture briefing, which
    covers the same ground (the day's procedure, the accusation rule, what
    each side wins on), is dropped rather than said a second time."""
    ref = ChangelingReferee.new(5, seed=5, briefing=True)
    policies = build_policies(ref, _BriefingArgs(), random.Random(5))
    assert policies[0].backend.briefing == ""


def test_the_two_furniture_rules_compose_and_the_listen_note_survives_briefing():
    """The merge of S21 and S27 put two independent reasons to change the
    console furniture on one string, so the composed cell needs its own test.

    `--briefing` drops BRIEFING because `ref.briefing_text()` covers it. It does
    NOT cover the listen shorthand - briefing_text() names no `say`-with-nothing
    and still says "one turn each, in seat order" - so under random-active turns
    the note has to survive the arm, and it is then the ONLY furniture the seat
    gets."""
    ref = ChangelingReferee.new(5, seed=5, briefing=True,
                                turn_mode=TURNS_RANDOM_ACTIVE)
    policies = build_policies(ref, _BriefingArgs(), random.Random(5))
    assert policies[0].backend.briefing == LISTEN_NOTE
    assert BRIEFING not in policies[0].backend.briefing


def test_the_listen_note_is_absent_when_turns_are_fixed_under_briefing():
    """The negative half: without random-active turns the composed path must
    still hand a --briefing seat nothing at all, or the test above would pass
    on a briefing string that always carries the note."""
    ref = ChangelingReferee.new(5, seed=5, briefing=True, turn_mode=TURNS_FIXED)
    policies = build_policies(ref, _BriefingArgs(), random.Random(5))
    assert policies[0].backend.briefing == ""


def test_the_flag_leaves_other_seats_random():
    """The flag only changes what the human seat's console is handed, not who
    plays the table."""
    ref = ChangelingReferee.new(5, seed=5, briefing=True)
    policies = build_policies(ref, _BriefingArgs(), random.Random(5))
    for seat in (1, 2, 3, 4):
        assert isinstance(policies[seat], RandomPolicy)


def test_the_frame_reaches_the_human_seats_rendered_prompt_when_the_arm_is_on():
    """End to end: --briefing on the referee puts the frame in seat 0's own
    render, and the console prints exactly that render every turn."""
    ref = ChangelingReferee.new(5, seed=5, briefing=True)
    policies = build_policies(ref, _BriefingArgs(), random.Random(5))
    console = policies[0].backend
    console.stdin = io.StringIO("say I will wait\nvote 1\n" * 40)
    out = io.StringIO()
    console.stdout = out
    rng = random.Random(5)
    play_game(ref, {0: policies[0],
                    **{s: RandomPolicy(rng) for s in (1, 2, 3, 4)}})
    printed = out.getvalue()
    assert ref.briefing_text() in printed
    assert "How the day runs" in printed


def test_the_frame_is_absent_from_the_rendered_prompt_by_default():
    ref = ChangelingReferee.new(5, seed=5)
    policies = build_policies(ref, _Args(), random.Random(5))
    console = policies[0].backend
    console.stdin = io.StringIO("say I will wait\nvote 1\n" * 40)
    out = io.StringIO()
    console.stdout = out
    rng = random.Random(5)
    play_game(ref, {0: policies[0],
                    **{s: RandomPolicy(rng) for s in (1, 2, 3, 4)}})
    assert "How the day runs" not in out.getvalue()


# ---- --turns: the console side of the turn-taking arm ---------------------


def test_fixed_is_the_default_and_the_briefing_is_unchanged():
    """The default arm's console furniture must stay byte-identical - a person
    playing `fixed` today reads exactly what they read before this flag existed."""
    ref = ChangelingReferee.new(5, seed=5)
    assert ref.turn_mode == TURNS_FIXED
    policies = build_policies(ref, _Args(), random.Random(5))
    assert policies[0].backend.briefing == BRIEFING
    assert "listen" not in policies[0].backend.briefing.lower()


def test_random_active_appends_the_listen_note_to_the_briefing():
    ref = ChangelingReferee.new(5, seed=5, turn_mode=TURNS_RANDOM_ACTIVE)
    policies = build_policies(ref, _Args(), random.Random(5))
    briefing = policies[0].backend.briefing
    assert briefing == BRIEFING + LISTEN_NOTE
    assert "listen" in briefing.lower()


def test_random_active_prompts_the_human_only_on_their_own_turns():
    """Seed 6's random-active schedule for one round is [0, 1, 0, 2, 0] - seat 0
    holds the floor three times out of five, and seats 3 and 4 never do. A driver
    that asked every seat every turn (the `fixed`-shaped bug this flag exists to
    avoid) would prompt the human all five times instead of three."""
    ref = ChangelingReferee.new(5, seed=6, discussion_rounds=1,
                                turn_mode=TURNS_RANDOM_ACTIVE)
    assert ref.speaking_order() == [0, 1, 0, 2, 0]
    console = ConsoleBackend(keys=ACTION_KEYS)
    console.stdin = io.StringIO("say I am seat 0\n" * 10 + "vote 1\n" * 10)
    console.stdout = io.StringIO()
    rng = random.Random(6)
    human = LLMPolicy(backend=console, retries=8, fallback=RandomPolicy(rng))
    policies = {s: (human if s == 0 else RandomPolicy(rng)) for s in range(ref.n)}

    rec = play_game(ref, policies)

    human_turns = [d for d in rec.decision_log
                   if d.seat == 0 and d.phase == "discuss"]
    assert len(human_turns) == 3
    assert all(d.served_by == "human" for d in human_turns)


def test_an_empty_human_entry_listens_exactly_like_the_driver_routes_say():
    """Seed 6, turn 1: seat 0 is on the clock. A bare `say` - already legal
    shorthand for ``{"say": ""}`` - must reach the referee as a listen, the same
    route the driver takes for a model's empty ``say`` in `player.play_game`."""
    ref = ChangelingReferee.new(5, seed=6, discussion_rounds=1,
                                turn_mode=TURNS_RANDOM_ACTIVE)
    assert ref.on_the_clock() == 0
    console = ConsoleBackend(keys=ACTION_KEYS)
    console.stdin = io.StringIO("say\n" + "say I am seat 0\n" * 10 +
                                "vote 1\n" * 10)
    console.stdout = io.StringIO()
    rng = random.Random(6)
    human = LLMPolicy(backend=console, retries=8, fallback=RandomPolicy(rng))
    policies = {s: (human if s == 0 else RandomPolicy(rng)) for s in range(ref.n)}

    rec = play_game(ref, policies)

    first_seat0_turn = next(d for d in rec.decision_log
                            if d.seat == 0 and d.phase == "discuss")
    assert first_seat0_turn.played == "listens"
    assert first_seat0_turn.served_by == "human"
    assert rec.fallbacks == 0


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


def test_referee_transcript_flag_writes_a_live_game_log():
    """Break caught: parser-only flag or post-game renderer leaves no tailable
    sidecar during normal demo execution."""
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "referee.log"
        run = subprocess.run(
            [sys.executable, "-m", "games.changeling.demo", "--seed", "42",
             "--rounds", "1", "--referee-transcript", str(path)],
            text=True, capture_output=True, check=False)
        assert run.returncode == 0, run.stderr
        assert path.read_text(encoding="utf-8").splitlines()

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
