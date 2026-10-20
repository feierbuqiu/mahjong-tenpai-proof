
import json, collections
d=json.load(open(r"D:\DSH\MJ2\work\data\out\global.json"))
cls=d["classes"]
for su in ("m","p","s","z"):
    sel=[c for c in cls if c["sub_universe"]==[su]]
    n=len(sel)
    nc={k:sum(1 for c in sel if c["no_common_code"][k]) for k in ("1","2","3","4")}
    print("sub_universe=%s: classes=%d no_common=%s" % (su,n,nc))
empty=[c for c in cls if c["sub_universe"]==[]]
print("unconfined classes:", len(empty))
tot=sum(len(c["sources"]) for c in cls)
print("total classes:", len(cls), "total source blocks:", tot)
# k=2 sub-universe certificate numbers
for su in ("m","p","s"):
    sel=[c for c in cls if c["sub_universe"]==[su]]
    n2=sum(1 for c in sel if c["no_common_code"]["2"])
    n1=sum(1 for c in sel if c["no_common_code"]["1"])
    print("%s: k=2 sum_tau_LB = %d + %d = %d  vs 9^2=%d ;  k=1 LB = %d vs 9" % (su,len(sel),n2,len(sel)+n2,81,len(sel)+n1))
