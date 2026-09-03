"""Pack loading, and the payload position the menu encodes."""

import json

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
