# -*- coding: utf-8 -*-
"""k4_units_fix.py -- 修正版单元模型 + Hall 检查（Lead）
kind I : 单元 X（要求 码 ⊆ X）
kind II: |am1⊎am2|>=4 -> 单元 am1⊎am2（一条码覆盖整块）
         否则：选尺寸>=3 的一侧，对其每个 X 生成行单元 X ⊕ am_other（关键修正）
         两侧都=2：按对单元 X1⊕X2
用 PROFII_D 的 xs 列表分别求极小，避免展开乘积。
"""
import sys, os, collections, math, json, time, pickle
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
if os.path.exists(CACHE):
    T=pickle.load(open(CACHE,'rb'))
else:
    T=table_lib.build()
CLS=T['cls']
t0=time.time()
need=collections.defaultdict(set); sizes=collections.Counter(); nunit=0
for W,blocks in CLS.items():
    u=set()
    for b in blocks:
        if b[0]=='I':
            for (c,X) in table_lib.block_sources(T,b)[1]:
                u.add(tuple(lift(c,X)))
        elif b[0]=='II':
            (c1,s1,k1)=b[1]; (c2,s2,k2)=b[2]
            am=b[5]
            if sum(am)>=4:
                u.add(tuple(am))
            else:
                am1, xs1 = T['PROFII_D'][(c1,s1,k1)]
                am2, xs2 = T['PROFII_D'][(c2,s2,k2)]
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
        else:
            u.add(tuple(b[1]))
    for V in u:
        nunit+=1; sizes[sum(V)]+=1
        need[V].add(W)
print("distinct units %d total %d  sizes %s (%.0fs)" % (len(need), nunit, sorted(sizes.items()), time.time()-t0), flush=True)
def cap(X):
    tiles=[]
    for t,c in enumerate(X):
        for _ in range(c): tiles.append(t)
    n=len(tiles); seen=set()
    for i in range(n):
        for j in range(i,n):
            for k in range(j,n):
                for l in range(k,n): seen.add(tuple(sorted((tiles[i],tiles[j],tiles[k],tiles[l]))))
    return sum(p4(mu) for mu in seen)
bad=[]; checked=0
for X,cls in need.items():
    s=sum(X)
    if s<4 or s>8: continue
    checked+=1
    c=cap(X); d=len(cls)
    if d>c: bad.append((d,c,X))
print("checked units %d  Hall violations: %d" % (checked, len(bad)))
for d,c,X in sorted(bad,key=lambda z:-z[0])[:12]:
    print("   D=%d Cap=%d X=%s" % (d,c,[(t,x) for t,x in enumerate(X) if x]))
json.dump({"violations":[[d,c,[t for t,x in enumerate(X) if x]] for d,c,X in bad][:300], "distinct_units":len(need), "nunit":nunit, "sizes":{str(k):v for k,v in sizes.items()}}, open('work/recon/k4_unit_hall_fix.json','w'))
