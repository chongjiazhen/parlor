"""Play one game and audit gate #1 every turn.

By default a random-legal policy stands in for the LLM players, so the state
machine and the leak audit run with no model at all. ``--backend`` swaps in live
players; ``--speaker`` puts a model on the discussion phase only, which is the
cheap way to eyeball whether agents will actually deceive.

    python -m games.cabal.demo                       # random players, 1984-en face
    python -m games.cabal.demo --theme plain         # sterile functional names
    python -m games.cabal.demo --rounds 2            # two discussion rounds
    python -m games.cabal.demo --backend local --model qwen36-35b-a3b-iq3
    python -m games.cabal.demo --backend clean --speaker   # only discussion is live
    python -m games.cabal.demo --transcript game.md        # readable log on disk
"""

from __future__ import annotations

import argparse
import os
import random

from core.backends import Backend
from games.cabal import transcript
from games.cabal.audit import leak_audit, secret_terms  # noqa: F401 (re-export)
from games.cabal.player import LLMPolicy, RandomPolicy, play_game
from games.cabal.referee import CabalReferee, Phase
from games.cabal.roles import DEFAULT_THEME, THEMES


def build_policies(ref: CabalReferee, args, rng: random.Random) -> dict:
    """Seat -> policy. ``--speaker`` keeps everything mechanical except the talking."""
    fallback = RandomPolicy(rng=rng)
    if not args.backend:
        return {s: fallback for s in ref.assignment}
    backend = Backend.named(
        args.backend,
        args.model,
        api_key=os.environ.get("PARLOR_API_KEY") or os.environ.get("FREELLMAPI_KEY"),
    )
    llm = LLMPolicy(backend=backend, retries=args.retries, fallback=fallback)
    if args.speaker:
        return {s: _SpeechOnly(llm, fallback) for s in ref.assignment}
    return {s: llm for s in ref.assignment}


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
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--theme", choices=list(THEMES), help="role skin (default: 1984-en)")
    ap.add_argument("--rounds", type=int, default=1, help="discussion rounds per proposal")
    ap.add_argument("--backend", choices=["local", "clean", "gray"],
                    help="run live players (default: random policy, no model)")
    ap.add_argument("--model", default="auto")
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--speaker", action="store_true",
                    help="model plays the discussion phase only")
    ap.add_argument("--transcript", help="write this game as markdown here")
    args = ap.parse_args()

    theme = THEMES[args.theme] if args.theme else DEFAULT_THEME
    rng = random.Random(args.seed)
    ref = CabalReferee.new(5, seed=args.seed, theme=theme, discussion_rounds=args.rounds)
    policies = build_policies(ref, args, rng)

    print(f"=== 5-seat hidden-role game, theme='{theme.name}' ===\n")
    print("--- one seat's private view (seat 0), the exact bytes it would send ---")
    print(ref.prompt_for(0) if 0 in ref.acting_seats() else ref.render_context(0))
    print("\n--- play ---")
    rec = play_game(ref, policies)          # gate #1 audited every turn, raises on a leak
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
