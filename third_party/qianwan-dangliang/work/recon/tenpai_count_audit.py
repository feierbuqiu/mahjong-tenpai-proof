# -*- coding: utf-8 -*-
"""tenpai_count_audit.py -- A1 听牌手牌总数对账（从零穷举重算）。

裁决对象
--------
  团队（work/data/STATS.md, census_two.py）：标准型听牌手牌 54,747,045；总数 92,371,838
  审计（work/audit/t15_counts.py）    ：标准型听牌手牌 54,793,476；总数 92,418,269
  差 46,431，全在"标准型"分量；双方对 七对子 37,657,312 / 重叠 32,676 / 国士 157 一致。

三条从零实现的计数路径
----------------------
  路径 A（结构分解，distinct 口径）：标准型听牌手 H 唯一分解 H = A ⊎ F，
        A = H 在"主动类别"内的部分（|A|≡1 mod 3 单类别；或两个类别各 ≡2 mod 3），
        F = 其余类别内张数为 3 的倍数的**面子并**，按 **不同牌张向量** 计数。
  路径 A'（结构分解，naive 口径）：同 A，但 F 按**面子多重集**计数（= 审计 t15 的写法，
        不去重）：用于复现审计数字并量化多算量。
  路径 B（和牌侧，无结构假设）：枚举全部 14 张标准和牌 W（4 面子+1 对），
        13 张手牌 H = W - t，用"最小听牌张唯一计数"规则去重，直接得到标准型听牌手牌数。
  路径 C（暴力）：受限宇宙 S 内逐手枚举 13 张牌，直接判定听牌，用于校验 A/A'/B。

用法
----
  python -u work/recon/tenpai_count_audit.py structure   # 全局结构口径（A vs A'）
  python -u work/recon/tenpai_count_audit.py witness     # 多算见证（审计口径重复计数的具体手牌）
  python -u work/recon/tenpai_count_audit.py winning     # 和牌侧全空间计数（B）
  python -u work/recon/tenpai_count_audit.py validate    # 子宇宙暴力校验（A/A' 对 C）
  python -u work/recon/tenpai_count_audit.py all
"""
import sys, os, json, math, time, itertools
from functools import lru_cache
from collections import Counter

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "out")
os.makedirs(OUTDIR, exist_ok=True)
RESULT_PATH = os.path.join(OUTDIR, "tenpai_count_audit.json")

BASE = [0, 9, 18, 27]
LEN = [9, 9, 9, 7]
CATNAME = ["m", "p", "s", "z"]
TILE_NAMES = (["%dm" % i for i in range(1, 10)] + ["%dp" % i for i in range(1, 10)]
              + ["%ds" % i for i in range(1, 10)] + ["E", "S", "W", "N", "Haku", "Hatsu", "Chun"])
CAT_TILES = [[BASE[c] + i for i in range(LEN[c])] for c in range(4)]
ALL_TILES = list(range(34))
TT = [1 << i for i in range(34)]


def cat_of(t):
    return 0 if t < 9 else 1 if t < 18 else 2 if t < 27 else 3


def nm(t):
    return TILE_NAMES[t]


def hand_str(v):
    """34 计数 -> 可读牌名（按花色分组）"""
    out = []
    for c in range(4):
        s = "".join(TILE_NAMES[t].rstrip("mpsz") for t in CAT_TILES[c] for _ in range(v[t]))
        if s:
            out.append(s + CATNAME[c])
    return " ".join(out)


# ---------------------------------------------------------------- 0. 从零的判定内核
@lru_cache(maxsize=400000)
def is_melds(v):
    """v: 34 元计数元组；能否拆成若干面子（刻子/顺子；字牌不能顺）。"""
    i = -1
    for k in range(34):
        if v[k]:
            i = k
            break
    if i < 0:
        return True
    if v[i] >= 3:
        w = list(v)
        w[i] -= 3
        if is_melds(tuple(w)):
            return True
    if i < 27 and (i % 9) <= 6 and v[i + 1] and v[i + 2]:
        w = list(v)
        w[i] -= 1
        w[i + 1] -= 1
        w[i + 2] -= 1
        if is_melds(tuple(w)):
            return True
    return False


@lru_cache(maxsize=400000)
def is_win(v):
    """v: 34 元计数元组（总张数 ≡ 2 mod 3）；是否是 若干面子 + 恰好 1 对。"""
    stack = [(v, False)]
    while stack:
        w, used = stack.pop()
        i = -1
        for k in range(34):
            if w[k]:
                i = k
                break
        if i < 0:
            if used:
                return True
            continue
        if w[i] >= 3:
            u = list(w)
            u[i] -= 3
            stack.append((tuple(u), used))
        if i < 27 and (i % 9) <= 6 and w[i + 1] and w[i + 2]:
            u = list(w)
            u[i] -= 1
            u[i + 1] -= 1
            u[i + 2] -= 1
            stack.append((tuple(u), used))
        if not used and w[i] >= 2:
            u = list(w)
            u[i] -= 2
            stack.append((tuple(u), True))
    return False


