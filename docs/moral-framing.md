# Moral framing as a measured variable

Written 2026-08-25. Unrun. Arrived sideways, out of a licensing question about the
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
  3. a rich fiction of equal length and register with sabotage VILLAINOUS - the
     saboteurs are the betrayers, the majority are the wronged. Same word count,
     same density of loaded nouns.
  4. optional: rich fiction, morally NEUTRAL - a sport, a heist with no victim.

Polarity is arms 2 vs 3, and only 2 vs 3 - they differ in valence and in nothing
else. Richness is 2+3 vs 1. Without arm 3 the experiment cannot make a claim about
morality at all, and that is the difference between a result and an anecdote.

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
