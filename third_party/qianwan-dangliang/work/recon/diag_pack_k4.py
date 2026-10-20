# -*- coding: utf-8 -*-
"""diag_pack_k4.py -- 诊断『稀缺优先分配』失败原因（Lead）
构造单元 -> 预留 chiitoi/tanki 族 -> 对每个稀缺单元(|X|<=7)统计候选码与空闲情况，记录失败明细。
"""
import sys, os, json, collections, math, itertools, time
sys.path.insert(0, 'work/strategy')
import table_lib
from table_lib import CAT_BASE, MELDS_IN_CAT
HONN = ["E","S","W","N","Haku","Hatsu","Chun"]
def nm(t): return ("%d%s" % (t % 9 + 1, "mps"[t // 9])) if t < 27 else HONN[t - 27]
def ti(s): return 27 + HONN.index(s) if s in HONN else "mps".index(s[-1])*9 + int(s[0]) - 1
def lift(c, X):
    v = [0]*34
    for i, x in enumerate(X): v[CAT_BASE[c]+i] = x
    return v
FACT=[math.factorial(i) for i in range(5)]
def p4(mu):
    c=collections.Counter(mu); return 24//math.prod(FACT[v] for v in c.values())
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
T=table_lib.build(); CLS=T['cls']
G=json.load(open('work/data/out/global.json',encoding='utf-8'))
chiit={int(m): sorted(set(ti(d['z']) for d in lst)) for m,lst in G['chiitoi_descriptors'].items()}
# --- 单元 ---
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
# --- 预留 ---
usage=collections.Counter(); owner={}   # mu -> list of (kind, class)
def take(mu, who):
    if usage[mu] < p4(mu):
        usage[mu]+=1; owner.setdefault(mu,[]).append(who); return True
    return False
z_users=collections.defaultdict(list)
for mask,zs in chiit.items():
    for z in zs: z_users[z].append(mask)
resv_chi=0
for z, masks in z_users.items():
    tiles=[t for t in range(34) if t!=z]
    gr=[tiles[0:7],tiles[7:14],tiles[14:21],tiles[21:27],tiles[27:33]]
    fam=[tuple(sorted((z,a,a,b))) for g in gr for a,b in itertools.combinations(g,2)]
    for mask in masks:
        for mu in fam:
            if take(mu,('chiit',mask,z)): resv_chi+=1
resv_tanki=0
for W,zs in tanki.items():
    for (z,inert) in zs:
        for cat in inert:
            for M in MELDS_IN_CAT[cat]:
                tal=[t for t,x in enumerate(M) for _ in range(x)]
                mu=tuple(sorted((z,tal[0],tal[1],tal[2])))
                if take(mu,('tanki',W,z)): resv_tanki+=1
print("reserved chiit=%d tanki=%d multisets_used=%d" % (resv_chi,resv_tanki,len(usage)), flush=True)
# --- 稀缺单元诊断 ---
scarce=[]
for W, keys in percls.items():
    for i,X in enumerate(keys):
        if sum(X)<=7: scarce.append((sum(X),W,i))
scarce.sort(key=lambda z:z[0])
fail=[]; stats=collections.Counter()
t0=time.time()
for (s,W,i) in scarce:
    cands=list(subs4(percls[W][i]))
    free=[mu for mu in cands if usage[mu]<p4(mu)]
    stats[('ok' if free else 'fail', s)] += 1
    if not free:
        blk=collections.Counter()
        for mu in cands:
            for (k,who,z) in owner.get(mu,[]): blk[k]+=1
        fail.append({"W":[nm(t) for t in sorted(W)],"|X|":s,"ncand":len(cands),"blockers":dict(blk),"X":[nm(t) for t in percls[W][i] for _ in range(1)][:0] or [nm(t) for t in sorted(W)]})
print("scarce units=%d  fail=%d  (%.0fs)" % (len(scarce), len(fail), time.time()-t0))
print("per-(result,|X|):", sorted(stats.items()))
print("fail per |X|:", collections.Counter(f["|X|"] for f in fail))
print("fail classes top:", collections.Counter(tuple(f["W"]) for f in fail).most_common(8))
json.dump(fail[:500], open('work/recon/diag_pack_fail.json','w'), ensure_ascii=False, indent=1)
