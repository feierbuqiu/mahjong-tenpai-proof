# -*- coding: utf-8 -*-
"""t12_hard_bases.py v2 (memory-lean) -- exact coverage check for the 285 standard-type
bases where no plan code already fits the active part A.
For every filler F (union of melds in the inert categories) we require some class code
to be a sub-multiset of A+F.  Violating F's are engine-verified before reporting.
"""
import sys, os, json, time, gc
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from mjcore import *
from collections import Counter

D=os.path.dirname(os.path.abspath(__file__))
BASE=[0,9,18,27]; LEN=[9,9,9,7]
PLANF="D:/DSH/MJ2/work/verify/plan_k4_FINAL.json"
P=json.load(open(PLANF,encoding="utf-8"))
PLAN={}
for r in P["plan"]:
    W=frozenset(nm_idx(x) for x in r["W"])
    PLAN[W]=[tuple(sorted(Counter(nm_idx(t) for t in c).items())) for c in r["codes"]]

MELDS={}
for ci in range(4):
    lst=[]
    for i in range(LEN[ci]):
        v=[0]*34; v[BASE[ci]+i]=3; lst.append(tuple(v))
    if ci<3:
        for i in range(LEN[ci]-2):
            v=[0]*34
            for k in range(3): v[BASE[ci]+i+k]=1
            lst.append(v)
    MELDS[ci]=lst

_MC={}
def meld_multisets(ci,s):
    key=(ci,s)
    if key in _MC: return _MC[key]
    if s==0:
        _MC[key]=[tuple([0]*34)]; return _MC[key]
    out=[]; ms=MELDS[ci]
    acc=[0]*34
    def rec(i,left):
        if left==0:
            out.append(tuple(acc)); return
        for j in range(i,len(ms)):
            u=ms[j]
            ok=True
            for t in range(34):
                if u[t]:
                    if acc[t]+u[t]>4: ok=False; break
            if not ok: continue
            for t in range(34): acc[t]+=u[t]
            rec(j,left-3)
            for t in range(34): acc[t]-=u[t]
    rec(0,s)
    _MC[key]=out; return out

_FNP={}
def fillers_np(inert,m):
    key=(tuple(inert),m)
    if key in _FNP: return _FNP[key]
    rows=[]
    def rec(i,rem,acc):
        if i==len(inert):
            if rem==0: rows.append(np.array(acc,dtype=np.int8))
            return
        ci=inert[i]
        for s in range(0,min(rem,12)+1,3):
            for v in meld_multisets(ci,s):
                ok=True
                for t in range(34):
                    if v[t]:
                        if acc[t]+v[t]>4: ok=False; break
                if not ok: continue
                for t in range(34): acc[t]+=v[t]
                rec(i+1,rem-s,acc)
                for t in range(34): acc[t]-=v[t]
    rec(0,m,[0]*34)
    if not rows:
        arr=np.zeros((0,34),dtype=np.int8)
    else:
        arr=np.stack(rows)
    del rows; gc.collect()
    _FNP[key]=arr
    return arr

def engine_check(h):
    w=waits(h); cs=PLAN.get(w)
    if cs is None: return ["missing_class"]+[nm(t) for t in sorted(w)]+[hand_str(h)]
    for cod in cs:
        if all(h[t]>=v for t,v in cod): return None
    return ["uncovered"]+[nm(t) for t in sorted(w)]+[hand_str(h)]

if __name__=="__main__":
    t0=time.time()
    hard=json.load(open(D+"/t6_hard_bases.json"))
    print("hard bases:",len(hard),flush=True)
    bad=[]; checked=0
    for bi,b in enumerate(hard):
        Av=from_str(b["A"])
        if sum(Av)!=b["s"] if b["kind"]=="I" else False:
            pass
        inert = tuple(i for i in range(4) if i!=b["c"]) if b["kind"]=="I" else tuple(i for i in range(4) if i not in (b["c1"],b["c2"]))
        m=13-sum(Av)
        W=frozenset(nm_idx(x) for x in b["W"])
        codes=PLAN.get(W)
        if codes is None:
            bad.append({"base":b,"err":"class not in plan"}); continue
        R=[]
        for cod in codes:
            r=[0]*34; ok=True
            for t,v in cod:
                need=v-Av[t]
                if need<=0: continue
                cat=0 if t<9 else (1 if t<18 else (2 if t<27 else 3))
                if cat not in inert: ok=False; break
                r[t]=need
            if ok: R.append(tuple(r))
        R=sorted(set(R), key=lambda r: sum(r))
        Rmin=[]
        for r in R:
            if any(all(r2[t]<=r[t] for t in range(34)) for r2 in Rmin): continue
            Rmin.append(r)
        if not Rmin:
            bad.append({"base":b,"err":"no feasible code"}); continue
        F=fillers_np(inert,m)
        if F.shape[0]==0:
            bad.append({"base":b,"err":"no fillers"}); continue
        good=np.zeros(F.shape[0],dtype=bool)
        for r in Rmin:
            rr=np.array(r,dtype=np.int8)
            good |= (F>=rr).all(axis=1)
        nbad=int((~good).sum())
        checked+=1
        if nbad:
            idx=int(np.argmax(~good))
            h=tuple(int(Av[t])+int(F[idx][t]) for t in range(34))
            ec=engine_check(h)
            bad.append({"base":b,"nbad":nbad,"of":int(F.shape[0]),"F":hand_str(F[idx]),"hand":hand_str(h),"engine":ec})
            print("  BAD base",b["kind"],b["A"],"m",m,"nbad",nbad,"engine",ec,flush=True)
        if bi%40==0:
            print("[%5.0fs] %d/%d hard bases; cache=%d"%(time.time()-t0,bi,len(hard),len(_FNP)),flush=True)
    out={"hard_bases":len(hard),"checked":checked,"bases_with_bad_F":len(bad),"details":bad[:20],"elapsed":round(time.time()-t0,1)}
    json.dump(out,open(D+"/t12_hard_bases.json","w"),ensure_ascii=False,indent=1)
    print(json.dumps({k:v for k,v in out.items() if k!="details"},ensure_ascii=False))
    print("details:",json.dumps(bad[:6],ensure_ascii=False)[:1200])
