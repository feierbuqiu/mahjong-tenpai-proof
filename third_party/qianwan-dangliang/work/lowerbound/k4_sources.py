# -*- coding: utf-8 -*-
"""k4_sources.py --- 精确来源判定 (用 work/recon/table_perA.pkl 的 A 变体表)
对任意 k=4 plan: 判定 "码 c 是否 ⊆ 类 W 的某手牌"
  块来源 = 表格 'cls'[W] (kind I / II / KOK), A 变体表 = PROFI_D / PROFII_D
  判据: 码在主动类别的部分 ⊆ 某个 A 变体, 其余牌可塞进 j 个惰性面子 (暴力划分 min_parts),
        或 ⊆ 国士手牌, 或符合该类的 chiitoi 形状 (6 对 + z)。
这是**完整**判据 (不再用 minA1/minA2 的保守近似)。
"""
import os, sys, pickle, itertools, collections
import lower
from lower import melds_only
HERE = os.path.dirname(os.path.abspath(__file__))
CAT_OF = [0]*9+[1]*9+[2]*9+[3]*7
OFF = (0,9,18,27); LN = (9,9,9,7)
_T = None
def table():
    global _T
    if _T is None:
        for p in (os.path.join(os.path.dirname(HERE), "recon", "table_perA.pkl"),
                  os.path.join(os.path.dirname(HERE), "strategy", "out", "table_cache.pkl")):
            if os.path.exists(p):
                try:
                    _T = pickle.load(open(p, "rb")); break
                except Exception:
                    continue
    return _T
HONN = ["E","S","W","N","Haku","Hatsu","Chun"]; HON = {n:27+i for i,n in enumerate(HONN)}
def to_idx(w):
    o=[]
    for x in w:
        if isinstance(x,int): o.append(x)
        elif x in HON: o.append(HON[x])
        else: o.append("mps".index(x[-1])*9+int(x[0])-1)
    return o
def contains(h,c):
    need={}
    for t in c: need[t]=need.get(t,0)+1
    return all(h[t]>=v for t,v in need.items())
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
                if len(grp)<=2: ok=True
                elif len(grp)==3:
                    if len(set(grp))==1: ok=True
                    else:
                        sd=sorted(grp)
                        ok=(len(set(sd))==3 and CAT_OF[sd[0]]==CAT_OF[sd[2]]<3 and sd[1]==sd[0]+1 and sd[2]==sd[1]+1)
                else: ok=False
                if ok: rec([rest[i] for i in range(len(rest)) if i not in combo], parts+1)
    rec(sorted(R),0); return best[0]
KOК = tuple(sorted([0,8,9,17,18,26]+list(range(27,34))))
KOK_HANDS = []
_H13=[0]*34
for t in KOК: _H13[t]=1
KOK_HANDS.append(tuple(_H13))
for miss in KOК:
    for d in KOК:
        if d==miss: continue
        h=list(_H13); h[miss]=0; h[d]+=1; KOK_HANDS.append(tuple(h))

_CLS = None; _IDX = {}
def cls_blocks():
    global _CLS
    if _CLS is None: _CLS = table()["cls"]
    return _CLS
def block_index(W, bi, blk):
    """缓存块内 A 变体的 (tile->list of variants) 索引"""
    key=(id(W), bi)
    if key in _IDX: return _IDX[key]
    T = table()
    if blk[0]=="I":
        c_i, s, pkey = blk[1]; am, xs = T["PROFI_D"][(c_i, s, pkey)]
        idx=collections.defaultdict(list)
        for X in xs:
            for j,v in enumerate(X):
                if v: idx[OFF[c_i]+j].append(X)
        _IDX[key]=("I", c_i, s, idx, len(xs))
    elif blk[0]=="II":
        (c1,s1,k1)=blk[1]; (c2,s2,k2)=blk[2]
        am1,xs1 = T["PROFII_D"][(c1,s1,k1)]; am2,xs2 = T["PROFII_D"][(c2,s2,k2)]
        idx1=collections.defaultdict(list); idx2=collections.defaultdict(list)
        for X in xs1:
            for j,v in enumerate(X):
                if v: idx1[OFF[c1]+j].append(X)
        for X in xs2:
            for j,v in enumerate(X):
                if v: idx2[OFF[c2]+j].append(X)
        _IDX[key]=("II", c1, c2, s1, s2, idx1, idx2, len(xs1), len(xs2))
    else:
        _IDX[key]=("KOK",)
    return _IDX[key]

