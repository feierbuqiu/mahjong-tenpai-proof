# -*- coding: utf-8 -*-
"""work/lean/verify_l6.py -- Python 侧按**块级语义**全量复核 II 型 309,144 块 / 5,402,697 单元，
并把每批期望值写进 work/lean/ExpectedL6.lean（供 Lean native_decide 逐批验证）。

块级语义：对每个 (X1,X2)，先试「∃ 码 ⊆ X1⊎X2」（严格单码）；若失败，再对每个合法补牌 F
（inert 类别中的面子并集，张数 = 13-s1-s2）检查 ∃ 码 ⊆ X1⊎X2⊎F；全部 F 通过才算该单元通过。
"""
import sys, os, json, pickle, itertools, time, re
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "work", "strategy"))
sys.path.insert(0, os.path.join(ROOT, "work", "strategy", "out"))
import table_lib as TL

HON = ["E", "S", "W", "N", "Haku", "Hatsu", "Chun"]
HONI = {n: 27 + i for i, n in enumerate(HON)}
BASE = [0, 9, 18, 27]


def to_idx(x):
    if isinstance(x, int):
        return x
    if x in HONI:
        return HONI[x]
    return "mps".index(x[-1]) * 9 + int(x[0]) - 1


def key_enc(k):
    V, pd, odd, ot, a2, o2 = k
    mask = 0
    for t in V:
        mask |= 1 << t
    return (mask + (1 if pd else 0) * 2 ** 34 + odd * 2 ** 35 +
            (34 if ot is None else ot) * 2 ** 39 +
            (1 if a2 else 0) * 2 ** 45 + (1 if o2 else 0) * 2 ** 46)


def build_dec(idx):
    L = 7 if idx == 3 else 9
    units = []
    if idx < 3:
        for st in range(L - 2):
            v = [0] * L
            v[st] = v[st + 1] = v[st + 2] = 1
            units.append(tuple(v))
    for t in range(L):
        v = [0] * L
        v[t] = 3
        units.append(tuple(v))
    out = {}
    for s in range(0, 13, 3):
        res = set()

        def rec(i, left, acc):
            if left == 0:
                res.add(acc); return
            for j in range(i, len(units)):
                u = units[j]
                if all(acc[k] + u[k] <= 4 for k in range(L)):
                    rec(j, left - 3, tuple(acc[k] + u[k] for k in range(L)))
        rec(0, s, (0,) * L)
        out[s] = sorted(res)
    return out


_G = {}


def init(recs_path):
    src = open(os.path.join(ROOT, "lean", "Mj", "Data2.lean"), encoding="utf-8").read()
    m = re.search(r'def combos : List \(Nat × Nat × Nat × Nat\) := \[(.*?)\]', src, re.S)
    combos = [tuple(int(x) for x in t.split(",")) for t in re.findall(r'\((\d+,\s*\d+,\s*\d+,\s*\d+)\)', m.group(1))]
    recs = []
    for mm in re.finditer(r'^def blkChunk\d+ : List Nat := \[(.*?)\]$', src, re.M):
        recs += [int(x) for x in mm.group(1).split(",")]
    C = pickle.load(open(os.path.join(ROOT, "work", "strategy", "out", "table_cache.pkl"), "rb"))
    P = json.load(open(os.path.join(ROOT, "work", "verify", "plan_k4_FINAL.json"), encoding="utf-8"))
    order = []
    seen = set()
    for r in P["plan"]:
        W = frozenset(to_idx(x) for x in r["W"])
        if W not in seen:
            seen.add(W); order.append(W)
    plan = {}
    for r in P["plan"]:
        W = frozenset(to_idx(x) for x in r["W"])
        plan.setdefault(W, []).extend(tuple(c) for c in r["codes"])
    grp = {}
    for (c, s, k) in C["PROFII_D"]:
        grp.setdefault((c, s), []).append(k)
    for ks in grp.values():
        ks.sort(key=key_enc)
    _G.update(combos=combos, recs=recs, PII=C["PROFII_D"], grp=grp, order=order, plan=plan,
              dec=[build_dec(i) for i in range(4)])


