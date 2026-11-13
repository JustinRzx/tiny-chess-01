import sys

def pi(n):
    if n < 2:
        return 0
    size = (n + 1) // 2
    sieve = bytearray(b"\x01") * size
    sieve[0] = 0
    for i in range(3, int(n ** 0.5) + 1, 2):
        if sieve[i // 2]:
            start = i * i // 2
            sieve[start::i] = b"\x00" * ((size - 1 - start) // i + 1)
    return 1 + sieve.count(1)

def main():
    nums = sys.stdin.read().split()
    out = [str(pi(int(x))) for x in nums]
    sys.stdout.write("\n".join(out) + ("\n" if out else ""))

if __name__ == "__main__":
    main()
