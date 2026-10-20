
import json, collections
for path in ("work/recon/lead_plan_k3.json", "work/strategy/out/plan.json"):
    p = json.load(open(path, encoding="utf-8")); rows = p["plan"]
    zero = sum(1 for r in rows if len(r["codes"]) == 0)
    own = {}
    for r in rows:
        for c in r["codes"]:
            key = tuple(sorted(c)); own[key] = own.get(key, 0) + 1
    dist = collections.Counter(own.values())
    print(path, "classes", len(rows), "zero-code classes", zero,
          "distinct codes", len(own), "codes used exactly once", dist.get(1, 0),
          "max reuse", max(own.values()))
