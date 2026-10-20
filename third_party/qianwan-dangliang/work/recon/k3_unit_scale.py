# -*- coding: utf-8 -*-
"""k3_unit_scale.py -- 估计 k=3 装包的『覆盖单元』规模（Lead）
单元 = 来源块；|am|>=3 的来源可用一族 3-码(⊆am) 覆盖；|am|<3 的来源需按 A 展开。
"""
import json, sys, os, collections
sys.path.insert(0, 'work/strategy')
import table_lib
T = table_lib.build()
print("table built: classes", len(T['cls']))
g = json.load(open('work/data/out/global.json', encoding='utf-8'))
cls = g['classes']
print("global classes", len(cls))

def am_of(s):
    if s['kind'] == 'I':
        return [int(c) for c in s['A']]
    if s['kind'] == 'II':
        v1 = [int(c) for c in s['minA1']]; v2 = [int(c) for c in s['minA2']]
        return [a+b for a, b in zip(v1, v2)]
    return [int(c) for c in s['A']] if 'A' in s else None

# kokushi source fields
for r in cls:
    for s in r['sources']:
        if s['kind'] == 'kokushi':
            print("kokushi source keys:", list(s.keys()), json.dumps(s, ensure_ascii=False)[:200]); break
    else: continue
    break

def expand_II(xs1, xs2):
    return len(xs1) * len(xs2)

tot_units = 0; small_units = 0; small_expanded = 0
per_class_units = []
small_by_class = collections.Counter()
for r, blks in zip(cls, [None]*len(cls)):
    pass

# 用 block_sources 展开：对每个类统计单元数与 |am|<3 单元展开后的 A 数
CLS = T['cls']
Wlist = [r['W'] for r in cls]
def W_to_fs(W):
    out = []
    for nm in W:
        out.append(nm)
    return frozenset(out)
big = 0
for i, r in enumerate(cls):
    # find matching class key in T['cls'] by W list
    pass
print("done stage1")
