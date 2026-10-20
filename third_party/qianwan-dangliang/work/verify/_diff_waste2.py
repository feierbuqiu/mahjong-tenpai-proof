
import json
def mine_set(d):
    s = set()
    for e in d["waste_by_class"]:
        W = tuple(sorted(e["W"]))
        for c in e["codes"]:
            s.add((W, tuple(sorted(c))))
    return s
m = json.load(open("work/verify/waste_list_exact.json", encoding="utf-8"))
A = mine_set(m)
print("mine: count field", m["waste_count"], "sum codes", sum(len(e["codes"]) for e in m["waste_by_class"]), "set", len(A))
a = json.load(open("work/lowerbound/waste_list.json", encoding="utf-8"))
print("analyst keys:", {k: (str(v)[:60] if not isinstance(v, (list, dict)) else type(v).__name__ + " len " + str(len(v))) for k, v in a.items()})
print("analyst total:", a.get("total"))
cl = a["classes"]
print("analyst classes type:", type(cl).__name__)
if isinstance(cl, dict):
    k0 = list(cl.keys())[:1]
    print("  sample key:", k0, "value:", str(cl[k0[0]])[:200])
    B = set()
    for Wk, codes in cl.items():
        Wt = tuple(sorted(str(Wk).strip("[]'\"").split(","))) if isinstance(Wk, str) else tuple(sorted(Wk))
        for c in codes:
            B.add((Wt, tuple(sorted(c))))
else:
    print("  sample:", json.dumps(cl[0], ensure_ascii=False)[:200])
    B = set()
    for e in cl:
        W = tuple(sorted(e["W"])); 
        for c in e.get("codes", []): B.add((W, tuple(sorted(c))))
print("analyst set:", len(B))
only_mine = A - B; only_theirs = B - A
print("only mine:", len(only_mine), " only analyst:", len(only_theirs))
for x in list(only_mine)[:6]: print("   only mine:", x)
for x in list(only_theirs)[:6]: print("   only analyst:", x)
