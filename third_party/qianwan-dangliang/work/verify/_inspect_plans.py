
import json
from collections import defaultdict
for path in ("work/recon/lead_plan_k3.json", "work/strategy/out/plan.json"):
    p = json.load(open(path, encoding="utf-8"))
    rows = p["plan"] if isinstance(p, dict) and "plan" in p else p
    print("===", path, "rows", len(rows))
    print("row0:", json.dumps(rows[0], ensure_ascii=False)[:300])
    print("row1:", json.dumps(rows[1], ensure_ascii=False)[:300])
    c2w = defaultdict(list)
    for r in rows:
        W = r["W"] if not isinstance(r["W"], int) else r["W"]
        for c in r["codes"]:
            c2w[tuple(sorted(c))].append(W)
    multi = [(c, ws) for c, ws in c2w.items() if len(ws) > 1]
    print("codes used in >1 class:", len(multi))
    for c, ws in multi[:3]:
        print("  code", c, "classes:", ws[:3])
    # 是否同一个 W 出现在多行?
    ws_all = [tuple(sorted(r["W"])) if isinstance(r["W"], list) else r["W"] for r in rows]
    print("distinct W rows:", len(set(ws_all)))