_KOKC = {}
def kok_hands_for_class(W):
    """按类重建国士来源手牌 (verifier 指出不能全局池化):
       |W|=13 -> 13 张幺九各一张; |W|=1 -> 除该张外 12 张幺九各一张 + 任一张重复 (12 手)"""
    if W in _KOKC: return _KOKC[W]
    if len(W) == 13:
        out = [tuple(_H13)]
    elif len(W) == 1:
        t = next(iter(W)); others = [x for x in KOК if x != t]; out = []
        for d in others:
            h = [0]*34
            for x in others: h[x] = 1
            h[d] += 1
            out.append(tuple(h))
    else:
        out = []
    _KOKC[W] = out; return out
def code_in_class(W, c, chiit_zs):
    """精确: 码 c 是否 ⊆ 类 W 的某手牌"""
    cc = collections.Counter(c)
    for bi, blk in enumerate(cls_blocks().get(W, [])):
        info = block_index(W, bi, blk)
        if info[0]=="KOK":
            if any(contains(h,c) for h in kok_hands_for_class(W)): return True, "kokushi"
        elif info[0]=="I":
            _, c_i, s, idx, nxs = info
            if any(CAT_OF[t]!=c_i and CAT_OF[t] not in [x for x in range(4) if x!=c_i] for t in cc): pass
            rest = [t for t,k in cc.items() if CAT_OF[t]!=c_i for _ in range(k)]
            j = (13-s)//3
            if min_parts(rest) > j: continue
            cands = None
            for t in cc:
                if CAT_OF[t]==c_i:
                    lst = idx.get(t, [])
                    cands = lst if cands is None else [X for X in cands if X in set(lst)]
                    if not cands: break
            if cands is None: cands = [None]  # 码在主动类别无牌 -> 任意 X 都可
            for X in cands:
                if X is None: return True, "I"
                ok=True
                for t,k in cc.items():
                    if CAT_OF[t]==c_i and X[t-OFF[c_i]] < k: ok=False; break
                if ok: return True, "I"
        else:
            _, c1, c2, s1, s2, idx1, idx2, n1, n2 = info
            rest = [t for t,k in cc.items() if CAT_OF[t] not in (c1,c2) for _ in range(k)]
            if any(CAT_OF[t] not in [x for x in range(4) if x not in (c1,c2)] for t in rest): continue
            j = (13-s1-s2)//3
            if min_parts(rest) > j: continue
            def cand(idx, ci):
                cands=None
                for t,k in cc.items():
                    if CAT_OF[t]==ci:
                        lst=idx.get(t,[])
                        cands = lst if cands is None else [X for X in cands if X in set(lst)]
                        if not cands: return None
                return cands if cands is not None else [None]
            c1c = cand(idx1, c1); c2c = cand(idx2, c2)
            if c1c and c2c:
                for X1 in (c1c if c1c!=[None] else [None]):
                    for X2 in (c2c if c2c!=[None] else [None]):
                        ok=True
                        for t,k in cc.items():
                            if CAT_OF[t]==c1 and X1 is not None and X1[t-OFF[c1]]<k: ok=False; break
                            if CAT_OF[t]==c2 and X2 is not None and X2[t-OFF[c2]]<k: ok=False; break
                        if ok: return True, "II"
    # chiitoi 形状
    for z in chiit_zs:
        if cc.get(z,0) > 1: continue
        if any(t!=z and v>2 for t,v in cc.items()): continue
        if len([t for t in cc if t!=z]) <= 6: return True, "chiitoi"
    return False, "none"
