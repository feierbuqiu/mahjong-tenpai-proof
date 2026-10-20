
import json
from collections import Counter
mine = json.load(open("work/verify/census_strict.json", encoding="utf-8"))
mine = [frozenset(x) for x in mine]
theirs_d = json.load(open("work/data/out/global.json", encoding="utf-8"))
print("their n_classes:", theirs_d["n_classes"], "by_size:", theirs_d["by_size"])
print("their extra keys:", {k: (str(v)[:200]) for k, v in theirs_d.items() if k not in ("classes",)})
cls = theirs_d["classes"]
print("their classes type:", type(cls), (len(cls) if hasattr(cls,'__len__') else ''))
if isinstance(cls, dict):
    k0 = list(cls.keys())[:2]
    print("sample:", {k: str(cls[k])[:200] for k in k0})
    theirs = set()
    for k, v in cls.items():
        if isinstance(v, list) and all(isinstance(x, int) for x in v):
            theirs.add(frozenset(v))
        elif isinstance(v, dict):
            w = v.get("W") or v.get("w") or v.get("tiles")
            if w is not None: theirs.add(frozenset(w))
    print("parsed theirs:", len(theirs))
else:
    theirs = set(frozenset(x) for x in cls)
    print("parsed theirs:", len(theirs))
print("mine:", len(mine), "size dist:", dict(sorted(Counter(len(W) for W in mine).items())))
print("theirs size dist:", dict(sorted(Counter(len(W) for W in theirs).items())))
only_mine = set(mine) - theirs; only_theirs = theirs - set(mine)
print("only mine:", len(only_mine), "only theirs:", len(only_theirs))
print("sample only_mine:", [sorted(x) for x in list(only_mine)[:8]])
print("sample only_theirs:", [sorted(x) for x in list(only_theirs)[:8]])
