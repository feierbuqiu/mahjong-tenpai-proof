
import sys
from collections import Counter, defaultdict
from itertools import combinations
sys.path.insert(0, "work/verify")
from indep_core import compute_W, is_win_std_fast, is_win_chiitoi_strict, gen_vectors, is_win_full

# strict chiitoi-listening one-suit 13-tile hands
chi = set()
for combo in combinations(range(9),7):
    for s in combo:
        c=[0]*9
        for i in combo: c[i]=2
        c[s]=1
        chi.add(tuple(c))
print("strict chiitoi-listening one-suit hands:", len(chi))
# for each, is there a standard listening tile?
chi_only=[]; chi_std=[]
for h in chi:
    std=False
    for t in range(9):
        if h[t]>=4: continue
        c=list(h)+[0]*25; c[t]+=1
        if is_win_std_fast(c): std=True; break
    (chi_std if std else chi_only).append(h)
print("chiitoi+standard:", len(chi_std), " chiitoi-ONLY (W_std empty):", len(chi_only))

# full flush W with/without chiitoi in W
def flush_sets(include_chi):
    hands=set(); classes=defaultdict(list)
    for h in gen_vectors(9,13):
        c=list(h)+[0]*25
        W=set()
        for t in range(9):
            if c[t]>=4: continue
            c[t]+=1
            win = is_win_std_fast(c) or (include_chi and is_win_chiitoi_strict(c))
            c[t]-=1
            if win: W.add(t)
        if W:
            hands.add(h); classes[frozenset(W)].append(h)
    return hands, classes
for inc in (True, False):
    hands, classes = flush_sets(inc)
    nc={}
    for k in (1,2,3,4):
        nc[k]=sum(1 for W,hs in classes.items() if sum(min(x[t] for x in hs) for t in range(9))<k)
    print("include_chiitoi=",inc," hands=",len(hands)," classes=",len(classes)," no_common=",nc)
# where do chi_only hands' W live? W is a singleton {t}
Wc = Counter()
for h in chi_only:
    W=compute_W(list(h)+[0]*25)
    Wc[tuple(sorted(W))]+=1
print("chi_only W distribution:", Wc.most_common(12))
