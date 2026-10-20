#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T6a: 独立重放 T3 证书 work/lowerbound/certificate.json 并尝试证伪."""
import json, sys, time
from collections import defaultdict
sys.path.insert(0, "work/verify")
from indep_core import compute_W, gen_vectors

cert = json.load(open("work/lowerbound/certificate.json", encoding="utf-8"))
report = {"structural": [], "per_k": {}}

# ---- 1. 结构数字 ----
mine_flows = 0
for h in gen_vectors(9, 13): mine_flows += 1
report["structural"].append(("L5 flush enumeration = 93600",
    mine_flows == cert["L5_flush_enumeration"]["direct"] == 93600))
report["structural"].append(("crosscheck win = 13259 (my standard-only 14-tile wins)",
    cert["crosscheck_win"]["pathA_all_14_vectors"] == 13259))
report["structural"].append(("flush census 40196/387",
    cert["flush_census"]["tenpai_hands_full_W"] == 40196 and cert["flush_census"]["classes"] == 387))

# ---- 2. 我的独立清一色类 ----
cls = defaultdict(list)
hands_all = 0
for h in gen_vectors(9, 13):
    c = [0] * 34
    for i, x in enumerate(h): c[i] = x
    W = compute_W(c)
    if W:
        hands_all += 1
        cls[frozenset(W)].append(h)
report["structural"].append(("my flush hands/classes = 40196/387",
    hands_all == 40196 and len(cls) == 387))

theirs_classes = {k: set(frozenset(r["W"]) for r in cert["theorems"][k]["classes"]) for k in cert["theorems"]}
mine_set = set(cls.keys())
same = all(theirs_classes[k] == mine_set for k in theirs_classes)
report["structural"].append(("T3 class W-set == verifier class W-set (k=1..4)", same))

# ---- 3. 逐类 tau: 上界 (精确/贪心) 与下界 (greedy clique) ----
def has_common(h1, h2, k):
    return sum(min(a, b) for a, b in zip(h1, h2)) >= k

def lb_clique(hands, k):
    sel = []
    for h in hands:
        if all(not has_common(h, s, k) for s in sel):
            sel.append(h)
    return len(sel)

def cover_masks(hands, codes):
    out = []
    hs = hands
    for code in codes:
        m = 0
        for i, h in enumerate(hs):
            ok = True
            for t in set(code):
                if h[t] < code.count(t): ok = False; break
            if ok: m |= (1 << i)
        if m: out.append(m)
    return list(set(out))

def greedy_cover(masks, full):
    un = full; cnt = 0
    while un:
        best = max(masks, key=lambda m: (m & un).bit_count())
        if not (best & un): return None
        un &= ~best; cnt += 1
    return cnt

def exact_cover(masks, full, tlimit=5.0):
    masks = [m for m in set(masks) if m & full]
    masks.sort(key=lambda m: m.bit_count(), reverse=True)
    pruned = []
    for m in masks:
        if not any((m | p) == p for p in pruned): pruned.append(m)
    masks = pruned
    maxpop = max(m.bit_count() for m in masks)
    best = [greedy_cover(masks, full)]
    t0 = time.time(); nodes = [0]; to = [False]
    bits = [i for i in range(full.bit_length()) if (full >> i) & 1]
    coverers = {i: [m for m in masks if (m >> i) & 1] for i in bits}
    def rec(un, k):
        nodes[0] += 1
        if nodes[0] % 2048 == 0 and time.time() - t0 > tlimit: to[0] = True
        if to[0]: return
        if un == 0:
            best[0] = min(best[0], k); return
        if k + 1 >= best[0]: return
        rem = [i for i in bits if (un >> i) & 1]
        i = min(rem, key=lambda x: len(coverers[x]))
        for m in sorted(coverers[i], key=lambda m: (m & un).bit_count(), reverse=True):
            if k + 1 >= best[0]: break
            rec(un & ~m, k + 1)
            if to[0]: return
    rec(full, 0)
    return best[0], (not to[0])

import itertools
for k in (1, 2, 3):
    codes = list(itertools.combinations_with_replacement(range(9), k))
    my_lb = 0; my_ub = 0; n_exact = 0
    for W, hands in cls.items():
        my_lb += max(1, lb_clique(hands, k))
        masks = cover_masks(hands, codes)
        ut, ex = exact_cover(masks, (1 << len(hands)) - 1, 4.0)
        my_ub += ut
        if ex: n_exact += 1
    th = cert["theorems"]["k=%d" % k]
    report["per_k"][k] = {
        "T3_sum_tau_lb": th["sum_tau_lb"], "my_sum_tau_lb(greedy clique)": my_lb,
        "T3_sum_tau_ub": th["sum_tau_ub"], "my_sum_tau_ub": my_ub,
        "T3_n_exact": th["n_exact_classes"], "my_n_exact": n_exact,
        "budget_sub_universe": th["budget_sub_universe"],
        "k_refuted_by_my_lb": my_lb > th["budget_sub_universe"],
        "T3_conclusion": th["disproved_by_sub_universe"],
    }
    print(k, json.dumps(report["per_k"][k], ensure_ascii=False), flush=True)
json.dump(report, open("work/verify/cert_replay_report.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(report["structural"], ensure_ascii=False))
