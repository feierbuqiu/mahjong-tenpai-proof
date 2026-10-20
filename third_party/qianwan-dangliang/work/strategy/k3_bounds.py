# -*- coding: utf-8 -*-
"""k3_bounds.py -- k=3 的 tau 上下界与子宇宙预算(严谨部分) + 全局贪心上界.

输出 out/k3_bounds.json
- 子宇宙 U ∈ {m,p,s,z}: 穷尽 U 内全部 13 张多重集 -> 类 -> (下界=packing, 上界=贪心覆盖, 公共码)
- 全局: 逐类贪心上界(不带容量约束, 用 strategy 元素机); 下界 >= 1(平凡) + 子宇宙的严谨下界
"""
import sys, os, json, itertools, collections, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjlib import *
import table_lib as TL
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
K = 3
T0 = time.time()
def log(*a): print("[%7.1fs]" % (time.time()-T0), *a, flush=True)

def all_hands_ntypes(ntypes):
    for combo in itertools.combinations_with_replacement(range(ntypes), 13):
        h = [0]*ntypes
        for x in combo: h[x] += 1
        if max(h) <= 4: yield tuple(h)

def universe(name, ntypes, base, budget):
    hands = []
    for h in all_hands_ntypes(ntypes):
        H = [0]*34
        for i in range(ntypes): H[base+i] = h[i]
        W = waits13(tuple(H))
        if W: hands.append((tuple(H), W))
    cls = collections.defaultdict(list)
    for H, W in hands: cls[W].append(H)
    cands = [tuple(sorted((base+a, base+b, base+c)))
             for a in range(ntypes) for b in range(a, ntypes) for c in range(b, ntypes)]
    stat = {"hands": len(hands), "classes": len(cls), "candidates": len(cands),
            "tau_upper_sum": 0, "tau_lower_sum": 0, "common_code_classes": 0,
            "per_class": [], "budget": budget, "ordered_slots": ntypes**3}
    for W, hs in cls.items():
        # 公共码?
        n = len(hs)
        full = (1 << n) - 1
        cov = {}
        for m in cands:
            mask = 0
            for i, H in enumerate(hs):
                if all(H[x] >= m.count(x) for x in set(m)): mask |= 1 << i
            if mask: cov[m] = mask
        if any(v == full for v in cov.values()):
            tu = 1; tl = 1; common = True
        else:
            common = False
            # 上界: 贪心覆盖
            unc = full; ch = 0
            while unc:
                best = max(cov, key=lambda m: bin(cov[m] & unc).count("1"))
                unc &= ~cov[best]; ch += 1
                if ch > 200: break
            tu = ch
            # 下界: packing (两两无公共 3-码 <=> 逐牌最小和 < 3)
            order = sorted(range(n), key=lambda i: sum(1 for m in cands if all(hs[i][x] >= m.count(x) for x in set(m))))
            pack = []
            for i in order:
                ok = True
                for j in pack:
                    inter = sum(min(hs[i][t], hs[j][t]) for t in range(34))
                    if inter >= 3: ok = False; break
                if ok: pack.append(i)
            tl = len(pack)
        stat["tau_upper_sum"] += tu; stat["tau_lower_sum"] += tl
        if common: stat["common_code_classes"] += 1
        stat["per_class"].append({"W": sorted(W), "hands": n, "tau_upper": tu, "tau_lower": tl,
                                  "common": common})
    stat["per_class"].sort(key=lambda d: -d["tau_upper"])
    stat["ok_by_lower"] = stat["tau_lower_sum"] <= budget
    stat["ok_by_upper"] = stat["tau_upper_sum"] <= budget
    log("宇宙 %s: 手牌 %d, 类 %d, 候选 3-码 %d ; Στ 下界 %d / 上界 %d vs 预算 %d (%s)" % (
        name, stat["hands"], stat["classes"], stat["candidates"], stat["tau_lower_sum"],
        stat["tau_upper_sum"], budget, "下界<=预算 OK" if stat["ok_by_lower"] else "**下界>预算: 否证**"))
    return stat

res = {"universes": {}, "global": {}}
res["universes"]["m"] = universe("m", 9, 0, 9**3)
res["universes"]["p"] = universe("p", 9, 9, 9**3)
res["universes"]["s"] = universe("s", 9, 18, 9**3)
res["universes"]["z"] = universe("z", 7, 27, 7**3)

# ---------- 全局: 逐类贪心上界(不带容量约束) ----------
import strategy as SG
T = TL.build()
CLS = T["cls"]
INFO = {}
for W, blocks in CLS.items():
    keys, cands, modes = SG.class_elements(T, W, blocks)
    INFO[W] = (keys, cands)
tot = 0; top = []
for W, (keys, cands) in INFO.items():
    ch, unc = SG.greedy_elems(keys, cands, frozenset())
    if unc: ch = ch + [m for i in unc for m in list(cands[i])[:1]]
    sz = len(ch); tot += sz
    top.append({"W": sorted(W), "tau_upper": sz, "elements": len(keys)})
top.sort(key=lambda d: -d["tau_upper"])
res["global"] = {"classes": len(INFO), "sum_tau_upper": tot, "budget": 34**3,
                 "ok_by_upper": tot <= 34**3, "top20": top[:20],
                 "sum_tau_lower_trivial": len(INFO)}
log("全局: 类 %d, Στ 上界(贪心, 无容量约束) = %d vs 预算 %d ; 平凡下界 %d" % (
    len(INFO), tot, 34**3, len(INFO)))
log("需求最大的 20 个类:")
for d in top[:20]:
    print("   ", [tile_name(t) for t in d["W"]], "τ_upper=", d["tau_upper"], "elements=", d["elements"])
json.dump(res, open(os.path.join(OUT, "k3_bounds.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
log("写出 out/k3_bounds.json")
