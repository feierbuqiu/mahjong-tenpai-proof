# -*- coding: utf-8 -*-
"""cross_global.py -- 我的独立类表 vs enum-core global.json 对拍"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import table_lib as TL
G = json.load(open(r"D:\DSH\MJ2\work\data\out\global.json", encoding="utf-8"))
mine = set(frozenset(W) for W in TL.build()["cls"].keys())
theirs = set()
for c in G["classes"]:
    theirs.add(frozenset(c["W"]))
    # W 里可能是牌名字符串? 检查
print("mine=%d enum-core=%d" % (len(mine), len(theirs)))
from mjlib import tile_name
HN = {"E": 27, "S": 28, "W": 29, "N": 30, "Haku": 31, "Hatsu": 32, "Chun": 33}
m2 = {tile_name(t): t for t in range(34)}
m2.update(HN)
theirs = set(frozenset(m2[x] for x in W) for W in theirs)
diff1 = mine - theirs; diff2 = theirs - mine
print("only_mine=%d only_theirs=%d" % (len(diff1), len(diff2)))
def fmt(W): 
    from mjlib import tile_name
    return sorted(tile_name(t) for t in W)
print("only_mine 样例:", [fmt(W) for W in sorted(diff1, key=lambda w:(len(w),sorted(w)))[:8]])
print("only_theirs 样例:", [fmt(W) for W in sorted(diff2, key=lambda w:(len(w),sorted(w)))[:8]])
from collections import Counter
print("only_mine |W| 分布:", dict(sorted(Counter(len(W) for W in diff1).items())))
print("only_theirs |W| 分布:", dict(sorted(Counter(len(W) for W in diff2).items())))
print("enum-core by_size:", G.get("by_size"))
print("enum-core no_common_code:", G.get("no_common_code"))
print("enum-core sum_K:", G.get("sum_K_over_classes"))
