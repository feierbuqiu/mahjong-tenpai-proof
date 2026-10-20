# -*- coding: utf-8 -*-
"""
k3_subuniverse.py --- T8: 把子宇宙预算引理推广到 k=3, 系统普查牌集合 U

判据 (k=3):  对任意 U,  Σ_{C : C∩U≠∅} τ_U(C) ≤ |U|^3
  其中 N(U) = 有"全部落在 U 内"的听牌手牌的类数; L(U) = 其中在 U 内**无公共 3-码**的类数。
  因为 τ_U ≥ 1, 且无公共码 ⇔ τ_U ≥ 2, 故 Σ τ_U ≥ N + L。
  **若 N(U) + L(U) > |U|^3, 则 k=3 不可行。**

关键简化 (本脚本据此实现, 并有自检):
  码 c (3 张的多重集, ⊆U) 对所有 U-手牌可用 ⟺ 逐牌最小计数 m_t = min_{H∈C∩U} n_t(H) 满足 Σ_t m_t ≥ 3。
  故 L(U) = #{C : C∩U ≠ ∅ 且 Σ_t m_t(C) ≤ 2}。
"""
import itertools, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lower import waits, is_std_win, is_chiitoi_win, is_kokushi_win, TERMINALS

CAT = [0]*9 + [1]*9 + [2]*9 + [3]*7
T0 = time.time()
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "k3_subuniverse.json")
if len(sys.argv) > 3: OUT = sys.argv[3] if os.path.isabs(sys.argv[3]) else os.path.join(os.getcwd(), sys.argv[3])

def gen_vectors(U, total=13, cap=4):
    n = len(U); cnt = [0]*n
    def rec(i, rem):
        if i == n-1:
            if rem <= cap:
                cnt[i] = rem
                yield tuple(cnt)
            cnt[i] = 0
            return
        for v in range(min(cap, rem)+1):
            cnt[i] = v
            yield from rec(i+1, rem-v)
        cnt[i] = 0
    yield from rec(0, total)

def quick_ok(c34, U):
    """必要条件快速筛: 标准型余数型, 或七对子型(6对+1单), 或国士型"""
    ncat = [0, 0, 0, 0]
    for t in U: ncat[CAT[t]] += c34[t]
    r = sorted(x % 3 for x in ncat)
    if r == [0, 0, 0, 1] or r == [0, 0, 2, 2]: return True
    n2 = n1 = 0
    for x in c34:
        if x == 2: n2 += 1
        elif x == 1: n1 += 1
        elif x != 0: return False
    if n2 == 6 and n1 == 1: return True
    if all(c34[t] == 0 for t in range(34) if t not in TERMINALS):
        if sum(1 for t in TERMINALS if c34[t] > 0) >= 12: return True
    return False

def census(U, verbose=False):
    U = sorted(set(U)); n = len(U)
    idx = {t: i for i, t in enumerate(U)}
    classes = {}   # W -> 逐牌最小计数 (len n)
    nhands = 0
    for vec in gen_vectors(U):
        c34 = [0]*34
        for i, t in enumerate(U):
            if vec[i]: c34[t] = vec[i]
        if not quick_ok(c34, U): continue
        W = waits(c34)
        if not W: continue
        nhands += 1
        m = classes.get(W)
        if m is None:
            classes[W] = list(vec)
        else:
            for i in range(n):
                if vec[i] < m[i]: m[i] = vec[i]
    N = len(classes)
    L = sum(1 for m in classes.values() if sum(m) <= 2)
    b = n**3
    return {"U": U, "|U|": n, "budget": b, "N": N, "L": L, "N_plus_L": N+L,
            "ratio": (N+L)/b, "disproved": (N+L) > b, "tenpai_hands_in_U": nhands,
            "time_s": round(time.time()-T0, 1)}

