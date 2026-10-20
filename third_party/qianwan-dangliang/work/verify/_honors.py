
import sys
sys.path.insert(0, "work/verify")
from census import Uni, brute_census, brute_chiitoi_census
uni = Uni((7,), cat_is_honor=[True])
for mode in ('strict', 'loose'):
    cen = uni.strict_census() if mode == 'strict' else uni.loose_census()
    _, only = brute_chiitoi_census(uni, mode)
    cen2 = set(cen) | {frozenset([z]) for z in only}
    bc, bh = brute_census(uni, mode)
    print("honors-only", mode, "sig", len(cen2), "brute", len(bc), "hands", bh,
          "missing", len(bc - cen2), "extra", len(cen2 - bc), flush=True)