def add(v, t, k=1):
    w = list(v)
    w[t] += k
    return tuple(w)


def wp_nonempty(v):
    """Wp(v) = {t : v+t 是 面子+对} 是否非空（|v| ≡ 1 mod 3）"""
    for t in range(34):
        if v[t] < 4 and is_win(add(v, t)):
            return True
    return False


def v_nonempty(v):
    """V(v) = {t : v+t 全是面子} 是否非空（|v| ≡ 2 mod 3）"""
    for t in range(34):
        if v[t] < 4 and is_melds(add(v, t)):
            return True
    return False


def waits_std(v):
    """标准型听牌张集合（13 张手牌）"""
    if sum(v) != 13:
        return set()
    return {t for t in range(34) if v[t] < 4 and is_win(add(v, t))}


def waits_all(v):
    """题目口径的全部听牌张（标准 ∪ 七对子）；国士另算"""
    w = waits_std(v)
    if sum(v) == 13:
        nz = [x for x in v if x]
        if len(nz) == 7 and sum(1 for x in nz if x == 1) == 1 and sum(1 for x in nz if x == 2) == 6:
            w.add(next(t for t in range(34) if v[t] == 1))
    return w


def chiitoi_tenpai(v):
    nz = [x for x in v if x]
    return sum(v) == 13 and len(nz) == 7 and sum(1 for x in nz if x == 1) == 1 \
        and sum(1 for x in nz if x == 2) == 6


def one2(v):
    nz = [x for x in v if x]
    return sum(1 for x in nz if x == 1) == 1 and all(x == 2 for x in nz if x != 1)


def all2(v):
    nz = [x for x in v if x]
    return len(nz) > 0 and all(x == 2 for x in nz)


# ---------------------------------------------------------------- 1. 枚举工具
def enum_multisets(s, kinds, cap=4):
    """size s 的所有多重集（kinds 内每张 ≤cap），返回 34 元计数元组列表"""
    K = len(kinds)
    res = []
    if K == 0:
        return [tuple([0] * 34)] if s == 0 else []
    cur = [0] * K

    def rec(pos, left):
        if pos == K - 1:
            if left <= cap:
                cur[pos] = left
                v = [0] * 34
                for j in range(K):
                    v[kinds[j]] = cur[j]
                res.append(tuple(v))
            return
        for x in range(0, min(cap, left) + 1):
            cur[pos] = x
            rec(pos + 1, left - x)

    rec(0, s)
    return res


MELD_VECS = {}
for _c in range(4):
    _lst = []
    for _t in CAT_TILES[_c]:
        _v = [0] * 34
        _v[_t] = 3
        _lst.append(tuple(_v))
    if _c < 3:
        for _i in range(LEN[_c] - 2):
            _v = [0] * 34
            for _k in range(3):
                _v[BASE[_c] + _i + _k] = 1
            _lst.append(tuple(_v))
    MELD_VECS[_c] = _lst


def meld_multisets(c, s, allowed=None):
    """类别 c 内、总张数 s 的**面子多重集**（按下标非降枚举，含重复牌张向量）。
    返回 list（含重复）—— 审计 t15_counts.py::meld_multisets 的口径。"""
    if s == 0:
        return [tuple([0] * 34)]
    ms = [v for v in MELD_VECS[c]
          if allowed is None or all(v[t] == 0 or t in allowed for t in range(34))]
    out = []
    acc = [0] * 34

    def rec(i, left):
        if left == 0:
            out.append(tuple(acc))
            return
        for j in range(i, len(ms)):
            u = ms[j]
            ok = True
            for t in range(34):
                if u[t] and acc[t] + u[t] > 4:
                    ok = False
                    break
            if not ok:
                continue
            for t in range(34):
                acc[t] += u[t]
            rec(j, left - 3)
            for t in range(34):
                acc[t] -= u[t]

    rec(0, s)
    return out


_MMC = {}


def mm(c, s, allowed_key=None):
    k = (c, s, allowed_key)
    if k not in _MMC:
        allowed = None if allowed_key is None else set(allowed_key)
        lst = meld_multisets(c, s, allowed)
        _MMC[k] = (len(lst), set(lst))
    return _MMC[k]


