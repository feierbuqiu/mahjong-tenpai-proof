
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""work/recon/tenpai_verify_struct.py -- 结构枚举 (Type I/II A/F) 双口径独立重算 (verifier 自写).
约定: 手牌限制在 universe(默认全部 34 张); A 的补牌判定用"自由"面子表 (补牌 t 可在 universe 之外,
与审计/团队一致); 惰性填充用 universe 限制的面子表.
  distinct 口径: 填充按相异牌张向量数 (D)  ; naive 口径: 按面子多重集数 (N) = 审计 t15 的 out=[]
用法: --universe <types|all> ; --global
"""
import sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from tenpai_verify_indep import dec_table, LEN, BASE, POW5

def cat_of(t): return (t // 9) if t < 27 else 3

def idxv(v):
    s = 0
    for i in range(len(v)): s += v[i] * POW5[i]
    return s

def mok(tbl, v): return int(tbl[idxv(v)]) > 0

def pair_dec(tbl, v):
    for i in range(len(v)):
        if v[i] >= 2:
            v[i] -= 2
            ok = mok(tbl, v)
            v[i] += 2
            if ok: return True
    return False

def wset_nonempty(tbl, v):
    for i in range(len(v)):
        if v[i] < 4:
            v[i] += 1
            ok = pair_dec(tbl, v)
            v[i] -= 1
            if ok: return True
    return False

def vset_list(tbl, v):
    out = []
    for i in range(len(v)):
        if v[i] < 4:
            v[i] += 1
            if mok(tbl, v): out.append(i)
            v[i] -= 1
    return out

def multiset_lists(c, s, types):
    """类别 c 内、允许位置(由 types 决定)上总数 s、每张<=4 的全部向量 (list of list)"""
    L = LEN[c]
    allowed = list(range(L))
    if types is not None:
        keep = set((t % 9) if c < 3 else (t - 27) for t in types if cat_of(t) == c)
        allowed = [i for i in allowed if i in keep]
    res = []
    def rec(j, rem, cur):
        if j == len(allowed):
            if rem == 0:
                v = [0] * L
                for i, li in enumerate(allowed): v[li] = cur[i]
                res.append(v)
            return
        for k in range(0, min(4, rem) + 1):
            cur.append(k); rec(j + 1, rem - k, cur); cur.pop()
    rec(0, s, [])
    return res

def fill_tables(types):
    """universe 限制下每类的 D[c][s]=相异可分解向量数, N[c][s]=面子多重集数"""
    D = []; N = []
    for c in range(4):
        L = LEN[c]; allowed = [i for i in range(L)]
        if types is not None:
            keep = set((t % 9) if c < 3 else (t - 27) for t in types if cat_of(t) == c)
            allowed = [i for i in allowed if i in keep]
        tbl = dec_table(c, set(allowed))
        d = [0] * 14; n = [0] * 14
        for idx in range(5 ** L):
            v = []; r = idx
            for _ in range(L): v.append(r % 5); r //= 5
            if any(v[i] and i not in allowed for i in range(L)): continue
            s = sum(v)
            if s > 13: continue
            val = int(tbl[idx])
            if val > 0: d[s] += 1; n[s] += val
        D.append(d); N.append(n)
    return D, N

def nfill(inert, m, tab):
    res = 0
    def rec(i, rem, prod):
        nonlocal res
        if i == len(inert):
            if rem == 0: res += prod
            return
        ci = inert[i]
        for s in range(0, rem + 1, 3):
            if tab[ci][s] == 0: continue
            rec(i + 1, rem - s, prod * tab[ci][s])
    rec(0, m, 1)
    return res

def run(types, label):
    t0 = time.time()
    D, N = fill_tables(types)
    free = [dec_table(c, None) for c in range(4)]
    tot_d = tot_n = 0; det = []
    for c in range(4):
        inert = tuple(i for i in range(4) if i != c)
        for s in (1, 4, 7, 10, 13):
            m = 13 - s
            fd = nfill(inert, m, D); fn = nfill(inert, m, N)
            nA = 0
            for A in multiset_lists(c, s, types):
                if wset_nonempty(free[c], A): nA += 1
            tot_d += nA * fd; tot_n += nA * fn
            det.append(["I", "mpsz"[c], s, nA, fd, fn, nA * (fn - fd)])
    for c1 in range(4):
        for c2 in range(c1 + 1, 4):
            inert = tuple(i for i in range(4) if i not in (c1, c2))
            for s1 in (2, 5, 8, 11):
                for s2 in (2, 5, 8, 11):
                    if s1 + s2 not in (4, 7, 10, 13): continue
                    m = 13 - s1 - s2
                    fd = nfill(inert, m, D); fn = nfill(inert, m, N)
                    L1 = [(A, vset_list(free[c1], A), pair_dec(free[c1], A)) for A in multiset_lists(c1, s1, types)]
                    L2 = [(A, vset_list(free[c2], A), pair_dec(free[c2], A)) for A in multiset_lists(c2, s2, types)]
                    nP = 0
                    for A1, V1, p1 in L1:
                        for A2, V2, p2 in L2:
                            if (V2 if p1 else []) or (V1 if p2 else []): nP += 1
                    tot_d += nP * fd; tot_n += nP * fn
                    if nP: det.append(["II", "mpsz"[c1] + "mpsz"[c2], "%d+%d" % (s1, s2), nP, fd, fn, nP * (fn - fd)])
    out = {"label": label, "distinct": tot_d, "naive": tot_n, "excess": tot_n - tot_d,
           "sec": round(time.time() - t0, 1), "detail": det}
    print("%-22s distinct=%-10d naive=%-10d excess=%-6d (%.0fs)" % (label, tot_d, tot_n, tot_n - tot_d, out["sec"]), flush=True)
    return out

if __name__ == "__main__":
    args = sys.argv[1:]
    res = {}
    if "--universe" in args:
        res["2m3m4m+E"] = run([1, 2, 3, 27], "2m3m4m+E")
        res["1m2m3m1p2p3p"] = run([0, 1, 2, 9, 10, 11], "1m2m3m1p2p3p")
        res["1m2m3m4m5m1p"] = run([0, 1, 2, 3, 4, 9], "1m2m3m4m5m1p")
        res["1m2m3m4m1p2p3p4p"] = run([0, 1, 2, 3, 9, 10, 11, 12], "1m2m3m4m1p2p3p4p")
        res["flush"] = run(list(range(9)), "flush(9)")
        res["m1-6+p1-6"] = run([0, 1, 2, 3, 4, 5, 9, 10, 11, 12, 13, 14], "m1-6+p1-6")
    if "--global" in args:
        res["global"] = run(None, "GLOBAL(34)")
    json.dump(res, open(os.path.join(HERE, "out", "tenpai_verify_struct.json"), "w"), ensure_ascii=False, indent=1)
    print("wrote out/tenpai_verify_struct.json", flush=True)
