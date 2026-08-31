# Belfry Model Adjudicator Implementation Plan

> **Execution:** Follow tasks in order. Each checkbox marks one verified step.

**Goal:** Add bounded model referee for belfry setup discretion and pre-committed, non-VOID source-discrimination arm.

**Architecture:** ModelAdjudicator owns one JSON-choice adapter over existing state.Adjudicator setup seams. run_belfry constructs it independently from player policies and records own integrity stratum. New verdict controller reads paired random/model JSONL records, validates provenance and exact recipe, then evaluates held-out source discrimination.

**Tech Stack:** Python 3 stdlib, unittest, existing Backend, belfry records, core.integrity, shell launcher.

**Basis:** commit 295977c, model-adjudicator contract and arm boundary.

## Global Constraints

- Created: 2026-08-31T06:49:34Z.
- Model sees bounded legal menus only, never grimoire, player asks, or public text.
- --seed pins deal, player sampler, adjudicator sampler, and fallback selection.
- Adjudicator temperature is 0.0; player temperature stays independent.
- Gate #1 remains default-on at play_game; provenance never reaches seat ask.
- Player and adjudicator fallback rates are separate denominators.
- Criterion and launcher commit before model-referee arm launches.
- Verdict voids above 10%, not at 10%; random control's absent adjudicator rate is n/a.

---

## File structure

| File | Responsibility |
|---|---|
| games/belfry/adjudicator.py | Typed legal menu, strict JSON parse, seeded fallback, private provenance. |
| games/belfry/state.py | Precise protocol and choice-event storage on Grimoire. |
| eval/run_belfry.py | Separate adjudicator CLI/backend/record/summary path. |
| eval/belfry_adjudicator_verdict.py | Paired-arm integrity controller and held-out classifier. |
| eval/runs/belfry-adjudicator.cmd | Frozen pre-committed model/control launch recipe. |
| docs/belfry-adjudicator-criterion.md | Promise: recipe, voids, classifier, report limits. |
| games/belfry/RULES.md | Canonical scope and knowledge-model update after contract exists. |

### Task 1: Typed adjudicator adapter

**Files:**

- Create: games/belfry/adjudicator.py
- Modify: games/belfry/state.py:37-64,270-378
- Test: games/belfry/test_model_adjudicator.py

**Interfaces:**

- Consumes: Backend.complete_meta(context) -> tuple[str, str], game-local random.Random, and four Adjudicator protocol methods.
- Produces: ChoiceEvent(key: str, options: tuple[str, ...], selected: str, fallback: bool, recovered: bool, upstream: str | None) and ModelAdjudicator(backend: Backend, rng: random.Random).

- [ ] **Step 1: Write failing test**

~~~python
def test_illegal_choice_uses_seeded_menu_fallback():
    adj = ModelAdjudicator(FakeBackend('{"choice":"not-offered"}'), random.Random(9))
    assert adj.sot_belief([ROLES["witness"], ROLES["gauge"]], random.Random(4)) == ROLES["gauge"]
    assert adj.events[0].fallback is True
~~~

- [ ] **Step 2: Run test to verify it fails**

Run: py -3 -m unittest games.belfry.test_model_adjudicator -v

Expected: FAIL importing ModelAdjudicator.

- [ ] **Step 3: Write minimal implementation**

~~~python
@dataclass(frozen=True)
class ChoiceEvent:
    key: str
    options: tuple[str, ...]
    selected: str
    fallback: bool
    recovered: bool
    upstream: str | None

class ModelAdjudicator:
    def choose(self, key: str, options: list[str]) -> str:
        try:
            reply, upstream = self.backend.complete_meta(
                json.dumps({"choice_key": key, "options": options}))
            parsed = json.loads(reply)
            if (type(parsed) is not dict or set(parsed) != {"choice"}
                    or type(parsed["choice"]) is not str
                    or parsed["choice"] not in options):
                raise ValueError("reply did not select one offered option")
            selected, fallback = parsed["choice"], False
        except Exception:
            selected, upstream, fallback = self.rng.choice(options), None, True
        self.events.append(ChoiceEvent(key, tuple(options), selected, fallback,
                                       False, upstream))
        return selected
~~~

Implement all four protocol methods by translating roles/seats to strings and back. Store events on Grimoire.adjudicator_events after each call. Do not expose backend reply text.

- [ ] **Step 4: Run tests to verify pass**

Run: py -3 -m unittest games.belfry.test_model_adjudicator games.belfry.test_adjudicator games.belfry.test_adjudicator_integration -v

