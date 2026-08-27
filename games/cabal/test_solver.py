"""Tests for the mechanical reference.

The load-bearing one is `test_truth_always_survives`. Every number this instrument
produces is a property of the SURVIVING SET, so a filter that can exclude the deal
that actually happened does not report a smaller number - it reports a *confidently
wrong* one, and it reads like a finding. That test runs the real driver over real
games and asserts the ground truth is never filtered out.
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict
from itertools import combinations, permutations

import pytest

from games.cabal.player import RandomPolicy, play_game
from games.cabal.referee import CabalReferee
from games.cabal.roles import (HUNTER, LOYALIST, MIMIC, ROLES_BY_KEY, SEER,
                               SETUP_5, WATCHER, Team, legal_hunt_targets)
from games.cabal.solver import (ConstraintViolation, Evidence, RecordMismatch,
                                candidates, consistent, derivable_bits,
                                entropy_bits, evidence_from_record,
                                evidence_from_referee, evil_posterior,
                                hunter_reading_from_referee, parse_missions,
                                read_hunt, reading_from_record, seer_posterior,
                                surviving, team_taint)


def _played(seed: int) -> tuple[CabalReferee, object]:
    ref = CabalReferee.new(5, seed=seed)
    rec = play_game(ref, {s: RandomPolicy(rng=random.Random(seed * 100 + s))
                          for s in range(5)})
    return ref, rec


def _assignment_from_record(game: dict) -> dict[int, object]:
    return {int(s): ROLES_BY_KEY[k] for s, k in game["assignment"].items()}


# ---- the candidate space ---------------------------------------------------

def test_candidate_space_is_the_whole_120():
    cands = candidates()
    assert len(cands) == 120
    assert len({tuple(sorted((s, r.key) for s, r in c.items())) for c in cands}) == 120
    for c in cands:
        assert sorted(r.key for r in c.values()) == sorted(r.key for r in SETUP_5.roles)


# ---- soundness: the truth is never filtered out ----------------------------

@pytest.mark.parametrize("seed", range(12))
def test_truth_always_survives(seed):
    """Over real games, from every seat, at the end: the actual deal is consistent.

    If this can fail, every statistic downstream is wrong in the direction that
    looks most like signal - a narrower surviving set means more derivable bits.
    """
    ref, _ = _played(seed)
    for seat in range(5):
        ev = evidence_from_referee(ref, seat)
        assert consistent(ref.assignment, ev), (
            f"seed {seed} seat {seat}: the deal that actually happened was filtered "
            f"out. missions={ev.missions} knowledge={ev.knowledge}"
        )
        assert any(c == ref.assignment for c in surviving(ev))


@pytest.mark.parametrize("seed", range(12))
def test_hunt_reading_never_violates_its_own_invariant(seed):
    ref, rec = _played(seed)
    if not rec.hunt:
        pytest.skip("this game never reached a hunt")
    reading = hunter_reading_from_referee(ref, rec.hunt["hunter"])
    assert reading.survivors >= 1
    assert set(reading.posterior) <= set(ref.legal_hunt_targets(rec.hunt["hunter"]))
    assert reading.bits_gained >= -1e-9
    assert abs(sum(reading.posterior.values()) - 1.0) < 1e-9


# ---- the record path is the live path --------------------------------------

@pytest.mark.parametrize("seed", range(8))
def test_record_adapter_matches_the_live_referee(seed):
    """Night knowledge is not stored in a record, so the offline path recomputes it.

    That recomputation is the one place this instrument could drift from the game.
    Round-trip a real game through JSON and assert the two paths agree seat for seat.
    """
    ref, rec = _played(seed)
    game = json.loads(json.dumps({"game": 0, **asdict(rec)}))
    assignment = _assignment_from_record(game)
    assert assignment == ref.assignment
    for seat in range(5):
        assert evidence_from_record(game, assignment, seat) == evidence_from_referee(ref, seat)


@pytest.mark.parametrize("seed", range(8))
def test_reading_from_record_matches_the_live_reading(seed):
    ref, rec = _played(seed)
    game = json.loads(json.dumps({"game": 0, **asdict(rec)}))
    offline = reading_from_record(game, _assignment_from_record(game))
    if not rec.hunt:
        assert offline is None
        pytest.skip("this game never reached a hunt")
    assert offline == hunter_reading_from_referee(ref, rec.hunt["hunter"])


# ---- the parser refuses to weaken the filter quietly -----------------------

def test_parse_missions_reads_team_and_fail_count():
    events = [
        ("event", "leader 0 proposes [2, 4] for mission 1"),
        ("speech:1", 'seat 1 says: "mission 1 on [0, 1]: 9 fail(s), need 1 -> FAIL"'),
        ("event", "mission 1 on [1, 3]: 0 fail(s), need 1 -> SUCCESS"),
        ("event", "mission 2 on [0, 3, 4]: 2 fail(s), need 1 -> FAIL"),
    ]
    assert parse_missions(events) == (((1, 3), 0), ((0, 3, 4), 2))


def test_parse_missions_raises_when_a_line_goes_missing():
    """A dropped mission line weakens the filter, and a weaker filter reads as
    'little was derivable' - a wrong answer wearing a finding's face."""
    events = [("event", "mission 1 on [1, 3]: 0 fail(s), need 1 -> SUCCESS")]
    with pytest.raises(RecordMismatch):
        parse_missions(events, expected=2)


