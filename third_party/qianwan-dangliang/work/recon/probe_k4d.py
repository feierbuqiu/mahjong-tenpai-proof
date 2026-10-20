
import json, collections
d=json.load(open(r"D:\DSH\MJ2\work\strategy\out\plan_k4.json"))
plan=d["plan"]
empty=[x for x in plan if not x.get("codes")]
print("empty:", len(empty))
subs=collections.Counter(tuple(x.get("sub") or []) for x in empty)
print("empty by sub:", dict(list(subs.items())[:6]))
print("sample empty W:", [x["W"] for x in empty[:8]])
g=json.load(open(r"D:\DSH\MJ2\work\recon\k4_subuniverse_covers.json"))
wm={int(k) for k,v in g.items()}
used=[x for x in plan if not x.get("codes") and x.get("Wmask") in wm]
print("empty classes that HAVE a precomputed cover:", len(used))
