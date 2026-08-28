"""The ahead-reveal count is only worth having if its exemptions are exact.

Every case is synthetic: `eval/records/` is gitignored, so a test reading a real
record would pass on this box and fail on a clone. The real-record agreement is
the module's own control, which a person runs.

Three properties carry the whole definition and each is exercised on both sides,
because each one is a way to report a number that is not the behaviour:

- the same-turn move exemption, which must NOT extend to the next turn - a
  referee that declares a room and enters it later has still told the party about
  a room they were not in;
- a re-declaration is not a second reveal, or every session that walks past a
  room it already knows scores an ahead-reveal on the way out;
- an ``("npc", ...)`` id names a creature, not a place, so it is out of scope
  rather than counted against whatever room the party happened to be in.
"""
from __future__ import annotations

from eval import durf_reveal_order as ro

ORDER = ["R1", "R2", "R3", "R4"]

TEXT = {
    ("room", "R1"): "R1 Entry slope: a scree slope down into the barrow.",
    ("room", "R2"): "R2 Antechamber: bare stone and a low stone bier.",
    ("room", "R3"): "R3 Gallery: a chasm spanned by an old rope bridge.",
    ("hidden", "R2"): "A loose flagstone covers a shallow cavity.",
    ("npc", "barrow-rats"): "Three barrow-rats: Skill 2, 0 HD.",
}
DECL = {text: fid for fid, text in TEXT.items()}
SEEDED = {("room", "R1")}


def say(who="Vesh", text="I look around."):
    return {"kind": "speech", "who": who, "text": text}


def ref(text):
    return {"kind": "referee", "who": "referee", "text": text}


def move(room):
    return ref(f"{ro.MOVE_PREFIX}{room} Antechamber. {TEXT[('room', room)]}")


def row(*entries, declared=None):
    seen = set(SEEDED)
    for entry in entries:
        into = ro.moved_to(entry)
        if into is not None:
            seen.add(("room", into))
        elif entry["text"] in DECL:
            seen.add(DECL[entry["text"]])
    return {"index": 0, "gate1_held": True, "transcript": list(entries),
            "declared": [list(f) for f in sorted(declared or seen)]}


#: A synthetic dungeon, not the shipped one - the same reason every other case
#: here is synthetic. R1->R2 is blocked and R3->R4 is in sight, so both branches
#: of the grade are exercised by the fixture a test controls.
ROOMS = {
    "R1": {"id": "R1", "exits": [{"to": "R2", "via": "a slope", "sight": False}]},
    "R2": {"id": "R2", "exits": [{"to": "R1", "via": "a slope", "sight": False},
                                 {"to": "R3", "via": "a door", "sight": False}]},
    "R3": {"id": "R3", "exits": [{"to": "R2", "via": "a door", "sight": False},
                                 {"to": "R4", "via": "a bridge", "sight": True}]},
    "R4": {"id": "R4", "exits": [{"to": "R3", "via": "a bridge", "sight": True}]},
}


def ahead(a_row):
    return ro.replay(a_row, DECL, SEEDED, ORDER, ROOMS)["ahead"]


def test_declaring_the_room_being_entered_is_not_ahead():
    """The exemption. `call_move` reveals what it enters; that is entering."""
    assert ahead(row(say(), ref(TEXT[("room", "R2")]), move("R2"))) == []


def test_the_exemption_does_not_reach_the_next_turn():
    """Mutation of the case above: the same two entries, one turn apart.

    Without a turn boundary the lookahead would exempt any reveal a later move
    eventually matched, and a referee that narrates R2 for three turns before
    walking in would score clean.
    """
    found = ahead(row(say(), ref(TEXT[("room", "R2")]), say(), move("R2")))
    assert [a["fact"] for a in found] == [["room", "R2"]]
    assert found[0]["from"] == "R1"


def test_a_room_declared_and_never_entered_is_ahead():
    found = ahead(row(say(), ref(TEXT[("room", "R3")])))
    assert [a["fact"] for a in found] == [["room", "R3"]]
    assert found[0]["distance"] == 2


def test_a_hidden_fact_is_keyed_by_the_room_in_its_id():
    """Its text names no room, so the join is by id. Both directions."""
    assert [a["fact"] for a in ahead(row(say(), ref(TEXT[("hidden", "R2")])))] \
        == [["hidden", "R2"]]
    assert ahead(row(say(), move("R2"), say(),
                     ref(TEXT[("hidden", "R2")]))) == []


