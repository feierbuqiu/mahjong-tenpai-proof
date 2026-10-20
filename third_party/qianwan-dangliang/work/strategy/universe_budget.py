# -*- coding: utf-8 -*-
"""universe_budget.py -- 子宇宙预算检验 (lead 引理): sum_C tau_U(C) <= |Codes(U)|.

U = 单花色 m (9 张, 预算 9^3=729) ; U = 字牌 z (7 张, 预算 7^3=343).
命中集只允许用 U 内的码 => 就是对"全落在 U 内的手牌子族"求最小覆盖(多重要求)。
"""
import sys, os, json, itertools, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjlib import *
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)
T0 = time.time()
def log(*a): print("[%6.1fs]" % (time.time()-T0), *a, flush=True)

def pair_melds(seg):
    L = len(seg)
    for pi in range(L):
        if seg[pi] >= 2:
            d = list(seg); d[pi] -= 2
            if can_melds(tuple(d), len(seg) == 7): return True
    return False

def solve_universe(name, ntypes, base, budget):
    """枚举 U 内所有 13 张手牌 -> W -> 类; 计算每类最小命中集(3-码多重集)."""
    log("== 宇宙 %s: %d 种牌, 预算 %d" % (name, ntypes, budget))
    hands = []
    for combo in itertools.combinations_with_replacement(range(ntypes), 13):
        c = [0]*ntypes
        for x in combo: c[x] += 1
        if max(c) > 4: continue
        hands.append(tuple(c))
    log("  U 内 13 张手牌总数: %d" % len(hands))
    def W_of(c):
        W = set()
        for t in range(ntypes):
            if c[t] < 4:
                d = list(c); d[t] += 1
                if pair_melds(d): W.add(base + t)
        # 七对子(严格口径: 6 个对子 + 1 张单牌)
        ones = [i for i, x in enumerate(c) if x == 1]
        if len(ones) == 1 and sum(1 for x in c if x == 2) == 6: W.add(base + ones[0])
        return frozenset(W)
    cls = {}
    for h in hands:
        cls.setdefault(W_of(h), []).append(h)
    log("  听牌类数(W!=空): %d" % len([W for W in cls if W]))
    cands = [m for m in itertools.combinations_with_replacement(range(ntypes), 3)]
    log("  候选 3-码多重集: %d (有序码 %d)" % (len(cands), ntypes**3))
    # 类 -> 覆盖分析
    stats = {"tau1": 0, "tau2": 0, "tau3": 0, "tau4plus": 0, "sum_tau": 0, "classes": 0}
    detail = []
    taus = []
    for W, hs in sorted(cls.items(), key=lambda kv: -len(kv[1])):
        if not W: continue
        stats["classes"] += 1
        n = len(hs)
        full = (1 << n) - 1
        masks = {}
        for ci, m in enumerate(cands):
            mm = 0
            need = {}
            for x in m: need[x] = need.get(x, 0)+1
            for i, h in enumerate(hs):
                if all(h[x] >= v for x, v in need.items()): mm |= 1 << i
            if mm: masks[m] = mm
        # tau == 1 ?
        core_size = max(len(m) for m, mm in masks.items() if mm == full) if any(mm == full for mm in masks.values()) else 0
        if any(mm == full for mm in masks.values()):
            taus.append(1); stats["tau1"] += 1; continue
        # tau == 2 ?
        two = False
        items = list(masks.items())
        for i in range(len(items)):
            mi, mmi = items[i]
            for j in range(i+1, len(items)):
                if (mmi | items[j][1]) == full:
                    two = True; break
            if two: break
        if two:
            taus.append(2); stats["tau2"] += 1; continue
        # greedy (>=3)
        uncovered = full; chosen = []
        while uncovered:
            best = max(items, key=lambda kv: bin(kv[1] & uncovered).count("1"))
            chosen.append(best[0]); uncovered &= ~best[1]
        t = len(chosen); taus.append(t)
        if t == 3: stats["tau3"] += 1
        else: stats["tau4plus"] += 1
        detail.append({"W": sorted(W), "hands": n, "tau": t})
    stats["sum_tau"] = sum(taus)
    stats["tau_dist"] = {str(k): taus.count(k) for k in sorted(set(taus))}
    stats["budget"] = budget
    stats["feasible_within_budget"] = stats["sum_tau"] <= budget
    log("  类数=%d  tau 分布=%s  SUM_tau=%d  预算=%d  => %s" % (
        stats["classes"], stats["tau_dist"], stats["sum_tau"], budget,
        "OK" if stats["sum_tau"] <= budget else "**超预算: k=3 不可行证据**"))
    if detail[:5]: log("  高 tau 例: %s" % detail[:5])
    return stats, detail

res = {}
res["m"], det_m = solve_universe("m (单花色)", 9, 0, 9**3)
res["z"], det_z = solve_universe("z (字牌)", 7, 27, 7**3)
json.dump({"stats": {k: v[0] for k, v in []} } if False else
          {"m": res["m"], "z": res["z"], "example_high_tau": det_m[:10] + det_z[:10]},
          open(os.path.join(OUT, "universe_budget.json"), "w"), ensure_ascii=False, indent=1)
log("完成")
