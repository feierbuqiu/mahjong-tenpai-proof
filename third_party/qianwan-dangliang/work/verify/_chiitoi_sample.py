
import json, sys, random, itertools
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
rng = random.Random(99)
fail = []; zero = 0; n = 0; nobs = 0
for it in range(300000):
    z = rng.randrange(34)
    others = [t for t in range(34) if t != z]
    K = rng.sample(others, 6)
    hand=[0]*34
    for t in K: hand[t]=2
    hand[z]=1
    W = compute_W(hand)
    n += 1
    if not W: nobs += 1; continue
    cs = plancls.get(W)
    if not cs:
        zero += 1
        if len(fail) < 3: fail.append({"kind": "zero-code-class", "W": sorted(W), "hand": hand})
        continue
    if not any(contains(hand, c) for c in cs):
        if len(fail) < 6: fail.append({"kind": "coverage-fail", "W": sorted(W), "hand": hand, "codes": cs})
print("chiitoi hand samples:", n, "listening:", n-nobs, "zero-code-class:", zero, "coverage-fail:", len([f for f in fail if f['kind']=='coverage-fail']))
for f in fail[:4]:
    print(f["kind"], "W=", f["W"], "codes=", f.get("codes"))
