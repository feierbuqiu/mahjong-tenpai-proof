
import json, sys
HON=["E","S","W","N","Haku","Hatsu","Chun"]
def ti(x):
    if isinstance(x,int): return x
    if x in HON: return 27+HON.index(x)
    return "mps".index(x[-1])*9+int(x[0])-1
def nm(t): return ("%d%s"%(t%9+1,"mps"[t//9])) if t<27 else HON[t-27]
ORPH=[0,8,9,17,18,26]+list(range(27,34))
def kok_family(S):
    fam=[]
    if len(S)==13: 
        h=[0]*34
        for o in ORPH: h[o]=1
        fam.append(h)
    else:
        t=S[0]; base=[o for o in ORPH if o!=t]
        for d in base:
            h=[0]*34
            for o in base: h[o]=1
            h[d]+=1; fam.append(h)
    return fam
m=json.load(open("work/verify/waste_list_exact.json",encoding="utf-8"))
D={}
for e in m["waste_by_class"]:
    W=tuple(sorted(ti(x) for x in e["W"]))
    for c in e["codes"]: D.setdefault(W,set()).add(tuple(ti(x) for x in c))
a=json.load(open("work/lowerbound/waste_list.json",encoding="utf-8"))
B={}
for e in a["classes"]:
    W=tuple(sorted(ti(x) for x in e["W"]))
    for c in e["del"]: B.setdefault(W,set()).add(tuple(ti(x) for x in c))
DS={(W,c) for W,l in D.items() for c in l}; BS={(W,c) for W,l in B.items() for c in l}
print("mine=%d analyst=%d | mine-analyst=%d analyst-mine=%d | union=%d" % (len(DS),len(BS),len(DS-BS),len(BS-DS),len(DS|BS)))
print("\n== mine - analyst (我判定为浪费, 分析师未列) ==")
for W,c in sorted(DS-BS):
    fam=kok_family(list(W))
    sub=any(all(c.count(i)<=h[i] for i in range(34)) for h in fam)
    print("  W=%-14s code=%-26s |W|=%d  ⊆该类KOK手工? %s" % (",".join(nm(t) for t in W)[:22], ",".join(nm(t) for t in c), len(W), sub))
print("\n== analyst - mine ==")
for W,c in sorted(BS-DS):
    print("  W=%-14s code=%s" % (",".join(nm(t) for t in W)[:22], ",".join(nm(t) for t in c)))
# which classes do the extras belong to
from collections import Counter
print("\nextra classes:", Counter(tuple(sorted(W)) for W,_ in (DS-BS)))
