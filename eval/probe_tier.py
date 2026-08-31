"""Burst-probe a backend tier before trusting it to carry a run.

A single call is not a liveness test. A key under cooldown serves the occasional
request while failing a stream, so a one-shot probe reports healthy about a tier
that cannot finish a game - and the tell is invisible from the one call, because
that call succeeds normally. Measured 2026-08-25 on the gray tier: a pinned
``gpt-oss-120b`` served 1 of 12, and the ONE success was the fastest call of the
set at 0.4s. Anyone probing once would have started a 25-game run against it.

The second thing a burst shows is WHO is answering. ``auto`` served 12 of 12 in
the same minute and looked healthy - but every upstream it routed to was a 20B or
30B-a3b model, because the large ones were exactly what had cooled. Availability
is not capability. Only the response body's top-level ``model`` says who answered,
so this prints it per call rather than trusting the requested id.

Usage::

    python -m eval.probe_tier --backend gray --model gpt-oss-120b
    python -m eval.probe_tier --backend gray --model auto -n 20
    python -m eval.probe_tier --backend local --model hexis-active

Exit status is 0 when the tier carried the burst, 1 when it did not, so this can
gate a run script.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

from core.backends import ENDPOINTS


def probe_once(url: str, model: str, key: str | None, timeout: float) -> tuple[int | str, float, str, str]:
    """One call. Returns (status, seconds, served_model, detail).

    ``status`` is an HTTP code, or an exception name when nothing came back.
    """
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "Reply with the single word: ok"}],
        "max_tokens": 8,
        "temperature": 0,
    }).encode()
    req = urllib.request.Request(
        url.rstrip("/") + "/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    if key:
        req.add_header("Authorization", f"Bearer {key}")
    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            obj = json.loads(resp.read().decode("utf-8", "replace"))
            text = (obj.get("choices") or [{}])[0].get("message", {}).get("content", "")
            # the REQUESTED id is not the served one - only the body says who answered
            return resp.status, time.monotonic() - started, str(obj.get("model", "?")), text.strip()[:24]
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:120].replace("\n", " ")
        return e.code, time.monotonic() - started, "", detail
    except Exception as e:  # timeout, refused, reset - all "no answer", none fatal here
        return type(e).__name__, time.monotonic() - started, "", str(e)[:120]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--backend", default="gray", choices=sorted(ENDPOINTS))
    ap.add_argument("--model", default="auto")
    ap.add_argument("--require-served",
                    help="fail unless every successful response names this exact "
                         "upstream model in its response body")
    ap.add_argument("-n", "--calls", type=int, default=12,
                    help="burst size; 12 is enough to expose a cooldown (default: 12)")
    # A probe asks for 8 tokens. A call that has not answered in 30s is not slow,
    # it is wedged - and a gate that waits 12 x 120s is a gate nobody puts in front
    # of a run.
    ap.add_argument("--timeout", type=float, default=30.0)
    args = ap.parse_args(argv)

    endpoint = ENDPOINTS[args.backend]
    # same key convention as eval.run_cabal - never a path into anyone's config
    key = os.environ.get("PARLOR_API_KEY") or os.environ.get("FREELLMAPI_KEY")
    if args.backend != "local" and not key:
        print(f"{args.backend} needs a key: set PARLOR_API_KEY or FREELLMAPI_KEY", file=sys.stderr)
        return 2

    print(f"{args.backend} {endpoint.base_url} model={args.model} n={args.calls}")
    ok: list[float] = []
    codes: dict[object, int] = {}
    served: dict[str, int] = {}
    n = args.calls
    failed = 0
    made = 0
    for i in range(1, n + 1):
        status, secs, who, detail = probe_once(endpoint.base_url, args.model, key, args.timeout)
        made = i
        codes[status] = codes.get(status, 0) + 1
        if status == 200:
            ok.append(secs)
            served[who] = served.get(who, 0) + 1
            print(f"[{i:2}/{n}] 200 {secs:6.1f}s served={who} {detail!r}")
        else:
            failed += 1
            print(f"[{i:2}/{n}] {status} {secs:6.1f}s {detail}")
        # The verdict needs ok >= n-1, so two failures decide it. Keep going and a
        # wedged tier costs n x timeout, which is why nobody would gate on this.
        if failed > 1:
            print(f"[--/{n}] stopping early: {failed} failures, the verdict cannot change")
            break

    print(f"\nok={len(ok)}/{made} attempted (burst of {n}) "
          f"codes={ {str(k): v for k, v in codes.items()} }")
    if ok:
        ok.sort()
        print(f"latency ok: min={ok[0]:.1f}s med={ok[len(ok) // 2]:.1f}s max={ok[-1]:.1f}s")
    if served:
        print("served upstreams: " + ", ".join(f"{m} x{c}" for m, c in sorted(served.items(), key=lambda kv: -kv[1])))
        if len(served) > 1:
            print("  NOTE: more than one upstream answered - availability is not capability.")
            print("  Pin a model before any A/B, and stratify results by served upstream.")
    wrong = {name: count for name, count in served.items()
             if args.require_served is not None and name != args.require_served}
    carried = len(ok) >= n - 1 and not wrong
    if wrong:
        print("  WRONG UPSTREAM: expected "
              f"{args.require_served}; got "
              + ", ".join(f"{name} x{count}" for name, count in wrong.items()))
    print("VERDICT:", "can carry a stream" if carried else
          "wrong upstream served" if wrong else
          "PARTIAL - single calls serve, a stream does not" if ok else
          "tier is not answering")
    return 0 if carried else 1


if __name__ == "__main__":
    raise SystemExit(main())
