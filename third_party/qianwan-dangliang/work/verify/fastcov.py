#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fastcov.py -- 高效版覆盖检查 (numpy 向量化 + 手牌->W 磁盘缓存).
替换 gap_exact/k4_gap_classes 里最慢的两件事:
  1) 对全部单类别手牌反复调用 compute_W  => 缓存到 work/verify/cache_w_<cat>.npz (只算一次)
  2) 逐手逐码的 Python 包含判断           => numpy 广播 (H >= need).all(axis=1)
用法: python -u work/verify/fastcov.py <plan.json> [--rebuild]
"""
import json, sys, os, time, itertools
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from indep_core import compute_W, gen_vectors

HERE = os.path.dirname(os.path.abspath(__file__))
CATS = {"m": (9, 0), "p": (9, 9), "s": (9, 18), "z": (7, 27)}
HONN = ["E", "S", "W", "N", "Haku", "Hatsu", "Chun"]
NM = lambda t: ("%d%s" % (t % 9 + 1, "mps"[t // 9])) if t < 27 else HONN[t - 27]

def cache_path(name): return os.path.join(HERE, "cache_w_%s.npz" % name)

def build_cache(name, K, off, force=False):
    hp, wp = cache_path(name), os.path.join(HERE, "cache_w_%s.json" % name)
    if not force and os.path.exists(hp) and os.path.exists(wp):
        d = np.load(hp); return d["hands"], d["wids"], json.load(open(wp))
    t0 = time.time()
    hands = np.array(list(gen_vectors(K, 13)), dtype=np.int8)
    wset, wids = {}, np.empty(len(hands), dtype=np.int32)
    for i, h in enumerate(hands):
        c = [0] * 34
        for j, x in enumerate(h):
            if x: c[off + j] = x
        key = tuple(sorted(compute_W(c)))
        if key not in wset: wset[key] = len(wset)
        wids[i] = wset[key]
    wlist = [None] * len(wset)
    for k, v in wset.items(): wlist[v] = list(k)
    np.savez(hp, hands=hands, wids=wids)
    json.dump(wlist, open(wp, "w"))
    print("[fastcov] built cache %s: %d hands, %d W, %.1fs" % (name, len(hands), len(wset), time.time() - t0), flush=True)
    return hands, wids, wlist

def load_plan(path):
    HON = {"E": 27, "S": 28, "W": 29, "N": 30, "Haku": 31, "Hatsu": 32, "Chun": 33}
    def to_idx(w):
        if isinstance(w, int): return [t for t in range(34) if (w >> t) & 1]
        out = []
        for nm in w:
            if isinstance(nm, int): out.append(nm)
            elif nm in HON: out.append(HON[nm])
            else: out.append("mps".index(nm[-1]) * 9 + int(nm[0]) - 1)
        return out
    p = json.load(open(path, encoding="utf-8"))
    rows = p["plan"] if isinstance(p, dict) and "plan" in p else p
    return {frozenset(to_idx(r["W"])): [tuple(c) for c in r["codes"]] for r in rows}

def gap(path, rebuild=False):
    plancls = load_plan(path)
    out = {"plan": path, "zero_code_classes": sum(1 for cs in plancls.values() if not cs), "suits": {}}
    for name, (K, off) in CATS.items():
        hands, wids, wlist = build_cache(name, K, off, rebuild)
        zeros = 0; fails = 0; per_class = {}; class_size = {}
        for wid, W in enumerate(wlist):
            key = frozenset(W)
            idx = np.nonzero(wids == wid)[0]
            codes = plancls.get(key)
            if codes is None: continue
            if not codes:
                zeros += len(idx); continue
            H = hands[idx]
            covered = np.zeros(len(idx), dtype=bool)
            for c in codes:
                if any(t < off or t >= off + K for t in c):   # 混门码不可能装进全落本门的手牌
                    continue
                need = np.zeros(K, dtype=np.int8)
                for t in c: need[t - off] += 1
                covered |= (H >= need).all(axis=1)
            f = int((~covered).sum())
            if f:
                per_class[key] = f; class_size[key] = len(idx)
        fails = sum(per_class.values())
        ordered_fail = sorted(per_class, key=lambda W: -per_class[W])
        out["suits"][name] = {"uncovered_in_zero_code_classes": zeros, "uncovered_in_coded_classes": fails,
                              "classes_with_failures": len(per_class),
                              "top": [{"W": [NM(t) for t in sorted(W)], "uncovered": per_class[W]} for W in ordered_fail[:6]],
                              "all_failures": [{"W": [NM(t) for t in sorted(W)], "uncovered": per_class[W],
                                                "class_size": class_size[W]} for W in ordered_fail]}
        print(name, json.dumps(out["suits"][name], ensure_ascii=False)[:300], flush=True)
    return out

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "work/strategy/out/plan_k4.json"
    t0 = time.time()
    res = gap(path, "--rebuild" in sys.argv)
    res["secs"] = round(time.time() - t0, 1)
    json.dump(res, open(os.path.join(HERE, "fastcov_report.json"), "w"), ensure_ascii=False, indent=1)
    print("TOTAL", res["secs"], "s")
