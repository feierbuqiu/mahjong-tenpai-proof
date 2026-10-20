
import json, pickle
HON=["E","S","W","N","Haku","Hatsu","Chun"]
def t2s(t): return ("%d%s"%((t%9)+1,"mps"[t//9])) if t<27 else HON[t-27]
def s2t(s):
    H={n:27+i for i,n in enumerate(HON)}
    if s in H: return H[s]
    if s.endswith("z"): return 27+int(s[:-1])-1
    return (0 if s.endswith("m") else 1 if s.endswith("p") else 2)*9+int(s[:-1])-1
def keyof(w): return frozenset(s2t(x) if isinstance(x,str) else x for x in w)
p=json.load(open(r"D:\DSH\MJ2\work\recon\plan_k4_u9.json"))["plan"]
T=pickle.load(open(r"D:\DSH\MJ2\work\recon\table_perA.pkl","rb"))
CLS=T["cls"]
for target in [{12,16},{16,22},{20,23,26}]:
    for e in p:
        if keyof(e["W"])==target:
            codes=[tuple(c) for c in e["codes"]]
            print("W=",[t2s(t) for t in sorted(target)],"n_codes=",len(codes))
            print("   sample:", [[t2s(x) for x in c] for c in codes[:5]])
            p_codes=[c for c in codes if any(t//9==1 for t in c) and any(t//9 in (0,2,3) for t in c)]
            print("   codes with (p + inert):", len(p_codes), [[t2s(x) for x in c] for c in p_codes[:5]])
            print("   blocks:", len(CLS.get(target,[])))
            break