def filler_counts(cats, m, allowed_key=None, even_only=False):
    """返回 (naive_count, distinct_set)：inert 类别 cats 内总张数 m 的补牌族 F。
    naive_count = 面子多重集口径（审计 t15）；distinct_set = 不同牌张向量（正确口径）。
    even_only=True 只保留'每张计数 ∈ {0,2}'的 F（七对子重叠用）。"""
    per = {}
    for c in cats:
        for s in range(0, m + 1, 3):
            n, st = mm(c, s, allowed_key)
            if even_only:
                st = {v for v in st if all(x in (0, 2) for x in v)}
                n = len(st)
            per[(c, s)] = (n, st)
    naive = 0
    keys = set()

    def rec_n(i, rem, prod):
        nonlocal naive
        if i == len(cats):
            if rem == 0:
                naive += prod
            return
        c = cats[i]
        for s in range(0, rem + 1, 3):
            n, _ = per[(c, s)]
            if n:
                rec_n(i + 1, rem - s, prod * n)

    def rec_d(i, rem, acc):
        if i == len(cats):
            if rem == 0:
                keys.add(tuple(acc))
            return
        c = cats[i]
        for s in range(0, rem + 1, 3):
            _, st = per[(c, s)]
            for v in st:
                rec_d(i + 1, rem - s, [a + b for a, b in zip(acc, v)])

    rec_n(0, m, 1)
    rec_d(0, m, [0] * 34)
    return naive, keys


# ---------------------------------------------------------------- 2. 路径 A/A'：结构分解
def a_type1(c, allowed_key=None):
    """按 s 统计主动部 A（单类别，|A|≡1 mod 3）：(n_wp, n_wp_and_one2)"""
    tiles = CAT_TILES[c] if allowed_key is None else [t for t in CAT_TILES[c] if t in allowed_key]
    out = {}
    for s in (1, 4, 7, 10, 13):
        n_wp = 0
        n_wp_o2 = 0
        for A in enum_multisets(s, tiles):
            if wp_nonempty(A):
                n_wp += 1
                if one2(A):
                    n_wp_o2 += 1
        out[s] = (n_wp, n_wp_o2)
    return out


def a_type2(c, allowed_key=None):
    """按 s 统计主动部 A（|A|≡2 mod 3）：Counter[(pd, Vne, all2, one2)]"""
    tiles = CAT_TILES[c] if allowed_key is None else [t for t in CAT_TILES[c] if t in allowed_key]
    out = {}
    for s in (2, 5, 8, 11):
        cnt = Counter()
        for A in enum_multisets(s, tiles):
            pd = is_win(A)
            vne = v_nonempty(A)
            cnt[(bool(pd), bool(vne), all2(A), one2(A))] += 1
        out[s] = cnt
    return out


