
import json, time, itertools, random, sys
sys.setrecursionlimit(100000)
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

def build(n):
    patterns=[]   # canonical multisets (a<=b<=c)
    for a in range(n):
        for b in range(a,n):
            for c in range(b,n):
                need=[0]*n; need[a]+=1; need[b]+=1; need[c]+=1
                patterns.append(need)
    NP=len(patterns)
    grp_full={}; grp_std={}
    n_std=0; n_chi=0
    for X in gen(13,n):
        Wstd=set()
        for t in range(n):
            if X[t]<4:
                l=list(X); l[t]+=1
                if melds_pair(l): Wstd.add(t)
        odd=[i for i,v in enumerate(X) if v%2==1]
        Wf=set(Wstd)
        if len(odd)==1: Wf.add(odd[0])
        if Wstd: n_std+=1
        if Wf:
            if not Wstd: n_chi+=1
            m=0
            for pi,need in enumerate(patterns):
                ok=True
                for i in range(n):
                    if need[i]>X[i]: ok=False; break
                if ok: m |= 1<<pi
            grp_full.setdefault(frozenset(Wf),[]).append(m)
            if Wstd: grp_std.setdefault(frozenset(Wstd),[]).append(m)
    return patterns, grp_full, grp_std, n_std, n_chi

def minimal(masks):
    ms=sorted(set(masks), key=lambda m: bin(m).count('1'))
    keep=[]
    for m in ms:
        if not any((k & m)==k for k in keep): keep.append(m)
    return keep

def greedy(ms, rnd=None):
    rem=list(ms); used=0
    while rem:
        cand=0
        for m in rem: cand|=m
        best=-1; bestp=0
        plist=[]
        tmp=cand
        while tmp:
            b=tmp & -tmp; p=b.bit_length()-1; tmp^=b
            hit=0
            for m in rem:
                if (m>>p)&1: hit+=1
            if hit>best: best=hit; bestp=p; plist=[p]
            elif hit==best: plist.append(p)
        if rnd is not None and len(plist)>1: bestp=rnd.choice(plist)
        used+=1
        rem=[m for m in rem if not ((m>>bestp)&1)]
    return used

def maxdisjoint(ms):
    order=sorted(ms, key=lambda m: bin(m).count('1'))
    chosen=[]; covered=0
    for m in order:
        if not (m & covered):
            chosen.append(m); covered|=m
    return len(chosen)

def exact_tau(ms, ub, timelimit=20.0):
    ms=minimal(ms)
    # tau=1
    inter=None
    for m in ms:
        inter = m if inter is None else (inter & m)
        if inter==0: break
    if inter: return 1,'exact'
    # tau=2
    union=0
    for m in ms: union|=m
    tmp=union
    while tmp:
        b=tmp & -tmp; p=b.bit_length()-1; tmp^=b
        unc=[m for m in ms if not ((m>>p)&1)]
        if unc:
            it=None
            for m in unc:
                it = m if it is None else (it & m)
                if it==0: break
            if it: return 2,'exact'
    lb=maxdisjoint(ms)
    if lb>=ub: return ub,'lb=ub'
    t0=time.time()
    idx={id(m):i for i,m in enumerate(ms)}
    fail=set()
    def can(rem, k):
        if not rem: return True
        if k==0: return False
        if time.time()-t0 > timelimit: raise TimeoutError
        key=(tuple(sorted(rem)), k)
        if key in fail: return False
        if maxdisjoint([ms[i] for i in rem]) > k:
            fail.add(key); return False
        # pick mask with fewest patterns
        pick=min(rem, key=lambda i: bin(ms[i]).count('1'))
        m=ms[pick]
        tmp=m
        opts=[]
        while tmp:
            b=tmp & -tmp; opts.append(b.bit_length()-1); tmp^=b
        # sort options by coverage desc
        opts.sort(key=lambda p: -sum(1 for i in rem if (ms[i]>>p)&1))
        for p in opts:
            newrem=[i for i in rem if not ((ms[i]>>p)&1)]
            if can(newrem, k-1): return True
        fail.add(key); return False
    try:
        for t in range(max(3,lb), ub+1):
            if can(list(range(len(ms))), t): return t,'exact'
    except TimeoutError:
        return ub,'timeout(ub)'
    return ub,'shouldnot'

def run(n, name):
    t0=time.time()
    patterns, gf, gs, n_std, n_chi = build(n)
    out=dict(name=name, n_patterns=len(patterns), n_hands_std=n_std, n_hands_chiitoi_only=n_chi,
             n_groups_full=len(gf), n_groups_std_only=len(gs))
    tot=0; dist={}; kinds={}
    rows=[]
    for W,ms in gf.items():
        ub=greedy(ms)
        # randomized restarts to improve ub
        rnd=random.Random(12345)
        for _ in range(60):
            g=greedy(ms, rnd)
            if g<ub: ub=g
        ex,kind=exact_tau(ms, ub)
        tot+=ex; dist[ex]=dist.get(ex,0)+1; kinds[kind]=kinds.get(kind,0)+1
        rows.append({"W":sorted(W),"tau":ex,"kind":kind})
    out.update(sum_tau=tot, tau_dist={str(k):v for k,v in sorted(dist.items())},
               kinds=kinds, code_budget=n**3, secs=round(time.time()-t0,1))
    return out, rows

r9,rows9 = run(9,'suit'); print("SUIT:", json.dumps(r9,ensure_ascii=False), flush=True)
r7,rows7 = run(7,'honors'); print("HONORS:", json.dumps(r7,ensure_ascii=False), flush=True)
json.dump({"suit":r9,"honors":r7,"rows_suit":rows9[:500],"rows_honors":rows7[:500]},
          open(r"D:\DSH\MJ2\work\recon\flush_tau_exact.json","w"))
print("done")
