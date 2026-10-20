
import sys, os, json, pickle, random
sys.path.insert(0,"work/verify"); sys.path.insert(0,"work/strategy")
import indep_core as IC
HON=["E","S","W","N","Haku","Hatsu","Chun"]
def nm(t): return ("%d%s"%(t%9+1,"mps"[t//9])) if t<27 else HON[t-27]
BASE=[0,9,18,27]
C=pickle.load(open("work/strategy/out/table_cache.pkl","rb"))
CLS, PROFI_D, PROFII_D = C["cls"], C["PROFI_D"], C["PROFII_D"]
P=json.load(open("work/verify/plan_k4_final.json",encoding="utf-8"))
plan={frozenset(r["W"]):[tuple(c) for c in r["codes"]] for r in P["plan"]}
Z=json.load(open("work/verify/plan_k4_zero.json",encoding="utf-8"))
empties=[frozenset(r["W"]) for r in Z["plan"] if not r["codes"]]
rng=random.Random(4242)
def build_dec():
    D={}
    for idx in range(4):
        L=7 if idx==3 else 9
        units=[]
        if idx<3:
            for st in range(L-2):
                v=[0]*L; v[st]=1; v[st+1]=1; v[st+2]=1; units.append(tuple(v))
        for t in range(L):
            v=[0]*L; v[t]=3; units.append(tuple(v))
        for s in range(0,13,3):
            res=set()
            def rec(i,left,acc):
                if left==0: res.add(acc); return
                for j in range(i,len(units)):
                    u=units[j]
                    if all(acc[k]+u[k]<=4 for k in range(L)): rec(j,left-3,tuple(acc[k]+u[k] for k in range(L)))
            rec(0,s,(0,)*L)
            D[(idx,s)]=sorted(res)
    return D
_DEC=build_dec()
def dec_vecs(ci,s): return _DEC.get((ci,s),[])
def gen_hand(blocks):
    for b in blocks:
        for _ in range(300):
            A=[0]*34; ok=True
            if b[0]=="I":
                key=b[1]; e=PROFI_D.get(key)
                if not e: continue
                X=rng.choice(e[1])
                for i,x in enumerate(X): A[BASE[key[0]]+i]=x
                rem=13-key[1]; cats=[i for i in range(4) if i!=key[0]]
                for ii,ci in enumerate(cats):
                    left=len(cats)-ii-1
                    opts=[s for s in range(0,rem+1,3) if rem-s<=12*left and (s==0 or dec_vecs(ci,s))]
                    if not opts: ok=False; break
                    s=rng.choice(opts)
                    if s:
                        v=rng.choice(dec_vecs(ci,s))
                        for i,x in enumerate(v): A[BASE[ci]+i]=x
                    rem-=s
            elif b[0]=="II":
                e1,e2=PROFII_D.get(b[1]),PROFII_D.get(b[2])
                if not e1 or not e2: continue
                X1=rng.choice(e1[1]); X2=rng.choice(e2[1])
                for i,x in enumerate(X1): A[BASE[b[1][0]]+i]=x
                for i,x in enumerate(X2): A[BASE[b[2][0]]+i]=x
                rem=13-b[1][1]-b[2][1]; cats=[i for i in range(4) if i not in (b[1][0],b[2][0])]
                for ii,ci in enumerate(cats):
                    left=len(cats)-ii-1
                    opts=[s for s in range(0,rem+1,3) if rem-s<=12*left and (s==0 or dec_vecs(ci,s))]
                    if not opts: ok=False; break
                    s=rng.choice(opts)
                    if s:
                        v=rng.choice(dec_vecs(ci,s))
                        for i,x in enumerate(v): A[BASE[ci]+i]=x
                    rem-=s
            else:
                continue
            if ok and sum(A)==13:
                # 4 张上限
                if max(A)<=4: return A
    return None
print("empty classes:",len(empties))
res=[]
for W in empties:
    blocks=CLS.get(W,[])
    kinds=[b[0] for b in blocks]
    hands=[]
    for _ in range(300):
        h=gen_hand(blocks)
        if h: hands.append(h)
    wok=0; cov=0; uncon=None
    for h in hands:
        if frozenset(IC.compute_W(h))==W:
            wok+=1
            cs=plan.get(W,[])
            hit=[c for c in cs if all(h[t]>=c.count(t) for t in range(34))]
            if hit: cov+=1
            elif uncon is None: uncon=h
    res.append((W,kinds,len(hands),wok,cov,uncon))
for W,kinds,ng,wok,cov,uncon in res[:12]:
    hs=",".join(nm(t) for t in sorted(W))
    ex="" if uncon is None else "  未覆盖例: "+"".join(nm(t)*uncon[t] for t in range(34))
    print("%-24s kinds=%-18s gen=%3d Wok=%3d cov=%3d%s" % (hs[:24],",".join(kinds)[:18],ng,wok,cov,ex))
print("TOTAL: gen=%d W-ok=%d covered=%d" % (sum(r[2] for r in res),sum(r[3] for r in res),sum(r[4] for r in res)))
from collections import Counter
print("block kinds across 30 classes:", Counter(k for r in res for k in r[1]))
