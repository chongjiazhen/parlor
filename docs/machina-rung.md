# Machina rung - design specification

**2026-09-03T16:59:14Z.** Drafted before implementation. `machina` is a
functional key, not a game title or a claim about any source game.

## Problem statement

A Parlor table needs a dramatic mecha campaign whose pilots can hold private
facts, make consequential choices, and play through theatre-of-mind action. A
grid-first tactical ruleset does not fit this table: it spends context on spatial
state, makes the referee a combat calculator, and cannot express several desired
tones without carrying mutually incompatible subsystems.

## Solution

`machina` is a Parlor-native, AI-refereed campaign engine. It keeps one dramatic
resolution kernel - position, effect, clocks, pressure and fallout - and loads a
pack that supplies setting material plus exactly one tone-specific pressure
subsystem. The first packs are `iron-horizon` (real-military), `crown-of-stars`
(super robot), and `signal-wound` (institutional trauma). All action is
theatre-of-mind. Secret pilot, machine and faction facts are rendered only to
entitled seats and audited by gate #1.

## User stories

1. As a pilot, I want to attempt an action from a stated fictional position, so
   that machine choice matters without a grid. **Independent test:** one action
   resolves to an outcome carrying a changed clock, pressure, condition, or
   established fictional fact; no coordinate, range, map, initiative, or movement
   field exists in its ask or state.
2. As a pilot, I want my private history, machine condition and secrets withheld
   from other pilots, so that relationships and revelations are play rather than
   shared prompt context. **Independent test:** gate #1 raises when a foreign
   private fact is planted in any reachable ask, and accepts the entitled pilot's
   own ask.
3. As a referee, I want one bounded decision interface for adjudicating uncertain
   actions, so that an AI referee can rule fiction without owning hidden state or
   bypassing audit. **Independent test:** same seeded action and referee response
   produces same state transition and referee decision record; malformed or
   refused response is explicit, never silently interpreted as success.
4. As a table, I want a pack to make missions feel military, super-robot, or
   institutional-trauma driven, so that tone changes stakes rather than labels.
   **Independent test:** identical core action enters a pack-specific pressure
   transition in each of the three example packs, while core outcome and audit
   behavior remain identical.
5. As a campaign, I want each mission to create repair, relationship and faction
   fallout, so that drama persists beyond one scene. **Independent test:** a
   completed mission returns a public mission result plus private pilot fallout;
   subsequent asks show only facts entitled to their seat.
6. As an operator, I want locally supplied packs, so that Parlor ships procedure
   and schema rather than borrowed setting expression. **Independent test:**
   loader accepts each tracked example pack, refuses malformed packs loudly, and
   resolves a local directory using same schema.

## Implementation decisions

- New rung: `games/machina/`; do not widen `core/` before a second game needs its
  abstractions. It owns state, ask construction, referee protocol, audit and pack
  loader.
- Engine state has public mission clocks and facts, then per-seat private pilot
  and machine facts. Gate #1 audits every reachable model-facing ask against that
  seat's entitlement. Player speech remains gameplay and is excluded from the
  referee-byte audit, matching existing channel rules.
- Scene kernel is fixed: referee states position/effect and consequence clocks;
  pilot names an approach; dice or seeded chance resolves uncertainty; outcome
  advances progress or consequence and may cost pressure or condition. The
  referee may establish facts only through an explicit decision record.
- No grid representation: no coordinates, distances, facing, movement allowance,
  turn order, tactical range band, armor facing, or per-weapon hit calculation.
- A machine is a frame with three systems and tags. Systems grant fictional
  permissions or a bounded effect change. Tags qualify what is plausible. Neither
  changes resolution rules.
- Every pack provides playbooks, frames, systems, starting clocks, mission hooks,
  and one `pressure` definition with trigger, track, spend/relief rules and
  fallout. Packs cannot alter core resolution, entitlement, audit, or output
  schema.
- `iron-horizon` pressure is supply and command friction. Spending resources or
  breaking orders changes mission cost and later support.
- `crown-of-stars` pressure is tension. Escalation unlocks transformation,
  combination and named finishing permissions; it does not grant automatic
  success.
- `signal-wound` pressure is synchronization and institutional control. Pushing
  capability increases sync strain and gives institution clocks leverage; fallout
  changes pilot relationships and machine availability. It must not import a
  branded setting or source-specific terms.
- Example packs are original minimal material, tracked with individual licenses,
  never a renamed or structurally copied published game. Operator-owned material
  remains untracked under `games/machina/packs/`.

## Testing decisions

- Use stdlib tests alongside `games/machina/`, following existing game tests.
- Test external behavior: action outcomes, no-grid ask/state shape, fallback or
  refusal behavior, pack validation, each pressure transition, mission fallout,
  seeded repeatability, and reachable-state leak planting.
- Use `play_game(..., audit=True)` or machina's equivalent default-on audit. A
  test must demonstrate that the guard fails before accepting its green case.
- Add one scripted human/demo mission per tracked pack; verify output records
  public result and private facts without revealing foreign facts.

## Out of scope

- Full campaign generator, published-system conversion, grid combat, detailed
  equipment accounting, every mecha genre, and source-material packs.
- A live model campaign or quality measurement criterion. Those require a frozen
  criterion after engine behavior exists.
- Generalizing machina abstractions into `core/` without second-game evidence.

## Further notes

- Packs are intentionally strong but bounded: one pressure subsystem may alter
  stakes and available dramatic permissions, never replace action resolution or
  secret handling.
- First delivery is vertical, not exhaustive: three small playable example packs
  exercising same scene kernel. More frame, system and playbook volume comes only
  after a table exposes a missing behavior.
