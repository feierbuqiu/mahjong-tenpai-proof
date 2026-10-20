
import sys
from collections import Counter, defaultdict
from itertools import combinations_with_replacement as cwr, combinations
sys.path.insert(0, "work/verify")
from indep_core import compute_W, is_win_std_fast, is_win_chiitoi_strict

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
n_chi_only = 0
for combo in combinations(range(9),7):
    c=[0]*9
    for i in combo: c[i]=2
    if tuple(c) not in wins: n_chi_only += 1
    wins.add(tuple(c))
print("wins(melds+pair+chiitoi):", len(wins), " distinct chiitoi-only added:", n_chi_only)

bad = 0
for w14 in wins:
    c = list(w14) + [0]*25
    if not (is_win_std_fast(c) or is_win_chiitoi_strict(c)):
        bad += 1
        if bad <= 5: print("NOT A WIN:", w14)
print("enum wins that fail independent win test:", bad)
# direct brute force over all sum-14 vectors
std = 0; chi_only = 0
for a in range(5):
 for b in range(5):
  for c_ in range(5):
   for d in range(5):
    for e in range(5):
     for f in range(5):
      for g in range(5):
       for h_ in range(5):
        for i_ in range(5):
         pass
import indep_core as ic
std = 0; chi_only = 0
for v in ic.gen_vectors(9,14):
    c = list(v)+[0]*25
    if is_win_std_fast(c): std += 1
    elif is_win_chiitoi_strict(c): chi_only += 1
print("direct: std wins", std, "chiitoi-only", chi_only, "total", std+chi_only, " vs enum", len(wins))

Wmap = defaultdict(set)
for w14 in wins:
    for t in range(9):
        if w14[t]>0:
            hands = list(w14); hands[t]-=1
            Wmap[tuple(hands)].add(t)
print("listening hands (win-minus-one):", len(Wmap))
missing=0; ex=[]
for hands,W in Wmap.items():
    W2=compute_W(list(hands)+[0]*25)
    if set(W)!=set(W2):
        missing+=1
        if len(ex)<8: ex.append((hands,sorted(W),sorted(W2)))
for x in ex: print("DIFF", x)
print("win-minus-one hands whose W != compute_W:", missing)
