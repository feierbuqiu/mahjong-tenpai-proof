#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T6b 缺口精确统计: 空码类 / 有码类的覆盖失败 / chiitoi / Type I 块."""
import json, sys, itertools, time
from collections import defaultdict
sys.path.insert(0, "work/verify")
from indep_core import compute_W, gen_vectors

T0 = time.time()
plan = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "work/strategy/out/plan.json", encoding="utf-8"))
if isinstance(plan, list): plan = {"plan": plan}
HON0 = {"E": 27, "S": 28, "W": 29, "N": 30, "Haku": 31, "Hatsu": 32, "Chun": 33}
def _to_idx(w):
    if isinstance(w, int): return [t for t in range(34) if (w >> t) & 1]
    out = []
    for nm in w:
        if isinstance(nm, int): out.append(nm)
        elif nm in HON0: out.append(HON0[nm])
        else: out.append("mps".index(nm[-1]) * 9 + int(nm[0]) - 1)
    return out
plan["plan"] = [{"W": _to_idx(r["W"]), "codes": r["codes"]} for r in plan["plan"]]
plancls = {frozenset(r["W"]): [tuple(c) for c in r["codes"]] for r in plan["plan"]}
zero = {W for W, cs in plancls.items() if not cs}
def contains(h, c):
    need = {}
    for t in c: need[t] = need.get(t, 0) + 1
    return all(h[t] >= v for t, v in need.items())
out = {"zero_code_classes": len(zero)}
# 类别分布
catof = lambda W: len(set(0 if t < 9 else 1 if t < 18 else 2 if t < 27 else 3 for t in W))
from collections import Counter
out["zero_code_by_ncat"] = dict(Counter(catof(W) for W in zero))
out["coded_by_ncat"] = dict(Counter(catof(W) for W in plancls if W not in zero))
# 单类别手牌
res = {}
for name, (K, off) in zip(("m", "p", "s", "z"), ((9, 0), (9, 9), (9, 18), (7, 27))):
    z_hands = 0; cf = 0; cf_zero = 0; ex = []
    for h in gen_vectors(K, 13):
        c = [0] * 34
        for i, x in enumerate(h):
            if x: c[off + i] = x
        W = compute_W(c)
        if not W: continue
        cs = plancls.get(frozenset(W))
        if not cs:
            if frozenset(W) in zero: z_hands += 1; cf_zero += 1; continue
        if not any(contains(c, code) for code in cs):
            cf += 1
            if len(ex) < 5: ex.append({"W": sorted(W), "hand": list(h)})
    res[name] = {"uncovered_hands": cf, "of_which_zero_code_class": cf_zero, "examples": ex}
    print(name, json.dumps(res[name])[:300], flush=True)
out["suits"] = res
# chiitoi
g = json.load(open("work/data/out/global.json", encoding="utf-8"))
HON = {"E": 27, "S": 28, "W": 29, "N": 30, "Haku": 31, "Hatsu": 32, "Chun": 33}
def idx(nm): return HON[nm] if nm in HON else "mps".index(nm[-1]) * 9 + int(nm[0]) - 1
def ok(z, codes):
    zc = [c for c in codes if c.count(z) <= 1 and all(c.count(t) <= 2 for t in set(c) if t != z)]
    single = set(); hyper = []
    for c in zc:
        R = frozenset(t for t in c if t != z)
        if not R: return True
        if len(R) == 1: single |= R
        else: hyper.append(R)
    allowed = [t for t in range(34) if t != z and t not in single]
    found = []
    def rec(s, Kx):
        if found: return
        if len(Kx) == 6:
            Ks = set(Kx)
            if all(not (R <= Ks) for R in hyper): found.append(1)
            return
        if len(allowed) - s < 6 - len(Kx): return
        for i in range(s, len(allowed)):
            Kx.append(allowed[i]); rec(i + 1, Kx); Kx.pop()
            if found: return
    rec(0, [])
    return not found
bad_zero = 0; bad_coded = 0; ex2 = []
for key, lst in g["chiitoi_descriptors"].items():
    for d in lst:
        z = idx(d["z"]); W = frozenset(set(idx(x) for x in d["Wstd"]) | {z})
        cs = plancls.get(W)
        if cs is None: continue
        if not cs: bad_zero += 1
        elif not ok(z, cs):
            bad_coded += 1
            if len(ex2) < 5: ex2.append({"W": sorted(W), "z": z})
out["chiitoi"] = {"fail_zero_code_class": bad_zero, "fail_coded_class": bad_coded, "examples": ex2}
print("chiitoi zero", bad_zero, "coded", bad_coded, flush=True)
# Type I blocks
uncovered_blocks = 0; unc_zero = 0; unc_coded = []
def parse(ds, ci):
    off = (0, 9, 18, 27)[ci]; u = [0] * 34
    for i, ch in enumerate(ds):
        if ch != "0": u[off + i] = int(ch)
    return u
SU = {"m": 0, "p": 1, "s": 2, "z": 3}
DEC = {}
def dec_vecs(ci, s):
    key = (ci, s)
    if key in DEC: return DEC[key]
    from indep_core import melds_only, melds_only_honor
    K = (9, 9, 9, 7)[ci]; hon = (ci == 3); off = (0, 9, 18, 27)[ci]
    o = []
    for v in gen_vectors(K, s):
        if (melds_only_honor(v) if hon else melds_only(v)):
            u = [0] * 34
            for i, x in enumerate(v):
                if x: u[off + i] = x
            o.append(tuple(u))
    DEC[key] = o; return o
def covered(A, inert, m, codes):
    if any(contains(A, c) for c in codes): return True
    ii = [SU[x] for x in inert]
    def rec(i, rem, hand):
        for c in codes:
            if contains(hand, c): return True
        if i == len(ii): return rem != 0
        ci = ii[i]
        for s in range(0, rem + 1, 3):
            if (rem - s) > 12 * (len(ii) - i - 1): continue
            for v in dec_vecs(ci, s):
                h2 = list(hand)
                for t, x in enumerate(v): h2[t] += x
                if not rec(i + 1, rem - s, h2): return False
        return True
    return rec(0, m, list(A))
for row in g["classes"]:
    W = frozenset()
    names = row["W"]
    Ws = frozenset()
    for nm in names:
        Ws |= {HON[nm] if nm in HON else "mps".index(nm[-1]) * 9 + int(nm[0]) - 1}
    if Ws not in plancls: continue
    codes = plancls[Ws]
    if any(s["kind"] == "kokushi" for s in row.get("sources", [])): continue
    for s in row.get("sources", []):
        if s["kind"] != "I": continue
        ci = SU[s["cat"]]; A = parse(s["A"], ci)
        m = 13 - sum(A)
        if not covered(A, s["inert"], m, codes):
            uncovered_blocks += 1
            if not codes: unc_zero += 1
            elif len(unc_coded) < 5: unc_coded.append({"W": sorted(Ws), "A": s["A"], "cat": s["cat"]})
out["typeI_blocks_uncovered"] = {"total": uncovered_blocks, "in_zero_code_class": unc_zero,
                                 "in_coded_class": uncovered_blocks - unc_zero, "examples_coded": unc_coded}
print("typeI uncovered", uncovered_blocks, "zero-class", unc_zero, flush=True)
out["elapsed"] = round(time.time() - T0, 1)
json.dump(out, open("work/verify/gap_exact.json", "w"), ensure_ascii=False, indent=1)
