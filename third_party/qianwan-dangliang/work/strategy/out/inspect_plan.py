# -*- coding: utf-8 -*-
import json, sys, os, itertools, collections, math, time
sys.stdout.reconfigure(encoding="utf-8")
P = json.load(open("work/strategy/out/plan_k4_v2.json", encoding="utf-8"))
print("top keys:", list(P.keys()))
print("k=", P.get("k"), "n_classes=", P.get("n_classes"), "n_codes=", P.get("n_codes"))
r0 = P["plan"][0]
print("entry keys:", list(r0.keys()))
print("sample entry:", {k: (v if not isinstance(v, list) else v[:3]) for k, v in r0.items()})
lens = collections.Counter(len(r["codes"]) for r in P["plan"])
print("codes-per-class histogram (top):", sorted(lens.items())[:10], "...", sorted(lens.items())[-5:])
cl = collections.Counter()
for r in P["plan"]:
    for c in r["codes"]: cl[tuple(sorted(c))] += 1
print("总码数 =", sum(len(r["codes"]) for r in P["plan"]), " 不同有序码 =", len({tuple(c) for r in P["plan"] for c in r["codes"]}), " 不同多重集 =", len(cl))
print("超过 p4 的多重集数 =", sum(1 for mu, n in cl.items() if n > 24 // math.prod(math.factorial(v) for v in collections.Counter(mu).values())))
G = json.load(open("work/data/out/global.json", encoding="utf-8"))
print("global.json keys:", list(G.keys()))
print("classes:", len(G["classes"]), " chiitoi_descriptors:", len(G["chiitoi_descriptors"]))
print("sample chiitoi desc:", list(G["chiitoi_descriptors"].items())[:1])
print("sample source:", json.dumps(G["classes"][0], ensure_ascii=False)[:400])
kinds = collections.Counter(s["kind"] for r in G["classes"] for s in r.get("sources", []))
print("source kinds:", kinds)
