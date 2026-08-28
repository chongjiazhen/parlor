"""Play one belfry game and audit gate #1 every turn.

The twin of the other rungs' demos, and it exists for the same two reasons: to run
the state machine and the leak audit with no model at all, and to seat a person at
the table.

    py -3 -m games.belfry.demo                        # random players, no model
    py -3 -m games.belfry.demo --seats 7 --seed 11
    py -3 -m games.belfry.demo --script compact       # the cheap payload
    py -3 -m games.belfry.demo --human 0
    py -3 -m games.belfry.demo --human 0 --backend local --model qwen36-35b-a3b-iq3

``--human`` hands that seat the exact bytes its model would receive and nothing
else. ONE seat and ONE game: a terminal is a single channel, so two people at it
would read each other's private view. Without ``--backend`` the other seats are
the random control, which is playable but not an opponent; pair the two flags for
a real table.

Nothing here is a measurement - it prints one game and stops.
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

from core.backends import (Backend, ENDPOINTS, REGISTERS, api_key_from_env,
                           require_key)
from core.console import ConsoleBackend, human_seats
from games.belfry.audit import leak_audit
from games.belfry.player import (ACTION_KEYS, LLMPolicy, RandomPolicy,
                                 play_game)
from games.belfry.referee import BelfryReferee
from games.belfry.roles import DEFAULT_SCRIPT, DISTRIBUTION, SCRIPTS

#: Console furniture, never the payload - see ``core/console.py``.
BRIEFING = """belfry in one screen. A circle of seats. A demon and its minions know each
other; everybody else knows almost nothing, and some of what they do know is
false.

  Nights     roles wake in a fixed order. Some are asked to choose a seat, some
             are simply told something. A seat whose ability has been switched
             off is told something FALSE, in the same words, and is not told
             that.
  Days       everyone talks - the dead included. Then any living seat may
             nominate one seat once, and everyone with a vote answers each
             nomination at the same time. Most votes, at least half the living
             seats, is executed at dusk.
  Dying      the dead keep their voice all game and one single vote.
  Win        good wins when the demon is dead. Evil wins when two seats are left
             alive with the demon among them, or when the good side executes the
             one seat it must not.
  Public     everything said, every nomination, every vote count, every death.
             No role is ever named out loud by the referee.
  Secret     every role, every night action, everything you were told.