def structural(allowed_key=None, verbose=True, sub=None):
    """路径 A / A'。返回 dict。sub=(cats, allowed_set) 用于子宇宙（不按完整 4 类别分组）。"""
    t0 = time.time()
    if allowed_key is None:
        cats_used = [0, 1, 2, 3]
    elif sub is not None:
        cats_used = sub
    else:
        cats_used = [0, 1, 2, 3]
    A1 = {c: a_type1(c, allowed_key) for c in cats_used}
    A2 = {c: a_type2(c, allowed_key) for c in cats_used}
    std_d = std_n = ov_d = ov_n = 0
    detail = []
    for c in cats_used:
        inert = tuple(x for x in cats_used if x != c)
        for s, (n_wp, n_wp_o2) in A1[c].items():
            m = 13 - s
            if m < 0 or m % 3:
                continue
            if n_wp == 0:
                continue
            nf, keys = filler_counts(inert, m, allowed_key)
            if not keys and nf == 0:
                continue
            nfe, keyse = filler_counts(inert, m, allowed_key, even_only=True)
            std_d += n_wp * len(keys)
            std_n += n_wp * nf
            ov_d += n_wp_o2 * len(keyse)
            ov_n += n_wp_o2 * nfe
            detail.append(("I", CATNAME[c], s, n_wp, len(keys), nf, n_wp * len(keys), n_wp * nf,
                           n_wp * (nf - len(keys))))
    for i in range(len(cats_used)):
        for j in range(i + 1, len(cats_used)):
            c1, c2 = cats_used[i], cats_used[j]
            inert = tuple(x for x in cats_used if x not in (c1, c2))
            for s1 in (2, 5, 8, 11):
                B1 = A2[c1].get(s1)
                if not B1:
                    continue
                n1 = sum(B1.values())
                p1 = sum(v for (pd, vn, a2, o2), v in B1.items() if pd)
                q1 = sum(v for (pd, vn, a2, o2), v in B1.items() if vn)
                r1 = sum(v for (pd, vn, a2, o2), v in B1.items() if pd and vn)
                for s2 in (2, 5, 8, 11):
                    B2 = A2[c2].get(s2)
                    if not B2:
                        continue
                    if s1 + s2 not in (4, 7, 10, 13):
                        continue
                    n2 = sum(B2.values())
                    p2 = sum(v for (pd, vn, a2, o2), v in B2.items() if pd)
                    q2 = sum(v for (pd, vn, a2, o2), v in B2.items() if vn)
                    r2 = sum(v for (pd, vn, a2, o2), v in B2.items() if pd and vn)
                    npair = p1 * q2 + p2 * q1 - r1 * r2
                    if npair <= 0:
                        continue
                    m = 13 - s1 - s2
                    nf, keys = filler_counts(inert, m, allowed_key)
                    nfe, keyse = filler_counts(inert, m, allowed_key, even_only=True)
                    ovpairs = 0
                    for (pd1, v1, a1, o1), t1 in B1.items():
                        for (pd2, v2, a2, o2f), t2 in B2.items():
                            if not ((pd1 and v2) or (pd2 and v1)):
                                continue
                            if (o1 and a2 and not o2f) or (o2f and a1 and not o1):
                                ovpairs += t1 * t2
                    std_d += npair * len(keys)
                    std_n += npair * nf
                    ov_d += ovpairs * len(keyse)
                    ov_n += ovpairs * nfe
                    detail.append(("II", CATNAME[c1] + CATNAME[c2], "%d+%d" % (s1, s2),
                                   npair, len(keys), nf, npair * len(keys), npair * nf,
                                   npair * (nf - len(keys))))
    chi = 28 * math.comb(34, 6)
    kok = 157
    res = {
        "standard_distinct": std_d,
        "standard_naive": std_n,
        "overlap_distinct": ov_d,
        "overlap_naive": ov_n,
        "excess_standard": std_n - std_d,
        "excess_overlap": ov_n - ov_d,
        "chiitoi": chi,
        "kokushi": kok,
        "total_distinct": std_d + chi - ov_d + kok,
        "total_naive": std_n + chi - ov_n + kok,
        "sec": round(time.time() - t0, 1),
        "detail": detail,
    }
    if verbose:
        for d in detail:
            print("   ", d)
    return res


# ---------------------------------------------------------------- 3. 路径 C：子宇宙暴力
def std_tenpai_bool(v):
    """13 张手牌是否有标准型听牌（短路）"""
    for t in range(34):
        if v[t] < 4 and is_win(add(v, t)):
            return True
    return False


def _brute_worker(args):
    """并行暴力：固定某张牌的张数，枚举其余"""
    S, ft, fc = args
    rest = [t for t in S if t != ft]
    n_any = n_std = n_chi = n_ov = 0
    for v in enum_multisets(13 - fc, rest, cap=4):
        w = list(v)
        w[ft] = fc
        w = tuple(w)
        st = std_tenpai_bool(w)
        ch = chiitoi_tenpai(w)
        if st or ch:
            n_any += 1
        if st:
            n_std += 1
        if ch:
            n_chi += 1
        if st and ch:
            n_ov += 1
    return (n_any, n_std, n_chi, n_ov, fc)


def brute_parallel(S, nproc=4):
    S = sorted(S)
    ft = S[0]
    args = [(tuple(S), ft, fc) for fc in range(5)]
    import multiprocessing as mp
    with mp.Pool(min(nproc, len(args))) as pool:
        res = pool.map(_brute_worker, args)
    n_any = sum(r[0] for r in res)
    n_std = sum(r[1] for r in res)
    n_chi = sum(r[2] for r in res)
    n_ov = sum(r[3] for r in res)
    return n_any, n_std, n_chi, n_ov


def brute(S):
    """受限宇宙 S：逐手 13 张枚举，直接判定。返回 (listening_any_std_or_chi, standard, chiitoi, overlap)"""
    S = sorted(S)
    n_any = n_std = n_chi = n_ov = 0
    for v in enum_multisets(13, S, cap=4):
        st = std_tenpai_bool(v)
        ch = chiitoi_tenpai(v)
        if st or ch:
            n_any += 1
        if st:
            n_std += 1
        if ch:
            n_chi += 1
        if st and ch:
            n_ov += 1
    return n_any, n_std, n_chi, n_ov


def structural_S(S, dedup=True):
    """子宇宙 S 内的结构计数（路径 A 为 distinct，A' 为 naive）。"""
    allowed = set(S)
    r = structural(allowed_key=tuple(sorted(S)), sub=[c for c in range(4) if any(cat_of(t) == c for t in S)],
                   verbose=False)
    return (r["standard_distinct"], r["standard_naive"], r["overlap_distinct"], r["overlap_naive"])


