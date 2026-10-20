import sys, pickle, collections
sys.path.insert(0,'work/strategy')
import table_lib
from table_lib import CAT_BASE
T=pickle.load(open('work/strategy/out/table_cache.pkl','rb'))
CLS=T['cls']
def lift(c,X):
    v=[0]*34
    for i,x in enumerate(X): v[CAT_BASE[c]+i]=x
    return v
W=frozenset([22,25])  # 5s,8s
tgt=tuple(1 if t in (22,23,24,25) else 0 for t in range(34))
print("W in CLS:", W in CLS, "nblocks", len(CLS.get(W,[])))
n4=0; found=False
for b in CLS[W]:
    if b[0]!='I': continue
    for (cc,X) in table_lib.block_sources(T,b)[1]:
        V=lift(cc,X)
        if sum(V)==4:
            n4+=1
            if tuple(V)==tgt: found=True
print("kind I size-4 units:", n4, "target found:", found)
# 也看该类的 block key 概览
ks=collections.Counter((b[0], b[1][1] if b[0]=='I' else (b[1][1],b[2][1])) for b in CLS[W])
print("block kinds/sizes:", ks.most_common(8))
