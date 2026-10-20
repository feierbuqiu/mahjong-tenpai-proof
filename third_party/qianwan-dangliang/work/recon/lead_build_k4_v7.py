# -*- coding: utf-8 -*-
"""Lead k=4 v7: 
   - 每块 minA>=K -> 一条码 ⊆ minA;
   - 块 minA<K -> 若该类有共同牌集 I(!=空) 则用容量丰富的族:
       triplet a: (a,a,u,v)  (u,v ∈ I)
       run abc : (a,b,c,u)  (u ∈ I)
     否则逐 A 贪心;
   - 全部码容量感知(4-多重集的使用次数 <= 排列数), 有序码全局唯一。"""
import pickle, itertools, math, collections, time, json
T0=time.time()
def log(*a): print("[%7.1fs]"%(time.time()-T0), *a, flush=True)
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
used=collections.Counter(); PERMC={}
def perms_of(m):
    if m not in PERMC: PERMC[m]=sorted(set(itertools.permutations(m)))
    return PERMC[m]
def take(m):
    ps=perms_of(m); u=used[m]
    if u>=len(ps): return None
    used[m]=u+1; return list(ps[u])
def tiles(cats): return [CB[c]+i for c in cats for i in range(CL[c])]
def runs(cats):
    out=[]
    for c in cats:
        if c<3: out += [(CB[c]+i,CB[c]+i+1,CB[c]+i+2) for i in range(7)]
    return out
def family(I, cats):
    out=set(); I=sorted(I)
    for a in tiles(cats):
        for ui,u in enumerate(I):
            for v in I[ui:]:
                out.add(tuple(sorted((a,a,u,v))))
        for u in I:
            out.add(tuple(sorted((a,a,a,u))))
    for r in runs(cats):
        for u in I:
            out.add(tuple(sorted(r+(u,))))
    return out
def covers(pat,A):
    for t in set(pat):
        if A[t]<pat.count(t): return False
    return True
plan={}; stats=collections.Counter(); fails=[]
for idx,(W,blocks) in enumerate(CLS.items()):
    # 分组 + 单位
    groups=collections.defaultdict(list); units=[]; allA=[]
    for b in blocks:
        kind,k1,k2,mode,z,am,nsrc=b
        if kind=="I":
            c,s,pkey=k1; am_,xs=PI[(c,s,pkey)]
            inert=tuple(x for x in range(4) if x!=c)
            groups[inert].append(("tri",None))
            As=[v34(c,X) for X in xs]
        elif kind=="II":
            c1,s1,k1x=k1; c2,s2,k2x=k2
            am1,xs1=PII[(c1,s1,k1x)]; am2,xs2=PII[(c2,s2,k2x)]
            inert=tuple(x for x in range(4) if x not in (c1,c2))
            amv=tuple(a+b for a,b in zip(v34(c1,am1),v34(c2,am2)))
            if sum(amv)>=K:
                units.append(amv); allA.append(amv); continue
            groups[inert].append(("tri",None))
            if len(xs1)*len(xs2)<=20000:
                As=[]
                for X1 in xs1:
                    v1=v34(c1,X1)
                    for X2 in xs2:
                        As.append(tuple(a+b for a,b in zip(v1,v34(c2,X2))))
            else:
                As=[amv]
        else:
            units.append(tuple(1 if (t in (0,8,9,17,18,26) or 27<=t<=33) else 0 for t in range(34)))
            continue
        allA.extend(As)
    # I = 交集
    I=None
    for A in allA:
        sup={i for i,n in enumerate(A) if n}
        I = sup if I is None else (I & sup)
        if not I: break
    I = I or set()
    codes=[]
    # 1) 单位覆盖(容量感知贪心)
    units=list(set(units))
    if units:
        unc=set(range(len(units)))
        while unc:
            i=min(unc,key=lambda j: sum(units[j])); A=units[i]
            tl=[]
            for t,n in enumerate(A): tl+=[t]*n
            best=None; bc=0
            for pat in set(itertools.combinations_with_replacement(tl,K)):
                if used[pat]>=nperm(pat): continue
                cnt=sum(1 for j in unc if covers(pat,units[j]))
                if cnt>bc: bc=cnt; best=pat
            if best is None: break
            cd=take(best)
            if cd is None: break
            codes.append(cd); unc={j for j in unc if not covers(best,units[j])}
        if unc: fails.append((W,"unit",len(unc)))
    # 2) 族覆盖
    for inert in groups:
        if not I:
            fails.append((W,"no-anchor",len(groups[inert]))); stats["no_anchor"]+=1; continue
        fam=family(I, inert)
        miss=0; got=0
        for pat in fam:
            cd=take(pat)
            if cd: codes.append(cd); got+=1
            else: miss+=1
        stats["fam"]+=1
        if miss: fails.append((W,"fam-partial",miss))
    plan[W]={"codes":codes}
    if not codes: fails.append((W,"empty",0))
    if (idx+1)%400==0: log("  %d/%d codes=%d fails=%d"%(idx+1,len(CLS),sum(used.values()),len(fails)))
allc=[tuple(c) for v in plan.values() for c in v["codes"]]
log("DONE classes=%d codes=%d distinct=%d dups=%d fails=%d stats=%s"%(len(plan),len(allc),len(set(allc)),len(allc)-len(set(allc)),len(fails),dict(stats)))
log("fail kinds:", dict(collections.Counter(f[1] for f in fails)))
def t2s(t):
    L="mpsz"; return ("%d%s"%((t%9)+1,L[t//9])) if t<27 else ("%dz"%((t-27)+1))
json.dump({"k":K,"n_classes":len(plan),"n_codes":len(allc),
 "plan":[{"W":[t2s(x) for x in sorted(W)],"codes":v["codes"]} for W,v in plan.items()],
 "fails":[[[t2s(x) for x in sorted(W)],k,n] for (W,k,n) in fails[:300]]},
 open(r"D:\DSH\MJ2\work\recon\plan_k4_v7.json","w"))
log("written plan_k4_v7.json")
