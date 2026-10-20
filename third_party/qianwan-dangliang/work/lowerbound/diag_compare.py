# -*- coding: utf-8 -*-
"""对比 lb_flush 的精确 tau 与 lower.py 的 tau_bounds"""
import itertools, json, sys
sys.path.insert(0, "work/lowerbound")
from lower import flush_census, code_space, mask_of, tau_bounds, melds_only

hands, classes = flush_census()
print("类=%d 手=%d" % (len(classes), sum(len(v) for v in classes.values())))
for k in (1,):
    combos, reqs = code_space(9, k)
    print("k=%d 码数=%d" % (k, len(combos)))
    diffs = []
    for W, hs in classes.items():
        # 暴力精确 tau (对 9 张牌的全子集)
        supps = [frozenset(i for i in range(9) if h[i] > 0) for h in hs]
        common = set(supps[0])
        for s in supps[1:]: common &= s
        if common:
            exact = 1
        else:
            exact = None
            for size in (2, 3, 4):
                for S in itertools.combinations(range(9), size):
                    Ss = set(S)
                    if all(Ss & s for s in supps): exact = size; break
                if exact: break
        masks = [mask_of(h, reqs) for h in hs]
        lb, ub, ex, cov = tau_bounds(masks, len(combos))
        if not (lb == exact == ub):
            diffs.append((W, len(hs), exact, lb, ub, ex))
    print("不一致的类数 =", len(diffs))
    for d in diffs[:12]: print("  W=%s size=%d 暴力=%s lower=(lb %s,ub %s,exact %s)" % d)
    # 分布
    tot_b = 0; tot_l = 0
    for W, hs in classes.items():
        supps = [frozenset(i for i in range(9) if h[i] > 0) for h in hs]
        common = set(supps[0])
        for s in supps[1:]: common &= s
        if common: tot_b += 1; continue
        e=None
        for size in (2,3,4):
            for S in itertools.combinations(range(9), size):
                Ss=set(S)
                if all(Ss & s for s in supps): e=size; break
            if e: break
        tot_b += e
    print("暴力精确 Sigma tau (k=1) =", tot_b)
