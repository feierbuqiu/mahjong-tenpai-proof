# -*- coding: utf-8 -*-
import sys, os, json, collections
sys.path.insert(0, r"D:\DSH\MJ2\work\strategy")
from mjlib import *
import table_lib as TL, strategy as SG
P = json.load(open(r"D:\DSH\MJ2\work\strategy\out\plan_k3.json", encoding="utf-8"))
empt = [pc for pc in P["plan"] if not pc["codes"]]
print("空码类:", len(empt), "样例:", [ [tile_name(t) for t in pc["W"]] for pc in empt[:6]])
T = TL.build(); CLS = T["cls"]
for pc in empt[:3]:
    W = frozenset(pc["W"])
    keys, cands, modes = SG.class_elements(T, W, CLS[W])
    sup = collections.Counter()
    for k in keys:
        v = k[2] if k[0] == "S" else k[1]
        sup[tuple(sorted({cat_of(i) for i,n in enumerate(v) if n}))] += 1
    print("类", [tile_name(t) for t in W], "块数", len(CLS[W]), "元素", len(keys), "支撑分布", dict(sup))
    print("  modes:", collections.Counter(m[0] for m in modes))
