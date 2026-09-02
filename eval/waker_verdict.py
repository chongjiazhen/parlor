"""``docs/changeling-waker-criterion.md`` as arithmetic - the S19 verdict.

    py -3 -m eval.waker_verdict                       # the arm the criterion promised
    py -3 -m eval.waker_verdict <record.json>         # audit any other record
    py -3 -m eval.waker_verdict --transcript out.md   # and render the evidence

**A separate module from ``eval.s5_verdict`` on purpose.** That tool takes a record
path and its arithmetic went table-general on 2026-09-02, so it LOOKS like the tool
for this arm. It is not: its ``CRITERION_BAR`` is S2's 35.95% and the narrative
around it is S2's promises verbatim - no random side, ~260 blind votes, clears from
42% up. Pointed at a six-seat record it would call this gate against the five-seat
bar and print the wrong criterion's power line underneath, at exit 0. It also
reproduces a PUBLISHED number, so it is the wrong thing to rebuild. Belfry already
answers this shape with one verdict module per criterion; this is that pattern.

What it does NOT do: re-specify a gate, choose a statistic, or edit the criterion.
Every bar below is quoted from a document written before the run. Where the run and
the promise fail to line up, the mismatch is printed and left standing - the clause
S5 had to record rather than smooth.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

from core import integrity
from core.stats import bootstrap_ci, wilson
from eval.s5_verdict import (accuracy, blind_chance, dawn_wolves, derived_chance,
                             load, seats_in, stratum, villager_votes, votes,
                             winnable)

#: The arm the criterion promised, and its paired control on the same seeds.
CAMPAIGN = "eval/records/waker1.json"
CONTROL = "eval/records/waker1-random.json"
DOC = "docs/changeling-waker-criterion.md"

#: **THE BAR.** Quoted from the criterion, which measured it BEFORE the run with
#: ``--arm random --seats 6 --games 4000 --seed 900000``: the derived per-vote
#: chance of that arm. The criterion also records the arm's own measured blind
#: accuracy, 28.82%, and names the HIGHER of the two so a reader cannot pick after
#: the fact. Taking the higher makes the gate harder by 1.3 points.
CRITERION_BAR = 0.3014
MEASURED_ARM_BLIND = 0.2882

#: The criterion's own tolerance: "if the run's own random arm disagrees with
#: 30.14% by more than a point, that arm is the bar and this number is the thing
#: that was wrong."
OWN_ARM_TOLERANCE = 0.01

#: Below this the gate is REFUSED rather than failed - a 40-vote interval spans
#: everything and reads as a result.
BLIND_FLOOR_VOTES = 150

#: Pre-committed power: 1.383 blind votes per scored game x 200 x 98.4% winnable.
PREDICTED_BLIND_VOTES = 272
#: "the floor clears 30.14% from a true rate of 36% upward; 35% does not clear"
PROMISED_DETECTABLE = 0.36

GAMES_PROMISED = 200


def blind(v: dict) -> bool:
    """The gate's own denominator: a villager seat the night told NOTHING, keyed by
    S10's told-based rule. ``villager_votes`` has already dropped dawn wolves."""
    return v["knowledge_class"] == "none"


def blind_accuracy(games: list[dict]) -> float | None:
    return accuracy(games, blind)


def waker_seated(game: dict) -> bool:
    return "waker" in (game.get("dealt") or {}).values()


def _pct(value) -> str:
    return "n/a" if value is None else f"{value:.2%}"


def _ci(interval) -> str:
    return "" if interval is None else f" [{interval[0]:.2%}, {interval[1]:.2%}]"


def control_reads(path: str) -> dict | None:
    """The paired random arm on the same seeds - what the own-arm clause reads.

    ``None`` when it is absent, and that is REPORTED rather than defaulted: S2 ran
    no random side, the clause had nothing to fire on, and S5 had to record that.
    A tool that quietly used the criterion's number would have hidden it.
    """
    try:
        summary, games = load(path)
    except FileNotFoundError:
        return None
    live = winnable(games)
    return {"path": path, "games": len(games), "scored": len(live),
            "derived": derived_chance(live), "blind": blind_accuracy(live),
            "blind_votes": votes(live, blind),
            "arm": summary.get("args", {}).get("arm")}


