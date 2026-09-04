"""The choosing seat: a model reply becomes a pick, or the budget hands it back."""

from experiments.ensemble.draft import Draft
from experiments.ensemble.pack import Pack
from experiments.ensemble.seats import ChoosingSeat, render_choice_ask
from experiments.ensemble.session import run_draft


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


class Meta:
    """A backend that reports which upstream served the reply, as the real one does."""

    def __init__(self, replies, upstream="up-1"):
        self.replies = list(replies)
        self.upstream = upstream

    def complete_meta(self, context, history=None):
        return (self.replies.pop(0) if self.replies else "{}"), self.upstream

    def complete(self, context):
        return self.complete_meta(context)[0]


def test_the_seat_reports_the_upstream_that_served_it():
    seat = ChoosingSeat(seat=0, backend=Meta(['{"pick": "B"}'], upstream="glm-4.7"))
    assert seat.choose(MENU, taken=()) == "B"
    assert seat.upstream == "glm-4.7"


def test_a_backend_without_complete_meta_still_works():
    """The test doubles and any scripted seat expose only ``complete``."""
    seat = ChoosingSeat(seat=0, backend=Canned(['{"pick": "B"}']))
    assert seat.choose(MENU, taken=()) == "B"
    assert seat.upstream is None


def test_the_record_names_the_upstream_per_seat(tmp_path):
    """On ``auto:*`` a different upstream may serve each seat, so the record must
    say which. A figure that cannot name its upstream cannot be compared later."""
    import json
    p = tmp_path / "p.json"
    p.write_text(json.dumps({"pack": "t", "playbooks": [
        {"name": n, "about": f"{n} line.", "questions": []} for n in "AB"]}), encoding="utf-8")
    pack = Pack.load(p)
    seats = [ChoosingSeat(seat=0, backend=Meta(['{"pick": "A"}'], upstream="x")),
             ChoosingSeat(seat=1, backend=Meta(['{"pick": "B"}'], upstream="y"))]
    rec = run_draft(pack, seats, seed=1)
    assert rec["upstreams"] == {0: "x", 1: "y"}


def test_upstreams_is_present_even_when_nothing_reports_one(tmp_path):
    import json
    p = tmp_path / "p.json"
    p.write_text(json.dumps({"pack": "t", "playbooks": [
        {"name": "A", "about": "A line.", "questions": []}]}), encoding="utf-8")
    pack = Pack.load(p)
    rec = run_draft(pack, [ChoosingSeat(seat=0, backend=Canned(['{"pick": "A"}']))], seed=1)
    assert rec["upstreams"] == {0: None}


class Stalls:
    """A backend whose provider accepts the connection and then stops talking."""

    def __init__(self, exc=None, then=None):
        self.exc = exc or TimeoutError("timed out")
        self.then = list(then or [])
        self.calls = 0

    def complete_meta(self, context, history=None):
        self.calls += 1
        if self.then:
            return self.then.pop(0), "up"
        raise self.exc


def test_a_stalled_provider_costs_a_fallback_not_the_run():
    back = Stalls()
    seat = ChoosingSeat(seat=0, backend=back, retries=3)
    assert seat.choose(MENU, taken=()) is None
    assert back.calls == 3
    assert seat.transport_errors == 3


def test_a_transport_error_still_spends_only_its_own_budget():
    """A stall that clears inside the budget is a normal decision, not a fallback."""
    back = Stalls(then=[])
    back.then = []
    seat = ChoosingSeat(seat=0, backend=Stalls(then=[]), retries=1)
    assert seat.choose(MENU, taken=()) is None


def test_a_provider_that_recovers_inside_the_budget_answers():
    class Flaky(Stalls):
        def complete_meta(self, context, history=None):
            self.calls += 1
            if self.calls == 1:
                raise TimeoutError("timed out")
            return '{"pick": "B"}', "up"
    seat = ChoosingSeat(seat=0, backend=Flaky(), retries=3)
    assert seat.choose(MENU, taken=()) == "B"
    assert seat.transport_errors == 1


def test_a_connection_refusal_is_transport_too():
    import urllib.error
    seat = ChoosingSeat(seat=0, backend=Stalls(exc=urllib.error.URLError("refused")),
                        retries=2)
    assert seat.choose(MENU, taken=()) is None
    assert seat.transport_errors == 2


def test_a_programming_error_is_NOT_swallowed():
    """Only transport failures are absorbed. A bug must still crash the run."""
    import pytest
    seat = ChoosingSeat(seat=0, backend=Stalls(exc=ValueError("bug")), retries=2)
    with pytest.raises(ValueError):
        seat.choose(MENU, taken=())


def test_the_record_counts_transport_errors_separately(tmp_path):
    """A run at 100% fallback from a dead endpoint must not read like a bad model."""
    import json
    p = tmp_path / "p.json"
    p.write_text(json.dumps({"pack": "t", "playbooks": [
        {"name": n, "about": f"{n} line.", "questions": []} for n in "AB"]}), encoding="utf-8")
    pack = Pack.load(p)
    seats = [ChoosingSeat(seat=0, backend=Stalls(), retries=1),
             ChoosingSeat(seat=1, backend=Meta(['{"pick": "B"}'])) ]
    rec = run_draft(pack, seats, seed=1)
    assert rec["transport_errors"] == 1
    assert rec["fallbacks"] >= 1
    assert len(set(rec["picks"].values())) == 2
