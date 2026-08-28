# DURF - session transcript

ruleset `DURF 2.2 (2021)` | seed `5170` | 3 round(s) | 5 turns

*DURF by Emiel Boven, edited by Ava Islam, CC BY 4.0*

## Public record

*Italic lines are the referee's own words - the kernel's results and the adjudicator's narration, and the only channel gate #1 audits. Plain lines are what a seat said or declared; those are gameplay. No seat's private reasoning appears anywhere below - it never enters either channel.*

- Vesh: "I check the floor for anything loose."
- *Vesh rolls DEX for 18 against 15 - success.*
- *Vesh runs his hands along the scree, feeling for anything that might give way.*
- Vesh: "I look around the room carefully."
- Ola: "I listen at the door before touching it."
- *Ola rolls WIL for 11 against 15 - failure.*
- *Ola presses her ear to the cold iron door, straining to hear what lies beyond.*

## Gate #1 - the entitlement audit

Verdict: **LEAKED**.

Facts the adjudicator DECLARED to the party:

- `['room', 'R1']`

Facts it did not, which no referee byte above may show:

- `['room', 'R2']`
- `['room', 'R3']`
- `['room', 'R4']`
- `['hidden', 'R2']`
- `['hidden', 'R3']`
- `['hidden', 'R4']`
- `['npc', 'barrow-rats']`
- `['npc', 'barrow-wight']`

### The leak, in seat 0's context

- `['room', 'R2']` reached it via the term `iron door`

Carried by the referee line(s):

> Ola presses her ear to the cold iron door, straining to hear what lies beyond.

## Integrity (referee-side)

- 0/5 decisions fell back (0.00%)
- 0 were sent back by the parser or the kernel and then answered legally
- 0 refused attempts, of which 0 were rule refusals

- the session ended early: `LeakDetected: gate #1 violated in seat 0's context: ['room', 'R2'] via 'iron door' | carried by: ['Ola presses her ear to the cold iron door, straining to hear what lies beyond.']`
