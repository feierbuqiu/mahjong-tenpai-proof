
import sys, os, json, pickle
sys.path.insert(0,"work/strategy")
HON=["E","S","W","N","Haku","Hatsu","Chun"]
def ti(x):
    if isinstance(x,int): return x
    if x in HON: return 27+HON.index(x)
    return "mps".index(x[-1])*9+int(x[0])-1
def nm(t): return ("%d%s"%(t%9+1,"mps"[t//9])) if t<27 else HON[t-27]
CLS=pickle.load(open("work/strategy/out/table_cache.pkl","rb"))["cls"]
ORPH=frozenset([0,8,9,17,18,26]+list(range(27,34)))
print("class in cache:", ORPH in CLS)
for b in CLS.get(ORPH,[])[:8]:
    print("  block kind:", b[0], "len", len(b))
m=json.load(open("work/verify/waste_list_exact.json",encoding="utf-8"))
for e in m["waste_by_class"]:
    if len(e["W"])==13 and set(ti(x) for x in e["W"])==set(ORPH):
        print("my kokushi waste entries:", len(e["codes"]))
        for c in e["codes"][:20]: print("    ",[nm(t) for t in (ti(x) for x in c)])
