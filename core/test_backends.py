"""Transport-level retry: a throttle must cost wall-clock, not measurement.

The failure this guards against does not look like a failure. A provider that
429s every call sends every decision to the random fallback, and the run then
reports a model that cannot follow the rules - 89% fallback, measured, with
nothing in the numbers to say the model was never asked.
"""

from __future__ import annotations

import io
import unittest
import urllib.error
from unittest import mock

from core.backends import (ENDPOINTS, RETRY_CODES, Backend, MissingKey,
                           api_key_from_env, require_key)


def http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("http://x/v1", code, "nope", {}, None)


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def reply(text: str = "ok") -> FakeResponse:
    import json
    return FakeResponse(json.dumps(
        {"choices": [{"message": {"content": text}}]}).encode())


class TestTransportRetry(unittest.TestCase):
    def setUp(self):
        self.backend = Backend.named("clean", "m", rate_backoff=0.0)

    def run_with(self, side_effect):
        with mock.patch("urllib.request.urlopen", side_effect=side_effect) as opener, \
             mock.patch("core.backends.time.sleep") as slept:
            return self.backend.complete("hi"), opener, slept

    def test_a_throttled_call_is_retried_until_it_lands(self):
        out, opener, slept = self.run_with(
            [http_error(429), http_error(429), reply("landed")])
        self.assertEqual(out, "landed")
        self.assertEqual(opener.call_count, 3)
        self.assertEqual(slept.call_count, 2)

    def test_backoff_doubles(self):
        backend = Backend.named("clean", "m", rate_backoff=2.0)
        with mock.patch("urllib.request.urlopen",
                        side_effect=[http_error(429), http_error(503), reply()]), \
             mock.patch("core.backends.time.sleep") as slept:
            backend.complete("hi")
        self.assertEqual([c.args[0] for c in slept.call_args_list], [2.0, 4.0])

    def test_it_gives_up_and_raises_rather_than_looping_forever(self):
        backend = Backend.named("clean", "m", rate_backoff=0.0, rate_retries=2)
        with mock.patch("urllib.request.urlopen",
                        side_effect=[http_error(429)] * 9) as opener, \
             mock.patch("core.backends.time.sleep"):
            with self.assertRaises(urllib.error.HTTPError):
                backend.complete("hi")
        self.assertEqual(opener.call_count, 3)      # 1 try + 2 retries, bounded

    def test_a_stale_model_id_raises_at_once(self):
        """404 is the tell for a catalog entry the provider no longer serves.
        Waiting 30s to be told that is worse than being told now."""
        with mock.patch("urllib.request.urlopen",
                        side_effect=[http_error(404), reply()]) as opener, \
             mock.patch("core.backends.time.sleep") as slept:
            with self.assertRaises(urllib.error.HTTPError):
                self.backend.complete("hi")
        self.assertEqual(opener.call_count, 1)
        self.assertEqual(slept.call_count, 0)

    def test_only_later_codes_retry(self):
        self.assertEqual(RETRY_CODES, {429, 500, 502, 503, 504})
        self.assertNotIn(404, RETRY_CODES)
        self.assertNotIn(400, RETRY_CODES)


class TestSamplerSeed(unittest.TestCase):
    """``--seed`` fixed the deal and left the model free, so a re-run was a
    different draw. Measured 2026-08-26: the same 20 games at seed 1000 produced
    63 missions and 9 hunts one night, 74 and 11 the next - and the gate metric
    moved with them. A comparison cannot have one variable while its instrument
    has an unmeasured one."""

    def sent(self, **kw) -> dict:
        import json
        backend = Backend.named("clean", "m", **kw)
        with mock.patch("urllib.request.urlopen", return_value=reply()) as opened:
            backend.complete("ctx")
        return json.loads(opened.call_args[0][0].data)

    def test_a_pinned_seed_reaches_the_provider(self):
        self.assertEqual(self.sent(seed=1000)["seed"], 1000)

    def test_seed_zero_is_a_seed_not_an_absence(self):
        """The falsy-seed trap: 0 is a legal seed, and a truthiness check would
        silently drop it and hand back an unseeded run wearing a seeded name."""
        self.assertEqual(self.sent(seed=0)["seed"], 0)

    def test_no_seed_asked_for_means_no_seed_claimed(self):
        """An unpinned run must not send one. A default seed would make every run
        secretly reproducible-looking while the records say nothing about it."""
        self.assertNotIn("seed", self.sent())


