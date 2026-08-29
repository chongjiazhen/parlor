"""What a human seat is allowed to see, and how its typing becomes a move.

Two properties matter here and the rest is convenience. First, a human seat must
receive the SAME bytes a model seat receives - if the console added or withheld
anything, a hand-played game would stop being evidence about gate #1. Second, a
mistyped answer must never become a random move on the person's behalf.
"""

from __future__ import annotations

import io
import json

import pytest

from core.console import HUMAN, ConsoleBackend, TooManyHumans, human_seats


def console(text: str, keys=("team", "say", "vote", "card", "target", "think", "note")):
    backend = ConsoleBackend(keys=keys)
    backend.stdin = io.StringIO(text)
    backend.stdout = io.StringIO()
    return backend


# ---- shorthand -> the reply a model would have sent -----------------------

def test_shorthand_becomes_json_the_game_can_parse():
    reply, served = console("vote y\n").complete_meta("your view")
    assert json.loads(reply) == {"vote": "y"}
    assert served == HUMAN


def test_values_stay_strings_for_the_games_own_coercion():
    """``core.replies`` turns ``y`` into True and ``0 3`` into a seat list,
    because that is how a model's reply is read. A second coercion here could
    drift from the one every recorded number was measured with."""
    reply, _ = console("team 0 3\n").complete_meta("view")
    assert json.loads(reply) == {"team": "0 3"}


def test_several_keys_split_only_before_a_key():
    reply, _ = console("say wait; seat 2 worries me; think 1 and 4 look paired\n") \
        .complete_meta("view")
    obj = json.loads(reply)
    assert obj["say"] == "wait; seat 2 worries me"
    assert obj["think"] == "1 and 4 look paired"


def test_raw_json_passes_through_unrepaired():
    """The game's parser owns the complaint about malformed JSON, and it is the
    same complaint the models get."""
    reply, _ = console('{"vote": true}\n').complete_meta("view")
    assert json.loads(reply) == {"vote": True}


def test_multi_line_json_is_read_whole():
    reply, _ = console('{\n "vote":\n true}\n').complete_meta("view")
    assert json.loads(reply) == {"vote": True}


# ---- a typo is not a decision ---------------------------------------------

def test_an_unknown_key_is_re_asked_locally_not_returned():
    """It must not reach the policy: an unparseable line there spends one of the
    seat's retries, and at the end of that budget the RANDOM policy plays."""
    backend = console("wibble yes\nvote n\n")
    reply, _ = backend.complete_meta("view")
    assert json.loads(reply) == {"vote": "n"}
    assert "not an action key" in backend.stdout.getvalue()


def test_blank_lines_are_ignored():
    reply, _ = console("\n\nvote y\n").complete_meta("view")
    assert json.loads(reply) == {"vote": "y"}


def test_question_mark_reprints_the_view():
    backend = console("?\nvote y\n")
    backend.complete_meta("SEAT VIEW HERE")
    assert backend.stdout.getvalue().count("SEAT VIEW HERE") == 2


def test_eof_ends_the_game_rather_than_playing_random():
    """EOF raises ``KeyboardInterrupt``, a ``BaseException``, so it passes through
    ``LLMPolicy``'s ``except Exception`` instead of being retried and falling back
    to a move nobody made."""
    with pytest.raises(KeyboardInterrupt):
        console("").complete_meta("view")


# ---- the human sees the seat's bytes, and only those ----------------------

def test_the_view_is_printed_verbatim():
    backend = console("vote y\n")
    backend.complete_meta("line one\nline two")
    out = backend.stdout.getvalue()
    assert "line one\nline two" in out


def test_the_banner_is_printed_once():
    backend = console("vote y\nvote n\n")
    backend.complete_meta("view")
    backend.complete_meta("view")
    assert backend.stdout.getvalue().count("exact text this seat's") == 1


def test_a_human_seat_gets_the_same_bytes_as_a_model_seat():
    """The property the whole flag exists for. Rendered once by the referee, so
    there is no second render that could differ - this test is what keeps it that
    way if someone gives the console its own view."""
    from games.cabal.player import ACTION_KEYS
    from games.cabal.referee import CabalReferee

    ref = CabalReferee.new(5, seed=7)
    seat = ref.leader
    expected = ref.prompt_for(seat)

    backend = ConsoleBackend(keys=ACTION_KEYS)
    backend.stdin = io.StringIO("team 0 1 2\n")
    backend.stdout = io.StringIO()
    backend.complete_meta(expected)
    assert expected in backend.stdout.getvalue()


