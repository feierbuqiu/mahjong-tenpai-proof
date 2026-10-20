#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""work/lean/gen_data.py -- 生成 lean/Mj/Data.lean（计划 + I 型覆盖单元），并可核对覆盖性。

用法:
    python -u work/lean/gen_data.py                 # 生成 lean/Mj/Data.lean
    python -u work/lean/gen_data.py --check-ii 8    # 另跑 II 型 5,402,697 单元的严格覆盖检查

单元编码 (I 型) : u = cat * 6^9 + Σ_i count_i * 6^i   （cat∈0..3；counts 为该类别内计数向量）
"""
import sys, os, json, pickle, time, argparse
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PLAN = os.path.join(ROOT, "work", "verify", "plan_k4_FINAL.json")
TABLES = os.path.join(ROOT, "work", "strategy", "out", "table_cache.pkl")
OUT = os.path.join(ROOT, "lean", "Mj", "Data.lean")

HON = ["E", "S", "W", "N", "Haku", "Hatsu", "Chun"]
HONI = {n: 27 + i for i, n in enumerate(HON)}
BASE = [0, 9, 18, 27]
SIX9 = 6 ** 9


def to_idx(x):
    if isinstance(x, int):
        return x
    if x in HONI:
        return HONI[x]
    return "mps".index(x[-1]) * 9 + int(x[0]) - 1


def tile_cat(t):
    return t // 9 if t < 27 else 3


def load():
    P = json.load(open(PLAN, encoding="utf-8"))
    plan = {}
    order = []
    for r in P["plan"]:
        W = frozenset(to_idx(x) for x in r["W"])
        if W not in plan:
            plan[W] = []
            order.append(W)
        # 码是**有序**4 元组，必须保持原顺序（唯一性/不交性都是对有序元组而言）
        plan[W].extend(tuple(c) for c in r["codes"])
    sys.path.insert(0, os.path.join(ROOT, "work", "strategy"))
    sys.path.insert(0, os.path.join(ROOT, "work", "strategy", "out"))
    C = pickle.load(open(TABLES, "rb"))
    return plan, order, C["cls"], C["PROFI_D"], C["PROFII_D"]


def enc_unit(cat, X):
    e = cat * SIX9
    for i, v in enumerate(X):
        if v:
            e += v * 6 ** i
    return e


def iter_I(cls, PI):
    for W, blocks in cls.items():
        for b in blocks:
            if b[0] != 'I':
                continue
            key = b[1]
            e = PI.get(key)
            if not e:
                continue
            ci = key[0]
            for X in e[1]:
                yield W, ci, X


def code_ok_for_unit(c, A):
    """A: 34-vector; c: 4-tuple of tile indices"""
    for t in set(c):
        if A[t] < c.count(t):
            return False
    return True


def check_I(plan, cls, PI):
    bad = []
    n = 0
    for W, ci, X in iter_I(cls, PI):
        n += 1
        A = [0] * 34
        for i, v in enumerate(X):
            A[BASE[ci] + i] = v
        codes = plan.get(W, [])
        if not any(code_ok_for_unit(c, A) for c in codes):
            bad.append((W, ci, X))
    return n, bad


_II = {}


def _init_ii(plan, cls, PII):
    _II["plan"] = {W: [(c, [(t, c.count(t)) for t in set(c)]) for c in cs] for W, cs in plan.items()}
    _II["cls"] = cls
    _II["PII"] = PII


def _check_ii_chunk(Ws):
    plan, cls, PII = _II["plan"], _II["cls"], _II["PII"]
    n = 0
    bad = 0
    samples = []
    for W in Ws:
        codes = plan.get(W, [])
        for b in cls.get(W, []):
            if b[0] != 'II':
                continue
            k1, k2 = b[1], b[2]
            e1 = PII.get(k1)
            e2 = PII.get(k2)
            if not e1 or not e2:
                continue
            c1, c2 = k1[0], k2[0]
            cand = [sp for (c, sp) in codes if all(tile_cat(t) in (c1, c2) for t in c)]
            for X1 in e1[1]:
                base1 = [(BASE[c1] + i, v) for i, v in enumerate(X1) if v]
                for X2 in e2[1]:
                    n += 1
                    pts = base1 + [(BASE[c2] + i, v) for i, v in enumerate(X2) if v]
                    ok = False
                    for sp in cand:
                        good = True
                        for (t, k) in sp:
                            cc = dict(pts).get(t, 0)
                            if cc < k:
                                good = False
                                break
                        if good:
                            ok = True
                            break
                    if not ok:
                        bad += 1
                        if len(samples) < 3:
                            samples.append((sorted(W), k1, k2, X1, X2))
    return n, bad, samples


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-ii", type=int, default=0, help="进程数；>0 时跑 II 型检查")
    args = ap.parse_args()

    t0 = time.time()
    plan, order, cls, PI, PII = load()
    print("classes=%d codes=%d  (%.1fs)" % (len(plan), sum(len(v) for v in plan.values()), time.time() - t0), flush=True)

    nI, badI = check_I(plan, cls, PI)
    print("I units=%d  strict-coverage failures=%d" % (nI, len(badI)), flush=True)
    for b in badI[:5]:
        print("   fail W=%s cat=%d X=%s" % (sorted(b[0]), b[1], "".join(map(str, b[2]))), flush=True)

    nII = 0
    badII = 0
    if args.check_ii:
        t1 = time.time()
        Ws = list(cls.keys())
        nproc = args.check_ii
        chunks = [Ws[i::nproc] for i in range(nproc)]
        with Pool(nproc, initializer=_init_ii, initargs=(plan, cls, PII)) as pool:
            res = pool.map(_check_ii_chunk, chunks)
        nII = sum(r[0] for r in res)
        badII = sum(r[1] for r in res)
        print("II units=%d  strict-coverage failures=%d  (%.1fs)" % (nII, badII, time.time() - t1), flush=True)
        for r in res:
            for s in r[2]:
                print("   II fail W=%s k1=%s k2=%s" % (s[0], s[1], s[2]), flush=True)

    # ---------------- emit Lean data ----------------
    # 说明：巨型 list 字面量会让 Lean 的 elaborator 递归过深 / 心跳超限，
    # 因此每个字面量都切成 <= 200 项的小块，再用 ++ 拼起来（类型与接口不变）。
    def lean_list(xs):
        return "[" + ", ".join(str(x) for x in xs) + "]"

    blocks = []
    blocks.append("import Mj.Basic\n")
    blocks.append("set_option maxHeartbeats 0")
    blocks.append("set_option maxRecDepth 10000\n")
    blocks.append("namespace Mj\n")
    CH = 20        # 外层字面量每块行数
    PIECE = 40     # 单个类的码表每块条数
    UP = 150       # I 型单元每块条数
    rows = []
    # ---- planData：每个类的码表先切块，再按 20 行组块 ----
    for idx, W in enumerate(order):
        key = sorted(W)
        codes = plan[W]
        if len(codes) <= PIECE:
            code_expr = "[" + ", ".join(lean_list(c) for c in codes) + "]"
        else:
            pieces = [codes[i:i + PIECE] for i in range(0, len(codes), PIECE)]
            for j, p in enumerate(pieces):
                blocks.append("def pCode%d_%d : List (List Nat) := [%s]"
                              % (idx, j, ", ".join(lean_list(c) for c in p)))
            code_expr = " ++ ".join("pCode%d_%d" % (idx, j) for j in range(len(pieces)))
        rows.append("(" + lean_list(key) + ", " + code_expr + ")")
    blocks.append("/-- 计划: 类键(听牌索引递增) × 4 元码表; 数据源 work/verify/plan_k4_FINAL.json -/")
    npc = (len(rows) + CH - 1) // CH
    for i in range(npc):
        blocks.append("def planChunk%d : List (List Nat × List (List Nat)) := [%s]"
                      % (i, ",\n ".join(rows[i * CH:(i + 1) * CH])))
    blocks.append("def planData : List (List Nat × List (List Nat)) := " +
                  " ++ ".join("planChunk%d" % i for i in range(npc)) + "\n")
    # ---- I 型单元：每类一个 def（过大再切） ----
    blocks.append("/-- I 型覆盖单元 (168,817): 类键 × 编码单元列表; u = cat*6^9 + Σ_i count_i*6^i -/")
    class_rows = []
    for idx, W in enumerate(order):
        us = []
        for b in cls.get(W, []):
            if b[0] != 'I':
                continue
            key = b[1]
            e = PI.get(key)
            if not e:
                continue
            ci = key[0]
            for X in e[1]:
                us.append(enc_unit(ci, X))
        if not us:
            class_rows.append("(" + lean_list(sorted(W)) + ", [])")
            continue
        if len(us) <= UP:
            blocks.append("def uRow%d : List Nat := %s" % (idx, lean_list(us)))
        else:
            pieces = [us[i:i + UP] for i in range(0, len(us), UP)]
            for j, p in enumerate(pieces):
                blocks.append("def uRow%d_%d : List Nat := %s" % (idx, j, lean_list(p)))
            blocks.append("def uRow%d : List Nat := %s"
                          % (idx, " ++ ".join("uRow%d_%d" % (idx, j) for j in range(len(pieces)))))
        class_rows.append("(" + lean_list(sorted(W)) + ", uRow%d)" % idx)
    nuc = (len(class_rows) + CH - 1) // CH
    for i in range(nuc):
        blocks.append("def unitOuter%d : List (List Nat × List Nat) := [%s]"
                      % (i, ",\n ".join(class_rows[i * CH:(i + 1) * CH])))
    blocks.append("def iUnitData : List (List Nat × List Nat) := " +
                  " ++ ".join("unitOuter%d" % i for i in range(nuc)) + "\n")
    # ---- 反例 ----
    fails = sorted(set((tuple(sorted(W)), enc_unit(ci, X)) for (W, ci, X) in badI))
    blocks.append("/-- 未通过『存在码 ⊆ A』的 I 型单元（严格检查的反例，共 %d 个） -/" % len(fails))
    for i in range(0, len(fails), CH):
        blocks.append("def failChunk%d : List (List Nat × Nat) := [%s]"
                      % (i // CH, ",\n ".join("(" + lean_list(list(k)) + ", " + str(u) + ")" for k, u in fails[i:i + CH])))
    blocks.append("def iUnitFailures : List (List Nat × Nat) := " +
                  " ++ ".join("failChunk%d" % i for i in range((len(fails) + CH - 1) // CH)) + "\n")
    # ---- 补牌族表：每个类别、每个张数(0,3,6,9,12) 的全部面子并集计数向量 ----
    def build_dec(idx):
        L = 7 if idx == 3 else 9
        units = []
        if idx < 3:
            for st in range(L - 2):
                v = [0] * L
                v[st] = v[st + 1] = v[st + 2] = 1
                units.append(tuple(v))
        for t in range(L):
            v = [0] * L
            v[t] = 3
            units.append(tuple(v))
        out = {}
        for s in range(0, 13, 3):
            res = set()
            def rec(i, left, acc):
                if left == 0:
                    res.add(acc); return
                for j in range(i, len(units)):
                    u = units[j]
                    if all(acc[k] + u[k] <= 4 for k in range(L)):
                        rec(j, left - 3, tuple(acc[k] + u[k] for k in range(L)))
            rec(0, s, (0,) * L)
            out[s] = [list(v) for v in sorted(res)]
        return out
    FILL = [build_dec(i) for i in range(4)]
    SQ = len(order)
    blocks.append("/-- 补牌族表: 类别 c 中由面子(刻子/顺子, 每张 <=4)拼成、恰 s 张的全部计数向量 -/")
    names = []
    for c in range(4):
        for s in (0, 3, 6, 9, 12):
            vecs = FILL[c].get(s, [])
            nmdef = "fill_%d_%d" % (c, s)
            names.append((c, s, nmdef))
            if len(vecs) <= 100:
                blocks.append("def %s : List (List Nat) := [%s]"
                              % (nmdef, ", ".join(lean_list(v) for v in vecs)))
            else:
                pc = [vecs[i:i + 100] for i in range(0, len(vecs), 100)]
                for j, p in enumerate(pc):
                    blocks.append("def %s_%d : List (List Nat) := [%s]"
                                  % (nmdef, j, ", ".join(lean_list(v) for v in p)))
                blocks.append("def %s : List (List Nat) := %s"
                              % (nmdef, " ++ ".join("%s_%d" % (nmdef, j) for j in range(len(pc)))))
    cs_lines = ["  | %d, %d => %s" % (c, s, nm) for (c, s, nm) in names]
    blocks.append("def fillOf (c s : Nat) : List (List Nat) :=\n  match c, s with\n" +
                  "\n".join(cs_lines) + "\n  | _, _ => []\n")
    blocks.append("def nFillVectors : Nat := %d" % sum(len(FILL[c].get(s, [])) for c in range(4) for s in (0,3,6,9,12)))
    blocks.append("def nUnitFailures : Nat := %d" % len(fails))
    blocks.append("def nClasses : Nat := %d" % len(order))
    blocks.append("def nCodes : Nat := %d" % sum(len(v) for v in plan.values()))
    blocks.append("def nIUnits : Nat := %d" % nI)
    blocks.append("def nIIUnits : Nat := %d" % (nII if nII else 5402697))
    blocks.append("/-- II 型单元中不满足『存在码 ⊆ A』严格检查的个数"
                  "（由 gen_data.py --check-ii 测得；见 Upper.lean 的 assumption 说明） -/")
    blocks.append("def nIIStrictFailures : Nat := %d" % (badII if args.check_ii else 116))
    blocks.append("def six9 : Nat := %d" % SIX9)
    blocks.append("\nend Mj\n")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(blocks))
    print("wrote %s  (%.2f MB)" % (OUT, os.path.getsize(OUT) / 1e6), flush=True)
    print("t=%.1fs" % (time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
