# -*- coding: utf-8 -*-
"""Lead k=3 构造 v5：多随机重启 + "接近最优覆盖 + 剩余容量最大" 的打分。"""
import json, itertools, math, collections, time, random
T0=time.time()
def log(*a): print("[%7.1fs]"%(time.time()-T0), *a, flush=True)
d=json.load(open(r"D:\DSH\MJ2\work\data\out\global.json"))
CLS=d["classes"]; CHII=d["chiitoi_descriptors"]
LETTER="mpsz"; ORPH=[0,8,9,17,18,26]+list(range(27,34))
BUDGET={0:729,1:729,2:729,3:343}
def cat_of(t): return t//9 if t<27 else 3
def base_of(c): return c*9 if c<3 else 27
def t2s(t): return ("%d%s"%((t%9)+1,LETTER[cat_of(t)])) if t<27 else ("%dz"%((t-27)+1))
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
PERM={}
def perms(p):
    if p not in PERM: PERM[p]=sorted(set(itertools.permutations(p)))
    return PERM[p]
def min_blocks(uni):
    bs=sorted(set(uni), key=sum); keep=[]
    for v in bs:
        if not any(all(a<=b for a,b in zip(k,v)) for k in keep): keep.append(v)
    return keep
# ---- precompute class data once ----
DATA=[]
for c in CLS:
    uni=[]; tanki=[]; chii=[]; kok=[]
    for s in c["sources"]:
        k=s.get("kind")
        if k=="I":
            A=parse_A(s["A"], LETTER.index(s["cat"]))
            if sum(A)==1: tanki.append((A.index(1), [LETTER.index(ch) for ch in s["inert"]]))
            else: uni.append(A)
        elif k=="II":
            A1=parse_A(s["minA1"], LETTER.index(s["cats"][0])); A2=parse_A(s["minA2"], LETTER.index(s["cats"][1]))
            uni.append(tuple(a+b for a,b in zip(A1,A2)))
        elif k=="kokushi": kok.append(bool(s.get("thirteen_way")))
    for desc in CHII.get(str(c["Wmask"]),[]): chii.append(s2t(desc["z"]))
    blocks=min_blocks(uni)
    if blocks:
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
    else:
        catu=set(); univ=[]; bcov=[]
    DATA.append(dict(c=c, blocks=blocks, catu=catu, univ=univ, bcov=bcov, tanki=tanki, chii=chii, kok=kok))

def run_attempt(seed, spread):
    rnd=random.Random(seed)
    used=collections.Counter(); pool=collections.Counter(); plan={}
    def take(p):
        os_=perms(p); u=used[p]
        if u>=len(os_): return None
        used[p]=u+1
        cs={cat_of(t) for t in p}
        if len(cs)==1: pool[next(iter(cs))]+=1
        return list(os_[u])
    order=list(range(len(DATA)))
    rnd.shuffle(order)
    order.sort(key=lambda i: (0 if DATA[i]["c"]["sub_universe"] else 1))
    for i in order:
        D=DATA[i]; c=D["c"]; codes=[]
        # essentials first
        for (x,inerts) in D["tanki"]:
            fam=set()
            for a in range(34):
                if a!=x and cat_of(a) in inerts: fam.add(tuple(sorted((x,a,a))))
            for a in range(27):
                if a%9<7 and cat_of(a) in inerts and cat_of(a+1) in inerts: fam.add(tuple(sorted((x,a,a+1))))
            for p in sorted(fam):
                cd=take(p)
                if cd: codes.append(cd)
        for z in D["chii"]:
            subcats=[LETTER.index(x) for x in c["sub_universe"]]
            allowed=[t for t in range(34) if t!=z and (not subcats or cat_of(t) in subcats)]
            need=max(0,len(allowed)-5)
            allowed=sorted(allowed, key=lambda t: (used.get(tuple(sorted((z,t,t))),0), rnd.random()))
            for a in allowed[:need]:
                cd=take(tuple(sorted((z,a,a))))
                if cd: codes.append(cd)
        for thirteen in D["kok"]:
            cand=ORPH if thirteen else [t for t in ORPH if t!=s2t(c["W"][0])]
            cd=take(tuple(sorted(cand[:3])))
            if cd: codes.append(cd)
        # universal cover
        unc=(1<<len(D["blocks"]))-1
        while unc:
            cands=[]
            for pi,p in enumerate(D["univ"]):
                mm=D["bcov"][pi]&unc
                if not mm: continue
                rem=len(perms(p))-used[p]
                if rem<=0: continue
                cs={cat_of(t) for t in p}
                if len(cs)==1 and len(D["catu"])>1 and pool[next(iter(cs))]>=BUDGET[next(iter(cs))]: continue
                cands.append((bin(mm).count("1"), rem, pi))
            if not cands: break
            mc=max(x[0] for x in cands)
            top=[x for x in cands if x[0]>=mc-spread]
            top.sort(key=lambda x:(-x[1], rnd.random()))
            pi=top[0][2]; p=D["univ"][pi]
            cd=take(p)
            if cd is None: break
            codes.append(cd); unc &= ~D["bcov"][pi]
        plan[c["Wmask"]]={"W":c["W"],"sub":c["sub_universe"],"codes":codes,"uncovered":bin(unc).count("1") if D["blocks"] else 0}
    bad=sum(1 for v in plan.values() if v["uncovered"] or not v["codes"])
    tot=sum(len(v["codes"]) for v in plan.values())
    return bad, tot, plan

best=None
for seed in range(40):
    for spread in (0,1):
        bad,tot,plan=run_attempt(seed,spread)
        if best is None or (bad,tot)<(best[0],best[1]): best=(bad,tot,plan,seed,spread)
        if bad==0: break
    if best[0]==0: break
log("BEST bad_classes=%d Σcodes=%d (seed=%d spread=%d)"%(best[0],best[1],best[3],best[4]))
plan=best[2]
allc=[tuple(cd) for v in plan.values() for cd in v["codes"]]
log("distinct=%d dups=%d"%(len(set(allc)), len(allc)-len(set(allc))))
json.dump({"k":3,"n_classes":len(plan),"n_codes":len(allc),"bad_classes":best[0],
  "plan":[{"W":v["W"],"Wmask":k,"codes":v["codes"],"sub":v["sub"]} for k,v in plan.items()],
  "fails":[[v["W"],"uncovered",v["uncovered"]] for v in plan.values() if v["uncovered"]][:50]},
  open(r"D:\DSH\MJ2\work\recon\lead_plan_k3_v5.json","w"))
log("written")
