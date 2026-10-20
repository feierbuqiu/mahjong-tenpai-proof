#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dump_gap_hands.py <plan.json> <class:1p,4p> [cat] -- 列出该类的未覆盖手牌 + 该类码.
用 fastcov 的 W/hands 缓存, 秒级。
"""
import json, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
CATS = {"m": (9, 0), "p": (9, 9), "s": (9, 18), "z": (7, 27)}
HON = {"E": 27, "S": 28, "W": 29, "N": 30, "Haku": 31, "Hatsu": 32, "Chun": 33}
HONN = ["E", "S", "W", "N", "Haku", "Hatsu", "Chun"]
NM = lambda t: ("%d%s" % (t % 9 + 1, "mps"[t // 9])) if t < 27 else HONN[t - 27]
def to_idx_one(nm):
    if nm in HON: return HON[nm]
    return "mps".index(nm[-1]) * 9 + int(nm[0]) - 1
def to_idx(w):
    if isinstance(w, int): return [t for t in range(34) if (w >> t) & 1]
    out = []
    for nm in w:
        if isinstance(nm, int): out.append(nm)
        elif nm in HON: out.append(HON[nm])
        else: out.append(to_idx_one(nm))
    return out

def load_cache(name):
    d = np.load(os.path.join(HERE, "cache_w_%s.npz" % name))
    return d["hands"], d["wids"], json.load(open(os.path.join(HERE, "cache_w_%s.json" % name)))

def main():
    plan_path = sys.argv[1]
    target = frozenset(to_idx_one(x) for x in sys.argv[2].split(","))
    p = json.load(open(plan_path, encoding="utf-8"))
    rows = p["plan"] if isinstance(p, dict) and "plan" in p else p
    plancls = {frozenset(to_idx(r["W"])): [tuple(c) for c in r["codes"]] for r in rows}
    codes = plancls.get(target)
    cat = "mpsz"[[i for i, t in enumerate(sorted(target))][0] // 9] if target else "m"
    c0 = min(target)
    cat = "m" if c0 < 9 else "p" if c0 < 18 else "s" if c0 < 27 else "z"
    K, off = CATS[cat]
    hands, wids, wlist = load_cache(cat)
    wid = None
    for i, W in enumerate(wlist):
        if frozenset(W) == target: wid = i; break
    print("plan:", plan_path, "| class:", ",".join(NM(t) for t in sorted(target)), "| cat:", cat)
    print("codes in plan for this class:", "None(no row)" if codes is None else ("%d 条" % len(codes)))
    if codes: print("  codes:", [[NM(t) for t in c] for c in codes[:20]], "..." if len(codes) > 20 else "")
    if wid is None:
        print("class has no single-suit hands"); return
    idx = np.nonzero(wids == wid)[0]
    H = hands[idx]
    covered = np.zeros(len(idx), dtype=bool)
    for c in (codes or []):
        if any(t < off or t >= off + K for t in c): continue
        need = np.zeros(K, dtype=np.int8)
        for t in c: need[t - off] += 1
        covered |= (H >= need).all(axis=1)
    unc = idx[~covered]
    print("class hands in this suit: %d, uncovered: %d" % (len(idx), len(unc)))
    for j in unc[:6]:
        row = hands[j]
        print("   hand:", " ".join(NM(off + i) for i in range(K) for _ in range(int(row[i]))))

if __name__ == "__main__":
    main()
