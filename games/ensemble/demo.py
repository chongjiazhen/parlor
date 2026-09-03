"""Run one session-0 draft. Scripted by default, model seats on ``--arm llm``.

    py -3 -m games.ensemble.demo --pack <dir-or-file> --seats 5 --seed 1
    py -3 -m games.ensemble.demo --pack <path> --arm llm --backend local

The pack is a path because a table's material is not in this tree
(``docs/content-packs.md``). Nothing here names a system.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

from core.backends import ENDPOINTS, Backend, api_key_from_env, require_key

from .pack import Pack, PackError
from .seats import ChoosingSeat
from .session import run_draft


class ScriptedSeat:
    """The random policy, wearing a seat. What a fallback plays, made explicit."""

    def __init__(self, seat: int, rng: random.Random):
        self.seat = seat
        self.rng = rng

    def choose(self, menu, taken=()):
        left = [e["name"] for e in menu if e["name"] not in set(taken)]
        return self.rng.choice(left) if left else None


def build_seats(args, pack, rng):
    if args.arm != "llm":
        return [ScriptedSeat(i, random.Random(rng.random())) for i in range(args.seats)]
    endpoint = ENDPOINTS[args.backend]
    key = api_key_from_env()
    require_key(endpoint, key)
    out = []
    for i in range(args.seats):
        backend = Backend(endpoint=endpoint, model=args.model, api_key=key,
                          temperature=args.temperature, timeout=args.timeout,
                          max_tokens=args.max_tokens, seed=args.seed,
                          enable_thinking=(False if args.no_thinking else None))
        out.append(ChoosingSeat(seat=i, backend=backend, retries=args.retries))
    return out


def resolve_pack(path) -> Path:
    p = Path(path)
    return p / "playbooks.json" if p.is_dir() else p


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Session 0: the playbook draft.")
    ap.add_argument("--pack", required=True, help="pack directory or playbooks.json")
    ap.add_argument("--seats", type=int, default=5)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--arm", choices=("scripted", "llm"), default="scripted")
    ap.add_argument("--backend", choices=tuple(ENDPOINTS), default="local")
    ap.add_argument("--model", default="")
    ap.add_argument("--temperature", type=float, default=0.8)
    ap.add_argument("--timeout", type=float, default=60.0)
    ap.add_argument("--retries", type=int, default=3)
    # A reasoning upstream spends this budget on visible thinking before it
    # answers, and a run that never emits JSON reads in the summary as a model
    # that cannot follow the rules. Measured on the clean tier at max_tokens=8:
    # auto:reliable and auto:fast both returned finish_reason "length" with the
    # whole reply in reasoning_content.
    ap.add_argument("--max-tokens", type=int, default=1536)
    ap.add_argument("--no-thinking", action="store_true",
                    help="ask the provider to disable visible reasoning")
    ap.add_argument("--json", action="store_true", help="print the record only")
    args = ap.parse_args(argv)
    # A pack may carry any script; the console's cp1252 default raises AFTER a
    # partial write, so the failure looks like a truncated run rather than an
    # encoding fault.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    try:
        pack = Pack.load(resolve_pack(args.pack))
    except PackError as exc:
        print(f"pack: {exc}", file=sys.stderr)
        return 2
    rng = random.Random(args.seed)
    try:
        seats = build_seats(args, pack, rng)
    except Exception as exc:                       # noqa: BLE001 - reported, not swallowed
        print(f"backend: {exc}", file=sys.stderr)
        return 3
    rec = run_draft(pack, seats, seed=args.seed)

    if args.json:
        print(json.dumps(rec, ensure_ascii=False, indent=1))
        return 0
    print(f"pack {rec['pack']}  seats {rec['seats']}  seed {rec['seed']}  arm {args.arm}")
    for seat in sorted(rec["picks"]):
        print(f"  seat {seat}: {rec['picks'][seat]}")
    served = {u for u in rec["upstreams"].values() if u}
    if served:
        print("served by: " + ", ".join(sorted(served)))
    print(f"fell back: {rec['fallbacks']}/{rec['seats']} "
          f"({rec['fallback_rate']:.0%})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
