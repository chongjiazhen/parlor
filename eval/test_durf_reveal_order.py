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


def ahead(a_row):
    return ro.replay(a_row, DECL, SEEDED, ORDER)["ahead"]


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
    assert ro.control([good], [ro.replay(good, DECL, SEEDED, ORDER)]) == []

    lying = dict(good, declared=[["room", "R1"], ["room", "R2"], ["room", "R3"]])
    assert ro.control([lying], [ro.replay(lying, DECL, SEEDED, ORDER)])


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
