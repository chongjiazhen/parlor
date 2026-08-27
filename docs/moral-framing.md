# Moral framing as a measured variable

Written 2026-08-25. Arms 3 and 4 built 2026-08-27; still UNRUN, so every number
below is absent rather than pending. Arrived sideways, out of a licensing question about the
default theme, which is a bad provenance for a research direction - so it is
written down narrowly rather than talked up.

**The question.** Holding mechanics, seeds, and information exactly fixed, does the
FICTION an agent is playing inside change how readily it deceives? `cabal` is an
unusually clean place to ask, because a theme is display-only by construction: swap
`Theme` and every rule, every entitlement, every byte of private knowledge is
identical. The only thing that moved is what the seat believes it is doing.

**The confound, which is the whole design problem.** `1984-en` vs `plain` is not
one variable. It is at least three: moral polarity (sabotage heroic vs neutral),
narrative richness (a blurb vs no blurb), and register (loaded vocabulary vs
sterile). A difference across that pair says nothing about morality specifically -
it could be that any fiction beats no fiction. The arms that separate them:

  1. `plain` - no fiction. Floor.
  2. `1984-en` - rich fiction, sabotage HEROIC (what ships today).
  3. `1984-inv` - rich fiction, sabotage VILLAINOUS. Built 2026-08-27; unrun.
  4. `drill-en` - rich fiction, morally NEUTRAL. Built 2026-08-27; unrun.

**Arms 3 and 4 exist as themes as of 2026-08-27** (`games/cabal/roles.py`), so this
doc no longer describes them as things to design. `DEFAULT_THEME` is unchanged and
no run has asked for either, so no recorded number moved.

**Arm 3 is the 1984 skin INVERTED, not a new fiction, and that is the design.** The
arm's whole job is to differ from arm 2 in valence and in nothing else, so a fresh
setting would reintroduce the confound `bnw-en` was added to control. Same world,
same register, same vocabulary shelf; only who-wrongs-whom moves. The trusting
majority becomes an underground cell running five drops out of the city, and the
informed minority are plants placed to lose each drop and give the cell up at the
end. Its blurb ascribes no trait to the seat ("were placed here", not "are paid"),
which is Hagendorff's constraint below rather than an editorial preference.

**Arm 4 is a sanctioned exercise with no victim** - a readiness drill everyone
signed for, where two seats were assigned to make each evolution fail so the
weaknesses surface in port. Sabotage is neither heroic nor villainous, and nothing
outside the drill is lost. It is the floor the 2-vs-3 contrast is read against:
without it, "valence moved deception" and "valence in either direction moved
deception away from neutral" produce the same number.

`bnw-en` (added 2026-08-27) is a second arm-2: rich fiction, sabotage HEROIC, same
polarity as `1984-en` and a different fiction. It is not arm 3 and does not
substitute for it. What it buys is the control arm 3 cannot supply - two heroic
fictions differing only in vocabulary, so a 2-vs-3 gap can be read against a
2-vs-2' gap, and "polarity moved it" separated from "this particular fiction moved
it". Nothing has been run on it.

**But `bnw-en` does not currently hold richness fixed, which is the one thing a
vocabulary control has to do.** Measured 2026-08-27: `1984-en` is 53 words, `bnw-en`
is 84, over half again as long. So a 2-vs-2' gap is confounded by blurb DENSITY -
the same axis this doc asks the changeling enrichment to isolate separately. The
three English arms are all exactly 53 words for that reason. Fixing it means
trimming `bnw-en` to 53 or lengthening `1984-en`, one of them and not both, and
either is a prompt edit that orphans any number recorded against that face. Do it
before the arm is run, not after.

**A `bnw-inv` was considered and rejected (2026-08-27).** It would give a 2x2 -
{1984, bnw} x {heroic, villainous} - and so a polarity main effect estimable across
two fictions rather than one. The reason not to: Brave New World does not invert
cleanly. Orwell's world has an unambiguous oppressor, so flipping who the plants
serve produces a fiction villainous in the same register and to the same degree.
Huxley's horror is *consensual*, and the novel's premise is precisely that the
conditioned majority is not free - so an inversion has to ask a seat to believe the
majority genuinely chose their stability and the minority are stealing it, which the
source fiction actively undercuts. That yields a mildly-villainous arm, a shrunken
gap on the `bnw` row, and a 2x2 interaction whose null cannot be read: "polarity
does not generalise across fictions" and "the second inversion was not much of an
inversion" produce the same number. Same failure the fae skin was rejected for, one
level up. If 2-vs-3 shows an effect and it needs to be shown to generalise, invert a
fiction that inverts cleanly - not this one. Fourth in line regardless, behind
running arms 1-4 at all.

