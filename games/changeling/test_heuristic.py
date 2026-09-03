"""Tests for changeling's control-ladder middle rung.

Same three things `games/cabal/test_heuristic.py` holds, and the third first: the
policy is legal everywhere, it never falls back, and it cannot consult what the
referee did not render to it - here, above all, a seat's dawn TRUTH.
"""

from __future__ import annotations

import random
from types import SimpleNamespace

import pytest

from games.changeling.heuristic import HeuristicPolicy, accusations, self_claims
from games.changeling.night import Act
from games.changeling.player import RandomPolicy, play_game
from games.changeling.referee import ChangelingReferee, Phase
from games.changeling.roles import (BYSTANDER, DECEIVED, PACK, SPOTTER, SWAPPER,
                                    SWITCHER, DEFAULT_THEME, Side)

NAMES = DEFAULT_THEME.card_names


def _pick(*wanted):
    """A night chooser that takes the first WANTED option on offer, else the first
    legal one - so a test can state the night it means without a seed hunt."""
    def choose(seat: int, act: Act, options: list):
        for w in wanted:
            if w in options:
                return w
        return options[0]
    return choose


def _table(dealt, centre, choose=None, rounds: int = 1):
    ref = ChangelingReferee.new(5, seed=7, discussion_rounds=rounds,
                                dealt=dict(enumerate(dealt)), centre=list(centre),
                                choose=choose)
    policies = {s: HeuristicPolicy(rng=random.Random(100 + s)) for s in range(5)}
    return ref, policies


def _discuss(ref, policies, scripted: dict[int, str] | None = None):
    """Run every discussion round by hand, so a test can seat one scripted line."""
    scripted = scripted or {}
    while ref.phase is Phase.DISCUSS:
        for seat in ref.speaking_order():
            if seat in scripted:
                ref.speak(seat, scripted[seat])
            else:
                ref.speak(seat, policies[seat].act(ref, seat)["say"])
        ref.close_round()
    assert ref.phase is Phase.VOTE


# ---- legality and gate #1 ---------------------------------------------------

@pytest.mark.parametrize("seed", range(25))
def test_every_game_is_legal_and_leak_free(seed):
    ref = ChangelingReferee.new(5, seed=seed)
    policies = {s: HeuristicPolicy(rng=random.Random(seed * 10 + s))
                for s in range(5)}
    rec = play_game(ref, policies)
    assert rec.error is None
    assert rec.winner in (Side.VILLAGE.value, Side.PACK.value)
    assert rec.fallbacks == 0        # a rules bot has nothing to fall back FROM


class _Forbidden(dict):
    """A dawn-truth table that raises on any read. The policy must never need it."""

    def __getitem__(self, key):
        raise AssertionError(f"policy read dawn truth for seat {key}")

    def get(self, key, default=None):
        raise AssertionError(f"policy read dawn truth for seat {key}")


@pytest.mark.parametrize("seed", range(10))
def test_it_cannot_consult_dawn_truth(seed):
    """`play_game`'s audit checks what the REFEREE renders, not what a policy goes
    and reads, so this is the check that the policy stays inside its view: with
    the truth table replaced by one that raises, every decision must still land.
    `holds` is the only referee door onto that table and is closed the same way."""
    ref = ChangelingReferee.new(5, seed=seed, discussion_rounds=2)
    policies = {s: HeuristicPolicy(rng=random.Random(seed)) for s in range(5)}
    real_truth = ref.night.truth
    ref.night.truth = _Forbidden()
    ref.holds = lambda seat: (_ for _ in ()).throw(
        AssertionError(f"policy called holds({seat})"))
    _discuss(ref, policies)
    votes = {s: policies[s].act(ref, s)["vote"] for s in range(5)}
    ref.night.truth = real_truth
    for s, t in votes.items():
        assert t in ref.legal_votes(s)


# ---- the vote ----------------------------------------------------------------

def test_a_seat_the_night_named_as_pack_gets_the_vote():
    # seat 0 looks at seat 1 and sees the pack card; nothing moves it afterwards
    ref, policies = _table(
        [SPOTTER, PACK, BYSTANDER, BYSTANDER, DECEIVED],
        [PACK, SWAPPER, SWITCHER], choose=_pick(("seat", 1), ("centre", 1)))
    assert [k.label for k in ref.entitled_knowledge(0)] == ["pack"]
    _discuss(ref, policies)
    assert policies[0].act(ref, 0)["vote"] == 1


def test_the_pack_points_together_and_never_at_itself():
    ref, policies = _table(
        [PACK, PACK, SPOTTER, BYSTANDER, BYSTANDER],
        [SWAPPER, SWITCHER, DECEIVED], choose=_pick(("centre", (0, 1))))
    _discuss(ref, policies)
    v0, v1 = policies[0].act(ref, 0)["vote"], policies[1].act(ref, 1)["vote"]
    assert v0 == v1
    assert v0 not in (0, 1)


def test_a_pack_seat_claims_the_bystander_card_and_accuses_its_target():
    ref, policies = _table(
        [PACK, PACK, SPOTTER, BYSTANDER, BYSTANDER],
        [SWAPPER, SWITCHER, DECEIVED], choose=_pick(("centre", (0, 1))))
    said = policies[0].act(ref, 0)["say"]
    assert self_claims(said, NAMES) == {("dealt", "bystander"),
                                        ("present", "bystander")}
    (target,) = accusations(said, NAMES["pack"])
    assert target not in (0, 1)
    # the fellow, speaking later, reads the accusation and repeats it
    ref.speak(0, said)
    assert accusations(policies[1].act(ref, 1)["say"], NAMES["pack"]) == [target]


