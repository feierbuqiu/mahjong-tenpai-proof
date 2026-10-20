
import json
p = json.load(open("work/recon/plan_k4_v6.json", encoding="utf-8"))
rows = p["plan"] if isinstance(p, dict) and "plan" in p else p
print("sample0:", json.dumps(rows[0], ensure_ascii=False)[:250])
names = set()
for r in rows[:400]:
    for nm in (r["W"] if isinstance(r["W"], list) else []): names.add(nm)
print("sample names:", sorted(names)[:25])
