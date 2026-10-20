# -*- coding: utf-8 -*-
"""诊断: 清一色胜牌/听牌数的独立交叉核对 (两条完全不同路径)"""
import itertools, time
from functools import lru_cache
T0=time.time()
@lru_cache(maxsize=None)
def melds_only(c):
    n=len(c); i=0
    while i<n and c[i]==0: i+=1
    if i==n: return 0
    best=None
    if c[i]>=3:
        c2=list(c); c2[i]-=3
        r=melds_only(tuple(c2))
        if r is not None: best=r+1
    if i+2<n and c[i+1]>0 and c[i+2]>0:
        c2=list(c); c2[i]-=1;c2[i+1]-=1;c2[i+2]-=1
        r=melds_only(tuple(c2))
        if r is not None and (best is None or r+1<best): best=r+1
    return best
def is_std_win9(c):
    for i in range(9):
        if c[i]>=2:
            c2=list(c); c2[i]-=2
            if melds_only(tuple(c2))==4: return True
    return False

# 路径 A: 枚举全部 14 张 9-向量 (cap4), 直接判胜
winA=set()
for c in itertools.product(range(5),repeat=9):
    if sum(c)==14 and is_std_win9(c): winA.add(c)
print("A) 14 张清一色胜牌(4面子+雀头) =", len(winA), " t=%.1f"%(time.time()-T0), flush=True)

# 路径 B: 枚举 4 个面子的多重集 (含重复起步的顺子), 再加雀头
melds=[]
for i in range(9):
    v=[0]*9; v[i]=3; melds.append(tuple(v))
for i in range(7):
    v=[0]*9; v[i]=1; v[i+1]=1; v[i+2]=1; melds.append(tuple(v))
winB=set()
for combo in itertools.combinations_with_replacement(range(len(melds)),4):
    v=[0]*9
    for m in combo:
        for i in range(9): v[i]+=melds[m][i]
    if any(x>4 for x in v): continue
    for p in range(9):
        if v[p]+2<=4:
            w=list(v); w[p]+=2
            winB.add(tuple(w))
print("B) 14 张清一色胜牌(面子组合+雀头) =", len(winB), " t=%.1f"%(time.time()-T0), flush=True)
print("   A == B ?", winA==winB)
if winA!=winB:
    print("   |A-B| =", len(winA-winB), " |B-A| =", len(winB-winA))
    print("   示例 A-B:", sorted(winA-winB)[:3])
    print("   示例 B-A:", sorted(winB-winA)[:3])

# 路径 A 生成听牌, 路径 B 生成听牌, 并直接枚举 13 向量验证
tpA=set()
for w in winA:
    for t in range(9):
        if w[t]>0:
            h=list(w); h[t]-=1; tpA.add(tuple(h))
tpB=set()
for w in winB:
    for t in range(9):
        if w[t]>0:
            h=list(w); h[t]-=1; tpB.add(tuple(h))
tpDirect=set()
for c in itertools.product(range(5),repeat=9):
    if sum(c)!=13: continue
    ok=False
    for t in range(9):
        if c[t]<4:
            d=list(c); d[t]+=1
            if is_std_win9(d): ok=True; break
    if ok: tpDirect.add(c)
print("听牌手牌: 由A删牌=%d, 由B删牌=%d, 直接判=%d" % (len(tpA),len(tpB),len(tpDirect)), flush=True)
print("   tpA==tpDirect ?", tpA==tpDirect, " tpB==tpDirect ?", tpB==tpDirect)

# 七对子听牌 (清一色内): 6 对 + 1 单张
chi=set()
for single in range(9):
    for pairs in itertools.combinations([i for i in range(9) if i!=single],6):
        c=[0]*9
        for p in pairs: c[p]=2
        c[single]=1
        chi.add(tuple(c))
# 七对子胜牌 (14 张 7 对)
chiwin=set()
for combo in itertools.combinations(range(9),7):
    c=[0]*9
    for p in combo: c[p]=2
    chiwin.add(tuple(c))
print("七对子: 14张胜牌=%d, 13张听牌(6对+1单)=%d" % (len(chiwin), len(chi)), flush=True)
print("七对子听牌中不是标准听牌的 =", len(chi-tpDirect), " 其中标准听牌 =", len(chi&tpDirect), flush=True)
# 标准听牌中不是七对子听牌的 = 总数
print("清一色听牌总数(标准)  =", len(tpDirect), flush=True)
print("清一色听牌总数(标准∪七对) =", len(tpDirect|chi), flush=True)
