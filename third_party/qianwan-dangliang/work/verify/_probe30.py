
import sys, json, itertools
sys.path.insert(0,"work/verify")
import indep_core as IC
HON=["E","S","W","N","Haku","Hatsu","Chun"]
def nm(t): return ("%d%s"%(t%9+1,"mps"[t//9])) if t<27 else HON[t-27]
P=json.load(open("work/verify/plan_k4_final.json",encoding="utf-8"))
plan={}
for r in P["plan"]: plan[frozenset(r["W"])]=[tuple(c) for c in r["codes"]]
# canonical hand: 123m 456m 123p 456p 7p
H=[0,1,2,3,4,5,9,10,11,12,13,14,15]
v=[0]*34
for t in H: v[t]+=1
W=IC.compute_W(v)
print("hand H =", ",".join(nm(t) for t in H))
print("W(H) =", sorted(nm(t) for t in W), "|W|=",len(W))
key=frozenset(W)
codes=plan.get(key,[])
print("plan codes for that W:",len(codes))
cov=[c for c in codes if all(v[t]>=c.count(t) for t in range(34))]
print("codes ⊆ H (i.e. this hand is covered):",len(cov))
for c in cov[:5]: print("   ", ",".join(nm(t) for t in c))
# also: is H's class among the 30 empty ones?
Z=json.load(open("work/verify/plan_k4_zero.json",encoding="utf-8"))
zero={frozenset(r["W"]):len(r["codes"]) for r in Z["plan"]}
print("zero-plan codes for this class:", zero.get(key))
