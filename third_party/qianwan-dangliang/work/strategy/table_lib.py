# -*- coding: utf-8 -*-
"""table_lib.py -- 严格七对子口径的类表(供 strategy.py / check.py 复用)。

块 = (kind, key1, key2, mode, z, cap, nsrc)
  kind='I'  : key1=(c,s,pkey)  pkey=(Wp,odd,ot,ps)
  kind='II' : key1=(c1,s1,k1), key2=(c2,s2,k2)  k=(V,pd,odd,ot,all2,one2)
  kind='KOK': key1=W(W 本身)
"""
import itertools, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjlib import *
CAP = 4
SIZES_I = (1,4,7,10,13); SIZES_II = (2,5,8,11)
KOK = tuple(KOKUSHI_TILES)

def seg_melds(size, length, honors):
    res = []
    for combo in itertools.combinations_with_replacement(range(length), size):
        c = [0]*length
        for x in combo: c[x] += 1
        if max(c) <= CAP and can_melds(tuple(c), honors): res.append(tuple(c))
    return res

MELFAM = {k: {s: (seg_melds(s, k[0], k[1]) if s else [tuple([0]*k[0])]) for s in (0,3,6,9,12)} for k in ((9,False),(7,True))}
MELDS_IN_CAT = {}
for ci in range(4):
    L = CAT_LEN[ci]; base = CAT_BASE[ci]
    lst = []
    for i in range(L):
        v = [0]*34; v[base+i] = 3; lst.append(tuple(v))
    if ci < 3:
        for i in range(L-2):
            v = [0]*34; v[base+i] += 1; v[base+i+1] += 1; v[base+i+2] += 1; lst.append(tuple(v))
    MELDS_IN_CAT[ci] = lst

FAMC = {}
def fam_flags(cats, m):
    key = (tuple(cats), m)
    if key in FAMC: return FAMC[key]
    chi = False; nochi = False; n = 0
    def rec(i, rem, acc):
        nonlocal chi, nochi, n
        if i == len(cats):
            if rem != 0: return
            n += 1
            if all(x in (0,2) for x in acc): chi = True
            else: nochi = True
            return
        ci = cats[i]; L = CAT_LEN[ci]; base = CAT_BASE[ci]
        for sd in (0,3,6,9,12):
            if sd > rem: break
            for v in MELFAM[(L, ci==3)][sd]:
                nxt = list(acc)
                for j, x in enumerate(v): nxt[base+j] += x
                rec(i+1, rem-sd, nxt)
    rec(0, m, [0]*34)
    FAMC[key] = (chi, nochi, n)
    return FAMC[key]

FAMLIST = {}
def fam_list(cats, m, want_chi):
    key = (tuple(cats), m, want_chi)
    if key in FAMLIST: return FAMLIST[key]
    out = []
    def rec(i, rem, acc):
        if i == len(cats):
            if rem != 0: return
            if (all(x in (0,2) for x in acc)) == want_chi: out.append(tuple(acc))
            return
        ci = cats[i]; L = CAT_LEN[ci]; base = CAT_BASE[ci]
        for sd in (0,3,6,9,12):
            if sd > rem: break
            for v in MELFAM[(L, ci==3)][sd]:
                nxt = list(acc)
                for j, x in enumerate(v): nxt[base+j] += x
                rec(i+1, rem-sd, nxt)
    rec(0, m, [0]*34)
    FAMLIST[key] = out
    return out

def flags_vec(X):
    nz = [x for x in X if x]
    return all(x == 2 for x in nz), (sum(1 for x in nz if x == 1) == 1 and all(x == 2 for x in nz if x != 1))

def x_profile(c, X):
    L = CAT_LEN[c]; h = (c == 3)
    Wp = set(); V = set()
    for t in range(L):
        if X[t] < CAP:
            d = list(X); d[t] += 1
            for pi in range(L):
                if d[pi] >= 2:
                    e = list(d); e[pi] -= 2
                    if can_melds(tuple(e), h): Wp.add(t); break
            if can_melds(tuple(d), h): V.add(t)
    pd = False
    for pi in range(L):
        if X[pi] >= 2:
            e = list(X); e[pi] -= 2
            if can_melds(tuple(e), h): pd = True; break
    ot = [i for i, x in enumerate(X) if x % 2]
    a2, o2 = flags_vec(X)
    return (frozenset(CAT_BASE[c]+t for t in Wp), frozenset(CAT_BASE[c]+t for t in V), pd,
            len(ot), (CAT_BASE[c]+ot[0]) if len(ot) == 1 else None, a2, o2)

def all_vectors(c, size):
    L = CAT_LEN[c]
    for combo in itertools.combinations_with_replacement(range(L), size):
        v = [0]*L
        for x in combo: v[x] += 1
        if max(v) <= CAP: yield tuple(v)

