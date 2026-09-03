"""Run DURF sessions and report whether gate #1 held.

``eval/durf_score.py`` scores rulings in isolation and says, in its own docstring,
that it does not exercise gate #1 at all - there is no player seat, so there is
nothing for a world fact to leak TO. **This driver is the half that does.** One
fixed dungeon, three player seats, a deterministic kernel, and a model adjudicator
that declares its reveals as typed facts.

**What it reports, and the sentence to quote instead of a wider one.** Whether a
render can be audited against the facts the adjudicator declared, with
``find_leaks`` unchanged. Not whether the session was good, coherent or
well-refereed - there is no fixture for that and no judge is built for one, the
same refusal ``docs/durf-rung.md`` makes about decision 5.

**A leak is a MEASUREMENT here, and that is why this driver differs from the other
two.** ``eval/run_changeling.py`` re-raises on a leak because its referee is
deterministic: a leak there is an engine bug and nothing downstream of it is
scoreable. Here the referee is a model, so a leak is model behaviour and the thing
being measured. ``play_session`` still RAISES - gate #1 is the driver's guarantee
and no caller can opt out of it - and this driver catches it per session, ENDS
that session at the leak so no further bytes leave, names the fact and the line
that carried it, and runs the next one.

The ``scripted`` arm needs no model and no GPU. It is the instrument control: its
referee declares before it narrates by construction, so a leak in that arm means
the ENGINE leaks and no live number means anything until it is fixed. Run it
before quoting anything from a live arm.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time

from core import integrity
from core.backends import ENDPOINTS, Backend, api_key_from_env, require_key
from core.runlog import (RunState, claim_record, record_paths,
                         run_with_marker)
from core.stats import wilson
from games.durf import rules, seats, session as session_mod

RUN_STATE = RunState()


def build_backend(args) -> Backend | None:
    if args.arm != "llm":
        return None
    return Backend(
        endpoint=ENDPOINTS[args.backend], model=args.model,
        api_key=api_key_from_env(),
        system_prompt=seats.ADJUDICATOR_SYSTEM_PROMPT,
        temperature=args.temperature, timeout=args.timeout,
        max_tokens=args.max_tokens, seed=args.seed,
        enable_thinking=(False if args.no_thinking else None))


def build_seats(sess, args, backend, rng):
    """The party and the referee for one session.

    The players stay SCRIPTED even on the live arm unless ``--llm-players`` is
    passed, and that is a measurement decision rather than a saving: this rung's
    question is about the referee's declarations, and a party that varies makes
    the adjudicator's job vary with it. A live party is a second variable and it
    gets its own flag.
    """
    if args.arm == "llm" and args.llm_players:
        players = {s: seats.LLMPlayer(backend=Backend(
            endpoint=ENDPOINTS[args.backend], model=args.model,
            api_key=api_key_from_env(),
            system_prompt=seats.PLAYER_SYSTEM_PROMPT,
            temperature=args.temperature, timeout=args.timeout,
            max_tokens=args.max_tokens, seed=args.seed,
            enable_thinking=(False if args.no_thinking else None)), seat=s)
            for s in sess.kernel.pcs}
    else:
        players = {s: seats.ScriptedPlayer(s, random.Random(rng.random()))
                   for s in sess.kernel.pcs}
    adjudicator = (seats.LLMAdjudicator(backend=backend, retries=args.retries)
                   if args.arm == "llm"
                   else seats.ScriptedAdjudicator(random.Random(rng.random())))
    return players, adjudicator


def one_session(index: int, args) -> session_mod.SessionRecord:
    seed = None if args.seed is None else args.seed + index
    rng = random.Random(seed)
    sess = session_mod.new(seed=seed)
    players, adjudicator = build_seats(sess, args, build_backend(args), rng)
    try:
        rec = session_mod.play_session(sess, players, adjudicator,
                                       rounds=args.rounds)
    except session_mod.LeakDetected as leak:
        # Named and recorded, and the session stops here: gate #1 failing is this
        # rung's result, and continuing to render after one would be sending bytes
        # the audit has already refused. The record comes off the EXCEPTION rather
        # than being rebuilt - a fresh one would drop the decisions the session
        # made before it leaked, and the run's fallback rate would then be over a
        # denominator missing exactly the sessions that went wrong.
        rec = leak.record
        rec.error = f"LeakDetected: {leak}"
    except Exception as exc:            # one bad session must not kill the run
        rec = session_mod.SessionRecord(rounds=args.rounds)
        rec.error = f"{type(exc).__name__}: {exc}"
    rec.seed = seed
    return rec


def as_line(index: int, rec: session_mod.SessionRecord) -> str:
    return json.dumps({
        "index": index, "seed": rec.seed, "rounds": rec.rounds,
        "turns": rec.turns, "gate1_held": rec.gate1_held, "leaks": rec.leaks,
        "declared": rec.declared, "undeclared": rec.undeclared,
        "decisions": rec.decisions, "fallbacks": rec.fallbacks,
        "recovered": rec.recovered, "refused_attempts": rec.refused_attempts,
        "rule_refused_attempts": rec.rule_refused_attempts,
        "decision_log": rec.decision_log, "transcript": rec.transcript,
        "error": rec.error})


def score(records: list) -> dict:
    """Gate #1, and the accounting every number in this repo ships beside.

    ``audited`` is the denominator and it is the sessions that actually reached a
    verdict - a session that errored before any render was audited did not pass
    gate #1 and did not fail it, and pooling it either way makes the denominator a
    statement about crashes.
    """
    audited = [r for r in records if r.gate1_held is not None]
    held = [r for r in audited if r.gate1_held]
    leaked = [r for r in audited if not r.gate1_held]
    facts_leaked: dict[str, int] = {}
    for rec in leaked:
        for entry in rec.leaks:
            for fact, term in entry["leaks"]:
                key = f"{fact} via {term!r}"
                facts_leaked[key] = facts_leaked.get(key, 0) + 1
    return {
        "sessions": len(records),
        "audited": len(audited),
        "unaudited": len(records) - len(audited),
        "gate1": {
            "held": len(held), "leaked": len(leaked),
            "hold_rate": len(held) / len(audited) if audited else None,
            "ci95": wilson(len(held), len(audited)) if audited else None,
        },
        "leaked_facts": dict(sorted(facts_leaked.items(),
                                    key=lambda kv: -kv[1])),
        "evidence": [line for rec in leaked for entry in rec.leaks
                     for line in entry["evidence"]][:10],
        "turns": sum(r.turns for r in records),
        "errors": [r.error for r in records if r.error][:6],
        "integrity": integrity.summarise(records, trace_lines=6),
    }


def report(s: dict, args, elapsed: float) -> list[str]:
    i = s["integrity"]
    out = [f"=== {s['sessions']} DURF sessions ({args.arm} arm, "
           f"backend={args.backend or 'none'}, model={args.model}, "
           f"{args.rounds} rounds) in {elapsed:.1f}s ===",
           f"ruleset {rules.RULESET}. {rules.ATTRIBUTION}", ""]
    out += integrity.report_lines(i)
    out.append("  (the unit here is one adjudicator or player decision; a 'clean "
               "game' above is one session nothing was sent back on)")

    g = s["gate1"]
    out += ["", "gate #1 - is a render auditable against the facts the "
                "adjudicator declared"]
    if not s["audited"]:
        out.append("  NO VERDICT: no session reached an audited render.")
    else:
        band = ("" if not g["ci95"]
                else f"  [{g['ci95'][0]:.2%}, {g['ci95'][1]:.2%}]")
        out.append(f"  held in {g['held']}/{s['audited']} sessions "
                   f"({g['hold_rate']:.2%}){band}")
        if s["unaudited"]:
            out.append(f"  {s['unaudited']} session(s) reached no audited render "
                       f"and are OUT of that denominator - not a pass")
    if i["fallback_rate"] > integrity.VOID_BAR:
        out += ["", f"VOID: {i['fallback_rate']:.2%} of decisions fell back, above "
                    f"the {integrity.VOID_BAR:.0%} bar. The rate above is not this "
                    f"model's."]
        return out

    if s["leaked_facts"]:
        out += ["", "  the facts that reached a seat undeclared:"]
        out += [f"    {count}x {key}" for key, count in s["leaked_facts"].items()]
        out += ["", "  the referee lines that carried them:"]
        out += [f"    {line}" for line in s["evidence"]]
    elif s["audited"]:
        out.append("  no undeclared world fact reached any seat's context.")

    if args.arm == "scripted":
        out += ["", "  (the scripted arm is the INSTRUMENT CONTROL, not a "
                    "baseline: its referee declares before it narrates by "
                    "construction, so a leak here means the engine leaks)"]
    if s["errors"]:
        out += ["", "  sessions that ended early:"]
        out += [f"    {e}" for e in s["errors"]]
    if i["trace_sample"]:
        out += ["", "  why turns were refused or retried:"]
        out += [f"    {line}" for line in i["trace_sample"]]
    return out


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", choices=list(seats.ARMS), default="scripted")
    ap.add_argument("--sessions", type=int, default=1)
    ap.add_argument("--rounds", type=int, default=3,
                    help="turns per seat; one round is one declaration each")
    ap.add_argument("--backend", choices=list(ENDPOINTS))
    ap.add_argument("--model", default="auto")
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--temperature", type=float, default=0.0,
                    help="0.0 by default here, unlike the player-facing default: "
                         "measured on the isolated instrument, greedy decoding is "
                         "seed-invariant and buys accuracy a referee has no use "
                         "for sampling on (docs/durf-rung.md, the temperature arm)")
    ap.add_argument("--max-tokens", type=int, default=1536)
    ap.add_argument("--timeout", type=float, default=120.0)
    ap.add_argument("--no-thinking", action="store_true")
    ap.add_argument("--llm-players", action="store_true",
                    help="put a model in the player seats too. A SECOND variable - "
                         "this rung's question is about the referee")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--out", help="write the summary here as JSON; the per-session "
                                  "JSONL is its sibling")
    args = ap.parse_args()

    if args.arm == "llm" and not args.backend:
        ap.error("--arm llm needs --backend; a live arm with no endpoint would "
                 "fall back on every turn and score the scripted referee")
    if args.backend:
        require_key(ENDPOINTS[args.backend], api_key_from_env())

    # The same door: an occupied record path is refused before a session is
    # played, not discovered when two files disagree afterwards.
    if args.out:
        claim_record(args.out)

    RUN_STATE.requested = args.sessions
    started = time.time()
    records = []
    for index in range(args.sessions):
        rec = one_session(index, args)
        records.append(rec)
        RUN_STATE.landed += 1
        if args.out:
            with open(record_paths(args.out)[1], "a", encoding="utf-8") as fh:
                fh.write(as_line(index, rec) + "\n")
        held = {True: "gate #1 held", False: "GATE #1 LEAKED",
                None: "unaudited"}[rec.gate1_held]
        print(f"[{index + 1}/{args.sessions}] {held}, {rec.turns} turns, "
              f"{rec.fallbacks}/{rec.decisions} fell back"
              + (f" - {rec.error}" if rec.error else ""), flush=True)

    scored = score(records)
    print("\n".join(report(scored, args, time.time() - started)))

    if args.out:
        with open(record_paths(args.out)[0], "w", encoding="utf-8") as fh:
            json.dump({"score": scored, "args": vars(args)}, fh, indent=2)
        print(f"\nwrote {record_paths(args.out)[0]}")


if __name__ == "__main__":
    sys.exit(run_with_marker(main, RUN_STATE))
