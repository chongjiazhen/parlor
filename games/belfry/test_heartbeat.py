"""The off-map faction, seated at belfry's table - off by default.

Three claims, in the order they are worth: the flag off changes nothing, a leaky
render is CAUGHT by belfry's own gate #1, and the snapshot the render was built
under is what catches it.
"""

from __future__ import annotations

import hashlib
import random

import pytest

from games.belfry.audit import LeakDetected, assert_no_leak, leak_audit
from games.belfry.heartbeat import BelfryHeartbeat, honest_render
from games.belfry.player import RandomPolicy, play_game
from games.belfry.referee import BelfryReferee
from games.belfry.roles import SCRIPTS
from games.heartbeat.heartbeat import audit as fact_audit

#: seeds 0..19, 5 seats, compact script, one talk round, 12-day bound, the random
#: policy on `Random(9000 + seed)`. Every byte every seat was sent, plus each
#: game's outcome, referee log and public channel. Measured on the commit BEFORE
#: the heartbeat existed and pasted here: a digest computed after the change
#: would pin the change to itself and prove nothing.
BELFRY_DIGEST_SEEDS_0_19 = (
    "b545eeba3ada04de6781ff928af3414e6cc251be1f3582deb0fcf80fa5386e66")


def _play(seed: int, seats: int = 5, heartbeat=None, hasher=None):
    """One game to the end, hashing every prompt as it is sent."""
    ref = BelfryReferee.new(seats, seed=seed, script=SCRIPTS["compact"],
                            discussion_rounds=1, max_days=12, heartbeat=heartbeat)
    pol = {s: RandomPolicy(rng=random.Random(9000 + seed)) for s in range(ref.n)}
    while not ref.done():
        turn = ref.pending()
        if turn is None:
            break
        assert_no_leak(ref)
        prompt = ref.prompt_for(turn.seat)
        if hasher is not None:
            hasher.update(prompt.encode("utf-8"))
        ref.submit(turn.seat, pol[turn.seat].act(ref, turn.seat))
    if hasher is not None:
        hasher.update(f"|{ref.winner}|{ref.reason}|{ref.day}|".encode("utf-8"))
        for line in ref.referee_log:
            hasher.update(line.encode("utf-8"))
        for tag, text in ref.public_events:
            hasher.update(f"{tag}::{text}".encode("utf-8"))
    return ref


def leaky_render(hb: BelfryHeartbeat, seat: int, night: int) -> str:
    """Every fact that has been laid, entitled or not. The variant that must fail."""
    return "\n".join(hb.world.facts[f].text for f in sorted(hb.world.facts)
                     if hb.world.laid_at[f] <= night)


def _hb(seed: int, seats: int = 5, renderer=honest_render, beats: int = 12):
    """Beats on every night, so night 1 always has a fact to be wrong about."""
    return BelfryHeartbeat.build(seed, seats, max_days=12, beats=beats,
                                 renderer=renderer)


# ---- the flag off ----------------------------------------------------------

def test_belfry_is_byte_identical_over_20_seeds_with_the_flag_off():
    h = hashlib.sha256()
    for seed in range(20):
        _play(seed, hasher=h)
    assert h.hexdigest() == BELFRY_DIGEST_SEEDS_0_19


def test_the_referee_default_carries_no_faction():
    ref = BelfryReferee.new(5, seed=1, script=SCRIPTS["compact"])
    assert ref.heartbeat is None
    assert "off the map" not in ref.render_context(0)


# ---- gate #1 ---------------------------------------------------------------

def test_a_leaky_heartbeat_render_is_caught_by_belfrys_own_audit():
    ref = BelfryReferee.new(5, seed=3, script=SCRIPTS["compact"],
                            heartbeat=_hb(3, renderer=leaky_render))
    found = [row for row in leak_audit(ref) if row[1] == -1]
    assert found, "a render carrying every fact reached a seat entitled to none"
    with pytest.raises(LeakDetected):
        assert_no_leak(ref)


