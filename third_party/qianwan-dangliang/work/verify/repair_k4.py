#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 plan_k4_merged.json 的『同一有序码被多类使用』修复为全局唯一有序码。
原理: 覆盖只依赖码的多重集; 同一多重集的任一未使用排列都可替换, 覆盖完全不变。
输出 work/verify/plan_k4_repaired.json
"""
import json, sys, collections, itertools

HON = {"E": 27, "S": 28, "W": 29, "N": 30, "Haku": 31, "Hatsu": 32, "Chun": 33}
def to_idx(w):
    if isinstance(w, int): return [t for t in range(34) if (w >> t) & 1]
    out = []
    for nm in w:
        if isinstance(nm, int): out.append(nm)
        elif nm in HON: out.append(HON[nm])
        else: out.append("mps".index(nm[-1]) * 9 + int(nm[0]) - 1)
    return out

src = sys.argv[1] if len(sys.argv) > 1 else "work/recon/plan_k4_merged.json"
p = json.load(open(src, encoding="utf-8"))
rows = p["plan"]
used = set()
out_rows = []
reassigned = 0
fail = 0
for r in rows:
    W = to_idx(r["W"])
    new_codes = []
    for c in r["codes"]:
        ct = tuple(c)
        if ct not in used:
            used.add(ct); new_codes.append(list(ct)); continue
        m = tuple(sorted(ct))
        cand = None
        for pm in itertools.permutations(sorted(set(m)), len(m)):
            # 去重的排列生成: 用 set(permutations) 更慢, 这里用 multiset 排列
            pass
        for pm in sorted(set(itertools.permutations(m))):
            if pm not in used:
                cand = pm; break
        if cand is None:
            fail += 1
            new_codes.append(list(ct))     # 多重集容量耗尽(极端), 原样保留
        else:
            used.add(cand); new_codes.append(list(cand)); reassigned += 1
    out_rows.append({"W": r["W"], "codes": new_codes, "modes": r.get("modes", [])})
out = {"k": p.get("k", 4), "n_classes": len(out_rows), "n_codes": sum(len(r["codes"]) for r in out_rows),
       "plan": out_rows, "source": src, "permutation_reassignments": reassigned,
       "multiset_capacity_failures": fail}
json.dump(out, open("work/verify/plan_k4_repaired.json", "w"), ensure_ascii=False)
print("classes", len(out_rows), "codes", out["n_codes"], "distinct ordered", len(used),
      "perm-reassignments", reassigned, "capacity-failures", fail)
# 复核
own = collections.Counter()
for r in out_rows:
    for c in r["codes"]: own[tuple(c)] += 1
print("ordered codes reused>1:", sum(1 for v in own.values() if v > 1))
zero = sum(1 for r in out_rows if not r["codes"])
print("zero-code classes:", zero)
# 多重集多重度检查
ms = collections.Counter()
for r in out_rows:
    for c in r["codes"]: ms[tuple(sorted(c))] += 1
over = {m: k for m, k in ms.items() if k > len(set(itertools.permutations(m)))}
print("multisets over permutation capacity:", len(over))
