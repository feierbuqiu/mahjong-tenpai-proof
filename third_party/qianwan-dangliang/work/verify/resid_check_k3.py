#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""resid_check_k3.py <plan_k3.json> -- k=3 定向残余复验: (a) Type I 块 (b) chiitoi 抽样 (c) 结构化模拟."""
import json, sys, os, random, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from indep_core import closed_form_W, compute_W, gen_vectors, melds_only, melds_only_honor, CAP, KOKUSHI_IDX
HON = {"E": 27, "S": 28, "W": 29, "N": 30, "Haku": 31, "Hatsu": 32, "Chun": 33}
HONN = ["E", "S", "W", "N", "Haku", "Hatsu", "Chun"]
NM = lambda t: ("%d%s" % (t % 9 + 1, "mps"[t // 9])) if t < 27 else HONN[t - 27]
def to_idx(w):
    if isinstance(w, int): return [t for t in range(34) if (w >> t) & 1]
    out = []
    for nm in w:
        if isinstance(nm, int): out.append(nm)
        elif nm in HON: out.append(HON[nm])
        else: out.append("mps".index(nm[-1]) * 9 + int(nm[0]) - 1)
    return out
PLAN = sys.argv[1] if len(sys.argv) > 1 else "work/strategy/out/plan_k3.json"
P = json.load(open(PLAN, encoding="utf-8"))
rows = P["plan"] if isinstance(P, dict) and "plan" in P else P
plancls = {}
for r in rows:
    W = frozenset(to_idx(r["W"]))
    plancls.setdefault(W, []).extend(tuple(c) for c in r["codes"])
KCODE = len(rows[0]["codes"][0]) if rows and rows[0]["codes"] else 3
print("plan:", PLAN, "classes:", len(plancls), "code length:", KCODE)
def contains(h, c):
    need = {}
    for t in c: need[t] = need.get(t, 0) + 1
    return all(h[t] >= v for t, v in need.items())
SU = {"m": 0, "p": 1, "s": 2, "z": 3}
DEC = {}
def dec_vecs(ci, s):
    k = (ci, s)
    if k in DEC: return DEC[k]
    K = (9, 9, 9, 7)[ci]; hon = ci == 3; off = (0, 9, 18, 27)[ci]
    out = []
    for v in gen_vectors(K, s):
        if (melds_only_honor(v) if hon else melds_only(v)):
            u = [0] * 34
            for i, x in enumerate(v):
                if x: u[off + i] = x
            out.append(tuple(u))
    DEC[k] = out; return out
def parse(ds, ci):
    off = (0, 9, 18, 27)[ci]; u = [0] * 34
    for i, ch in enumerate(ds):
        if ch != "0": u[off + i] = int(ch)
    return u
def covered(A, inert, m, codes):
    if any(contains(A, c) for c in codes): return True
    ii = [SU[x] for x in inert]
    def rec(i, rem, hand):
        for c in codes:
            if contains(hand, c): return True
        if i == len(ii): return rem != 0
        ci = ii[i]
        for s in range(0, rem + 1, 3):
            if (rem - s) > 12 * (len(ii) - i - 1): continue
            for v in dec_vecs(ci, s):
                h2 = list(hand)
                for t, x in enumerate(v): h2[t] += x
                if not rec(i + 1, rem - s, h2): return False
        return True
    return rec(0, m, list(A))
# (a) Type I
g = json.load(open("work/data/out/global.json", encoding="utf-8"))
tot = unc = 0; bad = []; hard = 0
for row in g["classes"]:
    W = frozenset(to_idx(row["W"]))
    if W not in plancls: continue
    if any(s["kind"] == "kokushi" for s in row.get("sources", [])): continue
    codes = plancls[W]
    for s in row.get("sources", []):
        if s["kind"] != "I": continue
        tot += 1
        ci = SU[s["cat"]]; A = parse(s["A"], ci); m = 13 - sum(A)
        if not covered(A, s["inert"], m, codes):
            unc += 1
            if len(bad) < 8: bad.append({"W": row["W"], "A": s["A"], "cat": s["cat"], "m": m})
print("(a) TypeI blocks", tot, "uncovered", unc)
for b in bad: print("    ", b)
# (b) chiitoi 手牌级 + k=3 参照族 {(z,a,a)}
rng = random.Random(2026)
cf = 0; zc = 0; ref_ok = 0; ex = []
for _ in range(200000):
    z = rng.randrange(34); Kk = rng.sample([t for t in range(34) if t != z], 6)
    hand = [0] * 34
    for t in Kk: hand[t] = 2
    hand[z] = 1
    W = closed_form_W(hand)
    if not W: continue
    cs = plancls.get(W)
    if not cs: zc += 1; continue
    if not any(contains(hand, c) for c in cs):
        cf += 1
        if any(contains(hand, (z, a, a)) for a in Kk): ref_ok += 1
        if len(ex) < 5: ex.append({"W": [NM(t) for t in sorted(W)], "hand": [NM(i) for i in range(34) for _ in range(hand[i])]})
print("(b) chiitoi samples fail:", cf, "zero-code:", zc, " (of the sampled fails, 参照族 {(z,a,a)} 本可命中的手数:", ref_ok, ")")
for e in ex: print("    ", e)
# (c) 结构化模拟
CATS = ((9, 0), (9, 9), (9, 18), (7, 27))
def rand_hand():
    t = rng.random(); hand = [0] * 34
    def rv(ci, n):
        K, _ = CATS[ci]; c = [0] * K
        for _ in range(n):
            while True:
                x = rng.randrange(K)
                if c[x] < CAP: c[x] += 1; break
        return c
    if t < 0.3:
        ci = rng.randrange(4); n = rng.choice([1, 4, 7, 10, 13]); X = rv(ci, n)
        for i, x in enumerate(X): hand[CATS[ci][1] + i] += x
        cats = [c for c in range(4) if c != ci]; rem = 13 - n
        for idx, cj in enumerate(cats):
            left = len(cats) - idx - 1
            s = rng.choice([s for s in range(0, rem + 1, 3) if rem - s <= 12 * left and (s == 0 or dec_vecs(cj, s))])
            if s:
                v = rng.choice(dec_vecs(cj, s))
                for i, x in enumerate(v): hand[i] += x
            rem -= s
    elif t < 0.75:
        c1, c2 = rng.sample(range(4), 2)
        n1 = rng.choice([2, 5, 8, 11]); n2 = rng.choice([2, 5, 8, 11])
        if n1 + n2 > 13: n1, n2 = 2, 2
        for cc, nn in ((c1, n1), (c2, n2)):
            X = rv(cc, nn)
            for i, x in enumerate(X): hand[CATS[cc][1] + i] += x
        cats = [c for c in range(4) if c not in (c1, c2)]; rem = 13 - n1 - n2
        for idx, cj in enumerate(cats):
            left = len(cats) - idx - 1
            s = rng.choice([s for s in range(0, rem + 1, 3) if rem - s <= 12 * left and (s == 0 or dec_vecs(cj, s))])
            if s:
                v = rng.choice(dec_vecs(cj, s))
                for i, x in enumerate(v): hand[i] += x
            rem -= s
    elif t < 0.92:
        kinds = rng.sample(range(34), 7); z = rng.choice(kinds)
        for kk in kinds: hand[kk] = 2
        hand[z] = 1
    elif t < 0.96:
        ks = rng.sample(KOKUSHI_IDX, 12)
        for kk in ks: hand[kk] = 1
        hand[rng.choice(ks)] += 1
    else:
        for _ in range(13):
            while True:
                x = rng.randrange(34)
                if hand[x] < CAP: hand[x] += 1; break
    return hand
cf2 = 0; ex2 = []; nl = 0; hits = set(); bf = 0; bf_bad = 0
for it in range(300000):
    h = rand_hand(); W = closed_form_W(h)
    if not W: continue
    nl += 1; hits.add(W)
    cs = plancls.get(W)
    if not cs or not any(contains(h, c) for c in cs):
        cf2 += 1
        if len(ex2) < 5: ex2.append({"W": [NM(t) for t in sorted(W)], "hand": [NM(i) for i in range(34) for _ in range(h[i])]})
    if it % 2000 == 0:
        b = compute_W(h); bf += 1
        if b != W: bf_bad += 1
print("(c) sim listening", nl, "classes_hit", len(hits), "coverage-fail", cf2, "| brute-force W 抽检", bf, "失配", bf_bad)
for e in ex2: print("    ", e)
