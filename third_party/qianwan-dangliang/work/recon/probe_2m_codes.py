
import json, collections
HON=["E","S","W","N","Haku","Hatsu","Chun"]
H2={n:27+i for i,n in enumerate(HON)}
def s2t(s):
    if s in H2: return H2[s]
    if s.endswith("z"): return 27+int(s[:-1])-1
    return (0 if s.endswith("m") else 1 if s.endswith("p") else 2)*9+int(s[:-1])-1
def keyof(w): return frozenset(s2t(x) if isinstance(x,str) else x for x in w)
def nm(t): return ("%d%s"%((t%9)+1,"mps"[t//9])) if t<27 else HON[t-27]
plan=json.load(open(r"D:\DSH\MJ2\work\recon\plan_k4_u19.json"))["plan"]
for e in plan:
    if keyof(e["W"])==frozenset({1}):
        cs=[tuple(c) for c in e["codes"]]
        print("n codes:", len(cs))
        catpat=collections.Counter("".join(sorted({("mpsz"[t//9]) for t in c})) for c in cs)
        print("category patterns:", dict(catpat.most_common(8)))
        print("sample:", [[nm(t) for t in c] for c in cs[:8]])
        break
