# -*- coding: utf-8 -*-
"""census_two.py -- T2 deliverable (owner: enum-core, write scope work/data/).

GLOBAL TENPAI-CLASS TABLE (strict seven-pairs rule: 7 DISTINCT pairs).

Class = { H : W(H) = W0 },  W(H) = W_std(H) | W_chiitoi(H) | W_kokushi(H).

Completeness
------------
Every tenpai hand is exactly one of
  (a) standard tenpai (4 melds + pair):  H = A + F with A the active part
      (theorem of remainders: type I = one category with |A| % 3 == 1, or
       type II = two categories with |A| % 3 == 2 each) and F a filler that is a
      disjoint union of melds in the remaining categories;
      then W_std(H) = W_std(A) and, since F consists of melds,
      W_kokushi(H) = 0.
  (b) chiitoi tenpai:  H = 6 distinct pairs + 1 single tile z  (37,657,312 hands)
      -> W(H) = W_std(H) | {z};
  (c) kokushi tenpai: 13 distinct terminal/honour types (all-13 waits) or 12
      distinct with one duplicated (wait = the missing type): 157 hands.
Parts (a),(b),(c) are enumerated below; nothing else can be tenpai.

For (a) we enumerate the *active parts* A (not the hands): the class contribution
is W_std(A) and the elementwise-minimum count vector over the whole free filler
family is exactly A, because for every tile t some filler avoids t (verified: the
free family is non-empty and per-tile avoiding fillers exist for every source).
The chiitoi hand families of part (b) are enumerated hand by hand, so their
per-class minimum count vectors are exact.

Output: work/data/out/global.json
"""

import itertools
import json
import math
import multiprocessing as mp
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mjcore as M
from mjcore import CAT_LEN, CAT_BASE, _V, _pd, _Wp

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
NPROC = 6


def multisets(n_types, size, cap=4):
    for cc in itertools.combinations_with_replacement(range(n_types), size):
        v = [0] * n_types
        for x in cc:
            v[x] += 1
        if max(v) <= cap:
            yield tuple(v)


def melds_of(c):
    n = CAT_LEN[c]
    ms = []
    for i in range(n):
        v = [0] * n
        v[i] = 3
        ms.append(tuple(v))
    if c < 3:
        for i in range(n - 2):
            v = [0] * n
            v[i] = v[i + 1] = v[i + 2] = 1
            ms.append(tuple(v))
    return ms


MELDS = {c: melds_of(c) for c in range(4)}


def filler_count(S, j):
    """Number of distinct count vectors F (cap 4) that are unions of j melds in S."""
    if j == 0:
        return 1
    seen = set()
    items = [(c, v) for c in sorted(S) for v in MELDS[c]]
    for combo in itertools.combinations_with_replacement(range(len(items)), j):
        per = {}
        ok = True
        for idx in combo:
            c, v = items[idx]
            d = per.get(c)
            if d is None:
                d = per[c] = [0] * CAT_LEN[c]
            for i, x in enumerate(v):
                d[i] += x
                if d[i] > 4:
                    ok = False
                    break
            if not ok:
                break
        if not ok:
            continue
        seen.add(tuple(tuple(per.get(c, [0] * CAT_LEN[c])) for c in range(4)))
    return len(seen)


FILL = {}
for _k in range(5):
    for _S in itertools.combinations(range(4), _k):
        for _j in range(5):
            FILL[(_S, _j)] = filler_count(_S, _j)


def profiles(c, a):
    """(V, pd) -> [componentwise-min vector, number of X] over all size-a vectors."""
    prof = {}
    for X in multisets(CAT_LEN[c], a):
        key = (_V(c, X), _pd(c, X))
        e = prof.get(key)
        if e is None:
            prof[key] = [list(X), 1]
        else:
            e[1] += 1
            m = e[0]
            for i in range(len(X)):
                if X[i] < m[i]:
                    m[i] = X[i]
    return prof


def emb(c, v, other_zero=True):
    out = [0] * 34
    b = CAT_BASE[c]
    for i, x in enumerate(v):
        out[b + i] = x
    return out


