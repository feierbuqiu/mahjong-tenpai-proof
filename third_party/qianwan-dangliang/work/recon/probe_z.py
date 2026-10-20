
import json, collections
d=json.load(open(r"D:\DSH\MJ2\work\data\out\global.json"))
cd=d["chiitoi_descriptors"]
zs=collections.Counter()
for k,v in cd.items():
    for e in v: zs[e["z"]]+=1
print("distinct z strings:", sorted(zs.items(), key=lambda x:str(x[0]))[:40])
bad=[z for z in zs if not (isinstance(z,str) and z and z[-1] in "mpsz")]
print("bad z:", bad[:20], "count", len(bad))