Expected: PASS; malformed, extra-key, non-string, transport, and illegal outputs fall back reproducibly.

- [ ] **Step 5: Commit**

~~~text
git add games/belfry/adjudicator.py games/belfry/state.py games/belfry/test_model_adjudicator.py
git commit -m "feat(belfry): add bounded model adjudicator"
~~~

### Task 2: Separate driver integrity and records

**Files:**

- Modify: eval/run_belfry.py:40-120,200-350
- Modify: games/belfry/player.py:GameRecord
- Test: eval/test_run_belfry_adjudicator.py
- Test: eval/test_run_belfry.py

**Interfaces:**

- Consumes: ModelAdjudicator, ChoiceEvent, game seed computed by one_game.
- Produces: optional record field adjudicator={"calls": int, "fallbacks": int, "recovered": int, "events": list[dict], "upstreams": dict[str, int]}.

- [ ] **Step 1: Write failing tests**

~~~python
def test_model_adjudicator_uses_game_seed_not_run_seed():
    args = make_args(adjudicator="model", seed=6100)
    assert build_adjudicator(args, 6100).backend.seed == 6100
    assert build_adjudicator(args, 6101).backend.seed == 6101

def test_score_keeps_adjudicator_fallback_out_of_player_integrity():
    summary = score([record_with_adjudicator(fallbacks=1, calls=4)])
    assert summary["integrity"]["fallbacks"] == 0
    assert summary["adjudicator_integrity"]["fallback_rate"] == 0.25
~~~

- [ ] **Step 2: Run tests to verify failure**

Run: py -3 -m unittest eval.test_run_belfry_adjudicator eval.test_run_belfry -v

Expected: FAIL because no model-adjudicator config or independent summary exists.

- [ ] **Step 3: Write minimal implementation**

~~~python
ap.add_argument("--adjudicator", choices=("random", "model"), default="random")
ap.add_argument("--adjudicator-backend", choices=tuple(ENDPOINTS))
ap.add_argument("--adjudicator-model")

def build_adjudicator(args, seed):
    if args.adjudicator == "random":
        return None
    return ModelAdjudicator(build_adjudicator_backend(args, seed), random.Random(seed))
~~~

Require adjudicator backend/model only for model. Set its backend temperature 0.0 and preserve player options untouched. Serialize events through asdict in each game row. Keep legacy rows readable by returning None for absent stratum.

- [ ] **Step 4: Run tests to verify pass**

Run: py -3 -m unittest eval.test_run_belfry_adjudicator eval.test_run_belfry -v

Expected: PASS; random arm has no adjudicator calls and model arm has separate counts.

- [ ] **Step 5: Commit**

~~~text
git add eval/run_belfry.py games/belfry/player.py eval/test_run_belfry_adjudicator.py eval/test_run_belfry.py
git commit -m "feat(eval): record belfry adjudicator integrity"
~~~

### Task 3: Private-channel audit regression

**Files:**

- Modify: games/belfry/test_model_adjudicator.py
- Modify: games/belfry/test_adjudicator_integration.py

**Interfaces:**

- Consumes: fixed legal ModelAdjudicator and BelfryReferee.new.
- Produces: proof choice provenance stays absent from player prompts and unchanged gate #1 audit inputs.

- [ ] **Step 1: Write failing test**

~~~python
def test_model_choice_provenance_never_reaches_player_prompt():
    ref = referee_with_fixed_model_adjudicator()
    payloads = capture_all_prompt_for(ref)
    assert all("adjudicator" not in payload.lower() for payload in payloads)
    assert ref.grim.adjudicator_events
~~~

- [ ] **Step 2: Run test to verify failure**

Run: py -3 -m unittest games.belfry.test_model_adjudicator -v

Expected: FAIL until capture seam and private event handling are complete.

- [ ] **Step 3: Write minimal containment implementation**

Keep events on Grimoire only. Do not append them to events, speech, SeatView, or prompt builder. Preserve existing play_game assertion path.

- [ ] **Step 4: Run regression tests**

Run: py -3 -m unittest games.belfry.test_model_adjudicator games.belfry.test_adjudicator_integration games.belfry.test_referee -v

Expected: PASS; normal prompt/audit fixtures remain byte-identical.

- [ ] **Step 5: Commit**

~~~text
git add games/belfry/test_model_adjudicator.py games/belfry/test_adjudicator_integration.py
git commit -m "test(belfry): guard adjudicator provenance channel"
~~~

