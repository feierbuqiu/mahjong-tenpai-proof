#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lb_flush.py  ---  T3 (analyst-lower) 独立清一色普查 + tau 下界
写作用域: work/lowerbound/

独立于 work/data/mjcore.py 与 work/recon/recon_flush.py:
  * 手牌 = 34 维计数向量; 类别内花色向量用"最左非零位"递归分解 (穷尽, 见注释证明)
  * 清一色 13 张手牌 = 全部 9 元计数向量 (每型 <=4 张) 的完全枚举, 无遗漏
  * W(H) = W_std(H) ∪ W_chiitoi(H) ∪ W_kokushi(H)   (MODEL.md 第 1 节)
  * 码 = 有序 k 元组; 判不相交可等价地使用"无序多重集" (见 LOWERBOUND.md 命题 1)
输出: work/lowerbound/flush_report.json
"""
import itertools, json, sys, time
from functools import lru_cache

T0 = time.time()
BASE = {0: 0, 1: 9, 2: 18, 3: 27}
SIZE = {0: 9, 1: 9, 2: 9, 3: 7}
TERMINALS = (0, 8, 9, 17, 18, 26, 27, 28, 29, 30, 31, 32, 33)

@lru_cache(maxsize=None)
def melds_only(c):
    """c: tuple of counts for ONE category. Return min #melds to clear, or None.
    穷尽性证明: 设 i = 最小非零位. 任何覆盖 i 的面子只能是以 i 起的三张刻子,
    或 i,i+1,i+2 顺子 (i-1,i-2 处计数为 0, 不可能). 故两支即穷尽."""
    n = len(c)
    i = 0
    while i < n and c[i] == 0:
        i += 1
    if i == n:
        return 0
    best = None
    if c[i] >= 3:
        c2 = list(c); c2[i] -= 3
        r = melds_only(tuple(c2))
        if r is not None:
            best = r + 1
    if i + 2 < n and c[i+1] > 0 and c[i+2] > 0:
        c2 = list(c); c2[i] -= 1; c2[i+1] -= 1; c2[i+2] -= 1
        r = melds_only(tuple(c2))
        if r is not None and (best is None or r + 1 < best):
            best = r + 1
    return best

def is_std_win(cnt):
    """14 张标准型: 4 面子 + 1 雀头"""
    for i in range(34):
        if cnt[i] >= 2:
            c = list(cnt); c[i] -= 2
            tot = 0; ok = True
            for cat in range(4):
                b, n = BASE[cat], SIZE[cat]
                m = melds_only(tuple(c[b:b+n]))
                if m is None:
                    ok = False; break
                tot += m
            if ok and tot == 4:
                return True
    return False

def is_chiitoi_win(cnt):
    """14 张七对子"""
    n_pair = 0
    for x in cnt:
        if x == 0:
            continue
        if x != 2:
            return False
        n_pair += 1
    return n_pair == 7

def is_kokushi_win(cnt):
    """14 张国士: 幺九字全齐 + 其中一张重一次"""
    s = 0
    for i in range(34):
        if cnt[i] == 0:
            continue
        if i not in TERMINALS:
            return False
        s += cnt[i]
    if s != 14:
        return False
    return sum(1 for i in TERMINALS if cnt[i] >= 1) == 13

def waits(cnt, use_chiitoi=True, use_kokushi=True):
    """W(H): 返回排序后的可和牌元组"""
    res = []
    for t in range(34):
        if cnt[t] >= 4:
            continue
        c = list(cnt); c[t] += 1
        if is_std_win(c) or (use_chiitoi and is_chiitoi_win(c)) or (use_kokushi and is_kokushi_win(c)):
            res.append(t)
    return tuple(res)

# ---------------- 清一色 13 张手牌完全枚举 ----------------
def enumerate_flush(tile_base=0, ntypes=9):
    hands = []
    for c in itertools.product(range(5), repeat=ntypes):
        if sum(c) != 13:
            continue
        cnt = [0]*34
        for i, v in enumerate(c):
            if v:
                cnt[tile_base + i] = v
        hands.append(tuple(cnt))
    return hands

def main():
    variant = sys.argv[1] if len(sys.argv) > 1 else "full"
    use_chiitoi = (variant != "stdonly")
    hands = enumerate_flush()
    print("[%s] 清一色 13 张计数向量总数 = %d  (t=%.1fs)" % (variant, len(hands), time.time()-T0), flush=True)
    cls = {}
    for h in hands:
        W = waits(h, use_chiitoi=use_chiitoi)
        if W:
            cls.setdefault(W, []).append(h)
    print("清一色听牌手牌 = %d, 听牌类 = %d  (t=%.1fs)" % (sum(len(v) for v in cls.values()), len(cls), time.time()-T0), flush=True)

    # --- M_k 作为无序多重集 (9 型) ---
    combos = {k: list(itertools.combinations_with_replacement(range(9), k)) for k in (1, 2, 3, 4)}
    def Mset(h, k):
        out = set()
        for comb in combos[k]:
            ok = True
            for x in set(comb):
                if h[x] < comb.count(x):
                    ok = False; break
            if ok:
                out.add(comb)
        return out

    report = {"variant": variant, "n_hands": sum(len(v) for v in cls.values()), "n_classes": len(cls)}

    # ---- k=1: 精确 tau ----
    tau1 = {}
    for W, hs in cls.items():
        supps = [frozenset(i for i in range(9) if h[i] > 0) for h in hs]
        common = set(supps[0])
        for s in supps[1:]:
            common &= s
        if common:
            tau1[W] = 1
            continue
        # 精确最小命中小集合 (<=4 层)
        found = None
        for size in (2, 3, 4):
            for S in itertools.combinations(range(9), size):
                Ss = set(S)
                if all(Ss & s for s in supps):
                    found = size; break
            if found:
                break
        tau1[W] = found if found else 5
    s1 = sum(tau1.values())
    print("k=1: 类数=%d, 无公共码类=%d, sum tau = %d, tau 分布=%s" % (
        len(cls), sum(1 for v in tau1.values() if v >= 2), s1,
        {v: sum(1 for x in tau1.values() if x == v) for v in sorted(set(tau1.values()))}), flush=True)
    report["k1"] = {"sum_tau": s1, "no_common": sum(1 for v in tau1.values() if v >= 2),
                    "tau_dist": {str(v): sum(1 for x in tau1.values() if x == v) for v in sorted(set(tau1.values()))}}

    # ---- k=2,3,4: 公共码是否存在 ----
    for k in (2, 3, 4):
        noc = 0
        for W, hs in cls.items():
            cs = Mset(hs[0], k)
            for h in hs[1:]:
                cs &= Mset(h, k)
                if not cs:
                    break
            if not cs:
                noc += 1
        print("k=%d: 无公共码类 = %d / %d" % (k, noc, len(cls)), flush=True)
        report["k%d" % k] = {"no_common": noc}

    json.dump(report, open("work/lowerbound/flush_report.json", "w"), ensure_ascii=False, indent=1)
    print("written work/lowerbound/flush_report.json", flush=True)

if __name__ == "__main__":
    main()
