"""Play one DURF session and audit gate #1 on every render.

By default a scripted party and a scripted referee run the whole session with no
model at all, which is the same instrument control ``eval/durf_session.py``
describes: the scripted adjudicator declares before it narrates by construction,
so a leak on this arm means the ENGINE leaks.

    python -m parlor play durf                          # scripted party and referee
    python -m parlor play durf --rounds 2
    python -m parlor play durf --arm llm --backend local --model qwen36-35b-a3b-iq3
    python -m parlor play durf --human 0                # you play Vesh
    python -m parlor play durf --human 0 --arm llm --backend local

**``--human`` seats a person in a PARTY seat, never in the referee's.** The party
is the side of the boundary gate #1 guards - a person in the referee's chair
would hold the whole world and there would be nothing to audit - so a human
adjudicator is not a flag this driver withholds, it is a different measurement.

What a person in a party seat is handed is ``Session.deliver``'s return value and
nothing else: the same string that seat's model would receive, through the same
entitlement audit, which raises before a byte carrying an undeclared world fact
can reach the terminal. If the person can work out what is behind the iron door,
they worked it out from bytes a model would have had too.

This driver reports one session for a reader. It writes no record and scores
nothing: ``eval/durf_session.py`` is the measurement lane and stays the only
thing that produces a number.
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

from core.backends import (Backend, ENDPOINTS, api_key_from_env, require_key)
from core.console import ConsoleBackend, human_seats
from games.durf import rules, seats, session as session_mod
from games.durf.seats import PLAYER_KEYS as ACTION_KEYS

#: Console furniture, printed once beside the view and never inside it. See
#: ``core/console.py`` §COMMANDS for why this does not touch the payload: the
#: per-turn ask says what this character may do and is silent on what a dungeon
#: session IS, and a model arrives knowing the shape while a person does not.
BRIEFING = """durf in one screen. You are one character in a party of three, in a barrow, with
a referee who holds the whole world. There is no win condition and no score: the
session runs for a fixed number of rounds and stops.

  Your turn   say what your character does, in a sentence. The referee rules on
              it, calls the kernel for anything mechanical, and narrates what the
              table sees.
  The dice    are never yours. You never roll, never total, never state a result.
  Your sheet  is above your view in full - attributes, slots, Armor, Wounds,
              Stress, what you carry. All of it is public at this table.
  Secret      is the world, not the seats: room contents you have not entered,
              whether something is trapped, an NPC's statistics, what lies past
              your light. Every seat is equally un-entitled to those, and the
              referee has to declare one before it can reach you.

Shorthand for this game:   do I lift the flagstone with my dagger
                           say hold the light steady; do I step onto the bridge
                           think the far side is too quiet