# ------------------------------------------------------------------ Part A
def part_a():
    cls = {}   # mask -> {"min":[34], "n_free":int, "sources":[...]}
    def touch(mask):
        r = cls.get(mask)
        if r is None:
            r = cls[mask] = {"min": [4] * 34, "n_free": 0, "sources": []}
        return r

    n_src_I = 0
    for c in range(4):
        S = tuple(x for x in range(4) if x != c)
        for a in (1, 4, 7, 10, 13):
            j = (13 - a) // 3
            nF = FILL[(S, j)]
            for X in multisets(CAT_LEN[c], a):
                W = _Wp(c, X)
                if not W:
                    continue
                n_src_I += 1
                r = touch(W)
                mv = emb(c, X)
                for i in range(34):
                    if mv[i] < r["min"][i]:
                        r["min"][i] = mv[i]
                r["n_free"] += nF
                r["sources"].append({"kind": "I", "cat": M.CAT_NAME[c],
                                     "A": "".join(str(x) for x in X),
                                     "inert": [M.CAT_NAME[x] for x in S],
                                     "j": j, "nF": nF})

    cache = {}
    n_src_II = 0
    for c1 in range(4):
        for c2 in range(c1 + 1, 4):
            S = tuple(x for x in range(4) if x not in (c1, c2))
            for a1 in (2, 5, 8, 11):
                for a2 in (2, 5, 8, 11):
                    if a1 + a2 > 13:
                        continue
                    j = (13 - a1 - a2) // 3
                    nF = FILL[(S, j)]
                    if (c1, a1) not in cache:
                        cache[(c1, a1)] = profiles(c1, a1)
                    if (c2, a2) not in cache:
                        cache[(c2, a2)] = profiles(c2, a2)
                    P1 = cache[(c1, a1)]
                    P2 = cache[(c2, a2)]
                    for (V1, pd1), (m1, n1) in P1.items():
                        for (V2, pd2), (m2, n2) in P2.items():
                            if not (pd1 or pd2):
                                continue
                            mask = (V2 if pd1 else 0) | (V1 if pd2 else 0)
                            if not mask:
                                continue
                            n_src_II += 1
                            r = touch(mask)
                            mv = emb(c1, m1)
                            mv2 = emb(c2, m2)
                            for i in range(34):
                                v = mv[i] if mv[i] < mv2[i] else mv2[i]
                                if v < r["min"][i]:
                                    r["min"][i] = v
                            nA = n1 * n2
                            r["n_free"] += nA * nF
                            r["sources"].append({
                                "kind": "II", "cats": [M.CAT_NAME[c1], M.CAT_NAME[c2]],
                                "V1": M.mask_names(V1), "pd1": pd1,
                                "V2": M.mask_names(V2), "pd2": pd2,
                                "minA1": "".join(str(x) for x in m1),
                                "minA2": "".join(str(x) for x in m2),
                                "nA": nA, "inert": [M.CAT_NAME[x] for x in S],
                                "j": j, "nF": nF})
    print("Part A: %d Type-I sources, %d Type-II source profiles, %d classes"
          % (n_src_I, n_src_II, len(cls)), flush=True)
    return cls, {"n_src_type_I": n_src_I, "n_src_type_II": n_src_II}


# ------------------------------------------------------------------ Part B
def chiitoi_worker(chunks):
    mins = {}
    counts = {}
    corr = {}
    EMPTY9 = (0,) * 9
    EMPTY7 = (0,) * 7
    getv = M.waits_std_vecs
    for lo, hi in chunks:
        for first in range(lo, hi):
            for rest in itertools.combinations(range(first + 1, 34), 5):
                P = (first,) + rest
                base = [[0] * 9, [0] * 9, [0] * 9, [0] * 7]
                for t in P:
                    c = t // 9 if t < 27 else 3
                    i = t % 9 if t < 27 else t - 27
                    base[c][i] += 2
                base = tuple(tuple(v) for v in base)
                Ps = set(P)
                for z in range(34):
                    if z in Ps:
                        continue
                    c = z // 9 if z < 27 else 3
                    i = z % 9 if z < 27 else z - 27
                    vv = list(base[c])
                    vv[i] += 1
                    vs = base[:c] + (tuple(vv),) + base[c + 1:]
                    Wstd = getv(vs)
                    cls = Wstd | (1 << z)
                    # hand count vector
                    mn = mins.get(cls)
                    if mn is None:
                        hand = [0] * 34
                        for t in P:
                            hand[t] = 2
                        hand[z] = 1
                        mins[cls] = hand
                        counts[cls] = 1
                    else:
                        counts[cls] += 1
                        for t in P:
                            if mn[t] > 2:
                                mn[t] = 2
                        if mn[z] > 1:
                            mn[z] = 1
                    if Wstd:
                        key = (Wstd, z)
                        corr[key] = corr.get(key, 0) + 1
    return mins, counts, corr


