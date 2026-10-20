#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""waste_codes_exact.py <plan.json> -- 精确/半精确判定"浪费码", 并对齐两种定义:
  定义 A (analyst 可能用的): 码 μ 不是任何来源单元的"通用码"(即 μ ⊄ 任何一个 A / minA1+minA2)
  定义 B (verifier 定义, 真正不可用): μ ⊄ 该类的任何一手牌(A+F / X1+X2+F / kokushi / chiitoi)
输出: 两种口径的计数 + 定义B 的实例; 另做纯字牌 28 类/322 手交叉核对。
"""
import json, sys, os, random, itertools, time, collections
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from indep_core import compute_W, melds_only, melds_only_honor, gen_vectors
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
def parse(ds, ci):
    off = (0, 9, 18, 27)[ci]; u = [0] * 34
    for i, ch in enumerate(ds):
        if ch != "0": u[off + i] = int(ch)
    return u
SU = {"m": 0, "p": 1, "s": 2, "z": 3}
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
rows = P["plan"]
plancls = {}
for r in rows:
    W = frozenset(to_idx(r["W"]))
    plancls.setdefault(W, []).extend(tuple(c) for c in r["codes"])
g = json.load(open("work/data/out/global.json", encoding="utf-8"))
srcrec = {}
for row in g["classes"]:
    W = frozenset(to_idx(row["W"]))
    srcrec[W] = row.get("sources", [])
def contains(h, c):
    need = {}
    for t in c: need[t] = need.get(t, 0) + 1
    return all(h[t] >= v for t, v in need.items())
# ---------- 定义 A: 非通用码 ----------
t0 = time.time()
nonuni = 0; tot = 0
for W, cs in plancls.items():
    As = []
    for s in srcrec.get(W, []):
        if s["kind"] == "I":
            As.append(parse(s["A"], SU[s["cat"]]))
        elif s["kind"] == "II":
            v = [0] * 34
            for name in ("minA1", "minA2"):
                ds = s.get(name)
                if ds is None: continue
                ci = SU[s["cats"][0 if name == "minA1" else 1]]
                u = parse(ds, ci)
                for i, x in enumerate(u): v[i] += x
            As.append(v)
    for c in cs:
        tot += 1
        if not any(contains(A, c) for A in As):
            nonuni += 1
print("定义 A (非通用码 = 不 ⊆ 任何来源 A/minA):", nonuni, "/", tot, "(%.1f%%)" % (100.0 * nonuni / tot))
# ---------- 定义 B: 真正不可用 (抽样该类的多手牌 + 精确复核可疑者) ----------
rng = random.Random(7)
def sample_hands(W, k=250):
    hands = []
    for s in srcrec.get(W, []):
        if s["kind"] == "I":
            ci = SU[s["cat"]]; A = parse(s["A"], ci); m = 13 - sum(A)
            cats = [SU[x] for x in s["inert"]]
        elif s["kind"] == "II":
            cats = [SU[x] for x in s["inert"]]
            A = [0] * 34; m = None
            v1 = parse(s["minA1"], SU[s["cats"][0]]); v2 = parse(s["minA2"], SU[s["cats"][1]])
            for i, x in enumerate(v1): A[i] += x
            for i, x in enumerate(v2): A[i] += x
            m = 13 - sum(A)
        else:
            continue
        if m is None or m < 0: continue
        for _ in range(max(1, k // max(1, len(srcrec.get(W, []))))):
            F = [0] * 34; rem = m; ok = True
            for ii, cj in enumerate(cats):
                left = len(cats) - ii - 1
                opts = [s2 for s2 in range(0, rem + 1, 3) if rem - s2 <= 12 * left and (s2 == 0 or dec_vecs(cj, s2))]
                if not opts: ok = False; break
                s2 = rng.choice(opts)
                if s2:
                    v = rng.choice(dec_vecs(cj, s2))
                    for i, x in enumerate(v): F[i] += x
                rem -= s2
            if ok and rem == 0:
                hands.append([A[i] + F[i] for i in range(34)])
    # chiitoi / kokushi 补充
    for key, lst in g["chiitoi_descriptors"].items():
        for d in lst:
            z = to_idx_one(d["z"]); Wc = frozenset(set(to_idx(d["Wstd"])) | {z})
            if Wc == W:
                for _ in range(60):
                    Kk = rng.sample([t for t in range(34) if t != z], 6)
                    h = [0] * 34
                    for t in Kk: h[t] = 2
                    h[z] = 1
                    hands.append(h)
    return hands
susp = []; checked = 0
for W, cs in plancls.items():
    hands = sample_hands(W)
    if not hands: continue
    Hm = np.array(hands, dtype=np.int8)
    for c in cs:
        checked += 1
        cv = np.array([c.count(t) for t in range(34)], dtype=np.int8)
        if not (Hm >= cv).all(axis=1).any():
            susp.append((W, c))
print("定义 B 抽样(每类多手牌)后『可疑不可用』码:", len(susp), "/", checked, " (%.0fs)" % (time.time() - t0))
cnt = collections.Counter(W for W, _ in susp)
print("可疑码涉及的类数:", len(cnt), "| 最多的类:", [([NM(t) for t in sorted(W)], n) for W, n in cnt.most_common(3)])
for W, c in susp[:6]: print("   例:", [NM(t) for t in c], "-> 类", [NM(t) for t in sorted(W)])
json.dump({"plan": plan_path, "definition_A_nongeneric": nonuni, "total_codes": tot,
           "definition_B_suspected_unusable": len(susp),
           "examples": [[[NM(t) for t in c], [NM(t) for t in sorted(W)]] for W, c in susp[:40]]},
          open(os.path.join(HERE, "waste_codes_report.json"), "w"), ensure_ascii=False, indent=1)
# ---------- 纯字牌交叉核对 ----------
d = np.load(os.path.join(HERE, "cache_w_z.npz"))
hands = d["hands"]; wl = json.load(open(os.path.join(HERE, "cache_w_z.json")))
listen = 0; cls = set()
for i, h in enumerate(hands):
    if wl[d["wids"][i]]:
        listen += 1; cls.add(d["wids"][i])
print("纯字牌: 听牌手牌", listen, "类数", len(cls), "(期望 322 / 28)")
