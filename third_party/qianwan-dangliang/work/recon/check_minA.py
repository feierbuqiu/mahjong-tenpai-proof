
import pickle, json
T=pickle.load(open(r"D:\DSH\MJ2\work\recon\table_perA.pkl","rb"))
CLS,PI,PII=T["cls"],T["PROFI_D"],T["PROFII_D"]
key=frozenset({1})   # 2m
blocks=CLS.get(key,[])
print("blocks:", len(blocks))
tgt=(1,0,1,2,0,0,0,0,0)
found=False; sizes={}
for b in blocks:
    kind,k1,k2,mode,z,am,nsrc=b
    if kind!="I": continue
    c,s,pkey=k1
    am_,xs=PI[(c,s,pkey)]
    sizes[s]=sizes.get(s,0)+len(xs)
    for X in xs:
        if tuple(X)==tgt: found=True
    if s==4:
        print("  s=4 block: cat",c,"pkey",str(pkey)[:60],"n_xs",len(xs),"min",am_)
        print("   xs sample:", xs[:5])
print("target A in xs?:", found, " sizes:", sizes)
