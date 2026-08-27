# RESUME - open work

Queue only. Done work leaves to git log - **delete the row**.

**One exception, and it is the slice table below: a finished slice is struck
through and annotated, never deleted.** Live rows cite slices by name - S6's
pre-committed criterion rests on "the baseline derived by S3", and four items read
"re-homed 2026-08-27 (S1)". Delete the row and those pointers dangle, which costs
more than the two lines it saves. Everything else in this file follows the rule
above.

What's next:

## Session slices - what one `/new` should take

The queue is 24 open items and a cold session cannot rank them. These are the
units: each is one session's worth, has a stated entry condition, and ends in a
thing that exists. **Take exactly one.** They are ordered by what unblocks what,
not by appeal.

The split that matters is GPU-bound versus attention-bound. A GPU run needs a
launch and a log tail; it does not need a session watching it. So an S with a run
in it should launch first and spend the wait on the paired CPU slice, and the
table says which pairs.

| # | slice | needs | entry condition | done when |
|---|---|---|---|---|
| ~~**S1**~~ | ~~Call cabal gate #3.~~ **CALLED 2026-08-27** - 3a abandoned at every table size, 3b gets one pre-committed 40-game campaign. See the verdict section below. | - | - | done |
| **S2** | **changeling: clean re-run, then 200 games.** The powers re-run (~30m), then the run its blind stratum actually needs (~5h). | GPU all session | none | `RULES.md` table is on clean numbers and a 200-game record exists |
| ~~**S3**~~ | ~~cabal scorer honesty.~~ **LANDED 2026-08-27** - all four derived numbers now come from the knowledge model or the record. The bar for S6 is unchanged (`SETUP_5` legal set is 3, so the derived chance IS 1/3); the audit's role-outing count was near-zero by construction and is not. See the measured rows below. | - | - | done |
| ~~**S4**~~ | ~~Ops hygiene.~~ **LANDED 2026-08-27** - `core/runlog.py` writes `PARLOR DONE rc=N games=L/R elapsed=Ns` from both eval drivers; both games record a fallback's REASON per decision on a `refused` field; the untracked `run-hunt20.cmd` is retired and its exact invocation preserved in `eval/runs/hunt-local.cmd`. Records changed, play did not - the bytes a model receives are identical, so S6 may freeze on this code. | - | - | done |
| **S5** | **changeling: read the 200-game run.** Gate #3 at a real N, the `false` stratum, the sleeper-decoy rate, diverged-vs-intact accuracy. | no GPU | S2 landed | a dated writeup in `RULES.md`, gates called or refused by their own rule |
| **S6** | **The gate #3b campaign - cabal's LAST GPU program.** 40 games, `--seed 2000` then `--seed 3000`, code frozen. Pre-committed bar below. Doubles as the second draw, so it also resolves step-not-slope, the `five_rejects` shift and run-length degradation. **ARM 1 IN FLIGHT since 2026-08-27 12:05 local** - `hunt6a`, seed 2000, `qwen36-35b-a3b-iq3`, detached, log `eval/records/hunt6a.log`, ETA ~18:42 that day. **CODE IS FROZEN AT `2c0e2a3` UNTIL ARM 2 LANDS** - no prompt, scorer or rules edit, and no second GPU job (one card, and S2 wants the same one). Judge it by that log's `PARLOR DONE rc=` line or its JSONL, never by a process probe. **ARM 2 IS ARMED AND WAITING** - `chain-after.cmd` on sentinel `eval/records/hunt6a.json`, detached since 12:16, log `eval/records/hunt6b-chain.log`, bound 1200 polls (~10h) with `on-timeout=refuse` so a hung arm 1 leaves the card idle rather than putting a second 35B on it. **Both arms are therefore scheduled - do not launch either by hand.** If the chain refuses, arm 2 is `eval\runs\hunt-local.cmd hunt6b 20 3000 qwen36-35b-a3b-iq3` once arm 1's log ends in `PARLOR DONE`. | GPU ~13.2h (2 nights) | **UNBLOCKED - S3 landed 2026-08-27**, and the derived bar evaluates to 1/3 on `SETUP_5`, so the pre-committed power table stands unchanged | 3b called or refused by its own rule, and the three draw-dependent items resolved |
| ~~**S7**~~ | ~~Measured prompt variables.~~ **DROPPED as a cabal GPU program** - a paired cabal arm is 13.2h to move a number 3a no longer spends precision on. Re-homed: see the verdict section. | - | - | done |
| **S8** | **Next rung or publish.** 6/7p + information-degrading evils, Spike #2's faction heartbeat, or `docs/prior-work.md` and pre-public hygiene. | varies | S5 done (S1 is called) | scoped in its own session, not here |

**S1 is called, and it freed half the queue.** S6 survives in a changed and
bounded form; S7 and the cloud arm are dead. The verdict and its arithmetic are
the section immediately below - read it before restarting any cabal run.

**Do not mix cabal and changeling in one session.** They have separate `RULES.md`
files, separate scorers and separate baselines, and every number confusion in this
file so far came from carrying one game's intuition into the other's denominator.

## Gate #3 called - 2026-08-27 (S1)

**Gate #3a is ABANDONED at 5 seats and at every other table size; gate #3b gets
ONE pre-committed 40-game campaign and then cabal stops.** Decided on `hunt20c`'s
own interval plus arithmetic on the records already in hand, with no new games.
The instrument was controlled first: the analysis pipeline reproduced the recorded
+8.82%/+9.00% slopes of `hunt20b`/`hunt20c`, their binary figures and all four CIs
exactly, and
reconstructed every vote's team membership from `public_events` with
proposals x 5 == votes in 20 of 20 games. **Every number below is
recomputable**: `py -3 -m eval.gate3_arithmetic`, which prints its own
instrument control first and exits non-zero if the reconstruction stops
checking. A verdict that retires a gate should not rest on arithmetic nobody
can re-run.
- **The reason to stop is NOT that N is unaffordable. It is that the
  affordable N buys precision on a quantity that is not the gate's.** This
  file said "cannot show gate #3a at an affordable N" from `hunt20d` onward;
  that was written before anyone priced it, and it is wrong. Priced
  against `hunt20c`'s own per-game bootstrap SD (4.75% on the graded slope):

  | target | games for a 95% floor above 0 | GPU at 19.85 min/game |
  |---|---|---|
  | at the raw +9.00% effect | ~22 | 7.3 h |
  | if the honest effect is 75% of it | ~38 | 13 h |
  | if the honest effect is 50% of it | ~86 | 28 h |

  Two to four overnight runs. Affordable. The problem is what arrives at the
  end of them.
- **The deconfounded estimator accrues at ~0.3-0.4 votes per game, and no
  table size fixes it.** The self-membership confound is not a bias to
  correct, it is a sampling floor: at 5 seats a clean 3-team holds ALL three
  good seats, so an off-team blind vote on a clean team can only occur on a
  2-person clean team. Measured on both post-fix runs:

  | blind stratum | `hunt20b` | `hunt20c` |
  |---|---|---|
  | all blind (the reported binary) | +19.94% (n=44/71) | +18.11% (n=50/108) |
  | ON-team | +22.01% (n=38/33) | +8.91% (n=42/43) |
  | **OFF-team - the only unconfounded cell** | **+9.65% (n=6/38)** | **+18.08% (n=8/65)** |

  **The two runs put the split in OPPOSITE directions** - `hunt20b` says the
  confounded cell is the flattering one, `hunt20c` says the reverse - on 6
  and 8 off-team clean votes respectively (9 in `hunt20`). That instability
  IS the finding: the cell that would answer gate #3a is too thin to hold a
  sign across two draws, so no amount of reasoning about the direction of the
  confound rescues the headline. Forty such votes is ~100-134 games (33-44 h)
  and a hundred is ~250-330 games, and that is the raw sample count before
  any interval is asked of it. The metric that would actually answer gate #3a
  costs an order of magnitude more than the confounded one, and the
  confounded one is all any affordable run measures.
