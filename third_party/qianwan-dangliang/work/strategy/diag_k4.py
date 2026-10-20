# -*- coding: utf-8 -*-
import json, os, sys, itertools, collections
sys.path.insert(0, r"D:\DSH\MJ2\work\strategy")
from math import factorial
def perm_count(m):
    d = 1
    for x in set(m): d *= factorial(m.count(x))
    return factorial(len(m))//d
P = json.load(open(r"D:\DSH\MJ2\work\strategy\out\plan_k4.json", encoding="utf-8"))
print("k=", P["k"], "classes=", P["n_classes"], "codes=", P["n_codes"])
use = collections.Counter(); ordcodes = collections.Counter()
share = 0
for pc in P["plan"]:
    for c in pc["codes"]:
        use[tuple(sorted(c))] += 1
        ordcodes[tuple(c)] += 1
over = [(m, c, perm_count(m)) for m, c in use.items() if c > perm_count(m)]
print("不同多重集:", len(use), " 超容量多重集:", len(over))
print("最大超容量 top10:", sorted(over, key=lambda x: -(x[1]-x[2]))[:10])
print("有序码复用(不同类用同一有序码):", sum(1 for c, n in ordcodes.items() if n > 1))
empty = [pc["W"] for pc in P["plan"] if not pc["codes"]]
print("空码类:", len(empty))
print("空码类样例:", empty[:9])
print("每类码数分布:", collections.Counter(len(pc["codes"]) for pc in P["plan"]).most_common(8))
