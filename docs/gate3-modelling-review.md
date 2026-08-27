# Modelling review - 2026-08-26

## Resolution - read this first

**Closed 2026-08-27. Every ranked change landed, and the gate this review was
sharpening was then abandoned on a finding the review did not reach.** What
follows the divider is the review as written, kept dated and unedited because the
argument is what makes the current scorer legible - not because it describes
current code. It does not. **Its line citations are stale**: `run_games.py` moved
under them when the fixes landed, so read them as pointers to functions, never as
line numbers.

Where each ranked change lives now:

| Ranked change | Landed as |
|---|---|
| 1. `p_clean` on the blind population; watcher excluded | `score()` builds `strata` keyed by `knowledge_class` and takes BOTH terms from each stratum. The watcher is its own `aura` stratum, printed beside the gate by `_strata_lines`. The correction is recorded in the comment above `strata`, with the seed-1000 numbers that motivated it |
| 3. Interval, cluster treatment, min-n | `bootstrap_discrimination` resamples GAMES; the verdict gates on the interval floor. `_ci_floor` returns `None` rather than 0, `_blind_line` prints `REFUSED`, and an empty cell can no longer pass or fail a gate |
| 4. Hunter baseline from the legal set | Averaged over each hunt's own `legal_targets`; `None` when no hunt carries the field, which fails the gate CLOSED |
| 5. Over-sabotage denominator | Sunk missions **on which the game continued**; the free rows are reported as their own line rather than dropped |
| 6. Reframe over-sabotage's normative claim | **Landed 2026-08-28 (S9).** The docstring no longer argues against itself: the irreducible-rate half is stated as holding only for a pair that finds NO convention, so the normative count for a capable pair is ~0 and the observed 39-45% reads as "the pair failed to find a convention" rather than as an equilibrium that forbids zero. No number changed |
| 2. Un-bundle the need-disclosure from the rerun (7.1) | Moot - the rerun it protected was for a gate since abandoned |

**The knowledge classes shipped as `none`/`aura`/`identity`**, not the
`none`/`magic`/`evil` this review proposed. Same three strata, functional keys.

**And the finding that ended it, which is not in this document.** The re-score
below (`+13.57% -> +2.53%`) was confirmed, and then superseded. Two post-fix runs
put the binary blind figure at +19.94% and +18.11%, both clearing zero - but the
off-team cell, the only one free of the self-membership confound this review
raises at follow-up §6, came back +9.65% (n=6) and +18.08% (n=8), **splitting in
opposite directions across the two runs**. The unconfounded estimator accrues at
~0.4 votes per game and no table size fixes it, because at 5 seats a clean
3-person team holds all three good seats. Gate #3a was abandoned at every table
size on 2026-08-27; the graded taint slope is the gate that remains, and gate #3b
got the campaign. This review treats the self-membership confound as a bias to
acknowledge; it is a sampling floor, and that is what killed the gate.

`RESUME.md` is the live account and this file is not - where the two disagree,
`RESUME.md` wins. The arithmetic behind the sampling floor is `eval/gate3_arithmetic.py`.

---

Scope: the six claims as posed, against `eval/run_games.py`, `eval/audit_decisions.py`,
`games/cabal/referee.py`, `games/cabal/player.py`, `docs/player-counts.md`, RESUME.md.
Verdicts first, argument after. The two findings that should change numbers are in
claims 1 and 7.1.

---

## 1. Blind-split as the gate #3a statistic - OVERSTATED, and the asymmetry is a real bias

**Verdict: the motivation is right, the implemented statistic is not the one argued for.
The `p_clean` asymmetry inflates `discrimination_blind`, and the report's "free of both
biases" comment (run_games.py:287-294) is false as written.**

The argument for splitting is sound: handed knowledge and concealment both live in the
informed-tainted bucket, so removing informed votes from the tainted term removes both.
But the statistic actually computed is

```
discrimination_blind = p_clean(ALL good seats) - p_tainted(blind good seats only)   # run_games.py:204-213, 242
```

and the clean term is contaminated by exactly the bias the split exists to remove:

- On a clean team, `knew_evil_on_team` is structurally False (the intersection at
  player.py:370 is empty when no evil is on the team), so no "blind" filter on clean
  votes is even expressible with the recorded field. But the seer is NOT blind on a
  clean team - at 5 seats it sees both evils (roles.py:34, both evil roles default
  `seen_by_seer=True`), so it *certifies* every clean team as clean. Its ~always-approve
  on clean is handed knowledge, and it sits in `p_clean`.
