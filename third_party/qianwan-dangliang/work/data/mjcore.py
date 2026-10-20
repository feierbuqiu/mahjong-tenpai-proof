# -*- coding: utf-8 -*-
"""mjcore.py -- MJ2 core library (owner: enum-core, write scope work/data/).

Tile model
----------
34 tile types:  0-8 = 1m..9m, 9-17 = 1p..9p, 18-26 = 1s..9s, 27-33 = 1z..7z (E,S,W,N,Haku,Hatsu,Chun).
A hand is a multiset: a 34-tuple of counts, each 0..4.
Categories: 0=m, 1=p, 2=s, 3=z.  Category vectors vs[c] are 9-tuples (7 for honors).

Contents
--------
* win recognition: standard (4 melds + pair), chiitoi (7 pairs), kokushi
* W(H) = W_std(H) | W_chiitoi(H) | W_kokushi(H)   (34-bit bitmask)
* active/inert decomposition H = A + F (remainder theorem)
* single-category primitives: melds_only, melds_pair, V(X), Wp(X), odd(X)
* code machinery: M_k(H), common-code criterion, transversal helpers

All wait sets are 34-bit bitmasks (bit t set <=> tile t in W).

Closed forms (verified in census_single.py / STATS_single.md)
-------------------------------------------------------------
melds_only(X): X splits into melds (runs/triplets), no pair.
melds_pair(X): X splits into melds + exactly one pair.
V(X)  = {t : melds_only(X + t)}          (meaningful when |X| % 3 == 2)
Wp(X) = {t : melds_pair(X + t)}          (meaningful when |X| % 3 == 1)
odd(X) = number of tile types with odd count in X.

Type I  (one active category c, |A| % 3 == 1):  W_std = Wp(A)
Type II (two active categories c1,c2, both |X| % 3 == 2):
        W_std = (melds_pair(X2) ? V(X1) : {}) | (melds_pair(X1) ? V(X2) : {})
"""

from functools import lru_cache
import itertools

CAT_BASE = (0, 9, 18, 27)
CAT_LEN = (9, 9, 9, 7)
CAT_NAME = ("m", "p", "s", "z")
N_TILES = 34
HAND_SIZE = 13
WIN_SIZE = 14

SUIT_NAMES = "mps"
HONOR_NAMES = ("E", "S", "W", "N", "Haku", "Hatsu", "Chun")

TERMINAL_HONOR = (0, 8, 9, 17, 18, 26, 27, 28, 29, 30, 31, 32, 33)
KOKUSHI_MASK = 0
for _t in TERMINAL_HONOR:
    KOKUSHI_MASK |= 1 << _t
ALL_MASK = (1 << N_TILES) - 1


