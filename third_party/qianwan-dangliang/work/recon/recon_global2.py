
import json, time, itertools
from functools import lru_cache

def ncat(c): return 9 if c < 3 else 7
def gidx(c, i): return c*9+i if c < 3 else 27+i

_memo = {}
def melds_only(c):
    k = tuple(c); r = _memo.get(k)
    if r is not None: return r
    n = len(k); i = 0
    while i < n and k[i] == 0: i += 1
    if i == n: _memo[k]=True; return True
    res=False
    if k[i] >= 3:
        l=list(k); l[i]-=3
        if melds_only(tuple(l)): res=True
    if not res and i+2<n and k[i+1]>0 and k[i+2]>0:
        l=list(k); l[i]-=1; l[i+1]-=1; l[i+2]-=1
        if melds_only(tuple(l)): res=True
    _memo[k]=res; return res

def melds_pair(c):
    for j in range(len(c)):
        if c[j] >= 2:
            l=list(c); l[j]-=2
            if melds_only(tuple(l)): return True
    return False

def gen(size, n, cap=4):
    cur=[0]*n
    def rec(i, rem):
        if i==n-1:
            if rem<=cap:
                cur[i]=rem; yield tuple(cur); cur[i]=0
            return
        for v in range(min(cap,rem)+1):
            cur[i]=v; yield from rec(i+1, rem-v)
        cur[i]=0
    yield from rec(0,size)

melds_of = {}
for c in range(4):
    n = ncat(c); ms=[]
    for i in range(n):
        v=[0]*n; v[i]=3; ms.append(tuple(v))
    if c < 3:
        for i in range(n-2):
            v=[0]*n; v[i]=1; v[i+1]=1; v[i+2]=1; ms.append(tuple(v))
    melds_of[c]=ms

t0=time.time()
_fcache={}
def filler_data(S, j):
    key=(tuple(sorted(S)), j)
    if key in _fcache: return _fcache[key]
    items=[(c,v) for c in sorted(S) for v in melds_of[c]]
    has_zero=False; odd1=set(); seen=set()
    for combo in itertools.combinations_with_replacement(range(len(items)), j):
        per={}
        ok=True
        for idx in combo:
            c,v = items[idx]
            d = per.setdefault(c, [0]*ncat(c))
            for i,x in enumerate(v):
                d[i]+=x
                if d[i] > 4: ok=False; break
            if not ok: break
        if not ok: continue
        defaults=[[0]*ncat(c) for c in range(4)]
        sig=tuple(tuple(per.get(c, defaults[c])) for c in sorted(S))
        if sig in seen: continue
        seen.add(sig)
        oddn=0; oddt=[]
        for c in sorted(S):
            for i,x in enumerate(per.get(c, [0]*ncat(c))):
                if x % 2 == 1:
                    oddn+=1; oddt.append(gidx(c,i))
        if oddn==0: has_zero=True
        elif oddn==1: odd1.add(oddt[0])
    res=(has_zero, frozenset(odd1), len(seen))
    _fcache[key]=res
    return res

# per-category signatures
catI={}; catII={}
SIZES_I=(1,4,7,10,13); SIZES_II=(2,5,8,11)
for c in range(4):
    n=ncat(c); SI=set(); SII=set()
    for size in SIZES_I:
        for X in gen(size,n):
            Wp=0
            for t in range(n):
                if X[t]<4:
                    l=list(X); l[t]+=1
                    if melds_pair(l): Wp |= 1<<t
            odd=[i for i,v in enumerate(X) if v%2==1]
            SI.add((tuple(X), Wp, (1 if len(odd)==1 else (0 if not odd else 2)), odd[0] if len(odd)==1 else -1, size))
    for size in SIZES_II:
        for X in gen(size,n):
            V=0
            for t in range(n):
                if X[t]<4:
                    l=list(X); l[t]+=1
                    if melds_only(l): V |= 1<<t
            pd=melds_pair(X)
            odd=[i for i,v in enumerate(X) if v%2==1]
            SII.add((V, pd, (1 if len(odd)==1 else (0 if not odd else 2)), odd[0] if len(odd)==1 else -1, size))
    catI[c]=SI; catII[c]=SII
    print("cat %d sigI=%d sigII=%d" % (c,len(SI),len(SII)), flush=True)

def gset(c, mask): return frozenset(gidx(c,i) for i in range(ncat(c)) if (mask>>i)&1)

CLASS=set()
# Type I
for c in range(4):
    S=[x for x in range(4) if x!=c]
    for (Xt, Wp, oddn, oddt, size) in catI[c]:
        m=13-size; j=m//3
        hz, o1, _ = filler_data(S, j)
        base=gset(c,Wp)
        if Wp: CLASS.add(base)
        if oddn==1 and hz and Wp: CLASS.add(base | {gidx(c,oddt)})
        elif oddn==1 and hz and not Wp: CLASS.add(frozenset({gidx(c,oddt)}))
        if oddn==0:
            for z in o1: CLASS.add(base | {z})
for S in ([1,2,3],[0,2,3],[0,1,3],[0,1,2],[2,3],[1,3],[1,2],[0,3],[0,2],[0,1]):
    for j in range(5):
        hz,o1,cnt = filler_data(S,j)
        print("   filler S=%s j=%d: #distinctF=%d has_zero_odd=%s #odd1tiles=%d" % (S,j,cnt,hz,len(o1)), flush=True)
print("after TypeI |CLASS|=%d t=%.1fs"%(len(CLASS),time.time()-t0), flush=True)

# Type II
for (c1,c2) in [(a,b) for a in range(4) for b in range(a+1,4)]:
    S=[x for x in range(4) if x not in (c1,c2)]
    for (V1,pd1,o1n,o1t,s1) in catII[c1]:
        for (V2,pd2,o2n,o2t,s2) in catII[c2]:
            if s1+s2 > 13: continue
            m=13-s1-s2; j=m//3
            hz,o1,_=filler_data(S,j)
            Wstd=0
            if pd1: Wstd |= V2
            if pd2: Wstd |= V1
            Wf = gset(c1, Wstd & ((1<<ncat(c1))-1)) | gset(c2, Wstd >> ncat(c1))
            if Wstd: CLASS.add(Wf)
            tot=o1n+o2n
            if tot==1 and hz:
                z = gidx(c1,o1t) if o1n==1 else gidx(c2,o2t)
                CLASS.add(Wf | {z})
            if tot==0:
                for z in o1: CLASS.add(Wf | {z})
    print("pair(%d,%d) |CLASS|=%d t=%.1fs"%(c1,c2,len(CLASS),time.time()-t0), flush=True)

for z in range(34): CLASS.add(frozenset({z}))
term=[0,8,9,17,18,26]+list(range(27,34))
CLASS.add(frozenset(term))
print("GLOBAL CLASSES =", len(CLASS), flush=True)
sizes={}
for w in CLASS: sizes[len(w)]=sizes.get(len(w),0)+1
print("by |W|:", dict(sorted(sizes.items())), flush=True)
print("64^k budgets: k=2:%d k=3:%d"%(34**2,34**3))
json.dump({"n_classes":len(CLASS),"by_size":{str(k):v for k,v in sizes.items()}}, open(r"D:\DSH\MJ2\work\recon\global_classes_v2.json","w"))
print("t=%.1fs"%(time.time()-t0))
