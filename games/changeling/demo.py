"""Play one changeling game and audit gate #1 every turn.

The twin of ``games.cabal.demo``, and it exists for the same two reasons: to run
the state machine and the leak audit with no model at all, and to seat a person
at the table. This rung's whole point is that a seat can be wrong about ITSELF -
the night moves cards, and a seat is told what it was dealt, never what it now
holds - which is a claim you can only really feel from inside a seat.

    python -m games.changeling.demo                  # random players, folk face
    python -m games.changeling.demo --theme greek    # the vocabulary control
    python -m games.changeling.demo --rounds 2
    python -m games.changeling.demo --human 0        # you play seat 0
    python -m games.changeling.demo --human 0 --backend local --model qwen36-35b-a3b-iq3

``--human`` hands that seat the exact bytes its model would receive and nothing
else. ONE seat and ONE game: this module plays a single game and stops, and a
terminal is a single channel, so two people at it would read each other's private
view. Without ``--backend`` the other seats are the random control, which is
playable but not an opponent; pair the two flags for a real table.

Scoring lives in ``eval.run_changeling`` - this prints one game and stops. Nothing
here is a measurement.
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
from games.changeling.audit import leak_audit
from games.changeling.player import (ACTION_KEYS, LLMPolicy, RandomPolicy,
                                     play_game)
from games.changeling.night import deal
from games.changeling.referee import (TURN_MODES, TURNS_FIXED,
                                      TURNS_RANDOM_ACTIVE, ChangelingReferee)
from games.changeling.roles import DEFAULT_THEME, SETUPS, THEMES, Side

#: See ``games.cabal.demo.BRIEFING`` - console furniture, never the payload.
BRIEFING = """changeling in one screen. Five seats, eight cards: five dealt out, three left
face down in the centre. Two of the eight are pack (evil).

  The rule   you ACT on the card you were dealt, and you WIN with the card you
             HOLD at dawn. The night moves cards, and a seat is never told that
             its own card moved - so you can play a whole game sincerely wrong
             about yourself.
  Win        the village wins if any accused seat holds pack at dawn. Otherwise
             the pack wins. Judged on dawn truth, never on the deal or on belief.
  Day        one discussion round-robin, then every seat names exactly one OTHER
             seat, simultaneously. Most votes is accused; on a tie, all tied
             seats are accused. Naming yourself is refused.
  Public     everything said in discussion, and the votes.
  Secret     every card, the whole night. What you were shown, if anything, is
             yours alone - and it was true when you saw it.
  Given      at least one pack card is always dealt to a SEAT, never both to the
             centre. That is a public rule, so every seat may reason from it.

