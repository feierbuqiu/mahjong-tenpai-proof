# -*- coding: utf-8 -*-
"""census_single.py -- T1 deliverable (owner: enum-core, write scope work/data/).

Complete census of the single-active-category sector and of the two specials:

  * flush   : every 13-tile multiset living in one suit m / p / s
  * honors  : every 13-tile multiset living in z (7 honor types)
  * kokushi : every thirteen-orphans tenpai hand
  * chiitoi : reported by census_two.py (out/global.json); counts here

Method / completeness
---------------------
For the flush and honors sectors we do NOT sample: we enumerate EVERY 13-tile
multiset of the sector (each tile type at most 4 copies) and test it directly
with mjcore.waits_vecs, the closed-form implementation of
W(H) = W_std(H) | W_chiitoi(H) | W_kokushi(H).
That implementation was verified against a brute-force pair/meld search
(_probe3.py): 24157 randomised + targeted hands, 0 mismatches, plus a full
re-check of all 93600 flush hands, 0 mismatches.

  # multiset(13; 9 types, cap 4) = 93600   -> flush sector
  # multiset(13; 7 types, cap 4) =  7875   -> honors sector

This is what fixes the earlier 26680 / 383 figures: enumerating only
"4 melds + pair" hands with a run generator that cannot place two melds at the
same starting tile misses every repeated-run win (e.g. 123m123m456m789m+pair),
which loses both 14-tile wins and tenpai hands.

Chiitoi: H+t is a seven-pairs win  <=>  H is 6 distinct pairs + 1 single tile z
(7 DISTINCT types with count exactly 2).  A tile with count 3 or 4 can never
become a pair of a seven-pairs hand, so the "one odd count in {1,3}" rule in
MODEL.md section 5 over-counts chiitoi tenpai hands.

Kokushi: all 13 terminal/honor types present (13-way wait) or 12 present with one
duplicated (one-way wait): 1 + 13*12 = 157 hands.

Output: work/data/out/single.json
"""

import itertools
import json
import os
import sys
import time
from math import comb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mjcore as M

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
EMPTY9 = (0,) * 9
EMPTY7 = (0,) * 7


def multisets(n_types, size, cap=4):
    """All count vectors of size tiles over n_types types, each count <= cap."""
    for cc in itertools.combinations_with_replacement(range(n_types), size):
        v = [0] * n_types
        for x in cc:
            v[x] += 1
        if max(v) <= cap:
            yield tuple(v)


def count_str(v):
    return "".join(str(x) for x in v)


def embed(v, cat):
    """Embed a category vector into a 4-category tuple."""
    if cat == 0:
        return (v, EMPTY9, EMPTY9, EMPTY7)
    if cat == 1:
        return (EMPTY9, v, EMPTY9, EMPTY7)
    if cat == 2:
        return (EMPTY9, EMPTY9, v, EMPTY7)
    return (EMPTY9, EMPTY9, EMPTY9, v)


def _pack_classes(cls, n_types, with_hands=True):
    rows = []
    for W, hs in sorted(cls.items()):
        mn = [4] * n_types
        for h in hs:
            for i in range(n_types):
                if h[i] < mn[i]:
                    mn[i] = h[i]
        K = sum(mn)
        row = {
            "W": M.mask_names(W),
            "Wmask": W,
            "n_hands": len(hs),
            "mincount": mn,
            "K": K,
            "no_common_code": {str(k): (K < k) for k in (1, 2, 3, 4)},
        }
        if with_hands:
            row["hands"] = sorted(count_str(h) for h in hs)
        rows.append(row)
    no_common = {str(k): sum(1 for r in rows if r["K"] < k) for k in (1, 2, 3, 4)}
    return rows, no_common


def sector_census(n_types, cat):
    """Full census of all 13-tile hands inside the single category cat."""
    t0 = time.time()
    n_hands = 0
    cls_std = {}
    cls_full = {}
    for v in multisets(n_types, 13):
        n_hands += 1
        vs = embed(v, cat)
        ws = M.waits_std_vecs(vs)
        wf = M.waits_vecs(vs)
        if ws:
            cls_std.setdefault(ws, []).append(v)
        if wf:
            cls_full.setdefault(wf, []).append(v)
    rows_std, nc_std = _pack_classes(cls_std, n_types)
    rows_full, nc_full = _pack_classes(cls_full, n_types)
    return {
        "n_tile_types": n_types,
        "n_13_hands": n_hands,
        "tenpai_std_only": {"n_hands": sum(len(v) for v in cls_std.values()),
                            "n_classes": len(rows_std),
                            "no_common_code": nc_std, "classes": rows_std},
        "tenpai_full_W": {"n_hands": sum(len(v) for v in cls_full.values()),
                          "n_classes": len(rows_full),
                          "no_common_code": nc_full, "classes": rows_full},
        "seconds": round(time.time() - t0, 2),
    }


