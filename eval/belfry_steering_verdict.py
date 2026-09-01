"""Apply Belfry's pre-committed steered-discretion criterion (S23).

S8b showed the model's bounded setup choices are DISTINGUISHABLE from seeded
random. It could not show they are BETTER, and no arm on this recipe can: the
herring reaches exactly one call site, so the good seats it may be placed on are
mechanically exchangeable and there is no board-derived quality ordering to grade
against. What is gradable without inventing a taste nobody here can ground is
whether that discretion FOLLOWS A STATED RULE it needs the board to apply.

The rule's content is a probe, not a claim about good refereeing. See
`docs/belfry-discretion-quality-criterion.md`, which is the binding promise.
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

from core.stats import wilson
from eval.belfry_adjudicator_verdict import (
    ADJUDICATOR_MODEL,
    ADJUDICATOR_TEMPERATURE,
    ArmRead,
    EVENT_FIELDS,
    EvidenceError,
    FALLBACK_CEILING,
    _duplicate_seeds,
    _fmt_rate,
    _herring_from_log,
    _normal_deal,
    _read_arm,
    _recipe_mismatches,
    load,
)
from games.belfry.adjudicator import HERRING_STEER_RULE, preferred_herring
from games.belfry.roles import Align, COMPACT, Team
from games.belfry.state import deal


CONTROL_CAMPAIGN = "eval/records/belfry-steering-control.json"
STEERED_CAMPAIGN = "eval/records/belfry-steering-model.json"
CRITERION_DOC = "docs/belfry-discretion-quality-criterion.md"
GAMES_PROMISED = 360
FIRST_SEED = 6100
LAST_SEED = 6459
SEATS = 5
#: Every compact five-seat deal has three good seats and no outsiders, so the
#: per-call chance of hitting the rule's one preferred option is exactly 1/3.
#: A menu of any other size means the recipe is not this one, and voids.
MENU_SIZE = 3
CHOICE_KEY = "herring_registration"

COMMON_ARGS = {
    "games": GAMES_PROMISED,
    "arm": "random",
    "seats": SEATS,
    "script": "compact",
    "backend": None,
    "model": "auto",
    "rounds": 1,
    "max_days": 12,
    "register": "character",
    "retries": 2,
    "temperature": 0.8,
    "max_tokens": 1536,
    "timeout": 120.0,
    "no_thinking": True,
    "seed": FIRST_SEED,
}
CONTROL_ARGS = {
    **COMMON_ARGS,
    "adjudicator": "random",
    "adjudicator_backend": None,
    "adjudicator_model": None,
    "adjudicator_temperature": None,
    "adjudicator_steer": False,
    "out": CONTROL_CAMPAIGN,
}
STEERED_ARGS = {
    **COMMON_ARGS,
    "adjudicator": "model",
    "adjudicator_backend": "local",
    "adjudicator_model": ADJUDICATOR_MODEL,
    "adjudicator_temperature": ADJUDICATOR_TEMPERATURE,
    "adjudicator_steer": True,
    "out": STEERED_CAMPAIGN,
}

# One arm, one binding - the same object shape S32 landed on the S8 verdict:
# record paths, demanded settings and the promising document move together or
# not at all.
ARMS = {
    "s23": {
        "control": CONTROL_CAMPAIGN,
        "model": STEERED_CAMPAIGN,
        "control_args": CONTROL_ARGS,
        "model_args": STEERED_ARGS,
        "doc": CRITERION_DOC,
    },
}


def offered_order(seed: int, options: list[str]) -> tuple[str, ...]:
    """The menu order the steered ask used, rebuilt from the game seed alone.

    ``ModelAdjudicator._offer`` draws the same stream. A scorer that trusted the
    record's own order instead could not tell the referee's shuffle from a model
    that reordered the menu in its reply.
    """
    order = random.Random(f"belfry-ask:{seed}:{CHOICE_KEY}")
    return tuple(order.sample(options, len(options)))


def _expected(seed: int) -> tuple[tuple[str, ...], tuple[str, ...], str | None,
                                  str | None]:
    """Deal, offered menu, the rule's answer, and the seeded-random outcome."""
    grim = deal(SEATS, COMPACT, random.Random(seed))
    dealt = tuple(seat.dealt.key for seat in grim.seats)
    if grim.find_believer("diviner") is None:
        return dealt, (), None, None
    good = [seat.index for seat in grim.seats if seat.align is Align.GOOD]
    demon = next((seat.index for seat in grim.seats
                  if seat.role.team is Team.DEMON), None)
    if demon is None:
        raise EvidenceError(f"seed {seed} deals no demon")
    options = offered_order(seed, [str(s) for s in good])
    preferred = str(preferred_herring(SEATS, demon, good))
    return dealt, options, preferred, str(grim.herring)


