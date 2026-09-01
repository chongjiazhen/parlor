"""Apply Belfry's pre-committed paired model-adjudicator criterion.

The raw per-game rows are the evidence. Their summaries are an independent
instrument control, and the paired random arm is replayed from its seeds before
any source-discrimination number is read.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from core.stats import wilson
from games.belfry.roles import Align, COMPACT
from games.belfry.state import deal


CONTROL_CAMPAIGN = "eval/records/belfry-adjudicator-control.json"
MODEL_CAMPAIGN = "eval/records/belfry-adjudicator-model.json"
V2_CONTROL_CAMPAIGN = "eval/records/belfry-adjudicator-v2-control.json"
V2_MODEL_CAMPAIGN = "eval/records/belfry-adjudicator-v2-model.json"
GAMES_PROMISED = 60
FIRST_SEED = 6100
LAST_SEED = 6159
FALLBACK_CEILING = 0.10
ADJUDICATOR_TEMPERATURE = 0.0
ADJUDICATOR_MODEL = "qwen36-35b-a3b-iq3"

COMMON_ARGS = {
    "games": GAMES_PROMISED,
    "arm": "random",
    "seats": 5,
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
    "out": CONTROL_CAMPAIGN,
}
MODEL_ARGS = {
    **COMMON_ARGS,
    "adjudicator": "model",
    "adjudicator_backend": "local",
    "adjudicator_model": ADJUDICATOR_MODEL,
    "adjudicator_temperature": ADJUDICATOR_TEMPERATURE,
    "out": MODEL_CAMPAIGN,
}
V2_CONTROL_ARGS = {**CONTROL_ARGS, "out": V2_CONTROL_CAMPAIGN}
V2_MODEL_ARGS = {**MODEL_ARGS, "out": V2_MODEL_CAMPAIGN}

# One arm's WHOLE binding - the record paths it reads, the settings it demands,
# and the document that promised them - as a single object. They are not separate
# flags on purpose: the old --v2 flag switched the expected args and not the
# default record paths, so a bare invocation loaded the v1 records and reported
# it as a criterion violation rather than as the wrong file. One binding, one
# switch, nothing that can half-move.
ARMS = {
    "v1": {
        "control": CONTROL_CAMPAIGN,
        "model": MODEL_CAMPAIGN,
        "control_args": CONTROL_ARGS,
        "model_args": MODEL_ARGS,
        "doc": "docs/belfry-adjudicator-criterion.md",
    },
    "v2": {
        "control": V2_CONTROL_CAMPAIGN,
        "model": V2_MODEL_CAMPAIGN,
        "control_args": V2_CONTROL_ARGS,
        "model_args": V2_MODEL_ARGS,
        "doc": "docs/belfry-adjudicator-v2-criterion.md",
    },
}

EVENT_FIELDS = {
    "key", "options", "selected", "fallback", "recovered", "upstream",
}
CHOICE_KEY = "herring_registration"


class EvidenceError(ValueError):
    """The files cannot support any read, independently of the arm result."""


@dataclass(frozen=True)
class Trace:
    """One bounded choice with the label and split key kept out of its feature."""

    seed: int
    source: str
    key: str
    option_count: int
    selected_index: int


@dataclass
class ArmRead:
    summary: dict
    rows: list[dict]
    decisions: int
    fallbacks: int
    played: int
    adjudicator_calls: int
    adjudicator_fallbacks: int
    adjudicator_recovered: int
    seed_rows: dict[int, dict]

    @property
    def player_fallback_rate(self) -> float:
        return self.fallbacks / self.decisions if self.decisions else 0.0

    @property
    def adjudicator_fallback_rate(self) -> float | None:
        if not self.adjudicator_calls:
            return None
        return self.adjudicator_fallbacks / self.adjudicator_calls


def feature(trace: Trace) -> tuple[str, int, int]:
    """The entire classifier input: no seed, source, upstream, or raw text."""
    return trace.key, trace.option_count, trace.selected_index


def split_traces(traces: list[Trace]) -> tuple[list[Trace], list[Trace]]:
    """Use even game seeds for training and odd game seeds for the held-out read."""
    train = [trace for trace in traces if trace.seed % 2 == 0]
    test = [trace for trace in traces if trace.seed % 2 == 1]
    train_seeds = {trace.seed for trace in train}
    test_seeds = {trace.seed for trace in test}
    if not train_seeds.isdisjoint(test_seeds):
        raise EvidenceError("a training game seed entered the held-out trace set")
    if not train or not test:
        raise EvidenceError("both training and held-out traces are required")
    return train, test


def _balanced(traces: list[Trace]) -> None:
    grouped: dict[tuple[int, str], Counter] = defaultdict(Counter)
    for trace in traces:
        if trace.source not in {"random", "model"}:
            raise EvidenceError(f"unknown source label {trace.source!r}")
        grouped[(trace.seed, trace.key)][trace.source] += 1
    for (seed, key), counts in grouped.items():
        if counts != Counter({"random": 1, "model": 1}):
            raise EvidenceError(
                f"seed {seed} choice {key} does not have one trace per source")


def held_out_accuracy(traces: list[Trace]) -> float:
    """Empirical source classification with half credit for an exact tie."""
    _balanced(traces)
    train, test = split_traces(traces)
    train_random = [trace for trace in train if trace.source == "random"]
    train_model = [trace for trace in train if trace.source == "model"]
    if len(train_random) != len(train_model):
        raise EvidenceError("classifier training labels are not balanced")
    counts_random = Counter(feature(trace) for trace in train_random)
    counts_model = Counter(feature(trace) for trace in train_model)

    points = 0.0
    for trace in test:
        item = feature(trace)
        random_p = counts_random[item] / len(train_random)
        model_p = counts_model[item] / len(train_model)
        if random_p == model_p:
            points += 0.5
        else:
            predicted = "random" if random_p > model_p else "model"
            points += float(predicted == trace.source)
    return points / len(test)


def load(path: Path) -> tuple[dict, list[dict]]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    rows_path = path.with_suffix(path.suffix + ".jsonl")
    rows = [json.loads(line) for line in
            rows_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return summary, rows


def _unpack(evidence) -> tuple[dict, list[dict]]:
    if (not isinstance(evidence, tuple) or len(evidence) != 2
            or not isinstance(evidence[0], dict)
            or not isinstance(evidence[1], list)
            or any(not isinstance(row, dict) for row in evidence[1])):
        raise EvidenceError("an arm must be a (summary, JSONL rows) tuple")
    return evidence


def _same_number(published, derived) -> bool:
    if isinstance(published, bool) or isinstance(derived, bool):
        return published == derived
    if isinstance(published, (int, float)) and isinstance(derived, (int, float)):
        return abs(published - derived) <= 1e-9
    return published == derived


def _integer(value, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise EvidenceError(f"{name} must be a non-negative integer")
    return value


def _read_arm(evidence, label: str) -> ArmRead:
    summary, rows = _unpack(evidence)
    played_rows = [row for row in rows if not row.get("error")]
    decisions = sum(_integer(row.get("decisions"), "decisions")
                    for row in played_rows)
    fallbacks = sum(_integer(row.get("fallbacks"), "fallbacks")
                    for row in played_rows)
    if fallbacks > decisions:
        raise EvidenceError(f"{label} has more player fallbacks than decisions")

    calls = adjudicator_fallbacks = recovered = 0
    upstreams: Counter = Counter()
    for row in played_rows:
        block = row.get("adjudicator")
        if block is None:
            continue
        if not isinstance(block, dict):
            raise EvidenceError(f"{label} adjudicator provenance is not an object")
        events = block.get("events")
        if not isinstance(events, list):
            raise EvidenceError(f"{label} adjudicator events are missing")
        row_calls = _integer(block.get("calls"), "adjudicator calls")
        row_fallbacks = _integer(block.get("fallbacks"), "adjudicator fallbacks")
        row_recovered = _integer(block.get("recovered"), "adjudicator recovered")
        if row_calls != len(events):
            raise EvidenceError(f"{label} adjudicator calls disagree with events")
        if any(not isinstance(event, dict) for event in events):
            raise EvidenceError(f"{label} adjudicator event is not an object")
        if row_fallbacks != sum(event.get("fallback") is True for event in events):
            raise EvidenceError(
                f"{label} adjudicator fallbacks disagree with events")
        if row_recovered != sum(event.get("recovered") is True for event in events):
            raise EvidenceError(
                f"{label} adjudicator recovered count disagrees with events")
        event_upstreams = Counter(
            event["upstream"] for event in events if event.get("upstream"))
        block_upstreams = block.get("upstreams")
        if (not isinstance(block_upstreams, dict)
                or any(not isinstance(key, str)
                       or isinstance(value, bool)
                       or not isinstance(value, int)
                       or value < 0
                       for key, value in block_upstreams.items())
                or Counter(block_upstreams) != event_upstreams):
            raise EvidenceError(
                f"{label} adjudicator upstream census disagrees with events")
        calls += row_calls
        adjudicator_fallbacks += row_fallbacks
        recovered += row_recovered
        upstreams.update(event_upstreams)

    score = summary.get("score")
    if not isinstance(score, dict):
        raise EvidenceError(f"{label} summary published no score")
    integrity = score.get("integrity")
    if not isinstance(integrity, dict):
        raise EvidenceError(f"{label} summary published no player integrity")
    checks = [
        ("requested games", score.get("games_requested"), len(rows)),
        ("played games", score.get("games_completed"), len(played_rows)),
        ("player decisions", integrity.get("decisions"), decisions),
        ("player fallbacks", integrity.get("fallbacks"), fallbacks),
        ("player fallback rate", integrity.get("fallback_rate"),
         fallbacks / decisions if decisions else 0.0),
    ]
    adj = score.get("adjudicator_integrity")
    if calls:
        if not isinstance(adj, dict):
            raise EvidenceError(f"{label} summary published no adjudicator integrity")
        checks += [
            ("adjudicator calls", adj.get("calls"), calls),
            ("adjudicator fallbacks", adj.get("fallbacks"),
             adjudicator_fallbacks),
            ("adjudicator recovered", adj.get("recovered"), recovered),
            ("adjudicator fallback rate", adj.get("fallback_rate"),
             adjudicator_fallbacks / calls),
            ("adjudicator upstream census", adj.get("upstreams"),
             dict(upstreams.most_common())),
        ]
    elif adj is not None:
        raise EvidenceError(
            f"{label} summary reports adjudicator calls absent from its rows")
    for name, published, derived in checks:
        if published is None or not _same_number(published, derived):
            raise EvidenceError(
                f"{label} {name}: summary {published!r}, rows {derived!r}")

    seed_rows: dict[int, dict] = {}
    for row in rows:
        index = _integer(row.get("index"), f"{label} row index")
        seed = FIRST_SEED + index
        if seed not in seed_rows:
            seed_rows[seed] = row
    return ArmRead(summary, rows, decisions, fallbacks, len(played_rows), calls,
                   adjudicator_fallbacks, recovered, seed_rows)


def _recipe_mismatches(read: ArmRead, expected: dict, label: str) -> list[str]:
    args = read.summary.get("args")
    if not isinstance(args, dict):
        return [f"{label} args: expected launch settings, record none"]
    out = []
    for key, want in expected.items():
        if key not in args:
            out.append(f"{label} {key}: expected {want!r}, record missing")
        elif args[key] != want:
            out.append(f"{label} {key}: expected {want!r}, record {args[key]!r}")
    return out


def _duplicate_seeds(read: ArmRead) -> list[int]:
    seeds = [FIRST_SEED + row["index"] for row in read.rows
             if isinstance(row.get("index"), int)
             and not isinstance(row.get("index"), bool)]
    return sorted(seed for seed, count in Counter(seeds).items() if count > 1)


def _normal_deal(row: dict, label: str, seed: int) -> tuple[str, ...]:
    raw = row.get("dealt")
    if not isinstance(raw, dict):
        raise EvidenceError(f"{label} seed {seed} published no deal")
    try:
        values = tuple(raw[str(seat)] if str(seat) in raw else raw[seat]
                       for seat in range(5))
    except (KeyError, TypeError) as exc:
        raise EvidenceError(f"{label} seed {seed} has an incomplete deal") from exc
    compact_keys = {role.key for role in COMPACT.roles}
    if (len(raw) != 5 or len(set(values)) != 5
            or any(role not in compact_keys for role in values)):
        raise EvidenceError(f"{label} seed {seed} has a corrupt compact deal")
    return values


def _herring_from_log(row: dict, label: str, seed: int) -> str | None:
    log = row.get("log")
    if not isinstance(log, list) or any(not isinstance(line, str) for line in log):
        raise EvidenceError(f"{label} seed {seed} has no readable referee log")
    suffix = " reads as the demon to the diviner all game"
    prefix = "discretion: seat "
    found = [line[len(prefix):-len(suffix)] for line in log
             if line.startswith(prefix) and line.endswith(suffix)]
    if len(found) > 1:
        raise EvidenceError(f"{label} seed {seed} has duplicate herring outcomes")
    return found[0] if found else None


def _expected(seed: int) -> tuple[tuple[str, ...], tuple[str, ...], str | None]:
    grim = deal(5, COMPACT, random.Random(seed))
    dealt = tuple(seat.dealt.key for seat in grim.seats)
    options = tuple(str(seat.index) for seat in grim.seats
                    if seat.align is Align.GOOD)
    selected = None if grim.find_believer("diviner") is None else str(grim.herring)
    return dealt, options, selected


def _model_trace(row: dict, seed: int, options: tuple[str, ...],
                 expected_call: bool, voids: list[str]) -> tuple[Trace | None, bool]:
    block = row.get("adjudicator")
    if not expected_call:
        if block is not None:
            voids.append(f"model seed {seed} has provenance for no legal setup call")
        return None, False
    if block is None:
        voids.append(f"model seed {seed} is missing adjudicator provenance")
        return None, False
    events = block.get("events", []) if isinstance(block, dict) else []
    if len(events) != 1 or not isinstance(events[0], dict):
        voids.append(f"model seed {seed} does not carry exactly one choice event")
        return None, False
    event = events[0]
    extra = set(event) - EVENT_FIELDS
    if extra:
        voids.append(
            f"classifier input leakage at model seed {seed}: extra event field(s) "
            + ", ".join(sorted(extra)))
        return None, False
    missing = EVENT_FIELDS - set(event)
    if missing:
        voids.append(
            f"model seed {seed} is missing provenance field(s) "
            + ", ".join(sorted(missing)))
        return None, False
    if event["key"] != CHOICE_KEY:
        voids.append(f"model seed {seed} carries unknown choice key {event['key']!r}")
        return None, False
    if not isinstance(event["options"], list) or tuple(event["options"]) != options:
        voids.append(f"model seed {seed} legal menu does not reconstruct")
        return None, False
    if event["selected"] not in options:
        voids.append(f"model seed {seed} selected a value outside its legal menu")
        return None, False
    if type(event["fallback"]) is not bool or type(event["recovered"]) is not bool:
        voids.append(f"model seed {seed} has non-boolean provenance flags")
        return None, False
    if event["fallback"] and event["upstream"] is not None:
        voids.append(f"model seed {seed} fallback carries model provenance")
        return None, False
    if not event["fallback"] and event["upstream"] != ADJUDICATOR_MODEL:
        voids.append(
            f"model seed {seed} ran {event['upstream']!r}, not the committed "
            f"{ADJUDICATOR_MODEL!r}")
        return None, False
    logged = _herring_from_log(row, "model", seed)
    if logged != event["selected"]:
        voids.append(f"model seed {seed} event disagrees with referee outcome")
        return None, False
    return (Trace(seed, "model", CHOICE_KEY, len(options),
                  options.index(event["selected"])), event["fallback"])


def _paired_traces(control: ArmRead, model: ArmRead,
                   voids: list[str]) -> list[Trace]:
    traces: list[Trace] = []
    fallback_pairs: set[tuple[int, str]] = set()
    expected_seeds = set(range(FIRST_SEED, LAST_SEED + 1))
    for label, read in (("control", control), ("model", model)):
        duplicates = _duplicate_seeds(read)
        if duplicates:
            voids.append(
                f"{label} duplicate game seed(s): "
                + ", ".join(map(str, duplicates)))
        missing = sorted(expected_seeds - set(read.seed_rows))
        outside = sorted(set(read.seed_rows) - expected_seeds)
        if missing:
            voids.append(f"{label} has {len(missing)} missing promised game seed(s)")
        if outside:
            voids.append(f"{label} has game seed(s) outside 6100..6159")

    paired = expected_seeds & set(control.seed_rows) & set(model.seed_rows)
    for seed in sorted(paired):
        control_row, model_row = control.seed_rows[seed], model.seed_rows[seed]
        expected_deal, options, random_selected = _expected(seed)
        control_deal = _normal_deal(control_row, "control", seed)
        model_deal = _normal_deal(model_row, "model", seed)
        if control_deal != expected_deal:
            voids.append(f"control reconstruction failed at game seed {seed}")
            continue
        if model_deal != control_deal:
            voids.append(f"paired deals differ at game seed {seed}")
            continue
        logged_random = _herring_from_log(control_row, "control", seed)
        if logged_random != random_selected:
            voids.append(f"control reconstruction failed at game seed {seed}")
            continue
        expected_call = random_selected is not None
        model_trace, fell_back = _model_trace(
            model_row, seed, options, expected_call, voids)
        if not expected_call:
            continue
        random_trace = Trace(seed, "random", CHOICE_KEY, len(options),
                             options.index(random_selected))
        traces.append(random_trace)
        if model_trace:
            traces.append(model_trace)
        if fell_back:
            fallback_pairs.add((seed, CHOICE_KEY))

    # A fallback is the random policy wearing the model's label. Remove that event
    # and its paired control event so both labels keep exactly the same support.
    return [trace for trace in traces
            if (trace.seed, trace.key) not in fallback_pairs]


def _fmt_rate(fallbacks: int, decisions: int) -> str:
    if not decisions:
        return "n/a"
    return f"{fallbacks}/{decisions} = {fallbacks / decisions:.2%}"


def report(control_evidence, model_evidence, *,
           control_args: dict = CONTROL_ARGS, model_args: dict = MODEL_ARGS,
           criterion_path: str = "docs/belfry-adjudicator-criterion.md") \
        -> tuple[list[str], int]:
    """Return the paired-arm read and its stable controller exit code."""
    out = [
        "belfry model adjudicator - paired source-discrimination arm",
        f"criterion: {criterion_path} "
        "(pre-committed, not editable)",
    ]
    try:
        control = _read_arm(control_evidence, "control")
        model = _read_arm(model_evidence, "model")
    except (EvidenceError, KeyError, TypeError, ValueError) as exc:
        out += ["", f"instrument control DISAGREES: {exc}",
                "no verdict: the summary and raw evidence must agree first"]
        return out, 1

    out += ["", "instrument control - summaries against their JSONL rows",
            "  both published integrity strata reproduce from raw rows"]
    mismatches = (_recipe_mismatches(control, control_args, "control")
                  + _recipe_mismatches(model, model_args, "model"))
    if mismatches:
        out += ["", "criterion binding"]
        out += [f"  NOT this criterion: {mismatch}" for mismatch in mismatches]
        return out, 3

    out += ["", "fallback rates - independent denominators",
            f"  control player fallback: "
            f"{_fmt_rate(control.fallbacks, control.decisions)}",
            "  control adjudicator fallback: n/a (random control makes no calls)",
            f"  model player fallback: "
            f"{_fmt_rate(model.fallbacks, model.decisions)}",
            f"  model adjudicator fallback: "
            f"{_fmt_rate(model.adjudicator_fallbacks, model.adjudicator_calls)}",
            f"  adjudicator route: local {ADJUDICATOR_MODEL}, temperature "
            f"{ADJUDICATOR_TEMPERATURE:.1f} fixed by the driver"]

    voids: list[str] = []
    for label, read in (("control", control), ("model", model)):
        if read.played < GAMES_PROMISED:
            voids.append(
                f"{label} played {read.played}/{GAMES_PROMISED} promised games")
        if any(row.get("error") for row in read.rows):
            voids.append(f"{label} contains an errored game")
        if read.player_fallback_rate > FALLBACK_CEILING:
            voids.append(
                f"{label} player fallback rate {read.player_fallback_rate:.2%} "
                f"is above {FALLBACK_CEILING:.0%}")
    if control.adjudicator_calls:
        voids.append("control contains adjudicator calls; its rate must be n/a")
    model_rate = model.adjudicator_fallback_rate
    if model_rate is None:
        voids.append("model arm has no adjudicator calls")
    elif model_rate > FALLBACK_CEILING:
        voids.append(
            f"model adjudicator fallback rate {model_rate:.2%} is above "
            f"{FALLBACK_CEILING:.0%}")

    try:
        traces = _paired_traces(control, model, voids)
        if traces and not voids:
            _balanced(traces)
    except EvidenceError as exc:
        out += ["", f"instrument control DISAGREES: {exc}"]
        return out, 1
    if voids:
        out += ["", "void conditions, pre-committed"]
        out += [f"  VOID: {reason}" for reason in voids]
        return out, 2

    try:
        accuracy = held_out_accuracy(traces)
        _, test = split_traces(traces)
    except EvidenceError as exc:
        out += ["", f"  VOID: classifier boundary failed: {exc}"]
        return out, 2
    chance = wilson(len(test) // 2, len(test))
    verdict = "DISTINGUISHABLE" if accuracy > chance[1] else "NOT SHOWN"
    out += ["", "held-out source discrimination",
            f"  {len(traces) // 2} paired legal traces after dropping model "
            f"fallback pairs",
            f"  train: even game seeds; test: odd game seeds "
            f"({len(test)} balanced labelled traces)",
            f"  chance interval: [{chance[0]:.2%}, {chance[1]:.2%}] "
            f"(Wilson 95% at {len(test) // 2}/{len(test)})",
            f"  source accuracy: {accuracy:.2%}",
            f"  VERDICT: {verdict}",
            "  this tests whether bounded setup choices differ from seeded "
            "random, not whether the model choices are better"]
    return out, 0


def resolve(argv: list[str] | None = None) -> tuple[dict, Path, Path]:
    """The arm one invocation binds, and the two record paths that come with it.

    Separated from ``main`` so the binding is testable without loading a record.
    The bug this replaced was entirely in which paths a flag resolved to, and a
    test that must read evidence off disk to see that is too expensive to exist.
    An explicitly supplied positional still wins, because the tool is also
    pointed at ad-hoc records by hand.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--criterion", choices=sorted(ARMS), default="v1",
                        help="which pre-committed arm to bind (default v1). It "
                             "switches the record paths and the expected settings "
                             "together; there is no flag for one without the other")
    parser.add_argument("--v2", action="store_true",
                        help="alias for --criterion v2. Kept because "
                             "eval/runs/belfry-adjudicator-v2.cmd is a tracked "
                             "recipe and docs/slices.md cites this spelling as "
                             "the arithmetic behind a published S8b number")
    parser.add_argument("control", nargs="?", default=None)
    parser.add_argument("model", nargs="?", default=None)
    args = parser.parse_args(argv)
    arm = ARMS["v2" if args.v2 else args.criterion]
    return (arm,
            Path(args.control) if args.control else Path(arm["control"]),
            Path(args.model) if args.model else Path(arm["model"]))


def main(argv: list[str] | None = None) -> int:
    arm, control_path, model_path = resolve(argv)
    try:
        control = load(control_path)
        model = load(model_path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"missing or corrupt evidence: {exc}")
        return 1
    lines, code = report(control, model, control_args=arm["control_args"],
                         model_args=arm["model_args"], criterion_path=arm["doc"])
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    sys.exit(main())
