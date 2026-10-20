
import sys, pickle, json
sys.path.insert(0,"work/strategy")
CLS=pickle.load(open("work/strategy/out/table_cache.pkl","rb"))["cls"]
HON=["E","S","W","N","Haku","Hatsu","Chun"]
def nm(t): return ("%d%s"%(t%9+1,"mps"[t//9])) if t<27 else HON[t-27]
# how many classes have a KOK block; dump one full block
nk=0; ex=[]
for W,blocks in CLS.items():
    for b in blocks:
        if b[0]=="KOK":
            nk+=1
            if len(ex)<4: ex.append((W,b))
            break
print("classes with KOK block:",nk)
for W,b in ex:
    print("W:",[nm(t) for t in sorted(W)])
    for i,x in enumerate(b):
        if isinstance(x,list):
            print("   field",i,"list len",len(x),"first:",x[0] if x and not isinstance(x[0],(list,tuple)) else (x[0] if x else None))
        else:
            print("   field",i,"=",repr(x)[:200])