def test_a_redeclaration_is_not_a_second_reveal():
    """The party walks into R2, walks on, and the referee says R2's text again."""
    walked = row(say(), move("R2"), say(), move("R3"), say(),
                 ref(TEXT[("room", "R2")]))
    assert ahead(walked) == []


def test_an_npc_fact_is_out_of_scope():
    """Its id names a creature group; no room comparison is meaningful."""
    assert ahead(row(say(), ref(TEXT[("npc", "barrow-rats")]))) == []


def test_the_control_catches_a_replay_that_misses_a_declaration():
    """Mutation: a record claiming a declaration the transcript does not carry.

    This is the failure the control exists for - a replay that silently misses
    declarations measures every count against the wrong entitlement.
    """
    good = row(say(), ref(TEXT[("room", "R2")]))
    assert ro.control([good], [ro.replay(good, DECL, SEEDED, ORDER, ROOMS)]) == []

    lying = dict(good, declared=[["room", "R1"], ["room", "R2"], ["room", "R3"]])
    assert ro.control([lying], [ro.replay(lying, DECL, SEEDED, ORDER, ROOMS)])


def test_leak_context_names_the_declaration_the_narration_answered():
    """Which seat declaration a leaking line was answering is read, not argued."""
    carrying = "Ola presses her ear to the iron door."
    leaking = {"index": 0, "declared": [],
               "transcript": [say("Vesh", "I check the floor."),
                              ref("Vesh runs his hands along the scree."),
                              say("Ola", "I listen at the door before touching it."),
                              ref(carrying)],
               "leaks": [{"viewer": 0, "leaks": [[["room", "R2"], "iron door"]],
                          "evidence": [carrying]}]}
    got = ro.leak_context(leaking)
    assert [(g["who"], g["declaration"]) for g in got] == [
        ("Ola", "I listen at the door before touching it.")]


def test_a_room_in_sight_is_graded_apart_from_one_behind_a_door():
    """The distinction the fixture's sightlines were stated to make. Same shape of
    reveal, two rooms, two grades - and the mutation that matters is the one where
    both come back ``blocked``, which is the instrument before this existed."""
    text = "R4 Tomb: a sealed stone sarcophagus."
    decl = dict(DECL, **{text: ("room", "R4")})
    seen = ro.replay(
        {"index": 0, "gate1_held": True, "declared": [["room", "R1"], ["room", "R2"],
                                                      ["room", "R3"], ["room", "R4"]],
         "transcript": [say(), move("R2"), move("R3"), ref(text)]},
        decl, SEEDED, ORDER, ROOMS)["ahead"]
    assert [a["grade"] for a in seen] == ["in_sight"]

    blocked = ahead(row(say(), ref(TEXT[("room", "R3")])))
    assert [a["grade"] for a in blocked] == ["blocked"]


def test_a_hidden_fact_is_blocked_even_across_an_open_sightline():
    """Hidden is what a room does not show a party standing IN it, so a sightline
    into that room cannot carry it. Without this branch the grade would exempt a
    referee that announced what is under a flagstone in the room next door."""
    rooms = dict(ROOMS)
    rooms["R1"] = {"id": "R1",
                   "exits": [{"to": "R2", "via": "an arch", "sight": True}]}
    seen = ro.replay(row(say(), ref(TEXT[("hidden", "R2")])),
                     DECL, SEEDED, ORDER, rooms)["ahead"]
    assert [a["grade"] for a in seen] == ["blocked"]


def test_distance_is_walked_along_the_exits_not_the_fixture_order():
    """``ROOMS`` is a corridor, so order and graph agree on it; the mutant is a
    dungeon where they do not. R1 exits straight to R4, and a distance read off
    the listing order would call that three rooms."""
    rooms = {
        "R1": {"id": "R1", "exits": [{"to": "R4", "via": "a shaft", "sight": False}]},
        "R2": {"id": "R2", "exits": [{"to": "R4", "via": "a door", "sight": False}]},
        "R3": {"id": "R3", "exits": [{"to": "R4", "via": "a door", "sight": False}]},
        "R4": {"id": "R4", "exits": [{"to": "R1", "via": "a shaft", "sight": False},
                                     {"to": "R2", "via": "a door", "sight": False},
                                     {"to": "R3", "via": "a door", "sight": False}]},
    }
    text = "R4 Tomb: a sealed stone sarcophagus."
    seen = ro.replay(row(say(), ref(text)), dict(DECL, **{text: ("room", "R4")}),
                     SEEDED, ORDER, rooms)["ahead"]
    assert [a["distance"] for a in seen] == [1]
