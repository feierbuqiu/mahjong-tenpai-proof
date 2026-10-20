# -*- coding: utf-8 -*-
"""_tau_flush.py -- exact transversal numbers tau_m of the 387 flush classes + certificate."""
import sys, json, itertools, time
sys.path.insert(0, r"D:\DSH\MJ2\work\data")
import mjcore as M
import multiprocessing as mp

CANDS = list(itertools.combinations_with_replacement(range(9), 3))
NC = len(CANDS)
# multiplicity-aware requirement per candidate, e.g. (3,3,3) needs count >= 3
CD = []
for cd in CANDS:
    need = {}
    for x in cd:
        need[x] = need.get(x, 0) + 1
    CD.append(tuple(sorted(need.items())))

def build(hands):
    n = len(hands)
    C = [0] * NC
    hc = [[] for _ in range(n)]
    for j, h in enumerate(hands):
        for i in range(NC):
            ok = True
            for x, k in CD[i]:
                if h[x] < k:
                    ok = False
                    break
            if ok:
                C[i] |= 1 << j
                hc[j].append(i)
    return C, hc, (1 << n) - 1

def packing_lb(unc, C, hc):
    cnt = 0
    u = unc
    while u:
        i = (u & -u).bit_length() - 1
        cnt += 1
        shared = 0
        for c in hc[i]:
            shared |= C[c]
        u &= ~shared
    return cnt

def greedy_ub(C, full):
    u = full
    chosen = []
    while u:
        bi = -1
        bn = -1
        for i in range(NC):
            v = (C[i] & u).bit_count()
            if v > bn:
                bn = v
                bi = i
        chosen.append(bi)
        u &= ~C[bi]
    return chosen


def bb(C, hc, full):
    g = greedy_ub(C, full)
    best = [len(g), g]
    memo = {}
    def rec(unc, depth, chosen):
        if unc == 0:
            if depth < best[0]:
                best[0] = depth
                best[1] = list(chosen)
            return
        prev = memo.get(unc)
        if prev is not None and prev <= depth:
            return
        memo[unc] = depth
        if depth + packing_lb(unc, C, hc) >= best[0]:
            return
        # pick uncovered hand with fewest covering candidates
        u = unc
        bi = -1; bn = 10 ** 9
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
            if best[0] <= depth + 1:
                return
    rec(full, 0, [])
    return best[1]

def exact(C, hc, full):
    idx = [i for i in range(NC) if C[i] & full]
    for i in idx:
        if (C[i] & full) == full:
            return [i]
    for i in idx:
        u = full & ~C[i]
        if u == 0:
            return [i]
        for j in idx:
            if (u & ~C[j]) == 0:
                return [i, j]
    for i in idx:
        u1 = full & ~C[i]
        for j in idx:
            u2 = u1 & ~C[j]
            if u2 == 0:
                return [i, j]
            for k in idx:
                if (u2 & ~C[k]) == 0:
                    return [i, j, k]
    return bb(C, hc, full)

def work(rows):
    out = []
    for r in rows:
        hands = [tuple(int(ch) for ch in s) for s in r["hands"]]
        C, hc, full = build(hands)
        t0 = time.time()
        w = exact(C, hc, full)
        dt = time.time() - t0
        if dt > 2.0:
            print("   slow class W=%s n=%d K=%d tau=%d %.1fs" % (r["W"], len(hands), r["K"], len(w), dt), flush=True)
        cov = 0
        for c in w:
            cov |= C[c]
        assert cov == full, ("witness fails", r["W"])
        out.append({"Wmask": r["Wmask"], "W": r["W"], "K": r["K"], "n_hands": len(hands),
                    "tau": len(w),
                    "codes": ["".join(str(x + 1) for x in CANDS[c]) for c in w]})
    return out

if __name__ == "__main__":
    t0 = time.time()
    s1 = json.load(open(r"D:\DSH\MJ2\work\data\out\single.json", encoding="utf-8"))
    res = {}
    for key in ("flush_m", "flush_p", "flush_s"):
        rows = s1[key]["tenpai_full_W"]["classes"]
        rows2 = sorted(rows, key=lambda r: -r["n_hands"])
        groups = [[] for _ in range(6)]
        for i, r in enumerate(rows2):
            groups[i % 6].append(r)
        with mp.Pool(6) as pool:
            out = pool.map(work, groups)
        flat = [x for o in out for x in o]
        dist = {}
        sm = 0
        for x in flat:
            dist[x["tau"]] = dist.get(x["tau"], 0) + 1
            sm += x["tau"]
        print(key, "classes:", len(flat), "tau dist:", dict(sorted(dist.items())), "SUM tau =", sm,
              "budget 729 ->", "INFEASIBLE" if sm > 729 else "not refuted", "%.1fs" % (time.time() - t0), flush=True)
        res[key] = {"dist": {str(k): v for k, v in dist.items()}, "sum": sm, "classes": flat}
    json.dump(res, open(r"D:\DSH\MJ2\work\data\out\cert_tau_flush.json", "w"), ensure_ascii=False, indent=1)
    print("t=%.1fs" % (time.time() - t0), flush=True)
