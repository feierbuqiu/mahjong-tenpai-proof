# -*- coding: utf-8 -*-
"""Lead: 针对 fastcov 报出的缺口类 + 空码类, 用逐 A 覆盖重建(容量感知), 合并进 plan_k4_u1.json -> plan_k4_u2.json"""
import pickle, itertools, math, collections, json, time
T0=time.time()
def log(*a): print("[%6.1fs]"%(time.time()-T0), *a, flush=True)
K=4
T=pickle.load(open(r"D:\DSH\MJ2\work\recon\table_perA.pkl","rb"))
CLS,PI,PII=T["cls"],T["PROFI_D"],T["PROFII_D"]
CB=[0,9,18,27]; CL=[9,9,9,7]
def v34(c,X):
    base=CB[c]; v=[0]*34
    for i,n in enumerate(X):
        if n: v[base+i]=n
    return tuple(v)
def nperm(m):
    f=1
    for x in set(m): f*=math.factorial(m.count(x))
    return 24//f
def t2s(t):
    L="mpsz"; return ("%d%s"%((t%9)+1,L[t//9])) if t<27 else ("%dz"%((t-27)+1))
def s2t(s):
    H={"E":27,"S":28,"W":29,"N":30,"Haku":31,"Hatsu":32,"Chun":33}
    if s in H: return H[s]
    if s.endswith("z"): return 27+int(s[:-1])-1
    return (0 if s.endswith("m") else 1 if s.endswith("p") else 2)*9+int(s[:-1])-1
def keyof(w): return frozenset(s2t(x) if isinstance(x,str) else x for x in w)
# ---- 载入 u1 与缺口清单 ----
u1=json.load(open(r"D:\DSH\MJ2\work\recon\plan_k4_u1.json"))["plan"]
rep=json.load(open(r"D:\DSH\MJ2\work\verify\fastcov_report.json"))
targets=set()
for e in u1:
    if not e.get("codes"): targets.add(keyof(e["W"]))
for sname,info in rep.get("suits",{}).items():
    for it in info.get("top",[]): targets.add(keyof(it["W"]))
log("target classes:", len(targets))
# ---- 构造 per-A 需求 ----
def class_As(W):
    As=set()
    for b in CLS.get(W,[]):
        kind,k1,k2,mode,z,am,nsrc=b
        if kind=="I":
            c,s,pkey=k1; am_,xs=PI[(c,s,pkey)]
            if sum(am_)>=K: As.add(tuple(am_))
            else: 
                for X in xs: As.add(v34(c,X))
        elif kind=="II":
            c1,s1,k1x=k1; c2,s2,k2x=k2
            am1,xs1=PII[(c1,s1,k1x)]; am2,xs2=PII[(c2,s2,k2x)]
            amv=tuple(a+b for a,b in zip(v34(c1,am1),v34(c2,am2)))
            if sum(amv)>=K: As.add(amv)
            elif len(xs1)*len(xs2)<=20000:
                for X1 in xs1:
                    v1=v34(c1,X1)
                    for X2 in xs2: As.add(tuple(a+b for a,b in zip(v1,v34(c2,X2))))
            else: As.add(amv)
        else:
            As.add(tuple(1 if (t in (0,8,9,17,18,26) or 27<=t<=33) else 0 for t in range(34)))
    return As
# 先占用 u1 已有码
used=collections.Counter(); usedset=set()
plan={}
for e in u1:
    W=keyof(e["W"])
    codes=[tuple(c) for c in e.get("codes",[])]
    if W in targets:   # 目标类稍后重建, 先不占用它们的码
        plan[W]={"W":e["W"],"codes":[]}
        continue
    for c in codes: used[c]+=1; usedset.add(c)
    plan[W]={"W":e["W"],"codes":codes}
log("reserved codes from kept classes: %d"%sum(used.values()))
PERMC={}
def perms_of(m):
    if m not in PERMC: PERMC[m]=sorted(set(itertools.permutations(m)))
    return PERMC[m]
def take(m):
    ps=perms_of(m)
    for p in ps:
        if p not in usedset:
            usedset.add(p); used[m]+=1; return list(p)
    return None
fails=[]
for ti,W in enumerate(sorted(targets, key=lambda w: len(CLS.get(w,[])))):
    As=list(class_As(W))
    if not As:
        plan[W]={"W":[t2s(x) for x in sorted(W)],"codes":[]}; fails.append((W,"no-req")); continue
    unc=set(range(len(As)))
    codes=[]
    guard=0
    while unc and guard<4000:
        guard+=1
        i=min(unc, key=lambda j: sum(As[j]))
        A=As[i]; tl=[]
        for t,n in enumerate(A): tl+=[t]*n
        best=None; bc=0
        for pat in set(itertools.combinations_with_replacement(tl,K)):
            if used[pat]>=nperm(pat): continue
            cnt=0
            for j in unc:
                Aj=As[j]
                ok=True
                for t in set(pat):
                    if Aj[t]<pat.count(t): ok=False; break
                if ok: cnt+=1
            if cnt>bc: bc=cnt; best=pat
        if best is None: break
        cd=take(best)
        if cd is None: break
        codes.append(cd)
        newunc=set()
        for j in unc:
            Aj=As[j]; ok=True
            for t in set(best):
                if Aj[t]<best.count(t): ok=False; break
            if not ok: newunc.add(j)
        unc=newunc
    plan[W]={"W":[t2s(x) for x in sorted(W)],"codes":codes}
    if unc: fails.append((W,"uncoveredA",len(unc)))
    if not codes: fails.append((W,"empty"))
    if (ti+1)%50==0: log("  %d/%d codes=%d fails=%d"%(ti+1,len(targets),sum(used.values()),len(fails)))
out=[]
for W,v in plan.items():
    out.append({"W":v["W"],"codes":v["codes"]})
allc=[tuple(c) for e in out for c in e["codes"]]
log("classes=%d codes=%d distinct=%d dups=%d empty=%d fails=%d"%(len(out),len(allc),len(set(allc)),len(allc)-len(set(allc)),sum(1 for e in out if not e["codes"]),len(fails)))
log("fail kinds:", dict(collections.Counter(f[1] for f in fails)))
json.dump({"k":4,"n_classes":len(out),"n_codes":len(set(allc)),"plan":out},
          open(r"D:\DSH\MJ2\work\recon\plan_k4_u2.json","w"))
log("written plan_k4_u2.json")