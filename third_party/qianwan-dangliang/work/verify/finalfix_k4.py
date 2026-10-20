#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""finalfix_k4.py <base plan.json>
步骤: (1) 删除废码(⊄ 该类任何手牌) (2) chiitoi 61 类: α≤5 五组二元族 (z,a,a,b), 不足则两组三元族 (z,a,b,c)
      (3) Type I 残余块: 通用码(⊆A)优先 + 补牌族贪心
输出 work/verify/plan_k4_final.json
"""
import json, sys, os, itertools, random, time, collections
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
CATS = {"m": (9, 0), "p": (9, 9), "s": (9, 18), "z": (7, 27)}
SU = {"m": 0, "p": 1, "s": 2, "z": 3}
def load_cache(name):
    d = np.load(os.path.join(HERE, "cache_w_%s.npz" % name))
    return d["hands"], d["wids"], json.load(open(os.path.join(HERE, "cache_w_%s.json" % name)))
def contains(h, c):
    need = {}
    for t in c: need[t] = need.get(t, 0) + 1
    return all(h[t] >= v for t, v in need.items())
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
            out.append(tuple(u))
    DEC[k] = out; return out
def parse(ds, ci):
    off = (0, 9, 18, 27)[ci]; u = [0] * 34
    for i, ch in enumerate(ds):
        if ch != "0": u[off + i] = int(ch)
    return u

base = sys.argv[1] if len(sys.argv) > 1 else "work/strategy/out/plan_k4_v2.json"
P = json.load(open(base, encoding="utf-8"))
rows = P["plan"]
plancls = {}
for r in rows:
    W = frozenset(to_idx(r["W"]))
    plancls.setdefault(W, []).extend(tuple(c) for c in r["codes"])
used = set()
for cs in plancls.values():
    for c in cs: used.add(c)
n0 = len(used)
t0 = time.time()
parr = {}
def perms(m):
    k = tuple(sorted(m))
    if k not in parr: parr[k] = sorted(set(itertools.permutations(k)))
    return parr[k]
def free_perm(m):
    for pm in perms(m):
        if pm not in used: return pm
    return None
def drop(mset_key):
    pass
# ---------- (1) 删除废码 ----------
removed = 0
for name, (K, off) in CATS.items():
    hands, wids, wlist = load_cache(name)
    for wid, Wl in enumerate(wlist):
        W = frozenset(Wl); cs = plancls.get(W)
        if not cs: continue
        idx = np.nonzero(wids == wid)[0]
        H = hands[idx]
        keep = []
        for c in cs:
            if any(t < off or t >= off + K for t in c): keep.append(c); continue
            need = np.zeros(K, dtype=np.int8)
            for t in c: need[t - off] += 1
            if (H >= need).all(axis=1).any(): keep.append(c)
            else:
                used.discard(c); removed += 1
        plancls[W] = keep
print("(1) 删除废码:", removed, " (%.0fs)" % (time.time() - t0), flush=True)
# ---------- (2) chiitoi 族 ----------
g = json.load(open("work/data/out/global.json", encoding="utf-8"))
descs = []
for key, lst in g["chiitoi_descriptors"].items():
    for d in lst:
        z = to_idx_one(d["z"])
        W = frozenset(set(to_idx(d["Wstd"])) | {z})
        descs.append((W, z))
tiles_all = list(range(34))
bin_ok = 0; tri_ok = 0; both_fail = []
for W, z in descs:
    if W not in plancls: continue
    pool = [t for t in tiles_all if t != z]
    done = False
    for attempt in range(15):
        rr = random.Random(hash((z, tuple(sorted(W)), attempt)) % (2 ** 31))
        sh = pool[:]; rr.shuffle(sh)
        parts = [sh[i::5] for i in range(5)]
        codes = []; ok = True
        for part in parts:
            for a, b in itertools.combinations(part, 2):
                cp = free_perm((z, a, a, b))
                if cp is None: ok = False; break
                codes.append(cp)
            if not ok: break
        if ok:
            for cp in codes: used.add(cp); plancls[W].append(cp)
            bin_ok += 1; done = True; break
    if done: continue
    # 三元族: 2 组 17/16
    for attempt in range(8):
        rr = random.Random(hash((z, tuple(sorted(W)), 999 + attempt)) % (2 ** 31))
        sh = pool[:]; rr.shuffle(sh)
        parts = [sh[:17], sh[17:]]
        codes = []; ok = True
        for part in parts:
            for tri in itertools.combinations(part, 3):
                cp = free_perm((z,) + tri)
                if cp is None: ok = False; break
                codes.append(cp)
            if not ok: break
        if ok:
            for cp in codes: used.add(cp); plancls[W].append(cp)
            tri_ok += 1; done = True; break
    if not done: both_fail.append({"W": [NM(t) for t in sorted(W)], "z": NM(z)})
print("(2) chiitoi: 二元族成功", bin_ok, "三元族成功", tri_ok, "二者皆失败", len(both_fail),
      " (%.0fs)" % (time.time() - t0), flush=True)
# ---------- (3) Type I 残余 ----------
rowsG = g["classes"]
blocks = unc = fixedA = 0; hard = []
def typeI_ok(A, inert, m, codes):
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
for row in rowsG:
    W = frozenset(to_idx(row["W"]))
    if W not in plancls: continue
    if any(s["kind"] == "kokushi" for s in row.get("sources", [])): continue
    codes = plancls[W]
    for s in row.get("sources", []):
        if s["kind"] != "I": continue
        blocks += 1
        ci = SU[s["cat"]]; A = parse(s["A"], ci); m = 13 - sum(A)
        if typeI_ok(A, s["inert"], m, codes): continue
        unc += 1
        Atiles = [i for i in range(34) for _ in range(A[i])]
        got = None
        for m4 in sorted(set(itertools.combinations_with_replacement(Atiles, 4))):
            cp = free_perm(m4)
            if cp is not None and contains(A, cp): got = cp; break
        if got is not None:
            plancls[W].append(got); used.add(got); fixedA += 1
        else:
            hard.append({"W": row["W"], "A": s["A"], "cat": s["cat"], "m": m})
print("(3) TypeI: blocks", blocks, "uncovered", unc, "修好", fixedA, "硬块", len(hard), " (%.0fs)" % (time.time() - t0), flush=True)
out_rows = [{"W": r["W"], "codes": [list(c) for c in plancls[frozenset(to_idx(r["W"]))]], "modes": r.get("modes", [])} for r in rows]
out = {"k": 4, "n_classes": len(out_rows), "n_codes": sum(len(r["codes"]) for r in out_rows), "plan": out_rows,
       "base": base, "finalfix": {"removed_waste": removed, "chiitoi_bin": bin_ok, "chiitoi_tri": tri_ok,
       "chiitoi_fail": both_fail, "typeI_uncovered_before": unc, "typeI_fixedA": fixedA,
       "typeI_hard": len(hard), "typeI_hard_all": hard, "added": len(used) - n0}}
json.dump(out, open(os.path.join(HERE, "plan_k4_final.json"), "w"), ensure_ascii=False)
print("TOTAL classes", len(out_rows), "codes", out["n_codes"], "added", len(used) - n0)
