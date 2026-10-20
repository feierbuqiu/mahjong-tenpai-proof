
import json, sys, itertools
sys.path.insert(0, "work/verify")
from indep_core import melds_only, melds_only_honor, gen_vectors
HON = {"E": 27, "S": 28, "W": 29, "N": 30, "Haku": 31, "Hatsu": 32, "Chun": 33}
def to_idx(w):
    if isinstance(w, int): return [t for t in range(34) if (w >> t) & 1]
    out=[]
    for nm in w:
        if isinstance(nm, int): out.append(nm)
        elif nm in HON: out.append(HON[nm])
        else: out.append("mps".index(nm[-1])*9 + int(nm[0]) - 1)
    return out
P = json.load(open("work/recon/plan_k4_u14.json", encoding="utf-8"))
rows = P["plan"]
print("row0 W:", rows[0]["W"], " codelen:", len(rows[0]["codes"]) if rows[0]["codes"] else 0)
# how many rows have W == ['2m'] ?
sel = [r for r in rows if to_idx(r["W"]) == [1]]
print("rows with W=[2m]:", len(sel), " codes:", [len(r["codes"]) for r in sel])
codes = [tuple(c) for r in sel for c in r["codes"]]
print("distinct codes for class {2m}:", len(set(codes)), "sample:", codes[:5])
A = [0]*34
for i,ch in enumerate("101200000"):
    if ch!="0": A[i]=int(ch)
print("A counts m:", [A[i] for i in range(9)], "|A|=", sum(A))
# F: p(6 tiles)+s(3 tiles) with m=9? inert = p,s,z each ≡0 mod3 summing 9
def dec(ci, s):
    K=(9,9,9,7)[ci]; hon=ci==3; off=(0,9,18,27)[ci]
    out=[]
    for v in gen_vectors(K,s):
        if (melds_only_honor(v) if hon else melds_only(v)):
            u=[0]*34
            for i,x in enumerate(v):
                if x: u[off+i]=x
            out.append(tuple(u))
    return out
def contains(h,c):
    need={}
    for t in c: need[t]=need.get(t,0)+1
    return all(h[t]>=v for t,v in need.items())
uncovered = 0; total = 0
for a in (0,3,6,9):      # p
    for b in (0,3,6,9):
        if a+b>9: continue
        c_ = 9-a-b
        if c_ % 3: continue
        for vp in dec(1,a):
            for vs in dec(2,b):
                for vz in dec(3,c_):
                    F=[0]*34
                    for t,x in enumerate(vp): F[t]+=x
                    for t,x in enumerate(vs): F[t]+=x
                    for t,x in enumerate(vz): F[t]+=x
                    H=[A[i]+F[i] for i in range(34)]
                    total += 1
                    if not any(contains(H,cc) for cc in codes): uncovered += 1
print("block A=101200000: F total", total, " uncovered F", uncovered)