def test_it_satisfies_the_backend_seam():
    """``LLMPolicy`` reaches its backend through exactly these, and a driver's
    report reads ``model`` off it. Anything more and a human seat would need its
    own policy."""
    backend = ConsoleBackend(keys=("vote",))
    assert callable(backend.complete_meta) and callable(backend.complete)
    assert backend.model == HUMAN


# ---- one person per terminal ----------------------------------------------

def test_one_human_seat_is_read():
    assert human_seats("0", 5) == {0}
    assert human_seats(" 3 ", 5) == {3}
    assert human_seats(None, 5) == set()


def test_a_second_human_seat_is_REFUSED():
    """Not a missing feature - the invariant asserting itself. Two people share
    one terminal, so each would read the other's private view scroll past, which
    is the property this arena exists to demonstrate the absence of. The
    referee's audit cannot see it: both renders are correct, and what is wrong is
    that one pair of eyes receives both."""
    with pytest.raises(TooManyHumans):
        human_seats("0,3", 5)
    with pytest.raises(TooManyHumans):
        human_seats("0 3", 5)


def test_the_refusal_says_why():
    with pytest.raises(SystemExit) as caught:
        human_seats("0,1", 5)
    assert "read the other" in str(caught.value)


def test_a_seat_that_does_not_exist_is_refused():
    with pytest.raises(SystemExit):
        human_seats("7", 5)


def test_the_same_seat_twice_is_one_person_not_two():
    """``--human 0,0`` is a typo, not a second player - refusing it would be the
    guard firing on the wrong thing."""
    assert human_seats("0,0", 5) == {0}


# ---- commands, which are furniture and not moves --------------------------

RULES_STUB = "# stub rules\n\nThree missions held wins it.\n"


def briefed(text, tmp_path=None, briefing="OBJECTIVE: hold three missions.",
            rules=None):
    backend = ConsoleBackend(keys=("team", "say", "vote", "card", "target",
                                   "think", "note"),
                             briefing=briefing, rules_path=rules)
    backend.stdin = io.StringIO(text)
    backend.stdout = io.StringIO()
    return backend


def test_a_command_is_not_a_move_and_does_not_reach_the_game():
    """The whole safety argument for commands in one assertion: whatever the
    console answered, the reply handed back is the MOVE and nothing else. If a
    command could leak into the reply it would be an action nobody played."""
    backend = briefed("help\nrules\n?\nvote y\n")
    reply, served = backend.complete_meta("your view")
    assert json.loads(reply) == {"vote": "y"}
    assert served == HUMAN


def test_the_briefing_prints_under_the_banner_and_only_once():
    backend = briefed("vote y\nvote n\n")
    backend.complete_meta("view")
    backend.complete_meta("view")
    assert backend.stdout.getvalue().count("OBJECTIVE: hold three missions.") == 1


def test_help_reprints_the_briefing_mid_game():
    backend = briefed("help\nvote y\n")
    backend.complete_meta("view")
    assert backend.stdout.getvalue().count("OBJECTIVE: hold three missions.") == 2


def test_rules_prints_the_games_own_rules_file(tmp_path):
    path = tmp_path / "RULES.md"
    path.write_text(RULES_STUB, encoding="utf-8")
    backend = briefed("rules\nvote y\n", rules=str(path))
    backend.complete_meta("view")
    assert "Three missions held wins it." in backend.stdout.getvalue()


def test_an_unreadable_rules_file_costs_a_line_and_not_the_game(tmp_path):
    """Orientation is a convenience, and a convenience must not be able to end a
    seat that can still make its move."""
    backend = briefed("rules\nvote y\n", rules=str(tmp_path / "gone.md"))
    reply, _ = backend.complete_meta("view")
    assert json.loads(reply) == {"vote": "y"}
    assert "cannot read" in backend.stdout.getvalue()


def test_no_command_word_is_also_an_action_key():
    """A game that named an action ``rules`` would have it shadowed by the
    console. Asserted over every REGISTERED game rather than the two that exist
    today, so a rung added later is covered the day it lands."""
    from importlib import import_module

    from core.console import COMMANDS
    from core.registry import RUNGS

    for name, rung in RUNGS.items():
        keys = import_module(rung.module).ACTION_KEYS
        assert not set(keys) & set(COMMANDS), name


