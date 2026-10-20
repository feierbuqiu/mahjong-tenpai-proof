
import json, sys, itertools
sys.path.insert(0, "work/verify")
from indep_core import compute_W
HON = {"E": 27, "S": 28, "W": 29, "N": 30, "Haku": 31, "Hatsu": 32, "Chun": 33}
def to_idx(w):
    if isinstance(w, int): return [t for t in range(34) if (w >> t) & 1]
    out=[]
    for nm in w:
        if isinstance(nm, int): out.append(nm)
        elif nm in HON: out.append(HON[nm])
        else: out.append("mps".index(nm[-1])*9 + int(nm[0]) - 1)
    return out
plan = json.load(open("work/recon/lead_plan_k3_v5.json", encoding="utf-8"))
plancls = {frozenset(to_idx(r["W"])): [tuple(c) for c in r["codes"]] for r in plan["plan"]}
def contains(h, c):
    need={}
    for t in c: need[t]=need.get(t,0)+1
    return all(h[t]>=v for t,v in need.items())

# --- 反例 1: m 覆盖缺口 (W=[2,4], hand [4,4,3,0,2,0,0,0,0]) ---
hand_m = [4,4,3,0,2,0,0,0,0]
c = [0]*34
for i,x in enumerate(hand_m): c[i]=x
W = compute_W(c)
print("hand_m W(brute force) =", sorted(W), " 计划类码 =", plancls.get(frozenset(W)))
print("  任何码 ⊆ 手牌?", any(contains(c, code) for code in plancls.get(frozenset(W), [])))

# --- 反例 2: chiitoi 缺口 ---
g = json.load(open("work/data/out/global.json", encoding="utf-8"))
def ci_ok(z, codes):
    zc = [c for c in codes if c.count(z) <= 1 and all(c.count(t) <= 2 for t in set(c) if t != z)]
    single=set(); hyper=[]
    for cc in zc:
        R=frozenset(t for t in cc if t!=z)
        if not R: return True, None
        if len(R)==1: single|=R
        else: hyper.append(R)
    allowed=[t for t in range(34) if t!=z and t not in single]
    found=[]
    def rec(s,K):
        if found: return
        if len(K)==6:
            Ks=set(K)
            if all(not (R<=Ks) for R in hyper): found.append(list(K))
            return
        if len(allowed)-s < 6-len(K): return
        for i in range(s,len(allowed)):
            K.append(allowed[i]); rec(i+1,K); K.pop()
            if found: return
    rec(0,[])
    return (not found), (found[0] if found else None)
shown = 0
for key, lst in g["chiitoi_descriptors"].items():
    for d in lst:
        z = to_idx([d["z"]])[0]
        Wc = frozenset(set(to_idx(d["Wstd"])) | {z})
        codes = plancls.get(Wc)
        if not codes: continue
        okk, wit = ci_ok(z, codes)
        if not okk and wit is not None:
            hand = [0]*34
            for t in wit: hand[t]=2
            hand[z]=1
            Wb = compute_W(hand)
            print("chiitoi counterexample: z=", z, "K=", wit, " code list=", codes)
            print("   hand counts:", hand)
            print("   W(brute force) =", sorted(Wb), " class key =", sorted(Wc), " 一致?", Wb==Wc)
            print("   任何码 ⊆ 手牌?", any(contains(hand, code) for code in codes))
            shown += 1
            break
    if shown >= 2: break
