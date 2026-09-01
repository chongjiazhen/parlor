# Design notes and reference

The index of this directory, moved out of `queue.md` 2026-08-28. Durable material
lives beside the code, not in the queue; `queue.md` keeps the open rows.

**When this flat directory should become folders.** Nothing here is broken by 23
files in one namespace - the defects this layout has actually produced were stale
claims and a partly-true index, which folders do not fix. The split worth making,
if one is, is the two classes with OPPOSITE maintenance rules: docs that must
track the code (`action-channel`, `content-packs`, `model-facing-text`,
`evidence-discipline`, `preset-axes`, `information-model`) against dated records
that must never be edited (every criterion and verdict, `measurements`, `slices`).
Four triggers, any one of which flips the answer - the first is checked by
`scripts/hygiene-check.sh` as an advisory and the rest are judgement:

1. This file passes **150 lines**, at which point the index that stands in for
   folders is skimmed rather than used.
2. A doc has **two plausible homes** and the answer matters - i.e. it is cited
   from two different reader contexts.
3. A **second contributor**, or external readers after publishing. Folders are a
   coordination tool; a single author with `AGENTS.md` as the map does not need
   them, and someone who cannot ask does.
4. **~40 files**, as a crude backstop on scanning a flat directory.

**Three of the files below are the queue's own drained halves** rather than design
notes - what landed, what was measured, what was settled - and they are listed here
because this file claims to be the index of the directory and an index that is
partly true is worse than none.
- `docs/slices.md` - the closed slice ledger, S1-S7 and S9-S11, struck and kept
  because live rows cite them by name.
- `docs/measurements.md` - the dated numbers, the route call and the backend
  notes. **Read before trusting any number in this repo.**
- `docs/decisions.md` - settled calls, applied criteria, and the CALLED-gate
  table plus the do-not-re-derive list (out of `queue.md`, 2026-09-01).
- `docs/open-arms.md` - 2026-08-28. The argument behind each open row in
  `queue.md`, which carries only the ask and the entry condition. **Read the
  entry for a row before taking that row**, not before picking one.
- `docs/worklane.md` - 2026-08-29. Which open rows may be handed to a delegated
  worker, the worktree that contains one, and the three classes that may not be
  delegated at all. **Read it before dispatching anything**, not after.

- `docs/information-model.md` - 2026-08-28. The settled vocabulary for what this
  repo calls entitlement, cited by identifier: information set, percept,
  synchronous perfect recall, the chance move that turns incomplete information
  into imperfect, public versus private observation. Gate #1 in one line - a
  seat's bytes must be a function of its information set - and the three rungs as
  one percept function of increasing generality. Carries its own read-depth note;
  two citations are deliberately not first-hand and nothing rests on them.
- `docs/model-facing-text.md` - the two rules for a string a model actually reads:
  prompt the positive, and a prompt edit is a measured change, not a cleanup.
  Read before touching `core/backends.py` or either game's `referee.py` /
  `player.py`.
- `docs/action-channel.md` - why free-text JSON stays the action channel, and the
  kernel/adjudicator split the RPG rung needs. Read before adding a second game's
  phases or touching `parse_action`.
- `docs/durf-rung.md` - the cheap version of the endgame rung, scoped 2026-08-27:
  a DURF session with a deterministic kernel under a model adjudicator, the
  False Pass / False Check / refusal number it produces against CoC-Seduce's
  9.58% floor, and the finding that DURF's secrets belong to the WORLD rather
  than to seats, which is the first evidence for fact-keyed entitlement in
  `core/`. Read before scoping any RPG rung, and before widening `find_leaks`.
  Its kernel table is pinned to DURF 2.2 and the doc now carries the fetchable
  source URL plus the version line to check on any re-read.
- `games/durf/fixtures/` - that rung's INSTRUMENT, labelled 2026-08-27 before any
  model ran: 48 declarations and 12 morale events, each carrying the rule it
  rests on. **Read its README before quoting any number from it.** Degenerate
  baselines are **61.9% always-roll / 38.1% never-roll** over the 42 declarations
  that admit a roll answer (54.2% / 33.3% over all 48) - the first draft's
  "never-roll 46%" pooled the six refusal traps into the no-roll bucket and is
  retracted there. Re-derived and source-verified the same day, which killed
  three of the six traps: the slot costs made `d013`, `d017` and `d018`
  satisfiable, so a model ruling them correctly would have scored a False Pass.
  The state moved to the labels, never the reverse, and every `slots_used` is now
  derivable from a `slot_costs` block. **The scorer landed 2026-08-28**
  (`eval/durf_score.py`); there is still no durf engine, and nothing here needs
  one - the fixture is 60 independent items against a fixed scenario.
- `docs/moral-framing.md` - the theme-polarity experiment, its confound, the
  verified deception/framing prior work, the name-form axis, and **§The changeling
  skin set, which owns every skin's design and sourcing rules** (moved out of this
  file 2026-08-28 - it was 134 lines of design in a queue). Arms 3 (`1984-inv`) and
  4 (`drill-en`) on cabal and the whole changeling set are BUILT and unrun; read it
  before running any of them, and before editing any blurb - the faces are
  length-matched on purpose and frozen.
