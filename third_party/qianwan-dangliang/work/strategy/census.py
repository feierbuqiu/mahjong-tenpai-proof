# -*- coding: utf-8 -*-
"""census.py -- 结构化全局类普查(designer-encoder, work/strategy/) —— 修正版。

H = A ⊎ F; W(H) = W_std(A) ∪ {z : odd(A)+odd(F)=1, z=唯一奇数张}.
Type I : A 全在一个类别 c, |X| ∈ {1,4,7,10,13}, W_std = Wp(X)
Type II: A 分属 c1,c2, |Xi| ∈ {2,5,8,11}, W_std = (pd1?V2:∅) ∪ (pd2?V1:∅)
"""
import sys, os, json, itertools, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjlib import *

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)
T0 = time.time()
def log(*a): print("[%7.1fs]" % (time.time() - T0), *a, flush=True)

CAP = 4
SIZES_I = (1, 4, 7, 10, 13)
SIZES_II = (2, 5, 8, 11)
LC = ((9, False), (9, False), (9, False), (7, True))

def seg_melds(size, length, honors):
    res = []
    for combo in itertools.combinations_with_replacement(range(length), size):
        c = [0]*length
        for x in combo: c[x] += 1
        if max(c) > CAP: continue
        if can_melds(tuple(c), honors): res.append(tuple(c))
    return res

MELD_FAM = {}
for key in ((9, False), (7, True)):
    L, h = key
    MELD_FAM[key] = {s: (seg_melds(s, L, h) if s else [tuple([0]*L)]) for s in (0, 3, 6, 9, 12)}
log("面子族: " + ", ".join("%s s%d->%d" % (k, s, len(v)) for k, d in MELD_FAM.items() for s, v in d.items()))

# ------------- (S,m) 家族分析
FAM = {}
def fam_stats(cats, m):
    key = (tuple(cats), m)
    if key in FAM: return FAM[key]
    st = {0: (True, frozenset(), False)}   # size -> (has odd0, set of tiles for exact-1-odd, has 2+)
    for ci in cats:
        L = CAT_LEN[ci]
        fam = MELD_FAM[(L, ci == 3)]
        base = CAT_BASE[ci]
        new = {}
        for sz, (h0, z1, h2) in st.items():
            for sd, vecs in fam.items():
                ns = sz + sd
                if ns > m: continue
                for vec in vecs:
                    ot = {base + i for i, x in enumerate(vec) if x % 2}
                nodd = len(ot)
                nh0, nz1, nh2 = new.get(ns, (False, frozenset(), False))
                if h0 and nodd == 0: nh0 = True
                if h0 and nodd == 1: nz1 = nz1 | frozenset(ot)
                if h0 and nodd >= 2: nh2 = True
                if h2: nh2 = True
                if z1:
                    if nodd == 0: nz1 = nz1 | z1
                    else: nh2 = True
                new[ns] = (nh0, nz1, nh2)
        st = new
    r = st.get(m, (False, frozenset(), False))
    res = {"zero_odd": r[0], "odd1": set(r[1]), "two_plus": r[2],
           "has_odd_ge1": bool(r[1]) or r[2], "odd_not1": r[0] or r[2]}
    FAM[key] = res
    return res
log("(S,m) 家族分析完成, 共 %d 组" % (4*5*2 + 6*5*2))

# ------------- X 剖析
def rem_pair(v, pi):
    w = list(v); w[pi] -= 2
    return tuple(w)

def x_profile(c, X):
    L = CAT_LEN[c]; h = (c == 3)
    Wp = set(); V = set()
    for t in range(L):
        if X[t] < CAP:
            d = list(X); d[t] += 1
            d = tuple(d)
            if any(d[pi] >= 2 and can_melds(rem_pair(d, pi), h) for pi in range(L)): Wp.add(t)
            if can_melds(d, h): V.add(t)
    pd = any(X[pi] >= 2 and can_melds(rem_pair(X, pi), h) for pi in range(L))
    ot = tuple(i for i, x in enumerate(X) if x % 2)
    return (frozenset(CAT_BASE[c] + t for t in Wp), frozenset(CAT_BASE[c] + t for t in V), pd,
            len(ot), (CAT_BASE[c] + ot[0]) if len(ot) == 1 else None)

