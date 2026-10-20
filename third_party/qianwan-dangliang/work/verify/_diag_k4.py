
import json, sys, collections
sys.path.insert(0, "work/verify")
from indep_core import compute_W, gen_vectors
HON = {"E": 27, "S": 28, "W": 29, "N": 30, "Haku": 31, "Hatsu": 32, "Chun": 33}
def to_idx(w):
    if isinstance(w, int): return [t for t in range(34) if (w >> t) & 1]
    out=[]
    for nm in w:
        if isinstance(nm, int): out.append(nm)
        elif nm in HON: out.append(HON[nm])
        else: out.append("mps".index(nm[-1])*9 + int(nm[0]) - 1)
    return out
plan = json.load(open("work/strategy/out/plan_k4.json", encoding="utf-8"))
plancls = {frozenset(to_idx(r["W"])): [tuple(c) for c in r["codes"]] for r in plan["plan"]}
NM = lambda t: ("%d%s" % (t%9+1, "mps"[t//9])) if t < 27 else ["E","S","W","N","Haku","Hatsu","Chun"][t-27]
for W in (frozenset({0,3}), frozenset({0,3,6}), frozenset({2})):
    cs = plancls.get(W, [])
    print("class", [NM(t) for t in sorted(W)], "n_codes", len(cs))
    print("   codes:", [[NM(t) for t in c] for c in cs][:12])
# 找该类的第一手牌, 看码为何装不进
cnt = 0
for h in gen_vectors(9, 13):
    c=[0]*34
    for i,x in enumerate(h):
        if x: c[i]=x
    W = compute_W(c)
    if W == frozenset({0,3}):
        print("sample hand:", [NM(i) for i in range(9) for _ in range(h[i])])
        for code in plancls[W]:
            need = collections.Counter(code)
            fits = all(c[t] >= v for t, v in need.items())
            print("   code", [NM(t) for t in code], "fits?", fits, "needs", {NM(t): v for t, v in need.items()})
        cnt += 1
        if cnt >= 1: break
