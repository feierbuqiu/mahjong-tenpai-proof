# -*- coding: utf-8 -*-
"""t11_chiitoi_exact.py -- EXACT, exhaustive verification of the whole chiitoi family.

All chiitoi listening hands are H = 2K + z with K a 6-subset of kinds, z not in K.
* Phase A: for every z, search ALL K (33 choose 6) for a hand not covered by S_{{z}}
  (exact bitmask DFS).  A hand with F=2K not meld-decomposable has class exactly {z},
  so this phase alone verifies every such hand.
* Phase B: for every K with 2K meld-decomposable (these are K = two disjoint runs,
  each doubled) and every z not in K, compute the true class with the independent
  engine and check coverage by that class's codes.
Together: every chiitoi listening hand is checked exactly.
"""
import sys, os, json, time, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjcore import *
from collections import Counter

D=os.path.dirname(os.path.abspath(__file__))
PLANF="D:/DSH/MJ2/work/verify/plan_k4_FINAL.json"
P=json.load(open(PLANF,encoding="utf-8"))
PLAN={}
for r in P["plan"]:
    W=frozenset(nm_idx(x) for x in r["W"])
    PLAN[W]=[tuple(sorted(Counter(nm_idx(t) for t in c).items())) for c in r["codes"]]

t0=time.time()
out={}
# ---------------- Phase A
uncovered=[]
for z in range(34):
    W=frozenset([z]); codes=PLAN.get(W)
    if codes is None:
        uncovered.append({"z":nm(z),"reason":"class {z} absent from plan"}); continue
    sup=set()
    for cod in codes:
        d=dict(cod)
        if d.get(z,0)>1: continue
        if any(v>2 for t,v in cod if t!=z): continue
        m=0
        for t,v in cod:
            if t!=z: m |= (1<<t)
        if m: sup.add(m)
    sups=sorted(sup, key=lambda x: bin(x).count("1"))
    allowed=[t for t in range(34) if t!=z]
    # remove tiles that are single-tile supports (a size-1 support makes any K containing it covered)
    allowed=[t for t in allowed if not any(s==(1<<t) for s in sups)]
    n=len(allowed)
    found=[None]
    def rec(i, chosen_mask, cnt):
        if cnt==6: return True
        if n-i < 6-cnt: return False
        t=allowed[i]
        cm=chosen_mask | (1<<t)
        bad=False
        for s in sups:
            if s & ~cm == 0: bad=True; break
        if not bad:
            if rec(i+1, cm, cnt+1):
                found[0]=cm; return True
        return rec(i+1, chosen_mask, cnt)
    ok=rec(0,0,0)
    if ok:
        K=[t for t in range(34) if (found[0]>>t)&1]
        h=[0]*34
        for t in K: h[t]=2
        h[z]=1
        h=tuple(h)
        uncovered.append({"z":nm(z),"K":[nm(t) for t in K],"hand":hand_str(h),"W":[nm(t) for t in sorted(waits(h))],
                          "covered_by_plan": None})
    if z%5==0: print("[%5.0fs] phaseA z=%d" % (time.time()-t0, z), flush=True)
out["phaseA_uncovered_count"]=len(uncovered)
out["phaseA_uncovered"]=uncovered[:20]
print("phaseA: uncovered z count =", len(uncovered), flush=True)

# ---------------- Phase B
def runs():
    out=[]
    for ci,(off,L) in enumerate(((0,9),(9,9),(18,9),(27,7))):
        if ci==3: continue
        for st in range(L-2):
            out.append(frozenset(off+st+k for k in range(3)))
    return out
R=runs()
badB=[]
checkedB=0
for r1,r2 in itertools.combinations(R,2):
    if r1 & r2: continue
    Kmb = (1<<min(r1)) | (1<<min(r2))
    Kset = sorted(r1|r2)
    F=[0]*34
    for t in Kset: F[t]=2
    assert melds_ok(tuple(F))
    for z in range(34):
        if z in r1 or z in r2: continue
        h=list(F); h[z]+=1
        if h[z]!=1: continue
        h=tuple(h)
        checkedB+=1
        w=waits(h)
        cs=PLAN.get(w)
        if cs is None:
            badB.append({"hand":hand_str(h),"W":[nm(t) for t in sorted(w)],"err":"class not in plan"}); continue
        hit=any(all(h[t]>=v for t,v in cod) for cod in cs)
        if not hit:
            badB.append({"hand":hand_str(h),"W":[nm(t) for t in sorted(w)],"err":"uncovered"})
out["phaseB_hands_checked"]=checkedB
out["phaseB_bad"]=badB[:20]
out["phaseB_bad_count"]=len(badB)
out["elapsed"]=round(time.time()-t0,1)
print("phaseB: checked %d hands, bad=%d" % (checkedB, len(badB)))
for b in badB[:10]: print("   ", b)
json.dump(out, open(D+"/t11_chiitoi_exact.json","w"), ensure_ascii=False, indent=1)
