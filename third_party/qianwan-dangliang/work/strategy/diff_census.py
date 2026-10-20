# -*- coding: utf-8 -*-
"""diff_census.py -- 两套全局类普查交叉核对 + 手牌级见证验证(ground truth: waits13)。

my_impl  : census.py 的规则(每条规则的 no-chi/chi 条件都已正确处理)
lead_impl: work/recon/recon_global2.py 的规则(无条件加 Wp; 用于对拍)
对每个"只在一侧出现"的类, 用其来源构造见证手牌 H, 用 waits13(H) 判定谁对。
"""
import sys, os, json, itertools, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjlib import *
T0 = time.time()
def log(*a): print("[%6.1fs]" % (time.time()-T0), *a, flush=True)

CAP = 4
SIZES_I = (1, 4, 7, 10, 13)
SIZES_II = (2, 5, 8, 11)
LC = ((9, False), (9, False), (9, False), (7, True))

def seg_melds(size, length, honors):
    res = []
    for combo in itertools.combinations_with_replacement(range(length), size):
        c = [0]*length
        for x in combo: c[x] += 1
        if max(c) <= CAP and can_melds(tuple(c), honors): res.append(tuple(c))
    return res
MELFAM = {k: {s: (seg_melds(s, k[0], k[1]) if s else [tuple([0]*k[0])]) for s in (0,3,6,9,12)} for k in ((9,False),(7,True))}

FCACHE = {}
def fam_list(cats, m):
    """枚举全部 F (每类张数≡0 mod 3, 总和 m, 每类可拆面子, cap4)"""
    key = (tuple(cats), m)
    if key in FCACHE: return FCACHE[key]
    out = []
    def rec(i, rem, acc):
        if i == len(cats):
            if rem == 0: out.append(tuple(acc))
            return
        ci = cats[i]; L = CAT_LEN[ci]; base = CAT_BASE[ci]
        for sd in (0,3,6,9,12):
            if sd > rem: break
            for v in MELFAM[(L, ci==3)][sd]:
                nxt = list(acc)
                for j,x in enumerate(v): nxt[base+j] += x
                rec(i+1, rem-sd, nxt)
    rec(0, m, [0]*34)
    FCACHE[key] = out
    return out

def fam_stats(cats, m):
    lst = fam_list(cats, m)
    zero = any(sum(1 for x in f if x % 2) == 0 for f in lst)
    odd1 = set()
    two = False
    for f in lst:
        ot = [i for i,x in enumerate(f) if x % 2]
        if len(ot) == 1: odd1.add(ot[0])
        elif len(ot) >= 2: two = True
    return {"lst": lst, "zero_odd": zero, "odd1": odd1,
            "has_odd_ge1": bool(odd1) or two, "odd_not1": zero or two}

def pick_F(cats, m, need):
    """need: ('zero',) | ('nonzero',) | ('not1',) | ('odd1', z) | ('any',)"""
    fs = fam_stats(cats, m)
    for f in fs["lst"]:
        ot = [i for i,x in enumerate(f) if x % 2]
        if need[0] == "zero" and len(ot) == 0: return f
        if need[0] == "nonzero" and len(ot) != 0: return f
        if need[0] == "not1" and len(ot) != 1: return f
        if need[0] == "odd1" and len(ot) == 1 and ot[0] == need[1]: return f
        if need[0] == "any": return f
    return None

def x_profile(c, X):
    L = CAT_LEN[c]; h = (c == 3)
    Wp = set(); V = set()
    for t in range(L):
        if X[t] < CAP:
            d = list(X); d[t] += 1
            for pi in range(L):
                if d[pi] >= 2:
                    e = list(d); e[pi] -= 2
                    if can_melds(tuple(e), h): Wp.add(CAT_BASE[c]+t); break
            if can_melds(tuple(d), h): V.add(CAT_BASE[c]+t)
    pd = False
    for pi in range(L):
        if X[pi] >= 2:
            e = list(X); e[pi] -= 2
            if can_melds(tuple(e), h): pd = True; break
    ot = [i for i,x in enumerate(X) if x % 2]
    return (frozenset(CAT_BASE[c]+t for t in Wp), frozenset(CAT_BASE[c]+t for t in V), pd,
            len(ot), (CAT_BASE[c]+ot[0]) if len(ot)==1 else None)