'rules' prints the full rules.
"""

#: Printed only under ``--turns random-active``, appended to ``BRIEFING``. The
#: referee's own ask already tells the seat on the clock that an empty `say`
#: listens - that text is payload, audited, and unconditional. This is console
#: furniture for the same fact, spelled out once up front rather than left for a
#: person to infer from the ask alone: type ``say`` with nothing after it (the
#: existing shorthand already turns that into an empty ``say``) to pass.
LISTEN_NOTE = """
This game is using random-active turns: each turn the floor goes to one seat,
drawn at random, not round-robin - you may hold the floor twice in a round or not
at all. Type `say` with nothing after it to listen and pass the turn.
"""

RULES_PATH = str(Path(__file__).with_name("RULES.md"))


def opening_view(ref: ChangelingReferee, humans: set[int]) -> str:
    """What the demo prints before the first move.

    The reader's peek at one seat's view is a LEAK once a person is at the table,
    and here it is a worse one than in cabal: seat 0's view names the card seat 0
    was DEALT, and this deck holds duplicates, so one seat's deal narrows what
    every other seat can be holding. The referee's own audit cannot catch it -
    that audit grades what the REFEREE renders to a seat, and this print is the
    harness talking past it. So the guard lives here, in a function a test can
    call, rather than as a branch inside ``main``.
    """
    if humans:
        seat = next(iter(humans))
        return (f"(you are playing seat {seat}; the sample private view, the night "
                "and the dawn truth are withheld until the game ends)")
    return ("--- one seat's private view (seat 0), the exact bytes it would send "
            "---\n" + ref.prompt_for(0))


def build_policies(ref: ChangelingReferee, args, rng: random.Random) -> dict:
    """Seat -> policy.

    One ``LLMPolicy`` per seat, as ``eval.run_changeling`` does and for its
    reason: a shared object makes ``upstreams`` one Counter that the record then
    sums once per seat, multiplying the census by the live-seat count.

    A human seat is the same policy over a ``ConsoleBackend`` - same prompt, same
    parser, same refuse-and-retell loop. Its retry budget is wide because the
    fallback at the end of that loop plays a RANDOM move, and a person who
    mistypes twice has not decided to hand their seat to the control policy.
    """
    humans = human_seats(args.human, ref.n, args.seed)
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

    briefing = BRIEFING
    if getattr(ref, "turn_mode", TURNS_FIXED) == TURNS_RANDOM_ACTIVE:
        briefing = BRIEFING + LISTEN_NOTE

    def policy(seat: int):
        if seat in humans:
            return LLMPolicy(backend=ConsoleBackend(keys=ACTION_KEYS,
                                                   briefing=briefing,
                                                   rules_path=RULES_PATH,
                                                   other_model=args.model if args.backend else None),
                             retries=args.human_retries,
                             fallback=RandomPolicy(rng))
        if backend is None:
            return RandomPolicy(rng)
        return LLMPolicy(backend=backend, retries=args.retries,
                         fallback=RandomPolicy(rng))

    return {s: policy(s) for s in range(ref.n)}


def constrained_deal(setup, rng: random.Random, seat: int, key: str):
    """Deal normally, then SWAP the wanted card into ``seat``.

    **Why a swap and not a re-deal.** The obvious implementation reshuffles until
    the wanted card lands - and every discarded shuffle is draws taken from the
    seeded generator, so the same seed would produce a different night, different
    policy choices, and a game that cannot be compared to its unconstrained twin.
    Swapping after one deal keeps the stream at exactly the position an
    unconstrained run leaves it, and preserves the deck multiset: no card is
    created or destroyed, one pair changes hands.

    It is still not a sample - the seat's card was chosen, not dealt - which is why
    the record it produces is marked. What it costs is only that the OTHER seats'
    holdings are a permutation of the seed's, not the seed's own.
    """
    dealt, centre = deal(setup, rng)
    if dealt[seat].key != key:
        donor = next((s for s, c in dealt.items() if c.key == key), None)
        if donor is not None:
            dealt[donor], dealt[seat] = dealt[seat], dealt[donor]
        else:
            slot = next((i for i, c in enumerate(centre) if c.key == key), None)
            if slot is None:
                raise SystemExit(
                    f"no {key!r} was dealt or left in the centre this game, and "
                    f"this deck holds "
                    f"{sorted({c.key for c in setup.deck})}")
            centre[slot], dealt[seat] = dealt[seat], centre[slot]
    # The setup promises at least one pack card is SEATED, and seats reason from
    # that promise. Swapping the last one into the centre would quietly retract it.
    if setup.require_seated_pack and not any(c.side is Side.PACK
                                             for c in dealt.values()):
        raise SystemExit(
            f"seating {key!r} at seat {seat} would move the only pack card out of "
            "the seats, and the rules text every seat reads promises one is there")
    return dealt, centre


def main() -> None:
    # A CJK skin cannot be printed to the Windows console, whose default codec is
    # cp1252: the game runs, the render is correct, and the process dies at the
    # moment of writing it out. Same guard both eval drivers carry.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--theme", choices=list(THEMES), help="card skin (default: folk)")
    ap.add_argument("--rounds", type=int, default=2, help="discussion rounds")
    ap.add_argument("--turns", choices=list(TURN_MODES), default=TURNS_FIXED,
                    help="`fixed` (default) asks every seat once a round, in "
                         "seat order. `random-active` makes a round a budget "
                         "of n turns; each turn the floor goes to one seat, "
                         "drawn at random, and that seat may listen instead "
                         "of speaking.")
    ap.add_argument("--backend", choices=["local", "clean", "gray"],
                    help="run live players (default: random policy, no model)")
    ap.add_argument("--model", default="auto")
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--no-thinking", action="store_true",
                    help="ask the chat template to skip the reasoning pass")
    ap.add_argument("--register", choices=list(REGISTERS), default="character")
    ap.add_argument("--human", metavar="SEAT",
                    help="play ONE seat yourself: a seat number, or `random` "
                         "to draw one from --seed (a terminal is one channel, "
                         "so it seats one person)")
    ap.add_argument("--human-role", metavar="KEY",
                    help="UAT: deal this card key to the human seat, by swapping "
                         "it in after the deal. Not a sample - the record is "
                         "marked. Needs --human")
    ap.add_argument("--referee-transcript", metavar="PATH",
                    help="append referee-only log lines here as the game runs")
    ap.add_argument("--human-retries", type=int, default=99,
                    help="mistyped answers a human seat may make before its move "
                         "falls back to random (default: effectively unlimited)")
    args = ap.parse_args()

    # Refuse at the DOOR, never at game 200. An off-box route with no key does
    # not crash - it 401s every attempt, falls back on every decision, and
    # reports a number the scorer then voids after the GPU is spent.
    if args.backend:
        require_key(ENDPOINTS[args.backend], api_key_from_env())

    theme = THEMES[args.theme] if args.theme else DEFAULT_THEME
    rng = random.Random(args.seed)
    setup = SETUPS[5]
    humans = human_seats(args.human, setup.n, args.seed)
    dealt = centre = None
    if args.human_role:
        if not humans:
            raise SystemExit("--human-role picks what the PERSON plays, so it "
                             "needs --human to say which seat that is")
        keys = sorted({c.key for c in setup.deck})
        if args.human_role not in keys:
            raise SystemExit(f"{args.human_role!r} is not in this deck. It holds "
                             f"{keys}")
        dealt, centre = constrained_deal(setup, random.Random(args.seed),
                                         next(iter(humans)), args.human_role)
    ref = ChangelingReferee.new(5, seed=args.seed, theme=theme,
                                discussion_rounds=args.rounds,
                                dealt=dealt, centre=centre,
                                turn_mode=args.turns,
                                transcript_path=args.referee_transcript)
    policies = build_policies(ref, args, rng)

    print(f"=== 5-seat changeling, theme='{theme.name}' ===\n")
    print(opening_view(ref, humans))
    print("\n--- play ---")
    try:
        rec = play_game(ref, policies, uat=bool(args.human_role) or None)
        # gate #1 audited every turn, raises on a leak
    except KeyboardInterrupt:
        # A human seat ends its game this way (Ctrl-C, or a closed pipe). It is
        # an abandoned game, not a crash, and it has no record - so say that and
        # leave, rather than printing a half-game's numbers as if they meant
        # something.
        print("\n(game abandoned - no record written)")
        return
    finally:
        ref.close()
    for line in ref.referee_log:
        print(" ", line)

    leaks = leak_audit(ref)
    print(f"\ngate #1 leak audit: {'CLEAN' if not leaks else leaks} "
          f"({ref.n} seats, every turn)")
    print(f"winner: {rec.winner}  ({rec.reason})")
    if rec.decisions:
        print(f"decisions: {rec.decisions}, illegal-after-retries fallbacks: "
              f"{rec.fallbacks}")
    # Dealt, dawn truth and dawn belief side by side, because the interesting
    # seats are the ones where the second and third columns disagree - that is
    # the thing this rung exists to make visible, and one column cannot show it.
    print("\n(referee-side only - dealt / holds at dawn / believes it holds:)")
    for s in range(ref.n):
        mark = "  <- diverged" if s in rec.diverged else ""
        print(f"  seat {s}: {rec.dealt.get(s, '?')} / {rec.truth.get(s, '?')} / "
              f"{rec.belief.get(s, '?')}{mark}")


if __name__ == "__main__":
    main()
