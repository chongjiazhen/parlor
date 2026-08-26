# RESUME - open work

Queue only. Done work leaves to git log. What's next:

- [x] **`hunt20` landed, was scored, and then the STATISTIC turned out to be
      wrong. Gate #3a is NOT SHOWN.** 20/20 games, rc=0, 0.49% fallback
      (11/2231), 100% pinned `qwen36-35b-a3b-iq3`. Re-scored 2026-08-26 on the
      corrected metric, no new games needed - every input was already in the JSONL:

      | stratum | discrimination | n clean/tainted | 95% CI (per-game bootstrap) |
      |---|---|---|---|
      | pooled, all good (old headline) | +31.55% | 159/228 | [+22.78%, +39.68%] |
      | **`none` - loyalist - THE GATE** | **+2.53%** | 53/76 | **[-13.45%, +18.04%]** |
      | `magic` - watcher | +7.00% | 53/76 | [-9.71%, +23.46%] |
      | `evil` - seer | +85.13% | 53/76 | [+77.14%, +92.77%] |

      - **The entire gate #3a signal was the seer spending handed knowledge.** The
        seats that had to deduce sit at +2.53% with an interval straddling zero.
        The earlier "+30.7% / +31.55%, gate #3a holds, reproduced" claim was an
        artifact of pooling three populations.
      - The intermediate `+13.57%` figure (headline for about an hour on
        2026-08-26) was wrong two ways at once: `p_clean` was unfiltered, so it
        carried the seer's clean-team certification (94.3% vs the loyalist's
        73.6%), and the watcher sat in the "blind" pool while holding an aura pair
        that certifies taint outright on some team shapes.
      - **Gate #3b also not shown**: hunter 33.33% (3/9, CI 12.06%-64.58%), and
        that 3/9 was scored under the old rule where the model chose from 4 targets
        against a 3-target control.
      - **Gate #2 stays unreadable** by its own conditionality - evil 70%, but 5 of
        20 wins were `five_rejects`.
      - Found by a modelling-logic review (Fable, 2026-08-26). Its full text and
        the re-score are in `_review-modelling.md` (gitignored). Its remaining
        unactioned findings are the items below.
- [ ] **Residual confounds in the corrected metric - scope the CLAIM, do not
      pretend they are fixed.**
      - **Seer-originated public signal.** Clean teams are disproportionately
        seer-proposed, and its votes and speech are public. A blind seat trusting
        a seat it has learned to trust is doing real social deduction, but it is
        the seer's knowledge one hop removed. Unremovable without removing the
        game. So gate #3a-blind measures *information reaching blind seats through
        play*, not *blind seats detecting evil unaided* - and the report must say
        that rather than claiming the number is deconfounded.
      - **Self-membership.** A seat votes differently on a team it is ON, and at 5
        seats a clean 3-team contains ALL three good seats, so nearly every blind
        clean vote is a self-vote. Measured on seed 1000: loyalist OFF-team
        -13.83% (n=9/49) vs ON-team +3.20% (n=44/27). Only 9 off-team clean votes
        exist at 5p, so it cannot be conditioned away here - report the split,
        state the residual.
      - Both push the honest number DOWN, not up.
- [x] **Graded taint landed 2026-08-26 - and it does NOT rescue gate #3a, it
      sharpens the null.** I called it "the only route to a resolvable gate";
      that oversold it. What it actually buys is precision, measured on the same
      seed-1000 records with no new games:

      | metric | estimate | 95% CI | width |
      |---|---|---|---|
      | binary clean-vs-tainted | +2.53% | [-13.45%, +18.04%] | 31.5 pts |
      | **graded, per extra saboteur** | **+1.20%** | **[-8.44%, +9.63%]** | **18.1 pts** |

      Interval width nearly halved at the same N. The dose-response is flat -
      approval by taint level runs **74% / 71% / 71%** - and the 1-to-2 step goes
      marginally the WRONG way, so there is no signal to find rather than a weak
      one being lost in noise.
      - Slope = OLS of approval on the evil count, sign-flipped so positive means
        "approves less as the team gets dirtier". It DEGENERATES to the binary
        figure when only two levels occur, so it is a better estimator of the same
        quantity, not a different claim - there is a test asserting exactly that.
      - The per-level table ships beside the slope, because a slope alone hides
        non-monotonicity, and a seat that rejects one saboteur but approves two is
        not a weak deducer - it is responding to something other than taint.
      - Binary figure still printed, marked superseded. Kept because earlier runs
        reported it, not because it means anything.
