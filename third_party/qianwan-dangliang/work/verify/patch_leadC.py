
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_leadC.py -- 为 block_coverage_exact.json 里 55 条未覆盖基式贪心补码 (候选补丁, verifier 命名空间).
选码: 取该基式 DFS 给出的见证手牌内的 4 张组合, 要求全 plan 全局唯一; 加入后重跑该基式 DFS 直到覆盖.
输出 work/verify/plan_k4_leadC_patched.json
"""
import sys, os, json, pickle, itertools
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE); sys.path.insert(0,os.path.join(HERE,"..","strategy"))
import block_coverage_exact as BCE
HON=["E","S","W","N","Haku","Hatsu","Chun"]
def nm(t): return ("%d%s"%(t%9+1,"mps"[t//9])) if t<27 else HON[t-27]
HONI={"E":27,"S":28,"W":29,"N":30,"Haku":31,"Hatsu":32,"Chun":33}
def ti(x):
    if isinstance(x,int): return x
    if x in HONI: return HONI[x]
    return "mps".index(x[-1])*9+int(x[0])-1
PLAN="work/recon/plan_k4_leadC.json"; DST="work/verify/plan_k4_leadC_patched.json"
C=pickle.load(open(os.path.join(HERE,"..","strategy","out","table_cache.pkl"),"rb"))
BCE._G["cls"],BCE._G["PI"],BCE._G["PII"]=C["cls"],C["PROFI_D"],C["PROFII_D"]
for i in range(4): BCE._G[i]=BCE.build_dec(i)
P=json.load(open(PLAN,encoding="utf-8"))
plan={}
for r in P["plan"]:
    W=frozenset(ti(x) for x in r["W"]); plan.setdefault(W,[]).extend(tuple(c) for c in r["codes"])
used=set(c for cs in plan.values() for c in cs)
print("初始: 类 %d 码 %d" % (len(plan),len(used)))
B=json.load(open(os.path.join(HERE,"block_coverage_exact.json"),encoding="utf-8"))
items=B["uncovered_I"]+B["uncovered_II"]
BASE=[0,9,18,27]; CATI={"m":0,"p":1,"s":2,"z":3}
added=0; fails=[]
for it in items:
    W=frozenset(ti(t) for t in it["W"])
    if it["kind"]=="I":
        ci=CATI[it["cat"]]; A=[int(ch) for ch in it["A"]]
        base=[0]*34
        for t,x in enumerate(A): base[BASE[ci]+t]=x
        inert=tuple(i for i in range(4) if i!=ci); rem=13-sum(A)
    else:
        c1,c2=CATI[it["cats"][0]],CATI[it["cats"][1]]
        A1=[int(ch) for ch in it["A1"]]; A2=[int(ch) for ch in it["A2"]]
        base=[0]*34
        for t,x in enumerate(A1): base[BASE[c1]+t]=x
        for t,x in enumerate(A2): base[BASE[c2]+t]=x
        inert=tuple(i for i in range(4) if i not in (c1,c2)); rem=13-sum(A1)-sum(A2)
    for _try in range(60):
        codes=plan.get(W,[])
        ok,wit=BCE.dfs(base,inert,rem,codes)
        if ok: break
        h=list(wit)
        tiles=[t for t in range(34) for _ in range(h[t])]
        cands=[]
        for comb in set(itertools.combinations(sorted(tiles),4)):
            c=tuple(sorted(comb))
            if c in used: continue
            # 优先: 本类已有码覆盖率提升潜力 (简单起见: 只要求 ⊆ 见证手牌)
            cands.append(c)
        if not cands: fails.append({"W":it["W"],"witness":"".join(nm(t)*h[t] for t in range(34))}); break
        c=cands[0]
        plan.setdefault(W,[]).append(c); used.add(c); added+=1
    else:
        fails.append({"W":it["W"],"reason":"60 次补码后仍未覆盖"})
print("补码 %d 条 ; 失败基式 %d ; 总码 %d" % (added,len(fails),len(used)))
rows=[]
for W,cs in plan.items():
    rows.append({"W":[nm(t) for t in sorted(W)],"codes":[list(c) for c in cs]})
JSONP={"k":4,"n_classes":len(rows),"n_codes":sum(len(r["codes"]) for r in rows),"plan":rows,
       "base":PLAN,"patch_added":added}
json.dump(JSONP, open(os.path.join(HERE,"plan_k4_leadC_patched.json"),"w",encoding="utf-8"), ensure_ascii=False)
print("已写 work/verify/plan_k4_leadC_patched.json")
if fails: print("失败:", fails[:5])
