# parlor

A PettingZoo-style arena for LLM agents playing hidden-information games - built to
prove one hard property before anything else: **independent context**. Each agent
sees only its own view of the world; secrets it isn't entitled to are not merely
hidden in the UI, they are *absent from the bytes sent to its model*.

The endgame is a freeform AI-run TTRPG: independent actors, off-map factions acting
on their own clock, and a referee that oversees without micromanaging. The games
below are increasingly-freeform test harnesses for that one `core/` engine. We start
with `cabal` - a bounded team-mission hidden-role deduction game - because it is
the purest test of the property, and
its referee needs zero judgment: it is a unit test, not an opinion.

Naming is deliberately branding-free. The canonical layer (dir, class, role *keys*)
is functional - `seer`, `watcher`, `mimic`, `hunter` - so the engine reads cleanly
and carries no game's trademark. Fiction lives only in swappable **themes**; the
default face is a 1984 skin (public-domain novel), with a sterile `plain` skin as
fallback. Game *rules/mechanics* aren't copyrightable; only *expression* (names,
art, text) is, and none of that is baked into the code.

## The ladder (rule-heavy -> judgment-heavy)

| Rung | Referee is | Status |
|---|---|---|
| **cabal** (hidden-role missions) | pure deterministic code | spike #1 (here) |
| Secret Hitler | deterministic + forced reveals | next (fully CC-licensed) |
| Blood on the Clocktower | a Storyteller with discretion | north star |
| Freeform TTRPG (5e SRD) | mostly LLM judgment | the actual product |

## Layout

```
core/observability.py   SeatView, Knowledge, find_leaks  (partial-observability spine + gate #1)
core/backends.py        one adapter: local:8090 / clean:3001 / gray:3003, pluggable player prompt
games/cabal/roles.py    roles as data (functional keys) + swappable themes (1984-en default)
games/cabal/referee.py  deterministic state machine (propose -> discuss -> vote -> mission -> hunt)
games/cabal/player.py   policies (random / LLM), reply parsing, retry loop, game driver
games/cabal/demo.py     one game, random or live players, per-turn leak audit
games/cabal/test_*.py   gate #1 (no leak) + referee win paths + parsing/plumbing
eval/run_games.py       run-N-games scoring for gates #2/#3 (deception, deduction)
```

## Two public channels, and the line between them

The discussion phase is where an agent can *say* anything, including a lie. That
made one distinction load-bearing, so the referee keeps two tagged channels:

| channel | written by | audited by gate #1? |
|---|---|---|
| `("event", ...)` | the referee | **yes** - a referee naming a role is a leak |
| `("speech:<seat>", ...)` | a player, via `speak()` | no - a claim about a role is a move, true or false |

A player's private reasoning is in neither: the JSON envelope gives it a `think`
field, the driver reads it for the log and drops it, and only `say` reaches
`speak()`. Three mutation-checked tests hold that line (`test_player.py`).

## The three gates

1. **No leak** - no seat's context reveals another's secret role. *(green: `test_leak_audit.py`)*
2. **Deception works** - evil wins a non-trivial share via failed missions or a correct hunt.
   *(live players wired; not yet shown - see below)*
3. **Deduction works** - good votes / the hunt beat chance. *(live players wired; not yet shown)*

**Gate #2 is conditional on gate #3, and that is measured, not pedantry.** Against
good seats voting at chance, evil wins ~65% of games with no deception in the loop
at all (`--arm random`, n=200). So an evil win rate is only evidence of deception
once the good side demonstrably deduces; the scorer refuses to call gate #2 until
gate #3 holds, and voids both verdicts when too many decisions fell back to random.

## Run

```bash
python -m unittest discover -s . -p "test_*.py"   # all tests, no dependencies
python -m games.cabal.demo                         # watch a random game (default 1984-en face)
python -m games.cabal.demo --theme plain           # sterile functional names
python -m games.cabal.demo --rounds 2              # two discussion rounds per proposal

# live players (needs a backend; PARLOR_API_KEY for the cloud tiers)
python -m games.cabal.demo --backend local --model <armed-model>
python -m games.cabal.demo --backend clean --speaker    # model on the discussion only

# scoring
python -m eval.run_games --games 200 --arm random                 # the chance baseline
python -m eval.run_games --games 20 --backend clean --model <id> --workers 3
```

Pin a model id; `auto` picks a different upstream per request, and a catalog entry
can be stale (`model_not_found` at call time on a model `/v1/models` lists). The
scorer reports a fallback rate and the refusal trace beside every number, so a dead
endpoint reads as "the run is void", not "the model played badly".

Python 3.10+. No dependencies (stdlib only) for the referee and gates; a backend is
only needed once LLM players go live.
