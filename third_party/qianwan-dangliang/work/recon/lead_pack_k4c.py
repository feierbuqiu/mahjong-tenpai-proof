# -*- coding: utf-8 -*-
"""lead_pack_k4c.py -- Lead 的 k=4 从零构造 v3（正确的单元模型 + 预留受限族 + 稀缺优先 + 覆盖/余量打分）
单元模型（关键修正）：
  kind I : 每个 X（码 ⊆ X 即可覆盖该 X 的全部补牌手牌）
  kind II: |am1⊎am2| >= 4 -> 单元 = am（一条码覆盖整块）
           否则 -> 按 (X1,X2) 对展开，单元 = X1⊎X2（|单元| >= 4）
  kokushi: 手牌本体
  chiitoi/tanki: 预留族
输出 work/recon/plan_k4_leadC.json
"""
import sys, os, json, collections, math, itertools, random, time, pickle
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
    key=tuple(V)
    r=LC.get(key)
    if r is not None: return r
    tiles=[]
    for t,c in enumerate(V):
        for _ in range(min(c,4)): tiles.append(t)
    out=set(); n=len(tiles)
    for a in range(n):
        for b in range(a,n):
            for c in range(b,n):
                for d in range(c,n): out.add((tiles[a],tiles[b],tiles[c],tiles[d]))
    r=list(out); LC[key]=r
    return r
T=pickle.load(open('work/strategy/out/table_cache.pkl','rb')) if os.path.exists('work/strategy/out/table_cache.pkl') else table_lib.build()
CLS=T['cls']
G=json.load(open('work/data/out/global.json',encoding='utf-8'))
chiit={int(m): sorted(set(ti(d['z']) for d in lst)) for m,lst in G['chiitoi_descriptors'].items()}
t0=time.time()
percls={}; tanki=collections.defaultdict(set)
for W,blocks in CLS.items():
    reqs=set()
    for b in blocks:
        if b[0]=='I':
            c=b[1][0]; inert=tuple(x for x in range(4) if x!=c)
            for (cc,X) in table_lib.block_sources(T,b)[1]:
                V=lift(cc,X)
                if sum(V)>=4: reqs.add(tuple(V))
                else: tanki[W].add((next(t for t,x in enumerate(V) if x), inert))
        elif b[0]=='II':
            (c1,s1,k1)=b[1]; (c2,s2,k2)=b[2]; am=b[5]
            if sum(am)>=4: reqs.add(tuple(am))
            else:
                _,xs1=T['PROFII_D'][(c1,s1,k1)]; _,xs2=T['PROFII_D'][(c2,s2,k2)]
                for X1 in xs1:
                    V1=lift(c1,X1)
                    for X2 in xs2:
                        V2=lift(c2,X2); reqs.add(tuple(V1[i]+V2[i] for i in range(34)))
        else: reqs.add(tuple(b[1]))
    percls[W]=list(reqs)
print("units %d (%.0fs)" % (sum(len(v) for v in percls.values()), time.time()-t0), flush=True)
usage=collections.Counter(); cover={W:[] for W in percls}
def take(mu):
    if usage[mu]<p4(mu): usage[mu]+=1; return True
    return False
# 预留 chiitoi（93 对最小族）与 tanki
z_users=collections.defaultdict(list)
for mask,zs in chiit.items():
    for z in zs: z_users[z].append(mask)
mask2W={}
for r in CLS:
    m2=0
    for t in r: m2|=1<<t
    mask2W[m2]=r
chiit_ok=0; chiit_fail=[]
for z,masks in z_users.items():
    tiles=[t for t in range(34) if t!=z]
    gr=[tiles[0:7],tiles[7:14],tiles[14:21],tiles[21:27],tiles[27:33]]
    fam=[tuple(sorted((z,a,a,b))) for g in gr for a,b in itertools.combinations(g,2)]
    for mask in masks:
        got=[mu for mu in fam if take(mu)]
        W=mask2W.get(mask)
        if W is not None: cover[W].extend(got)
        if len(got)==len(fam): chiit_ok+=1
        else: chiit_fail.append([mask,nm(z),len(fam)-len(got)])
print("chiitoi reserved ok %d fail %d" % (chiit_ok, len(chiit_fail)), flush=True)
for W,zs in tanki.items():
    for (z,inert) in zs:
        for cat in inert:
            for M in MELDS_IN_CAT[cat]:
                tal=[t for t,x in enumerate(M) for _ in range(x)]
                mu=tuple(sorted((z,tal[0],tal[1],tal[2])))
                if take(mu): cover[W].append(mu)
U={W:np.array(percls[W],dtype=np.int8) for W in percls}
cov={W:np.zeros(len(percls[W]),bool) for W in percls}
for W in percls:
    for mu in cover[W]:
        cov[W] |= (U[W]>=np.array(vec4(tuple(sorted(mu))),dtype=np.int8)).all(-1)
tasks=[]
for W in percls:
    for i in range(len(percls[W])): tasks.append((sum(percls[W][i]),W,i))
