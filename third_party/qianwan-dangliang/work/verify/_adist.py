
import json,collections
B=json.load(open("work/verify/block_coverage_exact.json",encoding="utf-8"))
items=B["uncovered_I"]+B["uncovered_II"]
cnt=collections.Counter()
for it in items:
    if it["kind"]=="I":
        n=sum(int(c) for c in it["A"])
    else:
        n=sum(int(c) for c in it["A1"])+sum(int(c) for c in it["A2"])
    cnt[n]+=1
print("|A| 分布:",dict(sorted(cnt.items())))
print("总条目:",len(items))
print("|A|>=4 的条目:",sum(v for k,v in cnt.items() if k>=4))
for it in items:
    n=(sum(int(c) for c in it["A"]) if it["kind"]=="I" else sum(int(c) for c in it["A1"])+sum(int(c) for c in it["A2"]))
    if n<4: print("   |A|=%d %s %s" % (n,it["kind"],",".join(it["W"])),"A="+str(it.get("A") or (it["A1"]+"/"+it["A2"])))
