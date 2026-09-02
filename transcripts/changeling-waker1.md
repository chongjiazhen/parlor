# Changeling - waker arm verdict

Rendered 2026-09-02T00:32:04Z from untracked
`eval/records/waker1.json` and its `.jsonl` sibling, by `py -3 -m eval.waker_verdict`.

Criterion `docs/changeling-waker-criterion.md`, pre-committed and not editable.

```text
changeling waker arm - eval/records/waker1.json
criterion: docs/changeling-waker-criterion.md (pre-committed, not editable)

instrument control - the record against what the criterion promised
   seats [6] - the six-seat waker deck
   seats        6
   seed         12000
   temperature  0.8
   rounds       2
   arm          'llm'
   blind votes  scorer 262, recomputed 262  agrees

void conditions, pre-committed
   fallback 11/3600 = 0.31%, under the 10% ceiling
   recovered 246/3600 = 6.83%
   200 played games, as promised
   5 game(s) seated no pack at dawn and are excluded; scored on 195

the bar - and the clause that can move it
   criterion bar 30.14% (its measured arm read 28.82%; the criterion names the HIGHER)
   this run's own random arm: derived 31.12%, blind accuracy 28.63% over 262 votes on 195 scored games
   agrees within 1% (0.98%), so the criterion's bar stands
   THE BAR IS 30.14% - the criterion's pre-measured derived chance

gate #3 - blind villager accuracy, the pre-committed statistic
   statistic  votes by villager seats the night told NOTHING (`none` stratum, S10's told-based rule)
   120/262 = 45.80%
   Wilson    floor 39.87% [39.87%, 51.85%]
   bootstrap floor 38.87% [38.87%, 52.70%]   (over games, so wider - votes in one game share a deal)
   the criterion requires BOTH floors to clear, stated in advance because S5 had to record which applied after the fact
      Wilson floor 39.87% clears 30.14%
      bootstrap floor 38.87% clears 30.14%
   -> gate #3 HOLDS

   power, as computed BEFORE the run, against what landed:
      predicted ~272 blind votes; landed 262
      a true 34%: Wilson floor 28.50% vs 30.14% -> does NOT clear
      a true 35%: Wilson floor 29.59% vs 30.14% -> does NOT clear
      a true 36%: Wilson floor 30.31% vs 30.14% -> clears
      a true 38%: Wilson floor 32.50% vs 30.14% -> clears
      a true 40%: Wilson floor 34.33% vs 30.14% -> clears
      The promise: "the floor clears from a true rate of 36% upward".

gate #2 - deception, conditional on #3
   pack win rate 54.36% [47.35%, 61.20%] over 195 scored games
   against THIS RUN'S own random arm, never a reference from another day
   NO VERDICT: the criterion declares no bar for #2, so it is reported as a rate with an interval and nothing more.

the waker split - an OBSERVATION, and the criterion forbids promoting it to a gate
   waker seated     125 games, 162 blind votes, 45.68% [38.20%, 53.36%]
   waker in centre   70 games, 100 blind votes, 46.00% [36.56%, 55.74%]
   Different deals, not the same ones - one run carrying its own control is weaker than same-seed pairing and the criterion says so.

free off the same records, and none of them a gate
   `false` stratum   48.25% (114 votes)
   `none` stratum   45.80% (262 votes)
   diverged        42.81% (313 votes)
   intact          47.88% (543 votes)
   None of the three may be promoted to a gate after the fact.

**A dated snapshot of one model on one deck, never a claim about models.**
```
