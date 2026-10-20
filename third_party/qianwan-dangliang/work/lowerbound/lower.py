#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lower.py --- T3 (analyst-lower): 最小可行 k 的下界证书
写作用域: work/lowerbound/

用法:
    python -u work/lowerbound/lower.py            # 生成 certificate.json 并自检
    python -u work/lowerbound/lower.py --verify   # 只重放证书

引理 (LOWERBOUND.md 有完整证明):
  L0  k 可行 <=> 存在码函数 c(H) in M_k(H), W(H1)!=W(H2) => c(H1)!=c(H2)
            <=> 每个听牌类 C 有命中集 S_C (与每个 M_k(H), H in C 相交), 不同类 S_C 两两不交。
  L1  有序码总数 34^k; M_k 的相交性只取决于码的多重集, 故 tau 可用无序多重集码计算。
  L2  子宇宙预算引理: 对牌集 U, sum_{C 含 U 内手牌的类} tau_U(C) <= |U|^k。
  L3  余数定理: 标准型和牌 14 张恰一类 ≡2 (mod 3), 其余 ≡0。
  L4  七对子判据: H 是七对子听牌 <=> H 恰为 6 对 + 1 单 (天凤: 7 种不同对子)。
  L5  清一色 13 张手牌 = 93600 个计数向量 (完全枚举)。

