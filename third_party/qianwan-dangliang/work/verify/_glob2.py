
import sys, json, pickle, random
sys.path.insert(0,"work/verify"); sys.path.insert(0,"work/strategy")
import indep_core as IC
HON=["E","S","W","N","Haku","Hatsu","Chun"]
def nm(t): return ("%d%s"%(t%9+1,"mps"[t//9])) if t<27 else HON[t-27]
BASE=[0,9,18,27]
C=pickle.load(open("work/strategy/out/table_cache.pkl","rb"))
CLS,PROFI_D,PROFII_D=C["cls"],C["PROFI_D"],C["PROFII_D"]
P=json.load(open("work/verify/plan_k4_final.json",encoding="utf-8"))
plan={frozenset(r["W"]):[tuple(c) for c in r["codes"]] for r in P["plan"]}
allcodes=[(frozenset(r["W"]),tuple(c)) for r in P["plan"] for c in r["codes"]]
Z=json.load(open("work/verify/plan_k4_zero.json",encoding="utf-8"))
empties=[frozenset(r["W"]) for r in Z["plan"] if not r["codes"]]
def build_dec():
    D={}
    for idx in range(4):
        L=7 if idx==3 else 9; units=[]
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
rng=random.Random(4242)
def gen_hand(blocks):
    b=blocks[0]
    for _ in range(400):
        A=[0]*34; ok=True
        if b[0]=="I":
            key=b[1]; e=PROFI_D.get(key)
            if not e: return None
            X=rng.choice(e[1])
            for i,x in enumerate(X): A[BASE[key[0]]+i]=x
            rem=13-key[1]; cats=[i for i in range(4) if i!=key[0]]
        else:
            e1,e2=PROFII_D.get(b[1]),PROFII_D.get(b[2])
            if not e1 or not e2: return None
            X1=rng.choice(e1[1]); X2=rng.choice(e2[1])
            for i,x in enumerate(X1): A[BASE[b[1][0]]+i]=x
            for i,x in enumerate(X2): A[BASE[b[2][0]]+i]=x
            rem=13-b[1][1]-b[2][1]; cats=[i for i in range(4) if i not in (b[1][0],b[2][0])]
        for ii,ci in enumerate(cats):
            left=len(cats)-ii-1
            opts=[s for s in range(0,rem+1,3) if rem-s<=12*left and (s==0 or _DEC.get((ci,s)))]
            if not opts: ok=False; break
            s=rng.choice(opts)
            if s:
                v=rng.choice(_DEC[(ci,s)])
                for i,x in enumerate(v): A[BASE[ci]+i]=x
            rem-=s
        if ok and sum(A)==13 and max(A)<=4: return A
    return None
print("%-24s %3s %6s %6s %8s %8s %8s" % ("class W","n","W-ok","sameC","global","otherC","globalCovered"))
tot=[0,0,0,0]
for W in empties:
    blocks=CLS.get(W,[]); n=0; same=0; glob=0; other=0
    for _ in range(12):
        for _try in range(300):
            h=gen_hand(blocks)
            if not h: break
            if frozenset(IC.compute_W(h))!=W: continue
            n+=1
            s=sum(1 for Wc,c in allcodes if Wc==W and all(h[t]>=c.count(t) for t in range(34)))
            g=[1 for Wc,c in allcodes if all(h[t]>=c.count(t) for t in range(34))]
            same+=s; glob+=len(g); other+=len(g)-s
            break
    print("%-24s %3d %6d %6d %8.1f %8.1f %8s" % (",".join(nm(t) for t in sorted(W))[:24],n,n,same,glob/max(n,1),other/max(n,1),
          "YES" if glob>0 else "NO"))
    tot[0]+=n; tot[1]+=same; tot[2]+=glob; tot[3]+=other
print("TOTAL hands=%d same-class hits=%d global hits=%d other-class hits=%d" % tuple(tot))
