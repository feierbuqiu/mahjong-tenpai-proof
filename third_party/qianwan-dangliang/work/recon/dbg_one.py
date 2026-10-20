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
W=frozenset([4,7])   # 5m,8m
blocks=CLS[W]
print("n blocks", len(blocks), collections.Counter(b[0] for b in blocks))
n4=0; hit=False
for b in blocks:
    if b[0]=='I':
        for (cc,X) in table_lib.block_sources(T,b)[1]:
            V=lift(cc,X); s=sum(V)
            if s==4:
                n4+=1
                if tuple(V)==tuple([1 if t in (4,5,6,7) else 0 for t in range(34)]): hit=True
print("kind I size-4 units:", n4, "contains m5m6m7m8:", hit)
