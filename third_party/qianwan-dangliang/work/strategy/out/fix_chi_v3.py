# -*- coding: utf-8 -*-
"""fix_chi_v3.py -- 只修 chiitoi 族 (轻量: 不加载 table_lib)
对每个 (类 W, z): 随机抽样 5 组划分(7,7,7,6,6) 的 33 张非 z 牌, 选缺失最少的划分,
把 93 对 (a,b) 的码 mu=(z,a,a,b) 各取一条未用排列装入 W。
输出 out/plan_k4_v3.json + out/fix_chi_v3_report.json
"""
import sys, os, json, itertools, math, collections, time, random
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
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
rng = random.Random(20240613)
P = json.load(open(os.path.join(HERE,"plan_k4_v2.json"), encoding="utf-8"))
cls = {}; used = collections.defaultdict(list); mset = {}
for r in P["plan"]:
    W = frozenset(to_idx(r["W"])); cs = [tuple(c) for c in r["codes"]]
    cls[W] = cs; mset[W] = collections.Counter(tuple(sorted(c)) for c in cs)
    for c in cs: used[tuple(sorted(c))].append((W, c))
log("载入: %d 类 %d 码" % (len(cls), sum(len(v) for v in cls.values())))
PERM = {}
def perms(mu):
    if mu not in PERM: PERM[mu] = sorted(set(itertools.permutations(mu)))
    return PERM[mu]
def p4(mu):
    c = collections.Counter(mu); return 24 // math.prod(math.factorial(v) for v in c.values())
def try_take(mu, W):
    lst = used[mu]
    if len(lst) >= p4(mu): return None
    taken = set(c for _, c in lst)
    for p in perms(mu):
        if p not in taken:
            lst.append((W, p)); cls[W].append(p); mset[W][mu] += 1; return p
    return None
def has_indep6(W, z):
    adj = set()
    for mu, n in mset[W].items():
        if n > 0 and len(mu) == 4 and mu.count(z) == 1:
            rest = [t for t in mu if t != z]
            if len(set(rest)) == 2 and rest[0] == rest[1]:
                a = rest[0]; b = [t for t in rest if t != a]
    # 用 (z,a,a,b) 的集合构建图
    adj = [[False]*34 for _ in range(34)]
    for mu in mset[W]:
        if mset[W][mu] <= 0: continue
        if mu.count(z) != 1: continue
        rest = [t for t in mu if t != z]
        if len(rest) == 3:
            c = collections.Counter(rest)
            two = [t for t, k in c.items() if k == 2]
            one = [t for t, k in c.items() if k == 1]
            if len(two) == 1 and len(one) == 1:
                a = two[0]; b = one[0]
                adj[a][b] = adj[b][a] = True
    verts = [t for t in range(34) if t != z]
    def rec(cands, need):
        if need == 0: return True
        for i, v in enumerate(cands):
            if len(cands) - i < need: return False
            nxt = [u for u in cands[i+1:] if not adj[v][u]]
            if rec(nxt, need-1): return True
        return False
    return rec(verts, 6)
G = json.load(open("work/data/out/global.json", encoding="utf-8"))
chiit = {int(k): [to_idx([d["z"]])[0] for d in v] for k, v in G["chiitoi_descriptors"].items()}
wz_list = []
for mask, zs in sorted(chiit.items()):
    W = frozenset(t for t in range(34) if (mask >> t) & 1)
    if W not in cls: continue
    for z in zs: wz_list.append((W, z))
log("(W,z) 对总数 = %d, 其中当前 α>=6 的 = %d" % (len(wz_list), sum(1 for W,z in wz_list if has_indep6(W,z))))
fixed = 0; failed = []; canon_missing_before = 0; canon_missing_after = 0; installed_codes = 0
for (W, z) in wz_list:
    tiles = [t for t in range(34) if t != z]
    # 规范划分的缺口(与 designer 口径一致, 仅用于对照)
    gr = [tiles[0:7], tiles[7:14], tiles[14:21], tiles[21:27], tiles[27:33]]
    canon_missing_before += sum(1 for g in gr for a, b in itertools.combinations(g, 2)
                                if mset[W][tuple(sorted((z, a, a, b)))] == 0)
    if not has_indep6(W, z):
        continue
    best = None
    for attempt in range(600):
        ts = tiles[:]; rng.shuffle(ts)
        groups = [ts[0:7], ts[7:14], ts[14:21], ts[21:27], ts[27:33]]
        missing = []
        for g in groups:
            for a, b in itertools.combinations(g, 2):
                mu = tuple(sorted((z, a, a, b)))
                if mset[W][mu] > 0: continue
                if len(used[mu]) >= p4(mu): missing.append((a, b))
        if not missing:
            best = (groups, []); break
        if best is None or len(missing) < len(best[1]): best = (groups, missing)
    groups, missing = best
    got = 0; miss2 = []
    for g in groups:
        for a, b in itertools.combinations(g, 2):
            mu = tuple(sorted((z, a, a, b)))
            if mset[W][mu] > 0: got += 1; continue
            p = try_take(mu, W)
            if p: got += 1; installed_codes += 1
            else: miss2.append((nm(a), nm(b)))
    if miss2: failed.append({"W": [nm(t) for t in sorted(W)], "z": nm(z), "missing_pairs": len(miss2), "sample": miss2[:5]})
    else: fixed += 1
log("chiitoi: 修好 %d 个 (W,z), 失败 %d; 新增码 %d" % (fixed, len(failed), installed_codes))
after = [{"W": [nm(t) for t in sorted(W)], "z": nm(z)} for W, z in wz_list if has_indep6(W, z)]
canon_missing_after = sum(1 for (W, z) in wz_list for g in [ [t for t in range(34) if t != z][0:7], [t for t in range(34) if t != z][7:14],
                        [t for t in range(34) if t != z][14:21], [t for t in range(34) if t != z][21:27], [t for t in range(34) if t != z][27:33] ]
                        for a, b in itertools.combinations(g, 2) if mset[W][tuple(sorted((z, a, a, b)))] == 0)
allc = [c for v in cls.values() for c in v]
log("落盘校验: 类 %d, 码 %d, 不同 %d, 空类 %d" % (len(cls), len(allc), len(set(allc)), sum(1 for v in cls.values() if not v)))
log("chiitoi 残余 α>=6 的 (W,z) = %d ; 规范划分缺口 %d -> %d" % (len(after), canon_missing_before, canon_missing_after))
json.dump({"k": 4, "n_classes": len(cls), "n_codes": len(set(allc)),
           "plan": [{"W": sorted(W), "codes": [list(c) for c in cls[W]]} for W in sorted(cls, key=lambda S: sorted(S))]},
          open(os.path.join(HERE, "plan_k4_v3.json"), "w", encoding="utf-8"), ensure_ascii=False)
json.dump({"base": "plan_k4_v2.json", "stage": "chiitoi-only", "n_classes": len(cls), "n_codes": len(set(allc)),
           "chiitoi_Wz_total": len(wz_list), "chiitoi_Wz_fixed": fixed, "chiitoi_Wz_failed": len(failed),
           "chiitoi_residual_alpha6": len(after), "chiitoi_canon_missing_before": canon_missing_before,
           "chiitoi_canon_missing_after": canon_missing_after, "codes_added": installed_codes,
           "typeI_untouched_expected": 47, "failed": failed[:40], "residual": after[:40],
           "time_s": round(time.time()-T0, 1)},
          open(os.path.join(HERE, "fix_chi_v3_report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
log("写出 plan_k4_v3.json + fix_chi_v3_report.json")
