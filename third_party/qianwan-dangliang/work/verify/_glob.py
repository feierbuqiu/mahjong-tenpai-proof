
import sys, json, pickle, random
sys.path.insert(0,"work/verify"); sys.path.insert(0,"work/strategy")
import indep_core as IC
HON=["E","S","W","N","Haku","Hatsu","Chun"]
def nm(t): return ("%d%s"%(t%9+1,"mps"[t//9])) if t<27 else HON[t-27]
def hs(ts): return "".join(nm(t) for t in ts)
P=json.load(open("work/verify/plan_k4_final.json",encoding="utf-8"))
classes=[(frozenset(r["W"]),[tuple(c) for c in r["codes"]]) for r in P["plan"]]
# 三个被清空类的实例手牌 (来自上一个探针输出)
samples=[
 ([0,1,2,3,3,3,9,9,9,10,11,12,13], frozenset([0,3,9,12,15])),   # 2m3m4m 4m4m 1p1p1p 2p3p4p5p6p (需要重算 W)
 ([0,0,0,1,2,9,10,11,12,13,14,14,14], frozenset([0,3,9,12,15])),
 ([1,2,3,3,3,10,11,12,13,14,15,16,17], frozenset([1,4,10,13,16])),
]
for ts,Wexp in samples:
    v=[0]*34
    for t in ts: v[t]+=1
    W=IC.compute_W(v)
    print("hand:",hs(sorted(ts)),"| W=",sorted(nm(t) for t in W),"| 期望=",sorted(nm(t) for t in Wexp))
    hit=[]
    for Wc,cs in classes:
        for c in cs:
            if all(v[t]>=c.count(t) for t in range(34)): hit.append((Wc,c))
    print("   全局 ⊆ 该手牌的码数:",len(hit))
    from collections import Counter
    cc=Counter(frozenset(Wc)==W for Wc,_ in hit)
    print("   其中属于同类:",cc.get(True,0)," 属于异类:",cc.get(False,0))
    for Wc,c in hit[:5]: print("      类 W=",",".join(nm(t) for t in sorted(Wc))," 码=",",".join(nm(t) for t in c))
