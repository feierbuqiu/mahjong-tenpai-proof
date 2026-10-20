# -*- coding: utf-8 -*-
"""k4_unit_hall.py -- 单元级 Hall 检查（Lead）: D(X) vs Cap(X)=Σ_{μ⊆X} p4(μ)"""
import sys, collections, math, json, time
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
T=table_lib.build(); CLS=T['cls']
t0=time.time()
need=collections.defaultdict(set)   # X -> set of classes
for W,blocks in CLS.items():
    u=set()
    for b in blocks:
        if b[0]=='I':
            for (c,X) in table_lib.block_sources(T,b)[1]:
                V=lift(c,X); u.add(tuple(V))
        elif b[0]=='II':
            am=b[5]; s1=b[1][1]; s2=b[2][1]
            if sum(am)>=4: u.add(tuple(am))
            elif max(s1,s2)>=4:
                for (c1,X1,c2,X2) in table_lib.block_sources(T,b)[1]:
                    u.add(tuple(lift(c1,X1) if s1>=s2 else lift(c2,X2)))
            else:
                for (c1,X1,c2,X2) in table_lib.block_sources(T,b)[1]:
                    V1=lift(c1,X1); V2=lift(c2,X2); u.add(tuple(V1[i]+V2[i] for i in range(34)))
        else: u.add(tuple(b[1]))
    for V in u:
        if 4<=sum(V)<=7: need[V].add(W)
print("distinct scarce units %d (%.0fs)" % (len(need), time.time()-t0))
def cap(X):
    cnts=[c for c in X if c]
    tot=0
    for a in range(len(cnts)+2):
        pass
    # 枚举 X 的 4-子多重集
    tiles=[]
    for t,c in enumerate(X):
        for _ in range(c): tiles.append(t)
    n=len(tiles); seen=set()
    for i in range(n):
        for j in range(i,n):
            for k in range(j,n):
                for l in range(k,n):
                    seen.add(tuple(sorted((tiles[i],tiles[j],tiles[k],tiles[l]))))
    return sum(p4(mu) for mu in seen)
bad=[]; ratios=[]
for X,cls in need.items():
    d=len(cls); c=cap(X); ratios.append((d,c,d/c if c else 9e9))
    if d>c: bad.append((d,c,X))
print("Hall violations (D(X) > Cap(X)): %d" % len(bad))
for d,c,X in sorted(bad, key=lambda z:-z[0])[:15]:
    print("   D=%d Cap=%d X=%s" % (d,c,[(t,x) for t,x in enumerate(X) if x]))
ratios.sort(key=lambda z:-z[2])
print("top D/Cap ratios:", [(round(r,2),d,c) for d,c,r in ratios[:10]])
json.dump({"violations":[[d,c,[t for t,x in enumerate(X) if x]] for d,c,X in bad][:200]}, open('work/recon/k4_unit_hall.json','w'))
