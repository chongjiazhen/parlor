"""The deterministic half: the arithmetic, the refusals, and what it must not print.

Every rule tested here comes from ``docs/durf-rung.md`` §The kernel, pinned to
DURF 2.2 (2021). The last test in this file is not about arithmetic at all - it is
gate #1 reaching into the kernel, because a result line that printed an NPC's Skill
would leak a world fact that no reveal ever declared.
"""

from __future__ import annotations

import random

import pytest

from games.durf import facts, kernel


def fixed(*rolls):
    """A kernel whose dice are a scripted sequence, so an assertion is arithmetic.

    A seeded rng would make each of these tests a statement about a seed rather
    than about a rule, and a re-seed would then silently re-baseline them.
    """
    k = kernel.load(seed=0)
    queue = list(rolls)
    k.d = lambda sides: queue.pop(0)
    return k


def test_an_action_roll_succeeds_over_fifteen_and_not_on_it():
    k = fixed(13)                       # Ola DEX 3 -> 16, over 15
    assert "success" in k.call_roll(1, "DEX")
    k = fixed(12)                       # -> 15 exactly, which is not over
    assert "failure" in k.call_roll(1, "DEX")


def test_a_close_combat_tie_goes_to_the_attacker_and_not_to_the_defender():
    """The rules give ties three different answers; this is the close-combat one."""
    # Vesh STR 3 on a d20 of 15 -> 18; the rats' Skill 2 on a d20 of 16 -> 18.
    attacking = fixed(15, 16)
    assert "success" in attacking.call_roll(0, "STR", vs="barrow-rats")

    defending = fixed(15, 16)
    assert "failure" in defending.call_roll(0, "STR", vs="barrow-rats",
                                            defending=True)


def test_armour_is_a_depleting_pool_and_the_remainder_lands_as_wounds():
    k = fixed(6)                        # the HD roll after the wound
    line = k.call_damage(0, 5)          # Vesh: 3 Armor points
    assert k.pcs[0].armor_points == 0
    assert k.pcs[0].wounds == 2
    assert "3 soaked" in line


def test_a_shield_never_reduces_damage_below_one():
    k = fixed(6)
    k.call_damage(0, 1, shield=True)
    assert k.pcs[0].armor_points == 2, "1 damage, shielded to 1, soaked by armour"


def test_direct_damage_bypasses_the_armour_pool():
    k = fixed(6)
    k.call_damage(0, 4, direct=True)
    assert k.pcs[0].armor_points == 3 and k.pcs[0].wounds == 4


def test_the_death_check_is_at_or_under_wounds_and_zero_hd_dies_to_any_wound():
    k = fixed(2)                        # 1 HD rolls 2, against 2 Wounds -> death
    k.call_damage(0, 5)
    assert k.pcs[0].dead

    k = fixed(3)                        # 1 HD rolls 3, against 2 Wounds -> lives
    k.call_damage(0, 5)
    assert not k.pcs[0].dead


def test_pushing_needs_an_empty_slot_and_costs_one():
    k = kernel.load(seed=0)
    with pytest.raises(kernel.IllegalCall, match="no empty slot"):
        k.call_push(0)                  # Vesh is at 13/13
    before = k.pcs[1].slots_free
    k.call_push(1)
    assert k.pcs[1].slots_free == before - 1 and k.pcs[1].stress == 1
    assert k.pcs[1].buffs == 1


def test_a_buff_is_spent_by_the_next_roll_whether_it_lands_or_not():
    k = kernel.load(seed=0)
    k.call_push(1)
    rolls = iter([1, 6])                # d20 = 1, then the Buff's d6 = 6
    k.d = lambda sides: next(rolls)
    k.call_roll(1, "DEX")
    assert k.pcs[1].buffs == 0


def test_casting_checks_every_precondition_the_rules_name():
    k = kernel.load(seed=0)
    with pytest.raises(kernel.IllegalCall, match="does not know"):
        k.call_cast(2, "Fireball")
    k.call_token(2, "gagged by the wight's grave-wrappings")
    with pytest.raises(kernel.IllegalCall, match="cannot speak"):
        k.call_cast(2, "Pippi's Slumber")


def test_a_token_writes_nothing_public_because_it_carries_no_entitlement():
    k = kernel.load(seed=0)
    assert k.call_token(2, "gagged") == ""
    assert k.public == []


