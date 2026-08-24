"""Play one game with a random-legal driver, and audit gate #1 every turn.

No model calls - a random policy stands in for the LLM players, just to exercise
the referee state machine and prove that no seat's rendered context ever leaks
another seat's role. Run:

    python -m games.cabal.demo                 # default face (1984-en)
    python -m games.cabal.demo --theme plain   # sterile functional names
    python -m games.cabal.demo --theme 1984-cn --seed 7
"""

from __future__ import annotations

import argparse
import random

from core.observability import find_leaks
from games.cabal.referee import CabalReferee, Phase
from games.cabal.roles import DEFAULT_THEME, THEMES, Team


def secret_terms(ref: CabalReferee) -> dict[int, list[str]]:
    """Each seat's role, in both skins - the sentinels a leak would trip."""
    return {
        s: [role.key, ref.theme.role_names[role.key]]
        for s, role in ref.assignment.items()
    }


def audit(ref: CabalReferee) -> list[tuple[int, int, str]]:
    """Return every (viewer, leaked_seat, term). Empty == gate #1 holds."""
    terms = secret_terms(ref)
    out = []
    for viewer in ref.assignment:
        entitled = {k.seat for k in ref.entitled_knowledge(viewer)}
        for seat, term in find_leaks(ref.render_context(viewer), terms, entitled, viewer):
            out.append((viewer, seat, term))
    return out


def play(ref: CabalReferee, rng: random.Random) -> None:
    seats = list(ref.assignment)
    guard = 0
    while ref.phase is not Phase.DONE:
        guard += 1
        assert guard < 1000, "referee failed to terminate"
        # gate #1 holds at every reachable state, not just at setup
        leaks = audit(ref)
        assert not leaks, f"LEAK: {leaks}"

        if ref.phase is Phase.PROPOSE:
            size = ref.setup.team_sizes[ref.mission_index]
            ref.propose(ref.leader, rng.sample(seats, size))
        elif ref.phase is Phase.VOTE:
            # bias toward approval so missions actually run in a random game
            ref.vote({s: rng.random() < 0.7 for s in seats})
        elif ref.phase is Phase.MISSION:
            cards = {}
            for s in ref.proposal:
                evil = ref.assignment[s].team is Team.EVIL
                cards[s] = evil and rng.random() < 0.5
            ref.mission(cards)
        elif ref.phase is Phase.HUNT:
            hunter = ref.seat_of("hunter")
            good = [s for s in seats if ref.assignment[s].team is Team.GOOD]
            ref.hunt(hunter, rng.choice(good))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--theme", choices=list(THEMES), help="role skin (default: 1984-en)")
    args = ap.parse_args()

    theme = THEMES[args.theme] if args.theme else DEFAULT_THEME
    rng = random.Random(args.seed)
    ref = CabalReferee.new(5, seed=args.seed, theme=theme)

    print(f"=== 5-seat hidden-role game, theme='{theme.name}' ===\n")
    print("--- one seat's private view (seat 0), the exact bytes it would send ---")
    print(ref.render_context(0))
    print("\n--- play ---")
    play(ref, rng)
    for line in ref.log:
        print(" ", line)

    leaks = audit(ref)
    print(f"\ngate #1 leak audit: {'CLEAN' if not leaks else leaks} "
          f"({ref.n} seats, every turn)")
    print(f"winner: {ref.theme.faction_names[ref.winner]}")
    print("\n(secret assignment, referee-side only:)")
    for s, r in sorted(ref.assignment.items()):
        print(f"  seat {s}: {r.key}")


if __name__ == "__main__":
    main()
