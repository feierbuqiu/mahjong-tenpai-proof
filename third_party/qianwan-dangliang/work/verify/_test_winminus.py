
import sys, itertools
from collections import defaultdict
sys.path.insert(0, "work/verify")
from indep_core import compute_W, gen_vectors, melds_only, CAP

# ---- independent path: enumerate 14-tile one-suit winning hands, subtract one tile ----
melds9 = []
for i in range(9): melds9.append(tuple([1 if j in (i,i+1,i+2) else 0 for j in range(9)]))  # runs
for i in range(9): 
    t = [0]*9; t[i] = 3; melds9.append(tuple(t))  # triplets
melds9 = [m for m in melds9 if sum(m)==3]

wins = set()
from itertools import combinations_with_replacement as cwr
for combo in cwr(range(len(melds9)), 4):
    c = [0]*9
    for idx in combo:
        for j in range(9): c[j] += melds9[idx][j]
    if max(c) > 4: continue
    for p in range(9):
        cc = list(c); cc[p] += 2
        if cc[p] <= 4:
            wins.add(tuple(cc))
# chiitoi strict in one suit
for combo in cwr(range(9), 7):
    c = [0]*9
    for i in combo: c[i] = 2
    wins.add(tuple(c))
print("one-suit 14-tile winning hands:", len(wins))

Wmap = defaultdict(set)
for w14 in wins:
    for t in range(9):
        if w14[t] > 0:
            h = list(w14); h[t] -= 1
            Wmap[tuple(h)].add(t)
print("distinct one-suit 13-tile listening hands (win-minus-one):", len(Wmap))

# compare with compute_W
mismatch = 0
for h, W in Wmap.items():
    c = list(h) + [0]*25
    W2 = compute_W(c)
    if set(W) != set(W2):
        mismatch += 1
        if mismatch <= 5: print("MISMATCH", h, sorted(W), sorted(W2))
# also all 93600 hands: are compute_W-empty hands really not listening?
allv = list(gen_vectors(9,13))
print("all one-suit 13-tile multisets:", len(allv))
extra = 0
for h in allv:
    c = list(h) + [0]*25
    W2 = compute_W(c)
    if W2 and tuple(h) not in Wmap:
        extra += 1
        if extra <= 5: print("compute_W says listening but not reachable:", h, sorted(W2))
print("mismatches:", mismatch, " compute_W-only listening hands:", extra)
# W histogram from win-minus-one
from collections import Counter
print("W size hist:", sorted(Counter(len(v) for v in Wmap.values()).items()))
