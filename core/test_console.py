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
