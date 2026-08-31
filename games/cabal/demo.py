"""Play one game and audit gate #1 every turn.

By default a random-legal policy stands in for the LLM players, so the state
machine and the leak audit run with no model at all. ``--backend`` swaps in live
players; ``--speaker`` puts a model on the discussion phase only, which is the
cheap way to eyeball whether agents will actually deceive.

    python -m games.cabal.demo                       # random players, plain face
    python -m games.cabal.demo --theme plain         # sterile functional names
    python -m games.cabal.demo --theme bnw-en        # the other dystopia face
    python -m games.cabal.demo --rounds 2            # two discussion rounds
    python -m games.cabal.demo --backend local --model qwen36-35b-a3b-iq3
    python -m games.cabal.demo --backend clean --speaker   # only discussion is live
    python -m games.cabal.demo --solver                    # mechanical vote reader
    python -m games.cabal.demo --transcript game.md        # readable log on disk
    python -m games.cabal.demo --human 0                   # you play seat 0
    python -m games.cabal.demo --human 0 --backend local --model qwen36-35b-a3b-iq3

``--human`` seats a person at the terminal, handed the exact bytes that seat's
model would receive and nothing else - the gate-#1 property, checkable by hand.
ONE seat and ONE game: this module plays a single game and stops, and a terminal
is a single channel, so two people at it would read each other's private view.
Without ``--backend`` the other four seats are the random control, which is
playable but not an opponent; pair the two flags for a real table.
"""

from __future__ import annotations

import argparse
import os
import random
import sys
from pathlib import Path

from core.backends import (Backend, ENDPOINTS, REGISTERS, api_key_from_env,
                           require_key)
from core.console import ConsoleBackend, human_seats
from games.cabal import transcript
from games.cabal.audit import leak_audit, secret_terms  # noqa: F401 (re-export)
from games.cabal.player import ACTION_KEYS, LLMPolicy, RandomPolicy, play_game
from games.cabal.referee import CabalReferee, Phase
from games.cabal.roles import DEFAULT_THEME, THEMES
from games.cabal.solver import SolverPolicy

#: The standing frame a person needs and the per-turn ask does not carry: what
#: wins, what the counters on the board do, what stays secret. Printed by the
#: CONSOLE only - see ``core.console.COMMANDS`` for why it is not in the payload.
#: Written against ``RULES.md``, which ``rules`` prints in full.
BRIEFING = """cabal in one screen. Five seats: three run the missions, two work against them.
You are told your own role, whatever the night gave you, and nothing else.

  Win      Good holds 3 of the 5 missions AND survives the hunt at the end.
           Evil sinks 3 missions, OR draws 5 rejected proposals in a row, OR -
           once good has held 3 - correctly names the seat the night showed both
           evil seats to.
  Round    the leader proposes a team; the table talks; every seat votes; a
           strict majority (3 of 5) sends the team on the mission.
  Teams    missions 1..5 take 2, 3, 2, 3, 3 seats. A single fail card sinks one.
  Rejects  a rejected proposal passes leadership on and adds to the reject
           streak. Five in a row and evil takes the game. A passed vote resets it.
  Public   every vote and every approver, the proposal, and the NUMBER of fails.
  Secret   who played which mission card, always. Good may not play a fail card -
           the referee refuses it.

'rules' prints the full rules.
"""

#: Read at ``rules`` time rather than at import: an unreadable file must cost a
#: message and not a startup.
RULES_PATH = str(Path(__file__).with_name("RULES.md"))


def opening_view(ref: CabalReferee, humans: set[int]) -> str:
    """What the demo prints before the first move.

    The reader's peek at one seat's private view is a LEAK once a person is at
    the table: seat 0's role is exactly what a human in seat 3 must not know, and
    the demo would hand it over before anyone has moved. The referee's own audit
    cannot catch this - that audit grades what the REFEREE renders to a seat, and
    this print is the harness talking past it. So the guard lives here, in a
    function a test can call, rather than as a branch inside ``main``.
    """
    if humans:
        seat = next(iter(humans))
        return (f"(you are playing seat {seat}; the sample private view and the "
                "referee log are withheld until the game ends)")
    return ("--- one seat's private view (seat 0), the exact bytes it would send "
            "---\n"
            + (ref.prompt_for(0) if 0 in ref.acting_seats()
               else ref.render_context(0)))


def build_policies(ref: CabalReferee, args, rng: random.Random) -> dict:
    """Seat -> policy. ``--speaker`` keeps everything mechanical except the talking.

    A human seat is an ``LLMPolicy`` over a ``ConsoleBackend``: same prompt, same
    parser, same refuse-and-retell loop. Its retry budget is wide because the
    fallback at the end of that loop plays a RANDOM move, and a person who
    mistypes twice has not decided to hand their seat to the control policy.
    """
    fallback = RandomPolicy(rng=rng)
    humans = {s: LLMPolicy(backend=ConsoleBackend(keys=ACTION_KEYS,
                                                 briefing=BRIEFING,
                                                 rules_path=RULES_PATH),
                           retries=args.human_retries, fallback=fallback)
              for s in human_seats(args.human, ref.n, args.seed)}
    if args.solver:
        return {s: humans.get(s, SolverPolicy(fallback=fallback))
                for s in ref.assignment}
    if not args.backend:
        return {s: humans.get(s, fallback) for s in ref.assignment}
    backend = Backend.named(
        args.backend,
        args.model,
        api_key=api_key_from_env(),
        system_prompt=REGISTERS[args.register],
        seed=args.seed,
    )
    llm = LLMPolicy(backend=backend, retries=args.retries, fallback=fallback)
    if args.speaker:
        return {s: humans.get(s, _SpeechOnly(llm, fallback)) for s in ref.assignment}
    return {s: humans.get(s, llm) for s in ref.assignment}


