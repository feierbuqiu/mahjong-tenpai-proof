# -*- coding: utf-8 -*-
"""快速探针: 清一色 387 类在 k=3 的贪心命中集大小分布"""
import itertools, time, json
from functools import lru_cache
T0=time.time()
@lru_cache(maxsize=None)
def melds_only(c):
    n=len(c); i=0
    while i<n and c[i]==0: i+=1
    if i==n: return 0
    best=None
    if c[i]>=3:
        c2=list(c); c2[i]-=3
        r=melds_only(tuple(c2))
        if r is not None: best=r+1
    if i+2<n and c[i+1]>0 and c[i+2]>0:
        c2=list(c); c2[i]-=1;c2[i+1]-=1;c2[i+2]-=1
        r=melds_only(tuple(c2))
        if r is not None and (best is None or r+1<best): best=r+1
    return best
def is_std_win(cnt):
    for i in range(34):
        if cnt[i]>=2:
            c=list(cnt); c[i]-=2
            tot=0; ok=True
            for b,n in ((0,9),(9,9),(18,9),(27,7)):
                m=melds_only(tuple(c[b:b+n]))
                if m is None: ok=False; break
                tot+=m
            if ok and tot==4: return True
    return False
def is_chiitoi_win(cnt):
    np_=0
    for x in cnt:
        if x==0: continue
        if x!=2: return False
        np_+=1
    return np_==7
def waits(cnt):
    res=[]
    for t in range(34):
        if cnt[t]>=4: continue
        c=list(cnt); c[t]+=1
        if is_std_win(c) or is_chiitoi_win(c): res.append(t)
    return tuple(res)
cls={}
for c in itertools.product(range(5),repeat=9):
    if sum(c)!=13: continue
    cnt=[0]*34
    for i,v in enumerate(c):
        if v: cnt[i]=v
    W=waits(cnt)
    if W: cls.setdefault(W,[]).append(tuple(cnt))
print("类=%d 手牌=%d (t=%.1f)"%(len(cls),sum(len(v) for v in cls.values()),time.time()-T0),flush=True)

k=3
combos=list(itertools.combinations_with_replacement(range(9),k))
req=[tuple((t,comb.count(t)) for t in set(comb)) for comb in combos]
NC=len(combos)
print("k=3 无序码个数 =",NC,flush=True)

def analyze(W,hs):
    # hand masks over codes
    hm=[]
    for h in hs:
        m=0
        for ci,need in enumerate(req):
            ok=True
            for t,n in need:
                if h[t]<n: ok=False; break
            if ok: m|=1<<ci
        hm.append(m)
    full=(1<<len(hs))-1
    common=full
    for m in hm: common&=m
    if common: return (1,None,None)
    # cover[code] over hands
    n=len(hs)
    cover=[0]*NC
    for i,m in enumerate(hm):
        mm=m
        while mm:
            b=mm&-mm; c=b.bit_length()-1; cover[c]|=1<<i; mm^=b
    # greedy: pick max cover
    unc=full; greedy=[]
    while unc:
        best=-1; bc=None
        for c in range(NC):
            v=(cover[c]&unc).bit_count()
            if v>best: best=v; bc=c
        if best==0: return (None,None,None)
        greedy.append(bc); unc &= ~cover[bc]
    g=len(greedy)
    # redundancy removal
    changed=True
    while changed and len(greedy)>1:
        changed=False
        for i in range(len(greedy)):
            un=full
            for j,c in enumerate(greedy):
                if j!=i: un &= ~cover[c]
            if un==0:
                greedy.pop(i); changed=True; break
    return (g,len(greedy),greedy)

res={}
taus={}
for W,hs in cls.items():
    g,red,gl=analyze(W,hs)
    taus[W]=red if red is not None else g
    res[W]=(g,red)
dist={}
for v in taus.values(): dist[v]=dist.get(v,0)+1
print("k=3 贪心(去冗余后)tau 分布 =",dict(sorted(dist.items())),flush=True)
print("k=3 Sigma(贪心去冗余) =",sum(taus.values())," vs 9^3 =",729,flush=True)
print("t=%.1f"%(time.time()-T0),flush=True)
json.dump({"dist":{str(a):b for a,b in dist.items()},"sum":sum(taus.values()),
           "per_class":{",".join(map(str,W)):v for W,v in taus.items()}},
          open("work/lowerbound/probe_tau3.json","w"))