### Task 4: Pre-committed paired-arm verdict controller

**Files:**

- Create: eval/belfry_adjudicator_verdict.py
- Create: eval/test_belfry_adjudicator_verdict.py
- Create: docs/belfry-adjudicator-criterion.md

**Interfaces:**

- Consumes: random/model summary plus JSONL rows with optional adjudicator blocks.
- Produces: report(control, model) -> tuple[list[str], int], returning 0 for non-VOID read, 2 for stated void, 3 for recipe mismatch, and 1 for missing/corrupt evidence.

- [ ] **Step 1: Write failing tests**

~~~python
def test_adjudicator_fallback_over_ten_percent_voids_arm():
    lines, code = report(control_rows(), model_rows(calls=10, fallbacks=2))
    assert code == 2
    assert any("VOID" in line for line in lines)

def test_exactly_ten_percent_adjudicator_fallback_is_not_void():
    lines, code = report(control_rows(), model_rows(calls=10, fallbacks=1))
    assert code == 0
~~~

- [ ] **Step 2: Run tests to verify failure**

Run: py -3 -m unittest eval.test_belfry_adjudicator_verdict -v

Expected: FAIL importing verdict module.

- [ ] **Step 3: Write minimal controller and criterion**

~~~python
def held_out_accuracy(traces: list[Trace]) -> float:
    by_seed = group_by_seed(traces)
    assert len(by_seed) == len({trace.seed for trace in traces})
    train = [trace for seed, rows in by_seed.items() if seed % 2 == 0 for trace in rows]
    test = [trace for seed, rows in by_seed.items() if seed % 2 == 1 for trace in rows]
    assert {trace.seed for trace in train}.isdisjoint({trace.seed for trace in test})
    model_counts = Counter(feature(trace) for trace in train if trace.source == "model")
    random_counts = Counter(feature(trace) for trace in train if trace.source == "random")
    return sum(classify(feature(trace), model_counts, random_counts) == trace.source
               for trace in test) / len(test)
~~~

Bind 60 games each, seeds 6100..6159, compact 5-seat/one-round random-player recipe, local model, no-thinking, 0.0 adjudicator temperature. Verify control/model deals match by game seed. Reject missing provenance. Print player and model-adjudicator rates; control adjudicator rate is n/a.

- [ ] **Step 4: Run controller tests to verify pass**

Run: py -3 -m unittest eval.test_belfry_adjudicator_verdict -v

Expected: PASS for each void, duplicate seed, label leakage, training-seed leak, recipe mismatch, and source-discrimination fixture.

- [ ] **Step 5: Commit**

~~~text
git add eval/belfry_adjudicator_verdict.py eval/test_belfry_adjudicator_verdict.py docs/belfry-adjudicator-criterion.md
git commit -m "feat(eval): precommit belfry adjudicator arm"
~~~

### Task 5: Launcher, canonical rules, and verification

**Files:**

- Create: eval/runs/belfry-adjudicator.cmd
- Modify: games/belfry/RULES.md:Discretion,Variant axes
- Modify: queue.md:S8 and belfry row

**Interfaces:**

- Consumes: frozen driver flags and criterion record paths.
- Produces: tracked dual-arm recipe; run output stays untracked.

- [ ] **Step 1: Write failing configuration test**

~~~python
def test_model_arm_requires_separate_adjudicator_route():
    with self.assertRaises(SystemExit):
        parse_args(["--adjudicator", "model"])
~~~

- [ ] **Step 2: Run test to verify failure**

Run: py -3 -m unittest eval.test_run_belfry_adjudicator -v

Expected: FAIL until required model-adjudicator route validation exists.

- [ ] **Step 3: Freeze recipe and canonical prose**

Create belfry-adjudicator.cmd: burst probe, then random control and model arm into distinct JSON and JSONL paths. Update RULES.md to state setup-only model discretion and private provenance. Update only S8/queue rows changed by this work. Do not add run output.

- [ ] **Step 4: Run verification**

Run: py -3 -m unittest discover -v

Run: git diff --check

Run: C:\Program Files\Git\bin\sh.exe scripts/hygiene-check.sh --budget

Expected: full suite passes, diff has no whitespace errors, hygiene gate passes.

- [ ] **Step 5: Commit**

~~~text
git add eval/runs/belfry-adjudicator.cmd games/belfry/RULES.md queue.md
git commit -m "docs(belfry): freeze adjudicator arm recipe"
~~~
