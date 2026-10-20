
import json, time, itertools
from functools import lru_cache

_memo={}
def melds_only(c):
    k=tuple(c); r=_memo.get(k)
    if r is not None: return r
    n=len(k); i=0
    while i<n and k[i]==0: i+=1
    if i==n: _memo[k]=True; return True
    res=False
    if k[i]>=3:
        l=list(k); l[i]-=3
        if melds_only(tuple(l)): res=True
    if not res and i+2<n and k[i+1]>0 and k[i+2]>0:
        l=list(k); l[i]-=1; l[i+1]-=1; l[i+2]-=1
        if melds_only(tuple(l)): res=True
    _memo[k]=res; return res
def melds_pair(c):
    for j in range(len(c)):
        if c[j]>=2:
            l=list(c); l[j]-=2
            if melds_only(tuple(l)): return True
    return False

def gen(size,n,cap=4):
    cur=[0]*n
    def rec(i,rem):
        if i==n-1:
            if rem<=cap:
                cur[i]=rem; yield tuple(cur); cur[i]=0
            return
        for v in range(min(cap,rem)+1):
            cur[i]=v; yield from rec(i+1, rem-v)
        cur[i]=0
    yield from rec(0,size)

def analyze(n, k):
    t0=time.time()
    codes=[(a,b,c) for a in range(n) for b in range(n) for c in range(n)]
    cidx={c:i for i,c in enumerate(codes)}
    combos=[]
    for a in range(n):
        for b in range(a,n):
            for c in range(b,n):
                need=[0]*n; need[a]+=1; need[b]+=1; need[c]+=1
                ms=0
                for p in set(itertools.permutations((a,b,c))): ms |= 1<<cidx[p]
                combos.append((need, ms))
    groups={}
    nhands=0
    for X in gen(13,n):
        W=set()
        for t in range(n):
            if X[t]<4:
                l=list(X); l[t]+=1
                if melds_pair(l): W.add(t)
        odd=[i for i,v in enumerate(X) if v%2==1]
        if len(odd)==1: W.add(odd[0])
        if W:
            nhands+=1
            groups.setdefault(frozenset(W),[]).append(X)
    # masks
    gmasks={}
    for W,hs in groups.items():
        ms=[]
        for X in hs:
            m=0
            for need,msk in combos:
                ok=True
                for i in range(n):
                    if need[i]>X[i]: ok=False; break
                if ok: m |= msk
            ms.append(m)
        gmasks[W]=ms
    NC=n**k
    def taus(masks):
        inter=None
        for m in masks:
            inter = m if inter is None else (inter & m)
            if inter==0: break
        if inter: return 1, 0
        # tau=2 ?
        union=0
        for m in masks: union |= m
        c=0
        while union:
            if union & 1:
                unc=[m for m in masks if not ((m>>c)&1)]
                if unc:
                    it=None
                    for m in unc:
                        it = m if it is None else (it & m)
                        if it==0: break
                    if it: return 2, 0
            union >>= 1; c+=1
        # greedy upper bound
        rem=list(masks); used=0
        while rem:
            # pick code hitting most
            best=-1; bestc=None
            cand=0
            for m in rem: cand |= m
            cc=0; tmp=cand
            while tmp:
                if tmp & 1:
                    hit=sum(1 for m in rem if (m>>cc)&1)
                    if hit>best: best=hit; bestc=cc
                tmp >>= 1; cc+=1
            used+=1
            rem=[m for m in rem if not ((m>>bestc)&1)]
        return used, 1
    total=0; exact=0; greedy=0; dist={}
    for W,ms in gmasks.items():
        t,g = taus(ms)
        total+=t; dist[t]=dist.get(t,0)+1
        if g: greedy+=1
        else: exact+=1
    return dict(n=n, n_hands=nhands, n_groups=len(groups), code_space=NC,
                sum_tau_upper=total, tau_dist=dist, groups_with_greedy_upper=greedy,
                groups_exact=exact, secs=round(time.time()-t0,1))

r9 = analyze(9,3); print("SUIT (9 tiles, k=3):", json.dumps(r9, ensure_ascii=False), flush=True)
r7 = analyze(7,3); print("HONORS (7 tiles, k=3):", json.dumps(r7, ensure_ascii=False), flush=True)
json.dump({"suit":r9,"honors":r7}, open(r"D:\DSH\MJ2\work\recon\flush_tau.json","w"))