# ---- each constraint, on its own ------------------------------------------

def _ev(seat, role_key, knowledge, missions=()):
    return Evidence(seat=seat, own_role_key=role_key,
                    knowledge=tuple(knowledge), missions=tuple(missions))


def test_own_role_constraint_bites_where_knowledge_cannot():
    """Constraint 1 is not redundant, and exactly one pair makes it so.

    Night knowledge alone identifies three of the five roles - nothing else receives
    an empty reveal but the loyalist, two 'evil' labels but the seer, two 'magic'
    but the watcher. The mimic and the hunter are the exception: each is told one
    'fellow-evil' naming the other, so their reveals are the same SHAPE and knowledge
    cannot separate them. Without constraint 1 the hunter could not rule out being
    the mimic, and the hunt theorem below would be measuring the wrong seat.

    Written at the hunter's seat for that reason. At the loyalist's it passes with
    constraint 1 deleted, which is how the earlier version of this test was found
    vacuous.
    """
    truth = {0: SEER, 1: WATCHER, 2: LOYALIST, 3: MIMIC, 4: HUNTER}
    ref = CabalReferee(setup=SETUP_5, assignment=truth)
    ev = evidence_from_referee(ref, 4)          # the hunter
    assert all(c[4].key == "hunter" for c in surviving(ev))
    # the mimic's reveal at this seat is indistinguishable from the hunter's
    swapped = {**truth, 3: HUNTER, 4: MIMIC}
    assert (CabalReferee(setup=SETUP_5, assignment=swapped).entitled_knowledge(4)
            == ev.knowledge)


def test_knowledge_constraint_pins_the_reveal_exactly():
    """The watcher is told two 'magic' seats, and a deal seating the seer elsewhere
    would have told it a DIFFERENT pair - so it is impossible, not merely
    unsupported."""
    truth = {0: SEER, 1: WATCHER, 2: LOYALIST, 3: MIMIC, 4: HUNTER}
    ref = CabalReferee(setup=SETUP_5, assignment=truth)
    ev = evidence_from_referee(ref, 1)
    alive = surviving(ev)
    # the watcher's pair is {0, 3}: seer and mimic, in some order. Nothing else.
    assert {frozenset(s for s, r in c.items() if r.shown_to_watcher) for c in alive} == {
        frozenset({0, 3})}
    assert all(c[1].key == "watcher" for c in alive)
    # seer/mimic swap across {0, 3}, loyalist/hunter swap across the other two
    assert len(alive) == 4