- [ ] **Derive the hunter baseline from the legal target set, not a hardcoded
      1/3.** `run_games.py` hardcodes `hunter_baseline: 1/3` and prints "chance
      33.33%". Both are correct ONLY at 5 seats with a hunter that knows its ally.
      At 7p/3-evil the legal set is 4; under the queued blind-evil variant it is 4
      at 5 seats too - and `RandomPolicy` and `validate_hunt` both derive from
      `entitled_knowledge`, so they will silently agree on the new set while the
      scorer keeps gating against 1/3, in the flattering direction. Compute it as
      `1/len(legal_targets)` from the same source the policy uses.
- [ ] **Condition over-sabotage on the game continuing before quoting 41%.** A
      double fail on evil's THIRD failed mission is costless - the game ends there,
      the identification is never paid for, and it weakly insures against a
      miscount. Those rows are not coordination failures. `audit_decisions.py`
      counts every `fails > need`.
- [ ] **`outed_own_role_in_public` reads near-zero by construction, not by
      virtue.** It matches functional keys (`seer`, `mimic`) against speech
      rendered in the 1984 theme, where seats say "Thought Police" and
      "Doublethinker". The reported 0/1290 supports nothing. Match theme names too,
      or scope the check to `--theme plain` runs.
- [ ] **`hunt_named_impossible` assumes the current knowledge model.** It derives
      allies as "all other evils", correct at 5p but wrong under a future
      `sees_fellow_evil=False` variant, where it would flag legal hunts as
      regressions. Same trap as the hardcoded 1/3.
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
- [x] **Seed 1000 re-run landed 2026-08-26 (`hunt20b`) - and it is VOID as a
      comparison. The tripwire fired and it was right.** 20/20 games, 4h42m, 0.54%
      fallback (11/2033), 100% pinned `qwen36-35b-a3b-iq3`, zero errors. The item
      predicted "hunter shifts slightly and nothing else; if anything else moves,
      something else changed too". Everything moved, and **three** things had
      changed, not one:
      1. **`c43274e` put the `need` disclosure in the MISSION ask at 08:13**, 43
         minutes before launch. This file says that change "must land first and
         alone or the two are confounded". It did not. (It also did not do its job:
         over-sabotage is 41% of sunk missions in BOTH runs - 12/29 then 15/37 - so
         the focal-point problem was never threshold ignorance, exactly as the
         over-sabotage item argued.)
      2. **The sampler was never seeded.** `--seed` fixed the deal and the fallback
         RNG and nothing about the model, so the two runs are two different draws:
         63 missions and 9 hunts one night, 74 and 11 the next. Fixed since
         (`2cfe9d5`, see §Measured), but it fixes nothing retroactively.
      3. **The two runs were scored by different code.** `hunt20`'s JSONL predates
         both `knowledge_class` and `team_evil_count`, so the current `score()`
         cannot read it at all - its "+2.53% / +1.20%" line in this file came from a
         separate reconstruction pass, not from the scorer the new run used.
      - **Gate #3b still not shown, and that verdict IS safe** - it is a floor test
        computed inside one run: hunter 6/11 = 54.55%, Wilson floor 28.01%, short of
        the 1/3 bar. Per the pre-committed criterion the answer is "not shown at
        this N", not "run more games until it clears".
      - **Gate #3a's movement is NOT bankable.** Blind taint sensitivity went
        +1.20% -> +8.82% with a floor clearing 0 for the first time. That is one
        draw, against three uncontrolled differences, with intervals that overlap
        heavily. Reporting it as "gate #3a holds" would repeat the exact error this
        file caught a week ago - a real number pooled or drawn from the wrong
        population and quoted as a finding.
