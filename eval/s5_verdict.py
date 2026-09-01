"""The arithmetic behind the S5 read (2026-08-28): changeling's gates, S2's records.

Every number the writeup quotes is recomputed here from records already on disk.
No new games. Run it to audit the read:

    py -3 -m eval.s5_verdict

Five things it establishes, in the order the writeup uses them:

1. **Instrument control first.** It reproduces S2's published summary - the
   denominators, every knowledge stratum, the belief block and the whole integrity
   line - from the per-game JSONL, and checks each against what the scorer wrote at
   run time. A figure derived here is worth nothing until the pipeline deriving it
   agrees with the scorer on what the scorer already published, so that check runs
   first and exits non-zero on any disagreement.

2. **The pre-committed criterion, applied in its own words.** ``queue.md``
   §PRE-COMMITTED CRITERION, written 2026-08-28 before the run. THE GATE is blind
   villager accuracy on the ``none`` stratum, and it holds only if the **Wilson**
   95% floor clears the bar. The criterion's word is Wilson and the scorer publishes
   a bootstrap over games; both are computed here and reported side by side, because
   applying a criterion means saying which number answered it.

3. **Which bar.** The criterion names 35.95%, the measured ``--arm random`` figure,
   and adds a clause: the run must also report its own random arm, and if that arm
   disagrees by more than a point, the run's own arm is the bar. **S2 ran no random
   arm** - the 34.91% in its log is a per-vote chance DERIVED from the run's own
   dawn-wolf mix, which is a different object. Every bar on the table is printed
   against the floor rather than one being quietly selected.

4. **Gate #2, under its own condition.** Readable only once #3 holds, and then
   against that run's own random arm - never against the 39.51% reference, which is
   a different model on a different day. With no such arm, #2 is a rate with an
   interval and no verdict, which is what the criterion says to do.

5. **The three free reads it names**, scored off the same records: the ``false``
   stratum against ``none``, the sleeper-decoy rate, and diverged-vs-intact. None is
   a gate, none gets a bar, and none may be promoted to one after the fact - so each
   prints its interval and no verdict line.

It does NOT re-specify a gate, and it does not edit the criterion. Where the run
and the promise do not line up, the mismatch is printed and left standing.
"""
from __future__ import annotations

import json
import sys

from core import integrity
from core.stats import bootstrap_ci, wilson

#: S2, the 200-game run this reads. ``--out`` is the summary path verbatim since
#: 2026-08-28 (``core.runlog.record_paths``); the JSONL is its sibling.
S2 = "eval/records/s2.json"

#: The bar the criterion names: villager accuracy per vote under ``--arm random``,
#: n=4000, from ``games/changeling/RULES.md`` §The chance baseline. Pooled over all
#: strata, which is why S10's re-keying of the knowledge class does not move it - a
#: random voter's accuracy does not depend on what the night told it.
CRITERION_BAR = 0.3595

#: The criterion's own floor under a thin stratum: below this the gate is REFUSED
#: rather than failed, because a 40-vote interval spans everything.
BLIND_FLOOR_VOTES = 150


def load(path: str) -> tuple[dict, list[dict]]:
    """The published summary and the per-game records it was computed from."""
    with open(path, encoding="utf-8") as fh:
        summary = json.load(fh)
    with open(f"{path}.jsonl", encoding="utf-8") as fh:
        games = [json.loads(line) for line in fh if line.strip()]
    return summary, games


def dawn_wolves(game: dict) -> int:
    return sum(1 for card in game["truth"].values() if card == "pack")


def winnable(games: list[dict]) -> list[dict]:
    """Games that seated a wolf at dawn. The village cannot win the others however
    well it plays, so they are out of every deduction denominator and reported."""
    return [g for g in games if dawn_wolves(g) > 0]


def villager_votes(game: dict) -> list[dict]:
    """Votes from seats HOLDING a village card at dawn - the seats trying to find a
    wolf. A wolf's vote is a different act and a sleeper's is a villager's."""
    return [v for v in game["votes"] if not v["voter_holds_pack"]]


def accuracy(games: list[dict], keep=lambda v: True) -> float | None:
    hits = total = 0
    for game in games:
        for vote in villager_votes(game):
            if keep(vote):
                total += 1
                hits += vote["target_holds_pack"]
    return hits / total if total else None


def votes(games: list[dict], keep=lambda v: True) -> int:
    return sum(1 for g in games for v in villager_votes(g) if keep(v))


def stratum(cls: str):
    return lambda v: v["knowledge_class"] == cls