def test_a_village_seat_states_its_own_card_truthfully():
    ref, policies = _table(
        [SPOTTER, PACK, BYSTANDER, BYSTANDER, DECEIVED],
        [PACK, SWAPPER, SWITCHER], choose=_pick(("seat", 3), ("centre", 1)))
    assert self_claims(policies[0].act(ref, 0)["say"], NAMES) == {
        ("dealt", "spotter"), ("present", "spotter")}
    # the deceived seat believes the card it was dealt, and says so - a stale truth
    assert self_claims(policies[4].act(ref, 4)["say"], NAMES) == {
        ("dealt", "deceived"), ("present", "deceived")}


def test_a_claim_that_collides_with_the_seats_own_card_draws_the_vote():
    # seat 0 knows it is the spotter and saw two centre cards; seat 2 claims spotter
    ref, policies = _table(
        [SPOTTER, BYSTANDER, BYSTANDER, PACK, DECEIVED],
        [PACK, SWAPPER, SWITCHER], choose=_pick(("centre", (1, 2)), ("centre", 0)))
    _discuss(ref, policies,
             scripted={2: f"I went to sleep as the {NAMES['spotter']}."})
    assert policies[0].act(ref, 0)["vote"] == 2


def test_a_claim_to_a_card_the_seat_saw_in_the_centre_draws_the_vote():
    # seat 0 saw the swapper card in the centre; seat 1 claims to be the swapper
    ref, policies = _table(
        [SPOTTER, BYSTANDER, BYSTANDER, PACK, DECEIVED],
        [PACK, SWAPPER, SWITCHER], choose=_pick(("centre", (1, 2)), ("centre", 0)))
    _discuss(ref, policies,
             scripted={1: f"I went to sleep as the {NAMES['swapper']}."})
    assert policies[0].act(ref, 0)["vote"] == 1


def test_a_claim_that_contradicts_what_the_seat_looked_at_draws_the_vote():
    # seat 0 looked at seat 2 and saw a bystander; seat 2 then claims the switcher
    ref, policies = _table(
        [SPOTTER, BYSTANDER, BYSTANDER, PACK, DECEIVED],
        [PACK, SWAPPER, SWITCHER], choose=_pick(("seat", 2), ("centre", 0)))
    _discuss(ref, policies,
             scripted={2: f"I went to sleep as the {NAMES['switcher']}."})
    assert policies[0].act(ref, 0)["vote"] == 2


def test_a_present_claim_is_not_refuted_because_the_card_may_have_moved():
    # seat 0 (spotter, saw the centre) hears seat 2 say "I am the Seer" - which the
    # thief could truthfully say - and does not point at it for that alone
    ref, policies = _table(
        [SPOTTER, BYSTANDER, BYSTANDER, PACK, DECEIVED],
        [PACK, SWAPPER, SWITCHER], choose=_pick(("centre", (1, 2)), ("centre", 0)))
    _discuss(ref, policies, scripted={
        2: f"I went to sleep as the {NAMES['bystander']}. I am the {NAMES['spotter']}.",
        3: f"I went to sleep as the {NAMES['swapper']}."})
    assert policies[0].act(ref, 0)["vote"] == 3


def test_a_robbed_seat_is_expected_to_claim_the_card_the_thief_took():
    # seat 0 (swapper) robbed seat 1 of the spotter card; seat 1 truthfully says
    # it went to sleep as the spotter, and the thief does not point at it
    ref, policies = _table(
        [SWAPPER, SPOTTER, BYSTANDER, PACK, DECEIVED],
        [PACK, SWITCHER, BYSTANDER], choose=_pick(("seat", 1), ("centre", 0)))
    assert ref.believes(0).key == "spotter"
    _discuss(ref, policies, scripted={
        1: f"I went to sleep as the {NAMES['spotter']}.",
        2: f"I went to sleep as the {NAMES['spotter']}."})
    assert policies[0].act(ref, 0)["vote"] == 2


def test_more_deal_claims_than_the_deck_holds_puts_every_claimant_in_the_frame():
    ref, policies = _table(
        [SPOTTER, BYSTANDER, BYSTANDER, PACK, DECEIVED],
        [PACK, SWAPPER, SWITCHER], choose=_pick(("centre", (1, 2)), ("centre", 0)))
    line = f"I went to sleep as the {NAMES['bystander']}."
    _discuss(ref, policies, scripted={
        1: line, 2: line, 3: line,
        4: f"I went to sleep as the {NAMES['deceived']}."})
    assert policies[0].act(ref, 0)["vote"] in (1, 2, 3)


def test_a_blind_seat_with_nothing_to_go_on_still_votes_legally():
    ref, policies = _table(
        [BYSTANDER, PACK, SPOTTER, BYSTANDER, DECEIVED],
        [PACK, SWAPPER, SWITCHER], choose=_pick(("centre", (1, 2)), ("centre", 0)))
    _discuss(ref, policies)
    assert policies[0].act(ref, 0)["vote"] in ref.legal_votes(0)


# ---- the runner ----------------------------------------------------------------

def test_the_runner_seats_the_heuristic_without_a_backend():
    from eval.run_changeling import ARMS, build_policies
    assert "heuristic" in ARMS
    ref = ChangelingReferee.new(5, seed=3)
    args = SimpleNamespace(arm="heuristic", backend=None)
    policies = build_policies(ref, args, random.Random(3), 3)
    assert all(isinstance(p, HeuristicPolicy) for p in policies.values())
    assert len({id(p.rng) for p in policies.values()}) == 1
    assert not any(isinstance(p, RandomPolicy) for p in policies.values())
