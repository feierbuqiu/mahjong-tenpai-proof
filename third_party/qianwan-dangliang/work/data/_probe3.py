# -*- coding: utf-8 -*-
"""_probe3.py -- randomized + targeted brute-force cross-check of mjcore.waits."""
import sys, time, random, itertools
sys.path.insert(0, r"D:\DSH\MJ2\work\data")
import mjcore as M

def ok_melds_suit(c):
    def rec(c, i):
        while i < 9 and c[i] == 0: i += 1
        if i == 9: return True
        if c[i] >= 3:
            c[i]-=3
            if rec(c,i): c[i]+=3; return True
            c[i]+=3
        if i <= 6 and c[i+1] >= 1 and c[i+2] >= 1:
            c[i]-=1;c[i+1]-=1;c[i+2]-=1
            if rec(c,i): c[i]+=1;c[i+1]+=1;c[i+2]+=1; return True
            c[i]+=1;c[i+1]+=1;c[i+2]+=1
        return False
    return rec(list(c),0)

def ok_melds(c, v):
    if c < 3: return ok_melds_suit(v)
    return all(x % 3 == 0 for x in v)

def brute_win(cnt):
    if sum(cnt) != 14: return False
    vs = [cnt[0:9], cnt[9:18], cnt[18:27], cnt[27:34]]
    # standard
    for pc in range(4):
        v = list(vs[pc]); done = False
        for p in range(len(v)):
            if v[p] >= 2:
                w = list(v); w[p] -= 2
                if ok_melds(pc, w): done = True; break
        if done and all(ok_melds(c, vs[c]) for c in range(4) if c != pc):
            return True
    # chiitoi: 7 distinct types x2
    if all(x == 0 or x == 2 for x in cnt) and sum(1 for x in cnt if x == 2) == 7:
        return True
    # kokushi
    present = 0
    for i, x in enumerate(cnt):
        if x: present |= 1 << i
    if present == M.KOKUSHI_MASK: return True
    return False

def brute_waits(cnt):
    res = 0
    for t in range(34):
        if cnt[t] >= 4: continue
        w = list(cnt); w[t] += 1
        if brute_win(w): res |= 1 << t
    return res

def rand_hand(rng, mode="uniform"):
    while True:
        cnt = [0]*34
        if mode == "uniform":
            for _ in range(13):
                cnt[rng.randrange(34)] += 1
        elif mode == "cluster":
            base = rng.randrange(34)
            for _ in range(13):
                t = min(33, max(0, base + rng.randrange(-3,4)))
                cnt[t] += 1
        elif mode == "pairs":
            for _ in range(6):
                cnt[rng.randrange(34)] += 2
            cnt[rng.randrange(34)] += 1
        elif mode == "triples":
            for _ in range(4):
                cnt[rng.randrange(34)] += 3
            cnt[rng.randrange(34)] += 1
        if max(cnt) <= 4 and sum(cnt) == 13:
            return tuple(cnt)

rng = random.Random(12345)
bad = 0; n = 0; t0 = time.time()
cases = []
for mode in ("uniform","cluster","pairs","triples"):
    for _ in range(6000):
        cases.append(rand_hand(rng, mode))
# all kokushi-shaped 13 hands
TH = M.TERMINAL_HONOR
for combo in itertools.combinations(TH, 12):
    for i in combo:
        c = [0]*34
        for t in combo: c[t] += 1
        c[i] += 1
        cases.append(tuple(c))
c = [0]*34
for t in TH: c[t] += 1
cases.append(tuple(c))
for h in cases:
    n += 1
    a = M.waits(h); b = brute_waits(list(h))
    if a != b:
        bad += 1
        if bad <= 10:
            print("MISMATCH", h, M.mask_names(a), M.mask_names(b))
print("cross-check: %d hands, %d mismatches (%.1fs)" % (n, bad, time.time()-t0))

# flush full enumeration re-check
def multisets(n_types, size, cap=4):
    for cc in itertools.combinations_with_replacement(range(n_types), size):
        v = [0]*n_types
        for x in cc: v[x]+=1
        if max(v) <= cap: yield tuple(v)
bad2 = 0
for v in multisets(9,13):
    a = M.waits_vecs((v,(0,)*9,(0,)*9,(0,)*7))
    b = brute_waits(list(v)+[0]*25)
    if a != b: bad2 += 1
print("flush full check mismatches:", bad2)
