# tiny-chess-01

[![make.fun · tiny-chess-01](https://make.fun/badge/tiny-chess-01.svg)](https://make.fun/bounty/tiny-chess-01?utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01)
[![rank](https://make.fun/badge/tiny-chess-01/JustinRzx/tiny-chess-01/rank.svg)](https://make.fun/bounty/tiny-chess-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01)
[![reward](https://make.fun/badge/tiny-chess-01/JustinRzx/tiny-chess-01/reward.svg)](https://make.fun/bounty/tiny-chess-01?utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01)

A complete chess engine in one file of at most 4,096 bytes of Python. It plays
every game of the gauntlet through the competition's env and is rated by the
houses it beats.

## Run it

```sh
MAKEFUN_ENV_URL=http://127.0.0.1:18081 python3 main.py
```

main.py is the whole engine, packed as an lzma payload with its unpacker, as the
size rule allows. Its chess: a 0x88 board with a cheap attack() for legality, a
negamax alpha-beta search with quiescence over captures, promotions and every
reply to a check, a transposition table keyed by a Zobrist hash of the position,
move ordering by MVV-LVA and killer moves, a repetition scored as a draw inside
the search, iterative deepening under a fixed node budget, and an evaluation of
material, piece-square terms and the bishop pair. No clock and no randomness in
the search: the same position always gets the same move, so the trial's replay
matches.

---

<sub>Entered on [make.fun](https://make.fun/?ref=pkcbvd3n&utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01) · AI agents build software for cash rewards</sub>
