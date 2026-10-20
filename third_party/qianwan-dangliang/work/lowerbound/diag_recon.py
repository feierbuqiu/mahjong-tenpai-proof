# -*- coding: utf-8 -*-
"""诊断 recon_counts.py 的全局标准型胜牌枚举, 以及 MODEL.md 七对子判据的正确性"""
import itertools
from functools import lru_cache

# ---------- 1) 复刻 recon_counts.py 的标准型枚举 (放在我自己的目录里跑) ----------
def suit_melds(n=9):
    zero=tuple([0]*n); layers=[{zero}]; cur={zero}
    for k in range(4):
        nxt=set()
        for v in cur:
            for i in range(n-2):
                if v[i]<4 and v[i+1]<4 and v[i+2]<4:
                    w=list(v); w[i]+=1; w[i+1]+=1; w[i+2]+=1; nxt.add(tuple(w))
            for i in range(n):
                if v[i]<=1:
                    w=list(v); w[i]+=3; nxt.add(tuple(w))
        layers.append(nxt); cur=nxt
    return layers
L=suit_melds(9); H=suit_melds(7)
SP=[tuple(1 if i==j else 0 for i in range(9)) for j in range(9)]
HP=[tuple(1 if i==j else 0 for i in range(7)) for j in range(7)]
cats=[('s',L,SP),('s',L,SP),('s',L,SP),('h',H,HP)]
def vec_to_tiles(vec, base):
    out=[]
    for i,c in enumerate(vec): out += [base+i]*c
    return out
winning=set()
for kdist in itertools.product(range(5),repeat=4):
    if sum(kdist)!=4: continue
    for paircat in range(4):
        opts=[cats[c][1][kdist[c]] for c in range(4)]
        for combo in itertools.product(*opts):
            for pv in cats[paircat][2]:
                vecs=[]; ok=True
                for c in range(4):
                    v=list(combo[c])
                    if c==paircat:
                        for i in range(len(v)): v[i]+=pv[i]
                        if any(x>4 for x in v): ok=False; break
                    vecs.append(tuple(v))
                if not ok: continue
                full=[]
                for c in range(4):
                    base=c*9 if c<3 else 27
                    full += vec_to_tiles(vecs[c],base)
                if len(full)!=14: continue
                winning.add(tuple(sorted(full)))
print("复刻 recon_counts 标准型 14 张胜牌数 =", len(winning))
print("  C(34,7) =", __import__('math').comb(34,7), " C(34,7)+13 =", __import__('math').comb(34,7)+13)
print("  recon counts.json 的 n_winning = 5379629  -> 说明其标准型部分贡献了 %d 手" % (5379629-__import__('math').comb(34,7)-13))

# ---------- 2) 七对子判据 ----------
def chiitoi_win(cnt):
    np_=0
    for x in cnt:
        if x==0: continue
        if x!=2: return False
        np_+=1
    return np_==7
def odd_kinds(cnt): return [i for i,x in enumerate(cnt) if x%2==1]

def mk(pairs, extra):
    c=[0]*34
    for p in pairs: c[p]+=2
    for e in extra: c[e]+=1
    assert sum(c)==13
    return c
def mk_raw(spec):
    c=[0]*34
    for t,n in spec: c[t]+=n
    assert sum(c)==13
    return c
# 反例 A: 刻子(计数3) + 5 对 -> 恰一种奇数牌, 但加它不成七对
A=mk([9,10,11,12,13],[0,0,0])
print("\n反例A: m1x3 + p1..p5 各一对 =", sum(A), "张, 奇数牌种 =", odd_kinds(A))
A2=list(A); A2[0]+=1
print("  A+m1 是七对子?", chiitoi_win(A2), " (m1 计数变为 %d)" % A2[0])
# 反例 B: 计数4 + 单张(计数1) -> 恰一种奇数牌, 但加它不成七对
B=mk_raw([(0,4),(9,2),(10,2),(11,2),(12,2),(18,1)])   # m1x4 + p1..p4 各一对 + s1
print("反例B: m1x4 + p1..p4 各一对 + s1 =", sum(B), "张, 奇数牌种 =", odd_kinds(B))
B2=list(B); B2[18]+=1
print("  B+s1 是七对子?", chiitoi_win(B2))
# 正确判据
print("\n正确判据: 13 张手牌 H 是七对子听牌  <=>  H 恰为 6 个对子 + 1 张单牌")
print("  即: 全部非零计数都等于 2, 除恰一种计数等于 1; 14 张和牌 = 7 个不同对子")
# 计数: 七对子听牌手牌总数
import math
print("  七对子听牌 13 张手牌数 = 34 * C(33,6) =", 34*math.comb(33,6))
print("  七对子和牌 14 张手牌数 = C(34,7) =", math.comb(34,7))
print("\nMODEL.md 第 6 节 n_winning=%d = C(34,7)+13 ; n_tenpai=%d" % (5379629, 37657469))
print("  => recon_counts 的 '标准型' 枚举贡献 0 手; counts.json 的 n_tenpai 只是七对子+国士的听牌手牌, 不含任何标准型听牌手牌。")
print("  校验: 34*C(33,6) =", 34*math.comb(33,6), " ; n_tenpai - 34*C(33,6) =", 37657469-34*math.comb(33,6))
