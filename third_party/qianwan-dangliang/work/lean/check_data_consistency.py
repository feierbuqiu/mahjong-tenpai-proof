# -*- coding: utf-8 -*-
"""check_data_consistency.py -- 校验 lean/Mj/Data.lean 的 planData 与 work/verify/plan_k4_FINAL.json 完全一致（Lead）
比较：类数、每类键（waits 递增索引）与码列表（有序 4 元组）逐类逐条一致。
"""
import json, re, sys, collections

# 1) Python 侧的真实方案
P = json.load(open('work/verify/plan_k4_FINAL.json', encoding='utf-8'))
HONN = ['E','S','W','N','Haku','Hatsu','Chun']
def ti(s): return 27 + HONN.index(s) if s in HONN else 'mps'.index(s[-1])*9 + int(s[0]) - 1
plan = {}
for r in P['plan']:
    key = tuple(sorted(ti(x) for x in r['W']))
    plan[key] = [tuple(c) for c in r['codes']]
py_codes = [c for cs in plan.values() for c in cs]
print('Python: classes', len(plan), 'codes', len(py_codes), 'distinct codes', len(set(py_codes)))

# 2) Lean Data.lean 里的 planData（解析其文本表示）
txt = open('lean/Mj/Data.lean', encoding='utf-8').read()
m = re.search(r'def planData\s*:\s*List \(List Nat × List \(List Nat\)\)\s*:=\s*(.*?)\n(def |theorem |#|end )', txt, re.S)
if not m:
    print('ERROR: 无法在 Data.lean 中定位 planData 定义'); sys.exit(1)
body = m.group(1)
# 去掉注释与换行，按顶层括号切分类条目
body = re.sub(r'--[^\n]*', '', body)
items = []
depth = 0; cur = ''
for ch in body:
    if ch == '(': depth += 1
    if ch == ')': depth -= 1
    if ch == ',' and depth == 0:
        items.append(cur); cur = ''
        continue
    if depth >= 0: cur += ch
if cur.strip(): items.append(cur)
lean_plan = []
for it in items:
    it = it.strip()
    if not it: continue
    mm = re.match(r'^\(\s*\[([^\]]*)\]\s*,\s*\[([^\]]*)\]\s*\)$', it, re.S)
    if not mm: continue
    key = tuple(int(x) for x in re.findall(r'-?\d+', mm.group(1)))
    codes = re.findall(r'\[([^\[\]]*)\]', mm.group(2))
    cs = [tuple(int(x) for x in re.findall(r'-?\d+', c)) for c in codes]
    lean_plan.append((key, cs))
lean_codes = [c for _, cs in lean_plan for c in cs]
print('Lean  : classes', len(lean_plan), 'codes', len(lean_codes), 'distinct codes', len(set(lean_codes)))

# 3) 逐类比较
lean_map = {k: cs for k, cs in lean_plan}
only_py = set(plan) - set(lean_map)
only_lean = set(lean_map) - set(plan)
print('keys only in Python:', len(only_py), 'keys only in Lean:', len(only_lean))
diff = 0
for k in set(plan) & set(lean_map):
    if sorted(plan[k]) != sorted(lean_map[k]):
        diff += 1
        if diff <= 3: print('  class mismatch', k, 'py', len(plan[k]), 'lean', len(lean_map[k]))
print('classes with differing code sets:', diff)
print('CONSISTENT:', (len(only_py) == 0 and len(only_lean) == 0 and diff == 0))