- [x] **`hunt20c` LANDED 2026-08-26 21:29:52 SGT - the anchor exists.** 20/20
      games, 6h37m (23818.2s), off commit `f8c5f71`, clean tree, seed 1000, 2
      rounds, pinned `qwen36-35b-a3b-iq3` (100% served), notebook OFF, zero errors,
      1.78% fallback (48/2691). It is the first run in the repo a later run can be
      compared against.
      - **Both gates not shown, and both verdicts are safe.** Blind taint
        sensitivity +9.00% [-0.25%, +18.18%] - the floor INCLUDES 0. Hunter 5/9 =
        55.56%, floor 26.66%, short of the 1/3 bar for the third run running. Evil
        80.00% [58.40%, 91.93%], unreadable per the gate-#2-is-conditional rule.
      - **The result of the day is a negative, and it is about the INSTRUMENT.**
        `hunt20b` reported +8.82% [+0.94%, +16.82%]; `hunt20c` reports +9.00%
        [-0.25%, +18.18%]. The point estimates are effectively the same and the
        floor verdict INVERTS. At n=20 the floor's position relative to 0 is being
        decided by noise, not by signal - so "the CI floor cleared 0" is not a
        finding at this N, and anyone reading `hunt20b`'s floor as "gate #3a holds"
        would have had to unread it tonight. Second independent reason the `hunt20b`
        void was correct.
      - **This is still NOT the spread measurement.** `hunt20b` ran pre-`2cfe9d5`
        with an unseeded sampler; `hunt20c` is post. One uncontrolled variable
        remains between them, so the above is suggestive, not measured. The pair
        that measures spread is `hunt20c` + `hunt20d`, both off the same code.
      - **The graded slope is fitting a step function - two runs now agree.**
        Approval by taint level: `hunt20b` 93/70/77, `hunt20c` 82/64/64. Both show a
        real 0->1 drop and NO further response at 2; `hunt20c`'s 1->2 leg is exactly
        flat. A linear "+X% per extra saboteur" through a step is the wrong
        statistic, and in both runs the binary clean-vs-tainted split is the
        better-behaved one (`hunt20c`: +18.11% [+3.52%, +33.53%]). The scorer's
        "superseded by the graded slope above" note has it backwards; fix that
        before the next scoring pass, and see the taint-level item.
      - **`llama-server` degrades over a long run - the fallback rate is partly a
        function of RUN LENGTH.** Games 0-6 ran 0.83% (8/968); games 7-19 ran 2.32%
        (40/1723); the last five ran 2.73% (15/549). Bucketing the refusal traces
        mid-run: EMPTY replies (`reply: ''`) grew 22 -> 32 while every parse-failure
        bucket stayed flat or fell, and `3 attempts failed, playing random` more
        than doubled. Empties are the server returning nothing, not the model
        answering badly. Carry this into the pair: `hunt20d` is the same length and
        should show the same shape - if it does not, that is a fact about the
        backend, not the game.
      - **Evil's win PATH moved a lot**: `five_rejects` 0/20 in `hunt20b` -> 6/20
        here, now the single most common path (vs missions_failed 5, hunt_hit 5).
        Deadlocking the table is not sabotage; if this holds in `hunt20d` it changes
        what gate #2 would even be measuring.
- [ ] **NEXT: `hunt20d` - the paired re-run that measures the spread.** Same
      everything as `hunt20c`: 20 games, seed 1000, 2 rounds, pinned
      `qwen36-35b-a3b-iq3`, notebook OFF, `eval\runs\hunt-local.cmd hunt20d 20 1000`.
      Budget ~6h40m on the GPU.
      - **Launching off HEAD is valid and was checked.** `git diff f8c5f71..HEAD`
        over non-`.md` paths is EMPTY - the four commits since the anchor are all
        docs. Re-run that check at launch time, not from this line.
      - What the pair buys, in order: the run-to-run spread on blind taint
        sensitivity (the number every "+X% vs +Y%" claim in this file has assumed
        and none has measured); whether the step-not-slope shape replicates a third
        time; whether the `five_rejects` path shift is real; and whether the
        transport degradation is a property of run length.
      - **The spread is the ONUW/cloud decision variable.** Wider than the ~+9pp
        effect -> 5-seat cabal cannot show gate #3a at an affordable N. See the
        Spike #1.5 item.
