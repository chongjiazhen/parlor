"""``parlor doctor`` - can this box put models in the other seats, and which one?

Everything a person needs before a live game is true of the BOX, not of the repo,
so no flag and no ``--help`` can answer it: which route is reachable, whether the
key that route needs is set, and which model ids the router will actually accept.
Without this the sequence is three hand-written ``curl`` calls, and the failure it
prevents is the expensive one - a run that starts, falls back on every decision
because the endpoint was never reachable, and reports a number that is the random
policy wearing a model's name.

**A catalog listing is not a promise, and this module says so rather than implying
it.** ``/v1/models`` answers from configuration: the local router lists a model that
is merely CONFIGURED, and a cloud tier lists one whose upstream is cooled down. Both
serve a listed id with ``model_not_armed`` or ``model_not_found`` at call time. So
the listing is reported as a catalog, and ``--probe`` sends a real one-token
completion through ``Backend`` - the same class a game uses, so a probe that passes
is evidence about the path the game will take and not about a neighbouring one.

Probing is opt-in because it is not free everywhere: on ``local`` it occupies the
GPU for a moment, and on the off-box tiers it spends a request against a free quota.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

from core.backends import ENDPOINTS, Backend, Endpoint, api_key_from_env

#: Short on purpose. This is a reachability question, and a route that needs ten
#: seconds to answer it is one a person wants told about now rather than waited on.
TIMEOUT = 6.0

#: The catalog line is truncated rather than wrapped - a gateway can list a hundred
#: ids and the answer to "is this route alive" does not improve after the first few.
MAX_MODELS_SHOWN = 6


def catalog(endpoint: Endpoint, key: str | None,
            timeout: float = TIMEOUT) -> tuple[str, list[str]]:
    """``(status, model ids)``. Never raises: every failure here is a line to print.

    The status strings are plain English rather than codes, because the reader is a
    person deciding what to type next and the remedy differs per failure - an
    unreachable loopback port means start the server, a 401 means export the key.
    """
    req = urllib.request.Request(endpoint.base_url.rstrip("/") + "/models")
    if key:
        req.add_header("Authorization", "Bearer " + key)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            return f"refused ({exc.code}) - the key was rejected", []
        return f"reachable, but /models says {exc.code}", []
    except urllib.error.URLError as exc:
        return f"unreachable - {exc.reason}", []
    except json.JSONDecodeError:
        return "answered, but not with a model list", []
    except (TimeoutError, OSError) as exc:
        return f"unreachable - {exc}", []
    ids = [str(m.get("id")) for m in (body.get("data") or []) if m.get("id")]
    return "live", ids


def probe(endpoint: Endpoint, key: str | None, model: str,
          timeout: float = TIMEOUT) -> str:
    """One real completion, through the class the games use.

    ``max_tokens=1`` and ``rate_retries=0``: this asks whether the path answers at
    all, and a throttle retried four times would turn a diagnostic into a wait. One
    token is enough - the question is served-or-not, never quality.
    """
    backend = Backend(endpoint=endpoint, model=model, api_key=key,
                      max_tokens=1, timeout=timeout, rate_retries=0,
                      temperature=0.0)
    try:
        _, served_by = backend.complete_meta("ok")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:160].replace("\n", " ")
        return f"REFUSED {exc.code} {detail}".rstrip()
    except Exception as exc:  # noqa: BLE001 - every failure is a line, not a crash
        return f"REFUSED {type(exc).__name__}: {exc}"
    return f"answered, served by {served_by!r}"


def report(routes=None, do_probe: bool = False, model: str | None = None,
           timeout: float = TIMEOUT) -> tuple[str, int]:
    """The whole report as text, plus the exit code.

    Exit 1 when NO route can serve a game, so this is usable as a gate in front of a
    long unattended run. One live route is a success even if the other two are down:
    a person needs one.
    """
    routes = routes if routes is not None else ENDPOINTS
    key = api_key_from_env()
    lines = ["parlor doctor - can this box seat models?", ""]
    usable = 0

    for name, endpoint in routes.items():
        if not endpoint.needs_key:
            key_note = "keyless"
        elif key:
            key_note = "key set"
        else:
            key_note = "no key (export PARLOR_API_KEY)"
        status, ids = catalog(endpoint, key if endpoint.needs_key else None, timeout)
        if status == "live":
            usable += 1
        lines.append(f"  {name:<6} {endpoint.base_url}")
        lines.append(f"         {endpoint.note}; {key_note}")
        lines.append(f"         {status}")
        if ids:
            shown = ", ".join(ids[:MAX_MODELS_SHOWN])
            extra = len(ids) - MAX_MODELS_SHOWN
            more = f", +{extra} more" if extra > 0 else ""
            lines.append(f"         catalog: {shown}{more}")
        if do_probe and status == "live":
            target = model or (ids[0] if ids else None)
            if target is None:
                lines.append("         probe: skipped - the catalog named no model")
            else:
                verdict = probe(endpoint, key if endpoint.needs_key else None,
                                target, timeout)
                lines.append(f"         probe {target}: {verdict}")
        lines.append("")

    if usable:
        lines += [
            "A catalog entry is configuration, not a promise: an id can be listed and",
            "cold, and the call then fails with model_not_armed or model_not_found.",
            "Confirm one with a real call:",
            "  parlor doctor --probe",
            "",
            "Then play, pinning the id that answered:",
            "  parlor play cabal --human 0 --backend local --model <id>",
        ]
    else:
        lines += [
            "No route can serve a game. The games still run with no model at all -",
            "random players in the other seats, which is the cheapest way to learn",
            "the flow before spending a GPU on it:",
            "  parlor play cabal --human 0",
        ]
    return "\n".join(lines), (0 if usable else 1)


USAGE = """\
usage: parlor doctor [--probe] [--model ID]

Reports which backend routes this box can reach, whether the key each one needs is
set, and what models it lists. --probe additionally sends one real one-token
completion per live route, which is the only check that tells a listed model from
an armed one."""


def main(argv: list[str]) -> int:
    """``doctor [--probe] [--model ID]``, parsed by hand for the reason
    ``parlor.__main__`` gives for not using argparse: two string comparisons cannot
    claim an abbreviation out of a command line meant for something else."""
    do_probe = False
    model = None
    rest = list(argv)
    while rest:
        arg = rest.pop(0)
        if arg == "--probe":
            do_probe = True
        elif arg == "--model":
            if not rest:
                print("--model needs an id", file=sys.stderr)
                return 2
            model = rest.pop(0)
        elif arg in ("-h", "--help"):
            print(USAGE)
            return 0
        else:
            print(f"unknown doctor flag {arg!r}\n\n{USAGE}",
                  file=sys.stderr)
            return 2
    text, code = report(do_probe=do_probe, model=model)
    print(text)
    return code
