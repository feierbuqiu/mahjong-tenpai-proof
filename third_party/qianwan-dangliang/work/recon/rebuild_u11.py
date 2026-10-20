
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
bykey={keyof(e["W"]):e for e in base}
usedset=set()
def put_perm(pat):
    for p in sorted(set(itertools.permutations(pat))):
        if p not in usedset: usedset.add(p); return list(p)
    return None
plan=[]; subkeys=[]; added=0; failc=0
# 1) 先给 1189 个子宇宙类分配本门覆盖
for W,cs in cov.items():
    e=bykey.get(W)
    if e is None: continue
    codes=[]
    for pat in cs:
        c=put_perm(tuple(sorted(pat)))
        if c: codes.append(c); added+=1
        else: failc+=1
    # 再补它原有的 tanki/chiitoi 族码
    for c in e.get("codes",[]):
        c=tuple(c)
        if c in usedset: continue
        usedset.add(c); codes.append(list(c))
    plan.append({"W":[t2s(x) for x in sorted(W)],"codes":codes})
    subkeys.append(W)
print("sub classes:", len(plan), "codes:", added, "fail pat:", failc)
# 2) 其余类沿用 u9（换排列保唯一）
subset=set(subkeys); other=0
for e in base:
    W=keyof(e["W"])
    if W in subset: continue
    codes=[]
    for c in e.get("codes",[]):
        c=tuple(c)
        if c in usedset: 
            alt=put_perm(tuple(sorted(c)))
            if alt: codes.append(alt)
        else:
            usedset.add(c); codes.append(list(c))
    plan.append({"W":e["W"],"codes":codes}); other+=1
allc=[tuple(c) for e in plan for c in e["codes"]]
print("classes:",len(plan),"other:",other,"codes:",len(allc),"distinct:",len(set(allc)),
      "empty:",sum(1 for e in plan if not e["codes"]))
json.dump({"k":4,"n_classes":len(plan),"n_codes":len(set(allc)),"plan":plan},
          open(r"D:\DSH\MJ2\work\recon\plan_k4_u11.json","w"))
print("written plan_k4_u11.json")