def integrity_lines(summary: dict, games: list[dict]) -> tuple[list[str], bool]:
    """The pre-committed void conditions. Returns (lines, voided)."""
    score = summary.get("score", {})
    out, voided = [], False
    decisions = sum(g.get("decisions", 0) for g in games)
    fallbacks = sum(g.get("fallbacks", 0) for g in games)
    recovered = sum(g.get("recovered", 0) for g in games)
    rate = fallbacks / decisions if decisions else 0.0
    if rate > 0.10:
        out.append(f"   VOID: fallback {rate:.2%} of {decisions} decisions is over "
                   "the pre-committed 10% ceiling. A decision no model could make "
                   "legally is played at random; a run that hides that is the "
                   "random policy wearing a model's name.")
        voided = True
    else:
        out.append(f"   fallback {fallbacks}/{decisions} = {rate:.2%}, under the "
                   "10% ceiling")
    rec_rate = recovered / decisions if decisions else 0.0
    flag = " - FLAGGED beside the verdict, not a void" if rec_rate > integrity.RECOVERED_WARN_BAR else ""
    out.append(f"   recovered {recovered}/{decisions} = {rec_rate:.2%}{flag}")
    played = score.get("games_completed", len(games))
    if played < GAMES_PROMISED:
        out.append(f"   VOID: {played} played games against {GAMES_PROMISED} "
                   "promised - a short run is not a small arm")
        voided = True
    else:
        out.append(f"   {played} played games, as promised")
    return out, voided


def waker_seat(game: dict) -> int | None:
    """The seat DEALT the waker, or ``None``. Dealt, not held: this read is about
    the seat that performed the wake, and ``WAKE`` is last in ``NIGHT_ORDER`` so
    nothing moves after it - that seat's belief matches its dawn truth whatever
    card it ends up holding, which is the whole property the deck was built to
    seat."""
    for seat, card in (game.get("dealt") or {}).items():
        if card == "waker":
            return int(seat)
    return None


def waker_votes(games: list[dict]) -> list[dict]:
    """Villager votes cast BY the waker seat. A wolf's vote is a different act, so
    ``villager_votes`` has already dropped them - including a waker whose card was
    stolen and who holds ``pack`` at dawn."""
    out = []
    for game in games:
        seat = waker_seat(game)
        if seat is None:
            continue
        out += [v for v in villager_votes(game) if v["seat"] == seat]
    return out


def table_votes(games: list[dict]) -> list[dict]:
    """Every OTHER villager vote at the same tables - the comparison set."""
    out = []
    for game in games:
        seat = waker_seat(game)
        if seat is None:
            continue
        out += [v for v in villager_votes(game) if v["seat"] != seat]
    return out


def _rate(vs: list[dict]) -> float | None:
    return sum(v["target_holds_pack"] for v in vs) / len(vs) if vs else None


def card_moved(game: dict, seat: int) -> bool:
    """Did the night move this seat's card? Dealt against dawn truth."""
    return (game.get("dealt") or {}).get(str(seat)) != game["truth"].get(str(seat))


def _diff(games: list[dict], pick_a, pick_b):
    """(rate_a - rate_b) over a resampled list of GAMES, or ``None``.

    The unit is the game, not the vote - the waker's vote and the table's votes in
    one game share a deal, a night and a table, so treating them as independent
    draws reports an interval far tighter than the data supports. Same reason
    belfry resamples games for discrimination.
    """
    a = [v for g in games for v in pick_a(g)]
    b = [v for g in games for v in pick_b(g)]
    if not a or not b:
        return None
    return (sum(v["target_holds_pack"] for v in a) / len(a)
            - sum(v["target_holds_pack"] for v in b) / len(b))


