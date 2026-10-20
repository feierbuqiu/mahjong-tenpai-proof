# -*- coding: utf-8 -*-
import random
random.seed(20260917)
HON=[27,28,29,30,31,32,33]
out=[]
def emit(v):
    out.append(list(v))
# 1) uniform random 13 tiles
for _ in range(800):
    v=[0]*34
    for _ in range(13):
        while True:
            t=random.randrange(34)
            if v[t]<4:
                v[t]+=1
                break
    emit(v)
# 2) random winning shape minus one tile (tenpai)
def rand_win14():
    melds=[]
    while len(melds)<4:
        if random.random()<0.5:
            t=random.randrange(34)
            m=[0]*34
            m[t]=3
        else:
            c=random.randrange(3)
            s=random.randrange(7)
            off=c*9+s
            m=[0]*34
            m[off]+=1; m[off+1]+=1; m[off+2]+=1
        melds.append(m)
    t=random.randrange(34)
    p=[0]*34
    p[t]=2
    v=[0]*34
    allm=melds+[p]
    for m in allm:
        for i in range(34):
            v[i]+=m[i]
    if max(v)>4:
        return None
    return v
n=0
while n<700:
    v=rand_win14()
    if v is None:
        continue
    tiles=[t for t,c in enumerate(v) for _ in range(c)]
    t=random.choice(tiles)
    v[t]-=1
    emit(v)
    n+=1
# 3) kokushi tenpai
KOK=[0,8,9,17,18,26]+HON
base=[0]*34
for t in KOK:
    base[t]=1
emit(base)
for miss in KOK:
    for dup in KOK:
        if dup==miss:
            continue
        w=list(base)
        w[miss]=0
        w[dup]+=1
        emit(w)
# 4) chiitoi tenpai (6 pairs + 1 single)
for _ in range(300):
    ts=random.sample(range(34),7)
    v=[0]*34
    for t in ts[:6]:
        v[t]=2
    v[ts[6]]=1
    emit(v)
with open('work/lean_hand_input.txt','w',encoding='utf-8') as f:
    for v in out:
        f.write(','.join(str(x) for x in v)+chr(10))
print('wrote', len(out), 'hands')