def cmd_validate():
    big = "big" in sys.argv
    TESTS = [
        tuple(range(0, 3)) + tuple(range(9, 12)),
        tuple(range(0, 5)) + (9,),
        (0, 8, 9, 17, 18, 26, 27, 33),
        tuple(range(0, 4)) + tuple(range(9, 13)),
        (1, 2, 3, 27),                 # 含刻子/顺子歧义的最小宇宙
        (1, 2, 3, 9, 10, 11),          # 两门内多重歧义
        tuple(range(0, 9)),            # 清一色整门
    ]
    if big:
        TESTS.append(tuple(range(0, 6)) + tuple(range(9, 15)))   # 12 张牌宇宙（审计用过的）
    rows = []
    for S in TESTS:
        t0 = time.time()
        b = brute_parallel(S, 4) if big else brute(S)
        sd, sn, od, on = structural_S(S)
        row = {"S": [nm(t) for t in S], "brute_any": b[0], "brute_standard": b[1],
               "brute_chiitoi": b[2], "brute_overlap": b[3],
               "struct_standard_distinct": sd, "struct_standard_naive": sn,
               "struct_overlap_distinct": od, "struct_overlap_naive": on,
               "distinct_matches_brute": sd == b[1], "naive_matches_brute": sn == b[1],
               "sec": round(time.time() - t0, 1)}
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
    j = load_result()
    j["validate_small"] = rows
    save_result(j)


# ---------------------------------------------------------------- 4. 路径 B：和牌侧（无结构假设）
def cmd_winning():
    import numpy as np
    t0 = time.time()
    meld_arr = np.array([list(v) for c in range(4) for v in MELD_VECS[c]], dtype=np.uint8)
    NM = meld_arr.shape[0]
    combos = np.array(list(itertools.combinations_with_replacement(range(NM), 4)), dtype=np.int64)
    cnt = meld_arr[combos].sum(axis=1).astype(np.int64)
    valid = (cnt <= 4).all(axis=1)
    cnt = cnt[valid]
    print("   面子 4-多重集: %d（合法 %d）" % (combos.shape[0], cnt.shape[0]), flush=True)

    def pack(rows):
        lo = np.zeros(rows.shape[0], dtype=np.uint64)
        hi = np.zeros(rows.shape[0], dtype=np.uint64)
        c = rows.astype(np.uint64)
        for i in range(21):
            lo |= c[:, i] << np.uint64(3 * i)
        for i in range(21, 34):
            hi |= c[:, i] << np.uint64(3 * (i - 21))
        return lo, hi

    lo0, hi0 = pack(cnt)
    los, his = [], []
    for p in range(34):
        m = cnt[:, p] <= 2
        if not m.any():
            continue
        l = lo0[m]
        h = hi0[m]
        if p < 21:
            l = l + (np.uint64(2) << np.uint64(3 * p))
        else:
            h = h + (np.uint64(2) << np.uint64(3 * (p - 21)))
        los.append(l)
        his.append(h)
    lo14 = np.concatenate(los)
    hi14 = np.concatenate(his)
    keys = np.empty(lo14.size, dtype=[("lo", "<u8"), ("hi", "<u8")])
    keys["lo"] = lo14
    keys["hi"] = hi14
    kv = keys.view("V16").ravel()
    uk = np.unique(kv)
    w = np.empty(uk.size, dtype=[("lo", "<u8"), ("hi", "<u8")])
    w.view("V16").ravel()[:] = uk
    wlo = np.ascontiguousarray(w["lo"])
    whi = np.ascontiguousarray(w["hi"])
    print("   14 张标准和牌（不同牌张向量）: %d   [%.0fs]" % (uk.size, time.time() - t0), flush=True)

    def field(lo, hi, t):
        return ((lo >> np.uint64(3 * t)) & np.uint64(7)) if t < 21 else ((hi >> np.uint64(3 * (t - 21))) & np.uint64(7))

    total = 0
    CH = 2_000_000
    for t in range(34):
        c = field(wlo, whi, t)
        sel = np.nonzero(c >= 1)[0]
        if sel.size == 0:
            continue
        hit_t = 0
        for a in range(0, sel.size, CH):
            sl = sel[a:a + CH]
            l = wlo[sl] - (np.uint64(1) << np.uint64(3 * t) if t < 21 else np.uint64(0))
            h = whi[sl] - (np.uint64(1) << np.uint64(3 * (t - 21)) if t >= 21 else np.uint64(0))
            ok = np.ones(l.size, dtype=bool)
            for tp in range(t):
                if not ok.any():
                    break
                idx = np.nonzero(ok)[0]
                ct = field(l[idx], h[idx], tp)
                can = ct < 4
                if not can.any():
                    continue
                idx = idx[can]
                l2 = l[idx]
                h2 = h[idx]
                if tp < 21:
                    l2 = l2 + (np.uint64(1) << np.uint64(3 * tp))
                else:
                    h2 = h2 + (np.uint64(1) << np.uint64(3 * (tp - 21)))
                k2 = np.empty(l2.size, dtype=[("lo", "<u8"), ("hi", "<u8")])
                k2["lo"] = l2
                k2["hi"] = h2
                v2 = k2.view("V16").ravel()
                pos = np.searchsorted(uk, v2)
                np.clip(pos, 0, uk.size - 1, out=pos)
                same = (wlo[pos] == l2) & (whi[pos] == h2)
                ok[idx[same]] = False
            hit_t += int(ok.sum())
        total += hit_t
        print("   t=%2d(%s) 贡献 %d  [%.0fs]" % (t, nm(t), hit_t, time.time() - t0), flush=True)
    print("路径 B：标准型听牌手牌 =", total, flush=True)
    j = load_result()
    j["winning_side_standard"] = total
    j["winning_side_sec"] = round(time.time() - t0, 1)
    save_result(j)
    return total