def build(report=None):
    PROF_I = {}; PROF_II = {}
    for c in range(4):
        for s in SIZES_I:
            g = {}
            for X in all_vectors(c, s):
                Wp, V, pd, odd, ot, a2, o2 = x_profile(c, X)
                k = (Wp, odd, ot, o2)
                e = g.setdefault(k, [None, []])
                if e[0] is None: e[0] = [0]*34
                e[1].append(X)
                for i in range(CAT_LEN[c]):
                    if X[i] < e[0][CAT_BASE[c]+i]: e[0][CAT_BASE[c]+i] = X[i]
            PROF_I[(c, s)] = [(k, tuple(v[0]), v[1]) for k, v in g.items()]
        for s in SIZES_II:
            g = {}
            for X in all_vectors(c, s):
                Wp, V, pd, odd, ot, a2, o2 = x_profile(c, X)
                k = (V, pd, odd, ot, a2, o2)
                e = g.setdefault(k, [None, []])
                if e[0] is None: e[0] = [0]*34
                e[1].append(X)
                for i in range(CAT_LEN[c]):
                    if X[i] < e[0][CAT_BASE[c]+i]: e[0][CAT_BASE[c]+i] = X[i]
            PROF_II[(c, s)] = [(k, tuple(v[0]), v[1]) for k, v in g.items()]
    PROFI_D = {(c, s, k): (am, xs) for (c, s), lst in PROF_I.items() for (k, am, xs) in lst}
    PROFII_D = {(c, s, k): (am, xs) for (c, s), lst in PROF_II.items() for (k, am, xs) in lst}
    CLS = {}
    def add(W, blk):
        if not W: return
        CLS.setdefault(frozenset(W), []).append(blk)
    for c in range(4):
        S = tuple(x for x in range(4) if x != c)
        for s in SIZES_I:
            m = 13-s
            chiF, nochiF, nfam = fam_flags(S, m)
            for (pkey, am, xs) in PROF_I[(c, s)]:
                Wp, odd, ot, ps = pkey
                if Wp and ((not ps) or nochiF):
                    add(Wp, ("I", (c, s, pkey), None, "nochi", None, am, len(xs)))
                if ps and chiF:
                    add(Wp | {ot}, ("I", (c, s, pkey), None, "chi", ot, am, len(xs)))
    for c1 in range(4):
        for c2 in range(c1+1, 4):
            S = tuple(x for x in range(4) if x not in (c1, c2))
            for s1 in SIZES_II:
                for s2 in SIZES_II:
                    tot = s1+s2
                    if tot not in (4,7,10,13): continue
                    m = 13-tot
                    chiF, nochiF, nfam = fam_flags(S, m)
                    for (k1, am1, xs1) in PROF_II[(c1, s1)]:
                        V1, pd1, odd1, ot1, a21, o21 = k1
                        for (k2, am2, xs2) in PROF_II[(c2, s2)]:
                            V2, pd2, odd2, ot2, a22, o22 = k2
                            am = tuple(min(CAP, am1[i]+am2[i]) for i in range(34))
                            Wstd = (V2 if pd1 else frozenset()) | (V1 if pd2 else frozenset())
                            ps = (o21 and a22) or (a21 and o22)
                            za = (ot1 if o21 else ot2) if ps else None
                            if Wstd and ((not ps) or nochiF):
                                add(Wstd, ("II", (c1, s1, k1), (c2, s2, k2), "nochi", None, am, len(xs1)*len(xs2)))
                            if ps and chiF:
                                add(Wstd | {za}, ("II", (c1, s1, k1), (c2, s2, k2), "chi", za, am, len(xs1)*len(xs2)))
    # 国士: 直接枚举所有国士听牌手牌(13 面 + 12 种带一对), 用 waits13 定类
    H13 = [0]*34
    for t in KOK: H13[t] = 1
    add(frozenset(waits13(tuple(H13))), ("KOK", tuple(H13), None, "exact", None, tuple(H13), 1))
    for t in KOK:                      # 缺 t
        for d in KOK:                  # 重复的牌
            if d == t: continue
            H = [0]*34
            for x in KOK: H[x] = 1
            H[t] = 0; H[d] += 1
            W = frozenset(waits13(tuple(H)))
            add(W, ("KOK", tuple(H), t, "exact", None, tuple(H), 1))
    return {"cls": CLS, "PROFI_D": PROFI_D, "PROFII_D": PROFII_D,
            "fam_list": fam_list, "fam_flags": fam_flags}

def block_sources(T, b):
    """返回块的来源描述: ('xset', [X,...]) | ('pairs', [(X1,X2),...]) | ('fam', [F,...]) | ('hand', [H])"""
    kind = b[0]
    if kind == "I":
        (c, s, pkey) = b[1]
        am, xs = T["PROFI_D"][(c, s, pkey)]
        return "xset", [(c, X) for X in xs]
    if kind == "II":
        (c1, s1, k1) = b[1]; (c2, s2, k2) = b[2]
        am1, xs1 = T["PROFII_D"][(c1, s1, k1)]; am2, xs2 = T["PROFII_D"][(c2, s2, k2)]
        return "pairs", [(c1, X1, c2, X2) for X1 in xs1 for X2 in xs2]
    (W,) = (b[1],)
    return "hand", [W]