- Magnitude: 1 of the 3 good seats is the seer. If blind seats approve clean at
  `b` and the seer at ~1.0, the pooled `p_clean` is inflated by roughly `(1-b)/3`.
  At b=0.6 that is ~13 points - the same order as the blind figure being gated
  (+13.57% on hunt20, +13.7% on the q36 12-game run). A material share of the blind
  number can be the seer's clean-side certification, not blind deduction.

**Correct treatment:** make the two terms the same population. Either filter both
sides to seats holding no `"evil"`-label night knowledge (equivalently, role key
!= seer - the assignment is in the record), or record a symmetric per-vote field
(`seat_had_evil_knowledge`, not `knew_evil_on_team` which is team-conditional).
`discrimination_blind = p_clean(blind) - p_tainted(blind)`. Expect the number to
drop; per the repo's own doctrine that drop is the truer number.

Second contamination, smaller: the **watcher is not blind**. It is told two seats
carry an aura, one of which is the mimic (roles.py:34-37). A watcher rejecting
aura-carrying teams is acting on handed (ambiguous) knowledge, and it counts as
blind because only labels `evil`/`fellow-evil` feed `knew_evil_on_team`
(player.py:362-363). Direction: inflates blind discrimination. At 5 seats the
"blind" bucket is watcher+loyalist, so up to half its votes carry this. Either
exclude the watcher from blind, or report it as its own stratum.

**On the statistic itself:** a raw difference of proportions with no interval and a
`> 0` gate (run_games.py:337) is a sign test on a point estimate. That is
inconsistent with gate #3b, which demands a Wilson floor above baseline. +0.5% on
40 votes would "pass" 3a. Two fixes, both cheap: (a) report a Newcombe/Wilson
difference interval and gate on its floor > 0; (b) note that votes are clustered
(same seat votes many times per game, games share a seed lattice), so the honest
interval is a per-game bootstrap or cluster-adjusted - independent-Bernoulli
n=387 overstates the evidence. The pre-committed-criterion discipline applied to
the hunt should apply here; today 3a is the soft half of a gate whose other half
is hard.

---

## 2. The 1/3 hunter baseline - SOUND as a null; the gate is honest but nearly unfalsifiable at this N, and the constant is a trap

**Verdict: SOUND on the null, with three flags.**

The null is right. `RandomPolicy` HUNT (player.py:129-136) excludes self + the
night-named ally, leaving the 3 good seats, one of which is the seer -> 1/3.
`validate_hunt` (referee.py:455-465) now refuses exactly the same two seats, so
the model's legal action set equals the control's. The null hypothesis "the hunter
uses only its entitled knowledge and nothing from play" is the correct no-deduction
null, and conditioning on reaching the hunt phase does not move it (given ignoring
play, the target is uniform on 3 whatever selected the game).

Flags:

1. **Underpowered by design, and "not shown" is doing double duty.** At n=9 the
   Wilson floor clears 1/3 only at 6/9+ (~67% observed). At a true 60% hunter that
   is ~50% power; at a true 45% essentially none. So "not shown" conflates "at
   chance" with "cannot be distinguished from chance at this N". The pre-committed
   criterion (RESUME:253-273) handles this correctly - no peeking, respecify the
   metric - so the *process* is defensible. But the report line
   (run_games.py:301-303) prints the CI without printing what the gate could
   detect; a reader sees "33.33%, chance 33.33%" and reads "hunter is at chance"
   when the run cannot support that reading either. The graded-hunt respecification
   is the right fix; until then the verdict line should say "underpowered below
   ~16 hunts" rather than implying an evidential null result.

2. **`hunter_baseline: 1/3` is hardcoded (run_games.py:248) and the 33.33% in the
   report string (run_games.py:303) likewise.** Both are only correct at 5 seats
   with a hunter that knows its ally. At 7p/3-evil the legal set is 4 (baseline
   1/4); under the queued blind-evil variant (`sees_fellow_evil=False`) it is 4
   at 5 seats too - `RandomPolicy` and `validate_hunt` both derive from
   `entitled_knowledge` and will silently agree on the new set while the scorer
   keeps gating against 1/3, in the flattering direction. Compute the baseline as
   `1/len(legal_targets)` from the same source the policy uses.

