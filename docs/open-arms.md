# Open arms - the reasoning behind the open queue rows

`queue.md` is the queue and is budgeted in bytes, so it carries the ASK and the
entry condition for each open row. What it cannot carry is the argument behind
the row - why the arm is worth running, what it confounds, what a result would
and would not establish. That is what is here.

**Read the entry for a row before taking that row**, not before picking one. The
queue is what ranks the work; this file is what you need once you have chosen.

Moved out of `queue.md` 2026-08-28, when the queue was 68 KB against its own
30 KB budget and the ratchet had been holding it flat rather than shrinking it.
**Nothing was rewritten - every entry below is verbatim where it came from**,
which is the same rule the 2026-08-28 `docs/` split followed. A row that has
since been reworded in the queue is the live statement; this is the reasoning.


## Gate #2 has a cheaper falsifiable design

- [ ] **Gate #2 has a cheaper falsifiable design than waiting on gate #3.**
      `--arm llm` vs `--arm llm-good` on the same seeds isolates evil's
      contribution against a fixed opponent population, using arms that already
      exist. The conditionality then softens from a hard refusal to "the
      unconditional headline rate is only quotable once #3 holds". Also: the ~65%
      no-deception baseline is a property of `RandomPolicy(fail_rate, approve_rate)`,
      not of the game - fine as an existence proof, wrong if quoted as the game's
      intrinsic evil floor. And `rate_ok`'s 5% CI-floor bar is pre-declared
      nowhere; it deserves a line in the pre-committed criterion the way 3b's did.


## Two behaviours the auditor prices, neither of them bugs

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


## What writes a stale `.git/index.lock`

- [ ] **Find what writes a stale `.git/index.lock` in this repo.** 2026-08-28: a
      0-byte lock appeared at 08:44 with no `git.exe` running and blocked a commit
      40 minutes later, mid-session, with the index intact. Removing it was the
      documented remedy and cost nothing - but an unattended run that commits its
      own records would have died on it, silently, at a point where the run itself
      was healthy. Candidates: the rtk PreToolUse hook, which is EXCLUDED for git
      on WSL but **live on native Windows** (`RTK.md`), or a crashed helper. Cheap
      probe: log the lock's ctime against the tool-call transcript next time it
      appears. Until then, `/mingw64/bin/git` for anything whose answer gates a
      commit, which is `RTK.md`'s standing rule anyway.


## Negation pass over the model-facing strings

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
      a prompt edit landed mid-campaign confounds that campaign exactly the way
      `c43274e` confounded `hunt20b`. **UNBLOCKED 2026-08-28**: S6 is down, nothing
      is in flight, and the standing rule is the check rather than the wait - run
      the liveness command above before landing it, not a remembered freeze.
      **Re-homed 2026-08-27 (S1):** measure it on changeling, where a paired
      20-game arm is ~30 min against cabal's 13.2 h. Cabal's referee refusals stay
      as written.


## Does the standing frame belong in the PAYLOAD? A `--briefing` arm

- [ ] **Does the standing frame belong in the PAYLOAD? A `--briefing` arm.** The
      ask carries the rule that bites in that phase and no more - VOTE the
      five-reject rule, MISSION `need` and the stake, PROPOSE nothing about what
      wins. Deliberate per-phase drip (`referee.py`, the `need` comment) and
      unplayable for a person, which is why the console got a `BRIEFING` OUTSIDE
      the payload. Whether a MODEL wants it is unmeasured, and the one measurement
      here cuts both ways: `_night_against_the_table` restates a fact the seat held
      already, +7% -> +63% on the 12B, INVERTED on q36 (+80% vs +72%) - so expect a
      capability-dependent sign. **The lane notes make ABSENCE the novel arm**:
      every build read from source states full rules in the system prompt and none
      ablates that. Off by default, one variable, re-baselines what runs under it;
      changeling (~30 min). **Done when** a paired arm exists, both fallback rates.


## A per-seat private notebook - built, unmeasured

- [ ] **A per-seat private notebook - BUILT 2026-08-26, UNMEASURED.** `--notebook`
      on `run_cabal.py` and `demo.py`; off by default. A seat's `note` is filed
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


