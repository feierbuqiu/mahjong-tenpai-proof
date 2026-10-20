# -*- coding: utf-8 -*-
"""pack_k4.py -- k=4 显式构造(按 lead 的验证模板改写: 阈值 3->4, 3-码->4-码, p3->p4)

覆盖单元: kind I 每个 X; kind II 的 am(|am|>=4) 或较大一侧 X / 两侧=2 时按对;
          |X|=1 单骑 -> 面子族; chiitoi -> (z,a,a,b) 对族; kokushi -> 手牌本体.
全局: 逐类容量感知贪心(只挑仍有空闲排列 p4(mu)=4!/prod(mult!) 的码) => 有序码天然不冲突.
输出 out/plan_k4.json / out/pack_k4_report.json
"""
import sys, os, json, collections, time, math, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import table_lib
from table_lib import CAT_BASE, MELDS_IN_CAT
K = 4
HONN = ["E", "S", "W", "N", "Haku", "Hatsu", "Chun"]
def nm(t): return ("%d%s" % (t % 9 + 1, "mps"[t // 9])) if t < 27 else HONN[t - 27]
def lift(c, X):
    v = [0]*34
    for i, x in enumerate(X): v[CAT_BASE[c]+i] = x
    return v
def perm_count(mu):
    c = collections.Counter(mu)
    return 24 // math.prod(math.factorial(v) for v in c.values())
T0 = time.time()
def log(*a): print("[%7.1fs]" % (time.time()-T0), *a, flush=True)

T = table_lib.build(); CLS = T["cls"]
log("table built: %d classes" % len(CLS))
G = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "out", "global.json"), encoding="utf-8"))
def ti(s): return 27 + HONN.index(s) if s in HONN else "mps".index(s[-1])*9 + int(s[0]) - 1
chiit = {int(m): sorted(set(ti(d["z"]) for d in lst)) for m, lst in G["chiitoi_descriptors"].items()}
log("chiitoi descriptors: %d classes" % len(chiit))

percls = {}; tanki = collections.defaultdict(set)
for W, blocks in CLS.items():
    reqs = set()
    for b in blocks:
        if b[0] == "I":
            c = b[1][0]
            for (cc, X) in table_lib.block_sources(T, b)[1] if False else table_lib.block_sources(T, b)[1]:
                V = lift(cc, X); s = sum(V)
                if s >= K: reqs.add(tuple(V))
                else:
                    z = next(t for t, x in enumerate(V) if x)
                    tanki[W].add((z, tuple(x for x in range(4) if x != cc)))
        elif b[0] == "II":
            am = b[5]; s1 = b[1][1]; s2 = b[2][1]
            if sum(am) >= K: reqs.add(tuple(am))
            elif max(s1, s2) >= K:
                for (c1, X1, c2, X2) in table_lib.block_sources(T, b)[1]:
                    V = lift(c1, X1) if s1 >= s2 else lift(c2, X2)
                    reqs.add(tuple(V))
            else:
                for (c1, X1, c2, X2) in table_lib.block_sources(T, b)[1]:
                    V1 = lift(c1, X1); V2 = lift(c2, X2)
                    reqs.add(tuple(V1[i]+V2[i] for i in range(34)))
        else:
            reqs.add(tuple(b[1]))
    percls[W] = [list(v) for v in reqs]
log("units: Σ=%d, tanki classes=%d, max/class=%d" % (
    sum(len(v) for v in percls.values()), len(tanki), max(len(v) for v in percls.values())))

usage = collections.Counter()
def take(mu):
    if usage[mu] < perm_count(mu):
        usage[mu] += 1; return True
    return False

# ---- chiitoi 族 (k=4): 前 3 个 z 用 33 条 (z,a,a,b)? -> 用 93 对族更稳; 这里统一用对族 ----
tiles33 = {z: [t for t in range(34) if t != z] for z in range(34)}
def chiit_family(z, variant=1):
    """(z,a,a,b) 对族: 33 张非 z 牌分 5 组(7,7,7,6,6)、组内连边 => 任意 6 对(6 种子)必含一条边 (alpha=5<6)."""
    gr = [tiles33[z][0:7], tiles33[z][7:14], tiles33[z][14:21], tiles33[z][21:27], tiles33[z][27:33]]
    return [tuple(sorted((z, a, a, b))) for g in gr for a, b in itertools.combinations(g, 2)]
chiit_codes = collections.defaultdict(list); chiit_missing = []
for mask, zs in chiit.items():
    for zi, z in enumerate(zs):
        fam = chiit_family(z, 1)
        got = [mu for mu in fam if take(mu)]
        chiit_codes[mask].extend(got)
        if len(got) != len(fam): chiit_missing.append((mask, nm(z), len(fam)-len(got)))
