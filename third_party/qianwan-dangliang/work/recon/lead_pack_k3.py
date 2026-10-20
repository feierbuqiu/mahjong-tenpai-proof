# -*- coding: utf-8 -*-
"""lead_pack_k3.py -- Lead 的 k=3 显式构造（独立于 designer 的路径）
输出：work/recon/plan_k3_lead.json, work/recon/k3_lead_report.json

覆盖模型（保守/充分；核心引理：码 c ⊆ 活性部 A ⇒ c ⊆ 手牌 A⊎F）：
  kind I  : 每个 X（活性向量）一个单元，码 c ⊆ X；|X|=1（单骑）改用面子族
            （对 inert 花色每个面子 M：刻子 aaa -> (z,a,a)，顺子 abc -> (z,a,a+1)）
  kind II : |am|>=3 时整块一条码 ⊆ am（am 为两侧逐元素极小之和）；
            否则取较大一侧做侧覆盖（c ⊆ X1 ⇒ c ⊆ X1⊎X2⊎F）；两侧皆 2 张时按对展开
  kokushi : 单元 = 国士手牌本体
  chiitoi : 手牌 {z}⊎2K (|K|=6)：族 {(z,a,a): a≠z} 全覆盖（取 a∈K）；
            同一 z 超过 3 个类时用 5 组(7,7,7,6,6)鸽笼对族（93 对，α=5<6）
全局：逐类容量感知贪心（只挑仍有空闲排列 p(μ) 的码）⇒ 有序码天然全局不冲突。
"""
import sys, os, json, collections, time, math, itertools
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'strategy'))
import table_lib
from table_lib import CAT_BASE, MELDS_IN_CAT

