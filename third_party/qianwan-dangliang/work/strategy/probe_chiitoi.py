# -*- coding: utf-8 -*-
"""probe_chiitoi.py -- 检验 lead 的 chiitoi 附加规则完备性。

规则(lead 消息): 只有 (|F|=0 且 odd(A)=1) 或 (|F|=3 且 odd(A)=0) 才会出现 chiitoi 附加。
本脚本用完整的 W(H) 计算寻求反例。
"""
import sys, itertools
sys.path.insert(0, r"D:\DSH\MJ2\work\strategy")
from mjlib import *

def show(c):
    return "".join(tile_name(t) * n for t, n in enumerate(c))

def odd_cnt(c):
    return sum(1 for x in c if x % 2)

# ---------- 1. 具体反例: |A|=7 (m 内), odd(A)=1 ; F = 两条相同顺子 123p+123p (全偶, odd(F)=0)
A = counts([0, 0, 1, 1, 2, 2, 2])          # 1m1m2m2m3m3m3m
F = counts([9, 9, 10, 10, 11, 11])          # 1p1p2p2p3p3p
H = tuple(a + b for a, b in zip(A, F))
print("反例: A =", show(A), "|A|=", n_cards(A), "odd(A)=", odd_cnt(A))
print("      F =", show(F), "melds =", melds_in(F), "odd(F)=", odd_cnt(F))
print("      H =", show(H), "|H|=", n_cards(H), "odd(H)=", odd_cnt(H))
std = set()
for t in range(34):
    if H[t] < 4:
        d = list(H); d[t] += 1
        if win_std(tuple(d)): std.add(t)
Wh = set(waits13(H))
print("      W_std(A) [=W_std(H)] =", sorted(tile_name(t) for t in std))
print("      W(H) 完整            =", sorted(tile_name(t) for t in Wh))
print("      chiitoi 附加         =", sorted(tile_name(t) for t in Wh - std))
print()

# ---------- 2. 系统性扫描: 对若干 (|A|, F) 组合, 枚举所有 A, 统计 chiitoi 附加情况
def cat_vectors(size, length, cap=4):
    for combo in itertools.combinations_with_replacement(range(length), size):
        c = [0] * length
        for x in combo: c[x] += 1
        if max(c) <= cap: yield tuple(c)

# 惰性补牌族: 给定类别内 size 张可拆面子的多重集
def meld_multisets(size, length, honors=False):
    if size % 3: return []
    res = []
    for combo in itertools.combinations_with_replacement(range(length), size):
        c = [0] * length
        for x in combo: c[x] += 1
        if max(c) <= 4 and can_melds(tuple(c), honors): res.append(tuple(c))
    return res

P6 = meld_multisets(6, 9)      # p 内 6 张可拆面子
P9 = meld_multisets(9, 9)
P12 = meld_multisets(12, 9)
print("p 内可拆面子的多重集数: 6张=%d, 9张=%d, 12张=%d" % (len(P6), len(P9), len(P12)))
print()

# F 例子(全部放在 p 类, 其他惰性类 0 张; 也允许混合见后)
F_examples = {}
for f in P6:
    if odd_cnt(f) == 0: F_examples.setdefault("P6_odd0", []).append(f)
for f in P9:
    if odd_cnt(f) == 1: F_examples.setdefault("P9_odd1", []).append(f)
for f in P12:
    if odd_cnt(f) == 0: F_examples.setdefault("P12_odd0", []).append(f)
for f in P6:
    if odd_cnt(f) == 1: F_examples.setdefault("P6_odd1", []).append(f)
for k in F_examples: print("F 例子族 %-10s 个数=%d  例: %s" % (k, len(F_examples[k]), show(F_examples[k][0])))
print()

# 取每个族的少量样本, 与所有 |A| 对应的 A 向量组合, 比较 W(H) 与 W_std(A)
sizes_A = {13: 0, 10: 3, 7: 6, 4: 9, 1: 12}
report = {}
for sizeA, Ftot in sizes_A.items():
    A_vecs = list(cat_vectors(sizeA, 9))
    key = None
    if Ftot == 0: key = None   # 无惰性: F = {} 唯一
    print("### |A|=%d, |F|=%d : A 向量 %d 个" % (sizeA, Ftot, len(A_vecs)))
    stat = {}
    for fname, flist in ([("empty", [tuple([0]*9)])] if Ftot == 0 else
                         [(k, v[:3]) for k, v in F_examples.items()]):
        mism = 0; tot = 0; oddA1 = 0; ex = None
        for A9 in A_vecs:
            A34 = tuple(A9) + tuple([0]*25)
            # 只保留 A 本身"能被完成"的(标准听牌非空) —— 这里全保留, 用正例统计数据
            for f in flist:
                F34 = tuple([0]*9) + tuple(f) + tuple([0]*16)
                H = tuple(a + b for a, b in zip(A34, F34))
                if n_cards(H) != 13: continue
                tot += 1
                if odd_cnt(A34) == 1: oddA1 += 1
                # lead 规则预测
                pred = (Ftot == 0 and odd_cnt(A34) == 1) or (Ftot == 3 and odd_cnt(A34) == 0)
                std = set()
                for t in range(34):
                    if H[t] < 4:
                        d = list(H); d[t] += 1
                        if win_std(tuple(d)): std.add(t)
                # 真实 chiitoi 附加
                chi = set(waits13(H)) - std
                real = len(chi) > 0
                if real != pred:
                    mism += 1
                    if ex is None and real and not pred:
                        ex = (show(A34), show(F34), sorted(tile_name(t) for t in chi))
        print("    F族=%-9s 组合数=%d  odd(A)=1 个数=%d  规则不符=%d" % (fname, tot, oddA1, mism))
        if ex: print("      反例: A=%s  F=%s  chiitoi附加=%s" % ex)
