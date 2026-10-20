
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""perclass_coverage.py <plan.json> [hands_per_class] -- 缺失的验收线: 逐类"同类覆盖"抽样审计.

对每个类 C: 从其来源块 (cls[W] 的 I/II/KOK) 随机构造手牌, 用独立 compute_W 确认 W(H)==C,
再检查 S_C 中是否存在码 c ⊆ H (同类覆盖). 报告没有任何同类覆盖的类 (= 该类的手牌无法被
本类码覆盖 => k=4 方案在该类上失效).
输出 work/verify/perclass_coverage.json
"""
import sys, os, json, pickle, random
import numpy as np
from multiprocessing import Pool
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "strategy"))
from indep_core import compute_W
BASE=[0,9,18,27]
HON=["E","S","W","N","Haku","Hatsu","Chun"]
def nm(t): return ("%d%s"%(t%9+1,"mps"[t//9])) if t<27 else HON[t-27]
HONI={"E":27,"S":28,"W":29,"N":30,"Haku":31,"Hatsu":32,"Chun":33}
def _to_idx(x):
    if isinstance(x,int): return x
    if x in HONI: return HONI[x]
    return "mps".index(x[-1])*9+int(x[0])-1
_DEC={}
def build_dec(idx):
    L=7 if idx==3 else 9; units=[]
    if idx<3:
        for st in range(L-2):
            v=[0]*L; v[st]=1; v[st+1]=1; v[st+2]=1; units.append(tuple(v))
    for t in range(L):
        v=[0]*L; v[t]=3; units.append(tuple(v))
    out={}
    for s in range(0,13,3):
        res=set()
        def rec(i,left,acc):
            if left==0: res.add(acc); return
            for j in range(i,len(units)):
                u=units[j]
                if all(acc[k]+u[k]<=4 for k in range(L)): rec(j,left-3,tuple(acc[k]+u[k] for k in range(L)))
        rec(0,s,(0,)*L)
        out[s]=sorted(res)
    return out
_G={}
def init_worker():
    global CLS,PROFI_D,PROFII_D,PLAN
    PLANP=sys.argv[1] if len(sys.argv)>1 else os.path.join(HERE,"plan_k4_final.json")
    C=pickle.load(open(os.path.join(HERE,"..","strategy","out","table_cache.pkl"),"rb"))
    CLS,PROFI_D,PROFII_D=C["cls"],C["PROFI_D"],C["PROFII_D"]
    P=json.load(open(PLANP,encoding="utf-8"))
    PLAN={}
    for r in P["plan"]:
        Wk=frozenset(_to_idx(x) for x in r["W"])
        r=dict(r); r["W"]=Wk
        n=len(r["codes"])
        M=np.zeros((n,34),dtype=np.int8)
        for i,c in enumerate(r["codes"]):
            for t in c: M[i,t]+=1
        PLAN[r["W"]]=M
    for i in range(4): _G[i]=build_dec(i)
def make_hand(W, rng):
    blocks=CLS.get(W,[])
    if not blocks: return None
    b=blocks[rng.randrange(len(blocks))]
    for _ in range(60):
        A=[0]*34; ok=True
        if b[0]=="I":
            e=PROFI_D.get(b[1]); 
            if not e: return None
            X=e[1][rng.randrange(len(e[1]))]
            for i,x in enumerate(X): A[BASE[b[1][0]]+i]=x
            rem=13-b[1][1]; cats=[i for i in range(4) if i!=b[1][0]]
        elif b[0]=="II":
            e1,e2=PROFII_D.get(b[1]),PROFII_D.get(b[2])
            if not e1 or not e2: return None
            for i,x in enumerate(e1[1][rng.randrange(len(e1[1]))]): A[BASE[b[1][0]]+i]=x
            for i,x in enumerate(e2[1][rng.randrange(len(e2[1]))]): A[BASE[b[2][0]]+i]=x
            rem=13-b[1][1]-b[2][1]; cats=[i for i in range(4) if i not in (b[1][0],b[2][0])]
        else:
            # KOK 来源: 该类手牌 = 13 张幺九各一张 (13 面) 或 12 张其它幺九 + 任一张重复 (缺一张)
            ORPH=[0,8,9,17,18,26]+list(range(27,34))
            S=sorted(W)
            base=[o for o in ORPH if o not in S]
            fam=[]
            if len(S)==13:
                h=[0]*34
                for o in ORPH: h[o]=1
                fam.append(h)
            elif len(S)==1:
                for d in base:
                    h=[0]*34
                    for o in base: h[o]=1
                    h[d]+=1
                    fam.append(h)
            if fam: return fam[rng.randrange(len(fam))]
        for ii,ci in enumerate(cats):
            left=len(cats)-ii-1
            opts=[s for s in range(0,rem+1,3) if rem-s<=12*left and (s==0 or _G[ci].get(s))]
            if not opts: ok=False; break
            s=opts[rng.randrange(len(opts))]
            if s:
                v=_G[ci][s][rng.randrange(len(_G[ci][s]))]
                for i,x in enumerate(v): A[BASE[ci]+i]=x
            rem-=s
        if ok and sum(A)==13 and max(A)<=4: return A
    return None
def work(item):
    W, hs = item
    rng=random.Random(1000003 ^ (hash(tuple(sorted(W))) & 0xffff))
    codes=PLAN.get(W)
    okc=0; nu=0; ex=None; nblocks=len(CLS.get(W,[]))
    for _ in range(hs):
        A=make_hand(W,rng)
        if A is None: continue
        if frozenset(compute_W(A))!=W: continue
        nu+=1
        if codes is not None and len(codes):
            v=np.array(A,dtype=np.int8)
            hit=bool(((codes<=v).all(axis=1)).any())   # codes 为 (n,34) 计数矩阵
        else: hit=False
        if hit: okc+=1
        elif ex is None: ex=A
    return {"W":[nm(t) for t in sorted(W)],"codes":0 if codes is None else len(codes),
            "hands_tested":nu,"covered":okc,"blocks":nblocks,
            "example_uncovered":("".join(nm(t)*ex[t] for t in range(34)) if ex else None)}
if __name__=="__main__":
    PLANP=sys.argv[1] if len(sys.argv)>1 else os.path.join(HERE,"plan_k4_final.json")
    HS=int(sys.argv[2]) if len(sys.argv)>2 else 30
    import pickle as pk
    C=pk.load(open(os.path.join(HERE,"..","strategy","out","table_cache.pkl"),"rb"))
    keys=list(C["cls"].keys())
    nproc=min(12,os.cpu_count() or 4)
    with Pool(nproc, initializer=init_worker) as pool:
        res=pool.map(work, [(W,HS) for W in keys], chunksize=max(1,len(keys)//(nproc*16)))
    tested=[r for r in res if r["hands_tested"]>0]
    bad=[r for r in tested if r["covered"]==0]
    partial=[r for r in tested if 0<r["covered"]<r["hands_tested"]]
    out={"plan":PLANP,"hands_per_class":HS,"classes_tested":len(tested),
         "fully_uncovered_classes":len(bad),"partially_uncovered_classes":len(partial),
         "fully_uncovered":sorted(bad,key=lambda r:(r["blocks"],r["W"])),
         "partial":[{"W":r["W"],"tested":r["hands_tested"],"covered":r["covered"]} for r in partial]}
    json.dump(out, open(os.path.join(HERE,"perclass_coverage.json"),"w"), ensure_ascii=False, indent=1)
    print("类数(实测手牌)=%d  完全无同类覆盖=%d  部分=%d" % (len(tested),len(bad),len(partial)))
    from collections import Counter
    print("完全无覆盖类的块类型:", Counter(r["blocks"] for r in bad))
    for r in sorted(bad,key=lambda r:(r["blocks"],r["W"]))[:12]:
        print("   %-26s 本类码=%4d 测试手牌=%2d 覆盖=0  例: %s" % (",".join(r["W"])[:26],r["codes"],r["hands_tested"],r["example_uncovered"]))
    print("写出 work/verify/perclass_coverage.json")
