# -*- coding: utf-8 -*-
import sys, json, collections
sys.path.insert(0, r"D:\DSH\MJ2\work\strategy")
from mjlib import *
import table_lib as TL, strategy as SG
SG.K = 3
T = TL.build(); CLS = T["cls"]
W = frozenset([1,4,20,23,26])   # 2m,5m,3s,6s,9s
keys, cands, modes = SG.class_elements(T, W, CLS[W])
print("blocks:", len(CLS[W]), "modes:", modes)
for k in keys:
    v = k[2] if k[0] == "S" else k[1]
    nz = [(tile_name(i), n) for i, n in enumerate(v) if n]
    print(" key", k[0], "support", sorted({cat_of(i) for i, n in enumerate(v) if n}), "vec", nz, "|cands|", len(cands[keys.index(k)]))
core = [min((k[2] if k[0]=="S" else k[1])[i] for k in keys) for i in range(34)]
print("core sum:", sum(core))
for k in keys:
    v = k[2] if k[0] == "S" else k[1]
    ks = SG.ksubs(tuple(v))
    d = [m for m in ks if m[0]!=m[1] and m[1]!=m[2]]
    print("  元素 m-only? ", sorted({cat_of(i) for i,n in enumerate(v) if n}), "ksubs", len(ks), "distinct-subs", len(d))