def test_a_move_wins_the_word_if_a_game_ever_takes_it():
    """The shadowing rule, stated as behaviour: if ``rules`` were an action key,
    typing it plays the action. The guard above keeps that hypothetical, and this
    keeps the precedence correct if it ever stops being one."""
    backend = ConsoleBackend(keys=("rules",), rules_path="/nonexistent")
    backend.stdin = io.StringIO("rules\n")
    backend.stdout = io.StringIO()
    reply, _ = backend.complete_meta("view")
    assert json.loads(reply) == {"rules": ""}


def test_other_model_display_known():
    # Test that when other_model is set, the greet line shows it.
    backend = ConsoleBackend(keys=("vote",), other_model="test-model")
    backend.stdin = io.StringIO("vote y\n")
    backend.stdout = io.StringIO()
    backend.complete_meta("view")
    out = backend.stdout.getvalue()
    assert "The other seats are served by: test-model" in out


def test_other_model_display_unknown():
    # Test that when other_model is None, the greet line shows unknown.
    backend = ConsoleBackend(keys=("vote",))
    backend.stdin = io.StringIO("vote y\n")
    backend.stdout = io.StringIO()
    backend.complete_meta("view")
    out = backend.stdout.getvalue()
    assert "The other seats are served by: unknown" in out


def test_model_command_does_not_consume_retry():
    # The model command should not count as a move and not end the turn.
    backend = ConsoleBackend(keys=("vote",), other_model="test-model")
    # ONE stream. The command is answered and the SAME ask is put again, so the
    # move has to be waiting on the next line. Two separate streams exhaust stdin
    # mid-ask, which surfaces as "input closed" rather than as a result - and
    # that crash is what hid the dead `model` command from this very test.
    backend.stdin = io.StringIO("vote a\nmodel\nvote y\n")
    backend.stdout = io.StringIO()
    backend.complete_meta("view")            # spends the greeting
    backend.stdout = io.StringIO()           # so the next line can only be the command
    reply, served = backend.complete_meta("view")
    # An unregistered word is not a command: it is an unparsed move, refused, and
    # the seat is asked again - which reaches the same `vote y` and passes every
    # assertion below. Only the printed line separates a live command from a dead
    # one, and this is the assertion that fails when `model` leaves COMMANDS.
    assert "test-model" in backend.stdout.getvalue()
    assert json.loads(reply) == {"vote": "y"}
    assert served == HUMAN


def test_model_field_still_human():
    # Ensure that the model field (for served-by) is still HUMAN by default.
    backend = ConsoleBackend(keys=("vote",))
    assert backend.model == HUMAN


def test_the_briefing_never_enters_the_seats_view():
    """Gate #1's neighbour. The briefing is console furniture: it is printed
    around the view, never into it, so the bytes the referee rendered are what a
    model would have received and a hand-played game stays evidence about the
    payload."""
    view = "You are seat 0. Board: mission 1."
    backend = briefed("vote y\n")
    backend.complete_meta(view)
    printed = backend.stdout.getvalue()
    assert view in printed
    assert "OBJECTIVE" not in view
    assert printed.index("OBJECTIVE") < printed.index(view)


def test_random_seats_exactly_one_person_and_inside_the_table():
    for seed in range(40):
        seats = human_seats("random", 5, seed)
        assert len(seats) == 1
        assert 0 <= next(iter(seats)) < 5


def test_the_same_seed_seats_the_same_person_every_time():
    # The claim `--seed` makes. Both demos resolve `--human` twice - once in
    # `main`, once in `build_policies` - so a draw that moved between calls would
    # seat the person in one place and point the console at another.
    for seed in (0, 7, 1000):
        assert human_seats("random", 5, seed) == human_seats("random", 5, seed)


def test_the_draw_does_not_consume_the_callers_random_stream():
    """The sharp one. Drawing from the rng the policies deal out of would change
    what every random seat played at that seed - a silent re-baseline of every
    number recorded under it, bought for a convenience."""
    import random as _r
    before = _r.Random(4).random()
    human_seats("random", 5, 4)
    assert _r.Random(4).random() == before


def test_different_seeds_can_seat_different_people():
    assert len({next(iter(human_seats("random", 5, s))) for s in range(40)}) > 1


def test_random_without_a_seed_refuses_rather_than_guessing():
    try:
        human_seats("random", 5)
    except SystemExit as exc:
        assert "--seed" in str(exc)
    else:
        raise AssertionError("an unseeded random draw was allowed")


def test_an_explicit_seat_ignores_the_seed_entirely():
    assert human_seats("3", 5, 99) == {3}
    assert human_seats("3", 5) == {3}
