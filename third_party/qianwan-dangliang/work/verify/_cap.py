
import json, collections, itertools
HON = {"E": 27, "S": 28, "W": 29, "N": 30, "Haku": 31, "Hatsu": 32, "Chun": 33}
def to_idx(w):
    if isinstance(w, int): return [t for t in range(34) if (w >> t) & 1]
    out=[]
    for nm in w:
        if isinstance(nm, int): out.append(nm)
        elif nm in HON: out.append(HON[nm])
        else: out.append("mps".index(nm[-1])*9 + int(nm[0]) - 1)
    return out
p = json.load(open("work/recon/plan_k4_merged.json", encoding="utf-8"))
plancls = {frozenset(to_idx(r["W"])): [tuple(c) for c in r["codes"]] for r in p["plan"]}
ms = collections.Counter()
for W, cs in plancls.items():
    for c in cs: ms[tuple(sorted(c))] += 1
over = {m: k for m, k in ms.items() if k > len(set(itertools.permutations(m)))}
print("over-capacity multisets:", len(over), " affected code entries:", sum(k - len(set(itertools.permutations(m))) for m, k in over.items()))
# 受影响类
affected = collections.Counter()
wpk = collections.defaultdict(list)
for W, cs in plancls.items():
    for c in cs:
        if tuple(sorted(c)) in over: affected[W] += 1
print("classes holding over-capacity codes:", len(affected))
print("classes whose ALL codes are over-capacity:", sum(1 for W, cs in plancls.items() if cs and all(tuple(sorted(c)) in over for c in cs)))
# 分布: 这些类的 W 跨类别数
from collections import Counter
def ncat(W): return len(set(0 if t<9 else 1 if t<18 else 2 if t<27 else 3 for t in W))
print("ncat dist of affected:", dict(Counter(ncat(W) for W in affected)))
print("top over-capacity multisets (multiset, used, capacity):")
for m, k in sorted(over.items(), key=lambda kv: -(kv[1]))[:6]:
    print("   ", m, k, len(set(itertools.permutations(m))))
