#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对 plan_k4 给出【需要修的类清单】(按未覆盖手牌数排序) + 精确缺口."""
import json, sys, collections
sys.path.insert(0, "work/verify")
from indep_core import compute_W, gen_vectors
HON = {"E": 27, "S": 28, "W": 29, "N": 30, "Haku": 31, "Hatsu": 32, "Chun": 33}
def to_idx(w):
    if isinstance(w, int): return [t for t in range(34) if (w >> t) & 1]
    out=[]
    for nm in w:
        if isinstance(nm, int): out.append(nm)
        elif nm in HON: out.append(HON[nm])
        else: out.append("mps".index(nm[-1])*9 + int(nm[0]) - 1)
    return out
plan = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "work/strategy/out/plan_k4.json", encoding="utf-8"))
plancls = {frozenset(to_idx(r["W"])): [tuple(c) for c in r["codes"]] for r in plan["plan"]}
def contains(h, c):
    need={}
    for t in c: need[t]=need.get(t,0)+1
    return all(h[t]>=v for t,v in need.items())
NM = lambda t: ("%d%s" % (t%9+1, "mps"[t//9])) if t < 27 else ["E","S","W","N","Haku","Hatsu","Chun"][t-27]
suits = {"m": (9,0), "p": (9,9), "s": (9,18), "z": (7,27)}
out = {"zero_code_classes": sorted([sorted(W) for W, cs in plancls.items() if not cs]),
       "suits": {}, "total_uncovered_in_coded_classes": 0}
for name, (K, off) in suits.items():
    per_class = collections.Counter()
    hands_by_class = collections.Counter()
    for h in gen_vectors(K, 13):
        c=[0]*34
        for i,x in enumerate(h):
            if x: c[off+i]=x
        W = compute_W(c)
        if not W: continue
        key = frozenset(W)
        hands_by_class[key] += 1
        cs = plancls.get(key)
        if not cs: continue          # 空码类单独统计
        if not any(contains(c, code) for code in cs): per_class[key] += 1
    out["suits"][name] = {"classes_with_failures": len(per_class),
                          "uncovered_hands_total": sum(per_class.values()),
                          "total_listening": sum(hands_by_class.values()),
                          "top": [{"W": [NM(t) for t in sorted(W)], "uncovered": n, "class_size": hands_by_class[W],
                                   "n_codes": len(plancls[W]),
                                   "has_local_code": any(all(off <= t < off + K for t in code) for code in plancls[W])}
                                  for W, n in per_class.most_common(12)]}
    out["total_uncovered_in_coded_classes"] += sum(per_class.values())
    print(name, "classes_with_failures", len(per_class), "uncovered", sum(per_class.values()), flush=True)
    for t in out["suits"][name]["top"][:6]: print("   ", t, flush=True)
print("zero-code classes:", len(out["zero_code_classes"]))
print("total uncovered hands in coded classes:", out["total_uncovered_in_coded_classes"])
json.dump(out, open("work/verify/k4_gap_classes.json", "w"), ensure_ascii=False, indent=1)
