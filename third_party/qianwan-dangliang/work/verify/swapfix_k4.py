#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""swapfix_k4.py -- 按 lead 的替换算法清掉 Type I 47 个 hard 块:
对饱和的 mu=multiset(A)(|A|=4), 找占用者 C' \in USERS(mu), 把 C' 的该码换成替代码(需保持 C' 仍全覆盖),
腾出 1 个排列给需要 mu 的类. 每步都用 DFS/缓存复检 donar 覆盖, 保证不放坏.
"""
import json, sys, os, itertools, time, collections
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from indep_core import melds_only, melds_only_honor, gen_vectors
HON = {"E": 27, "S": 28, "W": 29, "N": 30, "Haku": 31, "Hatsu": 32, "Chun": 33}
HONN = ["E", "S", "W", "N", "Haku", "Hatsu", "Chun"]
NM = lambda t: ("%d%s" % (t % 9 + 1, "mps"[t // 9])) if t < 27 else HONN[t - 27]
def to_idx_one(nm):
    nm = str(nm).strip()
    if nm in HON: return HON[nm]
    if nm and nm[0] in "mps": return "mps".index(nm[0]) * 9 + int(nm[1:]) - 1
    return "mps".index(nm[-1]) * 9 + int(nm[0]) - 1
def to_idx(w):
    if isinstance(w, int): return [t for t in range(34) if (w >> t) & 1]
    if w and all(isinstance(x, int) for x in w): return list(w)
    return [to_idx_one(nm) for nm in w]
CATS = {"m": (9, 0), "p": (9, 9), "s": (9, 18), "z": (7, 27)}
SU = {"m": 0, "p": 1, "s": 2, "z": 3}
def contains(h, c):
    need = {}
    for t in c: need[t] = need.get(t, 0) + 1
    return all(h[t] >= v for t, v in need.items())
DEC = {}
def dec_vecs(ci, s):
    k = (ci, s)
    if k in DEC: return DEC[k]
    K = (9, 9, 9, 7)[ci]; hon = ci == 3; off = (0, 9, 18, 27)[ci]
    out = []
    for v in gen_vectors(K, s):
        if (melds_only_honor(v) if hon else melds_only(v)):
            u = [0] * 34
            for i, x in enumerate(v):
                if x: u[off + i] = x
            out.append(tuple(u))
    DEC[k] = out; return out
def parse(ds, ci):
    off = (0, 9, 18, 27)[ci]; u = [0] * 34
    for i, ch in enumerate(ds):
        if ch != "0": u[off + i] = int(ch)
    return u
PLAN = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "plan_k4_final.json")
P = json.load(open(PLAN, encoding="utf-8"))
rows = P["plan"]
plancls = {}
for r in rows:
    W = frozenset(to_idx(r["W"]))
    plancls.setdefault(W, []).extend(tuple(c) for c in r["codes"])
used = set()
for cs in plancls.values():
    for c in cs: used.add(c)
parr = {}
def perms(m):
    k = tuple(sorted(m))
    if k not in parr: parr[k] = sorted(set(itertools.permutations(k)))
    return parr[k]
def free_perm(m):
    for pm in perms(m):
        if pm not in used: return pm
    return None
# --- 预取每类的 Type I 来源 + 单花色手牌索引 ---
g = json.load(open("work/data/out/global.json", encoding="utf-8"))
srcs = {}
for row in g["classes"]:
    W = frozenset(to_idx(row["W"]))
    lst = []
    for s in row.get("sources", []):
        if s["kind"] == "I":
            ci = SU[s["cat"]]; A = parse(s["A"], ci); lst.append((A, s["inert"], 13 - sum(A), s["cat"]))
    srcs[W] = lst
cache = {}
for name, (K, off) in CATS.items():
    d = np.load(os.path.join(HERE, "cache_w_%s.npz" % name))
    wl = json.load(open(os.path.join(HERE, "cache_w_%s.json" % name)))
    cache[name] = (d["hands"], d["wids"], [frozenset(x) for x in wl], K, off)
def su_ok(W, codes):
    for name, (hands, wids, wlist, K, off) in cache.items():
        for wid, Wl in enumerate(wlist):
            if Wl != W: continue
            idx = np.nonzero(wids == wid)[0]
            H = hands[idx]
            covered = np.zeros(len(idx), dtype=bool)
            for c in codes:
                if any(t < off or t >= off + K for t in c): continue
                need = np.zeros(K, dtype=np.int8)
                for t in c: need[t - off] += 1
                covered |= (H >= need).all(axis=1)
            if not covered.all(): return False
    return True
def ti_ok(W, codes):
    for (A, inert, m, cat) in srcs.get(W, []):
        if any(contains(A, c) for c in codes): continue
        ii = [SU[x] for x in inert]
        def rec(i, rem, hand):
            for c in codes:
                if contains(hand, c): return True
            if i == len(ii): return rem != 0
            ci = ii[i]
            for s in range(0, rem + 1, 3):
                if (rem - s) > 12 * (len(ii) - i - 1): continue
                for v in dec_vecs(ci, s):
                    h2 = list(hand)
                    for t, x in enumerate(v): h2[t] += x
                    if not rec(i + 1, rem - s, h2): return False
            return True
        if not rec(0, m, list(A)): return False
    return True
def cls_ok(W, codes):
    return su_ok(W, codes) and ti_ok(W, codes)
hard = P.get("finalfix", {}).get("typeI_hard_all", [])
print("hard 块:", len(hard), flush=True)
owners = collections.defaultdict(set)
for W, cs in plancls.items():
    for c in cs: owners[tuple(sorted(c))].add(W)
t0 = time.time(); fixed = 0; blocked = []
for h in hard:
    W = frozenset(to_idx(h["W"])); ci = SU[h["cat"]]; A = parse(h["A"], ci)
    mu = tuple(sorted(A))
    if free_perm(mu) is not None:
        cp = free_perm(mu); plancls[W].append(cp); used.add(cp); fixed += 1; continue
    done = False
    for C2 in list(owners[mu]):
        if C2 == W: continue
        cdel = [c for c in plancls[C2] if tuple(sorted(c)) == mu]
        if not cdel: continue
        c0 = cdel[0]
        plancls[C2].remove(c0); used.discard(c0)
        if cls_ok(C2, plancls[C2]):
            cp = free_perm(mu); plancls[W].append(cp); used.add(cp); fixed += 1; done = True
            print("  swap ok: mu", [NM(t) for t in mu], "donor", [NM(t) for t in sorted(C2)], "(%.0fs)" % (time.time() - t0), flush=True)
            break
        # 尝试给 donor 补一条替代码
        repl = None
        for (A2, inert2, m2, cat2) in srcs.get(C2, []):
            At = [i for i in range(34) for _ in range(A2[i])]
            if len(At) < 4: continue
            for m4 in itertools.combinations_with_replacement(At, 4):
                cpn = free_perm(m4)
                if cpn is not None and contains(A2, cpn): repl = cpn; break
            if repl: break
        if repl is not None:
            plancls[C2].append(repl); used.add(repl)
            if cls_ok(C2, plancls[C2]):
                cp = free_perm(mu); plancls[W].append(cp); used.add(cp); fixed += 1; done = True
                print("  swap+repl ok: mu", [NM(t) for t in mu], "donor", [NM(t) for t in sorted(C2)], flush=True)
                break
            used.discard(repl); plancls[C2].remove(repl)
        plancls[C2].append(c0); used.add(c0)
    if not done:
        blocked.append({"W": h["W"], "A": h["A"], "mu": [NM(t) for t in mu],
                        "owners": [[NM(t) for t in sorted(x)] for x in list(owners[mu])[:6]]})
print("修好", fixed, "仍阻塞", len(blocked), " (%.0fs)" % (time.time() - t0), flush=True)
out_rows = [{"W": r["W"], "codes": [list(c) for c in plancls[frozenset(to_idx(r["W"]))]], "modes": r.get("modes", [])} for r in rows]
out = {"k": 4, "n_classes": len(out_rows), "n_codes": sum(len(r["codes"]) for r in out_rows), "plan": out_rows,
       "base": PLAN, "swapfix": {"hard_before": len(hard), "fixed": fixed, "blocked": blocked}}
json.dump(out, open(os.path.join(HERE, "plan_k4_final.json"), "w"), ensure_ascii=False)
json.dump({"fixed": fixed, "blocked": blocked}, open(os.path.join(HERE, "swapfix_report.json"), "w"), ensure_ascii=False, indent=1)
print("TOTAL codes", out["n_codes"])