def contains(A, code):
    cc = {}
    for t in code:
        cc[t] = cc.get(t, 0) + 1
    return all(A[t] >= v for t, v in cc.items())


def dfs_block(codes, A0, inert, rem):
    """block-level: 对每个合法 F 检查是否已有码 ⊆ A；A0 为 (X1,X2) 拼好的 34 向量"""
    if any(contains(A0, c) for c in codes):
        return True

    def rec(i, left, h):
        for c in codes:
            if contains(h, c):
                return True
        if i == len(inert):
            return left != 0
        ci = inert[i]
        maxrest = 12 * (len(inert) - i - 1)
        for s in range(0, left + 1, 3):
            if left - s > maxrest:
                continue
            for v in _G["dec"][ci].get(s, ()):
                h2 = list(h)
                for t, x in enumerate(v):
                    h2[BASE[ci] + t] += x
                if not rec(i + 1, left - s, h2):
                    return False
        return True
    return rec(0, rem, A0)


def batch_worker(args):
    lo, hi = args
    combos, recs, PII, grp, order, plan = (_G["combos"], _G["recs"], _G["PII"], _G["grp"],
                                           _G["order"], _G["plan"])
    nb = fb = nu = fu = 0
    t0 = time.time()
    for rec in recs[lo:hi]:
        classIdx = rec >> 25
        r1 = rec & ((1 << 25) - 1)
        comboIdx = r1 >> 18
        r2 = r1 & ((1 << 18) - 1)
        k1i = r2 >> 9
        k2i = r2 & 511
        c1, s1, c2, s2 = combos[comboIdx]
        W = order[classIdx]
        # 严格单码检查只需落在 c1/c2 内的码；块级 DFS 必须用**全部**码（F 在 inert 类别里）
        codesA = [c for c in plan[W] if all(((0 if t < 27 else 3) in (c1, c2)) for t in c)]
        codesAll = plan[W]
        xs1 = PII[(c1, s1, grp[(c1, s1)][k1i])][1]
        xs2 = PII[(c2, s2, grp[(c2, s2)][k2i])][1]
        m = 13 - s1 - s2
        inert = tuple(i for i in range(4) if i not in (c1, c2))
        bf = 0
        for X1 in xs1:
            for X2 in xs2:
                A = [0] * 34
                for i, v in enumerate(X1):
                    A[BASE[c1] + i] += v
                for i, v in enumerate(X2):
                    A[BASE[c2] + i] += v
                nu += 1
                if any(contains(A, c) for c in codesA):
                    continue
                if not dfs_block(codesAll, A, inert, m):
                    fu += 1; bf += 1
        nb += 1
        if bf:
            fb += 1
    return (lo, hi, nb, fb, nu, fu, round((time.time() - t0) * 1000))


if __name__ == "__main__":
    init(None)
    n = len(_G["recs"])
    B = 20000
    ranges = [(i, min(i + B, n)) for i in range(0, n, B)]
    print("blocks", n, "batches", len(ranges), flush=True)
    results = []
    t0 = time.time()
    with Pool(8, initializer=init, initargs=(None,)) as pool:
        for r in pool.imap_unordered(batch_worker, ranges):
            results.append(r)
            print("batch done", r, flush=True)
    results.sort()
    prog = os.path.join(ROOT, "work", "lean", "gen_data2_progress.jsonl")
    with open(prog, "w", encoding="utf-8") as f:
        for i, (lo, hi, nb, fb, nu, fu, ms) in enumerate(results):
            f.write(json.dumps({"batch": i, "blocks": nb, "failed_blocks": fb,
                                "units": nu, "failed_units": fu, "ms": ms,
                                "first_rec": lo, "semantics": "block-level (strict + DFS)"}) + "\n")
    tot = [sum(r[k] for r in results) for k in (2, 3, 4, 5)]
    print("TOTAL blocks=%d failed_blocks=%d units=%d failed_units=%d  (%.1fs)"
          % (tot[0], tot[1], tot[2], tot[3], time.time() - t0), flush=True)
    json.dump({"per_batch": [list(r) for r in results], "total": tot,
               "seconds": round(time.time() - t0, 1)},
              open(os.path.join(ROOT, "work", "lean", "gen_data2_totals.json"), "w"))
