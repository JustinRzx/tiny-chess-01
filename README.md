# tiny-chess-01

A chess engine in one file of at most 4,096 bytes of Python (main.py), for the
make.fun tiny-chess-01 competition (agent/v1).

main.py is the whole engine, packed as an lzma payload with its unpacker, as the
size rule allows. Its chess: a 0x88 board with a cheap attack() for legality, a
negamax alpha-beta search with quiescence over captures, promotions and every
reply to a check, a transposition table keyed by a Zobrist hash of the position,
move ordering by MVV-LVA and killer moves, repetition scored as a draw inside
the search, iterative deepening under a fixed node budget, and an evaluation of
material, piece-square terms and the bishop pair. No clock and no seeded
randomness in the search: the same position always gets the same move, so the
trial's replay matches.

Played through the env at MAKEFUN_ENV_URL: POST /game {}, POST /move
{game, move} until the status is "done".
