# -*- coding: utf-8 -*-
"""export_waste_exact.py --- 用 A 变体表精确导出"不 ⊆ 本类任何手牌"的码 (可安全删除)
输出: work/lowerbound/waste_list.json (Lead 指定格式) + waste_sample_evidence.json
"""
import sys, os, json, itertools, collections, random, time
sys.stdout.reconfigure(encoding="utf-8")
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import k4_sources as KS
T0=time.time()
def log(*a): print("[%7.1fs]"%(time.time()-T0), *a, flush=True)
HONN=["E","S","W","N","Haku","Hatsu","Chun"]
def nm(t): return ("%d%s"%(t%9+1,"mps"[t//9])) if t<27 else HONN[t-27]
def to_idx(w):
    o=[]
    for x in w:
        if isinstance(x,int): o.append(x)
        elif x in HONN: o.append(27+HONN.index(x))
        else: o.append("mps".index(x[-1])*9+int(x[0])-1)
    return o
PLANP=sys.argv[1] if len(sys.argv)>1 else "work/verify/plan_k4_final.json"
P=json.load(open(PLANP,encoding="utf-8"))
cls={}
for r in P["plan"]:
    W=frozenset(to_idx(r["W"])); cls[W]=[tuple(c) for c in r["codes"]]
G=json.load(open("work/data/out/global.json",encoding="utf-8"))
CH={}
for mask,v in G.get("chiitoi_descriptors",{}).items():
    W=frozenset(t for t in range(34) if (int(mask)>>t)&1); CH[W]=[to_idx([d["z"]])[0] for d in v]
log("plan=%s: %d 类 %d 码" % (PLANP,len(cls),sum(len(v) for v in cls.values())))
waste=collections.defaultdict(list); nver=0
for W in sorted(cls, key=lambda S: sorted(S)):
    zs=CH.get(W,[])
    for c in cls[W]:
        ok,why=KS.code_in_class(W,c,zs)
        if ok: nver+=1
        else: waste[W].append(list(c))
tot=sum(len(v) for v in waste.values())
log("精确④: 通过 %d ; 待删 **%d** 条 / %d 类" % (nver, tot, len(waste)))
out={"k":4,"plan":PLANP,
     "note":"码 c 不 ⊆ 该类任何手牌 ⇒ 删除不影响覆盖 (判定用 A 变体表 table_perA.pkl, 精确; 前提: 来源清单完备)",
     "method":"块来源 cls[W] (I/II/KOK) + PROFI_D/PROFII_D 的全部 A 变体 + 惰性补牌族 min_parts + chiitoi 形状",
     "classes":[{"W":[nm(t) for t in sorted(W)],"del":waste[W]} for W in waste],
     "total":tot}
json.dump(out, open(os.path.join(HERE,"waste_list.json"),"w",encoding="utf-8"), ensure_ascii=False)
log("写出 waste_list.json (total=%d)" % tot)

# ---- 200 条抽样证据 ----
rng=random.Random(20240616)
pool=[(W,c) for W in waste for c in waste[W]]
rng.shuffle(pool); sample=pool[:200]
ev=[]; cex=[]
for (W,c) in sample:
    cc=collections.Counter(c); per=[]
    for bi,blk in enumerate(KS.cls_blocks().get(W,[])):
        info=KS.block_index(W,bi,blk)
        if info[0]=="KOK": per.append({"block":"KOK","contains":any(KS.contains(h,c) for h in KS.KOK_HANDS)})
        elif info[0]=="I":
            _,c_i,s,idx,nxs=info; j=(13-s)//3
            rest=[t for t,k in cc.items() if KS.CAT_OF[t]!=c_i for _ in range(k)]
            mp=KS.min_parts(rest)
            ncat_ok=all(KS.CAT_OF[t]!=c_i for t in rest)
            per.append({"block":"I","cat":c_i,"|A|":s,"j":j,"A_variants":nxs,
                        "min_parts(rest)":mp,"rest_ok":ncat_ok and mp<=j})
        else:
            _,c1,c2,s1,s2,idx1,idx2,n1,n2=info; j=(13-s1-s2)//3
            rest=[t for t,k in cc.items() if KS.CAT_OF[t] not in (c1,c2) for _ in range(k)]
            mp=KS.min_parts(rest)
            per.append({"block":"II","cats":[c1,c2],"sizes":[s1,s2],"A1_var":n1,"A2_var":n2,"j":j,
                        "min_parts(rest)":mp,"rest_ok":mp<=j})
    ev.append({"W":[nm(t) for t in sorted(W)],"code":[nm(t) for t in c],"per_block":per,
               "chiitoi_zs":[nm(z) for z in CH.get(W,[])]})
    if any(p.get("contains") for p in per): cex.append({"W":[nm(t) for t in sorted(W)],"code":[nm(t) for t in c]})
log("抽样 200 条: 重新独立判定后仍为'不可用'的 = %d ; 反例 = %d" % (200-len(cex), len(cex)))
json.dump({"sample_size":200,"counterexamples":cex,"evidence":ev},
          open(os.path.join(HERE,"waste_sample_evidence.json"),"w",encoding="utf-8"), ensure_ascii=False)
log("写出 waste_sample_evidence.json")
