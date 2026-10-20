#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""refit_local_k4.py <plan.json>
局部重排: 只保留"混门码"占用, 对每个含单门手牌的类用【最小命中集】重设本门码.
=> 释放被逐 A 码占满的本门池 (m/p/s 9^4=6561), 同时保证单门手牌全覆盖.
输出 work/verify/plan_k4_refit.json
"""
import json, sys, os, time, itertools
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
CATS = {"m": (9, 0), "p": (9, 9), "s": (9, 18), "z": (7, 27)}
HON = {"E": 27, "S": 28, "W": 29, "N": 30, "Haku": 31, "Hatsu": 32, "Chun": 33}
def to_idx(w):
    if isinstance(w, int): return [t for t in range(34) if (w >> t) & 1]
    out = []
    for nm in w:
        if isinstance(nm, int): out.append(nm)
        elif nm in HON: out.append(HON[nm])
        else: out.append("mps".index(nm[-1]) * 9 + int(nm[0]) - 1)
    return out
def cat(t): return 0 if t < 9 else 1 if t < 18 else 2 if t < 27 else 3
def load_cache(name):
    d = np.load(os.path.join(HERE, "cache_w_%s.npz" % name))
    return d["hands"], d["wids"], json.load(open(os.path.join(HERE, "cache_w_%s.json" % name)))

def greedy_cover(Hu, K, off, used, cap_ms):
    """贪心: 每次选能覆盖最多未覆盖手牌的本门 4-多重集(需有未占用的排列)"""
    n = len(Hu)
    uncovered = np.ones(n, dtype=bool)
    chosen = []
    allneed = {}
    while uncovered.any():
        best = None; bestcnt = -1; bestmask = None
        for m in cap_ms:
            need = allneed.get(m)
            if need is None:
                need = np.zeros(K, dtype=np.int8)
                for t in m: need[t] += 1
                allneed[m] = need
            mask = (Hu >= need).all(axis=1) & uncovered
            c = int(mask.sum())
            if c > bestcnt: bestcnt, best, bestmask = c, m, mask
        if best is None or bestcnt == 0: return None
        free = None
        for pm in sorted(set(itertools.permutations(best))):
            code = tuple(off + t for t in pm)
            if code not in used: free = code; break
        if free is None:
            cap_ms = [m for m in cap_ms if m != best]
            continue
        used.add(free); chosen.append(free); uncovered &= ~bestmask
    return chosen

def main():
    path = sys.argv[1]
    p = json.load(open(path, encoding="utf-8"))
    rows = p["plan"]
    plancls, wkeys = {}, []
    for r in rows:
        W = frozenset(to_idx(r["W"])); plancls[W] = [tuple(c) for c in r["codes"]]; wkeys.append(W)
    # 1) 先找出"含单门手牌"的类 (只有这些类才允许重置本门码)
    has_single = set()
    for name, (K, off) in CATS.items():
        hands, wids, wlist = load_cache(name)
        for Wl in wlist:
            has_single.add(frozenset(Wl))
    # used = 不含单门手牌类的全部码 + 含单门手牌类的混门码
    used = set()
    for W, cs in plancls.items():
        if W in has_single:
            keep = [c for c in cs if len(set(cat(t) for t in c)) >= 2]
            for c in keep: used.add(c)
            plancls[W] = keep
        else:
            for c in cs: used.add(c)
            plancls[W] = list(cs)
    rep = {"base": path, "suits": {}, "t0": round(time.time(), 1)}
    for name, (K, off) in CATS.items():
        hands, wids, wlist = load_cache(name)
        ms_all = list(itertools.combinations_with_replacement(range(K), 4))
        fixed = total_new = 0
        for wid, Wl in enumerate(wlist):
            W = frozenset(Wl)
            if W not in plancls: continue
            idx = np.nonzero(wids == wid)[0]
            H = hands[idx]
            cov = np.zeros(len(idx), dtype=bool)
            for c in plancls[W]:
                if any(t < off or t >= off + K for t in c): continue
                need = np.zeros(K, dtype=np.int8)
                for t in c: need[t - off] += 1
                cov |= (H >= need).all(axis=1)
            Hu = H[~cov]
            if len(Hu) == 0: continue
            cap_ms = [m for m in ms_all
                      if any(tuple(off + u for u in pm) not in used for pm in set(itertools.permutations(m)))
                      and (Hu >= np.array([m.count(i) for i in range(K)], dtype=np.int8)).all(axis=1).any()]
            sel = greedy_cover(Hu, K, off, used, cap_ms)
            if sel is None:
                print("  FAIL class", [Wl], name, flush=True); continue
            plancls[W].extend(sel); fixed += 1; total_new += len(sel)
        rep["suits"][name] = {"classes_refit": fixed, "new_local_codes": total_new}
        print(name, json.dumps(rep["suits"][name]), flush=True)
    out_rows = [{"W": r["W"], "codes": [list(c) for c in plancls[frozenset(to_idx(r["W"]))]], "modes": r.get("modes", [])} for r in rows]
    out = {"k": p.get("k", 4), "n_classes": len(out_rows), "n_codes": sum(len(r["codes"]) for r in out_rows),
           "plan": out_rows, "base": path, "refit": rep}
    json.dump(out, open(os.path.join(HERE, "plan_k4_refit.json"), "w"), ensure_ascii=False)
    print("TOTAL classes", len(out_rows), "codes", out["n_codes"], "secs", round(time.time() - rep["t0"], 1))

if __name__ == "__main__":
    main()