def all_vectors(c, size):
    L = CAT_LEN[c]
    for combo in itertools.combinations_with_replacement(range(L), size):
        v = [0]*L
        for x in combo: v[x] += 1
        if max(v) <= CAP: yield tuple(v)

# ---------- 收集: 每个类 -> 来源(witness 参数)
def build(impl):
    CLS = {}
    def add(W, src):
        if not W: return
        CLS.setdefault(frozenset(W), []).append(src)
    # Type I
    for c in range(4):
        S = tuple(x for x in range(4) if x != c)
        for s in SIZES_I:
            m = 13-s
            for X in all_vectors(c, s):
                Wp, V, pd, odd, ot = x_profile(c, X)
                if impl == "mine":
                    fs = fam_stats(S, m)
                    if Wp:
                        noch = fs["has_odd_ge1"] if odd == 1 else fs["odd_not1"] if odd == 0 else True
                        if noch: add(Wp, ("I", c, X, "nochi", None))
                    if odd == 1 and fs["zero_odd"] and ot is not None:
                        add(Wp | {ot}, ("I", c, X, "chi", ot))
                    elif odd == 0:
                        for z in sorted(fs["odd1"]): add(Wp | {z}, ("I", c, X, "chi", z))
                else:
                    fs = fam_stats(S, m)
                    if Wp: add(Wp, ("I", c, X, "nochi", None))
                    if odd == 1 and fs["zero_odd"] and Wp: add(Wp | {ot}, ("I", c, X, "chi", ot))
                    elif odd == 1 and fs["zero_odd"] and not Wp: add(frozenset([ot]), ("I", c, X, "chi", ot))
                    if odd == 0:
                        for z in sorted(fs["odd1"]): add(Wp | {z}, ("I", c, X, "chi", z))
    # Type II
    for c1 in range(4):
        for c2 in range(c1+1, 4):
            S = tuple(x for x in range(4) if x not in (c1,c2))
            for s1 in SIZES_II:
                for X1 in all_vectors(c1, s1):
                    V1, Wp1, pd1, odd1, ot1 = x_profile(c1, X1)
                    for s2 in SIZES_II:
                        tot = s1+s2
                        if tot not in (4,7,10,13): continue
                        m = 13-tot
                        fs = fam_stats(S, m)
                        for X2 in all_vectors(c2, s2):
                            V2, Wp2, pd2, odd2, ot2 = x_profile(c2, X2)
                            Wstd = (V2 if pd1 else frozenset()) | (V1 if pd2 else frozenset())
                            osum = odd1+odd2
                            if impl == "mine":
                                if Wstd:
                                    noch = fs["has_odd_ge1"] if osum==1 else fs["odd_not1"] if osum==0 else True
                                    if noch: add(Wstd, ("II",(c1,X1),(c2,X2),"nochi",None))
                            else:
                                if Wstd: add(Wstd, ("II",(c1,X1),(c2,X2),"nochi",None))
                            if osum == 1 and fs["zero_odd"]:
                                z = ot1 if odd1==1 else ot2
                                if z is not None: add(Wstd | {z}, ("II",(c1,X1),(c2,X2),"chi",z))
                            elif osum == 0:
                                for z in sorted(fs["odd1"]): add(Wstd | {z}, ("II",(c1,X1),(c2,X2),"chi",z))
    for z in range(34): add(frozenset([z]), ("chionly", z))
    term = frozenset(KOKUSHI_TILES)
    add(term, ("kokushi13", None))
    for t in KOKUSHI_TILES: add(term-{t}, ("kokushi12", t))
    return CLS

