# -*- coding: utf-8 -*-
"""fix_chiit_k4.py -- 用『随机 5 组划分 + 93 对族』补全 k=4 plan 的 chiitoi 覆盖（Lead）
输入 work/strategy/out/plan_k4_v2.json，输出 work/recon/plan_k4_v3c.json
"""
import sys, os, json, collections, math, itertools, random
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
order = [r["W"] for r in rows]
G = json.load(open('work/data/out/global.json', encoding='utf-8'))
chiit = {int(m): sorted(set(ti(d['z']) for d in lst)) for m, lst in G['chiitoi_descriptors'].items()}
# usage / used permutations
usage = collections.Counter(); used = collections.defaultdict(set)
for W, cs in plancls.items():
    for c in cs:
        mu = tuple(sorted(c)); usage[mu] += 1; used[mu].add(tuple(c))
rng = random.Random(4242)
def partition(z):
    t = [x for x in range(34) if x != z]
    rng.shuffle(t)
    return [t[0:7], t[7:14], t[14:21], t[21:27], t[27:33]]
added = 0; miss_report = []
for mask, zs in chiit.items():
    # 找到对应的类
    W = None
    for r in rows:
        m2 = 0
        for x in r["W"]: m2 |= 1 << idx(x)
        if m2 == mask: W = key(r["W"]); break
    if W is None: continue
    for z in zs:
        best = None
        for trial in range(600):
            gr = partition(z)
            pairs = [tuple(sorted((z, a, a, b))) for g in gr for a, b in itertools.combinations(g, 2)]
            missing = [mu for mu in pairs if usage[mu] >= p4(mu)]
            if best is None or len(missing) < best[0]:
                best = (len(missing), pairs)
                if not missing: break
        missing_n, pairs = best
        got = 0
        for mu in pairs:
            if usage[mu] < p4(mu):
                ps = [pp for pp in set(itertools.permutations(mu)) if pp not in used[mu]]
                if not ps: continue
                c = sorted(ps)[0]
                plancls[W].append(c); used[mu].add(c); usage[mu] += 1; got += 1
        added += got
        if missing_n: miss_report.append([ [nm(x) for x in sorted(W)], nm(z), missing_n ])
print("chiitoi: added %d codes; (class,z) with residual misses: %d" % (added, len(miss_report)))
for x in miss_report[:10]: print("   ", x)
out_plan = []
for W, cs in plancls.items():
    out_plan.append({"W": [nm(t) for t in sorted(W)], "codes": [list(c) for c in cs]})
allc = [tuple(c) for r in out_plan for c in r["codes"]]
rep = {"n_classes": len(out_plan), "n_codes": len(allc), "distinct": len(set(allc)),
       "empty": sum(1 for r in out_plan if not r["codes"]),
       "over_cap": sum(1 for mu, n in usage.items() if n > p4(mu)),
       "chiit_added": added, "chiit_residual_pairs_desc": len(miss_report)}
json.dump({"k": 4, "n_classes": len(out_plan), "n_codes": len(allc), "plan": out_plan},
          open(os.path.join(HERE, 'plan_k4_v3c.json'), 'w'))
json.dump({"report": rep, "miss": miss_report[:50]}, open(os.path.join(HERE, 'fix_chiit_report.json'), 'w'), ensure_ascii=False, indent=1)
print(rep)