- `docs/content-packs.md` - the engine/content split the endgame rung needs: what
  ships, what stays local, why the example pack is required rather than a courtesy,
  and why "local" is not the same as "untransmitted". Read before laying out
  `games/<rung>/`, not after.
- `docs/preset-axes.md` - the question after content packs, answered no: entitlement
  schema, resolution kernel and authority topology are three different kinds of
  axis, only the first is flag-shaped, and a flag list is 2^N unmeasured fallback
  rates wearing one measured number's name. Carries the boundary of the formal
  prior art (`arXiv:2205.00451`).
- `docs/scripted-rungs-cabal.md` - why the control ladder keeps climbing on hand
  rules rather than a learned policy, and the three rungs that follow. Unmeasured.
- `docs/quorum-live4-criterion.md` - **the operative quorum pre-commitment**;
  arithmetic `eval/quorum_live1_verdict.py`. `-live1-`, `-live2-` and `-live3-`
  stand beside it, superseded IN WRITING and unrun: each was retired before
  launch because the instrument changed under it, never after a number landed.
- `docs/belfry-live2-criterion.md` - **the operative belfry pre-commitment**;
  arithmetic `eval.belfry_live1_verdict --criterion live2`. `-live1-` beside it
  is retired on RUNNABILITY not a bar - its settings measure 58.33% fallback
  and fire its own void. Neither is to be edited.
- `docs/belfry-discretion-quality-criterion.md` - S23's pre-commitment, and the
  finding that made it what it is: belfry's setup discretion has NO board-derived
  quality ordering to grade, so what it grades is whether that discretion follows
  a stated rule. Arithmetic `eval.belfry_steering_verdict --criterion s23`. Unrun.
- `docs/player-counts.md` - supported vs best-play sizes per rung, Secret Hitler's
  native blind-evil at 7+, and why a bigger cabal table worsens the denominator.
- **OFF-REPO, path in `CLAUDE.local.md`** - the neighbour list, the positioning
  argument and the raw notes behind both: who else has built this, what parlor
  claims and against whom, the licence and `DEFAULT_THEME` calls, and the ledger
  of what is still owed a first-hand read. **Read before publishing or writing an
  abstract, and before any writeup that quotes a gate #2 or #3 number.** It is out
  of the tree deliberately - see §Outstanding debt - and it does not come back in.
- `docs/reference-policies.md` - what a number is scored AGAINST: the mechanical
  solver (120 assignments, hard constraints only), the pinned spec and corpus, the
  additive-not-substitutive rule, the heuristic rung, and **§Results plus §The
  control ladder, which carry the three findings of 2026-08-27** - the hunt's
  MECHANICAL denominator is zero by proof, the un-entitled good seats read flat
  against what the record proved, and a 60-line rule out-hunts the model 94.3% to
  48.3% on the model's own records. Read before implementing any reference arm or
  quoting a gate as a fraction. Note §Results carries a same-day supersession: its
  "captured is undefined" line is about the mechanical arm only, and the ladder
  section is where the behavioural denominator lands.
- `docs/evidence-discipline.md` - how this repo handles a number, a citation, a
  run and its own record: the three rules for citing work nobody here has read,
  pre-commitment, why a rate over another gate's outcome is not projectable from
  one draw, and the render-control method that proves a freeze held. Read before
  quoting an outside source, before writing a criterion, and before claiming a
  refactor moved no model-facing byte.
- `docs/gate3a-retired.md` / `docs/gate3b-verdict.md` - cabal's two gate #3
  verdicts, each recomputable (`eval.gate3_arithmetic`, `eval.s6_verdict`). Read
  before restarting any cabal run or quoting either half.
- `eval/durf_rescore.py` - re-audits a stored DURF session against any term set,
  no GPU and no re-run: entitlement is reconstructible from the transcript because
  publishing a fact writes its own text as a referee entry. Prices a sentinel
  change against records already on disk. A counterfactual, never a read.
- `eval/durf_camp1_verdict.py` - the DURF gate #1 criterion as arithmetic,
  written before the campaign landed and pinned by `eval/test_durf_camp1_verdict.py`
  against synthetic records, so the promise cannot drift to fit the result.
- `docs/durf-gate1-criterion.md` - DURF's pre-commitment for the campaign that
  replaces the voided 3/6 read: 100 sessions, the Wilson-floor-clears-50% bar and
  the power arithmetic behind it. Written before the run; not to be edited.
- `docs/changeling-gate3-criterion.md` - changeling's pre-commitment, verbatim and
  not to be edited; the outcome is `games/changeling/RULES.md` §S2 read.
- `docs/gate3-modelling-review.md` - the 2026-08-26 review that sharpened the old
  blind gate, closed on all six items. **Read its header before its body** - its
  line citations are stale.
- `docs/faction-heartbeat.md` - Spike #2 scoped: the typed-fact channel, why it is
  the small version of the adjudicator's hardest part, and the one new gate #1
  failure it introduces (entitlement gains a time axis).
- `docs/reproducibility.md` - two 20-game runs at one seed came back byte-identical,
  so a same-seed repeat cannot measure spread. Read before scheduling ANY run whose
  purpose is variability, and before quoting a "+X% vs +Y%" comparison.
