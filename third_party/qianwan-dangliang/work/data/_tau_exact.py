# -*- coding: utf-8 -*-
"""_tau_exact.py -- close the open flush/honors classes exactly with a dual-LB branch and bound."""
import sys, json, itertools, time
sys.path.insert(0, r"D:\DSH\MJ2\work\data")
import mjcore as M
import multiprocessing as mp

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

def greedy_ub(C, hc, full):
    NC = len(C); u = full; chosen = []
    while u:
        bi = -1; bn = -1
        for i in range(NC):
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

def dual_lb_sub(C, hc, unc):
    idx = []
    u = unc
    while u:
        i = (u & -u).bit_length() - 1
        u &= u - 1
        idx.append(i)
    idx.sort(key=lambda i: len(hc[i]))
    NC = len(C)
    load = {}
    total = 0.0
    for h in idx:
        cs = hc[h]
        best = 1.0
        for c in cs:
            v = 1.0 - load.get(c, 0.0)
            if v < best: best = v
        if best > 1e-12:
            for c in cs: load[c] = load.get(c, 0.0) + best
            total += best
    return total

def exact(C, hc, full, deadline=None):
    ub = greedy_ub(C, hc, full)
    best = [len(ub), ub]
    memo = {}
    nodes = [0]
    def rec(unc, depth, chosen):
        nodes[0] += 1
        if deadline and nodes[0] % 512 == 0 and time.time() > deadline:
            raise TimeoutError
        if unc == 0:
            if depth < best[0]:
                best[0] = depth; best[1] = list(chosen)
            return
        prev = memo.get(unc)
        if prev is not None and prev <= depth: return
        memo[unc] = depth
        if depth + packing_lb(C, hc, unc) >= best[0]: return
        if depth + int(dual_lb_sub(C, hc, unc) + 1e-9) >= best[0]: return
        u = unc; bi = -1; bn = 10**9
        while u:
            i = (u & -u).bit_length() - 1
            u &= u - 1
            cands = [c for c in hc[i] if C[c] & unc]
            if len(cands) < bn:
                bn = len(cands); bi = i
                if bn <= 1: break
        if bi < 0: return
        cands = [c for c in hc[bi] if C[c] & unc]
        cands.sort(key=lambda c: -(C[c] & unc).bit_count())
        for c in cands:
            chosen.append(c)
            rec(unc & ~C[c], depth + 1, chosen)
            chosen.pop()
            if best[0] <= depth + 1: return
    try:
        rec(full, 0, [])
        return best[0], True, nodes[0]
    except TimeoutError:
        return best[0], False, nodes[0]

def work(args):
    n_types, rows, tlimit = args
    CANDS, CD = make(n_types)
    out = []
    for r in rows:
        hands = [tuple(int(ch) for ch in x) for x in r["hands"]]
        C, hc, full = build(hands, CANDS, CD)
        t0 = time.time()
        t, ok, nodes = exact(C, hc, full, deadline=t0 + tlimit)
        out.append({"W": r["W"], "n": len(hands), "K": r["K"], "tau": t,
                    "exact": ok, "nodes": nodes, "sec": round(time.time()-t0, 1)})
        if not ok:
            print("   TIMEOUT/inexact", r["W"], "ub=", t, flush=True)
    return out

if __name__ == "__main__":
    t0 = time.time()
    s1 = json.load(open(r"D:\DSH\MJ2\work\data\out\single.json", encoding="utf-8"))
    b = json.load(open(r"D:\DSH\MJ2\work\data\out\cert_tau_bounds.json", encoding="utf-8"))
    openm = [c for c in b["flush_m"]["classes"] if not c["exact"]]
    Wset = set(tuple(c["W"]) for c in openm)
    rows = [r for r in s1["flush_m"]["tenpai_full_W"]["classes"] if tuple(r["W"]) in Wset]
    print("open flush_m classes:", len(rows), flush=True)
    rows.sort(key=lambda r: -r["n_hands"])
    groups = [[] for _ in range(6)]
    for i, r in enumerate(rows): groups[i % 6].append(r)
    with mp.Pool(6) as pool:
        res = pool.map(work, [(9, g, 600) for g in groups])
    flat = [x for o in res for x in o]
    inex = [x for x in flat if not x["exact"]]
    closed_sum = sum(x["tau"] for x in flat if x["exact"])
    inex_sum = sum(x["tau"] for x in flat if not x["exact"])
    print("closed:", len(flat)-len(inex), " inexact:", len(inex),
          " sum(exact tau):", closed_sum, " sum(inexact UB):", inex_sum, flush=True)
    base = b["flush_m"]["sum_lb"] - sum(c["lb"] for c in openm)   # exact part
    print("exact-part sum:", base, " => SUM tau_m =", base + closed_sum + inex_sum, flush=True)
    json.dump({"classes": flat}, open(r"D:\DSH\MJ2\work\data\out\cert_tau_flush_exact.json", "w"),
              ensure_ascii=False)
    print("t=%.1fs" % (time.time()-t0), flush=True)
