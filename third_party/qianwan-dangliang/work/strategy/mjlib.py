# -*- coding: utf-8 -*-
"""work/strategy/mjlib.py -- designer-encoder 自用核心库（独立实现，供 T4 策略/自检使用）。

牌模型: 0-8=1m..9m, 9-17=1p..9p, 18-26=1s..9s, 27-33=1z..7z(东..中)
类别: 0=m,1=p,2=s,3=z(7 种字牌整体一类)
所有手牌用长度 34 的计数元组表示。
"""
from functools import lru_cache
from itertools import combinations_with_replacement, permutations

N = 34
CAT_BASE = (0, 9, 18, 27)
CAT_LEN = (9, 9, 9, 7)
CAT_NAME = ("m", "p", "s", "z")


def cat_of(t):
    if t < 9:
        return 0
    if t < 18:
        return 1
    if t < 27:
        return 2
    return 3


def tile_name(t):
    return "%d%s" % (t - CAT_BASE[cat_of(t)] + 1, CAT_NAME[cat_of(t)])


def counts(tiles):
    c = [0] * N
    for t in tiles:
        c[t] += 1
    return tuple(c)


def tiles_of(c):
    out = []
    for i, n in enumerate(c):
        out.extend([i] * n)
    return out


def n_cards(c):
    return sum(c)


# ---------------------------------------------------------------- 面子分解
@lru_cache(maxsize=None)
def can_melds(seg, honors):
    """seg: 单类别计数元组; honors=True 时只允许刻子。"""
    seg = list(seg)
    i = 0
    length = len(seg)
    while i < length and seg[i] == 0:
        i += 1
    if i == length:
        return True
    if seg[i] >= 3:
        nxt = seg[:]
        nxt[i] -= 3
        if can_melds(tuple(nxt), honors):
            return True
    if not honors and i + 2 < length and seg[i + 1] and seg[i + 2]:
        nxt = seg[:]
        nxt[i] -= 1
        nxt[i + 1] -= 1
        nxt[i + 2] -= 1
        if can_melds(tuple(nxt), honors):
            return True
    return False


def cats_can_melds(c):
    for ci in range(4):
        b, L = CAT_BASE[ci], CAT_LEN[ci]
        if not can_melds(tuple(c[b:b + L]), ci == 3):
            return False
    return True


# ---------------------------------------------------------------- 和牌判定
def win_std(c14):
    """14 张：标准型 4 面子 + 雀头。"""
    if sum(c14) != 14:
        return False
    for p in range(N):
        if c14[p] >= 2:
            d = list(c14)
            d[p] -= 2
            if cats_can_melds(d):
                return True
    return False


def win_chiitoi(c14):
    """严格口径(天凤): 7 个**不同**牌种的对子; 4 张同牌不算两对。"""
    return sum(c14) == 14 and sum(1 for x in c14 if x == 2) == 7


KOKUSHI_TILES = (0, 8, 9, 17, 18, 26, 27, 28, 29, 30, 31, 32, 33)


def win_kokushi(c14):
    if sum(c14) != 14:
        return False
    for t in range(N):
        if c14[t] and t not in KOKUSHI_TILES:
            return False
    if all(c14[t] >= 1 for t in KOKUSHI_TILES):
        return True
    return False


def win14(c14):
    return win_std(c14) or win_chiitoi(c14) or win_kokushi(c14)


def waits13(c13):
    """返回 frozenset of 听牌牌值（W(H) 完整定义）。"""
    res = set()
    for t in range(N):
        if c13[t] < 4:
            d = list(c13)
            d[t] += 1
            if win14(tuple(d)):
                res.add(t)
    return frozenset(res)


# ---------------------------------------------------------------- k-码
def submults(c, k):
    """返回 H 的所有大小 k 子多重集（规范形：元组排序后）"""
    present = tiles_of(c)
    out = set()
    for combo in combinations_with_replacement(present, k):
        # combo 已有序；但需检查多重数
        ok = True
        need = {}
        for x in combo:
            need[x] = need.get(x, 0) + 1
        for x, n in need.items():
            if c[x] < n:
                ok = False
                break
        if ok:
            out.add(combo)
    return out


def perms_of_multiset(m):
    return set(permutations(m))


def multiset_capacity(m):
    """该多重集可产生的不同有序 k 元组个数 = k!/prod(mult!)"""
    from math import factorial
    den = 1
    for x in set(m):
        den *= factorial(m.count(x))
    return factorial(len(m)) // den


# ---------------------------------------------------------------- 结构：主动部/惰性部
def remainder_type(c):
    return tuple(x % 3 for x in (sum(c[0:9]), sum(c[9:18]), sum(c[18:27]), sum(c[27:34])))


def active_cats(c):
    """返回主动类别列表（余数 ∈{1,2} 的类别）。"""
    return tuple(ci for ci in range(4) if remainder_type(c)[ci] in (1, 2))


def split_active(c):
    """返回 (A, F, cats_active, cats_lazy)"""
    ca = active_cats(c)
    A = [0] * N
    F = [0] * N
    for ci in range(4):
        b, L = CAT_BASE[ci], CAT_LEN[ci]
        tgt = A if ci in ca else F
        for t in range(b, b + L):
            tgt[t] = c[t]
    return tuple(A), tuple(F), ca


def melds_in(c):
    """若每个类别都能拆成面子则返回面子总数，否则 None"""
    tot = 0
    for ci in range(4):
        b, L = CAT_BASE[ci], CAT_LEN[ci]
        seg = c[b:b + L]
        s = sum(seg)
        if s % 3:
            return None
        if not can_melds(tuple(seg), ci == 3):
            return None
        tot += s // 3
    return tot