def _steered_event(row: dict, seed: int, options: tuple[str, ...],
                   expected_call: bool,
                   voids: list[str]) -> tuple[dict | None, bool]:
    block = row.get("adjudicator")
    if not expected_call:
        if block is not None:
            voids.append(
                f"steered seed {seed} has provenance for no legal setup call")
        return None, False
    if block is None:
        voids.append(f"steered seed {seed} is missing adjudicator provenance")
        return None, False
    events = block.get("events", []) if isinstance(block, dict) else []
    if len(events) != 1 or not isinstance(events[0], dict):
        voids.append(
            f"steered seed {seed} does not carry exactly one choice event")
        return None, False
    event = events[0]
    if set(event) != EVENT_FIELDS:
        voids.append(f"steered seed {seed} provenance fields are not "
                     + ", ".join(sorted(EVENT_FIELDS)))
        return None, False
    if event["key"] != CHOICE_KEY:
        voids.append(f"steered seed {seed} carries unknown choice key "
                     f"{event['key']!r}")
        return None, False
    if not isinstance(event["options"], list) or tuple(event["options"]) != options:
        voids.append(f"steered seed {seed} offered menu does not reconstruct")
        return None, False
    if event["selected"] not in options:
        voids.append(f"steered seed {seed} selected a value outside its legal menu")
        return None, False
    if type(event["fallback"]) is not bool or type(event["recovered"]) is not bool:
        voids.append(f"steered seed {seed} has non-boolean provenance flags")
        return None, False
    if event["fallback"] and event["upstream"] is not None:
        voids.append(f"steered seed {seed} fallback carries model provenance")
        return None, False
    if not event["fallback"] and event["upstream"] != ADJUDICATOR_MODEL:
        voids.append(f"steered seed {seed} ran {event['upstream']!r}, not the "
                     f"committed {ADJUDICATOR_MODEL!r}")
        return None, False
    if _herring_from_log(row, "steered", seed) != event["selected"]:
        voids.append(f"steered seed {seed} event disagrees with referee outcome")
        return None, False
    return event, event["fallback"]