# ---------------------------------------------------------------- 5. 见证：审计口径多算的具体手牌
def meld_multi_lists(c, s, allowed=None):
    """类别 c 内总张数 s 的面子多重集（元素为面子 (count_vec, [tile])），含重复分解"""
    if s == 0:
        return [[]]
    ms = []
    for v in MELD_VECS[c]:
        if allowed is not None and any(v[t] and t not in allowed for t in range(34)):
            continue
        tiles = []
        for t in range(34):
            tiles += [t] * v[t]
        ms.append((v, tiles))
    out = []
    acc = [0] * 34
    cur = []

    def rec(i, left):
        if left == 0:
            out.append(list(cur))
            return
        for j in range(i, len(ms)):
            v, tiles = ms[j]
            if any(v[t] and acc[t] + v[t] > 4 for t in range(34)):
                continue
            for t in range(34):
                acc[t] += v[t]
            cur.append((v, tiles))
            rec(j, left - 3)
            cur.pop()
            for t in range(34):
                acc[t] -= v[t]

    rec(0, s)
    return out


def filler_meld_lists(cats, m):
    """inert 类别内总张数 m 的补牌族：[(牌张向量, [面子多重集])]；同一向量多次出现 = 多分解"""
    res = []

    def rec(i, rem, acc, cur):
        if i == len(cats):
            if rem == 0:
                res.append((tuple(acc), list(cur)))
            return
        c = cats[i]
        for s in range(0, rem + 1, 3):
            for ml in meld_multi_lists(c, s):
                na = list(acc)
                for v, _tl in ml:
                    for t in range(34):
                        na[t] += v[t]
                rec(i + 1, rem - s, na, cur + [ml])

    rec(0, m, [0] * 34, [])
    return res


def decompose(v):
    """唯一结构分解 H = A ⊎ F：返回 (kind, cats, A列表, Wstd)"""
    sizes = [sum(v[t] for t in CAT_TILES[c]) for c in range(4)]
    one = [c for c in range(4) if sizes[c] % 3 == 1]
    two = [c for c in range(4) if sizes[c] % 3 == 2]
    if len(one) == 1 and all(sizes[c] % 3 == 0 for c in range(4) if c != one[0]):
        c = one[0]
        A = tuple(v[t] if cat_of(t) == c else 0 for t in range(34))
        F = tuple(v[t] - A[t] for t in range(34))
        W = {t for t in range(34) if A[t] < 4 and is_win(add(A, t))} if is_melds(F) else set()
        return "I", (c,), (A,), W
    if len(two) == 2 and all(sizes[c] % 3 == 0 for c in range(4) if c not in two):
        A1 = tuple(v[t] if cat_of(t) == two[0] else 0 for t in range(34))
        A2 = tuple(v[t] if cat_of(t) == two[1] else 0 for t in range(34))
        V1 = {t for t in range(34) if A1[t] < 4 and is_melds(add(A1, t))}
        V2 = {t for t in range(34) if A2[t] < 4 and is_melds(add(A2, t))}
        F = tuple(v[t] - A1[t] - A2[t] for t in range(34))
        W = ((V2 if is_win(A1) else set()) | (V1 if is_win(A2) else set())) if is_melds(F) else set()
        return "II", tuple(two), (A1, A2), W
    return None, (), (), set()


