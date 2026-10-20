
import json, sys, collections
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
p = json.load(open("work/strategy/out/plan_k4.json", encoding="utf-8"))
rows = p["plan"] if isinstance(p, dict) and "plan" in p else p
print("top keys:", list(p.keys())[:8] if isinstance(p, dict) else "list")
print("k meta:", p.get("k") if isinstance(p, dict) else None, "fails:", len(p.get("fails", [])) if isinstance(p, dict) else 0)
plancls = {}
dup = 0
for r in rows:
    W = frozenset(to_idx(r["W"]))
    if W in plancls: dup += 1
    plancls[W] = [tuple(c) for c in r["codes"]]
zero = sum(1 for cs in plancls.values() if not cs)
ordered = collections.Counter(); multisets = collections.Counter()
for cs in plancls.values():
    for c in cs: ordered[c] += 1; multisets[tuple(sorted(c))] += 1
perms = lambda m: 1 if len(set(m)) == 1 else (3 if len(set(m)) == 2 else 6)
print("HARD CHECKS for plan_k4.json")
print(" classes:", len(plancls), " duplicate W rows:", dup)
print(" class set == verifier 2846:", plancls.keys() == mine, " missing:", len(mine - set(plancls)), " extra:", len(set(plancls) - mine))
print(" zero-code classes:", zero)
print(" total codes:", sum(len(v) for v in plancls.values()), " distinct ordered:", len(ordered))
print(" ordered codes reused >1:", sum(1 for v in ordered.values() if v > 1))
print(" multiset over perm-capacity:", sum(1 for m, k in multisets.items() if k > perms(m)))
print(" invalid codes (bad len/mult>4):", sum(1 for cs in plancls.values() for c in cs if len(c) != 4 or any(c.count(t) > 4 for t in set(c))))
print(" max codes per class:", max(len(cs) for cs in plancls.values()))