def all_vectors(c, size):
    L = CAT_LEN[c]
    for combo in itertools.combinations_with_replacement(range(L), size):
        v = [0]*L
        for x in combo: v[x] += 1
        if max(v) <= CAP: yield tuple(v)

PROF_I = {}   # (c,s) -> dict (Wp,odd,ot) -> count
PROF_II = {}  # (c,s) -> dict (V,pd,odd,ot) -> count
for c in range(4):
    for s in SIZES_I:
        d = {}
        for X in all_vectors(c, s):
            Wp, V, pd, odd, ot = x_profile(c, X)
            k = (Wp, odd, ot)
            d[k] = d.get(k, 0) + 1
        PROF_I[(c, s)] = d
    for s in SIZES_II:
        d = {}
        for X in all_vectors(c, s):
            Wp, V, pd, odd, ot = x_profile(c, X)
            k = (V, pd, odd, ot)
            d[k] = d.get(k, 0) + 1
        PROF_II[(c, s)] = d
log("profile 数: I=" + str({k: len(v) for k, v in PROF_I.items()}) + " ; II=" + str({k: len(v) for k, v in PROF_II.items()}))

classes = {}
def add_class(W, src):
    if not W: return
    classes.setdefault(W, []).append(src)

# ------------- Type I
for c in range(4):
    S = tuple(x for x in range(4) if x != c)
    for s in SIZES_I:
        m = 13 - s
        fs = fam_stats(S, m)
        for (Wp, odd, ot), cnt in PROF_I[(c, s)].items():
            if Wp:
                noch = (fs["has_odd_ge1"] if odd == 1 else fs["odd_not1"] if odd == 0 else True)
                if noch: add_class(Wp, ("I", c, s, None, cnt))
            if odd == 1:
                if fs["zero_odd"] and ot is not None:
                    add_class(frozenset(Wp | {ot}), ("I", c, s, ot, cnt))
            elif odd == 0:
                for z in sorted(fs["odd1"]):
                    add_class(frozenset(Wp | {z}), ("I", c, s, z, cnt))
log("Type I 后类数: %d" % len(classes))

# ------------- Type II (按 (V,pd) 分组加速)
for c1 in range(4):
    for c2 in range(c1+1, 4):
        S = tuple(x for x in range(4) if x not in (c1, c2))
        # 把 (c1,s) 的 profile 按 (V,pd) 分组, 保留 (s,odd,ot,cnt)
        g1 = {}
        for s in SIZES_II:
            for (V, pd, odd, ot), cnt in PROF_II[(c1, s)].items():
                g1.setdefault((V, pd), []).append((s, odd, ot, cnt))
        g2 = {}
        for s in SIZES_II:
            for (V, pd, odd, ot), cnt in PROF_II[(c2, s)].items():
                g2.setdefault((V, pd), []).append((s, odd, ot, cnt))
        for (V1, pd1), lst1 in g1.items():
            for (V2, pd2), lst2 in g2.items():
                Wstd = frozenset((V2 if pd1 else frozenset()) | (V1 if pd2 else frozenset()))
                for (s1, odd1, ot1, n1) in lst1:
                    for (s2, odd2, ot2, n2) in lst2:
                        tot = s1 + s2
                        if tot not in (4, 7, 10, 13): continue
                        m = 13 - tot
                        fs = fam_stats(S, m)
                        osum = odd1 + odd2
                        if Wstd:
                            noch = (fs["has_odd_ge1"] if osum == 1 else fs["odd_not1"] if osum == 0 else True)
                            if noch: add_class(Wstd, ("II", (c1, c2), (s1, s2), None, n1*n2))
                        zs = []
                        if osum == 1 and fs["zero_odd"]:
                            z = ot1 if odd1 == 1 else ot2
                            if z is not None: zs.append(z)
                        elif osum == 0:
                            zs = sorted(fs["odd1"])
                        for z in zs:
                            add_class(frozenset(Wstd | {z}), ("II", (c1, c2), (s1, s2), z, n1*n2))
log("Type II 后类数: %d" % len(classes))

