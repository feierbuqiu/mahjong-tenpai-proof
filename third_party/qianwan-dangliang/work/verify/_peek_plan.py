
import json
p = json.load(open("work/strategy/out/plan.json", encoding="utf-8"))
print("keys:", list(p.keys()))
for k, v in p.items():
    if isinstance(v, list):
        print(k, "list len", len(v), "sample:", json.dumps(v[:1], ensure_ascii=False)[:300])
    else:
        print(k, "=", json.dumps(v, ensure_ascii=False)[:200])
plan = p["plan"]
print("n classes in plan:", len(plan))
print("sample row:", json.dumps(plan[0], ensure_ascii=False)[:400])
