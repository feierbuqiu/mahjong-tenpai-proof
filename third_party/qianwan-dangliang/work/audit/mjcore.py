# -*- coding: utf-8 -*-
"""skeptic-audit: independent tile/win/wait engine written from scratch.

Conventions (index 0..33):
  0..8   = 1m..9m
  9..17  = 1p..9p
  18..26 = 1s..9s
  27..33 = 1z..7z (East,South,West,North,Haku,Hatsu,Chun)

Win types implemented independently:
  std      : 4 melds (triplet or, in suits only, run) + 1 pair
  chiitoi  : STRICT tenhou rule = 7 *distinct* pairs (four identical tiles are NOT two pairs)
  kokushi  : 13 orphan kinds, exactly one of them doubled
Multiplicity cap: no tile may appear more than 4 times in a hand.
"""
from functools import lru_cache
from itertools import combinations_with_replacement

N = 34
MW = "mps"
HON = ["E", "S", "W", "N", "Haku", "Hatsu", "Chun"]
ORPHANS = (0, 8, 9, 17, 18, 26, 27, 28, 29, 30, 31, 32, 33)


def nm(t):
    return ("%d%s" % (t % 9 + 1, MW[t // 9])) if t < 27 else HON[t - 27]


def nm_idx(x):
    if isinstance(x, int):
        return x
    if x in HON:
        return 27 + HON.index(x)
    return MW.index(x[-1]) * 9 + int(x[0]) - 1


def hand_str(c):
    return "".join(nm(t) * c[t] for t in range(N)) or "-"


def empty():
    return (0,) * N


def add(c, t, n=1):
    l = list(c)
    l[t] += n
    return tuple(l)


def sub(c, t, n=1):
    l = list(c)
    l[t] -= n
    return tuple(l)


def from_str(s):
    """parse '123m456p77z' (digit runs terminated by a suit/honor letter)"""
    c = [0] * N
    buf = ""
    i = 0
    while i < len(s):
        ch = s[i]
        if ch.isdigit():
            buf += ch
            i += 1
            continue
        if ch in MW:
            for d in buf:
                c[MW.index(ch) * 9 + int(d) - 1] += 1
            buf = ""
            i += 1
            continue
        if ch == "z":
            for d in buf:
                c[27 + int(d) - 1] += 1
            buf = ""
            i += 1
            continue
        # honor letter word
        matched = None
        for h in HON:
            if s.startswith(h, i):
                matched = h
                break
        if matched:
            assert not buf, "digits before honor name: %r" % s
            c[27 + HON.index(matched)] += 1
            i += len(matched)
            continue
        raise ValueError("bad char %r in %r" % (ch, s))
    assert not buf, "trailing digits"
    return tuple(c)


# ---------------------------------------------------------------- win checks
@lru_cache(maxsize=1<<17)
def melds_ok(c):
    """True iff c (total divisible by 3) decomposes into triplets and suit runs."""
    i = -1
    for k in range(N):
        if c[k]:
            i = k
            break
    if i < 0:
        return True
    if c[i] >= 3:
        l = list(c)
        l[i] -= 3
        if melds_ok(tuple(l)):
            return True
    if i < 27 and (i % 9) <= 6 and c[i + 1] > 0 and c[i + 2] > 0:
        l = list(c)
        l[i] -= 1
        l[i + 1] -= 1
        l[i + 2] -= 1
        if melds_ok(tuple(l)):
            return True
    return False


@lru_cache(maxsize=1<<17)
def win_std(c):
    if sum(c) != 14:
        return False
    for i in range(N):
        if c[i] >= 2:
            l = list(c)
            l[i] -= 2
            if melds_ok(tuple(l)):
                return True
    return False


@lru_cache(maxsize=1<<16)
def win_chiitoi(c):
    if sum(c) != 14:
        return False
    return all(x in (0, 2) for x in c) and sum(1 for x in c if x == 2) == 7


@lru_cache(maxsize=1<<16)
def win_kokushi(c):
    if sum(c) != 14:
        return False
    if any(c[t] for t in range(N) if t not in ORPHANS):
        return False
    if any(c[t] == 0 for t in ORPHANS):
        return False
    return sum(1 for t in ORPHANS if c[t] == 2) == 1


@lru_cache(maxsize=1<<17)
def is_win(c):
    if sum(c) != 14 or max(c) > 4:
        return False
    return win_std(c) or win_chiitoi(c) or win_kokushi(c)


@lru_cache(maxsize=1<<16)
def waits(c13):
    """W(H): all tiles t with H+t a winning hand (4-copy cap respected)."""
    if sum(c13) != 13:
        return frozenset()
    out = []
    for t in range(N):
        if c13[t] >= 4:
            continue
        if is_win(add(c13, t)):
            out.append(t)
    return frozenset(out)


@lru_cache(maxsize=1<<16)
def waits_std(c13):
    out = []
    for t in range(N):
        if c13[t] >= 4:
            continue
        if win_std(add(c13, t)):
            out.append(t)
    return frozenset(out)


# ---------------------------------------------------------------- enumeration
def multisets(k, kinds=None, cap=4):
    """all count-vectors of size k over 'kinds' with each count <= cap"""
    if kinds is None:
        kinds = tuple(range(N))
    kinds = tuple(kinds)

    def rec(i, left, cur):
        if i == len(kinds):
            if left == 0:
                yield tuple(cur)
            return
        # prune: remaining kinds
        rem_kinds = len(kinds) - i - 1
        lo = max(0, left - cap * rem_kinds)
        hi = min(cap, left)
        for v in range(lo, hi + 1):
            cur[kinds[i]] = v
            yield from rec(i + 1, left - v, cur)
            cur[kinds[i]] = 0

    yield from rec(0, k, [0] * N)


def submultisets(c, k):
    """all sub-multisets of size k of c, as count vectors (k<=4 typical)"""
    tiles = [t for t in range(N) if c[t]]
    out = set()
    for combo in combinations_with_replacement(tiles, k):
        ok = True
        need = {}
        for t in combo:
            need[t] = need.get(t, 0) + 1
        for t, v in need.items():
            if c[t] < v:
                ok = False
                break
        if ok:
            out.add(combo)
    return out


def contains_any(hand_counts, codes):
    """codes: iterable of sorted tuples (multisets)"""
    for c in codes:
        need = {}
        for t in c:
            need[t] = need.get(t, 0) + 1
        ok = True
        for t, v in need.items():
            if hand_counts[t] < v:
                ok = False
                break
        if ok:
            return c
    return None