## Larger setups (6/7p) + the two information-degrading evils

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
      - **The gate that gated this is CALLED** - 3a retired and 3b not shown,
        2026-08-27 - so the sequencing constraint is now only the general one:
        changing what the seer knows mid-run means neither the old nor the new
        number means anything. Land it between campaigns, as the hardening pass you
        would actually publish from. What still blocks it is that cabal has no GPU
        program left, not a gate.
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
        identical by construction. **FIXED 2026-08-27, and the remedy this file
        proposed was the wrong one.** Re-keying `secret_terms` so identical-role
        seats do not audit against each other is a blanket skip, and a skip buys
        the false positive off with a false negative - the audit would then be
        blind to the referee genuinely naming a same-role seat, which is the
        shipped-leak half the top invariant refuses. What landed instead narrows
        the CORPUS, the way `include_speech=False` already does: the viewer's own
        "Your role:" line is removed before the scan, since that is the only place
        the referee asserts a seat's role to that seat. `find_leaks` stays naive, a
        duplicate term anywhere else still fires, and the same shape is what
        changeling reached from the other side. Mutation-checked - the blanket skip
        was written, and it kills the soundness test by name.


## Seat the changeling expansion cards, which means picking a deck

- [ ] **Seat the changeling expansion cards, which means picking a deck.** The
      cards themselves landed 2026-08-27: `kindred` (the pack's mirror on the
      village side) and `waker` (acts last, so it is the only seat whose belief is
      guaranteed true at dawn) are implemented, skinned, resolved and tested, and
      `SETUP_5` deals neither - the same footing as cabal's `LURKER`/`STRAY`, for
      the same reason: every recorded changeling number was played on the
      eight-card deck, so a deck change re-baselines all of them. **The DECK DESIGN
      landed 2026-08-27** in `games/changeling/RULES.md` §The decks that would seat
      them, and that section is the source of record - two decks, each with its
      arithmetic measured over 4000 nights, plus the four expansions costed and not
      built. **Do not restate its numbers here.** What is open is the part a design
      doc cannot close:
      - **Register the setups, then measure.** Both decks are UNBLOCKED as of
        2026-08-28 - they waited on keying the knowledge class on what the seat was
        told, which landed in S10. `py -3 -m eval.strata` prices a deck's strata
        before it is built: add a row to its `DECKS` table and read the blind count
        off 4000 nights.
      - **Every deck change costs at least TWO variables.** `len(deck) == n +
        centre` means a card cannot be added without growing the table or the
        centre, so there is no one-variable arm in this game. Choose the second
        variable deliberately and report it.
      - **Route call: `waker` is the one worth a run.** Every other seat has to
        infer that the night moved it and this one is told, so it is the cleanest
        handle on whether a model reasons about divergence at all rather than about
        who is lying - and its deck seats it in 62% of games, so one run carries
        its own control with no paired second run.


## Candidate changeling skins - built, all unrun

- [ ] **Candidate changeling skins - BUILT 2026-08-27, ALL UNRUN.** `greek`,
      `greek-named`, `journey`, `investiture`, `masquerade` and `folk-inv` exist as
      themes; `DEFAULT_THEME` is still `folk` and no number has moved. **The design
      is `docs/moral-framing.md` §The changeling skin set - what each arm is FOR**,
      which owns the arm ladder, the name-form axis, the corpus-sourcing rules and
      the length control. Read it before running or editing any of them; do not
      restate it here.
      - **What is open is which arm gets GPU first**, and the ranking is a route
        call this file owes: `greek` for the vocabulary control, `folk-inv` for
        polarity, the `greek`/`greek-named` pair for name form - that pair being the
        cleanest single-variable manipulation in the repo, since it moves eight
        strings and nothing else.
      - **A blurb is a prompt**, so every face is frozen at its measured length and
        an edit orphans whatever has been recorded against it.


## Ship a werewolf-vocabulary theme on changeling

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


## "changeling feels random" - four levers, and which of them this rung already has

