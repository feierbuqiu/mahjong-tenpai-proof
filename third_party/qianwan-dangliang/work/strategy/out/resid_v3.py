# -*- coding: utf-8 -*-
"""resid_v3.py -- 复现 plan_k4_v2.json 的残余: TypeI 未覆盖块 / chiitoi 缺失对 / II / kokushi"""
import sys, os, json, itertools, math, collections, time
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "work/strategy")
from mjlib import *
import table_lib as TL
K = 4
T0 = time.time()
def log(*a): print("[%7.1fs]" % (time.time()-T0), *a, flush=True)
HONN = ["E","S","W","N","Haku","Hatsu","Chun"]; HON = {n:27+i for i,n in enumerate(HONN)}
def nm(t): return ("%d%s" % (t%9+1, "mps"[t//9])) if t < 27 else HONN[t-27]
def to_idx(w):
    o=[]
    for x in w:
        if isinstance(x,int): o.append(x)
        elif x in HON: o.append(HON[x])
        else: o.append("mps".index(x[-1])*9+int(x[0])-1)
    return o
SU = {"m":0,"p":1,"s":2,"z":3}

P = json.load(open("work/strategy/out/plan_k4_v2.json", encoding="utf-8"))
cls = {}; used = collections.defaultdict(list)
for r in P["plan"]:
    W = frozenset(to_idx(r["W"])); cls[W] = [tuple(c) for c in r["codes"]]
    for c in cls[W]: used[tuple(sorted(c))].append((W, tuple(c)))
log("载入 %d 类 %d 码 (%d 不同多重集)" % (len(cls), sum(len(v) for v in cls.values()), len(used)))
def p4(mu):
    c = collections.Counter(mu); return 24 // math.prod(math.factorial(v) for v in c.values())
over = [(mu,len(l)) for mu,l in used.items() if len(l) > p4(mu)]
dups = sum(len(l) for l in used.values()) - len(used) - sum(0 for _ in [])
allc = [c for v in cls.values() for c in v]
log("有序码总数 %d, 不同 %d, 超容量多重集 %d, 空类 %d" % (len(allc), len(set(allc)), len(over), sum(1 for v in cls.values() if not v)))
def contains(h,c):
    need={}
    for t in c: need[t]=need.get(t,0)+1
    return all(h[t]>=v for t,v in need.items())
def parse(ds,ci):
    off=(0,9,18,27)[ci]; u=[0]*34
    for i,ch in enumerate(ds):
        if ch!="0": u[off+i]=int(ch)
    return tuple(u)
G = json.load(open("work/data/out/global.json", encoding="utf-8"))
FAMC={}
def fam(S,m,chi):
    key=(tuple(S),m,chi)
    if key not in FAMC: FAMC[key]=TL.fam_list(S,m,chi)
    return FAMC[key]
def block_covered(A, inert, m, codes):
    if any(contains(A,c) for c in codes): return True
    S=tuple(SU[x] for x in inert)
    fl=list(fam(S,m,False))+list(fam(S,m,True))
    if not fl: return False
    for F in fl:
        hand=tuple(A[i]+F[i] for i in range(34))
        if not any(contains(hand,c) for c in codes): return False
    return True
# ---- Type I / II / kokushi ----
cnt = collections.Counter(); unc = collections.Counter(); bad = collections.defaultdict(list)
for row in G["classes"]:
    W = frozenset(to_idx(row["W"]))
    if W not in cls: continue
    codes = cls[W]
    for s in row.get("sources", []):
        kd = s["kind"]; cnt[kd]+=1
        if kd == "I":
            ci=SU[s["cat"]]; A=parse(s["A"],ci); m=13-sum(A)
            if not block_covered(A,s["inert"],m,codes):
                unc["I"]+=1
                if len(bad["I"])<6: bad["I"].append({"W":row["W"],"A":s["A"],"cat":s["cat"],"m":m})
        elif kd == "II":
            # 判据: 存在码 ⊆ am (s 里可能有 am 字段?) 先看字段
            if "am" in s:
                am=tuple(s["am"])
                if not any(contains(am,c) for c in codes): unc["II"]+=1
            else:
                unc["II_unknown"]+=1
        elif kd == "kokushi":
            H=parse_hand = None
            if "hand" in s:
                H=tuple(s["hand"])
                if not any(contains(H,c) for c in codes): unc["KOK"]+=1
            else:
                unc["KOK_unknown"]+=1
log("来源块统计: %s" % dict(cnt))
log("未覆盖: %s" % dict(unc))
for b in bad["I"]: log("   TypeI 例: %s" % b)
log("global.json source 字段样例: %s" % json.dumps(G["classes"][0]["sources"][0], ensure_ascii=False)[:500])
# ---- chiitoi ----
chiit = {int(k): [to_idx([d["z"]])[0] for d in v] for k,v in G["chiitoi_descriptors"].items()}
nz_pairs=0; miss=0; miss_list=[]
for mask, zs in sorted(chiit.items()):
    W = frozenset(t for t in range(34) if (mask>>t)&1)
    if W not in cls: continue
    mset = collections.Counter(tuple(sorted(c)) for c in cls[W])
    for z in zs:
        tiles=[t for t in range(34) if t!=z]
        gr=[tiles[0:7],tiles[7:14],tiles[14:21],tiles[21:27],tiles[27:33]]
        for g in gr:
            for a,b in itertools.combinations(g,2):
                mu=tuple(sorted((z,a,a,b))); nz_pairs+=1
                if mset[mu]==0:
                    miss+=1
                    if len(miss_list)<8: miss_list.append((sorted(W),nm(z),nm(a),nm(b)))
log("chiitoi: (W,z) 数 = %d, 规范划分对总数 = %d, 缺失 = %d" % (sum(len(v) for v in chiit.values()), nz_pairs, miss))
for m_ in miss_list: log("   缺 %s" % (m_,))
