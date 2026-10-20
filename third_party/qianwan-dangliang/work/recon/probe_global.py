
import json
d=json.load(open(r"D:\DSH\MJ2\work\data\out\global.json"))
print("top keys:", list(d.keys())[:20])
cls=d["classes"] if "classes" in d else d
print("type:", type(cls), "len:", len(cls))
c=cls[0]
print("keys of a class:", list(c.keys()))
for kk in c:
    v=c[kk]
    s=str(v)
    print("  ", kk, "=", s[:180])
# aggregate
import collections
nn=len(cls)
totK=0; su=collections.Counter()
for c in cls:
    totK += c.get("K") or c.get("K_cover") or 0
    su[c.get("sub_universe")] += 1
print("n_classes", nn, "sumK", totK)
print("sub_universe counts:", dict(list(su.items())[:12]))
nsrc=collections.Counter(len(c.get("sources",[])) for c in cls)
print("sources-per-class distribution (head):", dict(sorted(nsrc.items())[:15]))
