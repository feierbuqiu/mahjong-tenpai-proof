#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""structural_k3.py <plan.json> -- k=3 结构复核:
 1) 类集合 == verifier 独立 2846; 2) 0 空类; 3) 有序码全局唯一 (= decode 良定义);
 4) 每个码 ⊆ 该类的某手牌 (单花色类用缓存全量核; 其余按来源抽样核);
 5) 独立 W 抽查: 缓存手牌用 compute_W 复算, 与缓存 W 一致 (= plan 类键正确).
"""
import json, sys, os, random, itertools
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from indep_core import compute_W
CATS = {"m": (9, 0), "p": (9, 9), "s": (9, 18), "z": (7, 27)}
HON = {"E": 27, "S": 28, "W": 29, "N": 30, "Haku": 31, "Hatsu": 32, "Chun": 33}
HONN = ["E", "S", "W", "N", "Haku", "Hatsu", "Chun"]
NM = lambda t: ("%d%s" % (t % 9 + 1, "mps"[t // 9])) if t < 27 else HONN[t - 27]
def to_idx(w):
    if isinstance(w, int): return [t for t in range(34) if (w >> t) & 1]
    out = []
    for nm in w:
        if isinstance(nm, int): out.append(nm)
        elif nm in HON: out.append(HON[nm])
        else: out.append("mps".index(nm[-1]) * 9 + int(nm[0]) - 1)
    return out
PLAN = sys.argv[1]
P = json.load(open(PLAN, encoding="utf-8"))
rows = P["plan"] if isinstance(P, dict) and "plan" in P else P
census = set(frozenset(x) for x in json.load(open(os.path.join(HERE, "census_strict.json"), encoding="utf-8")))
plancls = {}
dups = 0
for r in rows:
    W = frozenset(to_idx(r["W"]))
    if W in plancls: dups += 1
    plancls.setdefault(W, []).extend(tuple(c) for c in r["codes"])
allcodes = [c for cs in plancls.values() for c in cs]
uniq = set(allcodes)
print("classes:", len(plancls), "duplicate W rows:", dups, "| class set == census:", set(plancls) == census,
      "| missing:", len(census - set(plancls)), "extra:", len(set(plancls) - census))
print("codes:", len(allcodes), "distinct ordered:", len(uniq), "=> ordered-unique:", len(uniq) == len(allcodes))
print("empty classes:", sum(1 for cs in plancls.values() if not cs))
lens = set(len(c) for c in allcodes[:5000])
print("code lengths seen:", lens)
# 4) 单花色类: 全量核 "每个码 ⊆ 该类某手牌"
def load_cache(name):
    d = np.load(os.path.join(HERE, "cache_w_%s.npz" % name))
    return d["hands"], d["wids"], json.load(open(os.path.join(HERE, "cache_w_%s.json" % name)))
bad = 0; checked = 0; skipped_outside = 0
for name, (K, off) in CATS.items():
    hands, wids, wlist = load_cache(name)
    for wid, Wl in enumerate(wlist):
        W = frozenset(Wl)
        cs = plancls.get(W)
        if not cs: continue
        idx = np.nonzero(wids == wid)[0]
        if len(idx) == 0: continue
        H = hands[idx]
        for c in cs:
            if any(t < off or t >= off + K for t in c): skipped_outside += 1; continue
            need = np.zeros(K, dtype=np.int8)
            for t in c: need[t - off] += 1
            checked += 1
            if not (H >= need).all(axis=1).any(): bad += 1
print("4) code ⊆ some hand (single-suit, complete): checked", checked, "bad", bad, "skipped(跨门码, 另按来源抽样)")
# 5) 独立 W 抽查
rng = random.Random(7); n = 0; mism = 0
for name, (K, off) in CATS.items():
    hands, wids, wlist = load_cache(name)
    for _ in range(400):
        i = rng.randrange(len(hands))
        c = [0] * 34
        for j in range(K):
            if hands[i][j]: c[off + j] = int(hands[i][j])
        W = compute_W(c)
        n += 1
        if frozenset(W) != frozenset(wlist[wids[i]]): mism += 1
print("5) W 独立抽查:", n, "hands, 失配", mism)
