# -*- coding: utf-8 -*-
"""t1c_cert_check.py -- verify the claimed lower-bound certificates row by row,
with our own engine.  Covers k3_disproof_certificate.json and certificate.json.
"""
import sys, os, json, hashlib, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjcore import *

D = os.path.dirname(os.path.abspath(__file__))
t0=time.time()
C = json.load(open("D:/DSH/MJ2/work/lowerbound/k3_disproof_certificate.json", encoding="utf-8"))
out = {"file": "k3_disproof_certificate.json", "keys": list(C.keys())}

U = tuple(range(1,8))
hands = list(multisets(13, U))
groups = {}
for h in hands:
    w = waits(h)
    if w: groups.setdefault(w, []).append(h)
myN = len(groups)
codes = sorted({tuple(t for t in U for _ in range(v[t])) for v in multisets(3, U)})
def fits(h,c):
    need={}
    for t in c: need[t]=need.get(t,0)+1
    return all(h[t]>=v for t,v in need.items())
myL = []
for w,hs in groups.items():
    if not any(all(fits(h,c) for h in hs) for c in codes):
        myL.append(w)
out["my_N"] = myN; out["my_L"] = len(myL)
out["cert_N"] = C["N"]; out["cert_L"] = C["L"]; out["cert_N_plus_L"] = C["N_plus_L"]
out["arithmetic_ok"] = (C["N"]==myN and C["L"]==len(myL) and C["N_plus_L"]==myN+len(myL) and C["N_plus_L"]>C["budget"])

# all_class_W
def ptile(s):
    if s in HON: return 27 + HON.index(s)
    if s[0].isdigit(): return MW.index(s[-1])*9 + int(s[0]) - 1
    if s[0] in MW: return MW.index(s[0])*9 + int(s[1:]) - 1
    raise ValueError(s)
def parse_Wfield(w):
    if isinstance(w, str): return frozenset(ptile(x) for x in w.split(","))
    return frozenset(ptile(x) for x in w)
cert_classes = set(parse_Wfield(wl) for wl in C["all_class_W"])
out["cert_all_class_W_len"] = len(C["all_class_W"])
out["class_set_equal"] = (cert_classes == set(groups.keys()))
out["missing_from_cert"] = [[nm(t) for t in sorted(w)] for w in set(groups.keys())-cert_classes][:10]
out["extra_in_cert"] = [[nm(t) for t in sorted(w)] for w in cert_classes-set(groups.keys())][:10]

# digest attempts
cands = {}
lst = C["all_class_W"]
cands["json_sorted_str"] = hashlib.sha256(json.dumps(sorted(lst), ensure_ascii=False).encode()).hexdigest()
cands["json_sorted_ascii"] = hashlib.sha256(json.dumps(sorted(lst)).encode()).hexdigest()
cands["lines"] = hashlib.sha256(("\n".join(",".join(sorted(w)) for w in sorted(lst))).encode()).hexdigest()
cands["lines_mine"] = hashlib.sha256(("\n".join(",".join(nm(t) for t in sorted(w)) for w in sorted(groups.keys(), key=lambda s: sorted(s)))).encode()).hexdigest()
out["digest_target"] = C["class_list_digest_sha256"]
out["digest_attempts"] = cands
out["digest_matched"] = [k for k,v in cands.items() if v==C["class_list_digest_sha256"]]

# L_classes blockers
bad=[]
for e in C["L_classes"]:
    W = parse_Wfield(e["W"])
    n_ok = True
    if W not in groups:
        bad.append({"W":e["W"],"err":"class not in my class set"}); continue
    if e.get("class_size") != len(groups[W]):
        bad.append({"W":e["W"],"err":"class_size %r vs mine %d" % (e.get("class_size"), len(groups[W]))}); n_ok=False
    seen_codes=set()
    for b in e["blockers"]:
        code = tuple(sorted(ptile(x) for x in b["code"]))
        hh = [0]*34
        for (t,c) in b["hand"]:
            hh[ptile(t)] = c
        hh=tuple(hh)
        seen_codes.add(code)
        if sum(hh)!=13 or max(hh)>4 or any(hh[t] for t in range(34) if t not in U):
            bad.append({"W":e["W"],"err":"invalid blocker hand","hand":b["hand"]}); continue
        if waits(hh) != W:
            bad.append({"W":e["W"],"err":"blocker hand not in class","hand":b["hand"],"W_hand":[nm(t) for t in sorted(waits(hh))]}); continue
        if all(hh[t]>=v for t,v in __import__("collections").Counter(code).items()):
            bad.append({"W":e["W"],"err":"blocker hand CONTAINS the code","code":b["code"],"hand":b["hand"]})
    if set(codes) - seen_codes:
        bad.append({"W":e["W"],"err":"blockers do not cover all 84 codes","missing":len(set(codes)-seen_codes)})
out["L_class_checks"] = len(C["L_classes"])
out["L_class_bad"] = bad[:20]
out["L_class_bad_count"] = len(bad)
out["myL_equals_certL_set"] = (set(myL) == set(parse_Wfield(e["W"]) for e in C["L_classes"]))

json.dump(out, open(D+"/t1c_k3cert.json","w"), ensure_ascii=False, indent=1)
for k,v in out.items():
    if k in ("digest_attempts","missing_from_cert","extra_in_cert","L_class_bad"): continue
    print(k,"=",v)
print("digest matched:", out["digest_matched"])
print("bad rows:", json.dumps(out["L_class_bad"][:5], ensure_ascii=False)[:800])
print("elapsed %.0fs"%(time.time()-t0))
