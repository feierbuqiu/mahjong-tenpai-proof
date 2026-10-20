
import json, hashlib, os
HON=["E","S","W","N","Haku","Hatsu","Chun"]
HONI={"E":27,"S":28,"W":29,"N":30,"Haku":31,"Hatsu":32,"Chun":33}
def ti(x):
    if isinstance(x,int): return x
    if x in HONI: return HONI[x]
    return "mps".index(x[-1])*9+int(x[0])-1
def nm(t): return ("%d%s"%(t%9+1,"mps"[t//9])) if t<27 else HON[t-27]
SRC="work/verify/plan_k4_leadC_patched.json"; DST="work/verify/plan_k4_FINAL.json"
P=json.load(open(SRC,encoding="utf-8"))
Wl=json.load(open("work/verify/waste_leadC_patched.json",encoding="utf-8"))
drop={}
for e in Wl["waste_by_class"]:
    W=frozenset(ti(x) for x in e["W"])
    drop.setdefault(W,set()).update(tuple(ti(x) for x in c) for c in e["codes"])
removed=0; rows=[]
for r in P["plan"]:
    W=frozenset(ti(x) for x in r["W"]); d=drop.get(W,set())
    keep=[c for c in r["codes"] if tuple(c) not in d]
    removed += len(r["codes"])-len(keep)
    rows.append({"W":r["W"],"codes":keep})
out={"k":4,"n_classes":len(rows),"n_codes":sum(len(r["codes"]) for r in rows),"plan":rows,
     "base":SRC,"removed_unusable":[{"W":e["W"],"codes":e["codes"]} for e in Wl["waste_by_class"]]}
json.dump(out, open(DST,"w",encoding="utf-8"), ensure_ascii=False)
h=hashlib.sha256(open(DST,"rb").read()).hexdigest()
print("删除 %d 条不可用码 ; 最终 %d 类 / %d 码" % (removed,out["n_classes"],out["n_codes"]))
print("sha256:",h)
open("work/verify/plan_k4_FINAL.sha256","w").write(h+"  work/verify/plan_k4_FINAL.json\n")
