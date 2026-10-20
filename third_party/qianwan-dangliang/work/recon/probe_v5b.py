
import json
p=json.load(open(r"D:\DSH\MJ2\work\recon\lead_plan_k3_v5.json"))
for x in p["plan"]:
    if x["W"]==['3s','4s','5s','9s']:
        print("found:", json.dumps(x, ensure_ascii=False)[:400])
        break
else:
    print("not found by W")
# count by Wmask presence
import collections
print("total in plan:", len(p["plan"]))
codes=[len(x["codes"]) for x in p["plan"]]
print("zero codes:", sum(1 for c in codes if c==0), "min",min(codes),"max",max(codes))