- **7p and 8p do not reopen it - checked, not assumed.** Off-team-clean good
  votes per vote event, random teams, official mission sizes: 5p **0.120**,
  7p **0.160**, 8p **0.100**. 7p's +33% raw yield is eaten by 40% more
  speaking seats (0.0229 vs 5p's 0.0240 per unit speaking cost) and 8p is
  half as good. This closes the door the 6/7p item left ajar: there is no
  cabal configuration where the honest gate-#3a number gets cheaper.
  Consistent with `docs/player-counts.md`, which reached the same conclusion
  from the clean-team side.
- **A second, independent reason: the declared statistic cannot be repaired
  after the fact.** The scorer calls the graded slope THE GATE, and its floor
  is decided by noise at this N (+0.94% then -0.25% on a point estimate that
  barely moved). The binary blind figure clears 0 in both runs that have it
  (`hunt20b` +19.94% [+6.27%, +32.02%], `hunt20c` +18.11% [+3.52%, +33.53%])
  and is better-specified for a step-shaped response - but promoting it now
  would be choosing the statistic with the results in view, which is the
  `hunt20b` error wearing a third hat. So the strongest 3a evidence in the
  repo sits on a statistic that cannot honestly be declared the gate, and
  buying N does not change that either.
- **What gate #3a is allowed to be reported as, and it is not nothing.**
  "Blind seats approve clean teams more than tainted ones by ~+18pp (binary,
  two runs agreeing), and ~+9pp per additional saboteur; both figures pool
  self-votes with off-team votes and are downstream of seer-originated public
  signal, so they measure *information reaching blind seats through play*,
  not *blind seats detecting evil unaided*. The unaided estimator exists
  (off-team, clean-vs-tainted) but its sample accrues at 0.4 votes/game and
  is unaffordable at this rung." That paragraph is publishable and it is the
  end of the matter - the honest claim was already reachable, and more GPU
  was only ever going to narrow an interval around the wrong quantity.
- **Gate #3b is the exception, because it has no confound of this kind.** One
  hunt per game, a legal target set, one bit. Post-fix runs: `hunt20b` 6/11,
  `hunt20c` 5/9. Pooled 11/20 = 55.00%, Wilson [34.21%, 74.18%] - **which
  clears 1/3 by 0.9pp, and that is peeking, not a result.** The criterion is
  a floor inside one run and three runs pooled after the fact is exactly the
  stopping rule this repo refuses. It is quoted here only to show the
  campaign below is not hopeless.
- **The negation pass, the notebook, theme polarity and mini-personas are
  re-homed, not cancelled.** Each is a prompt change and so a measured
  change; a paired cabal arm now costs 13.2 h to move a number 3a no longer
  spends precision on. They belong on changeling, where a paired 20-game arm
  is ~30 min, or they land nowhere. None may land before the S6 campaign
  finishes - a prompt edit mid-campaign confounds it the way `c43274e`
  confounded `hunt20b`.
- **The cloud arm dies with 3a.** Cloud was wanted because gate #3 read as a
  cloud-scale job. 3b at 40 games is 13.2 h on a pinned local model with
  known attribution, which is strictly better evidence than a time-varying
  `auto` mix. There is no longer a condition worth watching for.
- [ ] **PRE-COMMITTED CRITERION for the S6 gate-#3b campaign (written 2026-08-27,
      BEFORE the run).** Same discipline as the 2026-08-25 criterion, which held.
      - **40 games total: `--seed 2000` (20) then `--seed 3000` (20), code frozen
        between them.** No prompt, scorer or rules edit lands while it is in
        flight. Expect ~20 hunts at the observed 0.50 hunts/game.
      - **3b holds only if the hunter's Wilson 95% floor clears the baseline
        derived by S3** - `1/len(legal_targets)`, not the hardcoded 1/3. If S3
        moves the bar, the bar moves; the floor test does not.
      - **Power, computed before the run:** at a true 55% the gate needs 18 hunts
        (~36 games); at 50%, 27 hunts (~54 games); at 45%, 57 hunts (~114 games).
        So 40 games CAN show a strong hunter and CANNOT settle a marginal one.
      - **If it lands marginal the answer is "not shown", and cabal stops anyway.**
        No third campaign. That is the whole point of pre-committing the budget
        rather than the result.
      - **It is also the second draw**, at a different seed base, which is the only
        thing that resolves the three items waiting on one: step-not-slope, the
        `five_rejects` shift, and run-length degradation. Score those off the same
        records - they are free, and they are the reason the campaign is 2x20 at
        two seed bases rather than 40 at one.
- [ ] **The 26 self-outing lines, READ 2026-08-27 - most of them are not
      self-outings, and the count's own vocabulary is why.** Every line dumped in
      full against its seat's dealt role. The heuristic's 26/1580 is **~8 genuine
      self-identifications, in 4 of 20 games**; the other ~21 are a seat using its
      OWN role's word to accuse somebody else ("that's a Watcher's tell", "no
      legitimate Outer Party member would reject every mission"), which is the
      opposite of outing itself.
      - **The `hunt20c` cluster was read backwards, and this file said so.** The
        11-line cluster on one seat is game 11 seat 1, and all 11 are accusations
        aimed outward. The "that was cover. As Inner Party, I now urge..." quote is
        a DIFFERENT seat (game 4 seat 0) with 4 lines. One-line truncation is what
        made the two look like one thing.
      - **Root cause, and it is a theme problem, not a play problem.** On `1984-en`
        the role names ARE ordinary faction nouns of the fiction - `watcher` is
        "Inner Party", `loyalist` is "Outer Party" - so the word carries no secret
        and saying it is usually just table talk. Same class as the plain-skin
        "Loyalist" collision already flagged for the leak audit. A functional-key
        match sees nothing (the old 0/1290) and a theme-name match over-counts by
        ~3x; neither is a measurement. The fix is a claim-shaped match (first
        person, present tense) and it is a code change, so it waits for the freeze.
      - **What the 8 real ones are: all TRUE, none of them the seer.** Game 4 seat 0
        and game 9 seat 4 and game 16 seat 1 are the `watcher` naming itself; game 13
        seat 4 is the `mimic` - an EVIL seat outing itself, twice, in one game. The
        seer never announced itself in any of the 20 games.
      - **So gate #3b is NOT contaminated, and that is the load-bearing part while
        S6 is in flight.** The hunter's target is the seer, and no announcement in
        this run named it. The hunt half of gate #3 can be read off the S6 records
        without this caveat.
      - **Gate #3a carries a small real confound: 4 of 20 games.** A true "I am the
        Inner Party" from a knowledge-holding good seat hands the table a fact, so
        good's discrimination on those games is partly compliance rather than
        deduction. It does not move the S1 verdict - 3a is abandoned on other
        grounds - but it belongs in the paragraph 3a IS allowed to be reported as.
      - **The check cannot see the interesting case, BY CONSTRUCTION.** It matches
        only the seat's OWN role name, so every hit is trivially true and a mimic
        claiming to be the seer - deception working, the thing worth counting - is
        invisible to it. "Is the announcement true?" was never a question this
        number could answer. Counting FALSE claims needs a different check.
- [ ] **Gate #2 has a cheaper falsifiable design than waiting on gate #3.**
      `--arm llm` vs `--arm llm-good` on the same seeds isolates evil's
      contribution against a fixed opponent population, using arms that already
      exist. The conditionality then softens from a hard refusal to "the
      unconditional headline rate is only quotable once #3 holds". Also: the ~65%
      no-deception baseline is a property of `RandomPolicy(fail_rate, approve_rate)`,
      not of the game - fine as an existence proof, wrong if quoted as the game's
      intrinsic evil floor. And `rate_ok`'s 5% CI-floor bar is pre-declared
      nowhere; it deserves a line in the pre-committed criterion the way 3b's did.
