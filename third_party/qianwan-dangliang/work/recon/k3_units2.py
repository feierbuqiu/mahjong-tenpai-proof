# -*- coding: utf-8 -*-
"""k3_units2.py -- 改进的 k=3 装包单元统计（Lead）
- kind I : |X|>=3 -> (req,X) ; |X|=1 -> (tanki,c)
- kind II: |am|>=3 -> (req,am) 一条码覆盖整块
           |am|<3 -> 取较大的那一侧做『侧覆盖』(per-X 需求, 因为 c⊆X ⇒ c⊆X1+X2+F)
           两侧都只有 2 张 -> 按对展开
"""
import sys, collections, pickle, time
sys.path.insert(0, 'work/strategy')
import table_lib
from table_lib import CAT_BASE
T = table_lib.build()
CLS = T['cls']
def lift(c, X):
    v = [0]*34
    for i, x in enumerate(X): v[CAT_BASE[c]+i] = x
    return v
cnt = collections.Counter(); unit_counts = []; pair2 = 0; big = []
t0 = time.time()
for W, blocks in CLS.items():
    units = []
    for b in blocks:
        if b[0] == 'I':
            for (c, X) in table_lib.block_sources(T, b)[1]:
                V = lift(c, X)
                units.append(('req', V) if sum(V) >= 3 else ('tanki', c, sum(V)))
        elif b[0] == 'II':
            am = b[5]; s1 = b[1][1]; s2 = b[2][1]
            if sum(am) >= 3:
                units.append(('req', list(am)))
            elif max(s1, s2) >= 3:
                src = table_lib.block_sources(T, b)[1]
                if s1 >= s2:
                    side = set(tuple(lift(x[0], x[1])) for x in src)
                else:
                    side = set(tuple(lift(x[2], x[3])) for x in src)
                for V in side: units.append(('req', list(V)))
            else:
                for (c1, X1, c2, X2) in table_lib.block_sources(T, b)[1]:
                    V1 = lift(c1, X1); V2 = lift(c2, X2)
                    units.append(('req', [V1[i]+V2[i] for i in range(34)]))
                    pair2 += 1
        else:
            units.append(('kok', b[1]))
    unit_counts.append(len(units))
    if len(units) > 2000: big.append((len(units), sorted(W)))
    for u in units: cnt[u[0]] += 1
print("units total %d  (req %d tanki %d kok %d)  s1=s2=2 pair-expansions %d  %.1fs" % (
    sum(unit_counts), cnt['req'], cnt['tanki'], cnt['kok'], pair2, time.time()-t0))
uc = sorted(unit_counts)
print("units/class: min %d p50 %d p90 %d mean %.1f max %d" % (uc[0], uc[len(uc)//2], uc[int(len(uc)*0.9)], sum(uc)/len(uc), uc[-1]))
print("classes >2000 units:", len(big), big[:8])
pickle.dump(unit_counts, open('work/recon/k3_unit_counts2.pkl','wb'))