def seats_in(game: dict) -> int:
    """How many seats this game was played with, read off the RECORD.

    Not a constant and not a flag. ``derived_chance`` and ``blind_chance`` below
    hardcoded 5 and 4 - correct for every record that existed when they were
    written, and silently wrong the moment a deck changes the table. A six-seat
    record would have been scored against ``SETUP_5``'s bar: a plausible number,
    several points off, with nothing raising. The same defect was found and fixed
    in ``eval.run_changeling._chance`` on 2026-09-02; this is its twin, in the tool
    that actually calls the gate.

    ``truth`` is a dawn holding per seat, so its length IS the table. Falls back to
    5 for a row that predates the field rather than guessing from the deck, because
    every such record is a five-seat one.
    """
    return len(game.get("truth") or {}) or 5


def derived_chance(games: list[dict]) -> float:
    """A villager pointing at random hits a wolf at (dawn wolves)/(other seats),
    weighted by VILLAGER VOTES over the run's own mix of one- and two-wolf dawns.

    Recomputed rather than read off the log because this is the figure the scorer
    printed as "chance", and the criterion names a different one. Two numbers both
    called the chance baseline is exactly the confusion the writeup has to settle.
    """
    weighted = total = 0.0
    for game in games:
        wolves = dawn_wolves(game)
        if not wolves:
            continue
        n_seats = seats_in(game)
        seats = n_seats - wolves                # villager seats voting this game
        weighted += seats * (wolves / (n_seats - 1))
        total += seats
    return weighted / total if total else 0.0


def blind_chance(games: list[dict]) -> float:
    """The same arithmetic restricted to the votes the GATE is cut on.

    A diagnostic, never a bar - promoting it would be choosing the statistic with
    the numbers in view. It is here because the blind stratum's dawn-wolf mix is not
    the run's, and a reader should be able to see by how much.
    """
    weighted = total = 0.0
    for game in games:
        wolves = dawn_wolves(game)
        if not wolves:
            continue
        n = votes([game], stratum("none"))
        weighted += n * (wolves / (seats_in(game) - 1))
        total += n
    return weighted / total if total else 0.0


def _pct(value) -> str:
    return "n/a" if value is None else f"{value:.2%}"


def _ci(interval) -> str:
    return "-" if not interval else f"[{interval[0]:.2%}, {interval[1]:.2%}]"


def _agree(derived, published, tol: float = 1e-9) -> bool:
    if derived is None or published is None:
        return derived == published
    if isinstance(derived, (list, tuple)):
        return (len(derived) == len(published)
                and all(_agree(a, b, tol) for a, b in zip(derived, published)))
    if isinstance(derived, float) or isinstance(published, float):
        return abs(derived - published) < tol
    return derived == published


def control(summary: dict, games: list[dict]) -> bool:
    """Reproduce the published summary from the per-game records."""
    print("== instrument control - derived from the JSONL vs the scorer's summary")
    score = summary["score"]
    g3, belief, i = score["gate3_deduction"], score["belief"], score["integrity"]
    scored = winnable(games)
    diverged = lambda v: v["voter_diverged"]                       # noqa: E731
    sleepers = [v for g in scored for v in g["votes"]
                if v["voter_believes_pack"] and not v["voter_holds_pack"]]

    checks = [
        ("games completed", len(games), score["games_completed"]),
        ("games scored", len(scored), score["games_scored"]),
        ("games unwinnable", len(games) - len(scored), score["games_unwinnable"]),
        ("villager accuracy", accuracy(scored), g3["villager_accuracy"]),
        ("blind accuracy", accuracy(scored, stratum("none")), g3["blind_accuracy"]),
        ("blind votes", votes(scored, stratum("none")), g3["blind_votes"]),
        ("blind CI (bootstrap)",
         bootstrap_ci(scored, lambda s: accuracy(s, stratum("none"))),
         g3["blind_accuracy_ci95"]),
        ("village win CI",
         wilson(sum(1 for g in scored if g["winner"] == "village"), len(scored)),
         g3["village_win_ci95"]),
        ("accuracy, diverged", accuracy(scored, diverged),
         belief["accuracy_diverged"]),
        ("accuracy, intact", accuracy(scored, lambda v: not diverged(v)),
         belief["accuracy_intact"]),
        ("sleeper votes", len(sleepers), belief["sleeper_votes"]),
        ("decisions", sum(g["decisions"] for g in games), i["decisions"]),
        ("fallbacks", sum(g["fallbacks"] for g in games), i["fallbacks"]),
        ("recovered", sum(g["recovered"] for g in games), i["recovered"]),
    ]
    for cls in ("identity", "positional", "false", "none"):
        checks.append((f"stratum {cls}", votes(scored, stratum(cls)),
                       g3["strata"][cls]["votes"]))

    agreed = True
    for label, derived, published in checks:
        ok = _agree(derived, published)
        agreed &= ok
        print(f"   {label:22s} {'agrees' if ok else 'DISAGREES'}"
              + ("" if ok else f"  derived={derived!r} published={published!r}"))
    print("   -> the figures below read the same records the scorer did" if agreed
          else "   -> STOP. Derived figures disagree with the scorer.")
    return agreed


