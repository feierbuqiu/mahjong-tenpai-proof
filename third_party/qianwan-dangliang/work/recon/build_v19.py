# -*- coding: utf-8 -*-
"""Lead v16: base=refit(单门已 0), 对每个类补"⊆A 的 4-码"覆盖其全部来源 A(最小 A 归约),
   并对含 chiitoi 描述子的类补 93 边族。容量感知 + 全局有序码唯一。"""
import pickle, itertools, math, collections, json, time
T0=time.time()
def log(*a): print("[%6.1fs]"%(time.time()-T0), *a, flush=True)
K=4
BASE=r"D:\DSH\MJ2\work\verify\plan_k4_refit.json"
OUT=r"D:\DSH\MJ2\work\recon\plan_k4_u18.json"
T=pickle.load(open(r"D:\DSH\MJ2\work\recon\table_perA.pkl","rb"))
CLS,PI,PII=T["cls"],T["PROFI_D"],T["PROFII_D"]
CB=[0,9,18,27]; CL=[9,9,9,7]; HON=["E","S","W","N","Haku","Hatsu","Chun"]
def v34(c,X):
    base=CB[c]; v=[0]*34
    for i,n in enumerate(X):
        if n: v[base+i]=n
    return tuple(v)
def nperm(m):
    f=1
    for x in set(m): f*=math.factorial(m.count(x))
    return 24//f
def keyof(w):
    H={n:27+i for i,n in enumerate(HON)}
    def s2t(s):
        if s in H: return H[s]
        if s.endswith("z"): return 27+int(s[:-1])-1
        return (0 if s.endswith("m") else 1 if s.endswith("p") else 2)*9+int(s[:-1])-1
    return frozenset(s2t(x) if isinstance(x,str) else x for x in w)
base=json.load(open(BASE))["plan"]
used=collections.Counter(); usedset=set(); plan={}
for e in base:
    W=keyof(e["W"]); codes=[tuple(c) for c in e.get("codes",[])]
    for c in codes: used[c]+=1; usedset.add(c)
    plan[W]={"W":e["W"],"codes":codes}
log("base classes=%d codes=%d"%(len(plan),len(usedset)))
PERMC={}
def perms_of(m):
    if m not in PERMC: PERMC[m]=sorted(set(itertools.permutations(m)))
    return PERMC[m]
def take(m):
    for p in perms_of(m):
        if p not in usedset: usedset.add(p); used[m]+=1; return list(p)
    return None
def put(pat,out):
    if used[pat]>=nperm(pat): return False
    cd=take(pat)
    if cd is None: return False
    out.append(cd); return True
gj=json.load(open(r"D:\DSH\MJ2\work\data\out\global.json"))
chiitoi={int(k):v for k,v in gj["chiitoi_descriptors"].items()}
wm2key={c["Wmask"]: keyof(c["W"]) for c in gj["classes"]}
def inert_of(W):
    inerts=set()
    for b in CLS.get(W,[]):
        kind,k1,k2,mode,z,am,nsrc=b
        if kind=="I": inerts |= {x for x in range(4) if x!=k1[0]}
        elif kind=="II": inerts |= {x for x in range(4) if x not in (k1[0],k2[0])}
        else: inerts |= set(range(4))
    return inerts
def all_As(W):
    As=set()
    for b in CLS.get(W,[]):
        kind,k1,k2,mode,z,am,nsrc=b
        if kind=="I":
            c,s,pkey=k1; am_,xs=PI[(c,s,pkey)]
            for X in xs: As.add(v34(c,X))
        elif kind=="II":
            c1,s1,k1x=k1; c2,s2,k2x=k2
            am1,xs1=PII[(c1,s1,k1x)]; am2,xs2=PII[(c2,s2,k2x)]
            if len(xs1)*len(xs2)<=3000:
                for X1 in xs1:
                    for X2 in xs2: As.add(tuple(a+b for a,b in zip(v34(c1,X1),v34(c2,X2))))
            else:
                As.add(tuple(a+b for a,b in zip(v34(c1,am1),v34(c2,am2))))
        else:
            As.add(tuple(1 if (t in (0,8,9,17,18,26) or 27<=t<=33) else 0 for t in range(34)))
    return As
KOK_ALL=tuple(1 if (t in (0,8,9,17,18,26) or 27<=t<=33) else 0 for t in range(34))
def minimal(As):
    bs=sorted(As, key=sum); keep=[]
    for A in bs:
        if sum(A)<K: continue
        if not any(all(k[t]<=A[t] for t in range(34)) for k in keep): keep.append(A)
        if len(keep)>3000: break
    return keep
