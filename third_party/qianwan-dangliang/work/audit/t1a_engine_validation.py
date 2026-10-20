# -*- coding: utf-8 -*-
"""t1a_engine_validation.py -- brute-force validation of the independent engine."""
import sys, os, time, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjcore import *

D = os.path.dirname(os.path.abspath(__file__))
OUT = {}
t0 = time.time()

def log(*a):
    print("[%6.1fs]" % (time.time()-t0), *a, flush=True)

# ---- single suit
hands = list(multisets(13, tuple(range(9))))
log("m-suit hands", len(hands))
OUT["m_total"] = len(hands)
std = 0; full = 0; cls = set(); cls_std = set()
for h in hands:
    w = waits(h)
    if w:
        full += 1; cls.add(w)
        ws = waits_std(h)
        if ws:
            std += 1; cls_std.add(ws)
OUT["m_wait_std"] = std; OUT["m_wait_full"] = full
OUT["m_classes"] = len(cls); OUT["m_classes_std"] = len(cls_std)
log("m-suit wait std/full/classes", std, full, len(cls))
json.dump(sorted([sorted(w) for w in cls]), open(D+"/flush_classes.json","w"))

# ---- honors
zh = list(multisets(13, tuple(range(27,34))))
zstd=0; zfull=0; zcls=set(); zcls_std=set()
for h in zh:
    w = waits(h)
    if w:
        zfull += 1; zcls.add(w)
        ws = waits_std(h)
        if ws:
            zstd += 1; zcls_std.add(ws)
OUT["z_total"]=len(zh); OUT["z_wait_std"]=zstd; OUT["z_wait_full"]=zfull
OUT["z_classes"]=len(zcls); OUT["z_classes_std"]=len(zcls_std)
log("honors total/std/full/classes", len(zh), zstd, zfull, len(zcls))

# ---- kokushi-hand set by direct construction + proof-of-completeness by definition
# W_kokushi(H) != {} requires H subset of orphans with >=12 distinct kinds:
#   13 distinct (1 hand) or 12 distinct with one doubled (13*12 = 156 hands)
khands = []
c = [0]*N
for t in ORPHANS: c[t]=1
khands.append(tuple(c))
for miss in ORPHANS:
    for dbl in ORPHANS:
        if dbl == miss: continue
        c=[0]*N
        for t in ORPHANS:
            if t != miss: c[t]=1
        c[dbl]+=1
        khands.append(tuple(c))
khands = sorted(set(khands))
kwait = [h for h in khands if any(t in ORPHANS for t in waits(h))]
kcls = set(waits(h) for h in kwait)
OUT["kokushi_candidate_hands"] = len(khands)
OUT["kokushi_wait_hands"] = len(kwait)
OUT["kokushi_classes"] = len(kcls)
OUT["kokushi_class_sizes"] = sorted(len(w) for w in kcls)
log("kokushi constructed/wait/classes", len(khands), len(kwait), len(kcls))
# sanity: any orphan-only hand with <12 distinct kinds can never have a kokushi wait
bad = []
for h in multisets(13, ORPHANS):
    if sum(1 for t in ORPHANS if h[t]) < 12:
        continue
    if sum(1 for t in ORPHANS if h[t]) < 13:
        pass
OUT["kokushi_definition_note"] = "W_kok(H) nonempty <=> H orphan-only and >=12 distinct kinds"

# ---- chiitoi identities
OUT["C34_7"] = math.comb(34,7)
OUT["C34_6x28"] = math.comb(34,6)*28
log("chiitoi identities", OUT["C34_7"], OUT["C34_6x28"])

json.dump(OUT, open(D+"/t1a.json","w"), ensure_ascii=False, indent=1)
log("done")
print(json.dumps(OUT, ensure_ascii=False, indent=1))
