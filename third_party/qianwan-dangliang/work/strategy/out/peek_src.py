import json, collections
G = json.load(open("work/data/out/global.json", encoding="utf-8"))
seen = {}
for row in G["classes"]:
    for s in row.get("sources", []):
        seen.setdefault(s["kind"], (row["W"], s))
for k,(W,s) in seen.items():
    print(k, "W=", W, "fields=", list(s.keys()))
    print("   ", json.dumps(s, ensure_ascii=False)[:600])
    print()
print("meta:", json.dumps(G["meta"], ensure_ascii=False)[:800])