added=0; slow=[]
for ti,W in enumerate(sorted(CLS.keys(), key=lambda w: len(CLS[w]))):
    e=plan.get(W)
    if e is None: continue
    As=all_As(W)
    big=minimal([A for A in As if sum(A)>=K])
    new=[]; unc=set(range(len(big))); guard=0
    while unc and guard<1500:
        guard+=1
        i=min(unc,key=lambda j: sum(big[j])); A=big[i]
        tl=[t for t,n in enumerate(A) for _ in range(n)]
        best=None; bc=0
        for pat in set(itertools.combinations_with_replacement(tl,K)):
            if used[pat]>=nperm(pat): continue
            cnt=0
            for j in unc:
                Aj=big[j]; ok=True
                for t in set(pat):
                    if Aj[t]<pat.count(t): ok=False; break
                if ok: cnt+=1
            if cnt>bc: bc=cnt; best=pat
        if best is None:
            inerts=inert_of(W)
            tiles=[CB[c]+i2 for c in sorted(inerts) for i2 in range(CL[c])]
            rr=[]
            for c in sorted(inerts):
                if c<3: rr += [(CB[c]+i2,CB[c]+i2+1,CB[c]+i2+2) for i2 in range(7)]
            # 选一个剩余容量最大的 (u,v) ⊆ A, 然后加**整个**族
            bestpair=None; bestrem=-1
            for u in range(34):
                if A[u]<1: continue
                for v in range(u,34):
                    if A[v]<1 or (u==v and A[u]<2): continue
                    if not tiles: continue
                    f0=tiles[0]
                    rem=nperm(tuple(sorted((u,v,f0,f0))))-used[tuple(sorted((u,v,f0,f0)))]
                    if rem>bestrem: bestrem=rem; bestpair=(u,v)
            if bestpair:
                u,v=bestpair
                for f in tiles:
                    for pat in [tuple(sorted((u,v,f,f))),tuple(sorted((u,u,f,f))),tuple(sorted((v,v,f,f))),tuple(sorted((u,f,f,f)))]:
                        put(pat,new)
                for r0 in rr:
                    f1,f2,f3=r0
                    for pat in [tuple(sorted((u,v,f1,f2))),tuple(sorted((u,v,f2,f3))),tuple(sorted((u,f1,f2,f3)))]:
                        put(pat,new)
            unc.discard(i)
            continue
        if best is not None and not put(best,new):
            best=None
        if best is None:
            unc.discard(i); continue
        unc={j for j in unc if all(big[j][t]>=best.count(t) for t in set(best))}
    # 国士类: 用"12 张公共牌"内的码 (排除该类缺的那张)
    if any(b[0]=="KOK" for b in CLS.get(W,[])):
        miss=None
        if len(W)==1: miss=next(iter(W))
        cand=[t for t in range(34) if KOK_ALL[t] and t!=miss]
        for pat in set(itertools.combinations_with_replacement(cand,K)):
            if put(pat,new): break
        for pat in [tuple(sorted((cand[0],cand[1],cand[2],cand[3])))]:
            put(pat,new)
    # chiitoi 族
    wm=None
    for k,w in wm2key.items():
        if w==W: wm=k; break
    if wm is not None and wm in chiitoi:
        # 93 边: 33 种牌分 5 组(7,7,7,6,6), 组内完全图
        zs=[d["z"] for d in chiitoi[wm]]
        for zname in zs:
            Hs={"E":27,"S":28,"W":29,"N":30,"Haku":31,"Hatsu":32,"Chun":33}
            z=Hs.get(zname, None)
            if z is None:
                z=(0 if zname.endswith("m") else 1 if zname.endswith("p") else 2)*9+int(zname[:-1])-1
            others=[t for t in range(34) if t!=z]
            groups=[others[i::5] for i in range(5)]
            for g in groups:
                for a in range(len(g)):
                    for b in range(a+1,len(g)):
                        for pat in [tuple(sorted((z,g[a],g[b],g[a]))), tuple(sorted((z,g[a],g[b],g[b])))]:
                            put(pat,new)
    e["codes"].extend(new); added+=len(new)
    if (ti+1)%300==0: log("  %d/%d added=%d codes=%d"%(ti+1,len(CLS),added,len(usedset)))
allc=[tuple(c) for pe in plan.values() for c in pe["codes"]]
log("classes=%d codes=%d distinct=%d added=%d empty=%d"%(len(plan),len(allc),len(set(allc)),added,sum(1 for pe in plan.values() if not pe["codes"])))
json.dump({"k":4,"n_classes":len(plan),"n_codes":len(set(allc)),
           "plan":[{"W":v["W"],"codes":v["codes"]} for v in plan.values()]}, open(OUT,"w"))
log("written",OUT)