class TestEndpointsComeFromTheEnvironment(unittest.TestCase):
    """A box's topology is configuration, not source. The loopback defaults stay so
    a fresh clone still runs with nothing set - that is the "no dependencies, no API
    key" promise in README.md - but they are overridable."""

    def reloaded(self, **env):
        import importlib

        import core.backends as backends
        with mock.patch.dict("os.environ", env, clear=False):
            return importlib.reload(backends).ENDPOINTS

    def tearDown(self):
        import importlib

        import core.backends as backends
        importlib.reload(backends)          # leave the module as the suite found it

    def test_a_clone_with_nothing_set_gets_the_loopback_defaults(self):
        env = {k: "" for k in ("PARLOR_ENDPOINT_LOCAL", "PARLOR_ENDPOINT_CLEAN",
                               "PARLOR_ENDPOINT_GRAY")}
        got = self.reloaded(**env)
        self.assertEqual(got["local"].base_url, "http://127.0.0.1:8090/v1")
        self.assertEqual(got["clean"].base_url, "http://127.0.0.1:3001/v1")
        self.assertEqual(got["gray"].base_url, "http://127.0.0.1:3003/v1")

    def test_each_route_reads_its_own_variable(self):
        got = self.reloaded(PARLOR_ENDPOINT_LOCAL="http://box:9/v1")
        self.assertEqual(got["local"].base_url, "http://box:9/v1")
        self.assertEqual(got["clean"].base_url, "http://127.0.0.1:3001/v1")

    def test_an_EMPTY_variable_falls_back_rather_than_resolving_to_nothing(self):
        """A shell that exports an unset variable meant to unset it. Resolving that
        to "" would point every request at a URL too broken to read as a config
        mistake."""
        self.assertEqual(self.reloaded(PARLOR_ENDPOINT_GRAY="")["gray"].base_url,
                         "http://127.0.0.1:3003/v1")


class TestTheKeyHasOneSource(unittest.TestCase):
    """It was open-coded at five call sites and one of them read only the second
    variable - changeling's eval driver, the one that runs for five hours."""

    def key(self, **env):
        import importlib

        import core.backends as backends
        with mock.patch.dict("os.environ", env, clear=True):
            return importlib.reload(backends).api_key_from_env()

    def tearDown(self):
        import importlib

        import core.backends as backends
        importlib.reload(backends)

    def test_the_documented_name_wins(self):
        self.assertEqual(self.key(PARLOR_API_KEY="a", FREELLMAPI_KEY="b"), "a")

    def test_the_legacy_name_is_honoured_second(self):
        """An environment that predates the rename keeps working."""
        self.assertEqual(self.key(FREELLMAPI_KEY="b"), "b")

    def test_nothing_set_is_None_not_empty_string(self):
        self.assertIsNone(self.key())

    def test_an_EMPTY_variable_is_treated_as_unset(self):
        """Same refusal `_base_url` makes: an exported-but-empty variable meant to
        be unset, and "" would satisfy a truthiness check at the door and then fail
        every request."""
        self.assertIsNone(self.key(PARLOR_API_KEY=""))
        self.assertEqual(self.key(PARLOR_API_KEY="", FREELLMAPI_KEY="b"), "b")


class TestAnOffBoxRunRefusesToStartWithoutAKey(unittest.TestCase):
    """The failure this replaces is silent and expensive. An unauthenticated
    off-box run does not crash: it 401s every attempt, exhausts every retry, falls
    back on every decision, and reports a number - which the scorer voids AFTER the
    GPU is spent. Fail at the door instead.

    Everything is reached through the MODULE, never through a name imported at the
    top of this file. The env-var tests above reload ``core.backends``, which
    rebinds every class in it - so a module-level ``from ... import MissingKey``
    holds a stale class object, ``assertRaises`` stops matching the exception
    actually raised, and it reads as "the guard did not fire".
    """

    def setUp(self):
        import core.backends as backends
        self.b = backends

    def test_an_off_box_route_with_no_key_refuses(self):
        with self.assertRaises(self.b.MissingKey) as caught:
            self.b.require_key(self.b.ENDPOINTS["clean"], None)
        self.assertIn("PARLOR_API_KEY", str(caught.exception))
        self.assertIn("local", str(caught.exception),
                      "the refusal must name the way out")

    def test_it_is_a_SystemExit_so_it_stops_a_launcher_at_the_door(self):
        """Rather than a stack trace inside game 1 of 200."""
        self.assertTrue(issubclass(self.b.MissingKey, SystemExit))

    def test_gray_refuses_too(self):
        with self.assertRaises(self.b.MissingKey):
            self.b.require_key(self.b.ENDPOINTS["gray"], None)

    def test_local_is_keyless_and_must_not_be_blocked(self):
        self.b.require_key(self.b.ENDPOINTS["local"], None)      # raises nothing

    def test_a_key_present_passes(self):
        self.b.require_key(self.b.ENDPOINTS["clean"], "sk-whatever")

    def test_an_EMPTY_key_is_refused_rather_than_accepted(self):
        """An empty string satisfies a truthiness check at the door and then fails
        every request after it."""
        with self.assertRaises(self.b.MissingKey):
            self.b.require_key(self.b.ENDPOINTS["clean"], "")

    def test_needs_key_is_its_own_flag(self):
        """It agrees with ``parallel`` today. One is about how many workers may run,
        the other about whether an unauthenticated request is refused, so a route
        that moved on one axis and not the other would make a conflated flag wrong
        in the direction that costs a whole run."""
        self.assertFalse(self.b.ENDPOINTS["local"].needs_key)
        self.assertTrue(self.b.ENDPOINTS["clean"].needs_key)
        self.assertTrue(self.b.ENDPOINTS["gray"].needs_key)


if __name__ == "__main__":
    unittest.main()
