# -*- coding: utf-8 -*-
"""diff_typeI.py -- Type I(单类别主动) 两套实现的对拍 + 见证验证, 并检查 fam 家族数据。"""
import sys, os, json, itertools, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjlib import *
T0 = time.time()
def log(*a): print("[%6.1fs]" % (time.time()-T0), *a, flush=True)
CAP = 4
SIZES_I = (1,4,7,10,13)

def seg_melds(size, length, honors):
    res = []
    for combo in itertools.combinations_with_replacement(range(length), size):
        c = [0]*length
        for x in combo: c[x] += 1
        if max(c) <= CAP and can_melds(tuple(c), honors): res.append(tuple(c))
    return res
MELFAM = {k: {s: (seg_melds(s, k[0], k[1]) if s else [tuple([0]*k[0])]) for s in (0,3,6,9,12)} for k in ((9,False),(7,True))}

def fam_lead(cats, j):
    """复刻 recon_global2.filler_data"""
    items = [(c, v) for c in sorted(cats) for v in
             ([tuple(3 if i==x else 0 for i in range(CAT_LEN[c])) for x in range(CAT_LEN[c])] +
              ([tuple(1 if i in (x,x+1,x+2) else 0 for i in range(CAT_LEN[c])) for x in range(CAT_LEN[c]-2)] if c<3 else []))]
    zero = False; odd1 = set(); seen = set()
    for combo in itertools.combinations_with_replacement(range(len(items)), j):
        per = {}; ok = True
        for idx in combo:
            c, v = items[idx]
            d = per.setdefault(c, [0]*CAT_LEN[c])
            for i, x in enumerate(v):
                d[i] += x
                if d[i] > 4: ok = False; break
            if not ok: break
        if not ok: continue
        sig = tuple(tuple(per.get(c, [0]*CAT_LEN[c])) for c in sorted(cats))
        if sig in seen: continue
        seen.add(sig)
        ot = []
        for c in sorted(cats):
            for i, x in enumerate(per.get(c, [0]*CAT_LEN[c])):
                if x % 2: ot.append(CAT_BASE[c]+i)
        if len(ot) == 0: zero = True
        elif len(ot) == 1: odd1.add(ot[0])
    return {"zero_odd": zero, "odd1": odd1}

def fam_mine(cats, m):
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
                for j, x in enumerate(v): nxt[base+j] += x
                rec(i+1, rem-sd, nxt)
    rec(0, m, [0]*34)
    zero = False; odd1 = set()
    for f in out:
        ot = [i for i,x in enumerate(f) if x % 2]
        if len(ot) == 0: zero = True
        elif len(ot) == 1: odd1.add(ot[0])
    return {"zero_odd": zero, "odd1": odd1, "nfam": len(out)}

log("== (S,m) 家族数据对拍 ==")
for c in range(4):
    S = tuple(x for x in range(4) if x != c)
    for s in SIZES_I:
        m = 13-s; j = m//3
        a = fam_lead(S, j); b = fam_mine(S, m)
        flag = "OK" if (a["zero_odd"] == b["zero_odd"] and a["odd1"] == b["odd1"]) else "**DIFF**"
        log("  c=%d S=%s m=%2d: lead(zero=%s,|odd1|=%d) mine(zero=%s,|odd1|=%d,#fam=%d) %s" % (
            c, S, m, a["zero_odd"], len(a["odd1"]), b["zero_odd"], len(b["odd1"]), b["nfam"], flag))

def all_vectors(c, size):
    L = CAT_LEN[c]
    for combo in itertools.combinations_with_replacement(range(L), size):
        v = [0]*L
        for x in combo: v[x] += 1
        if max(v) <= CAP: yield tuple(v)

def x_profile(c, X):
    L = CAT_LEN[c]; h = (c == 3)
    Wp = set()
    for t in range(L):
        if X[t] < CAP:
            d = list(X); d[t] += 1
            for pi in range(L):
                if d[pi] >= 2:
                    e = list(d); e[pi] -= 2
                    if can_melds(tuple(e), h): Wp.add(CAT_BASE[c]+t); break
    ot = [i for i,x in enumerate(X) if x % 2]
    return (frozenset(Wp), len(ot), (CAT_BASE[c]+ot[0]) if len(ot)==1 else None)

MY = {}; LD = {}
for c in range(4):
    S = tuple(x for x in range(4) if x != c)
    for s in SIZES_I:
        m = 13-s
        fm = fam_mine(S, m); fl = fam_lead(S, m//3)
        for X in all_vectors(c, s):
            Wp, odd, ot = x_profile(c, X)
            # lead
            if Wp: LD.setdefault(Wp, []).append((c, s, X, "nochi", None))
            if odd == 1 and fl["zero_odd"] and ot is not None:
                W = Wp | {ot}
                if Wp or True: LD.setdefault(W, []).append((c, s, X, "chi", ot))
            if odd == 0:
                for z in sorted(fl["odd1"]): LD.setdefault(Wp | {z}, []).append((c, s, X, "chi", z))
            # mine
            if Wp:
                noch = (bool(fm["odd1"]) or False) if odd == 1 else True
                # mine: nochi iff exists F with odd != (1-odd)... 计算:
                noch = (len(fm["odd1"])>0 or fm.get("two_plus", False) or (odd==0 and fm["zero_odd"]) or odd not in (0,1))
                if odd == 1: noch = len(fm["odd1"]) > 0 or fm.get("two_plus", False)
                elif odd == 0: noch = fm["zero_odd"] or fm.get("two_plus", False)
                else: noch = True
                if noch: MY.setdefault(Wp, []).append((c, s, X, "nochi", None))
            if odd == 1 and fm["zero_odd"] and ot is not None:
                MY.setdefault(Wp | {ot}, []).append((c, s, X, "chi", ot))
            elif odd == 0:
                for z in sorted(fm["odd1"]): MY.setdefault(Wp | {z}, []).append((c, s, X, "chi", z))
log("Type I: my=%d lead=%d" % (len(MY), len(LD)))
only_my = sorted(set(MY)-set(LD), key=lambda w:(len(w),tuple(sorted(w))))
only_ld = sorted(set(LD)-set(MY), key=lambda w:(len(w),tuple(sorted(w))))
log("only_my=%d only_lead=%d" % (len(only_my), len(only_ld)))
json.dump({"my": len(MY), "lead": len(LD), "only_my": len(only_my), "only_lead": len(only_ld),
           "only_my_sample": [sorted(W) for W in only_my[:40]],
           "only_lead_sample": [sorted(W) for W in only_ld[:40]]},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "diff_typeI.json"), "w"))
# 展示几个
log("only_my 样例: %s" % [sorted(tile_name(t) for t in W) for W in only_my[:8]])
log("only_lead 样例: %s" % [sorted(tile_name(t) for t in W) for W in only_ld[:8]])
log("按 |W| 分布 only_my: %s ; only_lead: %s" % (
    {k: sum(1 for W in only_my if len(W)==k) for k in sorted({len(W) for W in only_my})},
    {k: sum(1 for W in only_ld if len(W)==k) for k in sorted({len(W) for W in only_ld})}))
