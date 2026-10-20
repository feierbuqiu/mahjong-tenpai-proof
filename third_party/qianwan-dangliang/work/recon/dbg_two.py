import sys, pickle, collections, itertools
import numpy as np
sys.path.insert(0,'work/strategy')
import table_lib
from table_lib import CAT_BASE
T=pickle.load(open('work/strategy/out/table_cache.pkl','rb'))
CLS=T['cls']
def lift(c,X):
    v=[0]*34
    for i,x in enumerate(X): v[CAT_BASE[c]+i]=x
    return v
W=frozenset([4,7])
percls={W:list({tuple(lift(cc,X)) for b in CLS[W] if b[0]=='I' for (cc,X) in table_lib.block_sources(T,b)[1]
                if sum(lift(cc,X))>=4} |
               {(tuple(b[5]) if sum(b[5])>=4 else None) for b in CLS[W] if b[0]=='II'} - {None})}
keys=percls[W]
target=tuple(1 if t in (4,5,6,7) else 0 for t in range(34))
print("units", len(keys), "target present:", target in keys, "idx:", keys.index(target) if target in keys else -1)
U=np.array(keys,dtype=np.int8)
tgt=np.array(target,dtype=np.int8)
print("units dominated by target:", int((U<=tgt).all(-1).sum()) if False else int((U<=tgt).all(-1).sum() if (U<=tgt).all(-1).any() else 0))
# 该类是否含 chiitoi / tanki 预留?
G=__import__('json').load(open('work/data/out/global.json',encoding='utf-8'))
HONN=['E','S','W','N','Haku','Hatsu','Chun']
def ti(s): return 27+HONN.index(s) if s in HONN else 'mps'.index(s[-1])*9+int(s[0])-1
m2=0
for t in W: m2|=1<<t
zs=set()
for mask,lst in G['chiitoi_descriptors'].items():
    if int(mask)==m2: zs={ti(d['z']) for d in lst}
print("chiitoi zs:", zs)
print("tanki units(|X|=1):", sum(1 for V in keys if sum(V)==1))
