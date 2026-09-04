# parlor

**A table of AI players that genuinely do not know what you know.**

Sit down in one seat. Every other seat is held by a model with its own private
view of the same game - its own secret role, its own night knowledge, its own
wrong ideas about you. Nobody at the table can read anyone else's, including the
referee's own bookkeeping, because an un-entitled secret is not hidden in a UI or
discouraged by a prompt: it is **absent from the bytes sent to that seat's model**.

That property is what makes a table of AI teammates worth playing against. If
every seat renders from one shared transcript, no teammate can be surprised, none
can keep something back, none can be wrong in a way you have to work around - and
bluffing, dramatic irony and betrayal are structurally impossible, however good
the prose is. Most multi-agent chat frameworks share one history by construction -
a group chat renders every member from the same log, and per-member visibility is
routinely declined as a feature because the whole design assumes one transcript.

This is not a claim to be first at anything - only that the repo treats
information isolation as a machine-checked invariant that fails the run, rather
than a leakage rate measured afterwards. The nearest survey of the area
([arXiv:2607.12406](https://arxiv.org/html/2607.12406v1)) names
"isolation-by-construction" as open future work and calls this the **agent-agent**
boundary.

The endgame is a freeform AI-run TTRPG - independent actors, off-map factions on
their own clock, and a referee that oversees without micromanaging. The games
below are increasingly-freeform test harnesses for one `core/` engine, and they
are deliberately the *hard* case: if seats can keep secrets from each other and
from you in a hidden-role game, a party where the rogue has a secret patron is
easy by comparison.

**Five rungs, and the set is gated rather than collected.** A game earns a place
in `games/` by exposing one named executable risk to information isolation or
referee judgment that no existing rung already expresses - the five below are
five different information models, not five card games. Genre, familiarity and a
working play loop earn nothing on their own, which is why `games/` and
`core/registry.py` hold the same five names and why proof fixtures that nobody
sits down at live in `experiments/` instead. The full test is `AGENTS.md`
§Invariants.

## Try it

```bash
python -m parlor --list                       # the games you can sit at
python -m parlor play cabal                   # a whole game, random players, no model needed
python -m parlor play cabal --human 0         # you play seat 0
python -m parlor play changeling --human 0    # your own card can change under you
python -m parlor play quorum --human 0        # the secret is dealt in play, not at the deal
python -m parlor play belfry --seats 7 --human 0   # days and nights, and the referee may lie to you
python -m parlor play durf --human 0          # a dungeon party: the secret is the world, not a seat
```

Each game keeps its own flags - `play cabal --help` prints cabal's. One person per
game: a terminal is one channel, so two seats at it would read each other's private
view.

No dependencies, no API key, no GPU. The referee and the leak audit are stdlib
Python; a backend is only needed to put models in the other seats.

`pip install -e .` puts the same entry point on PATH as `parlor`, which is worth
one line of setup because `python -m parlor` silently requires you to be standing
in a checkout. It adds no dependency: the referee and both gates stay stdlib, and a
fresh clone with no install plays exactly the same games.

**In a game, three words are not moves.** `?` reprints the view, `help` reprints the
orientation, and `rules` prints that game's full `RULES.md`. They are answered by
the console and never reach the referee: the console is allowed to help, and the ask
is not allowed to change. Why the ask tells you what you may play now and not what
wins is *Context is a budget* below.

Before a live game, `parlor doctor` answers the part no `--help` can, because its
answer is about the box and not the repo:

```bash
parlor doctor            # which routes are reachable, which key is set, what they list
parlor doctor --probe    # one real one-token call per live route
```

The probe is the point. `/v1/models` answers from configuration, so a listed id can
be cold and fail at call time with `model_not_armed` or `model_not_found`; only a
call distinguishes a catalog from an armed model. It exits non-zero when no route
can serve a game, so it can gate an unattended run.

A rendered game to read instead:
[`transcripts/local-q36-2rounds-game0.md`](transcripts/local-q36-2rounds-game0.md)
- played on the `1984-en` skin, which the header states, so it does not look like
the sterile default the commands above produce.

**`--human SEAT` hands a person exactly the bytes that seat's model would have
received and nothing else** - so the isolation property is not something you take
on trust from a test, it is something you can sit inside and try to break. One
seat and one game per run, and that is the property asserting itself rather than a
missing feature: a terminal is a single channel, so two people at it would read
each other's private view. A second human seat needs a second channel.

## The ladder (rule-heavy -> judgment-heavy)

| Rung | Referee is | Status |
|---|---|---|
| **cabal** (hidden-role missions) | pure deterministic code | spike #1 |
| **changeling** (belief can diverge from truth) | deterministic, one night | spike #2 |
| **quorum** (entitlement cascades over a secret created in play) | deterministic, per event | spike #3 |
| Secret Hitler | deterministic + forced reveals | **not as a port** - a port buys recognition and no engine progress. `quorum` is that shape, built for the entitlement axis below rather than the recognition |
| **belfry** (the referee may state a falsehood to a seat, as a rule) | deterministic, discretion drawn from the seed | spike #4 |
| the same rung with a MODEL in the referee's seat | LLM judgment over one isolated decision | next - belfry's discretionary choices are already isolated and logged, so this replaces one function and nothing about the audit |
| Freeform TTRPG (5e SRD) | mostly LLM judgment | the actual product |

Ordered by how much JUDGMENT the referee needs, which is the axis the engine risk
sits on. A rung that adds rules without adding discretion is a lateral move, which
is why the third row is not planned.

**cabal** is a bounded team-mission deduction game, modelled on The Resistance:
Avalon: a leader proposes a team, the table argues, everyone votes, the team plays
success/fail cards in secret, and only the *count* of fails is ever public. Three
missions held wins it for the majority; three sunk wins it for the saboteurs, who
get one last shot at naming the seat that secretly knew them. **changeling** is a
different question, modelled on One Night Ultimate Werewolf: roles move during the
night, so a seat is told what it was *dealt* and never what it now *holds*, and it
can play a whole game sincerely wrong about itself. **quorum** is a legislative
cascade, modelled on Secret Hitler: each event deals a fresh hand that narrows as
it passes down the offices - three cards to the proposer, two to the enactor, one
enacted in public - so what a seat may see is a fact about the office it holds at
that event and not about the role it was dealt.

That last one is the second axis this ladder is ordered on, and it is why a third
deterministic rung was worth building. Entitlement is **dealt once** in cabal,
**mutable but still role-shaped** in changeling, and in quorum it **cascades over
an object that did not exist at the deal** - so the audit question changes from
*may this seat know this fact* to *may this seat know it at this point in the
chain*, and a referee that caches entitlement per seat rather than per event
passes every earlier test while being wrong.

**belfry** is the fourth, modelled on Blood on the Clocktower: a town square over
many days and nights, 22 roles on a public script of which nobody knows which are
in play, nominations and simultaneous votes, and a dead seat that keeps its voice
and one vote. What it adds to the ladder is not the size. In the three rungs before
it the referee always tells the truth; here it **lies on purpose, to a seat that is
not told**, because a poisoned or deluded seat is a rule of the game. So gate #1
stops meaning "tell the truth to the entitled" and starts meaning **never state a
true association a seat has not earned** - and a lie is safe only when it is built
to miss, which is why a false reveal is drawn from what a seat is NOT and a poisoned
watcher sees a derangement rather than a shuffle. A shuffle leaves fixed points, and
a fixed point is a true fact delivered to a seat with no claim on it: a real leak
wearing a lie's provenance.

The other thing it adds is that a referee of this family is normally a PERSON who is
allowed to choose. A deterministic referee cannot have taste, so every such choice -
which seat a reveal points at, whether an ambiguous seat reads as evil, who dies when
a kill is deflected - is drawn from the run's seeded RNG and written to the
referee-side log. That keeps `--seed` meaning what it means everywhere else in this
repo, and it is what makes the next rung cheap: the discretion is already one
isolated, logged set of calls, so putting a model in that seat changes one function.

Full rules and the knowledge tables: `games/cabal/RULES.md`,
`games/changeling/RULES.md`, `games/quorum/RULES.md`, `games/belfry/RULES.md`.

## Two public channels, and the line between them

The discussion phase is where an agent can *say* anything, including a lie. That
made one distinction load-bearing, so the referee keeps two tagged channels:

| channel | written by | audited by gate #1? |
|---|---|---|
| `("event", ...)` | the referee | **yes** - a referee naming a role is a leak |
| `("speech:<seat>", ...)` | a player, via `speak()` | no - a claim about a role is a move, true or false |

A player's private reasoning is in neither: the JSON envelope gives it a `think`
field, the driver reads it for the log and drops it, and only `say` reaches
`speak()`. Three tests hold that line - `test_think_is_dropped_say_is_kept`,
`test_driver_never_puts_think_on_the_table`, `test_a_lie_in_say_is_gameplay_not_a_leak`.

`--notebook` adds a private third channel: a seat's `note` comes back to that seat
and to no other, on every later call, so a read survives the turn that formed it.
It leaves the audit view with speech, because player-authored text is one class -
and a seat writing down a correct guess must not score as a referee leak.

The gate is enforced, not remembered. `play_game(..., audit=True)` is the default
and **raises** on a leak, so every game - demo, hand-played, test, and every game
in an N-game eval - is audited at every reachable state. `test_audit_coverage.py`
walks all five phases in **every** skin - it iterates `THEMES` rather than a list,
so a skin added later is covered the day it lands - audits `prompt_for` (the ask,
not just the view), and plants a leak in each phase's ask to prove the audit is
still reading it.

## Context is a budget, and the ask is incremental

parlor is **local-first**: the runs behind its numbers are one model served
serially on one box, not a frontier API with a context window nobody counts
(`docs/measurements.md` §Route - local is the gate lane). That makes the payload a
budget, and it is spent deliberately.

**A rule reaches a seat at the phase where it is actionable, and not before.** The
vote ask states the five-rejection rule; the mission ask states how many fails sink
it and what the seat's own side wants; the propose ask states neither, because
neither is actionable while you are picking a team. There is no standing rules
block anywhere - a seat is never handed the whole game, only the part of it that is
live.

**This is a position, not an omission**, and two measured things hold it there.
Every byte in the payload is audited by gate #1 and re-baselines every number
recorded under it, so context is never free. And restating a fact a seat *already
holds* is measured to cut both ways: one such line bought +7% -> +63% discrimination
on a 12B and then inverted on a stronger model, +80% without it against +72% with
it. More context is not monotonically better, so it is added as an arm and never on
the argument that it ought to help.

It is a real fork, and the queue carries the arm that would test it. A person is a
separate question with a free answer - the console prints a briefing and the full
rules beside the view, outside the payload, where neither cost lands.

## The gates - one property and two dated snapshots

**Gate #1 - no leak.** No seat's context reveals another's secret. This is the one
that measures *parlor*, it is green, and it is executable rather than argued
(`test_leak_audit.py`, `test_audit_coverage.py`).

The other two measure whichever model was armed, so they are reported as dated
snapshots and never as this repo's result - identical prompts scored **-0.2% on a
12B and +66% on 120B-class**, which is the whole argument for the distinction:

- **Gate #3 - deduction.** Blind seats approve clean teams over tainted ones by
  ~+18pp (binary, two runs agreeing). That figure pools self-votes with off-team
  votes and sits downstream of seer-originated public signal, so it measures
  *information reaching blind seats through play*, not unaided detection. The
  unaided estimator exists and accrues at ~0.4 votes/game, which is unaffordable
  at this rung - the arithmetic is re-runnable (`py -3 -m eval.gate3_arithmetic`).
- **Gate #2 - deception.** Evil wins a non-trivial share by sinking missions or a
  correct hunt. **Conditional on gate #3, and that is measured, not pedantry:**
  against good seats voting at chance, evil wins ~65% of games with no deception
  in the loop at all (`--arm random`, n=200). So an evil win rate is only evidence
  of deception once the good side demonstrably deduces.

Every number ships beside its fallback rate and the scorer voids a verdict above
10%. A decision no model made legally is played at random, and a run that hides
that is the random policy wearing a model's name. Beside it: how many decisions
the referee sent back before the model got them right, how random a table each
seat actually played against, and how many games ran with neither.

## Layout

```
core/observability.py      SeatView, Knowledge, find_leaks  (partial-observability spine + gate #1)
core/backends.py           one adapter, three routes (local / clean / gray), pluggable player prompt
core/console.py            a human seat wearing the backend interface (--human)
core/replies.py            model reply -> values (JSON out of prose, salvage, coercion)
core/runlog.py             a run writes its own terminal marker, from a finally
core/stats.py              Wilson intervals, bootstrap CIs
core/integrity.py          what a run's numbers are worth: three outcomes, caused vs witnessed

games/cabal/RULES.md       rules + the night-knowledge table the gates stratify on
games/cabal/roles.py       roles as data (functional keys) + 7 swappable themes
games/cabal/referee.py     deterministic state machine (propose -> discuss -> vote -> mission -> hunt)
games/cabal/audit.py       gate #1 as an executable guarantee - the driver runs it, and it raises
games/cabal/player.py      policies (random / LLM / human), phase->key mapping, retry loop, driver
games/cabal/transcript.py  one game -> readable markdown, straight off the public record
games/cabal/demo.py        one game, random or live or hand-played
games/cabal/solver.py      the mechanical reference - what the rules alone determine
games/cabal/heuristic.py   a rules-only policy, the rung the model is scored against

games/changeling/RULES.md  rules, and what a seat can and cannot know about itself
games/changeling/night.py  the night: roles move, and the seat is not told
games/changeling/referee.py, roles.py, audit.py, player.py, demo.py   as above, 8 themes

games/quorum/RULES.md      rules, and what an OFFICE entitles a seat to see
games/quorum/referee.py    the deck and the cascade - a hand narrows as it passes down
games/quorum/roles.py, audit.py, player.py, demo.py   as above, 2 themes

games/belfry/RULES.md      rules, the night order, and what a lie has to miss
games/belfry/state.py      the board the referee keeps, and the seeded discretion
games/belfry/night.py      what a seat is told, and how a false version of it is built
games/belfry/referee.py    days and nights as a cursor: pending() says who is on the clock
games/belfry/roles.py, audit.py, player.py, demo.py   as above, 2 scripts

core/registry.py           name -> the driver that plays that rung
core/doctor.py             `parlor doctor` - what this BOX can serve, and a real probe
parlor/__main__.py         `parlor play <game>`, and no game logic
pyproject.toml             the console script; no runtime dependency, ever

eval/run_cabal.py          run-N-games scoring for cabal's gates
eval/run_changeling.py     the same for changeling
eval/run_quorum.py         the same for quorum
eval/run_belfry.py         the same for belfry - executions against the chance rate on their own boards
eval/gate3_arithmetic.py   the gate-#3 verdict's arithmetic, re-runnable with its own control
eval/s6_verdict.py         the gate-#3b verdict, reproduced from each arm's own records
eval/strata.py             changeling's knowledge strata, counted over N nights
eval/derivable.py          what a seat could derive with no model at all
eval/ladder.py             the control ladder: random, rules-only, model
eval/audit_decisions.py    mine a finished run for moves wrong on their own terms

games/durf/                a fourth rung, scoped - a session engine and a labelled
                           fixture, and no console seat yet, so it is not registered

scripts/hygiene-check.sh   a pre-commit gate over the lines a commit ADDS
scripts/install-hooks.sh   installs it (`.git/hooks` is per-clone, so this is one command)
```

After cloning, `sh scripts/install-hooks.sh`. The gate reads added lines only,
so it never argues with what is already in the tree, and it holds no literal
name, address or key - only the shapes of one.

`core/` holds what the next game up the ladder inherits; `games/<name>/` holds
what is about *that* game. Reply-reading is in `core/` because a truncated reply
or a `"Approve."` where a boolean was asked for is a property of talking to
models, not of hidden roles - only the phase-to-key mapping is the game's.

## Run

```bash
python -m unittest discover -s . -p "test_*.py"   # unittest-style subset, no dependencies
python -m pytest                                  # everything (requires pytest)

python -m games.cabal.demo --theme plain           # sterile functional names
python -m games.cabal.demo --rounds 2              # two discussion rounds per proposal
python -m games.changeling.demo --theme greek      # the vocabulary-control skin

# live players (needs a backend; PARLOR_API_KEY for the off-box routes)
# each route defaults to a loopback URL and reads PARLOR_ENDPOINT_LOCAL /
# _CLEAN / _GRAY if you serve them somewhere else
python -m games.cabal.demo --backend local --model <armed-model>
python -m games.cabal.demo --backend clean --speaker    # model on the discussion only
python -m games.cabal.demo --human 0 --backend local --model <armed-model>

# scoring
python -m eval.run_cabal --games 200 --arm random                 # the chance baseline
python -m eval.run_cabal --games 20 --backend clean --model <id> --workers 3
python -m eval.run_cabal --games 20 --arm llm-good --backend clean --model <id>
python -m eval.run_changeling --games 200 --arm random

# a game a human can read
python -m games.cabal.demo --transcript game.md
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
and who was on them, no slogans. It bites hardest on a fictional skin: on `1984-en`
agents answered each other in
Party rhetoric for a whole game without once naming who was on the mission that
failed, which is a table that never starts deducing.

Pin a model id; `auto` picks a different upstream per request, and a catalog entry
can be stale (`model_not_found` at call time on a model `/v1/models` lists). The
scorer reports a fallback rate and the refusal trace beside every number, so a dead
endpoint reads as "the run is void", not "the model played badly".

## Naming, themes, and what is actually in this repo

Naming is deliberately branding-free. The canonical layer - directory, class, role
*keys* - is functional (`seer`, `watcher`, `mimic`, `hunter`), so the engine reads
cleanly and carries no game's trademark. Game rules and mechanics are not
copyrightable; only *expression* is - names, art, text - and no game's expression
is baked into the engine. Naming a game in prose as the thing a rung is modelled
on is reference, not reliance: nothing here needs a licence from anyone.

Fiction lives only in swappable **themes**, which are display-only and sit outside
that guarantee. `plain` is the sterile functional skin in all three games. cabal
ships 8 (default `lodge`, fraternal-order vocabulary; `1984-en` is a dystopia skin
evoking Orwell's *Nineteen Eighty-Four*); changeling ships 8 (default `folk`, plain
folk-game vocabulary); quorum ships 2 (default `guild`). What a theme carries is
coined vocabulary and prose written here - single words and short phrases are not
copyrightable, the novels' text is, and none of it is in this repo.

**cabal defaulted to `1984-en` until 2026-08-28 and now defaults to `lodge`.**
Nothing about the reasoning above changed; the skin is still shipped and still
supported. It is simply surface a public tree carries for no benefit when a face
that references nothing costs the same. It went to `plain` first and then to
`lodge` the same day, which puts all three rungs on one rule rather than on a
coincidence: default to a rights-free fiction, keep `plain` as the sterile
fallback. **Every recorded cabal number was played on `1984-en`**, so a run meant
to compare against one passes `--theme 1984-en`.

Themes are also an experimental dial, not just decoration - length-matched arms
exist for polarity and vocabulary controls. Design and the confounds:
`docs/moral-framing.md`.

MIT licensed. Python 3.10+, stdlib only for the referee, the gates and both
demos; a backend is needed only once LLM players go live.
