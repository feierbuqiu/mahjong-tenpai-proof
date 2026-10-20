"""Third, fully separate implementation (pure Python, no shared code with the C tools)
of the k = 3 impossibility certificate.

Claim: among 13-tile hands that use only the seven tiles 2m..8m (each at most 4
copies), the tenpai hands realise more than 7**3 = 343 distinct wait sets.
Every such hand can only show ordered triples drawn from {2m..8m}^3 (343 of
them), and hands with different wait sets must show different triples, so no
k = 3 protocol exists (pigeonhole).  Same argument gives k = 1, 2 impossible.

Rules follow 呆饼问题（二） section 2: standard form (4 melds + pair, chi only
inside a number suit), seven pairs = 7 DISTINCT pairs, kokushi, and the waited
tile must have fewer than 4 copies in the hand.
Output: out/u7_certificate.txt with one witness hand per wait set.
"""
import itertools
import sys
from functools import lru_cache

SUITS = "mps"
TILES = [f"{r}{s}" for s in SUITS for r in range(1, 10)] + ["E", "S", "W", "N", "P", "F", "C"]
ORPHANS = {"1m", "9m", "1p", "9p", "1s", "9s", "E", "S", "W", "N", "P", "F", "C"}
INDEX = {t: i for i, t in enumerate(TILES)}


def is_number(i):
    return i < 27


@lru_cache(maxsize=None)
def melds_only(counts):
    """counts: tuple of 34 ints. True if all tiles split into pons / chis."""
    try:
        i = next(k for k, c in enumerate(counts) if c)
    except StopIteration:
        return True
    c = list(counts)
    if c[i] >= 3:
        c[i] -= 3
        if melds_only(tuple(c)):
            return True
        c[i] += 3
    if is_number(i) and i % 9 <= 6 and c[i + 1] and c[i + 2]:
        c[i] -= 1
        c[i + 1] -= 1
        c[i + 2] -= 1
        if melds_only(tuple(c)):
            return True
    return False


def complete14(counts):
    if sum(counts) != 14 or max(counts) > 4:
        return False
    for j, cj in enumerate(counts):
        if cj >= 2:
            c = list(counts)
            c[j] -= 2
            if melds_only(tuple(c)):
                return True
    if sum(1 for x in counts if x == 2) == 7:
        return True
    names = {TILES[i] for i, x in enumerate(counts) if x}
    if names == ORPHANS:
        return True
    return False


def waits(counts):
    out = []
    for t in range(34):
        if counts[t] >= 4:
            continue
        c = list(counts)
        c[t] += 1
        if complete14(tuple(c)):
            out.append(TILES[t])
    return tuple(out)


def hand_str(counts):
    return "".join(TILES[i] * x for i, x in enumerate(counts) if x)


def universe(tile_names):
    idx = [INDEX[t] for t in tile_names]
    for combo in itertools.product(range(5), repeat=len(idx)):
        if sum(combo) != 13:
            continue
        c = [0] * 34
        for i, x in zip(idx, combo):
            c[i] = x
        yield tuple(c)


def main(out_path):
    U = ["2m", "3m", "4m", "5m", "6m", "7m", "8m"]
    classes = {}
    nh = nt = 0
    for h in universe(U):
        nh += 1
        w = waits(h)
        if w:
            nt += 1
            classes.setdefault(w, h)
    n = len(classes)
    print(f"U = {{{', '.join(U)}}}: hands={nh} tenpai={nt} distinct wait sets N={n} ; |U|^3={len(U) ** 3}")
    print("k=3 impossible by pigeonhole" if n > len(U) ** 3 else "no contradiction")
    # whole suit for k = 1, 2
    full = [f"{r}m" for r in range(1, 10)]
    cls_full = set()
    nt_full = 0
    for h in universe(full):
        w = waits(h)
        if w:
            nt_full += 1
            cls_full.add(w)
    print(f"whole m suit: tenpai={nt_full} distinct wait sets={len(cls_full)} ; 9^1=9, 9^2=81")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# k=3 lower-bound certificate: {n} distinct wait sets among 13-tile hands within 2m..8m (> 343)\n")
        f.write("# wait_set <TAB> witness_hand\n")
        for w in sorted(classes, key=lambda w: (len(w), [INDEX[t] for t in w])):
            f.write(",".join(w) + "\t" + hand_str(classes[w]) + "\n")
    print(f"certificate written to {out_path}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "u7_certificate.txt")
