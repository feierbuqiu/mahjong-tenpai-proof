# -*- coding: utf-8 -*-
"""Lead k=3 构造 v4：先占必需码族(tanki/chiitoi/kokushi)，再对普通块做"覆盖率优先、剩余容量次之"的全局装包。"""
import json, itertools, math, collections, time
T0=time.time()
def log(*a): print("[%7.1fs]"%(time.time()-T0), *a, flush=True)
d=json.load(open(r"D:\DSH\MJ2\work\data\out\global.json"))
CLS=d["classes"]; CHII=d["chiitoi_descriptors"]
LETTER="mpsz"; ORPH=[0,8,9,17,18,26]+list(range(27,34))
BUDGET={0:729,1:729,2:729,3:343}
def cat_of(t): return t//9 if t<27 else 3
def base_of(c): return c*9 if c<3 else 27
HONOR={"E":27,"S":28,"W":29,"N":30,"Haku":31,"Hatsu":32,"Chun":33}
def s2t(s):
    if s in HONOR: return HONOR[s]
    if s.endswith("z"): return 27+int(s[:-1])-1
    return base_of(LETTER.index(s[-1]))+int(s[:-1])-1
def t2s(t): return ("%d%s"%((t%9)+1,LETTER[cat_of(t)])) if t<27 else ("%dz"%((t-27)+1))
def parse_A(s,cat):
    base=base_of(cat); v=[0]*34
    for i,ch in enumerate(s):
        n=int(ch)
        if n: v[base+i]=n
    return tuple(v)
PERM={}
def perms(p):
    if p not in PERM: PERM[p]=sorted(set(itertools.permutations(p)))
    return PERM[p]
used=collections.Counter(); pool=collections.Counter()
def take(p):
    os_=perms(p); u=used[p]
    if u>=len(os_): return None
    used[p]=u+1
    cs={cat_of(t) for t in p}
    if len(cs)==1: pool[next(iter(cs))]+=1
    return list(os_[u])
def reqs(c):
    uni=[]; tanki=[]; chii=[]; kok=[]
    for s in c["sources"]:
        k=s.get("kind")
        if k=="I":
            A=parse_A(s["A"], LETTER.index(s["cat"]))
            if sum(A)==1: tanki.append((A.index(1), [LETTER.index(ch) for ch in s["inert"]]))
            else: uni.append(A)
        elif k=="II":
            A1=parse_A(s["minA1"], LETTER.index(s["cats"][0]))
            A2=parse_A(s["minA2"], LETTER.index(s["cats"][1]))
            uni.append(tuple(a+b for a,b in zip(A1,A2)))
        elif k=="kokushi": kok.append(bool(s.get("thirteen_way")))
    for desc in CHII.get(str(c["Wmask"]),[]): chii.append(s2t(desc["z"]))
    return uni,tanki,chii,kok
def min_blocks(uni):
    bs=sorted(set(uni), key=sum); keep=[]
    for v in bs:
        if not any(all(a<=b for a,b in zip(k,v)) for k in keep): keep.append(v)
    return keep

log("classes=%d"%len(CLS))
order=sorted(CLS, key=lambda c: (0 if c["sub_universe"] else 1, len(c["sources"])))
plan={}; fails=[]; essential_used=0
stage=list(order)
DATA=[]
for c in stage:
    uni,tanki,chii,kok=reqs(c)
    DATA.append((c,min_blocks(uni),tanki,chii,kok))

# ---------- Phase 1: essential families ----------
for (c,blocks,tanki,chii,kok) in DATA:
    codes=[]
    for (x,inerts) in tanki:
        fam=set()
        for a in range(34):
            if a!=x and cat_of(a) in inerts: fam.add(tuple(sorted((x,a,a))))
        for a in range(27):
            if a%9<7 and cat_of(a) in inerts and cat_of(a+1) in inerts: fam.add(tuple(sorted((x,a,a+1))))
        for p in sorted(fam): 
            cd=take(p)
            if cd: codes.append(cd); essential_used+=1
    for z in chii:
        subcats=[LETTER.index(x) for x in c["sub_universe"]]
        allowed=[t for t in range(34) if t!=z and (not subcats or cat_of(t) in subcats)]
        need=max(0,len(allowed)-5)
        allowed=sorted(allowed, key=lambda t: used.get(tuple(sorted((z,t,t))),0))
        for a in allowed[:need]:
            cd=take(tuple(sorted((z,a,a))))
            if cd: codes.append(cd); essential_used+=1
    for thirteen in kok:
        cand=ORPH if thirteen else [t for t in ORPH if t!=s2t(c["W"][0])]
        cd=take(tuple(sorted(cand[:3])))
        if cd: codes.append(cd)
    plan[c["Wmask"]]={"W":c["W"],"sub":c["sub_universe"],"codes":codes}
log("phase1 done: essential codes=%d pool=%s"%(essential_used,dict(pool)))

# ---------- Phase 2: universal covers ----------
def mono(p):
    cs={cat_of(t) for t in p}
    return next(iter(cs)) if len(cs)==1 else None
for (c,blocks,tanki,chii,kok) in DATA:
    if not blocks: continue
    catu=set()
    for A in blocks: catu |= {cat_of(t) for t,n in enumerate(A) if n}
    tiles=[]
    for cc in sorted(catu):
        b=base_of(cc); n=9 if cc<3 else 7
        tiles += [b+i for i in range(n)]
    univ=list(itertools.combinations_with_replacement(tiles,3))
    bcov=[0]*len(univ)
    for bi,A in enumerate(blocks):
        for pi,p in enumerate(univ):
            ok=True
            for t in set(p):
                if A[t]<p.count(t): ok=False; break
            if ok: bcov[pi]|=1<<bi
    unc=(1<<len(blocks))-1
    while unc:
        best=-1; bk=None
        for pi,p in enumerate(univ):
            cvg=bin(bcov[pi]&unc).count("1")
            if cvg==0: continue
            rem=len(perms(p))-used[p]
            if rem<=0: continue
            m=mono(p)
            if m is not None and len(catu)>1 and pool[m]>=BUDGET[m]: continue
            key=(cvg, rem)
            if bk is None or key>bk: bk=key; best=pi
        if best<0: break
        p=univ[best]
        cd=take(p)
        if cd is None: break
        plan[c["Wmask"]]["codes"].append(cd)
        unc &= ~bcov[best]
    if unc:
        fails.append((c["W"],"cover-fail",bin(unc).count("1")))
    if not plan[c["Wmask"]]["codes"]:
        fails.append((c["W"],"empty",0))
allc=[tuple(cd) for v in plan.values() for cd in v["codes"]]
dups=len(allc)-len(set(allc))
log("DONE classes=%d Σcodes=%d distinct=%d dups=%d pool=%s fails=%d"%(len(plan),len(allc),len(set(allc)),dups,dict(pool),len(fails)))
if fails: log("fails sample:", fails[:12])
json.dump({"k":3,"n_classes":len(plan),"n_codes":len(allc),"pool":dict(pool),
  "plan":[{"Wmask":k,"W":[t2s(x) for x in v["W"] if False] or v["W"],"codes":v["codes"],"sub":v["sub"]} for k,v in plan.items()],
  "fails":fails}, open(r"D:\DSH\MJ2\work\recon\lead_plan_k3_v4.json","w"))
log("written lead_plan_k3_v4.json")
