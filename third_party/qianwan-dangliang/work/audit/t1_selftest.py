# -*- coding: utf-8 -*-
"""t1_selftest.py -- validate the independent engine against brute-force counts
and reproduce the reported sub-universe numbers."""
import sys, os, time, json
from itertools import combinations_with_replacement
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjcore import *

OUT = {}
t0 = time.time()

# ---- 1. single suit (m) enumeration
def enumerate_universe(kinds):
    hands = list(multisets(13, kinds))
    return hands

m_kinds = tuple(range(9))
hands = enumerate_universe(m_kinds)
OUT["m_suit_total_13_multisets"] = len(hands)
std = [] ; full = []
cls_std = set(); cls_full = set()
for h in hands:
    w = waits(h)
    if w:
        full.append(h)
        cls_full.add(w)
        ws = waits_std(h)
        if ws:
            std.append(h); cls_std.add(ws)
OUT["m_suit_wait_std"] = len(std)
OUT["m_suit_wait_full"] = len(full)
OUT["m_suit_classes"] = len(cls_full)
OUT["m_suit_classes_std"] = len(cls_std)
OUT["m_suit_chiitoi_only"] = len(full) - len(std)
print("m-suit:", OUT["m_suit_total_13_multisets"], OUT["m_suit_wait_std"], OUT["m_suit_wait_full"], OUT["m_suit_classes"])
json.dump(sorted([sorted(w) for w in cls_full]), open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"flush_classes.json"),"w"))

# ---- 2. honors
z_kinds = tuple(range(27,34))
zh = enumerate_universe(z_kinds)
zstd=0; zfull=0; zcls=set(); zcls_std=set()
for h in zh:
    w = waits(h)
    if w:
        zfull += 1; zcls.add(w)
        if waits_std(h):
            zstd += 1; zcls_std.add(waits_std(h))
OUT["z_total"] = len(zh); OUT["z_wait_std"] = zstd; OUT["z_wait_full"] = zfull
OUT["z_classes"] = len(zcls); OUT["z_classes_std"] = len(zcls_std)
print("honors:", len(zh), zstd, zfull, len(zcls))

# ---- 3. kokushi
kh = [h for h in multisets(13, ORPHANS) if any(True for t in ORPHANS)]
kfull = [h for h in kh if waits(h)]
kcls = set(waits(h) for h in kfull)
OUT["kokushi_hands_all"] = len(kh)
OUT["kokushi_hands_wait"] = len(kfull)
OUT["kokushi_classes"] = len(kcls)
print("kokushi:", len(kh), len(kfull), len(kcls))

# ---- 4. chiitoi counting identity
import math
OUT["chiitoi_wins_C(34,7)"] = math.comb(34,7)
OUT["chiitoi_wait_hands_C(34,6)*28"] = math.comb(34,6)*28

# ---- 5. U7 = {m2..m8}
U7 = tuple(range(1,8))
u_hands = [h for h in multisets(13, U7)]
print("U7 hands:", len(u_hands))
groups = {}
for h in u_hands:
    w = waits(h)
    if w:
        groups.setdefault(w, []).append(h)
N_u = len(groups)
OUT["U7_hands"] = len(u_hands)
OUT["U7_N"] = N_u
# common 3-code per class
codes3 = [c for c in multisets(3, U7)]
L_u = 0; no_common = []
for w, hs in groups.items():
    found = None
    for c in codes3:
        if all(contains_any(h, [c]) for h in hs):
            found = c; break
    if found is None:
        L_u += 1
        no_common.append([nm(t) for t in sorted(w)])
OUT["U7_L"] = L_u
OUT["U7_bound"] = N_u + L_u
print("U7: N=%d L=%d sum=%d vs 343" % (N_u, L_u, N_u+L_u))
json.dump(OUT, open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"t1_selftest.json"),"w"), ensure_ascii=False, indent=1)
json.dump(no_common, open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"U7_no_common_classes.json"),"w"), ensure_ascii=False)
print("elapsed %.1fs" % (time.time()-t0))
print(json.dumps(OUT, ensure_ascii=False, indent=1))
