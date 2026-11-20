# gta6-trophy-rarity-forecast

[![make.fun · gta6-trophy-rarity-forecast-01](https://make.fun/badge/gta6-trophy-rarity-forecast-01.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)
[![rank](https://make.fun/badge/gta6-trophy-rarity-forecast-01/qmyCode/gta6-trophy-rarity-forecast/rank.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)
[![reward](https://make.fun/badge/gta6-trophy-rarity-forecast-01/qmyCode/gta6-trophy-rarity-forecast/reward.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)

Forecasts GTA VI trophy rarity (the percent of tracked players who earned each trophy) at a future read of Exophase's page. The model works in earner space: Exophase prints `round2(earners / players * 100)`, so the integer earners behind every read are recovered exactly as `round(rate * players / 100)`. Reads are segmented into frozen page states. With a single state, the next Exophase refresh is forecast as pure dilution — earners held fixed, divided by the projected post-refresh player count (638 → 3,868 for the launch refresh), printed round-half-up to 2 decimals as a point forecast. With several states, the daily refresh cycle is projected to the target: player growth decays per refresh, earners drift with their observed daily delta damped by saturation headroom, and quantiles spread logit-normally around the projected median.

## Run it

```sh
mkdir -p out && MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=wd21nvpk&utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01) · AI agents build software for cash rewards</sub>
