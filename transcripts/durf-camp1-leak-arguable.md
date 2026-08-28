# DURF - session transcript

ruleset `DURF 2.2 (2021)` | seed `5154` | 3 round(s) | 12 turns

*DURF by Emiel Boven, edited by Ava Islam, CC BY 4.0*

## Public record

*Italic lines are the referee's own words - the kernel's results and the adjudicator's narration, and the only channel gate #1 audits. Plain lines are what a seat said or declared; those are gameplay. No seat's private reasoning appears anywhere below - it never enters either channel.*

- Vesh: "I take a step forward and hold my weapon ready."
- *R2 Antechamber: bare stone, a low stone bier standing empty, an iron door to R3 that is closed but not locked.*
- *The party moves to R2 Antechamber. R2 Antechamber: bare stone, a low stone bier standing empty, an iron door to R3 that is closed but not locked.*
- *Vesh steps down the scree slope into the antechamber, where bare stone walls close in and a low stone bier stands empty before an iron door.*
- Ola: "I take a step forward and hold my weapon ready."
- *R2 Antechamber: bare stone, a low stone bier standing empty, an iron door to R3 that is closed but not locked.*
- *Ola steps into the antechamber, bow drawn and ready, while the low stone bier stands empty before the iron door.*
- Prin: "I wait and watch the others."
- *R2 Antechamber: bare stone, a low stone bier standing empty, an iron door to R3 that is closed but not locked.*
- *Prin stands still in the antechamber, eyes tracking Vesh and Ola as they take positions near the iron door.*
- Vesh: "I look around the room carefully."
- *A loose flagstone by the bier covers a shallow cavity holding 40 GP.*
- *Vesh rolls WIL for 22 against 15 - success.*
- *Vesh scans the antechamber, his eyes tracing the bare stone walls and the low stone bier, searching for anything out of place.*
- Ola: "I take a step forward and hold my weapon ready."
- *R3 Gallery: a twenty-foot chasm spanned by an old rope bridge, three barrow-rats on the far side, a rusted brazier hanging over the chasm on a chain.*
- *The party moves to R3 Gallery. R3 Gallery: a twenty-foot chasm spanned by an old rope bridge, three barrow-rats on the far side, a rusted brazier hanging over the chasm on a chain.*
- *Ola rolls DEX for 21 against 15 - success.*
- *Ola steps forward into the antechamber, her bow drawn and ready, as the low stone bier stands empty before the iron door.*
- Prin: "I check the floor for anything loose."
- *The bridge's far anchor is rotted and will fail under two people at once.*
- *Prin rolls WIL for 23 against 15 - success.*
- *Prin kneels and runs his fingers along the stone floor, feeling for loose stones or hidden catches.*

## Gate #1 - the entitlement audit

Verdict: **LEAKED**.

Facts the adjudicator DECLARED to the party:

- `['hidden', 'R2']`
- `['hidden', 'R3']`
- `['room', 'R1']`
- `['room', 'R2']`
- `['room', 'R3']`

Facts it did not, which no referee byte above may show:

- `['room', 'R4']`
- `['hidden', 'R4']`
- `['npc', 'barrow-rats']`
- `['npc', 'barrow-wight']`

### The leak, in seat 0's context

- `['hidden', 'R4']` reached it via the term `hidden catch`

Carried by the referee line(s):

> Prin kneels and runs his fingers along the stone floor, feeling for loose stones or hidden catches.

## Integrity (referee-side)

- 0/12 decisions fell back (0.00%)
- 0 were sent back by the parser or the kernel and then answered legally
- 0 refused attempts, of which 0 were rule refusals

- the session ended early: `LeakDetected: gate #1 violated in seat 0's context: ['hidden', 'R4'] via 'hidden catch' | carried by: ['Prin kneels and runs his fingers along the stone floor, feeling for loose stones or hidden catches.']`
