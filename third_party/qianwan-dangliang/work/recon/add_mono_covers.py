# -*- coding: utf-8 -*-
"""Lead v14: 在 base plan 上, 为 1189 个单类别(=含清一色手牌)类补"本门 4-码"覆盖其纯本门手牌。
   容量感知: 每个 4-多重集的使用次数 <= 排列数 p4(m)。产物 plan_k4_u12.json"""
import pickle, itertools, math, collections, json, time
T0=time.time()
def log(*a): print("[%6.1fs]"%(time.time()-T0), *a, flush=True)
K=4
BASE=r"D:\DSH\MJ2\work\recon\plan_k4_u9.json"
OUT=r"D:\DSH\MJ2\work\recon\plan_k4_u12.json"
T=pickle.load(open(r"D:\DSH\MJ2\work\recon\table_perA.pkl","rb"))
CLS,PI,PII=T["cls"],T["PROFI_D"],T["PROFII_D"]
CB=[0,9,18,27]; CL=[9,9,9,7]; HON=["E","S","W","N","Haku","Hatsu","Chun"]
def t2s(t): return ("%d%s"%((t%9)+1,"mps"[t//9])) if t<27 else HON[t-27]
def v34(c,X):
    base=CB[c]; v=[0]*34
    for i,n in enumerate(X):
        if n: v[base+i]=n
    return tuple(v)
def nperm(m):
    f=1
    for x in set(m): f*=math.factorial(m.count(x))
    return 24//f
HON2={n:27+i for i,n in enumerate(HON)}
def s2t(s):
    if s in HON2: return HON2[s]
    if s.endswith("z"): return 27+int(s[:-1])-1
    return (0 if s.endswith("m") else 1 if s.endswith("p") else 2)*9+int(s[:-1])-1
def keyof_idx(w):
    return frozenset(s2t(x) if isinstance(x,str) else x for x in w)
base=json.load(open(BASE))["plan"]
used=collections.Counter(); usedset=set(); plan=[]
for e in base:
    codes=[tuple(c) for c in e.get("codes",[])]
    for c in codes: used[c]+=1; usedset.add(c)
    plan.append({"W":e["W"],"codes":codes})
# 目标: 单类别类(其 A 全落本门) 且有 size-13 的纯本门手牌
targets=[]
for W,blocks in CLS.items():
    cats=set()
    for b in blocks:
        kind,k1,k2,mode,z,am,nsrc=b
        if kind=="I":
            c=k1[0]; cats.add(c)
        elif kind=="II":
            cats.add(k1[0]); cats.add(k2[0])
        else:
            cats.add(3)
    if len(cats)!=1: continue
    cat=next(iter(cats))
    pure=[]
    for b in blocks:
        kind,k1,k2,mode,z,am,nsrc=b
        if kind=="II": continue
        if kind=="I":
            c,s,pkey=k1
            if s!=13: continue
            am_,xs=PI[(c,s,pkey)]
            pure += [v34(c,X) for X in xs]
    if pure: targets.append((W,cat,pure))
idx={keyof_idx(pe["W"]): pe for pe in plan}
log("target classes with pure-category hands:", len(targets))
added=0; failc=0
for ti,(W,cat,pure) in enumerate(sorted(targets, key=lambda x: -len(x[2]))):
    e=idx.get(W)
    if e is None: continue
    unc=set(range(len(pure))); guard=0
    while unc and guard<4000:
        guard+=1
        # 候选: 从未覆盖手牌里取最小的那手的 4-子集, 按覆盖数与剩余容量选
        j=min(unc, key=lambda j: sum(pure[j]))
        A=pure[j]; tl=[]
        for t,n in enumerate(A): tl+=[t]*n
        best=None; bc=0
        for pat in set(itertools.combinations_with_replacement(tl,K)):
            rem=nperm(pat)-used[pat]
            if rem<=0: continue
            cnt=sum(1 for jj in unc if all(pure[jj][t]>=pat.count(t) for t in set(pat)))
            if cnt>bc: bc=cnt; best=pat
        if best is None: break
        cd=None
        for p in sorted(set(itertools.permutations(best))):
            if p not in usedset: usedset.add(p); cd=list(p); break
        if cd is None: break
        used[best]+=1; e["codes"].append(cd); added+=1
        unc={jj for jj in unc if not all(pure[jj][t]>=best.count(t) for t in set(best))}
    if unc: failc+=1
    if (ti+1)%100==0: log("  %d/%d added=%d codes=%d"%(ti+1,len(targets),added,sum(used.values())))
allc=[tuple(c) for pe in plan for c in pe["codes"]]
log("classes=%d codes=%d distinct=%d added=%d failclasses=%d empty=%d"%(
    len(plan),len(allc),len(set(allc)),added,failc,sum(1 for pe in plan if not pe["codes"])))
json.dump({"k":4,"n_classes":len(plan),"n_codes":len(set(allc)),"plan":plan}, open(OUT,"w"))
log("written",OUT)