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
games/cabal/referee.py  deterministic state machine
games/cabal/demo.py     random-driver full game + per-turn leak audit
games/cabal/test_*.py   gate #1 (no leak) + referee win paths
eval/                   run-N-games scoring for gates #2/#3 (deception, deduction) - later
```

## The three gates

1. **No leak** - no seat's context reveals another's secret role. *(green: `test_leak_audit.py`)*
2. **Deception works** - evil wins a non-trivial share via failed missions or a correct hunt. *(needs live players)*
3. **Deduction works** - good votes / the hunt beat chance. *(needs live players)*

## Run

```bash
python -m unittest discover -s . -p "test_*.py"   # all tests, no dependencies
python -m games.cabal.demo                         # watch a random game (default 1984-en face)
python -m games.cabal.demo --theme plain           # sterile functional names
python -m games.cabal.demo --theme 1984-cn         # Chinese 1984 flavor
```

Python 3.10+. No dependencies (stdlib only) for the referee and gates; a backend is
only needed once LLM players go live.
