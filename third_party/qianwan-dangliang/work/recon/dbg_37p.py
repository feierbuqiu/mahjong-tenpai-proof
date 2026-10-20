
import pickle, collections, itertools
T=pickle.load(open(r"D:\DSH\MJ2\work\recon\table_perA.pkl","rb"))
CLS,PI,PII=T["cls"],T["PROFI_D"],T["PROFII_D"]
CB=[0,9,18,27]
def v34(c,X):
    base=CB[c]; v=[0]*34
    for i,n in enumerate(X):
        if n: v[base+i]=n
    return tuple(v)
key=frozenset({11,15})   # 3p,7p
blocks=CLS.get(key,[])
print("blocks:",len(blocks))
sizes=collections.Counter()
AsBySize=collections.Counter()
for b in blocks:
    kind,k1,k2,mode,z,am,nsrc=b
    if kind=="I":
        c,s,pkey=k1
        am_,xs=PI[(c,s,pkey)]
        sizes[("I",s)]+=1; AsBySize[s]+=len(xs)
    else:
        sizes[(kind,)]+=1
print("block kinds:", dict(sizes))
print("A counts by block size:", dict(AsBySize))
# 总 A 去重
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
            for X2 in xs2:
                As.add(tuple(a+b for a,b in zip(v34(c1,X1),v34(c2,X2))))
print("distinct A:", len(As), " of size 13:", sum(1 for A in As if sum(A)==13))
