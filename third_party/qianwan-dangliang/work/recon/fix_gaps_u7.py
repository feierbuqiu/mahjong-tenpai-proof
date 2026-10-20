# -*- coding: utf-8 -*-
"""Lead v11: 目标类按"类级二元覆盖 + 补牌面子码"重建。产物 plan_k4_u7.json (= u1 ∪ v11 目标类码)"""
import pickle, itertools, math, collections, json, time
T0=time.time()
def log(*a): print("[%6.1fs]"%(time.time()-T0), *a, flush=True)
K=4
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
def tiles(cats): return [CB[c]+i for c in cats for i in range(CL[c])]
def runs(cats):
    out=[]
    for c in cats:
        if c<3: out += [(CB[c]+i,CB[c]+i+1,CB[c]+i+2) for i in range(7)]
    return out
u1=json.load(open(r"D:\DSH\MJ2\work\recon\plan_k4_u6.json"))["plan"]
rep=json.load(open(r"D:\DSH\MJ2\work\verify\fastcov_report.json"))
targets=set()
for e in u1:
    if not e.get("codes"): targets.add(keyof(e["W"]))
for sname,info in rep.get("suits",{}).items():
    for it in info.get("top",[]): targets.add(keyof(it["W"]))
log("targets:",len(targets))
used=collections.Counter(); usedset=set(); keep={}
for e in u1:
    W=keyof(e["W"])
    if W in targets: continue
    for c in e.get("codes",[]):
        c=tuple(c); used[c]+=1; usedset.add(c)
    keep[W]=[tuple(c) for c in e.get("codes",[])]
PERMC={}
def perms_of(m):
    if m not in PERMC: PERMC[m]=sorted(set(itertools.permutations(m)))
    return PERMC[m]
def take(m):
    for p in perms_of(m):
        if p not in usedset: usedset.add(p); used[m]+=1; return list(p)
    return None
def put(pat, out):
    if len(pat)!=K or used[pat]>=nperm(pat): return False
    cd=take(pat)
    if cd is None: return False
    out.append(cd); return True
def put_tri(u,v,f,out):
    for pat in [tuple(sorted((u,v,f,f))),tuple(sorted((u,u,f,f))),tuple(sorted((v,v,f,f))),tuple(sorted((u,f,f,f)))]:
        if put(pat,out): return True
    return False
def put_run(u,v,r,out):
    f1,f2,f3=r
    for pat in [tuple(sorted((u,v,f1,f2))),tuple(sorted((u,v,f2,f3))),tuple(sorted((u,f1,f2,f3))),tuple(sorted((v,f1,f2,f3)))]:
        if put(pat,out): return True
    return False
newcodes={}
for ti,W in enumerate(sorted(targets, key=lambda w: len(CLS.get(w,[])))):
    blocks=CLS.get(W,[]); As=[]; inerts=set()
    for b in blocks:
        kind,k1,k2,mode,z,am,nsrc=b
        if kind=="I":
            c,s,pkey=k1; am_,xs=PI[(c,s,pkey)]
            inerts |= {x for x in range(4) if x!=c}
            As += [v34(c,X) for X in xs]
        elif kind=="II":
            c1,s1,k1x=k1; c2,s2,k2x=k2
            am1,xs1=PII[(c1,s1,k1x)]; am2,xs2=PII[(c2,s2,k2x)]
            inerts |= {x for x in range(4) if x not in (c1,c2)}
            if len(xs1)*len(xs2)<=4000:
                As += [tuple(a+b for a,b in zip(v34(c1,X1),v34(c2,X2))) for X1 in xs1 for X2 in xs2]
            else:
                As.append(tuple(a+b for a,b in zip(v34(c1,am1),v34(c2,am2))))
        else:
            inerts |= set(range(4))
            As.append(tuple(1 if (t in (0,8,9,17,18,26) or 27<=t<=33) else 0 for t in range(34)))
    As=list(set(As))
    codes=[]; unc=set(range(len(As))); guard=0
    while unc and guard<60:
        guard+=1
        best=None; bc=0
        for u in range(34):
            for v in range(u,34):
                cnt=0
                for j in unc:
                    Aj=As[j]
                    if Aj[u]>=1 and Aj[v]>=1 and (u!=v or Aj[u]>=2): cnt+=1
                if cnt>bc: bc=cnt; best=(u,v)
        if best is None or bc==0: break
        u,v=best
        for f in tiles(inerts): put_tri(u,v,f,codes)
        for r in runs(inerts): put_run(u,v,r,codes)
        unc={j for j in unc if not (As[j][u]>=1 and As[j][v]>=1 and (u!=v or As[j][u]>=2))}
    # F=∅ 的手牌(|A|=13): 需要码 ⊆ A
    for A in As:
        if sum(A)==13:
            tl=[t for t,n in enumerate(A) for _ in range(n)]
            if tl:
                for pat in set(itertools.combinations_with_replacement(tl,K)):
                    if put(pat,codes): break
    if unc: 
        pass
    newcodes[W]=(codes, len(unc))
    if (ti+1)%40==0: log("  %d/%d codes=%d"%(ti+1,len(targets),sum(used.values())))
out=[]; added=0
allW=list(keep.keys())+list(newcodes.keys())
for W in set(list(keep.keys())+list(newcodes.keys())):
    codes=list(keep.get(W,[]))
    for c in newcodes.get(W,([],0))[0]:
        codes.append(tuple(c)); added+=1
    out.append({"W":[t2s(x) for x in sorted(W)],"codes":[list(c) for c in codes]})
allc=[tuple(c) for e in out for c in e["codes"]]
log("classes=%d codes=%d distinct=%d added=%d empty=%d"% (len(out),len(allc),len(set(allc)),added,sum(1 for e in out if not e["codes"])))
json.dump({"k":4,"n_classes":len(out),"n_codes":len(set(allc)),"plan":out}, open(r"D:\DSH\MJ2\work\recon\plan_k4_u7.json","w"))
log("written plan_k4_u7.json")