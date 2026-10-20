# -*- coding: utf-8 -*-
"""t4_subuniverse.py v2 -- EXHAUSTIVE coverage sweep over complete 13-tile hand spaces
inside chosen tile subsets (not sampling).  Sparse code representation for speed."""
import sys, os, json, time, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjcore import *
from multiprocessing import Pool

D = os.path.dirname(os.path.abspath(__file__))
PLANF = "D:/DSH/MJ2/work/verify/plan_k4_FINAL.json"

def load_plan():
    P = json.load(open(PLANF, encoding="utf-8"))
    plan = {}
    for r in P["plan"]:
        W = frozenset(nm_idx(x) for x in r["W"])
        cs = []
        for c in r["codes"]:
            cnt = collections.Counter(nm_idx(t) for t in c)
            cs.append(tuple(sorted(cnt.items(), key=lambda kv: -kv[1])))
        plan[W] = cs
    return plan

PLAN=None
def init():
    global PLAN
    PLAN=load_plan()

def contains(h, code):
    for t,v in code:
        if h[t] < v: return False
    return True

def sweep(arg):
    tag,kinds,cap = arg
    hands=0; listening=0; missing=[]; uncovered=[]; witness={}
    for h in multisets(13, kinds, cap=cap):
        if cap < 4 and max(h) > cap: continue
        hands+=1
        w=waits(h)
        if not w: continue
        listening+=1
        cs=PLAN.get(w)
        if cs is None:
            if len(missing)<10: missing.append(hand_str(h))
            continue
        hit=None
        for c in cs:
            if contains(h,c): hit=c; break
        if hit is not None:
            witness.setdefault(w, hand_str(h))
        else:
            if len(uncovered)<10: uncovered.append({"hand":hand_str(h),"W":[nm(t) for t in sorted(w)]})
    return {"tag":tag,"kinds":[nm(t) for t in kinds],"cap":cap,"hands":hands,"listening":listening,
            "classes":len(witness),"missing":missing,"uncovered":uncovered,
            "witness":{",".join(nm(t) for t in sorted(w)):h for w,h in witness.items()}}

SETS = [
  ("m_suit", tuple(range(0,9)),4),
  ("p_suit", tuple(range(9,18)),4),
  ("s_suit", tuple(range(18,27)),4),
  ("honors", tuple(range(27,34)),4),
  ("U7_m2m8", tuple(range(1,8)),4),
  ("m1_5+p1_5", tuple(range(0,5))+tuple(range(9,14)),4),
  ("m1_9+z1", tuple(range(0,9))+ (27,),4),
  ("m1_9+z1_3", tuple(range(0,9))+ (27,28,29),4),
  ("m2_8+z1_4", tuple(range(1,8))+ (27,28,29,30),4),
  ("m1_4+p1_4+s1_4", tuple(range(0,4))+tuple(range(9,13))+tuple(range(18,22)),4),
  ("m1_6+p1_6", tuple(range(0,6))+tuple(range(9,15)),4),
  ("honors+m1_5", tuple(range(27,34))+tuple(range(0,5)),4),
  ("m1_9+p1_3+z1", tuple(range(0,9))+tuple(range(9,12))+(27,),4),
  ("m2_9+p1_6", tuple(range(1,9))+tuple(range(9,15)),4),
  ("chi_shaped_m1_9_p1_4_z1", tuple(range(0,9))+tuple(range(9,13))+(27,),2),
  ("chi_shaped_honors+m1_9", tuple(range(27,34))+tuple(range(0,9)),2),
]

if __name__=="__main__":
    t0=time.time()
    res=[]
    with Pool(6, initializer=init) as pool:
        for r in pool.imap_unordered(sweep, SETS):
            res.append(r)
            print("%-24s hands=%7d listening=%6d classes=%4d missing=%d uncovered=%d (%.0fs)" %
                  (r["tag"],r["hands"],r["listening"],r["classes"],len(r["missing"]),len(r["uncovered"]),time.time()-t0), flush=True)
            for x in r["uncovered"][:3]: print("     UNCOVERED", x, flush=True)
            for x in r["missing"][:3]: print("     MISSING-CLASS", x, flush=True)
    out={"plan":PLANF,"sets":res,"elapsed":round(time.time()-t0,1)}
    json.dump(out, open(D+"/t4_subuniverse.json","w"), ensure_ascii=False, indent=1)
    tot_h=sum(r["hands"] for r in res); tot_l=sum(r["listening"] for r in res)
    print("TOTAL hands=%d listening=%d missing_shapes=%d uncovered=%d" % (tot_h,tot_l,sum(len(r["missing"]) for r in res),sum(len(r["uncovered"]) for r in res)))
