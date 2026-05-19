# Opening Range Breakout (ORB)

> **Status: template.** Sections marked `TBD` need values from Paul before W2 starts. The W2 setup specialist (`backend/app/agents/setup_orb.py`) will parse the front-matter and the **Quality bands** table into Python constants and apply them deterministically. Anything left as `TBD` becomes a runtime "rule unspecified" gap flag in the critique.

---

```yaml
# Front-matter consumed verbatim by setup_orb.py. Keep keys in this exact form.
setup: orb
version: 1
markets: [US, IN, DE]
```

## Definition

A long (or short) entry triggered when price breaks above (below) the high (low) of a fixed "opening range" formed in the first N minutes of the regular session, on confirming volume.

## Opening range window

| Market | Session open (local) | Range window | Earliest entry | Latest entry |
|---|---|---|---|---|
| US (NYSE/NASDAQ) | 09:30 ET | TBD (5/15/30 min) | TBD | TBD |
| IN (NSE/BSE)     | 09:15 IST | TBD | TBD | TBD |
| DE (XETRA)       | 09:00 CET | TBD | TBD | TBD |

Paul: confirm the range window per market and the cutoff after which a fresh ORB signal no longer counts.

## Entry rules

1. Range is established once price has closed the configured window.
2. Long entry: price prints above range high. Short entry: below range low.
3. Entry on close of the breakout bar (TBD: or on first tick above the level — Paul picks).
4. Volume confirmation: breakout-bar volume must be at least `TBD x` the average volume of the last N bars of the same timeframe (Paul: pick N and multiple).
5. Optional gap rule: if the regular-session open gapped more than `TBD %` from the previous close, ORB is skipped (gap-and-go is a different setup).

## Invalidation

- Re-entry inside the opening range within `TBD` bars of the breakout.
- Close back through the level on increased volume.
- Hit of the configured stop.

## Stop placement

- Long: `min(opposite side of opening range, entry - TBD * ATR(14))`.
- Short: mirror.

Paul: confirm whether the stop hugs the range opposite or uses the wider of (range opposite, ATR multiple).

## Target placement

- Default first target: `entry + TBD * (entry - stop)` (i.e. R-multiple).
- Default second target: prior-day high / low or nearest swing high / low — whichever is further.
- If the path to the first target has a clear intervening resistance within `TBD %` of entry, the setup quality drops one band.

## Quality bands

The specialist returns one of `strong | marginal | weak`. Bands are evaluated in order; first match wins.

| Band | All of the following must hold |
|---|---|
| `strong` | Volume >= `TBD x` average; breakout candle range <= `TBD x` ATR(14); no intervening resistance to first target; sector ETF green on the day. |
| `marginal` | Volume >= `TBD x` average; breakout candle within `TBD x` ATR; sector neutral or mixed. |
| `weak` | Any of: volume below threshold; breakout candle wider than `TBD x` ATR; intervening resistance within `TBD %`; sector ETF red. |

Paul: fill in each `TBD` with a single number you can defend.

## R/R defaults

| | Long | Short |
|---|---|---|
| Min acceptable R/R for any band | TBD | TBD |
| Preferred R/R for `strong` | TBD | TBD |

The structure critic (`structure.py`) refuses a setup if its R/R falls below the minimum, regardless of band.

## Market-specific notes

Anything that diverges from the US defaults per market goes here. Examples to confirm:

- **IN:** lower average volume on small-caps means the volume multiplier needs to be reset.
- **DE:** XETRA's auction-driven open may distort the first 5 minutes — Paul, is your range window 15+ to avoid the auction?

## What the specialist will check at runtime

The W2 `setup_orb.py` will, given a parsed thesis with `setup=orb`:

1. Verify the breakout actually happened in the configured window for the named exchange.
2. Pull 20-day average volume from yfinance and compute the breakout-bar ratio.
3. Compute ATR(14) and the candle-range ratio.
4. Walk the resistance map (from the structure critic) for intervening levels.
5. Pull the sector ETF (US: XLK/XLF/etc.; IN: sectoral indices; DE: DAX sub-sectors) and check end-of-day color.
6. Apply the **Quality bands** table to assign `strong | marginal | weak`.
7. Hand the result + supporting numbers to the synthesizer; the critic re-verifies the math.

Each step that hits a `TBD` value flags the critique with `setup_rules_incomplete: orb`.
