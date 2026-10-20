
import json, collections, sys
for path in ("work/recon/k4_subuniverse_covers.json", "work/recon/k4_cross_covers.json",
             "work/recon/k4_nine_covers.json", "work/recon/plan_k4_merged.json"):
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        print(path, "LOAD FAIL", e); continue
    print("===", path, type(d).__name__)
    if isinstance(d, dict):
        for k, v in list(d.items())[:6]:
            print("   key", repr(k)[:40], type(v).__name__, (len(v) if hasattr(v, "__len__") else v))
            if isinstance(v, list) and v: print("      sample:", json.dumps(v[0], ensure_ascii=False)[:200])
            elif isinstance(v, dict):
                kk = list(v.keys())[:1]
                print("      sample:", kk, json.dumps(v[kk[0]], ensure_ascii=False)[:200] if kk else "")
    elif isinstance(d, list):
        print("   len", len(d), "sample:", json.dumps(d[0], ensure_ascii=False)[:250])
