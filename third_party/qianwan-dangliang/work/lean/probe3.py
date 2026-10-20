# -*- coding: utf-8 -*-
"""work/lean/probe3.py -- analyse the 169 failing I-units."""
import sys, pickle, json, collections
sys.path.insert(0, r'D:\DSH\MJ2\work\strategy'); sys.path.insert(0, r'D:\DSH\MJ2\work\strategy\out')
HON = ["E","S","W","N","Haku","Hatsu","Chun"]; HONI = {n:27+i for i,n in enumerate(HON)}
def to_idx(x):
    if isinstance(x,int): return x
    if x in HONI: return HONI[x]
    return "mps".index(x[-1])*9+int(x[0])-1
def nm(t): return ("%d%s"%(t%9+1,"mps"[t//9])) if t<27 else HON[t-27]

P=json.load(open(r'D:\DSH\MJ2\work\verify\plan_k4_FINAL.json',encoding='utf-8'))
plan={}
for r in P["plan"]:
    W=frozenset(to_idx(x) for x in r["W"]); plan.setdefault(W,[]).extend(tuple(sorted(c)) for c in r["codes"])
C=pickle.load(open(r'D:\DSH\MJ2\work\strategy\out\table_cache.pkl','rb'))
cls,PI=C['cls'],C['PROFI_D']

def local(c,cat):
    off=(cat*9) if cat<3 else 27; n=9 if cat<3 else 7; e=0
    for i in range(n):
        k=c.count(off+i)
        if k: e+=k*6**i
    return e
def tile_cat(t): return t//9 if t<27 else 3
def le_digits(x,y):
    for _ in range(9):
        if x%6>y%6: return False
        x//=6; y//=6
    return True

fails=[]
for W,blocks in cls.items():
    for b in blocks:
        if b[0]!='I': continue
        key=b[1]; ci=key[0]; s=key[1]; e=PI.get(key)
        if not e: continue
        cand=[local(c,ci) for c in plan.get(W,[]) if all(tile_cat(t)==ci for t in c)]
        for X in e[1]:
            enc=0
            for i,v in enumerate(X):
                if v: enc+=v*6**i
            if not any(le_digits(ce,enc) for ce in cand):
                fails.append((tuple(sorted(W)),ci,s,X))
print("failures:",len(fails))
cnt=collections.Counter((f[1],f[2]) for f in fails)
print("by (cat,size):",dict(cnt))
bycls=collections.Counter(f[0] for f in fails)
print("by class (top10):",bycls.most_common(10))
for W,ci,s,X in fails[:12]:
    print("  W=%s cat=%d size=%d X=%s  plan_codes=%s"%( [nm(t) for t in W],ci,s,"".join(str(x) for x in X),
          [list(c) for c in plan.get(frozenset(W),[])][:6]))
