# Belfry - live1 measurement rendering

Rendered 2026-08-31T02:47:27Z from untracked
`eval/records/belfry-live1.json` and its `.jsonl` sibling.

## Arm identity

100 games | `--arm llm` | 5 seats | compact script | 1 talk round | seed 6100 |
local `qwen36-35b-a3b-iq3` | `--no-thinking` | temperature 0.8

The random control in `docs/measurements.md` uses 5 seats, compact, one round and
seed 6100. This record is not execution of `docs/belfry-live1-criterion.md`: that
criterion fixed 60 games, temperature 0.0 and no `--no-thinking`. Its scorer now
refuses this record as a criterion mismatch.

## Record rendering

| measure | live1 |
|---|---|
| games | 100/100 |
| good win rate | 42/100 = 42.00% [32.80%, 51.79%] |
| mean days | 2.36 |
| good-seat vote discrimination | 16.09pp [11.44pp, 20.82pp] |
| yes on evil nominee | 591/801 = 73.78% |
| yes on good nominee | 634/1099 = 57.69% |
| day-1 voted execution accuracy | 29/60 = 48.33% [36.17%, 60.69%], chance 40.00% |
| all voted living-seat execution accuracy | 62/134 = 46.27% [38.05%, 54.70%], chance 44.50% |
| good-seat accuracy / always-no | 55.58% / 57.84% (1900 votes) |
| fallback | 82/5515 = 1.49% |
| vote fallback | 10/3260 = 0.31% |
| recovered legal answer | 708/5515 = 12.84% |
| endings | attrition 58; demon-dead 42 |

The game-bootstrap interval on vote discrimination clears zero. This is a result
of this 100-game, sampled-player arm, not a pre-committed criterion verdict. The
day-1 interval spans its chance rate. Pooled execution is descriptive only: finding
the demon ends a game and changes later execution opportunities.
