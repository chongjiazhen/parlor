"""Pack loading, and the payload position the menu encodes."""

import json
from pathlib import Path

import pytest

from games.ensemble.pack import Pack, PackError


def _pack(tmp_path, playbooks):
    p = tmp_path / "playbooks.json"
    p.write_text(json.dumps({"pack": "t", "playbooks": playbooks}), encoding="utf-8")
    return p


def _pb(name, about="A line about it. A second sentence.", n=2):
    return {"name": name, "about": about,
            "questions": [{"question": f"q{i}?", "options": ["a", "b"]} for i in range(n)]}


def test_loads_from_an_arbitrary_path(tmp_path):
    pack = Pack.load(_pack(tmp_path, [_pb("THE ONE"), _pb("THE OTHER")]))
    assert pack.names() == ("THE ONE", "THE OTHER")


def test_missing_file_raises_packerror(tmp_path):
    with pytest.raises(PackError):
        Pack.load(tmp_path / "nope.json")


def test_a_nameless_playbook_is_refused(tmp_path):
    with pytest.raises(PackError):
        Pack.load(_pack(tmp_path, [_pb(""), _pb("THE OTHER")]))


def test_duplicate_names_are_refused(tmp_path):
    with pytest.raises(PackError):
        Pack.load(_pack(tmp_path, [_pb("THE ONE"), _pb("THE ONE")]))


def test_menu_carries_a_hook_and_not_the_sheet(tmp_path):
    """The choose-phase ask is a budget: names plus one line, never 22 sheets."""
    pack = Pack.load(_pack(tmp_path, [_pb("THE ONE"), _pb("THE OTHER")]))
    menu = pack.menu()
    assert menu[0] == {"name": "THE ONE", "hook": "A line about it."}
    blob = json.dumps(menu)
    assert "q0?" not in blob and "options" not in blob


def test_sheet_is_available_for_the_seat_that_took_it(tmp_path):
    pack = Pack.load(_pack(tmp_path, [_pb("THE ONE")]))
    sheet = pack.sheet("THE ONE")
    assert sheet["questions"][0]["options"] == ["a", "b"]


def test_sheet_of_an_unknown_name_raises(tmp_path):
    pack = Pack.load(_pack(tmp_path, [_pb("THE ONE")]))
    with pytest.raises(KeyError):
        pack.sheet("THE MISSING")


EXAMPLE = Path(__file__).resolve().parent / "packs" / "example" / "playbooks.json"


def test_the_shipped_example_pack_loads_and_satisfies_the_schema():
    """Every rung owes one pack under terms that permit shipping it.

    It is the fixture the loader is tested against and the executable half of
    the schema documentation, so a change that breaks the format fails here
    rather than in somebody's run. ``docs/content-packs.md`` §The example pack.
    """
    pack = Pack.load(EXAMPLE)
    assert len(pack.names()) >= 5
    assert len(set(pack.names())) == len(pack.names())
    for entry in pack.menu():
        assert entry["hook"], f"{entry['name']} has no menu hook"
        assert entry["hook"].count(".") == 1, f"{entry['name']} hook is not one sentence"
    for name in pack.names():
        sheet = pack.sheet(name)
        assert sheet["questions"], f"{name} has no questions"
        for q in sheet["questions"]:
            assert q["options"], f"{name}: {q['question']} has no options"


def test_the_example_pack_seats_a_full_draft():
    from games.ensemble.draft import Draft
    pack = Pack.load(EXAMPLE)
    d = Draft(pack.names(), seats=5, seed=1)
    while not d.done:
        d.offer()
        d.take(d.remaining()[0])
    assert len(set(d.picks.values())) == 5
