#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""chk_chiitoi.py <plan.json> -- 精确判定 61 个 chiitoi 类的覆盖 + (z,a,a,b) 容量饱和分析."""
import json, sys, os, itertools, collections
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
P = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "work/strategy/out/plan_k4_v2.json", encoding="utf-8"))
rows = P["plan"] if isinstance(P, dict) and "plan" in P else P
plancls = {}
for r in rows:
    W = frozenset(to_idx(r["W"]))
    plancls.setdefault(W, []).extend(tuple(c) for c in r["codes"])
allc = [c for cs in plancls.values() for c in cs]
p4 = {}
for m in set(tuple(sorted(c)) for c in allc):
    p4[m] = len(set(itertools.permutations(m)))
used_perm = collections.Counter(tuple(sorted(c)) for c in allc)
g = json.load(open("work/data/out/global.json", encoding="utf-8"))
descs = []
for key, lst in g["chiitoi_descriptors"].items():
    for d in lst:
        z = to_idx_one(d["z"])
        W = frozenset(set(to_idx(d["Wstd"])) | {z})
        descs.append((W, z))
print("chiitoi descriptors:", len(descs), "涉及类:", len(set(W for W, _ in descs)))

def chiitoi_covered(z, codes, find_witness=True):
    """返回 (是否全覆盖, 见证 K). 码 c 命中 {z}⊎2K  <=> c[z]<=1, c[x]<=2 (x≠z), 且 P(c)={x≠z:c[x]>0} ⊆ K."""
    Ps = []
    for c in codes:
        if c.count(z) > 1: continue
        if any(c.count(t) > 2 for t in set(c) if t != z): continue
        R = frozenset(t for t in c if t != z)
        if not R: return True, None     # 不可能 (c=(z,z,z,z) 已排除) 但保守
        Ps.append(R)
    singles = set()
    for R in Ps:
        if len(R) == 1: singles |= R
    allowed = [t for t in range(34) if t != z and t not in singles]
    hyper = [R for R in Ps if len(R) > 1]
    found = []
    def rec(start, K):
        if found: return
        if len(K) == 6:
            Ks = set(K)
            if all(not (R <= Ks) for R in hyper): found.append(list(K))
            return
        if len(allowed) - start < 6 - len(K): return
        for i in range(start, len(allowed)):
            K.append(allowed[i]); rec(i + 1, K); K.pop()
            if found: return
    if len(allowed) < 6: return True, None
    rec(0, [])
    return (not found), (found[0] if found else None)

fail_classes = collections.Counter()
fail_desc = []
sat = 0; sat_free = 0
for W, z in descs:
    codes = plancls.get(W, [])
    ok, wit = chiitoi_covered(z, codes)
    if not ok:
        fail_classes[W] += 1
        if len(fail_desc) < 8:
            # 该 z 的 (z,a,a,b) 码的多重集容量状况
            mset = [m for m in set(tuple(sorted(c)) for c in codes)
                    if m[0] == z and m[1] == m[2] and m[3] != z and (m[3] != z)]
            capinfo = [(list(m), used_perm[m], p4[m]) for m in mset[:5]]
            fail_desc.append({"W": [NM(t) for t in sorted(W)], "z": NM(z), "witness_K": [NM(t) for t in wit],
                              "n_codes": len(codes), "pairs_cap_sample": capinfo})
print("chiitoi 描述子覆盖失败的 (类,z) 数:", sum(fail_classes.values()), "涉及类数:", len(fail_classes))
for W, n in fail_classes.most_common(8):
    print("   类", [NM(t) for t in sorted(W)], "失败描述子数", n)
for d in fail_desc[:4]: print("   witness:", json.dumps(d, ensure_ascii=False)[:400])
# (z,a,a,b) 多重集容量饱和统计
sat_full = 0; sat_partial = 0; tot = 0
for m, k in used_perm.items():
    if len(m) == 4 and m[1] == m[2] and m[1] != m[0] and m[1] != m[3] and len(set(m)) == 3:
        tot += 1
        if k >= 12: sat_full += 1
        else: sat_partial += 1
print("形如 (z,a,a,b)(a≠b, 三张不同) 的多重集: 已用 %d 个, 其中 12/12 饱和 %d, 未满 %d" % (tot, sat_full, sat_partial))
