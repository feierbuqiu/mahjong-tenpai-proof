
import json, sys, collections
sys.path.insert(0, "work/verify")
mine = set(frozenset(x) for x in json.load(open("work/verify/census_strict.json", encoding="utf-8")))
HON = {"E": 27, "S": 28, "W": 29, "N": 30, "Haku": 31, "Hatsu": 32, "Chun": 33}
def to_idx(w):
    if isinstance(w, int): return [t for t in range(34) if (w >> t) & 1]
    out = []
    for nm in w:
        if isinstance(nm, int): out.append(nm)
        elif nm in HON: out.append(HON[nm])
        else: out.append("mps".index(nm[-1]) * 9 + int(nm[0]) - 1)
    return out
for path in ("work/recon/lead_plan_k3_v5.json", "work/recon/lead_plan_k3_v4.json"):
    p = json.load(open(path, encoding="utf-8"))
    rows = p["plan"] if isinstance(p, dict) and "plan" in p else p
    plancls = {frozenset(to_idx(r["W"])): [tuple(c) for c in r["codes"]] for r in rows}
    zero = sum(1 for cs in plancls.values() if not cs)
    ordered = collections.Counter()
    multisets = collections.Counter()
    for cs in plancls.values():
        for c in cs: ordered[c] += 1; multisets[tuple(sorted(c))] += 1
    perms = lambda m: 1 if len(set(m)) == 1 else (3 if len(set(m)) == 2 else 6)
    print(path)
    print("  meta:", {k: v for k, v in (p.items() if isinstance(p, dict) else []) if k != "plan"})
    print("  classes", len(plancls), "missing vs mine", len(mine - set(plancls)), "extra", len(set(plancls) - mine),
          "zero-code", zero, "codes", sum(len(v) for v in plancls.values()),
          "ordered reused>1", sum(1 for v in ordered.values() if v > 1),
          "multi over cap", sum(1 for m, k in multisets.items() if k > perms(m)))