def verify(src):
    kind = src[0]
    if kind == "kokushi13":
        H = [0]*34
        for t in KOKUSHI_TILES: H[t] += 1
        return waits13(tuple(H))
    if kind == "kokushi12":
        t = src[1]; H = [0]*34
        for x in KOKUSHI_TILES: H[x] += 1
        H[t] += 1
        return waits13(tuple(H))
    if kind == "chionly":
        return None
    if kind == "I":
        _, c, X, mode, z = src
        S = tuple(x for x in range(4) if x != c)
        m = 13 - sum(X)
        Wp, V, pd, odd, ot = x_profile(c, X)
        if mode == "nochi":
            need = ("nonzero",) if odd == 1 else ("not1",) if odd == 0 else ("any",)
        else:
            need = ("zero",) if odd == 1 else ("odd1", z)
        F = pick_F(S, m, need)
        if F is None: return None
        H = list(X); H = [0]*9 + [0]*0
        H = [0]*34
        for i, x in enumerate(X):
            if i < CAT_LEN[c]: H[CAT_BASE[c]+i] = x
        for i in range(34): H[i] += F[i]
        return waits13(tuple(H))
    if kind == "II":
        _, (c1, X1), (c2, X2), mode, z = src
        S = tuple(x for x in range(4) if x not in (c1,c2))
        m = 13 - sum(X1) - sum(X2)
        V1, Wp1, pd1, odd1, ot1 = x_profile(c1, X1)
        V2, Wp2, pd2, odd2, ot2 = x_profile(c2, X2)
        osum = odd1+odd2
        if mode == "nochi":
            need = ("nonzero",) if osum == 1 else ("not1",) if osum == 0 else ("any",)
        else:
            need = ("zero",) if osum == 1 else ("odd1", z)
        F = pick_F(S, m, need)
        if F is None: return None
        H = [0]*34
        for i, x in enumerate(X1): H[CAT_BASE[c1]+i] = x
        for i, x in enumerate(X2): H[CAT_BASE[c2]+i] = x
        for i in range(34): H[i] += F[i]
        return waits13(tuple(H))
    return None

MY = build("mine"); LD = build("lead")
log("my classes=%d  lead classes=%d" % (len(MY), len(LD)))
only_my = sorted(set(MY) - set(LD), key=lambda w: (len(w), tuple(sorted(w))))
only_ld = sorted(set(LD) - set(MY), key=lambda w: (len(w), tuple(sorted(w))))
log("only_my=%d  only_lead=%d" % (len(only_my), len(only_ld)))

def check(cls_list, tag, limit=12):
    good = bad = unknown = 0
    examples = []
    for W in cls_list:
        ok = False; unk = False
        for src in MY.get(W, []) if tag == "my" else LD.get(W, []):
            Wt = verify(src)
            if Wt is None: unk = True; continue
            if Wt == W: ok = True; break
        if ok: good += 1
        elif unk: unknown += 1
        else: bad += 1
        if len(examples) < limit:
            examples.append((sorted(tile_name(t) for t in W), "OK" if ok else ("UNK" if unk else "BAD")))
    log("  [%s] verified_ok=%d bad=%d unknown=%d" % (tag, good, bad, unknown))
    for e in examples: log("     %s -> %s" % (e[0], e[1]))
    return good, bad, unknown

log("== 只在我这侧出现的类(k=见上), 用其来源验证 ==")
check(only_my, "my")
log("== 只在 lead 侧出现的类 ==")
check(only_ld, "lead")
json.dump({"my": len(MY), "lead": len(LD), "only_my": len(only_my), "only_lead": len(only_ld),
           "only_my_sample": [sorted(W) for W in only_my[:50]],
           "only_lead_sample": [sorted(W) for W in only_ld[:50]]},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "diff_census.json"), "w"))
log("完成")
