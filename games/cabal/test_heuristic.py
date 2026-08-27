"""Tests for the control ladder's middle rung.

Three things are worth holding here, and the third is the one a reviewer should
check first: the policy is legal everywhere, it does not deadlock itself, and it
cannot see what the referee did not render to it.
"""

from __future__ import annotations

import random

import pytest

from games.cabal.heuristic import (HeuristicPolicy, hunt_by_rejections,
                                   hunt_by_votes)
from games.cabal.player import RandomPolicy, play_game
from games.cabal.referee import CabalReferee, Phase
from games.cabal.roles import (HUNTER, LOYALIST, MIMIC, SEER, SETUP_5, WATCHER,
                               Team)


def _play(seed: int, heuristic_good=True, heuristic_evil=True):
    ref = CabalReferee.new(5, seed=seed)
    policies = {}
    for s in range(5):
        use = (heuristic_good if ref.assignment[s].team is Team.GOOD
               else heuristic_evil)
        rng = random.Random(seed * 10 + s)
        policies[s] = HeuristicPolicy(rng=rng) if use else RandomPolicy(rng=rng)
    return ref, play_game(ref, policies)


# ---- legality and gate #1 ---------------------------------------------------

@pytest.mark.parametrize("seed", range(25))
def test_every_game_is_legal_and_leak_free(seed):
    """`play_game` audits gate #1 at every reachable state and raises on a leak, and
    the referee raises on any illegal move. Both are on by default, so a clean run
    over 25 seeds is the assertion."""
    ref, rec = _play(seed)
    assert rec.error is None
    assert rec.winner in ("good", "evil")
    assert rec.fallbacks == 0        # a rules bot has nothing to fall back FROM


def test_it_cannot_consult_what_it_was_not_rendered():
    """Swap two roles the acting seat has no way to tell apart, and its decisions
    must not move.

    The hunter is told one thing - which seat is its ally - so a watcher and a
    loyalist at two other seats are indistinguishable to it. Same public record,
    same entitled knowledge, different truth. A policy reaching past its view for
    `ref.assignment` would answer differently here, and nothing in `play_game`'s
    gate #1 audit would catch it: that audits what the REFEREE renders, not what a
    policy goes and reads.
    """
    # Seats 0 and 1 carry no fail, so a team of [0, 1] is one an entitled loyalist
    # APPROVES. That matters: a board where it would reject anyway hides the
    # difference the swap is supposed to expose, and an earlier version of this test
    # did exactly that and passed against the mutant.
    record = [
        ("event", "leader 0 proposes [1, 2] for mission 1"),
        ("event", "vote on [1, 2]: 3/5 approve (approved by [0, 1, 2]) -> APPROVED"),
        ("event", "mission 1 on [1, 2]: 0 fail(s), need 1 -> SUCCESS"),
        ("event", "leader 1 proposes [2, 3, 4] for mission 2"),
        ("event", "vote on [2, 3, 4]: 3/5 approve (approved by [3, 4, 0]) -> APPROVED"),
        ("event", "mission 2 on [2, 3, 4]: 1 fail(s), need 1 -> FAIL"),
    ]
    truth = {0: SEER, 1: WATCHER, 2: LOYALIST, 3: MIMIC, 4: HUNTER}

    def decide(assignment, seat, proposal, phase=Phase.VOTE):
        ref = CabalReferee(setup=SETUP_5, assignment=assignment,
                           public_events=list(record), phase=phase,
                           proposal=proposal, mission_index=2)
        return HeuristicPolicy(rng=random.Random(1)).act(ref, seat)

    # The hunter is told exactly one thing - which seat is its ally - so a watcher
    # and a loyalist elsewhere are the same seat to it.
    hunter_swap = {**truth, 1: LOYALIST, 2: WATCHER}
    assert (CabalReferee(setup=SETUP_5, assignment=truth).entitled_knowledge(4)
            == CabalReferee(setup=SETUP_5,
                            assignment=hunter_swap).entitled_knowledge(4))
    assert decide(truth, 4, (0, 3, 4)) == decide(hunter_swap, 4, (0, 3, 4))
    assert (decide(truth, 4, (0, 3, 4), Phase.HUNT)
            == decide(hunter_swap, 4, (0, 3, 4), Phase.HUNT))

    # The loyalist is told NOTHING, so every arrangement of the other four is the
    # same board to it - including one that moves the evil seats. This is the case
    # that has teeth: a policy reading `ref.assignment` for the evil pair answers
    # {3, 4} on one and {0, 4} on the other, and votes differently on a team of
    # [0, 1]. The hunter case above cannot catch that, because there the two happen
    # to agree.
    evil_moved = {**truth, 0: MIMIC, 3: SEER}
    assert (CabalReferee(setup=SETUP_5, assignment=truth).entitled_knowledge(2)
            == CabalReferee(setup=SETUP_5,
                            assignment=evil_moved).entitled_knowledge(2) == ())
    assert decide(truth, 2, (0, 1)) == decide(evil_moved, 2, (0, 1))
    assert decide(truth, 2, (0, 1))["vote"] is True   # and it is the APPROVE branch


# ---- the rules that are choices, not deductions ----------------------------

