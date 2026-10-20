# -*- coding: utf-8 -*-
"""Lead: k=4 构造 v6 —— 块级：minA>=K 用单码；minA<K 用"锚牌+补牌族"覆盖；否则逐 A。容量感知。"""
import pickle, itertools, math, collections, time, sys
T0=time.time()
def log(*a): print("[%7.1fs]"%(time.time()-T0), *a, flush=True)
K=4
T=pickle.load(open(r"D:\DSH\MJ2\work\recon\table_perA.pkl","rb"))
CLS, PI, PII = T["cls"], T["PROFI_D"], T["PROFII_D"]
CAT_BASE=[0,9,18,27]; CAT_LEN=[9,9,9,7]
def cat_of(t): return t//9 if t<27 else 3
def v34(c,X):
    base=CAT_BASE[c]; v=[0]*34
    for i,n in enumerate(X):
        if n: v[base+i]=n
    return tuple(v)
def nperm(mult):
    f=1
    for x in set(mult): f*=math.factorial(mult.count(x))
    return 24//f
used=collections.Counter()
PERMC={}
def perms_of(mult):
    if mult not in PERMC: PERMC[mult]=sorted(set(itertools.permutations(mult)))
    return PERMC[mult]
def take(mult):
    ps=perms_of(mult); u=used[mult]
    if u>=len(ps): return None
    used[mult]=u+1
    return list(ps[u])
def tiles_of_cats(cats):
    out=[]
    for c in cats: out += [CAT_BASE[c]+i for i in range(CAT_LEN[c])]
    return out
def runs_of_cats(cats):
    out=[]
    for c in cats:
        if c<3:
            for i in range(7): out.append((CAT_BASE[c]+i, CAT_BASE[c]+i+1, CAT_BASE[c]+i+2))
    return out
def family_patterns(x, cats):
    out=set()
    for a in tiles_of_cats(cats): out.add(tuple(sorted((x,a,a,a))))
    for r in runs_of_cats(cats):
        for extra in tiles_of_cats(cats):
            out.add(tuple(sorted((x,)+r+(extra,))))
    return out
def covers(pat, A):
    for t in set(pat):
        if A[t] < pat.count(t): return False
    return True

plan={}; stats=collections.Counter(); fails=[]
for idx,(W,blocks) in enumerate(CLS.items()):
    units=[]; fams=[]
    for b in blocks:
        kind,k1,k2,mode,z,am,nsrc = b
        if kind=="I":
            c,s,pkey=k1; am_,xs=PI[(c,s,pkey)]
            As=[v34(c,X) for X in xs]
            if sum(am_)>=K:
                units.append(tuple(am_)); stats["unit_minA"]+=1
            else:
                common=None
                for A in As:
                    sup={i for i,n in enumerate(A) if n}
                    common = sup if common is None else (common & sup)
                    if not common: break
                if common:
                    fams.append((sorted(common), (c,))); stats["fam_I"]+=1
                else:
                    units.extend(As); stats["perA_I"]+=1
        elif kind=="II":
            c1,s1,k1x=k1; c2,s2,k2x=k2
            am1,xs1=PII[(c1,s1,k1x)]; am2,xs2=PII[(c2,s2,k2x)]
            a1=v34(c1,am1); a2=v34(c2,am2); amv=tuple(x+y for x,y in zip(a1,a2))
            if sum(amv)>=K:
                units.append(amv); stats["unit_minA_II"]+=1
            else:
                if len(xs1)*len(xs2)<=20000:
                    As=set()
                    for X1 in xs1:
                        v1=v34(c1,X1)
                        for X2 in xs2:
                            v2=v34(c2,X2)
                            As.add(tuple(x+y for x,y in zip(v1,v2)))
                else:
                    As={amv}; stats["big_prod"]+=1
                common=None
                for A in As:
                    sup={i for i,n in enumerate(A) if n}
                    common = sup if common is None else (common & sup)
                    if not common: break
                if common:
                    fams.append((sorted(common), (c1,c2))); stats["fam_II"]+=1
                else:
                    units.extend(As); stats["perA_II"]+=1
        else:
            units.append(tuple(1 if t in (0,8,9,17,18,26) or 27<=t<=33 else 0 for t in range(34)))
            stats["kok"]+=1
    units=list(set(units))
    codes=[]
    # ---- units: 容量感知贪心 ----
    if units:
        unc=set(range(len(units)))
        # 候选: 从小 A 的 unit 生成
        while unc:
            i=min(unc, key=lambda j: sum(units[j]))
            A=units[i]
            tl=[]
            for t,n in enumerate(A): tl += [t]*n
            best=None; bc=0
            for pat in set(itertools.combinations_with_replacement(tl,K)):
                if used[pat]>=nperm(pat): continue
                cnt=0
                for j in unc:
                    if covers(pat, units[j]): cnt+=1
                if cnt>bc: bc=cnt; best=pat
            if best is None: break
            cd=take(best)
            if cd is None: break
            codes.append(cd)
            unc={j for j in unc if not covers(best, units[j])}
        if unc: fails.append((W,"unit-uncovered",len(unc)))
    # ---- families ----
    for anchors, cats in fams:
        pats=family_patterns(anchors[0], cats)
        ok=all(used[p]<nperm(p) for p in pats)
        if not ok:
            # 换锚
            for x in anchors[1:]:
                p2=family_patterns(x, cats)
                if all(used[p]<nperm(p) for p in p2): pats=p2; ok=True; break
        if not ok:
            # 只加未满的
            pats={p for p in pats if used[p]<nperm(p)}
            fails.append((W,"fam-partial",0))
        for p in pats:
            cd=take(p)
            if cd: codes.append(cd)
    plan[W]={"codes":codes}
    if not codes: fails.append((W,"empty",0))
    if (idx+1)%300==0:
        log("  %d/%d codes=%d fails=%d stats=%s"%(idx+1,len(CLS),sum(used.values()),len(fails),dict(stats)))
allc=[tuple(c) for v in plan.values() for c in v["codes"]]
log("DONE classes=%d codes=%d distinct=%d dups=%d fails=%d"%(len(plan),len(allc),len(set(allc)),len(allc)-len(set(allc)),len(fails)))
log("stats:", dict(stats))
from collections import Counter as C2
log("fail kinds:", dict(C2(f[1] for f in fails)))
import json
def t2s(t):
    L="mpsz"
    return ("%d%s"%((t%9)+1,L[t//9])) if t<27 else ("%dz"%((t-27)+1))
json.dump({"k":K,"n_classes":len(plan),"n_codes":len(allc),
  "plan":[{"W":[t2s(x) for x in sorted(W)],"codes":v["codes"]} for W,v in plan.items()],
  "fails":[[ [t2s(x) for x in sorted(W)],k,n] for (W,k,n) in fails[:200]]},
  open(r"D:\DSH\MJ2\work\recon\plan_k4_v6.json","w"))
log("written plan_k4_v6.json")
