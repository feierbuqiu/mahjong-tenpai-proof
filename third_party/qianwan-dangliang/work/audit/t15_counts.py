# -*- coding: utf-8 -*-
"""t15_counts.py -- independent re-derivation of the two headline global counts:
   (i)  number of listening hands with a standard wait  (MODEL claims 54,747,045)
   (ii) number of hands that are both standard-type and chiitoi-wait (MODEL claims 32,676)
Method: every standard-type listening hand has a UNIQUE active part A and a
meld-decomposable filler F, so the count is sum over bases of #fillers; the overlap is
sum over bases whose A is chiitoi-compatible (counts<=2, exactly one 1) of the number of
all-even meld-decomposable fillers.
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjcore import *

D=os.path.dirname(os.path.abspath(__file__))
BASE=[0,9,18,27]; LEN=[9,9,9,7]
t0=time.time()

MELDS={}
for ci in range(4):
    lst=[]
    for i in range(LEN[ci]):
        v=[0]*34; v[BASE[ci]+i]=3; lst.append(tuple(v))
    if ci<3:
        for i in range(LEN[ci]-2):
            v=[0]*34
            for k in range(3): v[BASE[ci]+i+k]=1
            lst.append(v)
    MELDS[ci]=lst
def meld_multisets(ci,s):
    out=[]; ms=MELDS[ci]; acc=[0]*34
    def rec(i,left):
        if left==0:
            out.append(tuple(acc)); return
        for j in range(i,len(ms)):
            u=ms[j]; ok=True
            for t in range(34):
                if u[t] and acc[t]+u[t]>4: ok=False; break
            if not ok: continue
            for t in range(34): acc[t]+=u[t]
            rec(j,left-3)
            for t in range(34): acc[t]-=u[t]
    rec(0,s); return out
_MM={}
def mm(ci,s):
    key=(ci,s)
    if key not in _MM: _MM[key]=meld_multisets(ci,s)
    return _MM[key]
_NF={}
def nfill(inert,m):
    key=(tuple(inert),m)
    if key in _NF: return _NF[key]
    # convolution over categories
    counts=[len(mm(ci,s)) if s>0 else 1 for ci in inert for s in [0]]
    tot=0
    def rec(i,rem):
        nonlocal tot
        if i==len(inert):
            if rem==0: tot+=1
            return
        for s in range(0,min(rem,12)+1,3):
            rec(i+1,rem-s)
    # proper product
    res=0
    def rec2(i,rem,prod):
        nonlocal res
        if i==len(inert):
            if rem==0: res+=prod
            return
        for s in range(0,min(rem,12)+1,3):
            c=len(mm(inert[i],s))
            if c==0: continue
            rec2(i+1,rem-s,prod*c)
    rec2(0,m,1)
    _NF[key]=res; return res

def all2_fillers_count(inert,m):
    """number of meld-decomposable fillers whose every nonzero count equals 2"""
    tot=0
    def rec2(i,rem,prod):
        nonlocal tot
        if i==len(inert):
            if rem==0: tot+=prod
            return
        for s in range(0,min(rem,12)+1,3):
            c=0
            for v in mm(inert[i],s):
                if all(x in (0,2) for x in v): c+=1
            if c==0: continue
            rec2(i+1,rem-s,prod*c)
    rec2(0,m,1)
    return tot

def pair_decomp(v):
    for i in range(34):
        if v[i]>=2:
            w=list(v); w[i]-=2
            if melds_ok(tuple(w)): return True
    return False
def Wp_set(v):
    out=set()
    for t in range(34):
        if v[t]<4:
            w=list(v); w[t]+=1
            if pair_decomp(tuple(w)): out.add(t)
    return frozenset(out)
def Vset(v):
    out=set()
    for t in range(34):
        if v[t]<4:
            w=list(v); w[t]+=1
            if melds_ok(tuple(w)): out.add(t)
    return frozenset(out)
def one2(v):
    nz=[x for x in v if x]
    return (nz.count(1)==1 and all(x==2 for x in nz if x!=1))

tot_std=0; tot_overlap=0
# ---- I
for c in range(4):
    kinds=range(BASE[c],BASE[c]+LEN[c])
    for s in (1,4,7,10,13):
        m=13-s; inert=tuple(i for i in range(4) if i!=c)
        nf=nfill(inert,m); a2=all2_fillers_count(inert,m)
        for A in multisets(s, kinds):
            if not Wp_set(A): continue
            tot_std += nf
            if one2(A): tot_overlap += a2
    print("[%4.0fs] I cat=%d  std=%d overlap=%d"%(time.time()-t0,c,tot_std,tot_overlap), flush=True)
# ---- II
for c1 in range(4):
    for c2 in range(c1+1,4):
        inert=tuple(i for i in range(4) if i not in (c1,c2))
        for s1 in (2,5,8,11):
            for s2 in (2,5,8,11):
                if s1+s2 not in (4,7,10,13): continue
                m=13-s1-s2; nf=nfill(inert,m); a2=all2_fillers_count(inert,m)
                L1=[]; L2=[]
                for A in multisets(s1, range(BASE[c1],BASE[c1]+LEN[c1])):
                    L1.append((A, Vset(A), pair_decomp(A)))
                for A in multisets(s2, range(BASE[c2],BASE[c2]+LEN[c2])):
                    L2.append((A, Vset(A), pair_decomp(A)))
                for A1,V1,pd1 in L1:
                    for A2,V2,pd2 in L2:
                        Wstd=(V2 if pd1 else frozenset()) | (V1 if pd2 else frozenset())
                        if not Wstd: continue
                        tot_std += nf
                        A=tuple(A1[t]+A2[t] for t in range(34))
                        if one2(A): tot_overlap += a2
        print("[%4.0fs] II pair=(%d,%d) std=%d overlap=%d"%(time.time()-t0,c1,c2,tot_std,tot_overlap), flush=True)

chi=C(34,6)*28 if False else __import__("math").comb(34,6)*28
out={"standard_type_hands":tot_std,"claim":54747045,
     "standard_and_chiitoi_overlap":tot_overlap,"claim_overlap":32676,
     "chiitoi_hands":chi,"kokushi_hands":157,
     "derived_total":tot_std+chi-tot_overlap+157,"claim_total":92371838,
     "elapsed":round(time.time()-t0,1)}
json.dump(out,open(D+"/t15_counts.json","w"),ensure_ascii=False,indent=1)
print(json.dumps(out,ensure_ascii=False,indent=1))
