
import json, os
p=r"D:\DSH\MJ2\work\strategy\out\plan_k4.json"
if os.path.exists(p):
    d=json.load(open(p)); plan=d["plan"]
    empty=[x for x in plan if not x.get("codes")]
    allc=[tuple(c) for x in plan for c in x.get("codes",[])]
    print("k=",d.get("k"),"classes=",len(plan),"codes=",len(allc),"distinct=",len(set(allc)),"empty=",len(empty))
else: print("no plan_k4")
