# -*- coding: utf-8 -*-
"""_tau_bounds.py -- certified lower/upper bounds on tau_m for all 387 flush classes.

LB1 = integral packing: a set of hands that pairwise share no common 3-code
      (each needs its own code)  -> tau >= |packing|
LB2 = fractional packing (greedy dual): weights y_h with sum_{h contains c} y_h <= 1
      for every candidate c -> tau >= ceil(sum y_h)
UB  = greedy set cover
If UB == LB -> tau is exact.
"""
import sys, json, itertools, time
sys.path.insert(0, r"D:\DSH\MJ2\work\data")
import mjcore as M

CANDS = list(itertools.combinations_with_replacement(range(9), 3))
NC = len(CANDS)
CD = []
for cd in CANDS:
    need = {}
    for x in cd: need[x] = need.get(x, 0) + 1
    CD.append(tuple(sorted(need.items())))

def build(hands):
    n = len(hands)
    C = [0] * NC
    hc = [[] for _ in range(n)]
    for j, h in enumerate(hands):
        for i in range(NC):
            ok = True
            for x, k in CD[i]:
                if h[x] < k: ok = False; break
            if ok:
                C[i] |= 1 << j
                hc[j].append(i)
    return C, hc, (1 << n) - 1

def greedy_ub(C, hc, full):
    u = full; chosen = []
    while u:
        bi = -1; bn = -1
        for i in range(NC):
            v = (C[i] & u).bit_count()
            if v > bn: bn = v; bi = i
        chosen.append(bi); u &= ~C[bi]
    return len(chosen)

def packing_lb(C, hc, full):
    u = full; cnt = 0
    while u:
        i = (u & -u).bit_length() - 1
        cnt += 1
        shared = 0
        for c in hc[i]: shared |= C[c]
        u &= ~shared
    return cnt

def dual_lb(C, hc, n):
    load = [0.0] * NC
    total = 0.0
    order = sorted(range(n), key=lambda h: len(hc[h]))
    for h in order:
        cs = hc[h]
        best = 1.0
        for c in cs:
            v = 1.0 - load[c]
            if v < best: best = v
        if best > 1e-12:
            for c in cs: load[c] += best
            total += best
    return total

if __name__ == "__main__":
    t0 = time.time()
    s1 = json.load(open(r"D:\DSH\MJ2\work\data\out\single.json", encoding="utf-8"))
    out = {}
    for key in ("flush_m", "flush_p", "flush_s"):
        rows = s1[key]["tenpai_full_W"]["classes"]
        res = []
        sum_lb = 0; sum_ub = 0; exact = 0; gap = 0
        for r in rows:
            hands = [tuple(int(ch) for ch in s) for s in r["hands"]]
            C, hc, full = build(hands)
            if (1 << len(hands)) - 1 == 0: continue
            lb1 = packing_lb(C, hc, full)
            lb2 = int(dual_lb(C, hc, len(hands)) + 1e-9)
            lb = max(lb1, lb2)
            ub = greedy_ub(C, hc, full)
            if lb > ub: lb = ub   # cannot happen; safety
            if lb == ub: exact += 1
            else: gap += 1
            sum_lb += lb; sum_ub += ub
            res.append({"W": r["W"], "n": len(hands), "K": r["K"], "lb_pack": lb1,
                        "lb_dual": lb2, "lb": lb, "ub": ub, "exact": lb == ub})
        print(key, "classes:", len(rows), " exact via bounds:", exact, " open:", gap,
              " SUM LB =", sum_lb, " SUM UB =", sum_ub, flush=True)
        print("   -> 729 budget:", "INFEASIBLE (SUM LB > 729)" if sum_lb > 729 else
              ("feasible by sum-UB" if sum_ub <= 729 else "UNDECIDED"), flush=True)
        out[key] = {"sum_lb": sum_lb, "sum_ub": sum_ub, "classes": res}
    json.dump(out, open(r"D:\DSH\MJ2\work\data\out\cert_tau_bounds.json", "w"), ensure_ascii=False)
    print("t=%.1fs" % (time.time() - t0), flush=True)
