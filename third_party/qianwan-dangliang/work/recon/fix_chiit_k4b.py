# -*- coding: utf-8 -*-
"""fix_chiit_k4b.py -- chiitoi 覆盖：直接用『全部仍有空闲的 (z,a,a,b) 对』构族（Lead）
族 P 覆盖完备 <=> 饱和对构成的图无 6-团（即 free 对图的独立数 <= 5）。
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

def max_clique_size(adj, verts):
    best = [0]
    def bk(cand, cur):
        if not cand:
            if cur > best[0]: best[0] = cur
            return
        if cur + len(cand) <= best[0]: return
        for i, v in enumerate(cand):
            if cur + len(cand) - i <= best[0]: return
            bk([u for u in cand[i+1:] if u in adj[v]], cur+1)
    bk(sorted(verts), 0)
    return best[0]

added = 0; residual = []
for mask, zs in chiit.items():
    W = wmap.get(mask)
    if W is None: continue
    for z in zs:
        tiles = [x for x in range(34) if x != z]
        allp = list(itertools.combinations(tiles, 2))
        free = []; sat = []
        for (a, b) in allp:
            mu1 = tuple(sorted((z, a, a, b))); mu2 = tuple(sorted((a, a, b, b)))
            ok = (usage[mu1] < p4(mu1)) or (usage[mu2] < p4(mu2))
            (free if ok else sat).append((a, b))
        adj = collections.defaultdict(set)
        for (a, b) in sat:
            adj[a].add(b); adj[b].add(a)
        mc = max_clique_size(adj, set(tiles))
        if mc >= 6:
            residual.append([[nm(x) for x in sorted(W)], nm(z), len(sat), mc])
            continue
        got = 0
        for (a, b) in free:
            done = False
            for mu in (tuple(sorted((z, a, a, b))), tuple(sorted((a, a, b, b)))):
                if usage[mu] >= p4(mu): continue
                ps = [pp for pp in set(itertools.permutations(mu)) if pp not in used[mu]]
                if not ps: continue
                c = sorted(ps)[0]
                plancls[W].append(c); used[mu].add(c); usage[mu] += 1; got += 1; done = True
                break
            if not done: print("   !! pair (%s,%s) unexpectedly saturated" % (nm(a), nm(b)))
        added += got
print("chiitoi: added %d codes; (class,z) with alpha>=6 residual: %d" % (added, len(residual)))
for x in residual[:10]: print("   ", x)
out_plan = [{"W": [nm(t) for t in sorted(W)], "codes": [list(c) for c in cs]} for W, cs in plancls.items()]
allc = [tuple(c) for r in out_plan for c in r["codes"]]
rep = {"n_classes": len(out_plan), "n_codes": len(allc), "distinct": len(set(allc)),
       "empty": sum(1 for r in out_plan if not r["codes"]),
       "over_cap": sum(1 for mu, n in usage.items() if n > p4(mu)),
       "chiit_added": added, "residual_class_z": len(residual)}
json.dump({"k": 4, "n_classes": len(out_plan), "n_codes": len(allc), "plan": out_plan},
          open(os.path.join(HERE, 'plan_k4_v3c.json'), 'w'))
json.dump({"report": rep, "residual": residual[:50]}, open(os.path.join(HERE, 'fix_chiit_report_b.json'), 'w'), ensure_ascii=False, indent=1)
print(rep)
