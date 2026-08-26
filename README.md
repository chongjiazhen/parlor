# parlor

A PettingZoo-style arena for LLM agents playing hidden-information games - built to
prove one hard property before anything else: **independent context**. Each agent
sees only its own view of the world; secrets it isn't entitled to are not merely
hidden in the UI, they are *absent from the bytes sent to its model*.

The endgame is a freeform AI-run TTRPG: independent actors, off-map factions acting
on their own clock, and a referee that oversees without micromanaging. The games
below are increasingly-freeform test harnesses for that one `core/` engine. We start
with `cabal` - a bounded team-mission hidden-role deduction game, modelled on The
Resistance: Avalon - because it is the purest test of the property, and its referee
needs zero judgment: it is a unit test, not an opinion.

**The game, if you don't know it.** The family plays 5-10 and is usually best at
7-8; this ships the 5-seat setup, which is the cheapest to run and, for what is
being measured here, the densest in usable samples. Five players. Two are secretly
saboteurs and
know each other. Of the other three, one secretly knows who they are, and a second
knows only that the informant is one of two people - without knowing which of those
two is the informant and which is a saboteur wearing the same face. Each round a
leader proposes a small team, everyone argues, everyone votes. The chosen team goes
on a mission and plays cards in secret - a saboteur may fail it, and only the number
of fails becomes public, never who played what. Three missions held wins it for the
majority; three failed wins it for the saboteurs. If the majority is about to win,
the saboteurs get one last shot: name the player who secretly knew, and take the
game instead. Everything interesting happens in the argument between those votes,
which is exactly what is being measured.

Naming is deliberately branding-free. The canonical layer (dir, class, role *keys*)
is functional - `seer`, `watcher`, `mimic`, `hunter` - so the engine reads cleanly
and carries no game's trademark. Game *rules/mechanics* aren't copyrightable; only
*expression* (names, art, text) is, and no game's expression is baked into the
engine. Naming a game in prose as the thing a rung is modelled on is reference, not
reliance: nothing here needs a licence from anyone.

Fiction lives only in swappable **themes**, which are display-only and sit outside
that guarantee. `plain` is the sterile functional skin. The shipping default is a
dystopia skin evoking Orwell's *Nineteen Eighty-Four* - public domain in the UK/EU
since 2021, still under US copyright until 2045, so it is a flavour choice and not
a licensing claim. Run `--theme plain` for a face that makes no reference at all.

Full rules, the night-knowledge table, and what each seat can derive:
`games/cabal/RULES.md`.

## The ladder (rule-heavy -> judgment-heavy)

| Rung | Referee is | Status |
|---|---|---|
| **cabal** (hidden-role missions) | pure deterministic code | spike #1 (here) |
| Secret Hitler | deterministic + forced reveals | next |
| Blood on the Clocktower | a Storyteller with discretion | north star |
| Freeform TTRPG (5e SRD) | mostly LLM judgment | the actual product |

## Layout

```
core/observability.py   SeatView, Knowledge, find_leaks  (partial-observability spine + gate #1)
core/backends.py        one adapter: local:8090 / clean:3001 / gray:3003, pluggable player prompt
core/replies.py         model reply -> values (JSON out of prose, salvage, coercion)
games/cabal/RULES.md    the rules + the night-knowledge table the gates stratify on
games/cabal/roles.py    roles as data (functional keys) + swappable themes (1984-en default)
games/cabal/referee.py  deterministic state machine (propose -> discuss -> vote -> mission -> hunt)
games/cabal/audit.py    gate #1 as an executable guarantee - the driver runs it, and it raises
games/cabal/player.py   policies (random / LLM), phase->key mapping, retry loop, game driver
games/cabal/demo.py     one game, random or live players
games/cabal/transcript.py  one game -> readable markdown, straight off the public record
games/cabal/test_*.py   gate #1 (no leak) + referee win paths + parsing/plumbing
eval/run_games.py       run-N-games scoring for gates #2/#3 (deception, deduction)
```

`core/` holds what the next game up the ladder inherits; `games/cabal/` holds what
is about *this* game. Reply-reading is in `core/` because a truncated reply or a
`"Approve."` where a boolean was asked for is a property of talking to models, not
of hidden roles - only the phase-to-key mapping is cabal's.

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

The gate is enforced, not remembered. `play_game(..., audit=True)` is the default
and **raises** on a leak, so every game - demo, test, and every game in an N-game
eval - is audited at every reachable state. `test_audit_coverage.py` walks all five
phases in all three skins, audits `prompt_for` (the ask, not just the view), and
plants a leak in each phase's ask to prove the audit is still reading it.

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
python -m eval.run_games --games 20 --arm llm-good --backend clean --model <id>

# a game a human can read
python -m games.cabal.demo --transcript game.md
python -m eval.run_games --games 12 ... --transcript one-game.md
python -m games.cabal.transcript run.json --game 3 --out game3.md
```

**Arms.** `--arm llm` seats both sides on the model, which measures deduction and
deception entangled - good failing to deduce and evil deceiving well move the
numbers the same way. `llm-good` / `llm-evil` seat one side live against the random
control, so the live side is the only thing moving. Note where gate #3's two halves
live: the vote half is the good seats, but the hunt half is the **hunter, who is
evil**. A mixed arm therefore carries one half at most, and every verdict line
names the side it is entitled to speak for.

**Transcripts** render from the two public channels in the order the referee wrote
them, never from re-derived end state: referee events in italic, player speech
plain. Below the assignment reveal comes the referee-side half a post-game read
needs - every decision in order, the private reasoning behind it, and the plays
the table is never told (who put the fail card in). Gate #1 governs the bytes a
seat's *model* receives, and none of that section ever reaches one. Raw run JSON
stays out of git (`eval/records/` is gitignored); a rendered transcript that
evidences a claim is what gets committed.

**Register** is a separate dial from the fiction skin. `--register character`
(default) plays the theme; `--register plain` keeps the same rules and asks for
the argument instead of the performance - name seats, cite which missions failed
and who was on them, no slogans. On the 1984 skin agents answered each other in
Party rhetoric for a whole game without once naming who was on the mission that
failed, which is a table that never starts deducing.

Pin a model id; `auto` picks a different upstream per request, and a catalog entry
can be stale (`model_not_found` at call time on a model `/v1/models` lists). The
scorer reports a fallback rate and the refusal trace beside every number, so a dead
endpoint reads as "the run is void", not "the model played badly".

Python 3.10+. No dependencies (stdlib only) for the referee and gates; a backend is
only needed once LLM players go live.