def waker_seat_read(games: list[dict]) -> list[str]:
    """**The question this deck was built to ask.** An OBSERVATION with no bar -
    the criterion pre-registered it that way and forbids promoting it after the
    fact, because the seat casts one vote per game.

    Three comparisons, fixed before the numbers were looked at, and each reported
    as a DIFFERENCE with a game bootstrap rather than two intervals side by side.
    Overlapping Wilson bands are not a comparison: they answer "could each rate be
    equal to some third value", which is not the question.

    1. the waker seat against every other villager at the same tables;
    2. the waker seat against the ``identity`` stratum only - the like-for-like
       set, since both know a card, so a gap here is about knowing YOUR OWN card
       rather than about knowing one at all;
    3. the waker split on whether the night MOVED its card, which is the
       divergence question the rung exists for. Not on ``voter_diverged``: the
       waker wakes last in ``NIGHT_ORDER``, so nothing moves after it and its
       belief always matches its truth. That field is False for this seat by
       construction, and the read below asserts it rather than quietly reporting
       a zero-vote cell.

    **The waker is never in the blind stratum**, so the seated-versus-centre split
    in `docs/measurements.md` cannot answer this and is a different reading.
    """
    seated = [g for g in games if waker_seat(g) is not None]

    # One implementation each, shared with the module-level readers - a
    # second copy here is what a test can guard while the report calls the
    # other. Measured: a mutant that put the waker back into the table set
    # passed 24 of 24 while these were duplicated.
    def w_of(g):
        return waker_votes([g])

    def t_of(g):
        return table_votes([g])

    def ident_of(g):
        return [v for v in t_of(g) if v["knowledge_class"] == "identity"]

    out = ["", "the waker SEAT itself - the question the deck was built to ask",
           "   pre-registered as an OBSERVATION with no bar. Differences carry a "
           "game bootstrap; two overlapping Wilson bands are not a comparison."]

    wv, tv = [v for g in seated for v in w_of(g)], [v for g in seated for v in t_of(g)]
    iv = [v for g in seated for v in ident_of(g)]
    for label, vs in (("waker seat", wv), ("every other villager", tv),
                      ("...of those, identity", iv)):
        n = len(vs)
        out.append(f"   {label:24s} {_pct(_rate(vs))}"
                   f"{_ci(wilson(round((_rate(vs) or 0) * n), n))} ({n} votes)")

    for label, pick in (("vs the whole table", t_of), ("vs identity only", ident_of)):
        point = _diff(seated, w_of, pick)
        ci = bootstrap_ci(seated, lambda gs, p=pick: _diff(gs, w_of, p))
        reads = (ci is not None and (ci[0] > 0 or ci[1] < 0))
        out.append(f"   difference {label:20s} {_pct(point)}{_ci(ci)}"
                   + ("  - the interval clears zero" if reads
                      else "  - the interval SPANS zero"))

    diverged = [v for v in wv if v["voter_diverged"]]
    out.append(f"   instrument control: {len(diverged)} waker vote(s) marked "
               "diverged - WAKE is last, so belief always matches truth here and "
               "anything but zero means the night order changed under this read")

    moved = [v for g in seated for v in w_of(g) if card_moved(g, waker_seat(g))]
    intact = [v for g in seated for v in w_of(g)
              if not card_moved(g, waker_seat(g))]
    for label, vs in (("waker, card was moved", moved),
                      ("waker, card untouched", intact)):
        n = len(vs)
        out.append(f"   {label:24s} {_pct(_rate(vs))}"
                   f"{_ci(wilson(round((_rate(vs) or 0) * n), n))} ({n} votes)")
    out.append("   No bar, no verdict, and not promotable to one - the criterion "
               "said so before the run.")
    return out