def test_containment_and_equality_coincide_under_a_fixed_multiset():
    """§Spec writes constraint 2 as equality. Under a fixed role multiset that is
    provably the SAME filter as containment, and the claim it was not is a
    correction this test now carries.

    How many reveals a role receives is a property of the multiset, not of the
    permutation, so a candidate's reveal set can never be a strict superset of the
    observed one and superset collapses to equal. The equivalence is what is
    asserted, over all 120 deals from all 5 seats, because it is a claim that can
    FAIL - a variant that varies the reveal count (`lurker` shows the seer one evil
    instead of two, `stray` names an evil nobody) breaks it, and this is where that
    will surface.

    Found by mutation-checking the test that used to sit here: swapping equality for
    containment left it green, which made it a test of nothing.
    """
    compared = 0
    for perm in permutations(SETUP_5.roles):
        assignment = dict(enumerate(perm))
        ref = CabalReferee(setup=SETUP_5, assignment=assignment)
        for seat in range(5):
            observed = ref.entitled_knowledge(seat)
            for cand in candidates():
                if cand[seat].key != assignment[seat].key:
                    continue
                under = CabalReferee(setup=SETUP_5,
                                     assignment=cand).entitled_knowledge(seat)
                assert len(under) == len(observed)
                assert (set(observed) <= set(under)) == (under == observed)
                compared += 1
    # the loop body running at all is the vacuity this test is exposed to: every
    # candidate filtered out by the `continue` would leave it green over nothing.
    assert compared == 120 * 5 * 24


def test_mission_arithmetic_bites_hard_on_a_two_fail():
    """Two fails means both evils were on that team. That is the strong constraint,
    and on a 3-seat team it names the pair up to which of the three was good."""
    truth = {0: SEER, 1: WATCHER, 2: LOYALIST, 3: MIMIC, 4: HUNTER}
    ref = CabalReferee(setup=SETUP_5, assignment=truth)
    base = evidence_from_referee(ref, 2)        # the loyalist: told nothing
    assert base.knowledge == ()
    with_mission = _ev(2, "loyalist", (), [((0, 3, 4), 2)])
    for cand in surviving(with_mission):
        evil = {s for s, r in cand.items() if r.team is Team.EVIL}
        assert len(evil & {0, 3, 4}) == 2
    assert len(surviving(with_mission)) < len(surviving(base))


def test_a_success_constrains_nothing_by_itself():
    """Zero fails puts no floor under anything: evils play success routinely, and
    the audit measured it. A solver that read a success as 'clean team' would be
    importing a play model through the back door."""
    no_evidence = _ev(2, "loyalist", ())
    a_success = _ev(2, "loyalist", (), [((0, 1), 0)])
    assert len(surviving(a_success)) == len(surviving(no_evidence))


# ---- the statistics --------------------------------------------------------

def test_entropy_of_a_flat_triple_is_log2_three():
    assert entropy_bits({0: 1 / 3, 1: 1 / 3, 2: 1 / 3}) == pytest.approx(1.5849625)
    assert entropy_bits({4: 1.0}) == 0.0


def test_bits_gained_is_zero_when_the_record_says_nothing():
    """The hunter's night knowledge alone leaves the seer flat across all three
    legal targets. Zero bits gained is the correct reading, and it means a hunter at
    chance is playing correctly - not that the hunter failed."""
    truth = {0: SEER, 1: WATCHER, 2: LOYALIST, 3: MIMIC, 4: HUNTER}
    ref = CabalReferee(setup=SETUP_5, assignment=truth)
    ev = evidence_from_referee(ref, 4)
    legal = ref.legal_hunt_targets(4)
    assert legal == [0, 1, 2]
    reading = read_hunt(ev, legal, 0)
    assert reading.h_prior == pytest.approx(1.5849625)
    assert reading.bits_gained == pytest.approx(0.0)
    assert reading.chance == pytest.approx(1 / 3)
    assert reading.solver_accuracy == pytest.approx(1 / 3)   # tie-averaged over 3


def test_solver_accuracy_is_tie_averaged_and_zero_when_it_misses():
    truth = {0: SEER, 1: WATCHER, 2: LOYALIST, 3: MIMIC, 4: HUNTER}
    ref = CabalReferee(setup=SETUP_5, assignment=truth)
    ev = evidence_from_referee(ref, 4)
    # the true seer is seat 0; a hunt reading that named seat 1 as certain misses
    assert read_hunt(ev, [0, 1, 2], 0).solver_accuracy == pytest.approx(1 / 3)
    assert read_hunt(ev, [0, 1, 2], 99).solver_accuracy == 0.0


