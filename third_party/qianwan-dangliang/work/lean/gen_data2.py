#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""work/lean/gen_data2.py -- L6 第一步：生成 lean/Mj/Data2.lean（II 型 profile 表 + 309,144 块记录）。

* profTable：对 16 个 (cat,size) 组合，内联 (profile key -> |xs|, Σenc(xs))。
  key = (V, pd, odd, ot, a2, o2)（与 table_lib.x_profile / PROF_II 的键一致）。
* blocks：309,144 个 II 块，编码为单个 Nat:
    rec = classIdx * 2^25 + comboIdx * 2^18 + k1idx * 2^9 + k2idx
  其中 classIdx 指向 Mj.Data.planData 的行号，comboIdx 指向 combos 列表（(c1,s1,c2,s2)，96 个），
  k1idx/k2idx 指向 profTable 中该 (c,size) 分组的条目。
* 自检（Python 侧）：用 table_lib 的 all_vectors + x_profile 重新枚举，与 PROFII_D 的 xs 逐条对拍。
"""
import sys, os, json, pickle, time, itertools

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "work", "strategy"))
sys.path.insert(0, os.path.join(ROOT, "work", "strategy", "out"))

import table_lib as TL

PLAN = os.path.join(ROOT, "work", "verify", "plan_k4_FINAL.json")
TABLES = os.path.join(ROOT, "work", "strategy", "out", "table_cache.pkl")
OUT = os.path.join(ROOT, "lean", "Mj", "Data2.lean")

HON = ["E", "S", "W", "N", "Haku", "Hatsu", "Chun"]
HONI = {n: 27 + i for i, n in enumerate(HON)}


def to_idx(x):
    if isinstance(x, int):
        return x
    if x in HONI:
        return HONI[x]
    return "mps".index(x[-1]) * 9 + int(x[0]) - 1


def encX(X):
    """order-independent checksum of a count vector (digits <= 4, base 5)"""
    e = 0
    for i, x in enumerate(X):
        e += x * 5 ** i
    return e


def key_enc(k):
    """与 Lean 的 keyEnc 完全一致：V + pd*2^34 + odd*2^35 + ot*2^39 + a2*2^45 + o2*2^46"""
    V, pd, odd, ot, a2, o2 = k
    mask = 0
    for t in V:
        mask |= 1 << t
    return (mask + (1 if pd else 0) * 2 ** 34 + odd * 2 ** 35 +
            (34 if ot is None else ot) * 2 ** 39 +
            (1 if a2 else 0) * 2 ** 45 + (1 if o2 else 0) * 2 ** 46)


def keytuple(k):
    return key_enc(k)


def load():
    P = json.load(open(PLAN, encoding="utf-8"))
    order = []
    seen = set()
    for r in P["plan"]:
        W = frozenset(to_idx(x) for x in r["W"])
        if W not in seen:
            seen.add(W)
            order.append(W)
    C = pickle.load(open(TABLES, "rb"))
    return order, C["cls"], C["PROFII_D"]


def check_python_enum(PII):
    """每个 (c,s) 只枚举一遍并分组，再与 PROFII_D 的 xs / am 逐条对拍"""
    bad = 0
    checked = 0
    for c in range(4):
        for s in (2, 5, 8, 11):
            g = {}
            for X in TL.all_vectors(c, s):
                # PROFII_D 的键是 x_profile 去掉第一分量 Wp 后的 6 元组
                g.setdefault(TL.x_profile(c, X)[1:], []).append(X)
            for k, xs in g.items():
                if (c, s, k) not in PII:
                    bad += 1
                    print("  EXTRA key in my enumeration (c=%d,s=%d)" % (c, s))
                    continue
                am, xs_ref = PII[(c, s, k)]
                checked += 1
                if sorted(xs) != sorted(xs_ref):
                    bad += 1
                    if bad <= 3:
                        print("  MISMATCH (c=%d,s=%d) len mine=%d profII=%d" % (c, s, len(xs), len(xs_ref)))
                # 注：table_lib 里 PROFII_D 的 am 分量是 [0]*34 占位（其 min 更新条件写错），
                # 只用 xs 做对拍；这里确认 am 确实是占位零向量。
                if any(am):
                    bad += 1
                    if bad <= 5:
                        print("  AM not placeholder (c=%d,s=%d)" % (c, s))
            miss = [k for k in g if (c, s, k) not in PII]
            # 反向：PROFII_D 有而我没有的键
            for (cc, ss, k) in PII:
                if cc == c and ss == s and k not in g:
                    bad += 1
                    print("  MISSING key (c=%d,s=%d)" % (c, s))
    return checked, bad


def main():
    t0 = time.time()
    order, cls, PII = load()
    print("classes=%d PROFII_D entries=%d" % (len(order), len(PII)), flush=True)

    checked, bad = check_python_enum(PII)
    print("python re-enumeration vs PROFII_D: checked %d keys, mismatches %d" % (checked, bad), flush=True)

    # ---- profTable: 16 组，键按 canonical 顺序 ----
    SIZES_II = (2, 5, 8, 11)
    groups = {}
    for c in range(4):
        for s in SIZES_II:
            ks = [k for (cc, ss, k) in PII if cc == c and ss == s]
            ks.sort(key=keytuple)
            infos = []
            for k in ks:
                xs = PII[(c, s, k)][1]
                infos.append((k, len(xs), sum(encX(X) for X in xs)))
            groups[(c, s)] = (ks, infos)
    ki = {}
    for (c, s), (ks, infos) in groups.items():
        for j, k in enumerate(ks):
            ki[(c, s, k)] = j
    print("profiles per group:", {("%d,%d" % k): len(v[0]) for k, v in sorted(groups.items())}, flush=True)

    # ---- combos and blocks ----
    combos = [(c1, s1, c2, s2) for c1 in range(4) for c2 in range(c1 + 1, 4)
              for s1 in SIZES_II for s2 in SIZES_II]
    ci = {cb: i for i, cb in enumerate(combos)}
    print("combos:", len(combos), flush=True)
    recs = []
    n_units = 0
    for idx, W in enumerate(order):
        for b in cls.get(W, []):
            if b[0] != 'II':
                continue
            k1, k2 = b[1], b[2]          # (c1,s1,k1key) / (c2,s2,k2key)
            (c1, s1) = k1[0], k1[1]
            (c2, s2) = k2[0], k2[1]
            j1 = ki[(c1, s1, k1[2])]
            j2 = ki[(c2, s2, k2[2])]
            cb = (c1, s1, c2, s2)
            recs.append(idx * (1 << 25) + ci[cb] * (1 << 18) + j1 * (1 << 9) + j2)
            n_units += len(PII[k1][1]) * len(PII[k2][1])
    print("II block records:", len(recs), "units:", n_units, flush=True)

    # ---- emit Lean ----
    L = []
    L.append("import Mj.Basic")
    L.append("")
    L.append("set_option maxHeartbeats 0")
    L.append("set_option maxRecDepth 200000")
    L.append("")
    L.append("namespace Mj")
    L.append("")
    L.append("/-- II 型 profile 键：k = (V, pd, odd, ot, a2, o2)；V 为 34 位掩码 -/")
    L.append("structure ProfKey where")
    L.append("  V : Nat")
    L.append("  pd : Bool")
    L.append("  odd : Nat")
    L.append("  ot : Option Nat")
    L.append("  a2 : Bool")
    L.append("  o2 : Bool")
    L.append("deriving BEq, DecidableEq, Repr")
    L.append("")
    L.append("structure ProfInfo where")
    L.append("  key : ProfKey")
    L.append("  nXs : Nat")
    L.append("  hXs : Nat")
    L.append("deriving Repr")
    L.append("")
    def pk(k):
        V, pd, odd, ot, a2, o2 = k
        mask = 0
        for t in V:
            mask |= 1 << t
        ots = "none" if ot is None else "some %d" % ot
        return ("{ V := %d, pd := %s, odd := %d, ot := %s, a2 := %s, o2 := %s }"
                % (mask, "true" if pd else "false", odd, ots,
                   "true" if a2 else "false", "true" if o2 else "false"))

    # profTable 的条目按 keyEnc 升序（与 Lean 的 aggOf 输出顺序一致）

    grow = []
    for (c, s) in sorted(groups):
        ks, infos = groups[(c, s)]
        ents = ["{ key := %s, nXs := %d, hXs := %d }" % (pk(k), n, h) for (k, n, h) in infos]
        if len(ents) <= 40:
            grow.append("  ((%d, %d), [%s])" % (c, s, ", ".join(ents)))
        else:
            pieces = [ents[i:i + 40] for i in range(0, len(ents), 40)]
            for j, p in enumerate(pieces):
                L.append("def pr_%d_%d_%d : List ProfInfo := [%s]" % (c, s, j, ", ".join(p)))
            nm = "pr_%d_%d" % (c, s)
            L.append("def %s : List ProfInfo := %s"
                     % (nm, " ++ ".join("pr_%d_%d_%d" % (c, s, j) for j in range(len(pieces)))))
            grow.append("  ((%d, %d), %s)" % (c, s, nm))
    L.append("/-- 每个 (cat,size) 的 profile 表（键 + 由 Python 侧算出的 |xs| 与 Σenc） -/")
    L.append("def profTable : List ((Nat × Nat) × List ProfInfo) := [")
    L.append(",\n".join(grow))
    L.append("]")
    L.append("")
    L.append("/-- (c1,s1,c2,s2) 组合表（96 个） -/")
    L.append("def combos : List (Nat × Nat × Nat × Nat) := [")
    L.append(", ".join("(%d, %d, %d, %d)" % cb for cb in combos))
    L.append("]")
    L.append("")
    L.append("/-- 309,144 个 II 块记录（编码 rec = classIdx*2^25 + comboIdx*2^18 + k1idx*2^9 + k2idx） -/")
    CH = 30
    BATCH = 64
    nch = (len(recs) + CH - 1) // CH
    for i in range(0, len(recs), CH):
        L.append("def blkChunk%d : List Nat := [%s]" % (i // CH, ", ".join(str(r) for r in recs[i:i + CH])))
    nb = (nch + BATCH - 1) // BATCH
    for b in range(nb):
        lo, hi = b * BATCH, min((b + 1) * BATCH, nch)
        L.append("def blkB%d : List Nat := %s"
                 % (b, " ++ ".join("blkChunk%d" % i for i in range(lo, hi))))
    L.append("def blocks : List Nat := " + " ++ ".join("blkB%d" % b for b in range(nb)))
    L.append("")
    L.append("def nIIBlocks : Nat := %d" % len(recs))
    L.append("def nIIUnitsTotal : Nat := %d" % n_units)
    L.append("def nIIProfiles : Nat := %d" % len(PII))
    L.append("")
    L.append("end Mj")
    src = "\n".join(L) + "\n"
    open(OUT, "w", encoding="utf-8").write(src)
    print("wrote %s (%.2f MB)  t=%.1fs" % (OUT, os.path.getsize(OUT) / 1e6, time.time() - t0), flush=True)
    json.dump({"n_blocks": len(recs), "n_units": n_units, "n_profiles": len(PII),
               "python_check_keys": checked, "python_check_mismatches": bad},
              open(os.path.join(ROOT, "work", "lean", "gen_data2_report.json"), "w"))


if __name__ == "__main__":
    main()