def test_the_honest_heartbeat_is_clean_over_50_seeds():
    for seed in range(50):
        ref = _play(seed, heartbeat=_hb(seed))
        assert not leak_audit(ref)


def test_a_render_reaches_only_the_seats_entitled_to_its_facts():
    ref = BelfryReferee.new(5, seed=7, script=SCRIPTS["compact"], heartbeat=_hb(7))
    hb = ref.heartbeat
    fid = next(iter(hb.world.facts))
    text = hb.world.facts[fid].text
    for seat in range(ref.n):
        entitled = fid in hb.world.entitled(seat, ref.day)
        assert (text in ref.render_context(seat)) is entitled


# ---- the snapshot ----------------------------------------------------------

def test_recompute_at_a_later_night_misses_what_the_build_snapshot_catches():
    """The silent failure `docs/faction-heartbeat.md` section 1 names, seated.

    A leaky render built on night 1 goes out to a seat entitled to nothing. The
    fact then goes public on night 2 by a route the faction does not own. The
    snapshot the render was built under still catches the leak; entitlement
    recomputed at night 2 reads it clean.
    """
    ref = BelfryReferee.new(5, seed=11, script=SCRIPTS["compact"],
                            heartbeat=_hb(11, renderer=leaky_render))
    hb = ref.heartbeat
    fid = next(iter(hb.world.facts))
    seat = next(s for s in range(ref.n)
                if fid not in hb.world.entitled(s, 1))
    ref.render_context(seat)
    built = ref.heartbeat_render(seat)
    assert built.tick == 1

    # The world moves on: another beat, and the fact goes public by a route the
    # faction does not own.
    hb.tick(2)
    hb.world.publish(fid, 2)

    # Through the production call, so a `leaks` that fetched entitlement again -
    # at the latest night, at the world as it now stands, by any route other than
    # the render's own snapshot - fails here.
    assert hb.leaks(built), "the build snapshot lost the leak"
    assert not fact_audit(built, hb.snapshot(2)), (
        "recompute was expected to miss it; if it no longer does, this test has "
        "stopped measuring the failure it was written for")


# ---- the clock -------------------------------------------------------------

def test_the_schedule_is_a_pure_function_of_the_seed():
    assert (BelfryHeartbeat.build(41, 5).nights
            == BelfryHeartbeat.build(41, 5).nights)
    assert (BelfryHeartbeat.build(41, 5).nights
            != BelfryHeartbeat.build(42, 5).nights)


def test_nothing_reads_a_clock():
    a = _play(17, heartbeat=_hb(17, beats=3))
    b = _play(17, heartbeat=_hb(17, beats=3))
    assert a.heartbeat.report() == b.heartbeat.report()
    assert a.render_context(0) == b.render_context(0)


def test_ticks_are_counted_per_night():
    ref = _play(23, heartbeat=_hb(23, beats=3))
    hb = ref.heartbeat
    acted = [night for night, n in hb.ticks.items() if n]
    assert acted == [n for n in hb.nights if n <= ref.day]
    assert sum(hb.ticks.values()) == len(hb.actions) == hb.tally.decisions


def test_the_factions_decisions_stay_out_of_the_seat_denominator():
    """The gates measure seats. Pooling the faction in would move every rate."""
    hb = _hb(29, beats=3)
    on = play_game(BelfryReferee.new(5, seed=29, script=SCRIPTS["compact"],
                                     heartbeat=hb),
                   {s: RandomPolicy(rng=random.Random(29)) for s in range(5)})
    off = play_game(BelfryReferee.new(5, seed=29, script=SCRIPTS["compact"]),
                    {s: RandomPolicy(rng=random.Random(29)) for s in range(5)})
    assert hb.tally.decisions > 0
    assert on.decisions == off.decisions
    assert on.fallbacks == off.fallbacks
    assert hb.report()["fallback_rate"] == 0.0
