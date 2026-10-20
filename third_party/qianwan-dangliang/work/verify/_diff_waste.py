
import json, os
mine = json.load(open("work/verify/waste_list_exact.json", encoding="utf-8"))
print("mine: waste_count", mine["waste_count"], "classes", len(mine["waste_by_class"]), "audit", mine["audit"])
def norm(entry_list):
    s = set()
    for e in entry_list:
        W = tuple(sorted(e["W"])) if isinstance(e.get("W"), list) else None
        for c in e["codes"]:
            s.add((W, tuple(sorted(c))))
    return s
A = norm(mine["waste_by_class"])
print("mine set size:", len(A))
for path in ("work/lowerbound/waste_list.json", "work/lowerbound/waste_list_exact.json"):
    if not os.path.exists(path): print(path, "missing"); continue
    d = json.load(open(path, encoding="utf-8"))
    print(path, "type", type(d).__name__, "keys", list(d.keys())[:8] if isinstance(d, dict) else len(d))
    if isinstance(d, dict):
        for k, v in list(d.items())[:4]:
            print("   ", k, type(v).__name__, (len(v) if hasattr(v, "__len__") else v))
    break
