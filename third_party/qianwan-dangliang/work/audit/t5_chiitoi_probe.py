# -*- coding: utf-8 -*-
"""t5_chiitoi_probe.py -- adversarial probe of a suspected gap:
hands H that are 6 pairs + 1 single where the 'inert' filler is NOT meld-decomposable
have class {z} (pure chiitoi wait), NOT Wp(A) union {z}.
The team's block check appears to test such hands only against the wrong class's codes.
Here we hunt for an actually uncovered hand.
"""
import sys, os, json, random, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjcore import *

PLANF = "D:/DSH/MJ2/work/verify/plan_k4_FINAL.json"
P = json.load(open(PLANF, encoding="utf-8"))
PLAN = {}
for r in P["plan"]:
    W = frozenset(nm_idx(x) for x in r["W"])
    PLAN[W] = [tuple(nm_idx(t) for t in c) for c in r["codes"]]

def covered(h):
    w = waits(h)
    if not w: return ("nowait", None)
    cs = PLAN.get(w)
    if cs is None: return ("missing_class", w)
    for c in cs:
        need = {}
        for t in c: need[t]=need.get(t,0)+1
        if all(h[t]>=v for t,v in need.items()): return ("ok", w)
    return ("uncovered", w)

# --- the targeted example: A=1122334m (one odd), F = 11p 99p 11s (all counts 2, not melds)
h = from_str("1122334m") + from_str("11p") + from_str("99p") + from_str("11s")
print("target hand:", hand_str(h), "sum", sum(h))
print("W =", [nm(t) for t in sorted(waits(h))], "std =", [nm(t) for t in sorted(waits_std(h))],
      "chiitoi =", win_chiitoi(add(h, 3)), " 4m idx=3")
print("plan lookup:", covered(h))

# --- exhaustive family: A one2 in one suit + three arbitrary pairs elsewhere, all-2 filler
bad = []
t0=time.time()
# A: multiset in one suit of sizes 1,7,13 with counts<=2 and exactly one count==1 rest==2
def one2_vectors(L, s):
    out=[]
    for combo in multisets(s, range(L), cap=2):
        nz=[combo[i] for i in range(L) if combo[i]]
        if nz.count(1)==1 and all(x==2 for x in nz if x!=1): out.append(combo)
    return out

def pair_multisets(kinds, npairs):
    """all ways to pick npairs distinct kinds from kinds"""
    from itertools import combinations
    for cmb in combinations(kinds, npairs):
        v=[0]*34
        for t in cmb: v[t]=2
        yield tuple(v)

tiles_m = list(range(9))
n_checked=0; n_singleton=0
for s in (1,7,13):
    for X in one2_vectors(9, s):
        A = [0]*34
        for i in range(9):
            A[i]=X[i]
        rem = 13-s   # even? s odd -> rem even; pairs needed = rem//2
        npairs = rem//2
        other_kinds = [t for t in range(34) if t not in range(9)]
        for F in pair_multisets(other_kinds, npairs):
            h = tuple(A[i]+F[i] for i in range(34))
            if sum(h)!=13 or max(h)>2: continue
            n_checked+=1
            w = waits(h)
            if w==frozenset([X.index(1)]):
                n_singleton+=1
            st,ww = covered(h)
            if st!="ok":
                bad.append((hand_str(h), [nm(t) for t in sorted(w)], st))
        if time.time()-t0 > 40:
            break
    if time.time()-t0 > 40: break
print("family checked=%d singleton-class=%d failures=%d  (%.0fs)" % (n_checked, n_singleton, len(bad), time.time()-t0))
for b in bad[:20]: print("   FAIL", b)
json.dump({"checked":n_checked,"singleton":n_singleton,"bad":bad[:100]}, open("D:/DSH/MJ2/work/audit/t5_chiitoi_probe.json","w"), ensure_ascii=False, indent=1)
