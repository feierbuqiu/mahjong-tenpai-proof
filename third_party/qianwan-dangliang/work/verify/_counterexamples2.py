
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
NM = lambda t: ("%d%s" % (t%9+1, "mps"[t//9])) if t < 27 else ["E","S","W","N","Haku","Hatsu","Chun"][t-27]

hand_m = [4,4,3,0,2,0,0,0,0]
c = [0]*34
for i,x in enumerate(hand_m): c[i]=x
W = compute_W(c)
print("CASE1 hand(m):", [NM(i) for i in range(9) for _ in range(hand_m[i])])
print("  W(brute) =", [NM(t) for t in sorted(W)])
print("  plan codes =", [[NM(t) for t in code] for code in plancls.get(frozenset(W), [])])
print("  any code subset of hand?", any(contains(c, code) for code in plancls.get(frozenset(W), [])))
g = json.load(open("work/data/out/global.json", encoding="utf-8"))
def ci_ok(z, codes):
    zc = [cc for cc in codes if cc.count(z) <= 1 and all(cc.count(t) <= 2 for t in set(cc) if t != z)]
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
shown=0
for key, lst in g["chiitoi_descriptors"].items():
    for d in lst:
        z = to_idx([d["z"]])[0]
        Wc = frozenset(set(to_idx(d["Wstd"])) | {z})
        codes = plancls.get(Wc)
        if not codes: continue
        okk, wit = ci_ok(z, codes)
        if not okk and wit is not None:
            hand=[0]*34
            for t in wit: hand[t]=2
            hand[z]=1
            Wb = compute_W(hand)
            print("CASE2 chiitoi: z=", NM(z), " 6 pairs:", [NM(t) for t in wit], " plan codes:", [[NM(t) for t in cc] for cc in codes])
            print("   W(brute)=", [NM(t) for t in sorted(Wb)], " class=", [NM(t) for t in sorted(Wc)], " same?", Wb==Wc)
            print("   any code subset?", any(contains(hand, cc) for cc in codes))
            shown+=1; break
    if shown>=2: break