- [ ] **Two behaviours the auditor prices, neither of them bugs** (steer
      2026-08-26 - my PROOF classification was wrong on both).
      - **A good seat approves a known-tainted team, 7/76 (9%).** Legal and
        plausibly CORRECT: a seer that always rejects exactly the tainted teams
        has a perfect tell, and the hunter's whole job is finding the seer, so
        buying concealment with mission EV is real play. The model appears to do
        it deliberately - a seer's private reasoning reads "I must support [1,4]
        ... and vote yes - without revealing I know who's darkness." Checked the
        one forced case (four rejections, a fifth loses outright): 0 of 7 were
        under that pressure, so they were free choices - but free is not the same
        as careless, and this count cannot separate strategy from lapse.
        **Consequence for the metric, which is the part that matters:** gate #3a's
        "good approves clean vs tainted" scores a concealing seer as a bad one, so
        the headline +31.55% and the blind-seat +13.57% are not measuring the same
        thing. Blind seats have nothing to hide, which is why that half is the
        sturdier number - and an argument for reporting it as the primary.
      - **Over-sabotage, 12/63 missions.** Two evils on one mission decide
        independently and the game gives them NO private channel, so playing
        success is only better if the other one fails and nothing says it will.
        Anti-coordination with a mixed equilibrium; the ideal count is not zero
        and calling it dominated was wrong.
        Still worth counting for one reason: a focal point needs no channel at all
        - "the lower-numbered evil on this team plays fail" is derivable by both
        seats from the public proposal alone, and Schelling points do not require
        communication. A pair that finds any such convention drives this near zero
        without signalling. 41% of sunk missions says the model finds none. That is
        a fact about reasoning, not a rules violation.
        So the `need` disclosure stays worth doing (it is entitled rules
        information the ask withholds) but stop expecting it to zero this number.
- [ ] **Three questions wait on the S6 second draw, and only a DIFFERENT seed base
      answers them.** All three are `hunt20c` observations that `hunt20d`
      reproduced byte for byte, which says nothing - a same-seed re-run replays the
      same calls (`docs/reproducibility.md`). Score all three off S6's records.
      - **Step, not slope.** Approval by taint level ran 93/70/77 (`hunt20b`) and
        82/64/64 (`hunt20c`): a real 0->1 drop and no further response at 2, with
        `hunt20c`'s 1->2 leg exactly flat. A third flat or rising leg makes it a
        shape - then fix the scorer note (its own item below).
      - **`five_rejects` as evil's main win path.** 0/20 in `hunt20b`, 6/20 in
        `hunt20c`, where it became the single most common path (vs missions_failed
        5, hunt_hit 5). Deadlocking the table is not sabotage, and one draw cannot
        tell a real shift from noise.
      - **`llama-server` degrades over a long run, so the fallback rate is partly a
        function of RUN LENGTH.** `hunt20c` ran 0.83% (8/968) over games 0-6 and
        2.32% (40/1723) over games 7-19; the last five ran 2.73% (15/549).
        Bucketing refusal traces mid-run, EMPTY replies (`reply: ''`) grew 22 -> 32
        while every parse-failure bucket stayed flat or fell. Empties are the
        server returning nothing, not the model answering badly. A different seed
        base at the same length separates run-length degradation from this deal.
- [ ] **Re-run changeling's powers arms on the FIXED lane - the paired result
      stands, the absolute rates do not.** Both arms of the 2026-08-27 comparison
      ran with `run_changeling` sending the run's base seed as the sampler seed for
      every game (fixed in `af7e6a0`), plus the game-weighted `_chance` and the
      wrong-denominator random reference. Both arms carried all three identically on
      identical deals, so the -10pp rule-error finding is unaffected; the villager
      accuracy, village win rate and chance figures quoted in `RULES.md` are not
      clean estimates of what this model does per game. ~30 min for 20 games each
      arm at `--no-thinking`; re-run both, not just the after arm, or the pairing is
      lost. Update the table in `games/changeling/RULES.md` and drop the caveat
      block above it.
- [ ] **The scorer steers readers to the mis-specified statistic - do NOT fix this
      until a second DRAW.** `_blind_line` prints "superseded by the graded slope above,
      which uses every taint level" (`eval/run_games.py`), but the taint response
      looks like a STEP in both runs that have the table (`hunt20b` 93/70/77,
      `hunt20c` 82/64/64), and an OLS slope through a step is the wrong summary.
      **The reason to wait**: retargeting that note would rest on two draws of n=20
      whose 1->2 legs sit inside noise - the same evidence quality this file just
      finished voiding a gate verdict over. Fixing it now would be the `hunt20b`
      error wearing a different hat. A run at a different seed base is the trigger,
      not `hunt20d`, which reproduced `hunt20c` byte for byte: a third flat
      or rising 1->2 leg makes it a shape, and then change the note AND make
      `taint_sensitivity` say the slope is fitted to a non-monotone table.
      **The trigger now has a date: the S6 campaign is the second draw**, and its
      taint-level table is the third leg. Score it off those records. Note the S1
      verdict does NOT pre-empt this - it declines to PROMOTE the binary to the
      gate, which is a different act from fixing a scorer note that points readers
      at a mis-specified statistic.
- [ ] **Gate #3 was never blocked on the table talk - that read was wrong.** It was
      model capability: identical prompts scored -0.2% on the 12B and +66% on
      120B-class. `--register plain` helped the 12B (+16.7%) but bought suspicion,
      not judgement (7 of 8 games died at five_rejects). `--simultaneous` is built
      and unmeasured; the salience line has no measured benefit anywhere and is a
      removal candidate, on its own measurement.
- [ ] **Judge a detached run only by its own log/JSONL - never by a proxy.** Three
      times in one session CPU seconds, Win32 IO counters, and an exit code each
      read as liveness for network-bound work; the IO-counter one killed a healthy
      cloud run (those counters track FILE io, not sockets). And probe a cloud tier
      with a BURST (12 back-to-back), never a single call: a key under cooldown
      serves the occasional request while failing a stream, so a single-call probe
      says "healthy" about a tier that cannot carry a run.
- [ ] **Negation pass over the model-facing strings** (the rule is
      `.claude/rules/model-facing-text.md`, path-scoped so it fires when you open
      the files that hold them). Steering by prohibition makes the banned behaviour
      MORE available, and the live prompts do it in at least three places:
      `"speak in the first person, and do not answer your own earlier lines"`
      (referee DISCUSS ask), `"do not defer to whatever the table already seems to
      think"` (plain register), `"no theatrics, no slogans, no world-flavour"`
      (same). Each has a positive form - speak TO the other seats; form your own
      read first; speak plainly and cite the record. The referee's refusals
      (`cannot fail a mission`, `cannot be the informant`) are hard guardrails and
      stay, though each already pairs with a positive instruction.
      **This is a measured change, not a cleanup** - same seeds, one variable, and
      it waits until the runs in flight land or it contaminates them.
      **Re-homed 2026-08-27 (S1):** measure it on changeling, where a paired
      20-game arm is ~30 min against cabal's 13.2 h. It must not land before the S6
      campaign finishes - a prompt edit mid-campaign confounds it exactly the way
      `c43274e` confounded `hunt20b`. Cabal's referee refusals stay as written.
- [ ] **A per-seat private notebook - BUILT 2026-08-26, UNMEASURED.** `--notebook`
      on `run_games.py` and `demo.py`; off by default. A seat's `note` is filed
      under its own seat and rendered back to that seat alone on every later call,
      so a read survives the turn that formed it. Cap: last 6 lines of 160
      characters, stamped with the mission it was written on.
      - **It is a prompt change, so it is a MEASURED change** (`--notebook` vs not,
        same seeds, one variable, reported beside its fallback rate) and it waits
        behind the seed-1000 re-run the same way the negation pass does. Nothing
        about it is quotable until that arm exists.
        **Re-homed 2026-08-27 (S1)** to changeling for the same reason as the
        negation pass, and it stays OFF for the S6 campaign, which runs on frozen
        code. A memory that survives the turn is a bigger prompt change than the
        others here, so it is the one most worth a cheap paired arm.
      - Gate #1 holds by construction and the audit says so: the notebook leaves
        the audit view with speech (`include_notes` defaults to `include_speech`),
        because `find_leaks` is naive substring matching and a seat writing down a
        correct GUESS would otherwise score as a referee leak. Four mutation-checked
        tests, each killed by its own named test with a compiling mutant.
      - Two costs it buys, both real: it rides on every call (~1.1 kB at full
        notebook), and it hands the seats a memory the earlier runs did not have,
        so no number from before it is comparable to a number after it.
