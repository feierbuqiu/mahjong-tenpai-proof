
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""block_coverage_exact.py <plan.json> -- 精确逐块覆盖检查 (MODEL.md 条件2), 覆盖 I 与 II 两类块.

对每个类 W 的每个来源块:
  I  块: 基式 X 遍历 PROFI_D[key][1] 的全部 A 变体; 余牌在同一类内以面子补全 (inert 类别);
  II 块: 基式 X1∈PROFII_D[k1][1], X2∈PROFII_D[k2][1]; 余牌在 inert 类别内面子补全;
  对每一种基式: 若存在本类码 c ⊆ 基式, 则该基式下全部手牌被覆盖; 否则 DFS 枚举补全,
  途中每扩展一步就检查是否已有码被包含 (早停).
未覆盖 => 存在该类的一手牌不被本类任何码覆盖 (条件2 违反); 记录见证手牌.
输出 work/verify/block_coverage_exact.json
"""
import sys, os, json, pickle
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
BASE=[0,9,18,27]
_G={}
def build_dec(idx):
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
    return out
def init_worker():
    global PLANP
    PLANP=sys.argv[1] if len(sys.argv)>1 else os.path.join(HERE,"plan_k4_final.json")
    C=pickle.load(open(os.path.join(HERE,"..","strategy","out","table_cache.pkl"),"rb"))
    _G["cls"],_G["PI"],_G["PII"]=C["cls"],C["PROFI_D"],C["PROFII_D"]
    for i in range(4): _G[i]=build_dec(i)
    P=json.load(open(PLANP,encoding="utf-8"))
    plan={}
    for r in P["plan"]:
        W=frozenset(to_idx(x) for x in r["W"])
        plan.setdefault(W,[]).extend(tuple(c) for c in r["codes"])
    _G["plan"]={W:[tuple(sorted(c)) for c in cs] for W,cs in plan.items()}
def contains(h,c):
    cc={}
    for t in c: cc[t]=cc.get(t,0)+1
    return all(h[t]>=v for t,v in cc.items())
def dfs(base, inert, rem, codes):
    """返回 (True, None) 表示该基式下全部手牌都被覆盖; 否则 (False, 见证手牌向量)"""
    if any(contains(base,c) for c in codes): return True, None
    def rec(i,left,h):
        for c in codes:
            if contains(h,c): return True, None
        if i==len(inert):
            if left==0:
                if sum(h)!=13 or max(h)>4: raise AssertionError("非法见证手牌 %r" % (h,))
                return False, h
            return True, None
        ci=inert[i]
        for s in range(0,left+1,3):
            if left-s>12*(len(inert)-i-1): continue
            for v in _G[ci].get(s,()):
                h2=list(h)
                for t,x in enumerate(v): h2[BASE[ci]+t]+=x     # 注意 +BASE[ci]: 之前漏了偏移
                if sum(h2)>13 or max(h2)>4: raise AssertionError("非法手牌 %r" % (h2,))
                ok,w=rec(i+1,left-s,h2)
                if not ok: return False,w
        return True,None
    return rec(0,rem,base)
def work(ws):
    cls=_G["cls"]; PI=_G["PI"]; PII=_G["PII"]; plan=_G["plan"]
    nI=nII=0; bad=[]
    for W in ws:
        codes=plan.get(W,[])
        for b in cls.get(W,[]):
            if b[0]=="I":
                e=PI.get(b[1])
                if not e: continue
                ci=b[1][0]; s=b[1][1]
                inert=tuple(i for i in range(4) if i!=ci)   # 与 global.json 的 inert 一致 (cat 之外全部)
                for X in e[1]:
                    base=[0]*34
                    for t,x in enumerate(X): base[BASE[ci]+t]=x
                    nI+=1
                    ok,wit=dfs(base, inert, 13-s, codes)
                    if ok: continue
                    bad.append({"W":[nm(t) for t in sorted(W)],"kind":"I","cat":"mpsz"[ci],"A":"".join(str(x) for x in X),
                                "witness":"".join(nm(t)*wit[t] for t in range(34))})
            elif b[0]=="II":
                k1,k2=b[1],b[2]; e1=PII.get(k1); e2=PII.get(k2)
                if not e1 or not e2: continue
                c1,c2,s1,s2=k1[0],k2[0],k1[1],k2[1]
                inert=tuple(i for i in range(4) if i not in (c1,c2))
                for X1 in e1[1]:
                    for X2 in e2[1]:
                        base=[0]*34
                        for t,x in enumerate(X1): base[BASE[c1]+t]=x
                        for t,x in enumerate(X2): base[BASE[c2]+t]=x
                        nII+=1
                        ok,wit=dfs(base, inert, 13-s1-s2, codes)
                        if ok: continue
                        bad.append({"W":[nm(t) for t in sorted(W)],"kind":"II",
                                    "cats":"mpsz"[c1]+"mpsz"[c2],
                                    "A1":"".join(str(x) for x in X1),"A2":"".join(str(x) for x in X2),
                                    "witness":"".join(nm(t)*wit[t] for t in range(34))})
    return {"I_checked":nI,"II_checked":nII,"bad":bad}
if __name__=="__main__":
    PLANP=sys.argv[1] if len(sys.argv)>1 else os.path.join(HERE,"plan_k4_final.json")
    C=pickle.load(open(os.path.join(HERE,"..","strategy","out","table_cache.pkl"),"rb"))
    keys=list(C["cls"].keys())
    nproc=min(12,os.cpu_count() or 4)
    chunks=[keys[i::nproc] for i in range(nproc)]
    with Pool(nproc, initializer=init_worker) as pool:
        res=pool.map(work, chunks)
    nI=sum(r["I_checked"] for r in res); nII=sum(r["II_checked"] for r in res)
    bad=[x for r in res for x in r["bad"]]
    # 去重: 同一类同一基式可能来自多个块 (键不同/装饰不同)
    seen=set(); ded=[]
    for x in bad:
        k=(tuple(x["W"]),x["kind"],x.get("cat",""),x.get("cats",""),x.get("A",""),x.get("A1",""),x.get("A2",""))
        if k in seen: continue
        seen.add(k); ded.append(x)
    bad=ded
    badI=[x for x in bad if x["kind"]=="I"]; badII=[x for x in bad if x["kind"]=="II"]
    out={"plan":PLANP,"I_base_checked":nI,"II_base_checked":nII,
         "I_uncovered":len(badI),"II_uncovered":len(badII),"total_uncovered":len(bad),
         "uncovered_I":badI[:200],"uncovered_II":badII[:200],
         "classes_with_uncovered":len(set(tuple(x["W"]) for x in bad))}
    json.dump(out, open(os.path.join(HERE,"block_coverage_exact.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
    print("基式检查: I=%d II=%d ; 未覆盖: I=%d II=%d ; 涉及类=%d" % (nI,nII,len(badI),len(badII),out["classes_with_uncovered"]))
    for x in bad[:14]: print("   ",x)
    print("已写 work/verify/block_coverage_exact.json")
