
import pickle, collections, sys
sys.path.insert(0,"work/strategy")
C=pickle.load(open("work/strategy/out/table_cache.pkl","rb"))
CLS,PROFI_D,PROFII_D=C["cls"],C["PROFI_D"],C["PROFII_D"]
ii=[]; ik=collections.Counter()
for W,blocks in CLS.items():
    for b in blocks:
        ik[b[0]]+=1
        if b[0]=="II":
            k1,k2=b[1],b[2]
            e1,e2=PROFII_D.get(k1),PROFII_D.get(k2)
            ii.append((len(e1[1]) if e1 else 0, len(e2[1]) if e2 else 0))
print("CLS block kinds:",ik)
print("II blocks:",len(ii))
import numpy as np
a=np.array(ii)
print("variant counts: max1=%d max2=%d mean1=%.1f mean2=%.1f" % (a[:,0].max(),a[:,1].max(),a[:,0].mean(),a[:,1].mean()))
print("pairs product sum=%.3g max=%d" % ((a[:,0]*a[:,1]).sum(), (a[:,0]*a[:,1]).max()))
# I blocks variant sizes
isizes=[len(PROFI_D[b[1]][1]) for W,bs in CLS.items() for b in bs if b[0]=="I" and b[1] in PROFI_D]
print("I blocks with variants:",len(isizes),"max variants:",max(isizes),"sum:",sum(isizes))
print("sample II block:",[b for W,bs in CLS.items() for b in bs if b[0]=="II"][0])
