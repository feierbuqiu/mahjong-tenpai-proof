
import json, collections
d=json.load(open(r"D:\DSH\MJ2\work\data\out\global.json"))
cls=d["classes"]
# find a class with kind II sources
for c in cls:
    ks=set(s.get("kind") for s in c["sources"])
    if "II" in ks and len(c["sources"])<8:
        print("class W=",c["W"],"K=",c["K"],"sub=",c["sub_universe"],"n_src=",len(c["sources"]))
        for s in c["sources"]:
            print("   ", json.dumps(s, ensure_ascii=False)[:300])
        break
print("---- chiitoi descriptors sample ----")
cd=d["chiitoi_descriptors"]
items=list(cd.items())[:3]
for k,v in items: print(k, "->", json.dumps(v, ensure_ascii=False)[:300])
print("---- a class with K>0 ----")
for c in cls:
    if c["K"]==5 and len(c["sources"])<12:
        print("W=",c["W"],"K=",c["K"],"sources:")
        for s in c["sources"]: print("   ", json.dumps(s, ensure_ascii=False)[:220])
        break