# ------------- 纯七对子(Wstd=∅)
for c in range(4):
    S = tuple(x for x in range(4) if x != c)
    for s in SIZES_I:
        m = 13 - s
        fs = fam_stats(S, m)
        for (Wp, odd, ot), cnt in PROF_I[(c, s)].items():
            if Wp: continue
            if odd == 1 and fs["zero_odd"] and ot is not None:
                add_class(frozenset([ot]), ("I-chionly", c, s, ot, cnt))
            elif odd == 0:
                for z in sorted(fs["odd1"]):
                    add_class(frozenset([z]), ("I-chionly", c, s, z, cnt))
for c1 in range(4):
    for c2 in range(c1+1, 4):
        S = tuple(x for x in range(4) if x not in (c1, c2))
        g1 = {}
        for s in SIZES_II:
            for (V, pd, odd, ot), cnt in PROF_II[(c1, s)].items():
                g1.setdefault((V, pd), []).append((s, odd, ot, cnt))
        g2 = {}
        for s in SIZES_II:
            for (V, pd, odd, ot), cnt in PROF_II[(c2, s)].items():
                g2.setdefault((V, pd), []).append((s, odd, ot, cnt))
        for (V1, pd1), lst1 in g1.items():
            for (V2, pd2), lst2 in g2.items():
                Wstd = frozenset((V2 if pd1 else frozenset()) | (V1 if pd2 else frozenset()))
                if Wstd: continue
                for (s1, odd1, ot1, n1) in lst1:
                    for (s2, odd2, ot2, n2) in lst2:
                        tot = s1 + s2
                        if tot not in (4, 7, 10, 13): continue
                        m = 13 - tot
                        fs = fam_stats(S, m)
                        osum = odd1 + odd2
                        if osum == 1 and fs["zero_odd"]:
                            z = ot1 if odd1 == 1 else ot2
                            if z is not None: add_class(frozenset([z]), ("II-chionly", (c1, c2), (s1, s2), z, n1*n2))
                        elif osum == 0:
                            for z in sorted(fs["odd1"]):
                                add_class(frozenset([z]), ("II-chionly", (c1, c2), (s1, s2), z, n1*n2))
log("含纯七对子后类数: %d" % len(classes))

# ------------- 国士
KOK = frozenset(KOKUSHI_TILES)
add_class(KOK, ("kokushi13",))
for t in KOKUSHI_TILES:
    add_class(KOK - {t}, ("kokushi12", t))
log("含国士后类数: %d" % len(classes))

# ------------- 统计
size_dist = {}
for W in classes: size_dist[len(W)] = size_dist.get(len(W), 0) + 1
nsrc = sorted(len(v) for v in classes.values())
buckets = {"1": 0, "2-5": 0, "6-20": 0, "21-100": 0, "101-1000": 0, ">1000": 0}
for x in nsrc:
    b = "1" if x == 1 else "2-5" if x <= 5 else "6-20" if x <= 20 else "21-100" if x <= 100 else "101-1000" if x <= 1000 else ">1000"
    buckets[b] += 1
res = {"classes": len(classes), "size_dist": dict(sorted(size_dist.items())),
       "source_buckets": buckets, "max_sources": nsrc[-1] if nsrc else 0,
       "sum_sources": sum(nsrc),
       "budgets": {"34^1": 34, "34^2": 34**2, "34^3": 34**3, "34^4": 34**4, "34^5": 34**5},
       "singleton_classes": len([W for W in classes if len(W) == 1])}
log("类大小分布 |W|:", res["size_dist"])
log("来源数分布:", buckets, " max=%d sum=%d" % (res["max_sources"], res["sum_sources"]))
log("预算: 34^2=%d 34^3=%d 34^4=%d 34^5=%d" % (34**2, 34**3, 34**4, 34**5))
log("==> 类数 %d ; k=4 预算 %d ; k=3 预算 %d" % (len(classes), 34**4, 34**3))
json.dump(res, open(os.path.join(OUT, "census_stats.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# 保存类表(W -> 来源), 供构造阶段使用（紧凑字符串）
def src_str(s):
    return "|".join(str(x) for x in s)
with open(os.path.join(OUT, "classes.tsv"), "w", encoding="utf-8") as f:
    for W in sorted(classes, key=lambda w: (len(w), tuple(sorted(w)))):
        f.write(",".join(map(str, sorted(W))) + "\t" + ";".join(src_str(s) for s in classes[W]) + "\n")
log("写 classes.tsv 完成 (%d 类)" % len(classes))
