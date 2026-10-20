
import pickle, json, itertools
T=pickle.load(open(r"D:\DSH\MJ2\work\recon\table_perA.pkl","rb"))
CLS,PI,PII=T["cls"],T["PROFI_D"],T["PROFII_D"]
CB=[0,9,18,27]; CL=[9,9,9,7]; HON=["E","S","W","N","Haku","Hatsu","Chun"]
def t2s(t): return ("%d%s"%((t%9)+1,"mps"[t//9])) if t<27 else HON[t-27]
def v34(c,X):
    base=CB[c]; v=[0]*34
    for i,n in enumerate(X):
        if n: v[base+i]=n
    return tuple(v)
u5=json.load(open(r"D:\DSH\MJ2\work\recon\plan_k4_u5.json"))["plan"]
H={n:27+i for i,n in enumerate(HON)}
def keyof(w):
    def s2t(s):
        if s in H: return H[s]
        if s.endswith("z"): return 27+int(s[:-1])-1
        return (0 if s.endswith("m") else 1 if s.endswith("p") else 2)*9+int(s[:-1])-1
    return frozenset(s2t(x) if isinstance(x,str) else x for x in w)
for target in [frozenset({30,31}), frozenset({20,23,26})]:
    codes=None
    for e in u5:
        if keyof(e["W"])==target: codes=[tuple(c) for c in e["codes"]]; break
    print("W=", [t2s(t) for t in sorted(target)], "n_codes=", len(codes) if codes else None)
    if codes: print("   sample codes:", [[t2s(x) for x in c] for c in codes[:6]])
    blocks=CLS.get(target,[])
    print("   blocks:", len(blocks))
    for b in blocks[:6]:
        kind,k1,k2,mode,z,am,nsrc=b
        print("     ", kind, k1 if kind!="II" else (k1,k2), "mode",mode,"am_sum",sum(am),"nsrc",nsrc)
