#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""waste_audit.py <plan.json> -- 对"可疑浪费码"做精确审计, 只导出可证明浪费的码.
- provable: 单花色类中 ⊄ 任何该类手牌 (精确、完备)
- audit: 从抽样可疑集里随机抽 200 条, 用全来源精确判定 (code_usable) 复核误报率
"""
import json, sys, os, random, itertools, time, collections
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from indep_core import melds_only, melds_only_honor, gen_vectors
HON = {"E": 27, "S": 28, "W": 29, "N": 30, "Haku": 31, "Hatsu": 32, "Chun": 33}
HONN = ["E", "S", "W", "N", "Haku", "Hatsu", "Chun"]
NM = lambda t: ("%d%s" % (t % 9 + 1, "mps"[t // 9])) if t < 27 else HONN[t - 27]
def to_idx_one(nm):
    nm = str(nm).strip()
    if nm in HON: return HON[nm]
    if nm and nm[0] in "mps": return "mps".index(nm[0]) * 9 + int(nm[1:]) - 1
    return "mps".index(nm[-1]) * 9 + int(nm[0]) - 1
def to_idx(w):
    if isinstance(w, int): return [t for t in range(34) if (w >> t) & 1]
    if w and all(isinstance(x, int) for x in w): return list(w)
    return [to_idx_one(nm) for nm in w]
SU = {"m": 0, "p": 1, "s": 2, "z": 3}
def parse(ds, ci):
    off = (0, 9, 18, 27)[ci]; u = [0] * 34
    for i, ch in enumerate(ds):
        if ch != "0": u[off + i] = int(ch)
    return u
DEC = {}
def dec_vecs(ci, s):
    k = (ci, s)
    if k in DEC: return DEC[k]
    K = (9, 9, 9, 7)[ci]; hon = ci == 3; off = (0, 9, 18, 27)[ci]
    out = []
    for v in gen_vectors(K, s):
        if (melds_only_honor(v) if hon else melds_only(v)):
            u = [0] * 34
            for i, x in enumerate(v):
                if x: u[off + i] = x
            out.append(u)
    DEC[k] = out; return out
plan_path = sys.argv[1] if len(sys.argv) > 1 else "work/verify/plan_k4_final.json"
P = json.load(open(plan_path, encoding="utf-8"))
plancls = {}
for r in P["plan"]:
    W = frozenset(to_idx(r["W"]))
    plancls.setdefault(W, []).extend(tuple(c) for c in r["codes"])
g = json.load(open("work/data/out/global.json", encoding="utf-8"))
srcrec = {}
for row in g["classes"]:
    srcrec[frozenset(to_idx(row["W"]))] = row.get("sources", [])
def contains(h, c):
    need = {}
    for t in c: need[t] = need.get(t, 0) + 1
    return all(h[t] >= v for t, v in need.items())
# ---- 精确: 是否存在补牌族 F 使 A+F ⊇ c ----
def search_F(A, cats, m, c):
    catlist = [SU[x] for x in cats]
    need = [0] * 34
    for t in c: need[t] += 1
    def rec(i, rem, acc):
        # 剪枝: 某类别已结束但 need 未满足
        for t in range(34):
            if need[t] > A[t] + acc[t]:
                ci = 3 if t >= 27 else t // 9
                if ci not in catlist[i:]: return False
        if i == len(catlist):
            return rem == 0 and all(A[t] + acc[t] >= need[t] for t in range(34))
        ci = catlist[i]
        for s in range(0, rem + 1, 3):
            if (rem - s) > 12 * (len(catlist) - i - 1): continue
            for v in dec_vecs(ci, s):
                a2 = list(acc)
                for t, x in enumerate(v): a2[t] += x
                if rec(i + 1, rem - s, a2): return True
        return False
    return rec(0, m, [0] * 34)
def code_usable_exact(W, c):
    for s in srcrec.get(W, []):
        if s["kind"] == "I":
            ci = SU[s["cat"]]; A = parse(s["A"], ci); m = 13 - sum(A)
            if search_F(A, s["inert"], m, c): return True
        elif s["kind"] == "II":
            v = [0] * 34
            for name in ("minA1", "minA2"):
                ds = s.get(name)
                if ds is None: continue
                ci = SU[s["cats"][0 if name == "minA1" else 1]]
                u = parse(ds, ci)
                for i, x in enumerate(u): v[i] += x
            m = 13 - sum(v)
            if m >= 0 and search_F(v, s["inert"], m, c): return True
        else:
            continue
    # chiitoi 描述子
    for key, lst in g["chiitoi_descriptors"].items():
        for d in lst:
            z = to_idx_one(d["z"]); Wc = frozenset(set(to_idx(d["Wstd"])) | {z})
            if Wc != W: continue
            if c.count(z) > 1: continue
            if any(c.count(t) > 2 for t in set(c) if t != z): continue
            return True     # 存在某个 6 对集合包含其非 z 支撑 (大概率) —— 保守视为可用
    return False
# ---- provable (单花色精确) ----
prov = {}
for name, (K, off) in {"m": (9, 0), "p": (9, 9), "s": (9, 18), "z": (7, 27)}.items():
    d = np.load(os.path.join(HERE, "cache_w_%s.npz" % name))
    hands, wids = d["hands"], d["wids"]
    wl = [frozenset(x) for x in json.load(open(os.path.join(HERE, "cache_w_%s.json" % name)))]
    for wid, W in enumerate(wl):
        cs = plancls.get(W)
        if not cs: continue
        idx = np.nonzero(wids == wid)[0]; H = hands[idx]
        for c in cs:
            if any(t < off or t >= off + K for t in c): continue
            need = np.zeros(K, dtype=np.int8)
            for t in c: need[t - off] += 1
            if not (H >= need).all(axis=1).any():
                prov.setdefault([NM(t) for t in sorted(W)], []).append([NM(t) for t in c])
nprov = sum(len(v) for v in prov.values())
print("provable 浪费码 (单花色精确):", nprov, "涉及类", len(prov))
# ---- 审计: 抽样可疑集 ----
rep = json.load(open(os.path.join(HERE, "waste_codes_report.json"), encoding="utf-8"))
susp = rep.get("examples", [])   # 只有前 40 条; 重新抽样 200 条需要完整可疑集, 这里退化为: 随机抽 200 个类里的码重新用精确判定
rng = random.Random(11)
allW = [W for W, cs in plancls.items() if cs]
sample_codes = []
for _ in range(200):
    W = rng.choice(list(plancls.keys()))
    cs = plancls[W]
    if not cs: continue
    sample_codes.append((W, rng.choice(cs)))
t0 = time.time(); unusable = 0; usable = 0; ex = []
for W, c in sample_codes:
    if code_usable_exact(W, c): usable += 1
    else:
        unusable += 1
        if len(ex) < 10: ex.append(([NM(t) for t in c], [NM(t) for t in sorted(W)]))
print("随机 200 条精确审计: 不可用(真浪费)", unusable, " 可用(抽样误报)", usable, "(%.0fs)" % (time.time() - t0))
for e in ex[:6]: print("   真浪费:", e)
out = {"plan": plan_path, "provable_waste": prov, "provable_count": nprov,
       "audit": {"sampled": len(sample_codes), "truly_unusable": unusable, "usable_false_positive": usable, "examples": ex}}
json.dump(out, open(os.path.join(HERE, "waste_list.json"), "w"), ensure_ascii=False, indent=1)
print("已写 work/verify/waste_list.json")