class _SpeechOnly:
    """Model on the discussion phase, random everywhere else. One LLM call per seat
    per round instead of one per decision - enough to see whether it will lie."""

    def __init__(self, llm, fallback):
        self.llm, self.fallback = llm, fallback
        self.last_fell_back = False

    @property
    def trace(self):
        return self.llm.trace

    @property
    def upstreams(self):
        """Pass the served-upstream tally through the wrapper, or a --speaker game
        reports that nothing answered it."""
        return self.llm.upstreams

    def act(self, ref, seat):
        inner = self.llm if ref.phase is Phase.DISCUSS else self.fallback
        action = inner.act(ref, seat)
        self.last_fell_back = getattr(inner, "last_fell_back", False)
        return action


def main() -> None:
    # A CJK skin cannot be printed to the Windows console, whose default codec is
    # cp1252: the game runs, the render is correct, and the process dies at the
    # moment of writing it out. Both Chinese skins were unrunnable here without
    # PYTHONIOENCODING set, which is a fact about the terminal, not the arena.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--theme", choices=list(THEMES), help="role skin (default: lodge)")
    ap.add_argument("--rounds", type=int, default=1, help="discussion rounds per proposal")
    arm = ap.add_mutually_exclusive_group()
    arm.add_argument("--backend", choices=["local", "clean", "gray"],
                     help="run live players (default: random policy, no model)")
    arm.add_argument("--solver", action="store_true",
                     help="seat mechanical vote reader (no model calls)")
    ap.add_argument("--model", default="auto")
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--speaker", action="store_true",
                    help="model plays the discussion phase only")
    ap.add_argument("--simultaneous", action="store_true",
                    help="every seat commits its line before seeing its neighbours")
    ap.add_argument("--notebook", action="store_true",
                    help="each seat keeps a private notebook, read back only to itself")
    ap.add_argument("--register", choices=list(REGISTERS), default="character",
                    help="'character' roleplays the skin, 'plain' argues from the "
                         "record out of character")
    ap.add_argument("--human", metavar="SEAT",
                    help="play ONE seat yourself: a seat number, or `random` "
                         "to draw one from --seed (a terminal is one channel, "
                         "so it seats one person)")
    ap.add_argument("--human-retries", type=int, default=99,
                    help="mistyped answers a human seat may make before its move "
                         "falls back to random (default: effectively unlimited)")
    ap.add_argument("--transcript", help="write this game as markdown here")
    args = ap.parse_args()

    # Refuse at the DOOR, never at game 200. An off-box route with no key does
    # not crash - it 401s every attempt, falls back on every decision, and
    # reports a number the scorer then voids after the GPU is spent.
    if args.backend:
        require_key(ENDPOINTS[args.backend], api_key_from_env())

    theme = THEMES[args.theme] if args.theme else DEFAULT_THEME
    rng = random.Random(args.seed)
    ref = CabalReferee.new(5, seed=args.seed, theme=theme, discussion_rounds=args.rounds,
                           simultaneous=args.simultaneous, notebook=args.notebook)
    policies = build_policies(ref, args, rng)

    humans = human_seats(args.human, ref.n, args.seed)

    print(f"=== 5-seat hidden-role game, theme='{theme.name}' ===\n")
    print(opening_view(ref, humans))
    print("\n--- play ---")
    try:
        rec = play_game(ref, policies)      # gate #1 audited every turn, raises on a leak
    except KeyboardInterrupt:
        # A human seat ends its game this way (Ctrl-C, or a closed pipe). It is
        # an abandoned game, not a crash, and it has no record - so say that and
        # leave, rather than printing a half-game's numbers as if they meant
        # something.
        print("\n(game abandoned - no record written)")
        return
    for line in ref.log:
        print(" ", line)

    leaks = leak_audit(ref)
    print(f"\ngate #1 leak audit: {'CLEAN' if not leaks else leaks} "
          f"({ref.n} seats, every turn)")
    print(f"winner: {ref.theme.faction_names[ref.winner]}")
    if rec.decisions:
        print(f"decisions: {rec.decisions}, illegal-after-retries fallbacks: {rec.fallbacks}")
    print("\n(secret assignment, referee-side only:)")
    for s, r in sorted(ref.assignment.items()):
        print(f"  seat {s}: {r.key}")

    if args.transcript:
        text = transcript.from_referee(ref, rec, meta={
            "backend": args.backend, "model": args.model if args.backend else None,
            "rounds": args.rounds, "seed": args.seed,
        })
        print(f"\nwrote transcript to {transcript.write(args.transcript, text)}")


if __name__ == "__main__":
    main()
