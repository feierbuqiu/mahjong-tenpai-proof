# -*- coding: utf-8 -*-
"""t1d_flush_lb.py -- independent recomputation of the flush sub-universe transversals
tau_1 and tau_2 for the 387 single-suit classes (k=1,2 lower bounds)."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjcore import *
D=os.path.dirname(os.path.abspath(__file__))
t0=time.time()
def log(*a): print("[%5.0fs]"%(time.time()-t0), *a, flush=True)

M = range(9)
hands = [h for h in multisets(13, M)]
groups = {}
for h in hands:
    w = waits(h)
    if w: groups.setdefault(w, []).append(h)
log("flush classes:", len(groups), "wait hands:", sum(len(v) for v in groups.values()))

# k=1 exact
codes1 = [(t,) for t in range(9)]
def fit1(h,c): return h[c[0]] >= 1
def common(hs, codes, fit):
    for c in codes:
        if all(fit(h,c) for h in hs): return c
    return None
tau1 = {}
for w,hs in groups.items():
    if common(hs, codes1, fit1) is not None: tau1[w]=1
    else:
        # try size 2
        found=False
        for i in range(9):
            for j in range(i+1,9):
                if all(fit1(h,codes1[i]) or fit1(h,codes1[j]) for h in hs):
                    found=True; break
            if found: break
        tau1[w]=2 if found else 3
log("sum tau1:", sum(tau1.values()), " no-common:", sum(1 for v in tau1.values() if v>1))

# k=2 exact-ish: codes = ordered pairs within the suit
codes2 = [(a,b) for a in range(9) for b in range(9)]
def fit2(h,c):
    a,b=c
    if h[a] < 1: return False
    if a==b: return h[b] >= 2
    return h[b] >= 1
def pairwise_lb(hs):
    n=len(hs)
    # a set of hands pairwise having no common code -> tau >= size
    adj=[[False]*n for _ in range(n)]
    for i in range(n):
        for j in range(i+1,n):
            # common code exists iff exists ordered pair (a,b) fitting both
            # = exists a,b with min(h1[a],h2[a])>=1 (and mult) -> just check max
            ok=False
            for a in range(9):
                if hs[i][a]<1 or hs[j][a]<1: continue
                for b in range(9):
                    need_a = 1; need_b = 1
                    if a==b: need_a=2
                    if hs[i][a]>=need_a and hs[i][b]>=1 and hs[j][a]>=need_a and hs[j][b]>=1:
                        ok=True; break
                if ok: break
            if not ok: adj[i][j]=adj[j][i]=True
    order=sorted(range(n), key=lambda i:-sum(adj[i]))
    best=0
    for s0 in order:
        cur=[s0]
        for j in order:
            if j in cur: continue
            if all(adj[j][k] for k in cur): cur.append(j)
        best=max(best,len(cur))
    return best
def greedy(hs):
    rem=list(hs); n=0
    while rem:
        h0=rem[0]
        best=None;bestn=0
        for c in codes2:
            if not fit2(h0,c): continue
            k=sum(1 for h in rem if fit2(h,c))
            if k>bestn: bestn=k;best=c
        n+=1
        rem=[h for h in rem if not fit2(h,best)]
    return n
lb2={}; ub2={}
for w,hs in groups.items():
    lb2[w]=pairwise_lb(hs); ub2[w]=greedy(hs)
log("sum tau2 lb(clique):", sum(lb2.values()), " sum ub(greedy):", sum(ub2.values()))
res={"n_classes":len(groups), "sum_tau1":sum(tau1.values()), "tau1_hist":{k:list(tau1.values()).count(k) for k in set(tau1.values())},
     "sum_tau2_lb_clique":sum(lb2.values()), "sum_tau2_ub_greedy":sum(ub2.values()),
     "budget_k1":9,"budget_k2":81,"budget_k3":729,"budget_k4":6561,
     "cert_claims":{"k1":427,"k2_lb":447,"k2_ub":457}}
json.dump(res, open(D+"/t1d_flush_lb.json","w"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
