# Support / Resistance Bounce

> **Status: template.** Sections marked `TBD` need values from Paul before W2 starts. The W2 setup specialist (`backend/app/agents/setup_sr_bounce.py`) will parse the front-matter and the **Level quality** + **Quality bands** tables into Python constants. Anything left as `TBD` becomes a runtime "rule unspecified" gap flag in the critique.

---

```yaml
# Front-matter consumed verbatim by setup_sr_bounce.py.
setup: sr_bounce
version: 1
markets: [US, IN, DE]
```

## Definition

A long (or short) entry placed near a horizontal price level that has historically held as support (resistance), anticipating that buyers (sellers) will defend it again. Trigger is reaction off the level, not a breakout through it.

## Level identification

A level is admissible only if it scores `>= TBD` on the **Level quality** table below. Level identification logic:

1. Look back over `TBD` days of daily bars (timeframe-of-thesis or 1D, whichever is longer).
2. Cluster swing-highs (for resistance) or swing-lows (for support) within `TBD * ATR(14)` of each other into a single level.
3. The level price is the volume-weighted average of the cluster's wicks.

## Level quality

Each touch and confluence contributes points. Threshold for admissibility: `TBD` points.

| Factor | Points |
|---|---|
| Each historical touch within the last `TBD` days | TBD |
| Age of first touch (the older, the more points, capped at `TBD`) | TBD |
| Confluence with a 20 / 50 / 200 SMA within `TBD %` | TBD |
| Confluence with a prior-day or weekly extreme | TBD |
| Confluence with a round number (psychological level) | TBD |
| Confluence with VWAP at the time of entry | TBD |
| Level has been broken and reclaimed (penalty) | TBD (negative) |

Paul: fill in points and the admissibility threshold. The W2 specialist applies the table exactly.

## Entry rules

1. Price approaches the level from the favorable side (e.g. for long support: price drops to within `TBD %` of the level).
2. Reaction candle prints (Paul: pin/hammer/engulfing list goes here, or specify "any close back away from the level by >= TBD %").
3. Entry on close of the reaction candle (TBD: or on break of its high for longs).
4. Volume confirmation: reaction-candle volume >= `TBD x` average of last N bars.
5. Skip if a meaningful catalyst (earnings, FOMC, ECB, RBI policy) is scheduled in the next `TBD` hours.

## Invalidation

- Close beyond the level by more than `TBD * ATR(14)`.
- N consecutive closes against the entry direction.
- Hit of the configured stop.

## Stop placement

- Long support: `level - TBD * ATR(14)` (or below the reaction candle low — Paul picks the rule).
- Short resistance: mirror.

## Target placement

- Default first target: the next opposing admissible level (resistance for a long off support, and vice versa).
- Default second target: prior-day / week extreme on the target side.
- Minimum acceptable distance to first target: `TBD %` of entry price, otherwise the setup is downgraded one band.

## Quality bands

| Band | All of the following must hold |
|---|---|
| `strong` | Level score >= `TBD`; reaction candle volume >= `TBD x` average; no scheduled catalyst inside `TBD` hours; aligned with trend on the higher timeframe. |
| `marginal` | Level score in `[TBD, TBD)`; reaction candle volume >= `TBD x`; trend neutral or counter. |
| `weak` | Level score below `TBD`; OR no volume confirmation; OR catalyst within window; OR R/R below minimum. |

## R/R defaults

| | Long | Short |
|---|---|---|
| Min acceptable R/R | TBD | TBD |
| Preferred R/R for `strong` | TBD | TBD |

## Market-specific notes

- **US:** intraday S/R holds well during pre-market overlap with European session; less so during the post-close drift.
- **IN:** lower liquidity near close — Paul, do you avoid S/R entries after 15:00 IST?
- **DE:** XETRA's mid-day liquidity dip — any time-of-day restrictions on entries?

## What the specialist will check at runtime

The W2 `setup_sr_bounce.py` will, given a parsed thesis with `setup=sr_bounce`:

1. Reconstruct the level from yfinance bars using the **Level identification** rules.
2. Score the level against the **Level quality** table.
3. Verify the proximity of entry to the reconstructed level.
4. Pull volume context for the reaction candle.
5. Check the calendar (EDGAR / NSE / DGAP) for scheduled catalysts in the configured window.
6. Apply the **Quality bands** to assign `strong | marginal | weak`.
7. Hand the result + supporting numbers to the synthesizer; the critic re-verifies the math.

Each step that hits a `TBD` value flags the critique with `setup_rules_incomplete: sr_bounce`.
