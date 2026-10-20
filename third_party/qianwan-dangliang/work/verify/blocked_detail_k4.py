#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""blocked_detail_k4.py <plan.json> -- 报出 chiitoi 族的饱和明细与可释放容量"""
import json, sys, os, itertools, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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
P = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "work/strategy/out/plan_k4_v2.json", encoding="utf-8"))
rows = P["plan"]
plancls = {}
for r in rows:
    W = frozenset(to_idx(r["W"]))
    plancls.setdefault(W, []).extend(tuple(c) for c in r["codes"])
allc = [c for cs in plancls.values() for c in cs]
perm_used = collections.Counter(tuple(sorted(c)) for c in allc)
def cap(m): return len(set(itertools.permutations(tuple(sorted(m)))))
def free(m):
    m = tuple(sorted(m)); return cap(m) - perm_used.get(m, 0)
g = json.load(open("work/data/out/global.json", encoding="utf-8"))
descs = []
for key, lst in g["chiitoi_descriptors"].items():
    for d in lst:
        z = to_idx_one(d["z"]); W = frozenset(set(to_idx(d["Wstd"])) | {z})
        descs.append((W, z))
print("chiitoi 描述子:", len(descs))
summary = []
for W, z in descs:
    pool = [t for t in range(34) if t != z]
    sh = pool[:]           # 固定 5 组划分 (确定性)
    parts = [sh[i::5] for i in range(5)]
    need = [ (a, b) for part in parts for a, b in itertools.combinations(part, 2) ]
    sat = [ (a, b) for a, b in need if free((z, a, a, b)) == 0 ]
    summary.append({"W": [NM(t) for t in sorted(W)], "z": NM(z), "pairs_needed": len(need), "pairs_saturated": len(sat),
                    "sat_examples": [[NM(a), NM(b)] for a, b in sat[:3]]})
tot_sat = sum(s["pairs_saturated"] for s in summary)
print("需要 (z,a,a,b) 对总数:", sum(s["pairs_needed"] for s in summary), "其中饱和:", tot_sat)
print("完全无饱和的类数:", sum(1 for s in summary if s["pairs_saturated"] == 0))
for s in summary[:6]: print("   ", json.dumps(s, ensure_ascii=False)[:220])
json.dump(summary, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "blocked_chiitoi.json"), "w"), ensure_ascii=False, indent=1)
# 可释放容量: 对本门池里"被 4-码占用但类并不需要"的估计 —— 统计各类码数分布
per_class = collections.Counter(len(cs) for cs in plancls.values())
print("每类码数分布 (前8):", dict(sorted(per_class.items())[:8]))
print("总码数:", len(allc), "不同多重集:", len(perm_used),
      "仍有空排列的多重集:", sum(1 for m in perm_used if cap(m) > perm_used[m]))
