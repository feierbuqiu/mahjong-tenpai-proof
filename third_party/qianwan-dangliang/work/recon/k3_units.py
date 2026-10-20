# -*- coding: utf-8 -*-
"""k3_units.py -- k=3 装包单元统计（Lead）"""
import sys, os, collections, pickle, time
sys.path.insert(0, 'work/strategy')
import table_lib
from table_lib import CAT_BASE, CAT_LEN
t0 = time.time()
T = table_lib.build()
print("build %.1fs, classes %d" % (time.time()-t0, len(T['cls'])), flush=True)
CLS = T['cls']

def lift(c, X):
    v = [0]*34
    for i, x in enumerate(X): v[CAT_BASE[c]+i] = x
    return v

stats = collections.Counter()
unit_counts = []
big = []
pair_expand = 0
t0 = time.time()
for W, blocks in CLS.items():
    units = []
    for b in blocks:
        kind = b[0]
        if kind == 'I':
            src = table_lib.block_sources(T, b)
            assert src[0] == 'xset'
            for (c, X) in src[1]:
                V = lift(c, X); s = sum(V)
                if s >= 3: units.append(('req', V))
                else: units.append(('tanki', c, s))
        elif kind == 'II':
            am = b[5]
            if sum(am) >= 3:
                units.append(('req', list(am)))
            else:
                src = table_lib.block_sources(T, b)
                assert src[0] == 'pairs'
                for (c1, X1, c2, X2) in src[1]:
                    V1 = lift(c1, X1); V2 = lift(c2, X2)
                    V = [V1[i]+V2[i] for i in range(34)]
                    units.append(('req', V)); pair_expand += 1
        else:
            units.append(('kok', b[1]))
    unit_counts.append(len(units))
    if len(units) > 1500: big.append((len(units), sorted(W)))
print("total classes %d, total units %d, pair_expand %d, %.1fs" % (len(CLS), sum(unit_counts), pair_expand, time.time()-t0), flush=True)
uc = sorted(unit_counts)
print("units/class: min %d median %d mean %.1f max %d" % (uc[0], uc[len(uc)//2], sum(uc)/len(uc), uc[-1]))
print("classes with >1500 units:", len(big), big[:6])
hist = collections.Counter()
for n in unit_counts:
    hist[min(n//100, 20)] += 1
print("hist (bucket=100, 20 means >=2000):", sorted(hist.items()))
pickle.dump(unit_counts, open('work/recon/k3_unit_counts.pkl','wb'))
