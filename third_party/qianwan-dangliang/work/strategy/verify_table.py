# -*- coding: utf-8 -*-
"""verify_table.py -- 逐类见证验证(ground truth = waits13 严格口径)。"""
import sys, os, time, itertools, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjlib import *
import table_lib as TL
T0 = time.time()
T = TL.build()
CLS = T["cls"]
print("类数 =", len(CLS), flush=True)

def witness_hand(b):
    kind = b[0]
    if kind == "KOK":
        return list(b[1])
    if kind == "I":
        (c, s, pkey) = b[1]; mode = b[3]
        am, xs = T["PROFI_D"][(c, s, pkey)]
        X = xs[0]
        S = tuple(x for x in range(4) if x != c); m = 13-s
        ps = pkey[3]
        if mode == "chi": fs = TL.fam_list(S, m, True)
        elif ps: fs = TL.fam_list(S, m, False)
        else: fs = TL.fam_list(S, m, True) + TL.fam_list(S, m, False)
        if not fs: return None
        F = fs[0]
        H = [0]*34
        for i in range(CAT_LEN[c]): H[CAT_BASE[c]+i] = X[i]
        for i in range(34): H[i] += F[i]
        return H
    if kind == "II":
        (c1, s1, k1) = b[1]; (c2, s2, k2) = b[2]; mode = b[3]
        am1, xs1 = T["PROFII_D"][(c1, s1, k1)]; am2, xs2 = T["PROFII_D"][(c2, s2, k2)]
        X1 = xs1[0]; X2 = xs2[0]
        S = tuple(x for x in range(4) if x not in (c1, c2)); m = 13-s1-s2
        ps = ((k1[5] and k2[4]) or (k1[4] and k2[5]))
        if mode == "chi": fs = TL.fam_list(S, m, True)
        elif ps: fs = TL.fam_list(S, m, False)
        else: fs = TL.fam_list(S, m, True) + TL.fam_list(S, m, False)
        if not fs: return None
        F = fs[0]
        H = [0]*34
        for i in range(CAT_LEN[c1]): H[CAT_BASE[c1]+i] = X1[i]
        for i in range(CAT_LEN[c2]): H[CAT_BASE[c2]+i] = X2[i]
        for i in range(34): H[i] += F[i]
        return H
    return None

bad = {}; ok = 0
examples = {}
for W, blocks in CLS.items():
    good = False
    for b in blocks:
        H = witness_hand(b)
        if H is None or sum(H) != 13: continue
        if waits13(tuple(H)) == W: good = True; break
    if good: ok += 1
    else:
        bad[len(W)] = bad.get(len(W), 0) + 1
        examples.setdefault(len(W), []).append([[tile_name(t) for t in sorted(W)], len(blocks)])
print("见证通过 %d / %d ; 失败分布(按|W|): %s" % (ok, len(CLS), dict(sorted(bad.items()))), flush=True)
for kk in sorted(examples)[:6]:
    print("  |W|=%d 失败例: %s" % (kk, examples[kk][:3]), flush=True)
# 失败中最小的几类详细
fl = sorted([W for W in CLS if all(True for _ in [0])], key=lambda w: len(w))
print("时间 %.1fs" % (time.time()-T0))
