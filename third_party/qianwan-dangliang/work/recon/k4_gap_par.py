# -*- coding: utf-8 -*-
"""k4_gap_par.py <plan.json> [--jobs N] -- Lead 的多进程 Type I 块级覆盖检查（提速版）
串行版 work/recon/k4_gap_blocks.py 约 195 s；本版按类切块并行。
"""
import sys, os, json, time, collections, itertools
import multiprocessing as mp
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
HONN = ["E","S","W","N","Haku","Hatsu","Chun"]
SU = {"m":0,"p":1,"s":2,"z":3}
CATLEN=[9,9,9,7]; BASE=[0,9,18,27]
MELDS={}
for ci in range(4):
    L=CATLEN[ci]; b=BASE[ci]; lst=[]
    for i in range(L):
        v=[0]*34; v[b+i]=3; lst.append(tuple(v))
    if ci<3:
        for i in range(L-2):
            v=[0]*34
            for j in (i,i+1,i+2): v[b+j]+=1
            lst.append(tuple(v))
    MELDS[ci]=lst
MELDV={}
for ci in range(4):
    d={0:[tuple([0]*34)]}
    for s3 in (1,2,3,4):
        out=[]
        for combo in itertools.combinations_with_replacement(range(len(MELDS[ci])), s3):
            v=[0]*34
            for m_ in combo:
                for t in range(34): v[t]+=MELDS[ci][m_][t]
            if max(v)<=4: out.append(tuple(v))
        d[s3*3]=out
    MELDV[ci]=d
def ti(s): return 27+HONN.index(s) if s in HONN else "mps".index(s[-1])*9+int(s[0])-1
def parse(ds,ci):
    off=BASE[ci]; v=[0]*34
    for i,ch in enumerate(ds):
        if ch!='0': v[off+i]=int(ch)
    return v
_G={}
def _init(plan_path, classes):
    P=json.load(open(plan_path,encoding='utf-8'))
    rows=P["plan"] if isinstance(P,dict) and "plan" in P else P
    _G['plan']={frozenset((x if isinstance(x,int) else ti(x)) for x in r["W"]):[tuple(c) for c in r["codes"]] for r in rows}
    _G['classes']=classes
def _mat(codes):
    M=np.zeros((len(codes),34), dtype=np.int8)
    for i,c in enumerate(codes):
        for t in c: M[i,t]+=1
    return M
def _cnt(h,c):
    for t in set(c):
        if h[t] < c.count(t): return False
    return True
def _covered(A, inert, m, codes):
    if any(_cnt(A,c) for c in codes): return True
    ii=[SU[x] for x in inert]
    def rec(i, rem, hand):
        for c in codes:
            if _cnt(hand,c): return True
        if i==len(ii): return rem!=0
        ci=ii[i]
        for s in range(0,rem+1,3):
            if (rem-s) > 12*(len(ii)-i-1): continue
            for V in MELDV[ci][s]:
                h2=[hand[t]+V[t] for t in range(34)]
                if not rec(i+1,rem-s,h2): return False
        return True
    return rec(0,m,list(A))
def _work(chunk):
    plan=_G['plan']; out=[]
    for row in chunk:
        W=frozenset(ti(x) for x in row["W"])
        if W not in plan: continue
        if any(s["kind"]=="kokushi" for s in row.get("sources",[])): continue
        codes=plan[W]
        M=_mat(codes)
        for s in row.get("sources",[]):
            if s["kind"]!="I": continue
            ci=SU[s["cat"]]; A=parse(s["A"],ci); m=13-sum(A)
            if (M <= np.array(A, dtype=np.int8)).all(1).any(): continue
            if not _covered(A, s["inert"], m, codes):
                out.append({"W":row["W"],"A":s["A"],"cat":s["cat"],"m":m})
    return out
def main():
    plan=sys.argv[1]
    jobs=int(sys.argv[sys.argv.index('--jobs')+1]) if '--jobs' in sys.argv else (os.cpu_count() or 4)
    G=json.load(open('work/data/out/global.json',encoding='utf-8'))
    cls=G['classes']; n=len(cls)
    nb=min(jobs*16, n)
    chunks=[cls[i*n//nb:(i+1)*n//nb] for i in range(nb)]
    t0=time.time()
    with mp.Pool(jobs, initializer=_init, initargs=(plan, None)) as pool:
        res=list(pool.imap_unordered(_work, chunks, chunksize=1))
    bad=[x for r in res for x in r]
    print("PARALLEL jobs=%d classes=%d  uncovered=%d  %.1fs" % (nb, n, len(bad), time.time()-t0))
    json.dump(bad, open(os.path.join(HERE,'k4_gap_par.json'),'w'), ensure_ascii=False)
if __name__=="__main__":
    main()
