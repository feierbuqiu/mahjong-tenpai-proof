
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sim_fail_detail.py <plan.json> [N] -- 与 fastverify 相同口径的 1e6 手模拟, 但把失败手牌全部落盘.
输出 work/verify/sim_fail_detail.json (失败手牌 + 其 W + 本类码数)
"""
import sys, os, json, random, pickle
from multiprocessing import Pool
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE,"..","strategy"))
HON=["E","S","W","N","Haku","Hatsu","Chun"]
def nm(t): return ("%d%s"%(t%9+1,"mps"[t//9])) if t<27 else HON[t-27]
HONI={"E":27,"S":28,"W":29,"N":30,"Haku":31,"Hatsu":32,"Chun":33}
def to_idx(x):
    if isinstance(x,int): return x
    if x in HONI: return HONI[x]
    return "mps".index(x[-1])*9+int(x[0])-1
BASE=[0,9,18,27]; CAP=4
_G={}
def init_worker():
    global PLANP
    PLANP=sys.argv[1] if len(sys.argv)>1 else os.path.join(HERE,"plan_k4_final.json")
    from indep_core import closed_form_W, KOKUSHI_IDX
    _G["cw"]=closed_form_W; _G["kok"]=KOKUSHI_IDX
    P=json.load(open(PLANP,encoding="utf-8"))
    plan={}
    for r in P["plan"]:
        W=frozenset(to_idx(x) for x in r["W"])
        plan.setdefault(W,[]).extend(tuple(c) for c in r["codes"])
    _G["plan"]={W:[[h.count(t) for t in range(34)] for h in cs] for W,cs in plan.items()}
    _G["dec"]={}
    for idx in range(4):
        L=7 if idx==3 else 9; units=[]
        if idx<3:
            for st in range(L-2):
                v=[0]*L; v[st]=1; v[st+1]=1; v[st+2]=1; units.append(tuple(v))
        for t in range(L):
            v=[0]*L; v[t]=3; units.append(tuple(v))
        out={}
        for s in range(0,13,3):
            res=set()
            def rec(i,left,acc):
                if left==0: res.add(acc); return
                for j in range(i,len(units)):
                    u=units[j]
                    if all(acc[k]+u[k]<=4 for k in range(L)): rec(j,left-3,tuple(acc[k]+u[k] for k in range(L)))
            rec(0,s,(0,)*L)
            out[s]=sorted(res)
        _G["dec"][idx]=out
def work(arg):
    seed,n=arg
    rng=random.Random(seed); plan=_G["plan"]; cw=_G["cw"]; dec=_G["dec"]
    CATSx=((9,0),(9,9),(9,18),(7,27)); fails=[]
    listening=0
    def rv(ci,n2):
        K,_=CATSx[ci]; c=[0]*K
        for _ in range(n2):
            while True:
                x=rng.randrange(K)
                if c[x]<CAP: c[x]+=1; break
        return c
    for _ in range(n):
        t=rng.random(); h=[0]*34
        if t<0.3:
            ci=rng.randrange(4); n1=rng.choice([1,4,7,10,13]); X=rv(ci,n1)
            for i,x in enumerate(X): h[CATSx[ci][1]+i]+=x
            cats=[c for c in range(4) if c!=ci]; rem=13-n1
            for ii,cj in enumerate(cats):
                left=len(cats)-ii-1
                opts=[s for s in range(0,rem+1,3) if rem-s<=12*left and (s==0 or dec[cj].get(s))]
                if not opts: rem=-1; break
                s=rng.choice(opts)
                if s:
                    v=rng.choice(dec[cj][s])
                    for i,x in enumerate(v): h[BASE[cj]+i]+=x
                rem-=s
            if rem!=0: continue
        elif t<0.75:
            c1,c2=rng.sample(range(4),2)
            n1=rng.choice([2,5,8,11]); n2=rng.choice([2,5,8,11])
            if n1+n2>13: n1,n2=2,2
            for cc,nn in ((c1,n1),(c2,n2)):
                X=rv(cc,nn)
                for i,x in enumerate(X): h[CATSx[cc][1]+i]+=x
            cats=[c for c in range(4) if c not in (c1,c2)]; rem=13-n1-n2
            for ii,cj in enumerate(cats):
                left=len(cats)-ii-1
                opts=[s for s in range(0,rem+1,3) if rem-s<=12*left and (s==0 or dec[cj].get(s))]
                if not opts: rem=-1; break
                s=rng.choice(opts)
                if s:
                    v=rng.choice(dec[cj][s])
                    for i,x in enumerate(v): h[BASE[cj]+i]+=x
                rem-=s
            if rem!=0: continue
        elif t<0.92:
            kinds=rng.sample(range(34),7); z=rng.choice(kinds)
            for kk in kinds: h[kk]=2
            h[z]=1
        elif t<0.96:
            ks=rng.sample(_G["kok"],12)
            for kk in ks: h[kk]=1
            h[rng.choice(ks)]+=1
        else:
            for _ in range(13):
                while True:
                    x=rng.randrange(34)
                    if h[x]<CAP: h[x]+=1; break
        if sum(h)!=13 or max(h)>4: continue
        W=cw(h)
        if not W: continue
        listening+=1
        cs=plan.get(W,[])
        if not cs: fails.append({"hand":"".join(nm(t)*h[t] for t in range(34)),"W":[nm(t) for t in sorted(W)],"codes":0,"reason":"no-codes"}); continue
        ok=False
        for c in cs:
            if all(h[t]>=c[t] for t in range(34)): ok=True; break
        if not ok: fails.append({"hand":"".join(nm(t)*h[t] for t in range(34)),"W":[nm(t) for t in sorted(W)],"codes":len(cs),"reason":"no-code-subset"})
    return listening, fails
if __name__=="__main__":
    PLANP=sys.argv[1] if len(sys.argv)>1 else os.path.join(HERE,"plan_k4_final.json")
    N=int(sys.argv[2]) if len(sys.argv)>2 else 1000000
    nproc=min(12,os.cpu_count() or 4)
    chunks=[(9000+i, N//nproc) for i in range(nproc)]
    with Pool(nproc, initializer=init_worker) as pool:
        res=pool.map(work, chunks)
    listening=sum(r[0] for r in res); fails=[x for r in res for x in r[1]]
    out={"plan":PLANP,"samples":N,"listening":listening,"fails":len(fails),"fail_examples":fails[:100]}
    json.dump(out, open(os.path.join(HERE,"sim_fail_detail.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
    print("听牌手牌=%d 失败=%d" % (listening,len(fails)))
    for f in fails[:12]: print("   ",f["hand"],"W=",",".join(f["W"]),"本类码=",f["codes"])
    print("已写 work/verify/sim_fail_detail.json")
