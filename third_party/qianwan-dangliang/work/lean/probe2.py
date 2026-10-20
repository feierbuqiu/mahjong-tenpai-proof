# -*- coding: utf-8 -*-
"""work/lean/probe2.py -- coverage analysis of plan_k4_FINAL against the block base forms."""
import sys, pickle, json, time
sys.path.insert(0, r'D:\DSH\MJ2\work\strategy'); sys.path.insert(0, r'D:\DSH\MJ2\work\strategy\out')
HON = ["E","S","W","N","Haku","Hatsu","Chun"]
HONI = {n: 27 + i for i, n in enumerate(HON)}
def to_idx(x):
    if isinstance(x, int): return x
    if x in HONI: return HONI[x]
    return "mps".index(x[-1]) * 9 + int(x[0]) - 1
BASE = [0, 9, 18, 27]

P = json.load(open(r'D:\DSH\MJ2\work\verify\plan_k4_FINAL.json', encoding='utf-8'))
plan = {}
for r in P["plan"]:
    W = frozenset(to_idx(x) for x in r["W"])
    plan.setdefault(W, []).extend(tuple(sorted(c)) for c in r["codes"])
print("plan classes:", len(plan), "codes:", sum(len(v) for v in plan.values()))

C = pickle.load(open(r'D:\DSH\MJ2\work\strategy\out\table_cache.pkl','rb'))
cls, PI, PII = C['cls'], C['PROFI_D'], C['PROFII_D']
print("cls classes:", len(cls), " same class set:", set(cls) == set(plan))
cc = [len(v) for v in plan.values()]
cc.sort()
print("codes/class: max", cc[-1], "mean %.2f" % (sum(cc)/len(cc)), "top5", cc[-5:])

# group codes by category, local base-6 encoding
SIX9 = 6**9
def code_local(c, cat):
    off = (cat*9) if cat < 3 else 27
    n = 9 if cat < 3 else 7
    e = 0
    for i in range(n):
        t = off + i
        k = c.count(t)
        if k: e += k * 6**i
    return e
def tile_cat(t): return t//9 if t < 27 else 3

t0 = time.time()
codes_by_cat = {}
for W, cs in plan.items():
    g = {0: [], 1: [], 2: [], 3: []}
    for c in cs:
        cats = set(tile_cat(t) for t in c)
        if len(cats) == 1:
            cat = cats.pop()
            g[cat].append(code_local(c, cat))
    codes_by_cat[W] = g
tot_checks = 0
nI = 0
fail = []
for W, blocks in cls.items():
    g = codes_by_cat.get(W, {0:[],1:[],2:[],3:[]})
    for b in blocks:
        if b[0] != 'I': continue
        key = b[1]; ci = key[0]; e = PI.get(key)
        if not e: continue
        cand = g[ci]
        for X in e[1]:
            nI += 1
            tot_checks += len(cand)
            enc = 0
            for i, v in enumerate(X):
                if v: enc += v * 6**i
            ok = False
            for ce in cand:
                # digitwise <=
                x, y = ce, enc
                good = True
                for _ in range(9):
                    if x % 6 > y % 6: good = False; break
                    x //= 6; y //= 6
                if good: ok = True; break
            if not ok:
                fail.append((sorted(W), ci, X))
print("I units:", nI, " code-comparisons:", tot_checks, " I coverage failures:", len(fail))
print("   examples:", fail[:5])
print("t=%.1fs" % (time.time()-t0))
