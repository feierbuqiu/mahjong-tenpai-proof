
import pickle
T=pickle.load(open(r"D:\DSH\MJ2\work\recon\table_perA.pkl","rb"))
CLS,PI,PII=T["cls"],T["PROFI_D"],T["PROFII_D"]
CB=[0,9,18,27]; CL=[9,9,9,7]; K=4
def v34(c,X):
    base=CB[c]; v=[0]*34
    for i,n in enumerate(X):
        if n: v[base+i]=n
    return tuple(v)
key=frozenset({1})
As=set()
for b in CLS.get(key,[]):
    kind,k1,k2,mode,z,am,nsrc=b
    if kind=="I":
        c,s,pkey=k1; am_,xs=PI[(c,s,pkey)]
        for X in xs: As.add(v34(c,X))
    elif kind=="II":
        c1,s1,k1x=k1; c2,s2,k2x=k2
        am1,xs1=PII[(c1,s1,k1x)]; am2,xs2=PII[(c2,s2,k2x)]
        for X1 in xs1:
            for X2 in xs2: As.add(tuple(a+b for a,b in zip(v34(c1,X1),v34(c2,X2))))
    else:
        As.add(tuple(1 if (t in (0,8,9,17,18,26) or 27<=t<=33) else 0 for t in range(34)))
tgt=[0]*34
for i,ch in enumerate("101200000"): tgt[i]=int(ch)
tgt=tuple(tgt)
print("target in As:", tgt in As, " total A:", len(As))
big=[A for A in As if sum(A)>=K]
bs=sorted(big,key=sum); keep=[]
for A in bs:
    if not any(all(k[t]<=A[t] for t in range(34)) for k in keep): keep.append(A)
    if len(keep)>3000: break
print("target in minimal:", tgt in keep, " minimal count:", len(keep))
if tgt not in keep:
    sub=[A for A in keep if all(A[t]<=tgt[t] for t in range(34))]
    print("smaller minimal A's contained in target:", len(sub), [(sum(A),A[:5]) for A in sub[:3]])
