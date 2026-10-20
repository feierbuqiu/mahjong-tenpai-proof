# -*- coding: utf-8 -*-
"""Lead v9: 对缺口类做 (a) 单位码(|am|>=K) + (b) 类级锚牌族(容量分散) + (c) 逐 A 退路。产物 plan_k4_u3.json"""
import pickle, itertools, math, collections, json, time
T0=time.time()
def log(*a): print("[%6.1fs]"%(time.time()-T0), *a, flush=True)
K=4
T=pickle.load(open(r"D:\DSH\MJ2\work\recon\table_perA.pkl","rb"))
CLS,PI,PII=T["cls"],T["PROFI_D"],T["PROFII_D"]
CB=[0,9,18,27]; CL=[9,9,9,7]
HON=["E","S","W","N","Haku","Hatsu","Chun"]
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
def tiles(cats): return [CB[c]+i for c in cats for i in range(CL[c])]
def runs(cats):
    out=[]
    for c in cats:
        if c<3: out += [(CB[c]+i,CB[c]+i+1,CB[c]+i+2) for i in range(7)]
    return out
u1=json.load(open(r"D:\DSH\MJ2\work\recon\plan_k4_u1.json"))["plan"]
rep=json.load(open(r"D:\DSH\MJ2\work\verify\fastcov_report.json"))
targets=set()
for e in u1:
    if not e.get("codes"): targets.add(keyof(e["W"]))
for sname,info in rep.get("suits",{}).items():
    for it in info.get("top",[]): targets.add(keyof(it["W"]))
log("targets:",len(targets))
used=collections.Counter(); usedset=set(); plan={}
for e in u1:
    W=keyof(e["W"]); codes=[tuple(c) for c in e.get("codes",[])]
    if W in targets: plan[W]={"W":e["W"],"codes":[]}; continue
    for c in codes: used[c]+=1; usedset.add(c)
    plan[W]={"W":e["W"],"codes":codes}
PERMC={}
def perms_of(m):
    if m not in PERMC: PERMC[m]=sorted(set(itertools.permutations(m)))
    return PERMC[m]
def take(m):
    for p in perms_of(m):
        if p not in usedset: usedset.add(p); used[m]+=1; return list(p)
    return None
def fam_choose(I,cats):
    I=sorted(I); out=[]
    for a in tiles(cats):
        best=None; br=-1
        for ui,u in enumerate(I):
            for v in I[ui:]:
                p=tuple(sorted((a,a,u,v))); r=nperm(p)-used[p]
                if r>br: br=r; best=p
        if best and br>0: out.append(best)
        else:
            for u in I:
                p=tuple(sorted((a,a,a,u))); r=nperm(p)-used[p]
                if r>0: out.append(p); break
    for r0 in runs(cats):
        best=None; br=-1
        for u in I:
            p=tuple(sorted(r0+(u,))); r=nperm(p)-used[p]
            if r>br: br=r; best=p
        if best and br>0: out.append(best)
    return out
fails=[]
for ti,W in enumerate(sorted(targets, key=lambda w: len(CLS.get(w,[])))):
    blocks=CLS.get(W,[]); units=[]; groups=collections.defaultdict(list); allA=[]
    for b in blocks:
        kind,k1,k2,mode,z,am,nsrc=b
        if kind=="I":
            c,s,pkey=k1; am_,xs=PI[(c,s,pkey)]
            As=[v34(c,X) for X in xs]
            inert=tuple(x for x in range(4) if x!=c)
        elif kind=="II":
            c1,s1,k1x=k1; c2,s2,k2x=k2
            am1,xs1=PII[(c1,s1,k1x)]; am2,xs2=PII[(c2,s2,k2x)]
            inert=tuple(x for x in range(4) if x not in (c1,c2))
            amv=tuple(a+b for a,b in zip(v34(c1,am1),v34(c2,am2)))
            if sum(amv)>=K: units.append(amv); allA.append(amv); continue
            if len(xs1)*len(xs2)<=20000:
                As=[tuple(a+b for a,b in zip(v34(c1,X1),v34(c2,X2))) for X1 in xs1 for X2 in xs2]
            else: As=[amv]
        else:
            units.append(tuple(1 if (t in (0,8,9,17,18,26) or 27<=t<=33) else 0 for t in range(34))); continue
        groups[inert].append(As); allA.extend(As)
    I=None
    for A in allA:
        sup={i for i,n in enumerate(A) if n}
        I=sup if I is None else (I&sup)
        if not I: break
    I=I or set()
    codes=[]
    for A in list(set(units)):
        best=None; bc=-1
        tl=[]
        for t,n in enumerate(A): tl+=[t]*n
        for pat in set(itertools.combinations_with_replacement(tl,K)):
            r=nperm(pat)-used[pat]
            if r<=0: continue
            if r>bc: bc=r; best=pat
        if best:
            cd=take(best)
            if cd: codes.append(cd)
    for inert,AsList in groups.items():
        if not I:
            fails.append((W,"no-anchor")); continue
        for pat in fam_choose(I,inert):
            cd=take(pat)
            if cd: codes.append(cd)
            else: fails.append((W,"fam-cap"))
    if not codes: fails.append((W,"empty"))
    plan[W]={"W":[t2s(x) for x in sorted(W)],"codes":codes}
    if I:
        # 逐 A 退路: 对族还覆盖不到的部分, 用 A 自身码(容量感知)
        A_left=None
        # 简化: 若类很小(|A|总数<=400), 直接补 A 码
        allset=list(set(allA))
        if len(allset)<=400 and groups:
            unc=set(range(len(allset)))
            guard=0
            while unc and guard<600:
                guard+=1
                i=min(unc,key=lambda j: sum(allset[j])); A=allset[i]
                tl=[]
                for t,n in enumerate(A): tl+=[t]*n
                best=None; bc=0
                for pat in set(itertools.combinations_with_replacement(tl,K)):
                    if nperm(pat)-used[pat]<=0: continue
                    cnt=sum(1 for j in unc if all(allset[j][t]>=pat.count(t) for t in set(pat)))
                    if cnt>bc: bc=cnt; best=pat
                if best is None: break
                cd=take(best)
                if cd is None: break
                codes.append(cd)
                unc={j for j in unc if not all(allset[j][t]>=best.count(t) for t in set(best))}
    if (ti+1)%50==0: log("  %d/%d codes=%d fails=%d"%(ti+1,len(targets),sum(used.values()),len(fails)))
out=[{"W":v["W"],"codes":v["codes"]} for v in plan.values()]
allc=[tuple(c) for e in out for c in e["codes"]]
log("classes=%d codes=%d distinct=%d empty=%d fails=%d kinds=%s"%(len(out),len(allc),len(set(allc)),sum(1 for e in out if not e["codes"]),len(fails),dict(collections.Counter(f[1] for f in fails))))
json.dump({"k":4,"n_classes":len(out),"n_codes":len(set(allc)),"plan":out}, open(r"D:\DSH\MJ2\work\recon\plan_k4_u3.json","w"))
log("written plan_k4_u3.json")