- [ ] **Mini-personas** (credulous / suspicious / contrarian / by-the-numbers) as
      per-seat judgment biases, assigned from the game seed and recorded so the
      scorer can split by persona. Trigger: only if a table that argues from
      evidence still votes identically. NOT for flavour - votes are already
      independent (§Measured), so this buys nothing until the talk carries evidence.
      **Re-homed 2026-08-27 (S1)** to changeling if built at all - its trigger was
      never met on cabal and cabal no longer buys measured prompt variables.
- [ ] **Larger setups (6/7p) + the two information-degrading evils.** Package them
      together, because both only make sense at 3 evil seats.
      - The engine already supports both, and has since the first commit: `Role`
        carries `seen_by_seer` (False = the evil the seer cannot see) and
        `sees_fellow_evil` / `seen_by_fellow_evil` (False = the evil who neither
        knows nor is known by its own side). `entitled_knowledge` honours all
        three, so each role is ~2 lines of DATA. The cost is measurement, not code.
      - **Why they are worth more than variety: they degrade information in a
        principled way.** The unseen-evil variant halves the seer's knowledge, so
        the current +30.7% local / +66% cloud stops being partly "the seer acting on
        a handed answer" (already isolated at +13.7% by the blind-seat split) and
        becomes a claim about deduction. The blind-evil variant makes evil deceive
        WITHOUT knowing its partner, which is the honest version of gate #2 - the
        current claim is really "two agents told about each other cooperated".
      - **Not before gate #3 is called.** Changing what the seer knows mid-run means
        neither the old nor the new number means anything. Sequence them as the
        hardening pass you would actually publish from.
      - At 5 seats there are only 2 evil, so the unseen variant leaves the seer
        seeing exactly one and the blind variant leaves two evils who know nothing
        of each other - swingy to the point of noise. These are 7+ roles.
      - **A bigger table does NOT fix the thin denominator - it makes it worse.**
        This file used to blame the ~12-votes-a-run sample on the 5-seat size
        ("because most teams in a 5-seat game carry an evil"), which implies a
        larger table would help. It would not. Clean teams get
        combinatorially rarer as seats grow, faster than the extra good voters
        compensate; gate #3b is untouched at any size since hunts are one per game.
        Arithmetic, table, and the graded-taint fix that DOES work:
        `docs/player-counts.md`.
        **Checked from the other side 2026-08-27 and it holds harder than this
        bullet claimed.** Off-team-clean good votes per vote event - the only
        unconfounded gate-#3a cell - run 5p **0.120**, 7p **0.160**, 8p **0.100**;
        per unit speaking cost 0.0240 / 0.0229 / 0.0125. 7p's raw gain is eaten by
        its extra speakers. So a bigger table does not rescue gate #3a either, and
        these variants are worth building for what they degrade about INFORMATION,
        never as a sampling fix.
      - **The roles themselves landed 2026-08-27** as `LURKER` (unseen by the seer)
        and `STRAY` (neither knows nor is known by its own side), named in all five
        skins, plus `ALL_ROLES` and three theme guards in `test_audit_coverage.py`.
        Nothing deals them - what is left is the 6/7p setups and the measurement,
        which was always the cost. Verified on a hand-built 7-seat deal: the seer
        sees every evil but the lurker, and no evil sees the stray.
      - Watch role-name vs faction-name substring collisions in the leak audit (see
        the plain-skin "Loyalist" case). **A sharper one found while checking the
        above, and it is not about naming at all:** two seats holding the SAME role
        break the audit outright. Each one's own role name is the other's secret
        term, so the 7p deal with two `loyalist` seats reported a mutual leak in
        every skin - a false positive no rename can fix, since the term is
        identical by construction. A setup that repeats a role needs `secret_terms`
        keyed so identical-role seats do not audit against each other, and that is
        setup work, not theme work.
- [ ] **Seat the changeling expansion cards, which means picking a deck.** The
      cards themselves landed 2026-08-27: `kindred` (the pack's mirror on the
      village side) and `waker` (acts last, so it is the only seat whose belief is
      guaranteed true at dawn) are implemented, skinned, resolved and tested, and
      `SETUP_5` deals neither - the same footing as cabal's `LURKER`/`STRAY`, for
      the same reason: every recorded changeling number was played on the
      eight-card deck, so a deck change re-baselines all of them. What is left is
      the deck design and the measurement, not the code.
      - **Do it after S2/S5**, and expect `waker` to be the one worth a run:
        every other seat has to infer that the night moved it, and this one is
        told, so it is the cleanest handle on whether a model reasons about
        divergence at all rather than about who is lying.
      - Landing `kindred` found a real gate #1 leak, now fixed and guarded: two
        meeting kinds sharing the sentence "one of your own" made a stale village
        reveal byte-identical to the one that betrays a wolf moved into that seat.
        `Card.kin_form` is per-kind data; `pack` keeps its sentence, because
        rewording it would be a prompt edit under the queued 200-game run.
      - Four notable expansions costed and NOT built, in `RULES.md`: a third win
        condition (cheapest interesting one, and it lands on the scorer, not the
        night), an evil that sees the pack unseen, a card that copies another and
        acts as it (the game is named for it, and it makes the night recursive), a
        mass positional shuffle (cheap, but variety).

