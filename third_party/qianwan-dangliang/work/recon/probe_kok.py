
import json
d=json.load(open(r"D:\DSH\MJ2\work\data\out\global.json"))
cls=d["classes"]
for c in cls:
    ks=[s.get("kind") for s in c["sources"]]
    if "kokushi" in ks:
        print("W=",c["W"],"Wmask=",c["Wmask"],"sub=",c["sub_universe"],"n_kok=",c["n_kokushi_hands"])
        for s in c["sources"]:
            if s.get("kind")=="kokushi": print("   kok:", json.dumps(s,ensure_ascii=False)[:400])
        break
# a class with chiitoi descriptors + its Wmask
cd=d["chiitoi_descriptors"]
print("n chiitoi descriptor groups:", len(cd))
for k,v in list(cd.items())[:2]:
    print("mask",k,"->",json.dumps(v,ensure_ascii=False)[:300])
print("kokushi classes:", sum(1 for c in cls if any(s.get("kind")=="kokushi" for s in c["sources"])))
print("classes with chiitoi desc:", sum(1 for c in cls if str(c["Wmask"]) in cd))
print("size-13 classes:", sum(1 for c in cls if c["size"]==13))
