
import sys, pickle, os
sys.path.insert(0, "work/strategy")
for p in ("work/strategy/out/table_cache.pkl", "work/recon/table_perA.pkl"):
    if not os.path.exists(p): print(p, "missing"); continue
    try:
        d = pickle.load(open(p, "rb"))
    except Exception as e:
        print(p, "LOAD FAIL", e); continue
    print("===", p, type(d).__name__, list(d.keys())[:8] if isinstance(d, dict) else "")
    for k in list(d.keys()):
        v = d[k]
        print("   ", k, type(v).__name__, len(v) if hasattr(v, "__len__") else "")
        if isinstance(v, dict):
            kk = list(v.keys())[:2]
            for x in kk:
                print("      key", x, "->", type(v[x]).__name__, str(v[x])[:220])
    break
