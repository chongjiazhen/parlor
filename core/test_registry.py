"""One command over the games, and the two things it must not do.

The registry's job is small - a player should be able to find a game without
knowing which module it lives in. What matters is what it leaves alone. It must
hand a game's own flags to that game untouched, because the moment this layer
starts interpreting them it can change what a seat is sent, and both games'
recorded numbers were measured through the drivers as they stand. And it must
only name rungs a person can actually sit at, since a name in ``--list`` that
answers ``--human`` with a traceback is worse than an absent one.
"""

from __future__ import annotations

import sys
from importlib import import_module

import pytest

from core import registry
from core.registry import RUNGS, Rung, UnknownRung, listing, lookup
from parlor.__main__ import main as cli


# ---- the table itself ---------------------------------------------------

def test_every_registered_rung_resolves_to_a_callable_driver():
    """Catches a renamed or moved demo at test time rather than at the moment a
    player types its name."""
    for name, rung in RUNGS.items():
        assert callable(rung.driver()), name


def test_every_registered_rung_seats_a_person():
    """The registration line, asserted rather than described.

    A rung belongs here when it has a console seat - not when it is the right
    genre. ``durf`` is absent for exactly this reason and would pass any test
    that only asked whether it was a game; it fails this one, because nothing in
    it imports a console. When it grows one it registers beside the others.
    """
    for name, rung in RUNGS.items():
        mod = import_module(rung.module)
        assert hasattr(mod, "human_seats"), name
        assert hasattr(mod, "ConsoleBackend"), name


def test_listing_names_every_rung():
    text = listing()
    for name in RUNGS:
        assert name in text


def test_unknown_rung_names_what_is_registered():
    with pytest.raises(UnknownRung) as exc:
        lookup("nosuch")
    for name in RUNGS:
        assert name in str(exc.value)


def test_a_driver_with_no_main_is_refused_by_name():
    """``core.registry`` imports fine and has no ``main``, which is the shape a
    stale entry has: the module is there, the entry point is not."""
    rung = Rung("stale", "core.registry", "points at a module with no main")
    with pytest.raises(UnknownRung) as exc:
        rung.driver()
    assert "stale" in str(exc.value)
    assert "main()" in str(exc.value)


# ---- dispatch -----------------------------------------------------------

class _Spy:
    def __init__(self, boom=False):
        self.argv = None
        self.boom = boom

    def __call__(self):
        self.argv = list(sys.argv)
        if self.boom:
            raise RuntimeError("the game blew up")


@pytest.fixture
def spy(monkeypatch):
    s = _Spy()
    monkeypatch.setitem(RUNGS, "spy", Rung("spy", "core.registry", "a fake rung"))
    monkeypatch.setattr(Rung, "driver", lambda self: s)
    return s


def test_play_hands_the_game_its_own_command_line(spy):
    assert cli(["play", "spy", "--seed", "7", "--human", "0"]) == 0
    assert spy.argv[1:] == ["--seed", "7", "--human", "0"]


def test_the_usage_line_names_the_command_the_player_typed(spy):
    cli(["play", "spy", "--help"])
    assert spy.argv[0] == "parlor play spy"


def test_a_flag_this_layer_owns_still_reaches_the_game(spy):
    """``--list`` is ours before a game name and the game's after one. If this
    layer ever claims it in the tail, a game that grows a ``--list`` of its own
    silently stops receiving it."""
    cli(["play", "spy", "--list"])
    assert spy.argv[1:] == ["--list"]


def test_argv_is_restored_after_a_game_that_raises(monkeypatch):
    s = _Spy(boom=True)
    monkeypatch.setitem(RUNGS, "spy", Rung("spy", "core.registry", "a fake rung"))
    monkeypatch.setattr(Rung, "driver", lambda self: s)
    before = list(sys.argv)
    with pytest.raises(RuntimeError):
        cli(["play", "spy", "--seed", "1"])
    assert sys.argv == before


# ---- the command surface ------------------------------------------------

def test_list_works_before_and_after_the_verb(capsys):
    assert cli(["--list"]) == 0
    first = capsys.readouterr().out
    assert cli(["play", "--list"]) == 0
    assert capsys.readouterr().out == first


def test_no_arguments_prints_usage(capsys):
    assert cli([]) == 0
    assert "usage:" in capsys.readouterr().out


def test_play_with_no_game_is_an_error(capsys):
    assert cli(["play"]) == 2
    assert "usage:" in capsys.readouterr().err


def test_an_unknown_verb_is_an_error(capsys):
    assert cli(["score", "cabal"]) == 2
    assert "score" in capsys.readouterr().err
