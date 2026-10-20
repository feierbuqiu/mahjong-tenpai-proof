import sys, os, json
sys.path.insert(0,'D:/DSH/MJ2/work/audit')
from mjcore import *
from collections import Counter
P=json.load(open('D:/DSH/MJ2/work/verify/plan_k4_FINAL.json',encoding='utf-8'))
PLAN={}
for r in P['plan']:
    W=frozenset(nm_idx(x) for x in r['W'])
    PLAN[W]=[tuple(nm_idx(t) for t in c) for c in r['codes']]

# explicit gap hand: A = 1m, F = pairs 1p..6p (each x2)
h=[0]*34
h[0]=1
for t in range(9,15): h[t]=2
h=tuple(h)
print("hand:", hand_str(h), "sum", sum(h), "max", max(h))
print("W(H) =", [nm(t) for t in sorted(waits(h))])
print("W_std =", [nm(t) for t in sorted(waits_std(h))], "win_chiitoi(H+1m)=", win_chiitoi(add(h,0)))
print("melds_ok(F) =", melds_ok(tuple(0 if t not in range(9,15) else 2 for t in range(34))))
W=frozenset(waits(h))
cs=PLAN.get(W)
print("class found in plan:", cs is not None, "n_codes:", len(cs) if cs else 0)
fit=[c for c in (cs or []) if all(h[t]>=v for t,v in Counter(c).items())]
print("codes fitting this hand:", [[nm(t) for t in c] for c in fit][:10], " count:", len(fit))
print()
print("all codes of class {1m} (first 40):", [[nm(t) for t in c] for c in (PLAN.get(frozenset([0])) or [])][:40])
