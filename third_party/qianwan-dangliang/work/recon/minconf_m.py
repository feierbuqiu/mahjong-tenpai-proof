# -*- coding: utf-8 -*-
"""对 m 子宇宙(387 类, 165 个 3-码多重集, 总容量 729)做 min-conflicts 装包试验。
   每个类需要一个"块覆盖", 每个多重集的使用次数不得超过其排列数。"""
import json, itertools, math, collections, random, time
T0=time.time()
def log(*a): print("[%6.1fs]"%(time.time()-T0), *a, flush=True)
d=json.load(open(r"D:\DSH\MJ2\work\data\out\global.json"))
CLS=d["classes"]; LETTER="mpsz"
def cat_of(t): return t//9 if t<27 else 3
def base_of(c): return c*9 if c<3 else 27
def parse_A(s,cat):
    base=base_of(cat); v=[0]*34
    for i,ch in enumerate(s):
        n=int(ch)
        if n: v[base+i]=n
    return tuple(v)
PERM={}
def nperm(p):
    if p not in PERM:
        f=1
        for x in set(p): f*=math.factorial(p.count(x))
        PERM[p]=6//f
    return PERM[p]
def min_blocks(uni):
    bs=sorted(set(uni), key=sum); keep=[]
    for v in bs:
        if not any(all(a<=b for a,b in zip(k,v)) for k in keep): keep.append(v)
    return keep
classes=[]
for c in CLS:
    if c["sub_universe"]!=["m"]: continue
    uni=[]
    for s in c["sources"]:
        if s.get("kind")=="I" and s["cat"]=="m":
            A=parse_A(s["A"],0)
            if sum(A)>=3: uni.append(A)
        elif s.get("kind")=="II" and "m" in s["cats"]:
            j=s["cats"].index("m"); A=parse_A(s["minA1"] if j==0 else s["minA2"],0)
            if sum(A)>=3: uni.append(A)
    blocks=min_blocks(uni)
    classes.append((c["Wmask"], c["W"], blocks))
log("m-classes=%d"%len(classes))
tiles=list(range(9))
pats=[tuple(sorted(p)) for p in itertools.combinations_with_replacement(tiles,3)]
pidx={p:i for i,p in enumerate(pats)}
caps=[nperm(p) for p in pats]
bcov=[]
for (wm,w,blocks) in classes:
    row=[0]*len(pats); n=0
    for bi,A in enumerate(blocks):
        for pi,p in enumerate(pats):
            ok=True
            for t in set(p):
                if A[t]<p.count(t): ok=False; break
            if ok: row[pi]|=1<<bi
    bcov.append(row)
nb=[len(b) for (_,_,b) in classes]
def cover(ci, banned):
    row=bcov[ci]; nb_=nb[ci]; unc=(1<<nb_)-1; out=[]
    while unc:
        best=-1; bkey=None
        for pi in range(len(pats)):
            if pi in banned: continue
            mm=row[pi]&unc
            if not mm: continue
            key=(bin(mm).count("1"), caps[pi])
            if bkey is None or key>bkey: bkey=key; best=pi
        if best<0: return None
        out.append(best); unc &= ~row[best]
    return out
def solve(seed, iters=300000):
    rnd=random.Random(seed)
    covers=[cover(i,set()) for i in range(len(classes))]
    if any(c is None for c in covers): return None
    best=None
    for it in range(iters):
        usage=collections.Counter()
        for cv in covers: usage.update(cv)
        over=[p for p in usage if usage[p]>caps[p]]
        if not over:
            return covers, sum(usage.values())
        if best is None or len(over)<best[1]: best=(None,len(over),it)
        p=rnd.choice(over)
        owners=[i for i,cv in enumerate(covers) if p in cv]
        rnd.shuffle(owners)
        for i in owners:
            banned={q for q in usage if usage[q]>=caps[q]}
            banned.add(p)
            nc=cover(i,banned)
            if nc is not None:
                covers[i]=nc; break
    return best
res=None
for seed in range(8):
    r=solve(seed)
    if r and isinstance(r,tuple) and r[0] is not None:
        log("FEASIBLE seed=%d total=%d"%(seed,r[1])); res=("ok",seed,r[1]); break
    else:
        log("seed=%d -> %s"%(seed, (r[1] if isinstance(r,tuple) and r[0] is None else r)))
        if res is None: res=("partial",seed,r)
log("RESULT:", res)
json.dump({"result":str(res)}, open(r"D:\DSH\MJ2\work\recon\minconf_m.json","w"))