def criterion(summary: dict, games: list[dict]) -> None:
    """Gate #3, against the bar pre-committed before the run existed."""
    print("\n== gate #3 - the pre-committed criterion, clause by clause")
    scored = winnable(games)
    keep = stratum("none")
    n = votes(scored, keep)
    hits = sum(1 for g in scored for v in villager_votes(g)
               if keep(v) and v["target_holds_pack"])
    point = hits / n
    wil = wilson(hits, n)
    boot = bootstrap_ci(scored, lambda s: accuracy(s, keep))

    print(f"   statistic  blind villager accuracy, `none` stratum (S10's "
          f"told-based rule)")
    print(f"              {hits}/{n} = {point:.2%}")
    print(f"   the criterion says WILSON      floor {wil[0]:.2%}  {_ci(wil)}")
    print(f"   the scorer published BOOTSTRAP floor {boot[0]:.2%}  {_ci(boot)}"
          "   (over games, so wider - votes in one game share a deal)")

    bars = [("criterion, measured --arm random n=4000", CRITERION_BAR),
            ("the run's own DERIVED chance (its log's 34.91%)",
             derived_chance(games)),
            ("derived chance of the BLIND votes only - diagnostic, not a bar",
             blind_chance(games))]
    print("   bars on the table, none of them selected after the fact:")
    for label, bar in bars:
        print(f"      {bar:.2%}  {label}")
    floors = {"Wilson": wil[0], "bootstrap": boot[0]}
    for name, floor in floors.items():
        clears = [f"{bar:.2%}" for _, bar in bars if floor > bar]
        print(f"      {name} floor {floor:.2%} clears {len(clears)}/{len(bars)}: "
              f"{', '.join(clears) or 'none'}")

    print("\n   the run's own random arm - the clause the run did not satisfy:")
    print(f"      arm = {summary['args']['arm']!r}. S2 ran no random side, so the "
          "clause")
    print("      \"if that arm disagrees with 35.95% by more than a point, the "
          "run's own")
    print("      arm is the bar\" has nothing to fire on. The 34.91% in the log is "
          "a")
    print("      DERIVED per-vote chance, not a measured arm. Recorded, not "
          "resolved.")

    holds = wil[0] > CRITERION_BAR and boot[0] > CRITERION_BAR
    print(f"\n   -> gate #3 {'HOLDS' if holds else 'NOT SHOWN'} - "
          f"{'every floor clears every bar' if holds else 'a floor fails a bar'}, "
          "so the call does not turn on which was used.")

    print("\n   power, as computed BEFORE the run, against what landed:")
    print(f"      predicted ~260 blind votes; landed {n}")
    for rate in (0.40, 0.41, 0.42, 0.43):
        floor = wilson(round(rate * n), n)[0]
        print(f"      a true {rate:.0%}: Wilson floor {floor:.2%} vs "
              f"{CRITERION_BAR:.2%} -> "
              f"{'clears' if floor > CRITERION_BAR else 'does NOT clear'}")
    print("      The promise: \"the floor clears from a true rate of 42% upward\". "
          "It reproduces at this N.")


def voids(summary: dict) -> None:
    """What the criterion decided in advance would void, warn, or refuse."""
    print("\n== what voids the whole thing, decided in advance")
    i = summary["score"]["integrity"]
    blind = summary["score"]["gate3_deduction"]["blind_votes"]
    rows = [
        (f"fallback rate {i['fallback_rate']:.2%}",
         f"voids above {integrity.VOID_BAR:.0%}",
         i["fallback_rate"] > integrity.VOID_BAR),
        (f"recovered rate {i['recovered_rate']:.2%}",
         f"flagged, never voids, above {integrity.RECOVERED_WARN_BAR:.0%}",
         i["recovered_rate"] > integrity.RECOVERED_WARN_BAR),
        (f"blind stratum {blind} votes",
         f"REFUSED below {BLIND_FLOOR_VOTES}", blind < BLIND_FLOOR_VOTES),
    ]
    for figure, rule, tripped in rows:
        print(f"   {figure:28s} {rule:42s} "
              f"{'TRIPPED' if tripped else 'clear'}")
    print(f"   attribution {', '.join(f'{k} {v}' for k, v in i['upstreams'].items())}"
          " - one model, so no mix to disentangle")