tasks.sort(key=lambda t:t[0])
print("tasks %d (%.0fs)" % (len(tasks), time.time()-t0), flush=True)
rng=random.Random(11); picks=0; fails=[]; t1=time.time()
for n_,(s,W,i) in enumerate(tasks):
    if cov[W][i]: continue
    cands=subs4(percls[W][i])
    free=[mu for mu in cands if usage[mu]<p4(mu)]
    if not free:
        fails.append((s,[nm(t) for t in sorted(W)],len(cands))); cov[W][i]=True; continue
    if len(free)>400:
        rng.shuffle(free); free=free[:400]
    rem=np.nonzero(~cov[W])[0]; sub=U[W][rem]
    C=np.array([vec4(mu) for mu in free],dtype=np.int8)
    cnt=np.zeros(len(free),dtype=np.int32)
    for st in range(0,len(free),24):
        blk=C[st:st+24]
        cnt[st:st+len(blk)]=(sub[:,None,:]>=blk[None,:,:]).all(-1).sum(0)
    slack=np.array([p4(mu)-usage[mu] for mu in free],dtype=np.int32)
    score=cnt.astype(np.int64)*8+np.minimum(slack,24)
    j=int(score.argmax()); mu=free[j]
    take(mu); cover[W].append(mu); picks+=1
    cov[W] |= (U[W]>=np.array(vec4(mu),dtype=np.int8)).all(-1)
    if n_%400000==0: print("  %d/%d picks=%d fails=%d %.0fs" % (n_,len(tasks),picks,len(fails),time.time()-t1), flush=True)
print("done picks=%d fails=%d (%.0fs total)" % (picks,len(fails),time.time()-t0), flush=True)
# --- 收尾清扫：确保每个单元都被某条已选码覆盖 ---
rest=0; t2=time.time()
for W in percls:
    need=np.nonzero(~cov[W])[0]
    for i in need:
        if cov[W][i]: continue
        cands=subs4(percls[W][i]); free=[mu for mu in cands if usage[mu]<p4(mu)]
        if not free:
            fails.append((sum(percls[W][i]),[nm(t) for t in sorted(W)],len(cands))); rest+=1; cov[W][i]=True; continue
        mu=free[0]; take(mu); cover[W].append(mu); picks+=1
        cov[W] |= (U[W]>=np.array(vec4(mu),dtype=np.int8)).all(-1)
print("sweep: extra picks=%d still_uncovered=%d (%.0fs)" % (picks-6934 if picks>=6934 else picks, rest, time.time()-t2), flush=True)
print("fail by |X|:", collections.Counter(f[0] for f in fails))
print("fail classes:", collections.Counter(tuple(f[1]) for f in fails).most_common(8))
Wt=frozenset([4,7]); tgt=tuple(1 if t in (4,5,6,7) else 0 for t in range(34))
print("DBG tasks",len(tasks),"size4",sum(1 for t in tasks if t[0]==4), flush=True)
if Wt in percls:
    ii=percls[Wt].index(tgt) if tgt in percls[Wt] else -1
    print("DBG ii",ii,"entry",tuple(percls[Wt][ii])==tgt if ii>=0 else None,"in tasks:", any(t[1]==Wt and t[2]==ii for t in tasks), flush=True)
if Wt in percls and tgt in percls[Wt]:
    ii=percls[Wt].index(tgt)
    print("DBG unit cov=",bool(cov[Wt][ii]),"code in cover:",tuple(sorted((4,5,6,7))) in set(tuple(sorted(m)) for m in cover[Wt]),
          "ncodes",len(cover[Wt]),"|X|",sum(percls[Wt][ii]), flush=True)
else:
    print("DBG target unit MISSING from percls:", Wt in percls, flush=True)
plan=[]; used=collections.Counter()
for W in percls:
    codes=[]
    for mu in sorted(set(tuple(sorted(m)) for m in cover[W])):
        ps=sorted(set(itertools.permutations(mu)))
        k=used[mu]
        if k<len(ps):
            used[mu]+=1; codes.append(list(ps[k]))
    plan.append({"W":[nm(t) for t in sorted(W)],"codes":codes})
allc=[tuple(c) for r in plan for c in r["codes"]]
rep={"n_classes":len(plan),"n_codes":len(allc),"distinct":len(set(allc)),
     "empty":sum(1 for r in plan if not r["codes"]),"fails":len(fails),
     "chiit_ok":chiit_ok,"chiit_fail":len(chiit_fail),"over_cap":sum(1 for m,n in usage.items() if n>p4(m))}
json.dump({"k":4,"n_classes":len(plan),"n_codes":len(allc),"plan":plan}, open('work/recon/plan_k4_leadC.json','w'))
json.dump({"report":rep,"fails":fails[:200],"chiit_fail":chiit_fail[:50]}, open('work/recon/plan_k4_leadC_report.json','w'), ensure_ascii=False, indent=1)
print(rep)
