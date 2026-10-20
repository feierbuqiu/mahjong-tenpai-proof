# -*- coding: utf-8 -*-
"""测量: 单类别类(387/门) 的全部来源块 需要多少"本门"3-码来覆盖 (子宇宙预算的紧约束)."""
import json, itertools, collections, time
d=json.load(open(r"D:\DSH\MJ2\work\data\out\global.json"))
CLS=d["classes"]; LETTER="mpsz"
def base_of(c): return c*9 if c<3 else 27
def parse_A(s,cat):
    base=base_of(cat); v=[]
    for i,ch in enumerate(s):
        for _ in range(int(ch)): v.append(base+i)
    return tuple(sorted(v))
PATS={}
for c in range(4):
    n=9 if c<3 else 7; base=base_of(c)
    tiles=[base+i for i in range(n)]
    PATS[c]=[tuple(sorted(p)) for p in itertools.combinations_with_replacement(tiles,3)]
def cover_size(fam, pats):
    fam=list(set(fam))
    if not fam: return 0,0
    # each pattern covers fam items containing it
    cov=[frozenset(i for i,A in enumerate(fam) if all(A.count(t)>=p.count(t) for t in set(p))) for p in pats]
    cov=[c for c in cov if c]
    universe=set(range(len(fam))); chosen=0
    unc=set(universe)
    while unc:
        best=None; bc=0
        for cset in cov:
            n=len(cset & unc)
            if n>bc: bc=n; best=cset
        if best is None: break
        chosen+=1; unc-=best
    return chosen, len(unc)

res={}
for cat,letter in enumerate(LETTER):
    sel=[c for c in CLS if c["sub_universe"]==[letter]]
    tot=0; leftover=0; sizes=[]
    t0=time.time()
    for c in sel:
        fam=[]
        for s in c["sources"]:
            if s.get("kind")=="I" and s["cat"]==letter:
                fam.append(parse_A(s["A"],cat))
            elif s.get("kind")=="II" and letter in s["cats"]:
                # 只有 A 完全落在本门时才耗本门码预算; 取 minA1/minA2 中本门部分
                j=s["cats"].index(letter)
                A=parse_A(s["minA1"] if j==0 else s["minA2"], cat)
                fam.append(A)
        cs,left=cover_size(fam, PATS[cat])
        tot+=cs; leftover+=left; sizes.append((cs,len(set(fam))))
    res[letter]=dict(classes=len(sel), sum_cover=tot, uncovered=leftover, budget=(9**3 if cat<3 else 7**3), secs=round(time.time()-t0,1))
    print(letter, json.dumps(res[letter]), flush=True)
    top=sorted(sizes, reverse=True)[:6]
    print("   top cover sizes:", top, flush=True)
json.dump(res, open(r"D:\DSH\MJ2\work\recon\subuniverse_cover.json","w"))
