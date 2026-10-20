
import pickle, json, os
for p in ("work/strategy/out/table_cache.pkl", "work/recon/table_perA.pkl"):
    if not os.path.exists(p): print(p, "missing"); continue
    d = pickle.load(open(p, "rb"))
    print("===", p, type(d), list(d.keys())[:8] if isinstance(d, dict) else "")
    for k in list(d.keys())[:6]:
        v = d[k]
        t = type(v).__name__
        n = len(v) if hasattr(v, "__len__") else ""
        print("   ", k, t, n)
        if isinstance(v, dict):
            kk = list(v.keys())[:2]
            for x in kk:
                print("      key", x, "->", type(v[x]).__name__, str(v[x])[:180])
    break