- [ ] **"changeling feels random" - instrument it before fixing it.** Raised
      2026-08-29 from hand play, against the folk account of why the family of
      one-night games this rung is modelled on feels arbitrary to new tables.
      Nothing here is a citation: the levers are restated in this repo's terms
      because the arguments stand or fall on their own, and none of them has been
      measured here.
      - **The starting position is that this rung's gate #3 HOLDS over 200 games.**
        So a table that wins is already discriminating. "Feels random" is a claim
        about a DIFFERENT quantity that no number here reports: whether the vote
        that lands was reasoned or lucky. **The first move is therefore an
        instrument, not a rule change** - a per-game deduction score off records
        that already exist, separating won-by-deduction from won-by-draw. Until
        that exists, every lever below is a fix to an unmeasured complaint, and
        adopting one blind would re-baseline the numbers that DO exist.
      - **Hidden role change is the thesis, not the defect.** A seat whose own card
        moved under it is what this rung was built to demonstrate and what
        separates it from cabal. It stays. What is worth asking is whether the
        seats are told plainly enough that it can happen - which is where the
        model-facing wording bug found the same day lands, since a seat told it
        "went to sleep as" its post-night card is being actively misinformed about
        exactly this.
      - **Tracking who moved what is a working-memory task, and this rung already
        has the affordance built.** `--notebook` (§A per-seat private notebook)
        is a per-seat scratchpad that survives the turn, built 2026-08-26 and
        never measured. This gives it a sharper hypothesis than "more context
        helps": a seat that cannot carry the night's swaps across rounds must vote
        on impressions, so the notebook should move the DEDUCTION score more than
        the win rate. That is a prediction the arm can falsify, which is better
        than the one it has now.
      - **Discussion length is already a flag and has never been an arm.**
        `discussion_rounds` defaults to 2. If a table is voting on impressions
        because it has not had room to argue, more rounds is the one-variable test,
        and it costs GPU linearly in decisions. Cheap, honest, and it may well
        return nothing - the measured pattern on this box is that extra context is
        not monotonically good.
      - **Village seats have no reason to bluff, and that is the strongest of these
        readings.** The folk account says an all-honest table collapses the game:
        with every villager stating what it did, contradictions come only from
        mechanical swaps, and nobody can tell a switch from a lie. This rung's ask
        never invites a village seat to say anything false, and the same argument
        is cabal's gate #3 wearing different clothes. **Measurable off existing
        records before any change**: how often does a village seat say something
        untrue? If the answer is ~never, the table is playing the collapsed game
        and the finding stands on its own, independent of any fix.
        - **MEASURED 2026-09-01 (S17), and the reading does not hold here.** A seat
          that believes itself a villager names a card it was never shown on 14.0%
          of its deal claims and 15.0% of its present claims over S2's 200 games;
          wolf-believing seats on 32.9% of present claims. So this table is not the
          all-honest one the argument assumes, and a lever justified by "nobody has
          any reason to lie" no longer has that justification here. Instrument
          `py -3 -m eval.changeling_claims`, numbers and caveats in
          `docs/measurements.md` §2026-09-01 (S17). Pre-S14 wording, and a LOWER
          bound - 42.2% of utterances name a card in a shape the claim rules do not
          read.
      - **A losing-is-winning role is the one genuinely new card here.** A seat
        that wins by being executed forces every other seat to weigh whether an
        accusation is being courted rather than earned, which is a reason to
        analyse behaviour rather than accuse the first contradiction. It is a
        RULES change and a new win condition, so it re-baselines everything and
        belongs behind the deck decision, not in front of it.
      - **One tension worth stating rather than resolving here.** The same account
        argues for FEWER chaotic moving parts until a table has the baseline
        deduction, which cuts against the standing route call that the expansion
        deck is the run worth having (§Seat the changeling expansion cards). Both
        cannot be tested first. The deduction instrument above is what would settle
        it, because it is the only thing that can say whether the current deck is
        already past what the seats can track.


## Spike #2: off-map faction heartbeat

