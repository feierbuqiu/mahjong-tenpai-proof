# -*- coding: utf-8 -*-
"""fix30.py -- 重解 137 个"全未覆盖"II 型类的命中集(perclass_coverage.json -> fully_uncovered).
基线 plan_k4_zero.json(已删浪费码); 只改这些类, 其余保持; 容量/有序码全局不交.
输出 work/strategy/out/plan_k4_v5.json + out/fix30_report.json
"""
import sys, os, json, itertools, math, collections, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjlib import *
import table_lib as TL
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out")
K = 4
T0 = time.time()
def log(*a): print("[%7.1fs]" % (time.time()-T0), *a, flush=True)
HONN = ["E","S","W","N","Haku","Hatsu","Chun"]; HON = {n:27+i for i,n in enumerate(HONN)}
def to_idx(w):
    o = []
    for x in w:
        if isinstance(x, int): o.append(x)
        elif x in HON: o.append(HON[x])
        else: o.append("mps".index(x[-1])*9 + int(x[0]) - 1)
    return o
def pl(mu): return sorted(set(itertools.permutations(mu)))
def p4(mu):
    c = collections.Counter(mu); return 24 // math.prod(math.factorial(v) for v in c.values())
BASE = os.path.join(ROOT, "verify", "plan_k4_zero.json")
P = json.load(open(BASE, encoding="utf-8")); rows = P["plan"] if isinstance(P, dict) and "plan" in P else P
plancls = {frozenset(to_idx(r["W"])): [tuple(c) for c in r["codes"]] for r in rows}
used = collections.defaultdict(list)
for W, cs in plancls.items():
    for c in cs: used[tuple(sorted(c))].append((W, c))
log("基线 %s: %d 类 %d 码" % (os.path.basename(BASE), len(plancls), sum(len(v) for v in plancls.values())))
def take(mu, W):
    lst = used[mu]
    if len(lst) >= p4(mu): return None
    t = {c for _, c in lst}
    for p in pl(mu):
        if p not in t: lst.append((W, p)); return p
    return None
def contains(h, c):
    need = {}
    for t in c: need[t] = need.get(t,0)+1
    return all(h[t] >= v for t, v in need.items())
T = TL.build(); CLS = T["cls"]
def units_of(W):
    reqs = set()
    for b in CLS[W]:
        k = b[0]
        if k == "I":
            for (cc, X) in TL.block_sources(T, b)[1]:
                v = [0]*34
                for i, x in enumerate(X): v[TL.CAT_BASE[cc]+i] = x
                if sum(v) >= K: reqs.add(tuple(v))
        elif k == "II":
            am = b[5]
            if sum(am) >= K: reqs.add(tuple(am))
            else:
                for (c1, X1, c2, X2) in TL.block_sources(T, b)[1]:
                    v = [0]*34
                    for i, x in enumerate(X1): v[TL.CAT_BASE[c1]+i] += x
                    for i, x in enumerate(X2): v[TL.CAT_BASE[c2]+i] += x
                    if sum(v) >= K: reqs.add(tuple(v))
        else:
            reqs.add(tuple(b[1]))
    return [r for r in reqs if sum(r) >= K]
def ksubs34(vec):
    tiles = [t for t, n in enumerate(vec) for _ in range(min(n, K))]
    o = set()
    for combo in itertools.combinations_with_replacement(tiles, K):
        need = {}
        for x in combo: need[x] = need.get(x,0)+1
        if all(vec[x] >= v for x, v in need.items()): o.add(combo)
    return o
pc = json.load(open(os.path.join(ROOT, "verify", "perclass_coverage.json"), encoding="utf-8"))
targets = [frozenset(to_idx(e["W"])) for e in pc["fully_uncovered"]]
targets = [W for W in targets if W in plancls]
log("目标类: %d" % len(targets))
fixed = 0; miss = []; nnew = 0
for W in targets:
    plancls[W] = []
    units = units_of(W)
    cov = [False]*len(units); chosen = []
    guard = 0
    while not all(cov) and guard < 4000:
        guard += 1
        cnt = collections.Counter()
        left = [i for i, c in enumerate(cov) if not c]
        if not left: break
        for i in left:
            for mu in ksubs34(units[i]):
                if len(used[mu]) < p4(mu): cnt[mu] += 1
        if not cnt: break
        best = max(cnt, key=lambda m: (cnt[m], -len(used[m])))
        p = take(best, W)
        if p is None: break
        chosen.append(best)
        for i in left:
            if any(contains(units[i], c) for c in [best]): cov[i] = True
    plancls[W] = chosen
    nnew += len(chosen)
    if all(cov) and chosen: fixed += 1
    else: miss.append({"W": sorted(W), "units": len(units), "uncovered": sum(1 for c in cov if not c)})
log("修复: 完全覆盖 %d / %d, 仍缺 %d, 新增码 %d" % (fixed, len(targets), len(miss), nnew))
allc = [c for cs in plancls.values() for c in cs]
empty = [sorted(W) for W in plancls if not plancls[W]]
over = [mu for mu, lst in used.items() if len(lst) > p4(mu)]
log("校验: 类 %d 码 %d 不同 %d 空类 %d 超容量 %d" % (len(plancls), len(allc), len(set(allc)), len(empty), len(over)))
json.dump({"k": 4, "n_classes": len(plancls), "n_codes": len(set(allc)),
           "plan": [{"W": sorted(W), "codes": [list(c) for c in plancls[W]]} for W in sorted(plancls, key=lambda S: sorted(S))]},
          open(os.path.join(OUT, "plan_k4_v5.json"), "w", encoding="utf-8"), ensure_ascii=False)
json.dump({"base": BASE, "n_classes": len(plancls), "n_codes": len(set(allc)), "n_empty": len(empty),
           "over_capacity": len(over), "targets": len(targets), "fixed": fixed, "missing": miss[:40],
           "n_missing": len(miss), "new_codes": nnew,
           "empty_classes": empty[:20]}, open(os.path.join(OUT, "fix30_report.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
log("写出 out/plan_k4_v5.json + out/fix30_report.json")
