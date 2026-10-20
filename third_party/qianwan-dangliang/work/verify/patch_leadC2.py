
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_leadC2.py -- 最小补丁: 对 55 条未覆盖基式各补 1 条码.
未覆盖基式 |A| 全为 4 => 取 A 的多重集的一个排列(有序码)即可覆盖整块 (c ⊆ A ⊆ 块内每手牌).
要求: 该有序码全局唯一 (当前 17,291 条已唯一). 补完用 block_coverage_exact 自检 I=0 II=0.
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
PLAN="work/recon/plan_k4_leadC.json"; DST=os.path.join(HERE,"plan_k4_leadC_patched.json")
C=pickle.load(open(os.path.join(HERE,"..","strategy","out","table_cache.pkl"),"rb"))
BCE._G["cls"],BCE._G["PI"],BCE._G["PII"]=C["cls"],C["PROFI_D"],C["PROFII_D"]
for i in range(4): BCE._G[i]=BCE.build_dec(i)
P=json.load(open(PLAN,encoding="utf-8"))
plan={}; order=[]
for r in P["plan"]:
    W=frozenset(ti(x) for x in r["W"]); plan.setdefault(W,[]).extend(tuple(c) for c in r["codes"]); order.append(W)
used=set(c for cs in plan.values() for c in cs)
print("底版: 类 %d 码 %d" % (len(plan),len(used)))
B=json.load(open(os.path.join(HERE,"block_coverage_exact.json"),encoding="utf-8"))
items=B["uncovered_I"]+B["uncovered_II"]
BASE=[0,9,18,27]; CATI={"m":0,"p":1,"s":2,"z":3}
added=0; bad=[]; report=[]
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
    tiles=[]
    for t,x in enumerate(base): tiles += [t]*x
    assert len(tiles)==4, (it, tiles)
    pick=None
    for comb in sorted(set(itertools.permutations(tiles))):
        if comb not in used: pick=comb; break
    if pick is None:
        bad.append({"W":it["W"],"kind":it["kind"],"reason":"A 的 24 个排列全被占用"}); continue
    plan[W].append(tuple(pick)); used.add(tuple(pick)); added+=1
    ok,wit=BCE.dfs(base,inert,rem,plan[W])
    report.append({"W":it["W"],"kind":it["kind"],"code":list(pick),"base_now_covered":bool(ok)})
    if not ok: bad.append({"W":it["W"],"kind":it["kind"],"reason":"补码后仍不覆盖"})
print("补码 %d 条 ; 失败 %d ; 总码 %d" % (added,len(bad),len(used)))
miss=[r for r in report if not r["base_now_covered"]]
print("补码后仍不覆盖的基式:",len(miss))
rows=[{"W":[nm(t) for t in sorted(W)],"codes":[list(c) for c in sorted(set(plan[W]))]} for W in order]
tot=sum(len(r["codes"]) for r in rows)
out={"k":4,"n_classes":len(rows),"n_codes":tot,"plan":rows,"base":PLAN,
     "patch":{"added":added,"bases":len(items),"code_list":[r["code"] for r in report]}}
json.dump(out, open(DST,"w",encoding="utf-8"), ensure_ascii=False)
print("已写",DST,"; 类 %d 码 %d" % (len(rows),tot))
if bad: print("失败:",bad[:5])
