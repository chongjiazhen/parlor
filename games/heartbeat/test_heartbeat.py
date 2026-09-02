"""The heartbeat spike is scored on one question, and this file asks it.

Can a render be audited against the entitlement that held when it was BUILT?
``docs/faction-heartbeat.md`` §1 names the failure: a fact legitimately secret at
tick t and legitimately public at t+1 by another route, a render at t that leaked
it, and an audit that recomputes entitlement at audit time and reads clean. The
guard test below builds exactly that fixture. It was written before the loop
audited against a snapshot, and it went red against a loop that audited at the
end of the run - that red run is the mutation check.
"""

from __future__ import annotations

import json

import pytest

from games.heartbeat import heartbeat as hb


def leaky_renderer(leak_at: dict[tuple[int, int], hb.FactId]):
    """A renderer that slips one un-entitled fact's TEXT into named renders.

    Stands in for a model narrator paraphrasing a secret: the render is built
    honestly from the seat's entitled facts, then the fact at ``(tick, seat)`` is
    appended whether the seat may know it or not.
    """
    def render(world: hb.World, seat: int, tick: int) -> str:
        text = hb.default_renderer(world, seat, tick)
        fid = leak_at.get((tick, seat))
        if fid is not None:
            text += "\n" + world.facts[fid].text
        return text
    return render


class TestSnapshotAudit:
    def test_leak_at_t_caught_by_snapshot_missed_by_recompute_when_public_at_t_plus_1(self):
        """The guard. Fact F reaches seat 0 only at tick 5, by another route (a
        table-wide publish, not the faction's own propagation). The renderer
        leaked F to seat 0 at tick 4. The loop must record that leak."""
        world = hb.World.build(seed=7, n_seats=3, n_places=2)
        fid = world.add_fact(("plan", "t04"), "raid@p1#t04",
                             "the faction will raid place 1 [raid@p1#t04]",
                             tick=4)
        world.learn(fid, seat=0, tick=99)  # never, by propagation
        world.learn(fid, seat=1, tick=4)

        run = hb.Run(world, ticks=6, renderer=leaky_renderer({(4, 0): fid}),
                     after_tick={5: lambda w: w.publish(fid, tick=5)})
        run.play()

        caught = [(t, s, f) for (t, s, f, _term) in run.leaks]
        assert (4, 0, fid) in caught, (
            "the render at tick 4 leaked a fact seat 0 was not entitled to at "
            "tick 4; auditing it against entitlement recomputed after tick 5 "
            "reads clean, which is the failure the snapshot exists to prevent")

        # The contrast, stated in the same test so a reader sees both halves:
        # the same render audited against entitlement recomputed NOW is clean.
        render = next(r for r in run.renders if r.tick == 4 and r.seat == 0)
        now = world.snapshot(tick=5)
        assert hb.audit(render, now) == []
        assert hb.audit(render, render.snapshot) == [(fid, "raid@p1#t04")]

    def test_clean_renders_audit_clean_against_their_snapshot(self):
        run = hb.Run(hb.World.build(seed=11, n_seats=4, n_places=3), ticks=12)
        run.play()
        assert run.renders, "the loop built no renders"
        assert run.leaks == []

    def test_fixture_counts_caught_against_missed(self):
        """Six injected leaks, four of whose facts go public later by another
        route. The snapshot audit catches all six; a recompute at the end of the
        run misses the four. The numbers are the spike's result."""
        world = hb.World.build(seed=3, n_seats=3, n_places=2)
        injected = {}
        after = {}
        for i in range(6):
            t = 2 + i
            fid = world.add_fact(("plan", f"t{t:02d}"), f"plan#{t:02d}",
                                 f"a plan laid on tick {t:02d} [plan#{t:02d}]",
                                 tick=t)
            for s in range(3):
                world.learn(fid, seat=s, tick=99)
            injected[(t, 0)] = fid
            if i < 4:
                after[t + 1] = (lambda w, f=fid, tt=t + 1: w.publish(f, tick=tt))
        run = hb.Run(world, ticks=10, renderer=leaky_renderer(injected),
                     after_tick=after)
        run.play()

        caught = {(t, s, f) for (t, s, f, _) in run.leaks}
        assert caught == {(t, s, f) for (t, s), f in injected.items()}

        end = world.snapshot(tick=9)
        missed = [r for r in run.renders if (r.tick, r.seat) in injected
                  and hb.audit(r, end) == []]
        assert len(missed) == 4
        assert run.report()["leaks"] == {"caught_by_snapshot": 6,
                                         "missed_by_recompute_at_end": 4}


