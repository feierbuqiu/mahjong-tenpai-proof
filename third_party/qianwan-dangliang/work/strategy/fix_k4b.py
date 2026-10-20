# -*- coding: utf-8 -*-
"""fix_k4b.py -- 换码(displacement)修复: 在 plan_k4_fixed.json 上修 Type I 残余块 + chiitoi 缺失对.
算法(lead 指定): 块 C 需要 mu ⊆ A; 若 mu 饱和, 驱逐一个占用者 C' (把 C' 的 mu 换成 nu ⊆ am'(C'中所有含 mu 的单元的逐元素极小)), 再把 mu 给 C.
输出 out/plan_k4_v2.json + out/fix_k4b_report.json
"""
import sys, os, json, itertools, math, collections, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjlib import *
import table_lib as TL
K = 4
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out")
T0 = time.time()
def log(*a): print("[%7.1fs]" % (time.time()-T0), *a, flush=True)
HONN = ["E", "S", "W", "N", "Haku", "Hatsu", "Chun"]
HON = {n: 27+i for i, n in enumerate(HONN)}
def to_idx(w):
    o = []
    for x in w:
        if isinstance(x, int): o.append(x)
        elif x in HON: o.append(HON[x])
        else: o.append("mps".index(x[-1])*9 + int(x[0]) - 1)
    return o