- [ ] **Spike #2: off-map faction heartbeat - SCOPED 2026-08-27,
      `docs/faction-heartbeat.md`.** Read it before costing this against S8's other
      options, because the scoping moved it.
      - **It is not an alternative to the adjudicator spike, it is the small
        version of that spike's hardest part.** Both need the typed-fact channel -
        an actor declares its intended reveals as typed facts, entitlement is
        checked against those, and the prose is audited against the facts it did
        NOT declare. A faction needs it over three action types; a Storyteller over
        20+ characters of discretion. S8 lists them side by side as though they
        were separate options; they are not.
      - **The "long-running agent process" half of the original stub is
        backwards.** A wall-clock actor has no fixed call order, which voids the
        seed invariant `docs/reproducibility.md` measured. Ticks are counted, the
        schedule derives from the game seed, and whether a process drives it must
        not be observable in the record.
      - **The one new gate #1 failure, and it is silent**: entitlement gains a time
        axis, so a render must be audited against the entitlement snapshot taken
        when it was BUILT, never against entitlement recomputed at audit time - by
        then the fact may have gone public by other means and a real leak reads
        clean. Capture the snapshot with the render.
      - Faction decisions stay OUT of the run's denominator (the gates measure
        seats), and the faction's fallback rate is reported beside the run's.


## Evil over-sabotages

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
        and it needs no measurement to justify. The gate it was sequenced behind is
        called, so what is left is the ordinary rule: it changes behaviour, so it
        lands between campaigns and not into one.
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
      - Sequence: measured change, same seeds, one variable, between campaigns -
        the gate this waited on is called. Distribution above is from a PARTIAL run (13 of 20) and is an
        incidental mechanical count, not the pre-committed hunt metric - recompute
        on the full run before quoting it anywhere load-bearing.


## Theme as an experimental variable

- [ ] **Theme as an experimental variable, not a default to fix** (design:
      `docs/moral-framing.md`). `1984-en` stays the shipping default;
      there is no licensing reason to drop it and it is the face every committed
      transcript wears. What is open is that the blurb inverts moral polarity -
      sabotage reads as heroic, deceit as survival - and nothing measures whether
      that moves behaviour. No number in §Measured records which theme produced it,
      so a theme change is a MEASURED change on the same terms as the negation
      pass: same seeds, one variable, landed between campaigns. The gate it used to
      wait on is called.
      **Re-homed 2026-08-27 (S1)** to changeling, which ships a folk-game theme of
      its own and so poses the polarity question at 1/26th the GPU cost. `1984-en`
      remains cabal's shipping default and is the face of every committed
      transcript; nothing about cabal's theme changes.
      **Arms built 2026-08-27**, on cabal, as themes only: `1984-inv` (arm 3,
      villainous - the 1984 skin inverted rather than a new fiction, so 2-vs-3
      differs in valence and nothing else) and `drill-en` (arm 4, neutral - a
      sanctioned drill with no victim). Unrun, and adding them moved no number
      because nothing runs on a face until a run asks for it by name. (cabal's
      `DEFAULT_THEME` did later move, `1984-en` -> `plain` on 2026-08-28, for
      publish-surface reasons and not as an arm; `games/cabal/roles.py` carries
      that note beside both theme constants, which is where a reader of a number
      will be.) `bnw-en` was 84 words against `1984-en`'s 53, confounding the
      vocabulary control with density; trimmed the same day, and all four English
      faces are now 53 words / 281-291 chars. Frozen from here - a blurb is a
      prompt, so a later edit orphans whatever has been recorded against it. One
      thing left to settle before spending GPU: whether the run happens on cabal or
      on the re-homed changeling rung. A `bnw-inv` was considered and rejected -
      reasoning in the doc.


## Seat the solver as an ARM

- [x] **Seat the solver as an ARM - BUILT 2026-08-31T16:30:30.3689832Z.**
      `SolverPolicy` acts on mechanically certain VOTEs only and delegates mixed
      evidence plus every other phase to `RandomPolicy`; `--solver` seats it in the
      cabal demo. `evidence_from_referee(ref, seat)` remains the whole reader, so
      gate #1 safety is by construction. No campaign or measurement claimed. The
      hunt remains mechanically flat, so this policy can differ from random only at
      the VOTE, where the live question remains.


## Seat the heuristic against the MODEL

- [ ] **Seat the heuristic against the MODEL, which is the arm that does not exist
      yet.** The rung is built (`games/cabal/heuristic.py`, `python -m eval.ladder`)
      and both halves it can reach without a GPU are measured - see §Measured. What
      is missing is the third: a game with heuristic seats and LLM seats at the same
      table, which needs GPU and the eval driver's arm plumbing - and cabal has no
      GPU program left, so it queues behind changeling or lands at the publish
      boundary. Read the artifact warning in §Measured first - the
      all-heuristic arm's 99.5% hunter is a deterministic twin reading its own tell,
      and a mixed table is where that stops being a confound and starts being the
      measurement.


