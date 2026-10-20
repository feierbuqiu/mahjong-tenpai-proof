# -*- coding: utf-8 -*-
"""k4_units_fix2.py -- 修正版单元模型 + **正确的** Cap(X) 计算（Lead）
Cap(X) = X 的 4-子多重集个数（严格索引组合）的排列数之和 = 『有序 4-码且多重集 ⊆ X』的条数。
"""
import sys, os, collections, math, json, time, pickle, itertools
sys.path.insert(0,'work/strategy')
import table_lib
from table_lib import CAT_BASE
FACT=[math.factorial(i) for i in range(5)]
def p4(mu):
    c=collections.Counter(mu); return 24//math.prod(FACT[v] for v in c.values())
def lift(c,X):
    v=[0]*34
    for i,x in enumerate(X): v[CAT_BASE[c]+i]=x
    return v
CACHE='work/strategy/out/table_cache.pkl'
T=pickle.load(open(CACHE,'rb')) if os.path.exists(CACHE) else table_lib.build()
CLS=T['cls']
HON=[27,28,29,30,31,32,33]
def cap(X):
    tiles=[]
    for t,c in enumerate(X):
        for _ in range(c): tiles.append(t)
    return sum(p4(mu) for mu in set(itertools.combinations(tiles,4)))
# 自检：Cap({0:2,2:3}) 应为 10
x=[0]*34; x[0]=2; x[2]=3
print("selfcheck Cap({m1x2,m3x3}) =", cap(x), "(expect 10)", flush=True)
t0=time.time()
need=collections.defaultdict(set); sizes=collections.Counter(); nunit=0
for W,blocks in CLS.items():
    u=set()
    for b in blocks:
        if b[0]=='I':
            for (c,X) in table_lib.block_sources(T,b)[1]:
                u.add(tuple(lift(c,X)))
        elif b[0]=='II':
            (c1,s1,k1)=b[1]; (c2,s2,k2)=b[2]; am=b[5]
            if sum(am)>=4: u.add(tuple(am))
            else:
                am1,xs1=T['PROFII_D'][(c1,s1,k1)]; am2,xs2=T['PROFII_D'][(c2,s2,k2)]
                A1=list(am1); A2=list(am2)
                if s1>=3:
                    for X1 in xs1:
                        V1=lift(c1,X1); u.add(tuple(V1[i]+A2[i] for i in range(34)))
                elif s2>=3:
                    for X2 in xs2:
                        V2=lift(c2,X2); u.add(tuple(A1[i]+V2[i] for i in range(34)))
                else:
                    for X1 in xs1:
                        V1=lift(c1,X1)
                        for X2 in xs2:
                            V2=lift(c2,X2); u.add(tuple(V1[i]+V2[i] for i in range(34)))
        else: u.add(tuple(b[1]))
    for V in u:
        nunit+=1; sizes[sum(V)]+=1; need[V].add(W)
print("distinct units %d total %d sizes %s (%.0fs)" % (len(need), nunit, sorted(sizes.items()), time.time()-t0), flush=True)
bad=[]; checked=0
for X,cls in need.items():
    s=sum(X)
    if s<4 or s>9: continue
    checked+=1; c=cap(X); d=len(cls)
    if d>c: bad.append((d,c,X))
print("checked %d units; Hall violations: %d" % (checked, len(bad)))
for d,c,X in sorted(bad,key=lambda z:-z[0])[:12]:
    print("   D=%d Cap=%d X=%s" % (d,c,[(t,x) for t,x in enumerate(X) if x]))
json.dump({"violations":[[d,c,[t for t,x in enumerate(X) if x]] for d,c,X in bad][:300],
           "distinct_units":len(need),"nunit":nunit}, open('work/recon/k4_unit_hall_fix2.json','w'))
