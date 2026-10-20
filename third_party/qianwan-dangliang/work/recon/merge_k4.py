# -*- coding: utf-8 -*-
"""Lead: 稳健合并（唯一有序码保证 + 结构覆盖自检）→ work/recon/plan_k4_merged.json"""
import json, itertools, collections
GJ=r"D:\DSH\MJ2\work\data\out\global.json"
PL=r"D:\DSH\MJ2\work\strategy\out\plan_k4.json"
SUB=r"D:\DSH\MJ2\work\recon\k4_subuniverse_covers.json"
CROSS=r"D:\DSH\MJ2\work\recon\k4_cross_covers.json"
LETTER="mpsz"
HONOR={"E":27,"S":28,"W":29,"N":30,"Haku":31,"Hatsu":32,"Chun":33}
def s2t(s):
    if s in HONOR: return HONOR[s]
    if s.endswith("z"): return 27+int(s[:-1])-1
    return (0 if s.endswith("m") else 1 if s.endswith("p") else 2)*9+int(s[:-1])-1
d=json.load(open(GJ))
plan=json.load(open(PL))["plan"]
sub=json.load(open(SUB)); cross=json.load(open(CROSS))
wm2key={c["Wmask"]: frozenset(s2t(x) for x in c["W"]) for c in d["classes"]}
key2blocks={}
for c in d["classes"]:
    key2blocks[frozenset(s2t(x) for x in c["W"])]=c["sources"]
extra={}
for k,v in sub.items():
    kk=wm2key.get(int(k))
    if kk: extra.setdefault(kk,[]).extend(v["codes"])
for k,v in cross.items():
    ks=k.strip("frozenset({})").split(",")
    key=frozenset(int(x) for x in ks if x.strip())
    extra.setdefault(key,[]).extend(v["codes"])
print("extra keys:", len(extra))

used=set(); fails=0; rerouted=0
def perm_of(multiset, prefer=None):
    global fails
    cands=[tuple(c) for c in itertools.permutations(multiset)]
    if prefer is not None and tuple(prefer) in cands and tuple(prefer) not in used:
        used.add(tuple(prefer)); return tuple(prefer)
    for p in sorted(set(cands)):
        if p not in used: used.add(p); return p
    fails+=1; return None
out=[]; empt=0
for e in plan:
    key=frozenset(e["W"])
    codes=[]
    for cd in e.get("codes",[]):
        cd=tuple(cd)
        if cd in used:
            alt=perm_of(tuple(sorted(cd)))
            if alt is None: continue
            codes.append(alt); rerouted+=1
        else:
            used.add(cd); codes.append(cd)
    for pat in extra.get(key,[]):
        p=perm_of(tuple(sorted(pat)))
        if p is not None: codes.append(p)
    if not codes: empt+=1; print("EMPTY:", sorted(e["W"]), flush=True)
    out.append({"W":e["W"],"codes":[list(c) for c in codes]})
allc=[tuple(c) for e in out for c in e["codes"]]
print("classes:",len(out),"codes:",len(allc),"distinct:",len(set(allc)),"dups:",len(allc)-len(set(allc)),"empty:",empt,"rerouted:",rerouted,"perm_fail:",fails)

# 结构自检: 每类 |A|>=4 的来源块是否被该类自己的码覆盖
bad=0; badblocks=0
for e in out:
    key=frozenset(e["W"]); srcs=key2blocks.get(key,[])
    A_vecs=[]
    for s in srcs:
        if s.get("kind")=="I":
            from math import factorial
            base=(0 if s["cat"]=="m" else 1 if s["cat"]=="p" else 2 if s["cat"]=="s" else 3)*9
            v=[0]*34
            for i,ch in enumerate(s["A"]):
                n=int(ch)
                if n: v[base+i]=n
            if sum(v)>=4: A_vecs.append(tuple(v))
        elif s.get("kind")=="II":
            v=[0]*34
            for cat,keyx in zip(s["cats"],[s["minA1"],s["minA2"]]):
                base=(0 if cat=="m" else 1 if cat=="p" else 2 if cat=="s" else 3)*9
                for i,ch in enumerate(keyx):
                    n=int(ch)
                    if n: v[base+i]+=n
            if sum(v)>=4: A_vecs.append(tuple(v))
    if not A_vecs: continue
    unc=0
    for A in set(A_vecs):
        if not any(all(A[t]>=c.count(t) for t in set(c)) for c in [tuple(x) for x in e["codes"]]): unc+=1
    if unc: bad+=1; badblocks+=unc
print("classes with uncovered |A|>=4 blocks:", bad, "total uncovered blocks:", badblocks)
json.dump({"k":4,"n_classes":len(out),"n_codes":len(allc),"plan":out}, open(r"D:\DSH\MJ2\work\recon\plan_k4_merged.json","w"))
print("written")
