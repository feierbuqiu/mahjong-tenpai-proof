
import sys, pickle, json
sys.path.insert(0,"work/strategy")
CLS=pickle.load(open("work/strategy/out/table_cache.pkl","rb"))["cls"]
HON=["E","S","W","N","Haku","Hatsu","Chun"]
def nm(t): return ("%d%s"%(t%9+1,"mps"[t//9])) if t<27 else HON[t-27]
ORPH=set([0,8,9,17,18,26]+list(range(27,34)))
rows=[]
for W,blocks in CLS.items():
    for b in blocks:
        if b[0]=="KOK":
            rows.append((len(W), sorted(W), b[2], tuple(sorted(W))==tuple(sorted(ORPH))))
            break
print("KOK classes:",len(rows))
for r in sorted(rows): print("  |W|=%d miss_field=%s full_orphans=%s W=%s" % (r[0], r[2], r[3], [nm(t) for t in r[1]][:4]))
# is field2 == the single W element for |W|=1?
bad=[r for r in rows if r[0]==1 and r[2]!=r[1][0]]
print("inconsistent field2:",len(bad))
