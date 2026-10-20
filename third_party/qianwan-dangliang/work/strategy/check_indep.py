# -*- coding: utf-8 -*-
"""check_indep.py -- 独立复核清一色数字(MODEL 6 节: 26680 手 / 383 类 / k=4 全有公共码)。"""
import sys, os, itertools, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjlib import *

BASE = 0

# ---------- A. 用"面子多重集"生成法独立枚举和牌(允许重复顺子!)
MELDS = []
for s in range(7):            # 顺子
    MELDS.append(tuple(sorted((s, s+1, s+2))))
for s in range(9):            # 刻子
    MELDS.append((s, s, s))
def vec_of(ms):
    c = [0]*9
    for m in ms:
        for x in m: c[x] += 1
    return tuple(c)
wins_ms = set()
for combo in itertools.combinations_with_replacement(range(len(MELDS)), 4):
    c = [0]*9
    for idx in combo:
        for x in MELDS[idx]: c[x] += 1
    if max(c) <= 4: wins_ms.add(tuple(c))
win14 = set()
for v in wins_ms:
    for pi in range(9):
        if v[pi] <= 2:
            w = list(v); w[pi] += 2
            win14.add(tuple(w))
print("A. 面子多重集法: 4面子多重集数=%d, 和牌14张=%d" % (len(wins_ms), len(win14)))

# ---------- B. 直接枚举所有 13 张多重集, 逐个判定是否听牌
tenpai_direct = set()
all13 = 0
for combo in itertools.combinations_with_replacement(range(9), 13):
    c = [0]*9
    for x in combo: c[x] += 1
    if max(c) > 4: continue
    all13 += 1
    ok = False
    for t in range(9):
        if c[t] < 4:
            d = list(c); d[t] += 1
            if pair_melds := any(d[pi] >= 2 and can_melds(tuple(
                    [d[j] - (2 if j == pi else 0) for j in range(9)]), False) for pi in range(9)):
                ok = True; break
    if ok: tenpai_direct.add(tuple(c))
print("B. 直接法: 13张多重集总数=%d, 听牌=%d" % (all13, len(tenpai_direct)))

# ---------- C. "和牌减一张"法
tenpai_sub = set()
for w in win14:
    for i in range(9):
        if w[i]:
            h = list(w); h[i] -= 1
            tenpai_sub.add(tuple(h))
print("C. 和牌减一张法: 听牌=%d" % len(tenpai_sub))
print("   直接法 == 减一张法 ?", tenpai_direct == tenpai_sub)

# ---------- D. 类与公共码
def wstd(h9):
    res = []
    for t in range(9):
        if h9[t] < 4:
            d = list(h9); d[t] += 1
            if any(d[pi] >= 2 and can_melds(tuple([d[j] - (2 if j == pi else 0) for j in range(9)]), False) for pi in range(9)):
                res.append(t)
    return tuple(res)
cls = {}
for h in tenpai_direct:
    cls.setdefault(frozenset(wstd(h)), []).append(h)
nocommon = {}
for k in (1,2,3,4):
    nc = 0
    for W, hs in cls.items():
        K = [min(h[i] for h in hs) for i in range(9)]
        if sum(K) < k: nc += 1
    nocommon[k] = nc
print("D. 类数=%d  无公共码 k=1..4 = %s" % (len(cls), nocommon))

# ---------- E. 反例: recon 的 gen_run_vecs 是否漏掉"重复顺子"?
#     具体手牌: 1122334455667 (六对+单张7) -> 听 7
h = [0]*9
for i in range(6): h[i] = 2
h[6] = 1
h = tuple(h)
print("E. h=%s 在直接法听牌集中: %s ; W(h)=%s" % (h, h in tenpai_direct, sorted(wstd(h))))
# recon 版 R4: 复刻其递归
def recon_R4():
    n=9; res=set()
    def rec(pos, remaining, vec):
        if remaining == 0: res.add(vec); return
        if pos >= n: return
        if vec[pos] <= 1:
            v=list(vec); v[pos]+=3
            if max(v)<=4: rec(pos+1, remaining-1, tuple(v))
        if pos+2 < n:
            v=list(vec)
            if v[pos]<4 and v[pos+1]<4 and v[pos+2]<4:
                v[pos]+=1; v[pos+1]+=1; v[pos+2]+=1
                rec(pos+1, remaining-1, tuple(v))
        rec(pos+1, remaining, vec)
    rec(0,4,tuple([0]*n)); return res
R4 = recon_R4()
print("   recon R4 数=%d (真值 %d), 缺 %d" % (len(R4), len(wins_ms), len(wins_ms - R4)))
# recon 的 tenpai 集
rec_ten = set()
for v in R4:
    for pi in range(9):
        if v[pi] <= 2:
            w = list(v); w[pi] += 2
            rec_ten.add(tuple(w))
rec_tp = set()
for w in rec_ten:
    for i in range(9):
        if w[i]:
            x = list(w); x[i] -= 1
            rec_tp.add(tuple(x))
print("   recon: 和牌=%d 听牌=%d 类=%d" % (len(rec_ten), len(rec_tp), len({frozenset(wstd(x)) for x in rec_tp})))
print("   recon 听牌集 ⊂ 真听牌集 ?", rec_tp <= tenpai_direct, " 差 =", len(tenpai_direct - rec_tp))
