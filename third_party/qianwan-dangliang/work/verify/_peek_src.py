
import json
g = json.load(open("work/data/out/global.json", encoding="utf-8"))
rows = g["classes"]
for r in rows:
    srcs = r.get("sources", [])
    kinds = set(s["kind"] for s in srcs)
    if "II" in kinds:
        print("class W=", r["W"], "nhands", r["n_hands"])
        for s in srcs:
            if s["kind"] == "II":
                print("  II source:", json.dumps(s, ensure_ascii=False)[:300]); break
        for s in srcs:
            if s["kind"] != "II":
                print("  other:", json.dumps(s, ensure_ascii=False)[:200]); break
        break
# 是否有 KOK 来源
for r in rows:
    for s in r.get("sources", []):
        if s["kind"] not in ("I","II"):
            print("kind", s["kind"], json.dumps(s, ensure_ascii=False)[:300]); break
    else:
        continue
    break
print("chiitoi_descriptors sample:", json.dumps(list(g["chiitoi_descriptors"].items())[:1], ensure_ascii=False)[:400])
print("n classes with chiitoi desc:", len(g["chiitoi_descriptors"]))
