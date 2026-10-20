#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_k3_disproof.py -- 独立重放 k=3 否证证书 (U={m2..m8})."""
import json, sys, os, itertools, hashlib
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from indep_core import compute_W, gen_vectors
HONN = ["E", "S", "W", "N", "Haku", "Hatsu", "Chun"]
HOND = {n: 27 + i for i, n in enumerate(HONN)}
NM = lambda t: ("%s%d" % ("mps"[t // 9], t % 9 + 1)) if t < 27 else HONN[t - 27]
def idx_of_name(nm):
    nm = str(nm).strip()
    if nm in HOND: return HOND[nm]
    if nm and nm[0] in "mps": return "mps".index(nm[0]) * 9 + int(nm[1:]) - 1
    return "mps".index(nm[-1]) * 9 + int(nm[0]) - 1
cert = json.load(open("work/lowerbound/k3_disproof_certificate.json", encoding="utf-8"))
U = cert["tile_indices"]
K = len(U)
print("U =", cert["U"], "| |U| =", K, "| budget", cert["budget"])
# --- 独立重算 N / L for this U ---
hands = [0] * 0
cls = defaultdict(list)
nv = 0
for v in gen_vectors(K, 13):
    nv += 1
    c = [0] * 34
    for i, x in enumerate(v): c[U[i]] = x
    W = compute_W(c)
    if W: cls[frozenset(W)].append(tuple(v))
nh = sum(len(v) for v in cls.values())
N = len(cls)
Lset = []
for W, hs in cls.items():
    m = [min(h[i] for h in hs) for i in range(K)]
    if sum(m) < 3: Lset.append(W)
print("独立重算: vectors", nv, "listening hands", nh, "N =", N, "L =", len(Lset))
print("证书:      vectors", cert["n_vectors"], "listening hands", cert["n_hands"], "N =", cert["N"], "L =", cert["L"])
print("N 一致:", N == cert["N"], "| L 一致:", len(Lset) == cert["L"], "| hands 一致:", nh == cert["n_hands"])
print("Sum_tau 下界 N+L =", N + len(Lset), "> budget", cert["budget"], ":", (N + len(Lset)) > cert["budget"])
# 类集合一致
def parse_names(s):
    return [idx_of_name(x.strip()) for x in str(s).split(",") if x.strip()]
cert_classes = set()
for s in cert["all_class_W"]:
    cert_classes.add(frozenset(parse_names(s)))
print("类集合与证书 all_class_W 一致:", cert_classes == set(cls), "| 差:", len(cert_classes ^ set(cls)))
cert_L = set(frozenset(idx_of_name(x) for x in e["W"]) for e in cert["L_classes"])
print("L 集合一致:", cert_L == set(Lset), "| 差:", len(cert_L ^ set(Lset)))
# 3-码全集 (无序多重集) over U
allms = set()
for combo in itertools.combinations_with_replacement(U, 3):
    allms.add(tuple(sorted(combo)))
print("U 上 3-多重集总数:", len(allms), "| 有序码:", K ** 3)
# --- 逐条 blocker 校验 ---
bad_hand = bad_w = bad_code = 0
incomplete = []
covered_ms_counts = []
for e in cert["L_classes"]:
    W = frozenset(idx_of_name(x) for x in e["W"])
    seen = set()
    for b in e["blockers"]:
        code = [idx_of_name(x) for x in b["code"]]
        c = [0] * 34
        for nm, cnt in b["hand"]: c[idx_of_name(nm)] = cnt
        if sum(c) != 13 or any(c[t] > 4 for t in range(34)): bad_hand += 1
        Wc = compute_W(c)
        if Wc != W: bad_w += 1
        need = {}
        for t in code: need[t] = need.get(t, 0) + 1
        if all(c[t] >= v for t, v in need.items()): bad_code += 1   # 码竟能装进该手牌 => 该 blocker 无效
        seen.add(tuple(sorted(code)))
    missing = allms - seen
    if missing: incomplete.append({"W": e["W"], "missing_multisets": len(missing)})
print("blocker 校验: 非法手牌", bad_hand, "| W 不符", bad_w, "| blocker 失效(码反而能装进)", bad_code)
print("blocker 覆盖的多重集不足的类数:", len(incomplete), (incomplete[:3] if incomplete else ""))
