"""Session 0: seats draft playbooks in turn, and a taken pick is an illegal move."""

import pytest

from games.ensemble.draft import Draft, NotEnoughPlaybooks


NAMES = ("A", "B", "C", "D")


def test_every_seat_ends_with_a_distinct_playbook():
    d = Draft(NAMES, seats=3, seed=1)
    while not d.done:
        d.offer()
        d.take(d.remaining()[0])
    assert len(set(d.picks.values())) == 3
    assert set(d.picks) == {0, 1, 2}


def test_the_menu_shrinks_as_seats_take():
    d = Draft(NAMES, seats=2, seed=1)
    d.offer(); d.take("B")
    assert "B" not in d.remaining()


def test_a_taken_pick_is_a_fallback_and_still_yields_a_legal_playbook():
    d = Draft(NAMES, seats=2, seed=1)
    d.offer(); d.take("A")
    d.offer(); d.take("A")
    assert d.fallbacks == 1
    assert d.picks[1] != "A"
    assert d.picks[1] in NAMES


def test_an_unknown_name_is_a_fallback():
    d = Draft(NAMES, seats=1, seed=1)
    d.offer(); d.take("NOT A PLAYBOOK")
    assert d.fallbacks == 1
    assert d.picks[0] in NAMES


def test_a_legal_pick_is_not_counted_as_a_fallback():
    d = Draft(NAMES, seats=1, seed=1)
    d.offer(); d.take("C")
    assert d.fallbacks == 0
    assert d.picks[0] == "C"


def test_the_same_seed_drafts_the_same_way():
    def run():
        d = Draft(NAMES, seats=3, seed=99)
        while not d.done:
            d.offer(); d.take("A")       # every seat after the first falls back
        return d.picks, d.fallbacks
    assert run() == run()


def test_a_different_seed_can_draft_differently():
    def run(seed):
        d = Draft(NAMES, seats=3, seed=seed)
        while not d.done:
            d.offer(); d.take("A")
        return d.picks
    assert any(run(s) != run(1) for s in range(2, 40))


def test_fewer_playbooks_than_seats_raises_rather_than_seating_a_duplicate():
    with pytest.raises(NotEnoughPlaybooks):
        Draft(("A", "B"), seats=3, seed=1)


def test_taking_before_offering_raises():
    d = Draft(NAMES, seats=1, seed=1)
    with pytest.raises(RuntimeError):
        d.take("A")


def test_distribution_records_every_seat_in_turn_order():
    d = Draft(NAMES, seats=3, seed=1)
    order = []
    while not d.done:
        order.append(d.offer())
        d.take(d.remaining()[0])
    assert order == [0, 1, 2]
