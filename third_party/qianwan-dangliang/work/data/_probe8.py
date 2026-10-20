# -*- coding: utf-8 -*-
"""_probe8.py -- exact parity-rule (4-tiles-count-as-2-pairs) chiitoi extras -> class masks.

Enumerates every 13-tile hand with exactly one odd-count type (the parity reading of
MODEL.md 5), i.e. patterns: a quads + b pairs + z(t=1 or 3), 2a+b = (12 or 10)/2.
class = W_std(H) | (1<<z).
"""
import sys, time, itertools, json, math
sys.path.insert(0, r"D:\DSH\MJ2\work\data")
import mjcore as M
import multiprocessing as mp

EMPTY9=(0,)*9; EMPTY7=(0,)*7

def hands_pattern(a,b,t,i):
    """yield (base_cat_tuples, used_set) for first chosen type == i; then caller adds z."""
    if a==0:
        rest = itertools.combinations(range(i+1,34), b-1)
        for c in rest:
            yield (i,)+c
    else:
        rest = itertools.combinations(range(i+1,34), a-1)
        for q in rest:
            quads=(i,)+q
            avail=[x for x in range(34) if x not in quads]
            for p in itertools.combinations(avail, b):
                # canonical: first pair may be < i, so dedupe by requiring min(quads)<min(pairs) OR quads min is i (already fixed)
                yield quads, p

def build(t):
    a,b,t_ = t
    out=[]
    for i in range(34):
        cnt=0
        if a==0:
            if i > 34-b: continue
            for pairs in hands_pattern(a,b,t_,i):
                out.append((i,a,b,t_,pairs))
        else:
            if i > 34-a: continue
            for quads,pairs in hands_pattern(a,b,t_,i):
                out.append((i,a,b,t_,quads,pairs))
    return out

def worker(tasks):
    res=set()
    for (a,b,t_,i) in tasks:
        if a==0:
            for pairs in hands_pattern(a,b,t_,i):
                used=set(pairs)
                base=[ [0]*9, [0]*9, [0]*9, [0]*7 ]
                for x in pairs:
                    c=x//9 if x<27 else 3; j=x%9 if x<27 else x-27
                    base[c][j]+=2
                base=tuple(tuple(v) for v in base)
                for z in range(34):
                    if z in used: continue
                    c=z//9 if z<27 else 3; j=z%9 if z<27 else z-27
                    vv=list(base[c]); vv[j]+=t_
                    vs=base[:c]+(tuple(vv),)+base[c+1:]
                    res.add(M.waits_std_vecs(vs)|(1<<z))
        else:
            for quads,pairs in hands_pattern(a,b,t_,i):
                used=set(quads)|set(pairs)
                base=[ [0]*9, [0]*9, [0]*9, [0]*7 ]
                for x in quads:
                    c=x//9 if x<27 else 3; j=x%9 if x<27 else x-27
                    base[c][j]+=4
                for x in pairs:
                    c=x//9 if x<27 else 3; j=x%9 if x<27 else x-27
                    base[c][j]+=2
                base=tuple(tuple(v) for v in base)
                for z in range(34):
                    if z in used: continue
                    c=z//9 if z<27 else 3; j=z%9 if z<27 else z-27
                    vv=list(base[c]); vv[j]+=t_
                    vs=base[:c]+(tuple(vv),)+base[c+1:]
                    res.add(M.waits_std_vecs(vs)|(1<<z))
    return res

if __name__=="__main__":
    t0=time.time()
    PATTERNS=[(0,6,1),(1,4,1),(2,2,1),(3,0,1),(0,5,3),(1,3,3),(2,1,3)]
    total=sum(math.comb(34,a)*math.comb(34-a,b)*(34-a-b) for (a,b,t) in PATTERNS)
    print("parity hands total =", total, flush=True)
    tasks=[]
    for (a,b,t) in PATTERNS:
        hi = 34-b if a==0 else 34-a
        for i in range(hi):
            tasks.append((a,b,t,i))
    print("outer tasks:", len(tasks), flush=True)
    # balance by weight
    def w(t):
        a,b,tt,i=t
        if a==0: return math.comb(34-i-1,b-1)*1
        return math.comb(34-i-1,a-1)*math.comb(34-(a+b),b)
    tasks.sort(key=w, reverse=True)
    groups=[[] for _ in range(6)]
    ws=[0]*6
    for tk in tasks:
        k=ws.index(min(ws)); groups[k].append(tk); ws[k]+=w(tk)
    with mp.Pool(6) as pool:
        res=pool.map(worker, groups)
    B=set()
    for s_ in res: B|=s_
    print("parity chiitoi-derived classes:", len(B), "t=%.1fs"%(time.time()-t0), flush=True)
    json.dump({"masks":sorted(B)}, open(r"D:\DSH\MJ2\work\data\out\_probe_parity_masks.json","w"))
