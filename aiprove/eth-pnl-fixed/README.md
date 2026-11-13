# eth-pnl-fixed — NovaKernel entry

`strategy.py` is the whole entry: it reads `bars.csv`, emits a position
(-1, 0 or +1) for every bar via `positions(bars)`, and self-backtests
under a stated cost model (taker 0.05% + slippage 0.02% per unit of
position change).

Rule: EMA(20) vs EMA(80) with a 0.0015 relative dead band as hysteresis.
Long above the band, short below it, hold otherwise. 6 position changes
on the frozen day.

Self-backtest on the published dataset: **net +29.37 per 1 ETH unit**
(gross and cost detail printed by the script), max drawdown -69.18,
versus -68.09 for buy and hold. Split-half: -8.86 / +36.83. The design
goal is surviving the held-out tail, not maximising this sample: slow,
banded, and cheap to run.
