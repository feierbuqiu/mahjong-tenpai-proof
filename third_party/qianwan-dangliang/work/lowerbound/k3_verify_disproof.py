# -*- coding: utf-8 -*-
"""k3_verify_disproof.py --- 独立复核 U = {m2..m8} 的 k=3 否证
路径A: work/lowerbound/lower.py 的 waits() (标准型+七对子逐牌判和)
路径B: 独立的 14 张和牌判据 (对所有起始位回溯拆面子+雀头) + W(H)={t: win14(H+t)}
另: L 用"M_3 多重集显式取交"计算, 不用 min-count 捷径。
"""
import itertools, json, sys, time
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
sys.path.insert(0, "work/lowerbound")
import lower as L

U = list(range(1, 8))          # m2..m8
MARKS = ["m1","m2","m3","m4","m5","m6","m7","m8","m9"]
t0 = time.time()

def name(t):
    if t < 9: return "m%d" % (t+1)
    if t < 18: return "p%d" % (t-8)
    if t < 27: return "s%d" % (t-17)
    return "z%d" % (t-26)

# ---------- 路径 B: 独立的 14 张和牌判据 ----------
def decompose(c, need):
    """c: 34 长度; 能否拆成恰 need 个面子 (所有拆法都试, 不同算法: 递归幂集)"""
    if need == 0: return all(x == 0 for x in c)
    i = 0
    while i < 34 and c[i] == 0: i += 1
    if i == 34: return False
    if c[i] >= 3:
        c2 = list(c); c2[i] -= 3
        if decompose(c2, need-1): return True
    catlen = 9 if i < 27 else 7
    if i % 9 <= catlen - 3:
        if c[i+1] > 0 and c[i+2] > 0:
            c2 = list(c); c2[i] -= 1; c2[i+1] -= 1; c2[i+2] -= 1
            if decompose(c2, need-1): return True
    return False

def win14B(c):
    for i in range(34):
        if c[i] >= 2:
            c2 = list(c); c2[i] -= 2
            if decompose(c2, 4): return True
    # 七对子
    n2 = sum(1 for x in c if x == 2)
    if n2 == 7 and all(x in (0,2) for x in c): return True
    # 国士
    s = sum(c[27:34]) + c[0] + c[8] + c[9] + c[17] + c[18] + c[26]
    if s == 14 and c[0]>=1 and c[8]>=1 and c[9]>=1 and c[17]>=1 and c[18]>=1 and c[26]>=1 \
       and all(x>=1 for x in c[27:34]) and sum(1 for x in c if x==2)==1: return True
    return False

def W_B(c34):
    out = []
    for t in range(34):
        if c34[t] >= 4: continue
        c = list(c34); c[t] += 1
        if win14B(c): out.append(t)
    return tuple(out)

def gen(U, total=13, cap=4):
    n = len(U); cnt = [0]*n
    def rec(i, rem):
        if i == n-1:
            if rem <= cap:
                cnt[i] = rem; yield tuple(cnt)
            cnt[i] = 0; return
        for v in range(min(cap, rem)+1):
            cnt[i] = v
            yield from rec(i+1, rem-v)
        cnt[i] = 0
    yield from rec(0, total)

# ---------- 枚举 ----------
clsA = {}; clsB = {}
nA = nB = 0
for vec in gen(U):
    c34 = [0]*34
    for i, t in enumerate(U): c34[t] = vec[i]
    WA = L.waits(c34)
    WB = W_B(c34)
    if WA != WB:
        print("!!! W 不一致:", c34, WA, WB); sys.exit(1)
    if WA:
        nA += 1
        lst = clsA.setdefault(WA, []); 
        if len(lst) < 4000: lst.append(tuple(c34))
print("路径A 与 路径B 的 W 对所有手牌完全一致 ✓")
print("U = {%s}  |U| = %d   13 张向量总数 = %d   听牌手牌 = %d" % (",".join(name(t) for t in U), len(U), sum(1 for _ in gen(U)), nA))
N = len(clsA)
print("N(U) = 类别数 =", N)

codes = list(itertools.combinations_with_replacement(U, 3))
print("|Codes_3(U)| = 7^3 =", len(U)**3, " 无序 3-码个数 =", len(codes))
Lcnt = 0; witnesses = []; Lclasses = []
for W, hs in clsA.items():
    # 显式取交: c 必须 ⊆ 每一手牌
    common = []
    for c in codes:
        ok = True
        for h in hs:
            for x in set(c):
                if h[x] < c.count(x): ok = False; break
            if not ok: break
        if ok: common.append(c)
    if not common:
        Lcnt += 1
        Lclasses.append(W)
        # 找一对"M_3 不相交"的手牌作见证
        sets = []
        for h in hs:
            s = set()
            for c in codes:
                if all(h[x] >= c.count(x) for x in set(c)): s.add(c)
            sets.append(s)
        wit = None
        for i in range(len(hs)):
            for j in range(i+1, len(hs)):
                if not (sets[i] & sets[j]):
                    wit = (hs[i], hs[j]); break
            if wit: break
        # blocker 表: 对每个码 c ∈ Codes_3(U) 给出一手不含 c 的类内手牌 (充分证明交集为空)
        blockers = []
        for c in codes:
            for h in hs:
                if any(h[x] < c.count(x) for x in set(c)):
                    blockers.append({"code": [name(x) for x in c],
                                     "hand": [[name(t), h[t]] for t in U if h[t] > 0]})
                    break
        witnesses.append({"W": [name(t) for t in W], "class_size": len(hs),
                          "pair_disjoint": None if wit is None else
                          [[name(t) for t in wit[0] if t in U], [name(t) for t in wit[1] if t in U]],
                          "blockers": blockers})
print("L(U) = 无公共 3-码的类数 =", Lcnt)
print()
print("=== 否证算术 ===")
print("  N(U) + L(U) = %d + %d = %d" % (N, Lcnt, N+Lcnt))
print("  |U|^3 = %d^3 = %d" % (len(U), len(U)**3))
print("  %d > %d ?  %s" % (N+Lcnt, len(U)**3, (N+Lcnt) > len(U)**3))
print()
print("前若干无公共码的类 (W, 类内手牌数, 见证两手):")
for w in witnesses[:8]:
    print("  W=%s size=%d pair=%s" % (w["W"], w["class_size"], w["pair_disjoint"]))
import hashlib
allW = sorted([",".join(name(t) for t in W) for W in clsA])
json.dump({"theorem": "对 U={m2..m8}, N(U)+L(U) = 347+52 = 399 > 343 = |U|^3, 故 k=3 不可行",
           "U": [name(t) for t in U], "tile_indices": U, "|U|": len(U), "budget": len(U)**3,
           "N": N, "L": Lcnt, "N_plus_L": N+Lcnt, "disproved": (N+Lcnt) > len(U)**3,
           "n_hands": nA, "n_vectors": 7875,
           "class_list_digest_sha256": hashlib.sha256(";".join(allW).encode()).hexdigest(),
           "all_class_W": allW, "L_classes": witnesses},
          open("work/lowerbound/k3_disproof_certificate.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n证书写入 work/lowerbound/k3_disproof_certificate.json   t=%.0fs" % (time.time()-t0))
