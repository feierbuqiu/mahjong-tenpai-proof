# -*- coding: utf-8 -*-
"""_probe13.py -- (1) elementwise-min of every filler family; (2) mincount criterion spot check."""
import sys, itertools, json
sys.path.insert(0, r"D:\DSH\MJ2\work\data")
import mjcore as M
from mjcore import CAT_LEN, CAT_BASE

# --- filler families
MELDS = {}
def melds_of(c):
    n=CAT_LEN[c]; ms=[]
    for i in range(n):
        v=[0]*n; v[i]=3; ms.append(tuple(v))
    if c<3:
        for i in range(n-2):
            v=[0]*n; v[i]=v[i+1]=v[i+2]=1; ms.append(tuple(v))
    return ms
MELDS={c:melds_of(c) for c in range(4)}

def fillers(S,j):
    if j==0:
        yield tuple(tuple([0]*CAT_LEN[c]) for c in range(4)); return
    seen=set()
    items=[(c,v) for c in sorted(S) for v in MELDS[c]]
    for combo in itertools.combinations_with_replacement(range(len(items)), j):
        per={}; ok=True
        for idx in combo:
            c,v=items[idx]
            d=per.get(c)
            if d is None: d=per[c]=[0]*CAT_LEN[c]
            for i,x in enumerate(v):
                d[i]+=x
                if d[i]>4: ok=False; break
            if not ok: break
        if not ok: continue
        key=tuple(tuple(per.get(c,[0]*CAT_LEN[c])) for c in range(4))
        if key in seen: continue
        seen.add(key)
        yield key

print("== elementwise min over each filler family (must be all-zero) ==")
worst=0
for k in range(5):
    for S in itertools.combinations(range(4),k):
        for j in range(5):
            mn=[4]*34
            n=0
            for F in fillers(S,j):
                n+=1
                for c in range(4):
                    b=CAT_BASE[c]
                    for i,x in enumerate(F[c]):
                        if x<mn[b+i]: mn[b+i]=x
            if n==0:
                print("  EMPTY filler family S=%s j=%d"%(S,j)); continue
            mx=max(mn)
            if mx>0:
                worst=max(worst,mx)
                print("  NONZERO min S=%s j=%d -> %s"%(S,j,[(M.tile_name(i),mn[i]) for i in range(34) if mn[i]>0]))
print("worst nonzero min over all families:", worst)

print("== mincount criterion vs explicit M_k intersection (sample flush classes) ==")
s1=json.load(open(r"D:\DSH\MJ2\work\data\out\single.json", encoding="utf-8"))
rows=s1["flush_m"]["tenpai_full_W"]["classes"]
import random
random.seed(7)
checked=0; bad=0
for r in random.sample([x for x in rows if x["n_hands"]<=300], 25):
    hands=[]
    for hs in r["hands"]:
        v=[int(ch) for ch in hs]
        cnt=[0]*34
        for i,x in enumerate(v): cnt[i]=x
        hands.append(tuple(cnt))
    mn=[4]*34
    for h in hands:
        for i in range(34):
            if h[i]<mn[i]: mn[i]=h[i]
    K=sum(mn)
    for k in (1,2,3,4):
        # explicit intersection of M_k
        common=None
        for h in hands:
            cs=M.codes_of(h,k)
            common = cs if common is None else (common & cs)
            if not common: break
        pred = (K>=k)
        act = bool(common)
        if pred!=act:
            bad+=1; print("   MISMATCH", r["W"], k, "K=",K, "explicit=",act)
    checked+=1
print("checked classes:", checked, "mismatches:", bad)
