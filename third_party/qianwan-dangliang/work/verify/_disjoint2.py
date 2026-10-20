
import json, collections
mine = set(frozenset(x) for x in json.load(open("work/verify/census_strict.json", encoding="utf-8")))
for path in ("work/recon/lead_plan_k3.json", "work/strategy/out/plan.json"):
    p = json.load(open(path, encoding="utf-8")); rows = p["plan"]
    zero = sum(1 for r in rows if len(r["codes"]) == 0)
    ordered = collections.Counter()
    multi = collections.Counter()
    for r in rows:
        for c in r["codes"]:
            ordered[tuple(c)] += 1
            multi[tuple(sorted(c))] += 1
    perms = lambda m: 1 if len(set(m)) == 1 else (3 if len(set(m)) == 2 else 6)
    over_cap = sum(1 for m, k in multi.items() if k > perms(m))
    print(path)
    print("  classes", len(rows), "zero-code classes", zero)
    print("  distinct ORDERED codes", len(ordered), "ordered codes reused >1:", sum(1 for v in ordered.values() if v > 1))
    print("  distinct multisets", len(multi), "multisets exceeding permutation capacity:", over_cap)
    print("  classes missing from my census:", len(mine - set(frozenset(r["W"]) for r in rows)))
