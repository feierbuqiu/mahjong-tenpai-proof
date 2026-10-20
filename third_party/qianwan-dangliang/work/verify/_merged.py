
import json, collections
HON = {"E": 27, "S": 28, "W": 29, "N": 30, "Haku": 31, "Hatsu": 32, "Chun": 33}
def to_idx(w):
    if isinstance(w, int): return [t for t in range(34) if (w >> t) & 1]
    out=[]
    for nm in w:
        if isinstance(nm, int): out.append(nm)
        elif nm in HON: out.append(HON[nm])
        else: out.append("mps".index(nm[-1])*9 + int(nm[0]) - 1)
    return out
mine = set(frozenset(x) for x in json.load(open("work/verify/census_strict.json", encoding="utf-8")))
p = json.load(open("work/recon/plan_k4_merged.json", encoding="utf-8"))
plancls = {frozenset(to_idx(r["W"])): [tuple(c) for c in r["codes"]] for r in p["plan"]}
zero = [W for W, cs in plancls.items() if not cs]
own = collections.defaultdict(list)
for W, cs in plancls.items():
    for c in cs: own[c].append(W)
dups = {c: ws for c, ws in own.items() if len(ws) > 1}
print("classes", len(plancls), "missing", len(mine - set(plancls)), "extra", len(set(plancls)-mine))
print("zero-code classes", len(zero), [sorted(W) for W in zero])
print("total codes", sum(len(v) for v in plancls.values()), "distinct ordered", len(own), "duplicated ordered codes", len(dups),
      "extra uses", sum(len(v)-1 for v in dups.values()))
# 对有重复码的类: 去掉重复码(只留一个 owner)后是否还有码
for c, ws in list(dups.items())[:5]:
    print("  code", c, "used by", len(ws), "classes; sizes", [len(plancls[w]) for w in ws])
