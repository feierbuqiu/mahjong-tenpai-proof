# -*- coding: utf-8 -*-
"""est_gap.py -- 估算补全 Lean 缺口所需的规模（Lead）"""
import sys, os, collections, pickle, json
sys.path.insert(0,'work/strategy')
import table_lib
T=pickle.load(open('work/strategy/out/table_cache.pkl','rb'))
CLS=T['cls']
# II 块统计
nb=collections.Counter()
pairs_expand=0
for W,blocks in CLS.items():
    for b in blocks:
        if b[0]=='II':
            nb[(b[1][1],b[2][1])]+=1
            if sum(b[5])<4:
                pairs_expand+=1
print("II blocks total:", sum(nb.values()))
print("II blocks by (s1,s2):", dict(sorted(nb.items())))
print("II blocks needing per-pair expansion (|am|<4):", pairs_expand)
# 每个 II 块的 (X1,X2) 对数（=单元数）
tot_units=0; mx=0
for W,blocks in CLS.items():
    for b in blocks:
        if b[0]=='II' and sum(b[5])<4:
            _,x1=T['PROFII_D'][(b[1][0],b[1][1],b[1][2])]
            _,x2=T['PROFII_D'][(b[2][0],b[2][1],b[2][2])]
            n=len(x1)*len(x2); tot_units+=n; mx=max(mx,n)
print("II per-pair units total:", tot_units, "max per block:", mx)
# 编码规模估算：每单元若用 (类索引, X1 索引, X2 索引) 三数 -> 约 3 字节紧凑
print("raw compact size estimate MB:", round(tot_units*3/1e6,1))