HONN = ["E", "S", "W", "N", "Haku", "Hatsu", "Chun"]
def nm(t): return ("%d%s" % (t % 9 + 1, "mps"[t // 9])) if t < 27 else HONN[t - 27]
def lift(c, X):
    v = [0] * 34
    for i, x in enumerate(X): v[CAT_BASE[c] + i] = x
    return v
def perm_count(mu):
    c = collections.Counter(mu)
    return 6 // math.prod(math.factorial(v) for v in c.values())

print("building table ...", flush=True); t0 = time.time()
T = table_lib.build(); CLS = T['cls']
print("table %.1fs, %d classes" % (time.time() - t0, len(CLS)), flush=True)
G = json.load(open(os.path.join(HERE, '..', 'data', 'out', 'global.json'), encoding='utf-8'))
def ti(s): return 27 + HONN.index(s) if s in HONN else "mps".index(s[-1]) * 9 + int(s[0]) - 1
chiit = {int(m): sorted(set(ti(d['z']) for d in lst)) for m, lst in G['chiitoi_descriptors'].items()}

print("building units ...", flush=True); t0 = time.time()
percls = {}                              # W -> list[list[int]] 34 向量
tanki = collections.defaultdict(set)     # W -> set of (z, inert_cats)
for W, blocks in CLS.items():
    reqs = set()
    for b in blocks:
        if b[0] == 'I':
            c = b[1][0]; inert = tuple(x for x in range(4) if x != c)
            for (cc, X) in table_lib.block_sources(T, b)[1]:
                V = lift(cc, X); s = sum(V)
                if s >= 3: reqs.add(tuple(V))
                else:
                    z = next(t for t, x in enumerate(V) if x)
                    tanki[W].add((z, inert))
        elif b[0] == 'II':
            am = b[5]; s1 = b[1][1]; s2 = b[2][1]
            if sum(am) >= 3: reqs.add(tuple(am))
            elif max(s1, s2) >= 3:
                for (c1, X1, c2, X2) in table_lib.block_sources(T, b)[1]:
                    V = lift(c1, X1) if s1 >= s2 else lift(c2, X2)
                    reqs.add(tuple(V))
            else:
                for (c1, X1, c2, X2) in table_lib.block_sources(T, b)[1]:
                    V1 = lift(c1, X1); V2 = lift(c2, X2)
                    reqs.add(tuple(V1[i] + V2[i] for i in range(34)))
        else:
            reqs.add(tuple(b[1]))
    percls[W] = [list(v) for v in reqs]
print("units %.1fs total %d; tanki classes %d" % (time.time() - t0, sum(len(v) for v in percls.values()), len(tanki)), flush=True)

usage = collections.Counter()
cover = {}
def take(mu):
    if usage[mu] < perm_count(mu):
        usage[mu] += 1; return True
    return False

# ---- chiitoi 族 ----
chiit_codes = collections.defaultdict(list); chiit_missing = []
z_users = collections.defaultdict(list)
for mask, zs in chiit.items():
    for z in zs: z_users[z].append(mask)
for z in sorted(z_users):
    for idx, mask in enumerate(z_users[z]):
        if idx < 3:
            fam = [tuple(sorted((z, a, a))) for a in range(34) if a != z]
        else:
            tiles = [t for t in range(34) if t != z]
            gr = [tiles[0:7], tiles[7:14], tiles[14:21], tiles[21:27], tiles[27:33]]
            fam = [tuple(sorted((z, a, b))) for g in gr for a, b in itertools.combinations(g, 2)]
        got = [mu for mu in fam if take(mu)]
        chiit_codes[mask].extend(got)
        if len(got) != len(fam): chiit_missing.append((mask, z, len(fam) - len(got)))
print("chiitoi families %d, incomplete %d" % (sum(len(v) for v in z_users.values()), len(chiit_missing)), flush=True)

# ---- tanki 族 ----
tanki_codes = collections.defaultdict(set); tanki_missing = []
for W, zs in tanki.items():
    for (z, inert) in zs:
        fam = set()
        for cat in inert:
            for M in MELDS_IN_CAT[cat]:
                tal = [t for t, x in enumerate(M) for _ in range(x)]
                fam.add(tuple(sorted((z, tal[0], tal[1]))))
        for mu in fam:
            if take(mu): tanki_codes[W].add(mu)
        if len(tanki_codes[W] & fam) != len(fam):
            tanki_missing.append((sorted(W), nm(z), len(fam) - len(tanki_codes[W] & fam)))
print("tanki families %d, incomplete %d" % (len(tanki_codes), len(tanki_missing)), flush=True)
for x in tanki_missing[:5]: print("   tanki missing", x, flush=True)

# ---- 逐类贪心 ----
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
                    for c_ in range(b, m): cnt[(tiles[a], tiles[b], tiles[c_])] += 1
        picks = []
        for mu, _ in cnt.most_common():
            if usage[mu] >= perm_count(mu) or mu in out: continue
            picks.append(mu)
            if len(picks) >= 30: break
        if not picks: return out, len(left)
        pset = set(picks)
        for mu in picks:
            if take(mu): out.append(mu)
        for i in left:
            tiles = []
            for t, c in enumerate(reqs[i]):
                for _ in range(min(c, 4)): tiles.append(t)
            m = len(tiles); hit = False
            for a in range(m):
                for b in range(a, m):
                    for c_ in range(b, m):
                        if (tiles[a], tiles[b], tiles[c_]) in pset: hit = True; break
                    if hit: break
                if hit: break
            if hit: cov[i] = 1

order = sorted(percls.keys(), key=lambda W: -len(percls[W]))
t0 = time.time(); fails = []
for n_, W in enumerate(order):
    got, left = cover_class(percls[W])
    mask = 0
    for t in W: mask |= 1 << t
    allc = sorted(set(got) | set(tanki_codes.get(W, ())) | set(chiit_codes.get(mask, ())))
    cover[W] = allc
    if left: fails.append(([nm(t) for t in sorted(W)], len(percls[W]), left))
    if n_ % 250 == 0:
        print("  %d/%d %.0fs codes=%d fails=%d" % (n_, len(order), time.time() - t0, sum(len(v) for v in cover.values()), len(fails)), flush=True)
print("greedy %.1fs; codes %d; fail classes %d" % (time.time() - t0, sum(len(v) for v in cover.values()), len(fails)), flush=True)
for f in fails[:12]: print("  FAIL", f, flush=True)

# ---- 分配排列，输出 plan ----
used_perm = collections.Counter()
plan = []
for W in sorted(cover.keys(), key=lambda S: sorted(S)):
    codes = []
    for mu in cover[W]:
        ps = sorted(set(itertools.permutations(mu)))
        i = used_perm[mu]; assert i < len(ps), mu
        used_perm[mu] += 1
        codes.append(list(ps[i]))
    plan.append({"W": [nm(t) for t in sorted(W)], "codes": codes})
allcodes = [tuple(c) for r in plan for c in r["codes"]]
rep = {"k": 3, "n_classes": len(plan), "n_codes": len(allcodes),
       "distinct_codes": len(set(allcodes)), "empty_classes": sum(1 for r in plan if not r["codes"]),
       "fail_classes": len(fails), "fails": fails[:50],
       "chiit_missing": chiit_missing[:20], "tanki_missing": tanki_missing[:20],
       "max_multiset_use": max(usage.values()) if usage else 0}
out = {"k": 3, "n_classes": len(plan), "n_codes": len(allcodes), "plan": plan}
json.dump(out, open(os.path.join(HERE, 'plan_k3_lead.json'), 'w'))
json.dump(rep, open(os.path.join(HERE, 'k3_lead_report.json'), 'w'), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in rep.items() if k not in ('fails',)}, ensure_ascii=False), flush=True)
