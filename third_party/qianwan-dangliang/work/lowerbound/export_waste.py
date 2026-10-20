# -*- coding: utf-8 -*-
"""export_waste.py --- 导出"码不 ⊆ 本类任何手牌"的无效码清单 (可安全删除, 释放多重集容量)
判定 (逐类):
  A 精确层(tier=0): Type I 来源 -> 枚举同类同尺寸且 profile 相同的全部 X (X-set),
                    码 ⊆ 某手牌 <=> (码在主动类别的部分 ⊆ 某 X) 且 (码的其余牌可塞进 j 个惰性面子)
                    + 国士手牌 + chiitoi 手牌形状
  B 充分层(tier=1): Type II 来源只有 minA1/minA2 (充分判据) -> 这些类**不进删除清单**, 只列入 review
输出: work/lowerbound/waste_list.json  (+ 200 条抽样证据)
"""
import sys, os, json, itertools, collections, time, random
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lower import waits, melds_only
T0 = time.time()
def log(*a): print("[%7.1fs]" % (time.time()-T0), *a, flush=True)
HONN = ["E","S","W","N","Haku","Hatsu","Chun"]; HON = {n:27+i for i,n in enumerate(HONN)}
def nm(t): return ("%d%s" % (t%9+1, "mps"[t//9])) if t < 27 else HONN[t-27]
def to_idx(w):
    o=[]
    for x in w:
        if isinstance(x,int): o.append(x)
        elif x in HON: o.append(HON[x])
        else: o.append("mps".index(x[-1])*9+int(x[0])-1)
    return o
SU={"m":0,"p":1,"s":2,"z":3}
CAT_OF=[0]*9+[1]*9+[2]*9+[3]*7
def contains(h,c):
    need={}
    for t in c: need[t]=need.get(t,0)+1
    return all(h[t]>=v for t,v in need.items())
def parse(ds,ci):
    off=(0,9,18,27)[ci]; u=[0]*34
    for i,ch in enumerate(ds):
        if ch!="0": u[off+i]=int(ch)
    return tuple(u)
PLANP = sys.argv[1] if len(sys.argv)>1 else "work/verify/plan_k4_final.json"
P=json.load(open(PLANP,encoding="utf-8"))
cls={}
for r in P["plan"]:
    W=frozenset(to_idx(r["W"])); cls[W]=[tuple(c) for c in r["codes"]]
G=json.load(open("work/data/out/global.json",encoding="utf-8"))
ROWS={}
for r in G["classes"]: ROWS[frozenset(to_idx(r["W"]))]=r
log("plan=%s: %d 类 %d 码" % (PLANP,len(cls),sum(len(v) for v in cls.values())))

def min_parts(R):
    if not R: return 0
    best=[99]
    def rec(rem,parts):
        if parts>=best[0]: return
        if not rem: best[0]=parts; return
        first=rem[0]; rest=rem[1:]
        for size in (1,2,3):
            for combo in itertools.combinations(range(len(rest)), size-1):
                grp=[first]+[rest[i] for i in combo]
                ok = len(grp)<=2
                if not ok and len(grp)==3:
                    if len(set(grp))==1: ok=True
                    else:
                        sd=sorted(grp)
                        ok=(len(set(sd))==3 and CAT_OF[sd[0]]==CAT_OF[sd[2]]<3 and sd[1]==sd[0]+1 and sd[2]==sd[1]+1)
                if ok:
                    rec([rest[i] for i in range(len(rest)) if i not in combo], parts+1)
    rec(sorted(R),0); return best[0]

# ---- Type I 的 X-set 分组 (每个 (类别,尺寸) 只算一次) ----
KEYED={}
def keyed(ci,s):
    key=(ci,s)
    if key in KEYED: return KEYED[key]
    off=(0,9,18,27)[ci]; Ln=(9,9,9,7)[ci]; d=collections.defaultdict(list)
    for combo in itertools.combinations_with_replacement(range(Ln), s):
        v=[0]*Ln
        for x in combo: v[x]+=1
        if max(v)>4: continue
        u=[0]*34
        for i,x in enumerate(v): u[off+i]=x
        d[xkey(tuple(u),ci)].append(tuple(u))
    KEYED[key]=d; return d
def xkey(X,ci):
    off=(0,9,18,27)[ci]; Ln=(9,9,9,7)[ci]
    xs=[X[off+i] for i in range(Ln)]
    Wp=set()
    for t in range(Ln):
        if xs[t]>=4: continue
        d=list(xs); d[t]+=1; hit=False
        for pi in range(Ln):
            if d[pi]>=2:
                e=list(d); e[pi]-=2
                if melds_only(tuple(e)) is not None: hit=True; break
        if hit: Wp.add(off+t)
    otl=[i for i,x in enumerate(xs) if x%2]
    odd=len(otl); otv=(off+otl[0]) if odd==1 else None
    nz=[x for x in xs if x]
    o2=(sum(1 for x in nz if x==1)==1 and all(x==2 for x in nz if x!=1))
    return (frozenset(Wp), odd, otv, o2)

CHIIT={}
for mask,v in G.get("chiitoi_descriptors",{}).items():
    W=frozenset(t for t in range(34) if (int(mask)>>t)&1)
    CHIIT[W]=[to_idx([d["z"]])[0] for d in v]
KOК=tuple(sorted([0,8,9,17,18,26]+list(range(27,34))))
kok_hands=[]
H13=[0]*34
for t in KOК: H13[t]=1
kok_hands.append(tuple(H13))
for miss in KOК:
    for d in KOК:
        if d==miss: continue
        h=list(H13); h[miss]=0; h[d]+=1; kok_hands.append(tuple(h))

def chiitoi_shape_ok(W,c):
    if W not in CHIIT: return False
    cc=collections.Counter(c)
    for z in CHIIT[W]:
        if cc.get(z,0)>1: continue
        if any(t!=z and v>2 for t,v in cc.items()): continue
        S=[t for t in cc if t!=z]
        if len(S)<=6 and all(CAT_OF[t]==CAT_OF[t] for t in S): return True
    return False

def classify(W,c):
    """返回 (in_class: bool, tier: 0 精确 / 1 充分, reason)"""
    row=ROWS.get(W)
    if row is None: return False,1,"no_row"
    tier=0; reasons=[]
    for s in row.get("sources",[]):
        if s["kind"]=="I":
            ci=SU[s["cat"]]; A=parse(s["A"],ci); size=sum(A); j=(13-size)//3
            inert=[SU[x] for x in s["inert"]]
            cc=collections.Counter(c)
            cpart=[t for t,k in cc.items() if CAT_OF[t]==ci for _ in range(k)]
            if any(CAT_OF[t] not in inert for t in cc if CAT_OF[t]!=ci): continue
            R=[t for t,k in cc.items() if CAT_OF[t]!=ci for _ in range(k)]
            if min_parts(R)>j: continue
            # 码在主动类别的部分必须 ⊆ 某个 X
            XS=keyed(ci,size).get(xkey(A,ci),[])
            need=collections.Counter(cpart)
            for X in XS:
                if all(X[t]>=k for t,k in need.items()): return True,0,"I"
            reasons.append("I:catpart_not_in_Xset(%d X's)"%len(XS))
        elif s["kind"]=="II":
            tier=1
            c1,c2=SU[s["cats"][0]],SU[s["cats"][1]]
            u1=parse(s["minA1"],c1); u2=parse(s["minA2"],c2)
            inert=[SU[x] for x in s["inert"]]
            cc=collections.Counter(c)
            if any((CAT_OF[t]==c1 and u1[t]<k) or (CAT_OF[t]==c2 and u2[t]<k) for t,k in cc.items()): continue
            R=[t for t,k in cc.items() if CAT_OF[t] not in (c1,c2) for _ in range(k)]
            if any(CAT_OF[t] not in inert for t in R): continue
            j=max((13-sum(u1)-sum(u2))//3,0)
            if min_parts(R)<=j: return True,1,"II-sufficient"
        elif s["kind"]=="kokushi":
            if any(contains(h,c) for h in kok_hands): return True,0,"kokushi"
    if chiitoi_shape_ok(W,c): return True,0,"chiitoi"
    return False,tier,";".join(reasons) or "no_source_matched"

# ---- 全类扫描 ----
waste_safe=collections.defaultdict(list); waste_review=collections.defaultdict(list)
nver=0
for W in sorted(cls, key=lambda S: sorted(S)):
    hs=cls[W]
    for c in hs:
        ok,tier,why=classify(W,c)
        if ok: nver+=1; continue
        if tier==0: waste_safe[W].append(list(c))
        else: waste_review[W].append(list(c))
n_safe=sum(len(v) for v in waste_safe.values()); n_rev=sum(len(v) for v in waste_review.values())
log("④ 重判: 通过 %d ; 精确层待删 %d ; TypeII 待复核 %d" % (nver, n_safe, n_rev))
out={"k":4,"plan":PLANP,"note":"码 c 不 ⊆ 该类任何手牌 ⇒ 删除不影响覆盖 (前提: 来源清单完备)",
     "tier0_note":"tier0 = Type I 全 X-set × 惰性补牌族 + 国士 + chiitoi 形状, 精确枚举",
     "tier1_note":"tier1 = 含 Type II 来源的类, 只用了 minA1/minA2 充分判据 -> 不进删除清单",
     "classes":[{"W":[nm(t) for t in sorted(W)],"del":waste_safe[W]} for W in waste_safe],
     "review_classes":[{"W":[nm(t) for t in sorted(W)],"del":waste_review[W]} for W in waste_review],
     "total":n_safe,"review_total":n_rev}
json.dump(out, open(os.path.join(HERE,"waste_list.json"),"w",encoding="utf-8"), ensure_ascii=False)
log("写出 waste_list.json: 删除清单 %d 条 / %d 类 ; review %d 条 / %d 类" % (
    n_safe, len(waste_safe), n_rev, len(waste_review)))

# ---- 200 条抽样证据: 对该类做**完备手牌枚举**扫描, 证明无一包含 ----
rng=random.Random(20240615)
pool=[(W,c) for W in waste_safe for c in waste_safe[W]]
rng.shuffle(pool)
sample=pool[:200]
MELDVC={}
def meld_vecs(cat,s):
    key=(cat,s)
    if key in MELDVC: return MELDVC[key]
    Ln=(9,9,9,7)[cat]; off=(0,9,18,27)[cat]; out=[]
    if s==0: out=[tuple([0]*34)]
    else:
        for combo in itertools.combinations_with_replacement(range(Ln), s):
            v=[0]*Ln
            for x in combo: v[x]+=1
            if max(v)>4: continue
            if cat==3:
                if all(x%3==0 for x in v): out.append(tuple([0]*off+v+[0]*(34-off-Ln)))
            elif melds_only(tuple(v)) is not None: out.append(tuple([0]*off+v+[0]*(34-off-Ln)))
    MELDVC[key]=out; return out
def fillers(inert,j):
    out=[]
    def rec(i,rem,acc):
        if i==len(inert):
            if rem==0: out.append(tuple(acc))
            return
        for s in range(0,rem+1,3):
            for v in meld_vecs(inert[i],s): rec(i+1,rem-s,[acc[q]+v[q] for q in range(34)])
    rec(0,3*j,[0]*34); return out
ev=[]
for (W,c) in sample:
    row=ROWS.get(W); hands=[]
    for s in (row.get("sources",[]) if row else []):
        if s["kind"]=="I":
            ci=SU[s["cat"]]; A=parse(s["A"],ci); size=sum(A); j=(13-size)//3
            XS=keyed(ci,size).get(xkey(A,ci),[]); FL=fillers([SU[x] for x in s["inert"]],j)
            for X in XS:
                for F in FL: hands.append(tuple(X[q]+F[q] for q in range(34)))
        elif s["kind"]=="kokushi": hands.extend(kok_hands)
    hit=any(contains(h,c) for h in hands)
    src=("I,s=%d,j=%d,Xset=%d,F=%d" % (sum(parse(s["A"],SU[s["cat"]])), (13-sum(parse(s["A"],SU[s["cat"]])))//3,
          len(keyed(SU[s["cat"]],sum(parse(s["A"],SU[s["cat"]]))).get(xkey(parse(s["A"],SU[s["cat"]]),SU[s["cat"]]),[])), 0)
          if row and row["sources"] and row["sources"][0]["kind"]=="I" else "n/a")
    ev.append({"W":[nm(t) for t in sorted(W)],"code":[nm(t) for t in c],
               "hands_scanned":len(hands),"any_contains":hit,"source_info":src})
bad=[e for e in ev if e["any_contains"]]
log("抽样 200 条: 完备枚举扫描后仍无包含的 = %d ; 反例 = %d" % (200-len(bad), len(bad)))
json.dump({"sample_size":200,"counterexamples":bad,"evidence":ev},
          open(os.path.join(HERE,"waste_sample_evidence.json"),"w",encoding="utf-8"), ensure_ascii=False)
log("写出 waste_sample_evidence.json")
