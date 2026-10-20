
import json
d = json.load(open("work/data/out/global.json", encoding="utf-8"))
rows = d["classes"]
print("n rows", len(rows))
print(json.dumps(rows[0], ensure_ascii=False)[:800])
print(json.dumps(rows[100], ensure_ascii=False)[:800])
