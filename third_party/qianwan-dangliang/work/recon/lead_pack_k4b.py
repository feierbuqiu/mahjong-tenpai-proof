# -*- coding: utf-8 -*-
"""lead_pack_k4b.py -- Lead 的 k=4 从零构造（预留受限族 + 全局 |X| 升序 + 覆盖/容量余量打分）
关键改动（相对 lead_pack_k4.py）：打分 = 类内新覆盖*10 + 容量余量(p4-usage)，避免抢光热门码。
输出 work/recon/plan_k4_leadB.json
"""
import sys, os, json, collections, math, itertools, random, time
import numpy as np
sys.path.insert(0, 'work/strategy')
import table_lib
from table_lib import CAT_BASE, MELDS_IN_CAT
HONN = ["E","S","W","N","Haku","Hatsu","Chun"]
def nm(t): return ("%d%s" % (t % 9 + 1, "mps"[t // 9])) if t < 27 else HONN[t - 27]
def ti(s): return 27 + HONN.index(s) if s in HONN else "mps".index(s[-1])*9 + int(s[0]) - 1
def lift(c, X):
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
def subs4(V):
    tiles=[]
    for t,c in enumerate(V):
        for _ in range(min(c,4)): tiles.append(t)
    out=set(); n=len(tiles)
    for a in range(n):
        for b in range(a,n):
            for c in range(b,n):
                for d in range(c,n): out.add((tiles[a],tiles[b],tiles[c],tiles[d]))
    return out
print("build table ...", flush=True); t0=time.time()
T=table_lib.build(); CLS=T['cls']
G=json.load(open('work/data/out/global.json',encoding='utf-8'))
chiit={int(m): sorted(set(ti(d['z']) for d in lst)) for m,lst in G['chiitoi_descriptors'].items()}
percls={}; tanki=collections.defaultdict(set)
for W, blocks in CLS.items():
    reqs=set()
    for b in blocks:
        if b[0]=='I':
            c=b[1][0]; inert=tuple(x for x in range(4) if x!=c)
            for (cc,X) in table_lib.block_sources(T,b)[1]:
                V=lift(cc,X)
                if sum(V)>=4: reqs.add(tuple(V))
                else: tanki[W].add((next(t for t,x in enumerate(V) if x), inert))
        elif b[0]=='II':
            am=b[5]; s1=b[1][1]; s2=b[2][1]
            if sum(am)>=4: reqs.add(tuple(am))
            elif max(s1,s2)>=4:
                for (c1,X1,c2,X2) in table_lib.block_sources(T,b)[1]:
                    reqs.add(tuple(lift(c1,X1) if s1>=s2 else lift(c2,X2)))
            else:
                for (c1,X1,c2,X2) in table_lib.block_sources(T,b)[1]:
                    V1=lift(c1,X1); V2=lift(c2,X2); reqs.add(tuple(V1[i]+V2[i] for i in range(34)))
        else: reqs.add(tuple(b[1]))
    percls[W]=list(reqs)
print("units %d (%.0fs)" % (sum(len(v) for v in percls.values()), time.time()-t0), flush=True)
usage=collections.Counter(); cover={W:[] for W in percls}
def take(mu):
    if usage[mu]<p4(mu): usage[mu]+=1; return True
    return False
# 预留 chiitoi（最小 93 对族）与 tanki
resv=0
z_users=collections.defaultdict(list)
for mask,zs in chiit.items():
    for z in zs: z_users[z].append(mask)
chiit_ok=0; chiit_fail=[]
for z,masks in z_users.items():
    tiles=[t for t in range(34) if t!=z]
    gr=[tiles[0:7],tiles[7:14],tiles[14:21],tiles[21:27],tiles[27:33]]
    fam=[tuple(sorted((z,a,a,b))) for g in gr for a,b in itertools.combinations(g,2)]
    for mask in masks:
        got=[mu for mu in fam if take(mu)]
        coverW=None
        for r in CLS:
            m2=0
            for t in r: m2|=1<<t
            if m2==mask: coverW=r; break
        if coverW is not None: cover[coverW].extend(got)
        if len(got)==len(fam): chiit_ok+=1
        else: chiit_fail.append([mask,nm(z),len(fam)-len(got)])
        resv+=len(got)
for W,zs in tanki.items():
    for (z,inert) in zs:
        fam=set()
        for cat in inert:
            for M in MELDS_IN_CAT[cat]:
                tal=[t for t,x in enumerate(M) for _ in range(x)]
                fam.add(tuple(sorted((z,tal[0],tal[1],tal[2]))))
        for mu in fam:
            if take(mu): cover[W].append(mu); resv+=1
print("reserved %d codes; chiitoi ok %d / fail %d" % (resv, chiit_ok, len(chiit_fail)), flush=True)
# 单元 -> 类 的全局排序（|X| 升序）
U={W:np.array(percls[W],dtype=np.int8) for W in percls}
cov={W:np.zeros(len(percls[W]),bool) for W in percls}
# 先标记已被预留码覆盖的单元
for W in percls:
    for mu in cover[W]:
        cov[W] |= (U[W]>=np.array(vec4(sorted(mu)),dtype=np.int8)).all(-1)
tasks=[]
for W in percls:
    for i,X in enumerate(percls[W]): tasks.append((sum(X),W,i))
tasks.sort(key=lambda t:t[0])
print("tasks %d" % len(tasks), flush=True)
rng=random.Random(7)
picks=0; fails=[]; t0=time.time()
for n_,(s,W,i) in enumerate(tasks):
    if cov[W][i]: continue
    cands=list(subs4(percls[W][i]))
    free=[mu for mu in cands if usage[mu]<p4(mu)]
    if not free:
        fails.append((s,[nm(t) for t in sorted(W)],len(cands))); cov[W][i]=True; continue
    if len(free)>300:
        rng.shuffle(free); free=free[:300]
    rem=np.nonzero(~cov[W])[0]; sub=U[W][rem]
    C=np.array([vec4(mu) for mu in free],dtype=np.int8)
    cnt=np.zeros(len(free),dtype=np.int32)
    for st in range(0,len(free),24):
        blk=C[st:st+24]
        cnt[st:st+len(blk)]=(sub[:,None,:]>=blk[None,:,:]).all(-1).sum(0)
    slack=np.array([p4(mu)-usage[mu] for mu in free],dtype=np.int32)
    score=cnt*10+np.minimum(slack,24)
    j=int(score.argmax()); mu=free[j]
    take(mu); cover[W].append(mu); picks+=1
    cov[W] |= (U[W]>=np.array(vec4(mu),dtype=np.int8)).all(-1)
    if n_%200000==0: print("  %d/%d picks=%d fails=%d %.0fs" % (n_,len(tasks),picks,len(fails),time.time()-t0), flush=True)
print("done picks=%d fails=%d (%.0fs)" % (picks,len(fails),time.time()-t0), flush=True)
print("fail sample:", fails[:10])
plan=[]; used=collections.Counter()
for W in percls:
    codes=[]
    for mu in cover[W]:
        mu=tuple(sorted(mu))
        ps=sorted(set(itertools.permutations(mu)))
        k=used[mu]; used[mu]+=1
        if k>=len(ps): continue
        codes.append(list(ps[k]))
    plan.append({"W":[nm(t) for t in sorted(W)],"codes":codes})
allc=[tuple(c) for r in plan for c in r["codes"]]
rep={"n_classes":len(plan),"n_codes":len(allc),"distinct":len(set(allc)),
     "empty":sum(1 for r in plan if not r["codes"]),"fails":len(fails),
     "chiit_fail":len(chiit_fail),"over_cap":sum(1 for m,n in usage.items() if n>p4(m))}
json.dump({"k":4,"n_classes":len(plan),"n_codes":len(allc),"plan":plan}, open('work/recon/plan_k4_leadB.json','w'))
json.dump({"report":rep,"fails":fails[:200],"chiit_fail":chiit_fail[:50]}, open('work/recon/plan_k4_leadB_report.json','w'), ensure_ascii=False, indent=1)
print(rep)