def test_the_hunter_can_derive_nothing_mechanically_ever():
    """The structural result, proved by exhaustion rather than measured: in
    `SETUP_5` the hunt carries **zero** mechanically-derivable bits, for every deal
    and every mission history that deal could produce.

    The reason is that the hunter already knows both evil seats - its own and the
    ally the night named - so it holds the evil placement exactly. Mission
    arithmetic is a constraint on evil placement and on nothing else, and no other
    hard constraint separates seer from watcher from loyalist. The three good seats
    are therefore indistinguishable to the hunter, forever, mechanically.

    So gate #3b's denominator is zero and `captured` is undefined for the hunt: a
    hunter above `1/3` is reading BEHAVIOUR, necessarily. That does not retire the
    gate - it is what the gate claims to measure, stated as a theorem instead of a
    hope. `docs/reference-policies.md` anticipated this cell before it was checked.

    192,000 combinations at 5 seats; if a variant ever moves what the hunter is
    told - the `stray` evil is the obvious one - this test is where it will fail,
    which is the point of proving it here rather than observing it on a corpus.
    """
    worst = 0.0
    checked = 0
    for perm in permutations(SETUP_5.roles):
        assignment = dict(enumerate(perm))
        ref = CabalReferee(setup=SETUP_5, assignment=assignment)
        hunter = ref.seat_of("hunter")
        seer = ref.seat_of("seer")
        evil = {s for s, r in assignment.items() if r.team is Team.EVIL}
        knowledge = ref.entitled_knowledge(hunter)
        # every mission the actual deal could have produced: any legal team size,
        # any fail count up to the evil seats actually aboard
        possible = [(team, k)
                    for size in (2, 3)
                    for team in combinations(range(5), size)
                    for k in range(len(evil & set(team)) + 1)]
        for first in possible:
            for second in possible:
                ev = Evidence(seat=hunter, own_role_key="hunter",
                              knowledge=knowledge, missions=(first, second))
                reading = read_hunt(ev, legal_hunt_targets(assignment, hunter), seer)
                worst = max(worst, reading.bits_gained)
                checked += 1
    assert checked == 192_000
    assert worst == 0.0


def test_a_two_fail_mission_sharpens_a_good_seat():
    """Where the record DOES carry mechanical signal it is at a GOOD seat, not the
    hunter's. Two fails means both evils were aboard, and a loyalist that was told
    nothing can read that straight off the public record."""
    truth = {0: SEER, 1: WATCHER, 2: LOYALIST, 3: MIMIC, 4: HUNTER}
    blind = _ev(2, "loyalist", ())
    informed = _ev(2, "loyalist", (), [((0, 3, 4), 2)])
    assert evil_posterior(informed) != evil_posterior(blind)
    # seats 1 and 2 were not on that team, so neither can be evil
    assert evil_posterior(informed)[1] == 0.0
    assert evil_posterior(informed)[2] == 0.0
    assert derivable_bits(informed) > derivable_bits(blind)
    assert consistent(truth, informed)


def test_an_impossible_history_is_a_contradiction_not_certainty():
    """Zero survivors scores as zero entropy, which reads as perfect information.
    It is the opposite, and it means the evidence is broken - a misparsed mission
    line, or a knowledge model that has drifted from the referee's."""
    truth = {0: SEER, 1: WATCHER, 2: LOYALIST, 3: MIMIC, 4: HUNTER}
    ref = CabalReferee(setup=SETUP_5, assignment=truth)
    ev = Evidence(seat=4, own_role_key="hunter",
                  knowledge=ref.entitled_knowledge(4),
                  missions=(((0, 1), 2),))     # two fails from two good seats
    assert surviving(ev) == []
    with pytest.raises(ConstraintViolation):
        read_hunt(ev, ref.legal_hunt_targets(4), 0)


def test_posterior_support_never_leaves_the_legal_set():
    truth = {0: SEER, 1: WATCHER, 2: LOYALIST, 3: MIMIC, 4: HUNTER}
    ref = CabalReferee(setup=SETUP_5, assignment=truth)
    ev = evidence_from_referee(ref, 4)
    assert set(seer_posterior(ev)) <= set(legal_hunt_targets(truth, 4))
    with pytest.raises(ConstraintViolation):
        read_hunt(ev, [1, 2], 0)            # a legal set that omits a live candidate