## Group-sequential design instead of a pre-committed fixed N

- [ ] **Group-sequential design instead of a pre-committed fixed N.** S6 commits
      40 games and forbids a third campaign, because stopping when a floor happens
      to cross is peeking - correct, and the named fix is not "don't look". It is
      alpha spending: Wald's SPRT (1945), O'Brien-Fleming boundaries (1979),
      Lan-DeMets (1983). A boundary computed BEFORE the run lets you look
      repeatedly and stop early legitimately, which on a 13.2 h campaign is real
      GPU. **It must be designed BEFORE the next campaign**, never retrofitted to
      S6's records - that would be the peeking it exists to prevent, which is the
      real gate here and not the freeze this line used to cite.


## Obtain the paywalled theory chapter

- [ ] **Obtain the paywalled theory chapter before publishing anything about gate
      #1.** It is the one result that could bound gate #1's shape, no free copy
      exists, and the route is a request to its authors. **The target, the reason
      it matters and the drafted request are off-repo**
      (`agi2026-chapter-request.md` beside the neighbour list; `CLAUDE.local.md`
      has the path) - a private request naming real people is not repo content.
      What belongs here is only the dependency: no public claim about gate #1
      until that chapter is read.
      Two published hybrids are in the same debt: both hand belief inference to a
      structured model and use the LLM only for language, i.e. the strongest
      results on this task come from NOT asking the model to deduce. That is the
      framing gate #3 should be reported against. Neither voids the gate; both
      change what its number means to a reader. Identifiers in the off-repo
      ledger.


## The thesis moved on 2026-08-27

- [ ] **The thesis moved on 2026-08-27 - `README.md` now leads on the product
      claim, and the off-repo positioning argument still leads on the research
      one.** The original thesis is LLM agents as GM *and teammates* for solitaire
      play; existing chat products give one counterparty, and a table of AI
      teammates is only interesting if they do not share a brain. So independent
      context is the PRODUCT REQUIREMENT, not a research property, and `README.md`
      was rewritten to lead on that. Both framings are true and aimed
      at different readers. **Reconcile them in the off-repo file, not here** - the
      failure to avoid is a stale copy that says which framing LEADS while
      disagreeing with the README. Three things to fold in there, all chat-only
      today:
      - **Which framing leads.** Product thesis primary, isolation-by-construction
        as the credential. The evidence is that mainstream multi-agent chat shares
        one history by construction, and where per-character state exists it is
        MEMORY - what a character recalls, not what it is forbidden to be told.
      - **The cost tension, which is the reason nobody does this.** Independent
        context costs N x tokens, and shipping products say so themselves when
        they explain why they centralize. The differentiator IS the cost
        structure, and any product framing has to answer it.
      - **The answer is already designed, filed under scoring.** The `SolverPolicy`
        in `docs/reference-policies.md` is specced as an INSTRUMENT,
        but it is also a teammate that plays correctly for zero tokens - the same
        move the published hybrids won with, and the direct answer to the N x
        bullet above. Cheap competent seats + a small model for the talking.
      **Also decided in that conversation and not yet anywhere:** the queue fanned
      out horizontally at rung 1 instead of cutting a thin path to the end (976
      lines, 25 open items, two games on the SAME rung, nine built-but-unrun
      things), and the walking skeleton that was missing got built by accident the
      same day as `--human`. The cut that follows - gates #2/#3 demoted from gates
      to dated model snapshots, which kills most of the theme, persona, 6/7p and
      cloud items - is the queue.md restructure, and it waits for S6 so the verdict
      section can drain to `docs/` complete rather than mid-flight.


## While the card is busy - the standing menu

Verbatim from `queue.md`, with ONE cell since superseded in place and dated -
the Secret Hitler verdict, reconciled below the table. The question behind it recurs - *a run is in flight,
so what can this session actually do?* - and the answer is stable, which is why
it is reference rather than queue.

