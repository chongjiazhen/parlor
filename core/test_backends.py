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

from core.backends import RETRY_CODES, Backend


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


if __name__ == "__main__":
    unittest.main()