def _compliance(control: ArmRead, steered: ArmRead,
                voids: list[str]) -> tuple[int, int, int, int]:
    """(steered hits, steered scored calls, control hits, control calls).

    A fallback is the seeded menu wearing the model's label, so it leaves the
    numerator AND the denominator - and its paired control call goes with it, so
    both rates keep exactly the same support.
    """
    expected_seeds = set(range(FIRST_SEED, LAST_SEED + 1))
    for label, read in (("control", control), ("steered", steered)):
        duplicates = _duplicate_seeds(read)
        if duplicates:
            voids.append(f"{label} duplicate game seed(s): "
                         + ", ".join(map(str, duplicates)))
        missing = sorted(expected_seeds - set(read.seed_rows))
        outside = sorted(set(read.seed_rows) - expected_seeds)
        if missing:
            voids.append(
                f"{label} has {len(missing)} missing promised game seed(s)")
        if outside:
            voids.append(f"{label} has game seed(s) outside "
                         f"{FIRST_SEED}..{LAST_SEED}")

    steered_hits = steered_calls = control_hits = control_calls = 0
    paired = expected_seeds & set(control.seed_rows) & set(steered.seed_rows)
    for seed in sorted(paired):
        control_row, steered_row = control.seed_rows[seed], steered.seed_rows[seed]
        expected_deal, options, preferred, random_selected = _expected(seed)
        if _normal_deal(control_row, "control", seed) != expected_deal:
            voids.append(f"control reconstruction failed at game seed {seed}")
            continue
        if _normal_deal(steered_row, "steered", seed) != expected_deal:
            voids.append(f"paired deals differ at game seed {seed}")
            continue
        if _herring_from_log(control_row, "control", seed) != random_selected:
            voids.append(f"control reconstruction failed at game seed {seed}")
            continue
        expected_call = random_selected is not None
        event, fell_back = _steered_event(
            steered_row, seed, options, expected_call, voids)
        if not expected_call:
            continue
        if len(options) != MENU_SIZE:
            voids.append(f"game seed {seed} offers {len(options)} options, not "
                         f"{MENU_SIZE}: chance is not 1/{MENU_SIZE} on this deal")
            continue
        if event is None or fell_back:
            continue
        steered_calls += 1
        steered_hits += event["selected"] == preferred
        control_calls += 1
        control_hits += random_selected == preferred
    return steered_hits, steered_calls, control_hits, control_calls