# ---------------------------------------------------------------- naming
def tile_name(t):
    if t < 27:
        return "%d%s" % (t % 9 + 1, SUIT_NAMES[t // 9])
    return HONOR_NAMES[t - 27]


def tiles_of(counts):
    out = []
    for i, c in enumerate(counts):
        out.extend([i] * c)
    return out


def counts_of(tiles):
    c = [0] * N_TILES
    for t in tiles:
        c[t] += 1
    return tuple(c)


def mask_names(mask):
    return [tile_name(t) for t in range(N_TILES) if mask >> t & 1]


def cat_of(t):
    return t // 9 if t < 27 else 3


def vec_of(counts, c):
    b = CAT_BASE[c]
    return counts[b:b + CAT_LEN[c]]


def vecs_of(counts):
    return (counts[0:9], counts[9:18], counts[18:27], counts[27:34])


def counts_from_vecs(vs):
    out = []
    for c in range(4):
        out.extend(vs[c])
    return tuple(out)


def pack(counts):
    x = 0
    for i, c in enumerate(counts):
        x |= c << (3 * i)
    return x


def unpack(x):
    return tuple((x >> (3 * i)) & 7 for i in range(N_TILES))


def vs_pack(vs):
    return (pack(counts_from_vecs(vs)),)


# ---------------------------------------------------------------- melds
@lru_cache(maxsize=None)
def melds_ok9(v):
    """True iff a 9-count suit vector is a disjoint union of runs/triplets."""
    i = 0
    while i < 9 and v[i] == 0:
        i += 1
    if i == 9:
        return True
    if v[i] >= 3:
        w = list(v)
        w[i] -= 3
        if melds_ok9(tuple(w)):
            return True
    if i <= 6 and v[i + 1] and v[i + 2]:
        w = list(v)
        w[i] -= 1
        w[i + 1] -= 1
        w[i + 2] -= 1
        if melds_ok9(tuple(w)):
            return True
    return False


@lru_cache(maxsize=None)
def melds_ok(c, v):
    """True iff category-c count vector v is a disjoint union of melds."""
    if c < 3:
        return melds_ok9(v)
    for x in v:
        if x % 3:
            return False
    return True


@lru_cache(maxsize=None)
def _melds_pair(c, v):
    n = 0
    for x in v:
        n += x
    if n % 3 != 2:
        return False
    for p in range(CAT_LEN[c]):
        if v[p] >= 2:
            w = list(v)
            w[p] -= 2
            if melds_ok(c, tuple(w)):
                return True
    return False


def melds_pair(c, v):
    return _melds_pair(c, tuple(v))


@lru_cache(maxsize=None)
def _V(c, v):
    """V(X) = {t in category c : melds_only(X + t)} ; needs |X| % 3 == 2."""
    n = 0
    for x in v:
        n += x
    if n % 3 != 2:
        return 0
    base = CAT_BASE[c]
    m = 0
    for t in range(CAT_LEN[c]):
        if v[t] < 4:
            w = list(v)
            w[t] += 1
            if melds_ok(c, tuple(w)):
                m |= 1 << (base + t)
    return m


def V(c, v):
    return _V(c, tuple(v))


@lru_cache(maxsize=None)
def _Wp(c, v):
    """Wp(X) = {t in category c : melds_pair(X + t)} ; needs |X| % 3 == 1.

    Definitional: t qualifies iff X + t can be split into melds + exactly one pair.
    The pair may be the added tile itself (X[t] == 1), so the pair choice is made
    on the *augmented* vector.
    """
    n = 0
    for x in v:
        n += x
    if n % 3 != 1:
        return 0
    base = CAT_BASE[c]
    ln = CAT_LEN[c]
    m = 0
    for t in range(ln):
        if v[t] >= 4:
            continue                      # 4-copy cap on X + t
        w = list(v)
        w[t] += 1
        for p in range(ln):
            if w[p] >= 2:
                w[p] -= 2
                ok = melds_ok(c, tuple(w))
                w[p] += 2
                if ok:
                    m |= 1 << (base + t)
                    break
    return m


def Wp(c, v):
    return _Wp(c, tuple(v))


@lru_cache(maxsize=None)
def _pd(c, v):
    return _melds_pair(c, tuple(v))


def pd(c, v):
    return _pd(c, tuple(v))


def odd_count(v):
    """number of tile types with odd count."""
    n = 0
    for x in v:
        n += x & 1
    return n


def odd_mask(c, v):
    base = CAT_BASE[c]
    m = 0
    for t, x in enumerate(v):
        if x & 1:
            m |= 1 << (base + t)
    return m


# ---------------------------------------------------------------- wins
def is_win_std(counts):
    """14 tiles: standard 4 melds + 1 pair."""
    total = 0
    for x in counts:
        total += x
    if total != WIN_SIZE:
        return False
    for pc in range(4):
        if _melds_pair(pc, vec_of(counts, pc)):
            ok = True
            for c in range(4):
                if c == pc:
                    continue
                v = vec_of(counts, c)
                n = 0
                for x in v:
                    n += x
                if n % 3 or not melds_ok(c, v):
                    ok = False
                    break
            if ok:
                return True
    return False


def is_win_chiitoi(counts):
    k = 0
    for x in counts:
        if x == 2:
            k += 1
        elif x != 0:
            return False
    return k == 7


def is_win_kokushi(counts):
    total = 0
    present = 0
    for i, x in enumerate(counts):
        total += x
        if x:
            present |= 1 << i
    return total == WIN_SIZE and present == KOKUSHI_MASK


def is_win(counts):
    return is_win_std(counts) or is_win_chiitoi(counts) or is_win_kokushi(counts)


# ---------------------------------------------------------------- waits
def waits_std(counts):
    return waits_std_vecs(vecs_of(counts))


def waits_std_vecs(vs):
    rem = []
    for c in range(4):
        n = 0
        for x in vs[c]:
            n += x
        if n % 3:
            rem.append((c, n))
    nr = len(rem)
    if nr == 1:
        c, n = rem[0]
        if n % 3 != 1:
            return 0
        for d in range(4):
            if d != c and not melds_ok(d, vs[d]):
                return 0
        return _Wp(c, vs[c])
    if nr == 2:
        (c1, n1), (c2, n2) = rem
        if n1 % 3 != 2 or n2 % 3 != 2:
            return 0
        for d in range(4):
            if d != c1 and d != c2 and not melds_ok(d, vs[d]):
                return 0
        res = 0
        if _pd(c2, vs[c2]):
            res |= _V(c1, vs[c1])
        if _pd(c1, vs[c1]):
            res |= _V(c2, vs[c2])
        return res
    return 0


def waits_chiitoi(counts):
    """Chiitoi tenpai: H is 6 distinct pairs + 1 single tile z.

    H + z is then a 7-pairs win (7 DISTINCT types x 2).  Note that a hand with a
    3-count (or a 4-count) is NOT chiitoi tenpai: adding a tile to a 3-count would
    give a 4-count, and "7 pairs" here means 7 distinct types with count exactly 2
    (the recon enumeration C(34,7) confirms this reading).
    """
    z = -1
    npair = 0
    for i, x in enumerate(counts):
        if x == 0:
            continue
        if x == 2:
            npair += 1
        elif x == 1:
            if z >= 0:
                return 0
            z = i
        else:
            return 0
    if z >= 0 and npair == 6:
        return 1 << z
    return 0


def waits_chiitoi_vecs(vs):
    z = -1
    npair = 0
    for c in range(4):
        base = CAT_BASE[c]
        for t, x in enumerate(vs[c]):
            if x == 0:
                continue
            if x == 2:
                npair += 1
            elif x == 1:
                if z >= 0:
                    return 0
                z = base + t
            else:
                return 0
    if z >= 0 and npair == 6:
        return 1 << z
    return 0


def waits_kokushi(counts):
    present = 0
    for i, x in enumerate(counts):
        if x:
            present |= 1 << i
    if present & ~KOKUSHI_MASK:
        return 0
    k = 0
    p = present
    while p:
        k += 1
        p &= p - 1
    if k == 13:
        return KOKUSHI_MASK
    if k == 12:
        return KOKUSHI_MASK ^ present
    return 0


def waits_vecs(vs):
    """W(H) for H given as a 4-tuple of category count vectors."""
    w = waits_std_vecs(vs)
    w |= waits_chiitoi_vecs(vs)
    present = 0
    for c in range(4):
        base = CAT_BASE[c]
        for t, x in enumerate(vs[c]):
            if x:
                present |= 1 << (base + t)
    if not (present & ~KOKUSHI_MASK):
        k = 0
        p = present
        while p:
            k += 1
            p &= p - 1
        if k == 13:
            w |= KOKUSHI_MASK
        elif k == 12:
            w |= KOKUSHI_MASK ^ present
    return w


def waits(counts):
    return waits_vecs(vecs_of(counts))


# ---------------------------------------------------------------- decomposition
def active_cats(counts):
    return [c for c in range(4) if sum(vec_of(counts, c)) % 3]


def decompose(counts):
    """Return (active_category_list, A_counts, F_counts) per remainder theorem."""
    vs = vecs_of(counts)
    act = [c for c in range(4) if sum(vs[c]) % 3]
    A = [0] * N_TILES
    F = [0] * N_TILES
    for c in range(4):
        b = CAT_BASE[c]
        tgt = A if c in act else F
        for t, x in enumerate(vs[c]):
            tgt[b + t] = x
    return act, tuple(A), tuple(F)


def hand_type(counts):
    """'I' single-category active, 'II' two-category active, 'X' impossible."""
    act = active_cats(counts)
    if len(act) == 1 and sum(vec_of(counts, act[0])) % 3 == 1:
        return "I"
    if len(act) == 2:
        vs = vecs_of(counts)
        if all(sum(vs[c]) % 3 == 2 for c in act):
            return "II"
    return "X"


# ---------------------------------------------------------------- codes
def counts_list(H):
    return list(H)


def max_common_code_len(hands):
    """K = sum_t min_H H[t].  A common code of length k exists iff k <= K."""
    mn = [4] * N_TILES
    for h in hands:
        for t in range(N_TILES):
            x = h[t]
            if x < mn[t]:
                mn[t] = x
    return sum(mn), mn


def codes_of(H, k):
    """All ordered k-tuples (as tuples of tile ids) whose multiset is a sub-multiset of H."""
    tiles = tiles_of(H)
    out = set()
    for combo in itertools.combinations_with_replacement(range(N_TILES), k):
        need = {}
        ok = True
        for x in combo:
            need[x] = need.get(x, 0) + 1
            if need[x] > H[x]:
                ok = False
                break
        if not ok:
            continue
        for p in set(itertools.permutations(combo)):
            out.add(p)
    return out


def min_common_code_len_naive(hands):
    """Naive intersection of M_k for growing k, for cross-checking."""
    return max_common_code_len(hands)


if __name__ == "__main__":
    # tiny self-test
    assert melds_ok9((1, 1, 1, 0, 0, 0, 0, 0, 0))
    assert not melds_ok9((1, 1, 0, 0, 0, 0, 0, 0, 0))
    h = counts_of([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    h = list(h)
    h[0] = 1
    h[1] = 1
    h[2] = 1
    h[3] = 1
    h[4] = 1
    h[5] = 1
    h[6] = 1
    h[7] = 1
    h[8] = 1
    h[9] = 4
    print("self-test waits of 111222333444m+5m?:", mask_names(waits(tuple(h))))
    print("mjcore ok")
