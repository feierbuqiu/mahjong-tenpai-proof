
import json, sys, os
import numpy as np
sys.path.insert(0, "work/verify")
HERE = "work/verify"
CATS = {"m": (9, 0), "p": (9, 9), "s": (9, 18), "z": (7, 27)}
HON = {"E": 27, "S": 28, "W": 29, "N": 30, "Haku": 31, "Hatsu": 32, "Chun": 33}
HONN = ["E", "S", "W", "N", "Haku", "Hatsu", "Chun"]
NM = lambda t: ("%d%s" % (t % 9 + 1, "mps"[t // 9])) if t < 27 else HONN[t - 27]
def to_idx_one(nm):
    return HON[nm] if nm in HON else "mps".index(nm[-1]) * 9 + int(nm[0]) - 1
p = json.load(open("work/recon/plan_k4_u9.json", encoding="utf-8"))
rows = p["plan"]
def to_idx(r):
    out=[]
    for nm in r["W"]:
        out.append(HON[nm] if nm in HON else "mps".index(nm[-1])*9 + int(nm[0]) - 1)
    return frozenset(out)
plancls = {to_idx(r): [tuple(c) for c in r["codes"]] for r in rows}
for spec in ("3p,7p", "1s,7s", "3p,6p", "2s,3s"):
    W = frozenset(to_idx_one(x) for x in spec.split(","))
    c0 = min(W); cat = "m" if c0 < 9 else "p" if c0 < 18 else "s" if c0 < 27 else "z"
    K, off = CATS[cat]
    d = np.load(os.path.join(HERE, "cache_w_%s.npz" % cat)); hands = d["hands"]; wids = d["wids"]
    wl = json.load(open(os.path.join(HERE, "cache_w_%s.json" % cat)))
    wid = [i for i, x in enumerate(wl) if frozenset(x) == W]
    if not wid: print(spec, "no hands"); continue
    idx = np.nonzero(wids == wid[0])[0]; H = hands[idx]
    mn = H.min(axis=0)
    codes = plancls.get(W, [])
    print("== class", spec, "| hands", len(idx), "| plan codes", len(codes))
    print("   intersection min counts (per suit tile):", {NM(off+i): int(mn[i]) for i in range(K) if mn[i] > 0})
    tot = int(mn.sum())
    print("   sum(min) =", tot, "=> 存在公共 4-码?" , tot >= 4)
    if tot >= 4:
        need = np.zeros(K, dtype=np.int8); rem = 4
        for i in range(K):
            take = min(int(mn[i]), rem)
            need[i] = take; rem -= take
            if rem == 0: break
        fits_all = (H >= need).all(axis=1).all()
        code = [NM(off+i) for i in range(K) for _ in range(int(need[i]))]
        print("   建议公共码:", code, " 对所有", len(idx), "手牌都成立?", bool(fits_all),
              " 已在 plan 中?", any(tuple(sorted([off+i for i in range(K) for _ in range(int(need[i]))])) == tuple(sorted(c)) for c in codes))
