"""Play one game and audit gate #1 every turn.

By default a random-legal policy stands in for the LLM players, so the state
machine and both halves of the leak audit run with no model at all.

    python -m games.quorum.demo                      # random players, guild face
    python -m games.quorum.demo --theme plain        # sterile functional names
    python -m games.quorum.demo --rounds 2           # two discussion rounds
    python -m games.quorum.demo --backend local --model qwen36-35b-a3b-iq3
    python -m games.quorum.demo --backend clean --speaker   # only discussion is live
    python -m games.quorum.demo --human 0                   # you play seat 0
    python -m games.quorum.demo --human 0 --backend local --model qwen36-35b-a3b-iq3

``--human`` seats a person at the terminal, handed the exact bytes that seat's
model would receive and nothing else. On this rung that is worth more than on the
two before it: a person in the enactor's chair holds two cards and knows the
proposer saw three, and whether the third is inferable is a question a human can
answer by sitting there. ONE seat and ONE game - a terminal is a single channel,
so two people at it would read each other's private view.
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

from core.backends import (Backend, ENDPOINTS, REGISTERS, api_key_from_env,
                           require_key)
from core.console import ConsoleBackend, human_seats
from games.quorum.audit import dependence_leaks, identity_leaks
from games.quorum.player import ACTION_KEYS, LLMPolicy, RandomPolicy, play_game
from games.quorum.referee import Phase, QuorumReferee
from games.quorum.roles import DEFAULT_THEME, THEMES

#: See ``games.cabal.demo.BRIEFING`` - console furniture, never the payload.
BRIEFING = """quorum in one screen. Five seats legislating: three majority, two minority. The
two minority seats know each other; the three majority seats know nothing. What
a seat may SEE is a fact about the office it holds this event, not about its role.

  Win       majority: 5 majority cards enacted, or the principal removed from
            play. minority: 6 minority cards enacted, or the principal installed
            as enactor on a passed vote once 3 minority cards are enacted.
  Event     the proposer nominates an enactor; every living seat votes, publicly,
            and a strict majority passes (a tie fails); the proposer is dealt 3
            cards, discards 1 face down and passes 2; the enactor discards 1 and
            the last card is enacted in the open; both may then claim what they
            saw; a power fires if the enactment reached its threshold; discussion.
  Stall     three failed votes in a row and the top card enacts unseen, with no
            claim attached. Any passed vote resets that track.
  Public    every vote in full, every enactment, every claim.
  Secret    the hand of 3 and both discards. A claim about them is not checked by
            any rule - and no seat's assertion can end the game.

'rules' prints the full rules.
"""

RULES_PATH = str(Path(__file__).with_name("RULES.md"))


def opening_view(ref: QuorumReferee, humans: set[int]) -> str:
    """What the demo prints before the first move.

    The reader's peek at one seat's private view is a LEAK once a person is at the
    table: seat 0's role is exactly what a human in seat 3 must not know, and the
    demo would hand it over before anyone has moved. The referee's own audit
    cannot catch this - it grades what the REFEREE renders to a seat, and this
    print is the harness talking past it. So the guard lives here, in a function a
    test can call, rather than as a branch inside ``main``.
    """
    if humans:
        seat = next(iter(humans))
        return (f"(you are playing seat {seat}; the sample private view and the "
                "referee log are withheld until the game ends)")
    return ("--- one seat's private view (seat 0), the exact bytes it would send "
            "---\n"
            + (ref.prompt_for(0) if 0 in ref.on_clock()
               else ref.render_context(0)))


class _SpeechOnly:
    """Model on the discussion phase, random everywhere else. One LLM call per seat
    per round instead of one per decision - enough to see whether it will lie about
    a draw, which is the behaviour this rung exists to measure."""

    def __init__(self, llm, fallback):
        self.llm, self.fallback = llm, fallback
        self.last_fell_back = False

    @property
    def trace(self):
        return self.llm.trace

    @property
    def upstreams(self):
        return self.llm.upstreams

    def act(self, ref, seat):
        inner = self.llm if ref.phase is Phase.DISCUSS else self.fallback
        action = inner.act(ref, seat)
        self.last_fell_back = getattr(inner, "last_fell_back", False)
        return action


def build_policies(ref: QuorumReferee, args, rng: random.Random) -> dict:
    """Seat -> policy. A human seat is an ``LLMPolicy`` over a ``ConsoleBackend``:
    same prompt, same parser, same refuse-and-retell loop. Its retry budget is wide
    because the fallback at the end of that loop plays a RANDOM move, and a person
    who mistypes twice has not decided to hand their seat to the control policy."""
    fallback = RandomPolicy(rng=rng)
    humans = {s: LLMPolicy(backend=ConsoleBackend(keys=ACTION_KEYS,
                                                 briefing=BRIEFING,
                                                 rules_path=RULES_PATH),
                           retries=args.human_retries, fallback=fallback)
              for s in human_seats(args.human, ref.n, args.seed)}
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


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--theme", choices=list(THEMES), help="role skin (default: guild)")
    ap.add_argument("--rounds", type=int, default=1,
                    help="discussion rounds per nomination")
    ap.add_argument("--backend", choices=["local", "clean", "gray"],
                    help="run live players (default: random policy, no model)")
    ap.add_argument("--model", default="auto")
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--speaker", action="store_true",
                    help="model plays the discussion phase only")
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
    args = ap.parse_args()

    # Refuse at the DOOR, never at game 200. An off-box route with no key does not
    # crash - it 401s every attempt, falls back on every decision, and reports a
    # number the scorer then voids after the GPU is spent.
    if args.backend:
        require_key(ENDPOINTS[args.backend], api_key_from_env())

    theme = THEMES[args.theme] if args.theme else DEFAULT_THEME
    rng = random.Random(args.seed)
    ref = QuorumReferee.new(5, seed=args.seed, theme=theme,
                            discussion_rounds=args.rounds)
    policies = build_policies(ref, args, rng)
    humans = human_seats(args.human, ref.n, args.seed)

    print(f"=== 5-seat legislative hidden-role game, theme='{theme.name}' ===\n")
    print(opening_view(ref, humans))
    print("\n--- play ---")
    try:
        rec = play_game(ref, policies)   # gate #1 audited every turn, raises on a leak
    except KeyboardInterrupt:
        print("\n(game abandoned - no record written)")
        return
    for line in ref.log:
        print(" ", line)

    ident, depend = identity_leaks(ref), dependence_leaks(ref)
    clean = not ident and not depend
    print(f"\ngate #1 leak audit: {'CLEAN' if clean else (ident, depend)} "
          f"({ref.n} seats, both mechanisms, every turn)")
    print(f"winner: {ref.theme.side_names[ref.winner]} ({ref.win_reason})")
    if rec.decisions:
        print(f"decisions: {rec.decisions}, "
              f"illegal-after-retries fallbacks: {rec.fallbacks} "
              f"({rec.fallback_rate:.1%})")
    print(f"events: {len(rec.draws)} drawn, {rec.forced_enactments} of them forced "
          f"(every card drawn advanced one side, so the office had no other legal "
          f"move)")
    print("\n(secret assignment, referee-side only:)")
    for s, r in sorted(ref.assignment.items()):
        print(f"  seat {s}: {r.key}")


if __name__ == "__main__":
    main()
