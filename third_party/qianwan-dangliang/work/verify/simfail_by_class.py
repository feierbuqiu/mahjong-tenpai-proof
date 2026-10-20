#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""simfail_by_class.py <plan.json> [n_sim] -- 把模拟失败手牌按类聚类, 并检查是否都落在
(61 个 chiitoi 类) ∪ (47 个 Type I 硬块所属类) 内."""
import json, sys, os, random, collections
from multiprocessing import Pool, cpu_count
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fastverify_k4 as F

def worker(arg):
    seed, n = arg
    rng = random.Random(seed)
    plan = F._G["plan"]; mat = F._G["mat"]; closed_W = F._G["closed_W"]
    from indep_core import CAP, KOKUSHI_IDX
    CATSx = ((9, 0), (9, 9), (9, 18), (7, 27))
    def rv(ci, n2):
        K, _ = CATSx[ci]; c = [0] * K
        for _ in range(n2):
            while True:
                x = rng.randrange(K)
                if c[x] < CAP: c[x] += 1; break
        return c
    fails = collections.Counter(); listening = 0
    for _ in range(n):
        t = rng.random(); h = [0] * 34
        if t < 0.3:
            ci = rng.randrange(4); n1 = rng.choice([1, 4, 7, 10, 13]); X = rv(ci, n1)
            for i, x in enumerate(X): h[CATSx[ci][1] + i] += x
            cats = [c for c in range(4) if c != ci]; rem = 13 - n1
            for ii, cj in enumerate(cats):
                left = len(cats) - ii - 1
                s = rng.choice([s for s in range(0, rem + 1, 3) if rem - s <= 12 * left and (s == 0 or F.dec_vecs(cj, s))])
                if s:
                    v = rng.choice(F.dec_vecs(cj, s))
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
                s = rng.choice([s for s in range(0, rem + 1, 3) if rem - s <= 12 * left and (s == 0 or F.dec_vecs(cj, s))])
                if s:
                    v = rng.choice(F.dec_vecs(cj, s))
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
        M = mat.get(W)
        if M is None or not (M <= h).all(axis=1).any():
            fails[tuple(sorted(W))] += 1
    return listening, fails

def main():
    plan = sys.argv[1] if len(sys.argv) > 1 else "work/verify/plan_k4_final.json"
    N = int(sys.argv[2]) if len(sys.argv) > 2 else 1_000_000
    np_ = min(cpu_count(), 12)
    per = N // np_
    with Pool(np_, initializer=F._init, initargs=(plan,)) as pool:
        res = pool.map(worker, [(5000 + i, per) for i in range(np_)])
    listening = sum(r[0] for r in res)
    tot = collections.Counter()
    for _, c in res: tot.update(c)
    nfail = sum(tot.values())
    # 61 个 chiitoi 类 + 47 硬块类
    g = json.load(open("work/data/out/global.json", encoding="utf-8"))
    chi = set()
    for key, lst in g["chiitoi_descriptors"].items():
        for d in lst:
            z = F.to_idx_one(d["z"]); chi.add(tuple(sorted(set(F.to_idx(d["Wstd"])) | {z})))
    P = json.load(open(plan, encoding="utf-8"))
    hard = set()
    for h in P.get("finalfix", {}).get("typeI_hard_all", []):
        hard.add(tuple(sorted(F.to_idx(h["W"]))))
    in_chi = sum(v for k, v in tot.items() if k in chi)
    in_hard = sum(v for k, v in tot.items() if k in hard)
    in_both = sum(v for k, v in tot.items() if k in chi or k in hard)
    out = {"plan": plan, "samples": N, "listening": listening, "fail_total": nfail,
           "fail_rate": round(nfail / max(1, listening), 4),
           "distinct_fail_classes": len(tot),
           "fail_in_chiitoi_classes": in_chi, "fail_in_hard_block_classes": in_hard,
           "fail_in_union": in_both, "fail_outside_union": nfail - in_both,
           "top_classes": [{"W": list(k), "fail": v} for k, v in tot.most_common(12)],
           "outside_examples": [list(k) for k, v in tot.most_common() if not (k in chi or k in hard)][:10]}
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "simfail_by_class.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "top_classes"}, ensure_ascii=False, indent=1)[:1500])
    print("top classes:", json.dumps(out["top_classes"][:8], ensure_ascii=False)[:600])

if __name__ == "__main__":
    main()
