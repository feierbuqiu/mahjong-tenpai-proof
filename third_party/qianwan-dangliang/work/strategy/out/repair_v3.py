# -*- coding: utf-8 -*-
"""repair_v3.py -- 把 plan_k4_v2.json 修到零残余 (T 后续任务)
修法一: chiitoi 每个 (W,z) 重新选 5 组划分 (7,7,7,6,6), 使 93 对的码全部可安装;
        饱和时用链式换码 (深度<=3)。
修法二: Type I 残余块用链式换码 (深度<=3, 访问集合防环)。
输出: out/plan_k4_v3.json + out/repair_v3_report.json
用法: python -u work/strategy/out/repair_v3.py [--time-budget 秒]
"""
import sys, os, json, itertools, math, collections, time, random
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "work/strategy")
from mjlib import *
import table_lib as TL
K = 4
T0 = time.time()
BUDGET = 1800
for i, a in enumerate(sys.argv):
    if a == "--time-budget": BUDGET = int(sys.argv[i+1])
def log(*a): print("[%7.1fs]" % (time.time()-T0), *a, flush=True)
def out_of_time(): return (time.time()-T0) > BUDGET
HERE = os.path.dirname(os.path.abspath(__file__))
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
rng = random.Random(20240613)

# ---------------- 载入 ----------------
P = json.load(open(os.path.join(HERE,"plan_k4_v2.json"), encoding="utf-8"))
cls = {}; used = collections.defaultdict(list); mset = {}
for r in P["plan"]:
    W = frozenset(to_idx(r["W"])); cs = [tuple(c) for c in r["codes"]]
    cls[W] = cs; mset[W] = collections.Counter(tuple(sorted(c)) for c in cs)
    for c in cs: used[tuple(sorted(c))].append((W, c))
log("载入 plan_k4_v2: %d 类, %d 码" % (len(cls), sum(len(v) for v in cls.values())))
PERM = {}
def perms(mu):
    if mu not in PERM: PERM[mu] = sorted(set(itertools.permutations(mu)))
    return PERM[mu]
def p4(mu):
    c = collections.Counter(mu); return 24 // math.prod(math.factorial(v) for v in c.values())
def contains(h,c):
    need={}
    for t in c: need[t]=need.get(t,0)+1
    return all(h[t]>=v for t,v in need.items())
def take(mu, W):
    lst = used[mu]
    if len(lst) >= p4(mu): return None
    taken = set(c for _,c in lst)
    for p in perms(mu):
        if p not in taken:
            lst.append((W,p)); cls[W].append(p); mset[W][mu]+=1
            return p
    return None
def drop(mu, W, c):
    used[mu].remove((W,c)); cls[W].remove(c)
    mset[W][mu]-=1
    if mset[W][mu] <= 0: del mset[W][mu]
def gen_subs(vec, k=K):
    tiles = [t for t,n in enumerate(vec) for _ in range(min(n,4))]
    s = set()
    for combo in itertools.combinations_with_replacement(tiles, k):
        need = {}
        for x in combo: need[x] = need.get(x,0)+1
        if all(vec[x] >= v for x,v in need.items()): s.add(combo)
    return s

# ---------------- units / am_of (供换码用) ----------------
T = TL.build(); CLS = T["cls"]
UC = {}
def units(W):
    if W in UC: return UC[W]
    reqs = set(); bl = CLS.get(W, [])
    for b in bl:
        if b[0] == "I":
            for (cc, X) in TL.block_sources(T, b)[1]:
                v = [0]*34
                for i,x in enumerate(X): v[CAT_BASE[cc]+i] = x
                if sum(v) >= K: reqs.add(tuple(v))
        elif b[0] == "II":
            am = b[5]
            if sum(am) >= K: reqs.add(tuple(am))
            else:
                for (c1,X1,c2,X2) in TL.block_sources(T, b)[1]:
                    v = [0]*34
                    if b[1][1] >= b[2][1]:
                        for i,x in enumerate(X1): v[CAT_BASE[c1]+i] = x
                    else:
                        for i,x in enumerate(X2): v[CAT_BASE[c2]+i] = x
                    reqs.add(tuple(v))
        else:
            reqs.add(tuple(b[1]))
    UC[W] = list(reqs); return UC[W]
