#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""permfix_k4.py <base plan.json>
(1) 排列回退 + 通用码优先: 对每个未覆盖的 Type I 块, 优先取一个 ⊆A 的 4-码(多重集⊆A的任一未用排列).
(2) chiitoi: 对含七对子描述子的类, 加入鸽笼对族 {(a,a,b,b)}: 把 33 张非 z 牌分成 6 组,
    同组任意两张 a,b 都满足: 任意 6 对集合 K 必含同组两张(鸽笼) => (a,a,b,b) ⊆ {z}⊎2K.
输出 work/verify/plan_k4_permfix.json
"""
import json, sys, os, itertools, collections, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from indep_core import melds_only, melds_only_honor, gen_vectors
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
SU = {"m": 0, "p": 1, "s": 2, "z": 3}
def parse(ds, ci):
    off = (0, 9, 18, 27)[ci]; u = [0] * 34
    for i, ch in enumerate(ds):
        if ch != "0": u[off + i] = int(ch)
    return u
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
def contains(h, c):
    need = {}
    for t in c: need[t] = need.get(t, 0) + 1
    return all(h[t] >= v for t, v in need.items())

def main():
    base = sys.argv[1]
    P = json.load(open(base, encoding="utf-8"))
    rows = P["plan"]
    plancls = {}
    for r in rows: plancls[frozenset(to_idx(r["W"]))] = [tuple(c) for c in r["codes"]]
    used = set()
    for cs in plancls.values():
        for c in cs: used.add(c)
    n0 = len(used)
    permcache = {}
    def free_perm(mset):
        key = tuple(sorted(mset))
        ps = permcache.get(key)
        if ps is None:
            ps = sorted(set(itertools.permutations(key))); permcache[key] = ps
        for pm in ps:
            if pm not in used: return pm
        return None
    def typeI_covered(A, inert, m, codes):
        if any(contains(A, c) for c in codes): return True
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
        return rec(0, m, list(A))
    g = json.load(open("work/data/out/global.json", encoding="utf-8"))
    t0 = time.time()
    blocks = 0; uncov = 0; fixedA = 0; hard = []
    for row in g["classes"]:
        W = frozenset(to_idx(row["W"]))
        if W not in plancls: continue
        if any(s["kind"] == "kokushi" for s in row.get("sources", [])): continue
        codes = plancls[W]
        for s in row.get("sources", []):
            if s["kind"] != "I": continue
            blocks += 1
            ci = SU[s["cat"]]; A = parse(s["A"], ci); m = 13 - sum(A)
            if typeI_covered(A, s["inert"], m, codes): continue
            uncov += 1
            Atiles = [i for i in range(34) for _ in range(A[i])]
            cands = sorted(set(itertools.combinations_with_replacement(Atiles, 4)))
            got = None
            for m4 in cands:
                cp = free_perm(m4)
                if cp is not None and contains(A, cp):
                    got = cp; break
            if got is not None:
                plancls[W].append(got); used.add(got); fixedA += 1
            else:
                hard.append({"W": row["W"], "A": s["A"], "cat": s["cat"], "m": m, "nA": len(Atiles)})
                # 硬块第二招: 枚举 F, 用"全 4-多重集(有自由排列)"贪心覆盖未命中 F
                Fs = []
                ii = [SU[x] for x in s["inert"]]
                def genFi(i, rem, acc):
                    if i == len(ii):
                        if rem == 0: Fs.append(tuple(acc))
                        return
                    ci2 = ii[i]
                    for sd in range(0, rem + 1, 3):
                        if (rem - sd) > 12 * (len(ii) - i - 1): continue
                        for v in dec_vecs(ci2, sd):
                            a2 = list(acc)
                            for t, x in enumerate(v): a2[t] += x
                            genFi(i + 1, rem - sd, a2)
                genFi(0, m, [0] * 34)
                unc = [F for F in Fs if not any(contains([A[t] + F[t] for t in range(34)], c) for c in plancls[W])]
                rounds = 0
                while unc and rounds < 12:
                    cand = set()
                    for F in unc[:40]:
                        H = [A[t] + F[t] for t in range(34)]
                        tiles = [t for t in range(34) for _ in range(H[t])]
                        for m4 in set(itertools.combinations_with_replacement(tiles, 4)):
                            cand.add(m4)
                    best = None; bc = -1; bcode = None
                    for m4 in cand:
                        cp = free_perm(m4)
                        if cp is None: continue
                        cnt = sum(1 for F in unc if contains([A[t] + F[t] for t in range(34)], cp))
                        if cnt > bc: bc, best, bcode = cnt, m4, cp
                    if best is None or bc <= 0: break
                    plancls[W].append(bcode); used.add(bcode); fixedA += 1
                    unc = [F for F in unc if not contains([A[t] + F[t] for t in range(34)], bcode)]
                    rounds += 1
            if blocks % 20000 == 0:
                print("  ... blocks", blocks, "uncov", uncov, "fixedA", fixedA, "%.0fs" % (time.time() - t0), flush=True)
    print("TypeI: blocks", blocks, "uncovered", uncov, "fixed_by_superset_code", fixedA, "hard", len(hard))
    if hard: print("  hard examples:", json.dumps(hard[:5], ensure_ascii=False))
    # (B) chiitoi 鸽笼对族
    nonz = [t for t in range(34) if t != 0]
    chi_fixed = 0; chi_codes = 0
    for key, lst in g["chiitoi_descriptors"].items():
        for d in lst:
            z = to_idx([d["z"]])[0] if not isinstance(d["z"], int) else d["z"]
            W = frozenset(set(to_idx(d["Wstd"])) | {z})
            if W not in plancls: continue
            tiles = [t for t in range(34) if t != z]
            rr = random.Random(abs(hash((z, tuple(sorted(W)))) ) % (2**31))
            tiles = tiles[:]; rr.shuffle(tiles)
            parts = [tiles[i::6] for i in range(6)]
            added_here = 0
            for part in parts:
                for a, b in itertools.combinations(part, 2):
                    cp = free_perm((a, a, b, b))
                    if cp is not None:
                        plancls[W].append(cp); used.add(cp); added_here += 1
            chi_fixed += 1; chi_codes += added_here
    print("chiitoi classes processed:", chi_fixed, "codes added:", chi_codes)
    out_rows = [{"W": r["W"], "codes": [list(c) for c in plancls[frozenset(to_idx(r["W"]))]], "modes": r.get("modes", [])} for r in rows]
    out = {"k": P.get("k", 4), "n_classes": len(out_rows), "n_codes": sum(len(r["codes"]) for r in out_rows),
           "plan": out_rows, "base": base, "permfix": {"typeI_blocks": blocks, "typeI_uncovered": uncov,
           "fixed_by_superset": fixedA, "hard_blocks": len(hard), "hard_examples": hard[:5],
           "chiitoi_classes": chi_fixed, "chiitoi_codes_added": chi_codes, "added_total": len(used) - n0}}
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "plan_k4_permfix.json"), "w"), ensure_ascii=False)
    print("TOTAL classes", len(out_rows), "codes", out["n_codes"], "added", len(used) - n0, "secs", round(time.time() - t0, 1))

if __name__ == "__main__":
    main()