def report(path: str = CAMPAIGN, control_path: str = CONTROL) -> tuple[list[str], int]:
    summary, games = load(path)
    args = summary.get("args", {})
    off_criterion = path != CAMPAIGN
    out = [f"changeling waker arm - {path}",
           f"criterion: {DOC} (pre-committed, not editable)"]
    if off_criterion:
        out += ["", f"** NOT the pre-committed arm ({CAMPAIGN} is in force). The "
                    "arithmetic below is an AUDIT of this record, never a verdict. **"]

    # ---- instrument control, first and always -----------------------------
    live = winnable(games)
    seat_counts = {seats_in(g) for g in games}
    out += ["", "instrument control - the record against what the criterion promised"]
    out.append(f"   seats {sorted(seat_counts)} "
               + ("- the six-seat waker deck" if seat_counts == {6}
                  else "- DISAGREES: the criterion is SETUP_6_WAKER, six seats"))
    for field, want in (("seats", 6), ("seed", 12000), ("temperature", 0.8),
                        ("rounds", 2), ("arm", "llm")):
        got = args.get(field)
        ok = got == want
        out.append(f"   {field:12s} {got!r}" + ("" if ok else f"  DISAGREES: promised {want!r}"))
    if not args.get("no_thinking"):
        out.append("   no_thinking  DISAGREES: the criterion promised --no-thinking")
    published = summary.get("score", {}).get("gate3_deduction", {}).get("blind_votes")
    recomputed = votes(live, blind)
    agrees = published is None or published == recomputed
    out.append(f"   blind votes  scorer {published}, recomputed {recomputed}"
               + ("  agrees" if agrees else "  DISAGREES"))
    if not agrees:
        out += ["", "no verdict: a number this file derives is worth nothing until "
                    "it agrees with what the scorer published."]
        return out, 1

    # ---- the void conditions ----------------------------------------------
    out += ["", "void conditions, pre-committed"]
    lines, voided = integrity_lines(summary, games)
    out += lines
    out.append(f"   {len(games) - len(live)} game(s) seated no pack at dawn and are "
               f"excluded; scored on {len(live)}")

    # ---- the bar, and the own-arm clause -----------------------------------
    ctrl = control_reads(control_path)
    bar, bar_why = CRITERION_BAR, "the criterion's pre-measured derived chance"
    out += ["", "the bar - and the clause that can move it"]
    out.append(f"   criterion bar {CRITERION_BAR:.2%} (its measured arm read "
               f"{MEASURED_ARM_BLIND:.2%}; the criterion names the HIGHER)")
    if ctrl is None:
        out.append(f"   this run's own random arm: ABSENT at {control_path}. The "
                   "own-arm clause has nothing to fire on and the criterion's bar "
                   "stands. Recorded, not resolved.")
    else:
        gap = abs(ctrl["derived"] - CRITERION_BAR)
        out.append(f"   this run's own random arm: derived {ctrl['derived']:.2%}, "
                   f"blind accuracy {_pct(ctrl['blind'])} over {ctrl['blind_votes']} "
                   f"votes on {ctrl['scored']} scored games")
        if gap > OWN_ARM_TOLERANCE:
            bar = ctrl["derived"]
            bar_why = (f"the RUN'S OWN random arm - it disagrees with the "
                       f"criterion's {CRITERION_BAR:.2%} by {gap:.2%}, over the "
                       "one-point tolerance, so the criterion says this arm is the "
                       "bar and its number was the thing that was wrong")
        else:
            out.append(f"   agrees within {OWN_ARM_TOLERANCE:.0%} ({gap:.2%}), so "
                       "the criterion's bar stands")
    out.append(f"   THE BAR IS {bar:.2%} - {bar_why}")

    # ---- gate #3 ------------------------------------------------------------
    n = votes(live, blind)
    hits = round((blind_accuracy(live) or 0) * n)
    out += ["", "gate #3 - blind villager accuracy, the pre-committed statistic"]
    out.append("   statistic  votes by villager seats the night told NOTHING "
               "(`none` stratum, S10's told-based rule)")
    if n < BLIND_FLOOR_VOTES:
        out += [f"   {hits}/{n} = {_pct(blind_accuracy(live))}",
                f"   REFUSED, not failed: {n} blind votes is under the "
                f"pre-committed floor of {BLIND_FLOOR_VOTES}. An interval this wide "
                "spans everything and would read as a result."]
        return out, 3 if not voided else 2

    wil = wilson(hits, n)
    boot = bootstrap_ci(live, blind_accuracy)
    out += [f"   {hits}/{n} = {blind_accuracy(live):.2%}",
            f"   Wilson    floor {wil[0]:.2%}{_ci(wil)}",
            f"   bootstrap floor {boot[0]:.2%}{_ci(boot)}   (over games, so wider - "
            "votes in one game share a deal)"]
    out.append("   the criterion requires BOTH floors to clear, stated in advance "
               "because S5 had to record which applied after the fact")
    clears = {"Wilson": wil[0] > bar, "bootstrap": boot[0] > bar}
    for name, ok in clears.items():
        out.append(f"      {name} floor {'%.2f%%' % (100 * (wil[0] if name == 'Wilson' else boot[0]))} "
                   f"{'clears' if ok else 'does NOT clear'} {bar:.2%}")
    holds = all(clears.values()) and not voided
    if voided:
        out.append("   -> gate #3 VOID - a void condition fired above. The "
                   "arithmetic is printed because a refused record is still audited.")
    else:
        out.append(f"   -> gate #3 {'HOLDS' if holds else 'NOT SHOWN'}"
                   + ("" if holds else " - the criterion's answer for a marginal "
                      "landing is 'not shown', and it pre-committed to no second "
                      "campaign chasing it"))

    out += ["", "   power, as computed BEFORE the run, against what landed:",
            f"      predicted ~{PREDICTED_BLIND_VOTES} blind votes; landed {n}"]
    for rate in (0.34, 0.35, PROMISED_DETECTABLE, 0.38, 0.40):
        floor = wilson(round(rate * n), n)[0]
        out.append(f"      a true {rate:.0%}: Wilson floor {floor:.2%} vs "
                   f"{bar:.2%} -> {'clears' if floor > bar else 'does NOT clear'}")
    out.append(f"      The promise: \"the floor clears from a true rate of "
               f"{PROMISED_DETECTABLE:.0%} upward\".")

    # ---- gate #2, conditional ----------------------------------------------
    out += ["", "gate #2 - deception, conditional on #3"]
    if not holds:
        out.append("   NOT READ. Villagers at chance hand the pack a win rate with "
                   "no deception in it, so #2 is unreadable until #3 holds. The "
                   "criterion says so in advance.")
    else:
        village = sum(1 for g in live if g.get("winner") == "village")
        pack_rate = 1 - village / len(live)
        pw = wilson(len(live) - village, len(live))
        out.append(f"   pack win rate {pack_rate:.2%}{_ci(pw)} over {len(live)} "
                   "scored games")
        if ctrl is not None:
            out.append(f"   against THIS RUN'S own random arm, never a reference "
                       f"from another day")
        out.append("   NO VERDICT: the criterion declares no bar for #2, so it is "
                   "reported as a rate with an interval and nothing more.")

    # ---- the waker split - an observation, never a gate ---------------------
    seated = [g for g in live if waker_seated(g)]
    absent = [g for g in live if not waker_seated(g)]
    out += ["", "the waker split - an OBSERVATION, and the criterion forbids "
            "promoting it to a gate"]
    for label, subset in (("waker seated", seated), ("waker in centre", absent)):
        nn = votes(subset, blind)
        acc = blind_accuracy(subset)
        out.append(f"   {label:16s} {len(subset):3d} games, {nn:3d} blind votes, "
                   f"{_pct(acc)}{_ci(wilson(round((acc or 0) * nn), nn))}")
    out.append("   Different deals, not the same ones - one run carrying its own "
               "control is weaker than same-seed pairing and the criterion says so.")

    # ---- free off the same records, none of them a gate ---------------------
    out += ["", "free off the same records, and none of them a gate"]
    for cls in ("false", "none"):
        nn = votes(live, stratum(cls))
        out.append(f"   `{cls}` stratum   {_pct(accuracy(live, stratum(cls)))} "
                   f"({nn} votes)")
    div = [v for g in live for v in villager_votes(g) if v["voter_diverged"]]
    intact = [v for g in live for v in villager_votes(g) if not v["voter_diverged"]]
    for label, vs in (("diverged", div), ("intact", intact)):
        hit = sum(v["target_holds_pack"] for v in vs)
        out.append(f"   {label:12s}    {_pct(hit / len(vs) if vs else None)} "
                   f"({len(vs)} votes)")
    out.append("   None of the three may be promoted to a gate after the fact.")
    out += waker_seat_read(live)

    out += ["", "**A dated snapshot of one model on one deck, never a claim about "
            "models.**"]
    if voided:
        return out, 2
    return out, 0


