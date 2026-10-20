# -*- coding: utf-8 -*-
"""chiit_fix2.py -- chiitoi 修复 v2(lead 修正版): 最小二元族(~93 条, Turán 5 组) + 少量三元修补.
对每个 (类,z) 串行:
  1) 随机搜索数百个 5 组划分, 取"93 条组内对中可安装条数最多"者, 装入其可安装对;
  2) 反复求"未被已装对/三元覆盖"的独立 6 集 K6, 对 K6 装一条可安装三元码(优先覆盖最多未覆盖 6 集);
  3) 找不到可安装三元 -> 记录 K6 的 6 张牌与 20 个三元在各形状下的 usage/p4(残余).
输入 work/verify/plan_k4_final.json(只读) -> 输出 out/plan_k4_v4.json + out/chiit_fix2_report.json
"""
import sys, os, json, random, itertools, math, collections, time
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
def free(mu): return len(used[mu]) < p4(mu)
def take(mu, W):
    lst = used[mu]
    if len(lst) >= p4(mu): return None
    t = {c for _, c in lst}
    for p in pl(mu):
        if p not in t: lst.append((W, p)); return p
    return None

def parts5(tiles, rng):
    """随机 5 组划分: 组大小 7,7,7,6,6"""
    t = list(tiles); rng.shuffle(t)
    return [t[0:7], t[7:14], t[14:21], t[21:27], t[27:33]]

def find_uncovered6(tiles, pairs, triples):
    """找 6 集 K: 不含任何 pairs 中的对, 也不含任何 triples 中的三元"""
    adj = {t: set() for t in tiles}
    for (a, b) in pairs:
        adj[a].add(b); adj[b].add(a)
    order = sorted(tiles, key=lambda t: -len(adj[t]))
    res = [None]
    def rec(idx, chosen):
        if res[0] is not None: return
        if len(chosen) == 6:
            s = set(chosen)
            for tr in triples:
                if tr <= s: return
            res[0] = list(chosen); return
        if len(chosen) + (len(order) - idx) < 6: return
        for i in range(idx, len(order)):
            v = order[i]
            if any(u in adj[v] for u in chosen): continue
            rec(i+1, chosen + [v])
            if res[0] is not None: return
    rec(0, [])
    return res[0]

rng = random.Random(20240607)
G = json.load(open(os.path.join(ROOT, "data", "out", "global.json"), encoding="utf-8"))
chiit = {int(k): [to_idx([d["z"]])[0] for d in v] for k, v in G["chiitoi_descriptors"].items()}
ok_n = 0; res_n = 0; add_codes = 0; n_tri = 0; residues = []
for mask, zs in sorted(chiit.items()):
    W = frozenset(t for t in range(34) if (mask >> t) & 1)
    if W not in plancls: continue
    for z in zs:
        tiles = [t for t in range(34) if t != z]
        best = None; bestc = -1
        for _ in range(200):
            grps = parts5(tiles, rng)
            cnt = 0; inst = []
            for g in grps:
                for a, b in itertools.combinations(sorted(g), 2):
                    mu = tuple(sorted((z, a, a, b)))
                    if free(mu): cnt += 1; inst.append((a, b, mu))
            if cnt > bestc: bestc = cnt; best = inst
        pairs = set(); added = 0
        for (a, b, mu) in best:
            p = take(mu, W)
            if p: plancls[W].append(p); pairs.add(frozenset((a, b))); added += 1
        triples = []
        guard = 0
        while guard < 400:
            guard += 1
            K6 = find_uncovered6(tiles, [(min(p), max(p)) for p in pairs], triples)
            if K6 is None: break
            cand = []
            for tri in itertools.combinations(sorted(K6), 3):
                for mu in (tuple(sorted((z,)+tri)), tuple(sorted((tri[0], tri[0], tri[1], tri[2])))):
                    if free(mu): cand.append((mu, tri)); break
            if not cand: break
            cand.sort(key=lambda x: -sum(1 for t in x[1]))
            mu, tri = cand[0]
            p = take(mu, W)
            if p is None: break
            plancls[W].append(p); triples.append(frozenset(tri)); added += 1; n_tri += 1
        add_codes += added
        if find_uncovered6(tiles, [(min(p), max(p)) for p in pairs], triples) is None: ok_n += 1
        else:
            res_n += 1
            if len(residues) < 15:
                K6 = find_uncovered6(tiles, [(min(p), max(p)) for p in pairs], triples)
                detail = []
                for tri in itertools.combinations(sorted(K6), 3):
                    row = {"tri": [nm(t) for t in tri]}
                    for sh, mu in (("zabc", tuple(sorted((z,)+tri))), ("aabc", tuple(sorted((tri[0], tri[0], tri[1], tri[2]))))):
                        row[sh] = {"mu": [nm(t) for t in mu], "usage": len(used[mu]), "p4": p4(mu)}
                    detail.append(row)
                residues.append({"W": sorted(W), "z": nm(z), "K6": [nm(t) for t in K6], "triples": detail})
log("chiitoi v2: 完成 %d, 残余 %d, 新增码 %d (其中三元修补 %d)" % (ok_n, res_n, add_codes, n_tri))
allc = [c for cs in plancls.values() for c in cs]
empty = [sorted(W) for W in plancls if not plancls[W]]
over = [mu for mu, lst in used.items() if len(lst) > p4(mu)]
log("校验: 类 %d 码 %d 不同 %d 空类 %d 超容量 %d" % (len(plancls), len(allc), len(set(allc)), len(empty), len(over)))
json.dump({"k": 4, "n_classes": len(plancls), "n_codes": len(set(allc)),
           "plan": [{"W": sorted(W), "codes": [list(c) for c in plancls[W]]} for W in sorted(plancls, key=lambda S: sorted(S))]},
          open(os.path.join(OUT, "plan_k4_v4.json"), "w", encoding="utf-8"), ensure_ascii=False)
json.dump({"n_classes": len(plancls), "n_codes": len(set(allc)), "n_empty": len(empty), "over_capacity": len(over),
           "chi_ok": ok_n, "chi_residual": res_n, "chi_added_codes": add_codes, "chi_triples": n_tri,
           "residues": residues}, open(os.path.join(OUT, "chiit_fix2_report.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
log("写出 out/plan_k4_v4.json + out/chiit_fix2_report.json")
