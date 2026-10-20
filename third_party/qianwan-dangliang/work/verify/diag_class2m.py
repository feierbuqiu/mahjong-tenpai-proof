#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""diag_class2m.py <plan.json> -- 精确诊断类 {2m} (A='101200000') 的覆盖矛盾."""
import json, sys, os, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from indep_core import melds_only, melds_only_honor, gen_vectors
HON = {"E": 27, "S": 28, "W": 29, "N": 30, "Haku": 31, "Hatsu": 32, "Chun": 33}
HONN = ["E", "S", "W", "N", "Haku", "Hatsu", "Chun"]
NM = lambda t: ("%d%s" % (t % 9 + 1, "mps"[t // 9])) if t < 27 else HONN[t - 27]
def to_idx(w):
    if isinstance(w, int): return [t for t in range(34) if (w >> t) & 1]
    out = []
    for nm in w:
        if isinstance(nm, int): out.append(nm)
        elif nm in HON: out.append(HON[nm])
        else: out.append("mps".index(nm[-1]) * 9 + int(nm[0]) - 1)
    return out
P = json.load(open(sys.argv[1], encoding="utf-8"))
rows = P["plan"]
plancls = {}
for r in rows:
    W = frozenset(to_idx(r["W"]))
    plancls[W] = [tuple(c) for c in r["codes"]]
used = set()
for cs in plancls.values():
    for c in cs: used.add(c)
codes = plancls[frozenset([1])]
A = [0] * 34
for i, ch in enumerate("101200000"):
    if ch != "0": A[i] = int(ch)
Atiles = [i for i in range(9) for _ in range(A[i])]
print("class {2m}: codes", len(codes), "| A =", [NM(t) for t in Atiles])
print("codes subset of A:", [[NM(t) for t in c] for c in codes if all(A[t] >= 1 for t in set(c)) and all(A[t] >= c.count(t) for t in set(c))])
# 关键多重集 {1m,3m,4m,4m}
m = tuple(sorted(Atiles))
perms = sorted(set(itertools.permutations(m)))
print("multiset", [NM(t) for t in m], "permutations:", len(perms),
      "used globally:", sum(1 for pm in perms if pm in used))
print("  used perms:", [[NM(t) for t in pm] for pm in perms if pm in used][:12])
# 枚举该块的全部 F
DEC = {}
def dec(ci, s):
    k = (ci, s)
    if k in DEC: return DEC[k]
    K = (9, 9, 9, 7)[ci]; hon = ci == 3; off = (0, 9, 18, 27)[ci]
    out = []
    for v in gen_vectors(K, s):
        if (melds_only_honor(v) if hon else melds_only(v)):
            u = [0] * 34
            for i, x in enumerate(v):
                if x: u[off + i] = x
            out.append(tuple(u))
    DEC[k] = out; return out
def contains(h, c):
    need = {}
    for t in c: need[t] = need.get(t, 0) + 1
    return all(h[t] >= v for t, v in need.items())
Fs = []
for a in (0, 3, 6, 9):
    for b in (0, 3, 6, 9):
        if a + b > 9: continue
        c_ = 9 - a - b
        if c_ % 3: continue
        for vp in dec(1, a):
            for vs in dec(2, b):
                for vz in dec(3, c_):
                    F = [0] * 34
                    for t, x in enumerate(vp): F[t] += x
                    for t, x in enumerate(vs): F[t] += x
                    for t, x in enumerate(vz): F[t] += x
                    Fs.append(F)
print("block F count:", len(Fs))
unc = [F for F in Fs if not any(contains([A[i] + F[i] for i in range(34)], c) for c in codes)]
print("uncovered F:", len(unc))
# 用"全 4-多重集"求该块的最小命中集 (贪婪)
cands = list(itertools.combinations_with_replacement(range(34), 4))
def greedy_cover(Flist):
    un = list(range(len(Flist))); chosen = []
    while un:
        best = None; bc = -1
        for m2 in cands:
            need = {}
            for t in m2: need[t] = need.get(t, 0) + 1
            cnt = sum(1 for j in un if all((A[t] + Flist[j][t]) >= v for t, v in need.items()))
            if cnt > bc: bc, best = cnt, m2
            if bc == len(un): break
        if best is None or bc == 0: return chosen, len(un)
        need = {}
        for t in best: need[t] = need.get(t, 0) + 1
        un = [j for j in un if not all((A[t] + Flist[j][t]) >= v for t, v in need.items())]
        chosen.append(best)
    return chosen, 0
chosen, left = greedy_cover(Fs)
print("greedy min-hit over WHOLE block:", len(chosen), "left", left)
print("  codes:", [[NM(t) for t in c] for c in chosen[:12]])
# 只对未覆盖的 142 个 F 求命中集
ch2, left2 = greedy_cover(unc)
print("greedy min-hit over the 142 uncovered F:", len(ch2), "left", left2)
print("  codes:", [[NM(t) for t in c] for c in ch2[:12]])
# 每个未覆盖 F 是否"含某个 run 对"? 统计需要什么形状
need_shapes = {"subset_of_A": 0, "run_pair": 0, "other": 0}
for F in unc:
    H = [A[i] + F[i] for i in range(34)]
    if any(all(H[t] >= c.count(t) for t in set(c)) for c in [tuple(Atiles)]):
        need_shapes["subset_of_A"] += 1