def am_of(W, mu):
    us = [X for X in units(W) if contains(X, mu)]
    if not us: return None
    return tuple(min(u[i] for u in us) for i in range(34))

MOVES = 0
def free_slot(mu, depth, visited):
    """返回可应用的动作序列 [(W2, old_code, nu)]，使 used[mu] 空出一个槽；否则 None"""
    if depth <= 0: return None
    for (W2, c) in list(used[mu]):
        if W2 in visited: continue
        am = am_of(W2, mu)
        if am is None or sum(am) < K: continue
        cands = [x for x in gen_subs(am) if x != mu and mset[W2][x] == 0]
        cands.sort(key=lambda x: len(used[x]))
        for nu in cands[:400]:
            if len(used[nu]) < p4(nu):
                return [(W2, c, nu)]
            sub = free_slot(nu, depth-1, visited | {W2})
            if sub is not None:
                return sub + [(W2, c, nu)]
    return None
def apply_moves(moves):
    global MOVES
    for (W2, old, nu) in moves:
        drop(tuple(sorted(old)), W2, old)
        nc = take(nu, W2)
        if nc is None: return False
        MOVES += 1
    return True

# ---------------- 修法一: chiitoi ----------------
G = json.load(open("work/data/out/global.json", encoding="utf-8"))
chiit = {int(k): [to_idx([d["z"]])[0] for d in v] for k,v in G["chiitoi_descriptors"].items()}
def has_indep6(pairs, z):
    adj = [[False]*34 for _ in range(34)]
    for (a,b) in pairs: adj[a][b] = adj[b][a] = True
    verts = [t for t in range(34) if t != z]
    def rec(cands, need):
        if need == 0: return True
        for i,v in enumerate(cands):
            if len(cands)-i < need: return False
            nxt = [u for u in cands[i+1:] if not adj[v][u]]
            if rec(nxt, need-1): return True
        return False
    return rec(verts, 6)
def avail_pairs(W, z):
    P = set()
    for mu in mset[W]:
        if mu[0] == z and mu[1] == mu[2] and mu[3] != z and len(set(mu)) == 3:
            P.add((mu[1], mu[3]))
    return P
chi_fixed = 0; chi_still = []
for mask, zs in sorted(chiit.items()):
    W = frozenset(t for t in range(34) if (mask>>t)&1)
    if W not in cls: continue
    for z in zs:
        if not has_indep6(avail_pairs(W,z), z): continue
        ok = False
        for attempt in range(80):
            tiles = [t for t in range(34) if t != z]; rng.shuffle(tiles)
            groups = [tiles[0:7], tiles[7:14], tiles[14:21], tiles[21:27], tiles[27:33]]
            pairs = [p for g in groups for p in itertools.combinations(g,2)]
            installed = []; good = True
            for (a,b) in pairs:
                mu = tuple(sorted((z,a,a,b)))
                if mset[W][mu] > 0: continue
                code = take(mu, W)
                if code: installed.append((mu, code)); continue
                mv = free_slot(mu, 3, {W})
                if mv and apply_moves(mv):
                    code = take(mu, W)
                    if code: installed.append((mu, code)); continue
                good = False; break
            if good: ok = True; break
            for (mu, code) in installed: drop(mu, W, code)
        if ok: chi_fixed += 1
        else:
            chi_still.append({"W": sorted(W), "W_nm": [nm(t) for t in sorted(W)], "z": nm(z),
                              "avail_pairs": len(avail_pairs(W,z))})
log("chiitoi: 修好 (W,z) = %d, 仍失败 = %d, 链式换码动作 = %d" % (chi_fixed, len(chi_still), MOVES))

