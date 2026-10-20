# -*- coding: utf-8 -*-
"""chiit_fix.py -- 用『自由码贪心组族』修 chiitoi (lead 算法).
对每个 (类,z): 顶点=33 张非 z 牌; 边={a,b} 若 (z,a,a,b) 或 (a,a,b,b) 仍可安装(有空闲排列).
循环: 找独立 6 集 K6 -> 用 (z,a,b,c)/(a,a,b,c) 三元码覆盖之(补该三元的子对边) -> 重复到无 K6.
最后逐条码分配未用排列, 追加进该类 codes.
输入 work/verify/plan_k4_final.json(只读) -> 输出 out/plan_k4_v3.json + out/chiit_fix_report.json
"""
import sys, os, json, itertools, math, collections, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjlib import *
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out")
T0 = time.time()
def log(*a): print("[%7.1fs]" % (time.time()-T0), *a, flush=True)
HONN = ["E","S","W","N","Haku","Hatsu","Chun"]; HON = {n:27+i for i,n in enumerate(HONN)}
def to_idx(w):
    o = []
    for x in w:
        if isinstance(x, int): o.append(x)
        elif x in HON: o.append(HON[x])
        else: o.append("mps".index(x[-1])*9 + int(x[0]) - 1)
    return o
def nm(t): return ("%d%s" % (t%9+1, "mps"[t//9])) if t < 27 else HONN[t-27]
def pl(mu): return sorted(set(itertools.permutations(mu)))
def p4(mu):
    c = collections.Counter(mu); return 24 // math.prod(math.factorial(v) for v in c.values())
P = json.load(open(os.path.join(ROOT, "verify", "plan_k4_final.json"), encoding="utf-8"))
rows = P["plan"] if isinstance(P, dict) and "plan" in P else P
plancls = {frozenset(to_idx(r["W"])): [tuple(c) for c in r["codes"]] for r in rows}
used = collections.defaultdict(list)
for W, cs in plancls.items():
    for c in cs: used[tuple(sorted(c))].append((W, c))
log("基线 %d 类 %d 码" % (len(plancls), sum(len(v) for v in plancls.values())))
def take(mu, W):
    lst = used[mu]
    if len(lst) >= p4(mu): return None
    t = {c for _, c in lst}
    for p in pl(mu):
        if p not in t: lst.append((W, p)); return p
    return None
def max_indep6(adj, tiles):
    """找大小 6 的独立集(回溯)"""
    best = None
    def rec(cand, chosen):
        nonlocal best
        if best is not None: return
        if len(chosen) == 6: best = list(chosen); return
        if len(chosen) + len(cand) < 6: return
        cl = list(cand)
        for i, v in enumerate(cl):
            if best is not None: return
            rec([u for u in cl[i+1:] if u not in adj[v]], chosen + [v])
    rec(list(tiles), [])
    return best

G = json.load(open(os.path.join(ROOT, "data", "out", "global.json"), encoding="utf-8"))
chiit = {int(k): [to_idx([d["z"]])[0] for d in v] for k, v in G["chiitoi_descriptors"].items()}
ok_n = 0; res_n = 0; add_codes = 0; residues = []
for mask, zs in sorted(chiit.items()):
    W = frozenset(t for t in range(34) if (mask >> t) & 1)
    if W not in plancls: continue
    for z in zs:
        tiles = [t for t in range(34) if t != z]
        own = {tuple(sorted(c)) for c in plancls[W]}
        # 图: 边 = 存在可安装的二元码
        adj = {t: set() for t in tiles}
        pair_mu = {}
        for a, b in itertools.combinations(tiles, 2):
            for mu in (tuple(sorted((z, a, a, b))), tuple(sorted((a, a, b, b)))):
                if len(used[mu]) < p4(mu):
                    adj[a].add(b); adj[b].add(a); pair_mu[(a, b)] = mu; break
        added = []
        guard = 0
        while guard < 60:
            guard += 1
            K6 = max_indep6(adj, tiles)
            if K6 is None: break
            found = None
            for tri in itertools.combinations(K6, 3):
                for mu in (tuple(sorted((z,)+tri)), tuple(sorted((tri[0], tri[0], tri[1], tri[2])))):
                    if len(used[mu]) < p4(mu): found = mu; break
                if found: break
            if found is None: break
            p = take(found, W)
            if p is None: break
            plancls[W].append(p); added.append(found)
            for x, y in itertools.combinations(sorted(found) if False else sorted(set(found)), 2):
                pass
            a, b, c = sorted(tri)
            for x, y in ((a, b), (a, c), (b, c)):
                adj[x].add(y); adj[y].add(x)
            pair_mu.pop((a, b), None)
        # 安装所有可安装对
        for (a, b), mu in list(pair_mu.items()):
            if mu in own or any(tuple(sorted(x)) == mu for x in plancls[W]): continue
            p = take(mu, W)
            if p: plancls[W].append(p); added.append(mu)
        add_codes += len(added)
        if max_indep6(adj, tiles) is None: ok_n += 1
        else:
            res_n += 1
            if len(residues) < 20: residues.append({"W": sorted(W), "z": nm(z), "added": len(added)})
log("chiitoi: (类,z) 完成 %d, 残余 %d, 新增码 %d" % (ok_n, res_n, add_codes))
allc = [c for cs in plancls.values() for c in cs]
empty = [sorted(W) for W in plancls if not plancls[W]]
over = [mu for mu, lst in used.items() if len(lst) > p4(mu)]
log("校验: 类 %d 码 %d 不同 %d 空类 %d 超容量 %d" % (len(plancls), len(allc), len(set(allc)), len(empty), len(over)))
json.dump({"k": 4, "n_classes": len(plancls), "n_codes": len(set(allc)),
           "plan": [{"W": sorted(W), "codes": [list(c) for c in plancls[W]]} for W in sorted(plancls, key=lambda S: sorted(S))]},
          open(os.path.join(OUT, "plan_k4_v3.json"), "w", encoding="utf-8"), ensure_ascii=False)
json.dump({"n_classes": len(plancls), "n_codes": len(set(allc)), "n_empty": len(empty),
           "over_capacity": len(over), "chi_ok": ok_n, "chi_residual": res_n, "chi_added_codes": add_codes,
           "residues": residues}, open(os.path.join(OUT, "chiit_fix_report.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
log("写出 out/plan_k4_v3.json + out/chiit_fix_report.json")
