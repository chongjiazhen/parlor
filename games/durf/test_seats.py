"""The session envelope's parser, and the one shape it was measured into accepting.

The adjudicator's four keys are executed, so the parser is strict about SHAPE:
half a turn applied is a state the transcript cannot explain. What it is not
strict about is a shape that is unambiguous, and the first live arm found one.
"""

from __future__ import annotations

import pytest

from games.durf import seats


def test_a_turn_parses_its_four_keys():
    turn = seats.parse_turn(
        '{"think": "t", "reveal": [["room", "R2"]], '
        '"calls": [{"call": "tick", "turns": 1}], '
        '"ask": {"seat": 1, "question": "well?"}, "narrate": "n"}')
    assert turn.reveal == (("room", "R2"),)
    assert turn.calls == ({"call": "tick", "turns": 1},)
    assert turn.ask == {"seat": 1, "question": "well?"}
    assert turn.think == "t" and turn.narrate == "n"


def test_a_single_flat_fact_id_is_one_id_and_not_two():
    """``["room", "R2"]`` where a list OF ids was asked for.

    The two shapes are distinguishable - a list of ids has list elements - and
    read as a list of ids this would be two single-part ids, of which no fact has
    any. So it widens the shape and guesses at no meaning. Measured on the first
    live arm (2026-08-28): the flat form was most of that run's 21% recovered rate.
    """
    assert seats.parse_turn('{"reveal": ["room", "R2"], "narrate": "n"}').reveal \
        == (("room", "R2"),)


def test_a_bare_string_reveal_is_still_refused():
    with pytest.raises(seats.IllegalReply, match="bare string"):
        seats.parse_turn('{"reveal": [["room", "R2"], "hidden"], "narrate": "n"}')


def test_calls_must_be_objects_because_they_are_executed():
    with pytest.raises(seats.IllegalReply, match="list of call objects"):
        seats.parse_turn('{"calls": ["roll the dice"], "narrate": "n"}')


def test_a_lone_call_object_is_accepted_as_a_list_of_one():
    turn = seats.parse_turn('{"calls": {"call": "tick"}, "narrate": "n"}')
    assert turn.calls == ({"call": "tick"},)


def test_an_ask_with_no_question_is_refused_rather_than_sent_empty():
    with pytest.raises(seats.IllegalReply, match="no question"):
        seats.parse_turn('{"ask": {"seat": 1, "question": "  "}, "narrate": "n"}')


def test_a_player_must_say_what_it_does():
    with pytest.raises(seats.IllegalReply, match="'do' must say"):
        seats.parse_declaration('{"think": "hmm", "say": "hello"}')
    assert seats.parse_declaration(
        '{"do": "I open the door", "say": "here goes"}').do == "I open the door"


def test_the_adjudicator_prompt_carries_its_four_blocks_in_order():
    """Split along its seams so a bad ruling can be attributed to one of them.

    Retrofitting the split invalidates every arm run before it, which is why the
    order is pinned rather than left to whoever edits the template next.
    """
    from games.durf import session as session_mod

    sess = session_mod.new(seed=1)
    prompt = seats.adjudicator_prompt(sess, "Vesh looks around.")
    marks = [prompt.index(block) for block in
             (seats.ADJ_RULES, seats.ADJ_PROCEDURE, seats.ADJ_SCHEMA,
              seats.ADJ_DISCRETION)]
    assert marks == sorted(marks)
    assert "Vesh looks around." in prompt


def test_the_referee_view_lists_the_undeclared_facts_by_id():
    """A referee that cannot name a fact cannot declare it, and a paraphrase is
    exactly what the audit cannot see."""
    from games.durf import session as session_mod

    sess = session_mod.new(seed=1)
    view = seats.referee_view(sess)
    assert "['hidden', 'R2']" in view
    assert "NOT YET DECLARED" in view
