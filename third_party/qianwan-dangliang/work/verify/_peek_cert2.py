
import json
c = json.load(open("work/lowerbound/k3_disproof_certificate.json", encoding="utf-8"))
print("keys:", list(c.keys()))
for k, v in c.items():
    if isinstance(v, list): print(" ", k, "list len", len(v), "sample:", json.dumps(v[0], ensure_ascii=False)[:200] if v else "")
    elif isinstance(v, dict): print(" ", k, "dict keys", list(v.keys())[:6])
    else: print(" ", k, "=", str(v)[:80])
lc = c.get("L_classes") or c.get("l_classes") or c.get("blockers")
if lc: print("L sample:", json.dumps(lc[0] if isinstance(lc, list) else list(lc.items())[0], ensure_ascii=False)[:600])
