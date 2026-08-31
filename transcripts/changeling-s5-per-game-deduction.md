# Changeling - S5 per-game deduction rendering

Rendered 2026-08-31T12:18:54.3264788Z from untracked
`eval/records/s2.json` and its `.jsonl` sibling by `py -3 -m eval.deduction`.

## Record integrity

- completed games: 200
- fallback: 0.40%, below 10% void bar
- winnable games: 195
- control: `py -3 -m unittest eval.test_deduction -v` replays each recorded
  winner from its votes, including tie-accuses-all

## Per-game deduction

```text
per-game deduction over 195 winnable games (5 excluded: no wolf at dawn, or no votes)

  votes vs this game's own chance baseline
    above      89  (45.6%)
    at         29  (14.9%)
    below      77  (39.5%)

  mean per-game lift  +0.169 [+0.085, +0.255]
    0.000 is a table voting at random; 1.000 is every villager on a wolf

  decisiveness - fewest vote changes that flip the winner
    1 vote     88  (45.1%)
    2 votes    99  (50.8%)
    3+          8  (4.1%)

  village wins decided by ONE vote  35/79 (44.3%) [33.9%, 55.3%]
    the measurable half of "it feels random": a win this thin was
    available to a table that had deduced nothing
```
