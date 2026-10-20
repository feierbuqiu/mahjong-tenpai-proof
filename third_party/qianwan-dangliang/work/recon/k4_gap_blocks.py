# -*- coding: utf-8 -*-
"""k4_gap_blocks.py <plan.json> -- Lead 独立枚举 Type I 未覆盖块（自己的 DFS 实现）"""
import sys, os, json, collections, time
HERE = os.path.dirname(os.path.abspath(__file__))
HONN = ["E","S","W","N","Haku","Hatsu","Chun"]
def ti(s): return 27 + HONN.index(s) if s in HONN else "mps".index(s[-1])*9 + int(s[0]) - 1
SU = {"m":0,"p":1,"s":2,"z":3}
CATLEN = [9,9,9,7]; BASE = [0,9,18,27]
MELDS = {}
for ci in range(4):
    L = CATLEN[ci]; b = BASE[ci]; lst = []
    for i in range(L):
        v = [0]*34; v[b+i] = 3; lst.append(tuple(v))
    if ci < 3:
        for i in range(L-2):
            v = [0]*34
            for j in (i,i+1,i+2): v[b+j] += 1
            lst.append(tuple(v))
    MELDS[ci] = lst
MELDV = {}
for ci in range(4):
    d = {0: [tuple([0]*34)]}
    for s3 in (1,2,3,4):
        out = []
        for combo in __import__('itertools').combinations_with_replacement(range(len(MELDS[ci])), s3):
            v = [0]*34
            for m_ in combo:
                for t in range(34): v[t] += MELDS[ci][m_][t]
            if max(v) <= 4: out.append(tuple(v))
        d[s3*3] = out
    MELDV[ci] = d
def parse(ds, ci):
    off = BASE[ci]; v = [0]*34
    for i,ch in enumerate(ds):
        if ch != '0': v[off+i] = int(ch)
    return v
def contains(h, c):
    for t in set(c):
        if h[t] < c.count(t): return False
    return True
P = json.load(open(sys.argv[1], encoding='utf-8'))
rows = P["plan"] if isinstance(P, dict) and "plan" in P else P
plancls = {frozenset((x if isinstance(x,int) else ti(x)) for x in r["W"]): [tuple(c) for c in r["codes"]] for r in rows}
G = json.load(open('work/data/out/global.json', encoding='utf-8'))

def covered(A, inert, m, codes):
    if any(contains(A, c) for c in codes): return True
    ii = [SU[x] for x in inert]
    def rec(i, rem, hand):
        for c in codes:
            if contains(hand, c): return True
        if i == len(ii): return rem != 0
        ci = ii[i]
        for s in range(0, rem+1, 3):
            if (rem - s) > 12*(len(ii)-i-1): continue
            for V in MELDV[ci][s]:
                h2 = [hand[t]+V[t] for t in range(34)]
                if not rec(i+1, rem-s, h2): return False
        return True
    return rec(0, m, list(A))

t0 = time.time(); bad = []; tot = 0; skipkok = 0
for row in G["classes"]:
    W = frozenset(ti(x) for x in row["W"])
    if W not in plancls: continue
    codes = plancls[W]
    if any(s["kind"] == "kokushi" for s in row.get("sources", [])):
        skipkok += 1; continue
    for s in row.get("sources", []):
        if s["kind"] != "I": continue
        ci = SU[s["cat"]]; A = parse(s["A"], ci); m = 13 - sum(A)
        tot += 1
        if not covered(A, s["inert"], m, codes):
            bad.append({"W": row["W"], "A": s["A"], "cat": s["cat"], "m": m, "ncodes": len(codes)})
            if len(bad) % 25 == 0: print("  ... %d bad %.0fs" % (len(bad), time.time()-t0), flush=True)
print("TypeI blocks %d uncovered %d (kokushi classes skipped %d) %.0fs" % (tot, len(bad), skipkok, time.time()-t0))
for b in bad[:12]: print("   ", b)
json.dump(bad, open(os.path.join(HERE, 'k4_gap_blocks.json'), 'w'), ensure_ascii=False)
