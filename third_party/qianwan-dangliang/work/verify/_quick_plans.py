
import json, sys
mine = set(frozenset(x) for x in json.load(open("work/verify/census_strict.json", encoding="utf-8")))
for path in ("work/recon/lead_plan_k3.json", "work/strategy/out/plan.json"):
    p = json.load(open(path, encoding="utf-8"))
    if isinstance(p, dict) and "plan" in p:
        rows = p["plan"]; meta = {k: v for k, v in p.items() if k != "plan"}
    else:
        rows = p; meta = {}
    plancls = {}
    for r in rows:
        W = frozenset(r["W"]); plancls[W] = [tuple(sorted(c)) for c in r["codes"]]
    owner = {}; coll = 0
    for W, cs in plancls.items():
        for c in cs:
            if c in owner and owner[c] != W: coll += 1
            owner[c] = W
    print(path)
    print("  meta:", json.dumps({k: (str(v)[:120]) for k, v in meta.items()}, ensure_ascii=False)[:300])
    print("  classes:", len(plancls), "missing:", len(mine - set(plancls)), "extra:", len(set(plancls) - mine),
          "codes:", sum(len(v) for v in plancls.values()), "distinct:", len(owner), "collisions:", coll)