- [ ] **Candidate changeling skins, and which arm each is FOR** (scoped
      2026-08-27). All of them sit behind arm 3, the
      inverted-polarity skin - two more rich arm-2 fictions and still no claim
      about morality is the trap `docs/moral-framing.md` exists to name.
      **BUILT 2026-08-27, as themes only:** `greek` (the vocabulary control below)
      and `investiture` (the Fengshen arm 4 below). Unrun, `DEFAULT_THEME` still
      `folk`, no number moved. Both are 59 words against `folk`'s 59, and 312/308
      chars against its 316 - length is held on BOTH axes, because a same-word-count
      blurb ran 13% short in bytes on cabal and word count alone is not the control.
      **The inverted-polarity skin landed the same day and the blocker is cleared.**
      `folk-inv` is the hunted framing: same village, same night, opposite valence.
      Six of its eight names are `folk`'s own and unchanged - only the two carrying
      the valence move, `Werewolf` to `Hunted` and `Seer` to `Witchfinder` - so 2-vs-3
      differs in valence and very nearly nothing else, which is tighter than cabal's
      `1984-inv` manages. The village still wins by naming one of them; the blurb
      stops calling that a rescue. The set is now floor / polarity / inverted polarity
      / vocabulary control / two neutrals, all at 59 words and 308-316 chars, all
      unrun.
      **Reading the rendered preamble under `greek` caught a live prompt bug that no
      test held**: the `deceived` power hardcoded "a {centre}", so a skin naming the
      pile with a vowel put "a altar card" in front of every seat. The article now
      comes from `roles.indefinite()` and a guard renders every skin's power text;
      `folk` and `plain` render the bytes they always did, so the queued 200-game run
      is untouched. Read the prompt, not just the tests, when a skin lands.
      - **Greek myth = the vocabulary control (arm 2').** What `bnw-en` is to
        `1984-en`. Register-distant from `folk` in the way a fae skin was not, and
        the fit is structural rather than decorative: metamorphosis and theoxeny
        are the corpus, gods walk unrecognised, Proteus is a different thing each
        time you grip him, Circe changes what you are while you are her guest.
        Polarity maps onto `folk`'s cleanly, which is exactly what a control needs.
      - **Fengshen Yanyi = a better arm 4 than the masquerade.** Its conceit is
        that the dead of the war are enrolled in the celestial bureaucracy and both
        sides execute a mandate: "one side must lose, and losing is not damnation"
        is a morally NEUTRAL frame that is also rich, where a masquerade is neutral
        by being thin. Check the reading against the text before building on it.
        **Both built 2026-08-27, and the masquerade objection is what gives it a
        job.** They are neutral by DIFFERENT mechanisms - `investiture` with total
        stakes that do not matter, `masquerade` with no stakes at all - so the pair
        separates an act with no moral weight from an act with no consequences,
        which one neutral arm confounds. If 4 and 4' differ, what moved was stakes
        rather than valence. `masquerade` is thin in the conceit only: 59 words,
        like every other arm here. The Fengshen reading is still from general
        knowledge, not a pass over the text; that check is still owed and what it
        would move is the blurb, not the mechanics.
      - **Journey to the West holds the best statement of this rung's premise.**
        The Six-Eared Macaque: an impostor identical to Sun Wukong, indistinguish-
        able to the gods and to the pilgrims who travelled with him. That is the
        belief/truth split in one episode. If one myth skin ever ships, that is its
        blurb.
      - **The mashup, asked 2026-08-27: right as SOURCING, wrong as DESIGN.** The
        two share a pantheon - Nezha, Li Jing, Erlang Shen, Laozi are in both - so
        drawing on both is how the folk cosmology actually works, not a mangling.
        But their value here is opposite: Fengshen's is neutral polarity, JTTW's is
        righteous-pilgrims-versus-impostors. Mash them and the skin's polarity is
        indeterminate, which is the `1984-en`-vs-`plain` confound rebuilt by hand.
        So: one corpus owns the FRAME, the other supplies vocabulary and imagery
        across the shared pantheon. A mashup in practice, one variable on paper.
        **The first `investiture` was Fengshen top to bottom and did not honour the
        sourcing half; re-vocabularied 2026-08-27** across the pantheon, with a test
        the division can be applied by, one name at a time: a figure enters if its
        story reinforces the bureaucratic conceit or is silent about it, and stays
        out if it arrives arguing one side is righteous. Zhong Kui is in for his
        APPOINTMENT - failed the examination, died on the steps, woke into an office,
        which is the frame's own claim told as a biography - and his demon-hunt is
        out, being the same man. Lotus Body is Nezha.
      - **A second test: corpus signatures are RESERVED, even when they pass the
        polarity one** (2026-08-27, after a pure-JTTW skin was costed). Six-Eared
        Macaque was in `investiture` for a few hours and is out again: as a card it
        takes no side, but it is the JTTW skin's headline, and two faces sharing
        their most distinctive name stop being two vocabularies - which is the whole
        variable a control arm moves. Shared-pantheon figures (Nezha, Zhong Kui,
        Yang Jian) stay free to both; signatures do not. `Yellow Turban` went with
        it, colliding lexically rather than by ownership with `Yellow Wind`.
        `investiture`'s swapper/switcher/kindred are now Earth-Traveller / Duty
        Officer / Same List, the last two also pulling toward the bureaucratic frame.
      - **`journey`, the pure-JTTW skin, BUILT 2026-08-27.** pack = Six-Eared
        Macaque, spotter = Fiery Eyes, swapper = Hair Double, switcher = Yellow Wind,
        deceived = River-Drinker, bystander = Porter, kindred = Vow-Bound, waker =
        Cast-Off Body (the corpse at the Lingyun crossing - looking at what you
        actually are, after everything). Sides The Pilgrims / The Impostors, pile
        `baggage`. **It does not add an arm.** Its polarity matches `folk`, so it is a
        second candidate for the ONE vocabulary-control slot `greek` holds, and two
        2' arms carry no more information than one. `greek` keeps the slot: `folk` and
        `greek` both run on predator and prey, where `journey` runs on legitimate
        versus counterfeit - nobody is eaten, and the wrong is that the wrong one is
        wearing the face. A different moral axis, which a control must not move. So
        `journey` ships to be READ (the skin to put in front of someone asking what
        parlor is for, since its source states this rung's premise outright) and
        `greek` ships to be RUN. Reversing that is a swap, not an addition.
      - **`greek` lost its proper names the same day, and that is the control
        working.** It was 6-of-8 proper names - Empousa, Pythia, Hermes, Circe,
        Dioscuri, Narcissus - while `folk` is 8-of-8 common nouns and so is every
        other skin, `journey` included. So folk-vs-greek moved vocabulary AND name
        type, the `bnw-en` word-count defect in a different currency. Name type is not
        cosmetic: a proper name is an opaque token that pays off only from the model's
        priors and pays nothing without them, while a common noun restates a power the
        preamble already prints - so the two hand a weak model different amounts, and
        that gap would have been read as vocabulary. Now Hollow Guest / Oracle /
        Trickster / Enchantress / Lotus-Eater / Shepherd / Twins / Pool-Gazer, same
        register, no personal names. **Check name type on any future skin**; nothing
        tests it, because "is this a proper name" is not a property code can decide.
      - **The proper names came back the same day as `greek-named`, which is the
        right LAYER for them** - not a reversal. Dropping them from the CONTROL was
        correct; treating them as a defect rather than a variable was not. The pair
        differs in exactly eight strings, the card names, with blurb, pile, sides,
        polarity, corpus and length all identical - the cleanest single-variable
        manipulation in the repo, since every other arm pair moves a whole fiction.
        It is worth running because the preamble prints every power in full, so the
        names carry no information: whatever separates the pair moved through priors
        and salience, which is a confound underneath every polarity arm. Axis, ladder
        and the CN follow-up: `docs/moral-framing.md` §Name form.
      - **CN name forms are the next rung on that axis, not a new one** - a
        transliteration (`Liu'er Mihou`) is opaque where a gloss (`Six-Eared Macaque`)
        is not, and Han script is opaquer again. `journey` / `investiture` are where
        it would go, and it also tests whether the effect travels or belongs to one
        fiction. Not built: the Greek pair isolates the axis at no fiction cost and
        comes first. The console prerequisite below is now cleared either way.
      - **Ship any myth skin in English first.** A `*-cn` skin moves fiction AND
        language at once and cannot be read. The clean language control already
        exists and has never been run - `1984-en` vs `1984-cn` holds the fiction
        byte-identical and moves only the language, on a game whose numbers are
        already in hand.
      - **Prerequisite for any CJK skin here: DONE 2026-08-27.**
        `eval/run_changeling.py` printed its report with no `sys.stdout.reconfigure`
        and would have died on the cp1252 console exactly as cabal's demo did before
        `320e322`. Landed as the one line it was, ahead of the skin.
        **And the same line was missing from `eval/run_games.py`, which is the worse
        half and was not on anyone's list**: cabal's EVAL lane already accepts
        `--theme 1984-cn` and `--theme bnw-cn`, so a CJK run could have completed in
        full and then died at the moment of printing its report - hours of model
        calls, a non-zero exit, and nothing wrong with the arena. Both fixed.
        Changeling still has no demo entry point.

- [ ] **Ship a werewolf-vocabulary theme on changeling - and that is the WHOLE
      answer to public legibility.** A public repo has a real problem that "team-
      mission hidden-role deduction game" means nothing to anyone outside the
      hobby, while "werewolf / seer / villager" means something to nearly everyone.
      That is public-domain folk-game vocabulary (Mafia, Davidoff 1986), carries no
      branding question, and lands on a rung that is already built.
      - **This is why a vanilla Werewolf RUNG is not worth building**: it sits on
        the same rung as cabal (deterministic referee, bounded actions, no
        judgment), so it buys recognition and no engine progress, and it has
        elimination - a shrinking table, variable agent count per game, dead seats
        contributing no decisions, i.e. the N problem from the wrong side.
        Legibility is a theme and a README paragraph, not a spike.
      - **changeling does not retire cabal's gates.** Different rung, different
        deduction task. Which game's numbers get published first is the only thing
        it settles; a cabal gate left uncalled stays uncalled.
- [ ] Spike #2: off-map faction heartbeat - factions acting on their own clock,
      driven by a long-running agent process outside the game loop.
- [ ] **Evil over-sabotages, and it is the seer-salience bug wearing the other
      team's colours.** Scored on the FULL 20-game run: 63 mission resolutions,
      fail-count distribution `{0: 34, 1: 17, 2: 12}`, need=1 throughout. So **12
      of 29 failed missions (41%) had BOTH evils play fail when one sufficed**, and
      12 of 63 missions overall (19%). The partial-run figure was 45%/9-of-20; the
      full run settles it at 41%.
      **Restated 2026-08-27 (S3): the honest figure conditions on the game
      continuing** - a double fail on evil's third failed mission is free, since the
      game ends on that resolution and the identification is never paid for.
      Re-scored, `hunt20b` is 11/28 = 39% and `hunt20c` is 10/22 = 45%. The
      correction moves the number by ~2pp in each direction and changes nothing
      about this item: evil still hands over the pair on ~2 of every 5 sinkings it
      actually pays for.
      On a 2-seat team two fails name both of them outright; on a 3-seat team it
      cuts the good side's search to three pairs. It is the single largest free
      information gift on the board and evil hands it over on two of every five
      missions it sinks.
      - The rules already allow the right move. `validate_card` refuses only a GOOD
        seat playing fail, so evil may play success freely, and the MISSION prompt
        already says "weigh sabotage now against the suspicion a fail here would
        put on this team". The capability is there; nothing lines it up.
      - **Two fixes here, NOT one, and they are different kinds of thing.** Keeping
        them apart is the whole judgement in this item.
      - **(a) Disclose `need` - a harness BUG, fix unconditionally.** `need` appears
        only in the public event AFTER resolution (`referee.py` mission()), never in
        the ask. How many fails a mission requires is PUBLIC RULES INFORMATION - a
        human reads it off the board before playing a card. Withholding it is an
        information asymmetry against the game's own rules, i.e. the seat is being
        asked to weigh redundant sabotage against a threshold it was never given.
        This is not a hint and not a nudge; it is restoring entitled information,
        and it needs no measurement to justify. It does still need to be SEQUENCED
        after gate #3, because it changes behaviour mid-run like anything else.
      - **(b) Naming the partner on this team - a HINT, and the evidence points
        AGAINST it.** The seat can derive "my partner is on this team" from the
        public proposal plus its night knowledge. Spelling that out is exactly what
        `_night_against_the_table` does for the seer - and that line's value
        INVERTED with model capability: +63% on the 12B bench, then **+80% as-is vs
        +72% with the line** on q36, i.e. actively harmful, because it competes with
        reasoning a capable model already does. So do not assume the mirror fix
        helps; the one measurement we have on this exact move says it hurts on the
        model gate runs actually use. If (b) is tried at all it is a measured arm of
        its own, and (a) must land first and alone or the two are confounded.
      - **This is a confound in gate #3a, not just an evil-side weakness.** Good's
        +30.7% discrimination is measured against an evil side that self-identifies
        on 45% of its successful sabotages. Some unknown share of that number is
        good exploiting a blunder rather than deducing from discussion. So fixing
        evil is not a fairness gesture - it is required before the good-side number
        means what it claims. Expect discrimination to DROP when this lands; that
        drop is a truer number, not a regression.
      - Sequence: measured change, same seeds, one variable, after gate #3 is
        called. Distribution above is from a PARTIAL run (13 of 20) and is an
        incidental mechanical count, not the pre-committed hunt metric - recompute
        on the full run before quoting it anywhere load-bearing.
- [ ] **Stratify cloud results by served upstream instead of pooling them.** The
      problem with an `auto` run was never that it is undocumented - `complete_meta`
      already returns the served model and the report prints the mix. It is that
      POOLING hunts across a time-varying model population computes a Wilson
      interval over an ill-defined denominator. Record the served upstream on each
      decision, report per model class, and an `auto` run stops being "several
      models averaged": cells accumulate ACROSS runs, so tonight's nano hunts and a
      future 120B-class run land in different cells instead of contaminating one.
      Retires the "reproducible, unlike the cloud's 30-upstream mix" asymmetry -
      stratified, a cloud run is reproducible at the cell level. Does not rescue a
      thin run: ~10 hunts over 3+ upstreams is nothing per cell.
- [ ] **Theme as an experimental variable, not a default to fix** (design:
      `docs/moral-framing.md`). `1984-en` stays the shipping default;
      there is no licensing reason to drop it and it is the face every committed
      transcript wears. What is open is that the blurb inverts moral polarity -
      sabotage reads as heroic, deceit as survival - and nothing measures whether
      that moves behaviour. No number in §Measured records which theme produced it,
      so a theme change is a MEASURED change on the same terms as the negation
      pass: same seeds, one variable, after gate #3 is called.
      **Re-homed 2026-08-27 (S1)** to changeling, which ships a folk-game theme of
      its own and so poses the polarity question at 1/26th the GPU cost. `1984-en`
      remains cabal's shipping default and is the face of every committed
      transcript; nothing about cabal's theme changes.
      **Arms built 2026-08-27**, on cabal, as themes only: `1984-inv` (arm 3,
      villainous - the 1984 skin inverted rather than a new fiction, so 2-vs-3
      differs in valence and nothing else) and `drill-en` (arm 4, neutral - a
      sanctioned drill with no victim). Unrun, `DEFAULT_THEME` untouched, so no
      number moved. `bnw-en` was 84 words against `1984-en`'s 53, confounding the
      vocabulary control with density; trimmed the same day, and all four English
      faces are now 53 words / 281-291 chars. Frozen from here - a blurb is a
      prompt, so a later edit orphans whatever has been recorded against it. One
      thing left to settle before spending GPU: whether the run happens on cabal or
      on the re-homed changeling rung. A `bnw-inv` was considered and rejected -
      reasoning in the doc.
- [ ] **Two shapes not to harden further before game #2** - cabal's `Phase` enum,
      the `action_prompt` if-chain, and `ACTION_KEYS`. Reasoning and the exact
      constraint: `docs/action-channel.md`.

## Pre-committed criteria

**The S6 gate-#3b campaign's criterion (written 2026-08-27, BEFORE the run) is the
queue item of that name above** - 40 games at two seed bases, frozen code, floor
against the S3-derived baseline, and no third campaign if it lands marginal. It
lives there rather than here so the budget sits beside the slice that spends it;
this is the pointer, not a second copy.

### For the hunt run (written 2026-08-25 19:54, BEFORE the numbers)

Run in flight: 20 games, `qwen36-35b-a3b-iq3`, seed 1000, 2 rounds, hunt fix in,
detached (`eval/records/run-hunt20.cmd`, log `eval/records/hunt20.log`).

- **Gate #3b holds only if the hunter's Wilson 95% floor clears 1/3.** That is the
  bar the scorer already applies; it is written here so it cannot be softened after
  seeing the result.
- **If it lands near chance, the answer is "not shown at this N" - NOT "run more
  games until it clears".** Stopping when a floor happens to cross is peeking, and
  it manufactures the significance it claims to find. A repo that voids runs over
  10% fallback and refuses to read gate #2 off a random baseline cannot ship that.
- **Power, computed before the run:** at a true 60% the gate needs ~16 hunts
  (~21-38 games); at 50%, ~32 hunts (~43-76 games); at 45%, ~62 hunts (83-148
  games). This run yields ~8-15 hunts. So it can SHOW a strong hunter and cannot
  settle a marginal one - that asymmetry is the reason for the bullet above.
- **If the hunter lands marginal, respecify the metric rather than buying games.**
  Gate #3 is bottlenecked on its lowest-power half: the vote metric collects
  100-222 samples per 12 games, the hunt collects 5. A ranked or confidence-graded
  hunt would yield graded signal per hunt instead of one bit, which is the same
  reason the blind-seat split beats the raw discrimination number.

## Measured, dated - numbers before opinions

All local `rocinante-x-12b-heretic-q4`, seed 400, 8 games, 2 rounds, <1% fallback
unless said otherwise. Fallback rate is quoted because a number without it is the
random policy wearing a model's name.

| what | result | 2026-08-25 |
|---|---|---|
| good vote discrimination, baseline | -0.2% (n=138 votes) | at chance |
| seer approving a team carrying a KNOWN evil | 42% baseline -> 43% with the salience line | the line does nothing in a live game |
| same seer decision, isolated bench, no discussion | 83% -> 37% (n=30/cell, p<0.001) | the line works when nothing buries it |
| `--rounds 2` vs 1 round | 1 of 8 games deadlocked vs 2 of 2 | two rounds is the floor |
| vote unanimity | 11% of 46 votes (spread 1/5..4/5) | votes are ALREADY independent, just uninformed |
| record length vs the 60-line cap | 10 of 16 games over, speech:facts ~4:1 | the trim was deleting missions 1-2 (fixed, `3d0d07d`) |
| cap at 512 vs 1536 max_tokens, `nemotron-3-super` | 0/4 -> 2/4 parsed, failures truncated at BOTH caps | no cap fixes a model that thinks out loud; pin one that does not |
| **cloud `auto` (mixed 120B-class), character register, 12 games** | **discrimination +66.0%** (clean 94.4%, tainted 28.4%, n=192; 2.5% fallback) | **gate #3a HOLDS - it was model capability, not the prompt** |
| same run, hunter | 33.3% (3/9, CI floor 12.1%) | exactly chance - gate #3b is now the blocker |
| local 12B, `--register plain`, same seeds as the salient run | discrimination +16.7% (blind seats +11.4%, n=76) | first positive on the 12B, but 7 of 8 games died at five_rejects |
| **local `qwen36-35b-a3b-iq3` (MoE 35B-A3B APEX), 12 games, 0.69% fallback** | **discrimination +30.7%** (blind seats +13.7%, n=222); evil 66.7% with 6 wins by SINKING missions and 32 fail cards | gate #3a holds on ONE pinned local model - reproducible, unlike the cloud's 30-upstream `auto` mix |
| same model, seer bench | +80% as-is vs +72% with the salience line | the salience line is now HARMFUL - it competes with reasoning a capable model already does |
| hunts across ALL live runs | 8/26 = 31%, and **5 of 26 named the hunter's own ally** | fixed in `hunt()`: a seat the night named as yours cannot be the seer, so the referee refuses it |
| cost, `q36` local | ~14.6 min/game (reasoning distill, long generations) | a 50-game hunter run is ~12h overnight; cloud is ~3 min/game when quota allows |

Added 2026-08-26, all `qwen36-35b-a3b-iq3`, seed 1000, 20 games, 2 rounds. **NONE of
these three columns is a controlled comparison of another.** `hunt20` vs `hunt20b`
differ by three things (see the `hunt20b` item); `hunt20b` vs `hunt20c` differ by the
sampler pin `2cfe9d5`, which landed between them. They are three draws, which is all
they are. `hunt20d` is not a fourth column - it reproduced `hunt20c` exactly
(`docs/reproducibility.md`), so a controlled pair still needs a different seed.

| what | `hunt20` (08-25 19:54) | `hunt20b` (08-26 08:56) | `hunt20c` (08-26 14:52) |
|---|---|---|---|
| blind taint sensitivity - THE GATE | +1.20% [-8.44%, +9.63%] | +8.82% [+0.94%, +16.82%] | +9.00% [**-0.25%**, +18.18%] |
| blind, binary (superseded - see below) | +2.53% [-13.45%, +18.04%] | +19.94% [+6.27%, +32.02%] | +18.11% [+3.52%, +33.53%] |
| approval by taint level, blind | - | 93% / 70% / 77% (41/44, 28/40, 24/31) | 82% / 64% / 64% (41/50, 37/58, 32/50) |
| hunter | 3/9 = 33.33%, floor 12.06% | 6/11 = 54.55%, floor 28.01% | 5/9 = 55.56%, floor 26.66% |
| evil win rate | 70%, 5 of 14 by `five_rejects` | 75%, **0** by `five_rejects` | 80%, **6 of 16** by `five_rejects` |
| evil win paths | 6 missions / 5 rejects / 3 hunts | 9 missions / 0 rejects / 6 hunts | 5 missions / 6 rejects / 5 hunts |
| missions, fail-card distribution | 63, `{0:34, 1:17, 2:12}` | 74, `{0:37, 1:22, 2:15}` | 62, `{0:35, 1:15, 2:12}` (derived) |
| over-sabotage, share of sunk, UNCONDITIONED (superseded 2026-08-27) | 12/29 = 41% | 15/37 = 41% | 12/27 = 44% |
| over-sabotage, **conditioned on the game continuing** - the honest figure | - | **11/28 = 39%** | **10/22 = 45%** |
| fallback rate | 0.49% (11/2231) | 0.54% (11/2033) | 1.78% (48/2691) |
| wall clock | - | 4h42m | 6h37m |

Two things this table now shows that no single column does:

- **The GATE row's point estimate is stable (+8.82 -> +9.00) while its floor verdict
  INVERTS** (+0.94 -> -0.25). At n=20 the floor's position relative to 0 is noise.
  Do not report "the floor cleared 0" as a finding at this N.
- **The taint-level row is a STEP, not a slope, in both runs that have it** - a real
  0->1 drop and no further response at 2 (`hunt20c`'s 1->2 leg is exactly flat). The
  linear "per extra saboteur" statistic is mis-specified for this shape, and the
  binary row is the better-behaved one. The scorer's "superseded by the graded slope"
  note has it backwards.
- `hunt20c`'s fail-card distribution is DERIVED (62 missions, 27 sunk, 39 cards, max 2
  fails at 5 seats => `{0:35, 1:15, 2:12}`), not read from a scorer field. The JSONL
  carries `fails_played` per GAME only.

| what | result | 2026-08-26 |
|---|---|---|
| **the sampler was never seeded** | same 20 games, seed 1000, twice: 63 missions / 9 hunts vs 74 / 11 | **`--seed` fixed the deal and the fallback RNG and NOTHING about the model.** Every "same seeds, one variable" number in this file was read against an unmeasured run-to-run spread |
| sampler pinned (`2cfe9d5`), verified on the instrument | two calls at seed 1000 to local `q36` byte-identical; seed 7 differs | llama.cpp honours `seed`; on cloud it is a best-effort hint and unproven until a repeat run shows it |
| `need` disclosure vs over-sabotage | 41% of sunk missions in both runs | disclosing the threshold did NOT reduce redundant sabotage - the problem is the missing focal point, not missing rules |

Added 2026-08-27 (S1). No new games - all of it is arithmetic on `hunt20b`/`hunt20c`
records, with the pipeline first reproducing both runs' recorded slopes, binaries
and CIs exactly, and reconstructing team membership from `public_events` (proposals
x 5 == votes, 20 of 20 games).

| what | result | what it decides |
|---|---|---|
| **blind gate #3a, split by self-membership** | `hunt20b` ON **+22.01%** (38/33) / OFF **+9.65%** (6/38); `hunt20c` ON **+8.91%** (42/43) / OFF **+18.08%** (8/65) | **the two runs split in OPPOSITE directions** - the unconfounded cell cannot hold a sign at this N |
| **off-team clean blind votes per game** | **0.30-0.40** (6 in `hunt20b`, 8 in `hunt20c`, 9 in `hunt20`) | 40 samples = 100-134 games = 33-44 h; the honest 3a estimator is unaffordable |
| off-team-clean good votes per vote event, by table size | 5p **0.120**, 7p **0.160**, 8p **0.100**; per speaking-seat 0.0240 / 0.0229 / 0.0125 | **no cabal table size reopens gate #3a** |
| games for a 95% floor above 0, graded slope (bootstrap SD 4.75% at n=20) | ~22 at the raw +9.00%; ~38 at 75% of it; ~86 at 50% | N was never the binding constraint - the quantity is |
| gate #3b, pooled post-fix hunter | 11/20 = 55.00%, Wilson [34.21%, 74.18%] | clears 1/3 by 0.9pp, and pooling three runs after the fact is PEEKING - not a result |
| gate #3b, games needed by true rate | 55% -> 18 hunts (~36 games); 50% -> 27 (~54); 45% -> 57 (~114), at 0.50 hunts/game | the S6 budget of 40 games, and the asymmetry it pre-commits to |

Added 2026-08-27 (S3). No new games - the four scorer/audit numbers re-derived and
re-run over `hunt20b`/`hunt20c`. Each fix is mutation-checked: the pre-fix
derivation restored as a compiling mutant, killed by its own named test, restored.

| what | result | what it decides |
|---|---|---|
| **hunter baseline, derived** `1/len(legal_targets)` per hunt, meaned over hunts | **1/3 on `SETUP_5`** - unchanged, because the legal set is 3 in every game of it | **S6's pre-committed bar and power table stand as written.** The bar was RIGHT; what was wrong was that it was a constant. A 7p or blind-evil deal makes it 1/4 and the scorer now follows |
| a run whose hunts record no legal-target count | **REFUSED**, not defaulted | fails closed, same shape as the empty blind stratum - a default grades a record against whichever chance the reader assumed |
| **over-sabotage, conditioned on the game continuing** | `hunt20b` 15/37 -> **11/28 = 39%**; `hunt20c` 12/27 -> **10/22 = 45%** | the correction is real and it does NOT rescue the finding - 4 and 2 of the redundant cards were free, and the rate barely moves. Evil still over-sabotages ~2 of every 5 payable sinkings |
| **`outed_own_role_in_public`, matched against theme names** | 0/1290 (matcher-blind) -> `hunt20b` **4/1150**, `hunt20c` **26/1580 = 1.6%** | **the old zero was a property of the matcher, not of the play.** It looked for `seer`/`mimic` in speech that can only ever say "Thought Police"/"Inner Party". Seats DO name their own role in public, and `hunt20c` seat 0 does it repeatedly as cover |
| `hunt_named_impossible`, allies from `known_allies` | 0/11 and 0/9, unchanged on these runs | no regression on the shipping deal, and it stops flagging a legal hunt on a `stray` - which is a wrong PROOF-class finding, the worst kind this file can emit |

## Decisions already locked

**Code invariants moved to `CLAUDE.md`** - it is always loaded, these are not,
and two copies of one rule is how the stale copy wins an argument. What stays
here is project state: the route calls and what a run measured.

- **A run writes its own terminal marker; a wrapper cannot be trusted to outlive
  it.** `core/runlog.py`, used by both eval drivers: `PARLOR DONE rc=N
  games=landed/requested elapsed=Ns`, written from a `finally` so it survives a
  crash, a `sys.exit` and a Ctrl-C. It contains `DONE rc=` so old greps still find
  it. **A log whose last line is a progress line is a killed run** - that is the
  whole point, and nothing writes the marker for a process killed outright. The
  `.cmd` echo stays for the one case python cannot cover: a crash before the driver
  runs at all.
- **`refused` is the fallback census; `note` is cabal's notebook.** Both games
  record the refusal that produced a fallback on the decision itself, so a run's
  refusal diagnosis is a census in the JSONL rather than a sampled trace (8/game)
  and an end-of-run report that does not exist until the run ends. It holds the
  last ATTEMPT's complaint, not the "N attempts failed" summary. Two consequences
  for old records: pre-2026-08-27 JSONL has no `refused` at all, and changeling's
  records before that date carry the same string under `note`.
- Independent context = one model + per-seat private context slice, not N brains.
- Referee is deterministic code; LLM only for players (and, later, judgment-GMs).
- Cloud is fine for game-fiction secrets (not credentials); local for deception checks.
- **`--rounds 2` cleared the rejection deadlock.** 1 of 8 games ended `five_rejects`
  at two discussion rounds, against 2 of 2 at one round. One round gives a vote
  nothing to reason from; treat 2 as the floor for any live run.
- **Pin a model for attribution, use `auto` for capacity - and record the served
  upstream either way.** freellmapi fails over across its keys, but a pinned id can
  only hop between keys for providers serving that exact id, so a cooled provider
  returns an instant 429 with no hop available. `auto` has the whole catalog and
  keeps answering. The response body's top-level `model` is the ONLY thing that
  says who answered; `Backend.complete_meta` returns it and the report prints the
  mix, so an `auto` run is honest about being several models averaged.

## Design notes and reference - `docs/`

Durable material lives beside the code, not in the queue. This file stays the
queue, the dated measurements, and the route decisions.

- `docs/action-channel.md` - why free-text JSON stays the action channel, and the
  kernel/adjudicator split the RPG rung needs. Read before adding a second game's
  phases or touching `parse_action`.
- `docs/moral-framing.md` - the theme-polarity experiment, its confound, and the
  verified deception/framing prior work. Arms 3 (`1984-inv`) and 4 (`drill-en`)
  are BUILT as of 2026-08-27 and unrun; read it before running any of them, and
  before editing any blurb - the four English faces are length-matched on purpose
  and frozen.
- `docs/player-counts.md` - supported vs best-play sizes per rung, Secret Hitler's
  native blind-evil at 7+, and why a bigger cabal table worsens the denominator.
- `docs/prior-work.md` - AvalonBench and how to position against it. Read before
  flipping the repo public.
- `docs/reproducibility.md` - two 20-game runs at one seed came back byte-identical,
  so a same-seed repeat cannot measure spread. Read before scheduling ANY run whose
  purpose is variability, and before quoting a "+X% vs +Y%" comparison.

## Route: local is for spot-checks, not for gates

Local needs no wiring - `Backend` passes `--model` straight through and the router
is exact-match, so any armed model is one flag away. The question is whether it is
worth running there at all, and for the GATES it is not: local is serial, ~9 min a
game, so the N-game statistics gate #3 needs are unaffordable there. Local's job is
the thing cloud cannot do - an uncensored model, privately, to answer "will it
deceive at all" - and that answer is already in hand.

Reach for a better local model (a qwen3.8-27b, or a half-resident quant sized so an
image-diffusion model stays co-resident on the 16 GB card) only when one of these
lands: a cloud model turns out to REFUSE to deceive (untested - the one cloud run
was void), or you want games running alongside image gen. Neither is on the gate
path today.

## Backend notes (measured 2026-08-25)

- `local:8090` armed: `rocinante-x-12b-heretic-q4`. The heretic 12B
  deceives without any prompt escalation - the mimic fabricated a prior private
  conversation to build credibility, the hunter played concerned-loyalist and then
  correctly named the seer. `PLAYER_SYSTEM_PROMPT` needed no jailbreak. Cost: ~3s
  per decision, ~9 min per game, serial.
- **Burst-probe result, gray, 2026-08-25 23:10 - the single-call trap firing
  exactly as documented.** Pinned `gpt-oss-120b`: **1/12 served, 11 instant 429s**
  (`All models exhausted: 8 routes checked, 7 rate-limited or on cooldown, 1 no
  usable key`), and the ONE success was the FASTEST call of the set at 0.4s. A
  single-call probe would have reported the tier healthy and fast. This is why the
  `huntcloud` run sat alive for 72 minutes and wrote zero games: pinned to a model
  whose whole route pool was cooled, refused in 40ms, nothing to fail over to.
  Killed rather than waited out - free-tier cooldowns clear on nobody's schedule.
- **`auto` availability is NOT `auto` capability** (same probe, same minute).
  `auto` served **12/12 at 0.3s median** - but the upstreams were
  `gpt-oss-20b`, `gpt-oss-safeguard-20b` (x5), `nemotron-3-nano-30b-a3b` (x6). Not
  one 120B-class model: the big ones are exactly what is cooled. So `auto`'s
  composition is time-varying and **anti-correlated with the thing being measured**
  - it degrades precisely when capacity is short, which is when you reach for it.
  A gate run on tonight's `auto` would most likely read "hunter at chance" while
  actually measuring which models were uncooled at 23:10. Given -0.2% on the 12B
  vs +66% on 120B-class, a 20B/30B-nano mix sits near the at-chance end. False
  negative wearing a real number; worse than no run.
- `clean:3001` needs `PARLOR_API_KEY`. Pin a model - `glm-4.7` is in `/v1/models`
  and 404s at call time (stale catalog entry), and `auto` silently varies the
  upstream per request. Live and answering: `minimax-m3`, `nemotron-3-super`,
  `qwen3-30b-a3b-fp8`, `gpt-oss-120b`, `glm-4.7-flash`. Bursts draw 429s - hence the
  transport backoff and `--workers 3`.
- **The cap was the cause, and 1536 is not enough for a rambler** (measured
  2026-08-25, same VOTE prompt, n=4 per cell, `clean`). `nemotron-3-super`:
  `max_tokens=512` -> 0/4 parsed, every reply ~2100 chars of visible reasoning cut
  mid-sentence; at 1536 -> 2/4, and both failures were ~6000 chars, i.e. truncated
  at the new cap too. So a model that thinks out loud does it at whatever length it
  likes and no cap is a fix. `gpt-oss-120b` answers in 80-125 chars, 4/4 at both
  caps - pin it for gate runs. `minimax-m3` itself is still unverified: the
  provider has been 429ing it since the void run, and a 429 is a transport failure,
  not a refusal. `qwen3-30b-a3b-fp8` and `glm-4.7-flash` currently 502.
