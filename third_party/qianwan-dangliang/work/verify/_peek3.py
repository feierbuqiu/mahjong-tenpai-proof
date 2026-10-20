
import json
d = json.load(open("work/data/out/global.json", encoding="utf-8"))
rows = d["classes"]
for r in rows:
    if r["size"] >= 9:
        print(json.dumps(r["W"], ensure_ascii=False))
        break
# collect all tile names
names = set()
for r in rows:
    names.update(r["W"])
print("all names:", sorted(names))
