# -*- coding: utf-8 -*-
"""k3_descriptor_stats.py -- chiitoi 描述子的 z 分布 / 每类来源规模统计（Lead）"""
import json, collections
HONN = ["E","S","W","N","Haku","Hatsu","Chun"]
def ti(nm):
    if nm in HONN: return 27 + HONN.index(nm)
    return "mps".index(nm[-1])*9 + int(nm[0]) - 1
g = json.load(open('work/data/out/global.json', encoding='utf-8'))
cls = g['classes']
cd = g['chiitoi_descriptors']
print("classes with chiitoi descriptors:", len(cd))
per_z = collections.Counter()
multi = 0
for key, lst in cd.items():
    zs = set(ti(d['z']) for d in lst)
    if len(zs) > 1: multi += 1
    for z in zs: per_z[z] += 1
print("classes whose descriptors use >1 distinct z:", multi)
print("max #classes sharing one z:", max(per_z.values()))
print("z histogram:", sorted(per_z.items(), key=lambda kv: -kv[1])[:12])
# sources stats
st = collections.Counter(); small = collections.Counter()
for r in cls:
    for s in r['sources']:
        if s['kind'] == 'I':
            n = sum(int(c) for c in s['A'])
        elif s['kind'] == 'II':
            n = sum(int(c) for c in s['minA1']) + sum(int(c) for c in s['minA2'])
        else:
            n = 13
        st[n] += 1
        if n < 3: small[r['W'][0] if r['W'] else '?'] += 1
print("|am| distribution:", sorted(st.items()))
print("classes with |am|<3 sources:", len(small), "total such sources:", sum(small.values()))
print("top:", small.most_common(8))
# kinds
kk = collections.Counter(s['kind'] for r in cls for s in r['sources'])
print("source kinds:", kk)