Polarity is arms 2 vs 3, and only 2 vs 3 - they differ in valence and in nothing
else. Richness is 2+3 vs 1. Without arm 3 the experiment cannot make a claim about
morality at all, and that is the difference between a result and an anecdote.

**A vocabulary control has to be register-DISTANT, and that is why a fae skin was
rejected** (2026-08-27, changeling). The proposal was a Fair Folk changeling skin
beside `folk`: same polarity, same richness, different mythology - a 2-vs-2' pair
like `1984-en`/`bnw-en`. It fails as a control because the two are barely distant
at all. Same register (folk horror), same setting (a village at night), same
premise (something swapped you while you slept), same moral shape. The likely
result is no difference, and a null there is uninterpretable: "vocabulary does not
move it" and "those were one fiction under two names" produce the same number.
A null result nobody can read costs GPU and then gets cited. If this repo ever
wants a changeling vocabulary control, it has to move the register as far as it
can while holding polarity - the clinical-SF body-snatcher framing, not another
mythology off the same shelf. It is third in line regardless, behind arms 3 and 4.

The fae material is not wasted; it is in the wrong LAYER. It belongs in the prose
of a richer `folk`, not in a skin of its own - the rung is already *called*
`changeling` in the branding-free canonical layer, and `folk`'s blurb already
carries the premise ("some of what you know about yourself stopped being true
while you slept"). A skin would be restating in costume what the name and the
blurb already say.

**If that enrichment happens, it ships as a NEW theme key, not as an edit to
`folk`.** Two reasons, and the second is the one that binds. A blurb edit is a
prompt edit, so rewriting the default face orphans every number recorded against
it, and a 200-game run is queued on this one. And keeping both makes the pair
measurable: same polarity, same vocabulary, more prose is a clean richness arm on
an axis none of 1-4 isolates - blurb DENSITY, held apart from valence and from
which fiction it is.

**What this repo brings that a prompt-level study does not.** Gate #1 makes
information equality a machine-checked property rather than an assumption, so a
behavioural difference cannot be a leak. Fallback rates are recorded per run and
void above 10%, so a "refused to deceive" cell cannot be a parse failure wearing a
moral face - which is the obvious way this result gets faked. And the criterion can
be pre-committed the way gate #3b already was.

## Prior work - verified 2026-08-25, read before designing arm 3

All four opened and confirmed; identifiers are exact so nobody re-searches for them.

- **Hagendorff, "Deception Abilities Emerged in Large Language Models"**,
  arXiv:2307.16513, PNAS 121(24), doi:10.1073/pnas.2317967121 (2024). **The
  closest prior result, and it constrains the design.** It reports that eliciting
  Machiavellianism in an LLM alters its propensity to deceive - so "manipulating
  the fiction moves deception rates" is ALREADY SHOWN, single-agent. Arm 3 must
  therefore not touch the seat's persona or traits; if it does, this is a
  replication wearing a new skin. The one thing left unclaimed is the valence of
  the ACT with the agent's character held fixed.
- **Park, Goldstein, O'Gara, Chen, Hendrycks, "AI Deception: A Survey of
  Examples, Risks, and Potential Solutions"**, arXiv:2308.14752, Patterns (2024).
  Survey; defines deception as systematic inducement of false beliefs in pursuit
  of an outcome other than truth. Covers CICERO. Use its definition rather than
  coining one.
- **Meinke, Schoen, Scheurer, Balesni, Shah, Hobbhahn (Apollo Research),
  "Frontier Models are Capable of In-context Scheming"**, arXiv:2412.04984
  (2024). Six agentic evals; covert vs deferred subversion. Nearest neighbour for
  eval DESIGN, not for the question.
- **Pan, Shern et al., "Do the Rewards Justify the Means? Measuring Trade-Offs
  Between Rewards and Ethical Behavior in the MACHIAVELLI Benchmark"**,
  arXiv:2304.03279, ICML 2023 (oral). 134 choose-your-own-adventure games, half a
  million scenarios, reward-vs-ethics tension. Nearest neighbour for the SETTING.

**So the contribution, if any, is narrower than it first looked.** Not "does fiction
move deception" - Hagendorff answers that. What is left: whether the moral valence
of the act, with persona held fixed, moves deception in a MULTI-AGENT game where
information isolation is machine-checked rather than assumed, pre-registered, and
reported with its fallback rate. Workshop-paper shaped at most, and only if the
effect survives arm 3. If arm 3 shows nothing, that is the honest result and it
ships as one.

**Precondition: not before gate #3 is called.** Same reasoning as every other
measured change - and gate #3's own N problem binds here twice as hard, because
this needs four arms rather than one. It is an argument for doing ONUW first (~10-15
calls a game against cabal's 80-220), not for running it sooner.

See also `prior-work.md` (AvalonBench, and HARBOR on persona dynamics).
