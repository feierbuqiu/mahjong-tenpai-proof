# -*- coding: utf-8 -*-
import sys, collections, itertools
sys.path.insert(0, r"D:\DSH\MJ2\work\strategy")
from mjlib import *
import table_lib as TL, strategy as SG
SG.K = 3
T = TL.build(); CLS = T["cls"]
K = 3
def support(key):
    v = key[2] if key[0] == "S" else key[1]
    return {cat_of(i) for i, n in enumerate(v) if n}
def vec(key):
    return key[2] if key[0] == "S" else key[1]
INFO = {W: SG.class_elements(T, W, CLS[W]) for W in CLS}
W = frozenset([1,4,20,23,26])
keys, cands, modes = INFO[W]
els = [k for k in keys if support(k) == {0}]
print("els in m:", len(els))
core = [min(vec(k)[i] for k in els) for i in range(34)]
print("core sum:", sum(core))
els_v = [vec(k) for k in els]
cand = []
for v in els_v:
    d = [m for m in SG.ksubs(tuple(v)) if m[0]!=m[1] and m[1]!=m[2]]
    cand.append(d if d else list(SG.ksubs(tuple(v))))
ch, unc = SG.greedy_elems(els_v, cand, frozenset())
print("greedy chosen:", ch, "unc:", len(unc))
print("候选示例:", cand[0][:3])
