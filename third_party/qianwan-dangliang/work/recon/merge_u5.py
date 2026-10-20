
import json, itertools
HON=["E","S","W","N","Haku","Hatsu","Chun"]
def t2s(t): return ("%d%s"%((t%9)+1,"mps"[t//9])) if t<27 else HON[t-27]
def s2t(s):
    H={n:27+i for i,n in enumerate(HON)}
    if s in H: return H[s]
    if s.endswith("z"): return 27+int(s[:-1])-1
    return (0 if s.endswith("m") else 1 if s.endswith("p") else 2)*9+int(s[:-1])-1
def keyof(w): return frozenset(s2t(x) if isinstance(x,str) else x for x in w)
a=json.load(open(r"D:\DSH\MJ2\work\recon\plan_k4_u1.json"))["plan"]
b=json.load(open(r"D:\DSH\MJ2\work\recon\plan_k4_u4.json"))["plan"]
bb={keyof(e["W"]):[tuple(c) for c in e["codes"]] for e in b}
used=set(); out=[]; added=0
for e in a:
    W=keyof(e["W"]); codes=[]
    for c in e.get("codes",[]):
        c=tuple(c)
        if c not in used: used.add(c); codes.append(c)
    for c in bb.get(W,[]):
        c=tuple(c)
        if c not in used: used.add(c); codes.append(c); added+=1
    out.append({"W":e["W"],"codes":[list(c) for c in codes]})
allc=[tuple(c) for e in out for c in e["codes"]]
print("classes:",len(out),"codes:",len(allc),"distinct:",len(set(allc)),"added:",added,"empty:",sum(1 for e in out if not e["codes"]))
json.dump({"k":4,"n_classes":len(out),"n_codes":len(set(allc)),"plan":out}, open(r"D:\DSH\MJ2\work\recon\plan_k4_u5.json","w"))
print("written plan_k4_u5.json")
