
import json, itertools, collections
P = json.load(open("work/recon/plan_k4_u20.json", encoding="utf-8"))
rows = P["plan"]
used = set()
for r in rows:
    for c in r["codes"]: used.add(tuple(c))
ms = collections.Counter(tuple(sorted(c)) for c in used)
free_total = 0; ms_with_free = 0
for m, k in ms.items():
    p = len(set(itertools.permutations(m)))
    if p > k:
        ms_with_free += 1; free_total += (p - k)
print("total ordered codes used:", len(used))
print("distinct multisets used:", len(ms))
print("multisets with UNUSED permutations:", ms_with_free, " total unused permutations:", free_total)
# 其中"仍有自由排列"的多重集里, 最常用的几个
top = sorted(((m, k, len(set(itertools.permutations(m)))) for m, k in ms.items() if len(set(itertools.permutations(m))) > k),
             key=lambda x: -(x[2]-x[1]))[:8]
HON = {"E": 27, "S": 28, "W": 29, "N": 30, "Haku": 31, "Hatsu": 32, "Chun": 33}
HONN = ["E","S","W","N","Haku","Hatsu","Chun"]
NM = lambda t: ("%d%s" % (t%9+1, "mps"[t//9])) if t < 27 else HONN[t-27]
for m, k, p in top:
    print("   multiset", [NM(t) for t in m], "used", k, "/", p, "free", p-k)
