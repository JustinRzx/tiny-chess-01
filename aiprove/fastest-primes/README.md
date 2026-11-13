# fastest-primes — NovaKernel entry

Run command:

```bash
python3 primes.py
```

Reads integer N on stdin (one per line if several are given) and prints
pi(N), the count of primes <= N, for each. N up to 5,000,000.

Implementation: odd-only bytearray sieve of Eratosthenes with slice
assignment. Verified against the public samples (10→4, 100→25, 1000→168,
100000→9592, 1000000→78498) and pi(5,000,000) = 348,513 in ~0.04 s.
