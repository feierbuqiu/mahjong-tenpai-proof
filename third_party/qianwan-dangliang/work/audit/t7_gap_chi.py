# -*- coding: utf-8 -*-
"""t7_gap_chi.py (v2, 34-vector logic) -- EXHAUSTIVE check of the region the team's
pipeline structurally cannot test:
    H = A (+) F,  A chiitoi-compatible active part (counts<=2, exactly one count 1 => z),
    F all-even (counts in {0,2}) and NOT meld-decomposable.
Then W_std(H)=empty (F is not meld-decomposable) and W_chiitoi(H)={z}, so H belongs to
the pure tanki class {z}.  The team's block coverage / per-class sampling only build F
from meld-decomposable fillers, and their chi-block check tests such hands against
S_{Wp(A) union {z}} -- a different class -- never against S_{{z}}.
"""
import sys, os, json, time, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from mjcore import *
from collections import Counter

D=os.path.dirname(os.path.abspath(__file__))
BASE=[0,9,18,27]; LEN=[9,9,9,7]
PLANF="D:/DSH/MJ2/work/verify/plan_k4_FINAL.json"
P=json.load(open(PLANF,encoding="utf-8"))
PLAN={}
for r in P["plan"]:
    W=frozenset(nm_idx(x) for x in r["W"])
    PLAN[W]=[tuple(sorted(Counter(nm_idx(t) for t in c).items())) for c in r["codes"]]

def one2_vecs(c, size):
    """34-vectors with support in category c, counts<=2, exactly one count 1, rest 2"""
    out=[]
    for v in multisets(size, range(BASE[c], BASE[c]+LEN[c]), cap=2):
        nz=[x for x in v if x]
        if nz.count(1)==1 and all(x==2 for x in nz if x!=1): out.append(v)
    return out

def a2_vecs(c, size):
    out=[]
    for v in multisets(size, range(BASE[c], BASE[c]+LEN[c]), cap=2):
        nz=[x for x in v if x]
        if nz and all(x==2 for x in nz): out.append(v)
    return out

def meld_decomp_kinds(mask):
    v=[0]*34; m=int(mask); t=0
    while m:
        if m&1: v[t]=2
        m>>=1; t+=1
    return melds_ok(tuple(v))

def check_config(A, inert, m, z, report, tag):
    codes=PLAN.get(frozenset([z]))
    if codes is None:
        report.append({"err":"class {z} not in plan","z":nm(z)}); return 0,0,1
    R=[]
    for cod in codes:
        r=0; ok=True
        for t,v in cod:
            need=v-A[t]
            if need<0: ok=False; break
            if need==0: continue
            if need>2 or (0 if t<9 else (1 if t<18 else (2 if t<27 else 3))) not in inert: ok=False; break
            r |= (1<<t)
        if ok: R.append(r)
    if not R:
        report.append({"err":"NO code can fit ANY gap hand for this A","z":nm(z),"A":hand_str(A),"tag":tag})
        return 0,0,1
    kinds=[]
    for ci in inert: kinds += list(range(BASE[ci], BASE[ci]+LEN[ci]))
    half=m//2
    Rarr=np.array(R,dtype=np.int64)
    tot=gap=bad=0
    chunk=[]
    for combo in itertools.combinations(kinds, half):
        mask=0
        for t in combo: mask |= (1<<t)
        chunk.append(mask)
        if len(chunk)>=150000:
            t2,g2,b2=_mpass(chunk,Rarr,report,z,tag)
            tot+=t2; gap+=g2; bad+=b2; chunk=[]
    if chunk:
        t2,g2,b2=_mpass(chunk,Rarr,report,z,tag)
        tot+=t2; gap+=g2; bad+=b2
    return tot,gap,bad

def _mpass(chunk,Rarr,report,z,tag):
    F=np.array(chunk,dtype=np.int64)
    nonmeld=np.array([not meld_decomp_kinds(x) for x in chunk],dtype=bool)
    good=np.zeros(len(F),dtype=bool)
    for r in Rarr:
        good |= (F & int(r))==int(r)
    bad = nonmeld & (~good)
    if bad.any():
        idx=int(np.argmax(bad))
        report.append({"err":"UNCOVERED gap hand","z":nm(z),"tag":tag,
                       "F_kinds":[nm(t) for t in range(34) if (int(F[idx])>>t)&1]})
    return int(nonmeld.sum()), int(nonmeld.sum()-bad.sum()), int(bad.sum())

if __name__=="__main__":
    t0=time.time()
    report=[]; grand=grand_gap=grand_bad=0
    for c in range(4):
        inert=tuple(i for i in range(4) if i!=c)
        for size in (1,7,13):
            m=13-size
            if m%2: continue
            nA=0
            for X in one2_vecs(c,size):
                A=tuple(X)
                z=[t for t in range(34) if A[t]==1][0]
                tot,gap,bad=check_config(A,inert,m,z,report,"I-c%d-s%d"%(c,size))
                grand+=tot; grand_gap+=gap; grand_bad+=bad; nA+=1
            print("[%5.0fs] I cat=%d size=%d A's=%d  F=%d verified=%d bad=%d" % (time.time()-t0,c,size,nA,grand,grand_gap,grand_bad), flush=True)
    for c1 in range(4):
        for c2 in range(c1+1,4):
            inert=tuple(i for i in range(4) if i not in (c1,c2))
            for (sc,sd) in ((c1,c2),(c2,c1)):
                for s1,s2 in ((2,5),(5,2)):
                    m=13-s1-s2
                    if m%2 or m==0: continue
                    for X1 in one2_vecs(sc,s1):
                        z=[t for t in range(34) if X1[t]==1][0]
                        for X2 in a2_vecs(sd,s2):
                            A=tuple(X1[t]+X2[t] for t in range(34))
                            tot,gap,bad=check_config(A,inert,m,z,report,"II-c%d-s%d"%(sc,s1))
                            grand+=tot; grand_gap+=gap; grand_bad+=bad
                print("[%5.0fs] II pair=(%d,%d) F=%d verified=%d bad=%d" % (time.time()-t0,c1,c2,grand,grand_gap,grand_bad), flush=True)
    out={"gap_hands_checked":grand,"covered":grand_gap,"uncovered":grand_bad,
         "counterexamples":report[:50],"elapsed":round(time.time()-t0,1)}
    json.dump(out, open(D+"/t7_gap_chi.json","w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False)[:3000])
