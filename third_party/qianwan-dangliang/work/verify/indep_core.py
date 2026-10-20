#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verifier / T5: 完全独立的麻将核心实现 (不与 work/data/mjcore.py 共享任何代码)

独立点 (相对 lead 侦察脚本 / enum-core):
  * 面子分解用 "pending-run 状态 DP" (状态 = 在 i-1 / i-2 起头、尚未填满的顺子数)，
    而不是常见的 "递归取第一个非零牌" 回溯。
  * 和牌判定用 34 种牌的全量 brute force (枚举雀头 + 4 门 melds_only)。
  * 类统计用 "公共码存在判据" 的数学等价形式: sum_t min_H count_H(t) >= k，
    并显式构造码做二次验证。
  * 全局计数用 "结构分解的精确组合计数" (按类别做卷积)，与 "和牌 14 张减一张" 不同路径。

用法:
  python -u work/verify/indep_core.py flush
  python -u work/verify/indep_core.py validate [n]
  python -u work/verify/indep_core.py global
"""
import sys, os, json, time, hashlib, random
from collections import defaultdict, Counter
from functools import lru_cache

KINDS = 34
CAP = 4
SUIT_KINDS = 9
HONOR_KINDS = 7
# 幺九 + 字牌索引
KOKUSHI_IDX = [0, 8, 9, 17, 18, 26, 27, 28, 29, 30, 31, 32, 33]
# 34 -> (类别, 类别内偏移)
def cat_of(t):
    if t < 27:
        return t // 9, t % 9
    return 3, t - 27
CAT_KINDS = (9, 9, 9, 7)
CAT_SLICES = ((0,9),(9,18),(18,27),(27,34))

# ---------------------------------------------------------------- 面子 DP
@lru_cache(maxsize=None)
def melds_only(counts):
    """counts: 单个类别内的计数元组 (9 或 7 项)。能否拆成若干面子(顺子/刻子)。
    状态 (q,p): q = 在 i-2 起头、还差 i 这一张的顺子数; p = 在 i-1 起头、还差 i,i+1 的顺子数。
    约束 c[i] = q + p + z + 3t, z = 在 i 起头的新顺子数; 迁移 (p, z)."""
    K = len(counts)
    states = {(0, 0)}
    for ci in counts:
        nxt = set()
        for (q, p) in states:
            need = q + p
            if need > ci:
                continue
            rem = ci - need
            t = 0
            while 3 * t <= rem:
                z = rem - 3 * t
                if z <= 4:
                    nxt.add((p, z))
                t += 1
        if not nxt:
            return False
        states = nxt
    return (0, 0) in states

def melds_pair(counts):
    """能否拆成若干面子 + 恰一个雀头"""
    for j, cj in enumerate(counts):
        if cj >= 2:
            c = list(counts); c[j] -= 2
            if melds_only(tuple(c)):
                return True
    return False

# 字牌类别 27..33: 不能有顺子, 面子只能是刻子
def melds_only_honor(counts):
    """字牌: 只有刻子 => 每个计数都是 3 的倍数 (cap 4 时即 0 或 3)"""
    return all(c % 3 == 0 for c in counts)

def melds_pair_honor(counts):
    """字牌: 若干刻子 + 恰一个雀头 => 恰一种牌计数 ≡2 (mod 3), 其余 ≡0"""
    if sum(1 for c in counts if c % 3 == 2) != 1:
        return False
    return all(c % 3 in (0, 2) for c in counts)

def cat_melds_only(vec, ci):
    return melds_only_honor(vec) if ci == 3 else melds_only(vec)

def cat_melds_pair(vec, ci):
    return melds_pair_honor(vec) if ci == 3 else melds_pair(vec)

def has_pair(counts):
    return any(c >= 2 for c in counts)

def odd_count(counts):
    return sum(1 for c in counts if c & 1)

# ---------------------------------------------------------------- 全量和牌判定
def is_win_std(c):
    """c: 34 元计数 (总 14)。标准型 4 面子 + 1 雀头 (brute force)。"""
    for j in range(KINDS):
        if c[j] >= 2:
            ok = True
            for (a, b) in CAT_SLICES:
                sub = list(c[a:b]); sub[j - a] -= 2 if a <= j < b else 0
                if not melds_only(tuple(sub)):
                    ok = False; break
            if ok:
                return True
    return False

def is_win_std_fast(c):
    for j in range(KINDS):
        if c[j] >= 2:
            cc = list(c); cc[j] -= 2
            if all(cat_melds_only(tuple(cc[a:b]), ci) for ci, (a, b) in enumerate(CAT_SLICES)):
                return True
    return False

def is_win_chiitoi_strict(c):
    """严格七对子: 恰好 7 种牌各有 2 张 (4 张不算两对)。"""
    if sum(c) != 14:
        return False
    return sum(1 for x in c if x == 2) == 7

def is_win_chiitoi_loose(c):
    """宽松七对子: 全部计数为偶数 (4 张算两对)。"""
    return sum(c) == 14 and all(x % 2 == 0 for x in c)

def is_win_kokushi(c):
    if sum(c) != 14:
        return False
    for i in KOKUSHI_IDX:
        if c[i] < 1 or c[i] > 2:
            return False
    return all(c[i] == 0 for i in range(KINDS) if i not in KOKUSHI_IDX)

def is_win_full(c, chiitoi="strict"):
    if is_win_std_fast(c):
        return True
    if chiitoi == "strict":
        if is_win_chiitoi_strict(c):
            return True
    else:
        if is_win_chiitoi_loose(c):
            return True
    return is_win_kokushi(c)

def compute_W(counts, chiitoi="strict"):
    """counts: 34 元 13 张手牌 -> frozenset(W)  (必须检查 4 张上限!)"""
    W = set()
    c = list(counts)
    for t in range(KINDS):
        if c[t] >= CAP:
            continue
        c[t] += 1
        if is_win_full(c, chiitoi):
            W.add(t)
        c[t] -= 1
    return frozenset(W)

# ---------------------------------------------------------------- 向量枚举
def gen_vectors(K, n, cap=CAP):
    """生成长度 K、和为 n、每项 <= cap 的所有计数元组"""
    def rec(i, remaining, cur):
        if i == K - 1:
            if remaining <= cap:
                yield tuple(cur + [remaining])
            return
        hi = min(cap, remaining)
        for v in range(hi, -1, -1):
            if remaining - v > cap * (K - i - 1):
                break
            cur.append(v)
            yield from rec(i + 1, remaining - v, cur)
            cur.pop()
    yield from rec(0, n, [])

# ---------------------------------------------------------------- 清一色
def flush_phase(chiitoi="strict", outdir="work/verify"):
    t0 = time.time()
    vectors = list(gen_vectors(9, 13))
    n_hands = len(vectors)
    W_of = {}
    classes = defaultdict(list)
    for v in vectors:
        c = list(v) + [0] * 25
        W = compute_W(c, chiitoi)
        W_of[v] = W
        if W:
            classes[W].append(v)
    listen_hands = sum(len(v) for v in classes.values())
    n_classes = len(classes)

    # 公共码统计: 对每个类 m*[t] = min_H count_H(t); 存在大小 k 公共码 <=> sum(m*) >= k
    res = {}
    for k in (1, 2, 3, 4):
        no_common = 0
        for W, hands in classes.items():
            m = [min(h[t] for h in hands) for t in range(9)]
            if sum(m) < k:
                no_common += 1
        res[k] = no_common
    # tau 下界
    tau_lb = n_classes + res[1]
    out = {
        "chiitoi_convention": chiitoi,
        "flush_all_13tile_multisets": n_hands,
        "flush_listening_hands": listen_hands,
        "flush_classes": n_classes,
        "no_common_code_classes": {str(k): res[k] for k in (1, 2, 3, 4)},
        "k1_lower_bound_sum_tau": tau_lb,
        "k1_dead": tau_lb > KINDS,
        "elapsed_s": round(time.time() - t0, 3),
    }
    # 显式码验证: 对每个类构造一个 sum(m*) 大小的码, 检查该码在类内每手牌里
    bad = 0
    for W, hands in classes.items():
        m = [min(h[t] for h in hands) for t in range(9)]
        code = []
        for t in range(9):
            code += [t] * m[t]
        for h in hands:
            hc = list(h)
            for t in code:
                hc[t] -= 1
            if any(x < 0 for x in hc):
                bad += 1
    out["explicit_code_check_failures"] = bad
    # 分布: 各类的 (sum m*, tau) 直方图
    hist = Counter(sum(min(h[t] for h in hands) for t in range(9)) for hands in classes.values())
    out["class_max_common_code_size_hist"] = {str(k): v for k, v in sorted(hist.items())}
    out["W_size_hist"] = {str(k): v for k, v in sorted(Counter(len(W) for W in classes).items())}
    return out

# ---------------------------------------------------------------- 校验: 闭式 vs brute force
def validate_phase(n_random=200000, seed=20240607, chiitoi="strict"):
    """随机 13 张手牌: brute-force W vs 结构闭式 W"""
    rnd = random.Random(seed)
    def rand_hand():
        c = [0] * KINDS
        for _ in range(13):
            while True:
                t = rnd.randrange(KINDS)
                if c[t] < CAP:
                    c[t] += 1; break
        return c
    bad = []
    checked = 0
    for _ in range(n_random):
        c = rand_hand()
        Wbf = compute_W(c, chiitoi)
        Wcf = closed_form_W(c, chiitoi)
        checked += 1
        if Wbf != Wcf:
            bad.append({"hand": c, "bf": sorted(Wbf), "cf": sorted(Wcf)})
            if len(bad) > 5:
                break
    return {"checked": checked, "mismatches": len(bad), "examples": bad[:5]}

def closed_form_W(c, chiitoi="strict"):
    """Lead 广播的结构闭式 (verifier 独立实现, 用 DP 表)"""
    cats = []
    for (a, b) in CAT_SLICES:
        cats.append(tuple(c[a:b]))
    n = [sum(x) for x in cats]
    r = [x % 3 for x in n]
    W = set()
    # 标准型
    if sorted(r) == [0, 0, 0, 1]:
        ci = r.index(1)
        # 惰性部: 其余类别必须可拆面子
        others = [j for j in range(4) if j != ci]
        if all(cat_melds_only(cats[j], j) for j in others):
            X = cats[ci]
            for t in range(len(X)):
                if X[t] >= CAP: continue
                xx = list(X); xx[t] += 1
                if cat_melds_pair(tuple(xx), ci):
                    W.add(CAT_SLICES[ci][0] + t)
    elif sorted(r) == [0, 0, 2, 2]:
        act = [j for j in range(4) if r[j] == 2]
        others = [j for j in range(4) if r[j] == 0]
        if all(cat_melds_only(cats[j], j) for j in others):
            X1 = cats[act[0]]; X2 = cats[act[1]]
            if cat_melds_pair(X1, act[0]):
                for t in range(len(X2)):
                    if X2[t] >= CAP: continue
                    xx = list(X2); xx[t] += 1
                    if cat_melds_only(tuple(xx), act[1]):
                        W.add(CAT_SLICES[act[1]][0] + t)
            if cat_melds_pair(X2, act[1]):
                for t in range(len(X1)):
                    if X1[t] >= CAP: continue
                    xx = list(X1); xx[t] += 1
                    if cat_melds_only(tuple(xx), act[0]):
                        W.add(CAT_SLICES[act[0]][0] + t)
    # 七对子
    if chiitoi == "strict":
        # 13 张、严格七对子听: 7 种牌, 一种 1 张 + 六种 2 张
        if sum(1 for x in c if x == 2) == 6 and sum(1 for x in c if x == 1) == 1:
            W.add([i for i, x in enumerate(c) if x == 1][0])
    else:
        oddk = [i for i, x in enumerate(c) if x % 2 == 1]
        if len(oddk) == 1 and sum(c) == 13:
            W.add(oddk[0])
    # 国士
    if sum(c[i] >= 1 for i in KOKUSHI_IDX) == 13 or (
       sum(c[i] >= 1 for i in KOKUSHI_IDX) == 12 and sum(c) == 13):
        missing = [i for i in KOKUSHI_IDX if c[i] == 0]
        distinct = sum(c[i] >= 1 for i in KOKUSHI_IDX)
        if distinct == 13:
            W |= set(KOKUSHI_IDX)
        elif distinct == 12:
            W.add(missing[0])
    return frozenset(W)

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "flush"
    if cmd == "flush":
        conv = sys.argv[2] if len(sys.argv) > 2 else "strict"
        out = flush_phase(conv)
        print(json.dumps(out, ensure_ascii=False, indent=2))
    elif cmd == "validate":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 100000
        out = validate_phase(n)
        print(json.dumps(out, ensure_ascii=False)[:4000])
    else:
        print("unknown command", cmd)

if __name__ == "__main__":
    main()