log("chiitoi families done, incomplete=%d" % len(chiit_missing))

# ---- tanki 族 (k=4): 刻子 (z,a,a,a) / 顺子 (z,a,b,c) ----
tanki_codes = collections.defaultdict(set); tanki_missing = []
for W, zs in tanki.items():
    for (z, inert) in zs:
        fam = set()
        for cat in inert:
            for M in MELDS_IN_CAT[cat]:
                tal = [t for t, x in enumerate(M) for _ in range(x)]
                fam.add(tuple(sorted((z, tal[0], tal[1], tal[2]))))
        for mu in fam:
            if take(mu): tanki_codes[W].add(mu)
        if len(tanki_codes[W] & fam) != len(fam):
            tanki_missing.append((sorted(W), nm(z), len(fam)-len(tanki_codes[W] & fam)))
log("tanki families: %d classes, incomplete=%d" % (len(tanki_codes), len(tanki_missing)))

# ---- 逐类容量感知贪心 (4-码) ----
def cover_class(reqs):
    n = len(reqs); cov = bytearray(n); out = []
    while True:
        left = [i for i in range(n) if not cov[i]]
        if not left: return out, 0
        cnt = collections.Counter()
        for i in left:
            tiles = []
            for t, c in enumerate(reqs[i]):
                for _ in range(min(c, 4)): tiles.append(t)
            m = len(tiles)
            for a in range(m):
                for b in range(a, m):
                    for c_ in range(b, m):
                        for d in range(c_, m):
                            cnt[(tiles[a], tiles[b], tiles[c_], tiles[d])] += 1
        picks = []
        for mu, _ in cnt.most_common():
            if usage[mu] >= perm_count(mu) or mu in out: continue
            picks.append(mu)
            if len(picks) >= 40: break
        if not picks: return out, len(left)
        pset = set(picks)
        for mu in picks:
            take(mu); out.append(mu)
        for i in left:
            tiles = []
            for t, c in enumerate(reqs[i]):
                for _ in range(min(c, 4)): tiles.append(t)
            m = len(tiles); hit = False
            for a in range(m):
                for b in range(a, m):
                    for c_ in range(b, m):
                        for d in range(c_, m):
                            if (tiles[a], tiles[b], tiles[c_], tiles[d]) in pset: hit = True; break
                        if hit: break
                    if hit: break
                if hit: break
            if hit: cov[i] = 1

order = sorted(percls.keys(), key=lambda W: -len(percls[W]))
fails = []; cover = {}
t0 = time.time()
for n_, W in enumerate(order):
    got, left = cover_class(percls[W])
    mask = sum(1 << t for t in W)
    allc = sorted(set(got) | set(tanki_codes.get(W, ())) | set(chiit_codes.get(mask, ())))
    cover[W] = allc
    if left: fails.append(([nm(t) for t in sorted(W)], len(percls[W]), left))
    if n_ % 250 == 0:
        log("  %d/%d codes=%d fails=%d" % (n_, len(order), sum(len(v) for v in cover.values()), len(fails)))
log("greedy done: codes=%d, fail classes=%d" % (sum(len(v) for v in cover.values()), len(fails)))
for f in fails[:10]: log("  FAIL %s" % (f,))

# ---- 分配排列 ----
used_perm = collections.Counter(); plan = []
for W in sorted(cover.keys(), key=lambda S: sorted(S)):
    codes = []
    for mu in cover[W]:
        ps = sorted(set(itertools.permutations(mu)))
        i = used_perm[mu]
        assert i < len(ps), (mu, i)
        used_perm[mu] += 1
        codes.append(list(ps[i]))
    plan.append({"W": sorted(W), "codes": codes})
allc = [tuple(c) for r in plan for c in r["codes"]]
rep = {"k": K, "n_classes": len(plan), "n_codes": len(allc), "distinct_codes": len(set(allc)),
       "empty_classes": sum(1 for r in plan if not r["codes"]), "fail_classes": len(fails),
       "fails": fails[:50], "chiit_missing": chiit_missing[:20], "tanki_missing": tanki_missing[:20],
       "max_multiset_use": max(usage.values()) if usage else 0}
json.dump({"k": K, "n_classes": len(plan), "n_codes": len(allc), "plan": plan},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "plan_k4.json"), "w", encoding="utf-8"), ensure_ascii=False)
json.dump(rep, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "pack_k4_report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
log("写出 out/plan_k4.json (codes=%d, empty=%d, fails=%d)" % (len(allc), rep["empty_classes"], len(fails)))