def transcript(path: str, lines: list[str], rendered_at: str) -> list[str]:
    """The committed evidence, rendered from the SAME lines the verdict printed.

    Not a second scorer: the body below IS the verdict's output, so the artifact
    cannot disagree with the tool a reader recomputes from. Same contract as the
    quorum and belfry renderers landed 2026-09-02.
    """
    return [f"# Changeling - waker arm verdict", "",
            f"Rendered {rendered_at} from untracked", f"`{path}` and its `.jsonl` "
            f"sibling, by `py -3 -m eval.waker_verdict`.", "",
            f"Criterion `{DOC}`, pre-committed and not editable.", "",
            "```text", *lines, "```"]


def main() -> int:
    ap = argparse.ArgumentParser(
        description="apply the changeling waker-deck criterion")
    ap.add_argument("record", nargs="?", default=CAMPAIGN,
                    help=f"the run summary .json (default {CAMPAIGN})")
    ap.add_argument("--control", default=CONTROL,
                    help="the paired random arm the own-arm clause reads")
    ap.add_argument("--transcript", metavar="PATH",
                    help="also render the committed evidence. A REFUSED "
                         "record still renders - the refusal is the "
                         "finding, and a renderer that returned early "
                         "would leave a published number with no artifact "
                         "behind it.")
    args = ap.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        lines, code = report(args.record, args.control)
    except FileNotFoundError as exc:
        print(f"no record at {exc.filename} - the arm has not been run")
        return 1
    print(chr(10).join(lines))
    if args.transcript:
        # Stamped from the CLOCK, never from a date in a prompt.
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        body = transcript(args.record, lines, stamp)
        with open(args.transcript, "w", encoding="utf-8") as fh:
            fh.write(chr(10).join(body) + chr(10))
        print(f"{chr(10)}wrote {args.transcript}")
    return code


if __name__ == "__main__":
    sys.exit(main())
