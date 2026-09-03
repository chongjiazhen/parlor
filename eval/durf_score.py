"""Score a model adjudicator against the labelled DURF fixture.

``games/durf/fixtures/`` is the instrument, labelled 2026-08-27 before any model
ran. This is the scorer it was built for: it asks one arm to rule on all 48
declarations and all 12 morale events, and reports the three quantities
``docs/durf-rung.md`` pre-committed to - False Pass, False Check, Refusal - each
beside the run's fallback rate, voided above it.

**What this measures, and the sentence to quote instead of a wider one.** Three of
the adjudicator's five decisions, one item at a time, against a fixed scenario. It
is not a session, there is no engine, no kernel executes anything, and **no player
seat exists - so gate #1 is not exercised and no number here says anything about
the leak boundary.** ``games/durf/fixture.render_scenario`` hands the adjudicator
the referee's whole view, hidden room contents included, because that is what a
referee sees. The audit arrives with the session engine.

Definitions, stated once, because every rate below is only as good as its
denominator:

- **False Pass** - the adjudicator let something through that the rules do not:
  it ruled ``no_roll`` where the labels require a roll, or granted a **trap** at
  all (as a roll or as an automatic success). Denominator: the 26 roll-required
  declarations plus the 6 traps. The two trap sub-counts are reported apart,
  because granting a trap outright is a worse failure than calling for a roll on
  one, and pooling them hides which happened.
- **False Check** - it demanded a roll on one of the 16 declarations that require
  none and are not traps.
- **Over-refusal** - it ruled ``illegal`` on a declaration the rules permit. Not
  in CoC-Seduce's pair, and it has to be counted somewhere or an arm that refuses
  everything scores a perfect False Pass rate. Denominator: the 42 non-traps.
- **Refusal** - it declined to rule, the third outcome
  ``docs/durf-rung.md`` requires be named in the denominator or not at all.
  Reported over all 48, never dropped.
- **Attribute error** - decision 1 right and decision 2 wrong: it called for a
  roll where one was due and named the wrong governing attribute. Scored over the
  rolls it got right, since an attribute for a roll that should not happen is
  answering a question that was never reached.
- **Fallback** - no ruling parsed after the retries, so ``RandomAdjudicator``
  played it. Not a model answer at all; ``core.integrity``'s bar voids the run
  above 10%, the same constant both games void on.

**Two instrument controls, both required, both derived rather than chosen.**

- The **degenerate arms**. ``--arm always-roll`` and ``--arm never-roll`` need no
  model and reproduce the fixture README's published 61.9% / 38.1% decision-1
  accuracy over the 42 scorable declarations. A scorer that does not return those
  two numbers is wrong about its own denominator, which is why they are arms
  rather than a comment.
- The **floor tier**, and its bar is **pre-committed here, before any model has
  run, and derived rather than picked**: floor-tier decision-1 accuracy must have
  a Wilson floor clearing the better of the two degenerate baselines computed on
  *the floor tier itself*. A model that cannot beat a constant policy on the
  declarations the rules answer unambiguously is not being measured on
  adjudication, and the run is void. Derived, so a fixture edit moves the bar with
  the labels instead of leaving a stale literal behind.

The unit is a declaration, and declarations are independent items rather than
turns inside a shared deal - so the interval here is Wilson and there is no
game-clustered bootstrap. ``core.stats.bootstrap_ci`` exists for the case where
the unit is a game; importing it here would be resampling something that is not a
cluster.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from dataclasses import dataclass, field

from core import integrity
from core.backends import ENDPOINTS, Backend, api_key_from_env, require_key
from core.runlog import (RunState, claim_record, record_paths,
                         run_with_marker)
from core.stats import wilson
from games.durf import adjudicate, fixture, rules

#: What this run knows about itself, for the terminal marker. The marker says
#: "games"; this driver's unit is one fixture item, and the report says so.
RUN_STATE = RunState()

#: Outcome vocabulary. One string per item, and they partition: every item lands
#: in exactly one, which is what lets the rates below share a denominator without
#: any of them double-counting.
CORRECT = "correct"
FALSE_PASS = "false_pass"
FALSE_CHECK = "false_check"
OVER_REFUSAL = "over_refusal"
REFUSAL = "refusal"


@dataclass
class ItemRecord:
    """One fixture item, as ``core.integrity.summarise`` wants to read it.

    Carries the arena's decision-accounting fields verbatim so the integrity block
    is the shared one rather than a second implementation of a void bar. It holds
    exactly one decision, so ``clean_games`` counts clean ITEMS - the report says
    that in words rather than letting "games" be read as games.
    """
    item: str
    kind: str
    tier: str
    adversarial: bool = False
    label: dict = field(default_factory=dict)
    answer: dict = field(default_factory=dict)
    outcome: str = CORRECT
    attribute_error: bool = False
    opposed_error: bool = False
    think: str = ""
    narrate: str = ""
    decisions: int = 1
    fallbacks: int = 0
    recovered: int = 0
    refused_attempts: int = 0
    rule_refused_attempts: int = 0
    decision_log: list = field(default_factory=list)
    upstreams: dict = field(default_factory=dict)
    trace_sample: list = field(default_factory=list)
    error: str = ""


def _ask_one(arm, prompt: str, item: dict, kind: str) -> tuple[object, ItemRecord]:
    """One item through the arm, with the per-item accounting the arena keeps."""
    answer = arm.morale(prompt, item) if kind == "morale" else arm.rule(prompt, item)
    fell_back = bool(getattr(arm, "last_fell_back", False))
    refusals = int(getattr(arm, "last_refusals", 0))
    rule_refusals = int(getattr(arm, "last_rule_refusals", 0))
    served = str(getattr(arm, "last_upstream", "") or "")
    rec = ItemRecord(
        item=item["id"], kind=kind, tier=item["tier"],
        adversarial=bool(item.get("adversarial")),
        fallbacks=int(fell_back),
        recovered=int(bool(rule_refusals) and not fell_back),
        refused_attempts=refusals, rule_refused_attempts=rule_refusals,
        upstreams={served: 1} if served else {},
        trace_sample=list(getattr(arm, "trace", [])[-1:]) if refusals else [],
        think=getattr(answer, "think", ""), narrate=getattr(answer, "narrate", ""),
    )
    # `seat 0` throughout: there is one referee seat, so `witnessed` has no other
    # seat to be a rate over and `core.integrity._witnessed` returns None rather
    # than 0.00%. That is the honest answer for a one-seat run, not a gap.
    rec.decision_log.append({
        "turn": 0, "seat": 0, "phase": kind, "played": item["id"],
        "refused": str(getattr(arm, "last_refusal", "") or "") if refusals else "",
        "refusals": refusals, "rule_refusals": rule_refusals,
        "fell_back": fell_back, "served_by": served})
    return answer, rec


def grade_declaration(decl: dict, ruling: adjudicate.Ruling) -> tuple[str, bool, bool]:
    """One declaration -> (outcome, attribute_error, opposed_error).

    The traps come first because they are the only items whose correct answer is
    ``illegal``: on every other declaration ``illegal`` is an over-refusal, and on
    a trap ``roll`` and ``no_roll`` are both False Passes.
    """
    if ruling.ruling == "decline":
        return REFUSAL, False, False
    if decl["refuse"]:
        return (CORRECT if ruling.ruling == "illegal" else FALSE_PASS), False, False
    if ruling.ruling == "illegal":
        return OVER_REFUSAL, False, False
    if decl["roll"]:
        if not ruling.rolls:
            return FALSE_PASS, False, False
        return (CORRECT,
                ruling.attribute != decl["attribute"],
                bool(ruling.opposed) != bool(decl["opposed"]))
    return (CORRECT if not ruling.rolls else FALSE_CHECK), False, False


def grade_morale(event: dict, call: adjudicate.MoraleCall) -> str:
    if call.declined:
        return REFUSAL
    if call.morale == event["morale"]:
        return CORRECT
    # A missed morale moment lets the NPCs fight on when the rules-as-written
    # trigger fired: the adjudicator let the fiction pass without the check the
    # rules hand it. A called one where nothing shocked them is the over-demand.
    return FALSE_PASS if event["morale"] else FALSE_CHECK


def run_items(fx: fixture.Fixture, arm, limit: int | None = None,
              on_land=None, allow_decline: bool = True) -> list[ItemRecord]:
    """Every item through the arm, landing each one as it finishes.

    ``on_land`` is called with each record the moment it is graded, so a run that
    dies at item 40 leaves 40 items on disk rather than nothing. Same reason both
    game drivers append their JSONL per game instead of writing it at the end.
    """
    scenario_text = fixture.render_scenario(fx)
    records: list[ItemRecord] = []
    decls = fx.declarations[:limit] if limit else fx.declarations
    events = fx.morale_events[:limit] if limit else fx.morale_events
    for decl in decls:
        prompt = adjudicate.declaration_prompt(scenario_text, decl, allow_decline)
        ruling, rec = _ask_one(arm, prompt, decl, "declaration")
        rec.label = {"roll": decl["roll"], "attribute": decl["attribute"],
                     "opposed": decl["opposed"], "refuse": decl["refuse"]}
        rec.answer = {"ruling": ruling.ruling, "attribute": ruling.attribute,
                      "opposed": ruling.opposed}
        rec.outcome, rec.attribute_error, rec.opposed_error = grade_declaration(decl, ruling)
        records.append(rec)
        RUN_STATE.landed += 1
        if on_land:
            on_land(len(records) - 1, rec)
    for event in events:
        prompt = adjudicate.morale_prompt(scenario_text, event)
        call, rec = _ask_one(arm, prompt, event, "morale")
        rec.label = {"morale": event["morale"]}
        rec.answer = {"morale": call.morale}
        rec.outcome = grade_morale(event, call)
        records.append(rec)
        RUN_STATE.landed += 1
        if on_land:
            on_land(len(records) - 1, rec)
    return records


def as_line(index: int, rec: ItemRecord) -> str:
    """One JSONL line. ``decision_log`` rides along so a re-score can rebuild the
    integrity block off the record rather than off a printed rate."""
    return json.dumps({
        "index": index, "item": rec.item, "kind": rec.kind, "tier": rec.tier,
        "adversarial": rec.adversarial, "label": rec.label, "answer": rec.answer,
        "outcome": rec.outcome, "attribute_error": rec.attribute_error,
        "opposed_error": rec.opposed_error, "think": rec.think,
        "narrate": rec.narrate, "fallbacks": rec.fallbacks,
        "recovered": rec.recovered, "refused_attempts": rec.refused_attempts,
        "rule_refused_attempts": rec.rule_refused_attempts,
        "decision_log": rec.decision_log})


def _rate(hits: int, total: int) -> dict:
    return {"hits": hits, "n": total,
            "rate": hits / total if total else None,
            "ci95": wilson(hits, total)}


def degenerate_baselines(items: list[dict]) -> dict[str, float | None]:
    """The two constant policies, scored on whatever subset is handed in.

    Derived from the labels every time rather than quoted, so the floor-tier bar
    below moves with a fixture edit instead of going stale against it. A trap is
    an error for both policies: neither ever answers ``illegal``.
    """
    if not items:
        return {"always_roll": None, "never_roll": None}
    always = sum(1 for d in items if d["roll"] and not d["refuse"])
    never = sum(1 for d in items if not d["roll"] and not d["refuse"])
    return {"always_roll": always / len(items), "never_roll": never / len(items)}


def score(records: list[ItemRecord], fx: fixture.Fixture) -> dict:
    decls = [r for r in records if r.kind == "declaration"]
    morale = [r for r in records if r.kind == "morale"]
    by_id = {d["id"]: d for d in fx.declarations}

    # The denominators come from the FIXTURE, not from the records' copies of the
    # labels. Two derivations of "which declarations admit a roll answer" is how a
    # scorer comes to disagree with the README's published baseline while both
    # halves look right - so there is one, in `Fixture.scorable`, and this reads it.
    scorable_ids = {d["id"] for d in fx.scorable}
    scorable = [r for r in decls if r.item in scorable_ids]
    traps = [r for r in decls if r.item not in scorable_ids]
    needs_roll = [r for r in scorable if by_id[r.item]["roll"]]
    needs_none = [r for r in scorable if not by_id[r.item]["roll"]]

    fp_pool = needs_roll + traps
    false_pass = sum(1 for r in fp_pool if r.outcome == FALSE_PASS)
    trap_granted_roll = sum(1 for r in traps
                            if r.outcome == FALSE_PASS and r.answer.get("ruling") == "roll")
    trap_granted_auto = sum(1 for r in traps
                            if r.outcome == FALSE_PASS and r.answer.get("ruling") == "no_roll")

    ruled_rolls = [r for r in needs_roll if r.outcome == CORRECT]
    tiers = {}
    for tier in ("floor", "judgment", "trap"):
        pool = [r for r in decls if r.tier == tier]
        tiers[tier] = {
            **_rate(sum(1 for r in pool if r.outcome == CORRECT), len(pool)),
            "baselines": degenerate_baselines([by_id[r.item] for r in pool]),
        }

    adversarial = [r for r in decls if r.adversarial]
    i = integrity.summarise(records, trace_lines=6)
    floor_bar = _floor_bar(tiers["floor"])
    return {
        "fixture": {"version": fx.version, "ruleset": fx.ruleset,
                    "scenario": fx.scenario_id, "labelled": fx.labelled,
                    "attribution": rules.ATTRIBUTION,
                    "balance": fixture.balance(fx)},
        "items": len(records),
        "decision1": {
            **_rate(sum(1 for r in scorable if r.outcome == CORRECT), len(scorable)),
            "denominator": "the declarations that admit a roll/no-roll answer",
            "baselines": degenerate_baselines([by_id[r.item] for r in scorable]),
            "all48": _rate(sum(1 for r in decls if r.outcome == CORRECT), len(decls)),
        },
        "false_pass": {**_rate(false_pass, len(fp_pool)),
                       "trap_granted_as_roll": trap_granted_roll,
                       "trap_granted_outright": trap_granted_auto,
                       "traps": len(traps)},
        "false_check": _rate(sum(1 for r in needs_none if r.outcome == FALSE_CHECK),
                             len(needs_none)),
        "over_refusal": _rate(sum(1 for r in scorable if r.outcome == OVER_REFUSAL),
                              len(scorable)),
        "refusal": _rate(sum(1 for r in decls if r.outcome == REFUSAL), len(decls)),
        "decision2": {
            "attribute_error": _rate(sum(1 for r in ruled_rolls if r.attribute_error),
                                     len(ruled_rolls)),
            "opposed_error": _rate(sum(1 for r in ruled_rolls if r.opposed_error),
                                   len(ruled_rolls)),
        },
        "tiers": tiers,
        "adversarial": _rate(sum(1 for r in adversarial if r.outcome == CORRECT),
                             len(adversarial)),
        "morale": {
            **_rate(sum(1 for r in morale if r.outcome == CORRECT), len(morale)),
            "missed": sum(1 for r in morale if r.outcome == FALSE_PASS),
            "over_called": sum(1 for r in morale if r.outcome == FALSE_CHECK),
            "refused": sum(1 for r in morale if r.outcome == REFUSAL),
        },
        "floor_control": floor_bar,
        "integrity": i,
    }


def _floor_bar(floor: dict) -> dict:
    """The pre-committed instrument control, derived from the floor tier's own labels.

    Passes when the floor tier's Wilson FLOOR clears the better degenerate baseline
    on that same tier. Graded on the interval floor rather than the point estimate,
    the way every verdict in this repo is - a point estimate above a bar at n=34 is
    not a result.
    """
    baselines = [v for v in floor["baselines"].values() if v is not None]
    bar = max(baselines) if baselines else None
    ci = floor["ci95"]
    return {"bar": bar, "bar_source": "better degenerate baseline on the floor tier",
            "accuracy": floor["rate"], "ci95": ci,
            "floor": ci[0] if ci else None,
            "passes": bool(ci and bar is not None and ci[0] > bar)}


def _pct(value, width: int = 6) -> str:
    return "n/a".rjust(width) if value is None else f"{value:.2%}".rjust(width)


def _band(ci) -> str:
    return "  (CI unavailable)" if not ci else f"  [{ci[0]:.2%}, {ci[1]:.2%}]"


def report(s: dict, args, elapsed: float) -> list[str]:
    f = s["fixture"]
    vocab = "roll/no_roll/illegal" + ("" if getattr(args, "no_decline", False)
                                      else "/decline")
    out = [f"=== {s['items']} fixture items ({args.arm} arm, "
           f"backend={args.backend or 'none'}, model={args.model}, "
           f"vocabulary={vocab}) in {elapsed:.1f}s ===",
           f"fixture {f['scenario']} v{f['version']}, {f['ruleset']}, labelled "
           f"{f['labelled']}. {f['attribution']}", ""]

    i = s["integrity"]
    out += integrity.report_lines(i)
    out.append("  (the unit here is one fixture item, not a game - a 'clean game' "
               "above is one item nothing was sent back on)")
    if i["fallback_rate"] > integrity.VOID_BAR:
        out += ["", f"VOID: {i['fallback_rate']:.2%} of items fell back to the random "
                    f"adjudicator, above the {integrity.VOID_BAR:.0%} bar. No rate "
                    f"below is this model's."]
        return out

    fc = s["floor_control"]
    out += ["", "instrument control - the floor tier",
            f"  accuracy   {_pct(fc['accuracy'])}{_band(fc['ci95'])} against a "
            f"derived bar of {_pct(fc['bar'])} ({fc['bar_source']})"]
    if not fc["passes"]:
        out += ["  VOID: the floor tier's interval does not clear a constant policy on "
                "the same items. A model failing the declarations the rules answer "
                "unambiguously is not being measured on adjudication."]

    d1 = s["decision1"]
    b = d1["baselines"]
    out += ["", "decision 1 - does this need a roll",
            f"  accuracy   {_pct(d1['rate'])}{_band(d1['ci95'])} over {d1['n']} "
            f"({d1['denominator']})",
            f"  baselines  always-roll {_pct(b['always_roll'])}, never-roll "
            f"{_pct(b['never_roll'])} on the same items",
            f"  all 48     {_pct(d1['all48']['rate'])}{_band(d1['all48']['ci95'])} "
            f"(traps included, where the correct answer is a refusal)"]

    fp, fk, orf, ref = (s["false_pass"], s["false_check"], s["over_refusal"],
                        s["refusal"])
    out += ["", "the three pre-committed rates",
            f"  False Pass   {_pct(fp['rate'])}{_band(fp['ci95'])} "
            f"({fp['hits']}/{fp['n']}); of {fp['traps']} traps, "
            f"{fp['trap_granted_as_roll']} granted as a roll and "
            f"{fp['trap_granted_outright']} outright",
            f"  False Check  {_pct(fk['rate'])}{_band(fk['ci95'])} "
            f"({fk['hits']}/{fk['n']})",
            f"  Refusal      {_pct(ref['rate'])}{_band(ref['ci95'])} "
            f"({ref['hits']}/{ref['n']} declined to rule)",
            f"  over-refusal {_pct(orf['rate'])}{_band(orf['ci95'])} "
            f"({orf['hits']}/{orf['n']} legal declarations ruled illegal)"]

    d2 = s["decision2"]
    out += ["", "decision 2 - which attribute, and opposed",
            f"  wrong attribute  {_pct(d2['attribute_error']['rate'])} "
            f"({d2['attribute_error']['hits']}/{d2['attribute_error']['n']} of the "
            f"rolls it correctly called for)",
            f"  wrong opposed    {_pct(d2['opposed_error']['rate'])} "
            f"({d2['opposed_error']['hits']}/{d2['opposed_error']['n']})"]

    m = s["morale"]
    out += ["", "decision 4 - morale",
            f"  accuracy   {_pct(m['rate'])}{_band(m['ci95'])} ({m['hits']}/{m['n']}); "
            f"{m['missed']} missed, {m['over_called']} over-called, {m['refused']} "
            f"refused. A constant answer scores 50% by construction"]

    out += ["", "by tier"]
    for tier, cell in s["tiers"].items():
        out.append(f"  {tier:9s} {_pct(cell['rate'])}{_band(cell['ci95'])} "
                   f"({cell['hits']}/{cell['n']})")
    a = s["adversarial"]
    out.append(f"  {'argued':9s} {_pct(a['rate'])}{_band(a['ci95'])} "
               f"({a['hits']}/{a['n']} Pseudo-Logic declarations)")

    verdict = ("worth continuing" if (ref["rate"] or 0) <= integrity.VOID_BAR
               else "a negative result about the action channel, not a failed run")
    out += ["", f"pre-committed read: refusal at {_pct(ref['rate'])} against the "
                f"{integrity.VOID_BAR:.0%} bar - {verdict}."]
    if i["trace_sample"]:
        out += ["", "  why rulings were refused or retried:"]
        out += [f"    {line}" for line in i["trace_sample"]]
    return out


def build_backend(args) -> Backend | None:
    if args.arm != "llm":
        return None
    return Backend(
        endpoint=ENDPOINTS[args.backend], model=args.model,
        api_key=api_key_from_env(), system_prompt=rules.ADJUDICATOR_SYSTEM_PROMPT,
        temperature=args.temperature, timeout=args.timeout,
        max_tokens=args.max_tokens, seed=args.seed,
        enable_thinking=(False if args.no_thinking else None))


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", choices=list(adjudicate.ARMS), default="llm")
    ap.add_argument("--backend", choices=list(ENDPOINTS))
    ap.add_argument("--model", default="auto")
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--temperature", type=float, default=0.8)
    ap.add_argument("--max-tokens", type=int, default=1536)
    ap.add_argument("--timeout", type=float, default=120.0)
    ap.add_argument("--no-thinking", action="store_true",
                    help="ask the chat template to skip the model's reasoning pass")
    ap.add_argument("--no-decline", action="store_true",
                    help="drop `decline` from the ruling vocabulary. A MODEL-FACING "
                         "change and the pre-registered second arm - see "
                         "docs/durf-rung.md, First run")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--limit", type=int, default=None,
                    help="first N declarations and N morale events, for a smoke run. "
                         "A limited run is NOT the fixture and its rates are not "
                         "comparable to a full one")
    ap.add_argument("--out", help="write the summary here as JSON; the per-item "
                                  "JSONL is its sibling")
    args = ap.parse_args()

    if args.arm == "llm" and not args.backend:
        ap.error("--arm llm needs --backend; a live arm with no endpoint would "
                 "fall back on every item and score the random adjudicator")
    if args.backend:
        require_key(ENDPOINTS[args.backend], api_key_from_env())

    # The same door: an occupied record path is refused before an item is
    # scored, not discovered when two files disagree afterwards.
    if args.out:
        claim_record(args.out)

    fx = fixture.load()
    # Before anything is scored: the published counts, re-derived from the file.
    fixture.check_balance(fx)
    RUN_STATE.requested = (len(fx.declarations) + len(fx.morale_events)
                           if not args.limit else 2 * args.limit)

    rng = random.Random(args.seed)
    arm = adjudicate.build_arm(args.arm, backend=build_backend(args),
                               retries=args.retries, rng=rng,
                               allow_decline=not args.no_decline)

    on_land = None
    if args.out:
        def on_land(index: int, rec: ItemRecord) -> None:
            with open(record_paths(args.out)[1], "a", encoding="utf-8") as fh:
                fh.write(as_line(index, rec) + "\n")

    started = time.time()
    records = run_items(fx, arm, args.limit, on_land,
                        allow_decline=not args.no_decline)
    scored = score(records, fx)
    print("\n".join(report(scored, args, time.time() - started)))

    if args.out:
        with open(record_paths(args.out)[0], "w", encoding="utf-8") as fh:
            json.dump({"score": scored, "args": vars(args)}, fh, indent=2)
        print(f"\nwrote {record_paths(args.out)[0]}")


if __name__ == "__main__":
    sys.exit(run_with_marker(main, RUN_STATE))
