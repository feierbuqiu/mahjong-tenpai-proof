
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
def cat(t):
    return 0 if t < 9 else 1 if t < 18 else 2 if t < 27 else 3
for path in ("work/recon/plan_k4_u9.json", "work/recon/plan_k4_u7.json"):
    p = json.load(open(path, encoding="utf-8"))
    used = set()
    for r in p["plan"]:
        for c in r["codes"]: used.add(tuple(c))
    pools = {"m": 9**4, "p": 9**4, "s": 9**4, "z": 7**4}
    names = "mpsz"
    cnt = collections.Counter()
    mixed = 0
    for c in used:
        cats = set(cat(t) for t in c)
        if len(cats) == 1: cnt[names[list(cats)[0]]] += 1
        else: mixed += 1
    print(path, "| total codes", len(used), "| per-suit local:", {k: (cnt[k], pools[k]) for k in "mpsz"}, "| mixed", mixed)
