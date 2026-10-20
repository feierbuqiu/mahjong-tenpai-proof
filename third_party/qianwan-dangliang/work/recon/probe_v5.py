
import json, collections
p=json.load(open(r"D:\DSH\MJ2\work\recon\lead_plan_k3_v5.json"))
plan=p["plan"]
empty=[x for x in plan if not x["codes"]]
print("classes:",len(plan),"empty:",len(empty),"n_codes:",p["n_codes"])
print("fails recorded:", len(p.get("fails",[])))
sizes=collections.Counter(len(x["W"]) for x in empty)
print("empty class |W| distribution:", dict(sorted(sizes.items())))
subs=collections.Counter(tuple(x.get("sub") or []) for x in empty)
print("empty class sub_universe:", dict(list(subs.items())[:8]))
print("sample empty W:", [x["W"] for x in empty[:10]])
nonempty_fail=[x for x in plan if x["codes"] and x.get("uncovered")]
print("classes with codes but uncovered blocks:", len(nonempty_fail))
