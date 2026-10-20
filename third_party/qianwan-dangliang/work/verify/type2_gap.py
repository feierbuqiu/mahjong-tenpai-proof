
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""type2_gap.py -- 导出"同类覆盖 = 0"的确切类清单与证据 (可复现).
来源: work/verify/perclass_coverage.json 的 fully_uncovered; 对每类抽样构造手牌(用该类来源块),
手牌归属由独立 compute_W 判定 === 该类; 统计本类码命中 / 全局码命中 / 一条未覆盖手牌,
并记录该类来源块的 kind 组成 (I/II/KOK) 与样本手牌的来源块号.
输出 work/verify/type2_gap.json
"""
import sys, os, json, pickle, random
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE,"..","strategy"))
import numpy as np
from indep_core import compute_W
from collections import Counter
HON=["E","S","W","N","Haku","Hatsu","Chun"]
def nm(t): return ("%d%s"%(t%9+1,"mps"[t//9])) if t<27 else HON[t-27]
BASE=[0,9,18,27]
C=pickle.load(open(os.path.join(HERE,"..","strategy","out","table_cache.pkl"),"rb"))
CLS,PROFI_D,PROFII_D=C["cls"],C["PROFI_D"],C["PROFII_D"]
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
DEC={i:build_dec(i) for i in range(4)}
def cmat(codes):
    M=np.zeros((len(codes),34),dtype=np.int8)
    for i,c in enumerate(codes):
        for t in c: M[i,t]+=1
    return M
P=json.load(open(os.path.join(HERE,"plan_k4_final.json"),encoding="utf-8"))
plan={frozenset(r["W"]):cmat(r["codes"]) for r in P["plan"]}
ALLM=np.vstack([cmat(r["codes"]) for r in P["plan"]])
cov=json.load(open(os.path.join(HERE,"perclass_coverage.json"),encoding="utf-8"))
targets=[frozenset(x) for x in json.load(open(os.path.join(HERE,"_targets.json"),encoding="utf-8"))] if os.path.exists(os.path.join(HERE,"_targets.json")) else None
def gen(W,rng):
    blocks=CLS[W]; bi=rng.randrange(len(blocks)); b=blocks[bi]
    for _ in range(80):
        A=[0]*34; ok=True
        if b[0]=="I":
            e=PROFI_D.get(b[1])
            if not e: return None,None
            X=e[1][rng.randrange(len(e[1]))]
            for i,x in enumerate(X): A[BASE[b[1][0]]+i]=x
            rem=13-b[1][1]; cats=[i for i in range(4) if i!=b[1][0]]
        elif b[0]=="II":
            e1,e2=PROFII_D.get(b[1]),PROFII_D.get(b[2])
            if not e1 or not e2: return None,None
            for i,x in enumerate(e1[1][rng.randrange(len(e1[1]))]): A[BASE[b[1][0]]+i]=x
            for i,x in enumerate(e2[1][rng.randrange(len(e2[1]))]): A[BASE[b[2][0]]+i]=x
            rem=13-b[1][1]-b[2][1]; cats=[i for i in range(4) if i not in (b[1][0],b[2][0])]
        else: return None,None
        for ii,ci in enumerate(cats):
            left=len(cats)-ii-1
            opts=[s for s in range(0,rem+1,3) if rem-s<=12*left and (s==0 or DEC[ci].get(s))]
            if not opts: ok=False; break
            s=opts[rng.randrange(len(opts))]
            if s:
                v=DEC[ci][s][rng.randrange(len(DEC[ci][s]))]
                for i,x in enumerate(v): A[BASE[ci]+i]=x
            rem-=s
        if ok and sum(A)==13 and max(A)<=4: return A,bi
    return None,None
rows=[]
wl=[frozenset(int(t) if isinstance(t,int) else t for t in x) for x in []]
for entry in cov["fully_uncovered"]:
    W=frozenset()
    # 由名字转回索引
    HONI={"E":27,"S":28,"W":29,"N":30,"Haku":31,"Hatsu":32,"Chun":33}
    idxs=[]
    for x in entry["W"]:
        idxs.append(HONI[x] if x in HONI else "mps".index(x[-1])*9+int(x[0])-1)
    W=frozenset(idxs)
    kinds=Counter(b[0] for b in CLS.get(W,[]))
    rng=random.Random(31337 ^ (hash(tuple(sorted(W))) & 0xffff))
    tested=0; same=0; glob=0; ex=None; exbi=None
    for _ in range(40):
        A,bi=gen(W,rng)
        if A is None: continue
        if frozenset(compute_W(A))!=W: continue
        tested+=1
        v=np.array(A,dtype=np.int8)
        M=plan.get(W)
        s=int(((M<=v).all(axis=1)).sum()) if M is not None and len(M) else 0
        g=int(((ALLM<=v).all(axis=1)).sum())
        same+=s; glob+=g
        if s==0 and ex is None: ex=A; exbi=bi
    rows.append({"W":[nm(t) for t in sorted(W)],"blocks_kinds":dict(kinds),"n_blocks":len(CLS.get(W,[])),
                 "baseline_codes":int(len(plan[W])),"hands_verified":tested,"same_class_hits":same,
                 "global_hits":glob,"example_uncovered_hand":("".join(nm(t)*ex[t] for t in range(34)) if ex is not None else None),
                 "example_source_block_index":exbi})
out={"plan":os.path.join(HERE,"plan_k4_final.json"),
     "criterion":"MODEL.md line 29-31: S_C ⊆ ∪_{H∈C}M_k(H); S_C 必命中类内每一手牌; 各类码集两两不交",
     "source":"work/verify/perclass_coverage.json:fully_uncovered",
     "classes":rows,"n_uncovered":len(rows),"hands_total":sum(r['hands_verified'] for r in rows),
     "same_class_hits_total":sum(r['same_class_hits'] for r in rows),
     "global_hits_total":sum(r['global_hits'] for r in rows)}
json.dump(out, open(os.path.join(HERE,"type2_gap.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("无同类覆盖类: %d ; 抽样手牌 %d ; 同类命中合计 %d ; 全局命中合计 %d" %
      (len(rows),out["hands_total"],out["same_class_hits_total"],out["global_hits_total"]))
print("这些类的来源块 kind 组成 (类计数):", Counter(tuple(sorted(r["blocks_kinds"].items())) for r in rows))
print("无覆盖手牌来源块 kind 组成:", Counter(tuple(sorted(r["blocks_kinds"].items())) for r in rows).most_common(3))
for r in rows[:6]:
    print("   %-26s 块=%s 本类码=%4d 手牌=%2d 同类命中=%d 全局命中=%d 例:%s" %
          (",".join(r["W"])[:26],r["blocks_kinds"],r["baseline_codes"],r["hands_verified"],r["same_class_hits"],r["global_hits"],r["example_uncovered_hand"]))
print("已写 work/verify/type2_gap.json")
