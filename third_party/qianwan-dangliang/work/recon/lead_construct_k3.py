# -*- coding: utf-8 -*-
"""Lead 版 k=3 构造（v3）：每个多重集的多重排列作为独立码资源, 容量感知装包。"""
import json, itertools, math, collections, time
T0=time.time()
def log(*a): print("[%6.1fs]"%(time.time()-T0), *a, flush=True)
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
def parse_A(s,cat):
    base=base_of(cat); v=[0]*34
    for i,ch in enumerate(s):
        n=int(ch)
        if n: v[base+i]=n
    return tuple(v)
ORD={}
def orderings(p):
    if p not in ORD: ORD[p]=sorted(set(itertools.permutations(p)))
    return ORD[p]
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
used={}            # pattern -> #orderings used
pool=collections.Counter()
def take(p):
    """占用 p 的一个未用排列; 返回该有序码, 失败返回 None"""
    os_=orderings(p); u=used.get(p,0)
    if u>=len(os_): return None
    used[p]=u+1
    cs={cat_of(t) for t in p}
    if len(cs)==1: pool[next(iter(cs))]+=1
    return list(os_[u])
plan={}; fails=[]
order=sorted(CLS, key=lambda c: (0 if c["sub_universe"] else 1, len(c["sources"])))
log("classes=%d"%len(CLS))
for idx,c in enumerate(order):
    uni,tanki,chii,kok=reqs(c)
    pats=set()
    for (x,inerts) in tanki:
        for a in range(34):
            if a!=x and cat_of(a) in inerts: pats.add(tuple(sorted((x,a,a))))
        for a in range(27):
            if a%9<7 and cat_of(a) in inerts and cat_of(a+1) in inerts: pats.add(tuple(sorted((x,a,a+1))))
    for z in chii:
        allowed=[t for t in range(34) if t!=z]
        need=max(0,len(allowed)-5)
        allowed=sorted(allowed, key=lambda t: used.get(tuple(sorted((z,t,t))),0))
        for a in allowed[:need]: pats.add(tuple(sorted((z,a,a))))
    for thirteen in kok:
        cand=ORPH if thirteen else [t for t in ORPH if t!=s2t(c["W"][0])]
        pats.add(tuple(sorted(cand[:3])))
    blk=list(set(uni))
    if blk:
        catu=set()
        for A in blk: catu |= {cat_of(t) for t,n in enumerate(A) if n}
        tiles=[]
        for cc in sorted(catu):
            b=base_of(cc); n=9 if cc<3 else 7
            tiles += [b+i for i in range(n)]
        univ=list(itertools.combinations_with_replacement(tiles,3))
        nb=len(blk); cov=[0]*len(univ)
        for bi,A in enumerate(blk):
            tl=[]
            for t,n in enumerate(A): tl += [t]*n
            for p in set(itertools.combinations_with_replacement(tl,3)):
                cov[univ.index(p)] |= (1<<bi)
        def usable(p):
            if used.get(p,0) >= len(orderings(p)): return False
            cs={cat_of(t) for t in p}
            if len(cs)==1 and len(catu)>1 and pool[next(iter(cs))] >= BUDGET[next(iter(cs))]: return False
            return True
        unc=(1<<nb)-1
        while unc:
            best=-1; bc=0
            for pi,p in enumerate(univ):
                if p in pats or not usable(p): continue
                cnt=bin(cov[pi]&unc).count("1")
                if cnt>bc: bc=cnt; best=pi
            if best<0: break
            p=univ[best]; pats.add(p); unc &= ~cov[best]
        if unc: fails.append((c["Wmask"],"cover-fail",bin(unc).count("1")))
    codes=[]; bad=0
    for p in sorted(pats, key=lambda p: -len(orderings(p))):
        cd=take(p)
        if cd is None: bad+=1
        else: codes.append(cd)
    if bad: fails.append((c["Wmask"],"capacity",bad))
    if not codes: fails.append((c["Wmask"],"empty",0))
    plan[c["Wmask"]]={"W":c["W"],"sub":c["sub_universe"],"codes":codes}
    if (idx+1)%300==0:
        log("  %d/%d codes=%d pool=%s fails=%d"%(idx+1,len(order),sum(used.values()),dict(pool),len(fails)))
allc=[tuple(cd) for v in plan.values() for cd in v["codes"]]
log("DONE classes=%d Σcodes=%d distinct_ordered=%d pool=%s fails=%d"%(len(plan),len(allc),len(set(allc)),dict(pool),len(fails)))
if len(allc)!=len(set(allc)): log("!! ordered code collision")
if fails: log("fails:", fails[:10])
json.dump({"k":3,"n_classes":len(plan),"n_codes":len(allc),"pool":dict(pool),
           "plan":[{"Wmask":k,**v} for k,v in plan.items()],"fails":fails},
          open(r"D:\DSH\MJ2\work\recon\lead_plan_k3.json","w"))
log("written")
