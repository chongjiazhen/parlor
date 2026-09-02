"""The DURF kernel, as the adjudicator is told it, plus the version it is pinned to.

**This is prompt text, so every string here is a model-facing byte.** Editing one
re-baselines every number scored against it, the same way a theme blurb does in
``games/cabal``. The digest below is length-stable on purpose: it is the whole
rules surface the adjudicator gets, and a run that grew it is not comparable to a
run that did not. **It grew on 2026-09-02** - per-weapon slot costs corrected,
the attack attributes (STR close, DEX ranged) and the full-turn cast added, all
three found missing or wrong against the source - so every durf number scored
before that date was scored against the shorter digest.

**Version pin.** DURF 2.2 (2021). ``docs/durf-rung.md`` carries the fetchable
source and the line to check on any re-read - the document is a living artifact
under its author's control, so a re-read that finds a different version line has
re-baselined the fixture and the labels have to be re-verified before any number
from them means anything.

**Attribution, owed by the licence rather than offered as a courtesy.** DURF is
written and illustrated by Emiel Boven, edited by Ava Islam, CC BY 4.0. What ships
here is a paraphrase of the mechanics the adjudicator needs, not the rules text.

What is NOT here is the adjudicator's own five decisions - those live in
``adjudicate.py``, because the kernel is the part a model never touches.
"""

from __future__ import annotations

#: The pinned ruleset. Recorded on every run so a record cannot be read against
#: the wrong rules text.
RULESET = "DURF 2.2 (2021)"

#: The three attributes. Here rather than in the fixture because they are a fact
#: about the ruleset, and both the fixture loader and the adjudicator read them.
ATTRIBUTES = ("STR", "DEX", "WIL")

#: Named in the record beside ``RULESET`` for the same reason.
ATTRIBUTION = "DURF by Emiel Boven, edited by Ava Islam, CC BY 4.0"

#: The mechanics an adjudicator has to know to answer decisions 1, 2 and 4, and
#: nothing beyond them. Advancement, downtime, the encounter table and the
#: Blunders table are all absent - they are kernel arithmetic no ruling turns on,
#: and every line of prompt that cannot change an answer is a line competing with
#: the ones that can.
KERNEL_DIGEST = """\
DURF 2.2 mechanics (the parts a ruling turns on):

- Attributes are STR, DEX and WIL. An action roll is d20 + the governing
  attribute, and OVER 15 succeeds. Saves are action rolls.
- An opposed roll is against an NPC: both roll, highest wins. NPCs add their
  Skill instead of an attribute. Close combat is an opposed STR roll and
  ranged combat an opposed DEX roll; a ranged defender who wins deals no
  damage. Close-combat ties go to the attacker.
- A roll is for an UNCERTAIN outcome under pressure or opposition. Something
  certain resolves without one; something impossible is refused, not rolled.
- Pushing happens before a roll: take one Stress to gain a Buff. It needs at
  least one EMPTY inventory slot, and it is repeatable while slots last. NPCs
  cannot push and take no Stress.
- Inventory slots are 10 + STR. Most items take one slot. Medium armour takes
  two and heavy armour three. A sword, axe, flail or pistol takes two; a bow
  takes two; a greatsword, halberd, warhammer or crossbow takes three. Each
  Stress occupies a slot. Wounds and GP occupy none. A character cannot carry
  more items or Stress than they have slots.
- Casting a spell is a WIL roll. It requires an empty slot, a free hand, and the
  ability to speak. Success costs one Stress; failure costs neither. A caster
  who spends a full turn (10 minutes) on the spell casts it without a roll and
  still takes the Stress. A character can only cast a spell they know.
- Armour is a depleting pool, not flat reduction: damage drains Armor points
  first and the remainder lands as Wounds. Shields reduce damage by 1, never
  below 1.
- On receiving Wounds a character rolls all their HD (d6 each); a result at or
  under their accumulated Wounds is death. 0 HD dies to any Wound.
- NPCs carry a Morale value (ML). The morale roll is 2d6 and a result HIGHER
  than ML means the NPCs flee or parley. The rules specify the roll and leave
  the trigger to the referee: it is rolled when something shocks the NPCs - more
  resistance than they expected, their leader killed, and the like.
- Time runs in rounds (10 seconds), turns (10 minutes) and watches (4 hours).

There are no character classes, no skills and no proficiencies in DURF. A
character being described as trained, expert or practised at something carries
no mechanical weight and changes no ruling.\
"""

#: The adjudicator's frame. Deliberately does NOT ask for a good session, a fair
#: table or a fun scene: this instrument grades three decisions against a labelled
#: fixture and nothing it says about pacing or description is measured.
#:
#: Written positively where it can be. ``.claude/rules/model-facing-text.md``'s
#: negation rule applies to this file as much as to the player prompts - steering
#: by prohibition makes the banned behaviour more available - so the two hard
#: constraints that survive as refusals ("no roll is not the same as success",
#: and the illegal case) are stated as what to DO with each, and each pairs with
#: a positive instruction.
ADJUDICATOR_SYSTEM_PROMPT = (
    "You are the referee of a tabletop roleplaying game running on the DURF 2.2 "
    "rules. A player declares what their character does; you rule on it. Rule "
    "from the rules text and the stated state of the world, and let the fiction "
    "follow from the ruling rather than the other way round. Three rulings are "
    "available to you and each says something different: call for a roll when "
    "the outcome is genuinely uncertain, resolve without a roll when the outcome "
    "follows from what is already established, and refuse the declaration as "
    "illegal when a rule or the character's own state forbids the attempt. "
    "Answer with JSON."
)
