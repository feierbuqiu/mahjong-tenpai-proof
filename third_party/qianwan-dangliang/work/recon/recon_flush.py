
import itertools, json, time
from functools import lru_cache

# ---------- tile model: 0-8 m1-9, 9-17 p1-9, 18-26 s1-9, 27-33 z1-7
def tiles(cat, n=9):
    base = cat*9 if cat < 3 else 27
    return base, n

def win_check_suit(cnt, need_melds):
    # cnt: tuple of 9 counts; can it be split into need_melds melds + 0/1 pair? returns pair index or None
    # try each pair position
    for pi in range(9):
        if cnt[pi] >= 2:
            c = list(cnt); c[pi] -= 2
            if _melds_only(c) == need_melds:
                return pi
    return None

def _melds_only(c, memo={}):
    key = tuple(c)
    if key in memo: return memo[key]
    # count of melds to clear c
    i = 0
    while i < len(c) and c[i] == 0: i += 1
    if i == len(c):
        memo[key] = 0; return 0
    best = None
    # triplet
    if c[i] >= 3:
        c2 = list(c); c2[i] -= 3
        r = _melds_only(c2)
        if r is not None: best = r+1
    # run
    if i+2 < len(c) and c[i+1] > 0 and c[i+2] > 0:
        c2 = list(c); c2[i]-=1; c2[i+1]-=1; c2[i+2]-=1
        r = _melds_only(c2)
        if r is not None:
            best = r+1 if best is None else min(best, r+1)
    memo[key] = best
    return best

# flush winning hands: 4 melds + pair in one 9-tile suit (allow up to 4 copies)
win = set()
def gen_run_vecs(n, k):
    # all multisets of k melds (runs/triplets) in n tiles -> count vectors
    res=set(); zero=tuple([0]*n)
    def rec(pos, remaining, vec):
        if remaining == 0:
            res.add(vec); return
        if pos >= n: return
        for take_trip in (1,):
            if vec[pos] <= 1:
                v=list(vec); v[pos]+=3
                if max(v)<=4: rec(pos+1, remaining-1, tuple(v))
        if pos+2 < n:
            v=list(vec)
            if v[pos]<4 and v[pos+1]<4 and v[pos+2]<4:
                v[pos]+=1; v[pos+1]+=1; v[pos+2]+=1
                rec(pos+1, remaining-1, tuple(v))
        rec(pos+1, remaining, vec)
    rec(0, k, zero)
    return res
R4 = gen_run_vecs(9,4)
print("run vecs for 4 melds:", len(R4), flush=True)
for v in R4:
    for pi in range(9):
        if v[pi]+2 <= 4:
            w=list(v); w[pi]+=2
            win.add(tuple(w))
print("flush winning 14-hands:", len(win), flush=True)

# flush tenpai hands: remove one tile from a winning hand
tenpai = {}
for w in win:
    for i in range(9):
        if w[i] > 0:
            h = list(w); h[i] -= 1
            tenpai[tuple(h)] = True
print("flush tenpai 13-hands:", len(tenpai), flush=True)

def waits_flush(h):
    res=[]
    for t in range(9):
        if h[t] < 4:
            w=list(h); w[t]+=1
            # winning iff exists pair pi with _melds_only(cnt-pair)==4, or 7 pairs impossible (13)
            for pi in range(9):
                if w[pi]>=2:
                    c=list(w); c[pi]-=2
                    if _melds_only(c)==4:
                        res.append(t); break
    return tuple(res)

cls = {}
for h in tenpai:
    W = waits_flush(h)
    cls.setdefault(W, []).append(h)
print("flush classes (distinct wait sets):", len(cls), flush=True)
sizes = sorted((len(v) for v in cls.values()), reverse=True)
print("class size: max %d min %d; top10 %s" % (sizes[0], sizes[-1], sizes[:10]), flush=True)

# k=2 / k=3 / k=4 common-code analysis (codes = ordered tuples of distinct tiles present with multiplicity)
def code_set(h, k):
    # all ordered k-tuples whose multiset is a sub-multiset of h
    tiles_present = []
    for i,c in enumerate(h):
        tiles_present += [i]*c
    out=set()
    seen=set()
    for combo in itertools.combinations_with_replacement(range(9), k):
        ok=True
        need={}
        for x in combo: need[x]=need.get(x,0)+1
        for x,n in need.items():
            if h[x] < n: ok=False; break
        if not ok: continue
        # permutations
        for p in set(itertools.permutations(combo)):
            out.add(p)
    return out

for k in (1,2,3,4):
    total=0; no_common=0
    for W, hs in cls.items():
        common=None
        if k<=3:
            cs = code_set(hs[0], k)
            for h in hs[1:]:
                cs &= code_set(h, k)
            common = len(cs)
        else:
            common = -1
        if k<=3:
            if common==0: no_common+=1
    print("k=%d: classes=%d, classes_without_common_code=%s" % (k, len(cls), no_common), flush=True)

# also: number of distinct capped profiles (information of k=3 code space) per class
for k in (1,2,3):
    sig = {}
    for W, hs in cls.items():
        s = frozenset(tuple(min(c,k) for c in h) for h in hs)
        sig.setdefault(s, []).append(W)
    shared = sum(1 for s,ws in sig.items() if len(ws)>1)
    print("k=%d distinct profiles=%d profiles shared by >1 class=%d" % (k, len(sig), shared), flush=True)
json.dump({"flush_classes":len(cls), "flush_tenpai":len(tenpai)}, open(r"D:\DSH\MJ2\work\recon\flush.json","w"))
