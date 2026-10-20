
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""work/recon/tenpai_verify_indep.py -- task-20 独立复核 (verifier 独立实现, 不复用 designer 脚本)

  python -u work/recon/tenpai_verify_indep.py --witness
  python -u work/recon/tenpai_verify_indep.py --small
  python -u work/recon/tenpai_verify_indep.py --full
  python -u work/recon/tenpai_verify_indep.py --report
最多 4 进程; 结果写 work/recon/out/tenpai_verify_indep.json
"""
import sys, os, json, time, itertools
from math import comb
from multiprocessing import Pool
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
LEN = [9, 9, 9, 7]; BASE = [0, 9, 18, 27]
ORPH = [0, 8, 9, 17, 18, 26, 27, 28, 29, 30, 31, 32, 33]
POW5 = [5 ** i for i in range(9)]
SH = [1 << (3 * i) for i in range(34)]
RES = {}

def cat_units(ci, allowed=None):
    L = LEN[ci]; units = []
    if ci < 3:
        for st in range(L - 2):
            if allowed is None or all((st + k) in allowed for k in range(3)):
                u = [0] * L
                for k in range(3): u[st + k] = 1
                units.append(tuple(u))
    for t in range(L):
        if allowed is not None and t not in allowed: continue
        u = [0] * L; u[t] = 3; units.append(tuple(u))
    return units

_DEC = {}
def dec_table(ci, allowed=None):
    key = (ci, None if allowed is None else tuple(sorted(allowed)))
    if key in _DEC: return _DEC[key]
    L = LEN[ci]
    units = cat_units(ci, allowed)
    tbl = np.zeros(5 ** L, dtype=np.int32); memo = {}
    def cnt_from(j, v):
        """用下标 >= j 的面子多重集拼出 v 的方案数 (每个多重集只计一次)"""
        if not any(v): return 1
        key = (j, v)
        if key in memo: return memo[key]
        tot = 0
        for k in range(j, len(units)):
            u = units[k]
            if all(u[i] <= v[i] for i in range(L)):
                tot += cnt_from(k, tuple(v[i] - u[i] for i in range(L)))
        memo[key] = tot; return tot
    def cnt(v): return cnt_from(0, v)
    for idx in range(5 ** L):
        v = []; r = idx
        for _ in range(L): v.append(r % 5); r //= 5
        if sum(v) <= 13: tbl[idx] = cnt(tuple(v))
    _DEC[key] = tbl; return tbl

def dec_tables_for(types):
    cats = sorted(set((t // 9) if t < 27 else 3 for t in types))
    out = []
    for c in range(4):
        if c in cats:
            allowed = set((t % 9) if c < 3 else (t - 27) for t in types
                          if ((t // 9) if t < 27 else 3) == c)
            out.append(dec_table(c, allowed))
        else:
            out.append(dec_table(c, None))
    return out

def cat_idx(full34, c):
    idx = 0; b = BASE[c]
    for i in range(LEN[c]): idx += full34[b + i] * POW5[i]
    return idx

def std_win(full, dec):
    """标准型和牌: 4 面子 + 1 雀头 (只用 dec 表; 字牌表无顺子)"""
    for c in range(4):
        ok = True
        for c2 in range(4):
            if c2 != c and dec[c2][cat_idx(full, c2)] == 0: ok = False; break
        if not ok: continue
        b = BASE[c]
        for i in range(LEN[c]):
            t = b + i
            if full[t] >= 2:
                full[t] -= 2
                good = dec[c][cat_idx(full, c)]
                full[t] += 2
                if good: return True
    return False

# ---------------- 手牌枚举 (宇宙) ----------------
def hands_of_chunk(types, total, order_lo, order_hi):
    n = len(types); out = []
    def rec(i, rem, cur, rank):
        # rank = 该分支覆盖的手牌数下界用不上; 直接全部生成再切分
        pass
    # 直接生成全部 (宇宙规模有限), 由调用方切分
    allh = []
    def rec2(i, rem, cur):
        if i == n:
            if rem == 0: allh.append(tuple(cur))
            return
        for k in range(0, min(4, rem) + 1):
            cur.append(k); rec2(i + 1, rem - k, cur); cur.pop()
    rec2(0, total, [])
    return allh[order_lo:order_hi]

def _small_worker(arg):
    types, rows = arg
    dec = dec_tables_for(types)
    canon = naive = waitpairs = ovch = ovko = 0
    n = 0
    for row in rows:
        n += 1
        full = [0] * 34
        for j, t in enumerate(types): full[t] = row[j]
        w = False
        for t in types:
            if full[t] >= 4: continue
            full[t] += 1
            if std_win(full, dec): w = True; waitpairs += 1
            full[t] -= 1
        if not w: continue
        canon += 1
        m = 1
        for c in range(4):
            if sum(full[BASE[c]:BASE[c] + LEN[c]]) % 3 == 0:
                m *= int(dec[c][cat_idx(full, c)])
        naive += m
        if sum(1 for t in types if full[t] == 1) == 1 and sum(1 for t in types if full[t] == 2) == 6:
            ovch += 1
        if all(t in ORPH for t in types):
            so = sum(full[t] for t in ORPH)
            if so == 13 and all(full[t] <= 2 for t in ORPH) and sum(1 for t in ORPH if full[t] == 2) <= 1:
                ovko += 1
    return (n, canon, naive, waitpairs, ovch, ovko)

def run_small(types, label, nproc=4):
    t0 = time.time()
    cnt = [0]
    def rec(i, rem, cur):
        if i == len(types):
            if rem == 0: cnt[0] += 1
            return
        for k in range(0, min(4, rem) + 1):
            cur.append(k); rec(i + 1, rem - k, cur); cur.pop()
    rec(0, 13, [])
    total = cnt[0]
    allh = []
    def gen(i, rem, cur):
        if i == len(types):
            if rem == 0: allh.append(tuple(cur))
            return
        for k in range(0, min(4, rem) + 1):
            cur.append(k); gen(i + 1, rem - k, cur); cur.pop()
    gen(0, 13, [])
    step = max(1, total // (nproc * 8))
    jobs = [(types, allh[i:i + step]) for i in range(0, total, step)]
    with Pool(nproc) as pool:
        parts = pool.map(_small_worker, jobs)
    n = sum(p[0] for p in parts); canon = sum(p[1] for p in parts)
    naive = sum(p[2] for p in parts); wp = sum(p[3] for p in parts)
    ovch = sum(p[4] for p in parts); ovko = sum(p[5] for p in parts)
    r = {"universe": label, "types": types, "hands": n, "canonical": canon, "naive": naive,
         "excess": naive - canon, "wait_pairs": wp, "ov_chiitoi": ovch, "ov_kokushi": ovko,
         "sec": round(time.time() - t0, 1)}
    print("  %-34s hands=%-9d canonical=%-8d naive=%-8d excess=%-6d (%.1fs)" %
          (label, n, canon, naive, naive - canon, r["sec"]), flush=True)
    return r

def mode_small():
    print("== 子宇宙逐手暴力 (verifier 独立实现) ==", flush=True)
    res = []
    res.append(run_small([0, 1, 2, 9, 10, 11], "1m2m3m1p2p3p"))
    res.append(run_small([0, 1, 2, 3, 4, 9], "1m2m3m4m5m1p"))
    res.append(run_small([0, 8, 9, 17, 18, 26, 27, 31], "1m9m1p9p1s9s东中"))
    res.append(run_small(list(range(9)), "清一色 m1..m9"))
    res.append(run_small([0, 1, 2, 3, 9, 10, 11, 12], "1m2m3m4m1p2p3p4p"))
    res.append(run_small([1, 2, 3, 27], "2m3m4m东"))
    res.append(run_small([1, 2, 3, 9, 10, 11], "2m3m4m1p2p3p"))
    res.append(run_small([0, 1, 2, 3, 4, 5, 9, 10, 11, 12, 13, 14], "m1-6 + p1-6 (12 张牌)"))
    RES["small"] = res

def mode_witness():
    print("== 最小见证 ==", flush=True)
    types = [18, 19, 20, 21] + [27]      # 1s2s3s4s + 东 (H 里 1s2s3s4s 各 3 张)
    H = [0] * 34
    H[18] = H[19] = H[20] = H[21] = 3; H[27] = 1
    dec = dec_tables_for(list(range(34)))
    waits = []
    for t in range(34):
        if H[t] >= 4: continue
        H[t] += 1
        if std_win(H, dec): waits.append(t)
        H[t] -= 1
    # H+东 的面子多重集分解数 (2 个类别: s 门的 111222333444, 东 的 1 张)
    svec = [H[18 + i] for i in range(9)]
    decs = int(dec[2][cat_idx(H, 2)])
    mult = 1
    for c in range(4):
        if sum(H[BASE[c]:BASE[c] + LEN[c]]) % 3 == 0:
            mult *= int(dec[c][cat_idx(H, c)])
    print("  H = 111222333444s + 东 (13 张): waits_std = %s" % waits, flush=True)
    print("  s 门 111222333444 的面子多重集分解数 = %d ; naive 口径计数 = %d ; canonical = 1" % (decs, mult), flush=True)
    RES["witness"] = {"hand": "111222333444s+E", "waits": waits, "decomp_count_s": decs, "naive_count": mult}
    # 列出 3 种分解
    units = cat_units(2)
    sols = []
    def rec(i, left, acc, pick):
        if left == 0:
            if all(x == 0 for x in acc): sols.append(list(pick))
            return
        for j in range(i, len(units)):
            u = units[j]
            if all(acc[k] >= u[k] for k in range(9)):
                na = [acc[k] - u[k] for k in range(9)]
                rec(j, left - 3, na, pick + [u])
    rec(0, 12, svec, [])
    def fmt(u):
        s = ""
        for i, x in enumerate(u):
            if x: s += "%d s" % (i + 1)
        return s
    print("  分解: %s" % [ " + ".join(fmt(u) for u in sol) for sol in sols ], flush=True)
    RES["witness"]["solutions"] = [[[("s%d" % (i + 1), u[i]) for i in range(9) if u[i]] for u in sol] for sol in sols]

if __name__ == "__main__":
    args = sys.argv[1:]
    if "--witness" in args: mode_witness()
    if "--small" in args: mode_small()
    json.dump(RES, open(os.path.join(OUT, "tenpai_verify_indep.json"), "w"), ensure_ascii=False, indent=1)
    print("wrote out/tenpai_verify_indep.json", flush=True)
