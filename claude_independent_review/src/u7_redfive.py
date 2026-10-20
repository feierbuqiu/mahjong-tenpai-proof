"""Sensitivity check (NOT the user's model): Tenhou's default ruleset has one red 5m
among the four 5m.  A red 5m would be a physically distinguishable symbol, so
hands that contain it could send an 8th symbol.  Hands dealt WITHOUT the red 5m
hold at most three (normal) 5m and can only send triples over the 7 normal
tiles 2m..8m.  Count distinct wait sets N' among those hands (and the classes
L' with no common 3-sub-multiset); if N' (or N' + L') > 343 the k = 3
impossibility survives even with a red five.
"""
import sys
sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
from u7_lowerbound import universe, waits, INDEX  # noqa: E402  (my own module)


def main():
    U = ["2m", "3m", "4m", "5m", "6m", "7m", "8m"]
    i5 = INDEX["5m"]
    for cap5, label in ((4, "all hands (user's model, no red tiles)"), (3, "hands without the red 5m (at most 3 normal 5m)")):
        mins = {}
        for h in universe(U):
            if h[i5] > cap5:
                continue
            w = waits(h)
            if not w:
                continue
            if w in mins:
                mins[w] = tuple(min(a, b) for a, b in zip(mins[w], h))
            else:
                mins[w] = h
        n = len(mins)
        L = sum(1 for m in mins.values() if sum(m) < 3)
        print(f"{label}: N={n}  L3={L}  N+L3={n + L}  vs 7^3=343 -> "
              f"{'k=3 impossible' if n + L > 343 else 'no contradiction from this U'}")


if __name__ == "__main__":
    main()
