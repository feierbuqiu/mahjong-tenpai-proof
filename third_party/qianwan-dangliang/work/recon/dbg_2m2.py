
import json, itertools, collections
HON=["E","S","W","N","Haku","Hatsu","Chun"]
H2={n:27+i for i,n in enumerate(HON)}
def s2t(s):
    if s in H2: return H2[s]
    if s.endswith("z"): return 27+int(s[:-1])-1
    return (0 if s.endswith("m") else 1 if s.endswith("p") else 2)*9+int(s[:-1])-1
def keyof(w): return frozenset(s2t(x) if isinstance(x,str) else x for x in w)
plan=json.load(open(r"D:\DSH\MJ2\work\recon\plan_k4_u19.json"))["plan"]
codes=None
for e in plan:
    if keyof(e["W"])==frozenset({1}): codes=[tuple(c) for c in e["codes"]]; break
print("class {2m} codes:", len(codes))
A=[0]*34
for i,ch in enumerate("101200000"): A[i]=int(ch)
A=tuple(A)
print("A tiles:", [(i,n) for i,n in enumerate(A) if n])
sub=[c for c in codes if all(A[t]>=c.count(t) for t in set(c))]
print("codes in A:", len(sub), sub[:5])
# 枚举 F: p,s,z 各 3 个面子(共 9 张), cap 4
CB=[0,9,18,27]; CL=[9,9,9,7]
melds=[]
for c in (1,2,3):
    b=CB[c]; n=CL[c]
    for i in range(n):
        v=[0]*34; v[b+i]=3; melds.append(tuple(v))
    if c<3:
        for i in range(n-2):
            v=[0]*34
            for k in range(3): v[b+i+k]=1
            melds.append(tuple(v))
melds=list(set(melds))
print("melds in p,s,z:", len(melds))
def addfs(n):
    out=set()
    for combo in itertools.combinations_with_replacement(range(len(melds)), n):
        v=[0]*34; ok=True
        for mi in combo:
            m=melds[mi]
            for t in range(34):
                if m[t]:
                    v[t]+=m[t]
                    if v[t]>4: ok=False; break
            if not ok: break
        if ok: out.add(tuple(v))
    return out
Fs=addfs(3)
print("distinct F (3 melds):", len(Fs))
unc=[]
for F in Fs:
    hand=tuple(a+b for a,b in zip(A,F))
    hit=any(all(hand[t]>=c.count(t) for t in set(c)) for c in codes)
    if not hit: unc.append(F)
print("uncovered (A,F) count:", len(unc), "of", len(Fs))
if unc:
    F=unc[0]
    print("  one uncovered F:", "".join("%s:%d"%(HON[t-27] if t>=27 else str(t%9+1)+"mps"[t//9],n) for t,n in enumerate(F) if n))
    hand=tuple(a+b for a,b in zip(A,F))
    print("  hand:", " ".join((HON[t-27] if t>=27 else str(t%9+1)+"mps"[t//9])*n for t,n in enumerate(hand) if n))
    print("  codes that fit the hand:", sum(1 for c in codes if all(hand[t]>=c.count(t) for t in set(c))))