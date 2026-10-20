
import pickle, collections, time
T=pickle.load(open(r"D:\DSH\MJ2\work\recon\table_perA.pkl","rb"))
CLS=T["cls"]; PI=T["PROFI_D"]; PII=T["PROFII_D"]
def v34(c, X):
    base=(0 if c==0 else 9 if c==1 else 18 if c==2 else 27)
    v=[0]*34
    for i,n in enumerate(X):
        if n: v[base+i]=n
    return tuple(v)
t0=time.time()
stats=collections.Counter(); tot_req=0; big=[]
kindinfo=collections.Counter()
for W,blocks in CLS.items():
    As=set()
    for b in blocks:
        kind,k1,k2,mode,z,am,nsrc = b
        kindinfo[kind]+=1
        na=sum(am)
        if na>=4:
            As.add(tuple(am)); stats["am>=4"]+=1
        else:
            stats["am<4"]+=1
            if kind=="I":
                c,s,pkey=k1; am_,xs=PI[(c,s,pkey)]
                for X in xs: As.add(v34(c,X))
            elif kind=="II":
                c1,s1,k1x=k1; c2,s2,k2x=k2
                am1,xs1=PII[(c1,s1,k1x)]; am2,xs2=PII[(c2,s2,k2x)]
                if len(xs1)*len(xs2) > 50000:
                    As.add(tuple(am))   # 保守: 用 min（可能 <4 张, 单独报告）
                    stats["too_many_pairs"]+=1
                else:
                    for X1 in xs1:
                        v1=v34(c1,X1)
                        for X2 in xs2:
                            v2=v34(c2,X2)
                            As.add(tuple(a+b for a,b in zip(v1,v2)))
            else:
                As.add(tuple(am))
    tot_req+=len(As)
    if len(As)>1000: big.append((len(As), sorted(W)[:4]))
print("blocks:", dict(stats), "kinds:", dict(kindinfo))
print("total distinct A-requirements:", tot_req)
print("classes with >1000 A's:", len(big), sorted(big, reverse=True)[:6])
print("time %.1fs"%(time.time()-t0))
