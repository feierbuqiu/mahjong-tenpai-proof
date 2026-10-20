# -*- coding: utf-8 -*-
"""t1b_k3_disproof.py (v2, fixed code representation) -- INDEPENDENT recomputation
of the k=3 disproof numbers for U={m2..m8}.
"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjcore import *

D = os.path.dirname(os.path.abspath(__file__))
t0=time.time()
def log(*a): print("[%6.1fs]"%(time.time()-t0), *a, flush=True)

U = tuple(range(1,8))          # m2..m8 (indices 1..7)
hands = list(multisets(13, U))
groups = {}
for h in hands:
    w = waits(h)
    if w:
        groups.setdefault(w, []).append(h)
N = len(groups)
log("U7 13-multisets:", len(hands), " N(U):", N, " U-wait-hands:", sum(len(v) for v in groups.values()))

codes = []
for v in multisets(3, U):
    codes.append(tuple(t for t in U for _ in range(v[t])))
codes = sorted(set(codes))
log("candidate 3-codes inside U:", len(codes))

def fits(h, c):
    need = {}
    for t in c: need[t]=need.get(t,0)+1
    return all(h[t]>=v for t,v in need.items())

# --- no-common-code classes + greedy hitting upper bound + exact tau (branch&bound)
def common_code(hs):
    for c in codes:
        if all(fits(h,c) for h in hs): return c
    return None

def greedy_tau(hs):
    rem=list(hs); n=0
    while rem:
        best=None;bestn=0
        for c in codes:
            k=sum(1 for h in rem if fits(h,c))
            if k>bestn: bestn=k;best=c
        if bestn==0: break
        n+=1
        rem=[h for h in rem if not fits(h,best)]
    return n

def exact_tau(hs):
    """branch and bound: minimum number of codes hitting all hands"""
    hs=list(hs)
    if not hs: return 0
    if common_code(hs): return 1
    # candidates: codes fitting the first hand
    cand=[c for c in codes if fits(hs[0],c)]
    best=[len(hs)]
    def rec(unchosen, used):
        if used>=best[0]: return
        if not unchosen:
            best[0]=used; return
        if used+1>=best[0]: return
        # bound: pairwise-incompatible count
        h0=unchosen[0]
        for c in cand:
            if not fits(h0,c): continue
            rest=[h for h in unchosen if not fits(h,c)]
            rec(rest, used+1)
            if best[0]==1: return
    rec(hs,0)
    return best[0]

def lb_pairwise(hs):
    """valid lower bound: size of a set of hands pairwise having no common code"""
    n=len(hs)
    incompat=[[False]*n for _ in range(n)]
    for i in range(n):
        for j in range(i+1,n):
            if sum(min(hs[i][t],hs[j][t]) for t in U) < 3:
                incompat[i][j]=incompat[j][i]=True
    order=sorted(range(n), key=lambda i:-sum(incompat[i]))
    best=0
    # greedy clique (on incompat graph)
    for s0 in order:
        cur=[s0]
        for j in order:
            if j in cur: continue
            if all(incompat[j][k] for k in cur): cur.append(j)
        best=max(best,len(cur))
    return best

taus_g=[]; taus_ex=[]; taus_lb=[]; nocommon=[]
for i,(w,hs) in enumerate(sorted(groups.items(), key=lambda kv: sorted(kv[0]))):
    if i%50==0: log("tau progress",i,"/",N)
    if common_code(hs) is None: nocommon.append(w)
    taus_g.append(greedy_tau(hs)); taus_lb.append(lb_pairwise(hs))
    taus_ex.append(None)
log("L(U):", len(nocommon))
res = {
 "U": [nm(t) for t in U], "U7_hands": len(hands), "N": N,
 "L": len(nocommon), "N_plus_L": N+len(nocommon), "budget_7pow3": 343,
 "sum_tau_greedy_upper": sum(taus_g),
 "sum_tau_pairwise_lower": sum(taus_lb),
 "tau_greedy_dist": {k: taus_g.count(k) for k in sorted(set(taus_g))},
 "tau_lb_dist": {k: taus_lb.count(k) for k in sorted(set(taus_lb))},
 "no_common_classes": [[nm(t) for t in sorted(w)] for w in nocommon],
 "class_sizes": sorted(len(v) for v in groups.values()),
}
log("sum tau greedy upper:", sum(taus_g), " sum pairwise lb:", sum(taus_lb))
json.dump(res, open(D+"/t1b_k3_disproof.json","w"), ensure_ascii=False, indent=1)
print(json.dumps({k:v for k,v in res.items() if k not in ("no_common_classes","class_sizes")}, ensure_ascii=False, indent=1))
