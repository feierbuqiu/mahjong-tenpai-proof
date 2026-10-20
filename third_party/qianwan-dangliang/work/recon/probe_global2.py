
import json, collections
d=json.load(open(r"D:\DSH\MJ2\work\data\out\global.json"))
print("meta:", json.dumps(d["meta"], ensure_ascii=False)[:800])
print("n_classes:", d["n_classes"], "sum_K_over_classes:", d["sum_K_over_classes"])
cls=d["classes"]
Kd=collections.Counter(c["K"] for c in cls)
print("K distribution:", dict(sorted(Kd.items())[:20]))
# class {1m}
for c in cls:
    if c["W"]==["1m"]:
        print("class 1m: K=",c["K"],"n_sources=",len(c["sources"]))
        for s in c["sources"][:12]:
            print("   ", json.dumps(s, ensure_ascii=False)[:200])
        break
# how many classes have a size-1 source
cnt=0; tot=0
for c in cls:
    for s in c["sources"]:
        if s.get("kind")=="I" and s.get("A","").count("1")==1 and sum(int(ch) for ch in s["A"])==1:
            cnt+=1; break
print("classes with a tanki (|A|=1) source:", cnt)
# how many classes have K==0
print("classes with K==0:", sum(1 for c in cls if c["K"]==0))
# check sub_universe distribution
su=collections.Counter("".join(c["sub_universe"]) for c in cls)
print("sub_universe:", dict(sorted(su.items())))
# distribution of source kinds
kk=collections.Counter(s.get("kind") for c in cls for s in c["sources"])
print("source kinds:", dict(kk))
print("total sources:", sum(len(c["sources"]) for c in cls))
print("chiitoi_descriptors:", type(d["chiitoi_descriptors"]), len(d["chiitoi_descriptors"]) if hasattr(d["chiitoi_descriptors"],'__len__') else '')