def test_the_fifth_proposal_is_approved_whatever_the_record_says():
    """A rules bot that rejects on suspicion alone loses at `five_rejects`, which is
    a bug in the bot rather than a finding about the game."""
    truth = {0: SEER, 1: WATCHER, 2: LOYALIST, 3: MIMIC, 4: HUNTER}
    record = [("event", "mission 1 on [1, 2]: 1 fail(s), need 1 -> FAIL")]
    policy = HeuristicPolicy(rng=random.Random(0))
    for rejects, expected in ((0, False), (4, True)):
        ref = CabalReferee(setup=SETUP_5, assignment=truth,
                           public_events=list(record), phase=Phase.VOTE,
                           proposal=(1, 2), reject_count=rejects)
        assert policy.act(ref, 0)["vote"] is expected


def test_good_never_plays_a_fail_and_evil_always_does():
    truth = {0: SEER, 1: WATCHER, 2: LOYALIST, 3: MIMIC, 4: HUNTER}
    ref = CabalReferee(setup=SETUP_5, assignment=truth, phase=Phase.MISSION,
                       proposal=(0, 3, 4))
    policy = HeuristicPolicy(rng=random.Random(0))
    assert policy.act(ref, 0)["card"] is False       # seer
    assert policy.act(ref, 3)["card"] is True        # mimic
    assert policy.act(ref, 4)["card"] is True        # hunter


def test_a_good_seat_still_approves_once_every_seat_carries_a_fail():
    """Regression on a measured self-inflicted loss, tested as the property rather
    than as a win rate.

    The first version rejected any team carrying a seat with a fail against it. Two
    failed missions between them touch nearly every seat, so it then rejected
    everything and handed the game over at `five_rejects` - 0.5% good wins against
    41% for the random control. The rule now rejects only the seats the record
    points at HARDEST, so a least-suspect team is still approvable.

    Written against a constructed board because the win-rate version was vacuous:
    against a RANDOM evil the broken rule still won often enough to pass a
    threshold, and it only collapses against an opponent that sabotages every time.
    """
    truth = {0: SEER, 1: WATCHER, 2: LOYALIST, 3: MIMIC, 4: HUNTER}
    record = [
        ("event", "mission 1 on [0, 1, 3]: 1 fail(s), need 1 -> FAIL"),
        ("event", "mission 2 on [2, 3, 4]: 2 fail(s), need 1 -> FAIL"),
    ]
    # every seat now carries at least one fail: 0,1 -> 1; 2,4 -> 2; 3 -> 3
    def votes(proposal):
        ref = CabalReferee(setup=SETUP_5, assignment=truth,
                           public_events=list(record), phase=Phase.VOTE,
                           proposal=proposal, mission_index=2)
        return HeuristicPolicy(rng=random.Random(0)).act(ref, 2)["vote"]

    assert votes((0, 1)) is True      # the least-charged pair is still approvable
    assert votes((0, 3)) is False     # seat 3 is what the record points at hardest


# ---- the hunt rules ---------------------------------------------------------

def _votes(*rows):
    return tuple((team, frozenset(ayes)) for team, ayes in rows)


def test_hunt_by_votes_finds_the_seat_that_tracked_taint():
    """Seat 1 rejected every tainted team and approved every clean one; seat 2 did
    the opposite; seat 0 was indifferent. The rule names seat 1."""
    votes = _votes(
        ((3, 4), {2}),          # tainted (evil is {3, 4}): 1 rejected, 2 approved
        ((0, 1), {0, 1, 2}),    # clean: 1 approved, 2 approved
        ((1, 3), {0, 2}),       # tainted: 1 rejected, 2 approved
        ((0, 2), {1, 2}),       # clean: 1 approved
    )
    assert hunt_by_votes([0, 1, 2], {3, 4}, votes) == [1]


def test_hunt_by_rejections_ignores_the_hunters_night_knowledge():
    """Its control value depends on that: whatever it scores is the tell that
    survives with NO private information, so it must not quietly use any."""
    votes = _votes(((3, 4), {2}), ((0, 1), {0, 2}), ((1, 3), {2}))
    assert hunt_by_rejections([0, 1, 2], {3, 4}, votes) == \
        hunt_by_rejections([0, 1, 2], {0, 1}, votes)
    assert hunt_by_rejections([0, 1, 2], set(), votes) == [1]   # 1 rejected twice


def test_both_rules_return_the_whole_argmax_set():
    """The tie-break belongs to the caller - `rng.choice` when seated, tie-averaged
    when scoring a corpus. A rule that picked for them would put tie-break luck
    inside every number."""
    votes = _votes(((3, 4), set()), ((0, 1), {0, 1, 2}))
    assert hunt_by_votes([0, 1, 2], {3, 4}, votes) == [0, 1, 2]
    assert hunt_by_rejections([0, 1, 2], {3, 4}, votes) == [0, 1, 2]


def test_the_seated_hunt_only_ever_names_a_legal_target():
    for seed in range(25):
        ref, rec = _play(seed)
        if rec.hunt:
            assert rec.hunt["target"] in ref.legal_hunt_targets(rec.hunt["hunter"])
