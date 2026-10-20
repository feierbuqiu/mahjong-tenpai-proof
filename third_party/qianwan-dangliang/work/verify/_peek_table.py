
import pickle, sys
p = "work/strategy/out/table.pkl"
d = pickle.load(open(p, "rb"))
print("top type:", type(d))
if isinstance(d, dict):
    for k, v in d.items():
        t = type(v).__name__
        n = len(v) if hasattr(v, "__len__") else ""
        print("  key:", repr(k)[:40], t, "len", n)
        if isinstance(v, dict):
            ks = list(v.keys())[:3]
            print("     sample keys:", [repr(x)[:70] for x in ks])
            for x in ks[:1]:
                print("     sample val:", repr(v[x])[:300])
        elif isinstance(v, (list, tuple)):
            print("     sample:", repr(v[:2])[:300])
