
import json, sys
p1 = "work/data/out/global.json"
d = json.load(open(p1, encoding="utf-8"))
print("type:", type(d))
if isinstance(d, dict):
    print("keys:", list(d.keys())[:20])
    for k in list(d.keys())[:3]:
        v = d[k]
        print(k, type(v), str(v)[:300])
elif isinstance(d, list):
    print("len:", len(d), str(d[:3])[:400])
print("---- census_stats.json")
print(open("work/strategy/out/census_stats.json", encoding="utf-8").read()[:800])
print("---- flush_tau_exact.json head")
t = json.load(open("work/recon/flush_tau_exact.json", encoding="utf-8"))
print(type(t), (list(t.keys())[:10] if isinstance(t, dict) else len(t)))
print(str(t)[:600])
