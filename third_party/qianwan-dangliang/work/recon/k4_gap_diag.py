# -*- coding: utf-8 -*-
"""k4_gap_diag.py -- 对 155 个未覆盖块，检查其候选 4-多重集是否还有空闲排列（Lead）"""
import json, os, sys, collections, math, itertools
HERE = os.path.dirname(os.path.abspath(__file__))
HONN = ["E","S","W","N","Haku","Hatsu","Chun"]
def ti(s): return 27 + HONN.index(s) if s in HONN else "mps".index(s[-1])*9 + int(s[0]) - 1
SU = {"m":0,"p":1,"s":2,"z":3}; BASE=[0,9,18,27]
FACT=[math.factorial(i) for i in range(5)]
def p4(mu):
    c = collections.Counter(mu); return 24 // math.prod(FACT[v] for v in c.values())
P = json.load(open(sys.argv[1] if len(sys.argv)>1 else 'work/verify/plan_k4_permfix.json', encoding='utf-8'))
rows = P["plan"]
plancls = {frozenset((x if isinstance(x,int) else ti(x)) for x in r["W"]): [tuple(c) for c in r["codes"]] for r in rows}
usage = collections.Counter()
for W, cs in plancls.items():
    for c in cs:
        usage[tuple(sorted(c))] += 1
bad = json.load(open(os.path.join(HERE, 'k4_gap_blocks.json'), encoding='utf-8'))
print("gaps:", len(bad))
def parse(ds, ci):
    off = BASE[ci]; v=[0]*34
    for i,ch in enumerate(ds):
        if ch!='0': v[off+i]=int(ch)
    return v
def subs4(A):
    tiles=[]
    for t,c in enumerate(A):
        for _ in range(c): tiles.append(t)
    out=set()
    n=len(tiles)
    for a in range(n):
        for b in range(a,n):
            for c_ in range(b,n):
                for d in range(c_,n): out.add(tuple(sorted((tiles[a],tiles[b],tiles[c_],tiles[d]))))
    return out
res=[]
for g in bad:
    W = frozenset(ti(x) for x in g["W"]); ci = SU[g["cat"]]; A = parse(g["A"], ci)
    have = set(plancls.get(W, []))
    cands = subs4(A)
    free = sum(max(0, p4(mu) - usage[mu]) for mu in cands if mu not in have)
    inc  = sum(1 for mu in cands if mu in have)
    res.append((free, inc, len(cands), g["W"], g["A"], g["cat"], g["m"]))
res.sort()
print("free-slot distribution (free, incover, #cands):")
for r in res[:20]: print("   ", r)
print("blocks with 0 free slots:", sum(1 for r in res if r[0]==0))
print("blocks with >=1 free:", sum(1 for r in res if r[0]>0))
import statistics
print("median free=%.1f mean=%.1f max=%d" % (statistics.median([r[0] for r in res]), statistics.mean([r[0] for r in res]), max(r[0] for r in res)))
