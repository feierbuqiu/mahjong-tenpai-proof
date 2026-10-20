# -*- coding: utf-8 -*-
"""Lead v21: base=refit. 每类:
   (1) 用 ⊆A 的 4-码 覆盖其最小 A 集(容量感知); 
   (2) 剩余 A 用"二元覆盖 × 补牌面子族"(刻子型 (u,v,f,f) 与 顺子型 (u,v,f1,f2) 都要生成, 每种多备选);
   (3) chiitoi 族 / 国士码。
   计时统计缺失数。产物 plan_k4_u20.json"""
import pickle, itertools, math, collections, json, time
T0=time.time()
def log(*a): print("[%6.1fs]"%(time.time()-T0), *a, flush=True)
K=4
BASE=r"D:\DSH\MJ2\work\verify\plan_k4_refit.json"
OUT=r"D:\DSH\MJ2\work\recon\plan_k4_u21.json"
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
    if len(pat)!=K: return False
    if used[pat]>=nperm(pat): return False
    cd=take(pat)
    if cd is None: return False
    out.append(cd); return True
gj=json.load(open(r"D:\DSH\MJ2\work\data\out\global.json"))
chiitoi={int(k):v for k,v in gj["chiitoi_descriptors"].items()}
wm2key={c["Wmask"]: keyof(c["W"]) for c in gj["classes"]}
key2wm={v:k for k,v in wm2key.items()}
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
def inerts_of(W):
    inerts=set()
    for b in CLS.get(W,[]):
        kind,k1,k2,mode,z,am,nsrc=b
        if kind=="I": inerts |= {x for x in range(4) if x!=k1[0]}
        elif kind=="II": inerts |= {x for x in range(4) if x not in (k1[0],k2[0])}
        else: inerts |= set(range(4))
    return sorted(inerts)
def minimal(As):
    bs=sorted([A for A in As if sum(A)>=K], key=sum); keep=[]
    for A in bs:
        if not any(all(k[t]<=A[t] for t in range(34)) for k in keep): keep.append(A)
        if len(keep)>3000: break
    return keep
def family(u,v,inerts,out):
    tiles=[CB[c]+i for c in inerts for i in range(CL[c])]
    rr=[]
    for c in inerts:
        if c<3: rr += [(CB[c]+i,CB[c]+i+1,CB[c]+i+2) for i in range(7)]
    def bestof(pats):
        best=None; br=-1
        for pat in pats:
            r=nperm(pat)-used[pat]
            if r>br: br=r; best=pat
        if best is not None and br>0: put(best,out)
    for f in tiles:
        bestof([tuple(sorted((u,v,f,f))),tuple(sorted((u,u,f,f))),tuple(sorted((v,v,f,f))),
                tuple(sorted((u,f,f,f))),tuple(sorted((u,u,v,f))),tuple(sorted((v,v,u,f)))])
    for (f1,f2,f3) in rr:
        bestof([tuple(sorted((u,v,f1,f2))),tuple(sorted((u,v,f2,f3))),tuple(sorted((u,v,f1,f3))),
                tuple(sorted((u,f1,f2,f3))),tuple(sorted((v,f1,f2,f3)))])
    # 若该 (u,v) 的族容量普遍吃紧, 追加 (u,f1,f2,f3)/(v,...) 变体与 (u,v,f,f) 的其它组合
    for (f1,f2,f3) in rr:
        for pat in [tuple(sorted((u,f1,f2,f3))),tuple(sorted((v,f1,f2,f3))),
                    tuple(sorted((u,u,f1,f2))),tuple(sorted((v,v,f1,f2))),
                    tuple(sorted((u,v,f1,f1))),tuple(sorted((u,v,f2,f2)))]:
            r=nperm(pat)-used[pat]
            if r>0: put(pat,out)
missing=collections.Counter()
for ti,W in enumerate(sorted(CLS.keys(), key=lambda w: len(CLS[w]))):
    e=plan.get(W)
    if e is None: continue
    As=all_As(W); big=minimal(As); new=[]
    unc=set(range(len(big)))
    # (1) ⊆A 贪心
    guard=0
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
        if best is None: break
        if not put(best,new): break
        unc={j for j in unc if all(big[j][t]>=best.count(t) for t in set(best))}
    # (2) 剩余 A: 二元覆盖 + 完整族(刻子+顺子)
    if unc:
        inerts=inerts_of(W)
        pairs=[]
        while unc:
            bestp=None; bc=0
            for u in range(34):
                for v in range(u,34):
                    cnt=sum(1 for j in unc if big[j][u]>=1 and big[j][v]>=1 and (u!=v or big[j][u]>=2))
                    if cnt>bc: bc=cnt; bestp=(u,v)
            if bestp is None or bc==0: break
            pairs.append(bestp)
            unc={j for j in unc if not (big[j][bestp[0]]>=1 and big[j][bestp[1]]>=1 and (bestp[0]!=bestp[1] or big[j][bestp[0]]>=2))}
        for (u,v) in pairs: family(u,v,inerts,new)
        if unc: missing["A_uncovered"]+=len(unc)
    # (3) chiitoi
    wm=key2wm.get(W)
    if wm in chiitoi:
        for d in chiitoi[wm]:
            zname=d["z"]; z=(next(iter(keyof([zname]))) if not isinstance(zname,int) else zname)
            others=[t for t in range(34) if t!=z]
            groups=[others[i::5] for i in range(5)]
            for g in groups:
                for a in range(len(g)):
                    for b in range(a+1,len(g)):
                        for pat in [tuple(sorted((z,g[a],g[b],g[a]))),tuple(sorted((z,g[a],g[b],g[b])))]:
                            put(pat,new)
    # (4) 国士
    if any(b[0]=="KOK" for b in CLS.get(W,[])):
        miss=next(iter(W)) if len(W)==1 else None
        cand=[t for t in range(34) if (t in (0,8,9,17,18,26) or 27<=t<=33) and t!=miss]
        put(tuple(sorted(cand[:4])),new)
    e["codes"].extend(new)
    if (ti+1)%400==0: log("  %d/%d codes=%d missing=%s"%(ti+1,len(CLS),len(usedset),dict(missing)))
allc=[tuple(c) for pe in plan.values() for c in pe["codes"]]
log("classes=%d codes=%d distinct=%d empty=%d missing=%s"%(len(plan),len(allc),len(set(allc)),sum(1 for pe in plan.values() if not pe["codes"]),dict(missing)))
json.dump({"k":4,"n_classes":len(plan),"n_codes":len(set(allc)),
           "plan":[{"W":v["W"],"codes":v["codes"]} for v in plan.values()]}, open(OUT,"w"))
log("written",OUT)