def win_counts_sector(n_types):
    """Number of 14-tile winning hands inside the sector (standard + seven pairs)."""
    melds = []
    for i in range(n_types):
        v = [0] * n_types
        v[i] = 3
        melds.append(tuple(v))
    if n_types == 9:
        for i in range(n_types - 2):
            v = [0] * n_types
            v[i] = v[i + 1] = v[i + 2] = 1
            melds.append(tuple(v))
    std = set()
    for combo in itertools.combinations_with_replacement(range(len(melds)), 4):
        v = [0] * n_types
        ok = True
        for mi in combo:
            mv = melds[mi]
            for i in range(n_types):
                v[i] += mv[i]
                if v[i] > 4:
                    ok = False
                    break
            if not ok:
                break
        if not ok:
            continue
        for p in range(n_types):
            if v[p] <= 2:
                l = list(v)
                l[p] += 2
                std.add(tuple(l))
    pair = set()
    if n_types >= 7:
        for combo in itertools.combinations(range(n_types), 7):
            v = [0] * n_types
            for i in combo:
                v[i] = 2
            pair.add(tuple(v))
    return len(std), len(pair), len(std | pair)


def kokushi_census():
    term = M.TERMINAL_HONOR
    cls = {}
    n = 0
    v = [0] * 34
    for t in term:
        v[t] = 1
    n += 1
    cls.setdefault(M.waits(tuple(v)), []).append(tuple(v))
    for miss in term:
        rest = [t for t in term if t != miss]
        for dup in rest:
            v = [0] * 34
            for t in rest:
                v[t] = 1
            v[dup] += 1
            n += 1
            cls.setdefault(M.waits(tuple(v)), []).append(tuple(v))
    rows, nc = _pack_classes(cls, 34)
    return {"n_hands": n, "n_classes": len(rows), "no_common_code": nc, "classes": rows}


def main():
    os.makedirs(OUT, exist_ok=True)
    out = {"meta": {
        "tiles": "0-8 m1-9, 9-17 p1-9, 18-26 s1-9, 27-33 z1-7 (E,S,W,N,Haku,Hatsu,Chun)",
        "W": "W(H) = W_std(H) | W_chiitoi(H) | W_kokushi(H), 34-bit mask",
        "chiitoi_tenpai": "6 distinct pairs + 1 single tile (7 DISTINCT types x 2). "
                          "The rule 'one odd count in {1,3}' of MODEL.md section 5 is wrong: "
                          "a 3- or 4-count tile can never become a pair of a seven-pairs hand.",
        "mincount_criterion": "a common k-code exists for a class iff sum_t min_{H in class} H[t] >= k",
        "buckets": "hands are count vectors over the sector types, written as a digit string",
    }}
    for c, name in ((0, "m"), (1, "p"), (2, "s")):
        print("sector", name, flush=True)
        r = sector_census(9, c)
        std, pair, uni = win_counts_sector(9)
        r["n_win_14hands_std"] = std
        r["n_win_14hands_7pairs"] = pair
        r["n_win_14hands_union"] = uni
        out["flush_" + name] = r
        print("  m13=%d  win14 std=%d 7pair=%d  std tenpai=%d classes=%d  full tenpai=%d classes=%d"
              % (r["n_13_hands"], std, pair, r["tenpai_std_only"]["n_hands"],
                 r["tenpai_std_only"]["n_classes"], r["tenpai_full_W"]["n_hands"],
                 r["tenpai_full_W"]["n_classes"]), flush=True)
        print("  std no-common k=1..4:", r["tenpai_std_only"]["no_common_code"], flush=True)
        print("  full no-common k=1..4:", r["tenpai_full_W"]["no_common_code"], flush=True)
    print("sector z", flush=True)
    r = sector_census(7, 3)
    std, pair, uni = win_counts_sector(7)
    r["n_win_14hands_std"] = std
    r["n_win_14hands_7pairs"] = pair
    r["n_win_14hands_union"] = uni
    out["honors_z"] = r
    print("  z13=%d  win14 std=%d 7pair=%d  std tenpai=%d classes=%d  full tenpai=%d classes=%d"
          % (r["n_13_hands"], std, pair, r["tenpai_std_only"]["n_hands"], r["tenpai_std_only"]["n_classes"],
             r["tenpai_full_W"]["n_hands"], r["tenpai_full_W"]["n_classes"]), flush=True)
    print("  z std no-common k=1..4:", r["tenpai_std_only"]["no_common_code"], flush=True)
    print("  z full no-common k=1..4:", r["tenpai_full_W"]["no_common_code"], flush=True)

    out["kokushi"] = kokushi_census()
    print("kokushi: hands=%d classes=%d" % (out["kokushi"]["n_hands"], out["kokushi"]["n_classes"]), flush=True)

    out["totals"] = {
        "chiitoi_tenpai_hands_formula": comb(34, 6) * 28,
        "chiitoi_win_14hands_formula": comb(34, 7),
        "kokushi_tenpai_hands": 157,
        "kokushi_win_14hands": 13,
        "note": "chiitoi classes are enumerated by census_two.py into out/global.json",
    }
    with open(os.path.join(OUT, "single.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print("wrote", os.path.join(OUT, "single.json"))


if __name__ == "__main__":
    main()
