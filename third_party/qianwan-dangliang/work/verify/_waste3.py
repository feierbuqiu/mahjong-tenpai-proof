
import json
HON=["E","S","W","N","Haku","Hatsu","Chun"]
def nm(t): return ("%d%s"%(t%9+1,"mps"[t//9])) if t<27 else HON[t-27]
W=json.load(open("work/verify/waste_leadC_patched.json",encoding="utf-8"))
print("waste_count:",W.get("waste_count"),"classes:",len(W["waste_by_class"]))
for e in W["waste_by_class"]:
    print("  类 W=",",".join(e["W"])," 码:",[ "".join(c) for c in e["codes"]])
base=json.load(open("work/recon/plan_k4_leadC.json",encoding="utf-8"))
def key(r): return tuple(sorted(r["W"]))
bset={key(r):set(tuple(c) for c in r["codes"]) for r in base["plan"]}
pat=json.load(open("work/verify/plan_k4_leadC_patched.json",encoding="utf-8"))
pset={key(r):set(tuple(c) for c in r["codes"]) for r in pat["plan"]}
for e in W["waste_by_class"]:
    Wt=tuple(sorted(e["W"]))
    for c in e["codes"]:
        name=[x for x in base["plan"] if key(x)==Wt][0]["W"]
        # 码在 waste 里是名字
        ci=tuple(["mpsz".index(x[-1])*9+int(x[0])-1 if x not in HON else 27+HON.index(x) for x in c])
        print("  类",",".join(e["W"]),"码(索引)",ci,"在底版leadC中?",ci in bset.get(Wt,set()),"在补丁版中?",ci in pset.get(Wt,set()))
