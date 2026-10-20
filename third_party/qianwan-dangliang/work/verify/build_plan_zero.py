
import json, collections
HON=["E","S","W","N","Haku","Hatsu","Chun"]
def ti(x):
    if isinstance(x,int): return x
    if x in HON: return 27+HON.index(x)
    return "mps".index(x[-1])*9+int(x[0])-1
def nm(t): return ("%d%s"%(t%9+1,"mps"[t//9])) if t<27 else HON[t-27]
SRC="work/verify/plan_k4_final.json"
P=json.load(open(SRC,encoding="utf-8"))
W=json.load(open("work/verify/waste_list_exact.json",encoding="utf-8"))
waste={}
for e in W["waste_by_class"]:
    key=tuple(sorted(ti(x) for x in e["W"]))
    waste.setdefault(key,set()).update(tuple(ti(x) for x in c) for c in e["codes"])
tot_del=0; cls_touched=0; unmatched=collections.Counter(); matched_all=set()
newplan=[]
for r in P["plan"]:
    key=tuple(sorted(r["W"]))
    ws=waste.get(key,set())
    keep=[]; dele=[]
    for c in r["codes"]:
        t=tuple(c)
        if t in ws: dele.append(c); matched_all.add((key,t))
        else: keep.append(c)
    if dele: cls_touched+=1
    tot_del+=len(dele)
    newplan.append({"W":r["W"],"codes":keep,"modes":r.get("modes",[])})
allw={(k,c) for k,s in waste.items() for c in s}
unmatched=allw-matched_all
out={"k":4,"n_classes":len(newplan),"n_codes":sum(len(r["codes"]) for r in newplan),
     "plan":newplan,
     "base":SRC,
     "waste_removed":{"source":"work/verify/waste_list_exact.json","deleted":tot_del,
                      "classes_touched":cls_touched,"unmatched_waste_entries":len(unmatched)}}
dst="work/verify/plan_k4_zero.json"
json.dump(out, open(dst,"w",encoding="utf-8"), ensure_ascii=False)
print("删除 %d 码 / %d 类 ; 未匹配的浪费条目 = %d" % (tot_del, cls_touched, len(unmatched)))
print("码数 %d -> %d (类数 %d)" % (P["n_codes"], out["n_codes"], out["n_classes"]))
for x in list(unmatched)[:5]: print("   未匹配:",[nm(t) for t in x[0]],[nm(t) for t in x[1]])
print("已写",dst)
