# -*- coding: utf-8 -*-
"""work/lean/probe10.py -- 用 Python 独立复核 Lean 的前 20,000 个块（严格判据）"""
import sys, os, json, pickle
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "work", "strategy")); sys.path.insert(0, os.path.join(ROOT, "work", "strategy", "out"))
import table_lib as TL

src = open(os.path.join(ROOT, "lean", "Mj", "Data2.lean"), encoding="utf-8").read()
# combos
import re
m = re.search(r'def combos : List \(Nat × Nat × Nat × Nat\) := \[(.*?)\]', src, re.S)
combos = [tuple(int(x) for x in t.split(",")) for t in re.findall(r'\((\d+,\s*\d+,\s*\d+,\s*\d+)\)', m.group(1))]
recs = []
for mm in re.finditer(r'^def blkChunk\d+ : List Nat := \[(.*?)\]$', src, re.M):
    recs += [int(x) for x in mm.group(1).split(",")]
print("combos", len(combos), "blocks", len(recs))
# profTable order per (c,s): 从 Data2 不能直接读 key，改用 table_cache 的 PROFII_D 并按 keyEnc 排序
C = pickle.load(open(os.path.join(ROOT, "work", "strategy", "out", "table_cache.pkl"), "rb"))
cls, PII = C["cls"], C["PROFII_D"]
def key_enc(k):
    V, pd, odd, ot, a2, o2 = k
    mask = 0
    for t in V: mask |= 1 << t
    return (mask + (1 if pd else 0)*2**34 + odd*2**35 + (34 if ot is None else ot)*2**39
            + (1 if a2 else 0)*2**45 + (1 if o2 else 0)*2**46)
grp = {}
for (c,s,k) in PII:
    grp.setdefault((c,s), []).append(k)
for ks in grp.values(): ks.sort(key=key_enc)
# planData order
P = json.load(open(os.path.join(ROOT, "work", "verify", "plan_k4_FINAL.json"), encoding="utf-8"))
HON = ["E","S","W","N","Haku","Hatsu","Chun"]; HONI = {n:27+i for i,n in enumerate(HON)}
def to_idx(x):
    if isinstance(x,int): return x
    if x in HONI: return HONI[x]
    return "mps".index(x[-1])*9+int(x[0])-1
order=[]; seen=set()
for r in P["plan"]:
    W=frozenset(to_idx(x) for x in r["W"])
    if W not in seen: seen.add(W); order.append(W)
plan={}
for r in P["plan"]:
    W=frozenset(to_idx(x) for x in r["W"]); plan.setdefault(W,[]).extend(tuple(c) for c in r["codes"])
def contains(A, code):
    cc={}
    for t in code: cc[t]=cc.get(t,0)+1
    return all(A[t]>=v for t,v in cc.items())
nb=0; failb=0; units=0; failu=0
for rec in recs[:20000]:
    classIdx = rec >> 25
    r1 = rec & ((1<<25)-1)
    comboIdx = r1 >> 18
    r2 = r1 & ((1<<18)-1)
    k1i = r2 >> 9; k2i = r2 & 511
    c1,s1,c2,s2 = combos[comboIdx]
    W = order[classIdx]
    codes = [tuple(c) for c in plan[W] if all((0 if t<27 else 3) in (c1,c2) for t in c)]
    ks1 = grp[(c1,s1)][k1i]; ks2 = grp[(c2,s2)][k2i]
    for X1 in PII[(c1,s1,ks1)][1]:
        for X2 in PII[(c2,s2,ks2)][1]:
            A = [0]*34
            for i,v in enumerate(X1): A[c1*9+i if c1<3 else 27+i] += v
            for i,v in enumerate(X2): A[c2*9+i if c2<3 else 27+i] += v
            units += 1
            if not any(contains(A,c) for c in codes):
                failu += 1
    nb += 1
    if failu and False: pass
print("first 20000 blocks: units", units, "failing units", failu)
# count failing blocks
failb = 0
for rec in recs[:20000]:
    classIdx = rec >> 25; r1 = rec & ((1<<25)-1); comboIdx = r1 >> 18
    r2 = r1 & ((1<<18)-1); k1i = r2 >> 9; k2i = r2 & 511
    c1,s1,c2,s2 = combos[comboIdx]
    W = order[classIdx]
    codes = [tuple(c) for c in plan[W] if all((0 if t<27 else 3) in (c1,c2) for t in c)]
    ks1 = grp[(c1,s1)][k1i]; ks2 = grp[(c2,s2)][k2i]
    bad = False
    for X1 in PII[(c1,s1,ks1)][1]:
        for X2 in PII[(c2,s2,ks2)][1]:
            A=[0]*34
            for i,v in enumerate(X1): A[c1*9+i if c1<3 else 27+i]+=v
            for i,v in enumerate(X2): A[c2*9+i if c2<3 else 27+i]+=v
            if not any(contains(A,c) for c in codes): bad=True; break
        if bad: break
    if bad: failb += 1
print("failing blocks:", failb)
