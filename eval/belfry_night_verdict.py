"""Apply Belfry's pre-committed night-coherence criterion.

The first arm on the axis RULES §Discretion calls "per-query discretion": the
false neighbour count a switched-off gauge is told, chosen by the model referee
at play time with the seat's prior tellings in view. The rung's own stated
position is that a lie is worth something only if its owner can build one
consistent story on it, so the gradable question is whether the referee HOLDS
the lie across nights while the seat's living neighbours are unchanged.

The unit is a PAIR of consecutive false tellings to one seat over the same
neighbours. The true count is the same on both nights (it is a function of the
neighbours), the menu is the two other counts, and the previous false count is
always one of them - so chance is exactly one half per pair, whatever the deal.
The control arm's own coherence is the chance-neutrality control: seeded random
must sit at one half, or the instrument is reading something other than the
choice. `docs/belfry-night-coherence-criterion.md` is the binding promise.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from core.stats import bootstrap_ci, wilson

CONTROL_CAMPAIGN = "eval/records/belfry-night-control.json"
MODEL_CAMPAIGN = "eval/records/belfry-night-model.json"
CRITERION_DOC = "docs/belfry-night-coherence-criterion.md"
GAMES_PROMISED = 1000
FIRST_SEED = 12000
LAST_SEED = 12999
SEATS = 9
SCRIPT = "compact"
ADJUDICATOR_MODEL = "qwen36-35b-a3b-iq3"
FALLBACK_CEILING = 0.10
#: Two false counts on offer, the previous one always among them.
CHANCE = 0.5
#: The control's coherence must sit inside its own interval around CHANCE
#: within this tolerance, or the instrument is suspect.
CONTROL_TOLERANCE = 0.0

COMMON_ARGS = {
    "games": GAMES_PROMISED, "arm": "random", "seats": SEATS, "script": SCRIPT,
    "backend": None, "rounds": 1, "seed": FIRST_SEED,
}
CONTROL_ARGS = {**COMMON_ARGS, "adjudicator": "random",
                "adjudicator_night": False}
MODEL_ARGS = {**COMMON_ARGS, "adjudicator": "model",
              "adjudicator_model": ADJUDICATOR_MODEL,
              "adjudicator_night": True, "adjudicator_steer": False,
              "adjudicator_night_no_prior": False,
              "adjudicator_night_transcript": False}

#: The follow-up the first criterion names in its last section: the same ask
#: with ``prior`` withheld, on its own seeds, against its own control. Bound by
#: ``docs/belfry-night-noprior-criterion.md``.
NOPRIOR_CONTROL_CAMPAIGN = "eval/records/belfry-night-noprior-control.json"
NOPRIOR_MODEL_CAMPAIGN = "eval/records/belfry-night-noprior-model.json"
NOPRIOR_CRITERION_DOC = "docs/belfry-night-noprior-criterion.md"
NOPRIOR_FIRST_SEED = 13000
NOPRIOR_LAST_SEED = 13999
NOPRIOR_COMMON_ARGS = {**COMMON_ARGS, "seed": NOPRIOR_FIRST_SEED}
NOPRIOR_CONTROL_ARGS = {**NOPRIOR_COMMON_ARGS, "adjudicator": "random",
                        "adjudicator_night": False}
NOPRIOR_MODEL_ARGS = {**NOPRIOR_COMMON_ARGS, "adjudicator": "model",
                      "adjudicator_model": ADJUDICATOR_MODEL,
                      "adjudicator_night": True, "adjudicator_steer": False,
                      "adjudicator_night_no_prior": True,
                      "adjudicator_night_transcript": False}
#: The supplied-memory read the withheld arm is held against, as published
#: 2026-09-02 (`docs/measurements.md` §belfry night coherence). A comparison
#: to a point estimate would read noise as a gap; the call is on intervals.
SUPPLIED_COHERENT = 152
SUPPLIED_PAIRS = 163

#: The session-memory arm the withheld criterion's last section names: the
#: withheld ask carrying the referee's own transcript of the game so far. Bound
#: by ``docs/belfry-night-transcript-criterion.md``; held against BOTH
#: published reads on intervals.
TRANSCRIPT_CONTROL_CAMPAIGN = "eval/records/belfry-night-transcript-control.json"
TRANSCRIPT_MODEL_CAMPAIGN = "eval/records/belfry-night-transcript-model.json"
TRANSCRIPT_CRITERION_DOC = "docs/belfry-night-transcript-criterion.md"
TRANSCRIPT_FIRST_SEED = 15000
TRANSCRIPT_LAST_SEED = 15999
TRANSCRIPT_COMMON_ARGS = {**COMMON_ARGS, "seed": TRANSCRIPT_FIRST_SEED}
TRANSCRIPT_CONTROL_ARGS = {**TRANSCRIPT_COMMON_ARGS, "adjudicator": "random",
                           "adjudicator_night": False}
TRANSCRIPT_MODEL_ARGS = {**TRANSCRIPT_COMMON_ARGS, "adjudicator": "model",
                         "adjudicator_model": ADJUDICATOR_MODEL,
                         "adjudicator_night": True, "adjudicator_steer": False,
                         "adjudicator_night_no_prior": True,
                         "adjudicator_night_transcript": True}
#: The withheld read, as published 2026-09-02 (`docs/measurements.md`
#: §belfry night coherence, prior WITHHELD) - the floor the transcript arm
#: has to clear to show the channel carried anything.
WITHHELD_COHERENT = 94
WITHHELD_PAIRS = 122

ARMS = {
    "supplied": {
        "title": "play-time discretion arm, prior supplied",
        "control": CONTROL_CAMPAIGN, "model": MODEL_CAMPAIGN,
        "control_args": CONTROL_ARGS, "model_args": MODEL_ARGS,
        "doc": CRITERION_DOC,
        "first_seed": FIRST_SEED, "last_seed": LAST_SEED,
        "compare_to_supplied": False,
    },
    "withheld": {
        "title": "play-time discretion arm, prior WITHHELD",
        "control": NOPRIOR_CONTROL_CAMPAIGN, "model": NOPRIOR_MODEL_CAMPAIGN,
        "control_args": NOPRIOR_CONTROL_ARGS, "model_args": NOPRIOR_MODEL_ARGS,
        "doc": NOPRIOR_CRITERION_DOC,
        "first_seed": NOPRIOR_FIRST_SEED, "last_seed": NOPRIOR_LAST_SEED,
        "compare_to_supplied": True,
        "supplied_labels": ("NEEDS MEMORY", "HOLDS UNAIDED"),
    },
    "transcript": {
        "title": "play-time discretion arm, prior WITHHELD, own transcript",
        "control": TRANSCRIPT_CONTROL_CAMPAIGN,
        "model": TRANSCRIPT_MODEL_CAMPAIGN,
        "control_args": TRANSCRIPT_CONTROL_ARGS,
        "model_args": TRANSCRIPT_MODEL_ARGS,
        "doc": TRANSCRIPT_CRITERION_DOC,
        "first_seed": TRANSCRIPT_FIRST_SEED, "last_seed": TRANSCRIPT_LAST_SEED,
        "compare_to_supplied": True,
        "supplied_labels": ("BELOW SUPPLIED", "AS GOOD AS SUPPLIED"),
        "compare_to_withheld": True,
    },
}


class EvidenceError(ValueError):
    """The files cannot support any read, independently of the arm result."""


@dataclass(frozen=True)
class Pair:
    game: int
    seat: int
    night: int
    previous: int
    told: int

    @property
    def coherent(self) -> bool:
        return self.told == self.previous


def coherence_pairs(rows: list[dict], game: int = 0) -> list[Pair]:
    """The gradable pairs in one game's `gauge_told`: a false telling whose
    immediately previous telling to the same seat was false and counted over the
    same living neighbours. A truthful telling on either side, or a table that
    changed between them, is not a pair - the first has no lie to hold, the
    second no obligation to hold it."""
    by_seat: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        by_seat[int(row["seat"])].append(row)
    out: list[Pair] = []
    for seat, tellings in by_seat.items():
        tellings.sort(key=lambda r: int(r["night"]))
        for prev, cur in zip(tellings, tellings[1:]):
            if prev["truthful"] or cur["truthful"]:
                continue
            if list(prev["neighbours"]) != list(cur["neighbours"]):
                continue
            # A fallback is the seeded menu wearing the model's name, so it
            # leaves the denominator (S23's rule). The PREVIOUS telling stays
            # whoever chose it: it is what the seat holds.
            if cur.get("source") == "fallback":
                continue
            out.append(Pair(game, seat, int(cur["night"]),
                            int(prev["count"]), int(cur["count"])))
    return out


@dataclass(frozen=True)
class Read:
    games: int
    decisions: int
    fallbacks: int
    tellings: int
    false_tellings: int
    sources: dict[str, int]
    pairs: int
    coherent: int
    wilson: tuple[float, float] | None
    bootstrap: tuple[float, float] | None

    @property
    def rate(self) -> float | None:
        return self.coherent / self.pairs if self.pairs else None

    @property
    def fallback_rate(self) -> float:
        return self.fallbacks / self.decisions if self.decisions else 0.0


def coherence_read(rows: list[dict]) -> Read:
    """One arm's coherence, floored twice: Wilson over pairs and a bootstrap
    over GAMES, because pairs inside one game share a deal and a poisoner."""
    played = [r for r in rows if not r.get("error")]
    per_game: list[list[Pair]] = []
    tellings = false_tellings = 0
    sources: Counter = Counter()
    for row in played:
        if "gauge_told" not in row:
            raise ValueError(f"game {row.get('index')} carries no gauge_told "
                             "field: this record predates the instrument and "
                             "cannot be read by it")
        told = row["gauge_told"]
        tellings += len(told)
        false_tellings += sum(1 for t in told if not t["truthful"])
        sources.update(t["source"] for t in told if not t["truthful"])
        per_game.append(coherence_pairs(told, int(row.get("index", 0))))
    pairs = [p for game in per_game for p in game]
    coherent = sum(p.coherent for p in pairs)
    units = [g for g in per_game if g]

    def stat(sample):
        flat = [p for g in sample for p in g]
        return sum(p.coherent for p in flat) / len(flat) if flat else None

    return Read(
        games=len(played),
        decisions=sum(int(r.get("decisions", 0)) for r in played),
        fallbacks=sum(int(r.get("fallbacks", 0)) for r in played),
        tellings=tellings, false_tellings=false_tellings,
        sources=dict(sources), pairs=len(pairs), coherent=coherent,
        wilson=wilson(coherent, len(pairs)),
        bootstrap=bootstrap_ci(units, stat) if units else None,
    )


def verdict(control: Read, model: Read) -> str:
    """The criterion's four outcomes. Both floors must clear CHANCE for
    COHERENT; the control must contain CHANCE or the instrument is suspect."""
    if control.wilson is None or not (control.wilson[0] - CONTROL_TOLERANCE
                                      <= CHANCE
                                      <= control.wilson[1] + CONTROL_TOLERANCE):
        return "INSTRUMENT SUSPECT"
    if model.wilson is None or model.bootstrap is None:
        return "NO VERDICT"
    if model.wilson[0] > CHANCE and model.bootstrap[0] > CHANCE:
        return "COHERENT"
    return "NOT SHOWN"


def load(path: Path) -> tuple[dict, list[dict]]:
    import json
    summary = json.loads(path.read_text(encoding="utf-8"))
    rows_path = path.with_suffix(path.suffix + ".jsonl")
    rows = [json.loads(line) for line in
            rows_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return summary, rows


def _recipe_voids(summary: dict, rows: list[dict], expected: dict,
                  label: str, arm: dict) -> list[str]:
    voids = []
    args = summary.get("args", {})
    for key, want in expected.items():
        # A boolean flag absent from the recorded args is a flag that did not
        # exist when the record was taken, and a flag that did not exist was
        # off. The supplied-memory record predates the withholding flag; a
        # binding that read its absence as a mismatch would void a published
        # read over a setting that could not have been on.
        got = args.get(key, False if want is False else None)
        if got != want:
            voids.append(f"{label}: launch setting {key}={got!r}, criterion "
                         f"promised {want!r}")
    first, last = arm["first_seed"], arm["last_seed"]
    seeds = [first + int(r["index"]) for r in rows]
    if sorted(seeds) != list(range(first, last + 1)):
        voids.append(f"{label}: {len(rows)} rows do not cover seeds "
                     f"{first}..{last} exactly once")
    if any(r.get("error") for r in rows):
        voids.append(f"{label}: carries an errored game")
    return voids


def _adjudicator_voids(rows: list[dict]) -> tuple[list[str], dict]:
    calls = fallbacks = recovered = 0
    upstreams: Counter = Counter()
    voids = []
    for row in rows:
        block = row.get("adjudicator")
        if block is None:
            continue
        calls += block["calls"]
        fallbacks += block["fallbacks"]
        recovered += block.get("recovered", 0)
        for event in block["events"]:
            if event["key"] != "gauge_false_count":
                continue
            if not event["fallback"] and event["upstream"] != ADJUDICATOR_MODEL:
                voids.append(f"game {row['index']}: a gauge choice served by "
                             f"{event['upstream']!r}, not {ADJUDICATOR_MODEL}")
            if event["fallback"] and event["upstream"] is not None:
                voids.append(f"game {row['index']}: a fallback carries "
                             f"provenance")
        night_events = sum(1 for e in block["events"]
                           if e["key"] == "gauge_false_count")
        false_told = sum(1 for t in row.get("gauge_told", ())
                         if not t["truthful"])
        if night_events != false_told:
            voids.append(f"game {row['index']}: {night_events} gauge choice "
                         f"events against {false_told} false tellings")
    rate = fallbacks / calls if calls else 0.0
    if rate > FALLBACK_CEILING:
        voids.append(f"adjudicator fallback {fallbacks}/{calls} = {rate:.2%} "
                     f"is above the {FALLBACK_CEILING:.0%} void bar")
    return voids, {"calls": calls, "fallbacks": fallbacks,
                   "recovered": recovered, "rate": rate,
                   "upstreams": dict(upstreams)}


def supplied_call(model: Read, arm: dict = ARMS["withheld"]) -> str | None:
    """An arm against the published supplied-memory read, on intervals. The
    arm's first label when the whole Wilson interval sits below the supplied
    read's lower endpoint; its second when the intervals touch or the arm sits
    above; None with no pair to grade."""
    if model.wilson is None:
        return None
    below, other = arm["supplied_labels"]
    supplied_low, _ = wilson(SUPPLIED_COHERENT, SUPPLIED_PAIRS)
    _, arm_high = model.wilson
    return below if arm_high < supplied_low else other


def unaided_call(model: Read) -> str | None:
    """The withheld arm's line: NEEDS MEMORY or HOLDS UNAIDED."""
    return supplied_call(model, ARMS["withheld"])


