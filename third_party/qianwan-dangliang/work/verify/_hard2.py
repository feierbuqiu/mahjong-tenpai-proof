
import json, collections, sys
HON = {"E": 27, "S": 28, "W": 29, "N": 30, "Haku": 31, "Hatsu": 32, "Chun": 33}
def to_idx(w):
    if isinstance(w, int): return [t for t in range(34) if (w >> t) & 1]
    out=[]
    for nm in w:
        if isinstance(nm, int): out.append(nm)
        elif nm in HON: out.append(HON[nm])
        else: out.append("mps".index(nm[-1])*9 + int(nm[0]) - 1)
    return out
mine = set(frozenset(x) for x in json.load(open("work/verify/census_strict.json", encoding="utf-8")))
for path in ("work/strategy/out/plan_k4.json", "work/recon/plan_k4_v6.json"):
    p = json.load(open(path, encoding="utf-8"))
    rows = p["plan"] if isinstance(p, dict) and "plan" in p else p
    plancls = {}
    for r in rows: plancls[frozenset(to_idx(r["W"]))] = [tuple(c) for c in r["codes"]]
    zero = sum(1 for cs in plancls.values() if not cs)
    own = collections.Counter(); ms = collections.Counter()
    for cs in plancls.values():
        for c in cs: own[c] += 1; ms[tuple(sorted(c))] += 1
    import itertools
    over = sum(1 for m, k in ms.items() if k > len(set(itertools.permutations(m))))
    print(path, "| classes", len(plancls), "missing", len(mine-set(plancls)), "extra", len(set(plancls)-mine),
          "| zero-code", zero, "| codes", sum(len(v) for v in plancls.values()),
          "| distinct ordered", len(own), "| reused", sum(1 for v in own.values() if v>1),
          "| multisets over cap", over, flush=True)
