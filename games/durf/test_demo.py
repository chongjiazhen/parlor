"""What a person sitting in a DURF party seat is allowed to see.

The rung's own gate #1 tests live in ``test_session.py`` and grade what the
REFEREE renders to a seat. This file grades the other half, which that audit
cannot see: the driver itself. A console seat receives ``Session.deliver``'s
bytes and the audit stands behind them - but the harness prints around the game
too, and a driver that prints the referee's world for the reader's benefit hands
over, in one screen, everything the audit spends the session withholding.

So the guard here is one sentence: **a person playing a seat never has an
undeclared world fact printed at them**, by the game or by the driver. It is
mutation-checked - ``opening_view`` without its human branch fails
``test_the_opening_view_withholds_the_referees_world_from_a_person`` and nothing
else, so the test attributes the guard it holds.
"""

from __future__ import annotations

import io
import json
import random

import pytest

from core import registry
from core.console import TooManyHumans
from games.durf import demo, seats, session as session_mod

#: Terms from ``fixtures/facts.json`` that no seat is entitled to at the start of
#: a session: the cavity under the antechamber floor, the rotted anchor, how the
#: sarcophagus opens, and what is in the rooms the party has not entered.
UNDECLARED_TERMS = (
    "shallow cavity", "40 GP", "anchor is rotted", "under two people at once",
    "counterweighted", "hidden catch", "stone bier", "iron door",
    "twenty-foot chasm", "rope bridge", "barrow-wight standing over it",
    "sealed stone sarcophagus", "chill touch", "ML 10",
)


def args(**over):
    """The driver's own defaults, so a test cannot pass against a flag set the
    command line does not produce."""
    parsed = demo.parser().parse_args([])
    for key, value in over.items():
        setattr(parsed, key, value)
    return parsed


def undeclared_in(text: str) -> list[str]:
    low = text.lower()
    return [t for t in UNDECLARED_TERMS if t.lower() in low]


# ---- the registry entry ---------------------------------------------------

def test_the_registry_resolves_this_rung():
    """A name in ``--list`` that answers ``--human`` with an error is worse than
    an absent one, so registering durf and having a console seat are one change."""
    assert registry.lookup("durf").driver() is demo.main
    assert "durf" in registry.listing()


def test_the_registry_summary_says_what_is_secret_here():
    """The other four rungs hide a seat's secret. This one hides the world, which
    is the sentence a person choosing a rung needs."""
    assert "world" in registry.lookup("durf").summary.lower()


# ---- seating --------------------------------------------------------------

def test_a_human_seat_outside_the_table_is_refused():
    session = session_mod.new(seed=7)
    with pytest.raises(SystemExit) as caught:
        demo.build_players(session, args(human="7"), random.Random(0))
    assert "0..2" in str(caught.value)


def test_two_human_seats_are_refused_because_a_terminal_is_one_channel():
    session = session_mod.new(seed=7)
    with pytest.raises(TooManyHumans):
        demo.build_players(session, args(human="0 1"), random.Random(0))


def test_the_named_seat_is_the_console_and_the_rest_stay_scripted():
    session = session_mod.new(seed=7)
    players = demo.build_players(session, args(human="1"), random.Random(0))
    assert isinstance(players[1].backend, demo.DurfConsole)
    assert isinstance(players[0], seats.ScriptedPlayer)
    assert isinstance(players[2], seats.ScriptedPlayer)


def test_a_run_with_no_human_seats_nobody():
    session = session_mod.new(seed=7)
    players = demo.build_players(session, args(), random.Random(0))
    assert all(isinstance(p, seats.ScriptedPlayer) for p in players.values())


# ---- THE GUARD ------------------------------------------------------------

def test_the_opening_view_withholds_the_referees_world_from_a_person():
    """The guard, and the reason this file exists.

    ``referee_view`` lists every undeclared fact by id AND by text. Printed for a
    reader of a scripted run it is the whole point of the driver; printed beside
    a person playing a seat it is the leak, and the session's audit cannot see it
    because the referee never rendered it to anyone.
    """
    session = session_mod.new(seed=7)
    assert undeclared_in(demo.opening_view(session, humans=set())), (
        "the reader's peek is supposed to carry the undeclared world - a test "
        "that passes because the peek is empty proves nothing")
    assert undeclared_in(demo.opening_view(session, humans={0})) == []


def test_the_withheld_view_says_so_rather_than_printing_nothing():
    """A silent withholding reads as a broken driver. It says whose seat it is
    and that the peek is held back - and "withheld" is a word ``referee_view``
    does not contain, so this cannot pass on the unguarded text."""
    text = demo.opening_view(session_mod.new(seed=7), humans={2})
    assert "seat 2" in text and "withheld" in text


def test_a_console_seat_is_handed_the_bytes_the_audit_passed_and_no_others():
    """The console prints ``deliver``'s return value verbatim.

    Not "something like it": if the driver added a line of its own to the view,
    a hand-played session would stop being evidence about gate #1, because the
    person would be reading bytes no model was ever given.
    """
    session = session_mod.new(seed=7)
    players = demo.build_players(session, args(human="0"), random.Random(0))
    console = players[0].backend
    console.stdin = io.StringIO("do I look around\n")
    console.stdout = io.StringIO()

    context = session.deliver(0)
    declaration = players[0].declare(context)

    assert declaration.do == "I look around"
    printed = console.stdout.getvalue()
    assert context in printed
    assert undeclared_in(printed) == []


def test_a_leaking_referee_stops_the_session_before_the_console_prints_it():
    """The end-to-end statement: gate #1 raises on the way to the terminal.

    ``deliver`` is the only way bytes reach a seat and it audits before it
    returns, so the leaking context is never handed to the console at all - the
    person's terminal ends the session instead of showing them the fact.
    """
    session = session_mod.new(seed=7)
    players = demo.build_players(session, args(human="0"), random.Random(0))
    console = players[0].backend
    console.stdin = io.StringIO("do I wait\n" * 40)
    console.stdout = io.StringIO()

    leaky = _Referee(seats.Turn(narrate="A shallow cavity under the bier."))
    with pytest.raises(session_mod.LeakDetected):
        session_mod.play_session(session, players, leaky, rounds=2)

    assert undeclared_in(console.stdout.getvalue()) == []


def test_the_rules_command_prints_this_rungs_pinned_digest():
    """Console furniture, outside the payload - and the pinned constant rather
    than a second account of the same rules in a file beside it."""
    from games.durf import rules

    console = demo.DurfConsole(keys=seats.PLAYER_KEYS)
    console.stdin = io.StringIO("rules\ndo I wait\n")
    console.stdout = io.StringIO()
    reply, _ = console.complete_meta("your view")

    assert json.loads(reply) == {"do": "I wait"}
    printed = console.stdout.getvalue()
    assert rules.KERNEL_DIGEST in printed
    assert undeclared_in(printed) == []


class _Referee:
    """A referee that plays exactly the turns handed to it, then goes quiet.

    A local copy of ``test_session.py``'s twin rather than an import: that file's
    control is what makes ITS numbers mean anything, and a shared helper is how
    one of them later grows a change nobody re-argued.
    """

    def __init__(self, *turns):
        self.turns = list(turns)
        self.trace: list = []
        self.upstreams: dict = {}
        self.last_fell_back = False
        self.last_refusals = 0
        self.last_rule_refusals = 0
        self.last_refusal = ""
        self.last_upstream = ""

    def rule(self, prompt, session, event):
        return self.turns.pop(0) if self.turns else seats.Turn(narrate="Nothing.")