# ---------------- 修法二: Type I ----------------
def parse(ds, ci):
    off=(0,9,18,27)[ci]; u=[0]*34
    for i,ch in enumerate(ds):
        if ch!="0": u[off+i]=int(ch)
    return tuple(u)
FAMC = {}
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
def try_fix_block(W, A):
    cands = sorted(gen_subs(A), key=lambda x: len(used[x]))
    for mu in cands:
        if len(used[mu]) < p4(mu):
            if take(mu, W): return True
    for mu in cands:
        mv = free_slot(mu, 3, {W})
        if mv and apply_moves(mv) and take(mu, W): return True
    return False
typei_tot = 0; typei_unc = []; fixed = 0; touched = set()
log("开始 Type I 全量枚举(可能较慢)…")
for row in G["classes"]:
    W = frozenset(to_idx(row["W"]))
    if W not in cls: continue
    for s in row.get("sources", []):
        if s["kind"] != "I": continue
        typei_tot += 1
        ci=SU[s["cat"]]; A=parse(s["A"],ci); m=13-sum(A)
        if block_covered(A, s["inert"], m, cls[W]): continue
        typei_unc.append({"W": row["W"], "cat": s["cat"], "A": s["A"], "m": m})
        if out_of_time():
            log("!! 时间预算到, 停止枚举"); break
    if out_of_time(): break
log("Type I: 块 %d, 未覆盖 %d" % (typei_tot, len(typei_unc)))
for b in typei_unc:
    W = frozenset(to_idx(b["W"])); ci = SU[b["cat"]]; A = parse(b["A"], ci)
    if try_fix_block(W, A):
        fixed += 1; touched.add(W)
    else:
        log("   仍无法修: %s" % b)
log("Type I: 修好 %d / %d (链式换码动作累计 %d)" % (fixed, len(typei_unc), MOVES))

# ---------------- 落盘 ----------------
allc = [c for v in cls.values() for c in v]
empty = [sorted(W) for W in cls if not cls[W]]
over = [(mu,len(l)) for mu,l in used.items() if len(l) > p4(mu)]
rng_chk = [ (W,zs) for mask,zs in chiit.items() for W in [frozenset(t for t in range(34) if (mask>>t)&1)] for z in zs if W in cls ]
chi_after = []
for (W,z) in rng_chk:
    if has_indep6(avail_pairs(W,z), z): chi_after.append({"W":[nm(t) for t in sorted(W)],"z":nm(z)})
log("落盘校验: 类 %d, 码 %d, 不同 %d, 空类 %d, 超容量 %d" % (len(cls), len(allc), len(set(allc)), len(empty), len(over)))
log("chiitoi 残余 (α>=6 的 (W,z)) = %d ; TypeI 修好 %d/%d" % (len(chi_after), fixed, len(typei_unc)))
json.dump({"k":4, "n_classes":len(cls), "n_codes":len(set(allc)),
           "plan":[{"W":sorted(W), "codes":[list(c) for c in cls[W]]} for W in sorted(cls, key=lambda S: sorted(S))]},
          open(os.path.join(HERE,"plan_k4_v3.json"),"w",encoding="utf-8"), ensure_ascii=False)
json.dump({"base":"plan_k4_v2.json","n_classes":len(cls),"n_codes":len(set(allc)),"n_empty":len(empty),
           "over_capacity":len(over),"max_use":max(len(l) for l in used.values()),
           "movements":MOVES,
           "typeI_total_blocks":typei_tot,"typeI_uncovered_before":len(typei_unc),"typeI_fixed":fixed,
           "typeI_uncovered_after":len(typei_unc)-fixed,
           "chiitoi_Wz_fixed":chi_fixed,"chiitoi_Wz_still":len(chi_still),
           "chiitoi_residual_alpha6_after":len(chi_after),
           "chiitoi_still":chi_still[:40],"chiitoi_after":chi_after[:40],
           "time_s":round(time.time()-T0,1),"completed": not out_of_time()},
          open(os.path.join(HERE,"repair_v3_report.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
log("写出 plan_k4_v3.json + repair_v3_report.json")
