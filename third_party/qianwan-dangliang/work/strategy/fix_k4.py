# -*- coding: utf-8 -*-
"""fix_k4.py -- 在 work/verify/plan_k4_permfix.json 基础上做局部修复(不重建):
  ① chiitoi: 61 个描述子类补 (z,a,a,b) 5组(7,7,7,6,6) 对族(93 条)
  ② Type I 残余块: 未覆盖块追加一条 4-多重集码(优先空闲排列)
输出 out/plan_k4_fixed.json (W=牌索引) + out/fix_k4_report.json
"""
import sys, os, json, itertools, math, collections, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjlib import *
import table_lib as TL
K = 4
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
T0 = time.time()
def log(*a): print("[%7.1fs]" % (time.time()-T0), *a, flush=True)
HONN = ["E", "S", "W", "N", "Haku", "Hatsu", "Chun"]
HON = {n: 27+i for i, n in enumerate(HONN)}
def to_idx(w):
    out = []
    for x in w:
        if isinstance(x, int): out.append(x)
        elif x in HON: out.append(HON[x])
        else: out.append("mps".index(x[-1])*9 + int(x[0]) - 1)
    return out
def nm(t): return ("%d%s" % (t % 9 + 1, "mps"[t // 9])) if t < 27 else HONN[t - 27]
def perm_list(mu): return sorted(set(itertools.permutations(mu)))
def p4(mu):
    c = collections.Counter(mu)
    return 24 // math.prod(math.factorial(v) for v in c.values())

P = json.load(open(os.path.join(ROOT, "verify", "plan_k4_permfix.json"), encoding="utf-8"))
rows = P["plan"]
plancls = {frozenset(to_idx(r["W"])): [tuple(c) for c in r["codes"]] for r in rows}
log("载入底 plan: %d 类, %d 码" % (len(plancls), sum(len(v) for v in plancls.values())))
used = collections.defaultdict(list)
for W, codes in plancls.items():
    for c in codes: used[tuple(sorted(c))].append((W, c))
def take(mu, W):
    lst = used[mu]
    if len(lst) >= p4(mu): return None
    taken = {c for _, c in lst}
    for p in perm_list(mu):
        if p not in taken:
            lst.append((W, p)); return p
    return None
def has_mu(W, mu): return any(tuple(sorted(c)) == mu for c in plancls[W])
SU = {"m": 0, "p": 1, "s": 2, "z": 3}
def parse(ds, ci):
    off = (0, 9, 18, 27)[ci]; u = [0]*34
    for i, ch in enumerate(ds):
        if ch != "0": u[off+i] = int(ch)
    return tuple(u)
def contains(h, c):
    need = {}
    for t in c: need[t] = need.get(t, 0)+1
    return all(h[t] >= v for t, v in need.items())
def ksubs34(vec):
    tiles = [t for t, n in enumerate(vec) for _ in range(min(n, 4))]
    out = set()
    for combo in itertools.combinations_with_replacement(tiles, K):
        need = {}
        for x in combo: need[x] = need.get(x, 0)+1
        if all(vec[x] >= v for x, v in need.items()): out.add(combo)
    return out
G = json.load(open(os.path.join(ROOT, "data", "out", "global.json"), encoding="utf-8"))
FAMC = {}
def fam(S, m, chi):
    key = (tuple(S), m, chi)
    if key not in FAMC: FAMC[key] = TL.fam_list(S, m, chi)
    return FAMC[key]
def block_covered(A, inert, m, chi, codes):
    if any(contains(A, c) for c in codes): return True
    S = tuple(SU[x] for x in inert)
    fl = list(fam(S, m, chi))
    if not fl: fl = fam(S, m, True) + fam(S, m, False)
    for F in fl:
        hand = tuple(A[i] + F[i] for i in range(34))
        if not any(contains(hand, c) for c in codes): return False
    return True

# ① chiitoi
miss_chi = []; add_chi = 0
chiit = {int(k): [to_idx([d["z"]])[0] for d in v] for k, v in G["chiitoi_descriptors"].items()}
for mask, zs in sorted(chiit.items()):
    W = frozenset(t for t in range(34) if (mask >> t) & 1)
    if W not in plancls: continue
    for z in zs:
        tiles = [t for t in range(34) if t != z]
        gr = [tiles[0:7], tiles[7:14], tiles[14:21], tiles[21:27], tiles[27:33]]
        for g in gr:
            for a, b in itertools.combinations(g, 2):
                mu = tuple(sorted((z, a, a, b)))
                if has_mu(W, mu): continue
                p = take(mu, W)
                if p is None: miss_chi.append((sorted(W), nm(z), nm(a), nm(b)))
                else: plancls[W].append(p); add_chi += 1
log("① chiitoi: 追加 %d 条, 无法追加 %d" % (add_chi, len(miss_chi)))

# ② Type I
n_blk = 0; unc_blk = 0; fixed = 0; miss_blk = []
for row in G["classes"]:
    W = frozenset(to_idx(row["W"]))
    if W not in plancls: continue
    if any(s["kind"] == "kokushi" for s in row.get("sources", [])): continue
    for s in row.get("sources", []):
        if s["kind"] != "I": continue
        n_blk += 1
        ci = SU[s["cat"]]; A = parse(s["A"], ci); m = 13 - sum(A)
        chi = (s.get("z") is not None)
        if block_covered(A, s["inert"], m, chi, plancls[W]): continue
        unc_blk += 1
        done = False
        for mu in sorted(ksubs34(A), key=lambda x: len(used[x])):
            p = take(mu, W)
            if p is not None:
                plancls[W].append(p); fixed += 1; done = True; break
        if not done:
            miss_blk.append({"W": row["W"], "A": s["A"], "cat": s["cat"], "inert": s["inert"], "m": m})
log("② TypeI 块: %d, 未覆盖 %d, 已修 %d, 仍缺 %d" % (n_blk, unc_blk, fixed, len(miss_blk)))

allc = [c for W in plancls for c in plancls[W]]
empty = [sorted(W) for W in plancls if not plancls[W]]
over = [mu for mu, lst in used.items() if len(lst) > p4(mu)]
log("校验: 类 %d, 码 %d, 不同有序码 %d, 空类 %d, 超容量多重集 %d" % (
    len(plancls), len(allc), len(set(allc)), len(empty), len(over)))
out = {"k": 4, "n_classes": len(plancls), "n_codes": len(set(allc)),
       "plan": [{"W": sorted(W), "codes": [list(c) for c in plancls[W]]} for W in sorted(plancls, key=lambda S: sorted(S))]}
json.dump(out, open(os.path.join(OUT, "plan_k4_fixed.json"), "w", encoding="utf-8"), ensure_ascii=False)
rep = {"n_classes": len(plancls), "n_codes": len(set(allc)), "empty": empty[:10], "n_empty": len(empty),
       "over_capacity": len(over), "chi_added": add_chi, "n_chi_missing": len(miss_chi),
       "chi_missing": miss_chi[:20], "typeI_blocks": n_blk, "typeI_uncovered_before": unc_blk,
       "typeI_fixed": fixed, "n_typeI_missing": len(miss_blk), "typeI_missing": miss_blk[:30]}
json.dump(rep, open(os.path.join(OUT, "fix_k4_report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
log("写出 out/plan_k4_fixed.json + out/fix_k4_report.json")