定理 A  k=1 不可行: 清一色子宇宙 U=m, sum tau = 427 > 9 = 9^1  (> 34 = 34^1)。
定理 B  k=2 不可行: sum tau = sum_lb >= 440 > 81 = 9^2        (> 1156 = 34^2)。
附注   k=3 未被清一色子宇宙否证: sum tau <= sum_ub < 729 = 9^3 (构造性上界)。
"""
import itertools, json, os, sys, time
from functools import lru_cache
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
CERT = os.path.join(HERE, "certificate.json")
T0 = time.time()

CAT_LEN  = (9, 9, 9, 7)
CAT_BASE = (0, 9, 18, 27)
TERMINALS = (0, 8, 9, 17, 18, 26, 27, 28, 29, 30, 31, 32, 33)

@lru_cache(maxsize=None)
def melds_only(c):
    """单类别计数向量能否拆成纯面子; 返回面子数或 None。
    穷尽性: 取最小非零位 i; 任何覆盖 i 的面子只能是以 i 起的刻子或 i,i+1,i+2 顺子。"""
    n = len(c); i = 0
    while i < n and c[i] == 0: i += 1
    if i == n: return 0
    best = None
    if c[i] >= 3:
        c2 = list(c); c2[i] -= 3
        r = melds_only(tuple(c2))
        if r is not None: best = r + 1
    # 字牌类别长度 7, 不能组顺子; 只有 9 长度的数牌类别才允许 i,i+1,i+2 顺子
    if n == 9 and i + 2 < n and c[i+1] > 0 and c[i+2] > 0:
        c2 = list(c); c2[i] -= 1; c2[i+1] -= 1; c2[i+2] -= 1
        r = melds_only(tuple(c2))
        if r is not None and (best is None or r + 1 < best): best = r + 1
    return best

def is_std_win(cnt):
    for i in range(34):
        if cnt[i] >= 2:
            c = list(cnt); c[i] -= 2
            tot = 0; ok = True
            for b, n in zip(CAT_BASE, CAT_LEN):
                m = melds_only(tuple(c[b:b+n]))
                if m is None: ok = False; break
                tot += m
            if ok and tot == 4: return True
    return False

def is_chiitoi_win(cnt):
    """7 种不同的对子 (计数 4 不算两对)"""
    npair = 0
    for x in cnt:
        if x == 0: continue
        if x != 2: return False
        npair += 1
    return npair == 7

def is_kokushi_win(cnt):
    s = 0
    for i in range(34):
        if cnt[i] == 0: continue
        if i not in TERMINALS: return False
        s += cnt[i]
    return s == 14 and sum(1 for i in TERMINALS if cnt[i] >= 1) == 13

def waits(cnt):
    out = []
    for t in range(34):
        if cnt[t] >= 4: continue
        c = list(cnt); c[t] += 1
        if is_std_win(c) or is_chiitoi_win(c) or is_kokushi_win(c): out.append(t)
    return tuple(out)

# ---------- 清一色完全枚举 (L5) + 胜牌两路径交叉验证 ----------
def flush_win_paths():
    winA = set()
    for c in itertools.product(range(5), repeat=9):
        if sum(c) == 14 and is_std_win(list(c) + [0]*25): winA.add(c)
    melds = []
    for i in range(9):
        v = [0]*9; v[i] = 3; melds.append(tuple(v))
    for i in range(7):
        v = [0]*9; v[i] = 1; v[i+1] = 1; v[i+2] = 1; melds.append(tuple(v))
    winB = set()
    for combo in itertools.combinations_with_replacement(range(len(melds)), 4):
        v = [0]*9
        for m in combo:
            w = melds[m]
            for i in range(9): v[i] += w[i]
        if any(x > 4 for x in v): continue
        for p in range(9):
            if v[p] + 2 <= 4:
                w = list(v); w[p] += 2; winB.add(tuple(w))
    return winA, winB

def flush_census():
    hands = []
    for c in itertools.product(range(5), repeat=9):
        if sum(c) == 13:
            cnt = [0]*34
            for i, v in enumerate(c):
                if v: cnt[i] = v
            hands.append(tuple(cnt))
    classes = {}
    for h in hands:
        W = waits(h)
        if W: classes.setdefault(W, []).append(h)
    return hands, classes

# ---------- 码与 tau ----------
def code_space(n, k):
    combos = list(itertools.combinations_with_replacement(range(n), k))
    reqs = [tuple(sorted(((t, comb.count(t)) for t in set(comb)))) for comb in combos]
    return combos, reqs

def mask_of(h, reqs):
    m = 0
    for ci, need in enumerate(reqs):
        ok = True
        for t, n in need:
            if h[t] < n: ok = False; break
        if ok: m |= (1 << ci)
    return m

def bits_of(m):
    out = []
    while m:
        b = m & -m; out.append(b.bit_length()-1); m ^= b
    return out

def greedy_cover(masks, ncodes, cover):
    """greedy + 去冗余, 返回覆盖全部手牌的码索引列表 (上界见证)"""
    full = (1 << len(masks)) - 1
    unc = full; chosen = []
    while unc:
        best = -1; bc = None
        for c in range(ncodes):
            v = (cover[c] & unc).bit_count()
            if v > best: best = v; bc = c
        if best == 0: return None
        chosen.append(bc); unc &= ~cover[bc]
    changed = True
    while changed and len(chosen) > 1:
        changed = False
        for i in range(len(chosen)):
            un = full
            for j, c in enumerate(chosen):
                if j != i: un &= ~cover[c]
            if un == 0:
                chosen.pop(i); changed = True; break
    return chosen

class _Cap(Exception):
    pass

def _find_cover(masks, cover, keep, cih, full, t, cap):
    """找大小 <= t 的覆盖, 返回 (cover_list 或 None, 是否穷尽搜索)。"""
    nodes = [0]
    memo = {}
    def rec(unc, left):
        if unc == 0: return []
        if left == 0: return None
        nodes[0] += 1
        if nodes[0] > cap: raise _Cap()
        key = (unc, left)
        if key in memo: return memo[key]
        h = (unc & -unc).bit_length() - 1
        for c in cih[h]:
            r = rec(unc & ~cover[c], left-1)
            if r is not None:
                out = [c] + r; memo[key] = out; return out
        memo[key] = None
        return None
    try:
        return rec(full, t), True
    except _Cap:
        return None, False

def tau_bounds(masks, ncodes, node_cap=300000):
    """返回 (lb, ub, exact, cover_codes)。
       ub: greedy + 去冗余 给出的构造性命中集 (上界见证);
       lb: 已证下界 (1 若有公共码; 否则 >=2, 由 blocker 表证明; 搜索穷尽时可提升).
    注: common 必须在【码】全空间上取交, 不在手牌掩码上取交。"""
    n = len(masks); full = (1 << n) - 1
    all_codes = (1 << ncodes) - 1
    cover = [0]*ncodes
    for i, m in enumerate(masks):
        mm = m
        while mm:
            b = mm & -mm; cover[b.bit_length()-1] |= (1 << i); mm ^= b
    common = all_codes
    for m in masks: common &= m
    if common:
        return 1, 1, True, [bits_of(common)[0]]
    chosen = greedy_cover(masks, ncodes, cover)
    ub = len(chosen)
    present = [c for c in range(ncodes) if cover[c]]
    # t=2: 公共码已排除 => tau >= 2
    for i in range(len(present)):
        ci = cover[present[i]]
        for j in range(i+1, len(present)):
            if (ci | cover[present[j]]) == full:
                return 2, 2, True, [present[i], present[j]]
    if ub <= 2:
        return 2, ub, True, chosen
    keep = [c for c in present if not any(c2 != c and (cover[c] | cover[c2]) == cover[c2] for c2 in present)]
    if not keep: keep = present
    cih = [[c for c in keep if (m >> c) & 1] for m in masks]
    for i in range(n): cih[i].sort(key=lambda c: -cover[c].bit_count())
    lb = 2
    for t in range(3, ub):
        res, exhaustive = _find_cover(masks, cover, keep, cih, full, t, node_cap)
        if res is not None:
            return t, t, True, res
        if not exhaustive:
            break
        lb = t + 1
    return lb, ub, (lb == ub), chosen

def hand_json(h):
    return [[t, h[t]] for t in range(34) if h[t]]

# ---------- 证书 ----------
def build():
    rep = {}
    n_direct = sum(1 for c in itertools.product(range(5), repeat=9) if sum(c) == 13)
    n_ie = comb(21, 8) - 9*comb(16, 8) + 36*comb(11, 8)
    rep["L5_flush_enumeration"] = {"direct": n_direct, "inclusion_exclusion": n_ie, "agree": n_direct == n_ie}
    print("[L5] 单花色 13 张计数向量: 直接穷举=%d 容斥=%d %s" % (n_direct, n_ie, "OK" if n_direct == n_ie else "MISMATCH"), flush=True)
    winA, winB = flush_win_paths()
    rep["crosscheck_win"] = {"pathA_all_14_vectors": len(winA), "pathB_meld_multisets": len(winB), "agree": winA == winB}
    print("[交叉验证] 清一色 14 张标准型胜牌: A=%d B=%d %s" % (len(winA), len(winB), "OK" if winA == winB else "MISMATCH"), flush=True)
    hands, classes = flush_census()
    rep["flush_census"] = {"tenpai_hands_full_W": sum(len(v) for v in classes.values()), "classes": len(classes)}
    print("[普查] 清一色听牌手牌=%d 类=%d (t=%.1fs)" % (rep["flush_census"]["tenpai_hands_full_W"], len(classes), time.time()-T0), flush=True)

    rep["lemmas"] = {
        "L0": "k 可行 <=> 每类有命中集且不同类命中集两两不交 (LOWERBOUND.md 命题 1)",
        "L1": "有序码 34^k; tau 可用无序多重集码计算",
        "L2": "子宇宙预算: sum_{C 含 U 内手牌} tau_U(C) <= |U|^k",
        "L3": "标准型和牌 14 张恰一类 ≡2 (mod 3), 其余 ≡0",
        "L4": "H 是七对子听牌 <=> H = 6 对 + 1 单",
        "L5": "清一色 13 张手牌 = 93600 个计数向量",
    }
    rep["sub_universe"] = {"U": "m1..m9", "size": 9, "codes": {str(k): 9**k for k in (1,2,3,4)}}
    rep["theorems"] = {}
    for k in (1, 2, 3, 4):
        combos, reqs = code_space(9, k)
        recs = []; sum_lb = 0; sum_ub = 0; n_exact = 0
        for W, hs in classes.items():
            masks = [mask_of(h, reqs) for h in hs]
            lb, ub, exact, cov = tau_bounds(masks, len(combos))
            sum_lb += lb; sum_ub += ub; n_exact += 1 if exact else 0
            r = {"W": list(W), "class_size": len(hs), "tau_lb": lb, "tau_ub": ub, "exact": exact}
            if ub > 1 and cov:
                r["cover_codes"] = cov   # 构造性上界见证: 这些码命中类内每一手牌
            if lb >= 2:
                # 下界见证: 对每个码给出"不含它"的一手牌 (交集为空)
                blocked = []
                union = 0
                for m in masks: union |= m
                for c in bits_of(union):
                    for i, m in enumerate(masks):
                        if not ((m >> c) & 1):
                            blocked.append([c, i]); break
                r["blockers"] = blocked
            recs.append(r)
        b9 = 9**k; b34 = 34**k
        rep["theorems"]["k=%d" % k] = {
            "class_count": len(classes), "sum_tau_lb": sum_lb, "sum_tau_ub": sum_ub,
            "n_exact_classes": n_exact, "budget_sub_universe": b9, "budget_global": b34,
            "disproved_by_sub_universe": sum_lb > b9, "disproved_by_global_count": len(classes) > b34,
            "flush_sub_universe_allows": sum_ub <= b9, "classes": recs}
        print("[k=%d] Sigma tau in [%d, %d] (exact classes %d/%d) | 9^%d=%d -> %s | #classes=%d vs 34^%d=%d -> %s" % (
            k, sum_lb, sum_ub, n_exact, len(classes), k, b9,
            ("否证" if sum_lb > b9 else ("可行(上界内)" if sum_ub <= b9 else "未定")),
            len(classes), k, b34, "否证" if len(classes) > b34 else "-"), flush=True)
    with open(CERT, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False)
    print("[写入] %s (%d bytes)" % (CERT, os.path.getsize(CERT)), flush=True)
    return rep

def verify(path=CERT):
    with open(path, encoding="utf-8") as f:
        cert = json.load(f)
    ok = True
    def chk(cond, msg):
        nonlocal ok
        if not cond:
            ok = False; print("  [FAIL] " + msg)
    hands, classes = flush_census()
    chk(sum(len(v) for v in classes.values()) == cert["flush_census"]["tenpai_hands_full_W"], "听牌手牌数")
    chk(len(classes) == cert["flush_census"]["classes"], "类数")
    chk({tuple(r["W"]) for r in cert["theorems"]["k=1"]["classes"]} == set(classes.keys()), "类集合一致")
    for k in (1, 2, 3, 4):
        combos, reqs = code_space(9, k)
        rec_k = cert["theorems"]["k=%d" % k]
        sl = su = 0
        for r in rec_k["classes"]:
            W = tuple(r["W"]); hs = classes[W]
            masks = [mask_of(h, reqs) for h in hs]
            full = (1 << len(hs)) - 1
            sl += r["tau_lb"]; su += r["tau_ub"]
            # 上界见证: cover_codes 必须命中类内每一手牌
            if "cover_codes" in r:
                cov = 0
                for c in r["cover_codes"]:
                    for i, m in enumerate(masks):
                        if (m >> c) & 1: cov |= (1 << i)
                chk(cov == full, "k=%d W=%s 上界见证未覆盖全部手牌" % (k, W))
            # 下界见证: blockers 表必须证明交集为空
            if r["tau_lb"] >= 2:
                b = r.get("blockers")
                chk(b is not None, "k=%d W=%s 缺下界见证" % (k, W))
                if b is not None:
                    for c, i in b:
                        chk(not ((masks[i] >> c) & 1), "k=%d W=%s 阻塞表[%d,%d]不成立" % (k, W, c, i))
                    chk(len(b) == len({c for c, _ in b}), "k=%d W=%s 阻塞表有重复码" % (k, W))
        chk(sl == rec_k["sum_tau_lb"], "k=%d sum_lb 一致" % k)
        chk(su == rec_k["sum_tau_ub"], "k=%d sum_ub 一致" % k)
        chk((sl > 9**k) == rec_k["disproved_by_sub_universe"], "k=%d 否证标志" % k)
        print("  k=%d: Sigma tau in [%d, %d]; 9^%d=%d 34^%d=%d" % (k, sl, su, k, 9**k, k, 34**k), flush=True)
    print("CERTIFICATE VERIFIED" if ok else "CERTIFICATE FAILED", flush=True)
    return ok

if __name__ == "__main__":
    if "--verify" in sys.argv:
        verify()
    else:
        build()
        print("--- 重放自检 ---", flush=True)
        verify()
