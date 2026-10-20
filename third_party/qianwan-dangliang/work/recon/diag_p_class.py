
import numpy as np, json
HON=["E","S","W","N","Haku","Hatsu","Chun"]
def t2s(t): return ("%d%s"%((t%9)+1,"mps"[t//9])) if t<27 else HON[t-27]
z=np.load(r"D:\DSH\MJ2\work\verify\cache_w_p.npz"); hands=z["hands"]; wids=z["wids"]
wlist=json.load(open(r"D:\DSH\MJ2\work\verify\cache_w_p.json"))
plan={}
import collections
def keyof(w):
    H={n:27+i for i,n in enumerate(HON)}
    def s2t(s):
        if s in H: return H[s]
        if s.endswith("z"): return 27+int(s[:-1])-1
        return (0 if s.endswith("m") else 1 if s.endswith("p") else 2)*9+int(s[:-1])-1
    return frozenset(s2t(x) if isinstance(x,str) else x for x in w)
for e in json.load(open(r"D:\DSH\MJ2\work\recon\plan_k4_u9.json"))["plan"]:
    plan[keyof(e["W"])]=[tuple(c) for c in e["codes"]]
for want in [(11,15),(11,14),(20,22)]:
    key=frozenset(want)
    wid=None
    for i,W in enumerate(wlist):
        if frozenset(W)==key: wid=i; break
    if wid is None: print("no wid for",want); continue
    idx=np.nonzero(wids==wid)[0]
    codes=plan.get(key,[])
    mono=[c for c in codes if all(9<=t<18 for t in c)]
    H=hands[idx]; cov=np.zeros(len(idx),dtype=bool)
    for c in mono:
        need=np.zeros(9,dtype=np.int8)
        for t in c: need[t-9]+=1
        cov |= (H>=need).all(axis=1)
    unc=idx[~cov]
    print("W=",[t2s(t) for t in sorted(key)],"hands=",len(idx),"codes=",len(codes),"mono_codes=",len(mono),"uncovered=",len(unc))
    print("   mono codes sample:", [[t2s(x) for x in c] for c in mono[:6]])
    for i in unc[:3]:
        v=hands[i]
        print("   uncovered hand:", "".join("%d%s"%(n,"123456789"[j]) for j,n in enumerate(v) if n))
