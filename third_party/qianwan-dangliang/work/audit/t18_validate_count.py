# -*- coding: utf-8 -*-
"""t18_validate_count.py v2 -- validate the structural counting method (t15) against
brute force on small restricted tile universes."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjcore import *
D=os.path.dirname(os.path.abspath(__file__))
def cat(t): return 0 if t<9 else (1 if t<18 else (2 if t<27 else 3))

def brute(S):
    n=0; nstd=0
    for h in multisets(13, sorted(S)):
        if waits(h): n+=1
        if waits_std(h): nstd+=1
    return n,nstd

def structural(S):
    S=set(S)
    # meld multisets of size s inside category c, using only tiles of S
    _mm={}
    def mm(c,s):
        key=(c,s)
        if key in _mm: return _mm[key]
        if s==0:
            _mm[key]=[tuple([0]*34)]; return _mm[key]
        ms=[]
        T=[t for t in sorted(S) if cat(t)==c]
        for t in T:
            v=[0]*34; v[t]=3; ms.append(tuple(v))
        if c<3:
            for t in T:
                if t%9<=6 and (t+1) in S and (t+2) in S:
                    v=[0]*34
                    for k in range(3): v[t+k]=1
                    ms.append(tuple(v))
        out=set(); acc=[0]*34
        def rec(i,left):
            if left==0: out.add(tuple(acc)); return
            for j in range(i,len(ms)):
                u=ms[j]; ok=True
                for t in range(34):
                    if u[t] and acc[t]+u[t]>4: ok=False; break
                if not ok: continue
                for t in range(34): acc[t]+=u[t]
                rec(j,left-3)
                for t in range(34): acc[t]-=u[t]
        rec(0,s)
        _mm[key]=[tuple(x) for x in out]; return _mm[key]
    _nf={}
    def nfill(cats,m):
        key=(tuple(cats),m)
        if key in _nf: return _nf[key]
        res=0
        def rec2(i,rem,prod):
            nonlocal res
            if i==len(cats):
                if rem==0: res+=prod
                return
            for s in range(0,min(rem,12)+1,3):
                c=len(mm(cats[i],s))
                if c==0: continue
                rec2(i+1,rem-s,prod*c)
        rec2(0,m,1)
        _nf[key]=res; return res
    def pd(v):
        for i in range(34):
            if v[i]>=2:
                w=list(v); w[i]-=2
                if melds_ok(tuple(w)): return True
        return False
    def Wp_nonempty(v):
        for x in range(34):
            if v[x]<4:
                w=list(v); w[x]+=1
                if pd(tuple(w)): return True
        return False
    def Vset(v):
        return {x for x in range(34) if v[x]<4 and melds_ok(tuple(v[t]+1 if t==x else v[t] for t in range(34)))}
    total=0
    for c in range(4):
        T1=[t for t in S if cat(t)==c]
        for s in (1,4,7,10,13):
            for A in multisets(s, sorted(T1)):
                if not Wp_nonempty(A): continue
                total+=nfill(tuple(i for i in range(4) if i!=c), 13-s)
    for c1 in range(4):
        for c2 in range(c1+1,4):
            inert=tuple(i for i in range(4) if i not in (c1,c2))
            for s1 in (2,5,8,11):
                for s2 in (2,5,8,11):
                    if s1+s2 not in (4,7,10,13): continue
                    L1=[(A,Vset(A),pd(A)) for A in multisets(s1, sorted(t for t in S if cat(t)==c1))]
                    L2=[(A,Vset(A),pd(A)) for A in multisets(s2, sorted(t for t in S if cat(t)==c2))]
                    for A1,V1,P1 in L1:
                        for A2,V2,P2 in L2:
                            if not ((V2 if P1 else set())|(V1 if P2 else set())): continue
                            total+=nfill(inert,13-s1-s2)
    return total

TESTS=[tuple(range(0,3))+tuple(range(9,12)),
       tuple(range(0,5))+(9,),
       (0,8,9,17,18,26,27,33),
       tuple(range(0,4))+tuple(range(9,13)),
       (0,1,2,3,4,5,6,7,8),
       tuple(range(0,6))+tuple(range(9,15))]
out=[]
for S in TESTS:
    t0=time.time()
    b=list(brute(S)); s=structural(S)
    r={"S":[nm(t) for t in S],"listening":b[0],"brute_standard":b[1],"structural":s,"match":b[1]==s,"sec":round(time.time()-t0,1)}
    out.append(r); print(r, flush=True)
json.dump({"tests":out,"model_claim":54747045,"my_full_count":54793476,"difference":54793476-54747045},
          open(D+"/t18_validate_count.json","w"),ensure_ascii=False,indent=1)
