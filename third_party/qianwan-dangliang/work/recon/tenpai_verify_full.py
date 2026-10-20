
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""work/recon/tenpai_verify_full.py -- 全局独立枚举 (task-20 复核, verifier).
路径 B 独立版: 枚举全部 14 张标准和牌 W (4 面子+对, 去重) -> H = W - t 去重 = 标准型听牌手牌.
同时对同一 H 集合按“惰性类别面子多重集之积”口径求和 (= 审计 t15 未去重口径), 并统计与七对/国士重叠.
"""
import sys, os, json, time, itertools
from math import comb
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from tenpai_verify_indep import dec_table, LEN, BASE, ORPH, POW5, SH, OUT

def melds34():
    melds = []
    for ci in range(4):
        b = BASE[ci]; L = LEN[ci]
        if ci < 3:
            for st in range(L - 2):
                v = [0] * 34
                for k in range(3): v[b + st + k] = 1
                melds.append(tuple(v))
        for t in range(L):
            v = [0] * 34; v[b + t] = 3; melds.append(tuple(v))
    return melds

def decode_keys(keys):
    N = len(keys); out = np.zeros((N, 34), dtype=np.uint8)
    lo = keys[:, 0]; hi = keys[:, 1]
    for i in range(34):
        src = lo if i < 21 else hi
        out[:, i] = ((src >> np.uint64(3 * (i if i < 21 else i - 21))) & np.uint64(7)).astype(np.uint8)
    return out

def encode_rows(rows):
    N = len(rows)
    lo = np.zeros(N, dtype=np.uint64); hi = np.zeros(N, dtype=np.uint64)
    for i in range(21): lo += rows[:, i].astype(np.uint64) * np.uint64(SH[i])
    for i in range(21, 34): hi += rows[:, i].astype(np.uint64) * np.uint64(SH[i - 21])
    return np.stack([lo, hi], axis=1)

def main():
    t0 = time.time()
    dec = [dec_table(c, None) for c in range(4)]
    M = np.array(melds34(), dtype=np.int16)
    combos = list(itertools.combinations_with_replacement(range(len(M)), 4))
    lo_parts = []; hi_parts = []; CH = 20000
    for i in range(0, len(combos), CH):
        ch = combos[i:i + CH]
        S = M[np.array(ch).ravel()].reshape(len(ch), 4, 34).sum(axis=1).astype(np.int16)
        S = S[S.max(axis=1) <= 4]
        base_lo = np.zeros(len(S), dtype=np.uint64); base_hi = np.zeros(len(S), dtype=np.uint64)
        for j in range(21): base_lo += S[:, j].astype(np.uint64) * np.uint64(SH[j])
        for j in range(21, 34): base_hi += S[:, j].astype(np.uint64) * np.uint64(SH[j - 21])
        for p in range(34):
            m = S[:, p] <= 3
            l2 = base_lo[m].copy(); h2 = base_hi[m].copy()
            if p < 21: l2 += np.uint64(SH[p])
            else: h2 += np.uint64(SH[p - 21])
            lo_parts.append(l2); hi_parts.append(h2)
    K = np.stack([np.concatenate(lo_parts), np.concatenate(hi_parts)], axis=1)
    del lo_parts, hi_parts
    Wk = np.unique(K, axis=0); del K
    nW = len(Wk)
    print("14 张标准和牌 W (去重) = %d  (%.1fs)" % (nW, time.time() - t0), flush=True)
    Wd = decode_keys(Wk); del Wk
    hp = []
    for t in range(34):
        m = Wd[:, t] > 0
        if not m.any(): continue
        sub = Wd[m].copy(); sub[:, t] -= 1
        hp.append(np.unique(encode_rows(sub), axis=0))
    Hk = np.unique(np.concatenate(hp), axis=0); del hp, Wd
    canon = len(Hk)
    print("标准型听牌手牌 H (去重) = %d  (%.1fs)" % (canon, time.time() - t0), flush=True)
    ovch = ovko = 0; naive = 0
    B = 2000000
    for i in range(0, canon, B):
        blk = decode_keys(Hk[i:i + B])
        n1 = (blk == 1).sum(axis=1); n2 = (blk == 2).sum(axis=1)
        ovch += int(((n1 == 1) & (n2 == 6)).sum())
        so = blk[:, ORPH].sum(axis=1); mx = blk[:, ORPH].max(axis=1); two = (blk[:, ORPH] == 2).sum(axis=1)
        ovko += int(((so == 13) & (mx <= 2) & (two <= 1)).sum())
        mult = np.ones(len(blk), dtype=np.int64)
        for c in range(4):
            s = blk[:, BASE[c]:BASE[c] + LEN[c]].sum(axis=1)
            iv = np.zeros(len(blk), dtype=np.int64)
            for j in range(LEN[c]): iv += blk[:, BASE[c] + j].astype(np.int64) * POW5[j]
            mult *= np.where(s % 3 == 0, dec[c][iv].astype(np.int64), 1)
        naive += int(mult.sum())
    chiitoi = comb(34, 6) * 28
    ko = 157
    out = {"winning_vectors": nW, "standard_canonical": canon, "standard_naive": naive,
           "excess": naive - canon, "ov_std_chiitoi": ovch, "ov_std_kokushi": ovko,
           "chiitoi": chiitoi, "kokushi": ko,
           "total_canonical": canon + chiitoi + ko - ovch - ovko,
           "total_naive": naive + chiitoi + ko - ovch - ovko,
           "sec": round(time.time() - t0, 1)}
    json.dump(out, open(os.path.join(OUT, "tenpai_verify_full.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1), flush=True)

if __name__ == "__main__":
    main()