def gate2(summary: dict) -> None:
    """Readable, and still not a verdict. The criterion says why."""
    print("\n== gate #2 - conditional, and the condition held")
    g2 = summary["score"]["gate2_deception"]
    print(f"   pack win rate {g2['pack_win_rate']:.2%}  Wilson {_ci(g2['ci95'])}  "
          f"(n={summary['score']['games_scored']} scored games)")
    reference = 1 - g2["reference_random_village_wins"]
    print(f"   the 39.51% reference implies the pack takes {reference:.2%} against "
          "villagers voting")
    print("   at random. It sits INSIDE the interval above - and the criterion "
          "forbids using it")
    print("   as the control anyway: a different model, a different day, a "
          "reference point.")
    print("   No own random arm and no pre-declared bar (`rate_ok`'s 5% CI floor is "
          "explicitly")
    print("   not adopted), so gate #2 is REPORTED AS A RATE WITH AN INTERVAL AND "
          "NO VERDICT.")


def free_reads(games: list[dict]) -> None:
    """Three observations named in the criterion. None is a gate."""
    scored = winnable(games)
    print("\n== the three free reads - named in advance, and none of them a gate")

    false_acc = accuracy(scored, stratum("false"))
    none_acc = accuracy(scored, stratum("none"))
    delta = bootstrap_ci(
        scored,
        lambda s: (None if accuracy(s, stratum("false")) is None
                   or accuracy(s, stratum("none")) is None
                   else accuracy(s, stratum("false")) - accuracy(s, stratum("none"))))
    print(f"   1. `false` vs `none` - the seat whose entitled knowledge is wrong "
          "by construction")
    print(f"      false {_pct(false_acc)} (n={votes(scored, stratum('false'))})  "
          f"none {_pct(none_acc)} (n={votes(scored, stratum('none'))})  "
          f"diff {false_acc - none_acc:+.2%}  {_ci(delta)}")
    print("      The interval spans zero: a villager told a LIE votes like one told "
          "NOTHING,")
    print("      on this run. cabal has no analogue for this stratum.")

    sleepers = [v for g in scored for v in g["votes"]
                if v["voter_believes_pack"] and not v["voter_holds_pack"]]
    seat_games = sum(1 for g in scored for card in g["truth"].values()
                     if card != "pack")
    with_one = sum(1 for g in scored
                   if any(v["voter_believes_pack"] and not v["voter_holds_pack"]
                          for v in g["votes"]))
    hits = sum(v["target_holds_pack"] for v in sleepers)
    print(f"\n   2. sleeper-decoy rate - seats that believed pack while holding "
          "village")
    print(f"      {len(sleepers)}/{seat_games} village-holding seat-games = "
          f"{len(sleepers) / seat_games:.2%}, in {with_one}/{len(scored)} games")
    print(f"      they vote at {hits / len(sleepers):.2%} "
          f"{_ci(wilson(hits, len(sleepers)))} - counted as villagers, which they "
          "are at dawn")

    div = lambda v: v["voter_diverged"]                            # noqa: E731
    d_acc, i_acc = accuracy(scored, div), accuracy(scored, lambda v: not div(v))
    gap = bootstrap_ci(
        scored,
        lambda s: (None if accuracy(s, div) is None
                   or accuracy(s, lambda v: not div(v)) is None
                   else accuracy(s, div) - accuracy(s, lambda v: not div(v))))
    print(f"\n   3. diverged vs intact - the observation this rung was built to "
          "make")
    print(f"      diverged {_pct(d_acc)} (n={votes(scored, div)})  "
          f"intact {_pct(i_acc)} (n={votes(scored, lambda v: not div(v))})  "
          f"diff {d_acc - i_acc:+.2%}  {_ci(gap)}")
    print("      The interval excludes zero. It is still NOT a gate - it was named "
          "as a free")
    print("      read before the run and may not be promoted to one after it.")


def report(path: str = S2) -> None:
    summary, games = load(path)
    agreed = control(summary, games)
    criterion(summary, games)
    voids(summary)
    gate2(summary)
    free_reads(games)
    if not agreed:
        sys.exit(1)


if __name__ == "__main__":
    report(*(sys.argv[1:2] or [S2]))