def recall_call(model: Read) -> str | None:
    """The transcript arm against the published withheld read, on intervals.
    RECALLS when the whole Wilson interval sits above the withheld read's
    upper endpoint - the channel carried something the model used; NO RECALL
    when the intervals touch or the arm sits below; None with no pair."""
    if model.wilson is None:
        return None
    _, withheld_high = wilson(WITHHELD_COHERENT, WITHHELD_PAIRS)
    arm_low, _ = model.wilson
    return "RECALLS" if arm_low > withheld_high else "NO RECALL"


def _ci(ci) -> str:
    return "n/a" if ci is None else f"[{ci[0]:.2%}, {ci[1]:.2%}]"


def report(control_evidence, model_evidence,
           arm: dict = ARMS["supplied"]) -> tuple[list[str], int]:
    """The paired read and its exit code: 0 read, 3 refused or void. A refused
    record is still audited - the arithmetic prints below the refusal."""
    out = [f"belfry night coherence - {arm['title']}",
           f"criterion: {arm['doc']} (pre-committed, not editable)"]
    c_summary, c_rows = control_evidence
    m_summary, m_rows = model_evidence
    voids = _recipe_voids(c_summary, c_rows, arm["control_args"], "control", arm)
    voids += _recipe_voids(m_summary, m_rows, arm["model_args"], "model", arm)
    adj_voids, adj = _adjudicator_voids(m_rows)
    voids += adj_voids
    control = coherence_read(c_rows)
    model = coherence_read(m_rows)
    for label, read in (("control", control), ("model", model)):
        if read.fallback_rate > FALLBACK_CEILING:
            voids.append(f"{label}: player fallback {read.fallback_rate:.2%} "
                         f"is above the void bar")
    for label, read in (("control", control), ("model", model)):
        out += [
            "",
            f"{label}: {read.games} games, player fallback "
            f"{read.fallbacks}/{read.decisions} = {read.fallback_rate:.2%}",
            f"  gauge tellings {read.tellings}, false {read.false_tellings}, "
            f"sources {read.sources}",
            f"  pairs {read.pairs}, coherent {read.coherent}"
            + (f" = {read.rate:.2%}" if read.rate is not None else ""),
            f"  Wilson {_ci(read.wilson)}  bootstrap-by-game "
            f"{_ci(read.bootstrap)}",
        ]
    out += ["",
            f"adjudicator: {adj['fallbacks']}/{adj['calls']} fell back "
            f"({adj['rate']:.2%}), recovered {adj['recovered']}",
            f"chance per pair: {CHANCE:.2%} exactly (two options, the previous "
            f"count always one of them)"]
    call = verdict(control, model)
    if arm.get("compare_to_withheld"):
        withheld = wilson(WITHHELD_COHERENT, WITHHELD_PAIRS)
        out += ["", f"against the withheld read "
                f"{WITHHELD_COHERENT}/{WITHHELD_PAIRS} = "
                f"{WITHHELD_COHERENT / WITHHELD_PAIRS:.2%} {_ci(withheld)}: "
                f"{recall_call(model) or 'no pair to compare'}"]
    if arm["compare_to_supplied"]:
        supplied = wilson(SUPPLIED_COHERENT, SUPPLIED_PAIRS)
        out += ["", f"against the supplied-memory read "
                f"{SUPPLIED_COHERENT}/{SUPPLIED_PAIRS} = "
                f"{SUPPLIED_COHERENT / SUPPLIED_PAIRS:.2%} {_ci(supplied)}: "
                f"{supplied_call(model, arm) or 'no pair to compare'}"]
    if voids:
        out += ["", "VOID - the record is refused:"] + [f"  {v}" for v in voids]
        out += ["", f"arithmetic below the refusal: {call}"]
        return out, 3
    out += ["", f"verdict: {call}"]
    return out, 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--criterion", choices=sorted(ARMS), default="supplied",
                    help="which pre-committed arm to bind (default supplied, "
                         "the 2026-09-02 read; withheld is the memory arm; "
                         "transcript is the session-memory arm)")
    ap.add_argument("control", nargs="?")
    ap.add_argument("model", nargs="?")
    args = ap.parse_args(argv)
    arm = ARMS[args.criterion]
    control_path = Path(args.control or arm["control"])
    model_path = Path(args.model or arm["model"])
    try:
        lines, rc = report(load(control_path), load(model_path), arm)
    except (OSError, ValueError) as exc:
        print(f"refused: {exc}")
        return 3
    print("\n".join(lines))
    return rc


if __name__ == "__main__":
    sys.exit(main())
