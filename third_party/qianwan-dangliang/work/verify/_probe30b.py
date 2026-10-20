
import sys, os, json, pickle, random
sys.path.insert(0,"work/verify"); sys.path.insert(0,"work/strategy")
import indep_core as IC
HON=["E","S","W","N","Haku","Hatsu","Chun"]
def nm(t): return ("%d%s"%(t%9+1,"mps"[t//9])) if t<27 else HON[t-27]
CAT_BASE={"m":0,"p":9,"s":18,"z":27}
C=pickle.load(open("work/strategy/out/table_cache.pkl","rb"))
CLS, PROFI_D, PROFII_D = C["cls"], C["PROFI_D"], C["PROFII_D"]
P=json.load(open("work/verify/plan_k4_final.json",encoding="utf-8"))
plan={frozenset(r["W"]):[tuple(c) for c in r["codes"]] for r in P["plan"]}
Z=json.load(open("work/verify/plan_k4_zero.json",encoding="utf-8"))
zero={frozenset(r["W"]):len(r["codes"]) for r in Z["plan"]}
empties=[frozenset(r["W"]) for r in Z["plan"] if not r["codes"]]
rng=random.Random(4242)
def gen_hand(blocks, cl):
    """从来源块随机构造一手牌 (13 张)"""
    for b in blocks:
        for _ in range(200):
            A=[0]*34
            if b[0]=="I":
                key=b[1]; e=PROFI_D.get(key)
                if not e: continue
                xs=e[1]; X=rng.choice(xs)
                for i,x in enumerate(X): A[CAT_BASE[key[0]]+i]=x
                rem=13-key[1]
                cats=[i for i in range(4) if i!=key[0]]
                ok=True
                for ii,ci in enumerate(cats):
                    left=len(cats)-ii-1
                    opts=[s for s in range(0,rem+1,3) if rem-s<=12*left]
                    if not opts: ok=False; break
                    s=rng.choice(opts)
                    if s:
                        # 随机用 melds 分解占 s 张
                        for _try in range(50):
                            v=cl.dec_vecs(ci,s)
                            if v: break
                        else: ok=False; break
                        v=rng.choice(v)
                        base=CAT_BASE["mpsz"[ci]]
                        for i,x in enumerate(v): A[base+i]=x
                    rem-=s
                if ok and rem==0 and sum(A)==13: return A
            elif b[0]=="II":
                e1,e2=PROFII_D.get(b[1]),PROFII_D.get(b[2])
                if not e1 or not e2: continue
                X1=rng.choice(e1[1]); X2=rng.choice(e2[1])
                for i,x in enumerate(X1): A[CAT_BASE[b[1][0]]+i]=x
                for i,x in enumerate(X2): A[CAT_BASE[b[2][0]]+i]=x
                rem=13-b[1][1]-b[2][1]; cats=[i for i in range(4) if i not in (b[1][0],b[2][0])]
                ok=True
                for ii,ci in enumerate(cats):
                    left=len(cats)-ii-1
                    opts=[s for s in range(0,rem+1,3) if rem-s<=12*left]
                    if not opts: ok=False; break
                    s=rng.choice(opts)
                    if s:
                        v=None
                        for _try in range(50):
                            vv=cl.dec_vecs(ci,s)
                            if vv: v=rng.choice(vv); break
                        if v is None: ok=False; break
                        base=CAT_BASE["mpsz"[ci]]
                        for i,x in enumerate(v): A[base+i]=x
                    rem-=s
                if ok and rem==0 and sum(A)==13: return A
            else:
                return None
    return None
import importlib
sys.path.insert(0,"work/verify")
# dec_vecs 从 waste_exact 借用? 单独实现: 枚举该花色内 3 的倍数的合法 melds 分解
def dec_vecs(cat, s):
    idx={"m":0,"p":1,"s":2,"z":3}[cat]
    return _DEC.get((idx,s), [])
# 构造 _DEC: 花色内所有 melds 组合 (runs for mps, triplets only for z)
def build_dec():
    D={}
    for idx,cat in enumerate("mpsz"):
        L=7 if idx==3 else 9
        # 单位 meld 集合
        units=[]
        if idx<3:
            for st in range(L-2): 
                v=[0]*L; v[st]=1; v[st+1]=1; v[st+2]=1; units.append(tuple(v))
        for t in range(L):
            v=[0]*L; v[t]=3; units.append(tuple(v))
        for s in range(0,13,3):
            res=set()
            def rec(i,left,acc):
                if left==0: res.add(acc); return
                for j in range(i,len(units)):
                    u=units[j]
                    if all(acc[k]+u[k]<=4 for k in range(L)):
                        rec(j,left-3,tuple(acc[k]+u[k] for k in range(L)))
            rec(0,s,(0,)*L)
            D[(idx,s)]=sorted(res)
    return D
_DEC=build_dec()
th=type("D",(),{"dec_vecs":staticmethod(lambda cat,s: dec_vecs(cat,s))})()
print("empty classes:",len(empties))
res=[]
for W in empties:
    blocks=CLS.get(W,[])
    hands=[]
    for _ in range(400):
        h=gen_hand(blocks,th)
        if h: hands.append(h)
    wok=0; cov=0; uncon=None
    for h in hands:
        if frozenset(IC.compute_W(h))==W:
            wok+=1
            cs=plan.get(W,[])
            hit=[c for c in cs if all(h[t]>=c.count(t) for t in range(34))]
            if hit: cov+=1
            elif uncon is None: uncon=h
    res.append((W,len(blocks),len(hands),wok,cov,uncon))
print("%-28s %5s %6s %6s %6s" % ("W","blocks","gen","W-ok","covered"))
for W,nb,ng,wok,cov,uncon in res[:12]:
    print("%-28s %5d %6d %6d %6d  %s" % (",".join(nm(t) for t in sorted(W))[:28],nb,ng,wok,cov,
          ("uncovered e.g. "+",".join(nm(t) for t in [t for t in range(34) for _ in range(uncon[t])])) if uncon else ""))
tot_wok=sum(r[3] for r in res); tot_cov=sum(r[4] for r in res)
print("TOTAL: W-verified hands=%d covered=%d uncovered=%d" % (tot_wok,tot_cov,tot_wok-tot_cov))
