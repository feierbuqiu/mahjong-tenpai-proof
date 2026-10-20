
import json
p = json.load(open("work/strategy/out/plan.json", encoding="utf-8"))
rows = p["plan"]
print("keys of row:", list(rows[0].keys()))
print("n rows:", len(rows))
import collections
lc = collections.Counter(len(r["codes"]) for r in rows)
print("codes-per-class distribution (first 10):", dict(sorted(lc.items())[:10]))
print("max codes per class:", max(lc))
print("any 'chosen' key:", any("chosen" in r for r in rows))