def nm(t): return ("%d%s" % (t % 9 + 1, "mps"[t // 9])) if t < 27 else HONN[t - 27]
def pl(mu): return sorted(set(itertools.permutations(mu)))
def p4(mu):
    c = collections.Counter(mu)
    return 24 // math.prod(math.factorial(v) for v in c.values())
P = json.load(open(os.path.join(OUT, "plan_k4_fixed.json"), encoding="utf-8"))
plancls = {frozenset(r["W"]): [tuple(c) for c in r["codes"]] for r in P["plan"]}
used = collections.defaultdict(list)
for W, cs in plancls.items():
    for c in cs: used[tuple(sorted(c))].append((W, c))
log("载入: %d 类, %d 码" % (len(plancls), sum(len(v) for v in plancls.values())))
def take(mu, W):
    lst = used[mu]
    if len(lst) >= p4(mu): return None
    taken = {c for _, c in lst}
    for p in pl(mu):
        if p not in taken: lst.append((W, p)); return p
    return None
def drop(mu, W, c):
    used[mu].remove((W, c)); plancls[W].remove(c)
def contains(h, c):
    need = {}
    for t in c: need[t] = need.get(t, 0)+1
    return all(h[t] >= v for t, v in need.items())
SU = {"m": 0, "p": 1, "s": 2, "z": 3}
def parse(ds, ci):
    off = (0, 9, 18, 27)[ci]; u = [0]*34
    for i, ch in enumerate(ds):
        if ch != "0": u[off+i] = int(ch)
    return tuple(u)
def ksubs34(vec):
    tiles = [t for t, n in enumerate(vec) for _ in range(min(n, 4))]
    out = set()
    for combo in itertools.combinations_with_replacement(tiles, K):
        need = {}
        for x in combo: need[x] = need.get(x, 0)+1
        if all(vec[x] >= v for x, v in need.items()): out.add(combo)
    return out
T = TL.build(); CLS = T["cls"]
UC = {}
def units(W):
    if W in UC: return UC[W]
    reqs = set()
    for b in CLS[W]:
        k = b[0]
        if k == "I":
            c = b[1][0]
            for (cc, X) in TL.block_sources(T, b)[1]:
                v = [0]*34
                for i, x in enumerate(X): v[CAT_BASE[cc]+i] = x
                if sum(v) >= K: reqs.add(tuple(v))
        elif k == "II":
            am = b[5]
            if sum(am) >= K: reqs.add(tuple(am))
            else:
                for (c1, X1, c2, X2) in TL.block_sources(T, b)[1]:
                    v = [0]*34
                    if b[1][1] >= b[2][1]:
                        for i, x in enumerate(X1): v[CAT_BASE[c1]+i] = x
                    else:
                        for i, x in enumerate(X2): v[CAT_BASE[c2]+i] = x
                    reqs.add(tuple(v))
        else:
            reqs.add(tuple(b[1]))
    UC[W] = list(reqs); return UC[W]
def am_of(W, mu):
    us = [X for X in units(W) if contains(X, mu)]
    if not us: return None
    return tuple(min(u[i] for u in us) for i in range(34))

fixed_blocks = 0; miss_blocks = []
G = json.load(open(os.path.join(ROOT, "data", "out", "global.json"), encoding="utf-8"))
FAMC = {}
def fam(S, m, chi):
    key = (tuple(S), m, chi)
    if key not in FAMC: FAMC[key] = TL.fam_list(S, m, chi)
    return FAMC[key]
def block_covered(A, inert, m, codes):
    if any(contains(A, c) for c in codes): return True
    S = tuple(SU[x] for x in inert)
    fl = list(fam(S, m, False)) + list(fam(S, m, True))
    if not fl: return False
    for F in fl:
        hand = tuple(A[i]+F[i] for i in range(34))
        if not any(contains(hand, c) for c in codes): return False
    return True
def try_fix_block(W, A, inert, m):
    cands = sorted(ksubs34(A), key=lambda x: len(used[x]))
    free = [x for x in cands if len(used[x]) < p4(x)]
    if free:
        p = take(free[0], W)
        if p: plancls[W].append(p); return True
    for mu in cands:
        for (W2, c) in list(used[mu]):
            am = am_of(W2, mu)
            if am is None or sum(am) < K: continue
            nus = sorted([x for x in ksubs34(am) if x not in [tuple(sorted(y)) for y in plancls[W2]]],
                         key=lambda x: len(used[x]))
            for nu in nus:
                if len(used[nu]) >= p4(nu): continue
                drop(mu, W2, c)
                pnu = take(nu, W2)
                if pnu is None:
                    used[mu].append((W2, c)); plancls[W2].append(c); continue
                plancls[W2].append(pnu)
                pmu = take(mu, W)
                if pmu is None:
                    # 回滚
                    drop(nu, W2, pnu); used[mu].append((W2, c)); plancls[W2].append(c); continue
                plancls[W].append(pmu); return True
    return False

cnt = 0
for row in G["classes"]:
    W = frozenset(to_idx(row["W"]))
    if W not in plancls: continue
    if any(s["kind"] == "kokushi" for s in row.get("sources", [])): continue
    for s in row.get("sources", []):
        if s["kind"] != "I": continue
        ci = SU[s["cat"]]; A = parse(s["A"], ci); m = 13 - sum(A)
        if block_covered(A, s["inert"], m, plancls[W]): continue
        cnt += 1
        if try_fix_block(W, A, s["inert"], m):
            fixed_blocks += 1
        else:
            miss_blocks.append({"W": row["W"], "A": s["A"], "cat": s["cat"], "inert": s["inert"], "m": m})
log("TypeI 残余块: %d, 换码修复 %d, 仍缺 %d" % (cnt, fixed_blocks, len(miss_blocks)))

# chiitoi 缺失对
miss_chi = []; fix_chi = 0
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
                if any(tuple(sorted(c)) == mu for c in plancls[W]): continue
                p = take(mu, W)
                if p: plancls[W].append(p); fix_chi += 1; continue
                ok = False
                for (W2, c) in list(used[mu]):
                    am = am_of(W2, mu)
                    if am is None or sum(am) < K: continue
                    nus = sorted([x for x in ksubs34(am) if x not in [tuple(sorted(y)) for y in plancls[W2]]],
                                 key=lambda x: len(used[x]))
                    for nu in nus:
                        if len(used[nu]) >= p4(nu): continue
                        drop(mu, W2, c)
                        pnu = take(nu, W2)
                        if pnu is None:
                            used[mu].append((W2, c)); plancls[W2].append(c); continue
                        plancls[W2].append(pnu)
                        pmu = take(mu, W)
                        if pmu is None:
                            drop(nu, W2, pnu); used[mu].append((W2, c)); plancls[W2].append(c); continue
                        plancls[W].append(pmu); fix_chi += 1; ok = True; break
                    if ok: break
                if not ok: miss_chi.append((sorted(W), nm(z), nm(a), nm(b)))
log("chiitoi: 换码补 %d, 仍缺 %d" % (fix_chi, len(miss_chi)))
allc = [c for W in plancls for c in plancls[W]]
empty = [sorted(W) for W in plancls if not plancls[W]]
over = [mu for mu, lst in used.items() if len(lst) > p4(mu)]
log("校验: 类 %d, 码 %d, 不同 %d, 空类 %d, 超容量 %d, 最大用量 %d" % (
    len(plancls), len(allc), len(set(allc)), len(empty), len(over), max((len(v) for v in used.values()), default=0)))
json.dump({"k": 4, "n_classes": len(plancls), "n_codes": len(set(allc)),
           "plan": [{"W": sorted(W), "codes": [list(c) for c in plancls[W]]} for W in sorted(plancls, key=lambda S: sorted(S))]},
          open(os.path.join(OUT, "plan_k4_v2.json"), "w", encoding="utf-8"), ensure_ascii=False)
json.dump({"n_classes": len(plancls), "n_codes": len(set(allc)), "n_empty": len(empty),
           "over_capacity": len(over), "max_use": max((len(v) for v in used.values()), default=0),
           "typeI_uncovered_after": len(miss_blocks), "typeI_fixed": fixed_blocks,
           "chi_fixed": fix_chi, "chi_missing_after": len(miss_chi),
           "typeI_missing": miss_blocks[:40], "chi_missing": miss_chi[:40]},
          open(os.path.join(OUT, "fix_k4b_report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
log("写出 out/plan_k4_v2.json + out/fix_k4b_report.json")
