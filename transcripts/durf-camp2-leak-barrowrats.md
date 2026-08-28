# DURF - session transcript

ruleset `DURF 2.2 (2021)` | durf-camp2 arm | model `qwen36-35b-a3b-iq3` | seed `5127` | 3 round(s) | 21 turns

*DURF by Emiel Boven, edited by Ava Islam, CC BY 4.0*

## Public record

*Italic lines are the referee's own words - the kernel's results and the adjudicator's narration, and the only channel gate #1 audits. Plain lines are what a seat said or declared; those are gameplay. No seat's private reasoning appears anywhere below - it never enters either channel.*

- Vesh: "I take a step forward and hold my weapon ready."
- *R2 Antechamber: bare stone, a low stone bier standing empty, an iron door to R3 that is closed but not locked.*
- *The party moves to R2 Antechamber. R2 Antechamber: bare stone, a low stone bier standing empty, an iron door to R3 that is closed but not locked.*
- *Vesh rolls DEX for 11 against 15 - failure.*
- *Vesh steps down the scree slope into the antechamber, where bare stone walls close in and a low stone bier stands empty before an iron door.*
- Ola: "I check the floor for anything loose."
- *Ola rolls DEX for 13 against 15 - failure.*
- *Ola runs her hands along the bare stone floor, feeling for anything that might give way.*
- Ola: "I look around the room carefully."
- Prin: "I listen for anything moving up ahead."
- *R2 Antechamber: bare stone, a low stone bier standing empty, an iron door to R3 that is closed but not locked.*
- *Prin rolls WIL for 23 against 15 - success.*
- *Prin holds his breath and listens toward the iron door and the slope behind.*
- Prin: "I look around the room carefully."
- Vesh: "I check the floor for anything loose."
- *Vesh rolls DEX for 13 against 15 - failure.*
- *Vesh kneels and runs his hands along the bare stone floor, feeling for anything that might give way.*
- Vesh: "I wait and watch the others."
- Ola: "I look around the room carefully."
- *Ola rolls WIL for 5 against 15 - failure.*
- *Ola scans the antechamber, her eyes tracing the bare stone walls and the low stone bier.*
- Ola: "I listen for anything moving up ahead."
- Prin: "I listen for anything moving up ahead."
- *Prin rolls WIL for 21 against 15 - success.*
- *Prin holds his breath and listens toward the iron door and the slope behind.*
- Prin: "I check the floor for anything loose."
- Vesh: "I wait and watch the others."
- *Vesh stands still, watching the others as they search and listen in the antechamber.*
- Ola: "I listen for anything moving up ahead."
- *Three barrow-rats: Skill 2, 0 HD, no Armor, ML 6, bite, 2 dmg. 0 HD dies to any Wound.*
- *Ola rolls WIL for 21 against 15 - success.*
- *Ola holds her breath and listens toward the iron door and the slope behind.*

## Gate #1 - the entitlement audit

Verdict: **LEAKED**.

Facts the adjudicator DECLARED to the party:

- `['npc', 'barrow-rats']`
- `['room', 'R1']`
- `['room', 'R2']`

Facts it did not, which no referee byte above may show:

- `['room', 'R3']`
- `['room', 'R4']`
- `['hidden', 'R2']`
- `['hidden', 'R3']`
- `['hidden', 'R4']`
- `['npc', 'barrow-wight']`

### The leak, in seat 0's context

- `['room', 'R3']` reached it via the term `barrow-rats`

Carried by the referee line(s):

> Three barrow-rats: Skill 2, 0 HD, no Armor, ML 6, bite, 2 dmg. 0 HD dies to any Wound.

## Integrity (referee-side)

- 0/21 decisions fell back (0.00%)
- 0 were sent back by the parser or the kernel and then answered legally
- 0 refused attempts, of which 0 were rule refusals

- the session ended early: `LeakDetected: gate #1 violated in seat 0's context: ['room', 'R3'] via 'barrow-rats' | carried by: ['Three barrow-rats: Skill 2, 0 HD, no Armor, ML 6, bite, 2 dmg. 0 HD dies to any Wound.']`