'rules' prints the full rules.
"""

RULES_PATH = str(Path(__file__).with_name("RULES.md"))


def opening_view(ref: BelfryReferee, humans: set[int]) -> str:
    """What the demo prints before the first move.

    The reader's peek at one seat's view is a LEAK once a person is at the table:
    the sample names what that seat is, and on a table this small that narrows
    every other seat. The referee's own audit cannot catch it - that audit grades
    what the REFEREE renders to a seat, and this print is the harness talking past
    it. So the guard lives here, in a function a test can call.

    The sample is whichever seat is first on the clock rather than seat 0: this
    game's first decision belongs to whoever wakes first, and only a seat that is
    being asked something has an ask to print.
    """
    if humans:
        seat = next(iter(humans))
        return (f"(you are playing seat {seat}; the sample private view and the "
                "board are withheld until the game ends)")
    turn = ref.pending()
    if turn is None:
        return "(nobody is on the clock)"
    return (f"--- one seat's private view (seat {turn.seat}), the exact bytes it "
            "would send ---\n" + ref.prompt_for(turn.seat))


def build_policies(ref: BelfryReferee, args, rng: random.Random) -> dict:
    """Seat -> policy. One ``LLMPolicy`` per seat, never one shared object: a
    shared ``upstreams`` Counter is summed once per seat and multiplies the census
    by the live-seat count.

    A human seat is the same policy over a ``ConsoleBackend`` - same prompt, same
    parser, same refuse-and-retell loop. Its retry budget is wide because the
    fallback at the end of that loop plays a RANDOM move, and a person who
    mistypes twice has not decided to hand their seat to the control policy.
    """
    humans = human_seats(args.human, ref.n)
    backend = None
    if args.backend:
        backend = Backend.named(
            args.backend,
            args.model,
            api_key=api_key_from_env(),
            system_prompt=REGISTERS[args.register],
            seed=args.seed,
            enable_thinking=(False if args.no_thinking else None),
        )

    def policy(seat: int):
        if seat in humans:
            return LLMPolicy(backend=ConsoleBackend(keys=ACTION_KEYS,
                                                    briefing=BRIEFING,
                                                    rules_path=RULES_PATH),
                             retries=args.human_retries,
                             fallback=RandomPolicy(rng))
        if backend is None:
            return RandomPolicy(rng)
        return LLMPolicy(backend=backend, retries=args.retries,
                         fallback=RandomPolicy(rng))

    return {s: policy(s) for s in range(ref.n)}


def main() -> None:
    # The Windows console defaults to cp1252 and dies at the moment of writing a
    # character it cannot encode - the game runs, the render is correct, and the
    # process dies printing it. Same guard the other drivers carry.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser()
    ap.add_argument("--seats", type=int, default=7,
                    choices=sorted(DISTRIBUTION), help="how many seats")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--script", choices=list(SCRIPTS),
                    help="which roles could be in play (default: full)")
    ap.add_argument("--rounds", type=int, default=1,
                    help="rounds of talk per day, every seat speaking once")
    ap.add_argument("--max-days", type=int, default=12,
                    help="the structural bound: a game that reaches it has no "
                         "winner rather than running on")
    ap.add_argument("--backend", choices=["local", "clean", "gray"],
                    help="run live players (default: random policy, no model)")
    ap.add_argument("--model", default="auto")
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--no-thinking", action="store_true",
                    help="ask the chat template to skip the reasoning pass")
    ap.add_argument("--register", choices=list(REGISTERS), default="character")
    ap.add_argument("--human", metavar="SEAT",
                    help="play ONE seat yourself, e.g. 0 (a terminal is one "
                         "channel, so it seats one person)")
    ap.add_argument("--human-retries", type=int, default=99,
                    help="mistyped answers a human seat may make before its move "
                         "falls back to random (default: effectively unlimited)")
    args = ap.parse_args()

    # Refuse at the DOOR, never at game 200. An off-box route with no key does not
    # crash - it 401s every attempt, falls back on every decision, and reports a
    # number the scorer then voids after the GPU is spent.
    if args.backend:
        require_key(ENDPOINTS[args.backend], api_key_from_env())

    script = SCRIPTS[args.script] if args.script else DEFAULT_SCRIPT
    rng = random.Random(args.seed)
    ref = BelfryReferee.new(args.seats, seed=args.seed, script=script,
                            discussion_rounds=args.rounds,
                            max_days=args.max_days)
    policies = build_policies(ref, args, rng)
    humans = human_seats(args.human, ref.n)

    print(f"=== {args.seats}-seat belfry, script='{script.name}' ===\n")
    print(opening_view(ref, humans))
    print("\n--- play ---")
    try:
        rec = play_game(ref, policies)   # gate #1 audited every turn, raises on a leak
    except KeyboardInterrupt:
        # A human seat ends its game this way. It is an abandoned game, not a
        # crash, and it has no record - so say that and leave, rather than printing
        # a half-game's numbers as if they meant something.
        print("\n(game abandoned - no record written)")
        return

    for tag, text in ref.public_events:
        print(f"  [{tag}] {text}")
    leaks = leak_audit(ref)
    print(f"\ngate #1 leak audit: {'CLEAN' if not leaks else leaks} "
          f"({ref.n} seats, every turn)")
    print(f"winner: {rec.winner}  ({rec.reason})")
    if rec.error:
        print(f"error: {rec.error}")
    if rec.decisions:
        print(f"decisions: {rec.decisions}, illegal-after-retries fallbacks: "
              f"{rec.fallbacks}")
    print("\n(referee-side only - the board:)")
    for s in ref.grim.seats:
        note = "" if s.dealt is s.role else f" (dealt {s.dealt.key})"
        believed = "" if s.believes is s.role else f", believes {s.believes.key}"
        print(f"  seat {s.index}: {s.role.key}{note}{believed}"
              f"{'' if s.alive else '  <- dead'}")
    print("\n(referee-side log:)")
    for line in ref.referee_log:
        print("  " + line)


if __name__ == "__main__":
    main()
