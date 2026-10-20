#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verifier T6: 独立精确计算"子宇宙预算引理"所需的 Σ τ_U(C).
U = 单花色(9 张) 或 字牌(7 张), k=3.
对类 C: τ_U(C) = 命中 C 中"全落在 U 内"的手牌子族的最小码(3 张多重集)数。
精确最小集合覆盖 (branch & bound), 超时则退回贪心上界并记录.
"""
import sys, os, json, time, itertools
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from indep_core import compute_W, gen_vectors, melds_only, CAP

def build_classes(K, mode, offset=0):
    cls = defaultdict(list)
    for h in gen_vectors(K, 13):
        c = [0] * 34
        for i, x in enumerate(h): c[offset + i] = x
        W = compute_W(c, chiitoi=mode)
        if W:
            cls[W].append(h)
    return cls

def multiset_codes(K):
    return [code for code in itertools.combinations_with_replacement(range(K), 3)]

def cover_masks(hands, codes):
    masks = []
    for code in codes:
        need = [0] * (max(max(h) for h in hands) and 0)  # unused
    # build per-hand containment quickly
    hs = []
    for h in hands:
        hs.append(h)
    masks = []
    for code in codes:
        m = 0
        for i, h in enumerate(hs):
            ok = True
            for t in set(code):
                if h[t] < code.count(t):
                    ok = False; break
            if ok: m |= (1 << i)
        if m: masks.append(m)
    return list(set(masks))

def greedy_cover(masks, full):
    un = full; cnt = 0
    while un:
        best = max(masks, key=lambda m: (m & un).bit_count())
        if (best & un) == 0: return None
        un &= ~best; cnt += 1
    return cnt

def exact_min_cover(masks, full, tlimit=8.0):
    masks = [m for m in set(masks) if m & full]
    if not masks: return None, 'infeasible'
    # 去掉被支配的
    masks.sort(key=lambda m: m.bit_count(), reverse=True)
    pruned = []
    for m in masks:
        if not any((m | p) == p for p in pruned):
            pruned.append(m)
    masks = pruned
    maxpop = max(m.bit_count() for m in masks)
    t0 = time.time()
    best = [greedy_cover(masks, full)]
    nodes = [0]
    timed_out = [False]
    # covering map: bit -> list of masks containing it
    bits = [i for i in range(full.bit_length()) if (full >> i) & 1]
    coverers = {i: [m for m in masks if (m >> i) & 1] for i in bits}
    def rec(un, k):
        nodes[0] += 1
        if nodes[0] % 4096 == 0 and time.time() - t0 > tlimit:
            timed_out[0] = True
        if timed_out[0]: return
        if un == 0:
            if k < best[0]: best[0] = k
            return
        if k + 1 >= best[0]: return
        # 选覆盖者最少的未覆盖手牌
        rem = [i for i in bits if (un >> i) & 1]
        i = min(rem, key=lambda x: len(coverers[x]))
        cand = sorted(coverers[i], key=lambda m: (m & un).bit_count(), reverse=True)
        for m in cand:
            nk = k + 1
            if nk >= best[0]: break
            rec(un & ~m, nk)
            if timed_out[0]: return
    rec(full, 0)
    return best[0], ('timeout(ub)' if timed_out[0] else 'exact')

def run(K, name, mode, offset=0, tlimit=8.0):
    cls = build_classes(K, mode, offset)
    codes = multiset_codes(K)
    rows = []
    t0 = time.time()
    for W, hands in sorted(cls.items(), key=lambda kv: -len(kv[1])):
        masks = cover_masks(hands, codes)
        full = (1 << len(hands)) - 1
        tau, kind = exact_min_cover(masks, full, tlimit)
        rows.append({'W': sorted(W), 'n_hands': len(hands), 'tau': tau, 'kind': kind})
    dist = defaultdict(int)
    for r in rows: dist[r['tau']] += 1
    out = {'name': name, 'K': K, 'mode': mode, 'n_classes': len(rows),
           'sum_tau': sum(r['tau'] for r in rows),
           'tau_dist': {str(k): v for k, v in sorted(dist.items())},
           'n_timeouts': sum(1 for r in rows if r['kind'] != 'exact'),
           'code_budget': K ** 3, 'secs': round(time.time() - t0, 1),
           'rows': rows}
    return out

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'strict'
    res = []
    for (K, name, off) in [(9, 'suit', 0), (7, 'honors', 27)]:
        o = run(K, name, mode, off)
        o2 = dict(o); o2.pop('rows')
        print(json.dumps(o2, ensure_ascii=False), flush=True)
        res.append({k: v for k, v in o.items() if k != 'rows'})
        json.dump(o, open(f'work/verify/tau_{name}_{mode}.json', 'w'))
    json.dump(res, open(f'work/verify/tau_summary_{mode}.json', 'w'))