3. Already flagged in RESUME but worth repeating because it bounds the current
   number: the 3/9 was scored under the old rule (self-target legal, so the model
   guessed from 4 while the control guessed from 3). The standing 33.33% is not a
   clean measurement against its own printed baseline. The rerun is the fix -
   but see 7.1, the rerun is no longer single-variable.

---

## 3. Over-sabotage as anti-coordination - (a) OVERSTATED, (b) SOUND with a scope note

**(a) "the ideal count is NOT zero" - true only for convention-less symmetric play,
and it contradicts (b) as stated.** The game (2 evils, need=1, no channel) is a
volunteer's-dilemma variant: it has a symmetric mixed equilibrium with irreducible
double-fails, AND asymmetric pure equilibria (designated failer) with zero. (b)
correctly says a focal point selects the asymmetric equilibrium and is derivable:
both evils know both identities (`sees_fellow_evil=True`), the proposal is public,
so "lowest-numbered evil on the team fails" is common knowledge between them with
zero communication. If (b) holds, the ideal count for capable reasoners IS ~zero.
So (a) is defensible only as "a nonzero count is not a rules bug" - the
audit_decisions.py:69-98 docstring gets this framing right ("some double-fail rate
is irreducible" is the part that overreaches; irreducible only if no convention is
found, and finding one is precisely the reasoning capability being priced). Keep
the count under COST, but the normative benchmark for a strong model is ~0, not
"some".

**(b) survives the information-leak question.** The convention leaks nothing
incremental to the good side because card attribution is never public
(referee.py:404-407: only the count is emitted). Good observes the same "1 fail"
under a focal-point pair as under a lucky mixed pair; the convention only moves
mass from {0 fails, 2 fails} to {1 fail}. The 0->1 shift is the sabotage margin,
not the coordination margin - whether to sink the mission at all is a separate
decision the convention does not touch, so "always exactly 1 on tainted teams"
does not follow from adopting it, and the succeeded-mission-certifies-clean leak
is a property of the sabotage policy, not the focal point. No repeated-game leak
either: which evil played the card is unobservable, so there is nothing for good
to condition on.

**One correction to the count itself:** `over_sabotage` (audit_decisions.py:87-98)
counts `fails > need` on every mission, including the mission whose fail is evil's
THIRD - the game ends there (referee.py:412-413), the identification cost is never
paid, and a double fail is strictly costless (even weakly good: it guarantees the
win against a miscount). Those rows are not anti-coordination failures. Condition
the count on the game continuing (fails-so-far < 2 before resolution) before
quoting 12/63 or 41% as "free information handed over".

---

## 4. Concealment - SOUND, and the case is stronger than stated

**Verdict: SOUND for this ruleset.** Two facts make it near-decisive rather than
merely plausible:

