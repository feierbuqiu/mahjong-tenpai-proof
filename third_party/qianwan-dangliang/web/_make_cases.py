# -*- coding: utf-8 -*-
"""_make_cases.py -- 生成 JS 引擎交叉核对用例(随机 13 张手牌 + Python 真值 waits)"""
import sys, os, json, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "work", "strategy"))
from mjlib import *
random.seed(4242)
cases = []
for _ in range(3000):
    c = [0]*34; n = 0
    while n < 13:
        t = random.randrange(34)
        if c[t] < 4: c[t] += 1; n += 1
    cases.append({"c": c, "w": sorted(waits13(tuple(c)))})
# 加一些国士/七对子构造与听牌手牌
for miss in KOKUSHI_TILES:
    c = [0]*34
    for t in KOKUSHI_TILES: c[t] = 1
    c[miss] += 1
    if sum(c) == 14:
        c[miss] -= 1
    cases.append({"c": c, "w": sorted(waits13(tuple(c)))})
c = [0]*34
for i in range(6): c[i*2] = 2
c[6] = 1
cases.append({"c": c, "w": sorted(waits13(tuple(c)))})
json.dump(cases, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_js_cases.json"), "w"), ensure_ascii=False)
print("cases", len(cases))
