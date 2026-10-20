
import json, collections
for path in [r"D:\DSH\MJ2\work\recon\plan_k4_u9.json", r"D:\DSH\MJ2\work\verify\plan_k4_refit.json", r"D:\DSH\MJ2\work\recon\plan_k4_u13.json"]:
    d=json.load(open(path))["plan"]
    t=collections.Counter()
    for e in d:
        w=e["W"]
        if isinstance(w,int): t["int"]+=1
        elif isinstance(w,list) and w and isinstance(w[0],int): t["intlist"]+=1
        else: t["namelist"]+=1
    print(path.split("\\")[-1], "classes", len(d), dict(t), "empty", sum(1 for e in d if not e.get("codes")))
