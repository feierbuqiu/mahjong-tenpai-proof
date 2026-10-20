# -*- coding: utf-8 -*-
import random
random.seed(777)
out=[]
HON=[27,28,29,30,31,32,33]
# 1) U7 全部手牌（m2..m8，7875）
def hands_in(tiles, tot):
    res=[]
    cur=[0]*len(tiles)
    def rec(i, rem):
        if i==len(tiles)-1:
            if rem<=4:
                v=[0]*34
                for j,t in enumerate(tiles): v[t]=cur[j]
                v[tiles[i]]=rem
                res.append(v)
            return
        for c in range(min(4,rem)+1):
            cur[i]=c
            rec(i+1, rem-c)
        cur[i]=0
    rec(0,tot)
    return res
out += hands_in([1,2,3,4,5,6,7],13)
# 2) 单花色随机 20000 手
allf = hands_in(list(range(9)),13)
print('flush total', len(allf))
out += random.sample(allf, 20000)
# 3) 混合：随机 3000 + 国士/七对听牌 2000
for _ in range(3000):
    v=[0]*34
    for _ in range(13):
        while True:
            t=random.randrange(34)
            if v[t]<4:
                v[t]+=1
                break
    out.append(v)
KOK=[0,8,9,17,18,26]+HON
for _ in range(500):
    w=[0]*34
    for t in KOK: w[t]=1
    miss=random.choice(KOK); dup=random.choice([t for t in KOK if t!=miss])
    w[miss]=0; w[dup]+=1
    out.append(w)
for _ in range(500):
    ts=random.sample(range(34),7)
    v=[0]*34
    for t in ts[:6]: v[t]=2
    v[ts[6]]=1
    out.append(v)
with open('work/lean_hand_input.txt','w',encoding='utf-8') as f:
    for v in out: f.write(','.join(str(x) for x in v)+chr(10))
print('wrote', len(out))
