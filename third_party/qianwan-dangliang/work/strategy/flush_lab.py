# -*- coding: utf-8 -*-
"""flush_lab.py -- 试验场: 清一色(单花色 m)383 类的 k=2/3/4 策略实验。

产出: work/strategy/out/flush_lab.json
"""
import sys, os, json, itertools, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjlib import *

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)
T0 = time.time()

def log(*a):
    print("[%6.1fs]" % (time.time() - T0), *a, flush=True)

SUIT = 0  # m
BASE = SUIT * 9

def pair_melds_flush(c9):
    for pi in range(9):
        if c9[pi] >= 2:
            d = list(c9); d[pi] -= 2
            if can_melds(tuple(d), False):
                return True
    return False

# ---------- 1. 清一色 14 张和牌 / 13 张听牌
log("枚举清一色 14 张和牌 ...")
wins = []
for combo in itertools.combinations_with_replacement(range(9), 14):
    c = [0]*9
    for x in combo: c[x] += 1
    if max(c) > 4: continue
    if pair_melds_flush(c): wins.append(tuple(c))
log("清一色和牌 14 张:", len(wins))

tenpai = set()
for w in wins:
    for i in range(9):
        if w[i]:
            h = list(w); h[i] -= 1
            tenpai.add(tuple(h))
log("清一色听牌(标准) 13 张:", len(tenpai))

# ---------- 2. 两种 W: W_std(仅标准) 与 W_full(含七对子/国士)
def w_std_flush(h9):
    res = []
    for t in range(9):
        if h9[t] < 4:
            d = list(h9); d[t] += 1
            if pair_melds_flush(d): res.append(BASE + t)
    return tuple(res)

hands34 = []
for h9 in sorted(tenpai):
    c = [0]*34
    for i in range(9): c[BASE + i] = h9[i]
    hands34.append((h9, tuple(c)))

cls_std = {}
cls_full = {}
for h9, c34 in hands34:
    Ws = frozenset(w_std_flush(h9))
    Wf = waits13(c34)          # 完整
    cls_std.setdefault(Ws, []).append(h9)
    cls_full.setdefault(Wf, []).append(h9)

log("类数: W_std=%d, W_full=%d" % (len(cls_std), len(cls_full)))
# W_full 相对 W_std 的变化
added = sum(1 for h9, c34 in hands34 if len(waits13(c34)) > len(frozenset(w_std_flush(h9))))
log("W_full 严格大于 W_std 的手牌数:", added)
chi_hands = [(h9, sorted(tile_name(t) for t in waits13(c34) - frozenset(w_std_flush(h9))))
             for h9, c34 in hands34 if waits13(c34) - frozenset(w_std_flush(h9))]
log("七对子附加非空的清一色手牌数:", len(chi_hands), "例:", chi_hands[:3])

def core_codes(hands9, k):
    """返回 (|K|, K 元组) —— K = 逐点最小(公共牌多重集)"""
    K = [4]*9
    for h in hands9:
        for i in range(9):
            if h[i] < K[i]: K[i] = h[i]
    return sum(K), tuple(K)

def submults9(h9, k):
    present = []
    for i, n in enumerate(h9): present += [i]*n
    out = set()
    for combo in itertools.combinations_with_replacement(present, k):
        need = {}
        for x in combo: need[x] = need.get(x, 0)+1
        if all(h9[x] >= n for x, n in need.items()): out.add(combo)
    return out

report = {"flush": {}, "hand_counts": {}}
report["hand_counts"] = {"winning14": len(wins), "tenpai13_std": len(tenpai),
                         "classes_Wstd": len(cls_std), "classes_Wfull": len(cls_full),
                         "hands_with_chiitoi_extra": len(chi_hands)}

for tag, cls in (("W_std", cls_std), ("W_full", cls_full)):
    sig = {}
    nocommon = {}
    for k in (1, 2, 3, 4):
        nc = 0
        for W, hs in cls.items():
            sz, K = core_codes(hs, k)
            if sz < k: nc += 1
        nocommon[k] = nc
    report["flush"][tag] = {"classes": len(cls), "classes_without_common_code": nocommon}
    log("%s: 类数=%d 无公共码(k=1..4)=%s" % (tag, len(cls), nocommon))

json.dump(report, open(os.path.join(OUT, "flush_lab.json"), "w"), ensure_ascii=False, indent=1)
log("阶段 1 完成, 写入 flush_lab.json")
