
import json, time, itertools
from functools import lru_cache

def ncat(c): return 9 if c < 3 else 7
def gidx(c, i): return c*9+i if c < 3 else 27+i

_memo = {}
def melds_only(c):
    k = tuple(c)
    r = _memo.get(k)
    if r is not None: return r
    n = len(k); i = 0
    while i < n and k[i] == 0: i += 1
    if i == n:
        _memo[k] = True; return True
    res = False
    if k[i] >= 3:
        l = list(k); l[i] -= 3
        if melds_only(tuple(l)): res = True
    if not res and i+2 < n and k[i+1] > 0 and k[i+2] > 0:
        l = list(k); l[i] -= 1; l[i+1] -= 1; l[i+2] -= 1
        if melds_only(tuple(l)): res = True
    _memo[k] = res
    return res

def melds_pair(c):
    for j in range(len(c)):
        if c[j] >= 2:
            l = list(c); l[j] -= 2
            if melds_only(tuple(l)): return True
    return False

def gen(size, n, cap=4):
    cur = [0]*n
    def rec(i, rem):
        if i == n-1:
            if rem <= cap:
                cur[i] = rem; yield tuple(cur); cur[i] = 0
            return
        for v in range(min(cap, rem)+1):
            cur[i] = v
            yield from rec(i+1, rem-v)
        cur[i] = 0
    yield from rec(0, size)

t0 = time.time()
SIZES_I  = (1,4,7,10,13)
SIZES_II = (2,5,8,11)

# per-category signatures
catI = {}   # c -> set of (Wp_frozen_local, odd_count, odd_tile or -1, size)
catII = {}  # c -> set of (V_frozen_local, pd, odd_count, odd_tile or -1, size)
for c in range(4):
    n = ncat(c)
    SI = set(); SII = set()
    for size in SIZES_I:
        for X in gen(size, n):
            Wp = 0
            for t in range(n):
                if X[t] < 4:
                    l = list(X); l[t] += 1
                    if melds_pair(l): Wp |= 1 << t
            odd_tiles = [i for i,v in enumerate(X) if v % 2 == 1]
            if Wp or (size == 13 and len(odd_tiles) == 1) or (size == 10 and not odd_tiles):
                SI.add((Wp, len(odd_tiles), odd_tiles[0] if len(odd_tiles)==1 else -1, size))
    for size in SIZES_II:
        for X in gen(size, n):
            V = 0
            for t in range(n):
                if X[t] < 4:
                    l = list(X); l[t] += 1
                    if melds_only(l): V |= 1 << t
            pd = melds_pair(X)
            odd_tiles = [i for i,v in enumerate(X) if v % 2 == 1]
            SII.add((V, pd, len(odd_tiles), odd_tiles[0] if len(odd_tiles)==1 else -1, size))
    catI[c] = SI; catII[c] = SII
    print("cat %d: |sigI|=%d |sigII|=%d  t=%.1fs" % (c, len(SI), len(SII), time.time()-t0), flush=True)

CLASS = set()
def gset(c, mask):
    return frozenset(gidx(c,i) for i in range(ncat(c)) if (mask >> i) & 1)

# Type I
nI = 0
for c in range(4):
    for (Wp, oddn, oddt, size) in catI[c]:
        if Wp:
            CLASS.add(gset(c, Wp)); nI += 1
        if size == 13 and oddn == 1:
            CLASS.add(gset(c, Wp) | {gidx(c, oddt)})
        if size == 10 and oddn == 0:
            for c2 in range(4):
                if c2 == c: continue
                for i in range(ncat(c2)):
                    CLASS.add(gset(c, Wp) | {gidx(c2, i)})
print("after Type I: |CLASS|=%d  t=%.1fs" % (len(CLASS), time.time()-t0), flush=True)

# Type II
pairs = [(a,b) for a in range(4) for b in range(a+1,4)]
for (c1,c2) in pairs:
    for (V1, pd1, o1n, o1t, s1) in catII[c1]:
        for (V2, pd2, o2n, o2t, s2) in catII[c2]:
            Wstd = 0
            if pd1: Wstd |= V2
            if pd2: Wstd |= V1
            base = gset(c1, 0)
            if Wstd:
                CLASS.add(gset(c1, Wstd & ((1<<ncat(c1))-1)) | gset(c2, Wstd >> ncat(c1)))
            tot = s1 + s2
            if tot == 13 and o1n + o2n == 1:
                z = gidx(c1, o1t) if o1n == 1 else gidx(c2, o2t)
                Wf = gset(c1, Wstd & ((1<<ncat(c1))-1)) | gset(c2, Wstd >> ncat(c1))
                CLASS.add(Wf | {z})
            elif tot == 10 and o1n == 0 and o2n == 0:
                Wf = gset(c1, Wstd & ((1<<ncat(c1))-1)) | gset(c2, Wstd >> ncat(c1))
                for c3 in range(4):
                    if c3 in (c1,c2): continue
                    for i in range(ncat(c3)):
                        CLASS.add(Wf | {gidx(c3,i)})
    print("pair (%d,%d) done |CLASS|=%d t=%.1fs" % (c1,c2,len(CLASS), time.time()-t0), flush=True)

# singletons (chiitoi-only) + kokushi
for z in range(34): CLASS.add(frozenset({z}))
term = [0,8,9,17,18,26] + list(range(27,34))
CLASS.add(frozenset(term))
print("GLOBAL CLASSES =", len(CLASS), flush=True)
sizes = {}
for w in CLASS: sizes[len(w)] = sizes.get(len(w),0)+1
print("by |W|:", dict(sorted(sizes.items())), flush=True)
json.dump({"n_classes": len(CLASS), "by_size": {str(k):v for k,v in sizes.items()}},
          open(r"D:\DSH\MJ2\work\recon\global_classes.json","w"))
print("t=%.1fs" % (time.time()-t0))
