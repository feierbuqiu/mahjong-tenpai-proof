# -*- coding: utf-8 -*-
"""_tau_cert.py -- machine-checkable tau certificate for the single-suit / honour sub-universes.

For every class C of the flush sectors (3 x 387) and the honours sector (28) we emit
  lb  : certified lower bound on tau_U(C)  (max of integral packing and greedy fractional packing)
  ub  : greedy cover size (a valid hitting set)  -> tau_U(C) <= ub
  cover: the hitting-set codes themselves
  exact: lb == ub  -> tau_U(C) is exactly lb
Every cover is re-verified here directly against every hand of the class.
"""
import sys, json, itertools, time
sys.path.insert(0, r"D:\DSH\MJ2\work\data")
import mjcore as M

def make(n_types):
    CANDS = list(itertools.combinations_with_replacement(range(n_types), 3))
    CD = []
    for cd in CANDS:
        need = {}
        for x in cd: need[x] = need.get(x, 0) + 1
        CD.append(tuple(sorted(need.items())))
    return CANDS, CD

def build(hands, CANDS, CD):
    n = len(hands); NC = len(CANDS)
    C = [0]*NC; hc = [[] for _ in range(n)]
    for j, h in enumerate(hands):
        for i in range(NC):
            ok = True
            for x, k in CD[i]:
                if h[x] < k: ok = False; break
            if ok:
                C[i] |= 1 << j; hc[j].append(i)
    return C, hc, (1 << n) - 1

def greedy(C, full):
    u = full; chosen = []
    while u:
        bi = -1; bn = -1
        for i in range(len(C)):
            v = (C[i] & u).bit_count()
            if v > bn: bn = v; bi = i
        chosen.append(bi); u &= ~C[bi]
    return chosen

def packing_lb(C, hc, unc):
    u = unc; cnt = 0
    while u:
        i = (u & -u).bit_length() - 1
        cnt += 1
        shared = 0
        for c in hc[i]: shared |= C[c]
        u &= ~shared
    return cnt

def dual_lb(C, hc, n):
    load = {}; total = 0.0
    for h in sorted(range(n), key=lambda x: len(hc[x])):
        best = 1.0
        for c in hc[h]:
            v = 1.0 - load.get(c, 0.0)
            if v < best: best = v
        if best > 1e-12:
            for c in hc[h]: load[c] = load.get(c, 0.0) + best
            total += best
    return total

def run(key, n_types, rows, out):
    CANDS, CD = make(n_types)
    res = []
    sl = 0; su = 0; nex = 0
    for r in rows:
        hands = [tuple(int(ch) for ch in x) for x in r["hands"]]
        C, hc, full = build(hands, CANDS, CD)
        lb = max(packing_lb(C, hc, full), int(dual_lb(C, hc, len(hands)) + 1e-9))
        cov = greedy(C, full)
        ub = len(cov)
        # verify cover
        u = 0
        for c in cov: u |= C[c]
        assert u == full, ("cover invalid", r["W"])
        codes = ["".join(str(x + 1) for x in CANDS[c]) for c in cov]
        res.append({"W": r["W"], "n_hands": len(hands), "K": r["K"], "lb": lb, "ub": ub,
                    "exact": lb == ub, "cover": codes})
        sl += lb; su += ub
        if lb == ub: nex += 1
    out[key] = {"n_classes": len(rows), "exact_classes": nex, "sum_lb": sl, "sum_ub": su,
                "budget": n_types ** 3, "classes": res}
    print("%-10s classes=%3d exact=%3d SUM_LB=%4d SUM_UB=%4d budget=%d -> %s"
          % (key, len(rows), nex, sl, su, n_types ** 3,
             "INFEASIBLE" if sl > n_types ** 3 else ("sum-UB fits" if su <= n_types ** 3 else "UNDECIDED")),
          flush=True)

if __name__ == "__main__":
    t0 = time.time()
    s1 = json.load(open(r"D:\DSH\MJ2\work\data\out\single.json", encoding="utf-8"))
    out = {}
    run("flush_m", 9, s1["flush_m"]["tenpai_full_W"]["classes"], out)
    run("flush_p", 9, s1["flush_p"]["tenpai_full_W"]["classes"], out)
    run("flush_s", 9, s1["flush_s"]["tenpai_full_W"]["classes"], out)
    run("honors_z", 7, s1["honors_z"]["tenpai_full_W"]["classes"], out)
    # known exact values from the dedicated B&B run (56 classes closed) + 2 proven earlier
    try:
        ex = json.load(open(r"D:\DSH\MJ2\work\data\out\cert_tau_flush_exact.json", encoding="utf-8"))
        out["bb_closed"] = {c["W"][0] if False else str(c["W"]): c for c in ex["classes"]}
    except Exception as e:
        out["bb_closed"] = {}
    json.dump(out, open(r"D:\DSH\MJ2\work\data\out\cert_tau.json", "w"), ensure_ascii=False)
    print("wrote out/cert_tau.json  t=%.1fs" % (time.time() - t0), flush=True)
