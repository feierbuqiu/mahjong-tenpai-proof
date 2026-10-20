
import sys
from collections import Counter, defaultdict
sys.path.insert(0, "work/verify")
from indep_core import compute_W, is_win_std_fast, gen_vectors
from itertools import combinations_with_replacement as cwr

melds9 = []
for i in range(7): melds9.append(tuple([1 if j in (i,i+1,i+2) else 0 for j in range(9)]))
for i in range(9):
    t=[0]*9; t[i]=3; melds9.append(tuple(t))
wins = set()
for combo in cwr(range(len(melds9)), 4):
    c=[0]*9
    for idx in combo:
        for j in range(9): c[j]+=melds9[idx][j]
    if max(c)>4: continue
    for p in range(9):
        cc=list(c); cc[p]+=2
        if cc[p]<=4: wins.add(tuple(cc))
nchi=0
for combo in cwr(range(9),7):
    c=[0]*9
    for i in combo: c[i]=2
    if tuple(c) not in wins: nchi+=1
    wins.add(tuple(c))
print("wins(melds+pair+chiitoi):", len(wins), " chiitoi-only added:", nchi)

direct_std=0; direct_chi=0
for v in gen_vectors(9,14):
    c=list(v)
    if is_win_std_fast(c): direct_std+=1
    elif sum(1 for x in c if x==2)==7: direct_chi+=1
print("direct: std wins", direct_std, "chiitoi-only", direct_chi, "sum", direct_std+direct_chi)
print("enum - direct =", len(wins)-(direct_std+direct_chi))

Wmap = defaultdict(set)
for w14 in wins:
    for t in range(9):
        if w14[t]>0:
            h=list(w14); h[t]-=1
            Wmap[tuple(h)].add(t)
print("listening hands (win-minus-one):", len(Wmap))
missing=0
examples=[]
for h,W in Wmap.items():
    c=list(h)+[0]*25
    W2=compute_W(c)
    if set(W)!=set(W2):
        missing+=1
        if len(examples)<8: examples.append((h,sorted(W),sorted(W2)))
for e in examples: print("DIFF", e)
print("hands where win-minus-one W != compute_W:", missing)
extra=0
ex2=[]
for h in gen_vectors(9,13):
    c=list(h)+[0]*25
    W2=compute_W(c)
    if W2 and tuple(h) not in Wmap:
        extra+=1
        if len(ex2)<8: ex2.append((h,sorted(W2),sorted(Wmap.get(tuple(h),[]))))
for e in ex2: print("compute_W-only", e)
print("compute_W listening hands:", sum(1 for h in gen_vectors(9,13) if compute_W(list(h)+[0]*25)))
