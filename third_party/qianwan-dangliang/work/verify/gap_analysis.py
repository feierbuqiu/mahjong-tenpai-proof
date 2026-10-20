#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T6b: 对当前 plan 做缺口分析: 995 个空码类 vs 有码类的真实失败."""
import json, sys, itertools, time
from collections import defaultdict
sys.path.insert(0, "work/verify")
from indep_core import compute_W, gen_vectors

T0 = time.time()
plan = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "work/strategy/out/plan.json", encoding="utf-8"))
rows = plan["plan"]
plancls = {frozenset(r["W"]): [tuple(c) for c in r["codes"]] for r in rows}
zero = [W for W, cs in plancls.items() if not cs]
print("zero-code classes:", len(zero))

def contains(h, c):
    need = {}
    for t in c: need[t] = need.get(t, 0) + 1
    return all(h[t] >= v for t, v in need.items())

out = {"zero_code_classes": len(zero), "suits": {}, "chiitoi_fail_nonempty": [], "chiitoi_fail_zero": 0}
K_CAT = ((9, 0), (9, 9), (9, 18), (7, 27))
for name, (K, off) in zip(("m", "p", "s", "z"), K_CAT):
    n = 0; zero_hands = 0; cov_fail = []; snd_fail = []; nlisten = 0
    codes_here = {}
    for W, cs in plancls.items():
        for c in cs:
            if all(off <= t < off + K for t in c): codes_here[c] = W
    for h in gen_vectors(K, 13):
        c = [0] * 34
        for i, x in enumerate(h):
            if x: c[off + i] = x
        W = compute_W(c)
        if not W: continue
        nlisten += 1; n += 1
        cs = plancls.get(frozenset(W))
        if not cs:
            zero_hands += 1; continue
        if not any(contains(c, code) for code in cs):
            if len(cov_fail) < 5: cov_fail.append({"W": sorted(W), "hand": list(h)})
        tiles = [t for t in range(off, off + K) if c[t] > 0]
        bad = None
        for comb in itertools.combinations_with_replacement(tiles, 3):
            for pm in set(itertools.permutations(comb)):
                w2 = codes_here.get(pm)
                if w2 is not None and w2 != frozenset(W):
                    bad = (list(pm), sorted(w2), sorted(W)); break
            if bad: break
        if bad and len(snd_fail) < 5: snd_fail.append(bad)
    out["suits"][name] = {"listening_hands": nlisten, "hands_in_zero_code_classes": zero_hands,
                          "coverage_fail": len(cov_fail), "soundness_fail": len(snd_fail),
                          "coverage_examples": cov_fail, "soundness_examples": snd_fail}
    print(name, json.dumps(out["suits"][name], ensure_ascii=False)[:400], flush=True)

# chiitoi: 用 global.json 的 descriptors
g = json.load(open("work/data/out/global.json", encoding="utf-8"))
HON = {"E": 27, "S": 28, "W": 29, "N": 30, "Haku": 31, "Hatsu": 32, "Chun": 33}
def idx(nm):
    if nm in HON: return HON[nm]
    return "mps".index(nm[-1]) * 9 + int(nm[0]) - 1
def chiitoi_ok(z, codes):
    zcodes = [c for c in codes if c.count(z) <= 1]
    single = set(); hyper = []
    for c in zcodes:
        R = frozenset(t for t in c if t != z)
        if not R: return True
        if len(R) == 1: single |= R
        else: hyper.append(R)
    allowed = [t for t in range(34) if t != z and t not in single]
    found = []
    def rec(start, K_):
        if found: return
        if len(K_) == 6:
            Ks = set(K_)
            if all(not (R <= Ks) for R in hyper): found.append(list(K_))
            return
        if len(allowed) - start < 6 - len(K_): return
        for i in range(start, len(allowed)):
            K_.append(allowed[i]); rec(i + 1, K_); K_.pop()
            if found: return
    rec(0, [])
    return not found
for key, lst in g["chiitoi_descriptors"].items():
    for d in lst:
        z = idx(d["z"]); W = frozenset(set(idx(x) for x in d["Wstd"]) | {z})
        cs = plancls.get(W)
        if not cs:
            out["chiitoi_fail_zero"] += 1
        elif not chiitoi_ok(z, cs):
            if len(out["chiitoi_fail_nonempty"]) < 10:
                out["chiitoi_fail_nonempty"].append({"W": sorted(W), "z": z})
print("chiitoi: fail in zero-code classes:", out["chiitoi_fail_zero"],
      " fail in classes WITH codes:", len(out["chiitoi_fail_nonempty"]), flush=True)
json.dump(out, open("work/verify/gap_analysis.json", "w"), ensure_ascii=False, indent=1)
print("elapsed", round(time.time() - T0, 1))
