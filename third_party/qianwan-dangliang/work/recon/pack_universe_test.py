# -*- coding: utf-8 -*-
"""子宇宙装包试验: 对每门(n=9/7)的类集合, 用容量感知贪心把"来源块覆盖码"装进 |codes|=n^3 的池。
   容量: 多重集 p 的排列数 (1/3/6)。多随机顺序重复, 报告最优。"""
import json, itertools, math, collections, random, time
d=json.load(open(r"D:\DSH\MJ2\work\data\out\global.json"))
CLS=d["classes"]
LETTER="mpsz"
def base_of(c): return c*9 if c<3 else 27
def parse_A(s,cat):
    base=base_of(cat); v=[0]*34
    for i,ch in enumerate(s):
        n=int(ch)
        if n: v[base+i]=n
    return tuple(v)
def cap(p):
    f=1
    for x in set(p): f*=math.factorial(p.count(x))
    return 6//f
def class_blocks(c, letter, cat):
    out=[]
    for s in c["sources"]:
        if s.get("kind")=="I" and s["cat"]==letter: out.append(parse_A(s["A"],cat))
        elif s.get("kind")=="II" and letter in s["cats"]:
            j=s["cats"].index(letter)
            out.append(parse_A(s["minA1"] if j==0 else s["minA2"], cat))
    return [b for b in out if sum(b)>=3]

def attempt(cat, letter, order, ratio):
    n=9 if cat<3 else 7; base=base_of(cat)
    univ=[tuple(sorted(p)) for p in itertools.combinations_with_replacement([base+i for i in range(n)],3)]
    caps={p:cap(p) for p in univ}
    used=collections.Counter()
    total=0; fails=0
    for c in order:
        blk=list(set(class_blocks(c,letter,cat)))
        if not blk: continue
        tl=[]
        for A in blk:
            for t,cn in enumerate(A): tl += [t]*cn
        # per-pattern coverage of blocks
        bcov=[0]*len(univ)
        for bi,A in enumerate(blk):
            for pi,p in enumerate(univ):
                if all(A.count(t)>=p.count(t) for t in set(p)): bcov[pi]|=1<<bi
        unc=(1<<len(blk))-1
        while unc:
            best=-1; bs=-1.0
            for pi,p in enumerate(univ):
                rem=caps[p]-used[p]
                if rem<=0: continue
                cvg=bin(bcov[pi]&unc).count("1")
                if cvg==0: continue
                s=(cvg**ratio)*(rem**0.5 if ratio<2 else rem)
                if s>bs: bs=s; best=pi
            if best<0: break
            used[univ[best]]+=1; total+=1
            unc &= ~bcov[best]
        if unc: fails+=1
    return total, fails, sum(used.values())

random.seed(7)
res={}
for cat,letter in enumerate(LETTER):
    sel=[c for c in CLS if c["sub_universe"]==[letter]]
    best=None
    for trial in range(24):
        order=sel[:]; random.shuffle(order)
        for ratio in (1,2):
            t,f,u=attempt(cat,letter,order,ratio)
            if best is None or (f,t)<(best[1],best[0]): best=(t,f,u)
    res[letter]=dict(classes=len(sel),best_total=best[0],uncovered_classes=best[1],codes_used=best[2],budget=(9**3 if cat<3 else 7**3))
    print(letter, json.dumps(res[letter]), flush=True)
json.dump(res, open(r"D:\DSH\MJ2\work\recon\pack_universe_test.json","w"))
