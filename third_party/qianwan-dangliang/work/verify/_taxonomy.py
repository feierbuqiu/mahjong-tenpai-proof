
import json, sys
from collections import Counter, defaultdict
sys.path.insert(0, "work/verify")
import census as C

mine = [frozenset(x) for x in json.load(open("work/verify/census_strict.json", encoding="utf-8"))]
def ncat(W): return len(set(0 if t < 9 else 1 if t < 18 else 2 if t < 27 else 3 for t in W))
d = Counter(ncat(W) for W in mine)
print("classes by #categories of W:", dict(sorted(d.items())), "total", len(mine))

uni = C.Uni((9, 9, 9, 7), cat_is_honor=[False, False, False, True], kokushi=True)
std = uni.std_census()
strict_all = uni.strict_census()
chi_sources = strict_all - std           # 只由七对子附加产生的 W
print("std classes", len(std), " strict(raw)", len(strict_all))
print("chiitoi-only-new W values:", len(chi_sources))

# 逐类统计"是否含七对子来源": 重跑 strict 的附加枚举, 记录每个 W 是否来自七对子手
Kc = uni.cat_kinds
chiW = set(); kokW = {frozenset(C.KOKUSHI_IDX)}
import itertools
for z in range(uni.nkinds):
    zc = uni.cat_of(z); lz = z - uni.offs[zc]
    for ks in itertools.product(*[range(0, Kc[c]+1) for c in range(uni.nc)]):
        if sum(ks) != 7 or ks[zc] < 1: continue
        tot = [2*ks[c] - (1 if c == zc else 0) for c in range(uni.nc)]
        if any(t < 0 for t in tot) or sum(tot) != 13: continue
        r = [t % 3 for t in tot]
        n1 = sum(1 for x in r if x == 1); n2 = sum(1 for x in r if x == 2)
        if n1 == 1 and n2 == 0:
            ci = r.index(1)
            if ci != zc: continue
            lazy = [c for c in range(uni.nc) if c != ci]
            if not all(uni.lazy_all2_exists(c, tot[c]) for c in lazy): continue
            for v in uni._act_vecs_z(ci, ks[ci], lz):
                chiW.add(uni._wp_of(v, ci) | {z})
        elif n1 == 0 and n2 == 2:
            act = [c for c in range(uni.nc) if r[c] == 2]
            lazy = [c for c in range(uni.nc) if r[c] == 0]
            ok = True
            for c in lazy:
                if c == zc:
                    if not uni.lazy_z_exists(c, tot[c], lz): ok = False; break
                else:
                    if not uni.lazy_all2_exists(c, tot[c]): ok = False; break
            if not ok: continue
            vl = [uni._act_vecs_z(c, ks[c], lz) if c == zc else uni._act_vecs_all2(c, ks[c]) for c in act]
            for v1 in vl[0]:
                for v2 in vl[1]:
                    chiW.add(uni._wstd2(v1, v2, act[0], act[1]) | {z})
print("classes with strict chiitoi source (W values from 6-pairs+1 hands):", len(chiW))
print("  subset of my census:", chiW <= set(mine))
# 子宇宙类
subu = {}
for name, K, off, hon in [("m",9,0,False),("p",9,9,False),("s",9,18,False),("z",7,27,True)]:
    u = C.Uni((K,), cat_is_honor=[hon])
    cls = set()
    for h in C.gen_vectors(K, 13):
        c = [0]*34
        for i,x in enumerate(h): c[off+i] = x
        from indep_core import compute_W
        W = compute_W(c)
        if W: cls.add(W)
    subu[name] = cls
    print("sub-universe", name, "classes:", len(cls))
allsub = set().union(*subu.values())
print("union of sub-universe classes:", len(allsub), " remaining:", len(mine) - len(allsub))
print("typeI(1 cat) == sub-universe classes:", set(W for W in mine if ncat(W) == 1) == allsub)
print("kokushi 13-set in census:", kokW <= set(mine))