1. **Votes are public with attribution** (referee.py:366-369 prints "approved by
   [ayes]") and **the hunter knows the ground-truth taint of every historical
   team** (it knows itself and its ally). So the hunter can compute every good
   seat's exact clean/tainted vote split from the public record. A seer that
   discriminates perfectly is not "at risk of a tell" - it is *identified by
   deterministic computation* by any hunter that thinks to do it. Concealment is
   not a style choice in this ruleset; against a competent hunter it is the only
   thing standing between a good 3-mission lead and a guaranteed steal.

2. **The mission-EV cost is only paid when pivotal; the tell is emitted always.**
   A vote passes at 3/5, so the seer's approve changes the outcome only when the
   other four split 2-2. An approve on a tainted team in a non-pivotal spot costs
   ~nothing in mission EV and buys record-level cover unconditionally. So the EV
   arithmetic is lopsided: concealment is worth it whenever
   dP(hunter misses) x P(reach hunt | strategy) outweighs the *pivotal-case-only*
   mission loss, and the pivotality discount makes the left side win at almost any
   plausible parameterisation. 7/76 (~9%) occasional cover-approvals is consistent
   with a sensible mixed strategy, and the observed private reasoning quoted in
   RESUME says the model is doing it on purpose at least once.

Corollary already half-drawn in the repo: this permanently caps what pooled gate
#3a can mean, because optimal seer play *should* score as imperfect
discrimination. One more reason the blind split (fixed per claim 1) is the gate.

---

## 5. Table-size arithmetic - SOUND

Recomputed from scratch; every cell checks.

- 5p, 2 evil, sizes (2,3,2,3,3): P(clean) = C(3,k)/C(5,k) = .3/.1/.3/.1/.1,
  mean 0.18; x3 good voters = 0.54. Matches docs/player-counts.md:45.
- 7p, 3 evil, sizes (2,3,3,4,4): 6/21, 4/35, 4/35, 1/35, 1/35, mean 0.1143;
  x4 = 0.457. Matches :46.
- 8p, 3 evil, sizes (3,4,4,5,5): 10/56, 5/70, 5/70, 1/56, 1/56, mean 0.0714;
  x5 = 0.357. Matches :47.

Team sizes match Avalon's published tables. 0.36/0.54 = 0.667, so "~two-thirds"
holds, the "~60% more calls" is right on speakers per round (8/5), and the
direction-vs-magnitude caveat about non-random proposals is correctly stated. The
conclusion - table size is orthogonal to the binding constraint, the fix is graded
taint - follows. One sharpening: under LLM leaders the proposal distribution is
endogenous to play, so P(clean) per vote event is also a *behavioural* outcome,
not just combinatorics; the doc's parenthetical covers this adequately.

---

## 6. Gate #2 conditionality - SOUND as refusal-to-overclaim, but the sharper falsifiable design exists and is cheaper

**Verdict: SOUND, not unfalsifiable - but it is the second-best design.**

The measured basis is real: against chance voters, evil wins ~65% with zero
deception, so an unconditioned evil win rate measures the baseline, and deception
has no channel to move a chance voter anyway. Refusing to read gate #2 in that
regime is honest, and it is not unfalsifiability - gate #2 remains falsifiable
*in the regime where its premise is defined* (a deceivable opponent). The
five_rejects decomposition (run_games.py:188-197, reported by_path) already guards
the other pollution: 5/20 evil wins by deadlock are not deception either way.

Three flags:

1. **The contrast design answers the question without waiting on gate #3's
   binary.** Deception's own controlled measurement is `--arm llm` vs
   `--arm llm-good` on the same seeds: good live in both, evil live vs random,
   difference in evil win rate (and in missions-failed path share) is evil's
   contribution against a *fixed* opponent population. That is evidence of
   effective evil play even when good's discrimination is marginal, and it uses
   arms that already exist. The conditionality then softens from a hard refusal to
   "the headline unconditional rate is only quotable once #3 holds", which is the
   defensible part of the claim.

2. **The conditioning inherits gate #3a's weakness.** Once claim 1's fixes land,
   fine; today gate #2 can be unlocked by a sign-test 3a (`> 0`, no interval) and
   an adequately-powered 3b - the gatekeeper is softer than the gate it guards.

3. **The ~65% is a property of the control knobs, not the game.**
   `RandomPolicy(fail_rate=0.5, approve_rate=0.7)` (player.py:109-110) sets that
   baseline; different knobs give a different number. Fine as an existence proof
   ("a non-deceiving evil already wins a lot"), wrong if ever quoted as the
   game's intrinsic evil floor. Also `rate_ok`'s 5% CI-floor bar
   (run_games.py:341) is arbitrary and pre-declared nowhere I can find - it
   deserves a line in the pre-committed criterion the way 3b's bar got one.

---

## 7. Not asked, and it matters

### 7.1 The seed-1000 rerun is already two-variable - the RESUME's own prediction is broken

RESUME:44-56 commits to "expect the re-run to shift hunter accuracy slightly and
nothing else", and RESUME's over-sabotage item (:200-218) commits to landing the
`need` disclosure "after gate #3 is called... (a) must land first and alone". But
commit `c43274e` (2026-08-26, "grade gate 3a on the blind half, **and tell the
mission its threshold**") already put the need-disclosure into the live MISSION
prompt (referee.py:532-544: "This mission fails if {need}..." plus the evil stake
naming `{need}` again) in the same commit as the scorer change. The rerun will
therefore differ from hunt20 in (at least) hunt legality AND mission-phase
information, so:

- the "if it moves anything other than the hunt, something else changed" tripwire
  will fire by construction, and
- over-sabotage rate, fail-card counts, evil win path mix, and (via the
  good-exploits-blunders confound RESUME:219-225 documents) gate #3a itself are
  all expected to move.

Either revert the prompt half of `c43274e` until the hunt-only rerun lands, or
rewrite the rerun item to name both variables and drop the single-variable claim.
Silently keeping both makes the next comparison unattributable - the exact failure
the repo's own measured-change discipline exists to prevent.

### 7.2 `discrimination_blind` degenerate denominators pass the gate silently

`p_blind` defaults 0.0 when `blind_tainted` is empty (run_games.py:212-213), and
`p_clean` 0.0 when `clean` is empty. A run with zero blind tainted votes reports
`discrimination_blind = p_clean > 0` and PASSES n_3a; a run with zero clean votes
reports a negative number and fails it - both are "no data", scored with opposite
signs. Gate n_3a should require minimum n on both denominators (the report already
prints them; the verdict ignores them).

### 7.3 The pooled/blind comparison in prose mixes two different clean terms

Every quoted pair ("+31.55% pooled, +13.57% blind") shares one `p_clean`, so the
difference between pooled and blind is *entirely* a tainted-side statement. Once
claim 1's fix lands, re-derive both from the blind population before narrating the
gap as "handed knowledge + concealment" - some of the current gap narrative will
turn out to live on the clean side.

### 7.4 Small, worth a line each

- **Vote CIs are absent everywhere** while game-level and hunt-level numbers get
  Wilson. If the gate is votes, votes need the interval (clustered, per 1).
- **`third_person_self`** (audit_decisions.py:149-165): the first-person strip
  runs once, so "I'm seat 1, but seat 1 was accused" still fires; acknowledged
  HEURISTIC, fine - but note the regex `\b(?:...|as|being)[, ]+seat \d+` also
  strips genuinely third-person "as seat 4 argued", under-counting. Cosmetic.
- **`outed_own_role_in_public`** matches the functional key (`seer`, `hunter`)
  against themed speech; under the 1984 skin players speak the theme's role
  names, not the keys, so this check reads near-zero on themed runs by
  construction, not by virtue. Match theme names too or scope it to `--theme
  plain` runs.
- **`hunt_named_impossible`** derives allies as "all other evils"
  (audit_decisions.py:57-59) - correct at 5p, but under a future
  `sees_fellow_evil=False` variant it would flag legal hunts as regressions.
  Same class of trap as the hardcoded 1/3; both assume the current knowledge
  model in what claims to be a rules-level check.
- **Gate #3 whole requires the full `llm` arm** (both sides live,
  run_games.py:332-340), i.e. the only arm that can pass the deduction gate is
  the arm the README warns measures deduction and deception entangled. For 3a
  that is arguably the *right* population (deduction against live deceivers is
  the claim), but the README's entanglement warning and the verdict logic
  deserve one connecting sentence so a reader doesn't take them as contradictory.

---

## Summary of required changes, ranked

1. **Fix `p_clean` to the blind population** (claim 1) - the current blind gate is
   inflated by the seer's clean-side certification; the headline blind numbers
   will drop and must be re-derived. Exclude or stratify the watcher.
2. **Un-bundle the need-disclosure from the hunt rerun** (7.1) or re-scope the
   rerun's prediction - today's plan violates the repo's own one-variable rule.
3. **Interval + cluster treatment on 3a; min-n on both denominators** (1, 7.2).
4. **Derive the hunter baseline from the legal target set, not 1/3** (claim 2).
5. **Condition over-sabotage on the game continuing** (claim 3) before quoting 41%.
6. Reframe (a) of the over-sabotage story: ideal ~0 via the focal point; the
   count prices failure to find it, not an irreducible equilibrium rate.

---

## Follow-up: corrected p_clean design

Answers in the order asked, then two things the design misses - the second one
(self-membership) is a third confounder of the same rank as the seer one.

### 0. Do this before any of it: re-score, don't re-run

Every input to the corrected statistic - `assignment`, per-vote `seat`,
`approved`, `team_has_evil`, plus the proposal in `public_events` - is already in
the hunt20 JSONL. This is a scorer-side change; recompute the corrected
discrimination on the existing records first. It answers the magnitude question
(and my direction prediction below) empirically, today, for zero GPU-hours, and
it tells you whether the interval machinery in (5) is even load-bearing before
you build it.

### 1. The field - right idea, wrong type

A bool derived from labels `{"evil", "fellow-evil"}` works at 5p but bakes in the
current knowledge model twice over (same trap as the hardcoded 1/3). Record the
seat's **knowledge class** instead, derived from `entitled_knowledge(seat)` at
vote time: `"evil"` (any evil-identifying label), `"magic"` (aura only),
`"none"`. One field, and blind/watcher/seer strata, options (a)(b)(c), and every
future variant fall out of it without another schema change. Blindness predicate
= `class == "none"`, i.e. *the night told this seat nothing*, which is the
definition the prose has been using all along. Keep `knew_evil_on_team` for the
audit, agreed.

### 2. Residual biases in `p_clean(blind) - p_tainted(blind)`

Handed knowledge: none left **at the seat level** once the watcher is out (see
3). But one channel survives by construction and should be scoped, not fixed:
**seer-originated public signal**. Clean teams are disproportionately
seer-proposed (it knows which teams are clean), and its votes and speech are
public. A blind seat that approves teams proposed by a seat it has come to trust
is doing real social deduction - but it is the seer's knowledge one hop removed,
not autonomous taint detection. You cannot remove this without removing the game;
its converse (a concealing seer injecting misleading approvals that DEFLATE blind
discrimination) is equally structural. So the claim wording must match the
measurement: gate #3a-blind measures *information reaching blind seats through
play*, not *blind seats detecting evil unaided*. That is the right thing to
measure for a social deduction harness - say so once, in the report comment that
currently says "free of both biases".

Concealment: blind seats have no hunt exposure (only the seer is huntable), so no
first-order concealment bias. Second order: a **decoy watcher** - voting
informed-looking to draw a hypothetical hunt onto itself - would distort the
watcher stratum upward. One more reason the watcher is not blind (3).

### 3. The watcher - (c), and (a) is worse than it looks

Not (a). The watcher's knowledge is stronger than "ambiguous aura": at 5p it
knows the aura pair {seer, mimic} contains exactly one evil AND, by elimination,
that the two non-aura, non-self seats contain exactly the other one. So it
*certifies taint outright* on some team shapes - both aura seats on one team, or
both non-aura others on one team, is a team it KNOWS is tainted - and it can
bound every other team's taint probability well off the blind prior. That is
handed structural knowledge, sometimes certainty, and it sits in half the
"blind" votes at 5p. Direction: inflates. Magnitude: checkable on existing
records (compare watcher vs loyalist strata - point 0), and my expectation is it
matters, because the certainty cases are not rare among 2-seat teams.

Not (b) as a silent collapse either - your n objection is real. So (c): **gate on
the `"none"` stratum (loyalist at 5p), print the `"magic"` stratum beside it.**
If the loyalist-only n is too thin to gate on - likely, see 5 - the honest
conclusion is that this is the thin-denominator problem again, and the fix is the
graded-taint respecification already queued in docs/player-counts.md:56-60, not
re-admitting a contaminated population to buy n. A wide interval on the right
population beats a tight one on the wrong population.

### 4. Min-n floor: gate on the interval and the floor question dissolves

Any fixed floor (20? 30?) is arbitrary and will be argued with later. If the
verdict gates on the difference-interval floor > 0 (5), the min-n guard is
subsumed: a thin cell produces a wide interval that cannot clear zero, and the
verdict degrades to "not shown" automatically, with the power statement built in.
Keep exactly one explicit guard: **either denominator zero -> hard refusal**,
worded like the fallback void ("gate #3a not shown - no blind votes on clean
teams"), three-valued and never a silent False, and definitely never the current
fail-open 0.0 (run_games.py:212-213). Distinguishing "refused" from "failed" in
the output matters: a fail invites tuning, a refusal invites more data.

### 5. Interval: per-game bootstrap as the gate, Newcombe printed beside

Implement both; gate on the bootstrap. Reasons:

- **Clustering unit is the game**, full stop - seats nest within games (seat 3 of
  game 1 shares nothing with seat 3 of game 2), so resampling game indices with
  replacement handles both seat- and game-level correlation at once. Stdlib-only,
  ~30 lines, fits the repo's no-deps rule; Newcombe is closed-form and worth
  printing as the naive reference.
- **Not precision theatre at this N.** ~150 blind tainted votes over 20 games is
  ~7.5 per cluster; with within-game correlation rho ~ 0.2 the design effect is
  ~2.3, i.e. the honest interval is ~1.5x the naive one. A +13% with naive SE
  ~5% has a naive floor near +3% and a clustered floor near -3% - exactly the
  band the current numbers live in, so the correction can flip the verdict.
  Under stratification per (3) the loyalist-only n is ~half that, and the
  clustered interval will likely straddle zero at 20 games. Expect it, and let
  the report say "wider than the naive interval because votes cluster by game"
  so the widening reads as method, not regression.
- Caveat stated up front: a percentile bootstrap on 20 clusters is itself rough
  (the interval's own coverage is approximate). It is still the least-wrong
  option at this N; the real fix is more games or the graded metric.

### 6. The third population issue - yes, and it is not the one you named

Seer-as-leader is the signal-laundering channel scoped in (2). The sharper
selection effect is **self-membership**: a seat votes differently on a team it is
ON (self-trust is rational and observed), and self-membership is mechanically
correlated with taint *for good seats*. At 5p a clean 3-team contains ALL three
good seats, so every blind voter on a clean 3-team is voting on its own team; a
tainted team carries 1-2 good seats, so blind voters are often off it. So
`p_clean(blind)` is partly "seats approve teams they are on", which is
taint-independent self-preference scored as discrimination. Direction: inflates.
Structural nastiness: you cannot fully condition it away at 5p, because off-team
blind votes on clean teams barely exist (only size-2 clean teams leave a good
seat off, and only one). Treatment: report the on-team/off-team split as strata
(the data is in the records - proposal + voter seat), state the residual
confound, and add it to the pile of reasons the graded-taint metric is the real
gate. Do not let the headline imply the corrected number is deconfounded.

### 7. Direction and magnitude

Drop is the right central prediction, with one checkable inversion scenario.
Arithmetic: with roughly equal vote counts per good seat, p_clean(pooled) =
(2 x p_clean(blind) + p_clean(seer)) / 3, so the correction moves the clean term
by one third of the seer-vs-blind clean-approval gap. If the seer certifies clean
at ~95% and blind seats sit near 70%, that is ~8 points: **+13.57% -> roughly +5
to +9, comfortable-to-marginal**, which is why (5) is load-bearing. The inversion
scenario: a seer noising its record by rejecting some CLEAN teams (concealment
spent on the clean side) would put its clean-approval BELOW the blind seats' and
the correction would RAISE the number. I rate it unlikely - rejecting clean costs
mission EV in the direction good cannot afford - but it is one groupby on the
existing JSONL (point 0), so check rather than predict. The watcher exclusion (3)
and the self-membership acknowledgement (6) both push further down; if the
corrected, stratified, clustered number still clears zero at 20 games, that is a
result worth believing. If it does not, that is the metric telling you what the
power notes already said.

---

## Re-score on existing records (2026-08-26, no new games)

Per follow-up point 0. Inputs already in `eval/records/hunt20-q36.json.jsonl`;
knowledge class derived from `assignment` (seer -> evil, watcher -> magic,
loyalist -> none). 4000-resample per-game bootstrap, seed 7.

| stratum | discrimination | n clean / tainted | 95% CI |
|---|---|---|---|
| pooled, all good (old headline) | +31.55% | 159 / 228 | [+22.78%, +39.68%] |
| **class none (loyalist) - the gate** | **+2.53%** | 53 / 76 | **[-13.45%, +18.04%]** |
| class magic (watcher) | +7.00% | 53 / 76 | [-9.71%, +23.46%] |
| class evil (seer) | +85.13% | 53 / 76 | [+77.14%, +92.77%] |

`p_clean` by class: seer 94.3%, loyalist 73.6%, watcher 62.3%.
Self-membership split, loyalist: OFF-team -13.83% (n=9 clean / 49 tainted),
ON-team +3.20% (44 / 27).

Cross-check: 53x3 = 159 and 76x3 = 228 match the scorer's own pooled counts, and
the old "blind" n=152 tainted is exactly watcher + loyalist - confirming the old
figure pooled two strata and used an unfiltered clean term.

**Conclusion: gate #3a is NOT SHOWN on the corrected statistic.** The whole
signal was the seer spending handed knowledge (+85%). No inversion scenario -
p_clean(seer) 94.3% confirms certification rather than record-noising. The
interval says 20 games cannot settle it either way, which makes the graded-taint
respecification the only route to a resolvable gate at achievable N, not an
optimisation.

*Landed in the scorer 2026-08-27, and the graded slope became the gate. The last
line of this section - that 20 games cannot settle it either way - held, and went
further than predicted: see the Resolution at the top.*
