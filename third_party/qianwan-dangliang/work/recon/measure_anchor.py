
import pickle, collections, time
T=pickle.load(open(r"D:\DSH\MJ2\work\recon\table_perA.pkl","rb"))
CLS,PI,PII=T["cls"],T["PROFI_D"],T["PROFII_D"]
CAT_BASE=[0,9,18,27]; CAT_LEN=[9,9,9,7]
def v34(c,X):
    base=CAT_BASE[c]; v=[0]*34
    for i,n in enumerate(X):
        if n: v[base+i]=n
    return tuple(v)
t0=time.time()
dist=collections.Counter(); anchors=collections.Counter(); big=0
for W,blocks in CLS.items():
    inter=None; nA=0
    for b in blocks:
        kind,k1,k2,mode,z,am,nsrc=b
        As=[]
        if kind=="I":
            c,s,pkey=k1; am_,xs=PI[(c,s,pkey)]
            As=[v34(c,X) for X in xs]
        elif kind=="II":
            c1,s1,k1x=k1; c2,s2,k2x=k2
            am1,xs1=PII[(c1,s1,k1x)]; am2,xs2=PII[(c2,s2,k2x)]
            if len(xs1)*len(xs2)<=5000:
                for X1 in xs1:
                    v1=v34(c1,X1)
                    for X2 in xs2:
                        v2=v34(c2,X2)
                        As.append(tuple(a+b for a,b in zip(v1,v2)))
            else:
                big+=1
                As=[tuple(a+b for a,b in zip(v34(c1,am1),v34(c2,am2)))]
        else:
            As=[tuple(1 if (t in (0,8,9,17,18,26) or 27<=t<=33) else 0 for t in range(34))]
        for A in As:
            nA+=1
            sup=frozenset(i for i,n in enumerate(A) if n)
            inter = sup if inter is None else (inter & sup)
            if not inter: break
        if inter is not None and not inter: break
    k = len(inter) if inter is not None else 0
    dist[k if k<5 else "5+"]+=1
    if k==1: anchors[next(iter(inter))]+=1
print("class-level common-tile set size distribution:", dict(sorted(dist.items(), key=str)))
print("classes with |I|==1, anchor histogram (top10):", anchors.most_common(10))
print("blocks with too-many-pairs (fell back to min):", big, " time %.1fs"%(time.time()-t0))
