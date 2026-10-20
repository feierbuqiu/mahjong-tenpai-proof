
import pickle, itertools, collections, math
T=pickle.load(open(r"D:\DSH\MJ2\work\recon\table_perA.pkl","rb"))
CLS,PI,PII=T["cls"],T["PROFI_D"],T["PROFII_D"]
CB=[0,9,18,27]; CL=[9,9,9,7]
def v34(c,X):
    base=CB[c]; v=[0]*34
    for i,n in enumerate(X):
        if n: v[base+i]=n
    return tuple(v)
K=4
key=frozenset({1})
blocks=CLS.get(key,[])
As=set()
for b in blocks:
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
print("distinct A:", len(As))
big=[A for A in As if sum(A)>=K]
bs=sorted(big, key=sum); keep=[]
for A in bs:
    if not any(all(k[t]<=A[t] for t in range(34)) for k in keep): keep.append(A)
    if len(keep)>3000: break
print("big A:", len(big), " minimal:", len(keep))
import collections as C
sz=C.Counter(sum(A) for A in keep)
print("minimal A size dist:", dict(sz))
tgt=(1,0,1,2,0,0,0,0,0)
print("target in minimal?:", tgt in keep, " target in big?:", tgt in big)
# target 是否被更小的 minimal A 包含
subs=[A for A in keep if all(A[t]<=tgt[t] for t in range(34))]
print("minimal A's contained in target:", len(subs), [sum(A) for A in subs][:5])