- [ ] **The JSONL records no REASON for a fallback.** Every `fell_back` entry in
      `decision_log` carries `note: ""` and `served_by: ""`, so a run's refusal
      diagnosis exists only in `trace_sample` (sampled, 8/game) and the log's final
      report block (deduped, capped at 6 lines) - neither of which is a census, and
      the second of which does not exist until the run ends. Diagnosing the
      `hunt20c` fallback drift mid-run meant bucketing sampled traces and saying so
      out loud; the next reader may not add the caveat. Populate `note` on the
      fallback path, where the refusal string is already in hand.
- [ ] **The scorer steers readers to the mis-specified statistic - do NOT fix this
      until `hunt20d`.** `_blind_line` prints "superseded by the graded slope above,
      which uses every taint level" (`eval/run_games.py`), but the taint response
      looks like a STEP in both runs that have the table (`hunt20b` 93/70/77,
      `hunt20c` 82/64/64), and an OLS slope through a step is the wrong summary.
      **The reason to wait**: retargeting that note would rest on two draws of n=20
      whose 1->2 legs sit inside noise - the same evidence quality this file just
      finished voiding a gate verdict over. Fixing it now would be the `hunt20b`
      error wearing a different hat. `hunt20d`'s table is the trigger: a third flat
      or rising 1->2 leg makes it a shape, and then change the note AND make
      `taint_sensitivity` say the slope is fitted to a non-monotone table.
- [ ] **The local launcher loses its own completion marker.** `hunt20b` finished
      cleanly - full report, complete JSON, 20 JSONL lines, zero errors - and wrote
      no `DONE rc=` line, because `cmd.exe` did not survive to echo it after python
      exited. That line is the one thing distinguishing "finished" from "killed at
      hour four", which is exactly the judgement the detached-run invariant says to
      make from the log alone. Have `run_games.py` write its own terminal marker
      rather than trusting the wrapper to outlive it.
- [ ] **Re-plan the cloud arm - it is dead, not pending.** `huntcloud` was killed 2026-08-25
      23:10 after 72 minutes alive with zero games written: it pinned
      `gpt-oss-120b` (not `auto`, whatever an earlier version of this line said) on
      a tier where 7 of that model's 8 routes were cooled, so every call was refused
      in 40ms. Burst-probe evidence in §Backend notes.
      - **ONUW is not an option on this list.** An earlier version of this line
        offered "spend the effort on ONUW instead" as the preferred third choice.
        It is not an alternative to fixing cloud - it is concurrent work on a
        different game, and cabal still needs its N from somewhere. See its item.
      - **Do not run `auto` to get games moving.** The tier's population is
        currently 20B/30B-nano, and gate #3 is known to be model-capability-bound:
        identical prompts scored -0.2% on the 12B and +66% on cloud. A null from
        that population is a fact about the model, not about the game, and it would
        be indistinguishable in the records from a real negative result.
      - **The only real option is a pinned known-good model once its routes cool.**
        `gpt-oss-120b` answers in 80-125 chars, 4/4 at both caps (§Backend notes) -
        pin it, never `auto`. Unblock condition is mechanical: a burst probe passes
        on it. Until then this item is parked, not pending.
      - **It may not be needed at all.** Cloud was wanted because gate #3 reads as
        a cloud-scale job, but that predates any measurement of the run-to-run
        spread. The anchor pair settles whether local N suffices; gate #3b already
        looks like 2-4 overnight local runs. Decide the cloud arm after the pair,
        not before.
