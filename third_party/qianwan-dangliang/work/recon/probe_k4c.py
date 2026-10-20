
import json
d=json.load(open(r"D:\DSH\MJ2\work\strategy\out\plan_k4.json"))
plan=d["plan"]
allc=[tuple(c) for x in plan for c in x.get("codes",[])]
empty=[x for x in plan if not x.get("codes")]
print("classes:",len(plan),"codes:",len(allc),"distinct:",len(set(allc)),"empty:",len(empty))
print("k:",d.get("k"),"fails:",str(d.get("fails"))[:150])
# per-suit usage of 4-codes
import collections
per=collections.Counter()
for c in allc:
    cs={(t//9 if t<27 else 3) for t in c}
    if len(cs)==1: per[list(cs)[0]]+=1
print("monochromatic code usage m/p/s/z:", dict(per), "(budgets 6561/6561/6561/2401)")
