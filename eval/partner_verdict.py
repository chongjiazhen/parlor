"""The changeling partner-protection arm, scored as its criterion promised.

``py -3 -m eval.partner_verdict [records-dir]`` reads the two records
``eval/runs/changeling-partner-arm.cmd`` writes - one live arm and its random
control on the same deals - and prints the read
``docs/changeling-partner-criterion.md`` pre-committed: the pack's partner-vote
rate, arm minus control, under a Newcombe interval, voids first.

The count is NOT reimplemented here. It is ``eval.changeling_audit``'s
``partner_votes``, the same function whose free reads on four earlier arms are
why this criterion exists - so the primary and the free read that motivated it
cannot drift apart. Blind villager accuracy, the primary of both pair criteria,
is a free read in this file and carries no verdict: a gate #3 call belongs to a
criterion that made it primary.

A voided or refused record is still AUDITED - every figure prints and the exit
code says 3 - because this repo publishes numbers from records and a scorer that
returns early leaves a published number with no instrument in the tree.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from core import integrity
from core.stats import wilson
from eval.changeling_audit import partner_votes
from eval.gate3_bar import REFERENCE_CHANCE
from eval.skin_pair_verdict import (
    BLIND,
    Arm,
    Verdict,
    _ci,
    _excludes_zero,
    load,
    newcombe,
)

#: The frozen file this module answers to. The settings below are a COPY of its
#: §Settings block and a test reads the file to hold them equal - the failure
#: this repo has already paid for (belfry live1) is a launcher and a criterion
#: disagreeing while each looked right on its own.
CRITERION = "docs/changeling-partner-criterion.md"
STEM = "cl-partner"
EXPECTED = {"arm": "llm", "theme": "folk", "seats": 5, "seed": 17000,
            "rounds": 2, "no_thinking": True, "temperature": 0.8,
            "model": "qwen36-35b-a3b-iq3"}
#: Under this many partner-eligible votes the read is REFUSED, not called.
VOTES_FLOOR = 150


def settings_voids(args: dict) -> list[str]:
    """Every criterion setting the record's own `args` contradicts."""
    return [f"{k} is {args.get(k)!r}, criterion says {v!r}"
            for k, v in EXPECTED.items() if args.get(k) != v]


def partner(games: list[dict]) -> tuple[int, int]:
    """(votes for the fellow, votes by seats that were told one)."""
    hits, total, _, _ = partner_votes(games)
    return hits, total


def _eligible_by_game(games: list[dict]) -> dict:
    return {g.get("game"): partner_votes([g])[1] for g in games}


def census_void(arm_games: list[dict], ctrl_games: list[dict]) -> str | None:
    """The criterion's census check, over the deals the two actually share.

    Random play does not speak, so eligibility - who was told a fellow - is a
    property of the DEAL and must match seed for seed. The control is five times
    the arm, so only the shared game indices are compared; a disagreement there
    means the deal moved under the arm and no difference is readable.
    """
    arm_n, ctrl_n = _eligible_by_game(arm_games), _eligible_by_game(ctrl_games)
    shared = [i for i in arm_n if i in ctrl_n]
    if not shared:
        return "arm and control share no game index - not the same deal"
    off = [i for i in shared if arm_n[i] != ctrl_n[i]]
    if off:
        return (f"{len(off)} of {len(shared)} shared deals disagree on the "
                f"eligible count, first at game {off[0]}")
    return None


def verdict(arm: Arm, ctrl: Arm) -> Verdict:
    """The call, voids first, exactly as the criterion ordered them."""
    ha, na = partner(arm.games)
    hc, nc = partner(ctrl.games)
    interval = newcombe(hc, nc, ha, na) if na and nc else None
    diff = None if not na or not nc else ha / na - hc / nc

    reasons: list[str] = []
    if arm.fallback_rate > integrity.VOID_BAR:
        reasons.append(f"{arm.name}: fallback {arm.fallback_rate:.2%} above "
                       f"{integrity.VOID_BAR:.0%}")
    if census := census_void(arm.games, ctrl.games):
        reasons.append(f"census: {census}")
    if reasons:
        return Verdict("VOID", tuple(reasons), diff, interval, None)

    if na < VOTES_FLOOR:
        reasons.append(f"{arm.name}: {na} partner-eligible votes, under "
                       f"{VOTES_FLOOR}")
    if reasons or interval is None:
        return Verdict("REFUSED",
                       tuple(reasons) or ("an arm has no eligible votes",),
                       diff, interval, None)

    informs = _excludes_zero(interval)
    return Verdict("INFORMS" if informs else "NOT SHOWN",
                   (f"Newcombe interval {'excludes' if informs else 'includes'}"
                    " zero",), diff, interval, None)


def report(records: Path) -> int:
    path = records / f"{STEM}.json"
    with open(path, encoding="utf-8") as fh:
        args = json.load(fh)["args"]
    arm, ctrl = load(path), load(records / f"{STEM}-random.json")

    print("== settings pin - the record's own args against the criterion")
    voids = settings_voids(args)
    print(f"   {STEM:12s} {'matches' if not voids else 'VOIDED'}")
    for v in voids:
        print(f"      {v}")

    print("\n== read the fallback rate FIRST")
    flag = (" RECOVERED FLAGGED"
            if arm.recovered_rate > integrity.RECOVERED_WARN_BAR else "")
    print(f"   {STEM:12s} fallback {arm.fallback_rate:.2%}  recovered "
          f"{arm.recovered_rate:.2%}{flag}  games {len(arm.games)}, scored "
          f"{len(arm.scored)}")

    v = verdict(arm, ctrl)
    ha, na = partner(arm.games)
    hc, nc = partner(ctrl.games)
    print("\n== the primary - a pack seat voted the fellow it was told")
    print(f"   arm      {ha}/{na} = {ha / na:.2%}  Wilson {_ci(wilson(ha, na))}"
          if na else "   arm      refused")
    print(f"   control  {hc}/{nc} = {hc / nc:.2%}  Wilson {_ci(wilson(hc, nc))}"
          if nc else "   control  refused")
    print(f"   difference (arm minus control) {v.diff:+.2%}"
          if v.diff is not None else "   difference refused")
    print(f"   Newcombe 95%  {_ci(v.newcombe)}   <- the interval the criterion "
          "names")
    print("   below the control is the pack PROTECTING its partner; above it is "
          "the opposite. The criterion pre-commits neither.")

    print("\n== free read, no verdict - blind villager accuracy")
    for name, a in ((STEM, arm), (f"{STEM}-random", ctrl)):
        hits, k = a.blind
        point = f"{hits / k:.2%}" if k else "refused"
        print(f"   {name:20s} {hits}/{k} = {point}  Wilson {_ci(wilson(hits, k))}")
    print(f"   the reference is {REFERENCE_CHANCE:.2%}; this file makes no gate "
          "#3 call, its criterion did not name one")

    for r in v.reasons:
        print(f"   {r}")
    call = v.call if not voids else f"VOID (settings) - the arithmetic read {v.call}"
    print(f"\n   -> {call}")
    return 0 if not voids and v.call in ("INFORMS", "NOT SHOWN") else 3


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    return report(Path(args[0]) if args else Path("eval/records"))


if __name__ == "__main__":
    sys.exit(main())