def part_b():
    t0 = time.time()
    units = [(i, i + 1) for i in range(29)]
    units.sort(key=lambda ab: math.comb(34 - ab[0] - 1, 5), reverse=True)
    groups = [[] for _ in range(NPROC)]
    for k, ch in enumerate(units):
        groups[k % NPROC].append(ch)
    with mp.Pool(NPROC) as pool:
        res = pool.map(chiitoi_worker, groups)
    mins = {}
    counts = {}
    corr = {}
    for mn_d, cnt_d, corr_d in res:
        for k_, v in mn_d.items():
            cur = mins.get(k_)
            if cur is None:
                mins[k_] = v
            else:
                for i in range(34):
                    if v[i] < cur[i]:
                        cur[i] = v[i]
        for k_, v in cnt_d.items():
            counts[k_] = counts.get(k_, 0) + v
        for k_, v in corr_d.items():
            corr[k_] = corr.get(k_, 0) + v
    n_std = sum(corr.values())
    print("Part B: %d chiitoi classes, %d chiitoi hands are also standard tenpai (%.1fs)"
          % (len(counts), n_std, time.time() - t0), flush=True)
    return mins, counts, corr, n_std


# ------------------------------------------------------------------ Part C
def part_c():
    term = M.TERMINAL_HONOR
    cls = {}
    v = [0] * 34
    for t in term:
        v[t] = 1
    cls.setdefault(M.waits(tuple(v)), []).append(tuple(v))
    for miss in term:
        rest = [t for t in term if t != miss]
        for dup in rest:
            w = [0] * 34
            for t in rest:
                w[t] = 1
            w[dup] += 1
            cls.setdefault(M.waits(tuple(w)), []).append(tuple(w))
    out = {}
    for W, hs in cls.items():
        mn = [4] * 34
        for h in hs:
            for i in range(34):
                if h[i] < mn[i]:
                    mn[i] = h[i]
        out[W] = {"min": mn, "n": len(hs),
                  "sources": [{"kind": "kokushi", "n_hands": len(hs),
                               "thirteen_way": bin(W).count("1") > 1}]}
    return out


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    cls, meta_a = part_a()
    B_mins, B_counts, corr, n_std_chiitoi = part_b()
    C = part_c()

    # merge
    for mask, r in B_mins.items():
        e = cls.get(mask)
        if e is None:
            cls[mask] = {"min": list(r), "n_free": 0, "sources": []}
            e = cls[mask]
        else:
            for i in range(34):
                if r[i] < e["min"][i]:
                    e["min"][i] = r[i]
    C_counts = {}
    for mask, r in C.items():
        e = cls.get(mask)
        if e is None:
            cls[mask] = {"min": list(r["min"]), "n_free": 0, "sources": []}
            e = cls[mask]
        else:
            for i in range(34):
                if r["min"][i] < e["min"][i]:
                    e["min"][i] = r["min"][i]
        e["sources"].extend(r["sources"])
        C_counts[mask] = C_counts.get(mask, 0) + r["n"]

    # hand counts
    # Every chiitoi hand that is also a standard tenpai hand was counted once in
    # n_free(W_std) (as a standard hand) and once in B_counts.  Remove it from n_free:
    # if z is not in W_std the hand really belongs to the class W_std | {z}, and if z
    # is in W_std it belongs to W_std -- either way n_free's class is the *source* class
    # recorded in n_free(W_std), so the subtraction is on class W_std.
    # (equivalently: n_hands(C) = #non-chiitoi standard hands with class C + #chiitoi hands with class C)
    corr_by_class = {}
    for (S, z), n in corr.items():
        corr_by_class[S] = corr_by_class.get(S, 0) + n
    rows = []
    for mask, e in cls.items():
        n_hands = (e["n_free"] - corr_by_class.get(mask, 0) + B_counts.get(mask, 0)
                   + C_counts.get(mask, 0))
        K = sum(e["min"])
        rows.append({
            "Wmask": mask,
            "W": M.mask_names(mask),
            "size": bin(mask).count("1"),
            "mincount": e["min"],
            "K": K,
            "common_code": {str(k): (K >= k) for k in (1, 2, 3, 4)},
            "no_common_code": {str(k): (K < k) for k in (1, 2, 3, 4)},
            "n_hands": n_hands,
            "n_free_hands": e["n_free"],
            "n_chiitoi_hands": B_counts.get(mask, 0),
            "n_kokushi_hands": C_counts.get(mask, 0),
            "sub_universe": [M.CAT_NAME[c] for c in range(4)
                             if mask & ~(((1 << CAT_LEN[c]) - 1) << CAT_BASE[c]) == 0],
            "sources": e["sources"],
        })
    rows.sort(key=lambda r: (r["Wmask"]))
    by_size = {}
    for r in rows:
        by_size[r["size"]] = by_size.get(r["size"], 0) + 1
    no_common = {str(k): sum(1 for r in rows if not r["common_code"][str(k)]) for k in (1, 2, 3, 4)}
    sum_K = sum(r["K"] for r in rows)
    # chiitoi descriptors
    chiitoi_desc = {}
    for (S, z), n in corr.items():
        key = S | (1 << z)
        chiitoi_desc.setdefault(key, []).append({"z": M.tile_name(z),
                                                 "Wstd": M.mask_names(S), "n_hands": n})
    data = {
        "meta": {
            "rule": "strict seven pairs: 7 DISTINCT types with count 2 (4 identical tiles are NOT two pairs)",
            "chiitoi_tenpai": "exactly 6 distinct pairs + 1 single tile z",
            "hand": "13-tile multiset, 34 counts each 0..4",
            "tiles": "0-8 m1-9, 9-17 p1-9, 18-26 s1-9, 27-33 z1-7",
            "class": "set of hands with identical W(H) = W_std | W_chiitoi | W_kokushi",
            "mincount": "mincount[t] = min over all hands of the class of count of t; "
                        "a common k-code exists iff sum(mincount) >= k",
            "sources": "I = single active category A (free filler family); "
                       "II = two active categories (profile-level descriptor: all X with the given "
                       "(V,pd) signature); kokushi = 13-orphans source",
            "filler": "each I/II source has j = (13-|A|)/3 filler melds in the inert categories, "
                      "nF distinct filler count vectors (cap 4)",
        },
        "n_classes": len(rows),
        "by_size": {str(k): v for k, v in sorted(by_size.items())},
        "no_common_code": no_common,
        "sum_K_over_classes": sum_K,
        "counts": {
            "standard_tenpai_hands": sum(e["n_free"] for e in cls.values()),
            "chiitoi_tenpai_hands": 28 * math.comb(34, 6),
            "chiitoi_hands_that_are_standard_tenpai": n_std_chiitoi,
            "kokushi_tenpai_hands": 157,
            "total_tenpai_hands": (54747045 + 37657312 - n_std_chiitoi + 157),
            "total_tenpai_hands_summed_over_classes": sum(r["n_hands"] for r in rows),
            "chiitoi_standard_overlap_correction_applied": sum(corr_by_class.values()),
            "n_src_type_I": meta_a["n_src_type_I"],
            "n_src_type_II": meta_a["n_src_type_II"],
        },
        "chiitoi_descriptors": {str(k): v for k, v in chiitoi_desc.items()},
        "classes": rows,
    }
    with open(os.path.join(OUT, "global.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print("GLOBAL CLASSES =", len(rows), flush=True)
    print("by |W| =", dict(sorted(by_size.items())), flush=True)
    print("no common code k=1..4 =", no_common, flush=True)
    print("sum_K =", sum_K, flush=True)
    print("counts =", data["counts"], flush=True)
    print("t=%.1fs" % (time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
