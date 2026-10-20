# -*- coding: utf-8 -*-
"""fix_chiit_k4c.py -- chiitoi 覆盖用『三元族 (z,a,b,c)』（Lead）
理由：二元族 (z,a,a,b)/(a,a,b,b) 在底 plan 里已被大量占用（每 z 有 212~309 对饱和 ⇒ alpha>=6），
而三元码 (z,a,b,c) 只要 {a,b,c} ⊆ K 即可装进 {z}⊎2K。
把 33 张非 z 牌分成 2 组 (17,16)：任意 6 对集合 K 必有一组含 >=3 张 ⇒ 该组的三元组命中 K。
族大小 C(17,3)+C(16,3) = 680+560 = 1240 条/（类,z）。
"""
import sys, os, json, collections, math, itertools
HERE = os.path.dirname(os.path.abspath(__file__))
HONN = ["E","S","W","N","Haku","Hatsu","Chun"]
def ti(s): return 27 + HONN.index(s) if s in HONN else "mps".index(s[-1])*9 + int(s[0]) - 1
def nm(t): return ("%d%s" % (t % 9 + 1, "mps"[t // 9])) if t < 27 else HONN[t - 27]
def idx(x): return x if isinstance(x, int) else ti(x)
FACT = [math.factorial(i) for i in range(5)]
def p4(mu):
    c = collections.Counter(mu); return 24 // math.prod(FACT[v] for v in c.values())
P = json.load(open('work/strategy/out/plan_k4_v2.json', encoding='utf-8'))
rows = P["plan"]
key = lambda W: frozenset(idx(x) for x in W)
plancls = {key(r["W"]): [tuple(c) for c in r["codes"]] for r in rows}
G = json.load(open('work/data/out/global.json', encoding='utf-8'))
chiit = {int(m): sorted(set(ti(d['z']) for d in lst)) for m, lst in G['chiitoi_descriptors'].items()}
wmap = {}
for r in rows:
    m2 = 0
    for x in r["W"]: m2 |= 1 << idx(x)
    wmap[m2] = key(r["W"])
usage = collections.Counter(); used = collections.defaultdict(set)
for W, cs in plancls.items():
    for c in cs:
        mu = tuple(sorted(c)); usage[mu] += 1; used[mu].add(tuple(c))
added = 0; residual = []
for mask, zs in chiit.items():
    W = wmap.get(mask)
    if W is None: continue
    for z in zs:
        tiles = [x for x in range(34) if x != z]
        best = None
        for cut in range(14, 20):
            g1 = tiles[:cut]; g2 = tiles[cut:]
            fam = [tuple(sorted((z, a, b, c))) for g in (g1, g2) for a, b, c in itertools.combinations(g, 3)]
            miss = 0
            for mu in fam:
                ps = [pp for pp in set(itertools.permutations(mu)) if pp not in used[mu]]
                if usage[mu] + 0 >= p4(mu) or not ps: miss += 1
            if best is None or miss < best[0]:
                best = (miss, fam)
                if miss == 0: break
        miss, fam = best
        got = 0
        for mu in fam:
            if usage[mu] >= p4(mu): continue
            ps = [pp for pp in set(itertools.permutations(mu)) if pp not in used[mu]]
            if not ps: continue
            c = sorted(ps)[0]
            plancls[W].append(c); used[mu].add(c); usage[mu] += 1; got += 1
        added += got
        if miss: residual.append([[nm(x) for x in sorted(W)], nm(z), miss, got])
print("chiitoi(triple): added %d codes; residual (class,z): %d" % (added, len(residual)))
for x in residual[:10]: print("   ", x)
out_plan = [{"W": [nm(t) for t in sorted(W)], "codes": [list(c) for c in cs]} for W, cs in plancls.items()]
allc = [tuple(c) for r in out_plan for c in r["codes"]]
rep = {"n_classes": len(out_plan), "n_codes": len(allc), "distinct": len(set(allc)),
       "empty": sum(1 for r in out_plan if not r["codes"]),
       "over_cap": sum(1 for mu, n in usage.items() if n > p4(mu)),
       "chiit_added": added, "residual_class_z": len(residual)}
json.dump({"k": 4, "n_classes": len(out_plan), "n_codes": len(allc), "plan": out_plan},
          open(os.path.join(HERE, 'plan_k4_v3t.json'), 'w'))
json.dump({"report": rep, "residual": residual[:50]}, open(os.path.join(HERE, 'fix_chiit_report_c.json'), 'w'), ensure_ascii=False, indent=1)
print(rep)