The GPU-bound / attention-bound split above has a recurring question behind it:
*a run is in flight, so what can this session actually do?* The answer is stable,
so it lives here instead of being retyped. **The freeze is the binding
constraint, not the GPU** - no prompt, scorer or rules edit while an arm is
running, which rules out most of the queue and all of the measured work.

**Whether a freeze is in force is `queue.local.md`'s to say** - this table is
kept for whenever one is. Its standing lesson is the reusable half: an instrument
scored against records that already exist costs nothing and can outrank the run it
is waiting on.

| option | verdict | why |
|---|---|---|
| Secret Hitler | **no - SUPERSEDED 2026-08-28, see below** | *(2026-08-27 read, kept as written.)* Same rung as cabal - deterministic referee, bounded actions, no judgment - so it buys recognition and no engine progress. Identical argument to the one already made against a vanilla Werewolf rung. Its policy deck is more rules, not a different knowledge model |
| Blood on the Clocktower | **right target, wrong size - and now scope it against what exists** | The only one of these that is a genuinely different rung: the Storyteller makes *discretionary* rulings, which is the judgment-GM `docs/action-channel.md` splits the kernel/adjudicator for. But it is 20+ characters and the discretion is the hard part - so the session-sized version is a SPIKE that scopes the adjudicator against 3-4 characters, never the game. **Confirmed from outside 2026-08-27** - a public LLM-vs-LLM arena at this game already exists and is rated, another build scripts the storyteller outright, and a third puts an LLM in that seat; the off-repo ledger names all three. **So an LLM arena at this game is NOT the contribution. The discretionary adjudicator plus the entitlement audit is.** Two free controls worth copying from the rated one: shuffled turn order against positional advantage, and role-flipped mirrored matches |
| 5e / a rules-lite RPG | **the endgame, and not yet** | This is the rung the repo is aimed at. `docs/action-channel.md` says do not harden cabal's `Phase` enum, `action_prompt` chain or `ACTION_KEYS` before game #2 exists - and a rules-lite system is the honest cheap version of this, not 5e |
| `/improve-codebase-architecture` | **no, and least of all now** | A refactor under a freeze is risk with no measurement, and the two shapes actually worth restructuring are named in `docs/action-channel.md` as things to leave alone until game #2 |

**The Secret Hitler row is refuted by `quorum`, built the same day it was
written.** The row moved into this file verbatim at 20:30 on 2026-08-27; the
rung's design landed 16:20 and its referee 16:28, so the tree carried a live
recommendation against building what it had just built. The measurement the row
lacked is `games/quorum/RULES.md`, and it decides the opposite: **entitlement
here CASCADES over an object that did not exist at the deal.** Each legislative
event creates a fresh secret - a hand drawn from a shuffled deck - which passes
down a three-tier chain narrowing at each step, keyed to a ROTATING OFFICE rather
than to a dealt role. So the audit question changes shape: cabal asks *may this
seat know this fact*, quorum asks *may this seat know this fact at this point in
the chain*, and a referee caching entitlement per seat rather than per event is
wrong in a way that passes every cabal-era and changeling-era test. The
proposer's discard is the sharp case - an entitlement that EXPIRES one step down
a chain, with the next seat down actively trying to infer it - and **naive
substring matching cannot see it**, because a card's vocabulary is shared with
the public channel where a role name is not. That finding landed before the rung
had any code, which is exactly what the row said the game could not produce.

**What survives is the row's TEST, not its verdict.** "More rules, not a different
knowledge model" is still the right question to put to a candidate rung; it was
answered wrong here because it was asked of the published game's policy deck
instead of its entitlement chain. The neighbouring verdicts are untouched - no
model has played quorum, it has no gate, no criterion and no verdict, so this
reconciles a design position and promotes nothing.


**Direction, called 2026-08-27 against the literature** (argument kept off-repo):
gate #1 measures parlor and is durable; gates #2 and #3 measure a MODEL and decay
with the next checkpoint - S1 already found the tell, -0.2% on a 12B against +66%
on 120B-class. Nothing built so far de-risks the actual product claim, "a referee
that oversees without micromanaging". So after S6 and the S5 read, the next spike
is the **adjudicator** against 3-4 discretion-heavy characters - not a whole
game's roster, and not Secret Hitler, which is cabal's rung again.