- [ ] **Move `run-hunt20.cmd` into `eval/runs/` once the run lands.** The cloud
      launcher moved there 2026-08-26 and is now tracked and probe-gated
      (`eval/runs/hunt-cloud.cmd`); the local one is still the untracked copy in
      `eval/records/`, and it is NOT safe to move while it executes - `cmd.exe`
      reads a batch file incrementally, so moving it mid-run can lose the trailing
      `DONE rc=` line. Launchers are inputs, not run output; `eval/records/` is
      gitignored, which is why tonight's misconfigured cloud recipe left no
      reviewable record of what it launched.
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
- [ ] **A per-seat private notebook - BUILT 2026-08-26, UNMEASURED.** `--notebook`
      on `run_games.py` and `demo.py`; off by default. A seat's `note` is filed
      under its own seat and rendered back to that seat alone on every later call,
      so a read survives the turn that formed it. Cap: last 6 lines of 160
      characters, stamped with the mission it was written on.
      - **It is a prompt change, so it is a MEASURED change** (`--notebook` vs not,
        same seeds, one variable, reported beside its fallback rate) and it waits
        behind the seed-1000 re-run the same way the negation pass does. Nothing
        about it is quotable until that arm exists.
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
- [ ] **Gate #3 needs N far past 8 games.** Hunter accuracy is 1-in-5 to 3-in-6 at
      n<=6 hunts; the CI floor cannot clear 1/3 at that size whatever the truth is.
      And `good approve clean team` runs on ~12 votes a run, because most teams in a
      5-seat game carry an evil - that denominator is too thin to gate on.
      "This is a cloud-scale job, so it waits on quota, not on the GPU" is what this
      line used to say, and it was written before anything measured the run-to-run
      spread or the local per-game cost. Gate #3b now looks like 2-4 overnight local
      runs. Whether cloud is needed is a question the anchor pair answers - see the
      cloud-arm item.
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
        The gate-#3-needs-N item above blames the ~12-votes-a-run sample on the
        5-seat size ("because most teams in a 5-seat game carry an evil"), which
        implies a larger table would help. It would not. Clean teams get
        combinatorially rarer as seats grow, faster than the extra good voters
        compensate; gate #3b is untouched at any size since hunts are one per game.
        Arithmetic, table, and the graded-taint fix that DOES work:
        `docs/player-counts.md`.
      - Watch role-name vs faction-name substring collisions in the leak audit (see
        the plain-skin "Loyalist" case).
- [ ] **Naming discipline, for when ONUW gets built.** Prose may NAME the games a
      rung is modelled on - README has done that since commit #1 and that is
      nominative reference, not passing off. What must never enter the canonical
      layer is a game's expression: its role names, art, or text. So ONUW's roles
      arrive as functional keys (`swapper`, `switcher`, `deceived`), never as the
      published character names, exactly as this game uses seer/watcher/mimic.
- [ ] **Spike #1.5: One Night Ultimate Werewolf** - ahead of Secret Hitler, and not
      for freshness. Two reasons, both structural:
      - **Belief != truth.** Robber/troublemaker/drunk swap roles during the night,
        so a seat's knowledge of ITS OWN role can be stale and false. `SeatView`
        renders truth today; ONUW forces the split between what is true and what
        this seat believes, and makes gate #1 strictly harder - the referee must
        maintain a false belief without correcting it and without leaking the swap.
        Sharper test of independent context than cabal can pose, where every seat's
        knowledge is both true and static.
      - **It fixes the N bottleneck.** One night, one discussion, one vote: ~10-15
        model calls against cabal's 80-220, so 10-20x the games per hour. Every hard
        question this session was gated on games-per-hour (14 min/game local, 5
        hunts per 12 games, a gate needing 30+). ONUW turns "cannot afford the N"
        into "run 200 overnight".
      Also no elimination, which is the point of preferring this family. Secret
      Hitler stays the better LADDER step (forced reveals, a deck the referee
      controls) but ONUW is the better ENGINE step.
      - **The constraint is "do not change cabal's RULES mid-measurement", NOT "do
        not build game #2".** This line used to read "do it only once gate #3 is
        called", which contradicts the N argument directly above it: it pays the
        expensive N in the game that is worst at producing it, before building the
        thing that makes N cheap. They do not compete for the same resource either -
        cabal's remaining cost is GPU wall-clock, ONUW's is attention, and the card
        is booked either way. So ONUW is buildable NOW, alongside a running hunt.
        What must not happen concurrently is an edit to what a cabal seat knows or
        is asked; that is the 6/7p item's block and it stands.
      - **ONUW does not retire cabal's gates.** Different rung, different deduction
        task. Building it decides which game's numbers get published first. It
        settles nothing about gate #3, and a cabal gate left uncalled stays uncalled.
      - **When to stop spending GPU on cabal's gate #3: after the anchor pair, if
        the run-to-run spread is as wide as the effect.** `hunt20c` plus one paired
        re-run is the first comparison the repo can make, and the spread it measures
        is the decision. Wider than the ~+9pp taint sensitivity -> 5-seat cabal
        cannot show gate #3a at an affordable N, and the GPU goes to ONUW. Narrower
        -> the N is known and it is a scheduling call. Gate #3b is a separate and
        cheaper question: 54.55% observed puts it in the ~32-62 hunt band, which at
        `hunt20b`'s 0.55 hunts/game is 58-113 games, 2-4 overnight runs.
      - It is also the pressure test for what really belongs in `core/`, and that
        question wants evidence, not a guess - an argument for building it while the
        cabal answer is open, not after.
      - **Ship a werewolf-vocabulary theme on this rung, and that is the whole
        answer to public legibility.** A public repo has a real problem that "team-
        mission hidden-role deduction game" means nothing to anyone outside the
        hobby, while "werewolf / seer / villager" means something to nearly
        everyone. That vocabulary is public-domain folk-game vocabulary (Mafia,
        Davidoff 1986) carrying no branding question, and it lands free on a rung
        already queued on engine grounds. **This is why a vanilla Werewolf rung is
        NOT worth building for legibility**: it sits on the same rung as cabal
        (deterministic referee, bounded actions, no judgment), so it buys
        recognition and no engine progress, and it has elimination - a shrinking
        table, variable agent count per game, dead seats contributing no decisions,
        i.e. the N problem from the wrong side. Legibility is a theme and a README
        paragraph, not a spike.
