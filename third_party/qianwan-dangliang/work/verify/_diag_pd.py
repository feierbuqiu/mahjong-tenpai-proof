
import sys, random
sys.path.insert(0, "work/verify")
from indep_core import compute_W, closed_form_W, melds_only, melds_pair, has_pair, gen_vectors, CAT_SLICES

# 1) random full-universe hands: brute-force W vs closed form
rnd = random.Random(7)
mism = 0; checked = 0; ex = []
for it in range(30000):
    c = [0]*34
    for _ in range(13):
        while True:
            t = rnd.randrange(34)
            if c[t] < 4: c[t] += 1; break
    Wb = compute_W(c)
    Wc = closed_form_W(c)
    checked += 1
    if Wb != Wc:
        mism += 1
        if len(ex) < 5: ex.append((c, sorted(Wb), sorted(Wc)))
print("random hands checked:", checked, "mismatch:", mism)
for e in ex: print("EX", e)

# 2) targeted: Type II with pd(X2) true but melds_pair(X2) false
hits = 0
found = []
from itertools import combinations
for n2 in (2,5,8,11):
    for X2 in gen_vectors(9, n2):
        if not has_pair(X2) or melds_pair(X2): continue
        for n1 in (2,5,8,11):
            m = 13-n1-n2
            if m < 0 or m % 3: continue
            for X1 in gen_vectors(9, n1):
                for t in range(9):
                    if X1[t] >= 4: continue
                    xx = list(X1); xx[t] += 1
                    if not melds_only(tuple(xx)): continue
                    # X2 as other active category in a real hand: need F decomposable size m
                    found.append((X1, t, X2, n1, n2, m))
                    hits += 1
                    break
                if found and len(found) >= 6: break
            if len(found) >= 6: break
        if len(found) >= 6: break
    if len(found) >= 6: break
print("pd-but-not-melds_pair Type II candidates found:", hits)
for (X1,t,X2,n1,n2,m) in found:
    # construct H: X1 in m-category(0), X2 in p-category(1), F = 4 melds in s-category (if m==12) etc.
    print("X1=",X1,"t=",t,"X2=",X2,"n1,n2,m=",n1,n2,m)
