
import json
Z=json.load(open("work/verify/plan_k4_zero.json",encoding="utf-8"))
F=json.load(open("work/verify/plan_k4_final.json",encoding="utf-8"))
HON=["E","S","W","N","Haku","Hatsu","Chun"]
def nm(t): return ("%d%s"%(t%9+1,"mps"[t//9])) if t<27 else HON[t-27]
emp=[(r["W"],len(r["codes"])) for r in Z["plan"] if not r["codes"]]
print("empty classes in zero plan:",len(emp))
old={tuple(sorted(r["W"])):len(r["codes"]) for r in F["plan"]}
for W,n in emp[:12]:
    print("   W=%s  baseline codes=%d" % (",".join(nm(t) for t in W), old.get(tuple(sorted(W)),-1)))
