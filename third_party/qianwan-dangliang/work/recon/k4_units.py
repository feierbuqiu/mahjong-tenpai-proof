# -*- coding: utf-8 -*-
"""k4_units.py -- k=4 装包单元统计（Lead）"""
import sys, collections, pickle, time
sys.path.insert(0, 'work/strategy')
import table_lib
from table_lib import CAT_BASE
T = table_lib.build(); CLS = T['cls']
def lift(c, X):
    v = [0]*34
    for i, x in enumerate(X): v[CAT_BASE[c]+i] = x
    return v
cnt = collections.Counter(); unit_counts = []; big = []; tanki = 0
t0 = time.time()
for W, blocks in CLS.items():
    units = set()
    for b in blocks:
        if b[0] == 'I':
            for (c, X) in table_lib.block_sources(T, b)[1]:
                V = lift(c, X)
                if sum(V) >= 4: units.add(('req', tuple(V)))
                else: units.add(('tanki', tuple(V)))
        elif b[0] == 'II':
            am = b[5]; s1 = b[1][1]; s2 = b[2][1]
            if sum(am) >= 4:
                units.add(('req', tuple(am)))
            elif max(s1, s2) >= 4:
                for (c1, X1, c2, X2) in table_lib.block_sources(T, b)[1]:
                    V = lift(c1, X1) if s1 >= s2 else lift(c2, X2)
                    units.add(('req', tuple(V)))
            else:
                for (c1, X1, c2, X2) in table_lib.block_sources(T, b)[1]:
                    V1 = lift(c1, X1); V2 = lift(c2, X2)
                    units.add(('req', tuple(V1[i]+V2[i] for i in range(34))))
        else:
            units.add(('req', tuple(b[1])))
    n = len(units); unit_counts.append(n)
    if n > 1000: big.append((n, sorted(W)))
    for u in units: cnt[u[0]] += 1
print("units total %d (req %d tanki %d) %.1fs" % (sum(unit_counts), cnt['req'], cnt['tanki'], time.time()-t0))
uc = sorted(unit_counts)
print("units/class: min %d p50 %d p90 %d mean %.1f max %d" % (uc[0], uc[len(uc)//2], uc[int(len(uc)*0.9)], sum(uc)/len(uc), uc[-1]))
print("classes >1000 units:", len(big), big[:8])
