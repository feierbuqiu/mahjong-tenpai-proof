
import json, sys, itertools
from collections import defaultdict
sys.path.insert(0, "work/verify")
from indep_core import compute_W, gen_vectors

cert = json.load(open("work/lowerbound/certificate.json", encoding="utf-8"))
cls = defaultdict(list)
for h in gen_vectors(9, 13):
    c = [0] * 34
    for i, x in enumerate(h): c[i] = x
    W = compute_W(c)
    if W: cls[frozenset(W)].append(h)

def has_common(h1, h2, k):
    return sum(min(a, b) for a, b in zip(h1, h2)) >= k

def cover_masks(hands, codes):
    out = []
    for code in codes:
        m = 0
        for i, h in enumerate(hands):
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

import time
def exact_cover(masks, full, tlimit=3.0):
    masks = [m for m in set(masks) if m & full]
    masks.sort(key=lambda m: m.bit_count(), reverse=True)
    pruned = []
    for m in masks:
        if not any((m | p) == p for p in pruned): pruned.append(m)
    masks = pruned
    best = [greedy_cover(masks, full)]
    t0 = time.time(); nodes = [0]; to = [False]
    bits = [i for i in range(full.bit_length()) if (full >> i) & 1]
    cov = {i: [m for m in masks if (m >> i) & 1] for i in bits}
    def rec(un, k):
        nodes[0] += 1
        if nodes[0] % 2048 == 0 and time.time() - t0 > tlimit: to[0] = True
        if to[0]: return
        if un == 0:
            best[0] = min(best[0], k); return
        if k + 1 >= best[0]: return
        rem = [i for i in bits if (un >> i) & 1]
        i = min(rem, key=lambda x: len(cov[x]))
        for m in sorted(cov[i], key=lambda m: (m & un).bit_count(), reverse=True):
            if k + 1 >= best[0]: break
            rec(un & ~m, k + 1)
            if to[0]: return
    rec(full, 0)
    return best[0], (not to[0])

for k in (2, 3):
    codes = list(itertools.combinations_with_replacement(range(9), k))
    t3 = {frozenset(r["W"]): r for r in cert["theorems"]["k=%d" % k]["classes"]}
    bad = 0; worse = []; better = 0; mine_ub_smaller = 0
    for W, hands in cls.items():
        r = t3.get(W)
        if r is None: continue
        masks = cover_masks(hands, codes)
        ub, ex = exact_cover(masks, (1 << len(hands)) - 1, 3.0)
        if ub < r["tau_lb"]:
            bad += 1
            if len(worse) < 5: worse.append((sorted(W), r["tau_lb"], ub, len(hands), ex))
        if ub < r["tau_ub"]: mine_ub_smaller += 1
        if r["exact"] and ub != r["tau_ub"]: better += 1
    print("k=%d classes compared=%d  T3_lb > my_ub (T3 lb 可能错): %d  my_ub < T3_ub: %d  exact-but-differ: %d" %
          (k, len(cls), bad, mine_ub_smaller, better))
    for x in worse: print("   ", x)
