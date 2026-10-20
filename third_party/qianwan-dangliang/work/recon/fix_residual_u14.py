# -*- coding: utf-8 -*-
"""Lead v15: 以 refit 为底, 对残余失败类补 (1) |A|>=4 的单位码 (2) chiitoi 族 (3) 小 |A| 块的二元覆盖+补牌码。
   容量感知; 产物 plan_k4_u14.json"""
import pickle, itertools, math, collections, json, time
T0=time.time()
def log(*a): print("[%6.1fs]"%(time.time()-T0), *a, flush=True)
K=4
BASE=r"D:\DSH\MJ2\work\verify\plan_k4_refit.json"
OUT=r"D:\DSH\MJ2\work\recon\plan_k4_u14.json"
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
def t2s(t): return ("%d%s"%((t%9)+1,"mps"[t//9])) if t<27 else HON[t-27]
def s2t(s):
    H={n:27+i for i,n in enumerate(HON)}
    if s in H: return H[s]
    if s.endswith("z"): return 27+int(s[:-1])-1
    return (0 if s.endswith("m") else 1 if s.endswith("p") else 2)*9+int(s[:-1])-1
def keyof(w): return frozenset(s2t(x) if isinstance(x,str) else x for x in w)
base=json.load(open(BASE))["plan"]
used=collections.Counter(); usedset=set(); plan={}
for e in base:
    W=keyof(e["W"]); codes=[tuple(c) for c in e.get("codes",[])]
    for c in codes: used[c]+=1; usedset.add(c)
    plan[W]={"W":e["W"],"codes":codes}
log("base classes:",len(plan),"codes:",len(usedset))
PERMC={}
def perms_of(m):
    if m not in PERMC: PERMC[m]=sorted(set(itertools.permutations(m)))
    return PERMC[m]
def take(m):
    for p in perms_of(m):
        if p not in usedset: usedset.add(p); used[m]+=1; return list(p)
    return None
def put(pat,out):
    if pat not in PERMC: PERMC[pat]=sorted(set(itertools.permutations(pat)))
    if used[pat]>=nperm(pat): return False
    cd=take(pat)
    if cd is None: return False
    out.append(cd); return True
# ---- 目标类: 已知残余 + 所有含七对子描述子的类 ----
gj=json.load(open(r"D:\DSH\MJ2\work\data\out\global.json"))
chiitoi={int(k):v for k,v in gj["chiitoi_descriptors"].items()}
wm2key={c["Wmask"]: keyof(c["W"]) for c in gj["classes"]}
targets=set()
for wm in chiitoi: 
    k=wm2key.get(wm)
    if k: targets.add(k)
for name in [["2m"],["2s"],["1p"],["9m"],["Haku"]]:
    targets.add(keyof(name))
log("targets:",len(targets))
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
            if len(xs1)*len(xs2)<=4000:
                for X1 in xs1:
                    for X2 in xs2: As.add(tuple(a+b for a,b in zip(v34(c1,X1),v34(c2,X2))))
            else:
                As.add(tuple(a+b for a,b in zip(v34(c1,am1),v34(c2,am2))))
        else:
            As.add(tuple(1 if (t in (0,8,9,17,18,26) or 27<=t<=33) else 0 for t in range(34)))
    return As
added=0
for W in sorted(targets, key=lambda w: len(CLS.get(w,[]))):
    e=plan.get(W)
    if e is None: continue
    As=all_As(W); new=[]
    # (1) |A|>=4: 贪心单位码
    big=[A for A in As if sum(A)>=K]
    unc=set(range(len(big))); guard=0
    while unc and guard<600:
        guard+=1
        i=min(unc,key=lambda j: sum(big[j])); A=big[i]
        tl=[t for t,n in enumerate(A) for _ in range(n)]
        best=None; bc=0
        for pat in set(itertools.combinations_with_replacement(tl,K)):
            if used[pat]>=nperm(pat): continue
            cnt=sum(1 for j in unc if all(big[j][t]>=pat.count(t) for t in set(pat)))
            if cnt>bc: bc=cnt; best=pat
        if best is None: break
        if not put(best,new): break
        unc={j for j in unc if not all(big[j][t]>=best.count(t) for t in set(best))}
    # (2) 小 |A| 块: 二元覆盖 + 补牌码
    small=[A for A in As if sum(A)<K]
    if small:
        # 找补牌类别: 该类所有块的 inert 并集
        inerts=set()
        for b in CLS.get(W,[]):
            kind,k1,k2,mode,z,am,nsrc=b
            if kind=="I": inerts |= {x for x in range(4) if x!=k1[0]}
            elif kind=="II": inerts |= {x for x in range(4) if x not in (k1[0],k2[0])}
            else: inerts |= set(range(4))
        tiles=[CB[c]+i for c in sorted(inerts) for i in range(CL[c])]
        runs=[]
        for c in sorted(inerts):
            if c<3: runs += [(CB[c]+i,CB[c]+i+1,CB[c]+i+2) for i in range(7)]
        # 覆盖所有 small
        unc=set(range(len(small))); guard=0
        while unc and guard<200:
            guard+=1
            best=None; bc=0
            for u in range(34):
                for v in range(u,34):
                    cnt=sum(1 for j in unc if small[j][u]>=1 and small[j][v]>=1 and (u!=v or small[j][u]>=2))
                    if cnt>bc: bc=cnt; best=(u,v)
            if best is None or bc==0:
                # 无法用二元覆盖: 直接对每个 A 试 ⊆A 的码(若 |A|>=K 已在上面处理)
                break
            u,v=best
            for f in tiles:
                for pat in [tuple(sorted((u,v,f,f))),tuple(sorted((u,u,f,f))),tuple(sorted((v,v,f,f))),tuple(sorted((u,f,f,f)))]:
                    put(pat,new)
            for r in runs:
                f1,f2,f3=r
                for pat in [tuple(sorted((u,v,f1,f2))),tuple(sorted((u,v,f2,f3))),tuple(sorted((u,f1,f2,f3)))]:
                    put(pat,new)
            unc={j for j in unc if not (small[j][u]>=1 and small[j][v]>=1 and (u!=v or small[j][u]>=2))}
    # (3) chiitoi 族 (93 边)
    descs=chiitoi.get(None)  # placeholder
    e["codes"].extend(new); added+=len(new)
allc=[tuple(c) for pe in plan.values() for c in pe["codes"]]
log("classes=%d codes=%d distinct=%d added=%d empty=%d"%(len(plan),len(allc),len(set(allc)),added,sum(1 for pe in plan.values() if not pe["codes"])))
json.dump({"k":4,"n_classes":len(plan),"n_codes":len(set(allc)),
           "plan":[{"W":v["W"],"codes":v["codes"]} for v in plan.values()]}, open(OUT,"w"))
log("written",OUT)
