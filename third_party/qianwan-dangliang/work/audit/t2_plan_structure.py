# -*- coding: utf-8 -*-
"""t2_plan_structure.py -- structural audit of plan_k4_FINAL.json, independent of any
team script.  Verifies:
  * class keys unique, count matches n_classes
  * codes: length 4, valid tiles, multiplicity <=4, sorted-or-not
  * global uniqueness of codes (ordered tuples AND multisets) = disjointness condition
  * every class in the plan is non-empty and every code is realisable-in-principle
  * cross-checks the 3 "removed_unusable" codes
"""
import sys, os, json, hashlib, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjcore import *

D = os.path.dirname(os.path.abspath(__file__))
P = json.load(open("D:/DSH/MJ2/work/verify/plan_k4_FINAL.json", encoding="utf-8"))
raw = open("D:/DSH/MJ2/work/verify/plan_k4_FINAL.json","rb").read()
print("sha256:", hashlib.sha256(raw).hexdigest())
print("declared:", json.load(open("D:/DSH/MJ2/work/verify/final_certificate.json",encoding="utf-8"))["plan"]["sha256"])

rep = {}
plan = P["plan"]
rep["n_classes_declared"] = P["n_classes"]
rep["n_codes_declared"] = P["n_codes"]
rep["n_classes_actual"] = len(plan)
rep["n_codes_actual"] = sum(len(r["codes"]) for r in plan)

keys = []
all_ord = collections.Counter()
all_set = collections.Counter()
errors = []
class_of_code = {}
for r in plan:
    W = frozenset(nm_idx(x) for x in r["W"])
    keys.append(W)
    for c in r["codes"]:
        if len(c) != 4: errors.append(("codelen", W, c)); continue
        idx = tuple(nm_idx(x) for x in c)
        cnt = collections.Counter(idx)
        if max(cnt.values()) > 4: errors.append(("mult4", W, c))
        all_ord[idx] += 1
        all_set[tuple(sorted(idx))] += 1
        class_of_code.setdefault(idx, []).append(W)
rep["unique_class_keys"] = len(set(keys)) == len(keys)
rep["class_keys_dupes"] = len(keys) - len(set(keys))
rep["errors"] = errors[:20]
rep["num_errors"] = len(errors)
rep["ordered_codes_distinct"] = len(all_ord)
rep["ordered_dup_count"] = sum(v-1 for v in all_ord.values() if v > 1)
rep["multiset_codes_distinct"] = len(all_set)
rep["multiset_dup_count"] = sum(v-1 for v in all_set.values() if v > 1)
rep["sorted_always"] = all(tuple(c) == tuple(sorted(c)) for r in plan for c in map(lambda x: tuple(nm_idx(y) for y in x), r["codes"]))
dup_examples = [x for x,v in all_ord.items() if v>1][:10]
rep["ordered_dup_examples"] = [[nm(t) for t in x] for x in dup_examples]
mdup = [x for x,v in all_set.items() if v>1][:10]
rep["multiset_dup_examples"] = [[nm(t) for t in x] for x in mdup]

# per-class code counts
sizes = sorted(len(r["codes"]) for r in plan)
rep["codes_per_class_min"] = sizes[0]; rep["codes_per_class_max"] = sizes[-1]
rep["codes_per_class_sum"] = sum(sizes)
rep["classes_with_zero_codes"] = sum(1 for s in sizes if s==0)

# the 3 removed codes: check they are NOT needed (i.e. absent from the plan)
removed = P.get("removed_unusable", [])
rep["removed"] = []
for r in removed:
    W = frozenset(nm_idx(x) for x in r["W"])
    for c in r["codes"]:
        idx = tuple(sorted(nm_idx(x) for x in c))
        rep["removed"].append({"W": [nm(t) for t in sorted(W)], "code": [nm(t) for t in idx],
                               "also_used_by": len(class_of_code.get(tuple(nm_idx(x) for x in c), []))})
    # is the class still present and still has codes?
    hit = [q for q in plan if frozenset(nm_idx(x) for x in q["W"]) == W]
    rep["removed"][-1]["class_present"] = bool(hit)
    rep["removed"][-1]["class_code_count"] = len(hit[0]["codes"]) if hit else None

# class key distribution by |W| and category composition
wsize = collections.Counter(len(k) for k in keys)
rep["W_size_hist"] = dict(sorted(wsize.items()))
rep["n_classes_with_W_size13"] = wsize.get(13,0)

json.dump({k:v for k,v in rep.items()}, open(D+"/t2_plan_structure.json","w"), ensure_ascii=False, indent=1)
for k,v in rep.items():
    if k in ("errors","ordered_dup_examples","multiset_dup_examples","removed"): continue
    print(k, "=", v)
print("removed:", json.dumps(rep["removed"], ensure_ascii=False))
print("errors:", rep["errors"][:5])
