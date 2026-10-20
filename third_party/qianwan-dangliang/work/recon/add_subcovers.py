
import json, itertools
HON=["E","S","W","N","Haku","Hatsu","Chun"]
def t2s(t): return ("%d%s"%((t%9)+1,"mps"[t//9])) if t<27 else HON[t-27]
def s2t(s):
    H={n:27+i for i,n in enumerate(HON)}
    if s in H: return H[s]
    if s.endswith("z"): return 27+int(s[:-1])-1
    return (0 if s.endswith("m") else 1 if s.endswith("p") else 2)*9+int(s[:-1])-1
def keyof(w): return frozenset(s2t(x) if isinstance(x,str) else x for x in w)
base=json.load(open(r"D:\DSH\MJ2\work\recon\plan_k4_u9.json"))["plan"]
sub=json.load(open(r"D:\DSH\MJ2\work\recon\k4_subuniverse_covers.json"))
gj=json.load(open(r"D:\DSH\MJ2\work\data\out\global.json"))
wm2key={c["Wmask"]: frozenset(s2t(x) for x in c["W"]) for c in gj["classes"]}
cov={}
for k,v in sub.items():
    kk=wm2key.get(int(k))
    if kk: cov[kk]=[tuple(c) for c in v["codes"]]
print("sub-universe classes with covers:", len(cov))
usedset=set(); used=set()
plan=[]
for e in base:
    W=keyof(e["W"]); codes=[]
    for c in e.get("codes",[]):
        c=tuple(c)
        if c not in usedset: usedset.add(c); codes.append(c)
    plan.append({"W":e["W"],"codes":codes})
idx={keyof(e["W"]):e for e in plan}
added=0; fail=0
for W,cs in cov.items():
    e=idx.get(W)
    if e is None: continue
    for pat in cs:
        if len(pat)!=4: fail+=1; continue
        for p in sorted(set(itertools.permutations(pat))):
            if p not in usedset: usedset.add(p); e["codes"].append(list(p)); added+=1; break
        else: fail+=1
allc=[tuple(c) for e in plan for c in e["codes"]]
print("classes:",len(plan),"codes:",len(allc),"distinct:",len(set(allc)),"added_sub:",added,"fail:",fail,
      "empty:",sum(1 for e in plan if not e["codes"]))
json.dump({"k":4,"n_classes":len(plan),"n_codes":len(set(allc)),"plan":plan},
          open(r"D:\DSH\MJ2\work\recon\plan_k4_u10.json","w"))
print("written plan_k4_u10.json")
