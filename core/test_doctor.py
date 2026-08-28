"""What ``parlor doctor`` must not do: reassure.

The report exists to stop one failure - starting a long run against a route that
cannot serve it - so the tests here are all about the report being HONEST when the
box is broken, and about it never overstating what a catalog listing proves.
"""

from __future__ import annotations

import json
import urllib.error

import pytest

from core import doctor
from core.backends import Endpoint

LOCAL = Endpoint("local", "http://127.0.0.1:9/v1", False, "serial, on-box, private")
CLEAN = Endpoint("clean", "http://127.0.0.1:9/v1", True, "parallel, off-box",
                 needs_key=True)


class FakeResponse:
    def __init__(self, payload):
        self._payload = json.dumps(payload).encode()

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def serving(payload, monkeypatch, capture=None):
    def fake_urlopen(req, timeout=None):
        if capture is not None:
            capture.append(req)
        return FakeResponse(payload)

    monkeypatch.setattr(doctor.urllib.request, "urlopen", fake_urlopen)


def failing(exc, monkeypatch):
    def fake_urlopen(req, timeout=None):
        raise exc

    monkeypatch.setattr(doctor.urllib.request, "urlopen", fake_urlopen)


# ---- the catalog read -----------------------------------------------------

def test_a_live_route_reports_its_model_ids(monkeypatch):
    serving({"data": [{"id": "a"}, {"id": "b"}]}, monkeypatch)
    status, ids = doctor.catalog(LOCAL, None)
    assert status == "live"
    assert ids == ["a", "b"]


def test_a_dead_port_is_a_line_and_not_an_exception(monkeypatch):
    """Every failure has to survive into the report. A doctor that raises on the
    first dead route never tells you about the live one below it."""
    failing(urllib.error.URLError("connection refused"), monkeypatch)
    status, ids = doctor.catalog(LOCAL, None)
    assert "unreachable" in status
    assert ids == []


def test_a_rejected_key_says_so_rather_than_saying_down(monkeypatch):
    """A 401 and an unreachable port need different remedies - export a key
    versus start a server - so they must not read the same."""
    failing(urllib.error.HTTPError("u", 401, "no", {}, None), monkeypatch)
    status, _ = doctor.catalog(CLEAN, "bad-key")
    assert "refused (401)" in status
    assert "unreachable" not in status


def test_the_key_rides_the_catalog_request_when_the_route_needs_one(monkeypatch):
    captured = []
    serving({"data": []}, monkeypatch, capture=captured)
    doctor.catalog(CLEAN, "sekrit")
    assert captured[0].get_header("Authorization") == "Bearer sekrit"


# ---- the report -----------------------------------------------------------

def test_no_usable_route_exits_nonzero(monkeypatch):
    """So it can gate an unattended run. A box that cannot seat a model must not
    report success to a script."""
    failing(urllib.error.URLError("nope"), monkeypatch)
    text, code = doctor.report(routes={"local": LOCAL})
    assert code == 1
    assert "No route can serve a game" in text


def test_one_live_route_is_a_success_even_beside_a_dead_one(monkeypatch):
    calls = {"n": 0}

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise urllib.error.URLError("nope")
        return FakeResponse({"data": [{"id": "armed"}]})

    monkeypatch.setattr(doctor.urllib.request, "urlopen", fake_urlopen)
    text, code = doctor.report(routes={"clean": CLEAN, "local": LOCAL})
    assert code == 0
    assert "armed" in text


def test_a_keyless_route_is_not_reported_as_missing_a_key(monkeypatch):
    """``local`` needs no key, and telling a person to export one to fix a route
    that never wanted one sends them at the wrong problem."""
    monkeypatch.setattr(doctor, "api_key_from_env", lambda: None)
    serving({"data": [{"id": "x"}]}, monkeypatch)
    text, _ = doctor.report(routes={"local": LOCAL})
    assert "keyless" in text
    assert "export PARLOR_API_KEY" not in text


def test_the_report_never_calls_a_listed_model_armed(monkeypatch):
    """The one claim this tool could make that would be worth less than silence.
    A listing is configuration; only a call is evidence."""
    serving({"data": [{"id": "cold-model"}]}, monkeypatch)
    text, _ = doctor.report(routes={"local": LOCAL})
    assert "catalog:" in text
    assert "not a promise" in text
    assert "armed" not in text.replace("model_not_armed", "")


def test_a_probe_is_not_sent_unless_asked(monkeypatch):
    """It costs a GPU moment locally and a free-tier request off-box, so the
    default must stay a read."""
    serving({"data": [{"id": "x"}]}, monkeypatch)
    monkeypatch.setattr(doctor, "probe",
                        lambda *a, **k: pytest.fail("probed without --probe"))
    doctor.report(routes={"local": LOCAL})


def test_a_probe_reports_the_upstream_that_actually_answered(monkeypatch):
    serving({"data": [{"id": "x"}]}, monkeypatch)
    monkeypatch.setattr(doctor, "probe", lambda *a, **k: "answered, served by 'real-id'")
    text, _ = doctor.report(routes={"local": LOCAL}, do_probe=True)
    assert "real-id" in text


def test_a_refused_probe_is_reported_and_not_raised(monkeypatch):
    """A refusal is the finding. Raising it would lose the routes below."""
    class Boom:
        def complete_meta(self, _):
            raise RuntimeError("model_not_armed")

    monkeypatch.setattr(doctor, "Backend", lambda **kw: Boom())
    verdict = doctor.probe(LOCAL, None, "cold")
    assert "REFUSED" in verdict and "model_not_armed" in verdict


# ---- the flags ------------------------------------------------------------

def test_an_unknown_flag_is_refused_rather_than_ignored(capsys):
    assert doctor.main(["--probes"]) == 2


def test_model_without_a_value_is_refused(capsys):
    assert doctor.main(["--model"]) == 2


def test_help_costs_no_network(monkeypatch):
    failing(AssertionError("doctor --help must not reach the network"), monkeypatch)
    assert doctor.main(["--help"]) == 0
