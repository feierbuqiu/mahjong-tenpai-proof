# -*- coding: utf-8 -*-
"""lead_check_disproof.py -- Lead 独立复核 analyst-lower 的 k=3 否证（U = {m2..m8}）
用 verifier 的 indep_core.compute_W（独立实现）+ 我自己的枚举，检查 N、L 与预算 7^3=343。
"""
import sys, os, json, itertools, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'verify'))
from indep_core import compute_W
HONN = ["E","S","W","N","Haku","Hatsu","Chun"]
def nm(t): return ("%d%s" % (t % 9 + 1, "mps"[t // 9])) if t < 27 else HONN[t - 27]

def hands_in(U):
    """所有 13 张、每种 <=4 的手牌（U 为 tile idx 列表）"""
    n = len(U); out = []
    cur = [0]*n
    def rec(i, rem):
        if i == n-1:
            if rem <= 4:
                v = [0]*34
                for j, t in enumerate(U): v[t] = cur[j]
                cur[i] = rem; v[U[i]] = rem
                out.append(tuple(v))
            cur[i] = 0
            return
        for c in range(min(4, rem)+1):
            cur[i] = c; rec(i+1, rem-c)
        cur[i] = 0
    rec(0, 13); return out

def run(U, label):
    hs = hands_in(U)
    cls = collections.defaultdict(list)
    nten = 0
    for v in hs:
        W = compute_W(list(v))
        if W:
            nten += 1
            cls[frozenset(W)].append(v)
    N = len(cls)
    # L: 类内 U 内手牌的多重集交集 < 3 张
    L = 0; lcls = []
    for W, hands in cls.items():
        inter = [min(h[t] for h in hands) for t in range(34)]
        if sum(inter) < 3:
            L += 1; lcls.append([nm(t) for t in sorted(W)])
    print("%s |U|=%d hands=%d tenpai=%d N=%d L=%d  N+L=%d  budget=%d  ratio=%.3f  %s" % (
        label, len(U), len(hs), nten, N, L, N+L, len(U)**3, (N+L)/len(U)**3,
        "DISPROVED" if N+L > len(U)**3 else "no"))
    return N, L, lcls

r1 = run([8,9,10,11,12,13], "m7..m8? (check)") if False else None
# U = m2..m8  -> indices 1..7
res = run(list(range(1,8)), "U={m2..m8}")
# 自检： U = m1..m9 -> 387 / 87
sel = run(list(range(0,9)), "U={m1..m9} (self-check 387/87)")
json.dump({"U_m2m8": {"N": res[0], "L": res[1], "budget": 343, "L_classes": res[2]},
           "U_m1m9": {"N": sel[0], "L": sel[1], "budget": 729}},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lead_disproof_check.json'), 'w'), ensure_ascii=False, indent=1)
print("saved work/recon/lead_disproof_check.json")
