"""The choosing seat: a model reply becomes a pick, or the budget hands it back."""

from games.ensemble.draft import Draft
from games.ensemble.pack import Pack
from games.ensemble.seats import ChoosingSeat, render_choice_ask
from games.ensemble.session import run_draft


class Canned:
    """A backend that replies from a script. seed is part of the payload upstream."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.asks = []

    def complete(self, context):
        self.asks.append(context)
        return self.replies.pop(0) if self.replies else "{}"


MENU = [{"name": "A", "hook": "First."}, {"name": "B", "hook": "Second."},
        {"name": "C", "hook": "Third."}]


def test_the_ask_carries_the_menu_and_what_is_gone():
    ask = render_choice_ask(seat=1, menu=MENU, taken=("A",))
    assert "B" in ask and "Second." in ask
    assert "A" in ask


def test_the_ask_does_not_carry_a_full_sheet():
    """The payload position: names plus a hook, and the sheet only to the taker."""
    ask = render_choice_ask(seat=0, menu=MENU, taken=())
    assert "options" not in ask and "question" not in ask


def test_a_clean_reply_becomes_the_pick():
    seat = ChoosingSeat(seat=0, backend=Canned(['{"think": "hm", "pick": "B"}']))
    assert seat.choose(MENU, taken=()) == "B"


def test_think_is_not_echoed_into_the_pick():
    seat = ChoosingSeat(seat=0, backend=Canned(['{"think": "C is best", "pick": "B"}']))
    assert seat.choose(MENU, taken=()) == "B"


def test_an_unparseable_reply_exhausts_the_budget_and_returns_none():
    back = Canned(["not json", "still not json", "nope"])
    seat = ChoosingSeat(seat=0, backend=back, retries=3)
    assert seat.choose(MENU, taken=()) is None
    assert len(back.asks) == 3


def test_a_late_good_reply_inside_the_budget_is_taken():
    back = Canned(["garbage", '{"pick": "C"}'])
    seat = ChoosingSeat(seat=0, backend=back, retries=3)
    assert seat.choose(MENU, taken=()) == "C"


def test_run_draft_seats_everyone_and_reports_its_fallback_rate(tmp_path):
    import json
    p = tmp_path / "p.json"
    p.write_text(json.dumps({"pack": "t", "playbooks": [
        {"name": n, "about": f"{n} line.", "questions": []} for n in "ABC"]}), encoding="utf-8")
    pack = Pack.load(p)
    seats = [ChoosingSeat(seat=i, backend=Canned([f'{{"pick": "{n}"}}']))
             for i, n in enumerate("ABC")]
    rec = run_draft(pack, seats, seed=7)
    assert rec["picks"] == {0: "A", 1: "B", 2: "C"}
    assert rec["fallbacks"] == 0 and rec["fallback_rate"] == 0.0
    assert rec["distribution"] == {"A": 1, "B": 1, "C": 1}


def test_a_seat_that_never_answers_is_a_fallback_in_the_record(tmp_path):
    import json
    p = tmp_path / "p.json"
    p.write_text(json.dumps({"pack": "t", "playbooks": [
        {"name": n, "about": f"{n} line.", "questions": []} for n in "AB"]}), encoding="utf-8")
    pack = Pack.load(p)
    seats = [ChoosingSeat(seat=0, backend=Canned(["junk"]), retries=1),
             ChoosingSeat(seat=1, backend=Canned(["junk"]), retries=1)]
    rec = run_draft(pack, seats, seed=7)
    assert rec["fallbacks"] == 2
    assert rec["fallback_rate"] == 1.0
    assert set(rec["picks"].values()) == {"A", "B"}


def test_a_fallback_can_take_the_name_a_later_seat_wanted(tmp_path):
    """Not a bug: the random policy plays a real pick, so it really removes it.

    A later seat asking for that name is then making an illegal move and is
    counted as one. The rate measures decisions the run could not honour, and
    this is one of them.
    """
    import json
    p = tmp_path / "p.json"
    p.write_text(json.dumps({"pack": "t", "playbooks": [
        {"name": n, "about": f"{n} line.", "questions": []} for n in "AB"]}), encoding="utf-8")
    pack = Pack.load(p)
    seats = [ChoosingSeat(seat=0, backend=Canned(["junk"]), retries=1),
             ChoosingSeat(seat=1, backend=Canned(['{"pick": "B"}']))]
    rec = run_draft(pack, seats, seed=7)
    assert rec["picks"][0] == "B"
    assert rec["fallbacks"] == 2
    assert set(rec["picks"].values()) == {"A", "B"}