- [ ] Spike #2: off-map faction heartbeat - factions acting on their own clock,
      driven by a long-running agent process outside the game loop.
- [ ] **Evil over-sabotages, and it is the seer-salience bug wearing the other
      team's colours.** Scored on the FULL 20-game run: 63 mission resolutions,
      fail-count distribution `{0: 34, 1: 17, 2: 12}`, need=1 throughout. So **12
      of 29 failed missions (41%) had BOTH evils play fail when one sufficed**, and
      12 of 63 missions overall (19%). The partial-run figure was 45%/9-of-20; the
      full run settles it at 41%.
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
- [ ] **Two shapes not to harden further before game #2** - cabal's `Phase` enum,
      the `action_prompt` if-chain, and `ACTION_KEYS`. Reasoning and the exact
      constraint: `docs/action-channel.md`.

## Pre-committed criterion for the hunt run (written 2026-08-25 19:54, BEFORE the numbers)

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
they are. The first controlled pair will be `hunt20c` vs `hunt20d`.

| what | `hunt20` (08-25 19:54) | `hunt20b` (08-26 08:56) | `hunt20c` (08-26 14:52) |
|---|---|---|---|
| blind taint sensitivity - THE GATE | +1.20% [-8.44%, +9.63%] | +8.82% [+0.94%, +16.82%] | +9.00% [**-0.25%**, +18.18%] |
| blind, binary (superseded - see below) | +2.53% [-13.45%, +18.04%] | +19.94% [+6.27%, +32.02%] | +18.11% [+3.52%, +33.53%] |
| approval by taint level, blind | - | 93% / 70% / 77% (41/44, 28/40, 24/31) | 82% / 64% / 64% (41/50, 37/58, 32/50) |
| hunter | 3/9 = 33.33%, floor 12.06% | 6/11 = 54.55%, floor 28.01% | 5/9 = 55.56%, floor 26.66% |
| evil win rate | 70%, 5 of 14 by `five_rejects` | 75%, **0** by `five_rejects` | 80%, **6 of 16** by `five_rejects` |
| evil win paths | 6 missions / 5 rejects / 3 hunts | 9 missions / 0 rejects / 6 hunts | 5 missions / 6 rejects / 5 hunts |
| missions, fail-card distribution | 63, `{0:34, 1:17, 2:12}` | 74, `{0:37, 1:22, 2:15}` | 62, `{0:35, 1:15, 2:12}` (derived) |
| over-sabotage, share of sunk (unconditioned - see the open item) | 12/29 = 41% | 15/37 = 41% | 12/27 = 44% |
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

## Decisions already locked

**Code invariants moved to `CLAUDE.md`** - it is always loaded, these are not,
and two copies of one rule is how the stale copy wins an argument. What stays
here is project state: the route calls and what a run measured.

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
  verified deception/framing prior work. Read before designing arm 3.
- `docs/player-counts.md` - supported vs best-play sizes per rung, Secret Hitler's
  native blind-evil at 7+, and why a bigger cabal table worsens the denominator.
- `docs/prior-work.md` - AvalonBench and how to position against it. Read before
  flipping the repo public.

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
