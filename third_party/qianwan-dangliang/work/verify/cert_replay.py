#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T6a: 独立重放 + 主动证伪 k=1 / k=2 不可行证书.
引理(子宇宙预算): 对任意牌集合 U, 令 tau_U(C) = C 中"全落 U 内"手牌子族在 Codes(U) 内的最小命中集.
  => Sum_C tau_U(C) <= |Codes(U)| = K^k  (不同类的码集两两不交)
下界: tau_U(C) >= 2 iff 类内不存在公共 k-码 (sum_t min_H count_H(t) < k).
"""
import sys, json, itertools, time
sys.path.insert(0, "work/verify")
from collections import defaultdict
from indep_core import compute_W, gen_vectors

def universe_classes(K, offset):
    cls = defaultdict(list)
    for h in gen_vectors(K, 13):
        c = [0] * 34
        for i, x in enumerate(h): c[offset + i] = x
        W = compute_W(c)          # strict 天凤口径
        if W: cls[W].append(h)
    return cls

def no_common(cls, k):
    n = 0
    for W, hands in cls.items():
        m = [min(h[t] for h in hands) for t in range(len(hands[0]))]
        if sum(m) < k: n += 1
    return n

t0 = time.time()
res = {"note": "strict 天凤七对子口径; 所有数字由 verifier 独立枚举得到", "universes": {}}
for name, K, off in [("m", 9, 0), ("p", 9, 9), ("s", 9, 18), ("z", 7, 27)]:
    cls = universe_classes(K, off)
    n = len(cls)
    nc = {str(k): no_common(cls, k) for k in (1, 2, 3, 4)}
    row = {"classes": n, "hands": sum(len(v) for v in cls.values()), "no_common": nc,
           "sum_tau_lb_k1": n + nc["1"], "budget_k1": K, "k1_dead": (n + nc["1"]) > K,
           "sum_tau_lb_k2": n + nc["2"], "budget_k2": K * K, "k2_dead": (n + nc["2"]) > K * K}
    res["universes"][name] = row
    print(name, json.dumps(row, ensure_ascii=False), flush=True)

# 全局计数下界 (需要全局类数 2846, 由 census.py full 独立得到)
theirs = json.load(open("work/data/out/global.json", encoding="utf-8"))
mine = json.load(open("work/verify/census_strict.json", encoding="utf-8"))
res["global"] = {
    "verifier_classes": len(mine), "enum_core_classes": theirs["n_classes"],
    "budget_k1": 34, "budget_k2": 34 * 34, "budget_k3": 34 ** 3,
    "k1_dead_global": len(mine) > 34, "k2_dead_global": len(mine) > 1156,
    "k3_dead_global": len(mine) > 34 ** 3,
}
print("global", json.dumps(res["global"], ensure_ascii=False), flush=True)
res["elapsed"] = round(time.time() - t0, 1)
json.dump(res, open("work/verify/cert_k1_k2.json", "w"), ensure_ascii=False, indent=1)