'rules' prints the DURF mechanics this session runs on.
"""


class DurfConsole(ConsoleBackend):
    """A console whose ``rules`` prints this rung's pinned digest.

    Every other rung points ``rules_path`` at its own ``RULES.md``, so a player
    and a scorer never read two different accounts of one rule. DURF's canonical
    statement is not a file in this tree - it is ``rules.KERNEL_DIGEST``, the
    pinned, length-stable paraphrase of DURF 2.2 that the adjudicator is given and
    every recorded number was scored against. Pointing at that constant keeps the
    single source; writing a RULES.md beside it would be the second account.
    """

    def _rules(self) -> str:
        return f"{rules.RULESET}\n\n{rules.KERNEL_DIGEST}\n\n{rules.ATTRIBUTION}"


def opening_view(session, humans: set[int]) -> str:
    """What this driver prints before the first declaration.

    The reader's peek is the REFEREE's view, and it lists every undeclared world
    fact by id and by text - what is behind the iron door, which anchor is rotted,
    what the wight can do. That is exactly the corpus gate #1 keeps out of a
    seat's context, so printing it beside a person playing a seat hands over, in
    one screen, everything the audit spends the whole session withholding.

    The session's own audit cannot catch this. It grades what the REFEREE renders
    to a seat, and this print is the harness talking past it - so the guard lives
    here, in a function a test can call, rather than as a branch inside ``main``.
    """
    if humans:
        seat = next(iter(humans))
        return (f"(you are playing seat {seat}; the referee's view of the world "
                "is withheld until the session ends)")
    return ("--- the referee's view of the world, the reader's peek ---\n"
            + seats.referee_view(session))


def build_players(session, args, rng: random.Random) -> dict:
    """Seat -> player. A human seat is an ``LLMPlayer`` over a console backend:
    same prompt, same parser, same refuse-and-retell loop, so a person's typing is
    judged by the code that judges a model's reply and not by a second one.

    Its retry budget is wide because the fallback at the end of that loop plays a
    SCRIPTED line on the seat's behalf, and a person who mistypes twice has not
    decided to hand their character to the control policy.
    """
    humans = human_seats(args.human, len(session.kernel.pcs), args.seed)
    scripted = {s: seats.ScriptedPlayer(s, random.Random(rng.random()))
                for s in session.kernel.pcs}
    if not humans:
        return scripted
    seat = next(iter(humans))
    console = DurfConsole(keys=ACTION_KEYS, briefing=BRIEFING,
                          other_model=(args.model if args.arm == "llm"
                                       else "a scripted party and referee"),
                          seed=args.seed)
    scripted[seat] = seats.LLMPlayer(backend=console, seat=seat,
                                     retries=args.human_retries,
                                     fallback=seats.ScriptedPlayer(seat))
    return scripted


def build_adjudicator(args, rng: random.Random):
    """The referee's seat: scripted by default, a model on ``--arm llm``.

    A human never sits here. The referee holds every undeclared fact, so there is
    no entitlement boundary to audit around it and nothing this driver prints to
    that seat could be a leak - which makes a human referee a different question
    with a different instrument, not a flag.
    """
    if args.arm != "llm":
        return seats.ScriptedAdjudicator(random.Random(rng.random()))
    backend = Backend(
        endpoint=ENDPOINTS[args.backend], model=args.model,
        api_key=api_key_from_env(),
        system_prompt=seats.ADJUDICATOR_SYSTEM_PROMPT,
        temperature=args.temperature, timeout=args.timeout,
        max_tokens=args.max_tokens, seed=args.seed,
        enable_thinking=(False if args.no_thinking else None))
    return seats.LLMAdjudicator(backend=backend, retries=args.retries)


DUNGEONS = Path(__file__).resolve().parent / "dungeons"


def dungeon_dir(name):
    """Resolve ``--dungeon`` to a directory, or None for the shipped one.

    A bare name is looked up under ``dungeons/``; anything else is taken as a
    path. Both are checked here rather than at load, so a typo names the
    dungeons that DO exist instead of raising on a missing scenario.json.
    """
    if name is None:
        return None
    cand = DUNGEONS / name
    root = cand if cand.is_dir() else Path(name)
    if not (root / "scenario.json").is_file():
        have = []
        if DUNGEONS.is_dir():
            have = sorted(d.name for d in DUNGEONS.iterdir() if d.is_dir())
        raise SystemExit(
            f"no dungeon at {root}: it holds no scenario.json. "
            f"Dungeons that ship: {have or [chr(40)+chr(41)]}")
    return root


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--rounds", type=int, default=3,
                    help="one round is one declaration from each living seat")
    ap.add_argument("--arm", choices=list(seats.ARMS), default="scripted",
                    help="who referees (default: the scripted control, no model)")
    ap.add_argument("--backend", choices=list(ENDPOINTS),
                    help="endpoint for the referee's model")
    ap.add_argument("--model", default="auto")
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--temperature", type=float, default=0.0,
                    help="greedy by default, as the eval lane is: a referee has "
                         "no use for sampling (docs/durf-rung.md)")
    ap.add_argument("--max-tokens", type=int, default=1536)
    ap.add_argument("--timeout", type=float, default=120.0)
    ap.add_argument("--no-thinking", action="store_true")
    ap.add_argument("--dungeon", default=None, metavar="NAME|DIR",
                    help="a dungeon under games/durf/dungeons/, or a path to a "
                         "directory holding scenario.json and facts.json "
                         "(default: the shipped graded dungeon)")
    ap.add_argument("--human", metavar="SEAT",
                    help="play ONE party seat yourself: a seat number, or "
                         "`random` to draw one from --seed (a terminal is one "
                         "channel, so it seats one person)")
    ap.add_argument("--human-retries", type=int, default=99,
                    help="mistyped answers a human seat may make before its turn "
                         "falls back to a scripted line (default: effectively "
                         "unlimited)")
    return ap


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parser().parse_args()

    if args.arm == "llm" and not args.backend:
        raise SystemExit(
            "--arm llm needs --backend; a live referee with no endpoint would "
            "fall back on every turn and run the scripted control under a "
            "model's name")
    if args.backend:
        require_key(ENDPOINTS[args.backend], api_key_from_env())

    rng = random.Random(args.seed)
    session = session_mod.new(seed=args.seed, path=dungeon_dir(args.dungeon))
    players = build_players(session, args, rng)
    adjudicator = build_adjudicator(args, rng)
    humans = human_seats(args.human, len(session.kernel.pcs), args.seed)

    print(f"=== a DURF session, {rules.RULESET}. {rules.ATTRIBUTION} ===")
    print(f"=== {len(session.kernel.pcs)} party seats, {args.rounds} rounds, "
          f"referee: {args.arm} ===\n")
    print(opening_view(session, humans))
    print("\n--- play ---")

    leaked = None
    try:
        rec = session_mod.play_session(session, players, adjudicator,
                                       rounds=args.rounds)
    except session_mod.LeakDetected as leak:
        # Gate #1 raised, which is this rung's measurement rather than a crash.
        # The session stops here: continuing to render would send bytes the audit
        # has already refused.
        rec, leaked = leak.record, leak
    except KeyboardInterrupt:
        print("\n(session abandoned)")
        return

    for entry in session.transcript:
        print(entry.line())

    # Three states, never two. ``None`` is a session that reached no audited
    # render: it did not pass gate #1 and it did not fail it, and printing it as
    # either is the pooling ``eval/durf_session.py`` §score refuses to do.
    verdict = {True: "CLEAN", False: "LEAKED",
               None: "NO VERDICT - no render was audited"}[rec.gate1_held]
    print(f"\ngate #1 leak audit: {verdict} "
          f"({len(session.kernel.pcs)} seats, every render)")
    if leaked is not None:
        print(f"  {leaked}")
    print(f"turns: {rec.turns}, decisions: {rec.decisions}, "
          f"fell back: {rec.fallbacks}")
    if rec.error:
        print(f"  {rec.error}")

    print("\n(the world, referee-side only:)")
    print(f"  declared to the party: {rec.declared or '(none)'}")
    print(f"  never declared:        {rec.undeclared or '(none)'}")


if __name__ == "__main__":
    main()