def test_morale_breaks_on_higher_than_ml_and_holds_on_equal():
    k = fixed(3, 3)                     # 2d6 = 6 against the rats' ML 6
    assert "hold their ground" in k.call_morale("barrow-rats")
    k = fixed(3, 4)                     # 7, over 6
    assert "break" in k.call_morale("barrow-rats")


def test_the_clock_is_kernel_evaluated_and_a_one_is_an_encounter():
    k = fixed(1, 5)
    line = k.call_tick(2)
    assert k.elapsed_turns == 6 and k.encounters == 1
    assert "wandering encounter" in line


def test_an_unrecognised_call_raises_rather_than_being_dropped():
    """``docs/action-channel.md``: a dropped call is indistinguishable from one
    the model never emitted, so a broken session reads as a quiet one."""
    k = kernel.load(seed=0)
    with pytest.raises(kernel.IllegalCall, match="unknown call"):
        k.execute({"call": "teleport", "room": "R4"})
    with pytest.raises(kernel.IllegalCall, match="does not take those arguments"):
        k.execute({"call": "tick", "hours": 3})
    assert k.public == [], "a refused call must write nothing"


def test_the_blocking_ask_is_not_a_kernel_call():
    """It sits in the envelope beside ``calls`` because the kernel owns state and
    cannot perform a round trip. This is the loud failure that keeps that split
    honest rather than a comment claiming it."""
    k = kernel.load(seed=0)
    with pytest.raises(kernel.IllegalCall, match="unknown call"):
        k.execute({"call": "ask", "seat": 1, "question": "what do you see?"})


def test_entering_a_room_reveals_its_contents_and_only_its_contents():
    k = kernel.load(seed=0)
    k.call_move("R2")
    assert ("room", "R2") in k.ledger.revealed
    assert ("hidden", "R2") not in k.ledger.revealed, (
        "arriving somewhere shows what is in it, never what is hidden in it")


def test_no_public_line_carries_an_npc_statistic():
    """Gate #1, reaching into the kernel.

    The party sees totals and outcomes; an NPC's Skill, ML and attack description
    are world facts that reach them through a declared reveal or not at all. The
    fact set carries those strings as sentinels so this test can be a scan rather
    than a promise.
    """
    k = kernel.load(seed=1)
    k.execute({"call": "move", "room": "R3"})
    for _ in range(8):
        k.execute({"call": "roll", "seat": 1, "attribute": "DEX",
                   "vs": "barrow-rats"})
        k.execute({"call": "morale", "group": "barrow-rats"})
        k.execute({"call": "damage", "seat": 1, "amount": 2})
        if k.pcs[1].dead:
            break
    corpus = "\n".join(k.public)
    hits = facts.find_fact_leaks(corpus, k.ledger.secret_terms(),
                                 k.ledger.entitled)
    assert hits == [], f"the kernel published a world fact: {hits}"


def test_the_seed_reaches_every_die():
    a = kernel.load(seed=99)
    b = kernel.load(seed=99)
    calls = [{"call": "roll", "seat": 1, "attribute": "DEX"},
             {"call": "tick", "turns": 3},
             {"call": "morale", "group": "barrow-rats"}]
    assert [a.execute(c) for c in calls] == [b.execute(c) for c in calls]
    other = kernel.load(seed=100)
    assert [other.execute(c) for c in calls] != [
        kernel.load(seed=99).execute(c) for c in calls]


def test_a_dead_character_takes_no_further_actions():
    k = fixed(1)
    k.call_damage(0, 9)
    assert k.pcs[0].dead
    with pytest.raises(kernel.IllegalCall, match="is dead"):
        k.call_roll(0, "STR")


def test_the_fixture_state_and_the_slot_arithmetic_agree():
    """``fixtures/README.md`` records that three of the six traps once turned on a
    ``slots_free`` nobody could reproduce. The kernel loads that same state, so it
    is the place the arithmetic is held."""
    k = kernel.load(seed=0)
    assert k.pcs[0].slots_free == 0     # Vesh, and d013/d017 turn on it
    assert k.pcs[1].slots_free == 4     # Ola, and d018's fifth push turns on it
    for pc in k.pcs.values():
        assert pc.slots_total == 10 + pc.STR
        assert pc.slots_used <= pc.slots_total


def test_the_rng_is_not_shared_with_the_declaration_fixture(monkeypatch):
    """Two kernels at the same seed roll the same dice; one kernel's rolls never
    reach into module state something else reads."""
    a, b = kernel.load(seed=5), kernel.load(seed=5)
    a.d(20)
    assert b.d(20) == random.Random(5).randint(1, 20)
