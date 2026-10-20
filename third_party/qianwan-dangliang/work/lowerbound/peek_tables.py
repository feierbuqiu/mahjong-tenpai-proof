import pickle, sys, os, json, collections
sys.stdout.reconfigure(encoding="utf-8")
for p in ("work/recon/table_perA.pkl","work/strategy/out/table_cache.pkl"):
    if not os.path.exists(p): print(p, "NOT FOUND"); continue
    try:
        d = pickle.load(open(p,"rb"))
        print(p, "loaded:", type(d), list(d.keys())[:10] if isinstance(d,dict) else "")
        if isinstance(d,dict):
            for kk in list(d.keys())[:8]:
                v = d[kk]
                print("   key", kk, "->", type(v), (len(v) if hasattr(v,'__len__') else ""))
            if "PROFI_D" in d:
                k0 = list(d["PROFI_D"].keys())[:2]
                for kk in k0:
                    am, xs = d["PROFI_D"][kk]
                    print("   PROFI_D[", kk, "] am sum", sum(am), "xs len", len(xs), "sample xs", xs[:2])
            if "PROFII_D" in d:
                k0 = list(d["PROFII_D"].keys())[:2]
                for kk in k0:
                    am, xs = d["PROFII_D"][kk]
                    print("   PROFII_D[", kk, "] am sum", sum(am), "xs len", len(xs), "sample xs", xs[:2])
    except Exception as e:
        print(p, "load err", e)
