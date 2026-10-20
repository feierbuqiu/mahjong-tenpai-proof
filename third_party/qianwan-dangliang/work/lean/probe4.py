# -*- coding: utf-8 -*-
"""work/lean/probe4.py -- count DFS nodes for the 169 failing I-units (block-level semantics)."""
import sys, pickle, json, itertools, time
sys.path.insert(0, r'D:\DSH\MJ2\work\strategy'); sys.path.insert(0, r'D:\DSH\MJ2\work\strategy\out')
HON=["E","S","W","N","Haku","Hatsu","Chun"]; HONI={n:27+i for i,n in enumerate(HON)}
def to_idx(x):
    if isinstance(x,int): return x
    if x in HONI: return HONI[x]
    return "mps".index(x[-1])*9+int(x[0])-1
BASE=[0,9,18,27]
def nm(t): return ("%d%s"%(t%9+1,"mps"[t//9])) if t<27 else HON[t-27]

P=json.load(open(r'D:\DSH\MJ2\work\verify\plan_k4_FINAL.json',encoding='utf-8'))
plan={}
for r in P["plan"]:
    W=frozenset(to_idx(x) for x in r["W"]); plan.setdefault(W,[]).extend(tuple(sorted(c)) for c in r["codes"])
C=pickle.load(open(r'D:\DSH\MJ2\work\strategy\out\table_cache.pkl','rb'))
cls,PI=C['cls'],C['PROFI_D']

def build_dec(idx):
    L=7 if idx==3 else 9; units=[]
    if idx<3:
        for st in range(L-2):
            v=[0]*L; v[st]=v[st+1]=v[st+2]=1; units.append(tuple(v))
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
    return out
DEC=[build_dec(i) for i in range(4)]

TAB={}
def filler_tab(c,s): return DEC[c].get(s,())

nodes=[0]
def contains(h,c):
    cc={}
    for t in c: cc[t]=cc.get(t,0)+1
    return all(h[t]>=v for t,v in cc.items())

def dfs(base, inert, rem, codes):
    nodes[0]+=1
    if any(contains(base,c) for c in codes): return True
    def rec(i,left,h):
        nodes[0]+=1
        for c in codes:
            if contains(h,c): return True
        if i==len(inert):
            return left!=0
        ci=inert[i]
        maxrest=12*(len(inert)-i-1)
        for s in range(0,left+1,3):
            if left-s>maxrest: continue
            for v in filler_tab(ci,s):
                h2=list(h)
                for t,x in enumerate(v): h2[BASE[ci]+t]+=x
                if not rec(i+1,left-s,h2): return False
        return True
    return rec(0,rem,base)

t0=time.time()
units=[]
for W,blocks in cls.items():
    for b in blocks:
        if b[0]!='I': continue
        key=b[1]; ci=key[0]; e=PI.get(key)
        if not e: continue
        for X in e[1]: units.append((W,ci,X))
print("I units:",len(units))
fails=[]
for (W,ci,X) in units:
    A=[0]*34
    for i,v in enumerate(X): A[BASE[ci]+i]=v
    if not any(contains(A,c) for c in plan.get(W,[])): fails.append((W,ci,X,A))
print("failing units:",len(fails))
tot=0
for (W,ci,X,A) in fails:
    inert=tuple(i for i in range(4) if i!=ci)
    s=sum(X); rem=13-s
    nodes[0]=0
    ok=dfs(A,inert,rem,plan.get(W,[]))
    tot+=nodes[0]
    if not ok: print("  DFS says NOT covered!",sorted(W),ci,X)
print("total DFS nodes over failing units:",tot,"  time %.1fs"%(time.time()-t0))
