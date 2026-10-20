# -*- coding: utf-8 -*-
"""t13_kokushi_and_sampling.py -- (1) verify all 157 kokushi listening hands exactly,
(2) large independent END-TO-END random simulation: generate random hands from every
structural family, compute W with the independent engine, and require the plan to
contain the class and a fitting code.
"""
import sys, os, json, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjcore import *
from multiprocessing import Pool
from collections import Counter

D=os.path.dirname(os.path.abspath(__file__))
PLANF="D:/DSH/MJ2/work/verify/plan_k4_FINAL.json"
BASE=[0,9,18,27]; LEN=[9,9,9,7]

_P={}
def init():
    P=json.load(open(PLANF,encoding="utf-8"))
    plan={}
    for r in P["plan"]:
        W=frozenset(nm_idx(x) for x in r["W"])
        plan[W]=[tuple(sorted(Counter(nm_idx(t) for t in c).items())) for c in r["codes"]]
    _P["plan"]=plan
    _P["melds"]={}
    for ci in range(4):
        lst=[]
        for i in range(LEN[ci]):
            v=[0]*34; v[BASE[ci]+i]=3; lst.append(tuple(v))
        if ci<3:
            for i in range(LEN[ci]-2):
                v=[0]*34
                for k in range(3): v[BASE[ci]+i+k]=1
                lst.append(tuple(v))
        _P["melds"][ci]=lst
    _P["decf"]={}
    def dec(ci,s):
        key=(ci,s)
        if key in _P["decf"]: return _P["decf"][key]
        out=[]; ms=_P["melds"][ci]
        def rec(i,left,acc):
            if left==0: out.append(tuple(acc)); return
            for j in range(i,len(ms)):
                u=ms[j]
                if all(acc[t]+u[t]<=4 for t in range(34)): rec(j,left-3,tuple(acc[t]+u[t] for t in range(34)))
        if s==0: out=[tuple([0]*34)]
        else: rec(0,s,tuple([0]*34))
        _P["decf"][key]=out; return out
    _P["dec"]=dec

def check(h):
    w=waits(h)
    if not w: return None
    cs=_P["plan"].get(w)
    if cs is None: return ("missing_class", [nm(t) for t in sorted(w)], hand_str(h))
    for cod in cs:
        if all(h[t]>=v for t,v in cod): return None
    return ("uncovered", [nm(t) for t in sorted(w)], hand_str(h))

def kokushi_check():
    ks=[]
    c=[0]*34
    for t in ORPHANS: c[t]=1
    ks.append(tuple(c))
    for miss in ORPHANS:
        for dbl in ORPHANS:
            if dbl==miss: continue
            c=[0]*34
            for t in ORPHANS:
                if t!=miss: c[t]=1
            c[dbl]+=1
            ks.append(tuple(c))
    ks=sorted(set(ks))
    bad=[b for b in (check(h) for h in ks) if b]
    return {"hand_count":len(ks),"listening":sum(1 for h in ks if waits(h)),"bad":bad}

def sim(arg):
    seed,n=arg
    rng=random.Random(seed)
    dec=_P["dec"]
    bad=[]; listening=0; byfam=Counter()
    for _ in range(n):
        t=rng.random(); h=[0]*34
        if t<0.30:   # I-type: active single category
            ci=rng.randrange(4); s=rng.choice([1,4,7,10,13])
            kinds=list(range(BASE[ci],BASE[ci]+LEN[ci]))
            for _ in range(s): h[rng.choice(kinds)]+=1
            if max(h)>4: continue
            fam="I"
            rem=13-s
            for cj in [c for c in range(4) if c!=ci]:
                maxs=min(rem,12); opts=[x for x in range(0,maxs+1,3) if dec(cj,x)]
                x=rng.choice(opts) if opts else 0
                xs=dec(cj,x)
                v=rng.choice(xs) if x else tuple([0]*34)
                for k in range(34): h[k]+=v[k]
                rem-=x
            if sum(h)!=13 or max(h)>4: continue
        elif t<0.62: # II-type
            ci,cj=rng.sample(range(4),2)
            si=rng.choice([2,5,8,11]); sj=rng.choice([2,5,8,11])
            if si+sj>13: si=sj=2
            for c,s in ((ci,si),(cj,sj)):
                kinds=list(range(BASE[c],BASE[c]+LEN[c]))
                for _ in range(s):
                    k=rng.choice(kinds)
                    while h[k]>=4: k=rng.choice(kinds)
                    h[k]+=1
            rem=13-si-sj
            for c in [x for x in range(4) if x not in (ci,cj)]:
                opts=[x for x in range(0,rem+1,3) if dec(c,x)]
                x=rng.choice(opts) if opts else 0
                v=dec(c,x)[rng.randrange(len(dec(c,x)))] if x else tuple([0]*34)
                for k in range(34): h[k]+=v[k]
                rem-=x
            if sum(h)!=13 or max(h)>4: continue
            fam="II"
        elif t<0.80: # chiitoi
            ks=rng.sample(range(34),7)
            for k in ks[:6]: h[k]=2
            h[ks[6]]=1
            fam="chi"
        elif t<0.88: # kokushi
            ks=rng.sample(ORPHANS,12)
            for k in ks: h[k]=1
            h[rng.choice(ks)]+=1
            fam="kok"
        else:        # uniform random 13 multiset
            for _ in range(13):
                while True:
                    x=rng.randrange(34)
                    if h[x]<4: h[x]+=1; break
            fam="uni"
        b=check(tuple(h))
        if b: bad.append({"fam":fam,"err":b})
        else:
            w=waits(tuple(h))
            if w: listening+=1; byfam[fam]+=1
    return {"seed":seed,"listening":listening,"bad":bad[:5],"nbad":len(bad),"byfam":dict(byfam)}

if __name__=="__main__":
    t0=time.time()
    with Pool(6, initializer=init) as pool:
        kok=pool.apply(kokushi_check)
        res=pool.map(sim, [(1000+i, 150000) for i in range(12)])
    total_listen=sum(r["listening"] for r in res)
    bad=[(r["seed"],b) for r in res for b in r["bad"]]
    byfam=Counter()
    for r in res: byfam.update(r["byfam"])
    out={"kokushi":kok,"sim_hands":12*150000,"sim_listening":total_listen,
         "sim_bad":len(bad),"sim_bad_examples":bad[:10],"by_family":dict(byfam),
         "elapsed":round(time.time()-t0,1)}
    json.dump(out, open(D+"/t13_kokushi_sampling.json","w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False)[:3000])
