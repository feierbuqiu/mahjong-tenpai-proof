# -*- coding: utf-8 -*-
"""replace_list.py -- 产出饱和多重集的『占用者及其可替换性』清单.
基线: work/verify/plan_k4_final.json (只读, 不修改)
输出: work/strategy/out/replace_candidates.json
  { mu, p4, usage, need:[需要它的类W], users:[{W, code, am'(逐牌最小), n_candidates, nu, blocked, units(若 blocked)}] }
"""
import sys, os, json, itertools, math, collections, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjlib import *
import table_lib as TL
K = 4
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out")
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
def nm(t): return ("%d%s" % (t%9+1, "mps"[t//9])) if t < 27 else HONN[t-27]
def p4(mu):
    c = collections.Counter(mu); return 24 // math.prod(math.factorial(v) for v in c.values())
def contains(h, c):
    need = {}
    for t in c: need[t] = need.get(t,0)+1
    return all(h[t] >= v for t, v in need.items())
def ksubs34(vec):
    tiles = [t for t,n in enumerate(vec) for _ in range(min(n,4))]
    o = set()
    for combo in itertools.combinations_with_replacement(tiles, K):
        need = {}
        for x in combo: need[x] = need.get(x,0)+1
        if all(vec[x] >= v for x, v in need.items()): o.add(combo)
    return o
SU = {"m":0,"p":1,"s":2,"z":3}
def parse(ds, ci):
    off=(0,9,18,27)[ci]; u=[0]*34
    for i,ch in enumerate(ds):
        if ch != "0": u[off+i] = int(ch)
    return tuple(u)

P = json.load(open(os.path.join(ROOT, "verify", "plan_k4_final.json"), encoding="utf-8"))
rows = P["plan"] if isinstance(P, dict) and "plan" in P else P
plancls = {frozenset(to_idx(r["W"])): [tuple(c) for c in r["codes"]] for r in rows}
allc = [c for cs in plancls.values() for c in cs]
log("基线: %d 类, %d 码, 不同 %d" % (len(plancls), len(allc), len(set(allc))))
used = collections.defaultdict(list)
for W, cs in plancls.items():
    for c in cs: used[tuple(sorted(c))].append((W, c))
log("不同多重集: %d" % len(used))

T = TL.build(); CLS = T["cls"]
UC = {}
def units(W):
    if W in UC: return UC[W]
    reqs = set()
    for b in CLS[W]:
        k = b[0]
        if k == "I":
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

need = collections.defaultdict(set)
meta = {}
# (i) Type I 硬块: |A|=4 且类内无码 ⊆ A  (ksubs(A,4) 只有 A 本身)
G = json.load(open(os.path.join(ROOT, "data", "out", "global.json"), encoding="utf-8"))
n_hard = 0
for row in G["classes"]:
    W = frozenset(to_idx(row["W"]))
    if W not in plancls: continue
    if any(s["kind"] == "kokushi" for s in row.get("sources", [])): continue
    for s in row.get("sources", []):
        if s["kind"] != "I": continue
        ci = SU[s["cat"]]; A = parse(s["A"], ci)
        if sum(A) != K: continue
        if any(contains(A, c) for c in plancls[W]): continue
        mu = tuple(sorted(t for t, n in enumerate(A) for _ in range(n)))
        need[mu].add(W); meta.setdefault(mu, {"kind": "typeI"})
        n_hard += 1
log("Type I 硬块(唯一候选 mu=A 且类内无码 ⊆ A): %d" % n_hard)

# (ii) chiitoi: 97 个 (类,z) 描述子的 93 对
chiit = {int(k): [to_idx([d["z"]])[0] for d in v] for k, v in G["chiitoi_descriptors"].items()}
n_chi = 0; n_sat = 0
for mask, zs in sorted(chiit.items()):
    W = frozenset(t for t in range(34) if (mask >> t) & 1)
    if W not in plancls: continue
    for z in zs:
        n_chi += 1
        tiles = [t for t in range(34) if t != z]
        gr = [tiles[0:7], tiles[7:14], tiles[14:21], tiles[21:27], tiles[27:33]]
        own = {tuple(sorted(c)) for c in plancls[W]}
        for g in gr:
            for a, b in itertools.combinations(g, 2):
                mu = tuple(sorted((z, a, a, b)))
                if mu in own: continue
                if len(used[mu]) >= p4(mu):
                    need[mu].add(W); meta.setdefault(mu, {"kind": "chiitoi"}); n_sat += 1
log("chiitoi: 描述子 %d 个, 饱和且类内缺失的对: %d ; 待处理 mu 总数 %d" % (n_chi, n_sat, len(need)))

out = []
users_tot = 0; repl_ok = 0; blocked = 0; nu_missing = 0
for mu, needs in sorted(need.items(), key=lambda kv: -len(kv[1])):
    entry = {"mu": list(mu), "mu_name": [nm(t) for t in mu], "p4": p4(mu), "usage": len(used[mu]),
             "need": [sorted(W) for W in sorted(needs, key=lambda S: sorted(S))], "users": []}
    for (W2, c) in used[mu]:
        us = [X for X in units(W2) if contains(X, mu)]
        am = tuple(min(u[i] for u in us) for i in range(34)) if us else tuple([0]*34)
        own = {tuple(sorted(y)) for y in plancls[W2]}
        cands = []
        if sum(am) >= K:
            cands = [x for x in ksubs34(am) if x not in own and len(used[x]) < p4(x)]
        users_tot += 1
        e = {"W": sorted(W2), "code": list(c), "am": [x for x in am], "am_size": sum(am),
             "n_candidates": len(cands)}
        if cands:
            repl_ok += 1
            cands.sort(key=lambda x: len(used[x]))
            e["nu"] = list(cands[0]); e["nu_name"] = [nm(t) for t in cands[0]]
        else:
            blocked += 1
            e["blocked"] = True
            e["units"] = [[(nm(t), n) for t, n in enumerate(X) if n] for X in (us if us else units(W2))][:50]
        entry["users"].append(e)
    out.append(entry)
rep = {"baseline": "work/verify/plan_k4_final.json", "n_mu": len(out),
       "n_typeI_hard_blocks": n_hard, "n_chiitoi_saturated_pairs": n_sat,
       "n_user_entries": users_tot, "n_users_replaceable": repl_ok,
       "replaceable_ratio": (repl_ok/users_tot if users_tot else 0.0),
       "n_users_blocked": blocked}
json.dump(rep, open(os.path.join(OUT, "replace_stats.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump({"stats": rep, "entries": out}, open(os.path.join(OUT, "replace_candidates.json"), "w", encoding="utf-8"), ensure_ascii=False)
log("写出 out/replace_candidates.json ; %s" % json.dumps(rep, ensure_ascii=False))
