# -*- coding: utf-8 -*-
"""t17_nocommon.py -- independently recompute the "no common k-code" class counts for
the 387 flush classes (MODEL/REPORT claim k=1..4 -> 40/53/87/111)."""
import sys, os, json, time, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjcore import *
D=os.path.dirname(os.path.abspath(__file__))
t0=time.time()
hands=list(multisets(13, range(9)))
groups={}
for h in hands:
    w=waits(h)
    if w: groups.setdefault(w,[]).append(h)
print("classes",len(groups),"hands",sum(len(v) for v in groups.values()),flush=True)

def submultisets_of(h,k):
    """all multisets (as sorted tuples of tiles) of size k inside h"""
    tiles=[t for t in range(34) if h[t]]
    out=set()
    for combo in itertools.combinations_with_replacement(tiles,k):
        c={}
        for t in combo: c[t]=c.get(t,0)+1
        if all(h[t]>=v for t,v in c.items()): out.add(combo)
    return out

res={}
for k in (1,2,3,4):
    nocommon=[]
    for w,hs in groups.items():
        cur=submultisets_of(hs[0],k)
        for h in hs[1:]:
            if not cur: break
            cur &= submultisets_of(h,k)
        if not cur: nocommon.append(w)
    res["k%d"%k]={"no_common":len(nocommon),"claim":{1:40,2:53,3:87,4:111}[k]}
    print(k, len(nocommon), "claim", {1:40,2:53,3:87,4:111}[k], "%.0fs"%(time.time()-t0), flush=True)
out={"classes":len(groups),"results":res,"elapsed":round(time.time()-t0,1)}
json.dump(out,open(D+"/t17_nocommon.json","w"),ensure_ascii=False,indent=1)
print(json.dumps(out,ensure_ascii=False))
