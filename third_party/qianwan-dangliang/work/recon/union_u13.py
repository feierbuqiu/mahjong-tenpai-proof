
import json, itertools
HON=["E","S","W","N","Haku","Hatsu","Chun"]
H2={n:27+i for i,n in enumerate(HON)}
def s2t(s):
    if s in H2: return H2[s]
    if s.endswith("z"): return 27+int(s[:-1])-1
    return (0 if s.endswith("m") else 1 if s.endswith("p") else 2)*9+int(s[:-1])-1
def keyof(w): return frozenset(s2t(x) if isinstance(x,str) else x for x in w)
A=json.load(open(r"D:\DSH\MJ2\work\recon\plan_k4_u9.json"))["plan"]
B=json.load(open(r"D:\DSH\MJ2\work\verify\plan_k4_refit.json"))["plan"]
bb={}
for e in B:
    k=keyof(e["W"])
    bb.setdefault(k,[])
    bb[k].extend([tuple(c) for c in e["codes"]])
usedset=set(); out=[]; added=0
for e in A:
    k=keyof(e["W"]); codes=[]
    for c in e.get("codes",[]):
        c=tuple(c)
        if c not in usedset: usedset.add(c); codes.append(list(c))
    for c in bb.get(k,[]):
        c=tuple(c)
        if c in usedset: continue
        usedset.add(c); codes.append(list(c)); added+=1
    out.append({"W":[x if isinstance(x,int) else s2t(x) for x in e["W"]],"codes":codes})
# refit 里有而 u9 没有的类也带上
seen={keyof(e["W"]) for e in out}
for k,cs in bb.items():
    if k in seen: continue
    codes=[]
    for c in cs:
        c=tuple(c)
        if c in usedset: continue
        usedset.add(c); codes.append(list(c))
    out.append({"W":sorted(k),"codes":codes})
allc=[tuple(c) for e in out for c in e["codes"]]
print("classes:",len(out),"codes:",len(allc),"distinct:",len(set(allc)),"added_refit:",added,
      "empty:",sum(1 for e in out if not e["codes"]))
json.dump({"k":4,"n_classes":len(out),"n_codes":len(set(allc)),"plan":out},
          open(r"D:\DSH\MJ2\work\recon\plan_k4_u13.json","w"))
print("written plan_k4_u13.json")
