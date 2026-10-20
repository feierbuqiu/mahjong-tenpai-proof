# -*- coding: utf-8 -*-
import sys, collections
sys.path.insert(0,'work/strategy')
import table_lib
from table_lib import CAT_BASE
T=table_lib.build(); CLS=T['cls']
def lift(c,X):
    v=[0]*34
    for i,x in enumerate(X): v[CAT_BASE[c]+i]=x
    return v
d=collections.Counter(); per=[]
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
    s=[sum(v) for v in u]
    per.append(s)
    for x in s: d[x]+=1
print("unit |X| distribution:", sorted(d.items()))
print("units with |X|<=7:", sum(v for k,v in d.items() if k<=7))
tot=sum(d.values()); print("total units", tot)
