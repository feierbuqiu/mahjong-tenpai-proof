
import json, sys, random
sys.path.insert(0, "work/verify")
from indep_core import closed_form_W, compute_W, gen_vectors, melds_only, melds_only_honor, CAP, KOKUSHI_IDX

def rand_hand():
    import random
    from indep_core import melds_only as mo, melds_only_honor as moh
    CAT_K=(9,9,9,7); CAT_OFF=(0,9,18,27); CAT_HON=(False,False,False,True)
    DEC={}
    def dec(ci,s):
        k=(ci,s)
        if k in DEC: return DEC[k]
        out=[]
        for v in gen_vectors(CAT_K[ci],s):
            if (moh(v) if CAT_HON[ci] else mo(v)):
                u=[0]*34
                for i,x in enumerate(v):
                    if x: u[CAT_OFF[ci]+i]=x
                out.append(tuple(u))
        DEC[k]=out; return out
    def rv(ci,n):
        c=[0]*CAT_K[ci]
        for _ in range(n):
            while True:
                t=rng.randrange(CAT_K[ci])
                if c[t]<CAP: c[t]+=1; break
        return c
    t=rng.random(); hand=[0]*34
    if t<0.30:
        ci=rng.randrange(4); n=rng.choice([1,4,7,10,13]); X=rv(ci,n)
        for i,x in enumerate(X): hand[CAT_OFF[ci]+i]+=x
        cats=[c for c in range(4) if c!=ci]; rem=13-n
        for idx,cj in enumerate(cats):
            left=len(cats)-idx-1
            ch=[s for s in range(0,rem+1,3) if rem-s<=12*left and (s==0 or dec(cj,s))]
            s=rng.choice(ch)
            if s:
                v=rng.choice(dec(cj,s))
                for i,x in enumerate(v): hand[i]+=x
            rem-=s
    elif t<0.75:
        c1,c2=rng.sample(range(4),2); n1=rng.choice([2,5,8,11]); n2=rng.choice([2,5,8,11])
        if n1+n2>13: n1,n2=2,2
        for cc,nn in ((c1,n1),(c2,n2)):
            X=rv(cc,nn)
            for i,x in enumerate(X): hand[CAT_OFF[cc]+i]+=x
        cats=[c for c in range(4) if c not in (c1,c2)]; rem=13-n1-n2
        for idx,cj in enumerate(cats):
            left=len(cats)-idx-1
            ch=[s for s in range(0,rem+1,3) if rem-s<=12*left and (s==0 or dec(cj,s))]
            s=rng.choice(ch)
            if s:
                v=rng.choice(dec(cj,s))
                for i,x in enumerate(v): hand[i]+=x
            rem-=s
    elif t<0.92:
        kinds=rng.sample(range(34),7); z=rng.choice(kinds)
        for k in kinds: hand[k]=2
        hand[z]=1
    elif t<0.96:
        ks=rng.sample(KOKUSHI_IDX,12)
        for k in ks: hand[k]=1
        hand[rng.choice(ks)]+=1
    else:
        for _ in range(13):
            while True:
                x=rng.randrange(34)
                if hand[x]<CAP: hand[x]+=1; break
    return hand

mine = set(frozenset(x) for x in json.load(open("work/verify/census_strict.json", encoding="utf-8")))
rng = random.Random(1234)
miss = []; hits = set(); n = 0; bf = 0; bf_bad = 0
for it in range(300000):
    h = rand_hand()
    W = closed_form_W(h)
    if not W: continue
    n += 1; hits.add(W)
    if W not in mine:
        if len(miss) < 5: miss.append({"W": sorted(W), "hand": h})
    if it % 5000 == 0:
        b = compute_W(h); bf += 1
        if b != W: bf_bad += 1
print("listening sampled:", n, "distinct classes hit:", len(hits), "not in census:", len(miss))
print("brute-force checked:", bf, "mismatch:", bf_bad)
for m in miss: print("MISS", m)
