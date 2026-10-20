#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fastverify_k4.py <plan.json> [n_sim] -- 多进程全套复核 (目标 < 1 分钟).
多进程 + initializer 载入只读数据; Type I 用 numpy 快路径(是否存在码 ⊆ A)后再 DFS;
chiitoi 精确判定; 单花色全量覆盖; 10^6 手结构化模拟。
"""
import json, sys, os, time, itertools, random
from multiprocessing import Pool, cpu_count
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
HON = {"E": 27, "S": 28, "W": 29, "N": 30, "Haku": 31, "Hatsu": 32, "Chun": 33}
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
CATS = {"m": (9, 0), "p": (9, 9), "s": (9, 18), "z": (7, 27)}
def parse(ds, ci):
    off = (0, 9, 18, 27)[ci]; u = [0] * 34
    for i, ch in enumerate(ds):
        if ch != "0": u[off + i] = int(ch)
    return u
def counts_of(c):
    u = [0] * 34
    for t in c: u[t] += 1
    return u
DEC = {}
def dec_vecs(ci, s):
    k = (ci, s)
    if k in DEC: return DEC[k]
    from indep_core import melds_only, melds_only_honor, gen_vectors
    K = (9, 9, 9, 7)[ci]; hon = ci == 3; off = (0, 9, 18, 27)[ci]
    out = []
    for v in gen_vectors(K, s):
        if (melds_only_honor(v) if hon else melds_only(v)):
            u = [0] * 34
            for i, x in enumerate(v):
                if x: u[off + i] = x
            out.append(tuple(u))
    DEC[k] = out; return out

_G = {}
def _init(plan_path):
    sys.path.insert(0, HERE)
    from indep_core import closed_form_W
    P = json.load(open(plan_path, encoding="utf-8"))
    rows = P["plan"]
    plan = {}
    for r in rows:
        W = frozenset(to_idx(r["W"]))
        plan.setdefault(W, []).extend(tuple(c) for c in r["codes"])
    _G["plan"] = plan
    _G["mat"] = {W: (np.array([counts_of(c) for c in cs], dtype=np.int8) if cs else np.zeros((0, 34), dtype=np.int8))
                 for W, cs in plan.items()}
    _G["closed_W"] = closed_form_W
    g = json.load(open("work/data/out/global.json", encoding="utf-8"))
    srcs = {}
    for row in g["classes"]:
        W = frozenset(to_idx(row["W"]))
        lst = []
        for s in row.get("sources", []):
            if s["kind"] == "I":
                ci = SU[s["cat"]]; A = parse(s["A"], ci)
                lst.append((tuple(A), tuple(SU[x] for x in s["inert"]), 13 - sum(A), s["cat"]))
        srcs[W] = lst
    _G["srcs"] = srcs
    caches = {}
    for name, (K, off) in CATS.items():
        d = np.load(os.path.join(HERE, "cache_w_%s.npz" % name))
        wl = [frozenset(x) for x in json.load(open(os.path.join(HERE, "cache_w_%s.json" % name)))]
        caches[name] = (d["hands"], d["wids"], wl, K, off)
    _G["caches"] = caches
    descs = []
    for key, lst in g["chiitoi_descriptors"].items():
        for d in lst:
            z = to_idx_one(d["z"]); W = frozenset(set(to_idx(d["Wstd"])) | {z})
            descs.append((W, z))
    _G["descs"] = descs
    _G["n_cls"] = len(plan)

# ---------- workers ----------
def w_typeI(ws):
    srcs = _G["srcs"]; mat = _G["mat"]
    blocks = 0; unc = []
    for W in ws:
        M = mat.get(W)
        if M is None or M.shape[0] == 0: M = None
        for (A, inert, m, cat) in srcs.get(W, []):
            blocks += 1
            Av = np.array(A, dtype=np.int8)
            if M is not None:
                sub = M[:, :] <= Av
                if sub.all(axis=1).any():
                    continue
            codes = _G["plan"].get(W, [])
            if _dfs_covered(A, inert, m, codes):
                continue
            unc.append({"W": sorted(W), "A": "".join(str(x) for x in A[(0 if cat in "mps" else 27):(9 if cat in "mps" else 34)]), "cat": cat, "m": m})
    return blocks, unc
_DFS = {}
def _dfs_covered(A, inert, m, codes):
    def contains(h, c):
        nh = {}
        for t in c: nh[t] = nh.get(t, 0) + 1
        for t, v in nh.items():
            if h[t] < v: return False
        return True
    if any(contains(A, c) for c in codes): return True
    def rec(i, rem, hand):
        for c in codes:
            if contains(hand, c): return True
        if i == len(inert): return rem != 0
        ci = inert[i]
        for s in range(0, rem + 1, 3):
            if (rem - s) > 12 * (len(inert) - i - 1): continue
            for v in dec_vecs(ci, s):
                h2 = list(hand)
                for t, x in enumerate(v): h2[t] += x
                if not rec(i + 1, rem - s, h2): return False
        return True
    return rec(0, m, list(A))
def w_chiitoi(chunk):
    plan = _G["plan"]; bad = []
    for W, z in chunk:
        codes = plan.get(W, [])
        if not codes: bad.append({"W": sorted(W), "z": z, "reason": "no-codes"}); continue
        ok, wit = _chi_ok(z, codes)
        if not ok: bad.append({"W": sorted(W), "z": z, "witness_K": wit})
    return bad
def _chi_ok(z, codes):
    """精确: 是否存在 6-子集 K (不含 z) 不含任何 P(c)=非z支撑集 => 未被覆盖.
    用 bitmask 分支: 取最低位 v, 分支"含 v / 不含 v", 含 v 时把与 chosen∪{v} 冲突的顶点剔除."""
    forb = []
    singles = 0
    for c in codes:
        if c.count(z) > 1: continue
        if any(c.count(t) > 2 for t in set(c) if t != z): continue
        m = 0
        for t in set(c):
            if t != z: m |= (1 << t)
        if m == 0: return True, None
        forb.append(m)
    for m in forb:
        if m & (m - 1) == 0: singles |= m
    allowed = 0
    for t in range(34):
        if t != z and not (singles >> t) & 1: allowed |= (1 << t)
    if bin(allowed).count("1") < 6: return True, None
    # 冲突: 含 v 后, u 与 (chosen ∪ {v}) 形成某个 P
    def conflicts(chosen_mask, v):
        bad = 0
        base = chosen_mask | (1 << v)
        for m in forb:
            need_extra = m & ~base
            if need_extra == 0: return None      # P ⊆ base => 该 P 已被包含 => 该组合非法(应由调用方保证不出现)
            if need_extra & (need_extra - 1) == 0:
                bad |= need_extra
        return bad
    # 不变式: chosen 内不含任何 P; cand 内每个 u 加入 chosen 都不会形成 P
    def rec(cand, chosen_mask, cnt):
        if cnt == 6: return True
        if bin(cand).count("1") < 6 - cnt: return False
        low = cand & -cand
        v = low.bit_length() - 1
        cand2 = cand & ~low
        if rec(cand2, chosen_mask, cnt): return True          # 不含 v
        new_chosen = chosen_mask | low                         # 含 v
        forbidden = 0
        for P in forb:
            rest = P & ~new_chosen
            if rest == 0:
                return False                                   # 某个 P 被完全包含 => 该分支非法
            if rest & (rest - 1) == 0:
                forbidden |= rest
        if rec(cand2 & ~forbidden, new_chosen, cnt + 1): return True
        return False
    return (not rec(allowed, 0, 0)), None
def w_su(ws):
    mat = _G["mat"]; res = []
    for name, (hands, wids, wl, K, off) in _G["caches"].items():
        for wid, W in enumerate(wl):
            if W not in ws: continue
            M = mat.get(W)
            idx = np.nonzero(wids == wid)[0]
            H = hands[idx]
            cov = np.zeros(len(idx), dtype=bool)
            if M is not None:
                for row in M:
                    if row[off:off + K].sum() == 0: continue
                    if row[off:off + K].sum() and not (row[:off].any() or row[off + K:].any()):
                        cov |= (H >= row[off:off + K]).all(axis=1)
            n = int((~cov).sum())
            if n: res.append({"cat": name, "W": sorted(W), "uncovered": n})
    return res
def w_sim(arg):
    seed, n = arg
    rng = random.Random(seed)
    plan = _G["plan"]; closed_W = _G["closed_W"]
    import itertools as it
    from indep_core import melds_only, melds_only_honor, gen_vectors, CAP, KOKUSHI_IDX
    CATSx = ((9, 0), (9, 9), (9, 18), (7, 27))
    def rv(ci, n2):
        K, _ = CATSx[ci]; c = [0] * K
        for _ in range(n2):
            while True:
                x = rng.randrange(K)
                if c[x] < CAP: c[x] += 1; break
        return c
    fails = 0; listening = 0; hits = set()
    for _ in range(n):
        t = rng.random(); h = [0] * 34
        if t < 0.3:
            ci = rng.randrange(4); n1 = rng.choice([1, 4, 7, 10, 13]); X = rv(ci, n1)
            for i, x in enumerate(X): h[CATSx[ci][1] + i] += x
            cats = [c for c in range(4) if c != ci]; rem = 13 - n1
            for ii, cj in enumerate(cats):
                left = len(cats) - ii - 1
                s = rng.choice([s for s in range(0, rem + 1, 3) if rem - s <= 12 * left and (s == 0 or dec_vecs(cj, s))])
                if s:
                    v = rng.choice(dec_vecs(cj, s))
                    for i, x in enumerate(v): h[i] += x
                rem -= s
        elif t < 0.75:
            c1, c2 = rng.sample(range(4), 2)
            n1 = rng.choice([2, 5, 8, 11]); n2 = rng.choice([2, 5, 8, 11])
            if n1 + n2 > 13: n1, n2 = 2, 2
            for cc, nn in ((c1, n1), (c2, n2)):
                X = rv(cc, nn)
                for i, x in enumerate(X): h[CATSx[cc][1] + i] += x
            cats = [c for c in range(4) if c not in (c1, c2)]; rem = 13 - n1 - n2
            for ii, cj in enumerate(cats):
                left = len(cats) - ii - 1
                s = rng.choice([s for s in range(0, rem + 1, 3) if rem - s <= 12 * left and (s == 0 or dec_vecs(cj, s))])
                if s:
                    v = rng.choice(dec_vecs(cj, s))
                    for i, x in enumerate(v): h[i] += x
                rem -= s
        elif t < 0.92:
            kinds = rng.sample(range(34), 7); z = rng.choice(kinds)
            for kk in kinds: h[kk] = 2
            h[z] = 1
        elif t < 0.96:
            ks = rng.sample(KOKUSHI_IDX, 12)
            for kk in ks: h[kk] = 1
            h[rng.choice(ks)] += 1
        else:
            for _ in range(13):
                while True:
                    x = rng.randrange(34)
                    if h[x] < CAP: h[x] += 1; break
        W = closed_W(h)
        if not W: continue
        listening += 1
        hits.add(W)
        cs = plan.get(W)
        if not cs:
            fails += 1; continue
        hh = np.array(h, dtype=np.int8)
        M = _G["mat"].get(W)
        if M is None or not (M <= hh).all(axis=1).any(): fails += 1
    return listening, len(hits), fails

def main():
    plan_path = sys.argv[1] if len(sys.argv) > 1 else "work/verify/plan_k4_final.json"
    N_SIM = int(sys.argv[2]) if len(sys.argv) > 2 else 1_000_000
    t0 = time.time()
    P = json.load(open(plan_path, encoding="utf-8"))
    rows = P["plan"]
    plancls = {}
    for r in rows: plancls.setdefault(frozenset(to_idx(r["W"])), []).extend(tuple(c) for c in r["codes"])
    allc = [c for cs in plancls.values() for c in cs]
    # 结构 (父进程)
    census = set(frozenset(x) for x in json.load(open(os.path.join(HERE, "census_strict.json"), encoding="utf-8")))
    struct = {"classes": len(plancls), "class_set_ok": set(plancls) == census,
              "empty_classes": sum(1 for cs in plancls.values() if not cs),
              "codes": len(allc), "ordered_unique": len(set(allc)) == len(allc),
              "code_len": sorted(set(len(c) for c in allc[:2000]))}
    nproc = min(cpu_count(), 12)
    ws = list(plancls.keys())
    k = max(1, len(ws) // (nproc * 16))
    chunks = [ws[i:i + k] for i in range(0, len(ws), k)]
    with Pool(nproc, initializer=_init, initargs=(plan_path,)) as pool:
        tA = time.time()
        resA = pool.map(w_typeI, chunks)
        tA = time.time() - tA
        tB = time.time()
        ds = json.load(open("work/data/out/global.json", encoding="utf-8"))
        descs = []
        for key, lst in ds["chiitoi_descriptors"].items():
            for d in lst:
                z = to_idx_one(d["z"]); W = frozenset(set(to_idx(d["Wstd"])) | {z})
                descs.append((W, z))
        kc = max(1, len(descs) // nproc + 1)
        resB = pool.map(w_chiitoi, [descs[i:i + kc] for i in range(0, len(descs), kc)])
        tB = time.time() - tB
        tC = time.time()
        per = N_SIM // nproc
        resC = pool.map(w_sim, [(1000 + i, per) for i in range(nproc)])
        tC = time.time() - tC
        tD = time.time()
        ks = max(1, len(chunks) // nproc + 1)
        resD = pool.map(w_su, chunks)
        tD = time.time() - tD
    blocks = sum(x[0] for x in resA); uncA = [u for x in resA for u in x[1]]
    chi_bad = [b for x in resB for b in x]
    listening = sum(x[0] for x in resC); hits = max(x[1] for x in resC); simf = sum(x[2] for x in resC)
    su_bad = [u for x in resD for u in x]
    out = {"plan": plan_path, "struct": struct, "typeI": {"blocks": blocks, "uncovered": len(uncA), "examples": uncA[:5]},
           "chiitoi": {"descriptors": len(descs), "fail": len(chi_bad), "examples": chi_bad[:5]},
           "sim": {"samples": N_SIM, "listening": listening, "classes_hit": hits, "fail": simf},
           "single_suit_uncovered": {"classes": len(su_bad), "hands": sum(u["uncovered"] for u in su_bad),
                                     "examples": su_bad[:5]},
           "timing": {"typeI_s": round(tA, 1), "chiitoi_s": round(tB, 1), "sim_s": round(tC, 1),
                      "su_s": round(tD, 1), "total_s": round(time.time() - t0, 1), "nproc": nproc}}
    json.dump(out, open(os.path.join(HERE, "fastverify_report.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1)[:2200])

if __name__ == "__main__":
    main()