## 2026-09-02 - moved from queue.md

Struck from the queue in the cull of 2026-09-02 because its trigger has never
been met, verbatim, so the ask survives the row:

- [ ] **Mini-personas** as per-seat judgment biases, assigned from the seed and
      recorded so the scorer can split by persona. Trigger: only if a table that
      argues from evidence still votes identically. Re-homed to changeling (S1);
      its trigger was never met on cabal.

The three DURF questions, moved out of `queue.md` the same day. They are argument
and reference, not asks a session takes; the queue keeps one row pointing here.
Verbatim:

- **`hidden catch`, camp1's term**, colliding with ordinary searching prose
  exactly as `loose flagstone` did - the model chose the words. Deliberately
  unfixed, and the argument is `docs/durf-rung.md`: scoring it as a hold moves no
  verdict, and the edit voids its own read. camp2's structural pair is CLOSED.
  **Deciding it does NOT oblige a re-run** - the 91/100 is a dated read under its
  own term set and stays quotable as that. Change the term, mark the read as
  scored under the old set, and run again only when something else needs it.
- **Movement is deliberately still unconstrained by the exit graph.** `call_move`
  accepts any room, so the party can go R1 to R4 in one call. Making it respect
  adjacency is a RULES change - it moves what is legal and therefore what the
  fallback rate counts - and it would be a second variable in the same campaign.
  Separate arm.
- **The tell question is a SEPARATE instrument and must not be folded back in.**
  Substring matching cannot see a referee that names the object of its own
  undeclared secret without naming the secret (`docs/action-channel.md`).
  Reveal-ahead is a COUNT, not a gate, and gate #1 must not be changed to catch it
  - declaring is the referee's authority, so the audit is correctly silent.
  Instrument `py -3 -m eval.durf_reveal_order <record>.json`, no GPU. There is
  still **no rubric for whether a refereed session was any GOOD**, and the
  reveal-ahead count must not be promoted into one.

## Session-0 is the play lane's first slice, 2026-09-03

The argument behind the play-lane row in `queue.md`. A scene loop is the obvious
first slice and the wrong one: it produces prose, and prose needs a rubric this
tree does not have (the same gap `docs/durf-rung.md` leaves open for a refereed
session). **A playbook draft produces a number on day one.**

- **A taken pick is an illegal move**, so the existing fallback instrument reads
  the draft unchanged - no new scorer, and the void rule applies as written.
- **The pick distribution is the read.** Whether seats collapse onto the same few
  playbooks is a diversity question with a free baseline: the operator ranked all
  22 by preference 2026-09-03, so model picks have a human ordering to correlate
  against rather than only a uniform null. Mode collapse here is the narrative
  twin of the agreeableness the economy-compliance question chases.
- **The payload is the design problem, and it is the standing-context invariant
  in miniature.** 22 full sheets in the choose-phase ask is a large payload paid
  by every seat, and the invariant says a rule reaches a seat at the phase where
  it is actionable. So: names plus a one-line hook to choose from, the full sheet
  only to the seat that took it. That is a position held for a reason, and it is
  measurable - a run that sends all 22 is the arm against it.
- **Local pack, all 22 entries; the tracked example pack is a different object.**
  `docs/content-packs.md`'s four-or-five-entries limit governs what SHIPS. A
  draft needs a real menu, and a menu of five is not a table's choice.



## 2026-09-03 - moved from queue.md

Two rows whose ASK is one sentence and whose body had grown into the argument
behind it. The queue keeps a short row pointing here; the reasoning is verbatim
below, so nothing is rewritten on the way out.

### The RP-tune bench