class TestDeterminism:
    def test_same_seed_same_schedule_and_byte_identical_records(self):
        a = hb.run(seed=1000, n_seats=4, n_places=3, ticks=20)
        b = hb.run(seed=1000, n_seats=4, n_places=3, ticks=20)
        assert a.schedule == b.schedule
        assert a.record_bytes() == b.record_bytes()

    def test_different_seed_moves_the_schedule(self):
        a = hb.run(seed=1000, n_seats=4, n_places=3, ticks=20)
        b = hb.run(seed=1001, n_seats=4, n_places=3, ticks=20)
        assert a.schedule != b.schedule or a.record_bytes() != b.record_bytes()

    def test_schedule_is_a_pure_function_of_the_seed(self):
        assert hb.schedule(seed=5, ticks=30, beats=6) == hb.schedule(5, 30, 6)
        s = hb.schedule(seed=5, ticks=30, beats=6)
        assert len(s) == 6 and s == tuple(sorted(set(s)))
        assert all(0 <= t < 30 for t in s)

    def test_record_carries_no_clock_but_ticks(self):
        rec = json.loads(hb.run(seed=2, n_seats=3, n_places=2, ticks=8)
                         .record_bytes())
        flat = json.dumps(rec)
        for word in ("time", "clock", "pid", "process", "elapsed"):
            assert word not in flat


class TestFactionAccounting:
    def test_faction_decisions_have_their_own_denominator_and_fallback(self):
        run = hb.run(seed=4, n_seats=3, n_places=2, ticks=20, beats=5)
        assert run.tally.decisions == 5
        assert run.tally.fallbacks == 0
        assert run.report()["faction"]["fallback_rate"] == 0.0
        assert "seat" not in run.report()["faction"]

    def test_an_illegal_policy_choice_is_a_counted_fallback_not_a_drop(self):
        class Illegal:
            def choose(self, tick, legal, rng):
                return ("assassinate", 0)
        run = hb.run(seed=4, n_seats=3, n_places=2, ticks=20, beats=5,
                     policy=Illegal())
        assert run.tally.decisions == 5
        assert run.tally.fallbacks == 5
        assert run.report()["faction"]["fallback_rate"] == 1.0
        assert len(run.actions) == 5, "a fallback still acts"

    def test_the_three_action_types_are_all_reachable(self):
        seen = set()
        for seed in range(10):
            run = hb.run(seed=seed, n_seats=3, n_places=2, ticks=30, beats=8)
            seen |= {a.kind for a in run.actions}
        assert seen == set(hb.ACTION_KINDS)


class TestFactTerms:
    def test_action_facts_pass_the_durf_collision_check(self):
        run = hb.run(seed=9, n_seats=3, n_places=3, ticks=40, beats=12)
        run.world.check_terms()  # raises FactError on a collision

    def test_a_colliding_term_is_refused_not_matched_cleverly(self):
        world = hb.World.build(seed=1, n_seats=2, n_places=2)
        world.add_fact(("a",), "raid@p1", "one raid@p1", tick=0)
        world.add_fact(("b",), "raid@p1#t01", "two raid@p1#t01", tick=1)
        with pytest.raises(hb.FactError):
            world.check_terms()

    def test_a_statement_without_its_own_sentinel_is_refused(self):
        """The first guard fixture shipped a text with no term in it, and the
        leak it injected audited clean. A fact whose statement cannot be matched
        is a fact the audit cannot see leave."""
        world = hb.World.build(seed=1, n_seats=2, n_places=2)
        with pytest.raises(hb.FactError, match="does not carry its term"):
            world.add_fact(("a",), "raid@p1", "the faction will raid", tick=0)