# ---------------- 待查 U 列表 (按 |U| 升序) ----------------
def build_us(maxsize):
    us = []
    def add(u, tag):
        u = sorted(set(u))
        if len(u) <= maxsize: us.append((tag, u))
    # A 单花色前缀 (含单花色真子集)
    for nn in range(3, 10): add(list(range(nn)), "m-prefix-%d" % nn)
    # B 前缀 + 一个东 (字牌)
    for nn in range(3, 10): add(list(range(nn)) + [27], "m-prefix-%d+E" % nn)
    # C 9m + h 张字牌
    for h in range(0, 8): add(list(range(9)) + list(range(27, 27+h)), "9m+%dz" % h)
    # D 双花色小 U
    for a in range(1, 8):
        for b in range(1, 8):
            if 4 <= a + b <= maxsize: add(list(range(a)) + list(range(9, 9+b)), "2suit-m%d+p%d" % (a, b))
    # E 三花色小 U
    for a in (2, 3, 4):
        for b in (2, 3, 4):
            for c in (2, 3, 4):
                if a + b + c <= maxsize:
                    add(list(range(a)) + list(range(9, 9+b)) + list(range(18, 18+c)), "3suit-m%d+p%d+s%d" % (a, b, c))
    # F 幺九字 (国士相关)
    term = [0, 8, 9, 17, 18, 26]
    add(term, "terminals6")
    for h in range(0, 8): add(term + list(range(27, 27+h)), "terminals6+%dz" % h)
    # G: m1..m9 去掉 k 张 (k=1,2) 的"缺口"子集, 及 +1 字牌 (探测 |U|=7,8,9 峰值附近)
    base = list(range(9))
    for kk in (1, 2):
        for missing in itertools.combinations(range(9), kk):
            u = [t for t in base if t not in missing]
            tag = "G-miss%d-%s" % (kk, ",".join(str(m) for m in missing))
            add(u, tag)
            add(u + [27], tag + "+E")
    # H: 字牌子集, 以及 字牌 + 小花色前缀 (探测"字牌密集"的小 U)
    for h in range(1, 8):
        add(list(range(27, 27+h)), "H-z%d" % h)
        for nn in (1, 2, 3):
            add(list(range(nn)) + list(range(27, 27+h)), "H-m%d+z%d" % (nn, h))
    # 去重 (按牌集合)
    seen = set(); out = []
    for tag, u in us:
        key = tuple(u)
        if key in seen: continue
        seen.add(key); out.append((tag, u))
    out.sort(key=lambda x: (len(x[1]), x[0]))
    return out

def main():
    maxsize = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    only = sys.argv[2] if len(sys.argv) > 2 else None
    results = []
    if os.path.exists(OUT):
        try: results = json.load(open(OUT, encoding="utf-8")).get("results", [])
        except Exception: results = []
    done = {tuple(r["U"]) for r in results}
    for tag, U in build_us(maxsize):
        if tuple(U) in done: continue
        if only and not tag.startswith(only): continue
        r = census(U)
        r["tag"] = tag
        results.append(r)
        print("[%-16s] |U|=%2d %3d^3=%6d  N=%5d L=%5d  N+L=%6d  ratio=%.3f %s (t=%.0fs)" % (
            tag, r["|U|"], r["|U|"], r["budget"], r["N"], r["L"], r["N_plus_L"], r["ratio"],
            "*** 否证! ***" if r["disproved"] else "", time.time()-T0), flush=True)
        json.dump({"results": results}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
    results.sort(key=lambda r: -r["ratio"])
    print("\n=== 比值前 10 ===")
    for r in results[:10]:
        print("  %-16s |U|=%2d budget=%6d N=%5d L=%5d N+L=%6d ratio=%.3f %s" % (
            r["tag"], r["|U|"], r["budget"], r["N"], r["L"], r["N_plus_L"], r["ratio"], "否证" if r["disproved"] else ""))
    dis = [r for r in results if r["disproved"]]
    print("\n否证的 U 个数 =", len(dis))
    print("结论: " + ("*** 存在否证 U => k=3 不可行 ***" if dis else "计数法仍未否证 k=3"))

if __name__ == "__main__":
    main()
