# -*- coding: utf-8 -*-
"""t6_base_scan.py (v2, 34-vector logic) -- independent enumeration of every standard
active part (A) that can carry a non-empty standard wait set, grouped by the class it
generates.  Checks (a) class census: every such class keys a plan entry,
(b) "easy coverage": some plan code of that class is already a sub-multiset of A.
"""
import sys, os, json, time, collections, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjcore import *
from collections import Counter

D=os.path.dirname(os.path.abspath(__file__))
BASE=[0,9,18,27]; LEN=[9,9,9,7]
PLANF="D:/DSH/MJ2/work/verify/plan_k4_FINAL.json"
P=json.load(open(PLANF,encoding="utf-8"))
PLAN={}
for r in P["plan"]:
    W=frozenset(nm_idx(x) for x in r["W"])
    PLAN[W]=[tuple(Counter(nm_idx(t) for t in c).items()) for c in r["codes"]]
print("plan classes:", len(PLAN), flush=True)

def cat_of(t): return 0 if t<9 else (1 if t<18 else (2 if t<27 else 3))

def pair_decomp(v):
    for i in range(34):
        if v[i]>=2:
            w=list(v); w[i]-=2
            if melds_ok(tuple(w)): return True
    return False

def Vset(v):
    out=set()
    for t in range(34):
        if v[t]<4:
            w=list(v); w[t]+=1
            if melds_ok(tuple(w)): out.add(t)
    return frozenset(out)

def Wp_set(v):
    out=set()
    for t in range(34):
        if v[t]<4:
            w=list(v); w[t]+=1
            if pair_decomp(tuple(w)): out.add(t)
    return frozenset(out)

def flags(v):
    nz=[x for x in v if x]
    one2 = (nz.count(1)==1 and all(x==2 for x in nz if x!=1))
    a2 = bool(nz) and all(x==2 for x in nz)
    return one2,a2

def easy(W,A):
    cs=PLAN.get(W)
    if cs is None: return None
    for cod in cs:
        if all(A[t]>=v for t,v in cod): return True
    return False

t0=time.time()
CLASS=collections.Counter()
hard=[]; missing=[]
I_bases=I_easy=0
# ---------------- I type
for c in range(4):
    kinds=range(BASE[c],BASE[c]+LEN[c])
    for s in (1,4,7,10,13):
        for A in multisets(s, kinds):
            Wp=Wp_set(A)
            if not Wp: continue
            one2,a2=flags(A)
            z=[t for t in range(34) if A[t]==1]
            tags=[(Wp,"nochi")]
            if one2: tags.append((frozenset(Wp)|{z[0]},"chi"))
            for W,mode in tags:
                W=frozenset(W); I_bases+=1; CLASS[W]+=1
                e=easy(W,A)
                if e is None: missing.append({"kind":"I","c":c,"s":s,"W":[nm(t) for t in sorted(W)]})
                elif e: I_easy+=1
                else: hard.append({"kind":"I","c":c,"s":s,"s_":s,"mode":mode,"W":[nm(t) for t in sorted(W)],"A":hand_str(A)})
    print("[%5.0fs] I cat=%d bases=%d easy=%d hard=%d missing=%d"%(time.time()-t0,c,I_bases,I_easy,len(hard),len(missing)), flush=True)

# ---------------- II type
II_bases=II_easy=0
for c1 in range(4):
    for c2 in range(c1+1,4):
        for s1 in (2,5,8,11):
            for s2 in (2,5,8,11):
                if s1+s2 not in (4,7,10,13): continue
                def build(c,s):
                    g=collections.defaultdict(list)
                    for A in multisets(s, range(BASE[c],BASE[c]+LEN[c])):
                        one2,a2=flags(A)
                        g[(pair_decomp(A), Vset(A), one2, a2)].append(A)
                    return g
                G1=build(c1,s1); G2=build(c2,s2)
                for k1,xs1 in G1.items():
                    pd1,V1,one21,a21 = k1
                    for k2,xs2 in G2.items():
                        pd2,V2,one22,a22 = k2
                        Wstd = (set(V2) if pd1 else set()) | (set(V1) if pd2 else set())
                        if not Wstd: continue
                        ps = (one21 and a22) or (a21 and one22)
                        Wstd_f = frozenset(Wstd)
                        for A1 in xs1:
                            for A2 in xs2:
                                A=tuple(A1[t]+A2[t] for t in range(34))
                                tags=[(Wstd_f,"nochi")]
                                if ps:
                                    z=[t for t in range(34) if A[t]==1][0]
                                    tags.append((Wstd_f|{z},"chi"))
                                for W,mode in tags:
                                    II_bases+=1; CLASS[W]+=1
                                    e=easy(W,A)
                                    if e is None: missing.append({"kind":"II","c1":c1,"c2":c2,"s1":s1,"s2":s2,"W":[nm(t) for t in sorted(W)]})
                                    elif e: II_easy+=1
                                    else: hard.append({"kind":"II","c1":c1,"c2":c2,"s1":s1,"s2":s2,"mode":mode,"W":[nm(t) for t in sorted(W)],"A":hand_str(A)})
        print("[%5.0fs] II pair=(%d,%d) bases=%d easy=%d hard=%d missing=%d"%(time.time()-t0,c1,c2,II_bases,II_easy,len(hard),len(missing)), flush=True)

rep={"plan_classes":len(PLAN),
     "standard_classes":len(CLASS),
     "I_bases":I_bases,"I_easy":I_easy,"II_bases":II_bases,"II_easy":II_easy,
     "hard_bases":len(hard),"missing_class_events":len(missing),
     "n_standard_classes_not_in_plan":sum(1 for w in CLASS if w not in PLAN),
     "sample_missing":missing[:20],
     "plan_classes_not_standard_root":sorted([[nm(t) for t in sorted(w)] for w in PLAN if w not in CLASS], key=lambda x: (len(x),x))[:80],
     "n_plan_classes_not_standard_root":sum(1 for w in PLAN if w not in CLASS),
     "elapsed":round(time.time()-t0,1)}
json.dump(rep, open(D+"/t6_base_scan.json","w"), ensure_ascii=False, indent=1)
json.dump(hard, open(D+"/t6_hard_bases.json","w"), ensure_ascii=False)
for k,v in rep.items():
    if k in ("sample_missing","plan_classes_not_standard_root"): continue
    print(k,"=",v)
print("classes never reached as standard roots (first 40):")
for x in rep["plan_classes_not_standard_root"][:40]: print("   ", ",".join(x))
