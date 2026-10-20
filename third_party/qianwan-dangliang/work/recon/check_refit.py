
import json, collections
HON=["E","S","W","N","Haku","Hatsu","Chun"]
def s2t(s):
    H={n:27+i for i,n in enumerate(HON)}
    if s in H: return H[s]
    if s.endswith("z"): return 27+int(s[:-1])-1
    return (0 if s.endswith("m") else 1 if s.endswith("p") else 2)*9+int(s[:-1])-1
d=json.load(open(r"D:\DSH\MJ2\work\verify\plan_k4_refit.json"))["plan"]
allc=[tuple(c) for e in d for c in e["codes"]]
print("classes:",len(d),"codes:",len(allc),"distinct:",len(set(allc)),"empty:",sum(1 for e in d if not e["codes"]))
print("code length set:", set(len(c) for c in allc))
# 单调子宇宙用量
per=collections.Counter()
for c in allc:
    cs={(t//9 if t<27 else 3) for t in c}
    if len(cs)==1: per[list(cs)[0]]+=1
print("mono code usage m/p/s/z:", dict(per), "budgets 6561/6561/6561/2401")
