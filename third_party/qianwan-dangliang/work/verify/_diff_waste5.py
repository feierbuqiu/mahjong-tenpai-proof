
import json
HON=["E","S","W","N","Haku","Hatsu","Chun"]
def ti(x):
    if isinstance(x,int): return x
    if x in HON: return 27+HON.index(x)
    return "mps".index(x[-1])*9+int(x[0])-1
def nm(t): return ("%d%s"%(t%9+1,"mps"[t//9])) if t<27 else HON[t-27]
m=json.load(open("work/verify/waste_list_exact.json",encoding="utf-8"))
A={}
for e in m["waste_by_class"]:
    W=tuple(sorted(ti(x) for x in e["W"]))
    for c in e["codes"]: A.setdefault(W,[]).append(tuple(ti(x) for x in c))
a=json.load(open("work/lowerbound/waste_list.json",encoding="utf-8"))
B={}
for e in a["classes"]:
    W=tuple(sorted(ti(x) for x in e["W"]))
    for c in e["del"]: B.setdefault(W,[]).append(tuple(ti(x) for x in c))
# ordered (W, code) sets, also multiset forms for reference
def flat(D, srt):
    s=set()
    for W,lst in D.items():
        for c in lst: s.add((W, tuple(sorted(c)) if srt else c))
    return s
for label,srt in (("ordered",False),("multiset",True)):
    A2,B2=flat(A,srt),flat(B,srt)
    print("%s: mine raw=%d uniq=%d | analyst raw=%d uniq=%d | onlyMine=%d onlyAnalyst=%d" %
          (label,sum(len(v) for v in A.values()),len(A2),sum(len(v) for v in B.values()),len(B2),
           len(A2-B2),len(B2-A2)))
    for x in sorted(B2-A2)[:4]: print("    onlyAnalyst:",[nm(t) for t in x[0]], [nm(t) for t in x[1]])
# duplicated (W,code) inside each list?
for nmx,D in (("mine",A),("analyst",B)):
    dup=0
    for W,lst in D.items():
        c=len(lst)-len(set(lst)); dup+=c
    print(nmx,"ordered dup entries:",dup, " classes:",len(D))
