# -*- coding: utf-8 -*-
"""patch_k4_leadD.py -- 对 plan_k4_leadC.json 做精确逐单元补码（Lead）
不依赖覆盖率标记：对每个类，用『该类的全部覆盖单元 X』显式验证是否存在码 ⊆ X，缺的补一条。
单元定义：kind I 的每个 X；kind II |am|>=4 的 am，否则按 (X1,X2) 对展开；kokushi 手牌；|X|=1 走 tanki 族。
输出 work/recon/plan_k4_leadD.json
"""
import sys, os, json, collections, itertools, math, time, pickle
import numpy as np
sys.path.insert(0,'work/strategy')
import table_lib
from table_lib import CAT_BASE, MELDS_IN_CAT
HONN=["E","S","W","N","Haku","Hatsu","Chun"]
def nm(t): return ("%d%s"%(t%9+1,"mps"[t//9])) if t<27 else HONN[t-27]
def ti(s): return 27+HONN.index(s) if s in HONN else "mps".index(s[-1])*9+int(s[0])-1
def lift(c,X):
    v=[0]*34
    for i,x in enumerate(X): v[CAT_BASE[c]+i]=x
    return v
FACT=[math.factorial(i) for i in range(5)]
def p4(mu):
    c=collections.Counter(mu); return 24//math.prod(FACT[v] for v in c.values())
def vec4(mu):
    v=[0]*34
    for t in mu: v[t]+=1
    return v
LC={}
def subs4(V):
    k=tuple(V); r=LC.get(k)
    if r is not None: return r
    tiles=[]
    for t,c in enumerate(V):
        for _ in range(min(c,4)): tiles.append(t)
    out=set(); n=len(tiles)
    for a in range(n):
        for b in range(a,n):
            for c in range(b,n):
                for d in range(c,n): out.add((tiles[a],tiles[b],tiles[c],tiles[d]))
    r=list(out); LC[k]=r; return r
T=pickle.load(open('work/strategy/out/table_cache.pkl','rb'))
CLS=T['cls']
P=json.load(open('work/recon/plan_k4_leadC.json',encoding='utf-8'))
codes={}
for r in P['plan']:
    W=frozenset(ti(x) for x in r['W'])
    codes[W]=[tuple(c) for c in r['codes']]
usage=collections.Counter()
for W,cs in codes.items():
    for c in cs: usage[tuple(sorted(c))]+=1
mask2W={}
for r in P['plan']:
    m=0
    for x in r['W']: m|=1<<ti(x)
    mask2W[m]=frozenset(ti(x) for x in r['W'])
G=json.load(open('work/data/out/global.json',encoding='utf-8'))
chiit={int(m): sorted(set(ti(d['z']) for d in lst)) for m,lst in G['chiitoi_descriptors'].items()}
# --- 建单元 ---
t0=time.time(); units={}; tanki=collections.defaultdict(set)
for W,blocks in CLS.items():
    u=set()
    for b in blocks:
        if b[0]=='I':
            c=b[1][0]; inert=tuple(x for x in range(4) if x!=c)
            for (cc,X) in table_lib.block_sources(T,b)[1]:
                V=tuple(lift(cc,X))
                if sum(V)>=4: u.add(V)
                else: tanki[W].add((next(t for t,x in enumerate(V) if x), inert))
        elif b[0]=='II':
            (c1,s1,k1)=b[1]; (c2,s2,k2)=b[2]; am=b[5]
            if sum(am)>=4: u.add(tuple(am))
            else:
                _,xs1=T['PROFII_D'][(c1,s1,k1)]; _,xs2=T['PROFII_D'][(c2,s2,k2)]
                for X1 in xs1:
                    V1=lift(c1,X1)
                    for X2 in xs2:
                        V2=lift(c2,X2); u.add(tuple(V1[i]+V2[i] for i in range(34)))
        else: u.add(tuple(b[1]))
    units[W]=list(u)
print("units %d (%.0fs)" % (sum(len(v) for v in units.values()), time.time()-t0), flush=True)
added=0; missing_n=0
for W in units:
    U=np.array(units[W],dtype=np.int8) if units[W] else np.zeros((0,34),np.int8)
    # 现有码覆盖
    cov=np.zeros(len(units[W]),bool)
    for c in codes.get(W,[]):
        cov |= (U>=np.array(vec4(tuple(sorted(c))),dtype=np.int8)).all(-1)
    if cov.all(): continue
    for i in np.nonzero(~cov)[0]:
        free=[mu for mu in subs4(units[W][i]) if usage[mu]<p4(mu)]
        if not free:
            missing_n+=1; continue
        mu=free[0]; usage[mu]+=1; codes.setdefault(W,[]).append(mu); added+=1
        cov |= (U>=np.array(vec4(mu),dtype=np.int8)).all(-1)
print("patched: added %d codes, unresolved units %d" % (added, missing_n), flush=True)
# --- tanki 族补 ---
tk=0
for W,zs in tanki.items():
    for (z,inert) in zs:
        for cat in inert:
            for M in MELDS_IN_CAT[cat]:
                tal=[t for t,x in enumerate(M) for _ in range(x)]
                mu=tuple(sorted((z,tal[0],tal[1],tal[2])))
                if mu not in set(tuple(sorted(c)) for c in codes.get(W,[])) and usage[mu]<p4(mu):
                    usage[mu]+=1; codes.setdefault(W,[]).append(mu); tk+=1
print("tanki added %d" % tk, flush=True)
# --- chiitoi 补（同 z 多类用不同划分：这里只检查族存在）---
plan=[]; used=collections.Counter()
for W,cs in codes.items():
    out=[]
    for mu in sorted(set(tuple(sorted(c)) for c in cs)):
        ps=sorted(set(itertools.permutations(mu))); k=used[mu]
        if k<len(ps): used[mu]+=1; out.append(list(ps[k]))
    plan.append({"W":[nm(t) for t in sorted(W)],"codes":out})
allc=[tuple(c) for r in plan for c in r["codes"]]
rep={"n_classes":len(plan),"n_codes":len(allc),"distinct":len(set(allc)),
     "empty":sum(1 for r in plan if not r["codes"]),"patched":added,"tanki":tk,"unresolved":missing_n,
     "over_cap":sum(1 for m,n in usage.items() if n>p4(m))}
json.dump({"k":4,"n_classes":len(plan),"n_codes":len(allc),"plan":plan}, open('work/recon/plan_k4_leadD.json','w'))
json.dump(rep, open('work/recon/plan_k4_leadD_report.json','w'), ensure_ascii=False, indent=1)
print(rep)
