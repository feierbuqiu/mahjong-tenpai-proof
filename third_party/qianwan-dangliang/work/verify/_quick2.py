
import json, collections
mine = set(frozenset(x) for x in json.load(open("work/verify/census_strict.json", encoding="utf-8")))
p = json.load(open("work/strategy/out/plan.json", encoding="utf-8"))
rows = p["plan"]
zero = sum(1 for r in rows if len(r["codes"]) == 0)
ordered = collections.Counter()
for r in rows:
    for c in r["codes"]: ordered[tuple(c)] += 1
multisets = collections.Counter()
for r in rows:
    for c in r["codes"]: multisets[tuple(sorted(c))] += 1
perms = lambda m: 1 if len(set(m)) == 1 else (3 if len(set(m)) == 2 else 6)
print("classes", len(rows), "zero-code", zero, "distinct ordered", len(ordered),
      "ordered reused>1", sum(1 for v in ordered.values() if v > 1),
      "multi over cap", sum(1 for m, k in multisets.items() if k > perms(m)))
print("W set == mine:", set(frozenset(r["W"]) for r in rows) == mine, "fails:", len(p.get("fails", [])))
