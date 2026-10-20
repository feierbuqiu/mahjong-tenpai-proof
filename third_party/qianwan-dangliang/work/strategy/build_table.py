# -*- coding: utf-8 -*-
"""build_table.py -- 权威类表(严格七对子口径: 6 对 + 1 单张, 4 张同牌不算两对)。

H = A ⊎ F:
  W_std: Type I  Wp(X) ; Type II (pd1?V2:∅) ∪ (pd2?V1:∅)
  七对子附加: 需 A 是"若干对子+1 单张"(ps), |A| ∈ {1,7,13}, 且 F 全为偶对
             (F 计数 ∈{0,2}); 此时 W = W_std ∪ {z_A}(单张牌).
  非 ps 的 A: 永远无七对子附加; ps 的 A 若 ∃F 不是全偶对 => 无附加.
"""
import sys, os, json, itertools, time, pickle, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjlib import *
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)
T0 = time.time()
def log(*a): print("[%7.1fs]" % (time.time()-T0), *a, flush=True)
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

FAMC = {}
def fam_flags(cats, m):
    """返回 (chiF_exists: ∃F 计数∈{0,2}; nochiF_exists: ∃F 有计数∉{0,2}; nfam)"""
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

def pick_F(cats, m, want_chi):
    res = [None]
    def rec(i, rem, acc):
        if res[0] is not None: return
        if i == len(cats):
            if rem != 0: return
            ischi = all(x in (0,2) for x in acc)
            if ischi != want_chi: return
            res[0] = list(acc); return
        ci = cats[i]; L = CAT_LEN[ci]; base = CAT_BASE[ci]
        for sd in (0,3,6,9,12):
            if sd > rem: break
            for v in MELFAM[(L, ci==3)][sd]:
                nxt = list(acc)
                for j, x in enumerate(v): nxt[base+j] += x
                rec(i+1, rem-sd, nxt)
                if res[0] is not None: return
    rec(0, m, [0]*34)
    return res[0]

def flags9(X):
    nz = [x for x in X if x]
    all2 = all(x == 2 for x in nz)
    one2 = (sum(1 for x in nz if x == 1) == 1) and all(x == 2 for x in nz if x != 1)
    return all2, one2

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
    a2, o2 = flags9(X)
    return (frozenset(CAT_BASE[c]+t for t in Wp), frozenset(CAT_BASE[c]+t for t in V), pd,
            len(ot), (CAT_BASE[c]+ot[0]) if len(ot) == 1 else None, a2, o2)

def all_vectors(c, size):
    L = CAT_LEN[c]
    for combo in itertools.combinations_with_replacement(range(L), size):
        v = [0]*L
        for x in combo: v[x] += 1
        if max(v) <= CAP: yield tuple(v)

PROF_I = {}; PROF_II = {}
log("枚举 profiles ...")
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
log("profiles: I=%d II=%d" % (len(PROFI_D), len(PROFII_D)))

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
            if Wp:
                if (not ps) or nochiF:
                    add(Wp, ("I", (c, s, pkey), None, "nochi", None, am, len(xs)))
            if ps and chiF:
                add(Wp | {ot}, ("I", (c, s, pkey), None, "chi", ot, am, len(xs)))
T1 = len(CLS)
mismatch = []
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
                        za = None
                        if ps: za = ot1 if o21 else ot2
                        if Wstd and ((not ps) or nochiF):
                            add(Wstd, ("II", (c1, s1, k1), (c2, s2, k2), "nochi", None, am, len(xs1)*len(xs2)))
                        if ps and chiF:
                            add(Wstd | {za}, ("II", (c1, s1, k1), (c2, s2, k2), "chi", za, am, len(xs1)*len(xs2)))
T2 = len(CLS)
term = frozenset(KOK)
add(term, ("KOK", term, None, "exact", None, tuple(1 if t in term else 0 for t in range(34)), 1))
for t in KOK:
    add(term-{t}, ("KOK", term-{t}, None, "exact", None, tuple(1 if (x in term and x != t) else 0 for x in range(34)), 1))
log("类数: TypeI=%d, +TypeII=%d, +kokushi=%d" % (T1, T2, len(CLS)))

u_of = {}
for W, blocks in CLS.items():
    u = [CAP]*34
    for b in blocks:
        cv = b[5]
        for i in range(34):
            if cv[i] < u[i]: u[i] = cv[i]
    u_of[W] = tuple(u)
stats = {"classes": len(CLS), "by_size": {}, "no_common": {}, "sum_u": {}}
for W, u in u_of.items():
    stats["by_size"][len(W)] = stats["by_size"].get(len(W), 0)+1
    stats["sum_u"][sum(u)] = stats["sum_u"].get(sum(u), 0)+1
for k in (2,3,4):
    n = sum(1 for u in u_of.values() if sum(u) < k)
    stats["no_common"][str(k)] = n
    log("k=%d: 无公共码类数 = %d / %d" % (k, n, len(u_of)))
log("|W| 分布: %s" % dict(sorted(stats["by_size"].items())))
log("Σu 分布: %s" % dict(sorted(stats["sum_u"].items())))
nb = [len(v) for v in CLS.values()]
log("每类块数: 1:%d 2-3:%d 4-10:%d >10:%d  max=%d Σ=%d" % (
    sum(1 for x in nb if x == 1), sum(1 for x in nb if 2 <= x <= 3), sum(1 for x in nb if 4 <= x <= 10),
    sum(1 for x in nb if x > 10), max(nb), sum(nb)))
json.dump(stats, open(os.path.join(OUT, "table_stats.json"), "w"), ensure_ascii=False, indent=1)
pickle.dump({"cls": CLS, "u_of": u_of, "PROFI_D_keys": list(PROFI_D.keys())[:1]}, open(os.path.join(OUT, "table.pkl"), "wb"))
log("写出 table.pkl / table_stats.json")
