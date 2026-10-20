
import sys, itertools
sys.path.insert(0, "work/verify")
from indep_core import melds_only, melds_pair, gen_vectors, is_win_std_fast, compute_W

# naive reference: first-nonzero recursion
def ref_melds_only(c):
    c = list(c)
    if all(x == 0 for x in c): return True
    i = next(i for i, x in enumerate(c) if x)
    if c[i] >= 3:
        c2 = list(c); c2[i] -= 3
        if ref_melds_only(c2): return True
    if i + 2 < len(c) and c[i+1] > 0 and c[i+2] > 0:
        c2 = list(c); c2[i] -= 1; c2[i+1] -= 1; c2[i+2] -= 1
        if ref_melds_only(c2): return True
    return False

bad = 0; cnt = 0
for n in range(0, 15):
    for v in gen_vectors(9, n):
        cnt += 1
        if bool(melds_only(v)) != bool(ref_melds_only(v)):
            bad += 1
            if bad < 6: print("MISMATCH melds_only", v, melds_only(v), ref_melds_only(v))
print("melds_only tested", cnt, "mismatches", bad)

# melds_pair reference
def ref_melds_pair(c):
    for j in range(len(c)):
        if c[j] >= 2:
            c2 = list(c); c2[j] -= 2
            if ref_melds_only(c2): return True
    return False
bad2 = 0; cnt2 = 0
for n in range(0, 15):
    for v in gen_vectors(9, n):
        cnt2 += 1
        if bool(melds_pair(v)) != bool(ref_melds_pair(v)):
            bad2 += 1
            if bad2 < 6: print("MISMATCH melds_pair", v, melds_pair(v), ref_melds_pair(v))
print("melds_pair tested", cnt2, "mismatches", bad2)

# honor category K=7 too
bad3 = 0; cnt3 = 0
for n in range(0, 15):
    for v in gen_vectors(7, n):
        cnt3 += 1
        if bool(melds_only(v)) != bool(ref_melds_only(v)):
            bad3 += 1
            if bad3 < 6: print("MISMATCH honor", v)
print("honor melds_only tested", cnt3, "mismatches", bad3)