def from_str(spec):
    """解析 '1p 1p 3p E 2z' 形式（z 可用 1z..7z 或 E/S/W/N/白/發/中）"""
    alias = {}
    for i in range(1, 10):
        alias["%dm" % i] = i - 1
        alias["%dp" % i] = 8 + i
        alias["%ds" % i] = 17 + i
    for i, name in enumerate(["E", "S", "W", "N", "Haku", "Hatsu", "Chun"]):
        alias[name] = 27 + i
        alias["%dz" % (i + 1)] = 27 + i
    alias["\u767d"] = 31
    alias["\u767a"] = 32
    alias["\u4e2d"] = 33
    v = [0] * 34
    for tok in spec.split():
        v[alias[tok]] += 1
    return tuple(v)


def cmd_witness():
    inert = (0, 1, 2)
    allF = filler_meld_lists(inert, 12)
    mult = Counter(vec for vec, _ in allF)
    dups = sorted(((v, k) for v, k in mult.items() if k > 1), key=lambda x: -x[1])
    print("F(inert=m,p,s; m=12)：面子多重集分解数=%d  不同牌张向量=%d  重复向量=%d  该池多算量=%d"
          % (len(allF), len(mult), len(dups), len(allF) - len(mult)), flush=True)
    v, k = dups[0]
    H = add(v, 27)
    print("见证 F = %s（重数 %d）" % (hand_str(v), k), flush=True)
    print("见证 H = A{E} \u229e F = %s（%d 张）" % (hand_str(H), sum(H)), flush=True)
    print("  H 的标准听牌张 = %s" % sorted(nm(t) for t in waits_std(H)), flush=True)
    print("  审计口径（面子多重集）把 H 计 %d 次；正确口径（去重牌张向量）计 1 次" % k, flush=True)
    decs = [c for vec, c in allF if vec == v]
    for idx, d in enumerate(decs, 1):
        flat = [m for ml in d for m in ml]
        print("  分解 %d: %s" % (idx, "  +  ".join("".join(nm(t) for t in tiles) for _v, tiles in flat)), flush=True)

    named = from_str("1p 1p 1p 1p 3p 4m 5m 6m 7m 8m 9m 2z 2z")
    kind, cats, parts, W = decompose(named)
    print("点名手牌 H2 = %s（%d 张）" % (hand_str(named), sum(named)), flush=True)
    print("  标准听牌张（从零算） = %s" % sorted(nm(t) for t in waits_std(named)), flush=True)
    print("  唯一结构分解 = Type %s, 主动类别=%s, Wstd=%s" %
          (kind, [CATNAME[c] for c in cats], sorted(nm(t) for t in W)), flush=True)
    print("  分解所得 Wstd 与 waits_std 一致：%s" % (W == waits_std(named)), flush=True)
    print("  说明：H2 加 2p = 1p1p1p + 1p2p3p + 456m + 789m + 22z（4 面子+1 对）"
          "，即 4 张同牌 1p 拆成刻子 111p 与顺子 123p 的一部分", flush=True)

    j = load_result()
    j["witness"] = {"pool_melds": len(allF), "pool_vectors": len(mult), "pool_excess": len(allF) - len(mult),
                    "F": hand_str(v), "F_multiplicity": k, "H": hand_str(H),
                    "H_waits": sorted(nm(t) for t in waits_std(H)),
                    "F_decompositions": ["  +  ".join("".join(nm(t) for t in tiles)
                                                     for _v, tiles in [m for ml in d for m in ml])
                                         for d in decs[:5]],
                    "named_hand": hand_str(named), "named_kind": kind,
                    "named_waits": sorted(nm(t) for t in waits_std(named)),
                    "named_decomp_matches": W == waits_std(named)}
    save_result(j)

