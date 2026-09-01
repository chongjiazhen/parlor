# Belfry - belfry-live2 measurement rendering

Rendered 2026-09-01T17:58:54Z from untracked
`eval/records/belfry-live2.json` and its `.jsonl` sibling.

## Arm identity

60 games | `--arm llm` | 5 seats | compact script | 1 talk round(s) | seed 6100 | local `qwen36-35b-a3b-iq3` | `--no-thinking` | temperature 0.0

Criterion `docs/belfry-live2-criterion.md`, pre-committed and not editable.

## Record rendering

| measure | belfry-live2 |
|---|---|
| games | 60/60 |
| yes on evil nominee | 351/471 = 74.52% |
| yes on good nominee | 369/681 = 54.19% |
| good-seat vote discrimination | 20.34% [13.77%, 27.01%] (bootstrap over 60 games) |
| day-1 voted execution accuracy | 16/38 = 42.11% |
| fallback | 43/3353 = 1.28% |
| vote fallback | 0/1972 = 0.00% |
| recovered legal answer | 7.25% |
| good win rate | 48.33% |

## What it reads

Clause A: INFORMS. The interval is a per-game bootstrap over 60 games - votes inside one game are correlated by the board that produced them, so the game is the resampling unit and never the vote. The random control read 2.41% [-1.49%, 6.15%] over 200 games and does not clear this bar, which is what earns the figure the right to be read.

**A dated snapshot of one model on one script at one talk round, never a claim about models.** No deduction or deception figure is inferred from the win rate: a win here is a four-day chain and the record does not attribute it to any one decision. Recompute every figure above with `py -3 -m eval.belfry_live1_verdict --criterion live2`.
