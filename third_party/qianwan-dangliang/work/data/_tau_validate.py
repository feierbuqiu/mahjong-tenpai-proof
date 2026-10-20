# -*- coding: utf-8 -*-
"""_tau_validate.py -- validate exact set-cover (tau<=3 loops + bb) against brute force."""
import itertools, random

def greedy_ub(sets, full):
    u = full; chosen = []
    while u:
        bi = -1; bn = -1
        for i, c in enumerate(sets):
            v = (c & u).bit_count()
            if v > bn: bn = v; bi = i
        chosen.append(bi); u &= ~sets[bi]
    return chosen

def packing_lb(sets, hc, unc):
    u = unc; cnt = 0
    while u:
        i = (u & -u).bit_length() - 1
        if not hc[i]: return 10 ** 9
        cnt += 1
        shared = 0
        for c in hc[i]: shared |= sets[c]
        u &= ~shared
    return cnt

def dual_lb(sets, hc, unc):
    idx = []; u = unc
    while u:
        i = (u & -u).bit_length() - 1; u &= u - 1; idx.append(i)
    idx.sort(key=lambda i: len(hc[i]))
    load = {}; total = 0.0
    for h in idx:
        best = 1.0
        for c in hc[h]:
            v = 1.0 - load.get(c, 0.0)
            if v < best: best = v
        if best > 1e-12:
            for c in hc[h]: load[c] = load.get(c, 0.0) + best
            total += best
    return total

def bb(sets, hc, full):
    g = greedy_ub(sets, full)
    best = [len(g), g]
    memo = {}
    def rec(unc, depth, chosen):
        if unc == 0:
            if depth < best[0]: best[0] = depth; best[1] = list(chosen)
            return
        prev = memo.get(unc)
        if prev is not None and prev <= depth: return
        memo[unc] = depth
        if depth + packing_lb(sets, hc, unc) >= best[0]: return
        if depth + int(dual_lb(sets, hc, unc) + 1e-9) >= best[0]: return
        u = unc; bi = -1; bn = 10**9
        while u:
            i = (u & -u).bit_length() - 1; u &= u - 1
            cs = [c for c in hc[i] if sets[c] & unc]
            if len(cs) < bn: bn = len(cs); bi = i
            if bn <= 1: break
        if bi < 0: return
        cs = [c for c in hc[bi] if sets[c] & unc]
        cs.sort(key=lambda c: -(sets[c] & unc).bit_count())
        for c in cs:
            chosen.append(c); rec(unc & ~sets[c], depth + 1, chosen); chosen.pop()
            if best[0] <= depth + 1: return
    rec(full, 0, [])
    return best[1]

def exact(sets, hc, full):
    m = len(sets)
    for i in range(m):
        if (sets[i] & full) == full: return [i]
    for i in range(m):
        u = full & ~sets[i]
        if u == 0: return [i]
        for j in range(m):
            if (u & ~sets[j]) == 0: return [i, j]
    for i in range(m):
        u1 = full & ~sets[i]
        for j in range(m):
            u2 = u1 & ~sets[j]
            if u2 == 0: return [i, j]
            for k in range(m):
                if (u2 & ~sets[k]) == 0: return [i, j, k]
    return bb(sets, hc, full)

def brute(sets, full):
    m = len(sets)
    for r in range(1, m + 1):
        for combo in itertools.combinations(range(m), r):
            u = 0
            for c in combo: u |= sets[c]
            if u == full: return r
    return None

rng = random.Random(7)
bad = 0; tested = 0; t0 = __import__("time").time()
for trial in range(800):
    ne = rng.randint(1, 12); m = rng.randint(1, 9)
    full = (1 << ne) - 1
    sets = []
    for _ in range(m):
        v = 0
        for e in range(ne):
            if rng.random() < 0.4: v |= 1 << e
        v |= 1 << rng.randrange(ne)
        sets.append(v)
    hc = [[] for _ in range(ne)]
    for i, v in enumerate(sets):
        for e in range(ne):
            if (v >> e) & 1: hc[e].append(i)
    if any(not h for h in hc):   # every element must be covered by >=1 set
        continue
    r = exact(sets, hc, full)
    e = brute(sets, full)
    tested += 1
    if len(r) != e:
        bad += 1
        if bad <= 3: print("MISMATCH got", len(r), "brute", e, sets)
    # witness check
    u = 0
    for c in r: u |= sets[c]
    assert u == full, ("witness invalid", sets, r)
print("validation: %d instances, mismatches = %d  (%.1fs)" % (tested, bad, __import__("time").time()-t0))
