
import json
from collections import defaultdict
mine = set(frozenset(x) for x in json.load(open("work/verify/census_strict.json", encoding="utf-8")))
for path in ("work/recon/lead_plan_k3.json", "work/strategy/out/plan.json"):
    p = json.load(open(path, encoding="utf-8"))
    rows = p["plan"]
    plancls = {}
    for r in rows:
        W = frozenset(r["W"]); plancls[W] = [tuple(sorted(c)) for c in r["codes"]]
    own = defaultdict(set)
    for W, cs in plancls.items():
        for c in cs: own[c].add(W)
    shared = {c: ws for c, ws in own.items() if len(ws) > 1}
    n_private = {W: sum(1 for c in cs if len(own[c]) == 1) for W, cs in plancls.items()}
    no_priv = [W for W, n in n_private.items() if n == 0]
    print("===", path)
    print("  classes", len(plancls), "codes", sum(len(v) for v in plancls.values()),
          "distinct", len(own), "shared codes", len(shared),
          "max fanout", max((len(v) for v in own.values()), default=0))
    print("  classes with >=1 private code:", sum(1 for n in n_private.values() if n >= 1),
          " classes with NO private code:", len(no_priv))
    print("  classes fully covered by private codes alone (count check):",
          sum(1 for W, cs in plancls.items() if all(len(own[c]) == 1 for c in cs)))
    print("  example no-private class:", sorted(next(iter(no_priv))) if no_priv else None)
