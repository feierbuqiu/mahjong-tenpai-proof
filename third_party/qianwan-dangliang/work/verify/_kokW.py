
import sys, itertools
sys.path.insert(0,"work/verify")
import indep_core as IC
HON=["E","S","W","N","Haku","Hatsu","Chun"]
def nm(t): return ("%d%s"%(t%9+1,"mps"[t//9])) if t<27 else HON[t-27]
ORPH=[0,8,9,17,18,26]+list(range(27,34))
def vec(ts):
    v=[0]*34
    for t in ts: v[t]+=1
    return v
# strict 13-orphan hand
H0=vec(ORPH)
print("strict 13 orphans W:", sorted(nm(t) for t in IC.compute_W(H0)), "|W|=",len(IC.compute_W(H0)))
# dup variants for missing 1m
for d in ORPH:
    if d==0: continue
    ts=[o for o in ORPH if o!=0]+[d]
    Hs=vec(ts)
    W=IC.compute_W(Hs)
    print("miss 1m, dup %-2s : |W|=%2d  W=%s" % (nm(d), len(W), sorted(nm(t) for t in W)[:6]))
    if len(W)<=3: print("      full W:", sorted(nm(t) for t in W))
