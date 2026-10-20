
import json, collections
p=json.load(open(r"D:\DSH\MJ2\work\strategy\out\plan_k4.json"))
print("keys:", list(p.keys())[:10])
print("k=",p.get("k"),"n_classes=",p.get("n_classes"),"n_codes=",p.get("n_codes"),"fails=",str(p.get("fails"))[:200])
plan=p.get("plan") or p.get("classes")
if isinstance(plan,list):
    print("plan len:", len(plan), "sample:", json.dumps(plan[0], ensure_ascii=False)[:300])
    nc=[len(x.get("codes",[])) for x in plan]
    print("codes per class: min",min(nc),"max",max(nc),"sum",sum(nc),"empty",sum(1 for x in nc if x==0))
    allc=[tuple(c) for x in plan for c in x.get("codes",[])]
    print("distinct ordered codes:", len(set(allc)), "dups:", len(allc)-len(set(allc)))
