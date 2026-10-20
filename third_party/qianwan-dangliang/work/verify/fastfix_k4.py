#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fastfix_k4.py <plan.json> -- 对失败类补上【精确最小命中集】(k=4, 本门码, 全局有序码唯一).
输出 work/verify/plan_k4_fastfix.json + fastfix_report.json
"""
import json, sys, os, time, itertools
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
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

def load_cache(name):
    d = np.load(os.path.join(HERE, "cache_w_%s.npz" % name))
    return d["hands"], d["wids"], json.load(open(os.path.join(HERE, "cache_w_%s.json" % name)))

def greedy(masks, full):
    un = full; out = []
    while un:
        best, bc = None, 0
        for m in masks:
            c = (m & un).bit_count()
            if c > bc: bc, best = c, m
        if best is None or bc == 0: return None
        un &= ~best; out.append(best)
    return out

def min_cover(masks, full, tlimit=2.5):
    masks = list({m for m in masks if m & full})
    masks.sort(key=lambda m: m.bit_count(), reverse=True)
    pr = []
    for m in masks:
        if not any((m | p) == p for p in pr): pr.append(m)
    masks = pr
    g = greedy(masks, full)
    best = [len(g) if g else 10**9, g]
    t0 = time.time(); to = [False]
    bits = [i for i in range(full.bit_length()) if (full >> i) & 1]
    cov = {i: [m for m in masks if (m >> i) & 1] for i in bits}
    def rec(un, chosen):
        if time.time() - t0 > tlimit: to[0] = True; return
        if un == 0:
            if len(chosen) < best[0]: best[0] = len(chosen); best[1] = list(chosen)
            return
        if len(chosen) + 1 >= best[0]: return
        rem = [i for i in bits if (un >> i) & 1]
        i = min(rem, key=lambda x: len(cov[x]))
        for m in sorted(cov[i], key=lambda m: (m & un).bit_count(), reverse=True):
            if len(chosen) + 1 >= best[0]: break
            chosen.append(m); rec(un & ~m, chosen); chosen.pop()
            if to[0]: return
    rec(full, [])
    return best[1], (not to[0])

def main():
    plan_path = sys.argv[1]
    p = json.load(open(plan_path, encoding="utf-8"))
    rows = p["plan"]
    plancls = {}
    order = []
    for r in rows:
        W = frozenset(to_idx(r["W"]))
        plancls[W] = [tuple(c) for c in r["codes"]]
        order.append(W)
    used = set()
    for cs in plancls.values():
        for c in cs: used.add(tuple(c))
    used0 = len(used)
    rep = {"plan": plan_path, "suits": {}, "added_codes": 0, "classes_fixed": 0, "still_failing": 0, "timeouts": 0}
    for name, (K, off) in CATS.items():
        hands, wids, wlist = load_cache(name)
        t0 = time.time(); fixed = 0; still = 0; to_n = 0; added = 0
        for wid, Wl in enumerate(wlist):
            W = frozenset(Wl)
            cs = plancls.get(W)
            if not cs: continue
            idx = np.nonzero(wids == wid)[0]
            H = hands[idx]
            covered = np.zeros(len(idx), dtype=bool)
            for c in cs:
                if any(t < off or t >= off + K for t in c): continue
                need = np.zeros(K, dtype=np.int8)
                for t in c: need[t - off] += 1
                covered |= (H >= need).all(axis=1)
            unc = np.nonzero(~covered)[0]
            if len(unc) == 0: continue
            Hu = H[unc]; full = (1 << len(unc)) - 1
            # 候选: 本门 4-多重集, 至少一个排列未被占用, 且 ⊆ 某手牌
            cand_masks = []; cand_code = []
            for m in itertools.combinations_with_replacement(range(K), 4):
                need = np.zeros(K, dtype=np.int8)
                for t in m: need[t] += 1
                mask = (Hu >= need).all(axis=1)
                cnt = int(mask.sum())
                if cnt == 0: continue
                free = None
                for pm in sorted(set(itertools.permutations(m))):
                    code = tuple(off + t for t in pm)
                    if code not in used: free = code; break
                if free is None: continue
                bits = 0
                for j in np.nonzero(mask)[0]: bits |= (1 << int(j))
                cand_masks.append(bits); cand_code.append(free)
            if not cand_masks:
                still += 1; continue
            sel, exact = min_cover(cand_masks, full)
            if sel is None:
                still += 1; continue
            if not exact: to_n += 1
            # 找每个 mask 对应的码 (取第一个匹配且未占用)
            chosen_codes = []
            used_local = set()
            for m in sel:
                for bits, code in zip(cand_masks, cand_code):
                    if bits == m and code not in used_local:
                        chosen_codes.append(code); used_local.add(code); break
            if len(chosen_codes) != len(sel):
                still += 1; continue
            for code in chosen_codes:
                used.add(code); plancls[W].append(code); added += 1
            fixed += 1
        rep["suits"][name] = {"fixed_classes": fixed, "still_failing": still, "added_codes": added,
                              "timeouts_greedy_only": to_n, "secs": round(time.time() - t0, 1)}
        print(name, json.dumps(rep["suits"][name]), flush=True)
    rep["added_codes"] = len(used) - used0
    rep["classes_fixed"] = sum(v["fixed_classes"] for v in rep["suits"].values())
    out_rows = [{"W": r["W"], "codes": [list(c) for c in plancls[frozenset(to_idx(r["W"]))]],
                 "modes": r.get("modes", [])} for r in rows]
    out = {"k": p.get("k", 4), "n_classes": len(out_rows),
           "n_codes": sum(len(r["codes"]) for r in out_rows), "plan": out_rows,
           "base": plan_path, "fastfix": rep}
    json.dump(out, open(os.path.join(HERE, "plan_k4_fastfix.json"), "w"), ensure_ascii=False)
    json.dump(rep, open(os.path.join(HERE, "fastfix_report.json"), "w"), ensure_ascii=False, indent=1)
    print("TOTAL added", rep["added_codes"], "fixed classes", rep["classes_fixed"], "still failing", rep["still_failing"])

if __name__ == "__main__":
    main()
