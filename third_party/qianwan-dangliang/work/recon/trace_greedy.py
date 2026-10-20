
import pickle, itertools, collections, math
T=pickle.load(open(r"D:\DSH\MJ2\work\recon\table_perA.pkl","rb"))
CLS,PI,PII=T["cls"],T["PROFI_D"],T["PROFII_D"]
CB=[0,9,18,27]; CL=[9,9,9,7]; K=4
def v34(c,X):
    base=CB[c]; v=[0]*34
    for i,n in enumerate(X):
        if n: v[base+i]=n
    return tuple(v)
def nperm(m):
    f=1
    for x in set(m): f*=math.factorial(m.count(x))
    return 24//f
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
big=[A for A in As if sum(A)>=K]
bs=sorted(big,key=sum); keep=[]
for A in bs:
    if not any(all(k[t]<=A[t] for t in range(34)) for k in keep): keep.append(A)
    if len(keep)>3000: break
tgt=[0]*34
for i,ch in enumerate("101200000"): tgt[i]=int(ch)
tgt=tuple(tgt)
# 模拟 v21 greedy(空容量)
used=collections.Counter(); usedset=set()
unc=set(range(len(keep))); covered_target=False; iter_count=0
while unc and iter_count<20:
    iter_count+=1
    i=min(unc,key=lambda j: sum(keep[j])); A=keep[i]
    tl=[t for t,n in enumerate(A) for _ in range(n)]
    best=None; bc=0
    for pat in set(itertools.combinations_with_replacement(tl,K)):
        cnt=0
        for j in unc:
            Aj=keep[j]
            if all(Aj[t]>=pat.count(t) for t in set(pat)): cnt+=1
        if cnt>bc: bc=cnt; best=pat
    print("iter",iter_count,"A size",sum(A),"best",best,"coverage",bc)
    if best is not None:
        used[best]+=1; usedset.add(best)
        if all(tgt[t]>=best.count(t) for t in set(best)): covered_target=True; print("  -> target covered by",best); break
        unc={j for j in unc if not all(keep[j][t]>=best.count(t) for t in set(best))}
print("target covered in first 20 iterations:", covered_target, " tgt in keep idx:", keep.index(tgt) if tgt in keep else None)
