
import json
HON=["E","S","W","N","Haku","Hatsu","Chun"]
H2={n:27+i for i,n in enumerate(HON)}
def s2t(s):
    if s in H2: return H2[s]
    if s.endswith("z"): return 27+int(s[:-1])-1
    return (0 if s.endswith("m") else 1 if s.endswith("p") else 2)*9+int(s[:-1])-1
def keyof(w): return frozenset(s2t(x) if isinstance(x,str) else x for x in w)
def nm(t): return ("%d%s"%((t%9)+1,"mps"[t//9])) if t<27 else HON[t-27]
plan=json.load(open(r"D:\DSH\MJ2\work\recon\plan_k4_u20.json"))["plan"]
for e in plan:
    if keyof(e["W"])==frozenset({1}):
        cs=[tuple(c) for c in e["codes"]]
        # 找 2 张 m + 2 张同门相邻的码 (run 型)
        runlike=[]
        for c in cs:
            ms=[t for t in c if t<9]; os_=[t for t in c if t>=9]
            if len(ms)==2 and len(os_)==2:
                a,b=sorted(os_)
                if a//9==b//9 and b-a==1: runlike.append(c)
        print("run-like codes:", len(runlike), [[nm(t) for t in c] for c in runlike[:6]])
        # 检查具体未覆盖手牌
        hand={0:1,2:1,3:2,15:1,16:1,17:1,21:1,22:1,23:1,24:1,25:1,26:1}
        fit=[c for c in cs if all(hand.get(t,0)>=c.count(t) for t in set(c))]
        print("codes fitting the sample hand:", len(fit), [[nm(t) for t in c] for c in fit[:5]])
        break