- [ ] **"q36 is terse and robotic" is a claim about a model, and there is no
      bench.** Candidates offered: RP-tuned Anubis-mini-8B, Rocinante-X-12B,
      Rocinante-XL-16B, Cydonia-24B against untuned gemma, qwen36-35b-a3b,
      qwen3.8-27B and its MTP build. **Read the direction note first.** It earns
      GPU on one parlor-shaped question only: whether fallback rate and deduction
      move together or apart across tunes, which is what an RP tune buys.
      Serial local lane; `--no-thinking` is a property of the rung, not the bench.
      **Entry condition: no arm in flight** - it queues behind every frozen arm on
      the merge list, all of which pair against a control that expires.
      **The gate is the source-rules MERGE, not an idle card** (2026-09-02): every
      frozen arm pairs against `cl-rounds2.json`, a control recorded on
      `qwen36-35b-a3b-iq3`, so a re-arm before those run voids them - and the merge
      re-baselines the rung anyway, so a second model's control is the only moment
      it is marginal cost rather than a new debt. **One candidate is already
      measured, and the row read as if none were:** `rocinante-x-12b-heretic-q4` is
      Rocinante-X-12B, and its cabal reading is the bench's own question answered
      apart - prose good enough to fabricate a prior conversation with no prompt
      escalation, vote discrimination -0.2% at chance (`docs/measurements.md`
      2026-08-25 and §Backend notes). One point, on the other rung and under the
      superseded vote rule, so it sharpens the prior and does not spend the bench.
      **Two corrections to the candidate list, 2026-09-02.** "Untuned gemma" is not
      on this box: `gemma`/`gemma-6` both alias an abliterated E4B, ~4B active, so
      against q36 they measure SCALE wearing a tune label. The armable comparator
      is `ablx` (`gemma-4-26B-A4B-it-abliterix-V6`, IQ4_XS), configured identically
      to q36 in `llm-serve/models.json` - same ctx, kv quant, batch, ngl, backend -
      and MoE A4B against A3B, so it swaps one variable where the dense RP tunes
      swap three. It is instruct, not a reasoning distill, so its per-game cost
      must be re-timed rather than inherited from q36's 91 s. And **each tune is
      TWO arms, not one**: gate #2 is conditional on gate #3, so a tune's evil win
      rate is unreadable without that tune's own good-side control. The 12B is the
      worked example - evil 62.5% (5/8, CI 30.6-86.3%) beside good discrimination
      -0.2%, which is the ~65% no-deception baseline hit exactly, so the run is
      consistent with the tune buying no deception at all. Its hunter, 3/6 against
      a 33.3% chance floor, is the only evil-side signal and sits inside q36's own
      33/55/56% range. **"An RP tune bought deception" is UNMEASURED, not shown.**

### Two pre-measurement positions refuted by work built the same week

- [x] **RECONCILED 2026-09-03, both instances.** (a) is dated and answered in
      place under `docs/action-channel.md`'s "Gate #1 does not survive a model DM"
      paragraph (that file carries no headings);
      (b) is dated in the table above and answered in the two paragraphs under
      it. Neither superseded reading was deleted. The ask, as written:
      **Two pre-measurement positions in `docs/` were refuted by work built the
      same week, and neither was reconciled.** One class, two instances, found
      2026-09-02 by reading them against the rungs that landed after them. Done
      when each doc states the position the measurement supports, with the
      superseded reading kept and dated rather than deleted.
      **(a) `docs/action-channel.md:82` says gate #1 "does not survive a model
      DM"**, written 2026-08-25 from a design read, with "the innkeeper looks
      nervous" as a leak carrying zero substring overlap. The DURF campaign then
      measured it: gate #1 HELD 91/100, then 99/100 under the topology edits, and
      `docs/durf-rung.md:811` decides the opposite call - a declared fact is entitled
      by definition, the audit is correctly silent, and the forward-reveal
      behaviour is a COUNT with no criterion. The innkeeper case is the one the
      count covers, not a leak: a GM that infers a nervous novice and telegraphs
      it is doing the job, and the residue is that **declaring sets its own bar**,
      which is the real open question and is not what the 08-25 paragraph says.
      **(b) `docs/open-arms.md` §While the card is busy rejects Secret Hitler as
      "the same rung as cabal ... its policy deck is more rules, not a different
      knowledge model."** `games/quorum/RULES.md:11` opens "Modelled on Secret
      Hitler" and argues at length that it IS a different knowledge model -
      entitlement cascades over an object created in play, keyed to a rotating
      office, and the proposer's discard is an entitlement that EXPIRES one step
      down a chain. Same day, hours apart: the rung's design landed 16:20, its
      referee 16:28, the row moved to `docs/` verbatim at 20:30. So the tree
      carries a live recommendation against building what it had just built.
