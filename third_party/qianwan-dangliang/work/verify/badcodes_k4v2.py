
import json, os, itertools, collections
import numpy as np
HERE = "work/verify"
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
P = json.load(open("work/strategy/out/plan_k4_v2.json", encoding="utf-8"))
rows = P["plan"]
plancls = {}
for r in rows:
    W = frozenset(to_idx(r["W"]))
    plancls.setdefault(W, []).extend(tuple(c) for c in r["codes"])
allc = [c for cs in plancls.values() for c in cs]
ms = collections.Counter(tuple(sorted(c)) for c in allc)
p4 = lambda m: len(set(itertools.permutations(m)))
over = {m: k for m, k in ms.items() if k > p4(m)}
print("codes", len(allc), "distinct ordered", len(set(allc)), "distinct multisets", len(ms))
print("multisets over p4 capacity:", len(over))
def load_cache(name):
    d = np.load(os.path.join(HERE, "cache_w_%s.npz" % name))
    return d["hands"], d["wids"], json.load(open(os.path.join(HERE, "cache_w_%s.json" % name)))
bad = []
for name, (K, off) in CATS.items():
    hands, wids, wlist = load_cache(name)
    for wid, Wl in enumerate(wlist):
        W = frozenset(Wl); cs = plancls.get(W)
        if not cs: continue
        idx = np.nonzero(wids == wid)[0]
        H = hands[idx]
        for c in cs:
            if any(t < off or t >= off + K for t in c): continue
            need = np.zeros(K, dtype=np.int8)
            for t in c: need[t - off] += 1
            if not (H >= need).all(axis=1).any():
                bad.append({"W": [NM(t) for t in sorted(W)], "code": [NM(t) for t in c], "cat": name, "modes": None})
print("bad codes (⊆ no hand of class):", len(bad))
for b in bad[:12]: print("   ", b)
