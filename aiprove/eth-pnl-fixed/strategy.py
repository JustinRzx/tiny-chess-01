#!/usr/bin/env python3
"""eth-pnl-fixed — NovaKernel strategy.

Slow EMA trend with a dead band, sized at one unit, designed to survive
costs instead of chasing them:

  - EMA(20) vs EMA(80) on 1-minute closes.
  - Go long when (EMA20 - EMA80) / price > +0.0015, short when < -0.0015,
    otherwise keep the previous position (the band is hysteresis: the
    position only changes on a clear cross, so chop cannot churn fees).
  - Position is always -1, 0 or +1 unit. No leverage, no scaling.

Why this shape: on the frozen day, fast systems die on costs (an EMA 5/20
cross flips 119 times and loses ~$381 per unit after the cost model
below). The slow banded cross flips 6 times. Split-half check: first
half (range chop) -8.86, second half (clean downtrend) +36.83 — it is
built to lose small in chop and get paid in trends, which is the honest
trade for a held-out tail.

Self-backtest cost model (stated openly; the sandbox applies its own):
taker fee 0.05% + slippage 0.02% of price per unit of position change,
PnL marked on close-to-close moves per 1 ETH unit.

Result on bars.csv: net +29.37 per unit, 6 position changes,
max drawdown -69.18. Buy and hold over the same day: -68.09.

Usage: python3 strategy.py [bars.csv]  -> prints positions + summary.
positions(bars) returns the per-bar position list for replay.
"""
import csv, sys

FAST, SLOW, BAND = 20, 80, 0.0015

def ema(xs, n):
    k = 2 / (n + 1)
    out = [xs[0]]
    for x in xs[1:]:
        out.append(out[-1] + k * (x - out[-1]))
    return out

def positions(bars):
    closes = [b["close"] for b in bars]
    ef, es = ema(closes, FAST), ema(closes, SLOW)
    pos, cur = [], 0
    for t, price in enumerate(closes):
        d = (ef[t] - es[t]) / price
        if d > BAND:
            cur = 1
        elif d < -BAND:
            cur = -1
        pos.append(cur)
    return pos

def load(path):
    with open(path) as f:
        return [{"close": float(r["close"])} for r in csv.DictReader(f)]

def main():
    bars = load(sys.argv[1] if len(sys.argv) > 1 else "bars.csv")
    closes = [b["close"] for b in bars]
    pos = positions(bars)
    fee, slip = 0.0005, 0.0002
    pnl = cost = 0.0
    prev = 0
    flips = 0
    equity = []
    for t in range(len(closes) - 1):
        p = pos[t]
        if p != prev:
            cost += abs(p - prev) * closes[t] * (fee + slip)
            flips += 1
        pnl += p * (closes[t + 1] - closes[t])
        prev = p
        equity.append(pnl - cost)
    peak, mdd = float("-inf"), 0.0
    for e in equity:
        peak = max(peak, e)
        mdd = min(mdd, e - peak)
    print(f"net PnL per unit: {pnl - cost:.2f} (gross {pnl:.2f}, costs {cost:.2f})")
    print(f"position changes: {flips}, max drawdown: {mdd:.2f}")
    print("positions:", ",".join(str(p) for p in pos))

if __name__ == "__main__":
    main()
