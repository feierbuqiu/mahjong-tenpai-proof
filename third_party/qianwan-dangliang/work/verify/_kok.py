
import json
HONN=["E","S","W","N","Haku","Hatsu","Chun"]
def to_idx(w):
    o=[]
    for x in w:
        if isinstance(x,int): o.append(x)
        elif x in HONN: o.append(27+HONN.index(x))
        else: o.append("mps".index(x[-1])*9+int(x[0])-1)
    return o
P=json.load(open("work/verify/plan_k4_final.json",encoding="utf-8"))
ORPH=set([0,8,9,17,18,26]+list(range(27,34)))
found=0
for r in P["plan"]:
    W=to_idx(r["W"])
    if set(W)==ORPH:
        found+=1
        codes=[to_idx(c) for c in r["codes"]]
        bad=[c for c in codes if not set(c)<=ORPH]
        print("kokushi class entry: n_codes=%d, non-subset codes=%d" % (len(codes),len(bad)))
        for c in bad: print("   ", [("%d%s"%(t%9+1,"mps"[t//9])) if t<27 else HONN[t-27] for t in c])
        # which of these are in analyst's del but not mine?
print("entries with W=orphans13:", found)