def report(control_evidence, steered_evidence, *,
           control_args: dict = CONTROL_ARGS, model_args: dict = STEERED_ARGS,
           criterion_path: str = CRITERION_DOC) -> tuple[list[str], int]:
    """Return the steered-discretion read and its stable controller exit code."""
    out = [
        "belfry steered discretion - pre-committed rule-application arm",
        f"criterion: {criterion_path} (pre-committed, not editable)",
        f"rule: {HERRING_STEER_RULE}",
    ]
    try:
        control = _read_arm(control_evidence, "control")
        steered = _read_arm(steered_evidence, "steered")
    except (EvidenceError, KeyError, TypeError, ValueError) as exc:
        out += ["", f"instrument control DISAGREES: {exc}",
                "no verdict: the summary and raw evidence must agree first"]
        return out, 1

    out += ["", "instrument control - summaries against their JSONL rows",
            "  both published integrity strata reproduce from raw rows"]
    mismatches = (_recipe_mismatches(control, control_args, "control")
                  + _recipe_mismatches(steered, model_args, "steered"))
    if mismatches:
        out += ["", "criterion binding"]
        out += [f"  NOT this criterion: {mismatch}" for mismatch in mismatches]
        return out, 3

    out += ["", "fallback rates - independent denominators",
            f"  control player fallback: "
            f"{_fmt_rate(control.fallbacks, control.decisions)}",
            "  control adjudicator fallback: n/a (random control makes no calls)",
            f"  steered player fallback: "
            f"{_fmt_rate(steered.fallbacks, steered.decisions)}",
            f"  steered adjudicator fallback: "
            f"{_fmt_rate(steered.adjudicator_fallbacks, steered.adjudicator_calls)}",
            f"  steered adjudicator recovered: "
            f"{_fmt_rate(steered.adjudicator_recovered, steered.adjudicator_calls)}",
            f"  adjudicator route: local {ADJUDICATOR_MODEL}, temperature "
            f"{ADJUDICATOR_TEMPERATURE:.1f} fixed by the driver",
            "  cost of steering: read beside S8b's blind 0/20 = 0.00%. A richer "
            "ask that breaks the parse is the first thing this arm can buy, and "
            "the void bar catches it either way"]

    voids: list[str] = []
    for label, read in (("control", control), ("steered", steered)):
        if read.played < GAMES_PROMISED:
            voids.append(f"{label} played {read.played}/{GAMES_PROMISED} "
                         "promised games")
        if any(row.get("error") for row in read.rows):
            voids.append(f"{label} contains an errored game")
        if read.player_fallback_rate > FALLBACK_CEILING:
            voids.append(f"{label} player fallback rate "
                         f"{read.player_fallback_rate:.2%} is above "
                         f"{FALLBACK_CEILING:.0%}")
    if control.adjudicator_calls:
        voids.append("control contains adjudicator calls; its rate must be n/a")
    steered_rate = steered.adjudicator_fallback_rate
    if steered_rate is None:
        voids.append("steered arm has no adjudicator calls")
    elif steered_rate > FALLBACK_CEILING:
        voids.append(f"steered adjudicator fallback rate {steered_rate:.2%} is "
                     f"above {FALLBACK_CEILING:.0%}")

    try:
        hits, calls, control_hits, control_calls = _compliance(
            control, steered, voids)
    except EvidenceError as exc:
        out += ["", f"instrument control DISAGREES: {exc}"]
        return out, 1
    if not voids and not calls:
        voids.append("no scored steered call survived; there is nothing to read")
    if voids:
        out += ["", "void conditions, pre-committed"]
        out += [f"  VOID: {reason}" for reason in voids]
        return out, 2

    # The seeded-random arm plays the same boards against the same rule. It has
    # no rule to follow, so its compliance IS the chance rate - and if it lands
    # outside its own interval the rule is not chance-neutral on these deals, so
    # no steered number above that bar would mean anything.
    control_band = wilson(control_calls // MENU_SIZE, control_calls)
    control_rate = control_hits / control_calls
    if not control_band[0] <= control_rate <= control_band[1]:
        out += ["", "void conditions, pre-committed",
                f"  VOID: control complied {control_hits}/{control_calls} = "
                f"{control_rate:.2%}, outside its own chance interval "
                f"[{control_band[0]:.2%}, {control_band[1]:.2%}]: the rule is not "
                f"chance-neutral on these deals"]
        return out, 2

    chance = wilson(calls // MENU_SIZE, calls)
    rate = hits / calls
    verdict = "STEERED" if rate > chance[1] else "NOT SHOWN"
    out += ["", "rule application on dealt boards",
            f"  {calls} scored steered calls after dropping fallback pairs",
            f"  menu of {MENU_SIZE}, offered in a seeded order: chance is "
            f"1/{MENU_SIZE} for any fixed seat-index or list-position prior",
            f"  control compliance: {control_hits}/{control_calls} = "
            f"{control_rate:.2%} (instrument control, inside its chance interval)",
            f"  chance interval: [{chance[0]:.2%}, {chance[1]:.2%}] "
            f"(Wilson 95% at {calls // MENU_SIZE}/{calls})",
            f"  steered compliance: {hits}/{calls} = {rate:.2%}",
            f"  VERDICT: {verdict}",
            "  this tests whether bounded setup discretion follows a stated rule "
            "given the board, not whether the rule is good refereeing, and not "
            "quality, wins, deduction, or general referee performance"]
    return out, 0


def resolve(argv: list[str] | None = None) -> tuple[dict, Path, Path]:
    """The arm one invocation binds, and the two record paths that come with it."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--criterion", choices=sorted(ARMS), default="s23",
                        help="which pre-committed arm to bind (default s23)")
    parser.add_argument("control", nargs="?", help="control campaign summary")
    parser.add_argument("model", nargs="?", help="steered campaign summary")
    args = parser.parse_args(argv)
    arm = ARMS[args.criterion]
    return (arm, Path(args.control or arm["control"]),
            Path(args.model or arm["model"]))


def main(argv: list[str] | None = None) -> int:
    arm, control_path, model_path = resolve(argv)
    lines, code = report(load(control_path), load(model_path),
                         control_args=arm["control_args"],
                         model_args=arm["model_args"],
                         criterion_path=arm["doc"])
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    sys.exit(main())
