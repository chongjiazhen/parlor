# Dungeons - the ones you PLAY

`games/durf/fixtures/` is the instrument. This directory is not.

A dungeon here ships two files, `scenario.json` and `facts.json`, and no third.
That absence is the whole distinction:

| file | what it is | who needs it |
|---|---|---|
| `scenario.json` | the world - rooms, exits, sightlines, party, NPCs, clock | anyone playing |
| `facts.json` | the world facts and their naive sentinels | gate #1, so the audit has a corpus |
| `declarations.json` | 48 labelled declarations on a pinned balance | **only** a scored run - and no dungeon here carries one |

So nothing in this directory is graded, no number is scored against it, and adding
one voids nothing. The graded dungeon is `fixtures/hollow-barrow`, whose rendering
is a model-facing byte of six recorded instrument runs: **editing that one
re-baselines every DURF number in the tree, and adding one here does not.** That
asymmetry is why play dungeons live in their own directory rather than beside it.

One directory is one dungeon. `kernel.load(path=...)` reads both files from it and
refuses a pair whose `scenario_id`s disagree, because a mismatched pair audits one
dungeon against another's sentinels and reports a hold over the wrong corpus -
green, and meaningless.

```
python -m parlor play durf --dungeon drowned-mill --human 0
```

---

## `drowned-mill` - 12 rooms, written in-house 2026-09-02

**Why it is not borrowed.** A dungeon is creative expression, so the
mechanics-are-not-copyrightable argument that lets four rungs name their source
game does not reach it. A licence sweep found the canonical teaching dungeon
(52 rooms, explicitly built to train new players and new referees) under a
non-commercial share-alike licence, every DURF-native community module either
all-rights-reserved or silent on licence, and exactly one shippable module, under
CC0 but written for another system. Writing one costs less than converting that
one and carries no attribution obligation at all. The sweep is in the working
notes; what survives here is the decision.

**The shape.** Four rooms teach, four rooms cost, four rooms pay - and the map is
a **loop**, which the graded dungeon is not. `kernel.distance` was written with a
comment noting that fixture-order and graph distance agree on a corridor and would
not on a loop; this is the first dungeon in the tree where they do not.

```
        R1 Millyard ─────────────────────────── R12 Overflow tunnel
         │                                            │
        R2 Wheelhouse                                 │
         │                                            │
        R3 Grinding floor ── R4 Sack store            │
         │                    │                       │
        R5 Sluice room       R6 Cistern               │
         └──── R7 Sunken stair ┘  │                   │
                    │            R8 Miller's room     │
                    └──── R9 Shrine ────┘             │
                            │                         │
                          R10 Bone weir ──────────────┘
                            │
                          R11 Vault
```

**The routing choice the loop buys.** The weir is six rooms from the door by the
mill and two by the channel. The back way is faster and arrives at the most
dangerous room in the dungeon with none of the information the mill would have
given you, so R12 states its warning in its own text - bones and cloth turning in
the current, coming down from upstream. A shortcut a party can read is a choice;
one they cannot is a gotcha.

**What each room is for.** A beginner dungeon should teach one thing at a time and
telegraph before it bites.

| room | teaches |
|---|---|
| R1 Millyard | read the scene. Two ways in, one of them visibly the hard way |
| R2 Wheelhouse | obvious treasure has an obvious cost. The key is on a body wedged in the thing holding the wheel |
| R3 Grinding floor | searching pays, and the air is thick with flour dust while the party carries a lit lantern |
| R4 Sack store | a fight you can win. 0 HD, ML 5: they die to any Wound and break early |
| R5 Sluice room | a lever whose consequence is written on the wall. The tide line says what shutting it does |
| R6 Cistern | something is in the water and the walkway means you need not go in |
| R7 Sunken stair | small bones, picked clean, upstream of where you are going |
| R8 Miller's room | not everything is a fight. He answers if he is spoken to, and he knows the chest |
| R9 Shrine | a trick, not a trap. The door opens for value left in the basin and shuts when it is taken back |
| R10 Bone weir | ML 12. They never flee, and they never leave this room. Knowing when to go is the lesson |
| R11 Vault | the answer is in the room. The dials spell the mill's name, burned into every tally-board beside them |
| R12 Overflow tunnel | the way out, and the way back in |

**Two places a party can be clever and one where it can be greedy.** Freeing the
body in R2 turns the wheel; the shrine door in R9 can be held open by anything of
value, including something the party would rather keep; the chest in R11 opens to
reading rather than to a roll. None of the three needs a roll to solve and all
three can be solved wrong.

**Balance is not pinned here and that is deliberate.** `fixtures/` publishes counts
and `check_balance` re-derives them, because a graded fixture edited without
re-counting flatters a model silently. Nothing here is scored, so there is nothing
to flatter. What IS enforced is `check_topology` on the exit graph and
`check_facts` on the sentinels, both at load, and both apply to every dungeon in
this directory.
