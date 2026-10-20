# -*- coding: utf-8 -*-
"""k4_tight_units.py -- 检查 |X|=4 单元（唯一候选 = 其自身多重集）的容量是否够（Lead）
若某多重集 mu 被 D(mu) 个不同类 '必须' 使用，而 p4(mu) < D(mu) ⇒ k=4 不可行。
"""
import sys, collections, math, json
sys.path.insert(0, 'work/strategy')
import table_lib
from table_lib import CAT_BASE
FACT=[math.factorial(i) for i in range(5)]
def p4(mu):
    c=collections.Counter(mu); return 24//math.prod(FACT[v] for v in c.values())
T=table_lib.build(); CLS=T['cls']
def lift(c,X):
    v=[0]*34
    for i,x in enumerate(X): v[CAT_BASE[c]+i]=x
    return v
need=collections.defaultdict(set)   # mu -> set of classes(W)
units4=0
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
        if sum(V)==4:
            units4+=1
            mu=tuple(sorted(t for t,c in enumerate(V) for _ in range(c)))
            need[mu].add(W)
print("|X|=4 units:", units4, "distinct multisets:", len(need))
over=[(mu,len(ws),p4(mu)) for mu,ws in need.items() if len(ws)>p4(mu)]
print("oversubscribed multisets:", len(over))
for mu,n,p in sorted(over,key=lambda z:-z[1])[:20]:
    print("   mu=%s  classes=%d  p4=%d" % (mu,n,p))
json.dump([[list(mu),n,p] for mu,n,p in over], open('work/recon/k4_tight_over.json','w'))