# ---------------------------------------------------------------- 6. 结果累积
def load_result():
    if os.path.exists(RESULT_PATH):
        try:
            with open(RESULT_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_result(j):
    with open(RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump(j, f, ensure_ascii=False, indent=1)


def cmd_structure():
    t0 = time.time()
    print("== 路径 A/A'：结构分解口径（全球 34 张牌） ==", flush=True)
    r = structural()
    print(json.dumps(r, ensure_ascii=False, indent=1), flush=True)
    print("团队标准型 = 54,747,045 ; 审计标准型 = 54,793,476 ; 团队总数 = 92,371,838 ; 审计总数 = 92,418,269", flush=True)
    print("distinct 对团队标准型：%s" % (r["standard_distinct"] == 54747045), flush=True)
    print("naive    对审计标准型：%s" % (r["standard_naive"] == 54793476), flush=True)
    print("distinct 总数对团队：%s" % (r["total_distinct"] == 92371838), flush=True)
    print("naive    总数对审计：%s" % (r["total_naive"] == 92418269), flush=True)
    print("重叠 distinct/naive = %d / %d（双方一致值 32,676）" % (r["overlap_distinct"], r["overlap_naive"]), flush=True)
    print("多算量 = naive - distinct = %d（标准型）+ %d（重叠）= %d" %
          (r["excess_standard"], r["excess_overlap"], r["excess_standard"] + r["excess_overlap"]), flush=True)
    ex = sorted([d for d in r["detail"] if d[8]], key=lambda x: -x[8])[:10]
    print("多算量最大的 10 个来源 (类型, 类别, s, #A/对数, evenF?, distinct, naive, 多算):", flush=True)
    for d in ex:
        print("   %s %-3s s=%-5s nA=%-7d F=%d/%d  distinct=%-9d naive=%-9d excess=%d" %
              (d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7], d[8]), flush=True)
    print("总耗时 %.1fs" % (time.time() - t0), flush=True)
    j = load_result()
    j["structure_global"] = r
    save_result(j)


def cmd_debug_overlap():
    """逐项打印重叠（标准型 ∩ 七对子）贡献，并用字面审计口径复核。"""
    print("== 重叠分项（标准型 ∩ 七对子）==", flush=True)
    tot1 = tot1n = tot2 = tot2n = 0
    for c in range(4):
        inert = tuple(x for x in range(4) if x != c)
        for s in (1, 4, 7, 10, 13):
            m = 13 - s
            tiles = CAT_TILES[c]
            n_wp = n_o2 = 0
            for A in enum_multisets(s, tiles):
                if wp_nonempty(A):
                    n_wp += 1
                    if one2(A):
                        n_o2 += 1
            if not n_o2:
                continue
            nfe, keyse = filler_counts(inert, m, even_only=True)
            print("  I  c=%-1s s=%2d m=%2d  A_wp=%-6d A_wp&one2=%-5d  evenF(naive/distinct)=%d/%d  贡献 %d/%d"
                  % (CATNAME[c], s, m, n_wp, n_o2, nfe, len(keyse), n_o2 * len(keyse), n_o2 * nfe), flush=True)
            tot1 += n_o2 * len(keyse)
            tot1n += n_o2 * nfe
    print("  Type I 重叠合计 naive/distinct = %d / %d" % (tot1n, tot1), flush=True)
    for i in range(4):
        for j in range(i + 1, 4):
            c1, c2 = i, j
            inert = tuple(x for x in range(4) if x not in (c1, c2))
            for s1 in (2, 5, 8, 11):
                B1 = a_type2(c1)[s1]
                for s2 in (2, 5, 8, 11):
                    if s1 + s2 not in (4, 7, 10, 13):
                        continue
                    B2 = a_type2(c2)[s2]
                    m = 13 - s1 - s2
                    ovp = 0
                    for (pd1, v1, a1, o1), t1 in B1.items():
                        for (pd2, v2, a2, o2f), t2 in B2.items():
                            if not ((pd1 and v2) or (pd2 and v1)):
                                continue
                            if (o1 and a2 and not o2f) or (o2f and a1 and not o1):
                                ovp += t1 * t2
                    if not ovp:
                        continue
                    nfe, keyse = filler_counts(inert, m, even_only=True)
                    print("  II %-2s %2d+%2d m=%d  pairs=%d  evenF(naive/distinct)=%d/%d  贡献 %d/%d"
                          % (CATNAME[c1] + CATNAME[c2], s1, s2, m, ovp, nfe, len(keyse),
                             ovp * len(keyse), ovp * nfe), flush=True)
                    tot2 += ovp * len(keyse)
                    tot2n += ovp * nfe
    print("  Type II 重叠合计 naive/distinct = %d / %d" % (tot2n, tot2), flush=True)
    print("  重叠总计 naive/distinct = %d / %d" % (tot1n + tot2n, tot1 + tot2), flush=True)
    j = load_result()
    j["overlap_debug"] = {"I_naive": tot1n, "I_distinct": tot1, "II_naive": tot2n, "II_distinct": tot2}
    save_result(j)


if __name__ == "__main__":
    cmds = [a for a in (sys.argv[1:] or ["all"]) if a != "big"]
    for cmd in cmds:
        if cmd == "structure":
            cmd_structure()
        elif cmd == "witness":
            cmd_witness()
        elif cmd == "winning":
            cmd_winning()
        elif cmd == "debug_overlap":
            cmd_debug_overlap()
        elif cmd == "validate":
            cmd_validate()
        elif cmd == "all":
            cmd_structure()
            cmd_witness()
        else:
            print("unknown cmd", cmd)