# -*- coding: utf-8 -*-
"""t9_gap_concrete2.py -- verify suspected counterexamples with the independent engine."""
import sys, os, json, itertools, time
sys.path.insert(0,'D:/DSH/MJ2/work/audit')
from mjcore import *
from collections import Counter
P=json.load(open('D:/DSH/MJ2/work/verify/plan_k4_FINAL.json',encoding='utf-8'))
PLAN={}
for r in P['plan']:
    W=frozenset(nm_idx(x) for x in r['W'])
    PLAN[W]=[tuple(nm_idx(t) for t in c) for c in r['codes']]

def mkh(Astr, Fkinds):
    h=list(from_str(Astr))
    for t in Fkinds: h[t]+=2
    return tuple(h)

bad=[]
t0=time.time()
Astr="1122334m"
# all F = 3 distinct kinds outside m-suit
others=[t for t in range(34) if t>=9]
n=0
for Fk in itertools.combinations(others,3):
    h=mkh(Astr,Fk)
    n+=1
    w=waits(h)
    if not w: continue
    cs=PLAN.get(w)
    if cs is None:
        bad.append((hand_str(h),[nm(t) for t in sorted(w)],"MISSING CLASS")); continue
    hit=[c for c in cs if all(h[t]>=v for t,v in Counter(c).items())]
    if not hit:
        if len(bad)<20:
            bad.append((hand_str(h),[nm(t) for t in sorted(w)],"UNCOVERED", len(cs)))
print("A=%s checked %d hands, bad=%d (%.0fs)" % (Astr,n,len(bad),time.time()-t0))
for b in bad[:10]: print("   ", b)
# also: is 4m's class present, how many codes, and does any code fit A itself?
W=frozenset(waits(from_str(Astr)))
print("W(A alone, 7 tiles)=", [nm(t) for t in sorted(W)])
for probe in [from_str(Astr)]:
    pass
# class {4m} codes that fit A=1122334m?
A=from_str(Astr)
cs=PLAN.get(frozenset([3]))
print("class {4m}: n_codes=",len(cs) if cs else None)
fits=[c for c in (cs or []) if all(A[t]>=v for t,v in Counter(c).items())]
print("codes ⊆ A:", [[nm(t) for t in c] for c in fits])
json.dump({"A":Astr,"checked":n,"bad":[list(map(str,b)) for b in bad[:50]]}, open('D:/DSH/MJ2/work/audit/t9_gap_concrete2.json','w'), ensure_ascii=False, indent=1)
